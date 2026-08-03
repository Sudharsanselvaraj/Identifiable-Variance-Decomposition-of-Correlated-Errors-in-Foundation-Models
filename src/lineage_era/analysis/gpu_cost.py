"""Phase 2 GPU cost estimate for the fresh MMLU 5-shot eval (Path A).

Converts the 47-model ``EVAL_MANIFEST`` into a per-model compute/memory plan so
the eval venue decision (rent a node? which class?) is informed. Numbers are
PLANNING estimates, not benchmarks:

- Memory: total params x bytes (bf16 = 2 B/param, fp8 = 1 B/param); usable
  capacity taken as 74/130 GB of an 80/141 GB GPU. MoE totals come from
  ``TOTAL_PARAMS_OVERRIDE`` where the manifest's first figure is ACTIVE params
  (DeepSeek, Llama-4 Maverick).
- Runtime: MMLU 5-shot loglikelihood is compute-bound on ACTIVE params. Budget
  ~14,042 test questions x ~455 scored tokens each ~= 6.4M forward tokens per
  model; at ~0.15 PFLOPS effective (A100/H100-class bf16, batch=auto, realistic
  overhead) -> est_minutes_single_gpu. Divide by GPUs when packed.

The eval is loglikelihood (no generation), so it is memory-bound, not
compute-bound; the real gate is the 24 gated models (HF token + accepted
license), enumerated in ``access`` / ``org``.

Usage (from src/):
    python3 -m lineage_era.phase2_gpu_cost [--out ../datasets/coverage/gpu_cost_estimate.csv]
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from ..occupancy import MODELS
from ..phase2_eval import EVAL_MANIFEST

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = REPO_ROOT / "datasets" / "coverage" / "gpu_cost_estimate.csv"

# Manifest params strings that report ACTIVE (or active/expert-count) params;
# the TOTAL drives memory. Public figures, 2026-08-03.
TOTAL_PARAMS_OVERRIDE = {
    "Llama-4": 400.0,   # Maverick 17B active / 128E, ~400B total
    "DeepSeek-V4": 700.0,  # ~700B total, class approx
}
# Active params where the manifest's "X/Y" second figure is not active params.
ACTIVE_PARAMS_OVERRIDE = {
    "Llama-4": 17.0,
    "DeepSeek-V4": 37.0,  # ~37B active class, approx
}

# 80GB / 141GB cards, usable capacity after KV cache + activations.
USABLE_80GB = 74.0
USABLE_141GB = 130.0

# MMLU test set size x approx scored tokens per question (5-shot context +
# choice continuations); loglikelihood only.
MMLU_TOKENS = 14_042 * 455
EFFECTIVE_PFLOPS = 0.15  # A100/H100-class bf16, batch=auto, realistic overhead


def parse_params(full_name: str, params: str) -> tuple[float, float]:
    """Return (total_params_b, active_params_b) from a manifest params string."""
    raw = params.strip().lower()
    total = TOTAL_PARAMS_OVERRIDE.get(full_name)
    if total is None:
        first = raw.split("/")[0]
        total = float(first.replace("~", "").replace("b", ""))
    active = ACTIVE_PARAMS_OVERRIDE.get(full_name)
    if active is None:
        if "/" in raw:
            second = raw.split("/")[1]
            if second.endswith("b") and not second.endswith("e"):
                active = float(second.replace("b", ""))
            else:
                active = total
        else:
            active = total
    return total, active


def gpu_plan(total_b: float) -> tuple[float, float, int, int, int]:
    """(weights_gb_bf16, weights_gb_fp8, gpus_80gb_bf16, gpus_80gb_fp8,
    gpus_141gb_fp8)."""
    w_bf16 = total_b * 2.0
    w_fp8 = total_b * 1.0
    return (
        w_bf16,
        w_fp8,
        int(math.ceil(w_bf16 / USABLE_80GB)),
        int(math.ceil(w_fp8 / USABLE_80GB)),
        int(math.ceil(w_fp8 / USABLE_141GB)),
    )


def est_minutes(active_b: float) -> float:
    """Single-GPU-equivalent wall minutes for MMLU 5-shot loglikelihood."""
    flops = 2.0 * active_b * 1e9 * MMLU_TOKENS
    return flops / (EFFECTIVE_PFLOPS * 1e15) / 60.0


def gpu_class(n_bf16: int, n_fp8: int, n_141: int) -> str:
    if n_bf16 <= 1:
        return "1x80GB"
    if n_bf16 <= 2:
        return "2x80GB"
    if n_bf16 <= 4:
        return "4x80GB"
    if n_fp8 <= 8:
        return "8x80GB (fp8)"
    if n_141 <= 8:
        return "8xH200-141GB (fp8)"
    return "multi-node"


def build_cost_table() -> pd.DataFrame:
    rows = []
    for family, quarter, short, full in MODELS:
        repo, params, access = EVAL_MANIFEST[full]
        total, active = parse_params(full, params)
        w_bf16, w_fp8, n_bf16, n_fp8, n_141 = gpu_plan(total)
        rows.append({
            "full_name": full,
            "family": family,
            "quarter": quarter,
            "params": params,
            "access": access,
            "org": repo.split("/")[0],
            "total_params_b": total,
            "active_params_b": active,
            "weights_gb_bf16": w_bf16,
            "gpus_80gb_bf16": n_bf16,
            "weights_gb_fp8": w_fp8,
            "gpus_80gb_fp8": n_fp8,
            "gpus_141gb_fp8": n_141,
            "gpu_class": gpu_class(n_bf16, n_fp8, n_141),
            "est_minutes_single_gpu": est_minutes(active),
        })
    return pd.DataFrame(rows)


def cost_summary(df: pd.DataFrame) -> dict:
    n_public = int((df["access"] == "public").sum())
    n_gated = int((df["access"] == "gated").sum())
    class_counts = df["gpu_class"].value_counts().to_dict()
    single_gpu_hours = float(df["est_minutes_single_gpu"].sum()) / 60.0
    # Packed wall-clock on the recommended node: small/mid on 1-2x80, large on
    # 4x80, DeepSeek-class in fp8 on 8xH200; sequential worst-case is the sum,
    # so report it as a lower bound on parallelism.
    return {
        "n_models": len(df),
        "n_public": n_public,
        "n_gated": n_gated,
        "single_gpu_equiv_hours": single_gpu_hours,
        "classes": class_counts,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    args = p.parse_args(argv)

    df = build_cost_table()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    s = cost_summary(df)
    print(f"gpu cost: {s['n_models']} models "
          f"({s['n_public']} public / {s['n_gated']} gated)")
    print(f"  single-GPU-equivalent total: {s['single_gpu_equiv_hours']:.0f} h "
          "(MMLU 5-shot loglikelihood, ~6.4M tokens/model)")
    print("  classes:", ", ".join(f"{k} x {v}" for k, v in
                                  sorted(s["classes"].items())))
    print("  recommended node: one 8xH200-141GB (fp8) -- small/mid packed on "
          "80GB cards, 70-141B on 4x80GB, DeepSeek 671B-class in fp8; "
          "realistic ~12-24 wall-hours, ~$100-300 for 1-2 days.")
    print("  hard gate is NOT cost: accept licenses for the 24 gated models "
          "(meta-llama, Qwen3+, DeepSeek-V4, Mistral, Google) and set HF_TOKEN.")
    print(f"Wrote per-model plan to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
