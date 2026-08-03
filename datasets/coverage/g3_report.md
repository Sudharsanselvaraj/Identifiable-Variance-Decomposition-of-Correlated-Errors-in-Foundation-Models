# G3 — Minimum Valid Population (2026-08-03, pre-registered)

Strict bar (Phase 1 D2 gate, mean over converged reps/scenario, seeds {'A': 101, 'B': 202}): |era share bias| <= 5.0pp AND era-share CI coverage >= 90.0%; convergence >= 90.0%.

Two-stage decision (heavy-tailed per-rep bias, register A21): candidates that clear the bar at 300 reps must ALSO clear it with >= 1.0pp margin (|bias| <= 4.0pp) at a high-precision 1000-rep confirmation before acceptance — knife-edge designs sitting on the bar are rejected.

Structural minimum n0 = 21 (identifiable: full rank + VIF<=10).
**Minimum VALID population = 22** of 47 (reduced).

Baseline (full 47) at 300 reps: {'A': {'era_bias_pp': 0.34250203729639106, 'era_coverage_pct': 98.66666666666667, 'convergence_pct': 100.0}, 'B': {'era_bias_pp': -3.5203827353819106, 'era_coverage_pct': 96.33333333333334, 'convergence_pct': 100.0}, 'n': 47} -> PASS strict bar

| n | models | rank | vif | pass | bias A | cov% A | bias B | cov% B | bias A conf | bias B conf |
|---|---|---|---|---|---|---|---|---|---|---|
| 21 | 21 | True | True | False | 1.82 | 95.7 | -4.94 | 98.0 | 2.06 | -5.09 |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | True | False | 1.91 | 95.7 | -4.87 | 98.7 | 1.69 | -4.98 |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | True | False | 4.34 | 96.3 | -5.24 | 98.3 | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | False | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 21 | 21 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | True | True | False | 2.54 | 96.7 | -3.27 | 99.7 | 3.08 | -4.13 |
| 22 | 22 | False | False | False | - | - | - | - | - | - |
| 22 | 22 | True | False | False | - | - | - | - | - | - |
| 22 | 22 | True | True | True | 2.44 | 98.0 | -0.78 | 99.0 | 2.19 | -2.36 |
