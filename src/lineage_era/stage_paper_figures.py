"""Stage pipeline figures into docs/07_Paper/figs/ as PNG candidates.

Maps the Phase 2 pipeline outputs (results/<dir>/figures/*.pdf) and the
deterministic G3 trace to the manuscript's five figure slots. The manuscript
keeps referencing figs/fig_placeholder.png until the authors wire their final
artwork in (see docs/07_Paper/Figures.md); this script produces the candidate
PNGs so that step is a file swap.

Mappings:
    figures/design_heatmap.pdf  -> fig_design.png    (F2)
    figures/variance_shares.pdf -> fig_partition.png (F5)
    figures/error_heatmap.pdf   -> fig_similarity.png(F4)
    g3_report.md trace (drawn)  -> fig_g3_trace.png  (F3)
    (F1 causal DAG is author schematic art - not auto-generated)

Usage (from src/):
    python3 -m lineage_era.stage_paper_figures --results-dir results/phase2
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
FIGS_DIR = REPO_ROOT / "docs" / "07_Paper" / "figs"
G3_REPORT = REPO_ROOT / "datasets" / "coverage" / "g3_report.md"

RENDER_DPI = 150

MAPPING = {
    "design_heatmap.pdf": "fig_design.png",
    "variance_shares.pdf": "fig_partition.png",
    "error_heatmap.pdf": "fig_similarity.png",
}


def pdf_to_png(pdf: Path, out: Path) -> None:
    tmp = out.with_suffix("")
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(RENDER_DPI), str(pdf), str(tmp)],
        check=True, capture_output=True,
    )
    rendered = out.parent / f"{out.stem}-{RENDER_DPI}.png"
    if not rendered.exists():
        rendered = next(out.parent.glob(f"{out.stem}-*.png"))
    rendered.replace(out)


def g3_trace_png(out: Path) -> None:
    """Draw the deterministic G3 trace: confirmation era-share bias vs n."""
    rows = []
    for line in G3_REPORT.read_text().splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|.*?\|\s*([\d.-]+|\-)\s*\|\s*([\d.-]+|\-)\s*\|$", line)
        if not m:
            continue
        n, a_conf, b_conf = int(m.group(1)), m.group(2), m.group(3)
        if a_conf == "-" and b_conf == "-":
            continue
        rows.append((n, a_conf, b_conf))

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.axhspan(-4.0, 4.0, color="#c8e6c9", alpha=0.5,
               label="confirmation band (|bias| \u2264 4.0pp)")
    ax.axhline(0, color="grey", lw=0.6)
    for i, (n, a_conf, b_conf) in enumerate(rows):
        x = n + 0.12 * (i % 3) - 0.12
        if b_conf != "-":
            color = "#4caf50" if abs(float(b_conf)) <= 4.0 else "#e53935"
            ax.scatter(x, float(b_conf), marker="o", s=45, color=color,
                       edgecolors="black", linewidths=0.6, zorder=3)
        if a_conf != "-":
            ax.scatter(x, float(a_conf), marker="^", s=40, color="white",
                       edgecolors="black", linewidths=0.7, zorder=3,
                       facecolors="none")
    for n, label in [(47, "baseline\nPASS"), (21, "n0=21\nFAIL"), (22, "winner\nPASS")]:
        ax.axvline(n, color="grey", lw=0.7, ls=":", alpha=0.7)
        ax.annotate(label, (n, 4.6), ha="center", fontsize=8, color="#333333")
    ax.set_xlabel("population size n")
    ax.set_ylabel("confirmation era-share bias (pp)")
    ax.set_title("G3 decision trace: era-share bias at 1000-rep confirmation "
                 "(o = scenario B, ^ = scenario A)")
    ax.set_xlim(18, 50)
    ax.set_ylim(-6.5, 6.0)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-dir", default="results/phase2")
    p.add_argument("--figs-dir", default=str(FIGS_DIR))
    args = p.parse_args(argv)

    figs_dir = Path(args.figs_dir)
    figs_dir.mkdir(parents=True, exist_ok=True)
    results = Path(args.results_dir)
    figures = results / "figures"

    done: list[str] = []
    missing: list[str] = []
    for pdf_name, png_name in MAPPING.items():
        pdf = figures / pdf_name
        if pdf.exists():
            pdf_to_png(pdf, figs_dir / png_name)
            done.append(png_name)
        else:
            missing.append(pdf_name)

    if G3_REPORT.exists():
        g3_trace_png(figs_dir / "fig_g3_trace.png")
        done.append("fig_g3_trace.png")
    else:
        missing.append("g3_report.md")

    if shutil.which("pdftoppm") is None:
        print("WARNING: pdftoppm not found; PDF->PNG skipped", file=sys.stderr)

    print(f"staged into {figs_dir}: {', '.join(sorted(done))}")
    if missing:
        print(f"not produced (real-data pass pending): {', '.join(sorted(missing))}")
    print("NOTE: manuscript.tex still references figs/fig_placeholder.png; "
          "wire these in only when final artwork is ready (Figures.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
