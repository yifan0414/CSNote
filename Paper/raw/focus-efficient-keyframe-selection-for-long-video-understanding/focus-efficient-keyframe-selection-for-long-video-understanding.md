---
title: FOCUS(frame)
authors:
  - Zirui Zhu
  - Hailun Xu
  - Yang Luo
  - Yong Liu
  - Kanchan Sarkar
  - Zhenheng Yang
  - Yang You
conference: ICLR 2026
year: 2025
arxiv_url: https://arxiv.org/abs/2510.27280
pdf_link: "[[assets/paper_2510.27280.pdf]]"
cover: "[[assets/pipeline_2510.27280.png]]"
updated: 2026-05-20
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: reading
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/NUS-HPC-AI-Lab/FOCUS
---

## TL;DR

- FOCUS 关注 long-video MLLM 的核心瓶颈：长视频会产生过多 visual tokens，而统一采样或先降采样再检索会错过关键片段。
- 它把 query-aware keyframe selection 建模成 Combinatorial Pure-Exploration (CPE) multi-armed bandit：短 temporal clips 是 arms，frame-query relevance 是 reward。
- 方法是 training-free、model-agnostic、plug-and-play；用 BLIP ITM 给 sampled frames 打 relevance score，再用 empirical mean 与 Bernstein confidence radius 做 optimistic selection。
- 实际算法把理论上的 sequential arm pulling 简化成两阶段 batched schedule：coarse exploration 先找高潜力 arms，fine-grained exploitation 再精炼，便于 GPU 并行。
- 在 LongVideoBench 和 Video-MME 上，FOCUS 在四种 MLLMs 上都提升 accuracy；对超过 20 分钟的视频，LongVideoBench 上相对 uniform sampling 提升 11.9 个百分点。
- 效率上，FOCUS 只处理少于 2% 的视频帧；在 LongVideoBench 上 report 为 1.6% frames seen、5.5 H100 GPU hours。

## Key Contributions

1. 论文把 query-aware keyframe selection 形式化为 budgeted CPE multi-armed bandit，而不是简单的 uniform sampling 或 dense retrieval。
2. 提出 FOCUS (Frame-Optimistic Confidence Upper-bound Selection)，用 empirical Bernstein confidence radius 同时考虑 high mean 与 high uncertainty clips。
3. 将 sequential optimistic arm selection 改造成 two-stage batched algorithm，在保留 optimism 思路的同时适配 GPU batch inference。
4. 在 LongVideoBench、Video-MME 以及 appendix 中的 MLVU、VSI-Bench 上验证了跨 MLLM backbone 的稳定收益。
5. 通过效率实验展示：相比 AKS 的 1 fps pre-filtering，FOCUS 可以 filtering-free 地减少 BLIP forward passes，同时提升 downstream QA accuracy。

## Method

核心问题：给定视频 $V=(x_1,\ldots,x_T)$ 与 query $q$，下游 MLLM $\Phi$ 只能接收 $K$ 个 frames。理想目标是选择 frame subset $\mathcal{K}$ 最大化 downstream utility：

$$
\mathcal{K}^{\mathrm{oracle}}(V,q)=\arg\max_{\mathcal{K}\subseteq\mathcal{T},|\mathcal{K}|=K}\mathbb{E}[R_\Phi(\mathcal{K}\mid V,q)].
$$

因为直接评估 $\Phi$ 的组合搜索不可行，论文使用 frame-query relevance surrogate：用 vision-language encoder $\psi$ 计算 $r_t=\psi(x_t,q;\theta)$，并将其视为 latent frame utility $y_t$ 的 noisy unbiased estimate。

FOCUS pipeline:

1. **Clip partition**：把长视频切成固定长度 clips $\mathcal{A}=\{A_a\}_{a=1}^{M}$，每个 clip 是一个 bandit arm。
2. **Arm reward**：pull arm $a$ 等价于从 clip $A_a$ 中采样一帧，观察 BLIP ITM relevance score $r_t$。
3. **Clip-level objective**：选择 top-$m$ arms，使 $\sum_{a\in S}\mu_a$ 最大，其中 $\mu_a$ 是该 clip 的 expected relevance。
4. **Confidence radius**：每个 arm 维护 empirical mean $\hat{\mu}_a(n)$、sample count $N_a(n)$ 与 empirical variance $\hat{\sigma}_a^2$，并计算 Bernstein-style radius：

$$
\beta_a(n)=\sqrt{\frac{2\hat{\sigma}_a^2\ln n}{\max(1,N_a(n))}}+\frac{3\ln n}{\max(1,N_a(n))}.
$$

