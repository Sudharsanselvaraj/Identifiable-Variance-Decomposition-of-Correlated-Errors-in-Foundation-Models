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
BLUE, LBLUE = "#1f4e79", "#9fb8d3"           # lineage / primary
ORANGE, LORANGE = "#b8652a", "#e3b48f"       # release time
GREY, LGREY = "#595959", "#bfbfbf"
BOX_FACE, BOX_EDGE = "#eef3f8", "#5b7a99"
RED = "#a61c1c"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.titlesize": 7.5,
    "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "lines.linewidth": 0.9, "errorbar.capsize": 1.8,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})
Z = 1.959964
SAMPLES = {"primary": "Primary", "primary_S2": "Primary, acc ≥ 0.30",
           "expanded": "Expanded", "expanded_S2": "Expanded, acc ≥ 0.30"}


def save(fig, name: str) -> str:
    fig.savefig(FIG / f"{name}.pdf", metadata={"CreationDate": None})
    plt.close(fig)
    return name


def zero(ax, horizontal=False):
    (ax.axhline if horizontal else ax.axvline)(0, color=GREY, lw=0.6, ls=(0, (3, 2)), zorder=0)


def box(ax, x, y, w, h, text, face=BOX_FACE, edge=BOX_EDGE, size=6.3, bold_first=True,
        lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.012",
                                fc=face, ec=edge, lw=lw, ls=ls, transform=ax.transAxes))
    lines = text.split("\n")
    if bold_first:
        ax.text(x + w / 2, y + h - 0.13 * h, lines[0], ha="center", va="top", fontsize=size,
                weight="bold", transform=ax.transAxes)
        ax.text(x + w / 2, y + 0.40 * h, "\n".join(lines[1:]),
                ha="center", va="center", fontsize=size - 0.4, transform=ax.transAxes,
                linespacing=1.25)
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
    ax.axhline(0.10, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.text(sc.F.min(), 0.096, "target RMSE 0.10", color=RED, ha="left", va="top", fontsize=6)
    ax.set_xlabel("Number of families (lineage levels)")
    ax.set_ylabel("Worst-case RMSE of a variance share")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout(pad=0.3)
    return save(fig, "precision_scaling")


# ------------------------------------------------------------------ 2 workflow
def fig_workflow():
    d = flow()
    c = d["cats"]
    fig, ax = blank(FULL, 2.75)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    row1 = [
        ("1  Source", f"Open LLM Leaderboard, version 1\n{fmt(d['total'])} models; MMLU, "
                      "14,042 items\nper-item details with option scores"),
        ("2  Lineage", f"declared base_model chain → root\neligible: {fmt(d['elig_p'])} primary"
                       f" (card links),\n{fmt(d['elig_x'])} expanded (+ config paths)"),
        ("3  Freeze", f"≤ 40 models per root, seed 0\n{fmt(d['frozen_p'])} primary + "
                      f"{fmt(d['frozen_x'])} expanded\n({fmt(d['union'])} unique; SHA-256 "
                      "recorded)"),
        ("4  Validate", f"argmax of option scores must match\nstored correctness on every item"
                        f"\n{fmt(c['validated'])} accepted, "
                        f"{fmt(d['union'] - c['validated'])} excluded (logged)"),
    ]
    row2 = [
        ("5  Pairs", f"$a_{{ij}}$ = P(same wrong | both wrong)\n{fmt(d['pairs_p'])} primary, "
                     f"{fmt(d['pairs_x'])} expanded\n≥ {fmt(d['den'].jointly_wrong_min.min())}"
                     " jointly wrong items per pair"),
        ("6  Estimate", f"shared root + release-gap bins\n+ accuracy sum and difference\n"
                        f"{d['n_prereg']} pre-registered analyses"),
        ("7  Audit (partly post hoc)", "root-level inference, outcomes,\nitem-difficulty "
                                       "nulls, gate audit,\nsize & architecture controls"),
    ]
    gap, w, h = 0.035, 0.2165, 0.30
    y1, y2 = 0.56, 0.12
    for k, (t, body) in enumerate(row1):
        x = 0.01 + k * (w + gap)
        box(ax, x, y1, w, h, f"{t}\n{body}", size=6.3)
        if k:
            arrow(ax, (x - gap + 0.003, y1 + h / 2), (x - 0.003, y1 + h / 2))
    x0 = 0.01 + (4 * (w + gap) - gap - (3 * w + 2 * gap)) / 2
    for k, (t, body) in enumerate(row2):
        x = x0 + k * (w + gap)
        last = k == 2
        box(ax, x, y2, w, h, f"{t}\n{body}", size=6.3, face="#f6f6f6" if last else BOX_FACE,
            edge=GREY if last else BOX_EDGE, ls="--" if last else "-")
        if k:
            arrow(ax, (x - gap + 0.003, y2 + h / 2), (x - 0.003, y2 + h / 2))
    # row 1 -> row 2
    xe, ym = 0.01 + 3 * (w + gap) + w / 2, (y1 + y2 + h) / 2
    ax.plot([xe, xe, x0 + w / 2], [y1 - 0.005, ym, ym], color=BOX_EDGE, lw=0.8,
            transform=ax.transAxes)
    arrow(ax, (x0 + w / 2, ym), (x0 + w / 2, y2 + h + 0.005))
    # pre-registration band over steps 2-6
    ax.text(0.5, 0.955, "Fixed before any outcome was computed: lineage rules, caps and seed, "
            "pair model, simulation gate (three dated amendments)", ha="center", va="center",
            fontsize=6.4, color=BLUE, transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=BLUE, lw=0.6))
    return save(fig, "fig_workflow")


