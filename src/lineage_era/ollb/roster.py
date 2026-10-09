"""Outcome-independent roster for Exp04 (Open LLM Leaderboard population).

Reads ONLY metadata columns from the leaderboard contents snapshot; score
columns are never loaded (see ``META_COLS``). Produces one row per eligible
model with its lineage root, tree depth and upload month.

Ancestors that are not themselves on the leaderboard are resolved through the
Hugging Face Hub (``cardData.base_model``) only when ``resolve=True``; results
are cached in ``datasets/ollb/lineage_cache.json`` so the walk is reproducible.

Usage (repo root):
    python3 -m lineage_era.ollb.roster            # offline, cache only
    python3 -m lineage_era.ollb.roster --resolve  # query the Hub for missing parents
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CONTENTS = ROOT / "datasets" / "kim" / "hugging_face.csv"
OUT_DIR = ROOT / "datasets" / "ollb"
CACHE = OUT_DIR / "lineage_cache.json"

# Metadata only. Adding a score column here breaks outcome independence.
META_COLS = ["name", "type", "architecture", "is_merged", "is_moe", "is_flagged",
             "is_official_provider", "upload_date", "base_model", "params_billions"]
MERGE_TYPE = "basemergesandmoerges"
MAX_DEPTH = 20


def load_metadata(path: Path = CONTENTS) -> pd.DataFrame:
    d = pd.read_csv(path, usecols=META_COLS).drop_duplicates("name")
    return d.reset_index(drop=True)


def load_cache() -> dict[str, str | None]:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def hub_parent(repo_id: str) -> str | None:
    """First declared base_model of a Hub repo, or None (root / unknown)."""
    from huggingface_hub import HfApi
    from huggingface_hub.utils import HfHubHTTPError

    try:
        info = HfApi().model_info(repo_id)
    except (HfHubHTTPError, OSError, ValueError):
        return None
    base = (info.card_data or {}).get("base_model") if info.card_data else None
    if isinstance(base, list):
        if len(base) != 1:      # multi-parent = merge; treat as unresolved root
            return None
        base = base[0]
    return base if isinstance(base, str) and base != repo_id else None


def build_roster(resolve: bool = False) -> pd.DataFrame:
    meta = load_metadata()
    # A model listing itself as base_model is a root only if it is a
    # pretrained checkpoint; otherwise its parent is unknown and must come from
    # the Hub (left out of `parent` so parent_of falls through to the cache).
    pretrained = {"pretrained", "continuouslypretrained"}
    parent = {}
    for n, b, t in zip(meta.name, meta.base_model, meta.type):
        if not isinstance(b, str) or b == "Removed":
            parent[n] = None
        elif b == n:
            if t in pretrained:
                parent[n] = None
        else:
            parent[n] = b
    cache = load_cache()

    def parent_of(n: str) -> str | None:
        if n in parent:
            return parent[n]
        if n not in cache and resolve:
            cache[n] = hub_parent(n)
        return cache.get(n)

    def walk(n: str) -> tuple[str, int, bool]:
        """(root, depth, resolved) following single-parent base_model links."""
        depth, seen = 0, {n}
        while depth < MAX_DEPTH:
            p = parent_of(n)
            if p is None:
                # Leaf of the known graph: resolved only if we know n is a root.
                known_root = n in parent or n in cache
                return n, depth, known_root
            if p in seen:
                return n, depth, False
            seen.add(p)
            n, depth = p, depth + 1
        return n, depth, False

    rows = []
    for r in meta.itertuples(index=False):
        merge = bool(r.is_merged) or r.type == MERGE_TYPE \
            or str(r.base_model).endswith("(Merge)")
        root, depth, resolved = walk(r.name)
        rows.append({
            "name": r.name, "root": root, "root_org": root.split("/")[0],
            "depth": depth, "lineage_resolved": resolved,
            "upload_month": str(pd.Period(r.upload_date, "M")) if
            isinstance(r.upload_date, str) else None,
            "params_billions": r.params_billions, "architecture": r.architecture,
            "type": r.type, "is_moe": bool(r.is_moe),
            "eligible": not (merge or bool(r.is_flagged)
                             or r.base_model == "Removed"),
            "exclusion": ("merge" if merge else "flagged" if r.is_flagged else
                          "base_removed" if r.base_model == "Removed" else ""),
        })

    if resolve:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
    return pd.DataFrame(rows)


def summarize(roster: pd.DataFrame) -> dict:
    e = roster[roster.eligible]
    per_root = e.groupby("root").agg(n=("name", "size"),
                                     months=("upload_month", "nunique"))
    return {
        "models": len(roster), "eligible": len(e),
        "lineage_resolved": int(e.lineage_resolved.sum()),
        "roots": int(per_root.shape[0]),
        "roots_ge2_models": int((per_root.n >= 2).sum()),
        "roots_ge2_months": int((per_root.months >= 2).sum()),
        "root_orgs": int(e.root_org.nunique()),
        "upload_months": int(e.upload_month.nunique()),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--resolve", action="store_true",
                    help="query the HF Hub for parents missing from the snapshot")
    args = ap.parse_args(argv)
    roster = build_roster(resolve=args.resolve)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    roster.to_csv(OUT_DIR / "roster.csv", index=False)
    for k, v in summarize(roster).items():
        print(f"{k:>18}: {v}")
    print(f"-> {OUT_DIR / 'roster.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
