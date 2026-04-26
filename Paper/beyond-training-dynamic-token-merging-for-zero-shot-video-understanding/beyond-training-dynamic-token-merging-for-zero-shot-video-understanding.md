---
title: "Beyond Training: Dynamic Token Merging for Zero-Shot Video Understanding"
authors:
  - Yiming Zhang
  - Zhuokai Zhao
  - Zhaorun Chen
  - Zenghui Ding
  - Xianjun Yang
  - Yining Sun
conference: ICCV 2025
year: 2024
arxiv_url: https://arxiv.org/abs/2411.14401
pdf_link: "[[assets/paper_2411.14401.pdf]]"
cover: "[[assets/pipeline_2411.14401.png]]"
updated: 2026-04-26
tags:
  - paper/arxiv
status: reading
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/Jam1ezhang/DYTO
datasets:
  - NExTQA
  - EgoSchema
  - IntentQA
  - VideoMME
  - MVBench
  - MSVD-QA
  - MSRVTT-QA
  - TGIF-QA
  - ANet-QA
  - Video-ChatGPT Generation
arxiv_version: v2
submitted: 2024-11-21
last_revised: 2025-03-24
doi: https://doi.org/10.48550/arXiv.2411.14401
---

## TL;DR

- DyTo 是一个 training-free 的 zero-shot video understanding 方法，目标是在不微调 image-based MLLM 的情况下，把长视频压缩成更有信息密度的视觉 token 序列。
- 核心做法是两级压缩：先用每帧的 `[CLS]` token 做 coarse-grained hierarchical clustering 选关键帧，再对每个关键帧做 fine-grained dynamic bipartite token merging。
- 相比 IG-VLM 和 SlowFast-LLaVA，DyTo 不是固定均匀采样少量帧，也不是简单 pooling，而是根据视频内容动态决定 frame cluster 和 token merge。
- 主表显示 DyTo 在 structured VQA 的多个模型尺寸上普遍优于 training-free baselines；34B setting 下 NExTQA 72.9、EgoSchema 56.8、VideoMME 53.4、MVBench 52.9。
- Open-ended VQA 的结果更混合：DyTo 在 VCG Average、TGIF-QA、ANet-QA 上较强，但 MSVD-QA / MSRVTT-QA 并非所有 setting 都优于 best baseline。
- 代价方面，appendix 报告在 EgoSchema 500 samples、LLaVA-NeXT-34B、<font color="#d83931">单张 A100 上 DyTo 为 6.22 s/item，SlowFast-LLaVA 为 5.74 s/item，略慢但同量级。</font>

## Key Contributions

1. 提出 DyTo，一种不需要 video fine-tuning 的 dynamic token merging framework，用 image-based MLLM 处理视频任务。
2. 用 hierarchical clustering 在时间维度上动态分割视频：基于每帧 `[CLS]` token 的语义距离与时间距离构建 1-NN temporal graph，再通过 connected components 和递归合并得到 frame clusters。
3. 用 dynamic bipartite token merging 替代简单 pooling：把每帧 patch tokens 分为两个集合，按 multi-head cosine similarity 找 top pairs 并 merge，从而在固定 visual token budget $Z$ 下尽量保留语义细节。
4. 在 structured VQA 与 open-ended VQA 上做较大范围评测，覆盖 10+ benchmarks、三类模型系列、多个模型尺寸，并与 fine-tuned models 和 training-free approaches 比较。
5. 通过 ablation、video length analysis、clustering visualization 和 time consumption experiment 分析 clustering 与 token merging 的作用。

## Method

DyTo 的 pipeline 可以理解为：

1. 对视频均匀采样 $N = 100$ frames。
2. 每帧经过 visual encoder，得到 visual tokens $V \in \mathbb{R}^{N \times L \times D}$，其中包含 `[CLS]` token。
3. 收集每帧 `[CLS]` token，作为 frame-level coarse representation。
4. 构建 temporally weighted distance matrix：

$$
W_t(i, j) =
\begin{cases}
\left(1 - \langle v_i, v_j \rangle\right)\frac{|t_i - t_j|}{N}, & i \ne j \\
1, & i = j
\end{cases}
$$

