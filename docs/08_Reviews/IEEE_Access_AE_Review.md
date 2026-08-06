# IEEE Access AE + Reviewer Review (2026-08-05)

Review of `docs/07_Paper/manuscript.tex` (9-page build) as a senior IEEE Access
Associate Editor, benchmarked against the official IEEE Access author
guidelines (no page limit; <20 pp recommended; figures 300/600 dpi; no strict
figure cap). Purpose: publishability, presentation, venue fit — with a
prioritized revision plan. The paper's technical core (identifiability-gated
REML variance decomposition, two-estimand rule, outcome-independent population
design) is judged sound; the presentation and completeness are not yet
publishable.

---

## 1. Assessment of the prior external review

The prior review's core thesis is **correct**: this reads as an excellent
research protocol, not a finished IEEE Access research article. Specific claims
verified against the text:

| Prior claim | Verdict |
|---|---|
| 9 pages, feels incomplete vs 15–18 typical | **True.** |
| Placeholder figure boxes are the biggest visual weakness | **True.** All 5 figures are `fig_placeholder.png`. |
| "Phase 0 / Phase 1 / Phase 2 / G3" sound like internal codenames | **True at subsection level.** Main headings are already academic (Introduction … Conclusion); but 7 subsection titles carry "Phase"/"G3" and two are both literally "Phase 2:". |
| Results reads like a proposal | **True, by design.** §VI opens "No empirical claim … is made in this version." |
| Discussion ~half page; Threats ~6 bullets; Conclusion ~half page | **True.** |
| Needs 10–12 figures / 8–10 tables / more appendices | **Directionally true**; see GPU-free additions below. |
| "Entire-page placeholder boxes" | **Overstated.** The `\Figure` blocks are single-column and the placeholder PNG is small; the issue is that empty-looking boxes break the visual rhythm and push float-heavy pages, not that boxes fill pages. |
| "Use one-column figures" | **Already the case** (single-column `\Figure`). The real risk is figure *size/placement* once real art lands, not column width. |

The most important correction to the prior review: **page count cannot be fixed
by prose.** Expanding 9 → 18 pages without running the eval would be padding.
The single highest-impact revision is completing the empirical measurement
pass (runbook `Exp02_GPU_Runbook.md`); the second is high-information,
GPU-free additions listed in §3–§4.

---

## 2. Line-grounded technical findings (beyond the prior review)

These are issues an expert statistical reviewer will raise that the prior
review missed:

1. **Terminology inconsistency (Critical).** Phase 0 defines the *connected
   subset* as the full 47-model population ("the connected subset … is the
   population itself"), and G3 selects a *22-model minimum valid population*
   drawn from it. But Fig. 5's caption says "variance shares … on the
   22-model connected subset", conflating the two. The 22-model set is not the
   connected subset; it is the G3 minimum valid population *within* it. This
   is precisely the kind of looseness a reviewer pounces on.
2. **Causal claim needs precision (Critical).** The Introduction and Fig. 1
   state "release year is simultaneously a *mediator* and a *confounder* of
   the lineage path." Under a standard causal reading, era is a **mediator**
   (family → release timing → shared environment → error) but is **not a
   formal confounder**: release date does not cause family membership, so it
   is not a common cause of lineage and error. The defensible statement is
   that era *confounds the observational family–error association* (family
   membership and error are both functions of release timing), and that the
   mediator path blocks any single causal attribution — which is exactly what
   the two-estimand rule responds to. Either tighten the sentence to
   "mediator of the lineage path and a potential confounder of the
   observational association," or add the formal identification argument
   (DAG → back-door/front-door reasoning → why θ_P and θ_M are separate) in an
   appendix. As written, a causal-reviewing expert can reject on this alone.
3. **Table 3 "PASS*" with −5.3 pp bias (Minor/Major).** The strict bar is
   defined on *era*-share bias (≤5 pp), but the D2 row shows family-share bias
   −5.3 pp flagged `PASS*`. Without an explicit statement that the bar applies
   to the era share, the row reads as a gate violation waived by footnote. The
   text explains this correctly later; the table must carry it inline.
4. **Two "Phase 2:" subsections (Minor).** §V-C and §V-D both begin "Phase 2:".
   Distinct descriptive titles are needed regardless of the Phase/G3 renaming.
5. **2000-repetition numbers not in the committed G3 report (Minor).** §VI-C
   reports "robust at 2000 repetitions (A 1.7 pp / B −3.2 pp)". These values
   exist in `Research_Decision_Log.md` (A 1.71 / B −3.2) but **not** in
   `datasets/coverage/g3_report.md`, so a reviewer checking the released
   artifact cannot reproduce the claim. Add the 2000-rep confirmation row to
   the report.
6. **Estimator-comparison claim is reproducible but buried (Major).** The
   statsmodels finding (REML objective 66.674 vs 65.994 on the balanced 12×12)
   is a genuine contribution and is reproducible from
   `analysis/reml.py` + decision log, but the manuscript only *points* to it.
   Promote it to a **table** (method, design, objective, family/era share,
   family-share coverage in simulation) — all numbers already exist, GPU-free.
7. **Sample-size honesty is present but must lead.** N=47 (22 measured),
   df=5 for family, 6 families. This caps what any partition can support. The
   manuscript discloses this correctly; the Discussion should open with what
   the instrument can and cannot resolve at this power, not close with it.
8. **Novelty framing (Major).** The claim "no verified prior work estimates
   σ²_L+σ²_E+σ²_U for model error traits on the connected subset" is
   defensible, but Related Work is thin on the closest statistical neighbors:
   variance-component / behavioral-embedding analyses of LLM behavior, the
   "model zoology" literature, and co-failure ceiling work (Chen is cited but
   deserves a fuller paragraph). A reviewer will probe exactly these.

---

## 3. Prioritized revision plan

### Critical (must fix before submission)

- **C1. Complete the empirical measurement pass.** Run the 22-model MMLU eval
  (14 public + 8 gated) per `Exp02_GPU_Runbook.md`; validate intake; run
  `phase2_decomposition`; report θ_P/θ_M, CIs, sensitivity against the
  pre-registered rule. No presentation work substitutes for this; it is the
  difference between "protocol" and "research article."
- **C2. Remove placeholder boxes at submission time.** Wire the real figures:
  `fig_design.png` and `fig_g3_trace.png` are staged and real now;
  `fig_similarity.png` / `fig_partition.png` after the eval. If submitting
  before the eval, include only real figures — never placeholder boxes.
- **C3. Fix the connected-subset terminology** (finding 1): Fig. 5 caption →
  "the G3 minimum valid population (22 of 47)".
- **C4. Fix the causal "confounder" claim** (finding 2): tighten wording or add
  the formal identification appendix.

### Major (strongly recommended)

- **M1. Rename subsection headings.** Drop "Phase 0/1/2", "G3", "D1/D2/D3"
  from headings; keep descriptive titles:
  - V-A "Study Population Construction" (was Phase 0)
  - V-B "Simulation Validation of the Estimator" (was Phase 1)
  - V-C "Pre-Analysis Study-Population Design (Minimum-Valid-Population Gate)"
    (was G3)
  - V-D "Trait Measurement and Decomposition" (was Phase 2)
  - VI-A "Population Audit" · VI-B "Simulation Validation" · VI-C
    "Pre-Analysis Population Design" · VI-D "Empirical Results" (once data exist)
- **M2. Add an architecture/pipeline overview figure** (GPU-free): population →
  identifiability gate → simulation validation → population design → eval →
  decomposition → decision layer. Readers need the visual spine.
- **M3. Add a notation table** and expand appendices: notation; REML/Woodbury
  derivation + complexity analysis; the crossing ⟹ identifiable rank argument
  (proof sketch); G3 optimizer constraints/cost tie-break; D3 detectors
  formally. All GPU-free.
- **M4. Add GPU-free figures:** (a) verified-lineage/connected-subset graph
  (families, quarters, VERIFIED_EDGES, chain); (b) D3 aliasing-detection
  diagnostic from the committed simulation outputs; (c) decision-rule framework
  (RQ6 rule as a diagram). These are real, data-backed, and cost nothing.
- **M5. Add GPU-free tables:** estimator comparison (66.674/65.994); GPU cost
  plan (from `gpu_cost_estimate.csv`); full model roster (family/quarter/
  access/params, appendix); notation table. Real numbers, already committed.
- **M6. Expand Related Work** to ~2–2.5 pp: behavioral entanglement,
  variance-components for model behavior, model zoology, co-failure ceiling.
  Verified references only (ledger).
- **M7. Expand Discussion to ~2 pp** (once results exist): why lineage vs era
  dominates; unexpected findings; engineering/deployment implications;
  verifier-ensemble implications (connect Chen co-failure ceiling to the
  partition: σ²_L+σ²_E bounds the all-wrong rate); benchmark implications;
  future work.
- **M8. Expand Threats to ~10–12 items:** selection bias, open-weight sampling
  bias, benchmark contamination/saturation, trait construction, missing
  lineage metadata, temporal drift, power/df, measurement-error independence,
  publication bias, generalizability off the connected subset.
- **M9. Expand Conclusion to ~1 pp** with a numbered contributions list; lead
  with the headline numbers once they exist.
- **M10. Restructure Results** (post-eval) into: A population statistics,
  B variance decomposition, C confidence intervals, D mechanistic analysis,
  E sensitivity, F ablations, G practical implications.

### Minor (editorial)

- **m1.** Table 3 footnote: make explicit the 5 pp bar is era-share only.
- **m2.** Convert bold run-in list items ("D1/D2/D3", "Results status") to
  prose paragraph lead-ins.
- **m3.** Add the 2000-rep confirmation row to `g3_report.md`.
- **m4.** After real figures land, tune placement (single-column inline `[h]`,
  avoid float-heavy near-empty pages); re-check pagination.
- **m5.** Abstract: pre-eval → foreground the methodological contribution;
  post-eval → add the headline shares. Keep ≤250 words.
- **m6.** Consistent stage naming (Phase vs Stage) throughout text and
  appendix titles.
- **m7.** Fill biography + acknowledgment + funding placeholders; confirm
  Hendrycks reference completeness.

### Optional (would increase impact)

- **O1.** Full 47-model eval for power (G3 shows 22 is valid; extra spend).
- **O2.** Additional sensitivity designs (era as trend vs iid; cross-family
  teacher-leakage variants).
- **O3.** A second benchmark beyond MMLU to bound contamination effects.
- **O4.** Formal decision framework for the RQ6 rule.
- **O5.** Complexity/benchmark-scaling appendix (tokens vs est. minutes).

---

## 4. Page-expansion map (9 → 17–19)

High-information additions only; marks GPU-free vs eval-dependent.

| Section | Now | Target | What fills it | GPU-free? |
|---|---|---|---|---|
| Introduction | 1.5 | 2.0 | motivation figure, contribution bullets, roadmap | yes |
| Related Work | 1.0 | 2.5 | M6 additions + diff table + co-failure paragraph | yes |
| Formal Model | 1.5 | 3.0 | notation table, identification argument, estimator details, complexity | yes |
| Methodology | 2.0 | 3.5 | architecture figure, lineage graph, D3 diagnostics, G3 optimizer detail | yes |
| Results | 1.5 | 4.0 | population stats, partition, CIs, mechanistic, sensitivity, ablations | **eval** |
| Discussion | 0.5 | 2.0 | M7 | **mostly eval** |
| Threats | 0.5 | 1.5 | M8 | yes |
| Conclusion | 0.3 | 1.0 | M9 | partly eval |
| Appendices | 1.0 | 3.0 | M3/M5 | yes |

Roughly **+5–7 pages are obtainable now without any GPU**, purely from
existing committed numbers and verified literature; the rest is gated on the
eval. Expanding the GPU-free portion now is worthwhile; expanding the
eval-dependent portion before running the pass would be speculative.

---

## 5. Verdict: protocol vs article

The paper is a **high-quality, honest registered-design study** and, as such,
is ahead of most submissions in reproducibility hygiene. But IEEE Access is a
research journal that publishes completed studies, and the manuscript as it
stands has no empirical findings: every Results subsection either reports a
design artifact or says "(TBD)". Two honest paths forward:

1. **Preferred:** complete the measurement pass (C1), then deliver a finished
   article: real partition, real CIs, real sensitivity, real figures, restructured
   Results, expanded Discussion/Threats/Conclusion. Target 17–19 pp.
2. **Fallback (weakens venue fit):** submit as a clearly-labeled
   design/protocol contribution with only the validated gate results, no
   placeholder figures, and a strong methodological framing. Accept that this
   reduces the acceptance probability at a research journal and would be a
   harder sell to IEEE Access reviewers than a completed empirical study.

The technical foundation — the identifiability gate, the two-estimand rule,
the outcome-independent population design, the reproducible estimator
comparison — is a legitimate 9.5/10 core. The gap to acceptance is execution
(the eval) plus presentation (this plan), not substance.
