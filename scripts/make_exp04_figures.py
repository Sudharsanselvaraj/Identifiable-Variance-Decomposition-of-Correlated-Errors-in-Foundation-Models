#!/usr/bin/env python3
"""Every manuscript figure, generated from committed outputs.

Numbers are read from results/ (written by run_exp04_final.py,
run_exp04_item_null.py, run_pair_gate_audit.py and run_precision_scaling.py);
nothing is typed in by hand. Two figures (agreement by release gap, the
lineage-by-month map) also need the rebuilt frozen lists and validated answer
files (see docs/REPRODUCIBILITY_CHECKLIST.md); the two schematic figures
(workflow, lineage-and-time illustration) take their counts from results/.

Output: vector PDFs in paper/figures/ with embedded TrueType fonts and no
creation timestamp, so reruns are byte-stable.

Usage (repo root):  python3 scripts/make_exp04_figures.py [--only NAME ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RES = ROOT / "results"
FIG = ROOT / "paper" / "figures"

# ------------------------------------------------------------------ style
COL, FULL = 3.5, 7.16                        # IEEE column / text width (in)
# Palette follows the authors' earlier manuscript (steel blue, salmon, sage);
# text is Times to match the IEEE body, diagrams are plain square boxes.
BLUE, LBLUE = "#6c8ebf", "#b5c7df"           # lineage / primary
ORANGE, LORANGE = "#d8887f", "#ecc3be"       # release time (salmon)
GREEN = "#8fbc94"
GREY, LGREY = "#606060", "#c0c0c0"
BOX_FACE, BOX_EDGE = "#eef3f8", "#5b7a99"
HILITE = "#e9eef5"
RED = "#c44e52"                              # criterion / threshold lines
INK = "#333333"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"],
    "mathtext.fontset": "stix", "font.size": 8,
    "axes.titlesize": 9, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 8, "axes.linewidth": 0.7, "axes.edgecolor": "#b0b0b0",
    "axes.labelcolor": INK, "text.color": INK, "axes.titlecolor": INK,
    "xtick.color": GREY, "ytick.color": GREY, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": "#e5e5e5",
    "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False,
    "pdf.fonttype": 42, "lines.linewidth": 1.0, "errorbar.capsize": 2.0,
    "axes.titleweight": "bold", "axes.titlelocation": "center",
})
Z = 1.959964
SAMPLES = {"primary": "Primary", "primary_S2": "Primary, acc ≥ 0.30",
           "expanded": "Expanded", "expanded_S2": "Expanded, acc ≥ 0.30"}


# One display name per lineage root, used by every figure that names roots.
ROOT_LABEL = {
    "meta-llama/Meta-Llama-3-8B": "Llama-3-8B", "meta-llama/Meta-Llama-3-70B": "Llama-3-70B",
    "meta-llama/Llama-2-7b-hf": "Llama-2-7B", "mistralai/Mistral-7B-v0.1": "Mistral-7B-v0.1",
    "mistral-community/Mistral-7B-v0.2": "Mistral-7B-v0.2",
    "mistralai/Mixtral-8x7B-v0.1": "Mixtral-8x7B-v0.1", "google/gemma-2b": "Gemma-2B",
    "google/gemma-7b": "Gemma-7B", "01-ai/Yi-34B-200K": "Yi-34B-200K",
    "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T": "TinyLlama-1.1B-3T",
    "Locutusque/TinyMistral-248M": "TinyMistral-248M",
    "openlm-research/open_llama_3b": "OpenLLaMA-3B"}


# MMLU subject -> category, as tagged in lm-evaluation-harness 0.4.12 (tasks/mmlu/default).
MMLU_CATEGORY = {**{s_: "STEM" for s_ in (
    "abstract_algebra anatomy astronomy college_biology college_chemistry "
    "college_computer_science college_mathematics college_physics computer_security "
    "conceptual_physics electrical_engineering elementary_mathematics high_school_biology "
    "high_school_chemistry high_school_computer_science high_school_mathematics "
    "high_school_physics high_school_statistics machine_learning").split()},
    **{s_: "humanities" for s_ in (
        "formal_logic high_school_european_history high_school_us_history "
        "high_school_world_history international_law jurisprudence logical_fallacies "
        "moral_disputes moral_scenarios philosophy prehistory professional_law "
        "world_religions").split()},
    **{s_: "social_sciences" for s_ in (
        "econometrics high_school_geography high_school_government_and_politics "
        "high_school_macroeconomics high_school_microeconomics high_school_psychology "
        "human_sexuality professional_psychology public_relations security_studies sociology "
        "us_foreign_policy").split()},
    **{s_: "other" for s_ in (
        "business_ethics clinical_knowledge college_medicine global_facts human_aging "
        "management marketing medical_genetics miscellaneous nutrition professional_accounting "
        "professional_medicine virology").split()}}
CAT_COLORS = {"STEM": BLUE, "humanities": ORANGE, "social_sciences": "#6a9f6f", "other": GREY}


def root_label(root: str) -> str:
    return ROOT_LABEL.get(root, root.split("/")[-1])


def save(fig, name: str) -> str:
    fig.savefig(FIG / f"{name}.pdf", metadata={"CreationDate": None})
    plt.close(fig)
    return name


def zero(ax, horizontal=False):
    (ax.axhline if horizontal else ax.axvline)(0, color="#999999", lw=0.7, ls=(0, (4, 3)),
                                               zorder=0)
    if not horizontal:                       # estimates on x: grid on x, not y
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)


def box(ax, x, y, w, h, text, face=BOX_FACE, edge=BOX_EDGE, size=8.5, bold_first=True,
        lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                fc=face, ec=edge, lw=lw, ls=ls, transform=ax.transAxes))
    lines = text.split("\n")
    if bold_first:
        ax.text(x + w / 2, y + h - 0.13 * h, lines[0], ha="center", va="top", fontsize=size,
                weight="bold", color="black", transform=ax.transAxes)
        ax.text(x + w / 2, y + 0.40 * h, "\n".join(lines[1:]),
                ha="center", va="center", fontsize=size - 0.4, color="black",
                transform=ax.transAxes, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
                transform=ax.transAxes, linespacing=1.25)


def arrow(ax, p, q, color=BOX_EDGE, style="-|>", lw=0.8, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, color=color,
                                 lw=lw, transform=ax.transAxes,
                                 connectionstyle=f"arc3,rad={rad}"))


def blank(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    return fig, ax


def fmt(n) -> str:
    return f"{int(n):,}"


# ------------------------------------------------------------------ data
def flow() -> dict:
    f = pd.read_csv(RES / "exp04_final/model_flow.csv").set_index("stage")
    e = pd.read_csv(RES / "exp04_final/sample_exclusions.csv").set_index("category")
    v = pd.read_csv(RES / "exp04_validation/per_model.csv")
    den = pd.read_csv(RES / "exp04_final/denominators.csv").set_index("population")
    pre = pd.read_csv(RES / "exp04_final/prereg_12.csv")
    row = lambda s: f.loc[[k for k in f.index if k.startswith(s)][0]]  # noqa: E731
    return dict(
        total=row("v1 leaderboard").primary, elig_p=row("eligible (primary").primary,
        elig_x=row("eligible (expanded").expanded, frozen_p=row("frozen").primary,
        frozen_x=row("frozen").expanded, val_p=row("validated").primary,
        val_x=row("validated").expanded, strict_p=row("  of which").primary
        if any(k.startswith("  of which") for k in f.index) else None,
        excl=e, union=len(v), overlap=int((v.in_primary_sample & v.in_expanded_sample).sum()),
        cats=v.category.value_counts(), pairs_p=den.loc["primary", "pairs"],
        pairs_x=den.loc["expanded", "pairs"], den=den, n_prereg=pre.analysis.nunique(),
        near_chance=int(((v.category == "validated") & (v.accuracy < 0.30)).sum()),
        acc=v.loc[v.category == "validated", "accuracy"].to_numpy())


def population(name: str):
    from lineage_era.ollb import analysis as A
    try:
        pop, _ = A.load_population(name, False)
    except FileNotFoundError as err:
        raise SystemExit(
            f"{err}\nTwo figures need the rebuilt frozen lists and the validated answer "
            "files, which are not redistributed: run the data steps of "
            "docs/REPRODUCIBILITY_CHECKLIST.md section 4 first (fetch_v1_contents_meta, "
            "roster_v1, rebuild_frozen_lists, download_ollb_v1, validation_report).") from None
    return pop


# ------------------------------------------------------------------ 1 precision
def fig_precision():
    sc = pd.read_csv(RES / "precision_gate/family_scaling.csv")
    fig, ax = plt.subplots(figsize=(COL, 2.35))
    styles = {8: (LBLUE, "s", "--"), 14: (BLUE, "o", "-")}
    for (E, M), g in sc.groupby(["E", "M"]):
        c, mk, ls = styles[E]
        ax.plot(g.F, g[["worst_family", "worst_era"]].max(axis=1), marker=mk, ms=3.2, color=c,
                ls=ls, label=f"{E} release quarters, {M} models per family")
    obs = pd.read_csv(RES / "precision_gate/summary.csv").set_index("design")
    tab = {"obs16": "16", "sel22": "22", "cand47": "47", "sweep_F6_E8_M5": "30",
           "sweep_F7_E8_M6": "42"}                        # Table I rows (models)
    o = obs.loc[list(tab)]
    ax.scatter(o.families, o.worst_share_rmse_mc, marker="x", s=16, color=ORANGE, lw=0.9,
               zorder=4, label="candidate designs (label: models)")
    offs = {"obs16": (-7, 0), "sel22": (7, 0), "sweep_F6_E8_M5": (-9, 6),
            "cand47": (-10, -3), "sweep_F7_E8_M6": (8, -5)}           # points, avoid overlap
    for k, r in o.iterrows():
        ax.annotate(tab[k], (r.families, r.worst_share_rmse_mc), xytext=offs[k],
                    textcoords="offset points", fontsize=7.5, color=ORANGE, va="center",
                    ha="right" if offs[k][0] < 0 else "left",
                    arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.4, shrinkA=0,
                                    shrinkB=2))
    ax.axhline(0.10, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.text(sc.F.max(), 0.096, "target RMSE 0.10", color=RED, ha="right", va="top", fontsize=7.5)
    ax.set_xlabel("Number of families (lineage levels)")
    ax.set_ylabel("Worst-case RMSE of a variance share")
    ax.set_ylim(0, 0.33); ax.set_xlim(-2, 63)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout(pad=0.3)
    return save(fig, "precision_scaling")


# ------------------------------------------------------------------ 1 workflow
def fig_workflow():
    fig, ax = blank(FULL, 1.75)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    steps = [("Source", "leaderboard,\nper-item MMLU"), ("Lineage", "declared\nparents → root"),
             ("Freeze", "≤ 40 per root,\nhashed lists"), ("Validate", "every item vs\nstored answer"),
             ("Pairs", "same wrong\noption"), ("Estimate", "pair model,\ndyadic SEs"),
             ("Check", "robustness,\npartly post hoc")]
    n, gap = len(steps), 0.012
    w, y0, h = (1 - gap * (n - 1) - 0.004) / n, 0.08, 0.56
    for k, (t, body) in enumerate(steps):
        x = 0.002 + k * (w + gap)
        last = k == n - 1
        box(ax, x, y0, w, h, f"{k + 1}  {t}\n{body}", size=8.5,
            face="#f6f6f6" if last else BOX_FACE, edge=GREY if last else BOX_EDGE,
            ls="--" if last else "-")
        if k:
            arrow(ax, (x - gap + 0.001, y0 + h / 2), (x - 0.001, y0 + h / 2))
    x1, x2 = 0.002 + (w + gap), 0.002 + 5 * (w + gap) + w
    ax.plot([x1, x1, x2, x2], [0.73, 0.78, 0.78, 0.73], color=BLUE, lw=0.8,
            transform=ax.transAxes)
    ax.text((x1 + x2) / 2, 0.81, "fixed in a dated analysis plan before any pair outcome "
            "was computed", ha="center", va="bottom", fontsize=9, color=BLUE,
            transform=ax.transAxes)
    return save(fig, "fig_workflow")


# ------------------------------------------------------------------ 3 schematic
def fig_schematic():
    fig, ax = plt.subplots(figsize=(COL, 2.55))
    ax.set_xlim(-0.8, 12.4); ax.set_ylim(0.0, 3.95)
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    ax.set_yticks([]); ax.set_xticks(range(0, 13, 2))
    ax.set_xlabel("Upload month (illustration; hypothetical models)")
    GREEN, LGREEN = "#4f6f52", "#a9c3a6"
    lanes = {"A": (2.35, 0.0, [("A1", 5), ("A2", 6), ("A3", 10)], BLUE, LBLUE),
             "B": (0.75, 7.0, [("B1", 9), ("B2", 10)], GREEN, LGREEN)}
    pos = {}
    for r, (y, m0, kids, c, lc) in lanes.items():
        ax.plot([m0, 11.6], [y, y], color="#e3e3e3", lw=0.8, zorder=0)
        ax.scatter(m0, y, s=48, marker="s", color=c, zorder=3)
        ax.text(m0, y + 0.28, f"root {r}", ha="center", fontsize=8.8, weight="bold", color=c)
        for name, m in kids:
            ax.annotate("", (m, y), (m0, y), arrowprops=dict(
                arrowstyle="-|>", color=LGREY, lw=0.6, mutation_scale=5, shrinkA=3, shrinkB=3,
                connectionstyle="arc3,rad=-0.28"))
            ax.scatter(m, y, s=24, color=lc, ec=c, lw=0.6, zorder=3)
            ax.text(m, y - 0.3, name, ha="center", fontsize=8.5)
            pos[name] = (m, y)
    def bracket(a, b, y, txt, c):
        x1, x2 = pos[a][0], pos[b][0]
        ax.plot([x1, x1, x2, x2], [y + 0.1, y, y, y + 0.1], color=c, lw=0.8)
        ax.text((x1 + x2) / 2, y - 0.08, txt, color=c, ha="center", va="top", fontsize=8.0)
    bracket("A1", "A2", 1.72, "shared root,\ngap 1 (bin 1–2)", BLUE)
    (xa, ya), (xb, yb) = pos["A3"], pos["B2"]
    ax.annotate("", (xb + 0.05, yb + 0.12), (xa + 0.05, ya - 0.42), arrowprops=dict(
        arrowstyle="<->", color=ORANGE, lw=0.9, mutation_scale=6))
    ax.text(xa + 0.35, (ya + yb) / 2 - 0.1, "different roots,\nsame month\n(bin 0)",
            color=ORANGE, fontsize=8.0, va="center")
    ax.text(-0.6, 0.12, "arcs: declared fine-tune ancestry", fontsize=7.5, color=GREY,
            ha="left")
    ax.text(-0.6, 3.93, "Outcome per pair: same wrong option given both wrong,\n"
            "adjusted for both models' accuracies", fontsize=7.5, color=INK, ha="left",
            va="top")
    fig.tight_layout(pad=0.3)
    return save(fig, "fig_schematic")


# ------------------------------------------------------------------ 3 data flow
# Drawing helpers for the study-flow diagram (inch coordinates, equal aspect).
def _cyl(ax, cx, top, w, h, label, size=7.6):
    """Database cylinder; label in the upper body, room for an arrow below."""
    eh = 0.09
    ax.add_patch(Ellipse((cx, top - h), w, eh, fc="#d4d4d4", ec="black", lw=0.6, zorder=2))
    ax.add_patch(Rectangle((cx - w / 2, top - h), w, h, fc="white", ec="none", zorder=3))
    ax.add_patch(Rectangle((cx - w / 2, top - h), w, h * 0.3, fc="#ececec", ec="none", zorder=3))
    for xx in (cx - w / 2, cx + w / 2):
        ax.plot([xx, xx], [top - h, top], color="black", lw=0.6, zorder=4)
    ax.add_patch(Ellipse((cx, top), w, eh, fc="white", ec="black", lw=0.6, zorder=4))
    ax.text(cx, top - 0.09 - 0.06 * (label.count("\n") + 1), label, ha="center", va="center", fontsize=size, zorder=5,
            linespacing=1.05)


def _down(ax, x, y0, y1):
    """Thick grey block arrow, as in the cylinders' outputs."""
    from matplotlib.patches import FancyArrow
    ax.add_patch(FancyArrow(x, y0, 0, y1 - y0, width=0.055, head_width=0.14, head_length=0.08,
                            length_includes_head=True, fc="#a9a9a9", ec="#4d4d4d", lw=0.5,
                            zorder=6))


