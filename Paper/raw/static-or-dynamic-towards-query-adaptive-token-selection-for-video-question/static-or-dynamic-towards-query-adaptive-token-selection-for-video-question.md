---
title: "Static or Dynamic: Towards Query-Adaptive Token Selection for Video Question Answering"
authors:
  - Yumeng Shi
  - Quanyu Long
  - Wenya Wang
conference: EMNLP 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2504.21403
pdf_link: "[[assets/paper_2504.21403.pdf]]"
cover: "[[assets/pipeline_2504.21403.png]]"
updated: 2026-05-10
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/ANDgate99/Explore-Then-Select
---

## TL;DR

- 这篇论文指出 VideoQA 的 token 压缩不应该只按固定规则做，因为不同问题对 static information 和 dynamic information 的依赖不同。
- 作者提出 training-free 的 **Explore-then-Select** 框架：先探索多种 key-frame / delta-frame token 配比，再用 query-aware attention metric 选择最适合当前问题的 token subsequence。
- 方法是 plug-and-play 的 pre-input compression，不需要训练，也不改 VideoLM 参数，目标是在固定 token budget 下保留更多与问题相关的视频信息。
- 主实验覆盖 long video benchmarks: VideoMME, EgoSchema, MLVU，以及 short video benchmarks: MSVD-QA, ActivityNet-QA；在 Qwen2-VL-7B 上提升最明显，VideoMME medium subset 最高提升 5.8%。
- 代价是 first-token latency 增加：selection 需要在 shallow attention layer 上比较多个候选 subsequences，但不影响后续 decoding。

## Key Contributions

1. 提出 **query-adaptive visual token selection**：根据问题类型动态平衡 key-frame tokens 表示的 static information 与 delta-frame tokens 表示的 temporal changes。
2. 设计 **Explore-then-Select** 两阶段框架：exploration 构造不同 static/dynamic token allocation 的候选 subsequences，selection 用 shallow attention 的 query-aware score 选最优候选。
3. 方法属于 **training-free + pre-input + video-specific** token compression，可直接接入 Qwen2-VL、LLaVA-OneVision、Qwen2.5-VL 等 VideoLM。
4. 实验显示该策略在 long video VideoQA 上更有效，尤其适合 token budget 严格、问题类型差异较大的场景。

## Method

问题设定：给定视频视觉 token sequence 长度 $L$，但推理时只能输入长度为 $L_b$ 的视觉 token budget，且通常 $L \gg L_b$。论文目标是先采样更多 frames 获得更丰富信息，再压缩到 $L_b$。

核心 pipeline:

1. **Frame categorization**：把视频 frames 划分为 key frames 和 delta frames。key-frame tokens 保留完整空间细节；delta-frame tokens 只保留与前一个 key frame 差异最大的局部 token。
2. **Exploration**：改变 key frame 数量 $N_s \in \{1,2,\dots,n\}$，生成 $n$ 个长度都为 $L_b$ 的候选 token subsequences。较小 $N_s$ 倾向 dynamic information，较大 $N_s$ 倾向 static information。
3. **Delta token selection**：对每个 interval 内的 token，计算其与前一个 key frame 相同空间位置 token 的 cosine dissimilarity，并选 top tokens。
4. **Selection**：在 VideoLM 的第二层 attention 上，用 textual query tokens 作为 query，instruction + visual tokens 作为 key，计算 visual tokens 被 query 关注的总分，选 attention score 最高的 subsequence 输入 LLM。

Key-frame indices:

$$
\mathcal{I}=\left\{\left\lfloor \frac{kT}{N_s}\right\rfloor+1 \mid k=0,1,\dots,N_s-1\right\}
$$

Delta-frame token difference metric:

$$
\mathcal{D}(\boldsymbol{f}_i,\boldsymbol{f}_j)=1-\frac{\boldsymbol{f}_i\cdot\boldsymbol{f}_j}{\|\boldsymbol{f}_i\|\|\boldsymbol{f}_j\|}
$$

Selection attention score:

$$
\boldsymbol{Q}=\boldsymbol{W}_{\text{Q}}\boldsymbol{H}_q, \quad
\boldsymbol{K}=\boldsymbol{W}_{\text{K}}\,\text{concat}(\boldsymbol{H}_i,\boldsymbol{H}_v)
$$

$$
\boldsymbol{S}=\text{softmax}\left(\frac{\boldsymbol{QK}^{\top}}{\sqrt{d_k}}\right)
$$

$$
\boldsymbol{s}=\max_i \boldsymbol{S}_{ij}, \quad
s=\sum_{j=N_i}^{N_i+N_v}\boldsymbol{s}_j, \quad
\bar{\boldsymbol{T}}_v=\underset{m\in\{1,2,\dots,n\}}{\arg\max}\,s^m
$$

