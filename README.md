# Lineage or Era?

An identifiability-gated variance decomposition of correlated errors in public language
models.

**One-sentence core question:** Determine whether the observed error-correlation
structure across public LLMs is separably explained by lineage vs. release-era, restricted
to whatever connected subset of the population makes that separation identifiable — and
what that implies for diversification-as-mitigation.

## Repo layout

| Path | Purpose |
|---|---|
| `docs/` | Research knowledge base — the source of truth for the project (structure under `docs/00_Project` … `docs/09_Roadmap`; see `RESEARCH_PROTOCOL.md` for the stage-gated execution plan) |
| `MASTER_PROMPT.md` | Execution master prompt; phase status; Phase 0 log (HF-verified) |
| `proposal.md` | Full research proposal draft (sections 1–14) |
| `notebooks/` | Analysis notebooks (Phase 1 onward) |
| `src/lineage_era/` | Simulation / decomposition code (Phase 1 onward) |
| `src/lineage_era/analysis/` | Phase 2 analysis package (trait, metadata, population, identifiability, reml, bootstrap, plots, report) |
| `src/results/phase2/` | Phase 2 engine outputs (battery, synthetic dry-run, final report) |
| `datasets/` | Item-level data; `phase2_eval_results.csv` lands here from the GPU eval run |

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
| `report.py` | `PHASE2_REPORT.md` generation + partition/summary tables |

## Standing rules

- No analysis code or data pulls before the plan for that step is approved (Phase 0 done;
  Phase 1 run — GO WITH CHANGES, see `PHASE1_REPORT.md`).
- Every citation is independently verified before it enters any document.
- Lead with the decomposition instrument and the identifiability gate; quantitative-genetics
  language is Phase 3 scaffolding only.

## Status

- Phase 0 (population) DONE. Phase 1 (simulation) COMPLETE — GO WITH CHANGES.
- Phase 2 instrument BUILT and verified (battery all pass; synthetic dry-run identical;
  G1 PASS with changes). **Awaiting the fresh-MMLU eval on a GPU host** — drop
  `datasets/phase2_eval_results.csv` back into the repo, then run
  `python3 -m lineage_era.phase2_decomposition` (see `RESEARCH_PROTOCOL.md`, Stage 2).
  G2 pending.
- The intake validator (`analysis/eval_check.py`) checks the eval CSV + per question
  samples against the 47-model contract and aborts with a precise message on any
  violation; a shape-exact simulated-eval dry-run (`analysis/eval_simulate.py` +
  `results/phase2_sim_dryrun/`) exercises the full real-data path GPU-free.
