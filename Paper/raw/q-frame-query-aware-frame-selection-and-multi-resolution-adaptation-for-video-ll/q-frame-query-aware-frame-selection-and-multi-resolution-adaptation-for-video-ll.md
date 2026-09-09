---
title: Q-Frame(frame)
authors:
  - Shaojie Zhang
  - Jiahui Yang
  - Jianqin Yin
  - Zhenbo Luo
  - Jian Luan
conference: ICCV 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2506.22139
pdf_link: "[[assets/paper_2506.22139.pdf]]"
cover: "[[_assets/images/pipeline_2506.22139.png]]"
updated: 2026-05-18
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: read
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: ""
---

## TL;DR

- Q-Frame 是一个 training-free、plug-and-play 的 Video-LLM 前处理框架，用 query-aware frame selection 代替固定 uniform sampling，并用 multi-resolution adaptation 在固定 token budget 下保留更多关键视觉细节。
- 方法由 Cross-modal Query Retrieval (CQR)、Query-Aware Frame Selection (QFS)、Multi-Resolution Adaptation (MRA) 三部分组成：先用 CLIP-like VLM 计算 query-frame 相关性，再用 Gumbel-Max 采样关键帧，最后给高/中/低相关帧分配不同分辨率。
- 实验覆盖 MLVU、LongVideoBench、Video-MME；Q-Frame 在 VILA-V1.5、Qwen2-VL、GPT-4o 上都能提升 uniform sampling baseline，说明它对模型架构相对无关。
- 主结果中，Qwen2-VL + Q-Frame 在 MLVU 达到 **65.4**，GPT-4o + Q-Frame 在 LongVideoBench 达到 **58.6**，并在 Video-MME overall 达到 **63.8 / 66.5** (w/o / w subtitles)。
- 主要 caveat 是它依赖 CLIP-like 静态图文匹配，缺少显式 temporal modeling；对需要事件顺序/因果关系的 temporal reasoning case 仍可能失败。

## Key Contributions

1. 提出 Q-Frame，把 frame selection 做成 query-aware，而不是对所有问题使用同一组均匀采样帧。
2. 使用 CLIP-like text-image matching + Gumbel-Max trick 完成训练无关的离散帧选择，不需要 fine-tune Video-LLM 或训练 frame ranker。
3. 引入 MRA，将视觉 token budget 分配给不同 resolution 的帧：更相关的帧保留高分辨率，低相关帧降分辨率以扩大可输入帧数。
4. 在开源模型 VILA-V1.5、Qwen2-VL 以及闭源 GPT-4o 上验证，覆盖 fixed input frames 与 fixed input tokens 两种设置。

## Method

Q-Frame 面向 Video Question Answering，但作者希望它也能迁移到 summarization、temporal grounding 等 video understanding 场景。输入视频为 $\mathcal{V}=\{\text{Frame}^i\}_{i=1}^{D}$，query 为 $q$，目标是在有限 visual token budget 下给 Video-LLM 提供更相关的 frame sequence。

核心流程：

```text
1. Uniformly sample T candidate frames from the original video.
2. Encode query and candidate frames with a CLIP-like VLM.
3. Compute query-frame matching intensity for each candidate frame.
4. Convert intensities to probabilities and sample frames with Gumbel-Max.
5. Assign selected / ranked frames to high, medium, or low resolution groups.
6. Feed text tokens + visual tokens into the target Video-LLM for generation.
```

CQR 使用 VLM text encoder 和 vision encoder 把 query 与 candidate frames 投到共享 embedding space：

$$
Q = \text{VLM}_{\text{text}}(q) \in \mathbb{R}^{d}, \quad
F = \text{VLM}_{\text{vision}}(\mathcal{F}) \in \mathbb{R}^{T \times d}
$$

每一帧的匹配强度用内积计算：

$$
I = QF^{\text{T}} \in \mathbb{R}^{1 \times T}
$$

QFS 先用 temperature scaling 得到分布：

$$
\pi = \text{Softmax}(I/\tau)
$$

再加入 Gumbel noise：

$$
g = -\log(-\log \epsilon), \quad \epsilon \in U[0,1]^T
$$

$$
p = \log \pi + g
$$

最后根据 $p$ 的排序选出 Top-$K$ frames：

$$
\text{idx}^{\text{select}} = \{i \mid \text{rank}(i) \leq K\}
$$

