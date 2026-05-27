---
title: VQOS
authors:
  - Zhirong Wu
  - Xiaodong Wang
  - Langling Huang
  - Teng Xu
  - Peixi Peng
conference: ICLR 2026
year: 2026
paper_url: ""
source_pdf: /Users/yifan/Downloads/6998_A_Training_Free_Framework (3).pdf
pdf_link: "[[assets/paper_6998_A_Training_Free_Framework_3_dfa959da.pdf]]"
cover: "[[assets/pipeline_6998_A_Training_Free_Framework_3_dfa959da.png]]"
updated: 2026-05-26
tags:
  - paper/pdf
  - long-video
  - video-qa
  - temporal-reasoning
  - question-aware
  - option-aware
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/wuzhirong520/VTR-VLM
---

## TL;DR

- 论文提出一个无需训练的长视频理解框架，把 `Video-Query-Options Similarity (VQOS)` 用于定位与问题/候选答案最相关的视频片段，再通过 `Adaptive Frame Sampling (AFS)` 与 `Dynamic Resolution Allocation (DRA)` 调配有限视觉 token 预算。
- 关键洞察是：只用 question 检索可能漏掉动作或时序线索；先由原始 MLLM 生成可能答案，再检索 “question + option” statements，可更聚焦于能验证假设的片段。
- 在 `LLaVA-Video-7B` 上，`Ours-GO` 将五项 benchmark 的报告平均分从 50.6 提至 55.9；在 `Qwen2.5-VL-7B` 上从 52.8 提至 57.8（Table 1, p. 7）。
- 提升主要集中于更长且关键事件稀疏的任务：例如 `LVBench` 上 `Qwen2.5-VL-7B + Ours-GO` 从 45.5 提至 52.7，`VideoEval-Pro Open` 从 27.7 提至 35.0（Table 1, p. 7）。
- 该方法的代价是额外 VTR 检索开销以及可能丢失全局叙事线索；附录实验显示，简单拼接全局文字摘要反而会降低准确率。

## Key Contributions

1. 提出 `VQOS`：对视频 segment 与由 question/option 组合得到的多个 textual hypotheses 计算相似度，借助候选答案增强 relevance estimation。
2. 提出 `AFS`：在总帧数固定时，把更高的 sampling density 分配给相似度更高的 segment，以保留关键时序细节。
3. 提出 `DRA`：在视觉 token budget 固定时，为高相关帧分配较高 spatial resolution，为较低相关帧压缩分辨率；该模块用于支持动态分辨率的 `Qwen2.5-VL`。
4. 将框架直接接入 `LLaVA-Video` 与 `Qwen2.5-VL` 的 7B/72B 版本，在 5 个 long-video benchmarks 上展示 training-free 的可扩展增益。

## Method

视频首先被均匀切为 $m$ 个 segments，$\mathcal{V}=\{V_1,V_2,\ldots,V_m\}$。VTR model 为 segment 与 question 提取 embedding，得到初始 question-only similarity：

$$
S_i^0 = \frac{f_{v_i} \cdot f_q}{\|f_{v_i}\| \cdot \|f_q\|}.
$$

随后原始 MLLM 生成 $z$ 个 plausible options，并与问题拼接形成 statements $\mathcal{T}=\{T_1,T_2,\ldots,T_z\}$。`VQOS` 对每个 segment 取多个 statement similarities 的最大值：

$$
S_i = \max_{f \in \mathcal{F}}
\frac{f_{v_i} \cdot f}{\|f_{v_i}\| \cdot \|f\|}.
$$

`AFS` 在总帧数 $N$ 不变的条件下，让更相关的片段采样更多帧：

$$
\sum_{i=1}^{k} p_i = N,\qquad S_i \leq S_j \Rightarrow p_i \leq p_j.
$$

`DRA` 则按相似度排序，为高相关帧给出较高分辨率，同时约束总视觉预算。论文使用 stride constraint $I=28$，并要求各 resolution levels 的总预算满足：

$$
\sum_{i=1}^{L} n_i = N,\qquad
\sum_{i=1}^{L} n_i H_i W_i = P.
$$

