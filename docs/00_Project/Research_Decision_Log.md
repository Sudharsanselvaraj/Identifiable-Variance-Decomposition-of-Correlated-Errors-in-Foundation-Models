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

## Pending / open

- **Phase 1 plan approval** (statsmodels MixedLM REML; D1/D2/D3; liability test;
  deliverables `phase1_simulation.py` + `PHASE1_REPORT.md`). User approved the
  `statsmodels` install; plan itself awaiting go.
- **Item-level benchmark procurement** for Phase 2. Decision deferred to the Phase 1
  approval step.
