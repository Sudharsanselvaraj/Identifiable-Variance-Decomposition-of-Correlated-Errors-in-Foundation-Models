# 02 Hypotheses

Every working hypothesis of the program, with its refutation condition. These are the
"armed" expectations; a hypothesis is refuted when its condition is observed. Statuses
track the Disconfirmability Register (`proposal.md` §8; `docs/06_Results/Negative_Results.md`).

| # | Hypothesis | Phase | Refutation condition | Status |
|---|---|---|---|---|
| H1 | Era variance (V_era) dominates lineage variance (V_lineage|era) on the connected subset. | 2 | V_lineage\|era indistinguishable from 0; or V_lineage share ≥ V_era share | Armed (Phase 2) |
| H2 | Diversification across families alone cannot significantly reduce correlated errors if V_era dominates. | 2 | V_lineage dominates → diversification is credible; H2 drops | Armed (Phase 2) |
| H3 | The era component shows a convergence trend across release quarters (shared error rises after lineage adjustment). | 2 | Flat trend → era-convergence refuted | Armed (Phase 2) |
| H4 | The mechanistic estimand (lineage holding era fixed) is nonzero on co-released cohorts / staggered fine-tunes. | 2 | Zero → mechanistic lineage refuted; nonzero with near-zero primary → primary confounded by era | Armed (Phase 2) |
| H5 | The crossed random-effects estimator recovers known ground truth under realistic occupancy (D2). | 1 | D2 bias/collapse → estimator unfit, no real-data claim | Armed (Phase 1) |
| H6 | A nested design produces detectably unidentifiable variance components (D3 must fail). | 1 | D3 estimates successfully (aliasing not detected) → mis-specification is silent; stop program | Armed (Phase 1) |
| H7 (Phase 3, analogy) | Δerror-response tracks h²·S (breeder's-equation test). | 3 | Does not track → drop the analogy; base decomposition untouched | Armed (Phase 3), gated |

Note: H1–H6 mirror the sub-question refutation conditions in `Research_Questions.md`.
H7 is analogy-layer only and cannot affect the base decomposition either way.
