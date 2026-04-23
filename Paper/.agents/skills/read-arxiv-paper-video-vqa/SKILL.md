---
name: read-arxiv-paper-vqa
description: Read an arXiv paper from an arXiv URL by downloading the /src archive, unpacking and traversing the LaTeX project recursively, extracting key experimental tables, and writing/overwriting a single Obsidian-compatible markdown note with YAML frontmatter. Use when asked to digest an arXiv paper for video understanding.
---

# Read arXiv Paper (TeX-first) → Obsidian Note

## Inputs
- arXiv URL (abs/pdf/id forms). Example (any equivalent form ok):
  - https://arxiv.org/abs/XXXX.XXXXX
  - https://arxiv.org/pdf/XXXX.XXXXX.pdf
- Optional:
  - output_note_path (if provided, MUST update that note; do not create another)
  - output_dir default: ./knowledge/arxiv/video_understanding/papers
  - tag/slug: optional; default arxiv_{id}

## 1) Normalize URL → arxiv_id (+ version)
- Extract arxiv_id, allow vN suffix if present.
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

## 4) Find LaTeX entrypoint (robust)
Heuristics:
- Prefer file defining \title / \author / \begin{document}
- Common names: main.tex, paper.tex, manuscript.tex
- If multiple candidates, choose the one with \begin{document} and the most \input/\include.

## 5) Recursively read TeX project
- Parse entrypoint, recursively inline:
  - \input{...}, \include{...}
  - referenced .tex in same project
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
  - columns separated by & and rows ended by \\
  - strip \hline, \toprule, \midrule, \bottomrule
- If conversion fails, include a fenced block with the raw LaTeX table and a short note.

### 6.2 Normalize experiment info (at least 3 tables when present)
Create these tables if information exists:
1) Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
2) Main Results (top-1/top-5/mAP/R@K etc.)
| Dataset | Metric | Baseline | Ours | Δ |
3) Training / Compute (if reported)
| Item | Value |
(e.g., backbone, frames, resolution, batch size, optimizer, lr, epochs, GPUs, pretrain data)

## 7) Write Obsidian note with YAML frontmatter
Obsidian frontmatter MUST be at the very top delimited by `---`.

If output_note_path is provided:
- Update that file in-place (overwrite placeholders, keep user annotations if possible).
Else:
- Write:
  {output_dir}/arxiv_{arxiv_id}.md

Frontmatter fields (suggested):
- title: "..."
- authors: ["...", "..."]
- arxiv_id: "..."
- arxiv_url: "..."
- pdf_url: "..."
- published: YYYY-MM-DD
- updated: YYYY-MM-DD
- categories: ["cs.CV", ...]
- tags: ["paper/arxiv", "video-understanding", "status/read"]
- status: "read"
- code: (url if known, else empty)
- datasets: ["Kinetics-400", ...] (best-effort)

Body sections (strict order):
1) TL;DR (3-6 bullets)
2) Key Contributions
3) Method (with a compact pseudocode or pipeline bullets)
4) Experiments
   - Datasets table
   - Main results table(s)
   - Ablations/Analysis tables (if present)
5) Limitations & Caveats
6) Concrete Implementation Ideas (2-5 actionable ideas)
7) Open Questions / Follow-ups
8) Citation (bibtex if available or arXiv cite line)

## 8) Safety and quality checks
- Do not hallucinate numbers: only include metrics that appear in the source.
- When unsure, mark as "not reported" and keep the evidence snippet.
- Keep tables faithful; avoid “cleaning” that changes meaning.
