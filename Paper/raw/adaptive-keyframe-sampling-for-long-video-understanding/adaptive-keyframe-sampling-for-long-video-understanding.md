---
title: (frame)AKS
authors:
  - Xi Tang
  - Jihao Qiu
  - Lingxi Xie
  - Yunjie Tian
  - Jianbin Jiao
  - Qixiang Ye
conference: CVPR 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2502.21271
pdf_link: "[[assets/paper_2502.21271.pdf]]"
cover: "[[assets/pipeline_2502.21271.png]]"
updated: 2026-05-18
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - question-aware
  - temporal-reasoning
  - video-llm
  - token-pruning
status: read
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/ncTimTang/AKS
---

## TL;DR

- 论文提出 Adaptive Keyframe Sampling (AKS)，把 long video MLLM 前面的 frame sampling 变成 question-aware 的 keyframe selection，而不是默认 uniform sampling。
- 核心思想是同时优化两件事：keyframe 与 prompt 的 relevance，以及 keyframes 对整段视频时间轴的 coverage。
- AKS 里的默认策略 ADA 会根据 score 分布递归决定“继续二分覆盖”还是“直接取高分帧”，在 TOP 和 BIN 两类极端策略之间自适应折中。
- 在 LongVideoBench val 和 VideoMME 上，AKS 能无训练地提升 Qwen2-VL、LLaVA-OV、LLaVA-Video 三个 baseline；LLaVA-Video-7B w/ AKS 达到 62.7% / 65.3%。
- 结果说明：对 long video MLLM 来说，视觉 token 数量固定时，输入帧的信息预过滤质量本身就是关键瓶颈。

## Key Contributions

- 提出一个 plug-and-play 的 keyframe selection 模块 AKS，可以直接插入现有 video-based MLLM 的 visual encoder 之前，不需要微调目标 MLLM。
- 将 keyframe selection 表述为 relevance 与 coverage 的联合优化：relevance 衡量 frame 是否有助于回答当前问题，coverage 避免 keyframes 过度集中在少数时间段。
- 设计 ADA (adaptive sampling)：用递归 judge-and-split 近似优化目标，使采样策略能在集中检索 single moment 与覆盖 multiple moments 之间切换。
- 在 LongVideoBench 和 VideoMME 上系统比较 UNI、TOP、BIN、ADA，并验证 frame sampling 频率、VL scorer、ADA 超参数对效果的影响。
- 展示 AKS 对 video referring 与 captioning 的定性迁移能力，强调 question-aware visual pre-filtering 可能是 long video understanding 的通用前处理方向。

## Method

给定视频 $\mathbf{V}\in\mathbb{R}^{T\times W\times H\times C}$ 与文本 prompt $\mathbf{Q}$，论文把每一帧 $\mathbf{V}_t$ 经过预训练视觉编码器得到 visual tokens $\mathbf{F}_t$。目标 MLLM 的视觉上下文容量有限，因此只能选择 $M$ 个 keyframes：

$$
\mathrm{KS}_M(\mathbf{Q},\mathbf{F})=\arg\max_{|\mathcal{I}|=M}G'(\{\mathbf{F}_t\mid t\in\mathcal{I}\})
$$

这里 $G'(\cdot)$ 表示 MLLM 对输出的隐式置信度，但它不可直接优化。论文用两个可计算因素近似：

$$
\mathrm{KS}_M(\mathbf{Q},\mathbf{F})=\arg\max_{|\mathcal{I}|=M}\sum_{t\in\mathcal{I}}s(\mathbf{Q},\mathbf{F}_t)+\lambda\cdot c(\mathcal{I})
$$

