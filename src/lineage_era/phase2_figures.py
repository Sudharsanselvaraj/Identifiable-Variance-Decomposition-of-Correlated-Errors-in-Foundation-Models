"""phase2_figures — compatibility shim.

Moved to ``analysis/plots.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_figures`` keeps working.
"""
from .analysis.plots import *  # noqa: F401,F403
from .analysis.plots import main

if __name__ == "__main__":
    raise SystemExit(main())
