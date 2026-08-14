---
title: Token Reduction via Local and Global Contexts Optimization for Efficient Video Large Language Models
authors:
  - Jinlong Li
  - Liyuan Jiang
  - Haonan Zhang
  - Nicu Sebe
conference: CVPR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2603.01400
pdf_link: "[[Paper/raw/token-reduction-via-local-and-global-contexts-optimization-for-efficient-video-large/assets/paper_2603.01400.pdf]]"
cover: "[[Paper/raw/token-reduction-via-local-and-global-contexts-optimization-for-efficient-video-large/assets/pipeline_2603.01400.png]]"
updated: 2026-06-01
tags:
  - paper/arxiv
  - video-llm
  - long-video
  - temporal-reasoning
  - token-pruning
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/TyroneLi/AOT
---

## TL;DR

- 论文提出 **AOT**，一个 training-free 的 Video LLM token reduction 方法：不只是丢弃或平均合并冗余 visual tokens，而是用 **Optimal Transport** 把被压缩 token 的信息聚合到保留的 token anchors 上。
- AOT 分两级做压缩：先在每帧内部用 local/global anchors 做 intra-frame OT，再在 frame clip 内用首帧作为 temporal anchors 做 inter-frame OT。
- 核心直觉是把 selected anchors 看作 demanders，把 unselected tokens 看作 suppliers，用 transport plan $T$ 决定每个被压缩 token 的上下文应当注入到哪些 anchors。
- 在 LLaVA-OneVision-7B 上，AOT 在 10% retained ratio 下保留 97.6% 的 vanilla 平均性能；在 LLaVA-Video-7B 上，15% retained ratio 下保留 95.5% 平均性能。
- OT 额外开销很小：32-frame LLaVA-OneVision 设置下，100 次 Sinkhorn iteration 的 intra/inter 总耗时约 2.11 ms，小于总推理时间 1%。
- 局限主要在 temporal anchors：inter-frame OT 的 clip/anchor 构建仍然偏 heuristic，复杂视频中错误分段会影响压缩质量。

## Key Contributions

1. 提出一个不依赖训练的 Video LLM token reduction 视角：保留 token anchors，同时把被移除/合并 token 的细粒度语义通过 OT 聚合回来。
2. 设计 local-global token anchors：global anchors 由 attention-guided token importance 选择，local anchors 在 grid windows 内选择，以兼顾语义重要性和空间覆盖。
3. 将 Optimal Transport 分别用于 intra-frame 和 inter-frame token aggregation，既压缩空间冗余，也压缩时间冗余，并保留高变化 temporal tokens。
4. 在 MVBench、EgoSchema、LongVideoBench、VideoMME 上验证，覆盖 LLaVA-OneVision-7B 与 LLaVA-Video-7B 两个 Video LLM backbone。

## Method

### Pipeline

1. **Global Anchors**：对有 `[CLS]` token 的视觉编码器，使用最终层 `[CLS]` attention 的 head-averaged score 选择 Top-$K$ visual tokens；没有 `[CLS]` 的模型使用 token 接收的平均 self-attention 作为 importance score。
2. **Local Anchors**：将每帧 feature map 划分为 $W$ 个 non-overlapping windows，在每个 window 内从浅层 attention 中选择局部重要 token，总预算为 $K$，每窗 $K_w=K/W$。
3. **Anchor Set**：最终 anchors 为 $\mathbf{X}_V^{\texttt{anchors}} = \mathbf{x}_V^{\mathtt{g}} \cup \mathbf{x}_V^{\mathtt{l}}$，局部与全局选择做去重并大致平衡。
4. **Intra-Frame OT**：每帧内用 anchors $\mathbf{X}_V^{\texttt{a}}$ 与 unanchors $\mathbf{X}_V^{\texttt{u}}$ 构造 cost matrix，采用 inverse cosine similarity：

$$
\mathbf{C}=\mathbf{1}-\left(\mathbf{X}^{a}_{V}\right)^{\top}\mathbf{X}^{u}_{V}
$$

求得 Sinkhorn OT plan $\mathbf{T}_{\mathrm{intra}}^*$ 后，将 unselected token 信息按 transport mass 注入 anchors：

$$
\tilde{\mathbf{x}}^{a}_j =
\frac{
    \mathbf{x}^{a}_j
    + \lambda_{intra} \sum_{i=1}^{N-M} T^*_{ij}\mathbf{x}^{u}_i
}{
    1 + \lambda_{intra} m_j
}, \quad
m_j=\sum_{i=1}^{N-M}T^*_{ij}
$$