- Relevance：$s(\mathbf{Q},\mathbf{F}_t)$ 用较轻量的 VL model 计算。实验默认使用 BLIP 的 image-text matching (ITM)，也 ablate 了 CLIP 与 Sevila。
- Coverage：$c(\mathcal{I})$ 用递归时间 bin 来近似，思想来自 Ripley's $K$-function。若 keyframes 在某层二分后的 bins 中分布过于不均，coverage 较弱。
- 三个基础策略：UNI 是 uniform sampling；TOP 忽略 coverage，只取最高 $M$ 个 relevance scores；BIN 强制覆盖 bins，在每个 bin 内取高分帧。
- ADA 是默认策略。它在每个 segment 内比较 $s_\mathrm{top}-s_\mathrm{all}$ 与阈值 $s_\mathrm{thr}$：若高分帧显著突出，就直接保留该段 top frames；否则继续二分以增强 temporal coverage。

紧凑伪代码如下：

```text
Input: matching_scores, max_level L, threshold s_thr, target frame count M
segments = [matching_scores]
for level in 0..L:
    next_segments = []
    frozen_segments = []
    for segment in segments:
        s_all = mean(segment)
        s_top = mean(top_M_scores(segment))
        if s_top - s_all >= s_thr:
            frozen_segments.append(segment)
        else:
            next_segments.extend(split_center(segment))
    segments = frozen_segments + next_segments
select frames from final segments proportionally by segment length, using top scores inside each segment
return selected frame indices
```

## Pipeline Figure

![[assets/pipeline_2502.21271.png]]

Caption: The overall framework of our approach. We insert a plug-and-play module, Adaptive Keyframe Sampling (AKS, marked in green frames) into the MLLM to improve the quality of sampled keyframes. Each red dot indicates a prompt-frame matching score ($s(\mathbf{Q},\mathbf{F}_t)$). AKS follows a recursive, judge-and-split optimization for keyframe selection.

Source: TeX includegraphics from `main.tex`, rendered from `fig/figure2_method_qjh.pdf` with `pdftoppm -cropbox`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| LongVideoBench (LVB) | Long-video multiple-choice QA | val | Accuracy (%) | 视频长度可超过 1 小时；实验不使用 subtitles，以聚焦视觉理解与 keyframe quality。 |
| VideoMME (V-MME) | Long-video multiple-choice QA | not reported | Accuracy (%) | 实验同样不使用 subtitles；作者认为其问题更常需要 multi-moment evidence。 |

### Main Results

作者在三类 baseline MLLM 上插入 AKS。下表保留论文原始 emphasis；灰色 proprietary models 在 TeX 中以 italic 标示，这里用同样的斜体表达。

| Method | Frames | LLM | LVB val acc. (%) | V-MME acc. (%) |
| ---- | ---- | ---- | ---- | ---- |
| *GPT-4V* | *256* | *--* | *61.3* | *59.9* |
| *GPT-4o* | *256* | *--* | *66.7* | *71.9* |
| *Gemini-1.5-Flash* | *256* | *--* | *61.6* | *70.3* |
| *Gemini-1.5-Pro* | *256* | *--* | *64.0* | *75.0* |
| VideoLLaVA | 8 | 7B | 39.1 | 39.9 |
| MiniCPM-V 2.6 | 64 | 8B | 54.9 | 60.9 |
| PLLaVA | 32 | 34B | 53.2 | - |
| VILA | - | 40B | - | 60.1 |
| Qwen2-VL | 32 | 7B | 55.5 | 57.6 |
| **Qwen2-VL w/ AKS** | 32 | 7B | **60.5** | **59.9** |
| LLaVA-OV | 32 | 7B | 54.8 | 56.5 |
| **LLaVA-OV w/ AKS** | 32 | 7B | **59.3** | **58.4** |
| LLaVA-Video | 64 | 7B | 58.9 | 64.4 |
| **LLaVA-Video w/ AKS** | 64 | 7B | **62.7** | **65.3** |

在 strong baseline LLaVA-Video-7B 上，AKS 带来 +3.8% LVB val 与 +0.9% VideoMME。论文特别指出，LLaVA-Video-7B w/ AKS 在 LongVideoBench 上比 LLaVA-Video-72B without AKS 高 0.8%，也高于使用 256 frames 的 GPT-4V 与 Gemini-1.5-Flash。

