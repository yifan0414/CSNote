---
title: Nar-KFC(frame)
authors:
  - Bo Fang
  - Yuxin Song
  - Haoyuan Sun
  - Qiangqiang Wu
  - Wenhao Wu
  - Antoni B. Chan
conference: ICLR 2026
year: 2026
paper_url: ""
source_pdf: /Users/yifan/Downloads/16552_Threading_Keyframe_with_.pdf
pdf_link: "[[assets/paper_16552_threading_keyframe_with_fe6fed5c.pdf]]"
cover: "[[assets/pipeline_16552_threading_keyframe_with_fe6fed5c.png]]"
updated: 2026-05-26
tags:
  - paper/pdf
  - video-llm
  - long-video
  - temporal-reasoning
  - question-aware
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/bofang98/Nar-KFC
openreview: https://openreview.net/forum?id=kyLS9EhPhY
---

## TL;DR

- 论文提出训练自由的 `Nar-KFC`，面向上下文长度受限的 MLLM 长视频理解：保留少量关键视觉帧，并以文本 narratives 补回稀疏采样造成的时序断点。
- `KFC` 将 keyframe selection 建模为同时优化 query-relevance 与 frame-diversity 的子图选择 / Integer Quadratic Programming (IQP) 问题，并用复杂度为 $O(NK)$ 的 Greedy Search (GS) 近似求解。
- 在 8-frame 设置下，`Nar-KFC` 对五种 MLLM 在 Video-MME、LongVideoBench (LVB) 和 MLVU 上均带来一致提升；以 InternVL3 为 backbone 时，Video-MME no-sub overall 从 59.0 提升到 **63.8**，MLVU 从 60.9 提升到 **68.4**。
- narratives 并非无成本：在 Video-MME no-sub 上，`Nar-KFC` 使用 11,005 tokens、202.6 TFLOPs、2.13 s/video，而 8 个 uniform frames 为 6,280 tokens、146.3 TFLOPs、1.03 s/video。

## Key Contributions

1. 将长视频关键帧选择明确表述为兼顾 query-relevance 与 frame-diversity 的图优化问题，并给出 IQP 目标，而不是仅依赖经验式采样规则。
2. 设计 practical `KFC (GS)`：通过 LowRank、Downsample、query-aware initialization 与 local refinement，在近似 IQP 效果的同时将搜索复杂度降到 $O(NK)$。
3. 提出 `Nar-KFC`：把 KFC-optimized keyframes 与由 non-keyframes 生成的 narratives 按真实时间顺序交错输入 MLLM，以恢复 temporal continuity。
4. 在多个 open-source MLLM 与长视频 benchmark 上验证该模块的 plug-and-play 性质，并公开代码。

## Method

**Problem setup.** 给定视频帧 $V=\{f_i\}_{i=1}^{N}$ 与查询 $q$，受上下文限制的 MLLM 仅能读取 $K$ 个视觉帧，其中 $1 \leq K \ll N$。论文希望选择的信息既与问题相关，又避免挤在相邻且重复的时间片段。

**KFC score.** 使用 CLIP-ViT-L-336px 得到归一化 frame/query embeddings。两类分数组合为：

$$
S_{\mathrm{QR}}(i)=\operatorname{sim}(f_i,q), \qquad
S_{\mathrm{FD}}(i,j)=\exp\left(-\operatorname{sim}(f_i,f_j)\right)
$$

$$
S(i,j)=S_{\mathrm{QR}}(i)+S_{\mathrm{FD}}(i,j)
=\operatorname{sim}(f_i,q)+\exp\left(-\operatorname{sim}(f_i,f_j)\right).
$$

**Optimization view.** 把 frame 看作图节点、$S(i,j)$ 看作边权，选择 $K$ 个节点以最大化所选子图的总权重。其 IQP 形式为：

$$
\max_{\mathbf{x}}\ \mathbf{x}^{\top}\mathbf{S}\mathbf{x}
\quad \text{s.t.} \quad
\mathbf{1}^{\top}\mathbf{x}=K,\quad x_i\in\{0,1\}.
$$

**Practical Greedy Search.** 精确 IQP 的最坏复杂度为指数级；实际推理采用以下流程：

1. 对 score matrix $\mathbf{S}$ 做 SVD，保留前 $N/4$ 个 singular values 形成 LowRank approximation。
2. 将矩阵进一步 downsample 到 $128 \times 128$，减少噪声及计算量。
3. 以最 query-relevant 的 frame 为初始节点，迭代加入与当前已选集合累计分数最高的 frame。
4. 在每个已选 frame 的 $k=2$ 邻域内 refinement；最终按时间排序输出 $K$ 个关键帧。

**Narrative threading.** `Nar-KFC` 使用 off-the-shelf `Qwen2-VL-2B` 为 non-keyframes 生成不超过 15 words 的 caption，并以 interval $\Delta$ 控制插入数量。关键帧与 narratives 依真实时间交错排列后送入 MLLM：

