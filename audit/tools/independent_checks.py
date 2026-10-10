#!/usr/bin/env python3
"""Audit Phase 3/4: further independent checks built on independent_verify.py.

  1. the 12 pre-specified analyses, reproduced independently
  2. descriptive claims of Section V-A / III (raw pattern, counts, accuracy trend)
  3. root dominance: drop the two largest roots, jackknife variance concentration
  4. alternative inference: jackknife over multi-model roots only, vertex bootstrap
  5. per-root coefficients: unweighted mean and DerSimonian-Laird pooling
  6. estimator variants: WLS by joint errors, equivalence bound
Outputs: audit/outputs/independent_checks.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
import independent_verify as V  # noqa: E402

OUT = {}


def tv_covariate(pred, I, J):
    dist = np.stack([(pred == o).mean(1) for o in range(4)], 1)
    return 0.5 * np.abs(dist[I] - dist[J]).sum(1)


def fit(sample, strict=False, s1=False, s2=False):
    s, pred, gold, acc = V.load(sample, 0.30 if s2 else None)
    if strict:
        keep = s.root_verified.to_numpy()
        s, pred, acc = s[keep].reset_index(drop=True), pred[keep], acc[keep]
    I, J, y, both, _ = V.pair_outcomes(pred, gold)
    X, root = V.design(s, acc, I, J)
    names = list(V.NAMES)
    if s1:
        X = np.column_stack([X, tv_covariate(pred, I, J)]); names.append("tv")
    b = V.ols(X, y)
    se = V.dyadic_se(X, y, b, I, J, len(s))
    return dict(s=s, pred=pred, gold=gold, acc=acc, I=I, J=J, y=y, both=both, X=X, root=root,
                b=b, se=se, names=names, n=len(s))


# ---------------------------------------------------------------- 1. the twelve analyses
pre = pd.read_csv(V.ROOT / "results/exp04_final/prereg_12.csv").set_index(["analysis", "term"])
twelve, maxdiff = {}, 0.0
for pop in ("primary", "expanded"):
    for tag, kw in (("", {}), ("_strict", dict(strict=True)), ("_S1position", dict(s1=True)),
                    ("_S2acc0.3", dict(s2=True)), ("_S1position_S2acc0.3", dict(s1=True, s2=True)),
                    ("_strict_S1position_S2acc0.3", dict(strict=True, s1=True, s2=True))):
        f = fit(pop, **kw)
        lab = pop + tag
        for term in ("same_root", "gap0"):
            k = f["names"].index(term)
            p = pre.loc[(lab, term)]
            d = max(abs(f["b"][k] - p.estimate), abs(f["se"][k] - p.se))
            maxdiff = max(maxdiff, d)
            twelve[f"{lab}|{term}"] = {"mine": float(f["b"][k]), "committed": float(p.estimate),
                                      "se_mine": float(f["se"][k]), "se_committed": float(p.se),
                                      "models": f["n"], "pairs": int(len(f["y"]))}
OUT["twelve_analyses"] = twelve
OUT["twelve_max_abs_diff_estimate_or_se"] = maxdiff
print(f"[1] 12 analyses x 2 terms reproduced; max |diff| in estimate or SE vs committed = {maxdiff:.2e}")

# ---------------------------------------------------------------- 2. descriptive claims
f = fit("primary")
s, pred, gold, acc, I, J, y, both, X, root, b = (f[k] for k in ("s", "pred", "gold", "acc", "I", "J", "y", "both", "X", "root", "b"))
sr = X[:, 1] == 1
gapcols = {"0": X[:, 2] == 1, "1-2": X[:, 3] == 1, "3-5": X[:, 4] == 1, "6-11": X[:, 5] == 1}
gapcols["12+"] = ~(gapcols["0"] | gapcols["1-2"] | gapcols["3-5"] | gapcols["6-11"])
desc = {"pairs": int(len(y)), "models": f["n"], "roots": int(root.max() + 1),
        "roots_with_2plus_models": int((np.bincount(root) >= 2).sum()),
        "same_root_pairs": int(sr.sum()), "mean_agreement": float(y.mean()),
        "mean_same_root": float(y[sr].mean()), "mean_diff_root": float(y[~sr].mean()),
        "joint_wrong_min": int(both.min()), "joint_wrong_median": float(np.median(both)), "joint_wrong_max": int(both.max()),
        "by_gap": {g: {"same_root_pairs": int((m & sr).sum()), "diff_root_pairs": int((m & ~sr).sum()),
                       "mean_same": float(y[m & sr].mean()) if (m & sr).sum() else None,
                       "mean_diff": float(y[m & ~sr].mean())} for g, m in gapcols.items()}}
per = pd.PeriodIndex(s.created_month, freq="M")
mm = (per.year * 12 + per.month).to_numpy()
yr = per.year.to_numpy()
desc["median_acc_2022_2023"] = float(np.median(acc[yr <= 2023])); desc["median_acc_2024"] = float(np.median(acc[yr == 2024]))
desc["spearman_acc_month"] = float(spearmanr(mm, acc).statistic)
desc["median_acc"] = float(np.median(acc)); desc["n_acc_below_0.30"] = int((acc < 0.30).sum())
top = pd.Series(root).value_counts().head(3)
desc["largest_roots"] = {s.root[np.flatnonzero(root == g)[0]]: int(c) for g, c in top.items()}
OUT["descriptive"] = desc
print(f"[2] pairs {desc['pairs']:,}; same-root {desc['same_root_pairs']}; mean agreement {desc['mean_agreement']:.4f} "
      f"(same {desc['mean_same_root']:.4f}, diff {desc['mean_diff_root']:.4f}); joint-wrong {desc['joint_wrong_min']}..{desc['joint_wrong_max']} med {desc['joint_wrong_median']:.0f}")
print("    by gap:", {g: (v['same_root_pairs'], round(v['mean_same'], 3) if v['mean_same'] else None, round(v['mean_diff'], 3)) for g, v in desc["by_gap"].items()})
print(f"    median accuracy 2022-23 {desc['median_acc_2022_2023']:.3f}, 2024 {desc['median_acc_2024']:.3f}; Spearman {desc['spearman_acc_month']:.3f}")

# without accuracy terms
Xn = X[:, :6]
bn = V.ols(Xn, y)
OUT["no_accuracy_terms"] = {nm: float(v) for nm, v in zip(V.NAMES[:6], bn)}
print("    without accuracy terms: shared-root %.1f, gap0 %.1f, gap1-2 %.1f, gap3-5 %.1f, gap6-11 %.1f" % tuple(100 * bn[1:6]))

# ---------------------------------------------------------------- 3. root dominance
se_jk, B = V.jackknife(X, y, root, I, J)
k = 1
roots_sorted = pd.Series(root).value_counts()
r1, r2 = roots_sorted.index[:2]
keep = ~np.isin(root[I], [r1, r2]) & ~np.isin(root[J], [r1, r2])
b_drop2 = V.ols(X[keep], y[keep])
se_drop2, _ = V.jackknife(X[keep], y[keep], root[keep] if False else root, I[keep], J[keep], groups=np.setdiff1d(np.unique(root), [r1, r2]))
OUT["drop_top2_roots"] = {"roots": [s.root[np.flatnonzero(root == r1)[0]], s.root[np.flatnonzero(root == r2)[0]]],
                          "same_root_pairs_left": int((X[keep, 1] == 1).sum()), "estimate": float(b_drop2[k]),
                          "jackknife_se": float(se_drop2[k]),
                          "ci": [float(b_drop2[k] - V.Z * se_drop2[k]), float(b_drop2[k] + V.Z * se_drop2[k])]}
dev2 = (B[:, k] - B[:, k].mean()) ** 2
order = np.argsort(-dev2)
OUT["jackknife_variance_concentration"] = {"top1_share": float(dev2[order[:1]].sum() / dev2.sum()),
                                           "top5_share": float(dev2[order[:5]].sum() / dev2.sum()),
                                           "top10_share": float(dev2[order[:10]].sum() / dev2.sum()),
                                           "n_roots_deleted": int(len(dev2)),
                                           "leave_one_out_min": float(B[:, k].min()), "leave_one_out_max": float(B[:, k].max())}
print(f"[3] drop the two largest roots entirely: shared-root {100*b_drop2[k]:.2f} pts, jackknife CI "
      f"[{100*OUT['drop_top2_roots']['ci'][0]:.1f}, {100*OUT['drop_top2_roots']['ci'][1]:.1f}], same-root pairs left {OUT['drop_top2_roots']['same_root_pairs_left']}")
print(f"    leave-one-root-out range {100*B[:,k].min():.2f}..{100*B[:,k].max():.2f}; jackknife variance: top-1 root {100*OUT['jackknife_variance_concentration']['top1_share']:.1f}%, top-5 {100*OUT['jackknife_variance_concentration']['top5_share']:.1f}%, top-10 {100*OUT['jackknife_variance_concentration']['top10_share']:.1f}% of {len(dev2)} deletions")

# ---------------------------------------------------------------- 4. alternative inference
multi = np.flatnonzero(np.bincount(root) >= 2)
se_m_only, _ = V.jackknife(X, y, root, I, J, groups=multi)
OUT["jackknife_multi_model_roots_only"] = {"G": int(len(multi)), "se": float(se_m_only[k]),
                                           "ci": [float(b[k] - V.Z * se_m_only[k]), float(b[k] + V.Z * se_m_only[k])]}
print(f"[4] jackknife over only the {len(multi)} multi-model roots: SE {100*se_m_only[k]:.2f} (all-roots jackknife SE {100*se_jk[k]:.2f}); CI [{100*OUT['jackknife_multi_model_roots_only']['ci'][0]:.1f}, {100*OUT['jackknife_multi_model_roots_only']['ci'][1]:.1f}]")
# vertex ("pigeonhole") bootstrap over roots = WLS with weights k_r(i) * k_r(j)
rng = np.random.default_rng(20261011)
G = int(root.max() + 1)
bb = []
for _ in range(2000):
    kk = np.bincount(rng.integers(0, G, G), minlength=G).astype(float)
    w = kk[root[I]] * kk[root[J]]
    if w[X[:, 1] == 1].sum() == 0:
        continue
    bb.append(V.ols(X, y, w)[k])
bb = np.array(bb)
OUT["vertex_bootstrap_root"] = {"B": int(len(bb)), "percentile_ci": [float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5))],
                                "sd": float(bb.std(ddof=1))}
print(f"    root vertex-bootstrap (B={len(bb)}): percentile CI [{100*np.percentile(bb,2.5):.1f}, {100*np.percentile(bb,97.5):.1f}], sd {100*bb.std(ddof=1):.2f} pts")

# ---------------------------------------------------------------- 5. per-root coefficients
sr_root = {g: ((root[I] == g) & (root[J] == g)) for g in np.unique(root)}
multi_roots = [g for g, m in sr_root.items() if m.sum() > 0]
cols = [sr_root[g].astype(float) for g in multi_roots]
Z = np.column_stack([X[:, :1]] + cols + [X[:, 2:]])
bz = V.ols(Z, y)
sez = V.dyadic_se(Z, y, bz, I, J, f["n"])
est = bz[1:1 + len(cols)]; s2 = sez[1:1 + len(cols)] ** 2
npr = np.array([int(c.sum()) for c in cols])
okr = (npr >= 10) & (s2 > 0)
w = 1 / s2[okr]; e = est[okr]; fe = (w * e).sum() / w.sum(); Q = (w * (e - fe) ** 2).sum(); kq = okr.sum()
tau2 = max(0.0, (Q - (kq - 1)) / (w.sum() - (w ** 2).sum() / w.sum())); wr = 1 / (s2[okr] + tau2)
re = (wr * e).sum() / wr.sum(); re_se = np.sqrt(1 / wr.sum())
OUT["per_root"] = {"roots_with_same_root_pairs": len(multi_roots), "unweighted_mean": float(est.mean()),
                   "unweighted_median": float(np.median(est)), "share_positive": float((est > 0).mean()),
                   "roots_ge10_pairs": int(okr.sum()), "dl_pooled": float(re), "dl_ci": [float(re - V.Z * re_se), float(re + V.Z * re_se)],
                   "tau": float(np.sqrt(tau2)), "mean_roots_lt10_pairs": float(est[npr < 10].mean()),
                   "pairs_in_roots_lt10": int(npr[npr < 10].sum()), "roots_lt10": int((npr < 10).sum())}
print(f"[5] per-root: {len(multi_roots)} roots; unweighted mean {100*est.mean():.1f} (median {100*np.median(est):.1f}); DL pooled over {okr.sum()} roots (>=10 pairs) {100*re:.1f} "
      f"[{100*(re-V.Z*re_se):.1f}, {100*(re+V.Z*re_se):.1f}], tau {100*np.sqrt(tau2):.1f}; {int((npr<10).sum())} roots with <10 pairs hold {int(npr[npr<10].sum())} pairs, their mean coef {100*est[npr<10].mean():.1f}")

# ---------------------------------------------------------------- 6. estimator variants
bw = V.ols(X, y, both.astype(float))
OUT["wls_joint_wrong"] = float(bw[k])
g0 = V.NAMES.index("gap0")
OUT["equivalence_bound_90"] = {"gap0_estimate": float(b[g0]), "jackknife_se": float(se_jk[g0]),
                               "interval90": [float(b[g0] - 1.6449 * se_jk[g0]), float(b[g0] + 1.6449 * se_jk[g0])]}
print(f"[6] WLS by joint-wrong items: shared-root {100*bw[k]:.2f}; same-month 90% jackknife interval "
      f"[{100*OUT['equivalence_bound_90']['interval90'][0]:.2f}, {100*OUT['equivalence_bound_90']['interval90'][1]:.2f}]")
Path(V.OUTD / "independent_checks.json").write_text(json.dumps(OUT, indent=1, default=float))
