"""phase2_bootstrap — compatibility shim.

Moved to ``analysis/bootstrap.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_bootstrap`` keeps working.
"""
from .analysis.bootstrap import *  # noqa: F401,F403
from .analysis.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
