# Simulated peer review (IEEE Access) with red-team objections

*Written after the audit, from the evidence in this directory. The reviewer is deliberately skeptical but fair. Statements about what was checked refer to `CLAIM_EVIDENCE_LEDGER.csv`.*

## 1. Summary of the contribution

The manuscript asks whether two open-weight language models that share a declared lineage root choose the same wrong MMLU answer more often than unrelated models, and how this association compares with release-time proximity. Using 977 models whose per-item predictions were reconstructed from the first Open LLM Leaderboard and checked item by item against stored correctness flags, it builds a pair-level data set (173,755 pairs in the primary sample; 430,128 in an expanded sample), regresses conditional wrong-option agreement on a shared-root indicator, release-gap bins and two accuracy terms, and uses dyadic and root-level inference. The headline is +13.3 percentage points (jackknife 95% CI 10.8–15.8) for shared lineage, against small, specification-dependent release-timing coefficients. The paper frames the work as diagnostic and observational, discloses that its plan was dated but not externally registered, labels every analysis as pre-specified, amended, exploratory or post hoc, and documents a withdrawn earlier per-model evaluation.

## 2. Major strengths

1. **The central number reproduces.** From the validated predictions, an implementation written from the manuscript's equations (no shared code) gives 13.293 points, jackknife CI [10.78, 15.80], and matches all twelve pre-specified analyses to 1e-9; the secondary outcomes (phi, CAPA, option-chance, item-distractor null, WLS) also reproduce.
2. **Validation is real, not nominal.** The extraction check compares the argmax option's correctness with the leaderboard's stored flag on every item. Re-extracting three models (one per storage layout) from the live leaderboard with separate code gave zero mismatches over 42,126 rows.
3. **Unusual honesty about process.** Table III classifies every analysis; the abstract says "not externally registered"; the limitations name the narrowly missed leakage criterion of the simulation check, the 3–5% SE under-coverage and the linear-accuracy false-rejection problem; the withdrawn evaluation is explained and its audit trail kept.
4. **The result is not fragile to the obvious threats.** Drop both dominant roots: the estimate rises to 15.9. Control for same uploader: 12.9. Remove degenerate and duplicate entries: 12.8. Alternative outcomes, nulls and accuracy controls: 11.0–14.9.
5. **Reproducibility effort exceeds the norm.** A clean clone rebuilds every table and PDF; the roster, frozen-list hashes and sampling regenerate from the public source today.

## 3. Major concerns

**M1. What "lineage" identifies.** The predictor is a declared `base_model` chain. Fine-tunes of one base share weights, tokenizer, prompt format, and often training data, uploader and recipe; the design cannot separate these. The paper says so, but the title and abstract speak of "lineage" and the discussion offers a mechanism-flavoured narrative ("Why lineage and not release timing"). The new same-uploader check suggests developer practice is a second, smaller route (+6.8 points) that leaves the lineage coefficient at about 13 — the authors should report it.

**M2. Few effective clusters and a pair-weighted estimand.** 63 roots inform the contrast; two supply 70% of same-root pairs; one root drives about 69% of the jackknife variance. Per-root coefficients range from 10 to 22 points and the unweighted mean is 25.3. The paper acknowledges this but leads with a normal-theory interval. A root bootstrap gives 11.4–19.6.

**M3. The release-timing question is under-identified.** RQ2 is answered with the Hub creation month, a noisy proxy for training-data time, in a 27-month window in which same-root pairs are almost all within a year. The same-month coefficient changes sign (+1.0 with the option-distribution control, +3.3 among accuracy-matched pairs, −1.5 to −2.2 above 0.30 accuracy). "Small and specification-dependent" is the honest summary, but "inconclusive" may be more accurate than the discussion's tilt toward lineage.

**M4. Benchmark and population scope.** One four-option benchmark scored by log-likelihood in an old pipeline; 42% of primary models (247/590) are near chance (<0.30), where agreement is dominated by letter preferences; contamination is acknowledged but not examined.

## 4. Minor concerns

