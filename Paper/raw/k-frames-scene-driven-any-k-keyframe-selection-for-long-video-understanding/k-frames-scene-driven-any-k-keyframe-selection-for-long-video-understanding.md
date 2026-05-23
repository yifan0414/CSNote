---
title: "K-frames: Scene-Driven Any-k Keyframe Selection for long video understanding"
authors:
  - Yifeng Yao
  - Yike Yun
  - Jing Wang
  - Huishuai Zhang
  - Dongyan Zhao
  - Ke Tian
  - Zhihao Wang
  - Minghui Qiu
  - Tao Wang
conference: ICLR 2026×
year: 2025
arxiv_url: https://arxiv.org/abs/2510.13891
pdf_link: "[[assets/paper_2510.13891.pdf]]"
cover: "[[assets/pipeline_2510.13891.png]]"
updated: 2026-05-20
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
  - benchmark
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

# TL;DR

- K-frames 把 long-video keyframe selection 从“挑离散帧”改写为“先预测 query-relevant key clips，再从 clip 中抽帧”的 clip2frame 范式，核心目标是保留 scene continuity。
- 作者构建 PeakClips：约 6.7K videos、108K scenes、281K scene-query relevance scores，通过 scene segmentation、hierarchical captioning、Gemini 2.5 Pro relevance scoring 与 SIGLIP 相似度细化得到 P1/P2 clips。
- 训练采用三阶段 curriculum：SFT1 学 temporal grounding / scene understanding，SFT2 学 query-conditioned key-clip prediction，RL 阶段用 GRPO 直接对 downstream VideoQA answer reward 优化选择策略。
- 在 MLVU、VideoMME、LVBench 上，K-frames 作为 plug-and-play 前端通常能提升 Qwen2.5-VL、Gemini2.5Pro、GPT-4o、InternVL3.5 等下游 MLLM，尤其在 Needle-QA 这类 temporal localization 任务上增益很大。
- 方法对 holistic/global understanding 任务收益较有限；把 selector 生成的 reason text 直接喂给下游模型反而可能干扰推理。

# Key Contributions

1. 提出 K-frames：query-conditioned、scene-driven、interpretable 的 keyframe selection 方法，输出连续 key clips 而不是孤立 frames，并支持 any-k sampling。
2. 构建 PeakClips：用于 scene-level relevance supervision 的大规模 long-video highlight dataset，包含 scene/chapter/video 层级 caption 与 query-conditioned relevance labels。
3. 设计三阶段 SFT-RL 训练流程：先打 temporal grounding 基础，再学习 key-clip perception，最后通过 downstream QA reward 对选择策略进行 RL alignment。
4. 在多个 long-video understanding benchmark 和不同开源/闭源 downstream MLLM 上验证了 model-agnostic 的性能提升。

# Method

K-frames 的基本思路是把长视频输入 $V = \{f_t\}_{t=1}^T$ 和 query $Q$ 交给一个轻量 MLLM selector，让它预测一组有时间边界、优先级和 rationale 的 clips $\mathcal{C}=\{c_i\}_{i=1}^N$。之后只在这些 key clips 内或以 key clips 为高密度区域抽取最终 $k$ 个 frames，再交给冻结的 downstream MLLM 回答问题。

PeakClips 的构建流程分三步：第一，用相邻帧 histogram difference 做 scene-aware segmentation，得到连续 scene clips；第二，用 Gemini 2.5 Pro 生成 clip-level、chapter-level、video-level 的 hierarchical captions；第三，用 Gemini 2.5 Pro 对每个 scene 与 query 的相关性打 1-5 分，并结合 SIGLIP frame-query similarity 细化 relevance score。最终分数 $\ge 4.9$ 的 clips 标为 P1，$[4.3,4.9)$ 标为 P2。

训练流程也分三段：SFT1 包含 caption-to-scene localization、scene-to-caption generation、clip-query relevance scoring，主要学习 temporal localization 与 scene understanding；SFT2 直接学习 query-conditioned key-clip prediction；RL 阶段以 SFT 模型为 cold-start policy，使用 GRPO 和冻结 Qwen2.5-VL-7B 的 answer quality reward 做 downstream alignment。

