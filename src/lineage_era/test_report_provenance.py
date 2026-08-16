"""Provenance labeling of Phase 2 reports (2026-08-06 AE review follow-up).

A shape-exact simulated dry-run is indistinguishable from a real run inside a
generated report unless the generator stamps the data source. These tests pin:

1. ``analysis/report.main`` — a report built from ``*.sim.csv`` input must carry
   a loud ``SIMULATED DRY-RUN DATA`` banner; real input must not.
2. ``analysis/report.main_tables`` — ``results_summary.csv`` records
   ``data_source`` and a ``simulated`` flag.
3. ``phase2_decomposition.main`` — refuses simulated/synthetic input into the
   default ``results/phase2`` path (exit 2) unless ``--sim-ok``.

Run from the repository root:
    python src/lineage_era/test_report_provenance.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import report  # noqa: E402


def _build_outdir(root: Path, n_models: int = 3) -> Path:
    out = root / "results"
    out.mkdir(parents=True, exist_ok=True)
    comps = pd.DataFrame([
        {"component": "family", "variance": 0.5, "se": 0.2,
         "share": 0.55, "share_lo": 0.2, "share_hi": 0.8},
        {"component": "era", "variance": 0.15, "se": 0.1,
         "share": 0.15, "share_lo": 0.02, "share_hi": 0.45},
        {"component": "unique", "variance": 0.35, "se": 0.08,
         "share": 0.30, "share_lo": 0.1, "share_hi": 0.6},
    ])
    comps.to_csv(out / "variance_partition.csv", index=False)
    bc = comps.rename(columns={"variance": "unused"})
    bc["mc_lo"] = bc["share"] - 0.01
    bc["mc_hi"] = bc["share"] + 0.01
    bc["mc_sd"] = 0.003
    bc.drop(columns=["unused"]).to_csv(out / "bootstrap_ci.csv", index=False)
    fam = pd.DataFrame({
        "family": ["A", "B"], "family_blup": [0.5, -0.5],
        "mean_trait": [0.6, -0.4], "n_models": [2, 1],
    })
    fam.to_csv(out / "family_effects.csv", index=False)
    era = pd.DataFrame({
        "era": ["2024Q1", "2024Q2"], "era_blup": [0.1, -0.1],
        "mean_trait": [0.2, -0.2], "n_models": [2, 1],
    })
    era.to_csv(out / "era_effects.csv", index=False)
    pd.DataFrame({"full_name": [f"m{i}" for i in range(n_models)],
                  "family": ["A", "A", "B"], "era": ["2024Q1", "2024Q2", "2024Q2"],
                  "trait": [0.7, 0.2, 0.0], "trait_se": [0.05] * n_models}
                 ).to_csv(out / "trait_table.csv", index=False)
    pd.DataFrame({"family": ["A", "B"], "era": ["2024Q1", "2024Q2"]}
                 ).to_csv(out / "analysis_design.csv", index=False)
    pd.DataFrame({"term": ["family", "era"], "max_vif": [1.1, 1.2]}
                 ).to_csv(out / "vif.csv", index=False)
    (out / "condition_number.txt").write_text("kappa = 12.3000\n")
    (out / "identifiability_report.md").write_text(
        "Identifiability audit\n\nVerdict: **PASS**\n")
    (out / "tables.md").write_text("### θ_P variance partition (variance_partition.csv)\n")
    (out / "figures").mkdir(exist_ok=True)
    return out


def test_sim_report_carries_banner() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = _build_outdir(Path(td))
        assert report.main(["--out-dir", str(out),
                            "--eval-csv", "datasets/phase2_eval_results.sim.csv"]) == 0
        text = (out / "PHASE2_REPORT.md").read_text()
        assert "SIMULATED DRY-RUN DATA — NOT REAL GPU OUTPUT" in text
        assert "phase2_eval_results.sim.csv" in text
        assert "phase2_eval_results.sim.csv" in text.split("Generated:", 1)[1]


def test_real_report_has_no_banner() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = _build_outdir(Path(td))
        assert report.main(["--out-dir", str(out),
                            "--eval-csv", "datasets/phase2_eval_results.csv"]) == 0
        text = (out / "PHASE2_REPORT.md").read_text()
        assert "SIMULATED" not in text
        assert "datasets/phase2_eval_results.csv" in text


def test_synthetic_report_is_labeled() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = _build_outdir(Path(td))
        assert report.main(["--out-dir", str(out), "--synthetic"]) == 0
        assert "SIMULATED DRY-RUN DATA" in (out / "PHASE2_REPORT.md").read_text()


def test_results_summary_records_provenance() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = _build_outdir(Path(td))
        report.main_tables(["--out-dir", str(out),
                            "--eval-csv", "datasets/phase2_eval_results.sim.csv"])
        df = pd.read_csv(out / "results_summary.csv")
        assert bool(df.loc[0, "simulated"]) is True
        assert df.loc[0, "data_source"] == "datasets/phase2_eval_results.sim.csv"
        report.main_tables(["--out-dir", str(out),
                            "--eval-csv", "datasets/phase2_eval_results.csv"])
        df2 = pd.read_csv(out / "results_summary.csv")
        assert bool(df2.loc[0, "simulated"]) is False
        assert df2.loc[0, "data_source"] == "datasets/phase2_eval_results.csv"


def test_decomposition_refuses_sim_into_real_path() -> None:
    from lineage_era import phase2_decomposition
    assert phase2_decomposition.main(["--synthetic"]) == 2
    assert phase2_decomposition.main(
        ["--eval-csv", "datasets/phase2_eval_results.sim.csv"]) == 2


def main() -> None:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok {t.__name__}")
    print(f"REPORT-PROVENANCE OK ({len(tests)} tests)")


if __name__ == "__main__":
    main()
