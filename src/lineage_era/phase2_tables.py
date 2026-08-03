"""phase2_tables — compatibility shim.

Moved to ``analysis/report.py`` (2026-08-03 review restructure: table blocks
live with the report); kept as a re-export so the CLI and
``phase2_decomposition`` keep working unchanged.
"""
from .analysis.report import *  # noqa: F401,F403
from .analysis.report import main_tables as main

if __name__ == "__main__":
    raise SystemExit(main())
