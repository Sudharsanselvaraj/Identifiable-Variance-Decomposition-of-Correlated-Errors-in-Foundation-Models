"""phase2_population_optimizer — compatibility shim.

Moved to ``analysis/population_optimizer.py`` (2026-08-03 G3 gate); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_population_optimizer``
keeps working.
"""
from .analysis.population_optimizer import *  # noqa: F401,F403
from .analysis.population_optimizer import main

if __name__ == "__main__":
    raise SystemExit(main())
