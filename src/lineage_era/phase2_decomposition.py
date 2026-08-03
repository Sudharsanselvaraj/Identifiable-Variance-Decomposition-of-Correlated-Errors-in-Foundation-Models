"""Phase 2 decomposition pipeline: one command end to end.

    python3 -m lineage_era.phase2_decomposition                 # real data path
    python3 -m lineage_era.phase2_decomposition --synthetic     # occupancy + scenario C
    python3 -m lineage_era.phase2_decomposition --audit-only    # stop after the gate

Pipeline: trait (fresh eval / synthetic) -> metadata -> identifiability audit
(ABORT on hard fail, exit 2) -> θ_P model + θ_M tables -> bootstrap CIs ->
sensitivity -> figures -> tables -> PHASE2_REPORT.md.

Real-data inputs (default): datasets/phase2_eval_results.csv (GPU runbook),
datasets/eval_samples/ (per-question JSONL), and the built-in occupancy table.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import dgp, estimator
from .occupancy import model_table

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"


def synthetic_trait_table(seed: int, scenario: dict,
                          trait_se: float) -> pd.DataFrame:
    """Realistic synthetic trait: real occupancy, scenario-C effects, fixed SE."""
    rng = np.random.default_rng(seed)
    design = model_table().rename(columns={"quarter": "era"})
    design["model"] = range(len(design))
    sim = dgp.simulate_trait(design, scenario, rng)
    out = sim[["full_name", "family", "era", "trait"]].copy()
    out["trait_se"] = trait_se
    return out


def run_trait(out_dir: Path, synthetic: bool, seed: int) -> pd.DataFrame:
    if synthetic:
        trait = synthetic_trait_table(seed, dgp.SCENARIOS["C"], trait_se=0.02)
        trait.to_csv(out_dir / "trait_table.csv", index=False)
        return trait
    from . import phase2_trait
    eval_df = phase2_trait.load_eval_results()
    samples = phase2_trait.load_question_samples()
    trait = phase2_trait.assemble_trait(eval_df, samples=samples)
    trait.to_csv(out_dir / "trait_table.csv", index=False)
    return trait


def run_metadata(out_dir: Path) -> pd.DataFrame:
    from . import phase2_metadata
    design = phase2_metadata.build_design()
    design.to_csv(out_dir / "analysis_design.csv", index=False)
    return design


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--synthetic", action="store_true",
                   help="dry-run pipeline on a synthetic trait over the real occupancy")
    p.add_argument("--audit-only", action="store_true",
                   help="run trait + metadata + audit, then stop")
    p.add_argument("--results-dir", default="results/phase2")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--bootstrap-reps", type=int, default=500)
    args = p.parse_args(argv)

    out_dir = Path(args.results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    trait = run_trait(out_dir, args.synthetic, args.seed)
    run_metadata(out_dir)

    from . import phase2_identifiability as audit_mod
    result = audit_mod.audit(trait)
    audit_mod.write_report(result, out_dir)
    pd.DataFrame([
        {"term": "family", "max_vif": result.checks["max_vif_family"]},
        {"term": "era", "max_vif": result.checks["max_vif_era"]},
    ]).to_csv(out_dir / "vif.csv", index=False)
    (out_dir / "condition_number.txt").write_text(
        f"kappa = {result.checks['condition_number']:.4f}\n"
        f"threshold = {audit_mod.KAPPA_MAX:.0f} (warning only)\n")
    print(f"Audit {'FAIL' if result.hard_fail else 'PASS'} "
          f"(κ={result.checks['condition_number']:.1f})")
    if result.hard_fail:
        print("ABORTING: identifiability gate failed.", file=sys.stderr)
        return 2
    if args.audit_only:
        print("--audit-only: stopped after the gate.")
        return 0

    from . import phase2_model, phase2_bootstrap, phase2_sensitivity
    from . import phase2_figures, phase2_tables, phase2_report

    vp, fit = phase2_model.variance_partition(trait)
    vp.to_csv(out_dir / "variance_partition.csv", index=False)
    fam, era = phase2_model.blups_by_level(trait, fit)
    fam.to_csv(out_dir / "family_effects.csv", index=False)
    era.to_csv(out_dir / "era_effects.csv", index=False)
    for name, table in phase2_model.theta_m_tables(trait, fit).items():
        table.to_csv(out_dir / f"{name}.csv", index=False)
    print(f"θ_P: family={vp.set_index('component').loc['family','share']:.3f} "
          f"era={vp.set_index('component').loc['era','share']:.3f}")

    phase2_bootstrap.main(["--df", str(out_dir / "trait_table.csv"),
                           "--reps", str(args.bootstrap_reps),
                           "--seed", str(args.seed),
                           "--out-dir", str(out_dir)])
    phase2_sensitivity.main(["--df", str(out_dir / "trait_table.csv"),
                             "--out-dir", str(out_dir)])
    phase2_figures.main(["--out-dir", str(out_dir)])
    phase2_tables.main(["--out-dir", str(out_dir)])
    phase2_report.main(["--out-dir", str(out_dir)])

    print(f"\nPipeline complete -> {out_dir}")
    print(f"Report: {out_dir / 'PHASE2_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
