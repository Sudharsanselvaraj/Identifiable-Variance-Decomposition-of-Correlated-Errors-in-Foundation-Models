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
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

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
    pop, _ = A.load_population(name, False)
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
    fig, ax = plt.subplots(figsize=(COL, 2.25))
    ax.set_xlim(-0.8, 12.4); ax.set_ylim(0.0, 3.3)
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
    fig.tight_layout(pad=0.3)
    return save(fig, "fig_schematic")


# ------------------------------------------------------------------ 3 data flow
def fig_dataflow():
    d = flow()
    c = d["cats"]
    v = pd.read_csv(RES / "exp04_validation/per_model.csv")
    acc = v[v.category == "validated"]
    both = int((acc.in_primary_sample & acc.in_expanded_sample).sum())
    pre = pd.read_csv(RES / "exp04_final/prereg_12.csv")
    strict = pre[pre.analysis.isin(["primary_strict", "expanded_strict"])] \
        .groupby("analysis").models.first()
    fig, ax = blank(FULL, 2.4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    W, H = 0.163, 0.21
    ys = {"p": 0.565, "x": 0.215}
    box(ax, 0.017, 0.315, 0.15, 0.33, f"Leaderboard v1\n{fmt(d['total'])} models\n"
        "MMLU, 14,042 items", size=9)
    cols = [0.208, 0.408, 0.608]
    for x, t in zip(cols, ("Eligible", "Frozen sample (≤ 40 per root)", "Validated")):
        ax.text(x + W / 2, 0.86, t, ha="center", va="bottom", fontsize=9, weight="bold")
    vals = {"p": ("Primary", [f"{fmt(d['elig_p'])} (card links)", f"{fmt(d['frozen_p'])}",
                              f"{fmt(d['val_p'])} ({fmt(strict['primary_strict'])} strict)"]),
            "x": ("Expanded", [f"{fmt(d['elig_x'])} (+ config links)", f"{fmt(d['frozen_x'])}",
                               f"{fmt(d['val_x'])} ({fmt(strict['expanded_strict'])} strict)"])}
    for key, (lab, vv) in vals.items():
        y = ys[key]
        arrow(ax, (0.167, 0.48 + (0.02 if key == "p" else -0.02)), (cols[0] - 0.004, y + H / 2))
        for k, x in enumerate(cols):
            box(ax, x, y, W, H, f"{lab}\n{vv[k]}", size=9)
            if k:
                arrow(ax, (cols[k - 1] + W + 0.004, y + H / 2), (x - 0.004, y + H / 2))
    ax.text(cols[1] + W / 2 + 0.1, 0.48, "same item-level checks for both", ha="center", va="center",
            fontsize=8.5, color=GREY, style="italic")
    box(ax, 0.82, 0.315, 0.163, 0.33, f"Accepted\n{fmt(len(acc))} unique models\n"
        f"({both} in both)", size=9)
    for key in ys:
        arrow(ax, (cols[2] + W + 0.004, ys[key] + H / 2 + (-0.02 if key == "p" else 0.02)),
              (0.818, 0.48 + (0.03 if key == "p" else -0.03)))
    ax.text(0.5, 0.03, f"Excluded and logged, none replaced: {c.get('no_complete_run', 0)} no "
            f"complete run, {c.get('repo_missing', 0)} repository missing, "
            f"{c.get('schema_error', 0)} unreadable (of {fmt(d['union'])} frozen)",
            ha="center", va="bottom", fontsize=8.5, color="black")
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
    short = {"meta-llama/Meta-Llama-3-8B": "Llama-3-8B", "mistralai/Mistral-7B-v0.1": "Mistral-7B-v0.1",
             "mistral-community/Mistral-7B-v0.2": "Mistral-7B-v0.2",
             "meta-llama/Meta-Llama-3-70B": "Llama-3-70B", "mistralai/Mixtral-8x7B-v0.1": "Mixtral-8x7B",
             "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T": "TinyLlama-1.1B",
             "openlm-research/open_llama_3b": "OpenLLaMA-3B", "Locutusque/TinyMistral-248M": "TinyMistral-248M"}
    names = [f"{short.get(r, r.split('/')[-1])} ({vc[r]})" for r in roots]
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
    fig, axes = plt.subplots(1, 3, figsize=(COL, 3.5), sharey=True,
                             gridspec_kw=dict(width_ratios=[1, 1, 0.9]))
    yy = np.arange(len(order))[::-1] + np.array([0.6 if a.startswith("primary") else 0
                                                 for a in order])
    ZOOM = (-0.04, 0.03)                              # range magnified in panel (c)
    for ax, t, title, c in zip(axes, ("same_root", "gap0", "gap0"),
                               ("(a) Shared\nroot", "(b) Same\nmonth", "(c) Same month,\nmagnified"),
                               (BLUE, ORANGE, ORANGE)):
        d = pre[pre.term == t].set_index("analysis").loc[order]
        for k, a in enumerate(order):
            base = a in ("primary", "expanded")
            ax.errorbar(d.estimate[a], yy[k], xerr=[[d.estimate[a] - d.ci_low[a]],
                        [d.ci_high[a] - d.estimate[a]]], fmt="D" if base else "o",
                        ms=3.4 if base else 2.8, color=c, mfc=c if base else "white", lw=0.8)
        zero(ax)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlabel("Coefficient")
    for ax in axes[:2]:                               # common scale: widths comparable
        ax.set_xlim(-0.04, 0.16)
        ax.set_xticks([0, 0.1])
    axes[1].add_patch(Rectangle((ZOOM[0], yy[-1] - 0.5), ZOOM[1] - ZOOM[0], yy[0] - yy[-1] + 1.2,
                                fill=False, ec=GREY, lw=0.6, ls=(0, (2, 2)), zorder=3))
    axes[2].set_xlim(*ZOOM); axes[2].set_xticks([-0.03, 0, 0.03], ["−0.03", "0", "0.03"])
    axes[0].set_yticks(yy, [PRETTY[a.partition("_")[2]] for a in order])
    for ax in axes:
        ax.axhspan(yy[5] - 0.45, yy[0] + 0.45, color="#f3f6fa", zorder=-1)
        ax.tick_params(axis="x", labelsize=7.5)
    axes[0].text(0.004, yy[0] + 0.5, "PRIMARY", fontsize=7.5, weight="bold", color=GREY,
                 va="center")
    axes[0].text(0.004, yy[6] + 0.5, "EXPANDED", fontsize=7.5, weight="bold", color=GREY,
                 va="center")
    axes[0].set_ylim(yy[-1] - 0.6, yy[0] + 0.9)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="D", color=GREY, ls="", ms=3.4, label="primary specification"),
         Line2D([], [], marker="o", color=GREY, mfc="white", ls="", ms=2.8,
                label="sensitivity analysis")]
    fig.legend(handles=h, loc="upper center", ncol=2, frameon=False, fontsize=7.5,
               bbox_to_anchor=(0.6, 1.0))
    fig.tight_layout(pad=0.3, w_pad=0.4, rect=(0, 0, 1, 0.93))
    return save(fig, "exp04_forest")


