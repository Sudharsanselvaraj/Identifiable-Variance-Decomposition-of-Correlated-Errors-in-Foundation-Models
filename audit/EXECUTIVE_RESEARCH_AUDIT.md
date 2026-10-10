# Executive research audit

**Project:** *Lineage and Release Timing in Correlated Errors of Open-Weight Language Models: A Pair-Level Study*
**Audited state:** GitHub `main` @ `3a6d1dc` (PR #5 merged); tree `febb36233df8` is identical to local branch `fix/figure-review-ieee` @ `d262d2e`. No unpushed commits.
**Date:** 2026-10-10. **Mode:** read-only. Nothing was pushed, merged, committed, reset or deleted. All new files are under `audit/` (untracked).

## Overall verdict

# Ready after minor corrections

**Why this rating, with evidence**

* The headline result **was independently reproduced**: an implementation written from the manuscript's equations, importing nothing from the release, gives a shared-root coefficient of **13.293 points** with jackknife 95% CI **[10.78, 15.80]** (manuscript: 13.3, 10.8–15.8), and reproduces all 12 pre-specified analyses to 1.2e-9, plus phi, CAPA, option-chance, the item-distractor null, WLS and the root-release-month model.
* Data validity was checked at the source: three models, one per storage layout, were re-extracted from the live public leaderboard with separate code — 0 mismatches over 42,126 item rows; 977 of 977 answer files match their recorded accuracy.
* **No critical or major correctness defect** was found in the data pipeline, estimator, inference, tables or figures. The 23 findings are 5 moderate, 16 minor, 2 informational; most are wording or documentation. None changes a reported number.
* It is not rated "Ready for submission" because (i) one chronology sentence is literally false (ISS-01), (ii) one spot-check sentence is misleading (ISS-02), (iii) the full 977-file re-download was not repeated (ISS-23), (iv) two biographies and the template fields are incomplete, and (v) a reviewer will raise the influence of a few roots (ISS-04), which has a ready answer in numbers the audit computed.

## Scientific contribution

A large, carefully validated, pair-level observational estimate that models descended from the same declared base choose the same wrong MMLU option about 13 percentage points more often (42.3% mean agreement) than unrelated models of equal accuracy and release gap, and that release proximity has only small, specification-dependent associations once accuracy is controlled. It is narrower than the first-ever claim ("to our knowledge … first to examine declared ancestry and release proximity jointly") and honestly bounded: observational, one benchmark, no ensemble test.

## Most serious correctness risks (all moderate or below)

1. **Influence of few roots** (ISS-04): 68.6% of the jackknife variance comes from deleting one root; the root bootstrap interval is asymmetric (11.4–19.6). Removing both dominant roots *raises* the estimate to 15.9 (CI 12.8–19.1), so the risk is to interval width, not to the sign or size.
2. **Loader does not bind files to models** (ISS-12): a swapped pair of validated answer files passes every gate check (reproducer in `audit/tools/repro_gate_limit.py`). The real data are clean (977/977 accuracies match the manifest). The paper does not depend on the gate's claim; the README does.
3. **Interpretation of "lineage"** (ISS-05, ISS-07): weights, data, uploader and recipe are not separable. A same-uploader control (+6.8 points for same-uploader pairs) leaves the lineage coefficient at 12.9.
4. **Statements that overreach slightly**: the freeze chronology (ISS-01), the accuracy spot check (ISS-02), "590 models" counting entries (ISS-03), and three interpretive phrases (ISS-07/08/09).
5. **Thin tests where the science lives** (ISS-13): 16% coverage of the current-study package; no unit test of the jackknife or validation report. The audit's independent code fills the gap and could be promoted to tests.

## Was the headline result independently reproduced?

**Yes** — from the validated predictions, by independent code (`STATISTICAL_VERIFICATION.md`). Not reproduced independently: the Monte Carlo simulations and about a dozen R-series analyses (listed there; they match committed outputs only).

## Was the full workflow reproduced?

**Partially.** Reproduced today from the public source or a clean clone: leaderboard metadata (hash identical to 9 Oct), roster, frozen-list SHA-256 hashes, seed-0 cap-40 sampling, all tables (byte-identical), both PDFs (text-identical), 14 of 20 figures, 73/73 tests. Not repeated: the full 977-file download (about 11 GB) and `validation_report.py` from scratch (last run by the authors on 9 Oct), and the analysis scripts inside a clean clone (no answer files there; replaced by independent code). Details and exit codes: `REPRODUCIBILITY_AUDIT.md`.

## Submission readiness

Ready after the mandatory corrections in `RECOMMENDED_CORRECTIONS.md` (seven items, five of them wording or author actions). IEEE Access checks that pass: AI disclosure in the Acknowledgment naming system, sections and level; 3–10 keywords (7); 16 pages (under 20); biographies present for all six authors (two incomplete); LaTeX and PDF generated from one source.

## Five highest-priority actions

1. Reword the two inaccurate sentences (freeze chronology, spot-check accuracy) and the "entries" count — ISS-01, 02, 03.
2. Report the root-bootstrap interval and the drop-two-largest-roots estimate next to the headline — ISS-04 (strengthens the paper).
3. Re-run the full download and validation in a clean environment and record the exit codes before submitting — ISS-23.
4. Bind answer files to the manifest (accuracy or hash) and add a jackknife/Eq. 3 test — ISS-12, ISS-13.
5. Complete author biographies, confirm the AI-use statement, and ask the editorial office about citation placement — ISS-14, ISS-15.

## Editorial assessment (Phase 11)

* **Question and gap** are clear (RQ1, RQ2) and the contribution is distinguished from Kim et al. (outcome shared; lineage per model; release timing; dependence-aware inference).
* **Method detail** is sufficient for replication; Eq. 1–3, the plan, and Algorithm S1 are explicit.
* **Results paragraphs** explain meaning, not just numbers; limitations are specific. Three phrases overreach slightly (ISS-07/08/09). The same headline number appears in the abstract, contributions, §V-B, §VI and §VIII; acceptable, but §V-D and §V-E are dense with parenthetical figures and could be shortened.
* **Terminology** is consistent (shared-root coefficient; same-month coefficient; entries vs models is the exception, ISS-03). MMLU and CI are undefined in the body (ISS-11).
* **Captions** are self-contained and name the interval type. No unsupported superiority or generalization claim was found.
* **Literature:** every cited work I could verify exists, with correct authors, venue and pages, and every attributed claim is in the source (21 papers checked against abstracts, full texts, PMLR, ACL, ICLR, NeurIPS pages). Classic textbook and journal references (Dietterich 2000, Kuncheva & Whitaker 2003, Patterson & Thompson 1971, Harville 1977, Searle et al. 1992, Brennan 2001, Fafchamps & Gubert 2007, Cameron et al. 2011, Aronow et al. 2015, Efron 1982, Breiman 2001, Kleinberg & Raghavan 2021, Bommasani et al. 2022, Hendrycks et al. 2021, Gao et al. 2021, Beeching et al. 2023) were **not** re-verified online. No systematic literature search was run, so a claim of "no missing prior work" is not made.

## Withdrawn earlier evaluation (Phase 6)

Distinct and correctly handled: 16 files, all predicting option A on all 14,042 items with one log-likelihood per item; Qwen-7B's 0.2294 equals the all-A share (3,222/14,042); no current script or result reads those files (the S1 precision script reads only model-name labels); the main paper has one sentence plus a pointer to S7, which separates recorded facts, plan, author reports and unknowns. Old data folders lack an in-folder INVALID notice (ISS-16).

## Pre-specification history (Phase 7)

Plan 11:27, OLS specification 12:06, amendment 2 13:09, freeze 13:15, bulk download from 13:46, amendment 3 14:44, first pair outcomes 15:55 (IST, 9 Oct). A history rewrite (to remove an unlicensed file) changed 19 hashes and **no** dates (26/26 preserved). The chronology is real but rests on commit times only, as the paper says; it is not external registration. No evidence was found that the headline analysis was chosen after seeing which result looked strongest (the jackknife was adopted because it is widest).

## Phase checklist

| Phase | Status | Output |
|---|---|---|
| 0 Project state | Done | this file; `PROJECT_INVENTORY.csv` (638 files) |
| 1 Read manuscript and supplement; claim ledger | Done (every section, caption, equation, reference, biography; generated table bodies checked via their generators and numbers) | `CLAIM_EVIDENCE_LEDGER.csv` (62 claims: 30 reproduced, 11 verified, 12 committed-only, 4 author statements, 4 imprecise, 1 partly contradicted) |
| 2 Pipeline | Done | §Reproducibility; issues ISS-01/03/12/21 |
| 3 Independent recomputation | Done | `STATISTICAL_VERIFICATION.md`, `audit/tools/` |
| 4 Methodology | Done | same |
| 5 Figures and tables | Done | `FIGURE_TABLE_AUDIT.md` |
| 6 Withdrawn evaluation | Done | above |
| 7 Prespecification | Done | above |
| 8 Reproducibility | Done; items D/E explicitly not tested | `REPRODUCIBILITY_AUDIT.md` |
| 9 Literature | Done for 21 sources; classic references not re-verified online | ledger C57 |
| 10 IEEE Access | Done from the three current policy pages | ledger C59; ISS-14/15 |
| 11 Editorial | Done (this file) | — |
| 12 Red team | Done | `FINAL_PEER_REVIEW.md` |

Blocked or incomplete, with reasons: full 977-file re-download (time/size; authors' 9 Oct run stands); re-running Monte Carlo simulations; analyses needing untracked `datasets/mmlu_redux`; anonymous (no-token) download.

## Limits and independence of this audit

This audit was performed by **Claude, the same AI system that, per the manuscript's own disclosure, wrote and debugged much of the analysis code and drafted the text**, and which assisted in this working session before the audit began. Independence is therefore limited by construction. Mitigations: the estimand was re-implemented from the manuscript's equations without importing the release; claims were checked against external sources (the live leaderboard, cited papers, IEEE policy pages, git history, a fresh clone of GitHub `main`); every ledger row states what kind of verification it received; and the tools are included so that a human statistician can re-run them (`python3 -W ignore audit/tools/independent_verify.py`, `independent_checks.py`). A human reviewer should treat this audit as strong evidence of arithmetic and pipeline correctness, and as no substitute for human judgement on interpretation.

## Index of files

`EXECUTIVE_RESEARCH_AUDIT.md` (this), `CLAIM_EVIDENCE_LEDGER.csv`, `FIGURE_TABLE_AUDIT.md`, `STATISTICAL_VERIFICATION.md`, `REPRODUCIBILITY_AUDIT.md`, `ISSUE_REGISTER.csv`, `RECOMMENDED_CORRECTIONS.md`, `FINAL_PEER_REVIEW.md`, `PROJECT_INVENTORY.csv`, `PROGRESS.md`, `tools/` (independent_verify.py, independent_checks.py, independent_extraction_check.py, repro_gate_limit.py, build_inventory.py, build_ledgers.py), `outputs/` (JSON results, repro_log.txt, figure_sizes.csv).
