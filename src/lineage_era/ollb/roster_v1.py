"""Outcome-independent roster for the v1 leaderboard (Exp04 primary arm).

Inputs (metadata only; the v1 score columns were never saved):
    datasets/ollb/v1_contents_meta.csv   leaderboard metadata columns
    datasets/ollb/hub_meta.jsonl         Hub base_model / created_at / renames

Each model gets: lineage root (walk of single-parent ``base_model`` links,
renames collapsed), depth, root organisation, Hub creation month, and an
eligibility flag with the reason for any exclusion.

Usage (repo root):  python3 -m lineage_era.ollb.roster_v1
Output: datasets/ollb/v1_roster.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .hub_meta import load as load_hub

ROOT = Path(__file__).resolve().parents[3]
META = ROOT / "datasets" / "ollb" / "v1_contents_meta.csv"
OUT = ROOT / "datasets" / "ollb" / "v1_roster.csv"
MAX_DEPTH = 20
PRETRAINED = ("pretrained", "continuously pretrained")


def build() -> pd.DataFrame:
    meta = (pd.read_csv(META).drop_duplicates("fullname")
            .rename(columns={"Weight type": "weight_type", "#Params (B)": "params_b"}))
    hub = load_hub()
    canon = {r: rec["id"] for r, rec in hub.items()}

    def node(repo: str) -> str:
        return canon.get(repo, repo)

    # parent links keyed by canonical id; multi-parent (merge) => no parent
    parent: dict[str, str | None] = {}
    multi: set[str] = set()
    for rec in hub.values():
        bm = rec["base_model"]
        key = rec["id"]
        if bm and len(bm) > 1:
            multi.add(key)
        parent[key] = node(bm[0]) if bm and len(bm) == 1 else None

    def walk(repo: str) -> tuple[str, int, bool]:
        n, depth, seen = node(repo), 0, set()
        while depth < MAX_DEPTH:
            seen.add(n)
            if n in multi:
                return n, depth, False          # lineage passes through a merge
            if n not in parent:
                return n, depth, False          # ancestor never fetched
            p = parent[n]
            if p is None or p == n:
                return n, depth, True
            if p in seen:
                return n, depth, False
            n, depth = p, depth + 1
        return n, depth, False

    rows = []
    for r in meta.itertuples(index=False):
        repo = r.fullname
        rec = hub.get(repo)
        root, depth, resolved = walk(repo)
        typ = str(r.Type) if isinstance(r.Type, str) else ""
        reasons = []
        if rec is None:
            reasons.append("hub_not_fetched")
        elif rec["status"] != "ok":
            reasons.append("hub_missing")
        if bool(r.Merged) or "merge" in typ or (rec and node(repo) in multi):
            reasons.append("merge")
        if bool(r.Flagged):
            reasons.append("flagged")
        if r.weight_type != "Original":         # Adapter / Delta weights
            reasons.append("adapter_or_delta")
        if not resolved:
            reasons.append("lineage_unresolved")
        # A depth-0 model is a true root only if it is a pretrained checkpoint;
        # a fine-tune with no declared parent has unknown lineage.
        if resolved and depth == 0 and not any(t in typ for t in PRETRAINED):
            reasons.append("undeclared_parent")
        created = rec.get("created_at") if rec else None
        rows.append({
            "repo": f"details_{repo.replace('/', '__')}", "model": repo,
            "id": node(repo), "root": root, "root_org": root.split("/")[0],
            "depth": depth, "type": typ, "architecture": r.Architecture,
            "params_b": r.params_b, "created_month": created[:7] if created else None,
            "eligible": not reasons, "exclusion": ";".join(reasons),
        })
    return pd.DataFrame(rows)


def main() -> int:
    roster = build()
    roster.to_csv(OUT, index=False)
    e = roster[roster.eligible]
    per_root = e.groupby("root").agg(n=("model", "size"),
                                     months=("created_month", "nunique"))
    print(f"models {len(roster)}  eligible {len(e)}  roots {len(per_root)}  "
          f"roots>=2 models {(per_root.n >= 2).sum()}  "
          f"roots>=2 months {(per_root.months >= 2).sum()}  "
          f"months {e.created_month.nunique()}")
    print(roster.exclusion.str.split(";").explode().value_counts().to_string())
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
