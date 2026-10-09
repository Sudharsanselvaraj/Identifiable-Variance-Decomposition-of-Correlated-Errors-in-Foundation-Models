"""Outcome-independent rosters for the v1 leaderboard (Exp04 primary arm).

Inputs (metadata only; the v1 score columns were never saved):
    datasets/ollb/v1_contents_meta.csv   leaderboard metadata columns
    datasets/ollb/hub_meta.jsonl         Hub base_model / created_at / renames
    datasets/ollb/config_lineage.jsonl   validated config.json parent links

Two populations are built and frozen side by side:

* primary  -- every lineage link comes from a model card's ``base_model``;
* expanded -- primary, plus models whose missing card link is supplied by a
  validated ``_name_or_path`` link (``config_lineage``, outcome ``ok``). Only
  the model's own first hop may come from config; everything above it must
  still be card-declared.

Each model gets: lineage root (single-parent walk, renames collapsed), depth,
root organisation, Hub creation month, the source of its first lineage hop,
and per-population eligibility with the reason for every exclusion.

Usage (repo root):  python3 -m lineage_era.ollb.roster_v1
Output: datasets/ollb/v1_roster.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .hub_meta import load as load_hub

ROOT = Path(__file__).resolve().parents[3]
META = ROOT / "datasets" / "ollb" / "v1_contents_meta.csv"
CONFIG = ROOT / "datasets" / "ollb" / "config_lineage.jsonl"
OUT = ROOT / "datasets" / "ollb" / "v1_roster.csv"
MAX_DEPTH = 20
PRETRAINED = ("pretrained", "continuously pretrained")

# Re-uploads / quantised mirrors that declare no base_model, mapped to the
# checkpoint they copy. Curated from repo names and cards (metadata only);
# every entry is a straight copy or quantisation, not a fine-tune.
MIRRORS = {
    "unsloth/mistral-7b-bnb-4bit": "mistralai/Mistral-7B-v0.1",
    "unsloth/llama-3-8b-Instruct": "meta-llama/Meta-Llama-3-8B-Instruct",
    "unsloth/llama-3-8b-bnb-4bit": "meta-llama/Meta-Llama-3-8B",
    "unsloth/tinyllama-chat-bnb-4bit": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "NousResearch/Meta-Llama-3-8B": "meta-llama/Meta-Llama-3-8B",
    "kuotient/Meta-Llama-3-8B": "meta-llama/Meta-Llama-3-8B",
    "mistral-community/Mixtral-8x22B-v0.1": "mistralai/Mixtral-8x22B-v0.1",
    "NousResearch/Llama-2-7b-hf": "meta-llama/Llama-2-7b-hf",
    "NousResearch/Llama-2-13b-hf": "meta-llama/Llama-2-13b-hf",
}


def load_config_links() -> dict[str, str]:
    if not CONFIG.exists():
        return {}
    links = {}
    for line in CONFIG.read_text().splitlines():
        r = json.loads(line)
        if r.get("outcome") == "ok":
            links[r["model"]] = r["candidate"]
    return links


def build() -> pd.DataFrame:
    meta = (pd.read_csv(META).drop_duplicates("fullname")
            .rename(columns={"Weight type": "weight_type", "#Params (B)": "params_b"}))
    hub = load_hub()
    canon = {r: rec["id"] for r, rec in hub.items()}
    hub = {**hub, **{rec["id"]: rec for rec in hub.values()}}
    config_links = load_config_links()

    def node(repo: str) -> str:
        return canon.get(repo, repo)

    # Leaderboard type per canonical id: a chain may only END at a pretrained
    # checkpoint, never at a leaderboard fine-tune with an undeclared parent.
    lb_type = {node(n): str(t) if isinstance(t, str) else ""
               for n, t in zip(meta.fullname, meta.Type)}

    parent: dict[str, str | None] = {}
    multi: set[str] = set()
    for rec in hub.values():
        bm = rec["base_model"]
        key = rec["id"]
        if bm and len(bm) > 1:
            multi.add(key)
        parent[key] = node(bm[0]) if bm and len(bm) == 1 else None

    def walk(start: str, first_hop: str | None = None) -> tuple[str, int, str]:
        """(root, depth, status); status 'ok' or the reason the walk failed."""
        n, depth, seen = node(start), 0, set()
        while depth < MAX_DEPTH:
            seen.add(n)
            if n in multi:
                return n, depth, "via_merge"
            p = first_hop if (depth == 0 and first_hop) else parent.get(n, "?")
            if p == "?":
                return n, depth, "ancestor_not_fetched"
            if depth > 0 and hub.get(n, {}).get("status") == "missing":
                # declared ancestor is deleted or not a valid repo id
                return n, depth, "ancestor_missing"
            if (p is None or p == n) and n in MIRRORS:
                p = node(MIRRORS[n])               # mirror -> copied checkpoint
            if p is None or p == n:
                t = lb_type.get(n)
                if t is not None and not any(k in t for k in PRETRAINED):
                    # ends at a leaderboard fine-tune that declares no parent
                    return n, depth, ("undeclared_parent" if depth == 0
                                      else "root_is_finetune")
                return n, depth, "ok"
            if p in seen:
                return n, depth, "cycle"
            n, depth = node(p), depth + 1
        return n, depth, "too_deep"

    rows = []
    for r in meta.itertuples(index=False):
        repo = r.fullname
        rec = hub.get(repo)
        typ = str(r.Type) if isinstance(r.Type, str) else ""
        base = []
        if rec is None:
            base.append("hub_not_fetched")
        elif rec["status"] != "ok":
            base.append("hub_missing")
        # The v1 contents booleans are leaderboard display filters and are
        # INVERTED: True means "not merged" / "not flagged" (Flagged is True on
        # all 7,260 rows; 746 of 1,029 merge-type rows have Merged == False).
        if (not bool(r.Merged)) or "merge" in typ or (rec and node(repo) in multi):
            base.append("merge")
        if not bool(r.Flagged):
            base.append("flagged")
        if r.weight_type != "Original":         # Adapter / Delta weights
            base.append("adapter_or_delta")

        root, depth, status = walk(repo)
        source = "card"
        x_root, x_depth, x_status, x_source = root, depth, status, source
        if status == "undeclared_parent" and repo in config_links:
            x_root, x_depth, x_status = walk(repo, first_hop=config_links[repo])
            x_source = "config"
        created = rec.get("created_at") if rec else None

        def reasons(st: str) -> str:
            return ";".join(base + ([] if st == "ok" else [st]))

        rows.append({
            "repo": f"details_{repo.replace('/', '__')}", "model": repo,
            "id": node(repo), "type": typ, "architecture": r.Architecture,
            "params_b": r.params_b,
            "created_month": created[:7] if created else None,
            "root": root, "root_org": root.split("/")[0], "depth": depth,
            # strict variant: the chain ends at a checkpoint the leaderboard
            # itself lists as pretrained (else the root's type is unverified)
            "root_verified": any(k in lb_type.get(root, "") for k in PRETRAINED),
            "root_verified_x": any(k in lb_type.get(x_root, "") for k in PRETRAINED),
            "eligible_primary": not reasons(status),
            "exclusion_primary": reasons(status),
            "root_x": x_root, "root_org_x": x_root.split("/")[0], "depth_x": x_depth,
            "lineage_source_x": x_source,
            "eligible_expanded": not reasons(x_status),
            "exclusion_expanded": reasons(x_status),
        })
    return pd.DataFrame(rows)


def describe(roster: pd.DataFrame, which: str) -> dict:
    sfx = "" if which == "primary" else "_x"
    e = roster[roster[f"eligible_{which}"]]
    per_root = e.groupby(f"root{sfx}").agg(n=("model", "size"),
                                           months=("created_month", "nunique"))
    return {"population": which, "models": len(e), "roots": len(per_root),
            "roots_ge2_models": int((per_root.n >= 2).sum()),
            "roots_ge2_months": int((per_root.months >= 2).sum()),
            "root_orgs": e[f"root_org{sfx}"].nunique(),
            "months": e.created_month.nunique(),
            "first_month": e.created_month.min(), "last_month": e.created_month.max(),
            "config_links": int((e.get("lineage_source_x", pd.Series(dtype=str))
                                 == "config").sum()) if which == "expanded" else 0}


def main() -> int:
    roster = build()
    roster.to_csv(OUT, index=False)
    print(pd.DataFrame([describe(roster, "primary"),
                        describe(roster, "expanded")]).to_string(index=False))
    for which in ("primary", "expanded"):
        print(f"\nexclusions ({which}):")
        print(roster[f"exclusion_{which}"].replace("", "(eligible)")
              .str.split(";").explode().value_counts().to_string())
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