# ------------------------------------------------------------------ 8 raw vs adjusted
GAPS = [("same_root", "shared root"), ("gap0", "0 months"), ("gap1_2", "1–2 months"),
        ("gap3_5", "3–5 months"), ("gap6_11", "6–11 months")]


def fig_rawadj():
    r = pd.read_csv(RES / "exp04_final/raw_vs_adjusted.csv")
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.35), sharey=True)
    y = np.arange(len(GAPS))[::-1]
    for ax, pop in zip(axes, ("primary", "expanded")):
        for lab, dy, c, mfc in (("raw (no accuracy terms)", 0.14, GREY, "white"),
                                ("adjusted (pre-registered)", -0.14, BLUE, BLUE)):
            d = r[(r.population == pop) & (r.model == lab)].set_index("term").loc[
                [g for g, _ in GAPS]]
            ax.errorbar(d.estimate, y + dy, xerr=[d.estimate - d.ci_low, d.ci_high - d.estimate],
                        fmt="o", ms=3, color=c, mfc=mfc, lw=0.8,
                        label=lab.split(" (")[0].capitalize() + (" (no accuracy terms)"
                                                                 if "raw" in lab else
                                                                 " (pre-specified)"))
        zero(ax)
        ax.set_title(f"({'ab'[pop == 'expanded']}) {pop.capitalize()}")
        ax.set_xlabel("Coefficient")
        ax.axhline(3.5, color=LGREY, lw=0.5)
    axes[0].set_yticks(y, [g for _, g in GAPS])
    axes[0].set_ylabel("Release gap (reference: 12+ months)", fontsize=7.8)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=7.5, handletextpad=0.2, bbox_to_anchor=(0.55, 1.0))
    fig.tight_layout(pad=0.3, w_pad=0.5, rect=(0, 0, 1, 0.9))
    return save(fig, "fig_raw_adjusted")


