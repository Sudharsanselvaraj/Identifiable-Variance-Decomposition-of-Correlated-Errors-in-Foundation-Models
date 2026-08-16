# Exp02 — GPU Runbook: Fresh MMLU 5-shot Eval (Phase 2a)

Executes the pre-registered fresh-eval pass on the **G3 minimum valid population
(22 of 47)**. This is the only step that needs a GPU host; everything else runs
on a laptop. Copy the commands below verbatim (run from `src/` on the GPU host).

## Scope

| | Count | Notes |
|---|---|---|
| Total models | 22 | `datasets/coverage/minimum_valid_population.csv` (G3 gate 2026-08-03) |
| Token-free (public) | 14 | Pass 1, no `HF_TOKEN` |
| Gated | 8 | Pass 2, license accepted + `HF_TOKEN` |
| Benchmark | MMLU 5-shot | loglikelihood, no generation (memory-bound) |

Per-model memory/GPU plan: `datasets/coverage/gpu_cost_estimate.csv`.
Recommended node: one **8xH200-141GB (fp8)**; realistic **~12-24 wall-hours**.
DeepSeek-V3.1/V3.2 (671B/685B class, token-free) are the highest-memory step —
they run in fp8 on the 141GB cards.

## Prerequisites

- Python 3.11, `pip install lm-eval accelerate` (lm_eval 0.4.x; the runner was
  smoke-tested against 0.4.12 on the laptop).
- A GPU node; `nvidia-smi` shows the H200s.
- Hugging Face account for the 8 gated licenses.

## Step 0 — checkout

```bash
git clone https://github.com/Sudharsanselvaraj/Identifiable-Variance-Decomposition-of-Correlated-Errors-in-Foundation-Models.git
cd Identifiable-Variance-Decomposition-of-Correlated-Errors-in-Foundation-Models/src
```

## Step 1 — Pass 1, token-free (14 public models)

```bash
python3 -m lineage_era.phase2_run_all --device cuda:0 --skip-gated
```

- Defaults to the G3 subset (22 models); `--skip-gated` runs the 14 token-free
  ones. Resume is automatic: re-running skips models already in
  `datasets/phase2_eval_results.csv`.
- Optional per-model pilot first (sanity that HF + lm_eval work on this host):
  `python3 -m lineage_era.phase2_eval --model Phi-1 --limit 100 --device cuda:0`
- Fix knobs if needed: `--dtype bfloat16` (default), `--attn sdpa` (default;
  sliding-window attention for Qwen/Mistral/DeepSeek/Gemma), `--batch auto`.

## Step 2 — accept the 8 gated licenses

HF UI per-repo, or `huggingface-cli login` then accept each repo's license:

| Family | Models | HF orgs |
|---|---|---|
| meta-llama | Llama-1, Llama-3.1, Llama-3.3 | `meta-llama/*` (3) |
| Mistral | Mistral-Small-3, Mistral-Small-3.2, Mistral-Small-4, Devstral-2 | `mistralai/*` (4) |
| Google | Gemma-3n | `google/*` (1) |

## Step 3 — Pass 2, gated (8 models)

```bash
export HF_TOKEN=hf_...        # token with the 8 licenses accepted
python3 -m lineage_era.phase2_run_all --device cuda:0
```

Only the 8 gated models run (pass-1 results are skipped automatically).

## Step 4 — validate intake (run on the GPU host OR the laptop, from `src/`)

```bash
python3 -m lineage_era.analysis.eval_check \
  --manifest ../datasets/coverage/minimum_valid_population.csv
```

Must exit 0. Contract checked: exactly 22 rows (no missing/extras/duplicates),
`acc`/`acc_norm`/`samples` sanity, per-question JSONL row counts, `correct`
values, common-item-set A15. Missing per-question samples are a warning, not a
fail (the aggregate CSV still drives θ_P).

## Step 5 — return results

Commit and push the two artifacts:

- `datasets/phase2_eval_results.csv` (22 rows)
- `datasets/eval_samples/` (per-question JSONL; ~22 files, only if
  `--no-samples` was NOT used — keep it on for the error-similarity panel)

## After return (no GPU)

```bash
python3 -m lineage_era.phase2_decomposition   # from src/, real-data path
```

