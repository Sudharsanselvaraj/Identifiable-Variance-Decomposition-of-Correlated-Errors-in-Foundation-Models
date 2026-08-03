"""error_similarity — secondary panel: pairwise error-similarity of the fresh eval.

The variance decomposition stays the primary result; this panel is the
supporting observational layer that motivates it (Observed overlap -> Why? ->
Identifiability -> Decomposition). It quantifies how much two models' error
sets overlap on the common MMLU item set and situates that overlap against a
four-tier null ladder.

Design decisions (research log 2026-08-03):

- Multiple measures are computed (Jaccard, overlap coefficient, cosine, phi =
  MCC, Yule's Q, Cohen's kappa). The primary measure is chosen by the
  pre-registered criteria in ``evaluate_criteria`` (calibration under the
  matched-accuracy null, robustness to unequal error rates, bootstrap
  stability, interpretability) applied to synthetic fixtures in
  ``test_error_similarity.py`` -- never by inspecting real results. The locked
  primary is ``PRIMARY_MEASURE`` below.
- Null ladder: observed -> matched-accuracy shuffle -> item-difficulty shuffle
  -> analytic independence. The matched-accuracy null (per-model error sets
  placed uniformly at random over the item set, preserving each model's
  accuracy) is the primary inferential null: "do models share significantly
  more errors than expected given identical accuracy?" The item-difficulty
  null additionally preserves each model's error count within item-difficulty
  strata (most conservative tier, expected closest to observed).
- Uncertainty: question-level block bootstrap (resample items) -> 95%
  percentile CIs on every summary, plus edge stability (fraction of bootstrap
  replicates in which each network edge appears).
- Structure: distance = 1 - primary similarity, average-linkage clustering
  (dendrogram), Louvain community detection compared against family / era
  labels (descriptive), top-k-per-node network (k=3, edges below a minimum
  similarity floor dropped), PCA + t-SNE embedding.

Outputs (under results/phase2/):
- error_similarity.csv   pairwise measures + bootstrap CIs for the primary
- similarity_matrix.csv  primary measure as a models x models matrix
- null_ladder.csv        observed vs the three null tiers per summary group
- family_era_overlap.csv within/between family & era means with CIs
- edge_stability.csv     network edges with bootstrap stability
- community_comparison.csv  Louvain vs family/era (adjusted Rand index)
- metric_selection.csv   pre-registered criterion values per measure
- figures: error_heatmap, error_dendrogram, error_network, error_embedding

Usage (from src/):
    python3 -m lineage_era.phase2_error_similarity \
        --trait-csv results/phase2/trait_table.csv --out-dir results/phase2
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..occupancy import model_table

# Locked by the pre-registered selection rule on synthetic fixtures
# (test_error_similarity.py; Research_Decision_Log 2026-08-03).
PRIMARY_MEASURE = "phi"

MEASURES = ["jaccard", "overlap", "cosine", "phi", "yule_q", "cohen_kappa"]
GROUPS = ["within_family", "between_family", "within_era", "across_era"]


# ------------------------------------------------------------------ inputs --
def load_samples(samples_dir: Path) -> pd.DataFrame:
    from .trait import load_question_samples

    samples = load_question_samples(samples_dir)
    if samples.empty:
        raise FileNotFoundError(
            f"no per-question samples under {samples_dir}; the panel needs "
            "item-level `correct` flags (drop --no-samples on the eval run)."
        )
    return samples


def error_matrix(samples: pd.DataFrame, table: pd.DataFrame | None = None
                 ) -> tuple[np.ndarray, list[str], list[str]]:
    """Common-item-set binary error matrix (models x items).

    error = 1 - correct; item = question text. Items not answered by every
    model are dropped (common item set, register A15). Returns (B, models,
    items) where B.dtype is int8.
    """
    if table is not None:
        keep = set(table["full_name"])
        samples = samples[samples["full_name"].isin(keep)]
    d = samples.dropna(subset=["correct"]).copy()
    d["error"] = (1 - d["correct"].astype(int)).astype(np.int8)
    if "question" not in d.columns:
        raise ValueError("samples missing 'question' column")
    piv = d.pivot_table(index="full_name", columns="question",
                        values="error", aggfunc="mean")
    piv = piv.dropna(axis=1)
    piv = piv.loc[:, piv.sum(axis=0) > 0]
    if piv.shape[1] < 100:
        print(f"WARNING: common item set only {piv.shape[1]} questions",
              file=__import__("sys").stderr)
    models = list(piv.index)
    items = list(piv.columns)
    return piv.to_numpy(dtype=np.int8), models, items


def design_map(trait_csv: Path | None) -> pd.DataFrame:
    """full_name -> family/era from the trait table (or the occupancy table)."""
    if trait_csv is not None and Path(trait_csv).exists():
        t = pd.read_csv(trait_csv)
        if {"full_name", "family", "era"}.issubset(t.columns):
            return t[["full_name", "family", "era"]]
    tab = model_table().rename(columns={"quarter": "era"})
    return tab[["full_name", "family", "era"]]


# -------------------------------------------------------------- measures ---
def _measure_matrices(B: np.ndarray) -> dict[str, np.ndarray]:
    """All pairwise similarity measures from a binary error matrix B.

    All pairs use the 2x2 confusion table for error=1:
        n11=S, n10, n01, n00  with n = #items, r_i = #errors of model i.
    """
    n = B.shape[1]
    S = B.astype(np.float64) @ B.T.astype(np.float64)      # n11, models x models
    r = B.sum(axis=1).astype(np.float64)                   # n1_
    ri = r[:, None]
    rj = r[None, :]
    n10 = ri - S
    n01 = rj - S
    n00 = n - ri - rj + S
    out = {}

    jac = S / np.maximum(ri + rj - S, np.finfo(float).eps)
    np.fill_diagonal(jac, 1.0)
    out["jaccard"] = jac

    ov = S / np.maximum(np.minimum(ri, rj), np.finfo(float).eps)
    np.fill_diagonal(ov, 1.0)
    out["overlap"] = ov

    cos = S / np.maximum(np.sqrt(ri * rj), np.finfo(float).eps)
    np.fill_diagonal(cos, 1.0)
    out["cosine"] = cos

    num = S * n00 - n10 * n01
    den_phi = np.sqrt(np.maximum(ri * rj * (n - ri) * (n - rj), 0.0))
    phi = np.where(den_phi > 0, num / np.maximum(den_phi, np.finfo(float).eps), 0.0)
    np.fill_diagonal(phi, 1.0)
    out["phi"] = phi

    den_y = S * n00 + n10 * n01
    yq = np.where(den_y > 0, num / np.maximum(den_y, np.finfo(float).eps), 0.0)
    np.fill_diagonal(yq, 1.0)
    out["yule_q"] = yq

    po = (S + n00) / n
    pe = (ri * rj + (n - ri) * (n - rj)) / (n * n)
    kap = np.where(1 - pe > 0, (po - pe) / np.maximum(1 - pe, np.finfo(float).eps), 0.0)
    np.fill_diagonal(kap, 1.0)
    out["cohen_kappa"] = kap

    return out


# -------------------------------------------------------------- nulls ------
def null_independence(B: np.ndarray) -> dict[str, np.ndarray]:
    """Analytic expectation of each measure under independent errors."""
    n = B.shape[1]
    p = B.sum(axis=1).astype(np.float64) / n
    pi = p[:, None]
    pj = p[None, :]
    eps = np.finfo(float).eps
    zero = np.zeros((len(p), len(p)))
    return {
        "jaccard": pi * pj / np.maximum(pi + pj - pi * pj, eps),
        "overlap": np.maximum(pi, pj),
        "cosine": np.sqrt(pi * pj),
        "phi": zero.copy(),
        "yule_q": zero.copy(),
        "cohen_kappa": zero.copy(),
    }


def _permuted_rows(B: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Each model's error set placed uniformly at random over the items."""
    n = B.shape[1]
    counts = B.sum(axis=1)
    out = np.zeros_like(B)
    for i, k in enumerate(counts):
        if k > 0:
            out[i, rng.choice(n, size=int(k), replace=False)] = 1
    return out


