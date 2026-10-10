"""Pre-data precision / separation gate for the pair-level lineage-vs-era design.

Uses only the roster (lineage root, creation month); no real outcomes.

Generative model (item level, K items, 4 options, gold = 0):
    correct_ik ~ Bernoulli(logistic(theta_i - d_k))
    if wrong, model i picks
        root attractor  R[root(i), k]        with prob lam_L
        era attractor   E[month(i), k]       with prob lam_E   (AR(1) over months:
                                                                 kept with prob rho)
        global attractor G[k]                with prob lam_G
        uniform wrong option                  otherwise

Pair outcome: agree_ij = P(same wrong option | both wrong).
Estimator: OLS of agree_ij on [1, same_root, time-gap bins, accuracy controls]
with two-way (model i, model j) cluster-robust standard errors.

The gate asks, on the real design:
  * separation: under era-only truth the lineage coefficient stays ~0 and vice
    versa (the confound between lineage and release time is handled);
  * calibration: under the null, nominal 5% tests reject ~5%;
  * precision: SE of each coefficient relative to a minimum effect of interest.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

GAP_BINS = [0, 1, 3, 6, 12, 10_000]           # months: 0, 1-2, 3-5, 6-11, 12+
GAP_LABELS = ["gap0", "gap1_2", "gap3_5", "gap6_11"]   # 12+ is the reference


@dataclass
class Truth:
    lam_L: float = 0.0
    lam_E: float = 0.0
    lam_G: float = 0.15
    rho: float = 0.8


def month_index(months: pd.Series) -> np.ndarray:
    p = pd.PeriodIndex(months, freq="M")
    return (p.year * 12 + p.month - (p.year.min() * 12 + 1)).to_numpy()


def simulate_choices(root_id: np.ndarray, month: np.ndarray, truth: Truth,
                     K: int, rng: np.random.Generator) -> np.ndarray:
    """N x K matrix of chosen options (0 = correct, 1..3 = wrong)."""
    N = len(root_id)
    theta = rng.normal(0.3, 1.0, N)
    d = rng.normal(0.0, 1.0, K)
    correct = rng.random((N, K)) < 1 / (1 + np.exp(-(theta[:, None] - d[None, :])))
    R = rng.integers(1, 4, (root_id.max() + 1, K))
    n_m = month.max() + 1
    E = np.empty((n_m, K), dtype=np.int64)
    E[0] = rng.integers(1, 4, K)
    for m in range(1, n_m):
        keep = rng.random(K) < truth.rho
        E[m] = np.where(keep, E[m - 1], rng.integers(1, 4, K))
    G = rng.integers(1, 4, K)
    u = rng.random((N, K))
    c1, c2, c3 = truth.lam_L, truth.lam_L + truth.lam_E, \
        truth.lam_L + truth.lam_E + truth.lam_G
    wrong = np.where(u < c1, R[root_id],
             np.where(u < c2, E[month],
              np.where(u < c3, G[None, :], rng.integers(1, 4, (N, K)))))
    return np.where(correct, 0, wrong)


def pair_agreement(ch: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Upper-triangle pair indices and agree_ij = same wrong / both wrong."""
    W = (ch > 0).astype(np.float32)
    both = W @ W.T
    same = sum(((ch == o).astype(np.float32) @ (ch == o).astype(np.float32).T)
               for o in (1, 2, 3))
    i, j = np.triu_indices(len(ch), 1)
    ok = both[i, j] > 0
    return i[ok], j[ok], (same[i, j] / np.maximum(both[i, j], 1))[ok]


def design(i: np.ndarray, j: np.ndarray, root_id: np.ndarray, month: np.ndarray,
           acc: np.ndarray) -> tuple[np.ndarray, list[str]]:
    gap = np.abs(month[i] - month[j])
    b = np.digitize(gap, GAP_BINS[1:])            # 0..4, 4 = 12+ (reference)
    cols = [np.ones(len(i)), (root_id[i] == root_id[j]).astype(float)]
    cols += [(b == k).astype(float) for k in range(4)]
    cols += [acc[i] + acc[j], np.abs(acc[i] - acc[j])]
    return np.column_stack(cols), ["const", "same_root", *GAP_LABELS,
                                   "acc_sum", "acc_absdiff"]


