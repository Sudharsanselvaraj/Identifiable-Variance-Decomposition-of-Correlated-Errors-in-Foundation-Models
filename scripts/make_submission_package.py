#!/usr/bin/env python3
"""Build a self-contained IEEE Access submission package.

IEEE Access requires the editable source and a PDF whose content matches
exactly. The repository source pulls tables from ../tables and figures from
../figures and finds the class and fonts through TEXINPUTS. This script makes
a flat folder that compiles with no environment variables:

  * generated table rows are inlined into the .tex;
  * only the figures the manuscript includes are copied;
  * only the class/style/font files the build actually opens are copied
    (taken from a -recorder run);

then compiles it in a fresh directory and checks that its text equals the
repository PDF's text. Output: paper/submission_package/ and
paper/submission_package.zip (both gitignored).

Usage (repo root, after `make -C paper`):  python3 scripts/make_submission_package.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SRC = PAPER / "src" / "ieee_access_manuscript.tex"
OUT = PAPER / "submission_package"
ZIP = PAPER / "submission_package.zip"
NAME = "ieee_access_manuscript"


def recorded_support_files() -> list[Path]:
    env = dict(os.environ, TEXINPUTS="../support:", TEXFONTS="../support:",
               TEXFONTMAPS="../support:")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdflatex", "-recorder", "-interaction=nonstopmode",
                        f"-output-directory={tmp}", SRC.name], cwd=SRC.parent,
                       env=env, capture_output=True, check=False)
        fls = Path(tmp, f"{NAME}.fls").read_text().splitlines()
    # Class/style/font files from ../support, plus images the class itself
    # loads through \graphicspath (bullet.png, notaglinelogo.png), which the
    # recorder logs as ../build/../figures/.
    files = set()
    for line in fls:
        if not line.startswith("INPUT "):
            continue
        f = line.split(" ", 1)[1]
        if f.startswith("../support/"):
            files.add((SRC.parent / f).resolve())
        elif "/figures/" in f and f.startswith(".."):
            files.add((SRC.parent.parent / "figures" / Path(f).name).resolve())
    return sorted(files)


def flatten(tex: str) -> tuple[str, list[str]]:
    def inline(m: re.Match) -> str:
        rows = (PAPER / "src" / m.group(1)).read_text().splitlines()
        return "\n".join(r for r in rows if not r.startswith("%"))
    tex = re.sub(r"\\tabinput\{([^}]+)\}", inline, tex)
    tex = tex.replace("\\graphicspath{{../figures/}}", "\\graphicspath{{./}}")
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    return tex, figs


def pdf_text(pdf: Path) -> str:
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    tex, figs = flatten(SRC.read_text())
    (OUT / f"{NAME}.tex").write_text(tex)
    for f in figs:
        shutil.copy(PAPER / "figures" / f, OUT / f)
    support = [f for f in recorded_support_files() if f.name not in figs]
    for f in support:
        shutil.copy(f, OUT / f.name)

    # Compile twice in a fresh copy with a clean environment.
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "build"
        shutil.copytree(OUT, build)
        env = {k: v for k, v in os.environ.items()
               if k not in ("TEXINPUTS", "TEXFONTS", "TEXFONTMAPS")}
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                                "-halt-on-error", f"{NAME}.tex"], cwd=build,
                               env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print("package does not compile standalone:\n" + r.stdout[-2000:])
            return 1
        log = (build / f"{NAME}.log").read_text(errors="replace")
        undefined = re.findall(r"(?:Reference|Citation) [^\n]* undefined", log)
        shutil.copy(build / f"{NAME}.pdf", OUT / f"{NAME}.pdf")
    same = pdf_text(OUT / f"{NAME}.pdf") == pdf_text(PAPER / "build" / f"{NAME}.pdf")

    # Supplementary material: flattened source + its figure, compiled standalone.
    sup, sfigs = flatten((PAPER / "src" / "supplement.tex").read_text())
    (OUT / "supplement.tex").write_text(sup)
    for f in sfigs:
        shutil.copy(PAPER / "figures" / f, OUT / f)
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "build"
        shutil.copytree(OUT, build)
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                "supplement.tex"], cwd=build, env=env, capture_output=True,
                               text=True)
        if r.returncode != 0:
            print("supplement does not compile standalone:\n" + r.stdout[-2000:])
            return 1
        sup_undef = re.findall(r"(?:Reference|Citation) [^\n]* undefined",
                               (build / "supplement.log").read_text(errors="replace"))
        shutil.copy(build / "supplement.pdf", OUT / "supplement.pdf")
    sup_same = pdf_text(OUT / "supplement.pdf") == pdf_text(PAPER / "build" / "supplement.pdf")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.iterdir()):
            z.write(f, f"{NAME}/{f.name}")
    print(f"files: 1 tex, {len(figs)} figures, {len(support)} class/style/font files, 1 pdf; "
          f"supplement: tex + pdf ({len(sfigs)} figure)")
    print(f"supplement: standalone compile OK; undefined: {len(sup_undef)}; "
          f"text identical to repository PDF: {sup_same}")
    print(f"standalone compile: OK; undefined references/citations: {len(undefined)}")
    print(f"PDF text identical to repository PDF: {same}")
    print(f"zip: {ZIP.relative_to(ROOT)} ({ZIP.stat().st_size / 1e6:.1f} MB; limit 40 MB)")
    return 0 if same and sup_same and not undefined and not sup_undef else 1


if __name__ == "__main__":
    sys.exit(main())
