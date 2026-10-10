#!/usr/bin/env python3
"""Exp04 post-hoc checks added after the pre-submission audit (audit/ISSUE_REGISTER.csv).

All post hoc; the main results were known. For the primary and expanded samples:

  ISS-04  influence of the largest roots
          - share of the delete-one-root jackknife variance of the shared-root
            coefficient due to the most influential deletion (top 1 / 5 / 10)
          - the pre-specified model refitted without the two largest roots
            (every model of those roots removed), with its jackknife CI
  ISS-05  developer practice: a same-uploader indicator (same Hub account, the
          part of the repository id before '/', case-insensitive)
          - shared-root coefficient controlling for it, and its own coefficient
          - shared-root coefficient excluding same-root pairs by one uploader

Inference: delete-one-root jackknife (the paper's main interval), 95% normal CIs.
The audit computed the same quantities with independent code
(audit/tools/independent_checks.py, audit/outputs/uploader_check.json).

Usage (repo root; needs the validated answer files):
    python3 scripts/run_exp04_audit_followup.py
Writes results/exp04_audit_followup/{followup.csv, summary.md}.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "exp04_audit_followup"
Z = 1.959963984540054

_spec = importlib.util.spec_from_file_location("run_exp04_final",
                                               ROOT / "scripts" / "run_exp04_final.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)


def ols(X, y):
    return np.linalg.solve(X.T @ X, X.T @ y)


def row(sample, check, term, est, se, pairs, **extra):
    return {"sample": sample, "check": check, "term": term, "estimate": est, "se_jackknife": se,
            "ci_lo": est - Z * se, "ci_hi": est + Z * se, "pairs": pairs, **extra}


def run(sample: str) -> list[dict]:
    d = F.prepared(sample)
    X, y, i, j, rid, names = d["X"], d["y"], d["i"], d["j"], d["rid"], d["names"]
    k = names.index("same_root")
    rows = []

    # ---- ISS-04: jackknife variance concentration and the two largest roots
    G = rid.max() + 1
    XtX, Xty = X.T @ X, X.T @ y
    loo = np.array([np.linalg.solve(XtX - X[m].T @ X[m], Xty - X[m].T @ y[m])[k]
                    for m in (((rid[i] == g) | (rid[j] == g)) for g in range(G))])
    dev = np.sort((loo - loo.mean()) ** 2)[::-1]
    se = F.jackknife_roots(X, y, rid, i, j)[k]
    b = ols(X, y)[k]
    rows.append(row(sample, "pre-specified model", "same_root", b, se, len(y),
                    jk_top1_share=dev[:1].sum() / dev.sum(), jk_top5_share=dev[:5].sum() / dev.sum(),
                    jk_top10_share=dev[:10].sum() / dev.sum(),
                    loo_min=loo.min(), loo_max=loo.max()))
    largest = pd.Series(rid).value_counts().index[:2]
    keep_m = ~np.isin(rid, largest)
    keep = keep_m[i] & keep_m[j]
    new_id = -np.ones(len(rid), int)
    new_id[keep_m] = pd.factorize(rid[keep_m])[0]
    b2 = ols(X[keep], y[keep])[k]
    se2 = F.jackknife_roots(X[keep], y[keep], new_id, i[keep], j[keep])[k]
    top = [d["pop"].root[np.flatnonzero(rid == g)[0]] for g in largest]
    rows.append(row(sample, "without the two largest roots", "same_root", b2, se2, int(keep.sum()),
                    same_root_pairs=int(X[keep, k].sum()), removed=" + ".join(top)))

    # ---- ISS-05: same uploader (Hub account)
    org = pd.factorize(d["pop"].model.str.split("/").str[0].str.lower())[0]
    su = (org[i] == org[j]).astype(float)
    sr = X[:, k] == 1
    Xu = np.column_stack([X, su])
    bu = ols(Xu, y)
    seu = F.jackknife_roots(Xu, y, rid, i, j)
    rows.append(row(sample, "controlling for same uploader", "same_root", bu[k], seu[k], len(y),
                    uploaders=int(org.max() + 1), same_root_same_uploader=int((sr & (su == 1)).sum()),
                    same_uploader_diff_root=int((~sr & (su == 1)).sum())))
    rows.append(row(sample, "controlling for same uploader", "same_uploader", bu[-1], seu[-1], len(y)))
    ex = ~(sr & (su == 1))
    b3 = ols(X[ex], y[ex])[k]
    se3 = F.jackknife_roots(X[ex], y[ex], rid, i[ex], j[ex])[k]
    rows.append(row(sample, "excluding same-root pairs by one uploader", "same_root", b3, se3,
                    int(ex.sum())))
    return rows


def main() -> int:
    # macOS Accelerate raises spurious matmul flags; the products are exact
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        df = pd.DataFrame([r for s in ("primary", "expanded") for r in run(s)])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "followup.csv", index=False)
    show = df[["sample", "check", "term", "estimate", "ci_lo", "ci_hi", "pairs"]].copy()
    for c in ("estimate", "ci_lo", "ci_hi"):
        show[c] = (100 * show[c]).round(2)
    pre = df[df.check == "pre-specified model"].set_index("sample")
    lines = ["# Exp04 post-hoc checks after the pre-submission audit", "",
             "All post hoc. Points; delete-one-root jackknife 95% CIs.", "",
             show.to_markdown(index=False), "",
             "Jackknife variance of the shared-root coefficient due to the most influential "
             "root deletions (share of the sum of squared deviations):", ""]
    for s, r in pre.iterrows():
        lines.append(f"- {s}: top 1 {100 * r.jk_top1_share:.1f}%, top 5 {100 * r.jk_top5_share:.1f}%, "
                     f"top 10 {100 * r.jk_top10_share:.1f}%; leave-one-root-out range "
                     f"{100 * r.loo_min:.2f} to {100 * r.loo_max:.2f}")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
