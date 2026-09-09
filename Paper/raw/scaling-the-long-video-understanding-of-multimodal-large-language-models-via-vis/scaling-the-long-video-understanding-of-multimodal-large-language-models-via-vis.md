---
title: FlexMem
authors:
  - Tao Chen
  - Kun Zhang
  - Qiong Wu
  - Xiao Chen
  - Chao Chang
  - Xiaoshuai Sun
  - Yiyi Zhou
  - Rongrong Ji
conference: CVPR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2603.29252
pdf_link: "[[assets/paper_2603.29252.pdf]]"
cover: "[[_assets/images/pipeline_2603.29252.png]]"
updated: 2026-05-13
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
rating:
topics:
  - Video Understanding
code: https://github.com/city1517/FlexMem
---

## TL;DR

- 论文提出 **FlexMem**，一个 training-free 的长视频理解方法，把 Video-MLLM 的 visual KV caches 当作可写入、可回忆的视觉记忆。
- 核心思路是让 MLLM 逐段观看视频：每个 clip 生成两类压缩记忆，`Context Memory` 用于跨 clip 信息传播，`Local Memory` 写入 memory bank 用于最终问答。
- 方法包含两种 memory reading：一种基于 question encoding 时的 cross-attention，另一种是更快的 **MemIndex**，用少量 cache layers 和 token index 近似 encoding-based retrieval。
- 在 LLaVA-Video 与 LLaVA-OneVision 上，FlexMem 可处理 512/1024 frames，并在多个 long VideoQA benchmark 上优于 AKS、AdaRETAKE 等高效长视频方法。
- 在 single 3090 GPU setting 下，FlexMem 仍可使用 13k decoding tokens 处理 512/1024 frames，并在五个 benchmark 上取得最高或并列最高结果。
- Caveat：MemIndex 在 streaming/backward tracing 上整体提升，但对 ASI 这类 task 并非单调更好；此外部分 full-comparison 结果标注为 A800 测试。

## Key Contributions

1. 从 **visual memory mechanism** 角度建模 long video understanding，目标是让 MLLM 像人一样连续观看、形成记忆、再根据问题回忆关键片段。
2. 提出 **Dual-Pathway Compression (DPC)**：用不同 attention-based scores 分别产生适合信息传播的 `Context Memory` 与适合答案生成的 `Local Memory`。
3. 设计两类 memory reading：encoding-based retrieval 使用 question-visual cross-attention；**MemIndex** 则用 compact index tensors 支持多问题和 streaming 场景。
4. 在五个 long VideoQA benchmarks 与一个 streaming/backward tracing task 上验证 FlexMem；作者报告其在单张 3090 GPU 上也能处理超过 1k frames。

## Method

FlexMem 将长视频 $V$ 划分为 $N$ 个 clips：$V=\{V_1,\cdots,V_N\}$。对每个 clip，MLLM 不再一次性吞入全部 visual tokens，而是迭代生成两类 KV-cache memory：

- `Context Memory` $C_i$：用于下一步 prefill 时传递历史上下文，使后续 clip 编码能看到短期历史。
- `Local Memory` $M_i$：写入 visual memory bank $M_{bank}$，用于最终 answer decoding 或后续 long-term recall。

第一步可写成：

$$
\text{MLLM}(V_1, \langle T_q \rangle)\rightarrow M_1, C_1
$$

后续第 $k$ 步会读取最近 context memories、当前 clip，并可选地读取部分 long-term memories 与文本问题：

$$
\text{MLLM}(\langle M_l \rangle,C_{k-n_s},...,C_{k-1}, V_k, \langle T_q \rangle)\rightarrow M_k, C_k
$$

视频看完后，FlexMem 从 memory bank 中召回最相关的 memory pieces，并用它们回答问题：

$$
\text{Recall}(M_{bank},T_q) \rightarrow M_i,...,M_{i+n_a-1}
$$

$$
\text{MLLM}(M_i,...,M_{i+n_a-1},T_q)\rightarrow Y
$$

**Dual-Pathway Compression.** DPC 的两个 score 对应 prefill 与 decoding 的不同需求：

- Context aggregation score 关注当前 token 是否能聚合历史 context、并向同 clip 内后续 token 传播信息：

$$
s^{l}_j = \sum_{k \in C} a_{jk}^l + \sum_{h \in V_i} a_{hj}^l
$$

- Local saliency score 关注 token 在当前 clip 内的显著性，用于保留更适合最终回答的 local evidence：

