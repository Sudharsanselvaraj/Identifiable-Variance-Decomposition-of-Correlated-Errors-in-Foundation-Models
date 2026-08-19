# Reproducibility Checklist

**Paper:** Identifiability-Gated Variance Decomposition of Foundation-Model Performance

---

## 1. Repository

| Item | Value |
|---|---|
| Repository URL | `https://github.com/[OWNER]/sudharsan2ndpaper` (placeholder — replace with actual) |
| Commit hash | `4f2b4bda3ffa97a245db4402ef7e76f66cfd2e19` |
| License | (specify) |

---

## 2. Software Environment

| Package | Version (used in paper) | Version (requirements.txt) | Installed |
|---|---|---|---|
| Python | 3.11.7 | — | 3.11.7 |
| NumPy | 2.1.3 | 1.26.4 | 2.1.3 |
| SciPy | 1.17.1 | 1.13.1 | 1.17.1 |
| pandas | 3.0.5 | 2.2.2 | 3.0.5 |
| statsmodels | 0.14.6 | 0.14.6 | 0.14.6 |
| matplotlib | 3.9.2 | — | 3.9.2 |
| PyTorch | 2.11.0 | — | 2.11.0 |
| lm-evaluation-harness | 0.4.12 | — | 0.4.12 |

**NOTE:** There is a version mismatch between `requirements.txt` (numpy 1.26.4, scipy 1.13.1, pandas 2.2.2) and the versions reported in the manuscript (numpy 2.1.3, scipy 1.17.1, pandas 3.0.5). The manuscript Section 14 lists the higher versions; `requirements.txt` pins older ones. **Action: update `requirements.txt` to match the actual environment or document the discrepancy.**

---

## 3. Hardware

| Stage | GPU | Precision | Notes |
|---|---|---|---|
| Evaluation (15 models) | NVIDIA A100-SXM4 80GB (RunPod) | BF16 | `--dtype bfloat16 --quant none --attn sdpa` |
| Evaluation (1 model) | NVIDIA A100-SXM4 80GB (RunPod) | 4-bit NF4 | Mistral-Small-4 (119B params, does not fit BF16 in 80GB) |
| Development / auditing | NVIDIA A16 (rented cloud) | — | Used for initial structural audit |
| CUDA available at reproduction time | False (CPU-only host) | — | Simulation and analysis are CPU-only; GPU needed only for model evaluation |

---

## 4. Random Seeds

| Component | Seed | Location in code |
|---|---|---|
| Phase 1 simulation (D1/D2/D3, all scenarios) | `--seed 1` (default) | `src/lineage_era/phase1_simulation.py:278` |
| Phase 2 synthetic battery (S1–S6) | `--seed 2026` (default) | `src/lineage_era/phase2_simulate.py:136` |
| G3 population optimizer — Scenario A | 101 | `src/lineage_era/analysis/population_optimizer.py:114` |
| G3 population optimizer — Scenario B | 202 | `src/lineage_era/analysis/population_optimizer.py:114` |
| Bootstrap CI (trait error MC) | `--seed 2026` (default) | `src/lineage_era/analysis/bootstrap.py:59` |
| Figure generation (PCA/t-SNE layout) | 42 | `src/lineage_era/gen_manuscript_figures.py:344` |
| Imputation | `--seed 2026` (default) | `src/lineage_era/analysis/impute.py:463` |

---

## 5. Empirical Dataset

### 5.1 Benchmark Configuration

| Item | Value |
|---|---|
| Benchmark | MMLU (Hendrycks et al., 2021) |
| Few-shot | 5 |
| Evaluation samples per model | 14,042 |
| Evaluation harness | lm-evaluation-harness 0.4.12 (EleutherAI) |
| Metric | Aggregate CSV accuracy (acc) |

### 5.2 Measured Models (16 evaluated)

