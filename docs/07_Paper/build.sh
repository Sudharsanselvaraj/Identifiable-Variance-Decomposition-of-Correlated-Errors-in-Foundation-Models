#!/bin/sh
# Build the manuscript. The IEEE Access class ships its own Times/Formata
# Type1 fonts in ieeeaccess_support/; .tfm files resolve via TFMFONTS and
# .pfb via T1FONTS, NOT via TEXINPUTS. Setting only TEXINPUTS compiles but
# drops every roman glyph to nullfont, silently producing a short PDF with
# no body text.
set -e
cd "$(dirname "$0")"
export TEXINPUTS="./ieeeaccess_support//:"
export TFMFONTS="./ieeeaccess_support//:"
export T1FONTS="./ieeeaccess_support//:"
export TEXFONTMAPS="./ieeeaccess_support//:"
for i in 1 2 3; do
  pdflatex -interaction=nonstopmode -file-line-error manuscript.tex >/dev/null
done
echo "pages:    $(python3 -c "import pypdf;print(len(pypdf.PdfReader('manuscript.pdf').pages))")"
echo "nullfont: $(grep -c nullfont manuscript.log || true)"
echo "overfull: $(grep -c Overfull manuscript.log || true)"
