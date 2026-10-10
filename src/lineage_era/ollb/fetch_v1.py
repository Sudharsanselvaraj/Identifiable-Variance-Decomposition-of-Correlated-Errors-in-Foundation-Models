"""Fetch per-question MMLU predictions from the v1 Open LLM Leaderboard.

For each ``open-llm-leaderboard-old/details_<org>__<name>`` repo:

1. list the ``hendrycksTest-*|5`` parquet files and group them by run;
2. pick the run that covers all 57 subjects with the most rows (some runs
   are --limit partial runs; using one would silently shrink the item set);
3. read ONLY ``predictions`` (per-choice log-likelihoods), ``gold``, ``acc``
   and the item hash, via ranged reads (~13 MB per model instead of ~80 MB);
4. verify argmax(predictions) reproduces the stored ``acc`` on every item
   (the guard that would have caught the original resps[0] bug);
5. write ``datasets/ollb/v1/<org>__<name>.npz`` with item id, hash, predicted
   choice and gold. Existing files are skipped, so the job is resumable.

Usage (repo root):
    python3 -m lineage_era.ollb.fetch_v1 --models datasets/ollb/v1_roster.csv
    python3 -m lineage_era.ollb.fetch_v1 --repo details_meta-llama__Llama-2-7b-hf
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "datasets" / "ollb" / "v1"
ORG = "open-llm-leaderboard-old"
N_SUBJECTS = 57
COLUMNS = ["predictions", "gold", "acc", "hashes"]
N_ITEMS = 14042
SUBJECT_WORKERS = 12
# Reference model with the legacy layout (gold + item hash stored); supplies
# gold by (subject, position) for runs whose gold column is empty.
REFERENCE = OUT / "meta-llama__Llama-2-7b-hf.npz"
_ref_cache: dict = {}


def reference() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """subject -> (gold, hash) arrays in row order, from the reference model."""
    if not _ref_cache:
        z = np.load(REFERENCE)
        subj = np.array([i.split(":")[0] for i in z["item"]])
        for s_ in np.unique(subj):
            m = subj == s_
            _ref_cache[s_] = (z["gold"][m], z["hash"][m])
    return _ref_cache


def _run_of(path: str) -> str:
    return path.split("/")[3]


def _subject_of(path: str) -> str:
    return path.split("hendrycksTest-")[1].split("|")[0]


_local = threading.local()


def _session():
    """One requests.Session per thread (Sessions are not thread-safe)."""
    import requests

    if not hasattr(_local, "s"):
        _local.s = requests.Session()
    return _local.s


class _RangeFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests, with a small
    read-ahead block cache. Plain synchronous requests, safe across threads
    (fsspec's shared async loop deadlocked under ~100 worker threads)."""

    def __init__(self, url: str, size: int, headers: dict | None = None,
                 block: int = 64 * 1024):
        self.url, self.size, self.headers, self.block = url, size, headers or {}, block
        self.pos, self.nbytes = 0, 0
        self._cache_start, self._cache = 0, b""

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def _fetch(self, start: int, end: int) -> bytes:
        for attempt in range(5):
            r = _session().get(self.url, timeout=60, headers={
                **self.headers, "Range": f"bytes={start}-{end - 1}"})
            if r.status_code in (200, 206):
                self.nbytes += len(r.content)
                return r.content if r.status_code == 206 else r.content[start:end]
            time.sleep(min(30, 2 * 2 ** attempt))
        raise OSError(f"range read failed ({r.status_code}) for {self.url[:80]}")

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        if n == 0:
            return b""
        cs, ce = self._cache_start, self._cache_start + len(self._cache)
        if not (cs <= self.pos and self.pos + n <= ce):
            start = self.pos
            end = min(self.size, start + max(n, self.block))
            if self.pos + n > self.size - self.block:
                # Parquet footer: pyarrow reads the last 8 bytes, then the
                # metadata just before them; fetch the whole tail at once.
                start = max(0, min(self.pos, self.size - 4 * self.block))
                end = self.size
            self._cache_start, self._cache = start, self._fetch(start, end)
            cs = start
        out = self._cache[self.pos - cs:self.pos - cs + n]
        self.pos += len(out)
        return out

    def readinto(self, b):
        data = self.read(len(b))
        b[:len(data)] = data
        return len(data)


