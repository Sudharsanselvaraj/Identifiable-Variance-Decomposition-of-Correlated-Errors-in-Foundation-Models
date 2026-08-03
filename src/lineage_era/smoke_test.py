"""Smoke test: validate the Phase 1 estimator stack on tiny synthetic data.

Checks three claims the implementation plan depends on:

  1. ``estimator.fit_lpm_vcomp`` (direct crossed REML) recovers known
     sigma2_L / sigma2_E / sigma2_U from balanced crossed data and is
     consistent with two-way ANOVA (the estimator was written because
     statsmodels MixedLM with a single group + ``vc_formula`` was found NOT to
     maximize the REML objective; see Research_Decision_Log 2026-08-03).
  2. ``share_ci`` and ``profile_flatness`` produce finite, sensible outputs.
  3. ``BinomialBayesMixedGLM`` (Laplace) fits a crossed binomial mixed model
     and exposes the variance-component posterior estimates.

Run from the repository root:
    python src/lineage_era/smoke_test.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estimator

RNG = np.random.default_rng(0)


def main() -> None:
    # --- Check 1: crossed VC recovery with the direct REML solver ----------
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

    fit = estimator.fit_lpm_vcomp(df)
    est = fit.s2
    shares = fit.shares
    print("direct crossed REML fit")
    print("  truth: sigma2_L=%.2f sigma2_E=%.2f sigma2_U=%.2f" % (s2_L, s2_E, s2_U))
    print("  est:   family=%.3f era=%.3f unique=%.3f" % (est["family"], est["era"], est["unique"]))
    print("  shares: family=%.3f era=%.3f unique=%.3f converged=%s"
          % (shares["family"], shares["era"], shares["unique"], fit.converged))

    assert fit.converged, "fit did not converge"
    assert all(v > 0 for v in est.values()), "variance components must be positive"
    assert 0.1 < est["family"] < 3.5, "family VC badly off"
    assert 0.05 < est["era"] < 2.0, "era VC badly off"
    assert 0.3 < est["unique"] < 2.0, "unique VC badly off"
    assert abs(shares["family"] - 0.435) < 0.30, "family share badly off"
    assert abs(shares["era"] - 0.217) < 0.30, "era share badly off"
    assert abs(shares["unique"] - 0.348) < 0.30, "unique share badly off"

    # --- Check 2: share CI and profile flatness are finite and sane --------
    ci = estimator.share_ci(fit)
    for k in ("family", "era", "unique"):
        lo, hi = ci[k]
        print("  share CI %-6s (%.3f, %.3f)" % (k, lo, hi))
        assert np.isfinite(lo) and np.isfinite(hi) and lo < hi
    flat = estimator.profile_flatness(fit, "family")
    print("  profile flatness (family) = %.3f" % flat)
    assert np.isfinite(flat) and flat > 0

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
