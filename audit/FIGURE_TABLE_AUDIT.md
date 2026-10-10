# Figure and table audit

Candidate: `origin/main` 3a6d1dc. Numbers follow the built PDFs (`paper/build/*.aux`). Each figure was inspected as a rendered image during this audit session, its generating function in `scripts/make_exp04_figures.py` was read, and (where possible) numbers printed inside the PDF were extracted with PyMuPDF and compared with the independent results. Text sizes are the smallest span measured in the figure PDF **at its placed size** (`audit/outputs/figure_sizes.csv`). IEEE guidance is about 8 pt or larger.

Regeneration: 14 of 20 figure PDFs rebuild byte-identically from `results/` alone; the 6 marked **[data]** need the validated answer files.

## A. Main-paper figures

| Fig. | File / generator | Purpose | Key values checked | Axes, denominators, uncertainty | Min text | Findings |
|---|---|---|---|---|---|---|
| 1 | `fig_agreement.pdf` `fig_agreement()` **[data]** | Raw pairwise agreement; shows accuracy and lineage structure | Caption: 7 roots with ≥8 models, 140 models, same-root mean **0.7345**, different-root **0.5644** (caption 0.734 / 0.564): **reproduced** | Colour = P(same wrong ∣ both wrong), clipped at 2nd/98th percentile (stated); 590 models; no intervals (descriptive) | 7.9 pt | Sound. Accuracy-sorted axis with tick labels is explained in the caption. No issue |
| 2 | `fig_dataflow.pdf` `fig_dataflow()` | Study flow: data collection to checks; counts | 6,896; 721; 1,295; 613; 967; 590; 928; 977; 541 in both; 1,018; 41 excluded; 173,755 / 430,128 pairs: **all match** manifest and independent counts. (Strict counts 554/789 no longer printed, they are in Table IV) | Counts are models, pairs only at the analysis step (stated). Solid vs dashed boxes encode fixed-in-plan vs added-later and are explained | 7.9 pt | Sound. Caption is two sentences. Cylinders/stacks are flowchart symbols, no decorative icons. "Eq. (2)" is hard-coded in the figure and equals the compiled equation number (checked) |
| 3 | `fig_accuracy.pdf` `fig_accuracy()` **[data]** | Accuracy distribution and trend over upload month; labelled base checkpoints | n = 590, median 0.415, 247 below 0.30, Spearman 0.409: **reproduced**. Quarterly median/IQR for quarters with ≥10 models | Density axis labelled "arbitrary units"; IQR ribbon is not a CI (caption says IQR) | 7.9 pt | Sound. Labels sit clear of data. Marker legend and diamonds explained |
| 4 | `fig_lineage_month_map.pdf` `fig_heatmap()` **[data]** | Roots × upload month, shows identification limits | Cell counts sum to 590 (10 roots 159 + 431 pooled); root labels from the shared label table (Llama-3-8B, Mistral-7B-v0.1, Mixtral-8x7B-v0.1, …) | Log colour scale with numbers printed in cells (readable in greyscale) | 7.4 pt | Sound. Slightly below 8 pt for tick labels |
| 5 | `fig_schematic.pdf` `fig_schematic()` | Predictors and a worked outcome example | Toy example recomputed: A1–A2 = 4/5 = 0.80 (5 jointly wrong, 4 same option); A3–B2 = 2/5 = 0.40: **correct** | Hypothetical models (stated). Okabe–Ito colours plus letters, so not colour-only | 7.7 pt | Sound |
| 6 | `exp04_agreement_by_gap.pdf` `fig_gap()` **[data]** | Unadjusted agreement by release gap | Pair counts 711/1,004/259/45 (same root) and 14,909/45,044/44,054/40,106/27,622 (different root): **reproduced**; Δ labels +29.7/+27.4/+27.7/+31.7 reproduced; means 0.749/0.726/0.708/0.712 vs 0.452/0.452/0.432/0.395/0.366 | Full 0–1 axis; dashed 1/3 line labelled; bars are IQR "not CIs" (caption); bin with 1 same-root pair omitted (stated, <20 pairs) | 7.4 pt | Sound. Percent vs percentage-point usage in Δ is consistent ("points") |
| 7 | `fig_raw_adjusted.pdf` `fig_rawadj()` **[data]** | Why accuracy must be adjusted for; raw vs adjusted coefficients | 28.3 → 13.3 (primary), 24.0 → 12.7 (expanded): **reproduced independently**; change labels Δ −15.0, −11.3, etc.; 171,735 and 2,020 pairs stated in the caption | (a) means with IQR bands, pairs per bin on log axis; (b, c) jackknife 95% CIs, gaps vs 12+. Line styles differ (greyscale-safe) | **5.6 pt** (exponent digits of "10²", "10⁴") | One tiny text item: replace mathtext exponents by plain labels (ISS-19). Otherwise sound; interval type stated per panel |
| 8 | `fig_timing.pdf` `fig_timing()` | Release-gap coefficients as annotated heatmaps | All 48 cells of panel (a) present and equal to `prereg_12.csv`; panel (b) values from `revision2.csv` (root-month primary reproduced independently: −0.1 etc.) | Diverging RdBu scale, symmetric ±3 points, values printed in every cell, bold = 95% CI excludes zero; (a) model-level CIs, (b) jackknife CIs (stated) | 7.9 pt | Sound. The bold rule mixes two CI types between panels, disclosed in the caption. Strong, honest summary of sign instability |
| 9 | `fig_inference.pdf` `fig_inference()` | Sensitivity to unit of dependence | Width ratios ×1.63/1.46/1.39/1.50 (shared root), ×1.28/1.28/1.33/1.34 (same month): **reproduced**; panel (c) bars = root-dyadic and jackknife widths relative to model-level | 95% CIs; ratio panel dashed at 1 | 7.5 pt | Sound. P/E labels defined in the caption |
| 10 | `fig_dose.pdf` `fig_dose()` | Dose-response by tree distance and relation; within-root estimates | Labels 177/699/1,112 and 260/627/1,101; within-root +5.5/+2.3/+4.7/+2.2: match `revision2.csv`, `R8.csv` (**committed only**, not recomputed independently) | Jackknife 95% CIs; band = pre-specified shared-root interval; marker area ∝ pairs | 7.9 pt | Sound. Panel (c) uses a different reference class ("vs distance 3+" / "vs more distant"), stated in the panel |
| 11 | `fig_heterogeneity.pdf` `fig_heterogeneity()` | Where the lineage association comes from | Same-root pair counts 741/666/136/105/91/45/28/208 and capability bands 124/244/531/1,121 match `heterogeneity.csv` (**committed only**); the leave-one-out and per-root summaries it supports were reproduced independently | (a) model-level CIs, (b) jackknife, (c) model-level, unadjusted for 57 tests (stated in-panel and caption); category by marker **and** colour (colour-blind safe) | 7.5 pt | Sound. Per-subject intervals are acknowledged as too narrow |