$$
\mathcal{M}\left(
\{f_{y_1},c_{y_1+\Delta},\ldots,c_{y_2-\Delta},f_{y_2},\ldots,c_{y_K-\Delta},f_{y_K}\},q
\right)
\rightarrow \mathrm{Answer}.
$$

该表示把关键视觉证据作为高信息密度主流，把中间时序上下文压缩为较省 token 的文本支流。

## Pipeline Figure

![[assets/pipeline_16552_threading_keyframe_with_fe6fed5c.png]]

Caption: Figure 2，`Nar-KFC` 将由 `KFC` 选出的 keyframes 与 off-the-shelf captioner 产生的 temporally interleaved narratives 串接起来，构造连续的长视频表示供 MLLM 推理。

Source: PDF page 4 的 Figure 2 裁剪图。

## Experiments

实验候选帧以 1 fps 从原视频采样；主表均使用 8 frames。除特殊说明外，ablation 使用 InternVL2 on Video-MME；论文报告实验运行于 8 A100 GPUs。

### Datasets

| Dataset | Task | Split / Size | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME | Long-video multiple-choice QA | 2,700 QA pairs | Accuracy (%) | 平均视频时长 17 min；报告 no sub. / sub. |
| LongVideoBench (LVB) | Long-video QA | Validation, 1,337 QA pairs | Accuracy (%) | 平均视频时长 12 min |
| MLVU | Multi-task long-video QA | M-avg, 2,593 questions, 9 categories | Accuracy (%) | 平均视频时长 12 min |
| MMBench-Video | Open-ended video QA | not reported in extracted PDF text | GPT-4-1106 judged score | 用于细粒度生成评估 |
| MLVU-OpenEnded | Open-ended video QA | G-avg | GPT-4-0125 judged score | 包含 Sub scene 与 Summary |

### Main Results

下表据 PDF page 7, Table 1 重构，均为 8-frame accuracy (%). `KFC` 和完整 `Nar-KFC` 均为论文提出的实验方法，因此其已报告数值加粗。

| Backbone / Setting | Size | Video-MME Overall no sub. / sub. | LVB | MLVU |
| --- | ---: | ---: | ---: | ---: |
| InternVL2 | 8B | 51.9 / 52.5 | 52.3 | 54.3 |
| + KFC | 8B | **53.5 / 55.0** | **53.3** | **62.2** |
| + Nar-KFC | 8B | **56.3 / 58.1** | **53.9** | **64.4** |
| Qwen2.5-VL | 7B | 55.4 / 55.9 | 52.7 | 55.8 |
| + KFC | 7B | **56.9 / 59.0** | **54.3** | **62.6** |
| + Nar-KFC | 7B | **57.9 / 58.6** | **55.3** | **64.4** |
| LLaVA-OneVision | 7B | 53.3 / 55.9 | 54.5 | 58.5 |
| + KFC | 7B | **55.4 / 58.2** | **55.6** | **65.0** |
| + Nar-KFC | 7B | **57.8 / 59.8** | **56.5** | **66.2** |
| LLaVA-Video | 7B | 55.9 / 56.7 | 54.2 | 60.5 |
| + KFC | 7B | **57.6 / 59.7** | **56.5** | **66.9** |
| + Nar-KFC | 7B | **61.6 / 63.0** | **57.7** | **67.7** |
| InternVL3 | 8B | 59.0 / 60.0 | 53.6 | 60.9 |
| + KFC | 8B | **60.8 / 61.4** | **54.5** | **67.5** |
| + Nar-KFC | 8B | **63.8 / 64.1** | **54.8** | **68.4** |

论文称，在 Video-MME no-sub overall 上，`Nar-KFC` 相对五个对应 MLLM baselines 平均提升 4.38 percentage points；在完整方案中，InternVL3 + Nar-KFC 达到最高报告结果 63.8。

### Open-Ended Generation

以下数值据 PDF page 8, Table 2 转录；分数由表中指定 GPT judge 计算。

| Backbone / Setting | MMBench-Video Overall | MLVU-OpenEnded G-Avg |
| --- | ---: | ---: |
| InternVL3-8B | 1.57 | 4.92 |
| + KFC | **1.58** | **4.95** |
| + Nar-KFC | **1.78** | **5.02** |
| Qwen3-VL-8B | 1.64 | 6.09 |
| + KFC | **1.69** | **6.00** |
| + Nar-KFC | **1.76** | **6.12** |

`KFC` 在 Qwen3-VL 的 MLVU-OpenEnded G-Avg 上未优于 uniform baseline；完整 `Nar-KFC` 则在两种 backbone 上均提高 G-Avg。

### Ablations / Analysis

主组件消融据 PDF page 8, Table 3 重构；Video-MME 列为 subtitle setting 下的 overall accuracy (%).

