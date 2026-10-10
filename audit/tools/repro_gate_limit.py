#!/usr/bin/env python3
"""Audit reproducer (issue ISS-12): the analysis gate does not bind an answer file to its model.

Works on a temporary copy of two answer files; the repository is not touched.
analysis.load_population / choice_matrix check item order, gold, hashes, length and option
range, and that the manifest marks the model 'validated'. They do not compare the file's
accuracy with the manifest's recorded accuracy, and the manifest stores no content hash.
Swapping the answer files of two validated models therefore passes every check.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lineage_era.ollb import analysis as A  # noqa: E402

pop, _ = A.load_population("primary", False)
a, b = pop.model.iloc[10], pop.model.iloc[400]
man = pd.read_csv(A.MANIFEST).set_index("model")
tmp = Path(tempfile.mkdtemp(prefix="audit_gate_"))
for m in pop.model:
    shutil.copy(A.answer_file(m), tmp / A.answer_file(m).name)
fa, fb = tmp / A.answer_file(a).name, tmp / A.answer_file(b).name
fa_t, fb_t = tmp / "swap_a.npz", tmp / "swap_b.npz"
fa.rename(fa_t); fb.rename(fb_t); fa_t.rename(fb); fb_t.rename(fa)      # swap contents
A.ANSWERS = tmp                                                           # gate now reads the swapped copy
pop2, info = A.load_population("primary", False)
pred, gold, checks = A.choice_matrix(pop2.model)                          # raises if any check fails
acc = (pred == gold[None]).mean(1)
ia, ib = list(pop2.model).index(a), list(pop2.model).index(b)
print("gate result: no exception; alignment checks:", {k: len(v) for k, v in checks.items()})
print(f"{a}: manifest accuracy {man.loc[a, 'accuracy']:.4f}, loaded file accuracy {acc[ia]:.4f}")
print(f"{b}: manifest accuracy {man.loc[b, 'accuracy']:.4f}, loaded file accuracy {acc[ib]:.4f}")
print("=> swapped files pass the gate; a manifest-accuracy comparison would catch it:",
      bool(abs(man.loc[a, "accuracy"] - acc[ia]) > 1e-9))
shutil.rmtree(tmp)