# ------------------------------------------------------------------ 3 schematic
def fig_schematic():
    fig, ax = plt.subplots(figsize=(COL, 2.05))
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
        ax.text(m0, y + 0.28, f"root {r}", ha="center", fontsize=6.2, weight="bold", color=c)
        for name, m in kids:
            ax.annotate("", (m, y), (m0, y), arrowprops=dict(
                arrowstyle="-|>", color=LGREY, lw=0.6, mutation_scale=5, shrinkA=3, shrinkB=3,
                connectionstyle="arc3,rad=-0.28"))
            ax.scatter(m, y, s=24, color=lc, ec=c, lw=0.6, zorder=3)
            ax.text(m, y - 0.3, name, ha="center", fontsize=6)
            pos[name] = (m, y)
    def bracket(a, b, y, txt, c):
        x1, x2 = pos[a][0], pos[b][0]
        ax.plot([x1, x1, x2, x2], [y + 0.1, y, y, y + 0.1], color=c, lw=0.8)
        ax.text((x1 + x2) / 2, y - 0.08, txt, color=c, ha="center", va="top", fontsize=5.6)
    bracket("A1", "A2", 1.72, "shared root,\ngap 1 (bin 1–2)", BLUE)
    (xa, ya), (xb, yb) = pos["A3"], pos["B2"]
    ax.annotate("", (xb + 0.05, yb + 0.12), (xa + 0.05, ya - 0.42), arrowprops=dict(
        arrowstyle="<->", color=ORANGE, lw=0.9, mutation_scale=6))
    ax.text(xa + 0.35, (ya + yb) / 2 - 0.1, "different roots,\nsame month\n(bin 0)",
            color=ORANGE, fontsize=5.6, va="center")
    ax.text(-0.6, 0.12, "arcs: declared fine-tune ancestry", fontsize=5.4, color=GREY,
            ha="left")
    fig.tight_layout(pad=0.3)
    return save(fig, "fig_schematic")


