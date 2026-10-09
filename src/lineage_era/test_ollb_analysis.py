"""Exp04: the real-data pair outcome equals the simulated one the gate used."""
import numpy as np
import pandas as pd

from lineage_era.ollb.analysis import pair_outcomes
from lineage_era.ollb.pair_gate import (Truth, design, ols_twoway,
                                        pair_agreement, simulate_choices)


def test_pair_outcomes_match_gate_definition():
    rng = np.random.default_rng(0)
    root_id = np.repeat(np.arange(10), 3)
    month = rng.integers(0, 12, 30)
    ch = simulate_choices(root_id, month, Truth(lam_L=0.1), K=400, rng=rng)
    # Gate encoding: 0 = correct, 1..3 = wrong options. Real encoding: the
    # chosen option index with a per-item gold. Map gold to option 0.
    gold = np.zeros(ch.shape[1], dtype=np.int8)
    i1, j1, y1 = pair_agreement(ch)
    i2, j2, y2, _ = pair_outcomes(ch.astype(np.int8), gold)
    assert np.array_equal(i1, i2) and np.array_equal(j1, j2)
    assert np.allclose(y1, y2)


def test_gold_not_option_zero():
    # Same answers relabelled so gold varies per item: agreement is unchanged.
    rng = np.random.default_rng(1)
    ch = simulate_choices(np.repeat(np.arange(5), 4), rng.integers(0, 6, 20),
                          Truth(), K=300, rng=rng)
    shift = rng.integers(0, 4, ch.shape[1])
    pred = ((ch + shift[None, :]) % 4).astype(np.int8)
    _, _, y_ref, _ = pair_outcomes(ch.astype(np.int8), np.zeros(300, np.int8))
    _, _, y_rel, _ = pair_outcomes(pred, (shift % 4).astype(np.int8))
    assert np.allclose(y_ref, y_rel)


def test_recovers_simulated_lineage_effect():
    rng = np.random.default_rng(2)
    root_id = np.repeat(np.arange(40), 5)
    month = rng.integers(0, 24, 200)
    ch = simulate_choices(root_id, month, Truth(lam_L=0.15), K=2000, rng=rng)
    i, j, y, _ = pair_outcomes(ch.astype(np.int8), np.zeros(2000, np.int8))
    acc = (ch == 0).mean(1)
    X, names = design(i, j, root_id, month, acc)
    beta, se = ols_twoway(X, y, i, j, 200)
    b = dict(zip(names, beta))
    assert b["same_root"] / se[names.index("same_root")] > 4
    assert abs(b["gap0"]) / se[names.index("gap0")] < 3


def test_position_tv_bounds():
    from lineage_era.ollb.analysis import position_tv
    pred = np.array([[0, 0, 0, 0], [0, 0, 0, 0], [1, 2, 3, 1]], np.int8)
    tv = position_tv(pred, np.array([0, 0]), np.array([1, 2]))
    assert tv[0] == 0.0 and tv[1] == 1.0


def test_dyadic_meat_matches_brute_force_with_shared_clusters():
    """Each pair of pairs sharing a cluster counted once, including pairs whose
    two endpoints are in the same cluster (root-level clustering)."""
    rng = np.random.default_rng(5)
    n_models, G = 12, 4
    root = rng.integers(0, G, n_models)
    i, j = np.triu_indices(n_models, 1)
    X = np.column_stack([np.ones(len(i)), rng.normal(size=len(i))])
    y = X @ np.array([0.3, 0.1]) + rng.normal(size=len(i))
    ci, cj = root[i], root[j]
    assert (ci == cj).any() and (ci != cj).any()
    _, se = ols_twoway(X, y, ci, cj, G)
    XtX_inv = np.linalg.inv(X.T @ X)
    e = y - X @ (XtX_inv @ X.T @ y)
    share = ((ci[:, None] == ci[None, :]) | (ci[:, None] == cj[None, :])
             | (cj[:, None] == ci[None, :]) | (cj[:, None] == cj[None, :]))
    s = X * e[:, None]
    meat = s.T @ (share.astype(float) @ s)
    V = XtX_inv @ meat @ XtX_inv
    assert np.allclose(se, np.sqrt(np.diag(V)))
    # model-level clustering (endpoints always distinct) is a special case
    _, se_m = ols_twoway(X, y, i, j, n_models)
    share_m = ((i[:, None] == i[None, :]) | (i[:, None] == j[None, :])
               | (j[:, None] == i[None, :]) | (j[:, None] == j[None, :]))
    Vm = XtX_inv @ (s.T @ (share_m.astype(float) @ s)) @ XtX_inv
    assert np.allclose(se_m, np.sqrt(np.diag(Vm)))
