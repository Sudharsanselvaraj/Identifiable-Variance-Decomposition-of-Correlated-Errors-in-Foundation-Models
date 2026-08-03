# Exp01 — Phase 1 Simulation Validation

**Status:** RUN (2026-08-03) — see `PHASE1_REPORT.md` (root). Verdict: **GO WITH CHANGES**.

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

See `PHASE1_REPORT.md` (root) for the full report. Summary (seed 1):

- **D1** (30×14×2, 300-rep calibration): share bias ≤ 2.5 pp, coverage 95–96%.
- **D2** (47-model occupancy): share bias ≤ 5.3 pp (family, scenario A), coverage 95–100%.
- **D3** (nested): detected in 100% of reps by all three detectors; silent coverage 0%.
- **Liability** (item-level probit, I=300): LPM and GLMM agree on family share;
  era variance underpowered at the 47-model occupancy on binary data (GLMM era
  boundary 20–60%), recoverable at D1 occupancy. Path decided: LPM-REML on
  per-model continuous traits for Phase 2.
- **L×E**: interaction non-identified at D2 (SE ratio ≈ 10⁴); documented.

Verdict: **GO WITH CHANGES** (changes = Phase 2 LPM-REML/continuous path;
item-level binary era claims at 47 models are underpowered; report F=6
family-share bias ≈ −5 pp).

## Interpretation / Failure

- GO: D1/D2 recover, D3 fails detectably.
- GO WITH CHANGES: acceptable bias under D2 with documented path choice.
- NO GO: silent mis-specification bias (RQ2) or D2 collapse (RQ1) — stop program.
