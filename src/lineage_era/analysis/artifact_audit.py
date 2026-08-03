"""Phase 2 artifact-availability audit: per-model x source reuse table.

Decision support (2026-08-03): can EXISTING public item-level predictions
replace or top up the fresh MMLU 5-shot eval for the 47-model connected subset?
Each model is scored against every candidate public source and a reuse verdict
is emitted, so the GPU decision rests on evidence, not assumption.

Candidate sources:
- Open LLM Leaderboard v2 per-sample JSONL (``datasets/kim/model_to_file.csv``):
  per-question predictions exist for 8/47 of our models, but on MMLU-PRO
  (10-choice, different items), frozen <= Dec 2024, and gated behind repo-term
  acceptance. Wrong benchmark -> not reusable for trait or panel.
- HELM per-question tall file (``all_mmlu_data_limitedcols.csv`` in Kim et al.'s
  GitHub release, arXiv:2506.07962, CC BY 4.0): per-question x model exists for
  the 14 HELM-reconciled models, but on HELM's own MMLU item set/template with
  HELM-specific question ids (no bridge to a fresh ``cais/mmlu`` run).
- HELM/HF aggregate MMLU accuracy (18/47, via ``population.RECONCILIATION``):
  score only -> cross-check (register A22), never the trait or the panel.

Verdict (see ``datasets/coverage/artifact_audit.csv``): under the designed
protocol (MMLU 5-shot, strict common item set, register A15) reusable
per-question coverage is 0/47, so the fresh eval of ALL 47 is the only
compliant path for BOTH the trait and the (zero-cost byproduct) error-similarity
panel. The no-artifact 29 are mostly post-freeze (2025Q1+) -- incl. every
DeepSeek -- plus pre-2024 stragglers that never reached leaderboard v2
(Llama-1, Qwen-7B, Phi-1/1.5, Phi-4, DeepSeek-V3).

Usage (from src/):
    python3 -m lineage_era.phase2_artifact_audit [--out ../datasets/coverage/artifact_audit.csv]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from ..occupancy import MODELS
from ..phase2_eval import EVAL_MANIFEST
from .population import RECONCILIATION

REPO_ROOT = Path(__file__).resolve().parents[3]
KIM_DIR = REPO_ROOT / "datasets" / "kim"
DEFAULT_OUT = REPO_ROOT / "datasets" / "coverage" / "artifact_audit.csv"

# HELM's per-question tall file ships in Kim et al.'s GitHub release (the repo
# only carries the aggregate ``model_accuracy.csv``).
HELM_TALL_REF = "all_mmlu_data_limitedcols.csv (Kim GitHub; not in-repo)"


def _parse_acc(v) -> float | None:
    """Parse an accuracy cell, tolerating HELM's JAX-era trailing 'F' suffix."""
    if pd.isna(v):
        return None
    s = str(v).strip().rstrip("fF")
    try:
        return float(s)
    except ValueError:
        return None


def load_aggregate_accuracy(helm_path: Path, hf_path: Path
                            ) -> tuple[dict[str, float], dict[str, float]]:
    """HELM / HF per-model MMLU accuracy, keyed by leaderboard model id.

    Mirrors ``population.load_kim_data`` so the audit agrees with the coverage
    gate on every number it reuses.
    """
    helm = pd.read_csv(helm_path)
    helm.columns = ["idx", "model", "accuracy"]
    helm_acc = {str(m): parsed for m, raw in
                zip(helm["model"], helm["accuracy"])
                if (parsed := _parse_acc(raw)) is not None}

    hf = pd.read_csv(hf_path, header=None)
    hf.columns = ["model", "accuracy"]
    hf_acc = {str(m): parsed for m, raw in
              zip(hf["model"], hf["accuracy"])
              if str(m).strip() and (parsed := _parse_acc(raw)) is not None}
    return helm_acc, hf_acc


