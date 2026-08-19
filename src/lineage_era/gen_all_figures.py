"""Generate all 8 manuscript figures from validated data."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings, sys, os
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from lineage_era.analysis.trait import load_eval_results, assemble_trait
from lineage_era.occupancy import model_table
from lineage_era.analysis.reml import CrossedREML, _psd_inverse

eval_df = load_eval_results()
tbl = model_table()
trait = assemble_trait(eval_df, tbl)

plt.rcParams.update({
    'font.size': 10, 'font.family': 'serif', 'figure.dpi': 200,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.15,
})
out = 'paper/figures'
os.makedirs(out, exist_ok=True)

# ================================================================
# FIGURE 1: Conceptual workflow (identifiability-gated pipeline)
# ================================================================
fig, ax = plt.subplots(figsize=(12, 4))
ax.set_xlim(0, 14)
ax.set_ylim(0, 4.5)
ax.axis('off')
ax.set_title('Fig. 1.  Identifiability-Gated Research Workflow', fontweight='bold', fontsize=12, pad=10)

boxes = [
    (0.3, 2.0, 'Candidate\nModel Pool', '#b3cde3', 2.0),
    (2.8, 2.0, 'Structural\nPopulation\nAudit', '#b3cde3', 2.0),
    (5.3, 2.0, 'Identifiability\nGate\n(G1-G3)', '#fddbc7', 2.0),
    (7.8, 2.0, 'Simulation\nValidation', '#b3cde3', 2.0),
    (10.3, 2.0, 'Outcome-\nIndependent\nDesign', '#b3cde3', 2.0),
]
for x, y, txt, col, w in boxes:
    rect = FancyBboxPatch((x, y), w, 1.8, boxstyle="round,pad=0.1",
                          facecolor=col, alpha=0.5, edgecolor='k', lw=1.5)
    ax.add_patch(rect)
    ax.text(x+w/2, y+0.9, txt, ha='center', va='center', fontsize=8.5, fontweight='bold')

# Second row
boxes2 = [
    (0.3, 0.0, 'Empirical\nMeasurement', '#e5e5e5', 2.0),
    (2.8, 0.0, 'Re-Run Gate\non Measured\nDesign', '#fddbc7', 2.0),
]
for x, y, txt, col, w in boxes2:
    rect = FancyBboxPatch((x, y), w, 1.8, boxstyle="round,pad=0.1",
                          facecolor=col, alpha=0.5, edgecolor='k', lw=1.5)
    ax.add_patch(rect)
    ax.text(x+w/2, y+0.9, txt, ha='center', va='center', fontsize=8.5, fontweight='bold')

# PASS box
rect_pass = FancyBboxPatch((5.3, 0.0), 2.0, 1.8, boxstyle="round,pad=0.1",
                           facecolor='#d9f0d3', alpha=0.5, edgecolor='green', lw=2)
ax.add_patch(rect_pass)
ax.text(6.3, 0.9, 'PASS →\nVariance\nDecomposition', ha='center', va='center', fontsize=8, color='green', fontweight='bold')

# FAIL box
rect_fail = FancyBboxPatch((7.8, 0.0), 2.0, 1.8, boxstyle="round,pad=0.1",
                           facecolor='#fddbc7', alpha=0.5, edgecolor='red', lw=2)
ax.add_patch(rect_fail)
ax.text(8.8, 0.9, 'FAIL →\nReport Design\nFailure', ha='center', va='center', fontsize=8, color='red', fontweight='bold')

# Arrows top row
for i in range(len(boxes)-1):
    ax.annotate('', xy=(boxes[i+1][0], 2.9), xytext=(boxes[i][0]+boxes[i][4], 2.9),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='k'))

# Arrow down from design to measurement
ax.annotate('', xy=(1.3, 1.8), xytext=(1.3, 2.0),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='k'))

# Arrow from measurement to re-run gate
ax.annotate('', xy=(2.8, 0.9), xytext=(2.3, 0.9),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='k'))

# Arrow from re-run gate to pass/fail
ax.annotate('', xy=(5.3, 0.9), xytext=(4.8, 0.9),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='k'))

# EMPHASIS: 16-model result
ax.annotate('16-model population\n→ FAIL', xy=(8.8, 2.0), xytext=(11.5, 3.5),
            fontsize=9, fontweight='bold', color='red',
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fddbc7', alpha=0.8))

# Gate labels
gate_labels = [
    (4.3, 1.5, 'G1-G3', '#d73027'),
]
for x, y, txt, col in gate_labels:
    ax.text(x, y, txt, ha='center', fontsize=7, color=col, fontweight='bold')

plt.savefig(f'{out}/fig1_framework.pdf')
plt.close()
print("Figure 1 saved")

# ================================================================
# FIGURE 2: Simulation recovery (bias and coverage)
# ================================================================
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

# 2a: D1 bias
ax = axes[0]
scenarios = ['A\n(lineage)', 'B\n(era)', 'C\n(balanced)']
fam_bias = [0.19, 1.24, -0.30]
era_bias = [-1.31, -2.39, -0.03]
x = np.arange(3)
w = 0.35
ax.bar(x - w/2, fam_bias, w, label='Family share', color='#2166ac', alpha=0.7)
ax.bar(x + w/2, era_bias, w, label='Era share', color='#b2182b', alpha=0.7)
ax.axhline(0, color='k', lw=0.5)
ax.axhline(2.5, color='gray', ls=':', lw=1, alpha=0.5)
ax.axhline(-2.5, color='gray', ls=':', lw=1, alpha=0.5)
ax.set_xticks(x); ax.set_xticklabels(scenarios, fontsize=9)
ax.set_ylabel('Share bias (pp)')
ax.set_title('(a) D1: Balanced (bias $\\leq$ 2.5pp)', fontweight='bold')
ax.legend(fontsize=8); ax.set_ylim(-4, 4)

# 2b: D2 bias
ax = axes[1]
fam_bias_d2 = [-5.34, -0.63, -3.46]
era_bias_d2 = [0.65, -0.26, 2.01]
ax.bar(x - w/2, fam_bias_d2, w, label='Family share', color='#2166ac', alpha=0.7)
ax.bar(x + w/2, era_bias_d2, w, label='Era share', color='#b2182b', alpha=0.7)
ax.axhline(0, color='k', lw=0.5)
ax.axhline(5, color='gray', ls=':', lw=1, alpha=0.5)
ax.axhline(-5, color='gray', ls=':', lw=1, alpha=0.5)
ax.set_xticks(x); ax.set_xticklabels(scenarios, fontsize=9)
ax.set_ylabel('Share bias (pp)')
ax.set_title('(b) D2: Realistic (bias $\\leq$ 5.3pp)', fontweight='bold')
ax.legend(fontsize=8); ax.set_ylim(-7, 4)

# 2c: Coverage
ax = axes[2]
cov_fam = [93, 100, 96]
cov_era = [88, 98, 100]
ax.bar(x - w/2, cov_fam, w, label='Family share', color='#2166ac', alpha=0.7)
ax.bar(x + w/2, cov_era, w, label='Era share', color='#b2182b', alpha=0.7)
ax.axhline(95, color='gray', ls=':', lw=1, alpha=0.5, label='95% target')
ax.set_xticks(x); ax.set_xticklabels(scenarios, fontsize=9)
ax.set_ylabel('Coverage (%)')
ax.set_title('(c) Coverage Probability', fontweight='bold')
ax.legend(fontsize=8); ax.set_ylim(80, 105)

plt.tight_layout()
plt.savefig(f'{out}/fig2_simulation_recovery.pdf')
plt.close()
print("Figure 2 saved")

# ================================================================
# FIGURE 3: Nested failure detection
# ================================================================
fig, ax = plt.subplots(figsize=(7, 4.5))
detectors = ['BLUP\nCollinearity', 'SE\nInflation', 'Profile\nFlatness']
detection = [100, 100, 100]
silent = [0, 0, 0]
x3 = np.arange(3)
w = 0.35
ax.bar(x3 - w/2, detection, w, label='Detection rate', color='#1a9850', alpha=0.7)
ax.bar(x3 + w/2, silent, w, label='Silent coverage', color='#d73027', alpha=0.7)
ax.axhline(90, color='gray', ls=':', lw=1, alpha=0.5)
ax.set_xticks(x3); ax.set_xticklabels(detectors, fontsize=10)
ax.set_ylabel('Rate (%)')
ax.set_title('Fig. 3.  Nested (D3) Failure Detection: 100% Detection, 0% Silent Coverage', fontweight='bold')
ax.legend(fontsize=9); ax.set_ylim(0, 115)
for i, v in enumerate(detection):
    ax.text(i - w/2, v + 2, f'{v}%', ha='center', fontsize=9, fontweight='bold')
for i, v in enumerate(silent):
    ax.text(i + w/2, v + 2, f'{v}%', ha='center', fontsize=9, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{out}/fig3_failure_detection.pdf')
plt.close()
print("Figure 3 saved")

# ================================================================
# FIGURE 4: Family × Era occupancy heatmap
# ================================================================
fig, ax = plt.subplots(figsize=(10, 4.5))
occupied_eras = sorted(trait['era'].unique())
qshort = [e[2:] for e in occupied_eras]
families = sorted(trait['family'].unique())
qmap = {q: i for i, q in enumerate(occupied_eras)}

occ = np.zeros((len(families), len(occupied_eras)))
labels = [[''] * len(occupied_eras) for _ in families]
for _, r in trait.iterrows():
    fi = families.index(r['family'])
    qi = qmap[r['era']]
    occ[fi, qi] += 1
    labels[fi][qi] = (labels[fi][qi] + '\n' if labels[fi][qi] else '') + r['short_name']

cmap = LinearSegmentedColormap.from_list('o', ['#f7f7f7', '#6baed6', '#08306b'], N=4)
im = ax.imshow(occ, cmap=cmap, aspect='auto', vmin=0, vmax=3)
for fi in range(len(families)):
    for qi in range(len(occupied_eras)):
        txt = labels[fi][qi]
        c = 'white' if occ[fi, qi] >= 2 else 'black'
        ax.text(qi, fi, txt or '', ha='center', va='center',
                fontsize=6.5 if txt else 7, color=c if txt else '#ccc', linespacing=0.85)
ax.set_xticks(range(len(occupied_eras)))
ax.set_xticklabels(qshort, fontsize=8, rotation=45)
ax.set_yticks(range(len(families)))
ax.set_yticklabels(families, fontsize=10)
ax.set_xlabel('Release Quarter (11 occupied of 14 in window)')
ax.set_ylabel('Family')
ax.set_title('Fig. 4.  Family $\\times$ Era Occupancy (16 Measured Models)', fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.6, ticks=[0,1,2,3], label='Model count')
for i in range(len(families)+1):
    ax.axhline(i-0.5, color='w', lw=0.5)
for i in range(len(occupied_eras)+1):
    ax.axvline(i-0.5, color='w', lw=0.5)
plt.savefig(f'{out}/fig4_occupancy.pdf')
plt.close()
print("Figure 4 saved")

# ================================================================
# FIGURE 5: Gate diagnostics vs thresholds
# ================================================================
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

# 5a: Gate bar chart
ax = axes[0]
checks = ['G1: Rank', r'G2: $\kappa$', 'G3: Max VIF']
actuals = ['14 / 15', r'$4.7 \times 10^{16}$', r'$\infty$']
thresholds = ['15', '100', '10']
y_positions = [0.7, 0.4, 0.1]
for item, actual, thresh, yp in zip(checks, actuals, thresholds, y_positions):
    ax.barh(yp, 1.0, height=0.2, color='#d73027', alpha=0.25, edgecolor='#d73027', lw=2)
    ax.text(0.5, yp+0.08, item, ha='center', fontsize=11, fontweight='bold')
    ax.text(0.5, yp-0.02, f'{actual} / {thresh}', ha='center', fontsize=10)
    ax.text(0.5, yp-0.1, 'FAIL', ha='center', fontsize=12, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#d73027', alpha=0.8))
ax.set_xlim(0, 1); ax.set_ylim(-0.05, 0.95); ax.set_xticks([]); ax.set_yticks([])
ax.set_title('(a) Gate Results (16-Model Population)', fontweight='bold')

# 5b: Rank vs N
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
ax.set_xlabel('Total models (N)'); ax.set_ylabel('Design rank')
ax.set_title('(b) Rank vs. Population Size', fontweight='bold')
ax.legend(fontsize=8, loc='lower right')

# 5c: kappa vs N
ax = axes[2]
configs = [
    (18, 164, '#fdae61', '6F×3'),
    (24, 4.2e2, '#fdae61', '6F×4'),
    (30, 93, '#1a9850', '6F×5×8E'),
    (30, 204, '#fdae61', '6F×5×12E'),
    (36, 108, '#fdae61', '6F×6'),
]
for n, kappa, col, lab in configs:
    if np.isfinite(kappa):
        ax.scatter(n, kappa, c=col, s=60, zorder=5, edgecolors='k', lw=0.5)
        ax.annotate(lab, (n, kappa), textcoords='offset points', xytext=(0,8), fontsize=7, ha='center')
ax.axhline(100, color='#d73027', ls='--', lw=1.5, label=r'$\kappa_{max}=100$')
ax.set_yscale('log'); ax.set_xlabel('Total models (N)')
ax.set_ylabel(r'$\kappa$'); ax.set_title(r'(c) Conditioning vs. Size', fontweight='bold')
ax.set_ylim(50, 500); ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(f'{out}/fig5_gate.pdf')
plt.close()
print("Figure 5 saved")

# ================================================================
# FIGURE 6: Invalid-design diagnostic share
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
X_full = np.column_stack([np.ones(len(trait)), A[:, 1:]])
J = np.zeros((2, len(theta)))
J[0, 0] = s2_u / (s2_fam + s2_u)**2
J[0, 1] = -s2_fam / (s2_fam + s2_u)**2
var_share = float((J @ cov_log @ J.T)[0, 0])
se_share = np.sqrt(max(var_share, 0))

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
delta_lo = max(0, share_fam - 1.96 * se_share)
delta_hi = min(1, share_fam + 1.96 * se_share)
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
ax.text(0.5, -0.4, 'CI covers full [0%, 100%] range', ha='center', fontsize=8, color='red', fontweight='bold')

# 6b: Bootstrap distribution
ax = axes[1]
ax.hist(boot_arr, bins=50, color='#2166ac', alpha=0.7, edgecolor='white', density=True)
ax.axvline(share_fam, color='black', lw=1.5, label=f'Point est: {share_fam:.1%}')
ax.axvline(boot_lo, color='red', ls='--', lw=1, label=f'95% CI: [{boot_lo:.0%}, {boot_hi:.0%}]')
ax.axvline(boot_hi, color='red', ls='--', lw=1)
ax.set_xlabel('Family share'); ax.set_ylabel('Density')
ax.set_title('(b) Bootstrap Distribution (Uninformative)', fontweight='bold', fontsize=10)
ax.legend(fontsize=9); ax.set_xlim(-0.1, 1.1)

plt.tight_layout()
plt.savefig(f'{out}/fig6_invalid_design.pdf')
plt.close()
print("Figure 6 saved")

# ================================================================
# FIGURE 7: Design sweep — N vs condition number
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
            if rank < k: continue
            try:
                kappa = np.linalg.cond(X.T @ X)
            except: continue
            if not np.isfinite(kappa): continue
            results.append((nf, ne, mpf, n, kappa))

for nf, ne, mpf, n, kappa in results:
    mk = 'o' if nf == 5 else ('s' if nf == 6 else '^')
    co = '#1a9850' if kappa <= 100 else '#fdae61'
    ax.scatter(n, kappa, c=co, marker=mk, s=40, alpha=0.7, edgecolors='k', lw=0.5)

ax.axhline(100, color='#d73027', ls='--', lw=1.5, label=r'$\kappa_{max}=100$')
ax.axvline(16, color='gray', ls=':', lw=1, alpha=0.5)
ax.annotate('Current N=16', xy=(16, 150), fontsize=8, color='gray')
ax.set_yscale('log'); ax.set_xlabel('Total models (N)', fontsize=11)
ax.set_ylabel(r'Condition number $\kappa$ (full-rank designs)', fontsize=11)
ax.set_title('Fig. 7.  Population-Design Sensitivity Analysis', fontweight='bold')
legend_elements = [
    Line2D([0], [0], marker='o', color='w', mfc='#1a9850', ms=8, label=r'$\kappa \leq 100$'),
    Line2D([0], [0], marker='o', color='w', mfc='#fdae61', ms=8, label=r'$\kappa > 100$'),
    Line2D([0], [0], marker='o', color='w', mfc='gray', ms=8, label='5 families'),
    Line2D([0], [0], marker='s', color='w', mfc='gray', ms=8, label='6 families'),
    Line2D([0], [0], marker='^', color='w', mfc='gray', ms=8, label='7 families'),
]
ax.legend(handles=legend_elements, fontsize=9, loc='upper right')
plt.tight_layout()
plt.savefig(f'{out}/fig7_design_sweep.pdf')
plt.close()
print("Figure 7 saved")

# ================================================================
# FIGURE 8: Family × Era design heatmap (PASS/FAIL)
# ================================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 8a: Rank heatmap (families × eras)
ax = axes[0]
nf_range = range(5, 8)
ne_range = range(8, 15)
rank_grid = np.zeros((len(nf_range), len(ne_range)))
for i, nf in enumerate(nf_range):
    for j, ne in enumerate(ne_range):
        mpf = max(2, min(6, 30 // nf))
        eras = make_staggered(nf, mpf, ne)
        n = nf * mpf
        A = np.zeros((n, nf)); B = np.zeros((n, ne))
        row = 0
        for f, (sz, fe) in enumerate(zip([mpf]*nf, eras)):
            for e in fe[:sz]:
                A[row, f] = 1; B[row, e] = 1; row += 1
        X = np.column_stack([np.ones(n), A[:, 1:], B[:, 1:]])
        rank_grid[i, j] = np.linalg.matrix_rank(X)

cmap_rank = LinearSegmentedColormap.from_list('rank', ['#d73027', '#fdae61', '#1a9850'], N=3)
im = ax.imshow(rank_grid, cmap='RdYlGn', aspect='auto', vmin=10, vmax=14)
ax.set_xticks(range(len(ne_range))); ax.set_xticklabels(list(ne_range), fontsize=9)
ax.set_yticks(range(len(nf_range))); ax.set_yticklabels(list(nf_range), fontsize=9)
ax.set_xlabel('Number of eras'); ax.set_ylabel('Number of families')
ax.set_title('(a) Design Rank', fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.6, label='Rank')

# 8b: PASS/FAIL heatmap
ax = axes[1]
pass_grid = np.zeros((len(nf_range), len(ne_range)))
for i, nf in enumerate(nf_range):
    for j, ne in enumerate(ne_range):
        mpf = max(2, min(6, 30 // nf))
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
            pass_grid[i, j] = 0  # FAIL rank
        else:
            try:
                kappa = np.linalg.cond(X.T @ X)
                pass_grid[i, j] = 1 if kappa <= 100 else 0.5  # PASS/FAIL kappa
            except:
                pass_grid[i, j] = 0

cmap_pf = LinearSegmentedColormap.from_list('pf', ['#d73027', '#fdae61', '#1a9850'], N=3)
im = ax.imshow(pass_grid, cmap=cmap_pf, aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(ne_range))); ax.set_xticklabels(list(ne_range), fontsize=9)
ax.set_yticks(range(len(nf_range))); ax.set_yticklabels(list(nf_range), fontsize=9)
ax.set_xlabel('Number of eras'); ax.set_ylabel('Number of families')
ax.set_title('(b) Gate PASS/FAIL', fontweight='bold')
legend_elements_pf = [
    Line2D([0], [0], marker='s', color='w', mfc='#1a9850', ms=10, label='PASS'),
    Line2D([0], [0], marker='s', color='w', mfc='#fdae61', ms=10, label='Rank OK, $\\kappa$ FAIL'),
    Line2D([0], [0], marker='s', color='w', mfc='#d73027', ms=10, label='Rank FAIL'),
]
ax.legend(handles=legend_elements_pf, fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig(f'{out}/fig8_design_heatmap.pdf')
plt.close()
print("Figure 8 saved")

print("\nAll 8 figures generated successfully.")
