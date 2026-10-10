# Corrections applied after the audit

Branch `fix/audit-corrections` (from `3a6d1dc`, = GitHub `main`). Nothing committed or pushed yet.
Status: **done** = edited; **pending run** = edited, but the step that regenerates committed outputs
still has to be run (see "Commands still to run"); **author** = only the authors can do it.

| Issue | Status | What changed |
|---|---|---|
| ISS-01 freeze chronology | done | §III-C: frozen "before the bulk download of predictions; only the reference model … had been fetched earlier" |
| ISS-02 spot-check accuracy | done | §III-A: 43.80 is the 57-subject average; item-level accuracy 42.76 stated |
| ISS-03 entries vs models | done | Abstract "590 leaderboard entries"; §III-C sentence "563 distinct repositories"; README |
| ISS-04 influence of few roots | done (numbers from audit; pending run of the repo script) | §V-E Inference: 69% / 86% of jackknife variance; without the two largest roots 16.0 (12.8–19.1); Limitations; Supplement S6 subsection; `scripts/run_exp04_audit_followup.py` |
| ISS-05 same uploader | done (same) | §V-E Controls: +6.7 (4.0–9.5), shared root 12.9 (10.8–15.1), excluding 140 pairs 12.3 (10.5–14.1); Discussion "Relation to earlier evidence"; Table III row; Supplement S6 incl. expanded sample |
| ISS-06 per-root mean | done | §V-G: 46 of 63 roots have <10 same-root pairs (77 pairs) |
| ISS-07 Discussion heading | done | "Why lineage may matter more than release timing" |
| ISS-08 / ISS-09 scope | done | "in the pre-specified model" added in §V-C and §V-D (both sentences) |
| ISS-10 "an hour" | done | "about forty minutes" |
| ISS-11 MMLU / CI | done | MMLU expanded in the Introduction (first body use); "95% confidence intervals (CIs)" in §IV-E |
| ISS-12 loader binding | done; **pending run** | `validation_report.py` writes `pred_sha256`; `analysis.choice_matrix` refuses files whose hash or accuracy differs from the manifest. The committed manifest must be regenerated (the loader now stops until it is) |
| ISS-13 tests | done | 3 new tests in `test_ollb_analysis.py` (swap, edit, missing hash column); new `test_ollb_inference.py` (jackknife vs literal refits, zero-variance case, toy end-to-end). `pytest -m "not slow"`: 77 passed |
| ISS-14 AI statement | partly; **author** | Acknowledgment now also names the pre-submission reproduction check. Authors confirm the level of use and ask the editorial office about citation placement |
| ISS-15 biographies | **author** | Degree names for Shree Harish V and Lavanya R; submitting author's ORCID |
| ISS-16 invalid data | done | `INVALID_DO_NOT_USE.md` in `datasets/eval_samples/` and `results/phase2_empirical/` |
| ISS-17 runbook | done | `compare_rosters.py` and the new follow-up script in README and checklist; stale "Pre-Registered" title in the checklist corrected |
| ISS-18 pins | done | `tabulate==0.9.0`, `pytest==9.1.1`, `huggingface_hub==0.36.2`, `pyarrow==25.0.0` in requirements.txt and pyproject.toml |
| ISS-19 figure text | done; **pending run** | Fig. 7 ticks "100"/"10k"; Fig. S5 x ticks 7.5 pt; Fig. S2 group labels without subscripts, criterion labels 8 pt. Figures must be regenerated (needs the manifest) |
| ISS-20 warnings | done | The flags come from macOS Accelerate matmul for any dtype (a random float64 product raises them and equals einsum exactly), not from float32. Silenced with `np.errstate` in `analysis.pair_outcomes`, `run_exp04_final.jackknife_roots` and the follow-up script; outputs byte-identical |
| ISS-21 973 files | done | Note in README and checklist |
| ISS-22 local main | done | fast-forwarded `af2f04d..3a6d1dc` |
| ISS-23 full re-download | **found a bug; rerun in progress** | A clean-room run of `download_ollb_v1.py` failed at its first step (exit 2): `fetch_v1.fetch_model` loaded the reference answer file before parsing any model, including the reference itself, so an empty `datasets/ollb/v1/` could never be filled. Fixed (reference loaded only for lighteval-layout runs); checklist notes the fix |

## New finding during the corrections

ISS-24 (moderate, fixed): the documented pipeline could not start from an empty answer-file
directory (above). The 9 October run worked only because the reference file had been fetched
before the freeze — the same file behind ISS-01.

## Update, 10 Oct 20:40 IST

All three regeneration steps have now run. The manifest differs from the committed one only by the
`pred_sha256` column (977 validated, 921 distinct hashes: identical-prediction entries share one).
`run_exp04_audit_followup.py` reproduces every number added to the text. Only Figs. 7, S2 and S5
changed; the other 17 figures are byte-identical. `pytest`: 79 passed. `repro_gate_limit.py` now
raises `not_the_validated_file`. IEEE 17 pp., supplement 16 pp., master 26 pp., no undefined
references. Still open: the full clean-room download (running) and the author items ISS-14/15.

## Commands that were blocked (since run)

```
PYTHONPATH=src python3 scripts/validation_report.py          # adds pred_sha256 to the manifest
PYTHONPATH=src python3 scripts/run_exp04_audit_followup.py   # writes results/exp04_audit_followup/
PYTHONPATH=src python3 scripts/make_exp04_figures.py         # Figs. 7, S2, S5
make -C paper && python3 scripts/make_master_manuscript.py
PYTHONPATH=src python3 audit/tools/repro_gate_limit.py       # must now raise ValueError
```

After the first command, `per_model.csv` should differ from the committed one only by the new
`pred_sha256` column, and `report.md` only by its commit line.
