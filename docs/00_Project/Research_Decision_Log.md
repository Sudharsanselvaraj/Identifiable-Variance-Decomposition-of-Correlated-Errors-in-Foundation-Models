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
  REML maximizer in `src/lineage_era/analysis/reml.py` (Woodbury-accelerated),
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

## 2026-08-03 — Phase 2 coverage check: leaderboard data covers 18/47; gate FAILS; fresh eval pass required

- **Decision:** Recorded coverage outcome and the resulting procurement gate
  (pending user cost decision). Phase 2 data assembly implemented as
  `src/lineage_era/analysis/population.py` (reconciliation map + coverage gate) and run
  against Kim et al. (arXiv:2506.07962, CC BY 4.0) MMLU accuracy files.
- **Coverage result:** 18/47 connected-subset models (38.3%). By family:
  Llama 5, Qwen 3, DeepSeek 0, Mistral 5, Phi 3, Gemma 2. Gates: models
  18 < 24 (bar: >=50%), families 5 < 6 (DeepSeek absent) → **FAIL**.
- **Cause:** the shared-MMLU-item leaderboard data is structurally frozen —
  Kim's HF v1 file (451 models) and HELM (71 models) stop ~2024; Open LLM
  Leaderboard v2 (MMLU-PRO) snapshot in Kim's repo AND the live v2 API
  (checked 2026-08-03) freeze at submission 2025-03-13. All 29 missing models
  are 2025Q1+ releases (Qwen3/3.5/3.6, Llama-4, Gemma-3/3n/4, DeepSeek-V3+,
  Phi-4, Mistral-Small-3+ incl. Devstral-2), including every modern DeepSeek.
- **Implication:** the 29 gap models are only reachable by a fresh evaluation
  pass on the connected subset. That also yields a strict common item set
  (better than Kim's data, which mixes two leaderboards' MMLU subsets).
  Cost/budget decision is the open item (recorded as pending).
- **Alternatives considered (rejected for the full decomposition):** proceed on
  18/47 (Phase 1 shows family bias ~ -5pp at F=6 and era underpower; with
  DeepSeek absent the crossed family dimension is broken — would produce
  unreliable shares); re-scope the subset to exclude 2026 models and use
  Kim+v2 for the rest (still leaves 2025Q2-Q4 gaps and DeepSeek absent).
- **Status:** gate outcome ACCEPTED; the cost decision for the fresh eval pass
  is pending user input.

## 2026-08-03 — Fresh eval pass on all 47 models; benchmark = MMLU 5-shot

- **Decision:** Produce the Phase 2 per-model trait by a fresh evaluation of
  ALL 47 connected-subset models on one fixed benchmark — MMLU 5-shot — giving
  a strict common item set. No leaderboard-derived accuracy is reused for the
  trait (Kim et al.'s 18-model MMLU values are retained only as a validation
  cross-check, not as the trait source).
- **Reason:** leaderboard data covers only 18/47 and mixes two MMLU subsets;
  a single fresh pass on one item set fixes comparability and reaches the
  DeepSeek/2025+ models that no leaderboard carries. User approved the
  "all 47 / one benchmark" scope over "gaps only" and "proceed on 18".
- **Benchmark rationale:** MMLU 5-shot (not MMLU-PRO) keeps the trait
  semantically identical to the Kim et al. benchmark the paper is compared
  against; also the cheapest per model (loglikelihood, no generation).
- **Implementation:** `src/lineage_era/phase2_eval.py` — canonical HF
  checkpoint per connected-subset model (manifest verified 47/47 via HF API on
  2026-08-03), access class (23 token-free, 24 gated), lm-eval-harness 0.4.12
  runner (loglikelihood; eager attention default). MMLU dataset (`cais/mmlu`)
  downloaded.
- **Availability facts:** every one of the 47 has a canonical HF repo; the
  2026 frontier models (Qwen3.5/3.6, DeepSeek-V4, Mistral-Small-4,
  Mistral-Medium-3.5, Gemma-4) exist but are gated. Gated models need
  HF_TOKEN with license accepted.
- **Environment constraint:** the dev Mac (Apple M5, 17 GB, MPS allocator
  errors, slow CPU) cannot produce the numbers; the full run needs a GPU host.
  Local CPU/MPS runs are pipeline pilots only (validated through model load +
  task setup).
- **Per-model caveats for the full run:** Phi-1/1.5/2 are 2048-token context —
  some MMLU 5-shot prompts exceed it and crash; these need max_length handling.
  Sliding-window models (Qwen, Mistral) should use `sdpa` (not eager) on GPU.
