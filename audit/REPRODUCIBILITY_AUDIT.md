# Reproducibility audit

Candidate: `origin/main` = 3a6d1dc (PR #5 merge); tree hash febb36233df8… is identical to the working branch `fix/figure-review-ieee` @ d262d2e. No unpushed commits. All experiments below were run in an **isolated clone** (`scratchpad/auditclone`, cloned from GitHub `main`) or in `audit/`; the source repository was not modified (`git status` shows only untracked `audit/` and the pre-existing untracked files).

## Environment

macOS 26.6.2 arm64 (APFS, case-insensitive), Python 3.11.7, numpy 2.1.3, pandas 3.0.5, scipy 1.17.1, matplotlib 3.9.2, pyarrow 25.0.0, huggingface_hub 0.36.2, pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026). Network available; a Hugging Face token exists locally but public leaderboard files return the same redirect with no header, with `Bearer None` and with an invalid token.

## A. What can be regenerated from committed files alone (clean clone, no downloaded data)

| Command (repo root of the clone) | Exit | Evidence |
|---|---|---|
| `PYTHONPATH=src python3 -m pytest -q -p no:warnings` | 0 | **73 passed in 28.4 s** (full suite incl. 2 slow tests) |
| `make -C paper tables` | 0 | 0 files differ from the committed tables |
| `make -C paper` | 0 | manuscript 16 pp., supplement 15 pp.; `pdftotext` of both rebuilt PDFs **identical** to the committed PDFs |
| `PYTHONPATH=src python3 scripts/make_exp04_figures.py` | **1 (by design)** | draws 14 of 20 figures byte-identically; skips `agreement, rawadj, heatmap, gap, detection, accuracy` and prints the steps that restore them |
| `PYTHONPATH=src python3 -m pytest --cov=lineage_era.ollb` | 0 | coverage of the current-study package **16%** (analysis.py 68%, pair_gate.py 76%; fetch_v1, roster, roster_v1, config_lineage, hub_meta 0%) |

## B. What requires external data retrieval (public Hugging Face sources)

| Command | Exit | Evidence |
|---|---|---|
| `python3 scripts/fetch_v1_contents_meta.py` | 0 | 7,260 rows; SHA-256 `84fc02f993a0…` equals the value recorded on 9 Oct (the live table is unchanged) |
| `PYTHONPATH=src python3 -m lineage_era.ollb.roster_v1` | 0 | 721 primary / 1,295 expanded eligible; exclusion counts equal the paper's (4,843 / 1,637 / 1,209 / 776 / 385 / 339 / 56) |
| `PYTHONPATH=src python3 scripts/rebuild_frozen_lists.py` | 0 | four `OK … matches the frozen hash` lines |
| `PYTHONPATH=src python3 scripts/compare_rosters.py` | 0 | the seed-0, cap-40 sampling regenerates all four recorded SHA-256 hashes; `results/exp04_rosters/*` unchanged |
| `python3 audit/tools/independent_extraction_check.py` (own reader, 3 models × 14,042 items, one per storage layout, 5 min 8 s) | 0 | 0 mismatches vs the stored answer files in prediction, correctness-vs-leaderboard-flag and answer key; run ids equal |
| Independent statistics (`independent_verify.py`, `independent_checks.py`) | 0 | reproduce all 12 analyses to 1.2e-9 (see STATISTICAL_VERIFICATION.md) |

## C. Credentials or paid infrastructure

None are needed for the current study. The earlier per-model evaluation (not used for results) required a rented A100 GPU; it cannot be rerun and is documented as such (S7).

## D. Not tested in this audit

* `scripts/download_ollb_v1.py` for all 977 models (about 11 GB of range reads) and `scripts/validation_report.py` from scratch. Last full run: the authors, 9 Oct 2026 (the README/checklist states exact reproduction). The independent check of 3 models and the matching manifest accuracies (977/977 files equal their recorded accuracy to 1e-16) support the stored files but do not replace a full re-download.
* An anonymous (no token) full download: the fetcher's rate-limit handling assumes the authenticated 5,000-requests-per-5-minutes window.
* `scripts/run_exp04_final.py`, `run_exp04_item_null.py`, `run_exp04_revision2.py`, `run_exp04_revision3.py`, `run_exp04_heterogeneity.py`, `run_exp04_matched_followup.py`, `run_pair_gate_audit.py` in the clean clone (no answer files there). Their central quantities were reproduced by independent code instead; the Monte Carlo audits and R-series items listed in STATISTICAL_VERIFICATION §6 were not re-run.
* `datasets/mmlu_redux/` (untracked, fetched separately) analyses.
* Other platforms and Python versions.

## E. What cannot currently be reproduced

* The earlier per-model evaluation (no raw `lm-eval` output survives; stated in S7).
* Exact external timestamps of the analysis plan (no registry deposit; commit times only).

## Findings (details in ISSUE_REGISTER.csv)

* **Fail-closed gate works as described** for item order, gold, hashes, length, option range and manifest status (15 tests), but **does not bind a file to its model**: the manifest stores accuracy and no hash, and the loader never compares them. Reproducer `audit/tools/repro_gate_limit.py` swaps two validated models' files (a 126M model scores 79%, a 70B model 24.6%) and every check passes (ISS-12). The real data are clean (977/977 equal).
* Test coverage is thin where the science lives: no unit test of the jackknife, the validation report, the fetcher, the roster or the lineage resolver (ISS-13).
* The runbook does not name `scripts/compare_rosters.py`, the only implementation of the documented sampling rule (ISS-17); dependencies in the retrieval path are unpinned and there is no lockfile (ISS-18).
* On a case-insensitive filesystem 977 validated models occupy 973 files: four case-variant pairs (e.g. `Facebook/OPT-125M` and `facebook/opt-125m`) are one Hub repository with identical run ids (ISS-21).
* Stale-artifact risk is low: `make -C paper` rebuilds PDFs from committed tables and figures, and the rebuilt text equals the committed PDFs; tables and 14 figures regenerate byte-identically. The committed PDFs are tracked and updated by the build.
* numpy prints spurious `divide by zero / overflow / invalid value in matmul` warnings from float32 matrix products on macOS Accelerate; results equal float64 independent code (ISS-20).

## Status line

* Full workflow reproduced end to end from the public source: **partially** (everything except the bulk download/validation of all 977 files today).
* Headline numerical result reproduced from validated predictions by independent code: **yes**.
* Tables and PDFs regenerated from committed outputs: **yes**. Figures: **14 of 20 without data (tested in the audit); 20 of 20 with the validated answer files (run earlier in the same working session, before this audit began, byte-identical; not repeated inside the audit)**.