def load_model_to_file(path: Path) -> dict[str, dict]:
    """hf repo -> per-sample JSONL pointer (Open LLM Leaderboard v2)."""
    df = pd.read_csv(path)
    return {str(r["Model"]): r for r in df.to_dict("records")}


def _freeze_from_filename(file: str) -> str:
    """Extract the eval-run timestamp from a per-sample filename, if present."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})T", file)
    return m.group(1) if m else ""


def build_audit(helm_path: Path = KIM_DIR / "model_accuracy.csv",
                hf_path: Path = KIM_DIR / "hf_model_accuracy.csv",
                m2f_path: Path = KIM_DIR / "model_to_file.csv") -> pd.DataFrame:
    """47-row per-model x source audit table."""
    helm_acc, hf_acc = load_aggregate_accuracy(helm_path, hf_path)
    m2f = load_model_to_file(m2f_path)

    rows = []
    for family, quarter, short, full in MODELS:
        repo, params, access = EVAL_MANIFEST[full]

        lb = RECONCILIATION.get(full)  # (source, leaderboard id) | None
        lb_source, lb_model, agg_acc = "", "", float("nan")
        if lb is not None:
            lb_source, lb_model = lb
            accs = helm_acc if lb_source == "helm" else hf_acc
            agg_acc = float(accs[lb_model]) if lb_model in accs else float("nan")

        pq_source = pq_file = pq_benchmark = ""
        if repo in m2f:
            pq_source = "openllm_mmlu_pro"
            pq_file = str(m2f[repo]["File"])
            pq_benchmark = "mmlu_pro"
        elif lb_source == "helm":
            pq_source = "helm_mmlu"
            pq_file = HELM_TALL_REF
            pq_benchmark = "helm_mmlu"

        rows.append({
            "family": family,
            "quarter": quarter,
            "short_name": short,
            "full_name": full,
            "hf_repo": repo,
            "params": params,
            "access": access,
            "lb_source": lb_source,
            "lb_model": lb_model,
            "aggregate_accuracy": agg_acc,
            "per_question_source": pq_source,
            "per_question_file": pq_file,
            "per_question_benchmark": pq_benchmark,
            "per_question_frozen": _freeze_from_filename(pq_file),
            "reuse_verdict": "cross-check-only" if lb_source else "none",
            "needs_inference": True,
        })
    return pd.DataFrame(rows)


def audit_summary(df: pd.DataFrame) -> dict:
    """Counts behind the reuse verdict."""
    n = len(df)
    return {
        "n_models": n,
        "cross_check": int((df["reuse_verdict"] == "cross-check-only").sum()),
        "none": int((df["reuse_verdict"] == "none").sum()),
        "openllm_mmlu_pro": int((df["per_question_source"] == "openllm_mmlu_pro").sum()),
        "helm_mmlu": int((df["per_question_source"] == "helm_mmlu").sum()),
        "needs_inference": int(df["needs_inference"].sum()),
        "protocol_matched_reuse": 0,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    args = p.parse_args(argv)

    df = build_audit()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    s = audit_summary(df)
    print(f"artifact audit: {s['n_models']} models")
    print(f"  aggregate cross-check only: {s['cross_check']} "
          f"(HELM 14 + HF 4 via RECONCILIATION)")
    print(f"  no public artifact: {s['none']} "
          "(mostly 2025Q1+ post-freeze incl. every DeepSeek; a few pre-2024 "
          "stragglers never reached leaderboard v2)")
    print(f"  per-question sources (NOT protocol-matched): "
          f"openllm MMLU-PRO {s['openllm_mmlu_pro']}, "
          f"helm MMLU {s['helm_mmlu']}")
    print(f"  protocol-matched per-question reuse: "
          f"{s['protocol_matched_reuse']}/47")
    print(f"  models needing fresh inference: {s['needs_inference']}/47")
    print("VERDICT: public item-level data cannot replace the fresh MMLU 5-shot "
          "eval (register A15 common item set); the panel rides the same run "
          "at zero extra cost.")
    print(f"Wrote per-model table to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
