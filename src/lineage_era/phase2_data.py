"""phase2_data — compatibility shim.

Moved to ``analysis/population.py`` (2026-08-03 review restructure); kept as a
re-export so existing callers (``phase2_sensitivity.kim_crosscheck``) keep
working.
"""
from .analysis.population import *  # noqa: F401,F403
from .analysis.population import main

if __name__ == "__main__":
    raise SystemExit(main())
