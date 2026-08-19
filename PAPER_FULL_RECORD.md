# Lineage or Era? An Identifiability-Gated Instrument for Decomposing Correlated Errors in Public Language Models

**Full Detailed Record — All Results, Methods, and Findings**

---

## Authors

- S. Kanaga Suba Raja (kanagass@srmist.edu.in) — SRM Institute of Science and Technology, Tiruchirappalli
- Shree Harish V — SRM Institute of Science and Technology, Tiruchirappalli
- Sudharsan S (ss0856@srmist.edu.in) — SRM Institute of Science and Technology, Tiruchirappalli

---

## Abstract

Public language models make correlated errors: when one open-weight model fails a question, its contemporaries and descendants often fail it as well. Whether this shared failure structure is driven by lineage—a model replicating the blind spots of the models and data it descends from—or by era—models released together acquiring the same errors through shared training data and technique—cannot be settled by measurement alone, because the two are confounded by construction: descendants are released after their ancestors, making release date both a mediator and a confounder of the lineage path.

This paper contributes the instrument that such a measurement requires. We formulate the attribution as a crossed variance decomposition into lineage, era, and model-specific components, give sufficient conditions under which that partition is identifiable, and separate the observational estimand from a mechanistic one that holds era exactly fixed. We then validate the instrument in three gated stages, each completed before any trait value is observed. A structural audit establishes that the documented release record—not a reconstructed family tree—yields a crossed, connected 47-model design. A simulation study shows that a direct restricted-maximum-likelihood estimator recovers known ground truth to within 2.5 percentage points under balanced occupancy and 5.3 under the real one, and, critically, fails detectably when family and era are nested: three independent detectors flag the aliasing in 100% of repetitions with zero silent coverage. Finally, an outcome-independent design procedure, which never reads a trait value, selects the smallest population that remains structurally identifiable and clears a simulation-based recoverability bar—22 of 47 models, at roughly one-third the measurement cost of the full population. We show the structural minimum of 21 is insufficient, so the additional model is statistically necessary rather than merely convenient. The empirical shares are the object of a measurement protocol that this paper pre-registers in full; the contribution here is the gated instrument, and the demonstration that identifiability, estimator validity, and population design can be settled before measurement rather than defended after it.

---

## 1. Introduction

### 1.1 The Problem

The growing reliance on a small number of public open-weight language models raises a statistical problem: when a group of models is given a hard question, they often fail together. Two explanations compete:

- **Lineage:** A model trained on another model's outputs tends to replicate that model's blind spots.
- **Era:** Models released at the same time are trained on largely the same scrapes of the web, the same benchmark-cleansed corpora, and the same dominant techniques, so they pick up the same errors independently.

**Why this matters practically:** A review pipeline routing each item to three open-weight models and escalating to a human only when they disagree. Its entire value rests on the assumption that the three fail independently. If they do not—if a shared ancestor or a shared training year makes them wrong together on the same items—then unanimity is loudest exactly where it is least trustworthy. The operator cannot detect this from per-model accuracy, which may be excellent for all three. What matters is the structure of the shared component, and whether adding a fourth model from a different family reduces it.

### 1.2 Why the Two Explanations Are Not Separable by Inspection

Descendants are always released after their ancestors, so release year lies on the lineage-to-error path: a child model inherits both the errors of its parent and the training environment of its own release date. Release year is therefore a mediator of the lineage path and a potential confounder of the observational family–error association. Any single-number answer that tries to assign shared error "to lineage" or "to era" conflates the two roles of release year.

### 1.3 The Central Methodological Claim

The ordering of decisions:

1. **Identifiability is verified before any trait is measured**
2. **The estimator is validated in simulation before any real data are analyzed**
3. **The study population is selected by a pre-analysis design procedure that never observes trait values, before any empirical inference**

Each of the three stages can fail, and each failure is one that a conventional analysis would absorb into its results rather than report. Running the three as gates converts each from an unreported assumption into a reported verdict.

---

## 2. Problem Formulation and Research Questions

### Primary Research Question (RQ0)

Whether the observed error-correlation structure across public open-weight language models can be separated into a lineage component and an era component; that is, whether the partition σ²_L + σ²_E + σ²_U is estimable and non-degenerate on the connected subset.

A positive answer requires both:
- (a) the estimator survives simulation validation under the realistic population occupancy
- (b) on real data, the lineage and era components are each estimated with non-degenerate intervals

### Refutable Sub-Questions

