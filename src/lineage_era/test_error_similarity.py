"""Validate the error-similarity panel + pre-registered primary-measure rule.

Fixtures (synthetic, validation only -- never a research result):

- balanced_signal:   family-clustered shared errors (trap items) at similar
                     model accuracies.
- imbalanced_signal: same family signal but model accuracies spread 0.55-0.95,
                     to test robustness of each measure to unequal error rates.
- no_overlap:        item difficulty + accuracy only, no family structure; the
                     calibration fixture.

Pre-registered criteria (Research_Decision_Log 2026-08-03): C1 calibration
(|within-family z| <= 2 vs the item-difficulty null on the no-overlap fixture),
C2 robustness (signal z >= 3 on the imbalanced fixture with sign agreeing with
the balanced fixture), C3 bootstrap stability (median CV <= 0.5), C4
interpretable. Tie-break: largest within-family z on the balanced fixture.

Run from the repository root:
    python src/lineage_era/test_error_similarity.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lineage_era.analysis import error_similarity as es  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _invlogit(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def make_fixture(seed: int, n_fam: int = 4, per: int = 3, n_items: int = 600,
                 trap: float = 0.30, imbalanced: bool = False,
                 shared: bool = True, n_eras: int = 6,
                 fam_clustered_acc: bool = False
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    fams = [f"F{i + 1}" for i in range(n_fam)]
    eras = [f"Q{q}" for q in range(n_eras)]
    models = [(fam, f"{fam}{k}") for fam in fams for k in range(per)]
    if not imbalanced:
        acc = np.clip(rng.normal(0.80, 0.04, len(models)), 0.6, 0.95)
    elif fam_clustered_acc:
        fam_base = rng.uniform(0.55, 0.95, n_fam)
        acc = np.concatenate([
            np.clip(np.full(per, fam_base[f]) + rng.normal(0.0, 0.02, per),
                    0.5, 0.98) for f in range(n_fam)])
    else:
        acc = rng.uniform(0.55, 0.95, len(models))
    diff = rng.normal(0.0, 1.0, n_items)
    trap_fam = np.where(rng.random(n_items) < trap,
                        rng.integers(0, n_fam, n_items), -1) if shared \
        else -np.ones(n_items, dtype=int)

    rows = []
    design = []
    for idx, (fam, name) in enumerate(models):
        intercept = np.log(acc[idx] / (1 - acc[idx]))
        for i in range(n_items):
            trap_penalty = 2.5 if trap_fam[i] == int(fam[1]) - 1 else 0.0
            p = _invlogit(diff[i] + intercept - trap_penalty)
            correct = int(rng.random() < p)
            rows.append({"full_name": name, "question": f"q{i}",
                         "subject": "mix", "correct": correct})
        design.append({"full_name": name, "family": fam, "era": eras[idx % n_eras]})
    return pd.DataFrame(rows), pd.DataFrame(design)


def _context(samples: pd.DataFrame, design: pd.DataFrame, seed: int,
             bootstrap_reps: int = 60, null_reps: int = 60) -> dict:
    B, models, items = es.error_matrix(samples, design)
    ctxt = {
        "B": B, "models": models, "design": design, "items": items,
        "matrices": es._measure_matrices(B),
        "null_mc_stats": es.null_mc(B, null_reps, seed, strata=False),
        "null_strata_stats": es.null_mc(B, null_reps, seed + 1, strata=True),
    }
    _, _, _, stability = es.question_bootstrap(B, bootstrap_reps, seed + 2,
                                               models, design)
    ctxt["stability"] = stability
    return ctxt


def _within_z_vs_strata(ctxt: dict, measure: str) -> float:
    mat = ctxt["matrices"][measure]
    null_mean, null_sd = ctxt["null_strata_stats"][measure]
    fam = ctxt["design"].set_index("full_name")["family"].reindex(ctxt["models"])
    fv = fam.to_numpy()
    i, j = np.triu_indices(len(fv), k=1)
    known = pd.notna(fv)
    wf = np.flatnonzero(known[i] & known[j] & (fv[i] == fv[j]))
    wi, wj = i[wf], j[wf]
    return float((mat[wi, wj].mean() - null_mean[wi, wj].mean())
                 / max(null_sd[wi, wj].mean(), 1e-9))


def main() -> None:
    ctx = {
        "balanced_signal": _context(*make_fixture(1), 101),
        "imbalanced_signal": _context(*make_fixture(2, imbalanced=True), 201),
        "no_overlap": _context(*make_fixture(3, shared=False), 301),
        "imbalanced_no_overlap": _context(
            *make_fixture(4, shared=False, imbalanced=True, fam_clustered_acc=True), 401),
    }
    selection = es.evaluate_criteria(ctx)
    out_dir = REPO_ROOT / "src/results/phase2"
    out_dir.mkdir(parents=True, exist_ok=True)
    selection.to_csv(out_dir / "metric_selection.csv", index=False)
    print(selection.to_string(index=False))

    chosen = selection.loc[selection["selected"], "measure"].iloc[0]
    print(f"\nselected primary measure (pre-registered rule): {chosen}")
    assert chosen in {"phi", "yule_q", "cohen_kappa"}, \
        "selection must prefer a chance-corrected measure"

    # signal detected on the signal fixture vs the matched-accuracy null
    for label in ("balanced_signal", "imbalanced_signal"):
        c = ctx[label]
        idx = np.triu_indices(len(c["models"]), k=1)
        obs = c["matrices"]["phi"][idx].mean()
        null = c["null_mc_stats"]["phi"][0][idx].mean()
        assert obs > null, f"family signal not detected ({label})"
    assert abs(_within_z_vs_strata(ctx["no_overlap"], "phi")) <= 3.0, \
        "calibration fixture far off the item-difficulty null"

    # end-to-end panel run on the balanced signal fixture
    samples, design = make_fixture(5)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        samp_dir = tmp_path / "eval_samples"
        samp_dir.mkdir(parents=True)
        (samp_dir / "fixture.jsonl").write_text(
            "\n".join(samples.to_json(orient="records", lines=True).splitlines()))
        es.run_panel(samp_dir, None, tmp_path, seed=42, bootstrap_reps=60,
                     null_reps=60, make_figures=True, design=design)
        for name in ("error_similarity.csv", "similarity_matrix.csv",
                     "null_ladder.csv", "family_era_overlap.csv",
                     "edge_stability.csv", "community_comparison.csv"):
            p = tmp_path / name
            assert p.exists(), f"missing {name}"
        stab = pd.read_csv(tmp_path / "edge_stability.csv")
        assert stab["stability"].between(0.0, 1.0).all()
        assert (tmp_path / "error_heatmap.pdf").exists()
        assert (tmp_path / "error_network.pdf").exists()
        assert (tmp_path / "error_dendrogram.pdf").exists()
        assert (tmp_path / "error_embedding_pca.pdf").exists()
        assert (tmp_path / "error_embedding_tsne.pdf").exists()

    print("ERROR-SIMILARITY VALIDATION OK")


if __name__ == "__main__":
    main()
