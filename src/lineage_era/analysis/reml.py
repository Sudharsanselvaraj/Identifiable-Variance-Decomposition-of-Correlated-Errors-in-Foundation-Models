"""The REML engine and the θ_P / θ_M model layer (analysis/reml.py).

Estimators (Phase 1-validated):
Path 1 (LPM-REML): crossed family + era variance-components model.

IMPORTANT VALIDATION FINDING (2026-08-03, see Research_Decision_Log):
statsmodels ``MixedLM`` with a single group + ``vc_formula`` does NOT maximize
the REML objective for crossed variance components. Cross-checked against a
direct brute-force REML maximization and two-way ANOVA (method of moments) on
the same datasets: ANOVA == brute-force REML exactly, while MixedLM reported
inflated components (e.g. family 0.61 vs 0.40, era 0.48 vs 0.31) that do not
maximize even its own REML objective. All optimizers/tolerances agree, so this
is a structural issue with the statsmodels path, not optimizer noise.

Consequently Path 1 is implemented HERE as a direct REML maximizer using the
standard restricted log-likelihood, accelerated with the Woodbury identity
(V = scale*I + C*diag(vcomp)*C', C low-rank), and verified to agree with
two-way ANOVA method of moments on balanced crossed data.

Path 2 (Binomial GLMM): item-level Bayesian logistic mixed model via
``BinomialBayesMixedGLM`` (Laplace / MAP). Used by the liability test as the
gold-standard reference.

Share CIs (LPM path): asymptotic normal approximation on the log-variances
using the numerical Hessian of the restricted log-likelihood, then Monte-Carlo
percentiles over the simplex. Coverage is validated empirically in the
simulation (a Phase 1 deliverable, not assumed).

Model layer (formerly ``phase2_model.py``): θ_P variance partition + θ_M
mechanism tables (era trend, dense-cell contrasts, chain slopes).
"""
from __future__ import annotations

import argparse
import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import chi2

from ..occupancy import DOCUMENTED_STATS, QUARTERS, VERIFIED_EDGES

PROFILE_CUTOFF = chi2.ppf(0.95, 1) / 2.0  # 1.9207


