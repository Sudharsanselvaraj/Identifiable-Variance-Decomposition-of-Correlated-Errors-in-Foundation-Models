# Evaluation

Metrics and their mapping to the research questions and the Disconfirmability Register.

## Primary metrics

| Metric | Definition | Used in | Maps to |
|---|---|---|---|
| Variance shares | σ²_L / σ²_E / σ²_U (normalized) with CIs | Phase 2 | RQ3, RQ4, RQ6 |
| Estimator bias/MSE | Recovery error on known ground truth | Phase 1 | RQ1 |
| D3 aliasing detection | Does the nested design fail detectably? | Phase 1 | RQ2 |
| CI coverage | Nominal vs. empirical coverage | Phase 1 | RQ1 precision |
| Era-convergence slope | Trend of era share / shared-error level across quarters (table entry only) | Phase 2 | RQ5 |
| θ_P vs. θ_M contrast | Nonzero difference brackets structural lineage | Phase 2 | RQ4, register item "primary confounded by era" |

## Decision metrics (gates)

| Gate | Criterion |
|---|---|
| Phase 1 | GO / GO WITH CHANGES / NO GO — direct verdicts, no hedging |
| Phase 2 | Partition reported as table; register interpreted; no headline collapse |
| Phase 3 | Δerror-response vs. h²·S tracking; otherwise drop analogy |

## Model comparison (if the field asks)

AIC/BIC and cross-validation are secondary here: the estimand is variance components with
validity established in simulation first, not a predictive-model competition. AIC/BIC are
used only for path selection (LPM-REML vs. GLMM) in Phase 1.

## Reporting rules

- Intervals reported with every estimate (identifiability condition 4).
- Precision is a first-class output, not a footnote.
- Era-convergence collapses into a table entry, never a standalone headline.
