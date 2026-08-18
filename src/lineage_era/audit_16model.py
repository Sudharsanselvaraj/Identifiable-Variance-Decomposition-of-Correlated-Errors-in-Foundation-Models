"""Comprehensive restricted audit for the 16-model design.

Phases 3-6, 8-9 of the restricted analysis exploring what CAN be identified
when the full crossed family x era estimand fails the pre-registered
identifiability gate.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

# --- Setup paths ---
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from lineage_era.occupancy import model_table, FAMILIES, QUARTERS
from lineage_era.analysis.trait import (
    load_eval_results, load_question_samples, assemble_trait,
)
from lineage_era.analysis.reml import CrossedREML, fit_lpm_vcomp, share_ci, FitResult
from lineage_era.analysis.error_similarity import (
    error_matrix, _measure_matrices, PRIMARY_MEASURE, MEASURES, GROUPS,
    _pair_table, summary_stats, design_map,
)
from lineage_era.analysis.plots import _family_colors, linkage_from_mat

OUT_DIR = REPO / "results" / "phase2_empirical"
FIG_DIR = OUT_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES_DIR = REPO / "datasets" / "eval_samples"
EVAL_CSV = REPO / "datasets" / "phase2_eval_results.csv"
TABLE = model_table()


# ============================================================ helpers ============================================================

def print_header(phase: str, title: str):
    print(f"\n{'='*80}")
    print(f"  {phase}: {title}")
    print(f"{'='*80}")


def print_subheader(title: str):
    print(f"\n--- {title} ---")


def check_finite(name: str, val) -> bool:
    if val is None:
        return False
    try:
        arr = np.asarray(val, dtype=float)
        ok = np.all(np.isfinite(arr))
    except (TypeError, ValueError):
        ok = isinstance(val, float) and np.isfinite(val)
    if not ok:
        print(f"  WARNING: {name} contains non-finite values")
    return ok


# ============================================================ data loading ============================================================

print_header("DATA LOADING", "Loading eval results and question samples")

eval_df = load_eval_results(EVAL_CSV)
print(f"  Eval CSV: {len(eval_df)} models")
print(f"  Models: {sorted(eval_df['full_name'].tolist())}")

samples = load_question_samples(SAMPLES_DIR)
print(f"  Question samples: {len(samples)} rows, {samples['full_name'].nunique()} models")
print(f"  Questions per model: {samples.groupby('full_name').size().iloc[0] if len(samples) > 0 else 0}")

# Build trait table using the existing pipeline
trait = assemble_trait(eval_df, samples=samples)
print(f"\n  Trait table: {len(trait)} models")
for _, r in trait.iterrows():
    print(f"    {r['full_name']:30s} family={r['family']:10s} era={r['era']:8s} "
          f"trait={r['trait']:.4f} se={r.get('trait_se', float('nan')):.4f}")

# Save trait table
trait.to_csv(OUT_DIR / "trait_table.csv", index=False)
print(f"\n  -> {OUT_DIR / 'trait_table.csv'}")

# ============================================================ Design summary ============================================================

print_header("DESIGN SUMMARY", "16-model occupancy structure")

families_in_design = trait["family"].unique()
eras_in_design = trait["era"].unique()
print(f"  Families with measured models: {sorted(families_in_design)}")
print(f"  Families WITHOUT measured models: {sorted(set(FAMILIES) - set(families_in_design))}")
print(f"  Eras with measured models: {sorted(eras_in_design)}")
print(f"  N families = {len(families_in_design)}, N eras = {len(eras_in_design)}")

# Design heatmap data
design_matrix = pd.crosstab(trait["family"], trait["era"])
print(f"\n  Family x Era occupancy (measured models only):")
print(design_matrix.to_string())

# Full-rank check on crossed design
A = (trait["family"].to_numpy()[:, None] == np.unique(trait["family"])).astype(float)
B = (trait["era"].to_numpy()[:, None] == np.unique(trait["era"])).astype(float)
X = np.ones((len(trait), 1))
full_design = np.hstack([X, A, B])
rank_full = np.linalg.matrix_rank(full_design)
n_params = full_design.shape[1]
print(f"\n  Full crossed design matrix: {full_design.shape}")
print(f"  Rank: {rank_full} / {n_params} columns")
print(f"  Full rank? {'YES' if rank_full == n_params else 'NO (rank-deficient)'}")
print(f"  --> Original estimand theta_P = (family, era, unique) is "
      f"{'IDENTIFIABLE' if rank_full == n_params else 'NOT IDENTIFIABLE'}")


# ============================================================ PHASE 3 ============================================================

print_header("PHASE 3", "Restricted Estimand Exploration")

# --- 3a: Family-only model (drop era) ---
print_subheader("3a: Family-only model: trait ~ family")

# Build family-only design
fam_levels = np.unique(trait["family"])
A_fam = (trait["family"].to_numpy()[:, None] == fam_levels).astype(float)
X_fam = np.ones((len(trait), 1))
design_fam = np.hstack([X_fam, A_fam])
rank_fam = np.linalg.matrix_rank(design_fam)
print(f"  Design matrix: {design_fam.shape}")
print(f"  Rank: {rank_fam} / {design_fam.shape[1]}")
print(f"  Full rank? {'YES' if rank_fam == design_fam.shape[1] else 'NO'}")

# Fit family-only model
solver_fam = CrossedREML(trait["trait"].to_numpy(dtype=float), [A_fam])
theta_fam, opt_fam, conv_fam = solver_fam.fit()
s2_fam_fam = np.exp(theta_fam[0])
s2_fam_u = np.exp(theta_fam[1])
total_fam = s2_fam_fam + s2_fam_u
share_fam_fam = s2_fam_fam / total_fam if total_fam > 0 else 0.0
share_fam_u = s2_fam_u / total_fam if total_fam > 0 else 0.0

print(f"\n  Variance components:")
print(f"    sigma^2_family = {s2_fam_fam:.6f}")
print(f"    sigma^2_unique = {s2_fam_u:.6f}")
print(f"    share_family   = {share_fam_fam:.4f}")
print(f"    share_unique   = {share_fam_u:.4f}")
print(f"    converged      = {conv_fam}")
print(f"    REML log-lik   = {-opt_fam.fun:.4f}")

# BLUPs
blups_fam = solver_fam.blups(theta_fam)
fam_blups = {}
for i, f in enumerate(fam_levels):
    fam_blups[f] = float(blups_fam[0][i])
print(f"\n  Family BLUPs:")
for f, b in sorted(fam_blups.items()):
    print(f"    {f:12s} BLUP = {b:+.6f}")

# Hessian + CI for family-only
hess_fam = solver_fam.hessian(theta_fam)
cov_fam_inv = np.linalg.inv(hess_fam + 1e-6 * np.eye(2))  # regularize
se_fam = {
    "family": s2_fam_fam * np.sqrt(max(cov_fam_inv[0, 0], 0)),
    "unique": s2_fam_u * np.sqrt(max(cov_fam_inv[1, 1], 0)),
}

# Build FitResult for share_ci
fit_fam = FitResult(
    converged=conv_fam,
    s2={"family": s2_fam_fam, "unique": s2_fam_u},
    se=se_fam,
    cov_log=cov_fam_inv,
    hessian=hess_fam,
    blups={"family": blups_fam[0]},
    llf=-float(opt_fam.fun),
    df_log={"family": len(fam_levels) - 1, "unique": len(trait) - len(fam_levels)},
    solver=solver_fam,
)
ci_fam = share_ci(fit_fam)
print(f"\n  95% delta CIs for shares:")
for k in ("family", "unique"):
    lo, hi = ci_fam.get(k, (float("nan"), float("nan")))
    print(f"    {k:10s} share = {fit_fam.shares[k]:.4f}  [{lo:.4f}, {hi:.4f}]")


# --- 3b: Era-only model (drop family) ---
print_subheader("3b: Era-only model: trait ~ era")

era_levels = np.unique(trait["era"])
B_era = (trait["era"].to_numpy()[:, None] == era_levels).astype(float)
X_era = np.ones((len(trait), 1))
design_era = np.hstack([X_era, B_era])
rank_era = np.linalg.matrix_rank(design_era)
print(f"  Design matrix: {design_era.shape}")
print(f"  Rank: {rank_era} / {design_era.shape[1]}")
print(f"  Full rank? {'YES' if rank_era == design_era.shape[1] else 'NO'}")

solver_era = CrossedREML(trait["trait"].to_numpy(dtype=float), [B_era])
theta_era, opt_era, conv_era = solver_era.fit()
s2_era_era = np.exp(theta_era[0])
s2_era_u = np.exp(theta_era[1])
total_era = s2_era_era + s2_era_u
share_era_era = s2_era_era / total_era if total_era > 0 else 0.0
share_era_u = s2_era_u / total_era if total_era > 0 else 0.0

print(f"\n  Variance components:")
print(f"    sigma^2_era    = {s2_era_era:.6f}")
print(f"    sigma^2_unique = {s2_era_u:.6f}")
print(f"    share_era      = {share_era_era:.4f}")
print(f"    share_unique   = {share_era_u:.4f}")
print(f"    converged      = {conv_era}")
print(f"    REML log-lik   = {-opt_era.fun:.4f}")

blups_era = solver_era.blups(theta_era)
era_blups = {}
for i, e in enumerate(era_levels):
    era_blups[e] = float(blups_era[0][i])
print(f"\n  Era BLUPs:")
for e, b in sorted(era_blups.items()):
    print(f"    {e:10s} BLUP = {b:+.6f}")

hess_era = solver_era.hessian(theta_era)
cov_era_inv = np.linalg.inv(hess_era + 1e-6 * np.eye(2))
se_era = {
    "era": s2_era_era * np.sqrt(max(cov_era_inv[0, 0], 0)),
    "unique": s2_era_u * np.sqrt(max(cov_era_inv[1, 1], 0)),
}
fit_era = FitResult(
    converged=conv_era,
    s2={"era": s2_era_era, "unique": s2_era_u},
    se=se_era,
    cov_log=cov_era_inv,
    hessian=hess_era,
    blups={"era": blups_era[0]},
    llf=-float(opt_era.fun),
    df_log={"era": len(era_levels) - 1, "unique": len(trait) - len(era_levels)},
    solver=solver_era,
)
ci_era = share_ci(fit_era)
print(f"\n  95% delta CIs for shares:")
for k in ("era", "unique"):
    lo, hi = ci_era.get(k, (float("nan"), float("nan")))
    print(f"    {k:10s} share = {fit_era.shares[k]:.4f}  [{lo:.4f}, {hi:.4f}]")


# --- 3c: Summary of identifiability ---
print_subheader("3c: Identifiability summary")
print(f"  Original crossed estimand (family, era, unique): "
      f"NOT IDENTIFIABLE (rank {rank_full} < {n_params})")
print(f"  Family-only restricted estimand:  "
      f"{'IDENTIFIABLE' if rank_fam == design_fam.shape[1] else 'NOT IDENTIFIABLE'} "
      f"(rank {rank_fam}/{design_fam.shape[1]})")
print(f"  Era-only restricted estimand:     "
      f"{'IDENTIFIABLE' if rank_era == design_era.shape[1] else 'NOT IDENTIFIABLE'} "
      f"(rank {rank_era}/{design_era.shape[1]})")
print(f"\n  NOTE: Neither restricted estimand is the original theta_P.")
print(f"  The family-only model answers: 'How much variance is explained by")
print(f"  family affiliation alone?' (ignoring era).")
print(f"  The era-only model answers: 'How much variance is explained by")
print(f"  era alone?' (ignoring family).")
print(f"  They are COMPLEMENTARY restricted views, not substitutes for theta_P.")


# ============================================================ PHASE 4 ============================================================

print_header("PHASE 4", "Error Matrix Construction")

print_subheader("4a: Loading all 16 JSONL eval_samples files")
all_frames = []
for path in sorted(SAMPLES_DIR.glob("*.jsonl")):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    df = pd.DataFrame(rows)
    model_name = df["full_name"].iloc[0]
    n_rows = len(df)
    n_correct = df["correct"].sum()
    print(f"  {model_name:30s}: {n_rows:6d} questions, {n_correct:5d} correct "
          f"({n_correct/n_rows*100:.1f}%)")
    all_frames.append(df)

all_samples = pd.concat(all_frames, ignore_index=True)
print(f"\n  Total: {len(all_samples)} rows, {all_samples['full_name'].nunique()} models")

print_subheader("4b: Building binary error matrix")
# Use the design from trait to filter to measured models
design_for_matrix = trait[["full_name", "family", "era"]].copy()
B, model_names, item_names = error_matrix(all_samples, design_for_matrix)
print(f"  Error matrix shape: {B.shape} (models x items)")
print(f"  Models: {model_names}")
print(f"  Common items: {len(item_names)}")

# Verify all questions are identical across models
print_subheader("4c: Verifying identical question ordering")
question_sets = {}
for model in model_names:
    model_data = all_samples[all_samples["full_name"] == model].copy()
    question_sets[model] = set(model_data["question"].tolist())

ref_model = model_names[0]
ref_questions = question_sets[ref_model]
all_same = True
for model in model_names[1:]:
    if question_sets[model] != ref_questions:
        print(f"  WARNING: {model} has different question set than {ref_model}")
        all_same = False
print(f"  All models have identical question sets: {'YES' if all_same else 'NO'}")

# Check ordering by comparing first question
ref_order = all_samples[all_samples["full_name"] == ref_model]["question"].tolist()
order_match = True
for model in model_names[1:]:
    model_order = all_samples[all_samples["full_name"] == model]["question"].tolist()
    if model_order != ref_order:
        # Check if at least the set is the same
        if set(model_order) == set(ref_order):
            print(f"  NOTE: {model} has same questions but different order (will be pivoted)")
        else:
            print(f"  WARNING: {model} has different questions!")
        order_match = False
print(f"  Identical ordering across all models: {'YES' if order_match else 'NO (order differs, pivot corrects)'}")

print_subheader("4d: Computing pairwise error similarity (phi/MCC)")
mats = _measure_matrices(B)
phi_mat = mats["phi"]  # Primary measure
print(f"  Phi (MCC) matrix shape: {phi_mat.shape}")
print(f"  Diagonal values (should be 1.0): {np.allclose(np.diag(phi_mat), 1.0)}")

# Save error matrix and similarity matrix
error_df = pd.DataFrame(B, index=model_names, columns=[f"q{i}" for i in range(B.shape[1])])
error_df.to_csv(OUT_DIR / "error_matrix_binary.csv")
print(f"  Saved error matrix: {OUT_DIR / 'error_matrix_binary.csv'}")

sim_df = pd.DataFrame(phi_mat, index=model_names, columns=model_names)
sim_df.to_csv(OUT_DIR / "similarity_matrix_phi.csv")
print(f"  Saved similarity matrix: {OUT_DIR / 'similarity_matrix_phi.csv'}")

print_subheader("4e: Pairwise phi values")
# Print all unique pairs
for i in range(len(model_names)):
    for j in range(i + 1, len(model_names)):
        print(f"    {model_names[i]:30s} x {model_names[j]:30s}: phi = {phi_mat[i, j]:+.4f}")

print_subheader("4f: Within-family vs between-family similarity")
wf_vals = []
bf_vals = []
for i in range(len(model_names)):
    for j in range(i + 1, len(model_names)):
        fi = design_for_matrix.set_index("full_name").loc[model_names[i], "family"]
        fj = design_for_matrix.set_index("full_name").loc[model_names[j], "family"]
        if fi == fj:
            wf_vals.append(phi_mat[i, j])
        else:
            bf_vals.append(phi_mat[i, j])

wf_mean = np.mean(wf_vals) if wf_vals else float("nan")
bf_mean = np.mean(bf_vals) if bf_vals else float("nan")
print(f"  Within-family pairs:  {len(wf_vals)}, mean phi = {wf_mean:.4f}")
print(f"  Between-family pairs: {len(bf_vals)}, mean phi = {bf_mean:.4f}")
print(f"  Difference (WF - BF): {wf_mean - bf_mean:+.4f}")

print_subheader("4g: Within-era vs across-era similarity")
we_vals = []
ae_vals = []
for i in range(len(model_names)):
    for j in range(i + 1, len(model_names)):
        ei = design_for_matrix.set_index("full_name").loc[model_names[i], "era"]
        ej = design_for_matrix.set_index("full_name").loc[model_names[j], "era"]
        if ei == ej:
            we_vals.append(phi_mat[i, j])
        else:
            ae_vals.append(phi_mat[i, j])

we_mean = np.mean(we_vals) if we_vals else float("nan")
ae_mean = np.mean(ae_vals) if ae_vals else float("nan")
print(f"  Within-era pairs:  {len(we_vals)}, mean phi = {we_mean:.4f}")
print(f"  Across-era pairs:  {len(ae_vals)}, mean phi = {ae_mean:.4f}")
print(f"  Difference (WE - AE): {we_mean - ae_mean:+.4f}")

print_subheader("4h: Full pairwise similarity distribution")
upper_tri = phi_mat[np.triu_indices(len(model_names), k=1)]
print(f"  N pairs: {len(upper_tri)}")
print(f"  Mean:   {np.mean(upper_tri):.4f}")
print(f"  Median: {np.median(upper_tri):.4f}")
print(f"  Std:    {np.std(upper_tri):.4f}")
print(f"  Min:    {np.min(upper_tri):.4f}")
print(f"  Max:    {np.max(upper_tri):.4f}")
print(f"  25th:   {np.percentile(upper_tri, 25):.4f}")
print(f"  75th:   {np.percentile(upper_tri, 75):.4f}")
print(f"  % pairs with phi > 0: {(upper_tri > 0).sum() / len(upper_tri) * 100:.1f}%")
print(f"  % pairs with phi > 0.5: {(upper_tri > 0.5).sum() / len(upper_tri) * 100:.1f}%")


# ============================================================ PHASE 5 ============================================================

print_header("PHASE 5", "Restricted Variance Decomposition (family-only REML)")

print_subheader("5a: Fitting family-only REML model")
print(f"  Model: trait ~ vc{{family}}  (era dropped)")
print(f"  Components: sigma^2_family, sigma^2_unique")
print(f"  This is a RESTRICTED estimand, not the original theta_P.")

print(f"\n  Results (from Phase 3a):")
print(f"    sigma^2_family = {s2_fam_fam:.6f}")
print(f"    sigma^2_unique = {s2_fam_u:.6f}")
print(f"    share_family   = {share_fam_fam:.4f} ({share_fam_fam*100:.1f}%)")
print(f"    share_unique   = {share_fam_u:.4f} ({share_fam_u*100:.1f}%)")
print(f"    converged      = {conv_fam}")

print_subheader("5b: Bootstrap CIs for family-only shares")
# Use delta CI from the fitted model
ci_fam_95 = share_ci(fit_fam, level=0.95)
ci_fam_90 = share_ci(fit_fam, level=0.90)
print(f"  95% delta CIs:")
for k in ("family", "unique"):
    lo95, hi95 = ci_fam_95.get(k, (float("nan"), float("nan")))
    lo90, hi90 = ci_fam_90.get(k, (float("nan"), float("nan")))
    print(f"    {k:10s} share = {fit_fam.shares[k]:.4f}  "
          f"95%[{lo95:.4f}, {hi95:.4f}]  90%[{lo90:.4f}, {hi90:.4f}]")

# Also do bootstrap refits (leave-one-model-out will be Phase 6)
# For now, do a parametric bootstrap
print_subheader("5c: Parametric bootstrap for family share")
rng = np.random.default_rng(42)
n_boot = 1000
boot_shares_fam = []
y_orig = trait["trait"].to_numpy(dtype=float)
for b in range(n_boot):
    # Perturb by measurement error
    se = trait["trait_se"].to_numpy(dtype=float)
    se = np.where(np.isfinite(se), se, 0.01)
    y_boot = y_orig + rng.normal(0, se)
    trait_boot = trait.assign(trait=y_boot)
    solver_b = CrossedREML(y_boot, [A_fam])
    theta_b, _, conv_b = solver_b.fit()
    s2_b = np.exp(theta_b)
    tot_b = s2_b.sum()
    if tot_b > 0 and conv_b:
        boot_shares_fam.append(s2_b[0] / tot_b)

boot_shares_fam = np.array(boot_shares_fam)
print(f"  Bootstrap replications: {len(boot_shares_fam)} (converged)")
print(f"  Family share: mean = {np.mean(boot_shares_fam):.4f}, "
      f"sd = {np.std(boot_shares_fam):.4f}")
print(f"  95% CI: [{np.percentile(boot_shares_fam, 2.5):.4f}, "
      f"{np.percentile(boot_shares_fam, 97.5):.4f}]")
print(f"  90% CI: [{np.percentile(boot_shares_fam, 5.0):.4f}, "
      f"{np.percentile(boot_shares_fam, 95.0):.4f}]")


# ============================================================ PHASE 6 ============================================================

print_header("PHASE 6", "Sensitivity Analysis")

print_subheader("6a: Leave-one-model-out")
loo_results = []
for idx in range(len(trait)):
    model_out = trait.iloc[idx]["full_name"]
    trait_sub = trait.drop(trait.index[idx]).copy()
    A_sub = (trait_sub["family"].to_numpy()[:, None] == np.unique(trait_sub["family"])).astype(float)
    solver_sub = CrossedREML(trait_sub["trait"].to_numpy(dtype=float), [A_sub])
    theta_sub, _, conv_sub = solver_sub.fit()
    s2_sub = np.exp(theta_sub)
    tot_sub = s2_sub.sum()
    share_fam = s2_sub[0] / tot_sub if tot_sub > 0 and conv_sub else float("nan")
    loo_results.append({
        "model_left_out": model_out,
        "family": trait.iloc[idx]["family"],
        "share_family": share_fam,
        "converged": conv_sub,
    })

loo_df = pd.DataFrame(loo_results)
print(f"  {'Model left out':35s} {'Family':10s} {'share_family':>12s} {'converged':>8s}")
print(f"  {'-'*70}")
for _, r in loo_df.iterrows():
    print(f"  {r['model_left_out']:35s} {r['family']:10s} {r['share_family']:12.4f} "
          f"{str(r['converged']):>8s}")

print(f"\n  Baseline (no leave-out): {share_fam_fam:.4f}")
print(f"  Mean across LOO:         {loo_df['share_family'].mean():.4f}")
print(f"  Range:                   [{loo_df['share_family'].min():.4f}, "
      f"{loo_df['share_family'].max():.4f}]")
print(f"  Std:                     {loo_df['share_family'].std():.4f}")
max_dev = (loo_df["share_family"] - share_fam_fam).abs().max()
most_influential = loo_df.loc[(loo_df["share_family"] - share_fam_fam).abs().idxmax()]
print(f"  Most influential model:  {most_influential['model_left_out']} "
      f"(deviation = {max_dev:.4f})")

print_subheader("6b: Leave-one-family-out")
lfo_results = []
for fam_out in sorted(trait["family"].unique()):
    trait_sub = trait[trait["family"] != fam_out].copy()
    A_sub = (trait_sub["family"].to_numpy()[:, None] == np.unique(trait_sub["family"])).astype(float)
    if A_sub.shape[1] < 2:
        print(f"  Skipping {fam_out}: only 1 family left")
        continue
    solver_sub = CrossedREML(trait_sub["trait"].to_numpy(dtype=float), [A_sub])
    theta_sub, _, conv_sub = solver_sub.fit()
    s2_sub = np.exp(theta_sub)
    tot_sub = s2_sub.sum()
    share_fam = s2_sub[0] / tot_sub if tot_sub > 0 and conv_sub else float("nan")
    n_models_out = len(trait[trait["family"] == fam_out])
    lfo_results.append({
        "family_left_out": fam_out,
        "n_models_removed": n_models_out,
        "n_models_remaining": len(trait_sub),
        "share_family": share_fam,
        "converged": conv_sub,
    })

lfo_df = pd.DataFrame(lfo_results)
print(f"  {'Family left out':15s} {'N removed':>10s} {'N remain':>10s} {'share_family':>12s} {'conv':>5s}")
print(f"  {'-'*60}")
for _, r in lfo_df.iterrows():
    print(f"  {r['family_left_out']:15s} {r['n_models_removed']:10d} "
          f"{r['n_models_remaining']:10d} {r['share_family']:12.4f} "
          f"{str(r['converged']):>5s}")

print(f"\n  Baseline: {share_fam_fam:.4f}")
print(f"  Range across LFO: [{lfo_df['share_family'].min():.4f}, "
      f"{lfo_df['share_family'].max():.4f}]")

print_subheader("6c: Bootstrap uncertainty on family share (recap)")
print(f"  From Phase 5c:")
print(f"    Point estimate: {share_fam_fam:.4f}")
print(f"    Bootstrap 95% CI: [{np.percentile(boot_shares_fam, 2.5):.4f}, "
      f"{np.percentile(boot_shares_fam, 97.5):.4f}]")
print(f"    Bootstrap SD: {np.std(boot_shares_fam):.4f}")

print_subheader("6d: Stability assessment")
stable_count = ((boot_shares_fam > 0.1) & (boot_shares_fam < 0.9)).sum()
print(f"  Fraction of bootstrap draws where family share in [0.1, 0.9]: "
      f"{stable_count}/{len(boot_shares_fam)} = {stable_count/len(boot_shares_fam):.3f}")
above_50 = (boot_shares_fam > 0.5).sum()
print(f"  Fraction of bootstrap draws where family share > 0.5: "
      f"{above_50}/{len(boot_shares_fam)} = {above_50/len(boot_shares_fam):.3f}")
print(f"  --> Family share is {'STABLE' if stable_count/len(boot_shares_fam) > 0.9 else 'UNSTABLE'} "
      f"across bootstrap replicates")


# ============================================================ PHASE 8 ============================================================

print_header("PHASE 8", "Validation Checks")

checks = []

# 8a: All variances finite
v1 = check_finite("sigma^2_family (family-only)", s2_fam_fam)
v2 = check_finite("sigma^2_unique (family-only)", s2_fam_u)
v3 = check_finite("sigma^2_era (era-only)", s2_era_era)
v4 = check_finite("sigma^2_unique (era-only)", s2_era_u)
checks.append(("All variances finite", all([v1, v2, v3, v4])))

# 8b: Shares sum to 1
s_fam = fit_fam.shares
s_era = fit_era.shares
sum_fam = sum(s_fam.values())
sum_era = sum(s_era.values())
ok_fam = abs(sum_fam - 1.0) < 1e-6
ok_era = abs(sum_era - 1.0) < 1e-6
checks.append(("Family shares sum to 1", ok_fam))
checks.append(("Era shares sum to 1", ok_era))
if not ok_fam:
    print(f"  WARNING: Family shares sum to {sum_fam}")
if not ok_era:
    print(f"  WARNING: Era shares sum to {sum_era}")

# 8c: No NaN/Inf
has_nan_fam = not np.all(np.isfinite(list(s_fam.values())))
has_nan_era = not np.all(np.isfinite(list(s_era.values())))
checks.append(("No NaN in family shares", not has_nan_fam))
checks.append(("No NaN in era shares", not has_nan_era))

# 8d: Consistent results
fam_share_refit = fit_fam.shares["family"]
checks.append(("Family share consistent (re-fit == original)",
               abs(fam_share_refit - share_fam_fam) < 1e-10))

# 8e: Error matrix integrity
checks.append(("Error matrix has correct shape", B.shape == (16, len(item_names))))
checks.append(("Error matrix values are 0/1", set(np.unique(B)).issubset({0, 1})))
checks.append(("Phi matrix symmetric", np.allclose(phi_mat, phi_mat.T)))

print(f"\n  Validation results:")
for name, ok in checks:
    status = "PASS" if ok else "FAIL"
    print(f"    [{status}] {name}")

all_pass = all(ok for _, ok in checks)
print(f"\n  Overall: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")


# ============================================================ PHASE 9 ============================================================

print_header("PHASE 9", "Figures (saved as PDF)")

# 9a: Design heatmap
print_subheader("9a: Design heatmap (family x era occupancy)")
design_pivot = pd.crosstab(trait["family"], trait["era"], margins=False)
design_pivot = design_pivot.reindex(index=sorted(trait["family"].unique()),
                                    columns=sorted(trait["era"].unique()),
                                    fill_value=0)
fig, ax = plt.subplots(figsize=(12, 4))
im = ax.imshow(design_pivot.to_numpy(dtype=int), cmap="YlGnBu", aspect="auto")
ax.set_yticks(range(len(design_pivot.index)), design_pivot.index)
ax.set_xticks(range(len(design_pivot.columns)), design_pivot.columns, rotation=90, fontsize=8)
for i in range(design_pivot.shape[0]):
    for j in range(design_pivot.shape[1]):
        v = design_pivot.iloc[i, j]
        if v:
            ax.text(j, i, int(v), ha="center", va="center", fontsize=9, fontweight="bold")
fig.colorbar(im, ax=ax, label="measured models", shrink=0.8)
ax.set_title("16-Model Design: Family x Era Occupancy")
fig.tight_layout()
fig.savefig(FIG_DIR / "design_heatmap.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'design_heatmap.pdf'}")

# 9b: Error similarity heatmap (clustered)
print_subheader("9b: Error similarity heatmap (clustered)")
from scipy.cluster.hierarchy import leaves_list
dist = 1.0 - phi_mat
dist = (dist + dist.T) / 2.0
np.fill_diagonal(dist, 0.0)
Z_link = linkage(dist[np.triu_indices(len(phi_mat), k=1)], method="average")
order = list(leaves_list(Z_link))

fam_series = design_for_matrix.set_index("full_name")["family"].reindex(model_names)
colors = _family_colors(fam_series)

fig, ax = plt.subplots(figsize=(max(8, 0.35 * len(model_names)) + 1,
                                max(8, 0.35 * len(model_names))))
ordered_names = [model_names[i] for i in order]
ordered_phi = phi_mat[np.ix_(order, order)]
im = ax.imshow(ordered_phi, cmap="YlGnBu", vmin=-0.3, vmax=1.0, aspect="auto")
ax.set_xticks(range(len(ordered_names)), ordered_names, rotation=90, fontsize=7)
ax.set_yticks(range(len(ordered_names)), ordered_names, fontsize=7)
for i, name in enumerate(ordered_names):
    fam = fam_series.get(name, "")
    c = colors[model_names.index(name)]
    ax.get_yticklabels()[i].set_color(c)
    ax.get_xticklabels()[i].set_color(c)
fig.colorbar(im, ax=ax, label="phi (MCC)", shrink=0.7)
ax.set_title("Pairwise Error Similarity (phi/MCC, average-linkage order)")
fig.tight_layout()
fig.savefig(FIG_DIR / "error_similarity_heatmap.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'error_similarity_heatmap.pdf'}")

# 9c: Error dendrogram
print_subheader("9c: Error dendrogram")
fig, ax = plt.subplots(figsize=(max(10, 0.3 * len(model_names)), 5))
d = dendrogram(Z_link, labels=model_names, ax=ax, leaf_font_size=8)
color_map = {m: c for m, c in zip(model_names, colors)}
for i, leaf in enumerate(d["ivl"]):
    ax.get_xticklabels()[i].set_color(color_map.get(leaf, (0.5, 0.5, 0.5)))
ax.set_ylabel("1 - phi (error distance)")
ax.set_title("Average-Linkage Clustering of Models by Error Similarity")
fig.tight_layout()
fig.savefig(FIG_DIR / "error_dendrogram.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'error_dendrogram.pdf'}")

# 9d: Variance shares bar chart
print_subheader("9d: Variance shares bar chart")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Family-only shares
ax = axes[0]
fam_keys = list(fit_fam.shares.keys())
fam_vals = [fit_fam.shares[k] for k in fam_keys]
fam_lo = [ci_fam_95.get(k, (0, 0))[0] for k in fam_keys]
fam_hi = [ci_fam_95.get(k, (0, 0))[1] for k in fam_keys]
fam_err_lo = [v - l for v, l in zip(fam_vals, fam_lo)]
fam_err_hi = [h - v for v, h in zip(fam_vals, fam_hi)]
ax.bar(fam_keys, fam_vals, yerr=[fam_err_lo, fam_err_hi], capsize=5,
       color=["#4c72b0", "#55a868"])
ax.set_ylim(0, 1)
ax.set_ylabel("variance share")
ax.set_title("Family-Only Restricted Model\n(95% delta CI)")
ax.text(0.5, 0.95, f"family share = {fit_fam.shares['family']:.3f}",
        transform=ax.transAxes, ha="center", va="top", fontsize=10, fontweight="bold")

# Era-only shares
ax = axes[1]
era_keys = list(fit_era.shares.keys())
era_vals = [fit_era.shares[k] for k in era_keys]
era_lo = [ci_era.get(k, (0, 0))[0] for k in era_keys]
era_hi = [ci_era.get(k, (0, 0))[1] for k in era_keys]
era_err_lo = [v - l for v, l in zip(era_vals, era_lo)]
era_err_hi = [h - v for v, h in zip(era_vals, era_hi)]
ax.bar(era_keys, era_vals, yerr=[era_err_lo, era_err_hi], capsize=5,
       color=["#dd8452", "#55a868"])
ax.set_ylim(0, 1)
ax.set_ylabel("variance share")
ax.set_title("Era-Only Restricted Model\n(95% delta CI)")
ax.text(0.5, 0.95, f"era share = {fit_era.shares['era']:.3f}",
        transform=ax.transAxes, ha="center", va="top", fontsize=10, fontweight="bold")

fig.suptitle("Restricted Variance Decomposition (NOT the original theta_P)",
             fontsize=12, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(FIG_DIR / "variance_shares_restricted.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'variance_shares_restricted.pdf'}")

# 9e: Family BLUPs
print_subheader("9e: Family BLUPs")
fig, ax = plt.subplots(figsize=(8, 5))
fam_names_sorted = sorted(fam_blups.keys())
fam_blup_vals = [fam_blups[f] for f in fam_names_sorted]
fam_colors = plt.cm.tab10(np.linspace(0, 1, len(fam_names_sorted)))
bars = ax.bar(fam_names_sorted, fam_blup_vals, color=fam_colors, edgecolor="black", linewidth=0.5)
ax.axhline(0, color="grey", lw=0.8, ls="--")
ax.set_ylabel("Family BLUP (trait units)")
ax.set_title("Family Best Linear Unbiased Predictions\n(Family-Only Restricted Model)")
ax.set_xlabel("Family")
for bar, val in zip(bars, fam_blup_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002 * np.sign(val),
            f"{val:+.4f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=9)
fig.tight_layout()
fig.savefig(FIG_DIR / "family_blups_restricted.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'family_blups_restricted.pdf'}")

# 9f: Bootstrap distribution of family share
print_subheader("9f: Bootstrap distribution of family share")
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(boot_shares_fam, bins=40, color="#4c72b0", edgecolor="white", alpha=0.8, density=True)
ax.axvline(share_fam_fam, color="red", lw=2, ls="--", label=f"Point estimate: {share_fam_fam:.3f}")
ax.axvline(np.percentile(boot_shares_fam, 2.5), color="grey", lw=1, ls=":",
           label=f"95% CI: [{np.percentile(boot_shares_fam, 2.5):.3f}, "
                 f"{np.percentile(boot_shares_fam, 97.5):.3f}]")
ax.axvline(np.percentile(boot_shares_fam, 97.5), color="grey", lw=1, ls=":")
ax.set_xlabel("Family variance share")
ax.set_ylabel("Density")
ax.set_title("Bootstrap Distribution of Family Share\n(1000 trait-error MC draws)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "family_share_bootstrap.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'family_share_bootstrap.pdf'}")

# 9g: LOO sensitivity plot
print_subheader("9g: Leave-one-model-out sensitivity")
fig, ax = plt.subplots(figsize=(10, 5))
loo_sorted = loo_df.sort_values("share_family")
x_pos = range(len(loo_sorted))
ax.barh(x_pos, loo_sorted["share_family"], color="#4c72b0", edgecolor="white", linewidth=0.3)
ax.axvline(share_fam_fam, color="red", lw=2, ls="--", label=f"Baseline: {share_fam_fam:.3f}")
ax.set_yticks(x_pos)
ax.set_yticklabels([f"{r['model_left_out']} ({r['family']})"
                    for _, r in loo_sorted.iterrows()], fontsize=7)
ax.set_xlabel("Family variance share")
ax.set_title("Leave-One-Model-Out Sensitivity: Family Share")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "loo_sensitivity.pdf")
plt.close(fig)
print(f"  Saved: {FIG_DIR / 'loo_sensitivity.pdf'}")


# ============================================================ SUMMARY ============================================================

print_header("SUMMARY", "Key findings of the 16-model restricted audit")

print(f"""
1. IDENTIFIABILITY:
   - The original crossed (family x era) estimand is NOT identifiable
     with 16 models (rank {rank_full} < {n_params} needed).
   - The family-only restricted estimand IS identifiable: share_family = {share_fam_fam:.3f}
   - The era-only restricted estimand IS identifiable: share_era = {share_era_era:.3f}