MRA 按 relevance rank 分配 resolution：

$$
\begin{aligned}
\text{idx}^{\text{high}} &= \{i \mid \text{rank}(i) \leq K\} \\
\text{idx}^{\text{mid}} &= \{i \mid K < \text{rank}(i) \leq M\} \\
\text{idx}^{\text{low}} &= \{i \mid M < \text{rank}(i) \leq N\}
\end{aligned}
$$

作者在 Qwen2-VL 设置中用 4 high-res + 8 medium-res + 32 low-res frames 近似匹配 8 个高分辨率帧的 token budget；约束写作：

$$
K + \frac{M}{4} + \frac{N}{16} = 8
$$

## Pipeline Figure

![[_assets/images/pipeline_2506.22139.png]]

Caption: The overall framework of Q-Frame. Q-Frame is composed of Cross-modal Query Retrieval (CQR), Query-Aware Frame Selection (QFS), and Multi-Resolution Adaptation (MRA). CQR retrieves query-relevant frames, QFS adaptively selects important temporal segments, and MRA allocates different resolutions to preserve fine details while reducing cost. The paper notes that MRA is not applicable to every Video-LLM preprocessing pipeline.

Source: TeX `\includegraphics` from `sec/3_method.tex` using `figs/framework.pdf`; rendered to PNG with `pdftoppm -cropbox` at 250 DPI. The original PDF crop box is 1096.08 x 367.92 pt, and the rendered PNG is 3806 x 1278 px.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MLVU | Multi-task long video understanding | 2,593 tasks across 9 categories | Accuracy (%) | Average video duration 12 minutes; includes movies, surveillance, cartoons, etc. |
| LongVideoBench | Long-context interleaved video-language QA | Validation set without subtitles, 1,337 QA pairs | Accuracy (%) | Average video duration 12 minutes; original benchmark has 3,763 videos and 6,678 questions. |
| Video-MME | Multi-domain video QA for MLLMs | 2,700 QA pairs from 900 videos; evaluated w/o and w subtitles | Accuracy (%) | Average video duration 17 minutes; paper also reports Short / Medium / Long duration subsets. |

### Experimental Setup

| Item | Value |
| ---- | ---- |
| Baseline models | VILA-V1.5, Qwen2-VL, GPT-4o |
| Q-Frame modules used | VILA-V1.5: QFS only; GPT-4o: QFS only; Qwen2-VL: QFS + MRA |
| Candidate frames | 128 uniformly sampled candidate frames |
| Selected input | 8 frames, or token-equivalent multi-resolution allocation |
| Evaluation toolkit | LMMs-Eval |
| Compute | 8 H100 GPUs |
| Main settings | Fixed input frames and fixed input tokens |

### Main Results

下表保留论文主表中最相关的对比行。Video-MME 数值格式为 `without subtitles / with subtitles`。

| Method | LLM Size | #Frames | MLVU | LongVideoBench | Video-MME Overall | Video-MME Short | Video-MME Medium | Video-MME Long |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Video-XL | 7B | 128/256 | 64.9 | - | 55.5 / 61.0 | 64.0 / 67.4 | 53.2 / 60.7 | 49.2 / 54.9 |
| LLaVA-OneVision | 7B | * | 64.7 | 56.3 | 58.2 / - | - / - | - / - | - / - |
| Video-CCAM | 9B | 96 | 58.5 | - | 50.3 / 52.6 | 61.9 / 63.1 | 49.2 / 52.3 | 39.6 / 42.4 |
| VILA-V1.5 | 8B | 8 | 46.3 | 47.1 | 47.5 / 50.0 | 57.8 / 61.6 | 44.3 / 46.2 | 40.3 / 42.1 |
| + Frame-Voyager | 8B | 8 | 49.8 | - | 50.5 / 53.6 | 60.3 / 65.0 | 47.3 / 50.3 | 43.9 / 45.3 |
| + **Q-Frame** | 8B | 8 | 54.4 | 51.6 | 50.7 / 55.0 | 59.8 / 65.3 | 48.0 / 53.4 | 44.2 / 46.2 |
| GPT-4o | - | 8 | 28.6 | 53.3 | 61.9 / 64.5 | 69.1 / 72.1 | 62.4 / 63.8 | 54.0 / 57.9 |
| + **Q-Frame** | - | 8 | 29.3 | **58.6** | **63.8** / **66.5** | **69.9** / **73.6** | **63.8** / **65.2** | **57.6** / **60.8** |
| Qwen2-VL-Video | 7B | 8 | 55.6 | 51.0 | 53.0 / 58.3 | 64.1 / 68.2 | 49.3 / 55.1 | 45.6 / 51.7 |
| Qwen2-VL | 7B | 8 | 56.9 | 53.5 | 53.7 / 59.4 | 65.0 / 69.8 | 50.7 / 56.2 | 45.3 / 52.1 |
| + **Q-Frame** | 7B | 4 + 8 + 32 | **65.4** | 58.4 | 58.3 / 61.8 | 69.4 / 73.2 | 57.1 / 61.0 | 48.3 / 51.1 |

