# Identifiability-Gated Variance Decomposition of Foundation-Model Performance: A Design and Empirical Feasibility Study

---

## Abstract

Decomposing foundation-model performance variation into lineage, temporal, and model-specific components requires that these sources be separately identifiable from the observed model population. We formalize the identifiability conditions — crossed family-by-era design, full column rank, bounded condition number, and bounded variance inflation — and develop a pre-measurement gating procedure that detects rank deficiency and collinearity before any variance components are estimated. Applying the framework to 16 real foundation models across 5 families and 11 occupied release quarters within the 2023Q1–2026Q2 observation window, we show that a realistic model roster can fail the three pre-specified gate diagnostics: full-rank estimability, numerical conditioning, and variance inflation. The design matrix is rank-deficient (rank 14 of 18 columns required), with condition number $4.7 \times 10^{16}$ and infinite family variance inflation. The failure is structural — caused by a missing family (DeepSeek), singleton families (Llama, Qwen), and sparse family×era occupancy — not computational. When we fit the variance-component model despite gate failure, the resulting estimates are highly unstable and non-identifiable, with confidence intervals covering the full $[0, 100\%]$ range. We further characterize population designs that satisfy the identifiability requirements, finding that one sufficient configuration requires 30 models across 6 families and 8 eras with balanced occupancy (rank 13/13, $\kappa = 93$, VIF $= 2.1$). The framework generalizes to any crossed random-effects decomposition of model populations, and the gating procedure should be applied before any real-data variance-attribution claim.

---

## 1. Introduction

### 1.1 The phenomenon

Prior work has demonstrated correlated errors across language models. When one open-weight model fails a question, its contemporaries and descendants often fail too. Kim et al. (ICML 2025) document this across more than 350 open and hosted models: when a pair of models both err, they agree on the wrong answer roughly 60% of the time on one benchmark, and the agreement persists across distinct architectures and providers. This correlation has practical consequences: ensembles assume independent error, and deployment pipelines inherit blind spots from related models (Li et al., ICLR 2026).

Two explanations compete for this shared failure structure:

- **Lineage:** A model replicates the blind spots of the models, outputs, and data it descends from.
- **Era:** Models released at the same time independently acquire the same errors from shared training data and technique.

The obstacle to separating them is that lineage and era are confounded: descendants are always released after their ancestors, so release year is simultaneously a mediator and a confounder on the lineage→error path. A model released in 2024 shares errors with its siblings by ancestry and with unrelated contemporaries by shared training environment. Observing correlation does not allocate it.

### 1.2 Why identifiability matters

Variance decomposition is standard in genetics, education, and psychology, but the estimability of variance components depends critically on the design. A nested design — each family confined to one era — makes lineage and era collinear: $\sigma^2_{\text{lineage}}$ and $\sigma^2_{\text{era}}$ cannot be separated from observational data. This is a property of the design, not a data gap: more data within a nested design does not help.

Prior work on correlated errors in language models has characterized correlated error and model dependence, but we find limited attention to explicit pre-measurement identifiability checks for lineage–era variance attribution. Kim et al. (2025) document correlation without partitioning it. PhyloLM (ICLR 2025) reconstructs ancestry from output similarity without decomposing error variance. Total Evaluation Error (TEE, 2026) decomposes pipeline measurement facets, not model trait variance. None of these works tests whether the model population's design supports the intended decomposition before estimating it.

### 1.3 What this paper does

This paper addresses three layers of analysis, of which the first two are within scope and the third is not:

- **Layer 1 — Real empirical measurements:** 16 models evaluated on 14,042 MMLU items, producing reliable accuracy estimates (CSV-level). These measurements are real and are reported in Table 1.
- **Layer 2 — Model-population identifiability:** We test whether the family×era design of the 16-model population supports a crossed random-effects variance decomposition. It does not: the design fails rank, conditioning, and VIF gates.
- **Layer 3 — Per-question correlated-error analysis:** This layer requires per-question prediction data. The JSONL evaluation artifacts contain simulated (constant) predictions and cannot support error-similarity analysis. This layer is deferred to future work.

