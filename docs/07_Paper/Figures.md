# Figures

Files live in `docs/07_Paper/figs/`. All five figure slots in `manuscript.tex`
currently reference `fig_placeholder.png`; the final author-submitted artwork is
added later (replace `fig_placeholder.png` per figure or point each `\Figure`
block at its own file).

| # | Intended content (caption spec) | File referenced now | Status |
|---|---|---|---|
| F1 | Causal DAG: family → release date (mediator/confounder) → error trait; era → error trait; teacher leakage → era channel | `fig_placeholder.png` | Placeholder — author adds schematic |
| F2 | Phase 0 design heatmap: 6 families × 14 quarters occupancy (47 models) | `fig_placeholder.png` | Placeholder — author adds heatmap |
| F3 | G3 gate trace: era-share bias vs population size (47/21/22), confirmation values | `fig_placeholder.png` | Placeholder — author adds trace panel |
| F4 | Pairwise error-overlap panel (phi, null ladder) | `fig_placeholder.png` | Placeholder — pending eval pass |
| F5 | σ²_L / σ²_E / σ²_U shares with CI error bars (Phase 2) | `fig_placeholder.png` | Placeholder — pending eval pass |

## Rules

- No figure that contradicts a table; figures render table numbers.
- The era-convergence trend is never promoted to a standalone headline figure.
- Until final artwork is added, every figure slot shows the explicit
  `fig_placeholder.png` box; no placeholder is ever shown as a result.
- Audit integrity: the template's `fig1.png` (magnetization sample) is never used.
