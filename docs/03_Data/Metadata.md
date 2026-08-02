# Metadata

Model-level metadata used to build the design. Source: Phase 0 verification method.

## Verification method (Phase 0)

- HF API `/api/models/{id}` for ~45 models: `createdAt`, `cardData.base_model`, license.
- **Era = public release date, not HF `createdAt`.**

## Documented release-date divergences (repo createdAt ≠ public release)

| Model | HF repo createdAt | Public release |
|---|---|---|
| Mistral Small 4 | 2026-01-23 | 2026-03-16 |
| Mistral Medium 3.5 | 2026-03-31 | 2026-04-29 |
| Gemma 4 | 2026-03-12 | 2026-04-02 |
| Phi-1 | 2023-09-10 | 2023-06-21 |

Rule for the design matrix: always use public release date for era. Phase 0 checked the
four known divergences; treat any other `createdAt`-based inference with the same
skepticism when extending the population.

## Access caveats

- meta-llama org is auth-gated; existence of Llama 4.5/5 inferred from the author listing,
  not exhaustively confirmed.
- `cardData.base_model` is sparse: only 5 verified cross-generation edges (see
  `docs/03_Data/Model_Lineages.md`).

## Fields to collect for Phase 2 assembly

Per model: id, family, release quarter (public), license, `base_model` (if present),
architecture class, parameter count, tokenizer (optional), RLHF/SFT lineage (from
technical reports), synthetic-data provenance (from technical reports). The last three
come from technical reports/papers, not HF metadata.
