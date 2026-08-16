"""Co-failure ceiling beta and the diversification counterfactual (claim C7).

Given a fitted variance partition (s2_L, s2_E, s2_U) on the trait scale (logit
accuracy) and the Phase 0 occupancy, compute the ensemble co-failure ceiling
beta(S) = P(all members of pool S wrong on a question) two ways:

  * ``all_wrong_montecarlo``  - exact DGP sampling (logistic link), the ground
    truth the closed form is validated against (simulation-first rule);
  * ``all_wrong_gaussian``    - probit closed form: sigma(x) ~= Phi(x/1.7)
    turns beta(S) into a k-variate normal CDF at zero (one-dimensional
    equicorrelated form when the pool is same-family and same-era).

``swap_counterfactual`` returns the change in beta when one pool member is
replaced by a model from an unrepresented family: the swap removes s2_L from
every pairwise latent covariance involving the replaced model and retains s2_E
when the replacement shares the pool's era. This is the decision-layer number
for RQ6 (is diversification a credible remedy) and the empirical content of
Proposition C7b in ``docs/02_Theory/CoFailure_Ceiling.md``.

All outputs are simulation output until Phase 2 real eval lands; the report
block carries the same SIMULATED provenance banner as the rest of the dry-run.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal

PROBIT_C = 1.6  # sigma(x) ~= Phi(x / c); c=1.6 minimizes max RELATIVE error
# (Amemiya 1981); 1.7 minimizes max absolute error, pi/sqrt(3) matches the
# logistic variance. 1.6 tracks the exact logistic DGP best for orthant
# probabilities (validated in test_cofailure.py).


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass(frozen=True)
class BetaResult:
    beta: float
    method: str
    pool: tuple[str, ...]


def pool_from_design(design: pd.DataFrame, names: Iterable[str]) -> pd.DataFrame:
    """Subset of the occupancy/trait table used as a pool.

    ``design`` must have ``full_name``, ``family``, and ``quarter``/``era``
    columns. Returns the same columns restricted to ``names``.
    """
    col = "era" if "era" in design.columns else "quarter"
    out = design.loc[design["full_name"].isin(names),
                     ["full_name", "family", col]].rename(columns={col: "quarter"})
    return out.reset_index(drop=True)


def _latent_covariance(pool: pd.DataFrame, s2: dict[str, float],
                       diff_sd: float, c: float) -> np.ndarray:
    """k x k covariance of Z_m = trait_m + delta + eta_m under the probit link."""
    k = len(pool)
    Sigma = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            if i == j:
                Sigma[i, j] = (s2["L"] + s2["E"] + s2["U"]) + diff_sd ** 2 + c ** 2
            else:
                same_fam = pool.loc[i, "family"] == pool.loc[j, "family"]
                same_era = pool.loc[i, "quarter"] == pool.loc[j, "quarter"]
                Sigma[i, j] = (s2["L"] * int(same_fam)
                               + s2["E"] * int(same_era)) + diff_sd ** 2
    return Sigma


def _equicorrelated_orthant(cov: float, var: float, k: int, threshold: float,
                            rng: np.random.Generator) -> float:
    """P(all Z_j < threshold) for equicorrelated normals.

    Z_j = sqrt(cov)*W + eps_j, eps_j ~ N(0, var - cov), W ~ N(0,1) i.i.d.
    Conditional on W the events are independent, so the k-dimensional orthant
    probability collapses to the one-dimensional integral
        E_W[Phi((threshold - W*sqrt(cov)) / sqrt(var - cov))^k].
    """
    sd_c = np.sqrt(max(cov, 0.0))
    sd_e = np.sqrt(max(var - cov, 1e-12))
    w = rng.normal(0.0, 1.0, 200_000)
    return float(np.mean(_phi((threshold - sd_c * w) / sd_e) ** k))


def _phi(x: np.ndarray) -> np.ndarray:
    from scipy.stats import norm
    return norm.cdf(x)


def all_wrong_gaussian(pool: pd.DataFrame, s2: dict[str, float],
                       mu: float = 0.0, diff_sd: float = 0.5,
                       c: float = PROBIT_C, seed: int = 0) -> float:
    """beta(S) via the probit closed form (k-variate normal orthant).

    With W_m = (trait_m - mu) + delta + eta_m, the all-wrong event is
    {trait_m + delta + eta_m < 0} = {W_m < -mu}, so
        beta(S) = Phi_k(-mu * 1; 0, Sigma),
    a k-variate normal CDF evaluated at a common threshold -mu. Uses the exact
    MVN CDF, with the one-dimensional equicorrelated form when every member
    shares family and era (large-k stable path).
    """
    k = len(pool)
    if k == 0:
        raise ValueError("empty pool")
    threshold = -mu
    Sigma = _latent_covariance(pool, s2, diff_sd, c)
    if k == 1:
        var = Sigma[0, 0]
        return float(_phi(np.array([threshold / np.sqrt(var)]))[0])
    same_fam = pool["family"].nunique() == 1
    same_era = pool["quarter"].nunique() == 1
    if k > 8 and same_fam and same_era:
        cov = Sigma[0, 1]
        var = Sigma[0, 0]
        return _equicorrelated_orthant(cov, var, k, threshold,
                                       np.random.default_rng(seed))
    return float(multivariate_normal(mean=np.zeros(k), cov=Sigma)
                 .cdf(np.full(k, threshold)))


def all_wrong_montecarlo(pool: pd.DataFrame, s2: dict[str, float],
                         mu: float = 0.0, diff_sd: float = 0.5,
                         n_items: int = 2000, n_reps: int = 50,
                         seed: int = 0) -> float:
    """beta(S) by exact DGP sampling on the trait scale (logistic link).

    trait_m = mu + alpha_{fam} + beta_{era} + u_m, alpha/beta/u Gaussian with
    variances s2["L"]/s2["E"]/s2["U"]; per item i, wrong with probability
    sigma(-(trait_m + delta_i)), delta_i ~ N(0, diff_sd^2).
    """
    rng = np.random.default_rng(seed)
    fams = pool["family"].unique().tolist()
    eras = pool["quarter"].unique().tolist()
    names = pool["full_name"].tolist()
    fam_of = dict(zip(names, pool["family"]))
    era_of = dict(zip(names, pool["quarter"]))
    sdL, sdE, sdU = np.sqrt(max(s2["L"], 0.0)), np.sqrt(max(s2["E"], 0.0)), \
        np.sqrt(max(s2["U"], 0.0))
    total = 0.0
    for _ in range(n_reps):
        alpha = {f: rng.normal(0.0, sdL) for f in fams}
        beta = {e: rng.normal(0.0, sdE) for e in eras}
        u = {p: rng.normal(0.0, sdU) for p in names}
        trait = {p: mu + alpha[fam_of[p]] + beta[era_of[p]] + u[p] for p in names}
        acc = 0.0
        for _ in range(n_items):
            delta = rng.normal(0.0, diff_sd)
            prod = 1.0
            for p in names:
                prod *= _sigmoid(-(trait[p] + delta))
            acc += prod
        total += acc / n_items
    return float(total / n_reps)


def swap_counterfactual(pool: pd.DataFrame, s2: dict[str, float],
                        swap_member: str, new_family: str, new_era: str,
                        mu: float = 0.0, diff_sd: float = 0.5,
                        c: float = PROBIT_C, n_items: int = 2000,
                        n_reps: int = 50, seed: int = 0,
                        method: str = "gaussian") -> dict:
    """Beta before/after replacing ``swap_member`` with a model from
    ``new_family``/``new_era`` (assumed unrepresented in the pool).

    Returns beta0, beta1, delta_beta = beta0 - beta1 (>= 0 when the swap helps),
    and the s2 context. ``method`` is "gaussian" (closed form) or "mc".
    """
    pool = pool.reset_index(drop=True)
    if swap_member not in set(pool["full_name"]):
        raise ValueError(f"{swap_member} not in pool")
    if new_family in set(pool["family"]):
        raise ValueError(
            f"{new_family} is not unrepresented; swap targets a new family")
    replaced = pool[pool["full_name"] != swap_member].copy()
    repl = pd.DataFrame([{"full_name": f"<{new_family}:{new_era}:replacement>",
                          "family": new_family, "quarter": new_era}])
    pool1 = pd.concat([replaced, repl], ignore_index=True)

    if method == "gaussian":
        b0 = all_wrong_gaussian(pool, s2, mu=mu, diff_sd=diff_sd, c=c, seed=seed)
        b1 = all_wrong_gaussian(pool1, s2, mu=mu, diff_sd=diff_sd, c=c,
                                seed=seed + 1)
    elif method == "mc":
        b0 = all_wrong_montecarlo(pool, s2, mu=mu, diff_sd=diff_sd,
                                  n_items=n_items, n_reps=n_reps, seed=seed)
        b1 = all_wrong_montecarlo(pool1, s2, mu=mu, diff_sd=diff_sd,
                                  n_items=n_items, n_reps=n_reps, seed=seed + 1)
    else:
        raise ValueError(method)
    return {
        "pool": tuple(pool["full_name"]),
        "swap_member": swap_member,
        "new_family": new_family,
        "new_era": new_era,
        "beta0": b0,
        "beta1": b1,
        "delta_beta": b0 - b1,
        "s2_L": s2["L"],
        "s2_E": s2["E"],
        "s2_U": s2["U"],
        "share_L": s2["L"] / sum(s2.values()),
        "share_E": s2["E"] / sum(s2.values()),
    }


def report_block(trait_table: pd.DataFrame,
                 variance_partition: pd.DataFrame) -> list[str]:
    """Decision-layer Markdown block for PHASE2_REPORT.md (claim C7).

    Builds a same-family pool from the trait table, computes the co-failure
    ceiling before/after a cross-family swap, and states the governing ratio.
    """
    s2 = {k: float(variance_partition.set_index("component")
                   .loc[name, "variance"])
          for k, name in [("L", "family"), ("E", "era"), ("U", "unique")]}
    mu = float(trait_table["trait"].mean())
    fam_counts = trait_table.groupby("family")["full_name"].count()
    fam = str(fam_counts.idxmax())
    members = trait_table[trait_table["family"] == fam]["full_name"].head(4).tolist()
    pool = pool_from_design(trait_table, members)
    eras = sorted(trait_table[trait_table["family"] == fam]["era"].unique().tolist())
    swap_member = members[0]
    new_family = str(
        trait_table.loc[~trait_table["family"].isin([fam]), "family"].iloc[0])
    new_era = eras[-1] if eras else "2024Q1"

    res = swap_counterfactual(pool, s2, swap_member, new_family, new_era,
                              mu=mu)
    share_L = res["share_L"]
    share_E = res["share_E"]
    lines = [
        "## Decision layer: co-failure ceiling and the diversification counterfactual",
        "",
        f"Pool: {len(members)} {fam} models "
        f"({', '.join(members)}) | trait mean μ={mu:.3f} (logit scale).",
        "",
        f"| | value |",
        "|---|---|",
        f"| β(S) current pool (all-wrong ceiling) | {res['beta0']:.4f} |",
        f"| β(S′) after swapping {swap_member} → {new_family} ({new_era}) | "
        f"{res['beta1']:.4f} |",
        f"| Δβ diversification value | {res['delta_beta']:.4f} |",
        f"| σ²_L share / σ²_E share | {share_L:.3f} / {share_E:.3f} |",
        "",
        f"Cross-family diversification value is governed by "
        f"σ²_L/(σ²_L+σ²_E) = {share_L / (share_L + share_E):.3f}: a swap removes "
        "σ²_L from the pairwise latent covariance but carries σ²_E when the "
        "replacement shares the pool's era.",
        "",
    ]
    return lines


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trait-csv", required=True)
    p.add_argument("--partition-csv", required=True)
    args = p.parse_args(argv)
    trait = pd.read_csv(args.trait_csv)
    vp = pd.read_csv(args.partition_csv)
    print("\n".join(report_block(trait, vp)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
