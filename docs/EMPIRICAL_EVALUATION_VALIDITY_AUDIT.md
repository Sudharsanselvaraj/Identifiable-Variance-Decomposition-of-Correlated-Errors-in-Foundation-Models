# EMPIRICAL EVALUATION VALIDITY AUDIT

Independent audit of all 16 model evaluations before manuscript claims are finalized.

## Audit Summary

| Status | Count | Models |
|---|---|---|
| PLAUSIBLE | 10 | Mistral-Small-3, Phi-3, Phi-4-reasoning-plus, Phi-4, Gemma-3n, Mistral-7B, Phi-2, Gemma-4-12B, Phi-1.5, Llama-1 |
| SUSPECT | 6 | Devstral-2, Phi-1, Mistral-Small-4, Mistral-Small-3.1, Mistral-Small-3.2, Qwen-7B |

## Per-Model Assessment

### PLAUSIBLE Models (10)

| Model | Accuracy | Reference | Discrepancy | Notes |
|---|---|---|---|---|
| Mistral-Small-3 | 80.69% | ~72-76% | +4-8pp | Slightly above reference; possibly lenient answer matching or different MMLU variant. Plausible. |
| Phi-3 (14B instruct) | 77.99% | ~76-78% | OK | Matches published scores. |
| Phi-4-reasoning-plus | 77.82% | ~76-78% | OK | Matches published scores. |
| Phi-4 (3.8B instruct) | 68.64% | ~68-70% | OK | Matches published scores. |
| Gemma-3n (~4B) | 63.64% | ~60-65% | OK | Within expected range. |
| Mistral-7B Instruct v0.3 | 61.86% | ~62-64% | OK | Matches published scores. |
| Phi-2 (2.7B) | 56.44% | ~56-57% | OK | Matches published scores. |
| Gemma-4-12B | 43.97% | ~68-72% | -24pp | Below published reference. Could be prompt-format difference, different MMLU variant, or genuine evaluation issue. FLAG for further investigation. |
| Phi-1.5 (1.3B) | 42.18% | ~43-45% | OK | Matches published scores for small model. |
| Llama-1 (7B base) | 34.24% | ~35-40% | OK | Base model without instruction tuning; expected to be low. |

### SUSPECT Models (6)

| Model | Accuracy | Reference | Discrepancy | Likely Cause |
|---|---|---|---|---|
| Devstral-2 (24B) | 25.15% | ~70-75% | -45pp | Near random for 4-choice. Chat template mismatch almost certain. |
| Phi-1 (1.3B code) | 24.80% | ~43-45% | -18pp | Near random. Could be genuine (very small code-focused model) or evaluation artifact. |
| Mistral-Small-4 (119B, 4-bit) | 24.33% | ~82-86% | -58pp | Near random despite 119B parameters. 4-bit quantization alone cannot explain this. Chat template mismatch. |
| Mistral-Small-3.1 (24B) | 23.40% | ~73-77% | -50pp | Near random. Same architecture as Mistral-Small-3 (80.69%). Chat template mismatch. |
| Mistral-Small-3.2 (24B) | 23.14% | ~73-77% | -50pp | Near random. Same architecture as Mistral-Small-3 (80.69%). Chat template mismatch. |
| Qwen-7B | 22.95% | ~56-58% | -33pp | Near random. Base model; may need different prompt format. |

## Critical Finding: Mistral-Small Family Discontinuity

| Model | Release | Accuracy | Delta |
|---|---|---|---|
| Mistral-Small-3 | Jan 2025 | 80.69% | — |
| Mistral-Small-3.1 | Mar 2025 | 23.40% | -57.3pp |
| Mistral-Small-3.2 | Jun 2025 | 23.14% | -57.5pp |

A 57-percentage-point degradation within a single model family over 2 months is **not plausible** as a real capability change. These are all 24B parameter models with the same base architecture.

**Root cause hypothesis:** The newer Mistral instruct models (3.1, 3.2, Devstral-2, Small-4) use a different chat template format that the lm-evaluation-harness default does not handle correctly. The models may be treating the MMLU prompt as a conversation and producing explanations rather than answer-choice letters, which then fail the answer-extraction scoring.

## JSONL Integrity

All 16 JSONL files contain constant predictions (all zeros). The per-question error vectors are **invalid** and cannot be used for any analysis.

## Impact on Manuscript

1. **The identifiability gate result is INVARIANT** — it depends only on the design matrix structure (which families and eras are represented), not on the trait values.

2. **The variance-component estimates are CONDITIONAL** — they assume the input accuracy values are valid. The 6 suspect models may distort the variance decomposition.

3. **The paper must disclose** this validity caveat prominently and not claim the CSV values are reliable without independent validation.

4. **The variance decomposition is reported as DIAGNOSTIC ONLY** — the 5.4% family-share point estimate and its CI are not inferentially interpretable regardless of evaluation validity.

## Recommendation

- Mark the 6 suspect models as having **unverified evaluation validity** in the manuscript
- State that the identifiability gate result is valid regardless of trait values
- State that any future variance-component interpretation requires independent validation of accuracy measurements
- Do NOT claim "16 models were validated" — say "16 models were evaluated; 10 show plausible accuracy values, 6 show values near chance level requiring independent verification"
