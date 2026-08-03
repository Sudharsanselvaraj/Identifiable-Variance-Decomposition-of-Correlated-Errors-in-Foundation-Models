"""Phase 2 figures (matplotlib PDFs) under results/phase2/figures/.

    design_heatmap.pdf   family x era occupancy counts (design_heatmap)
    family_vs_era.pdf    per-model family vs era BLUPs (alias check visual)
    variance_shares.pdf  θ_P shares with delta CIs
    blup_plot.pdf        family BLUPs over era (per-family trajectories)
    era_trend.pdf        mean trait and era BLUP across quarters
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..occupancy import FAMILIES, QUARTERS, design_counts

PALETTE = plt.get_cmap("tab10")


def design_heatmap(out: Path) -> None:
    counts = design_counts().fillna(0).astype(int)
    counts = counts.reindex(index=FAMILIES, columns=QUARTERS, fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    im = ax.imshow(counts.to_numpy(dtype=int), cmap="YlGnBu", aspect="auto")
    ax.set_yticks(range(len(FAMILIES)), FAMILIES)
    ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=90, fontsize=7)
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            v = counts.iloc[i, j]
            if v:
                ax.text(j, i, int(v), ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, label="models per cell", shrink=0.8)
    ax.set_title("Phase 2 design: occupied family x quarter cells")
    fig.tight_layout()
    fig.savefig(out / "design_heatmap.pdf")
    plt.close(fig)


def family_vs_era(model_effects: pd.DataFrame, out: Path) -> None:
    if model_effects.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for i, fam in enumerate(sorted(model_effects["family"].unique())):
        sub = model_effects[model_effects["family"] == fam]
        ax.scatter(sub["era_blup"], sub["family_blup"], label=fam,
                   color=PALETTE(i % 10), s=22)
    ax.axhline(0, color="grey", lw=0.6)
    ax.axvline(0, color="grey", lw=0.6)
    ax.set_xlabel("era BLUP")
    ax.set_ylabel("family BLUP")
    ax.set_title("Per-model family vs era BLUPs (alias check)")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "family_vs_era.pdf")
    plt.close(fig)


def variance_shares(vp: pd.DataFrame, out: Path) -> None:
    comps = vp["component"]
    share = vp["share"]
    lo = vp["share_lo"] - share
    hi = vp["share_hi"] - share
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(comps, share, yerr=[-lo, hi], capsize=5, color=["#4c72b0", "#dd8452", "#55a868"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("variance share")
    ax.set_title("θ_P variance partition (95% delta CI)")
    fig.tight_layout()
    fig.savefig(out / "variance_shares.pdf")
    plt.close(fig)


def blup_plot(model_effects: pd.DataFrame, out: Path) -> None:
    if model_effects.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, fam in enumerate(sorted(model_effects["family"].unique())):
        sub = model_effects[model_effects["family"] == fam]
        ax.plot(sub["era"], sub["family_blup"], marker="o", ms=4,
                label=fam, color=PALETTE(i % 10))
    ax.set_xlabel("era (quarter)")
    ax.set_ylabel("family BLUP")
    ax.set_title("Family BLUPs over era")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(out / "blup_plot.pdf")
    plt.close(fig)


def era_trend(era_effects: pd.DataFrame, out: Path) -> None:
    if era_effects.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(era_effects["era"], era_effects["mean_trait"], marker="o", ms=5,
            label="mean trait", color="#4c72b0")
    ax.plot(era_effects["era"], era_effects["era_blup"], marker="s", ms=5,
            label="era BLUP", color="#dd8452")
    ax.set_xlabel("era (quarter)")
    ax.set_ylabel("accuracy (trait scale)")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out / "era_trend.pdf")
    plt.close(fig)


# ------------------------------------------------ error-similarity figures --
def _family_colors(fam_series: pd.Series) -> list:
    ordered = sorted(fam_series.dropna().unique())
    code = {f: PALETTE(i % 10) for i, f in enumerate(ordered)}
    return [code.get(f, (0.5, 0.5, 0.5)) for f in fam_series]


def _era_markers(era_series: pd.Series) -> list:
    markers = ["o", "s", "^", "D", "P", "X", "v", "<", ">", "h"]
    ordered = sorted(era_series.dropna().unique())
    code = {e: markers[i % len(markers)] for i, e in enumerate(ordered)}
    return [code.get(e, "o") for e in era_series]


def error_heatmap(mat: np.ndarray, models: list[str], fam_series: pd.Series,
                  order: list[int], out: Path) -> None:
    labels = [models[i] for i in order]
    colors = _family_colors(fam_series.reindex(labels))
    fig, ax = plt.subplots(figsize=(max(6, 0.16 * len(models)) + 1,
                                    max(6, 0.16 * len(models))))
    im = ax.imshow(mat[np.ix_(order, order)], cmap="YlGnBu", vmin=-0.3,
                   vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=6)
    ax.set_yticks(range(len(labels)), labels, fontsize=6)
    for i, c in enumerate(colors):
        ax.get_yticklabels()[i].set_color(c)
    fig.colorbar(im, ax=ax, label="primary error similarity", shrink=0.7)
    ax.set_title("Pairwise error similarity (average-linkage order)")
    fig.tight_layout()
    fig.savefig(out / "error_heatmap.pdf")
    plt.close(fig)


def error_dendrogram(mat: np.ndarray, models: list[str], fam_series: pd.Series,
                     out: Path) -> None:
    from scipy.cluster.hierarchy import dendrogram
    Z = linkage_from_mat(mat)
    fig, ax = plt.subplots(figsize=(max(7, 0.22 * len(models)), 4.5))
    d = dendrogram(Z, labels=models, ax=ax, leaf_font_size=7)
    color = {m: c for m, c in zip(models, _family_colors(fam_series.reindex(models)))}
    for i, leaf in enumerate(d["ivl"]):
        ax.get_xticklabels()[i].set_color(color.get(leaf, (0.5, 0.5, 0.5)))
    ax.set_ylabel("1 - primary error similarity")
    ax.set_title("Average-linkage clustering of models by error similarity")
    fig.tight_layout()
    fig.savefig(out / "error_dendrogram.pdf")
    plt.close(fig)


def linkage_from_mat(mat: np.ndarray):
    from scipy.cluster.hierarchy import linkage
    dist = 1.0 - mat
    dist = (dist + dist.T) / 2.0
    np.fill_diagonal(dist, 0.0)
    return linkage(dist[np.triu_indices(len(mat), k=1)], method="average")


def error_network(edges: pd.DataFrame, models: list[str], fam_series: pd.Series,
                  era_series: pd.Series, out: Path, seed: int = 2026) -> None:
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(models)
    for _, r in edges.iterrows():
        G.add_edge(r["i"], r["j"], weight=r["weight"])
    pos = nx.spring_layout(G, seed=seed, k=0.7, iterations=120)
    node_colors = _family_colors(fam_series.reindex(models))
    node_markers = _era_markers(era_series.reindex(models))
    widths = [0.5 + 3.0 * G[u][v]["weight"] for u, v in G.edges()]

    fig, ax = plt.subplots(figsize=(max(8, 0.32 * len(models)),
                                    max(8, 0.32 * len(models))))
    nx.draw_networkx_edges(G, pos, ax=ax, width=widths, alpha=0.55,
                           edge_color="#888888")
    for i, m in enumerate(models):
        ax.scatter(*pos[m], s=90, color=node_colors[i], marker=node_markers[i],
                   edgecolors="black", linewidths=0.4, zorder=3)
        ax.annotate(m, pos[m], fontsize=5, xytext=(4, 4),
                    textcoords="offset points")
    ax.set_title("Model error-similarity network (top-k edges, "
                 "color=family, marker=era)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out / "error_network.pdf")
    plt.close(fig)


def error_embedding(mat: np.ndarray, models: list[str], fam_series: pd.Series,
                    era_series: pd.Series, out: Path, seed: int = 2026) -> None:
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    node_colors = _family_colors(fam_series.reindex(models))
    node_markers = _era_markers(era_series.reindex(models))

    def scatter(coords, title, fname):
        fig, ax = plt.subplots(figsize=(7.5, 6.5))
        for i, m in enumerate(models):
            ax.scatter(*coords[i], s=80, color=node_colors[i],
                       marker=node_markers[i], edgecolors="black",
                       linewidths=0.4, zorder=3)
            ax.annotate(m, coords[i], fontsize=5, xytext=(4, 4),
                        textcoords="offset points")
        ax.set_title(title)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(out / fname)
        plt.close(fig)

    pca = PCA(n_components=2, random_state=seed).fit_transform(mat)
    scatter(pca, "Model error-similarity: PCA (color=family, marker=era)",
            "error_embedding_pca.pdf")
    tsne = TSNE(n_components=2, random_state=seed, perplexity=min(15, len(models) - 1),
                init="pca").fit_transform(mat)
    scatter(tsne, "Model error-similarity: t-SNE (color=family, marker=era)",
            "error_embedding_tsne.pdf")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    figs = out_dir / "figures"
    figs.mkdir(parents=True, exist_ok=True)

    design_heatmap(figs)

    model_effects = pd.read_csv(out_dir / "model_effects.csv")
    family_vs_era(model_effects, figs)
    blup_plot(model_effects, figs)

    vp = pd.read_csv(out_dir / "variance_partition.csv")
    variance_shares(vp, figs)

    era_effects = pd.read_csv(out_dir / "era_effects.csv")
    era_trend(era_effects, figs)

    written = sorted(figs.glob("*.pdf"))
    print("figures:", ", ".join(p.name for p in written))
    print(f"-> {figs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
