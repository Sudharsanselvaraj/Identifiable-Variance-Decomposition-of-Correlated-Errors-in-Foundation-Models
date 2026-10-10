# Invalid data: do not use

The per-item files in this folder come from the earlier per-model evaluation
(16 of 20 planned runs), whose findings are withdrawn. The extraction script
kept one option score per item, so every file predicts option A on all 14,042
MMLU items. `datasets/phase2_eval_results.csv` holds the aggregate scores of the
same runs and is equally invalid.

No current analysis, table or figure reads these files. They are kept, unchanged,
as the audit trail described in Supplementary Section S7 of the manuscript and in
[RESEARCH_STATUS.md](../../RESEARCH_STATUS.md).
