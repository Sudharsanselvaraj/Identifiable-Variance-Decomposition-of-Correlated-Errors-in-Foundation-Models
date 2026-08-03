# Population Assumptions

The assumptions this population rests on. **Full detail lives in the Assumption
Register** (`docs/00_Project/ASSUMPTION_REGISTER.md`) — the single source of
truth. This page is the population-specific pointer.

## Assumptions that define the population

| ID | Assumption | Status |
|---|---|---|
| A1 | Family × quarter design is crossed (precondition for the partition) | Verified |
| A2 | Era = public release date, not HF `createdAt` | Verified (4 divergences); Open (other models) |
| A3 | Family = design grouping; lineage edges = documented parent–offspring relations | Verified (grouping); Partial (edges) |
| A4 | Connected subset is the population; claims scoped to it | Verified |
| A5 | Open-weight only | Verified |
| A6 | Llama lineage terminates at Llama 4 | Verified |
| A7 | DeepSeek-V4 is a new independent lineage | Verified |
| A8 | Teacher leakage assigned to the era channel (inflates σ²_E) | Assumed (direction disclosed) |
| A9 | Coverage sufficient: ≥24/47 models AND all 6 families | Verified (gate); Kim overlap Open |

## Assumptions that govern measurement on the population

| ID | Assumption | Status |
|---|---|---|
| A10 | Linearity/additivity on the liability scale | Tested (Phase 1) |
| A11 | Continuous per-model trait, not raw binary items | Decided |
| A15 | Common/comparable item set across models | Assumed (fresh pass) |
| A22 | Kim cross-check is sanity only, never validation | Decided |

## Two-estimand rule

The population supports two estimands that are never merged (register A23):
θ_P (lineage conditional on era) and θ_M (lineage with era held fixed, on
co-released cohorts and verified fine-tune chains). Release year is both a
confounder and a mediator on the lineage→error path; a single estimand would
conflate the two roles.

## Non-assumptions (deliberately out of scope)

- **No lineage × era interaction** is estimated (not identified from sparse
  cells; register A13).
- **No "true causal share"** — the pair (θ_P, θ_M) brackets the truth.
- **No phylogeny reconstruction** (PhyloLM), pipeline-measurement-error
  decomposition (TEE), dataset-lineage reconstruction, or monoculture welfare
  evaluation — see `docs/01_Literature/Related_Work_Gaps.md`.

## Sources

- Register: `docs/00_Project/ASSUMPTION_REGISTER.md`
- Design: `docs/10_Population/Population_Definition.md` and siblings
- Theory: `docs/02_Theory/Mathematical_Formulation.md`,
  `docs/02_Theory/Structural_Causal_Model.md`
