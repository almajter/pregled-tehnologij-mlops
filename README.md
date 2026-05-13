# Undergraduate Thesis — Pregled tehnologij MLOps

This repository contains the source files for my undergraduate thesis titled:

**"Pregled tehnologij MLOps"**
*(Overview of MLOps Technologies)*

---

## Project Structure

```text
.
├── thesis/          # LaTeX source for the written thesis
│   ├── main.tex
│   ├── metadata.tex
│   ├── literatura.bib
│   ├── chapters/    # Chapters
│   └── resources/   # Figures and diagrams
```

## GitHub Actions

A GitHub Actions workflow (`.github/workflows/latex.yml`) automatically compiles `main.tex`
and uploads the resulting PDF as an artifact on every push to or PR against `main`.
