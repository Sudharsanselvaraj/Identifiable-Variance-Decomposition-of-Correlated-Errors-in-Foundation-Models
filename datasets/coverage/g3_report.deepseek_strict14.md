# G3 — Minimum Valid Population (exclusion variant: deepseek_strict14)

Generated 2026-08-16. Pre-measurement exclusion variant of the pre-registered 2026-08-03 gate; the pre-registered artifacts are unchanged.

> **Outcome-independent study design.** G3 never observes trait values during optimization. Its inputs are occupancy (family × quarter), the lineage graph (VERIFIED_EDGES endpoints, Mistral-Small chain), identifiability constraints, and cost. All recoverability checks use fixed-design DGP simulations — never real eval outputs, accuracies, or error-similarity results.

> **Pre-measurement exclusion.** The candidate models below were removed from the pool BEFORE any measurement (no trait, accuracy, or eval output observed), and the population-design procedure was rerun on the remaining candidate pool.

```
EXCLUDED_PREMEASUREMENT:
  - DeepSeek-V3.1
  - DeepSeek-V3.2

REASON:
  unavailable_reproducible_compute

STATUS:
  pre_measurement

DATE:
  2026-08-16
```

## INFEASIBLE

Reason: 2025Q3 has no remaining candidate

The era-convergence window (every quarter 2023Q1-2026Q2 keeps >= 1 model) cannot be preserved after the pre-measurement exclusion: the quarter(s) above have no remaining candidate. The search was not run and no population was selected.
