# Timeline

Source: `proposal.md` §10. Execution may slip; gates (G1, G2) do not move — they are
honesty points.

| Window | Milestone | Depends on | Gate | Status |
|---|---|---|---|---|
| Week 1 | Phase 1 plan approval; `statsmodels` install; DGP scaffolding | — | — | DONE |
| Weeks 1–3 | Phase 1 simulation (D1/D2/D3, liability test) | Plan approval | G1 (Week 3): PASS → Phase 2; NO GO → stop/fix | DONE — G1 PASS (GO WITH CHANGES) |
| Weeks 4–5 | Item-level data procurement; design matrix assembly | G1 PASS; procurement | — | REROUTED — fresh MMLU eval replaces external procurement (decision log 2026-08-03) |
| Weeks 5–7 | Phase 2 decomposition; partition table; θ_M separately | Data ready | G2 (Week 7): report against register | ENGINE BUILT; awaiting GPU eval → G2 PENDING |
| Weeks 8–9 | Phase 3 analogies (if gated in) | Phase 2 survives | Drop if Δ doesn't track | Not started |
| Weeks 10–12 | Paper packaging; venue submission | — | Novelty audit + kill test before submission | Not started |

## 2–5 year horizon

- Re-audit novelty before every submission (the variance-decomposition-of-LLM-errors
  frontier moves fast).
- Re-run Phase 0 occupancy annually — the design is crossed today; it may not stay that
  way (Llama terminated; other lineages may too).
- Phase 3 analogies as a follow-on paper only if Phase 2 survives (never merged into the
  base claim).
