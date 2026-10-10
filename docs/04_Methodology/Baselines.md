> **Superseded: earlier study (notice added 2026-10-10).** This document belongs to the earlier per-model variance-decomposition study. That study's item-level predictions were invalid (the extraction code read only option A's log-likelihood) and its findings are withdrawn or corrected (Supplementary Section S2 of the current manuscript). It is kept as research history and is not evidence for the current pair-level study: see [RESEARCH_STATUS.md](../../RESEARCH_STATUS.md).

# Baselines

Every comparison we must beat or position against. All verified in `docs/01_Literature/Literature_Map.md`.

## Comparison baselines

| Baseline | What it is | What we compare | Expected relationship |
|---|---|---|---|
| **Kim et al. (ICML 2025)** | Cross-sectional agreement rate across 350+ models; shared architecture/provider factors | Our variance partition (lineage/era/model-unique) | Different object; our partition is the temporally-aware version of their correlation structure |
| **PhyloLM (ICLR 2025)** | Output-similarity trees; benchmark-score prediction | Our design-matrix approach taking release record as given | Complementary; their trees can be a robustness input, not a rival estimate |
| **TEE (2026)** | G-theory decomposition of pipeline facets | Our model-trait decomposition | Same estimator class, different grouping factors; composable, not competing |
| **Null model** | No lineage or era structure (models independent given item difficulty) | Evidence of nonzero σ²_L and/or σ²_E | The Subjectivity-of-Monoculture warning: avoid baseline-dependence by modeling shared random effects directly |

## Simulation baselines (Phase 1)

| Baseline | Role |
|---|---|
| D1 balanced-crossed (known truth) | Reference recovery |
| D2 realistic occupancy (Phase 0 table) | Realistic recovery + precision loss |
| D3 nested (known aliased) | Must-fail control |

## Decision baselines

| Baseline | Role |
|---|---|
| Diversification-across-families intuition | The intervention claim RQ6 tests |
| Monoculture-critics position ("not a problem") | Evaluated with the actual partition |