直觉上，selection 认为「query 对视觉 token 的累计关注越高」，这个候选 subsequence 越可能包含回答当前问题所需的信息。

## Pipeline Figure

![[assets/pipeline_2504.21403.png]]

Caption: Overview of our Explore-then-Select framework for token selection. During the exploration stage, multiple subsequences are generated from different combinations of key and delta-frame tokens. In the selection stage, these subsequences are evaluated using query-aware metrics computed from shallow attention layers, and the optimal subsequence is chosen as input to the LLM.

Source: TeX includegraphics from `acl_latex.tex`, `figure/framework_new.pdf`; converted to `assets/pipeline_2504.21403.png` with PDF crop box.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| VideoMME | Long video multiple-choice VideoQA | 900 videos, 2,700 QA pairs | Accuracy | 视频长度 11 seconds 到 1 hour；报告 Short / Medium / Long / Overall。 |
| EgoSchema | Long video multiple-choice VideoQA | over 5,000 questions | Accuracy | 视频平均约 3 minutes。 |
| MLVU | Long video multiple-choice VideoQA | test set over 500 QA pairs | Accuracy | 视频长度 3 minutes 到 2 hours；MLVU 生成 3 tokens。 |
| MSVD-QA | Short video open-ended VideoQA | test split about 13,000 questions | Accuracy, GPT-4o mini score | 1,970 short clips，平均约 10 seconds。 |
| ActivityNet-QA | Short video open-ended VideoQA | 800 videos, 8,000 QA pairs in test set | Accuracy, GPT-4o mini score | short video benchmark。 |

### Method Positioning

| Method | Pre-Input | Training-Free | Video-Specific |
| ---- | ---- | ---- | ---- |
| FastV | ✗ | ✓ | ✗ |
| ZipVL | ✗ | ✓ | ✗ |
| FrameFusion | ✗ | ✓ | ✓ |
| TokenPacker | ✓ | ✗ | ✗ |
| VideoStreaming | ✓ | ✗ | ✓ |
| SlowFocus | ✓ | ✗ | ✓ |
| LongVU | ✓ | ✗ | ✓ |
| **Ours** | **✓** | **✓** | **✓** |

论文强调：很多 training-free 方法只在 KV cache 内压缩，不能减少输入 LLM 的视觉 token 数；而 pre-input compression 方法通常需要训练。Explore-then-Select 填补的是 training-free pre-input video token compression。

### Main Results: Long Video Benchmarks

下表保留论文 Table 2 的主要矩阵。第一组 training-based video understanding methods 仅作参考，作者说明它们因训练成本不同而不完全可比。

| Model | Method | Sample | Budget | EgoSchema | VideoMME Short | VideoMME Medium | VideoMME Long | VideoMME Overall | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| VideoChat2 | - | 16 | - | 54.4 | 48.3 | 37.0 | 33.2 | 39.5 | - |
| LongVA | - | 128 | - | - | 61.1 | 50.4 | 46.2 | 52.6 | - |
| mPLUG-Owl3 | - | 128 | - | - | 70.0 | 57.7 | 50.1 | 59.3 | - |
| LongVU | - | 1fps | - | 67.6 | - | - | - | 60.6 | 65.4 |
| Qwen2-VL-7B | Original | 64 | - | 66.2 | 71.1 | 59.4 | 50.8 | 60.4 | 50.6 |
| Qwen2-VL-7B | Retrieval | 256 | 64 | 63.6 | 71.0 | 61.3 | 52.2 | 61.5 | 49.4 |
| Qwen2-VL-7B | Similarity | 256 | 64 | 66.6 | 71.4 | 60.6 | 51.8 | 61.3 | 53.0 |
| Qwen2-VL-7B | **Ours** | **256** | **64** | **67.8** | **72.4** | **63.1** | **53.2** | **62.9** | **54.4** |
| Qwen2-VL-7B | Original | 32 | - | 64.7 | 68.9 | 55.2 | 48.7 | 57.6 | 46.8 |
| Qwen2-VL-7B | Retrieval | 128 | 32 | 61.7 | 70.0 | 58.6 | 51.6 | 60.0 | 46.8 |
| Qwen2-VL-7B | Similarity | 128 | 32 | 65.6 | 70.1 | 58.7 | **51.8** | 60.2 | 47.2 |
| Qwen2-VL-7B | **Ours** | **128** | **32** | **66.7** | **71.4** | **61.0** | 51.7 | **61.4** | **52.2** |
| LLaVA-OneVision-7B | Original | 64 | - | 60.1 | 70.6 | 55.8 | 47.8 | 58.0 | 50.8 |
| LLaVA-OneVision-7B | Retrieval | 256 | 64 | 57.7 | 64.0 | 53.4 | 47.0 | 54.8 | 44.6 |
| LLaVA-OneVision-7B | Similarity | 256 | 64 | 59.6 | 71.0 | 57.9 | 50.8 | 59.9 | 48.4 |
| LLaVA-OneVision-7B | **Ours** | **256** | **64** | **60.3** | **71.9** | **58.3** | **51.4** | **60.6** | **51.2** |
| LLaVA-OneVision-7B | Original | 32 | - | 60.4 | **71.3** | 57.4 | 48.0 | 58.9 | 46.8 |
| LLaVA-OneVision-7B | Retrieval | 128 | 32 | 57.9 | 63.2 | 53.9 | 46.0 | 54.4 | 44.0 |
| LLaVA-OneVision-7B | Similarity | 128 | 32 | 60.2 | 70.8 | 57.1 | 49.7 | 59.2 | 50.2 |
| LLaVA-OneVision-7B | **Ours** | **128** | **32** | **60.5** | 70.2 | **58.0** | **51.6** | **59.9** | **51.0** |

