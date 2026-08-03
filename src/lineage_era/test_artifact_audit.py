"""Validate the artifact-availability audit and the GPU cost planner.

The audit must report 47/47 models needing fresh inference (reuse verdict
"none"/"cross-check-only", never protocol-matched reuse), agree with
``population.reconcile`` on the 18 aggregate cross-check accuracies, and
classify the per-question sources exactly (8 openllm MMLU-PRO + 10 helm MMLU).
The planner must bucket the manifest correctly (70B -> 2x80GB, DeepSeek-class
in fp8 on 141GB cards, gated/public split 24/23).

Run from the repository root:
    python src/lineage_era/test_artifact_audit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import artifact_audit  # noqa: E402
from lineage_era.analysis import gpu_cost  # noqa: E402
from lineage_era.analysis import population  # noqa: E402
from lineage_era.phase2_eval import EVAL_MANIFEST  # noqa: E402


def _audit() -> pd.DataFrame:
    df = artifact_audit.build_audit()
    assert len(df) == 47
    return df


def test_audit_full_coverage() -> None:
    df = _audit()
    assert set(df["full_name"]) == set(EVAL_MANIFEST)
    assert df["needs_inference"].all()


def test_audit_reuse_verdict_counts() -> None:
    df = _audit()
    assert int((df["reuse_verdict"] == "cross-check-only").sum()) == 18
    assert int((df["reuse_verdict"] == "none").sum()) == 29
    assert int((df["per_question_source"] == "openllm_mmlu_pro").sum()) == 8
    assert int((df["per_question_source"] == "helm_mmlu").sum()) == 10
    assert artifact_audit.audit_summary(df)["protocol_matched_reuse"] == 0
    # Every DeepSeek is artifact-free (leaderboard froze before V3 shipped).
    assert (df.loc[df["family"] == "DeepSeek", "reuse_verdict"] == "none").all()
    # The no-artifact set is dominated by post-freeze models but includes a few
    # pre-2024 stragglers that never reached leaderboard v2 (Llama-1, Qwen-7B,
    # Phi-1/1.5, Phi-4, DeepSeek-V3).
    none_names = set(df.loc[df["reuse_verdict"] == "none", "full_name"])
    assert {"Llama-1", "Qwen-7B", "Phi-1", "Phi-1.5", "Phi-4",
            "DeepSeek-V3"} <= none_names
    assert len(none_names) == 29


def test_audit_agrees_with_population() -> None:
    """Cross-check: the 18 aggregate accuracies match the coverage gate source."""
    df = _audit()
    rec = population.reconcile(population.load_kim_data())
    rec = rec[rec["covered"]].set_index("full_name")["accuracy"]
    aud = df.set_index("full_name")["aggregate_accuracy"]
    for full in rec.index:
        assert full in aud.index, full
        assert abs(float(aud[full]) - float(rec[full])) < 1e-9, full
    assert len(rec) == 18


def test_parse_acc_tolerates_f_suffix() -> None:
    assert artifact_audit._parse_acc("0.8000284859706595F") == 0.8000284859706595
    assert artifact_audit._parse_acc(0.65) == 0.65
    assert artifact_audit._parse_acc(None) is None


def test_cost_covers_manifest() -> None:
    df = gpu_cost.build_cost_table()
    assert len(df) == 47
    assert set(df["full_name"]) == set(EVAL_MANIFEST)
    s = gpu_cost.cost_summary(df)
    assert s["n_models"] == 47 and s["n_public"] == 23 and s["n_gated"] == 24


def test_cost_gpu_class_buckets() -> None:
    df = gpu_cost.build_cost_table().set_index("full_name")
    assert df.loc["Llama-2", "gpus_80gb_bf16"] == 2          # 140 GB bf16
    assert df.loc["Llama-2", "gpu_class"] == "2x80GB"
    assert df.loc["Llama-3.2", "gpu_class"] == "4x80GB"      # 180 GB bf16
    assert df.loc["Mixtral-8x7B", "active_params_b"] == 13.0
    # DeepSeek-class: TOTAL params drive memory (fp8, 141GB cards).
    assert df.loc["DeepSeek-V3", "total_params_b"] == 671.0
    assert df.loc["DeepSeek-V3", "active_params_b"] == 37.0
    assert df.loc["DeepSeek-V3", "gpus_141gb_fp8"] == 6
    assert df.loc["DeepSeek-V3", "gpu_class"] == "8xH200-141GB (fp8)"
    # Llama-4 Maverick: ~400B total / 17B active.
    assert df.loc["Llama-4", "total_params_b"] == 400.0
    assert df.loc["Llama-4", "active_params_b"] == 17.0
    assert df.loc["Llama-4", "gpu_class"] == "8x80GB (fp8)"


def main() -> None:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok {t.__name__}")
    print(f"ARTIFACT-AUDIT + GPU-COST VALIDATION OK ({len(tests)} tests)")


if __name__ == "__main__":
    main()
