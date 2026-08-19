# Peer Review Simulation

**Paper:** Identifiability-Gated Variance Decomposition of Foundation-Model Performance

This document simulates three adversarial reviewers to identify weaknesses before submission.

---

## REVIEWER A: Statistician / Mixed-Effects Expert

### Criticism A1: Identifiability of covariance basis matrices

The paper's Proposition 1 (Section 4.4) states that $\{I, Z_F Z_F^\top, Z_E Z_E^\top\}$ are linearly independent on the orthogonal complement of $\mathbf{1}$ when the design is connected and crossed. However, the proof is given by assertion ("which holds when..."), not by formal proof. For a crossed design with sparse occupancy (71% empty cells), the linear independence of these three $N \times N$ matrices in the space of symmetric matrices is not obvious. A formal argument—e.g., showing the off-diagonal entries provide independent information—would strengthen the claim. **The informal argument in Appendix D is correct but insufficient for a statistics audience.**

**Status: Partially addressed.** Appendix D provides an informal argument about off-diagonal entries, but a rigorous proof is not given. Recommend expanding the proof or citing the general result (e.g., Searle et al. 1992, Ch. 9) explicitly.

### Criticism A2: REML covariance structure misspecification

The model assumes $\alpha_f \sim N(0, \sigma^2_L)$ and $\beta_e \sim N(0, \sigma^2_E)$ are independent. In reality, model families may have heterogeneous variance (e.g., Mistral produces many more models than Llama), and eras may have heterogeneous variance (2025Q1 has 2 models, 2023Q3 has 3). The paper acknowledges the six-family small-sample limit but does not discuss whether heterogeneous family/era variances would bias the homogeneous-variance REML estimates. A simulation under heterogeneous variance would clarify robustness.

**Status: Not addressed.** This is a genuine limitation. Recommend adding a brief simulation under heterogeneous variance or discussing the sensitivity of homogeneous-variance REML to this misspecification.

### Criticism A3: Nelder-Mead optimizer choice and convergence

Section 9.3 states that "Nelder-Mead always finds a finite optimum of the restricted log-likelihood." This is not guaranteed: Nelder-Mead can fail to converge or converge to a saddle point, especially in higher dimensions. The code (`analysis/reml.py`) uses L-BFGS-B as well, but the paper's prose implies Nelder-Mead is the primary optimizer. Clarify which optimizer is used in which context, and report convergence diagnostics (gradient norm, Hessian positive-definiteness) for the empirical application.

**Status: Partially addressed.** The code uses both L-BFGS-B and Nelder-Mead, but the paper does not distinguish which is used where. Recommend clarifying in Section 6.1 and Appendix A.

### Criticism A4: Condition number threshold κ_max = 100

The paper cites "Belsley's classification: κ > 100 indicates severe multicollinearity" for the condition number threshold. Belsley (1991) actually distinguishes κ > 30 as "strong" and κ > 100 as "very strong" multicollinearity, and notes the threshold depends on sample size. The 100 threshold is a conventional choice, but the paper should acknowledge that different conventions exist (e.g., kutner et al. suggest 30 for small samples). More importantly, the threshold is validated through simulation, which is the correct approach—but the simulation validation uses D2 (47 models), not the 16-model population. The threshold's calibration at N=16 is not established.

**Status: Partially addressed.** The paper acknowledges thresholds are "conventional choices validated through simulation" (Section 13, item 8) but does not address calibration at N=16. Recommend adding a note that the threshold is calibrated at N=47 and its behavior at N=16 is extrapolated.

### Criticism A5: Bootstrap CI methodology

Section 9.2 reports a bootstrap 95% CI of $[3.4 \times 10^{-8}, 0.776]$ for the family share. The bootstrap procedure is described in Appendix A as "Monte Carlo delta method" using the asymptotic covariance from the numerically differentiated Hessian. This is a parametric bootstrap (or delta method), not a nonparametric bootstrap. The distinction matters: parametric bootstrap CIs rely on the model being correctly specified, which is exactly the situation where the design is rank-deficient. Report whether the Hessian is positive definite at the REML solution (it may not be in the rank-deficient case).