def ols_twoway(X: np.ndarray, y: np.ndarray, i: np.ndarray, j: np.ndarray,
               N: int) -> tuple[np.ndarray, np.ndarray]:
    """OLS with dyadic (Cameron–Gelbach–Miller / Aronow) clustering.

    Pair p has endpoints i[p], j[p] (models, or lineage roots for root-level
    clustering). The meat is the sum of e_p e_q x_p x_q' over all pairs p, q
    that share at least one endpoint cluster, each (p, q) counted once.

    S'S, with S_g the sum of the scores of pairs touching cluster g, counts a
    combination (p, q) once per cluster the two pairs have in common. Pairs in
    the same cell {a, b} with a != b have two clusters in common, so the cell
    sums T_ab are subtracted once (the CGM form V_a + V_b - V_ab). A pair whose
    two endpoints coincide (a same-root pair under root-level clustering) is
    added to its cluster once. For model-level clustering every cell holds a
    single pair, so this reduces to subtracting each pair's own term.
    """
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    s = X * e[:, None]
    two = i != j
    S = np.zeros((N, X.shape[1]))
    np.add.at(S, i, s)
    np.add.at(S, j[two], s[two])
    lo, hi = np.minimum(i, j)[two], np.maximum(i, j)[two]
    cell = np.unique(lo.astype(np.int64) * N + hi, return_inverse=True)[1]
    T = np.zeros((cell.max() + 1 if len(cell) else 0, X.shape[1]))
    np.add.at(T, cell, s[two])
    meat = S.T @ S - T.T @ T
    # Correction 2026-10-09: before this date every pair was added to both
    # endpoint clusters and only its own term was subtracted. That is exact for
    # model-level clustering (all pre-registered results), but under root-level
    # clustering it counted same-root pairs three times with themselves and
    # pairs spanning the same two roots twice with each other (conservative).
    V = XtX_inv @ meat @ XtX_inv
    return beta, np.sqrt(np.clip(np.diag(V), 0, None))


def root_bootstrap_pairs(members: list[np.ndarray],
                         draw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Model pairs of one root-cluster bootstrap replicate (vertex scheme).

    members[g] lists the models of root g; draw lists the roots drawn with
    replacement. The drawn copies are stacked and every pair of positions is
    kept unless both positions are the same model. Hence a pair of models
    from a root drawn k times enters k^2 times and stays a same-root pair
    (copies of one root are not relabelled as different roots), and a pair
    spanning roots drawn k and m times enters k*m times: the "pigeonhole"
    bootstrap for exchangeable (dyadic) arrays applied to root clusters.
    Returns the original model indices (a, c) of the kept pairs.
    """
    idx = np.concatenate([members[g] for g in draw])
    ii, jj = np.triu_indices(len(idx), 1)
    a, c = idx[ii], idx[jj]
    ok = a != c
    return a[ok], c[ok]


def run(roster: pd.DataFrame, truth: Truth, K: int = 1500, reps: int = 20,
        seed: int = 0) -> pd.DataFrame:
    root_id = pd.factorize(roster["root"])[0]
    month = month_index(roster["created_month"])
    rng = np.random.default_rng(seed)
    out = []
    for r in range(reps):
        ch = simulate_choices(root_id, month, truth, K, rng)
        acc = (ch == 0).mean(1)
        i, j, y = pair_agreement(ch)
        X, names = design(i, j, root_id, month, acc)
        beta, se = ols_twoway(X, y, i, j, len(roster))
        out.append({**{f"b_{n}": b for n, b in zip(names, beta)},
                    **{f"se_{n}": s for n, s in zip(names, se)}, "rep": r})
    return pd.DataFrame(out)


def summarize(res: pd.DataFrame, terms=("same_root", "gap0", "gap1_2")) -> dict:
    out = {}
    for t in terms:
        b, s = res[f"b_{t}"], res[f"se_{t}"]
        out[f"{t}_mean"] = b.mean()
        out[f"{t}_sd"] = b.std(ddof=1)
        out[f"{t}_se_mean"] = s.mean()
        out[f"{t}_reject5"] = float((np.abs(b / s) > 1.96).mean())
    return out