# ------------------------------------------------------------------ 4 validation
def fig_validation():
    d = flow()
    c = d["cats"]
    fig, ax = blank(COL, 3.2)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    W, X0, H = 0.56, 0.03, 0.105
    steps = [
        ("Details repository", "per-item parquet files, 57 subjects"),
        ("Select run", "most rows among runs covering all 57 subjects"),
        ("Read four fields per item", "option log-likelihoods, gold, stored acc, hash"),
        ("Chosen option = argmax", "of the per-option log-likelihoods"),
        ("Item-level checks", "(i) 14,042 items  (ii) argmax correct ⇔ stored\nacc, every item  "
                              "(iii) order & gold = reference"),
        ("Store", "chosen option, gold, item id, hash, run, layout"),
    ]
    ys = [0.86 - k * 0.15 for k in range(len(steps))]
    hs = [H + (0.035 if "\n" in b else 0) for _, b in steps]
    for k, ((t, b), y) in enumerate(zip(steps, ys)):
        box(ax, X0, y - hs[k] / 2, W, hs[k], f"{t}\n{b}", size=6.0)
        if k:
            arrow(ax, (X0 + W / 2, ys[k - 1] - hs[k - 1] / 2), (X0 + W / 2, y + hs[k] / 2))
    rej = [(1, f"no complete run: {c.get('no_complete_run', 0)}"),
           (0, f"repository missing: {c.get('repo_missing', 0)}"),
           (2, f"unreadable predictions: {c.get('schema_error', 0)}"),
           (4, f"failed an item check: {sum(c.get(k, 0) for k in ('acc_mismatch', 'item_count_mismatch', 'row_count_mismatch'))}")]
    for k, t in rej:
        y = ys[k]
        bx = X0 + W + 0.07
        box(ax, bx, y - 0.04, 0.33, 0.08, t, face="#fbf1f1", edge=RED, size=5.6,
            bold_first=False)
        arrow(ax, (X0 + W, y), (bx, y), color=RED)
    ax.text(X0 + W + 0.07 + 0.165, ys[0] + 0.065, "rejected (logged)",
            ha="center", fontsize=5.4, color=RED, weight="bold")
    ax.text(X0 + W + 0.07 + 0.165, ys[5], f"{fmt(c['validated'])} of {fmt(d['union'])}\n"
            "models accepted", ha="center", va="center", fontsize=6.5, weight="bold", color=BLUE)
    arrow(ax, (X0 + W, ys[5]), (X0 + W + 0.065, ys[5]), color=BLUE)
    ax.text(X0 + W + 0.07 + 0.165, ys[3] - 0.005, "newest layout: gold blank,\ntaken from reference by\n"
            "position; check (ii) fails\non ~3/4 of items if misaligned", ha="center",
            va="center", fontsize=5.3, color=GREY, linespacing=1.15)
    return save(fig, "fig_validation")


# ------------------------------------------------------------------ 5 population flow
def fig_population():
    d = flow()
    e = d["excl"]
    fig, ax = blank(COL, 3.25)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    box(ax, 0.18, 0.885, 0.64, 0.09,
        f"Leaderboard v1 models\n{fmt(d['total'])} (de-duplicated)", size=6.2)
    cols = [(0.03, "Primary", "card-declared links", d["elig_p"], d["frozen_p"], d["val_p"],
             "primary", d["strict_p"]),
            (0.53, "Expanded", "+ config.json paths", d["elig_x"], d["frozen_x"], d["val_x"],
             "expanded", None)]
    strict = pd.read_csv(RES / "exp04_final/prereg_12.csv")
    sm = strict[strict.analysis.isin(["primary_strict", "expanded_strict"])] \
        .groupby("analysis").models.first()
    for x, name, sub, el, fr, va, key, _ in cols:
        w = 0.44
        arrow(ax, (0.5, 0.885), (x + w / 2, 0.79))
        box(ax, x, 0.69, w, 0.10, f"{name}: eligible\n{fmt(el)} models ({sub})", size=6.0)
        arrow(ax, (x + 0.09, 0.69), (x + 0.09, 0.615))
        box(ax, x, 0.515, w, 0.10, f"Frozen sample\n{fmt(fr)} (≤ 40 per root, seed 0)",
            size=6.0)
        xa = x + 0.09
        arrow(ax, (xa, 0.515), (xa, 0.30))
        ex = e[key]
        txt = (f"excluded {fmt(ex.drop('validated').sum())}:\n"
               f"{ex['no_complete_run']} no complete run\n{ex['repo_missing']} repository missing\n"
               f"{ex['schema_error']} unreadable")
        box(ax, x + 0.165, 0.335, w - 0.165, 0.145, txt, face="#fbf1f1", edge=RED, size=5.3,
            bold_first=False)
        arrow(ax, (xa, 0.4075), (x + 0.165, 0.4075), color=RED)
        box(ax, x, 0.17, w, 0.13, f"Analysed\n{fmt(va)} models\n({fmt(sm[key + '_strict'])} "
            "with verified pretrained root)", face="#e3ecf5", size=6.0)
    ax.text(0.5, 0.075, f"The two frozen samples overlap in {fmt(d['overlap'])} models "
            f"({fmt(d['union'])} unique);\n{fmt(d['cats']['validated'])} validated, no excluded "
            "model replaced.", ha="center", va="center", fontsize=5.8, color=GREY)
    return save(fig, "fig_population")


