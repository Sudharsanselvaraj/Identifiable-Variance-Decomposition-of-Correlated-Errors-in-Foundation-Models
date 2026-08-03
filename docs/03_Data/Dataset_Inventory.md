# Dataset Inventory

**STATUS: path decided (2026-08-03); availability check pending.** Phase 1 F4
settled the procurement target: **item-level response logs aggregated into a
continuous per-model trait** (accuracy proportion or IRT-style ability
estimate). Raw item-by-item binary responses are NOT modeled directly (era
variance is underpowered at the 47-model occupancy on binary outcomes — Phase 1
F4). Primary candidate source: Kim et al. (arXiv:2506.07962, ICML 2025) public
item-level data, aggregated per model. Inventory table below fills in once
availability/license is confirmed.

## Requirements for the Phase 2 item set

- Item-level response records (per-model, per-item correctness) for the connected subset
  models — i.e., a common or comparable item set over the 2023Q1–2026Q2 window.
- **Modeling target: the aggregated continuous per-model score** (mean accuracy
  over the common item set, or an IRT 2PL/3PL person ability). The per-item
  Bernoulli layer is a data source, not the fitted outcome.
- Sufficient item count for per-model trait precision (identifiability condition 4:
  "error traits measured precisely enough"; CIs reported with every estimate).
  With thin item counts, prefer IRT ability over raw proportion and report item
  counts alongside.

## Aggregation pipeline (contract for Phase 2)

```
item-level response logs  --(common item set, per-model)-->  per-model score
  y_{m,i} in {0,1}                                            t_m = mean_i y_{m,i}
                                                                (or IRT person ability, s.e. via item information)
per-model score  --(LPM-REML crossed fit)-->  theta_P: s2_L, s2_E, s2_U + share CIs
```

- σ²_U is measured-with-error inclusive: variance of the trait estimator lands
  in the unique component; reported with the partition.
- Kim et al. (2506.07962) already publishes item-level results for 350+ models;
  aggregation per model is less work than a per-item binary fit, and the design
  stays identical to the validated D2 continuous regime.

## Known risks to this data (all inflate σ²_E or blur lineage)

| Risk | Direction | Mitigation |
|---|---|---|
| Benchmark contamination (models trained on leaderboard items) | Inflates era share | Exclude known-contaminated items where feasible; disclose |
| Response logs unavailable for older models | Coverage loss | Fallback: run a fresh evaluation pass on the connected subset |
| Item sets differ across models | Non-comparable traits | Use the intersection/comparable set; report overlap |

## Inventory table (to fill at procurement)

| Benchmark | Version | License | Questions | Split | Known contamination | Response logs available | Models covered |
|---|---|---|---|---|---|---|---|
| TBD | | | | | | | |

## Fallback plan

If no public item-level logs cover the connected subset, run a fresh evaluation pass on
the connected subset models with a fixed item set (cost/budget decision recorded in the
Research Decision Log when made).
