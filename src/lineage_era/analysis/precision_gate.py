"""Precision gate for the crossed family x era variance-components model.

Why this module exists
----------------------
The original gate (``identifiability.structural_checks``) tests rank, condition
number and VIF of the *fixed-effects* dummy design ``X = [1 | Z_F | Z_E]``. The
estimator actually fitted (``reml.CrossedREML``) treats family and era as
*random* effects with an intercept-only fixed part, so that dummy-design rank is
not the identifiability condition for (sigma2_L, sigma2_E, sigma2_U):

* Variance-component identifiability requires the covariance basis
  ``{Z_F Z_F', Z_E Z_E', I}`` to be linearly independent (``basis_rank == 3``).
* Whether the identified components are *reportable* is a question of
  precision, which is measured here directly:

  1. analytic: expected REML (Fisher) information at pre-specified variance
     scenarios -> delta-method SE of the family and era shares and the
     correlation between sigma2_L-hat and sigma2_E-hat (aliasing index);
  2. Monte Carlo: simulate y ~ N(mu, V(theta)) on the design, refit with the
     same CrossedREML estimator, and measure bias / RMSE / boundary rate of the
     share estimates. Asymptotic SEs are unreliable with ~5 family levels, so
     the Monte Carlo result is the verdict and the analytic SE is a fast screen.

Both use only the design (family, era) and the scenario grid -- never observed
trait values -- so the gate can run before any model is measured.

Scale: shares are invariant to a common rescaling of the variance components,
so scenarios are given as share triples summing to 1.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .reml import CrossedREML

# Scenario grid (family, era, unique) shares. A/B/C match the Phase 1
# simulation (D1/D2); D is a low-signal scenario closer to the observed
# 16-model diagnostic fit (family share ~5%).
SCENARIOS: dict[str, tuple[float, float, float]] = {
    "A_lineage": (0.50, 0.20, 0.30),
    "B_era": (0.20, 0.50, 0.30),
    "C_balanced": (0.33, 0.33, 0.34),
    "D_low_signal": (0.10, 0.10, 0.80),
}

# Pre-specified reportability bar: RMSE of each share <= 10 percentage points
# under every scenario (a 95% interval half-width of roughly +/-20pp).
SHARE_RMSE_MAX = 0.10
ALIAS_CORR_MAX = 0.90


def incidence(df: pd.DataFrame, family: str = "family", era: str = "era"):
    """Return (Z_F, Z_E) 0/1 indicator matrices for the occupied levels."""
    zf = (df[family].to_numpy()[:, None] == np.unique(df[family])).astype(float)
    ze = (df[era].to_numpy()[:, None] == np.unique(df[era])).astype(float)
    return zf, ze


def covariance_basis(zf: np.ndarray, ze: np.ndarray) -> list[np.ndarray]:
    return [zf @ zf.T, ze @ ze.T, np.eye(zf.shape[0])]


def covariance_basis_rank(zf: np.ndarray, ze: np.ndarray) -> int:
    """Rank of {Z_F Z_F', Z_E Z_E', I} as vectors in R^(n*n); 3 = identified."""
    B = np.stack([m.ravel() for m in covariance_basis(zf, ze)], axis=1)
    return int(np.linalg.matrix_rank(B))


def expected_information(zf: np.ndarray, ze: np.ndarray,
                         s2: tuple[float, float, float]) -> np.ndarray:
    """Expected REML information for (sigma2_L, sigma2_E, sigma2_U).

    I_ij = 0.5 * tr(P V_i P V_j), P = V^-1 - V^-1 1 (1' V^-1 1)^-1 1' V^-1.
    """
    basis = covariance_basis(zf, ze)
    V = sum(s * b for s, b in zip(s2, basis))
    Vi = np.linalg.inv(V)
    one = np.ones((V.shape[0], 1))
    P = Vi - (Vi @ one @ one.T @ Vi) / float(one.T @ Vi @ one)
    PB = [P @ b for b in basis]
    return np.array([[0.5 * np.trace(a @ b) for b in PB] for a in PB])


def analytic_precision(zf: np.ndarray, ze: np.ndarray,
                       shares: tuple[float, float, float]) -> dict:
    """Delta-method SE of the family/era shares and the sigma2_L/E correlation."""
    s = np.asarray(shares, dtype=float)
    info = expected_information(zf, ze, tuple(s))
    cond = float(np.linalg.cond(info))
    if not np.isfinite(cond) or cond > 1e12:
        return {"info_cond": cond, "se_share_family": np.inf,
                "se_share_era": np.inf, "corr_family_era": 1.0}
    cov = np.linalg.inv(info)
    total = s.sum()

    def share_se(k: int) -> float:
        grad = -s[k] / total**2 * np.ones(3)
        grad[k] += 1.0 / total
        return float(np.sqrt(max(grad @ cov @ grad, 0.0)))

    corr = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    return {"info_cond": cond, "se_share_family": share_se(0),
            "se_share_era": share_se(1), "corr_family_era": float(corr)}


def monte_carlo_precision(zf: np.ndarray, ze: np.ndarray,
                          shares: tuple[float, float, float],
                          reps: int = 200, seed: int = 0) -> dict:
    """Simulate on the design, refit with CrossedREML, summarize share recovery."""
    rng = np.random.default_rng(seed)
    n, nf, ne = zf.shape[0], zf.shape[1], ze.shape[1]
    sL, sE, sU = shares
    est = []
    n_conv = 0
    for _ in range(reps):
        y = (zf @ rng.normal(0, np.sqrt(sL), nf)
             + ze @ rng.normal(0, np.sqrt(sE), ne)
             + rng.normal(0, np.sqrt(sU), n))
        solver = CrossedREML(y, [zf, ze])
        theta, _, ok = solver.fit()
        n_conv += ok
        v = np.exp(theta)
        est.append(v / v.sum())
    est = np.array(est)
    truth = np.array(shares)
    err = est - truth
    lo, hi = np.percentile(est, [2.5, 97.5], axis=0)
    return {
        "mc_reps": reps,
        "mc_converged": n_conv / reps,
        "bias_share_family": float(err[:, 0].mean()),
        "bias_share_era": float(err[:, 1].mean()),
        "rmse_share_family": float(np.sqrt((err[:, 0] ** 2).mean())),
        "rmse_share_era": float(np.sqrt((err[:, 1] ** 2).mean())),
        "width95_share_family": float(hi[0] - lo[0]),
        "width95_share_era": float(hi[1] - lo[1]),
        # share < 1% = estimator collapsed the component to the boundary
        "boundary_rate_family": float((est[:, 0] < 0.01).mean()),
        "boundary_rate_era": float((est[:, 1] < 0.01).mean()),
    }


@dataclass
class GateResult:
    design: str
    basis_rank: int
    rows: pd.DataFrame          # one row per scenario

    @property
    def identified(self) -> bool:
        return self.basis_rank == 3

    @property
    def reportable(self) -> bool:
        if not self.identified or "rmse_share_family" not in self.rows:
            return False
        r = self.rows
        return bool((r["rmse_share_family"] <= SHARE_RMSE_MAX).all()
                    and (r["rmse_share_era"] <= SHARE_RMSE_MAX).all())

    @property
    def worst_rmse(self) -> float:
        if "rmse_share_family" not in self.rows:
            return float("nan")
        return float(self.rows[["rmse_share_family", "rmse_share_era"]].max().max())


def precision_gate(df: pd.DataFrame, name: str = "design",
                   scenarios: dict | None = None, reps: int = 200,
                   seed: int = 0, monte_carlo: bool = True) -> GateResult:
    """Run the identifiability + precision gate on a (family, era) design."""
    scenarios = scenarios or SCENARIOS
    zf, ze = incidence(df)
    rank = covariance_basis_rank(zf, ze)
    rows = []
    for i, (label, sh) in enumerate(scenarios.items()):
        row = {"design": name, "scenario": label, "n": len(df),
               "families": zf.shape[1], "eras": ze.shape[1], "basis_rank": rank}
        row.update(analytic_precision(zf, ze, sh) if rank == 3 else
                   {"info_cond": np.inf, "se_share_family": np.inf,
                    "se_share_era": np.inf, "corr_family_era": 1.0})
        if monte_carlo and rank == 3:
            row.update(monte_carlo_precision(zf, ze, sh, reps=reps, seed=seed + i))
        rows.append(row)
    return GateResult(design=name, basis_rank=rank, rows=pd.DataFrame(rows))
