---
title: (token)DyToK
authors:
  - Yulin Li
  - Haokun Gui
  - Ziyang Fan
  - Junjie Wang
  - Bin Kang
  - Bin Chen
  - Zhuotao Tian
conference: NeurIPS 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2512.06866
pdf_link: "[[assets/paper_2512.06866.pdf]]"
cover: "[[assets/pipeline_2512.06866.png]]"
updated: 2026-05-31
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/yu-lin-li/DyToK
---

## TL;DR

- 论文提出 **DyToK**：一个 training-free 的 video token compression 方法，用 VLLM 自身 attention 中的 query-conditioned keyframe prior 来动态分配每帧 token budget。
- 核心观察是：即使 VLLM 回答错误，它的 attention 仍常能定位到与问题相关的 keyframes；并且更深层 attention 比浅层更适合作为 frame importance prior。
- 为避免用主模型深层 attention 带来的重复计算，DyToK 使用同架构家族的 lightweight assistant model 提取 temporal importance，再把 token budget 按帧动态分配给现有 pruning 方法。
- 方法可插到 VisionZip、FastV、DyCoke 等 encoder feature-based 或 LLM attention-based compression pipelines 中；主实验显示在 aggressive compression 下收益更明显。
- 在 LLaVA-OneVision 32-frame 设置中，DyToK + VisionZip 在 10% token retention 下平均分为 48.8，达到 vanilla 的 90.2%，相比 VisionZip 提升 18.9 个相对百分点。
- 主要代价是需要一个额外 assistant model；作者也指出未来需要研究如何避免这个额外模型。

## Key Contributions

1. 论文经验性揭示了 VLLMs 的 attention layers 中存在可用于视频压缩的 query-conditioned keyframe prior：attention peak 与任务相关关键帧高度相关。
2. 提出 DyToK，一个 training-free、keyframe-aware 的动态压缩范式：不是二值地保留/丢弃 frame，而是按 frame importance 分配不同数量的 visual tokens。
3. 用 lightweight assistant model 近似主模型的 deep-layer attention prior，从而避免在主模型中先跑到深层再回头指导浅层 pruning 的高成本。
4. 设计了与现有 token pruning 方法兼容的模块化接口，可接入 VisionZip、FastV、DyCoke 等不同 compression backbone。
5. 在 VideoMME、LongVideoBench、MLVU 等 long-video benchmarks 上系统评估了 accuracy-efficiency trade-off，并给出 layer selection、assistant model、importance estimation、upper token limit 等消融。

## Method

DyToK 的输入是视频帧 token、用户 query 和总 token budget。方法先估计每帧的重要性，再把总 budget 动态分给每帧，最后调用任意兼容的 token pruning function。

**Temporal Importance Estimation**

- 对 assistant VLLM 的 deep layers 取 attention。
- 关注 last textual query token 到 visual tokens 的 cross-modal attention。
- 对选定深层集合 $\mathcal{L}'$ 聚合，得到 calibrated temporal importance：

$$
\hat{w}_f = \frac{1}{|\mathcal{L}'|} \sum_{l \in \mathcal{L}'} \text{Softmax}\left(\frac{\mathbf{Q}_l \mathbf{K}_l^{\top}}{\sqrt{D}}\right)
$$

其中 $\hat{w}_f$ 在实际使用中会聚合到 frame-level importance。论文默认使用深层 attention，因为浅层更局部、更噪声；实用实现中对所有模型平均最后三分之一层。

**Dynamic Frame-Level Compression**

- 初始 token allocation：

$$
a_f = \lfloor \hat{w}_f \times T_{\mathrm{total}} \rfloor
$$

- 计算剩余 token：

$$
T_{\mathrm{rem}} = T_{\mathrm{total}} - \sum_{f=1}^{F} a_f
$$