Cross-figure consistency: root labels come from one table (`ROOT_LABEL`), numbering follows first-citation order (checked programmatically for all figures and tables), percentages vs percentage points are used consistently, and all captions state their interval type. No caption was found to describe a different analysis from the one plotted.

## B. Supplement figures

| Fig. | File | Purpose | Findings |
|---|---|---|---|
| S1 | `precision_scaling.pdf` | Per-model variance decomposition precision | Values from `results/precision_gate` (**committed only**). 8.6 pt at placed size; target-RMSE line labelled; caption states RMSE is not a CI half-width |
| S2 | `fig_gate_audit.pdf` | Post-hoc simulation audit | **Text 5.1–6.8 pt at placed size** (two-tier tick labels, criterion annotations): enlarge (ISS-19). Wilson intervals stated. Chosen design flagged "10.8% > 10%" |
| S3 | `exp04_forest.pdf` | Twelve analyses (moved from main text) | All 12 rows reproduced independently; model-level CIs, stated as narrower than the headline jackknife interval; 7.3 pt |
| S4 | `fig_outcomes.pdf` | Outcome variants | 8.4 pt; phi/CAPA on their own scales (labelled) |
| S5 | `fig_item_null.pdf` | Item-difficulty-aware nulls | **5.3 pt tick labels and 6.8 pt legends** at placed size: enlarge (ISS-19). N1a mean and contrast reproduced independently; N1b/N2 committed only |
| S6 | `fig_controls.pdf` | Size and architecture controls | 8.4 pt; exploratory (stated) |
| S7 | `fig_detection.pdf` | Agreement as a signal of shared lineage | Histograms and ROC; AUC 0.95/0.88 asserted equal to the stored values by the figure script (not independent); 8.6 pt |

