---
title: VideoRouter
authors:
  - Kuanwei Lin
  - Wenhao Zhang
  - Ge Li
conference:
year: 2026
arxiv_url: https://arxiv.org/abs/2605.05848
pdf_link: "[[assets/paper_2605.05848.pdf]]"
cover: "[[assets/pipeline_2605.05848.png]]"
updated: 2026-05-12
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority: "1"
rating: "5"
topics:
  - Video Understanding
code: ""
---

## TL;DR

- VideoRouter 把 long-video MLLM 的 visual-token compression 重新表述为 **budgeted evidence allocation**：在固定视觉 token 预算下，决定 token 应该用于广覆盖还是集中保留关键帧细节。
- 方法由两个 router 组成：Semantic Router 根据 query 预测 Global / Fragment allocation policy，Image Router 复用早期 LLM 层对每帧做 frame-query relevance scoring。
- 在 Fragment policy 下，关键帧保留高分辨率 token，非关键帧做更激进 pooling；在 Global policy 下，模型保持更均匀的时序覆盖。
- 作者构建 Video-QTR-10K 和 Video-FLR-200K，分别监督 allocation-policy prediction 和 frame-level relevance prediction。
- 在 Video-MME、LongVideoBench、MLVU、LVBench、EgoSchema 等 long-video benchmarks 上，VideoRouter 在相近或更低 token 预算下提升 InternVL3 / Qwen2.5-VL 的表现，并报告最高 67.9% token reduction。

VideoRouter 是白盒、训练式、插入式改造 VLM。

它的改动主要有三层：

1. 在 VLM 外面/旁边加了 Router 模块
   它基于 InternVL 3 做 backbone，然后加入 Semantic Router 和 Image Router。论文说模型结构由 InternVL 3 backbone 和 dual routers 组成；并且会复用早期 language layers 作为 router feature extractor。
2. 需要访问 VLM 内部 hidden states，不是黑盒调用
   它把前 4 层 decoder 复制成一个 shadow stack，用来计算 router features。这个设计说明它不是简单地“先选帧，再把帧喂给 VLM”，而是需要改推理图、接入模型内部层。
3. 训练阶段会动 LLM backbone
   Stage 1/2 主要训练 router，冻结 backbone；但是 Stage 3 明确写了：冻结 vision encoder，unfreeze LLM backbone，做 joint fine-tuning。也就是说最后不是 training-free，LLM 部分参数会被微调。

## Key Contributions

1. **Budgeted Evidence Allocation**：把长视频压缩从“统一降采样”改成显式 token budget 下的 evidence allocation，区分 broad temporal coverage 与 high-resolution evidence preservation。
2. **Dual-Router Architecture**：Semantic Router 做 query-level policy selection；Image Router 做 frame-level relevance estimation，并复用 backbone 早期 language layers 作为轻量特征抽取器。
3. **Routing Supervision**：提出 Video-QTR-10K 和 Video-FLR-200K，用专门构造的数据监督 router，而不是直接给 benchmark answer knowledge。
4. **Controlled Efficiency Evidence**：在相同 64 sampled frames 与 $B_{\mathrm{img}}=12{,}288$ 预算下，对比 Uniform Pooling、CLIP Relevance Pooling、Data FT 等 baseline，证明收益主要来自 query-conditioned allocation。

## Method

VideoRouter 的输入是 video $V=\{f_t\}_{t=1}^{T}$ 和 question $q$，目标是在固定上下文窗口中最小化 visual-token cost，同时尽量保留 answer quality。整体流程是先决定“预算策略”，再决定“哪些帧值得高保真”。

**Backbone and feature extractor**：方法基于 InternVL3-8B。每一帧经 vision encoder 和 projection 得到 visual token sequence $Z_t$。为了避免额外引入重模型，VideoRouter 复制前 4 个 decoder layers 作为 shadow stack $\mathcal{E}_{1:4}$：

$$
H_q = \mathcal{E}_{1:4}(\mathrm{Emb}(q)), \qquad
H_{v,q}^{(t)} = \mathcal{E}_{1:4}([Z_t;\mathrm{Emb}(q)])
$$

**Semantic Router**：只看 question feature $H_q$，通过 pooling + Strategy MLP 预测 allocation policy：

