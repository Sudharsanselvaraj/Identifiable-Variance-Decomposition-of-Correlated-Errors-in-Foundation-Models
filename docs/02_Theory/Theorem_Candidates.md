# Theorem Candidates

Candidate formal statements, not proofs. Status tracks whether the statement is proven,
part of the base program, or deferred.

| Statement | Importance | Difficulty | Needed assumptions | Status |
|---|---|---|---|---|
| Crossed family × era design ⇒ σ²_L, σ²_E, σ²_U identified | High (the gate) | Low (textbook variance-components theory) | Linearity on liability scale; random effects independent of regressors | Formal in `Identifiability.md`; numerical confirmation due in Phase 1 D1/D2 |
| Nested design ⇒ σ²_L, σ²_E aliased | High (the counterexample) | Low | Same as above | Formal in `Identifiability.md`; D3 must reproduce |
| LPM-REML bias on liability-thresholded binary responses is bounded and path-decisive | Medium (decides estimator path) | Medium | Liability model is the truth | To be established in Phase 1 liability test |
| θ_P conservative w.r.t. structural lineage (era absorbs mediated path) | Medium | Medium | Release date is a mediator; era effect in model | Argument in `Mathematical_Formulation.md`; sharpened in Phase 2 |
| [Phase 3] Breeder's-equation relationship ΔR = h²·S holds for model populations under analogy | Low (analogy, gated) | High | Phase 2 survives; analogy assumptions | Deferred; drop if Δerror-response doesn't track (register item 3) |