## C. Tables

| Table | Generator | Contents verified | Status |
|---|---|---|---|
| I (main) | manual | Relation to prior work; every entry checked against the cited source (see CLAIM_EVIDENCE_LEDGER C57) | Verified |
| II (main) | `tab_descriptives.tex` | Primary column (590, 351/63 roots, 173,755 pairs, 2,020 same-root, median accuracy 0.415, 4,109 joint-wrong median, means 0.423/0.731/0.420) reproduced; S2 and expanded column pair and model counts reproduced | Verified |
| III (main) | manual | Status of every analysis; compared with the plan history (commits 898c223–679c5b7 and later); no mislabel found | Verified |
| IV (main) | `tab_prereg.tex` | All 12 rows (estimates, CIs, models, pairs) reproduced to 1.2e-9 | Verified |
| V (main) | `tab_robust.tex` | Rows reproduced independently: phi, CAPA, option-chance, N1a, WLS, cleaned sample, root-month. Others (N1b, accuracy-cell rows, matched pairs, pair × item, bootstrap, config, cap-15, MMLU-Redux, tree distance) match committed outputs only. Mixes three SE types (labelled in a column) | Partly independent |
| S-I … S-IV | `tab_precision`, manual, `tab_pairgate`, `tab_gateaudit` | S-II (findings of the earlier version) verified against the earlier manuscript and S7 files; others committed only | Mixed |
| S-V … S-XIV | `tab_rawadj`, `tab_inference`, `tab_outcome`, `tab_itemnull`, `tab_exploratory`, `tab_revision2`, `tab_revision3`, `_inf`, `_dose`, `tab_sim_real` | Coefficient rows of S-V and S-VI equal the independent results for the shared rows (shared-root/same-month with and without accuracy; three variance estimators); the rest committed only | Mixed |
| S-XV … S-XVIII | `tab_runpod_plan`, manual, `tab_runpod`, `tab_runpod_main` | The 16 recorded runs, all-A predictions, aggregate accuracies and chance-level models reproduced from the files (S7 text); environment table labels are evidence labels, none claims verification except the intake check, which was re-run | Verified |

## D. Prioritised corrections

1. (minor) Fig. 7 exponent digits at 5.6 pt; supplement Figs. S2 and S5 below 7 pt. ISS-19.
2. (minor) Main-paper figure text is 7.4–7.9 pt; IEEE asks about 8 pt or more. Consider +0.5 pt on the figures with 7.4–7.5 pt minima (Figs. 4, 6, 9, 11).
3. (optional) State in Fig. 8's caption that the bold rule uses model-level CIs in (a) and jackknife CIs in (b), which is already in the caption but easy to miss.
4. No figure was found to contain a wrong value, stale image, truncated axis, unlabeled baseline, or interval mislabelled as an SE or IQR.

## E. Is a separate end-to-end workflow figure needed?

No further figure. Fig. 2 already shows source → lineage → freeze → validation → pairs → model → inference → checks, and distinguishes fixed from later-added steps; Fig. 5 explains predictors and outcome with a worked example. Adding another would duplicate them.
