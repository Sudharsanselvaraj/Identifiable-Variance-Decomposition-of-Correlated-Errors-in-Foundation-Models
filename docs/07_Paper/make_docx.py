#!/usr/bin/env python3
"""Build manuscript.docx from manuscript.tex.

IEEE Access accepts either LaTeX or Word. Pandoc cannot read the ieeeaccess
class -- \\Figure, \\PARstart, \\history, \\authorrefmark, the biography
environments and the algorithm float defined in the preamble are all unknown to
it, and a bare `pandoc manuscript.tex` silently drops or mangles them.

This script rewrites the manuscript into a pandoc-readable subset first, then
converts. Cross-references and citations are resolved to their real numbers by
reading manuscript.aux, so the Word file says "Table 3" and "[12]" rather than
carrying dead \\ref markers.

Run ./build.sh first (make_docx reads the .aux it produces), then:
    python3 make_docx.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE / "manuscript.tex"
AUX = HERE / "manuscript.aux"
OUT = HERE / "manuscript.docx"
INTERMEDIATE = HERE / ".manuscript_pandoc.tex"


# ---------------------------------------------------------------- aux parsing
def load_labels() -> dict[str, str]:
    r"""label -> printed number, from \newlabel{key}{{number}{page}...}.

    The number field is not always a plain string: subsection references are
    stored as `\mbox {V-E}`, so it has to be brace-matched and unwrapped rather
    than read with a naive [^}]* regex, which truncates at the first brace and
    leaves the remainder as stray literal text in the output.
    """
    if not AUX.exists():
        sys.exit("manuscript.aux not found -- run ./build.sh first")
    aux = AUX.read_text()
    out = {}
    for m in re.finditer(r"\\newlabel\{", aux):
        try:
            key, j = read_group(aux, m.end() - 1)
            outer, _ = read_group(aux, j)
            number, _ = read_group(outer, 0)
        except (ValueError, AssertionError, IndexError):
            continue
        number = re.sub(r"\\mbox\s*", "", number).replace("{", "").replace("}", "")
        out[key] = number.strip()
    return out


def load_cites() -> dict[str, str]:
    """cite key -> reference number, from \\bibcite{key}{n}."""
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"\\bibcite\{([^}]*)\}\{([^}]*)\}", AUX.read_text())
    }


# ------------------------------------------------------------ brace matching
def read_group(s: str, i: int) -> tuple[str, int]:
    """Read a balanced {...} at or after s[i]. Returns (inner, next_i).

    Leading whitespace is skipped: \\Figure's file and caption groups are
    separated by a newline in the manuscript.
    """
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    assert s[i] == "{", s[i : i + 30]
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1 : j], j + 1
        j += 1
    raise ValueError("unbalanced braces")


# ------------------------------------------------------------- transformations
def convert_figures(t: str) -> str:
    r"""\Figure[pos](keys)[gfx]{file}{caption} -> a standard figure env."""
    out, i = [], 0
    pat = re.compile(r"\\Figure\s*(\[[^\]]*\])?\s*(\([^)]*\))?\s*(\[[^\]]*\])?\s*")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i : m.start()])
        path, j = read_group(t, m.end())
        caption, j = read_group(t, j)
        out.append(
            "\n\\begin{figure}\n\\centering\n"
            f"\\includegraphics[width=0.95\\linewidth]{{{path}}}\n"
            f"\\caption{{{caption}}}\n\\end{{figure}}\n"
        )
        i = j
    return "".join(out)


def convert_algorithms(t: str) -> str:
    r"""The float.sty algorithm float -> a bold run-in heading plus a list."""
    def repl(m: re.Match) -> str:
        body = m.group(1)
        cap = re.search(r"\\caption\{", body)
        title = ""
        if cap:
            title, _ = read_group(body, cap.end() - 1)
            body = body[: cap.start()] + body[body.index("\\begin{algsteps}") :]
        num = repl.counter = getattr(repl, "counter", 0) + 1
        body = body.replace("\\begin{algsteps}", "\\begin{enumerate}")
        body = body.replace("\\end{algsteps}", "\\end{enumerate}")
        return (
            f"\n\n\\noindent\\textbf{{Algorithm {num}: {title}}}\n\n{body}\n\n"
        )

    return re.sub(
        r"\\begin\{algorithm\}(?:\[[^\]]*\])?(.*?)\\end\{algorithm\}",
        repl, t, flags=re.S,
    )


def convert_biographies(t: str) -> str:
    def repl(m: re.Match) -> str:
        return f"\n\n\\subsection*{{{m.group(1)}}}\n{m.group(2)}\n"

    return re.sub(
        r"\\begin\{IEEEbiographynophoto\}\{([^}]*)\}(.*?)\\end\{IEEEbiographynophoto\}",
        repl, t, flags=re.S,
    )


def name_appendices(t: str) -> str:
    """After \\appendices, letter the sections the way LaTeX printed them."""
    if "\\appendices" not in t:
        return t
    head, tail = t.split("\\appendices", 1)
    letters = iter("ABCDEFGHIJK")

    def repl(m: re.Match) -> str:
        return f"\\section*{{Appendix {next(letters)}: {m.group(1)}}}"

    tail = re.sub(r"\\section\{([^}]*)\}", repl, tail)
    return head + "\n" + tail


def resolve_refs(t: str, labels: dict[str, str], cites: dict[str, str]) -> str:
    t = re.sub(r"\\eqref\{([^}]*)\}",
               lambda m: f"({labels.get(m.group(1), '?')})", t)
    t = re.sub(r"\\ref\{([^}]*)\}",
               lambda m: labels.get(m.group(1), "?"), t)

    def cite(m: re.Match) -> str:
        keys = [k.strip() for k in m.group(1).split(",")]
        return "[" + ", ".join(cites.get(k, "?") for k in keys) + "]"

    return re.sub(r"\\cite\{([^}]*)\}", cite, t)


STRIP_WITH_ARG = [
    "history", "doi", "tfootnote", "corresp", "markboth", "titlepgskip",
    "authorrefmark", "label", "graphicspath",
]
# Commands taking two brace groups; stripping only the first leaves the second
# behind as stray literal text.
STRIP_WITH_TWO_ARGS = ["setlength", "renewcommand"]
STRIP_BARE = [
    r"\\maketitle", r"\\EOD", r"\\appendices", r"\\hline", r"\\centering",
    r"\\noindent(?=\\)", r"\\PARstart",
    # Font-size switches inside tabulars: pandoc treats an unknown control
    # sequence in a table as an error and drops the whole float silently.
    r"\\footnotesize\b", r"\\scriptsize\b", r"\\small\b", r"\\tiny\b",
    r"\\normalsize\b",
]


def strip_ieee(t: str) -> str:
    # Strip comments first. One of the preamble comments contains the literal
    # string "\begin{document}", so locating the preamble boundary before
    # removing comments cuts in the wrong place and drags preamble code into
    # the body.
    t = re.sub(r"(?<!\\)%.*", "", t)

    # Drop the preamble entirely; rebuild only what pandoc needs.
    m = re.search(r"^[ \t]*\\begin\{document\}", t, re.M)
    if not m:
        sys.exit("could not locate \\begin{document}")
    t = t[m.end():]
    t = re.sub(r"^[ \t]*\\end\{document\}.*", "", t, flags=re.M | re.S)

    for cmd, ngroups in (
        [(c, 1) for c in STRIP_WITH_ARG] + [(c, 2) for c in STRIP_WITH_TWO_ARGS]
    ):
        out, i = [], 0
        while True:
            m = re.search(r"\\" + cmd + r"\s*(\[[^\]]*\])?\s*\{", t[i:])
            if not m:
                out.append(t[i:])
                break
            out.append(t[i : i + m.start()])
            j = i + m.end() - 1
            for _ in range(ngroups):
                _, j = read_group(t, j)
            i = j
        t = "".join(out)

    for pat in STRIP_BARE:
        t = re.sub(pat, "", t)

    # \Figure's optional (key=value) group is not a LaTeX optional arg.
    t = re.sub(r"^\s*\\vspace\*?\{[^}]*\}", "", t, flags=re.M)
    t = t.replace("\\begin{table*}", "\\begin{table}")
    t = t.replace("\\end{table*}", "\\end{table}")
    t = re.sub(r"\\begin\{table\}\s*\[[^\]]*\]", "\\\\begin{table}", t)
    t = re.sub(r"\\begin\{figure\}\s*\[[^\]]*\]", "\\\\begin{figure}", t)
    # pandoc's latex reader rejects @{} in a column spec (notably inside
    # \multicolumn) and drops the enclosing table without reporting anything.
    t = t.replace("@{}", "")
    t = t.replace("\\algkw", "\\textbf")
    t = re.sub(r"\\algind\{(\d+)\}", lambda m: "~" * (4 * int(m.group(1))), t)
    t = re.sub(r"\\algcomment\{([^}]*)\}", r"\\textit{-- \1}", t)
    t = re.sub(r"\\uppercase\{([^}]*)\}", r"\1", t)
    return t


def extract_front(t: str) -> tuple[str, str]:
    """Pull title/author/abstract/keywords out into a rebuilt front matter."""
    def grab(cmd: str) -> str:
        m = re.search(r"\\" + cmd + r"\s*(\[[^\]]*\])?\s*\{", t)
        if not m:
            return ""
        inner, _ = read_group(t, m.end() - 1)
        return inner

    title = grab("title")
    author = grab("author")
    address = grab("address")
    abstract = ""
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        abstract = m.group(1).strip()
    keywords = ""
    m = re.search(r"\\begin\{keywords\}(.*?)\\end\{keywords\}", t, re.S)
    if m:
        keywords = m.group(1).strip()

    body = t
    for blk in ("abstract", "keywords"):
        body = re.sub(r"\\begin\{" + blk + r"\}.*?\\end\{" + blk + r"\}",
                      "", body, flags=re.S)
    for cmd in ("title", "author", "address"):
        mm = re.search(r"\\" + cmd + r"\s*(\[[^\]]*\])?\s*\{", body)
        if mm:
            _, j = read_group(body, mm.end() - 1)
            body = body[: mm.start()] + body[j:]

    front = (
        f"\\section*{{{title}}}\n\n"
        f"\\noindent {author}\n\n"
        f"\\noindent \\emph{{{address}}}\n\n"
        f"\\subsection*{{Abstract}}\n{abstract}\n\n"
        f"\\noindent\\textbf{{Index Terms---}}{keywords}\n\n"
    )
    return front, body


def main() -> int:
    labels, cites = load_labels(), load_cites()
    t = TEX.read_text()

    t = convert_figures(t)
    t = convert_algorithms(t)
    t = convert_biographies(t)
    t = name_appendices(t)
    t = strip_ieee(t)
    t = resolve_refs(t, labels, cites)
    front, body = extract_front(t)

    doc = (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage{amsmath,amssymb,graphicx}\n"
        "\\begin{document}\n" + front + body + "\n\\end{document}\n"
    )
    INTERMEDIATE.write_text(doc)

    cmd = [
        "pandoc", str(INTERMEDIATE), "-f", "latex", "-t", "docx",
        "--resource-path", str(HERE), "-o", str(OUT),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return r.returncode
    if r.stderr.strip():
        sys.stderr.write(r.stderr)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