# ------------------------------------------------------------------ 9 inference
def fig_inference():
    inf = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    kinds = [("model-dyadic (pre-registered)", "model-level dyadic (pre-specified)", BLUE, "o"),
             ("root-dyadic", "root-level dyadic", GREY, "s"),
             ("delete-one-root jackknife", "delete-one-root jackknife", ORANGE, "^")]
    pops = list(SAMPLES)
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.45), sharey=True)
    y = np.arange(len(pops))[::-1]
    for ax, t, title in zip(axes, ("same_root", "gap0"),
                            ("(a) Shared root", "(b) Same month")):
        for k, (kind, lab, c, mk) in enumerate(kinds):
            d = inf[(inf.term == t) & (inf.inference == kind)].set_index("population").loc[pops]
            ax.errorbar(d.estimate, y + (0.22 - 0.22 * k), xerr=[d.estimate - d.ci_low,
                        d.ci_high - d.estimate], fmt=mk, ms=2.8, color=c, lw=0.8, label=lab,
                        mfc="white" if k else c)
        zero(ax)
        ax.set_title(title); ax.set_xlabel("Coefficient (95% CI)")
    axes[0].set_xlim(0, 0.18)
    axes[0].set_yticks(y, [SAMPLES[p] for p in pops])
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.0), handletextpad=0.2,
               columnspacing=0.8)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.86), w_pad=0.5)
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
    fig, ax = plt.subplots(figsize=(FULL, 2.5))
    data = tab.to_numpy().astype(float)
    masked = np.ma.masked_equal(data, 0)
    from matplotlib.colors import LogNorm
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("steel", ["#eef3f9", "#b5c7df", BLUE, "#3f5f8f"])
    cmap.set_bad("white")
    im = ax.imshow(masked, aspect="auto", cmap=cmap, norm=LogNorm(1, data.max()),
                   interpolation="none")
    for (r, c), v in np.ndenumerate(data):
        if v:
            ax.text(c, r, int(v), ha="center", va="center", fontsize=7.5,
                    color="white" if v > data.max() ** 0.6 else "black")
    ax.set_xticks(range(len(months)), [m.strftime("%b %y") if m.month in (1, 4, 7, 10)
                                       else "" for m in months], fontsize=8.0)
    short = lambda k: (k if len(k) <= 24 else k[:21] + "…")  # noqa: E731
    names = [f"{short(k.split('/')[-1])} (n={vc[k]})" for k in keep]
    names.append(f"{n_other_roots} other roots (n={int(data[-1].sum())})")
    ax.set_yticks(range(len(names)), names, fontsize=8.0)
    ax.set_xticks(np.arange(-0.5, len(months)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(names)), minor=True)
    ax.grid(False)
    ax.grid(which="minor", color="#e6e6e6", lw=0.3)
    ax.tick_params(which="minor", length=0)
    ax.axhline(len(keep) - 0.5, color=GREY, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)
    ax.set_xlabel("Hub upload month")
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    ticks = [t for t in (1, 2, 5, 10, 20, 50) if t <= data.max()]
    cb.set_ticks(ticks, labels=[str(t) for t in ticks]); cb.minorticks_off()
    cb.set_label("Models (log scale)", fontsize=7.5); cb.ax.tick_params(labelsize=5.5)
    fig.tight_layout(pad=0.3)
    return save(fig, "fig_lineage_month_map")