紧凑 pipeline：

```text
segment video -> VTR embeddings -> question-only ranking
              -> retrieve candidate pool
              -> MLLM generates plausible options
question + options -> VTR similarities (VQOS)
                   -> AFS: denser sampling on relevant segments
                   -> DRA: higher resolution on relevant frames
                   -> MLLM answers question
```

对于 multiple-choice questions，作者可以直接使用 dataset-provided options (`Ours-PO`)；对于一般问题，则使用模型生成 options (`Ours-GO`)，后者是更公平、也更通用的设置。

## Pipeline Figure

![[assets/pipeline_6998_A_Training_Free_Framework_3_dfa959da.png]]

Caption: Figure 2. Overall Framework. 原始 MLLM 生成 plausible answer options，VTR model 计算 option-conditioned video similarities，随后 `AFS` 与 `DRA` 分别控制采样密度和分辨率，最终交由 MLLM 作答。

Source: PDF page 4 cropped render at 250 DPI; caption and figure identity are directly visible in the PDF.

## Experiments

### Datasets

下表综合 Sec. 4.2 与 Table 12（pp. 8, 17）。除特别注明外，分数为论文报告的 accuracy。

| Dataset | Task | Split | Metric(s) | Videos / QAs | Avg. Duration | Notes |
| --- | --- | --- | --- | ---: | ---: | --- |
| LVBench | Extreme long-video understanding | not reported | Overall | 103 / 1549 | 67.3 min | 最长平均时长 benchmark |
| MLVU | Multi-task long-video understanding | dev | M-Avg | 1122 / 2174 | 12.6 min | 论文报告 `M-Avg` |
| LongVideoBench | Long-context video-language understanding | val | Overall | 735 / 1337 | 7.9 min | 不使用 interleaved subtitles |
| VideoMME | Comprehensive video understanding | not reported | Overall | 900 / 2700 | 17.0 min | 不使用 subtitles |
| VideoEval-Pro | Robust long-video evaluation | not reported | Open, MCQ | 465 / 1289 | 38.2 min | 每个视频超过 10 分钟 |

### Implementation Settings

| Item | Value |
| --- | --- |
| Video segmentation / VTR | 16-second segments; `PE-G/14`; retrieval at 1 FPS |
| LLaVA-Video setting | 7B/72B; max 64 input frames; top-16 segments; sampling levels `{2, 4, 8}`; fixed $384 \times 384$ input, so no DRA |
| Qwen2.5-VL setting | 7B/72B; max 768 frames; top-48 segments; sampling levels `{8, 16, 32}`; DRA budget $20480 \times 28 \times 28$; resolution levels 84 to 644 |
| Option rounds | `LLaVA-Video`: 3 generated-option iterations; `Qwen2.5-VL`: 1 iteration |
| Combined compression run | `Ours + AdaReTake` uses 2048 input frames |

### Main Results

Table 1（p. 7）中 training-free 7B settings 的关键结果如下。`Ours-PO` 利用了 dataset-provided multiple-choice options，因而其 open-ended cell 不可与 `Ours-GO` 直接类比。

| Model / Setting | LVBench Overall | MLVU M-Avg | LongVB Overall | VMME Overall | VEP Open | VEP MCQ | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-Video-7B | 42.0 | 69.3 | 57.4 | 63.2 | 24.2 | 47.6 | 50.6 |
| + AKS | 47.0 | 69.1 | 62.9 | 65.3 | 28.9 | 51.3 | 54.1 |
| + AdaReTake | 49.6 | 70.6 | 59.6 | 64.0 | 27.7 | 53.5 | 54.2 |
| **+ Ours-GO** | **51.3** | **70.3** | **61.0** | **64.8** | **32.7** | **55.3** | **55.9** |
| **+ Ours-PO** | **54.2** | **73.4** | **61.0** | **65.5** | - | **56.9** | **57.3** |
| Qwen2.5-VL-7B | 45.5 | 69.4 | 61.0 | 66.4 | 27.7 | 46.6 | 52.8 |
| + AdaReTake | 51.0 | 72.9 | 61.9 | 67.4 | 30.8 | 53.7 | 56.3 |
| **+ Ours-GO** | **52.7** | **72.3** | **63.4** | **66.7** | **35.0** | **56.9** | **57.8** |
| **+ Ours-GO + AdaReTake** | **55.5** | **74.3** | **63.0** | **69.3** | **35.4** | **57.3** | **59.1** |
| **+ Ours-PO** | **55.5** | **74.1** | **63.3** | **67.9** | - | **57.6** | **58.9** |
| **+ Ours-PO + AdaReTake** | **57.5** | **74.7** | **64.2** | **69.4** | - | **58.2** | **59.9** |

