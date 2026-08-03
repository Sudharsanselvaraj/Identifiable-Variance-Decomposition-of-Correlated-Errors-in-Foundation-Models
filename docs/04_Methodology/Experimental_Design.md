# Experimental Design

Everything: RQ → experiment → metrics → statistical test → expected outcome → gate.
Source: `proposal.md` §7. No results live here (see `docs/06_Results/`).

## Phase 1 — Simulation validation of the estimator

- **RQ:** RQ1 (recovery under D1/D2), RQ2 (detectable failure under mis-specification).
- **Estimator:** direct REML maximizer on crossed variance components (family, era) —
  `CrossedREML` in `src/lineage_era/estimator.py`. Plan's `statsmodels.MixedLM`
  crossed-vc form was found NOT to maximize the REML objective (see
  `Research_Decision_Log` 2026-08-03) and is not used; the direct solver is
  verified against ANOVA MoM. Binomial GLMM (`BinomBayesMixedGLM`) is the
  item-level binary reference in the liability test.
- **DGPs (known ground truth):**

| Regime | DGP | Expected outcome |
|---|---|---|
| D1 | Balanced crossed design, known σ²_L/σ²_E/σ²_U | Recovers ground truth (reference) |
| D2 | Occupancy copied from Phase 0 table (unbalanced, sparse cells) | Recovers ground truth with quantified precision loss; bias/collapse ⇒ estimator unfit, gate fails |
| D3 | Nested design (each family confined to one era) | **Must fail detectably** (σ²_L/σ²_E aliased) |
| Liability test | Continuous liability thresholded to binary; fit LPM-REML vs. GLMM | Decides the LPM-REML vs. GLMM path for Phase 2 |
| L×E interaction | Include lineage × era interaction in DGP | Expected unidentifiable from sparse cells; documented, not estimated |

- **Metrics:** bias and MSE of each variance component and share; CI coverage; detection
  rate of D3 aliasing.
- **Statistical test / verdict:** direct verdicts (GO / GO WITH CHANGES / NO GO). Silent
  mis-specification bias (RQ2) or D2 collapse (RQ1) ⇒ stop program.
- **Deliverables:** `phase1_simulation.py`, `PHASE1_REPORT.md` (bias tables, verdicts).
- **Gate:** PASS → Phase 2. No real-data claim precedes this gate.

## Phase 2 — Real-data decomposition on the connected subset

- **RQ:** RQ3 (primary θ_P), RQ4 (mechanistic θ_M, separate), RQ5 (era-convergence trend
  as a table entry).
- **Design:** family × quarter crossed on the connected subset; item-level error responses.
- **Steps:**
  1. Assemble item-level error responses for the connected subset models.
  2. Build the family × quarter design matrix from the Phase 0 table plus parent–offspring
     edges drawn from technical reports/papers (the `base_model` field is too sparse).
  3. Fit the mixed model validated in Phase 1 (LPM-REML or GLMM per the Phase 1 decision).
  4. Report the partition σ²_L / σ²_E / σ²_U with CIs as a **table**, not a headline.
     The era-convergence trend (RQ5) collapses into a table entry; it is not a standalone
     result.
  5. Report θ_M separately on co-released cohorts and staggered fine-tune chains. Never
     merge θ_M into θ_P (two-estimand rule).
- **Metrics:** variance shares with CIs; per-item-set precision; model-unique share.
- **Deliverables:** `phase2_decomposition.py`, `PHASE2_REPORT.md`, partition table.
- **Gate:** results interpreted against the Disconfirmability Register.

## Phase 3 — Secondary analogies (gated)

- **RQ:** Phase-3-only questions (see `Research_Questions.md`).
- **Gate:** only if Phase 2 survives.
- **Test:** breeder's-equation test (Δerror-response vs. h²·S); explicitly labeled
  analogy. If Δerror-response doesn't track, drop the analogy (register item 3); the base
  decomposition is untouched either way.
- **Deliverable:** `phase3_report.md`.

## Expected outcomes table

| RQ | Experiment | Expected outcome | Verdict if contradicted |
|---|---|---|---|
| RQ1 | D1/D2 simulation | Recovery with quantified precision loss | Estimator unfit; no real-data claim |
| RQ2 | D3 + liability test | Detectable failure / decisive path choice | Silent bias ⇒ stop |
| RQ3 | Phase 2 primary fit | θ_P estimated with non-degenerate interval | V_lineage\|era ≈ 0 ⇒ lineage refuted |
| RQ4 | Phase 2 mechanistic subsets | θ_M nonzero on small set | Zero ⇒ mechanistic lineage refuted |
| RQ5 | Phase 2 era trend table entry | Convergence or flat, reported as table entry | Flat ⇒ era-convergence refuted |
| RQ6 | Decision layer on partition | Diversification verdict | V_era dominates ⇒ diversification-as-remedy refuted |
