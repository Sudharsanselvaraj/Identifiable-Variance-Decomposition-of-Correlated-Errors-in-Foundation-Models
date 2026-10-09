#!/usr/bin/env python3
"""Size the Exp04 sample with the pair-level gate (no real outcomes used).

For each sample size N, draws an outcome-independent sample from the eligible
roster (shuffle with a fixed seed, cap models per lineage root), then simulates
null / lineage-only / era-only / both truths at several effect sizes and
records separation, calibration and power of the lineage and era terms.

Usage (repo root):
    python3 scripts/run_pair_gate.py --roster datasets/ollb/v1_roster.csv
Output: results/pair_gate/{gate_runs.csv, power.csv, summary.md}
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lineage_era.ollb.pair_gate import Truth, run, summarize  # noqa: E402

OUT = ROOT / "results" / "pair_gate"


def population(roster: pd.DataFrame, which: str) -> pd.DataFrame:
    """Eligible models of one frozen population with a common 'root' column."""
    if which == "expanded":
        e = roster[roster.eligible_expanded].assign(root=lambda d: d.root_x)
    else:
        e = roster[roster.eligible_primary]
    return e[e.created_month.notna()]


def sample(pop: pd.DataFrame, n: int, cap: int, seed: int = 0) -> pd.DataFrame:
    e = pop.sample(frac=1, random_state=seed).groupby("root").head(cap)
    return e.head(n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", default="datasets/ollb/v1_roster.csv")
    ap.add_argument("--population", choices=["primary", "expanded"], default="primary")
    ap.add_argument("--sizes", default="200,400,800,1200")
    ap.add_argument("--cap", type=int, default=40, help="max models per root (Amendment 2)")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--items", type=int, default=14042,
                    help="simulated items (= real MMLU item count)")
    args = ap.parse_args()
    pop = population(pd.read_csv(ROOT / args.roster), args.population)
    out = OUT / args.population
    out.mkdir(parents=True, exist_ok=True)

    truths = {"null": Truth()}
    for lam in (0.03, 0.05, 0.10):
        truths[f"lineage_{lam}"] = Truth(lam_L=lam)
        truths[f"era_{lam}"] = Truth(lam_E=lam)
    truths["both_0.05"] = Truth(lam_L=0.05, lam_E=0.05)

    rows = []
    for n in map(int, args.sizes.split(",")):
        s = sample(pop, n, args.cap)
        for label, t in truths.items():
            res = run(s, t, K=args.items, reps=args.reps, seed=n)
            rows.append({"N": len(s), "roots": s.root.nunique(),
                         "months": s.created_month.nunique(), "truth": label,
                         **summarize(res)})
            print(f"N={len(s)} {label}: same_root reject={rows[-1]['same_root_reject5']:.2f} "
                  f"gap0 reject={rows[-1]['gap0_reject5']:.2f}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "power.csv", index=False)
    (out / "summary.md").write_text(
        f"# Pair-gate power: {args.population} population "
        f"(reps={args.reps}, items={args.items}, cap={args.cap})\n\n"
        + df[["N", "roots", "months", "truth", "same_root_mean", "same_root_se_mean",
              "same_root_reject5", "gap0_mean", "gap0_se_mean", "gap0_reject5"]]
        .to_markdown(index=False, floatfmt=".4f") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
