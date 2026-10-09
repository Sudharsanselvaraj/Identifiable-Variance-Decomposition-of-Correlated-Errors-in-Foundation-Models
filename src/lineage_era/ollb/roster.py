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
ALIASES = OUT_DIR / "repo_aliases.json"   # old repo id -> current id (renames)

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


def load_aliases() -> dict[str, str]:
    return json.loads(ALIASES.read_text()) if ALIASES.exists() else {}


class HubUnavailable(Exception):
    """Transient Hub failure; the repo is retried on the next run, never cached."""


def hub_parent(repo_id: str, retries: int = 5) -> tuple[str, str | None]:
    """(current repo id, declared single base_model); parent None = root,
    missing or merge. The current id differs from ``repo_id`` after a rename.

    Rate limits and network errors raise HubUnavailable instead of returning
    None, so a throttled request is never recorded as "this model is a root".
    """
    import time

    from huggingface_hub import HfApi
    from huggingface_hub.utils import (GatedRepoError, HfHubHTTPError,
                                       RepositoryNotFoundError)

    for attempt in range(retries):
        try:
            info = HfApi().model_info(repo_id)
            break
        except (RepositoryNotFoundError, GatedRepoError):
            return repo_id, None
        except HfHubHTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (400, 404, 410):
                return repo_id, None
            time.sleep(min(60, 5 * 2 ** attempt))
        except (OSError, ValueError):
            time.sleep(min(60, 5 * 2 ** attempt))
    else:
        raise HubUnavailable(repo_id)
    base = info.card_data.get("base_model") if info.card_data else None
    if isinstance(base, list):
        if len(base) != 1:      # multi-parent = merge; treat as unresolved root
            return info.id, None
        base = base[0]
    ok = isinstance(base, str) and base not in (repo_id, info.id)
    return info.id, base if ok else None


def resolve_missing(names: list[str], parent: dict, cache: dict,
                    aliases: dict, workers: int = 8) -> None:
    """Breadth-first Hub resolution of every ancestor not yet known."""
    from concurrent.futures import ThreadPoolExecutor

    def unknown(n: str | None) -> bool:
        return isinstance(n, str) and n not in parent and n not in cache

    # Leaderboard roots (parent None) are queried too, only to record renames
    # so that e.g. Meta-Llama-3.1-8B and Llama-3.1-8B become one root.
    roots = {n for n in names if n in parent and parent[n] is None
             and n not in cache}
    frontier = sorted({n for n in names if unknown(n)} | roots
                      | {p for p in parent.values() if unknown(p)})
    level = 0
    while frontier:
        print(f"resolve level {level}: {len(frontier)} repos", flush=True)
        with ThreadPoolExecutor(workers) as pool:
            results = list(pool.map(_safe_parent, frontier))
        failed = 0
        for n, (ok, current, p) in zip(frontier, results):
            if ok:
                cache[n] = p
                if current != n:
                    aliases[n] = current
            else:
                failed += 1
        CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
        ALIASES.write_text(json.dumps(aliases, indent=0, sort_keys=True))
        print(f"  cached {len(frontier) - failed}, transient failures {failed}",
              flush=True)
        frontier = sorted({p for n, p in cache.items() if unknown(p)})
        level += 1
        if level > MAX_DEPTH:
            break


def _safe_parent(n: str) -> tuple[bool, str, str | None]:
    try:
        return (True, *hub_parent(n))
    except HubUnavailable:
        return False, n, None


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
    cache, aliases = load_cache(), load_aliases()
    if resolve:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        resolve_missing(list(meta.name), parent, cache, aliases)

    def parent_of(n: str) -> str | None:
        return parent[n] if n in parent else cache.get(n)

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
        root = aliases.get(root, root)
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
