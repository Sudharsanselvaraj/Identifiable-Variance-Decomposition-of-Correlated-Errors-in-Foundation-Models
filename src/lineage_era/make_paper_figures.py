"""GPU-free manuscript figures for docs/07_Paper/figs/.

All six figures are drawn from committed artifacts only (no GPU, no eval
outputs): the verified occupancy table, the lineage graph, the pre-registered
G3 report, and a fresh Phase 1 D3 aliasing-detection battery run on CPU. The
two eval-dependent figure slots (error similarity, theta_P partition) are
deliberately NOT produced here -- they stay placeholders until the real
measurement pass runs (Exp02_GPU_Runbook.md).

Outputs (docs/07_Paper/figs/):
    fig_design.png    F2  occupancy heatmap (real, 47-model connected subset)
    fig_dag.png       F1  causal structure (schematic, two-estimand rule)
    fig_pipeline.png  NEW architecture: three-stage protocol + three gates
    fig_lineage.png   NEW verified-lineage graph on the family x quarter grid
    fig_g3_trace.png  F3  G3 decision trace (regenerated from g3_report.md)
    fig_d3.png        NEW D3 aliasing-detection panel (fresh 300-rep battery)

Usage (from repo root):
    python3 src/lineage_era/make_paper_figures.py
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from lineage_era import phase1_simulation
from lineage_era.occupancy import (
    CAVEATS, FAMILIES, MODELS, QUARTERS, VERIFIED_EDGES, design_counts,
    quarters_with_n_families,
)
from lineage_era.phase2_eval import EVAL_MANIFEST

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGS_DIR = REPO_ROOT / "docs" / "07_Paper" / "figs"
G3_REPORT = REPO_ROOT / "datasets" / "coverage" / "g3_report.md"

DPI = 400

# IEEE Access page geometry, probed from ieeeaccess.cls:
#   \textwidth   = 505.12pt = 6.99in  (two-column span)
#   \columnwidth = 242.67pt = 3.36in  (single column)
# Figures MUST be authored at these widths. The class's \Figure macro picks
# single- vs double-column by measuring the graphic's natural width and
# defaults to [scale=1], so an oversized export silently overflows the text
# block (and is clipped at the trim). See docs/07_Paper/Figures.md.
W_DOUBLE = 6.99
W_SINGLE = 3.36

# Body text is Times; figures must match. Matplotlib's sans-serif default is
# the most common "assembled from defaults" tell in a submitted manuscript.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 6.5,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

# IEEE style: figures carry no internal title. The title text belongs in the
# caption, where it is typeset in the document font and cannot be clipped.
FAM_COLORS = {
    "Llama": "#4e79a7", "Qwen": "#f28e2b", "DeepSeek": "#e15759",
    "Mistral": "#76b7b2", "Phi": "#59a14f", "Gemma": "#edc948",
}
Q_IX = {q: i for i, q in enumerate(QUARTERS)}
FULLNAME_BY_SHORT = {m[2]: m[3] for m in MODELS}

# HF repo name in VERIFIED_EDGES -> manuscript full_name (None = external stub).
EDGE_ENDPOINT = {
    "Llama-3.3-70B-Instruct": "Llama-3.3",
    "Llama-3.1-70B": "Llama-3.1",
    "Phi-4-reasoning-plus": "Phi-4-reasoning-plus",
    "phi-4": "Phi-4",
    "Phi-4-reasoning-vision-15B": "Phi-4-reasoning-vision-15B",
    "Devstral-Small-2": "Devstral-2",
    "Mistral-Small-3.1-Base": "Mistral-Small-3.1",
    "DeepSeek-V3.2": "DeepSeek-V3.2",
    "V3.2-Exp-Base": None,
    "Phi-4-reasoning": None,
}


def _build_model_xy() -> dict[str, tuple[float, int]]:
    """Plot coordinates with co-located models spread inside their cell.

    Six (family, quarter) cells hold two or three models. Plotting them at the
    identical grid point stacks both the markers and their text labels, which
    is what rendered "Small"/"3.1" as "S1all" and "4-12B"/"4-9B" as "4-12B"
    with the 9B lost. Offsetting within the cell keeps every model readable and
    keeps the lineage arrows pointing at the right endpoint.
    """
    cells: dict[tuple[str, str], list[str]] = {}
    for fam, quarter, _short, full in MODELS:
        cells.setdefault((fam, quarter), []).append(full)
    xy: dict[str, tuple[float, int]] = {}
    for (fam, quarter), names in cells.items():
        n = len(names)
        for k, full in enumerate(names):
            # 0.46 grid units ~= 15pt at the published width, which clears the
            # widest co-located label pair ("4"/"4-12B", "L2"/"Small"). Smaller
            # offsets separate the markers but still overprint the text.
            dx = (k - (n - 1) / 2) * (0.46 if n > 1 else 0.0)
            xy[full] = (Q_IX[quarter] + dx, FAMILIES.index(fam))
            MODEL_SLOT[full] = (k, n)
    return xy


MODEL_SLOT: dict[str, tuple[int, int]] = {}
MODEL_XY = _build_model_xy()


def _pos(full_name: str) -> tuple[float, int] | None:
    return MODEL_XY.get(full_name)


# ------------------------------------------------------------ F2 design
def fig_design() -> None:
    counts = design_counts().reindex(index=FAMILIES, columns=QUARTERS, fill_value=0)
    counts = counts.fillna(0).astype(int)
    crossed_q = quarters_with_n_families(2)
    fig, ax = plt.subplots(figsize=(W_SINGLE, 1.85))
    im = ax.imshow(counts.to_numpy(int), cmap="YlGnBu", aspect="auto")
    # Annotate only cells carrying more than one model: 39 of the 47 cells hold
    # a single model, so printing "1" forty times adds ink without information.
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            v = int(counts.iloc[i, j])
            if v > 1:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=5.5,
                        color="#08306b")
    for q in QUARTERS:
        if q in crossed_q:
            ax.add_patch(plt.Rectangle((Q_IX[q] - 0.5, -0.5), 1, counts.shape[0],
                                       fill=False, edgecolor="#d97706",
                                       lw=0.9, ls=(0, (3, 1.5))))
    ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=90, fontsize=5.5)
    ax.set_yticks(range(len(FAMILIES)), FAMILIES, fontsize=6)
    ax.set_xlabel("release quarter", fontsize=7)
    ax.set_ylabel("model family", fontsize=7)
    cb = fig.colorbar(im, ax=ax, shrink=0.95, pad=0.02)
    cb.set_label("models per cell", fontsize=6)
    cb.ax.tick_params(labelsize=5.5)
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_design.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ F1 DAG
def fig_dag() -> None:
    """Causal structure, single-column.

    Node positions are laid out so that no edge passes through a node box and
    no two boxes overlap: the two causal paths from family membership to the
    error trait (lineage above, release-date/era below) fan out from the left
    and reconverge at Y on the right. All explanatory prose lives in the
    caption, not on the canvas.
    """
    fig, ax = plt.subplots(figsize=(W_SINGLE, 2.15))
    ax.axis("off")
    ax.set_xlim(-0.06, 1.12)
    ax.set_ylim(-0.14, 1.02)
    HW, HH = 0.13, 0.085          # box half-width / half-height

    pos = {
        "F": (0.13, 0.50),        # family membership
        "L": (0.44, 0.82),        # lineage channel
        "R": (0.44, 0.30),        # release quarter (mediator)
        "E": (0.80, 0.30),        # era / shared training environment
        "T": (0.44, 0.02),        # teacher leakage
        "Y": (0.88, 0.72),        # error trait
    }
    labels = {
        "F": "Family\nmembership",
        "L": "Lineage\nchannel",
        "R": "Release\nquarter",
        "E": "Era / shared\nenvironment",
        "T": "Teacher\nleakage",
        "Y": "Error trait\n$Y_i$",
    }
    fills = {"T": "#fef2f2", "Y": "#f0fdf4"}
    edges_c = {"T": "#b91c1c", "Y": "#166534"}

    patch = {}
    for n, (x, y) in pos.items():
        patch[n] = mpatches.FancyBboxPatch(
            (x - HW, y - HH), 2 * HW, 2 * HH, boxstyle="round,pad=0.010",
            fc=fills.get(n, "#eef2f7"), ec=edges_c.get(n, "#334155"), lw=0.9,
            zorder=3)
        ax.add_patch(patch[n])
        ax.text(x, y, labels[n], ha="center", va="center", fontsize=6,
                zorder=4)

    def edge(a, b, color="#334155", lw=1.1, style="-"):
        # patchA/patchB clip the arrow at the box boundary. A fixed shrink in
        # points cannot do this: the boxes are wider than they are tall, so any
        # single shrink value either buries the arrowhead inside a horizontal
        # neighbour or leaves a gap on a vertical one.
        ax.annotate("", xy=pos[b], xytext=pos[a],
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                    linestyle=style, patchA=patch[a],
                                    patchB=patch[b], shrinkA=1, shrinkB=1,
                                    mutation_scale=8),
                    zorder=2)

    edge("F", "L"); edge("L", "Y")                      # lineage path
    edge("F", "R"); edge("R", "E"); edge("E", "Y")      # era path
    edge("T", "E", color="#b91c1c", lw=1.0, style=(0, (3, 1.8)))

    # One role marker only. The dual mediator/confounder argument is made in
    # the caption; crowding the canvas with it is what produced the overprint
    # on the error-trait node in the previous version.
    ax.text(0.44, 0.435, "mediator", ha="center", va="center", fontsize=5.4,
            style="italic", color="#b45309", zorder=4)
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_dag.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ architecture
def fig_pipeline() -> None:
    """Protocol architecture as one left-to-right row, double-column.

    The previous two-row layout mixed row coordinates in its arrow calls, which
    is what drove the stage-3/stage-4 box collision. A single row of five
    stages with the three gates interleaved reads in one pass and halves the
    height. Explanatory prose is deferred to the caption.
    """
    fig, ax = plt.subplots(figsize=(W_DOUBLE, 1.55))
    ax.axis("off")
    ax.set_xlim(0, 14.95)
    ax.set_ylim(0, 3.30)

    BY, BH = 0.30, 2.70           # box bottom / height

    def box(x, w, title, body, fc, ec):
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, BY), w, BH, boxstyle="round,pad=0.03", fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, BY + BH - 0.34, title, ha="center", va="center",
                fontsize=6.4, fontweight="bold")
        ax.text(x + w / 2, BY + BH / 2 - 0.42, body, ha="center", va="center",
                fontsize=5.2, color="#1e293b", linespacing=1.45)

    def gate(x, w, text):
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, BY + BH / 2 - 0.48), w, 0.96, boxstyle="round,pad=0.03",
            fc="#fef3c7", ec="#b45309", lw=0.9))
        ax.text(x + w / 2, BY + BH / 2, text, ha="center", va="center",
                fontsize=4.9, color="#78350f", fontweight="bold",
                linespacing=1.3)

    def arrow(x1, x2):
        ax.annotate("", xy=(x2, BY + BH / 2), xytext=(x1, BY + BH / 2),
                    arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.0,
                                    mutation_scale=8))

    box(0.10, 2.30, "1. Population audit",
        "N = 47 open-weight models\n6 families $\\times$ 14 quarters\n"
        "connected subset (crossed)\n5 verified lineage edges",
        "#eef2f7", "#334155")
    arrow(2.40, 2.62)
    gate(2.65, 1.00, "GATE 1\nidentifiability")
    arrow(3.65, 3.87)

    box(3.90, 2.30, "2. Simulation validation",
        "D1 balanced reference\nD2 realistic occupancy\nD3 nested: must fail\n"
        "estimator + share CIs",
        "#eef2f7", "#334155")
    arrow(6.20, 6.42)
    gate(6.45, 1.00, "GATE 2\nstrict bar")
    arrow(7.45, 7.67)

    box(7.70, 2.30, "3. Pre-analysis design",
        "outcome-independent:\noccupancy + lineage +\nidentifiability + cost\n"
        "22 of 47 ($\\sim$67% cost)",
        "#eef2f7", "#334155")
    arrow(10.00, 10.22)
    gate(10.25, 1.00, "GATE 3\nminimum valid\npopulation")
    arrow(11.25, 11.47)

    box(11.50, 1.55, "4. Measure",
        "5-shot MMLU\n$\\theta_P$ / $\\theta_M$\nbootstrap CIs",
        "#fef2f2", "#991b1b")
    arrow(13.05, 13.27)
    box(13.30, 1.55, "5. Decision",
        "RQ6 rule:\nlineage vs era\ndominance",
        "#f0fdf4", "#166534")
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_pipeline.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ lineage graph
def fig_lineage() -> None:
    fig, ax = plt.subplots(figsize=(W_DOUBLE, 2.95))
    fam_of = {m[3]: m[0] for m in MODELS}

    # model points (public = open circle, gated = filled)
    for m in MODELS:
        fn, fam, q = m[3], m[0], m[1]
        access = EVAL_MANIFEST[fn][2]
        x, y = MODEL_XY[fn]
        ax.scatter(x, y, s=72, color=FAM_COLORS[fam],
                   facecolors="none" if access == "public" else FAM_COLORS[fam],
                   edgecolors=FAM_COLORS[fam], linewidths=1.2, zorder=3)
        # All labels sit at one height directly above their own marker;
        # separation is horizontal only. Staggering them vertically detaches
        # the raised label from its marker and reads as belonging to the row
        # above.
        ax.annotate(m[2], (x, y), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=6.0, color="#334155")

    # verified cross-generation edges (directed parent -> child)
    for parent, child, _q in VERIFIED_EDGES:
        pn = EDGE_ENDPOINT.get(parent); cn = EDGE_ENDPOINT.get(child)
        if pn is None or cn is None:
            continue
        p = _pos(pn); c = _pos(cn)
        if p and c:
            ax.annotate("", xy=c, xytext=p,
                        arrowprops=dict(arrowstyle="-|>", color="#1d4ed8",
                                        lw=2.0, shrinkA=16, shrinkB=16), zorder=2)
    # Mistral-Small chain (documented within-family chain)
    chain = ["Mistral-Small-3", "Mistral-Small-3.1", "Mistral-Small-3.2",
             "Mistral-Small-4", "Devstral-2"]
    for a, b in zip(chain[:-1], chain[1:]):
        p, c = _pos(a), _pos(b)
        if p and c:
            ax.annotate("", xy=c, xytext=p,
                        arrowprops=dict(arrowstyle="-|>", color="#0d9488",
                                        lw=2.0, ls=(0, (4, 2)), shrinkA=16,
                                        shrinkB=16), zorder=2)

    # teacher leakage (cross-family, from outside the design) - dashed grey
    leakage = [
        ("Phi-4", "GPT-4o (closed)"), ("Gemma-4", "Gemini-3 (closed)"),
        ("Gemma-4-12B", "Gemini-3 (closed)"),
    ]
    labelled_src: set[tuple[str, int]] = set()
    for fn, src in leakage:
        p = _pos(fn)
        if p:
            # Gemma-4 and Gemma-4-12B share one teacher; label it once per row
            # rather than printing "Gemini-3 (closed)" twice on top of itself.
            if (src, p[1]) in labelled_src:
                ax.annotate("", xy=(p[0], p[1] - 0.28),
                            xytext=(p[0] - 0.22, p[1] - 0.5),
                            arrowprops=dict(arrowstyle="-|>", color="#94a3b8",
                                            lw=1.1, ls=(0, (2, 2))))
                continue
            labelled_src.add((src, p[1]))
            ax.annotate("", xy=(p[0], p[1] - 0.28), xytext=(p[0] - 0.22, p[1] - 0.5),
                        arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.1,
                                        ls=(0, (2, 2))))
            ax.annotate(src, (p[0], p[1]), textcoords="offset points",
                        xytext=(-8, -12), ha="right", fontsize=6.0,
                        color="#475569")

    # legend
    handles = [
        plt.Line2D([], [], marker="o", color="none", markerfacecolor="#334155",
                   markeredgecolor="#334155", markersize=7, label="gated access"),
        plt.Line2D([], [], marker="o", color="none", markerfacecolor="none",
                   markeredgecolor="#334155", markersize=7, label="public access"),
        plt.Line2D([], [], color="#1d4ed8", lw=2.0, label="verified lineage edge"),
        plt.Line2D([], [], color="#0d9488", lw=2.0, ls=(0, (4, 2)),
                   label="documented within-family chain"),
        plt.Line2D([], [], color="#94a3b8", lw=1.1, ls=(0, (2, 2)),
                   label="cross-family teacher leakage"),
    ]
    # Legend below the axes: anchoring it outside on the right is what forced
    # the previous export past the two-column text width.
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.28),
              ncol=5, fontsize=6.0, frameon=False, handletextpad=0.5,
              columnspacing=1.4)

    ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=45, fontsize=6.5)
    ax.set_yticks(range(len(FAMILIES)), FAMILIES, fontsize=7)
    ax.set_xlabel("release quarter", fontsize=7.5)
    ax.grid(True, which="major", color="#e2e8f0", lw=0.5, zorder=0)
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_lineage.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ F3 G3 trace
def fig_g3_trace() -> None:
    rows = []
    for line in G3_REPORT.read_text().splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 13 or not cells[0].isdigit():
            continue
        rows.append(cells)
    rows = [[c if c not in ("-", "") else None for c in r] for r in rows]

    fig, ax = plt.subplots(figsize=(W_SINGLE, 2.35))
    ax.axhspan(-4.0, 4.0, color="#c8e6c9", alpha=0.5,
               label="confirmation band ($|$bias$|\\leq$4.0pp)")
    ax.axhline(0, color="grey", lw=0.6)
    # n=21 and n=22 sit ~0.1in apart on a single-column axis; separate their
    # marker clusters horizontally so the points do not stack.
    n_offs = {"47": 0.0, "21": -0.18, "22": 0.18}

    for r in rows:
        n = int(r[0])
        xoff = n_offs.get(str(n), 0.0)
        for col, marker in [(9, "^"), (10, "o"), (11, "v"), (12, "s")]:
            v = r[col]
            if v is None:
                continue
            v = float(v)
            color = "#4caf50" if abs(v) <= 4.0 else "#e53935"
            face = color if col in (10, 12) else "white"
            ax.scatter(n + xoff, v, marker=marker, s=26, color=face,
                       edgecolors="black", linewidths=0.5, zorder=3)

    # Stagger the three vertical annotations: at this scale n=21 and n=22 are
    # adjacent, so their labels are placed on opposite sides of the axis rather
    # than stacked (which is what produced the "FAILPASS" overprint).
    # n=21 and n=22 are one unit apart on a 30-unit axis, so their labels
    # cannot both sit above the markers. n=21 is labelled below the data
    # (lowest marker -5.0) and n=22 above it (highest marker 3.3); the two
    # never share a horizontal band.
    for n, label, y, va, color in [
        (21, "$n_0$=21\nfail", -7.2, "top", "#b91c1c"),
        (22, "winner\n$n$=22", 5.0, "bottom", "#166534"),
        (47, "full\npopulation", 5.0, "bottom", "#334155"),
    ]:
        # vlines, not axvline: a full-height rule would run straight through
        # the annotation text sitting above/below the data.
        ax.vlines(n, -6.2, 4.4, color="grey", lw=0.6, ls=":", alpha=0.7)
        ax.annotate(label, (n, y), ha="center", va=va, fontsize=6,
                    color=color, linespacing=1.3)
    ax.set_xlabel("population size $n$", fontsize=7.5)
    ax.set_ylabel("confirmation era-share bias (pp)", fontsize=7.5)
    ax.set_xlim(17.5, 50.5)
    ax.set_ylim(-9.6, 8.6)
    # Legend below the axes so it cannot overprint the in-plot annotations.
    ax.legend(fontsize=5.8, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.30))
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_g3_trace.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ D3 panel
def _d3_panel(ax, rates, label, colors) -> None:
    bars = ax.bar(["A", "B"], rates, color=colors, edgecolor="black",
                  linewidth=0.5, width=0.6)
    for b, v in zip(bars, rates):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.0, f"{v:.0f}%",
                ha="center", fontsize=6)
    ax.set_ylim(0, 116)
    ax.set_title(label, fontsize=6.5)
    ax.tick_params(labelsize=6)


def fig_d3() -> None:
    rng = np.random.default_rng(7)
    frames = []
    for scen in ("A", "B"):
        rows = phase1_simulation.run_nested("d3", scen, 300, rng)
        frames.append(pd.DataFrame(rows))
    df = pd.concat(frames)

    joint = [100.0 * df[df["scenario"] == s]["detected"].mean() for s in ("A", "B")]
    silent = df[df["detected"] == 0]["silent_ci_covers"]

    # Four panels at two-column width. The previous version drew three panels
    # on a 9.6in canvas inside a 6.99in text block, so the third panel
    # (profile-likelihood flatness) fell outside the trim and was never
    # visible; it also overwrote panel 1's detector label with the joint-
    # detection summary, leaving the first detector unnamed.
    fig, axes = plt.subplots(1, 4, figsize=(W_DOUBLE, 1.75), sharey=True)

    det = ["d_collinearity", "d_se_inflation", "d_profile_flat"]
    labels = ["BLUP\ncollinearity", "SE/est.\ninflation", "profile-lik.\nflatness"]
    for ax, col, lab in zip(axes[:3], det, labels):
        rates = [100.0 * df[df["scenario"] == s][col].mean() for s in ("A", "B")]
        _d3_panel(ax, rates, lab, ["#4e79a7", "#59a14f"])
    _d3_panel(axes[3], joint, "joint\ndetection", ["#166534", "#166534"])

    axes[0].set_ylabel("repetitions flagged (%)", fontsize=6.5)
    assert len(silent) == 0 or silent.sum() == 0, (
        "silent CI coverage must be zero under D3")
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_d3.png", dpi=DPI)
    plt.close(fig)


def main() -> int:
    FIGS_DIR.mkdir(parents=True, exist_ok=True)
    fig_design()
    fig_dag()
    fig_pipeline()
    fig_lineage()
    fig_g3_trace()
    fig_d3()
    print(f"wrote 6 figures to {FIGS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