5. **Inter-Frame OT**：把 sampled frames 划成 clips，每个 clip 的第一帧 intra-frame anchors 作为 temporal anchors。后续帧的 token 与当前 clip anchors 做 OT，对相似 token 做聚合，对变化大的 token 保留。
6. **High-Change Tokens**：对 inter-frame plan 做 row-normalization，$q_i^{(\ell)} = \max_j p_{ij}^{(\ell)}$。若 $q_i^{(\ell)} < \tau$，说明该 token 与已有 anchors 不够匹配，被视为 temporal dynamics token 保留。

### Compact Pseudocode

```text
for each frame:
  select global anchors by attention importance
  select local anchors within grid windows
  solve Sinkhorn OT between anchors and unselected tokens
  update anchors by transport-weighted aggregation

for each temporal clip:
  initialize clip anchors with first frame anchors
  for each following frame:
    solve Sinkhorn OT between clip anchors and frame anchors
    keep high-change tokens where max assignment < tau
    aggregate stable tokens into clip anchors
return compressed anchors + high-change temporal tokens
```

## Pipeline Figure

![[Paper/raw/token-reduction-via-local-and-global-contexts-optimization-for-efficient-video-large/assets/pipeline_2603.01400.png]]

Caption: Overall pipeline of AOT. The method compresses Video LLM tokens across spatiotemporal dimensions through optimal transport: local/global token anchors are established per frame, intra-frame OT aggregates informative cues from pruned tokens, and inter-frame OT compresses temporal redundancy while preserving dynamic tokens.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| MVBench | Multi-modal video understanding | not reported | Accuracy / score | 短视频与多任务视频理解 benchmark。 |
| EgoSchema | Long-form egocentric video QA | not reported | Accuracy / score | 用于长视频语义理解。 |
| LongVideoBench | Long-video understanding | not reported | Accuracy / score | 强调长上下文视频推理。 |
| VideoMME | Video multimodal evaluation | not reported | Accuracy / score | 覆盖不同长度和复杂场景。 |

### Main Results: LLaVA-OneVision-7B

表格保留论文 Table 1 的关键可比行。Avg. % 表示相对 vanilla 平均性能保留率；Best/second-best 高亮只在同等或相近 retained-ratio 分组内比较。

| Method | Prefilling FLOPs (T) ↓ | FLOPs Ratio ↓ | Retained Ratio | MVBench ↑ | EgoSchema ↑ | LongVideoBench ↑ | VideoMME ↑ | Avg. Score ↑ | Avg. % ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OV-7B | 40.8 | 100% | 100% | 58.3 | 60.4 | 56.4 | 58.6 | 58.4 | 100 |
| FastV | 9.3 | 22.8% | 100% | 55.9 | 57.5 | **56.7** | 56.1 | 56.5 | 96.7 |
| PDrop | 10.5 | 25.7% | 100% | 56.1 | 58.0 | 54.1 | 56.4 | 56.2 | 96.2 |
| DyCoke | 8.7 | 21.3% | 25% | 53.1 | 59.5 | 49.5 | 54.3 | 54.1 | 92.6 |
| VisionZip | 8.7 | 21.3% | 25% | <u>57.9</u> | <u>60.3</u> | <u>56.5</u> | **58.2** | <u>58.2</u> | <u>99.7</u> |
| PruneVid | 8.7 | 21.3% | 25% | 57.4 | 59.9 | 55.7 | 57.4 | 57.6 | 98.6 |
| **AOT** | 8.7 | 21.3% | 25% | **58.7** | **61.3** | 56.3 | 57.5 | **58.5** | **100.0** |
| VisionZip | 7.0 | 17.2% | 20% | <u>57.7</u> | <u>59.8</u> | 55.2 | **57.9** | <u>57.7</u> | <u>98.8</u> |
| PruneVid | 7.0 | 17.2% | 20% | 57.2 | 59.7 | 54.7 | 56.9 | 57.1 | 97.8 |
| **AOT** | 7.0 | 17.2% | 20% | **58.1** | **61.3** | <u>56.2</u> | <u>57.2</u> | **58.2** | **99.7** |
| VisionZip | 5.2 | 12.7% | 15% | 56.5 | <u>59.8</u> | 54.4 | 56.1 | 56.7 | 97.1 |
| PruneVid | 5.2 | 12.7% | 15% | <u>56.8</u> | 59.7 | <u>55.4</u> | <u>56.6</u> | <u>57.1</u> | <u>97.8</u> |
| **AOT** | 3.4 | 8.3% | 15% | **57.8** | **61.3** | 55.2 | <u>56.6</u> | **57.7** | **98.8** |
| VisionZip | 3.4 | 8.3% | 10% | 53.5 | 58.0 | 49.3 | 53.4 | 53.5 | 91.6 |
| PruneVid | 3.4 | 8.3% | 10% | <u>56.2</u> | <u>59.8</u> | <u>54.5</u> | 56.0 | <u>56.6</u> | <u>96.9</u> |
| **AOT** | 5.2 | 12.7% | 10% | **57.0** | **60.6** | 54.2 | <u>56.1</u> | **57.0** | **97.6** |

