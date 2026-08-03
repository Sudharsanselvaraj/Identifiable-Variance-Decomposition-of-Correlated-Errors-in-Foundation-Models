"""Run the full Phase 2 eval pass (MMLU 5-shot on all 47 connected-subset
models) on a GPU host, with resume.

This is the artifact the user runs where compute lives (decision 2026-08-03).
It loops the manifest in `phase2_eval.py`, skips models already present in
`datasets/phase2_eval_results.csv`, and continues past per-model failures.

Usage (from src/, on the GPU host, python3.11 + lm_eval + accelerate installed):

    export HF_TOKEN=hf_...        # for the 24 gated models (licenses accepted)
    python3 -m lineage_era.phase2_run_all --device cuda:0

Options:
    --device       default cuda:0
    --dtype        default bfloat16
    --attn         default sdpa (sdpa implements sliding-window attention;
                   required for Qwen/Mistral/DeepSeek/Gemma on GPU)
    --batch        lm-eval batch size, default auto
    --only NAME    run a single connected-subset model, e.g. "Phi-2"
    --skip-gated   skip the 24 gated models (no HF_TOKEN needed); implies the
                   coverage will be 23/47
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback

from .occupancy import MODELS
from .phase2_eval import (
    EVAL_MANIFEST,
    RESULTS_CSV,
    append_result,
    run_mmlu,
)

RESULTS_FIELDS = [
    "date", "full_name", "hf_repo", "benchmark", "fewshot",
    "acc", "acc_norm", "samples",
]


def done_models() -> set[str]:
    if not RESULTS_CSV.exists():
        return set()
    with open(RESULTS_CSV) as f:
        return {r["full_name"] for r in csv.DictReader(f) if r["full_name"]}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--attn", default="sdpa")
    p.add_argument("--batch", default="auto")
    p.add_argument("--only", default=None, help="run one model")
    p.add_argument("--skip-gated", action="store_true")
    p.add_argument("--no-samples", action="store_true",
                   help="skip per-question JSONL capture (aggregate CSV only)")
    args = p.parse_args(argv)

    if args.only is not None and args.only not in EVAL_MANIFEST:
        p.error(f"{args.only!r} not in EVAL_MANIFEST")
    if args.skip_gated and "HF_TOKEN" not in os.environ:
        print("--skip-gated: no HF_TOKEN required (gated models will be skipped)")

    targets = (
        [args.only]
        if args.only is not None
        else [m[3] for m in MODELS]
    )
    already = done_models()
    batch = int(args.batch) if args.batch.isdigit() else args.batch

    print(f"device={args.device} dtype={args.dtype} attn={args.attn} "
          f"batch={batch} | {len(targets)} target models, "
          f"{len(targets) - len([t for t in targets if t in already])} to run",
          flush=True)

    ok = fail = skipped = 0
    for full_name in targets:
        if full_name in already:
            print(f"[skip] {full_name} already in {RESULTS_CSV.name}", flush=True)
            continue
        access = EVAL_MANIFEST[full_name][2]
        if access == "gated" and args.skip_gated:
            print(f"[skip-gated] {full_name}", flush=True)
            skipped += 1
            continue
        print(f"[run] {full_name} ({EVAL_MANIFEST[full_name][0]}, {access})",
              flush=True)
        try:
            stats = run_mmlu(full_name, None, args.device, args.dtype,
                             args.attn, None, batch,
                             log_samples=not args.no_samples)
            print(f"[ok] {full_name}: acc={stats['acc']} "
                  f"acc_norm={stats['acc_norm']} ({stats['samples']} samples)",
                  flush=True)
            append_result(full_name, stats)
            ok += 1
        except Exception as e:  # noqa: BLE001 - keep the run going
            print(f"[fail] {full_name}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc(file=sys.stderr)
            fail += 1

    print(f"\nDONE: {ok} ok, {fail} failed, {skipped} skipped-gated, "
          f"{len(already)} already present -> {RESULTS_CSV}", flush=True)
    if ok + fail + skipped == 0:
        print("Nothing to do.", flush=True)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
