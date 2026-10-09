#!/usr/bin/env python3
"""Rebuild the full frozen Exp04 model lists from the public versions.

The public frozen lists (datasets/ollb/frozen/*.csv) omit three fields copied
from the leaderboard's metadata table, which declares no licence: ``type``,
``architecture`` and ``params_b``. This script re-attaches them from a locally
regenerated metadata table (scripts/fetch_v1_contents_meta.py) and writes the
full lists to datasets/ollb/frozen_full/ (gitignored). Each rebuilt file must
match, byte for byte, the SHA-256 recorded when the lists were frozen
(results/exp04_rosters/comparison.md); otherwise the script fails and the
analysis must not be run.

    --strip   (maintainer use) write the public versions from frozen_full/.

Usage (repo root):
    python3 scripts/fetch_v1_contents_meta.py
    python3 scripts/rebuild_frozen_lists.py
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "datasets" / "ollb" / "frozen"
FULL = ROOT / "datasets" / "ollb" / "frozen_full"
META = ROOT / "datasets" / "ollb" / "v1_contents_meta.csv"
NAMES = ["primary", "primary_sample_cap40", "expanded", "expanded_sample_cap40"]
COPIED = ["params_b", "architecture", "type"]


def recorded_hashes() -> dict[str, str]:
    text = (ROOT / "results/exp04_rosters/comparison.md").read_text()
    return dict(re.findall(r"- `([\w]+)\.csv`: `([0-9a-f]{64})`", text))


def metadata() -> pd.DataFrame:
    """The three fields per model, built exactly as roster_v1.build() does."""
    meta = (pd.read_csv(META).drop_duplicates("fullname")
            .rename(columns={"#Params (B)": "params_b"}))
    meta["type"] = [str(t) if isinstance(t, str) else "" for t in meta.Type]
    return meta.rename(columns={"fullname": "model", "Architecture": "architecture"})[
        ["model", "params_b", "architecture", "type"]]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip() -> None:
    for n in NAMES:
        full = pd.read_csv(FULL / f"{n}.csv", keep_default_na=False, dtype=str)
        full.drop(columns=COPIED).to_csv(PUBLIC / f"{n}.csv", index=False)
        print(f"wrote public {n}.csv ({len(full)} rows)")


def rebuild() -> int:
    want = recorded_hashes()
    meta = metadata()
    FULL.mkdir(parents=True, exist_ok=True)
    ok = True
    for n in NAMES:
        pub = pd.read_csv(PUBLIC / f"{n}.csv", keep_default_na=False, dtype=str)
        cols = list(pub.columns)
        order = cols[:5] + COPIED + cols[5:]          # original column order
        full = pub.merge(meta, on="model", how="left", validate="one_to_one")
        if full[COPIED].isna().all(axis=1).any():
            print(f"FAIL {n}: models missing from the metadata table")
            ok = False
            continue
        out = FULL / f"{n}.csv"
        full[order].to_csv(out, index=False)
        match = sha(out) == want[n]
        ok &= match
        print(f"{'OK  ' if match else 'FAIL'} {n}.csv sha256 {sha(out)[:16]}… "
              f"{'matches' if match else 'does NOT match'} the frozen hash")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strip", action="store_true")
    args = ap.parse_args()
    if args.strip:
        strip()
        return 0
    return rebuild()


if __name__ == "__main__":
    sys.exit(main())
