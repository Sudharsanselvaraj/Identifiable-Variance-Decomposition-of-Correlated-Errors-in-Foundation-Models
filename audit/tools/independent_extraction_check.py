#!/usr/bin/env python3
"""Audit Phase 2/8: independent re-extraction of raw leaderboard files.

Does NOT use lineage_era.ollb.fetch_v1. For a few models it downloads the public
per-subject parquet files, computes argmax(per-choice log-likelihoods) with its
own code, and compares row by row with the stored answer file datasets/ollb/v1/*.npz
(prediction, item order, gold) and with the leaderboard's stored per-item accuracy.
The raw files are cached under a temporary directory outside the repository.
"""
import ast
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[2]
ORG = "open-llm-leaderboard-old"
CACHE = Path(tempfile.gettempdir()) / "audit_hf_cache"


def subject(path):
    return re.search(r"hendrycksTest-(.*?)\|5", path).group(1)


def run_of(path):
    return re.search(r"(\d{4}-\d{2}-\d{2}T[\d:.\-]+)", path).group(1)


def check(repo, ref_gold):
    api = HfApi()
    files = [f for f in api.list_repo_files(f"{ORG}/{repo}", repo_type="dataset")
             if f.endswith(".parquet") and "hendrycksTest-" in f and "|5_" in f]
    runs = defaultdict(dict)
    for f in files:
        runs[run_of(f)][subject(f)] = f
    complete = {r: s for r, s in runs.items() if len(s) == 57}
    z = np.load(ROOT / "datasets/ollb/v1" / (repo.removeprefix("details_") + ".npz"))
    item, pred_st, gold_st = z["item"], z["pred"], z["gold"]
    pos = {}   # stored items are "subject:row"
    for k, it in enumerate(item):
        s, r = it.rsplit(":", 1); pos[(s, int(r))] = k
    n = mism_pred = mism_acc = mism_gold = layouts = 0
    best = None
    for run, subs in complete.items():
        rows = 0
        mp = ma = mg = 0
        for s, f in sorted(subs.items()):
            p = hf_hub_download(f"{ORG}/{repo}", f, repo_type="dataset", cache_dir=CACHE)
            t = pq.read_table(p)
            cols = t.column_names
            preds = t["predictions"].to_pylist()
            if "acc" in cols:
                str_layout = isinstance(t["acc"].to_pylist()[0], str)
                if str_layout:
                    preds = [ast.literal_eval(x) for x in preds]
                    gold = [int(g) for g in t["gold"].to_pylist()]
                    acc = [float(a) for a in t["acc"].to_pylist()]
                else:
                    gold = t["gold"].to_pylist(); acc = t["acc"].to_pylist()
            else:
                gold = list(ref_gold[s]); acc = [m["acc"] for m in t["metrics"].to_pylist()]
            for r_, (pl, g, a) in enumerate(zip(preds, gold, acc)):
                mine = int(np.argmax(np.asarray(pl, dtype=float)))
                k = pos[(s, r_)]
                mp += mine != pred_st[k]
                ma += float(mine == g) != float(a)
                mg += g != gold_st[k]
                rows += 1
        if best is None or rows > best[0]:
            best = (rows, run, mp, ma, mg)
    return {"repo": repo, "complete_runs": len(complete), "rows_in_longest_run": best[0], "run_used": best[1],
            "stored_run": str(z["run"]), "pred_mismatch_vs_stored": int(best[2]),
            "correctness_mismatch_vs_leaderboard_acc": int(best[3]), "gold_mismatch_vs_stored": int(best[4]),
            "my_accuracy": None}


def reference_gold():
    api = HfApi()
    repo = "details_meta-llama__Llama-2-7b-hf"
    z = np.load(ROOT / "datasets/ollb/v1/meta-llama__Llama-2-7b-hf.npz")
    g = defaultdict(dict)
    for it, gd in zip(z["item"], z["gold"]):
        s, r = it.rsplit(":", 1); g[s][int(r)] = int(gd)
    return {s: [d[i] for i in range(len(d))] for s, d in g.items()}


if __name__ == "__main__":
    repos = sys.argv[1:] or ["details_01-ai__Yi-9B-200K",
                             "details_PY007__TinyLlama-1.1B-intermediate-step-240k-503b",
                             "details_qualis2006__llama-2-7b-int4-python-code-18k"]
    rg = reference_gold()
    for r in repos:
        print(check(r, rg), flush=True)