def _line_arrow(ax, pts, color="black", lw=0.7):
    """Polyline whose last segment ends in an arrow head."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, zorder=1, solid_capstyle="butt")
    ax.annotate("", pts[-1], pts[-2], arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                                      mutation_scale=7, shrinkA=0, shrinkB=0))


def _doc(ax, x, y, w, h, ls="-"):
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    a = 0.03
    verts = [(x, y + a), (x, y + h), (x + w, y + h), (x + w, y + a),
             (x + 0.65 * w, y + 3 * a), (x + 0.35 * w, y - 2 * a), (x, y + a), (x, y + a)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), fc="white", ec="black", lw=0.6, ls=ls, zorder=4))


def _stack(ax, x, y, w, h, text, size=7.8, ls="-"):
    """Stack of three documents with a count, as in the reference diagram."""
    for k in (2, 1, 0):
        _doc(ax, x + k * 0.028, y + k * 0.028, w, h, ls=ls)
    ax.text(x + w / 2, y + h / 2 + 0.015, text, ha="center", va="center", fontsize=size,
            zorder=5, linespacing=1.1)


def _folder(ax, x, y, w, h):
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon([(x, y), (x, y + h), (x + 0.36 * w, y + h), (x + 0.44 * w, y + 0.88 * h),
                          (x + w, y + 0.88 * h), (x + w, y)], fc="#d99a20", ec="black", lw=0.6,
                         zorder=3))
    for k, fc in ((0, "#dcdcdc"), (1, "white")):
        ax.add_patch(Rectangle((x + 0.12 * w + k * 0.03, y + 0.22 * h - k * 0.03), 0.7 * w,
                               0.72 * h, fc=fc, ec="#555555", lw=0.5, zorder=4))
        for t in range(3):
            yy = y + 0.8 * h - k * 0.03 - t * 0.1 * h
            ax.plot([x + 0.2 * w + k * 0.03, x + 0.62 * w + k * 0.03], [yy, yy], color="#8a8a8a",
                    lw=0.5, zorder=4)
    ax.add_patch(Polygon([(x, y), (x + 0.06 * w, y + 0.6 * h), (x + 1.03 * w, y + 0.6 * h),
                          (x + w, y)], fc="#f6cf55", ec="black", lw=0.6, zorder=5))
    ax.add_patch(Rectangle((x + 0.55 * w, y + 0.22 * h), 0.28 * w, 0.11 * h, fc="#e0524e",
                           ec="black", lw=0.5, zorder=6))


def _icon_monitor(ax, cx, cy):
    from matplotlib.patches import Polygon
    ax.add_patch(FancyBboxPatch((cx - 0.25, cy - 0.12), 0.5, 0.32,
                                boxstyle="round,pad=0,rounding_size=0.03", fc="#2c3e50",
                                ec="#1b2631", lw=0.6, zorder=3))
    ax.add_patch(Rectangle((cx - 0.215, cy - 0.085), 0.43, 0.25, fc="#e8f1fa", ec="none", zorder=4))
    for k, (hh, c) in enumerate(zip((0.07, 0.12, 0.09, 0.17), ("#e74c3c", "#f39c12", "#27ae60",
                                                              "#3498db"))):
        ax.add_patch(Rectangle((cx + 0.0 + k * 0.045, cy - 0.065), 0.032, hh, fc=c, ec="#1b2631",
                               lw=0.4, zorder=5))
    ax.add_patch(plt.Circle((cx - 0.12, cy + 0.06), 0.055, fc="#f39c12", ec="#1b2631", lw=0.4,
                            zorder=5))
    from matplotlib.patches import Wedge
    ax.add_patch(Wedge((cx - 0.12, cy + 0.06), 0.055, 0, 120, fc="#3498db", ec="#1b2631", lw=0.4,
                       zorder=6))
    for t in range(3):
        ax.plot([cx - 0.19, cx - 0.06], [cy - 0.02 - t * 0.022] * 2, color="#2c3e50", lw=0.7,
                zorder=5)
    ax.add_patch(Rectangle((cx - 0.03, cy - 0.17), 0.06, 0.05, fc="#2c3e50", ec="none", zorder=3))
    ax.add_patch(Polygon([(cx - 0.11, cy - 0.19), (cx + 0.11, cy - 0.19), (cx + 0.08, cy - 0.165),
                          (cx - 0.08, cy - 0.165)], fc="#2c3e50", ec="none", zorder=3))


def _icon_tree(ax, cx, cy):
    """Lineage icon: a root checkpoint and its declared fine-tunes."""
    root = (cx, cy + 0.12)
    kids = [(cx - 0.17, cy - 0.01), (cx + 0.17, cy - 0.01)]
    grand = [(cx - 0.25, cy - 0.14), (cx - 0.09, cy - 0.14), (cx + 0.17, cy - 0.14)]
    for a, b in [(root, kids[0]), (root, kids[1]), (kids[0], grand[0]), (kids[0], grand[1]),
                 (kids[1], grand[2])]:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#2c3e50", lw=0.9, zorder=3)
    ax.add_patch(Rectangle((root[0] - 0.05, root[1] - 0.05), 0.1, 0.1, fc=BLUE, ec="#1b2631",
                           lw=0.6, zorder=4))
    for (x, y) in kids + grand:
        ax.add_patch(plt.Circle((x, y), 0.042, fc=LBLUE, ec="#1b2631", lw=0.6, zorder=4))


def _icon_clipboard(ax, cx, cy):
    from matplotlib.patches import Polygon
    ax.add_patch(FancyBboxPatch((cx - 0.15, cy - 0.19), 0.3, 0.38,
                                boxstyle="round,pad=0,rounding_size=0.025", fc="#5b7fb0",
                                ec="#1b2631", lw=0.6, zorder=3))
    ax.add_patch(Rectangle((cx - 0.12, cy - 0.16), 0.24, 0.3, fc="white", ec="#1b2631", lw=0.5,
                           zorder=4))
    ax.add_patch(FancyBboxPatch((cx - 0.06, cy + 0.15), 0.12, 0.06,
                                boxstyle="round,pad=0,rounding_size=0.015", fc="#95a5a6",
                                ec="#1b2631", lw=0.5, zorder=5))
    for t in range(4):
        yy = cy + 0.08 - t * 0.065
        ax.add_patch(Rectangle((cx - 0.095, yy - 0.018), 0.036, 0.036, fc="white", ec="#1b2631",
                               lw=0.45, zorder=5))
        ax.plot([cx - 0.04, cx + 0.09], [yy, yy], color="#2c3e50", lw=0.7, zorder=5)
    ax.add_patch(Polygon([(cx + 0.17, cy - 0.12), (cx + 0.21, cy - 0.12), (cx + 0.21, cy + 0.15),
                          (cx + 0.17, cy + 0.15)], fc="#f4c542", ec="#1b2631", lw=0.5, zorder=5))
    ax.add_patch(Polygon([(cx + 0.17, cy - 0.12), (cx + 0.21, cy - 0.12), (cx + 0.19, cy - 0.18)],
                         fc="#e8d5b0", ec="#1b2631", lw=0.5, zorder=5))
    ax.add_patch(Rectangle((cx + 0.17, cy + 0.15), 0.04, 0.035, fc="#e74c3c", ec="#1b2631",
                           lw=0.5, zorder=5))


def _panel(ax, x0, y0, x1, y1, title, fc):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec="none", zorder=0))
    ax.text((x0 + x1) / 2, y1 - 0.05, title, ha="center", va="top", fontsize=8.8,
            weight="bold", zorder=5)


def fig_dataflow():
    d = flow()
    c = d["cats"]
    v = pd.read_csv(RES / "exp04_validation/per_model.csv")
    acc = v[v.category == "validated"]
    both = int((acc.in_primary_sample & acc.in_expanded_sample).sum())
    jk = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    jk = jk[(jk.population == "primary") & (jk.term == "same_root")
            & (jk.inference == "delete-one-root jackknife")].iloc[0]
    n_out = int(c.get("no_complete_run", 0) + c.get("repo_missing", 0) + c.get("schema_error", 0))
    W, H = FULL, 4.05
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_axis_off()
    bf = lambda n: r"$\mathbf{" + fmt(n).replace(",", "{,}") + "}$"  # noqa: E731

    # ---------------- section 1: data collection and validation
    TOP0 = 1.68
    ax.add_patch(Rectangle((0.03, TOP0), W - 0.06, H - TOP0 - 0.03, fc="none", ec="black", lw=0.7,
                           ls=(0, (3, 2)), zorder=0))
    ax.text(0.1, H - 0.08, "Data Collection", ha="left", va="top", fontsize=11,
            weight="bold", style="italic")
    # inputs (left)
    icons = [(_icon_monitor, 3.45, "Open LLM\nLeaderboard v1", 0.24),
             (_icon_tree, 2.76, "Hub model cards", 0.21),
             (_icon_clipboard, 2.1, "Research question", 0.24)]
    for f, cy, lab, dy in icons:
        f(ax, 0.62, cy)
        ax.text(0.62, cy - dy, lab, ha="center", va="top", fontsize=7.6, linespacing=1.05)
    ax.plot([0.14, 0.14], [2.1, 3.45], color="black", lw=0.7)
    for _, cy, _, _ in icons:
        _line_arrow(ax, [(0.14, cy), (0.33, cy)])
    # connector to lineage resolution and the plan
    XC = 1.62
    ax.plot([0.9, XC], [2.76, 2.76], color="black", lw=0.7)
    ax.plot([XC, XC], [2.1, 3.42], color="black", lw=0.7)
    _line_arrow(ax, [(XC, 3.42), (1.9, 3.42)])
    _line_arrow(ax, [(0.86, 2.1), (1.98, 2.1)])
    for y, t in ((3.08, "Resolve\nlineage roots"), (2.46, "Fix sample rules\nand analysis plan")):
        ax.text(XC, y, t, ha="center", va="center", fontsize=8, weight="bold", linespacing=1.05,
                bbox=dict(fc="white", ec="none", pad=1.2), zorder=6)

    # lineage resolution (automated)
    _panel(ax, 1.92, 2.86, 4.72, H - 0.07, "Lineage Resolution", "#fbf1ea")
    xs = [2.38, 3.32, 4.26]
    ax.plot([xs[0], xs[-1]], [3.67, 3.67], color="black", lw=0.6)
    cyl_top, cyl_h = 3.57, 0.5
    for x, lab, out in zip(xs, ("Leaderboard\ncontents", "Model-card\nlinks", "+ first config\nlink"),
                           (f"{bf(d['total'])} models", f"{bf(d['elig_p'])} primary",
                            f"{bf(d['elig_x'])} expanded")):
        ax.plot([x, x], [3.67, cyl_top + 0.045], color="black", lw=0.6)
        _cyl(ax, x, cyl_top, 0.82, cyl_h, lab)
        _down(ax, x, cyl_top - 0.74 * cyl_h, 3.04)
        ax.text(x, 2.94, out, ha="center", va="center", fontsize=7.8)
    # frozen samples
    ax.text(4.97, 3.36, "Sample,\nfreeze", ha="center", va="bottom", fontsize=8,
            weight="bold", linespacing=1.05)
    _line_arrow(ax, [(4.74, 3.3), (5.2, 3.3)])
    _panel(ax, 5.22, 2.86, W - 0.07, H - 0.07, "Frozen Samples", "#e3edf7")
    ax.text((5.22 + W - 0.07) / 2, H - 0.25, "≤ 40 per root, SHA-256", ha="center", va="top",
            fontsize=7.4, color=GREY, style="italic")
    xf = [5.68, 6.62]
    for x, lab, n in zip(xf, ("Primary", "Expanded"), (d["frozen_p"], d["frozen_x"])):
        _cyl(ax, x, cyl_top, 0.8, cyl_h, lab)
        _down(ax, x, cyl_top - 0.74 * cyl_h, 3.04)
        ax.text(x, 2.94, f"{bf(n)} models", ha="center", va="center", fontsize=7.8)
    ax.text((xf[0] + xf[1]) / 2, cyl_top - 0.2, "+", ha="center", va="center", fontsize=13,
            color=GREY)

    # download -> frozen models -> validation
    _stack(ax, 6.22, 2.1, 0.5, 0.36, f"{bf(d['union'])}\nmodels")
    _line_arrow(ax, [(6.45, 2.86), (6.45, 2.53)])
    ax.text(6.5, 2.7, "Download", ha="left", va="center", fontsize=7.8, weight="bold")
    # reconstruct / check cycle
    cx0, cy0, r = 5.93, 2.5, 0.14
    for (a, b, fc) in (((cx0 - 0.03, cy0 + r), (cx0 - 0.03, cy0 - r), "#efe3bf"),
                       ((cx0 + 0.03, cy0 - r), (cx0 + 0.03, cy0 + r), "#d3d9ea")):
        ax.add_patch(FancyArrowPatch(a, b, connectionstyle="arc3,rad=1.0",
                                     arrowstyle="simple,head_length=4,head_width=6,tail_width=2.6",
                                     fc=fc, ec="#6b6b6b", lw=0.5, zorder=5))
    ax.text(cx0, cy0 + 0.2, "Reconstruct", ha="center", va="bottom", fontsize=7.6, weight="bold")
    ax.text(cx0, cy0 - 0.2, "Check", ha="center", va="top", fontsize=7.6, weight="bold")
    _line_arrow(ax, [(6.22, 2.2), (5.62, 2.2)])

    # item-level validation
    _panel(ax, 3.52, 1.74, 5.6, 2.8, "Item-Level Validation", "#e7f0df")
    ax.text(4.56, 2.6, "14,042 items each", ha="center", va="top", fontsize=7.4,
            color=GREY, style="italic")
    xv = [4.05, 5.07]
    for x, lab, n in zip(xv, ("Primary", "Expanded"), (d["val_p"], d["val_x"])):
        _cyl(ax, x, 2.42, 0.78, 0.36, lab)
        _down(ax, x, 2.42 - 0.7 * 0.36, 1.92)
        ax.text(x, 1.83, f"{bf(n)} models", ha="center", va="center", fontsize=7.8)
    ax.text((xv[0] + xv[1]) / 2, 2.22, "+", ha="center", va="center", fontsize=13, color=GREY)
    # exclusions
    _line_arrow(ax, [(6.47, 2.08), (6.47, 2.02)])
    ax.add_patch(Rectangle((5.95, 1.73), 1.12, 0.29, fc="#f6f6f6", ec=GREY, lw=0.6,
                           ls=(0, (3, 2)), zorder=3))
    ax.text(6.51, 1.875, f"{n_out} excluded, logged,\nnone replaced", ha="center", va="center",
            fontsize=7.4, zorder=4, linespacing=1.05)
    # accepted
    _line_arrow(ax, [(3.52, 2.2), (3.13, 2.2)])
    _folder(ax, 2.64, 1.98, 0.42, 0.34)
    ax.text(2.85, 1.9, f"Total {bf(len(acc))} models\n({both} in both samples)", ha="center",
            va="top", fontsize=7.8, linespacing=1.1)
    # plan document
    _stack(ax, 1.98, 1.88, 0.46, 0.36, "Dated\nplan", size=7.4)

    # ---------------- section 2: pair-level analysis
    B1 = 1.55
    ax.add_patch(Rectangle((0.03, 0.03), W - 0.06, B1 - 0.03, fc="#f4f4f4", ec="black", lw=0.7,
                           ls=(0, (3, 2)), zorder=0))
    ax.text(0.1, B1 - 0.06, "Pair-Level Analysis", ha="left", va="top", fontsize=11,
            weight="bold", style="italic")
    ax.text(W - 0.1, B1 - 0.08, "solid: fixed before any pair outcome was computed;  dashed: "
            "partly added after the first results", ha="right", va="top", fontsize=7.4,
            color=GREY)
    # accepted models feed the analysis
    _line_arrow(ax, [(2.85, 1.62), (2.85, 1.6), (0.08, 1.6), (0.08, 1.03), (0.36, 1.03)])
    steps = [("Pair Outcome", f"{bf(d['pairs_p'])}\npairs",
              f"P(same wrong | both\nwrong); expanded\n{fmt(d['pairs_x'])} pairs"),
             ("Pair Model", r"$\mathbf{+13.3}$" "\npoints",
              "shared root, adjusted\nfor accuracies and\nrelease gap"),
             ("Inference", f"{jk.ci_low * 100:.1f}–{jk.ci_high * 100:.1f}\n95% CI",
              "model-level SEs\nplanned; root\njackknife added"),
             ("Robustness Checks", f"{d['n_prereg']} fixed\n+ post hoc",
              "S1, S2 planned;\nnull models and\nheterogeneity later")]
    bw, x0, step = 1.42, 0.36, 1.71
    for k, (title, count, note) in enumerate(steps):
        x = x0 + k * step
        later = k >= 2
        ax.add_patch(Rectangle((x, 0.9), bw, 0.27, fc="white", ec="black", lw=0.8,
                               ls=(0, (3, 2)) if later else "-", zorder=3))
        ax.text(x + bw / 2, 1.035, title, ha="center", va="center", fontsize=9, weight="bold",
                zorder=4)
        if k:
            _line_arrow(ax, [(x - step + bw, 1.035), (x, 1.035)])
        _line_arrow(ax, [(x + 0.33, 0.9), (x + 0.33, 0.7)])
        _stack(ax, x + 0.06, 0.18, 0.54, 0.48, count, size=7.8, ls="--" if later else "-")
        ax.text(x + 0.7, 0.44, note, ha="left", va="center", fontsize=7.2, color=GREY,
                linespacing=1.1)
    return save(fig, "fig_dataflow")


# ------------------------------------------------------------------ 1 agreement matrix
def fig_agreement(min_root=8):
    """Pairwise agreement on wrong answers, in the manner of Kim et al.'s Fig. 1."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_exp04_final import prepared
    d = prepared("primary")
    n, pop, acc = len(d["pop"]), d["pop"], d["acc"]
    M = np.full((n, n), np.nan)
    M[d["i"], d["j"]] = d["y"]; M[d["j"], d["i"]] = d["y"]
    lo, hi = np.nanpercentile(d["y"], [2, 98])
    cmap = plt.get_cmap("viridis").copy(); cmap.set_bad("white")
    fig, axes = plt.subplots(1, 2, figsize=(FULL, 3.2),
                             gridspec_kw=dict(width_ratios=[1, 1.0], wspace=0.5))
    # (a) every model, sorted by accuracy
    o = np.argsort(acc)
    ax = axes[0]
    im = ax.imshow(M[np.ix_(o, o)], cmap=cmap, vmin=lo, vmax=hi, interpolation="nearest")
    th = [0.3, 0.5, 0.6, 0.7]                 # tick where sorted accuracy reaches th
    t = [int(np.searchsorted(acc[o], v)) for v in th]
    ax.set_xticks(t, [f"{v:.1f}" for v in th]); ax.set_yticks(t, [f"{v:.1f}" for v in th])
    ax.set_xlabel("Model, sorted by MMLU accuracy (ticks: accuracy)")
    ax.set_ylabel("Model, sorted by MMLU accuracy")
    ax.set_title(f"(a) All {n} models of the primary sample", fontsize=9, weight="normal")
    # (b) the largest roots, grouped by root and sorted by accuracy within root
    vc = pop.root.value_counts()
    roots = list(vc[vc >= min_root].index)
    o2, edges = [], [0]
    for r in roots:
        k = np.where(pop.root.to_numpy() == r)[0]
        o2 += list(k[np.argsort(acc[k])]); edges.append(len(o2))
    o2 = np.array(o2)
    inb = np.isin(np.arange(n), o2)
    sub = inb[d["i"]] & inb[d["j"]]
    sr = (d["rid"][d["i"]] == d["rid"][d["j"]])
    import json
    (RES / "exp04_revision3").mkdir(exist_ok=True)
    (RES / "exp04_revision3/fig1_blocks.json").write_text(json.dumps({
        "roots": roots, "models": int(len(o2)),
        "mean_agreement_same_root": float(d["y"][sub & sr].mean()),
        "mean_agreement_different_root": float(d["y"][sub & ~sr].mean()),
        "pairs_same_root": int((sub & sr).sum()), "pairs_different_root": int((sub & ~sr).sum())},
        indent=1))
    ax2 = axes[1]
    ax2.imshow(M[np.ix_(o2, o2)], cmap=cmap, vmin=lo, vmax=hi, interpolation="nearest")
    for a, b in zip(edges[:-1], edges[1:]):
        ax2.add_patch(Rectangle((a - 0.5, a - 0.5), b - a, b - a, fill=False, ec="white", lw=0.9))
    mids = [(a + b - 1) / 2 for a, b in zip(edges[:-1], edges[1:])]
    names = [f"{root_label(r)} ({vc[r]})" for r in roots]
    ax2.set_yticks(mids, names, fontsize=8)
    ax2.set_xticks([])
    ax2.set_xlabel("Model, grouped by lineage root (same order)")
    ax2.set_title(f"(b) {len(o2)} models from the {len(roots)} roots with ≥ {min_root} models",
                  fontsize=9, weight="normal")
    for a in axes:
        a.grid(False)
        a.tick_params(length=2)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(True)
        for sp in a.spines.values():
            sp.set_edgecolor("#808080")
    fig.subplots_adjust(left=0.06, right=0.87, bottom=0.12, top=0.93)
    fig.canvas.draw()
    bb = ax2.get_position()
    cb = fig.colorbar(im, cax=fig.add_axes([bb.x1 + 0.018, bb.y0, 0.013, bb.height]))
    cb.set_label("P(same wrong option | both wrong)")
    cb.outline.set_edgecolor("#808080")
    return save(fig, "fig_agreement")


