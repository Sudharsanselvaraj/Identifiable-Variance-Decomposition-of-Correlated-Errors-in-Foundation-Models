# Exp01 — Phase 1 Simulation Validation

**Status:** DESIGNED — not run. Requires Phase 1 plan approval + `statsmodels` install.

## Purpose

Show the crossed random-effects estimator recovers known ground truth before any real-data
claim (RQ1, RQ2). Establish the LPM-REML vs. GLMM path for Phase 2.

## Design

| Regime | DGP | Known truth | Expectation |
|---|---|---|---|
| D1 | Balanced crossed design | σ²_L, σ²_E, σ²_U chosen | Recovers ground truth (reference) |
| D2 | Occupancy copied from Phase 0 table (unbalanced, sparse cells) | Same | Recovers with quantified precision loss; bias/collapse ⇒ gate fails |
| D3 | Nested design (each family confined to one era) | σ²_L/σ²_E aliased | Must fail detectably |
| Liability | Continuous liability → binary threshold; fit LPM-REML vs. GLMM | Known components | Decides estimator path |
| L×E | Lineage × era interaction in DGP | Interaction non-identified | Documented, not estimated |

## Data

Synthetic only. Occupancy matrix sourced from `docs/03_Data/Model_Lineages.md`.

## Metrics

Bias and MSE of components and shares; CI coverage; D3 aliasing detection rate.

## Results

_(To be filled after run: `PHASE1_REPORT.md`.)_

## Interpretation / Failure

- GO: D1/D2 recover, D3 fails detectably.
- GO WITH CHANGES: acceptable bias under D2 with documented path choice.
- NO GO: silent mis-specification bias (RQ2) or D2 collapse (RQ1) — stop program.
