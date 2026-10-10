# RunPod Phase 2 evaluation: evidence audit (2026-10-10, revised)

Sections 1-9 record the audit before the authors' answers; Section 10 records
the resolution, which supersedes the open questions in Sections 5, 6 and 9.
`RunPod_proposed_manuscript.diff` is the proposal as reviewed; the applied
version adds the tightenings listed in Section 10.

Scope: reconstruct the single-A100 RunPod evaluation (the "per-model" arm) from
the repository, compare it with the account supplied for documentation
("20 measured: 17 bf16 + 3 NF4; 2 imputed"), and decide how it can be reported.
Nothing in the manuscript, data or results was changed by this audit.

## 1. Evidence inspected

| File / object | What it shows |
|---|---|
| `docs/05_Experiments/Exp02_GPU_Runbook.md` (addendum 2026-08-16) | Planned pod: A100-80GB SXM4, GPU disk >= 300 GB, Python 3.11 PyTorch template; ~604 GPU-min, ~10 h, ~$16-20 at ~$1.60/h; one model per invocation, verify 14,042 samples, commit, clear HF cache |
| `docs/00_Project/Research_Decision_Log.md` (two 2026-08-16 entries) | Single-pod decision; fidelity ledger amended before any eval (Phi-2 pilot failed pre-measurement, wrote no data); DeepSeek-V3.1/V3.2 to be imputed (m = 5, seed 2026); three re-gate variants infeasible |
| `datasets/coverage/trait_definition.csv` | Planned ledger: 17 bf16, 3 4-bit (Qwen1.5-72B, Llama-3.1-70B, Llama-3.3-70B), 2 imputed |
| `datasets/coverage/a100_full_subset.csv` | Planned 20-model manifest |
| `datasets/coverage/minimum_valid_population.csv`, `g3_report*.md` | 47 -> 22 selection and the three DeepSeek re-gate variants |
| `datasets/phase2_eval_results.csv` | **16 rows** (measured accuracies, lm-eval aggregate `acc`) |
| `datasets/eval_samples/*.jsonl` | **16 files**, 14,042 rows each |
| `src/lineage_era/phase2_eval.py`, `analysis/eval_check.py`, `analysis/impute.py` | Extraction, intake check, imputation code |
| `results/phase2_empirical/` | 16-model decomposition (earlier manuscript); no imputed rows |
| `docs/08_Reviews/Revision_2026-10_Precision_Gate.md` | 2026-10-09 audit that already found items 3.1-3.4 below |
| `paper/src/supplement.tex` S2 | Current manuscript: sixteen-model arm "not used for inference" |
| git history (commits 0258bfc, 0a86f3b, 38bace0 ... 535800a, 8aa1602) | Timeline below |

## 2. Timeline (from commit timestamps, UTC)

| When | Commit | Event |
|---|---|---|
| 2026-08-16 10:44 | 0258bfc | DeepSeek imputation rule and re-gate variant reports committed |
| 2026-08-16 15:01 | 0a86f3b | Single RunPod A100 run "pre-registered": 17 bf16 + 3 4-bit |
| 2026-08-16 18:08 | 38bace0 | First eval committed (Phi-1) |
| 2026-08-17 | 392ca62 ... f553bcf | 13 further models; Mistral-Small-4 committed as **4bit** |
| 2026-08-17 | fb2a98e, 19582a6 | Mistral-Small-3.1 = 0.249, Mistral-Small-3.2 = 0.250 |
| 2026-08-18 07:32-09:12 | 4129136, f5f51dc, 535800a | Qwen-7B; Mistral-Small-3.1/3.2 **re-run** ("corrected config") after the first results: 0.234, 0.231 |
| 2026-08-18 | 28b8c28 | 16-model audit: WITHHOLD decision |
| 2026-10-09 | 8aa1602 | Extraction bug found and fixed in code; per-question files not regenerated |

The imputation rule and the run plan were committed before the first
evaluation. The two Mistral-Small reruns were made after their first outcomes
were seen.

## 3. Discrepancies with the account supplied for documentation

1. **16 models were measured, not 20.** The four planned models with no
   result anywhere in the repository: Qwen1.5-72B, Llama-3.1-70B,
   Llama-3.3-70B (the three planned NF4 models) and Phi-4-reasoning-vision-15B.
   No decision-log entry records why they were not run.
2. **No planned 4-bit model was run.** The only 4-bit result is
   Mistral-Small-4, planned at bf16 as a 32B model; the evaluated repository
   (`Mistral-Small-4-119B-2603` in the sample file name) is a 119B model.
