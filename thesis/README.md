## About This Repository

This project contains my undergraduate thesis based on the official FRI UL template, cloned from the repository:

> [https://github.com/UL-FRI/thesis-BUN-BVS](https://github.com/UL-FRI/thesis-BUN-BVS)

The template was adapted to include my work titled:

> **Pregled tehnologij MLOps**
> *(Overview of MLOps Technologies)*

---

## How to Compile the Thesis

### Prerequisites

Install a LaTeX distribution:

#### **macOS**
```bash
brew install --cask mactex
```

## Compile the thesis
This will automatically compile the thesis and generate main.pdf.
```bash
latexmk \
    -pdf \
    -file-line-error \
    -interaction=nonstopmode \
    -outdir=build \
    main.tex
```

## Clean Up Auxiliary Files
To clean up temporary files:
```bash
latexmk -c
```

## Formatter
```bash
latexindent -l -w yourfile.tex
```

## VS Code
- Install LaTeX Workshop extension
