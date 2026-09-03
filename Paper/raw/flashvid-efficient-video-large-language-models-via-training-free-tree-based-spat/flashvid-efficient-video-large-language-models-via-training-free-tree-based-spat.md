---
title: (token)FlashVID
authors:
  - Ziyang Fan
  - Keyu Chen
  - Ruilong Xing
  - Yulin Li
  - Li Jiang
  - Zhuotao Tian
conference: ICLR 2026⭐️
year: 2026
arxiv_url: https://arxiv.org/abs/2602.08024
pdf_link: "[[assets/paper_2602.08024.pdf]]"
cover: "[[assets/pipeline_2602.08024.png]]"
updated: 2026-05-31
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/Fanziyang-v/FlashVID
---

## TL;DR

- FlashVID 是一个 training-free、plug-and-play 的 Video Large Language Models (VLLMs) 推理加速框架，目标是在极高压缩率下保留视频理解性能。
- 核心问题是现有视频 token 压缩方法常把 spatial redundancy 和 temporal redundancy 分开处理，忽略视频中物体位置、尺度、姿态随时间变化导致的 spatiotemporal 对应关系。
- 方法由两部分组成：ADTS 先选择有代表性且多样的 token，TSTM 再用 spatiotemporal redundancy trees 合并跨帧/帧内冗余 token。
- 在 LLaVA-OneVision、LLaVA-Video、Qwen2.5-VL 三个 VLLMs 和五个视频理解 benchmark 上，FlashVID 在相同 retention ratio 下通常优于 FastV、VisionZip、PruneVID、FastVID。
- 关键结果：LLaVA-OneVision 只保留 10% visual tokens 时，FlashVID 保留 99.1% 相对性能；在固定 token budget 下，Qwen2.5-VL 可处理 160 frames (10x)，平均分从 52.6 提升到 **57.1**，相对性能为 **108.6%**。

## Key Contributions

1. 论文指出视频中的 temporal redundancy 不应被绑定到固定 spatial location：相似语义区域会随运动发生位置、尺度、外观变化，因此固定位置的 temporal merging 容易合并低相关 token。
2. 提出 Tree-based Spatiotemporal Token Merging (TSTM)，用相邻帧 token 间的最大相似连接构建 redundancy trees，从而联合建模 spatial 与 temporal redundancy。
3. 提出 Attention and Diversity-based Token Selection (ADTS)，将 [CLS] attention、event relevance 和 Max-Min Diversity Problem (MMDP) 结合，用于先保留代表性/多样性 token，再把剩余 token 交给 TSTM 合并。
4. 在三类 VLLM 架构和五个 benchmark 上展示泛化性，并证明该方法能在固定算力预算下扩展输入帧数，改善 long-video understanding。

## Method

FlashVID 的输入是 video features $E_v \in \mathbb{R}^{F\times N_v\times d}$。整体流程可以理解为“先选代表性 token，再合并冗余 token”。

**TSTM: Tree-based Spatiotemporal Token Merging**

- 对相邻帧特征计算 token-level cosine similarity：

$$
S^{(f)} = \cos(E_v^{(f)}, E_v^{(f+1)}) \in \mathbb{R}^{N_v \times N_v}
$$

- 对第 $f$ 帧每个剩余 token $r_i^f$，在上一帧候选 token 中寻找最相似的 parent：

$$
p^* = \arg\max_{p \in \mathcal{R}^{(f-1)}} \mathrm{sim}(r_i^f, p)
$$

- 如果 $\mathrm{sim}(r_i^f,p^*) \geq T_\tau$，就连接到 parent，逐步形成 spatiotemporal redundancy trees。
- 每棵树 $\mathcal{T}^{(i)}$ 通过 aggregation 得到压缩 token：

$$
c^{(i)} = \textnormal{Agg}(\mathcal{T}^{(i)})
$$

**ADTS: Attention and Diversity-based Token Selection**

- 每帧计算 token pairwise cosine distance：

$$
D^{(f)} = 1 - \cos(E_v^{(f)}, E_v^{(f)})
$$

