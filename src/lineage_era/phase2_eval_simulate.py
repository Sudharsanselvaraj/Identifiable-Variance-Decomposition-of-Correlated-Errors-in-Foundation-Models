"""phase2_eval_simulate — compatibility shim.

Moved to ``analysis/eval_simulate.py`` (2026-08-03 review restructure); kept as
a re-export so the CLI ``python3 -m lineage_era.phase2_eval_simulate`` keeps
working.
"""
from .analysis.eval_simulate import *  # noqa: F401,F403
from .analysis.eval_simulate import main

if __name__ == "__main__":
    raise SystemExit(main())
