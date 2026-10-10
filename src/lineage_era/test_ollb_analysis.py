"""Exp04: the real-data pair outcome equals the simulated one the gate used."""
import numpy as np
import pandas as pd
import pytest

from lineage_era.ollb import analysis as A
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


# ---- fail-closed loading (validation manifest + alignment checks) ----------

K_TOY = 12


def _toy(tmp_path, monkeypatch, n=4, categories=None):
    """Tiny population: frozen sample, answer files and validation manifest."""
    frozen, answers = tmp_path / "frozen", tmp_path / "answers"
    frozen.mkdir()
    answers.mkdir()
    monkeypatch.setattr(A, "FROZEN", frozen)
    monkeypatch.setattr(A, "ANSWERS", answers)
    monkeypatch.setattr(A, "MANIFEST", tmp_path / "per_model.csv")
    monkeypatch.setattr(A, "N_ITEMS", K_TOY)
    rng = np.random.default_rng(3)
    models = [f"org/m{k}" for k in range(n)]
    items = np.array([f"s:{k}" for k in range(K_TOY)])
    gold = rng.integers(0, 4, K_TOY).astype(np.int8)
    preds = [rng.integers(0, 4, K_TOY).astype(np.int8) for _ in models]
    for m, p in zip(models, preds):
        np.savez(A.answer_file(m), item=items, gold=gold, hash=np.array([""] * K_TOY),
                 pred=p)
    pd.DataFrame({"model": models, "root": ["a", "a", "b", "b"][:n],
                  "created_month": ["2024-01"] * n, "root_verified": True}
                 ).to_csv(frozen / "primary_sample_cap40.csv", index=False)
    pd.DataFrame({"model": models,
                  "accuracy": [float((p == gold).mean()) for p in preds],
                  "pred_sha256": [A.pred_sha256(p) for p in preds],
                  "category": categories or ["validated"] * n}
                 ).to_csv(A.MANIFEST, index=False)
    return models, items, gold


def _rewrite(model, **fields):
    z = dict(np.load(A.answer_file(model)))
    z.update(fields)
    np.savez(A.answer_file(model), **z)


def test_clean_toy_population_loads(tmp_path, monkeypatch):
    models, _, _ = _toy(tmp_path, monkeypatch)
    pop, info = A.load_population("primary", False)
    pred, gold, checks = A.choice_matrix(pop.model)
    assert list(pop.model) == models and pred.shape == (4, K_TOY)
    assert not any(checks.values()) and "excluded_not_validated" not in info


def test_shuffled_item_order_stops_analysis(tmp_path, monkeypatch):
    models, items, _ = _toy(tmp_path, monkeypatch)
    _rewrite(models[2], item=items[::-1])
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="item_order_mismatch"):
        A.choice_matrix(pop.model)


def test_gold_mismatch_stops_analysis(tmp_path, monkeypatch):
    models, _, gold = _toy(tmp_path, monkeypatch)
    _rewrite(models[1], gold=(gold + 1) % 4)
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="gold_mismatch"):
        A.choice_matrix(pop.model)


def test_hash_mismatch_stops_analysis(tmp_path, monkeypatch):
    models, _, _ = _toy(tmp_path, monkeypatch)
    _rewrite(models[0], hash=np.array([f"h{k}" for k in range(K_TOY)]))
    _rewrite(models[3], hash=np.array([f"x{k}" for k in range(K_TOY)]))
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="hash_mismatch"):
        A.choice_matrix(pop.model)


def test_out_of_range_option_stops_analysis(tmp_path, monkeypatch):
    models, _, _ = _toy(tmp_path, monkeypatch)
    _rewrite(models[1], pred=np.full(K_TOY, 4, dtype=np.int8))
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="outside 0..3"):
        A.choice_matrix(pop.model)


def test_failed_check_model_is_excluded_and_reported(tmp_path, monkeypatch):
    models, _, _ = _toy(tmp_path, monkeypatch,
                        categories=["validated", "failed_check", "validated", "validated"])
    pop, info = A.load_population("primary", False)
    assert models[1] not in set(pop.model)
    assert info["excluded_not_validated"] == [models[1]]