- 用 [CLS] attention $A_\textnormal{[CLS]}$ 强调视觉编码器认为重要的 token。
- 用 event relevance $\bar{\mathbf{S}}_e$ 衡量 token 与整体视频事件的相关性：

$$
\bar{\mathbf{S}}_e = \frac{1}{F}\sum_{i=1}^F (E_v \cdot f_v^\top)[:,:,i]
$$

- 最终通过 calibrated MMDP 选择 informative 且 diverse 的 token：

$$
\mathcal{I} = \textnormal{MMDP}(D,A_{\textbf{[CLS]}},\bar{\textbf{S}}_e)
$$

**Compact Pseudocode**

```text
Input: video features E_v, threshold T_tau
For each frame f:
  compute pairwise distance D^(f), [CLS] attention, event relevance
  I^(f) <- calibrated MMDP(D^(f), A_[CLS]^(f), S_e^(f))
  R^(f) <- remaining tokens after ADTS selection
For f = 2..F:
  for each token in R^(f):
    link it to the most similar token in R^(f-1) if similarity >= T_tau
Aggregate each spatiotemporal redundancy tree
Return aggregated tokens union selected ADTS tokens
```

实现细节上，FlashVID 还使用 video partition 和 Inner-LLM Pruning。作者设置 segment threshold $S_\tau=0.9$、minimum segments $M_s=8$、pruning layer $K=20$、expansion factor $f_e=1.25$。

## Pipeline Figure

![[assets/pipeline_2602.08024.png]]

Caption: Overview of our FlashVID. FlashVID compresses visual tokens by two synergistic modules: (1) ADTS prioritizes spatiotemporally informative tokens while ensuring feature diversity by solving a calibrated Max-Min Diversity Problem (MMDP); (2) TSTM models redundancy by spatiotemporal redundancy trees, which effectively capture fine-grained video dynamics.

Source: TeX includegraphics from sections/3_method.tex -> figures/method.pdf

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| VideoMME | Video understanding / multiple-choice QA | 900 videos; 2,700 QA pairs | Accuracy / score reported as Short, Medium, Long, Overall | 覆盖 6 个领域、30 个子类，视频长度 11 秒到 1 小时。 |
| EgoSchema | Egocentric long-form video QA | Subset / Total | Accuracy / score | 约 5,000 five-choice QA，来自 250 小时 egocentric video；强调长时序推理。 |
| LongVideoBench | Long-context interleaved video-language understanding | 3,763 videos; 6,678 QA | Accuracy / score | “referring-reasoning” 任务，视频 8 秒到 1 小时。 |
| MVBench | Temporal understanding | 20 tasks | Accuracy / score | 由 static-to-dynamic task 构造，强调 temporal reasoning。 |
| MLVU | Long-video understanding | 3,102 QA | Accuracy / score | 覆盖 9 类 long-video 任务，视频 3 分钟到 2 小时；主要用于固定 token budget 的 frame extension 实验。 |

### Experimental Setup

| Item | Value |
| ---- | ---- |
| Evaluated VLLMs | LLaVA-OneVision, LLaVA-Video, Qwen2.5-VL |
| LLaVA-OneVision frame/token setting | 32 frames, $32\times196$ visual tokens |
| LLaVA-Video frame/token setting | 64 frames, $64\times169$ visual tokens; paper uses frame token setting |
| Compared baselines | FastV, VisionZip, PruneVID, FastVID |
| Evaluation framework | LMMs-Eval |
| Main hardware | NVIDIA A800 80G GPUs |
| Efficiency hardware | Single NVIDIA A100 GPU for LLaVA-OneVision efficiency analysis |
| Fairness control | Average token budget per Transformer layer is aligned across methods |

### Main Results: LLaVA-OneVision

表格保留论文主表中的核心列：VideoMME Overall、EgoSchema Total、LongVideoBench、MVBench、Avg. Score、Rel. Acc.。粗体沿用论文原表强调。

