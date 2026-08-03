# Trait Definition

The **trait** is the per-model continuous measurement that the crossed
variance-components model decomposes. Per Phase 1 F4, the analysis models a
continuous per-model trait (aggregated item responses), **not** raw item-level
binary responses (register A10, A11).

## Definition

```
trait(m) = accuracy of model m on the common MMLU item set (5-shot, loglikelihood)
trait_se(m) = measurement SE: binomial sqrt(p(1-p)/n), refined to the sample
              standard error of per-question scores when per-question samples exist
```

- Scale: continuous in [0, 1] (accuracy). The latent model assumes linear
  additivity on the liability scale; the continuous-trait path is the
  Phase 1-validated LPM-REML choice.
- σ²_U is **measured-with-error inclusive**: variance of the trait estimator
  lands in the unique component and is reported with the partition
  (`docs/03_Data/Dataset_Inventory.md`).

## Liability-scale latent structure (for reference)

```
y*_mi = δ_i + α_{f(m)} + β_{e(m)} + u_m + r_mi,   y_mi = 1{y*_mi > 0}
```
Full notation: `docs/02_Theory/Mathematical_Formulation.md`.

## How the trait is produced (Phase 2)

1. Fresh MMLU 5-shot eval of all 47 connected-subset models on the GPU host
   (`phase2_run_all.py`; `--no-samples` to skip per-question capture).
2. `analysis/trait.py` merges eval accuracy with the occupancy table → per-model
   `trait_table.csv` (trait, trait_se, n_items, n_correct, source) and, when
   per-question samples exist, `subject_acc.csv`.
3. Trait SE is binomial from the CSV counts, or sample SE from the per-question
   JSONL (`datasets/eval_samples/`).

## Item set

- Benchmark: MMLU 5-shot, `cais/mmlu` (14,042 test questions, 57 subjects),
  loglikelihood scoring — matches Kim et al. and the paper framing.
- One fixed item set across all models (a common item set is a stated
  assumption, register A15). Kim et al. leaderboard values are a documented
  sanity cross-check only, never validation (register A22).
- Per-model caveats: Phi-1/1.5/2 need `max_length=2048,truncation=True`;
  sliding-window models (Qwen, Mistral) should use `sdpa` attention.

## Precision requirement

Identifiability condition 4: traits must be measured precisely enough, and
precision is a first-class output — every estimate ships with CIs
(`analysis/bootstrap.py`: log-variance MC delta + trait-error Monte-Carlo that
perturbs each trait by its `trait_se` and refits). With thin item counts, prefer
IRT ability over raw proportion and report item counts alongside.

## Sources

- Formulation + assumptions: `docs/02_Theory/Mathematical_Formulation.md`
- Estimator paths: `docs/02_Theory/Statistical_Model.md`
- Data contract + inventory: `docs/03_Data/Dataset_Inventory.md`
