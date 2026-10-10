# Publisher-neutral manuscript

`src/master_manuscript.tex` is a plain single-column version (article class,
11 pt, A4, numbered sections, numeric citations) of the current manuscript,
for submission to journals other than IEEE Access.

It is **generated** from the IEEE Access source
`paper/src/ieee_access_manuscript.tex` by `scripts/make_master_manuscript.py`;
do not edit it by hand. Edit the IEEE source, then run

```bash
make -C master
```

which regenerates the source and builds `build/master_manuscript.pdf`. Text,
numbers, figures (`paper/figures/`), tables (`paper/tables/`), equations and
references are identical to the IEEE version; only the layout differs (no
IEEE front matter, no drop capital, no author biographies, single-column
figure and table sizing). The supplementary material
(`paper/build/supplement.pdf`) is already publisher-neutral and serves both
versions.

`archive/master_manuscript_v1_16model.tex` is the superseded single-column
version of the earlier 16-model manuscript, kept for the record; its findings
are withdrawn (Supplementary Sections S2 and S7).
