"""Phase 2 fresh evaluation pass: MMLU 5-shot on the 47-model connected subset.

Decision (2026-08-03): coverage from leaderboard data is only 18/47 and the 29
gaps are unreachable from public leaderboards, so the per-model trait is
produced by a FRESH evaluation of all 47 connected-subset models on one fixed
benchmark (MMLU 5-shot) -- a strict common item set. This module holds the
canonical Hugging Face checkpoint for each connected-subset model, its access
class, and a thin runner over lm-eval-harness.

Runner usage (from src/):
    python3 -m lineage_era.phase2_eval --manifest          # print the 47-model manifest
    python3 -m lineage_era.phase2_eval --model Phi-2 --limit 100   # pilot
    python3 -m lineage_era.phase2_eval --model Phi-2       # full MMLU 5-shot
    python3 -m lineage_era.phase2_eval --model Llama-3.3 --device cuda:0

Gated models (access="gated") require a Hugging Face token with the model
license accepted: set HF_TOKEN in the environment. The 70B+/MoE models
(DeepSeek, Llama-3.2-90B, Mistral-Large, Qwen 72B, ...) need a GPU host; this
module only orchestrates, it does not care where it runs.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

from .occupancy import FAMILIES, MODELS

DATASETS = Path(__file__).resolve().parents[2] / "datasets"
RESULTS_CSV = DATASETS / "phase2_eval_results.csv"

# full_name -> (hf repo, approximate params, access).
# access: "public" = token-free; "gated" = HF token + license acceptance.
EVAL_MANIFEST = {
    # Llama
    "Llama-1": ("meta-llama/Llama-1", "7B", "gated"),
    "Llama-2": ("meta-llama/Llama-2-70b-hf", "70B", "gated"),
    "Llama-3": ("meta-llama/Meta-Llama-3-70B-Instruct", "70B", "gated"),
    "Llama-3.1": ("meta-llama/Meta-Llama-3.1-70B-Instruct", "70B", "gated"),
    "Llama-3.2": ("meta-llama/Llama-3.2-90B-Vision-Instruct", "90B", "gated"),
    "Llama-3.3": ("meta-llama/Llama-3.3-70B-Instruct", "70B", "gated"),
    "Llama-4": ("meta-llama/Llama-4-Maverick-17B-128E-Instruct", "17B/128E", "gated"),
    # Qwen
    "Qwen-7B": ("Qwen/Qwen-7B", "7B", "public"),
    "Qwen1.5": ("Qwen/Qwen1.5-72B-Chat", "72B", "public"),
    "Qwen2": ("Qwen/Qwen2-72B-Instruct", "72B", "public"),
    "Qwen2.5": ("Qwen/Qwen2.5-72B-Instruct", "72B", "public"),
    "Qwen3": ("Qwen/Qwen3-30B-A3B-Instruct", "30B/3B", "gated"),
    "Qwen3.5": ("Qwen/Qwen3.5-32B", "32B", "gated"),
    "Qwen3.6": ("Qwen/Qwen3.6-32B", "32B", "gated"),
    # DeepSeek
    "DeepSeek-V3": ("deepseek-ai/DeepSeek-V3", "671B/37B", "public"),
    "DeepSeek-R1": ("deepseek-ai/DeepSeek-R1", "671B/37B", "public"),
    "DeepSeek-V3.1": ("deepseek-ai/DeepSeek-V3.1", "671B/37B", "public"),
    "DeepSeek-V3.2": ("deepseek-ai/DeepSeek-V3.2", "685B/37B", "public"),
    "DeepSeek-V4": ("deepseek-ai/DeepSeek-V4", "~700B", "gated"),
    # Mistral
    "Mistral-7B": ("mistralai/Mistral-7B-Instruct-v0.3", "7B", "public"),
    "Mixtral-8x7B": ("mistralai/Mixtral-8x7B-Instruct-v0.1", "46B/13B", "public"),
    "Mixtral-8x22B": ("mistralai/Mixtral-8x22B-Instruct-v0.1", "141B/39B", "public"),
    "Mistral-Large-2": ("mistralai/Mistral-Large-2407", "123B", "gated"),
    "Mistral-Small-2": ("mistralai/Mistral-Small-Instruct-2409", "24B", "public"),
    "Mistral-Small-3": ("mistralai/Mistral-Small-3-24B-Instruct-2501", "24B", "gated"),
    "Mistral-Small-3.1": ("mistralai/Mistral-Small-3.1-24B-Instruct-2503", "24B", "public"),
    "Mistral-Medium-3": ("mistralai/Mistral-Medium-3.1-32B-Instruct-2503", "32B", "gated"),
    "Mistral-Small-3.2": ("mistralai/Mistral-Small-3.2-24B-Instruct-2510", "24B", "gated"),
    "Mistral-Large-3": ("mistralai/Mistral-Large-3", "123B", "public"),
    "Ministral-3": ("mistralai/Ministral-3B-Instruct", "3B", "gated"),
    "Devstral-2": ("mistralai/Devstral-Small-2509", "24B", "gated"),
    "Mistral-Small-4": ("mistralai/Mistral-Small-4-32B-Instruct-2603", "32B", "gated"),
    "Mistral-Medium-3.5": ("mistralai/Mistral-Medium-3.5", "32B", "gated"),
    # Phi
    "Phi-1": ("microsoft/phi-1", "1.3B", "public"),
    "Phi-1.5": ("microsoft/phi-1_5", "1.3B", "public"),
    "Phi-2": ("microsoft/phi-2", "2.7B", "public"),
    "Phi-3": ("microsoft/Phi-3-medium-4k-instruct", "14B", "public"),
    "Phi-3.5": ("microsoft/Phi-3.5-mini-instruct", "3.8B", "public"),
    "Phi-4": ("microsoft/Phi-4-mini-instruct", "3.8B", "public"),
    "Phi-4-reasoning-plus": ("microsoft/Phi-4-reasoning-plus", "11B", "public"),
    "Phi-4-reasoning-vision-15B": ("microsoft/Phi-4-reasoning-vision-15B", "15B", "public"),
    # Gemma
    "Gemma-1": ("google/gemma-7b", "7B", "gated"),
    "Gemma-2": ("google/gemma-2-9b", "9B", "gated"),
    "Gemma-3": ("google/gemma-3-27b-it", "27B", "gated"),
    "Gemma-3n": ("google/gemma-3n-4b-it", "4B", "gated"),
    "Gemma-4": ("google/gemma-4", "~12B", "gated"),
    "Gemma-4-12B": ("google/gemma-4-12b-it", "12B", "public"),
}

# Design sanity: manifest must cover every connected-subset model.
assert set(EVAL_MANIFEST) == {m[3] for m in MODELS}, (
    "EVAL_MANIFEST != occupancy.MODELS"
)

# Extra lm-eval HF model_args per connected-subset model. Phi-1/1.5/2 are
# 2048-token context; some MMLU 5-shot prompts exceed it, so truncate to their
# native context (their papers' MMLU values are also at 2048).
EXTRA_MODEL_ARGS = {
    "Phi-1": "max_length=2048,truncation=True",
    "Phi-1.5": "max_length=2048,truncation=True",
    "Phi-2": "max_length=2048,truncation=True",
}


def manifest_table() -> list[dict]:
    rows = []
    for family, quarter, short, full in MODELS:
        repo, size, access = EVAL_MANIFEST[full]
        rows.append(
            {
                "family": family,
                "quarter": quarter,
                "short_name": short,
                "full_name": full,
                "hf_repo": repo,
                "params": size,
                "access": access,
            }
        )
    return rows


def print_manifest() -> None:
    rows = manifest_table()
    print(f"{'family':9s} {'quarter':8s} {'full_name':28s} {'hf_repo':55s} {'params':10s} {'access'}")
    for r in rows:
        print(
            f"{r['family']:9s} {r['quarter']:8s} {r['full_name']:28s} "
            f"{r['hf_repo']:55s} {r['params']:10s} {r['access']}"
        )
    n_public = sum(r["access"] == "public" for r in rows)
    print(f"\n{n_public}/47 token-free; 47/47 manifest complete.")


def _model_args(full_name: str, repo: str | None, dtype: str | None, attn: str) -> str:
    if repo is None:
        repo = EVAL_MANIFEST[full_name][0]
    args = f"pretrained={repo},trust_remote_code=True,attn_implementation={attn}"
    extra = EXTRA_MODEL_ARGS.get(full_name)
    if extra:
        args += f",{extra}"
    if dtype:
        args += f",dtype={dtype}"
    return args


def run_mmlu(full_name: str, limit: int | None, device: str, dtype: str | None,
             attn: str, repo: str | None, batch: int | str) -> dict:
    from lm_eval import simple_evaluate

    kwargs = dict(
        model="hf",
        model_args=_model_args(full_name, repo, dtype, attn),
        tasks=["mmlu"],
        num_fewshot=5,
        device=device,
        batch_size=batch,
        log_samples=False,
    )
    if limit is not None:
        kwargs["limit"] = limit
    results = simple_evaluate(**kwargs)
    res = results["results"]["mmlu"]
    return {
        "acc": res.get("acc,none"),
        "acc_norm": res.get("acc_norm,none"),
        "samples": res.get("samples"),
    }


def append_result(full_name: str, stats: dict, repo: str | None = None) -> None:
    if repo is None:
        repo = EVAL_MANIFEST[full_name][0]
    row = {
        "date": date.today().isoformat(),
        "full_name": full_name,
        "hf_repo": repo,
        "benchmark": "mmlu",
        "fewshot": 5,
        "acc": stats["acc"],
        "acc_norm": stats["acc_norm"],
        "samples": stats["samples"],
    }
    new = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"appended {full_name} -> {RESULTS_CSV}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", action="store_true", help="print the 47-model manifest")
    p.add_argument("--model", help="connected-subset full_name, e.g. Phi-2")
    p.add_argument("--repo", default=None, help="override HF repo (pilot non-members)")
    p.add_argument("--limit", type=int, default=None, help="eval subset (pilot only)")
    p.add_argument("--device", default="mps", help="mps | cpu | cuda:0")
    p.add_argument("--dtype", default=None, help="e.g. bfloat16, float16")
    p.add_argument("--attn", default="eager", help="eager | sdpa (eager avoids MPS buffer errors)")
    p.add_argument("--batch", default="auto", help="batch size; 2-8 on CPU/MPS pilots")
    args = p.parse_args(argv)

    if args.manifest:
        print_manifest()
        return 0
    if args.model is None:
        p.error("--model is required (or use --manifest)")
    if args.model not in EVAL_MANIFEST and args.repo is None:
        p.error(f"{args.model!r} not in EVAL_MANIFEST (pass --repo for a pilot)")
    if args.repo is not None and args.limit is None:
        p.error("--repo pilots must set --limit")
    if args.model != "Phi-2" and args.limit is not None:
        print(
            f"WARNING: --limit {args.limit} is a pipeline pilot; "
            "full MMLU 5-shot is the trait source.",
            file=sys.stderr,
        )
    if "HF_TOKEN" not in os.environ and args.repo is None \
            and EVAL_MANIFEST[args.model][2] == "gated":
        p.error(f"{args.model} is gated; set HF_TOKEN (license accepted).")

    batch = int(args.batch) if args.batch.isdigit() else args.batch
    stats = run_mmlu(args.model, args.limit, args.device, args.dtype, args.attn,
                     args.repo, batch)
    print(f"{args.model}: acc={stats['acc']} acc_norm={stats['acc_norm']} "
          f"({stats['samples']} samples)")
    append_result(args.model, stats, args.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
