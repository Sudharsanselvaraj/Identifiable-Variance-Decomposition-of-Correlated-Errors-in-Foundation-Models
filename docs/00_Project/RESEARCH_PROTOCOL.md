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

- **Goal:** fresh MMLU 5-shot trait on the **G3 minimum valid population (22 of
  47** connected-subset models), run through the identifiability gate, then
  decompose into σ²_L / σ²_E / σ²_U with intervals, plus the mechanistic θ_M
  tables.
- **Inputs:** eval manifest (`analysis/`), occupancy design, Phase 1-validated
  estimator, G3 subset (`datasets/coverage/minimal_population.csv`).
- **Actions:** (2a) **G3 population gate** (`analysis/population_optimizer.py`,
  DONE → 22 of 47) then fresh eval pass on a GPU host (`phase2_run_all.py`,
  defaults to the subset); (2b) eval intake validation (`analysis/eval_check.py
  --manifest datasets/coverage/minimal_population.csv`, abort on contract
  violation) + trait assembly (`analysis/trait.py`); (2c) design frame
  (`analysis/metadata.py`); (2d) **identifiability gate**
  (`analysis/identifiability.py`, hard-fail = abort); (2e) θ_P partition +
  θ_M tables (`analysis/reml.py`); (2f) bootstrap CIs + trait-error MC
  (`analysis/bootstrap.py`); (2g) sensitivity (`phase2_sensitivity.py`);
  (2h) figures + report (`analysis/plots.py`, `analysis/report.py`).
- **Runbook (2a) — execution order + gated checklist:** the fresh-eval pass is
  confirmed the only compliant source of per-question data (artifact audit
  2026-08-03: 0/47 public reuse; `datasets/coverage/artifact_audit.csv`) and the
  panel rides the same run at zero extra GPU. The G3 gate (pre-registered
  2026-08-03) set the scope to **22 of 47** — ~67% of the single-GPU cost. Run
  on one 8xH200-141GB (fp8) node; per-model memory/GPU plan in
  `datasets/coverage/gpu_cost_estimate.csv`. Order of work:
  0. **G3 population gate (DONE: PASS).** `phase2_population_optimizer.py` →
     22/47 (`datasets/coverage/minimal_population.csv`); `phase2_run_all.py`
     defaults to this subset (`--subset` overrides back to all 47).
  1. **Pass 1 — token-free:** `python3 -m lineage_era.phase2_run_all --skip-gated`
     (14/22 public) from `src/` on the GPU host. No HF token needed.
  2. **Accept the 8 subset-gated licenses** (HF UI per-repo, or
     `huggingface-cli login` + per-repo accept): meta-llama 3 (Llama-1/3.1/3.3),
     Mistral org 4 (Mistral-Small-3/3.2/4, Devstral-2), Google 1 (Gemma-3n).
  3. **Pass 2 — gated:** export `HF_TOKEN`, re-run without `--skip-gated`;
     resume is automatic (`done_models()` skips pass-1 results). DeepSeek-V3.1/
     V3.2 (671B class) run in fp8 on the 141GB cards — the highest-memory step,
     not a blocker.
  4. **Validate intake:** `analysis/eval_check.py --manifest
     datasets/coverage/minimal_population.csv` (22 rows, abort on contract
     violation) → Step 4 decomposition.
- **Synthetic pre-flight (no GPU):** battery S1–S6 (`phase2_simulate.py`)
  validates the gate before real numbers — currently ALL PASS; G3 adds the
  fixed-design battery in `population_optimizer.py`.
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
| G3 | Phase 2 pre-run | Minimum VALID population gate: identifiable + strict-bar + margin confirmation | PASS (22 of 47) |
| G4 | Pre-submission | Novelty audit + kill test + CFP check | PENDING |

> Note: the pre-submission gate was renumbered G3 → G4 (2026-08-03) when the
> Phase 2 minimum-valid-population gate took the G3 label.
