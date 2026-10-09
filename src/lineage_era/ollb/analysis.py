"""Exp04 primary analysis (pre-registered in docs/05_Experiments/Exp04_*.md).

For one frozen population sample:
    agree_ij = P(same wrong option | both wrong) over the 14,042 MMLU items
    agree_ij = b0 + bL*same_root + sum_g bE_g*[|dmonth| in g]
               + c1*(acc_i + acc_j) + c2*|acc_i - acc_j| + e_ij
with two-way (model i, model j) cluster-robust SEs. Gap bins 0, 1-2, 3-5,
6-11 months; 12+ is the reference.

Inputs: the frozen sample CSV (root, created_month, root_verified) and the
validated per-model answer files in datasets/ollb/v1/. Models whose download
was rejected are reported, never replaced.

Usage (repo root):
    python3 -m lineage_era.ollb.analysis --population primary
    python3 -m lineage_era.ollb.analysis --population expanded
    python3 -m lineage_era.ollb.analysis --population primary --strict
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .pair_gate import design, month_index, ols_twoway

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "datasets" / "ollb" / "frozen"
ANSWERS = ROOT / "datasets" / "ollb" / "v1"
OUT = ROOT / "results" / "exp04_analysis"


def answer_file(model: str) -> Path:
    return ANSWERS / f"{model.replace('/', '__')}.npz"


def load_population(name: str, strict: bool) -> tuple[pd.DataFrame, dict]:
    sample = pd.read_csv(FROZEN / f"{name}_sample_cap40.csv")
    if strict:
        sample = sample[sample.root_verified]
    have = sample.model.map(lambda m: answer_file(m).exists())
    info = {"frozen_sample": int(len(sample)), "with_answers": int(have.sum()),
            "missing_answers": sorted(sample.model[~have])}
    return sample[have].reset_index(drop=True), info


def choice_matrix(models: pd.Series) -> tuple[np.ndarray, np.ndarray, dict]:
    """N x K chosen options and the common gold vector; checks item alignment."""
    ref = np.load(answer_file(models.iloc[0]))
    items, gold = ref["item"], ref["gold"]
    ref_hash = None
    pred = np.empty((len(models), len(items)), dtype=np.int8)
    checks = {"item_order_mismatch": [], "gold_mismatch": [], "hash_mismatch": []}
    for r, m in enumerate(models):
        z = np.load(answer_file(m))
        if not np.array_equal(z["item"], items):
            checks["item_order_mismatch"].append(m)
        if not np.array_equal(z["gold"], gold):
            checks["gold_mismatch"].append(m)
        h = z["hash"]
        if (h != "").all():
            if ref_hash is None:
                ref_hash = h
            elif not np.array_equal(h, ref_hash):
                checks["hash_mismatch"].append(m)
        pred[r] = z["pred"]
    return pred, gold, checks


def pair_outcomes(pred: np.ndarray, gold: np.ndarray):
    """Upper-triangle pairs with agree_ij = same wrong option / both wrong."""
    wrong = pred != gold[None, :]
    W = wrong.astype(np.float32)
    both = W @ W.T
    same = np.zeros_like(both)
    for o in range(4):
        B = ((pred == o) & wrong).astype(np.float32)
        same += B @ B.T
    i, j = np.triu_indices(len(pred), 1)
    ok = both[i, j] > 0
    return i[ok], j[ok], (same[i, j] / both[i, j])[ok], both[i, j][ok]


def position_tv(pred: np.ndarray, i: np.ndarray, j: np.ndarray) -> np.ndarray:
    """Total-variation distance between two models' chosen-option distributions."""
    dist = np.stack([(pred == o).mean(1) for o in range(4)], axis=1)
    return 0.5 * np.abs(dist[i] - dist[j]).sum(1)


def run(name: str, strict: bool = False, position: bool = False,
        min_acc: float | None = None, out_root: Path = OUT) -> dict:
    """Primary model; position=True adds S1, min_acc adds S2 (Amendment 3)."""
    pop, info = load_population(name, strict)
    pred, gold, checks = choice_matrix(pop.model)
    acc = (pred == gold[None, :]).mean(1)
    if min_acc is not None:
        keep = acc >= min_acc
        info["dropped_below_min_acc"] = int((~keep).sum())
        pop, pred, acc = pop[keep].reset_index(drop=True), pred[keep], acc[keep]
    root_id = pd.factorize(pop.root)[0]
    month = month_index(pop.created_month)
    i, j, y, n_both = pair_outcomes(pred, gold)
    X, names = design(i, j, root_id, month, acc)
    if position:
        X = np.column_stack([X, position_tv(pred, i, j)])
        names = [*names, "position_tv"]
    beta, se = ols_twoway(X, y, i, j, len(pop))
    coef = pd.DataFrame({"term": names, "estimate": beta, "se": se})
    coef["z"] = coef.estimate / coef.se
    label = (f"{name}{'_strict' if strict else ''}"
             f"{'_S1position' if position else ''}"
             f"{f'_S2acc{min_acc:g}' if min_acc is not None else ''}")
    out = Path(out_root) / label
    out.mkdir(parents=True, exist_ok=True)
    coef.to_csv(out / "coefficients.csv", index=False)
    summary = {
        "population": label, **info, "models_analysed": int(len(pop)),
        "pairs": int(len(y)), "roots": int(pop.root.nunique()),
        "same_root_pairs": int((root_id[i] == root_id[j]).sum()),
        "mean_agreement": float(y.mean()), "mean_accuracy": float(acc.mean()),
        "alignment_checks": {k: len(v) for k, v in checks.items()},
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    return {"summary": summary, "coefficients": coef}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--population", choices=["primary", "expanded"], required=True)
    ap.add_argument("--strict", action="store_true",
                    help="restrict to roots verified as pretrained")
    ap.add_argument("--position", action="store_true",
                    help="S1: add answer-position-bias covariate")
    ap.add_argument("--min-acc", type=float, default=None,
                    help="S2: keep models with accuracy >= this (0.30)")
    args = ap.parse_args(argv)
    res = run(args.population, args.strict, args.position, args.min_acc)
    print(json.dumps(res["summary"], indent=1))
    print(res["coefficients"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