def _open_cdn(hf_path: str) -> _RangeFile:
    """Open a Hub file for ranged reads straight from its CDN location.

    One HEAD to the (rate-limited) resolve endpoint returns a redirect to a
    signed CDN URL plus the file size; footer and column-chunk range reads then
    go to the CDN and do not count against the 5000 / 5 min resolver window.
    """
    from huggingface_hub import get_token
    from urllib.parse import quote

    _, org, repo, rest = hf_path.split("/", 3)
    url = (f"https://huggingface.co/datasets/{org}/{repo}/resolve/main/"
           + quote(rest, safe="/"))
    auth = {"Authorization": f"Bearer {get_token()}"}
    for attempt in range(6):
        r = _session().head(url, headers=auth, allow_redirects=False, timeout=30)
        if r.status_code != 429:
            break
        time.sleep(30)
    loc = r.headers.get("Location", "")
    size = int(r.headers.get("X-Linked-Size") or r.headers.get("Content-Length") or 0)
    if r.status_code in (301, 302, 307, 308) and loc.startswith("http") and size:
        return _RangeFile(loc, size)
    # Not LFS-backed: read through the resolve URL (counts against the quota).
    h = _session().head(url, headers=auth, allow_redirects=True, timeout=30)
    return _RangeFile(url, int(h.headers["Content-Length"]), headers=auth)