5. 保留每个节点最近邻，构建 1-NN graph；再对称化 $G(j, i)=1$，用 connected components 得到 clusters，并递归合并 cluster。论文选择多个 clustering results 中的 second-largest one 作为最终 segmentation。
6. 从每个 cluster 采样 frames，得到 keyframe sequence $V_s$。
7. 对每个 keyframe 的 patch tokens 做 dynamic bipartite merging：把 tokens 分成 $P$ 和 $Q$ 两个不重叠集合，用 multi-head cosine similarity 找 top-$r_i$ pairs，再通过 pooling 合并。
8. merge ratio 由 visual token budget 控制；论文写作中给出 $r_i = R_0 - Z/K$，直觉上是让每个 cluster / selected frame 保留约 $Z/K$ 个视觉 token。原文关于最终 feature shape 的符号表述略不清晰，但 figure caption 明确说最终 output length 由 $Z$ 控制。

直觉上，DyTo 同时解决两个问题：哪些帧值得保留，以及每帧里哪些 patch tokens 可以安全合并。前者避免固定采样错过关键事件，后者避免 pooling 过度破坏空间细节。

## Pipeline Figure

![[assets/pipeline_2411.14401.png|716]]

Caption: The overview of DyTo, a training-free model built upon image-based MLLM without any fine-tuning. Specifically, DyTo first divides the video into $K$ clusters using the `[CLS]` token. Then the dynamic bipartite merging module samples frames from each cluster and controls the final output length as $Z$, resulting in better balance between computational efficiency and semantic richness.

Source: TeX includegraphics from `sec/3_method.tex` -> `figures/overview.pdf`; converted to PNG with `pdftoppm` at 250 DPI.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---:|---|---|
| NExTQA | structured video question answering | not reported | acc. (%) | multiple-choice VQA |
| EgoSchema | structured video question answering | not reported | acc. (%) | appendix time experiment uses 500 samples |
| IntentQA | structured video question answering | not reported | acc. (%) | multiple-choice VQA |
| VideoMME | structured video question answering | w/o subs | acc. (%) | no subtitle setting, isolates visual/temporal cues |
| MVBench | structured video question answering | not reported | acc. (%) | multiple-choice VQA |
| MSVD-QA | open-ended VQA | not reported | acc./score | free-form answer evaluation |
| MSRVTT-QA | open-ended VQA | not reported | acc./score | free-form answer evaluation |
| TGIF-QA | open-ended VQA | not reported | acc./score | free-form answer evaluation |
| ANet-QA | open-ended VQA | not reported | acc./score | ActivityNet-QA style open-ended VQA |
| Video-ChatGPT Generation | open-ended video dialogue generation | not reported | CI, DO, CU, TU, CO, Average | GPT-assisted evaluation; paper uses `GPT-3.5-Turbo-0125` |

### Main Results: Structured VQA

下表按原文 Table 1 的 training-free approaches 重排：左侧是 method / model setting，右侧是各 benchmark。DyTo 行为论文提出方法，因此数值加粗；fine-tuned models 的完整比较见原文 Table 1。

| Method | LVLM Size | Base Model | Frame Length | NExTQA acc. (%) | EgoSchema acc. (%) | IntentQA acc. (%) | VideoMME acc. (%) | MVBench acc. (%) |
|---|---:|---|---|---:|---:|---:|---:|---:|
| IG-VLM | 7B | LLaVA-NeXT-image | 6 | 63.1 | 35.8 | 60.1 | 39.8 | 41.3 |
| SlowFast | 7B | LLaVA-NeXT-image | 50 | 64.2 | 45.5 | 60.1 | 40.4 | 44.8 |
| **DyTo** | 7B | LLaVA-NeXT-image | dynamic | **65.7** | **48.6** | **61.6** | **41.2** | **45.2** |
| IG-VLM | 8B | InternVL2 | 6 | 79.9 | 65.6 | 81.8 | 49.4 | 65.3 |
| SlowFast | 8B | InternVL2 | 50 | 77.2 | 60.7 | 79.8 | 48.0 | 57.0 |
| **DyTo** | 8B | InternVL2 | dynamic | **81.4** | **67.6** | **83.0** | **59.3** | **66.2** |
| IG-VLM | 9B | Qwen-VL-Chat | 6 | 53.2 | 24.8 | 51.4 | 26.5 | 32.0 |
| SlowFast | 9B | Qwen-VL-Chat | 50 | 48.4 | 17.6 | 45.1 | 22.1 | 31.7 |
| **DyTo** | 9B | Qwen-VL-Chat | dynamic | **53.4** | **26.0** | **51.7** | **27.4** | **34.3** |
| IG-VLM | 26B | InternVL2 | 6 | 80.6 | 56.0 | 83.1 | 50.8 | 66.4 |
| SlowFast | 26B | InternVL2 | 50 | 79.2 | 54.8 | 82.8 | 49.4 | 61.8 |
| **DyTo** | 26B | InternVL2 | dynamic | **81.1** | **59.2** | **83.6** | **53.0** | **68.1** |
| IG-VLM | 34B | LLaVA-NeXT-image | 6 | 70.9 | 53.6 | 65.3 | 52.0 | 48.4 |
| SlowFast | 34B | LLaVA-NeXT-image | 50 | 71.9 | 55.8 | 66.2 | 53.2 | 51.2 |
| **DyTo** | 34B | LLaVA-NeXT-image | dynamic | **72.9** | **56.8** | **67.5** | **53.4** | **52.9** |

