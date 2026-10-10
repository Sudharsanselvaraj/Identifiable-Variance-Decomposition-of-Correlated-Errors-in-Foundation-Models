# Statistical verification report

Audit of *Lineage and Release Timing in Correlated Errors of Open-Weight Language Models* at `origin/main` 3a6d1dc (tree febb362). Date of audit: 2026-10-10. Read-only with respect to the repository; all code written for this audit is in `audit/tools/`, all outputs in `audit/outputs/`.

## 1. The estimand, written out

Models i = 1..N, items k = 1..K (K = 14,042), chosen option c_ik ∈ {A,B,C,D}, correct option t_k, error indicator w_ik = 1[c_ik ≠ t_k].

* **Unit of observation:** an unordered pair {i, j} of distinct leaderboard entries with at least one jointly wrong item (all 173,755 = C(590,2) primary pairs qualify; minimum 1,166 jointly wrong items).
* **Outcome:** a_ij = Σ_k 1[c_ik = c_jk ≠ t_k] / Σ_k w_ik w_jk (Eq. 1). Items where only one model is wrong or both are right are excluded from both numerator and denominator.
* **Model (Eq. 2):** a_ij = b0 + b_L s_ij + Σ_h b_E,h 1[|m_i − m_j| ∈ h] + γ1 (acc_i + acc_j) + γ2 |acc_i − acc_j| + ε_ij, where s_ij = 1[root(i) = root(j)], m = upload month (Hub creation month), h ∈ {0, 1–2, 3–5, 6–11} with 12+ as reference, acc = item-level accuracy over all 14,042 items. OLS, one row per pair.
* **Headline estimand:** b_L, the pair-weighted average difference in conditional same-wrong-option agreement between same-root and different-root pairs at equal release-gap bin and (linearly) equal accuracy sum and difference. It is a **descriptive population contrast over pairs of leaderboard entries**, weighted by number of same-root pairs: roots with more models contribute roughly quadratically more.
* **Dependence:** pairs sharing a model are dependent. The pre-specified variance (Eq. 3) sums e_p e_q x_p x_q' over all pairs p, q that share a model. Root-level variants treat roots as the clustering unit; the headline interval is the delete-one-root jackknife.

## 2. Independent implementation

`audit/tools/independent_verify.py` imports nothing from `lineage_era` or `scripts/`. It reads only the validated answer files, the frozen sample CSV (model, root, created_month, root_verified) and the manifest's `validated` flag, re-validates each file (14,042 items, same item ids and gold as the first model, options in 0..3), builds pairs by direct row-wise comparison (no matrix products), fits OLS by normal equations, computes Eq. 3 via per-model score sums, and a jackknife that refits the full OLS without every pair touching one root.

Checks of the implementation itself:

| Check | Result |
|---|---|
| Eq. 3 closed form vs O(P²) brute force on a 70-model subset (2,415 pairs) | max abs difference 1.9e-16 |
| Pair outcomes (row-wise) vs released float32 matrix products | headline estimate differs by 2.6e-10 (float32 rounding in the released code) |
| Each jackknife replicate refits the complete estimator | yes; no transformation, model selection or binning is re-estimated except accuracy cells (see §5) |

## 3. Numerical comparison: independent code vs released code vs committed output vs manuscript

All numbers are percentage points unless stated. "Committed" = `results/exp04_final/inference_audit.csv` / `prereg_12.csv`.

