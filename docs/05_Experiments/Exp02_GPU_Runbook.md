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