$$
\hat{s}^l_j = \sum_{k \in V_i} a_{kj}^l
$$

**Memory Reading.** Encoding-based reading 直接使用 question tokens 到 visual tokens 的 cross-attention 作为 clip relevance：

$$
g_i = \sum_{l =3}^L \sum_{j \in T_q}  \sum_{k \in V_i} a_{jk}^l
$$

作者指出浅层 attention 对 visual tokens 往往较均匀，因此实际只用第 3 层之后的 deeper layers。

**MemIndex.** 为避免新问题反复触发 MLLM video encoding，MemIndex 把 encoding-based retrieval 视作 upper bound，用 linear regression 拟合每层 relevance：

$$
\arg\min_{\sigma} \sum_{i=1}^D \left\| \sigma(R_i)  - g_i \right\|_2,\quad
\sigma(R_i)=\sum_{l=3}^L \alpha^l r_i^l
$$

然后选取 top-$K$ representative cache layers，并用 last question token 与少量 visual key vectors 做 compact matching。实验实现中使用 $K=3$ visual cache layers 与 $k=5$ visual index features。

```text
FlexMem pipeline
1. Split long video into clips.
2. For each clip:
   a. Encode current clip with recent context memories.
   b. Compress KV caches into Context Memory C_i and Local Memory M_i.
   c. Store M_i in visual memory bank; keep C_i for iterative propagation.
3. For a question:
   a. Recall relevant memories by encoding-based reading or MemIndex.
   b. Decode the final answer using recalled memories plus text instruction.
```

## Pipeline Figure

![[_assets/images/pipeline_2603.29252.png]]

Caption: Illustration of the proposed FlexMem method. The figure shows iterative clip encoding, Context Memory and Local Memory construction, visual memory bank recall, encoding-based indexing, and MemIndex with compact question/visual index tensors.

Source: TeX includegraphics from `sec/2_related_work.tex`, rendered from `figs/overview.pdf` using the PDF crop box.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MLVU | Long video understanding / multi-task VideoQA | not reported | M-avg | 视频长度从 3 分钟到 2 小时，强调 comprehensive temporal understanding。 |
| LongVideoBench | Long-context interleaved video-language understanding | Short / Medium / Long / All | Accuracy-like score | 视频最长约 1 小时，强调细粒度 retrieval 与 reasoning。 |
| LVBench | Extreme long video understanding | Val | Accuracy-like score | 平均视频时长约 68.4 分钟，强调 long-term memory retention。 |
| Video-MME | Multi-duration video understanding | Short / Medium / Long / All | Accuracy-like score | 覆盖 diverse genres 与 short/medium/long-form content。 |
| TimeScope | Long video capability probing | Test | Accuracy-like score | 视频从 1 分钟到 8 小时。 |
| OVOBench | Streaming / backward tracing QA | EPM / ASI / HLD / Average | Task scores | 用于验证 FlexMem + MemIndex 在 streaming QA 下的历史信息追踪。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training | Training-free；无需额外 fine-tuning。 |
| Base MLLMs | LLaVA-Video 7B, LLaVA-OneVision 7B |
| Long VideoQA reading | Encoding-based reading |
| Streaming QA reading | FlexMem + MemIndex |
| Sampled frames | TimeScope / LVBench / MLVU: 512 frames；Video-MME / LongVideoBench: 1024 frames |
| Final decoding tokens | LLaVA-Video: 13k；LLaVA-OneVision: 7k |
| MemIndex settings | $K=3$ visual cache layers；$k=5$ visual index features |
| Limited-memory setting | Single 3090 GPU / 24GB memory budget |
| Full FlexMem comparison note | 表中带 $^*$ 的 FlexMem 结果标注为 tested on one A800。 |

### Main Results

下面两张主表保留原论文对 best / second-best 的强调：source bold 记为 **bold**，source underline 记为 `<u>underline</u>`。

**Comparison with SOTA efficient methods on LLaVA-Video 7B**

