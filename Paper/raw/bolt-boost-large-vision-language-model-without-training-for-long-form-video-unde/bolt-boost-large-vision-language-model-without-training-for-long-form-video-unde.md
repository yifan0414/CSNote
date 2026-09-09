---
title: (frame)BOLT
authors:
  - Shuming Liu
  - Chen Zhao
  - Tianqi Xu
  - Bernard Ghanem
conference: CVPR 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2503.21483
pdf_link: "[[assets/paper_2503.21483.pdf]]"
cover: "[[_assets/images/pipeline_2503.21483.png]]"
updated: 2026-05-28
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - question-aware
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/sming256/BOLT
---

## TL;DR

- BOLT 是一种无需训练的 long-form video understanding 增强方法：不改动 VLM，只在 inference 时用 query-aware frame selection 替代 uniform sampling。
- 核心策略是 **Inverse Transform Sampling (ITS)**：根据 CLIP-L/14 计算的 query-frame similarity 构造时间分布，在关注相关帧的同时保留上下文与帧多样性。
- 对 LLaVA-OneVision-7B（8 frames），BOLT 将 Video-MME（无字幕）accuracy 从 53.8% 提高到 **56.1%**，将 MLVU 从 58.9% 提高到 **63.4%**。
- 作者提出 multi-source retrieval evaluation：把多个不相关视频拼接后再问其中一个视频的问题；在更强噪声下，16-frame BOLT 在 Video-MME 上从 47.8% 提高到 **53.4%**。
- 代价主要不是 ITS 本身，而是额外的 CLIP feature encoding：16-frame 推理总时间由 1.32 s 增至 2.53 s（+90.9%）。

## Key Contributions

- 通过 MultiHop-EgoQA 的 GT temporal segments 与新的 multi-source retrieval setting，实证说明 long video 中“选对帧”直接决定 VLM 的效果。
- 系统比较 training-free 的 Uniform、Top-K、Watershed Grouping 与 ITS；ITS 在 query relevance 和 temporal diversity 之间表现最稳健。
- 在五个 VQA benchmarks（Video-MME、EgoSchema、LongVideoBench、MLVU、NextQA）及多个 off-the-shelf VLM 上展示可插拔收益，不需要额外 fine-tuning。

## Method

BOLT 位于 frozen VLM 的输入端，只替换 temporal frame selection：

1. 将视频以 1 FPS 形成候选帧序列，并以 CLIP-L/14 编码每帧和问题文本，计算 cosine similarity $s_i$。
2. 将 similarity 归一化后用 $\alpha$ 调节分布锐度：

$$
s_i^r = \left(\frac{s_i - \min(s)}{\max(s) - \min(s)}\right)^\alpha
$$

3. 以精炼分数构造沿时间轴的 cumulative distribution function：

$$
F(i) = \frac{\sum_{j=1}^{i} s_j^r}{\sum_{j=1}^{N} s_j^r}
$$

4. 在 $F^{-1}$ 上均匀取 $N$ 个位置，得到输入 VLM 的帧：

$$
f_i' = f_{\arg\min_k\{F(k) \ge i/N\}}, \qquad i \in \{1,\ldots,N\}
$$

5. 所选帧送入原有 VLM 生成答案；VLM 参数全程冻结。论文设置中，Video-MME 与 MLVU 使用 $\alpha=3$，EgoSchema、LongVideoBench 与 NextQA 使用 $\alpha=2.5$。

直觉上，Top-K 容易挤在单个峰值周围而产生冗余；ITS 会增加高相似区域的采样密度，但仍给低概率上下文留出帧预算，因此更适合存在干扰片段的长视频。

## Pipeline Figure

![[_assets/images/pipeline_2503.21483.png]]

Caption: BOLT 的 training-free frame selection framework，并对比 Top-K、Watershed Grouping 与 Inverse Transform Sampling；ITS 依据相似度累积分布选取相关且分散的帧。

Source: TeX `\includegraphics{figures/method.pdf}` in `sec/3_method.tex`; rendered from the PDF figure `CropBox` at 250 DPI.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split / Setting | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME | Video QA | without subtitles; Short / Medium / Long | Accuracy (%) | 900 videos、2,700 questions；另构造 multi-source retrieval |
| EgoSchema | Video QA | Full / Subset | Accuracy (%) | 平均视频短于 2 分钟 |
| LongVideoBench | Long-video QA | standard | Accuracy (%) | 长视频 benchmark |
| MLVU | Multi-task long-video QA | standard | Accuracy (%) | 长视频 benchmark |
| NextQA | Video QA | standard | Accuracy (%) | 平均视频短于 2 分钟 |
| MultiHop-EgoQA | Grounded multi-hop VideoQA | GT temporal segment analysis | Average sentence similarity | 用于验证相关时段选择的重要性 |

### Main Results

