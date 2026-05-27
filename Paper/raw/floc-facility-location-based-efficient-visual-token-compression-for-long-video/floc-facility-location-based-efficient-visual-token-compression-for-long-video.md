---
title: FLoC(token compression)
authors:
  - Janghoon Cho
  - Jungsoo Lee
  - Munawar Hayat
  - Kyuwoong Hwang
  - Fatih Porikli
  - Sungha Choi
conference: ICLR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2511.00141
pdf_link: "[[assets/paper_2511.00141.pdf]]"
cover: "[[assets/pipeline_2511.00141.png]]"
updated: 2026-05-19
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - token-pruning
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- FLoC 是一个面向 long video understanding 的 visual token compression 框架，用 facility location function 在给定 token budget 下选择既 representative 又 diverse 的视觉 token 子集。
- 方法本身 training-free、model-agnostic、query-agnostic，可以作为 plug-and-play 模块接到 Qwen2.5-VL、InternVL3 等 video-LMM 的视觉 token 输入前。
- 核心优化目标是 $f(S)=\sum_{v\in V}\max_{u\in S}\mathrm{sim}(v,u)$；作者用 lazy greedy 利用 submodularity 减少 marginal gain 的重复计算，同时保留 greedy 的近似选择质量。
- 在 Video-MME、MLVU、LongVideoBench、EgoSchema 上，FLoC 在 $2^{-3}$、$2^{-4}$、$2^{-5}$ 压缩比下整体优于 LongVU、DivPrune、DyCoke、PruneVID、STTM、Scissor、FastVID 等压缩方法。
- 扩展到 1 FPS、最多 7200 frames 后，FLoC 让 Qwen2.5-VL-7B / 32B 在平均分上分别达到 67.03 / 70.63，超过 768-frame full-token 设置。
- 主要 caveat 是 block length $T$ 仍是经验超参；过短会造成 inter-block redundancy，过长会增加相似度计算开销。

## Key Contributions

- 把 long-video visual token selection 明确建模成 submodular facility location maximization：每个选中 token 不只是代表自身，而是覆盖整个 ground set 中与它相似的 token。
- 同时关注 representativeness 和 diversity：相比只保留 dense cluster center 的 clustering 方法，FLoC 更容易保留稀有但关键的视觉线索，例如小物体、短暂动作、局部细节。
- 用 lazy greedy 实现高效选择。算法维护候选 token 的 marginal gain upper bound，只在必要时重算 exact gain，从而避免 naive greedy 的大量重复评估。
- 设计为 training-free / model-agnostic / query-agnostic：不需要重训 compressor，也不依赖当前 query，因此可以一次压缩后复用压缩 token。
- 在多个 backbone 和 benchmark 上验证，包括 Qwen2.5-VL-7B、InternVL3-8B、Qwen2.5-VL-32B，以及 appendix 中的 Qwen2-VL 和 LLaVA-NeXT-Video。

## Method

FLoC 的输入是从视频中抽出的视觉 token 集合 $V=\{v_1,\dots,v_n\}$，目标是在预算 $K$ 下选出子集 $S\subseteq V, |S|\le K$。作者使用 facility location objective：

$$
S^*=\arg\max_{S\subseteq V, |S|\le K} f(S)
$$

$$
f(S)=\sum_{v\in V}\max_{u\in S}\mathrm{sim}(v,u)
$$

其中相似度默认是 cosine similarity：

$$
\mathrm{sim}(v,u)=\frac{v^\top u}{\|v\|\|u\|}
$$

直觉上，若某个候选 token 能覆盖许多原始 token，它的 marginal gain 会高；若它只重复已有选中 token 的信息，它的 marginal gain 会下降。由于 facility location 是 submodular，随着已选集合变大，新增 token 的边际收益满足 diminishing returns：

$$
f(A\cup\{v\})-f(A)\ge f(B\cup\{v\})-f(B),\quad A\subseteq B\subseteq V
$$

作者没有直接在全视频上一次性求解，而是把视频按 temporal block 切分，每个 block 内做 FLoC 选择，以控制计算量。选出的视觉 token 再与 text tokens 拼接后送入 video-LMM。

```text
Input: visual tokens V, token budget K
S <- empty set
For each token v in V:
  compute initial gain f({v})
  push v into priority queue Q by gain

While |S| < K:
  pop candidate v* with largest cached gain
  recompute exact marginal gain delta = f(S union {v*}) - f(S)
  if delta is still >= the largest cached gain in Q:
    add v* to S
  else:
    update v*'s priority to delta and push it back

Return S
```