在 72B scale，论文进一步报告 `Ours-GO` 将 `LLaVA-Video-72B` average 从 54.5 提至 **58.1**，将 `Qwen2.5-VL-72B` 从 58.2 提至 **61.4**（Table 1, p. 7）。

### Ablations / Analysis

Table 2（p. 7）显示组件逐步加入时的结果；`LVB-L` 与 `VMME-L` 是各自 long-video subsets，`VEP-M` 是 `VideoEval-Pro` MCQ subset。

| Variant / Setting | LVBench | MLVU | LVB-L | VMME-L | VEP-M | Delta Avg |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-Video-7B | 42.0 | 69.3 | 48.2 | 51.4 | 47.6 | - |
| + top-N frames retrieval | 49.6 | 70.0 | 55.3 | 51.8 | 53.5 | +4.3 |
| + top-k segments uniform sampling | 48.9 | 70.3 | 55.7 | 53.2 | 53.1 | +0.2 |
| + adaptive frame sampling | 50.2 | 70.4 | 56.6 | 53.2 | 54.2 | +0.7 |
| + generated options | 51.3 | 70.3 | 57.1 | 54.0 | 55.3 | +0.7 |
| **+ provided options** | **54.2** | **73.4** | **55.9** | **55.0** | **56.9** | **+1.5** |
| Qwen2.5-VL-7B | 45.5 | 69.4 | 53.7 | 55.6 | 46.6 | - |
| + top-N frames retrieval | 50.3 | 70.0 | 53.5 | 55.4 | 51.4 | +2.0 |
| + top-k segments uniform sampling | 50.1 | 70.3 | 53.9 | 55.1 | 51.1 | +0.0 |
| + adaptive frame sampling | 51.1 | 70.0 | 55.3 | 55.7 | 52.7 | +0.8 |
| + dynamic resolution allocation | 51.9 | 72.1 | 59.0 | 56.0 | 55.9 | +2.1 |
| + generated options | 52.7 | 72.3 | 58.5 | 56.4 | 56.9 | +0.4 |
| **+ provided options** | **55.5** | **74.1** | **58.9** | **56.9** | **57.6** | **+1.2** |

相似度计算的消融（Table 6, p. 10）进一步显示：在 `LLaVA-Video-7B` 上，从 question-only 到 3 rounds generated options，`VideoEval-Pro Open / MCQ / LVBench` 由 `31.0 / 54.2 / 50.2` 上升到 **`32.7 / 55.3 / 51.3`**；直接提供 options 时，`MCQ / LVBench` 为 **`56.9 / 54.2`**。

### Training / Compute

Table 18（p. 22）在 `LVBench` 上报告了 single-GPU runtime，说明精度提升并非免费；下表保留主要对照与可调 VTR 设置。

| Backbone | Method | VTR Model | Retrieval FPS | Accuracy (%) | Runtime (hour) |
| --- | --- | --- | ---: | ---: | ---: |
| LLaVA-Video | Baseline | - | - | 42.0 | 2.4 |
| LLaVA-Video | AdaReTake | - | - | 49.6 | 53.4 |
| LLaVA-Video | Ours-PO | PE-L/14 | 0.5 | **52.7** | 3.9 |
| LLaVA-Video | Ours-PO | PE-G/14 | 1.0 | **54.2** | 29.0 |
| Qwen2.5-VL | Baseline | - | - | 45.5 | 3.6 |
| Qwen2.5-VL | AdaReTake | - | - | 51.0 | 35.9 |
| Qwen2.5-VL | Ours-PO | PE-L/14 | 0.5 | **54.5** | 5.2 |
| Qwen2.5-VL | Ours-PO | PE-G/14 | 1.0 | **55.5** | 30.2 |

