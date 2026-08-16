# Co-Failure Ceiling β and the Diversification Counterfactual

Derivation for novelty claim C7 and the decision layer (RQ6). Status: **derived and
validated in simulation (2026-08-16)**; the empirical number is pending Phase 2 real
eval. Everything here uses the same DGP as `analysis/eval_simulate.py`, so the claim is
checked against the exact generative model, not just its own approximation.

## 1. Setup (the DGP)

Each model $m$ has an accuracy-scale trait

$$
\mathrm{acc}_m = \mu + \alpha_{f(m)} + \beta_{e(m)} + u_m,
\qquad
\alpha_f \sim \mathcal{N}(0, s^2_L),\ \beta_e \sim \mathcal{N}(0, s^2_E),\ u_m \sim \mathcal{N}(0, s^2_U),
$$

clamped to $[0.03, 0.97]$. On the logit scale $l_m = \operatorname{logit}(\mathrm{acc}_m)$
the delta method gives, at $\mu$,

$$
\operatorname{Var}(l_m) \approx \frac{s^2_L + s^2_E + s^2_U}{(\mu(1-\mu))^2},
\qquad
\operatorname{Cov}(l_m, l_{m'}) \approx \frac{s^2_L\,\mathbf{1}[f(m){=}f(m')] + s^2_E\,\mathbf{1}[e(m){=}e(m')]}{(\mu(1-\mu))^2}.
$$

When the trait is assembled and estimated *directly on the logit scale* — as it is in the
current pipeline (`trait = logit(accuracy)`), so the fitted $s^2_L, s^2_E, s^2_U$ are already
logit-scale variances — the denominator $(\mu(1-\mu))^2$ collapses to 1 and every formula
below is applied verbatim to the fitted components; the module `analysis/cofailure.py`
operates on the fitted trait scale and needs no delta-method rescaling.

Per question $i$ (shared item difficulty $\delta_i \sim \mathcal{N}(0, \sigma^2_\delta)$):

$$
p_{mi} = \sigma(l_m + \delta_i), \qquad E_{mi} \sim \mathrm{Bernoulli}(1 - p_{mi})
$$

where $E_{mi}=1$ means model $m$ is wrong on item $i$. Because $1-\sigma(x)=\sigma(-x)$,
the all-wrong indicator for a pool $S$ of $k$ models on item $i$ has probability

$$
\beta_i(S) = \prod_{m \in S} \sigma(-l_m - \delta_i),
\qquad
\beta(S) = \mathbb{E}\Big[\prod_{m \in S} \sigma(-l_m - \delta_i)\Big],
$$

the expectation over $(\alpha,\beta,u,\delta)$. This is Chen's co-failure ceiling
(all-wrong rate), re-expressed as a functional of the variance components.

## 2. Closed form via the probit approximation

Use $\sigma(x) \approx \Phi(x/\kappa)$, $\kappa = 1.6$ (Amemiya's logistic–normal link,
optimal for relative error; 1.7 minimizes absolute error and $\pi/\sqrt 3$ matches the
logistic variance). The implementation defaults to $\kappa=1.6$, which tracks the exact
logistic DGP best for the orthant probabilities this claim relies on. Let
$\mu_l = \mathbb{E}[l_m]$ (the mean trait on the logit scale) and put
$W_m = l_m - \mu_l + \delta_i + \eta_m$ with $\eta_m \sim \mathcal{N}(0,\kappa^2)$ i.i.d.
The all-wrong event is $\{l_m + \delta_i + \eta_m < 0\} = \{W_m < -\mu_l\}$, so

$$
\beta(S) \approx \mathbb{P}(W_1 < -\mu_l, \dots, W_k < -\mu_l)
= \Phi_k(-\mu_l \mathbf{1}; \mathbf{0}, \Sigma),
$$

the $k$-variate normal CDF at the common threshold $-\mu_l$ (zero mean) with covariance

$$
\Sigma_{mm} = \operatorname{Var}(l_m) + \sigma^2_\delta + \kappa^2,
\qquad
\Sigma_{mm'} = \operatorname{Cov}(l_m, l_{m'}) + \sigma^2_\delta
\quad (m \neq m').
$$

Proof of the equality: $\Phi((-l_m-\delta)/\kappa) = \mathbb{P}(\eta_m < -l_m - \delta)$ with
$\eta_m \sim \mathcal{N}(0,\kappa^2)$ i.i.d., so the product is the probability that all of
$Z_m = l_m + \delta + \eta_m$ fall below zero; after centering, $(W_1,\dots,W_k)$ is jointly
normal with zero mean and the covariance above, and the event is $\{W_m < -\mu_l\}$.

**Special case — exchangeable pool** (all members same family and same era):
$\Sigma = v\,I_k + r\,\mathbf{1}\mathbf{1}^\top$ with $r = \frac{s^2_L+s^2_E}{(\mu(1-\mu))^2} + \sigma^2_\delta$,
and $\Phi_k$ reduces to a one-dimensional integral. Writing
$W_j = \sqrt r\,U + \sqrt{v-r}\,\varepsilon_j$ with $U, \varepsilon_j$ i.i.d. $\mathcal{N}(0,1)$,
the orthant probability at threshold $-\mu_l$ is
$\mathbb{E}_U\big[\Phi^k\big(\frac{-\mu_l - \sqrt r\,U}{\sqrt{v-r}}\big)\big]$
(equicorrelated orthant probability), which is stable for any $k$.

**Ceiling bound (Proposition C7a).** $\beta(S)$ is strictly increasing in each off-diagonal
$\Sigma_{mm'}$, hence in $s^2_L$ and $s^2_E$. Consequently the quantity
$s^2_L + s^2_E$ — the between-model covariance share of the trait — pins the co-failure
ceiling: an ensemble's all-wrong rate cannot drop below the level implied by
$s^2_L + s^2_E$ regardless of pool composition. This is the formal version of the AE
review M7 remark "$\sigma^2_L + \sigma^2_E$ bounds the all-wrong rate."

## 3. The diversification counterfactual (what a swap buys)

Fix a pool $S$ of $k$ models and swap one member $m$ for a model $m^*$ from an
**unrepresented family** $f^* \notin \{f(m): m \in S\}$, keeping pool size and the target's
era. Writing $\Sigma'$ for the covariance of $S' = (S \setminus \{m\}) \cup \{m^*\}$,
the only off-diagonals that change are those touching the swapped member:

$$
\Sigma_{m'm^*}' - \Sigma_{m'm} = -\,\frac{s^2_L}{(\mu(1-\mu))^2}
   + \frac{s^2_E}{(\mu(1-\mu))^2}\Big(\mathbf{1}[e(m^*) = e(m')] - \mathbf{1}[e(m) = e(m')]\Big).
$$

That is, the swap **removes $s^2_L$ from every pairwise covariance involving the replaced
model and retains $s^2_E$ exactly when the replacement shares the pool's era**.

**Swap value (Proposition C7b).** Define the diversification value
$\Delta\beta = \beta(S) - \beta(S') \ge 0$. For fixed total trait variance, item noise, and
pool/era configuration:

1. $\Delta\beta$ is non-decreasing in $s^2_L$ (the removed component);
2. $\Delta\beta$ is non-increasing in $s^2_E$ (the carried component): if the replacement is
   in an era no pool member occupies, the $s^2_E$ term vanishes and $\Delta\beta$ grows;
3. with both $s^2_L, s^2_E$ scaled up together (fixed $s^2_L/s^2_E$), $\Delta\beta$ grows
   sublinearly in $\sigma^2_\delta + \kappa^2$ contrast — the item-level noise dampens the
   ceiling movement.

The actionable reading for RQ6: **the marginal value of cross-family diversification is
governed by $s^2_L / (s^2_L + s^2_E)$, not by the unique share $s^2_U$** — model-specific
noise is diversifiable within a family for free, while era-common error is not removed by
a family swap.

## 4. What the pipeline computes

`analysis/cofailure.py` exposes, given a fitted partition $(s^2_L, s^2_E, s^2_U)$ and the
occupancy:

- `all_wrong_gaussian(...)` — $\beta(S)$ via the probit closed form (general MVN CDF,
  with the equicorrelated one-dimensional form for same-family–same-era pools);
- `all_wrong_montecarlo(...)` — $\beta(S)$ by exact DGP sampling (logistic link, no
  approximation) — the ground truth the closed form is validated against;
- `swap_counterfactual(...)` — $\beta(S)$, $\beta(S')$, $\Delta\beta$ for a designated swap;
- `report_block(...)` — the decision-layer Markdown block for `PHASE2_REPORT.md`.

Validation (in `test_cofailure.py`, mirrors the repo's simulation-first rule): the closed
form must track the exact DGP within a documented tolerance on scenario S1 (lineage-heavy),
S2 (era-heavy), S3 (balanced); and the swap monotonicities of Proposition C7b must hold —
$\Delta\beta$ larger under S1 than under S2 with all else equal.

## 5. Honesty guardrails

- The number is only a ceiling given the model and its estimated components; it inherits
  every caveat of the partition (6-family df, contamination channel, temporal drift).
- The counterfactual assumes the swapped-in model's trait is drawn from the fitted
  family/era distribution — i.e., $\sigma^2$ is transportable to unmeasured models. Stated,
  not assumed silently.
- Until Phase 2 real eval, every number produced here is simulation output and must carry
  the same SIMULATED provenance banner as the rest of the dry-run report.