| Method | Retention $R$ | VideoMME Overall | EgoSchema Total | LongVideoBench | MVBench | Avg. Score | Rel. Acc (%) |
| ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | 100% | 58.5 | 60.3 | 56.6 | 58.3 | 58.4 | 100.0 |
| FastV | 25% | 56.5 | 57.8 | 55.4 | 56.4 | 56.5 | 96.7 |
| VisionZip | 25% | 58.1 | 60.4 | 56.4 | 57.8 | 58.2 | 99.7 |
| PruneVID | 25% | 56.4 | 58.1 | 55.4 | 56.8 | 56.7 | 97.1 |
| FastVID | 25% | 57.9 | 59.5 | 55.9 | 58.1 | 57.8 | 99.0 |
| FlashVID | 25% | **59.2** | **60.4** | **56.8** | **58.0** | **58.6** | **100.3** |
| FastV | 20% | 55.7 | 57.6 | 56.0 | 56.0 | 56.3 | 96.4 |
| VisionZip | 20% | 58.0 | 60.0 | 55.4 | 57.6 | 57.7 | 98.8 |
| PruneVID | 20% | 56.4 | **60.2** | 55.2 | 56.2 | 57.0 | 97.6 |
| FastVID | 20% | 57.9 | 59.5 | 55.9 | 58.1 | 57.9 | 99.1 |
| FlashVID | 20% | **58.2** | 60.1 | **58.5** | **58.2** | **58.7** | **100.5** |
| FastV | 15% | 54.6 | 56.6 | 54.8 | 55.0 | 55.2 | 94.5 |
| VisionZip | 15% | 55.6 | 60.0 | 54.1 | 53.5 | 55.8 | 95.5 |
| FastVID | 15% | 57.7 | 58.9 | 56.7 | **58.2** | 57.9 | 99.1 |
| PruneVID | 15% | 56.1 | 57.7 | 54.5 | 55.1 | 55.7 | 95.4 |
| FlashVID | 15% | **58.2** | **60.4** | **57.5** | 57.9 | **58.5** | **100.2** |
| FastV | 10% | 52.7 | 56.0 | 52.4 | 53.4 | 53.6 | 91.8 |
| VisionZip | 10% | 53.3 | 58.5 | 49.4 | 54.8 | 54.0 | 92.5 |
| PruneVID | 10% | 54.7 | 57.2 | 54.0 | 53.7 | 54.9 | 94.0 |
| FastVID | 10% | 57.2 | 58.7 | 55.7 | 57.0 | 57.1 | 97.8 |
| FlashVID | 10% | **57.8** | **60.0** | **56.5** | **57.4** | **57.9** | **99.1** |

### Main Results: LLaVA-Video

| Method | Retention $R$ | VideoMME Overall | EgoSchema Total | LongVideoBench | MVBench | Avg. Score | Rel. Acc (%) |
| ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | 100% | 64.2 | 57.3 | 59.5 | 61.9 | 60.7 | 100.0 |
| FastV | 20% | 59.2 | 54.1 | 56.0 | 58.4 | 56.9 | 93.7 |
| VisionZip | 20% | 61.7 | 56.4 | 58.0 | 59.8 | 59.0 | 97.2 |
| FastVID | 20% | **62.6** | 55.0 | 57.1 | **60.2** | 58.7 | 96.7 |
| FlashVID | 20% | 62.2 | **56.4** | **58.7** | 59.8 | **59.3** | **97.7** |
| FastV | 10% | 55.8 | 51.1 | 53.6 | 56.2 | 54.2 | 89.3 |
| VisionZip | 10% | 59.5 | 53.9 | 54.5 | 58.5 | 56.6 | 93.2 |
| FastVID | 10% | 59.8 | 52.4 | 56.9 | 59.3 | 57.1 | 94.1 |
| FlashVID | 10% | **60.9** | **54.9** | **57.7** | **59.3** | **58.2** | **95.9** |

### Main Results: Qwen2.5-VL

