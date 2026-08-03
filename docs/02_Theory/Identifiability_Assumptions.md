# Identifiability Assumptions

Every assumption the identifiability argument rests on, in the A + Evidence /
Violation / Impact format (adopted 2026-08-03 from the restructuring review).
The full consolidated status ledger is the **Assumption Register**
(`docs/00_Project/ASSUMPTION_REGISTER.md`); this page is the theory-specific
expansion. The identifiability *conditions and gate* live in
`docs/02_Theory/Identifiability.md` and `analysis/identifiability.py`.

## IA-1 — Crossed design

- **Statement:** the family × quarter design is crossed — families span multiple
  eras AND multiple families occupy each era. Crossed is the necessary and
  sufficient condition for separating σ²_L, σ²_E, σ²_U.
- **Evidence:** Phase 0 verified contingency table — 6 families × 14 quarters,
  11/14 quarters ≥2 families, no single-era family (`occupancy.check_consistency`
  reproduces the verdict offline).
- **Violation:** if the design is nested (family within era), lineage and era are
  collinear and the partition is unknowable from observational data, regardless
  of estimator quality. Drift toward nesting happens if a lineage terminates
  while others concentrate (Llama already terminated at Llama 4).
- **Impact:** non-identifiability is a property of the design, not a data gap;
  the partition is simply undefined. The audit gate (`rank`, VIF) aborts the
  pipeline on alias rather than reporting garbage.

## IA-2 — Linearity / additivity on the liability scale

- **Statement:** effects (α, β, u) combine additively on the latent scale.
- **Evidence:** Phase 1 liability test — continuous latent → binary threshold;
  LPM-REML on continuous per-model traits recovered components with acceptable
  bias under D2 (register A10).
- **Violation:** if the true model is strongly nonlinear on the liability scale
  (or the continuous-trait aggregation is a bad summary of item responses), the
  components are mis-calibrated.
- **Impact:** silent bias in the partition. Detected via the D3 must-fail control
  and battery S1–S3, S5; not assumed away.

## IA-3 — Random effects independent of regressors (and of each other)

- **Statement:** α, β, u are independent of the item difficulties δ and of each
  other (register A12).
- **Evidence:** stated in `Mathematical_Formulation.md`; **known violation** is
  teacher leakage (Phi-4 ← GPT-4o data; Gemma 2 9B ← 27B; Gemma 4 ← Gemini 3).
- **Violation:** leakage induces cross-family environmental sharing; an
  unrecognized missing variable (e.g., undisclosed RLHF data regime) does the
  same.
- **Impact:** leakage is **not** silently absorbed — it is assigned to the era
  channel (inflates σ²_E) and reported via the leaked-drop sensitivity (register
  A8). Unknown-unknowns are the subject of `docs/02_Theory/Failure_Cases.md`
  (FC-2).

## IA-4 — Finite measurement precision, handled by CIs

- **Statement:** per-model error traits are measured with finite precision;
  precision is a first-class output, not a footnote (register A14).
- **Evidence:** identifiability condition 4; every estimate ships with delta CIs
  (log-variance MC) and trait-error Monte-Carlo that perturbs each trait by its
  measurement SE (`analysis/bootstrap.py`).
- **Violation:** traits measured too coarsely (thin item counts) make the
  partition noise-dominated.
- **Impact:** wide intervals are reported honestly; with thin item counts the
  protocol prefers IRT ability over raw proportion and reports item counts
  alongside (`docs/03_Data/Dataset_Inventory.md`).

## IA-5 — No lineage × era interaction estimated

- **Statement:** the interaction is excluded from the estimands (register A13).
- **Evidence:** not identified from sparse cells; Phase 1 documented the
  non-identifiability; the lxe sensitivity quantifies the cell component.
- **Violation:** silently estimating it would produce garbage.
- **Impact:** none to validity — the interaction is documented, not estimated;
  θ_P and θ_M are the estimands.

## How these bind to the register and the gate

- Register rows: A1, A10, A12, A13, A14, A17, A18, A21.
- Gate: `analysis/identifiability.py` hard-fail = rank, VIF, BLUP collinearity,
  convergence; likelihood-based detectors (profile flatness, SE inflation) and κ
  are warnings at 6 family levels (df = 5) — pinned by battery S4 (must abort)
  and S6 (must not false-abort).
