# Reviewer2

Maintained log of real reviewer feedback per venue (when it exists). The
pre-registered likely objections live in `docs/06_Results/Reviewer_Questions.md`.

## ICML

_(empty)_

## NeurIPS

_(empty)_

## Measurement-focused venues

_(empty)_

## Journals (e.g., JMLR)

_(empty)_

## External audit (2026-08-05, pre-submission integrity review)

An independent review of `docs/07_Paper/manuscript.tex` (two reviewer pass-throughs)
flagged the following. Each finding was verified against the repo's artifacts before
acting. **Disposition:** all real findings fixed in the current manuscript; the paper
is now honest-methods framing (validated gates + pending measurement), never a
results claim.

| # | Finding | Verified? | Disposition |
|---|---|---|---|
| 1 | All five figures were the template's magnetization `fig1.png` | Real (template `access.tex` sample) | All replaced: `figs/fig_dag.png` (schematic), `figs/fig_design.png` (real occupancy), `figs/fig_g3_trace.png` (real trace); similarity/partition are explicitly labeled pending placeholders |
| 2 | `kim2025a` bibitem fabricated (does not exist) | Real — no such paper | Deleted; `\cite{kim2025,kim2025a}` collapsed to `\cite{kim2025}`; `kim2025` now the exact verified entry (Kim, Garg, Peng, Garg, ICML 2025, PMLR 267:30038–30066) |
| 3 | `phylolm2024` / `monoculture2024` were bare placeholder strings | Real | Filled from the verified ledger: Yax/Oudeyer/Palminteri (ICLR 2025); Hedden & Raghavan + Jo/Garg/Raghavan |
| 4 | `bates2015` (lme4) orphaned; lme4 unused in code | Real | Deleted from bibliography |
| 5 | statsmodels 66.674 vs 65.994 not checkable from the PDF | Finding is real and documented (`analysis/reml.py`, Decision Log 2026-08-03) | Reproducibility pointer added in §Estimators and Appendix C |
| 6 | Abstract/conclusion overstate a pending result | Real (§VI.D is all TBD) | Rewritten to honest-methods framing; §VI results-status callout added |
| 7 | Placeholder metadata (authors, DOI, bios) read as integrity smell | Partially — authors were real on request | Authors filled from author-provided details; history dates, DOI, funding, bios remain marked TODO placeholders with a fill-in checklist (never fabricated) |
| 8 | Two 2026 neighbors suggested | Chen "co-failure ceiling" and Kuai et al. "How independent…" — both verified real (arXiv:2606.27288, arXiv:2604.07650) | Added to the ledger and cited in Discussion / Related Work |

Scores in the review (3/10 reject at listed venues, JMLR major-revision-as-registered-report)
assume a completed empirical paper; the honest-methods version reframes the submission
as a validated instrument + pre-registered protocol (matching the JMLR Stage-1 suggestion).

## Venue norms to respect (verified at submission time, per operating rule 1)

- ICML: empirical + methodology papers; precedent — Kim et al. Correlated Errors
  (ICML 2025, PMLR 267).
- CFP details change; never assert a venue norm from memory at submission time.
