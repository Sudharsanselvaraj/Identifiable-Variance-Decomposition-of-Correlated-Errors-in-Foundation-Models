"""Lower-confidence ancestry from ``config.json`` ``_name_or_path`` (Exp04).

Applies only to models excluded because their model card declares no parent.
The field records the path the checkpoint was loaded from when it was saved,
which is often (not always) the parent repo. It is evidence, never ground
truth: every value gets an outcome code, and only ``ok`` links are used, and
only in the EXPANDED sensitivity roster -- never in the primary roster.

Outcome codes:
    ok              existing Hub repo, not the model itself
    no_config       config.json missing or unreadable
    missing_field   no _name_or_path
    local_path      absolute / home / relative filesystem path
    merge_path      path mentions a merge tool (mergekit, etc.) -> merge evidence
    not_repo_id     not of the form org/name
    self_reference  names the model itself
    not_on_hub      well-formed id that does not exist on the Hub

Metadata only: reads config.json (a few KB); never touches weights.
Records go to ``datasets/ollb/config_lineage.jsonl`` (resumable).

Usage (repo root):
    python3 -m lineage_era.ollb.config_lineage
"""
from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from . import hub_meta

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "datasets" / "ollb" / "config_lineage.jsonl"
REPO_ID = re.compile(r"^[A-Za-z0-9][\w.-]*/[\w.-]+$")
MERGE_HINT = re.compile(r"merge|mergekit|slerp|ties|dare", re.I)
MIN_INTERVAL = 0.12        # file reads use the resolver quota, not the API one


_lock = threading.Lock()
_next = [0.0]


def _throttle() -> None:
    with _lock:
        now = time.monotonic()
        wait = _next[0] - now
        _next[0] = max(now, _next[0]) + MIN_INTERVAL
    if wait > 0:
        time.sleep(wait)


def read_name_or_path(repo: str, retries: int = 5) -> tuple[str, str | None]:
    """('ok', value) | ('no_config', None) | ('missing_field', None).

    One plain GET on the resolve endpoint (file-download quota). HfFileSystem
    would add API calls per file and share the 1000 / 5 min API window.
    """
    import requests
    from huggingface_hub import get_token

    url = f"https://huggingface.co/{repo}/resolve/main/config.json"
    headers = {"Authorization": f"Bearer {get_token()}"} if get_token() else {}
    for attempt in range(retries):
        _throttle()
        try:
            r = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException:
            time.sleep(min(60, 3 * 2 ** attempt))
            continue
        if r.status_code in (401, 403, 404):
            return "no_config", None
        if r.status_code == 429:
            time.sleep(hub_meta._retry_after(type("E", (), {"response": r})()))
            continue
        if r.status_code != 200:
            time.sleep(min(60, 3 * 2 ** attempt))
            continue
        try:
            cfg = r.json()
        except ValueError:
            return "no_config", None
        val = cfg.get("_name_or_path") if isinstance(cfg, dict) else None
        return ("ok", val) if isinstance(val, str) and val.strip() else \
            ("missing_field", None)
    raise RuntimeError(f"transient failure reading {repo}/config.json")


def classify(repo: str, raw: str | None, status: str) -> tuple[str, str | None]:
    """Outcome code and normalised candidate parent (before the Hub check)."""
    if status != "ok":
        return status, None
    v = raw.strip().rstrip("/")
    if v.startswith(("/", "~", ".", "\\")) or re.match(r"^[A-Za-z]:\\", v) \
            or v.count("/") > 1:
        return ("merge_path" if MERGE_HINT.search(v) else "local_path"), None
    if not REPO_ID.match(v):
        return "not_repo_id", None
    if v.lower() == repo.lower():
        return "self_reference", None
    return "candidate", v


def load() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    return {r["model"]: r for r in map(json.loads, OUT.read_text().splitlines()) if r}


def run(workers: int = 6) -> pd.DataFrame:
    from .roster_v1 import build as build_roster
    roster = build_roster()          # from the finished Hub cache, not a stale CSV
    targets = roster.loc[roster.exclusion_primary == "undeclared_parent", "model"].tolist()
    done = load()
    todo = [m for m in targets if m not in done]
    print(f"config reads: {len(todo)} to fetch ({len(done)} cached)", flush=True)
    lock = threading.Lock()
    with open(OUT, "a") as fh:
        def work(m: str) -> None:
            try:
                status, raw = read_name_or_path(m)
            except RuntimeError:
                return                                    # retried next run
            outcome, cand = classify(m, raw, status)
            rec = {"model": m, "source_field": "_name_or_path", "raw": raw,
                   "candidate": cand, "outcome": outcome}
            with lock:
                done[m] = rec
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                if len(done) % 250 == 0:
                    print(f"  {len(done)}/{len(targets)}", flush=True)
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(work, todo))

    # Hub check of candidate parents (and their own ancestry) via hub_meta.
    cands = sorted({r["candidate"] for r in done.values() if r["outcome"] == "candidate"})
    print(f"validating {len(cands)} candidate parents on the Hub", flush=True)
    meta = hub_meta.resolve(cands, workers=3)
    for r in done.values():
        if r["outcome"] == "candidate":
            rec = meta.get(r["candidate"])
            if rec is None or rec["status"] != "ok":
                r["outcome"] = "not_on_hub"
            elif rec["id"].lower() == r["model"].lower():
                r["outcome"] = "self_reference"
            else:
                r["outcome"], r["candidate"] = "ok", rec["id"]
    df = pd.DataFrame(done.values())
    df["confidence"] = df.outcome.eq("ok").map({True: "config", False: "none"})
    OUT.write_text("".join(json.dumps(r) + "\n" for r in df.to_dict("records")))
    print(df.outcome.value_counts().to_string())
    return df


if __name__ == "__main__":
    run()
