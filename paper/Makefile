# IEEE Access manuscript build.
#
# Layout:
#   src/       ieee_access_manuscript.tex   (manuscript source)
#   figures/   figure PDFs / PNGs           (referenced via \graphicspath)
#   support/   class (.cls), style (.sty), .bst, fonts (.pfb/.tfm/.map/.fd), header logos
#   tables/    (optional data tables)
#   build/     generated .aux/.log/.pdf
#
# Usage:
#   make          build the PDF (two passes)
#   make pdf      same
#   make clean    remove build artifacts
#
# TeX needs the class, style, font-map and font files to be resolvable from
# ../support, which is why TEXINPUTS / TEXFONTS / TEXFONTMAPS are set here.

TEX      := pdflatex
SRC      := src/ieee_access_manuscript.tex
OUTDIR   := build
PDF      := build/ieee_access_manuscript.pdf

export TEXINPUTS   := ../support:
export TEXFONTS    := ../support:
export TEXFONTMAPS := ../support:

.PHONY: all pdf clean tables


all: pdf

pdf: $(PDF)

# Rebuild when the source, any generated table or any figure changes.
DEPS     := $(SRC) $(wildcard tables/*.tex) $(wildcard figures/*.pdf) $(wildcard figures/*.png)

$(PDF): $(DEPS)
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))

clean:
	rm -f build/*.aux build/*.log build/*.out build/*.pdf

# Regenerate table rows from the committed analysis outputs.
tables:
	cd .. && python3 scripts/make_exp04_tables.py