| RQ | Question | Operates on | Refutation condition | Status |
|---|---|---|---|---|
| RQ1 | Does the crossed random-effects estimator recover known ground truth under balanced-crossed (D1) and realistic-occupancy (D2)? | Simulated data | Bias or collapse under D2 | Reported |
| RQ2 | Under a nested design, does the estimator fail detectably? | Simulated data | Silent bias | Reported |
| RQ3 | What share of error covariance is attributable to lineage conditional on era? | Connected subset | σ²_L ≈ 0 | Pre-registered |
| RQ4 | Holding era exactly fixed, what is the structural contribution of lineage? | Co-released cohorts + fine-tune chains | — | Pre-registered |
| RQ5 | After lineage adjustment, does the era component converge across release quarters? | Connected subset | Flat trend | Pre-registered |
| RQ6 | Is cross-family diversification a credible mitigation for correlated failure? | Decision layer | Era dominates | Pre-registered |

### Two-Estimand Rule

- **RQ3 (observational, θ_P):** Lineage conditional on era grouping. Adjusts for era but cannot hold era fixed.
- **RQ4 (mechanistic, θ_M):** Lineage with era held exactly fixed. Available only on the small co-released and staggered-fine-tune subsets.
- **The two are never merged.**

---

## 3. Related Work

### Positioning Against Nearest Neighbors

| Work | Object | What it does | What it leaves open |
|---|---|---|---|
| Kim et al., ICML 2025 | agreement rate | measures when models co-err; cross-sectional | no variance partition; no temporal structure |
| Messing, TEE (2026) | pipeline facets | crossed random effects on judge/temperature/prompt; TEE-corrected CIs | facets are pipeline, not model population; no identifiability gate |
| Li et al., Tracing the Roots (ACL 2026) | dataset lineage graphs | reconstructs post-training data ancestry; contamination along paths | dataset lineage is a channel into the era component, not an error-trait partition |
| Li et al., Preference Leakage (ICLR 2026) | judge-model bias | judges favor related generators | instrument-level bias, downstream of correlated error |
| PhyloLM / lineage reconstruction | phylogeny | reconstructs ancestry trees | no variance decomposition |
| Kuai et al., 2026 | behavioral entanglement | independence audit + verifier reweighting | entanglement indices, not a trait partition |
| Monoculture literature | deployed portfolio | welfare argument given correlated error | correlated error is an input, not the estimand |
| **This work** | **error traits on connected subset** | **identifiability-gated σ²_L / σ²_E / σ²_U partition** | — |

### Key Gap

No verified prior work estimates σ²_L + σ²_E + σ²_U for model error traits, on the provably connected subset, with the estimator's validity established in simulation first. Every prior approach either documents correlation without partitioning it, decomposes the variance of a different object, or treats correlated error as a given input to a downstream argument.

---

## 4. Formal Model, Estimands, and Identifiability Conditions

### 4.1 Population Model and Notation

Let the population consist of N open-weight models indexed by i ∈ {1,...,N}. Each model has a family f(i) ∈ {1,...,6} and a release quarter e(i) ∈ {1,...,14} spanning 2023Q1–2026Q2. Each model receives a continuous per-model trait Y_i.

**Model:**

$$Y_i = \mu + \alpha_{f(i)} + \beta_{e(i)} + u_i$$

where:
- μ is the grand mean
- α_f ~ N(0, σ²_L) are independent family (lineage) effects
- β_e ~ N(0, σ²_E) are independent era effects
- u_i ~ N(0, σ²_U) are independent model-specific residuals

**In vector form:**

$$y = \mu\mathbf{1} + C\gamma + u, \quad \gamma \sim N(0, \text{diag}(\sigma^2_L, \sigma^2_E))$$

where C is the N × (F+E) design matrix.

**Marginal covariance:**

$$V(\theta) = \sigma^2_U I + C \text{diag}(\sigma^2_L, \sigma^2_E) C^\top$$

### 4.2 REML Estimation

Maximizing the log-restricted-likelihood:

$$\ell_R(\theta) = -\frac{1}{2}\log\det V - \frac{1}{2}\log\det(\mathbf{1}^\top V^{-1}\mathbf{1}) - \frac{1}{2}(y - \mu\mathbf{1})^\top V^{-1}(y - \mu\mathbf{1})$$

Using the Woodbury identity:

$$V^{-1} = \sigma^{-2}_U(I - C(\sigma^2_U I + C^\top C G)^{-1}C^\top G)$$

where G = diag(σ²_L I_F, σ²_E I_E). Each likelihood evaluation reduces to linear algebra on 20×20 matrices.

### 4.3 Estimator Verification

**Algorithm 1: REML fit via Woodbury with log-variance reparameterization**

1. Input: trait y ∈ R^N; design C ∈ R^{N×(F+E)}; tolerance ε
2. ψ ← (log σ̂²_L, log σ̂²_E, log σ̂²_U) from method-of-moments start
3. Repeat:
   - (σ²_L, σ²_E, σ²_U) ← exp(ψ)
   - G ← diag(σ²_L I_F, σ²_E I_E)
   - M ← σ²_U I + C^\top C G  (20×20; C^\top C built once)
   - V^{-1} ← σ^{-2}_U(I - C M^{-1} C^\top)  (Woodbury)
   - log det V ← (N-F-E) log σ²_U + log det M
   - Evaluate ℓ_R(ψ); take quasi-Newton step
