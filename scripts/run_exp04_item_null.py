#!/usr/bin/env python3
"""Item-difficulty-aware null models for Exp04 (post hoc, exploratory).

Added in response to review, after the results were known. Excess agreement
depends on the null model (Jo, Garg & Raghavan, 2026). Two item-aware nulls:

N1  same-wrong-option agreement relative to item-specific distractor
    popularity. For item k, p_k(o) is the share of wrong models choosing
    wrong option o; under the null two models that are both wrong on k pick
    the same option with probability q_k = sum_o p_k(o)^2. The pair's
    expected agreement is the mean of q_k over its jointly-wrong items, and
    the outcome is observed minus expected.
      N1a  p_k from all models (conservative: a large lineage cluster pulls
           p_k towards its own choices and is partly absorbed by the null);
      N1b  p_k with every lineage root weighted equally.
N2  co-failure (both wrong) relative to a Rasch model with item difficulty
    and model ability: logit P(wrong_ik) = d_k - theta_i, fitted by joint
    maximum likelihood; outcome = (observed - expected co-failures) / K.

Each outcome is regressed on the pre-registered design (Eq. 3) with dyadic
cluster-robust SEs, plus the delete-one-root jackknife for the lineage term.

Usage (repo root): python3 scripts/run_exp04_item_null.py
Output: results/exp04_item_null/item_null.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb.pair_gate import ols_twoway  # noqa: E402
from run_exp04_final import jackknife_roots, prepared  # noqa: E402

OUT = ROOT / "results" / "exp04_item_null"


def distractor_null(pred, gold, weights):
    """q_k = sum_o p_k(o)^2 with p_k from weighted wrong choices."""
    wrong = pred != gold[None, :]
    num = np.stack([((pred == o) & wrong).T.astype(float) @ weights for o in range(4)], 1)
    den = num.sum(1, keepdims=True)
    p = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    return (p ** 2).sum(1)                                  # K


def expected_agreement(pred, gold, q, i, j):
    W = (pred != gold[None, :]).astype(np.float32)
    num = (W * q[None, :].astype(np.float32)) @ W.T
    den = W @ W.T
    return (num[i, j] / den[i, j]).astype(float)


def rasch_errors(W: np.ndarray, iters: int = 200) -> np.ndarray:
    """JML Rasch for error probabilities: logit P(w_ik) = d_k - theta_i."""
    theta = np.zeros(W.shape[0])
    d = np.zeros(W.shape[1])
    for _ in range(iters):
        P = 1 / (1 + np.exp(-(d[None, :] - theta[:, None])))
        info = P * (1 - P)
        d += (W - P).sum(0) / np.maximum(info.sum(0), 1e-9)
        P = 1 / (1 + np.exp(-(d[None, :] - theta[:, None])))
        info = P * (1 - P)
        theta -= (W - P).sum(1) / np.maximum(info.sum(1), 1e-9)
        d = np.clip(d, -12, 12)
        theta -= theta.mean()
    return 1 / (1 + np.exp(-(d[None, :] - theta[:, None])))


def main() -> int:
    rows = []
    for pop_name in ("primary", "expanded"):
        for min_acc in (None, 0.30):
            dd = prepared(pop_name, min_acc=min_acc)
            pred, gold, i, j, rid = dd["pred"], dd["gold"], dd["i"], dd["j"], dd["rid"]
            X, names, y = dd["X"], dd["names"], dd["y"]
            N, K = pred.shape
            root_w = 1.0 / np.bincount(rid)[rid]               # each root sums to 1
            W = (pred != gold[None, :]).astype(float)
            P = rasch_errors(W)
            co_obs = (W @ W.T)[i, j]
            co_exp = (P @ P.T)[i, j]
            outcomes = {
                "pre-registered: same-wrong agreement": y,
                "N1a: minus item distractor null (all models)":
                    y - expected_agreement(pred, gold, distractor_null(pred, gold, np.ones(N)), i, j),
                "N1b: minus item distractor null (roots weighted equally)":
                    y - expected_agreement(pred, gold, distractor_null(pred, gold, root_w), i, j),
                "N2: excess co-failure over Rasch null (per item)": (co_obs - co_exp) / K,
            }
            for label, yy in outcomes.items():
                b, se = ols_twoway(X, yy, i, j, N)
                jk = jackknife_roots(X, yy, rid, i, j)
                for t in ("same_root", "gap0"):
                    k = names.index(t)
                    z = b[k] / se[k]
                    rows.append({"population": pop_name + ("_S2" if min_acc else ""),
                                 "outcome": label, "term": t, "estimate": b[k],
                                 "se": se[k], "ci_low": b[k] - 1.96 * se[k],
                                 "ci_high": b[k] + 1.96 * se[k],
                                 "p": 2 * norm.sf(abs(z)), "se_jackknife": jk[k],
                                 "p_jackknife": 2 * norm.sf(abs(b[k] / jk[k])),
                                 "outcome_mean": float(np.mean(yy)), "models": N})
            print(pop_name, min_acc, "done", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "item_null.csv", index=False)
    pd.set_option("display.width", 220)
    print(df[["population", "outcome", "term", "estimate", "se", "p", "se_jackknife",
              "p_jackknife", "outcome_mean"]].round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