Then: review `results/phase2/PHASE2_REPORT.md`, interpret against the
Disconfirmability Register (Exp02 §Interpretation / Failure), stage figures, and
fill the pending manuscript entries. See `Exp02_Phase2_Decomposition.md` and
`RESEARCH_PROTOCOL.md` (Phase 2, actions 2b-2h).

## Contingencies

- A model fails mid-run: the runner catches it, logs it, continues; resume
  retries nothing already present. If `eval_check` then flags a missing model,
  re-run with `--only <name>` or disclose the gap.
- Identifiability gate hard-fails on real data (exit 2): pipeline aborts before
  spend on analysis; report the negative result per the register — do not
  fabricate a workaround.
- Time/GPU constraints: the G3 gate pre-validated 22 as the minimum valid
  population; do not silently drop to a smaller set (statistical validity).

## Addendum (2026-08-16) — rented single-GPU host, 4-bit for the 70B+ tier

**When this applies.** Colab Pro (T4 16GB / L4 24GB) cannot host the 70B–90B
tier at bf16 (140–180GB) or the DeepSeek 671B/685B class at all. If the only
available rental is a single **H100/A100-80GB** (Vast.ai / RunPod / Lambda, on
demand ~$1.5–2.5/hr), the full 22 needs 4-bit quantization for the 70B+ tier.

**Fidelity consequence (must be disclosed).** `phase2_eval.py` and
`phase2_run_all.py` now tag every result row with a `fidelity` column
(`bf16`/`fp16`/`8bit`/`4bit`/`default`). A 4-bit trait is *not* the bf16 trait
the paper describes; record the deviation in `trait_definition.csv` /
`Novelty_Claims.md` before running, and keep the tag in any manuscript footnote.
`phase2_run_all --quant 4bit` tags the whole pass uniformly.

**One-GPU 80GB plan (≈12–20 wall-hours):**

| Tier | Models | Precision on one 80GB |
|---|---|---|
| ≤9B | Phi-1/1.5/2/3/3.5/4, Phi-4 reasoning, Gemma-3n/4, Ministral-3, Llama-1, Qwen-7B, Mistral-7B | bf16 (`--quant none`) |
| 24–32B | Mistral-Small-*, Medium-*, Devstral, Qwen3.x, Gemma-3, Mixtral-8x7B | bf16 (48–64GB fits) |
| 46–141B | Mixtral-8x22B, Mistral-Large-2/3, Llama-2/3/3.1/3.3, Llama-4, Qwen1.5/2/2.5 | **4-bit** (`--quant 4bit`) |
| 671B+ | DeepSeek-V3/R1/V3.1/V3.2/V4 | **not feasible** on one 80GB even at 4-bit (≈335GB) |

```bash
# bf16 pass for everything that fits (G3 22-subset; token-free then gated):
export HF_TOKEN=hf_...
python3 -m lineage_era.phase2_run_all --device cuda:0 --skip-gated --quant none
python3 -m lineage_era.phase2_run_all --device cuda:0 --quant none
# then a separate 4-bit pass for the 70B+ tier would be RECOMMENDED but the
# runner skips models already in the CSV -- so pick ONE fidelity per model:
# run the whole roster at --quant 4bit if any model must be 4-bit (uniform tag),
# or run the small tier at bf16 in a FIRST CSV and the 70B+ tier at 4-bit in a
# SECOND pass via --only, merging the two CSVs by hand and tagging each row.
```

Practical notes for an ephemeral rented instance:

- Run one pass, `git add datasets/phase2_eval_results.csv datasets/eval_samples/`
  and push after each session — the instance may be reclaimed at any time.
- `pip install lm-eval accelerate bitsandbytes` (bitsandbytes is required for
  `--quant 4bit`; 4-bit loading uses `load_in_4bit=True` through lm-eval).
- Sanity pilot first: `python3 -m lineage_era.phase2_eval --model Phi-1 --limit 100 --device cuda:0 --quant none`.
- If the DeepSeek tier is mandatory at bf16/fp8, that family needs a
  multi-GPU H200 rental (as in the original Step 0–5 plan) — do not fold a
  671B model onto a single 80GB card. Alternatively drop the DeepSeek family
  and re-run the G3 gate on the achievable roster (a design change, log it in
  `Research_Decision_Log.md`).
