THESIS_DIR := thesis
PROJECT_DIR := project
LATEXMK := latexmk -pdf -file-line-error -interaction=nonstopmode -outdir=build

.PHONY: pdf watch clean fmt sync lint up down

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

## --- project --------------------------------------------------------------

sync:
	cd $(PROJECT_DIR) && uv sync

lint:
	cd $(PROJECT_DIR) && uv run ruff check . && uv run ruff format --check .

up:
	cd $(PROJECT_DIR) && docker compose up -d

down:
	cd $(PROJECT_DIR) && docker compose down
