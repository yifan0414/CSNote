---
title: MDP3(frame)
authors:
  - Hui Sun
  - Shiyin Lu
  - Huanyu Wang
  - Qing-Guo Chen
  - Zhao Xu
  - Weihua Luo
  - Kaifu Zhang
  - Ming Li
conference: ICCV 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2501.02885
pdf_link: "[[assets/paper_2501.02885.pdf]]"
cover: ""
updated: 2026-05-26
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: reading
priority: "3"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/sunh-23/MDP3
---

## TL;DR

- 论文提出 `mDP3`（TeX 中写作 mDP$^3$），一个在推理时插入 Video-LLM 的 training-free、model-agnostic 帧选择方法。
- 作者认为 VidQA 选帧必须同时满足三点：与 query 相关、所选帧集合具有 list-wise diversity、并保留视频的 sequentiality。
- 方法以 VLM embedding 构造 query-conditioned multiple Gaussian kernel（CMGK），以 DPP 选取相关且不冗余的帧，再以 MDP/dynamic programming 在连续片段间分配选帧预算。
- 标准实验从均匀抽取的 128 个候选帧中选择 8 帧；在 Video-MME、MLVU、LongVideoBench$_{val}$ 上，将 `mDP3` 接到多种 Video-LLM 均改善结果。
- 在主表中，Ovis2 + `mDP3` 达到 Video-MME overall 63.9 / 66.1（无/有字幕）、MLVU 73.9、LVB$_{val}$ 62.7；这些值是论文显式加粗的最佳结果。
- 代价是增加 SigLIP text encoder 与选帧计算；作者还指出固定选择数量 $k$ 以及 pretrained VLM 的指令理解能力仍是限制。

## Key Contributions

1. 将 VidQA frame selection 明确建模为同时考虑 query relevance、list-wise diversity 与 sequentiality 的 subset selection 问题。
2. 提出 CMGK + DPP：在 RKHS 中让 frame-frame similarity 受当前 query 调制，再使用 DPP 的 log-determinant 分数鼓励集合多样性。
3. 提出 Markov Decision DPP：将视频切成连续 segments，以动态规划分配总选帧容量 $k$，并给出基于 greedy DPP 的 $(1-1/e)$ 近似分析。
4. 给出 plug-and-play 的 test-time 实证：无需为目标 Video-LLM 训练 selector，即可在多个 backbone 与长视频 benchmark 上得到一致收益。

## Method

给定视频 $V=\{f_i\}_{i=1}^{n}$、问题 $q$ 和容量 $k$，目标是选择索引集合：

$$
S^*=\underset{S\subseteq\{1,\ldots,n\},\ |S|=k}{\arg\max}\ \mathrm{Score}(S).
$$

**1. Conditional similarity.** 复用 pretrained VLM 将帧与问题映射到共同 embedding space，并使用多 Gaussian kernel。论文提出的 conditional kernel 为：

$$
\tilde{k}(f_i,f_j\mid q)=g(f_i,q)\,k(f_i,f_j)\,g(f_j,q), \qquad g,k\in\mathcal{K}.
$$

以 $\mathbf{r}_i=g(f_i,q)$ 和 frame similarity matrix $\mathbf{L}$ 表示时：

$$
\tilde{\mathbf{L}}=\operatorname{diag}(\mathbf{r})\mathbf{L}\operatorname{diag}(\mathbf{r}).
$$

**2. DPP for relevance and diversity.** 对候选集合 $S$，DPP 使用 $\det(\tilde{\mathbf{L}}_S)$ 评分。作者加入 $\lambda$ 平衡 relevance 与 diversity：

$$
\log\det(\tilde{\mathbf{L}}_S)
=\frac{1}{\lambda}\sum_{i\in S}\log(\mathbf{r}_i^2)
+\log\det(\mathbf{L}_S).
$$

固定容量的 DPP MAP 由 greedy marginal gain 和 incremental Cholesky update 近似求解，标准复杂度为 $\mathcal{O}(nk^2)$。

