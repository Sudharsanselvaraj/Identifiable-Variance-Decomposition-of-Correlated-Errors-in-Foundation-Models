# Statistical Model

The estimator class and the decision path. Source: `proposal.md` §7.1.

## Estimator

`statsmodels.MixedLM` — linear mixed model fit by **REML** (restricted maximum
likelihood), crossed random effects (family, era). This is the same estimator class as
TEE's G-theory decompositions (Messing, 2026), applied to a different object (model
traits, not pipeline facets).

## Model forms

| Form | Description | When used |
|---|---|---|
| **LPM-REML** | Linear probability model on binary error responses; REML on the crossed random effects | Candidate path; accepted only if the Phase 1 liability test shows acceptable bias |
| **GLMM** | Generalized linear mixed model (logit link) on the liability/threshold model | Alternative path; chosen if LPM-REML bias under the liability test is unacceptable |

## The Phase 1 liability decision (decides the Phase 2 path)

1. Generate continuous liability `y*` with known σ²_L/σ²_E/σ²_U.
2. Threshold to binary `y = 1{y* > 0}`.
3. Fit LPM-REML and GLMM.
4. Measure bias in the variance components under both.
5. Choose the path with acceptable bias; if both fail detectably, the instrument is unfit
   (RQ2 gate).

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
  finding). LPM-REML = direct REML maximizer in `src/lineage_era/estimator.py`
  (Woodbury-accelerated, verified against ANOVA MoM). Binomial GLMM
  (`BinomBayesMixedGLM`) remains the item-level reference.
- Deliverables: `phase1_simulation.py`, `PHASE1_REPORT.md` (bias tables, verdicts).