要点：Q-Frame 在 VILA-V1.5 上超过 Frame-Voyager，同时不需要训练 frame ranking model；在 GPT-4o 上提升 LongVideoBench 与 Video-MME；在 Qwen2-VL fixed-token 设置中显著提升 MLVU，并用 multi-resolution 输入扩大 effective frames。

### Performance Across Video Lengths

LongVideoBench 按 video duration 分组后，Q-Frame 对长视频收益更明显，但极短视频可能因为 uniform 8 frames 已经足够密集而收益有限。

| Model | (8s, 15s] | (15s, 1m] | (3m, 10m] | (15m, 60m] |
| ---- | ---- | ---- | ---- | ---- |
| VILA-V1.5 | 56.1 | 60.5 | 43.4 | 42.7 |
| + **Q-Frame** | 52.9 (-3.2) | 62.8 (+2.3) | 53.9 (+10.5) | 46.1 (+3.4) |
| GPT-4o | 53.4 | 64.8 | 52.4 | 46.8 |
| + **Q-Frame** | 60.3 (+6.9) | 68.0 (+3.2) | 59.7 (+7.3) | 54.3 (+7.5) |
| Qwen2-VL | 53.5 | 67.6 | 51.5 | 45.9 |
| + **Q-Frame** | 63.0 (+9.5) | 71.5 (+3.9) | 58.5 (+7.0) | 56.4 (+10.5) |

### Ablations / Analysis

Q-Frame 组件消融在 LongVideoBench + Qwen2-VL 上进行。作者标出的最优值保留为 bold。

| Sampling: Uniform | Sampling: CLIP | Sampling: QFS | Resolution: Fixed | Resolution: MRA | Acc (%) |
| ---- | ---- | ---- | ---- | ---- | ---- |
| ✓ |  |  | ✓ |  | 53.5 |
|  | ✓ |  | ✓ |  | 56.0 |
|  |  | ✓ | ✓ |  | 57.6 |
| ✓ |  |  |  | ✓ | 52.6 |
|  | ✓ |  |  | ✓ | 56.6 |
|  |  | ✓ |  | ✓ | **58.4** |

Resolution strategy ablation:

| High | Medium | Low | Acc (%) |
| ---- | ---- | ---- | ---- |
| ✓ |  |  | 57.6 |
|  | ✓ |  | 55.9 |
|  |  | ✓ | 49.0 |
| ✓ | ✓ |  | 57.9 |
| ✓ |  | ✓ | 58.1 |
|  | ✓ | ✓ | 56.3 |
| ✓ | ✓ | ✓ | **58.4** |

Frame resolution allocation ablation:

| K | M | N | Tokens / Video | Acc (%) |
| ---- | ---- | ---- | ---- | ---- |
| 8 | 0 | 0 | 2265.1 | 57.6 |
| 6 | 6 | 8 | 2304.1 (+1.7%) | 57.9 |
| 6 | 4 | 16 | 2312.5 (+2.0%) | 58.3 |
| 4 | 8 | 32 | 2344.8 (+3.5%) | **58.4** |
| 4 | 6 | 40 | 2355.8 (+4.0%) | 58.2 |
| 4 | 4 | 48 | 2370.1 (+4.6%) | 57.4 |

CLIP-like retrieval model ablation:

| Model | Acc (%) |
| ---- | ---- |
| - | 53.5 |
| CLIP | 57.8 |
| SigLIP | 57.9 |
| Long-CLIP | **58.4** |

Temperature parameter $\tau$ ablation:

