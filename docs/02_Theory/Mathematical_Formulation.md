# Mathematical Formulation

Formal statement of the estimand. This file contains equations and notation only — no
implementation, no data. Source: `proposal.md` §6.

## Variables

| Symbol | Meaning |
|---|---|
| `M` | Set of models in the connected subset (Phase 0 population) |
| `m` | A model, m ∈ M |
| `f(m)` | Family (lineage factor) of model m |
| `e(m)` | Release quarter (era factor) of model m |
| `I` | Item set (common or comparable benchmark items) |
| `i` | An item, i ∈ I |
| `y_mi` | Error indicator: 1 if model m answers item i incorrectly, else 0 |

## Random variables / latent structure (liability scale)

```
y*_mi = δ_i + α_{f(m)} + β_{e(m)} + u_m + r_mi,     y_mi = 1{y*_mi > 0}
```

| Term | Role | Distribution |
|---|---|---|
| `δ_i` | Item difficulty | Fixed effects (or random, alternative spec) |
| `α_f` | Lineage effect — shared by all members of family f | N(0, σ²_L) |
| `β_e` | Era effect — shared by all models released in quarter e | N(0, σ²_E) |
| `u_m` | Model-unique effect | N(0, σ²_U) |
| `r_mi` | Residual (threshold / liability error) | distribution per estimator path (LPM-REML vs. GLMM) |

## Assumptions (stated, not hidden)

1. **Crossed design:** the family × quarter design is crossed (Phase 0: verified,
   unbalanced/incomplete). This is what separates σ²_L, σ²_E, σ²_U.
2. **Linearity on liability scale:** effects combine additively on the latent scale.
   The continuous-liability → binary-threshold mis-specification is exactly what Phase 1
   tests.
3. **Random effects independent of regressors:** α, β, u independent of δ and of each
   other. Teacher leakage violates the independence of families; assigned to the era
   channel (inflates σ²_E), flagged, not silently absorbed.
4. **No lineage × era interaction estimated:** interaction not identified from the sparse
   cells; excluded from the estimands. Phase 1 documents the non-identifiability.

## The partition

On the liability scale, the model-level variance components are σ²_L, σ²_E, σ²_U,
normalized to a lineage share, era share, and model-unique share:

```
lineage share  = σ²_L / (σ²_L + σ²_E + σ²_U)
era share      = σ²_E / (σ²_L + σ²_E + σ²_U)
model-unique   = σ²_U / (σ²_L + σ²_E + σ²_U)
```

## Primary estimand (observational)

```
θ_P = σ²_L / (σ²_L + σ²_E + σ²_U)      [with β_e in the model]
```

- Lineage variance **conditional on release-era grouping**. A conditional variance share,
  not a causal direct effect.
- Because release year is a *mediator* on the lineage→error path (lineage moves release
  forward; era imposes its error regime), the era random effect absorbs the mediated
  portion ⇒ θ_P is conservative with respect to structural lineage.
- Deliberate: θ_P and θ_M bracket the truth; neither is asserted to be "the" causal share.

## Secondary estimand (mechanistic)

```
θ_M = σ²_L  restricted to co-released cohorts and staggered repeated fine-tunes,
            reported separately, never merged into θ_P.
```

- On co-released cohorts, era is held fixed by construction (same quarter, different
  families); on staggered fine-tune chains, lineage is held fixed while era moves.
- Difference between sibling-family co-release correlation and cross-family co-release
  correlation identifies lineage with era literally constant.
- Operating set is small (5 verified cross-generation `base_model` edges) ⇒ scoped
  structural claim, not a population claim.

## Identifier status of each parameter

| Parameter | Identified? | Condition |
|---|---|---|
| σ²_L | Yes | Crossed design (verified) + estimator validity (Phase 1) |
| σ²_E | Yes | Same |
| σ²_U | Yes | Same |
| σ²_L × σ²_E interaction | No | Sparse cells; excluded, documented in Phase 1 |
| θ_M | Yes but small-n | Co-released / staggered-fine-tune subsets only |
