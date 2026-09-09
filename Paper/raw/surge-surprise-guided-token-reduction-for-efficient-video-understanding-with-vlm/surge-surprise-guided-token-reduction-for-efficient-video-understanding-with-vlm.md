---
title: SURGE(token)
authors:
  - Chong Tang
  - Sannara Ek
  - Dirk Koch
  - Robert Mullins
  - Alex Weddell
  - Jagmohan Chauhan
conference: ICLR 2026
year: 2026
paper_url: ""
source_pdf: /Users/yifan/Downloads/593_SURGE_Surprise_Guided_Toke.pdf
pdf_link: "[[assets/paper_593_SURGE_Surprise_Guided_Toke_fa9d91a7.pdf]]"
cover: "[[_assets/images/pipeline_593_SURGE_Surprise_Guided_Toke_fa9d91a7.png]]"
updated: 2026-05-26
tags:
  - paper/pdf
  - video-llm
  - long-video
  - question-aware
  - token-pruning
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/BarryTang22/SURGE.git
---

## TL;DR

- SURGE 用 token 在时间上的可预测性来决定保留哪些视觉 token：不能由近期历史预测的 patch 被视为高 `surprise`，从而优先送入 LLM。
- 方法是 training-free 且 backbone-agnostic 的：在 vision encoder 输出的 patch embeddings 上计算 surprise，不需要重训，也不依赖内部 attention map。
- 在默认 $\rho=0.25$ 设置下，论文报告视觉/文本总 token 约缩至原来的 $26\%$--$27\%$；加入 CLIP Top-5 event focusing 的 `SURGE*` 约为 $14\%$--$16\%$，相当于最高约 $7\times$ token reduction。
- 在 Qwen2.5-VL 的 Video-MME profiling 中，$\rho=0.25$ 的 prefill FLOPs/latency 分别下降 $86\%/79\%$；主要代价是 `SURGE*` 的额外 CLIP 推理以及对 $K$ 和 query wording 的敏感性。

## Key Contributions

- 提出一个基于 prediction error 的视频 VLM token pruning 标准，将 temporal novelty 直接转化为可执行的 spatio-temporal mask。
- 通过 affine global drift detrending 与 running variance normalization，压制 camera pan 等整体运动导致的伪 surprise。
- 将 surprise curve 的 peak/event segmentation 与可选的 CLIP query-aware focusing 组合，以更少 token 覆盖与问题有关的新事件。
- 在 InternVL-3.5-VL、Video-LLaVA-Qwen 与 Qwen2.5-VL 上测试五个视频理解 benchmark，并展示与 AKS keyframe selection 的互补性。

## Method

1. **Token dynamics.** 对第 $t$ 帧的 spatial token $z_t^{(j)}$，SURGE 假设平滑视频在 token space 中近似满足 constant-velocity dynamics，并用近期位移作因果预测：

   $$
   \hat{z}_t^{(j)} = z_{t-1}^{(j)} + \tilde{\delta}_{t-1}^{(j)}.
   $$

2. **Global drift correction.** 以 token 的归一化空间坐标 $(x_j,y_j)$ 拟合 affine displacement field $c_0+c_xx_j+c_yy_j$，再从 token displacement 中减去该场。这样 camera motion 或 scene-level shift 不会轻易被误判为事件。

3. **Surprise scoring.** 预测残差经运行方差归一化，形成每个 token 的 novelty score：

   $$
   e_t^{(j)} = z_t^{(j)} - \hat{z}_t^{(j)}, \qquad
   s_t^{(j)} = \frac{\lVert e_t^{(j)} \rVert_2^2}{\sigma_t^{2,(j)}+\epsilon}.
   $$

4. **Adaptive masking.** 在整段 clip 或 streaming prefix 的 score 上求 global percentile threshold，仅保留 top-$\rho$ 的 token；special tokens 始终保留。默认设置为 $\rho=0.25$。

5. **Event focusing.** 将每个 temporal unit 中通过阈值的 token 数汇聚成 surprise curve，用 EMA 平滑并以 peak 划分 event intervals。`SURGE*` 进一步使用 CLIP `ViT-B/32` 对 peak frames 与 query 的相关性排序，仅聚焦 Top-$K$ events；默认 $K=5$。

6. **Insertion point.** Surprise 在 projection 前的 raw patch embeddings 上计算，mask 则作用于送往 language model 的视觉 token。因此它主要减少 multimodal LLM 的 prefill、attention 与 KV-cache 负担，而不消除已有 vision encoder 的前向计算。

## Pipeline Figure

![[_assets/images/pipeline_593_SURGE_Surprise_Guided_Toke_fa9d91a7.png]]

Caption: SURGE 先以 constant-velocity predictor 生成 token surprise score，经 surprise curve 检测 key events；可选的 CLIP query-aware focusing 选择相关事件，只将高 surprise token 送入 multimodal LLM。

Source: PDF page 4, Figure 2 embedded image (1677 x 822 px).

