#!/usr/bin/env python3
"""High-replication audit of the pair-level simulation gate (post hoc).

The pre-registered gate (scripts/run_pair_gate.py, Amendment 2) used 20
replicates per truth, so its rejection rates move in 5-point steps. This audit
re-runs the same simulation with many more replicates and reports Wilson 95%
intervals for null rejection, cross-leakage and power. It is a robustness check
added after the results were known; it does not replace the dated decision.

Usage (repo root):
    python3 scripts/run_pair_gate_audit.py --population primary --cap 40 --reps 1000
Output: results/pair_gate_audit/<population>_cap<cap>.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb.pair_gate import Truth, run  # noqa: E402
from run_pair_gate import population, sample  # noqa: E402

OUT = ROOT / "results" / "pair_gate_audit"
TERMS = ("same_root", "gap0", "gap1_2")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--population", choices=["primary", "expanded"], default="primary")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261009)
    args = ap.parse_args()
    roster = pd.read_csv(ROOT / "datasets/ollb/v1_roster.csv")
    s = sample(population(roster, args.population), 100000, args.cap)
    truths = {"null": Truth()}
    for lam in (0.03, 0.05, 0.10):
        truths[f"lineage_{lam}"] = Truth(lam_L=lam)
        truths[f"era_{lam}"] = Truth(lam_E=lam)
    truths["both_0.05"] = Truth(lam_L=0.05, lam_E=0.05)
    rows = []
    for k, (label, t) in enumerate(truths.items()):
        res = run(s, t, K=14042, reps=args.reps, seed=args.seed + k)
        for term in TERMS:
            rej = int((np.abs(res[f"b_{term}"] / res[f"se_{term}"]) > 1.96).sum())
            lo, hi = wilson(rej, args.reps)
            rows.append({"population": args.population, "cap": args.cap, "N": len(s),
                         "truth": label, "term": term, "reps": args.reps,
                         "rejections": rej, "rate": rej / args.reps,
                         "ci_low": lo, "ci_high": hi,
                         "mean_estimate": float(res[f"b_{term}"].mean()),
                         "sd_estimate": float(res[f"b_{term}"].std(ddof=1)),
                         "mean_se": float(res[f"se_{term}"].mean())})
        print(f"{label}: " + ", ".join(
            f"{r['term']} {r['rate']:.3f}" for r in rows[-len(TERMS):]), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"{args.population}_cap{args.cap}.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
