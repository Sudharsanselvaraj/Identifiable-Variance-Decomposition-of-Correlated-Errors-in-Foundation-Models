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
| `docs/` | Research knowledge base — the source of truth for the project (structure under `docs/00_Project` … `docs/09_Roadmap`) |
| `MASTER_PROMPT.md` | Execution master prompt; phase status; Phase 0 log (HF-verified) |
| `proposal.md` | Full research proposal draft (sections 1–14) |
| `notebooks/` | Analysis notebooks (Phase 1 onward) |
| `src/` | Simulation / decomposition code (Phase 1 onward) |
| `datasets/` | Item-level data (procurement pending; see `docs/03_Data`) |

## Standing rules

- No analysis code or data pulls before the plan for that step is approved (Phase 0 done;
  Phase 1 run — GO WITH CHANGES, see `PHASE1_REPORT.md`).
- Every citation is independently verified before it enters any document.
- Lead with the decomposition instrument and the identifiability gate; quantitative-genetics
  language is Phase 3 scaffolding only.