| Quantity | Independent | Committed output | Manuscript | Max abs. difference (indep. vs committed) |
|---|---|---|---|---|
| Primary shared-root b_L | 13.2929 | 13.2929 | 13.3 | 2.6e-10 |
| Primary jackknife 95% CI | [10.78, 15.80] | [10.78, 15.80] | 10.8–15.8 | SE 1.8e-11 |
| Primary model-level CI | [11.75, 14.84] | [11.75, 14.84] | 11.8–14.8 | SE 5e-11 |
| Primary same-month b_E,0 | 0.386 [−0.48, 1.25] | 0.386 | 0.4 (−0.5, +1.3) | 3.5e-10 |
| Expanded shared-root | 12.745 [10.98, 14.51] | 12.745 | 12.7 (11.0–14.5) | 3.2e-10 |
| Primary S2 shared-root / same-month | 11.98 / −1.45 [−3.03, +0.13] | same | −1.5 (−3.0 to +0.1) | 2.7e-10 / 1.2e-9 |
| Expanded S2 shared-root | 12.20 | same | within 11.7–13.4 | 3.5e-10 |
| All 12 pre-specified analyses (24 coefficients and SEs) | reproduced | — | 11.7–13.4 | 1.2e-9 |
| Without accuracy terms (shared root; gap 0 / 1–2 / 3–5 / 6–11) | 28.3; 8.7 / 8.5 / 6.5 / 2.9 | same | 28.3; 8.7 → 2.9 | — |
| WLS by jointly wrong items | 14.19 | 14.2 | 14.2 | — |
| Phi (error indicators) | 0.1698 | 0.170 | 0.170 | — |
| CAPA from chosen options | 0.1936 | 0.194 | 0.194 | — |
| Minus option-distribution chance | 12.51 | 12.5 | 12.5 | — |
| N1a (item distractor null): contrast; mean outcome | 13.31; 0.4233 → 0.0022 | 13.3; 0.002 | 13.3; 0.423 → 0.002 | — |
| Root-release-month model: shared root; same month | 13.1; −0.07 [−1.1, +1.0] | 13.1; −0.1 (−1.2, +1.0) | same | ≤0.05 |
| Different-root pairs sharing a root release month | 12,271 | 12,271 | 12,271 | 0 |
| Cleaned sample (21 degenerate models and 38 duplicate-vector entries removed) | 12.78 | 12.8 | 12.8 | — |
| Leave-one-root-out range | 13.10–14.36 | 13.1–14.4 | 13.1–14.4 | — |
| Unweighted mean of 63 per-root coefficients | 25.3 | 25.3 | 25.3 | — |
| DerSimonian–Laird pool, 16 roots with ≥10 pairs | 16.6 [12.5, 20.8], τ = 7.9 | same | same | — |
| 90% jackknife interval, same month (equivalence bound) | [−0.34, +1.11] | — | 1.1 | — |

Descriptives: 173,755 pairs; 2,020 same-root pairs; mean agreement 0.4233 (same-root 0.7313, different-root 0.4197); joint-wrong items 1,166–10,820 (median 4,109); same-root pairs by gap 711 / 1,004 / 259 / 45 / 1; median accuracy 0.415 (0.264 in 2022–23, 0.587 in 2024; Spearman with upload month 0.409). All match the manuscript.

**Verdict:** the headline result, its two intervals, all 12 pre-specified analyses and the secondary-outcome rows of Table V reproduce from the validated predictions with an implementation that shares no code with the release.

## 4. Answers to the Phase 3 questions

1. *Outcome and estimand:* §1. 2. *One model wrong:* excluded from numerator and denominator (conditioning). 3. *Both correct:* excluded. 4. *Accuracy enters* linearly as sum and absolute difference (flexible versions are post hoc, S6). 5. *Release gap* encoded as four indicator bins of |month difference|, reference 12+. 6. *Shared lineage* = equal resolved root string (declared `base_model` chain, Algorithm S1). 7. *Dependence:* handled by Eq. 3 (model-level), root-level dyadic and the jackknife; all three implemented and compared. 8. *Jackknife correctness:* verified (refits the entire OLS; deletion units = all 351 roots; (G−1)/G scaling). Using only the 63 multi-model roots as deletion units gives SE 1.25 vs 1.28 (CI [10.8, 15.7]). 9. *Critical values:* the manuscript uses 1.96 with G−1 = 350 degrees of freedom (t = 1.967): a 0.35% understatement of the half-width, immaterial. 10. *Specification matches manuscript:* yes. 11. *Weighting:* WLS by jointly wrong items 14.19 (no change); equal pair weights lets the two largest roots supply 1,407 of 2,020 same-root pairs.

## 5. Methodological audit

