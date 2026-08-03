# Statistical Model

The estimator class and the decision path. Source: `proposal.md` §7.1.

## Estimator

`CrossedREML` (`src/lineage_era/analysis/reml.py`) — direct restricted-likelihood
(REML) maximizer over log-variances for crossed random effects (family, era),
Woodbury-accelerated, share CIs via Monte-Carlo delta on the log-variances.
This is the same estimator class as TEE's G-theory decompositions (Messing,
2026), applied to a different object (model traits, not pipeline facets).
Validated in Phase 1: matches ANOVA MoM on balanced data, bias ≤ 2.5 pp,
coverage 95–96% at F=30. (Plan's `statsmodels.MixedLM` crossed-vc form was
found NOT to maximize the REML objective — see decision log; not used.)

## Model forms

| Form | Description | When used |
|---|---|---|
| **LPM-REML** | Linear mixed model (REML) on a continuous per-model trait; crossed random effects (family, era) | **ACCEPTED path (Phase 1 PASS, GO WITH CHANGES).** Continuous per-model trait = aggregation of item-level responses (mean accuracy or IRT ability) — raw binary items are not modeled directly (Phase 1 F4 era-power limit) |
| **GLMM** | Generalized linear mixed model (logit link) on item-level binary responses | Robustness check only; era claims from binary items at the 47-model occupancy are underpowered (Phase 1 F4: GLMM era-boundary collapse 20–60%) |

## The Phase 1 liability decision (decides the Phase 2 path)

1. Generate continuous liability `y*` with known σ²_L/σ²_E/σ²_U.
2. Threshold to binary `y = 1{y* > 0}`.
3. Fit LPM-REML and GLMM.
4. Measure bias in the variance components under both.
5. Choose the path with acceptable bias; if both fail detectably, the instrument is unfit
   (RQ2 gate).

**Outcome (2026-08-03):** LPM-REML on continuous per-model traits chosen. At the
real 47-model occupancy the GLMM era component collapses to the boundary
(20–60% of reps, era-share bias to −13/−16 pp) while continuous-trait recovery
is 98–100% era coverage (D2 continuous). The LPM-REML path is the Phase 1
validated estimator (`CrossedREML`); GLMM is demoted to robustness check.

## Uncertainty

- Variance-component intervals via bootstrap or parametric CIs — **reported with every
  estimate** (identifiability condition 4). Precision is a first-class output, not a
  footnote.
- The partition is normalized to shares; intervals on shares, not just components.

## Failure modes the estimator must expose

| Mode | Expected behavior |
|---|---|
| D1 balanced-crossed | Recovers ground truth (reference) |
| D2 realistic occupancy (Phase 0 table) | Recovers ground truth with quantified precision loss; bias/collapse ⇒ gate fails |
| D3 nested | Must fail detectably (σ²_L/σ²_E aliased) |
| L×E interaction in DGP | Unidentifiable from sparse cells; documented, not estimated |

## Environment

- Python 3.11 (numpy 1.26.4, scipy 1.13.1, pandas 2.2.2); no R.
- `statsmodels` is installed but NOT used for the LPM path: its single-group +
  `vc_formula` form does not maximize the crossed REML objective (Phase 1
  finding). LPM-REML = direct REML maximizer in `src/lineage_era/analysis/reml.py`
  (Woodbury-accelerated, verified against ANOVA MoM). Binomial GLMM
  (`BinomBayesMixedGLM`) remains the item-level reference.
- Deliverables: `phase1_simulation.py`, `PHASE1_REPORT.md` (bias tables, verdicts).