| # | Model | HuggingFace Repo | Family | Era | Accuracy | Fidelity |
|---|---|---|---|---|---|---|
| 1 | Mistral-Small-3 | `mistralai/Mistral-Small-24B-Instruct-2501` | Mistral | 2025Q1 | 0.8069 | BF16 |
| 2 | Phi-3 | `microsoft/Phi-3-medium-4k-instruct` | Phi | 2024Q2 | 0.7799 | BF16 |
| 3 | Phi-4-reasoning-plus | `microsoft/Phi-4-reasoning-plus` | Phi | 2025Q2 | 0.7782 | BF16 |
| 4 | Phi-4 | `microsoft/Phi-4-mini-instruct` | Phi | 2024Q4 | 0.6864 | BF16 |
| 5 | Gemma-3n | `google/gemma-3n-E4B-it` | Gemma | 2025Q2 | 0.6364 | BF16 |
| 6 | Mistral-7B | `mistralai/Mistral-7B-Instruct-v0.3` | Mistral | 2023Q3 | 0.6186 | BF16 |
| 7 | Phi-2 | `microsoft/phi-2` | Phi | 2023Q4 | 0.5644 | BF16 |
| 8 | Gemma-4-12B | `google/gemma-4-12b-it` | Gemma | 2026Q2 | 0.4397 | BF16 |
| 9 | Phi-1.5 | `microsoft/phi-1_5` | Phi | 2023Q3 | 0.4218 | BF16 |
| 10 | Llama-1 | `huggyllama/llama-7b` | Llama | 2023Q1 | 0.3424 | BF16 |
| 11 | Devstral-2 | `mistralai/Devstral-Small-2-24B-Instruct-2512` | Mistral | 2025Q4 | 0.2515 | BF16 |
| 12 | Phi-1 | `microsoft/phi-1` | Phi | 2023Q2 | 0.2480 | BF16 |
| 13 | Mistral-Small-4 | `mistralai/Mistral-Small-4-119B-2603` | Mistral | 2026Q1 | 0.2433 | 4-bit |
| 14 | Mistral-Small-3.1 | `mistralai/Mistral-Small-3.1-24B-Instruct-2503` | Mistral | 2025Q1 | 0.2340 | BF16 |
| 15 | Mistral-Small-3.2 | `mistralai/Mistral-Small-3.2-24B-Instruct-2506` | Mistral | 2025Q2 | 0.2314 | BF16 |
| 16 | Qwen-7B | `Qwen/Qwen-7B` | Qwen | 2023Q3 | 0.2295 | BF16 |

### 5.3 Candidate Population (47 models, NOT evaluated)

Defined in `src/lineage_era/occupancy.py`. Simulated accuracy in `datasets/phase2_eval_results.sim.csv` (2,000 samples per model, distinct from measured data). Simulation files for all 47 models in `datasets/eval_samples.sim/`.

### 5.4 G3 Selected Population (22 models, partially evaluated)

Defined in `datasets/coverage/minimum_valid_population.csv`. 16 of 22 were evaluated; DeepSeek-V3.1 (671B) and DeepSeek-V3.2 (685B) could not be evaluated due to compute constraints.

---

## 6. Simulation Parameters

### 6.1 Design Configurations

| Design | Families | Eras | Models per cell | Total N | Purpose |
|---|---|---|---|---|---|
| D1 (balanced crossed) | 30 | 14 | 2 | 840 | Estimator calibration (large family count) |
| D2 (realistic occupancy) | 6 | 14 | variable (sparse) | 47 | Small-sample limit validation |
| D3 (nested) | 6 | 6 | 2 (collinear) | 72 | Non-identifiability detection |

### 6.2 Variance Scenarios

| Scenario | σ²_L (lineage) | σ²_E (era) | σ²_U (unique) | Label |
|---|---|---|---|---|
| A | 0.50 | 0.20 | 0.30 | Lineage-dominant |
| B | 0.20 | 0.50 | 0.30 | Era-dominant |
| C | 0.33 | 0.33 | 0.34 | Balanced |

### 6.3 Phase 2 Synthetic Battery Scenarios