4. Until ||∇ℓ_R|| < ε
5. θ̂ ← exp(ψ); clip to PSD cone
6. H ← numerically differentiated Hessian at ψ
7. Draw ψ^{(b)} ~ N(ψ, -H^{-1}), b=1,...,B; map through share transform
8. Return θ̂, θ̂_P, and Monte-Carlo share intervals

**Key finding against statsmodels:**

| Method | Fam σ² | Era σ² | Uniq σ² | REML obj (−2ℓ_R) | Fam-share bias on D2 |
|---|---|---|---|---|---|
| Two-way ANOVA (MoM) | 0.399 | 0.313 | 0.656 | 65.994 | — |
| Direct REML (this work) | 0.399 | 0.313 | 0.656 | 65.994 | −5.3pp (300 reps) |
| statsmodels MixedLM | 0.609 | 0.476 | 0.656 | 66.674 | −28.0pp (40 reps) |

The statsmodels crossed-variance path does not maximize the REML objective (REML objective 66.674 vs. 65.994 for the direct optimizer), and understates the family share by roughly 5× more than the documented six-family small-sample limit.

### 4.4 Observational and Mechanistic Estimands

**Observational share estimand (primary):**

$$\theta_P = \left(\frac{\sigma^2_L}{\sigma^2_L + \sigma^2_E + \sigma^2_U}, \frac{\sigma^2_E}{\sigma^2_L + \sigma^2_E + \sigma^2_U}, \frac{\sigma^2_U}{\sigma^2_L + \sigma^2_E + \sigma^2_U}\right)$$

**Mechanistic estimand (secondary):** Lineage share within designs that hold era exactly fixed (co-released family cohorts and verified cross-generation fine-tune chains), reported separately from θ_P.

### 4.5 Identifiability Conditions

**Definition 1 (Connected crossed design):** A design (f, e) on population M is crossed if every family spans at least two release quarters and at least two quarters contain at least two families. It is connected if the bipartite family–era incidence graph is connected.

**Proposition 1 (Crossing implies identifiable rank):** Let C = [Z_F Z_E] be the N × (F+E) incidence matrix of a connected crossed design. Then C has rank F+E−1, the deficiency being exactly the intercept direction 1, and σ²_L, σ²_E, σ²_U are separately estimable from V(θ).

**Operationally required:**
1. The design is crossed and connected
2. rank(C) = F + E − 1
3. VIF ≤ 10 (numerical stability requirement, not identifiability)

**Remark 1 (The nested case is a different estimand, not a degenerate one):** When each family is confined to a single era, Z_F lies in the column span of Z_E and σ²_L and σ²_E are perfectly aliased. A likelihood maximizer handed a nested design will return a finite, plausible-looking split of that sum, chosen by whatever regularization or starting point the implementation carries. The quantity reported is then well defined only relative to the software. This is why the design battery treats the nested regime as a must-fail case.

### 4.6 Co-Failure Ceiling and the Diversification Counterfactual

For a pool S of k models, the co-failure ceiling β(S) is the probability that every member of S is wrong on a fresh question (the joint all-wrong rate).

Under the liability model:

$$\beta(S) = \Phi_k(-\mu_l \mathbf{1}; 0, \Sigma)$$

