# 03 Novelty Claims

Every novelty claim of the program, with closest paper, difference, likely reviewer
attack, defense, and confidence. Rule: **no claim without its differentiation-table
entry.** Every claim below is tied to the verified ledger in
`docs/01_Literature/Literature_Map.md`.

| Claim | Evidence | Closest paper | Difference | Reviewer attack | Defense | Confidence | Status |
|---|---|---|---|---|---|---|---|
| C1. First variance partition of foundation-model error traits into lineage / era / model-unique components | Design is crossed (Phase 0); estimator validated in Phase 1; no prior work estimates V_lineage + V_era + V_unique | Kim et al., Correlated Errors (ICML 2025) | Kim measures cross-sectional agreement (60%-when-both-err); we decompose covariance into components. Kim leaves causality/temporality open | "Kim already showed shared architecture/provider drive correlation" | Different object (agreement rate vs. variance partition); different question (where correlation concentrates vs. how much is lineage vs. era); Kim is cross-sectional by design | Medium | Pending Phase 1–2 |
| C2. Identifiability-gated design: the crossed-vs-nested question decides whether the decomposition is runnable at all | Phase 0 connectivity audit (2026-08-02): CROSSED, gate PASS; D3 nested must fail in simulation | None in the correlated-error literature (TEE applies G-theory to pipelines without an identifiability gate over model populations) | We gate the analysis on the connected subset; no prior work treats population identifiability as a precondition | "Everyone knows crossed designs are identified" | Known in variance-components theory, but not enforced as a gate over model populations; Phase 0 shows the field's assumption of independence is unmet (nested subpopulations exist) | High | Phase 0 passed |
| C3. Simulation-first validity: no real-data claim precedes Phase 1 validation | Phase 1 plan (D1/D2/D3 + liability test) | TEE (G-theory pipelines) validates its own estimator, but on pipeline facets, not model populations with sparse occupancy | We validate under the actual Phase 0 occupancy and require the nested case to fail detectably | "Simulation validation is standard practice" | Standard in principle, but the D3-must-fail requirement (silent-bias detection) is the specific guardrail the literature lacks; it decides LPM-REML vs. GLMM | High | Pending Phase 1 |
| C4. Two-estimand structure (θ_P / θ_M) as the guard against the mediator–confounder collapse of release year | Estimand fixed in master prompt; release year is both mediator and confounder | Kim et al. (no temporal structure); PhyloLM (no variance decomposition) | θ_M (mechanistic, era held fixed) is reported separately and never merged into θ_P (observational); neither claims to be the "true" causal share | "Why not one causal estimate?" | A single estimate would conflate the mediator and confounder roles of release year; the pair brackets the truth and is the only honest decomposition available | High | Estimand fixed |

## Consolidated novelty statement (from proposal §5.3)

No verified work estimates V_lineage + V_era + V_unique for model error traits, on the
provably connected subset, with the estimator's validity established in simulation first.
Every prior work either (a) documents correlation without partitioning it, (b) decomposes
variance of the wrong object (pipeline facets, dataset lineage), or (c) treats correlated
error as a given input to a welfare argument.

## Inference vs. speculation

- **Inference (settled):** Phase 0 design is crossed (unbalanced/incomplete); 5 verified
  cross-generation `base_model` edges; teacher leakage belongs in the era channel;
  DeepSeek V4 is a new lineage.
- **Speculation (not yet earned):** any statement about the size of V_lineage vs. V_era
  on real data, and any diversification recommendation. These become earned only after
  Phase 2, and only with the register's honesty rules applied.
