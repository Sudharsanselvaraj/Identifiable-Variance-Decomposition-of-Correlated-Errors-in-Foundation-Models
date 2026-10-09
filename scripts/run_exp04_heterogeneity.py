#!/usr/bin/env python3
"""Exp04: heterogeneity of the lineage association (post hoc, primary sample).

  H1  per-root shared-root coefficients for every root with >= 8 models
      (the shared-root indicator split by root; other multi-model roots pooled);
      model-level dyadic SEs (a delete-one-root jackknife is undefined per root)
  H2  delete-one-root range: the shared-root and same-month estimates when each
      root, and every pair involving it, is omitted in turn
  H3  per-subject estimates: the pre-specified model refitted with the outcome
      computed on the items of one MMLU subject (pairs with >= 10 jointly wrong
      items in that subject); model-level dyadic SEs
  H4  by capability: the shared-root indicator split by the lower accuracy of
      the two models (< 0.30, 0.30-0.50, 0.50-0.60, >= 0.60); jackknife SEs
  H5  detection: how well a pair's agreement separates same-root from
      different-root pairs (area under the ROC curve, raw and after removing the
      accuracy and release-gap terms), and the outcome distributions
  H6  descriptive statistics of the four analysed samples

Usage (repo root): python3 scripts/run_exp04_heterogeneity.py
Output: results/exp04_heterogeneity/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb import analysis as A  # noqa: E402
from lineage_era.ollb.pair_gate import design, month_index, ols_twoway  # noqa: E402
from run_exp04_final import jackknife_roots, prepared  # noqa: E402

OUT = ROOT / "results" / "exp04_heterogeneity"
Z = 1.959964
MIN_ROOT_MODELS = 8
MIN_SUBJECT_JOINT = 10


def split_same_root(X, names, masks):
    """Replace the shared-root column by one column per mask (masks partition it)."""
    k = names.index("same_root")
    cols = [X[:, :k]] + [m.astype(float)[:, None] for m, _ in masks] + [X[:, k + 1:]]
    return np.hstack(cols), names[:k] + [lab for _, lab in masks] + names[k + 1:]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    d = prepared("primary")
    pop, i, j, y, X, names, rid = (d["pop"], d["i"], d["j"], d["y"], d["X"], d["names"],
                                   d["rid"])
    same = rid[i] == rid[j]
    rows, info = [], {}

    # H1 per root
    counts = pop.root.value_counts()
    big = [r for r, n in counts.items() if n >= MIN_ROOT_MODELS]
    root_of_pair = pop.root.to_numpy()[i]
    masks = [(same & (root_of_pair == r), r) for r in big]
    masks.append((same & ~np.isin(root_of_pair, big), "other multi-model roots"))
    Xr, nr = split_same_root(X, names, masks)
    b, se = ols_twoway(Xr, y, i, j, len(pop))
    for m, lab in masks:
        k = nr.index(lab)
        rows.append({"analysis": "per root", "group": lab, "estimate": b[k], "se": se[k],
                     "ci95_low": b[k] - Z * se[k], "ci95_high": b[k] + Z * se[k],
                     "pairs": int(m.sum()),
                     "models": int(counts.get(lab, (pop.root.isin(
                         [r for r, n in counts.items() if 2 <= n < MIN_ROOT_MODELS])).sum()))})

    # H1b per root, without degenerate models and with identical-prediction
    # clusters collapsed (the duplicates sit mostly in small roots)
    pred = d["pred"]
    same_opt = sum((pred == o).astype(np.float32) @ (pred == o).astype(np.float32).T
                   for o in range(4)) / pred.shape[1]
    ident = same_opt[i, j] >= 0.999
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    N = len(pop)
    _, lab = connected_components(sp.coo_matrix(
        (np.ones(ident.sum()), (i[ident], j[ident])), shape=(N, N)), directed=False)
    first = np.zeros(N, bool)
    for c in np.unique(lab):
        idx = np.flatnonzero(lab == c)
        first[idx[np.argsort(pop.model.values[idx])[0]]] = True
    share = np.stack([(pred == o).mean(1) for o in range(4)], 1).max(1)
    keep = first & (share < 0.95)
    mk = keep[i] & keep[j]
    b, se = ols_twoway(Xr[mk], y[mk], i[mk], j[mk], N)
    for m, lab_ in masks:
        k = nr.index(lab_)
        rows.append({"analysis": "per root, clean sample", "group": lab_, "estimate": b[k],
                     "se": se[k], "ci95_low": b[k] - Z * se[k], "ci95_high": b[k] + Z * se[k],
                     "pairs": int((m & mk).sum())})

    # H2 delete-one-root range
    G = rid.max() + 1
    XtX, Xty = X.T @ X, X.T @ y
    roots = pd.factorize(pop.root)[1]
    est = []
    for g in range(G):
        m = (rid[i] == g) | (rid[j] == g)
        bg = np.linalg.solve(XtX - X[m].T @ X[m], Xty - X[m].T @ y[m])
        est.append((roots[g], bg[names.index("same_root")], bg[names.index("gap0")]))
    e = pd.DataFrame(est, columns=["root", "same_root", "gap0"])
    e.to_csv(OUT / "delete_one_root.csv", index=False)
    for t in ("same_root", "gap0"):
        info[f"delete_one_root_{t}"] = {
            "min": float(e[t].min()), "min_root": e.loc[e[t].idxmin(), "root"],
            "max": float(e[t].max()), "max_root": e.loc[e[t].idxmax(), "root"]}

    # H3 per subject
    items = np.load(A.answer_file(pop.model.iloc[0]))["item"]
    subj = np.array([str(it).split(":")[0] for it in items])
    pred, gold, acc = d["pred"], d["gold"], d["acc"]
    mon = month_index(pop.created_month)
    sub_rows = []
    for s_ in sorted(set(subj)):
        km = subj == s_
        si, sj, sy, snb = A.pair_outcomes(pred[:, km], gold[km])
        keep = snb >= MIN_SUBJECT_JOINT
        si, sj, sy = si[keep], sj[keep], sy[keep]
        Xs, ns = design(si, sj, rid, mon, acc)
        bs, ses = ols_twoway(Xs, sy, si, sj, len(pop))
        k, g = ns.index("same_root"), ns.index("gap0")
        sub_rows.append({"subject": s_, "items": int(km.sum()), "pairs": int(keep.sum()),
                         "same_root": bs[k], "same_root_se": ses[k],
                         "gap0": bs[g], "gap0_se": ses[g]})
    sub = pd.DataFrame(sub_rows)
    sub.to_csv(OUT / "per_subject.csv", index=False)
    info["per_subject"] = {
        "subjects": len(sub),
        "same_root_positive": int((sub.same_root > 0).sum()),
        "same_root_ci_excludes_zero": int((sub.same_root - Z * sub.same_root_se > 0).sum()),
        "same_root_median": float(sub.same_root.median()),
        "same_root_min": [sub.loc[sub.same_root.idxmin(), "subject"], float(sub.same_root.min())],
        "same_root_max": [sub.loc[sub.same_root.idxmax(), "subject"], float(sub.same_root.max())],
        "gap0_median": float(sub.gap0.median()),
        "gap0_ci_above_zero": int(((sub.gap0 - Z * sub.gap0_se) > 0).sum()),
        "gap0_ci_below_zero": int(((sub.gap0 + Z * sub.gap0_se) < 0).sum())}

    # H4 by capability (lower accuracy of the pair)
    low = np.minimum(acc[i], acc[j])
    bands = [(low < 0.30, "< 0.30"), ((low >= 0.30) & (low < 0.50), "0.30-0.50"),
             ((low >= 0.50) & (low < 0.60), "0.50-0.60"), (low >= 0.60, ">= 0.60")]
    masks = [(same & m, f"lower accuracy {lab}") for m, lab in bands]
    Xc, nc = split_same_root(X, names, masks)
    bc = np.linalg.lstsq(Xc, y, rcond=None)[0]
    sec = jackknife_roots(Xc, y, rid, i, j)
    for m, lab in masks:
        k = nc.index(lab)
        rows.append({"analysis": "by capability", "group": lab, "estimate": bc[k],
                     "se": sec[k], "ci95_low": bc[k] - Z * sec[k],
                     "ci95_high": bc[k] + Z * sec[k], "pairs": int(m.sum())})

    # H5 detection
    from scipy.stats import rankdata

    def auc(score, label):
        r = rankdata(score)
        n1, n0 = label.sum(), (~label).sum()
        return float((r[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    keepc = [k for k, n in enumerate(names) if n != "same_root"]
    bres = np.linalg.lstsq(X[:, keepc], y, rcond=None)[0]
    resid = y - X[:, keepc] @ bres
    det = {"auc_raw": auc(y, same), "auc_net_of_accuracy_and_gap": auc(resid, same),
           "same_root_pairs": int(same.sum()), "other_pairs": int((~same).sum())}
    for q in (0.5, 0.6, 0.7):
        det[f"share_same_root_pairs_above_{q}"] = float((y[same] > q).mean())
        det[f"share_other_pairs_above_{q}"] = float((y[~same] > q).mean())
    info["detection"] = det
    hist = np.histogram(y[same], bins=40, range=(0, 1))[0], \
        np.histogram(y[~same], bins=40, range=(0, 1))[0]
    pd.DataFrame({"bin_low": np.linspace(0, 1, 41)[:-1], "same_root": hist[0],
                  "different_root": hist[1]}).to_csv(OUT / "agreement_hist.csv", index=False)
    resid_hist = np.histogram(resid[same], bins=40, range=(-0.4, 0.6))[0], \
        np.histogram(resid[~same], bins=40, range=(-0.4, 0.6))[0]
    pd.DataFrame({"bin_low": np.linspace(-0.4, 0.6, 41)[:-1], "same_root": resid_hist[0],
                  "different_root": resid_hist[1]}).to_csv(OUT / "residual_hist.csv",
                                                           index=False)

    # H6 descriptives
    desc = []
    for pop_name, min_acc in (("primary", None), ("primary", 0.30), ("expanded", None),
                              ("expanded", 0.30)):
        dd = d if (pop_name, min_acc) == ("primary", None) else prepared(pop_name, min_acc=min_acc)
        vc = dd["pop"].root.value_counts()
        sr = dd["rid"][dd["i"]] == dd["rid"][dd["j"]]
        desc.append({"sample": pop_name + ("_S2" if min_acc else ""), "models": len(dd["pop"]),
                     "roots": len(vc), "roots_ge2": int((vc >= 2).sum()),
                     "pairs": len(dd["y"]), "same_root_pairs": int(sr.sum()),
                     "months": dd["pop"].created_month.nunique(),
                     "accuracy_median": float(np.median(dd["acc"])),
                     "accuracy_min": float(dd["acc"].min()), "accuracy_max": float(dd["acc"].max()),
                     "agreement_mean": float(dd["y"].mean()),
                     "agreement_same_root": float(dd["y"][sr].mean()),
                     "agreement_other": float(dd["y"][~sr].mean()),
                     "joint_wrong_median": float(np.median(dd["nb"]))})
    pd.DataFrame(desc).to_csv(OUT / "descriptives.csv", index=False)

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "heterogeneity.csv", index=False)
    (OUT / "info.json").write_text(json.dumps(info, indent=1, default=str))
    pd.set_option("display.width", 200)
    print(res.round(4).to_string(index=False))
    print(json.dumps(info, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
