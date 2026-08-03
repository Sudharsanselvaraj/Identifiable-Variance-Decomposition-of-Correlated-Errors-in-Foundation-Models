# Research Decision Log

Every major decision, with reason, evidence, alternatives, risk, and status. This
document preserves *why* the research evolved, not just *what* it became. Oldest first.

---

## 2026-07-XX (early) — Estimand structure fixed

- **Decision:** Two estimands — θ_P (observational primary: lineage conditional on era)
  and θ_M (mechanistic secondary: lineage holding era fixed, restricted to co-released
  cohorts and staggered fine-tunes), reported separately, never merged.
- **Reason:** Release year is both mediator and confounder on the lineage→error path; a
  single estimand would conflate them and silently collapse the analysis.
- **Evidence:** Master prompt framing; review of Kim et al. (cross-sectional, causality
  open).
- **Alternatives considered:** Single causal estimate (rejected: conflates mediator and
  confounder); instrumental-variable approaches (rejected: no credible instrument).
- **Risk:** Two estimands read as hedging. Mitigated by stating explicitly that the pair
  brackets the truth.
- **Status:** Accepted, non-negotiable.

---

## 2026-07-29 — Quantitative-genetics framing dropped as lead

- **Decision:** Dropped "Quantitative Genetics" as the primary framing. Lead with the
  decomposition instrument and the identifiability gate.
- **Reason:** The biology analogy overshadowed the statistical contribution; it also risks
  being read as claiming heredity that is not identified from observational data.
- **Evidence:** Novelty audit (see `docs/00_Project/Novelty_Claims.md`); the PhyloLM
  precedent showing "genetics" language for models is contested.
- **Alternatives considered:** Keep genetics framing as the title (rejected); use it as
  methodological inspiration only (adopted — Phase 3 gated scaffolding).
- **Risk:** None material. Fallback reserved: Phase 3 analogies can be introduced later,
  clearly labeled, only if Phase 2 survives.
- **Status:** Accepted.

---

## 2026-08-02 — Phase 0 identifiability gate PASS

- **Decision:** Proceed to Phase 1. The open-model population design is CROSSED
  (unbalanced/incomplete). GO.
- **Reason:** Identifiability is the binding constraint; the design supports separation.
- **Evidence:** HF-verified contingency table (6 families × 14 quarters, 11/14 quarters
  with ≥2 independent families, no family confined to a single era). Full log in
  `proposal.md` §14 and `MASTER_PROMPT.md`.
- **Alternatives considered:** NO GO (design nested) — not observed.
- **Risk:** Unbalanced/sparse cells; mitigated by Phase 1 D2 regime reproducing the actual
  occupancy before any real-data claim.
- **Status:** Accepted.

---

## 2026-08-02 — Preference Leakage venue corrected

- **Decision:** Cite Preference Leakage (Li et al., arXiv:2502.01534) as **ICLR 2026**,
  not EMNLP 2024.
- **Reason:** Independent verification showed the earlier venue was a citation error.
- **Evidence:** arXiv record (v3, "Accepted by ICLR 2026").
- **Alternatives considered:** None.
- **Risk:** None. Correction propagated into all documents.
- **Status:** Accepted.

---

## 2026-08-02 — proposal.md deleted, then rewritten as single document

- **Decision:** First: delete `proposal.md` and `audit_log.md` (user instruction).
  Then: rebuild `proposal.md` as the 14-section proposal, one section at a time, with
  every cited claim verified before inclusion.
- **Reason:** Clean single source of truth for the proposal text; mandatory citation
  verification on every entry.
- **Evidence:** Related-work ledger re-verified in-session (7 papers).
- **Alternatives considered:** Section-by-section chat-only drafting (rejected: no
  persistent artifact).
- **Risk:** Low.
- **Status:** Accepted.

---

## 2026-08-02 — Research knowledge base adopted

- **Decision:** Build `docs/` knowledge base (00–09 schema) as the project's source of
  truth, seeded from settled context; `MASTER_PROMPT.md` + `proposal.md` remain the
  running execution/proposal documents; git init for history.
- **Reason:** Persist rationale, novelty audits, kill tests, and decisions for a
  multi-year project; defend design choices at thesis review and rebuttal time.
