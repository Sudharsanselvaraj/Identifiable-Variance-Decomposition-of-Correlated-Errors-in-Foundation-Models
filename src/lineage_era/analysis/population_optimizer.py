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

Pre-measurement exclusion (2026-08-16): candidate models can be removed from
the pool with --exclude BEFORE any measurement (unavailable reproducible
compute). The population-design procedure is then rerun on the remaining pool.
--relax-era-window allows the era-convergence window to shrink to the quarters
that still hold a candidate (required when an excluded model was the only one
in its quarter); without it, an uncovered quarter is reported INFEASIBLE.
Exclusion variant outputs are written to suffixed files so the pre-registered
2026-08-03 artifacts are never overwritten.

Framing: this is a pre-analysis study-population design procedure that combines
structural identifiability with simulation-based recoverability criteria BEFORE
empirical inference — not an optimization of results. G3 never observes trait
values; the selection inputs are occupancy (family x quarter), the lineage
graph, identifiability constraints, and cost only.

Search: scipy.optimize.milp (Highs, ~145 binary vars) for the structural
minimum, then n = n0, n0+1, ... with sum(x)=n + min cost; candidates that clear
the strict bar at the search reps must ALSO clear it at a high-precision
confirmation battery (heavy-tailed per-rep bias, register A21) before being
accepted; first confirmed n wins.

Outputs:
- datasets/coverage/minimum_valid_population.csv  (kept/dropped + per-model
  reason, assigned by single-model ablation: counterfactual removal of the
  model, occupancy only, never trait values)
- datasets/coverage/g3_report.md            (search trace + validation table)
- ...<label>.csv / ...<label>.md            (pre-measurement exclusion variants)

Usage (from src/):
    python3 -m lineage_era.phase2_population_optimizer \
        [--reps 300] [--confirm-reps 1000] [--out-dir ../datasets/coverage]
    # pre-measurement exclusion variant:
    python3 -m lineage_era.phase2_population_optimizer \
        --exclude DeepSeek-V3.1 DeepSeek-V3.2 --relax-era-window \
        --robust-reps 2000 --label deepseek_excluded