**3. Sequential selection as an MDP.** 将视频按长度 $m$ 分成 $T=\lceil n/m\rceil$ 个连续片段；当前片段选择 $S_t$ 以前一片段 $S_{t-1}$ 为条件：

$$
\mathcal{P}(S_t\mid S_{t-1})
=\frac{\det(\tilde{\mathbf{L}}_{S_{t-1}\cup S_t})}
{\det(\tilde{\mathbf{L}}_t+\mathbf{I}_t)}.
$$

动态规划寻找各 segment 的容量 $k_t$，满足 $\sum_t k_t=k$。完整理论形式接近 $\mathcal{O}(nk^4)$；正文称 lazy 实现接近 $\mathcal{O}(nk^3)$，将独立更新并行化后可达到 $\mathcal{O}(nk^2)$。

**Compact Pipeline**

```text
Input: video frames V, query q, selected-frame budget k
1. Uniformly produce candidate frames; encode frames and query with a VLM.
2. Split candidates into consecutive segments of size m.
3. For each segment, build CMGK similarity conditioned on q.
4. Use greedy conditional DPP to evaluate selections of different sizes.
5. Dynamic programming allocates the total budget across segments.
6. Feed the selected frames, in temporal order, to the Video-LLM.
Output: answer from the Video-LLM using a compact selected-frame context.
```


