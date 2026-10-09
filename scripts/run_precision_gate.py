#!/usr/bin/env python3
"""Run the random-effects precision gate on every design discussed in the paper.

Compares the original fixed-effects gate (rank / kappa / VIF of [1|Z_F|Z_E])
with the precision gate (covariance-basis rank + Monte Carlo share recovery
under the fitted CrossedREML estimator) on:

  obs16            the 16 models actually evaluated
  obs16_noLlama1   obs16 minus Llama-1 (the paper's rank-restoring removal)
  sel22            the 22-model outcome-independent selection
  cand47           the full 47-model candidate frame
  sweep_F{F}_E{E}_M{M}  staggered designs from run_design_space_sweep.py
  nested72         D3-style nested reference (each family in one era)

Usage (repo root):  python3 scripts/run_precision_gate.py [--reps 200]
Outputs: results/precision_gate/{precision_gate.csv, summary.csv, summary.md}
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

from lineage_era.analysis.precision_gate import (  # noqa: E402
    SHARE_RMSE_MAX, precision_gate)
from lineage_era.occupancy import model_table  # noqa: E402
from run_design_space_sweep import make_staggered  # noqa: E402

OUT = ROOT / "results" / "precision_gate"


def fixed_effects_gate(df: pd.DataFrame) -> dict:
    """Original gate quantities, plus kappa's spread over reference levels."""
    zf = pd.get_dummies(df["family"]).to_numpy(float)
    ze = pd.get_dummies(df["era"]).to_numpy(float)
    p = zf.shape[1] + ze.shape[1] - 1
    X = np.column_stack([np.ones(len(df)), zf[:, :-1], ze[:, :-1]])
    rank = int(np.linalg.matrix_rank(X))
    kappas = []
    if rank == p:
        for i in range(zf.shape[1]):
            for j in range(ze.shape[1]):
                Xr = np.column_stack([np.ones(len(df)), np.delete(zf, i, 1),
                                      np.delete(ze, j, 1)])
                kappas.append(np.linalg.cond(Xr.T @ Xr))
    return {
        "fe_rank": rank, "fe_p": p, "fe_rank_ok": rank == p,
        "fe_kappa_default": float(np.linalg.cond(X.T @ X)),
        "fe_kappa_min_over_ref": float(min(kappas)) if kappas else np.inf,
        "fe_kappa_max_over_ref": float(max(kappas)) if kappas else np.inf,
    }


def designs() -> dict[str, pd.DataFrame]:
    table = model_table().rename(columns={"quarter": "era"})
    evaluated = pd.read_csv(ROOT / "datasets" / "phase2_eval_results.csv")["full_name"]
    sel = pd.read_csv(ROOT / "datasets" / "coverage" / "minimum_valid_population.csv")
    sel22 = sel.loc[sel["kept"].astype(str) == "True", "full_name"]

    out = {
        "obs16": table[table.full_name.isin(evaluated)],
        "obs16_noLlama1": table[table.full_name.isin(evaluated)
                                & (table.full_name != "Llama-1")],
        "sel22": table[table.full_name.isin(sel22)],
        "cand47": table,
    }
    for nf, ne, m in [(5, 8, 6), (6, 8, 5), (7, 8, 6), (6, 8, 3), (6, 12, 5),
                      (6, 14, 5), (5, 8, 2)]:
        rows = [(f"F{f}", f"E{e}") for f, eras in
                enumerate(make_staggered(nf, m, ne)) for e in eras[:m]]
        out[f"sweep_F{nf}_E{ne}_M{m}"] = pd.DataFrame(rows, columns=["family", "era"])
    out["nested72"] = pd.DataFrame([(f"F{f}", f"E{f}") for f in range(6)
                                    for _ in range(12)], columns=["family", "era"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    per_scenario, summary = [], []
    for name, df in designs().items():
        res = precision_gate(df, name=name, reps=args.reps)
        fe = fixed_effects_gate(df)
        per_scenario.append(res.rows.assign(**fe))
        summary.append({
            "design": name, "n": len(df), "families": df.family.nunique(),
            "eras": df.era.nunique(), **fe,
            "basis_rank": res.basis_rank,
            "max_se_share_analytic": float(res.rows[["se_share_family",
                                                     "se_share_era"]].max().max()),
            "worst_share_rmse_mc": res.worst_rmse,
            "precision_gate": ("PASS" if res.reportable else
                               "FAIL (not identified)" if not res.identified
                               else "FAIL (imprecise)"),
        })
        print(f"{name:22s} n={len(df):3d} basis={res.basis_rank} "
              f"fe_rank_ok={fe['fe_rank_ok']!s:5s} worst RMSE={res.worst_rmse:.3f} "
              f"-> {summary[-1]['precision_gate']}", flush=True)

    pd.concat(per_scenario).to_csv(OUT / "precision_gate.csv", index=False)
    s = pd.DataFrame(summary)
    s.to_csv(OUT / "summary.csv", index=False)
    (OUT / "summary.md").write_text(
        f"# Precision gate summary (reps={args.reps}, "
        f"bar: share RMSE <= {SHARE_RMSE_MAX:.2f} in every scenario)\n\n"
        + s.to_markdown(index=False, floatfmt=".3g") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
