#!/usr/bin/env python3
"""Audit Phase 0: programmatic inventory of every tracked file.

Writes audit/PROJECT_INVENTORY.csv. Classification is by path rules (first match
wins) and is an audit judgement, verified for the key rows by the later phases;
provenance (last commit, first commit date) comes from git.
Read-only with respect to the repository.
"""
import csv
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# (prefix or exact path, purpose, status, feeds_reported_results, kind, regenerable, depends_on)
R = [
    ("paper/src/ieee_access_manuscript.tex", "IEEE Access manuscript source", "CURRENT", "states results", "manual", "n/a", "paper/figures, paper/tables, paper/support"),
    ("paper/src/supplement.tex", "Supplementary material source", "CURRENT", "states results", "manual", "n/a", "paper/figures, paper/tables"),
    ("paper/src/archive/", "Earlier 16-model manuscript (withdrawn)", "OBSOLETE (withdrawn)", "no", "manual", "n/a", "-"),
    ("paper/build/", "Built PDFs of the current manuscript/supplement", "CURRENT (generated)", "states results", "generated", "make -C paper", "paper/src, paper/figures, paper/tables"),
    ("paper/figures/", "Figure PDFs of the current paper", "CURRENT (generated)", "plots results", "generated", "scripts/make_exp04_figures.py (14/20 from results/ alone; 6 need item-level data)", "results/, datasets/ollb/v1 (6 figs)"),
    ("paper/tables/", "LaTeX table bodies of the current paper", "CURRENT (generated)", "tabulates results", "generated", "scripts/make_exp04_tables.py from results/ alone", "results/"),
    ("paper/support/", "IEEE Access class, fonts, logos (third-party template files)", "CURRENT (template)", "no", "third-party", "n/a", "-"),
    ("paper/Makefile", "Manuscript build", "CURRENT", "no", "manual", "n/a", "-"),
    ("master/src/", "Generated single-column manuscript", "CURRENT (generated)", "states results", "generated", "scripts/make_master_manuscript.py", "paper/src/ieee_access_manuscript.tex"),
    ("master/build/", "Single-column PDF", "CURRENT (generated)", "states results", "generated", "make -C master", "master/src"),
    ("master/archive/", "Earlier single-column 16-model manuscript (withdrawn)", "OBSOLETE (withdrawn)", "no", "manual", "n/a", "-"),
    ("master/", "Single-column build files", "CURRENT", "no", "manual", "n/a", "-"),
    ("src/lineage_era/ollb/", "Current-study package: roster, fetch, analysis, pair-gate", "CURRENT", "YES (primary analysis)", "manual", "n/a", "datasets/ollb, results/exp04_validation"),
    ("src/lineage_era/test_ollb_analysis.py", "Tests of the current analysis, validation gate, bootstrap", "CURRENT", "supports", "manual", "n/a", "src/lineage_era/ollb"),
    ("src/lineage_era/test_precision_gate.py", "Tests of the per-model precision gate (S1)", "CURRENT (supplement S1)", "supports S1", "manual", "n/a", "src/lineage_era/analysis"),
    ("src/lineage_era/analysis/precision_gate.py", "Per-model precision simulation (S1)", "CURRENT (supplement S1)", "S1 only", "manual", "n/a", "-"),
    ("src/lineage_era/analysis/reml.py", "REML variance components (S1)", "CURRENT (supplement S1)", "S1 only", "manual", "n/a", "-"),
    ("src/lineage_era/analysis/", "Earlier per-model variance-decomposition code", "LEGACY (earlier study)", "no (S1 uses precision_gate/reml only)", "manual", "n/a", "-"),
    ("src/lineage_era/phase2_", "Earlier per-model evaluation pipeline", "LEGACY (earlier study)", "no", "manual", "n/a", "-"),
    ("src/lineage_era/test_", "Tests of legacy modules", "LEGACY tests", "no", "manual", "n/a", "-"),
    ("src/lineage_era/", "Earlier-study modules", "LEGACY (earlier study)", "no", "manual", "n/a", "-"),
    ("src/results/", "Dry-run outputs of the earlier study (simulated data)", "OBSOLETE (earlier study, simulated)", "no", "generated", "no", "-"),
    ("src/", "Package scaffold", "CURRENT", "no", "manual", "n/a", "-"),
    ("scripts/run_exp04_", "Current-study analysis scripts", "CURRENT", "YES", "manual", "n/a", "datasets/ollb, results/"),
    ("scripts/validation_report.py", "Validation manifest (gate input)", "CURRENT", "YES (gate)", "manual", "n/a", "datasets/ollb/v1"),
    ("scripts/download_ollb_v1.py", "Answer-file download", "CURRENT", "YES (inputs)", "manual", "needs network", "datasets/ollb/frozen_full"),
    ("scripts/fetch_v1_contents_meta.py", "Leaderboard metadata fetch", "CURRENT", "YES (inputs)", "manual", "needs network", "-"),
    ("scripts/rebuild_frozen_lists.py", "Rebuild and hash-check frozen lists", "CURRENT", "YES (inputs)", "manual", "needs network", "-"),
    ("scripts/compare_rosters.py", "Roster comparison", "CURRENT", "inputs", "manual", "n/a", "-"),
    ("scripts/make_exp04_", "Figure and table generation", "CURRENT", "plots/tabulates", "manual", "n/a", "results/"),
    ("scripts/make_master_manuscript.py", "Generates single-column manuscript", "CURRENT", "no", "manual", "n/a", "-"),
    ("scripts/make_submission_package.py", "Packaging helper", "CURRENT (not part of results)", "no", "manual", "n/a", "-"),
    ("scripts/run_pair_gate", "Pre-outcome simulation check", "CURRENT", "YES (design check)", "manual", "n/a", "-"),
    ("scripts/run_precision_", "Per-model precision simulation (S1)", "CURRENT (supplement S1)", "S1 only", "manual", "n/a", "-"),
    ("scripts/run_design_space_sweep.py", "Earlier-study design sweep", "LEGACY (earlier study)", "no", "manual", "n/a", "-"),
    ("scripts/regen_figs_8_9.py", "Earlier-study figure regeneration", "LEGACY (earlier study)", "no", "manual", "n/a", "-"),
    ("scripts/", "Scripts", "CHECK", "?", "manual", "?", "-"),
    ("results/exp04_validation/", "Validation manifest and report", "CURRENT", "YES (gate input)", "generated", "scripts/validation_report.py (needs item-level data)", "datasets/ollb/v1"),
    ("results/exp04_rosters/", "Roster hashes and comparison", "CURRENT", "YES (sample freeze)", "generated", "scripts/rebuild_frozen_lists.py", "network"),
    ("results/exp04_analysis/", "The 12 analyses fixed before any outcome", "CURRENT (first pair outcomes)", "YES (headline)", "generated", "python -m lineage_era.ollb.analysis", "validated answer files"),
    ("results/exp04_final/", "Reproduction, inference and outcome audits", "CURRENT", "YES (headline, intervals)", "generated", "scripts/run_exp04_final.py", "validated answer files"),
    ("results/exp04_item_null/", "Item-difficulty-aware nulls (post hoc)", "CURRENT (post hoc)", "YES", "generated", "scripts/run_exp04_item_null.py", "validated answer files"),
    ("results/exp04_revision2/", "Second-review analyses (post hoc)", "CURRENT (post hoc)", "YES", "generated", "scripts/run_exp04_revision2.py", "validated answer files"),
    ("results/exp04_revision3/", "Third/fourth-review analyses R7-R13 (post hoc)", "CURRENT (post hoc)", "YES", "generated", "scripts/run_exp04_revision3.py, run_exp04_matched_followup.py", "validated answer files, datasets/mmlu_redux"),
    ("results/exp04_heterogeneity/", "Heterogeneity and lineage detection (post hoc)", "CURRENT (post hoc)", "YES", "generated", "scripts/run_exp04_heterogeneity.py", "validated answer files"),
    ("results/pair_gate", "Pre-outcome simulation check and 500-replicate audit", "CURRENT", "design check", "generated", "scripts/run_pair_gate*.py", "-"),
    ("results/precision_gate/", "Per-model precision simulation (S1)", "CURRENT (supplement S1)", "S1 only", "generated", "scripts/run_precision_*.py", "-"),
    ("results/phase2_empirical/", "Invalid earlier per-model outputs", "OBSOLETE (invalid)", "no", "generated", "no", "-"),
    ("results/design_space/", "Earlier-study design sweep", "OBSOLETE (earlier study)", "no", "generated", "no", "-"),
    ("results/", "Results", "CHECK", "?", "generated", "?", "-"),
    ("datasets/ollb/frozen/", "Frozen roster lists (compact) with hashes", "CURRENT", "YES (sample)", "generated", "scripts/rebuild_frozen_lists.py", "network"),
    ("datasets/ollb/", "Leaderboard-derived inputs and logs", "CURRENT", "YES (inputs)", "generated", "network", "-"),
    ("datasets/eval_samples.sim", "Simulated per-question files (earlier-study dry run)", "OBSOLETE (earlier study, simulated)", "no", "generated", "no", "-"),
    ("datasets/eval_samples", "Invalid per-question files of the earlier per-model evaluation", "OBSOLETE (invalid)", "no", "generated", "no", "-"),
    ("datasets/phase2_eval_results.sim.csv", "Simulated results (earlier-study dry run)", "OBSOLETE (earlier study, simulated)", "no", "generated", "no", "-"),
    ("datasets/phase2_eval_results.csv", "Recorded aggregates of the invalid earlier evaluation", "OBSOLETE (invalid)", "no", "generated", "no", "-"),
    ("datasets/phase2_coverage.csv", "Earlier-study coverage table", "LEGACY (earlier study)", "no", "manual", "n/a", "-"),
    ("pyproject.toml", "Package metadata and pytest config", "CURRENT", "no", "manual", "n/a", "-"),
    ("requirements.txt", "Dependency list", "CURRENT", "no", "manual", "n/a", "-"),
    (".gitignore", "Ignore rules", "CURRENT", "no", "manual", "n/a", "-"),
    ("IEEEtran.cls", "Third-party IEEE class at repository root", "CURRENT (template)", "no", "third-party", "n/a", "-"),
    ("datasets/.gitkeep", "Placeholder", "CURRENT", "no", "manual", "n/a", "-"),
    ("notebooks/.gitkeep", "Placeholder", "CURRENT", "no", "manual", "n/a", "-"),
    ("datasets/coverage/", "Earlier-study population and plan files", "LEGACY (earlier study)", "no (S7/S1 labels only)", "manual", "n/a", "-"),
    ("datasets/kim/", "Public data of Kim et al. used for metadata name matching", "CURRENT (third-party)", "inputs", "third-party", "n/a", "-"),
    ("datasets/", "Datasets", "CHECK", "?", "?", "?", "-"),
    ("docs/05_Experiments/Exp04", "Dated analysis plan and three amendments", "CURRENT", "design record", "manual", "n/a", "-"),
    ("docs/REPRODUCIBILITY_CHECKLIST.md", "Reproduction runbook", "CURRENT", "no", "manual", "n/a", "-"),
    ("docs/release/", "Licensing notes", "CURRENT", "no", "manual", "n/a", "-"),
    ("docs/08_Reviews/", "Review and audit records", "CURRENT (records)", "no", "manual", "n/a", "-"),
    ("docs/archive/", "Earlier-study runbook", "OBSOLETE (earlier study)", "no", "manual", "n/a", "-"),
    ("docs/assets/", "README images", "CURRENT (generated)", "plots results", "generated", "scripts/make_exp04_figures.py --readme", "results/"),
    ("docs/07_Paper/", "Old paper and IEEE support of the earlier study", "OBSOLETE (withdrawn)", "no", "manual", "n/a", "-"),
    ("docs/", "Earlier-study documents (superseded banner added)", "OBSOLETE (earlier study)", "no", "manual", "n/a", "-"),
    ("README.md", "Repository landing page", "CURRENT", "states results", "manual", "n/a", "-"),
    ("RESEARCH_STATUS.md", "Current vs withdrawn map", "CURRENT", "no", "manual", "n/a", "-"),
]


