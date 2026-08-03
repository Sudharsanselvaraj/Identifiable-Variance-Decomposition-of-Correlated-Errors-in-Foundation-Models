"""Phase 2 tables: summary CSV and markdown table blocks for the report.

Produces results/phase2/results_summary.csv (one-row key quantities) and
results/phase2/tables.md (markdown blocks the report embeds).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


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


def main(argv: list[str] | None = None) -> int:
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
