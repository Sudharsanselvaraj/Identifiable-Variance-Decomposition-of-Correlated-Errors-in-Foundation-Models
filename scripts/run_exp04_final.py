#!/usr/bin/env python3
"""Exp04: reproduce every reported number from committed code + frozen data,
and run the inference / outcome audits requested before the manuscript rewrite.

Writes only to results/exp04_final/ and compares against the committed
outputs in results/exp04_analysis/ (commit 679c5b7).

Sections
  A  integrity: frozen-sample hashes; answer files re-validated
  B  model flow: 6,896 leaderboard models -> rosters -> samples -> analysed
  C  the 12 pre-registered analyses, reproduced and diffed
  D  inference audit: model-dyadic (pre-registered), root-dyadic and
     delete-one-root jackknife SEs, 95% CIs and p-values
  E  outcome audit: jointly-wrong denominators; WLS by denominator; pairs with
     >= 1000 jointly-wrong items; phi of error indicators (pre-registered
     secondary); agreement in excess of position-based chance (exploratory)
  F  exploratory E1/E2 reproduced and diffed
  G  figures for the manuscript

Usage (repo root): python3 scripts/run_exp04_final.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lineage_era.ollb import analysis as A  # noqa: E402
from lineage_era.ollb.pair_gate import design, month_index, ols_twoway  # noqa: E402

OUT = ROOT / "results" / "exp04_final"
COMMITTED = ROOT / "results" / "exp04_analysis"
FROZEN = ROOT / "datasets" / "ollb" / "frozen"
TERMS = ["same_root", "gap0", "gap1_2", "gap3_5", "gap6_11"]
PREREG = [  # (population, strict, position, min_acc)
    (p, s, pos, m) for p in ("primary", "expanded")
    for (s, pos, m) in [(False, False, None), (True, False, None),
                        (False, True, None), (False, False, 0.30),
                        (False, True, 0.30), (True, True, 0.30)]]


def ci(est, se):
    z = est / se
    return est - 1.96 * se, est + 1.96 * se, 2 * norm.sf(abs(z))


# ------------------------------------------------------------------ A
def integrity() -> dict:
    text = (ROOT / "results/exp04_rosters/comparison.md").read_text()
    want = dict(re.findall(r"- `([\w]+)\.csv`: `([0-9a-f]{64})`", text))
    got = {k: hashlib.sha256((FROZEN / f"{k}.csv").read_bytes()).hexdigest()
           for k in want}
    return {"hashes_match": got == want, "hashes": got}


# ------------------------------------------------------------------ B
def model_flow() -> pd.DataFrame:
    roster = pd.read_csv(ROOT / "datasets/ollb/v1_roster.csv")
    val = pd.read_csv(ROOT / "results/exp04_validation/per_model.csv")
    ok = set(val.model[val.category == "validated"])
    rows = [("v1 leaderboard models (contents table, de-duplicated)", len(roster), len(roster))]
    for col, label in [("eligible_primary", "primary"), ("eligible_expanded", "expanded")]:
        e = roster[roster[col] & roster.created_month.notna()]
        rows.append((f"eligible ({label} lineage rules, dated)", None, None))
        rows[-1] = rows[-1][:1] + ((len(e), None) if label == "primary" else (None, len(e)))
    p = pd.read_csv(FROZEN / "primary_sample_cap40.csv")
    x = pd.read_csv(FROZEN / "expanded_sample_cap40.csv")
    rows += [("frozen download sample (cap 40 per root)", len(p), len(x)),
             ("validated answers (analysed)", int(p.model.isin(ok).sum()),
              int(x.model.isin(ok).sum())),
             ("  of which root verified pretrained (strict)",
              int((p.model.isin(ok) & p.root_verified).sum()),
              int((x.model.isin(ok) & x.root_verified).sum()))]
    flow = pd.DataFrame(rows, columns=["stage", "primary", "expanded"])
    excl = []
    for name, s in [("primary", p), ("expanded", x)]:
        v = val.set_index("model").loc[s.model]
        excl.append(v.category.value_counts().rename(name))
    return flow, pd.concat(excl, axis=1).fillna(0).astype(int)


# ------------------------------------------------------------------ helpers
def prepared(pop_name: str, strict=False, min_acc=None):
    pop, _ = A.load_population(pop_name, strict)
    pred, gold, _ = A.choice_matrix(pop.model)
    acc = (pred == gold[None, :]).mean(1)
    if min_acc is not None:
        k = acc >= min_acc
        pop, pred, acc = pop[k].reset_index(drop=True), pred[k], acc[k]
    rid = pd.factorize(pop.root)[0]
    mon = month_index(pop.created_month)
    i, j, y, nb = A.pair_outcomes(pred, gold)
    X, names = design(i, j, rid, mon, acc)
    return dict(pop=pop, pred=pred, gold=gold, acc=acc, rid=rid, i=i, j=j,
                y=y, nb=nb, X=X, names=names)


def jackknife_roots(X, y, rid, i, j):
    """Delete-one-root jackknife over roots (drops every pair touching it)."""
    G = rid.max() + 1
    XtX, Xty = X.T @ X, X.T @ y
    # per-root contributions of the pairs touching that root
    betas = []
    for g in range(G):
        m = (rid[i] == g) | (rid[j] == g)
        Xg, yg = X[m], y[m]
        betas.append(np.linalg.solve(XtX - Xg.T @ Xg, Xty - Xg.T @ yg))
    B = np.array(betas)
    return np.sqrt((G - 1) / G * ((B - B.mean(0)) ** 2).sum(0))


# ------------------------------------------------------------------ D
def inference_audit() -> pd.DataFrame:
    rows = []
    for pop_name in ("primary", "expanded"):
        for min_acc in (None, 0.30):
            d = prepared(pop_name, min_acc=min_acc)
            X, y, i, j, rid = d["X"], d["y"], d["i"], d["j"], d["rid"]
            b, se_m = ols_twoway(X, y, i, j, len(d["pop"]))
            _, se_r = ols_twoway(X, y, rid[i], rid[j], rid.max() + 1)
            se_jk = jackknife_roots(X, y, rid, i, j)
            for t in ("same_root", "gap0"):
                k = d["names"].index(t)
                for label, se in [("model-dyadic (pre-registered)", se_m[k]),
                                  ("root-dyadic", se_r[k]),
                                  ("delete-one-root jackknife", se_jk[k])]:
                    lo, hi, p = ci(b[k], se)
                    rows.append({"population": pop_name + ("_S2" if min_acc else ""),
                                 "term": t, "inference": label, "estimate": b[k],
                                 "se": se, "ci_low": lo, "ci_high": hi, "p": p,
                                 "models": len(d["pop"]), "roots": int(rid.max() + 1)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ E
def outcome_audit() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, den = [], []
    for pop_name in ("primary", "expanded"):
        d = prepared(pop_name)
        X, y, i, j, nb, names = d["X"], d["y"], d["i"], d["j"], d["nb"], d["names"]
        N = len(d["pop"])
        den.append({"population": pop_name, "pairs": len(y),
                    "jointly_wrong_min": int(nb.min()),
                    "jointly_wrong_p05": int(np.percentile(nb, 5)),
                    "jointly_wrong_median": int(np.median(nb)),
                    "jointly_wrong_max": int(nb.max()),
                    "pairs_lt_1000": int((nb < 1000).sum())})
        variants = {}
        variants["primary outcome, OLS (pre-registered)"] = (X, y, None)
        variants["WLS, weight = jointly-wrong items"] = (X, y, nb)
        keep = nb >= 1000
        variants["pairs with >= 1000 jointly-wrong items"] = (X[keep], y[keep], None, keep)
        # phi of error indicators (pre-registered secondary outcome)
        W = (d["pred"] != d["gold"][None, :]).astype(np.float64)
        W -= W.mean(1, keepdims=True)
        sd = np.sqrt((W ** 2).mean(1))
        phi = (W @ W.T) / W.shape[1] / np.outer(sd, sd)
        variants["phi of error indicators (secondary)"] = (X, phi[i, j], None)
        # excess over position-based chance (exploratory)
        pr = d["pred"]
        wrong = pr != d["gold"][None, :]
        q = np.stack([((pr == o) & wrong).sum(1) / wrong.sum(1) for o in range(4)], 1)
        variants["agreement minus position-based chance (exploratory)"] = (
            X, y - (q[i] * q[j]).sum(1), None)
        for label, v in variants.items():
            Xv, yv, w = v[0], v[1], v[2]
            iv, jv = (i[v[3]], j[v[3]]) if len(v) == 4 else (i, j)
            if w is not None:
                sw = np.sqrt(w / w.mean())
                Xv, yv = Xv * sw[:, None], yv * sw
            b, se = ols_twoway(Xv, yv, iv, jv, N)
            for t in ("same_root", "gap0"):
                k = names.index(t)
                lo, hi, p = ci(b[k], se[k])
                rows.append({"population": pop_name, "variant": label, "term": t,
                             "estimate": b[k], "se": se[k], "ci_low": lo,
                             "ci_high": hi, "p": p, "pairs": len(yv)})
    return pd.DataFrame(rows), pd.DataFrame(den)


# ------------------------------------------------------------------ C / F
def reproduce_prereg() -> pd.DataFrame:
    rows = []
    for pop_name, strict, pos, m in PREREG:
        res = A.run(pop_name, strict, pos, m, out_root=OUT / "prereg")
        label = res["summary"]["population"]
        new = res["coefficients"].set_index("term")
        old = pd.read_csv(COMMITTED / label / "coefficients.csv").set_index("term")
        for t in TERMS:
            lo, hi, p = ci(new.loc[t, "estimate"], new.loc[t, "se"])
            rows.append({"analysis": label, "term": t,
                         "estimate": new.loc[t, "estimate"], "se": new.loc[t, "se"],
                         "ci_low": lo, "ci_high": hi, "p": p,
                         "models": res["summary"]["models_analysed"],
                         "pairs": res["summary"]["pairs"],
                         "max_abs_diff_vs_committed": float(
                             (new[["estimate", "se"]] - old[["estimate", "se"]])
                             .abs().to_numpy().max())})
    return pd.DataFrame(rows)


def reproduce_exploratory() -> pd.DataFrame:
    rows = []
    for pop_name in ("primary", "expanded"):
        for min_acc in (None, 0.30):
            d = prepared(pop_name, min_acc=min_acc)
            pop, i, j, rid = d["pop"], d["i"], d["j"], d["rid"]
            tv = A.position_tv(d["pred"], i, j)
            X = np.column_stack([d["X"], tv])
            b, se_m = ols_twoway(X, d["y"], i, j, len(pop))
            b2, se_r = ols_twoway(X, d["y"], rid[i], rid[j], rid.max() + 1)
            params = pd.to_numeric(pop.params_b, errors="coerce")
            lp = np.log(params.fillna(params.median()).clip(lower=0.01).to_numpy())
            arch = pd.factorize(pop.architecture.fillna("?"))[0]
            X3 = np.column_stack([X, np.abs(lp[i] - lp[j]), lp[i] + lp[j],
                                  (arch[i] == arch[j]).astype(float)])
            b3, se3 = ols_twoway(X3, d["y"], i, j, len(pop))
            n, g = d["names"].index("same_root"), d["names"].index("gap0")
            rows.append({"population": pop_name + ("_S2" if min_acc else ""),
                         "models": len(pop),
                         "same_root (model-cl)": f"{b[n]:+.4f} ({se_m[n]:.4f})",
                         "same_root (root-cl)": f"{b2[n]:+.4f} ({se_r[n]:.4f})",
                         "gap0 (root-cl)": f"{b2[g]:+.4f} ({se_r[g]:.4f})",
                         "same_root +size/arch": f"{b3[n]:+.4f} ({se3[n]:.4f})",
                         "gap0 +size/arch": f"{b3[g]:+.4f} ({se3[g]:.4f})",
                         "same_arch": f"{b3[-1]:+.4f} ({se3[-1]:.4f})"})
    new = pd.DataFrame(rows)
    old = pd.read_csv(COMMITTED / "exploratory_E1_E2.csv")
    new["matches_committed"] = (new.astype(str).values == old.astype(str).values).all(1)
    return new


# ------------------------------------------------------------------ G
def figures(prereg: pd.DataFrame) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figdir = ROOT / "paper" / "figures"
    made = []
    # Fig: forest plot of same_root and gap0 across the 12 analyses
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    order = list(dict.fromkeys(prereg.analysis))
    for ax, t, title in zip(axes, ("same_root", "gap0"),
                            ("Shared lineage root", "Same release month (vs. 12+)")):
        d = prereg[prereg.term == t].set_index("analysis").loc[order]
        yy = np.arange(len(order))[::-1]
        ax.errorbar(d.estimate, yy, xerr=1.96 * d.se, fmt="o", color="#1f4e79",
                    ms=4, capsize=2, lw=1)
        ax.axvline(0, color="0.5", lw=0.8, ls="--")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Δ P(same wrong | both wrong)", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_yticks(np.arange(len(order))[::-1])
    axes[0].set_yticklabels([o.replace("_", " ") for o in order], fontsize=7)
    fig.tight_layout()
    p = figdir / "exp04_forest.pdf"
    fig.savefig(p, metadata={"CreationDate": None}); plt.close(fig); made.append(p.name)

    # Fig: raw mean agreement by month gap, same vs different root (primary)
    d = prepared("primary")
    gap = np.abs(month_index(d["pop"].created_month)[d["i"]]
                 - month_index(d["pop"].created_month)[d["j"]])
    same = d["rid"][d["i"]] == d["rid"][d["j"]]
    bins = [0, 1, 3, 6, 12, 100]
    lab = ["0", "1–2", "3–5", "6–11", "12+"]
    b = np.digitize(gap, bins[1:])
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    MIN_PAIRS = 20   # bins with fewer pairs are not plotted (e.g. 1 same-root pair at 12+)
    for flag, name, c in [(True, "same root", "#b2182b"), (False, "different root", "#2166ac")]:
        cnt = [int(((b == k) & (same == flag)).sum()) for k in range(5)]
        m = [d["y"][(b == k) & (same == flag)].mean() if cnt[k] >= MIN_PAIRS else np.nan
             for k in range(5)]
        ax.plot(lab, m, "o-", label=name, color=c, ms=4)
        for k in range(5):
            if cnt[k] >= MIN_PAIRS:
                ax.annotate(f"n={cnt[k]:,}", (k, m[k]), textcoords="offset points",
                            xytext=(0, 5 if flag else -10), ha="center", fontsize=5.5,
                            color=c)
    ax.margins(x=0.08, y=0.12)
    ax.set_xlabel("Release-month gap", fontsize=8)
    ax.set_ylabel("Mean P(same wrong | both wrong)", fontsize=8)
    ax.tick_params(labelsize=7); ax.legend(fontsize=7, frameon=False, loc="center right")
    fig.tight_layout()
    p = figdir / "exp04_agreement_by_gap.pdf"
    fig.savefig(p, metadata={"CreationDate": None}); plt.close(fig); made.append(p.name)

    # Fig: precision of per-model family/era shares vs number of families
    sc = pd.read_csv(ROOT / "results/precision_gate/family_scaling.csv")
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for (E, M), g in sc.groupby(["E", "M"]):
        ax.plot(g.F, g[["worst_family", "worst_era"]].max(1), "o-", ms=3,
                label=f"{E} eras, {M} models/family")
    ax.axhline(0.10, color="0.5", ls="--", lw=0.8)
    ax.set_xlabel("Families (lineage levels)", fontsize=8)
    ax.set_ylabel("Worst-case share RMSE", fontsize=8)
    ax.tick_params(labelsize=7); ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    p = figdir / "precision_scaling.pdf"
    fig.savefig(p, metadata={"CreationDate": None}); plt.close(fig); made.append(p.name)
    return made


# ------------------------------------------------------------------ H
def extra_checks() -> pd.DataFrame:
    """Exploratory: no accuracy controls; cap-15 subset (a subset of cap 40
    under the same seeded order); same-root pair counts by gap bin."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_pair_gate import population, sample

    rows = []
    d = prepared("primary")
    keep = [k for k, n in enumerate(d["names"]) if not n.startswith("acc")]
    b, se = ols_twoway(d["X"][:, keep], d["y"], d["i"], d["j"], len(d["pop"]))
    names = [d["names"][k] for k in keep]
    for t in ("same_root", "gap0"):
        k = names.index(t)
        rows.append({"check": "no accuracy controls", "term": t,
                     "estimate": b[k], "se": se[k], "models": len(d["pop"])})
    roster = pd.read_csv(ROOT / "datasets/ollb/v1_roster.csv")
    c15 = set(sample(population(roster, "primary"), 100000, 15).model)
    c40 = set(sample(population(roster, "primary"), 100000, 40).model)
    assert c15 <= c40
    pop, _ = A.load_population("primary", False)
    p = pop[pop.model.isin(c15)].reset_index(drop=True)
    pred, gold, _ = A.choice_matrix(p.model)
    acc = (pred == gold[None, :]).mean(1)
    rid = pd.factorize(p.root)[0]
    i, j, y, _ = A.pair_outcomes(pred, gold)
    X, nm = design(i, j, rid, month_index(p.created_month), acc)
    b, se = ols_twoway(X, y, i, j, len(p))
    jk = jackknife_roots(X, y, rid, i, j)
    for t in ("same_root", "gap0"):
        k = nm.index(t)
        rows.append({"check": "cap-15 subset", "term": t, "estimate": b[k],
                     "se": se[k], "se_jackknife": jk[k], "models": len(p)})
    gap = np.abs(month_index(d["pop"].created_month)[d["i"]]
                 - month_index(d["pop"].created_month)[d["j"]])
    same = d["rid"][d["i"]] == d["rid"][d["j"]]
    bins = np.digitize(gap, [1, 3, 6, 12])
    for k, lab in enumerate(["0", "1-2", "3-5", "6-11", "12+"]):
        rows.append({"check": "same-root pairs by gap bin", "term": lab,
                     "estimate": int(((bins == k) & same).sum()), "models": len(d["pop"])})
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"A_integrity": integrity()}
    flow, excl = model_flow()
    flow.to_csv(OUT / "model_flow.csv", index=False)
    excl.to_csv(OUT / "sample_exclusions.csv")
    prereg = reproduce_prereg()
    prereg.to_csv(OUT / "prereg_12.csv", index=False)
    report["C_prereg_max_abs_diff"] = float(prereg.max_abs_diff_vs_committed.max())
    inf = inference_audit()
    inf.to_csv(OUT / "inference_audit.csv", index=False)
    out, den = outcome_audit()
    out.to_csv(OUT / "outcome_audit.csv", index=False)
    den.to_csv(OUT / "denominators.csv", index=False)
    expl = reproduce_exploratory()
    expl.to_csv(OUT / "exploratory_E1_E2.csv", index=False)
    report["F_exploratory_all_match"] = bool(expl.matches_committed.all())
    report["G_figures"] = figures(prereg)
    extra_checks().to_csv(OUT / "extra_checks.csv", index=False)
    (OUT / "report.json").write_text(json.dumps(report, indent=1))
    pd.set_option("display.width", 220)
    print(json.dumps(report, indent=1))
    print(flow.to_string(index=False)); print(excl.to_string())
    print(den.to_string(index=False))
    print(inf.round(4).to_string(index=False))
    print(out.round(4).to_string(index=False))
    ok = report["A_integrity"]["hashes_match"] and report["C_prereg_max_abs_diff"] < 1e-12 \
        and report["F_exploratory_all_match"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
