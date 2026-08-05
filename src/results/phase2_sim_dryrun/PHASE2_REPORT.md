# Phase 2 Report: Lineage vs Era Variance Decomposition

Generated: 2026-08-05  |  Design: 47 models, 6 families, 14 quarters

**Identifiability audit:** Verdict: **PASS**

## θ_P — primary variance partition (fresh MMLU 5-shot trait)

### θ_P variance partition (variance_partition.csv)

| component   |   variance |        se |   share |   share_lo |   share_hi |
|:------------|-----------:|----------:|--------:|-----------:|-----------:|
| family      |     0.5893 | 0.399622  |   0.557 |  0.214782  |   0.825509 |
| era         |     0.137  | 0.10209   |   0.129 |  0.0243001 |   0.454848 |
| unique      |     0.3321 | 0.0858098 |   0.314 |  0.110114  |   0.586038 |

### Bootstrap CIs (bootstrap_ci.csv)

| component   |   share |        se |   share_lo |   share_hi |    mc_lo |    mc_hi |      mc_sd |
|:------------|--------:|----------:|-----------:|-----------:|---------:|---------:|-----------:|
| family      |   0.557 | 0.399622  |  0.214782  |   0.825509 | 0.548965 | 0.562487 | 0.00359826 |
| era         |   0.129 | 0.10209   |  0.0243001 |   0.454848 | 0.12306  | 0.135094 | 0.00327399 |
| unique      |   0.314 | 0.0858098 |  0.110114  |   0.586038 | 0.306208 | 0.320075 | 0.00334986 |

### Family effects (family_effects.csv)

| family   |   family_blup |   mean_trait |   n_models |
|:---------|--------------:|-------------:|-----------:|
| DeepSeek |     -0.664239 |   -0.666486  |          5 |
| Gemma    |     -0.175082 |   -0.401491  |          6 |
| Llama    |     -0.833049 |   -1.03337   |          7 |
| Mistral  |      1.17164  |    1.23432   |         14 |
| Phi      |      0.389315 |    0.34553   |          8 |
| Qwen     |      0.111413 |   -0.0637433 |          7 |

### Era effects (era_effects.csv)

| era    |     era_blup |   mean_trait |   n_models |
|:-------|-------------:|-------------:|-----------:|
| 2023Q1 | -0.192668    |  -1.54686    |          1 |
| 2023Q2 |  0.229531    |   1.12109    |          1 |
| 2023Q3 |  0.0148788   |   0.179601   |          4 |
| 2023Q4 | -0.0988267   |   0.507752   |          2 |
| 2024Q1 | -0.0751348   |  -0.252155   |          2 |
| 2024Q2 |  0.000104549 |   0.0788789  |          5 |
| 2024Q3 | -0.156538    |  -0.077583   |          6 |
| 2024Q4 |  0.22924     |  -0.00898756 |          3 |
| 2025Q1 |  0.10884     |   0.496662   |          4 |
| 2025Q2 | -0.292356    |  -0.158609   |          6 |
| 2025Q3 | -0.0793885   |  -0.990185   |          1 |
| 2025Q4 |  0.713286    |   1.80407    |          4 |
| 2026Q1 | -0.0627218   |   0.389933   |          3 |
| 2026Q2 | -0.338246    |  -0.502618   |          5 |

- Family share: 0.557 (delta CI 0.215–0.826; trait-error MC 0.549–0.562)
- Era share: 0.129 (delta CI 0.024–0.455; trait-error MC 0.123–0.135)
- Unique/residual share: 0.314

## θ_M — mechanistic tables (reported separately, not part of θ_P)

- `era_trend.csv`: mean trait and era BLUP per quarter.
- `dense_cell_contrasts.csv`: family contrasts within the co-released quarters (2024Q2/Q3, 2025Q2).
- `chain_slopes.csv`: per-quarter slope along the verified fine-tune edges (occupancy.VERIFIED_EDGES).

## Sensitivity (results/phase2/sensitivity/)

- `leave_one_family.csv`: share change when each family is dropped.
- `leaked_drop.csv`: full design vs dropping cross-lab teacher-leak models (Phi-4 reasoners, Gemma-2-9B, Gemma-4).
- `lxe.csv`: family x era cell variance component added.
- `subject_drop.csv`: partition after dropping each MMLU subject group.
- `trait_definition.csv`: acc vs acc_norm trait variants.
- `kim_crosscheck.csv`: fresh acc vs Kim et al. leaderboard acc for the reconciled overlap (documented SANITY CHECK only — benchmark version, prompting, and few-shot protocols differ; deltas are expected and are not treated as validation).

## Figures (results/phase2/figures/)

- `blup_plot.pdf`
- `design_heatmap.pdf`
- `era_trend.pdf`
- `family_vs_era.pdf`
- `variance_shares.pdf`

## Error similarity (secondary panel)

Supporting observational layer for the decomposition; never part of the θ_P gate. Pairwise item-level error overlap on the common MMLU item set, situated against the null ladder (observed -> matched-accuracy shuffle -> item-difficulty shuffle -> analytic independence). Primary measure: **phi** (locked by the pre-registered selection rule, Research_Decision_Log 2026-08-03; all six measures are in `error_similarity.csv`).

- Within-family overlap: **0.056** vs matched-accuracy null 0.000 (z = 2.517); within-family exceeds between-family (0.057).
- Within-era overlap: 0.057 (null 0.000).
- Louvain communities: 6 on the top-k network (97 edges); adjusted Rand index vs family 0.029 vs era -0.009 — family-aligned (descriptive only).
- Full outputs: `error_similarity.csv`, `similarity_matrix.csv`, `null_ladder.csv`, `family_era_overlap.csv`, `edge_stability.csv`, `community_comparison.csv`; figures `error_heatmap`, `error_dendrogram`, `error_network`, `error_embedding_pca`, `error_embedding_tsne`.

## Caveats carried from Phase 0 (occupancy.CAVEATS)

- Llama open-weights lineage terminates at Llama 4 (Apr 2025). Post-2025 era variation is carried by Qwen/Mistral/DeepSeek/Gemma/Phi only — this is a real-world lineage-attrition fact, not an identification failure.
- `base_model` field is sparse: true cross-generation lineage is largely UNDOCUMENTED in HF cards (only 5 verified edges). Parent–offspring edges for the primary design must be drawn from technical reports/papers, not HF metadata. Affects Phase 3 analogies and the mechanistic estimand.
- DeepSeek V4 is a ground-up redesign (dropped MLA) — NOT a V3 descendant. Within-lab generation != within-lineage; V4 must be treated as a new independent lineage or dropped.
- Cross-family teacher leakage: Phi-4 trained on GPT-4o-generated data; Gemma 2 9B distilled from 27B; Gemma 4 built from Gemini 3. Independence assumption violated to unknown degree — these belong in V_era (shared environment); flag for the primary estimand.
- Mistral's Small (24B) chain (Small 3->3.1->3.2->4; Devstral-2 on Small-3.1-Base) is the only verified within-family chain; Large/Medium/Ministral are sibling branches, not a chain.

Small-sample limit: 6 family levels (df = 5) cap the family-share coverage below nominal; the SE-inflation detector is reported as a warning for this reason (see identifiability_report.md).