3. **All 16 per-question files are invalid.** Each stores one log-likelihood
   per item and predicts option A on all 14,042 items (`phase2_eval` read
   `resps[0]`). Their item-level correctness is the all-A rate (0.2295) for
   every model. No item-level analysis can use them; regenerating them needs
   the raw lm-eval sample outputs or a re-run.
4. **Several aggregate accuracies are implausible.** The CSV `acc` comes from
   lm-eval directly and is unaffected by the extraction bug, except that
   Qwen-7B (0.2295) equals the all-A rate exactly. Devstral-2 (0.251),
   Mistral-Small-3.1 (0.234), Mistral-Small-3.2 (0.231) and Mistral-Small-4
   (0.243) are at chance for 24B+ instruction models; a loader or
   chat-template problem is likely. Phi-1 (0.248) is a code model and may be
   genuinely near chance.
5. **Six models were run from repositories other than the ledger's:**
   Llama-1 (ledger `meta-llama/Llama-1`, run `huggyllama/llama-7b`),
   Mistral-Small-3 (`Mistral-Small-3-24B-Instruct-2501` vs
   `Mistral-Small-24B-Instruct-2501`), Gemma-3n (`gemma-3n-4b-it` vs
   `gemma-3n-E4B-it`), Mistral-Small-3.2 (`-2510` vs `-2506`), Devstral-2
   (`Devstral-Small-2509` vs `Devstral-Small-2-24B-Instruct-2512`) and
   Mistral-Small-4 (above).
6. **The DeepSeek imputation was implemented but never executed on measured
   data.** `results/phase2_empirical/` holds a 16-model fit with no imputed
   rows. Any statement that two traits "were imputed" describes a plan.
7. **Resources and cost are not recoverable from the repository.** The runbook
   gives planned values (>= 300 GB disk, ~604 GPU-min, ~$16-20 at ~$1.60/h).
   No pod configuration, volume record, event log or invoice is committed. A RunPod
   console view supplied during review shows a template and the account's
   current state, not the executed pod; its details are not recorded here.

## 4. Relationship to the current manuscript

- The pair-level study (977 leaderboard models; 590 primary, 928 expanded)
  uses none of the RunPod data. Its numbers are unaffected.
- The variance-decomposition precision figure (Fig. 4) and Supplementary S1
  use simulated traits on candidate rosters (`results/precision_gate/`); the
  point labelled 16 is the measured roster's *structure*, not its measured
  accuracies. These are traceable and remain valid.
- Supplement S2 already states that the sixteen-model arm is not used for
  inference, that four planned models were not evaluated, and that the
  extraction bug invalidated item-level predictions. It does not yet give the
  hardware, software, fidelity, timeline or the implausible accuracies.

## 5. What can be reported responsibly now

The RunPod run can be documented as an **earlier, incomplete per-model
evaluation that motivated the pair-level design and is not used for
inference**: 16 of a planned 20 models measured on one A100-80GB, with the
fidelity table as actually executed, the four unexplained omissions, the
invalid item-level files, the implausible accuracies, the planned (not
executed) imputation, and planned rather than actual resources.

It cannot be reported as 20 measured models, as a NF4 measurement of the 70B
tier, as an imputed 22-model analysis, or as evidence about quantization
effects. No BF16-versus-NF4 comparison exists, so the description of 4-bit as
"conservative" has no empirical support here.

## 6. Needed from the authors before documenting further

1. Do results for Qwen1.5-72B, Llama-3.1-70B, Llama-3.3-70B and
   Phi-4-reasoning-vision-15B exist anywhere (pod volume, another machine,
   unpushed commits)? If not, why were they not run (OOM, disk, gated access,
   time, cost)? If any reason involved seeing results, say so.
2. Do the raw lm-eval sample outputs for the 16 models survive (they contain
   all four log-likelihoods per item)? If so, the per-question files can be
   regenerated with the fixed extractor.
3. Why was Mistral-Small-4 run at 4-bit using the 119B repository?
4. What was changed in the Mistral-Small-3.1/3.2 "corrected config" reruns?
5. Actual pod disk and billed cost, from the RunPod billing or pod history, if
   they are to be reported; otherwise the paper reports planned values only.

## 7. Revision (same day): recovery search and verification

### 7.1 Search for raw lm-eval outputs (item 3 of the instructions)

| Where | Result |
|---|---|
| Working tree: `samples_*`, `results_*.json`, `*lm_eval*`, `*harness*` | none |
| Every path ever committed on any branch (716 paths) | no raw lm-eval output |
| `stash@{0}` and 60+ unreachable stash commits, including their untracked-file parents | no raw lm-eval output |
| Every historical version of the 16 per-question files (28 versions) | all store 1 log-likelihood per item |
| `~` to depth 6 (excluding `~/Library`) and `/Volumes`: `samples_mmlu*`, `results_2026-08*.json` | none |

