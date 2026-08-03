"""Phase 2 synthetic battery: validates the engine before real GPU numbers land.

Scenarios (shares on the model-level trait variance; all use U > 0 because the
direct-REML maximizer is only well-behaved in the residual-noise regime that
Phase 1 validated — the U = 0 boundary is pathological for any variance-
component estimator):
    S1  lineage-dominant     D2 occupancy, L=0.60, E=0.10, U=0.30
    S2  era-dominant         D2 occupancy, L=0.10, E=0.60, U=0.30
    S3  balanced 50/50       D2 occupancy, L=0.35, E=0.35, U=0.30
    S4  nested               design_d3 (family ~ era)      -> audit MUST abort
    S5  measurement noise    D2, scenario C + N(0, sigma_m^2) trait noise
    S6  D2-realistic         D2, scenario C                -> audit MUST pass

S1/S2/S3/S5 check share recovery (mean over reps). S4/S6 pin the audit
thresholds: nested must abort, the realistic design must not false-abort.

Outputs: battery.csv (per-rep), battery_summary.csv under results/phase2/.
Exit code 1 if any requirement fails.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import dgp, estimator
from .phase2_identifiability import audit

REQUIREMENTS: dict[str, list[str]] = {
    "S1": ["recover_lineage", "family_dominant"],
    "S2": ["recover_era", "era_dominant"],
    "S3": ["recover_50_50"],
    "S4": ["audit_must_abort"],
    "S5": ["recover_noisy"],
    "S6": ["audit_must_pass"],
}

# Tolerances reflect the documented small-sample bias of the 6-family design
# (converged means over 50 reps: dominant-channel share under-recovered by
# ~0.04-0.08; measurement noise widens the family-channel gap to ~0.11).
SHARE_TOL = {"S1": 0.10, "S2": 0.12, "S3": 0.08, "S5": 0.15}

SCENARIOS = {
    "S1": {"L": 0.60, "E": 0.10, "U": 0.30},
    "S2": {"L": 0.10, "E": 0.60, "U": 0.30},
    "S3": {"L": 0.35, "E": 0.35, "U": 0.30},
}


def shares(fit: estimator.FitResult) -> dict[str, float]:
    tot = sum(fit.s2.values())
    return {k: float(v / tot) if tot > 0 else 0.0 for k, v in fit.s2.items()}


def add_measurement_noise(df: pd.DataFrame, sigma_m: float,
                          rng: np.random.Generator) -> pd.DataFrame:
    out = df.copy()
    out["trait"] = out["trait"] + rng.normal(0.0, sigma_m, len(out))
    return out


def run_scenario(name: str, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(seed)
    for rep in range(reps):
        if name in SCENARIOS:
            scenario = SCENARIOS[name]
        else:
            scenario = dgp.SCENARIOS["C"]
        design = dgp.design_d3(rng) if name == "S4" else dgp.design_d2(rng)
        design["family"] = design["family"].astype(str)
        design["era"] = design["era"].astype(str)
        df = dgp.simulate_trait(design, scenario, rng)
        if name == "S5":
            df = add_measurement_noise(df, sigma_m=0.5, rng=rng)
        fit = estimator.fit_lpm_vcomp(df)
        sh = shares(fit)
        if name in ("S4", "S6"):
            # Full gate (check_profile=True): S6 must pass under the exact same
            # audit configuration the pipeline uses, so the no-false-abort pin
            # is meaningful. S4 abort is driven by the rank + collinearity
            # checks. Recovery scenarios skip the audit (it does not affect
            # shares and would dominate the runtime at high reps).
            result = audit(df)
            hard_fail = result.hard_fail
            cond = result.checks["condition_number"]
        else:
            hard_fail = False
            cond = float("nan")
        rows.append({
            "scenario": name, "rep": rep,
            "s2_family": fit.s2["family"], "s2_era": fit.s2["era"],
            "s2_unique": fit.s2["unique"],
            "share_family": sh["family"], "share_era": sh["era"],
            "share_unique": sh["unique"],
            "audit_hard_fail": hard_fail,
            "cond": cond,
        })
    return pd.DataFrame(rows)


def evaluate(out: pd.DataFrame, name: str) -> tuple[bool, list[str]]:
    mean = out.mean(numeric_only=True)
    if name == "S1":
        ok = (abs(mean["share_family"] - 0.60) <= SHARE_TOL["S1"]
              and mean["share_family"] >= mean["share_era"])
        return ok, [f"share_family={mean['share_family']:.3f}"]
    if name == "S2":
        ok = (abs(mean["share_era"] - 0.60) <= SHARE_TOL["S2"]
              and mean["share_era"] >= mean["share_family"])
        return ok, [f"share_era={mean['share_era']:.3f}"]
    if name == "S3":
        ok = (abs(mean["share_family"] - 0.35) <= SHARE_TOL["S3"]
              and abs(mean["share_era"] - 0.35) <= SHARE_TOL["S3"])
        return ok, [f"share_family={mean['share_family']:.3f} "
                    f"share_era={mean['share_era']:.3f}"]
    if name == "S4":
        return bool(out["audit_hard_fail"].all()), ["abort rate "
                                                    f"{out['audit_hard_fail'].mean():.0%}"]
    if name == "S5":
        ok = (abs(mean["share_family"] - 0.33) <= SHARE_TOL["S5"]
              and abs(mean["share_era"] - 0.33) <= SHARE_TOL["S5"])
        return ok, [f"share_family={mean['share_family']:.3f} "
                    f"share_era={mean['share_era']:.3f}"]
    if name == "S6":
        return not out["audit_hard_fail"].any(), ["abort rate "
                                                  f"{out['audit_hard_fail'].mean():.0%}"]
    raise ValueError(name)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reps", type=int, default=25)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    summary = []
    all_ok = True
    for name in REQUIREMENTS:
        out = run_scenario(name, args.reps, args.seed)
        frames.append(out)
        ok, notes = evaluate(out, name)
        summary.append({"scenario": name, "pass": ok, "notes": "; ".join(notes)})
        all_ok &= bool(ok)
        print(f"{name}: {'PASS' if ok else 'FAIL'}  {' '.join(notes)}")

    pd.concat(frames, ignore_index=True).to_csv(out_dir / "battery.csv", index=False)
    pd.DataFrame(summary).to_csv(out_dir / "battery_summary.csv", index=False)
    print(f"Battery: {'ALL PASS' if all_ok else 'REQUIREMENT FAILURE'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
