# 00_Project Vision

## Long-term vision

Understand the statistical structure of correlated failure across public language
models well enough to make *informed* mitigation decisions — chiefly
diversification-as-mitigation — on the basis of a variance partition, not intuition.

## Why this research exists

Public LLMs fail together. The correlation is measured (Kim et al., ICML 2025: ~60%
agreement when both models err on one leaderboard, across 350+ models), but *why* — shared
ancestry vs. shared release era — is untested. The two are entangled, so the question is
only answerable on the connected subset where they can be told apart.

## Scientific motivation

- The phenomenon (correlated error) is documented; the causal/structural attribution is
  open. Kim et al. explicitly leave causality and temporality open.
- The decomposition object (V_lineage + V_era + V_unique) does not exist in the literature.
- The design question — crossed vs. nested — decides identifiability before any analysis,
  and has not been treated as a gate by any prior work.

## Industrial motivation

- Ensemble practice assumes independent error; the assumption is unquantified.
- LLM-as-judge and hiring/ranking deployments inherit correlated blind spots
  (Preference Leakage documents the judge-side consequence).
- Diversification strategy is currently decided without an estimate of whether lineage or
  era drives shared errors.

## Research philosophy

- Identifiability before results. Any measurement is run through the crossed-vs-nested
  question before it becomes a plannable deliverable.
- Simulation before real data. No real-data claim precedes Phase 1 validation.
- Brutal honesty over encouragement. Direct verdicts (GO / GO WITH CHANGES / NO GO).
- Every novelty claim keeps its differentiation-table entry; no claim without a closest
  paper and a difference.
- Negative results are kept (see `docs/06_Results/Negative_Results.md`).

## Success criteria

1. Phase 1: the crossed random-effects estimator recovers known ground truth under
   realistic occupancy (D2), and fails detectably when the design is nested (D3).
2. Phase 2: a partition σ²_L / σ²_E / σ²_U with intervals on the connected subset, and the
   mechanistic estimand reported separately.
3. A clean answer to the diversification fork: V_lineage dominates (diversify families) or
   V_era dominates (diversify data/technique).
4. A paper whose novelty claims survive a Kill Test (see `docs/08_Reviews/Kill_Test.md`).

## Framing must-holds (non-negotiable)

- Lead with the decomposition instrument and the identifiability gate — never
  "quantitative genetics," never "error inheritance" in a title, abstract, or lead
  paragraph.
- Never use the term "convergent evolution" (claimed by Fu et al., arXiv:2604.20817, for a
  different phenomenon).
- Quantitative-genetics language (heritability, selection differential, breeder's equation)
  is Phase 3 scaffolding only, clearly labeled as analogy, gated behind Phase 2 surviving.