- **Evidence:** This project's own decision history (this log).
- **Alternatives considered:** GitHub-repo-style "idea → code → paper" (rejected: no
  decision trail); empty templates (rejected: no content to fill).
- **Risk:** Low. Maintenance burden mitigated by one-line pointer from `MASTER_PROMPT.md`.
- **Status:** Accepted.

---

## 2026-08-03 — Phase 0 codified into code; one record annotation flagged

- **Decision:** Codify the Phase 0 record into `src/lineage_era/occupancy.py`
  (models, edges, caveats, era divergences, offline consistency check). The
  table is the authoritative occupancy source for D2; the consistency check
  reproduces every hard Phase 0 stat exactly.
- **Reason:** D2 requires occupancy copied from the Phase 0 table; codifying it
  makes the simulation reproducible and auditable offline.
- **Evidence:** `occupancy.check_consistency()` reproduces 6 families × 14
  quarters, 47 models, 5 edges, 11/14 quarters ≥2 families, all row spans
  exactly. **Finding:** the Phase 0 log's dense-cell annotation (2024Q2=5,
  2024Q3=5, 2025Q2=6) does NOT match the table (2024Q2=5, 2024Q3=4, 2025Q2=5)
  under either a family-count or model-count reading. Annotation treated as
  inaccurate; table remains authoritative for D2.
- **Alternatives considered:** Correct the annotation silently (rejected:
  table is the verified record); fail hard on the mismatch (rejected: it is a
  descriptive note, not a gate criterion).
- **Risk:** None for D2 (occupancy comes from the table). Logged so the
  annotation is not re-quoted in the paper as a verified number.
- **Status:** Accepted.

---

## 2026-08-03 — statsmodels MixedLM crossed-VC path is suboptimal; Phase 1 LPM replaced with a direct REML maximizer

- **Decision:** Do NOT use statsmodels `MixedLM` (single group + `vc_formula`)
  for the crossed family × era variance-component model. Replace with a direct
  REML maximizer in `src/lineage_era/estimator.py` (Woodbury-accelerated),
  verified to agree exactly with two-way ANOVA method-of-moments on balanced
  crossed data.
- **Reason:** MixedLM does not maximize its own REML objective for crossed
  variance components. On an F=E=12, K=2 balanced dataset, brute-force REML
  and ANOVA both give (0.399, 0.313, 0.656), while MixedLM reports
  (0.609, 0.476, 0.656) — same scale (unique) but a family/era split that is
  NOT the REML optimum (objective 66.674 vs 65.994). Identical results under
  lbfgs/cg/powell/bfgs, reml=False, em=False, gtol=1e-12, maxiter=5000, so
  this is structural, not optimizer noise. Scale/unique is accurate; only the
  crossed split is wrong.
- **Evidence:** `ANOVA == brute-force REML == direct solver` across F=12/E=12,
  F=6/E=14, F=8/E=10; 100-rep D1 battery unbiased (F=50: s2 means
  0.501/0.200/0.302 vs truth 0.5/0.2/0.3); 300-rep D1 calibration coverage
  96/95/95 (scenario A) and 96/96/95 (B).
- **Alternatives considered:** keep MixedLM and report the bias (rejected: the
  estimator is the central deliverable and was not at the REML optimum);
  ANOVA MoM only (rejected: no joint covariance for share CIs; kept as the
  validation cross-check).
- **Risk:** Low. The direct REML is textbook (Searle/Harville), matches ANOVA,
  and passes the same gate the MixedLM version failed (bias ≤5pp, coverage
  ≥90%). Worth reporting the MixedLM behavior to statsmodels upstream.
- **Status:** Accepted.

## 2026-08-03 — D1 family count raised 6 -> 30; F=6 limits family-share coverage

- **Decision:** D1 (balanced, idealized reference) uses 30 families (14 eras,
  2 models/cell). D2 keeps the realistic 6-family occupancy.
- **Reason:** The plan's D1 is "balanced crossed design" (no count; 6×14×2 was
  an implementation detail). With F=6 (df=5) the realized family variance is so
  noisy that family-share CI coverage is capped ~85–92% regardless of CI
  method (chi-square-correct copula and normal-delta both fail the 90% gate);
  this is a design-power limit, not an estimator defect. F=30 separates
  "does the estimator work" (yes: bias ≤2.5pp, coverage 95–96%) from "does the
  6-family design resolve the family share" (only at the D2 occupancy, where
  sparse cells inflate CIs and coverage is 95–100%).