$$
p_s = g_s\!\left(\mathrm{Pooling}(H_q)\right), \qquad
\hat{y}_s=\arg\max_c p_s(c), \qquad y_s\in\{0,1\}
$$

其中 $y_s=0$ 表示 Global policy，倾向 broad temporal coverage；$y_s=1$ 表示 Fragment policy，倾向把预算集中到证据帧。

**Image Router**：当 Semantic Router 选择 Fragment policy 时，对每帧与 query 的融合特征打分：

$$
p_t = g_v\!\left(H_{v,q}^{(t)}\right), \qquad
\hat{y}_t=\mathbb{I}[p_t>0.5], \qquad y_t\in\{0,1\}
$$

$y_t=1$ 表示 Relevant frame，应保留高视觉保真；$y_t=0$ 表示 Irrelevant frame，可做 aggressive compression。

**Inference allocation**：

1. 先计算可用视觉预算：

$$
B_{\mathrm{img}}=L_{\mathrm{max}}-L_{\mathrm{text}}-L_{\mathrm{gen}}-\epsilon
$$

2. 若 $\hat{y}_s=0$，采用 Global policy：所有帧使用 uniform spatial pooling，默认 $s_g=2$；若仍超预算，再做 uniform temporal subsampling。
3. 若 $\hat{y}_s=1$，采用 Fragment policy：Relevant frames 使用高保真 scale $s_1=1$，Irrelevant frames 使用 aggressive scale $s_0=4$。
4. 分配优先级是：先保证 critical frames，再保留一部分 background frames；极端预算不足时，优先丢弃 low-priority frames，若 critical frames 也装不下，则在 critical set 中 uniform sample。
5. 最终得到 $Z_{\mathrm{final}}$，替换 prompt 中的 image placeholders 后交给 LLM 做 autoregressive decoding。

**Training objective**：三阶段训练。Stage 1 训练 Image Router 的 binary frame-relevance loss；Stage 2 训练 Semantic Router 的 cross-entropy loss；Stage 3 联合对齐 compressed visual sequence 与 answer generation：

$$
\mathcal{L}=\mathcal{L}_{\mathrm{LM}}+\lambda_s\mathcal{L}_{\mathrm{sem}}+\lambda_v\mathcal{L}_{\mathrm{img}}, \qquad \lambda_s=\lambda_v=0.01
$$

## Pipeline Figure

![[assets/pipeline_2605.05848.png]]

Caption: Overview of the VideoRouter framework. The Semantic Router predicts the dominant allocation policy and selects either broad Uniform Compression or Adaptive Compression. Under Adaptive Compression, the Image Router's frame-level scores drive token allocation dynamically.