### Main Results: LLaVA-Video-7B

| Method | Prefilling FLOPs (T) ↓ | FLOPs Ratio ↓ | Retained Ratio | MVBench ↑ | EgoSchema ↑ | LongVideoBench ↑ | VideoMME ↑ | Avg. Score ↑ | Avg. % ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-Video-7B | 80.2 | 100% | 100% | 60.4 | 57.2 | 58.9 | 64.3 | 60.2 | 100 |
| FastV | 17.1 | 21.3% | 100% | 54.3 | 54.1 | <u>55.0</u> | 58.8 | 55.6 | 92.4 |
| PDrop | 19.5 | 24.3% | 100% | 55.9 | 54.3 | 54.7 | <u>61.9</u> | <u>56.7</u> | <u>94.2</u> |
| VisionZip | 9.3 | 18.9% | 25% | <u>56.7</u> | <u>54.7</u> | 54.7 | 60.7 | <u>56.7</u> | <u>94.2</u> |
| DyCoke | 9.3 | 18.9% | 25% | 50.8 | - | 53.0 | 56.9 | - | - |
| **AOT** | 9.3 | 18.9% | 25% | **58.8** | **55.4** | **56.2** | **62.4** | **58.2** | **96.7** |
| VisionZip | 9.3 | 11.6% | 15% | <u>56.7</u> | <u>54.7</u> | <u>54.7</u> | <u>60.7</u> | <u>56.7</u> | <u>94.2</u> |
| **AOT** | 9.3 | 11.6% | 15% | **57.8** | **55.2** | **55.0** | **62.0** | **57.5** | **95.5** |

### Ablations / Analysis

| Variant / Setting | MVBench ↑ | EgoSchema ↑ | LongVideoBench ↑ | VideoMME ↑ | Avg. Score ↑ | Avg. % ↑ | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Vanilla | 58.3 | 60.4 | 56.4 | 58.6 | 58.4 | 100 | LLaVA-OneVision-7B baseline。 |
| w/o Local Anchors | 56.5 | 60.1 | 54.0 | 55.7 | 56.6 | 96.9 | 只保留 global anchors，空间覆盖下降。 |
| w/o Global Anchors | 55.5 | 59.4 | 53.4 | 53.1 | 55.4 | 94.9 | 只保留 local anchors，语义选择下降更明显。 |
| w/o OT | 56.1 | 60.2 | 53.5 | 55.8 | 56.4 | 96.6 | 去掉 OT aggregation，说明“聚合被剪 token 信息”有贡献。 |
| OT w/o Intra-frame | 57.1 | 60.2 | 53.6 | 54.6 | 56.3 | 96.6 | 只保留 inter-frame 部分。 |
| OT w/o Inter-frame | 56.1 | 60.0 | 53.6 | 55.9 | 56.4 | 96.6 | 只保留 intra-frame 部分。 |
| AOT | 57.0 | 60.6 | 54.2 | 56.1 | 57.0 | 97.6 | 完整方法，10% retained ratio。 |

| Aggregation | MVBench ↑ | EgoSchema ↑ | LongVideoBench ↑ | VideoMME ↑ | Avg. ↑ | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| No Merging | 56.1 | 60.2 | 53.5 | 55.8 | 56.4 | 不聚合被压缩 token。 |
| Cosine Merging | 51.5 | 55.8 | 51.1 | 51.3 | 52.4 | 简单 cosine weighting 表现明显更差。 |
| Ours AOT | 57.0 | 60.6 | 54.2 | 56.1 | 57.0 | Transport-weighted aggregation 最优。 |

| Random Anchor Ablation | MVBench ↑ | EgoSchema ↑ | LongVideoBench ↑ | VideoMME ↑ | Avg. Score ↑ | Avg. % ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanilla | 58.3 | 60.4 | 56.4 | 58.6 | 58.4 | 100 |
| w Random Anchors | 55.1 | 59.3 | 52.6 | 53.3 | 55.1 | 94.3 |
| AOT | 57.0 | 60.6 | 54.2 | 56.1 | 57.0 | 97.6 |