| Method | Sampled Frames | Input Tokens | TimeScope Test | LVBench Val | MLVU M-avg | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME All | LongVideoBench Short | LongVideoBench Medium | LongVideoBench Long | LongVideoBench All |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-Video 7B | 64frm | 13k | 65.0 | 42.6 | 71.2 | 76.1 | 61.0 | 52.4 | 63.2 | 71.5 | 60.7 | 52.1 | 60.0 |
| AKS | 1fps | 13k | 85.4 | 47.4 | 72.0 | **77.2** | **64.8** | 53.9 | **65.3** | **72.3** | <u>62.1</u> | **57.4** | <u>62.7</u> |
| Panels | 1fps | 13k | 79.2 | - | - | - | 62.2 | <u>54.0</u> | 64.4 | - | - | - | - |
| DToMA | - | 12k | - | - | 71.7 | - | - | - | <u>65.0</u> | - | - | - | 59.6 |
| Video-RAG | - | 15k | - | - | **72.4** | - | - | - | - | - | - | - | 58.7 |
| AdaRETAKE | 1024frm | 40k | **86.2** | <u>49.6</u> | 71.7 | 75.8 | 62.0 | 52.9 | 63.6 | 69.7 | 59.2 | 52.8 | 59.4 |
| **FlexMem**$^*$ | 512/1024frm | 13k | <u>85.9</u> | **51.0** | **72.4** | <u>76.3</u> | <u>63.3</u> | **54.4** | 64.7 | <u>71.5</u> | **65.5** | <u>57.3</u> | **63.6** |

**Comparison with SOTA efficient methods on LLaVA-OneVision 7B**

| Method | Sampled Frames | Input Tokens | TimeScope Test | LVBench Val | MLVU M-avg | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME All | LongVideoBench Short | LongVideoBench Medium | LongVideoBench Long | LongVideoBench All |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-OV 7B | 32frm | 7k | 56.3 | 38.4 | 63.4 | <u>70.6</u> | 54.8 | 48.2 | 57.8 | **69.5** | 53.4 | 49.8 | 56.2 |
| AKS | 1fps | 7k | - | <u>43.5</u> | <u>68.3</u> | - | - | - | 58.4 | 65.9 | **58.9** | <u>54.3</u> | <u>58.9</u> |
| Panels | 1fps | 7k | 69.5 | - | - | - | 56.2 | <u>50.2</u> | 58.9 | - | - | - | - |
| BOLT | 1fps | 7k | - | - | 65.8 | 69.2 | <u>56.8</u> | 47.3 | 57.8 | - | - | - | 57.0 |
| AdaRETAKE | 1024frm | 20k | <u>75.8</u> | 42.1 | 64.4 | **72.1** | 53.6 | **51.4** | **59.0** | <u>68.5</u> | 51.0 | 47.2 | 54.2 |
| **FlexMem**$^*$ | 512/1024frm | 7k | **80.5** | **46.2** | **68.9** | 70.0 | **57.3** | 49.8 | **59.0** | 67.9 | <u>58.0</u> | **55.0** | **59.4** |

**Single 3090 GPU limited-memory comparison on LLaVA-Video**

| Method | Sampled Frames | Input Tokens | TimeScope Test | LVBench Val | MLVU M-avg | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME All | LongVideoBench Short | LongVideoBench Medium | LongVideoBench Long | LongVideoBench All |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-Video 7B | 32frm | 7k | 58.3 | 41.4 | 68.5 | <u>74.8</u> | 58.4 | 52.0 | 61.7 | <u>70.6</u> | 59.0 | 50.5 | 58.6 |
| AKS | 1fps | 7k | <u>84.6</u> | 46.6 | 70.8 | 74.7 | <u>61.9</u> | 51.7 | 62.8 | 68.1 | 60.0 | <u>54.1</u> | 59.7 |
| AdaRETAKE | 384frm | 40k | 78.2 | <u>46.8</u> | <u>71.7</u> | 74.7 | 61.8 | <u>54.3</u> | <u>63.6</u> | 69.0 | <u>60.4</u> | 53.5 | <u>59.8</u> |
| **FlexMem** | 512/1024frm | 13k | **85.6** | **50.2** | **72.3** | **76.2** | **62.7** | **55.0** | **64.6** | **71.5** | **63.6** | **57.2** | **63.0** |

**Comparison with SOTA Video-MLLMs**

