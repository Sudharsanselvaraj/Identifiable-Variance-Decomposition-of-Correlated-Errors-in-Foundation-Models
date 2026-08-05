# Figures

Kept here so the paper's visual claims are pre-registered, not invented post-hoc.
Files live in `docs/07_Paper/figs/`; all are generated (see the figure scripts in
`src/lineage_era/`) and referenced by `manuscript.tex`.

| # | File | Content | Status |
|---|---|---|---|
| F1 | `fig_dag.png` | Causal DAG: family → release date (mediator/confounder) → error trait; era → error trait; teacher leakage → era channel | Real schematic (documented SCM) |
| F2 | `fig_design.png` | Phase 0 design heatmap: 6 families × 14 quarters occupancy (47 models) | Real (from `occupancy.design_counts`) |
| F3 | `fig_partition.png` | σ²_L / σ²_E / σ²_U shares with CI error bars (Phase 2) | Labeled pending placeholder → `variance_shares.pdf` after eval pass |
| F4 | `fig_g3_trace.png` | G3 gate trace: era-share bias vs population size (47/21/22), confirmation values | Real (from committed `g3_report.md` trace) |
| F5 | `fig_similarity.png` | Pairwise error-overlap panel (phi, null ladder) | Labeled pending placeholder → error-overlap outputs after eval pass |

## Rules

- No figure that contradicts a table; figures render table numbers.
- The era-convergence trend is never promoted to a standalone headline figure.
- Pending figures are explicitly labeled "pending the eval pass" in both the file and
  the caption; no placeholder is ever shown as a result.
- Audit integrity: the template's `fig1.png` (magnetization sample) is never used.