| Sinkhorn Iterations | Intra-Frame | Inter-Frame | Overall | % of Total Inference |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 0.50 ms | 1.50 ms | 2.00 ms | ≤ 1% |
| 100 | 0.51 ms | 1.60 ms | 2.11 ms | ≤ 1% |

### Training / Compute

| Item | Value |
| --- | --- |
| Training requirement | Training-free inference-time method |
| Backbones | LLaVA-OneVision-7B, LLaVA-Video-7B |
| Evaluation hardware | NVIDIA A100 GPUs; supplement specifies 8× NVIDIA A100 40GB |
| LLaVA-OneVision frames/tokens | 32 frames, $N_v=196$ tokens per frame |
| LLaVA-Video frames/tokens | 64 frames, $N_v=169$ tokens per frame |
| Sinkhorn iterations | 100 by default |
| OT entropy parameter | Supplement reports $\lambda=0.1$ |
| Aggregation weights | $\lambda_{intra}=1.0$, $\lambda_{inter}=1.0$ by default |
| LLaVA-OneVision intra-frame anchors | 126 / 144 / 196 / 205 for 10% / 15% / 20% / 25% budgets |
| LLaVA-Video intra-frame anchors | 108 / 144 / 176 / 198 for 10% / 15% / 20% / 25% budgets |
| Eval framework | LMMs Eval |

## Limitations & Caveats

- Inter-frame OT 的 temporal anchor 构造仍然 heuristic；不像 intra-frame 情况可以直接依赖成熟视觉编码器的 attention/feature 质量。
- 固定或动态 temporal segmentation 都可能产生 noisy boundaries；复杂视频中，视觉差异大的 frames 被放入同一 clip 会影响 aggregation。
- 论文主要验证 inference-time training-free setting，尚未展示与 fine-tuning/instruction tuning 联合优化后的收益。
- AOT 的目标是 efficient inference；对于强依赖微小运动、几何一致性、camera motion 或 3D correspondence 的任务，当前 anchors 是否保留足够结构信息仍是开放问题。
- 部分表格的 retained ratio 与 FLOPs ratio 并不单调一致：例如 LLaVA-OneVision 的 15% AOT 行为 3.4T / 8.3%，而 10% AOT 行为 5.2T / 12.7%。论文补充材料说明 overall retention 会通过调节 inter-frame keep threshold $\tau$ 匹配，因此复现时需要核对官方配置。

## Concrete Implementation Ideas

1. **先做可插拔 pre-LLM compressor**：把 AOT 包成 visual token preprocessor，输入 frame tokens + visual attention，输出 compressed anchors + high-change tokens，尽量不改 LLM 主体。
2. **复用现有 Sinkhorn 实现**：核心计算是 cost matrix、Sinkhorn scaling、transport-weighted aggregation；GPU 上保持 batched matrix ops，避免 Python loop 处理每个 token。
3. **保留 budget/threshold 配置表**：按 backbone、frame count、retained ratio 配置 $M$ 与 $\tau$，否则复现实验时很容易对不上 FLOPs。
4. **加 temporal diagnostics**：记录每个 clip 被保留的 high-change tokens 数量、$q_i$ 分布、clip boundary，可帮助定位复杂视频中性能下降。
5. **扩展到训练版**：由于 Sinkhorn OT 是 differentiable，可以尝试对 token anchors 或 threshold policy 做轻量 instruction tuning。

## Open Questions / Follow-ups

- 如果把 text query 纳入 cost matrix 或 anchor selection，是否能更好地处理 question-aware video QA？
- Dynamic Temporal Segmentation 的 clip 边界是否可以与 OT objective 联合优化，而不是先分段再聚合？
- AOT 对不同 visual encoder 的 attention 质量是否敏感，尤其是没有 `[CLS]` token 的 SigLip/Qwen-VL 系列？
- 10% retained ratio 下部分 LongVideoBench / VideoMME 分数仍低于最佳 baseline，是否说明某些长视频任务更需要 temporal high-change tokens 而不是更强 aggregation？
- 用 depth、camera motion、trajectory-aware cues 作为辅助监督，能否让 anchors 保留更多 3D/4D spatial consistency？

## Citation

```bibtex
@inproceedings{li2026token,
  title={Token Reduction via Local and Global Contexts Optimization for Efficient Video Large Language Models},
  author={Li, Jinlong and Jiang, Liyuan and Zhang, Haonan and Sebe, Nicu},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2026}
}
```

Links:
- arXiv: https://arxiv.org/abs/2603.01400
- Project: https://tyroneli.github.io/AOT/
- Code: https://github.com/TyroneLi/AOT
