"""phase2_metadata — compatibility shim.

Moved to ``analysis/metadata.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_metadata`` keeps working.
"""
from .analysis.metadata import *  # noqa: F401,F403
from .analysis.metadata import main

if __name__ == "__main__":
    raise SystemExit(main())
