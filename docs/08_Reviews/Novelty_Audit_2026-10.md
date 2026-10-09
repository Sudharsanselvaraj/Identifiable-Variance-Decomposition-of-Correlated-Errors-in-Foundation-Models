# Novelty audit — 2026-10-09

Scope: each claim the manuscript makes, checked against the literature through
October 2026 (arXiv, ICML/NeurIPS/ICLR/EMNLP proceedings, Hugging Face). Every
paper below was opened and its claim checked against its own text; search-engine
summaries were not relied on. Verdicts: **Novel** (no prior work found),
**Partly anticipated** (the idea exists, our version differs in a stated way),
**Anticipated** (prior work makes the claim).

## Verdicts

| # | Claim | Verdict | Closest prior work | What is ours |
|---|---|---|---|---|
| C1 | Sharing a declared lineage root is associated with choosing the same wrong answer (+13.3 points) | **Partly anticipated** | Kim et al. 2025 (shared provider / base architecture predict agreement); Bugaud 2026 (architectural families, VLMs); Choi et al. 2026 (truthfulness scores preserved in lineages) | Lineage resolved per model from declared ancestry to a root checkpoint; item-level outcome; 977 validated models; root-level inference. No prior study measures error agreement between fine-tunes of a shared checkpoint. |
| C2 | Release proximity shows no association of stable sign net of accuracy; bounded to about 1 point | **Novel as a test** | Kim et al. include undefined per-model "generation" covariates (positive, about +0.003) and interpret accuracy effects as convergence; Hossain et al. 2026 find error overlap tracks pretraining recency more than lineage (4 base models, "suggestive") | First direct test of release *proximity* between two models, jointly with lineage, under two timing measures, with equivalence bounds. Does not contradict Hossain et al.: their models are separately pretrained bases, a case our design cannot test. |
| C3 | Lineage and release timing tested jointly | **Novel** | None found | — |
| C4 | Dose-response: closer relatives agree more (18.5 / 13.6 / 11.5 points by tree distance) | **Novel** | Laufer et al. 2025 measure trait inheritance along trees but for metadata only; Tamura et al. 2025 use lineage to predict performance, not errors | Most distinctive finding. |
| C5 | Error agreement reveals lineage (AUC 0.95) | **Anticipated** | Nikolić et al. (NeurIPS 2025): derivation detected from output similarity, 90–95% precision on 600+ models; PhyloLM; LLM DNA (ICLR 2026); TokenPrint | Only the strength of the signal in benchmark *error* agreement. Reframed in the manuscript as corroboration. |
| C6 | Leaderboard data quality: duplicate entries, degenerate models | **Partly anticipated** | Paquin & Jain 2026: the leaderboard population "reduces to 869 distinct checkpoints" | Specific consequence for pairwise analyses (duplicates inflate same-root agreement; constant-answer models inflate different-root agreement), and the degenerate-model finding. Minor contribution. |
| C7 | Dyadic / root-level inference for pairwise LLM error regressions | **Novel in this literature** (standard in statistics) | Kim et al. describe no correction for dependence between pairs sharing a model (last 17% of their page could not be read) | Methodological improvement, not a statistical innovation. |
| C8 | Heterogeneity: present in every large root and all 57 MMLU subjects | **Novel detail** | None found | Supports C1. |

## Counterevidence that must be addressed

1. **Li & Hai 2026** (arXiv 2607.23931): across 20 instruction-tuned models from 10
   families on binary screening tasks, same-family membership is not associated with
   bad-state error dependence after controlling capability (coefficient −0.06, 95% CI
   −0.20 to 0.06; raw same-family 0.48 vs cross-family 0.60).
   *Reconciliation:* their families are separately pretrained siblings (e.g. Qwen2.5 at
   different sizes); our related pairs share a checkpoint. The two results together
   suggest shared weights, not a shared brand, carry shared errors. This is a reading,
   not something either study tests.
2. **Hossain et al. 2026** (arXiv 2606.20959): for four base models, overlap in
   parametric temporal-conflict errors tracks pretraining recency more than lineage
   (authors: "suggestive rather than conclusive"). Consistent with our stated
   limitation that pretraining era is nested in lineage in our population.

## Corrections made to the manuscript

- Kim et al.: "do not test this over release time" replaced by an accurate
  description (per-model generation covariates; proximity and lineage not separated;
  no described correction for pair dependence). Prior-work table updated.
- Lineage detection: now framed as corroborating provenance testing (Nikolić et
  al.), PhyloLM and LLM DNA.
- Related work: Li & Hai and Hossain et al. cited and reconciled; Choi et al.,
  Nikolić et al. and Tieman & Markou added.
- Data quality: Paquin & Jain credited for first noting leaderboard redundancy.

## Overall assessment

The contribution is a **focused empirical one**. The general idea that related
models make similar mistakes is anticipated. What is new: per-model declared
lineage tested jointly with release proximity; the dose-response; the
heterogeneity evidence; and the bounded timing null. Lineage detection from
agreement is not new and should not be sold as a contribution. Relative to the
nearest work (Kim et al. 2025), the delta is real but narrow. For a selective venue,
the missing piece remains a direct ensemble test (does choosing across lineages
improve voting at matched accuracy?).

## Sources checked

- Kim, Garg, Peng, Garg — Correlated errors in large language models (ICML 2025), arXiv 2506.07962
- Nikolić, Baluta, Saxena — Model provenance testing for LLMs (NeurIPS 2025), arXiv 2502.00706
- Li, Hai — State-dependent error correlations shape voting thresholds in committees of AI agents, arXiv 2607.23931
- Hossain et al. — Right knowledge, wrong answer: parametric temporal conflict, arXiv 2606.20959
- Paquin, Jain — What does MMLU actually measure?, arXiv 2609.09372
- Choi et al. — The truth stays in the family (ICML 2026), arXiv 2606.15821
- Tieman, Markou — Inferred generative-process diversity predicts correlated failure, arXiv 2609.03422
- Bugaud — Hidden clones (VLM ensembles), arXiv 2603.17111
- Laufer, Oderinwale, Kleinberg — Anatomy of a machine learning ecosystem, arXiv 2508.06811
- Tamura et al. — Can a crow hatch a falcon?, arXiv 2504.19811
- Wu et al. — LLM DNA (ICLR 2026), arXiv 2509.24496
- Hu et al. — Exploring model kinship for merging LLMs (Findings of EMNLP 2025), arXiv 2410.12613
- Kim, D. — Are diversity metrics measuring diversity?, arXiv 2607.20768
- Begin et al. — Preference optimization drives monoculture in LLM prediction markets, arXiv 2606.26583 (abstract only; not cited)