主要结论：Qwen2-VL-7B 上收益最稳定；256-64 setting 下相对 baseline 最高提升 EgoSchema 4.2%、VideoMME 2.5%、MLVU 5.0%；128-32 setting 下分别最高提升 5.0%、3.8%、5.4%，其中 VideoMME medium subset 提升 5.8%。LLaVA-OneVision-7B 的提升较小，作者推测与其 one-dimensional positional encoding 的噪声有关。

### Main Results: Short Video Benchmarks

| Model | Method | MSVD-QA Acc | MSVD-QA Score | ActivityNet-QA Acc | ActivityNet-QA Score |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2-VL | Original | 66.0 | 3.59 | 50.3 | 2.82 |
| Qwen2-VL | Retrieval | 64.4 | 3.52 | 48.6 | 2.74 |
| Qwen2-VL | Similarity | 66.5 | 3.60 | 51.4 | 2.87 |
| Qwen2-VL | **Ours** | **66.8** | **3.61** | **52.4** | **2.90** |
| LLaVA-OneVision | Original | 54.3 | 3.09 | 52.6 | 2.90 |
| LLaVA-OneVision | Retrieval | **54.8** | **3.12** | 50.1 | 2.77 |
| LLaVA-OneVision | Similarity | 54.3 | 3.10 | 52.4 | 2.89 |
| LLaVA-OneVision | **Ours** | 54.7 | 3.11 | **53.0** | **2.92** |

短视频场景中 frames 少、motion 更连贯，因此 static/dynamic allocation 的收益不如 long video 明显，但 Qwen2-VL 上仍稳定优于 baseline。

### Ablations / Analysis

Stage ablation on Qwen2-VL-7B, 128-frame sampling, 32-frame budget:

| Method | EgoSchema | VideoMME | MLVU |
| ---- | ---- | ---- | ---- |
| Original | 64.7 | 57.6 | 46.8 |
| Explore + Random | 66.3 | 60.7 | 50.2 |
| Explore + Select | **66.7** | **61.4** | **52.2** |

这说明 exploration 本身已经比原始 uniform sampling 更好，而 query-aware selection 还能进一步提升。

Metric design ablation on Qwen2-VL-7B, 128-frame sampling, 32-frame budget:

| Model | Method | EgoSchema | VideoMME |
| ---- | ---- | ---- | ---- |
| Qwen2-VL | w/ query | 66.3 | **61.6** |
| Qwen2-VL | w/o query | **66.7** | 61.4 |
| Qwen2-VL | mean | 66.0 | 60.9 |
| Qwen2-VL | max | **66.7** | **61.4** |

作者结论：在 $\boldsymbol{K}$ 中是否包含 query token 影响很小，因此最终设计省略；对 query dimension 做 max aggregation 比 mean 更好。

Efficiency trade-off on MLVU using Qwen2-VL, compressing sampled frames into a 32-frame budget:

| Metric | 32 | 64 | 128 | 256 | 512 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Accuracy (%) | 46.8 | 52.0 | 52.2 | 54.0 | 54.6 |
| Encoding (s) | 0.125 | 0.222 | 0.424 | 0.827 | 1.628 |
| Selection (s) | - | 0.537 | 0.557 | 0.565 | 0.575 |

更多 sampled frames 能提升 accuracy；encoding cost 近似线性增长，selection cost 稳定在约 0.5-0.6s，主要影响 first-token latency。

### Appendix Results

Qwen2.5-VL-7B long video benchmark:

| Model | Method | Sample | Budget | EgoSchema | VideoMME Short | VideoMME Medium | VideoMME Long | VideoMME Overall | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2.5-VL-7B | Original | 256 | - | 60.3 | 75.0 | 61.8 | 51.0 | 62.6 | 50.0 |
| Qwen2.5-VL-7B | Retrieval | 256 | 64 | 60.9 | 75.4 | **66.7** | 54.8 | 65.6 | 56.2 |
| Qwen2.5-VL-7B | Similarity | 256 | 64 | 60.8 | 74.0 | 64.7 | 54.3 | 64.3 | 53.6 |
| Qwen2.5-VL-7B | **Ours** | **256** | **64** | **61.6** | **75.8** | 65.2 | **56.1** | **65.7** | **58.4** |
| Qwen2.5-VL-7B | Original | 128 | - | 59.1 | 73.1 | 60.0 | 49.6 | 60.9 | 47.2 |
| Qwen2.5-VL-7B | Retrieval | 128 | 32 | 60.2 | **74.6** | **64.8** | 53.3 | **64.2** | 48.4 |
| Qwen2.5-VL-7B | Similarity | 128 | 32 | 60.0 | 73.3 | 60.9 | 51.6 | 61.9 | 47.6 |
| Qwen2.5-VL-7B | **Ours** | **128** | **32** | **60.6** | 74.1 | 63.2 | **53.9** | 63.7 | **51.6** |

Comparison with reproduced training-free LongVU:

| Model | Method | EgoSchema | VideoMME |
| ---- | ---- | ---- | ---- |
| Qwen2-VL | Original | 66.2 | 60.4 |
| Qwen2-VL | LongVU | 67.2 | 62.3 |
| Qwen2-VL | **Ours** | **67.8** | **62.9** |
| LLaVA-OneVision | Original | 60.1 | 58.0 |
| LLaVA-OneVision | LongVU | **60.3** | 59.3 |
| LLaVA-OneVision | **Ours** | **60.3** | **60.6** |
| Qwen2.5-VL | Original | 60.3 | 62.6 |
| Qwen2.5-VL | LongVU | 61.6 | 64.5 |
| Qwen2.5-VL | **Ours** | **61.6** | **65.7** |

作者认为 LongVU 在 training-free reproduction 下需要阈值和 heuristic 调参才能接近 token budget；Explore-then-Select 用 top-K selection，token count 控制更直接。

## Limitations & Caveats

- 模型 positional encoding 机制会影响方法表现：论文指出不同模型对 video length estimation 和 temporal localization 的能力不同，LLaVA-OneVision 的 one-dimensional positional encoding 可能带来噪声。
- 方法没有额外 memory overhead，但有额外 time cost；selection 需要计算第二层 attention 中 query-to-visual-token attention，并比较多个 subsequences。
- 额外开销主要发生在 initial token inference / first-token latency，不影响后续 decoding；但对 latency-sensitive serving 仍需要评估。
- search space 不是越大越好：EgoSchema 受益于更大 search space，但 VideoMME 会下降，作者将默认 search space size 设为 frame budget 的一半。
- training-based 方法与该 training-free 方法不完全可比；论文主要用 Original / Retrieval / Similarity 和 reproduced LongVU 做较公平对照。

## Concrete Implementation Ideas

1. 在本地 VideoLM inference pipeline 中，把 frame sampling 改成「oversample -> Explore-then-Select -> fit budget」，先对 Qwen2-VL 类模型试验，因为论文中它收益最大。
2. 将 $n$ 个候选 subsequences 并行计算 shallow attention score，减少 first-token latency；论文当前 selection cost 约 0.5-0.6s，仍有工程优化空间。
3. 为不同 benchmark / domain 记录 selected key:delta ratio，分析问题类型是否稳定对应 OCR/object recognition/action recognition 等类别。
4. 把 search space size 作为可配置参数：默认 $\lfloor T_b/2 \rfloor$，但对 EgoSchema-like 长视频推理可以尝试更大空间，对 VideoMME-like 混合长度任务保持保守。
5. 与 LongVU / frame retrieval 组合：先粗粒度去除明显冗余 frames，再在剩余 frames 上做 query-adaptive key/delta token allocation。

## Open Questions / Follow-ups

- Query-aware attention score 与最终 answer correctness 的相关性有多强？是否可以做 per-question confidence calibration？
- 如果模型没有易取的 shallow attention，或者使用 flash attention 难以暴露 attention map，selection stage 如何高效实现？
- Delta-frame token 的 cosine dissimilarity 是否会偏向局部视觉噪声？是否需要 motion-aware 或 object-aware filtering？
- 对 open-ended long video QA、temporal grounding、multi-hop video reasoning，key/delta allocation 是否仍然保持同样趋势？
- 能否学习一个轻量 predictor 近似 selection score，从而保留 training-free 主模型但减少多候选 attention 计算？

## Citation

```bibtex
@misc{shi2025staticdynamic,
  title = {Static or Dynamic: Towards Query-Adaptive Token Selection for Video Question Answering},
  author = {Shi, Yumeng and Long, Quanyu and Wang, Wenya},
  year = {2025},
  eprint = {2504.21403},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2504.21403}
}
```
