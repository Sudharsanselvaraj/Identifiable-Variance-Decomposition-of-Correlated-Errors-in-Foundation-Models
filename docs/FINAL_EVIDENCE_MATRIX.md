# FINAL_EVIDENCE MATRIX

Every scientific claim in the manuscript classified by evidence source.

| Claim | Evidence Source | Status | Safe to Publish? |
|---|---|---|---|
| 16 models evaluated on MMLU 5-shot, 14042 items | phase2_eval_results.csv | VERIFIED | YES |
| Mistral-Small-4 at 4-bit fidelity | phase2_eval_results.csv | VERIFIED | YES |
| Family×era occupancy is sparse (71% empty) | structural inspection of Table 6 | VERIFIED | YES |
| Design matrix rank = 14 of 18 | identifiability.py structural_checks | VERIFIED | YES |
| κ = 4.72×10^16 | identifiability.py structural_checks | VERIFIED | YES |
| VIF = ∞ | identifiability.py structural_checks | VERIFIED | YES |
| All three gate diagnostics FAIL | G1+G2+G3 from above | VERIFIED | YES |
| Family share point estimate 5.4% | REML fit (family-only model) | DIAGNOSTIC ONLY | NO as substantive finding |
| Era share ≈ 0% | REML fit (crossed model) | DIAGNOSTIC ONLY | NO as substantive finding |
| Bootstrap CI [3.4e-8, 0.776] | bootstrap analysis (1000 reps) | VERIFIED | YES, as showing unidentifiability |
| Delta CI covers [0%, 100%] | share_ci() from reml.py | VERIFIED | YES, as showing unidentifiability |
| LOO: removing Mistral-Small-3 shifts share to 26.4% | leave-one-out analysis | VERIFIED | YES, as showing instability |
| D1 recovery ≤ 2.5pp | Phase 1 simulation, d1_summary.csv | VERIFIED | YES |
| D2 recovery ≤ 5.3pp | Phase 1 simulation, d2_summary.csv | VERIFIED | YES |
| D3 detection 100%, silent coverage 0% | Phase 1 simulation, d3_summary.csv | VERIFIED | YES |
| LPM-REML preferred over binomial GLMM | Liability test, liability_summary.csv | VERIFIED | YES |
| L×E interaction non-identified (SE ratio ≈ 10^4) | Phase 1, lxe_summary.csv | VERIFIED | YES |
| statsmodels MixedLM does not maximize REML objective | Direct comparison, decision log 2026-08-03 | VERIFIED | YES |
| 30-model, 6F×8E sufficient design (κ=93, VIF=2.1) | Design sweep (generate_figures.py) | VERIFIED | YES, as sufficient design only |
| 22-model G3 minimum valid population | g3_report.md, minimum_valid_population.csv | VERIFIED | YES |
| 47-model candidate population | occupancy.py | VERIFIED | YES |
| DeepSeek NOT measured | phase2_eval_results.csv (absent) | VERIFIED | YES |
| JSONL files corrupted (all predict 0) | audit_summary.json | VERIFIED | YES |
| Error-similarity analysis not performed | JSONL corruption | VERIFIED | YES (explicitly disclosed) |
| Crossing implies identifiable rank (Proposition 1) | Mathematical derivation (Appendix D) | STRUCTURAL | YES |
| Nested case is different estimand (Remark 1) | Mathematical argument (Section 4.7) | STRUCTURAL | YES |
| Co-failure ceiling bounded by between-model share (Proposition 2) | Analytical derivation | STRUCTURAL | YES (in context of model) |
| Swap value governed by lineage-era ratio (Proposition 3) | Analytical derivation | STRUCTURAL | YES (in context of model) |
| Per-question error similarity across 16 models | JSONL (CORRUPTED) | INVALID | NO |
| Correlated-error empirical heatmap | Would require valid JSONL | NOT AVAILABLE | NO |
| "Family explains 5.4% of variance" | Invalid-design REML output | DIAGNOSTIC ONLY | NO |
| "Era has no effect" | Invalid-design REML output | DIAGNOSTIC ONLY | NO |
| "30 models is the universal minimum" | Design sweep (one configuration) | INSUFFICIENT | NO |
| "DeepSeek effects were measured" | DeepSeek not in eval results | FALSE | NO |
| "22 models were fully measured" | Only 16 of 22 evaluated | FALSE | NO |
