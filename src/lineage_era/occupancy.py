"""Phase 0 codification: verified occupancy design for the connected population.

Single source of truth for the family x quarter design used by D2 (realistic
occupancy) and by Phase 2 (the connected subset). Data is the HF-verified
contingency table logged in MASTER_PROMPT.md / proposal.md section 14
(2026-08-02). This module is OFFLINE: no network calls.

Distinguishing notes that bind downstream code:
- ``era`` is the PUBLIC RELEASE QUARTER, not HF ``createdAt`` (4 documented
  divergences in ``ERA_DIVERGENCES``).
- Cells hold model releases (1-3 per cell). The D2 regime copies this exact
  occupancy.
- The Llama row's ``(term.)`` cell is a note, not a model; it is excluded.
"""
from __future__ import annotations

import pandas as pd

FAMILIES = ["Llama", "Qwen", "DeepSeek", "Mistral", "Phi", "Gemma"]

QUARTERS = [
    "2023Q1", "2023Q2", "2023Q3", "2023Q4",
    "2024Q1", "2024Q2", "2024Q3", "2024Q4",
    "2025Q1", "2025Q2", "2025Q3", "2025Q4",
    "2026Q1", "2026Q2",
]

# (family, quarter, short_name, full_name) — copied verbatim from the
# Phase 0 contingency table. Abbreviations follow the table's key:
# L* = Llama, 4-r = Phi-4-reasoning-plus, 4-r-v = Phi-4-reasoning-vision-15B,
# Min3 = Ministral-3, Dev2 = Devstral-2.
MODELS = [
    # Llama
    ("Llama", "2023Q1", "L1", "Llama-1"),
    ("Llama", "2023Q3", "L2", "Llama-2"),
    ("Llama", "2024Q2", "L3", "Llama-3"),
    ("Llama", "2024Q3", "3.1", "Llama-3.1"),
    ("Llama", "2024Q3", "3.2", "Llama-3.2"),
    ("Llama", "2024Q4", "3.3", "Llama-3.3"),
    ("Llama", "2025Q2", "L4", "Llama-4"),
    # Qwen
    ("Qwen", "2023Q3", "7B", "Qwen-7B"),
    ("Qwen", "2024Q1", "1.5", "Qwen1.5"),
    ("Qwen", "2024Q2", "2", "Qwen2"),
    ("Qwen", "2024Q3", "2.5", "Qwen2.5"),
    ("Qwen", "2025Q2", "3", "Qwen3"),
    ("Qwen", "2026Q1", "3.5", "Qwen3.5"),
    ("Qwen", "2026Q2", "3.6", "Qwen3.6"),
    # DeepSeek
    ("DeepSeek", "2024Q4", "V3", "DeepSeek-V3"),
    ("DeepSeek", "2025Q1", "R1", "DeepSeek-R1"),
    ("DeepSeek", "2025Q3", "V3.1", "DeepSeek-V3.1"),
    ("DeepSeek", "2025Q4", "V3.2", "DeepSeek-V3.2"),
    ("DeepSeek", "2026Q2", "V4", "DeepSeek-V4"),
    # Mistral
    ("Mistral", "2023Q3", "7B", "Mistral-7B"),
    ("Mistral", "2023Q4", "Mixtral", "Mixtral-8x7B"),
    ("Mistral", "2024Q2", "8x22B", "Mixtral-8x22B"),
    ("Mistral", "2024Q3", "L2", "Mistral-Large-2"),
    ("Mistral", "2024Q3", "Small", "Mistral-Small-2"),
    ("Mistral", "2025Q1", "S3", "Mistral-Small-3"),
    ("Mistral", "2025Q1", "S3.1", "Mistral-Small-3.1"),
    ("Mistral", "2025Q2", "M3", "Mistral-Medium-3"),
    ("Mistral", "2025Q2", "S3.2", "Mistral-Small-3.2"),
    ("Mistral", "2025Q4", "L3", "Mistral-Large-3"),
    ("Mistral", "2025Q4", "Min3", "Ministral-3"),
    ("Mistral", "2025Q4", "Dev2", "Devstral-2"),
    ("Mistral", "2026Q1", "S4", "Mistral-Small-4"),
    ("Mistral", "2026Q2", "M3.5", "Mistral-Medium-3.5"),
    # Phi
    ("Phi", "2023Q2", "1", "Phi-1"),
    ("Phi", "2023Q3", "1.5", "Phi-1.5"),
    ("Phi", "2023Q4", "2", "Phi-2"),
    ("Phi", "2024Q2", "3", "Phi-3"),
    ("Phi", "2024Q3", "3.5", "Phi-3.5"),
    ("Phi", "2024Q4", "4", "Phi-4"),
    ("Phi", "2025Q2", "4-r", "Phi-4-reasoning-plus"),
    ("Phi", "2026Q1", "4-r-v", "Phi-4-reasoning-vision-15B"),
    # Gemma
    ("Gemma", "2024Q1", "1", "Gemma-1"),
    ("Gemma", "2024Q2", "2", "Gemma-2"),
    ("Gemma", "2025Q1", "3", "Gemma-3"),
    ("Gemma", "2025Q2", "3n", "Gemma-3n"),
    ("Gemma", "2026Q2", "4", "Gemma-4"),
    ("Gemma", "2026Q2", "4-12B", "Gemma-4-12B"),
]