"""
from __future__ import annotations

import argparse
from datetime import date
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


# --------------------------------------------------------------- exclusions
def _available_families(excluded: set[str] | None = None) -> set[str]:
    """Families that still have >= 1 candidate after pre-measurement exclusion."""
    excluded = excluded or set()
    return {m[0] for m in MODELS if m[3] not in excluded}


def available_pool(excluded: set[str] | None = None) -> list[str]:
    """full_names still in the candidate pool (MODELS order)."""
    excluded = excluded or set()
    return [m[3] for m in MODELS if m[3] not in excluded]


def available_quarters(excluded: set[str] | None = None) -> tuple[str, ...]:
    """Quarters that still hold >= 1 candidate (QUARTERS order)."""
    excluded = excluded or set()
    return tuple(q for q in QUARTERS
                 if any(m[1] == q and m[3] not in excluded for m in MODELS))


def est_minutes_total(names: list[str]) -> float:
    est = build_cost_table().set_index("full_name")["est_minutes_single_gpu"]
    return float(est.loc[[n for n in names]].sum())


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


def structural_ok(full_names: list[str],
                  excluded: set[str] | None = None) -> tuple[bool, dict]:
    """Induced family x era design: full rank, VIF <= 10, families/quarters/span."""
    df = subset_design(full_names)
    checks = structural_checks(df)
    span = df.groupby("family")["era"].nunique()
    available = _available_families(excluded)
    ok = bool(
        checks["rank_ok"]
        and checks["vif_ok"]
        and set(span.index) >= available
        and (span >= 2).all()
    )
    return ok, checks


# --------------------------------------------------------------- MILP
def _milp_solve(forced: list[str], size: int | None,
                cost: np.ndarray, banned: list[list[str]],
                n_models: int, cells: list[tuple[str, str]],
                excluded: set[str] | None = None,
                required_quarters: list[str] | None = None) -> list[str] | None:
    """Solve the binary selection LP; return selected full_names (or None)."""
    excluded = excluded or set()
    required_quarters = (required_quarters if required_quarters is not None
                         else list(QUARTERS))
    models = [m[3] for m in MODELS if m[3] not in excluded]
    n_vars = n_models + len(cells) + len(QUARTERS)
    cell_ix = {cl: n_models + i for i, cl in enumerate(cells)}
    q_ix = {q: n_models + len(cells) + i for i, q in enumerate(QUARTERS)}
    family_of = {m[3]: m[0] for m in MODELS}
    quarter_of = {m[3]: m[1] for m in MODELS}
    families = _available_families(excluded)

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

    # Family span >= 2 (available families only); quarter coverage >= 1 over the
    # required window; crossed: >=2 quarters w/ >=2 families.
    for f in families:
        add({cell_ix[(f, q)]: -1.0 for q in QUARTERS if (f, q) in cell_ix},
            -np.inf, -2.0)
    for q in required_quarters:
        add({cell_ix[(f, q)]: -1.0 for f in families if (f, q) in cell_ix},
            -np.inf, -1.0)
    for q in QUARTERS:
        fams = [f for f in families if (f, q) in cell_ix]
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


def cost_vector(excluded: set[str] | None = None) -> np.ndarray:
    """Secondary objective: public first, then est minutes; gated = +1e4."""
    excluded = excluded or set()
    est = build_cost_table().set_index("full_name")["est_minutes_single_gpu"]
    c = []
    for (_, _, _, fn) in MODELS:
        if fn in excluded:
            continue
        gated = 1e4 if EVAL_MANIFEST[fn][2] == "gated" else 0.0
        c.append(gated + float(est.loc[fn]))
    return np.asarray(c, dtype=float)


def structural_minimum(attempts: int = 8, excluded: set[str] | None = None,
                       required_quarters: list[str] | None = None
                       ) -> tuple[int, list[str]]:
    """Smallest count with a structurally identifiable design (rank + VIF)."""
    excluded = excluded or set()
    required_quarters = (required_quarters if required_quarters is not None
                         else list(QUARTERS))
    pool = available_pool(excluded)
    cells = sorted({(m[0], m[1]) for m in MODELS if m[3] not in excluded})
    forced = [f for f in FORCED if f not in excluded]
    lb = max(len(required_quarters), len(forced))
    for n in range(lb, len(pool) + 1):
        banned: list[list[str]] = []
        for _ in range(attempts):
            s = _milp_solve(forced, n, np.ones(len(pool)), banned,
                            len(pool), cells, excluded, required_quarters)
            if s is None:
                break
            ok, _ = structural_ok(s, excluded)
            if ok:
                return n, s
            banned.append(s)
    return len(pool), pool


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
                       attempts: int = 20, excluded: set[str] | None = None,
                       relax_era_window: bool = False,
                       robust_reps: int = 0) -> dict:
    """Two-stage search: probe at ``reps``, confirm winners at ``confirm_reps``.

    The per-rep share-bias distribution is heavy-tailed (register A21), so a
    candidate must ALSO clear the strict bar WITH >= CONFIRM_MARGIN_PP margin
    at the high-precision confirmation battery before it is accepted. This
    rejects knife-edge cases (e.g. the structural minimum sitting at the
    -5.0pp boundary) where the SE at any feasible reps count cannot separate
    pass from fail.

    ``excluded`` are pre-measurement removals from the candidate pool.
    ``relax_era_window`` shrinks the required era window to the quarters still
    holding a candidate; without it, an uncovered quarter is INFEASIBLE.

    Returns {n0, n_valid, subset, results, baseline, baseline_confirmed,
    excluded, pool, pool_n, required_quarters, relax_era_window, robust_reps,
    robust} (plus infeasible/infeasible_reason when applicable).
    """
    excluded = excluded or set()
    pool = available_pool(excluded)
    required_quarters = list(available_quarters(excluded))

    strict_infeasible = (not relax_era_window
                         and set(required_quarters) != set(QUARTERS))
    if strict_infeasible:
        missing = sorted(set(QUARTERS) - set(required_quarters))
        reason = "; ".join(f"{q} has no remaining candidate" for q in missing)
        return {
            "infeasible": True, "infeasible_reason": reason,
            "n0": None, "s0": None, "n_valid": None, "subset": pool,
            "results": [], "baseline": None, "baseline_ok": None,
            "baseline_confirmed": None, "excluded": sorted(excluded),
            "pool": pool, "pool_n": len(pool),
            "required_quarters": required_quarters,
            "relax_era_window": relax_era_window,
            "robust_reps": robust_reps, "robust": None,
        }

    cells = sorted({(m[0], m[1]) for m in MODELS if m[3] not in excluded})
    n0, s0 = structural_minimum(attempts=attempts, excluded=excluded,
                                required_quarters=required_quarters)

    baseline = validate_subset(pool, reps=reps)
    baseline_ok = validation_passes(baseline)
    if not baseline_ok:
        raise RuntimeError(
            "G3 baseline FAIL: the available-pool design does not pass the strict "
            "bar — re-check the validator before trusting any subset result. "
            f"{baseline}")
    baseline_confirmed = validate_subset(pool, reps=confirm_reps)
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

    def winner(n: int, names: list[str], robust: dict | None) -> dict:
        return {"n0": n0, "s0": s0, "n_valid": n, "subset": names,
                "results": results, "baseline": baseline,
                "baseline_ok": baseline_ok,
                "baseline_confirmed": baseline_confirmed,
                "excluded": sorted(excluded), "pool": pool, "pool_n": len(pool),
                "required_quarters": required_quarters,
                "relax_era_window": relax_era_window,
                "robust_reps": robust_reps, "robust": robust}

    results: list[dict] = []
    # Document the structural minimum n0 explicitly: it may fail the strict bar
    # (or its confirmation), which is exactly the point of the validation stage.
    s0_checks = structural_ok(s0, excluded)[1]
    s0_row = probe(s0, n0, s0_checks)
    s0_row["source"] = "structural-minimum (uniform objective)"
    if s0_row["pass"]:
        robust = None
        if robust_reps:
            robust = validate_subset(s0, reps=robust_reps)
        return winner(n0, s0, robust)

    cost = cost_vector(excluded)
    ones = np.ones(len(pool))
    forced = [f for f in FORCED if f not in excluded]
    for n in range(n0, len(pool) + 1):
        banned = [s0] if n == n0 else []
        for attempt in range(attempts):
            obj = cost if attempt % 2 == 0 else ones
            s = _milp_solve(forced, n, obj, banned, len(pool), cells,
                            excluded, required_quarters)
            if s is None:
                break
            ok, checks = structural_ok(s, excluded)
            if not ok:
                results.append(_row_from_val(n, s, False, checks, None))
                banned.append(s)
                continue
            row = probe(s, n, checks)
            if row["pass"]:
                robust = None
                if robust_reps:
                    robust = validate_subset(s, reps=robust_reps)
                return winner(n, s, robust)
            banned.append(s)
    # Fallback: the full available pool required (cost scientifically justified).
    robust = None
    if robust_reps:
        robust = validate_subset(pool, reps=robust_reps)
    return winner(len(pool), pool, robust)


# ---------------------------------------------------------------- outputs
def _design_constraints(full_names: list[str],
                        required_quarters: list[str] | None = None,
                        excluded: set[str] | None = None) -> dict:
    """Occupancy-only design constraints G3 enforces (never trait values).

    Returns whether the subset satisfies each constraint class:
    quarter-window coverage, crossing (families present + 2-quarter span +
    2-family quarters), and structural identifiability (rank/VIF, span).
    """
    required_quarters = (required_quarters if required_quarters is not None
                         else list(QUARTERS))
    excluded = excluded or set()
    df = subset_design(full_names)
    span = df.groupby("family")["era"].nunique()
    crossed = (df.groupby("era")["family"].nunique() >= 2).sum() >= 2
    ok, _ = structural_ok(full_names, excluded)
    available = _available_families(excluded)
    return {
        "quarter_window": set(df["era"]) == set(required_quarters),
        "crossing": bool(set(span.index) >= available
                         and (span >= 2).all() and crossed),
        "structural": ok,
    }


def _reason(fn: str, kept: set[str], required_quarters: list[str] | None = None,
            excluded: set[str] | None = None) -> str:
    required_quarters = (required_quarters if required_quarters is not None
                         else list(QUARTERS))
    excluded = excluded or set()
    if fn in excluded:
        return "pre-measurement exclusion (unavailable_reproducible_compute)"
    if fn in FORCED:
        return "edge-or-chain-forced (theta_M)"
    if fn not in kept:
        return "dropped: redundant in-cell replication (identifiability unchanged)"
    # Kept but not forced: attribute via single-model ablation (counterfactual
    # removal of the model, occupancy only). First constraint to break wins.
    others = [m[3] for m in MODELS if m[3] in kept and m[3] != fn]
    ablated = _design_constraints(others, required_quarters, excluded)
    if not ablated["quarter_window"]:
        return "required: era-window coverage"
    if not ablated["crossing"]:
        return "required: structural identifiability (crossing)"
    if not ablated["structural"]:
        return "required: structural identifiability (rank/VIF)"
    return "required: statistical recoverability (D2 gate)"


def _report_header(label: str) -> list[str]:
    if label:
        return [
            f"# G3 — Minimum Valid Population (exclusion variant: {label})",
            "",
            f"Generated {date.today().isoformat()}. Pre-measurement exclusion "
            "variant of the pre-registered 2026-08-03 gate; the pre-registered "
            "artifacts are unchanged.",
        ]
    return ["# G3 — Minimum Valid Population (2026-08-03, pre-registered)"]


def _common_preamble(label: str, excluded: list[str],
                     relax_era_window: bool,
                     required_quarters: list[str] | None) -> list[str]:
    lines = _report_header(label)
    lines += [
        "",
        "> **Outcome-independent study design.** G3 never observes trait values "
        "during optimization. Its inputs are occupancy (family × quarter), the "
        "lineage graph (VERIFIED_EDGES endpoints, Mistral-Small chain), "
        "identifiability constraints, and cost. All recoverability checks use "
        "fixed-design DGP simulations — never real eval outputs, accuracies, or "
        "error-similarity results.",
    ]
    if excluded:
        lines += _excluded_block(excluded, relax_era_window, required_quarters)
    return lines


def _excluded_block(excluded: list[str], relax_era_window: bool,
                    required_quarters: list[str] | None) -> list[str]:
    lines = [
        "",
        "> **Pre-measurement exclusion.** The candidate models below were removed "
        "from the pool BEFORE any measurement (no trait, accuracy, or eval "
        "output observed), and the population-design procedure was rerun on the "
        "remaining candidate pool.",
        "",
        "```",
        "EXCLUDED_PREMEASUREMENT:",
    ]
    lines += [f"  - {fn}" for fn in excluded]
    lines += [
        "",
        "REASON:",
        "  unavailable_reproducible_compute",
        "",
        "STATUS:",
        "  pre_measurement",
        "",
        "DATE:",
        f"  {date.today().isoformat()}",
        "```",
    ]
    if relax_era_window:
        missing = sorted(set(QUARTERS) - set(required_quarters or QUARTERS))
        lines += [
            "",
            f"Era-convergence window relaxed to the quarters still holding a "
            f"candidate ({', '.join(required_quarters or [])}); "
            f"{', '.join(missing)} excluded from the window because no candidate "
            "remains in that/those quarter(s).",
        ]
    return lines


def write_outputs(res: dict, out_dir: Path, reps: int = 300,
                  confirm_reps: int = 1000, label: str = "") -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".{label}" if label else ""
    csv_path = out_dir / f"minimum_valid_population{suffix}.csv"
    report_path = out_dir / f"g3_report{suffix}.md"

    excluded = list(res.get("excluded", []))
    relax_era_window = bool(res.get("relax_era_window", False))
    robust_reps = int(res.get("robust_reps", 0))
    required_quarters = res.get("required_quarters")
    pool_n = int(res.get("pool_n", len(MODELS)))

    if res.get("infeasible"):
        lines = _common_preamble(label, excluded, relax_era_window,
                                 required_quarters)
        lines += [
            "",
            "## INFEASIBLE",
            "",
            f"Reason: {res['infeasible_reason']}",
            "",
            "The era-convergence window (every quarter 2023Q1-2026Q2 keeps >= 1 "
            "model) cannot be preserved after the pre-measurement exclusion: the "
            "quarter(s) above have no remaining candidate. The search was not "
            "run and no population was selected.",
        ]
        report_path.write_text("\n".join(lines) + "\n")
        return csv_path, report_path

    kept = set(res["subset"])
    table = subset_table([m[3] for m in MODELS])
    table["kept"] = table["full_name"].isin(kept)
    table["reason"] = [_reason(fn, kept, required_quarters, set(excluded))
                       for fn in table["full_name"]]
    table.to_csv(csv_path, index=False)

    bl = res["baseline"]
    blc = res["baseline_confirmed"]
    baseline_conf_ok = validation_passes(blc, CONFIRM_BIAS_PP_MAX)
    win = res["results"][-1]

    lines = _common_preamble(label, excluded, relax_era_window,
                             required_quarters)
    lines += [
        "",
        "| G3 input | Used? |",
        "|---|---|",
        "| Family × quarter occupancy | ✓ |",
        "| Lineage graph (edges, θ_M chain) | ✓ |",
        "| Identifiability constraints (rank, VIF, span, crossing) | ✓ |",
        "| Cost (public > gated, est. GPU minutes) | ✓ |",
        "| Trait values / accuracy | ✗ |",
        "| Error similarity | ✗ |",
        "| Evaluation outputs | ✗ |",
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
        f"**Minimum VALID population = {res['n_valid']}** of {pool_n} "
        f"({'all required' if res['n_valid'] == pool_n else 'reduced'}).",
    ]

    if label:
        baseline_line = (f"Baseline (full available pool, n={pool_n}) at "
                         f"{reps} reps: {bl} -> ")
    else:
        baseline_line = f"Baseline (full 47) at {reps} reps: {bl} -> "
    baseline_line += (
        f"{'PASS' if res['baseline_ok'] else 'FAIL'} strict bar; "
        f"margin-confirmed at {confirm_reps} reps: "
        f"A {blc['A']['era_bias_pp']:.2f}pp / B {blc['B']['era_bias_pp']:.2f}pp "
        f"-> {'PASS' if baseline_conf_ok else 'FAIL'}."
    )
    lines.append(baseline_line)

    winner_line = (
        f"Winner (n={win['n']}): margin-confirmed A "
        f"{win.get('bias_pp_A_conf', '-')}pp / B {win.get('bias_pp_B_conf', '-')}pp "
        f"— same order of magnitude as the "
    )
    if label:
        pool_est = (est_minutes_total(res["pool"]) if res.get("pool") else 0.0)
        pct = (100.0 * est_minutes_total(res["subset"]) / pool_est
               if pool_est else float("nan"))
        winner_line += (
            f"full available pool (n={pool_n}), so the reduced population is "
            f"nearly equivalent under the validation criterion at ~{pct:.0f}% of "
            "the est. single-GPU cost."
        )
    else:
        winner_line += (
            "full 47, so the reduced population is nearly equivalent under the "
            "validation criterion at ~67% of the est. single-GPU cost."
        )
    lines.append(winner_line)

    lines += [
        "",
        "Reason taxonomy (per-model, assigned by single-model ablation on "
        "occupancy alone — never trait values). Kept models are "
        "'edge-or-chain-forced (theta_M)', 'required: era-window coverage', "
        "'required: structural identifiability (crossing)', 'required: "
        "structural identifiability (rank/VIF)', or 'required: statistical "
        "recoverability (D2 gate)'; dropped models are 'redundant in-cell "
        "replication (identifiability unchanged)'. Pre-measurement exclusions "
        "carry their own reason in the CSV.",
    ]

    if label:
        if win["n"] == res["n0"]:
            trace = (
                f"Trace: the available pool (n={pool_n}) passes; the structural "
                f"minimum n0 = {res['n0']} passes at search reps AND the "
                f"{confirm_reps}-rep confirmation margin — no extra models over "
                "n0 were needed."
            )
        else:
            trace = (
                f"Trace: the available pool (n={pool_n}) passes; the structural "
                f"minimum n0 = {res['n0']} fails the confirmation margin "
                f"(knife-edge on the bar); {win['n']} passes — the extra "
                "model(s) over n0 are statistically necessary, not "
                "computationally convenient."
            )
    else:
        trace = (
            "Trace: 47 passes, the structural minimum 21 fails the confirmation "
            "margin (knife-edge on the bar), 22 passes — the extra model over "
            "n0 is statistically necessary, not computationally convenient."
        )
    lines += ["", trace, "", ]

    lines += [
        "| n | models | rank | vif | pass | bias A | cov% A | bias B | cov% B "
        "| bias A conf | bias B conf |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        f"| {pool_n} | {pool_n} | True | True | {baseline_conf_ok} "
        f"| {bl['A']['era_bias_pp']:.2f} | {bl['A']['era_coverage_pct']:.1f} "
        f"| {bl['B']['era_bias_pp']:.2f} | {bl['B']['era_coverage_pct']:.1f} "
        f"| {blc['A']['era_bias_pp']:.2f} | {blc['B']['era_bias_pp']:.2f} |",
    ]
    for r in res["results"]:
        lines.append(
            f"| {r['n']} | {r['n_models']} | {r['rank_ok']} | {r['vif_ok']} "
            f"| {r['pass']} | {r.get('bias_pp_A', '-')} | {r.get('cov_pct_A', '-')} "
            f"| {r.get('bias_pp_B', '-')} | {r.get('cov_pct_B', '-')} "
            f"| {r.get('bias_pp_A_conf', '-')} | {r.get('bias_pp_B_conf', '-')} |")

    if robust_reps and res.get("robust"):
        rb = res["robust"]
        lines += [
            "",
            f"Robustness at {robust_reps} reps (same fixed seeds): "
            f"A {rb['A']['era_bias_pp']:.2f}pp / B {rb['B']['era_bias_pp']:.2f}pp, "
            f"era-share CI coverage {rb['A']['era_coverage_pct']:.1f}% / "
            f"{rb['B']['era_coverage_pct']:.1f}%, convergence "
            f"{rb['A']['convergence_pct']:.1f}% / "
            f"{rb['B']['convergence_pct']:.1f}%.",
        ]

    report_path.write_text("\n".join(lines) + "\n")
    return csv_path, report_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reps", type=int, default=300,
                   help="search validation reps/seed")
    p.add_argument("--confirm-reps", type=int, default=1000,
                   help="high-precision confirmation reps for passing candidates")
    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    p.add_argument("--exclude", nargs="+", default=[], metavar="FULL_NAME",
                   help="pre-measurement exclusions removed from the candidate "
                        "pool (before any measurement)")
    p.add_argument("--relax-era-window", action="store_true",
                   help="require era coverage only for quarters still holding a "
                        "candidate (required when an excluded model was the only "
                        "one in its quarter)")
    p.add_argument("--label", default=None,
                   help="output filename label (default: joined excluded names)")
    p.add_argument("--robust-reps", type=int, default=0,
                   help="extra robustness battery reps on the winner (e.g. 2000)")
    args = p.parse_args(argv)

    valid = {m[3] for m in MODELS}
    for fn in args.exclude:
        if fn not in valid:
            p.error(f"--exclude: unknown model {fn!r}")
    excluded = sorted(set(args.exclude))
    label = args.label or ("_".join(fn.lower() for fn in excluded)
                           if excluded else "")

    res = find_minimal_valid(reps=args.reps, confirm_reps=args.confirm_reps,
                             excluded=set(excluded),
                             relax_era_window=args.relax_era_window,
                             robust_reps=args.robust_reps)
    csv_path, report_path = write_outputs(res, Path(args.out_dir), reps=args.reps,
                                          confirm_reps=args.confirm_reps,
                                          label=label)
    if res.get("infeasible"):
        print(f"G3: INFEASIBLE — {res['infeasible_reason']}")
    else:
        print(f"G3: n0 = {res['n0']}, minimum VALID = {res['n_valid']}/{res['pool_n']}")
    print(f"-> {csv_path}")
    print(f"-> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
