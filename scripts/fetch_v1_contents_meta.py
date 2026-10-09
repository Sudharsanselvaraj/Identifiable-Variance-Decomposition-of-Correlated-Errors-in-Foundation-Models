#!/usr/bin/env python3
"""Regenerate datasets/ollb/v1_contents_meta.csv from the public leaderboard.

The leaderboard's contents table (open-llm-leaderboard-old/contents) declares
no licence, so the metadata copy is not redistributed with this repository.
This script re-creates it locally by reading the metadata columns only (the
score columns are never requested), exactly as used to build the Exp04
rosters on 2026-10-09.

Usage (repo root):  python3 scripts/fetch_v1_contents_meta.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "ollb" / "v1_contents_meta.csv"
SOURCE = ("datasets/open-llm-leaderboard-old/contents/data/"
          "train-00000-of-00001-96886cb34a7bc800.parquet")
META_COLS = ["eval_name", "Precision", "Type", "Weight type", "Architecture",
             "fullname", "Model sha", "Hub License", "#Params (B)",
             "Available on the hub", "Merged", "MoE", "Flagged", "date",
             "Chat Template", "Maintainers Choice"]
# SHA-256 of the file used for the frozen rosters (for verification only).
EXPECTED_SHA256 = "84fc02f993a0f14daf8e7d17eddcb806fb1fa8b757e6e7604686049d3560f013"


def main() -> int:
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    with HfFileSystem().open(SOURCE) as fh:
        table = pq.ParquetFile(fh).read(columns=META_COLS).to_pandas()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT, index=False)
    got = hashlib.sha256(OUT.read_bytes()).hexdigest()
    status = "matches" if got == EXPECTED_SHA256 else "DIFFERS FROM"
    print(f"wrote {OUT} ({len(table)} rows); sha256 {got[:16]}… {status} "
          "the file used for the frozen rosters")
    return 0 if got == EXPECTED_SHA256 else 1


if __name__ == "__main__":
    raise SystemExit(main())
