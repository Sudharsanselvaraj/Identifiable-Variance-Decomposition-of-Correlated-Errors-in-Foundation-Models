"""Validate the eval intake validator + shape-exact simulated eval generator.

The generator produces runbook-shaped data (47 models x shared item set,
per-question JSONL) from a per-question choice DGP with known family/era/model
effects. The validator must PASS on well-formed data, FAIL on each deliberate
mangling, and treat missing per-question samples as a warning (not a fail).

Run from the repository root:
    python src/lineage_era/test_eval_check.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import eval_check  # noqa: E402
from lineage_era.analysis import eval_simulate  # noqa: E402
from lineage_era.analysis import reml  # noqa: E402
from lineage_era import dgp  # noqa: E402
from lineage_era import phase2_trait  # noqa: E402


def _gen(n_items: int = 600, seed: int = 7, **kw) -> tuple[Path, Path]:
    tmp = Path(tempfile.mkdtemp())
    csv_path = tmp / "eval.csv"
    samp = tmp / "samples"
    eval_simulate.simulate_eval(scenario=dgp.SCENARIOS["A"], n_items=n_items,
                                seed=seed, csv_path=csv_path,
                                samples_dir=samp, **kw)
    return csv_path, samp


def test_validator_passes_wellformed() -> None:
    csv_path, samp = _gen()
    report = eval_check.validate_eval(csv_path, samp)
    assert report["ok"], report["errors"]
    assert not report["warnings"]
    rows = report["rows"]
    assert len(rows) == 47
    assert rows["has_jsonl"].all() and rows["rows_match"].all()
    assert rows["correct_ok"].all() and rows["item_set_match"].all()
    assert rows["n_missing_correct"].sum() == 0


def test_validator_missing_model_fails() -> None:
    csv_path, samp = _gen(drop=["Llama-1"])
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("missing from the eval CSV" in e and "Llama-1" in e
               for e in report["errors"])
    assert any("gated" in e for e in report["errors"])


def test_validator_extra_model_fails() -> None:
    csv_path, samp = _gen()
    df = pd.read_csv(csv_path)
    df.loc[len(df)] = {"date": "x", "full_name": "Not-A-Real-Model",
                       "hf_repo": "x/y", "benchmark": "mmlu", "fewshot": 5,
                       "acc": 0.5, "acc_norm": 0.5, "samples": 600}
    df.to_csv(csv_path, index=False)
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("not in the connected subset" in e for e in report["errors"])


def test_validator_duplicate_fails() -> None:
    csv_path, samp = _gen()
    df = pd.read_csv(csv_path)
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df.to_csv(csv_path, index=False)
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("duplicate" in e.lower() for e in report["errors"])


def test_validator_bad_acc_fails() -> None:
    csv_path, samp = _gen()
    df = pd.read_csv(csv_path)
    df.loc[df["full_name"] == "Phi-2", "acc"] = 1.7
    df.to_csv(csv_path, index=False)
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("acc not in" in e and "Phi-2" in e for e in report["errors"])


def test_validator_rows_mismatch_fails() -> None:
    csv_path, samp = _gen()
    f = next(samp.glob("*.jsonl"))
    lines = f.read_text().splitlines()
    f.write_text("\n".join(lines[:-1]))
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("JSONL rows but CSV samples" in e for e in report["errors"])


def test_validator_bad_correct_fails() -> None:
    csv_path, samp = _gen()
    f = next(samp.glob("*.jsonl"))
    lines = f.read_text().splitlines()
    row = json.loads(lines[0])
    row["correct"] = 2
    lines[0] = json.dumps(row)
    f.write_text("\n".join(lines))
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("correct values outside" in e for e in report["errors"])


def test_validator_item_set_mismatch_fails() -> None:
    csv_path, samp = _gen()
    files = sorted(samp.glob("*.jsonl"))
    f = files[1]
    lines = f.read_text().splitlines()
    row = json.loads(lines[0])
    row["question"] = "different-question-id"
    lines[0] = json.dumps(row)
    f.write_text("\n".join(lines))
    report = eval_check.validate_eval(csv_path, samp)
    assert not report["ok"]
    assert any("common item set" in e for e in report["errors"])


def test_missing_samples_is_warning_not_fail() -> None:
    csv_path, samp = _gen()
    empty = samp.parent / "no_samples"
    report = eval_check.validate_eval(csv_path, empty)
    assert report["ok"]
    assert any("no per-question samples" in w for w in report["warnings"])


def test_no_samples_csv_only() -> None:
    csv_path, samp = _gen(write_samples=False)
    assert not samp.exists()
    report = eval_check.validate_eval(csv_path, samp)
    assert report["ok"]
    assert any("no per-question samples" in w for w in report["warnings"])


def test_roundtrip_recovers_lineage_dominant() -> None:
    """Scenario A (L/E/U = .50/.20/.30) tracked over seeds.

    Single-seed share recovery is noisy at the real 6-family occupancy (Phase 1
    register A21), so assert mechanism per dataset and directionality on the
    mean over seeds (the Phase 1 battery convention).
    """
    fams, eras, uniqs = [], [], []
    for seed in (0, 7, 11, 21):
        csv_path, samp = _gen(n_items=1000, seed=seed)
        report = eval_check.validate_eval(csv_path, samp)
        assert report["ok"]
        eval_df = phase2_trait.load_eval_results(csv_path)
        samples = phase2_trait.load_question_samples(samp)
        trait = phase2_trait.assemble_trait(eval_df, samples=samples)
        assert len(trait) == 47 and trait["trait"].notna().all()
        vp, _ = reml.variance_partition(trait)
        sh = vp.set_index("component")["share"].to_dict()
        assert all(0.0 <= sh[k] <= 1.0 for k in ("family", "era", "unique"))
        assert abs(sum(sh.values()) - 1.0) < 1e-6
        fams.append(sh["family"]); eras.append(sh["era"]); uniqs.append(sh["unique"])
    mf, me = float(np.mean(fams)), float(np.mean(eras))
    print(f"mean recovered shares (4 seeds): family={mf:.3f} era={me:.3f} "
          f"unique={float(np.mean(uniqs)):.3f}")
    assert mf > me + 0.05, (mf, me)


def main() -> None:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok {t.__name__}")
    print(f"EVAL-CHECK VALIDATION OK ({len(tests)} tests)")


if __name__ == "__main__":
    main()
