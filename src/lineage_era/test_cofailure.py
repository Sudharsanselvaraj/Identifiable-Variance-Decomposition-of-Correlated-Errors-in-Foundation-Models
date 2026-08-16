"""Co-failure ceiling beta: validation of the closed form and the claims of
``analysis/cofailure.py`` / ``docs/02_Theory/CoFailure_Ceiling.md`` (C7).

Simulation-first rule: the analytic closed form is checked against the exact
logistic DGP (Monte Carlo), and the swap claims of Proposition C7b are pinned
as inequalities. Run:

    python src/lineage_era/test_cofailure.py

from the repository root (or pytest on the file).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import cofailure  # noqa: E402

S1 = {"L": 0.60, "E": 0.10, "U": 0.30}   # lineage-dominant
S2 = {"L": 0.10, "E": 0.60, "U": 0.30}   # era-dominant
S3 = {"L": 0.35, "E": 0.35, "U": 0.30}   # balanced


def _pool(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["full_name", "family", "quarter"])


def test_single_model_floor() -> None:
    one = _pool([("m", "F", "2024Q1")])
    assert abs(cofailure.all_wrong_gaussian(one, S1, mu=0.0) - 0.5) < 1e-9
    hi = cofailure.all_wrong_gaussian(one, S1, mu=2.0)   # accurate model
    lo = cofailure.all_wrong_gaussian(one, S1, mu=-2.0)  # weak model
    assert hi < 0.5 < lo


def test_closed_form_tracks_dgp() -> None:
    pool = _pool([("a", "F", "2024Q1"), ("b", "F", "2024Q2"),
                  ("c", "F", "2024Q3"), ("d", "F", "2024Q4")])
    for s2 in (S1, S2, S3):
        g = cofailure.all_wrong_gaussian(pool, s2, mu=0.0)
        mc = cofailure.all_wrong_montecarlo(pool, s2, mu=0.0,
                                            n_items=2000, n_reps=80, seed=11)
        assert abs(g - mc) < 0.03, f"closed form off by {g - mc:+.4f}"


def test_swap_value_increases_with_lineage_share() -> None:
    pool = _pool([("a", "F", "2024Q1"), ("b", "F", "2024Q2"),
                  ("c", "F", "2024Q3"), ("d", "F", "2024Q4")])
    d_s1 = cofailure.swap_counterfactual(pool, S1, "a", "G", "2025Q1")["delta_beta"]
    d_s3 = cofailure.swap_counterfactual(pool, S3, "a", "G", "2025Q1")["delta_beta"]
    d_s2 = cofailure.swap_counterfactual(pool, S2, "a", "G", "2025Q1")["delta_beta"]
    assert d_s1 > d_s3 > d_s2
    assert d_s2 > 0.0


def test_swap_carries_era_only() -> None:
    pool = _pool([("m0", "F", "2024Q2"), ("m1", "F", "2024Q2"),
                  ("m2", "F", "2024Q2"), ("m3", "F", "2024Q1")])
    era_match = cofailure.swap_counterfactual(pool, S1, "m3", "G", "2024Q2")
    fresh_era = cofailure.swap_counterfactual(pool, S1, "m3", "G", "2025Q1")
    assert fresh_era["delta_beta"] > era_match["delta_beta"]
    assert era_match["delta_beta"] > 0.0


def test_mixed_family_lowers_ceiling() -> None:
    same = _pool([("a", "F", "2024Q1"), ("b", "F", "2024Q1"),
                  ("c", "F", "2024Q1"), ("d", "F", "2024Q1")])
    mixed = _pool([("a", "F", "2024Q1"), ("b", "G", "2024Q1"),
                   ("c", "H", "2024Q1"), ("d", "J", "2024Q1")])
    assert cofailure.all_wrong_gaussian(same, S1, mu=0.0) > \
        cofailure.all_wrong_gaussian(mixed, S1, mu=0.0)


def test_equicorrelated_path_matches_mvn() -> None:
    rows = [(f"m{i}", "F", "2024Q1") for i in range(9)]
    pool = _pool(rows)
    g = cofailure.all_wrong_gaussian(pool, S1, mu=0.0)  # k>8 -> 1-d path
    Sigma = cofailure._latent_covariance(pool, S1, 0.5, cofailure.PROBIT_C)
    exact = float(multivariate_normal(mean=np.zeros(9), cov=Sigma)
                  .cdf(np.zeros(9)))
    assert abs(g - exact) < 1e-3


def test_report_block_renders() -> None:
    trait = pd.DataFrame({
        "full_name": ["a", "b", "c", "d", "e"],
        "family": ["F", "F", "F", "G", "G"],
        "era": ["2024Q1", "2024Q2", "2024Q3", "2024Q1", "2024Q2"],
        "trait": [0.1, 0.2, 0.3, -0.1, 0.0],
    })
    vp = pd.DataFrame({
        "component": ["family", "era", "unique"],
        "variance": [0.6, 0.1, 0.3],
    })
    lines = cofailure.report_block(trait, vp)
    text = "\n".join(lines)
    assert "Decision layer" in text
    assert "diversification value" in text
    assert "0.857" in text  # sigma2_L/(sigma2_L+sigma2_E) = 0.6/0.7


def main() -> None:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok {t.__name__}")
    print(f"CO-FAILURE CEILING OK ({len(tests)} tests)")


if __name__ == "__main__":
    main()