def _psd_inverse(H: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """Symmetrize and invert a (near-)PSD Hessian robustly.

    Sparse/aliased designs yield near-singular Hessians; the eigen-clip turns
    the pseudoinverse into the closest PSD inverse so SEs stay finite and the
    flat directions are reported as inflated (inf) rather than crashing.
    """
    H = (H + H.T) / 2.0
    w, V = np.linalg.eigh(H)
    w = np.clip(w, eps, None)
    return (V * (1.0 / w)) @ V.T


@dataclass
class FitResult:
    converged: bool = False
    n_convergence_warnings: int = 0
    s2: dict = field(default_factory=dict)          # {family, era, unique}
    se: dict = field(default_factory=dict)          # SE on the s2 scale
    cov_log: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    hessian: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    blups: dict = field(default_factory=dict)       # {family: np.ndarray, era: np.ndarray}
    llf: float = float("nan")
    df_log: dict = field(default_factory=dict)      # finite-sample df per component
    solver: object = None

    @property
    def shares(self) -> dict:
        total = sum(self.s2.values())
        return {k: v / total for k, v in self.s2.items()} if total > 0 else {}


# ---------------------------------------------------------------- REML core
class CrossedREML:
    """Restricted-likelihood maximizer for crossed variance-component models.

    Model: y = X beta + sum_j Z_j u_j + e, with u_j ~ N(0, s2_j * I),
    e ~ N(0, s2_u * I), X = column of ones. Optimization is on
    theta = [log s2_1, ..., log s2_k, log s2_u].
    """

    def __init__(self, y: np.ndarray, group_designs: list[np.ndarray]):
        y = np.asarray(y, dtype=float)
        self.n = len(y)
        self.k = len(group_designs)
        self.levels = [d.shape[1] for d in group_designs]
        self.C = np.hstack(group_designs) if group_designs else np.zeros((self.n, 0))
        self.kv = sum(self.levels)
        self.CtC = self.C.T @ self.C if self.kv else np.zeros((0, 0))
        self.CtX = self.C.T @ np.ones(self.n) if self.kv else np.zeros(0)
        self.CtY = self.C.T @ y if self.kv else np.zeros(0)
        self.XtX = float(self.n)
        self.XtY = float(y.sum())
        self.YtY = float(y @ y)

    def _objective(self, theta: np.ndarray) -> float:
        theta = np.clip(theta, -30, 30)
        sU = math.exp(theta[-1])
        Ddiag = np.repeat(np.exp(theta[:-1]), self.levels)
        if not self.kv:
            Vinv_y = self.YtY / sU
            XtViX = self.n / sU
            logdet = self.n * math.log(sU)
        else:
            G = np.diag(1.0 / Ddiag) + self.CtC / sU
            try:
                Ginv = np.linalg.inv(G)
            except np.linalg.LinAlgError:
                return 1e12
            gCtY = Ginv @ self.CtY
            gCtX = Ginv @ self.CtX
            YtViY = self.YtY / sU - (gCtY @ self.CtY) / sU**2
            XtViX = self.XtX / sU - (gCtX @ self.CtX) / sU**2
            XtViY = self.XtY / sU - (gCtX @ self.CtY) / sU**2
            logdet = (self.n * math.log(sU)
                      + float(np.sum(self.levels * theta[:-1]))
                      + float(np.linalg.slogdet(G)[1]))
            Vinv_y = YtViY
        if XtViX <= 0:
            return 1e12
        ytPy = Vinv_y - XtViY**2 / XtViX
        return 0.5 * (logdet + math.log(XtViX) + ytPy)

    def fit(self, method: str = "Nelder-Mead") -> tuple[np.ndarray, object, bool]:
        """Maximize REML over theta; returns (theta_hat, optim, converged)."""
        start = np.zeros(self.k + 1)
        for trial in [start, start - 0.5, start + 0.5, np.zeros(self.k + 1) + 0.3]:
            opt = minimize(self._objective, trial, method=method,
                           options={"maxiter": 800, "xatol": 1e-5, "fatol": 1e-7})
            if opt.success:
                break
        theta = np.clip(opt.x, -20, 20)
        return theta, opt, bool(opt.success)

    def hessian(self, theta: np.ndarray, eps: float = 1e-4) -> np.ndarray:
        """Numerical Hessian of the restricted log-likelihood at theta."""
        p = len(theta)
        H = np.zeros((p, p))
        for i in range(p):
            for j in range(p):
                ei, ej = np.zeros(p), np.zeros(p)
                ei[i], ej[j] = eps, eps
                fpp = self._objective(theta + ei + ej)
                fmm = self._objective(theta - ei - ej)
                fpm = self._objective(theta + ei - ej)
                fmp = self._objective(theta - ei + ej)
                H[i, j] = (fpp - fpm - fmp + fmm) / (4 * eps**2)
        return H

    def blups(self, theta: np.ndarray) -> dict:
        """Best linear unbiased predictions of the group effects (per group)."""
        sU = math.exp(theta[-1])
        Ddiag = np.repeat(np.exp(theta[:-1]), self.levels)
        if not self.kv:
            return {}
        G = np.diag(1.0 / Ddiag) + self.CtC / sU
        Ginv = np.linalg.inv(G)
        # Residuals for the fixed part: r = y - X beta_hat, beta_hat = (X'V^-1X)^-1 X'V^-1 y
        gCtX = Ginv @ self.CtX
        XtViX = self.XtX / sU - (gCtX @ self.CtX) / sU**2
        XtViY = self.XtY / sU - (gCtX @ self.CtY) / sU**2
        beta_hat = XtViY / XtViX
        # C' V^-1 (y - X beta_hat)
        gCtY = Ginv @ self.CtY
        CtVinv_r = self.CtY / sU - (self.CtC @ Ginv @ self.CtY) / sU**2 \
            - beta_hat * (self.CtX / sU - (self.CtC @ gCtX) / sU**2)
        out = {}
        offset = 0
        for j, lev in enumerate(self.levels):
            s2 = math.exp(theta[j])
            out[j] = s2 * CtVinv_r[offset:offset + lev]
            offset += lev
        return out


# -------------------------------------------------------------- interface
def fit_lpm_vcomp(df, reml: bool = True) -> FitResult:
    """Fit trait ~ vc{family, era} via the direct REML maximizer.

    If ``df`` has a ``trait`` column it is used directly; otherwise the first
    numeric column is treated as the response (for per-model proportion rows).
    """
    if "trait" in df.columns:
        y = df["trait"].to_numpy(dtype=float)
    else:
        y = df.select_dtypes(include=[np.number]).iloc[:, 0].to_numpy(dtype=float)
    A = (df["family"].to_numpy()[:, None] == np.unique(df["family"])).astype(float)
    B = (df["era"].to_numpy()[:, None] == np.unique(df["era"])).astype(float)

    solver = CrossedREML(y, [A, B])
    theta, opt, converged = solver.fit()
    s2_L, s2_E, s2_U = np.exp(theta)

    hess = solver.hessian(theta)
    cov_log = _psd_inverse(hess)
    n = len(df)
    f_lv, e_lv = A.shape[1], B.shape[1]
    se = {
        "family": s2_L * math.sqrt(max(cov_log[0, 0], 0.0)) if s2_L > 0 else float("inf"),
        "era": s2_E * math.sqrt(max(cov_log[1, 1], 0.0)) if s2_E > 0 else float("inf"),
        "unique": s2_U * math.sqrt(max(cov_log[2, 2], 0.0)) if s2_U > 0 else float("inf"),
    }
    b = solver.blups(theta)
    fam_idx = (A @ np.arange(A.shape[1])).astype(int)
    era_idx = (B @ np.arange(B.shape[1])).astype(int)
    return FitResult(
        converged=converged,
        n_convergence_warnings=0,
        s2={"family": float(s2_L), "era": float(s2_E), "unique": float(s2_U)},
        se=se,
        cov_log=cov_log,
        hessian=hess,
        blups={"family": b[0][fam_idx], "era": b[1][era_idx]},
        llf=-float(opt.fun),
        df_log={"family": f_lv - 1, "era": e_lv - 1, "unique": n - f_lv * e_lv},
        solver=solver,
    )


def fit_lpm_vcomp_cells(df, cell_col: str = "cell") -> FitResult:
    """Fit trait ~ vc{family, era, cell} (the L x E test)."""
    y = df["trait"].to_numpy(dtype=float)
    A = (df["family"].to_numpy()[:, None] == np.unique(df["family"])).astype(float)
    B = (df["era"].to_numpy()[:, None] == np.unique(df["era"])).astype(float)
    cells = np.unique(df[cell_col])
    C = (df[cell_col].to_numpy()[:, None] == cells).astype(float)

    solver = CrossedREML(y, [A, B, C])
    theta, opt, converged = solver.fit()
    s2_L, s2_E, s2_C, s2_U = np.exp(theta)
    hess = solver.hessian(theta)
    cov_log = _psd_inverse(hess)
    se_c = s2_C * math.sqrt(max(cov_log[2, 2], 0.0)) if s2_C > 0 else float("inf")
    b = solver.blups(theta)
    fam_idx = (A @ np.arange(A.shape[1])).astype(int)
    era_idx = (B @ np.arange(B.shape[1])).astype(int)
    return FitResult(
        converged=converged,
        n_convergence_warnings=0,
        s2={"family": float(s2_L), "era": float(s2_E),
            "cell": float(s2_C), "unique": float(s2_U)},
        se={"family": s2_L * math.sqrt(max(cov_log[0, 0], 0.0)),
            "era": s2_E * math.sqrt(max(cov_log[1, 1], 0.0)),
            "cell": se_c,
            "unique": s2_U * math.sqrt(max(cov_log[3, 3], 0.0))},
        cov_log=cov_log,
        hessian=hess,
        blups={"family": b[0][fam_idx], "era": b[1][era_idx]},
        llf=-float(opt.fun),
        df_log={"family": A.shape[1] - 1, "era": B.shape[1] - 1,
                "cell": C.shape[1] - 1, "unique": len(df) - C.shape[1]},
        solver=solver,
    )


def share_ci(fit: FitResult, level: float = 0.95, n_draws: int = 4000) -> dict:
    """Monte-Carlo delta CI for each share.

    Draws the log-variances jointly from a normal with the fitted REML
    covariance (``cov_log``), exponentiates, normalizes to the simplex, and
    takes percentile intervals. Empirically validated in the battery; with
    only 6 family levels (df = 5) the family-share coverage is capped below
    nominal (a documented small-sample limit of the design).
    """
    keys = list(fit.s2)
    k = len(keys)
    logs = [math.log(max(v, 1e-12)) for v in fit.s2.values()]
    if getattr(fit, "hessian", None) is not None and fit.hessian.size:
        cov = _psd_inverse(fit.hessian[:k, :k])
    else:
        cov = fit.cov_log[:k, :k]
    cov = (cov + cov.T) / 2.0
    w, V = np.linalg.eigh(cov)
    cov = (V * np.clip(w, 1e-6, None)) @ V.T
    draws = np.clip(np.random.default_rng(0).multivariate_normal(
        mean=logs, cov=cov, size=n_draws, check_valid="ignore"), -30, 30)
    exps = np.exp(draws)
    shares = exps / exps.sum(axis=1, keepdims=True)
    alpha = (1.0 - level) / 2.0
    lo, hi = alpha * 100, (1.0 - alpha) * 100
    return {
        k: (float(np.percentile(shares[:, i], lo)),
            float(np.percentile(shares[:, i], hi)))
        for i, k in enumerate(keys)
    }


def profile_flatness(fit: FitResult, vc_name: str = "family", dist: float = 0.5,
                     num: int = 25) -> float:
    """Profile drop over a +/- dist (log-scale) window around the MLE.

    < PROFILE_CUTOFF means a 95% profile CI cannot be established within the
    window — an unidentifiability signal (used in D3).
    """
    solver = fit.solver
    if solver is None:
        return float("inf")
    names = list(fit.s2)
    if vc_name not in names:
        return float("inf")
    ix = names.index(vc_name)
    theta0 = np.log(np.array([max(v, 1e-12) for v in fit.s2.values()]))
    base = solver._objective(theta0)
    values = []
    for delta in np.linspace(-dist, dist, num):
        theta = theta0.copy()
        theta[ix] += delta
        def prof_obj(t, fixed=ix, val=theta[ix]):
            t = t.copy()
            t[fixed] = val
            return solver._objective(t)
        opt = minimize(prof_obj, theta, method="Nelder-Mead",
                       options={"maxiter": 600, "xatol": 1e-3, "fatol": 1e-5})
        values.append(opt.fun)
    return float(max(values) - min(values))


def fit_glmm_binomial(y_binary: np.ndarray, fam: np.ndarray, era: np.ndarray,
                      model_id: np.ndarray) -> dict:
    """Item-level Binomial GLMM (Laplace). Returns variance components.

    One variance component per group via ``ident``. Returns
    {family, era, unique, converged}.
    """
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    n = len(y_binary)
    fam_levels = np.unique(fam)
    era_levels = np.unique(era)
    mod_levels = np.unique(model_id)
    d_f = (fam[:, None] == fam_levels).astype(float)
    d_e = (era[:, None] == era_levels).astype(float)
    d_m = (model_id[:, None] == mod_levels).astype(float)
    exog_vc = np.hstack([d_f, d_e, d_m])
    ident = np.concatenate([
        np.zeros(len(fam_levels), dtype=int),
        np.ones(len(era_levels), dtype=int),
        2 * np.ones(len(mod_levels), dtype=int),
    ])
    glm = BinomialBayesMixedGLM(y_binary, np.ones((n, 1)), exog_vc, ident)
    converged = True
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            mdf = glm.fit_map(method="BFGS")
        except Exception:  # noqa: BLE001
            mdf = None
            converged = False
        for w in caught:
            if "did not converge" in str(w.message).lower():
                converged = False
    if mdf is None:
        return {"family": float("nan"), "era": float("nan"),
                "unique": float("nan"), "converged": False}
    s2 = np.exp(2.0 * mdf.vcp_mean)
    return {"family": float(s2[0]), "era": float(s2[1]),
            "unique": float(s2[2]), "converged": converged}


# ------------------------------------------------------- θ_P / θ_M model layer
# (formerly ``phase2_model.py``; kept here so the REML engine and the model
# operations that consume it live in one module per the analysis/ layout).
QINDEX = {q: i for i, q in enumerate(QUARTERS)}


def shares_of(fit: FitResult) -> dict[str, float]:
    tot = sum(fit.s2.values())
    return {k: float(v / tot) if tot > 0 else 0.0 for k, v in fit.s2.items()}


def variance_partition(df: pd.DataFrame) -> pd.DataFrame:
    """θ_P table: per-component variance, SE, and share (+ log-delta CI)."""
    fit = fit_lpm_vcomp(df)
    sh = shares_of(fit)
    ci = share_ci(fit)
    rows = []
    for k in fit.s2:
        est, se = fit.s2[k], fit.se[k]
        lo, hi = ci.get(k, (float("nan"), float("nan")))
        rows.append({
            "component": k, "variance": est, "se": se,
            "share": sh[k], "share_lo": lo, "share_hi": hi,
        })
    return pd.DataFrame(rows), fit


def blups_by_level(df: pd.DataFrame,
                   fit: FitResult) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-level family and era BLUPs (deduped from the per-row BLUPs)."""
    fam, era = [], []
    for level, blup, col in (("family", "family_blup", "family"), ("era", "era_blup", "era")):
        out = df.assign(blup=fit.blups[level]).groupby(col)["blup"].first().reset_index()
        out.columns = [col, blup]
        (fam if level == "family" else era).append(out)
    fam[0] = fam[0].merge(df.groupby("family")["trait"].mean().reset_index(name="mean_trait"),
                          on="family")
    fam[0] = fam[0].merge(df.groupby("family").size().reset_index(name="n_models"), on="family")
    era[0] = era[0].merge(df.groupby("era")["trait"].mean().reset_index(name="mean_trait"),
                          on="era")
    era[0] = era[0].merge(df.groupby("era").size().reset_index(name="n_models"), on="era")
    return fam[0], era[0]


def theta_m_tables(df: pd.DataFrame, fit: FitResult) -> dict[str, pd.DataFrame]:
    """θ_M tables: era trend, dense-cell family contrasts, chain slopes."""
    model_eff = pd.DataFrame({
        "full_name": df["full_name"], "family": df["family"], "era": df["era"],
        "trait": df["trait"],
        "family_blup": fit.blups["family"], "era_blup": fit.blups["era"],
    })

    era_trend = df.groupby("era")["trait"].agg(["mean", "size"]).reset_index()
    era_trend.columns = ["era", "mean_trait", "n_models"]
    era_trend = era_trend.merge(
        model_eff.groupby("era")["era_blup"].first().reset_index(), on="era")
    era_trend["era_i"] = era_trend["era"].map(QINDEX)

    dense = []
    for q in DOCUMENTED_STATS["dense_cells"]:
        sub = df[df["era"] == q]
        for _, r in sub.iterrows():
            dense.append({"era": q, "family": r["family"], "full_name": r["full_name"],
                          "trait": r["trait"], "family_blup": float(
                              fit.blups["family"][sub.index.get_loc(r.name)])})
    dense_cells = pd.DataFrame(dense,
                               columns=["era", "family", "full_name", "trait",
                                        "family_blup"])

    chain = []
    for child, parent, _q in VERIFIED_EDGES:
        c = df[df["full_name"] == child]
        p = df[df["full_name"] == parent]
        if c.empty or p.empty:
            continue
        cr, pr = c.iloc[0], p.iloc[0]
        dq = QINDEX[cr["era"]] - QINDEX[pr["era"]]
        if dq <= 0:
            continue
        chain.append({
            "child": child, "parent": parent,
            "child_era": cr["era"], "parent_era": pr["era"],
            "delta_quarters": dq,
            "trait_slope_per_q": (cr["trait"] - pr["trait"]) / dq,
            "family_blup_slope_per_q": (
                fit.blups["family"][c.index[0]] - fit.blups["family"][p.index[0]]) / dq,
        })
    chain_slopes = pd.DataFrame(chain, columns=[
        "child", "parent", "child_era", "parent_era", "delta_quarters",
        "trait_slope_per_q", "family_blup_slope_per_q"])

    return {"model_effects": model_eff, "era_trend": era_trend,
            "dense_cells": dense_cells, "chain_slopes": chain_slopes}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--df", default=None,
                   help="trait table CSV; default results/phase2/trait_table.csv")
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(args.df) if args.df else out_dir / "trait_table.csv"
    if not path.exists():
        p.error(f"{path} not found (run trait assembly first)")
    df = pd.read_csv(path)
    if "era" not in df.columns:
        p.error("trait table missing 'era' column (run trait assembly)")

    vp, fit = variance_partition(df)
    vp.to_csv(out_dir / "variance_partition.csv", index=False)
    fam, era = blups_by_level(df, fit)
    fam.to_csv(out_dir / "family_effects.csv", index=False)
    era.to_csv(out_dir / "era_effects.csv", index=False)
    tm = theta_m_tables(df, fit)
    for name, table in tm.items():
        table.to_csv(out_dir / f"{name}.csv", index=False)

    print("θ_P variance partition:")
    for _, r in vp.iterrows():
        print(f"  {r['component']:7s} s2={r['variance']:.4f} "
              f"share={r['share']:.3f} [{r['share_lo']:.3f}, {r['share_hi']:.3f}]")
    print(f"  converged={fit.converged} llf={fit.llf:.2f}")
    print(f"θ_M: era_trend {len(tm['era_trend'])} eras, "
          f"dense cells {len(tm['dense_cells'])}, "
          f"chain edges {len(tm['chain_slopes'])}")
    print(f"-> {out_dir}")
    return 0
