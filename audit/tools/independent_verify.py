#!/usr/bin/env python3
"""Independent re-implementation of the paper's primary estimand (audit Phase 3).

Deliberately imports NOTHING from lineage_era / scripts. Built from the manuscript:

  a_ij = sum_k 1[c_ik = c_jk != t_k] / sum_k 1[c_ik != t_k] 1[c_jk != t_k]        (Eq. 1)
  a_ij = b0 + bL s_ij + sum_h bE_h 1[|m_i-m_j| in h] + g1 (acc_i+acc_j)
         + g2 |acc_i-acc_j| + e_ij ,  h in {0, 1-2, 3-5, 6-11}, ref 12+              (Eq. 2)
  OLS; model-level dyadic SEs (Eq. 3); delete-one-root jackknife.

Inputs read from disk: validated answer files datasets/ollb/v1/*.npz, frozen sample
CSV (model, root, created_month), validation manifest. Everything else is recomputed.
Outputs: audit/outputs/independent_results.json (+ printed comparison).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTD = ROOT / "audit" / "outputs"
OUTD.mkdir(parents=True, exist_ok=True)
Z = 1.959963984540054


def load(sample: str, min_acc=None):
    s = pd.read_csv(ROOT / f"datasets/ollb/frozen_full/{sample}_sample_cap40.csv")
    man = pd.read_csv(ROOT / "results/exp04_validation/per_model.csv")
    ok = set(man.model[man.category == "validated"])
    s = s[s.model.isin(ok)].reset_index(drop=True)
    preds, golds, items = [], [], []
    for m in s.model:
        z = np.load(ROOT / "datasets/ollb/v1" / (m.replace("/", "__") + ".npz"))
        preds.append(z["pred"].astype(np.int8)); golds.append(z["gold"].astype(np.int8)); items.append(z["item"])
    # independent file-level validation
    for k in range(1, len(preds)):
        assert len(preds[k]) == 14042 and (items[k] == items[0]).all() and (golds[k] == golds[0]).all()
        assert 0 <= preds[k].min() and preds[k].max() <= 3
    pred, gold = np.stack(preds), golds[0]
    acc = (pred == gold[None, :]).mean(1)
    keep = np.ones(len(s), bool) if min_acc is None else acc >= min_acc
    return s[keep].reset_index(drop=True), pred[keep], gold, acc[keep]


def pair_outcomes(pred, gold):
    """a_ij by direct comparison, one row at a time (no matrix products)."""
    n, K = pred.shape
    wrong = pred != gold[None, :]
    I, J, A, B = [], [], [], []
    for i in range(n - 1):
        w = wrong[i + 1:] & wrong[i]                      # both wrong
        sm = w & (pred[i + 1:] == pred[i])                # both wrong, same option
        both = w.sum(1); same = sm.sum(1)
        I.append(np.full(n - 1 - i, i)); J.append(np.arange(i + 1, n)); B.append(both); A.append(same)
    I, J, same, both = map(np.concatenate, (I, J, A, B))
    keep = both > 0
    return I[keep], J[keep], same[keep] / both[keep], both[keep], int((~keep).sum())


def design(s, acc, I, J):
    p = pd.PeriodIndex(s.created_month, freq="M")
    m = (p.year * 12 + p.month).to_numpy()
    gap = np.abs(m[I] - m[J])
    root = pd.factorize(s.root)[0]
    cols = [np.ones(len(I)), (root[I] == root[J]).astype(float),
            (gap == 0).astype(float), ((gap >= 1) & (gap <= 2)).astype(float),
            ((gap >= 3) & (gap <= 5)).astype(float), ((gap >= 6) & (gap <= 11)).astype(float),
            acc[I] + acc[J], np.abs(acc[I] - acc[J])]
    return np.column_stack(cols), root


NAMES = ["const", "same_root", "gap0", "gap1_2", "gap3_5", "gap6_11", "acc_sum", "acc_absdiff"]


def ols(X, y, w=None):
    if w is None:
        return np.linalg.solve(X.T @ X, X.T @ y)
    Xw = X * w[:, None]
    return np.linalg.solve(X.T @ Xw, Xw.T @ y)


def dyadic_se(X, y, b, I, J, n):
    """Eq. 3: sum over pairs p,q sharing >=1 model (p=q included), each (p,q) once."""
    e = y - X @ b
    s = X * e[:, None]                                   # pair scores
    S = np.zeros((n, X.shape[1]))
    np.add.at(S, I, s); np.add.at(S, J, s)               # sum of scores over pairs touching model i
    # sum_i S_i S_i' counts each (p,q) with exactly one shared model once and each p=q twice
    meat = S.T @ S - s.T @ s
    XtXi = np.linalg.inv(X.T @ X)
    return np.sqrt(np.diag(XtXi @ meat @ XtXi))


def dyadic_se_bruteforce(X, y, b, I, J):
    e = y - X @ b; s = X * e[:, None]; P = len(y)
    meat = np.zeros((X.shape[1],) * 2)
    for p in range(P):
        share = (I == I[p]) | (I == J[p]) | (J == I[p]) | (J == J[p])
        meat += np.outer(s[p], s[share].sum(0))
    XtXi = np.linalg.inv(X.T @ X)
    return np.sqrt(np.diag(XtXi @ meat @ XtXi))


def jackknife(X, y, root, I, J, groups=None):
    """Delete-one-root jackknife: refit OLS without every pair that touches the root."""
    rI, rJ = root[I], root[J]
    G = np.unique(root) if groups is None else np.asarray(groups)
    B = []
    XtX, Xty = X.T @ X, X.T @ y
    for g in G:
        m = (rI == g) | (rJ == g)
        Xg = X[m]
        B.append(np.linalg.solve(XtX - Xg.T @ Xg, Xty - Xg.T @ y[m]))
    B = np.array(B); n = len(G)
    return np.sqrt((n - 1) / n * ((B - B.mean(0)) ** 2).sum(0)), B


def run(sample, min_acc=None, label=None):
    t0 = time.time()
    s, pred, gold, acc = load(sample, min_acc)
    I, J, y, both, dropped = pair_outcomes(pred, gold)
    X, root = design(s, acc, I, J)
    b = ols(X, y)
    n = len(s)
    se_m = dyadic_se(X, y, b, I, J, n)
    se_jk, B = jackknife(X, y, root, I, J)
    k = NAMES.index("same_root"); g0 = NAMES.index("gap0")
    sr = X[:, k] == 1
    out = {"sample": label or sample, "models": int(n), "roots": int(root.max() + 1),
           "pairs": int(len(y)), "pairs_dropped_no_joint_errors": dropped,
           "same_root_pairs": int(sr.sum()), "mean_agreement": float(y.mean()),
           "mean_agreement_same_root": float(y[sr].mean()), "mean_agreement_diff_root": float(y[~sr].mean()),
           "joint_wrong_min": int(both.min()), "joint_wrong_median": float(np.median(both)),
           "joint_wrong_max": int(both.max()),
           "coef": {nm: float(v) for nm, v in zip(NAMES, b)},
           "se_model_dyadic": {nm: float(v) for nm, v in zip(NAMES, se_m)},
           "se_jackknife": {nm: float(v) for nm, v in zip(NAMES, se_jk)},
           "shared_root_ci_jackknife": [float(b[k] - Z * se_jk[k]), float(b[k] + Z * se_jk[k])],
           "shared_root_ci_model": [float(b[k] - Z * se_m[k]), float(b[k] + Z * se_m[k])],
           "same_month_ci_jackknife": [float(b[g0] - Z * se_jk[g0]), float(b[g0] + Z * se_jk[g0])],
           "jackknife_range_shared_root": [float(B[:, k].min()), float(B[:, k].max())],
           "seconds": round(time.time() - t0, 1)}
    return out, (s, pred, gold, acc, I, J, y, both, X, root, b)


if __name__ == "__main__":
    res = {}
    for sample, ma, lab in (("primary", None, "primary"), ("expanded", None, "expanded"),
                            ("primary", 0.30, "primary_S2"), ("expanded", 0.30, "expanded_S2")):
        r, _ = run(sample, ma, lab)
        res[lab] = r
        k = r["coef"]["same_root"]
        print(f"{lab:12s} models {r['models']} pairs {r['pairs']:,} | shared-root {100*k:.3f} pts "
              f"jackknife CI [{100*r['shared_root_ci_jackknife'][0]:.2f}, {100*r['shared_root_ci_jackknife'][1]:.2f}] "
              f"model CI [{100*r['shared_root_ci_model'][0]:.2f}, {100*r['shared_root_ci_model'][1]:.2f}] "
              f"| same-month {100*r['coef']['gap0']:.3f} | {r['seconds']}s", flush=True)
    (OUTD / "independent_results.json").write_text(json.dumps(res, indent=1))