# ------------------------------------------------------------------ 6 gate audit
def fig_gate():
    files = [("primary_cap15", "Primary, cap 15"), ("primary_cap40", "Primary, cap 40 (chosen)"),
             ("primary_cap1000", "Primary, uncapped"), ("expanded_cap40", "Expanded, cap 40")]
    aud = {k: pd.read_csv(RES / f"pair_gate_audit/{k}.csv", keep_default_na=False)
           for k, _ in files}
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.55), gridspec_kw=dict(width_ratios=[1, 1.45, 1.3]))
    from matplotlib.transforms import blended_transform_factory

    def groups(ax, spans):                   # second tier of x labels: (first, last, text)
        tr = blended_transform_factory(ax.transData, ax.transAxes)
        for a, b, t in spans:
            ax.plot([a - 0.3, b + 0.3], [-0.17, -0.17], color=GREY, lw=0.6, transform=tr,
                    clip_on=False)
            ax.text((a + b) / 2, -0.2, t, ha="center", va="top", fontsize=8, transform=tr)
        for a, _, _ in spans[1:]:
            ax.axvline(a - 0.5, color="#d0d0d0", lw=0.6)
    off = np.linspace(-0.27, 0.27, len(files))
    colors = [LBLUE, BLUE, GREY, ORANGE]
    marks = ["o", "D", "s", "^"]

    def pts(ax, rows, xs, k, label=None):
        r = rows
        ax.errorbar(xs + off[k], 100 * r.rate, yerr=[100 * (r.rate - r.ci_low),
                    100 * (r.ci_high - r.rate)], fmt=marks[k], ms=3, color=colors[k],
                    lw=0.7, label=label, mfc="white" if k != 1 else colors[k])

    # (a) null
    ax = axes[0]
    terms = ["same_root", "gap0", "gap1_2"]
    for k, (f, lab) in enumerate(files):
        a = aud[f]
        r = a[a.truth == "null"].set_index("term").loc[terms]
        pts(ax, r, np.arange(3), k, lab)
    ax.axhline(10, color=RED, ls=(0, (3, 2)), lw=0.7); ax.axhline(5, color=LGREY, lw=0.5)
    ax.text(2.45, 10.3, "10% criterion", color=RED, fontsize=7.5, ha="right", va="bottom")
    ax.set_xticks(range(3), ["root", "0 mo", "1–2 mo"])
    groups(ax, [(0, 2, "coefficient tested")])
    ax.set_ylabel("Rejection rate (%)"); ax.set_ylim(0, 16)
    ax.set_title("(a) Null")
    # (b) leakage
    ax = axes[1]
    labs, xs = [], 0
    for lam in ("0.03", "0.05", "0.1"):
        for k, (f, _) in enumerate(files):
            a = aud[f]
            pts(ax, a[(a.truth == f"era_{lam}") & (a.term == "same_root")], np.array([xs]), k)
        labs.append(f"{float(lam):.2f}"); xs += 1
    for lam in ("0.03", "0.05", "0.1"):
        for k, (f, _) in enumerate(files):
            a = aud[f]
            r = a[(a.truth == f"lineage_{lam}") & a.term.isin(["gap0", "gap1_2"])]
            pts(ax, r.loc[[r.rate.idxmax()]], np.array([xs]), k)
        labs.append(f"{float(lam):.2f}"); xs += 1
    ax.axhline(10, color=RED, ls=(0, (3, 2)), lw=0.7)
    a = aud["primary_cap40"]
    worst = a[(a.truth == "era_0.1") & (a.term == "same_root")].iloc[0]
    ax.annotate(f"{100 * worst.rate:.1f}% > 10%", (2 + off[1], 100 * worst.rate),
                (0.6, 15.2), fontsize=7.5, color=RED, ha="center", arrowprops=dict(arrowstyle="-", color=RED,
                                                                     lw=0.6))
    ax.set_xticks(range(xs), labs)
    groups(ax, [(0, 2, "root coef. under $λ_E$"), (3, 5, "month coef. under $λ_L$")])
    ax.set_ylim(0, 17); ax.set_title("(b) Leakage")
    # (c) power
    ax = axes[2]
    labs, xs = [], 0
    for term, truth, lab in (("same_root", "lineage", "root"), ("gap0", "era", "0 mo")):
        for lam in ("0.03", "0.05"):
            for k, (f, _) in enumerate(files):
                a = aud[f]
                pts(ax, a[(a.truth == f"{truth}_{lam}") & (a.term == term)], np.array([xs]), k)
            labs.append(f"{float(lam):.2f}"); xs += 1
    ax.axhline(80, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.set_xticks(range(xs), labs)
    groups(ax, [(0, 1, "root coef. under $λ_L$"), (2, 3, "0-mo coef. under $λ_E$")])
    ax.text(3.45, 78, "80% criterion", color=RED, fontsize=7.5, ha="right", va="top")
    ax.set_ylim(0, 105); ax.set_title("(c) Power")
    for ax in axes:
        ax.set_xlim(-0.5, len(ax.get_xticks()) - 0.5)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=4,
               frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(pad=0.3, rect=(0, 0.06, 1, 0.92))
    return save(fig, "fig_gate_audit")


# ------------------------------------------------------------------ 7 forest
PRETTY = {"": "baseline", "strict": "strict root", "S1position": "S1 option-distribution",
          "S2acc0.3": "S2 acc ≥ 0.30", "S1position_S2acc0.3": "S1 + S2",
          "strict_S1position_S2acc0.3": "strict + S1 + S2"}


def nice(a: str) -> str:
    pop, _, rest = a.partition("_")
    return f"{pop.capitalize()}: {PRETTY[rest]}"


def fig_forest():
    pre = pd.read_csv(RES / "exp04_final/prereg_12.csv")
    order = list(dict.fromkeys(pre.analysis))
    fig, axes = plt.subplots(1, 4, figsize=(FULL, 2.75), sharey=True,
                             gridspec_kw=dict(width_ratios=[1, 0.95, 0.85, 1.05]))
    tcol, axes = axes[3], axes[:3]
    yy = np.arange(len(order))[::-1] + np.array([0.6 if a.startswith("primary") else 0
                                                 for a in order])
    ZOOM = (-0.04, 0.03)                              # range magnified in panel (c)
    for ax, t, title, c in zip(axes, ("same_root", "gap0", "gap0"),
                               ("(a) Shared root", "(b) Same month", "(c) Same month, magnified"),
                               (BLUE, ORANGE, ORANGE)):
        d = pre[pre.term == t].set_index("analysis").loc[order]
        for k, a in enumerate(order):
            base = a in ("primary", "expanded")
            ax.errorbar(d.estimate[a], yy[k], xerr=[[d.estimate[a] - d.ci_low[a]],
                        [d.ci_high[a] - d.estimate[a]]], fmt="D" if base else "o",
                        ms=4.2 if base else 3.4, color=c, mfc=c if base else "white", lw=0.9)
        zero(ax)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Coefficient")
    for ax in axes[:2]:                               # common scale: widths comparable
        ax.set_xlim(-0.04, 0.16)
        ax.set_xticks([0, 0.05, 0.1, 0.15])
    axes[1].add_patch(Rectangle((ZOOM[0], yy[-1] - 0.5), ZOOM[1] - ZOOM[0], yy[0] - yy[-1] + 1.2,
                                fill=False, ec=GREY, lw=0.6, ls=(0, (2, 2)), zorder=3))
    axes[2].set_xlim(*ZOOM); axes[2].set_xticks([-0.03, 0, 0.03], ["−0.03", "0", "0.03"])
    axes[0].set_yticks(yy, [PRETTY[a.partition("_")[2]] for a in order])
    for ax in axes:
        ax.axhspan(yy[5] - 0.45, yy[0] + 0.45, color="#f3f6fa", zorder=-1)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].tick_params(axis="y", labelsize=8.5)
    axes[0].text(0.004, yy[0] + 0.5, "PRIMARY", fontsize=8, weight="bold", color=GREY,
                 va="center")
    axes[0].text(0.004, yy[6] + 0.5, "EXPANDED", fontsize=8, weight="bold", color=GREY,
                 va="center")
    axes[0].set_ylim(yy[-1] - 0.6, yy[0] + 0.9)
    # numeric column, points [95% CI], as in clinical forest plots
    tcol.set_axis_off()
    tcol.axhspan(yy[5] - 0.45, yy[0] + 0.45, color="#f3f6fa", zorder=-1)
    tcol.set_xlim(0, 1)
    for x_, t, c in ((0.03, "same_root", BLUE), (0.53, "gap0", ORANGE)):
        dd = pre[pre.term == t].set_index("analysis").loc[order]
        tcol.text(x_ + 0.21, yy[0] + 0.85, "Shared root" if t == "same_root" else "Same month",
                  ha="center", va="bottom", fontsize=7.6, weight="bold", color=c)
        for k, a in enumerate(order):
            tcol.text(x_ + 0.21, yy[k], f"{dd.estimate[a] * 100:+.1f} "
                      f"[{dd.ci_low[a] * 100:.1f}, {dd.ci_high[a] * 100:.1f}]",
                      ha="center", va="center", fontsize=6.4, color=INK,
                      weight="bold" if a in ("primary", "expanded") else "normal")
    tcol.text(0.5, yy[-1] - 0.75, "points [95% CI]", ha="center", va="top", fontsize=7,
              color=GREY)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="D", color=GREY, ls="", ms=4.2, label="primary specification"),
         Line2D([], [], marker="o", color=GREY, mfc="white", ls="", ms=3.4,
                label="sensitivity analysis"),
         Line2D([], [], color=GREY, lw=0.9, label="95% CI, model-level dyadic SEs")]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=8,
               bbox_to_anchor=(0.56, 1.0))
    fig.tight_layout(pad=0.3, w_pad=1.0, rect=(0, 0, 1, 0.92))
    return save(fig, "exp04_forest")