## Pipeline Figure

![[assets/pipeline_2511.00141.png]]

Caption: Overview of the proposed framework for selecting a visual token subset. The method compresses visual tokens extracted by a visual encoder from input video sequences into a diverse and representative subset within a given budget, then concatenates selected visual tokens with text tokens for the video-LMM. It is training-free and model-agnostic, so it can be integrated plug-and-play into video-LMM workflows.

Source: TeX `\includegraphics` from `iclr2026_conference.tex`, rendered from `figures/Pipeline.pdf` with PDF crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| Video-MME | Video understanding / video QA | not reported | Accuracy | 覆盖 sports、news、user-generated content 等多域视频；包含长视频场景。 |
| MLVU | Multi-Level Video Understanding | not reported | Accuracy | 包含 Holistic LVU、Single Detail LVU、Multi Detail LVU；作者特别分析 Needle QA 和 Ego Reasoning。 |
| LongVideoBench (LVB) | Long-form video understanding | not reported | Accuracy | 覆盖 lectures、live events、surveillance footage 等长视频。 |
| EgoSchema | Egocentric video understanding | not reported | Accuracy | 第一人称短视频，强调 schema-level reasoning 和 activity prediction。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training | FLoC 本身 training-free；不训练 compressor。 |
| Evaluation toolkit | `lmms-eval` |
| Hardware | NVIDIA H100 GPUs with multiprocessing |
| Main backbones | Qwen2.5-VL-7B, InternVL3-8B |
| Extended temporal setting | Qwen2.5-VL vision processing modified from max 768 frames to max 7200 frames at 1 FPS |
| Default similarity | Cosine similarity |
| Key hyperparameter | Block length $T$，作者建议较大固定值如 $T=32$ 作为稳健默认值 |

### Main Results

下表摘录主实验中 FLoC 的逐数据集结果，并加入 full-token baseline 与每个压缩设置下按 Avg. 计算的最佳非 FLoC compressed baseline。LVB 指 LongVideoBench。

| Model | Comp. Ratio | Method / Setting | Video-MME | MLVU | LVB | EgoSchema | Avg. |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2.5-VL-7B | 1 | Full tokens | 66.33 | 70.31 | 60.51 | 61.40 | 64.64 |
| Qwen2.5-VL-7B | $2^{-3}$ | Best compressed baseline Avg. (DyCoke) | 62.11 | 67.53 | 55.12 | 59.60 | 61.09 |
| Qwen2.5-VL-7B | $2^{-3}$ | **FLoC (Ours)** | **63.33** | **68.81** | **58.12** | **60.00** | **62.57** |
| Qwen2.5-VL-7B | $2^{-4}$ | Best compressed baseline Avg. (FastVID) | 58.67 | 65.52 | 54.23 | 57.20 | 58.91 |
| Qwen2.5-VL-7B | $2^{-4}$ | **FLoC (Ours)** | **60.89** | **66.19** | **55.27** | 58.00 | **60.09** |
| Qwen2.5-VL-7B | $2^{-5}$ | Best compressed baseline Avg. (FastVID) | 57.19 | 62.94 | 52.95 | **55.00** | 57.02 |
| Qwen2.5-VL-7B | $2^{-5}$ | **FLoC (Ours)** | **58.63** | **64.08** | **53.10** | 54.00 | **57.45** |
| InternVL3-8B | 1 | Full tokens | 66.63 | 72.68 | 59.39 | 70.00 | 67.18 |
| InternVL3-8B | $2^{-3}$ | Best compressed baseline Avg. (LongVU) | 64.70 | 69.50 | 55.35 | 69.20 | 64.69 |
| InternVL3-8B | $2^{-3}$ | **FLoC (Ours)** | **64.93** | **71.57** | 56.69 | **69.40** | **65.65** |
| InternVL3-8B | $2^{-4}$ | Best compressed baseline Avg. (DyCoke) | 61.37 | 65.13 | 53.10 | **67.40** | 61.75 |
| InternVL3-8B | $2^{-4}$ | **FLoC (Ours)** | **63.41** | **69.09** | **56.47** | 66.20 | **63.79** |
| InternVL3-8B | $2^{-5}$ | Best compressed baseline Avg. (DivPrune) | **60.85** | 65.46 | 52.88 | 59.40 | 59.65 |
| InternVL3-8B | $2^{-5}$ | **FLoC (Ours)** | 60.81 | **66.93** | **54.23** | **63.80** | **61.44** |