### Main Results: Open-ended VQA

Open-ended 结果不如 structured VQA 那样单向压制。DyTo 对 VCG Average、TGIF-QA、ANet-QA 较稳定；但 MSVD-QA 和 MSRVTT-QA 中，best baseline 有时更高。

| Size | Method | MSVD-QA acc. | MSVD-QA score | MSRVTT-QA acc. | MSRVTT-QA score | TGIF-QA acc. | TGIF-QA score | ANet-QA acc. | ANet-QA score | VCG Average |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 7B | Best training-free baseline | 78.7 | 3.9 | 66.2 | 3.4 | 77.5 | 4.0 | 53.9 | 3.2 | 3.04 |
| 7B | **DyTo** | **77.6** | **3.9** | **64.1** | **3.4** | **78.0** | **4.0** | **54.3** | **3.2** | **3.16** |
| 34B | Best training-free baseline | 79.6 | 4.1 | 67.1 | 3.7 | 80.6 | 4.3 | 58.8 | 3.5 | 3.30 |
| 34B | **DyTo** | **79.6** | **4.1** | **66.2** | **3.6** | **80.7** | **4.2** | **59.0** | **3.5** | **3.32** |

### Ablations / Analysis

原文 ablation table 用 SlowFast、DyTo w/o Clustering、DyTo w/o Token Merge、DyTo 比较 clustering 与 token merging。注意：这个表中 7B VideoMME 的 DyTo 数值是 42.7，而主结果表中是 41.2，原文存在不一致。

| Method | Size | NExTQA | EgoSchema | IntentQA | VideoMME | MVBench |
|---|---:|---:|---:|---:|---:|---:|
| SlowFast | 7B | 64.2 | 45.5 | 60.1 | 40.4 | 44.8 |
| DyTo w/o Clustering | 7B | 65.6 | 47.8 | 61.4 | 42.3 | 44.8 |
| DyTo w/o Token Merge | 7B | 64.9 | 45.6 | 60.5 | 41.2 | 44.6 |
| **DyTo** | 7B | **65.7** | **48.6** | **61.6** | **42.7** | **45.2** |
| SlowFast | 34B | 71.9 | 55.8 | 66.2 | 53.2 | 51.2 |
| DyTo w/o Clustering | 34B | 73.2 | 55.8 | 66.8 | 52.5 | 52.7 |
| DyTo w/o Token Merge | 34B | 72.2 | 56.0 | 66.3 | 51.7 | 51.8 |
| **DyTo** | 34B | **72.9** | **56.8** | **67.3** | **53.4** | **52.9** |

主要解读：

- Token merging 和 clustering 对大多数 benchmark 都有正贡献。
- NExTQA 上 `DyTo w/o Clustering` 在 34B 反而高于 full DyTo；作者解释为 NExTQA clips 较短，clustering 的收益不明显。
- Video length analysis 显示视频越长，DyTo 相对 IG-VLM / SlowFast-LLaVA 的性能下降更缓，因为它可以按视频内容动态选帧和压缩 token。
- Clustering visualization 中，DyTo 更容易覆盖所有关键事件；IG-VLM 和 SlowFast-LLaVA 可能因为固定采样漏掉某些事件。

