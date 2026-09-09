---
title: "STORM: Token-Efficient Long Video Understanding for Multimodal LLMs"
authors:
  - Jindong Jiang
  - Xiuyu Li
  - Zhijian Liu
  - Muyang Li
  - Guo Chen
  - Zhiqi Li
  - De-An Huang
  - Guilin Liu
  - Zhiding Yu
  - Kurt Keutzer
  - Sungjin Ahn
  - Jan Kautz
  - Hongxu Yin
  - Yao Lu
  - Song Han
  - Wonmin Byeon
conference: ICCV 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2503.04130
pdf_link: "[[assets/paper_2503.04130.pdf]]"
cover: "[[_assets/images/pipeline_2503.04130.png]]"
updated: 2026-05-26
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - token-pruning
  - video-llm
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- STORM（**S**patiotemporal **TO**ken **R**eduction for **M**ultimodal LLMs）针对 long-video Video-LLM 中“逐帧编码、由 LLM 承担全部时序推理”带来的长上下文成本与信息利用不足问题。
- 核心改动是在 image encoder 与 LLM 之间加入 **Mamba-based temporal projector**，让视觉 token 在进入压缩模块前已经聚合跨帧时序信息。
- 模型支持训练期的 temporal/spatial average pooling，以及测试期的 temporal token sampling；作者报告视觉 token 成本最多降低至原来的 $1/8$，固定帧数条件下 decoding latency 降低 $2.4$--$2.9\times$。
- 在作者控制的 8K token budget 设置下，`STORM + T. Pooling` 以 25% visual tokens 达到 MVBench 71.3、MLVU 72.5、LongVideoBench 59.5、VideoMME 63.4；再叠加 test-time sampling 后，MLVU/LongVideoBench 升至 72.9/60.5。
- 最重要的经验结论不是“更激进地删 token”，而是先通过 temporal modeling 生成可压缩的 token：128-frame temporal pooling 的 STORM 平均分为 66.7，而无 Mamba 的 VILA 为 64.3。

## Key Contributions

1. 提出位于视觉编码器与 LLM 之间的 Mamba temporal projector，通过双向时空扫描将跨帧历史编码进视觉 token，而不是让 LLM 从独立帧 token 中自行恢复动态关系。
2. 在 enriched tokens 上统一支持三类压缩：training-time temporal pooling、training-time spatial pooling 与 training-free temporal sampling，使更长视频可以保持在受控 LLM token budget 内。
3. 在 MVBench、MLVU、LongVideoBench 与 VideoMME 上展示精度/效率收益，并给出 token budget、latency、输入帧数、数据组成与 streaming variant 的分析。

## Method

**Pipeline.** STORM 基于 VILA-style video VLM：每帧先经过 vision encoder；projector 不再只是 MLP，而是 linear downsampling 加 Mamba temporal module；压缩后的 visual tokens 与文本 token 一并送入 LLM。

给定第 $t$ 帧的视觉 token $\mathbf{X}_t \in \mathbb{R}^{\hat{N}\times D}$，先用 linear layer 将空间 token 数降为 $N=\hat{N}/r$：

$$
\tilde{\mathbf{X}}_t=\mathrm{Linear}(\mathbf{X}_t), \qquad
\tilde{\mathbf{X}}\in\mathbb{R}^{T\times N\times D}.
$$

经过 $L$ 层 MambaMixer 的 residual 更新：

$$
\mathbf{X}^{(l)}
=\mathbf{X}^{(l-1)}
+\mathrm{MambaMixer}\left(\mathrm{Norm}\left(\mathbf{X}^{(l-1)}\right)\right).
$$

论文采用 frame 内及 frame 间的双向扫描，使 $\mathbf{X}^{(L)}$ 中的 token 已包含 temporal history，然后再压缩：

- **Temporal Pooling:** 每 $k$ 帧平均，输出维度为 $\mathbb{R}^{\frac{T}{k}\times N\times D}$；主结果采用 $4\times$ 压缩。
- **Spatial Pooling:** 每帧在空间 token 维度平均池化，输出为 $\mathbb{R}^{T\times \frac{N}{p}\times D}$。
- **Temporal Sampling:** 在 temporal projector 或 pooling 之后，测试时沿时间维均匀采样；主结果中的 `*` 表示额外 $2\times$ 压缩。

**Training flow.**

1. Alignment stage：冻结 image encoder 与 LLM，仅训练 temporal projector。
2. SFT stage：联合 fine-tune 三个组件；正文报告约 12.5M 的 text/image/video mixture，并以 32-frame 输入训练。
3. Long-video fine-tuning：带 training-time compression 的模型以 128-frame 输入在 LLaVA-Video 数据上继续适配，使 $4\times$ pooling 后的 LLM token 数仍接近 32-frame 设置。