5. **Optimism**：coarse stage 用 $\hat{\mu}_a+\beta_a$ 选 high-potential arms；fine stage 对这些 arms 追加采样，最终用 unbiased empirical means $\hat{\mu}_a$ 选 top-$m$ arms。
6. **Frame selection**：在选中的 arms 内，对 observed rewards 做 nearest-neighbor interpolation，按 interpolated rewards 构造 sampling distribution，并 without replacement 抽取最终 keyframes。

紧凑伪代码：

```text
Input: video V, query q, target keyframes K, clip length l, top arms m, coarse pulls q, fine pulls z, expansion alpha
Partition V into clips A_1 ... A_M
For every arm A_a:
  sample q frames and compute BLIP relevance rewards
  estimate mean, variance, and Bernstein radius beta_a
Select coarse arms by TopM(mean_a + beta_a, alpha * m)
For every coarse arm:
  sample z additional frames and update empirical mean
Select final arms by TopM(mean_a, m)
Within final arms:
  interpolate frame rewards and sample K keyframes without replacement
Return selected keyframes to downstream MLLM
```

## Pipeline Figure

![[assets/pipeline_2510.27280.png]]

Caption: Overview of FOCUS. FOCUS partitions videos into fixed-length clips as bandit arms, applies optimistic confidence upper-bound arm selection, and selects final keyframes within each promising arm.

Source: TeX includegraphics from `sections/methodv2.tex`, resolved to `figures/framework_v7.pdf`; converted to PNG with `pdftoppm -cropbox`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| LongVideoBench | Long-video multiple-choice QA | 论文沿用 LMMs-Eval 与 AKS protocol | Accuracy (%) | 禁用 subtitles，zero-shot，model frozen；长度桶中 Long 定义为 >20 min。 |
| Video-MME | Video multiple-choice QA | 原始 Short / Medium / Long categorization | Accuracy (%) | Short <2 min，Medium 4-15 min，Long 30-60 min。 |
| MLVU | Multi-task long-video understanding | Appendix additional benchmark | Accuracy (%) | 1,730 long videos，覆盖 movies、surveillance、egocentric recordings、cartoons、game videos。 |
| VSI-Bench | Video spatial intelligence QA | Appendix additional benchmark | Accuracy (%) | 288 egocentric indoor videos，>5,000 QA pairs，强调 spatial layout、navigation、distance estimation。 |

### Main Results

Video-question answering accuracy (%)；作者加粗的是 paired setting 中使用 FOCUS 的结果。

| Model | #Frame | LLM | LongVideoBench | Video-MME |
| --- | ---: | --- | ---: | ---: |
| GPT-4V | 256 | -- | 61.3 | 59.9 |
| Gemini-1.5-Flash | 256 | -- | 61.6 | 70.3 |
| Gemini-1.5-Pro | 256 | -- | 64.0 | 75.0 |
| VideoLLaVA | 8 | 7B | 39.1 | 39.9 |
| MiniCPM-V 2.6 | 64 | 8B | 54.9 | 60.9 |
| InternVL2-40B | 16 | 40B | 59.7 | 61.2 |
| LLaVA-Video-72B | 64 | 72B | 63.9 | 70.6 |
| GPT-4o | 32 | -- | 51.6 | 61.8 |
| GPT-4o w/ Ours | 32 | -- | **54.8** (+3.2) | **62.5** (+0.7) |
| Qwen2-VL-7B | 32 | 7B | 55.6 | 57.4 |
| Qwen2-VL-7B w/ Ours | 32 | 7B | **62.3** (+6.7) | **59.7** (+2.3) |
| LLaVA-OV-7B | 32 | 7B | 54.8 | 56.5 |
| LLaVA-OV-7B w/ Ours | 32 | 7B | **60.7** (+5.9) | **58.3** (+1.8) |
| LLaVA-Video-7B | 64 | 7B | 58.9 | 64.4 |
| LLaVA-Video-7B w/ Ours | 64 | 7B | **63.5** (+4.6) | **65.4** (+1.0) |

与 state-of-the-art training-free keyframe selection methods 的比较；使用 LLaVA-Video-7B，固定 $k=64$ keyframes。

| Method | LongVideoBench Short | LongVideoBench Medium | LongVideoBench Long | LongVideoBench Overall | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uniform | 67.5 | 57.4 | 51.8 | 58.9 | 76.4 | 62.6 | 54.3 | 64.4 |
| Top-$K$ | **72.3** | 58.0 | 60.5 | 62.3 | 75.4 | 60.4 | 53.0 | 62.9 |
| AKS | **72.3** | **59.2** | 56.1 | 62.1 | 76.3 | 62.8 | 54.7 | 64.6 |
| **FOCUS (ours)** | **72.3** | 59.0 | **63.7** | **63.5** | **76.5** | **63.5** | **56.1** | **65.4** |

