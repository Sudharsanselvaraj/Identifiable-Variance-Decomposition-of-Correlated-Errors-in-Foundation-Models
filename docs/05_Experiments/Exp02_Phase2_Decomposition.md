# Exp02 — Phase 2 Real-Data Decomposition

**Status:** DESIGNED — blocked on Phase 1 PASS + item-level benchmark procurement.

## Purpose

Estimate θ_P (primary, observational) and θ_M (mechanistic, separate) on the connected
subset; produce the partition table; report the era-convergence trend as a table entry
(RQ3, RQ4, RQ5).

## Design

1. Assemble item-level error responses for the connected subset models
   (`docs/03_Data/Dataset_Inventory.md`).
2. Build family × quarter design matrix from Phase 0 table + parent–offspring edges from
   technical reports/papers (`base_model` too sparse — 5 verified edges).
3. Fit the mixed model validated in Phase 1 (LPM-REML or GLMM per Phase 1 decision).
4. Report partition σ²_L / σ²_E / σ²_U with CIs as a table — not a headline.
5. Report θ_M separately on co-released cohorts and staggered fine-tune chains; never
   merge into θ_P (two-estimand rule).

## Data

Connected subset models, public item-level benchmark responses. Coverage and
contamination caveats in `Dataset_Inventory.md`.

## Metrics

Variance shares with CIs; per-item-set precision; era-convergence slope (table entry).

## Results

_(To be filled after run: `PHASE2_REPORT.md`.)_

## Interpretation / Failure

Interpreted against the Disconfirmability Register. Flat era-convergence = refuted
convergence; V_lineage|era ≈ 0 = lineage refuted; θ_M ≈ 0 = mechanistic lineage refuted;
θ_M nonzero with θ_P ≈ 0 = primary confounded by era.
