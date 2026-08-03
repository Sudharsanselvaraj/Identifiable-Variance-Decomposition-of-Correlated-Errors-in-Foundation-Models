"""Phase 1 simulation CLI: D1/D2/D3 + liability + LxE, with a gate verdict.

Run:
    python src/lineage_era/phase1_simulation.py --regime d1 --reps 100 --seed 1
    python src/lineage_era/phase1_simulation.py --regime all --reps 100 --seed 1

Writes per-rep CSVs and printed summaries under results/phase1/.
"""
from __future__ import annotations

import argparse
import math
import os

import numpy as np
import pandas as pd

from . import dgp, estimator, metrics

OUT_DIR = "results/phase1"

GATE = {
    "share_bias_pp": 5.0,
    "ci_coverage_lo": 90.0,
    "ci_coverage_hi": 99.0,
    "d3_fail_rate": 90.0,
    "d2_rel_bias": 0.10,
}


def _out(name: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    return os.path.join(OUT_DIR, name)


# ---------------------------------------------------------------- d1 / d2
def run_crossed(regime: str, scenario: str, reps: int, rng: np.random.Generator) -> list[dict]:
    rows = []
    for rep in range(reps):
        design = dgp.design_for(regime, rng)
        df = dgp.simulate_trait(design, dgp.SCENARIOS[scenario], rng)
        fit = estimator.fit_lpm_vcomp(df)
        ci = estimator.share_ci(fit)
        sh = fit.shares
        row = {
            "rep": rep, "scenario": scenario,
            "s2_family": fit.s2["family"], "s2_era": fit.s2["era"],
            "s2_unique": fit.s2["unique"],
            "share_family": sh["family"], "share_era": sh["era"],
            "share_unique": sh["unique"],
            "ci_family_low": ci["family"][0], "ci_family_high": ci["family"][1],
            "ci_era_low": ci["era"][0], "ci_era_high": ci["era"][1],
            "ci_unique_low": ci["unique"][0], "ci_unique_high": ci["unique"][1],
            "converged": int(fit.converged),
            "n_convergence_warnings": fit.n_convergence_warnings,
            "llf": fit.llf,
        }
        rows.append(row)
    return rows


# ------------------------------------------------------------------- d3
def run_nested(regime: str, scenario: str, reps: int, rng: np.random.Generator) -> list[dict]:
    rows = []
    for rep in range(reps):
        design = dgp.design_for(regime, rng)
        df = dgp.simulate_trait(design, dgp.SCENARIOS[scenario], rng)
        fit = estimator.fit_lpm_vcomp(df)
        diag = metrics.d3_diagnostics(fit)
        ci = estimator.share_ci(fit)
        sh = fit.shares
        raw_truth = dgp.SCENARIOS[scenario]
        truth = {"family": raw_truth["L"], "era": raw_truth["E"],
                 "unique": raw_truth["U"]}
        covers = all(
            metrics.coverage(ci[k], truth[k]) for k in ("family", "era", "unique")
        )
        row = {
            "rep": rep, "scenario": scenario,
            "s2_family": fit.s2["family"], "s2_era": fit.s2["era"],
            "s2_unique": fit.s2["unique"],
            "share_family": sh["family"], "share_era": sh["era"],
            "share_unique": sh["unique"],
            "ci_family_low": ci["family"][0], "ci_family_high": ci["family"][1],
            "ci_era_low": ci["era"][0], "ci_era_high": ci["era"][1],
            "ci_unique_low": ci["unique"][0], "ci_unique_high": ci["unique"][1],
            "converged": int(fit.converged),
            "n_convergence_warnings": fit.n_convergence_warnings,
            "d_collinearity": int(diag["collinearity"]),
            "d_se_inflation": int(diag["se_inflation"]),
            "d_profile_flat": int(diag["profile_flat"]),
            "d_non_convergence": int(diag["non_convergence"]),
            "detected": int(metrics.d3_detected(diag)),
            "silent_ci_covers": int(covers),
        }
        rows.append(row)
    return rows


# ------------------------------------------------------------- liability
def _liability_rows(scenario: str, reps: int, rng: np.random.Generator,
                    n_items: int, occupancy: str) -> list[dict]:
    rows = []
    design_fn = dgp.design_d1 if occupancy == "d1" else dgp.design_d2
    for rep in range(reps):
        design = design_fn(rng)
        long = dgp.simulate_liability(design, dgp.SCENARIOS[scenario], n_items, rng)
        raw_truth = dgp.SCENARIOS[scenario]
        truth = {"family": raw_truth["L"], "era": raw_truth["E"],
                 "unique": raw_truth["U"]}

        # LPM path on per-model error proportions.
        p = long.groupby("model").agg(
            family=("family", "first"), era=("era", "first"), p=("y", "mean")
        ).reset_index()
        fit = estimator.fit_lpm_vcomp(p.rename(columns={"p": "trait"}))
        for path, s2 in (("lpm", fit.s2),
                         ("glmm", estimator.fit_glmm_binomial(
                             long["y"].to_numpy(), long["family"].to_numpy(),
                             long["era"].to_numpy(), long["model"].to_numpy()))):
            conv = fit.converged if path == "lpm" else s2["converged"]
            s2c = {k: s2[k] for k in ("family", "era", "unique")}
            tot = sum(max(v, 0.0) for v in s2c.values())
            sh = {k: (v / tot if tot > 0 else float("nan")) for k, v in s2c.items()}
            rows.append({
                "rep": rep, "scenario": scenario, "path": path,
                "occ": occupancy,
                "s2_family": s2c["family"], "s2_era": s2c["era"],
                "s2_unique": s2c["unique"],
                "share_family": sh["family"], "share_era": sh["era"],
                "share_unique": sh["unique"],
                "bias_pp_family": (sh["family"] - truth["family"]) * 100,
                "bias_pp_era": (sh["era"] - truth["era"]) * 100,
                "era_boundary": int(s2c["era"] < 1e-6),
                "ranking_ok": int(metrics.ranking_ok(s2c, truth)),
                "converged": int(conv),
            })
    return rows


def run_liability(scenario: str, reps: int, rng: np.random.Generator,
                  n_items: int, occupancy: str) -> list[dict]:
    return _liability_rows(scenario, reps, rng, n_items, occupancy)


# ------------------------------------------------------------------ lxe
def run_lxe(scenario: str, reps: int, rng: np.random.Generator,
            s2_LE: float = 0.15) -> list[dict]:
    rows = []
    for rep in range(reps):
        design = dgp.design_d2(rng)
        df = dgp.simulate_trait_lxe(design, dgp.SCENARIOS[scenario], s2_LE, rng)
        df["cell"] = ["%s|%s" % (f, e) for f, e in zip(df["family"], df["era"])]

        # Model WITHOUT interaction.
        wo = estimator.fit_lpm_vcomp(df)
        # Model WITH a family x era variance component (direct REML, 4 params).
        try:
            fit_with = estimator.fit_lpm_vcomp_cells(df, "cell")
        except Exception:  # noqa: BLE001
            fit_with = None

        if fit_with is not None:
            s2_le = fit_with.s2["cell"]
            se_le = fit_with.se["cell"]
            collinear = metrics.collinearity_detected(fit_with)
        else:
            s2_le, se_le = math.nan, math.nan
            collinear = True
            fit_with = None

        rows.append({
            "rep": rep, "scenario": scenario,
            "s2_LE_est": s2_le,
            "s2_LE_se": se_le,
            "s2_LE_se_ratio": (se_le / s2_le if (math.isfinite(s2_le) and s2_le > 0) else math.nan),
            "s2_LE_converged": int(fit_with.converged) if fit_with is not None else 0,
            "s2_LE_n_warn": 0,
            "boundary_zero": int(math.isfinite(s2_le) and s2_le <= 0),
            "collinear_with": int(collinear),
            "llf_without": wo.llf,
            "llf_with": fit_with.llf if fit_with is not None else math.nan,
            "converged_without": int(wo.converged),
        })
    return rows


# -------------------------------------------------------------- summary
def summarize_crossed(rows: list[dict], scenario: str) -> dict:
    df = pd.DataFrame([r for r in rows if r["scenario"] == scenario])
    out = {"scenario": scenario}
    comp_map = {"L": "family", "E": "era", "U": "unique"}
    for k, truth_v in dgp.SCENARIOS[scenario].items():
        comp = comp_map[k]
        est = df[f"share_{comp}"]
        rb = metrics.relative_bias(est.mean(), truth_v)
        out[f"{comp}_rel_bias_mean"] = rb
        out[f"{comp}_share_bias_pp_mean"] = metrics.share_bias_pp(est.mean(), truth_v)
        covered = [
            metrics.coverage((lo, hi), truth_v)
            for lo, hi in zip(df[f"ci_{comp}_low"], df[f"ci_{comp}_high"])
        ]
        out[f"{comp}_coverage_pct"] = 100.0 * np.mean(covered)
        out[f"{comp}_ci_width_mean"] = np.mean(df[f"ci_{comp}_high"] - df[f"ci_{comp}_low"])
    out["convergence_pct"] = 100.0 * df["converged"].mean()
    out["n_convergence_warnings"] = int(df["n_convergence_warnings"].sum())
    return out


def summarize_nested(rows: list[dict], scenario: str) -> dict:
    df = pd.DataFrame([r for r in rows if r["scenario"] == scenario])
    out = {
        "scenario": scenario,
        "detected_pct": 100.0 * df["detected"].mean(),
        "d_collinearity_pct": 100.0 * df["d_collinearity"].mean(),
        "d_se_inflation_pct": 100.0 * df["d_se_inflation"].mean(),
        "d_profile_flat_pct": 100.0 * df["d_profile_flat"].mean(),
        "d_non_convergence_pct": 100.0 * df["d_non_convergence"].mean(),
        "convergence_pct": 100.0 * df["converged"].mean(),
    }
    undetected = df[df["detected"] == 0]
    out["silent_ci_covers_pct"] = (
        100.0 * undetected["silent_ci_covers"].mean() if len(undetected) else math.nan
    )
    return out


def summarize_liability(rows: list[dict], scenario: str) -> dict:
    df = pd.DataFrame([r for r in rows if r["scenario"] == scenario])
    out = {"scenario": scenario}
    for occ in sorted(df["occ"].unique()):
        sub = df[df["occ"] == occ]
        for path in ("lpm", "glmm"):
            q = sub[sub["path"] == path]
            out[f"{occ}_{path}_bias_pp_family"] = q["bias_pp_family"].mean()
            out[f"{occ}_{path}_bias_pp_era"] = q["bias_pp_era"].mean()
            out[f"{occ}_{path}_era_boundary_pct"] = 100.0 * q["era_boundary"].mean()
            out[f"{occ}_{path}_ranking_ok_pct"] = 100.0 * q["ranking_ok"].mean()
            out[f"{occ}_{path}_converged_pct"] = 100.0 * q["converged"].mean()
        l = sub[sub["path"] == "lpm"].sort_values("rep").reset_index(drop=True)
        g = sub[sub["path"] == "glmm"].sort_values("rep").reset_index(drop=True)
        if len(l) and len(g):
            out[f"{occ}_cross_path_share_family_corr"] = np.corrcoef(
                l["share_family"], g["share_family"])[0, 1]
            agree = np.mean(np.abs(l["share_family"] - g["share_family"]) < 0.10)
            out[f"{occ}_cross_path_share_family_agree_pct"] = 100.0 * agree
    return out


def summarize_lxe(rows: list[dict], scenario: str) -> dict:
    df = pd.DataFrame([r for r in rows if r["scenario"] == scenario])
    return {
        "scenario": scenario,
        "s2_LE_est_mean": df["s2_LE_est"].mean(),
        "s2_LE_se_ratio_mean": df["s2_LE_se_ratio"].mean(),
        "boundary_zero_pct": 100.0 * df["boundary_zero"].mean(),
        "collinear_with_pct": 100.0 * df["collinear_with"].mean(),
        "converged_with_pct": 100.0 * df["s2_LE_converged"].mean(),
        "converged_without_pct": 100.0 * df["converged_without"].mean(),
    }


def _print(name: str, summary: dict) -> None:
    print(f"[{name}]")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.3f}")
        else:
            print(f"  {k}: {v}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 1 simulation battery")
    ap.add_argument("--regime", required=True,
                    choices=["d1", "d2", "d3", "liability", "lxe", "all"])
    ap.add_argument("--reps", type=int, default=None,
                    help="reps per regime (defaults: 100 d1/d2/d3, 30 liability, 10 lxe)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n-items", type=int, default=300,
                    help="items per model in the liability test")
    ap.add_argument("--liability-occ", choices=["d2", "d1"], default="d2",
                    help="occupancy for the liability test (d2 = real design)")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    regimes = ["d1", "d2", "d3", "liability", "lxe"] if args.regime == "all" \
        else [args.regime]
    default_reps = {"d1": 100, "d2": 100, "d3": 100, "liability": 30, "lxe": 10}

    for regime in regimes:
        reps = args.reps if args.reps is not None else default_reps[regime]
        all_rows = []
        for scenario in ["A", "B", "C"]:
            r = rng
            if regime == "liability":
                rows = run_liability(scenario, reps, rng, n_items=args.n_items,
                                     occupancy=args.liability_occ)
            elif regime == "lxe":
                rows = run_lxe(scenario, reps, rng)
            else:
                rows = {"d1": run_crossed, "d2": run_crossed,
                        "d3": run_nested}[regime](regime, scenario, reps, rng)
            all_rows.extend(rows)

        df = pd.DataFrame(all_rows)
        df.to_csv(_out(f"{regime}.csv"), index=False)
        summarize = {
            "d1": summarize_crossed, "d2": summarize_crossed,
            "d3": summarize_nested, "liability": summarize_liability,
            "lxe": summarize_lxe,
        }[regime]
        summaries = [summarize(all_rows, s) for s in ["A", "B", "C"]]
        for s in summaries:
            _print(regime, s)
        pd.DataFrame(summaries).to_csv(_out(f"{regime}_summary.csv"), index=False)


if __name__ == "__main__":
    main()
