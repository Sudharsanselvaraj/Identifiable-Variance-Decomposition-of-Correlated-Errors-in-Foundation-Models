# Related Work Gaps

For every paper: limitation, future work, open assumptions, hidden assumptions. These are
the cells our differentiation rests on (see `docs/00_Project/Novelty_Claims.md`).

## Consolidated gap statement (proposal §5.3)

No verified work estimates V_lineage + V_era + V_unique for model error traits, on the
provably connected subset, with the estimator's validity established in simulation first.
Every prior work either (a) documents correlation without partitioning it, (b) decomposes
variance of the wrong object (pipeline facets, dataset lineage), or (c) treats correlated
error as a given input to a welfare argument.

---

## Kim et al. (ICML 2025)

- **Limitation:** Cross-sectional; no temporal/causal structure; agreement rates, not
  variance components.
- **Future work (theirs):** Causal and temporal attribution — left open.
- **Open assumptions:** That shared architecture/provider "explains" correlation without a
  decomposition; that independence is well-defined for downstream claims.
- **Hidden assumptions:** Models are exchangeable units; leaderboard items are
  representative; no contamination term.

## PhyloLM (ICLR 2025)

- **Limitation:** Reconstructs ancestry from output similarity; cannot distinguish shared
  environment (era) from shared lineage in the tree itself.
- **Future work (theirs):** Larger lineage analysis.
- **Open assumptions:** Output-similarity distance encodes lineage rather than era.
- **Hidden assumptions:** Nei-distance treats all output dimensions as neutral; no
  release-date structure.

## TEE (2026)

- **Limitation:** Decomposes pipeline facets (judge, temperature, prompt), not model
  traits; item×judge interaction is measurement structure, not model ancestry.
- **Future work (theirs):** Pipeline design / D-studies.
- **Open assumptions:** Model traits are fixed given the pipeline; no model-population
  structure.
- **Hidden assumptions:** That pipeline variance and model variance are separable in the
  way a single mixed model can capture; our program treats model variance as the target,
  TEE treats it as nuisance.

## Tracing the Roots (ACL 2026)

- **Limitation:** Dataset lineage, not model trait variance.
- **Future work (theirs):** Lineage-aware data curation.
- **Open assumptions:** Dataset ancestry ⇒ model behavior correlation (untested).
- **Hidden assumptions:** Dataset lineage is a proxy for error covariance; no trait-level
  measurement.

## The Subjectivity of Monoculture (2026)

- **Limitation:** Shows monoculture estimates are null-model-dependent but does not offer a
  decomposition that avoids the null.
- **Future work (theirs):** Better measurement of shared failure.
- **Open assumptions:** That a null-model-free decomposition exists.
- **Hidden assumptions:** Item-difficulty null models are the only alternative to
  independence-null models.

## Algorithmic Monoculture and its Critics (2026)

- **Limitation:** Treats correlated error as given; welfare argument does not depend on the
  partition's size.
- **Future work (theirs):** Empirical measurement of convergence.
- **Open assumptions:** The distribution of error correlation across lineage/era is
  irrelevant to the policy conclusion.
- **Hidden assumptions:** Diversification across labs/families is a meaningful intervention
  — exactly what our RQ6 tests.

## Preference Leakage (ICLR 2026)

- **Limitation:** Instrument-level bias; does not measure model error traits.
- **Future work (theirs):** Judge-family contamination studies.
- **Open assumptions:** Judge relatedness classes (same model / inheritance / family) are
  exhaustive and correctly weighted.
- **Hidden assumptions:** The generator-side correlation structure is separable from the
  judge-side bias — a separability our program partially tests by partitioning model error.

## Fu et al. (2026)

- **Limitation:** Fourier-representation convergence; term collision with "convergent
  evolution" only.
- **Future work:** n/a.
- **Open assumptions:** n/a.
- **Hidden assumptions:** n/a.

---

## Program-level open gaps (ours, to be closed)

1. Item-level benchmark data procurement (Phase 2 dependency).
2. Parent–offspring edges beyond the 5 verified `base_model` edges (from technical
   reports/papers).
3. Contamination of benchmark items inflating the era channel.
