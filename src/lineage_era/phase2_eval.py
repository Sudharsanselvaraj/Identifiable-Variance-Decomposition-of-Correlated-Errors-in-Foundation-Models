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
    python3 -m lineage_era.phase2_eval --model Llama-3.3 --quant 4bit --resume   # resume-safe
    python3 -m lineage_era.phase2_eval --all --quant 4bit --resume --device cuda:0  # whole roster

Each result row carries a fidelity column (bf16/fp16/4bit/8bit/default) so the
trait pipeline knows which models ran at reduced precision. --resume skips any
model already recorded in the results CSV; --all runs the whole manifest,
skipping gated models without an accepted HF_TOKEN and continuing past
individual failures (for long one-shot rented sessions).

Gated models (access="gated") require a Hugging Face token with the model
license accepted: set HF_TOKEN in the environment. The 70B+/MoE models
(DeepSeek, Llama-3.2-90B, Mistral-Large, Qwen 72B, ...) need a GPU host; this
module only orchestrates, it does not care where it runs.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

from .occupancy import FAMILIES, MODELS

DATASETS = Path(__file__).resolve().parents[2] / "datasets"
RESULTS_CSV = DATASETS / "phase2_eval_results.csv"
SAMPLES_DIR = DATASETS / "eval_samples"

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


def _model_args(full_name: str, repo: str | None, dtype: str | None, attn: str,
                quant: str = "none") -> str:
    if repo is None:
        repo = EVAL_MANIFEST[full_name][0]
    args = f"pretrained={repo},trust_remote_code=True,attn_implementation={attn}"
    extra = EXTRA_MODEL_ARGS.get(full_name)
    if extra:
        args += f",{extra}"
    if dtype:
        args += f",dtype={dtype}"
    if quant == "4bit":
        args += ",load_in_4bit=True"
    elif quant == "8bit":
        args += ",load_in_8bit=True"
    return args


def fidelity_label(dtype: str | None, quant: str) -> str:
    """Fidelity tag stored on each eval row for downstream provenance."""
    if quant == "4bit":
        return "4bit"
    if quant == "8bit":
        return "8bit"
    if dtype == "bfloat16":
        return "bf16"
    if dtype == "float16":
        return "fp16"
    return "default"


def already_done(full_name: str, repo: str) -> bool:
    """True when (full_name, repo) already has a row in the results CSV."""
    if not RESULTS_CSV.exists():
        return False
    with open(RESULTS_CSV) as f:
        for row in csv.DictReader(f):
            if row.get("full_name") == full_name and row.get("hf_repo", "") == repo:
                return True
    return False


def _samples_to_rows(full_name: str, repo: str, samples: dict) -> list[dict]:
    """Flatten lm_eval per-task samples into one row per question.

    Keeps item-level data (model_id, question, subject, gold answer, predicted
    choice, per-choice logprobs) so the Phase 2 engine can do question-level
    bootstrap, subject-wise decomposition, and item-level GLMM robustness
    without re-running the GPU evals.
    """
    rows = []
    for task, task_samples in samples.items():
        subject = task.removeprefix("mmlu_").replace("_", " ")
        for s in task_samples:
            doc = s.get("doc", {})
            resps = s.get("resps")
            logprobs = []
            if resps:
                logprobs = [float(r[0]) if isinstance(r, (list, tuple)) else float(r)
                            for r in resps]
            predicted = None
            if logprobs:
                predicted = int(max(range(len(logprobs)), key=logprobs.__getitem__))
            answer = doc.get("answer")
            rows.append({
                "full_name": full_name,
                "hf_repo": repo,
                "subject": doc.get("subject") or subject,
                "question": doc.get("question", ""),
                "choices": json.dumps(doc.get("choices", [])),
                "answer": answer,
                "predicted": predicted,
                "correct": int(predicted == answer) if answer is not None else None,
                "choice_logprobs": json.dumps(logprobs),
            })
    return rows


def write_samples(full_name: str, repo: str, samples: dict) -> Path | None:
    """Append per-question JSONL for one model under datasets/eval_samples/."""
    rows = _samples_to_rows(full_name, repo, samples)
    if not rows:
        return None
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    out = SAMPLES_DIR / f"{full_name}__{repo.replace('/', '__')}.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return out