SFT 使用标准 autoregressive objective：

$$
\mathcal{L}_{\text{SFT}} = -\log P(\mathcal{Y}_{\text{gt}} \mid V, Q, I; \theta)
$$

RL reward 对 multiple-choice QA 的正确选项概率和错误选项平均概率做 log-ratio，并用 $\tanh$ 平滑：

$$
\mathrm{Reward} = \tanh\!\left( \frac{1}{\tau}
\log \frac{p(\text{ans})}{\tfrac{1}{|Y|-1}\sum_{\hat{y} \neq \text{ans}} p(\hat{y})} \right)
$$

紧凑推理流程：

```text
Input: long video V, query Q, frame budget k
1. Uniformly sample T=256 candidate frames for the K-frames selector.
2. K-frames predicts query-relevant clips with P1/P2 priority and rationales.
3. If k=8, use Focused Sampling: sample only inside predicted key clips.
4. If k=32/64, use Hybrid Sampling: sample densely inside key clips and sparsely elsewhere.
5. Send the selected k frames plus Q to the downstream MLLM for final answering.
```

# Pipeline Figure

![[assets/pipeline_2510.13891.png]]

Caption: An overview of the K-frames framework. It features a two-stage Supervised Fine-Tuning (SFT) curriculum for temporal grounding and key-clip perception, followed by a Reinforcement Learning (RL) stage to align the selection policy with downstream task performance.

Source: TeX `\includegraphics` from `main.tex` using `figures/main_figure.pdf`; converted to PNG with PDF crop bounds at 250 dpi.

# Experiments

## Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| PeakClips | Training / relevance annotation | 6,702 videos; 108,221 scenes; 281,643 scene-query relevance scores | Relevance score 1-5; P1/P2 clips | 来源类别包括 NextQA、Academic、YouTube、PerceptionTest；用于 SFT supervision。 |
| Video-MME | Multiple-choice VideoQA | 900 videos; 2,700 QA; short / medium / long duration subsets | Accuracy | 用于评估 long-video understanding，不参与 PeakClips 标注。 |
| MLVU | Long-video VQA, including Needle-QA | 2,174 multiple-choice VQA pairs; 9 tasks | Accuracy; M-Avg; Needle-QA | Needle-QA 强调 temporal localization。 |
| LVBench | Long-video multiple-choice VQA | 1,549 QA; 6 tasks; average video duration 4,101 seconds | Accuracy | 视频最长，考察长上下文视频理解。 |

## PeakClips Statistics

| Annotation Type | Count | Average per Video |
| --- | ---: | ---: |
| Video-level Summarization | 6,702 | 1 |
| Chapter-level Description | 19,070 | 2.85 |
| Scene-level Description | 108,221 | 16.15 |
| Relevance Query | 16,883 | 2.52 |
| Scene-level Relevance Scores | 281,643 | 42.02 |
| Total Annotations | 281,643 |  |

## Main Results

下表保留主表中的关键汇总指标：MLVU Needle-QA、MLVU M-Avg、VideoMME Avg、LVBench。括号中是论文表格报告的相对 uniform sampling baseline 的提升。