# ------------------------------------------------------------------ 6 gate audit
def fig_gate():
    files = [("primary_cap15", "Primary, cap 15"), ("primary_cap40", "Primary, cap 40 (chosen)"),
             ("primary_cap1000", "Primary, uncapped"), ("expanded_cap40", "Expanded, cap 40")]
    aud = {k: pd.read_csv(RES / f"pair_gate_audit/{k}.csv", keep_default_na=False)
           for k, _ in files}
    fig, axes = plt.subplots(1, 3, figsize=(FULL, 2.45), gridspec_kw=dict(width_ratios=[1, 1.5, 1.5]))
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
    ax.set_xticks(range(3), ["root", "0 mo", "1–2 mo"])
    ax.set_ylabel("Rejection rate (%)"); ax.set_ylim(0, 16)
    ax.set_title("(a) Null: false rejection")
    # (b) leakage
    ax = axes[1]
    labs, xs = [], 0
    for lam in ("0.03", "0.05", "0.1"):
        for k, (f, _) in enumerate(files):
            a = aud[f]
            pts(ax, a[(a.truth == f"era_{lam}") & (a.term == "same_root")], np.array([xs]), k)
        labs.append(f"root | λE={float(lam):.2f}"); xs += 1
    for lam in ("0.03", "0.05", "0.1"):
        for k, (f, _) in enumerate(files):
            a = aud[f]
            r = a[(a.truth == f"lineage_{lam}") & a.term.isin(["gap0", "gap1_2"])]
            pts(ax, r.loc[[r.rate.idxmax()]], np.array([xs]), k)
        labs.append(f"month | λL={float(lam):.2f}"); xs += 1
    ax.axhline(10, color=RED, ls=(0, (3, 2)), lw=0.7)
    a = aud["primary_cap40"]
    worst = a[(a.truth == "era_0.1") & (a.term == "same_root")].iloc[0]
    ax.annotate(f"{100 * worst.rate:.1f}% > 10%", (2 + off[1], 100 * worst.rate),
                (1.25, 15.2), fontsize=6, color=RED, arrowprops=dict(arrowstyle="-", color=RED,
                                                                     lw=0.6))
    ax.set_xticks(range(xs), labs, rotation=30, ha="right")
    ax.set_ylim(0, 17); ax.set_title("(b) Cross-leakage: wrong term rejects")
    # (c) power
    ax = axes[2]
    labs, xs = [], 0
    for lam in ("0.03", "0.05"):
        for term, truth, lab in (("same_root", "lineage", "root"), ("gap0", "era", "0 mo")):
            for k, (f, _) in enumerate(files):
                a = aud[f]
                pts(ax, a[(a.truth == f"{truth}_{lam}") & (a.term == term)], np.array([xs]), k)
            labs.append(f"{lab} | λ={float(lam):.2f}"); xs += 1
    ax.axhline(80, color=RED, ls=(0, (3, 2)), lw=0.7)
    ax.set_xticks(range(xs), labs, rotation=30, ha="right")
    ax.set_ylim(0, 105); ax.set_title("(c) Power")
    for ax in axes:
        ax.set_xlim(-0.5, len(ax.get_xticks()) - 0.5)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=4,
               frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.92))
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
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.9), sharey=True)
    yy = np.arange(len(order))[::-1] + np.array([0.6 if a.startswith("primary") else 0
                                                 for a in order])
    for ax, t, title, c in zip(axes, ("same_root", "gap0"),
                               ("(a) Shared root", "(b) Same month"),
                               (BLUE, ORANGE)):
        d = pre[pre.term == t].set_index("analysis").loc[order]
        for k, a in enumerate(order):
            base = a in ("primary", "expanded")
            ax.errorbar(d.estimate[a], yy[k], xerr=[[d.estimate[a] - d.ci_low[a]],
                        [d.ci_high[a] - d.estimate[a]]], fmt="D" if base else "o",
                        ms=3.4 if base else 2.8, color=c, mfc=c if base else "white", lw=0.8)
        zero(ax)
        ax.set_title(title)
        ax.set_xlabel("Coefficient")
    axes[0].set_xlim(0, 0.16)
    g = pre[pre.term == "gap0"]
    lim = max(-g.ci_low.min(), g.ci_high.max()) + 0.004
    axes[1].set_xlim(-lim, lim)
    axes[0].set_yticks(yy, [PRETTY[a.partition("_")[2]] for a in order])
    for ax in axes:
        ax.axhspan(yy[5] - 0.45, yy[0] + 0.45, color="#f3f6fa", zorder=-1)
    axes[0].text(0.004, yy[0] + 0.5, "PRIMARY", fontsize=5.6, weight="bold", color=GREY,
                 va="center")
    axes[0].text(0.004, yy[6] + 0.5, "EXPANDED", fontsize=5.6, weight="bold", color=GREY,
                 va="center")
    axes[0].set_ylim(yy[-1] - 0.6, yy[0] + 0.9)
    fig.tight_layout(pad=0.3, w_pad=0.6)
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
                                                                 " (pre-registered)"))
        zero(ax)
        ax.set_title(f"({'ab'[pop == 'expanded']}) {pop.capitalize()}")
        ax.set_xlabel("Coefficient")
        ax.axhline(3.5, color=LGREY, lw=0.5)
    axes[0].set_yticks(y, [g for _, g in GAPS])
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=5.8, handletextpad=0.2, bbox_to_anchor=(0.55, 1.0))
    fig.tight_layout(pad=0.3, w_pad=0.5, rect=(0, 0, 1, 0.9))
    return save(fig, "fig_raw_adjusted")


