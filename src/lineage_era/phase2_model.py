"""phase2_model — compatibility shim.

Moved to ``analysis/reml.py`` (2026-08-03 review restructure: the θ_P / θ_M
model layer now lives with the REML engine); kept as a re-export so callers
(``phase2_sensitivity.shares_of``, ``phase2_decomposition``) keep working.
"""
from .analysis.reml import *  # noqa: F401,F403
from .analysis.reml import main

if __name__ == "__main__":
    raise SystemExit(main())