# Verified cross-generation / merge edges from the HF `base_model` field
# (Phase 0 log). All other `base_model` entries are within-generation
# base<->instruct links, not lineage.
VERIFIED_EDGES = [
    ("Llama-3.3-70B-Instruct", "Llama-3.1-70B", "2024Q4"),
    ("Phi-4-reasoning-plus", "phi-4", "2025Q2"),
    ("Phi-4-reasoning-vision-15B", "Phi-4-reasoning", "2026Q1"),
    ("Devstral-Small-2", "Mistral-Small-3.1-Base", "2025Q4"),
    ("DeepSeek-V3.2", "V3.2-Exp-Base", "2025Q4"),
]

# Open items / caveats (verbatim from the Phase 0 log; do not drop).
CAVEATS = [
    "Llama open-weights lineage terminates at Llama 4 (Apr 2025). Post-2025 "
    "era variation is carried by Qwen/Mistral/DeepSeek/Gemma/Phi only — this is "
    "a real-world lineage-attrition fact, not an identification failure.",
    "`base_model` field is sparse: true cross-generation lineage is largely "
    "UNDOCUMENTED in HF cards (only 5 verified edges). Parent–offspring edges "
    "for the primary design must be drawn from technical reports/papers, not "
    "HF metadata. Affects Phase 3 analogies and the mechanistic estimand.",
    "DeepSeek V4 is a ground-up redesign (dropped MLA) — NOT a V3 descendant. "
    "Within-lab generation != within-lineage; V4 must be treated as a new "
    "independent lineage or dropped.",
    "Cross-family teacher leakage: Phi-4 trained on GPT-4o-generated data; "
    "Gemma 2 9B distilled from 27B; Gemma 4 built from Gemini 3. Independence "
    "assumption violated to unknown degree — these belong in V_era (shared "
    "environment); flag for the primary estimand.",
    "Mistral's Small (24B) chain (Small 3->3.1->3.2->4; Devstral-2 on "
    "Small-3.1-Base) is the only verified within-family chain; Large/Medium/"
    "Ministral are sibling branches, not a chain.",
]

# Documented divergences: era = PUBLIC RELEASE DATE, not HF `createdAt`.
# (model, HF repo createdAt, public release date)
ERA_DIVERGENCES = [
    ("Mistral-Small-4", "2026-01-23", "2026-03-16"),
    ("Mistral-Medium-3.5", "2026-03-31", "2026-04-29"),
    ("Gemma-4", "2026-03-12", "2026-04-02"),
    ("Phi-1", "2023-09-10", "2023-06-21"),
]