* "frozen … before any prediction was downloaded" is not literally true (the reference model's file predates the freeze by 90 minutes).
* The spot check "extracted accuracy equals the official aggregate (43.80)" holds only for the 57-subject mean; the item-level accuracy is 42.76.
* The counts of "models" are leaderboard entries (563 distinct repositories among the 590).
* "MMLU" and "CI" are not defined in the body; two biographies are incomplete; the AI-use citation appears only in the Acknowledgment.
* Interpretive wording: "Neither measure alone shows a positive association", "within 0.6 points of zero in both populations" and the Discussion heading need "in the pre-specified model".
* Test coverage of the data-retrieval and roster code is nil; the loader does not bind files to models.
* A few supplement figures use text below 7 pt.

## 5. Questions for the authors

1. How many of the 63 informative roots are single-developer series (the "small roots" with coefficients near 22)? Does the within-root gradient survive after removing same-uploader pairs?
2. Would the lineage coefficient change if shared tokenizer were controlled (all fine-tunes share the base tokenizer, but different roots sometimes also share one)?
3. Can the release-timing analysis be repeated with a better date (the base model's documented release date rather than the Hub creation month)? The root-month analysis uses the root's Hub month.
4. What fraction of same-root pairs are merges or quantizations of the same checkpoint beyond the 38 duplicate-prediction entries?
5. Is any of the near-chance subset (247 models) driven by prompt-format incompatibility rather than capability, and does restricting to 0.30+ models change the picture of lineage vs era? (S2 says 12.0 and a negative same-month coefficient.)
6. What is the full 977-file re-download exit status in a clean environment?

## 6. Recommendation

**Minor revision (accept after minor corrections).** The core empirical finding is sound, reproduced independently, and honestly bounded; the weaknesses are in interpretation breadth (M1, M3) and wording, not in the arithmetic. IEEE Access's soundness-based criteria are met.

---

# Red-team: the five strongest reasons to reject, ranked

| # | Objection | Severity | Evidence | Headline affected? | Needs | Minimum remedy | Response supported by evidence? |
|---|---|---|---|---|---|---|---|
| 1 | "Declared lineage" confounds weights with shared data, recipes, developers, tokenizer; the paper cannot say lineage *per se* matters | major (interpretation) | Same-uploader control: 12.9; within-root gradient +5.5; the paper itself says the routes are not separated (§VI, VII) | Meaning, not magnitude | Clearer writing; optional new computation (done in audit) | Use "declared descent" in title-level claims; report uploader control; keep the observational framing | **Yes**: "We claim an association, not a mechanism; developer practice is examined and does not account for the estimate" |
| 2 | Inference rests on a handful of influential roots; the estimand weights two roots at 70% and the typical root differs (16.6 pooled, 25.3 unweighted) | moderate | 68.6% jackknife variance from one root; bootstrap CI 11.4–19.6; drop-top-2 15.9 [12.8, 19.1] | Interval width, not sign | Reporting only | Show bootstrap and drop-top-2 beside the headline; state the estimand as population-averaged over pairs | **Yes** (all three computed) |
| 3 | RQ2 is unanswerable with this proxy; the data are compatible with a modest timing effect (matched pairs +3.3) | major for RQ2 only | V-D; accuracy-matched +3.3 [1.4, 5.2] vs equivalence bound 1.1; sign flips by specification; period 27 months; era nested in lineage | No | Clearer writing; new data (independently pretrained, same-period models) for a real answer | Call RQ2 "inconclusive in these data", drop any tilt in the Discussion | **Partly**: the paper already says "sign depends on the specification"; it should not claim more |
| 4 | One benchmark, old pipeline, many near-chance models: agreement conditional on both wrong is mostly letter-preference noise at low accuracy; contamination unexamined | moderate | 247/590 below 0.30; S2 subset 11.98; S1 position control 13.3 | Generalization | New data for other benchmarks (not required for soundness) | State scope in the abstract as already done; keep S1/S2 prominent | **Yes**, for soundness within this population; not for generality |
| 5 | The process is not credible: unregistered plan, same-day plan and results, data-informed amendment, ~60 analyses, AI-written code and text | moderate | Plan→results 4 h 28 min; amendment 3 after seeing accuracies; commit dates preserved through a history rewrite (26/26); Table III; AI disclosure | No | Transparency (done); optional deposit of a dated hash now | Keep Table III and the not-registered statement; deposit a timestamped hash (it records a deposit date only) | **Yes**: nothing is hidden, and the headline does not depend on any post-hoc choice |

I did not manufacture further objections. Minor candidates (wording, coverage, figure sizes) are in the issue register.

## Strongest genuinely supported aspects

(1) an independently reproduced, large and robust association; (2) an item-level validation that would have caught the earlier extraction error and demonstrably does on re-extraction; (3) the transparency apparatus (Table III, S7, the explicit non-registration); (4) every cited claim about prior work that I checked matches its source; (5) a reproduction path that works from the public source and fails loudly when data are missing.
