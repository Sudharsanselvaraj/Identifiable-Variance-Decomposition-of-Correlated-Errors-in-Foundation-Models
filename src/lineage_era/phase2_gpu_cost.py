"""phase2_gpu_cost — compatibility shim.

Moved to ``analysis/gpu_cost.py`` (2026-08-03 GPU planning); kept as a
re-export so the CLI ``python3 -m lineage_era.phase2_gpu_cost`` keeps working.
"""
from .analysis.gpu_cost import *  # noqa: F401,F403
from .analysis.gpu_cost import main

if __name__ == "__main__":
    raise SystemExit(main())