> [!summary]+
> **Video + Question → 取候选帧 → VLM 编码 → 构造 query-conditioned similarity matrix → DPP 选相关且多样的帧 → 按时间分段并用 MDP/DP 分配每段选几帧 → 输出 k 帧给 Video-LLM。**
> 
> 论文强调好的 frame selection 需要同时满足三点：**query relevance、list-wise diversity、sequentiality**；MDP 3 正是围绕这三点设计的。arXiv 摘要也概括了这三步：条件高斯核估计 query-conditioned frame similarity，DPP 捕捉相关性与多样性，再用分段 + MDP 建模顺序性和预算分配。([arxiv.org](https://arxiv.org/abs/2501.02885))
> 
> ## Pipeline 分步
> 
> ### 1. 输入与候选帧采样
> 
> 输入是：
> 
> - 视频 $V=\{f_i\}_{i=1}^n$
> - 问题/query $q$
> - 目标选择帧数 $k$
> 
> 实验中通常不是直接处理所有原始帧，而是先均匀采样一批候选帧，例如 128 帧，再从中选出最终的 8 帧左右。
> 
> 
> ### 2. 用 VLM 得到 frame/query embedding
> 
> 使用预训练 VLM 的 vision encoder 和 text encoder：
> 
> $$
> f_i \leftarrow VLM_{vision}(f_i), \quad q \leftarrow VLM_{text}(q)
> $$
> 
> 这样每一帧和 query 都被映射到同一个语义空间中。
> 
> 
> ### 3. 构造 query-conditioned similarity matrix：CMGK
> 
> MDP 3 不直接用简单 cosine similarity，而是在 RKHS 里用条件多高斯核：
> 
> $$
> \tilde{k}(f_i, f_j|q)=g(f_i,q)k(f_i,f_j)g(f_j,q)
> $$
> 
> 可以理解为：
> 
> - $k(f_i,f_j)$：帧与帧之间的相似度；
> - $g(f_i,q)$：帧与 query 的相关性；
> - 两边乘 query relevance，是为了让与问题无关的帧被降权。
> 
> 矩阵形式：
> 
> $$
> \tilde{L} = diag(r) \cdot L \cdot diag(r)
> $$
> 
> 其中：
> 
> - $L$ 是 frame-frame similarity；
> - $r$ 是 frame-query relevance。
> 
> 
> ### 4. 用 DPP 做 list-wise frame selection
> 
> DPP 给一个帧集合 $S$ 打分：
> 
> $$
> P(S) \propto det(\tilde{L}_S)
> $$
> 
> 直觉上：
> 
> - 如果选出的帧都和 query 相关，分数高；
> - 如果选出的帧彼此太相似，行列式体积会变小，分数低；
> - 所以 DPP 会偏好 **相关且互补** 的帧集合。
> 
> 这一步解决的是：
> 
> > 不要只选 top-k query-relevant frames，因为那样可能都是重复帧；要选一个整体上好的 frame subset。
> 
> 
> ### 5. 视频分段，引入 sequentiality
> 
> 标准 DPP 本身不关心时间顺序。MDP 3 为了解决这个问题，会把视频切成连续片段：
> 
> $$
> N_n = \bigcup_{t=1}^{T} N_t
> $$
> 
> 然后在每个 segment 内做 DPP，但当前 segment 的选择会 conditioned on 前一个 segment 的选择：
> 
> $$
> P(S_t|S_{t-1})
> $$
> 
> 这样做的目的：
> 
> - 保留视频的时间结构；
> - 避免跨时间段选择过于混乱；
> - 对长视频尤其重要，因为关键信息往往集中在某些时间段，而不是均匀分布。
> 
> 
> ### 6. 用 MDP + Dynamic Programming 分配每段选几帧
> 
> 关键问题是：总共只能选 $k$ 帧，那每个 segment 选几帧？
> 
> 不能简单平均分，因为相关帧可能集中在某几个片段里。
> 
> 所以 MDP 3 把它建模成一个 MDP：
> 
> - **state**：当前到第几个 segment、已经选了多少帧；
> - **action**：当前 segment 选多少帧、选哪些帧；
> - **reward**：当前选择带来的 conditional DPP log-probability；
> - **transition**：更新已选择帧数；
> - **goal**：总共选满 $k$ 帧，并最大化累计 reward。
> 
> 最后用 dynamic programming 找到近似最优路径，也就是每段的选帧数量和具体帧集合。
> 
> 
> ### 7. 输出选中帧，送入任意 Video-LLM
> 
> MDP 3 是 **training-free + model-agnostic** 的，所以它不改 Video-LLM，也不需要重新训练 selector。
> 
> 最终输出：
> 
> $$
> S = S_1 \cup S_2 \cup ... \cup S_T
> $$
> 
> 然后按时间顺序把这些帧输入 Video-LLM，让模型回答问题。
> 
> ## 总结图
> 
> ```text
> Video + Query
>      ↓
> Uniformly sample candidate frames
>      ↓
> VLM encode frames and query
>      ↓
> CMGK: query-conditioned similarity matrix
>      ↓
> DPP: relevant + diverse frame subset scoring
>      ↓
> Segment video by time
>      ↓
> MDP/DP: allocate k frames across segments
>      ↓
> Selected key frames
>      ↓
> Video-LLM inference
> ```
> 
> ## 核心理解
> 
> MDP 3 不是简单的“挑最相关帧”，而是：
> 
> 1. **query relevance**：选和问题有关的；
> 2. **list-wise diversity**：选出来的一组帧不能太重复；
> 3. **sequentiality**：要尊重视频时间结构；
> 4. **dynamic allocation**：不同片段按重要性分配不同帧数。


## Pipeline Figure

TeX 源码未提供 caption 或文件名明确表示 pipeline、framework、overview 或 architecture 的主方法图。可解析的图资源均为 benchmark gain、latency、hyperparameter sensitivity、消融或 case-study 可视化，因此未把结果图误标成 pipeline figure，`cover` 留空。

## Experiments

**Evaluation Setup**

| Item | Value |
| --- | --- |
| Integration | inference-time plug-and-play frame selector for Video-LLMs |
| Standard selection setting | uniformly sample 128 candidate frames, then select 8 frames with `mDP3` |
| Primary backbones | VILA-V1.5, MiniCPM-V2.6, LLaVA-OneVision, Ovis2 |
| Tooling | LMMs-Eval and VLMEvalKit |
| Reported code | https://github.com/sunh-23/MDP3 |

**Datasets / Benchmarks**

| Dataset | Task | Split / Setting | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME | long-video multiple-choice QA | with and without subtitles | Accuracy (%) | 900 videos, 2,700 human-annotated QA pairs; average duration 17 min |
| MLVU | multi-task long video understanding | reported benchmark setting | Score / accuracy reported in table | 2,593 tasks over 9 categories; average duration 12 min |
| LongVideoBench | long-term video-language understanding | validation without subtitle interleaving (`LVB_val`) | Accuracy (%) | 1,337 QA pairs in used validation split; average duration 12 min |

**Main Results**

下表转录主表的整体 benchmark 列；Video-MME 数值为 without / with subtitles。粗体保留论文原表的显式强调，未对未加粗结果重新排名。

| Model / Selector | LLM Size | Frames | Video-MME Overall (wo / w subs) | MLVU | LVB$_{val}$ |
| --- | ---: | ---: | ---: | ---: | ---: |
| Video-XL | 7B | 128 / 256 | 55.5 / 61.0 | 64.9 | - |
| LLaVA-OneVision$^*$ | 7B | 32 | 58.2 / not reported | 64.7 | 56.3 |
| VILA-V1.5 | 8B | 8 | 47.5 / 50.0 | 46.3 | 47.1 |
| + Frame-Voyager | 8B | 8 | 50.5 / 53.6 | 49.8 | - |
| **+ mDP3** | 8B | 8 | 53.3 / 56.6 | 58.6 | 50.8 |
| MiniCPM-V2.6 | 7B | 8 | 52.6 / 53.1 | 55.4 | 51.2 |
| **+ mDP3** | 7B | 8 | 58.0 / 61.8 | 66.6 | 57.1 |
| LLaVA-OneVision | 7B | 8 | 53.6 / 53.9 | 59.3 | 54.2 |
| + Frame-Voyager | 7B | 8 | 57.5 / not reported | 65.6 | - |
| **+ mDP3** | 7B | 8 | 59.6 / 59.1 | 69.8 | 59.0 |
| Ovis2 | 7B | 8 | 58.9 / 62.1 | 60.9 | 56.9 |
| **+ mDP3** | 7B | 8 | **63.9 / 66.1** | **73.9** | **62.7** |

$^*$ `LLaVA-OneVision` 官方报告使用调优后的帧数量。`Video-XL` 在 Video-MME / MLVU 分别使用 128 / 256 帧。正文称 primary baselines 为 7B models，但主表将 VILA-V1.5 列为 8B、将 Ovis2 列为 7B；此处忠实保留表格记录。

**Results by Video Duration on LongVideoBench$_{val}$**

| Model / Selector | Overall | (8s, 15s] | (15s, 1m] | (3m, 10m] | (15m, 60m] |
| --- | ---: | ---: | ---: | ---: | ---: |
| VILA-V1.5 | 47.1 | 56.1 | 60.5 | 43.4 | 42.7 |
| **+ mDP3** | 50.8 | 57.7 | 66.3 | 48.3 | 45.6 |
| MiniCPM-V2.6 | 51.2 | 67.7 | 66.9 | 46.8 | 44.1 |
| **+ mDP3** | 57.1 | 67.2 | 70.9 | 56.1 | 50.4 |
| LLaVA-OneVision | 54.2 | 68.3 | 66.9 | 52.4 | 46.8 |
| **+ mDP3** | 59.0 | 70.4 | 73.3 | 57.8 | 51.8 |

作者观察到极短视频收益较小：在 `(8s, 15s]` 组中 MiniCPM-V2.6 从 67.7 降到 67.2；长视频组通常更受益于选择策略。

**Ablations / Analysis: VILA on Video-MME without Subtitles**

| Selector / Variant | Query Relevance | List-wise Diversity | Sequentiality | RKHS Similarity | Training-free Model-agnostic | Acc. (%) |
| --- | --- | --- | --- | --- | --- | ---: |
| Uniform | No | No | No | No | Yes | 47.5 |
| SigLIP top-$k$ | Yes | No | No | No | Yes | 50.6 |
| mDP3 w. MGK | No | Yes | Yes | Yes | Yes | 48.9 |
| DPP w. CMGK | Yes | Yes | No | Yes | Yes | 51.8 |
| mDP3 w. cosine similarity | Yes | Yes | Yes | No | Yes | 50.2 |
| **mDP3** | Yes | Yes | Yes | Yes | Yes | **53.3** |

**Training / Compute**

| Item | Value |
| --- | --- |
| VLM used for LLaVA-OneVision and MiniCPM selector | SigLIP; existing vision encoder reused, text encoder added |
| Query handling | SigLIP text sequences longer than 64 tokens are split, embedded, then pooled |
| Gaussian multi-kernel scales | $\alpha_u=2^i$, $i\in\{-3,-2,0,1,2\}$, with averaged kernel weights |
| Selected hyperparameters | $\lambda=0.2$, segment size $m=32$ for all tasks and benchmarks |
| Hardware | NVIDIA A100-PCIE-40GB or A100-PCIE-80GB; 256 AMD EPYC 7H12 CPU cores; Ubuntu 20.04.6 |
| Additional pretrained parameters | SigLIP text encoder: 0.450B; reported increases are 5.298% to 5.606% for listed backbones |
| Latency report (MiniCPM-V2.6, Video-MME without subtitles) | `mDP3` adds 1.94 s selection while reducing MLLM inference by 11.47 s; parallel `mDP3-P` adds 1.30 s |

## Limitations & Caveats

- `mDP3` relies on pretrained VLM representations. 这使它可以免训练接入不同 Video-LLM，但复杂 instruction 的理解上限也被 VLM 限制。
- 总选择量 $k$ 固定；附录明确指出方法有时会选到无用帧，而为每个样本调 relevance/diversity 权衡并不现实。
- $\lambda=0.2$ 与 $m=32$ 由 LLaVA-OneVision-mid training subset 的 cross-validation 确定，虽报告了敏感性分析，仍不是完全零配置。
- 与 uniform sampling 相比，极短视频不一定受益；LongVideoBench$_{val}$ 的一个短时长组甚至出现轻微下降。
- 复杂度降低依赖 lazy 与 parallel update 的实现策略；理论完整 DP、实际 lazy DP 与并行化版本应分开解读。
- 主文关于 VILA/Ovis2 的模型规模表述与主表存在不一致，比较模型大小时应回查原始实现或 leaderboard。

## Concrete Implementation Ideas

1. 将 selector 实现为独立 inference adapter：输入候选 frame embedding 与 query embedding，默认复现实验配置 $n=128$、$k=8$、$m=32$、$\lambda=0.2$，输出保持时间顺序的 frame indices。
2. 先实现 `DPP w. CMGK` baseline，再添加 segment-conditioned DP；使用 incremental Cholesky 更新记录各阶段 latency，验证 sequentiality 的增益是否值得额外开销。
3. 在现有 Video-LLM evaluation pipeline 中同时记录 accuracy、送入 LLM 的 visual token 数量和 end-to-end latency，避免只以 accuracy 判断部署价值。
4. 利用 DP trace 已保存的 $\mathcal{T}_{T,i}$（$i<k$）探索 adaptive $k$：以置信度、边际 log-determinant gain 或 token budget 作为停止准则。

## Open Questions / Follow-ups

- 在开放式生成、temporal grounding 或 video summarization 中，CMGK/DPP 的收益是否仍能重现，而不仅限于 multiple-choice VidQA？
- adaptive $k$ 的选择准则如何避免因 DPP 分数尺度在不同视频/问题间不可比而失效？
- 将更强的 text/video encoder 替换 SigLIP 时，额外推理成本与选帧收益之间如何权衡？
- 论文的 $(1-1/e)$ 保证在 lazy condition truncation 与并行更新实际实现中保留到什么程度？
- 对语义相近但时间顺序决定答案的问题，是否能设计专门 benchmark 更直接衡量 sequentiality？

## Citation

Hui Sun, Shiyin Lu, Huanyu Wang, Qing-Guo Chen, Zhao Xu, Weihua Luo, Kaifu Zhang, and Ming Li. *MDP3: A Training-free Approach for List-wise Frame Selection in Video-LLMs*. ICCV, 2025. arXiv:2501.02885 [cs.CV]. https://arxiv.org/abs/2501.02885
