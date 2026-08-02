# Novelty Audit

Every novelty audit of the program. An audit re-checks novelty claims
(`docs/00_Project/Novelty_Claims.md`) against the latest literature — because novelty is
a moving target.

## Audit record

| Date | Scope | Method | Result | Action |
|---|---|---|---|---|
| 2026-07-XX | Initial framing | Reviewed PhyloLM, Correlated Errors, monoculture lit | "Quantitative Genetics" framing unsafe as lead | Dropped as lead; kept as Phase 3 analogy |
| 2026-08-02 | Full related-work ledger | Web-verified all 7 papers (arXiv/proceedings), incl. venue correction | Ledger confirmed; Preference Leakage venue corrected (ICLR 2026, not EMNLP 2024) | Proposal §5 + Literature_Map updated |
| _next_ | Re-audit before submission | TBD | TBD | TBD |

## Audit protocol (run before any submission)

1. Re-verify every claim in the current related-work section against the arXiv record.
2. Search for any new work on variance decomposition of LLM error traits (this is the
   highest-risk frontier).
3. Update Novelty_Claims confidence and the Kill Test accordingly.
4. Record the audit here.