### Ablations / Analysis

不同 sampling strategies 的诊断实验使用 LLaVA-Video-7B：

| Sampling | LongVideoBench val acc. (%) | VideoMME acc. (%) |
| ---- | ---- | ---- |
| **UNI** | 58.9 | 64.4 |
| **TOP** | 62.4 | 63.7 |
| **BIN** | 60.2 | 65.2 |
| **ADA** | **62.7** | **65.3** |

作者解释：LongVideoBench 中很多问题集中在 single moment，TOP 常能找到局部关键帧；VideoMME 更常需要 multiple moments，BIN 的覆盖性更稳。ADA 吸收两者优点，因此两个 benchmark 都最好。

Sampling frequency ablation。每个候选帧先由 VL scorer 打分；降低 fps 会减少预过滤成本：

| Dataset | Frames of MLLM | 1 fps | 0.5 fps | 0.25 fps | 0.125 fps | 0.1 fps |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LongVideoBench val | 16 | **61.6** | 60.7 | 60.6 | 61.1 | 59.4 |
| LongVideoBench val | 32 | 61.9 | **62.1** | 59.8 | 60.2 | 58.5 |
| LongVideoBench val | 64 | **62.7** | 62.2 | 61.8 | 60.1 | 60.1 |
| VideoMME | 16 | 62.2 | **63.0** | 62.2 | 61.0 | 61.6 |
| VideoMME | 32 | 64.6 | 64.7 | **65.1** | 64.4 | 64.4 |
| VideoMME | 64 | **65.3** | 65.1 | 64.9 | 64.0 | 64.2 |

VL scorer ablation。不同 benchmark 对 scorer 的偏好不同：

| Dataset | Frames | Uniform | BLIP | Sevila | CLIP |
| ---- | ---- | ---- | ---- | ---- | ---- |
| LongVideoBench val | 16 | 57.4 | **61.6** | 59.2 | 60.2 |
| LongVideoBench val | 32 | 57.9 | **61.9** | 60.9 | **61.9** |
| LongVideoBench val | 64 | 58.9 | **62.7** | 61.5 | 62.2 |
| VideoMME | 16 | 60.6 | 62.2 | 63.0 | **63.1** |
| VideoMME | 32 | 63.9 | 64.6 | 63.7 | **65.0** |
| VideoMME | 64 | 64.4 | 65.3 | 65.1 | **65.6** |

论文认为 BLIP 在 LongVideoBench 更好，可能因为该 benchmark 更偏 object-level questions；CLIP 在 VideoMME 更好，可能因为其 generic image-text pretraining 更适合 global perception。

ADA hyper-parameters。每格为 `LVB / V-MME` accuracy (%)；表中 `62.6/54.5` 按 TeX 原文保留，数值看起来异常但未改写。