Source: TeX includegraphics from `sections/03_method.tex`, asset `figures/method.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| Video-FLR-200K | Image Router supervision | 200,664 QA instances | Frame relevance label agreement / router validation | 从 LLaVA-178K training split 的视觉材料构造，目标是标注回答 query 所需的 minimal sufficient frames。 |
| Video-QTR-10K | Semantic Router supervision | 10,000 video-query pairs | Allocation-policy label agreement / router validation | 通过 Global vs Fragment forced-policy A/B probing 为 query category 赋 allocation policy label。 |
| Video-MME | Long-video QA / video understanding | Evaluation benchmark | Accuracy (%) | 包含 short / medium / long videos，论文报告 Long 与 Overall。 |
| LongVideoBench | Extended temporal reasoning | Evaluation benchmark | Accuracy (%) | 重点测试 long-form temporal reasoning。 |
| MLVU | Multi-task long-video understanding | Evaluation benchmark | Accuracy (%) | 主实验与 controlled comparison 都报告。 |
| LVBench | Long-video understanding | Evaluation benchmark | Accuracy (%) | 主表报告。 |
| EgoSchema | Fine-grained spatiotemporal understanding | Evaluation benchmark | Accuracy (%) | 主表与 ablation 部分报告。 |

### Main Results

下面的主表混合了 prior work 原始设置与作者自己的 VideoRouter adaptation；因此更适合看整体位置。真正控制变量的 fair comparison 在下一张表。

| Method / Group | Video-MME Long | Video-MME Overall | LongVideoBench | MLVU | LVBench | EgoSchema |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Average Duration | 2386s | 1010s | 473s | 651s | 4101s | 180s |
| *Proprietary MLLMs* |  |  |  |  |  |  |
| GPT-4V | 53.5 | 59.9 | 59.1 | 49.2 | - | 55.6 |
| GPT-4o | 65.3 | 71.9 | 66.7 | 64.6 | 30.8 | 72.2 |
| *Open-source MLLMs* |  |  |  |  |  |  |
| Oryx-1.5 | - | 58.8 | 56.3 | 67.5 | - | - |
| MiniCPM-v2.6 | 51.8 | 60.9 | 54.9 | 37.3 | - | - |
| mPLUG-Owl3 | 50.1 | 59.3 | 52.1 | 63.7 | - | - |
| NVILA | 54.8 | 64.2 | - | 70.1 | - | - |
| LLaVA-Video | - | 63.3 | 58.2 | 70.8 | 41.5 | 57.3 |
| Video-XL | 49.2 | 55.5 | 49.5 | 64.9 | - | - |
| VideoLLaMA2 | - | 47.9 | - | 48.5 | - | 51.7 |
| Video-CCAM | 46.7 | 53.2 | - | 58.5 | - | - |
| Kangaroo | 46.7 | 56.0 | 54.8 | 61.0 | 39.4 | 62.7 |
| LongVA | 46.2 | 52.6 | - | 56.3 | - | - |
| LongVILA | - | 60.1 | 57.1 | - | - | - |
| LongVU | - | 60.6 | - | 65.4 | - | - |
| *Compression Methods* |  |  |  |  |  |  |
| LLaVA-OneVision | - | 58.2 | 56.5 | 64.7 | - | 60.1 |
| + FastV | - | 57.3 | - | - | - | - |
| + PruMerge | - | 52.9 | - | - | - | - |
| + DyCoke | - | 59.5 | - | - | - | - |
| + DyToK | 49.0 | 59.8 | 58.3 | 49.7 | - | - |
| + QTSplus | - | 52.9 | - | 60.9 | 36.7 | - |
| + DToMA | - | 65.0 | 59.6 | 71.7 | - | 59.3 |
| Qwen2.5-VL | - | 65.1 | 56.0 | 70.2 | 45.3 | 65.0 |
| + DIG | 55.3 | - | 61.4 | 70.7 | - | - |
| + FastV | - | 55.7 | 53.2 | 36.8 | - | - |
| + DyToK | - | 60.8 | 57.9 | 44.1 | - | - |
| + **VideoRouter** | 55.8 | 66.0 | 60.4 | 71.0 | 46.0 | 65.7 |
| InternVL3 | - | 66.3 | 58.8 | 71.4 | - | - |
| InternVL3* | 54.7 | 64.3 | 56.9 | 70.2 | 41.3 | 62.7 |
| **VideoRouter (Ours)** | 56.0 | 66.5 | 61.9 | 72.1 | 45.5 | 65.1 |

### Controlled InternVL3-8B Results

所有 budgeted rows 都从相同 64 sampled frames 出发，并共享最大视觉 token 预算 $B_{\mathrm{img}}=12{,}288$。这张表最能支撑“dynamic allocation 本身有效”的 claim。

| Method | Frames | Visual Tokens | Video-MME | LongVideoBench | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- |
| InternVL3 Dense | 64 | 16,384 | 66.3 | 58.8 | 71.4 |
| InternVL3 Budget | ~38 | 9,528 | 64.3 | 56.9 | 70.2 |
| Uniform Pooling | 64 | 8,192 | 65.4 | 58.9 | 70.6 |
| CLIP Relevance Pooling | 64 | 7,936 | 65.8 | 59.7 | 71.0 |
| Data FT + Uniform Pooling | 64 | 8,192 | 65.2 | 58.1 | 70.7 |
| **VideoRouter** | **64** | **7,748** | **66.5** | **61.9** | **72.1** |

### Cross-Backbone Qwen2.5-VL Results

| Method | Frames | Visual Tokens | Video-MME | LongVideoBench | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2.5-VL Dense | 64 | 16,384 | 65.5 | 56.8 | 70.5 |
| Qwen2.5-VL Budget | 64 | 9,680 | 65.1 | 56.0 | 70.2 |
| Uniform Pooling | 64 | 8,192 | 65.3 | 56.9 | 70.3 |
| CLIP Relevance Pooling | 64 | 7,936 | 65.6 | 57.6 | 70.7 |
| Data FT + Uniform Pooling | 64 | 8,192 | 65.4 | 56.6 | 70.6 |
| **Qwen2.5-VL + VideoRouter** | **64** | **7,910** | **66.0** | **60.4** | **71.0** |

### Ablations / Analysis

**Module Effectiveness**：去掉 Image Router 会削弱 fine-grained redundancy filtering；去掉 Semantic Router 会把 adaptive allocation 过度用于 holistic queries。

| Model | MME Long | MME Overall | LVB | MLVU |
| ---- | ---- | ---- | ---- | ---- |
| InternVL3* | 54.7 | 64.3 | 56.9 | 70.2 |
| w/o Image Router | 55.1 | 65.4 | 58.9 | 70.6 |
| w/o Semantic Router | 55.5 | 65.6 | 61.2 | 69.8 |
| **VideoRouter** | **56.0** | **66.5** | **61.9** | **72.1** |

**Training Strategy**：router pre-training 与 joint fine-tuning 都有贡献；直接跳过其中一个阶段会影响最终对齐。

| Training Strategy | MME Long | MME Overall | LVB | Ego |
| ---- | ---- | ---- | ---- | ---- |
| InternVL3* | 54.7 | 64.3 | 56.9 | 62.7 |
| w/o Joint FT (Stage 3) | 54.5 | 64.9 | 57.1 | 64.4 |
| w/o Pre-train (Stage 1 & 2) | 55.1 | 65.4 | 60.2 | 64.6 |
| **VideoRouter (Full)** | **56.0** | **66.5** | **61.9** | **65.1** |

**Budget Sensitivity on LongVideoBench**：64 frames 在极低预算更稳；预算变宽后，128 frames 因 temporal coverage 更好而反超。

| Method | 4K | 8K | 12K | 16K | 24K |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Uniform Pooling (64f) | 55.8 | 58.0 | 58.9 | 60.0 | 60.7 |
| CLIP Relevance Pooling (64f) | 56.9 | 59.2 | 60.3 | 61.1 | 61.5 |
| **VideoRouter (64f)** | **58.4** | **61.3** | 61.9 | 62.6 | 62.6 |
| **VideoRouter (128f)** | 54.9 | 59.8 | **62.4** | **63.4** | **63.8** |

**Latency / Memory Breakdown**：router 有额外 0.5s shadow-stack forward + heads，但减少 LLM prefill 后总体 TTFT 与 peak memory 都下降。

| Method | Visual Tokens | Router (s) | Vision+Compress (s) | LLM Prefill (s) | TTFT (s) | Peak Mem. (GB) |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| InternVL3 Dense | 16,384 | -- | 1.7 | 6.7 | 8.4 | 36.5 |
| InternVL3 Budget | 9,528 | -- | 1.1 | 3.9 | 5.0 | 25.8 |
| Uniform Pooling | 8,192 | -- | 1.2 | 3.6 | 4.8 | 24.6 |
| CLIP Relevance Pooling | 7,936 | 0.2 | 1.3 | 3.4 | 4.9 | 24.3 |
| **VideoRouter ($s=2,4$)** | **7,748** | **0.5** | **1.2** | **3.0** | **4.7** | **23.9** |
| **VideoRouter ($s=4,8$)** | **5,262** | **0.5** | **1.2** | **2.5** | **4.2** | **22.4** |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Backbone | InternVL3-8B; Qwen2.5-VL adaptation in appendix |
| Input frame size | $448\times448$ |
| Controlled input frames | 64 sampled frames; budgeted baseline dynamically samples ~38 frames |
| Max visual-token budget | $B_{\mathrm{img}}=12{,}288$ in controlled comparisons |
| Safety margin | $\epsilon=100$ tokens |
| Hardware | 4 NVIDIA H20 GPUs |
| Distributed training | DeepSpeed ZeRO-2 |
| Stage 1 | Train Image Router on Video-FLR-200K for 5 epochs; LR $5\times10^{-5}$; per-device batch size 16; gradient accumulation 4 |
| Stage 2 | Train Semantic Router on Video-QTR-10K for 2 epochs; LR $1\times10^{-5}$; per-device batch size 4; gradient accumulation 4 |
| Stage 3 | Joint fine-tuning for 1 epoch; LR $5\times10^{-6}$; per-device batch size 4; gradient accumulation 4 |
| Joint loss weights | $\lambda_s=\lambda_v=0.01$ |
| Default router depth | $k=4$ early LLM layers; Image Router accuracy 83.4% on 2,500 samples with lower overhead than 6/8 layers |
| Semantic Router validation | 98.2% accuracy on 2,350 test samples |
| Label audit | 94.0% agreement for allocation-policy labels; 88.4% agreement for frame-relevance labels |
| Default pooling scales | Global $s_g=2$; Fragment high-fidelity $s_1=1$ and irrelevant-frame $s_0=4$ |

## Limitations & Caveats

- 主要实验围绕 InternVL3-8B，虽然有 Qwen2.5-VL adaptation，但还不能证明对所有 Video-LLM backbone 都稳定有效。
- 方法依赖 offline sampled frames；真实流式视频、稀有事件、长尾场景下的 frame sampling 与 routing 仍可能成为瓶颈。
- Video-FLR-200K / Video-QTR-10K 是 VLM/LLM-assisted construction，虽然有 consistency、logical-coherence、counterfactual-necessity filters 和人工 audit，仍可能保留 teacher bias 或 label noise。
- 论文报告 deterministic benchmark accuracy，没有 error bars 或多次训练的 statistical significance tests。
- TTFT 统计是在 video loading 之后，不能直接代表端到端系统里视频解码、I/O、缓存 miss 的完整延迟。
- 源码 checklist 中说明当前 anonymized submission 尚未公开 code / generated datasets；复现仍依赖论文中的协议与未来 release。

## Concrete Implementation Ideas

1. 在已有 long-video QA pipeline 中加入一个 lightweight Semantic Router：先把 query 分成 Global / Fragment 两类，再选择 uniform coverage 或 adaptive allocation。
2. 把预算计算显式化：用 $B_{\mathrm{img}}=L_{\mathrm{max}}-L_{\mathrm{text}}-L_{\mathrm{gen}}-\epsilon$ 控制 visual tokens，并在日志里记录 actual visual tokens、TTFT、peak memory。
3. 对业务域视频构造小规模 frame-relevance supervision：用 dense caption + reverse-QA + counterfactual masking，先训练或校准 Image Router。
4. 给 router 加 confidence fallback：Semantic Router 低置信度时默认 Global policy，避免对 holistic query 过度集中少数帧。
5. 做 64f / 128f / budget sweep，而不是只比较单一 token 预算；这篇论文的结果提示低预算和高预算下最优采样深度可能不同。

## Open Questions / Follow-ups

- VideoRouter 在 InternVL3、Qwen2.5-VL 之外的 backbone 上是否仍然能复用“前 4 层 shadow stack”这个选择？
- Mixed queries 同时需要 broad temporal context 和 localized evidence，Semantic Router 的二分类 policy 是否足够，还是需要多策略或连续预算分配？
- Frame relevance labels 中相邻帧近似重复会带来标注歧义；实际部署时是否需要 temporal smoothing 或 segment-level routing？
- 如果公开 code / generated routing datasets，license、数据来源、自动生成 QA 的质量报告需要怎样配套发布？
- 能否把 Image Router 的 frame score 与现有 retrieval / keyframe selection 模块融合，减少额外 shadow-stack routing cost？

## Citation

Lin, Kuanwei; Zhang, Wenhao; Li, Ge. “VideoRouter: Query-Adaptive Dual Routing for Efficient Long-Video Understanding.” arXiv:2605.05848, 2026.

```bibtex
@misc{lin2026videorouter,
  title        = {VideoRouter: Query-Adaptive Dual Routing for Efficient Long-Video Understanding},
  author       = {Kuanwei Lin and Wenhao Zhang and Ge Li},
  year         = {2026},
  eprint       = {2605.05848},
  archivePrefix= {arXiv},
  primaryClass = {cs.CV},
  doi          = {10.48550/arXiv.2605.05848},
  url          = {https://arxiv.org/abs/2605.05848}
}
```