def _permuted_rows_strata(B: np.ndarray, bins: int,
                          rng: np.random.Generator) -> np.ndarray:
    """Model errors permuted within item-difficulty strata (most conservative).

    Items are binned by their error rate across models; within each bin every
    model keeps its observed error count but the specific items are permuted,
    preserving both per-model accuracy and item-difficulty alignment.
    """
    n = B.shape[1]
    item_rate = B.mean(axis=0)
    order = np.argsort(item_rate, kind="stable")
    edges = np.unique(np.round(np.linspace(0, n, bins + 1)).astype(int))
    out = np.zeros_like(B)
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi == lo:
            continue
        cols = order[lo:hi]
        block = B[:, cols]
        k = block.sum(axis=1)
        block = block.copy()
        for i, cnt in enumerate(k):
            if cnt > 0:
                which = rng.choice(len(cols), size=int(cnt), replace=False)
                block[i, :] = 0
                block[i, which] = 1
        out[:, cols] = block
    return out


def null_mc(B: np.ndarray, reps: int, seed: int, strata: bool,
            bins: int = 10) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Monte-Carlo null: per-replicate measure matrices -> (mean, sd)."""
    rng = np.random.default_rng(seed)
    sums = {m: np.zeros((B.shape[0], B.shape[0])) for m in MEASURES}
    sq = {m: np.zeros((B.shape[0], B.shape[0])) for m in MEASURES}
    for _ in range(reps):
        Bn = (_permuted_rows_strata(B, bins, rng) if strata
              else _permuted_rows(B, rng))
        mats = _measure_matrices(Bn)
        for m, mat in mats.items():
            sums[m] += mat
            sq[m] += mat * mat
    out = {}
    for m in MEASURES:
        mean = sums[m] / reps
        var = sq[m] / reps - mean * mean
        out[m] = (mean, np.sqrt(np.maximum(var, 0.0)))
    return out


# ----------------------------------------------------------- summaries -----
def _pair_table(mat: np.ndarray, models: list[str],
                design: pd.DataFrame) -> pd.DataFrame:
    fam = design.set_index("full_name")["family"]
    era = design.set_index("full_name")["era"]
    rows = []
    n = len(models)
    for i in range(n):
        for j in range(i + 1, n):
            fi, fj = fam.get(models[i]), fam.get(models[j])
            ei, ej = era.get(models[i]), era.get(models[j])
            same_fam = int(pd.notna(fi) and pd.notna(fj) and fi == fj)
            same_era = int(pd.notna(ei) and pd.notna(ej) and ei == ej)
            rows.append({
                "i": models[i], "j": models[j],
                "family_i": fi, "family_j": fj,
                "era_i": ei, "era_j": ej,
                "within_family": same_fam,
                "between_family": int(pd.notna(fi) and pd.notna(fj)) - same_fam,
                "within_era": same_era,
                "across_era": int(pd.notna(ei) and pd.notna(ej)) - same_era,
                "value": mat[i, j],
            })
    return pd.DataFrame(rows)


def summary_stats(mat: np.ndarray, models: list[str], design: pd.DataFrame,
                  ) -> dict[str, float]:
    pair = _pair_table(mat, models, design)
    out = {}
    for g in GROUPS:
        out[g] = float(pair.loc[pair[g] == 1, "value"].mean())
    return out


def _z(obs: float, null_mean: float, null_sd: float) -> float:
    return float((obs - null_mean) / null_sd) if null_sd > 0 else float("nan")


def build_null_ladder(obs_mat: np.ndarray, models: list[str],
                      design: pd.DataFrame, null_mc_stats: dict,
                      null_strata_stats: dict, null_ind: dict,
                      measure: str) -> pd.DataFrame:
    obs = summary_stats(obs_mat, models, design)
    mc_mean, mc_sd = null_mc_stats[measure]
    null = summary_stats(mc_mean, models, design)
    null_sd = summary_stats(mc_sd, models, design)
    st_mean, st_sd = null_strata_stats[measure]
    strata = summary_stats(st_mean, models, design)
    strata_sd = summary_stats(st_sd, models, design)
    indep = summary_stats(null_ind[measure], models, design)
    rows = []
    for g in GROUPS:
        rows.append({
            "group": g,
            "observed": obs[g],
            "matched_accuracy_mean": null[g],
            "matched_accuracy_sd": null_sd[g],
            "item_difficulty_mean": strata[g],
            "item_difficulty_sd": strata_sd[g],
            "independence_analytic": indep[g],
            "z_matched_accuracy": _z(obs[g], null[g], null_sd[g]),
            "z_item_difficulty": _z(obs[g], strata[g], strata_sd[g]),
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------ bootstrap -----
def question_bootstrap(B: np.ndarray, reps: int, seed: int,
                       models: list[str], design: pd.DataFrame,
                       top_k: int = 3, min_sim: float = 0.05
                       ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Question-level block bootstrap.

    Returns (pairwise CI frame for PRIMARY_MEASURE, group-mean CI frame,
    edge-stability frame, per-measure summary-stability dict). Edge stability =
    share of replicates in which the top-k edge (above the floor) is present.
    Summary stability = share of replicates in which within-family mean overlap
    exceeds between-family mean (sign consistency of the lineage summary).
    """
    rng = np.random.default_rng(seed)
    n_items = B.shape[1]
    n = B.shape[0]
    stab: dict[tuple[int, int], int] = {}
    sign_ok = {m: 0 for m in MEASURES}
    rep_means = {g: [] for g in GROUPS}
    rep_primary = []
    for _ in range(reps):
        cols = rng.integers(0, n_items, size=n_items)
        Bb = B[:, cols]
        mats = _measure_matrices(Bb)
        for m in MEASURES:
            s = summary_stats(mats[m], models, design)
            if s["within_family"] > s["between_family"]:
                sign_ok[m] += 1
        for g, v in summary_stats(mats[PRIMARY_MEASURE], models, design).items():
            rep_means[g].append(v)
        rep_primary.append(mats[PRIMARY_MEASURE])
        edges = topk_edges(mats[PRIMARY_MEASURE], top_k, min_sim)
        for (i, j, _w) in edges:
            key = (i, j) if i < j else (j, i)
            stab[key] = stab.get(key, 0) + 1

    # group CIs
    group_rows = []
    for g in GROUPS:
        a = np.asarray(rep_means[g])
        group_rows.append({
            "group": g,
            "mean": float(np.mean(a)),
            "ci_lo": float(np.percentile(a, 2.5)),
            "ci_hi": float(np.percentile(a, 97.5)),
        })
    group_ci = pd.DataFrame(group_rows)

    # pairwise CIs for the primary measure
    arr = np.stack(rep_primary)
    lo = np.percentile(arr, 2.5, axis=0)
    hi = np.percentile(arr, 97.5, axis=0)
    pair = _pair_table(arr.mean(axis=0), models, design)
    pair["ci_lo"] = pair.apply(lambda r: lo[np.searchsorted(models, r["i"]),
                                            np.searchsorted(models, r["j"])], axis=1)
    pair["ci_hi"] = pair.apply(lambda r: hi[np.searchsorted(models, r["i"]),
                                            np.searchsorted(models, r["j"])], axis=1)

    # edge stability
    stab_rows = []
    obs = _measure_matrices(B)[PRIMARY_MEASURE]
    for (i, j), cnt in stab.items():
        stab_rows.append({
            "i": models[i], "j": models[j],
            "weight": float(obs[i, j]),
            "stability": cnt / reps,
        })
    stability = pd.DataFrame(stab_rows).sort_values("stability", ascending=False)

    summary_stability = {m: cnt / reps for m, cnt in sign_ok.items()}
    return pair, group_ci, stability, summary_stability


