"""Phase 2 metadata: merge occupancy + manifest into the analysis design frame.

Combines the authoritative Phase 0 occupancy table (family, quarter), the
live HF manifest from ``phase2_eval.EVAL_MANIFEST`` (hf_repo, params, access),
release-date overrides (``occupancy.ERA_DIVERGENCES``), and analysis flags
(leaked-model and verified-edge membership) into one per-model design frame.

This frame is the single input to the identifiability audit and the
CrossedREML model. It is written to results/phase2/analysis_design.csv.

Usage (from src/):
    python3 -m lineage_era.phase2_metadata [--out-dir results/phase2]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .occupancy import ERA_DIVERGENCES, VERIFIED_EDGES, model_table
from .phase2_eval import EVAL_MANIFEST

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"

# Cross-family teacher leakage (occupancy.CAVEATS items 4): these models train
# on data produced by another lab's models, so they violate the independence
# assumption to an unknown degree. They belong in V_era (shared environment).
LEAKED_MODELS = {"Phi-4", "Gemma-2-9B", "Gemma-4"}


def build_design(table: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-model design frame: occupancy x manifest x flags."""
    if table is None:
        table = model_table()
    rows = []
    for _, r in table.iterrows():
        fn = r["full_name"]
        repo, params, access = EVAL_MANIFEST[fn]
        rows.append({
            "full_name": fn,
            "family": r["family"],
            "era": r["quarter"],
            "short_name": r["short_name"],
            "hf_repo": repo,
            "params": params,
            "access": access,
            "release_date": release_date(fn),
            "leaked": fn in LEAKED_MODELS,
            "in_chain": fn in {e[0] for e in VERIFIED_EDGES} | {e[1] for e in VERIFIED_EDGES},
        })
    return pd.DataFrame(rows)


def release_date(full_name: str) -> str | None:
    """Public release date; diverges from HF createdAt for 4 documented models."""
    for fn, created, released in ERA_DIVERGENCES:
        if fn == full_name:
            return released
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    design = build_design()
    design.to_csv(out_dir / "analysis_design.csv", index=False)

    print(f"Design frame: {len(design)} models x {design.shape[1]} columns")
    print(f"  families={design['family'].nunique()} quarters={design['era'].nunique()} "
          f"leaked={int(design['leaked'].sum())} in_chain={int(design['in_chain'].sum())}")
    print(f"-> {out_dir / 'analysis_design.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
