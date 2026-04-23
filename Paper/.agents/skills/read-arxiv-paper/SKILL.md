---
name: read-arxiv-paper 
description: Read an arXiv paper from an arXiv URL by downloading the /src archive, unpacking and traversing the LaTeX project recursively, extracting key experimental tables and the main pipeline figure, and writing/overwriting a single Obsidian-compatible markdown note with YAML frontmatter. Use when asked to digest an arXiv paper.
---

# Read arXiv Paper (TeX-first) → Obsidian Note

## Inputs

- arXiv URL (abs/pdf/id forms). Example (any equivalent form ok):
  - https://arxiv.org/abs/XXXX.XXXXX
  - https://arxiv.org/pdf/XXXX.XXXXX.pdf
- Optional:
  - output_note_path (if provided, MUST update that note; do not create another)
  - output_dir default: ./papers
  - tag/slug: optional; default arxiv_{id}

### Paper Name / Folder Naming

- use_title_as_filename (default: true)
- filename_max_len (default: 80)
- filename_case (default: "kebab") # kebab|snake|preserve
- reserved_char_replacement (default: "-")
- folder_layout (default: "paper_dir") # always: md + assets under same folder

**Sanitize rules (paper_name):**

1. Prefer title from TeX (`\title{...}`); fallback to `arxiv_{id}` if title not found or use_title_as_filename=false.
2. Strip simple LaTeX commands (`\textbf{}`, `\emph{}`, etc.) and math (`$...$`) best-effort.
3. Replace forbidden characters: `\/:*?"<>|` and control chars with `reserved_char_replacement`.
4. Collapse whitespace/separators to single `-` (kebab) or `_` (snake).
5. Trim leading/trailing `-`, `_`, `.`, and spaces.
6. Truncate to `filename_max_len` characters.
7. If result becomes empty -> `arxiv_{id}`.

### Derived Paths (single source of truth)

If `output_note_path` is NOT provided:

- paper_dir = {output_dir}/{paper_name}
- note_path = {paper_dir}/{paper_name}.md
- assets_dir = {paper_dir}/assets

If `output_note_path` IS provided:

- note_path = output_note_path (MUST write/update exactly this file)
- paper_dir = dirname(output_note_path)
- assets_dir = {paper_dir}/assets

> All generated assets go under `assets_dir` unless explicitly overridden.

### Optional — Pipeline Figure Extraction

- extract_pipeline_figure (default: true)
- max_pipeline_figures (default: 1)
- figure_keywords (default:
  ["pipeline","framework","overview","architecture","method","model","proposed",
  "system","approach","workflow","diagram",
  "框架","总体","架构","方法","流程","系统","概览"])
- figure_output_dir (default: assets_dir) # ✅ unified default
- figure_fallback_pdf (default: true)
- figure_raster_dpi (default: 250)
- figure_min_width_px (default: 800)


## 1) Normalize URL → arxiv_id (+ version)

- Extract arxiv_id, allow vN suffix if present.
- Support both new-style (XXXX.XXXXX) and old-style (e.g., cs/0601001) IDs.
- Build canonical:
  - abs_url: https://arxiv.org/abs/{arxiv_id}
  - pdf_url: https://arxiv.org/pdf/{arxiv_id}.pdf
  - src_url: https://arxiv.org/src/{arxiv_id}

## 2) Download source archive with cache

- Cache file:
  - ~/.cache/arxiv/src/{arxiv_id}.tar.gz
- If exists, reuse.
- Otherwise download from src_url.
- If /src is unavailable, fallback to PDF-only reading (last resort).

## 3) Unpack source

- Unpack to:
  - ~/.cache/arxiv/src/{arxiv_id}/
- Keep directory for incremental reads.
- Use safe extraction: prevent path traversal (e.g., disallow `../` escaping target dir).

## 4) Find LaTeX entrypoint (robust)

Heuristics:

- Prefer file defining \title / \author / \begin{document}
- Common names: main.tex, paper.tex, manuscript.tex
- If multiple candidates, choose the one with \begin{document} and the most \input/\include.

## 4.1 Extract Title → paper_name and create output folders

- Extract raw_title from TeX entrypoint `\title{...}` (best-effort).
- If `use_title_as_filename=true` and raw_title exists:
  - paper_name = sanitize_title(raw_title)
  - else paper_name = `arxiv_{arxiv_id}`
- Derive paths using **Derived Paths (single source of truth)** above.
- Ensure directories exist:
  - mkdir -p {paper_dir}
  - mkdir -p {assets_dir}
- Set:
  - figure_output_dir defaults to assets_dir (unless explicitly provided)

## 5) Recursively read TeX project

- Parse entrypoint, recursively inline:
  - \input{...}, \include{...}
- Ignore figures/binaries unless needed.
- Capture:
  - problem statement, contributions
  - method & training details (data, objectives, architecture, compute)
  - evaluation setup (datasets, metrics, baselines)
  - key results, limitations, open questions

## 6) Extract "relevant data" into Markdown tables

### 6.1 Identify candidate tables in TeX

- Locate environments:
  - \begin{table}...\end{table}
  - \begin{tabular}...\end{tabular}
- Extract caption if available (\caption{...})
- Convert common patterns to Markdown table:
  - columns separated by & and rows ended by \
  - strip \hline, \toprule, \midrule, \bottomrule
- If conversion fails, include a fenced block with the raw LaTeX table and a short note about why it failed (e.g., multicolumn/multirow).

### 6.2 Normalize experiment info (at least 3 tables when present)

Create these tables if information exists:

1. Datasets / Benchmarks
   | Dataset | Task | Split | Metric(s) | Notes |
