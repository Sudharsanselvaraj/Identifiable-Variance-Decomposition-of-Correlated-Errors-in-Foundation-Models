# Ablations

Planned and completed ablation-style analyses. Planned ones are listed now so they are
pre-registered rather than invented after results.

## Planned

| Ablation | Question | Phase |
|---|---|---|
| L×E interaction in/out | Does including the interaction (though unidentifiable) change the primary components? Expected: non-identifiable; document. | 1 |
| LPM vs. GLMM path | Does estimator choice change the partition materially on simulated data? | 1 |
| Occupancy sensitivity | Does dropping the densest cells (2024Q2–2025Q2) move the partition? | 2 |
| Teacher-leakage exclusion | Exclude Phi/Gemma leakage-affected models; does σ²_E drop? (Directional check.) | 2 |
| Item-set robustness | Intersection vs. full item set; do shares move within CI? | 2 |

## Completed

_(None yet.)_

## Rules

- Every ablation is logged with its verdict, even (especially) uninformative ones.
- Ablations never upgrade a null to a finding; they only test robustness of the partition.
