# Citation Graph

Directed edges: influence / dependence between works, from our perspective. Arrow = "built on / responds to / presupposes". This is our working model of how the literature relates, for positioning and rebuttal prep — not a claim about authors' actual reading history.

```
Algorithmic Monoculture and its Critics (2026)
        ↑   evaluates objections to
        |
The Subjectivity of Monoculture (2026)
        ↑   challenges the null model in
        |
Kim et al., Correlated Errors (ICML 2025)  ──────►  THIS PROPOSAL (partition + identifiability gate)
        ↑        ↑
        |        └── TEE (2026)  (same estimator class; pipeline facets — composed later)
        |
PhyloLM (ICLR 2025)  (lineage-as-similarity; complementary, no variance decomposition)

Preference Leakage (ICLR 2026)  (instrument-level consequence; downstream of correlated error)
Tracing the Roots (ACL 2026)    (dataset lineage; feeds our era channel)
```

## Reading

- **Kim et al.** is the empirical starting point: it documents the phenomenon and
  explicitly leaves causality/temporality open. Our θ_P/θ_M structure is the "causality"
  half they defer.
- **PhyloLM** is the nearest "lineage" paper; the differentiation is input/output
  (reconstruct vs. take-as-given).
- **TEE** shares the estimator class; the differentiation is grouping factors (pipeline
  facets vs. model traits). Composable: pipeline facets and model traits can be decomposed
  in the same framework.
- **Subjectivity** warns against baseline-dependent inference; we respond by modeling
  shared random effects directly (no independence null).
- **Critics** treats correlated error as given; we supply the estimate that decides whether
  "not a problem" survives.
- **Preference Leakage** is a consequence we cite for the stakes, not a rival.
- **Tracing the Roots** is a data-channel reference (shared training data ⇒ era component).

## Gaps this graph exposes (see Related_Work_Gaps.md)

1. No node partitions error variance by lineage vs. era.
2. No node treats population identifiability (crossed vs. nested) as a gate.
3. No node validates the estimator on the actual (unbalanced, sparse) occupancy before
   real-data claims.
