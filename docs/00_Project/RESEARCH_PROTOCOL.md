# Research Protocol

End-to-end protocol for the Lineage-vs-Era research program (adopted 2026-08-03
from the restructuring review). Written like a pre-registered clinical-trial
protocol: every stage names its goal, inputs, actions, and an **exit gate** that
must pass before the next stage. Gates are honesty points — they do not move.

This repository is a **scientific instrument** (a variance-decomposition
instrument for correlated model errors) and its papers are **Studies** run on
that instrument. The current paper is **Study 001** (`docs/07_Paper/`); a Phase 3
analogy paper would be Study 002.

## Phase mapping (repo scheme ↔ reviewer scheme)

The reviewer's 5-phase vocabulary maps onto the repository's existing (0–3)
scheme without renumbering anything — code, decision log, and gates keep their
names:

| Repository scheme (used everywhere) | Reviewer scheme (for cross-references) |
|---|---|
| Phase 0 — Population audit & identifiability | Phase 0 Research + Identifiability; Phase 1 Metadata + Population |
| Phase 1 — Simulation validation (D1/D2/D3) | Phase 1/2 boundary (estimator validation before trait measurement) |
| Phase 2 — Trait measurement + statistical decomposition | Phase 2 Trait Measurement + Phase 3 Statistical Decomposition |
| Phase 3 — gated analogies (never merged into base claims) | Phase 4 Scientific Conclusions (analogy layer only) |

GPU compute enters only at **Phase 2** (the fresh eval pass); Phases 0–1 run
entirely on CPU/offline data.

## Operating rules (apply to every stage)

1. **Identifiability before results** — any measurement runs through the
   crossed-vs-nested question before it becomes a deliverable.
2. **Simulation before real data** — no real-data claim precedes Phase 1
   validation (RQ2 stop rule).
3. **Pre-registration** — refutation conditions are recorded in the
   Disconfirmability Register (`docs/06_Results/Negative_Results.md`) and the
   Assumption Register before Phase 2 results exist.
4. **Honesty over encouragement** — direct verdicts (GO / GO WITH CHANGES /
   NO GO); negative results are kept.
5. **Decisions are logged** — every material decision enters
   `docs/00_Project/Research_Decision_Log.md` with reason, evidence,
   alternatives, risk, status.
6. **Two-estimand rule (non-negotiable)** — θ_P and θ_M are reported separately,
   never merged (register A23).

## Protocol stages

### Phase 0 — Population & identifiability (DONE: PASS)

- **Goal:** define the connected subset and prove the design question (crossed
  vs nested) is answerable.
- **Inputs:** HF API metadata for ~45 open-weight models; technical reports.
- **Actions:** build the verified family × quarter contingency table; check
  crossed-ness; record caveats.
- **Exit gate (G0):** crossed (unbalanced/incomplete) verified; otherwise the
  program does not start.
- **Deliverables:** `docs/10_Population/`, `occupancy.py`, identifiability
  conditions in `docs/02_Theory/Identifiability.md`.

### Phase 1 — Simulation validation (DONE: PASS, GO WITH CHANGES)

- **Goal:** prove the estimator recovers known ground truth under the real
  occupancy (D2), fails detectably when nested (D3), and that the liability
  decision (continuous trait) is sound.
- **Inputs:** Phase 0 occupancy; DGP + direct REML maximizer.
- **Actions:** D1 (balanced-crossed reference), D2 (realistic occupancy), D3
  (nested must-fail), liability test, coverage/CI checks.
- **Exit gate (G1):** bias ≤ tolerance under D2; D3 fails detectably; GLMM era
  collapse documented (led to the continuous-trait decision).
- **Deliverables:** `phase1_simulation.py`, `PHASE1_REPORT.md`,
  `Statistical_Model.md` path decision.

### Phase 2 — Trait measurement + statistical decomposition (IN PROGRESS)

- **Goal:** fresh MMLU 5-shot trait on all 47 connected-subset models, run
  through the identifiability gate, then decompose into σ²_L / σ²_E / σ²_U with
  intervals, plus the mechanistic θ_M tables.
- **Inputs:** eval manifest (`analysis/`), occupancy design, Phase 1-validated
  estimator.
- **Actions:** (2a) fresh eval pass on a GPU host (`phase2_run_all.py`);
  (2b) eval intake validation (`analysis/eval_check.py`, abort on contract
  violation) + trait assembly (`analysis/trait.py`); (2c) design frame
  (`analysis/metadata.py`); (2d) **identifiability gate**
  (`analysis/identifiability.py`, hard-fail = abort); (2e) θ_P partition +
  θ_M tables (`analysis/reml.py`); (2f) bootstrap CIs + trait-error MC
  (`analysis/bootstrap.py`); (2g) sensitivity (`phase2_sensitivity.py`);
  (2h) figures + report (`analysis/plots.py`, `analysis/report.py`).
- **Synthetic pre-flight (no GPU):** battery S1–S6 (`phase2_simulate.py`)
  validates the gate before real numbers — currently ALL PASS.
- **Exit gate (G2):** identifiability audit PASS on real data; partition
  reported **against the register**; θ_M reported separately; small-sample
  limits disclosed.
- **Deliverables:** `src/results/phase2/PHASE2_REPORT.md`, partition table,
  `bootstrap_ci.csv`, sensitivity blocks.

### Phase 3 — Gated analogies (DEFERRED; not part of Study 001)

- **Goal:** analogy layer (heritability h², selection differential, breeder's
  equation) — **only** if Phase 2 survives, and only in clearly-labeled analogy
  language (register item 3). Drop the analogy if Δerror-response doesn't track.
- **Deliverables:** follow-on paper = Study 002, never merged into the base
  claim.

### Paper / submission

- Pre-submission gate (`docs/09_Roadmap/Publication_Plan.md`):
  1. Novelty audit re-run.
  2. Kill test on every claim.
  3. Venue CFP checked at submission time; no stale venue claims.
  4. All citations from the verified ledger.
- Route: optional workshop preview → ICML (primary) or NeurIPS /
  measurement-focused venue → journal only if warranted.

## Gate ledger

| Gate | Stage | Criterion | Status |
|---|---|---|---|
| G0 | Phase 0 | Crossed design verified | PASS |
| G1 | Phase 1 | D2 recovery + D3 detectable + liability decision | PASS (GO WITH CHANGES) |
| G2 | Phase 2 | Real-data audit PASS; partition reported against register | PENDING (GPU eval) |
| G3 | Pre-submission | Novelty audit + kill test + CFP check | PENDING |