**Status: Partially addressed.** The code uses `analysis/bootstrap.py` with MC draws, but the positive-definiteness of the Hessian at the rank-deficient solution is not checked. Recommend adding a diagnostic.

### Criticism A6: REML vs. ML for variance components

The paper correctly chooses REML over ML to avoid downward bias. However, REML is invariant to the fixed effects only when the design matrix is the same across observations. In the crossed random-effects model, the intercept is the only fixed effect, so REML and ML differ only in the degrees-of-freedom correction. The correction is meaningful at N=16 (the effective df correction is approximately $(p-1)/N = 14/16 = 0.875$), but the paper does not quantify the ML vs. REML difference. A brief comparison would strengthen the choice.

**Status: Not addressed.** Recommend adding a sentence or table comparing REML and ML estimates for the 16-model population.

### Criticism A7: Profile likelihood threshold 1.9207

The threshold 1.9207 for profile flatness is derived from $\chi^2_1$ 95% critical value halved. This is the threshold for a single variance component's profile likelihood dropping by more than 1.9207 log-units. However, with three variance components, the relevant threshold should account for the multiplicity of three components. The Bonferroni-corrected threshold would be $\chi^2_1(0.95/3)/2 \approx 1.44$, which is less stringent. The current threshold may be overly conservative for flagging non-identifiability.

**Status: Not addressed.** Recommend either justifying the uncorrected threshold or applying a multiplicity correction.

### Criticism A8: Likelihood ratio test at the boundary

When a variance component is estimated at or near zero (as $\sigma^2_E \approx 2.06 \times 10^{-9}$ in Section 9.1), the standard $\chi^2$ asymptotics for likelihood ratio tests do not apply (self-concordance at the boundary). The paper does not perform a formal LRT, but the share CIs implicitly rely on asymptotic normality on the log-variance scale. This approximation may be poor when one component is near zero.

**Status: Partially addressed.** The paper acknowledges "the near-zero era estimate is not evidence of no era effect" but does not discuss the boundary asymptotics issue. Recommend a brief note.

**Overall verdict: MAJOR REVISION.** The statistical framework is sound and the identifiability analysis is valuable. However, several claims need stronger formal support (Proposition 1, profile likelihood threshold), and the robustness of REML to variance heterogeneity and boundary effects should be discussed. The simulation validation is the paper's strongest statistical contribution.

---

## REVIEWER B: LLM / ML Expert

### Criticism B1: Model selection is not principled

The 16 measured models appear to be a convenience sample of what was computationally feasible, not a principled selection. The paper acknowledges this (Section 7.9) but does not explain why specific models within each family were chosen. For example, within Phi, 5 models are measured (Phi-1 through Phi-4-reasoning-plus), but within Llama only Llama-1 (7B). Why not Llama-2, Llama-3, or Llama-3.1? The asymmetric coverage biases the family-era occupancy. The G3 procedure (Section 5.3) is designed to select populations outcome-independently, but the actual 16-model population was not selected by G3.

**Status: Addressed.** Section 7.9 explicitly states "16 of 22 were evaluated; DeepSeek-V3.1/V3.2 could not be evaluated due to compute constraints." However, the reason for the specific 16-of-22 selection is not documented.

### Criticism B2: MMLU as the sole benchmark is insufficient

MMLU (5-shot) is the only benchmark used. MMLU has known issues: contamination in pretraining data, saturation at frontier levels, and cultural/linguistic bias. The paper's caveat about benchmark contamination (Section 13, item 12) is appropriate but does not address whether MMLU's specific failure modes (e.g., factual recall vs. reasoning) would systematically bias the lineage/era variance decomposition. If lineage effects are stronger on reasoning tasks and era effects stronger on factual recall, the MMLU-specific decomposition may not generalize.

**Status: Partially addressed.** Section 13, item 5 acknowledges "Generalizability to other benchmarks is not established." Recommend expanding this to discuss how benchmark choice could interact with the variance decomposition.

