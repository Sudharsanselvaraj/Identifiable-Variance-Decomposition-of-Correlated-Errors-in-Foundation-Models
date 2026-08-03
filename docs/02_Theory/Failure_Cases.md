# Failure Cases

Structured failure cases that would corrupt the partition **without the analysis
noticing** — the silent-failure set. For each: the mechanism, how it is detected
(gate/battery/sensitivity), and the response. This consolidates failure modes
that previously lived in `docs/02_Theory/Identifiability.md` and
`docs/04_Methodology/Threats_to_Validity.md` into the reviewer-requested format.

## FC-1 — Lineage = Era (structural collapse)

- **Mechanism:** the design is nested in truth (families confined to single
  eras, or eras containing a single family), so σ²_L and σ²_E are aliased. If the
  estimator reports "success", mis-specification is silent.
- **Detection:** Phase 1 D3 must-fail control (100% detected); battery S4 must
  abort; `analysis/identifiability.py` rank + BLUP-collinearity checks are the
  on-pipeline gate.
- **Response:** hard-fail aborts the pipeline (exit 2, report). The partition is
  undefined on nested subpopulations by construction — reported as a design
  property, not a data gap.
- **Status:** no occurrence in the current population (design crossed, Phase 0
  verified).

## FC-2 — Unknown RLHF / data-regime variable (missing variable)

- **Mechanism:** an undisclosed training feature — post-training (RLHF) regime,
  synthetic-data recipe, or data-mixture — is correlated with families in a way
  the model does not include. It acts as an omitted random effect, biasing the
  family/era split toward whatever structure it shares.
- **Detection:** not directly observable from the design. Proxies: leaked-drop
  sensitivity (known leakage direction); trait-definition sensitivity (acc vs
  acc_norm); subject-drop sensitivity; the θ_P vs θ_M contrast (a near-zero θ_M
  with nonzero θ_P flags an era-mediated interpretation, RQ4). Unknown-unknowns
  are surfaced in the report's caveats, never silently absorbed.
- **Response:** document the direction of the suspected inflation (era or
  lineage); treat the partition as conditional on the measured environment; keep
  the assumption in the register (A8, A12) and the likely-objection ledger
  (`docs/06_Results/Reviewer_Questions.md`).
- **Status:** teacher leakage known and assigned to era (FC-2a, handled);
  other unknown regimes open.

## FC-3 — Hidden synthetic-data overlap (measurement contamination)

- **Mechanism:** the eval item set overlaps training data in a way that is
  correlated with era (benchmark contamination) — contemporaneous models share
  leaderboard-cleansed corpora, inflating σ²_E — or with family (e.g., a family
  distills its own eval data), blurring lineage.
- **Detection:** contamination is not directly detectable from the design;
  mitigate by item-set exclusion of known-contaminated items and disclose
  (`docs/03_Data/Dataset_Inventory.md` known-risk table). The fresh MMLU 5-shot
  uses one fixed item set so the trait is comparable by construction.
- **Response:** disclosed as an inflation direction; kim_crosscheck is a sanity
  check only, never validation (register A22).
- **Status:** possible, disclosed, item-set mitigation where feasible.

## FC-4 — Small-sample boundary pathology (estimator behavior, not data)

- **Mechanism:** with 6 family levels (df = 5) the family variance component has
  structurally wide intervals; at the U = 0 boundary the direct-REML maximizer is
  pathological (observed s2_era = 7771 during calibration).
- **Detection:** battery S1–S3, S5 use U > 0 exclusively; SE-inflation and
  profile-flatness detectors are **warnings** at df = 5 (they fire by
  construction), pinned by S6 no-false-abort. Rank/VIF/BLUP/convergence remain
  hard fails.
- **Response:** the wide family-share CI is the honest expression of the
  small-sample limit; never reinterpreted as identifiability failure.
- **Status:** documented small-sample limit (register A20, A21).

## FC-5 — Statsmodels path silently inflated (toolchain)

- **Mechanism:** `statsmodels.MixedLM` with single group + `vc_formula` does not
  maximize the crossed REML objective, reporting inflated components (family
  0.61 vs 0.40, era 0.48 vs 0.31).
- **Detection:** direct comparison — ANOVA == brute-force REML exactly, MixedLM
  does not.
- **Response:** MixedLM is not used for the LPM path; `analysis/reml.py` is the
  validated direct REML maximizer. Reportable upstream finding (register A19).

## Register cross-reference

Every failure case maps to register rows: FC-1 → A1, A17, A18; FC-2 → A8, A12,
A23; FC-3 → A15, A22; FC-4 → A20, A21; FC-5 → A19. Threats×mitigations are
tabulated in `docs/04_Methodology/Threats_to_Validity.md`.
