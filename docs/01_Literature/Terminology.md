# Terminology

Controlled vocabulary for the project. Definitions here are binding; drift from these
terms is a documentation error. Terms marked **[Phase 3]** are gated behind Phase 2
surviving and appear in the base documents only as explicitly-labeled notes.

Population-level definitions are consolidated in `docs/10_Population/`
(Population/Lineage/Environment/Trait/Selection/Inclusion-Exclusion definitions);
the assumption ledger is `docs/00_Project/ASSUMPTION_REGISTER.md`.

## Core settled terms

| Term | Definition | Notes |
|---|---|---|
| **Lineage** | Ancestry relation between models: a model replicates the blind spots of the model, outputs, and data it descends from (verified parent–offspring edges, fine-tune chains, teacher–student distillation). | Never "error inheritance"; never "convergent evolution" (term claimed by Fu et al., arXiv:2604.20817, for a different phenomenon). |
| **Era** | The release-quarter grouping of a model: contemporaneous models trained on shared web scrapes, benchmark-cleansed corpora, and dominant techniques. | Era = public release date, NOT HF `createdAt` (4 documented divergences in Phase 0). |
| **V_lineage / V_era / V_unique** | Variance components σ²_L, σ²_E, σ²_U on the liability scale: lineage-shared, era-shared, model-unique error variance. | The partition is the program's core object. |
| **θ_P (primary estimand)** | σ²_L / (σ²_L + σ²_E + σ²_U) with the era effect in the model — lineage conditional on era. Observational; conservative w.r.t. structural lineage (era absorbs the mediated path). | Never claimed to be the "true" causal share. |
| **θ_M (mechanistic estimand)** | Lineage variance restricted to co-released cohorts and staggered repeated fine-tunes, era held fixed by construction. Reported separately, never merged into θ_P. | Scoped to 5 verified cross-generation `base_model` edges. |
| **Connected subset** | The set of models on which lineage and era are separable (crossed design). The only population the partition is defined on. | Phase 0 verdict: CROSSED (unbalanced/incomplete), gate PASS. |
| **Identifiability** | Whether the variance components can be separately recovered from the design. Crossed ⇒ identified (given estimator validity); nested ⇒ aliased. | The gate. Non-identifiability is a property of the design, not a data gap. |
| **Crossed design** | Families spanning multiple eras AND multiple families per era. | Phase 0 verified. |
| **Nested design** | Each family confined to a single era; lineage and era collinear. | Phase 1 D3 must fail detectably. |
| **Two-estimand rule** | θ_P and θ_M are never merged; they bracket the truth. | Non-negotiable. |
| **Diversification-as-mitigation** | The intervention question RQ6 settles: if V_lineage dominates, diversify families; if V_era dominates, diversify data/technique. | The practical stakes. |
| **Teacher leakage** | Cross-family teacher–student or synthetic-data leakage (Phi-4 ← GPT-4o data; Gemma 2 9B ← 27B; Gemma 4 ← Gemini 3). | Assigned to the era channel (shared environment); inflates σ²_E. |

## **[Phase 3] Gated terms (analogy only, never in base claims)**

| Term | Definition | Gate |
|---|---|---|
| **Heritability (h²)** | Analogous share of trait variance attributable to lineage in a model population. | Phase 2 must survive first; labeled analogy. |
| **Selection differential (S)** | Analogous difference between selected and population mean error trait. | Phase 3; analogy label. |
| **Breeder's equation (ΔR = h²·S)** | Test that change in error response tracks lineage-shared variance × selection differential. | Phase 3; if Δerror-response doesn't track, drop the analogy (register item 3). |
| **Shared environment** | The era channel plus documented teacher leakage, treated jointly. | Used only as Phase-3-labeled scaffolding; base docs say "era" / "shared training data and technique." |

## Forbidden phrasings (in any base document)

- "Quantitative genetics" as a lead / title / abstract framing.
- "Error inheritance."
- "Convergent evolution" (any use).
