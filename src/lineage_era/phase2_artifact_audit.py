"""phase2_artifact_audit — compatibility shim.

Moved to ``analysis/artifact_audit.py`` (2026-08-03 audit restructure); kept as
a re-export so the CLI ``python3 -m lineage_era.phase2_artifact_audit`` keeps
working.
"""
from .analysis.artifact_audit import *  # noqa: F401,F403
from .analysis.artifact_audit import main

if __name__ == "__main__":
    raise SystemExit(main())
