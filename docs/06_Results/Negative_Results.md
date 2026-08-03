# Negative Results

Honest negative findings are kept — this is the file for them. Current content is the
pre-registered Disconfirmability Register (`proposal.md` §8): the conditions we expect may
refute claims. As Phase 1–3 run, actual negative outcomes get appended here.

## Pre-registered refutation conditions

| # | Condition observed | Claim refuted | Consequence | Status |
|---|---|---|---|---|
| 1 | V_era dominates (Phase 2) | Diversification-as-remedy for the connected population | Recommend era-level mitigation (data, technique), not family diversification | Armed (Phase 2) |
| 2 | Era-convergence trend flat | Era-convergence | Report as table entry; no trend claim | Armed (Phase 2) |
| 3 | Δerror-response does not track h²·S | Breeder's-equation analogy | Drop the analogy; base decomposition untouched | Armed (Phase 3) |
| 4 | Phase 0 connectivity audit fails | The program as scoped | Resampling required before anything else is fundable | Dormant (Phase 0 passed) |
| 5 | D2 bias/collapse (RQ1) | Estimator fitness | No real-data claim; fix or stop | Armed (Phase 1) |
| 6 | Silent mis-specification bias (RQ2) | Instrument validity | Stop program | Armed (Phase 1) |

No softening: a dominated V_era is a real finding for mitigation strategy, not a failure
to be reframed.

## Completed negative findings

- **2026-08-03 (Phase 1, liability test):** At the real 47-model occupancy,
  item-level **binary** outcomes cannot resolve the era variance component —
  the GLMM drives era to the boundary in 20–60% of reps and both LPM-REML and
  GLMM under-estimate era when it should dominate (era-share bias to −13/−16 pp).
  The same data at the well-powered D1 occupancy recovers (bias ≤ 5 pp, era
  boundary 0%), and the D2 **continuous** design recovers era with 98–100%
  coverage. Conclusion: the D2-era-binary collapse is a power limit, not an
  estimator defect. Consequence for Phase 2: era claims require per-model
  **continuous** traits (LPM-REML path); item-level binary era claims at 47
  models are underpowered.
- **2026-08-03 (Phase 1, estimator stack):** statsmodels `MixedLM` with a
  single group + `vc_formula` does not maximize its own REML objective for
  crossed variance components (suboptimal family/era split; e.g. 0.609/0.476
  vs the REML/ANOVA 0.399/0.313 on an F=E=12 balanced dataset). Replaced with a
  direct REML maximizer (verified against ANOVA MoM). Logged here so the
  MixedLM numbers are never quoted as estimator output.
- **2026-08-03 (Phase 1, D3):** As pre-registered, the nested design **was**
  detected — 100% of reps flagged by all three detectors (collinearity, SE
  inflation, profile flatness), 0% silent coverage. This is the expected
  aliasing failure, resolved in the estimator's favor (it fails detectably).

## Failed ideas log (append as they occur)

- **2026-08-03:** Share CI via t-inflated covariance and via chi-square/copula
  on the log-variances both under-covered at F=6 (family share ~85–92%).
  Reverted to normal MC delta on log-variances with log-draw clipping ±30 —
  coverage 95–96% at F=30. The F=6 limit is a design-power floor, not a CI fix.
