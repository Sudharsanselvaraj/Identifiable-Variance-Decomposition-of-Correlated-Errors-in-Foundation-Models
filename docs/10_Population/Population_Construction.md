# Population Construction

How the 47-model connected subset was assembled. The construction is codified in
`src/lineage_era/occupancy.py` (offline, no network calls) and is the single
source of truth for the design used by Phase 1 (D2) and Phase 2.

## Method (Phase 0)

1. **Frame:** enumerate public, open-weight, general-purpose models released
   2023Q1–2026Q2 with a canonical HF checkpoint.
2. **Verify per model via the HF API** (`/api/models/{id}`): `createdAt`,
   `cardData.base_model`, license.
3. **Assign era = public release date**, not HF `createdAt` (4 documented
   divergences — see `docs/03_Data/Metadata.md`).
4. **Classify family** from the verified contingency table (Phase 0 log,
   `proposal.md` §14).
5. **Record the contingency table** as `MODELS` in `occupancy.py`; the offline
   consistency check (`occupancy.check_consistency`) reproduces the Phase 0
   verdict (47 models, 6×14, crossed).

## Resulting design (verified numbers)

| Stat | Value |
|---|---|
| Models | 47 |
| Families | 6 (Llama, Qwen, DeepSeek, Mistral, Phi, Gemma) |
| Quarters | 14 (2023Q1–2026Q2) |
| Row spans | Llama 6, Qwen 7, DeepSeek 5, Mistral 9, Phi 8, Gemma 5 |
| Quarters with ≥2 families | 11 |
| Dense cells (≥3 families) | 2024Q2, 2024Q3, 2025Q2 |
| Verified `base_model` edges | 5 |

## Construction artifacts

- `occupancy.py` — the authoritative `MODELS` table, `VERIFIED_EDGES`,
  `ERA_DIVERGENCES`, `CAVEATS`, `DOCUMENTED_STATS`.
- `docs/03_Data/Metadata.md` — field definitions and release-date rule.
- `docs/03_Data/Model_Lineages.md` — the human-readable contingency table.
- `analysis/metadata.py` — merges occupancy with the live eval manifest into the
  per-model design frame (`analysis_design.csv`).

## Data-quality caveats carried into the analysis (do not drop)

Verbatim in `occupancy.CAVEATS` and surfaced in every
`PHASE2_REPORT.md`: Llama lineage termination; sparse `base_model`; DeepSeek-V4
ground-up redesign; cross-family teacher leakage; Mistral Small chain structure.
