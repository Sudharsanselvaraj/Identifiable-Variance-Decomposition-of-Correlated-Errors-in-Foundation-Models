# Inclusion / Exclusion

Eligibility rules for the population. Membership is decided once, at Phase 0,
and codified in `src/lineage_era/occupancy.py` (`MODELS`).

## Inclusion criteria

1. **Open-weight** — weights are public under a documented license (23 of 47 are
   token-free; 24 are gated behind accepted-license `HF_TOKEN`).
2. **General-purpose** language model — excludes benchmark-only or task-specific
   checkpoints.
3. **Canonical HF checkpoint** exists for the connected-subset entry (verified
   2026-08-03 for all 47).
4. **Public release in 2023Q1–2026Q2** (the era window of the design).
5. **In the connected subset** — family spans multiple eras and multiple
   families occupy its era (see `docs/10_Population/Selection_Definition.md`).

## Exclusion criteria (with reason)

| Excluded | Reason |
|---|---|
| Hosted/closed models (Qwen3.7/3.8-Max, Muse Spark, Magistral Medium, Codestral) | No open weights; outside the population frame (register A5) |
| Llama 4.5 / Llama 5 | Not visible as open-weight repos (auth-gated org; existence inferred from author listing only) |
| `(term.)` cell | Annotation, not a model (Llama row) |
| Within-generation base↔instruct pairs | Not lineage edges (`base_model` field, register A3) |
| DeepSeek-V4 as V3 descendant | Ground-up redesign (dropped MLA); treated as new lineage (register A7) |

## Gated-model handling (Phase 2 eval)

- 24 models are auth-gated (meta-llama org, Qwen3+, DeepSeek-V4, Mistral org
  gated items, Gemma-1/2/3/3n/4) and require `HF_TOKEN` with the license
  accepted on the run host.
- `--skip-gated` runs only the 23 token-free models (coverage 23/47 — does NOT
  meet the coverage bar); used only for pilots.
- Access class is recorded per model in the design frame
  (`analysis/metadata.py`; `analysis_design.csv` `access` column).

## Sensitive memberships (flagged, not dropped)

- **Leaked models** (Phi-4, Gemma-2-9B, Gemma-4): cross-family teacher leakage;
  kept in the design, flagged `leaked=True`, assigned to the era channel, and
  reported via the leaked-drop sensitivity (register A8).
- **In-chain models**: members of the 5 verified `base_model` edges; flagged
  `in_chain=True` (feeds θ_M).

## Update rule

Any model added to the population later must satisfy the same criteria, use the
public release date (register A2), and be re-run through
`occupancy.check_consistency()` and the identifiability gate.
