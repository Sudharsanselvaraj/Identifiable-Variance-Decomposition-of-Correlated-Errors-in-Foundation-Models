#!/usr/bin/env python3
"""
Design-space sweep for identifiability gate analysis.

Reconstructs the sweep logic from gen_all_figures.py (make_staggered + design
matrix construction) over the full parameter grid specified in Section X.A:
  - Families (F): 5-7
  - Eras (E): 8-14 (all integers)
  - Models per family (M): 2-6 (all integers)

For each (F, E, M) configuration, constructs a staggered family-era assignment,
builds the design matrix X = [1 | Z_F^(-) | Z_E^(-)], and evaluates:
  - Crossing (S1), Connectedness (S2), Rank (S3)
  - Condition number kappa(X'X) (N1, threshold 100)
  - Max VIF (N2, threshold 10)

Outputs: results/design_space/sweep_results.csv
"""
import numpy as np
import csv
import sys
from itertools import product


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


def check_crossing(eras, nf, ne):
    fam_span = [len(set(e_list)) for e_list in eras]
    if not all(s >= 2 for s in fam_span):
        return False
    era_count = [0] * ne
    for e_list in eras:
        for e in e_list:
            era_count[e] += 1
    return sum(1 for c in era_count if c >= 2) >= 2


def check_connected(eras, nf):
    adj = {f: set() for f in range(nf)}
    era_to_fams = {}
    for f, e_list in enumerate(eras):
        for e in e_list:
            era_to_fams.setdefault(e, []).append(f)
    for fams in era_to_fams.values():
        for i in range(len(fams)):
            for j in range(i + 1, len(fams)):
                adj[fams[i]].add(fams[j])
                adj[fams[j]].add(fams[i])
    visited = set()
    stack = [0]
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            stack.extend(adj[node] - visited)
    return len(visited) == nf


def compute_vif(X):
    n, p = X.shape
    if p <= 1:
        return 0.0
    Xc = X - X.mean(axis=0)
    vifs = []
    for j in range(1, p):
        mask = list(range(p))
        mask.pop(j)
        Xj = Xc[:, mask]
        resid = Xc[:, j] - Xj @ np.linalg.lstsq(Xj, Xc[:, j], rcond=None)[0]
        ss_res = np.sum(resid ** 2)
        ss_tot = np.sum((Xc[:, j] - Xc[:, j].mean()) ** 2)
        rj = 1.0 - ss_res / max(ss_tot, 1e-15)
        vif = 1.0 / max(1.0 - rj, 1e-15)
        vifs.append(vif)
    return max(vifs) if vifs else 0.0


def run_sweep():
    families_range = range(5, 8)
    eras_range = range(8, 15)
    mpf_range = range(2, 7)

    results = []
    total = 0

    for nf, ne, mpf in product(families_range, eras_range, mpf_range):
        total += 1
        n = nf * mpf
        era_assignments = make_staggered(nf, mpf, ne)

        A = np.zeros((n, nf))
        B = np.zeros((n, ne))
        row = 0
        for f, (sz, fe) in enumerate(zip([mpf] * nf, era_assignments)):
            for e in fe[:sz]:
                A[row, f] = 1
                B[row, e] = 1
                row += 1

        X = np.column_stack([np.ones(n), A[:, 1:], B[:, 1:]])
        p = X.shape[1]

        rank = int(np.linalg.matrix_rank(X))
        rank_pass = (rank == p)

        try:
            kappa = float(np.linalg.cond(X.T @ X))
        except Exception:
            kappa = float('inf')
        kappa_finite = np.isfinite(kappa)
        kappa_pass = kappa_finite and kappa <= 100

        try:
            vif = compute_vif(X)
        except Exception:
            vif = float('inf')
        vif_finite = np.isfinite(vif)
        vif_pass = vif_finite and vif <= 10

        crossing = check_crossing(era_assignments, nf, ne)
        connected = check_connected(era_assignments, nf)

        overall_pass = rank_pass and kappa_pass and vif_pass and crossing and connected

        results.append({
            'F': nf,
            'E': ne,
            'M': mpf,
            'N': n,
            'rank': rank,
            'p': p,
            'kappa': kappa,
            'vif': vif,
            'crossing': crossing,
            'connected': connected,
            'rank_pass': rank_pass,
            'kappa_pass': kappa_pass,
            'vif_pass': vif_pass,
            'overall_pass': overall_pass,
        })

    return results, total


if __name__ == '__main__':
    results, total = run_sweep()

    full_rank = sum(1 for r in results if r['rank_pass'])
    kappa_pass = sum(1 for r in results if r['kappa_pass'])
    all_gate = sum(1 for r in results if r['overall_pass'])

    print(f"Total configurations: {total}")
    print(f"Full rank:           {full_rank}")
    print(f"Kappa <= 100:        {kappa_pass}")
    print(f"All-gate passing:    {all_gate}")

    paper_total = 2184
    paper_rank = 847
    paper_kappa = 312
    paper_all = 298

    match = (total == paper_total and full_rank == paper_rank
             and kappa_pass == paper_kappa and all_gate == paper_all)
    if match:
        print("\nVERIFIED: All counts match paper claims.")
    else:
        print(f"\nMISMATCH with paper claims:")
        print(f"  Total:   {total} vs {paper_total}")
        print(f"  Rank:    {full_rank} vs {paper_rank}")
        print(f"  Kappa:   {kappa_pass} vs {paper_kappa}")
        print(f"  All:     {all_gate} vs {paper_all}")
        print("Halt: counts do not match. Investigate before proceeding.")

    outdir = 'results/design_space'
    import os
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, 'sweep_results.csv')
    with open(outpath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'F', 'E', 'M', 'N', 'rank', 'p', 'kappa', 'vif',
            'crossing', 'connected', 'rank_pass', 'kappa_pass',
            'vif_pass', 'overall_pass'])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved {len(results)} rows to {outpath}")