# ------------------------------------------------------------- network ------
def topk_edges(mat: np.ndarray, top_k: int = 3, min_sim: float = 0.05
               ) -> list[tuple[int, int, float]]:
    """Top-k strongest (non-self) edges per node, dropping edges < min_sim."""
    n = mat.shape[0]
    seen: set[tuple[int, int]] = set()
    edges = []
    for i in range(n):
        order = np.argsort(mat[i])[::-1]
        for j in order:
            if j == i or (i, j) in seen or (j, i) in seen:
                continue
            if mat[i, j] < min_sim:
                continue
            edges.append((i, int(j), float(mat[i, j])))
            seen.add((i, int(j)))
            if sum(1 for (a, b, _) in edges if a == i or b == i) >= top_k:
                break
    return edges


def communities(B: np.ndarray, models: list[str], design: pd.DataFrame,
                seed: int, top_k: int = 3, min_sim: float = 0.05
                ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Louvain communities on the top-k network vs family/era labels.

    Returns (edge table, community_comparison table). Descriptive only.
    """
    import networkx as nx
    from sklearn.metrics import adjusted_rand_score

    mat = _measure_matrices(B)[PRIMARY_MEASURE]
    fam = design.set_index("full_name")["family"]
    era = design.set_index("full_name")["era"]

    G = nx.Graph()
    for i, m in enumerate(models):
        G.add_node(m, family=fam.get(m), era=era.get(m))
    for (i, j, w) in topk_edges(mat, top_k, min_sim):
        G.add_edge(models[i], models[j], weight=w)

    parts = nx.community.louvain_communities(G, weight="weight", seed=seed,
                                             resolution=1.0)
    labels = {}
    for c, nodes in enumerate(parts):
        for node in nodes:
            labels[node] = c
    comm = [labels[m] for m in models]
    ari_fam = adjusted_rand_score([fam.get(m) for m in models], comm)
    ari_era = adjusted_rand_score([era.get(m) for m in models], comm)
    comparison = pd.DataFrame([{
        "algorithm": "louvain",
        "n_communities": len(parts),
        "n_edges": G.number_of_edges(),
        "ari_vs_family": float(ari_fam),
        "ari_vs_era": float(ari_era),
        "interpretation": (
            "family-aligned" if ari_fam >= ari_era else "era-aligned"),
    }])

    edges = pd.DataFrame([
        {"i": models[i], "j": models[j], "weight": w}
        for (i, j, w) in topk_edges(mat, top_k, min_sim)
    ])
    return edges, comparison


# ------------------------------------------------- metric selection ---------
def evaluate_criteria(contexts: dict[str, dict]) -> pd.DataFrame:
    """Pre-registered primary-measure selection criteria (validation time).

    Criteria fixed before results were inspected (Research_Decision_Log
    2026-08-03). ``contexts`` maps a fixture name to a dict with keys
    ``matrices`` (all pairwise measure matrices), ``B`` (error matrix),
    ``models``, ``design``, ``null_mc_stats`` (matched-accuracy null),
    ``null_strata_stats`` (item-difficulty null), ``stability``:

      C1 calibration     balanced no-overlap fixture: |within-family z| <= 2 vs
                        the conservative item-difficulty null (nominal type-I)
      C1b accuracy-robust imbalanced no-overlap fixture (within-family
                        accuracies clustered): |within-family z| <= 2 vs the
                        matched-accuracy null
      C2 robustness      within-family z >= 3 on the imbalanced signal fixture
                        (vs matched-accuracy null) with sign agreeing with the
                        balanced signal fixture
      C3 stability       sign-consistent (within > between) in >= 90% of
                        bootstrap replicates
      C4 interpretable   binary-agreement measures; chance-corrected measures
                        (phi, Yule's Q, kappa) are preferred for cross-pair
                        interpretation because raw overlap measures (Jaccard,
                        overlap, cosine) scale with per-model error rates

    Tie-break (only if >=2 measures pass): among chance-corrected passers, the
    largest within-family z on the balanced signal fixture; fall back to the
    largest within-family z overall. The selected measure is locked as
    PRIMARY_MEASURE.
    """
    z_max, sig_thr = 2.0, 0.9
    CHANCE_CORRECTED = {"phi", "yule_q", "cohen_kappa"}

    def _within_family_pos(ctxt: dict) -> tuple[np.ndarray, np.ndarray]:
        fam = ctxt["design"].set_index("full_name")["family"].reindex(ctxt["models"])
        fv = fam.to_numpy()
        i, j = np.triu_indices(len(fv), k=1)
        known = pd.notna(fv)
        wf = np.flatnonzero(known[i] & known[j] & (fv[i] == fv[j]))
        return i[wf], j[wf]

    def _within_z(ctxt: dict, measure: str, null_key: str) -> tuple[float, float]:
        mat = ctxt["matrices"][measure]
        null_mean, null_sd = ctxt[null_key][measure]
        wi, wj = _within_family_pos(ctxt)
        z = (mat[wi, wj].mean() - null_mean[wi, wj].mean()) \
            / max(null_sd[wi, wj].mean(), 1e-9)
        return float(z), float(mat[wi, wj].mean() - null_mean[wi, wj].mean())

    balanced = contexts.get("balanced_signal")
    imbalanced = contexts.get("imbalanced_signal")
    no_overlap = contexts.get("no_overlap")
    imbal_no_overlap = contexts.get("imbalanced_no_overlap")
    rows = []
    for m in MEASURES:
        # headline signal vs the matched-accuracy null (beyond identical accuracy)
        z_bal, sep_bal = _within_z(balanced, m, "null_mc_stats") if balanced else (np.nan, np.nan)
        z_imb, sep_imb = _within_z(imbalanced, m, "null_mc_stats") if imbalanced else (np.nan, np.nan)
        # calibration vs the conservative item-difficulty null
        z_no, _ = _within_z(no_overlap, m, "null_strata_stats") if no_overlap else (np.nan, np.nan)
        # accuracy-robustness: imbalanced no-overlap vs the matched-accuracy null
        z_ino, _ = _within_z(imbal_no_overlap, m, "null_mc_stats") if imbal_no_overlap else (np.nan, np.nan)
        stab = (balanced or no_overlap or {}).get("stability", {}).get(m, float("nan"))
        c1 = bool(abs(z_no) <= z_max) if no_overlap is not None else None
        c1b = bool(abs(z_ino) <= z_max) if imbal_no_overlap is not None else None
        c2 = None
        if imbalanced is not None and balanced is not None:
            c2 = bool(z_imb >= 3.0 and np.sign(sep_imb) == np.sign(sep_bal))
        rows.append({
            "measure": m,
            "C1_calibrated": c1,
            "C1b_accuracy_robust": c1b,
            "C2_robust_imbalanced": c2,
            "C3_stable_sign": bool(stab >= sig_thr),
            "C3_stability": round(float(stab), 3),
            "C4_chance_corrected": m in CHANCE_CORRECTED,
            "within_family_z_balanced": round(z_bal, 3),
            "within_family_z_imbalanced": round(z_imb, 3),
            "calibration_z_no_overlap": round(z_no, 3),
            "accuracy_robust_z": round(z_ino, 3),
        })
    out = pd.DataFrame(rows)
    passing = out[
        out["C1_calibrated"].fillna(True) &
        out["C1b_accuracy_robust"].fillna(True) &
        out["C2_robust_imbalanced"].fillna(True) &
        out["C3_stable_sign"]
    ]
    if not passing.empty:
        pref = passing[passing["C4_chance_corrected"]]
        pool = pref if not pref.empty else passing
        best = pool.loc[pool["within_family_z_balanced"].idxmax(), "measure"]
    else:
        best = None
    out["selected"] = out["measure"] == best
    return out


# -------------------------------------------------------------- orchestrate --
def run_panel(samples_dir: Path, trait_csv: Path | None, out_dir: Path,
              seed: int = 2026, bootstrap_reps: int = 500,
              null_reps: int = 200, top_k: int = 3, min_sim: float = 0.05,
              make_figures: bool = True, strata_bins: int = 10,
              design: pd.DataFrame | None = None
              ) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    samples = load_samples(samples_dir)
    if design is None:
        design = design_map(trait_csv)
    B, models, items = error_matrix(samples, design)
    rng = np.random.default_rng(seed)
    mats = _measure_matrices(B)

    ind = null_independence(B)
    mc = null_mc(B, null_reps, seed, strata=False, bins=strata_bins)
    diff = null_mc(B, null_reps, seed + 1, strata=True, bins=strata_bins)

    pair, group_ci, stability, _sum_stab = question_bootstrap(
        B, bootstrap_reps, seed, models, design, top_k, min_sim)
    ladder = build_null_ladder(mats[PRIMARY_MEASURE], models, design,
                               mc, diff, ind, PRIMARY_MEASURE)
    edges, community = communities(B, models, design, seed, top_k, min_sim)

    # pairwise table: all measures + bootstrap CI for the primary
    pair_out = _pair_table(mats[PRIMARY_MEASURE], models, design)
    for m in MEASURES:
        mat = mats[m]
        pair_out[m] = [mat[np.searchsorted(models, r["i"]),
                           np.searchsorted(models, r["j"])]
                       for r in pair_out[["i", "j"]].to_dict("records")]
    pair_out = pair_out.merge(pair[["i", "j", "ci_lo", "ci_hi"]],
                              on=["i", "j"], how="left")
    pair_out = pair_out.rename(columns={"value": f"{PRIMARY_MEASURE}_primary"})

    # pairwise table with all measures + primary CI
    pair_out = _pair_table(mats[PRIMARY_MEASURE], models, design)
    for m in MEASURES:
        pair_out[m] = pair_out.apply(
            lambda r: mats[m][np.searchsorted(models, r["i"]),
                              np.searchsorted(models, r["j"])], axis=1)
    pair_out = pair_out.merge(
        pair[["i", "j", "ci_lo", "ci_hi"]], on=["i", "j"], how="left")
    pair_out = pair_out.rename(columns={"value": f"{PRIMARY_MEASURE}_primary"})

    matrix = pd.DataFrame(mats[PRIMARY_MEASURE], index=models, columns=models)
    matrix.to_csv(out_dir / "similarity_matrix.csv")
    pair_out.to_csv(out_dir / "error_similarity.csv", index=False)
    ladder.to_csv(out_dir / "null_ladder.csv", index=False)
    group_ci.to_csv(out_dir / "family_era_overlap.csv", index=False)
    stability.to_csv(out_dir / "edge_stability.csv", index=False)
    edges.to_csv(out_dir / "error_network_edges.csv", index=False)
    community.to_csv(out_dir / "community_comparison.csv", index=False)

    if make_figures:
        from .plots import error_embedding, error_heatmap, error_network, \
            error_dendrogram
        order = _cluster_order(mats[PRIMARY_MEASURE])
        fam_series = design.set_index("full_name")["family"].reindex(models)
        era_series = design.set_index("full_name")["era"].reindex(models)
        error_heatmap(mats[PRIMARY_MEASURE], models, fam_series, order, out_dir)
        error_dendrogram(mats[PRIMARY_MEASURE], models, fam_series, out_dir)
        error_network(edges, models, fam_series, era_series, out_dir, seed)
        error_embedding(mats[PRIMARY_MEASURE], models, fam_series, era_series,
                        out_dir, seed)

    print(f"error-similarity panel: {len(models)} models, {len(items)} items")
    wf = ladder.set_index("group").loc["within_family"]
    print(f"  within-family {PRIMARY_MEASURE}: observed={wf['observed']:.3f} "
          f"matched-accuracy null={wf['matched_accuracy_mean']:.3f} "
          f"z={wf['z_matched_accuracy']:.2f}")
    print(f"  -> {out_dir / 'error_similarity.csv'}")
    return {"pair": pair_out, "ladder": ladder, "group_ci": group_ci,
            "stability": stability, "community": community}


def _cluster_order(mat: np.ndarray) -> list[int]:
    from scipy.cluster.hierarchy import linkage
    dist = 1.0 - mat
    dist = (dist + dist.T) / 2.0
    np.fill_diagonal(dist, 0.0)
    Z = linkage(dist[np.triu_indices(len(mat), k=1)], method="average")
    from scipy.cluster.hierarchy import leaves_list
    return list(leaves_list(Z))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--samples-dir", default="datasets/eval_samples")
    p.add_argument("--trait-csv", default="results/phase2/trait_table.csv")
    p.add_argument("--out-dir", default="results/phase2")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--bootstrap-reps", type=int, default=500)
    p.add_argument("--null-reps", type=int, default=200)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--min-sim", type=float, default=0.05)
    p.add_argument("--no-figures", action="store_true")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    samples_dir = Path(args.samples_dir)
    trait_csv = Path(args.trait_csv)
    run_panel(samples_dir, trait_csv, out_dir, seed=args.seed,
              bootstrap_reps=args.bootstrap_reps, null_reps=args.null_reps,
              top_k=args.top_k, min_sim=args.min_sim,
              make_figures=not args.no_figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