| Method | Retention $R$ | VideoMME Overall | EgoSchema Total | LongVideoBench | MVBench | Avg. Score | Rel. Acc (%) |
| ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | 100% | 61.3 | 58.3 | 58.9 | 68.0 | 61.6 | 100.0 |
| FastV | 20% | 59.2 | **57.1** | 54.2 | **66.8** | 59.3 | 96.3 |
| VisionZip | 20% | 59.0 | 56.6 | 56.3 | 66.4 | 59.6 | 96.8 |
| FastVID | 20% | 58.6 | 56.4 | 57.8 | 64.7 | 59.4 | 96.4 |
| FlashVID | 20% | **59.6** | 56.8 | **58.1** | 66.5 | **60.2** | **97.7** |
| FastV | 10% | 55.9 | 54.9 | 51.1 | 63.6 | 57.3 | 91.6 |
| VisionZip | 10% | 56.4 | 55.5 | 54.5 | 64.3 | 57.7 | 93.7 |
| FastVID | 10% | 56.3 | 55.6 | 55.4 | 62.3 | 57.4 | 93.2 |
| FlashVID | 10% | **57.3** | **55.9** | **57.1** | **65.5** | **58.9** | **95.6** |

### Fixed Token Budget: Qwen2.5-VL Frame Extension

这个表是论文最有用的实用结论之一：不是只看压缩后少算多少，而是在同一计算/显存预算内换取更多输入帧。

| Method | #Frames | Retention $R$ | VideoMME Overall | EgoSchema Total | LongVideoBench | MLVU | Avg. Score | Rel. Acc (%) |
| ---- | ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: |
| Vanilla | 16 (1x) | 100% | 57.0 | 55.6 | 56.9 | 40.6 | 52.6 | 100.0 |
| VisionZip | 80 (5x) | 20% | 62.1 | 58.2 | 57.4 | 43.1 | 55.2 | 104.9 |
| FastVID | 80 (5x) | 20% | 61.5 | 58.4 | 58.0 | 44.4 | 55.6 | 105.7 |
| FlashVID | 80 (5x) | 20% | **62.4** | **58.6** | **58.9** | **45.0** | **56.2** | **106.8** |
| VisionZip | 160 (10x) | 10% | 61.6 | **59.6** | 56.8 | 45.1 | 55.8 | 106.1 |
| FastVID | 160 (10x) | 10% | 61.9 | 59.1 | 58.0 | 43.8 | 55.7 | 105.9 |
| FlashVID | 160 (10x) | 10% | **62.4** | 59.5 | **58.9** | **47.5** | **57.1** | **108.6** |

### Ablations / Analysis

**ADTS module**

| Method | VideoMME | EgoSchema | LongVideoBench | MVBench | Rel. Acc |
| ---- | ----: | ----: | ----: | ----: | ----: |
| ATS | 55.5 | 59.5 | 55.0 | 56.2 | 96.9 |
| DTS | 55.7 | **60.3** | 55.3 | 55.5 | 97.1 |
| w/ E.R. | 56.0 | 60.2 | 55.1 | 56.8 | 97.6 |
| w/ C.A. | 57.3 | 59.7 | 55.7 | 57.3 | 98.5 |
| ADTS | **57.8** | 60.0 | **56.5** | **57.4** | **99.1** |

**ADTS/TSTM ratio $\alpha$**

| $\alpha$ | VideoMME | EgoSchema | LongVideoBench | MVBench | Rel. Acc |
| ---- | ----: | ----: | ----: | ----: | ----: |
| 0.0/TSTM | 56.7 | 60.2 | 55.3 | 55.6 | 97.4 |
| 0.2 | 56.2 | 59.8 | 55.3 | 56.5 | 97.4 |
| 0.4 | 56.4 | 60.0 | 55.1 | 57.2 | 97.9 |
| 0.6 | 57.0 | **60.4** | 55.8 | 57.0 | 98.5 |
| 0.7 | **57.8** | 60.0 | **56.5** | 57.4 | **99.1** |
| 0.8 | 57.2 | 60.1 | 56.3 | 57.1 | 98.8 |
| 1.0/ADTS | 56.9 | 60.1 | 55.6 | **57.6** | 98.5 |

**Efficiency on LLaVA-OneVision**

