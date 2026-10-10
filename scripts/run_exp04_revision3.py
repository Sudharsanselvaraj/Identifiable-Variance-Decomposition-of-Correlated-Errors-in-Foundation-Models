#!/usr/bin/env python3
"""Exp04, third external review: post-hoc analyses (none pre-specified).

  R7   flexible accuracy control: quadratic accuracy surface; accuracy-cell
       fixed effects (unordered pairs of accuracy deciles, and of 20 bins);
       accuracy-matched pairs (|acc_i - acc_j| <= 0.02) with decile cells
  R8   lineage dose-response within root (root fixed effects, same-root pairs
       only), and a random-effects (DerSimonian-Laird) pooling of per-root
       shared-root coefficients, so every root counts once
  R9   pair-by-item linear probability model with item fixed effects for the
       same-wrong-option indicator on jointly wrong items, computed exactly
       from aggregates (no pair x item table is formed); delete-one-root
       jackknife
  R10  root-level cluster bootstrap (percentile CIs) and a root-label
       permutation test (labels shuffled among models of the same upload
       quarter, root sizes preserved)
  R11  simulation check re-run on the real roster with the models' real
       accuracies (so ability clusters by root and month as in the data), plus
       a scenario with no lineage or release-time effect in which agreement
       depends non-linearly on ability
  R12  MMLU answer-key sensitivity: items annotated as erroneous in MMLU-Redux
       2.0 (Gema et al.) removed, and the analysis restricted to its 5,700
       re-annotated items

Usage (repo root): python3 scripts/run_exp04_revision3.py [--only R7 R8 ...]
Output: results/exp04_revision3/  (one CSV per section, plus info_*.json)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb import analysis as A  # noqa: E402
from lineage_era.ollb.pair_gate import (GAP_BINS, Truth, design, month_index,  # noqa: E402
                                        ols_twoway, pair_agreement)
from run_exp04_final import jackknife_roots, prepared  # noqa: E402

OUT = ROOT / "results" / "exp04_revision3"
Z95 = norm.ppf(0.975)
SAMPLES = (("primary", None), ("primary", 0.30), ("expanded", None), ("expanded", 0.30))


def tag(pop, min_acc):
    return pop + ("_S2" if min_acc else "")


def row(section, analysis, sample, term, est, se, extra=None, inference="jackknife"):
    return {"section": section, "analysis": analysis, "sample": sample, "term": term,
            "estimate": est, "se": se, "inference": inference,
            "ci95_low": est - Z95 * se, "ci95_high": est + Z95 * se,
            "p": 2 * norm.sf(abs(est / se)) if se > 0 else np.nan, **(extra or {})}


def jk_fit(X, y, d):
    """OLS with delete-one-root jackknife SEs. Deleting a root can empty an
    accuracy cell; the pseudo-inverse then sets that cell's coefficient to zero,
    which leaves every other coefficient unchanged."""
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    try:
        return b, jackknife_roots(X, y, d["rid"], d["i"], d["j"])
    except np.linalg.LinAlgError:
        rid, i, j = d["rid"], d["i"], d["j"]
        XtX, Xty = X.T @ X, X.T @ y
        B = []
        for g in range(rid.max() + 1):
            m = (rid[i] == g) | (rid[j] == g)
            B.append(np.linalg.pinv(XtX - X[m].T @ X[m]) @ (Xty - X[m].T @ y[m]))
        B = np.array(B)
        G = len(B)
        return b, np.sqrt((G - 1) / G * ((B - B.mean(0)) ** 2).sum(0))


def acc_cells(acc, i, j, nbins):
    """Dummies for unordered pairs of accuracy bins (quantile bins of this sample)."""
    edges = np.quantile(acc, np.linspace(0, 1, nbins + 1)[1:-1])
    b = np.digitize(acc, edges)
    lo, hi = np.minimum(b[i], b[j]), np.maximum(b[i], b[j])
    cell = pd.factorize(lo * nbins + hi)[0]
    D = np.zeros((len(i), cell.max() + 1))
    D[np.arange(len(i)), cell] = 1.0
    return D[:, 1:]                                  # first cell is the reference


# ------------------------------------------------------------------ R7
def r7():
    rows = []
    for pop, m in SAMPLES:
        d, t = prepared(pop, min_acc=m), tag(pop, m)
        X, y, names, i, j, acc = d["X"], d["y"], d["names"], d["i"], d["j"], d["acc"]
        base = [k for k, n in enumerate(names) if not n.startswith("acc")]
        s, a = acc[i] + acc[j], np.abs(acc[i] - acc[j])
        specs = {
            "pre-specified (linear sum and difference)": X,
            "no accuracy terms (total association)": X[:, base],
            "quadratic accuracy surface": np.column_stack([X, s ** 2, a ** 2, s * a]),
            "accuracy cells: deciles (55 cells)": np.column_stack(
                [X[:, base], acc_cells(acc, i, j, 10)]),
            "accuracy cells: 20 bins (210 cells)": np.column_stack(
                [X[:, base], acc_cells(acc, i, j, 20)]),
        }
        for label, Z in specs.items():
            b, se = jk_fit(Z, y, d)
            for term in ("same_root", "gap0"):
                k = names.index(term)
                rows.append(row("R7", label, t, term, b[k], se[k],
                                {"pairs": len(y), "models": len(d["pop"])}))
        close = a <= 0.02
        Z = np.column_stack([X[:, base], acc_cells(acc, i, j, 10)])[close]
        keep = np.abs(Z).sum(0) > 0
        b, se = jk_fit(Z[:, keep], y[close], {**d, "i": i[close], "j": j[close]})
        for term in ("same_root", "gap0"):
            k = names.index(term)
            rows.append(row("R7", "accuracy-matched pairs (|diff| <= 0.02) + decile cells",
                            t, term, b[k], se[k],
                            {"pairs": int(close.sum()),
                             "same_root_pairs": int((close & (d["rid"][i] == d["rid"][j])).sum())}))
        print(f"R7 {t} done", flush=True)
    return pd.DataFrame(rows), {}


# ------------------------------------------------------------------ R8
def r8():
    from run_exp04_revision2 import chain, graph
    hub, node, parent, multi = graph()
    d = prepared("primary")
    pop, i, j, y, X, names, rid = d["pop"], d["i"], d["j"], d["y"], d["X"], d["names"], d["rid"]
    ch = [chain(m, node, parent, multi, hub)[0] for m in pop.model]
    sr = rid[i] == rid[j]
    dist = np.full(len(i), -1)
    rel = np.full(len(i), "", dtype=object)
    for k in np.flatnonzero(sr):
        a, bb = ch[i[k]], ch[j[k]]
        c = next(n for n in a if n in bb)
        dist[k] = a.index(c) + bb.index(c)
        rel[k] = ("same repository" if dist[k] == 0 else "ancestor-descendant"
                  if a[0] in bb or bb[0] in a else "siblings"
                  if len(a) > 1 and len(bb) > 1 and a[1] == bb[1] else "more distant")
    rows, info = [], {}
    # (a) within root: same-root pairs only, root fixed effects
    s = sr & (dist > 0)
    roots = np.unique(rid[i][s])
    ctrl = [k for k, n in enumerate(names) if n not in ("const", "same_root")]
    F = (rid[i][s][:, None] == roots[None, 1:]).astype(float)        # root FE, ref = first
    for label, cols, cn in (
            ("within root: tree distance (ref. 3+)",
             [(dist[s] == 1), (dist[s] == 2)], ["distance 1", "distance 2"]),
            ("within root: relation (ref. more distant)",
             [(rel[s] == "ancestor-descendant"), (rel[s] == "siblings")],
             ["ancestor-descendant", "siblings"])):
        Z = np.column_stack([np.ones(s.sum())] + [c.astype(float) for c in cols]
                            + [X[s][:, ctrl], F])
        ys = y[s]
        b = np.linalg.lstsq(Z, ys, rcond=None)[0]
        # delete-one-root jackknife over the roots that contribute same-root pairs
        g_of = rid[i][s]
        bs = []
        for g in roots:
            keep = g_of != g
            Zk = Z[keep][:, np.abs(Z[keep]).sum(0) > 0]
            idx = np.flatnonzero(np.abs(Z[keep]).sum(0) > 0)
            bk = np.linalg.lstsq(Zk, ys[keep], rcond=None)[0]
            full = np.full(Z.shape[1], np.nan); full[idx] = bk
            bs.append(full[1:3])
        bs = np.array(bs)
        G = len(roots)
        se = np.sqrt((G - 1) / G * np.nansum((bs - np.nanmean(bs, 0)) ** 2, 0))
        for k, n in enumerate(cn):
            rows.append(row("R8", label, "primary", n, b[1 + k], se[k],
                            {"pairs": int(cols[k].sum()), "same_root_pairs": int(s.sum()),
                             "roots": int(G)}))
    # does composition matter? share of each distance class from small roots
    size = pd.Series(rid).value_counts()
    small = size.reindex(rid[i]).to_numpy() < 8
    info["distance_by_root_size"] = {
        f"distance {k}": {"pairs": int(((dist == k) if k < 3 else (dist >= 3)).sum()),
                          "from_roots_lt8_models": int((((dist == k) if k < 3 else (dist >= 3)) & small).sum())}
        for k in (1, 2, 3)}
    # (b) per-root coefficients, pooled with every root counted once
    multi_roots = [g for g in np.unique(rid) if ((rid[i] == g) & (rid[j] == g)).sum() > 0]
    cols = [((rid[i] == g) & (rid[j] == g)).astype(float) for g in multi_roots]
    Z = np.column_stack([X[:, :1]] + cols + [X[:, 2:]])
    b, se = ols_twoway(Z, y, i, j, len(pop))
    est_all, s2_all = b[1:1 + len(cols)], se[1:1 + len(cols)] ** 2
    npairs = np.array([int(c.sum()) for c in cols])
    # A root with one same-root pair fits that pair exactly, so its dyadic SE is
    # ~0; random-effects weights are meaningful only for roots with enough pairs.
    ok = (npairs >= 10) & np.isfinite(s2_all) & (s2_all > 0)   # dyadic variance can clip to 0
    est, s2 = est_all[ok], s2_all[ok]
    w = 1 / s2
    fe = (w * est).sum() / w.sum()
    Q = (w * (est - fe) ** 2).sum()
    k = len(est)
    tau2 = max(0.0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    wr = 1 / (s2 + tau2)
    re = (wr * est).sum() / wr.sum()
    re_se = np.sqrt(1 / wr.sum())
    rows.append(row("R8", "per-root coefficients, random-effects pooled (roots with >= 10 "
                    "same-root pairs)", "primary", "same_root", re, re_se,
                    {"roots": int(k), "tau": float(np.sqrt(tau2)),
                     "I2": float(max(0, (Q - (k - 1)) / Q)) if Q > 0 else 0.0},
                    inference="random-effects (DerSimonian-Laird), model-level dyadic SEs"))
    n_all = len(est_all)
    rows.append(row("R8", "per-root coefficients, unweighted mean over all roots", "primary",
                    "same_root", est_all.mean(), est_all.std(ddof=1) / np.sqrt(n_all),
                    {"roots": int(n_all)}, inference="SE of the mean across roots"))
    big = npairs >= 10
    info["per_root_estimates"] = {
        "roots": int(n_all), "median_all": float(np.median(est_all)),
        "share_positive_all": float((est_all > 0).mean()),
        "roots_ge10_pairs": int(big.sum()), "median_ge10": float(np.median(est_all[big])),
        "mean_lt10": float(est_all[~big].mean()), "roots_lt10": int((~big).sum())}
    return pd.DataFrame(rows), info


# ------------------------------------------------------------------ R9
def itemfe_fit(pred, gold, rid, mon, acc):
    """Exact OLS of 1[same wrong option] on pair covariates with item fixed effects,
    over all (pair, item) cells where both models are wrong."""
    N = len(pred)
    Wb = pred != gold[None, :]
    W = Wb.astype(np.float64)
    gap = np.abs(mon[:, None] - mon[None, :])
    gb = np.digitize(gap, GAP_BINS[1:])
    mats = [(rid[:, None] == rid[None, :]).astype(np.float64)]
    mats += [(gb == k).astype(np.float64) for k in range(4)]
    mats += [acc[:, None] + acc[None, :], np.abs(acc[:, None] - acc[None, :])]
    for M in mats:
        np.fill_diagonal(M, 0.0)
    C = len(mats)
    nk = Wb.sum(0).astype(np.float64)
    npair_k = nk * (nk - 1) / 2                         # jointly wrong pairs per item
    S = np.empty((C, pred.shape[1]))
    for c, M in enumerate(mats):
        S[c] = 0.5 * (W * (M @ W)).sum(0)               # sum of x_p over pairs in item k
    Yk = np.zeros(pred.shape[1])
    for o in range(4):
        co = ((pred == o) & Wb).sum(0).astype(np.float64)
        Yk += co * (co - 1) / 2
    both = W @ W.T
    same = np.zeros_like(both)
    for o in range(4):
        B = ((pred == o) & Wb).astype(np.float64)
        same += B @ B.T
    iu, ju = np.triu_indices(N, 1)
    Xp = np.column_stack([M[iu, ju] for M in mats])
    npp, sp = both[iu, ju], same[iu, ju]
    ok = npair_k > 0
    XtX = (Xp * npp[:, None]).T @ Xp - (S[:, ok] / npair_k[ok]) @ S[:, ok].T
    Xty = Xp.T @ sp - S[:, ok] @ (Yk[ok] / npair_k[ok])
    return np.linalg.solve(XtX, Xty)


def r9():
    rows, info = [], {}
    names = ["same_root", "gap0", "gap1_2", "gap3_5", "gap6_11", "acc_sum", "acc_absdiff"]
    for pop in ("primary", "expanded"):
        d = prepared(pop)
        pred, gold, rid, acc = d["pred"], d["gold"], d["rid"], d["acc"]
        mon = month_index(d["pop"].created_month)
        t0 = time.time()
        b = itemfe_fit(pred, gold, rid, mon, acc)
        G = rid.max() + 1
        bs = np.empty((G, len(b)))
        for g in range(G):
            k = rid != g
            bs[g] = itemfe_fit(pred[k], gold, rid[k], mon[k], acc[k])
            if g % 50 == 0:
                print(f"R9 {pop}: root {g}/{G} ({time.time() - t0:.0f}s)", flush=True)
        se = np.sqrt((G - 1) / G * ((bs - bs.mean(0)) ** 2).sum(0))
        for term in ("same_root", "gap0"):
            k = names.index(term)
            rows.append(row("R9", "pair x item model with item fixed effects", pop, term,
                            b[k], se[k], {"models": len(pred)}))
        # the same weighting without item fixed effects, for comparison
        n_both = d["nb"]
        Xw = d["X"] * np.sqrt(n_both)[:, None]
        yw = d["y"] * np.sqrt(n_both)
        bw = np.linalg.lstsq(Xw, yw, rcond=None)[0]
        sew = jackknife_roots(Xw, yw, rid, d["i"], d["j"])
        for term in ("same_root", "gap0"):
            k = d["names"].index(term)
            rows.append(row("R9", "pair x item model without item fixed effects (WLS)", pop,
                            term, bw[k], sew[k]))
        info[f"{pop}_seconds"] = round(time.time() - t0)
    return pd.DataFrame(rows), info


# ------------------------------------------------------------------ R10
def r10(B=999, seed=20261010):
    rows, info = [], {}
    for pop in ("primary", "expanded"):
        d = prepared(pop)
        pop_df, pred, rid, acc = d["pop"], d["pred"], d["rid"], d["acc"]
        N = len(pop_df)
        mon = month_index(pop_df.created_month)
        Y = np.full((N, N), np.nan)
        Y[d["i"], d["j"]] = d["y"]; Y[d["j"], d["i"]] = d["y"]
        names = d["names"]
        kk = [names.index("same_root"), names.index("gap0")]
        b0 = np.linalg.lstsq(d["X"], d["y"], rcond=None)[0][kk]
        rng = np.random.default_rng(seed)
        members = [np.flatnonzero(rid == g) for g in range(rid.max() + 1)]
        # cluster bootstrap over roots
        boot = []
        for _ in range(B):
            draw = rng.integers(0, len(members), len(members))
            idx = np.concatenate([members[g] for g in draw])
            ii, jj = np.triu_indices(len(idx), 1)
            a, c = idx[ii], idx[jj]
            ok = a != c
            a, c = a[ok], c[ok]
            yy = Y[a, c]
            fin = np.isfinite(yy)
            X, _ = design(a[fin], c[fin], rid, mon, acc)
            boot.append(np.linalg.lstsq(X, yy[fin], rcond=None)[0][kk])
        boot = np.array(boot)
        # permutation of root labels within upload quarter
        q = (mon // 3)
        perm = []
        for _ in range(B):
            r2 = rid.copy()
            for qq in np.unique(q):
                m = np.flatnonzero(q == qq)
                r2[m] = rng.permutation(rid[m])
            X, _ = design(d["i"], d["j"], r2, mon, acc)
            perm.append(np.linalg.lstsq(X, d["y"], rcond=None)[0][kk[0]])
        perm = np.array(perm)
        for k, term in enumerate(("same_root", "gap0")):
            lo, hi = np.percentile(boot[:, k], [2.5, 97.5])
            rows.append({"section": "R10", "analysis": "root cluster bootstrap (percentile)",
                         "sample": pop, "term": term, "estimate": b0[k],
                         "se": boot[:, k].std(ddof=1), "inference": f"bootstrap, B={B}",
                         "ci95_low": lo, "ci95_high": hi, "p": np.nan})
        rows.append({"section": "R10",
                     "analysis": "root-label permutation within upload quarter",
                     "sample": pop, "term": "same_root", "estimate": b0[0],
                     "se": perm.std(ddof=1), "inference": f"permutation, B={B}",
                     "ci95_low": np.percentile(perm, 2.5), "ci95_high": np.percentile(perm, 97.5),
                     "p": (1 + (np.abs(perm) >= abs(b0[0])).sum()) / (B + 1),
                     "perm_max_abs": float(np.abs(perm).max())})
        sr = rid[d["i"]] == rid[d["j"]]
        top2 = pd.Series(rid[d["i"]][sr]).value_counts().head(2).sum()
        info[pop] = {"roots": int(rid.max() + 1),
                     "roots_with_2plus_models": int((np.bincount(rid) >= 2).sum()),
                     "same_root_pairs": int(sr.sum()), "top2_root_same_root_pairs": int(top2)}
        print(f"R10 {pop} done", flush=True)
    return pd.DataFrame(rows), info


# ------------------------------------------------------------------ R11
def theta_for(acc, rng, K=20000):
    """Ability giving expected accuracy acc under logistic(theta - d), d ~ N(0,1)."""
    d = rng.normal(0, 1, K)
    grid = np.linspace(-6, 6, 1201)
    m = (1 / (1 + np.exp(-(grid[:, None] - d[None, :])))).mean(1)
    return np.interp(np.clip(acc, m[0], m[-1]), m, grid)


def simulate(root_id, month, theta, truth, K, rng, lam_g_vec=None):
    N = len(root_id)
    d = rng.normal(0.0, 1.0, K)
    correct = rng.random((N, K)) < 1 / (1 + np.exp(-(theta[:, None] - d[None, :])))
    R = rng.integers(1, 4, (root_id.max() + 1, K))
    E = np.empty((month.max() + 1, K), dtype=np.int64)
    E[0] = rng.integers(1, 4, K)
    for m in range(1, month.max() + 1):
        E[m] = np.where(rng.random(K) < truth.rho, E[m - 1], rng.integers(1, 4, K))
    Gk = rng.integers(1, 4, K)
    lg = np.full(N, truth.lam_G) if lam_g_vec is None else lam_g_vec
    u = rng.random((N, K))
    c1 = truth.lam_L
    c2 = c1 + truth.lam_E
    c3 = c2 + lg[:, None]
    wrong = np.where(u < c1, R[root_id], np.where(u < c2, E[month],
                     np.where(u < c3, Gk[None, :], rng.integers(1, 4, (N, K)))))
    return np.where(correct, 0, wrong)


def r11(reps=200, K=1500, seed=11):
    d = prepared("primary")
    pop, acc_real = d["pop"], d["acc"]
    rid = pd.factorize(pop.root)[0]
    mon = month_index(pop.created_month)
    rng = np.random.default_rng(seed)
    theta = theta_for(acc_real, rng)
    scen = {"null": (Truth(), None)}
    for lam in (0.03, 0.05, 0.10):
        scen[f"release-time {lam:.2f}"] = (Truth(lam_E=lam), None)
        scen[f"lineage {lam:.2f}"] = (Truth(lam_L=lam), None)
    a = np.clip(acc_real, 0, 1)
    scen["ability-dependent attractor (no lineage or release-time effect)"] = (
        Truth(lam_G=0.0), 0.05 + 0.5 * a ** 2)
    rows = []
    for name, (truth, lg) in scen.items():
        rej = {}
        est = {}
        for r in range(reps):
            ch = simulate(rid, mon, theta, truth, K, rng, lg)
            acc = (ch == 0).mean(1)
            i, j, y = pair_agreement(ch)
            X, names = design(i, j, rid, mon, acc)
            for spec in ("pre-specified", "decile cells"):
                Z = X if spec == "pre-specified" else np.column_stack(
                    [X[:, [k for k, n in enumerate(names) if not n.startswith("acc")]],
                     acc_cells(acc, i, j, 10)])
                b, se = ols_twoway(Z, y, i, j, len(pop))
                for term in ("same_root", "gap0", "gap1_2"):
                    k = names.index(term)
                    rej.setdefault((spec, term), []).append(abs(b[k] / se[k]) > 1.96)
                    est.setdefault((spec, term), []).append(b[k])
        for (spec, term), v in rej.items():
            n, x = len(v), int(np.sum(v))
            p = x / n
            z = Z95
            den = 1 + z * z / n
            mid = (p + z * z / (2 * n)) / den
            half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
            e = np.array(est[(spec, term)])
            rows.append({"section": "R11", "scenario": name, "spec": spec, "term": term,
                         "reps": n, "rejections": x, "rate": p, "ci_low": mid - half,
                         "ci_high": mid + half, "mean_estimate": e.mean(),
                         "mcse_estimate": e.std(ddof=1) / np.sqrt(n)})
        print(f"R11 {name} done", flush=True)
    info = {"theta_from_real_accuracy": True, "K": K, "reps": reps,
            "corr_real_vs_sim_accuracy": float(np.corrcoef(acc_real, acc)[0, 1])}
    return pd.DataFrame(rows), info


# ------------------------------------------------------------------ R12
def redux_flags(items):
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    from datasets import load_dataset
    red = pd.read_parquet(ROOT / "datasets/mmlu_redux/mmlu_redux_2.parquet")
    norm_q = lambda s: " ".join(str(s).split())  # noqa: E731
    flag = pd.Series("not in Redux", index=items)
    matched = 0
    for subj, g in red.groupby("subject"):
        test = load_dataset("cais/mmlu", subj, split="test").to_pandas()
        pos = {}
        for k, q in enumerate(test.question):
            pos.setdefault((norm_q(q), tuple(map(norm_q, test.choices[k]))), []).append(k)
        for q, ch, et in zip(g.question, g.choices, g.error_type):
            ks = pos.get((norm_q(q), tuple(map(norm_q, ch))))
            if ks:
                for k in ks:
                    key = f"{subj}:{k}"
                    if key in flag.index:
                        flag[key] = et
                        matched += 1
    return flag, matched


def r12():
    rows, info = [], {}
    for pop, m in SAMPLES:
        d, t = prepared(pop, min_acc=m), tag(pop, m)
        pop_df = d["pop"]
        z = np.load(A.answer_file(pop_df.model.iloc[0]))
        items = z["item"]
        if not info:
            flag, matched = redux_flags(items)
            info["items_matched"] = int(matched)
            info["flag_counts"] = flag.value_counts().to_dict()
        pred, gold, rid = d["pred"], d["gold"], d["rid"]
        mon = month_index(pop_df.created_month)
        f = flag.reindex(items).to_numpy()
        masks = {"all 14,042 items (pre-specified)": np.ones(len(items), bool),
                 "MMLU-Redux items only (5,700)": f != "not in Redux",
                 "MMLU-Redux items annotated ok only": f == "ok"}
        masks["items flagged as erroneous in MMLU-Redux removed"] = ~np.isin(
            f, ["bad_question_clarity", "wrong_groundtruth", "multiple_correct_answers",
                "no_correct_answer", "expert", "bad_options_clarity"])
        for label, mk in masks.items():
            acc = (pred[:, mk] == gold[None, mk]).mean(1)
            i, j, y, _ = A.pair_outcomes(pred[:, mk], gold[mk])
            X, names = design(i, j, rid, mon, acc)
            b, se = jk_fit(X, y, {"rid": rid, "i": i, "j": j})
            for term in ("same_root", "gap0"):
                k = names.index(term)
                rows.append(row("R12", label, t, term, b[k], se[k],
                                {"items": int(mk.sum()), "pairs": len(y)}))
        print(f"R12 {t} done", flush=True)
    return pd.DataFrame(rows), info


SECTIONS = {"R7": r7, "R8": r8, "R9": r9, "R10": r10, "R11": r11, "R12": r12}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=list(SECTIONS))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for k in a.only:
        res, info = SECTIONS[k]()
        res.to_csv(OUT / f"{k}.csv", index=False)
        (OUT / f"info_{k}.json").write_text(json.dumps(info, indent=1, default=str))
        pd.set_option("display.width", 250)
        cols = [c for c in ("analysis", "scenario", "spec", "sample", "term", "estimate",
                            "ci95_low", "ci95_high", "rate", "p") if c in res]
        print(res[cols].round(4).to_string(index=False))
        print(json.dumps(info, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
