# Lineage or Era?

An identifiability-gated variance decomposition of correlated errors in public language
models.

**One-sentence core question:** Determine whether the observed error-correlation
structure across public LLMs is separably explained by lineage vs. release-era, restricted
to whatever connected subset of the population makes that separation identifiable — and
what that implies for diversification-as-mitigation.

---

## Manuscript / publication (current focus)

The project's primary deliverable is an **IEEE Access** manuscript, now at **19 pages** and
at final submission read state. It is organized under `paper/` into a clean, rebuildable
layout:

| Path | Purpose |
|---|---|
| `paper/` | Submission package |
| `paper/src/` | `ieee_access_manuscript.tex` — the manuscript source |
| `paper/figures/` | 25 figure assets (`.pdf` / `.png`) referenced by the manuscript |
| `paper/support/` | IEEE Access class (`.cls`, `.bst`, `.sty`), embedded fonts (`.pfb/.tfm/.map/.fd`), header logos |
| `paper/tables/` | (reserved) data tables |
| `paper/build/` | Generated build artifacts: `.aux`, `.log`, and the compiled `.pdf` |
| `paper/Makefile` | One-command build: `make` (in `paper/`) → `build/ieee_access_manuscript.pdf` |

The Makefile wires up `TEXINPUTS` / `TEXFONTS` / `TEXFONTMAPS` so the class and embedded
fonts resolve from `support/` during compilation. Rebuild anytime with:

```sh
make -C paper          # builds paper/build/ieee_access_manuscript.pdf
make -C paper clean    # removes generated artifacts
```

## Repo layout

| Path | Purpose |
|---|---|
| `docs/` | Research knowledge base — source of truth for the project (structure under `docs/00_Project` … `docs/09_Roadmap`; see `RESEARCH_PROTOCOL.md`) |
| `paper/` | IEEE Access submission package (see above) |
| `scripts/` | Figure / analysis regeneration scripts (e.g. `regen_figs_8_9.py`, `run_design_space_sweep.py`) |
| `src/lineage_era/` | Simulation / decomposition code (Phase 0–2) |
| `src/lineage_era/analysis/` | Phase 2 analysis package (trait, metadata, population, identifiability, reml, bootstrap, plots, report) |
| `results/` | Phase 2 engine outputs: `phase2_empirical/`, `phase2_sim_dryrun/`, `design_space/` |
| `datasets/` | Item-level data; `phase2_eval_results.csv` (16-model empirical set) and `.sim` dry-run set |
| `notebooks/` | Analysis notebooks (empty at present) |
| `supplement/` | Supplementary material (reserved) |
| `requirements.txt` | Python dependencies |

## Analysis package (module map)

Top-level package modules are re-export shims for compatibility; the real code lives in
`src/lineage_era/analysis/`:

| Module | Purpose |
|---|---|
| `trait.py` | Aggregate per-question responses into a continuous per-model trait |
| `eval_check.py` | Eval intake validator — fails fast if the GPU-runbook CSV/samples are mis-shaped |
| `eval_simulate.py` | Shape-exact simulated eval output for GPU-free pipeline dry-runs |
| `metadata.py` | Family/era design matrix from the Phase 0 table + verified `base_model` edges |
| `population.py` | Connected-subset population construction (erosion, gating, membership) |
| `identifiability.py` | Identifiability pre-checks (κ, rank, VIF, profile flatness) before any fit |
| `reml.py` | CrossedREML estimator (σ²_L, σ²_E, σ²_U) + θ_P/θ_M decomposition layer |
| `bootstrap.py` | Bootstrap CIs over models; sensitivity grid |
| `plots.py` | Partition, era-convergence, and diagnostics figures |
| `report.py` | Report generation + partition/summary tables |

## Standing rules

- No analysis code or data pulls before the plan for that step is approved.
- Every citation is independently verified before it enters any document.
- Lead with the decomposition instrument and the identifiability gate; quantitative-genetics
  language is Phase 3 scaffolding only.

## Status

- **Phase 0** (population) — done.
- **Phase 1** (simulation) — complete.
- **Phase 2** (instrument + empirical) — built and verified; intake validator and
  shape-exact simulated dry-run (`results/phase2_sim_dryrun/`) pass. Empirical analysis
  runs on the 16-model `datasets/phase2_eval_results.csv` set.
- **Manuscript** — IEEE Access submission at 19 pages, final read state; rebuild from
  `paper/` via `make`.

## Contributing

This repository is shared; please coordinate changes to `paper/`, `docs/`, and `results/`
to avoid conflicting edits. Commit with clear, single-purpose messages and run
`make -C paper` after any manuscript change to confirm the PDF still builds.