def fetch_model(repo: str, retries: int = 4) -> dict:
    """Fetch one model; returns a status record (never raises)."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    out = OUT / f"{repo.removeprefix('details_')}.npz"
    if out.exists():
        return {"repo": repo, "status": "cached"}
    fs = HfFileSystem()
    base = f"datasets/{ORG}/{repo}"
    for attempt in range(retries):
        try:
            files = fs.glob(base + "/**/*hendrycksTest-*|5_*.parquet")
            by_run = defaultdict(dict)
            for f in files:
                by_run[_run_of(f)][_subject_of(f)] = f
            complete = {r: s for r, s in by_run.items() if len(s) == N_SUBJECTS}
            if not complete:
                return {"repo": repo, "status": "no_complete_run",
                        "runs": len(by_run)}
            # Most rows wins; later run breaks ties.
            sizes = {}
            for r, subj in complete.items():
                any_file = next(iter(subj.values()))
                with _open_cdn(any_file) as fh:
                    sizes[r] = pq.ParquetFile(fh).metadata.num_rows
            run = max(complete, key=lambda r: (sizes[r], r))

            def read_subject(subj: str):
                with _open_cdn(complete[run][subj]) as fh:
                    pf = pq.ParquetFile(fh)
                    names = set(pf.schema_arrow.names)
                    cols = (COLUMNS if "acc" in names
                            else ["predictions", "metrics"])
                    t = pf.read(columns=cols)
                    return subj, t, fh.nbytes

            with ThreadPoolExecutor(SUBJECT_WORKERS) as pool:
                tables = dict((s_, (t_, b_)) for s_, t_, b_ in
                              pool.map(read_subject, sorted(complete[run])))

            items, hashes, pred, gold = [], [], [], []
            n_bad = nbytes = 0
            schema = "legacy"
            for subj in sorted(tables):
                t, b = tables[subj]
                nbytes += b
                preds = t["predictions"].to_pylist()
                if "acc" in t.column_names and t.schema.field("acc").type == "string":
                    # Early-2023 variant: every column serialised as text.
                    schema = "legacy_str"
                    preds = [ast.literal_eval(p_) for p_ in preds]
                    golds = [int(g_) for g_ in t["gold"].to_pylist()]
                    accs = [float(a_) for a_ in t["acc"].to_pylist()]
                    hs = [ast.literal_eval(h_)["example"]
                          for h_ in t["hashes"].to_pylist()]
                elif "acc" in t.column_names:
                    golds = t["gold"].to_pylist()
                    accs = t["acc"].to_pylist()
                    hs = [h["example"] for h in t["hashes"].to_pylist()]
                else:
                    # Newer lighteval layout: gold is stored empty and there is
                    # no item hash. Gold comes from the reference model by
                    # (subject, position); the per-item acc check below then
                    # validates that alignment (a misaligned gold fails ~75%).
                    schema = "lighteval"
                    # Loaded only here: the reference model itself (legacy
                    # layout, gold stored) is fetched before its file exists.
                    ref = reference()
                    if subj not in ref or len(ref[subj][0]) != len(preds):
                        return {"repo": repo, "status": "row_count_mismatch",
                                "subject": subj, "run": run}
                    golds = list(ref[subj][0])
                    accs = [m["acc"] for m in t["metrics"].to_pylist()]
                    hs = [""] * len(preds)
                for k, (p, g, a, h) in enumerate(zip(preds, golds, accs, hs)):
                    choice = int(np.argmax(p)) if p else -1
                    n_bad += int(float(choice == g) != float(a))
                    # MMLU has 27 exact-duplicate questions, so the content
                    # hash is not unique; position within subject is the id
                    # and the hash is kept to verify alignment across models.
                    items.append(f"{subj}:{k}")
                    hashes.append(h)
                    pred.append(choice)
                    gold.append(g)
            if len(pred) != N_ITEMS:
                return {"repo": repo, "status": "item_count_mismatch",
                        "items": len(pred), "run": run, "schema": schema}
            if n_bad:
                return {"repo": repo, "status": "acc_mismatch", "n_bad": n_bad,
                        "items": len(pred), "run": run, "schema": schema}
            OUT.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out, item=np.array(items), hash=np.array(hashes),
                                pred=np.array(pred, np.int8),
                                gold=np.array(gold, np.int8), run=run, schema=schema)
            return {"repo": repo, "status": "ok", "items": len(pred), "run": run,
                    "schema": schema, "bytes": nbytes,
                    "acc": round(float(np.mean(np.array(pred) == np.array(gold))), 4)}
        except FileNotFoundError as exc:
            if "repository not found" in str(exc):
                return {"repo": repo, "status": "repo_missing"}
            if len(repo) > 96:
                # Hub repo names are capped at 96 characters, so the
                # leaderboard's details repo for this model cannot exist.
                return {"repo": repo, "status": "repo_missing",
                        "error": f"details repo name is {len(repo)} chars (> 96)"}
            err = f"{type(exc).__name__}: {str(exc)[:160]}"
            time.sleep(min(120, 10 * 2 ** attempt))
        except (KeyError, ValueError, IndexError, TypeError, SyntaxError) as exc:
            # Layout problems are deterministic: fail once, do not retry.
            return {"repo": repo, "status": "schema_error",
                    "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
        except Exception as exc:  # network / throttling: back off and retry
            err = f"{type(exc).__name__}: {str(exc)[:160]}"
            time.sleep(min(120, 10 * 2 ** attempt))
    return {"repo": repo, "status": "error", "error": err}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", help="CSV with a 'repo' column (details_<org>__<name>)")
    ap.add_argument("--repo", action="append", default=[])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    repos = list(args.repo)
    if args.models:
        repos += pd.read_csv(args.models)["repo"].tolist()
    log = OUT.parent / "fetch_v1_log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    done = errors = 0
    with ThreadPoolExecutor(args.workers) as pool, open(log, "a") as fh:
        futures = [pool.submit(fetch_model, r) for r in repos]
        for fut in as_completed(futures):
            rec = fut.result()
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            done += 1
            errors += rec["status"] == "error"
            if done % 25 == 0 or done == len(repos):
                print(f"{done}/{len(repos)} last={rec['status']}", flush=True)
    # Documented outcomes (no_complete_run, repo_missing, *_mismatch,
    # schema_error) are reported by scripts/validation_report.py; a model
    # still erroring after the retries is unresolved and fails the run.
    if errors:
        print(f"{errors} model(s) still erroring: re-run to resume", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
