"""Exp04 inference: the delete-one-root jackknife and a toy end-to-end pipeline.

The jackknife in scripts/run_exp04_final.py updates X'X by subtracting the
pairs that touch a root; here it is compared with literal refits. The
end-to-end test runs the fail-closed loader, pair outcomes, design (Eq. 2)
and two-way dyadic SEs (Eq. 3) on a toy population with a planted effect.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from lineage_era.ollb import analysis as A
from lineage_era.ollb.pair_gate import (Truth, design, month_index, ols_twoway,
                                        simulate_choices)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run_exp04_final.py"


def _final():
    spec = importlib.util.spec_from_file_location("run_exp04_final", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _toy_pairs(seed=11, n_models=30, G=6):
    rng = np.random.default_rng(seed)
    rid = rng.integers(0, G, n_models)
    month = rng.integers(0, 18, n_models)
    acc = rng.uniform(0.3, 0.7, n_models)
    i, j = np.triu_indices(n_models, 1)
    X, names = design(i, j, rid, month, acc)
    y = 0.4 + 0.12 * X[:, names.index("same_root")] + rng.normal(0, 0.05, len(i))
    return X, y, rid, i, j, names


def test_jackknife_downdate_equals_literal_refits():
    X, y, rid, i, j, _ = _toy_pairs()
    se = _final().jackknife_roots(X, y, rid, i, j)
    G = rid.max() + 1
    betas = []
    for g in range(G):
        keep = (rid[i] != g) & (rid[j] != g)
        betas.append(np.linalg.lstsq(X[keep], y[keep], rcond=None)[0])
    B = np.array(betas)
    want = np.sqrt((G - 1) / G * ((B - B.mean(0)) ** 2).sum(0))
    assert np.allclose(se, want)


def test_jackknife_is_zero_without_between_root_variation():
    # y exactly linear in X: every delete-one-root fit returns the same beta.
    X, _, rid, i, j, _ = _toy_pairs(seed=3)
    y = X @ np.linspace(0.1, 0.5, X.shape[1])
    assert np.allclose(_final().jackknife_roots(X, y, rid, i, j), 0, atol=1e-10)


def test_toy_end_to_end_recovers_planted_lineage_effect(tmp_path, monkeypatch):
    """Answer files -> manifest -> fail-closed loader -> Eq. 1 -> Eq. 2 -> Eq. 3."""
    K, G, per_root = 1500, 12, 4
    n = G * per_root
    monkeypatch.setattr(A, "FROZEN", tmp_path)
    monkeypatch.setattr(A, "ANSWERS", tmp_path)
    monkeypatch.setattr(A, "MANIFEST", tmp_path / "per_model.csv")
    monkeypatch.setattr(A, "N_ITEMS", K)
    rng = np.random.default_rng(8)
    root_id = np.repeat(np.arange(G), per_root)
    month = rng.integers(0, 20, n)
    ch = simulate_choices(root_id, month, Truth(lam_L=0.15), K=K, rng=rng)
    gold = rng.integers(0, 4, K).astype(np.int8)        # gold not always option 0
    pred = ((ch + gold[None, :]) % 4).astype(np.int8)  # gate code 0 = correct
    items = np.array([f"s:{k}" for k in range(K)])
    models = [f"org/m{k}" for k in range(n)]
    for m, p in zip(models, pred):
        np.savez(A.answer_file(m), item=items, gold=gold,
                 hash=np.array([""] * K), pred=p)
    months = [f"2023-{1 + mo % 12:02d}" if mo < 12 else f"2024-{1 + mo % 12:02d}"
              for mo in month]
    pd.DataFrame({"model": models, "root": [f"r{g}" for g in root_id],
                  "created_month": months, "root_verified": True}
                 ).to_csv(tmp_path / "primary_sample_cap40.csv", index=False)
    pd.DataFrame({"model": models,
                  "accuracy": [float((p == gold).mean()) for p in pred],
                  "pred_sha256": [A.pred_sha256(p) for p in pred],
                  "category": "validated"}).to_csv(A.MANIFEST, index=False)

    pop, _ = A.load_population("primary", False)
    P, gold2, _ = A.choice_matrix(pop.model)
    acc = (P == gold2[None, :]).mean(1)
    rid = pd.factorize(pop.root)[0]
    i, j, y, _ = A.pair_outcomes(P, gold2)
    X, names = design(i, j, rid, month_index(pop.created_month), acc)
    beta, se = ols_twoway(X, y, i, j, len(pop))
    k = names.index("same_root")
    assert beta[k] > 0 and beta[k] / se[k] > 4
    # the jackknife (headline interval) runs on the real design matrix
    se_jk = _final().jackknife_roots(X, y, rid, i, j)
    assert se_jk[k] > 0