## Pipeline Figure

![[_assets/images/pipeline_2503.04130.png]]

Caption: 作者的主方法图展示了 STORM pipeline：Mamba-based temporal projector 位于 image encoder 与 LLM 之间，产生携带时序历史的 Summary Tokens，以支持后续 token reduction。

Source: TeX `sec/3_method.tex` 中的 `\includegraphics{figures/figure1.pdf}`；源 PDF 使用可见 `CropBox` 以 250 DPI 转换为 PNG。

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Video duration reported in table |
| --- | --- | --- | --- | --- |
| MVBench | Video understanding / QA | test | Score / accuracy (%) | 16 sec |
| MLVU | Long-video understanding | dev | Score / accuracy (%) | 3--120 min |
| LongVideoBench | Long-video QA | val | Score / accuracy (%) | 8 sec--60 min |
| VideoMME | Video understanding | w/o subtitles | Score / accuracy (%) | 1--60 min |

### Training / Compute

| Item | Value |
| --- | --- |
| Main architecture | VILA codebase; PaliGemma vision encoder; Qwen2-VL LLM; randomly initialized temporal projector |
| Image resolution | $448 \times 448$ |
| SFT mixture | Approximately 12.5M samples; text-only, image-text and video-text data |
| Standard SFT video input | 32 frames |
| Training-time compression | $4\times$: temporal pooling maps 32 frames to 8 temporal groups; spatial pooling maps 256 tokens/frame to 64 |
| Long-video fine-tuning | 128-frame input; LLaVA-Video data reported as approximately 1.35M video-text pairs |
| Uncompressed training overhead | VILA 19.1 h vs STORM 20.1 h; approximately 5% overhead reported |
| Profiling hardware in appendix | Single NVIDIA DGX A100-80G |
| 256-frame profiling latency | No compression: 10.34 s; $4\times$ compression: 3.68 s; $8\times$ compression: 3.00 s |

注意：alignment data 的描述在论文内部不一致。实验正文称使用 `SVIT` 的 95K image-text pairs，附录则称所有模型使用 `LLaVA-CC3M-Pretrain-595K`；复现前应以公开配置或作者澄清为准。

### Main Results

下表摘取作者 “Comparison with Existing Video-LLMs” 表中的代表性行。加粗沿用原表标记；`*` 表示该分数采用额外 $2\times$ test-time temporal sampling。

| Method | Size | Comp. ratio (%) | Test frames | MVBench test | MLVU dev | LongVideoBench val | VideoMME w/o sub. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT4-O | - | - | 1 fps | 64.6 | 66.2 | - | 77.2 |
| LLaVA-OneVision | 7B | - | 32 | 56.7 | 64.7 | 56.5 | 58.2 |
| Oryx-1.5 | 7B | - | 64 | 67.6 | 67.5 | 56.3 | 58.8 |
| LongVU | 7B | - | 1 fps | 66.9 | 65.4 | - | 60.6 |
| Qwen2-VL | 7B | - | 2 fps | 67.0 | - | 55.6 | 63.3 |
| **STORM + T. Pooling (+ T. Sampling where marked)** | 7B | **25 / 12.5*** | 256 | **71.3** | **72.9*** | **60.5*** | **63.4** |

更可比的是所有 VILA-based 模型使用相同数据、training pipeline 与 8K training token budget 的控制实验；表内加粗同样保留作者原标记，latency 基于 256 frames。

| Model / Setting | Comp. ratio (%) | Latency (s) | Train frames | Test frames | MVBench | MLVU | LongVideoBench | VideoMME |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VILA Baseline | 100 | 4.31 | 32 | 256 | 69.5 | 70.2 | 55.9 | 60.1 |
| STORM | 100 | 4.47 | 32 | 256 | 70.3 | 71.1 | 54.5 | 62.4 |
| STORM + T. Pooling | 25 | 1.82 | 128 | 256 | **71.3** | 72.5 | 59.5 | **63.4** |
| STORM + T. Sampling* | 50 | 2.50 | 32 | 256 | 70.1 | 70.8 | 54.8 | 63.1 |
| STORM + T. Pooling + T. Sampling* | 12.5 | 1.51 | 128 | 256 | 70.6 | **72.9** | **60.5** | 62.4 |

在这一控制设置下，temporal pooling 更适合需要保留局部细节的 MVBench/VideoMME；额外 sampling 对偏全局长视频理解的 MLVU/LongVideoBench 更有利。

### Ablations / Analysis

**Temporal modeling and longer input.** 数值为四项 benchmark 的平均分；加粗来自论文原表。