# ------------------------------------------------------------------ 8 raw vs adjusted
GAPS = [("same_root", "shared root"), ("gap0", "0 months"), ("gap1_2", "1–2 months"),
        ("gap3_5", "3–5 months"), ("gap6_11", "6–11 months")]


def fig_rawadj():
    from matplotlib.colors import LogNorm
    from scipy.stats import pearsonr
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_exp04_final import prepared
    d = prepared("primary")
    r = pd.read_csv(RES / "exp04_final/raw_vs_adjusted.csv")
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.55),
                             gridspec_kw=dict(width_ratios=[1.35, 1, 1]))
    # (a) every primary pair: agreement against the pair's mean accuracy
    ax = axes[0]
    macc = (d["acc"][d["i"]] + d["acc"][d["j"]]) / 2
    sr = d["rid"][d["i"]] == d["rid"][d["j"]]
    hb = ax.hexbin(macc[~sr], d["y"][~sr], gridsize=(46, 30), extent=(0.2, 0.8, 0, 1),
                   cmap="Greys", norm=LogNorm(), mincnt=1, lw=0.1, edgecolors="face")
    ax.scatter(macc[sr], d["y"][sr], s=2.2, color=BLUE, alpha=0.45, lw=0, zorder=3)
    edges = np.arange(0.2, 0.825, 0.025)
    for mask, c, lab in ((~sr, ORANGE, "different roots"), (sr, BLUE, "same root")):
        k = np.digitize(macc[mask], edges)
        mm = [(edges[t - 1] + 0.0125, d["y"][mask][k == t].mean()) for t in np.unique(k)
              if (k == t).sum() >= 30]
        ax.plot(*zip(*mm), color=c, lw=1.4, zorder=4, label=f"{lab}: binned mean")
    rd, rs = pearsonr(macc[~sr], d["y"][~sr]).statistic, pearsonr(macc[sr], d["y"][sr]).statistic
    ax.text(0.97, 0.05, f"different roots: r = {rd:.2f}, n = {(~sr).sum():,}\n"
            f"same root: r = {rs:.2f}, n = {sr.sum():,}", transform=ax.transAxes, ha="right",
            va="bottom", fontsize=6.8, linespacing=1.2,
            bbox=dict(fc="white", ec=LGREY, lw=0.5, boxstyle="round,pad=0.25"), zorder=6)
    ax.set_xlim(0.2, 0.8); ax.set_ylim(0, 1)
    ax.set_xlabel("Mean accuracy of the two models")
    ax.set_ylabel("P(same wrong | both wrong)")
    ax.set_title("(a) All primary pairs")
    ax.legend(frameon=True, framealpha=0.9, edgecolor=LGREY, loc="upper left", fontsize=6.8,
              handlelength=1.2).get_frame().set_linewidth(0.5)
    cb = fig.colorbar(hb, ax=ax, fraction=0.05, pad=0.02)
    cb.set_label("Different-root pairs per cell", fontsize=6.8); cb.ax.tick_params(labelsize=6)
    # (b, c) raw -> adjusted coefficients as dumbbells
    y = np.arange(len(GAPS))[::-1]
    for ax, pop, title in ((axes[1], "primary", "(b) Primary"), (axes[2], "expanded", "(c) Expanded")):
        raw = r[(r.population == pop) & (r.model == "raw (no accuracy terms)")].set_index("term")
        adj = r[(r.population == pop) & (r.model == "adjusted (pre-registered)")].set_index("term")
        for k, (t, _) in enumerate(GAPS):
            x0, x1 = raw.estimate[t], adj.estimate[t]
            ax.plot([raw.ci_low[t], raw.ci_high[t]], [y[k] + 0.13] * 2, color=LGREY, lw=0.8)
            ax.plot([adj.ci_low[t], adj.ci_high[t]], [y[k] - 0.13] * 2, color=LBLUE, lw=0.8)
            ax.annotate("", (x1, y[k]), (x0, y[k]), arrowprops=dict(
                arrowstyle="-|>", color=GREY, lw=0.7, mutation_scale=6, shrinkA=3, shrinkB=3))
            ax.plot(x0, y[k], "o", ms=4, mfc="white", mec=GREY, mew=0.9, zorder=4,
                    label="raw (no accuracy terms)" if k == 0 else None)
            ax.plot(x1, y[k], "o", ms=4, color=BLUE, zorder=4,
                    label="adjusted (pre-specified)" if k == 0 else None)
            if t == "same_root":
                ax.text((x0 + x1) / 2, y[k] + 0.3, f"{x0 * 100:.1f} → {x1 * 100:.1f}",
                        ha="center", va="bottom", fontsize=7, color=INK)
        zero(ax)
        ax.axhline(3.5, color=LGREY, lw=0.5)
        ax.set_xlim(-0.03, 0.33)
        ax.set_ylim(-0.6, 4.75)
        ax.set_xlabel("Coefficient (95% CI)")
        ax.set_title(title)
        ax.set_yticks(y, [g for _, g in GAPS] if pop == "primary" else [])
    axes[2].legend(frameon=False, loc="center right", fontsize=6.8, handlelength=1)
    fig.tight_layout(pad=0.3, w_pad=1.6)
    return save(fig, "fig_raw_adjusted")


