# Lineage or Era?

**Lineage and Release Timing in Correlated Errors of Open-Weight Language Models: A Pair-Level Study**

*IEEE Access manuscript in preparation (14 pp. + 6 pp. supplement)*

Sudharsan S · S. Kanaga Suba Raja · Shree Harish V · Chin-Shiuh Shieh · Mong-Fong Horng · Lavanya R
SRM Institute of Science and Technology, Tiruchirappalli · National Kaohsiung University of Science and Technology

[![Manuscript](https://img.shields.io/badge/manuscript-14_pages-blue)](paper/build/ieee_access_manuscript.pdf)
[![Venue](https://img.shields.io/badge/target-IEEE_Access-00629B)](paper/build/ieee_access_manuscript.pdf)
[![Status](https://img.shields.io/badge/status-in_preparation-orange)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-not_yet_specified-lightgrey)](docs/release/LICENSING_NOTES.md)

---

## The question

When two public language models are both wrong on a question, they often choose the same
wrong answer. Is that associated more with shared **lineage** (one is fine-tuned from the
same base model as the other) or with **release timing** (they were published at about the
same time)? The two are entangled, because fine-tunes always appear after their bases.

## What we did

1. **Design diagnosis.** A per-model variance decomposition (family vs. release-era
   components) is identified but far too imprecise with the 5–7 families and ≤ 14 quarters
   real populations offer: worst-case share RMSE ≥ 0.18 in every design examined
   (supplementary material).
2. **Pair-level design.** For every pair of models we measure
   `a_ij = P(same wrong option | both wrong)` on MMLU (14,042 items) and regress it on a
   shared-lineage indicator, release-month-gap bins and both models' accuracies, with
   dyadic cluster-robust inference. Analysis, sample rules and a simulation gate were fixed
   in a dated analysis plan before any pair outcome was computed (pre-specified in this
   repository; not deposited with an external registry).
3. **Data.** Item-level predictions from the first Open LLM Leaderboard, validated item by
   item against the leaderboard's stored correctness: 977 accepted models in two
   overlapping populations (primary 590, expanded 928), lineage resolved from Hugging Face
   `base_model` declarations.

## What we found

| | Primary sample (590 models, 173,755 pairs) |
|---|---|
| Shared lineage root | **+13.3 points** (jackknife 95% CI 10.8–15.8); 11.7–13.4 across all 12 pre-specified analyses |
| Lineage dose-response | parent–child +18.5, distance 2 +13.6, more distant +11.5 points |
| Heterogeneity | present in each of the 7 largest base-model families (10.3–14.8) and all 57 MMLU subjects |
| Same release month vs. 12+ months, net of accuracy | +0.4 points; 90% interval excludes effects above 1.1 points; not stable in sign across specifications, also when timing is measured by the base model's release month |
| Same release month, unadjusted | +8.7 points, accounted for by accuracy similarity |
| Item-difficulty-aware nulls | average excess agreement ≈ 0; lineage contrast unchanged |

The results hold after removing duplicate leaderboard entries and degenerate models, and
after removing models whose config files contradict their declared lineage. They are
observational and come from one benchmark and a population dominated by community
fine-tunes; see the manuscript's limitations section.

## Repository

| Path | Contents |
|---|---|
| `paper/` | Manuscript and supplement source (`src/`), figures, generated tables, IEEE class files, `Makefile`; compiled PDFs in `paper/build/` |
| `src/lineage_era/ollb/` | Leaderboard pipeline: Hub metadata, lineage rosters, extraction and validation, pair gate, analysis |
| `src/lineage_era/analysis/` | Per-model precision analysis (crossed REML, expected information, Monte Carlo) |
| `scripts/` | Entry points: `run_exp04_final.py`, `run_exp04_item_null.py`, `run_pair_gate_audit.py`, `run_exp04_revision2.py`, `run_exp04_heterogeneity.py`, `make_exp04_tables.py`, `make_exp04_figures.py`, … |
| `results/` | Committed analysis outputs that every reported number and table is generated from |
| `datasets/ollb/frozen/` | Frozen model lists (public versions; see licensing below) |
| `docs/05_Experiments/Exp04_Leaderboard_Lineage_Era.md` | Analysis plan and its three dated amendments |
| `docs/REPRODUCIBILITY_CHECKLIST.md` | Environment, data sources, seeds and the full reproduction sequence |
| `docs/08_Reviews/` | Revision log, including errata |
| `paper/src/archive/`, `master/` | Superseded 16-model version (not used for inference) |

## Reproducing

```sh
python -m pip install -e ".[test,ollb]"
python -m pytest
```

The full sequence (regenerating the leaderboard metadata and answer files, rebuilding the
frozen lists against their recorded SHA-256 hashes, re-running every analysis, then
`make -C paper tables figures && make -C paper`) is in
[`docs/REPRODUCIBILITY_CHECKLIST.md`](docs/REPRODUCIBILITY_CHECKLIST.md).

## Data and licensing

The Open LLM Leaderboard's per-item details and metadata declare no licence. The derived
item-level answer files and three copied metadata fields are therefore **not** in this
repository; scripts regenerate them from the public source and verify them byte for byte.
A licence for the code has not yet been chosen; see
[`docs/release/LICENSING_NOTES.md`](docs/release/LICENSING_NOTES.md).

## Earlier version

An earlier 16-model version of this project reported an identifiability gate and
item-level results that are withdrawn: the gate tested the wrong model, and an extraction
bug made every item-level prediction constant. Section S2 of the supplement and
`docs/08_Reviews/Revision_2026-10_Precision_Gate.md` record what changed. That version's
source and PDF are kept in `paper/src/archive/` and in the earlier history of `main`.