| Scenario | Design | L | E | U | Validation target |
|---|---|---|---|---|---|
| S1 | D2 | 0.60 | 0.10 | 0.30 | Lineage-dominant recovery |
| S2 | D2 | 0.10 | 0.60 | 0.30 | Era-dominant recovery |
| S3 | D2 | 0.35 | 0.35 | 0.30 | 50/50 recovery |
| S4 | D3 (nested) | — | — | — | Audit MUST abort |
| S5 | D2 + measurement noise | 0.35 | 0.35 | 0.30 | Noisy recovery (σ_m = 0.5) |
| S6 | D2 | scenario C | | | Audit MUST pass |

### 6.4 Repetitions and Tolerances

- **Phase 1 (D1/D2/D3):** 300 repetitions per scenario
- **Phase 2 battery (S1–S6):** 25 repetitions per scenario (default `--reps 25`)
- **Share tolerances (Phase 2):** S1: 0.10, S2: 0.12, S3: 0.08, S5: 0.15

---

## 7. Gate Thresholds

| Gate | Metric | Threshold | Type |
|---|---|---|---|
| G1 | Rank(X) | = p (full column rank) | Structural |
| G2 | κ(X'X) | ≤ 100 | Numerical stability |
| G3 | max(VIF) | ≤ 10 | Numerical stability |

---

## 8. Key Output Artifacts

| Artifact | Path |
|---|---|
| 16-model accuracy data | `datasets/phase2_eval_results.csv` |
| G3 minimum valid population | `datasets/coverage/minimum_valid_population.csv` |
| 47-model population definition | `src/lineage_era/occupancy.py` |
| REML engine | `src/lineage_era/analysis/reml.py` |
| Identifiability audit | `src/lineage_era/analysis/identifiability.py` |
| Phase 1 simulation outputs | `src/results/phase1/` |
| Phase 2 dry-run outputs | `src/results/phase2_sim_dryrun/` |
| Trait definition (22-model roster) | `datasets/coverage/trait_definition.csv` |

---

## 9. Known Invalid Artifacts

| Artifact | Issue |
|---|---|
| `datasets/eval_samples/*.jsonl` (16 files) | All contain simulated constant predictions (every model predicts answer 0). NOT usable for per-question analysis. |
| `datasets/eval_samples.sim/*.jsonl` (47 files) | Simulated evaluation data (different from measured). 2,000 samples per model. |
| `results/phase2_empirical/similarity_matrix_phi.csv` | All 1.0 (degenerate, from corrupted JSONL) |
| `results/phase2_empirical/error_matrix_binary.csv` | All 1s (from corrupted JSONL) |

---

## 10. Reproduction Steps

### 10.1 Environment Setup

```bash
pip install numpy==2.1.3 scipy==1.17.1 pandas==3.0.5 statsmodels==0.14.6 matplotlib==3.9.2
pip install lm-eval==0.4.12  # for evaluation harness
```

### 10.2 Phase 1 Simulation (D1/D2/D3)

```bash
python src/lineage_era/phase1_simulation.py --regime all --reps 300 --seed 1
```

### 10.3 Phase 2 Synthetic Battery

```bash
python -m lineage_era.phase2_simulate --reps 25 --seed 2026
```

### 10.4 Empirical Gate Audit

```bash
python -m lineage_era.phase2_identifiability  # reads datasets/phase2_eval_results.csv
```

### 10.5 Model Evaluation (requires GPU)

```bash
# RunPod A100-80GB with lm-evaluation-harness
lm_eval --model hf --model_args pretrained=<repo>,dtype=bfloat16 \
  --tasks mmlu --num_fewshot 5 --batch_size auto
```

### 10.6 Figure Generation

```bash
python src/lineage_era/gen_manuscript_figures.py
```

---

## 11. Checklist Summary

- [ ] Repository URL is public and accessible
- [ ] Commit hash is pinned
- [ ] `requirements.txt` matches actual environment versions
- [ ] All random seeds are documented and reproducible
- [ ] Simulation configurations are fully specified
- [ ] Gate thresholds are pre-specified (not data-dependent)
- [ ] Known invalid artifacts are labeled and excluded from analysis
- [ ] GPU hardware is documented for evaluation stage
- [ ] Evaluation harness version is pinned
- [ ] Benchmark configuration (MMLU, 5-shot, 14042 items) is documented
