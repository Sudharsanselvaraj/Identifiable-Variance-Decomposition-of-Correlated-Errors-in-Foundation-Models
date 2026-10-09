#!/usr/bin/env python3
"""Exp04, second external review: post-hoc analyses (none pre-registered).

  R1  release timing measured by the ROOT's Hub release month (proxy for the
      pretraining era of the base), in place of / alongside the fine-tune's
      upload month
  R2  equivalence-style bounds for the same-month coefficient (90% CIs from the
      delete-one-root jackknife: the largest |effect| not excluded)
  R3  lineage dose-response: ancestor-descendant, sibling (same immediate
      parent) and more distant same-root pairs; tree distance
  R4  CAPA-style chance-adjusted agreement (Goel et al.) computed from the
      chosen options, as an alternative outcome
  R5  independent check of declared lineage: each primary model's config.json
      `_name_or_path` (read-only GET, cached in
      datasets/ollb/config_check_primary.jsonl, never written to the frozen Hub
      cache); where it names a cached Hub repo other than the model, does the
      chain from it reach the same root as the card-declared chain?
  R6  data quality: (a) degenerate models choosing one letter on >= 95% of
      items; (b) clusters of models with identical predictions (>= 99.9% of
      items, mostly the same repository listed under two names); the
      pre-registered model refitted without (a), with (b) collapsed to one
      model, and both

Chains are rebuilt with the same rules as lineage_era.ollb.roster_v1 and must
end at the root recorded in the frozen lists (checked; mismatches reported).

Usage (repo root): python3 scripts/run_exp04_revision2.py
Output: results/exp04_revision2/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb.hub_meta import load as load_hub  # noqa: E402
from lineage_era.ollb.pair_gate import design, month_index, ols_twoway  # noqa: E402
from lineage_era.ollb.roster_v1 import MAX_DEPTH, META, MIRRORS, load_config_links  # noqa: E402
from run_exp04_final import jackknife_roots, prepared  # noqa: E402

OUT = ROOT / "results" / "exp04_revision2"
Z90, Z95 = norm.ppf(0.95), norm.ppf(0.975)


# ------------------------------------------------------------------ lineage graph
def graph():
    """Same graph as roster_v1.build(): canonical ids, single parents, merges."""
    meta = pd.read_csv(META).drop_duplicates("fullname")
    hub = load_hub()
    canon = {r: rec["id"] for r, rec in hub.items()}
    hub = {**hub, **{rec["id"]: rec for rec in hub.values()}}
    node = lambda r: canon.get(r, r)  # noqa: E731
    parent, multi = {}, set()
    for rec in hub.values():
        bm = rec["base_model"]
        if bm and len(bm) > 1:
            multi.add(rec["id"])
        parent[rec["id"]] = node(bm[0]) if bm and len(bm) == 1 else None
    del meta
    return hub, node, parent, multi


def chain(start, node, parent, multi, hub, first_hop=None):
    """Nodes from the model to its root, following roster_v1.walk()."""
    n, out = node(start), []
    for depth in range(MAX_DEPTH):
        out.append(n)
        if n in multi:
            return out, "via_merge"
        p = first_hop if (depth == 0 and first_hop) else parent.get(n, "?")
        if p == "?":
            return out, "ancestor_not_fetched"
        if depth > 0 and hub.get(n, {}).get("status") == "missing":
            return out, "ancestor_missing"
        if (p is None or p == n) and n in MIRRORS:
            p = node(MIRRORS[n])
        if p is None or p == n:
            return out, "ok"
        if p in out:
            return out, "cycle"
        n = node(p)
    return out, "too_deep"


def jk(X, y, d):
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    se = jackknife_roots(X, y, d["rid"], d["i"], d["j"])
    return b, se


def row(label, pop, names, b, se, term, extra=None):
    k = names.index(term)
    r = {"analysis": label, "population": pop, "term": term, "estimate": b[k],
         "se_jackknife": se[k], "ci95_low": b[k] - Z95 * se[k],
         "ci95_high": b[k] + Z95 * se[k], "ci90_low": b[k] - Z90 * se[k],
         "ci90_high": b[k] + Z90 * se[k],
         "p": 2 * norm.sf(abs(b[k] / se[k]))}
    r["equivalence_bound_90"] = max(abs(r["ci90_low"]), abs(r["ci90_high"]))
    return {**r, **(extra or {})}


# ------------------------------------------------------------------ R5
CFG_CHECK = ROOT / "datasets" / "ollb" / "config_check_primary.jsonl"
DISAGREE: set[str] = set()         # models whose config chain reaches another root


def config_check(pop, node, parent, multi, hub) -> dict:
    from concurrent.futures import ThreadPoolExecutor

    from lineage_era.ollb.config_lineage import classify, read_name_or_path
    done = {}
    if CFG_CHECK.exists():
        done = {r["model"]: r for r in map(json.loads, CFG_CHECK.read_text().splitlines())}
    todo = [m for m in pop.model if m not in done]
    if todo:
        def work(m):
            try:
                st, raw = read_name_or_path(m)
            except RuntimeError:
                return None
            outcome, cand = classify(m, raw, st)
            return {"model": m, "raw": raw, "outcome": outcome, "candidate": cand}
        with ThreadPoolExecutor(6) as pool:
            for r in pool.map(work, todo):
                if r:
                    done[r["model"]] = r
        CFG_CHECK.write_text("".join(json.dumps(done[m]) + "\n" for m in sorted(done)))
    counts = {"models": len(pop), "read": 0, "names_cached_hub_repo": 0,
              "same_root": 0, "other_root": 0, "chain_unresolved": 0,
              "self_or_unusable": 0, "not_in_cache": 0}
    examples = []
    for m, r in zip(pop.model, pop.root):
        rec = done.get(m)
        if rec is None:
            continue
        counts["read"] += 1
        if rec["outcome"] != "candidate":
            counts["self_or_unusable"] += 1
            continue
        cand = node(rec["candidate"])
        if cand not in hub or hub[cand].get("status") != "ok":
            counts["not_in_cache"] += 1
            continue
        if cand == node(m):
            counts["self_or_unusable"] += 1
            continue
        counts["names_cached_hub_repo"] += 1
        c, st = chain(m, node, parent, multi, hub, first_hop=cand)
        if st != "ok":
            counts["chain_unresolved"] += 1
        elif c[-1] == node(r):
            counts["same_root"] += 1
        else:
            counts["other_root"] += 1
            examples.append((m, r, c[-1]))
            DISAGREE.add(m)
    counts["other_root_examples"] = examples[:15]
    return counts


# ------------------------------------------------------------------ main
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hub, node, parent, multi = graph()
    rows, info = [], {}

    for pop_name, min_acc in (("primary", None), ("primary", 0.30),
                              ("expanded", None), ("expanded", 0.30)):
        tag = pop_name + ("_S2" if min_acc else "")
        d = prepared(pop_name, min_acc=min_acc)
        pop, i, j, y, X, names = d["pop"], d["i"], d["j"], d["y"], d["X"], d["names"]

        # R2: equivalence bounds for the pre-registered model
        b, se = jk(X, y, d)
        for t in ("same_root", "gap0"):
            rows.append(row("pre-registered model", tag, names, b, se, t))

        # R1: root release month
        rmon_raw = [hub.get(node(r), {}).get("created_at") for r in pop.root]
        ok = np.array([m is not None for m in rmon_raw])
        info[f"{tag}_roots_with_release_month"] = f"{ok.sum()} of {len(ok)} models"
        keep = ok[i] & ok[j]
        rmon = month_index(pd.Series([m[:7] if m else "2000-01" for m in rmon_raw]))
        Xr, nr = design(i, j, d["rid"], rmon, d["acc"])
        Xr, yk = Xr[keep], y[keep]
        dk = {**d, "i": i[keep], "j": j[keep]}
        b, se = jk(Xr, yk, dk)
        for t in ("same_root", "gap0", "gap1_2", "gap3_5", "gap6_11"):
            rows.append(row("root release month in place of upload month", tag, nr, b,
                            se, t))
        gcols = [nr.index(g) for g in ("gap0", "gap1_2", "gap3_5", "gap6_11")]
        Xb = np.column_stack([X[keep], Xr[:, gcols]])
        nb = names + [f"root_{g}" for g in ("gap0", "gap1_2", "gap3_5", "gap6_11")]
        b, se = jk(Xb, yk, dk)
        for t in ("same_root", "gap0", "root_gap0", "root_gap1_2", "root_gap6_11"):
            rows.append(row("upload month and root release month together", tag, nb, b,
                            se, t))
        diff_root = d["rid"][i] != d["rid"][j]
        info[f"{tag}_different_root_pairs_same_root_month"] = int(
            (diff_root & (rmon[i] == rmon[j]) & keep).sum())

        # R4: CAPA-style chance-adjusted agreement from chosen options
        pred, acc = d["pred"], d["acc"]
        same = sum((pred == o).astype(np.float32) @ (pred == o).astype(np.float32).T
                   for o in range(4)) / pred.shape[1]
        c_obs = same[i, j]
        c_exp = acc[i] * acc[j] + (1 - acc[i]) * (1 - acc[j]) / 3
        capa = (c_obs - c_exp) / (1 - c_exp)
        for label, cols in (("CAPA outcome, with accuracy terms", list(range(len(names)))),
                            ("CAPA outcome, without accuracy terms",
                             [k for k, n in enumerate(names) if not n.startswith("acc")])):
            b, se = jk(X[:, cols], capa, d)
            nm = [names[k] for k in cols]
            for t in ("same_root", "gap0"):
                rows.append(row(label, tag, nm, b, se, t,
                                {"outcome_mean": float(capa.mean())}))

        # R6: data quality
        share = np.stack([(pred == o).mean(1) for o in range(4)], 1).max(1)
        degenerate = share >= 0.95
        ident = same[i, j] >= 0.999
        import scipy.sparse as sp
        from scipy.sparse.csgraph import connected_components
        N = len(pop)
        _, lab = connected_components(sp.coo_matrix(
            (np.ones(ident.sum()), (i[ident], j[ident])), shape=(N, N)), directed=False)
        first = np.zeros(N, bool)
        for c in np.unique(lab):
            idx = np.flatnonzero(lab == c)
            first[idx[np.argsort(pop.model.values[idx])[0]]] = True
        info[f"{tag}_degenerate_models"] = int(degenerate.sum())
        info[f"{tag}_identical_pairs"] = {"total": int(ident.sum()),
                                          "same_root": int((ident & (d["rid"][i] == d["rid"][j])).sum())}
        for label, keep_m in (("data quality: without degenerate models", ~degenerate),
                              ("data quality: identical-prediction clusters collapsed", first),
                              ("data quality: both", ~degenerate & first)):
            m = keep_m[i] & keep_m[j]
            b, se = jk(X[m], y[m], {**d, "i": i[m], "j": j[m]})
            for t in ("same_root", "gap0"):
                rows.append(row(label, tag, names, b, se, t,
                                {"models": int(keep_m.sum()), "pairs": int(m.sum())}))

        if tag != "primary":
            continue

        # R3: dose-response among same-root pairs (primary)
        ch, mism = [], 0
        for m, r in zip(pop.model, pop.root):
            c, st = chain(m, node, parent, multi, hub)
            ch.append(c)
            mism += c[-1] != node(r)
        info["primary_chain_root_mismatches"] = mism
        ids = [c[0] for c in ch]
        sr = d["rid"][i] == d["rid"][j]
        rel = np.full(len(i), "different root", dtype=object)
        dist = np.zeros(len(i), int)
        for k in np.flatnonzero(sr):
            a, bb = ch[i[k]], ch[j[k]]
            common = next(n for n in a if n in bb)
            dist[k] = a.index(common) + bb.index(common)
            if dist[k] == 0:
                rel[k] = "same repository"
            elif ids[i[k]] in bb or ids[j[k]] in a:
                rel[k] = "ancestor-descendant"
            elif len(a) > 1 and len(bb) > 1 and a[1] == bb[1]:
                rel[k] = "siblings"
            else:
                rel[k] = "more distant"
        info["primary_same_root_pair_types"] = (
            pd.Series(rel[sr]).value_counts().to_dict())
        info["primary_same_root_tree_distance"] = (
            pd.Series(dist[sr]).value_counts().sort_index().to_dict())
        types = ["same repository", "ancestor-descendant", "siblings", "more distant"]
        Xd = np.column_stack([X[:, :1]] + [(rel == t).astype(float) for t in types]
                             + [X[:, 2:]])
        nd = names[:1] + types + names[2:]
        b, se = jk(Xd, y, d)
        for t in types[1:]:
            rows.append(row("lineage dose-response: relation type", tag, nd, b, se, t,
                            {"pairs": int((rel == t).sum())}))
        bins = [("distance 0 (same repository)", dist == 0), ("distance 1", dist == 1),
                ("distance 2", dist == 2), ("distance 3+", dist >= 3)]
        Xt = np.column_stack([X[:, :1]] + [(sr & m).astype(float) for _, m in bins]
                             + [X[:, 2:]])
        nt = names[:1] + [n for n, _ in bins] + names[2:]
        b, se = jk(Xt, y, d)
        for t, m in bins[1:]:
            rows.append(row("lineage dose-response: tree distance", tag, nt, b, se, t,
                            {"pairs": int((sr & m).sum())}))

        # R5: independent lineage evidence from config.json
        info["primary_config_check"] = config_check(pop, node, parent, multi, hub)
        keep_m = ~pop.model.isin(DISAGREE).to_numpy()
        m = keep_m[i] & keep_m[j]
        b, se = jk(X[m], y[m], {**d, "i": i[m], "j": j[m]})
        for t in ("same_root", "gap0"):
            rows.append(row("without models whose config contradicts the card", tag, names,
                            b, se, t, {"models": int(keep_m.sum()), "pairs": int(m.sum())}))

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "revision2.csv", index=False)
    (OUT / "info.json").write_text(json.dumps(info, indent=1, default=str))
    pd.set_option("display.width", 220)
    print(json.dumps(info, indent=1, default=str))
    print(res[["analysis", "population", "term", "estimate", "ci95_low", "ci95_high", "p",
               "equivalence_bound_90"]].round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