- **Evidence:** F=6 balanced: family coverage 87–92% and share bias −4 to
  −5.6pp; F=50: coverage 92/90/94, s2 means essentially unbiased. D2 (real
  occupancy, F=6): coverage 95–100% because sparse cells widen CIs.
- **Risk:** D2 family-share bias in the lineage-dominant scenario is ~ −5pp
  (small-sample), right at the gate boundary — documented in the report.
- **Status:** Accepted.

## 2026-08-03 — Liability test: era variance underpowered on binary item data at 47 models

- **Decision:** The Phase 2 estimator path is **LPM-REML on per-model
  continuous traits**. The binomial GLMM remains the reference for item-level
  binary data but its era component collapses at the real 47-model occupancy.
- **Reason:** On item-level probit data, the GLMM (Laplace) recovers the
  partition at the well-powered D1 occupancy (bias ≤5pp, era boundary 0%,
  cross-path agreement 100%) but at D2 (47 models) the era variance collapses
  to the boundary in 20–60% of reps and era share bias reaches −13 to −16pp.
  The LPM on per-model proportions is also era-biased in the era-dominant
  scenario. Both paths agree on the family share (corr 0.81–0.92). The
  collapse is a power limit of binary outcomes at 47 models, not a GLMM bug.
  Phase 2 uses continuous per-model scores (the D2 continuous design recovers
  era with 98–100% coverage), so LPM-REML applies.
- **Evidence:** D2 liability 30-rep run: GLMM era-boundary 20–60%, converged
  33–67%; LPM era boundary 0–7%. D1 liability sensitivity: both paths bias
  ≤5pp, era boundary 0%, agreement 100%.
- **Risk:** If Phase 2 data turns out to be item-level binary, era claims will
  be underpowered at 47 models; mitigation documented in the report.
- **Status:** Accepted.

## 2026-08-03 — Phase 2 estimator path + procurement constraint (from Phase 1 F4)

- **Decision:** Phase 2 fits **LPM-REML on a continuous per-model trait** —
  never the raw item-level binary responses. The trait is an aggregation of
  item-level responses into a per-model continuous score: accuracy proportion
  or an IRT-style ability estimate (e.g., 2PL/3PL person score over the common
  item set). This is the Phase 2 kickoff pivot and a procurement constraint.
- **Reason:** Phase 1 F4 — item-level binary outcomes cannot resolve the era
  variance component at the real 47-model occupancy (GLMM era-boundary
  collapse 20–60%; era-share bias to −13/−16 pp), while per-model continuous
  traits recover era with 98–100% coverage (D2 continuous). The LPM-REML path
  was validated in Phase 1; it operates on continuous model-level traits
  anyway.
- **Procurement consequence:** benchmark procurement targets *item-level
  response logs* (as before) but the modeling target is the **aggregated
  per-model score**, not per-item Bernoulli fit. Compatible with reusing Kim
  et al.'s public data (arXiv:2506.07962, ICML 2025): aggregate their
  item-level results per model — strictly less work than modeling raw binary
  responses, and the same data serves a continuous-trait design.
- **Alternatives considered:** fit GLMM directly on item-level binary (rejected
  by F4 power limit at 47 models); treat per-model proportions as Gaussian
  directly (accepted for LPM; IRT ability as the precision-weighted upgrade if
  item counts are thin).
- **Risk:** aggregation discards item-level information and measurement-error
  structure; mitigated by reporting trait standard errors / item counts with
  every share CI. Variance of the trait estimator lands in σ²_U; document that
  σ²_U is measured-with-error inclusive.
- **Status:** Accepted.

---

## Pending / open

- **Item-level benchmark procurement for Phase 2** — DECISION MADE 2026-08-03
  (this entry): target = public item-level response logs aggregated into a
  continuous per-model trait; primary candidate = Kim et al. (arXiv:2506.07962)
  public data, aggregated per model. Remaining work = availability/license
  check on the connected subset, then fill `docs/03_Data/Dataset_Inventory.md`
  inventory table. No further estimator-path decision pending.