**A. Dependence in dyadic data.** The estimator family is appropriate for pair data with shared nodes (Fafchamps–Gubert, Aronow et al., Cameron et al.). The simulation in S3/S6 shows model-level SEs 3–5% too small, which the paper discloses and addresses with root-level intervals. One structural caveat: the jackknife deletes roots, and the accuracy-cell designs (R7) fix quantile bin edges on the full sample rather than re-binning inside each replicate (immaterial for the headline, which uses linear accuracy terms).

**B. Concentration in a few roots.** The jackknife SE of the lineage coefficient is driven by very few deletions: one root accounts for **68.6%** of the sum of squared leave-one-out deviations, five roots for 86.4%, ten for 92.9% (of 351 deletions). The root-vertex bootstrap interval is right-skewed (**11.5–19.0**, B = 2,000; the paper's B = 999 gives 11.4–19.6) because replicates that omit the two largest roots, whose coefficients are among the smallest, move the estimate up. Re-estimating after **removing both largest roots entirely** gives **15.95 points (jackknife CI 12.8–19.1; 613 same-root pairs remain)**. So the headline is not produced by the dominant roots; their inclusion pulls it *down*. This is a strength that the manuscript does not report. Reporting the bootstrap interval next to the headline would pre-empt the obvious criticism that a normal-theory interval rests on few effective clusters.

**C. Specification.** The linear accuracy control is a pre-specified choice that the authors themselves test: the S6 simulation shows false rejection of 27% (shared root) and 31% (same month) when agreement depends non-linearly on ability, with small bias (−0.15 points). Flexible controls (quadratic, 55 and 210 accuracy cells, matching) move the lineage estimate within 11.0–14.9. None of these specification checks was re-run independently here (committed outputs only), but they are internally consistent with the independent baseline.

**D. Unreported but informative sensitivity (new, computed by the audit; post hoc, not in the paper).**

| Check | Primary sample result |
|---|---|
| Control for same uploader (same Hub account) | shared root 12.93 (jackknife SE 1.09); same-uploader coefficient +6.75 (SE 1.42) |
| Drop same-root pairs that are also same-uploader (140 of 2,020) | 12.30 (SE 0.92) |
| Cluster the jackknife by uploader (238 uploaders) instead of root | SE 1.00 for the baseline coefficient |
| Expanded sample, same checks | 12.30; 11.95; SE 0.87 |

Same-account pairs do agree more (+6.75), so developer recipes are a real second pathway, but the lineage coefficient is almost unchanged by controlling for it. The paper lists a "same-root-organisation predictor" as *Not done*; this partly answers it.

**E. Interpretation.** The manuscript correctly states that the associations are observational, that release timing is measured by Hub creation month (noisy, nested in lineage), and that no ensemble was tested. It does not equate declared lineage with shared training data. Three phrasings are slightly stronger than the evidence (ISS-07, ISS-08, ISS-09 in the issue register). The 13.3-point result is large in practical terms (31% above the mean agreement of 42.3%), not merely statistically detectable.

**F. Multiple testing and forking paths.** Table III labels every analysis as pre-specified, amendment, exploratory, post hoc or not done; the paper reports roughly 60 analyses. The audit found no case in which the reported primary result depends on a post-hoc choice. The same-month coefficient changes sign across specifications; the paper reports this openly and builds its conclusion on it ("sign depends on the specification"). Per-subject results use model-level intervals the authors state are too narrow.

## 6. What remains unverified

* The Monte Carlo simulations (S1 precision, S3 gate audit, S6 real-accuracy simulation) were not re-run.
* R-series analyses not recomputed independently: quadratic/decile/210-cell accuracy controls, accuracy-matched pairs (R7, R13), pair × item model (R9), permutation test, MMLU-Redux subsets (needs untracked `datasets/mmlu_redux/`), tree-distance and within-root dose-response (R2, R8), capability and subject heterogeneity, joint timing model, size and architecture controls, N1b and the Rasch null.
* The lineage resolution itself (declared parents → roots) was reproduced only as far as regenerating the roster from the public source and matching the frozen-list hashes; the resolution logic was not re-implemented.
* Whether declared lineage reflects actual weight inheritance: not testable from these data.
