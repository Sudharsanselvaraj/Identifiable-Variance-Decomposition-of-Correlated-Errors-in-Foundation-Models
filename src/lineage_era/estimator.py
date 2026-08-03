"""estimator — compatibility shim for the REML engine.

Moved to ``analysis/reml.py`` (per the 2026-08-03 review restructure). This
module re-exports the full public API so existing imports
(``from . import estimator``) keep working unchanged.
"""
from .analysis.reml import *  # noqa: F401,F403