### Training / Compute

| Item | Value |
|---|---|
| Training | training-free; no video fine-tuning |
| Initial frames | $N = 100$ uniformly sampled frames |
| Visual token budget | $Z = 3680$ for 7B; $Z = 7200$ for 34B |
| Base model families | LLaVA-NeXT-image, InternVL2, Qwen-VL-Chat |
| Model sizes evaluated | 7B, 8B, 9B, 26B, 34B |
| Context extension | RoPE scaling factor 2; context length 4096 -> 8192 tokens |
| Open-ended evaluator | `GPT-3.5-Turbo-0125` following FreeVA |
| Reported hardware | evaluations could be conducted on a single NVIDIA A100 80GB; authors also use 8x A100 80GB server for acceleration |
| Time experiment | EgoSchema 500 samples, LLaVA-NeXT-34B, single NVIDIA A100 GPU |
| SlowFast-LLaVA latency | 5.74 s/item |
| DyTo latency | 6.22 s/item |

## Limitations & Caveats

- Open-ended VQA 并不是全面优于 baseline；表中 MSVD-QA / MSRVTT-QA 的 best baseline 有时高于 DyTo。
- 原文不同表格存在一个明显数值不一致：7B VideoMME 在主结果表是 41.2，在 ablation table 是 42.7。使用该结果时需要回看代码或 official benchmark logs。
- 方法依赖 visual encoder 输出 `[CLS]` token 和 patch token，并假设这些 token 在进入 LLM 前可被重新组织；对没有相似 token interface 的 VLM 架构，迁移性需要验证。
- 论文主要验证 VQA / video dialogue benchmarks；对 retrieval、dense captioning、streaming understanding 或 real-time deployment 的覆盖不足。
- Clustering 中选择 second-largest clustering result 是一个经验性 heuristic，论文没有给出很充分的失败案例分析。
- DyTo 虽然 training-free，但推理并非更快；appendix 显示在 A100 上比 SlowFast-LLaVA 略慢。

## Concrete Implementation Ideas

1. 把 DyTo 作为 video-to-token preprocessor 接到现有 image-based MLLM 前面，先在本地复现 $N=100,\ Z=3680/7200$ 的 token budget。
2. 在应用侧暴露 $Z$、最大 frames、cluster count 上限等参数，让用户在 latency 与 accuracy 之间选择 profile。
3. 对每个视频记录 cluster boundaries 和 selected keyframes，用可视化 dashboard 检查是否漏掉关键事件。
4. 与 uniform sampling、IG-VLM grid、SlowFast-style pooling 做同数据 A/B test，尤其关注长视频、事件密集视频、单一场景重复动作视频。
5. 如果用于生产，先加 fallback：当 clustering 产生过少 cluster 或相邻 cluster 高度相似时，退回 uniform + lightweight merge。

## Open Questions / Follow-ups

- `second-largest` clustering result 对单事件视频、重复动作视频、镜头快速切换视频是否稳定？
- $Z/K$ 的分配是否应该按 cluster importance 自适应，而不是所有 cluster 平均分配 token budget？
- 如果视觉编码器没有稳定的 `[CLS]` token，是否可以用 mean pooled patch token 或 learned summary token 替代？
- Open-ended VQA 使用 `GPT-3.5-Turbo-0125` 评估，换成 GPT-4.x 或人工评估后排序是否保持？
- DyTo 与 memory bank / streaming video methods 结合时，token merging 应该发生在 frame-level、segment-level 还是 memory-level？

## Citation

```bibtex
@misc{zhang2024beyondtrainingdynamictokenmerging,
  title = {Beyond Training: Dynamic Token Merging for Zero-Shot Video Understanding},
  author = {Yiming Zhang and Zhuokai Zhao and Zhaorun Chen and Zenghui Ding and Xianjun Yang and Yining Sun},
  year = {2024},
  eprint = {2411.14401},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  doi = {10.48550/arXiv.2411.14401},
  url = {https://arxiv.org/abs/2411.14401}
}
```

arXiv cite line: `arXiv:2411.14401v2 [cs.CV]`, submitted 2024-11-21, last revised 2025-03-24.
