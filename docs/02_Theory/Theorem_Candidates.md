# Theorem Candidates

Candidate formal statements, not proofs. Status tracks whether the statement is proven,
part of the base program, or deferred.

| Statement | Importance | Difficulty | Needed assumptions | Status |
|---|---|---|---|---|
| Crossed family × era design ⇒ σ²_L, σ²_E, σ²_U identified | High (the gate) | Low (textbook variance-components theory) | Linearity on liability scale; random effects independent of regressors | Formal in `Identifiability.md`; confirmed numerically in Phase 1 D1/D2 (share bias ≤ 5.3pp under D2 occupancy; coverage 88–100%) |
| Nested design ⇒ σ²_L, σ²_E aliased | High (the counterexample) | Low | Same as above | Formal in `Identifiability.md`; D3 reproduced (2026-08-16): 100% detection, 0% silent coverage |
| LPM-REML bias on liability-thresholded binary responses is bounded and path-decisive | Medium (decides estimator path) | Medium | Liability model is the truth | Established in Phase 1 liability test: family bias −2.5 to −15.9pp, ranking_ok 47–80%; GLMM boundary/convergence failures (46–100%) ⇒ LPM-REML path chosen |
| θ_P conservative w.r.t. structural lineage (era absorbs mediated path) | Medium | Medium | Release date is a mediator; era effect in model | Argument in `Mathematical_Formulation.md`; sharpened in Phase 2 |
| σ²_L + σ²_E binds the ensemble co-failure ceiling β; cross-family swap value governed by σ²_L/(σ²_L+σ²_E) | High (decision layer, RQ6) | Medium | Liability model holds (the DGP we validate against) | New (2026-08-16): derived in `CoFailure_Ceiling.md`; validated in simulation; empirical number pending Phase 2 |
| [Phase 3] Breeder's-equation relationship ΔR = h²·S holds for model populations under analogy | Low (analogy, gated) | High | Phase 2 survives; analogy assumptions | Deferred; drop if Δerror-response doesn't track (register item 3) |
