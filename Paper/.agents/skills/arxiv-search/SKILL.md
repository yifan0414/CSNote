---
name: arxiv-search
description: Search arXiv preprints and return formatted paper results (title and abstract summary). Use when a user asks to find recent or relevant papers on arXiv, especially in computer science, machine learning, math, statistics, physics, or quantitative biology.
---

# arXiv Search

Use `scripts/arxiv_search.py` to query arXiv and return a concise list of papers.

## Run
Use the workspace virtual environment when available:

```bash
/Users/su/hello/.venv/bin/python /Users/su/hello/.agents/skills/arxiv-search/scripts/arxiv_search.py "your search query" --max-papers 10
```

Or use system Python:

```bash
python3 /Users/su/hello/.agents/skills/arxiv-search/scripts/arxiv_search.py "your search query" --max-papers 10
```

## Arguments
- `query` (required): Search string, e.g. `"video question answering"`
- `--max-papers` (optional): Maximum number of papers to return (default `10`)

## Output
For each result, print:
- `Title`
- `Summary`

Each paper is separated by a blank line.

## Dependency
Install `arxiv` if missing:

```bash
/Users/su/hello/.venv/bin/python -m pip install arxiv
```

If unavailable, the script prints an install hint and exits cleanly.
