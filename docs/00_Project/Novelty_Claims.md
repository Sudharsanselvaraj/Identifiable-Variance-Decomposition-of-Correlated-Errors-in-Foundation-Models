# 03 Novelty Claims

Every novelty claim of the program, with closest paper, difference, likely reviewer
attack, defense, and confidence. Rule: **no claim without its differentiation-table
entry.** Every claim below is tied to the verified ledger in
`docs/01_Literature/Literature_Map.md`.

| Claim | Evidence | Closest paper | Difference | Reviewer attack | Defense | Confidence | Status |
|---|---|---|---|---|---|---|---|
| C1. First variance partition of foundation-model error traits into lineage / era / model-unique components | Design is crossed (Phase 0); estimator validated in Phase 1; no prior work estimates V_lineage + V_era + V_unique | Kim et al., Correlated Errors (ICML 2025) | Kim measures cross-sectional agreement (60%-when-both-err); we decompose covariance into components. Kim leaves causality/temporality open | "Kim already showed shared architecture/provider drive correlation" | Different object (agreement rate vs. variance partition); different question (where correlation concentrates vs. how much is lineage vs. era); Kim is cross-sectional by design | Medium | Phase 1 passed (D1/D2 share recovery under D2 occupancy); Phase 2 pending |
| C2. Identifiability-gated design: the crossed-vs-nested question decides whether the decomposition is runnable at all | Phase 0 connectivity audit (2026-08-02): CROSSED, gate PASS; D3 nested must fail in simulation | None in the correlated-error literature (TEE applies G-theory to pipelines without an identifiability gate over model populations) | We gate the analysis on the connected subset; no prior work treats population identifiability as a precondition | "Everyone knows crossed designs are identified" | Known in variance-components theory, but not enforced as a gate over model populations; Phase 0 shows the field's assumption of independence is unmet (nested subpopulations exist) | High | Phase 0 passed |
| C3. Simulation-first validity: no real-data claim precedes Phase 1 validation | Phase 1 plan (D1/D2/D3 + liability test) | TEE (G-theory pipelines) validates its own estimator, but on pipeline facets, not model populations with sparse occupancy | We validate under the actual Phase 0 occupancy and require the nested case to fail detectably | "Simulation validation is standard practice" | Standard in principle, but the D3-must-fail requirement (silent-bias detection) is the specific guardrail the literature lacks; it decides LPM-REML vs. GLMM | High | Pending Phase 1 |
| C4. Two-estimand structure (θ_P / θ_M) as the guard against the mediator–confounder collapse of release year | Estimand fixed in master prompt; release year is both mediator and confounder | Kim et al. (no temporal structure); PhyloLM (no variance decomposition) | θ_M (mechanistic, era held fixed) is reported separately and never merged into θ_P (observational); neither claims to be the "true" causal share | "Why not one causal estimate?" | A single estimate would conflate the mediator and confounder roles of release year; the pair brackets the truth and is the only honest decomposition available | High | Estimand fixed |
| C5. Differentiated statistical object vs. entanglement indices: orthogonal variance components with a separate era channel, not composite behavioral indices | Kuai et al. (2026, arXiv 2604.07650) audit behavioral entanglement across ~18 LLMs / 6 families with information-theoretic indices (Difficulty-Weighted BEI, Cumulative Information Gain) | Kuai et al., "How Independent Are Large Language Models? A Statistical Framework for Auditing Behavioral Entanglement and Reweighting Verifier Ensembles" | Different object: entanglement indices (composite, no component split) vs. our orthogonal V_lineage / V_era / V_unique; Kuai groups by family but does not separate lineage from era and has no identifiability gate | "Kuai already audits family-grouped correlated behavior at similar scale and recency — why REML variance components instead of entanglement indices?" | Different statistical tool (indices vs. variance decomposition), no era/lineage separation, and no identifiability-before-claims gate in Kuai; the θ_P/θ_M two-estimand rule is precisely what Kuai lacks. Head-to-head row added 2026-08-16 (AE review follow-up) | High (differentiation), Medium (headroom) | Pending Phase 2 |
| C6. Outcome-blind population design (G3): the model roster is shrunk 47→22 on occupancy, lineage graph, identifiability, and cost alone — never on trait values, accuracies, or eval outputs | `analysis/population_optimizer.py`; G3 report; roster in `manuscript` Table 3 | No competitor pre-registers the population itself; TEE/G-theory design studies fix facets, not the model roster | A pre-registration of the *population*, not just the analysis plan; structurally rules out population-level p-hacking of the trait | "Population pruning is standard" | Pruning here is outcome-blind by construction (no eval data exist at G3 time); it is the population-level analogue of an analysis pre-registration | High | G3 passed (22/47 kept, 67% GPU-min reduction) |
| C7. Decision-layer mapping: the variance partition → counterfactual co-failure ceiling β (all-wrong rate), with the per-swap diversification value expressed as a function of σ²_L / σ²_E | Derived in `docs/02_Theory/CoFailure_Ceiling.md`; validated in simulation against the DGP | Chen (2026) reports the all-wrong ceiling as a function of observed pairwise correlation but does not decompose it; Kim measures the agreement rate | We derive β from the *partition*: σ²_L+σ²_E binds the ceiling, and a cross-family swap removes σ²_L but carries σ²_E — so the swap's value is governed by σ²_L/(σ²_L+σ²_E) | "Chen already has the target quantity" | Chen gives the quantity, not the decomposition that says which intervention moves it; we supply the exact mapping | High (derivation), Medium (empirical) | Derivation + simulation validated (2026-08-16); empirical number pending Phase 2 |

## Consolidated novelty statement (from proposal §5.3)

No verified work estimates V_lineage + V_era + V_unique for model error traits, on the
provably connected subset, with the estimator's validity established in simulation first.
Every prior work either (a) documents correlation without partitioning it (including
entanglement indices and co-failure ceilings), (b) decomposes
variance of the wrong object (pipeline facets, dataset lineage), or (c) treats correlated
error as a given input to a welfare argument.

## Inference vs. speculation

- **Inference (settled):** Phase 0 design is crossed (unbalanced/incomplete); 5 verified
  cross-generation `base_model` edges; teacher leakage belongs in the era channel;
  DeepSeek V4 is a new lineage.
- **Speculation (not yet earned):** any statement about the size of V_lineage vs. V_era
  on real data, and any diversification recommendation. These become earned only after
  Phase 2, and only with the register's honesty rules applied.

## Explicitly not novelty claims (do not list as contributions)

- The `statsmodels` REML discrepancy (66.674 vs 65.994 objective value) is a bug report on
  a third-party library — useful, kept in the appendix, but incidental to the paper's
  contributions.
- Nothing about the REML estimator, the Woodbury-identity speedup, or the crossed-random-
  effects model is novel (Harville 1977; Patterson–Thompson 1971; Searle/Casella/
  McCulloch). The novelty is in *what* the machinery is applied to and *how* it is gated —
  never in the math itself.
