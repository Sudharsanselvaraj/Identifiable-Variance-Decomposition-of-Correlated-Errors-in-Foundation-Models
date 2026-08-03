"""Phase 2 primary model: the θ_P variance partition and θ_M mechanism tables.

θ_P (primary estimand — lineage vs era): REML variance components on the
crossed model-level trait via ``estimator.fit_lpm_vcomp``, converted to
variance shares on the simplex. CIs come from ``estimator.share_ci``
(log-variance MC delta).

θ_M (mechanistic, reported SEPARATELY, never merged into θ_P):
    - era_trend:      per-era mean trait and era BLUP
    - dense_cells:    family BLUP contrasts within the co-released quarters
                      (2024Q2 / 2024Q3 / 2025Q2 from occupancy.DOCUMENTED_STATS)
    - chain_slopes:   per-quarter trait/family-BLUP slope along the verified
                      parent->child fine-tune edges (occupancy.VERIFIED_EDGES)

Outputs (results/phase2/): variance_partition.csv, model_effects.csv,
family_effects.csv, era_effects.csv, era_trend.csv, dense_cell_contrasts.csv,
chain_slopes.csv.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import estimator
from .occupancy import (DOCUMENTED_STATS, QUARTERS, VERIFIED_EDGES)

QINDEX = {q: i for i, q in enumerate(QUARTERS)}


def shares_of(fit: estimator.FitResult) -> dict[str, float]:
    tot = sum(fit.s2.values())
    return {k: float(v / tot) if tot > 0 else 0.0 for k, v in fit.s2.items()}


def variance_partition(df: pd.DataFrame) -> pd.DataFrame:
    """θ_P table: per-component variance, SE, and share (+ log-delta CI)."""
    fit = estimator.fit_lpm_vcomp(df)
    sh = shares_of(fit)
    ci = estimator.share_ci(fit)
    rows = []
    for k in fit.s2:
        est, se = fit.s2[k], fit.se[k]
        lo, hi = ci.get(k, (float("nan"), float("nan")))
        rows.append({
            "component": k, "variance": est, "se": se,
            "share": sh[k], "share_lo": lo, "share_hi": hi,
        })
    return pd.DataFrame(rows), fit


def blups_by_level(df: pd.DataFrame, fit: estimator.FitResult) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-level family and era BLUPs (deduped from the per-row BLUPs)."""
    fam, era = [], []
    for level, blup, col in (("family", "family_blup", "family"), ("era", "era_blup", "era")):
        out = df.assign(blup=fit.blups[level]).groupby(col)["blup"].first().reset_index()
        out.columns = [col, blup]
        (fam if level == "family" else era).append(out)
    fam[0] = fam[0].merge(df.groupby("family")["trait"].mean().reset_index(name="mean_trait"),
                          on="family")
    fam[0] = fam[0].merge(df.groupby("family").size().reset_index(name="n_models"), on="family")
    era[0] = era[0].merge(df.groupby("era")["trait"].mean().reset_index(name="mean_trait"),
                          on="era")
    era[0] = era[0].merge(df.groupby("era").size().reset_index(name="n_models"), on="era")
    return fam[0], era[0]


def theta_m_tables(df: pd.DataFrame, fit: estimator.FitResult) -> dict[str, pd.DataFrame]:
    """θ_M tables: era trend, dense-cell family contrasts, chain slopes."""
    model_eff = pd.DataFrame({
        "full_name": df["full_name"], "family": df["family"], "era": df["era"],
        "trait": df["trait"],
        "family_blup": fit.blups["family"], "era_blup": fit.blups["era"],
    })

    era_trend = df.groupby("era")["trait"].agg(["mean", "size"]).reset_index()
    era_trend.columns = ["era", "mean_trait", "n_models"]
    era_trend = era_trend.merge(
        model_eff.groupby("era")["era_blup"].first().reset_index(), on="era")
    era_trend["era_i"] = era_trend["era"].map(QINDEX)

    dense = []
    for q in DOCUMENTED_STATS["dense_cells"]:
        sub = df[df["era"] == q]
        for _, r in sub.iterrows():
            dense.append({"era": q, "family": r["family"], "full_name": r["full_name"],
                          "trait": r["trait"], "family_blup": float(
                              fit.blups["family"][sub.index.get_loc(r.name)])})
    dense_cells = pd.DataFrame(dense,
                               columns=["era", "family", "full_name", "trait",
                                        "family_blup"])

    chain = []
    for child, parent, _q in VERIFIED_EDGES:
        c = df[df["full_name"] == child]
        p = df[df["full_name"] == parent]
        if c.empty or p.empty:
            continue
        cr, pr = c.iloc[0], p.iloc[0]
        dq = QINDEX[cr["era"]] - QINDEX[pr["era"]]
        if dq <= 0:
            continue
        chain.append({
            "child": child, "parent": parent,
            "child_era": cr["era"], "parent_era": pr["era"],
            "delta_quarters": dq,
            "trait_slope_per_q": (cr["trait"] - pr["trait"]) / dq,
            "family_blup_slope_per_q": (
                fit.blups["family"][c.index[0]] - fit.blups["family"][p.index[0]]) / dq,
        })
    chain_slopes = pd.DataFrame(chain, columns=[
        "child", "parent", "child_era", "parent_era", "delta_quarters",
        "trait_slope_per_q", "family_blup_slope_per_q"])

    return {"model_effects": model_eff, "era_trend": era_trend,
            "dense_cells": dense_cells, "chain_slopes": chain_slopes}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--df", default=None,
                   help="trait table CSV; default results/phase2/trait_table.csv")
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(args.df) if args.df else out_dir / "trait_table.csv"
    if not path.exists():
        p.error(f"{path} not found (run phase2_trait first)")
    df = pd.read_csv(path)
    if "era" not in df.columns:
        p.error("trait table missing 'era' column (run phase2_trait)")

    vp, fit = variance_partition(df)
    vp.to_csv(out_dir / "variance_partition.csv", index=False)
    fam, era = blups_by_level(df, fit)
    fam.to_csv(out_dir / "family_effects.csv", index=False)
    era.to_csv(out_dir / "era_effects.csv", index=False)
    tm = theta_m_tables(df, fit)
    for name, table in tm.items():
        table.to_csv(out_dir / f"{name}.csv", index=False)

    print("θ_P variance partition:")
    for _, r in vp.iterrows():
        print(f"  {r['component']:7s} s2={r['variance']:.4f} "
              f"share={r['share']:.3f} [{r['share_lo']:.3f}, {r['share_hi']:.3f}]")
    print(f"  converged={fit.converged} llf={fit.llf:.2f}")
    print(f"θ_M: era_trend {len(tm['era_trend'])} eras, "
          f"dense cells {len(tm['dense_cells'])}, "
          f"chain edges {len(tm['chain_slopes'])}")
    print(f"-> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