## Experiments

论文使用 `VLMEvalKit` 进行 inference-only evaluation；默认参数为 $\rho=0.25$、EMA $\gamma=0.9$、peak separation $\Delta=8$、`SURGE*` 的 CLIP Top-$K=5$。实验使用 1--8 张 NVIDIA A100 80GB GPU；附录称结果在 5 个 random seeds 上平均。

### Datasets / Benchmarks

| Dataset | Task | Split / Setting | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME (V-MME) | short-to-long video QA | 64-frame main table; also efficiency profiling | reported benchmark score | 用于 FLOPs/latency 分析 |
| MLVU | long-video multi-task understanding | main and long-context evaluation | M-Avg / G-Avg | 包括 needle QA、grounding、summarization |
| MMBench-Video (MMB-V) | multi-shot compositional/temporal QA | main and ablation | reported score | 对 token loss 敏感 |
| TempCompass (T-Compass) | fine-grained temporal reasoning | main and ablation | reported score | 测试 order/speed/duration |
| LongVideoBench (LVB) | very-long-video retrieval/reasoning | main and trade-off | reported score | 强调 cross-event reasoning |

### Main Results

PDF Table 1（page 7，64 frames）中的核心 SURGE 行如下；`Tokens` 是每样本平均 visual + fixed text token 数。下表的粗体用于标出论文方法行的已报告数值。

| Model / Method | Tokens | V-MME | MLVU (M / G) | MMB-V | T-Compass | LVB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| InternVL-3.5-VL (8B) | 17,124 | 66.0 | 71.7 / 3.44 | 1.54 | 68.9 | 61.3 |
| **+ SURGE** | **4,674** | **64.9** | **71.5 / 3.45** | **1.57** | **69.0** | **61.7** |
| **+ SURGE*** | **2,932** | **65.8** | **71.7 / 3.69** | **1.57** | **69.7** | **62.2** |
| Video-LLaVA-Qwen (7B) | 12,246 | 63.4 | 72.9 / 3.30 | 1.53 | 66.9 | 58.3 |
| **+ SURGE** | **3,324** | **63.1** | **72.9 / 3.30** | **1.53** | **67.0** | **59.1** |
| **+ SURGE*** | **1,884** | **64.5** | **72.7 / 3.20** | **1.60** | **66.9** | **61.9** |
| Qwen2.5-VL (7B) | 41,590 | 62.2 | 65.8 / 4.26 | 1.60 | 70.5 | 60.0 |
| **+ SURGE** | **10,992** | **60.9** | **65.7 / 4.26** | **1.72** | **70.5** | **59.4** |
| **+ SURGE*** | **5,207** | **62.7** | **66.1 / 4.24** | **1.70** | **67.7** | **61.3** |

论文还在 Table 1 中报告与 `AKS` 的组合：例如 InternVL-3.5-VL 的 `AKS w/ SURGE*` 使用 2,390 tokens，并得到 V-MME 66.2 与 MLVU 72.3 / 3.58，表明 frame selection 与 within-frame token pruning 可以组合。

### Token-Accuracy Trade-off

以下为 PDF Table 2（page 8）中 Qwen2.5-VL 的代表性行。该表是 pruning-budget sweep，和 Table 1 的 64-frame 汇总应按各自表内 protocol 解读。

| Method | $\rho$ | V-MME | MLVU (M / G) | MMB-V | T-Compass | LVB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL (7B) | 1.00 | 62.2 | 65.8 / 4.26 | 1.60 | 70.5 | 60.0 |
| **+ SURGE +/-0.7%** | **0.50** | **62.0** | **65.8 / 4.26** | **1.66** | **72.3** | **59.7** |
| **+ SURGE +/-0.4%** | **0.25** | **60.9** | **65.7 / 4.26** | **1.72** | **70.5** | **59.4** |
| + Random +/-13.2% | 0.25 | 53.6 | 55.9 / 3.32 | 0.96 | 57.4 | 49.7 |
| **+ SURGE +/-0.7%** | **0.10** | **60.3** | **65.8 / 4.22** | **1.58** | **70.2** | **58.6** |
| **+ SURGE +/-1.0%** | **0.01** | **58.7** | **65.8 / 4.22** | **1.55** | **70.2** | **55.7** |

### CLIP Event Focusing

PDF Table 3（page 8）显示极小的 $K$ 会丢失事件覆盖；当 $K=7$ 或 $10$ 时，`SURGE*` 基本恢复或超过 full-token baseline。

