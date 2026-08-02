# Literature Map

All entries independently verified (arXiv record / proceedings). Status of each paper:
included in proposal §5 differentiation table. Threat level = how likely a reviewer is to
argue this paper already covers our ground.

## Entry format

```
Paper / Venue
Contribution
Math / Object
Dataset
Limitation
Future work they name
Competition with us
Threat level
```

---

## 1. Kim et al., "Correlated Errors in Large Language Models"

- **Paper:** Kim, Garg, Peng, Garg. arXiv:2506.07962. ICML 2025 (PMLR 267:30038–30066).
- **Contribution:** Documents cross-sectional agreement: >350 open and hosted models, two
  leaderboards (HELM, HuggingFace) + resume-screening task; ~60% agreement when both
  models err on one leaderboard; shared architecture/provider factors; agreement persists
  across distinct architectures/providers at higher accuracy.
- **Object:** Agreement rates / correlation; not a variance decomposition.
- **Limitation:** Explicitly cross-sectional; causality and temporality left open by the
  authors.
- **Future work they name:** Causal/temporal attribution (left open).
- **Competition:** Closest empirical neighbor — same phenomenon, different question.
- **Threat:** High (a reviewer will cite it first). Neutralized by object difference
  (agreement rate vs. variance partition) + their own "causality open" statement.

## 2. PhyloLM — Yax, Oudeyer, Palminteri

- **Paper:** arXiv:2404.04671. ICLR 2025.
- **Contribution:** Phylogenetic (Nei-distance) trees from output similarity across open
  and closed models; tree distance predicts benchmark performance (MMLU, ARC, and others).
- **Object:** Ancestry reconstruction + score prediction; no error-trait variance
  decomposition.
- **Limitation:** Reconstructs ancestry from outputs rather than taking the release record
  as given; predicts aggregate scores, not error covariance.
- **Future work they name:** Broader lineage analysis (no variance decomposition).
- **Competition:** Low. Complementary direction.
- **Threat:** Medium (the "lineage" word invites confusion). Neutralized by input/output
  difference: we take the documented release record as given.

## 3. Total Evaluation Error (TEE) — Messing

- **Paper:** arXiv:2604.11581.
- **Contribution:** G-theory variance decomposition + D-study of LLM evaluation pipelines;
  facets incl. judge model, temperature, prompt; item×judge interaction; under-coverage of
  conventional CIs.
- **Object:** Measurement-pipeline variance, not model trait variance.
- **Limitation:** Grouping factors are properties of the evaluation, not of the models.
- **Future work they name:** Pipeline design / D-studies.
- **Competition:** Same estimator class (crossed random effects / REML), different object.
  Compatible, could be composed with our model-level decomposition.
- **Threat:** Medium (same estimator class invites "already done"). Neutralized by
  different grouping factors and different target of inference.

## 4. Tracing the Roots — Li et al.

- **Paper:** arXiv:2604.10480. ACL 2026 (2026.acl-long.435, pp. 9606–9625).
- **Contribution:** Multi-agent reconstruction of dataset lineage in post-training;
  83 seed → 430 datasets, 971 inheritance edges; contamination propagates along lineage
  paths.
- **Object:** Dataset ancestry graphs.
- **Limitation:** Not model error variance; dataset lineage is a channel into our era
  component (shared training data).
- **Future work they name:** Lineage-aware data curation.
- **Competition:** Low.
- **Threat:** Low.

## 5. The Subjectivity of Monoculture — Jo, Garg, Raghavan

- **Paper:** arXiv:2602.24086.
- **Contribution:** Monoculture estimates are null-model-dependent and vary with the
  population of models/items; increasingly expressive nulls can absorb model correlations.
- **Object:** Meta-analysis of monoculture measurement.
- **Limitation:** Does not estimate a variance partition; argues an estimand must be
  defined independently of a baseline.
- **Future work they name:** Better measurement of shared failure.
- **Competition:** Low (informs our choice to model shared random effects directly rather
  than rely on an independence null).
- **Threat:** Low.

## 6. Algorithmic Monoculture and its Critics — Hedden & Raghavan

- **Paper:** arXiv:2604.06047.
- **Contribution:** Evaluates objections to monoculture (systemic exclusion,
  gaming/agency, information aggregation/exploration); concludes monoculture is less
  problematic than critics claim; ensemble monoculture can outperform.
- **Object:** Welfare/critique of monoculture-as-harm.
- **Limitation:** Treats correlated error as a given input; never estimates it.
- **Future work they name:** Empirical measurement of convergence.
- **Competition:** Complementary — our partition is an input to their debate.
- **Threat:** Low.

## 7. Preference Leakage — Li et al.

- **Paper:** arXiv:2502.01534. **ICLR 2026** (venue corrected 2026-08-02).
- **Contribution:** LLM-as-judge bias toward generators related to the judge (same model,
  inheritance, same family); preference-leakage score; subtler than egocentric/length bias.
- **Object:** Instrument-level measurement bias.
- **Limitation:** Downstream consequence of correlated error, not its decomposition.
- **Future work they name:** Judge-family contamination studies.
- **Competition:** Low (instrument-level; ours is trait-level).
- **Threat:** Low.

## 8. Fu et al. (terminology holder, not related work)

- **Paper:** arXiv:2604.20817.
- **Contribution:** Convergence in learned Fourier representations of numbers.
- **Why listed:** Claims the term "convergent evolution" for a different phenomenon. We
  avoid the term entirely.
- **Threat:** Low (term-collision only).
