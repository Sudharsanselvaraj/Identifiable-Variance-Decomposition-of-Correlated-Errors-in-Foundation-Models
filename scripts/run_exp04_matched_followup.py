#!/usr/bin/env python3
"""Exp04 post hoc (fourth review): accuracy-matched pairs, composition and S1.

The accuracy-matched analysis of R7 (pairs with |acc_i - acc_j| <= 0.02, decile
accuracy cells) gives a positive same-month coefficient (+3.3 points, primary).
The review asked whether near-chance models drive it and whether it survives
the option-distribution covariate S1. For each sample (primary, expanded; all
models and accuracy >= 0.30) this script reports

  R13a  composition of the matched pairs: both models below 0.30, mean pair
        accuracy quartiles, share with both uploads before 2024
  R13b  the matched model as in R7, then with the S1 covariate (total-variation
        distance between the two models' chosen-option distributions)

Same code paths as R7 (scripts/run_exp04_revision3.py); delete-one-root
jackknife SEs. Usage (repo root): python3 scripts/run_exp04_matched_followup.py
Outputs: results/exp04_revision3/R13.csv, info_R13.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lineage_era.ollb import analysis as A  # noqa: E402
from run_exp04_final import prepared  # noqa: E402
from run_exp04_revision3 import OUT, SAMPLES, acc_cells, jk_fit, row, tag  # noqa: E402


def main() -> int:
    rows, info = [], {}
    for pop, m in SAMPLES:
        d, t = prepared(pop, min_acc=m), tag(pop, m)
        X, y, names, i, j, acc = d["X"], d["y"], d["names"], d["i"], d["j"], d["acc"]
        base = [k for k, n in enumerate(names) if not n.startswith("acc")]
        close = np.abs(acc[i] - acc[j]) <= 0.02
        ic, jc = i[close], j[close]
        macc = (acc[ic] + acc[jc]) / 2
        year = pd.PeriodIndex(d["pop"].created_month, freq="M").year.to_numpy()
        info[t] = {
            "matched_pairs": int(close.sum()),
            "same_root_pairs": int((d["rid"][ic] == d["rid"][jc]).sum()),
            "share_both_below_0.30": float(((acc[ic] < 0.30) & (acc[jc] < 0.30)).mean()),
            "mean_accuracy_quartiles": [float(q) for q in np.percentile(macc, [25, 50, 75])],
            "share_both_uploaded_before_2024": float(((year[ic] < 2024) & (year[jc] < 2024)).mean()),
            "same_month_pairs": int((d["X"][close][:, names.index("gap0")] == 1).sum()),
        }
        Z = np.column_stack([X[:, base], acc_cells(acc, i, j, 10)])
        tv = A.position_tv(d["pred"], i, j)
        for label, ZZ in (("accuracy-matched pairs + decile cells (R7)", Z),
                          ("accuracy-matched pairs + decile cells + S1", np.column_stack([Z, tv]))):
            Zc = ZZ[close]
            keep = np.abs(Zc).sum(0) > 0
            b, se = jk_fit(Zc[:, keep], y[close], {**d, "i": ic, "j": jc})
            for term in ("same_root", "gap0"):
                k = names.index(term)
                rows.append(row("R13", label, t, term, b[k], se[k],
                                {"pairs": int(close.sum())}))
        print(f"R13 {t} done", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "R13.csv", index=False)
    (OUT / "info_R13.json").write_text(json.dumps(info, indent=1))
    print(pd.DataFrame(rows)[["analysis", "sample", "term", "estimate", "ci95_low",
                              "ci95_high"]].to_string(index=False))
    print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
