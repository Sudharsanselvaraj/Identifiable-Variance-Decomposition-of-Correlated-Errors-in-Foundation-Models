"""Validate the G3 minimum-valid-population gate and its runbook wiring.

The gate is the pre-registered pre-GPU gate (2026-08-03): smallest connected
subset whose design is identifiable AND whose era recovery clears the strict
Phase 1 D2 bar on the fixed-design battery (scenarios A and B, mean over
reps). These tests pin the invariants, determinism, the n=47 fallback, and
the CSV -> --subset / --manifest plumbing.

Run from the repository root:
    python src/lineage_era/test_population_optimizer.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import population_optimizer as po  # noqa: E402
from lineage_era.analysis import eval_check  # noqa: E402
from lineage_era.phase2_eval import EVAL_MANIFEST  # noqa: E402


def test_structural_minimum_deterministic() -> None:
    n0a, s0a = po.structural_minimum()
    n0b, s0b = po.structural_minimum()
    assert (n0a, s0a) == (n0b, s0b)
    assert n0a < len(po.MODELS)


def test_structural_minimum_identifiable() -> None:
    n0, s0 = po.structural_minimum()
    assert len(s0) == n0
    ok, checks = po.structural_ok(s0)
    assert ok, checks


def test_baseline_full_47_passes_strict_bar() -> None:
    full = [m[3] for m in po.MODELS]
    val = po.validate_subset(full, reps=100)
    assert po.validation_passes(val), val
    for scen in po.VALIDATION_SCENARIOS:
        assert val[scen]["convergence_pct"] == 100.0


def test_validation_deterministic_per_reps() -> None:
    sub = [m[3] for m in po.MODELS]
    a = po.validate_subset(sub, reps=15)
    b = po.validate_subset(sub, reps=15)
    assert a == b


def test_search_minimum_below_full_and_valid() -> None:
    # Relax the confirmation margin so the baseline (B bias ~ -4.5pp at 100
    # reps) clears confirmation at test speed; the margin value itself is
    # pinned by the committed g3_report.md artifact.
    real = po.CONFIRM_BIAS_PP_MAX
    po.CONFIRM_BIAS_PP_MAX = 6.0
    try:
        res = po.find_minimal_valid(reps=100, confirm_reps=120, attempts=4)
    finally:
        po.CONFIRM_BIAS_PP_MAX = real
    assert res["baseline_ok"]
    assert res["baseline_confirmed"]["A"]["convergence_pct"] == 100.0
    assert 21 <= res["n_valid"] < len(po.MODELS), res["n_valid"]
    assert len(res["subset"]) == res["n_valid"]
    assert po.validation_passes(po.validate_subset(res["subset"], reps=100))
    ok, checks = po.structural_ok(res["subset"])
    assert ok, checks


def test_winner_hard_constraints_hold() -> None:
    """The committed winner: families, quarters, span, forced, crossed."""
    csv_path = po.REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"
    df = pd.read_csv(csv_path)
    kept = df.loc[df["kept"], "full_name"].tolist()
    sub = po.subset_table(kept)
    assert set(sub["family"]) == set(po.FAMILIES)
    span = sub.groupby("family")["quarter"].nunique()
    assert (span >= 2).all(), span
    assert set(sub["quarter"]) == set(po.QUARTERS)
    assert all(f in set(kept) for f in po.FORCED)
    per_q = sub.groupby("quarter")["family"].nunique()
    assert (per_q >= 2).sum() >= 2


def test_winner_keeps_theta_m_chain() -> None:
    csv_path = po.REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"
    df = pd.read_csv(csv_path)
    kept = set(df.loc[df["kept"], "full_name"])
    for name in po.MISTRAL_SMALL_CHAIN:
        assert name in kept
    assert "Llama-3.3" in kept and "Llama-3.1" in kept


REASON_ALLOWED = {
    "edge-or-chain-forced (theta_M)",
    "dropped: redundant in-cell replication (identifiability unchanged)",
    "required: era-window coverage",
    "required: structural identifiability (crossing)",
    "required: structural identifiability (rank/VIF)",
    "required: statistical recoverability (D2 gate)",
}


def test_csv_reason_taxonomy_complete() -> None:
    csv_path = po.REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"
    df = pd.read_csv(csv_path)
    assert set(df["reason"]) <= REASON_ALLOWED
    dropped = df.loc[~df["kept"]]
    kept = df.loc[df["kept"]]
    assert (dropped["reason"]
            == "dropped: redundant in-cell replication (identifiability unchanged)").all()
    forced_rows = kept[kept["full_name"].isin(set(po.FORCED))]
    assert (forced_rows["reason"] == "edge-or-chain-forced (theta_M)").all(), \
        forced_rows["reason"].tolist()


def test_report_refined_sections_present() -> None:
    report = (po.REPO_ROOT / "datasets" / "coverage" / "g3_report.md").read_text()
    assert "Outcome-independent study design" in report
    assert "| G3 input | Used? |" in report
    assert "Trait values / accuracy" in report
    assert "Minimum VALID population = 22" in report
    assert "| 47 | 47 | True | True | True" in report
    assert "| 22 | 22 | True | True | True | 2.44 | 98.0 | -0.78 | 99.0 | 2.19 | -2.36 |" in report
    assert "knife-edge" in report
    assert "redundant in-cell replication" in report


def test_write_outputs_roundtrip_consistent() -> None:
    """write_outputs on the committed winner reproduces the committed CSV
    reasons and a report whose winner row matches the committed trace."""
    csv_path = po.REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"
    df = pd.read_csv(csv_path)
    kept = df.loc[df["kept"], "full_name"].tolist()
    res = {
        "n0": 21, "n_valid": len(kept), "subset": kept, "results": [
            {"n": len(kept), "n_models": len(kept), "rank_ok": True,
             "vif_ok": True, "pass": True,
             "bias_pp_A": 2.44, "cov_pct_A": 98.0, "bias_pp_B": -0.78,
             "cov_pct_B": 99.0, "bias_pp_A_conf": 2.19, "bias_pp_B_conf": -2.36}],
        "baseline": {"A": {"era_bias_pp": 0.34, "era_coverage_pct": 98.7,
                           "convergence_pct": 100.0},
                     "B": {"era_bias_pp": -3.52, "era_coverage_pct": 96.3,
                           "convergence_pct": 100.0},
                     "n": 47},
        "baseline_ok": True,
        "baseline_confirmed": {"A": {"era_bias_pp": 1.54, "era_coverage_pct": 98.3,
                                     "convergence_pct": 100.0},
                               "B": {"era_bias_pp": -2.22, "era_coverage_pct": 97.5,
                                     "convergence_pct": 100.0},
                               "n": 47},
    }
    tmp = Path(tempfile.mkdtemp())
    csv_out, report_out = po.write_outputs(res, tmp)
    df_out = pd.read_csv(csv_out)
    assert df_out["reason"].tolist() == df["reason"].tolist()
    assert df_out["kept"].tolist() == df["kept"].tolist()
    txt = report_out.read_text()
    assert "| 47 | 47 | True | True | True" in txt
    assert "| 22 | 22 | True | True | True | 2.44 | 98.0 | -0.78 | 99.0 | 2.19 | -2.36 |" in txt


def test_fallback_returns_full_when_search_blocked() -> None:
    real = po._milp_solve
    real_margin = po.CONFIRM_BIAS_PP_MAX
    po._milp_solve = lambda *a, **k: None  # type: ignore[assignment]
    po.CONFIRM_BIAS_PP_MAX = 6.0
    try:
        res = po.find_minimal_valid(reps=100, confirm_reps=100, attempts=2)
    finally:
        po._milp_solve = real
        po.CONFIRM_BIAS_PP_MAX = real_margin
    assert res["n_valid"] == len(po.MODELS)
    assert res["subset"] == [m[3] for m in po.MODELS]


def test_cost_vector_finite_nonnegative() -> None:
    c = po.cost_vector()
    assert np.isfinite(c).all() and (c >= 0).all()
    assert len(c) == len(po.MODELS)


def test_runbook_subset_plumbing() -> None:
    from lineage_era.phase2_run_all import subset_models
    csv_path = po.REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"
    df = pd.read_csv(csv_path)
    expected = int(df["kept"].sum())
    names = subset_models(str(csv_path))
    assert len(names) == expected > 0
    assert len(set(names)) == len(names)
    assert all(n in EVAL_MANIFEST for n in names)


def test_eval_check_manifest_override() -> None:
    """A reduced-run intake validates against a subset manifest, not 47."""
    sub = [m[3] for m in po.MODELS if m[1] in ("2024Q4", "2025Q1")]
    manifest = pd.DataFrame({"full_name": sub})
    df = pd.DataFrame({
        "date": ["x"] * len(sub),
        "full_name": sub,
        "hf_repo": ["a/b"] * len(sub),
        "benchmark": ["mmlu"] * len(sub),
        "fewshot": [5] * len(sub),
        "acc": [0.5] * len(sub),
        "acc_norm": [0.5] * len(sub),
        "samples": [10] * len(sub),
    })
    tmp = Path(__import__("tempfile").mkdtemp())
    csv_path = tmp / "eval.csv"
    df.to_csv(csv_path, index=False)
    report = eval_check.validate_eval(csv_path, tmp / "samples",
                                      manifest=manifest)
    assert report["ok"], report["errors"]
    assert len(report["rows"]) == len(sub)


def main() -> None:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok {t.__name__}")
    print(f"POPULATION-OPTIMIZER VALIDATION OK ({len(tests)} tests)")


if __name__ == "__main__":
    main()
