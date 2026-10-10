# Audit progress (resumable)

Audit started 2026-10-10 on `fix/figure-review-ieee` @ d262d2e. Read-only: nothing pushed, merged, committed or deleted.

| Phase | Status | Output |
|---|---|---|
| 0 Project state | DONE | PROJECT_INVENTORY.csv, section 0 of EXECUTIVE_RESEARCH_AUDIT.md |
| 1 Read manuscript, claim ledger | DONE | CLAIM_EVIDENCE_LEDGER.csv |
| 2 Pipeline reconstruction | DONE | |
| 3 Independent recomputation | DONE | STATISTICAL_VERIFICATION.md |
| 4 Statistical methodology | DONE | |
| 5 Figures and tables | DONE | FIGURE_TABLE_AUDIT.md |
| 6 Withdrawn evaluation | DONE | |
| 7 Prespecification history | DONE | |
| 8 Reproducibility, software | DONE | REPRODUCIBILITY_AUDIT.md |
| 9 Literature, references | DONE | |
| 10 IEEE Access audit | DONE | |
| 11 Editorial review | pending | |
| 12 Red-team review | pending | FINAL_PEER_REVIEW.md |

## Phase 0 facts
- origin/main = 3a6d1dc (PR #3, #4, #5 merged). HEAD tree = origin/main tree (febb362...). Candidate = main; no unpushed commits.
- Local `main` is stale (72 behind). Branches: fix/figure-review-ieee, fix/review-validation-gate, revision/precision-gate (all merged), release/manuscript-v3 (old), backup/pre-history-rewrite (old).
- Untracked, not part of any commit: datasets/mmlu_redux/, master/tmp.txt, *.docx, *.fls. Ignored: datasets/ollb/v1 (answer files), frozen_full.
- Stash stash@{0}: unrelated old WIP (Qwen tokenizer patch in phase2_eval.py), earlier study.
- Candidate hashes (sha256 first 16): paper PDF 922e2d639ff0e425 (16 pp), supplement PDF 990b98b810f5c3cb (15 pp), master PDF 0e4181ba19826f2a (25 pp), manuscript tex 95262b09be584307, supplement tex ed2bcd0cdd0f7e40.
- Tracked obsolete PDFs: docs/07_Paper/manuscript.pdf, paper/src/archive/ieee_access_manuscript_v1_16model.pdf (+ earlier-study figures under results/phase2_empirical and src/results).

## Phases 1-3 facts (appended)
- Phase 1: manuscript (paper/src/ieee_access_manuscript.tex, 560 lines) and supplement (paper/src/supplement.tex) read in full.
- Phase 2: frozen lists hash-match recorded SHA-256; sampling rule = scripts/compare_rosters.py (seed 0, cap 40). 977 validated = 977 unique leaderboard names but 973 npz on this case-insensitive APFS volume: 4 case-variant pairs are one Hub repo (same run id) - harmless, informational. Primary 590 entries = 552 distinct prediction vectors.
- Phase 3: independent implementation (audit/tools/independent_verify.py, independent_checks.py) reproduces all 12 analyses to 1.2e-9; headline 13.293 pts, jackknife CI [10.78, 15.80]. New: dropping top-2 roots -> 15.95 [12.8, 19.1]; same-uploader control -> 12.93; cleaned 12.78.

## Status: all phases performed (2026-10-10). See EXECUTIVE_RESEARCH_AUDIT.md. Not done / blocked: full 977-file re-download; Monte Carlo re-runs; analyses needing datasets/mmlu_redux; anonymous download test.
