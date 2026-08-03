"""Phase 2 sensitivity: robustness of the θ_P partition to analysis choices.

Each block refits the crossed REML and records the shares. Outputs under
results/phase2/sensitivity/:
    trait_definition.csv    acc vs acc_norm variants (needs phase2_eval_results.csv)
    leave_one_family.csv    drop each family in turn
    leaked_drop.csv         full design vs dropping cross-lab teacher-leak models
    lxe.csv                 + family x era cell component (fit_lpm_vcomp_cells)
    subject_drop.csv        drop each MMLU subject group in turn (needs samples)
    kim_crosscheck.csv      fresh acc vs Kim et al. leaderboard acc for the
                            18 reconciled models (SANITY CHECK, not validation)

Missing inputs (eval CSV / samples) degrade gracefully to a note, so the
pipeline can be dry-run on a synthetic trait table.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from . import estimator
from .phase2_metadata import LEAKED_MODELS
from .phase2_model import shares_of

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# MMLU subject -> group tag, loaded from the installed lm_eval task yamls.
SUBJECT_GROUP: dict[str, str] = {
    "abstract_algebra": "stem", "anatomy": "other", "astronomy": "stem",
    "business_ethics": "other", "clinical_knowledge": "other",
    "college_biology": "stem", "college_chemistry": "stem",
    "college_computer_science": "stem", "college_mathematics": "stem",
    "college_medicine": "other", "college_physics": "stem",
    "computer_security": "stem", "conceptual_physics": "stem",
    "econometrics": "social_sciences", "electrical_engineering": "stem",
    "elementary_mathematics": "stem", "formal_logic": "humanities",
    "global_facts": "other", "high_school_biology": "stem",
    "high_school_chemistry": "stem", "high_school_computer_science": "stem",
    "high_school_european_history": "humanities", "high_school_geography": "social_sciences",
    "high_school_government_and_politics": "social_sciences",
    "high_school_macroeconomics": "social_sciences", "high_school_mathematics": "stem",
    "high_school_microeconomics": "social_sciences", "high_school_physics": "stem",
    "high_school_psychology": "social_sciences", "high_school_statistics": "stem",
    "high_school_us_history": "humanities", "high_school_world_history": "humanities",
    "human_aging": "other", "human_sexuality": "social_sciences",
    "international_law": "humanities", "jurisprudence": "humanities",
    "logical_fallacies": "humanities", "machine_learning": "stem",
    "management": "other", "marketing": "other", "medical_genetics": "other",
    "miscellaneous": "other", "moral_disputes": "humanities",
    "moral_scenarios": "humanities", "nutrition": "other", "philosophy": "humanities",
    "prehistory": "humanities", "professional_accounting": "other",
    "professional_law": "humanities", "professional_medicine": "other",
    "professional_psychology": "social_sciences", "public_relations": "social_sciences",
    "security_studies": "social_sciences", "sociology": "social_sciences",
    "us_foreign_policy": "social_sciences", "virology": "other",
    "world_religions": "humanities",
}


def _share_row(prefix: str, fit: estimator.FitResult) -> dict:
    sh = shares_of(fit)
    return {"label": prefix, "share_family": sh["family"],
            "share_era": sh["era"], "share_unique": sh["unique"],
            "converged": fit.converged}


def _fit(df: pd.DataFrame) -> estimator.FitResult:
    return estimator.fit_lpm_vcomp(df)


def leave_one_family(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fam in sorted(df["family"].unique()):
        sub = df[df["family"] != fam]
        rows.append({"dropped_family": fam, **_share_row(f"leave-out {fam}", _fit(sub))})
    return pd.DataFrame(rows)


def leaked_drop(df: pd.DataFrame) -> pd.DataFrame:
    full = _share_row("full", _fit(df))
    sub = df[~df["full_name"].isin(LEAKED_MODELS)] if "full_name" in df else df
    rows = [full, _share_row("without-leaked", _fit(sub))]
    return pd.DataFrame(rows)


def lxe(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["cell"] = list(zip(d["family"], d["era"]))
    fit = estimator.fit_lpm_vcomp_cells(d)
    tot = sum(fit.s2.values())
    return pd.DataFrame([{
        "component": k, "variance": fit.s2[k],
        "share": fit.s2[k] / tot if tot > 0 else 0.0,
        "converged": fit.converged,
    } for k in fit.s2])


def subject_drop(df: pd.DataFrame, samples: pd.DataFrame,
                 out: Path) -> pd.DataFrame | None:
    if samples.empty or "subject" not in samples.columns:
        print("  (subject_drop skipped: no question samples)", file=__import__("sys").stderr)
        return None
    g = samples.groupby(["full_name", "subject"])["correct"].mean()
    rows = []
    for group in sorted(set(SUBJECT_GROUP.values())):
        subjects = {s for s, grp in SUBJECT_GROUP.items() if grp == group}
        sub_df = df.copy()
        kept = []
        for _, r in sub_df.iterrows():
            vals = [g.get((r["full_name"], s)) for s in subjects]
            vals = [v for v in vals if v is not None and v == v]
            kept.append(float(np.mean(vals)) if vals else float("nan"))
        sub_df["trait"] = kept
        sub_df = sub_df.dropna(subset=["trait"])
        if len(sub_df) < 2 or sub_df["family"].nunique() < 2:
            print(f"  (subject_drop: group {group} leaves {len(sub_df)} models; "
                  "skipped)", file=__import__("sys").stderr)
            continue
        rows.append({"dropped_group": group, **_share_row(group, _fit(sub_df))})
    return pd.DataFrame(rows)


def trait_definition(df: pd.DataFrame, eval_csv: Path) -> pd.DataFrame | None:
    if not eval_csv.exists():
        return None
    ev = pd.read_csv(eval_csv)
    if "acc_norm" not in ev.columns:
        return None
    d = df[["full_name", "family", "era"]].merge(
        ev[["full_name", "acc", "acc_norm"]], on="full_name", how="left").dropna()
    d2 = d.copy()
    d2["trait"] = d["acc_norm"]
    d["trait"] = d["acc"]
    return pd.DataFrame([_share_row("acc", _fit(d)),
                         _share_row("acc_norm", _fit(d2))])


def kim_crosscheck(df: pd.DataFrame) -> pd.DataFrame:
    from . import phase2_data
    kim = phase2_data.load_kim_data()
    rec = phase2_data.reconcile(kim)
    rec = rec[["full_name", "accuracy"]].rename(columns={"accuracy": "kim_acc"})
    merged = df.merge(rec, on="full_name", how="inner")
    merged = merged[merged["kim_acc"].notna()].copy()
    if merged.empty:
        return merged
    merged["delta"] = merged["trait"] - merged["kim_acc"]
    return merged


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--df", default=None,
                   help="trait table CSV; default results/phase2/trait_table.csv")
    p.add_argument("--eval-csv", default=None)
    p.add_argument("--out-dir", default="results/phase2")
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sens = out_dir / "sensitivity"
    sens.mkdir(parents=True, exist_ok=True)

    path = Path(args.df) if args.df else out_dir / "trait_table.csv"
    if not path.exists():
        p.error(f"{path} not found (run phase2_trait first)")
    df = pd.read_csv(path)

    from .phase2_trait import DATASETS, load_question_samples
    samples = load_question_samples()

    done = []
    t = trait_definition(df, Path(args.eval_csv) if args.eval_csv
                         else DATASETS / "phase2_eval_results.csv")
    if t is None:
        print("  (trait_definition skipped: no eval CSV with acc_norm)",
              file=__import__("sys").stderr)
    else:
        t.to_csv(sens / "trait_definition.csv", index=False)
        done.append("trait_definition")

    leave_one_family(df).to_csv(sens / "leave_one_family.csv", index=False)
    done.append("leave_one_family")
    leaked_drop(df).to_csv(sens / "leaked_drop.csv", index=False)
    done.append("leaked_drop")
    lxe(df).to_csv(sens / "lxe.csv", index=False)
    done.append("lxe")

    sd = subject_drop(df, samples, sens)
    if sd is not None:
        sd.to_csv(sens / "subject_drop.csv", index=False)
        done.append("subject_drop")

    kc = kim_crosscheck(df)
    if not kc.empty:
        kc.to_csv(sens / "kim_crosscheck.csv", index=False)
        done.append("kim_crosscheck")
    else:
        print("  (kim_crosscheck skipped: no overlap models in trait table)",
              file=__import__("sys").stderr)

    print("Sensitivity blocks:", ", ".join(done) if done else "(none)")
    print(f"-> {sens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