# ------------------------------------------------------------------ 9 inference
def fig_inference():
    inf = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    kinds = [("model-dyadic (pre-registered)", "model-level dyadic (pre-specified)", BLUE, "o"),
             ("root-dyadic", "root-level dyadic", GREY, "s"),
             ("delete-one-root jackknife", "delete-one-root jackknife", ORANGE, "^")]
    pops = list(SAMPLES)
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.55), sharey=True)
    y = np.arange(len(pops))[::-1]
    for ax, t, title in zip(axes, ("same_root", "gap0"),
                            ("(a) Shared root", "(b) Same month")):
        base = inf[(inf.term == t) & (inf.inference == kinds[0][0])].set_index("population")
        for k, (kind, lab, c, mk) in enumerate(kinds):
            d = inf[(inf.term == t) & (inf.inference == kind)].set_index("population").loc[pops]
            ax.errorbar(d.estimate, y + (0.22 - 0.22 * k), xerr=[d.estimate - d.ci_low,
                        d.ci_high - d.estimate], fmt=mk, ms=2.8, color=c, lw=0.8, label=lab,
                        mfc="white" if k else c)
            if k == 2:                                # width relative to the model-level CI
                ratio = (d.ci_high - d.ci_low) / (base.ci_high - base.ci_low).loc[pops]
                for yy, rr in zip(y, ratio):
                    ax.text(0.163 if t == "same_root" else 0.034, yy - 0.22, f"×{rr:.2f}",
                            fontsize=6.6, color=c, va="center", ha="left")
        zero(ax)
        ax.set_title(title); ax.set_xlabel("Coefficient (95% CI)")
    axes[0].set_xlim(0.06, 0.19)
    axes[1].set_xlim(-0.05, 0.055)
    axes[0].set_yticks(y, [SAMPLES[p] for p in pops])
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=7.2, bbox_to_anchor=(0.5, 1.0), handletextpad=0.2,
               columnspacing=0.8)
    fig.text(0.99, 0.01, "×: jackknife CI width relative to model-level", ha="right",
             va="bottom", fontsize=6.6, color=ORANGE)
    fig.tight_layout(pad=0.3, rect=(0, 0.04, 1, 0.84), w_pad=0.5)
    return save(fig, "fig_inference")


