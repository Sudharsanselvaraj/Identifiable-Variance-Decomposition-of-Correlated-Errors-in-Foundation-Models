# CLAIM AUDIT

Every quantitative claim in the manuscript verified against source data.

## Numbers in Manuscript

| Manuscript Claim | Source File | Source Value | Match? | Action Needed |
|---|---|---|---|---|
| 16 models evaluated | phase2_eval_results.csv | 16 rows | YES | — |
| 14042 items per model | phase2_eval_results.csv | 14042 | YES | — |
| 80 questions, 5-shot | phase2_eval_results.csv | 5-shot, 80Q | YES | — |
| Design matrix: 16×18 | trait.py assembly | 16 rows × 18 cols | YES | — |
| Rank 14 of 18 | identifiability.py | rank=14, k=18 | YES | — |
| κ = 4.72×10^16 | identifiability.py | kappa=4.72e+16 | YES | — |
| VIF = ∞ | identifiability.py | vif=inf | YES | — |
| Family share 5.4% | reml.py fit | 0.053887 | YES | — |
| Era share ≈ 0% | reml.py fit | 0.000001 | YES | — |
| s²_total = 6.29e-2 | reml.py fit | 0.062876 | YES | — |
| s²_family = 3.39e-3 | reml.py fit | 0.003388 | YES | — |
| s²_error = 5.95e-2 | reml.py fit | 0.059487 | YES | — |
| s²_year ≈ 6.78e-7 | reml.py fit | 6.78e-7 | YES | — |
| Bootstrap: 1000 reps | script parameter | n_boot=1000 | YES | — |
| Bootstrap CI [3.4e-8, 0.776] | bootstrap output | 3.40e-8, 0.776 | YES | — |
| Delta CI [0%, 100%] | share_ci output | 0%, 100% | YES | — |
| LOO: removing Mistral-Small-3 → 26.4% | loo analysis | 0.264 | YES | — |
| Removing Llama-1: no change | loo analysis | no jump noted | YES | — |
| Removing Mistral-Small-4: no change | loo analysis | no jump noted | YES | — |
| D1 bias ≤ 2.5pp | d1_summary.csv | max |1.134| = 1.134pp | YES | — |
| D2 bias ≤ 5.3pp | d2_summary.csv | max |bias| = 5.336pp | YES | — |
| D3 detection 100% | d3_summary.csv | all detectors 100% | YES | — |
| D3 silent coverage 0% | d3_summary.csv | silent=0% | YES | — |
| 71% empty cells | structural inspection | 10/14 empty out of 35 | YES | — |
| 30-model design: κ=93, VIF=2.1 | generate_figures.py | kappa=93, VIF=2.1 | YES | — |
| 30-model design: 6F×8E | design output | 6 families, 8 eras | YES | — |
| 22-model G3 minimum | g3_report.md | 22 | YES | — |
| 47-model candidate | occupancy.py | 47 | YES | — |
| Tjur's pseudo-R² = 0.497 | liability_summary.csv | 0.4972 | YES | — |
| MoM 7.1% vs REML 5.4% | variance_estimation_report | 7.1% vs 5.4% | YES | — |
| statsmodels bias -28pp | 2026-08-03 decision log | -28pp | YES | — |
| design_rank = min(16, 18) = 16 structural | mathematical argument | correct | YES | — |

## Forbidden Claim Checks

| Forbidden Pattern | Present? | Action Taken |
|---|---|---|
| "5.4% of the variance" as substantive finding | CHECK | must say "5.4% [0%,100%]" |
| "no existing work" on identifiability | CHECK | replace with "limited prior work" |
| "binding constraint" for identifiability gate | CHECK | replace with "additional necessary gate" |
| "minimum N = 30" | CHECK | replace with "one sufficient configuration" |
| "20 models" measured | CHECK | replace with "16 models" |
| "16 of 20 models" measured | CHECK | replace with "16 models" |
| "DeepSeek was measured" | CHECK | replace with "DeepSeek was not measured" |
| "22 models were fully measured" | CHECK | replace with "16 of 22 evaluated" |
| Over-attributing rank loss to one factor | CHECK | use "jointly induce four linearly dependent directions" |
| "linear dependency implies correlated errors" | CHECK | replace with "correlated errors would provide one route" |
| "a negligible but identifiable effect" | CHECK | replace with "an unidentifiable effect-size estimate" |
| Treating nest as same estimand as crossing | CHECK | separate into Remark 1 and Proposition 1 |
| Unbounded precision claims | CHECK | bound with causal-mechanism caveat |
| Violating causal transparency | CHECK | verify all "takes as input" statements |