# ------------------------------------------------------------------ 14 agreement by gap
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
    fig, ax = plt.subplots(figsize=(COL, 2.35))
    MIN_PAIRS = 20   # bins with fewer pairs are not plotted (1 same-root pair at 12+)
    for flag, name, c, mk in [(True, "same lineage root", BLUE, "D"),
                              (False, "different roots", ORANGE, "o")]:
        cnt = np.array([int(((b == k) & (same == flag)).sum()) for k in range(5)])
        ys = [d["y"][(b == k) & (same == flag)] for k in range(5)]
        m = np.array([v.mean() if cnt[k] >= MIN_PAIRS else np.nan for k, v in enumerate(ys)])
        q = np.array([np.percentile(v, [25, 75]) if cnt[k] >= MIN_PAIRS else [np.nan] * 2
                      for k, v in enumerate(ys)])
        x = np.arange(5) + (0.08 if flag else -0.08)
        ax.vlines(x, q[:, 0], q[:, 1], color=c, lw=2.2, alpha=0.25)
        ax.plot(x, m, marker=mk, ms=3.2, color=c, label=name)
        for k in range(5):
            if cnt[k] >= MIN_PAIRS:
                ax.annotate(f"{cnt[k]:,}", (x[k], q[k, 1] if flag else q[k, 0]),
                            textcoords="offset points", xytext=(0, 3 if flag else -8),
                            ha="center", fontsize=7.5, color=c)
    ax.set_xticks(range(5), lab)
    ax.set_xlim(-0.45, 4.45)
    ax.set_xlabel("Release-month gap between the two models")
    ax.set_ylabel("P(same wrong | both wrong)")
    ax.set_ylim(0.2, 1.0)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout(pad=0.3)
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
    fig.tight_layout(pad=0.3, w_pad=0.6)
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
    n = pd.read_csv(RES / "exp04_item_null/item_null.csv")
    outs = [("pre-registered: same-wrong agreement", "observed", GREY, "o"),
            ("N1a: minus item distractor null (all models)", "N1a", BLUE, "s"),
            ("N1b: minus item distractor null (roots weighted equally)", "N1b", LBLUE, "D")]
    pops = list(SAMPLES)
    x = np.arange(len(pops))
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.45))
    for k, (o, lab, c, mk) in enumerate(outs):
        d = n[(n.outcome == o) & (n.term == "same_root")].set_index("population").loc[pops]
        axes[0].plot(x + (k - 1) * 0.18, d.outcome_mean, mk, color=c, ms=4.5, label=lab,
                     mfc=c if k < 2 else "white")
        axes[1].errorbar(x + (k - 1) * 0.18, d.estimate, yerr=Z * d.se_jackknife, fmt=mk,
                         ms=3.5, color=c, lw=1, mfc=c if k < 2 else "white")
    axes[0].set_ylim(-0.03, 0.62); axes[0].set_ylabel("Mean over pairs")
    axes[0].set_title("(a) Level")
    axes[1].set_ylim(0, 0.17); axes[1].set_ylabel("Shared-root coefficient")
    axes[1].set_title("(b) Lineage contrast")
    for ax in axes:
        zero(ax, horizontal=True)
        ax.set_xticks(x, ["P", "P-S2", "E", "E-S2"])
    axes[0].legend(frameon=False, loc="center right", fontsize=8, handletextpad=0.2)
    fig.tight_layout(pad=0.3, w_pad=0.8)
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
                fmt="o", ms=3.5, color=BLUE, lw=1)
    lab = [g.split("/")[-1].replace("Meta-", "") if g != "other multi-model roots"
           else "56 smaller roots" for g in r.group]
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
    ax.errorbar(x, sub.same_root, yerr=Z * sub.same_root_se, fmt="o", ms=2, color=BLUE,
                lw=0.6, elinewidth=0.6)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(sub)} MMLU subjects, sorted")
    ax.set_title("(c) By subject")
    ax.set_ylim(0, 0.25)
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
    pop = population("primary")
    v = pd.read_csv(RES / "exp04_validation/per_model.csv").set_index("model")
    pop = pop.assign(acc=v.loc[pop.model, "accuracy"].to_numpy())
    per = pd.PeriodIndex(pop.created_month, freq="M")
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.3), gridspec_kw=dict(width_ratios=[1, 1.5]))
    ax = axes[0]
    ax.hist(pop.acc, bins=np.arange(0.2, 0.85, 0.025), color=LBLUE, edgecolor=BLUE, lw=0.5)
    ax.axvline(0.25, color=GREY, ls=(0, (3, 2)), lw=0.7)
    ax.axvline(0.30, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.text(0.32, ax.get_ylim()[1] * 0.92, "S2\ncut-off", color=RED, fontsize=7.5, va="top")
    ax.set_xlabel("Accuracy")
    ax.set_ylabel("Models")
    ax.set_title("(a) Distribution")
    ax = axes[1]
    q = pd.PeriodIndex(per.asfreq("Q"))
    x = (per.year - 2022) * 12 + per.month
    ax.scatter(x, pop.acc, s=5, color=BLUE, alpha=0.35, lw=0)
    g = pop.groupby(q).acc
    med = g.median()[g.size() >= 10]                 # quarters with at least 10 models
    qx = [(p.year - 2022) * 12 + p.end_time.month - 1 for p in med.index]
    ax.plot(qx, med.values, "-", color=ORANGE, lw=1.4, label="quarterly median")
    ax.axhline(0.25, color=GREY, ls=(0, (3, 2)), lw=0.7)
    ticks = [(y - 2022) * 12 + 1 for y in (2022, 2023, 2024)]
    ax.set_xticks(ticks, ["2022", "2023", "2024"])
    ax.set_xlabel("Upload month")
    ax.set_title("(b) Over time")
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)
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
