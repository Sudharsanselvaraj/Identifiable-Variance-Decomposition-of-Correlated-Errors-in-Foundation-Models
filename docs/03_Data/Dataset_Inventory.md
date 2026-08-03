# Dataset Inventory

**STATUS: trait = fresh MMLU 5-shot eval on all 47 (decided 2026-08-03); run
venue open.** Phase 1 F4 settled the modeling target: a continuous per-model
trait aggregated from item-level responses — raw binary items are NOT modeled
directly. Kim et al. (arXiv:2506.07962, ICML 2025, **CC BY 4.0**) ships
per-model MMLU accuracy in-repo, but leaderboard data is frozen ~2024 and
covers only 18/47 connected-subset models (DeepSeek absent). The trait is
therefore produced by a fresh evaluation of ALL 47 connected-subset models on
MMLU 5-shot (strict common item set); Kim's values are kept only as a
validation cross-check. Infrastructure: `src/lineage_era/phase2_eval.py`
(47/47 manifest + lm-eval-harness runner). Run venue / HF token / budget open.

## Availability finding (2026-08-03)

- **Kim et al. repo** (`github.com/nikhgarg/llm_correlated_errors_public`,
  CC BY 4.0), files in `datasets/kim/`: `helm/model_accuracy.csv` (71 models,
  MMLU), `hugging_face/hf_model_accuracy.csv` (451 models, MMLU), plus
  `model_overview.csv` and `model_to_file.csv` metadata.
- **Coverage of the connected subset: 18/47 (38.3%)** — Llama 5, Qwen 3,
  DeepSeek 0, Mistral 5, Phi 3, Gemma 2. Gate (>=24/47 AND all 6 families)
  **FAILS**.
- **Cause:** leaderboard MMLU/MMLU-PRO data freezes around 2024 / Mar 2025
  (verified: Kim HF+HELM v1 files, Kim's OLLB v2 snapshot, and the live OLLB v2
  API all stop before the 2025Q1+ releases). All 29 missing models are
  2025Q1+ (incl. every modern DeepSeek) — only a fresh evaluation pass covers
  them.
- **Benchmark note:** Kim's data mixes two leaderboards' MMLU subsets, so it is
  not a strict common item set; the fresh pass uses one fixed item set instead.

## Fresh eval pass (decided; venue open)

- **Benchmark:** MMLU 5-shot (loglikelihood scoring; matches Kim et al. and the
  paper's framing). `cais/mmlu` dataset (all 57 subjects) downloaded.
- **Manifest:** all 47 connected-subset models have a canonical HF checkpoint
  (verified 2026-08-03). 23 token-free; 24 gated (meta-llama org, Qwen3+,
  DeepSeek-V4, Mistral org gated items, Gemma-1/2/3/3n/4) — gated models need
  `HF_TOKEN` with the license accepted. 2026 frontier cells (Qwen3.5/3.6,
  DeepSeek-V4, Mistral-Small-4, Mistral-Medium-3.5, Gemma-4) exist but are
  gated.
- **Runner:** `python3 -m lineage_era.phase2_eval --model <full_name>`
  (from `src/`); full per-model commands generated from the manifest.
- **Per-model caveats:** Phi-1/1.5/2 are 2048-token context — some MMLU 5-shot
  prompts exceed it and crash; needs `max_length` handling (their paper's MMLU
  values are also at 2048, so truncation is the faithful reading). Sliding-window
  models (Qwen, Mistral) should use `sdpa` on GPU, not `eager`.
- **Environment:** dev Mac cannot run evals at usable speed (M5 CPU, 17 GB,
  MPS allocator errors). Full run needs a GPU host; local runs are pilots only
  (pipeline validated through model load + task setup).

## Requirements for the Phase 2 item set

- Item-level response records (per-model, per-item correctness) for the connected subset
  models — i.e., a common or comparable item set over the 2023Q1–2026Q2 window.
- **Modeling target: the aggregated continuous per-model score** (mean accuracy
  over the common item set, or an IRT 2PL/3PL person ability). The per-item
  Bernoulli layer is a data source, not the fitted outcome.
- Sufficient item count for per-model trait precision (identifiability condition 4:
  "error traits measured precisely enough"; CIs reported with every estimate).
  With thin item counts, prefer IRT ability over raw proportion and report item
  counts alongside.

## Aggregation pipeline (contract for Phase 2)

```
item-level response logs  --(common item set, per-model)-->  per-model score
  y_{m,i} in {0,1}                                            t_m = mean_i y_{m,i}
                                                                (or IRT person ability, s.e. via item information)
per-model score  --(LPM-REML crossed fit)-->  theta_P: s2_L, s2_E, s2_U + share CIs
```

- σ²_U is measured-with-error inclusive: variance of the trait estimator lands
  in the unique component; reported with the partition.
- Kim et al. (2506.07962) already publishes item-level results for 350+ models;
  aggregation per model is less work than a per-item binary fit, and the design
  stays identical to the validated D2 continuous regime.

## Known risks to this data (all inflate σ²_E or blur lineage)

| Risk | Direction | Mitigation |
|---|---|---|
| Benchmark contamination (models trained on leaderboard items) | Inflates era share | Exclude known-contaminated items where feasible; disclose |
| Response logs unavailable for older models | Coverage loss | Fallback: run a fresh evaluation pass on the connected subset |
| Item sets differ across models | Non-comparable traits | Use the intersection/comparable set; report overlap |

## Inventory table (filled at eval run)

| Benchmark | Version | License | Questions | Split | Known contamination | Response logs available | Models covered |
|---|---|---|---|---|---|---|---|
| MMLU (fresh pass) | 5-shot, loglikelihood | `cais/mmlu` | 14,042 | dev 5-shot / test | possible (disclose) | per-model acc via lm-eval 0.4.12 | 47/47 (target) |

## Fallback plan

If the fresh eval pass is infeasible at budget, decompose on the 18/47
leaderboard-covered models and report the partition as covering 2023–2024 with
DeepSeek absent (last resort; Phase 1 shows family bias ~ -5pp at F=6 and era
underpower). Cost/budget decision recorded in the Research Decision Log.
