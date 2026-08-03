"""Phase 2 data assembly: reconcile the connected subset with leaderboard data.

Coverage check + per-model continuous trait for the Phase 2 decomposition.
The trait is the precomputed per-model MMLU accuracy from Kim et al.
(arXiv:2506.07962, ICML 2025, CC BY 4.0) — the Phase 1 F4 pivot: model a
continuous per-model trait, not raw item-level binary responses.

Sources (in ``datasets/kim/``):
- ``helm/model_accuracy.csv`` — 71 models, MMLU accuracy (HELM scenario).
- ``hugging_face/hf_model_accuracy.csv`` — 451 models, MMLU accuracy
  (HF Open LLM Leaderboard v1).

Coverage gate (decided 2026-08-03): proceed only if >= COVERAGE_BAR_MODELS of
the 47 connected-subset models AND all six families are present; otherwise the
data is insufficient and the fresh-eval-pass fallback must be decided first.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from ..occupancy import FAMILIES, MODELS, QUARTERS

REPO_ROOT = Path(__file__).resolve().parents[3]
KIM_DIR = REPO_ROOT / "datasets" / "kim"

# Bar: >= 50% of the 47 connected-subset models, and all 6 families.
COVERAGE_BAR_MODELS = 24
COVERAGE_BAR_FAMILIES = 6

# Phase 0 full_name -> (source, leaderboard model id).
# Selected so each covered model maps to its canonical open-weights checkpoint
# on the shared MMLU item sets. Models with no canonical checkpoint on either
# board are absent (the leaderboard MMLU data is frozen around 2024).
RECONCILIATION = {
    # Llama
    "Llama-2": ("helm", "meta/llama-2-70b"),
    "Llama-3": ("helm", "meta/llama-3-70b"),
    "Llama-3.1": ("helm", "meta/llama-3.1-70b-instruct-turbo"),
    "Llama-3.2": ("helm", "meta/llama-3.2-90b-vision-instruct-turbo"),
    "Llama-3.3": ("hf", "meta-llama/Llama-3.3-70B-Instruct"),
    # Qwen
    "Qwen1.5": ("helm", "qwen/qwen1.5-72b"),
    "Qwen2": ("helm", "qwen/qwen2-72b-instruct"),
    "Qwen2.5": ("hf", "Qwen/Qwen2.5-72B-Instruct"),
    # Mistral
    "Mistral-7B": ("helm", "mistralai/mistral-7b-instruct-v0.3"),
    "Mixtral-8x7B": ("helm", "mistralai/mixtral-8x7b-32kseqlen"),
    "Mixtral-8x22B": ("helm", "mistralai/mixtral-8x22b"),
    "Mistral-Large-2": ("helm", "mistralai/mistral-large-2407"),
    "Mistral-Small-2": ("hf", "mistralai/Mistral-Small-Instruct-2409"),
    # Phi
    "Phi-2": ("helm", "microsoft/phi-2"),
    "Phi-3": ("helm", "microsoft/phi-3-medium-4k-instruct"),
    "Phi-3.5": ("hf", "microsoft/Phi-3.5-mini-instruct"),
    # Gemma
    "Gemma-1": ("helm", "google/gemma-7b"),
    "Gemma-2": ("helm", "google/gemma-2-9b"),
}


def load_kim_data(kim_dir: Path = KIM_DIR) -> dict[str, pd.DataFrame]:
    """Load the Kim et al. MMLU accuracy files into a dict of DataFrames."""
    helm = pd.read_csv(kim_dir / "model_accuracy.csv")
    helm.columns = ["idx", "model", "accuracy"]
    helm = helm[["model", "accuracy"]]

    hf = pd.read_csv(kim_dir / "hf_model_accuracy.csv", header=None)
    hf.columns = ["model", "accuracy"]
    hf = hf.dropna()

    return {"helm": helm, "hf": hf}


def reconcile(kim: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Join the Phase 0 table with leaderboard accuracy via RECONCILIATION."""
    table = pd.DataFrame(MODELS, columns=["family", "quarter", "short_name", "full_name"])
    rows = []
    for _, r in table.iterrows():
        src = RECONCILIATION.get(r["full_name"])
        if src is None:
            rows.append({**r.to_dict(), "source": None, "lb_model": None, "accuracy": None})
            continue
        source, lb_id = src
        acc = kim[source].set_index("model").loc[lb_id, "accuracy"]
        rows.append(
            {
                **r.to_dict(),
                "source": source,
                "lb_model": lb_id,
                "accuracy": float(acc),
            }
        )
    out = pd.DataFrame(rows)
    out["covered"] = out["accuracy"].notna()
    return out


def coverage_report(rec: pd.DataFrame) -> dict:
    """Summary of coverage: counts by family, gates, and the verdict."""
    covered = rec[rec["covered"]]
    by_family = covered.groupby("family").size().reindex(FAMILIES).fillna(0).astype(int)
    n_covered = int(covered.shape[0])
    n_total = int(rec.shape[0])
    families_present = set(covered["family"]) if n_covered else set()
    gates = {
        "models": n_covered,
        "models_bar": COVERAGE_BAR_MODELS,
        "models_pass": n_covered >= COVERAGE_BAR_MODELS,
        "families": len(families_present),
        "families_bar": COVERAGE_BAR_FAMILIES,
        "families_pass": len(families_present) >= COVERAGE_BAR_FAMILIES,
        "families_missing": sorted(set(FAMILIES) - families_present),
    }
    gates["pass"] = gates["models_pass"] and gates["families_pass"]
    return {"covered": covered, "by_family": by_family, "n_covered": n_covered,
            "n_total": n_total, "gates": gates}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Phase 2 coverage check")
    ap.add_argument(
        "--out",
        default=str(REPO_ROOT / "datasets" / "phase2_coverage.csv"),
        help="output path for the per-model coverage table",
    )
    args = ap.parse_args(argv)

    if not (KIM_DIR / "model_accuracy.csv").exists():
        raise SystemExit(
            f"Kim data not found under {KIM_DIR}; run the download first "
            "(see Dataset_Inventory.md)."
        )

    rec = reconcile(load_kim_data())
    rep = coverage_report(rec)

    out = rec.sort_values(["family", "quarter"])
    out.to_csv(args.out, index=False)

    print(f"Coverage: {rep['n_covered']}/{rep['n_total']} models ({100*rep['n_covered']/rep['n_total']:.1f}%)")
    print("By family:", dict(rep["by_family"]))
    print("Gates:", rep["gates"])
    print(f"VERDICT: {'PASS — proceed to trait assembly' if rep['gates']['pass'] else 'FAIL — stop; decide fresh eval pass'}")
    print(f"Wrote per-model table to {args.out}")


if __name__ == "__main__":
    main()