The per-question predictions cannot be reconstructed. Nothing was
regenerated or inferred from aggregate accuracies.

### 7.2 Which measurements remain usable

None is used for inference. The 16 aggregate accuracies are lm-eval's own and
do not pass through the faulty extraction, but none can be validated item by
item. Only two recorded repositories also have item-validated leaderboard
predictions (`results/exp04_validation/per_model.csv`):

| Model | RunPod (lm-eval aggregate) | Leaderboard (item-validated) |
|---|---|---|
| Phi-1.5 (`microsoft/phi-1_5`) | 0.422 | 0.424 |
| Qwen-7B (`Qwen/Qwen-7B`) | 0.229 (= all-A rate) | 0.584 |

Chance-level and unresolved: Phi-1 (0.248), Mistral-Small-3.1 (0.234),
Mistral-Small-3.2 (0.231), Devstral-2 (0.251), Mistral-Small-4 (0.243).

### 7.3 Precision figure (Fig. 4) and Supplement S1

`scripts/run_precision_gate.py` reads `datasets/phase2_eval_results.csv` only
for the `full_name` column, to define the obs16 design's family x quarter
incidence; `analysis/precision_gate.monte_carlo_precision` simulates the
traits. `run_precision_scaling.py` uses synthetic staggered designs. No
measured accuracy or per-question output enters the figure or Table S-precision.
Kept, with a caption sentence saying so.

### 7.4 Timing of decisions (commit timestamps)

- Roster selection (G3, trait-blind by its report): 2026-08-03, last revised 2026-08-05.
- Imputation rule: 2026-08-16 10:44 UTC. Run plan: 2026-08-16 15:01 UTC.
- First evaluation: 2026-08-16 18:08 UTC.
- Mistral-Small-3.1/3.2 reruns: after their first results (2026-08-18).

## 8. Proposed manuscript change (not applied)

`docs/08_Reviews/RunPod_proposed_manuscript.diff` (applies cleanly to
`revision/precision-gate`; 4 files, +110/-6):

- Main paper: one sentence in the Introduction; one sentence in the Fig. 4
  caption; one clause in Data Availability. No result, count, table or figure
  of the pair-level study changes.
- Supplement S2: the sixteen-model row corrected ("two DeepSeek models
  imputed" -> imputation specified but not executed; per-question outputs
  invalid).
- Supplement S7 (new): selection and plan (planned resources labelled as
  planned), what was recorded, the four missing models (reason unknown), the
  Mistral-Small-4 mismatch, the extraction failure and recovery status, the
  unresolved chance-level accuracies, the leaderboard cross-check, and Table
  S-runpod generated from the ledger and result files.
- `scripts/make_exp04_tables.py`: `tab_runpod()` writes that table.

## 9. Still requires author confirmation

1. Why the four planned models were not run (or confirmation that the reason is unknown).
2. Why Mistral-Small-4 was run from the 119B repository in 4-bit.
3. What changed in the Mistral-Small-3.1/3.2 "corrected config" reruns.
4. Whether raw lm-eval outputs survive anywhere outside this computer (pod volume, another machine).
5. Actual pod disk, run time and billed cost, if they are to be reported.
6. Approval of the proposed diff.

## 10. Resolution (authors, 2026-10-10)

1. Four planned models: not run. The authors stopped after 16 models because
   further GPU time could not be funded. No decision-log entry records it.
2. Mistral-Small-4: run from `Mistral-Small-4-119B-2603` in 4-bit (commit
   f553bcf). No decision-log entry; the only rationale on record is
   `docs/archive/REPRODUCIBILITY_CHECKLIST_v1_16model.md` ("119B params, does
   not fit BF16 in 80GB").
3. Mistral-Small-3.1/3.2 reruns: commit 27886ef (quant kwargs, rope_parameters;
   2026-08-17 13:46 UTC) preceded the first runs (14:37, 15:24 UTC); commit
   cca711c (register Mistral3ForConditionalGeneration with
   AutoModelForCausalLM; 2026-08-18 05:42 UTC) is the change between the first
   runs (0.249/0.250) and the reruns (0.234/0.231).
4. Raw lm-eval outputs: none recoverable.
5. Disk, run time, cost: planned values only.
6. Diff approved and applied with the tightenings above; tables regenerated
   (no pair-level table changed), manuscript (16 pp.) and supplement (10 pp.)
   rebuilt with no undefined references; test suite 63 passed.
