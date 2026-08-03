"""phase2_report — compatibility shim.

Moved to ``analysis/report.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_report`` keeps working.
"""
from .analysis.report import *  # noqa: F401,F403
from .analysis.report import main

if __name__ == "__main__":
    raise SystemExit(main())
