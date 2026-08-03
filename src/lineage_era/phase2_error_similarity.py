"""phase2_error_similarity — compatibility shim.

Moved to ``analysis/error_similarity.py`` (2026-08-03 review restructure);
kept as a re-export so the CLI and the decomposition pipeline keep working.
"""
from .analysis.error_similarity import *  # noqa: F401,F403
from .analysis.error_similarity import main

if __name__ == "__main__":
    raise SystemExit(main())
