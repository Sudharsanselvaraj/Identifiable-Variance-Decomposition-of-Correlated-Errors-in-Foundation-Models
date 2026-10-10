# Publisher-neutral single-column manuscript (for journals other than IEEE Access).
#
# The source is GENERATED from paper/src/ieee_access_manuscript.tex by
# scripts/make_master_manuscript.py, so the two versions never drift apart.
# Figures and tables are shared with paper/ (paper/figures, paper/tables).
#
# Usage:
#   make          regenerate the source from the IEEE manuscript and build the PDF
#   make clean    remove build artifacts
#
# The superseded 16-model manuscript is kept in archive/.

TEX      := pdflatex
SRC      := src/master_manuscript.tex
IEEE     := ../paper/src/ieee_access_manuscript.tex
GEN      := ../scripts/make_master_manuscript.py
OUTDIR   := build
PDF      := build/master_manuscript.pdf
DEPS     := $(SRC) $(wildcard ../paper/tables/*.tex) $(wildcard ../paper/figures/*.pdf)

.PHONY: all pdf clean

all: pdf

pdf: $(PDF)

$(SRC): $(IEEE) $(GEN)
	cd .. && python3 scripts/make_master_manuscript.py

$(PDF): $(DEPS)
	mkdir -p $(OUTDIR)
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))
	cd $(dir $(SRC)) && $(TEX) -interaction=nonstopmode -halt-on-error -output-directory=../$(OUTDIR) $(notdir $(SRC))

clean:
	rm -f build/*.aux build/*.log build/*.out build/*.pdf