# ------------------------------------------------------------------ 10 outcomes
def fig_outcomes():
    o = pd.read_csv(RES / "exp04_final/outcome_audit.csv")
    variants = [("primary outcome, OLS (pre-registered)", "Pre-specified"),
                ("WLS, weight = jointly-wrong items", "WLS, jointly wrong"),
                ("agreement minus position-based chance (exploratory)",
                 "Minus option chance"),
                ("phi of error indicators (secondary)", "Phi of errors")]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.4), sharey=True)
    y = np.arange(len(variants))[::-1].astype(float)
    y[-1] -= 0.35                                  # separate the different-scale outcome
    for ax, t, title in zip(axes, ("same_root", "gap0"),
                            ("(a) Shared root", "(b) Same month")):
        for pop, dy, c, mfc in (("primary", 0.12, BLUE, BLUE), ("expanded", -0.12, GREY, "white")):
            d = o[(o.population == pop) & (o.term == t)].set_index("variant").loc[
                [v for v, _ in variants]]
            ax.errorbar(d.estimate, y + dy, xerr=[d.estimate - d.ci_low, d.ci_high - d.estimate],
                        fmt="o", ms=2.9, color=c, mfc=mfc, lw=0.8, label=pop.capitalize())
        zero(ax)
        ax.axhline((y[-1] + y[-2]) / 2, color=LGREY, lw=0.5)
        ax.set_title(title); ax.set_xlabel("Coefficient")
    axes[0].set_xlim(0, 0.2)
    axes[0].set_yticks(y, [v for _, v in variants])
    axes[0].text(0.198, y[-1] + 0.4, "phi: correlation scale", fontsize=7.5,
                 color=GREY, ha="right")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=7.5, bbox_to_anchor=(0.6, 1.0))
    fig.tight_layout(pad=0.3, w_pad=0.5, rect=(0, 0, 1, 0.91))
    return save(fig, "fig_outcomes")


# ------------------------------------------------------------------ 11 item nulls
def fig_itemnull():
    n = pd.read_csv(RES / "exp04_item_null/item_null.csv")
    outs = [("pre-registered: same-wrong agreement", "Observed agreement"),
            ("N1a: minus item distractor null (all models)", "N1a: minus distractor null"),
            ("N1b: minus item distractor null (roots weighted equally)",
             "N1b: same, roots equal")]
    pops = list(SAMPLES)
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.2),
                             gridspec_kw=dict(width_ratios=[1.15, 1.25, 1.0]))
    shades = [GREY, BLUE, LBLUE]
    x = np.arange(len(pops))
    ax = axes[0]
    for k, (o, lab) in enumerate(outs):
        m = n[(n.outcome == o) & (n.term == "same_root")].set_index("population") \
            .outcome_mean.loc[pops]
        ax.bar(x + (k - 1) * 0.26, m, 0.25, color=shades[k], label=lab)
    zero(ax, horizontal=True)
    ax.set_xticks(x, [SAMPLES[p].replace(", ", "\n") for p in pops])
    ax.set_ylabel("Mean outcome over pairs")
    ax.set_title("(a) Level: depends on the null")
    ax.set_ylim(-0.02, 0.85)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=1)
    ax = axes[1]
    for k, (o, lab) in enumerate(outs):
        d = n[(n.outcome == o) & (n.term == "same_root")].set_index("population").loc[pops]
        ax.errorbar(x + (k - 1) * 0.22, d.estimate, yerr=Z * d.se_jackknife, fmt="o", ms=3,
                    color=shades[k], lw=0.8, mfc=shades[k] if k != 2 else "white")
    ax.set_ylim(0, 0.17)
    ax.set_xticks(x, [SAMPLES[p].replace(", ", "\n") for p in pops])
    ax.set_ylabel("Shared-root coefficient")
    ax.set_title("(b) Lineage contrast: unchanged")
    ax = axes[2]
    o2 = "N2: excess co-failure over Rasch null (per item)"
    for k, (t, lab, c) in enumerate((("same_root", "shared root", BLUE),
                                     ("gap0", "same month", ORANGE))):
        d = n[(n.outcome == o2) & (n.term == t)].set_index("population").loc[pops]
        ax.errorbar(x + (k - 0.5) * 0.25, d.estimate, yerr=Z * d.se_jackknife, fmt="o", ms=3,
                    color=c, lw=0.8, label=lab)
    zero(ax, horizontal=True)
    ax.set_xticks(x, [SAMPLES[p].replace(", ", "\n") for p in pops])
    ax.set_ylabel("Excess co-failure per item")
    ax.set_title("(c) N2: co-failure vs Rasch")
    ax.legend(frameon=False, fontsize=7.5)
    for a in axes:
        a.tick_params(axis="x", labelsize=5.8)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    return save(fig, "fig_item_null")


# ------------------------------------------------------------------ 12 size/architecture
def _parse(s: str) -> tuple[float, float]:
    est, se = s.replace("(", "").replace(")", "").split()
    return float(est), float(se)


def fig_controls():
    e = pd.read_csv(RES / "exp04_final/exploratory_E1_E2.csv").set_index("population")
    pops = list(SAMPLES)
    cols = [("same_root (model-cl)", "shared root (pre-specified terms + S1)", BLUE, "o", BLUE),
            ("same_root +size/arch", "shared root (+ size, architecture)", BLUE, "o", "white"),
            ("same_arch", "same architecture", GREY, "s", GREY)]
    fig, ax = plt.subplots(figsize=(COL, 2.3))
    y = np.arange(len(pops))[::-1]
    for k, (col, lab, c, mk, mfc) in enumerate(cols):
        v = np.array([_parse(e.loc[p, col]) for p in pops])
        ax.errorbar(v[:, 0], y + 0.22 - 0.22 * k, xerr=Z * v[:, 1], fmt=mk, ms=3, color=c,
                    mfc=mfc, lw=0.8, label=lab)
    zero(ax)
    ax.set_yticks(y, [SAMPLES[p] for p in pops])
    ax.set_xlabel("Coefficient (95% CI, model-level dyadic)")
    fig.legend(*ax.get_legend_handles_labels(), frameon=False, fontsize=7.5,
               loc="upper center", ncol=1, bbox_to_anchor=(0.55, 1.0), handletextpad=0.2)
    ax.set_xlim(-0.01, 0.16)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.80))
    return save(fig, "fig_controls")


# ------------------------------------------------------------------ 13 lineage x month map
def fig_heatmap(top: int = 10):
    pop = population("primary")
    months = pd.period_range(pop.created_month.min(), pop.created_month.max(), freq="M")
    vc = pop.root.value_counts()
    keep = list(vc.index[:top])
    lab = pop.root.where(pop.root.isin(keep), "other")
    tab = pd.crosstab(lab, pd.PeriodIndex(pop.created_month, freq="M")) \
        .reindex(columns=months, fill_value=0)
    n_other_roots = pop.root.nunique() - len(keep)
    tab = tab.loc[keep + ["other"]]
    fig = plt.figure(figsize=(FULL, 3.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.6, 2.5], width_ratios=[30, 2.6, 0.45],
                          hspace=0.06, wspace=0.03, left=0.2, right=0.935, top=0.97, bottom=0.15)
    ax = fig.add_subplot(gs[1, 0])
    axt = fig.add_subplot(gs[0, 0], sharex=ax)
    axr = fig.add_subplot(gs[1, 1], sharey=ax)
    cax = fig.add_subplot(gs[1, 2])
    data = tab.to_numpy().astype(float)
    masked = np.ma.masked_equal(data, 0)
    from matplotlib.colors import LinearSegmentedColormap, LogNorm
    cmap = LinearSegmentedColormap.from_list("steel", ["#eef3f9", "#b5c7df", BLUE, "#3f5f8f"])
    cmap.set_bad("white")
    im = ax.imshow(masked, aspect="auto", cmap=cmap, norm=LogNorm(1, data.max()),
                   interpolation="none")
    for (r, c), v in np.ndenumerate(data):
        if v:
            ax.text(c, r, int(v), ha="center", va="center", fontsize=7,
                    color="white" if v > data.max() ** 0.6 else "black")
    ax.set_xticks(range(len(months)), [m.strftime("%b %y") if m.month in (1, 4, 7, 10)
                                       else "" for m in months], fontsize=8.0)
    names = [f"{root_label(k)} (n={vc[k]})" for k in keep]
    names.append(f"{n_other_roots} other roots (n={int(data[-1].sum())})")
    ax.set_yticks(range(len(names)), names, fontsize=8.0)
    ax.set_xticks(np.arange(-0.5, len(months)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(names)), minor=True)
    ax.grid(False)
    ax.grid(which="minor", color="#e6e6e6", lw=0.3)
    ax.tick_params(which="minor", length=0)
    ax.axhline(len(keep) - 0.5, color=GREY, lw=0.6)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(True)
    ax.set_xlabel("Hub upload month")
    # marginals: models per month (stacked: ten largest roots / others), models per row
    per_m = data.sum(0)
    big = data[:-1].sum(0)
    axt.bar(range(len(months)), big, color=BLUE, width=0.8, label="ten largest roots")
    axt.bar(range(len(months)), data[-1], bottom=big, color=LBLUE, width=0.8,
            label=f"{n_other_roots} other roots")
    axt.set_ylim(0, per_m.max() * 1.15)
    axt.set_ylabel("Models", fontsize=7.5)
    axt.tick_params(axis="x", labelbottom=False, length=0)
    axt.tick_params(axis="y", labelsize=7)
    axt.legend(frameon=False, fontsize=7.2, loc="upper left", ncol=2, handlelength=1)
    axr.barh(range(len(names)), data.sum(1), color=[BLUE] * len(keep) + [LBLUE], height=0.7)
    axr.tick_params(axis="y", labelleft=False, length=0)
    axr.tick_params(axis="x", labelsize=7)
    axr.set_xscale("log"); axr.set_xlim(3, 800)
    axr.set_xticks([10, 100], ["10", "100"])
    from matplotlib.ticker import NullLocator
    axr.xaxis.set_minor_locator(NullLocator())
    axr.grid(axis="y", visible=False); axr.grid(axis="x", visible=True)
    axr.set_xlabel("Models", fontsize=7.5)
    cb = fig.colorbar(im, cax=cax)
    ticks = [t for t in (1, 2, 5, 10, 20, 50) if t <= data.max()]
    cb.set_ticks(ticks, labels=[str(t) for t in ticks]); cb.minorticks_off()
    cb.set_label("Models per cell (log scale)", fontsize=7.5); cb.ax.tick_params(labelsize=6.5)
    return save(fig, "fig_lineage_month_map")