- `eval_check` (Step 4) is unaffected by the extra `fidelity` column.

## Addendum (2026-08-16) — three-machine split: Omen 4050 + Colab free + H100

**Chosen plan.** Models 1–16 run at 4-bit on the free machines (Omen RTX 4050
6GB + Colab free T4); models 17–20 run on one rented H100/A100-80GB; DeepSeek
V3.1/V3.2 (21–22) are **unassigned** — they do not fit any card in this plan
(671–685GB even at 4-bit) and still need the multi-GPU H200 node or the
redesign decision below.

| Machine | Models (#) | Command (from `src/`, after `git pull`) |
|---|---|---|
| Omen 4050 6GB | 1–8 (≤7B) | `--quant 4bit` on #3–8; `--quant none` on #1–2 |
| Colab free (T4) | 9–16 (11–24B) | `--quant 4bit` |
| H100/A100 80GB | 17–20 (32B, 3×70B) | `--quant none` for #17, `--quant 4bit` for #18–20 |
| imputed (no GPU) | 21–22 DeepSeek | completed by imputation (Addendum 2026-08-16) |

Per-machine command pattern (each model is one invocation so a lost Colab/Omen
session costs nothing):

```bash
export HF_TOKEN=hf_...                       # required: #4,6,13,15,16 are gated
python3 -m lineage_era.phase2_eval --model Phi-1 --device cuda:0 --quant none
python3 -m lineage_era.phase2_eval --model Phi-2 --device cuda:0 --quant 4bit
...
git add datasets/phase2_eval_results.csv datasets/eval_samples/
git commit -m "eval: Phi-1, Phi-2 (4bit) [Omen]"
git push                                        # next machine git pull + resumes
```

Or in one Colab notebook cell loop, `--all`-style but scoped:

```python
import os, subprocess
models = ["Phi-4-reasoning-plus","Gemma-4-12B","Phi-3","Phi-4-reasoning-vision-15B",
          "Mistral-Small-3","Mistral-Small-3.1","Mistral-Small-3.2","Devstral-2"]
for m in models:
    subprocess.run(["python3","-m","lineage_era.phase2_eval","--model",m,
                    "--device","cuda:0","--quant","4bit"])
```

**Fidelity ledger for this split** (record in `trait_definition.csv`):
- #1–2 bf16, #3–16 4-bit, #17 bf16, #18–20 4-bit, #21–22 TBD.
- Mixed precision across the roster — disclosed, and reviewers can be told it
  is conservative (memory-bound log-likelihood is robust to 4-bit within the
  family's variance, which is what the partition recovers).

**CSV sync contract:** one shared `datasets/phase2_eval_results.csv` in the
repo; each machine pushes after its models; `already_done` in
`phase2_eval.py` makes re-runs no-ops. Never overwrite — always `git pull`
before running and `git push` after.

**Blockers before `eval_check` can pass (22 rows):**
1. All 20 measured models evaluated and synced (DeepSeek V3.1/V3.2 are
   completed by imputation — see Addendum below; they never touch a GPU).
2. All 8 gated licenses accepted under one `HF_TOKEN`.
3. `eval_check` then verifies exactly 22 rows with `fidelity` tags.

## Addendum (2026-08-16) — DeepSeek V3.1/V3.2 completed by pre-registered imputation

**Decision (log: Research_Decision_Log 2026-08-16).** The DeepSeek pair
(671B/685B MoE, ≈340GB at 4-bit) requires an 8xH200-class node that is outside
the compute budget. Three pre-measurement re-gate variants proved no
DeepSeek-free gate-valid population exists (`g3_report.deepseek_*`), so the
cells are completed by MULTIPLE IMPUTATION from the variance-components model
fitted on the 20 measured models. This is a pre-registered availability
imputation, not empirical measurement.

**What to run.** The 20 measured models (rows 1–20 of the table above) are
evaluated and synced exactly as planned. Then, on the laptop from `src/`:

```bash
python3 -m lineage_era.phase2_impute \
  --eval-csv ../datasets/phase2_eval_results.csv \
  --samples-dir ../datasets/eval_samples \
  --label deepseek_imputed --m 5 --seed 2026
```

Produces (never clobbers the real CSV):
- `datasets/phase2_eval_results.deepseek_imputed.csv` — 20 measured rows
  (`fidelity` as recorded) + 2 rows with `fidelity="imputed"` (draw 0);
- `datasets/eval_samples.deepseek_imputed/` — measured JSONL + draw-0 imputed
  JSONL aligned to the shared item set (A15);
- `datasets/coverage/imputation_report.deepseek_imputed.md` — draws,
  per-draw/pooled variance-partition sensitivity, and the 20-only measured
  reference;
- `datasets/coverage/imputed_draws.deepseek_imputed.csv` — all M draws.

**Then run the pipeline against the imputed paths:**

```bash
python3 -m lineage_era.analysis.eval_check \
  --manifest ../datasets/coverage/minimum_valid_population.csv \
  --csv ../datasets/phase2_eval_results.deepseek_imputed.csv \
  --samples-dir ../datasets/eval_samples.deepseek_imputed
python3 -m lineage_era.phase2_decomposition \
  --eval-csv ../datasets/phase2_eval_results.deepseek_imputed.csv \
  --samples-dir ../datasets/eval_samples.deepseek_imputed
```

**Disclosure requirements (binding):**
- Every table/figure cell for DeepSeek-V3.1, DeepSeek-V3.2 is labeled
  "IMPUTED (pre-registered model-based imputation), not measured". The study is
  measured on 20 models and completed by imputation on 2.
- Record the deviation in `trait_definition.csv` and `Novelty_Claims.md`
  before running, and keep the label in any manuscript footnote.
- Report the with/without sensitivity from `imputation_report.*.md` (20-only
  measured partition vs per-draw + pooled 22-model partitions); era-share
  results for 2025Q3/2025Q4 rest on imputed values and must be presented with
  that caveat.
- If the multi-GPU node becomes affordable later, re-measure the pair, drop
  the imputed rows, and re-run — the module is a stopgap, not a replacement.

## Addendum (2026-08-16) — Colab Free/T4 subset procedure

**Execution split (partition files derived from `minimum_valid_population.csv`):**
- `datasets/coverage/colab_t4_subset.csv` — **16 models** for Colab Free/T4
  (your 15 + Gemma-4-12B, which the 22-model population requires and a T4 fits);
- `datasets/coverage/a100_80gb_subset.csv` — 4 models (Qwen1.5, Llama-3.1,
  Llama-3.3, Mistral-Small-4) for the 80GB rental;
- DeepSeek-V3.1/V3.2 — never touch a GPU; completed by imputation (above).

**Fidelity ledger:** `datasets/coverage/trait_definition.csv` records every
model's machine, precision, fidelity tag, and gated status **before** the run
(per-model `4bit`/`bf16`/`imputed`). The T4 pass uses `--dtype float16
--quant 4bit --attn sdpa` (T4 has no bf16 tensor cores; the fidelity tag is
`4bit` either way). Record any change to a model's precision in that file
before re-running.

**Colab procedure:** clone the repo, install `lm-eval==0.4.12 accelerate
bitsandbytes`, set `HF_TOKEN` (5 gated: Llama-1, Mistral-Small-3/3.2,
Devstral-2, Gemma-3n), point `HF_HOME` at `/content/hf_cache`. Pilot with
`phase2_eval --model Phi-2 --limit 100 ... --quant 4bit` and remove the pilot
row + its JSONL before production. Then run `phase2_run_all --only <name>`
per model from the subset CSV, verify `samples == 14042` in
`datasets/phase2_eval_results.csv`, commit+push, and delete
`/content/hf_cache/hub` before the next model. `phase2_run_all` skips models
already recorded, so a dropped session resumes by re-running the loop. The T4
pass completes first and pushes; the A100 pulls and resumes (never run both
concurrently — one shared CSV). Validate the T4 pass with:

```bash
python3 -m lineage_era.analysis.eval_check \
  --manifest ../datasets/coverage/colab_t4_subset.csv \
  --csv ../datasets/phase2_eval_results.csv \
  --samples-dir ../datasets/eval_samples
```
