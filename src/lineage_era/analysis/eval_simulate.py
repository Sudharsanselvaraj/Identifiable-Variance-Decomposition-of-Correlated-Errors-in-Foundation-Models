"""Shape-exact simulated eval output for offline pipeline dry-runs.

Generates ``phase2_eval_results.sim.csv`` + ``eval_samples.sim/`` (or any
``--csv`` / ``--samples-dir``) in the exact shape the GPU runbook would
produce (``phase2_eval.append_result`` / ``write_samples``), so the full Phase 2
chain — trait assembly, identifiability gate, decomposition, bootstrap,
sensitivity, error-similarity panel — can be exercised end to end with NO GPU.

Per-model ``correct`` flags come from a per-question choice DGP with known
structure: family + era + model effects with the scenario variance shares on
the ACCURACY scale (the scale the Phase 2 estimator decomposes) and shared item
difficulties, over one common item set (register A15). The measured trait is the
per-model mean accuracy. Single-seed recovery of the shares is noisy at the real
6-family occupancy (Phase 1 register A21), so the round-trip test asserts
mechanism plus mean-over-seeds directionality — never a single-dataset claim.

Writes NEVER clobber the real ``datasets/phase2_eval_results.csv`` /
``datasets/eval_samples/`` (distinct ``.sim`` defaults).

Usage (from src/):
    python3 -m lineage_era.phase2_eval_simulate --scenario A --n-items 2000
    python3 -m lineage_era.phase2_decomposition \
        --eval-csv ../datasets/phase2_eval_results.sim.csv \
        --samples-dir ../datasets/eval_samples.sim/
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from .. import dgp
from ..occupancy import model_table
from ..phase2_eval import EVAL_MANIFEST

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASETS = REPO_ROOT / "datasets"
DEFAULT_CSV = DATASETS / "phase2_eval_results.sim.csv"
DEFAULT_SAMPLES_DIR = DATASETS / "eval_samples.sim"

MMLU_SUBJECTS = [
    "abstract algebra", "anatomy", "astronomy", "business ethics",
    "clinical knowledge", "college biology", "college chemistry",
    "college computer science", "college mathematics", "college medicine",
    "college physics", "computer security", "conceptual physics",
    "econometrics", "electrical engineering", "elementary mathematics",
    "formal logic", "global facts", "high school biology",
    "high school chemistry", "high school computer science",
    "high school european history", "high school geography",
    "high school government and politics", "high school macroeconomics",
    "high school mathematics", "high school microeconomics",
    "high school physics", "high school psychology", "high school statistics",
    "high school us history", "high school world history", "human aging",
    "human sexuality", "international law", "jurisprudence",
    "logical fallacies", "machine learning", "management", "marketing",
    "medical genetics", "miscellaneous", "moral disputes", "moral scenarios",
    "nutrition", "philosophy", "prehistory", "professional accounting",
    "professional law", "professional medicine", "professional psychology",
    "public relations", "security studies", "sociology", "us foreign policy",
    "virology", "world religions",
]


def _invlogit(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def build_items(n_items: int, rng: np.random.Generator) -> list[dict]:
    """One shared question set (A15): question, subject, gold answer index."""
    return [
        {
            "question": f"q{i:06d}",
            "subject": MMLU_SUBJECTS[i % len(MMLU_SUBJECTS)],
            "choices": [f"choice {k}" for k in range(4)],
            "answer": 0,
        }
        for i in range(n_items)
    ]


def simulate_eval(scenario: dict | None = None, n_items: int = 2000,
                  seed: int = 0, mu: float = 0.55, tot_var: float = 0.01,
                  diff_sd: float = 0.5,
                  csv_path: Path = DEFAULT_CSV,
                  samples_dir: Path = DEFAULT_SAMPLES_DIR,
                  write_samples: bool = True,
                  drop: list[str] | None = None) -> dict:
    """Write shape-exact simulated eval output; return the report.

    ``scenario`` gives the L/E/U variance shares; they are placed on the
    accuracy scale via ``tot_var`` (the total between-model accuracy variance).
    ``drop`` removes models from the CSV (and skips their JSONL) to exercise
    the validator's fail-fast path.
    """
    if scenario is None:
        scenario = dgp.SCENARIOS["A"]
    s2_L = scenario["L"] * tot_var
    s2_E = scenario["E"] * tot_var
    s2_U = scenario["U"] * tot_var
    rng = np.random.default_rng(seed)
    design = model_table()
    fam = design["family"].tolist()
    era = design["quarter"].tolist()
    full = design["full_name"].tolist()
    if drop:
        keep = [fn for fn in full if fn not in drop]
    else:
        keep = full

    # Accuracy-scale effects: trait_m = mu + alpha_f + beta_e + u_m is exactly
    # the additive structure the Phase 2 estimator decomposes.
    alpha = {f: rng.normal(0.0, np.sqrt(s2_L))
             for f in design["family"].unique()}
    beta = {e: rng.normal(0.0, np.sqrt(s2_E))
            for e in design["quarter"].unique()}
    u = {fn: rng.normal(0.0, np.sqrt(s2_U)) for fn in full}
    delta = rng.normal(0.0, diff_sd, n_items)

    items = build_items(n_items, rng)
    rows_csv = []
    per_model = {}
    for fn in keep:
        acc = min(max(mu + alpha[fam[full.index(fn)]] + beta[era[full.index(fn)]]
                      + u[fn], 0.03), 0.97)
        lp_mu = np.log(acc / (1.0 - acc))
        correct = []
        logprobs = []
        for i, it in enumerate(items):
            p = _invlogit(lp_mu + delta[i])
            correct.append(int(rng.random() < p))
            # Shape-faithful predicted/logprobs: gold choice gets the item
            # score, distractors independent draws (a 4-way choice model).
            lp = [lp_mu + delta[i], rng.normal(0.0, 1.0),
                  rng.normal(0.0, 1.0), rng.normal(0.0, 1.0)]
            logprobs.append(lp)
        repo = EVAL_MANIFEST[fn][0]
        rows_csv.append({
            "date": date.today().isoformat(),
            "full_name": fn,
            "hf_repo": repo,
            "benchmark": "mmlu",
            "fewshot": 5,
            "acc": float(np.mean(correct)),
            "acc_norm": float(np.mean(correct)),
            "samples": n_items,
        })
        if write_samples:
            sample_rows = [
                {
                    "full_name": fn,
                    "hf_repo": repo,
                    "subject": it["subject"],
                    "question": it["question"],
                    "choices": json.dumps(it["choices"]),
                    "answer": it["answer"],
                    "predicted": int(max(range(4), key=logprobs[i].__getitem__)),
                    "correct": correct[i],
                    "choice_logprobs": json.dumps(logprobs[i]),
                }
                for i, it in enumerate(items)
            ]
            per_model[fn] = sample_rows

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows_csv).to_csv(csv_path, index=False)
    if write_samples:
        samples_dir.mkdir(parents=True, exist_ok=True)
        for fn, srows in per_model.items():
            repo = EVAL_MANIFEST[fn][0]
            out = samples_dir / f"{fn}__{repo.replace('/', '__')}.jsonl"
            with open(out, "w") as f:
                for r in srows:
                    f.write(json.dumps(r) + "\n")
    return {
        "scenario": scenario,
        "n_models": len(rows_csv),
        "n_items": n_items,
        "csv": csv_path,
        "samples_dir": samples_dir,
        "samples_written": write_samples,
        "acc_mean": float(np.mean([r["acc"] for r in rows_csv])),
        "acc_min": float(min(r["acc"] for r in rows_csv)),
        "acc_max": float(max(r["acc"] for r in rows_csv)),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", choices=["A", "B", "C"], default="A",
                   help="variance scenario (L/E/U) for the generating effects")
    p.add_argument("--n-items", type=int, default=2000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--csv", default=str(DEFAULT_CSV))
    p.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR))
    p.add_argument("--no-samples", action="store_true",
                   help="write the CSV only (exercise the binomial-SE path)")
    p.add_argument("--drop", default=None,
                   help="comma-separated full_names to omit (validator fail-fast)")
    args = p.parse_args(argv)

    drop = [s.strip() for s in args.drop.split(",")] if args.drop else None
    rep = simulate_eval(
        scenario=dgp.SCENARIOS[args.scenario],
        n_items=args.n_items, seed=args.seed,
        csv_path=Path(args.csv), samples_dir=Path(args.samples_dir),
        write_samples=not args.no_samples, drop=drop,
    )
    print(f"scenario {args.scenario}: {rep['n_models']} models x "
          f"{rep['n_items']} items; acc [{rep['acc_min']:.3f}, "
          f"{rep['acc_max']:.3f}] mean {rep['acc_mean']:.3f}")
    print(f"-> {rep['csv']}")
    if rep["samples_written"]:
        print(f"-> {rep['samples_dir']}/ ({rep['n_models']} JSONL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