### Criticism B3: "Foundation model" scope is misleading

The title says "Foundation-Model Performance" but the 16 measured models include small models (Phi-1 at 1.3B, Phi-1.5 at 1.3B, Qwen-7B at 7B) and instruction-tuned models (Mistral-7B-Instruct-v0.3, Phi-3-medium-4k-instruct). These are not "foundation models" in the pretraining sense—they are fine-tuned or instruction-tuned derivatives. The family grouping treats all models within a lineage as equivalent regardless of fine-tuning, which conflates pretraining lineage with instruction-tuning lineage. The paper defines "family" as a coarse proxy for ancestry (Section 11.2), but this conflation is not discussed.

**Status: Not addressed.** The term "foundation model" is used broadly. Recommend either narrowing the scope to "open-weight language models" or explicitly discussing the conflation of pretraining and instruction-tuning lineage.

### Criticism B4: Fidelity confound (BF16 vs. 4-bit)

One model (Mistral-Small-4) was evaluated at 4-bit quantization while the other 15 were at BF16. The paper acknowledges this (Section 7.4) but does not quantify the expected accuracy difference from quantization. If 4-bit quantization reduces MMLU accuracy by 5–10pp (as reported in the quantization literature), then Mistral-Small-4's low accuracy (24.3%) may be partially an artifact of quantization rather than a genuine capability difference. This confound affects the variance decomposition if quantization correlates with era (newer models are more likely to be quantized due to size growth).

**Status: Partially addressed.** Section 7.4 notes the distinction but Section 13, item 6 acknowledges it as a limitation. Recommend adding a quantitative estimate of the quantization effect.

### Criticism B5: Evaluation validity crisis undermines the empirical contribution

Six of 16 models (37.5%) produce accuracy at or below the 4-choice chance level (25%). The Mistral-Small family shows a 57-percentage-point degradation between versions. The paper attributes this to chat-template mismatch (Section 7.6), which is plausible but unverified. The paper correctly states the identifiability gate is invariant to trait values, but the empirical application—which is the paper's main real-world demonstration—uses these potentially invalid trait values. A reader may question whether the entire empirical exercise is meaningful if the input data is unreliable.

**Status: Addressed.** Section 7.6 provides a detailed caveat. However, the paper could be stronger by either (a) excluding the 6 suspect models and re-running the gate on the remaining 10, or (b) using independent reference accuracy scores (e.g., from the Open LLM Leaderboard) as a cross-check.

### Criticism B6: "Lineage" definition is underspecified

The paper defines "family" as a coarse proxy for ancestry, but the HuggingFace organization (e.g., "meta-llama" vs. "huggyllama" for Llama-1) is used as the family identifier. Llama-1 is hosted under `huggyllama/llama-7b`, while Llama-3 is under `meta-llama/Meta-Llama-3-70B-Instruct`. These are the same family in the paper's grouping, but the HuggingFace repos are different organizations. The family assignment is correct (both are Llama descendants), but the mechanism by which "family" captures lineage vs. architectural similarity vs. shared training data is unclear. If two unrelated models happen to share an architecture (e.g., both based on LLaMA), are they in the same family?

**Status: Partially addressed.** Section 7.3 says family is "verified against Hugging Face organization metadata and technical reports." Recommend clarifying the exact lineage-verification procedure.

### Criticism B7: Novelty relative to generalizability theory

The paper positions itself as introducing variance decomposition to LLM evaluation, but the same statistical machinery (crossed random effects, REML, generalizability theory) has been applied to educational measurement for decades. The paper cites Brennan (2001) and Cronbach et al. (1972) but does not explain why existing generalizability theory software (e.g., `g theory` in R, `urGENOVA`) was not used. The contribution is the application to a new domain (LLM populations), not the statistical method itself. This should be stated more explicitly.

**Status: Partially addressed.** Section 2.3 acknowledges the statistical machinery is "well established" and Section 2.6 positions the contribution as applying it to model populations. Recommend making the domain-application framing more prominent.

### Criticism B8: The 47-model "candidate population" is itself a convenience sample