以下为 Table 3 中 LLaVA-OneVision-7B 的成对比较。粗体沿用论文在每个 frame budget 内标出的结果。

| Frames | Method | Video-MME Overall | Short | Medium | Long | EgoSchema Full | Subset | LongVideoBench | MLVU | NextQA |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | LLaVA-OneVision | 53.8 | 63.6 | 52.0 | 45.7 | 59.17 | 62.0 | 54.2 | 58.9 | 77.4 |
| 8 | **LLaVA-OneVision + BOLT** | **56.1** | **66.8** | **54.2** | **47.3** | **59.23** | **62.2** | **55.6** | **63.4** | **77.4** |
| 16 | LLaVA-OneVision | 56.9 | 68.3 | 54.0 | **48.2** | 59.49 | 61.4 | 55.7 | 61.2 | 78.1 |
| 16 | **LLaVA-OneVision + BOLT** | **57.8** | **69.2** | **56.8** | 47.3 | **59.86** | **61.8** | **57.0** | **65.8** | **78.3** |
| 32 | LLaVA-OneVision | 58.5 | **70.3** | 56.6 | 48.8 | 60.36 | 62.2 | 56.4 | 63.2 | 79.4 |
| 32 | **LLaVA-OneVision + BOLT** | **59.9** | 70.1 | **60.0** | **49.6** | **60.66** | **64.0** | **59.6** | **66.8** | **79.5** |

**Off-the-shelf VLM transfer (Video-MME without subtitles, 8 frames).** 粗体按原表保留。

| Model | BOLT | Overall | Short | Medium | Long |
| --- | --- | ---: | ---: | ---: | ---: |
| Video-LLaVA-7B | No | 37.6 | 42.7 | 37.1 | 33.0 |
| Video-LLaVA-7B | Yes | **39.3** | **45.7** | **38.0** | **34.1** |
| LongVA-7B | No | 48.5 | 56.7 | 46.6 | 42.3 |
| LongVA-7B | Yes | **51.6** | **59.8** | **51.0** | **43.9** |
| InternVL2-8B | No | 52.6 | 62.4 | 51.1 | 44.2 |
| InternVL2-8B | Yes | **53.3** | **65.6** | **50.4** | **43.9** |
| LLaVA-Video-7B | No | 56.0 | 67.8 | 53.6 | 46.7 |
| LLaVA-Video-7B | Yes | **58.6** | **70.4** | **55.7** | **49.9** |

**Multi-source retrieval on Video-MME without subtitles ($K=4$, LLaVA-OneVision-7B).**

| Frames | Method | Overall | Short | Medium | Long |
| ---: | --- | ---: | ---: | ---: | ---: |
| 64 | LLaVA-OneVision | 52.1 | 61.8 | 50.8 | 43.8 |
| 64 | LLaVA-OneVision + BOLT | **54.9** | **66.1** | **54.2** | **44.4** |
| 16 | LLaVA-OneVision | 47.8 | 55.8 | 45.6 | 42.0 |
| 16 | LLaVA-OneVision + BOLT | **53.4** | **65.1** | **51.1** | **43.3** |

### Ablations / Analysis

**Selecting relevant temporal segments (MultiHop-EgoQA, 8 frames).**

| Frame Selection | LLaVA-NeXT-Video-7B sentence similarity | InternVL2-8B sentence similarity |
| --- | ---: | ---: |
| Uniform | 61.7 | 71.8 |
| GT segments | **62.8** (+1.1) | **72.5** (+0.7) |
| Without GT segments | 59.2 (-2.5) | 69.1 (-2.7) |

**Frame selection strategy (Video-MME, LLaVA-OneVision-7B, 16 frames).**

| Frame Selection | Query-aware | Standard accuracy (%) | Retrieval-Based accuracy (%) |
| --- | --- | ---: | ---: |
| Blind Test | No | 40.85 | 40.85 |
| Uniform | No | 56.85 | 47.78 |
| Uniform + Shuffle | No | 56.25 (-0.60) | 46.93 (-0.85) |
| Random | No | 55.15 (-1.70) | 46.05 (-1.73) |
| Top-K | Yes | 57.10 (+0.25) | 48.45 (+0.67) |
| Watershed | Yes | 57.23 (+0.38) | 49.15 (+1.37) |
| **ITS** | Yes | **57.78** (+0.93) | **53.37** (+5.59) |

**Similarity encoder selection (Video-MME, LLaVA-OneVision-7B, 16 frames).**

| Uniform baseline | Caption | SigLIP | CLIP | CLIP + SigLIP |
| ---: | ---: | ---: | ---: | ---: |
| 56.85 | 55.47 | 57.00 | **57.78** | **57.83** |

**Sharpness parameter $\alpha$ in ITS (LLaVA-OneVision-7B, 16 frames).** 原表未标粗最佳值，以下保留其未强调形式。

