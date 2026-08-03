# Paper Outline

Source: `proposal.md`. The 14-section proposal is the master outline; this file is the
paper-facing version.

| # | Section | Content source | Status |
|---|---|---|---|
| 1 | Title + Plain-Language Summary | Title fixed; summary in proposal §1 | Drafted |
| 2 | Abstract | proposal §2 (244 words, 200–250 budget) | Drafted |
| 3 | Motivation & Problem Statement | proposal §3 | Drafted |
| 4 | Precise Research Questions | proposal §4 | Drafted |
| 5 | Related Work + Differentiation | proposal §5 (verified ledger) | Drafted |
| 6 | Formal Estimand & Identifiability | proposal §6 | Drafted |
| 7 | Methodology per Phase | proposal §7 | Drafted |
| 8 | Disconfirmability Register | proposal §8 | Drafted |
| 9 | Feasibility & Data | proposal §9 | Drafted |
| 10 | Timeline | proposal §10 | Drafted |
| 11 | Risk Register | proposal §11 | Drafted |
| 12 | Venue & Positioning | proposal §12 | Drafted |
| 13 | Significance / Expected Contribution | proposal §13 | Drafted |
| 14 | Appendix — Phase 0 Log (verbatim) | proposal §14 | Drafted |

## Results/analysis section order (reviewer restructure)

Decomposition stays the centerpiece; the error-similarity panel is the supporting
observational layer. Headline framing: *observed* overlap → *why* it exists →
*identifiability* → *variance decomposition* → *implications*.

| § | Section | Content | Primary output |
|---|---|---|---|
| 5 | Observed Population | population definition, Phase 0 occupancy, connected subset, coverage gate | design heatmap |
| 6 | Error Similarity (secondary panel) | observed pairwise error overlap between models; chance-corrected measure (pre-registered rule locks phi); null ladder (observed → matched-accuracy → item-difficulty → independence) | error heatmap, network, embedding |
| 7 | Identifiability | crossed-design identifiability gate, rank/VIF, D3 must-fail control, sparse-cell caveats | rank/VIF table |
| 8 | Variance Decomposition | LPM-REML partition σ²_L / σ²_E / σ²_U with CIs; era-convergence trend; sensitivity blocks | partition table + variance-share plots |
| 9 | Intervention Implications | what the partition says about lineage vs. era as drivers of shared model error; θ_M scoped structural claims; scoped to the connected subset | discussion |

## Figure/table plan (see `Figures.md`, `Tables.md`)

- Figures: causal DAG (family/era/release-year), partition plot, Phase 0 density
  heatmap, error-similarity heatmap + dendrogram + top-3 network + PCA/t-SNE
  embeddings (secondary panel, `error_heatmap.pdf` / `error_network.pdf` /
  `error_dendrogram.pdf` / `error_embedding_*.pdf`).
- Tables: differentiation table, Phase 0 contingency table, register, partition
  table, error-similarity summary (`error_similarity.csv`) + edge stability +
  community comparison (panel).

## Packaging checklist (final)

- Every novelty claim mapped to its differentiation-table entry.
- Venue CFP checked at submission time (rule: no stale venue claims).
- References compiled from the verified ledger only.