| Model | 8F | 32F (T. Pooling) | 128F (T. Pooling) |
| --- | ---: | ---: | ---: |
| VILA (w/o Mamba) | **62.0** | 63.5 (+1.5) | 64.3 (+0.8) |
| STORM (w/ Mamba) | 61.6 | **64.2** (+2.6) | **66.7** (+2.5) |

**Spatial vs temporal pooling when extending frames.** 两种 pooling 都将 visual tokens 压缩到原始数量的 25%；加粗来自论文原表。

| Variant | LongVideoBench 32F | LongVideoBench 128F | VideoMME 32F | VideoMME 128F |
| --- | ---: | ---: | ---: | ---: |
| S. Pooling | **56.0** | 55.9 (-0.1) | 61.1 | 58.3 (-2.8) |
| T. Pooling | 54.2 | **59.5** (+5.3) | **61.2** | **63.4** (+2.2) |

**Architecture transfer on VideoMME (w/o subtitles).** 下表保留论文中 `Ours` latency/score 的加粗。

| Architecture | Resolution | VILA latency (ms) | STORM latency (ms) | VILA | STORM |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen2 7B + PaliGemma | $448\times448$ | 1980 | **926** | 59.7 | **61.2** |
| Llama3 8B + SigLip | $384\times384$ | 1560 | **724** | 54.6 | **56.8** |
| Qwen2 1.5B + SigLip | $384\times384$ | 724 | **486** | 49.6 | **52.6** |

## Limitations & Caveats

- 论文没有单独的 limitations section；以下风险来自文中实验设计与作者讨论。
- Alignment stage 的数据源/规模在正文与附录中矛盾（`SVIT` 95K 对比 `LLaVA-CC3M-Pretrain-595K`），会直接影响可复现性。
- 与外部 Video-LLMs 的比较使用不同训练数据、输入帧策略与部分缺失指标；SOTA 结论应主要视为报告性能对照，而非完全受控比较。
- 压缩策略存在任务依赖的 trade-off：sampling 对 MLVU/LongVideoBench 更有帮助，但在 MVBench/VideoMME 上 pooling-only 配置更强，表明细粒度视觉线索可能受更强时间采样影响。
- 作者将超长 token sequence 下的性能回落部分归因于预训练 LLM 的 effective context length，这在正文中明确为推测，尚非被单独验证的因果结论。
- Streaming/online 仅以 uni-directional STORM 在 VideoMME 上作初步验证；主方法及最强长视频结果仍以 bidirectional temporal modeling 为中心。

## Concrete Implementation Ideas

1. 在现有 VILA-style 模型中，将视觉 projector 改为 `Linear -> Mamba temporal module -> token compression -> LLM`，保持输入张量接口为 $T\times N\times D$，以便独立替换 compression 策略。
2. 先实现 `temporal_avg_pool(k=4)` 与测试期 `temporal_sample(s=2)` 两个最小组件，复现 25% 与 12.5% token ratio 的受控 8K-budget 实验，再考虑 spatial pooling。
3. 训练时分离 alignment、32-frame SFT 与 128-frame long-video fine-tuning 三阶段，并在开跑前确认 alignment dataset 的论文歧义，记录实际数据清单和样本数。
4. 用单卡 profiling 固定 frame count 与 token ratio，分别记录 vision tower、temporal projector 和 LLM latency，以判断收益是否确实来自压缩 LLM 输入而非其他实现差异。

## Open Questions / Follow-ups

- Alignment stage 实际采用 `SVIT` 95K 还是 `LLaVA-CC3M-Pretrain-595K`，作者发布配置能否消除这一矛盾？
- Temporal sampling 的最优比例是否可根据 query 类型或视频动态程度自适应选择，而非固定均匀抽样？
- 在严格 causal streaming 条件、长时运行 state retention 和实时吞吐评测下，uni-directional STORM 能否保持离线结果中的收益？
- 对需要 OCR 或瞬时细节定位的任务，是否可以用 learned token retention 或 question-aware gating 补偿 temporal sampling 的损失？

## Citation

Jindong Jiang, Xiuyu Li, Zhijian Liu, Muyang Li, Guo Chen, Zhiqi Li, De-An Huang, Guilin Liu, Zhiding Yu, Kurt Keutzer, Sungjin Ahn, Jan Kautz, Hongxu Yin, Yao Lu, Song Han, and Wonmin Byeon. *STORM: Token-Efficient Long Video Understanding for Multimodal LLMs*. arXiv:2503.04130 [cs.CV], 2025. Consulted revision: v4, 22 September 2025. https://arxiv.org/abs/2503.04130