# ------------------------------------------------------------------ 9 inference
def fig_inference():
    inf = pd.read_csv(RES / "exp04_final/inference_audit.csv")
    kinds = [("model-dyadic (pre-registered)", "model-level dyadic (pre-reg.)", BLUE, "o"),
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
               frameon=False, fontsize=5.6, bbox_to_anchor=(0.5, 1.0), handletextpad=0.2,
               columnspacing=0.8)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.86), w_pad=0.5)
    return save(fig, "fig_inference")


# ------------------------------------------------------------------ 10 outcomes
def fig_outcomes():
    o = pd.read_csv(RES / "exp04_final/outcome_audit.csv")
    variants = [("primary outcome, OLS (pre-registered)", "Pre-registered"),
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
    axes[0].text(0.198, y[-1] + 0.4, "phi: correlation scale", fontsize=5.2,
                 color=GREY, ha="right")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=5.8, bbox_to_anchor=(0.6, 1.0))
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
        bars = ax.bar(x + (k - 1) * 0.26, m, 0.25, color=shades[k], label=lab)
        for bb, v in zip(bars, m):
            ax.text(bb.get_x() + bb.get_width() / 2, max(v, 0) + 0.008, f"{0.0 if abs(v) < 5e-4 else v:.3f}",
                    rotation=90, ha="center", va="bottom", fontsize=4.6, color=GREY)
    zero(ax, horizontal=True)
    ax.set_xticks(x, [SAMPLES[p].replace(", ", "\n") for p in pops])
    ax.set_ylabel("Mean outcome over pairs")
    ax.set_title("(a) Level: depends on the null")
    ax.set_ylim(-0.02, 0.85)
    ax.legend(frameon=False, fontsize=5.8, loc="upper left", ncol=1)
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
    ax.legend(frameon=False, fontsize=5.8)
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
    cols = [("same_root (model-cl)", "shared root (pre-registered terms + S1)", BLUE, "o", BLUE),
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
    fig.legend(*ax.get_legend_handles_labels(), frameon=False, fontsize=5.8,
               loc="upper center", ncol=2, bbox_to_anchor=(0.55, 1.0), handletextpad=0.2)
    ax.set_xlim(-0.01, 0.16)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.86))
    return save(fig, "fig_controls")


