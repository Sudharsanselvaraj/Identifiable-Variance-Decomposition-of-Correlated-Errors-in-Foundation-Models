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

from .occupancy import FAMILIES, QUARTERS, design_counts

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
