"""phase2_eval_check — compatibility shim.

Moved to ``analysis/eval_check.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_eval_check`` keeps working.
"""
from .analysis.eval_check import *  # noqa: F401,F403
from .analysis.eval_check import main

if __name__ == "__main__":
    raise SystemExit(main())
