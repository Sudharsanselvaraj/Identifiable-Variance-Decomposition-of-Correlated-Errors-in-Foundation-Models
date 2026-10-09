# Publisher-neutral single-column master manuscript build.
#
# Layout:
#   src/            master_manuscript.tex   (manuscript source)
#   ../paper/figures/   figure PDFs / PNGs (shared with IEEE version)
#   build/          generated .aux/.log/.pdf
#
# Usage:
#   make          build the PDF (two passes)
#   make pdf      same
#   make clean    remove build artifacts

TEX      := pdflatex
SRC      := src/master_manuscript.tex
OUTDIR   := build
PDF      := build/master_manuscript.pdf

.PHONY: all pdf clean

all: pdf

pdf: $(PDF)
	@echo "WARNING: master/ is the SUPERSEDED 16-model manuscript; the current study is in paper/ (see master/README.md)."

$(PDF): $(SRC)
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))

clean:
	rm -f build/*.aux build/*.log build/*.out build/*.pdf