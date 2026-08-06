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

DPI = 300
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


def _pos(full_name: str) -> tuple[int, int] | None:
    row = [m for m in MODELS if m[3] == full_name]
    return (Q_IX[row[0][1]], FAMILIES.index(row[0][0])) if row else None


# ------------------------------------------------------------ F2 design
def fig_design() -> None:
    counts = design_counts().reindex(index=FAMILIES, columns=QUARTERS, fill_value=0)
    counts = counts.fillna(0).astype(int)
    crossed_q = quarters_with_n_families(2)
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    im = ax.imshow(counts.to_numpy(int), cmap="YlGnBu", aspect="auto")
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            v = int(counts.iloc[i, j])
            if v:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=7,
                        color="#08306b")
    for q in QUARTERS:
        if q in crossed_q:
            ax.add_patch(plt.Rectangle((Q_IX[q] - 0.5, -0.5), 1, counts.shape[0],
                                       fill=False, edgecolor="#d97706",
                                       lw=1.4, ls=(0, (5, 2))))
    ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=45, fontsize=7)
    ax.set_yticks(range(len(FAMILIES)), FAMILIES, fontsize=8)
    ax.set_xlabel("release quarter (public release date, not HF createdAt)",
                  fontsize=8)
    ax.set_ylabel("model family", fontsize=8)
    cb = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.01)
    cb.set_label("models per cell", fontsize=8)
    ax.set_title(f"Connected subset of the open-model population: 47 models, "
                 f"6 families x 14 quarters ({len(crossed_q)}/14 quarters crossed)",
                 fontsize=9)
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_design.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ F1 DAG
def fig_dag() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.axis("off")
    # node positions
    pos = {
        "F": (0.10, 0.72),          # family membership
        "L": (0.42, 0.86),          # lineage / inherited-error channel
        "R": (0.38, 0.52),          # release date
        "E": (0.62, 0.30),          # era / shared training environment
        "T": (0.82, 0.72),          # teacher leakage
        "Y": (0.78, 0.06),          # error trait
    }
    labels = {
        "F": "Family\nmembership",
        "L": "Lineage channel\n(inherited blind spots)",
        "R": "Release date\n(quarter)",
        "E": "Era / shared\ntraining environment",
        "T": "Teacher leakage\n(cross-family transfer)",
        "Y": "Error trait\n$Y_i$",
    }

    def node(n):
        x, y = pos[n]
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - 0.105, y - 0.075), 0.21, 0.15, boxstyle="round,pad=0.012",
            fc="#eef2f7", ec="#334155", lw=1.2))
        ax.text(x, y, labels[n], ha="center", va="center", fontsize=8)

    def edge(a, b, color="#334155", lw=1.6, style="-", zorder=1):
        ax.annotate("", xy=pos[b], xytext=pos[a],
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                    linestyle=style, shrinkA=22, shrinkB=22),
                    zorder=zorder)

    for n in pos:
        node(n)
    edge("F", "L"); edge("L", "Y")
    edge("F", "R"); edge("R", "E"); edge("E", "Y")
    edge("T", "E", color="#e15759", lw=1.4, style=(0, (4, 2)))

    # mediator / confounder annotations
    ax.annotate("mediator: the family's release schedule\npasses lineage through its era",
                xy=(0.50, 0.55), xytext=(0.18, 0.24),
                fontsize=7.5, color="#334155",
                arrowprops=dict(arrowstyle="-", color="#94a3b8", lw=0.8))
    ax.annotate("era is a mediator of the lineage path and a\n"
                "potential confounder of the observational\n"
                "family--error association",
                xy=(0.62, 0.26), xytext=(0.50, 0.86),
                fontsize=7.5, color="#b45309",
                arrowprops=dict(arrowstyle="-", color="#d97706", lw=0.8))

    ax.text(0.5, 0.03,
            "Single causal attribution is impossible by construction: a child model inherits both\n"
            "the errors of its parent (lineage channel) and the training environment of its own\n"
            "release date. Two estimands respond: $\\theta_P$ adjusts for era grouping; $\\theta_M$\n"
            "holds era exactly fixed on co-released cohorts and verified fine-tune chains.",
            ha="center", va="center", fontsize=8, color="#334155")
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_dag.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ architecture
def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)

    def box(x, y, w, h, title, body, fc, ec, fs=7.5):
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="center",
                fontsize=9, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.28, body, ha="center", va="center",
                fontsize=fs, color="#1e293b", linespacing=1.45)

    def gate(x, y, text):
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, y), 1.25, 0.62, boxstyle="round,pad=0.02", fc="#fef3c7",
            ec="#b45309", lw=1.3))
        ax.text(x + 0.625, y + 0.31, text, ha="center", va="center",
                fontsize=7.2, color="#78350f", fontweight="bold")

    def arrow(x1, y1, x2, y2, color="#475569"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8))

    y = 6.4
    box(0.3, y, 2.9, 2.6, "1. Population audit",
        "N = 47 open-weight models\n6 families x 14 quarters\nconnected subset (crossed)\n5 verified lineage edges",
        "#eef2f7", "#334155")
    gate(3.45, y + 0.99, "GATE 1\nidentifiability")
    box(5.0, y, 2.9, 2.6, "2. Simulation validation",
        "D1 balanced reference\nD2 realistic occupancy\nD3 nested: must fail\nestimator + share CIs validated",
        "#eef2f7", "#334155")
    gate(8.15, y + 0.99, "GATE 2\nstrict bar")

    y = 1.4
    gate(0.55, y + 0.99, "GATE 3\nminimum valid\npopulation")
    box(1.85, y, 3.3, 2.6, "3. Pre-analysis design (G3)",
        "outcome-independent: occupancy +\nlineage + identifiability + cost\nNEVER trait values\nresult: 22 of 47 models (~67% cost)",
        "#eef2f7", "#334155")
    box(5.4, y, 2.6, 2.6, "4. Measurement + decomposition",
        "5-shot MMLU pass\ntrait assembly\ntheta_P (REML) / theta_M\nbootstrap CIs",
        "#fef2f2", "#991b1b")
    box(8.25, y, 1.55, 2.6, "5. Decision",
        "RQ6 rule:\nlineage vs era\ndominance",
        "#f0fdf4", "#166534")

    arrow(3.2, y + 2.4, 3.45, y + 1.9)
    arrow(4.7, y + 2.4, 5.0, y + 2.4)
    arrow(7.9, y + 2.4, 8.15, y + 1.9)
    arrow(1.8, y + 1.9, 1.85, y + 1.4 + 1.9)
    arrow(5.15, y + 2.4, 5.4, y + 2.4)
    arrow(8.0, y + 2.4, 8.25, y + 2.4)

    ax.text(5.0, 0.28,
            "The ordering is the contribution: identifiability before measurement, simulation before\n"
            "real data, study-population design before inference. Stages 1--3 are complete and\n"
            "reported here; stage 4 is the pre-registered eval pass (Exp02_GPU_Runbook.md).",
            ha="center", va="center", fontsize=8, color="#334155")
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_pipeline.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ lineage graph
def fig_lineage() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    fam_of = {m[3]: m[0] for m in MODELS}

    # model points (public = open circle, gated = filled)
    for m in MODELS:
        fn, fam, q = m[3], m[0], m[1]
        access = EVAL_MANIFEST[fn][2]
        x, y = Q_IX[q], FAMILIES.index(fam)
        ax.scatter(x, y, s=72, color=FAM_COLORS[fam],
                   facecolors="none" if access == "public" else FAM_COLORS[fam],
                   edgecolors=FAM_COLORS[fam], linewidths=1.2, zorder=3)
        ax.annotate(m[2], (x, y), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=5.6, color="#475569")

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
    for fn, src in leakage:
        p = _pos(fn)
        if p:
            ax.annotate("", xy=(p[0], p[1] - 0.28), xytext=(p[0] - 0.22, p[1] - 0.5),
                        arrowprops=dict(arrowstyle="-|>", color="#94a3b8", lw=1.1,
                                        ls=(0, (2, 2))))
            ax.annotate(src, (p[0], p[1]), textcoords="offset points",
                        xytext=(-8, -12), ha="right", fontsize=5.4, color="#64748b")

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
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.02),
              fontsize=6.5, frameon=False)

    ax.set_xticks(range(len(QUARTERS)), QUARTERS, rotation=45, fontsize=7)
    ax.set_yticks(range(len(FAMILIES)), FAMILIES, fontsize=8)
    ax.set_xlabel("release quarter", fontsize=8)
    ax.set_title("Verified lineage on the connected subset: 5 parent--offspring "
                 "edges + documented Mistral-Small chain", fontsize=9)
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

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.axhspan(-4.0, 4.0, color="#c8e6c9", alpha=0.5,
               label="confirmation band (|bias| <= 4.0pp)")
    ax.axhline(0, color="grey", lw=0.6)
    n_offs = {"47": 0.0, "21": -0.22, "22": 0.0}

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
            ax.scatter(n + xoff, v, marker=marker, s=42, color=face,
                       edgecolors="black", linewidths=0.6, zorder=3)

    for n, label in [(47, "baseline\nPASS"), (21, "n0=21\nFAIL"),
                     (22, "winner\nPASS")]:
        ax.axvline(n, color="grey", lw=0.7, ls=":", alpha=0.7)
        ax.annotate(label, (n, 4.9), ha="center", fontsize=8, color="#333333")
    ax.set_xlabel("population size n")
    ax.set_ylabel("confirmation era-share bias (pp)")
    ax.set_title("G3 decision trace: era-share bias at the 1000-rep confirmation "
                 "(and 2000-rep robustness); o = B, ^ = A, s = B 2000, v = A 2000")
    ax.set_xlim(18, 50)
    ax.set_ylim(-6.8, 6.2)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIGS_DIR / "fig_g3_trace.png", dpi=DPI)
    plt.close(fig)