The 47-model population defined in `occupancy.py` is not a principled census of all open-weight models. It excludes closed models, proprietary models, and presumably many open-weight models that were not catalogued. The G3 procedure selects the minimum valid population from this candidate set, but the candidate set itself may be biased toward certain families or eras. The paper does not discuss how the 47-model frame was constructed.

**Status: Not addressed.** Recommend adding a brief description of how the 47-model candidate population was assembled and what it excludes.

**Overall verdict: MAJOR REVISION.** The paper's core contribution—the identifiability gate—is valuable and well-executed. However, the empirical application is undermined by evaluation validity concerns, and the framing (foundation models, lineage definition, candidate population construction) needs tightening. The novelty claim should be explicitly positioned as a domain application of established statistical methods.

---

## REVIEWER C: Highly Skeptical Journal Reviewer

### Criticism C1: The numbers 16, 22, and 47 are confusing

The paper discusses three population sizes: 16 (measured), 22 (G3 selected), and 47 (candidate frame). The relationships among these are not always clear. Section 7.9 says "16 of 22 were evaluated," but the 16 models are not a subset of the 22—DeepSeek-V3.1 and DeepSeek-V3.2 are in the 22 but not the 16, while the 16 includes models (Devstral-2, Phi-4-reasoning-plus, Gemma-3n, Gemma-4-12B) that may not be in the 22. The paper needs a clear population diagram showing which models are in which set.

**Status: Partially addressed.** Section 7.9 lists what is and is not measured, but the relationship between the 16, 22, and 47 sets is not made visually explicit. Recommend adding a Venn diagram or table showing set membership.

### Criticism C2: The identifiability gate's practical value is unclear

The paper demonstrates that the gate "works" by showing the 16-model design fails. But what actionable information does this provide? The paper says the decomposition is "not reportable," but does not suggest what an alternative analysis could be. If the gate always fails on convenience samples (which is likely for any realistic model population), what is the point? The design-space analysis (Section 10) identifies a 30-model sufficient configuration, but this configuration requires evaluating 30 models at significant compute cost. The practical recommendation—"apply the gate before any variance-attribution claim"—is valid but may be too strong a conclusion for a paper that demonstrates failure rather than success.

**Status: Not addressed.** The paper's framing is appropriately cautious, but the practical impact is limited by the negative result. Recommend discussing what analyses ARE valid on the 16-model population (e.g., descriptive statistics, pairwise comparisons) even if variance decomposition is not.

### Criticism C3: Invalid JSONL files and the deferred error-similarity analysis