- 用 fractional remainder $r_f = (\hat{w}_f \times T_{\mathrm{total}}) - a_f$ 排序，把剩余 token 分给最接近多拿一个 token 的 frames。
- 加入每帧 token 上限 $T_{\max}$，避免 temporal attention outlier 把过多 token 吸走；超过上限的 token 重新分配给仍有 capacity 的 frames。
- 最终对每帧调用兼容的 compression backbone：

$$
z_f = \texttt{Compression}(x_f, a_f)
$$

**Compact Pseudocode**

```text
Input: frame tokens {x_f}, assistant attention layers L', total budget T_total, per-frame cap T_max
1. Run lightweight assistant model and collect deep-layer cross-modal attention.
2. Aggregate attention into frame weights {w_hat_f}.
3. Allocate a_f = floor(w_hat_f * T_total).
4. Distribute remaining tokens by largest fractional remainders.
5. Clip allocations by T_max and redistribute excess tokens.
6. For each frame, run existing token selector Compression(x_f, a_f).
7. Feed compressed visual tokens into the primary VLLM.
```

## Pipeline Figure

![[assets/pipeline_2512.06866.png]]

Caption: **Illustration of DyToK.** 图中展示两阶段流程：先用 lightweight assistant model 的 cross-modal attention 估计 temporal importance，再按 frame importance 执行 Dynamic Frame-Level Compression，把更多 token 留给关键帧，同时兼容不同 pruning methods。