作者的结论是：在所有压缩比和两个 main backbone 上，FLoC 的 Avg. 都是 compressed methods 中最高；个别单列指标上其他方法可能更高，例如 InternVL3-8B 的 $2^{-3}$ LVB 或 Qwen2.5-VL-7B 的 $2^{-5}$ EgoSchema。

### Extended Temporal Input

该实验把 Qwen2.5-VL 的 temporal input 扩展到 1 FPS、最多 7200 frames，再压缩到模型的 optimal visual token length。表中 768-frame row 是原始 full-token 设置。

| Model | Max Frames | Method | Video-MME | MLVU | LVB | Avg. |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2.5-VL-7B | 768 | Full tokens | **66.33** | 70.31 | 60.51 | 65.82 |
| Qwen2.5-VL-7B | 7200 | Best compressed baseline Avg. (DyCoke) | 65.78 | 71.30 | **62.98** | 66.69 |
| Qwen2.5-VL-7B | 7200 | **FLoC (Ours)** | 65.85 | **72.63** | 62.60 | **67.03** |
| Qwen2.5-VL-32B | 768 | Full tokens | 70.41 | 71.57 | 62.60 | 68.19 |
| Qwen2.5-VL-32B | 7200 | Best compressed baseline Avg. (TS-LLaVA) | 70.22 | 73.09 | 65.00 | 69.44 |
| Qwen2.5-VL-32B | 7200 | **FLoC (Ours)** | **71.56** | **73.83** | **66.49** | **70.63** |

相对 768-frame baseline，FLoC 在 Avg. 上分别提升 1.21 points (7B) 和 2.44 points (32B)。这支持作者的核心观点：不是简单少看帧，而是先看更多帧、再做高质量 token selection，可以让 video-LMM 获得更好的长视频理解输入。

### Computation

主文的 computation table 比较了 clustering-based baselines 与 FLoC 的平均 compression time。下面保留作者表中的 $T=32$ 三组时间和 Average Accuracy。

| Method | Time Complexity | Time @ $2^{-5}$, $T=32$ | Time @ $2^{-4}$, $T=32$ | Time @ $2^{-3}$, $T=32$ | Average Accuracy |
| ---- | ---- | ---- | ---- | ---- | ---- |
| K-Means | $O(n\cdot K\cdot d\cdot i)$ | 59.00 | 113.0 | 218.0 | 58.66 |
| K-Medoids | $O(K\cdot(n-K)^2)$ | 0.716 | 0.747 | 0.877 | 56.22 |
| Spectral Clustering | $O(n^3)$ | 5.160 | 9.650 | 21.10 | 58.97 |
| FLoC (Ours) | $O(n\cdot K)$ | **0.413** | **0.475** | **0.527** | **59.74** |

作者还在 appendix 中用 Qwen2.5-VL-7B、784 frames、12.5% compression ratio 做 profiling：FLoC compression time 为 0.99s，inference time 为 1.70s，peak VRAM 为 17.96GB。作者同时指出 FLoC 的 FLOPs 较高，主要来自 pairwise similarity computations。

### Ablations / Analysis

**Similarity metric.** 作者比较了 cosine similarity 和把 Euclidean distance 通过 Gaussian kernel 转成 similarity 的设置。表中原文把第一列写作 $T$，但取值对应压缩比。

| Compression Ratio | Metric | VideoMME | MLVU | LVB | EgoSchema | Average | Difference |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| $2^{-3}$ | Cosine | 64.93 | 71.57 | 56.69 | 69.40 | 65.65 | +0.55 for Euclidean |
| $2^{-3}$ | Euclidean | 64.26 | 72.26 | 58.49 | 69.80 | 66.20 |  |
| $2^{-4}$ | Cosine | 63.41 | 69.09 | 56.47 | 66.20 | 63.79 | -0.27 for Euclidean |
| $2^{-4}$ | Euclidean | 62.74 | 69.50 | 55.42 | 66.40 | 63.52 |  |
| $2^{-5}$ | Cosine | 60.81 | 66.93 | 54.23 | 63.80 | 61.44 | -0.97 for Euclidean |
| $2^{-5}$ | Euclidean | 59.59 | 65.59 | 53.70 | 63.00 | 60.47 |  |

