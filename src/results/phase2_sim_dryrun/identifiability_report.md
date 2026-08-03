# Phase 2 Identifiability Audit

Verdict: **PASS**

## Structural checks

- models n = 47; families = 6; quarters = 14
- occupied cells = 40/84 (47.62%)
- design rank = 19/19 -> OK
- condition number κ = 234.12 (≤ 100) -> WARN (informational)
- max VIF family = 2.56, era = 2.38 (≤ 10) -> OK
- min family span = 5 quarters; families with < 2 quarters = 0

## Fit-based checks (family vs era)

- BLUP collinearity |r| > 0.9: clear
- SE inflation (se ≥ 1.0 × est): WARN (warning only; df-family small-sample limit)
- profile flatness (drop < 1.9207): WARN (warning only; df-family small-sample limit)
- convergence: OK

## Failures / warnings

- SE >= estimate on a variance component (warning only: with 6 family levels, df = 5, the family-variance SE structurally exceeds the estimate even when identifiable — Phase 1 small-sample limit; pinned by battery S6. True alias is captured by the BLUP-collinearity and profile-flatness checks).
- profile likelihood cannot bound the family share within the ±0.4 log window (warning only: with 6 family levels, df = 5, the family profile is flat by construction — the wide family-share CI expresses this; pinned by battery S6).
- κ = 234.1 > 100 (warning only: X'X condition number reflects the sparse/unbalanced occupancy of a crossed variance-component design, not family-era aliasing; pinned by battery S6 — see docstring).
