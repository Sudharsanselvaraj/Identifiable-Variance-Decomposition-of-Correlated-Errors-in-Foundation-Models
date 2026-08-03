"""Phase 2 report + table blocks: assemble results/phase2/PHASE2_REPORT.md,
results_summary.csv, and tables.md (analysis/report.py).

Embeds the audit verdict, θ_P partition, bootstrap CIs, θ_M tables,
sensitivity summaries, and figure list. The Kim cross-check is framed as a
documented sanity check only (benchmark version / prompting differences may
explain deltas), never as validation. ``main`` builds the report;
``main_tables`` builds the summary CSV and markdown table blocks.
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd


def _fmt(v) -> str:
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    vp = pd.read_csv(out_dir / "variance_partition.csv").set_index("component")
    bc = pd.read_csv(out_dir / "bootstrap_ci.csv").set_index("component")
    fam = pd.read_csv(out_dir / "family_effects.csv")
    era = pd.read_csv(out_dir / "era_effects.csv")
    design = pd.read_csv(out_dir / "analysis_design.csv")
    audit_md = (out_dir / "identifiability_report.md").read_text()
    verdict = next(ln for ln in audit_md.splitlines() if ln.startswith("Verdict:"))
    tables = (out_dir / "tables.md").read_text()

    L, E, U = "family", "era", "unique"
    lines = [
        "# Phase 2 Report: Lineage vs Era Variance Decomposition",
        "",
        f"Generated: {date.today().isoformat()}  |  "
        f"Design: {len(design)} models, {design['family'].nunique()} families, "
        f"{design['era'].nunique()} quarters",
        "",
        f"**Identifiability audit:** {verdict}",
        "",
        "## θ_P — primary variance partition (fresh MMLU 5-shot trait)",
        "",
        tables,
        f"- Family share: {_fmt(vp.loc[L, 'share'])} "
        f"(delta CI {_fmt(bc.loc[L, 'share_lo'])}–{_fmt(bc.loc[L, 'share_hi'])}; "
        f"trait-error MC {_fmt(bc.loc[L, 'mc_lo'])}–{_fmt(bc.loc[L, 'mc_hi'])})",
        f"- Era share: {_fmt(vp.loc[E, 'share'])} "
        f"(delta CI {_fmt(bc.loc[E, 'share_lo'])}–{_fmt(bc.loc[E, 'share_hi'])}; "
        f"trait-error MC {_fmt(bc.loc[E, 'mc_lo'])}–{_fmt(bc.loc[E, 'mc_hi'])})",
        f"- Unique/residual share: {_fmt(vp.loc[U, 'share'])}",
        "",
        "## θ_M — mechanistic tables (reported separately, not part of θ_P)",
        "",
        "- `era_trend.csv`: mean trait and era BLUP per quarter.",
        "- `dense_cell_contrasts.csv`: family contrasts within the co-released "
        "quarters (2024Q2/Q3, 2025Q2).",
        "- `chain_slopes.csv`: per-quarter slope along the verified fine-tune "
        "edges (occupancy.VERIFIED_EDGES).",
        "",
        "## Sensitivity (results/phase2/sensitivity/)",
        "",
        "- `leave_one_family.csv`: share change when each family is dropped.",
        "- `leaked_drop.csv`: full design vs dropping cross-lab teacher-leak "
        "models (Phi-4 reasoners, Gemma-2-9B, Gemma-4).",
        "- `lxe.csv`: family x era cell variance component added.",
        "- `subject_drop.csv`: partition after dropping each MMLU subject group.",
        "- `trait_definition.csv`: acc vs acc_norm trait variants.",
        "- `kim_crosscheck.csv`: fresh acc vs Kim et al. leaderboard acc for the "
        "reconciled overlap (documented SANITY CHECK only — benchmark version, "
        "prompting, and few-shot protocols differ; deltas are expected and are "
        "not treated as validation).",
        "",
        "## Figures (results/phase2/figures/)",
        "",
    ]
    figs = sorted(p.name for p in (out_dir / "figures").glob("*.pdf"))
    lines += [f"- `{f}`" for f in figs] + [""]

    lines += ["## Caveats carried from Phase 0 (occupancy.CAVEATS)", ""]
    from ..occupancy import CAVEATS
    lines += [f"- {c}" for c in CAVEATS] + [""]
    lines += [
        "Small-sample limit: 6 family levels (df = 5) cap the family-share "
        "coverage below nominal; the SE-inflation detector is reported as a "
        "warning for this reason (see identifiability_report.md).",
        "",
    ]
    (out_dir / "PHASE2_REPORT.md").write_text("\n".join(lines))
    print(f"-> {out_dir / 'PHASE2_REPORT.md'}")
    return 0


# --------------------------------------------------------------- table blocks
# (formerly ``phase2_tables.py``; the report and its markdown/CSV tables share
# one module per the analysis/ layout).
def _md(df: pd.DataFrame, title: str, fmt: str | None = None) -> str:
    if df.empty:
        return ""
    d = df.copy()
    if fmt:
        for col in d.select_dtypes("number"):
            if col in fmt:
                d[col] = d[col].map(lambda v: f"{v:{fmt[col]}}")
    lines = [f"### {title}", "", d.to_markdown(index=False), ""]
    return "\n".join(lines)


def build_tables(out_dir: Path) -> str:
    parts = []
    vp = pd.read_csv(out_dir / "variance_partition.csv")
    parts.append(_md(vp, "θ_P variance partition (variance_partition.csv)",
                     {"variance": ".4f", "share": ".3f"}))
    bc = pd.read_csv(out_dir / "bootstrap_ci.csv")
    parts.append(_md(bc, "Bootstrap CIs (bootstrap_ci.csv)", {"share": ".3f"}))
    fam = pd.read_csv(out_dir / "family_effects.csv")
    parts.append(_md(fam, "Family effects (family_effects.csv)"))
    era = pd.read_csv(out_dir / "era_effects.csv")
    parts.append(_md(era, "Era effects (era_effects.csv)"))
    return "\n".join(p for p in parts if p)


def results_summary(out_dir: Path) -> pd.DataFrame:
    vp = pd.read_csv(out_dir / "variance_partition.csv").set_index("component")
    bc = pd.read_csv(out_dir / "bootstrap_ci.csv").set_index("component")
    fam = pd.read_csv(out_dir / "family_effects.csv")
    era = pd.read_csv(out_dir / "era_effects.csv")
    audit = pd.read_csv(out_dir / "vif.csv")
    cond_txt = (out_dir / "condition_number.txt").read_text().splitlines()[0]
    report = (out_dir / "identifiability_report.md").read_text().splitlines()
    verdict = next((ln for ln in report if ln.startswith("Verdict:")), "Verdict: UNKNOWN")
    row = {
        "audit": "PASS" if "**PASS**" in verdict else "ABORT",
        "n_models": int(pd.read_csv(out_dir / "trait_table.csv").shape[0]),
        "n_families": int(fam.shape[0]),
        "n_quarters": int(era.shape[0]),
        "share_family": vp.loc["family", "share"], "share_era": vp.loc["era", "share"],
        "share_unique": vp.loc["unique", "share"],
        "share_family_ci": f"[{bc.loc['family', 'share_lo']:.3f}, {bc.loc['family', 'share_hi']:.3f}]",
        "share_era_ci": f"[{bc.loc['era', 'share_lo']:.3f}, {bc.loc['era', 'share_hi']:.3f}]",
        "family_vs_era": "family" if vp.loc["family", "share"] >= vp.loc["era", "share"] else "era",
        "condition_number": cond_txt.split("=")[1].strip().split()[0],
        "max_vif": max(audit["max_vif"]),
    }
    return pd.DataFrame([row])


def main_tables(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results_summary(out_dir).to_csv(out_dir / "results_summary.csv", index=False)
    (out_dir / "tables.md").write_text(build_tables(out_dir))
    print(f"-> {out_dir / 'results_summary.csv'}")
    print(f"-> {out_dir / 'tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