| Method | LLM | TimeScope Test | LVBench Val | MLVU M-avg | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME All | LongVideoBench Medium | LongVideoBench Long | LongVideoBench All |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| GPT-5 | - | - | - | 77.3 | - | - | - | 81.8 | - | - | 72.6 |
| GPT-4o | - | - | 27.0 | 64.6 | 80.0 | 70.3 | 65.3 | 71.9 | 69.1 | 60.9 | 66.7 |
| Gemini-1.5-Pro | - | - | 33.1 | - | 81.7 | 74.3 | 67.4 | 75.0 | 65.3 | 58.6 | 64.0 |
| Video-XL | 7B | - | - | 64.9 | 62.0 | 53.2 | 49.2 | 55.5 | 49.0 | 45.2 | 50.5 |
| mPLUG-Owl3 | 7B | - | 43.5 | 63.7 | 70.0 | 57.7 | 50.1 | 59.3 | - | - | 52.1 |
| Qwen2.5-VL | 7B | <u>81.0</u> | <u>45.3</u> | 70.2 | - | - | - | <u>65.1</u> | - | - | 56.0 |
| TimeMarker | 8B | - | 41.3 | 63.9 | 71.0 | 54.4 | 46.4 | 57.3 | - | - | 56.3 |
| LongVU | 7B | - | - | 65.4 | - | - | **59.5** | 60.6 | - | - | - |
| TSPO | 7B | - | <u>45.3</u> | **76.3** | - | - | 54.7 | **65.5** | - | - | **63.9** |
| LongVA | 7B | 55.9 | - | 56.3 | 61.1 | 50.4 | 46.2 | 52.6 | - | - | - |
| ByteVideoLLM | 14B | - | - | 70.1 | 74.4 | <u>62.9</u> | <u>56.4</u> | 64.6 | - | - | - |
| LLaVA-Video | 7B | 65.0 | 42.1 | 71.2 | <u>76.1</u> | 61.0 | 52.4 | 63.2 | <u>60.7</u> | <u>52.1</u> | 60.0 |
| **+ FlexMem** | 7B | **85.9** | **51.0** | <u>72.4</u> | **76.3** | **63.3** | 54.4 | 64.7 | **65.5** | **57.3** | <u>63.6</u> |

**Streaming QA / backward tracing on OVOBench**

| Methods | LLM | # Frames | EPM | ASI | HLD | Average |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Gemini-1.5-Pro | - | - | 58.6 | 76.4 | 52.6 | 62.5 |
| InternVL-V2 | 8B | 64 | <u>48.2</u> | 57.4 | <u>24.7</u> | <u>43.4</u> |
| LongVU | 7B | 1fps | 40.7 | <u>59.5</u> | 4.8 | 35.0 |
| Flash-VStream | 7B | 1fps | 39.1 | 37.2 | 5.9 | 27.4 |
| VideoLLM-online | 8B | 2fps | 22.2 | 18.8 | <u>12.2</u> | 17.7 |
| Dispider | 7B | 1fps | <u>48.5</u> | <u>55.4</u> | 4.3 | <u>36.1</u> |
| LLaVA-Video | 7B | 64 | 55.2 | **60.8** | 42.5 | 52.8 |
| **+ FlexMem w. MemIndex** | 7B | 1fps | **57.6** | 54.1 | **49.5** | **54.4** |

### Ablations / Analysis

**Encoding-based reading ablations**

| Group | Variant / Setting | LongVideoBench Short | LongVideoBench Medium | LongVideoBench Long | LongVideoBench All | LVBench Val |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Compression Strategy | Context Compression Only | 70.1 | 64.3 | 56.2 | 62.5 | 49.9 |
| Compression Strategy | Local Compression Only | 70.9 | 64.6 | 55.9 | 62.6 | 49.7 |
| Compression Strategy | Dual-Pathway$^{\ddag}$ | 71.5 | 65.5 | 57.3 | 63.6 | 51.0 |
| Context during Prefill | Context Memory Only | 71.2 | 65.0 | 53.5 | 61.9 | 50.5 |
| Context during Prefill | Local Memory Only | 71.2 | 63.3 | 54.6 | 61.8 | 50.0 |
| Context during Prefill | Combination of both$^{\ddag}$ | 71.5 | 65.5 | 57.3 | 63.6 | 51.0 |
| Context during Decoding | All $M_{bank}$ | 71.5 | 58.7 | 53.2 | 59.8 | 49.3 |
| Context during Decoding | Memory Reading$^{\ddag}$ | 71.5 | 65.5 | 57.3 | 63.6 | 51.0 |
| Number of Frames in Each Clip | 8$^{\ddag}$ | 71.5 | 65.5 | 57.3 | 63.6 | 51.0 |
| Number of Frames in Each Clip | 16 | 71.5 | 64.8 | 57.1 | 63.4 | 50.1 |
| Number of Frames in Each Clip | 32 | 70.1 | 62.6 | 55.7 | 61.7 | 49.3 |

