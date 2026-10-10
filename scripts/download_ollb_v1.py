#!/usr/bin/env python3
"""Bulk download for Exp04: exactly the frozen cap-40 samples, nothing else.

1. Verifies the SHA-256 of each frozen sample against the hashes recorded in
   results/exp04_rosters/comparison.md; aborts on any mismatch.
2. Writes the download list (union of the two samples) with membership flags
   to datasets/ollb/frozen/download_union.csv.
3. Fetches the reference model (meta-llama/Llama-2-7b-hf) first, on its own,
   and aborts unless its answer file has 14,042 items: runs in the newer
   lighteval layout take their gold answers from it, so it must exist before
   the concurrent download starts.
4. Runs lineage_era.ollb.fetch_v1 on that list (resumable; every outcome is
   appended to datasets/ollb/fetch_v1_log.jsonl). Exit status 1 if any model
   is still erroring after the retries (re-run to resume).

Usage (repo root):
    python3 scripts/download_ollb_v1.py --limit 10     # pilot batch
    python3 scripts/download_ollb_v1.py                # everything
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lineage_era.ollb import fetch_v1  # noqa: E402

FROZEN = ROOT / "datasets" / "ollb" / "frozen"
FULL = ROOT / "datasets" / "ollb" / "frozen_full"   # hash-verified full lists
SAMPLES = ["primary_sample_cap40", "expanded_sample_cap40"]


def recorded_hashes() -> dict[str, str]:
    text = (ROOT / "results" / "exp04_rosters" / "comparison.md").read_text()
    return dict(re.findall(r"- `([\w]+)\.csv`: `([0-9a-f]{64})`", text))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="pilot: first N models")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    want = recorded_hashes()
    frames = {}
    for name in SAMPLES:
        path = FULL / f"{name}.csv"
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want.get(name):
            print(f"ABORT: {path} hash {got} != recorded {want.get(name)}")
            return 2
        frames[name] = pd.read_csv(path)
        print(f"verified {name}: {len(frames[name])} models, sha256 {got[:12]}…")

    p, x = frames[SAMPLES[0]], frames[SAMPLES[1]]
    union = (pd.concat([p[["repo", "model"]], x[["repo", "model"]]])
             .drop_duplicates("model").sort_values("model").reset_index(drop=True))
    union["in_primary_sample"] = union.model.isin(p.model)
    union["in_expanded_sample"] = union.model.isin(x.model)
    union.to_csv(FROZEN / "download_union.csv", index=False)
    print(f"download list: {len(union)} models "
          f"(primary {union.in_primary_sample.sum()}, "
          f"expanded {union.in_expanded_sample.sum()})")

    ref_repo = "details_" + fetch_v1.REFERENCE.stem
    if not fetch_v1.REFERENCE.exists():
        rec = fetch_v1.fetch_model(ref_repo)
        fetch_v1.REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        with open(fetch_v1.OUT.parent / "fetch_v1_log.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"reference {ref_repo}: {rec['status']}")
    if not (fetch_v1.REFERENCE.exists()
            and len(np.load(fetch_v1.REFERENCE)["item"]) == fetch_v1.N_ITEMS):
        print(f"ABORT: reference answers {fetch_v1.REFERENCE} missing or incomplete")
        return 2

    repos = union.repo.tolist()
    if args.limit:
        repos = repos[: args.limit]
    return fetch_v1.main(["--workers", str(args.workers)]
                         + [a for r in repos for a in ("--repo", r)])


if __name__ == "__main__":
    raise SystemExit(main())
