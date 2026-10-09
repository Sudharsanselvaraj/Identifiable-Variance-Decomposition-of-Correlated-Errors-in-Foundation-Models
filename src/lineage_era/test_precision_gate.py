"""Tests for the random-effects precision gate (analysis/precision_gate.py)."""
import numpy as np
import pandas as pd

from lineage_era.analysis.precision_gate import (
    analytic_precision, covariance_basis_rank, incidence, monte_carlo_precision,
    precision_gate)


def _crossed(nf: int, ne: int, per_cell: int = 1) -> pd.DataFrame:
    rows = [(f"F{f}", f"E{e}") for f in range(nf) for e in range(ne)
            for _ in range(per_cell)]
    return pd.DataFrame(rows, columns=["family", "era"])


def test_nested_design_is_not_identified():
    # Each family confined to its own era: Z_F Z_F' == Z_E Z_E'.
    df = pd.DataFrame([(f"F{f}", f"E{f}") for f in range(6) for _ in range(4)],
                      columns=["family", "era"])
    assert covariance_basis_rank(*incidence(df)) == 2
    res = precision_gate(df, reps=5)
    assert not res.identified and not res.reportable


def test_fixed_effect_alias_does_not_break_variance_identifiability():
    # One family that is also the only model in its era: the fixed-effects
    # dummy design is rank deficient, but the variance components are not.
    df = pd.concat([_crossed(4, 4), pd.DataFrame([("Fx", "Ex")],
                                                 columns=["family", "era"])])
    zf, ze = incidence(df)
    X = np.column_stack([np.ones(len(df)), zf[:, 1:], ze[:, 1:]])
    assert np.linalg.matrix_rank(X) < X.shape[1]
    assert covariance_basis_rank(zf, ze) == 3


def test_analytic_se_shrinks_with_more_family_levels():
    shares = (0.33, 0.33, 0.34)
    small = analytic_precision(*incidence(_crossed(5, 8)), shares)
    large = analytic_precision(*incidence(_crossed(40, 8)), shares)
    assert large["se_share_family"] < small["se_share_family"] / 2


def test_monte_carlo_recovers_shares_on_large_balanced_design():
    zf, ze = incidence(_crossed(30, 14, per_cell=2))
    mc = monte_carlo_precision(zf, ze, (0.5, 0.2, 0.3), reps=30, seed=1)
    assert abs(mc["bias_share_family"]) < 0.06
    assert mc["rmse_share_era"] < 0.15