这里的趋势比较清楚：Dual-Pathway 优于只做 context/local 的单路压缩；prefill 时同时使用 context memory 与 local memory 最好；decoding 时从 memory bank 召回少量相关 memory 明显优于直接加载全部 $M_{bank}$。

**MemIndex design ablations**

| Layers | Text | Vision | MLVU Single | MLVU Multi | MLVU Holistic | MLVU M-avg | LVBench Val |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Encoding-based Index | - | - | 77.1 | 54.8 | 77.3 | 72.4 | 51.0 |
| All | All | All | 76.9 | 54.0 | 77.1 | 72.0 | 46.3 |
| 3 | All | All | 77.2 | 53.3 | 77.5 | 72.2 | 46.6 |
| 3 | Last-Token | All | 77.4 | 53.3 | 77.3 | 72.3 | 46.8 |
| 3 | Last-Token | AttEnc | 77.1 | 53.1 | 77.5 | 72.1 | 45.7 |

MemIndex 在 MLVU M-avg 上几乎逼近 encoding-based index，但 LVBench Val 有明显差距。这说明 compact index 对某些 long-context retrieval 场景可能仍会损失信息。

## Limitations & Caveats

- 论文强调 training-free，但实际实现仍需要访问和重排 Video-MLLM 内部 KV caches；这对封闭模型或不暴露 cache 的 inference stack 不友好。
- FlexMem 的 memory bank 随 clip 数增长，虽然每个 memory 被压缩，但论文正文没有给出足够细的端到端 memory growth / latency curve。
- Full comparison 中 FlexMem$^*$ 标注为 A800 测试，而 single-3090 表是另一组 limited-memory setting；跨表比较时要注意硬件条件。
- MemIndex 对 streaming/backward tracing 的 average 有提升，但 ASI 从 LLaVA-Video 的 60.8 降到 54.1，说明 compact retrieval 对某些 action sequence 类型问题可能不稳定。
- Encoding-based reading 对新问题可能需要重复进行带 question 的 memory encoding；MemIndex 是为了解决这个问题，但其拟合和 layer/token 选择的跨模型泛化还需要更多验证。

## Concrete Implementation Ideas

1. 在 LLaVA-Video 推理栈里增加 KV-cache hook：按 8-frame clip 切分视频，保存每层 visual token 的 key/value 与 attention map。
2. 先实现 encoding-based FlexMem：使用 $s_j^l$ 选出 `Context Memory`，使用 $\hat{s}_j^l$ 选出 `Local Memory`，再用 $g_i$ 召回 top-$n_a$ clips 做 final decoding。
3. 对多问题或 streaming QA，再加入 MemIndex：离线拟合每层权重 $\alpha^l$，运行时只保留 top-$K=3$ layers 与每 clip 的 $k=5$ visual index features。
4. 评估时优先复现 single-3090 table：对 LLaVA-Video 使用 13k decoding token budget，Video-MME / LongVideoBench 用 1024 frames，其余长视频 benchmark 用 512 frames。
5. 加 ablation flags：`context_only`、`local_only`、`dual_pathway`、`all_memory_decode`、`memory_reading`、`clip_size=8/16/32`，方便定位收益来自压缩、传播还是召回。

## Open Questions / Follow-ups

- Memory bank 的实际显存/延迟曲线如何随视频时长增长？“theoretically infinite-long videos” 在工程上对应的 upper bound 是什么？
- MemIndex 的 layer selection 是否能从 LLaVA-Video 迁移到 LLaVA-OneVision、Qwen2.5-VL、InternVL 等不同架构？
- 如果同一视频对应大量问题，是否可以完全 question-independent 地构建 memory bank，再用 MemIndex 回答所有问题？
- 对 ASI 这类 action sequence 任务，MemIndex 为什么低于原始 LLaVA-Video？是 compact index 丢掉了顺序信息，还是 recall/window 设计不适配？
- FlexMem 与现有 frame selection / temporal grounding 方法能否结合，例如先用 cheap retrieval 缩小范围，再在候选范围内做 KV-memory recall？

## Citation

```bibtex
@misc{chen2026scalinglongvideounderstanding,
      title={Scaling the Long Video Understanding of Multimodal Large Language Models via Visual Memory Mechanism}, 
      author={Tao Chen and Kun Zhang and Qiong Wu and Xiao Chen and Chao Chang and Xiaoshuai Sun and Yiyi Zhou and Rongrong Ji},
      year={2026},
      eprint={2603.29252},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2603.29252}, 
}
```