| $\alpha$ / Setting | Video-MME accuracy (%) | MLVU accuracy (%) | LongVideoBench accuracy (%) |
| --- | ---: | ---: | ---: |
| Uniform | 56.90 | 61.24 | 55.72 |
| 2.0 | 58.37 | 65.08 | 58.04 |
| 2.5 | 57.51 | 65.24 | 57.00 |
| 3.0 | 57.78 | 65.76 | 57.67 |
| 3.5 | 57.74 | 65.11 | 58.41 |

**Noise level in multi-source retrieval (Video-MME, 16 frames).** $K=1$ 退化为 standard setting，$K$ 越大背景噪声越强。

| Method | $K=1$ | $K=2$ | $K=4$ | $K=8$ |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 56.85 | 51.81 | 47.78 | 44.82 |
| Watershed | 57.23 | 53.70 | 48.67 | 45.89 |
| **ITS** | **57.78** | **54.93** | **53.37** | **49.04** |

### Training / Compute

| Item | Value |
| --- | --- |
| Training requirement | Training-free; frozen downstream VLM |
| Query-frame encoder | Pretrained CLIP-L/14 |
| Candidate frame rate | 1 FPS |
| Selection algorithm | Inverse Transform Sampling (ITS) |
| $\alpha$ | 3 for Video-MME / MLVU; 2.5 for EgoSchema / LongVideoBench / NextQA |
| Evaluation library | LMMs-Eval for multiple-choice accuracy |
| Experiment hardware | 2 x A100 GPUs |
| Inference cost setup | LLaVA-OneVision-7B, 16 frames, 1 x A100 |
| VLM inference time | 1.32 s |
| CLIP visual feature time | 1.21 s |
| ITS time | 0.003 s |
| Total time | 2.53 s (+90.9%) |

## Limitations & Caveats

- 论文明确指出，BOLT 依赖 query-frame similarity 的准确性；仅靠 CLIP 相似度可能捕获不到因果、组合推理或 multi-round VQA 所需的真正证据。
- 该方法不增加训练成本，但增加推理前的全视频 CLIP 扫描；论文报告总 latency 接近翻倍，长视频部署时需考虑这一开销。
- Multi-source retrieval evaluation 是以拼接不同视频模拟背景干扰的压力测试，能够测 retrieval robustness，但不完全等价于自然连续长视频中的事件演化。
- 对较短视频的 NextQA，收益很小（8 frames 为持平，16/32 frames 仅小幅变化），说明收益主要来自长视频和噪声上下文。
- 原文 Table 6 将 ITS 的 retrieval-based 分数记为 `53.37`，相邻正文写作 `53.35`，Table 5 四舍五入为 `53.4`；本笔记采用表格原值 `53.37`。
- Table 4 对 InternVL2+BOLT 的 Medium / Long 值也使用了粗体，尽管数值略低于对应 baseline；上表按作者强调原样保留，不将其解读为子集提升。

## Concrete Implementation Ideas

1. 在现有 Video-LLM 推理入口前增加 `FrameSelector`：缓存 1 FPS 的 CLIP image embeddings，每次 query 只编码文本并执行 ITS，从而摊薄重复提问场景中的额外耗时。
2. 将 ITS 与固定 frame budget controller 结合：对 similarity 分布平坦的视频降低 $\alpha$ 或回退到 uniform sampling，对尖峰明显的视频提升 query-focused 配额。
3. 在自有长视频数据上实现 multi-source retrieval stress test，分别报告 clean、distractor-heavy 和 naturally long settings，避免只优化标准短片段评估。
4. 针对 OCR、action causality 或 dialogue-dependent queries，比较 CLIP、SigLIP、caption embedding 与任务特定 retriever 的 calibration，而不先改动下游 VLM。

## Open Questions / Follow-ups

- 扫描整段长视频的 CLIP 成本随时长如何增长？embedding cache、scene boundary proposal 或 coarse-to-fine selection 能否保住效果并显著降低 90.9% latency overhead？
- 论文的相似度目标仅使用问题文本；对 multiple-choice tasks，把 answer options 纳入 query 是否会提升检索，也是否会带来 shortcut bias？
- ITS 对真正需要跨多个远距离事件进行 causal reasoning 的问题，是否仍会保留足够的过渡上下文？
- 在字幕、OCR、音频和 visual evidence 同时存在时，最合理的跨模态 frame/segment sampling 分布应如何构造？

## Citation

```bibtex
@inproceedings{liu2025bolt,
  title     = {BOLT: Boost Large Vision-Language Model Without Training for Long-form Video Understanding},
  author    = {Liu, Shuming and Zhao, Chen and Xu, Tianqi and Ghanem, Bernard},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year      = {2025},
  url       = {https://arxiv.org/abs/2503.21483}
}
```