| Method | $K$ | V-MME | MLVU (M / G) | MMB-V | T-Compass | LVB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL (7B) | - | 62.2 | 65.8 / 4.26 | 1.60 | 70.5 | 60.0 |
| **+ SURGE** | **-** | **60.9** | **65.7 / 4.26** | **1.72** | **70.5** | **59.4** |
| **+ SURGE*** | **1** | **51.7** | **37.9 / 2.51** | **1.09** | **23.9** | **40.1** |
| **+ SURGE*** | **5** | **62.0** | **66.1 / 4.24** | **1.70** | **67.7** | **56.3** |
| **+ SURGE*** | **7** | **62.3** | **66.8 / 4.30** | **1.65** | **70.5** | **60.2** |
| **+ SURGE*** | **10** | **62.7** | **66.8 / 4.26** | **1.71** | **71.0** | **60.2** |

### Ablations / Analysis

PDF Table 4（page 10）在 Qwen2.5-VL、$\rho=0.25$ 的固定预算下移除单个组件；移除 temporal predictor 的退化最大。

| Variant / Setting | MLVU (M / G) | T-Compass | MMB-V | Notes |
| --- | ---: | ---: | ---: | --- |
| **SURGE (full)** | **65.7 / 4.26** | **70.5** | **1.72** | full proposed method |
| w/o drift detrend (Eq. 4) | 64.9 / 4.18 | 69.4 | 1.65 | 保留 global mask 与 event segmentation |
| w/o variance norm (Eq. 5) | 65.1 / 4.22 | 69.7 | 1.70 | 保留 global mask 与 event segmentation |
| w/o temporal predictor (frame-diff only, Eq. 3) | 63.4 / 4.17 | 66.9 | 1.55 | 最大跌幅 |

### Efficiency / Compute

| Item | Value |
| --- | --- |
| Hardware | 1--8 x NVIDIA A100 80GB |
| Default inference setting | $\rho=0.25$, $\gamma=0.9$, $\Delta=8$, CLIP Top-$K=5$ |
| Qwen2.5-VL, Video-MME, $\rho=0.25$ | prefill FLOPs $-86\%$; prefill latency $-79\%$; generation FLOPs $-38\%$; generation latency $-14\%$ |
| Qwen2.5-VL, Video-MME, $\rho=0.01$ | prefill cost reduction $>98\%$; generation FLOPs approximately halved |
| `SURGE*` CLIP overhead | about 0.63--1.0 TFLOPs / 1027--1891 ms per query for 5--8 peaks |
| Long-context observation on MLVU | baseline exceeds A100 80GB VRAM beyond about 230 frames; SURGE/SURGE* run to 1024/3600 frames, with accuracy degrading when truncation dominates |

## Limitations & Caveats

- 论文明确指出 `SURGE*` 需要额外 CLIP pass，并且对 $K$ 与 query phrasing 敏感；Table 3 中 $K=1$ 的明显崩落说明 relevance-only focusing 会牺牲覆盖率。
- SURGE 在 vision encoder 产出 patch embeddings 后才剪枝，因此主要节约 multimodal LLM 阶段的 token、prefill 和 KV-cache 成本；它不是降低视觉编码器本身成本的方案。
- 极长上下文实验虽然证明可执行长度提升，但 1024 与 3600 frame 的性能下降受到截断影响，不能解释为无损扩展。
- Table 1 明确限定 64 frames，而 Table 2--3 是 Qwen2.5-VL 的 budget/focusing 分析；同名配置在不同表中的数字不应脱离相应 protocol 直接混用。

## Concrete Implementation Ideas

1. 在现有 video VLM inference wrapper 中先实现 `SurpriseMasker`：缓存最近两个 frame/chunk 的 pre-projection patch embeddings，完成 affine detrend、variance EMA 与 top-$\rho$ mask。
2. 将 profiling 拆成 vision encoder、multimodal prefill、decode 三段，分别测量 latency、peak VRAM 与 KV-cache 大小，以验证收益主要出现在哪个阶段。
3. 先上线无需 CLIP 的 SURGE，并用验证集按 memory budget 调整 $\rho$；仅在 long-video retrieval 类 query 中启用 `SURGE*`，避免无条件承担 CLIP overhead。
4. 对 streaming video 使用 observed-prefix quantile 与滑动事件缓冲区，检查 offline percentile selection 在因果部署中的性能变化。

## Open Questions / Follow-ups

- Surprise threshold 从完整 clip 的 global percentile 改为在线 quantile estimator 后，准确率与 temporal stability 会如何变化？
- 对 camera cut、字幕 overlay、快速 zoom 等强视觉变化，high surprise 是否总对应回答所需的信息，还是需要额外 semantic guardrail？
- `SURGE*` 能否以已有 VLM embedding 替代 CLIP relevance scorer，从而降低额外 latency 并减少 query wording sensitivity？
- 与 quantization、KV-cache compression 或 frame-level selector 组合时，收益是否近似可叠加，还是会出现 evidence coverage 的临界点？

## Citation

Tang, Chong, Sannara Ek, Dirk Koch, Robert Mullins, Alex Weddell, and Jagmohan Chauhan. "SURGE: Surprise-Guided Token Reduction for Efficient Video Understanding with VLMs." International Conference on Learning Representations (ICLR), 2026. Code: https://github.com/BarryTang22/SURGE.git

