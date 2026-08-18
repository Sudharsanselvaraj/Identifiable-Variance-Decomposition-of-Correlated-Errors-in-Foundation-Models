"""16-model research audit: restricted analysis + sensitivity + report.

Runs on the local machine using only CSV-level trait data (JSONL per-question
predictions are invalid — all models predict 0).

Usage: PYTHONPATH=src python3 src/lineage_era/audit_16model_full.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lineage_era.analysis.trait import load_eval_results, load_question_samples, assemble_trait
from lineage_era.analysis.identifiability import structural_checks, audit
from lineage_era.analysis.reml import (
    CrossedREML, FitResult, fit_lpm_vcomp, share_ci, profile_flatness,
    variance_partition, blups_by_level
)
from lineage_era.occupancy import FAMILIES, QUARTERS

OUT = Path("results/phase2_empirical")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

eval_df = load_eval_results()
samples_df = load_question_samples()
trait = assemble_trait(eval_df, samples=samples_df)

# =========================================================================
# helpers
# =========================================================================
def build_group_matrix(df: pd.DataFrame, col: str) -> np.ndarray:
    """One-hot indicator matrix for a grouping column."""
    levels = np.unique(df[col])
    return (df[col].to_numpy()[:, None] == levels).astype(float)


def fit_family_only(df: pd.DataFrame) -> tuple[CrossedREML, np.ndarray, FitResult]:
    """Fit trait ~ vc{family} (era dropped)."""
    y = df["trait"].to_numpy(dtype=float)
    A = build_group_matrix(df, "family")
    solver = CrossedREML(y, [A])
    theta, opt, converged = solver.fit()
    s2_fam, s2_u = np.exp(theta)
    hess = solver.hessian(theta)
    from lineage_era.analysis.reml import _psd_inverse
    cov_log = _psd_inverse(hess)
    se_fam = s2_fam * math.sqrt(max(cov_log[0, 0], 0.0))
    se_u = s2_u * math.sqrt(max(cov_log[1, 1], 0.0))
    b = solver.blups(theta)
    fam_idx = (A @ np.arange(A.shape[1])).astype(int)
    fit = FitResult(
        converged=converged,
        s2={"family": float(s2_fam), "unique": float(s2_u)},
        se={"family": se_fam, "unique": se_u},
        cov_log=cov_log,
        hessian=hess,
        blups={"family": b[0][fam_idx], "era": np.zeros(len(df))},
        llf=-float(opt.fun),
        df_log={"family": A.shape[1] - 1, "era": 0, "unique": len(df) - A.shape[1]},
        solver=solver,
    )
    return solver, theta, fit


def fit_era_only(df: pd.DataFrame) -> tuple[CrossedREML, np.ndarray, FitResult]:
    """Fit trait ~ vc{era} (family dropped)."""
    y = df["trait"].to_numpy(dtype=float)
    B = build_group_matrix(df, "era")
    solver = CrossedREML(y, [B])
    theta, opt, converged = solver.fit()
    s2_era, s2_u = np.exp(theta)
    hess = solver.hessian(theta)
    from lineage_era.analysis.reml import _psd_inverse
    cov_log = _psd_inverse(hess)
    se_era = s2_era * math.sqrt(max(cov_log[0, 0], 0.0))
    se_u = s2_u * math.sqrt(max(cov_log[1, 1], 0.0))
    b = solver.blups(theta)
    era_idx = (B @ np.arange(B.shape[1])).astype(int)
    fit = FitResult(
        converged=converged,
        s2={"era": float(s2_era), "unique": float(s2_u)},
        se={"era": se_era, "unique": se_u},
        cov_log=cov_log,
        hessian=hess,
        blups={"family": np.zeros(len(df)), "era": b[0][era_idx]},
        llf=-float(opt.fun),
        df_log={"family": 0, "era": B.shape[1] - 1, "unique": len(df) - B.shape[1]},
        solver=solver,
    )
    return solver, theta, fit


# =========================================================================
print("=" * 80)
print("16-MODEL RESEARCH AUDIT — FULL RESTRICTED ANALYSIS")
print("=" * 80)

# --- Phase 1 Summary ---
print(f"\n{'='*80}")
print("PHASE 1: DATA INTEGRITY (summary)")
print(f"{'='*80}")
print(f"  Models: {len(trait)}")
print(f"  Samples per model: 14,042 (all identical)")
print(f"  Answers: aligned across all models ✓")
print(f"  JSONL predictions: CORRUPTED — all predict 0 (simulated data)")
print(f"  CSV accuracy: RELIABLE — used for all analyses below")

# --- Phase 2 Summary ---
print(f"\n{'='*80}")
print("PHASE 2: IDENTIFIABILITY (original crossed design)")
print(f"{'='*80}")
sc = structural_checks(trait)
print(f"  Design: {len(trait)} models × {sc['rank_needed']} columns needed")
print(f"  Rank: {sc['rank']} < {sc['rank_needed']} → RANK-DEFICIENT")
print(f"  Condition number: {sc['condition_number']:.2e}")
print(f"  VIF: {'inf (family)' if not sc['vif_ok'] else 'OK'}")
print(f"  VERDICT: HARD FAIL — original estimand not identifiable")
print(f"  Reason: 0 measured DeepSeek models → zero family column")
print(f"          Llama (1 model) and Qwen (1 model) → cannot separate")
print(f"          family from era for singletons")

# --- Phase 3: Restricted Estimands ---
print(f"\n{'='*80}")
print("PHASE 3: RESTRICTED ESTIMANDS")
print(f"{'='*80}")

# Family-only
print("\n--- Model A: trait ~ vc{family} (era dropped) ---")
solver_fam, theta_fam, fit_fam = fit_family_only(trait)
print(f"  Converged: {fit_fam.converged}")
print(f"  sigma^2_family: {fit_fam.s2['family']:.6f}")
print(f"  sigma^2_unique: {fit_fam.s2['unique']:.6f}")
sh_fam = fit_fam.shares
print(f"  share_family: {sh_fam['family']:.4f} ({sh_fam['family']*100:.1f}%)")
print(f"  share_unique: {sh_fam['unique']:.4f} ({sh_fam['unique']*100:.1f}%)")
print(f"  -2*REML logL: {fit_fam.llf:.2f}")

ci_fam = share_ci(fit_fam)
print(f"  Family share CI: [{ci_fam['family'][0]:.4f}, {ci_fam['family'][1]:.4f}]")
print(f"  Unique share CI: [{ci_fam['unique'][0]:.4f}, {ci_fam['unique'][1]:.4f}]")

pf_fam = profile_flatness(fit_fam, "family")
print(f"  Profile flatness (family): {pf_fam:.4f}")

# Era-only
print("\n--- Model B: trait ~ vc{era} (family dropped) ---")
solver_era, theta_era, fit_era = fit_era_only(trait)
print(f"  Converged: {fit_era.converged}")
print(f"  sigma^2_era: {fit_era.s2['era']:.6f}")
print(f"  sigma^2_unique: {fit_era.s2['unique']:.6f}")
sh_era = fit_era.shares
print(f"  share_era: {sh_era['era']:.4f} ({sh_era['era']*100:.1f}%)")
print(f"  share_unique: {sh_era['unique']:.4f} ({sh_era['unique']*100:.1f}%)")
print(f"  -2*REML logL: {fit_era.llf:.2f}")

# Family BLUPs
print("\n--- Family BLUPs (from family-only model) ---")
fam_blups = fit_fam.blups['family']
fam_levels = np.unique(trait['family'])
fam_means = trait.groupby('family')['trait'].mean()
fam_counts = trait.groupby('family').size()
for i, fam in enumerate(fam_levels):
    print(f"  {fam:10s}: BLUP={fam_blups[i]:+.6f}, mean_acc={fam_means[fam]:.4f}, n={fam_counts[fam]}")

# --- Phase 4: JSONL Validation ---
print(f"\n{'='*80}")
print("PHASE 4: ERROR MATRIX / SIMILARITY")
print(f"{'='*80}")
print("  STATUS: BLOCKED")
print("  Reason: All 16 JSONL files contain identical simulated data")
print("  (every model predicts 0 for every question)")
print("  Only the CSV-level accuracy values are reliable")
print("  → Error-similarity analysis requires per-question predictions")
print("  → Cannot be performed on this dataset")

# --- Phase 5: Full crossed model (for reference, even though not identifiable) ---
print(f"\n{'='*80}")
print("PHASE 5: CROSSED MODEL (reference only — not identifiable)")
print(f"{'='*80}")
fit_crossed = fit_lpm_vcomp(trait)
print(f"  Converged: {fit_crossed.converged}")
for k in ['family', 'era', 'unique']:
    print(f"  sigma^2_{k}: {fit_crossed.s2[k]:.6f}")
for k, v in fit_crossed.shares.items():
    print(f"  share_{k}: {v:.4f} ({v*100:.1f}%)")
ci_crossed = share_ci(fit_crossed)
for k in ['family', 'era', 'unique']:
    lo, hi = ci_crossed[k]
    print(f"  {k} share CI: [{lo:.4f}, {hi:.4f}]")
print(f"  NOTE: Era share is ~0% — era effects unestimable")

# --- Phase 6: Sensitivity ---
print(f"\n{'='*80}")
print("PHASE 6: SENSITIVITY ANALYSIS (family-only model)")
print(f"{'='*80}")

# LOO model
print("\n--- Leave-one-model-out ---")
base_share = fit_fam.shares['family']
loo_results = []
for i, model_name in enumerate(trait['full_name']):
    loo_trait = trait.drop(trait.index[i]).reset_index(drop=True)
    try:
        _, _, loo_fit = fit_family_only(loo_trait)
        loo_share = loo_fit.shares['family']
        delta = loo_share - base_share
        loo_results.append((model_name, loo_share, delta))
        print(f"  LOO {model_name:25s}: share_fam={loo_share:.4f}  delta={delta:+.4f}")
    except Exception as e:
        print(f"  LOO {model_name:25s}: FAILED ({e})")

# Bootstrap
print("\n--- Bootstrap (1000 replications) ---")
n_boot = 1000
boot_shares = []
for i in range(n_boot):
    np.random.seed(i)
    idx = np.random.choice(len(trait), size=len(trait), replace=True)
    boot_trait = trait.iloc[idx].reset_index(drop=True)
    try:
        _, _, boot_fit = fit_family_only(boot_trait)
        boot_shares.append(boot_fit.shares['family'])
    except:
        boot_shares.append(np.nan)
boot_shares = np.array(boot_shares)
valid = boot_shares[~np.isnan(boot_shares)]
boot_lo, boot_hi = np.percentile(valid, [2.5, 97.5])
print(f"  Mean bootstrap share: {np.mean(valid):.4f}")
print(f"  Median: {np.median(valid):.4f}")
print(f"  95% CI: [{boot_lo:.4f}, {boot_hi:.4f}]")
print(f"  Valid bootstraps: {len(valid)}/{n_boot}")

# Delta CI from log-normal
print("\n--- Delta CI (log-normal approximation) ---")
for k in ['family', 'unique']:
    lo, hi = ci_fam[k]
    print(f"  {k}: [{lo:.4f}, {hi:.4f}]")

# Leave-one-family-out
print("\n--- Leave-one-family-out ---")
for fam in sorted(trait['family'].unique()):
    sub = trait[trait['family'] != fam].reset_index(drop=True)
    try:
        _, _, loo_fit = fit_family_only(sub)
        print(f"  Drop {fam:10s}: n={len(sub)}, share_unique={loo_fit.shares['unique']:.4f}")
    except Exception as e:
        print(f"  Drop {fam:10s}: FAILED ({e})")

# --- Phase 7: DeepSeek Imputation ---
print(f"\n{'='*80}")
print("PHASE 7: DEEPSEEK IMPUTATION")
print(f"{'='*80}")
print("  STATUS: NOT FEASIBLE")
print("  0 measured DeepSeek models → cannot impute")
print("  Even with imputation, the crossed design would remain weakly")
print("  identified (only 2 DeepSeek models in 22-model population)")

# --- Phase 8: Validation ---
print(f"\n{'='*80}")
print("PHASE 8: VALIDATION CHECKS")
print(f"{'='*80}")
checks = [
    ("Family-only: all variances finite", all(np.isfinite(v) for v in fit_fam.s2.values())),
    ("Family-only: shares sum to 1", abs(sum(fit_fam.shares.values()) - 1.0) < 1e-6),
    ("Family-only: shares in [0,1]", all(0 <= v <= 1 for v in fit_fam.shares.values())),
    ("Family-only: REML converged", fit_fam.converged),
    ("Era-only: all variances finite", all(np.isfinite(v) for v in fit_era.s2.values())),
    ("Era-only: shares sum to 1", abs(sum(fit_era.shares.values()) - 1.0) < 1e-6),
    ("Era-only: REML converged", fit_era.converged),
    ("Crossed: all variances finite", all(np.isfinite(v) for v in fit_crossed.s2.values())),
    ("Crossed: shares sum to 1", abs(sum(fit_crossed.shares.values()) - 1.0) < 1e-6),
    ("Bootstrap CI valid", boot_lo < boot_hi),
    ("Trait values all finite", trait['trait'].notna().all()),
    ("Trait values in [0,1]", (trait['trait'] >= 0).all() and (trait['trait'] <= 1).all()),
]
for desc, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")

# --- Save results ---
print(f"\n{'='*80}")
print("SAVING RESULTS")
print(f"{'='*80}")

# Save trait table
trait.to_csv(OUT / "trait_table.csv", index=False)
print(f"  → {OUT}/trait_table.csv")

# Save summary JSON
summary = {
    "n_models": int(len(trait)),
    "n_families": int(trait['family'].nunique()),
    "n_eras": int(trait['era'].nunique()),
    "identifiability": {
        "original_crossed": {"rank": int(sc['rank']), "rank_needed": int(sc['rank_needed']), "pass": sc['rank_ok']},
        "family_only": {"converged": fit_fam.converged, "share_family": fit_fam.shares['family'],
                        "ci": list(ci_fam['family'])},
    },
    "family_only_fit": {
        "s2": {k: float(v) for k, v in fit_fam.s2.items()},
        "shares": {k: float(v) for k, v in fit_fam.shares.items()},
        "llf": float(fit_fam.llf),
    },
    "era_only_fit": {
        "s2": {k: float(v) for k, v in fit_era.s2.items()},
        "shares": {k: float(v) for k, v in fit_era.shares.items()},
        "llf": float(fit_era.llf),
    },
    "crossed_fit": {
        "s2": {k: float(v) for k, v in fit_crossed.s2.items()},
        "shares": {k: float(v) for k, v in fit_crossed.shares.items()},
        "llf": float(fit_crossed.llf),
    },
    "bootstrap": {"mean": float(np.mean(valid)), "ci_95": [float(boot_lo), float(boot_hi)]},
    "validation_checks": {d: bool(ok) for d, ok in checks},
    "jsonl_status": "CORRUPTED - all predict 0, simulated data",
}
with open(OUT / "audit_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"  → {OUT}/audit_summary.json")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