# Stats as documented in the Phase 0 log (for the offline consistency check).
DOCUMENTED_STATS = {
    "n_families": 6,
    "n_quarters": 14,
    "n_models": 47,
    "n_edges": 5,
    "quarters_ge2_families": 11,
    "row_spans": {
        "Llama": 6, "Qwen": 7, "DeepSeek": 5, "Mistral": 9, "Phi": 8, "Gemma": 5,
    },
    "dense_cells": {"2024Q2": 5, "2024Q3": 5, "2025Q2": 6},
}


def model_table() -> pd.DataFrame:
    """DataFrame of models: columns family, quarter, short_name, full_name."""
    return pd.DataFrame(
        MODELS, columns=["family", "quarter", "short_name", "full_name"]
    )


def design_counts() -> pd.DataFrame:
    """Family x quarter model-count matrix (the D2 occupancy)."""
    df = model_table()
    counts = df.pivot_table(index="family", columns="quarter", values="full_name",
                            aggfunc="count").reindex(
        index=FAMILIES, columns=QUARTERS, fill_value=0
    )
    return counts


def family_span() -> dict[str, int]:
    """Number of distinct quarters with >=1 model per family."""
    df = model_table()
    return df.groupby("family")["quarter"].nunique().reindex(FAMILIES).to_dict()


def quarters_with_n_families(n: int = 2) -> list[str]:
    """Quarters containing at least ``n`` distinct families."""
    counts = design_counts()
    return [q for q in QUARTERS if (counts[q] > 0).sum() >= n]


def check_consistency() -> dict:
    """Reproduce the Phase 0 classification from the table offline.

    Returns a report dict. Hard structure facts are asserted (they are the
    documented Phase 0 verdict); the dense-cell annotation is reported as a
    soft finding because it does not match the table under either a family or
    model interpretation.
    """
    df = model_table()
    report = {
        "n_families": df["family"].nunique(),
        "n_quarters": df["quarter"].nunique(),
        "n_models": len(df),
        "n_edges": len(VERIFIED_EDGES),
        "row_spans": family_span(),
        "quarters_ge2_families": len(quarters_with_n_families(2)),
        "dense_cells_computed": {
            q: int((design_counts()[q] > 0).sum())
            for q in QUARTERS
            if (design_counts()[q] > 0).sum() >= 3
        },
    }
    doc = DOCUMENTED_STATS
    assert report["n_families"] == doc["n_families"]
    assert report["n_quarters"] == doc["n_quarters"]
    assert report["n_models"] == doc["n_models"]
    assert report["n_edges"] == doc["n_edges"]
    assert report["quarters_ge2_families"] == doc["quarters_ge2_families"]
    assert report["row_spans"] == doc["row_spans"], report["row_spans"]

    single_era_families = [f for f, s in report["row_spans"].items() if s <= 1]
    assert not single_era_families, f"family confined to a single era: {single_era_families}"

    # Verdict reproduction: crossed (unbalanced/incomplete) requires >=2
    # families in >=2 quarters, both directions non-empty, no single-era family.
    ge2 = quarters_with_n_families(2)
    crossed = len(ge2) >= 2 and not single_era_families
    report["verdict"] = "CROSSED (unbalanced/incomplete)" if crossed else "NOT CROSSED"

    # Soft finding: dense-cell annotation vs table-derived values.
    expected = doc["dense_cells"]
    computed = report["dense_cells_computed"]
    mismatch = {q: (computed.get(q), v) for q, v in expected.items()
                if computed.get(q) != v}
    report["dense_cell_annotation_mismatch"] = mismatch

    return report


if __name__ == "__main__":
    rep = check_consistency()
    for k, v in rep.items():
        print(f"{k}: {v}")
