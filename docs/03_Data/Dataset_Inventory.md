# Dataset Inventory

**STATUS: placeholder — item-level benchmark procurement is pending.** Procurement
decision is settled at the Phase 1 approval step. Until then, this file lists
requirements and risks, not assets.

## Requirements for the Phase 2 item set

- Item-level response records (per-model, per-item correctness) for the connected subset
  models — i.e., a common or comparable item set over the 2023Q1–2026Q2 window.
- Public evaluation suites that publish item-level responses.
- Sufficient item count for per-model trait precision (identifiability condition 4:
  "error traits measured precisely enough"; CIs reported with every estimate).

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
