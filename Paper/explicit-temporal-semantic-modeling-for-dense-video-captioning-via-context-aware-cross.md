---
title: "Explicit Temporal-Semantic Modeling for Dense Video Captioning via Context-Aware Cross-Modal Interaction"
authors:
  - "Mingda Jia"
  - "Weiliang Meng"
  - "Zenghuang Fu"
  - "Yiheng Li"
  - "Qi Zeng"
  - "Yifan Zhang"
  - "Ju Xin"
  - "Rongtao Xu"
  - "Jiguang Zhang"
  - "Xiaopeng Zhang"
arxiv_id: "2511.10134"
arxiv_url: "https://arxiv.org/abs/2511.10134"
pdf_url: "https://arxiv.org/pdf/2511.10134.pdf"
published: 2025-11-13
updated: 2025-11-13
categories: ["cs.CV"]
tags: ["paper/arxiv", "status/read", "video-captioning", "dense-video-captioning"]
status: "read"
code: ""
datasets: ["ActivityNet Captions", "YouCook2"]
pipeline_figure: "assets/pipeline_2511.10134.pdf"
pipeline_caption: "The overview of CACMI: CLIP frame features -> Cross-modal Frame Aggregation (clustering + retrieval) -> Context-aware Feature Enhancement -> deformable transformer for localization + captioning."
pipeline_source: "TeX includegraphics from aaai2026.tex (figure* label fig:overview, file figures/figure_main.pdf)"
---

## TL;DR
- Proposes **CACMI**, a dense video captioning framework that explicitly models temporal-semantic structure instead of fragment-level implicit retrieval.
- Introduces **Cross-modal Frame Aggregation (CFA)** to cluster temporally coherent pseudo-events, then retrieve event-aligned text features from a sentence bank.
- Introduces **Context-aware Feature Enhancement (CFE)** to fuse visual and textual features with query-guided attention to reduce modality mismatch.
- Reports SOTA/non-pretrained-best results on ActivityNet Captions and YouCook2 for both captioning and localization metrics.
- Key gains over CM$^2$: +0.12 CIDEr / +0.13 SODA_c on ActivityNet and +3.17 CIDEr / +0.23 SODA_c on YouCook2.

## Key Contributions
- Explicit temporal-semantic modeling for retrieval-augmented dense video captioning.
- A pseudo-event-centric retrieval pipeline (CFA) to avoid fragmented sliding-window semantics.
- A cross-modal enhancement block (CFE) that uses text-guided visual refinement before transformer decoding.

## Method
Pipeline summary:
1. Extract frame features `F^v` with CLIP ViT-L/14.
2. **Event Context Clustering**: agglomerative clustering + temporal constraint (`t_max`) to form pseudo-events.
3. **Event Semantic Retrieval**: cosine match pseudo-event features to sentence-bank embeddings; top-k retrieval; mean pooling to get `F^q`.
4. **Context-aware Feature Enhancement**: query-guided dual attention between `F^v` and `F^q`; concatenate attended features; project + 1D conv with global text vector.
5. Deformable transformer + multi-task heads for event localization, captioning (LSTM-based), and event counting.

Compact pseudocode:
```text
Fv = CLIP(video_frames)
Fc = temporal_constrained_clustering(Fv)
Fq = topk_text_retrieval_and_pool(Fc, sentence_bank)
F_enh = context_aware_fusion(Fv, Fq)
events = deformable_transformer(F_enh)
outputs = {boundaries, captions, event_count}
```

## Pipeline Figure
![[assets/pipeline_2511.10134.pdf]]

Caption: The overview of CACMI with CFA + CFE and downstream multi-task decoding.

Source: TeX includegraphics from `aaai2026.tex` (`figures/figure_main.pdf`, label `fig:overview`).
已经帮你创建好了：[[我已学算法总表]]
## Experiments
### Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---|---|---|
| ActivityNet Captions | Dense video captioning + event localization | Train 10,024 / Val 4,926 / Test 5,044 | BLEU4, METEOR, CIDEr, SODA_c, F1/Recall/Precision | ~20k videos, ~700h, avg 3.7 captions/video |
| YouCook2 | Dense video captioning + event localization | Standard split (counts not explicitly listed) | BLEU4, METEOR, CIDEr, SODA_c, F1/Recall/Precision | 2,000 videos, 176h, avg 7.7 captions/video; ~7% unavailable videos removed |

