"""Data generating processes for the Phase 1 simulation battery.

Designs
-------
D1 : balanced crossed  (30 families x 14 eras x 2 models per cell)
D2 : realistic occupancy, copied from the Phase 0 table (unbalanced/sparse)
D3 : nested (family confined to a single era) — must fail detectably
liability : D2 occupancy, item-level binary responses via a probit liability
lxe : D2 occupancy, continuous trait with an added family x era cell effect

Variance scenarios (shares sum to 1 on the model-level trait):
A lineage-dominant (0.50 / 0.20 / 0.30), B era-dominant (0.20 / 0.50 / 0.30),
C balanced (0.33 / 0.33 / 0.34)  [L / E / U].
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import occupancy

SCENARIOS = {
    "A": {"L": 0.50, "E": 0.20, "U": 0.30},  # lineage-dominant
    "B": {"L": 0.20, "E": 0.50, "U": 0.30},  # era-dominant
    "C": {"L": 0.33, "E": 0.33, "U": 0.34},  # balanced
}
SCENARIO_LABELS = {"A": "lineage-dominant", "B": "era-dominant", "C": "balanced"}


def _design_from_counts(counts: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Expand a family x quarter count matrix into one row per model."""
    rows = []
    model_id = 0
    for fam, q in counts.stack().index:
        n = int(counts.loc[fam, q])
        for _ in range(n):
            rows.append({"model": model_id, "family": fam, "era": q})
            model_id += 1
    return pd.DataFrame(rows)


def design_d1(rng: np.random.Generator, n_families: int = 30,
              n_eras: int = 14, per_cell: int = 2) -> pd.DataFrame:
    """Balanced crossed design: n_families x n_eras x per_cell models.

    n_families defaults to 30 so D1 validates the estimator independently of
    the small-family-count (df = 5) coverage limit of the real design; D2
    retains the realistic 6-family occupancy where that limit is quantified.
    """
    rows = []
    model_id = 0
    for f in range(n_families):
        for e in range(n_eras):
            for _ in range(per_cell):
                rows.append({"model": model_id, "family": f, "era": e})
                model_id += 1
    return pd.DataFrame(rows)


def design_d2(rng: np.random.Generator) -> pd.DataFrame:
    """Realistic occupancy: cell counts copied from the Phase 0 table.

    Model ids are shuffled so that within-cell ordering carries no meaning
    (reps differ by realized effects, not by the id labeling).
    """
    counts = occupancy.design_counts()
    return _design_from_counts(counts, rng)


def design_d3(rng: np.random.Generator, n_families: int = 6,
              per_cell: int = 3) -> pd.DataFrame:
    """Nested design: family f appears only in era f (family ~ era, collinear)."""
    rows = []
    model_id = 0
    for f in range(n_families):
        for _ in range(per_cell):
            rows.append({"model": model_id, "family": f, "era": f})
            model_id += 1
    return pd.DataFrame(rows)


def _effects(design: pd.DataFrame, scenario: dict, rng: np.random.Generator
             ) -> tuple[dict, dict, np.ndarray]:
    s2_L, s2_E, s2_U = scenario["L"], scenario["E"], scenario["U"]
    families = sorted(design["family"].unique())
    eras = sorted(design["era"].unique())
    alpha = {f: rng.normal(0.0, np.sqrt(s2_L)) for f in families}
    beta = {e: rng.normal(0.0, np.sqrt(s2_E)) for e in eras}
    u = rng.normal(0.0, np.sqrt(s2_U), len(design))
    return alpha, beta, u


def simulate_trait(design: pd.DataFrame, scenario: dict,
                   rng: np.random.Generator) -> pd.DataFrame:
    """Continuous model-level trait: trait_m = alpha_fam + beta_era + u_model.

    Variance components are exactly the scenario shares (total model-level
    trait variance = 1).
    """
    alpha, beta, u = _effects(design, scenario, rng)
    out = design.copy()
    out["trait"] = [
        alpha[f] + beta[e] + u_i
        for f, e, u_i in zip(out["family"], out["era"], u)
    ]
    return out


def simulate_trait_lxe(design: pd.DataFrame, scenario: dict,
                       s2_LE: float, rng: np.random.Generator) -> pd.DataFrame:
    """Trait with a family x era cell effect added (the L x E test).

    trait_m = alpha_fam + beta_era + gamma_{fam,era} + u_model, with
    gamma ~ N(0, s2_LE) per occupied cell. Total variance is rescaled so the
    generating shares (scenario + interaction) still sum to 1.
    """
    alpha, beta, u = _effects(design, scenario, rng)
    base = scenario["L"] + scenario["E"] + scenario["U"]
    scale = base + s2_LE
    cell = {}
    out = design.copy()
    out["cell"] = list(zip(out["family"], out["era"]))
    for c in sorted(set(out["cell"])):
        cell[c] = rng.normal(0.0, np.sqrt(s2_LE))
    out["trait"] = [
        (alpha[f] + beta[e] + cell[(f, e)] + u_i) / np.sqrt(scale)
        for f, e, u_i in zip(out["family"], out["era"], u)
    ]
    return out


def simulate_liability(design: pd.DataFrame, scenario: dict,
                       n_items: int, rng: np.random.Generator) -> pd.DataFrame:
    """Item-level binary responses via a probit liability model.

    y*_mi = delta_i + alpha_fam + beta_era + u_model + r_mi,  r ~ N(0, 1),
    y = 1{y* > 0}. delta_i ~ N(0, 1) are item difficulties shared by all
    models (they drop out of the model-level variance partition). The
    family/era/model effects are drawn on the liability scale with the
    scenario variances.
    """
    alpha, beta, u = _effects(design, scenario, rng)
    delta = rng.normal(0.0, 1.0, n_items)
    rows = []
    for model, f, e, u_i in zip(design["model"], design["family"],
                                design["era"], u):
        z = alpha[f] + beta[e] + u_i + delta + rng.normal(0.0, 1.0, n_items)
        for item in range(n_items):
            rows.append({
                "model": model, "family": f, "era": e,
                "item": item, "y": int(z[item] > 0.0),
            })
    return pd.DataFrame(rows)


def design_for(regime: str, rng: np.random.Generator) -> pd.DataFrame:
    """Return the design matrix for a regime."""
    if regime == "d1":
        return design_d1(rng)
    if regime == "d2":
        return design_d2(rng)
    if regime == "d3":
        return design_d3(rng)
    if regime in ("liability", "lxe"):
        return design_d2(rng)
    raise ValueError(f"unknown regime: {regime}")
