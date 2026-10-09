#!/usr/bin/env python3
"""Reconciled validation report for the Exp04 download (run before analysis).

Every model in the frozen download list (datasets/ollb/frozen/download_union.csv)
gets exactly one final category:

  validated        answer file present AND passes every file-level check below
  failed_check     answer file present but fails a file-level check (excluded)
  no_complete_run  leaderboard repo has no complete 57-subject MMLU run
  repo_missing     details repo deleted / not found
  acc_mismatch     extracted answers disagree with stored per-item correctness
  schema_error     unreadable layout
  unresolved       still erroring after the resumed pass, or never attempted

File-level checks (independent of the download log):
  * exactly 14,042 items;
  * item ids identical, in order, to the reference model (subject:position);
  * gold vector identical to the reference;
  * where the run stores item hashes, they equal the reference hashes;
  * predictions are valid options 0..3.
The per-item agreement with the leaderboard's stored correctness was enforced
at extraction (a file is only written when all 14,042 items agree).

Usage (repo root): python3 scripts/validation_report.py
Outputs: results/exp04_validation/{per_model.csv, report.md}
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "datasets" / "ollb" / "frozen"
ANS = ROOT / "datasets" / "ollb" / "v1"
LOG = ROOT / "datasets" / "ollb" / "fetch_v1_log.jsonl"
OUT = ROOT / "results" / "exp04_validation"
REF = ANS / "meta-llama__Llama-2-7b-hf.npz"
N_ITEMS = 14042


def last_log_status() -> dict[str, dict]:
    """Latest informative log record per repo ('cached' never overrides)."""
    out: dict[str, dict] = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r["status"] == "cached" and r["repo"] in out:
            continue
        out[r["repo"]] = r
    return out


def check_file(path: Path, ref) -> tuple[bool, str, dict]:
    z = np.load(path)
    info = {"schema": str(z["schema"]) if "schema" in z.files else "legacy",
            "run": str(z["run"]), "accuracy": float((z["pred"] == z["gold"]).mean())}
    if len(z["pred"]) != N_ITEMS:
        return False, f"items={len(z['pred'])}", info
    if not np.array_equal(z["item"], ref["item"]):
        return False, "item_order", info
    if not np.array_equal(z["gold"], ref["gold"]):
        return False, "gold", info
    h = z["hash"]
    if (h != "").all() and not np.array_equal(h, ref["hash"]):
        return False, "hash", info
    if z["pred"].min() < 0 or z["pred"].max() > 3:
        return False, "pred_range", info
    return True, "", info


def main() -> int:
    union = pd.read_csv(FROZEN / "download_union.csv")
    ref = np.load(REF)
    log = last_log_status()
    rows = []
    for r in union.itertuples(index=False):
        path = ANS / f"{r.repo.removeprefix('details_')}.npz"
        rec = {"repo": r.repo, "model": r.model,
               "in_primary_sample": r.in_primary_sample,
               "in_expanded_sample": r.in_expanded_sample}
        if path.exists():
            ok, why, info = check_file(path, ref)
            rec.update(info, category="validated" if ok else "failed_check",
                       detail=why, mb=round(path.stat().st_size / 1e6, 3))
        else:
            st = log.get(r.repo, {}).get("status", "never_attempted")
            cat = st if st in ("no_complete_run", "repo_missing", "acc_mismatch",
                               "schema_error") else "unresolved"
            rec.update(category=cat, detail=log.get(r.repo, {}).get("error", st))
        rows.append(rec)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "per_model.csv", index=False)

    def coverage(flag: str) -> pd.Series:
        return df[df[flag]].category.value_counts()

    v = df[df.category == "validated"]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    lines = [
        "# Exp04 download — reconciled validation report", "",
        f"Code commit: `{commit}`", "",
        f"Frozen download list: {len(df)} unique models "
        f"(primary sample {int(df.in_primary_sample.sum())}, "
        f"expanded sample {int(df.in_expanded_sample.sum())}).", "",
        "## Final category per model (each model counted once)", "",
        df.category.value_counts().to_frame("models").to_markdown(), "",
        "## Coverage of each frozen sample", "",
        pd.DataFrame({"primary_sample": coverage("in_primary_sample"),
                      "expanded_sample": coverage("in_expanded_sample")})
        .fillna(0).astype(int).to_markdown(), "",
        "## Validated files", "",
        f"- layouts: {v.schema.value_counts().to_dict()}",
        f"- storage: {v.mb.sum():.1f} MB in {len(v)} files",
        f"- accuracy: median {v.accuracy.median():.3f}, "
        f"{int((v.accuracy < 0.30).sum())} models below 0.30 (near chance; kept, "
        "flagged for the accuracy-control sensitivity check)", "",
        "## Not validated (documented exclusions, never replaced)", "",
        df[df.category != "validated"][["model", "category", "detail"]]
        .to_markdown(index=False) if (df.category != "validated").any() else "none",
    ]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:20]))
    return 0 if not (df.category == "unresolved").any() else 1


if __name__ == "__main__":
    sys.exit(main())