Source: TeX includegraphics from `3_method.tex`, rendered from `method.pdf` with PDF crop bounds into `assets/pipeline_2512.06866.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| VideoMME | Long-video understanding / video QA | Short / Medium / Long / Overall | Accuracy / score | 主实验报告 Overall，源表也给出长度分组。 |
| LongVideoBench | Long-video QA / understanding | Standard setting via LMMs-Eval | Accuracy / score | 覆盖分钟到小时级视频。 |
| MLVU | Multi-task long-video understanding | Standard setting via LMMs-Eval | Accuracy / score | 主实验三大 benchmark 之一。 |
| EgoSchema | Long-form video QA | Subset / Total | Accuracy / score | 用于 appendix 的 upper-limit ablation。 |
| VideoChatGPT | General descriptive video captioning queries | CO / CU / CI / DO / TU | GPT-3.5-Turbo-0613 score | 用于 general descriptive queries 分析。 |

### Main Results: Encoder Feature-Based Compression

主表使用 LLaVA-OneVision，32 frames，每帧 196 tokens，vanilla 共 6272 visual tokens。这里保留每组的 VideoMME Overall、LongVideoBench、MLVU、Average Score 和相对 vanilla 的百分比；源表中红色提升用 `Δ` 表示。

| Method | Retained Tokens | VideoMME Overall | LongVideoBench | MLVU | Avg. Score | Avg. % | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 6272 | 58.5 | 56.6 | 47.1 | 54.1 | 100.0 |  |
| VisionZip | 4704 | 57.8 | 55.4 | 45.0 | 52.7 | 97.4 |  |
| VisionZip† | 4704 | 58.6 | 56.0 | 46.0 | 53.5 | 98.9 |  |
| + DyToK | 4704 | 59.0 | 55.9 | 46.6 | 53.8 | 99.4 | +2.0 |
| DyCoke encoder | 4704 | 58.7 | 55.3 | 47.5 | 53.8 | 99.4 |  |
| + DyToK | 4704 | 59.0 | 56.5 | 47.7 | 54.4 | 100.6 | +1.2 |
| VisionZip | 3136 | 57.2 | 53.8 | 43.7 | 51.6 | 95.4 |  |
| VisionZip† | 3136 | 58.8 | 56.0 | 45.5 | 53.4 | 98.7 |  |
| + DyToK | 3136 | 59.1 | 56.4 | 46.2 | 53.9 | 99.6 | +4.2 |
| DyCoke encoder | 3136 | 58.4 | 55.4 | 46.6 | 53.5 | 98.9 |  |
| + DyToK | 3136 | 58.3 | 57.1 | 47.5 | 54.3 | 100.4 | +1.5 |
| VisionZip | 1568 | 54.2 | 51.4 | 41.2 | 48.9 | 90.4 |  |
| VisionZip† | 1568 | 58.1 | 55.8 | 44.8 | 52.9 | 97.8 |  |
| + DyToK | 1568 | 58.3 | 55.4 | 46.3 | 53.3 | 98.5 | +8.1 |
| DyCoke encoder | 1568 | 57.3 | 54.6 | 43.5 | 51.8 | 95.7 |  |
| + DyToK | 1568 | 57.1 | 55.2 | 45.1 | 52.5 | 97.0 | +1.3 |
| VisionZip | 1120 | 52.3 | 47.7 | 36.5 | 45.5 | 84.1 |  |
| VisionZip† | 1120 | 57.7 | 54.8 | 42.2 | 51.6 | 95.4 |  |
| + DyToK | 1120 | 57.8 | 56.0 | 45.2 | 53.0 | 98.0 | +13.9 |
| DyCoke encoder | 1120 | 55.4 | 52.6 | 45.3 | 51.1 | 94.5 |  |
| + DyToK | 1120 | 55.6 | 53.2 | 44.6 | 51.1 | 94.5 |  |
| VisionZip | 448 | 44.5 | 41.4 | 29.8 | 38.6 | 71.3 |  |
| VisionZip† | 448 | 49.8 | 47.8 | 37.6 | 45.1 | 83.4 |  |
| + DyToK | 448 | 53.2 | 50.4 | 42.8 | 48.8 | 90.2 | +18.9 |
| DyCoke encoder | 448 | 53.8 | 50.4 | 40.9 | 48.4 | 89.5 |  |
| + DyToK | 448 | 53.5 | 50.2 | 43.6 | 49.1 | 90.8 | +1.3 |

观察：DyToK 在高压缩区间更有价值，尤其对 VisionZip 系列，在 10% retention 下平均相对分从 71.3% 提到 90.2%。这支持论文的核心说法：当 token budget 很紧时，frame-level temporal importance 比 uniform 或静态 pruning 更关键。

### Main Results: LLM Attention-Based Compression

| Method | Retained Tokens | VideoMME Overall | LongVideoBench | MLVU | Avg. Score | Avg. % | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 6272 | 58.5 | 56.6 | 47.1 | 54.1 | 100.0 |  |
| FastV | 4704 | 57.6 | 57.1 | 46.5 | 53.7 | 99.3 |  |
| + DyToK | 4704 | 58.4 | 56.8 | 46.8 | 54.0 | 99.8 | +0.5 |
| DyCoke LLM | 4704 | 58.7 | 55.3 | 47.5 | 53.8 | 99.4 |  |
| + DyToK | 4704 | 58.6 | 55.9 | 47.5 | 54.0 | 99.8 | +0.4 |
| FastV | 3136 | 57.2 | 57.1 | 44.7 | 53.0 | 98.0 |  |
| + DyToK | 3136 | 58.5 | 57.2 | 46.3 | 54.0 | 99.8 | +1.8 |
| DyCoke LLM | 3136 | 58.4 | 55.4 | 46.6 | 53.5 | 98.9 |  |
| + DyToK | 3136 | 58.5 | 56.0 | 46.9 | 53.8 | 99.4 | +0.5 |
| FastV | 1568 | 56.0 | 56.6 | 43.7 | 52.1 | 96.3 |  |
| + DyToK | 1568 | 56.3 | 55.7 | 47.8 | 53.3 | 98.5 | +2.2 |
| DyCoke LLM | 1568 | 57.3 | 54.6 | 43.5 | 51.8 | 95.7 |  |
| + DyToK | 1568 | 57.1 | 54.8 | 45.4 | 52.4 | 96.9 | +1.2 |
| FastV | 896 | 51.1 | 51.2 | 38.3 | 46.9 | 86.7 |  |
| + DyToK | 896 | 54.8 | 52.6 | 43.2 | 50.2 | 92.8 | +6.1 |
| DyCoke LLM | 896 | 54.7 | 52.2 | 42.5 | 49.8 | 92.1 |  |
| + DyToK | 896 | 55.1 | 52.4 | 42.9 | 50.1 | 92.6 | +0.5 |
| DyCoke LLM | 448 | 53.8 | 50.4 | 40.9 | 48.4 | 89.5 |  |
| + DyToK | 448 | 54.2 | 50.4 | 41.2 | 48.6 | 89.8 | +0.3 |

FastV 在 90% pruning 时被作者省略，因为预算对齐后 FastV 保留 visual tokens 为 0，DyToK 也没有 token 可重新分配。

### Ablations / Analysis

**Layer selection.** 20% retention、32 frames。深层 attention 明显优于浅层；第 20 层达到最高平均分。

| Layer | VideoMME Overall | LongVideoBench | MLVU | Avg. Score | Avg. % |
| ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 58.5 | 56.6 | 47.1 | 54.1 | 100.0 |
| 0 | 54.0 | 52.0 | 40.8 | 48.9 | 90.5 |
| 4 | 55.3 | 53.5 | 42.3 | 50.4 | 93.1 |
| 8 | 55.0 | 53.4 | 41.5 | 50.0 | 92.3 |
| 12 | 56.1 | 53.3 | 43.3 | 50.9 | 94.1 |
| 16 | 56.6 | 53.4 | 44.9 | 51.6 | 95.4 |
| 20 | 57.5 | 55.5 | 46.3 | 53.1 | 98.2 |
| 23 | 57.1 | 53.8 | 45.1 | 52.0 | 96.1 |

**Assistant model size.** Base 使用 LLaVA-OneVision-7B 提供 keyframe prior，Tiny 使用 LLaVA-OneVision-0.5B。Tiny 在多数 compression ratios 下接近 Base，支持用轻量 assistant 降低 prior extraction 成本。

| Prior Model | Retained Tokens | VideoMME Overall | LongVideoBench | MLVU | Avg. Score | Avg. % | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 6272 | 58.5 | 56.6 | 47.1 | 54.1 | 100.0 |  |
| Base | 4704 | 59.1 | 55.7 | 47.5 | 54.1 | 100.0 |  |
| Tiny | 4704 | 59.0 | 55.9 | 46.6 | 53.8 | 99.4 | -0.6 |
| Base | 3136 | 59.3 | 55.9 | 46.0 | 53.7 | 99.3 |  |
| Tiny | 3136 | 59.1 | 56.4 | 46.2 | 53.9 | 99.6 | +0.3 |
| Base | 1568 | 58.6 | 57.2 | 46.6 | 54.1 | 100.0 |  |
| Tiny | 1568 | 58.3 | 55.4 | 46.3 | 53.3 | 98.5 | -1.5 |
| Base | 1120 | 58.3 | 55.8 | 46.5 | 53.5 | 98.9 |  |
| Tiny | 1120 | 57.8 | 56.0 | 45.2 | 53.0 | 98.0 | -0.9 |
| Base | 448 | 54.6 | 52.7 | 41.5 | 49.6 | 91.7 |  |
| Tiny | 448 | 53.2 | 50.4 | 42.8 | 48.8 | 90.2 | -1.5 |

**Importance estimation strategies.** DyToK 的 attention-based frame weighting 在低 retention ratio 下优势更明显。

| Method | Retention Ratio | VideoMME | LongVideoBench | MLVU | Avg. Score | Avg. % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 100% | 58.5 | 56.6 | 47.1 | 54.1 | 100.0 |
| Attention Entropy-Based | 25% | 58.3 | 55.9 | 45.6 | 53.3 | 98.5 |
| Feature Entropy-Based | 25% | 58.3 | 54.8 | 42.9 | 52.0 | 96.1 |
| Feature Magnitude-Based | 25% | 58.3 | 56.0 | 44.8 | 53.1 | 98.1 |
| DyToK | 25% | 58.3 | 55.4 | 46.3 | 53.3 | 98.5 |
| Attention Entropy-Based | 15% | 55.2 | 52.8 | 43.4 | 50.5 | 93.2 |
| Feature Entropy-Based | 15% | 55.2 | 52.7 | 44.9 | 50.9 | 94.1 |
| Feature Magnitude-Based | 15% | 54.7 | 53.3 | 43.8 | 50.6 | 93.5 |
| DyToK | 15% | 56.7 | 54.2 | 43.4 | 53.3 | 96.0 |
| Attention Entropy-Based | 10% | 50.6 | 48.1 | 38.6 | 45.7 | 84.5 |
| Feature Entropy-Based | 10% | 50.7 | 48.8 | 38.4 | 45.9 | 84.9 |
| Feature Magnitude-Based | 10% | 50.6 | 47.4 | 37.9 | 45.3 | 83.7 |
| DyToK | 10% | 53.2 | 50.4 | 42.8 | 48.8 | 90.2 |

**Efficiency.** LLaVA-OneVision 7B、32 frames、VisionZip pruning。Latency 是 prefilling time。

| Method | Retention Ratio | FLOPs (T) | Memory (GB) | Latency (ms) | VideoMME | LongVideoBench | MLVU | Avg. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 100% | 40.8 | 22.2 | 48.3 | 58.5 | 56.6 | 47.1 | 54.1 |
| DyToK | 75% | 32.6 | 20.2 | 44.1 | 59.0 | 55.9 | 46.6 | 53.8 |
| DyToK | 50% | 21.9 | 17.3 | 23.5 | 59.1 | 56.4 | 46.2 | 53.9 |
| DyToK | 25% | 12.2 | 17.3 | 11.3 | 58.3 | 55.4 | 46.3 | 53.3 |
| DyToK | 20% | 9.6 | 17.3 | 10.7 | 58.4 | 55.4 | 43.7 | 52.5 |
| DyToK | 15% | 8.4 | 17.3 | 10.4 | 56.7 | 54.2 | 43.4 | 51.4 |
| DyToK | 10% | 5.9 | 17.3 | 10.8 | 53.2 | 50.4 | 42.8 | 48.8 |

### Generalization Highlights

| Setting | Key Result |
| --- | --- |
| Qwen2.5-VL 7B, 32 frames, FastV | DyToK 在 75%、50%、25%、15% retention 下分别比 FastV 的 Avg.% 高 +3.8、+10.5、+12.4、+11.7；10% 时相同。 |
| LLaVA-OneVision, 64 frames, VisionZip† + DyToK (7B guide) | 90% pruning / 896 tokens 下 Avg. Score 52.0，Avg.% 93.7，相比 VisionZip 的 69.7% 有 +24.0 相对提升。 |
| Qwen2.5-VL 32B on MLVU, FastV baseline | 7B assistant guide 在 25%、20%、15% retention 下分别为 36.3、34.9、33.9，明显高于 FastV 的 23.6、22.3、17.1。 |
| VideoChatGPT descriptive queries | 10% retention 下 VisionZip Avg. 1.53，DyToK Avg. 2.37，说明非显式 QA 查询也能从 dynamic frame allocation 受益。 |

### Training / Compute

| Item | Value |
| --- | --- |
| Training | Training-free；不需要重新训练主 VLLM 或 pruning module。 |
| Main evaluated VLLM | LLaVA-OneVision 7B；appendix 还评估 Qwen2.5-VL。 |
| Assistant prior model | LLaVA-OneVision-0.5B 或同家族轻量模型；论文称约比 7B 小 14x。 |
| Main input setting | 32 frames，每帧 196 visual tokens，共 6272 tokens。 |
| Extended setting | 64 frames，共 12544 tokens。 |
| Compression backbones | VisionZip / VisionZip†, FastV, DyCoke encoder-side, DyCoke LLM-side。 |
| Budget matching | 作者按 FLOPs 对齐 computational budgets。 |
| Evaluation | LMMs-Eval standard settings for VideoMME, LongVideoBench, MLVU。 |
| Extra implementation detail | Qwen2.5-VL broader-model experiments 使用 NF4 4-bit quantization、bfloat16 compute、FlashAttention-2。 |

## Limitations & Caveats

- DyToK 的 efficiency 依赖 lightweight assistant model；这比直接用主模型深层 attention 便宜，但仍然引入额外模型和一次 prior extraction pass。
- attention prior 本身会有 temporal attention outlier：初始、末尾或中间非语义 frame 可能吸走过多 attention，因此方法需要 $T_{\max}$ 这类 per-frame cap 来稳定 allocation。
- 论文主要验证 video QA / long-video understanding；对 streaming video、实时交互、多轮对话或更开放的视频生成式任务，泛化仍需要额外确认。
- VisionZip† 是作者为适配 pooling 后 token pruning 做的改造版本，因此与原始 VisionZip 的比较需要注意 implementation changes。
- Qwen2.5-VL 的部分 pruning logic 因 sliding window attention 和 3D convolutions 做了适配；不同 VLLM 架构接入时可能需要工程调整。
- 作者报告了 speedup、FLOPs、memory 和 prefilling latency，但没有在正文中完整展开不同硬件、batch size、video length 分布下的系统吞吐分析。

## Concrete Implementation Ideas

1. 在现有 VLLM inference pipeline 前加一个 assistant attention pass，只保留 frame-level weights，不保存完整 token-level attention，以降低内存压力。
2. 把 DyToK 写成 budget allocator：输入 `{frame_id: weight}`、`T_total`、`T_max`，输出 `{frame_id: token_budget}`，再把 budget 交给现有 VisionZip/FastV selector。
3. 默认用 assistant 的最后三分之一 layers 做 attention aggregation；在高 retention ratio 下可优先尝试 last query token，在更激进 compression 下可比较 all query tokens。
4. 给 frame weight 分布加监控：如果单帧权重异常峰值过高，启用更紧的 $T_{\max}$ 或对 weights 做 clipping / temperature smoothing。
5. 对项目里的 long-video eval 先跑 25%、15%、10% retention 三个点，因为论文显示 DyToK 的边际收益在低 token budget 下最明显。

## Open Questions / Follow-ups

- 是否能不用 assistant model，而用 early-exit、proxy heads 或 learned lightweight predictor 直接预测 keyframe prior？
- $T_{\max}$ 应该如何随帧数、每帧 patch 数、video duration 和 VLLM 架构自动调整？
- temporal attention outlier 是否可通过 attention calibration、register token handling 或 positional encoding 修正来直接缓解？
- 对开放式生成任务、dense temporal grounding、multi-event reasoning，frame-level budget allocation 是否仍足够细粒度？
- 是否可以把 DyToK 和 KV-cache compression、speculative decoding、streaming memory 等系统级优化组合起来？

## Citation

```bibtex
@article{li2025less,
  title={Less Is More, but Where? Dynamic Token Compression via LLM-Guided Keyframe Prior},
  author={Li, Yulin and Gui, Haokun and Fan, Ziyang and Wang, Junjie and Kang, Bin and Chen, Bin and Tian, Zhuotao},
  journal={arXiv preprint arXiv:2512.06866},
  year={2025}
}
```

arXiv: [https://arxiv.org/abs/2512.06866](https://arxiv.org/abs/2512.06866). arXiv metadata comment: Accepted by NeurIPS 2025.