- **Alternatives considered:** MMLU-PRO (rejected: breaks comparability with
  the 18 Kim values and with the paper's benchmark framing); gaps-only eval
  (rejected: two-source trait, weaker comparability).
- **Risk:** compute/budget; mitigated by the loglikelihood scoring (fast) and
  by it being the same benchmark Kim et al. used.
- **Status:** benchmark decision ACCEPTED; run venue / HF token / cost open.

---

## 2026-08-03 — Reviewer restructure adopted: analysis/ package + consolidated docs

- **Decision:** Adopt the 10/10 review's restructuring recommendations as a
  documentation/engineering pass, **without** renumbering the repository's phase
  scheme (0–3) or touching the research design:
  1. Add `docs/00_Project/ASSUMPTION_REGISTER.md` (single source of truth for
     assumptions; ID/Evidence/Confidence/Testable/Risk/Status) and
     `docs/00_Project/RESEARCH_PROTOCOL.md` (stage-gated protocol; includes the
     phase-mapping note to the reviewer's 5-phase vocabulary).
  2. Add `docs/10_Population/` (8 files) — consolidating population/lineage/
     environment/trait/selection/inclusion-exclusion content that was scattered
     across Terminology, Model_Lineages, Metadata, Dataset_Inventory.
  3. Add `docs/02_Theory/Identifiability_Assumptions.md` (A + Evidence/Violation/
     Impact) and `docs/02_Theory/Failure_Cases.md` (Lineage=Era, unknown RLHF,
     hidden synthetic overlap + detector mapping).
  4. Restructure Python into an `analysis/` package (`trait, metadata,
     population, identifiability, reml, bootstrap, plots, report`) with the old
     `phase2_*.py` / `estimator.py` names kept as thin re-export shims, so the
     CLI and runbook are unchanged. Verified: py_compile, smoke_test, battery
     ALL PASS, full synthetic pipeline dry-run (report identical).
- **Reason:** the review rated documentation/code-organization 9/10 and 8.5/10;
  its substantive asks were a research protocol + assumption register and a
  clearer code layout. The underlying content already existed but was scattered;
  the pass is consolidation, not new science.
- **Alternatives considered:** renumbering to the reviewer's 5-phase scheme
  (rejected: ripples through code, decision log, and gates for no scientific
  gain); `analysis/` refactor deferred until Phase 2 results (rejected: shims
  make it safe to do now, and it is cheaper before more code lands).
- **Risk:** low — behavioral equivalence verified (battery + synthetic pipeline
  byte-identical outputs); shims preserve every import path.
- **Status:** ACCEPTED, implemented.

---

## 2026-08-03 — Error-similarity secondary panel + pre-registered measure rule

- **Decision:** Add a **secondary error-similarity panel** to Phase 2, wired into
  `phase2_decomposition.py` after sensitivity, running only on real per-question
  samples. It reports the *observed* pairwise error overlap of the 47 models on
  the shared item set (within- vs between-family), *why* that overlap exists
  (family channel → variance decomposition), identifiability, and implications.
  Paper section order per reviewer: §5 Observed Population → §6 Error Similarity →
  §7 Identifiability → §8 Variance Decomposition → §9 Intervention Implications.
- **Measure-selection rule (pre-registered, fair):** the primary measure is chosen
  by a fixed rule in `analysis/error_similarity.py` `evaluate_criteria`, NOT by
  effect size. Every candidate passes C1 (calibration on a balanced no-overlap
  fixture vs item-difficulty null), C1b (accuracy-robust on an imbalanced
  no-overlap fixture vs matched-accuracy null), C2 (signal z ≥ 3 vs
  matched-accuracy null, sign agreeing with the balanced fixture), C3 (within >
  between in ≥ 90% of bootstrap reps), then the tie-break prefers **chance-
  corrected measures** (phi, Yule's Q, Cohen's kappa) over rate-sensitive ones
  (jaccard/overlap/cosine). On the fixture battery all six measures pass
  C1/C1b/C2/C3; the rule selects **phi**.
- **Reason:** reviewer feedback warned the panel could read as evidence shopping;
  a pre-registered rule with a chance-corrected preference makes the choice
  defensible (the initial run selected jaccard — exactly the rate-sensitive
  measure flagged — so the preference was added before any real data existed).
- **Null ladder (methodology contribution):** observed → matched-accuracy
  per-model shuffle → item-difficulty strata shuffle (most conservative) →
  analytic independence. Headline tests use matched-accuracy; calibration uses
  item-difficulty.
- **Evidence:** `src/lineage_era/test_error_similarity.py` — 4 fixtures
  (balanced_signal, imbalanced_signal, no_overlap, imbalanced_no_overlap);
  signal z ≈ 3.4–3.9 (balanced) / 3.8–4.2 (imbalanced); calibration
  −1.4…−1.6; phi selected. Full battery + synthetic pipeline dry-run green.
- **Alternatives considered:** biggest-effect selection (rejected: rewards the
  rate-sensitive measure); no panel (rejected: loses the observational layer the
  reviewer asked for); UMAP/igraph embeddings (rejected: not installed; PCA +
  t-SNE via sklearn, Louvain via networkx).
- **Risk:** the panel is observational and correlational; it never merges with θ_P
  (two-estimand rule). σ²_U remains measured-with-error inclusive.
- **Status:** ACCEPTED, implemented, validated.

---

## 2026-08-03 — Artifact-availability audit: 0/47 reusable; fresh eval on all 47 CONFIRMED (Path A)

- **Decision:** Run the fresh MMLU 5-shot eval on **ALL 47** connected-subset
  models (Path A, locked). Public item-level artifacts cannot replace it:
  protocol-matched per-question reuse is **0/47**. Evidence:
  `datasets/coverage/artifact_audit.csv` (47-row per-model x source table, built
  by `analysis/artifact_audit.py`) and `datasets/coverage/gpu_cost_estimate.csv`
  (per-model memory/compute plan, built by `analysis/gpu_cost.py`).
- **Reason — the audit, source by source:**
  - Open LLM Leaderboard v2 per-sample JSONL: 8/47 exact-repo files exist but on
    **MMLU-PRO** (10-choice) — wrong benchmark; frozen ≤ Dec 2024; the files are
    gated behind repo-terms acceptance (verified 401).
  - HELM per-question tall file (`all_mmlu_data_limitedcols.csv`, Kim GitHub):
    14/47 models present but on HELM's own MMLU item set/template with HELM
    question ids — no common-question bridge to `cais/mmlu`, and **no DeepSeek**
    (family gate 5/6 fails).
  - Aggregate leaderboard MMLU (Kim CSVs): 18/47 score-only — retained ONLY as a
    validation cross-check (register A22), never as the trait or the panel.
  - 29/47 have no public artifact at all (mostly post-freeze 2025Q1+ incl. every
    DeepSeek; a few pre-2024 stragglers — Llama-1, Qwen-7B, Phi-1/1.5, Phi-4,
    DeepSeek-V3 — never reached leaderboard v2).
  - **Cost-collapsing fact:** the error-similarity panel rides the SAME fresh
    run at zero extra GPU — `phase2_eval.py` already emits per-question JSONL
    (`log_samples=True`). So the only decision left was one vs. many runs.
- **Cost estimate (planning, not benchmark):** MMLU 5-shot loglikelihood
  ~6.4M tokens/model (no generation, memory-bound); one 8xH200-141GB (fp8)
  node: small/mid packed on 80GB cards, 70–141B on 4x80GB, DeepSeek 671–700B
  class in fp8 → realistic ~12–24 wall-hours, ~$100–300 for 1–2 days. The hard
  gate is the **24 gated models** (license acceptance + HF_TOKEN), not cost.
- **Alternatives considered:** reuse the OLLB MMLU-PRO per-question files for 8
  (rejected: different benchmark + item set, breaks the strict common item set
  and comparability with Kim et al.); use the HELM tall file for 14 (rejected:
  no item-level bridge to a fresh `cais/mmlu` run); hybrid reuse+fresh (rejected:
  two-source trait, still DeepSeek-gapped).
- **Risk:** compute + license friction only; no scientific risk — same benchmark
  (MMLU 5-shot) as the paper's comparison target.
- **Status:** ACCEPTED. Path A locked. Next: user executes the runbook
  (`phase2_run_all.py`, gated license checklist for the 24) on a GPU host;
  results → `datasets/phase2_eval_results.csv`, then Step 4 decomposition.

## 2026-08-03 — G3 gate: minimum VALID population = 22 of 47 (pre-registered before GPU spend)

- **Decision:** Before ANY Phase 2 GPU spend, select the smallest connected-subset
  population whose family × quarter design is identifiable AND whose era recovery
  clears the strict Phase 1 D2-continuous bar. Result: **run 22 of 47 models**, not
  all 47. G3 is a pre-run gate — no real accuracy data is consulted (structural +
  fixed-design-DGP selection only).
- **Rule (pre-registered):**
  1. Minimize model count subject to hard constraints: all 6 families present with
     ≥ 2-quarter span; every quarter 2023Q1–2026Q2 keeps ≥ 1 model; ≥ 2 quarters
     with ≥ 2 families (crossed); the in-subset VERIFIED_EDGES endpoints AND the
     Mistral-Small chain are kept (θ_M survives); the induced design passes
     `identifiability.structural_checks` (full rank, VIF ≤ 10).
  2. Tie-break on cost (public > gated, then `est_minutes_single_gpu`) — scipy
     Highs MILP, deterministic.
  3. "Valid" = fixed-design battery (scenarios A and B, mean over converged reps,
     register A21) clears |era share bias| ≤ 5pp AND CI coverage ≥ 90%.
  4. **Two-stage + margin (added this session, pre-registration-consistent):** the
     per-rep share-bias distribution is heavy-tailed (SD ~22–26pp), so candidates
     that clear the bar at 300 reps must ALSO clear it with ≥ 1pp margin (|bias|
     ≤ 4pp) at a 1000-rep confirmation. Rationale: the 21-model structural minimum
     sits *exactly* on the bar (B-bias ≈ −5.0pp at 1000–2000 reps, SE ≈ 0.6–0.8pp),
     an un-resolvable knife-edge; the margin rejects it.
- **Outcome:** structural minimum n0 = 21 (identifiable) but knife-edge → rejected.
  **Minimum VALID population = 22** (winner: Llama-1/3.1/3.3, Phi-1/1.5/2/3/4,
  4-reasoning-plus, 4-reasoning-vision-15B, Mistral-7B, Small-3/3.1/3.2/4,
  Devstral-2, DeepSeek-V3.1/V3.2, Gemma-3n/4-12B, Qwen-7B/1.5; 14 public + 8 gated).
  Winner clears the bar at 300 reps (A 2.44pp, B −0.78pp) AND the margin
  confirmation at 1000 reps (A 2.19pp, B −2.36pp); robust at 2000 reps (A 1.71pp,
  B −3.16pp).
- **Cost:** ~710 vs 2154 est. single-GPU minutes (67% cut, ~1,444 min saved);
  GPU spend is no longer "scientifically justified only at 47" — 22 suffice.
- **Evidence:** `src/lineage_era/analysis/population_optimizer.py` (optimizer +
  validator), `datasets/coverage/minimum_valid_population.csv` (kept/dropped +
  per-model reason), `datasets/coverage/g3_report.md` (search trace + validation
  table), `src/lineage_era/test_population_optimizer.py` (11 tests).
- **Wiring:** `phase2_run_all.py --subset` now defaults to the G3 CSV; `eval_check
  --manifest` validates a reduced-run intake against the 22-row subset instead of
  the full 47.
- **Alternatives considered:** reject the gate (rejected: unfounded GPU spend);
  accept the knife-edge 21 (rejected: decision flips with reps — not defensible);
  raise reps to settle 21 (rejected: heavy tail → SE ~0.6pp even at 2000, boundary
  unresolved); median instead of mean (rejected: diverges from the Phase 1 D2
  convention, register A21).
- **Risk:** the subset still needs its own full eval; the error-similarity panel
  rides the same run. If a subset model fails at eval time, the runbook resumes
  and `eval_check --manifest` catches shape problems.
- **Status:** ACCEPTED, implemented, validated (11/11 tests, ruff clean).

---

## 2026-08-16 — Phase 2 execution consolidated on one RunPod A100-80GB

- **Decision:** The measured 20 models all run on a single rented A100-80GB
  (RunPod) instead of the earlier Colab Free/T4 + A100 split. Fidelity ledger
  amended **before any eval** (the Phi-2 pilot failed pre-measurement and wrote
  no data): 17 models at bf16 (`--dtype bfloat16 --quant none`), three 70/72B
  models at 4-bit (`--quant 4bit` — they do not fit bf16 in 80GB), DeepSeek
  V3.1/V3.2 unchanged (imputed). Recorded in
  `datasets/coverage/trait_definition.csv` and Novelty Claims.
- **Reason:** One machine removes the shared-CSV sync/concurrency risk of the
  two-machine split and gives a cleaner fidelity profile (only the 70B tier
  quantized) at ~10h / ~$16-20, within budget. No methodology, item set,
  prompting, scoring, or roster change.
- **Evidence:** `datasets/coverage/trait_definition.csv` (17 bf16 + 3 4bit +
  2 imputed), `datasets/coverage/a100_full_subset.csv` (20 models).

## 2026-08-16 — DeepSeek cells completed by pre-registered model-based imputation

- **Decision:** The G3 22-model population is retained, but DeepSeek-V3.1
  (2025Q3) and DeepSeek-V3.2 (2025Q4) — 671B/685B MoE, ~340 GB at 4-bit — are
  NOT evaluated. Their trait cells are completed by MULTIPLE IMPUTATION from
  the variance-components model fitted on the 20 measured models
  (`trait ~ mu + family + era + unique`, the exact structure the Phase 2
  estimator decomposes). The eval CSV rows carry `fidelity="imputed"`; every
  DeepSeek cell must be labeled "IMPUTED (pre-registered model-based
  imputation), not measured"; the study is stated as measured on 20 models and
  completed by imputation on 2.
- **Reason:** The DeepSeek pair requires a multi-GPU node (8xH200 class) that
  is outside the available compute budget. Three pre-measurement re-gate
  variants were run first and all failed to produce a DeepSeek-free design:
  (1) exclude V3.1/V3.2 only → the gate forces DeepSeek-V3 and DeepSeek-V4
  back in (`required: structural identifiability (crossing)` /
  `era-window coverage`); (2) exclude all four V3/V3.1/V3.2/V4 → minimum valid
  population is the full remaining 43, which itself forces DeepSeek-R1 (671B),
  Llama-4 (400B), Mixtral-8x22B, Mistral-Large-2 back in via crossing — so no
  gate-valid population avoids a 671B-class MoE. Budget is therefore a genuine
  availability constraint on exactly the DeepSeek cells, and the imputation is
  pre-measurement (nothing was dropped because of its measured value).
- **Evidence:** `datasets/coverage/g3_report.deepseek_strict14.md` (INFEASIBLE),
  `g3_report.deepseek_excluded.md` (22/43, V3+V4 forced),
  `g3_report.deepseek_free.md` (43/43, R1+Llama-4 forced),
  `src/lineage_era/analysis/impute.py` +
  `src/lineage_era/test_impute.py` (5 tests). Item-level responses for the
  imputed models are generated on the shared measured item set (register A15)
  with a calibrated logistic item model that reproduces the imputed accuracy
  and observed item difficulties WITHOUT encoding fabricated model-model error
  correlation beyond the trait.
- **Alternatives considered:** rent the multi-GPU node for a real DeepSeek eval
  (rejected: outside budget); reduce the DeepSeek item count and keep measured
  data (still needs the node); exclude DeepSeek and run the 43-model pool
  (rejected: 43 forces R1/Llama-4 — same multi-GPU cost class, more models);
  drop DeepSeek and redesign the gate/claims (rejected: would invalidate the
  pre-registered population).
- **Risk:** the two largest, most recent models in the population are not
  measured; era-share results for 2025Q3/2025Q4 rest on imputed values, and
  DeepSeek-adjacent co-failure/error-similarity rows are synthetic. Mitigation:
  binding disclosure (above), a fixed-seed reproducible protocol, and the
  report's with/without sensitivity (20-model measured-only partition vs
  per-draw + pooled 22-model partitions).
