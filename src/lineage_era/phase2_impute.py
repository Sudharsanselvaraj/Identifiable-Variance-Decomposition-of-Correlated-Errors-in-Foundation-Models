"""phase2_impute — compatibility shim.

Moved to ``analysis/impute.py``; kept as a re-export so the CLI
``python3 -m lineage_era.phase2_impute`` works (see the module docstring for
the pre-registered imputation protocol and usage).
"""
from .analysis.impute import *  # noqa: F401,F403
from .analysis.impute import main

if __name__ == "__main__":
    raise SystemExit(main())