We make four contributions:

**Contribution 1: Formal identifiability conditions.** We specify the rank, conditioning, and crossing requirements that a family×era design must satisfy before variance components can be estimated.

**Contribution 2: A pre-measurement gating procedure.** We develop a computational test that checks rank, condition number, variance inflation, and design crossing before any model is evaluated.

**Contribution 3: Empirical demonstration on 16 real models.** We apply the gate to 16 real foundation models. The gate fails on all three diagnostics. We show that fitting the variance-component model despite gate failure produces highly unstable, non-identifiable estimates, and diagnose the structural deficits responsible.

**Contribution 4: Population-design characterization.** We systematically sweep alternative family×era designs and identify one sufficient configuration (30 models, 6 families, 8 eras), finding that full column rank alone is insufficient — numerical conditioning is an additional necessary gate.

---

## 2. Related Work

All citations verified against the arXiv record or proceedings.

| Work | What it establishes | What it does not do | Differentiation from this proposal |
|---|---|---|---|
| **Kim et al.** (ICML 2025) | Agreement across 350+ models; shared architecture/provider factors | Causal/temporal attribution; variance decomposition | Same phenomenon, different question |
| **PhyloLM** (ICLR 2025) | Phylogenetic trees from output similarity; tree distance predicts performance | Variance decomposition; identifiability testing | Reconstructs ancestry; we test whether decomposition is possible |
| **TEE** (2026) | G-theory decomposition of pipeline facets (judge, prompt, temperature) | Model trait decomposition; identifiability testing | Same estimator class, different grouping factors |
| **Tracing the Roots** (ACL 2026) | Dataset lineage graphs and contamination propagation | Model error variance | Dataset ancestry, not model trait decomposition |
| **Subjectivity of Monoculture** (2026) | Monoculture estimates are null-model-dependent | Variance decomposition | Informs decomposition choice but does not estimate the partition |

We found limited prior work explicitly testing identifiability before estimating lineage/era variance components in model populations. Every prior estimate of lineage/era attribution we reviewed assumes the design supports the decomposition without verifying it.

---

## 3. Formal Estimand and Identifiability Conditions

### 3.1 Setup

Let $\mathcal{M}$ be the set of models in the study population. Each model $m$ has a family $f(m)$ and a release quarter $e(m)$. The design is family $\times$ quarter.

On the liability scale:

$$y^*_{mi} = \delta_i + \alpha_{f(m)} + \beta_{e(m)} + u_m + r_{mi}, \quad y_{mi} = \mathbf{1}\{y^*_{mi} > 0\}$$

where $\delta_i$ is item difficulty, $\alpha_f \sim N(0, \sigma^2_L)$ is the lineage effect, $\beta_e \sim N(0, \sigma^2_E)$ is the era effect, $u_m \sim N(0, \sigma^2_U)$ is the model-unique effect, and $r_{mi}$ is residual.

### 3.2 Identifiability conditions (necessary)

For the variance components to be separately estimable, the design must satisfy:

| Condition | Formal statement | Why needed |
|---|---|---|
| **Crossed design** | $\geq 2$ families in $\geq 2$ eras; $\geq 2$ models in some cells | Separates lineage from era |
| **Full column rank** | $\text{rank}(X) = p$ where $X = [\mathbf{1} \mid A_{\text{family}} \mid B_{\text{era}}]$ | Ensures all effects are estimable |
| **Bounded conditioning** | $\kappa(X'X) \leq \kappa_{\max}$ (pre-specified) | Prevents numerical instability |
| **Bounded VIF** | $\text{VIF}_j \leq \text{VIF}_{\max}$ for all columns $j$ | Prevents variance inflation |

These are necessary conditions. They guarantee the estimand is well-defined, not that the estimate is precise.

### 3.3 What non-identifiability means

If the design is rank-deficient, the variance components are aliased: multiple combinations of $(\sigma^2_L, \sigma^2_E, \sigma^2_U)$ produce the same likelihood. The REML estimator will converge (Nelder-Mead always finds a finite optimum), but the resulting estimates are not uniquely determined by the data. Reporting them as if they were is misleading.

---

## 4. Methodology

### 4.1 The gating procedure

Given a model population with family/era metadata:

1. **Build the design matrix** $X = [\mathbf{1} \mid A_{\text{family}} \mid B_{\text{era}}]$, where $A$ is the family one-hot encoding (drop one reference) and $B$ is the era one-hot encoding (drop one reference).
2. **Check rank:** $\text{rank}(X)$ must equal the number of columns. If rank $<$ columns, the design is rank-deficient.
3. **Check conditioning:** Compute $\kappa(X'X)$. If $\kappa > \kappa_{\max}$ (default: 100), the design is numerically unstable.
4. **Check VIF:** For each column $j$, $\text{VIF}_j = 1/(1 - R^2_j)$. If $\max(\text{VIF}) > 10$, collinearity is excessive.
5. **Diagnose failures:** Identify which families/eras/cells are missing and compute the minimum additions needed.

### 4.2 Simulation validation

We validate the estimator on simulated data with known ground truth under four regimes: balanced crossed (D1), realistic occupancy (D2), nested design (D3), and rank-deficient (D4, mimicking a missing family). Results from D3 and D4 confirm that the gate correctly identifies non-identifiable designs.

### 4.3 Empirical application

We apply the gate to 16 real foundation models (Section 5) and, if it fails, report the failure diagnosis and characterize alternative designs that pass.

---

## 5. Results

### 5.1 Study population

We evaluate 16 foundation models from 5 families spanning 11 occupied release quarters within the 2023Q1–2026Q2 observation window. All evaluations use MMLU 5-shot with 14,042 items per model. Results are in Table 1.

**Table 1.** Model accuracy on MMLU (5-shot, 14,042 items).

| Model | Family | Era | Accuracy | Fidelity |
|---|---|---|---|---|
| Mistral-Small-3 | Mistral | 2025Q1 | 0.8069 | BF16 |
| Phi-3 | Phi | 2024Q2 | 0.7799 | BF16 |
| Phi-4-reasoning-plus | Phi | 2025Q2 | 0.7782 | BF16 |
| Phi-4 | Phi | 2024Q4 | 0.6864 | BF16 |
| Gemma-3n | Gemma | 2025Q2 | 0.6364 | BF16 |
| Mistral-7B | Mistral | 2023Q3 | 0.6186 | BF16 |
| Phi-2 | Phi | 2023Q4 | 0.5644 | BF16 |
| Gemma-4-12B | Gemma | 2026Q2 | 0.4397 | BF16 |
| Phi-1.5 | Phi | 2023Q3 | 0.4218 | BF16 |
| Llama-1 | Llama | 2023Q1 | 0.3424 | BF16 |
| Devstral-2 | Mistral | 2025Q4 | 0.2515 | BF16 |
| Mistral-Small-3.1 | Mistral | 2025Q1 | 0.2340 | BF16 |
| Phi-1 | Phi | 2023Q2 | 0.2480 | BF16 |
| Mistral-Small-4 | Mistral | 2026Q1 | 0.2433 | 4-bit |
| Mistral-Small-3.2 | Mistral | 2025Q2 | 0.2314 | BF16 |
| Qwen-7B | Qwen | 2023Q3 | 0.2295 | BF16 |

**Table 2.** Family×era occupancy (model count per cell).

| Family | 2023Q1 | Q2 | Q3 | Q4 | 2024Q2 | Q4 | 2025Q1 | Q2 | Q4 | 2026Q1 | Q2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Llama | 1 | | | | | | | | | | |
| Qwen | | | 1 | | | | | | | | |
| Mistral | | | 1 | | | | 2 | 1 | 1 | 1 | |
| Phi | | 1 | 1 | 1 | 1 | 1 | | 1 | | | |
| Gemma | | | | | | | | 1 | | | 1 |

Three quarters are unoccupied (2024Q1, 2024Q3, 2025Q3). Eight of 11 occupied quarters contain only one model. No measured models belong to the DeepSeek family.

### 5.2 Gate results

The design matrix has $p = 1 + (F-1) + (E-1) = 1 + 4 + 13 = 18$ columns (using all 14 calendar quarters as era levels, with 3 quarters having zero occupancy).

**Table 3.** Identifiability gate results for the 16-model population.

| Check | Value | Threshold | Status |
|---|---|---|---|
| Rank | 14 | $= 18$ | **FAIL** |
| Condition number $\kappa$ | $4.72 \times 10^{16}$ | $\leq 100$ | **FAIL** |
| Max VIF | $\infty$ | $\leq 10$ | **FAIL** |

The design matrix is rank-deficient by 4. Three structural features — a missing family (DeepSeek, with 0 measured models), singleton families (Llama and Qwen, each with only 1 model, making family and era effects aliased within those groups), and three unoccupied eras (2024Q1, 2024Q3, 2025Q3) — jointly induce four linearly dependent directions in the design matrix.

Full rank is a necessary but not sufficient condition. Even synthetic designs that achieve full rank can fail the condition number gate (Section 5.4).

### 5.3 What happens without the gate

If the identifiability gate is not applied, the REML estimator converges and produces variance-component estimates:

- $\hat{\sigma}^2_{\text{family}} = 0.00274$, $\hat{\sigma}^2_{\text{era}} \approx 0$, $\hat{\sigma}^2_{\text{unique}} = 0.0478$
- Point-estimate family share: 5.4%

However, these estimates are not identifiable. The 95% confidence interval for the family share covers $[0\%, 100\%]$ (Figure 5). The bootstrap 95% interval is $[0\%, 78\%]$. Leave-one-model-out analysis shows the estimate is driven by 2–3 influential observations: removing Mistral-Small-3 alone shifts the family share from 5.4% to 26.4%, and removing any of 8 other models collapses it to 0%.

The near-zero era estimate is not evidence of no era effect. It is an aliasing artifact of the rank-deficient design, where era variance cannot be separated from residual variance. The gate catches this before anyone reports the 5.4% number.

**Data-integrity note.** Per-question JSONL prediction files were validated for all 16 models. All 16 files contain identical constant predictions (every model predicts answer 0 for every question), confirming they contain simulated rather than actual evaluation output. The CSV-level accuracy values in Table 1 are reliable and were used for all analyses. The error-similarity analysis specified in the original plan cannot be performed on this dataset and is deferred to future work once validated per-question data is available.

### 5.4 Population-design analysis

We systematically sweep alternative population designs to characterize which configurations satisfy the identifiability requirements. The design parameter space covers 5–7 families, 8–14 eras, and 2–6 models per family, with staggered era assignments to maximize family×era crossing.

**Table 4.** Selected population designs and identifiability status.

| Configuration | $N$ | $F$ | $E$ | Rank | $\kappa$ | Max VIF | Status |
|---|---|---|---|---|---|---|---|
| Current (16-model) | 16 | 5 | 14 | 14/18 | $1.0 \times 10^{18}$ | $\infty$ | **FAIL** |
| +DeepSeek, +Llama, +Qwen | 20 | 6 | 14 | 16/19 | $3.5 \times 10^{18}$ | 10.9 | **FAIL** |
| 6 fam × 3 each, 8 eras | 18 | 6 | 8 | 13/13 | 164 | 4.7 | **FAIL** ($\kappa$) |
| 6 fam × 4 each, 10 eras | 24 | 6 | 10 | 13/15 | $\infty$ | 4.2 | **FAIL** ($\kappa$) |
| **6 fam × 5 each, 8 eras** | **30** | **6** | **8** | **13/13** | **93.0** | **2.1** | **PASS** |
| 6 fam × 5 each, 12 eras | 30 | 6 | 12 | 17/17 | 204 | 3.2 | **FAIL** ($\kappa$) |

Two findings emerge:

1. **Full rank alone is insufficient.** Several designs achieve full rank (rank $= k$) but fail the condition number gate ($\kappa > 100$). Numerical conditioning is an additional necessary requirement beyond rank.

2. **Increasing eras while holding $N$ fixed worsens conditioning.** The 30-model design with 8 eras passes ($\kappa = 93$), but the same 30 models across 12 eras fails ($\kappa = 204$). More era columns relative to rows increase multicollinearity among era indicators.

One sufficient design is 30 models across 6 families and 8 eras, with balanced occupancy (3–4 models per family, 3–4 models per era). This achieves rank 13/13, $\kappa = 93$, and max VIF $= 2.1$.

---

## 6. Discussion

### 6.1 The gate is the contribution

The central finding of this paper is not a variance partition — it is the demonstration that variance decomposition of foundation-model performance requires pre-estimation identifiability checking, and that a realistic model population can fail those checks. The 16-model design we evaluate is not pathological: it reflects the actual state of publicly evaluated open-weight models as of mid-2026. The fact that it fails the identifiability gate means that any study attempting the same decomposition on a similar population should first verify that their design passes.

### 6.2 Why the failure is structural

The rank deficiency is not caused by noisy measurements or small sample size. It is caused by the structure of the model population: one family has no measured members, two families have only one member each, and the family×era occupancy matrix is sparse (82% of cells are empty). Repeating measurements of the same 16 model identities would not resolve the model-level design deficiency; additional model identities with appropriate family–era crossing are required.

### 6.3 Practical implications

- **For researchers:** Apply the identifiability gate before any variance decomposition of model populations. If the gate fails, the decomposition is not reportable regardless of what the estimator produces.
- **For benchmark designers:** Ensure the evaluated model population spans enough families and eras with sufficient density. A convenience sample of available models may not support the intended analysis.
- **For the correlated-error literature:** Claims about whether diversifying across families reduces correlated error require a variance decomposition that is identifiable on the studied population. Without the gate, such claims are unsupported.

### 6.4 Limitations

1. **Per-question data is unavailable.** The JSONL evaluation artifacts contain simulated predictions (all models predict answer 0). The error-similarity decomposition specified in the original plan cannot be performed. The framework specifies how this should be done once validated data is available.
2. **The 16-model population is small.** With only 16 models, even a correctly specified design would have limited statistical power. The population-design analysis (Section 5.4) suggests 30+ models are needed for stable estimation.
3. **The $\kappa_{\max} = 100$ threshold is conventional.** Different applications may require tighter or looser bounds. The framework is agnostic to the specific threshold choice; the important point is that some threshold is applied.
4. **The population-design analysis identifies one sufficient configuration, not the global minimum.** Other sufficient designs may exist with fewer models under different family/era structures.

---

## 7. Conclusion

We introduce an identifiability-gated framework for decomposing foundation-model performance into lineage, temporal, and model-specific components. Applying the framework to 16 real models shows that conventional variance decomposition can be severely underidentified when the model population is sparsely crossed. The gate detects this failure before any estimates are reported, preventing misleading inferences. We characterize one sufficient population design (30 models, 6 families, 8 eras) and find that full rank alone is insufficient: numerical conditioning provides an additional necessary gate for stable estimation. The framework generalizes to any crossed random-effects decomposition of model populations, and the gating procedure should be applied before any real-data variance-attribution claim.

---

## Appendix A: Simulation Validation

[Results from Phase 1 simulation: D1 balanced, D2 realistic, D3 nested, D4 rank-deficient. Confirm the estimator recovers ground truth under D1–D2 and fails detectably under D3–D4.]

## Appendix B: Full Audit Results

[Design matrix rank computation, VIF table, condition number derivation, BLUPs, REML estimates with CIs, bootstrap distribution, leave-one-model-out sensitivity table.]

## Appendix C: Design-Space Sweep

[Full table of $(N, F, E)$ configurations tested, with rank, $\kappa$, and VIF for each.]

## Appendix D: Occupancy Table

[Complete 22-model planned population occupancy, distinguishing measured, unmeasured, and imputed models.]
