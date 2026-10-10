# Recommended corrections (smallest defensible set)

Nothing here changes a reported number. The audit found no error in the headline result, its intervals, or any of the 12 pre-specified analyses. Issue IDs refer to `ISSUE_REGISTER.csv`. Replacement wording is given only where a change materially improves accuracy; everything else is left to the authors.

## A. Mandatory before submission

| # | Issue | Where | Replace with |
|---|---|---|---|
| 1 | ISS-01 | §III-C | *Current:* "...the samples were frozen with SHA-256 hashes before any prediction was downloaded." → *Proposed:* "...the samples were frozen with SHA-256 hashes before the bulk download of predictions; only the reference model, whose answers supply the answer key for newer storage layouts, had been fetched earlier." |
| 2 | ISS-02 | §III-A | *Current:* "...extracted accuracy also equals the leaderboard's official aggregate (43.80)." → *Proposed:* "...its extracted accuracy, averaged over the 57 subjects as the leaderboard does, equals the official aggregate (43.80); the item-level accuracy used below is 42.76." |
| 3 | ISS-03 | Abstract; §III-C | Introduce the counts once as "leaderboard entries" ("590 leaderboard entries, 563 distinct repositories"); the Data Quality paragraph already explains the duplicates. |
| 4 | ISS-11 | §III-A and §V | Expand "MMLU" at first body use and "confidence interval (CI)" at first body use (IEEE Access requires definitions in the body even if given in the abstract). |
| 5 | ISS-15 | Biographies; first page | Authors supply the degree names for Shree Harish V and Lavanya R; the submitting author needs an ORCID; DOI/volume/date fields are publisher-filled template text. |
| 6 | ISS-14 | Acknowledgment | Authors confirm that the stated level of AI use is accurate and ask the editorial office whether a citation to the AI system is expected in the drafted sections as well as in the Acknowledgment. |
| 7 | ISS-23 | Data Availability | Run `scripts/download_ollb_v1.py` and `scripts/validation_report.py` once more in a clean environment and record the exit codes; the statement that everything regenerates rests on the 9 Oct run plus this audit's partial re-test (3 of 977 models re-extracted; metadata, roster, frozen hashes and sampling reproduced). |

## B. Strongly recommended (a reviewer is likely to raise these)

| # | Issue | Proposal |
|---|---|---|
| 8 | ISS-04 | Report the root-bootstrap interval beside the headline: "13.3 points (jackknife 95% CI 10.8–15.8; root bootstrap 11.4–19.6)" in the abstract or §V-B, and add one sentence: "one root accounts for most of the jackknife variance; removing both largest roots gives 15.9 points (12.8–19.1)". The second number is a new post-hoc result (audit, reproducible with `audit/tools/independent_checks.py`) and favours the paper. |
| 9 | ISS-05 | Add a post-hoc robustness row: "Controlling for a shared uploader account (+6.8 points for same-uploader pairs), the shared-root coefficient is 12.9 (jackknife SE 1.1); excluding the 140 same-root pairs that share an uploader gives 12.3." Update Table III ("same-root-organisation predictor") accordingly: it is a different predictor, so keep "Not done" for same root organisation, but state that same uploader was examined. |
| 10 | ISS-12 | In `analysis.load_population`, compare each file's accuracy with the manifest accuracy (or store a sha256 in the manifest) and raise on mismatch; add a test using `audit/tools/repro_gate_limit.py` as the template. Needed if the README keeps describing the loader as fail-closed. |
| 11 | ISS-13 | Promote the brute-force Eq. 3 check, the jackknife refit and a toy end-to-end pipeline into `src/lineage_era/test_*.py`. |

## C. Optional polish

* ISS-06: add "46 of the 63 roots contribute fewer than 10 same-root pairs each (77 pairs in total)" next to the 25.3 and 16.6 figures.
* ISS-07: retitle the Discussion paragraph "Why lineage may matter more than release timing".
* ISS-08/09: "…within 0.6 points of zero in the pre-specified model…"; "Neither timing measure alone shows a positive association in the pre-specified model."
* ISS-10: "about forty minutes" instead of "an hour" before the fixed specification.
* ISS-16: add `INVALID_DO_NOT_USE.md` to `datasets/eval_samples/` and `results/phase2_empirical/`.
* ISS-17: add `scripts/compare_rosters.py` to the runbook before `download_ollb_v1.py` (it implements seed 0, cap 40).
* ISS-18: pin `huggingface_hub`, `pyarrow`, `tabulate`, `pytest` or add a lock file.
* ISS-19: plain tick labels in Fig. 7 (no mathtext exponents); enlarge text in supplement Figs. S2 and S5; consider +0.5 pt in Figs. 4, 6, 9, 11.
* ISS-20/21/22: float64 or suppressed warnings; note the 973-file effect of case-insensitive filesystems; fast-forward local `main`.

## D. What should *not* change

* The observational framing, the explicit "not preregistered" wording in the abstract, Table III, the disclosure of every post-hoc analysis, S7's evidence labels, the AI disclosure's content (system, sections, level), and the narrow novelty claim. These are accurate and are among the paper's strengths.
