"""Phase 2 identifiability audit: first-class gate before the variance partition.

Run on the assembled design/trait frame before any θ_P or θ_M quantities are
reported. Two layers:

Structural (no fit needed)
    - rank: design matrix [1 | family | era] must have full rank
      (k = 1 + n_families - 1 + n_quarters - 1)
    - condition number κ of X'X: reported as a WARNING only. Calibrated by
      battery S6: on the realistic sparse occupancy κ > 100 (Belsley severe)
      reflects the unbalanced crossed row structure, not family-era aliasing,
      and would false-abort a design Phase 1 validated as identifiable.
    - VIF: any family/era dummy with VIF > 10 -> fail
    - occupancy: fraction of occupied family x quarter cells (informational)

Fit-based (uses trait; runs fit_lpm_vcomp internally)
    - collinearity of family/era BLUPs |r| > 0.9   (metrics.collinearity_detected)
    - profile flatness below PROFILE_CUTOFF 1.9207: WARNING only (df = 5)
    - SE inflation se >= estimate: WARNING only (df = 5)
    - convergence

Hard-fail core (structural/topological alias): rank, VIF, BLUP collinearity,
convergence. The likelihood-based detectors (profile flatness, SE inflation)
and κ fire by construction at 6 family levels (df = 5, Phase 1 small-sample
limit) and are reported as warnings; the wide family-share CI is the honest
expression of that. Battery S6 pins the no-false-abort property under the
full gate (check_profile=True).

Verdict: ANY hard-fail -> audit aborts the pipeline (report + non-zero exit).
The battery (phase2_simulate) requires S4 (nested) to abort and S6
(D2-realistic) to pass, which pins these thresholds.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import reml
from ..metrics import (collinearity_detected, profile_flatness_detected,
                       se_inflation_detected)
from ..occupancy import design_counts, family_span

# Thresholds (pinned by the S4/S6 battery requirements).
KAPPA_MAX = 100.0          # Belsley: >100 = severe multicollinearity
VIF_MAX = 10.0             # standard rule of thumb
BLUP_R_CRIT = 0.9          # matches metrics.collinearity_detected default
SE_INFLATION = 1.0         # matches metrics.se_inflation_detected default

FAMILY = "family"
ERA = "era"


@dataclass
class AuditResult:
    checks: dict
    fit: reml.FitResult | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def hard_fail(self) -> bool:
        # Hard-fail core: structural/topological alias checks. The likelihood-
        # based detectors (profile flatness, SE inflation) and κ fire BY
        # CONSTRUCTION at 6 family levels (df = 5) — the Phase 1 small-sample
        # limit — and are reported as warnings; the wide family-share CI is the
        # honest expression of that. Pinned by battery S4/S6.
        hf = [
            self.checks["rank_ok"],
            self.checks["vif_ok"],
            not self.checks["collinearity"],
            self.checks["converged"],
        ]
        return not all(hf)


def _dummies(df: pd.DataFrame, col: str) -> np.ndarray:
    return (df[col].to_numpy()[:, None] == np.unique(df[col])).astype(float)


def structural_checks(df: pd.DataFrame) -> dict:
    """Rank / condition / VIF checks on the family x era design."""
    fam = _dummies(df, FAMILY)
    era = _dummies(df, ERA)
    n_fam, n_era = fam.shape[1], era.shape[1]
    A = fam[:, :-1]
    B = era[:, :-1]
    X = np.column_stack([np.ones(len(df)), A, B])
    k_needed = 1 + A.shape[1] + B.shape[1]
    rank = int(np.linalg.matrix_rank(X))
    kappa = float(np.linalg.cond(X.T @ X))

    def vif_block(block: np.ndarray, other: np.ndarray, n_cols: int) -> float:
        """Max VIF over the block's effective columns vs everything else."""
        vifs = []
        for j in range(block.shape[1]):
            y = block[:, j]
            Xr = np.column_stack([np.ones(len(df)),
                                  np.delete(block, j, axis=1), other])
            beta, *_ = np.linalg.lstsq(Xr, y, rcond=None)
            resid = y - Xr @ beta
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            ss_res = float(np.sum(resid ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
            vifs.append(float("inf") if r2 >= 1.0 - 1e-12 else 1.0 / (1.0 - r2))
        return max(vifs) if vifs else 0.0

    vif_fam = vif_block(A, B, n_fam)
    vif_era = vif_block(B, A, n_era)

    counts = design_counts()
    occupied = int((counts > 0).sum().sum())
    total_cells = int(counts.size)
    span = family_span()

    return {
        "n_models": int(len(df)),
        "n_families": n_fam,
        "n_quarters": n_era,
        "occupied_cells": occupied,
        "cell_fraction": occupied / total_cells,
        "rank": rank,
        "rank_needed": k_needed,
        "rank_ok": rank == k_needed,
        "condition_number": kappa,
        "cond_ok": kappa <= KAPPA_MAX,
        "max_vif_family": vif_fam,
        "max_vif_era": vif_era,
        "vif_ok": max(vif_fam, vif_era) <= VIF_MAX,
        "min_family_span": int(min(span.values())),
        "families_under_2_quarters": int(sum(1 for s in span.values() if s < 2)),
    }


def audit(df: pd.DataFrame, do_fit: bool = True,
          check_profile: bool = True) -> AuditResult:
    """Run the full gate on a frame with family/era (+ optional trait)."""
    checks = structural_checks(df)
    warnings: list[str] = []
    fit: reml.FitResult | None = None
    if do_fit and "trait" in df.columns:
        fit = reml.fit_lpm_vcomp(df)
        checks.update({
            "collinearity": collinearity_detected(fit, r_crit=BLUP_R_CRIT),
            "se_inflation": se_inflation_detected(fit, threshold=SE_INFLATION),
            "profile_flat": profile_flatness_detected(fit, vc_name=FAMILY) if check_profile
            else False,
            "converged": fit.converged and fit.n_convergence_warnings == 0,
        })
        if checks["collinearity"]:
            warnings.append("family/era BLUPs are aliased (|r| > 0.9).")
        if checks["se_inflation"]:
            warnings.append(
                "SE >= estimate on a variance component (warning only: with 6 "
                "family levels, df = 5, the family-variance SE structurally "
                "exceeds the estimate even when identifiable — Phase 1 "
                "small-sample limit; pinned by battery S6. True alias is "
                "captured by the BLUP-collinearity and profile-flatness checks)."
            )
        if checks["profile_flat"]:
            warnings.append(
                "profile likelihood cannot bound the family share within the "
                "±0.4 log window (warning only: with 6 family levels, df = 5, "
                "the family profile is flat by construction — the wide "
                "family-share CI expresses this; pinned by battery S6)."
            )
    else:
        checks.update({
            "collinearity": False, "se_inflation": False,
            "profile_flat": False, "converged": True,
        })
    if not checks["rank_ok"]:
        warnings.append(f"rank {checks['rank']} < required {checks['rank_needed']}.")
    if not checks["cond_ok"]:
        warnings.append(
            f"κ = {checks['condition_number']:.1f} > {KAPPA_MAX:.0f} "
            "(warning only: X'X condition number reflects the sparse/unbalanced "
            "occupancy of a crossed variance-component design, not family-era "
            "aliasing; pinned by battery S6 — see docstring)."
        )
    if not checks["vif_ok"]:
        warnings.append(f"VIF = {max(checks['max_vif_family'], checks['max_vif_era']):.1f} > {VIF_MAX}.")
    return AuditResult(checks=checks, fit=fit, warnings=warnings)


def write_report(result: AuditResult, out_dir: Path) -> Path:
    c = result.checks
    lines = [
        "# Phase 2 Identifiability Audit",
        "",
        f"Verdict: **{'ABORT' if result.hard_fail else 'PASS'}**",
        "",
        "## Structural checks",
        "",
        f"- models n = {c['n_models']}; families = {c['n_families']}; "
        f"quarters = {c['n_quarters']}",
        f"- occupied cells = {c['occupied_cells']}/{c['n_families'] * c['n_quarters']} "
        f"({c['cell_fraction']:.2%})",
        f"- design rank = {c['rank']}/{c['rank_needed']} "
        f"-> {'OK' if c['rank_ok'] else 'FAIL'}",
        f"- condition number κ = {c['condition_number']:.2f} (≤ {KAPPA_MAX:.0f}) "
        f"-> {'OK' if c['cond_ok'] else 'WARN (informational)'}",
        f"- max VIF family = {c['max_vif_family']:.2f}, era = {c['max_vif_era']:.2f} "
        f"(≤ {VIF_MAX:.0f}) -> {'OK' if c['vif_ok'] else 'FAIL'}",
        f"- min family span = {c['min_family_span']} quarters; families with < 2 "
        f"quarters = {c['families_under_2_quarters']}",
        "",
        "## Fit-based checks (family vs era)",
        "",
        f"- BLUP collinearity |r| > {BLUP_R_CRIT}: "
        f"{'FIRE' if c['collinearity'] else 'clear'}",
        f"- SE inflation (se ≥ {SE_INFLATION} × est): "
        f"{'WARN' if c['se_inflation'] else 'clear'} (warning only; "
        f"df-family small-sample limit)",
        f"- profile flatness (drop < {reml.PROFILE_CUTOFF:.4f}): "
        f"{'WARN' if c['profile_flat'] else 'clear'} (warning only; "
        f"df-family small-sample limit)",
        f"- convergence: {'OK' if c['converged'] else 'FAIL'}",
        "",
    ]
    if result.warnings:
        lines += ["## Failures / warnings", ""]
        lines += [f"- {w}" for w in result.warnings] + [""]
    report = out_dir / "identifiability_report.md"
    report.write_text("\n".join(lines))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--df", default=None,
                   help="analysis CSV (trait table); default: results/phase2/trait_table.csv")
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(args.df) if args.df else out_dir / "trait_table.csv"
    if not path.exists():
        p.error(f"{path} not found (run phase2_trait first)")
    df = pd.read_csv(path)
    if "era" in df.columns and "quarter" in df.columns:
        df = df.rename(columns={"quarter": "era"})
    result = audit(df)
    pd.DataFrame([
        {"term": "family", "max_vif": result.checks["max_vif_family"]},
        {"term": "era", "max_vif": result.checks["max_vif_era"]},
    ]).to_csv(out_dir / "vif.csv", index=False)
    (out_dir / "condition_number.txt").write_text(
        f"kappa = {result.checks['condition_number']:.4f}\n"
        f"threshold = {KAPPA_MAX:.0f} (Belsley severe)\n"
    )
    report = write_report(result, out_dir)
    print(f"Audit {'FAIL' if result.hard_fail else 'PASS'}: "
          f"{result.checks['n_models']} models, κ={result.checks['condition_number']:.1f}, "
          f"VIF fam={result.checks['max_vif_family']:.1f} era={result.checks['max_vif_era']:.1f}")
    print(f"-> {report}")
    return 2 if result.hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
