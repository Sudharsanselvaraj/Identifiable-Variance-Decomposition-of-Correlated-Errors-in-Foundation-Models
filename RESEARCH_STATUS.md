# Research status

Last updated 2026-10-10. This page says which files in the repository are the
current study and which are history.

## Current study

**Lineage and Release Timing in Correlated Errors of Open-Weight Language
Models: A Pair-Level Study.** When two open-weight models both answer an MMLU
question wrongly, how often do they choose the same wrong option, and how is
that associated with shared declared lineage and with release timing?

| What | Where |
|---|---|
| Manuscript (IEEE Access) | `paper/src/ieee_access_manuscript.tex` → `paper/build/ieee_access_manuscript.pdf` |
| Supplement | `paper/src/supplement.tex` → `paper/build/supplement.pdf` |
| Single-column version (other journals) | generated from the IEEE source: `master/` |
| Analysis plan and three amendments | `docs/05_Experiments/Exp04_Leaderboard_Lineage_Era.md` (chronology: `docs/REPRODUCIBILITY_CHECKLIST.md` §5) |
| Reproduction runbook | `docs/REPRODUCIBILITY_CHECKLIST.md` |
| Analysis code | `src/lineage_era/ollb/` and `scripts/*exp04*`, `scripts/validation_report.py`, `scripts/download_ollb_v1.py` |

Headline (primary sample, 590 models, 173,755 pairs): same declared lineage
root, +13.3 percentage points of same-wrong-option agreement at equal accuracy
and release gap (delete-one-root jackknife 95% CI 10.8–15.8; pairs weighted
equally, so the two largest roots dominate). Release proximity: small,
specification-dependent associations. Observational; no ensemble was tested.

## Evidence status of the results directories

| Directory | Status |
|---|---|
| `results/exp04_rosters/`, `results/exp04_validation/` | sample freeze (SHA-256) and the validation manifest the analysis reads |
| `results/pair_gate/` | simulation check run before any pair outcome (chose the per-root cap) |
| `results/exp04_analysis/` | the 12 analyses fixed before any pair outcome was computed |
| `results/exp04_final/` | the 12 analyses reproduced and diffed (`prereg/`), plus inference and outcome audits added after the first results |
| `results/exp04_item_null/`, `results/pair_gate_audit/`, `results/exp04_revision2/`, `results/exp04_heterogeneity/`, `results/exp04_revision3/` (R7–R13) | post hoc (review rounds); labelled as such in the manuscript |
| `results/precision_gate/` | per-model precision analysis that motivates the pair-level design (Supplementary S1) |
| `results/phase2_empirical/`, `results/design_space/` | earlier study (below); not evidence for the current one |

## Earlier study (withdrawn)

The repository began as a per-model variance-decomposition study ("identifiable
variance decomposition of correlated errors"), which is why the repository is
named that way. Its item-level predictions were invalid (the extraction code
read only option A's log-likelihood) and its findings are withdrawn or corrected;
Supplementary Section S2 lists each one. A later per-model evaluation on rented
GPUs recorded 16 runs whose per-question outputs are all invalid
(Supplementary Section S7, `docs/08_Reviews/RunPod_Phase2_Audit_2026-10-10.md`).

Files of the earlier study are kept as research history and carry a
"Superseded" notice: the documents under `docs/00_Project/` to `docs/10_Population/`
dated August 2026, `docs/CLAIM_AUDIT.md`, `docs/EVIDENCE_MATRIX.md`,
`docs/FINAL_EVIDENCE_MATRIX.md`, `docs/EMPIRICAL_EVALUATION_VALIDITY_AUDIT.md`,
`docs/PEER_REVIEW*.md`, the old paper in `docs/07_Paper/` and
`paper/src/archive/`, and `master/archive/`. The code paths
`src/lineage_era/analysis/` and `src/lineage_era/phase2_*` belong to it too;
their tests document the extraction bug and the identifiability analysis.

## Open before a public research release

- Licence: not yet chosen (`docs/release/LICENSING_NOTES.md`).
- The analysis plan was versioned in this repository, not registered
  externally; its chronology rests on commit times.
- Raw answer files and the leaderboard metadata copy are not redistributed;
  reproduction needs network access to the public source.
