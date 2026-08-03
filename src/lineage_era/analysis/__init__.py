"""analysis — Phase 2 statistical analysis layer (per the 2026-08-03 review).

Modules:
    trait.py         per-model trait assembly from fresh eval output
    metadata.py      occupancy x manifest design frame (incl. leak/chain flags)
    population.py    population construction, coverage gate, Kim reconciliation
    identifiability.py  first-class gate before the variance partition
    reml.py          CrossedREML engine + θ_P / θ_M model layer
    bootstrap.py     share CIs (delta + trait-error Monte-Carlo)
    error_similarity.py  secondary panel: pairwise error similarity + null ladder
    plots.py         figures (design heatmap, BLUPs, shares, era trend,
                     error-similarity heatmap/dendrogram/network/embedding)
    report.py        PHASE2_REPORT.md + summary/tables blocks

The top-level ``phase2_*.py`` / ``estimator.py`` names are kept as thin
re-export shims so the existing CLI and runbook continue to work unchanged.
"""
