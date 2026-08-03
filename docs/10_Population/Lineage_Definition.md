# Lineage Definition

**Lineage** is the ancestry relation between models: a model replicates the
blind spots of the model, outputs, and data it descends from (verified
parent–offspring edges, fine-tune chains, teacher–student distillation). It is
the V_lineage (σ²_L) channel of the partition.

## Two levels of lineage

| Level | Definition | Used by |
|---|---|---|
| **Family** | The verified design grouping (Llama, Qwen, DeepSeek, Mistral, Phi, Gemma) | Primary estimand θ_P (the design factor) |
| **Lineage edge** | A documented parent–offspring `base_model` relation | Mechanistic estimand θ_M + Phase 3 analogies |

The two must never be conflated (register A3): a family is a grouping; an edge is
a claim about direct ancestry (`docs/04_Methodology/Threats_to_Validity.md`).

## Verified edges (from `base_model` field)

| Child | Parent(s) | Quarter |
|---|---|---|
| Llama-3.3-70B-Instruct | Llama-3.1-70B | 2024Q4 |
| Phi-4-reasoning-plus | phi-4 | 2025Q2 |
| Phi-4-reasoning-vision-15B | Phi-4-reasoning | 2026Q1 |
| Devstral-Small-2 | Mistral-Small-3.1-Base | 2025Q4 |
| DeepSeek-V3.2 | V3.2-Exp-Base | 2025Q4 |

All other `base_model` entries are within-generation base↔instruct links (e.g.,
Qwen3-8B↔Qwen3-8B-Base), not lineage.

## Known chain structure

- **Mistral Small (24B) chain** — the only verified within-family chain:
  Small 3 → 3.1 → 3.2 → 4; Devstral-2 on Small-3.1-Base.
- **Llama** — terminates at Llama 4 (Apr 2025); post-2025 era variation carried
  by the other five families.
- **DeepSeek-V4** — ground-up redesign (dropped MLA); **not** a V3 descendant.
  Treated as a new independent lineage (register A7).

## Sparse-edges limitation

`base_model` is largely undocumented in HF cards: only **5 verified
cross-generation edges**. Parent–offspring edges for the primary design must come
from technical reports/papers. This constrains θ_M and the Phase 3 analogies,
**not** the identifiability of the primary design, which rests on family ×
quarter (see `docs/02_Theory/Identifiability.md`).

## Sources

- Verified contingency table + edges: `docs/03_Data/Model_Lineages.md`
- Codified: `src/lineage_era/occupancy.py` (`VERIFIED_EDGES`)
- Design metadata: `docs/03_Data/Metadata.md`