def test_answer_file_missing_from_manifest_stops_analysis(tmp_path, monkeypatch):
    _toy(tmp_path, monkeypatch)
    pd.read_csv(A.MANIFEST).iloc[:3].to_csv(A.MANIFEST, index=False)
    with pytest.raises(ValueError, match="not in the validation manifest"):
        A.load_population("primary", False)


def test_swapped_answer_files_stop_analysis(tmp_path, monkeypatch):
    """Two validated files exchanged after validation pass every alignment
    check; only the manifest's prediction hash binds a file to its model."""
    models, _, _ = _toy(tmp_path, monkeypatch)
    a, b = A.answer_file(models[0]), A.answer_file(models[2])
    tmp = a.with_suffix(".tmp")
    a.rename(tmp)
    b.rename(a)
    tmp.rename(b)
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="not_the_validated_file"):
        A.choice_matrix(pop.model)


def test_edited_answer_file_stops_analysis(tmp_path, monkeypatch):
    models, _, _ = _toy(tmp_path, monkeypatch)
    z = dict(np.load(A.answer_file(models[1])))
    _rewrite(models[1], pred=((z["pred"] + 1) % 4).astype(np.int8))
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="not_the_validated_file"):
        A.choice_matrix(pop.model)


def test_manifest_without_hashes_stops_analysis(tmp_path, monkeypatch):
    _toy(tmp_path, monkeypatch)
    pd.read_csv(A.MANIFEST).drop(columns="pred_sha256").to_csv(A.MANIFEST, index=False)
    pop, _ = A.load_population("primary", False)
    with pytest.raises(ValueError, match="no pred_sha256 column"):
        A.choice_matrix(pop.model)


def test_run_writes_nothing_when_checks_fail(tmp_path, monkeypatch):
    models, items, _ = _toy(tmp_path, monkeypatch)
    _rewrite(models[2], item=items[::-1])
    with pytest.raises(ValueError):
        A.run("primary", out_root=tmp_path / "out")
    assert not (tmp_path / "out").exists()


# ---- R10 root-cluster bootstrap: pair multiplicities -----------------------

def test_root_bootstrap_pair_multiplicities():
    from collections import Counter

    from lineage_era.ollb.pair_gate import root_bootstrap_pairs
    root = np.array([0, 0, 0, 1, 1, 2])            # roots of sizes 3, 2, 1
    members = [np.flatnonzero(root == g) for g in range(3)]
    draw = np.array([0, 0, 1])                       # root 0 twice, root 1 once
    a, c = root_bootstrap_pairs(members, draw)
    got = Counter(zip(np.minimum(a, c).tolist(), np.maximum(a, c).tolist()))
    # Reference: enumerate every pair of positions in the relabelled copies.
    copies = [(m, k) for k, g in enumerate(draw) for m in members[g]]
    want = Counter()
    for p in range(len(copies)):
        for q in range(p + 1, len(copies)):
            m1, m2 = copies[p][0], copies[q][0]
            if m1 != m2:
                want[(min(m1, m2), max(m1, m2))] += 1
    assert got == want
    assert got[(0, 1)] == 4                          # same-root, root drawn twice: k^2
    assert got[(0, 3)] == 2 and got[(3, 4)] == 1     # cross-root k*m; root drawn once
    assert 5 not in a and 5 not in c                 # root 2 not drawn


def test_root_bootstrap_matches_original_inline_code():
    rng = np.random.default_rng(7)
    root = rng.integers(0, 8, 40)
    members = [np.flatnonzero(root == g) for g in range(8)]
    from lineage_era.ollb.pair_gate import root_bootstrap_pairs
    for _ in range(20):
        draw = rng.integers(0, 8, 8)
        idx = np.concatenate([members[g] for g in draw])
        ii, jj = np.triu_indices(len(idx), 1)
        a0, c0 = idx[ii], idx[jj]
        ok = a0 != c0
        a, c = root_bootstrap_pairs(members, draw)
        assert np.array_equal(a, a0[ok]) and np.array_equal(c, c0[ok])
