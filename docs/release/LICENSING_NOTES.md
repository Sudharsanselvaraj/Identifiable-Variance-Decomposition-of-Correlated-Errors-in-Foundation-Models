# Licensing notes (prepared 2026-10-09; decisions pending)

## Proposed code licence
MIT (draft: `docs/release/LICENSE-MIT.draft`), covering the authors' original
code in `src/` and `scripts/`. **Not in effect** until:

- [ ] every co-author approves (Sudharsan S, S. Kanaga Suba Raja, Shree Harish V,
      Chin-Shiuh Shieh, Mong-Fong Horng, Lavanya R);
- [ ] SRM Institute of Science and Technology and National Kaohsiung University of
      Science and Technology IP / open-source policies are checked (they may
      determine the copyright holder);
- [ ] the copyright line is filled in.

## Runtime dependencies (not redistributed)
numpy, scipy, pandas, statsmodels (BSD); matplotlib (PSF-based); tabulate, pytest
(MIT); pyarrow, huggingface_hub, requests (Apache-2.0). All permissive and
installed separately; compatible with an MIT licence for our code.

## Excluded from the code licence (third-party material in the repository)
| Path | Owner / terms | Action needed |
|---|---|---|
| `paper/support/`, `docs/07_Paper/ieeeaccess_support/`, `IEEEtran.cls` | IEEE Access LaTeX template: class, bibliography style, fonts (`.pfb/.tfm/.map/.fd`), logos and placeholder author images | Check the template's redistribution terms (especially the fonts) before publishing the repository; otherwise remove and document how to obtain the template |
| `datasets/kim/` | Kim et al., CC BY 4.0 | Keep with attribution |
| `datasets/ollb/roster.csv` | derived from `datasets/kim/hugging_face.csv` (CC BY 4.0) | Keep with attribution |

## Third-party data not redistributed
| Data | Terms | Handling |
|---|---|---|
| Open LLM Leaderboard (v1) per-item details | none declared | regenerate: `scripts/download_ollb_v1.py` |
| Open LLM Leaderboard (v1) contents metadata | none declared | regenerate: `scripts/fetch_v1_contents_meta.py`; full frozen lists rebuilt by `scripts/rebuild_frozen_lists.py` (hash-verified) |
| MMLU | MIT | not copied |

Exact private copies of the regenerated inputs, with SHA-256 hashes and retrieval
dates, are kept outside version control in `private/exp04_input_snapshot/`.

## Still to decide
- Per-model aggregate accuracies derived from leaderboard predictions appear in
  `results/exp04_validation/per_model.csv` and `datasets/ollb/fetch_v1_log.jsonl`.
  They are computed statistics rather than copied records, but come from data with
  no declared licence; decide before publishing.
- The manuscript's own licence is set by the publisher's copyright form.
