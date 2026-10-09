#!/usr/bin/env python3
"""How many families/eras the precision gate needs.

Staggered designs with F in 6..60 and (E, M) in {(8, 4), (14, 6)}, 300 Monte
Carlo reps per scenario, scored with analysis.precision_gate.

Usage (repo root): python3 scripts/run_precision_scaling.py
Output: results/precision_gate/family_scaling.csv
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.analysis.precision_gate import precision_gate  # noqa: E402
from run_design_space_sweep import make_staggered  # noqa: E402


def main() -> int:
    rows = []
    for nf in [6, 10, 15, 20, 30, 40, 60]:
        for ne, m in [(8, 4), (14, 6)]:
            df = pd.DataFrame([(f"F{f}", f"E{e}") for f, eras in
                               enumerate(make_staggered(nf, m, ne)) for e in eras[:m]],
                              columns=["family", "era"])
            res = precision_gate(df, name=f"F{nf}_E{ne}_M{m}", reps=300)
            worst = res.rows[["rmse_share_family", "rmse_share_era"]].max()
            rows.append({"F": nf, "E": ne, "M": m, "N": len(df),
                         "worst_family": worst.iloc[0], "worst_era": worst.iloc[1],
                         "passes": res.reportable})
            print(rows[-1], flush=True)
    out = ROOT / "results" / "precision_gate" / "family_scaling.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