def classify(p):
    for pre, *rest in R:
        if p == pre or p.startswith(pre):
            return rest
    return ["No rule", "CHECK", "?", "?", "?", "?"]


def main():
    last, first = {}, {}
    out = subprocess.run(["git", "log", "--format=@%h %cs", "--name-only"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    cur = None
    for line in out.splitlines():
        if line.startswith("@"):
            cur = line[1:].split()
        elif line.strip() and cur:
            last.setdefault(line, cur)
            first[line] = cur
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    rows = []
    for p in filter(None, files):
        fp = ROOT / p
        if not fp.exists():
            continue
        purpose, status, feeds, kind, regen, deps = classify(p)
        rows.append({"path": p, "purpose": purpose, "status": status,
                     "feeds_reported_results": feeds, "generated_or_manual": kind,
                     "regenerable": regen, "depends_on": deps,
                     "last_commit": " ".join(last.get(p, ["?", "?"])),
                     "first_commit_date": first.get(p, ["?", "?"])[1],
                     "bytes": fp.stat().st_size,
                     "sha256_16": hashlib.sha256(fp.read_bytes()).hexdigest()[:16]})
    with open(ROOT / "audit" / "PROJECT_INVENTORY.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    print(len(rows), "files"); [print(f"  {n:4d} {s}") for s, n in c.most_common()]
    print("unclassified:", [r["path"] for r in rows if r["status"] == "CHECK"][:10])


main()