低压缩强度下 Euclidean 略高，但压缩更激进时 cosine 更稳。因此作者选择 cosine similarity 作为 default。

**MLVU fine-grained sub-tasks.** Appendix 强调 FLoC 在 Needle QA 和 Ego Reasoning 这类细粒度任务上优势明显，因为这些任务经常依赖短暂出现的小物体或局部状态。

| Ratio | Method | NQA | ER | Overall |
| ---- | ---- | ---- | ---- | ---- |
| $2^{-5}$ | Best non-FLoC NQA row (DivPrune) | 68.45 | 54.55 | 59.43% |
| $2^{-5}$ | **FLoC (Ours)** | **71.27** | **56.25** | **61.22%** |
| $2^{-4}$ | Best non-FLoC NQA row (DivPrune) | 72.11 | 58.24 | 62.24% |
| $2^{-4}$ | **FLoC (Ours)** | **74.93** | **59.09** | **64.54%** |
| $2^{-3}$ | Best non-FLoC NQA row (DivPrune) | 74.08 | 60.80 | 65.00% |
| $2^{-3}$ | **FLoC (Ours)** | **76.06** | **62.22** | **67.43%** |

**Representativeness / diversity.** 作者用 50 个 Video-MME 视频和 Qwen2-VL-7B，比较 averaged sum coverage 与 averaged distance。FLoC 在归一化 scatter plot 中主要落在第一象限，表示相对其它算法同时更 representative 和更 diverse。

## Limitations & Caveats

- Block length $T$ 仍需要经验设置。短 block 便宜但会造成 inter-block redundancy；长 block 能覆盖更长 temporal context，但增加 token selection 计算。
- FLoC 是 query-agnostic，一次压缩后可复用，但也意味着它不会针对具体问题动态保留 query-relevant tokens；在极端问题驱动场景中，query-aware reranking 可能仍有价值。
- Appendix profiling 显示 FLoC compression time 实用，但 FLOPs 较高，主要来自 pairwise similarity matrix；在 edge device 上是否稳定实时，还需要更贴近部署的测试。
- 扩展到 7200 frames 的实验需要修改 Qwen2.5-VL vision processing；真实系统还要处理视频解码、frame sampling、feature cache、I/O 等端到端瓶颈。
- 实验主要用 benchmark accuracy 评价。对于 captioning、dense event detection、multi-turn video dialogue 等任务，压缩后的信息损失形态可能不同。

## Concrete Implementation Ideas

- 在现有 video-LMM pipeline 中，把 FLoC 放在 visual encoder 之后、LLM input assembly 之前：先抽所有候选视觉 token，再按目标 context budget 选 $K$ 个 token。
- 对离线视频库，可以预计算并缓存 FLoC selected token indices/features；因为方法 query-agnostic，同一个视频可服务多次检索和 QA。
- 流式场景可以先用固定 $T=32$ 的 rolling block 做初版，后续再用 scene change detection 或 token redundancy statistics 自适应调整 block boundary。
- 若 pairwise similarity 成本过高，可尝试 ANN / chunked similarity / low-rank approximation，保留 facility location objective，但降低 similarity matrix 的内存和 FLOPs。
- 在 FLoC 后加轻量 query-aware reranker：先用 FLoC 保证全局覆盖，再从候选 token 中按 question-text relevance 做小范围重排，平衡 reusable compression 与 question specificity。

## Open Questions / Follow-ups

- Adaptive block length 应该由 scene cut、token embedding drift，还是 downstream uncertainty 来决定？
- Facility location 对 temporal order 的建模较弱；是否需要加入 temporal diversity 或 action-boundary prior？
- 如果 visual encoder 已经有强 temporal pooling，FLoC 的 marginal benefit 会不会下降？
- 在低端 GPU、NPU 或移动端上，pairwise similarity 的实际 latency / energy cost 如何？
- 是否可以把 FLoC selected token 作为 retrieval memory，用于 hour-level 或 day-level video QA？

## Citation

```bibtex
@misc{cho2026flocfacilitylocationbasedefficient,
      title={FLoC: Facility Location-Based Efficient Visual Token Compression for Long Video Understanding}, 
      author={Janghoon Cho and Jungsoo Lee and Munawar Hayat and Kyuwoong Hwang and Fatih Porikli and Sungha Choi},
      year={2026},
      eprint={2511.00141},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2511.00141}, 
}
```
