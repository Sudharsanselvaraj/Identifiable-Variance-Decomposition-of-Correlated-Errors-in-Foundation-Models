"""phase2_identifiability — compatibility shim.

Moved to ``analysis/identifiability.py`` (2026-08-03 review restructure); kept
as a re-export so the CLI and callers (``phase2_simulate.audit``,
``phase2_decomposition``) keep working unchanged.
"""
from .analysis.identifiability import *  # noqa: F401,F403
from .analysis.identifiability import main

if __name__ == "__main__":
    raise SystemExit(main())
