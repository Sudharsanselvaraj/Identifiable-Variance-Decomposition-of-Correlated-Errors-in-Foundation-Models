# Reviewer Questions

Every objection, with answer. Pre-registered likely objections come from the
Novelty_Claims "reviewer attack" column and the Threats-to-Validity file. Populated as
reviews arrive.

## Pre-registered (likely) objections

| Objection | Answer | Source |
|---|---|---|
| "Kim et al. already showed shared architecture/provider drive correlation" | Different object (agreement rate vs. variance partition), different question (documentation vs. decomposition); Kim leaves causality/temporality open | Novelty claim C1 |
| "TEE already did variance decomposition" | Same estimator class, different grouping factors (pipeline facets vs. model traits); composable | Novelty claim C3 / §5.2 |
| "Everyone knows crossed designs are identified" | True in theory; enforced as a gate here over a model population, with the D3-must-fail requirement and the actual (unbalanced) occupancy | Novelty claim C2 |
| "Why not one causal estimate?" | Release year is both mediator and confounder; a single estimate conflates the roles; θ_P/θ_M bracket the truth | Two-estimand rule |
| "The connected subset is small / unrepresentative" | Non-identifiability is a design property, not a data gap; claims are scoped to the connected subset by construction | Scope rules |
| "θ_M has 5 edges — underpowered" | Stated: θ_M is a scoped structural claim with explicit intervals, never a population claim | RQ4 scope |

## From reviews

### External audit (2026-08-05)

| Objection | Answer | Disposition |
|---|---|---|
| "The figures are placeholders / duplicated template art" | Confirmed and fixed: all five `\Figure` blocks used the template's magnetization sample (`fig1.png`) | Replaced with real generated figures (DAG, design, G3 trace) and two explicitly labeled pending placeholders; template plot never used |
| "`kim2025a` (Kim, Liu, Choi — When models agree to be wrong) is not a real paper" | Confirmed fabricated; the real cited work is Kim, Garg, Peng, Garg, "Correlated Errors in Large Language Models" (ICML 2025) | Deleted `kim2025a`; bibliography now matches the verified ledger exactly |
| "The abstract/conclusion decide a question the paper has not answered" | Fair; §VI.D empirical outputs were all pending | Rewritten to honest-methods framing: validated gates + pre-registered protocol, empirical partition explicitly deferred to the measurement pass |
| "The statsmodels 66.674 vs 65.994 claim is uncheckable" | Real and reproducible (direct maximizer vs statsmodels MixedLM; balanced 12×12; decision log 2026-08-03) | Reproducibility pointer added in §Estimators and Appendix C |
| "Orphaned references (lme4) / placeholder bib strings" | Confirmed | Removed `bates2015`, `kim2025a`; filled `phylolm2024`, `monoculture2024` from the verified ledger |
| "2026 work may pre-empt the claims (co-failure ceiling; behavioral entanglement)" | Verified both real (Chen, arXiv:2606.27288; Kuai et al., arXiv:2604.07650) | Cited in Discussion/Related Work as complementary neighbors; the variance-partition estimand remains open |