The paper acknowledges that all 16 per-question JSONL files contain constant predictions (Section 7.8). This means the error-similarity analysis—the analysis that motivated the paper in the first place (Kim et al.'s correlated errors)—cannot be performed. The paper defers this to "future work." But if the error-similarity analysis is deferred and the variance decomposition fails at the gate, what empirical result does the paper actually deliver? The answer is: the gate itself. But the gate is a diagnostic tool, not a finding. The paper may be better positioned as a methods paper (the gate) rather than an empirical paper.

**Status: Addressed.** Section 11.1 explicitly states "No model-by-item correlation claim is made from the empirical data." However, the practical impact of having no usable empirical finding beyond the gate diagnostic should be discussed more candidly.

### Criticism C4: Synthetic 30-model design is not validated against real data

The design-space analysis (Section 10) identifies a 30-model sufficient configuration (6 families × 8 eras, rank 13/13, κ=93, VIF=2.1). This is validated only through simulation—no real models have been evaluated under this design. The paper presents this as a practical recommendation, but the simulation assumes the D2 occupancy pattern, which may not match the actual 30-model population's occupancy. The recommendation to evaluate 30 models is a significant compute commitment, and the simulation validation does not guarantee the real design will achieve the same conditioning.

**Status: Partially addressed.** Section 10.3 says "This is one sufficient configuration, not the universal minimum." Recommend adding a caveat that the simulation-validated conditioning may not transfer to the real population.

### Criticism C5: Overclaiming in the abstract

The abstract states the gate "fails all three pre-specified gate diagnostics" and that the failure is "structural." This is correct but could be read as claiming the 16-model population is uniquely flawed. In reality, ANY convenience sample of LLMs is likely to fail the gate because model families are not evenly represented and release quarters are not evenly spaced. The negative result is not surprising—it is the expected outcome for any non-experimental model population. The paper should acknowledge that the gate failure is generic, not specific to this population.

**Status: Partially addressed.** Section 12.4 says "the 16-model population was assembled from publicly available models without regard to the identifiability requirements." Recommend adding that the gate failure is the expected outcome for convenience samples, making the gate's value as a pre-screening tool clearer.

### Criticism C6: The evaluation validity caveat is buried

The most damaging finding in the paper—that 37.5% of models produce chance-level accuracy and one family shows a 57pp degradation—is buried in Section 7.6 and reiterated in Section 13. This finding has implications beyond this paper: it suggests that published MMLU scores for some open-weight models may be artifacts of prompt formatting. The paper treats this as a caveat rather than a finding, but it deserves more prominence. At minimum, it should be listed as a limitation in the abstract or conclusion.

**Status: Partially addressed.** Section 7.6 provides a detailed discussion, but the finding is not mentioned in the abstract or conclusion. Recommend adding a sentence to the conclusion acknowledging the evaluation validity concern.

### Criticism C7: External validity is very limited

The paper is scoped to open-weight models on MMLU. It does not generalize to: closed models (GPT-4, Claude), non-English benchmarks, multi-modal models, or models released after mid-2026. The practical audience—practitioners assembling model portfolios—may find the scope too narrow to be actionable. The paper's recommendation to "apply the gating procedure before any real-data variance-attribution claim" is sound, but the demonstrated evidence is limited to a single benchmark with a convenience sample that mostly fails the gate.

**Status: Addressed.** Section 13, items 10 and 11 acknowledge external validity limitations. However, the paper could be more explicit about what findings DO generalize (the gate framework) vs. what does not (the specific variance shares).

### Criticism C8: The "simulation-validated estimator" is validated on its own DGP

The REML estimator is validated on data generated by the same model (Y = μ + α_f + β_e + u) that it estimates. This is circular: any consistent estimator will recover its own DGP's parameters. The validation shows the estimator works when the model is correctly specified. The more important question is robustness to model misspecification: what happens when the true DGP includes family-era interactions, non-normal effects, or heteroscedastic residuals? The paper acknowledges the interaction is non-identified (Section 6.6) but does not simulate misspecification.

**Status: Partially addressed.** Section 6.5 discusses liability (binary vs. continuous) and Section 6.6 discusses the interaction. But robustness to general misspecification (heteroscedasticity, non-normality) is not simulated. Recommend adding a brief robustness check.

**Overall verdict: MAJOR REVISION.** The paper identifies a real and important problem (non-identifiable variance decomposition in convenience model samples) and provides a useful diagnostic tool (the identifiability gate). However, the empirical contribution is severely limited by (a) invalid per-question data, (b) evaluation validity concerns for 37.5% of models, and (c) the gate's negative result being the expected outcome for convenience samples. The paper would benefit from reframing as a methods paper (the gate) rather than an empirical paper, or from substantially expanding the empirical evaluation to include a valid population.

---

## Summary of Critical Issues

| Issue | Reviewer | Severity | Addressed? |
|---|---|---|---|
| Formal proof of Proposition 1 | A | High | Partially |
| REML robustness to variance heterogeneity | A | Medium | No |
| Profile likelihood threshold (multiplicity) | A | Medium | No |
| "Foundation model" framing vs. instruction-tuned | B | Medium | No |
| 47-model candidate population construction | B | Medium | No |
| Evaluation validity for 6/16 models | B, C | High | Partially |
| Relationship among 16/22/47 populations | C | Medium | Partially |
| Practical value of gate (negative result) | C | High | No |
| Reframing as methods paper | C | High | No |
| Robustness to model misspecification | A, C | Medium | Partially |
