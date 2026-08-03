"""G3 gate: the minimum VALID connected-subset population for the Phase 2 eval.

Pre-registered 2026-08-03 (see Research_Decision_Log): BEFORE any GPU spend,
select the smallest connected-subset population whose family x quarter design
is identifiable AND whose era recovery clears the strict Phase 1 D2-continuous
bar (|era share bias| <= 5pp AND era-share CI coverage >= 90%). If the answer
is all 47, the full cost is scientifically justified; if fewer, GPU time drops
without weakening the paper.

Rule (structural only — no accuracy data is ever consulted):
1. Minimize model count subject to hard constraints:
   - all 6 families present; every family spans >= 2 quarters (Phase 0 crossed
     verdict); >= 2 quarters contain >= 2 families (crossed);
   - every quarter 2023Q1-2026Q2 keeps >= 1 model (era-convergence window);
   - the in-subset VERIFIED_EDGES endpoints AND the documented Mistral-Small
     chain are kept (theta_M survives the subset);
   - the induced design passes identifiability.structural_checks (full rank,
     VIF <= 10) — verified after selection, re-solved with a cut if not.
2. Tie-break on cost (public > gated, then est_minutes_single_gpu) for
   equal-count subsets — deterministic (scipy Highs).
3. "Valid", not just "identifiable": fixed-design DGP battery (dgp.simulate_trait
   on the subset occupancy, scenarios A and B, mean over reps) must satisfy the
   strict bar above. First n that passes is the minimum VALID population.

Search: scipy.optimize.milp (Highs, ~145 binary vars) for the structural
minimum, then n = n0, n0+1, ... with sum(x)=n + min cost; candidates that clear
the strict bar at the search reps must ALSO clear it at a high-precision
confirmation battery (heavy-tailed per-rep bias, register A21) before being
accepted; first confirmed n wins.

Outputs:
- datasets/coverage/minimal_population.csv  (kept/dropped + per-model reason)
- datasets/coverage/g3_report.md            (search trace + validation table)

Usage (from src/):
    python3 -m lineage_era.phase2_population_optimizer \
        [--reps 300] [--confirm-reps 1000] [--out-dir ../datasets/coverage]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from .. import dgp
from ..metrics import coverage, share_bias_pp
from ..occupancy import FAMILIES, MODELS, QUARTERS
from ..phase2_eval import EVAL_MANIFEST
from . import reml
from .gpu_cost import build_cost_table
from .identifiability import structural_checks

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_DIR = REPO_ROOT / "datasets" / "coverage"

# Strict bar (Phase 1 D2-continuous gate; phase1_simulation.GATE).
BIAS_PP_MAX = 5.0
COVERAGE_MIN = 90.0
CONVERGENCE_MIN = 90.0

# High-precision confirmation must clear the bar with >= 1pp margin, so the
# accepted population is robustly inside the bar rather than knife-edge on the
# heavy-tailed per-rep bias distribution (register A21).
CONFIRM_MARGIN_PP = 1.0
CONFIRM_BIAS_PP_MAX = BIAS_PP_MAX - CONFIRM_MARGIN_PP

# Edge endpoints (VERIFIED_EDGES, shortened names) -> connected-subset names.
# Endpoints outside the subset (Phi-4-reasoning, V3.2-Exp-Base) carry no
# constraint; only in-subset members force a keep.
EDGE_ENDPOINT_TO_FULLNAME = {
    "Llama-3.3-70B-Instruct": "Llama-3.3",
    "Llama-3.1-70B": "Llama-3.1",
    "Phi-4-reasoning-plus": "Phi-4-reasoning-plus",
    "phi-4": "Phi-4",
    "Phi-4-reasoning-vision-15B": "Phi-4-reasoning-vision-15B",
    "Devstral-Small-2": "Devstral-2",
    "Mistral-Small-3.1-Base": "Mistral-Small-3.1",
    "DeepSeek-V3.2": "DeepSeek-V3.2",
}
# Documented within-family chain (occupancy.CAVEATS), kept for theta_M.
MISTRAL_SMALL_CHAIN = ["Mistral-Small-3", "Mistral-Small-3.1",
                       "Mistral-Small-3.2", "Mistral-Small-4", "Devstral-2"]

FORCED = sorted({EDGE_ENDPOINT_TO_FULLNAME[e] for e in EDGE_ENDPOINT_TO_FULLNAME}
                | set(MISTRAL_SMALL_CHAIN))

VALIDATION_SCENARIOS = ("A", "B")  # lineage-dominant, era-dominant
_SEEDS = {"A": 101, "B": 202}      # fixed per scenario (deterministic battery)


# --------------------------------------------------------------- design
def subset_table(full_names: list[str]) -> pd.DataFrame:
    """MODELS rows restricted to ``full_names``, deterministic order."""
    df = pd.DataFrame(MODELS, columns=["family", "quarter", "short_name", "full_name"])
    sub = df[df["full_name"].isin(set(full_names))].copy()
    sub = sub.sort_values(["quarter", "family", "full_name"]).reset_index(drop=True)
    return sub


def subset_design(full_names: list[str]) -> pd.DataFrame:
    """dgp design frame (model, family, era) for the selected subset."""
    sub = subset_table(full_names)
    return pd.DataFrame({
        "model": range(len(sub)),
        "family": sub["family"].tolist(),
        "era": sub["quarter"].tolist(),
    })


def structural_ok(full_names: list[str]) -> tuple[bool, dict]:
    """Induced family x era design: full rank, VIF <= 10, families/quarters/span."""
    df = subset_design(full_names)
    checks = structural_checks(df)
    span = df.groupby("family")["era"].nunique()
    ok = bool(
        checks["rank_ok"]
        and checks["vif_ok"]
        and len(span) == len(FAMILIES)
        and (span >= 2).all()
    )
    return ok, checks


# --------------------------------------------------------------- MILP
def _milp_solve(forced: list[str], size: int | None,
                cost: np.ndarray, banned: list[list[str]],
                n_models: int, cells: list[tuple[str, str]]) -> list[str] | None:
    """Solve the binary selection LP; return selected full_names (or None)."""
    n_vars = n_models + len(cells) + len(QUARTERS)
    cell_ix = {cl: n_models + i for i, cl in enumerate(cells)}
    q_ix = {q: n_models + len(cells) + i for i, q in enumerate(QUARTERS)}
    family_of = {m[3]: m[0] for m in MODELS}
    quarter_of = {m[3]: m[1] for m in MODELS}
    models = [m[3] for m in MODELS]

    rows: list[tuple[dict[int, float], float, float]] = []  # (coeffs, lb, ub)

    def add(row: dict[int, float], lb: float, ub: float) -> None:
        rows.append((row, lb, ub))

    # x_m <= c_cell(m);  c_cell <= sum x over the cell.
    for m, fn in enumerate(models):
        add({m: 1.0, cell_ix[(family_of[fn], quarter_of[fn])]: -1.0}, -np.inf, 0.0)
    for cl, ix in cell_ix.items():
        fam, q = cl
        coeff = {ix: 1.0}
        for m, fn in enumerate(models):
            if family_of[fn] == fam and quarter_of[fn] == q:
                coeff[m] = -1.0
        add(coeff, -np.inf, 0.0)

    # Family span >= 2; quarter coverage >= 1; crossed: >=2 quarters w/ >=2 fams.
    for f in FAMILIES:
        add({cell_ix[(f, q)]: -1.0 for q in QUARTERS if (f, q) in cell_ix},
            -np.inf, -2.0)
    for q in QUARTERS:
        add({cell_ix[(f, q)]: -1.0 for f in FAMILIES if (f, q) in cell_ix},
            -np.inf, -1.0)
    for q in QUARTERS:
        fams = [f for f in FAMILIES if (f, q) in cell_ix]
        row = {q_ix[q]: 2.0}
        row.update({cell_ix[(f, q)]: -1.0 for f in fams})
        add(row, -np.inf, 0.0)
    add({q_ix[q]: -1.0 for q in QUARTERS}, -np.inf, -2.0)

    # Forced keeps (edges + chain) are equality.
    for fn in forced:
        m = models.index(fn)
        add({m: 1.0}, 1.0, 1.0)
    if size is not None:
        add({m: 1.0 for m in range(n_models)}, float(size), float(size))
    for s in banned:
        add({m: 1.0 for m, fn in enumerate(models) if fn in s},
            -np.inf, float(len(s) - 1))

    A = np.zeros((len(rows), n_vars))
    lb = np.full(len(rows), -np.inf)
    ub = np.full(len(rows), np.inf)
    for i, (coeff, lo, hi) in enumerate(rows):
        for j, v in coeff.items():
            A[i, j] = v
        lb[i], ub[i] = lo, hi

    c_full = np.zeros(n_vars)
    c_full[:n_models] = cost
    res = milp(
        c=c_full,
        integrality=np.ones(n_vars),
        bounds=Bounds(np.zeros(n_vars), np.ones(n_vars)),
        constraints=[LinearConstraint(A, lb, ub)],
        options={"time_limit": 60, "mip_rel_gap": 0.0},
    )
    if res.x is None or res.status != 0:
        return None
    return [fn for m, fn in enumerate(models) if res.x[m] > 0.5]


def cost_vector() -> np.ndarray:
    """Secondary objective: public first, then est minutes; gated = +1e4."""
    est = build_cost_table().set_index("full_name")["est_minutes_single_gpu"]
    c = np.zeros(len(MODELS))
    for i, (_, _, _, fn) in enumerate(MODELS):
        gated = 1e4 if EVAL_MANIFEST[fn][2] == "gated" else 0.0
        c[i] = gated + float(est.loc[fn])
    return c


def structural_minimum(attempts: int = 8) -> tuple[int, list[str]]:
    """Smallest count with a structurally identifiable design (rank + VIF)."""
    cells = sorted({(m[0], m[1]) for m in MODELS})
    lb = max(len(QUARTERS), len(FORCED))
    for n in range(lb, len(MODELS) + 1):
        banned: list[list[str]] = []
        for _ in range(attempts):
            s = _milp_solve(FORCED, n, np.ones(len(MODELS)), banned,
                            len(MODELS), cells)
            if s is None:
                break
            ok, _ = structural_ok(s)
            if ok:
                return n, s
            banned.append(s)
    return len(MODELS), [m[3] for m in MODELS]


# ------------------------------------------------------------- validation
def validate_subset(full_names: list[str], reps: int = 100) -> dict:
    """Strict-bar battery on the FIXED subset occupancy (scenarios A and B).

    Mean over converged reps (register A21): era share |bias| <= BIAS_PP_MAX,
    era share CI coverage >= COVERAGE_MIN, convergence >= CONVERGENCE_MIN.
    """
    design = subset_design(full_names)
    out = {}
    for scen in VALIDATION_SCENARIOS:
        rng = np.random.default_rng(_SEEDS[scen])
        truth = dgp.SCENARIOS[scen]["E"]
        eras, covers, conv = [], [], []
        for _ in range(reps):
            df = dgp.simulate_trait(design, dgp.SCENARIOS[scen], rng)
            fit = reml.fit_lpm_vcomp(df)
            if not fit.converged:
                continue
            ci = reml.share_ci(fit)
            eras.append(fit.shares["era"])
            covers.append(coverage(ci["era"], truth))
            conv.append(True)
        n_conv = len(conv)
        conv_pct = 100.0 * n_conv / reps if reps else 0.0
        out[scen] = {
            "era_bias_pp": share_bias_pp(float(np.mean(eras)) if eras else np.nan,
                                         truth),
            "era_coverage_pct": (100.0 * np.mean(covers) if covers else np.nan),
            "convergence_pct": conv_pct,
        }
    out["n"] = len(full_names)
    return out


def validation_passes(val: dict, bias_max: float = BIAS_PP_MAX) -> bool:
    for scen in VALIDATION_SCENARIOS:
        r = val[scen]
        if not (abs(r["era_bias_pp"]) <= bias_max
                and r["era_coverage_pct"] >= COVERAGE_MIN
                and r["convergence_pct"] >= CONVERGENCE_MIN):
            return False
    return True


def _row_from_val(n: int, names: list[str], ok: bool, checks: dict,
                  val: dict | None) -> dict:
    row: dict = {"n": n, "n_models": len(names), "structural_ok": ok,
                 "rank_ok": bool(checks["rank_ok"]),
                 "vif_ok": bool(checks["vif_ok"]), "pass": False}
    if val is not None:
        row["pass"] = validation_passes(val)
        for scen in VALIDATION_SCENARIOS:
            row[f"bias_pp_{scen}"] = round(val[scen]["era_bias_pp"], 2)
            row[f"cov_pct_{scen}"] = round(val[scen]["era_coverage_pct"], 1)
            row[f"conv_pct_{scen}"] = round(val[scen]["convergence_pct"], 1)
    return row


# ----------------------------------------------------------------- search
def find_minimal_valid(reps: int = 300, confirm_reps: int = 1000,
                       attempts: int = 20) -> dict:
    """Two-stage search: probe at ``reps``, confirm winners at ``confirm_reps``.

    The per-rep share-bias distribution is heavy-tailed (register A21), so a
    candidate must ALSO clear the strict bar WITH >= CONFIRM_MARGIN_PP margin
    at the high-precision confirmation battery before it is accepted. This
    rejects knife-edge cases (e.g. the structural minimum sitting at the
    -5.0pp boundary) where the SE at any feasible reps count cannot separate
    pass from fail.

    Returns {n0, n_valid, subset, results, baseline, baseline_confirmed}.
    """
    cells = sorted({(m[0], m[1]) for m in MODELS})
    n0, s0 = structural_minimum()

    baseline = validate_subset([m[3] for m in MODELS], reps=reps)
    baseline_ok = validation_passes(baseline)
    if not baseline_ok:
        raise RuntimeError(
            "G3 baseline FAIL: the full 47-model design does not pass the strict "
            "bar — re-check the validator before trusting any subset result. "
            f"{baseline}")
    baseline_confirmed = validate_subset([m[3] for m in MODELS],
                                         reps=confirm_reps)
    if not validation_passes(baseline_confirmed, CONFIRM_BIAS_PP_MAX):
        raise RuntimeError(
            "G3 baseline FAIL at confirmation reps — re-check before trusting "
            f"any subset result. {baseline_confirmed}")

    def probe(names: list[str], n: int, checks: dict) -> dict | None:
        """Validate at reps, confirm at confirm_reps (with margin); return row."""
        val = validate_subset(names, reps=reps)
        row = _row_from_val(n, names, True, checks, val)
        if row["pass"]:
            conf = validate_subset(names, reps=confirm_reps)
            for scen in VALIDATION_SCENARIOS:
                row[f"bias_pp_{scen}_conf"] = round(
                    conf[scen]["era_bias_pp"], 2)
                row[f"cov_pct_{scen}_conf"] = round(
                    conf[scen]["era_coverage_pct"], 1)
            row["pass"] = validation_passes(conf, CONFIRM_BIAS_PP_MAX)
        results.append(row)
        return row

    results: list[dict] = []
    # Document the structural minimum n0 explicitly: it may fail the strict bar
    # (or its confirmation), which is exactly the point of the validation stage.
    s0_checks = structural_ok(s0)[1]
    s0_row = probe(s0, n0, s0_checks)
    s0_row["source"] = "structural-minimum (uniform objective)"
    if s0_row["pass"]:
        return {"n0": n0, "s0": s0, "n_valid": n0, "subset": s0,
                "results": results, "baseline": baseline,
                "baseline_ok": baseline_ok,
                "baseline_confirmed": baseline_confirmed}

    cost = cost_vector()
    ones = np.ones(len(MODELS))
    for n in range(n0, len(MODELS) + 1):
        banned = [s0] if n == n0 else []
        for attempt in range(attempts):
            obj = cost if attempt % 2 == 0 else ones
            s = _milp_solve(FORCED, n, obj, banned, len(MODELS), cells)
            if s is None:
                break
            ok, checks = structural_ok(s)
            if not ok:
                results.append(_row_from_val(n, s, False, checks, None))
                banned.append(s)
                continue
            row = probe(s, n, checks)
            if row["pass"]:
                return {"n0": n0, "s0": s0, "n_valid": n, "subset": s,
                        "results": results, "baseline": baseline,
                        "baseline_ok": baseline_ok,
                        "baseline_confirmed": baseline_confirmed}
            banned.append(s)
    # Fallback: full 47 required (cost scientifically justified).
    full = [m[3] for m in MODELS]
    return {"n0": n0, "s0": s0, "n_valid": len(MODELS), "subset": full,
            "results": results, "baseline": baseline, "baseline_ok": baseline_ok,
            "baseline_confirmed": baseline_confirmed}


# ---------------------------------------------------------------- outputs
def _reason(fn: str, kept: set[str]) -> str:
    if fn in FORCED:
        return "edge-or-chain-forced (theta_M)"
    if fn not in kept:
        return "dropped: redundant in-cell replication (identifiability unchanged)"
    return "replication: required by the strict era-recovery gate"


def write_outputs(res: dict, out_dir: Path, reps: int = 300,
                  confirm_reps: int = 1000) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = set(res["subset"])
    table = subset_table([m[3] for m in MODELS])
    table["kept"] = table["full_name"].isin(kept)
    table["reason"] = [ _reason(fn, kept) for fn in table["full_name"]]
    csv_path = out_dir / "minimal_population.csv"
    table.to_csv(csv_path, index=False)

    lines = [
        "# G3 — Minimum Valid Population (2026-08-03, pre-registered)",
        "",
        f"Strict bar (Phase 1 D2 gate, mean over converged reps/scenario, "
        f"seeds {_SEEDS}): |era share bias| <= {BIAS_PP_MAX}pp AND era-share CI "
        f"coverage >= {COVERAGE_MIN}%; convergence >= {CONVERGENCE_MIN}%.",
        "",
        "Two-stage decision (heavy-tailed per-rep bias, register A21): candidates "
        f"that clear the bar at {reps} reps must ALSO clear it with "
        f">= {CONFIRM_MARGIN_PP}pp margin (|bias| <= {CONFIRM_BIAS_PP_MAX}pp) at a "
        f"high-precision {confirm_reps}-rep confirmation before acceptance — "
        "knife-edge designs sitting on the bar are rejected.",
        "",
        f"Structural minimum n0 = {res['n0']} (identifiable: full rank + VIF<=10).",
        f"**Minimum VALID population = {res['n_valid']}** of 47 "
        f"({'all 47 required' if res['n_valid'] == len(MODELS) else 'reduced'}).",
        "",
        f"Baseline (full 47) at {reps} reps: {res['baseline']} -> "
        f"{'PASS' if res['baseline_ok'] else 'FAIL'} strict bar",
        "",
        "| n | models | rank | vif | pass | bias A | cov% A | bias B | cov% B "
        "| bias A conf | bias B conf |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in res["results"]:
        lines.append(
            f"| {r['n']} | {r['n_models']} | {r['rank_ok']} | {r['vif_ok']} "
            f"| {r['pass']} | {r.get('bias_pp_A', '-')} | {r.get('cov_pct_A', '-')} "
            f"| {r.get('bias_pp_B', '-')} | {r.get('cov_pct_B', '-')} "
            f"| {r.get('bias_pp_A_conf', '-')} | {r.get('bias_pp_B_conf', '-')} |")
    report_path = out_dir / "g3_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    return csv_path, report_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reps", type=int, default=300,
                   help="search validation reps/seed")
    p.add_argument("--confirm-reps", type=int, default=1000,
                   help="high-precision confirmation reps for passing candidates")
    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = p.parse_args(argv)

    res = find_minimal_valid(reps=args.reps, confirm_reps=args.confirm_reps)
    csv_path, report_path = write_outputs(res, Path(args.out_dir),
                                          reps=args.reps,
                                          confirm_reps=args.confirm_reps)
    print(f"G3: n0 = {res['n0']}, minimum VALID = {res['n_valid']}/47")
    print(f"-> {csv_path}")
    print(f"-> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
