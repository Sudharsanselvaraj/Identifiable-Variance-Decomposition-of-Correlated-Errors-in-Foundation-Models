"""Phase 2 eval intake validation: fail fast before trait assembly.

Validates the GPU-runbook output (``datasets/phase2_eval_results.csv`` +
``datasets/eval_samples/``) against the contract the Phase 2 engine expects, so
a partial, failed, or mis-shaped eval is caught at intake with a precise message
instead of surfacing as a confusing mid-pipeline error.

Contract (written by ``phase2_eval.append_result`` / ``write_samples``):
- CSV columns: full_name, hf_repo, acc, acc_norm, samples (others tolerated).
- Exactly one row per model in the expected manifest: no missing, no extras,
  no duplicates. By default the manifest is the full 47-model connected subset
  (``occupancy.model_table()``); pass ``--manifest`` (e.g. the G3
  ``datasets/coverage/minimal_population.csv``) to validate a reduced-run
  intake against that subset instead.
- acc in (0, 1], samples integer > 0, no NaN.
- Per-question JSONL: one file per model, one row per scored question;
  row count == the CSV ``samples`` cell; ``correct`` in {0, 1} (unscored rows
  reported, not fatal); the question set is shared across models (register A15).

Missing per-question samples are a warning (the pipeline runs on binomial SE
and skips the error-similarity panel); every other violation is a hard fail.

Usage (from src/):
    python3 -m lineage_era.phase2_eval_check [--csv ...] [--samples-dir ...]
    python3 -m lineage_era.phase2_eval_check --manifest datasets/coverage/minimal_population.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ..occupancy import model_table
from ..phase2_eval import EVAL_MANIFEST

REQUIRED_COLUMNS = ["full_name", "hf_repo", "acc", "acc_norm", "samples"]


def _load_eval_csv(csv_path: Path) -> tuple[pd.DataFrame | None, list[str]]:
    errors: list[str] = []
    if not csv_path.exists():
        errors.append(f"{csv_path} not found")
        return None, errors
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # noqa: BLE001 — report any parse failure
        errors.append(f"{csv_path} unreadable: {exc}")
        return None, errors
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"{csv_path} missing columns: {missing}")
    return df, errors


def _check_models(df: pd.DataFrame, manifest: pd.DataFrame
                  ) -> tuple[list[str], list[str]]:
    """Row-set consistency vs the connected-subset manifest.

    Returns (errors, warnings). Missing models are errors; the gated ones get
    an explicit hint so a partial --skip-gated run is distinguishable from a
    run failure.
    """
    errors: list[str] = []
    warnings: list[str] = []
    expected = set(manifest["full_name"])
    present = set(df["full_name"])
    dups = df["full_name"][df["full_name"].duplicated()].unique().tolist()
    if dups:
        errors.append(f"duplicate full_name rows: {sorted(dups)}")
    extra = sorted(present - expected)
    if extra:
        errors.append(f"full_name not in the connected subset: {extra}")
    missing = sorted(expected - present)
    if missing:
        gated = sorted(m for m in missing if EVAL_MANIFEST[m][2] == "gated")
        public = sorted(m for m in missing if EVAL_MANIFEST[m][2] == "public")
        msg = f"{len(missing)} model(s) missing from the eval CSV: {missing}"
        if gated:
            msg += (f"; {len(gated)} are gated ({gated}) — rerun those with an "
                    "HF token (--skip-gated leaves them out by design)")
        if public:
            msg += f"; {len(public)} are token-free and should NOT be missing ({public})"
        errors.append(msg)
    return errors, warnings


def _check_values(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Per-row numeric sanity on acc / acc_norm / samples."""
    errors: list[str] = []
    for col, lo, hi in (("acc", 0.0, 1.0), ("acc_norm", 0.0, 1.0)):
        bad = df.loc[
            pd.to_numeric(df[col], errors="coerce").isna()
            | ~pd.to_numeric(df[col], errors="coerce").between(lo, hi, inclusive="both"),
            "full_name",
        ].tolist()
        if bad:
            errors.append(f"{col} not in [{lo}, {hi}] or NaN for: {sorted(set(bad))}")
    samples = pd.to_numeric(df["samples"], errors="coerce")
    bad_n = df.loc[samples.isna() | (samples <= 0), "full_name"].tolist()
    if bad_n:
        errors.append(f"samples not a positive integer for: {sorted(set(bad_n))}")
    return errors, []


