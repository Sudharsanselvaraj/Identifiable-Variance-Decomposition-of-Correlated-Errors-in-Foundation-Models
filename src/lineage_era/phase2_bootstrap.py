"""Phase 2 bootstrap: CIs for the θ_P variance shares.

Two layers, both reported:
    - ``share_ci`` (estimator): Monte-Carlo delta on the fitted log-variance
      covariance (parametric, reflects the REML uncertainty of the design).
    - trait-error MC: per-model trait is perturbed by its measurement error
      (trait_se from the per-question samples / binomial SE) and the model is
      refit each rep; percentiles of the refit shares propagate the trait
      measurement error through the whole decomposition.

Output: results/phase2/bootstrap_ci.csv with component, share, se,
share_lo/share_hi (delta), mc_lo/mc_hi/mc_sd (trait-error MC).

Usage (from src/):
    python3 -m lineage_era.phase2_bootstrap --df results/phase2/trait_table.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import estimator


def trait_error_mc(df: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    """Refit shares under per-model trait measurement error."""
    rng = np.random.default_rng(seed)
    keys = ("family", "era", "unique")
    draws = {k: [] for k in keys}
    y = df["trait"].to_numpy(dtype=float)
    se = df["trait_se"].to_numpy(dtype=float)
    for _ in range(reps):
        yb = y + rng.normal(0.0, se)
        d = df.assign(trait=yb)
        fit = estimator.fit_lpm_vcomp(d)
        tot = sum(fit.s2.values())
        for k in keys:
            draws[k].append(fit.s2[k] / tot if tot > 0 else 0.0)
    rows = []
    for k in keys:
        a = np.asarray(draws[k])
        rows.append({
            "component": k,
            "mc_lo": float(np.percentile(a, 2.5)),
            "mc_hi": float(np.percentile(a, 97.5)),
            "mc_sd": float(np.std(a, ddof=1)),
        })
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--df", default=None,
                   help="trait table CSV; default results/phase2/trait_table.csv")
    p.add_argument("--reps", type=int, default=500)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--se-constant", type=float, default=None,
                   help="constant trait_se to use if the table lacks trait_se")
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(args.df) if args.df else out_dir / "trait_table.csv"
    if not path.exists():
        p.error(f"{path} not found (run phase2_trait first)")
    df = pd.read_csv(path)
    if "trait_se" not in df.columns or df["trait_se"].isna().all():
        if args.se_constant is None:
            p.error("trait table has no usable trait_se; pass --se-constant")
        df["trait_se"] = args.se_constant
    elif df["trait_se"].isna().any():
        if args.se_constant is None:
            p.error("trait_se has missing values; pass --se-constant")
        df["trait_se"] = df["trait_se"].fillna(args.se_constant)

    fit = estimator.fit_lpm_vcomp(df)
    tot = sum(fit.s2.values())
    shares = {k: fit.s2[k] / tot if tot > 0 else 0.0 for k in fit.s2}
    ci = estimator.share_ci(fit)
    mc = trait_error_mc(df, args.reps, args.seed)
    mc = mc.set_index("component")

    rows = []
    for k in ("family", "era", "unique"):
        lo, hi = ci.get(k, (float("nan"), float("nan")))
        rows.append({
            "component": k, "share": shares[k],
            "se": fit.se[k],
            "share_lo": lo, "share_hi": hi,
            "mc_lo": mc.loc[k, "mc_lo"], "mc_hi": mc.loc[k, "mc_hi"],
            "mc_sd": mc.loc[k, "mc_sd"],
        })
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "bootstrap_ci.csv", index=False)
    for _, r in out.iterrows():
        print(f"{r['component']:7s} share={r['share']:.3f} "
              f"delta[{r['share_lo']:.3f},{r['share_hi']:.3f}] "
              f"trait-mc[{r['mc_lo']:.3f},{r['mc_hi']:.3f}]")
    print(f"-> {out_dir / 'bootstrap_ci.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
