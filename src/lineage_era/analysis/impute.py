"""Pre-registered model-based imputation of the DeepSeek trait cells.

Protocol (Research_Decision_Log 2026-08-16, "DeepSeek imputation"): the G3
minimum valid population (22) requires DeepSeek-V3.1 (2025Q3) and
DeepSeek-V3.2 (2025Q4), but their 671B-class memory footprint cannot be
evaluated within the available compute budget (a multi-GPU node is required).
That budget constraint is a PRE-MEASUREMENT availability constraint, not an
outcome-based exclusion.

The two DeepSeek cells are completed by MULTIPLE IMPUTATION from the fitted
variance-components model of the 20 measured models:

    trait ~ mu + family + era + unique

the exact additive structure the Phase 2 estimator decomposes. Per draw m:

  * one family effect alpha ~ N(0, s2_L) SHARED by both DeepSeek models (they
    belong to the same family), drawn from the fitted prior because the
    DeepSeek family has NO measured member in the 22-population;
  * independent era effects ~ N(0, s2_E) for 2025Q3 and 2025Q4 — both target
    cells are prior-dominated (2025Q3 has no measured model at all; 2025Q4 has
    only Devstral-2), so the full fitted era prior is used (conservative);
  * independent model effects ~ N(0, s2_U).

Per-question correctness for the imputed models is generated on the SHARED
measured item set (register A15): per-item difficulty delta_i is the logit of
the measured models' per-item mean correctness, and a per-model offset lambda
is calibrated by bisection so that the model's simulated accuracy equals its
imputed trait. This is the same logistic item model the Phase 1/co-failure DGP
uses; it preserves item-difficulty alignment and subject composition WITHOUT
encoding any fabricated model-model error correlation beyond the trait itself.

Disclosure obligations (binding):
  * the eval CSV rows for the imputed models carry ``fidelity="imputed"``;
  * every table/figure cell for DeepSeek-V3.1 / DeepSeek-V3.2 must be labeled
    "IMPUTED (pre-registered model-based imputation), not measured";
  * the manuscript, runbook, and this report must state that the study is
    measured on 20 models and completed by imputation on 2.

Outputs (never clobber the real datasets/phase2_eval_results.csv or
datasets/eval_samples/ — distinct ``.<label>`` defaults):
  - datasets/phase2_eval_results.<label>.csv   (draw-0 completed dataset: 20
    measured + 2 imputed; imputed rows carry fidelity="imputed")
  - datasets/eval_samples.<label>/             (JSONL for all 22 models)
  - datasets/coverage/imputation_report.<label>.md
  - datasets/coverage/imputed_draws.<label>.csv  (all M predictive draws)

Usage (from src/):
    python3 -m lineage_era.phase2_impute \
        --eval-csv ../datasets/phase2_eval_results.csv \
        --samples-dir ../datasets/eval_samples \
        --label deepseek_imputed --m 5 --seed 2026
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..occupancy import model_table
from ..phase2_eval import EVAL_MANIFEST
from .reml import fit_lpm_vcomp, shares_of

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASETS = REPO_ROOT / "datasets"
DEFAULT_EVAL_CSV = DATASETS / "phase2_eval_results.csv"
DEFAULT_SAMPLES_DIR = DATASETS / "eval_samples"

DEFAULT_TARGETS = ["DeepSeek-V3.1", "DeepSeek-V3.2"]
TRAIT_LOW, TRAIT_HIGH = 0.03, 0.97


def _logit(p: float) -> float:
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    return math.log(p / (1.0 - p))


def _invlogit(x):
    x = np.asarray(x, dtype=float)
    return 1.0 / (1.0 + np.exp(-x))


def load_measured(eval_csv: Path, samples_dir: Path,
                  targets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame,
                                               pd.DataFrame]:
    """Measured eval rows, measured question samples, and the 20-model trait frame.

    Trait frame columns: full_name, family, era, trait (occupancy merged with
    the measured MMLU 5-shot accuracy). Raises if any target is missing from
    the occupancy table or if no measured samples are found.
    """
    if not eval_csv.exists():
        raise FileNotFoundError(f"{eval_csv} not found; run the 20-model eval first")
    eval_df = pd.read_csv(eval_csv)
    if "full_name" not in eval_df.columns:
        raise ValueError(f"{eval_csv} missing 'full_name' column")

    design = model_table().rename(columns={"quarter": "era"})
    for t in targets:
        if t not in set(design["full_name"]):
            raise ValueError(f"target {t!r} not in the occupancy table")

    measured = eval_df[~eval_df["full_name"].isin(targets)].copy()
    if measured.empty:
        raise ValueError("no measured models (eval CSV holds only the targets?)")

    trait = design.merge(
        measured[["full_name", "acc"]], on="full_name", how="inner")
    trait["trait"] = trait["acc"].astype(float)
    trait = trait[["full_name", "family", "era", "trait"]]

    if not samples_dir.is_dir():
        raise FileNotFoundError(f"{samples_dir} not found; need measured samples")
    frames = []
    for path in sorted(samples_dir.glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        frames.append(pd.DataFrame(rows))
    samples = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if samples.empty:
        raise FileNotFoundError(f"no samples under {samples_dir}")
    samples = samples[samples["full_name"].isin(set(measured["full_name"]))]

    return measured, samples, trait


def fit_predictive(trait: pd.DataFrame) -> dict:
    """Fit the additive VC model on the measured traits; return fitted params."""
    fit = fit_lpm_vcomp(trait)
    return {
        "mu": float(trait["trait"].mean()),
        "s2_L": fit.s2["family"],
        "s2_E": fit.s2["era"],
        "s2_U": fit.s2["unique"],
        "converged": fit.converged,
        "n": len(trait),
    }


def draw_imputations(params: dict, targets: list[str], m: int, seed: int
                     ) -> list[dict[str, float]]:
    """M predictive draws for the targets.

    Each draw shares ONE family effect across the targets (same family) and
    uses independent era and model effects from the fitted priors.
    """
    rng = np.random.default_rng(seed)
    sdL = math.sqrt(max(params["s2_L"], 0.0))
    sdE = math.sqrt(max(params["s2_E"], 0.0))
    sdU = math.sqrt(max(params["s2_U"], 0.0))
    draws = []
    for _ in range(m):
        alpha = rng.normal(0.0, sdL)
        out = {}
        for t in targets:
            beta = rng.normal(0.0, sdE)
            u = rng.normal(0.0, sdU)
            out[t] = min(max(params["mu"] + alpha + beta + u, TRAIT_LOW), TRAIT_HIGH)
        draws.append(out)
    return draws


def common_item_frame(samples: pd.DataFrame, measured_names: set[str]
                      ) -> pd.DataFrame:
    """One row per question answered by EVERY measured model (register A15).

    Returns question, subject, answer, choices, and the per-item measured
    difficulty ``d`` = logit(mean correct rate across measured models).
    """
    by_model = {}
    for fn in measured_names:
        sub = samples[samples["full_name"] == fn].dropna(subset=["correct"])
        by_model[fn] = sub.set_index("question")
    if not by_model:
        raise ValueError("no measured samples to build the common item set")

    common = set.intersection(*[set(d.index) for d in by_model.values()])
    if not common:
        raise ValueError("no question answered by every measured model")
    meta = next(iter(by_model.values()))
    rows = []
    for q in sorted(common):
        p = float(np.mean([by_model[fn].loc[q, "correct"] for fn in by_model]))
        rows.append({
            "question": q,
            "subject": str(meta.loc[q, "subject"]),
            "answer": meta.loc[q, "answer"],
            "choices": meta.loc[q, "choices"],
            "d": _logit(min(max(p, 1e-3), 1.0 - 1e-3)),
        })
    return pd.DataFrame(rows)


def calibrate_offset(trait: float, diffs: np.ndarray) -> float:
    """lambda solving mean_i invlogit(logit(trait) + lambda - d_i) = trait."""
    target = _logit(trait)
    lo, hi = -15.0, 15.0

    def f(lam: float) -> float:
        return float(np.mean(_invlogit(target + lam - diffs))) - trait

    if f(lo) > 0:
        return lo
    if f(hi) < 0:
        return hi
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def simulate_item_rows(full_name: str, repo: str, trait: float,
                       items: pd.DataFrame, rng: np.random.Generator
                       ) -> list[dict]:
    """Per-question JSONL rows for one imputed model on the shared item set."""
    diffs = items["d"].to_numpy(dtype=float)
    offset = calibrate_offset(trait, diffs)
    target = _logit(trait)
    rows = []
    for _, it in items.iterrows():
        p = _invlogit(target + offset - it["d"])
        correct = int(rng.random() < p)
        choices = json.loads(it["choices"]) if isinstance(it["choices"], str) \
            else list(it["choices"])
        answer = int(it["answer"]) if it["answer"] is not None else None
        if correct and answer is not None:
            predicted = answer
        elif answer is not None and len(choices) > 1:
            predicted = int(rng.integers(0, len(choices)))
            while predicted == answer:
                predicted = int(rng.integers(0, len(choices)))
        else:
            predicted = None
        rows.append({
            "full_name": full_name,
            "hf_repo": repo,
            "subject": it["subject"],
            "question": it["question"],
            "choices": json.dumps(choices),
            "answer": answer,
            "predicted": predicted,
            "correct": correct,
            "choice_logprobs": "[]",
        })
    return rows


def impute(eval_csv: Path = DEFAULT_EVAL_CSV,
           samples_dir: Path = DEFAULT_SAMPLES_DIR,
           targets: list[str] | None = None,
           m: int = 5, seed: int = 2026,
           label: str = "deepseek_imputed",
           out_csv: Path | None = None,
           out_samples: Path | None = None,
           report_path: Path | None = None) -> dict:
    """Run the pre-registered imputation; write all outputs; return the report."""
    if targets is None:
        targets = DEFAULT_TARGETS
    out_csv = out_csv or DATASETS / f"phase2_eval_results.{label}.csv"
    out_samples = out_samples or DATASETS / f"eval_samples.{label}"
    report_path = report_path or DATASETS / "coverage" / f"imputation_report.{label}.md"

    measured, samples, trait = load_measured(eval_csv, samples_dir, targets)
    params = fit_predictive(trait)
    draws = draw_imputations(params, targets, m, seed)
    primary = draws[0]

    items = common_item_frame(samples, set(measured["full_name"]))
    rng = np.random.default_rng(seed + 10_000)

    out_samples.mkdir(parents=True, exist_ok=True)
    for path in sorted(samples_dir.glob("*.jsonl")):
        shutil.copy2(path, out_samples / path.name)
    for t in targets:
        repo = EVAL_MANIFEST[t][0]
        rows = simulate_item_rows(t, repo, primary[t], items, rng)
        fname = f"{t}__{repo.replace('/', '__')}.jsonl"
        with open(out_samples / fname, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    imputed_rows = []
    for t in targets:
        repo = EVAL_MANIFEST[t][0]
        imputed_rows.append({
            "date": date.today().isoformat(),
            "full_name": t,
            "hf_repo": repo,
            "benchmark": "mmlu",
            "fewshot": 5,
            "acc": primary[t],
            "acc_norm": primary[t],
            "samples": len(items),
            "fidelity": "imputed",
        })

    combined = measured.copy()
    if "fidelity" not in combined.columns:
        combined["fidelity"] = "measured"
    combined = pd.concat([combined, pd.DataFrame(imputed_rows)],
                         ignore_index=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_csv, index=False)

    draws_df = pd.DataFrame([
        {"draw": k, "full_name": t, "trait": v}
        for k, d in enumerate(draws) for t, v in d.items()
    ])
    draws_csv = report_path.with_name(f"imputed_draws.{label}.csv")
    draws_csv.parent.mkdir(parents=True, exist_ok=True)
    draws_df.to_csv(draws_csv, index=False)

    # 20-only reference partition + per-draw 22-model partitions.
    ref_fit = fit_lpm_vcomp(trait)
    ref_shares = shares_of(ref_fit)
    per_draw = []
    for k, draw in enumerate(draws):
        extra = pd.DataFrame([
            {"full_name": t, "family": "DeepSeek", "era": _era_of(t),
             "trait": draw[t]}
            for t in targets
        ])
        rows = pd.concat([trait, extra], ignore_index=True)
        fit = fit_lpm_vcomp(rows)
        per_draw.append({"draw": k, "shares": shares_of(fit),
                         "traits": dict(draw)})

    report_lines = _report(label, targets, params, draws, ref_shares, per_draw,
                           items, out_csv, out_samples, draws_csv)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n")

    return {
        "label": label, "n_measured": len(measured), "targets": targets,
        "m": m, "n_items": len(items),
        "csv": out_csv, "samples_dir": out_samples, "report": report_path,
        "draws_csv": draws_csv, "primary": primary,
        "params": params, "ref_shares": ref_shares,
        "per_draw": per_draw,
    }


def _era_of(full_name: str) -> str:
    row = model_table()[model_table()["full_name"] == full_name]
    if row.empty:
        raise ValueError(full_name)
    return str(row.iloc[0]["quarter"])


def _report(label: str, targets: list[str], params: dict,
            draws: list[dict[str, float]], ref_shares: dict,
            per_draw: list[dict], items: pd.DataFrame,
            out_csv: Path, out_samples: Path, draws_csv: Path) -> list[str]:
    lines = [
        f"# Pre-measurement model-based imputation ({label})",
        "",
        f"Generated {date.today().isoformat()}. The DeepSeek trait cells below "
        "are **NOT measured**: they are predictive draws from the "
        "variance-components model fitted on the measured models. This is a "
        "pre-registered availability imputation, not empirical measurement.",
        "",
        "> **DISCLOSURE (binding):** every table/figure cell for "
        f"{', '.join(targets)} must be labeled "
        '"IMPUTED (pre-registered model-based imputation), not measured". The '
        "study is measured on 20 models and completed by imputation on 2.",
        "",
        "```",
        "IMPUTED_PREMEASUREMENT:",
    ]
    for t in targets:
        lines.append(f"  - {t}")
    lines += [
        "REASON: unavailable_reproducible_compute",
        "STATUS: model_based_imputation",
        "DATE: " + date.today().isoformat(),
        "```",
        "",
        "## Fitted predictive model (20 measured models)",
        "",
        f"trait ~ mu + family + era + unique (the Phase 2 estimand structure); "
        f"mu = {params['mu']:.4f}, s2_L = {params['s2_L']:.5f}, "
        f"s2_E = {params['s2_E']:.5f}, s2_U = {params['s2_U']:.5f} "
        f"(converged={params['converged']}, n={params['n']}).",
        "",
        "Draws: one shared DeepSeek-family effect per draw (same family), "
        "independent era effects (2025Q3/2025Q4 are prior-dominated cells) and "
        "model effects, all from the fitted priors.",
        "",
        "| draw | " + " | ".join(targets) + " |",
        "|---|---|" + "---|" * len(targets),
    ]
    for k, d in enumerate(draws):
        lines.append("| " + str(k) + " | " +
                     " | ".join(f"{d[t]:.4f}" for t in targets) + " |")
    lines += [
        "",
        "## Variance partition (era share bias)",
        "",
        "| draw | share_family | share_era | share_unique |",
        "|---|---|---|---|",
    ]
    for d in per_draw:
        s = d["shares"]
        lines.append(f"| {d['draw']} | {s['family']:.4f} | {s['era']:.4f} | "
                     f"{s['unique']:.4f} |")
    pooled = {k: float(np.mean([d['shares'][k] for d in per_draw]))
              for k in per_draw[0]['shares']}
    spread = {k: float(np.std([d['shares'][k] for d in per_draw]))
              for k in pooled}
    lines.append(f"| pooled (mean over {len(per_draw)} draws) | "
                 f"{pooled['family']:.4f} | {pooled['era']:.4f} | "
                 f"{pooled['unique']:.4f} |")
    lines.append(f"| between-draw SD | {spread['family']:.4f} | "
                 f"{spread['era']:.4f} | {spread['unique']:.4f} |")
    lines += [
        "",
        f"Measured-only reference (20 models, no imputation): "
        f"share_family = {ref_shares['family']:.4f}, "
        f"share_era = {ref_shares['era']:.4f}, "
        f"share_unique = {ref_shares['unique']:.4f}. "
        "Compare with the pooled 22-model estimates above: the difference is "
        "the sensitivity of the decomposition to the DeepSeek imputation.",
        "",
        f"## Item-level generation",
        "",
        f"Common item set: {len(items)} questions answered by every measured "
        "model (register A15). Per-item difficulty from the measured models' "
        "logit mean-correct; per-model offset calibrated by bisection so the "
        "simulated accuracy equals the imputed trait (same logistic item model "
        "as the Phase 1 DGP). Item-level responses for the imputed models carry "
        "no fabricated model-model error correlation beyond the trait.",
        "",
        "## Outputs",
        "",
        f"- {out_csv} (primary completed dataset = draw 0; "
        f"fidelity='imputed' on the {', '.join(targets)} rows)",
        f"- {out_samples}/ (measured JSONL copied + draw-0 imputed JSONL)",
        f"- {draws_csv} (all {len(draws)} predictive draws for the sensitivity)",
        "",
        "Run downstream stages against the primary paths, e.g.:",
        f"    python3 -m lineage_era.phase2_trait --eval-csv {out_csv} "
        f"--samples-dir {out_samples}",
    ]
    return lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--eval-csv", default=str(DEFAULT_EVAL_CSV))
    p.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR))
    p.add_argument("--label", default="deepseek_imputed")
    p.add_argument("--targets",
                   default=",".join(DEFAULT_TARGETS))
    p.add_argument("--m", type=int, default=5)
    p.add_argument("--seed", type=int, default=2026)
    args = p.parse_args(argv)

    targets = [s.strip() for s in args.targets.split(",") if s.strip()]
    rep = impute(Path(args.eval_csv), Path(args.samples_dir), targets,
                 m=args.m, seed=args.seed, label=args.label)
    print(f"imputation {rep['label']}: {rep['n_measured']} measured + "
          f"{len(rep['targets'])} imputed x {rep['m']} draws; "
          f"{rep['n_items']} common items")
    print(f"-> {rep['csv']}")
    print(f"-> {rep['samples_dir']}/")
    print(f"-> {rep['draws_csv']}")
    print(f"-> {rep['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