效率比较；LongVideoBench 上使用 single NVIDIA H100 (80GB)。

| Method | Filtering-free | Frames Seen (%) | GPU hours |
| --- | --- | ---: | ---: |
| AKS w/o pre-filtering | No | 100 | 255 |
| AKS w/ pre-filtering | No | 3.7 | 9.3 |
| **FOCUS (Ours)** | Yes | 1.6 | 5.5 |

Efficiency-accuracy trade-off；$\alpha$ 控制进入 fine-grained exploration 的 arms fraction。

| Setting | Accuracy (%) | Frames Seen (%) | GPU hours |
| --- | ---: | ---: | ---: |
| $\alpha=0.1$ | 62.9 | 1.1 | 3.5 |
| $\alpha=0.25$ | 63.5 | 1.6 | 5.5 |
| $\alpha=0.5$ | 63.6 | 2.5 | 9.2 |

Appendix 中对 AKS 与 Q-Frame 的更完整比较：

| Model | #Frame | LLM | LongVideoBench | Video-MME |
| --- | ---: | --- | ---: | ---: |
| Qwen2-VL-7B | 32 | 7B | 55.6 | 57.4 |
| Qwen2-VL-7B w/ AKS | 32 | 7B | 57.8 | **59.7** |
| Qwen2-VL-7B w/ Q-Frame | 32 | 7B | 57.4 | 56.5 |
| Qwen2-VL-7B w/ Ours | 32 | 7B | **62.3** (+6.7) | **59.7** (+2.3) |
| LLaVA-OV-7B | 32 | 7B | 54.8 | 56.5 |
| LLaVA-OV-7B w/ AKS | 32 | 7B | 57.4 | 57.7 |
| LLaVA-OV-7B w/ Q-Frame | 32 | 7B | 54.8 | 56.8 |
| LLaVA-OV-7B w/ Ours | 32 | 7B | **60.7** (+5.9) | **58.3** (+1.8) |
| LLaVA-Video-7B | 64 | 7B | 58.9 | 64.4 |
| LLaVA-Video-7B w/ AKS | 64 | 7B | 62.1 | 64.6 |
| LLaVA-Video-7B w/ Q-Frame | 64 | 7B | 59.9 | 64.5 |
| LLaVA-Video-7B w/ Ours | 64 | 7B | **63.5** (+4.6) | **65.4** (+1.0) |

Additional benchmarks:

| Model | #Frame | LLM | MLVU | VSI-Bench |
| --- | ---: | --- | ---: | ---: |
| Qwen2-VL-7B | 32 | 7B | 59.7 | 36.5 |
| Qwen2-VL-7B w/ AKS | 32 | 7B | 64.3 | 36.9 |
| Qwen2-VL-7B w/ Ours | 32 | 7B | **67.0** (+6.7) | **39.0** (+2.5) |
| LLaVA-Video-7B | 64 | 7B | 68.2 | 41.7 |
| LLaVA-Video-7B w/ AKS | 64 | 7B | 71.2 | 42.2 |
| LLaVA-Video-7B w/ Ours | 64 | 7B | **72.7** (+4.5) | **42.4** (+0.7) |

### Ablations / Analysis

Two-stage exploration-exploitation ablation；LongVideoBench accuracy (%)。

| Backbone | Uniform | FOCUS-C | FOCUS-F | FOCUS |
| --- | ---: | ---: | ---: | ---: |
| Qwen2-VL | 55.6 | 61.7 | 61.5 | **62.3** |
| LLaVA-OV | 54.8 | 58.4 | 57.7 | **60.7** |
| LLaVA-Video | 58.9 | 62.3 | 62.5 | **63.5** |

其中 FOCUS-C 只做 coarse exploration，FOCUS-F 只做 fine-grained exploration；完整 FOCUS 说明 coarse localization 与 fine refinement 是互补的。

Bernstein confidence radius ablation；LongVideoBench accuracy (%)。

| Backbone | Uniform | FOCUS-M | FOCUS |
| --- | ---: | ---: | ---: |
| Qwen2-VL | 55.6 | 61.7 | **62.3** |
| LLaVA-OV | 54.8 | 58.1 | **60.7** |
| LLaVA-Video | 58.9 | 63.0 | **63.5** |

FOCUS-M 仅用 empirical mean rank arms；完整 FOCUS 用 Bernstein radius 形成 variance-aware UCB，对 high-variance clips 更稳。

Clip length ablation；LongVideoBench with LLaVA-Video-7B。

