# Lineage or Era?

**Identifiability-Gated Variance Decomposition of Foundation-Model Performance**

*A design and empirical feasibility study — IEEE Access (19 pp., submission-ready)*

Sudharsan S · S. Kanaga Suba Raja · Shree Harish V · Chin-Shiuh Shieh · Mong-Fong Horng · Lavanya R
SRM Institute of Science and Technology, Tiruchirappalli · National Kaohsiung University of Science and Technology

[![Manuscript](https://img.shields.io/badge/manuscript-19_pages-blue)](paper/build/ieee_access_manuscript.pdf)
[![Venue](https://img.shields.io/badge/venue-IEEE_Access-00629B)](paper/build/ieee_access_manuscript.pdf)
[![Status](https://img.shields.io/badge/status-submission_ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-unspecified-lightgrey)]()

---

## The one-sentence question

Public LLMs fail on the same questions together. Is that because they share **ancestry**
(lineage) or because they were trained in the same **stretch of time** (era) — and can a
real population of models even answer that, or does the confound make it undecidable?

## Why this is harder than it looks

Lineage and era are entangled by construction: a model is always released *after* its
parent, so "shares a family" and "shares a release year" are correlated by default. Before
any variance can be attributed to one or the other, the **population of models being
compared** has to satisfy a structural design condition — crossed, full-rank,
well-conditioned, non-collinear. Most naturally-occurring model populations don't. This
paper is about building the test that tells you *before* you run the analysis, not after.

<p align="center"><img src="paper/figures/fig1_workflow_diagram.pdf" width="640" alt="Workflow diagram"></p>

---

## TL;DR — what we did and what we found

| Step | Result |
|---|---|
| **1. Formalize identifiability** | Five gate conditions a family × era design must satisfy before variance components are estimable: crossing, full column rank, bounded condition number ($\kappa \le 100$), bounded VIF ($\le 10$), connectivity. |
| **2. Validate the estimator (simulation)** | A direct REML estimator recovers ground-truth variance shares to within **2.5 pp** under balanced occupancy and **5.3 pp** under realistic sparse occupancy. |
| **3. Stress-test failure detection** | When family and era are nested (non-identifiable by construction), three independent detectors flag the aliasing in **100% of repetitions**, with **zero silent (undetected) coverage**. |
| **4. Apply the gate to real models** | 16 real foundation models, 5 families, 11 release quarters. The design **fails 4 of 5 gate conditions**: rank 14/15, $\kappa = 4.7\times10^{16}$, infinite VIF. Only connectivity passes. |
| **5. Diagnose the failure** | Structural, not a sample-size problem: Llama is the *only* model in 2023Q1, so its family indicator is numerically identical to that era's indicator. |
| **6. Map the alternative design space** | Systematic sweep of 105 candidate populations found **3** that pass every gate; the best (30 models, 6 families, 8 eras) hits rank 13/13, $\kappa = 93$, VIF $= 2.1$. |

**Bottom line:** the intended lineage-vs-era decomposition is *not* run on the 16-model
population, because it would be uninterpretable garbage-in-garbage-out if it were —
naively fitting it anyway produces variance-share confidence intervals spanning the entire
$[0\%, 100\%]$ range. The contribution is the gate that catches this **before** anyone
publishes a number.

---

## Table of contents

- [Repository layout](#repository-layout)
- [Quickstart](#quickstart)
- [The identifiability gate](#the-identifiability-gate)
- [Data](#data)
- [Reproducing the paper](#reproducing-the-paper)
- [Analysis package (module map)](#analysis-package-module-map)
- [Figures](#figures)
- [Known caveats / invalid artifacts](#known-caveats--invalid-artifacts)
- [Citation](#citation)
- [Standing rules](#standing-rules)
- [Contributing](#contributing)

---

## Repository layout

```
.
├── paper/                  IEEE Access submission package
│   ├── src/                ieee_access_manuscript.tex — manuscript source
│   ├── figures/            25 figure assets (.pdf / .png)
│   ├── support/            IEEE class file, embedded fonts, header logos
│   ├── build/               make output → ieee_access_manuscript.pdf
│   └── Makefile             one-command build
├── src/lineage_era/         estimator + pipeline (Phase 0–2)
│   └── analysis/            trait, metadata, population, identifiability, reml,
│                             bootstrap, plots, report — the real implementation
├── scripts/                 figure / design-space regeneration entry points
├── results/                 phase2_empirical/, phase2_sim_dryrun/, design_space/
├── datasets/                phase2_eval_results.csv (16-model empirical set),
│                             .sim variants, per-model eval samples, coverage tables
├── docs/                    research knowledge base — hypotheses, protocol,
│                             assumption register, novelty claims, peer-review
│                             simulation, reproducibility checklist, negative results
└── requirements.txt
```

`docs/` is the project's source of truth — start with `docs/00_Project/Project_Vision.md`
and `docs/00_Project/RESEARCH_PROTOCOL.md` if you want the full research narrative rather
than just the code.

---

## Quickstart

```bash
git clone <this-repo>
cd Identifiable-Variance-Decomposition-of-Correlated-Errors-in-Foundation-Models
pip install -r requirements.txt

# Run the identifiability gate on the real 16-model population
python -m lineage_era.phase2_identifiability

# Run the Phase 1 simulation validation (D1/D2/D3 designs, 300 reps each)
python src/lineage_era/phase1_simulation.py --regime all --reps 300 --seed 1

# Rebuild the manuscript PDF
make -C paper
```

---

## The identifiability gate

Before any $\sigma^2_{\text{lineage}}$, $\sigma^2_{\text{era}}$, $\sigma^2_{\text{unique}}$
number is estimated, the candidate model population has to clear five pre-registered,
data-independent checks:

| Gate | Condition | Threshold |
|---|---|---|
| Crossing | Every family appears in ≥2 eras; every era contains ≥2 families | boolean |
| Rank | Design matrix has full column rank | `rank(X) = p` |
| Conditioning | Numerical stability of the Gram matrix | $\kappa(X^\top X) \le 100$ |
| Variance inflation | No near-collinear column | $\max(\text{VIF}) \le 10$ |
| Connectivity | Family–era incidence graph is one connected component | boolean |

A design that fails any of these is **not** fit — more data does not fix a structural
confound (e.g. a nested design where every family lives in exactly one era). This is the
computational core in `src/lineage_era/analysis/identifiability.py`.

---

## Data

**16 real foundation models**, evaluated on MMLU (5-shot, 14,042 items, via
`lm-evaluation-harness` 0.4.12), spanning 5 families and 11 release quarters
(`datasets/phase2_eval_results.csv`):

| Family | Models | Era span |
|---|---|---|
| Mistral | Mistral-7B, Mistral-Small-3/3.1/3.2/4, Devstral-2 | 2023Q3 – 2026Q1 |
| Phi | Phi-1, Phi-1.5, Phi-2, Phi-3, Phi-4, Phi-4-reasoning-plus | 2023Q2 – 2025Q2 |
| Gemma | Gemma-3n, Gemma-4-12B | 2025Q2 – 2026Q2 |
| Llama | Llama-1 | 2023Q1 (singleton — the structural failure point) |
| Qwen | Qwen-7B | 2023Q3 |

A 47-model **candidate population** (not evaluated, used for design-space analysis) is
defined in `src/lineage_era/occupancy.py`, with matching simulated accuracy data in
`datasets/eval_samples.sim/`. Full seeds, gate thresholds, and hardware are logged in
`docs/REPRODUCIBILITY_CHECKLIST.md`.

---

## Reproducing the paper

| Stage | Command | Output |
|---|---|---|
| Phase 1 simulation (estimator validation) | `python src/lineage_era/phase1_simulation.py --regime all --reps 300 --seed 1` | `src/results/phase1/` |
| Phase 2 synthetic battery | `python -m lineage_era.phase2_simulate --reps 25 --seed 2026` | `results/phase2_sim_dryrun/` |
| Empirical gate audit (16 models) | `python -m lineage_era.phase2_identifiability` | gate pass/fail report |
| Design-space sweep | `python scripts/run_design_space_sweep.py` | `results/design_space/sweep_results.csv` |
| Figures | `python src/lineage_era/gen_manuscript_figures.py` | `paper/figures/` |
| Manuscript PDF | `make -C paper` | `paper/build/ieee_access_manuscript.pdf` |

Model evaluation itself requires a GPU (A100-80GB used for the paper, BF16 / 4-bit NF4 for
the 119B model) and is not required to reproduce any of the statistical results, which run
on the pre-computed CSVs.

---

## Analysis package (module map)

Top-level modules under `src/lineage_era/` are re-export shims; the real implementation
lives in `src/lineage_era/analysis/`:

| Module | Purpose |
|---|---|
| `trait.py` | Aggregate per-question responses into a continuous per-model trait |
| `eval_check.py` | Eval intake validator — fails fast on a mis-shaped GPU-runbook CSV |
| `eval_simulate.py` | Shape-exact simulated eval output for GPU-free pipeline dry-runs |
| `metadata.py` | Family/era design matrix from the Phase 0 table + verified `base_model` edges |
| `population.py` | Connected-subset population construction (erosion, gating, membership) |
| `identifiability.py` | The gate: rank, $\kappa$, VIF, crossing, connectivity — before any fit |
| `reml.py` | Direct crossed-REML estimator ($\sigma^2_L$, $\sigma^2_E$, $\sigma^2_U$) |
| `bootstrap.py` | Bootstrap CIs over models; sensitivity grid |
| `plots.py` | Partition, era-convergence, and diagnostics figures |
| `report.py` | Report generation + partition/summary tables |

---

## Figures

25 figure assets in `paper/figures/`, covering: the study workflow (`fig1`), simulation
recovery and bias/coverage under D1–D3 (`fig2`, `fig2a–c`, `fig3`), real-population
occupancy and rank/conditioning diagnostics (`fig4`–`fig6`), the gate pass/fail audit
(`fig5a`, `fig7`), the (non-identifiable) point estimate under gate failure (`fig8`),
accuracy distribution (`fig9`), and the design-space stress tests / robustness checks
(`fig10`–`fig12`).

---

## Known caveats / invalid artifacts

Logged transparently rather than swept under the rug (see
`docs/REPRODUCIBILITY_CHECKLIST.md §9` and `docs/06_Results/Negative_Results.md`):

- `datasets/eval_samples/*.jsonl` (16 files) contain simulated constant predictions and are
  **not** usable for per-question analysis — the aggregate accuracy in
  `phase2_eval_results.csv` is the valid artifact.
- `results/phase2_empirical/similarity_matrix_phi.csv` and `error_matrix_binary.csv` are
  degenerate (all-1s), inherited from the corrupted JSONL above.
- `requirements.txt` pins older package versions than the ones actually used to produce the
  paper's numbers (see the checklist for the exact versions used).
- No real population evaluated in this study — real or synthetic — passes all five gate
  conditions simultaneously; the sufficient 30-model design is a design-grid finding, not a
  population that currently exists and has been evaluated.

---

## Citation

```bibtex
@article{sudharsan2026lineage,
  title   = {Identifiability-Gated Variance Decomposition of Foundation-Model
             Performance: A Design and Empirical Feasibility Study},
  author  = {Sudharsan, S. and Raja, S. Kanaga Suba and V, Shree Harish and
             Shieh, Chin-Shiuh and Horng, Mong-Fong and R, Lavanya},
  journal = {IEEE Access},
  year    = {2026}
}
```

---

## Standing rules

- No analysis code or data pulls before the plan for that step is approved.
- Every citation is independently verified before it enters any document.
- Lead with the decomposition instrument and the identifiability gate —
  quantitative-genetics language (heritability, breeder's equation) is Phase 3 scaffolding
  only, never in the title, abstract, or lead paragraph.

## Contributing

This repository is shared. Please coordinate changes to `paper/`, `docs/`, and `results/`
to avoid conflicting edits, commit with clear single-purpose messages, and run
`make -C paper` after any manuscript change to confirm the PDF still builds.