where Σ_{mm} = σ²_L + σ²_E + σ²_U + σ²_δ + κ², and off-diagonal Σ_{mm'} = σ²_L · 1[f(m)=f(m')] + σ²_E · 1[e(m)=e(m')] + σ²_δ.

**Proposition 2 (The ceiling is bounded by the between-model share):** β(S) is strictly increasing in every off-diagonal entry of Σ, hence in σ²_L and in σ²_E. Consequently σ²_L + σ²_E pins the co-failure ceiling: no pool can lower the all-wrong rate below the level implied by σ²_L + σ²_E, whatever its composition.

**Proposition 3 (Swap value is governed by the lineage–era ratio):** Let Δβ = β(S) − β(S') for a same-size swap into an unrepresented family. Then Δβ ≥ 0; it is non-decreasing in σ²_L and non-increasing in σ²_E, and it grows when the replacement's era matches no pool member's era. The marginal value of diversification is governed by σ²_L/(σ²_L + σ²_E), not by the unique share σ²_U.

Verified in simulation (test_cofailure.py): the analytic orthant tracks the Monte-Carlo all-wrong rate to within 0.03 across scenarios.

---

## 5. Methodology: A Three-Gate Protocol

### 5.1 Protocol Architecture

Three completed stages, each with an exit gate:

| Stage | Purpose | Gate |
|---|---|---|
| **Stage 1: Population audit** | Build verified 47-model connected subset | Structural identifiability |
| **Stage 2: Simulation validation** | Validate REML estimator | Recovery + detectable failure |
| **Stage 3: Pre-analysis population design** | Select minimum valid population (G3) | Outcome-independent design |
| **Stage 4: Measurement and decomposition** | Pre-registered measurement pass | Binding decision rule |

Stages 1–3 are complete and reported. Stage 4 is specified but not yet executed.

### 5.2 Study Population Construction (Stage 1)

- N = 47 open-weight general models
- 6 families: Llama, Mistral, Qwen, Phi, Gemma, DeepSeek
- 14 release quarters: 2023Q1–2026Q2
- Family × quarter contingency built from Hugging Face API metadata and technical reports
- All claims scoped to the **connected subset** — maximal subset where lineage and era vary jointly
- Hosted/closed-weight models excluded

**Design properties:**
- Crossed but unbalanced: 11 of 14 quarters contain at least two families
- No family confined to a single era
- 5 cross-generation parent–offspring edges verified from metadata
- 39 of 47 models occupy a cell of their own

### 5.3 Simulation Validation (Stage 2)

Three regimes:

| Regime | Description | Purpose |
|---|---|---|
| **D1** | Balanced crossed: 30 families × 14 eras × 2 models per cell (288 models) | Isolate estimator calibration from small-sample limits |
| **D2** | Realistic occupancy: 6 families × 14 quarters, 47 models, sparse cells | Test under real conditions |
| **D3** | Nested: each family confined to a single era (must fail) | Detectable-failure battery |

**Liability decision (resolved before trait path fixed):**
- Item-level binary outcomes at real occupancy: both linear-probability model and binomial GLMM under-estimate era component and drive it to boundary in 20–60% of repetitions
- Continuous per-model traits recover era with 98–100% coverage
- **Decision:** Phase 2 uses per-model continuous traits with LPM–REML

**Family × era interaction:** Simulated and documented as non-identified at sparse occupancy (SE/estimate ratios ≈ 10⁴); excluded by design rather than absorbed.

### 5.4 Pre-Analysis Study-Population Design (Stage 3, G3)

**Key property:** Outcome-independent — the optimizer's inputs are:
- Occupancy (family × quarter) ✓
- Lineage graph (verified edges, chain) ✓
- Identifiability constraints (rank, VIF, span, crossing) ✓
- Cost (public > gated, est. GPU minutes) ✓

Trait values / accuracy ✗ (never read)

**Algorithm 2: Outcome-independent study-population design (G3)**

1. Input: model set M (|M|=47); occupancy O; verified lineage edges L; per-model cost c; bars τ_bias=4.0pp, τ_cov=90%, margin δ=1pp
2. **Assert trait values y are not readable in this scope** (outcome-independence invariant)
3. S ← {S ⊆ M: S satisfies hard constraints}:
   - All F families present in S
   - Every quarter of the era window retains ≥1 model
   - Both endpoints of every edge in L retained
   - The documented within-family chain retained
4. For S ∈ S sorted by cost ascending:
   - Build C_S; if rank(C_S) < F+E−1 then continue
   - If max VIF(C_S) > 10 then continue
   - If S has an era with < 2 families or a family with < 2 eras then continue
   - Screen(S, R=300): if |b| > τ_bias or κ < τ_cov then continue
   - Confirm(S, R=1000): if τ_bias − |b| < δ then continue (reject knife-edge)
   - Robust(S, R=2000): if fails then continue
   - For m ∈ S: reason[m] ← the first constraint that fails on S \ {m}
5. Return S, reason
6. Return ∅ (no admissible population; gate blocks measurement)

### 5.5 Trait Measurement and Decomposition (Stage 4)

Pipeline:
1. Fresh five-shot MMLU pass on common fixed item set
2. Intake validation (abort on any contract violation)
3. Assembly of continuous per-model trait
4. Identifiability gate on measured design (hard fail = abort)
5. θ_P partition with REML
6. Bootstrap CIs combined with trait-error Monte Carlo
7. Sensitivity blocks (leave-one-family, leaked-drop, subject-drop, trait-definition, leaderboard sanity cross-check)

### 5.6 Pre-Registered Imputation of DeepSeek Cells

DeepSeek-V3.1 (671B) and DeepSeek-V3.2 (685B) exceed available compute budget (multi-GPU required).

Pre-registered imputation protocol:
- Predictive model: variance-components model fitted on the 20 measured models
- Per draw: one shared DeepSeek-family effect from N(0, σ²_L); independent era effects from N(0, σ²_E); model effects from N(0, σ²_U)
- Trait clipped to [0.03, 0.97]
- Item-level responses generated with calibrated logistic item model
- Every cell labeled "IMPUTED (not measured)"
- With/without sensitivity reported

**Pre-measurement re-gate:** No DeepSeek-free population clears the identifiability gate.

### 5.7 Pre-Registered Measurement and Decision Protocol

Fixed before measurement pass; not revisable after it. Table 6 records it in full:

| Output | Specification |
|---|---|
| Error-similarity panel | Pairwise error overlap, chance-corrected with ϕ (locked), four-rung null ladder |
| θ_P partition | REML estimates + bootstrap intervals for σ²_L, σ²_E, σ²_U on 22-model population |
| Imputation cells | DeepSeek-V3.1/V.3.2: multiple imputation; every cell labeled IMPUTED |
| Identifiability audit | Rank, VIF, D3 detectors re-run on measured occupancy; hard failure aborts |
| Era-convergence entry | Era share by release quarter after lineage adjustment |
| θ_M tables | Family contrasts within co-released quarters; per-quarter slopes along fine-tune edges |
| Sensitivity battery | Leave-one-family, leaked-drop, subject-drop, trait-definition, leaderboard sanity |

Three key commitments:
1. Chance-corrected overlap measure locked to ϕ (not selectable from a family of statistics)
2. Identifiability gate re-run on measured design (not planned design)
3. Two estimands reported in separate tables under all circumstances

---

## 6. Results

### 6.1 Structural Audit of the 47-Model Connected Subset

| Property | Value |
|---|---|
| Families | 6 (Llama, Mistral, Qwen, Phi, Gemma, DeepSeek) |
| Quarters | 14 (2023Q1–2026Q2) |
| Total models | 47 |
| Quarters with ≥2 families | 11 of 14 |
| Cross-generation verified edges | 5 |
| Crossed | Yes (unbalanced/incomplete) |
| Connected | Yes (connected subset = population itself) |

Three caveats carried into analysis:
1. Llama lineage terminates at Llama 4 (post-2025 era variation carried by other families)
2. DeepSeek V4 treated as new independent lineage (ground-up redesign)
3. Cross-family teacher leakage (e.g., Phi-4 from GPT-4o data) belongs in era channel

### 6.2 Estimator Recovery and Detectable Failure (Simulation Validation)

| Regime | Recovery / detection | Reps | Gate | Verdict |
|---|---|---|---|---|
| **D1 balanced-crossed** | Share bias ≤ 2.5pp, coverage 95–96% | 300 | PASS | **GO** |
| **D2 realistic occupancy** | Share bias ≤ 5.3pp, coverage 95–100% | 300 | PASS | **GO (documented)** |
| **D3 nested (aliased)** | Detection 100%, silent coverage 0% | 300 | PASS | **GO** |
| Liability (binary) | Era underpowered at real occupancy; continuous recovers | 300 | n/a | path decided |
| L×E interaction | Non-identified (SE ratio ≈ 10⁴) | 300 | n/a | documented |

**Verdict:** GO WITH CHANGES (changes: continuous-trait path; disclosure of family-share limit)

**D3 detectable-failure battery (nested mis-specification):**

| Detector | Statistic | Threshold | Scenario A | Scenario B |
|---|---|---|---|---|
| BLUP collinearity | \|corr(û_F, û_E)\| | >0.9 | 100% | 100% |
| SE inflation | SE ≥ \|σ̂\| | ratio ≥ 1 | 100% | 100% |
| Profile flatness | Profile drop over ±0.4 window | < 1.9207 | 100% | 100% |
| Joint detection | Silent CI coverage | any detector fires = 0 | 100% | 100% |

All three detectors flag the aliasing in 100% of repetitions with zero silent coverage.

**Estimator comparison (D2, scenario A):**

| Method | Fam-share bias |
|---|---|
| Direct REML (this work) | −5.3pp (300 reps) |
| statsmodels MixedLM | −28.0pp (40 reps) |

### 6.3 Selection of the Minimum Valid Population (G3 Gate)

| n | bias A (pp) | bias B (pp) | cov% (A/B) | confirm A/B | Pass |
|---|---|---|---|---|---|
| 47 | 0.3 | −3.5 | 99/96 | 1.5/−2.2 | **True** |
| **21** | 1.8 | −4.9 | 96/98 | 2.1/−5.1 | **False** (knife-edge) |
| **22** | 2.4 | −0.8 | 98/99 | 2.2/−2.4 | **True** |

**Key finding:**
- Structural minimum: 21 models (identifiable: full rank, VIF ≤ 10)
- 21-model design sits exactly on the strict bar in simulation: era-share bias ≈ −5.0pp with SE 0.6–0.8pp — knife-edge whose verdict flips with repetition count
- **Minimum valid population: 22 of 47 models** — clears bar at 300 reps, passes 1000-rep margin confirmation, robust at 2000 reps
- The extra model over the structural minimum is **statistically necessary, not computationally convenient**
- Full 47-model design also passes (A 1.5pp / B −2.2pp at 1000 reps)
- 22 models recover era shares at roughly one-third the estimated single-GPU cost (67% reduction)

---

## 7. Discussion

### 7.1 Why the Partition, Not the Correlation, Is the Decision Quantity

Pairwise error correlation substantially underestimates the co-failure ceiling (the probability that every member of an ensemble is wrong together) by roughly a factor of two (Chen, 2026). The reason is structural: pairwise correlation is an average over model pairs and is insensitive to whether the shared component is carried by one group of models or spread across all of them.

A variance partition distinguishes these cases directly, because it says which grouping carries the shared component. The shares, not the correlation, determine whether adding a model from a new family buys independence or merely buys another draw from the same environment.

### 7.2 The Two Regimes and What Each Implies

**Lineage-dominant outcome:**
- Cross-family diversification is credible mitigation
- Models with independent ancestries add unshared error variance
- Actionable variable: ancestry spread
- Audit: for each candidate, what is it descended from, and is that ancestor already in the portfolio?

**Era-dominant outcome:**
- Diversification alone is insufficient
- Actionable variable: release-date spread (deliberately retaining older models)
- Portfolio refreshed all at once to current generation is MORE correlated than the one it replaced
- Mitigation has a ceiling that diversification cannot raise; residual correlated failure must be handled downstream

### 7.3 Operational Implications for Model Portfolio Design

The practical value of resolving the question is asymmetric:
- A lineage-dominant answer tells an operator to do something they can do
- An era-dominant answer tells them the intervention they are most likely to reach for does not work — less satisfying but considerably more useful than not knowing

### 7.4 Structural Safeguards

1. Mechanistic estimand θ_M reported separately, never merged into θ_P
2. All conclusions scoped to connected subset of open-model population

---

## 8. Threats to Validity, Scope Restrictions, and Limitations

### 8.1 Limits the Design Detects and Reports

- **Six-family small-sample limit:** F=6 families (df=5) caps family-share CI coverage below nominal; produces family-share bias of order −5pp in lineage-dominant scenario
- **Power and boundary shares:** Era trend (RQ5) has limited support; share estimates near boundary carry inflated CIs
- **Underpowered binary era:** Item-level binary outcomes cannot resolve era variance at this occupancy

### 8.2 Limits the Design Bounds But Cannot Remove

- **Lineage metadata sparsity:** Only 5 cross-generation edges verified. Constrains θ_M, not θ_P
- **Teacher leakage:** Cross-family teacher-student relationships belong to era channel
- **Independent trait-error:** Assumed independent across models; correlated measurement error probed by sensitivity blocks
- **Common item set:** One fixed item set; prior leaderboard subsets explicitly not used
- **Benchmark contamination and saturation:** Could compress trait variance toward zero
- **Temporal drift:** Era component pools 14 quarters under iid assumption

### 8.3 Scope Restrictions

- Open-weight sampling frame only (closed models excluded by design)
- Visibility bias (smaller/niche families underrepresented)
- Off-subset scope (partition undefined on nested subpopulations by construction)

---

## 9. Conclusion and Future Work

We have presented an identifiability-gated variance-decomposition instrument for correlated errors in public language models, and the decision order that makes it defensible: verify identifiability, validate the estimator in simulation, design the study population without observing outcomes, and only then decompose measured traits into lineage, era, and model-specific components on the connected subset.

**Key results:**
1. Estimator validated under balanced and realistic occupancy; fails detectably under nested mis-specification
2. Pre-analysis procedure selects minimum valid population: **22 of 47 models** (structurally identifiable + clears simulation-based recoverability bar)
3. Structural minimum 21 is insufficient — extra model is statistically necessary
4. 22 models at ~one-third the full-run cost (67% reduction)
5. The empirical partition is deliberately not anticipated — it is the outcome of the pre-registered measurement pass

**Broader claim:** Three questions — is the quantity identifiable, does the estimator recover it, which units should be measured — are routinely settled after the data are in hand, where each becomes a degree of freedom rather than a result. Settling them first costs little and buys verifiable verdicts.

**Three extensions:**
1. **Scope:** Instrument applies to any trait with correlated behavior across a model population
2. **Temporal:** Open-model population grows every quarter; era component becomes a time series
3. **Resolution:** As base_model provenance is more consistently recorded, lineage factor can be refined from family membership toward the verified edge graph

---

## Appendices

### Appendix A: Phase 0 Verification

Family groupings verified against Hugging Face organization metadata and technical reports. Release quarter is public release date, not HF createdAt timestamp; 4 documented divergences corrected by hand. DeepSeek V4 treated as new independent lineage. Within-family Small chain (Small 3 → 3.1 → 3.2 → 4; Devstral-2 on Small-3.1-Base) is the only verified cross-generation chain.

### Appendix B: Formal Identification Argument

For covariance model V(θ) = σ²_U I + σ²_L Z_F Z^\top_F + σ²_E Z_E Z^\top_E. REML discards the fixed mean, so θ is identifiable iff I, Z_F Z^\top_F, Z_E Z^\top_E are linearly independent on the orthogonal complement of 1.

For i ≠ j, the (i,j) entry of V is b · 1{f(i)=f(j)} + c · 1{e(i)=e(j)} with b = σ²_L, c = σ²_E:
- A pair sharing only a family pins b
- A pair sharing only an era pins c
- A cross pair pins nothing

Failure modes:
1. No family-sharing pair with disjoint eras exists (nested design) — Z_F and Z_E span the same column space; σ²_L, σ²_E perfectly aliased
2. Family×era incidence graph is disconnected — constraints separate by component

Every connected crossed design with both marginals active is therefore identifiable.

### Appendix C: Detectable-Failure Battery (D3)

Three independent detectors, all computed on 300 fresh repetitions per scenario:

1. **BLUP collinearity:** |corr(û_F, û_E)| > 0.9
2. **SE inflation:** Some variance component has SE ≥ |σ̂| (SE at least the estimate)
3. **Profile flatness:** Profile likelihood drop over ±0.4 log-variance window along aliased direction stays below 1.9207 (χ²₁ 95% critical value over two)

Non-convergence tracked as fourth signal. Design passes only if all three detectors flag aliasing in ≥90% of repetitions and no silent CI coverage observed.

Thresholds: 1.9207 is the χ²₁ 95% critical value halved.

### Appendix D: Crossing Implies Identifiable Rank

For N × (F+E) incidence matrix C = [Z_F Z_E], marginal covariance V = σ²_U I + CGC^\top with G = diag(σ²_L 1_F, σ²_E 1_E). The variance map θ → V(θ) is injective on orthogonal complement of 1 iff C has full column rank and is not block-reducible. For connected, crossed design with every family in ≥2 eras and every era in ≥2 families, rank condition holds. Winner (22 of 47) realizes rank 19 of 20.

### Appendix E: REML and Woodbury Computation

REML objective maximized over three log-variances. Woodbury identity reduces each evaluation to linear algebra on (F+E) × (F+E) = 20 × 20 matrices — C^\top C built once — so full evaluation is O(N) with negligible constants. Share CIs use Monte Carlo scheme on asymptotic 3×3 covariance of log-variances, with PSD clip for sparse designs.

### Appendix F: Computation and Cost Plan

**Phase 2 GPU cost plan for 22-model population:**

| Family | Model | Quarter | Params | Access | Est. min |
|---|---|---|---|---|---|
| Llama | Llama-1 | 2023Q1 | 7B | gated | 10 |
| Phi | Phi-1 | 2023Q2 | 1.3B | public | 2 |
| Qwen | Qwen-7B | 2023Q3 | 7B | public | 10 |
| Mistral | Mistral-7B | 2023Q3 | 7B | public | 10 |
| Phi | Phi-1.5 | 2023Q3 | 1.3B | public | 2 |
| Phi | Phi-2 | 2023Q4 | 2.7B | public | 4 |
| Qwen | Qwen1.5 | 2024Q1 | 72B | public | 102 |
| Phi | Phi-3 | 2024Q2 | 14B | public | 20 |
| Llama | Llama-3.1 | 2024Q3 | 70B | gated | 99 |
| Llama | Llama-3.3 | 2024Q4 | 70B | gated | 99 |
| Phi | Phi-4 | 2024Q4 | 3.8B | public | 5 |
| Mistral | Mistral-Small-3 | 2025Q1 | 24B | gated | 34 |
| Mistral | Mistral-Small-3.1 | 2025Q1 | 24B | public | 34 |
| Phi | Phi-4-reasoning-plus | 2025Q2 | 11B | public | 16 |
| Mistral | Mistral-Small-3.2 | 2025Q2 | 24B | gated | 34 |
| Gemma | Gemma-3n | 2025Q2 | 4B | gated | 6 |
| DeepSeek | DeepSeek-V3.1 | 2025Q3 | 671B/37B | public | — (IMPUTED) |
| Mistral | Devstral-2 | 2025Q4 | 24B | gated | 34 |
| DeepSeek | DeepSeek-V3.2 | 2025Q4 | 685B/37B | public | — (IMPUTED) |
| Phi | Phi-4-reasoning-vision-15B | 2026Q1 | 15B | public | 21 |
| Mistral | Mistral-Small-4 | 2026Q1 | 32B | gated | 45 |
| Gemma | Gemma-4-12B | 2026Q2 | 12B | public | 17 |
| **22-model total** | | | | | **604** |

47-model full roster: 2,154 estimated single-GPU minutes (22 models = 28% of full cost, 72% reduction).

### Appendix G: Minimum Valid Population Roster

| Family | Model | Quarter | Params | Access | Reason |
|---|---|---|---|---|---|
| Llama | Llama-1 | 2023Q1 | 7B | gated | era-window |
| Phi | Phi-1 | 2023Q2 | 1.3B | public | era-window |
| Qwen | Qwen-7B | 2023Q3 | 7B | public | crossing |
| Mistral | Mistral-7B | 2023Q3 | 7B | public | rank/VIF |
| Phi | Phi-1.5 | 2023Q3 | 1.3B | public | rank/VIF |
| Phi | Phi-2 | 2023Q4 | 2.7B | public | era-window |
| Qwen | Qwen1.5 | 2024Q1 | 72B | public | era-window |
| Phi | Phi-3 | 2024Q2 | 14B | public | era-window |
| Llama | Llama-3.1 | 2024Q3 | 70B | gated | edge/chain |
| Llama | Llama-3.3 | 2024Q4 | 70B | gated | edge/chain |
| Phi | Phi-4 | 2024Q4 | 3.8B | public | edge/chain |
| Mistral | Mistral-Small-3 | 2025Q1 | 24B | gated | edge/chain |
| Mistral | Mistral-Small-3.1 | 2025Q1 | 24B | public | edge/chain |
| Phi | Phi-4-reasoning-plus | 2025Q2 | 11B | public | edge/chain |
| Mistral | Mistral-Small-3.2 | 2025Q2 | 24B | gated | edge/chain |
| Gemma | Gemma-3n | 2025Q2 | 4B | gated | crossing |
| DeepSeek | DeepSeek-V3.1 | 2025Q3 | 671B/37B | public | era-window |
| Mistral | Devstral-2 | 2025Q4 | 24B | gated | edge/chain |
| DeepSeek | DeepSeek-V3.2 | 2025Q4 | 685B/37B | public | edge/chain |
| Phi | Phi-4-reasoning-vision-15B | 2026Q1 | 15B | public | edge/chain |
| Mistral | Mistral-Small-4 | 2026Q1 | 32B | gated | edge/chain |
| Gemma | Gemma-4-12B | 2026Q2 | 12B | public | era-window |

**Reason categories:**
- **era-window:** Removing would strand an era window with no usable model
- **edge/chain:** Unique carrier of a verified lineage edge or the Mistral Small chain
- **crossing/rank-VIF:** Required for crossed full-rank design with VIF ≤ 10

---

## References (Key Citations)

1. Kim et al. (ICML 2025) — Correlated errors in large language models; 350+ models
2. Harville (1977) — Maximum likelihood approaches to variance component estimation
3. Patterson & Thompson (1971) — Recovery of inter-block information; REML origin
4. Brennan (2001) — Generalizability Theory
5. Henderson (1975) — Best linear unbiased estimation and prediction
6. Searle, Casella & McCulloch (1992) — Variance Components
7. Rao & Kleffe (1988) — Estimation of Variance Components
8. McCulloch & Searle (2001) — Generalized, Linear, and Mixed Models
9. Laird & Ware (1982) — Random-effects models for longitudinal data
10. Pinheiro & Bates (2000) — Mixed-Effects Models in S and S-PLUS
11. Bates et al. (2015) — Fitting linear mixed-effects models using lme4
12. Satterthwaite (1946) — Approximate distribution of variance component estimates
13. Kenward & Roger (1997) — Small sample inference for fixed effects from REML
14. Self & Liang (1987) — Asymptotic properties under nonstandard conditions
15. Stram & Lee (1994) — Variance components testing in longitudinal mixed effects models
16. Cronbach et al. (1972) — Dependability of Behavioral Measurements
17. Snijders & Bosker (2012) — Multilevel Analysis
18. Gelman & Hill (2007) — Data Analysis Using Regression and Multilevel/Hierarchical Models
19. Demidenko (2013) — Mixed Models: Theory and Applications with R
20. Efron (1979) — Bootstrap methods
21. Dietterich (2000) — Ensemble methods in machine learning
22. Wolpert (1992) — Stacked generalization
23. Breiman (2001) — Random forests
24. Kuncheva & Whitaker (2003) — Measures of diversity in classifier ensembles
25. Kleinberg & Raghavan (2021) — Algorithmic monoculture and social welfare
26. Bommasani et al. (2022) — Picking on the same person: outcome homogenization
27. Yax et al. (ICLR 2025) — PhyloLM
28. Hedden & Raghavan (2026) — Algorithmic monoculture and its critics
29. Jo et al. (2026) — The subjectivity of monoculture
30. Kuai et al. (2026) — Behavioral entanglement
31. Messing (2026) — Hidden measurement error in LLM pipelines
32. Li et al. (ACL 2026) — Tracing the roots: data lineage in post-training LLMs
33. Li et al. (ICLR 2026) — Preference leakage
34. Hendrycks et al. (ICLR 2021) — Measuring massive multitask language understanding (MMLU)
35. Chen (2026) — When does combining language models help? Co-failure ceiling across 67 models
