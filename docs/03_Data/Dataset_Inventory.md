# Dataset Inventory

**STATUS: trait = fresh MMLU 5-shot eval on the G3 minimum valid population,
22 of 47 (Path A LOCKED 2026-08-03; G3 gate PASS 2026-08-03); run venue open.**
Phase 1 F4 settled the modeling target: a continuous per-model trait aggregated
from item-level responses — raw binary items are NOT modeled directly. Kim et al.
(arXiv:2506.07962, ICML 2025, **CC BY 4.0**) ships per-model MMLU accuracy
in-repo, but leaderboard data is frozen ~2024 and covers only 18/47
connected-subset models (DeepSeek absent). The trait is therefore produced by a
fresh evaluation of the G3 subset — 22 of 47 connected-subset models on MMLU
5-shot (strict common item set); Kim's values are kept only as a validation
cross-check. The G3 gate (`datasets/coverage/g3_report.md`) showed the 22-model
population clears the strict Phase 1 D2 bar (mean-over-reps bias + margin
confirmation), so the extra 25 models are not GPU-justified. Infrastructure:
`src/lineage_era/phase2_eval.py` (47/47 manifest + lm-eval-harness runner) and
`src/lineage_era/phase2_run_all.py` (defaults to the G3 subset). Run venue /
HF token / budget open.

## Artifact-availability audit (2026-08-03)

Per-model x source reuse table: `datasets/coverage/artifact_audit.csv` (built
by `src/lineage_era/analysis/artifact_audit.py`). Verdict: **protocol-matched
per-question reuse = 0/47** — openllm MMLU-PRO per-sample JSONL exists for 8/47
(wrong benchmark, frozen ≤ Dec 2024, 401-gated), HELM per-question MMLU exists
for 10/47 (HELM item set/question ids — no bridge to `cais/mmlu`, no DeepSeek),
aggregate MMLU exists for 18/47 (score-only cross-check, register A22), and
29/47 have no public artifact. Every model therefore needs fresh inference.
GPU plan: `datasets/coverage/gpu_cost_estimate.csv` (built by
`src/lineage_era/analysis/gpu_cost.py`) — one 8xH200-141GB (fp8) node, ~12–24
wall-hours for all 47, ~$100–300; hard gate = the gated models, not cost. The
G3 gate (2026-08-03) cut the scope to 22 models (~67% of that cost).

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
- **Scope — G3 minimum valid population (22 of 47):** `datasets/coverage/
  minimum_valid_population.csv` (built by `src/lineage_era/analysis/
  population_optimizer.py`; report `datasets/coverage/g3_report.md`). The
  structural minimum (21) is identifiable but sits exactly on the strict bar
  (knife-edge, register A25), so the first confirmed-clearing population is 22.
  Subset: 14 public + 8 gated; est. ~710 vs 2154 single-GPU minutes (67% cut).
- **Manifest:** the 22 subset models have a canonical HF checkpoint (verified
  2026-08-03). Gated in the subset: meta-llama 3 (Llama-1/3.1/3.3), Mistral org
  4 (Mistral-Small-3/3.2/4, Devstral-2), Google 1 (Gemma-3n) — need `HF_TOKEN`
  with the license accepted.
- **Runner:** `python3 -m lineage_era.phase2_run_all --device cuda:0` (from
  `src/`; defaults to the G3 subset; `--only <full_name>` for one model;
  `--subset <csv>` to run a different set, e.g. all 47).
- **Per-model caveats:** Phi-1/1.5/2 are 2048-token context — some MMLU 5-shot
  prompts exceed it and crash; needs `max_length` handling (their paper's MMLU
  values are also at 2048, so truncation is the faithful reading). Sliding-window
  models (Qwen, Mistral) should use `sdpa` on GPU, not `eager`.
- **Intake validation:** `python3 -m lineage_era.phase2_eval_check --manifest
  datasets/coverage/minimum_valid_population.csv` (validates the 22-row intake against
  the G3 subset instead of the full 47).
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
| MMLU (fresh pass) | 5-shot, loglikelihood | `cais/mmlu` | 14,042 | dev 5-shot / test | possible (disclose) | per-model acc via lm-eval 0.4.12 | 22/47 (G3 subset) |

## Fallback plan

If the fresh eval pass is infeasible at budget, decompose on the 18/47
leaderboard-covered models and report the partition as covering 2023–2024 with
DeepSeek absent (last resort; Phase 1 shows family bias ~ -5pp at F=6 and era
underpower). Cost/budget decision recorded in the Research Decision Log.