2. Main Results
   | Dataset | Metric | Baseline | Ours | Δ |
3. Training / Compute (if reported)
   | Item | Value |

## 7) Extract pipeline/framework figure (TeX-first, PDF fallback)

### 7.1 TeX-first extraction (preferred)

Goal: locate the paper’s main “pipeline/framework/overview” figure from TeX source assets.

1. Collect candidate figures

- Scan recursively-read TeX content for `\begin{figure}` / `\begin{figure*}` blocks.
- For each block, extract:
  - caption_text from `\caption{...}` (best-effort)
  - label_text from `\label{...}` (optional)
  - include_paths from `\includegraphics[...] {path}` (may omit extension)

1. Resolve image file paths

- For each include path, attempt to resolve to an existing file in the unpacked source tree by trying extensions:
  - `.pdf`, `.png`, `.jpg`, `.jpeg`, `.eps`, `.svg`
- If the include path is relative, resolve against:
  - the directory of the TeX file that contains it
  - project root as fallback

1. Score candidates (pick pipeline-like figure)

- Score:
  - +5 for each keyword match in caption_text (case-insensitive)
  - +3 for each keyword match in label_text
  - +2 for each keyword match in filename
  - +2 if caption contains “overview/framework/architecture” (or 中文同义词)
  - -5 if caption suggests unrelated (e.g., “dataset”, “qualitative results”, “attention map”) unless also matches pipeline keywords
- Prefer larger images when possible:
  - If you can read image width, add + (width_px / 1000) capped at +3
- Discard candidates too small (width < figure_min_width_px) unless nothing else exists.

1. Export to Obsidian assets

- If `extract_pipeline_figure=false`, skip this entire section.
- Ensure `figure_output_dir` exists.
- Choose up to `max_pipeline_figures` top-scoring candidates.
- Copy into:
  - `{figure_output_dir}/pipeline_{arxiv_id}.{ext}`
- If target exists, do NOT overwrite; add suffix `_2`, `_3`, etc.

1. Optional: Convert vector to PNG for Obsidian

- If chosen asset is `.pdf/.eps/.svg` and conversion tools are available, export:
  - `{figure_output_dir}/pipeline_{arxiv_id}.png` using `figure_raster_dpi`
- If conversion not possible, keep original and embed as-is.

1. Record figure metadata

- pipeline_figure_path (relative to note, e.g., `assets/pipeline_XXXX.XXXXX.png`)
- pipeline_figure_caption (caption_text if any)
- pipeline_figure_source (e.g., `TeX includegraphics from <tex_file>`)

### 7.2 PDF fallback extraction

Trigger fallback when:

- no suitable TeX figure found OR included image files missing,
  AND `figure_fallback_pdf=true`.

1. Ensure PDF is available

- Download `{pdf_url}` to cache if needed.

1. Try image extraction from PDF (best-effort)

- Extract embedded images; filter out tiny ones using `figure_min_width_px`.
- Pick the largest / most pipeline-like (keyword-based if possible; otherwise size-based).
- Save as:
  - `{figure_output_dir}/pipeline_{arxiv_id}.png` (or jpg if extracted)

1. If extraction fails, render likely page(s) to PNG

- Search PDF text for “Figure” + any `figure_keywords`.
- Render matching page(s) (whole page acceptable):
  - `{figure_output_dir}/pipeline_{arxiv_id}_p{page}.png`
- Note explicitly this is a page render if not cropped.

1. Record metadata

- pipeline_figure_source = `PDF fallback (extracted image or rendered page)`
- pipeline_figure_caption = best-effort

## 8) Write Obsidian note with YAML frontmatter (single destination)

**Write/update EXACTLY `note_path`** (derived above).
Default behavior: **full rewrite** (strong overwrite) for stability.

Optional preservation rule (only if you implement it):

- If the existing note contains:
  - `<!-- USER_NOTES_START -->` ... `<!-- USER_NOTES_END -->`
    preserve that block verbatim when rewriting; otherwise overwrite everything.

Frontmatter fields (suggested):

- title: "..."
- authors: ["...", "..."]
- arxiv_id: "..."
- arxiv_url: "..."
- pdf_url: "..."
- published: YYYY-MM-DD
- updated: YYYY-MM-DD
- categories: ["cs.CV", ...]
- tags: ["paper/arxiv", "status/read", ...]
- status: "read"
- code: ""
- datasets: ["...", ...]

Frontmatter fields for pipeline figure (best-effort):

- pipeline_figure: "assets/pipeline_{arxiv_id}.png"
- pipeline_caption: "..."
- pipeline_source: "TeX includegraphics ... / PDF fallback ..."

Body sections (strict order):

1. TL;DR (3-6 bullets)
2. Key Contributions
3. Method (with compact pseudocode or pipeline bullets)
4. Pipeline Figure
   - If pipeline_figure exists:
     - `![[{pipeline_figure}]]`
     - Caption: {pipeline_caption}
     - Source: {pipeline_source}
5. Experiments
   - Datasets table
   - Main results table(s)
   - Ablations/Analysis tables (if present)
6. Limitations & Caveats
7. Concrete Implementation Ideas (2-5 actionable ideas)
8. Open Questions / Follow-ups
9. Citation (bibtex if available or arXiv cite line)

## 9) Safety and quality checks

- Do not hallucinate numbers: only include metrics that appear in the source.
- When unsure, mark as "not reported" and keep the evidence snippet.
- Keep tables faithful; avoid “cleaning” that changes meaning.
- For pipeline figure:
  - Do not claim it is the pipeline figure unless caption/keywords strongly indicate it.
  - If only a whole-page render is available, explicitly note it is a page render.