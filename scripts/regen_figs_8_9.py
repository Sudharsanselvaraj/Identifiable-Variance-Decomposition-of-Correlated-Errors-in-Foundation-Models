#!/usr/bin/env python3
"""Regenerate Figures 8 and 9 (rank vs N, kappa vs N) from sweep_results.csv.

Produces vector PDFs for the IEEE Access manuscript.
No G3 labeling — uses the current manuscript's gate terminology.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "results" / "design_space" / "sweep_results.csv"
OUTDIR = ROOT / "paper" / "figures"

# Read sweep data
rows = []
with open(SWEEP) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            'F': int(row['F']),
            'E': int(row['E']),
            'M': int(row['M']),
            'N': int(row['N']),
            'rank': int(row['rank']),
            'p': int(row['p']),
            'kappa': float(row['kappa']),
            'vif': float(row['vif']),
            'crossing': row['crossing'] == 'True',
            'connected': row['connected'] == 'True',
            'rank_pass': row['rank_pass'] == 'True',
            'kappa_pass': row['kappa_pass'] == 'True',
            'vif_pass': row['vif_pass'] == 'True',
            'overall_pass': row['overall_pass'] == 'True',
        })

# 16-model measured population (from sweep_results.csv row 1)
# Not in sweep — it's a special case. Add it manually.
measured_16 = {
    'N': 16, 'F': 5, 'E': 11, 'rank': 14, 'p': 15,
    'kappa': 4.7e16, 'rank_pass': False, 'overall_pass': False
}

# 22-model selected candidate
candidate_22 = {
    'N': 22, 'F': 6, 'E': 14, 'rank': 19, 'p': 19,
    'kappa': 1100, 'rank_pass': True, 'overall_pass': False
}

# Minimum passing config from sweep
passing_30 = {
    'N': 30, 'F': 6, 'E': 8, 'M': 5, 'rank': 13, 'p': 13,
    'kappa': 93.0, 'overall_pass': True
}

# ============================================================
# Figure 8: Population size (N) versus rank
# ============================================================
fig8, ax8 = plt.subplots(figsize=(3.5, 2.8))

for r in rows:
    if r['overall_pass']:
        color, marker, ms = '#2ca02c', 'o', 5
    elif r['rank_pass'] and not r['kappa_pass']:
        color, marker, ms = '#d4a017', 'o', 5
    else:
        color, marker, ms = '#999999', 'o', 3.5
    ax8.scatter(r['N'], r['rank'], c=color, marker=marker, s=ms**2,
                edgecolors='none', alpha=0.7, zorder=2)

# Mark passing config
ax8.scatter(passing_30['N'], passing_30['rank'], c='#2ca02c', marker='*',
            s=120, edgecolors='black', linewidths=0.5, zorder=5,
            label='Pass (N=30, F=6, E=8)')

# Mark 16-model measured
ax8.scatter(measured_16['N'], measured_16['rank'], c='red', marker='*',
            s=120, edgecolors='black', linewidths=0.5, zorder=5,
            label='16-model measured (rank 14/15)')

# Mark 22-model candidate
ax8.scatter(candidate_22['N'], candidate_22['rank'], c='#d4a017', marker='*',
            s=120, edgecolors='black', linewidths=0.5, zorder=5,
            label='22-model candidate (rank 19/19)')

ax8.set_xlabel('Population size (N)', fontsize=8)
ax8.set_ylabel('Rank', fontsize=8)
ax8.set_title('(a) Population size vs. rank', fontsize=9, fontweight='bold')
ax8.legend(fontsize=5.5, loc='lower right', framealpha=0.9)
ax8.tick_params(labelsize=7)
ax8.set_xlim(5, 48)
ax8.set_ylim(5, 22)

fig8.tight_layout()
fig8.savefig(OUTDIR / 'fig5b_rank_vs_population.pdf', format='pdf', dpi=300)
fig8.savefig(OUTDIR / 'fig5b_rank_vs_population.png', format='png', dpi=300)
print("Saved fig5b_rank_vs_population.pdf")
plt.close(fig8)

# ============================================================
# Figure 9: Conditioning (kappa) versus population size
# ============================================================
fig9, ax9 = plt.subplots(figsize=(3.5, 2.8))

# Plot all full-rank designs (finite kappa only)
kappa_vals = []
n_vals = []
for r in rows:
    if r['rank_pass'] and r['kappa'] < 1e15:
        kappa_vals.append(r['kappa'])
        n_vals.append(r['N'])
        color = '#2ca02c' if r['overall_pass'] else '#d4a017'
        ax9.scatter(r['N'], r['kappa'], c=color, marker='o', s=5**2,
                    edgecolors='none', alpha=0.7, zorder=2)

# Mark passing config
ax9.scatter(passing_30['N'], passing_30['kappa'], c='#2ca02c', marker='*',
            s=120, edgecolors='black', linewidths=0.5, zorder=5,
            label='Pass (N=30, $\kappa$=93)')

# Mark 16-model measured (off-scale, at top)
ax9.scatter(measured_16['N'], 1e17, c='red', marker='*', s=120,
            edgecolors='black', linewidths=0.5, zorder=5,
            label='16-model ($\kappa$=4.7$\\times10^{16}$)')

# Mark 22-model candidate
ax9.scatter(candidate_22['N'], candidate_22['kappa'], c='#d4a017', marker='*',
            s=120, edgecolors='black', linewidths=0.5, zorder=5,
            label='22-model ($\kappa$=1100)')

# kappa = 100 threshold line
ax9.axhline(y=100, color='red', linestyle='--', linewidth=0.8, alpha=0.7,
            label='$\kappa$ = 100 threshold', zorder=3)

ax9.set_yscale('log')
ax9.set_xlabel('Population size (N)', fontsize=8)
ax9.set_ylabel('$\\kappa(X^\\top X)$', fontsize=8)
ax9.set_title('(b) Conditioning vs. population size', fontsize=9, fontweight='bold')
ax9.legend(fontsize=5.5, loc='upper right', framealpha=0.9)
ax9.tick_params(labelsize=7)
ax9.set_xlim(5, 48)
ax9.set_ylim(50, 1e20)

fig9.tight_layout()
fig9.savefig(OUTDIR / 'fig5c_conditioning_vs_population.pdf', format='pdf', dpi=300)
fig9.savefig(OUTDIR / 'fig5c_conditioning_vs_population.png', format='png', dpi=300)
print("Saved fig5c_conditioning_vs_population.pdf")
plt.close(fig9)

print("Done — both figures regenerated without G3 labels.")
