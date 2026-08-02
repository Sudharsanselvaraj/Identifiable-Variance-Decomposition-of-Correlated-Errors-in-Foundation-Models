# 01 Research Questions

Source: `proposal.md` §4. All questions are defined **on the connected subset only** —
where lineage and era are separable. Where the design is nested, the partition is
undefined by construction (a property of the design, not a data gap).

## RQ0 — Main question (gated)

Can the observed error-correlation structure across public open-weight LMs be separated
into a lineage component and an era component — i.e., is the partition
V_lineage + V_era + V_unique estimable and non-degenerate on the connected subset?

Positive answer requires both: (a) the estimator survives Phase 1 simulation, and
(b) on real data, V_lineage|era and V_era are each estimated with non-degenerate
intervals.

## Sub-questions

| RQ | Question | Operates on | Phase | Refutation condition |
|---|---|---|---|---|
| RQ1 | Does the crossed random-effects estimator recover the true partition under known ground truth, in both a balanced-crossed (D1) and a realistic-occupancy (D2) regime? | Simulated data | 1 | Bias or collapse under D2 → estimator unfit; the real-data claim never proceeds |
| RQ2 | Under a mis-specified generative model (nested design; continuous liability thresholded to binary response), does the estimator fail *detectably* rather than silently? | Simulated data | 1 | Silent bias under mis-specification → stop program; fix or drop the instrument |
| RQ3 | On the connected subset, what share of error covariance is attributable to lineage *conditional on era*? (Primary, observational estimand.) | Connected subset of the Phase 0 population | 2 | V_lineage\|era indistinguishable from 0 → lineage refuted as a separable driver on the connected population |
| RQ4 | Holding era exactly fixed — co-released family cohorts and staggered repeated fine-tunes only — what is the structural contribution of lineage? (Secondary, mechanistic estimand.) | Co-released cohorts + staggered fine-tune chains | 2 | Reported separately, never merged into RQ3. Nonzero here with near-zero RQ3 → RQ3 is confounded by era; zero here → mechanistic lineage refuted too |
| RQ5 | After lineage adjustment, does the era component show a convergence trend across release quarters? | Connected subset | 2 | Flat trend → era-convergence refuted (register item 2; reported as a table entry, not a standalone result) |
| RQ6 | Conditional on the Phase 2 partition, is cross-family diversification a credible mitigation for correlated failure, or is era the binding constraint? | Decision layer on Phase 2 output | 2 | V_era dominates → diversification-as-remedy refuted for the connected population (register item 1) |

## Two-estimand rule (non-negotiable)

RQ3 and RQ4 answer different questions and are never merged. Release year is both a
mediator and a confounder on the lineage→error path, so the observational primary (RQ3)
adjusts for era grouping but cannot hold era fixed; the mechanistic secondary (RQ4) is the
only estimand that isolates lineage with era held fixed, and it is available only on the
small co-released and staggered-fine-tune subsets (5 verified cross-generation
`base_model` edges from Phase 0).

## Scope exclusions

None of RQ0–RQ6 is a phylogeny-reconstruction exercise (PhyloLM), a
pipeline-measurement-error decomposition (TEE), a dataset-lineage reconstruction
(Tracing the Roots), or a welfare evaluation of monoculture (monoculture-critics
literature). See `docs/01_Literature/Related_Work_Gaps.md`.

## Deferred / Phase-3-only questions (NOT part of the base program)

These belong to the gated Phase 3 analogy layer and are listed here only so they are
explicitly *not* base-program claims:

- Can variance components predict intervention effectiveness (diversification response)?
- Does the error structure obey population-level statistical dynamics (breeder's-equation
  test)?
- Does benchmark selection produce measurable selection pressure?

These become active only after Phase 2 survives, and only in clearly-labeled analogy
language.