| Metric | Uniform | 8s | 16s | 32s |
| --- | ---: | ---: | ---: | ---: |
| ACC | 58.9 | 63.7 | 63.5 | 62.3 |
| GPU hours | -- | 8.1 | 5.5 | 4.1 |

Vision-language encoder ablation；LongVideoBench with LLaVA-Video-7B。

| Metric | Uniform | CLIP | SigLIP | BLIP |
| --- | ---: | ---: | ---: | ---: |
| ACC | 58.9 | 60.2 | 60.9 | 63.5 |

### Training / Compute

| Item | Value |
| --- | --- |
| Frame relevance model | BLIP ITM in main experiments |
| Evaluation framework | LMMs-Eval protocol, following AKS open-source setup |
| Model setting | Zero-shot evaluation; model parameters frozen |
| Subtitle setting | Subtitles disabled for fair comparison |
| Downstream MLLMs | GPT-4o (0513), Qwen2-VL-7B, LLaVA-OV-7B, LLaVA-Video-7B; reference rows include GPT-4V, Gemini, VideoLLaVA, MiniCPM-V, InternVL2, LLaVA-Video-72B |
| Keyframe budget | 32 frames for GPT-4o / Qwen2-VL / LLaVA-OV; 64 frames for LLaVA-Video in main comparisons |
| SOTA comparison protocol | LLaVA-Video-7B, fixed $k=64$, same or comparable vision-language scoring model |
| Efficiency hardware | Single NVIDIA H100 (80GB) |
| Code | https://github.com/NUS-HPC-AI-Lab/FOCUS |

## Limitations & Caveats

- 论文明确假设 frame-query relevance scores 在 arm 内近似 i.i.d.，但真实视频存在 temporal dependency；相邻片段之间可能强相关，导致 classic CPE bandit 假设不完全成立。
- 作者指出可以进一步用 Lipschitz / metric bandits 或 contextual bandits 建模 temporal structure，这也是未来方向。
- Video-MME 的收益小于 LongVideoBench；论文解释为 Video-MME query 更偏 global understanding，信息帧更分散，因此 query-localized selection 的优势较弱。
- VSI-Bench 上增益也较小；短视频或低冗余 egocentric spatial reasoning 场景中，uniform sampling 已能覆盖较多有效信息。
- FOCUS 仍依赖 BLIP / CLIP / SigLIP 等 frame-query scoring model 的质量；如果 scorer 不擅长目标 query 或视觉细节，keyframe selection 可能受限。
- 论文主要报告 accuracy 与 keyframe selection cost；对 end-to-end latency、memory、不同 video fps/codec 的工程影响没有展开。

## Concrete Implementation Ideas

1. 在现有 Video-LLM inference pipeline 前加一个 `KeyframeSelector`：输入 decoded frame iterator 与 query，输出 selected frame indices；下游 MLLM 不需要改结构。
2. 默认配置可从论文的 practical setting 起步：clip length $l=16s$、$\alpha=0.25$、BLIP ITM scoring；如果预算更紧，用 $\alpha=0.1$ 换取更低 cost。
3. 对 streaming 或超长视频，先按时间生成 arms metadata，只对 sampled frames 做 decode + BLIP forward，避免把所有 frames 解码到内存。
4. 对 global queries 增加 diversity regularization 或 temporal coverage floor，避免 top arms 过度集中；这可以作为 FOCUS 与 AKS 思路的混合变体。
5. 用 cached frame embeddings / relevance scores 支持多 query 复用：同一视频多问题场景下，vision embedding 可缓存，query text embedding 和 similarity 可快速重算。

## Open Questions / Follow-ups

- 如果把 arm reward 从单帧 relevance 改成多帧 complementary utility，是否能更好处理需要跨片段推理的问题？
- Temporal dependency 是否可以通过 metric bandit / Gaussian process bandit / contextual bandit 明确建模，而仍保持 batched GPU-friendly？
- FOCUS 在字幕、多模态音频、或 ASR transcript 与 visual frames 联合选择场景中如何扩展？
- BLIP 在细粒度 action、spatial relation、OCR 等 query 上可能不是最优 scorer；是否可以用 task-adaptive scorer 或 MLLM hidden states 做 relevance？
- 论文报告的 GPU hours 是 selection cost；真实服务中加上 video decode、network I/O、batch scheduling 后，端到端 latency 曲线会怎样？

## Citation

```bibtex
@misc{zhu2025focus,
  title = {FOCUS: Efficient Keyframe Selection for Long Video Understanding},
  author = {Zhu, Zirui and Xu, Hailun and Luo, Yang and Liu, Yong and Sarkar, Kanchan and Yang, Zhenheng and You, Yang},
  year = {2025},
  eprint = {2510.27280},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2510.27280}
}
```
