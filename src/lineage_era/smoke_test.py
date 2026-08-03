"""Smoke test: validate the Phase 1 estimator stack on tiny synthetic data.

Checks three claims that the implementation plan depends on:

  1. statsmodels MixedLM fits a CROSSED two-way variance-components model
     (family + era) using a single group + ``vc_formula``, and recovers known
     sigma2_L, sigma2_E and scale (= sigma2_U at the trait level) from
     balanced crossed data.
  2. ``profile_re(..., vtype="vc")`` returns finite profile-likelihood CIs
     for the variance components that contain the generating values.
  3. ``BinomialBayesMixedGLM`` (Laplace) fits a crossed binomial mixed model
     and exposes the variance-component posterior estimates.

Run from the repository root:
    python src/lineage_era/smoke_test.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RNG = np.random.default_rng(0)


def fit_crossed_vcomp(df: pd.DataFrame) -> dict:
    """Fit a crossed family + era variance-components model to a trait column.

    One trait observation per (family, era) cell row; the 'model-level'
    uniqueness (sigma2_U) is absorbed into the residual scale, which is the
    trait-level DGP used in D1/D2.
    """
    model = smf.mixedlm(
        "trait ~ 1",
        df,
        groups=np.zeros(len(df)),
        vc_formula={
            "family": "0 + C(family)",
            "era": "0 + C(era)",
        },
    )
    return model.fit(reml=True)


def main() -> None:
    # --- Check 1: crossed VC recovery with MixedLM + vc_formula ------------
    F, E, K = 8, 10, 3
    s2_L, s2_E, s2_U = 1.0, 0.5, 0.8

    alpha = RNG.normal(0.0, np.sqrt(s2_L), F)
    beta = RNG.normal(0.0, np.sqrt(s2_E), E)

    fam = np.repeat(np.arange(F), E * K)
    era = np.tile(np.repeat(np.arange(E), K), F)
    trait = np.array(
        [alpha[f] + beta[e] + RNG.normal(0.0, np.sqrt(s2_U)) for f, e in zip(fam, era)]
    )
    df = pd.DataFrame({"trait": trait, "family": fam, "era": era})

    res = fit_crossed_vcomp(df)
    est = {
        "family": float(res.params["family Var"]),
        "era": float(res.params["era Var"]),
    }
    scale = float(res.scale)

    print("MixedLM crossed VC fit")
    print("  truth:    sigma2_L=%.2f sigma2_E=%.2f scale(=sigma2_U)=%.2f" % (s2_L, s2_E, s2_U))
    print("  est:      family=%.3f era=%.3f scale=%.3f" % (est["family"], est["era"], scale))
    print("  converged=%s" % res.converged)

    assert res.converged, "fit did not converge"
    assert 0.1 < est["family"] < 2.5, "family VC badly off"
    assert 0.05 < est["era"] < 1.5, "era VC badly off"
    assert 0.3 < scale < 2.0, "scale badly off"

    # --- Check 2: profile likelihood CIs on the variance components -------
    from scipy.stats import chi2

    cutoff = chi2.ppf(0.95, 1) / 2.0
    intervals = {}
    for name in ["family", "era"]:
        prof = res.profile_re(re_ix=name, vtype="vc", dist_low=0.01, dist_high=0.99)
        values, llf = prof[:, 0], prof[:, 1]
        llf_max = llf.max()
        mask = llf >= (llf_max - cutoff)
        lb, ub = float(values[mask].min()), float(values[mask].max())
        intervals[name] = (lb, ub)
        truth = {"family": s2_L, "era": s2_E}[name]
        print("  profile CI %-6s (%.3f, %.3f) truth=%.2f inside=%s"
              % (name, lb, ub, truth, lb < truth < ub))
        assert np.isfinite(lb) and np.isfinite(ub)
        assert lb < truth < ub, "profile CI misses truth"

    # --- Check 3: BinomialBayesMixedGLM (Laplace) at item level ------------
    # endog must be item-level 0/1; exog_vc columns are concatenated with an
    # integer `ident` flagging which columns carry random effects. The random
    # effect group standard deviations are s_j = exp(vcp_j), so the variance
    # components are sigma2_j = exp(2 * vcp_j).
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    I = 50
    N = F * E * K * I
    fam_i = np.repeat(fam, I)
    era_i = np.repeat(era, I)
    model_i = np.repeat(np.arange(F * E * K), I)
    fam_alpha = RNG.normal(0.0, 0.8, F)
    era_beta = RNG.normal(0.0, 0.5, E)
    mod_u = RNG.normal(0.0, 0.7, F * E * K)
    y = np.array([
        1 if 0.3 + fam_alpha[f] + era_beta[e] + mod_u[m] + RNG.normal(0.0, 1.0) > 0 else 0
        for f, e, m in zip(fam_i, era_i, model_i)
    ])
    d_f = (fam_i[:, None] == np.arange(F)).astype(float)
    d_e = (era_i[:, None] == np.arange(E)).astype(float)
    d_m = (model_i[:, None] == np.arange(F * E * K)).astype(float)
    exog_vc = np.hstack([d_f, d_e, d_m])
    ident = np.concatenate([
        np.zeros(F, dtype=int),
        np.ones(E, dtype=int),
        2 * np.ones(F * E * K, dtype=int),
    ])

    glm = BinomialBayesMixedGLM(y, np.ones((N, 1)), exog_vc, ident)
    mdf = glm.fit_map(method="BFGS")
    s2_glm = np.exp(2.0 * mdf.vcp_mean)
    print("BinomialBayesMixedGLM (Laplace) item-level fit ok")
    print("  vcp groups=%d sigma2=%s" % (len(s2_glm), np.round(s2_glm, 3)))
    assert len(s2_glm) == 3, "expected one variance component per ident group"
    assert np.all(np.isfinite(s2_glm)) and np.all(s2_glm >= 0), "GLMM variance components not finite"

    print("SMOKE OK")


if __name__ == "__main__":
    main()
