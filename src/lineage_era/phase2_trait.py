"""phase2_trait — compatibility shim.

Moved to ``analysis/trait.py`` (2026-08-03 review restructure); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_trait`` keeps working.
"""
from .analysis.trait import *  # noqa: F401,F403
from .analysis.trait import main

if __name__ == "__main__":
    raise SystemExit(main())
