"""Resumable Hugging Face Hub metadata cache for lineage and dates.

One JSON line per repo in ``datasets/ollb/hub_meta.jsonl``:
    {"repo", "id" (current id after renames), "base_model" (list or null),
     "created_at" (ISO), "status": ok | missing}

Transient failures (throttling, timeouts) are not written, so they are retried
on the next run. Every line is flushed as soon as it is fetched, so an
interrupted run loses nothing.

Usage (repo root):
    python3 -m lineage_era.ollb.hub_meta --names datasets/ollb/v1_contents_meta.csv:fullname \
        --names datasets/kim/hugging_face.csv:name
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "datasets" / "ollb" / "hub_meta.jsonl"
MAX_LEVELS = 20
# HF API policy: 1000 requests per 300 s fixed window (RateLimit-Policy header).
MIN_INTERVAL = 0.31
_rate_lock = threading.Lock()
_next_slot = [0.0]


def _throttle() -> None:
    """Global pacing across worker threads to stay under the API window."""
    with _rate_lock:
        now = time.monotonic()
        wait = _next_slot[0] - now
        _next_slot[0] = max(now, _next_slot[0]) + MIN_INTERVAL
    if wait > 0:
        time.sleep(wait)


def _retry_after(exc) -> float:
    """Seconds until the rate-limit window resets, from the RateLimit header."""
    hdr = getattr(getattr(exc, "response", None), "headers", {}) or {}
    for part in str(hdr.get("RateLimit", "")).split(";"):
        if part.strip().startswith("t="):
            try:
                return float(part.strip()[2:]) + 1
            except ValueError:
                pass
    return 60.0


def load() -> dict[str, dict]:
    if not CACHE.exists():
        return {}
    out = {}
    for line in CACHE.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["repo"]] = rec
    return out


def fetch(repo: str, retries: int = 6) -> dict | None:
    """Metadata record for one repo, or None on a transient failure."""
    from huggingface_hub import HfApi
    from huggingface_hub.utils import (GatedRepoError, HfHubHTTPError,
                                       RepositoryNotFoundError)

    if not isinstance(repo, str) or repo.count("/") != 1 or " " in repo:
        return {"repo": repo, "id": repo, "base_model": None,
                "created_at": None, "status": "missing"}
    for attempt in range(retries):
        _throttle()
        try:
            info = HfApi().model_info(repo, timeout=20)
            base = info.card_data.get("base_model") if info.card_data else None
            if isinstance(base, str):
                base = [base]
            return {"repo": repo, "id": info.id,
                    "base_model": base if isinstance(base, list) else None,
                    "created_at": info.created_at.isoformat() if info.created_at else None,
                    "status": "ok"}
        except (RepositoryNotFoundError, GatedRepoError):
            return {"repo": repo, "id": repo, "base_model": None,
                    "created_at": None, "status": "missing"}
        except HfHubHTTPError as exc:
            code = getattr(exc.response, "status_code", None)
            if code in (400, 401, 403, 404, 410):
                return {"repo": repo, "id": repo, "base_model": None,
                        "created_at": None, "status": "missing"}
            if code == 429:
                with _rate_lock:     # pause every worker until the window resets
                    _next_slot[0] = max(_next_slot[0],
                                        time.monotonic() + _retry_after(exc))
                continue
        except Exception:  # timeouts, connection resets
            pass
        time.sleep(min(90, 3 * 2 ** attempt))
    return None


def resolve(names: list[str], workers: int = 8) -> dict[str, dict]:
    """Fetch every name and, breadth-first, every declared ancestor."""
    cache = load()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    frontier = sorted({n for n in names if isinstance(n, str)} - set(cache))
    with open(CACHE, "a") as fh:
        for level in range(MAX_LEVELS):
            if not frontier:
                break
            print(f"level {level}: {len(frontier)} repos", flush=True)
            done = failed = 0

            def work(repo: str) -> None:
                nonlocal done, failed
                rec = fetch(repo)
                with lock:
                    if rec is None:
                        failed += 1
                    else:
                        cache[repo] = rec
                        fh.write(json.dumps(rec) + "\n")
                        fh.flush()
                    done += 1
                    if done % 250 == 0:
                        print(f"  {done}/{len(frontier)} (transient failures {failed})",
                              flush=True)

            with ThreadPoolExecutor(workers) as pool:
                list(pool.map(work, frontier))
            print(f"  level {level} done; transient failures {failed}", flush=True)
            parents = {p for r in cache.values() for p in (r["base_model"] or [])}
            frontier = sorted(p for p in parents if p not in cache)
    return cache


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--names", action="append", required=True,
                    help="CSV path:column with repo ids (repeatable)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)
    names = []
    for spec in args.names:
        path, col = spec.rsplit(":", 1)
        names += pd.read_csv(ROOT / path, usecols=[col])[col].dropna().tolist()
    cache = resolve(names, args.workers)
    print(f"cached repos: {len(cache)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