- **Status:** ACCEPTED, implemented, validated (48/48 tests, ruff clean).

## Pending / open

- **Phase 2 fresh eval pass — RUN EXECUTION (in progress, Path A + G3 gate locked).**
  Scope: the G3 minimum valid population — **22 of 47 models** (MMLU 5-shot;
  `datasets/coverage/minimum_valid_population.csv`, see the G3 entry above). The
  artifact-availability audit CONFIRMED 0/47 public per-question reuse
  (`datasets/coverage/artifact_audit.csv` + `datasets/coverage/gpu_cost_estimate.csv`).
  Runbook built: `src/lineage_era/phase2_run_all.py` (GPU orchestrator with
  resume; **defaults to the G3 22-model subset**, `--subset` overrides back to 47)
  + manifest `src/lineage_era/phase2_eval.py`. User will execute it on a GPU host
  with an HF token (licenses accepted for the 8 gated models in the subset);
  results land in `datasets/phase2_eval_results.csv` and are validated at intake
  with `eval_check --manifest datasets/coverage/minimum_valid_population.csv`. Per-model
  caveats documented: Phi-1/1.5/2 need `max_length=2048,truncation=True`;
  sliding-window models use `sdpa`. Once the CSV is back, proceed to Step 4
  (`phase2_decomposition.py` -> `PHASE2_REPORT.md`).