| Method | Retention $R$ | TFLOPs | Vision Encoding | Compression | LLM Forward | Prefilling Total | TTFT | Avg. Score | Rel. Acc (%) |
| ---- | ---- | ----: | ----: | ----: | ----: | ---- | ---- | ----: | ----: |
| Vanilla | 100% | 113.4 | 785.0 ms | - | 1220.8 ms | 1220.8 ms (1.0x) | 2005.8 ms (1.0x) | 58.9 | 100.0 |
| FastVID | 25% | 22.4 | 785.0 ms | 28.6 ms | 273.2 ms | 301.8 ms (4.0x) | 1086.8 ms (1.8x) | 58.0 | 98.5 |
| FlashVID | 10% | 8.6 | 785.0 ms | 60.2 ms | 133.1 ms | 193.3 ms (**6.3x**) | 978.3 ms (**2.1x**) | 58.4 | **99.1** |

## Limitations & Caveats

- 作者没有单独的 Limitations section；以下是从实验设置和方法机制中可见的 caveats。
- 方法依赖 vision encoder features、attention 信息和相似度阈值；在视频内容高度噪声化或跨帧外观剧烈变化时，TSTM 的 parent linking 仍可能合并不理想的 token。
- 论文主要比较 training-free acceleration baselines；与需要训练的压缩模型之间没有做同等训练预算/部署预算下的系统比较。
- 主实验集中在 multiple-choice video QA benchmarks；对开放式生成、细粒度定位、实时流式视频等场景的效果仍需额外验证。
- FlashVID 自身的 compression step 有额外耗时，例如 LLaVA-OneVision 上为 60.2 ms；虽然总 prefilling 和 TTFT 仍明显加速，但极低延迟场景需要看实现优化。
- 深度/广度约束没有带来收益，作者推测 $T_\tau$ 已提供类似效果；这也意味着 TSTM 的结构质量主要由相似度阈值和特征空间质量决定。

## Concrete Implementation Ideas

1. 在现有 VLLM inference pipeline 中优先做 before-LLM token compression，把 FlashVID 接在 vision encoder / projector 之后、LLM prefilling 之前，再按模型结构选择是否加入 Inner-LLM Pruning。
2. 对 long-video QA 应用，不要只追求固定帧数下的低 latency；可以像论文一样把压缩节省的 budget 换成更多 frames，特别适合 event retrieval 和 temporal reasoning。
3. 实现 TSTM 时保留 segment-level video partition，避免不同 scene 的 token 被错误合并；可先复用 DySeg 风格的 transition similarity。
4. 对不同 VLLM 先复现实验中的默认超参：$S_\tau=0.9$、$M_s=8$、$K=20$、$f_e=1.25$、$T_\tau=0.8$，再只对 token budget 和 retention ratio 做小范围 sweep。
5. 如果部署端最关心 TTFT，把 compression kernel 和 cosine similarity / top-parent search 做批处理或近似检索优化，因为论文表明 compression 自身也会成为非零开销。

## Open Questions / Follow-ups

- FlashVID 对开放式 video captioning、dense temporal grounding、multi-turn video dialogue 的影响如何？论文主表主要是 QA score。
- ADTS 的 [CLS] attention calibration 对没有显式 [CLS] token 的视觉编码器需要近似；不同 encoder 的 attention 质量会不会显著影响选择质量？
- TSTM 的 tree aggregation 使用 mean pooling 等简单聚合；是否可以用 lightweight learned aggregation，在少量训练成本下进一步提高极低 retention ratio 的性能？
- 在 streaming video 或 online setting 中，TSTM 是否可以增量维护 redundancy trees，而不是对完整视频一次性计算？
- Fixed token budget 下，帧数继续超过 160 frames 时是否仍有收益，还是会被 sampling density、query relevance 或 attention context 稀释限制？

## Citation

```bibtex
@misc{fan2026flashvidefficientvideolarge,
      title={FlashVID: Efficient Video Large Language Models via Training-free Tree-based Spatiotemporal Token Merging}, 
      author={Ziyang Fan and Keyu Chen and Ruilong Xing and Yulin Li and Li Jiang and Zhuotao Tian},
      year={2026},
      eprint={2602.08024},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2602.08024}, 
}
```
