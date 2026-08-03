# Selection Definition

How models are selected into the analysis sample, and what that selection does
and does not support. Selection is a **first-class population object**: the
connected-subset rule determines identifiability before any analysis
(`docs/02_Theory/Identifiability.md`).

## The selection rule (analysis sample = connected subset)

A model is in the analysis sample iff it belongs to the connected subset: its
family spans multiple eras AND multiple families occupy its era. This is
computed from the Phase 0 occupancy table, not assumed (register A4). Where the
design is nested, the partition is undefined **by construction** — a property of
the design, not a data gap.

## Measured coverage (Phase 0 → Phase 2)

| Gate | Rule | Status |
|---|---|---|
| Connected subset | Models on which lineage and era are separable | 47 models, CROSSED verified |
| Coverage bar (fresh eval) | ≥24/47 models AND all 6 families | TARGET 47/47 (fresh pass) |
| Kim leaderboard overlap | Leaderboard MMLU coverage of the connected subset | 18/47 (38.3%) — FAILS gate |
| 2025Q1+ coverage | Models released after the leaderboard freeze | 29 missing (incl. all modern DeepSeek) |

The coverage gate is hard-coded in `analysis/population.py`
(`COVERAGE_BAR_MODELS = 24`, `COVERAGE_BAR_FAMILIES = 6`; register A9). Because
leaderboard data freezes ~2024/Mar 2025, the trait must come from a **fresh**
eval pass of all 47 models, not from the leaderboard.

## Selection into θ_M (mechanistic estimand)

θ_M is restricted to co-released cohorts (2024Q2, 2024Q3, 2025Q2) and staggered
repeated fine-tunes along the 5 verified `base_model` edges. This is a small,
deliberately-scoped selection — θ_M is a structural claim on those subsets, never
a population claim.

## Selection bias posture

- Claims are scoped to the connected subset; no inference to non-open-weight or
  nested subpopulations.
- Missing `base_model` documentation selects *which* lineage edges are verified
  (5), constraining θ_M and Phase 3 analogies, not θ_P
  (`docs/02_Theory/Identifiability.md` open item).
- Benchmarks: fresh MMLU item set is fixed across models, so the trait is
  comparable by construction (register A15).

## Sources

- Connected-subset definition + RQ scoping: `docs/00_Project/Research_Questions.md`
- Coverage gate: `analysis/population.py`
- Availability finding: `docs/03_Data/Dataset_Inventory.md`
