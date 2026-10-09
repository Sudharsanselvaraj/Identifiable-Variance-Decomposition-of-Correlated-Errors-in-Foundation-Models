# Exp04 — Lineage vs era on the Open LLM Leaderboard population (Option B)

Status: **plan, pre-data.** Written 2026-10-09 before any per-question outcome
was read. Supersedes the 16-model empirical arm (see
`docs/08_Reviews/Revision_2026-10_Precision_Gate.md` for why that arm cannot
answer the question at any affordable N).

## Question

Across public open-weight models, how much of the **pairwise agreement in
errors** is explained by shared lineage (position in the `base_model`
ancestry tree) versus temporal proximity (release era), and is that split
estimable to a pre-specified precision on the available population?

## Why this design, given the precision result

The precision gate showed that a per-model trait decomposed into family and
quarter random effects needs ~60 family levels and ≥14 era levels to pin
either share within ±10pp. Two changes remove that ceiling:

1. **Many lineage levels.** The leaderboard has thousands of fine-tunes with a
   declared `base_model`, i.e. real ancestry trees, not 5–6 hand-labelled
   families.
2. **Pair-level outcome with continuous time.** The outcome is error agreement
   for each model pair, modelled with crossed (multi-membership) random effects
   for the two models plus pair covariates: lineage relation (same root, tree
   distance, parent–child) and |Δ upload date| in months. Time enters as a
   continuous distance, so precision no longer depends on how many quarters
   exist. This is also the quantity the paper's introduction is about.

## Data sources (verified reachable 2026-10-09)

| source | content | access | notes |
|---|---|---|---|
| `datasets/kim/hugging_face.csv` (in repo) | OLLB v2 contents snapshot: 4,576 rows / 4,497 models; `base_model`, `upload_date`, `type`, `is_merged`, params | local | metadata only; frozen at 2025-03-13 |
| `open-llm-leaderboard/<model>-details` (≈4,500 repos) | v2 per-question MMLU-Pro (12,032 items, 10 options) | HF, `gated=auto` | raw JSONL is ~327 MB/model; the auto-converted parquet (`refs/convert/parquet`) allows reading only `doc_id`, `acc`, per-choice scores |
| `open-llm-leaderboard-old/details_<model>` | v1 per-question MMLU 5-shot (57 subjects, 4 options) | HF, not gated | parquet; per-choice log-likelihoods + `gold` + item hash; replication on an earlier era and a different benchmark |

## Population construction (outcome-independent)

Built only from metadata; score columns (`mmlu_pro`, `average_score`, …) are
never read by the builder.

1. One row per model name (drop duplicate precision variants).
2. Exclude: flagged, `base_model == "Removed"`, merges (`is_merged` **or**
   `type == basemergesandmoerges` — 1,112 merge-type rows are not flagged
   `is_merged`; multi-parent lineage is a sensitivity analysis, not primary).
3. Resolve ancestry to a root by walking `base_model`; 2,073 parents are not
   on the leaderboard and must be resolved through the Hub model API
   (`cardData.base_model`), cached to `datasets/ollb/lineage_cache.json`.
4. Lineage variables per pair: same root; tree distance; parent–child; same
   root organisation.
5. Era: upload date (month). Root release date kept separately: for a
   fine-tune, pretraining era is a property of its root and therefore nested in
   lineage — only the post-training era is separable. This is stated as a
   scope limit, not hidden.
6. Freeze the roster (`datasets/ollb/roster.csv`) and run the precision gate on
   the frozen design **before** downloading any outcomes.

Initial metadata profile (no outcomes read): 3,229 eligible non-merge models;
upload quarters concentrated in 2024Q2–2025Q1 (465 / 663 / 1,116 / 1,472).
Lineage roots are under-resolved until step 3 runs.

## Outcomes and models

- Per model: correctness vector and chosen option per item (argmax of the
  per-choice scores, cross-checked against the stored `acc`, same guard as the
  fixed `phase2_eval._choice_logprobs`).
- Per pair: P(same wrong answer | both wrong) (Kim et al.'s measure) and the
  phi coefficient of error indicators.
- Primary model: pair outcome ~ lineage relation + f(|Δt|) + size/accuracy
  controls + (1 | model_i) + (1 | model_j) (multi-membership); variance and
  effect-size partition reported with precision-gate bounds.
- Secondary: per-model accuracy decomposition (the original estimand) on the
  large population, for comparison with the 16-model result.
- Replication: the same pipeline on v1 MMLU.

## Data volume (estimates, to confirm with a 1-model test)

- v2 projected columns: expected ~1–3 MB per model → roughly 5–13 GB transfer
  for all ~4,500; stored compactly as an int8 model × item matrix
  (~4,500 × 12,032 ≈ 55 MB).
- Hub metadata calls: ~2,000–4,000 `model_info` requests for lineage.

## Permissions needed before execution

1. Hub metadata calls using the stored HF login (read-only).
2. The v2 details repos are `gated=auto`: access must be requested/accepted by
   the account holder on Hugging Face.
3. A one-model test read (≈ 1–3 MB) to confirm schema and size, then the bulk
   download.

## Out of scope / threats

- Causal lineage effects (observational).
- Leaderboard population is dominated by community fine-tunes of a few large
  bases; results describe that population, not frontier releases.
- Contamination and self-selection into the leaderboard: disclosed.
- Overlap with Kim et al. (same v2 source): our contribution is the lineage
  tree + continuous-time separation + pre-specified precision gate; their
  pairwise regression used provider/architecture indicators only.