# ------------------------------------------------------------------ 13 lineage x month map
def fig_heatmap(top: int = 14):
    pop = population("primary")
    months = pd.period_range(pop.created_month.min(), pop.created_month.max(), freq="M")
    vc = pop.root.value_counts()
    keep = list(vc.index[:top])
    lab = pop.root.where(pop.root.isin(keep), "other")
    tab = pd.crosstab(lab, pd.PeriodIndex(pop.created_month, freq="M")) \
        .reindex(columns=months, fill_value=0)
    n_other_roots = pop.root.nunique() - len(keep)
    tab = tab.loc[keep + ["other"]]
    fig, ax = plt.subplots(figsize=(FULL, 2.9))
    data = tab.to_numpy().astype(float)
    masked = np.ma.masked_equal(data, 0)
    from matplotlib.colors import LogNorm
    cmap = plt.get_cmap("Blues").copy(); cmap.set_bad("white")
    im = ax.imshow(masked, aspect="auto", cmap=cmap, norm=LogNorm(1, data.max()),
                   interpolation="none")
    for (r, c), v in np.ndenumerate(data):
        if v:
            ax.text(c, r, int(v), ha="center", va="center", fontsize=4.8,
                    color="white" if v > data.max() ** 0.6 else "black")
    ax.set_xticks(range(len(months)), [m.strftime("%b %y") if m.month in (1, 4, 7, 10)
                                       else "" for m in months], fontsize=5.8)
    short = lambda k: (k if len(k) <= 24 else k[:21] + "…")  # noqa: E731
    names = [f"{short(k.split('/')[-1])} (n={vc[k]})" for k in keep]
    names.append(f"{n_other_roots} other roots (n={int(data[-1].sum())})")
    ax.set_yticks(range(len(names)), names, fontsize=5.8)
    ax.set_xticks(np.arange(-0.5, len(months)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(names)), minor=True)
    ax.grid(which="minor", color="#e6e6e6", lw=0.3)
    ax.tick_params(which="minor", length=0)
    ax.axhline(len(keep) - 0.5, color=GREY, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)
    ax.set_xlabel("Hub upload month")
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    ticks = [t for t in (1, 2, 5, 10, 20, 50) if t <= data.max()]
    cb.set_ticks(ticks, labels=[str(t) for t in ticks]); cb.minorticks_off()
    cb.set_label("Models (log scale)", fontsize=6); cb.ax.tick_params(labelsize=5.5)
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
                            ha="center", fontsize=5.2, color=c)
    ax.set_xticks(range(5), lab)
    ax.set_xlabel("Release-month gap between the two models")
    ax.set_ylabel("P(same wrong | both wrong)")
    ax.set_ylim(0.2, 1.0)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout(pad=0.3)
    return save(fig, "exp04_agreement_by_gap")


ALL = {"precision": fig_precision, "workflow": fig_workflow, "schematic": fig_schematic,
       "validation": fig_validation, "population": fig_population, "gate": fig_gate,
       "forest": fig_forest, "rawadj": fig_rawadj, "inference": fig_inference,
       "outcomes": fig_outcomes, "itemnull": fig_itemnull, "controls": fig_controls,
       "heatmap": fig_heatmap, "gap": fig_gap}


def build_all(only=None) -> list[str]:
    return [f() for k, f in ALL.items() if not only or k in only]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    print("\n".join(build_all(ap.parse_args().only)))
