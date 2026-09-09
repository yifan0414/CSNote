---
title: "MuKV: Multi-Grained KV Cache Compression for Long Streaming Video Question-Answering"
authors: ["Junbin Xiao", "Jiajun Chen", "Tianxiang Sun", "Xun Yang", "Angela Yao"]
conference: "CVPR"
year: 2026
arxiv_url: "https://arxiv.org/abs/2605.22269"
pdf_link: "[[assets/paper_2605.22269.pdf]]"
cover: "[[_assets/images/pipeline_2605.22269.png]]"
updated: 2026-06-06
tags: ["paper/arxiv", "video-qa", "long-video", "temporal-reasoning", "token-pruning", "video-llm"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: ""
---

## TL;DR

- MuKV 面向无限增长的 long streaming VideoQA，将历史视频保存为可直接用于 LLM decoding 的 KV cache，并同时追求高准确率、低在线延迟和有限离线存储。
- 核心表示不是单一 frame-level cache，而是 patch、frame、segment 三种粒度；它们分别保留局部细节、单帧语义和跨帧 temporal context。
- Dual-Signal KV-Cache Compression（DCP）融合 last-layer self-attention 与 FFT frequency signal，按粒度采用不同保留率，压缩冗余 KV token。
- 在线阶段先对三种粒度并行检索，再用高层 segment 表示校准低层候选，形成 semi-hierarchical retrieval。
- 在相同 59K memory tokens 下，MuKV-7B 相比 ReKV-7B 将 StreamingBench overall accuracy 从 62.3 提升到 64.4，并把 inference tokens 从 12.5K 降到 8.3K。
- 方法 training-free、model-agnostic；但对 Counting 等高度依赖细粒度变化的任务仍较弱，且效果对 sampling FPS、数据分布和压缩比例敏感。

## Key Contributions

1. 提出面向 streaming VideoQA 的 **multi-grained KV cache**：每个视频 segment 同时构造 patch、frame、segment 级别的 KV 表示，以兼顾空间细节和长程 temporal semantics。
2. 提出 **Dual-Signal KV-Cache Compression（DCP）**：融合 self-attention importance 与 token frequency，证明 frequency signal 能校正 attention 的位置偏置，并用于有效 token pruning。
3. 提出 **semi-hierarchical retrieval**：先跨粒度独立并行检索，再由 segment-level global context 对低粒度候选重排。
4. 在不增加 memory tokens 的条件下提升准确率和在线效率，并展示 DCP 可作为独立压缩模块增强 ReKV。

## Method

### Problem Setup

给定持续到达的视频流 $\mathcal{V}=\{f_t\}_{t=1}^{T}$，用户会在未知时间点 $t_i$ 提出问题 $q_i$。系统只能使用 $t_i$ 之前的视频内容回答，同时必须控制不断增长的历史 memory，并满足实时 QA 延迟要求。

### Offline Multi-Grained KV Memory

每个时间步处理一个含 $F$ 帧的 segment $v_t$，并从相同 visual tokens 分组得到三种粒度：

- **Segment-level** $v_t$：包含整个 segment 的 tokens，用于跨帧动作与事件语义。
- **Frame-level** $f_t$：使用 segment 的中间帧，保存单帧内容。
- **Patch-level** $p_{f_t}$：将中间帧划分为 $S$ 个 super-patches，保存区域级变化。

三种表示分别执行 LLM prefill，并在实践中并行运行。对每种粒度，MuKV 保存所有 Transformer layers 的 KV slices、对应时间戳，以及用于压缩的 attention weights。

### Dual-Signal KV-Cache Compression

以 frame-level tokens 为例，MuKV 从最后一层聚合 self-attention，得到 token importance：

$$
\mathbf{I}_{\text{att}}
=
\frac{1}{H P}
\sum_{h=1}^{H}
\sum_{i=1}^{P}
\mathbf{A}^{(L)}_{h,i}.
$$

随后沿 token sequence 对 key vectors 做 FFT，并对维度求均值得到 frequency indicator：

$$
\mathbf{Z}_{\text{fft}} = FFT(\mathbf{k}^{P \times D}),
\qquad
\mathbf{I}_{\text{fft}} = Mean(\mathbf{Z}_{\text{fft}}^{P \times D}).
$$

归一化后用加权和融合两个信号：

$$
\mathbf{I}_{f_t}
=
\alpha_{f_t}\widehat{\mathbf{I}}_{\text{att}}
+
(1-\alpha_{f_t})\widehat{\mathbf{I}}_{\text{fft}}.
$$

每种粒度按融合分数排序，仅保留 top-$\kappa_g$ tokens，其中 $\kappa_g=\lfloor\rho_g |g|\rfloor$。不同 $\rho_g$ 反映不同粒度的功能差异：论文默认更积极压缩 patch/frame，同时保留更多 segment tokens。

### Online Semi-Hierarchical Retrieval

1. 对每个 KV block 的 last-layer key vectors 做 mean pooling，得到 block representation。
2. 对问题 query tokens 做 mean pooling，形成全局问题表示 $\mathbf{q}$。
3. **Stage 1:** 在 patch、frame、segment 三种粒度内分别计算 cosine similarity，各取 top-$2k_g$ candidates。
4. **Stage 2:** 聚合 top segment candidates 得到 global query，并用它计算低粒度候选的一致性分数 $\gamma_j$。
5. 更新候选分数并取每种粒度 top-$k_g$：

$$
\widetilde{s}_j=(1-\lambda_g)s_j+\lambda_g\gamma_j.
$$

6. 将选中的 KV caches 直接作为 LLM context，与问题 tokens 一起 autoregressive decoding。

### Compact Pipeline

```text
video segment
  -> group visual tokens into patch / frame / segment representations
  -> parallel LLM prefill for three granularities
  -> DCP: attention score + FFT frequency score
  -> granularity-adaptive top-token retention
  -> timestamped offline KV memory

question at time t
  -> parallel retrieval within each granularity
  -> segment-guided cross-grain reranking
  -> load selected KV caches
  -> answer decoding
```

## Pipeline Figure

![[_assets/images/pipeline_2605.22269.png]]

Caption: Illustration of multi-grained video KV cache compression in offline memory.

Source: TeX `\includegraphics` from `sec/3_method.tex`, rendered from `figures/mukv.pdf` using the PDF crop box.

## Experiments

### Datasets

| Dataset | Task | Split / Scale | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| RVS-Ego / RVSEgo | Long streaming VideoQA | Main text: 1.4K questions, 11 egocentric videos, avg. 30 min | LLM-judge Acc, Score | Supplementary 写为 10 videos，与正文不一致 |
| RVS-Movie / RVSMovie | Long streaming VideoQA | Main text: 1.9K questions, 20 movies, avg. 1 h | LLM-judge Acc, Score | Supplementary 写为 22 videos，与正文不一致；answer-span ratio 更低 |
| StreamingBench Real-Time subset | Real-time visual understanding | 2.5K questions, 500 videos, avg. 10 min | Multi-choice accuracy | 10 类问题：OP, CR, CS, ATP, EU, TR, PR, SU, ACP, CT |
| MLVU | Offline long VideoQA | Supplementary evaluation | Accuracy | 假设问题在视频结尾提出 |
| EgoSchema | Offline long VideoQA | Supplementary evaluation | Accuracy | 假设问题在视频结尾提出 |
| Video-MME | Offline long VideoQA | Medium / Long / All | Accuracy | Supplementary evaluation |

### Main Results

下表采用正文中使用当前 GPT-3.5-turbo judge 的结果；论文将旧 GPT-3.5-turbo-0613 judge 结果单独灰显，因此不与其混合比较。

| Method | Size | Inf. Tok. ↓ | Mem. Tok. ↓ | RVSEgo Acc ↑ | RVSMovie Acc ↑ | StreamingBench All ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FVStream | 7B | -- | -- | 58.5 | **54.7** | 24.3 |
| LongVA (128F) | 7B | 18.4K | 0 | -- | -- | 60.0 |
| ReKV | 0.5B | 12.5K | 59K | 51.5 | 42.3 | 52.7 |
| **MuKV (Ours)** | 0.5B | 8.3K | 59K | **57.9** | **45.2** | **56.8** |
| ReKV | 7B | 12.5K | 59K | 56.2 | 48.2 | 62.3 |
| **MuKV (Ours)** | 7B | 8.3K | 59K | **59.5** | 48.5 | **64.4** |

与同规模 ReKV 相比：

- MuKV-0.5B 在 RVSEgo / RVSMovie / StreamingBench All 分别提升 $+6.4 / +2.9 / +4.1$ points。
- MuKV-7B 分别提升 $+3.3 / +0.3 / +2.1$ points，同时 inference tokens 从 12.5K 降到 8.3K。
- MuKV-7B 在 StreamingBench 的 CR、CS、EU、PR 等高层理解类别明显领先，但 Counting 从 ReKV 的 46.3 降到 39.4。

### Offline Long VideoQA

| Backbone / Method | Frames / FPS | Mem. Tok. | MLVU | EgoSchema | Video-MME Medium | Video-MME Long | Video-MME All |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OV-7B + ReKV | 0.5 fps | 5.9K | **68.5** | 60.7 | -- | -- | -- |
| LLaVA-OV-7B + MuKV | 0.5 fps | 5.9K | 67.8 | **63.3** | **57.9** | **52.1** | **61.2** |
| LLaVA-OV-0.5B + ReKV | 0.5 fps | 5.9K | 53.2 | 29.6 | 40.1 | 47.9 | 48.2 |
| LLaVA-OV-0.5B + MuKV | 0.5 fps | 5.9K | **55.2** | **30.5** | **41.4** | **48.5** | **49.1** |
| Qwen3-VL-4B | 768 frames | -- | 64.8 | 65.8 | 60.2 | 49.5 | 62.5 |
| Qwen3-VL-4B + MuKV | 0.5 fps | 5.9K | **66.0** | **67.0** | **61.8** | **51.0** | **63.6** |

### Ablations / Analysis

#### Multi-Granularity

| Patch | Frame | Segment | Inf. Tok. ↓ | Mem. Tok. ↓ | Acc@Ego ↑ | Acc@Movie ↑ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| ✓ |  |  | 8.3K | 47K | 51.6 | 44.1 |
|  | ✓ |  | 8.3K | 39K | 53.1 | 45.2 |
|  |  | ✓ | 8.3K | 10K | 54.9 | 44.8 |
| ✓ | ✓ |  | 8.3K | 53K | 55.1 | 43.6 |
| ✓ |  | ✓ | 8.3K | 53K | 55.2 | 45.1 |
|  | ✓ | ✓ | 8.3K | 53K | 55.4 | 43.7 |
| **✓** | **✓** | **✓** | 8.3K | 59K | **56.5** | **46.0** |

Segment-only 是最强单粒度；三粒度组合获得最佳结果，说明 global temporal context 与 local detail 互补。

#### Compression and Deployment

| Method / Compression | Inf. Tok. ↓ | Mem. Tok. ↓ | Acc@Ego ↑ | Acc@Movie ↑ |
| --- | ---: | ---: | ---: | ---: |
| MuKV, no compression | 12.5K | 177K | 53.7 | 44.3 |
| MuKV, attention only | 8.3K | 59K | 55.9 | 45.1 |
| MuKV, frequency only | 8.3K | 59K | 56.6 | 45.3 |
| **MuKV, DCP (67%)** | 8.3K | 59K | **57.3** | **45.6** |
| ReKV | 12.5K | 59K | 51.5 | 42.3 |
| ReKV, random drop 50% | 12.5K | 29K | 46.7 | 34.7 |
| ReKV, DCP (50%) | 6.3K | 29K | **56.1** | 44.9 |
| ReKV, DCP (90%) | 1.3K | 6K | 50.9 | **46.8** |

| Model | Compression Ratio | Time (s/Q) ↓ | KV-Cache (G/h) ↓ | Acc@Ego ↑ |
| --- | ---: | ---: | ---: | ---: |
| ReKV | 0 | 0.92 | 4.00 | 51.5 |
| MuKV | 0 | 0.72 | 3.72 | 53.7 |
| **MuKV** | **2/3** | **0.65** | **1.23** | **57.3** |
| MuKV | 1/2 | 0.67 | 1.85 | 53.7 |
| MuKV | 3/4 | 0.59 | 0.91 | 54.9 |

DCP 的收益不是来自任意 pruning：随机删除一半 ReKV tokens 会显著降准；保留高-frequency tokens 也优于保留 low-frequency tokens（Ego: 55.1 vs. 51.4；Movie: 43.9 vs. 41.4）。

#### Retrieval

| Retrieval | Acc@Ego ↑ | Acc@Movie ↑ |
| --- | ---: | ---: |
| Parallel | 56.5 | **46.0** |
| Hierarchical | 52.9 | 43.1 |
| Semi-Hierarchical | **57.9** | 45.2 |

Semi-hierarchical retrieval 在 Ego 上最佳，但 Movie 上略低于纯 parallel retrieval，说明 cross-grain coherence calibration 并非对所有视频分布都同样有效。

#### Sampling Rate Sensitivity

| Method | FPS | Mem. Tok. ↓ | RVS-Ego ↑ | StreamingBench All ↑ |
| --- | ---: | ---: | ---: | ---: |
| ReKV-7B | 0.5 | 59K | 56.2 | 62.3 |
| ReKV-7B | 2 | 236K | 54.8 | 62.9 |
| ReKV-7B | 3 | 354K | 53.9 | 62.5 |
| MuKV-7B | 0.5 | 59K | **59.5** | 64.4 |
| MuKV-7B | 2 | 118K | 57.7 | 68.2 |
| MuKV-7B | 3 | 354K | 56.1 | **71.4** |

更高 FPS 显著改善 StreamingBench，却降低 RVS-Ego；论文将其归因于 RVS-Ego 视觉变化较小，密集采样反而引入冗余。

### Training / Compute

| Item | Value |
| --- | --- |
| Training | Training-free |
| Backbone | LLaVA-OV 0.5B / 7B；Supplementary 还测试 Qwen2.5-VL 与 Qwen3-VL |
| Major experiment hardware | NVIDIA A5000, 24 GB |
| Default sampling | 0.5 FPS |
| Segment construction | 4 consecutive frames spanning 8 seconds |
| Original patches / super-patches | $P=196$, $S=4$ |
| Default total retrieved blocks | 64 |
| Patch / frame / segment $\alpha$ | $\{0.5, 0.7, 0.8\}$ |
| Patch / frame / segment retention $\rho$ | $\{0.1, 0.1, 0.8\}$ |
| Patch / frame / segment $k_g$ | $\{20, 32, 12\}$ |
| Patch / frame / segment $\lambda_g$ | $\{0.3, 0.3, 0\}$ |

## Limitations & Caveats

- 论文没有独立 Limitations section；以下除明确实验观察外，也包含基于方法设计的实现风险判断。
- **Counting weakness:** MuKV-7B 在 StreamingBench Counting 上低于 ReKV-7B（39.4 vs. 46.3），说明 compression 可能丢失对细粒度次数变化敏感的信息。
- **Dataset sensitivity:** 最佳 FPS、compression ratio 和 retrieval mixing weight 随数据分布变化明显；例如更高 FPS 提升 StreamingBench，却降低 RVS-Ego。
- **Evaluation drift:** RVS-Ego / RVS-Movie 使用 LLM judge，且默认 GPT-3.5-turbo-0613 已弃用；新旧 judge 结果不能直接混合比较。
- **Dataset count inconsistency:** 正文与 supplementary 对 RVS-Ego / RVS-Movie 的视频数量分别写成 11/20 与 10/22。
- **Parallel prefill assumption:** 每个时间步需对三种粒度执行三次 LLM prefill。论文称并行执行不增加 latency，但实际部署仍需要足够并行算力与显存带宽。
- **No released code URL reported:** TeX source 未提供官方代码链接，复现需自行实现 cache slicing、FFT scoring 和跨粒度 retrieval。

## Concrete Implementation Ideas

1. 在现有 Video-LLM streaming pipeline 中先只实现 DCP，并对 ReKV cache 做 attention-only、frequency-only、dual-signal 三组对照；这是验证收益最快、改动最局部的路径。
2. 将每个 KV block 存成 `{timestamp, granularity, pooled_last_key, per_layer_kv}`，使检索只读取轻量 pooled keys，命中后再加载完整 per-layer KV。
3. 为 Counting / fine-grained motion 类问题增加 query-aware retention：检测计数意图后降低 patch-level compression，或提高 patch retrieval quota。
4. 将固定 $\rho_g$ 与 $k_g$ 改为 memory-budget controller，根据视频变化率、问题类型和当前 cache size 动态分配三种粒度预算。
5. 对 semi-hierarchical reranking 加入可关闭的 dataset/query gate；当 segment-level coherence 不能提升 first-stage score separation 时退回 parallel retrieval。

## Open Questions / Follow-ups

- FFT frequency score 沿 token sequence 计算时，对 visual token 排列顺序和 patch grouping 有多敏感？
- 是否能用 temporal motion、novelty 或 scene-change signal 替代/补充 frequency，以改善 Counting 和快速局部变化？
- 三次并行 prefill 在不同 GPU、不同 backbone 和长时间运行下的真实吞吐、峰值显存与能耗如何？
- 固定的 patch/frame/segment 三层结构是否最优，还是可以用自适应 scene / event segmentation 生成更自然的高层粒度？
- Semi-hierarchical retrieval 在 Movie 上未胜过 parallel retrieval；如何判断何时应施加 cross-grain coherence？
- DCP 对 quantized KV cache、paged KV cache 和分布式 cache serving 是否仍保持收益？

## Citation

```bibtex
@article{xiao2026mukv,
  title   = {MuKV: Multi-Grained KV Cache Compression for Long Streaming Video Question-Answering},
  author  = {Xiao, Junbin and Chen, Jiajun and Sun, Tianxiang and Yang, Xun and Yao, Angela},
  journal = {arXiv preprint arXiv:2605.22269},
  year    = {2026},
  url     = {https://arxiv.org/abs/2605.22269}
}
```
