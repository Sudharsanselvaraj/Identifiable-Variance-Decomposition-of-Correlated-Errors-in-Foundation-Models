"""Metrics for the Phase 1 battery: bias, coverage, and the D3 diagnostics."""
from __future__ import annotations

import numpy as np

from . import estimator


def relative_bias(est: float, truth: float) -> float:
    """(est - truth) / truth. NaN-safe; returns 0 if truth is 0."""
    if truth == 0:
        return float("nan") if est != 0 else 0.0
    return (est - truth) / truth


def share_bias_pp(est: float, truth: float) -> float:
    """Absolute share bias in percentage points: (est - truth) * 100."""
    return (est - truth) * 100.0


def coverage(interval: tuple[float, float], truth: float) -> bool:
    """Whether a (low, high) interval covers the truth."""
    return interval[0] <= truth <= interval[1]


def ci_width(interval: tuple[float, float]) -> float:
    return interval[1] - interval[0]


def collinearity_detected(fit: estimator.FitResult, r_crit: float = 0.9) -> bool:
    """|corr(BLUP family, BLUP era)| > r_crit (aliasing of the two channels)."""
    fam = fit.blups.get("family")
    era = fit.blups.get("era")
    if fam is None or era is None or len(fam) < 2 or len(era) < 2:
        return False
    if np.all(fam == fam[0]) or np.all(era == era[0]):
        return False
    r = np.corrcoef(fam, era)[0, 1]
    return abs(r) > r_crit


def se_inflation_detected(fit: estimator.FitResult, threshold: float = 1.0) -> bool:
    """Any variance component has SE >= threshold * estimate (unidentifiable)."""
    for k in fit.s2:
        est = fit.s2[k]
        se = fit.se.get(k)
        if est <= 0 and se is not None:
            return True
        if se is not None and est > 0 and se / est >= threshold:
            return True
    return False


def profile_flatness_detected(fit: estimator.FitResult, vc_name: str = "family",
                              dist: float = 0.4, num: int = 15) -> bool:
    """Profile likelihood cannot establish a 95% CI over the window."""
    drop = estimator.profile_flatness(fit, vc_name, dist=dist, num=num)
    return drop < estimator.PROFILE_CUTOFF


def non_convergence_detected(fit: estimator.FitResult) -> bool:
    return (not fit.converged) or fit.n_convergence_warnings > 0


def d3_diagnostics(fit: estimator.FitResult) -> dict:
    """Run all D3 failure detectors; report per-detector booleans."""
    return {
        "collinearity": collinearity_detected(fit),
        "se_inflation": se_inflation_detected(fit),
        "profile_flat": profile_flatness_detected(fit),
        "non_convergence": non_convergence_detected(fit),
    }


def d3_detected(diag: dict) -> bool:
    """D3 correctly fails if ANY detector fires."""
    return any(diag.values())


def ratio_relative_bias(est: dict, truth: dict, a: str = "family",
                        b: str = "era") -> float:
    """Relative bias of the ratio est[a]/est[b] vs truth[a]/truth[b]."""
    est_r = est[a] / est[b] if est[b] else float("nan")
    true_r = truth[a] / truth[b] if truth[b] else float("nan")
    if true_r == 0:
        return float("nan")
    return (est_r - true_r) / true_r


def ranking_ok(est: dict, truth: dict) -> bool:
    """Whether the recovered family-vs-era ordering matches the truth."""
    est_dominant = "family" if est["family"] >= est["era"] else "era"
    true_dominant = "family" if truth["family"] >= truth["era"] else "era"
    return est_dominant == true_dominant
