THESIS_DIR := thesis
PROJECT_DIR := project
LATEXMK := latexmk -pdf -file-line-error -interaction=nonstopmode -outdir=build

.PHONY: help pdf watch clean fmt sync lint test up down

help:
	@echo "Thesis:"
	@echo "  make pdf     build thesis/build/main.pdf"
	@echo "  make watch   continuous rebuild"
	@echo "  make fmt     latexindent over thesis/**/*.tex"
	@echo "  make clean   remove build artifacts"
	@echo "Project:"
	@echo "  make sync    uv sync"
	@echo "  make lint    ruff check + format --check"
	@echo "  make test    pytest"
	@echo "  make up      docker compose up -d"
	@echo "  make down    docker compose down"

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

# pytest exits 5 when no tests are collected; tolerate that while the suite is empty.
test:
	cd $(PROJECT_DIR) && uv run pytest; status=$$?; [ $$status -eq 0 ] || [ $$status -eq 5 ]

up:
	cd $(PROJECT_DIR) && docker compose up -d

down:
	cd $(PROJECT_DIR) && docker compose down
