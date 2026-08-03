# Population Definition

The **population** is the connected subset: the set of public open-weight
language models on which lineage and era are separable. It is a *design*
population, not a census — membership is decided by the crossed-vs-nested
question (see `docs/02_Theory/Identifiability.md`).

## What the population is

| Element | Definition | Source |
|---|---|---|
| Sampling frame | Public, open-weight, general-purpose language models released 2023Q1–2026Q2 with a canonical HF checkpoint | Phase 0 selection |
| Family (lineage factor) | The model's ancestry group (Llama, Qwen, DeepSeek, Mistral, Phi, Gemma) | `docs/03_Data/Model_Lineages.md` |
| Era (era factor) | Public release quarter | `docs/10_Population/Environment_Definition.md` |
| Connected subset | Models in the crossed design: families spanning multiple eras AND multiple families per era | `Terminology.md` |

## Population statistics framing

This repository treats the model collection as a **population with structure**
(family, era, environment) and estimates variance components on a trait measured
on that population. The decomposition instrument is the program's core
contribution; quantitative-genetics vocabulary is Phase 3 scaffolding only and
never enters base claims (`docs/00_Project/Project_Vision.md`).

## Size and structure (Phase 0 verified)

- **47 models**, 6 families × 14 quarters (2023Q1–2026Q2).
- 11/14 quarters have ≥2 independent families; no family is confined to a single
  era.
- Design verdict: **CROSSED (unbalanced/incomplete)** — the gate that makes the
  partition estimable.

## Scope boundaries

- Open-weight only; hosted/closed (Qwen3.7/3.8-Max, Muse Spark, Magistral
  Medium, Codestral) excluded.
- All claims are scoped to the connected subset (register A4); non-separability
  on nested subpopulations is a design property, not a data gap.

## Governing documents

- Terminology: `docs/01_Literature/Terminology.md`
- Research questions (per-population refutation conditions):
  `docs/00_Project/Research_Questions.md`
- Identifiability conditions: `docs/02_Theory/Identifiability.md`