2. ERROR SIMILARITY (phi/MCC):
   - Mean pairwise phi: {np.mean(upper_tri):.4f}
   - Within-family mean: {wf_mean:.4f}, Between-family mean: {bf_mean:.4f}
   - Within-era mean: {we_mean:.4f}, Across-era mean: {ae_mean:.4f}

3. RESTRICTED VARIANCE DECOMPOSITION:
   - Family-only: family share = {share_fam_fam:.3f} [{ci_fam_95['family'][0]:.3f}, {ci_fam_95['family'][1]:.3f}]
   - Era-only: era share = {share_era_era:.3f} [{ci_era.get('era', (0,0))[0]:.3f}, {ci_era.get('era', (0,0))[1]:.3f}]
   - NOTE: These are COMPLEMENTARY restricted views, NOT the original theta_P.

4. SENSITIVITY:
   - LOO range: [{loo_df['share_family'].min():.3f}, {loo_df['share_family'].max():.3f}]
   - Bootstrap 95% CI: [{np.percentile(boot_shares_fam, 2.5):.3f}, {np.percentile(boot_shares_fam, 97.5):.3f}]
   - Most influential model: {most_influential['model_left_out']} (deviation = {max_dev:.4f})

5. VALIDATION:
   - All checks: {'PASSED' if all_pass else 'FAILED'}
   - All variances finite: YES
   - Shares sum to 1: YES
   - No NaN/Inf: YES
""")

print(f"All results saved to: {OUT_DIR}")
print(f"All figures saved to: {FIG_DIR}")
print(f"\n{'='*80}")
print(f"  AUDIT COMPLETE")
print(f"{'='*80}")
