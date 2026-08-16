"""Tests for the pre-registered DeepSeek imputation (analysis/impute.py)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lineage_era.analysis.eval_simulate import simulate_eval
from lineage_era.analysis.impute import impute

MEASURED = [
    "Llama-1", "Phi-1", "Mistral-7B", "Phi-1.5", "Qwen-7B", "Phi-2",
    "Qwen1.5", "Phi-3", "Llama-3.1", "Qwen2.5", "Llama-3.3", "Phi-4",
    "Mistral-Small-3", "Mistral-Small-3.1", "Gemma-3n", "Mistral-Small-3.2",
    "Phi-4-reasoning-plus", "Devstral-2", "Mistral-Small-4",
    "Phi-4-reasoning-vision-15B",
]
TARGETS = ["DeepSeek-V3.1", "DeepSeek-V3.2"]
ALL = MEASURED + TARGETS


@pytest.fixture()
def measured_inputs(tmp_path: Path):
    from lineage_era.phase2_eval import EVAL_MANIFEST

    drop = [fn for fn in EVAL_MANIFEST if fn not in MEASURED]
    sim_csv = tmp_path / "phase2_eval_results.csv"
    sim_samples = tmp_path / "eval_samples"
    simulate_eval(n_items=300, seed=0, csv_path=sim_csv,
                  samples_dir=sim_samples, drop=drop)
    return sim_csv, sim_samples


def _run(tmp_path: Path, measured_inputs, **kw):
    sim_csv, sim_samples = measured_inputs
    return impute(sim_csv, sim_samples, targets=list(TARGETS),
                  out_csv=tmp_path / "out.csv",
                  out_samples=tmp_path / "out_samples",
                  report_path=tmp_path / "report.md",
                  **kw)


def test_impute_shape_and_fidelity(tmp_path, measured_inputs):
    rep = _run(tmp_path, measured_inputs, m=3, seed=2026)
    df = pd.read_csv(rep["csv"])
    assert len(df) == 22
    assert set(df["full_name"]) == set(ALL)
    assert rep["n_measured"] == 20
    for t in TARGETS:
        row = df[df["full_name"] == t].iloc[0]
        assert row["fidelity"] == "imputed"
        assert 0.03 <= row["acc"] <= 0.97
    measured_fids = set(df[~df["full_name"].isin(TARGETS)]["fidelity"])
    assert measured_fids <= {"measured"}

    files = sorted(p.name for p in rep["samples_dir"].glob("*.jsonl"))
    assert len(files) == 22
    for t in TARGETS:
        assert any(f.startswith(t + "__") for f in files)


def test_impute_deterministic(tmp_path, measured_inputs):
    a = _run(tmp_path, measured_inputs, m=3, seed=2026)
    b = _run(tmp_path, measured_inputs, m=3, seed=2026)
    assert Path(a["csv"]).read_bytes() == Path(b["csv"]).read_bytes()
    assert Path(a["report"]).read_bytes() == Path(b["report"]).read_bytes()


def test_impute_accuracy_calibrated(tmp_path, measured_inputs):
    rep = _run(tmp_path, measured_inputs, m=1, seed=2026)
    df = pd.read_csv(rep["csv"])
    target = TARGETS[0]
    trait = float(df[df["full_name"] == target]["acc"].iloc[0])
    fname = [p for p in rep["samples_dir"].glob(f"{target}__*.jsonl")][0]
    rows = [json.loads(line) for line in fname.read_text().splitlines()]
    realized = float(np.mean([r["correct"] for r in rows]))
    assert abs(realized - trait) <= 0.05


def test_report_disclosure(tmp_path, measured_inputs):
    rep = _run(tmp_path, measured_inputs, m=3, seed=2026)
    text = Path(rep["report"]).read_text()
    assert "IMPUTED" in text
    assert "not measured" in text
    assert "pooled (mean over" in text
    assert "IMPUTED_PREMEASUREMENT" in text
    for t in TARGETS:
        assert t in text


def test_rejects_missing_measured_samples(tmp_path):
    with pytest.raises(FileNotFoundError):
        impute(tmp_path / "nope.csv", tmp_path / "nope_samples",
               targets=list(TARGETS))