def _samples_summary(samples_dir: Path, full_names: list[str],
                     samples_col: dict[str, int]
                     ) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Per-model per-question JSONL checks.

    Returns (rows, errors, warnings). ``rows`` carries one entry per model:
    has_jsonl, n_rows, rows_match, correct_ok, n_missing_correct,
    item_set_match.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if not samples_dir.is_dir():
        return _empty_rows(full_names), [], [f"{samples_dir}: no per-question samples "
                                             "(panel skipped; trait SE is binomial)"]

    files = sorted(samples_dir.glob("*.jsonl"))
    file_model: dict[str, Path] = {}
    per_model: dict[str, dict] = {}
    for path in files:
        try:
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path} unreadable: {exc}")
            continue
        if not rows:
            errors.append(f"{path} is empty")
            continue
        fn = rows[0].get("full_name")
        if not fn:
            errors.append(f"{path}: first row missing full_name")
            continue
        if fn in file_model:
            errors.append(f"multiple JSONL files for model {fn}")
            continue
        file_model[fn] = path
        cols = set(rows[0])
        if "question" not in cols:
            errors.append(f"{path}: rows missing 'question'")
        if "correct" not in cols:
            errors.append(f"{path}: rows missing 'correct'")
            correct = None
        else:
            correct = [r.get("correct") for r in rows]
        n_rows = len(rows)
        n_missing = (sum(c is None for c in correct) if correct is not None
                     else n_rows)
        bad_correct = (sorted({c for c in correct if c is not None}
                              - {0, 1}) if correct is not None else [1])
        qset = {r.get("question") for r in rows if r.get("question") is not None}
        per_model[fn] = {
            "has_jsonl": True,
            "n_rows": n_rows,
            "rows_match": n_rows == samples_col.get(fn),
            "correct_ok": not bad_correct,
            "n_missing_correct": n_missing,
            "item_set": qset,
            "file": path,
        }
        if not per_model[fn]["rows_match"]:
            errors.append(
                f"{fn}: {n_rows} JSONL rows but CSV samples={samples_col.get(fn)}")
        if not per_model[fn]["correct_ok"]:
            errors.append(f"{fn}: correct values outside {{0, 1}}: {bad_correct}")

    # Common-item-set check (register A15): all models share the same questions.
    item_sets = {fn: d["item_set"] for fn, d in per_model.items() if d["item_set"]}
    if item_sets:
        ref = next(iter(item_sets.values()))
        for fn, qset in item_sets.items():
            per_model[fn]["item_set_match"] = qset == ref
            if qset != ref:
                errors.append(
                    f"{fn}: question set differs from the reference model "
                    f"(|ref|={len(ref)}, |this|={len(qset)}) — common item set "
                    "violated (register A15)")

    rows = []
    for fn in full_names:
        d = per_model.get(fn)
        if d is None:
            warnings.append(f"{fn}: no per-question JSONL found")
            rows.append({"full_name": fn, "has_jsonl": False, "n_rows": None,
                         "rows_match": None, "correct_ok": None,
                         "n_missing_correct": None, "item_set_match": None})
        else:
            rows.append({"full_name": fn, "has_jsonl": True, "n_rows": d["n_rows"],
                         "rows_match": d["rows_match"], "correct_ok": d["correct_ok"],
                         "n_missing_correct": d["n_missing_correct"],
                         "item_set_match": d.get("item_set_match")})
    return pd.DataFrame(rows), errors, warnings


def _empty_rows(full_names: list[str]) -> pd.DataFrame:
    return pd.DataFrame([
        {"full_name": fn, "has_jsonl": False, "n_rows": None, "rows_match": None,
         "correct_ok": None, "n_missing_correct": None, "item_set_match": None}
        for fn in full_names
    ])


def validate_eval(csv_path: Path, samples_dir: Path,
                  manifest: pd.DataFrame | None = None) -> dict:
    """Validate the eval intake against the Phase 2 contract.

    Returns a report dict: ok, errors, warnings, rows (per-model), csv,
    summary.
    """
    manifest = model_table() if manifest is None else manifest
    full_names = manifest["full_name"].tolist()
    df, errors = _load_eval_csv(csv_path)
    warnings: list[str] = []
    rows = None

    if df is not None:
        m_err, m_warn = _check_models(df, manifest)
        errors += m_err
        warnings += m_warn
        v_err, v_warn = _check_values(df)
        errors += v_err
        warnings += v_warn
        samples_col = dict(zip(df["full_name"],
                               pd.to_numeric(df["samples"], errors="coerce").fillna(-1)))
        rows, s_err, s_warn = _samples_summary(samples_dir, full_names, samples_col)
        errors += s_err
        warnings += s_warn

    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "rows": rows,
        "csv": df,
        "manifest": manifest,
        "summary": _summary(errors, warnings, df),
    }
    return report


def _summary(errors: list[str], warnings: list[str],
             df: pd.DataFrame | None) -> str:
    if df is None:
        return f"{len(errors)} error(s); eval CSV not loaded"
    n = len(df)
    parts = [f"{n} CSV rows"]
    if errors:
        parts.append(f"{len(errors)} error(s)")
    if warnings:
        parts.append(f"{len(warnings)} warning(s)")
    return "; ".join(parts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", default="datasets/phase2_eval_results.csv")
    p.add_argument("--samples-dir", default="datasets/eval_samples")
    p.add_argument("--manifest", default=None,
                   help="subset CSV with a full_name column (e.g. the G3 "
                        "minimal_population.csv) to validate against instead "
                        "of the full 47-model connected subset")
    args = p.parse_args(argv)

    manifest = model_table()
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"FAIL {args.manifest}: not found")
            return 1
        mdf = pd.read_csv(manifest_path)
        if "full_name" not in mdf.columns:
            print(f"FAIL {args.manifest}: needs a 'full_name' column")
            return 1
        if "kept" in mdf.columns:
            mdf = mdf[mdf["kept"].astype(str).str.strip().str.lower() == "true"]
        manifest = mdf[["full_name"]]
        unknown = sorted(set(manifest["full_name"]) - set(EVAL_MANIFEST))
        if unknown:
            print(f"FAIL {args.manifest}: unknown full_name(s): {unknown}")
            return 1

    report = validate_eval(Path(args.csv), Path(args.samples_dir),
                           manifest=manifest)
    print(f"eval intake: {report['summary']}")
    for w in report["warnings"]:
        print(f"  WARN {w}")
    for e in report["errors"]:
        print(f"  FAIL {e}")
    rows = report["rows"]
    if rows is not None and not rows.empty:
        pd.set_option("display.max_rows", 100)
        print(rows.to_string(index=False))
    print("PASS" if report["ok"] else "FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
