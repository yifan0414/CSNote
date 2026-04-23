---
title: "∞-Video: A Training-Free Approach to Long Video Understanding via Continuous-Time Memory Consolidation"
authors:
  - "Saul Santos"
  - "António Farinhas"
  - "Daniel C. McNamee"
  - "André F. T. Martins"
arxiv_id: "2501.19098v1"
arxiv_url: "https://arxiv.org/abs/2501.19098v1"
pdf_url: "https://arxiv.org/pdf/2501.19098v1.pdf"
published: 2025-01-31
updated: 2025-05-19
categories:
  - "cs.CV"
  - "cs.LG"
tags:
  - "paper/arxiv"
  - "paper/video-understanding"
  - "paper/long-context"
  - "status/read"
status: "read"
code: "https://github.com/deep-spin/Infinite-Video"
datasets:
  - "NeXT-QA"
  - "EgoSchema"
  - "VideoMME"
  - "MovieChat-1K"
pipeline_figure: "assets/pipeline_2501.19098v1.png"
pipeline_caption: "Overview of ∞-Video with Video-LLaMA/VideoChat2 and continuous-time LTM over chunked video."
pipeline_source: "TeX includegraphics from main.tex (diagram.pdf), Figure labeled fig:overview."
---

## TL;DR
- Introduces **∞-Video**, a training-free way to extend short-context video Q-former models (Video-LLaMA, VideoChat2) to arbitrarily long videos.
- Adds a **continuous-time long-term memory (LTM)** to cross-attention and combines it with short-term memory (STM) via `Z = α Z_STM + (1-α) Z_LTM`.
- Replaces prior Gaussian continuous attention with a **Gibbs density** over continuous query-key similarity.
- Uses **memory consolidation** (contract + sample + regress) across chunks; “sticky memories” allocate more capacity to high-attention regions.
- Reports consistent gains for the Video-LLaMA family on long-video QA benchmarks, especially with sticky memories.
- Runs in a single pass over chunks and does not require retraining.

## Key Contributions
- Continuous-time LTM augmentation for existing video Q-formers.
- Gibbs-PDF continuous attention for stronger long-range memory retrieval.
- Sticky-memory consolidation based on accumulated attention density.
- Training-free adaptation of short-video architectures to long-video understanding.