| Downstream MLLM | Frames | Selector | MLVU Needle-QA | MLVU M-Avg | VideoMME Avg | LVBench |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Qwen2.5-VL 7B | 8 | Uniform | 58.6 | 53.9 | 53.0 | 52.8 |
| Qwen2.5-VL 7B | 8 | **K-frames** | 77.5 (+18.9) | 60.4 (+6.5) | 57.4 (+4.4) | 57.7 (+4.9) |
| Qwen2.5-VL 7B | 32 | Uniform | 63.4 | 61.7 | 60.2 | 59.3 |
| Qwen2.5-VL 7B | 32 | **K-frames** | 79.4 (+16.0) | 65.9 (+4.2) | 62.1 (+1.9) | 60.5 (+1.2) |
| Qwen2.5-VL 7B | 64 | Uniform | 67.7 | 65.6 | 62.8 | 59.9 |
| Qwen2.5-VL 7B | 64 | **K-frames** | 78.9 (+11.2) | 67.8 (+2.2) | 64.5 (+1.7) | 61.6 (+1.7) |
| Qwen2.5-VL 72B | 8 | Uniform | 51.6 | 56.3 | 57.7 | 55.6 |
| Qwen2.5-VL 72B | 8 | **K-frames** | 77.2 (+25.6) | 63.3 (+7.0) | 60.6 (+2.9) | 59.3 (+3.7) |
| Qwen2.5-VL 72B | 32 | Uniform | 67.3 | 64.0 | 65.3 | 60.8 |
| Qwen2.5-VL 72B | 32 | **K-frames** | 78.3 (+11.0) | 67.6 (+3.6) | 66.3 (+1.0) | 63.2 (+2.4) |
| Gemini2.5Pro | 8 | Uniform | 43.4 | 54.2 | 69.1 | 57.8 |
| Gemini2.5Pro | 8 | **K-frames** | 71.6 (+28.2) | 56.6 (+2.4) | 70.0 (+0.9) | 62.2 (+4.4) |
| Gemini2.5Pro | 32 | Uniform | 74.6 | 66.0 | 77.2 | 64.2 |
| Gemini2.5Pro | 32 | **K-frames** | 80.9 (+6.3) | 69.0 (+3.0) | 78.0 (+0.8) | 67.0 (+2.8) |
| GPT-4o | 8 | Uniform | 58.3 | 55.38 | 59.7 | 49.4 |
| GPT-4o | 8 | **K-frames** | 75.2 (+16.9) | 60.5 (+5.1) | 62.6 (+2.9) | 54.5 (+5.1) |
| GPT-4o | 32 | Uniform | 71.3 | 59.6 | 62.1 | 49.9 |
| GPT-4o | 32 | **K-frames** | 76.9 (+5.6) | 61.9 (+2.3) | 62.7 (+0.6) | 51.3 (+1.4) |

同 backbone 对比 ViaRL 时，K-frames 在 8-frame 设置下超过 ViaRL：Needle-QA 为 77.5 vs. 73.5，MLVU M-Avg 为 60.4 vs. 58.2。论文强调 ViaRL 需要优化下游 QwenVL2.5-7B，而 K-frames 是 plug-and-play selector。

## Ablations / Analysis

Training stages ablation 使用 Qwen2.5-VL-7B downstream MLLM，$k=32$ frames。

| Model / Stage | SFT1 | SFT2 | RL | Needle-QA | MLVU |
| --- | --- | --- | --- | ---: | ---: |
| Uniform baseline | - | - | - | 63.4 | 61.7 |
| SFT | - | ✓ | - | 75.8 | 64.1 |
| SFT | ✓ | ✓ | - | 76.3 | 64.5 |
| RL / full K-frames | ✓ | ✓ | ✓ | **79.4** | **65.9** |

Temporal prompts ablation 在 SFT2 model 上做，baseline 为 uniform sampling。

| Model / Setting | TP | VP | Needle-QA | MLVU |
| --- | --- | --- | ---: | ---: |
| Uniform baseline | - | - | 63.4 | 61.7 |
| SFT2 | ✓ | - | 75.5 | 63.9 |
| SFT2 | - | ✓ | 70.4 | 62.2 |
| SFT2 | ✓ | ✓ | **75.8** | **64.1** |

Reason text ablation 显示，selector 的 reason 更适合解释和调试，不一定适合直接作为 downstream prompt。下表为 InternVL3.5-8B。

| Frames | Selector / Prompt | MLVU | VideoMME Avg | LVBench |
| ---: | --- | ---: | ---: | ---: |
| 8 | Uniform | 60.5 | 58.1 | 57.7 |
| 8 | K-frames + reason text | 65.6 | 57.8 | 52.5 |
| 8 | **K-frames** | **64.4** | **60.4** | **60.0** |
| 32 | Uniform | 67.0 | 64.6 | 60.1 |
| 32 | K-frames + reason text | 65.3 | 57.7 | 53.8 |
| 32 | **K-frames** | **68.4** | **65.1** | **61.8** |

## Training / Compute

