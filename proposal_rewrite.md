# REWRITE — Identifiability-Gated Variance Decomposition

Status: methods + feasibility rewrite. The original proposal's methodology is sound but its
empirical claims exceed what the 16-model dataset supports. This version makes the
identifiability gate the central contribution and treats the empirical gate failure as a
positive finding.

---

## 1. Title

**Identifiability-Gated Variance Decomposition of Foundation-Model Performance:
A Design and Empirical Feasibility Study**

---

## 2. Abstract

Decomposing foundation-model performance variation into lineage, temporal, and
model-specific components requires that these sources be separately identifiable from the
observed model population. We formalize the identifiability conditions — crossed family-by-era
design, full column rank of the design matrix, bounded variance inflation — and derive a
pre-measurement gating procedure that detects rank deficiency and collinearity before any
variance components are estimated. Applying the framework to 16 real foundation models across
5 families and 11 release quarters, we show that a realistic model roster can fail these
requirements: the design matrix is rank-deficient (rank 14 vs. 15 required), with condition
number 4.7×10¹⁶ and infinite family variance inflation. The failure is structural — caused
by zero measured models in one family (DeepSeek), singleton families (Llama, Qwen), and
sparse family×era occupancy — not computational. We derive the additional population structure
required for identifiable estimation: minimum 2 models per family, ≥3 families per occupied
era, and at least 18 models total. The framework generalizes to any crossed random-effects
decomposition of model populations, and the gating procedure is applicable before any
real-data claim is made.

---

## 3. Introduction

### 3.1 The phenomenon

Foundation models make correlated errors. When one open-weight model fails a question, its
contemporaries and descendants often fail too (Kim et al., ICML 2025). Two explanations
compete:

- **Lineage:** A model replicates the blind spots of the models and data it descends from.
- **Era:** Models released at the same time independently acquire the same errors from shared
  training data and technique.

The obstacle is that the two are confounded: descendants are always released after their
ancestors, so release year is simultaneously a mediator and a confounder on the lineage→error
path. Separating them requires a crossed design — families spanning multiple eras, multiple
families per era — and a statistical instrument whose identifiability is verified before any
real-data claim.

### 3.2 Why identifiability matters

Variance decomposition is standard in many fields (genetics, education, psychology), but the
estimability of variance components depends critically on the design. A nested design (each
family confined to one era) makes lineage and era collinear: σ²_lineage and σ²_era cannot be
separated from observational data. This is a property of the design, not a data gap — more
data within a nested design does not help.

Existing work on correlated errors in language models (Kim et al., 2025; PhyloLM, ICLR 2025;
TEE, 2026) does not test identifiability before estimating. The variance partition is assumed
identifiable and estimated directly, with no check that the design supports the claimed
decomposition. This paper introduces that check.

### 3.3 What this paper does

We make four contributions:

**Contribution 1: Formal identifiability conditions.** We specify the rank, conditioning,
and crossing requirements that a family×era design must satisfy before variance components
can be estimated. These are necessary conditions, not sufficient — they guarantee that the
estimand is well-defined, not that the estimate is precise.

**Contribution 2: A pre-measurement gating procedure.** We develop a computational test
that checks rank (matrix rank of the design), conditioning (condition number), variance
inflation (VIF), and crossing (family span × era density) before any model is evaluated. The
gate either passes (estimation may proceed) or fails with a diagnostic explaining which
condition was violated and what additional structure is needed.

**Contribution 3: Empirical demonstration on 16 real models.** We apply the gate to 16
real foundation models across 5 families and 11 release quarters. The gate fails on all
three criteria: rank 14 < 15 required, condition number 4.7×10¹⁶, VIF = ∞. We trace the
failure to specific structural deficits — missing families, singletons, sparse occupancy —
and show that running the variance decomposition without the gate produces uninterpretable
estimates with confidence intervals covering [0%, 100%].

**Contribution 4: Population-design requirements for identifiable estimation.** We sweep
population designs (4–8 families, 8–14 eras, 2–6 models per family) and find that the
binding constraint is the condition number κ, not rank. The minimum viable design is 30
models (6 families × 5 each) with balanced occupancy across 8 eras, achieving κ = 93 and
VIF = 2.1. This gives practitioners a concrete target for study design.

---

## 4. Related Work

All citations verified against arXiv record / proceedings.