| $\tau$ | Acc (%) |
| ---- | ---- |
| 0.5 | 57.6 |
| 0.8 | **58.4** |
| 1.0 | 58.2 |
| 1.2 | 58.0 |

注：正文 supplemental 段落说最高点在 $\tau=1.2$，但表格 `tab:tau` 中最高值是 $\tau=0.8$ 的 **58.4**，这里按表格记录。

Candidate frames and overhead:

| Candidate Frames | Sampled Frames | Embedding Latency (ms) | Sampling Latency (ms) | LongVideoBench |
| ---- | ---- | ---- | ---- | ---- |
| 64 | 8 | 76.7 | 87.1 | 56.8 |
| 64 | 4 + 8 + 32 | 73.5 | 89.4 | 57.7 |
| 128 | 8 | 123.8 | 178.6 | 57.6 |
| 128 | 4 + 8 + 32 | 120.1 | 182.8 | 58.4 |
| 256 | 8 | 218.0 | 361.1 | 57.8 |
| 256 | 4 + 8 + 32 | 220.6 | 365.6 | 58.6 |

## Limitations & Caveats

- Q-Frame 依赖 CLIP-like pretrained model 的 image-text matching；如果 query 需要长文本理解或细粒度视频事件关系，retrieval signal 可能不够强。
- QFS 本质上仍然是稀疏帧选择，没有显式建模 temporal order、event boundary 或 causal transition；supplement 中的 bad case 显示它和 uniform sampling 都可能无法处理某些 temporal reasoning 问题。
- MRA 依赖目标 Video-LLM 的 preprocessing 机制；论文明确说明 dotted-line MRA 并不适用于每个模型，GPT-4o 也只使用 QFS。
- 方法在 fixed token budget 下有效，但 token budget 本身仍是固定的；作者把 adaptive frame budgeting 留作 future work。
- 评估主要基于 benchmark，真实应用中的 domain shift、query 分布、视频噪声和字幕/音频融合还需要额外验证。
- 预处理引入额外 embedding 和 sampling latency；虽然相对 Video-LLM 推理成本较小，但在高吞吐部署中仍需要缓存或批处理优化。

## Concrete Implementation Ideas

1. 在现有 Video-LLM inference pipeline 前增加一个 `QFrameSelector`：先 uniform sample 128 candidate frames，再用 Long-CLIP/SigLIP 计算 query-frame similarity，输出按时间排序的 selected frames。
2. 对每个视频缓存 frame embeddings；同一个视频面对不同 query 时只重复 text embedding、similarity、Gumbel-Max sampling，降低 CQR 成本。
3. 把 token budget solver 显式化：给定目标视觉 token 上限，自动搜索类似 4 high + 8 medium + 32 low 的 resolution allocation，而不是写死 $K,M,N$。
4. 对 temporal reasoning 场景加入 continuity constraint：在 Top-$K$ 相关帧附近扩展小窗口，或对相邻帧设置 coverage penalty，减少只选离散静态相关帧的问题。
5. 在产品侧暴露 $\tau$、candidate frame count、resolution tiers 三个可调参数，并记录每次 query 的 selected-frame timeline，方便 debug 和可解释性分析。

## Open Questions / Follow-ups

- Long-CLIP 在本论文中表现最好，但不同 CLIP-like model 对不同 benchmark / query 类型的稳定性如何？
- Gumbel-Max 的 stochastic selection 是否需要多次采样投票，尤其是在高风险或高噪声 query 中？
- 如果加入 video-text pretrained model 或 temporal encoder 替代 image-text CLIP，能否缓解 bad case 中的 temporal reasoning 失败？
- MRA 是否能和模型自身的 dynamic visual token pruning、KV cache compression 或 long-context attention 结合，而不是只做前处理？
- 作者没有给出公开 code；复现时需要确认 frame extraction、query prompt、resolution resize、Video-LLM preprocessing 的细节是否足以匹配论文结果。

## Citation

arXiv: [2506.22139](https://arxiv.org/abs/2506.22139), ICCV 2025.

```bibtex
@article{zhang2025qframe,
  title={Q-Frame: Query-aware Frame Selection and Multi-Resolution Adaptation for Video-LLMs},
  author={Zhang, Shaojie and Yang, Jiahui and Yin, Jianqin and Luo, Zhenbo and Luan, Jian},
  journal={arXiv preprint arXiv:2506.22139},
  year={2025}
}
```
