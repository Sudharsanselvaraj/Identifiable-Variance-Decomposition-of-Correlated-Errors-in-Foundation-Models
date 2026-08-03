# Environment Definition

The **environment** is everything shared by contemporaneous models other than
ancestry — the V_era (σ²_E) channel of the partition. It is measured by the
release quarter and qualified by documented cross-family sharing.

## Era as the environment proxy

- **Era = public release quarter** of the model.
- Rule: use public release date, **not** HF `createdAt` (4 documented
  divergences; `occupancy.ERA_DIVERGENCES`):
  Mistral-Small-4 (2026-03-16), Mistral-Medium-3.5 (2026-04-29), Gemma-4
  (2026-04-02), Phi-1 (2023-06-21). Applied for any model added to the
  population (register A2).
- The era channel captures shared web scrapes, benchmark-cleansed corpora, and
  the dominant techniques of a quarter.

## Teacher leakage → era channel (cross-family environmental sharing)

Cross-family teacher–student or synthetic-data leakage violates family
independence and is assigned to the era channel (inflates σ²_E), never silently
absorbed (register A8):

| Model | Leakage |
|---|---|
| Phi-4 | Trained on GPT-4o-generated data |
| Gemma 2 9B | Distilled from 27B |
| Gemma 4 | Built from Gemini 3 |

Leaked models are flagged in the design frame (`analysis/metadata.py`
`LEAKED_MODELS`) and the leaked-drop sensitivity is reported
(`analysis/sensitivity`).

## Benchmark contamination

Models trained on leaderboard items enter the era channel and inflate σ²_E;
disclosed as an inflation direction, mitigated by item-set choice where feasible
(`docs/04_Methodology/Threats_to_Validity.md`).

## Structural note

Release year is both a **confounder** (era imposes an error regime on every
contemporaneous model) and a **mediator** (lineage acts partly by moving release
forward) on the lineage→error path. This is why θ_P (era in the model) and θ_M
(era held fixed) are reported separately (`docs/02_Theory/Structural_Causal_Model.md`,
register A23).

## Sources

- Release-date rule + divergences: `docs/03_Data/Metadata.md`
- DAG + era channel: `docs/02_Theory/Structural_Causal_Model.md`
- Terminology: `docs/01_Literature/Terminology.md`
