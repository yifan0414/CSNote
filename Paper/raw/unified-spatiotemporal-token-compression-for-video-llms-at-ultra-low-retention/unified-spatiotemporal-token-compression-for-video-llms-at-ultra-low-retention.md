---
title: "Unified Spatiotemporal Token Compression for Video-LLMs at Ultra-Low Retention"
authors: ["Junhao Du", "Jialong Xue", "Anqi Li", "Jincheng Dai", "Guo Lu"]
conference: "CVPR"
year: 2026
arxiv_url: "https://arxiv.org/abs/2603.21957"
pdf_link: "[[assets/paper_2603.21957.pdf]]"
cover: "[[_assets/images/pipeline_2603.21957.png]]"
updated: 2026-05-31
tags: ["paper/arxiv", "video-qa", "long-video", "temporal-reasoning", "question-aware", "token-pruning", "video-llm"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: ""
---

## TL;DR

- 这篇论文把 Video-LLM 的 visual token 压缩重新表述为一个全局 spatiotemporal allocation 问题，而不是先时间后空间或先空间后时间的 two-stage pruning。
- 方法是 training-free、plug-and-play：LLM 外部做 unified spatiotemporal compression，LLM 内部再做 text-aware merging。
- 外部阶段用 attention score 估计 token contribution，用 cosine similarity 控制 redundancy；未保留的 token 不直接丢弃，而是进入 recycle pool，经 DPC-KNN 聚类后回填。
- 内部阶段用 text-to-visual attention 和 text-visual semantic similarity 共同打分，让视觉 token 的二次压缩更 question-aware，避免 last-token attention 的位置偏置。
- 在 LLaVA-OneVision-7B 上，2%/1% retention 时平均分 50.7，保留 90.1% baseline performance，同时 FLOPs 约为 2.6%；1%/0.5% 时仍有 84.1%。
- 主要限制是目前面向 fixed offline videos，不支持 real-time streaming token compression；uniform frame sampling 也可能在短视频引入冗余、在长视频漏掉关键片段。

## Key Contributions

1. 提出 unified spatiotemporal retention pool：在全局 token 池里同时考虑高贡献和低冗余，避免 two-stage methods 在 ultra-low retention 下的时空资源分配失衡。
2. 将 pruning 与 merging 结合：选中的 token 进入 retention pool，未选 token 进入 recycle pool，通过 DPC-KNN 聚类合并后回填，尽量保留 semantic completeness。
3. 设计 text-aware merging：在 LLM 内部结合 text-to-visual attention 与 text-visual cosine similarity，对与 query 更相关的视觉 token 保留更高优先级。
4. 全流程无需 retraining，并在 LLaVA-OneVision、LLaVA-Video、Qwen2.5-VL 等 backbones 上验证 cross-backbone generalization。

## Method

**Problem framing.** 给定视频经 encoder/projector 得到的 visual tokens，目标不是分别沿 temporal/spatial 维度做独立筛选，而是在一个 global budget 下选择最值得保留的 token，并把未保留 token 中的语义信息压缩回 retention pool。

**External: Unified Spatiotemporal Compression.**

1. 计算 visual token 的 contribution。若视觉 encoder 有 CLS token，则用 CLS attention；若类似 SigLIP 没有显式 CLS，则用每个 visual token 与其他 token 的平均 attention 近似。
2. 对候选 token $c$，计算它与 retention pool $\mathcal{P}$ 的最大 cosine similarity：

$$
\boldsymbol{S}=\mathrm{sim}(c,\mathcal{P})=\max_{p\in \mathcal{P}}\frac{c\cdot p}{\|c\|\|p\|}
$$

3. 如果 $\max \mathrm{sim}(c,\mathcal{P}) < \tau$，则 token 进入 retention pool；否则进入 recycle pool。论文主实验使用 $\tau=0.7$。
4. 对 recycle pool 做 DPC-KNN clustering。每个 token 的局部密度与到更高密度 token 的最小距离为：

$$
\rho_i=\exp\left(-\frac{1}{k}\sum_{v_j\in\mathrm{kNN}(v_i)}d(v_i,v_j)^2\right)
$$

$$
\delta_i=
\begin{cases}
\max_{j\neq i} d(v_i,v_j), & \rho_i=\max_k\rho_k \\
\min_{j:\rho_j>\rho_i} d(v_i,v_j), & \text{otherwise}
\end{cases}
$$

用 $\gamma_i=\rho_i\times\delta_i$ 选择 cluster centers，剩余 token 分配到最近中心并平均合并，再回填 retention pool。最终按原始 spatiotemporal order 重排。

**Internal: Text-Aware Merging.**

1. 在 LLM 内部从 self-attention 矩阵 $A\in\mathbb{R}^{(N_v' + N_q)\times(N_v' + N_q)}$ 中取 text-to-visual 子矩阵 $A_{qv}=A[N_v':,:N_v']$。
2. 对每个 visual token 取所有 text tokens 上的最大 attention，并 min-max normalize 得到 $A_m^{\mathrm{norm}}$。
3. 计算每个 visual token 与所有 text tokens 的最大 cosine similarity，并 normalize 得到 $S_m^{\mathrm{norm}}$。
4. 用超参 $\lambda$ 加权得到 token decision score：

$$
I(v_i)=(1-\lambda)\cdot A_m^{\mathrm{norm}}(v_i)+\lambda\cdot S_m^{\mathrm{norm}}(v_i)
$$

5. 保留 top $R\%$ visual tokens；其余 token 不直接丢弃，而是合并到最相似的 retained token。主实验设置为从 layer $K=18$ 开始，保留 top $R=50\%$，$\lambda=0.5$。

## Pipeline Figure

![[_assets/images/pipeline_2603.21957.png]]

Caption: 方法总览：先在 LLM 外部用 unified spatiotemporal compression 筛选高贡献、低冗余 token，并对 recycle pool 做聚类回填；随后在 LLM 内部用 text-aware merging 强化 query-relevant visual tokens。

Source: TeX includegraphics from `figs/overview.tex` -> `figs/overview/overview-111406.pdf`; rendered to PNG with `pdftoppm -cropbox`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MVBench | Video understanding QA，覆盖 20 个任务 | not reported | accuracy / score | 每个任务 200 个 QA pairs，强调 temporal comprehension。 |
| EgoSchema | 多选 video QA | not reported | accuracy / score | 超过 5,000 个 human-curated QA pairs，视频总长超过 250 小时，每题 5 个选项。 |
| MLVU | Long-form video understanding | not reported | score | 视频 3 分钟到 2 小时以上，平均约 12 分钟，含 topic reasoning、summarization、needle QA 等 9 类任务。 |
| LongVideoBench | Long video temporal retrieval / analysis | not reported | score | 3,763 个视频、6,678 个多选问题，覆盖 movies/news 等领域。 |
| VideoMME | Short/medium/long video QA | short / medium / long subsets | score | 900 个视频、2,700 个 QA pairs，时长 11 秒到 1 小时，覆盖 6 个视觉领域。 |
| ActivityNet-QA | Open-ended video QA | not reported | Accuracy, Score | 58,000 个 QA pairs / 5,800 个视频；论文用 GPT-3.5-Turbo 作为 response quality evaluator。 |

### Main Results: LLaVA-OneVision-7B

下表保留论文主表的数值和作者标注的 best / second-best emphasis。`A%/B%` 表示先在 LLM input 保留 `A%`，随后在 LLM forward 过程中压缩到 `B%`。

| Retention group | Method | FLOPs (T) | FLOPs Ratio | Retention Ratio | MVBench | EgoSchema | MLVU | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ----: | ----: | ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| baseline | LLaVA-OV-7B | 41.4 | 100% | 100% | 58.3 | 60.4 | 47.7 | 56.4 | 58.6 | 56.3 | 100 |
| 10% | FastV | 7.9 | 19.1% | 100%/10% | 53.2 | 55.9 | 41.6 | 52.1 | 52.7 | 51.1 | 90.8 |
| 10% | VisionZip | 4.0 | 9.6% | 10% | 53.5 | 58.0 | 42.5 | 49.3 | 53.4 | 51.3 | 91.2 |
| 10% | LLaVA-Scissor | 4.0 | 9.6% | 10% | - | 57.5 | - | - | 55.8 | - | - |
| 10% | FastVID | 4.0 | 9.6% | 10% | 55.9 | 58.7 | 42.6 | 56.3 | **57.3** | 54.2 | 96.2 |
| 10% | HoliTom | 3.4 | 8.2% | 10%/5% | 57.3 | **61.2** | <u>45.1</u> | 56.3 | <u>56.8</u> | <u>55.3</u> | <u>98.3</u> |
| 10% | **Ours (w/o M)** | 4.0 | 9.6% | 10% | <u>57.4</u> | 60.5 | 44.7 | **57.4** | 56.6 | <u>55.3</u> | <u>98.3</u> |
| 10% | **Ours** | 3.4 | 8.2% | 10%/5% | **57.7** | <u>60.6</u> | **45.5** | <u>56.4</u> | 56.6 | **55.4** | **98.4** |
| 5% | FastV | 6.4 | 15.5% | 100%/5% | 51.2 | 53.9 | 35.8 | 47.9 | 49.7 | 47.7 | 84.7 |
| 5% | VisionZip | 2.2 | 5.4% | 5% | 45.2 | 51.9 | 37.4 | 46.4 | 48.2 | 45.8 | 81.4 |
| 5% | LLaVA-Scissor | 2.2 | 5.4% | 5% | - | 56.6 | - | - | 53.3 | - | - |
| 5% | FastVID | 2.2 | 5.4% | 5% | 53.0 | 57.1 | 42.1 | 51.1 | 54.2 | 51.5 | 91.5 |
| 5% | HoliTom | 2.0 | 4.7% | 5%/2.5% | <u>55.6</u> | **60.5** | 40.6 | 53.6 | 54.2 | 52.9 | 94.0 |
| 5% | **Ours (w/o M)** | 2.2 | 5.4% | 5% | **56.4** | 59.5 | <u>42.5</u> | <u>53.7</u> | **55.0** | <u>53.4</u> | <u>94.9</u> |
| 5% | **Ours** | 2.0 | 4.7% | 5%/2.5% | **56.4** | <u>60.2</u> | **42.8** | **54.5** | <u>54.7</u> | **53.7** | **95.4** |
| 2% | FastV | 5.5 | 13.3% | 100%/2% | 49.0 | 50.6 | 34.1 | 47.1 | 47.3 | 45.6 | 81.0 |
| 2% | VisionZip | 1.2 | 2.9% | 2% | 41.7 | 47.6 | 31.8 | 45.1 | 45.9 | 42.4 | 75.3 |
| 2% | FastVID | 1.2 | 2.9% | 2% | 48.0 | 52.3 | 37.6 | 47.3 | 49.2 | 46.9 | 83.3 |
| 2% | HoliTom | 1.1 | 2.6% | 2%/1% | 52.6 | <u>57.2</u> | 37.4 | 48.5 | 51.1 | 49.4 | 87.7 |
| 2% | **Ours (w/o M)** | 1.2 | 2.9% | 2% | **52.9** | <u>57.2</u> | <u>39.5</u> | **51.0** | <u>51.3</u> | <u>50.4</u> | <u>89.5</u> |
| 2% | **Ours** | 1.1 | 2.6% | 2%/1% | <u>52.8</u> | **57.6** | **40.3** | <u>50.8</u> | **51.8** | **50.7** | **90.1** |
| 1% | FastV | 5.2 | 12.6% | 100%/1% | 48.2 | 48.8 | 32.3 | 45.5 | 46.2 | 44.2 | 78.5 |
| 1% | VisionZip | 0.9 | 2.1% | 1% | 40.8 | 43.8 | 29.7 | 44.4 | 44.3 | 40.6 | 72.1 |
| 1% | FastVID | 0.9 | 2.1% | 1% | 45.3 | 47.8 | 32.4 | 46.1 | 47.0 | 43.7 | 77.7 |
| 1% | HoliTom | 0.8 | 2.0% | 1%/0.5% | <u>49.6</u> | 52.9 | <u>33.9</u> | 48.1 | 49.0 | 46.7 | 82.9 |
| 1% | **Ours (w/o M)** | 0.9 | 2.1% | 1% | **50.5** | <u>53.3</u> | **34.4** | **49.1** | **49.8** | **47.4** | **84.2** |
| 1% | **Ours** | 0.8 | 2.0% | 1%/0.5% | **50.5** | **53.8** | **34.4** | <u>48.8</u> | <u>49.2</u> | <u>47.3</u> | <u>84.1</u> |

### Cross-Backbone Generalization

| Backbone / group | Method | FLOPs Ratio | Retention Ratio | MVBench | EgoSchema | MLVU | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ----: | ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| LLaVA-Video-7B baseline | LLaVA-Video-7B | 100% | 100% | 60.4 | 57.2 | 53.3 | 58.9 | 64.3 | 58.8 | 100 |
| LLaVA-Video-7B, 2% | HoliTom | 1.7% | 2%/1% | **50.2** | 46.5 | <u>39.9</u> | **50.7** | 55.3 | 48.5 | 82.5 |
| LLaVA-Video-7B, 2% | **Ours** | 1.7% | 2%/1% | <u>50.1</u> | **46.8** | **40.8** | <u>50.2</u> | **56.2** | **48.8** | **83.0** |
| LLaVA-Video-7B, 1% | HoliTom | 1.4% | 1%/0.5% | 46.4 | <u>41.1</u> | 38.9 | 48.8 | 51.7 | 45.4 | 77.2 |
| LLaVA-Video-7B, 1% | **Ours** | 1.4% | 1%/0.5% | **48.0** | **44.8** | **40.1** | **49.4** | **54.9** | **47.4** | **80.6** |
| LLaVA-OV-0.5B baseline | LLaVA-OV-0.5B | 100% | 100% | 46.6 | 26.6 | 33.5 | 47.5 | 43.7 | 39.6 | 100 |
| LLaVA-OV-0.5B, 2% | HoliTom | 1.8% | 2%/1% | 42.6 | 24.5 | <u>26.1</u> | 42.4 | 39.4 | <u>35.0</u> | <u>88.4</u> |
| LLaVA-OV-0.5B, 2% | **Ours** | 1.8% | 2%/1% | <u>42.7</u> | **24.8** | **26.4** | <u>45.2</u> | <u>40.4</u> | **35.9** | **90.7** |
| Qwen2.5-VL-7B baseline | Qwen2.5-VL | 100% | 100% | 63.0 | 52.8 | 38.5 | 55.0 | 57.5 | 53.4 | 100.0 |
| Qwen2.5-VL-7B, 2% | FastVID | not reported | 2% | 51.8 | 46.2 | 30.6 | 45.0 | <u>46.4</u> | 44.0 | 82.5 |
| Qwen2.5-VL-7B, 2% | **Ours (w/o M)** | not reported | 2% | **54.1** | <u>47.8</u> | **32.7** | <u>45.4</u> | **48.1** | **45.6** | **85.5** |
| Qwen2.5-VL-7B, 2% | **Ours** | not reported | 2% | <u>53.7</u> | **48.4** | <u>31.8</u> | **45.6** | **48.1** | <u>45.5</u> | <u>85.3</u> |

### Ablations / Analysis

**Module ablation at 2% retention.** 这里的 Avg % 以 LLaVA-OV-7B baseline 为 100%。

| Attn | Sim | Cluster | MVBench | EgoSchema | MLVU | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| yes | no | no | 41.4 | 46.6 | 30.8 | 44.7 | 45.3 | 41.8 | 74.2 |
| no | yes | no | 51.4 | 55.1 | 38.8 | 50.0 | 50.9 | 49.2 | 87.5 |
| no | no | yes | 52.2 | 55.0 | 36.3 | 48.4 | 51.3 | 48.6 | 86.4 |
| yes | yes | no | 52.1 | 56.8 | 38.4 | 49.9 | 51.2 | 49.7 | 88.2 |
| yes | no | yes | 48.3 | 51.4 | 33.2 | 46.4 | 49.5 | 45.8 | 81.3 |
| no | yes | yes | 51.8 | 55.5 | 38.4 | 50.6 | 51.0 | 49.5 | 87.9 |
| yes | yes | yes | **52.9** | **57.2** | **39.5** | **51.0** | **51.3** | **50.4** | **89.5** |

**Text-aware merging layer K.**

| Method | K | MVBench | EgoSchema | MLVU | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | - | 58.3 | 60.4 | 47.7 | 56.4 | 58.6 | 56.3 | 100 |
| Ours | 2 | 48.7 | 52.7 | 36.7 | 47.8 | 49.4 | 47.1 | 83.6 |
| Ours | 7 | 50.3 | 54.0 | 36.6 | 47.8 | 49.5 | 47.6 | 84.6 |
| Ours | 14 | **52.9** | 55.7 | 39.7 | **51.1** | 51.4 | 50.2 | 89.1 |
| Ours | 18 | 52.8 | **57.6** | **40.3** | 50.8 | **51.8** | **50.7** | **90.1** |
| Ours | 21 | 52.8 | 57.1 | 39.9 | 50.3 | 51.7 | 50.4 | 89.5 |

**Hyperparameters.**

| Hyperparameter | Best reported value | Evidence |
| ---- | ---- | ---- |
| Similarity threshold $\tau$ | 0.7 | Avg Score 50.4 / Avg % 89.5 at 2% tokens; $\tau=0.6$ has Avg Score 50.3，$\tau=0.8$ drops to 49.7。 |
| Cluster ratio | 0.3 | Avg Score 50.4 / Avg % 89.5；0.5 接近但 Avg Score 50.2。 |
| Text-aware balance $\lambda$ | 0.5 | Avg Score 50.7 / Avg % 90.1；0、0.25、1 都是 50.5，0.75 为 50.4。 |
| Inner pruning start layer $K$ | 18 | K=18 在主 ablation 中取得 Avg Score 50.7 / Avg % 90.1。 |

**Efficiency.**

| Method | Process (ms) | Prefill (ms) | TTFT (ms) | Throughput (token/s) | Score |
| ---- | ----: | ----: | ----: | ----: | ----: |
| Vanilla | - | 701.2 (1x) | 1104.7 | 27.6 | 56.3 |
| VisionZip | 35.8 | 42.1 (17x) | 451.6 | 35.4 | 45.8 |
| FastVid | **8.6** | 43.1 (16x) | **446.2** | 33.8 | 46.9 |
| HoliTom | 88.7 | 40.5 (17x) | 497.4 | 34.3 | 49.4 |
| Ours | 74.0 | **31.3 (22x)** | 473.8 | **35.7** | **50.7** |

**Higher frame sampling at 2% token retention.**

| Method | Frames | FLOPs (T) | VideoMME Short | VideoMME Medium | VideoMME Long | VideoMME Total |
| ---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | 16 | 19.0 | 68.2 | 53.8 | 48.2 | 56.7 |
| HoliTom | 64 | 1.7 | 63.0 | 53.9 | 46.3 | 54.4 |
| Ours | 64 | 1.7 | 62.4 | 53.3 | 47.6 | 54.5 |
| HoliTom | 96 | 2.2 | 64.1 | 52.4 | 45.9 | 54.1 |
| Ours | 96 | 2.2 | 65.8 | 55.0 | 46.8 | 55.9 |
| HoliTom | 128 | 2.8 | 66.2 | 53.2 | 46.8 | 55.4 |
| Ours | 128 | 2.8 | **68.4** | **55.3** | **50.2** | **58.0** |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training requirement | not required; training-free plug-and-play module |
| Main backbone | LLaVA-OneVision-7B |
| Additional backbones | LLaVA-Video-7B, LLaVA-OneVision-0.5B, Qwen2.5-VL-7B |
| Hardware | single NVIDIA RTX 4090 or A100 |
| LLaVA-OneVision video sampling | 32 frames per video |
| LLaVA-OneVision visual tokens | $N_v=196$ visual tokens per frame |
| LLaVA-Video video sampling | 64 frames per video |
| LLaVA-Video visual tokens | $N_v=169$ visual tokens per frame |
| External similarity threshold | $\tau=0.7$ |
| Cluster ratio | 0.3 |
| Internal LLM pruning layer | start from $K=18$ |
| Internal LLM retention | top $R=50\%$ visual tokens |
| Text-aware balance | $\lambda=0.5$ |
| Evaluation toolkit | LMMs-Eval |
| FLOPs metric | Prefilling + decoding FLOPs; supplementary formula fixes generated decoding tokens as $R=100$ |

## Limitations & Caveats

- 论文明确说明当前方法只支持 fixed offline videos，尚不支持 real-time streaming token compression。
- Uniform frame sampling 可能在短视频中采到冗余帧，也可能在长视频中错过关键片段；作者把 joint frame selection + token compression 作为 future work。
- 方法虽然 training-free，但需要访问 visual encoder/LLM 的 attention 或 hidden states；实际部署到黑盒 API 式 Video-LLM 时未必可直接实现。
- ActivityNet-QA 的 open-ended evaluation 使用 GPT-3.5-Turbo 做 evaluator，因此分数会受到 evaluator 稳定性和 prompt 设定影响。
- 主结果强调 ultra-low retention，但高 retention 区间存在 performance plateau；如果部署场景不受 compute/memory 强约束，收益可能主要体现在 latency/throughput 而非 accuracy。

## Concrete Implementation Ideas

1. 把外部 compression 做成 projector 后、LLM 前的 wrapper：输入 visual tokens，输出按原始时空顺序排列的 compressed visual tokens，并暴露 `target_retention`, `tau`, `cluster_ratio`。
2. 在 Video-LLM 推理框架里加一个 profiling mode，记录 retention ratio、prefill time、TTFT、throughput、KV cache memory，复现实验里的 efficiency table。
3. 对业务视频先做 adaptive frame sampling，再套 unified token compression；这样可以直接针对论文指出的 uniform frame sampling limitation 做改进。
4. 做一个 query-aware 可视化工具：显示 text-aware merging 中每个 query token 对 visual tokens 的 attention/similarity contribution，帮助分析“为什么保留这些 token”。
5. 如果目标是 streaming video，可把 retention/recycle pool 改为滑动窗口版本：只维护最近窗口和少量全局 memory tokens，再做 incremental clustering。

## Open Questions / Follow-ups

- 在没有显式 CLS token 的 encoder 上，用平均 attention 近似 CLS contribution 是否在所有 architecture 中都稳定？Qwen2.5-VL 的 window attention 场景尤其值得继续拆解。
- DPC-KNN clustering 的额外开销在长视频、大 batch 或实时场景下是否会抵消部分 latency gain？
- Text-aware merging 从 $K=18$ 开始最优，这是否与 LLaVA-OneVision-7B 的层数/语义对齐阶段绑定？换成更大模型或不同 RoPE 设定后是否需要重新搜索？
- 如果 question 在解码过程中被改写或生成链路较长，固定 prefill 阶段的 query relevance 是否足够？
- 与 adaptive frame selection、KV cache compression、speculative decoding 等系统优化叠加时，收益是否近似相加？

## Citation

```bibtex
@article{du2026unified,
  title={Unified Spatiotemporal Token Compression for Video-LLMs at Ultra-Low Retention},
  author={Du, Junhao and Xue, Jialong and Li, Anqi and Dai, Jincheng and Lu, Guo},
  journal={arXiv preprint arXiv:2603.21957},
  year={2026},
  note={Accepted by CVPR 2026},
  url={https://arxiv.org/abs/2603.21957}
}
```
