# Exp04 download — reconciled validation report

Code commit: `51477b61c18990011fabb5c5a373d8a08598ab61`

Frozen download list: 1018 unique models (primary sample 613, expanded sample 967).

## Final category per model (each model counted once)

| category        |   models |
|:----------------|---------:|
| validated       |      977 |
| no_complete_run |       33 |
| repo_missing    |        7 |
| schema_error    |        1 |

## Coverage of each frozen sample

| category        |   primary_sample |   expanded_sample |
|:----------------|-----------------:|------------------:|
| validated       |              590 |               928 |
| no_complete_run |               17 |                32 |
| repo_missing    |                5 |                 6 |
| schema_error    |                1 |                 1 |

## Validated files

- layouts: {'lighteval': 692, 'legacy': 253, 'legacy_str': 32}
- storage: 106.9 MB in 977 files
- accuracy: median 0.466, 339 models below 0.30 (near chance; kept, flagged for the accuracy-control sensitivity check)

## Not validated (documented exclusions, never replaced)

| model                                                                                     | category        | detail                                                                      |
|:------------------------------------------------------------------------------------------|:----------------|:----------------------------------------------------------------------------|
| 01-ai/Yi-6B-200K                                                                          | no_complete_run | no_complete_run                                                             |
| Andron00e/YetAnother_Open-Llama-3B-LoRA-OpenOrca                                          | no_complete_run | no_complete_run                                                             |
| Aspik101/tulu-7b-instruct-pl-lora_unload                                                  | no_complete_run | no_complete_run                                                             |
| FabbriSimo01/Facebook_opt_1.3b_Quantized                                                  | schema_error    | TypeError: '>' not supported between instances of 'NoneType' and 'NoneType' |
| FelixChao/vicuna-7B-chemical                                                              | no_complete_run | no_complete_run                                                             |
| GeorgiaTechResearchInstitute/galactica-6.7b-evol-instruct-70k                             | no_complete_run | no_complete_run                                                             |
| KoboldAI/OPT-350M-Nerys-v2                                                                | no_complete_run | no_complete_run                                                             |
| LLMs/Stable-Vicuna-13B                                                                    | no_complete_run | no_complete_run                                                             |
| MayaPH/opt-flan-iml-6.7b                                                                  | no_complete_run | no_complete_run                                                             |
| NousResearch/Nous-Hermes-2-Mixtral-8x7B-SFT                                               | repo_missing    | repo_missing                                                                |
| QueryloopAI/gemma-7b-openhermes                                                           | repo_missing    | repo_missing                                                                |
| RoversX/llama-2-7b-hf-small-shards-Samantha-V1-SFT                                        | no_complete_run | no_complete_run                                                             |
| TheBloke/Kimiko-13B-fp16                                                                  | no_complete_run | no_complete_run                                                             |
| TheBloke/WizardLM-Uncensored-SuperCOT-StoryTelling-30B-GPTQ                               | no_complete_run | no_complete_run                                                             |
| TheBloke/chronos-wizardlm-uc-scot-st-13B-GPTQ                                             | no_complete_run | no_complete_run                                                             |
| TheBloke/guanaco-33B-GPTQ                                                                 | no_complete_run | no_complete_run                                                             |
| TheBloke/medalpaca-13B-GPTQ-4bit                                                          | no_complete_run | no_complete_run                                                             |
| TheBloke/orca_mini_13B-GPTQ                                                               | no_complete_run | no_complete_run                                                             |
| ajibawa-2023/Young-Children-Storyteller-Mistral-7B                                        | repo_missing    | repo_missing                                                                |
| amazingvince/zephyr-smol_llama-100m-dpo-full                                              | no_complete_run | no_complete_run                                                             |
| bofenghuang/vigogne-2-13b-instruct                                                        | no_complete_run | no_complete_run                                                             |
| chargoddard/Yi-34B-Llama                                                                  | no_complete_run | no_complete_run                                                             |
| edor/Platypus2-mini-7B                                                                    | no_complete_run | no_complete_run                                                             |
| habanoz/TinyLlama-1.1B-intermediate-step-715k-1.5T-lr-5-1epch-airoboros3.1-1k-instruct-V1 | repo_missing    | details repo name is 98 chars (> 96)                                        |
| habanoz/TinyLlama-1.1B-intermediate-step-715k-1.5T-lr-5-2.2epochs-oasst1-top1-instruct-V1 | repo_missing    | details repo name is 98 chars (> 96)                                        |
| habanoz/TinyLlama-1.1B-intermediate-step-715k-1.5T-lr-5-3epochs-oasst1-top1-instruct-V1   | no_complete_run | no_complete_run                                                             |
| habanoz/TinyLlama-1.1B-intermediate-step-715k-1.5T-lr-5-4epochs-oasst1-top1-instruct-V1   | no_complete_run | no_complete_run                                                             |
| harborwater/open-llama-3b-claude-30k                                                      | no_complete_run | no_complete_run                                                             |
| internlm/internlm-20b                                                                     | no_complete_run | no_complete_run                                                             |
| internlm/internlm2-20b                                                                    | repo_missing    | repo_missing                                                                |
| internlm/internlm2-7b                                                                     | repo_missing    | repo_missing                                                                |
| monology/openinstruct-mistral-7b                                                          | no_complete_run | no_complete_run                                                             |
| openaccess-ai-collective/openhermes-2_5-dpo-no-robots                                     | no_complete_run | no_complete_run                                                             |
| psmathur/model_007_13b_v2                                                                 | no_complete_run | no_complete_run                                                             |
| pszemraj/pythia-6.9b-HC3                                                                  | no_complete_run | no_complete_run                                                             |
| rinna/bilingual-gpt-neox-4b                                                               | no_complete_run | no_complete_run                                                             |
| rinna/bilingual-gpt-neox-4b-8k                                                            | no_complete_run | no_complete_run                                                             |
| rinna/youri-7b                                                                            | no_complete_run | no_complete_run                                                             |
| rinna/youri-7b-chat                                                                       | no_complete_run | no_complete_run                                                             |
| tianlinliu0121/zephyr-7b-dpo-full-beta-0.2                                                | no_complete_run | no_complete_run                                                             |
| yec019/fbopt-350m-8bit                                                                    | no_complete_run | no_complete_run                                                             |