| Item | Value |
| --- | --- |
| Selector backbone | Qwen2.5-VL-3B |
| Candidate frames for selector | $T=256$ uniformly sampled frames per video |
| Downstream model during RL | Frozen Qwen2.5-VL-7B |
| SFT training data | PeakClips |
| RL training data | 20K samples from original LLaVA-Video-178K |
| Trainable parts | Vision encoder frozen; multimodal projector and LLM updated |
| SFT time | 36 hours for the first two supervised phases |
| RL time | 40 hours |
| Learning rate | $1.0\times10^{-5}$ for SFT; $1.0\times10^{-6}$ for RL |
| RL regularization | KL penalty coefficient 0.01 |
| Inference sampling | $k=8$: Focused Sampling; $k=32/64$: Hybrid Sampling |
| Hardware | Not reported in the active paper text |

# Limitations & Caveats

- 对 holistic/global-level query 的提升可能有限。论文在 MLVU Topic Reasoning 和 VideoMME Information Synopsis 上观察到无明显提升，因为这类问题需要覆盖整体视频，预测出的 relevant span 往往接近全视频，最终退化为 uniform-like sampling。
- 对极长视频，selector 仍只看 $T=256$ candidate frames；如果证据非常稀疏，初始候选采样本身可能已经漏掉关键信息。
- Reason text 不能直接等同于可靠的下游推理依据。InternVL3.5 ablation 显示，把 K-frames reason 拼进 downstream prompt 会在多数指标上下降。
- PeakClips 标注依赖 Gemini 2.5 Pro 与 SIGLIP similarity，数据质量和偏差会影响 selector 学到的 relevance policy。
- 论文写到 dataset and model will be available，但 arXiv 页面和正文未给出明确 code URL；复现性暂时取决于后续释放。

# Concrete Implementation Ideas

1. 在现有 VideoQA pipeline 前面加一个 K-frames-style selector：先输出 P1/P2 clips，再把抽出的 frames 交给原 downstream MLLM，不改下游模型结构。
2. 推理时默认不要把 selector rationale 喂给 downstream model；可以把 rationale 用作 UI/debug trace，帮助人检查为什么选这些 clips。
3. 针对成本敏感场景先跑 $k=8$ Focused Sampling，只有当问题需要全局上下文或模型置信度低时再升到 $k=32$ Hybrid Sampling。
4. 对 domain-specific 长视频数据，可以复用 PeakClips schema：scene boundary、clip/chapter/video caption、query-conditioned relevance score、P1/P2 标签。
5. 为 global-summary 类 query 加一个 fallback：如果预测 clips 覆盖接近全视频，直接使用 uniform/hybrid broader context，避免 selector 过度聚焦。

# Open Questions / Follow-ups

- P1/P2 阈值 4.9 与 4.3 是否对不同 domain、不同视频长度都稳定？是否需要校准？
- RL reward 只在 multiple-choice QA 上定义，迁移到 open-ended QA、captioning、retrieval 任务时是否仍然有效？
- Selector 如果加入 audio、ASR、subtitle 或 OCR token，会不会改善需要语音/文本线索的问题？
- Any-k sampling 的最优策略是否应该随 query 类型动态变化，而不是只按 $k=8$ focused、$k=32/64$ hybrid 固定规则？
- 当 code/model/dataset 释放后，需要检查 PeakClips 的 license、annotation prompt、数据格式和下游评测脚本是否足够复现论文数字。

# Citation

```bibtex
@misc{yao2025kframes,
  title={K-frames: Scene-Driven Any-k Keyframe Selection for long video understanding},
  author={Yifeng Yao and Yike Yun and Jing Wang and Huishuai Zhang and Dongyan Zhao and Ke Tian and Zhihao Wang and Minghui Qiu and Tao Wang},
  year={2025},
  eprint={2510.13891},
  archivePrefix={arXiv},
  primaryClass={cs.LG},
  url={https://arxiv.org/abs/2510.13891}
}
```

Cite as: arXiv:2510.13891 [cs.LG]. Submitted on 14 Oct 2025.

<!-- USER_NOTES_START -->

<!-- USER_NOTES_END -->