| $L \backslash s_\mathrm{thr}$ | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 1 | 62.4/63.8 | 62.4/64.0 | 62.5/64.2 | 62.0/64.1 | 61.8/63.8 | 61.9/64.0 |
| 2 | 62.4/63.8 | 62.0/64.0 | 62.4/64.0 | 61.8/63.5 | 61.7/63.4 | 62.0/63.6 |
| 3 | 62.4/63.8 | **62.8**/64.0 | 62.6/54.5 | 62.1/64.4 | 62.2/64.4 | 62.1/64.4 |
| 4 | 62.4/63.8 | 62.7/64.1 | 62.7/64.3 | 62.2/64.9 | 62.1/65.0 | 62.2/65.0 |
| 5 | 62.4/63.8 | 62.7/64.1 | 62.2/64.7 | 61.7/65.0 | 61.3/**65.3** | 61.7/65.2 |
| 6 | 62.4/63.8 | 62.7/64.0 | 62.3/64.5 | 61.8/65.0 | 61.3/65.1 | 61.4/65.1 |

作者总结：LongVideoBench 偏好较小的 $L$ 与 $s_\mathrm{thr}$，VideoMME 偏好更强的 coverage 设定，原因是前者关键证据更集中，后者更依赖多时刻信息。

### Training / Compute

| Item | Value |
| ---- | ---- |
| Target MLLMs | Qwen2-VL, LLaVA-OV, LLaVA-Video |
| Strongest baseline setting | LLaVA-Video uses SigLIP vision encoder and Qwen2-7B LLM |
| MLLM input frames | 32 or 64 for main tested open models |
| Candidate frame sampling | Default 1 frame per second from raw video |
| Default relevance scorer | BLIP image-text matching (ITM) |
| Alternative scorers | CLIP, Sevila |
| Tuning target MLLM | No tuning; only replace input frames with AKS-selected frames |
| Subtitles | Not used in LongVideoBench / VideoMME evaluation |

## Limitations & Caveats

- AKS 是 heuristic optimization，不直接监督 keyframe quality，也不真正优化目标 MLLM 的 confidence $G'(\cdot)$。
- Relevance 依赖外部 VL scorer；不同 scorer 在不同 benchmark 上表现不同，说明 scorer-domain mismatch 仍会影响采样质量。
- Coverage 用时间轴二分近似，不等价于 semantic coverage；重复动作、稀疏事件或复杂叙事结构可能让时间覆盖与信息覆盖不一致。
- 主要量化实验集中在 multiple-choice QA 的 LongVideoBench 与 VideoMME；video referring 和 captioning 只给定性展示。
- AKS 带来额外预处理成本，需要对候选帧做 VL scoring；虽然低 fps ablation 显示可以降采样，但真实部署仍要权衡 latency 与准确率。
- ADA 的 $L$ 和 $s_\mathrm{thr}$ 存在 dataset preference，不同任务可能需要自动或验证集驱动的参数选择。

## Concrete Implementation Ideas

1. 在 long-video QA pipeline 中把 AKS 做成 visual pre-router：先按 0.25-1 fps 抽候选帧，缓存 frame embeddings，再按每个 question 动态选 $M$ 帧送入 Video-LLM。
2. 同时暴露 UNI / TOP / BIN / ADA 四个模式，记录所选 frame indices 与 relevance curve，方便 debug answer failure 是采样问题还是 MLLM reasoning 问题。
3. 针对 question type 自适应选择 scorer：object-centric questions 优先 BLIP，global/perception questions 可尝试 CLIP，或者 ensemble 两者的 normalized score。
4. 在同一视频多问题场景下复用候选帧 visual embeddings，只对 text prompt 侧重新计算 matching score，降低 batch QA 成本。
5. 将 AKS 与 token pruning 组合：先 question-aware 选关键帧，再在关键帧内做 visual token compression，形成两级压缩。

## Open Questions / Follow-ups

- 能否用 question type classifier 自动调节 TOP/BIN/ADA 的偏好，替代手动选择 $L$ 与 $s_\mathrm{thr}$？
- 如果使用更强但更贵的 MLLM-as-scorer，accuracy 与成本会如何变化？是否存在一个可接受的 distillation 路径？
- Coverage 是否应该从 temporal bins 升级到 semantic event clusters，尤其是面对重复动作和非线性叙事视频？
- 加入 subtitles / audio 后，AKS 是否仍然带来同样幅度的视觉增益，还是会被语言线索部分替代？
- 是否可以构建 human keyframe annotations 或 weak labels，用来评估 keyframe selection 本身，而不仅是最终 QA accuracy？

## Citation

```bibtex
@misc{tang2025adaptivekeyframesamplinglong,
  title = {Adaptive Keyframe Sampling for Long Video Understanding},
  author = {Tang, Xi and Qiu, Jihao and Xie, Lingxi and Tian, Yunjie and Jiao, Jianbin and Ye, Qixiang},
  year = {2025},
  eprint = {2502.21271},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2502.21271}
}
```
