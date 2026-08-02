# Structural Causal Model

The assumed causal/structural story that motivates the estimand. This is the working DAG
for the proposal; it is a *model*, not a verified fact — verification is what the program
is for.

## DAG

```
                          ┌─────────────────────────────┐
                          │    era (release quarter)    │
                          │  shared data / technique    │
                          └───────────┬─────────────────┘
                                      │  shared errors
              ┌───────────────────────┼──────────────────────┐
              ▼                       ▼                      ▼
       [family / lineage] ──► [release date] ──► [model error trait]
              │                     ▲                      │
              │      (mediator      │                      │
              └─────────path ───────┘                      │
              │                                            │
              └──────────► [teacher leakage] ──► [shared env] ──┐
                                                               ▼
                                                     [era channel, σ²_E]
```

## Key structural facts

1. **Release date is both a confounder and a mediator** on the lineage→error path.
   - *Confounder:* era imposes an error structure on every contemporaneous model
     regardless of ancestry.
   - *Mediator:* lineage acts partly by moving release forward into new data regimes.
   - Consequence: a single estimand conflates the two roles ⇒ the two-estimand rule
     (θ_P observational, θ_M mechanistic).
2. **Family → model error trait** is the lineage channel (σ²_L): parent–offspring edges,
   fine-tune chains, teacher–student distillation.
3. **Era → model error trait** is the era channel (σ²_E): shared web scrapes,
   benchmark-cleansed corpora, dominant technique. This includes documented **teacher
   leakage** (Phi-4 ← GPT-4o data; Gemma 2 9B ← 27B; Gemma 4 ← Gemini 3) — cross-family
   environmental sharing, assigned to σ²_E, not σ²_L.
4. **Benchmark contamination** (models trained on leaderboard items) enters the era
   channel and inflates σ²_E; disclosed as an inflation direction, mitigated by item-set
   choice where feasible.

## What is NOT in the DAG (deliberately)

- No common-cause node connecting independent families other than era and leakage.
  Family independence is treated as a stated assumption (violated by teacher leakage to a
  known-but-unknown degree).
- No lineage × era interaction node (not identified from sparse cells).
- No "true causal share" node: the program reports the pair (θ_P, θ_M) as bracketing the
  truth, not a single causal number.

## Open edges to verify (each maps to a Phase)

| Edge | Question | Phase |
|---|---|---|
| family → error trait | Is lineage variance nonzero conditional on era? | 2 (θ_P) |
| family → error trait (era fixed) | Structural lineage contribution on co-released/fine-tune subsets | 2 (θ_M) |
| era → error trait | Era variance share; convergence trend | 2 (θ_P / RQ5) |
| era → error trait (via contamination) | Inflation direction of σ²_E | 2 (disclosure) |
