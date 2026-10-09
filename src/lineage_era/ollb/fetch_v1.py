"""Fetch per-question MMLU predictions from the v1 Open LLM Leaderboard.

For each ``open-llm-leaderboard-old/details_<org>__<name>`` repo:

1. list the ``hendrycksTest-*|5`` parquet files and group them by run;
2. pick the run that covers all 57 subjects with the most rows (some runs
   are --limit partial runs; using one would silently shrink the item set);
3. read ONLY ``predictions`` (per-choice log-likelihoods), ``gold``, ``acc``
   and the item hash, via ranged reads (~13 MB per model instead of ~80 MB);
4. verify argmax(predictions) reproduces the stored ``acc`` on every item
   (the guard that would have caught the original resps[0] bug);
5. write ``datasets/ollb/v1/<org>__<name>.npz`` with item id, hash, predicted
   choice and gold. Existing files are skipped, so the job is resumable.

Usage (repo root):
    python3 -m lineage_era.ollb.fetch_v1 --models datasets/ollb/v1_roster.csv
    python3 -m lineage_era.ollb.fetch_v1 --repo details_meta-llama__Llama-2-7b-hf
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "datasets" / "ollb" / "v1"
ORG = "open-llm-leaderboard-old"
N_SUBJECTS = 57
COLUMNS = ["predictions", "gold", "acc", "hashes"]


def _run_of(path: str) -> str:
    return path.split("/")[3]


def _subject_of(path: str) -> str:
    return path.split("hendrycksTest-")[1].split("|")[0]


def fetch_model(repo: str, retries: int = 4) -> dict:
    """Fetch one model; returns a status record (never raises)."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    out = OUT / f"{repo.removeprefix('details_')}.npz"
    if out.exists():
        return {"repo": repo, "status": "cached"}
    fs = HfFileSystem()
    base = f"datasets/{ORG}/{repo}"
    for attempt in range(retries):
        try:
            files = fs.glob(base + "/**/*hendrycksTest-*|5_*.parquet")
            by_run = defaultdict(dict)
            for f in files:
                by_run[_run_of(f)][_subject_of(f)] = f
            complete = {r: s for r, s in by_run.items() if len(s) == N_SUBJECTS}
            if not complete:
                return {"repo": repo, "status": "no_complete_run",
                        "runs": len(by_run)}
            # Most rows wins; later run breaks ties.
            sizes = {}
            for r, subj in complete.items():
                any_file = next(iter(subj.values()))
                with fs.open(any_file, block_size=64 * 1024) as fh:
                    sizes[r] = pq.ParquetFile(fh).metadata.num_rows
            run = max(complete, key=lambda r: (sizes[r], r))

            items, hashes, pred, gold, n_bad = [], [], [], [], 0
            nbytes = 0
            for subj in sorted(complete[run]):
                with fs.open(complete[run][subj], block_size=64 * 1024,
                             cache_type="readahead") as fh:
                    t = pq.ParquetFile(fh).read(columns=COLUMNS)
                    nbytes += getattr(fh.cache, "total_requested_bytes", 0)
                for k, (p, g, a, h) in enumerate(zip(t["predictions"].to_pylist(),
                                      t["gold"].to_pylist(),
                                      t["acc"].to_pylist(),
                                      t["hashes"].to_pylist())):
                    choice = int(np.argmax(p)) if p else -1
                    n_bad += int(float(choice == g) != float(a))
                    # MMLU has 27 exact-duplicate questions, so the content
                    # hash is not unique; position within subject is the id
                    # and the hash is kept to verify alignment across models.
                    items.append(f"{subj}:{k}")
                    hashes.append(h["example"])
                    pred.append(choice)
                    gold.append(g)
            if n_bad:
                return {"repo": repo, "status": "acc_mismatch", "n_bad": n_bad,
                        "items": len(pred), "run": run}
            OUT.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out, item=np.array(items), hash=np.array(hashes), pred=np.array(pred, np.int8),
                                gold=np.array(gold, np.int8), run=run)
            return {"repo": repo, "status": "ok", "items": len(pred), "run": run,
                    "bytes": nbytes}
        except Exception as exc:  # network / throttling: back off and retry
            err = f"{type(exc).__name__}: {str(exc)[:160]}"
            time.sleep(min(120, 10 * 2 ** attempt))
    return {"repo": repo, "status": "error", "error": err}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", help="CSV with a 'repo' column (details_<org>__<name>)")
    ap.add_argument("--repo", action="append", default=[])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    repos = list(args.repo)
    if args.models:
        repos += pd.read_csv(args.models)["repo"].tolist()
    log = OUT.parent / "fetch_v1_log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    with ThreadPoolExecutor(args.workers) as pool, open(log, "a") as fh:
        futures = [pool.submit(fetch_model, r) for r in repos]
        for fut in as_completed(futures):
            rec = fut.result()
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            done += 1
            if done % 25 == 0 or done == len(repos):
                print(f"{done}/{len(repos)} last={rec['status']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
