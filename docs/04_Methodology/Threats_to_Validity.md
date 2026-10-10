> **Superseded: earlier study (notice added 2026-10-10).** This document belongs to the earlier per-model variance-decomposition study. That study's item-level predictions were invalid (the extraction code read only option A's log-likelihood) and its findings are withdrawn or corrected (Supplementary Section S2 of the current manuscript). It is kept as research history and is not evidence for the current pair-level study: see [RESEARCH_STATUS.md](../../RESEARCH_STATUS.md).

# Threats to Validity

Expanded from the Risk Register (`proposal.md` §11). Organized by validity type.
Consolidated assumption ledger: `docs/00_Project/ASSUMPTION_REGISTER.md`;
silent-failure cases with detection: `docs/02_Theory/Failure_Cases.md`.

## Internal validity

| Threat | Direction | Mitigation |
|---|---|---|
| Release-year mediator/confounder conflation | θ_P vs. θ_M collapse | Two-estimand rule, non-negotiable; never merge |
| Binary-response mis-specification biases components | Wrong partition | Phase 1 liability test decides LPM-REML vs. GLMM before any real-data claim |
| REML convergence on sparse cells | Non-identifiable fits | D2 regime reproduces occupancy before real data; failure = gate failure |
| Teacher leakage violating family independence | Inflates σ²_E | Assigned to era channel explicitly; disclosed as inflation direction |
| Benchmark contamination | Inflates σ²_E | Item-set exclusion of known-contaminated items; disclosed |
| Nested subpopulations within the "crossed" population | Aliasing | D3 must-fail control; connected-subset audit |

## External validity

| Threat | Mitigation |
|---|---|
| Claims restricted to the connected subset only | Every RQ explicitly scoped; non-identifiability stated as design property, not data gap |
| Llama open-weights termination (Apr 2025) | Stated population fact; post-2025 era variation carried by 5 families |
| Open-weight ≠ hosted/closed models | Population scoped to open-weight; hosted-only excluded (Phase 0) |

## Construct validity

| Threat | Mitigation |
|---|---|
| Error trait defined by a specific item set | Common/comparable item set; item difficulty in the model; precision reported |
| "Lineage" vs. "family" conflation | Family = verified design grouping; lineage edges = documented parent–offspring relations (5 verified; rest from technical reports) |
| Era as release quarter vs. training window | Era = public release date (4 documented divergences checked); training-window proximity is a disclosed approximation |

## Statistical validity

| Threat | Mitigation |
|---|---|
| Small mechanistic subset (5 edges) | θ_M reported separately with explicit interval; no population claim |
| Multiple testing across RQs | Register pre-registers refutation conditions before Phase 2 results |
| Null-model dependence of monoculture measures | We model shared random effects directly (no independence null) — per Subjectivity-of-Monoculture warning |
| CI under-coverage (as TEE found for its pipelines) | Bootstrap/parametric intervals; coverage checked in Phase 1 D1/D2 |
