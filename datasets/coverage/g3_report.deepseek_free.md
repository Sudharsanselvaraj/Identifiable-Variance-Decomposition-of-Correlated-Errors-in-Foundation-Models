# G3 — Minimum Valid Population (exclusion variant: deepseek_free)

Generated 2026-08-16. Pre-measurement exclusion variant of the pre-registered 2026-08-03 gate; the pre-registered artifacts are unchanged.

> **Outcome-independent study design.** G3 never observes trait values during optimization. Its inputs are occupancy (family × quarter), the lineage graph (VERIFIED_EDGES endpoints, Mistral-Small chain), identifiability constraints, and cost. All recoverability checks use fixed-design DGP simulations — never real eval outputs, accuracies, or error-similarity results.

> **Pre-measurement exclusion.** The candidate models below were removed from the pool BEFORE any measurement (no trait, accuracy, or eval output observed), and the population-design procedure was rerun on the remaining candidate pool.

```
EXCLUDED_PREMEASUREMENT:
  - DeepSeek-V3
  - DeepSeek-V3.1
  - DeepSeek-V3.2
  - DeepSeek-V4

REASON:
  unavailable_reproducible_compute

STATUS:
  pre_measurement

DATE:
  2026-08-16
```

Era-convergence window relaxed to the quarters still holding a candidate (2023Q1, 2023Q2, 2023Q3, 2023Q4, 2024Q1, 2024Q2, 2024Q3, 2024Q4, 2025Q1, 2025Q2, 2025Q4, 2026Q1, 2026Q2); 2025Q3 excluded from the window because no candidate remains in that/those quarter(s).

| G3 input | Used? |
|---|---|
| Family × quarter occupancy | ✓ |
| Lineage graph (edges, θ_M chain) | ✓ |
| Identifiability constraints (rank, VIF, span, crossing) | ✓ |
| Cost (public > gated, est. GPU minutes) | ✓ |
| Trait values / accuracy | ✗ |
| Error similarity | ✗ |
| Evaluation outputs | ✗ |

Strict bar (Phase 1 D2 gate, mean over converged reps/scenario, seeds {'A': 101, 'B': 202}): |era share bias| <= 5.0pp AND era-share CI coverage >= 90.0%; convergence >= 90.0%.

Two-stage decision (heavy-tailed per-rep bias, register A21): candidates that clear the bar at 300 reps must ALSO clear it with >= 1.0pp margin (|bias| <= 4.0pp) at a high-precision 1000-rep confirmation before acceptance — knife-edge designs sitting on the bar are rejected.

Structural minimum n0 = 43 (identifiable: full rank + VIF<=10).
**Minimum VALID population = 43** of 43 (all required).
Baseline (full available pool, n=43) at 300 reps: {'A': {'era_bias_pp': 0.5692413985880801, 'era_coverage_pct': np.float64(99.66666666666667), 'convergence_pct': 100.0}, 'B': {'era_bias_pp': -1.5763456814092747, 'era_coverage_pct': np.float64(97.66666666666667), 'convergence_pct': 100.0}, 'n': 43} -> PASS strict bar; margin-confirmed at 1000 reps: A 1.07pp / B -2.11pp -> PASS.
Winner (n=43): margin-confirmed A 1.07pp / B -2.11pp — same order of magnitude as the full available pool (n=43), so the reduced population is nearly equivalent under the validation criterion at ~100% of the est. single-GPU cost.

Reason taxonomy (per-model, assigned by single-model ablation on occupancy alone — never trait values). Kept models are 'edge-or-chain-forced (theta_M)', 'required: era-window coverage', 'required: structural identifiability (crossing)', 'required: structural identifiability (rank/VIF)', or 'required: statistical recoverability (D2 gate)'; dropped models are 'redundant in-cell replication (identifiability unchanged)'. Pre-measurement exclusions carry their own reason in the CSV.

Trace: the available pool (n=43) passes; the structural minimum n0 = 43 passes at search reps AND the 1000-rep confirmation margin — no extra models over n0 were needed.

| n | models | rank | vif | pass | bias A | cov% A | bias B | cov% B | bias A conf | bias B conf |
|---|---|---|---|---|---|---|---|---|---|---|
| 43 | 43 | True | True | True | 0.57 | 99.7 | -1.58 | 97.7 | 1.07 | -2.11 |
| 43 | 43 | True | True | True | 0.57 | 99.7 | -1.58 | 97.7 | 1.07 | -2.11 |

Robustness at 2000 reps (same fixed seeds): A 1.05pp / B -1.65pp, era-share CI coverage 98.6% / 98.6%, convergence 100.0% / 100.0%.
