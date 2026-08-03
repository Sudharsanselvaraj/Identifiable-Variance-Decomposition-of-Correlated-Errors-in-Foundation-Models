"""Phase 2 trait assembly: aggregate eval output into a per-model trait table.

Ingests ``datasets/phase2_eval_results.csv`` (per-model MMLU 5-shot acc from the
fresh pass) and, when available, the per-question JSONL under
``datasets/eval_samples/`` produced by ``phase2_eval.py``. The trait is the
continuous per-model MMLU accuracy (Phase 1 F4 pivot: model a continuous
per-model trait, not raw item-level binary responses). When question samples
exist, a per-model trait SE (binomial) and a subject-level accuracy table are
also produced.

Outputs (under src/results/phase2/):
- trait_table.csv : full_name, family, era, short_name, trait, trait_se,
  n_items, n_correct, source
- subject_acc.csv : full_name, subject, n_items, n_correct, acc  (if samples)

Usage (from src/):
    python3 -m lineage_era.phase2_trait [--eval-csv ...] [--out-dir results/phase2]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .occupancy import model_table

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"
DEFAULT_EVAL_CSV = DATASETS / "phase2_eval_results.csv"
DEFAULT_SAMPLES_DIR = DATASETS / "eval_samples"


def load_eval_results(csv_path: Path = DEFAULT_EVAL_CSV) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run the fresh MMLU 5-shot eval pass first "
            "(phase2_run_all.py on a GPU host)."
        )
    df = pd.read_csv(csv_path)
    if "full_name" not in df.columns:
        raise ValueError(f"{csv_path} missing 'full_name' column")
    return df


def load_question_samples(samples_dir: Path = DEFAULT_SAMPLES_DIR) -> pd.DataFrame:
    """Concat all per-question JSONL files into one long DataFrame.

    Empty if the samples dir is missing or has no files.
    """
    if not samples_dir.is_dir():
        return pd.DataFrame()
    frames = []
    for path in sorted(samples_dir.glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        frames.append(pd.DataFrame(rows))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def assemble_trait(eval_df: pd.DataFrame, table: pd.DataFrame | None = None,
                   samples: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-model trait frame: merge eval acc with the Phase 0 occupancy table.

    trait      = per-model MMLU 5-shot accuracy (continuous, 0..1)
    trait_se   = binomial SE sqrt(p(1-p)/n); refined from question samples when
                 available (sample standard error of the per-question scores)
    n_items    = number of scored questions
    """
    if table is None:
        table = model_table()
    if samples is None:
        samples = load_question_samples()

    se_by_model = {}
    n_by_model = {}
    if not samples.empty:
        g = samples.groupby("full_name")["correct"]
        n_by_model = g.size().to_dict()
        se_by_model = {
            m: float(gd.std(ddof=1) / np.sqrt(len(gd))) if len(gd) > 1 else float("nan")
            for m, gd in g
        }

    rows = []
    for _, r in eval_df.iterrows():
        fn = r["full_name"]
        acc = float(r["acc"])
        n = int(n_by_model.get(fn, r.get("samples", np.nan))) if n_by_model else r.get("samples")
        n = n if n == n else np.nan
        se = se_by_model.get(fn)
        if se is None and n == n and acc == acc and n > 0:
            se = float(np.sqrt(max(acc * (1.0 - acc) / n, 0.0)))
        n_correct = int(round(acc * n)) if n == n and acc == acc else np.nan
        rows.append({
            "full_name": fn,
            "hf_repo": r.get("hf_repo", ""),
            "trait": acc,
            "trait_se": se,
            "n_items": n,
            "n_correct": n_correct,
            "source": "fresh",
        })
    trait = pd.DataFrame(rows)
    if table is not None:
        trait = table.merge(trait, on="full_name", how="left")
        trait["era"] = trait["quarter"]
    return trait


def subject_accuracy(samples: pd.DataFrame) -> pd.DataFrame:
    """Per-model x subject accuracy from the question samples (empty if none)."""
    if samples.empty or "subject" not in samples.columns:
        return pd.DataFrame()
    g = samples.groupby(["full_name", "subject"])["correct"]
    out = g.agg(n_items="size", n_correct="sum").reset_index()
    out["acc"] = out["n_correct"] / out["n_items"]
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--eval-csv", default=str(DEFAULT_EVAL_CSV))
    p.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR))
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    eval_df = load_eval_results(Path(args.eval_csv))
    samples = load_question_samples(Path(args.samples_dir))
    trait = assemble_trait(eval_df, samples=samples)
    trait.to_csv(out_dir / "trait_table.csv", index=False)

    if samples.empty:
        print("No per-question samples found; trait SE is binomial from the CSV "
              "sample counts.", file=__import__("sys").stderr)
    subj = subject_accuracy(samples)
    if not subj.empty:
        subj.to_csv(out_dir / "subject_acc.csv", index=False)

    print(f"Trait table: {len(trait)} models, "
          f"{int(trait['n_items'].sum()) if trait['n_items'].notna().any() else 0} questions")
    print(f"-> {out_dir / 'trait_table.csv'}")
    if not subj.empty:
        print(f"-> {out_dir / 'subject_acc.csv'} ({len(subj)} model x subject rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
