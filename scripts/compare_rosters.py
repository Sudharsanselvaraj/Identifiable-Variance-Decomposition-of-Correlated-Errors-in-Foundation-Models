#!/usr/bin/env python3
"""Freeze and compare the Exp04 primary and expanded rosters (metadata only).

For each population (and its strict variant, roots verified as pretrained on
the leaderboard) reports: models, roots, root orgs, months, crossing (roots in
>= 2 months, months with >= 2 roots), connectedness of the root-month
bipartite graph (largest component share), the fixed-effects diagnostics
(rank, kappa) on root x quarter, and the analytic random-effects precision
gate on root x quarter for the per-model trait.

Also writes the frozen rosters with a SHA-256 so the bulk download can be
pinned to exactly these model lists.

Usage (repo root): python3 scripts/compare_rosters.py
Outputs: datasets/ollb/frozen/{primary,expanded}.csv,
         results/exp04_rosters/{comparison.csv, comparison.md, recovery.md}
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lineage_era.analysis.precision_gate import (  # noqa: E402
    SCENARIOS, analytic_precision, covariance_basis_rank, incidence)
from lineage_era.ollb.roster_v1 import build  # noqa: E402

OUT = ROOT / "results" / "exp04_rosters"
FROZEN = ROOT / "datasets" / "ollb" / "frozen"
CAP = 40


def largest_component_share(df: pd.DataFrame) -> float:
    """Share of models in the largest connected root-month component."""
    adj: dict[str, set[str]] = {}
    for r, m in zip("R:" + df["root"], "M:" + df["created_month"]):
        adj.setdefault(r, set()).add(m)
        adj.setdefault(m, set()).add(r)
    seen, best = set(), set()
    for start in adj:
        if start in seen:
            continue
        comp, stack = set(), [start]
        while stack:
            v = stack.pop()
            if v not in comp:
                comp.add(v)
                stack.extend(adj[v] - comp)
        seen |= comp
        best = max(best, comp, key=len)
    roots = {v[2:] for v in best if v.startswith("R:")}
    return float(df["root"].isin(roots).mean())


def fixed_effects(df: pd.DataFrame) -> dict:
    zf, ze = incidence(df.rename(columns={"quarter": "era"}))
    X = np.column_stack([np.ones(len(df)), zf[:, 1:], ze[:, 1:]])
    rank = int(np.linalg.matrix_rank(X))
    return {"fe_rank": rank, "fe_p": X.shape[1],
            "fe_kappa": float(np.linalg.cond(X.T @ X))}


def describe(df: pd.DataFrame, label: str) -> dict:
    per_root = df.groupby("root").created_month.nunique()
    per_month = df.groupby("created_month").root.nunique()
    q = df.assign(era=pd.PeriodIndex(df.created_month, freq="M").asfreq("Q").astype(str))
    zf, ze = incidence(q.rename(columns={"root": "family"}))
    gate = {k: analytic_precision(zf, ze, v) for k, v in SCENARIOS.items()}
    return {
        "population": label, "models": len(df), "roots": df.root.nunique(),
        "root_orgs": df.root.str.split("/").str[0].nunique(),
        "months": df.created_month.nunique(),
        "span": f"{df.created_month.min()}..{df.created_month.max()}",
        "roots_ge2_models": int((df.root.value_counts() >= 2).sum()),
        "roots_ge2_months": int((per_root >= 2).sum()),
        "months_ge2_roots": int((per_month >= 2).sum()),
        "largest_component_share": round(largest_component_share(df), 3),
        "top_root_share": round(df.root.value_counts(normalize=True).iloc[0], 3),
        **fixed_effects(q.rename(columns={"root": "family"})),
        "cov_basis_rank": covariance_basis_rank(zf, ze),
        "max_se_share_per_model_trait": round(max(
            max(g["se_share_family"], g["se_share_era"]) for g in gate.values()), 3),
    }


def main() -> int:
    roster = build()
    OUT.mkdir(parents=True, exist_ok=True)
    FROZEN.mkdir(parents=True, exist_ok=True)
    pops = {
        "primary": roster[roster.eligible_primary],
        "expanded": roster[roster.eligible_expanded].assign(
            root=lambda d: d.root_x, root_verified=lambda d: d.root_verified_x),
    }
    rows, hashes = [], {}
    for name, pop in pops.items():
        pop = pop[pop.created_month.notna()]
        cols = ["repo", "model", "root", "root_verified", "created_month",
                "params_b", "architecture", "type"] + \
            (["lineage_source_x"] if name == "expanded" else [])
        frozen = pop[cols].sort_values("model").reset_index(drop=True)
        path = FROZEN / f"{name}.csv"
        frozen.to_csv(path, index=False)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        # Download sample: same rule as scripts/run_pair_gate.py (seed 0,
        # at most CAP models per root), Amendment 2.
        samp = (frozen.sample(frac=1, random_state=0).groupby("root").head(CAP)
                .sort_values("model").reset_index(drop=True))
        spath = FROZEN / f"{name}_sample_cap{CAP}.csv"
        samp.to_csv(spath, index=False)
        hashes[f"{name}_sample_cap{CAP}"] = hashlib.sha256(spath.read_bytes()).hexdigest()
        rows.append(describe(pop[pop.model.isin(samp.model)], f"{name}_sample_cap{CAP}"))
        rows.append(describe(pop, name))
        rows.append(describe(pop[pop.root_verified], f"{name}_strict"))
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "comparison.csv", index=False)

    # How many of the undeclared-parent exclusions were actually recovered.
    cfg = pd.DataFrame(map(json.loads, (ROOT / "datasets/ollb/config_lineage.jsonl")
                           .read_text().splitlines()))
    cfg = cfg.drop_duplicates("model", keep="last")     # resumed runs append
    rec = roster[roster.exclusion_primary == "undeclared_parent"]
    recovered = int(rec.eligible_expanded.sum())
    still = rec.loc[~rec.eligible_expanded, "exclusion_expanded"].value_counts()
    (OUT / "recovery.md").write_text(
        "# Config-based ancestry recovery\n\n"
        f"Models excluded from primary only for an undeclared parent: {len(rec)}\n\n"
        "## `_name_or_path` outcomes\n\n"
        + cfg.outcome.value_counts().to_frame("models").to_markdown() + "\n\n"
        f"Recovered into the expanded roster: **{recovered}** of {len(rec)}\n\n"
        "## Why the rest stay excluded (expanded walk)\n\n"
        + still.to_frame("models").to_markdown() + "\n")
    (OUT / "comparison.md").write_text(
        "# Exp04 roster comparison (frozen, metadata only)\n\n"
        + comp.set_index("population").T.to_markdown() + "\n\n## Frozen roster hashes (SHA-256)\n\n"
        + "\n".join(f"- `{k}.csv`: `{v}`" for k, v in hashes.items()) + "\n")
    print(comp.T.to_string(header=False))
    print(json.dumps(hashes, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