# ------------------------------------------------------------ D3 panel
def fig_d3() -> None:
    rng = np.random.default_rng(7)
    frames = []
    for scen in ("A", "B"):
        rows = phase1_simulation.run_nested("d3", scen, 300, rng)
        frames.append(pd.DataFrame(rows))
    df = pd.concat(frames)

    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.4))

    det = ["d_collinearity", "d_se_inflation", "d_profile_flat"]
    labels = ["BLUP\ncollinearity", "SE/est.\ninflation", "profile-lik.\nflatness"]
    for ax, col, lab in zip(axes[:3], det, labels):
        rates = [100.0 * df[df["scenario"] == s][col].mean() for s in ("A", "B")]
        bars = ax.bar(["A", "B"], rates, color=["#4e79a7", "#59a14f"],
                      edgecolor="black", linewidth=0.6)
        for b, v in zip(bars, rates):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}%",
                    ha="center", fontsize=8)
        ax.set_ylim(0, 108)
        ax.set_title(lab, fontsize=8.5)
        ax.set_ylabel("repetitions flagged (%)", fontsize=7.5)
        ax.tick_params(labelsize=8)
        if ax is not axes[0]:
            ax.set_ylabel("")

    joint = [100.0 * df[df["scenario"] == s]["detected"].mean() for s in ("A", "B")]
    axes[0].set_title("joint detection:\n100% / 100%", fontsize=9,
                      color="#166534")

    silent = df[df["detected"] == 0]["silent_ci_covers"]
    axes[0].text(1.5, -26, f"silent CI coverage (undetected reps): "
                f"{len(silent)} total, 0 covered", ha="center", fontsize=8,
                color="#166534")
    fig.suptitle("D3 (nested design): aliasing must be detected, never silently "
                 "\"succeed\" -- 300 reps/scenario, fixed seed",
                 fontsize=9.5)
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
