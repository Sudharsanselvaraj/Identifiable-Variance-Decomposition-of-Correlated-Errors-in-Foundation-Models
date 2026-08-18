# Phase 2 Research Audit Report — 16-Model Dataset

**Date:** 2026-08-18
**Status:** WITHHOLD — study not ready for submission
**Decision:** WITHHOLD (see §12)

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Phase 1: Data Integrity](#2-phase-1-data-integrity)
3. [Phase 2: Identifiability](#3-phase-2-identifiability)
4. [Phase 3: Restricted Estimands](#4-phase-3-restricted-estimands)
5. [Phase 4: Error Matrix](#5-phase-4-error-matrix)
6. [Phase 5: Variance Decomposition](#6-phase-5-variance-decomposition)
7. [Phase 6: Sensitivity Analysis](#7-phase-6-sensitivity-analysis)
8. [Phase 7: DeepSeek Imputation](#8-phase-7-deepseek-imputation)
9. [Phase 8: Validation](#9-phase-8-validation)
10. [Phase 9: Figures](#10-phase-9-figures)
11. [Phase 10-11: Manuscript & Novelty](#11-phase-10-11-manuscript--novelty)
12. [Decision](#12-decision)
13. [Path to Proceed](#13-path-to-proceed)

---

## 1. Executive Summary

We attempted to execute a 12-phase research audit on a 16-model dataset (out of 22 planned) for the paper "Identifiability-Gated Variance Decomposition of Correlated Errors in Foundation Models."

**The study has three fatal limitations that prevent submission:**

1. **Identifiability failure:** The 16-model design is rank-deficient (rank 14 < 15 required). The original crossed family × era variance decomposition cannot be legitimately estimated.

2. **Corrupted per-question data:** All 16 JSONL files contain identical simulated data (every model predicts 0 for every question). The error-similarity analysis — a core contribution of the paper — cannot be performed.

3. **Uninformative results:** Even under the restricted (family-only) estimand, the family-share CI covers the entire [0, 1] range. Bootstrap 95% CI: [0.0000, 0.7756]. The data cannot distinguish whether family explains 0% or 78% of variance.

**Verdict: WITHHOLD.** The study requires new data collection (re-run per-question evaluations + add 4 missing models) before it can be completed.

---

## 2. Phase 1: Data Integrity

### 2.1 CSV Results
- **16 rows**, one per model
- **14,042 samples** per model (all identical)
- **No duplicates**, no missing fields, no pilot/artifacts
- All answers aligned across models (verified by checking 3 model pairs)

### 2.2 JSONL Per-Question Data — CRITICAL FAILURE

| Check | Result |
|-------|--------|
| JSONL files exist | 16 ✓ |
| Rows per file | 14,042 ✓ |
| Predictions identical across files | **YES — all predict 0** |
| JSONL accuracy matches CSV | **1/16 match** (only Qwen-7B) |
| Prediction values | `{0}` for every model, every question |

**Root cause:** The JSONL files were populated with simulated data (from `phase2_eval_simulate.py`) rather than actual lm_eval output. The real predictions were generated on the RunPod GPU but were not preserved in the synced repository.

**Impact:** The error-similarity analysis (§4) and per-question decomposition are impossible with this dataset.

---

## 3. Phase 2: Identifiability

### 3.1 Original Crossed Design

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Rank | 14 | ≥ 15 | **FAIL** |
| Condition number | 4.72 × 10¹⁶ | ≤ 100 | **FAIL** |
| VIF (family) | inf | ≤ 10 | **FAIL** |
| BLUP collinearity | Not computable | r < 0.9 | — |
| Profile flatness | 0.0106 | > 1.92 | **FAIL** |

**Design matrix:** 16 rows × 15 columns (1 intercept + 4 family dummies + 10 era dummies)

**Why rank-deficient:**
- 0 measured DeepSeek models → no DeepSeek family column
- Llama has 1 model, Qwen has 1 model → these singletons cannot separate family from era
- One linear dependency exists in the design

**Pre-registered threshold:** rank ≥ k = 1 + 5 + 13 = 19 (for 22-model design). With 16 models and 11 eras, k = 1 + 4 + 10 = 15, and rank = 14 < 15.

### 3.2 Occupancy

| | Families | Eras |
|---|---------|------|
| Total | 6 | 14 |
| Measured | 5 (0 DeepSeek) | 11 (missing 2024Q1, 2024Q3, 2025Q3) |
| Sparsity | 82.14% (69 empty cells of 84) |

Family counts: Mistral=6, Phi=6, Gemma=2, Llama=1, Qwen=1

---

## 4. Phase 3: Restricted Estimands

Two restricted models were fit as alternatives to the original estimand.

### 4.1 Model A: Family-only (era dropped)

| Component | σ² | Share | 95% CI |
|-----------|-----|-------|--------|
| Family | 0.002743 | 5.4% | [0.0000, 0.9960] |
| Unique | 0.047776 | 94.6% | [0.0040, 1.0000] |

- REML converged: Yes
- Profile flatness: 0.0106 (profile flat → CI wide by construction)
- **The CI covers essentially the entire [0, 1] range.** The data is uninformative about the family share.

### 4.2 Model B: Era-only (family dropped)

| Component | σ² | Share |
|-----------|-----|-------|
| Era | ≈ 0 | 0.0% |
| Unique | 0.0499 | 100.0% |

- REML converged: Yes
- Era effects are essentially zero — the 11 occupied eras explain nothing beyond noise.

### 4.3 Interpretation

The data suggest:
- **Family effects are real but tiny** (point estimate 5.4%), with enormous uncertainty
- **Era effects are negligible** (point estimate 0%)
- **94.6% of variance is model-specific** — each model's accuracy is determined by its own characteristics, not by family or era

However, these estimates are so uncertain that they cannot support any quantitative claim.

---

## 5. Phase 4: Error Matrix

**Status: BLOCKED**

All 16 JSONL files contain identical predictions (all zeros). The per-question error matrix cannot be constructed. The core contribution of the paper — analyzing correlated errors across models — is impossible without real per-question data.

---

## 6. Phase 5: Variance Decomposition

### Crossed Model (reference only — not identifiable)

| Component | σ² | Share | 95% CI |
|-----------|-----|-------|--------|
| Family | 0.002743 | 5.4% | [0.0000, 0.9798] |
| Era | 0.000000 | 0.0% | [0.0000, 1.0000] |
| Unique | 0.047776 | 94.6% | [0.0000, 1.0000] |

The crossed model confirms: era effects are zero, and the family CI covers [0, 98%].

### Bootstrap Distribution

| Statistic | Value |
|-----------|-------|
| Mean share_family | 0.2282 |
| Median share_family | 0.1668 |
| 95% CI | [0.0000, 0.7756] |
| Valid bootstraps | 1000/1000 |

The bootstrap mean (22.8%) is higher than the REML point estimate (5.4%) because bootstraps that sample models from different families inflate the between-family variance. The 95% CI is [0%, 78%] — uninformative.

---

## 7. Phase 6: Sensitivity Analysis

### Leave-One-Model-Out

| Removed Model | share_family | Δ |
|---------------|-------------|---|
| Mistral-Small-3 | 0.2640 | +0.2097 |
| Phi-1 | 0.2030 | +0.1487 |
| Mistral-7B | 0.1209 | +0.0666 |
| *8 models removed* | 0.0000 | -0.0543 |

**Key finding:** Removing any of the 8 models with extreme accuracy (Mistral-Small-3 at 0.81, Phi-1 at 0.25) dramatically shifts the family share. Removing Mistral-Small-3 causes it to drop from 5.4% to 0%. The result is driven by 2-3 influential observations.

### Leave-One-Family-Out

| Removed Family | n remaining | share_unique |
|----------------|-------------|--------------|
| Phi | 10 | 100.0% |
| Mistral | 10 | 93.2% |
| Gemma | 14 | 89.9% |
| Llama | 15 | 94.0% |
| Qwen | 15 | 95.3% |

Dropping Phi causes the family share to collapse to 0%. The Phi family (6 models with accuracy range 0.25-0.78) is the sole driver of the apparent family effect.

---

## 8. Phase 7: DeepSeek Imputation

**Status: NOT FEASIBLE**

- 0 measured DeepSeek models → no basis for imputation
- Even with 2 imputed DeepSeek models, the design would still be rank-deficient
- The pre-registered imputation module requires measured models in the target family

---

## 9. Phase 8: Validation

| Check | Status |
|-------|--------|
| All variances finite | PASS |
| Shares sum to 1 | PASS |
| Shares in [0,1] | PASS |
| Family-only REML converged | PASS |
| Era-only REML converged | PASS |
| Crossed REML converged | PASS |
| Bootstrap CI valid | PASS |
| Trait values all finite | PASS |
| Trait values in [0,1] | PASS |

All computational checks pass. The failure is structural (identifiability), not computational.

---

## 10. Phase 9: Figures

Seven figures generated:
1. `design_heatmap.pdf` — Family × era occupancy
2. `error_similarity_heatmap.pdf` — **Invalid** (corrupted JSONL data)
3. `error_dendrogram.pdf` — **Invalid** (corrupted JSONL data)
4. `variance_shares_restricted.pdf` — Family-only variance shares
5. `family_blups_restricted.pdf` — Family BLUPs
6. `family_share_bootstrap.pdf` — Bootstrap distribution
7. `loo_sensitivity.pdf` — Leave-one-model-out sensitivity

---

## 11. Phase 10-11: Manuscript & Novelty

### Novelty Audit

The paper's core claim — quantifying how much of foundation-model accuracy variance is attributable to family lineage, training era, and correlated errors — is **novel** and **important**. No prior work has performed this analysis with identifiability-gated methods.

However, the current dataset cannot support this claim. The study would be the first to show:
- A rigorous identifiability gate for variance decomposition
- Crossed variance-component models for foundation model evaluation
- Error-similarity analysis across model families

### Manuscript Status

Sections 1-8 of the proposal are well-written and scientifically sound. The methodology (identifiability gating, REML, bootstrap CIs) is appropriate. The pre-registration is detailed and honest.

**Cannot proceed to writing results/discussion until data collection is complete.**

---

## 12. Decision

### WITHHOLD — Do not submit

**Three independent fatal limitations:**

1. **Structural:** The 16-model design is rank-deficient. The original estimand is not identifiable. The restricted estimands have CIs covering [0, 100%].

2. **Data integrity:** Per-question predictions are corrupted/simulated. The error-similarity analysis is impossible.

3. **Statistical power:** Even the restricted family-only model cannot distinguish family share = 0% from family share = 78%. The study is severely underpowered.

### Specific Failures Against Pre-Registered Criteria

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Rank | ≥ k | 14 < 15 | FAIL |
| VIF | ≤ 10 | inf | FAIL |
| Kappa | ≤ 100 | 4.72 × 10¹⁶ | FAIL |
| Profile flatness | > 1.92 | 0.0106 | FAIL |

---

## 13. Path to Proceed

The study can proceed to submission if and when:

### Minimum Requirements (must fix all)
1. **Re-run all 16 models** with correct `--log_samples` and verify JSONL outputs contain real per-question predictions
2. **Add 4 missing models** (Qwen1.5-72B, Llama-3.1-70B, Llama-3.3-70B, Phi-4-reasoning-vision-15B) or accept reduced scope
3. **Verify JSONL accuracy matches CSV accuracy** for all models before analysis

### Recommended (would substantially strengthen the paper)
4. Add the 2 DeepSeek models (V3.1, V3.2) to enable family identifiability
5. Fill the 3 missing eras (2024Q1, 2024Q3, 2025Q3) to improve era identifiability
6. Add at least 2 models per family for all singleton families (Llama, Qwen)

### Alternative Path (reduced scope)
If the full 22-model dataset is not achievable, the paper could be reformulated as:
- A **methods paper** demonstrating the identifiability-gating framework (no data required)
- A **descriptive study** of accuracy trends across 16 models (no variance decomposition)
- A **power analysis** quantifying what sample size would be needed

---

*Report generated: 2026-08-18*
*Audit code: `src/lineage_era/audit_16model_full.py`*
*Results: `results/phase2_empirical/audit_summary.json`*