# ------------------------------------------------------------------ 14 agreement by gap
def _half_violin(ax, x, vals, side, color, width=0.4):
    from scipy.stats import gaussian_kde
    v = vals if len(vals) <= 20000 else \
        np.random.default_rng(0).choice(vals, 20000, replace=False)
    grid = np.linspace(0, 1, 241)
    dens = gaussian_kde(v, bw_method="scott")(grid)
    dens = dens / dens.max() * width
    keep = dens > width * 0.01
    g, dd = grid[keep], dens[keep]
    ax.fill_betweenx(g, x, x + side * dd, color=color, alpha=0.35, lw=0)
    ax.plot(x + side * dd, g, color=color, lw=0.6)
    q1, q3 = np.percentile(vals, [25, 75])
    ax.plot([x + side * 0.05] * 2, [q1, q3], color=color, lw=2.2, solid_capstyle="butt")


def fig_gap():
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_exp04_final import prepared
    from lineage_era.ollb.pair_gate import month_index
    d = prepared("primary")
    mi = month_index(d["pop"].created_month)
    gap = np.abs(mi[d["i"]] - mi[d["j"]])
    same = d["rid"][d["i"]] == d["rid"][d["j"]]
    b = np.digitize(gap, [1, 3, 6, 12])
    lab = ["0", "1–2", "3–5", "6–11", "12+"]
    fig, ax = plt.subplots(figsize=(COL, 2.75))
    MIN_PAIRS = 20   # bins with fewer pairs are not plotted (1 same-root pair at 12+)
    for flag, name, c, mk, side in [(True, "same lineage root", BLUE, "D", 1),
                                    (False, "different roots", ORANGE, "o", -1)]:
        cnt = np.array([int(((b == k) & (same == flag)).sum()) for k in range(5)])
        m = np.full(5, np.nan)
        for k in range(5):
            if cnt[k] >= MIN_PAIRS:
                vals = d["y"][(b == k) & (same == flag)]
                _half_violin(ax, k, vals, side, c)
                m[k] = vals.mean()
                ax.text(k + side * 0.2, 1.075 if flag else 0.015, f"{cnt[k]:,}", ha="center",
                        va="top" if flag else "bottom", fontsize=6.8, color=c)
        ax.plot(np.arange(5) + side * 0.05, m, marker=mk, ms=3.2, color=c, lw=0.9,
                mec="white", mew=0.4, zorder=5, label=name)
    ax.axhline(1 / 3, color=GREY, lw=0.7, ls=(0, (4, 3)), zorder=0)
    ax.set_xticks(range(5), lab)
    ax.set_xlim(-0.55, 4.55)
    ax.set_xlabel("Release-month gap between the two models")
    ax.set_ylabel("P(same wrong | both wrong)")
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.axhline(1.0, color="#d0d0d0", lw=0.5, zorder=0)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    h, l = ax.get_legend_handles_labels()
    h += [Patch(fc=LGREY, alpha=0.6, lw=0), Line2D([], [], color=GREY, lw=2.2),
          Line2D([], [], color=GREY, lw=0.7, ls=(0, (4, 3)))]
    l += ["density across pairs", "interquartile range", "1/3: uniform over three wrong options"]
    fig.legend(h, l, loc="upper center", ncol=2, frameon=False, fontsize=7.2,
               bbox_to_anchor=(0.54, 1.0), handlelength=1.5, columnspacing=0.8)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.8))
    return save(fig, "exp04_agreement_by_gap")


# ------------------------------------------------------------------ dose-response
def fig_dose():
    rv = pd.read_csv(RES / "exp04_revision2/revision2.csv")
    pre = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    base = pre[(pre.population == "primary") & (pre.term == "same_root")
               & (pre.inference == "delete-one-root jackknife")].iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.3), sharey=True,
                             gridspec_kw=dict(width_ratios=[1, 1]))
    for ax, analysis, terms, labels, title in (
            (axes[0], "lineage dose-response: tree distance",
             ["distance 1", "distance 2", "distance 3+"], ["1", "2", "3+"],
             "(a) Tree distance"),
            (axes[1], "lineage dose-response: relation type",
             ["ancestor-descendant", "siblings", "more distant"],
             ["direct\nline", "siblings", "more\ndistant"], "(b) Relation")):
        d = rv[(rv.population == "primary") & (rv.analysis == analysis)].set_index("term").loc[terms]
        x = np.arange(len(terms))
        ax.errorbar(x, d.estimate, yerr=[d.estimate - d.ci95_low, d.ci95_high - d.estimate],
                    fmt="o", ms=4, color=BLUE, lw=1)
        for k, n in enumerate(d.pairs):
            ax.annotate(f"{int(n):,}", (x[k], d.ci95_high.iloc[k]), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=7.5, color=GREY)
        ax.axhspan(base.ci_low, base.ci_high, color=LBLUE, alpha=0.35, lw=0)
        ax.axhline(base.estimate, color=BLUE, lw=0.6, ls=(0, (3, 2)))
        ax.set_xticks(x, labels)
        ax.set_xlim(-0.5, len(terms) - 0.5)
        ax.set_title(title)
    axes[0].set_ylabel("Coefficient vs different roots")
    axes[0].set_ylim(0.08, 0.235)
    fig.text(0.55, 0.995, "in the plan, first run after review (supporting evidence)",
             ha="center", va="top", fontsize=7.5, color=GREY, style="italic")
    fig.tight_layout(pad=0.3, w_pad=0.6, rect=(0, 0, 1, 0.94))
    return save(fig, "fig_dose")


# ------------------------------------------------------------------ timing measures
def fig_timing():
    raw = pd.read_csv(RES / "exp04_final/raw_vs_adjusted.csv")
    rv = pd.read_csv(RES / "exp04_revision2/revision2.csv")
    bins = ["gap0", "gap1_2", "gap3_5", "gap6_11"]
    lab = ["0", "1–2", "3–5", "6–11"]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.35), sharey=True)
    x = np.arange(len(bins))
    for ax, pop, title in ((axes[0], "primary", "(a) Primary"), (axes[1], "expanded", "(b) Expanded")):
        u = raw[(raw.population == pop) & (raw.model == "adjusted (pre-registered)")] \
            .set_index("term").loc[bins]
        r = rv[(rv.population == pop) & (rv.analysis ==
               "root release month in place of upload month")].set_index("term").loc[bins]
        ax.errorbar(x - 0.1, u.estimate, yerr=[u.estimate - u.ci_low, u.ci_high - u.estimate],
                    fmt="o", ms=3.5, color=ORANGE, lw=1, label="upload month")
        ax.errorbar(x + 0.1, r.estimate, yerr=[r.estimate - r.ci95_low, r.ci95_high - r.estimate],
                    fmt="s", ms=3.5, color=GREY, mfc="white", lw=1, label="root release month")
        zero(ax, horizontal=True)
        ax.set_xticks(x, lab)
        ax.set_xlabel("Gap (months; vs 12+)")
        ax.set_title(title)
    axes[0].set_ylabel("Coefficient")
    axes[0].set_ylim(-0.045, 0.045)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=8, bbox_to_anchor=(0.55, 1.0), handletextpad=0.2,
               columnspacing=0.8)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.9), w_pad=0.6)
    return save(fig, "fig_timing")


# ------------------------------------------------------------------ item nulls (main text)
def fig_itemnull_main():
    """Shared-root coefficient under the item-level nulls (levels: supplement)."""
    n = pd.read_csv(RES / "exp04_item_null/item_null.csv")
    outs = [("pre-registered: same-wrong agreement", "observed", GREY, "o"),
            ("N1a: minus item distractor null (all models)", "N1a", BLUE, "s"),
            ("N1b: minus item distractor null (roots weighted equally)", "N1b", LBLUE, "D")]
    pops = list(SAMPLES)
    x = np.arange(len(pops))
    fig, ax = plt.subplots(figsize=(COL, 2.2))
    for k, (o, lab, c, mk) in enumerate(outs):
        d = n[(n.outcome == o) & (n.term == "same_root")].set_index("population").loc[pops]
        ax.errorbar(x + (k - 1) * 0.18, d.estimate, yerr=Z * d.se_jackknife, fmt=mk,
                    ms=3.5, color=c, lw=1, mfc=c if k < 2 else "white", label=lab)
    ax.set_ylim(0, 0.17); ax.set_ylabel("Shared-root coefficient")
    zero(ax, horizontal=True)
    ax.set_xticks(x, ["Primary", "Primary, S2", "Expanded", "Expanded, S2"])
    ax.legend(frameon=False, loc="lower center", ncol=3, fontsize=8, handletextpad=0.2)
    fig.tight_layout(pad=0.3)
    return save(fig, "fig_item_null_main")