## Method
Pipeline summary:
1. Split video frames into chunks.
2. For each chunk, run standard Q-former cross-attention (STM).
3. Pool frame patch embeddings and fit a continuous signal `x(t)=B^T ψ(t)`.
4. Compute LTM attention with Gibbs density:
   - $s_i^h(t)=q_i^T k^h(t)$
   - $p_i^h(t)=exp(s_i^h(t))/∫exp(s_i^h(t'))dt$
   - $Z_i^h=E_{p_i^h}[v^h(t)]$
1. Consolidate memory each chunk:
   - contract old memory by `τ`
   - sample `T` points (uniform or sticky)
   - concatenate old+new contexts and refit continuous representation
6. Mix STM/LTM outputs with weight `α`, then running-average chunk embeddings before LLM decoding.

Compact pseudocode:
```text
for chunk c in video_chunks:
  Z_stm = QFormer_STM(chunk_c)
  Z_ltm = ContinuousAttention_LTM(memory, queries)
  Z = alpha * Z_stm + (1-alpha) * Z_ltm
  E_bar = ((c-1)/c) * E_bar + (1/c) * Project(Z)
  memory = Consolidate(memory, chunk_c, tau, T, mode={uniform|sticky})
answer = LLM(E_bar, question)
```

## Pipeline Figure
![[assets/pipeline_2501.19098v1.png]]

Caption: Overview of ∞-Video with chunked processing, STM+LTM fusion, and final LLM answering.

Source: TeX figure (`diagram.pdf`) included from `main.tex` (overview figure).

## Experiments
### Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---|---|---|
| NeXT-QA | Multiple-choice video QA | Standard eval split | Accuracy | Short videos (~44s avg) |
| EgoSchema (subset) | Multiple-choice egocentric QA | Benchmark subset | Accuracy | ~3 minute videos |
| VideoMME | Long-video multiple-choice QA | Medium/Long subsets | Accuracy (Medium, Long, Avg) | Videos up to ~1 hour |
| MovieChat-1K | Long-video open-ended QA | Benchmark set | Accuracy, Score, CI, DO, CU | GPT-3.5-based judging protocol |

### Main Results
| Dataset | Metric | Baseline | Ours | Δ |
|---|---|---|---|---|
| NeXT-QA (Video-LLaMA family) | Accuracy | ∞-Video LLaMA (No LTM): 37.6 | ∞-Video LLaMA (Sticky): **41.1** | +3.5 |
| EgoSchema (Video-LLaMA family) | Accuracy | ∞-Video LLaMA (No LTM): 40.8 | ∞-Video LLaMA (Sticky): **46.8** | +6.0 |
| VideoMME Avg (VideoChat2 family) | Accuracy (Avg) | VideoChat2: 42.1 | ∞-VideoChat2 (Sticky): **42.4** | +0.3 |
| VideoMME Long (VideoChat2 family) | Accuracy (Long) | VideoChat2: 38.0 | ∞-VideoChat2 (Sticky): **38.9** | +0.9 |
| MovieChat (Video-LLaMA family) | Accuracy | MovieChat: 67.8 | ∞-Video LLaMA (Sticky): **72.2** | +4.4 |
| MovieChat (Video-LLaMA family) | Score | MovieChat: 3.81 | ∞-Video LLaMA (Sticky): **3.88** | +0.07 |

### Additional Reported Results (selected)
| Setting | Key numbers |
|---|---|
| NeXT-QA / EgoSchema, ∞-VideoChat2 variants | No LTM: 78.1 / 64.6; Uniform: 78.1 / 64.4; Sticky: 78.1 / **64.8** |
| MovieChat, ∞-VideoChat2 variants | Sticky: 63.9 acc, 3.74 score; No-STM Sticky: **66.5** acc, **3.85** score |

### Training / Compute (reported hyperparameters)
| Item | Value |
|---|---|
| Integral approximation | Trapezoidal rule, 1000 samples |
| ∞-Video LLaMA chunks/frames (typical) | 8 chunks × 256 frames |
| ∞-Video LLaMA basis functions `N` | 1024 (except NeXT-QA uses all available frames setting) |
| ∞-VideoChat2 chunks/frames | 8 chunks × 16 frames |
| ∞-VideoChat2 basis functions `N` | 256 |
| Forgetting/consolidation factor `τ` | 0.75 (0.5 on VideoMME config) |
| STM/LTM mixing `α` | tested values; key comparisons include α=1.0 (no LTM), α=0.9, and α=0 (no STM in some ablations) |

### Ablations / Analysis
| Study | Finding |
|---|---|
| Sticky vs Uniform memory sampling | Sticky generally outperforms uniform, especially for Video-LLaMA variants. |
| No LTM vs LTM | LTM helps most in long-context settings; gains are stronger in Video-LLaMA family than VideoChat2 family. |
| No STM variants (MovieChat) | For VideoChat2, no-STM sticky can be strongest; for Video-LLaMA, balanced STM+LTM is better. |

## Limitations & Caveats
- Improvements are model-family dependent; gains are larger for Video-LLaMA than VideoChat2 in several settings.
- Some evaluations rely on external LLM-based judging prompts for open-ended QA.
- Added long-context capability may increase misuse risk in surveillance/privacy-sensitive scenarios (noted by authors).

## Concrete Implementation Ideas
- Add continuous-time LTM as a drop-in cross-attention branch for other video Q-former backbones.
- Start with sticky-memory sampling and tune `τ` and `N` per dataset duration regime.
- Use chunk-wise streaming inference with running-average token aggregation to keep memory bounded.
- For resource-constrained setups, reduce chunk frame count and increase `N` only where long-range retention matters.

## Open Questions / Follow-ups
- What adaptive policy for `α` (instead of fixed scalar) best balances STM/LTM across tasks?
- Can sticky-memory sampling be learned end-to-end while remaining training-efficient?
- How robust are gains on longer, noisier real-world videos beyond benchmark distributions?
- Would replay-like offline consolidation steps improve continual video understanding?

## Citation
```bibtex
@misc{santos2025inftyvideotrainingfreeapproachlong,
  title={$\infty$-Video: A Training-Free Approach to Long Video Understanding via Continuous-Time Memory Consolidation},
  author={Saul Santos and António Farinhas and Daniel C. McNamee and André F. T. Martins},
  year={2025},
  eprint={2501.19098},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2501.19098}
}
```