| Variant / Setting | Video-MME (sub.) | MLVU | Time Complexity | Notes |
| --- | ---: | ---: | --- | --- |
| Uniform | 52.5 | 54.3 | $O(1)$ | baseline |
| + Narratives | 55.4 | 59.4 | $O(N)$ | uniform frames 加 narratives |
| KFC (IQP) | **55.1** | **62.0** | $O(2^N)$ | theoretical optimization |
| KFC (GS) | **55.0** | **62.2** | $O(NK)$ | practical KFC |
| KFC (GS) w/o $S_{\mathrm{QR}}$ | 51.8 | 57.3 | $O(NK)$ | 移除 query-relevance |
| KFC (GS) w/o $S_{\mathrm{FD}}$ | 52.5 | 60.9 | $O(NK)$ | 移除 frame-diversity |
| Nar-KFC | **58.1** | **64.4** | $O(NK)$ | full method |

视频输入成分与推理负担据 PDF page 9, Table 6 重构，为 Video-MME no-sub 设置。

| Input Components | Accuracy (%) | Latency (s/video) | TFLOPs | Tokens / Video |
| --- | ---: | ---: | ---: | ---: |
| Narratives (210) | 51.1 | 0.98 | 109.6 | 4,725 |
| Frames (8, uniform) | 51.9 | 1.03 | 146.3 | 6,280 |
| Frames (8, KFC) | **53.5** | 1.31 | 146.3 | 6,280 |
| Interleave (8 + 210, Nar-KFC) | **56.3** | 2.13 | 202.6 | 11,005 |

时序结构分析据 PDF page 9, Table 7 重构；将两类输入真正 interleave 优于先后拼接。

| Temporal Structure | Video-MME no-sub Accuracy (%) |
| --- | ---: |
| Narratives $\rightarrow$ Keyframes $\rightarrow$ Query | 55.5 |
| Keyframes $\rightarrow$ Narratives $\rightarrow$ Query | 55.3 |
| Interleave (Nar-KFC) $\rightarrow$ Query | **56.3** |

### Training / Compute

| Item | Value |
| --- | --- |
| Candidate frame sampling | 1 fps |
| Main-table visual frame budget | 8 frames |
| Query / frame embedding model | CLIP-ViT-L-336px |
| IQP solver setting | CPLEX; maximum 40k search nodes |
| GS LowRank setting | retain top $N/4$ singular values |
| GS downsampled score matrix | $128 \times 128$ |
| GS refinement window | $k=2$ |
| Default narrative captioner | Qwen2-VL-2B |
| Default number of narratives | 210 |
| Reported experiment hardware | 8 A100 GPUs |

## Limitations & Caveats

- 论文未提供独立的 limitations section；以下局限来自其实验与方法描述。完整 `Nar-KFC` 的提升伴随明显输入与推理开销：相较 8 uniform frames，tokens 从 6,280 增至 11,005，latency 从 1.03 s 增至 2.13 s（page 9, Table 6）。
- narratives 不能替代关键视觉证据：单独使用 210 narratives 的 Video-MME no-sub accuracy 为 51.1，低于 8 uniform frames 的 51.9，说明 frame-to-caption conversion 会丢失信息。
- narrative 收益随视觉帧预算增加而缩小；论文在 Figure 3 中指出，MLVU 使用 32 keyframes 时 `KFC` alone 优于 `Nar-KFC`。
- open-ended 结果依赖 GPT-4 judge，可能受评判模型偏好影响；此外，使用 8 A100 GPUs 的研究配置并不直接等价于低成本生产推理。

## Concrete Implementation Ideas

1. 在已有 VideoQA inference wrapper 前加入 `KFCSelector`：以 CLIP embeddings 缓存每个视频的 frame features，按 query 动态输出 8 个 timestamps。
2. 实现 `GreedySearchSelector` 的逐步 ablation 开关：`low_rank`, `downsample`, `refine`，复现 Table 4 的组件增益并测量本地 latency。
3. 为 non-keyframes 离线缓存 `Qwen2-VL-2B` captions，并在运行时仅依据 keyframe timestamps 和 $\Delta$ 构造 temporal interleave prompt，避免重复 caption 开销。
4. 除 accuracy 外记录 tokens、TFLOPs/估算 FLOPs 与 end-to-end latency，以验证在目标部署约束下 `Nar-KFC` 的收益是否覆盖额外成本。

## Open Questions / Follow-ups

- `KFC` 在不同视频时长、问题类型和 frame budget 下的最优 $K$、$\Delta$ 是否可以由 query 或视频动态预测，而非固定配置？
- 如果 narratives 来自更强 captioner，page 9 显示准确率仅小幅提升；是否可以通过 event-aware caption selection 以更少 captions 达到相同效果？
- frame-diversity 使用外观 embedding 的反相似度；对需要细粒度动作顺序或音频线索的问题，是否需要 motion/audio-aware score？
- 在同等 token 或 wall-clock budget 下，与长上下文 VideoLLM、token compression 或 retrieval-based 方法的公平比较会如何变化？

## Citation

Bo Fang, Yuxin Song, Haoyuan Sun, Qiangqiang Wu, Wenhao Wu, and Antoni B. Chan. *Threading Keyframe with Narratives: MLLMs as Strong Long Video Comprehenders*. Published as a conference paper at ICLR, 2026.

Code: [https://github.com/bofang98/Nar-KFC](https://github.com/bofang98/Nar-KFC)
