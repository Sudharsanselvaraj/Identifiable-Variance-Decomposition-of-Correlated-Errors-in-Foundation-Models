# G3 — Minimum Valid Population (2026-08-03, pre-registered)

> **Outcome-independent study design.** G3 never observes trait values during optimization. Its inputs are occupancy (family × quarter), the lineage graph (VERIFIED_EDGES endpoints, Mistral-Small chain), identifiability constraints, and cost. All recoverability checks use fixed-design DGP simulations — never real eval outputs, accuracies, or error-similarity results.

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

Structural minimum n0 = 21 (identifiable: full rank + VIF<=10).
**Minimum VALID population = 22** of 47 (reduced).

Baseline (full 47) at 300 reps: {'A': {'era_bias_pp': 0.34250203729639106, 'era_coverage_pct': 98.66666666666667, 'convergence_pct': 100.0}, 'B': {'era_bias_pp': -3.5203827353819106, 'era_coverage_pct': 96.33333333333334, 'convergence_pct': 100.0}, 'n': 47} -> PASS strict bar; margin-confirmed at 1000 reps: A 1.54pp / B -2.22pp -> PASS.
Winner (n=22): margin-confirmed A 2.19pp / B -2.36pp — same order of magnitude as the full 47, so the reduced population is nearly equivalent under the validation criterion at ~67% of the est. single-GPU cost.

Reason taxonomy (per-model, assigned by single-model ablation on occupancy alone — never trait values). Kept models are 'edge-or-chain-forced (theta_M)', 'required: era-window coverage', 'required: structural identifiability (crossing)', 'required: structural identifiability (rank/VIF)', or 'required: statistical recoverability (D2 gate)'; dropped models are 'redundant in-cell replication (identifiability unchanged)'. The CSV carries the per-model reason.

Trace: 47 passes, the structural minimum 21 fails the confirmation margin (knife-edge on the bar), 22 passes — the extra model over n0 is statistically necessary, not computationally convenient.

| n | models | rank | vif | pass | bias A | cov% A | bias B | cov% B | bias A conf | bias B conf |
|---|---|---|---|---|---|---|---|---|---|---|
| 47 | 47 | True | True | True | 0.34 | 98.7 | -3.52 | 96.3 | 1.54 | -2.22 |
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
