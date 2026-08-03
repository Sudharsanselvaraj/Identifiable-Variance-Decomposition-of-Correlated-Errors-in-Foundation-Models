# Exp02 — Phase 2 Real-Data Decomposition

**Status:** INSTRUMENT BUILT — G1 PASSED (GO WITH CHANGES); path decided
(fresh MMLU eval, LPM-REML on continuous per-model traits). Awaiting the
GPU-host eval run; execution runbook in
[`RESEARCH_PROTOCOL.md`](../00_Project/RESEARCH_PROTOCOL.md) (Stage 2),
replacing the earlier external-data procurement plan (fresh-eval decision,
[`Research_Decision_Log.md`](../00_Project/Research_Decision_Log.md) 2026-08-03).

## Purpose

Estimate θ_P (primary, observational) and θ_M (mechanistic, separate) on the connected
subset; produce the partition table; report the era-convergence trend as a table entry
(RQ3, RQ4, RQ5).

## Design

1. Assemble item-level response logs for the connected subset models
   (`docs/03_Data/Dataset_Inventory.md`) and **aggregate to a continuous
   per-model trait** (mean accuracy or IRT person ability over the common item
   set). Raw per-item Bernoulli responses are NOT the fitted outcome (Phase 1
   F4: era underpowered on binary at 47 models).
2. Build family × quarter design matrix from Phase 0 table + parent–offspring edges from
   technical reports/papers (`base_model` too sparse — 5 verified edges).
3. Fit the validated Phase 1 estimator: **LPM-REML (CrossedREML) on the
   continuous per-model trait**. Binomial GLMM only as a robustness check, with
   the F4 era-power caveat.
4. Report partition σ²_L / σ²_E / σ²_U with CIs as a table — not a headline.
5. Report θ_M separately on co-released cohorts and staggered fine-tune chains; never
   merge into θ_P (two-estimand rule).

## Data

Connected subset models, public item-level benchmark responses (primary
candidate: Kim et al. 2506.07962 public data, aggregated per model). Coverage,
contamination, and aggregation caveats in `Dataset_Inventory.md`.

## Metrics

Variance shares with CIs; per-item-set precision; era-convergence slope (table entry).

## Results

_(To be filled after run: `PHASE2_REPORT.md`.)_

## Interpretation / Failure

Interpreted against the Disconfirmability Register. Flat era-convergence = refuted
convergence; V_lineage|era ≈ 0 = lineage refuted; θ_M ≈ 0 = mechanistic lineage refuted;
θ_M nonzero with θ_P ≈ 0 = primary confounded by era.
