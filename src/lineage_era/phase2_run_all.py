"""Run the Phase 2 eval pass (MMLU 5-shot on the G3 minimum valid population,
22 of 47 models) on a GPU host, with resume.

This is the artifact the user runs where compute lives (decision 2026-08-03;
G3 gate 2026-08-03 prescribes `datasets/coverage/minimum_valid_population.csv`,
22 models, unless a bigger run is wanted). It loops the manifest in
`phase2_eval.py`, skips models already present in
`datasets/phase2_eval_results.csv`, and continues past per-model failures.

Usage (from src/, on the GPU host, python3.11 + lm_eval + accelerate installed):

    export HF_TOKEN=hf_...        # for the 8 gated models in the subset
    python3 -m lineage_era.phase2_run_all --device cuda:0
    # or force the full 47-model run:
    python3 -m lineage_era.phase2_run_all --subset datasets/coverage/all_47.csv

Options:
    --device       default cuda:0
    --dtype        default bfloat16
    --attn         default sdpa (sdpa implements sliding-window attention;
                   required for Qwen/Mistral/DeepSeek/Gemma on GPU)
    --batch        lm-eval batch size, default auto
    --only NAME    run a single connected-subset model, e.g. "Phi-2"
    --subset CSV   run only the models whose full_name is in CSV (G3 gate:
                   datasets/coverage/minimum_valid_population.csv). Defaults to
                   that G3 file when present, else the full 47.
    --skip-gated   skip the gated models (no HF_TOKEN needed)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback
from pathlib import Path

from .occupancy import MODELS
from .phase2_eval import (
    EVAL_MANIFEST,
    RESULTS_CSV,
    append_result,
    run_mmlu,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
G3_SUBSET_CSV = REPO_ROOT / "datasets" / "coverage" / "minimum_valid_population.csv"

RESULTS_FIELDS = [
    "date", "full_name", "hf_repo", "benchmark", "fewshot",
    "acc", "acc_norm", "samples",
]


def done_models() -> set[str]:
    if not RESULTS_CSV.exists():
        return set()
    with open(RESULTS_CSV) as f:
        return {r["full_name"] for r in csv.DictReader(f) if r["full_name"]}


def subset_models(csv_path: str) -> list[str]:
    """full_name column of a subset CSV (e.g. the G3 minimal population).

    Respects a ``kept`` boolean column when present (G3 CSV marks dropped
    models); otherwise every full_name row is used.
    """
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    if not rows or "full_name" not in rows[0]:
        raise SystemExit(f"{csv_path}: needs a 'full_name' column")
    names = []
    for r in rows:
        if not r["full_name"]:
            continue
        kept = r.get("kept")
        if kept is not None and kept.strip().lower() == "false":
            continue
        names.append(r["full_name"])
    return names


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--attn", default="sdpa")
    p.add_argument("--batch", default="auto")
    p.add_argument("--only", default=None, help="run one model")
    p.add_argument("--subset", default=str(G3_SUBSET_CSV),
                   help="CSV with a full_name column (G3 minimal population); "
                        "defaults to datasets/coverage/minimum_valid_population.csv")
    p.add_argument("--skip-gated", action="store_true")
    p.add_argument("--no-samples", action="store_true",
                   help="skip per-question JSONL capture (aggregate CSV only)")
    args = p.parse_args(argv)

    if args.only is not None and args.only not in EVAL_MANIFEST:
        p.error(f"{args.only!r} not in EVAL_MANIFEST")
    if args.only is not None and args.subset is not None:
        p.error("--only and --subset are mutually exclusive")
    if args.skip_gated and "HF_TOKEN" not in os.environ:
        print("--skip-gated: no HF_TOKEN required (gated models will be skipped)")

    targets: list[str]
    if args.only is not None:
        targets = [args.only]
    elif args.subset:
        if not Path(args.subset).exists():
            print(f"[g3] subset {args.subset} not found — running the full 47 "
                  "(override with --subset <csv>)", flush=True)
            targets = [m[3] for m in MODELS]
        else:
            targets = subset_models(args.subset)
            bad = sorted({t for t in targets if t not in EVAL_MANIFEST})
            if bad:
                p.error(f"--subset {args.subset}: unknown full_name(s): {bad}")
    else:
        targets = [m[3] for m in MODELS]
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