def run_mmlu(full_name: str, limit: int | None, device: str, dtype: str | None,
             attn: str, repo: str | None, batch: int | str, quant: str = "none",
             log_samples: bool = True) -> dict:
    from lm_eval import simple_evaluate

    kwargs = dict(
        model="hf",
        model_args=_model_args(full_name, repo, dtype, attn, quant),
        tasks=["mmlu"],
        num_fewshot=5,
        device=device,
        batch_size=batch,
        log_samples=log_samples,
    )
    if limit is not None:
        kwargs["limit"] = limit
    results = simple_evaluate(**kwargs)
    res = results["results"]["mmlu"]
    if log_samples and "samples" in results:
        rrepo = repo if repo is not None else EVAL_MANIFEST[full_name][0]
        out = write_samples(full_name, rrepo, results["samples"])
        if out is not None:
            print(f"wrote {out.stat().st_size / 1e6:.1f} MB of question samples -> {out}")
    return {
        "acc": res.get("acc,none"),
        "acc_norm": res.get("acc_norm,none"),
        "samples": res.get("samples"),
    }


def append_result(full_name: str, stats: dict, repo: str | None = None,
                  fidelity: str = "default") -> None:
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
        "fidelity": fidelity,
    }
    if RESULTS_CSV.exists():
        with open(RESULTS_CSV) as f:
            header = next(csv.reader(f), [])
        if "fidelity" not in header:
            raise SystemExit(
                f"{RESULTS_CSV} exists without a 'fidelity' column; move/delete it "
                "and re-run (no real eval rows exist yet)."
            )
    new = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"appended {full_name} (fidelity={fidelity}) -> {RESULTS_CSV}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", action="store_true", help="print the 47-model manifest")
    p.add_argument("--all", action="store_true",
                   help="run the whole manifest (resume-safe, keeps going on failures)")
    p.add_argument("--model", help="connected-subset full_name, e.g. Phi-2")
    p.add_argument("--repo", default=None, help="override HF repo (pilot non-members)")
    p.add_argument("--limit", type=int, default=None, help="eval subset (pilot only)")
    p.add_argument("--device", default="mps", help="mps | cpu | cuda:0")
    p.add_argument("--dtype", default=None, help="e.g. bfloat16, float16")
    p.add_argument("--quant", default="none", choices=["none", "8bit", "4bit"],
                   help="load_in_8bit/load_in_4bit (needs bitsandbytes)")
    p.add_argument("--attn", default="eager", help="eager | sdpa (eager avoids MPS buffer errors)")
    p.add_argument("--batch", default="auto", help="batch size; 2-8 on CPU/MPS pilots")
    p.add_argument("--resume", action="store_true",
                   help="skip models already recorded in the results CSV")
    p.add_argument("--force", action="store_true",
                   help="ignore --resume and re-run even if already recorded")
    p.add_argument("--no-samples", action="store_true",
                   help="skip per-question JSONL capture (aggregate CSV only)")
    args = p.parse_args(argv)

    if args.manifest:
        print_manifest()
        return 0

    def run_one(full_name: str, repo: str | None = None) -> None:
        rrepo = repo if repo is not None else EVAL_MANIFEST[full_name][0]
        if args.resume and not args.force and already_done(full_name, rrepo):
            print(f"skip {full_name} (already recorded)")
            return
        stats = run_mmlu(full_name, args.limit, args.device, args.dtype,
                         args.attn, repo, batch, args.quant,
                         log_samples=not args.no_samples)
        print(f"{full_name}: acc={stats['acc']} acc_norm={stats['acc_norm']} "
              f"({stats['samples']} samples)")
        append_result(full_name, stats, repo,
                      fidelity=fidelity_label(args.dtype, args.quant))

    batch = int(args.batch) if args.batch.isdigit() else args.batch

    if args.all:
        if args.limit is not None:
            p.error("--limit is a single-model pilot; not valid with --all")
        done = failed = skipped = 0
        for full_name, (repo, _size, access) in EVAL_MANIFEST.items():
            if args.resume and not args.force and already_done(full_name, repo):
                skipped += 1
                continue
            if access == "gated" and "HF_TOKEN" not in os.environ:
                print(f"skip {full_name} (gated; no HF_TOKEN)", file=sys.stderr)
                skipped += 1
                continue
            try:
                run_one(full_name)
                done += 1
            except Exception as e:  # noqa: BLE001 -- keep the batch going
                failed += 1
                print(f"FAILED {full_name}: {e}", file=sys.stderr)
        print(f"\n--all done: {done} evaluated, {skipped} skipped, {failed} failed.")
        return 0 if failed == 0 else 1

    if args.model is None:
        p.error("--model is required (or use --manifest / --all)")
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

    run_one(args.model, args.repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