# ------------------------------------------------------------------ heterogeneity
def fig_heterogeneity():
    h = pd.read_csv(RES / "exp04_heterogeneity/heterogeneity.csv")
    sub = pd.read_csv(RES / "exp04_heterogeneity/per_subject.csv").sort_values("same_root")
    base = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    base = base[(base.population == "primary") & (base.term == "same_root")
                & (base.inference == "delete-one-root jackknife")].iloc[0]
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.6),
                             gridspec_kw=dict(width_ratios=[1.25, 0.8, 1.35]))
    # (a) per root
    ax = axes[0]
    r = h[h.analysis == "per root"].reset_index(drop=True)
    y = np.arange(len(r))[::-1]
    ax.errorbar(r.estimate, y, xerr=[r.estimate - r.ci95_low, r.ci95_high - r.estimate],
                fmt="none", color=BLUE, lw=1)
    ax.scatter(r.estimate, y, s=6 + 60 * np.sqrt(r.pairs / r.pairs.max()), color=BLUE,
               ec="white", lw=0.5, zorder=4)
    lab = [root_label(g) if g != "other multi-model roots" else "56 smaller roots"
           for g in r.group]
    ax.set_yticks(y, [f"{l} ({int(n)})" for l, n in zip(lab, r.pairs)])
    ax.set_xlabel("Shared-root coefficient")
    ax.set_title("(a) By root (same-root pairs)")
    # (b) by capability
    ax = axes[1]
    c = h[h.analysis == "by capability"].reset_index(drop=True)
    x = np.arange(len(c))
    ax.errorbar(x, c.estimate, yerr=[c.estimate - c.ci95_low, c.ci95_high - c.estimate],
                fmt="s", ms=3.5, color=BLUE, lw=1)
    ax.set_xticks(x, ["<.30", ".30–\n.50", ".50–\n.60", "≥.60"])
    ax.set_xlabel("Lower accuracy of the pair")
    ax.set_title("(b) By capability")
    ax.set_ylim(0, 0.32)
    # (c) per subject
    ax = axes[2]
    x = np.arange(len(sub))
    cat = sub.subject.map(MMLU_CATEGORY)
    for name, c in CAT_COLORS.items():
        m = (cat == name).to_numpy()
        ax.errorbar(x[m], sub.same_root[m], yerr=Z * sub.same_root_se[m], fmt="o", ms=2.3,
                    color=c, lw=0.6, elinewidth=0.6, label=name.replace("_", " "))
    for k, ha in ((0, "left"), (len(sub) - 1, "right")):
        ax.annotate(sub.subject.iloc[k].replace("_", " "), (x[k], sub.same_root.iloc[k]),
                    xytext=(4 if ha == "left" else -4, -12 if ha == "left" else 8),
                    textcoords="offset points", ha=ha, fontsize=6.8, color=INK,
                    arrowprops=dict(arrowstyle="-", color=GREY, lw=0.4))
    ax.legend(frameon=False, loc="lower right", fontsize=6.6, ncol=2, handletextpad=0.1,
              columnspacing=0.5, markerscale=1.2)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(sub)} MMLU subjects, sorted")
    ax.set_title("(c) By subject")
    ax.set_ylim(0, 0.25)
    ax.text(0.02, 0.97, "exploratory: 57 tests, no multiplicity adjustment",
            transform=ax.transAxes, ha="left", va="top", fontsize=7.5, color=GREY,
            style="italic")
    for a in axes:
        if a is axes[0]:
            a.axvspan(base.ci_low, base.ci_high, color=LBLUE, alpha=0.35, lw=0)
            a.axvline(base.estimate, color=BLUE, lw=0.6, ls=(0, (3, 2)))
            a.set_xlim(0, 0.28)
        else:
            a.axhspan(base.ci_low, base.ci_high, color=LBLUE, alpha=0.35, lw=0)
            a.axhline(base.estimate, color=BLUE, lw=0.6, ls=(0, (3, 2)))
    fig.tight_layout(pad=0.3, w_pad=0.8)
    return save(fig, "fig_heterogeneity")


# ------------------------------------------------------------------ detection
def fig_detection():
    import json
    info = json.loads((RES / "exp04_heterogeneity/info.json").read_text())["detection"]
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.3))
    for ax, f, xl, title, key in (
            (axes[0], "agreement_hist.csv", "P(same wrong | both wrong)", "(a) Agreement", "auc_raw"),
            (axes[1], "residual_hist.csv", "Net of accuracy and gap",
             "(b) Adjusted", "auc_net_of_accuracy_and_gap")):
        h = pd.read_csv(RES / "exp04_heterogeneity" / f)
        w = h.bin_low.diff().iloc[1]
        for col, c, lab, ls in (("different_root", ORANGE, "different roots", "-"),
                                ("same_root", BLUE, "same root", "-")):
            dens = h[col] / h[col].sum() / w
            ax.step(h.bin_low + w, dens, where="pre", color=c, lw=1.1, label=lab)
            ax.fill_between(h.bin_low + w, dens, step="pre", color=c, alpha=0.15, lw=0)
        ax.set_xlabel(xl)
        ax.set_title(f"{title}, AUC {info[key]:.2f}")
        ax.set_yticks([])
    axes[0].set_ylabel("Density")
    h, l = axes[0].get_legend_handles_labels()
    axes[1].legend(h, l, frameon=False, loc="upper right", fontsize=7.5, handlelength=1.2)
    fig.tight_layout(pad=0.3, w_pad=0.6)
    return save(fig, "fig_detection")


# ------------------------------------------------------------------ accuracy over time
def fig_accuracy():
    from scipy.stats import gaussian_kde, spearmanr
    pop = population("primary")
    v = pd.read_csv(RES / "exp04_validation/per_model.csv").set_index("model")
    pop = pop.assign(acc=v.loc[pop.model, "accuracy"].to_numpy())
    per = pd.PeriodIndex(pop.created_month, freq="M")
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.45), gridspec_kw=dict(width_ratios=[1, 1.5]))
    ax = axes[0]
    a = pop.acc.to_numpy()
    ax.hist(a, bins=np.arange(0.2, 0.85, 0.025), density=True, color=LBLUE, edgecolor=BLUE,
            lw=0.4, alpha=0.8)
    g = np.linspace(0.18, 0.85, 300)
    ax.plot(g, gaussian_kde(a, bw_method=0.18)(g), color=BLUE, lw=1.1)
    ax.plot(a, np.full(len(a), -0.25), "|", color=BLUE, ms=3.5, mew=0.3, alpha=0.5)
    top = ax.get_ylim()[1] * 1.32
    ax.set_ylim(-0.6, top)
    ax.axvline(0.25, color=GREY, ls=(0, (3, 2)), lw=0.7)
    ax.axvline(0.30, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.text(0.245, top * 0.985, "chance", color=GREY, fontsize=7.2, va="top", ha="right")
    ax.text(0.305, top * 0.985, "S2 cut-off", color=RED, fontsize=7.2, va="top", ha="left")
    ax.text(0.83, top * 0.72, f"n = {len(a)}\nmedian {np.median(a):.2f}\n"
            f"{int((a < 0.30).sum())} below 0.30", ha="right", va="top", fontsize=7,
            linespacing=1.15, bbox=dict(fc="white", ec=LGREY, lw=0.5, boxstyle="round,pad=0.25"))
    ax.set_xlabel("Accuracy")
    ax.set_ylabel("Density")
    ax.set_yticks([])
    ax.set_title("(a) Distribution")
    ax = axes[1]
    x = ((per.year - 2022) * 12 + per.month).to_numpy().astype(float)
    xj = x + np.random.default_rng(1).uniform(-0.3, 0.3, len(x))   # spread one-month columns
    dens = gaussian_kde(np.vstack([x / 30, a]))(np.vstack([x / 30, a]))
    o = np.argsort(dens)
    ax.scatter(xj[o], a[o], c=dens[o], cmap="Blues", vmin=-dens.max() * 0.3, s=6, lw=0,
               alpha=0.9)
    q = pd.PeriodIndex(per.asfreq("Q"))
    gq = pop.groupby(q).acc
    ok = gq.size() >= 10                              # quarters with at least 10 models
    med, lo, hi = gq.median()[ok], gq.quantile(0.25)[ok], gq.quantile(0.75)[ok]
    qx = [(p_.year - 2022) * 12 + p_.end_time.month - 1 for p_ in med.index]
    ax.fill_between(qx, lo.values, hi.values, color=ORANGE, alpha=0.18, lw=0,
                    label="quarterly IQR")
    ax.plot(qx, med.values, "-o", color=ORANGE, lw=1.3, ms=2.5, label="quarterly median")
    ax.axhline(0.25, color=GREY, ls=(0, (3, 2)), lw=0.7)
    rho = spearmanr(x, a).statistic
    ax.text(0.03, 0.62, f"Spearman ρ = {rho:.2f}", transform=ax.transAxes, fontsize=7,
            bbox=dict(fc="white", ec=LGREY, lw=0.5, boxstyle="round,pad=0.25"))
    ticks = [(y_ - 2022) * 12 + 1 for y_ in (2022, 2023, 2024)]
    ax.set_xticks(ticks, ["2022", "2023", "2024"])
    ax.set_xlabel("Upload month")
    ax.set_title("(b) Over time")
    ax.legend(frameon=False, loc="upper left", fontsize=7, handlelength=1.2)
    fig.tight_layout(pad=0.3, w_pad=0.6)
    return save(fig, "fig_accuracy")


ALL = {"precision": fig_precision, "workflow": fig_workflow, "schematic": fig_schematic,
       "dataflow": fig_dataflow, "agreement": fig_agreement, "gate": fig_gate,
       "forest": fig_forest, "rawadj": fig_rawadj, "inference": fig_inference,
       "outcomes": fig_outcomes, "itemnull": fig_itemnull, "controls": fig_controls,
       "heatmap": fig_heatmap, "gap": fig_gap, "dose": fig_dose, "timing": fig_timing,
       "itemnull_main": fig_itemnull_main, "heterogeneity": fig_heterogeneity,
       "detection": fig_detection, "accuracy": fig_accuracy}


README_FIGS = ["gap", "dose", "timing", "heterogeneity", "detection", "dataflow", "forest"]


def readme_assets() -> list[str]:
    """PNG copies of selected figures for the repository README (GitHub cannot
    show PDFs inline). Same drawing code as the paper figures."""
    out = ROOT / "docs" / "assets"
    out.mkdir(parents=True, exist_ok=True)
    global save
    orig = save

    def save_png(fig, name):
        fig.savefig(out / f"{name}.png", dpi=220, facecolor="white",
                    metadata={"Software": None})
        plt.close(fig)
        return name
    save = save_png
    try:
        return [ALL[k]() for k in README_FIGS]
    finally:
        save = orig


def build_all(only=None) -> list[str]:
    return [f() for k, f in ALL.items() if not only or k in only]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--readme", action="store_true", help="also write README PNGs")
    a = ap.parse_args()
    print("\n".join(build_all(a.only)))
    if a.readme:
        print("\n".join(f"docs/assets/{n}.png" for n in readme_assets()))
