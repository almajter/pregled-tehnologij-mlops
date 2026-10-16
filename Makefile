THESIS_DIR := thesis
LATEXMK := latexmk -pdf -file-line-error -interaction=nonstopmode -outdir=build

.PHONY: pdf watch clean fmt

## --- thesis ---------------------------------------------------------------

pdf:
	cd $(THESIS_DIR) && $(LATEXMK) main.tex

watch:
	cd $(THESIS_DIR) && $(LATEXMK) -pvc main.tex

clean:
	cd $(THESIS_DIR) && latexmk -C -outdir=build main.tex

fmt:
	cd $(THESIS_DIR) && latexindent -l -w -s main.tex metadata.tex chapters/*.tex
	cd $(THESIS_DIR) && rm -f *.bak[0-9]* chapters/*.bak[0-9]*
