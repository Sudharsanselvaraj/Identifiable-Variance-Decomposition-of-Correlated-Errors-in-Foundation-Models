# Identifiability

Probably the most important document. Source: `proposal.md` §6.4. Everything here
rests on the crossed-vs-nested question.

## Core claim

The partition (σ²_L, σ²_E, σ²_U) is estimable **iff** the design is crossed: families
spanning multiple eras AND multiple families per era. If the design is nested, lineage and
era are collinear and the partition is unknowable from observational data — regardless of
how good the estimator is.

## Necessary conditions (all verified, Phase 0)

| Condition | Status | Evidence |
|---|---|---|
| Crossed design: ≥2 families in ≥2 quarters, non-empty cells in both directions | VERIFIED | 6 families × 14 quarters (2023Q1–2026Q2); 11/14 quarters ≥2 independent families; no family confined to a single era |
| Not nested: within-family variation over time AND within-era variation across families | VERIFIED | Phase 0 row spans and column densities |
| Estimator validity under the actual (unbalanced, sparse) occupancy | TO BE SHOWN | Phase 1, D2 realistic-occupancy regime; D3 nested must fail |
| Error traits measured precisely enough | TO BE SHOWN | Item-set size; bootstrap/parametric CIs reported with every estimate |

## Sufficient conditions

Given the crossed design, the variance components are identified by standard
variance-components theory (REML/G-theory). The program's added requirement is
**simulation-first**: identifiability in theory is not enough; the estimator must recover
known ground truth under the *actual* occupancy (D2) and must fail detectably when the
design is nested (D3). Silent mis-specification bias = program stopped (RQ2).

## Counterexamples / failure modes

| Failure mode | Detection | Consequence |
|---|---|---|
| Nested subpopulation (family confined to one era) | Phase 1 D3 must reproduce aliasing | If D3 estimates "successfully," mis-specification is silent ⇒ stop |
| Balanced-looking but collinear occupancy | D2 with Phase 0 occupancy | Bias/collapse under D2 ⇒ estimator unfit, no real-data claim |
| Lineage × era interaction present in truth | Not identifiable from sparse cells | Excluded from estimands; documented, not estimated |
| Teacher leakage breaking family independence | Not directly detectable from the design | Assigned to σ²_E (era channel), disclosed as inflation direction |
| Contamination inflating era shared errors | Not directly detectable | Disclosed; item-set mitigation where feasible |

## Assumptions that identifiability rests on

1. Linearity/additivity on the liability scale.
2. Random effects independent of regressors (α, β, u ⊥ δ and mutually).
3. Crossed design (verified).
4. Measurement of model error traits has finite precision — handled by CIs, not ignored.

## Proof sketches (informal)

1. **Crossed ⇒ identified:** variance components of a two-way crossed design are
   identifiable from the ANOVA/REML likelihood under standard conditions; the family and
   era factors are linearly independent as grouping factors. This is textbook
   variance-components theory (Searle, Harville); Phase 1 confirms numerically on D1/D2.
2. **Nested ⇒ aliased:** if family is nested within era (or vice versa), the two grouping
   structures are coarser/finer versions of one another; the likelihood cannot separate
   σ²_L from σ²_E. Phase 1 D3 must demonstrate the aliasing empirically (flat/derivative
   likelihood or boundary estimates).

## Open item (do not drop)

- `base_model` sparsity means true cross-generation lineage is largely undocumented
  (5 verified edges). This constrains θ_M and the Phase 3 analogies, not the identifiability
  of the primary design (which rests on family × quarter, not on documented edges).