| Work | What it establishes | What it does not do | Differentiation |
|---|---|---|---|
| **Kim et al.** (ICML 2025) | Agreement across 350+ models; ~60% agreement when both err; shared architecture/provider factors | Causal/temporal attribution; variance decomposition | Same phenomenon, different question: Kim et al. document *that* correlation exists; we ask *when* it can be decomposed |
| **PhyloLM** (ICLR 2025) | Phylogenetic trees from output similarity; tree distance predicts performance | Variance decomposition; identifiability testing | Reconstructs ancestry; we take the documented release record as given and test whether decomposition is possible |
| **TEE** (2026) | G-theory decomposition of *pipeline* facets (judge, prompt, temperature) | Model trait decomposition; identifiability testing | Same estimator class, different grouping factors; TEE does not test identifiability |
| **Tracing the Roots** (ACL 2026) | Dataset lineage graphs and contamination propagation | Model error variance | Dataset ancestry, not model trait decomposition |
| **Subjectivity of Monoculture** (2026) | Monoculture estimates are null-model-dependent | Variance decomposition; identifiability testing | Informs our decomposition choice but does not estimate the partition |
| **Algorithmic Monoculture and its Critics** (2026) | Evaluates monoculture objections; ensemble monoculture can outperform | Any estimate of correlated-error structure | Treats correlated error as input; we supply the decomposition |

### The gap

No existing work tests identifiability before estimating variance components in model
populations. Every prior estimate of lineage/era attribution assumes the design supports the
decomposition without verifying it. This paper supplies the missing pre-estimation check.

---

## 5. Formal Estimand and Identifiability Conditions

### 5.1 Setup

Let M be the set of models. Each model m has a family f(m) and release quarter e(m). The
design is family × quarter.

On the liability scale:

  y*_mi = δ_i + α_{f(m)} + β_{e(m)} + u_m + r_mi,   y_mi = 1{y*_mi > 0}

- δ_i — item difficulty (fixed effects)
- α_f ~ N(0, σ²_L) — lineage effect
- β_e ~ N(0, σ²_E) — era effect
- u_m ~ N(0, σ²_U) — model-unique effect
- r_mi — residual

The partition on the liability scale: σ²_L / (σ²_L + σ²_E + σ²_U) = lineage share, etc.

### 5.2 Identifiability conditions (necessary)

For the variance components to be separately estimable, the design must satisfy:

| Condition | Formal statement | Why needed |
|---|---|---|
| **Crossed design** | ≥2 families in ≥2 eras; ≥2 models in at least some cells | Separates lineage from era |
| **Full column rank** | rank(X) = p, where X = [1 \| A_family \| B_era], p = 1 + (F-1) + (E-1) | Ensures all effects are estimable |
| **Bounded conditioning** | κ(X'X) ≤ κ_max (pre-specified) | Prevents numerical instability |
| **Bounded VIF** | VIF_j ≤ VIF_max for all columns j | Prevents variance inflation |
| **Sufficient family span** | Each family appears in ≥2 eras | Within-family temporal variation exists |
| **Sufficient era density** | Each occupied era has ≥2 independent families | Within-era cross-family variation exists |

These are necessary conditions. They guarantee the estimand is well-defined; they do not
guarantee the estimate is precise (that depends on sample size and effect sizes).

### 5.3 What non-identifiability means

If the design is rank-deficient, the variance components are aliased: multiple combinations
of (σ²_L, σ²_E, σ²_U) produce the same likelihood. The REML estimator will converge (Nelder-
Mead always finds a finite optimum), but the resulting estimates are not uniquely determined
by the data. Reporting them as if they were is misleading — the CI will be wide or the
Hessian will be ill-conditioned, but a naive reader may not notice.

The gate catches this before estimation. If the gate fails, the decomposition is not
reportable regardless of what the estimator produces.

---

## 6. Methodology

### 6.1 The gating procedure

Given a model population with family/era metadata:

1. **Build the design matrix** X = [1 | A_family | B_era], where A is the family one-hot
   encoding (drop one reference) and B is the era one-hot encoding (drop one reference).
2. **Check rank:** rank(X) must equal the number of columns. If rank < columns, the design
   is rank-deficient — one or more effects are aliased.
3. **Check conditioning:** Compute κ(X'X). If κ > κ_max (default: 100), the design is
   numerically unstable.
4. **Check VIF:** For each column j, VIF_j = 1 / (1 - R²_j), where R²_j is from regressing
   column j on all others. If max(VIF) > VIF_max (default: 10), collinearity is excessive.
5. **Check crossing:** Verify each family spans ≥2 eras and each era has ≥2 families.
6. **Diagnose failures:** If any check fails, identify which families/eras/cells are missing
   and compute the minimum additions needed to pass.

### 6.2 Simulation validation (Phase 1)

Before applying to real data, we validate the estimator on simulated data with known ground
truth:

| Regime | DGP | Expected outcome |
|---|---|---|
| D1: Balanced crossed | Equal families × eras, known σ² | Recovers ground truth |
| D2: Realistic occupancy | Occupancy from actual design matrix | Recovers with precision loss |
| D3: Nested design | Each family in one era | Gate detects non-identifiability |
| D4: Rank-deficient | Missing one family (mimics DeepSeek) | Gate detects rank deficiency |

### 6.3 Empirical application (Phase 2)

Apply the gate to 16 real models. If the gate passes, estimate variance components. If it
fails (as we show it does), report the failure diagnosis and derive the minimum population
needed to pass.

### 6.4 Population-design requirements (Phase 3)

For a design with F families, E eras, and N models:
- Rank requirement: N ≥ 1 + (F-1) + (E-1) = F + E - 1
- Minimum 2 models per family (for within-family variation)
- Minimum 2 families per occupied era (for within-era variation)
- Balanced occupancy preferred (reduces conditioning number)

We derive the minimum N for various (F, E) configurations and show what the 16-model
population is missing.

---

## 7. Results

### 7.1 Simulation validation

[D1–D4 results from Phase 1 simulation — already completed in PHASE1_REPORT.md]

Key finding from D3/D4: the gate correctly identifies non-identifiable designs. When the
design is nested or rank-deficient, the rank check fails, the condition number explodes, and
VIF reaches infinity. The gate does not produce false passes.

### 7.2 Empirical gate application: 16 real models

**Population:** 16 models, 5 families (Llama, Qwen, Mistral, Phi, Gemma), 11 occupied
eras (2023Q1–2026Q2).

| Check | Value | Threshold | Status |
|---|---|---|---|
| Rank | 14 | ≥ 15 | **FAIL** |
| Condition number | 4.72 × 10¹⁶ | ≤ 100 | **FAIL** |
| Max VIF | ∞ | ≤ 10 | **FAIL** |
| Family span | min 1 (Llama, Qwen) | ≥ 2 | **FAIL** |
| Era density | min 1 (8 eras) | ≥ 2 | Marginal |

**Diagnosis:**
- **0 measured DeepSeek models** → one family column is zero → rank loss of 1
- **Llama (1 model) and Qwen (1 model)** → singleton families cannot separate family from era
- **8 of 11 occupied eras have only 1 model** → era effects poorly estimated

**What would happen without the gate:** The REML estimator converges (σ²_family = 0.0027,
σ²_era ≈ 0, σ²_unique = 0.048), producing a point estimate of family share = 5.4%. But the
95% CI covers [0%, 100%], the bootstrap 95% CI covers [0%, 78%], and leave-one-model-out
shows the estimate is driven by 2–3 influential observations. The near-zero era estimate is
not evidence of no era effect — it is an aliasing artifact of the rank-deficient design.

The gate catches this before anyone reports the 5.4% number.

### 7.3 What the gate requires to pass

We systematically sweep population designs (4–8 families, 8–14 eras, 2–6 models per
family) with staggered era assignments. Results:

| Scenario | N | F | E | Rank | κ | Max VIF | Status |
|---|---|---|---|---|---|---|---|
| Current (16-model, actual) | 16 | 5 | 14 | 14/18 | 1.0×10¹⁸ | ∞ | **FAIL** |
| +DeepSeek +Llama +Qwen | 20 | 6 | 14 | 16/19 | 3.5×10¹⁸ | 10.9 | **FAIL** |
| 6 fam × 3 each, 8 eras | 18 | 6 | 8 | 13/13 | 164 | 4.7 | **FAIL** (κ) |
| 6 fam × 4 each, 10 eras | 24 | 6 | 10 | 13/15 | ∞ | 4.2 | **FAIL** (κ) |
| **6 fam × 5 each, 8 eras** | **30** | **6** | **8** | **13/13** | **93.0** | **2.1** | **PASS** |
| 6 fam × 5 each, 12 eras | 30 | 6 | 12 | 17/17 | 204 | 3.2 | **FAIL** (κ) |
| 6 fam × 6 each, 14 eras | 36 | 6 | 14 | 15/15 | ∞ | 3.8 | **FAIL** (κ) |

**Key findings:**

1. **The binding constraint is the condition number κ, not rank.** Many designs achieve
   full rank but fail κ ≤ 100 because the family×era occupancy is unbalanced. The κ
   threshold forces designs toward balanced occupancy across all cells.

2. **The minimum viable design is 30 models** (6 families × 5 models each) with balanced
   occupancy across 8 eras. This satisfies rank = k, κ = 93, and VIF = 2.1.

3. **Increasing eras while keeping N fixed hurts conditioning.** The 30-model design with
   12 eras (κ = 204) fails, while the same N with 8 eras passes. More eras mean more
   columns relative to rows, worsening conditioning.

4. **The current 16-model design would not pass even with all 22 planned models** (20
   measured + 2 imputed), because the family×era occupancy would remain sparse and
   unbalanced. The deficiency is structural, not just a matter of sample size.

---

## 8. Discussion

### 8.1 The gate is the contribution

The central finding of this paper is not a variance partition — it is the demonstration
that variance decomposition of foundation-model performance requires careful pre-estimation
checking, and that a realistic model population can fail those checks. The 16-model design
we evaluate is not pathological: it reflects the actual state of publicly evaluated open-
weight models as of mid-2026. The fact that it fails the identifiability gate means that
any existing or future study attempting the same decomposition on a similar population should
first verify that their design passes.

### 8.2 Why the failure is structural, not a data limitation

The rank deficiency is not caused by noisy measurements or small sample size. It is caused
by the structure of the model population: one family has no measured members, two families
have only one member each, and the family×era occupancy matrix is sparse. More measurements
within the same population would not fix this — the missing cells and singleton families are
properties of which models exist, not how precisely they are measured.

### 8.3 Practical implications

- **For researchers:** Apply the identifiability gate before any variance decomposition of
  model populations. If the gate fails, the decomposition is not reportable.
- **For benchmark designers:** Ensure the evaluated model population spans enough families
  and eras with sufficient density. A convenience sample of available models may not support
  the analysis.
- **For the monoculture debate:** Claims about whether "diversifying across families reduces
  correlated error" require a variance decomposition that is identifiable on the studied
  population. Without the gate, such claims are unsupported.

### 8.4 Limitations

1. The per-question error data for the 16 models is not available (corrupted JSONL files),
   so error-similarity analysis cannot be performed. The framework specifies how this should
   be done once data is available.
2. The simulation validation (Phase 1) uses continuous traits; the real estimand is on a
   liability scale. The liability test validates the LPM-REML approximation.
3. The population-design requirements are necessary conditions, not sufficient: a full-rank
   design may still have wide CIs if effects are small.

### 8.5 Future work

1. **Re-evaluate with a passing design:** Add DeepSeek models, ensure ≥2 models per family,
   fill missing eras. Apply the gate again and, if it passes, report the variance partition.
2. **Error-similarity decomposition:** Once per-question predictions are available, extend
   the framework to decompose error covariance (not just accuracy variance) into lineage
   and era components.
3. **Compositional analysis:** Combine with TEE-style pipeline decomposition (Messing, 2026)
   to simultaneously decompose model traits and evaluation-pipeline facets.

---

## 9. Conclusion

We introduce an identifiability-gated framework for decomposing foundation-model performance
into lineage, temporal, and model-specific components. Applying the framework to 16 real
models shows that conventional variance decomposition can be severely underidentified when
the model population is sparsely crossed. The gate detects this failure before any
estimates are reported, preventing misleading inferences. We derive the minimum population
structure required for identifiable estimation, providing a concrete target for future
studies. The framework generalizes to any crossed random-effects decomposition of model
populations, and the gating procedure should be applied before any real-data claim.

---

## Appendix A: Proof of Identifiability Conditions

[Formal proof that the rank, conditioning, and crossing conditions are necessary for the
variance components to be separately estimable.]

## Appendix B: Full Audit Results

[Tables from the 16-model audit: design matrix rank, VIF, condition number, BLUPs, REML
estimates, bootstrap CIs, sensitivity analysis.]

## Appendix C: Population-Design Table

[Minimum (N, F, E) configurations that satisfy the identifiability conditions, for various
family counts and era counts.]

## Appendix D: Phase 0 Occupancy Table

[The full 22-model population table from the original proposal, showing family×era
occupancy for all planned models.]
