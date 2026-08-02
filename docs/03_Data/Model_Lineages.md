# Model Lineages

Source: Phase 0 log (verbatim in `proposal.md` §14). This is the verified record of what
we know about ancestry in the open-model population — and its limits.

## Verified contingency table (public release quarter, open-weight general models)

| Family | 2023Q1 | Q2 | Q3 | Q4 | 2024Q1 | Q2 | Q3 | Q4 | 2025Q1 | Q2 | Q3 | Q4 | 2026Q1 | Q2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Llama | L1 | | L2 | | | L3 | 3.1, 3.2 | 3.3 | | L4 | | | | (term.) |
| Qwen | | | 7B | | 1.5 | 2 | 2.5 | | | 3 | | | 3.5 | 3.6 |
| DeepSeek | | | | | | | | V3 | R1 | | V3.1 | V3.2 | | V4 |
| Mistral | | | 7B | Mixtral | | 8x22B | L2, Small | | S3, S3.1 | M3, S3.2 | | L3, Min3, Dev2 | S4 | M3.5 |
| Phi | | 1 | 1.5 | 2 | | 3 | 3.5 | 4 | | 4-r | | | 4-r-v | |
| Gemma | | | | | 1 | 2 | | | 3 | 3n | | | | 4, 4-12B |

`(term.)` = Llama open-weights lineage terminates at Llama 4 (Apr 2025); no public
Llama 4.5 / Llama 5 repo visible. Proprietary/hosted-only (Qwen3.7/3.8-Max, Muse Spark,
Magistral Medium, Codestral) excluded. Abbreviations: 4-r = Phi-4-reasoning-plus,
4-r-v = Phi-4-reasoning-vision-15B, Min3 = Ministral 3, Dev2 = Devstral-2.

## Verified cross-generation / merge edges (from `base_model` field)

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
  Small 3 → 3.1 → 3.2 → 4; Devstral-2 on Small-3.1-Base. Large/Medium/Ministral are
  sibling branches, not a chain.
- **Llama** — terminates at Llama 4 (Apr 2025); post-2025 era variation carried by the
  other five families.
- **DeepSeek V4** — ground-up redesign (dropped MLA); NOT a V3 descendant. Treated as a
  new independent lineage or dropped. Within-lab generation ≠ within-lineage.

## Teacher leakage (cross-family environmental sharing → era channel)

- Phi-4 trained on GPT-4o-generated data.
- Gemma 2 9B distilled from 27B.
- Gemma 4 "built from Gemini 3".

## Open items (do not drop)

1. `base_model` field is sparse: only 5 verified cross-generation edges above. Parent–
   offspring edges for the primary design must come from technical reports/papers.
2. meta-llama org is auth-gated; existence of Llama 4.5/5 inferred from author listing
   (no model newer than Llama 4), not exhaustively confirmed.
3. Era = public release date, not HF `createdAt` (4 documented divergences — see
   `docs/03_Data/Metadata.md`).