### Main results table(s)
| Dataset              | Metric          | Baseline        | Ours      | Delta |
| -------------------- | --------------- | --------------- | --------- | ----- |
| ActivityNet Captions | BLEU4           | E$^2$DVC: 2.43  | **2.44**  | +0.01 |
| ActivityNet Captions | METEOR          | E$^2$DVC: 8.57  | **8.68**  | +0.11 |
| ActivityNet Captions | CIDEr           | E$^2$DVC: 33.63 | **33.80** | +0.17 |
| ActivityNet Captions | SODA_c          | CM$^2$: 6.18    | **6.39**  | +0.21 |
| YouCook2             | BLEU4           | E$^2$DVC: 1.68  | **1.70**  | +0.02 |
| YouCook2             | METEOR          | E$^2$DVC: 6.11  | **6.21**  | +0.10 |
| YouCook2             | CIDEr           | E$^2$DVC: 34.26 | **34.83** | +0.57 |
| YouCook2             | SODA_c          | E$^2$DVC: 5.39  | **5.57**  | +0.18 |
| ActivityNet Captions | Localization F1 | E$^2$DVC: 56.42 | **57.10** | +0.68 |
| YouCook2             | Localization F1 | E$^2$DVC: 28.87 | **29.34** | +0.47 |

### Ablations/Analysis tables
| Item | Value |
|---|---|
| Component ablation (ActivityNet): no CFA/CFE | B4 2.38, M 8.55, C 33.01, SODA_c 6.18, F1 55.21 |
| CFA only | B4 2.37, M 8.63, C 33.62, SODA_c 6.26, F1 56.07 |
| CFE only | B4 2.41, M 8.59, C 33.48, SODA_c 6.31, F1 56.95 |
| CFA + CFE | **B4 2.44, M 8.68, C 33.80, SODA_c 6.39, F1 57.10** |
| Cluster count sweep (N_cluster) | Best at **10** (B4 2.44, M 8.68, C 33.80, SODA_c 6.39, F1 57.10) |
| Retrieval top-k sweep | Best at **k=40** (B4 2.44, M 8.68, C 33.80, SODA_c 6.39, F1 57.10) |

### Training / Compute
| Item | Value |
|---|---|
| Visual encoder | CLIP ViT-L/14 |
| Sampling | 1 FPS |
| Input length | ActivityNet: 100 frames; YouCook2: 200 frames |
| Event queries (transformer) | ActivityNet: 10; YouCook2: 100 |
| Number of clusters | ActivityNet: 10; YouCook2: 20 |
| Retrieval top-k | 40 |
| GPU | NVIDIA RTX A6000 |

## Limitations & Caveats
- The method still relies on an external sentence bank; quality/coverage of that corpus may bound gains.
- YouCook2 results remain below pretrained Vid2Seq, suggesting data scarcity/domain diversity sensitivity.
- No explicit efficiency/latency analysis is reported for clustering + retrieval overhead.
- Hyperparameters (`N_cluster`, `k`) materially affect performance.

## Concrete Implementation Ideas
- Replace fixed top-k with adaptive retrieval (confidence-based dynamic k).
- Add lightweight temporal consistency regularization across neighboring pseudo-events.
- Distill CACMI into a smaller student model for lower-latency inference.
- Improve sentence-bank quality with domain-adaptive filtering or hard-negative mining.

## Open Questions / Follow-ups
- How robust is CACMI when sentence bank quality is noisy or out-of-domain?
- Can CFA be made differentiable end-to-end instead of clustering as a separate step?
- What is the runtime/memory tradeoff versus CM$^2$ and E$^2$DVC under identical hardware?
- Does multilingual sentence-bank retrieval improve performance for non-English captions?

## Citation
```bibtex
@misc{jia2025explicittemporalsemanticmodelingdense,
      title={Explicit Temporal-Semantic Modeling for Dense Video Captioning via Context-Aware Cross-Modal Interaction},
      author={Mingda Jia and Weiliang Meng and Zenghuang Fu and Yiheng Li and Qi Zeng and Yifan Zhang and Ju Xin and Rongtao Xu and Jiguang Zhang and Xiaopeng Zhang},
      year={2025},
      eprint={2511.10134},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2511.10134}
}
```