## Limitations & Caveats

- 方法偏向定位 query-relevant local evidence，可能遗漏需要完整叙事或跨长时间依赖的 global context。附录 F 在 `VideoEvalPro-MCQ` 上显示，把 global summary 直接拼入 `Ours-PO` 会令准确率从 56.9 降到 52.0；加入少量 uncovered temporal frames（$T=16$）才从 56.9 小幅升至 57.4。
- 生成更多 options 会提高正确答案覆盖率但同时增加 distractors：论文报告 generation rounds 从 1 增至 4 时，`OCA` 从 54.6% 升至 63.8%，而 `MPCO` 从 26.8% 降至 20.0%；实际 accuracy 在 3 rounds 达到峰值后轻微回落（p. 10）。
- `Ours-PO` 依赖测试题中已经给出的候选答案，只适用于 MCQ；用于与通用 open-ended 方法公平比较时，应优先观察 `Ours-GO`。
- 高性能设置的 VTR overhead 较大，例如 `Qwen2.5-VL + Ours-PO + PE-G/14` 在 `LVBench` 上运行时间为 30.2 hours，而 baseline 为 3.6 hours；论文建议以更小 VTR 或更低 FPS 调节成本。
- PDF 对表格文本的抽取基本清晰；本文表格依据 PDF 页 7、10、17 与 22 的可读文本重建，未引入外部 leaderboard 数字。

## Concrete Implementation Ideas

1. 将长视频离线预切为 16-second segments，并缓存 `PE-G/14` 或轻量 `PE-L/14` embeddings；在线每条问题只重新编码 text hypotheses 与做 ranking。
2. 对开放式 QA 实作 `Ours-GO`：先用低成本 question-only retrieval 建 candidate pool，再对检索到的 frames 生成 options，最后以 `question + option` 重新排序，避免对全视频反复调用 MLLM。
3. 在支持 variable-resolution input 的 backbone 中，将 `AFS` 与 `DRA` 共同实现为 budget allocator；在 fixed-resolution backbone 中只启用 `AFS`，与论文的 LLaVA-Video 设置保持一致。
4. 为故事概括或 holistic reasoning 类问题添加轻量 temporal-coverage fallback：保留若干未覆盖区间的中心帧，再移除最低 `VQOS` 帧，以测试附录 F 的视觉全局补充策略。
5. 若部署在 streaming video 场景，可按 1 FPS 增量缓存 segment embeddings；作者指出 `PE-G/14` 的每帧 embedding 时间约为 0.26 seconds，低于 1-second frame interval（p. 24）。

## Open Questions / Follow-ups

- `VQOS` 的最大值聚合是否会被一个语义近似但事实错误的 option 主导？使用 calibrated weighting、top-$r$ aggregation 或 uncertainty estimation 是否更稳健？
- 对需要 global narrative 的 benchmark，局部检索与 sparse global frames 的最优预算如何随视频长度变化？
- `SigLIP-LLaVA` 复用原始视觉 encoder pooling head 后已取得较强效果；是否可为更多 MLLM 设计无需训练的 compatible pooling strategy，从而避免额外 VTR 成本？
- 论文对最新、更大 context window 的 MLLM 是否仍能保持相同收益，需要在统一 runtime/token budget 下复验。

## Citation

Wu, Z., Wang, X., Huang, L., Xu, T., & Peng, P. (2026). *A Training-Free Framework for Long Video Understanding via Video-Query-Options Similarity*. Published as a conference paper at ICLR 2026.

- PDF asset: [[assets/paper_6998_A_Training_Free_Framework_3_dfa959da.pdf]]
- Code: https://github.com/wuzhirong520/VTR-VLM
