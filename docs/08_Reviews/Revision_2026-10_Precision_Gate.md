# Revision 2026-10: precision gate, reproduction, eval fix, selection reconciliation

Branch: `revision/precision-gate`. Status: steps 1–4 done; step 5 (manuscript
rewrite) waits on the Option A / Option B decision at the end.

## Headline

1. **The paper's gate tests the wrong model.** It checks rank/κ/VIF of the
   fixed-effects dummy design `[1 | Z_F | Z_E]`, but `reml.CrossedREML` fits
   family and era as *random* effects with an intercept-only fixed part. For
   that model the variance components are identified iff
   `{Z_F Z_F', Z_E Z_E', I}` is linearly independent — rank **3/3** for the
   16-model population. "Not identifiable" is false for the fitted model.
2. **The real problem is precision, and it is much worse than the paper says.**
   Under the fitted estimator, *no* design in the paper — not the 16, not the
   22, not the full 47-model frame, not the "sufficient" 30-model design —
   recovers the family or era share to within ±10pp RMSE. Precision is set by
   the number of **family levels** and **era levels**, not by N. Reaching
   ±10pp needs roughly **60 families and ≥14 eras**.
3. κ(X'X) depends on which level is dropped as reference: the "passing"
   30-model design has κ between **91.5 and 144** for the same design, so its
   PASS under κ ≤ 100 is an artifact of coding.
4. The constant per-question predictions were an extraction bug (fixed), not
   corrupt data.
5. The 16-model population was not what the selection procedure chose: four
   pre-registered models (Llama-3.1, Llama-3.3, Qwen1.5,
   Phi-4-reasoning-vision-15B) were dropped with no log entry. Adding just the
   two Llamas back removes the rank deficiency the paper's headline is built on.

## Step 1 — Precision gate (new)

Code: `src/lineage_era/analysis/precision_gate.py` (tests:
`test_precision_gate.py`). Drivers: `scripts/run_precision_gate.py`,
`scripts/run_precision_scaling.py`. Outputs: `results/precision_gate/`.

Two layers, both computed from design metadata only (pre-measurement):

- **Analytic screen:** expected REML information
  `I_ij = ½ tr(P V_i P V_j)` at four share scenarios (A lineage 0.5/0.2/0.3,
  B era 0.2/0.5/0.3, C balanced, D low-signal 0.1/0.1/0.8) → delta-method SE
  of each share, plus corr(σ̂²_L, σ̂²_E) as an aliasing index.
- **Monte Carlo verdict:** simulate on the design, refit with the same
  `CrossedREML`, report bias / RMSE / 95% width / boundary rate (500 reps).
  Pre-specified bar used here: share RMSE ≤ 0.10 in every scenario (this bar
  is an author decision; the RMSE values are reported so any bar can be read
  off).

The analytic SE tracks the Monte Carlo RMSE closely (e.g. obs16 scenario A:
0.289 vs 0.285; cand47: 0.187 vs 0.189), so the cheap screen is usable as a
pre-measurement gate.

| design | n | F | E | fixed-effects rank ok | κ (paper coding) | κ range over reference levels | covariance-basis rank | worst share RMSE (MC) |
|---|---|---|---|---|---|---|---|---|
| obs16 (measured) | 16 | 5 | 11 | no | 4.7e16 | singular | 3 | 0.302 |
| obs16 − Llama-1 | 15 | 4 | 10 | yes | 585 | 115–585 | 3 | 0.302 |
| sel22 (selected) | 22 | 6 | 14 | yes | 1100 | 285–1526 | 3 | 0.256 |
| cand47 (full frame) | 47 | 6 | 14 | yes | 234 | 166–1116 | 3 | 0.189 |
| sweep F6 E8 M5 (paper's "sufficient") | 30 | 6 | 8 | yes | 93* | 91.5–144 | 3 | 0.194 |
| sweep F7 E8 M6 | 42 | 7 | 8 | yes | 98* | 83–113 | 3 | 0.182 |
| sweep F6 E12 M5 | 30 | 6 | 12 | yes | 316 | 204–328 | 3 | 0.203 |
| nested reference | 72 | 6 | 6 | no | 4.9e17 | singular | **2** | not identified |

\* value from `sweep_results.csv` (drops the first level); the range column
shows the same design under every other reference choice.

Observations:

- Removing Llama-1 fixes the fixed-effects rank but does **not** change
  precision (0.302 → 0.302). The rank deficiency the paper centres on is
  irrelevant to the fitted model.
- The analytic corr(σ̂²_L, σ̂²_E) is ≤ 0.07 for every identified design: family
  and era are *not* aliased; they are each estimated from too few levels.
- Boundary collapse is common: obs16 collapses the era share to ~0 in 18–51%
  of replicates and the family share in 14–46% — so the observed σ̂²_era ≈ 0
  is exactly what the design produces whatever the truth is.

Scaling (`family_scaling.csv`, 300 reps): worst-case share RMSE

| F | E=8, M=4 | E=14, M=6 |
|---|---|---|
| 6 | 0.221 | 0.186 |
| 10 | 0.187 | 0.142 |
| 20 | 0.162 | 0.119 |
| 30 | 0.149 | 0.110 |
| 60 | 0.142 | **0.098 (pass)** |

With 8 eras the era share never gets below ~0.14 regardless of F: era
precision is capped by the number of quarters in the observation window.

## Step 2 — Reproduction of the paper's numbers

Everything computational reproduces exactly from the stored code and data:

| claim | reproduced |
|---|---|
| obs16 rank 14/15, κ = 4.7e16, VIF ∞ | yes |
| sum-to-zero coding κ = 3.6e16 | yes |
| sel22 κ = 1100 (fails N1) | yes |
| LOO: only removing Llama-1 restores rank; κ = 585 | yes |
| half-year κ = 227, year κ = 202 | yes |
| REML: σ²_fam 0.00274, σ²_era ≈ 0, σ²_unique 0.0478, share 5.4% | yes |
| LOO Mistral-Small-3 → family share 26.4%; 7 removals collapse it to 0 | yes |
| sweep 105 / 40 / 3 / 3 | yes (byte-identical CSV) |

But the following **text** claims are wrong (step 5 list below). Of the 7
models whose removal collapses the family share to 0, four are the near-chance
Mistral-family models (Devstral-2, Mistral-Small-3.1/3.2/4) and three are Phi
models — the 5.4% estimate leans on accuracies flagged as possibly invalid.

`scripts/run_design_space_sweep.py` compared against stale pre-revision
numbers (2184/847/312/298) and printed "MISMATCH"; constants updated to
105/40/3/3, now prints VERIFIED.

## Step 3 — Evaluation pipeline

- **Cause:** `phase2_eval._samples_to_rows` used `resps[0]`, i.e. only choice
  A's log-likelihood, so argmax was always 0. Fixed via `_choice_logprobs`,
  which reads one log-likelihood per choice (`filtered_resps`, falling back to
  `resps`), and a hard check that the extracted correctness agrees with
  lm_eval's own per-sample `acc`.
- **Intake guard:** `eval_check` now errors when a model predicts a single
  choice for every item or stores < 2 logprobs per item. It flags all 16
  existing files.
- **Tests:** `test_phase2_eval_samples.py` (6 cases, incl. string-typed
  values and the mismatch guard).
- **Not done (needs GPU or raw lm_eval output):** regenerating per-question
  files. The aggregate `acc` values in the CSV came from lm_eval directly and
  are unaffected by this bug, **except Qwen-7B (0.2294)**, which equals the
  all-"A" rate exactly and should be treated as an artifact. The other
  near-chance values need a separate check (chat template / loader), ideally
  against published MMLU scores.

## Step 4 — 47 → 22 → 16 reconciliation

- 47 candidate frame → 22 by Algorithm 1 (`minimum_valid_population.csv`,
  every keep/drop has a recorded reason).
- 2026-08-16 decision log: DeepSeek-V3.1/V3.2 not evaluated (compute) and
  pre-registered to be **imputed**; the paper does not mention imputation.
- 2026-08-16 pre-registration (commit 0a86f3b): one A100-80GB run of 20 models
  — 17 bf16 + Qwen1.5-72B, Llama-3.1-70B, Llama-3.3-70B at 4-bit.
- What actually ran: 16 models. Not run, with **no decision-log entry**:
  Llama-3.1, Llama-3.3, Qwen1.5 (the three planned 4-bit models) and
  Phi-4-reasoning-vision-15B (planned bf16). Mistral-Small-4, planned bf16,
  was run at 4-bit. No evaluated model was outside the selection.
- Consequence: obs16 + Llama-3.1 + Llama-3.3 has full fixed-effects rank
  (16/16). The paper's headline rank failure is created by the undocumented
  exclusions, not by the population-selection procedure. (Under the precision
  gate it fails either way.)
- Needed from the authors: the actual reason each of the four was dropped
  (OOM, gated access, loader error, time). If any reason involves looking at
  results, the outcome-independence claim must be weakened.

## Other fixes on this branch

- Two stale tests fixed: the manifest now loads Llama-1 and four others from
  public mirrors (28 public / 19 gated, not 23 / 24). Suite: 58/58 pass.
- `requirements.txt` updated to the versions the paper reports and the code
  was run with (numpy 2.1.3, scipy 1.17.1, pandas 3.0.5, statsmodels 0.14.6,
  matplotlib 3.9.2).

## Step 5 — Manuscript claims that must change (`paper/src/ieee_access_manuscript.tex`)

Not yet edited; the rewrite depends on the decision below.

| line | claim | problem |
|---|---|---|
| 118, 172, 691–717, 973, 1028 | "fails four of five gate conditions" / "not identifiable" | Covariance basis 3/3: the fitted model is identified. S1, S3, N1, N2 failures are one fact (Llama-1 alone in 2023Q1) counted four times, and are fixed-effects properties. |
| 261, 272 | θ_P identified iff crossed + full rank + κ + VIF | Wrong condition for a random-effects model. |
| 420 / abstract | recovery "within 2.5pp / 5.3pp" | These are mean bias, not precision. At the real occupancy RMSE is 0.19–0.30. The decision log (2026-08-03) already recorded that F=6 caps family-share coverage. |
| 754 | sweep enforces crossing and connectedness "by construction" | `sweep_results.csv`: 100/105 crossed, 60/105 connected. |
| 760, 820 | 30 models / 6 families / 8 eras is "sufficient" | κ is 91.5–144 depending on reference level; precision RMSE 0.19. All 3 passing designs sit at E = 8, the grid's lower edge; one has 5 families. |
| 830 | at κ_max = 50 the 30-model design "still passes (κ = 93)" | 93 > 50. False. |
| 552 | "four additional models were deprioritized" | Undocumented deviation from pre-registration; reason must be stated. |
| 552–586 | DeepSeek "could not be evaluated" | Pre-registered imputation not mentioned. |
| 583, 935, 1012 | JSONL "corrupted" | Extraction bug, now fixed; say so. |
| 600, Table | Qwen-7B accuracy 22.9% | Equals the bug's all-A rate; artifact. |
| 1068+ | six 2026 references, two truncated titles | Verify each before submission. |

## Decision needed

- **Option A — methods paper.** Replace the fixed-effects gate with the
  precision gate; the empirical result becomes "with ≤ 7 families and ≤ 14
  quarters the family/era shares cannot be estimated to better than ±20pp
  RMSE, whatever N is". Honest and fast, but the contribution is a design
  power analysis.
- **Option B — empirical paper.** The scaling result says ~60 families are
  needed for a per-model trait. That rules out "evaluate more models
  ourselves" but fits the Open LLM Leaderboard per-question details (already
  referenced in `artifact_audit.csv`), where "family" can be base model /
  developer across hundreds of models. An item- or pair-level outcome (error
  agreement per model pair, as in Kim et al.) carries far more information
  per model than one accuracy number and is the quantity the introduction is
  actually about.
