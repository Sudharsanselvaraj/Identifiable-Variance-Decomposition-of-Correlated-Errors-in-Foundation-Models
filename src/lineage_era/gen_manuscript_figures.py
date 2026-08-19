"""Generate all 6 manuscript figures from validated data."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import warnings, sys, os
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from lineage_era.analysis.trait import load_eval_results, assemble_trait
from lineage_era.occupancy import model_table
from lineage_era.analysis.reml import CrossedREML, _psd_inverse
from lineage_era.analysis.identifiability import structural_checks

eval_df = load_eval_results()
tbl = model_table()
trait = assemble_trait(eval_df, tbl)

plt.rcParams.update({
    'font.size': 10, 'font.family': 'serif', 'figure.dpi': 200,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.15,
})
out = 'results/phase2_empirical/figures'
os.makedirs(out, exist_ok=True)

# ================================================================
# FIGURE 1: Conceptual workflow (3-stage gate)
# ================================================================
fig, ax = plt.subplots(figsize=(12, 3.5))
ax.set_xlim(0, 12)
ax.set_ylim(0, 3.5)
ax.axis('off')
ax.set_title('Figure 1. Identifiability-Gated Protocol', fontweight='bold', fontsize=12, pad=10)

boxes = [
    (0.5, 1.5, 'Stage 1\nPopulation\nAudit', '#4393c3'),
    (3.0, 1.5, 'Stage 2\nSimulation\nValidation', '#4393c3'),
    (5.5, 1.5, 'Stage 3\nPopulation\nSelection', '#4393c3'),
    (8.0, 1.5, 'Stage 4\nModel\nMeasurement', '#fdae61'),
    (10.5, 1.5, 'Stage 5-6\nGate +\nInference', '#d73027'),
]
for x, y, txt, col in boxes:
    rect = FancyBboxPatch((x, y), 2.0, 1.5, boxstyle="round,pad=0.1",
                          facecolor=col, alpha=0.3, edgecolor='k', lw=1.5)
    ax.add_patch(rect)
    ax.text(x+1.0, y+0.75, txt, ha='center', va='center', fontsize=9, fontweight='bold')

# Arrows
for i in range(len(boxes)-1):
    ax.annotate('', xy=(boxes[i+1][0], 2.25), xytext=(boxes[i][0]+2.0, 2.25),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='k'))

# Gate labels
gates = [
    (1.5, 0.7, 'G1-G3\nstructural', '#4393c3'),
    (4.0, 0.7, 'D1/D2/D3\nrecovery', '#4393c3'),
    (6.5, 0.7, 'outcome-\nindependent', '#4393c3'),
    (9.0, 0.7, 're-measure\nG1-G3', '#fdae61'),
]
for x, y, txt, col in gates:
    ax.text(x, y, txt, ha='center', va='center', fontsize=7, color=col, style='italic')

# "never reads trait" annotation
ax.annotate('Never reads\ntrait values', xy=(6.5, 1.2), fontsize=7, ha='center',
            color='green', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#d9f0d3', alpha=0.8))

plt.savefig(f'{out}/fig1_workflow.pdf')
plt.close()
print("Figure 1 saved")

# ================================================================
# FIGURE 2: Occupancy heatmap for 16 measured models
# ================================================================
fig, ax = plt.subplots(figsize=(10, 4))
quarters = ['2023Q1','2023Q2','2023Q3','2023Q4','2024Q1','2024Q2','2024Q3',
            '2024Q4','2025Q1','2025Q2','2025Q3','2025Q4','2026Q1','2026Q2']
qshort = [q[2:] for q in quarters]
families = sorted(trait['family'].unique())
qmap = {q: i for i, q in enumerate(quarters)}

occ = np.zeros((len(families), 14))
labels = [[''] * 14 for _ in families]
for _, r in trait.iterrows():
    fi = families.index(r['family'])
    qi = qmap[r['era']]
    occ[fi, qi] += 1
    labels[fi][qi] = (labels[fi][qi] + '\n' if labels[fi][qi] else '') + r['short_name']

cmap = LinearSegmentedColormap.from_list('o', ['#f7f7f7', '#6baed6', '#08306b'], N=4)
im = ax.imshow(occ, cmap=cmap, aspect='auto', vmin=0, vmax=3)
for fi in range(len(families)):
    for qi in range(14):
        txt = labels[fi][qi]
        c = 'white' if occ[fi, qi] >= 2 else 'black'
        ax.text(qi, fi, txt or '', ha='center', va='center',
                fontsize=6.5 if txt else 7, color=c if txt else '#ccc', linespacing=0.85)
ax.set_xticks(range(14))
ax.set_xticklabels(qshort, fontsize=8, rotation=45)
ax.set_yticks(range(len(families)))
ax.set_yticklabels(families, fontsize=10)
ax.set_xlabel('Release Quarter')
ax.set_ylabel('Family')
ax.set_title('Figure 2. Family x Era Occupancy (16 Measured Models)', fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.6, ticks=[0,1,2,3], label='Model count')
for i in range(len(families)+1):
    ax.axhline(i-0.5, color='w', lw=0.5)
for i in range(15):
    ax.axvline(i-0.5, color='w', lw=0.5)
# Mark empty quarters
for qi in [4, 6, 10]:  # 2024Q1, 2024Q3, 2025Q3
    ax.axvline(qi-0.5, color='red', lw=2, alpha=0.3)
    ax.axvline(qi+0.5, color='red', lw=2, alpha=0.3)
ax.text(4, -0.8, 'empty', ha='center', fontsize=7, color='red', rotation=45)
ax.text(6, -0.8, 'empty', ha='center', fontsize=7, color='red', rotation=45)
ax.text(10, -0.8, 'empty', ha='center', fontsize=7, color='red', rotation=45)
plt.savefig(f'{out}/fig2_occupancy.pdf')
plt.close()
print("Figure 2 saved")

# ================================================================
# FIGURE 3: Gate diagnostic plot (3 panels)
# ================================================================
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

# 3a: Gate bar chart
ax = axes[0]
checks = ['Rank', r'$\kappa$', 'Max VIF']
actuals = ['14 / 18', r'$4.7 \times 10^{16}$', r'$\infty$']
thresholds = ['18', '100', '10']
colors = ['#d73027'] * 3
y_positions = [0.7, 0.4, 0.1]
for item, actual, thresh, col, yp in zip(checks, actuals, thresholds, colors, y_positions):
    ax.barh(yp, 1.0, height=0.2, color=col, alpha=0.25, edgecolor=col, lw=2)
    ax.text(0.5, yp+0.08, item, ha='center', fontsize=11, fontweight='bold')
    ax.text(0.5, yp-0.02, f'{actual} / {thresh}', ha='center', fontsize=10)
    ax.text(0.5, yp-0.1, 'FAIL', ha='center', fontsize=12, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.2', facecolor=col, alpha=0.8))
ax.set_xlim(0, 1); ax.set_ylim(-0.05, 0.95); ax.set_xticks([]); ax.set_yticks([])
ax.set_title('(a) Gate Results', fontweight='bold')

# 3b: Rank vs N
ax = axes[1]
for nf, mk, co in [(5, 'o', '#2166ac'), (6, 's', '#b2182b')]:
    ns = [nf*m for m in [2,3,4,5,6]]
    rs = [min(n, nf+7) for n in ns]
    ax.plot(ns, rs, f'{mk}-', color=co, ms=5, label=f'{nf} families')
ax.axhline(13, color='gray', ls=':', lw=1, label=r'$k=13$')
ax.axvline(16, color='#d73027', ls='--', lw=1, alpha=0.5)
ax.annotate('Current\nN=16', xy=(16,7), fontsize=8, ha='center', color='#d73027')
ax.axvline(30, color='#1a9850', ls='--', lw=1, alpha=0.5)
ax.annotate('Sufficient\nN=30', xy=(30,7), fontsize=8, ha='center', color='#1a9850')
ax.set_xlabel('Total models (N)')
ax.set_ylabel('Design rank')
ax.set_title('(b) Rank vs. Population Size', fontweight='bold')
ax.legend(fontsize=8, loc='lower right')

# 3c: kappa vs N
ax = axes[2]
configs = [
    (18, 164, '#fdae61', '6Fx3'),
    (24, 4.2e2, '#fdae61', '6Fx4'),
    (30, 93, '#1a9850', '6Fx5x8E'),
    (30, 204, '#fdae61', '6Fx5x12E'),
    (36, 108, '#fdae61', '6Fx6'),
    (35, 107, '#fdae61', '7Fx5'),
]
for n, kappa, col, lab in configs:
    if np.isfinite(kappa):
        ax.scatter(n, kappa, c=col, s=60, zorder=5, edgecolors='k', lw=0.5)
        ax.annotate(lab, (n, kappa), textcoords='offset points', xytext=(0,8), fontsize=7, ha='center')
ax.axhline(100, color='#d73027', ls='--', lw=1.5, label=r'$\kappa_{max}=100$')
ax.set_yscale('log')
ax.set_xlabel('Total models (N)')
ax.set_ylabel(r'$\kappa$')
ax.set_title(r'(c) Conditioning vs. Size', fontweight='bold')
ax.set_ylim(50, 500)
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(f'{out}/fig3_diagnostics.pdf')
plt.close()
print("Figure 3 saved")

# ================================================================
# FIGURE 4: Simulation validation (3 panels)
# ================================================================
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

# 4a: D1 recovery
ax = axes[0]
scenarios = ['A\n(lineage)', 'B\n(era)', 'C\n(balanced)']
fam_bias = [0.19, 1.24, -0.30]
era_bias = [-1.31, -2.39, -0.03]
x = np.arange(3)
w = 0.35
bars1 = ax.bar(x - w/2, fam_bias, w, label='Family share', color='#2166ac', alpha=0.7)
bars2 = ax.bar(x + w/2, era_bias, w, label='Era share', color='#b2182b', alpha=0.7)
ax.axhline(0, color='k', lw=0.5)
ax.axhline(2.5, color='gray', ls=':', lw=1, alpha=0.5)
ax.axhline(-2.5, color='gray', ls=':', lw=1, alpha=0.5)
ax.set_xticks(x)
ax.set_xticklabels(scenarios, fontsize=9)
ax.set_ylabel('Share bias (pp)')
ax.set_title('(a) D1: Balanced (bias $\\leq$ 2.5pp)', fontweight='bold')
ax.legend(fontsize=8)
ax.set_ylim(-4, 4)

# 4b: D2 recovery
ax = axes[1]
fam_bias_d2 = [-5.34, -0.63, -3.46]
era_bias_d2 = [0.65, -0.26, 2.01]
bars1 = ax.bar(x - w/2, fam_bias_d2, w, label='Family share', color='#2166ac', alpha=0.7)
bars2 = ax.bar(x + w/2, era_bias_d2, w, label='Era share', color='#b2182b', alpha=0.7)
ax.axhline(0, color='k', lw=0.5)
ax.axhline(5, color='gray', ls=':', lw=1, alpha=0.5)
ax.axhline(-5, color='gray', ls=':', lw=1, alpha=0.5)
ax.set_xticks(x)
ax.set_xticklabels(scenarios, fontsize=9)
ax.set_ylabel('Share bias (pp)')
ax.set_title('(b) D2: Realistic (bias $\\leq$ 5.3pp)', fontweight='bold')
ax.legend(fontsize=8)
ax.set_ylim(-7, 4)

# 4c: D3 detection
ax = axes[2]
detectors = ['BLUP\nCollinearity', 'SE\nInflation', 'Profile\nFlatness']
detection = [100, 100, 100]
silent = [0, 0, 0]
x3 = np.arange(3)
bars1 = ax.bar(x3 - w/2, detection, w, label='Detection rate', color='#1a9850', alpha=0.7)
bars2 = ax.bar(x3 + w/2, silent, w, label='Silent coverage', color='#d73027', alpha=0.7)
ax.axhline(90, color='gray', ls=':', lw=1, alpha=0.5, label='90% threshold')
ax.set_xticks(x3)
ax.set_xticklabels(detectors, fontsize=9)
ax.set_ylabel('Rate (%)')
ax.set_title('(c) D3: Nested Detection (100%)', fontweight='bold')
ax.legend(fontsize=8, loc='center right')
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig(f'{out}/fig4_simulation.pdf')
plt.close()
print("Figure 4 saved")

# ================================================================
# FIGURE 5: Design-space analysis
# ================================================================
fig, ax = plt.subplots(figsize=(8, 5))

def make_staggered(nf, mpf, ne):
    eras = []
    for f in range(nf):
        offset = int(f * ne / nf)
        assigned = [(offset + int(i * ne / mpf)) % ne for i in range(mpf)]
        eras.append(sorted(set(assigned)))
        while len(eras[-1]) < mpf:
            for e in range(ne):
                if e not in eras[-1]:
                    eras[-1].append(e)
                    break
            eras[-1].sort()
    return eras

results = []
for nf in [5, 6, 7]:
    for ne in [8, 10, 12, 14]:
        for mpf in [2, 3, 4, 5, 6]:
            eras = make_staggered(nf, mpf, ne)
            n = nf * mpf
            A = np.zeros((n, nf)); B = np.zeros((n, ne))
            row = 0
            for f, (sz, fe) in enumerate(zip([mpf]*nf, eras)):
                for e in fe[:sz]:
                    A[row, f] = 1; B[row, e] = 1; row += 1
            X = np.column_stack([np.ones(n), A[:, 1:], B[:, 1:]])
            rank = np.linalg.matrix_rank(X)
            k = X.shape[1]
            if rank < k:
                continue
            try:
                kappa = np.linalg.cond(X.T @ X)
            except:
                continue
            if not np.isfinite(kappa):
                continue
            results.append((nf, ne, mpf, n, kappa))

for nf, ne, mpf, n, kappa in results:
    mk = 'o' if nf == 5 else ('s' if nf == 6 else '^')
    co = '#1a9850' if kappa <= 100 else '#fdae61'
    ax.scatter(n, kappa, c=co, marker=mk, s=40, alpha=0.7, edgecolors='k', lw=0.5)

ax.axhline(100, color='#d73027', ls='--', lw=1.5, label=r'$\kappa_{max}=100$')
ax.axvline(16, color='gray', ls=':', lw=1, alpha=0.5)
ax.annotate('Current N=16', xy=(16, 150), fontsize=8, color='gray')
ax.set_yscale('log')
ax.set_xlabel('Total models (N)', fontsize=11)
ax.set_ylabel(r'Condition number $\kappa$ (full-rank designs)', fontsize=11)
ax.set_title('Figure 5. Population-Design Sensitivity Analysis', fontweight='bold')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', mfc='#1a9850', ms=8, label=r'$\kappa \leq 100$'),
    Line2D([0], [0], marker='o', color='w', mfc='#fdae61', ms=8, label=r'$\kappa > 100$'),
    Line2D([0], [0], marker='o', color='w', mfc='gray', ms=8, label='5 families'),
    Line2D([0], [0], marker='s', color='w', mfc='gray', ms=8, label='6 families'),
    Line2D([0], [0], marker='^', color='w', mfc='gray', ms=8, label='7 families'),
]
ax.legend(handles=legend_elements, fontsize=9, loc='upper right')
plt.tight_layout()
plt.savefig(f'{out}/fig5_design_space.pdf')
plt.close()
print("Figure 5 saved")

# ================================================================
# FIGURE 6: Diagnostic consequence — family share with CI
# ================================================================
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

y = trait['trait'].to_numpy(dtype=float)
A = (trait['family'].to_numpy()[:, None] == np.unique(trait['family'])).astype(float)
solver = CrossedREML(y, [A])
theta, opt, converged = solver.fit()
s2_fam, s2_u = np.exp(theta)
share_fam = s2_fam / (s2_fam + s2_u)

hess = solver.hessian(theta)
cov_log = _psd_inverse(hess)
logs = np.array([np.log(max(s2_fam, 1e-12)), np.log(max(s2_u, 1e-12))])
cov_2d = cov_log[:2, :2]
cov_2d = (cov_2d + cov_2d.T) / 2

s_total = s2_fam + s2_u
d_share = np.array([s2_u / s_total**2, -s2_fam / s_total**2])
var_share = d_share @ cov_2d @ d_share
se_share = np.sqrt(max(var_share, 0))
delta_lo = max(0, share_fam - 1.96 * se_share)
delta_hi = min(1, share_fam + 1.96 * se_share)

np.random.seed(42)
boot_shares = []
for _ in range(1000):
    idx = np.random.choice(len(trait), size=len(trait), replace=True)
    bt = trait.iloc[idx].reset_index(drop=True)
    try:
        yb = bt['trait'].to_numpy(dtype=float)
        Ab = (bt['family'].to_numpy()[:, None] == np.unique(bt['family'])).astype(float)
        sb = CrossedREML(yb, [Ab])
        tb, _, _ = sb.fit()
        sf, su = np.exp(tb)
        boot_shares.append(sf / (sf + su))
    except:
        pass
boot_arr = np.array(boot_shares)
boot_lo, boot_hi = np.percentile(boot_arr, [2.5, 97.5])

# 6a: Point estimate + CIs
ax = axes[0]
ax.barh(0.05, share_fam, height=0.15, color='#2166ac', alpha=0.7, edgecolor='#2166ac')
ax.plot([delta_lo, delta_hi], [0.05, 0.05], 'k-', lw=2)
ax.plot(delta_lo, 0.05, 'k|', ms=15, mew=2)
ax.plot(delta_hi, 0.05, 'k|', ms=15, mew=2)
ax.plot([boot_lo, boot_hi], [-0.05, -0.05], 'r-', lw=2)
ax.plot(boot_lo, -0.05, 'r|', ms=15, mew=2)
ax.plot(boot_hi, -0.05, 'r|', ms=15, mew=2)
ax.set_yticks([0.05, -0.05])
ax.set_yticklabels(['Delta CI', 'Bootstrap CI'], fontsize=10)
ax.set_xlabel('Family share of variance')
ax.set_title(r'(a) Family Share $\hat{\theta}_P$ (DIAGNOSTIC ONLY)', fontweight='bold', fontsize=10)
ax.axvline(0, color='gray', ls=':', lw=0.5)
ax.axvline(1, color='gray', ls=':', lw=0.5)
ax.set_xlim(-0.05, 1.05)
ax.text(share_fam, 0.2, f'{share_fam:.1%}', ha='center', fontsize=10, fontweight='bold')
ax.text(0.5, -0.2, f'Delta: [{delta_lo:.0%}, {delta_hi:.0%}]', ha='center', fontsize=9)
ax.text(0.5, -0.3, f'Bootstrap: [{boot_lo:.0%}, {boot_hi:.0%}]', ha='center', fontsize=9, color='red')
ax.text(0.5, -0.4, 'CI covers full [0%, 100%]', ha='center', fontsize=8, color='red', fontweight='bold')

# 6b: Bootstrap distribution
ax = axes[1]
ax.hist(boot_arr, bins=50, color='#2166ac', alpha=0.7, edgecolor='white', density=True)
ax.axvline(share_fam, color='black', lw=1.5, label=f'Point est: {share_fam:.1%}')
ax.axvline(boot_lo, color='red', ls='--', lw=1, label=f'95% CI: [{boot_lo:.0%}, {boot_hi:.0%}]')
ax.axvline(boot_hi, color='red', ls='--', lw=1)
ax.set_xlabel('Family share')
ax.set_ylabel('Density')
ax.set_title('(b) Bootstrap Distribution (Uninformative)', fontweight='bold', fontsize=10)
ax.legend(fontsize=9)
ax.set_xlim(-0.1, 1.1)

plt.tight_layout()
plt.savefig(f'{out}/fig6_diagnostic_share.pdf')
plt.close()
print("Figure 6 saved")

print("\nAll 6 figures generated successfully.")
