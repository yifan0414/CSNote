---
title: "Where to Focus: Query-Modulated Multimodal Keyframe Selection for Long Video Understanding"
authors:
  - Shaoguang Wang
  - Weiyu Guo
  - Ziyang Chen
  - Xuming Hu
  - Hui Xiong
conference:
year: 2026
arxiv_url: https://arxiv.org/abs/2604.17422
pdf_link: "[[assets/paper_2604.17422.pdf]]"
cover: "[[_assets/images/pipeline_2604.17422.png]]"
updated: 2026-05-20
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- 论文提出 **Q-Gate**：一个 plug-and-play、training-free 的长视频 keyframe selection 框架，把选帧问题重新表述为 query-modulated multimodal routing。
- 核心思想不是固定融合视觉/字幕线索，而是让 LLM Gater 根据问题意图动态分配三个 expert stream 的权重：Visual Grounding、Global Matching、Contextual Alignment。
- Q-Gate 重点解决静态融合中的 **modal noise**：视觉问题被无关字幕干扰，剧情/因果问题又缺少 narrative context。
- 在 LongVideoBench 和 Video-MME 上，Q-Gate 在多数受控复现实验中优于 Uniform、AKS*、VSLS、T*，尤其在 long/medium video split 和 Qwen3-VL backbone 上收益明显。
- 代价较低：框架无需训练，额外 routing 开销在作者的 end-to-end 分析中被描述为很小，同时因为只输入少量高价值帧，可以降低下游 VLM 的视觉 token 压力。

## Key Contributions

1. 将 long video keyframe selection 形式化为 **query-modulated routing problem**，用 Zero-Shot Mixture-of-Experts 的视角让 LLM 充当 gating network。
2. 设计三个互补 expert stream：$S_g$ 负责 object-level details，$S_m$ 负责 scene/global semantics，$S_c$ 负责 subtitle-driven narrative cues。
3. 通过 Min-Max Scaling 与 Masked Temperature Softmax 对异构分数做统一归一化，尤其避免没有字幕的帧在 softmax 后获得虚假概率质量。
4. 在 LongVideoBench 与 Video-MME 上给出跨 GPT-4o、Qwen3-VL-32B-Instruct、$K=8/32$ 的复现实验与 ablation，验证 dynamic gating、context stream、gater 模型选择和 temperature 的影响。
5. 提供可解释性分析：不同问题类型会触发不同权重分配，从 visual-heavy query 过渡到 narrative-heavy query。

## Method

Q-Gate 的 pipeline 可以压缩成三步：

1. **Multi-Granularity Scoring**  
   对视频 $V$ 中每个时间点生成三个对齐的 score distribution：
   - $S_g$: Visual Grounding，用 LLM 从 query 抽取视觉实体，再用 YOLO-World 检测帧中目标实体。
   - $S_m$: Global Matching，用 BLIP-2 ViT-L/14 的 image/text embedding 计算 query-frame cosine similarity。
   - $S_c$: Contextual Alignment，用 Sentence-BERT / all-mpnet-base-v2 计算 query 与对应 subtitle 的语义相似度；没有字幕时原始分数为 0。

2. **Unified Normalization**  
   每个 stream 先做 Min-Max Scaling：

   $$
   S_i^{scaled}(t)=\frac{s_i^{raw}(t)-\min(S_i^{raw})}{\max(S_i^{raw})-\min(S_i^{raw})}
   $$

   然后做 Masked Temperature Softmax：

   $$
   S_i(t)=
   \begin{cases}
   \frac{\exp(S_i^{scaled}(t)/\tau)}
   {\sum_{j:S_i^{raw}(j)>0}\exp(S_i^{scaled}(j)/\tau)} & \text{if } S_i^{raw}(t)>0 \\
   0 & \text{otherwise}
   \end{cases}
   $$

   实验默认 $\tau=0.5$。

3. **Query-Modulated Gating and Sampling**  
   GPT-4o 作为 LLM Gater，根据 query 生成权重 $W(q)=[w_g(q),w_m(q),w_c(q)]$，且 $\sum_i w_i=1$。最终融合分数为：

   $$
   S_{final}(t)=\sum_{i\in\{g,m,c\}} w_i(q)\cdot S_i(t)
   $$

   Sampler 选择 top-$K$ 帧，并把每张图像和对应字幕都用 timestamp 格式化进下游 VLM prompt，例如 image/subtitle 都锚定到 `MM:SS`，形成 temporal bridge。

## Pipeline Figure

![[_assets/images/pipeline_2604.17422.png]]

Caption: Overview of the **Q-Gate** framework. Given a video and a user query, Q-Gate computes multi-granularity scores from Visual Grounding, Global Matching, and Contextual Alignment; Query-Aware Gating dynamically modulates these streams into a final score distribution; Sampler selects top-$K$ frames/subtitles and builds a temporally aligned prompt for the downstream VLM. The caption explicitly notes that high-weight Contextual Alignment can suppress distractions from noisy visual streams.

Source: TeX `\includegraphics` from `main.tex`, using `figures/framework.pdf`; exported to PNG with `pdftoppm -cropbox`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| LongVideoBench | Long video QA / video understanding | Short <3min, Medium 3-15min, Long 15-60min | Accuracy (%) | 作者强调其同步多模态数据适合测试 look-and-listen synergy。 |
| Video-MME | Multi-modal video reasoning | Short <2min, Medium 4-30min, Long >30min | Accuracy (%) | 主要使用 Medium 与 Long subsets 测试长视频推理能力；表中也报告 Short。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training | Q-Gate 本身 training-free / optimization-free。 |
| Frame budget | $K=8$ 与 $K=32$。 |
| Visual Grounding | YOLO-World，appendix 指出使用 ResNet-50 backbone。 |
| Global Matching | BLIP-2 ViT-L/14 image/text encoders。 |
| Contextual Alignment | Sentence-Transformers `all-mpnet-base-v2`。 |
| Gater | GPT-4o 为主；ablation 中也测试 Qwen3-VL-32B 作为 gater。 |
| Downstream VLM | GPT-4o 与 Qwen3-VL-32B-Instruct。 |
| Normalization temperature | $\tau=0.5$。 |
| Code | 论文写明 code will be made publicly available upon acceptance；arXiv 源码中未给出仓库 URL。 |

### Main Results: GPT-4o Controlled Replication

所有数值为 accuracy (%)。加粗尽量保持原论文表格中的 emphasis；作者说明 Q-Gate 行中的蓝色括号为相对最佳 reproduced baseline 的绝对提升。

| Method | K | LVB Long | LVB Medium | LVB Short | Video-MME Long | Video-MME Medium | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| GPT-4o (Uniform) | 8 | 40.43 | 43.69 | 57.65 | 50.12 | 52.15 | 63.40 |
| GPT-4o + AKS* | 8 | 49.65 | 53.88 | 59.49 | 54.00 | 57.86 | 66.85 |
| GPT-4o + VSLS | 8 | 45.21 | 49.76 | 56.25 | 50.67 | 55.07 | 63.82 |
| GPT-4o + T* | 8 | 42.73 | 47.82 | 64.71 | 51.26 | 53.58 | 60.36 |
| **GPT-4o + Q-Gate (ours)** | 8 | **50.71** (+1.06) | **56.55** (+2.67) | 65.41 (+0.70) | **54.78** (+0.78) | **59.68** (+1.82) | **67.16** (+0.31) |
| GPT-4o (Uniform) | 32 | 43.79 | 46.36 | 60.00 | 52.40 | 52.96 | 68.63 |
| GPT-4o + AKS* | 32 | 47.70 | 50.97 | 61.88 | 52.89 | 59.20 | 66.63 |
| GPT-4o + VSLS | 32 | 44.50 | 49.51 | **68.24** | 50.68 | 55.11 | 64.05 |
| GPT-4o + T* | 32 | 43.62 | 48.79 | 63.53 | 51.48 | 56.01 | 66.28 |
| **GPT-4o + Q-Gate (ours)** | 32 | **50.35** (+2.65) | **53.64** (+2.67) | 63.75 | **60.05** (+7.16) | **62.77** (+3.57) | **69.44** (+0.81) |

### Main Results: Qwen3-VL Controlled Replication

| Method | K | LVB Long | LVB Medium | LVB Short | Video-MME Long | Video-MME Medium | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen3-VL (Uniform) | 8 | 46.63 | 51.46 | **71.76** | 51.14 | 52.15 | 63.40 |
| Qwen3-VL + AKS* | 8 | 54.61 | 60.92 | 70.59 | 54.45 | 58.33 | **68.79** |
| Qwen3-VL + VSLS | 8 | 51.60 | 55.83 | 69.41 | 51.37 | 53.76 | 66.50 |
| Qwen3-VL + T* | 8 | 50.89 | 54.13 | 67.06 | 52.28 | 55.60 | 65.79 |
| **Qwen3-VL + Q-Gate (ours)** | 8 | **58.69** (+4.08) | **63.11** (+2.19) | 68.24 | **57.19** (+2.74) | **61.29** (+2.96) | **73.04** (+4.25) |
| Qwen3-VL (Uniform) | 32 | 51.24 | 56.55 | **71.76** | 51.60 | 54.57 | 65.85 |
| Qwen3-VL + AKS* | 32 | 57.80 | **65.29** | 67.06 | 54.79 | 62.90 | 75.68 |
| Qwen3-VL + VSLS | 32 | 52.66 | 58.74 | 65.88 | 54.68 | 59.81 | 74.35 |
| Qwen3-VL + T* | 32 | 51.95 | 56.55 | 69.41 | 54.22 | 58.57 | 75.00 |
| **Qwen3-VL + Q-Gate (ours)** | 32 | **59.40** (+1.60) | 63.11 | 70.59 | **61.19** (+6.40) | **66.13** (+3.23) | **79.41** (+3.73) |

### Reported SOTA Reference Block

论文把这些作为 broader reference，并明确提醒 backbone VLM、参数量、frame input 不同，不能视为严格公平比较。

| Reference Method | Frames | LVB Long | LVB Medium | LVB Short | Video-MME Method | Frames | Video-MME Long | Video-MME Medium | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| FOCUS (LLaVA-V-7B) | 64 | 63.7 | 59.0 | 72.3 | FOCUS (LLaVA-V-7B) | 64 | 56.1 | 63.5 | 76.5 |
| LLaVA-OneVision-72B | 32 | 59.3 | 63.9 | 77.4 | LLaVA-OneVision-72B | 32 | 60.0 | 62.2 | 66.3 |
| GPT-4o (0513) | 256 | 61.6 | 66.7 | 76.8 | Q-Frame (GPT-4o) | 8 | 57.6 | 63.8 | 69.9 |
| LLaVA-Video-72B-Qwen2 | 128 | 59.3 | 63.9 | 77.4 | Gemini-1.5-Pro (0615) | 1 fps | 67.4 | 74.3 | 75.0 |

### Ablations / Analysis

#### Impact of Multi-Granularity Modalities

Qwen3-VL-32B-Instruct, $K=32$。去掉 $S_c$ 对 LongVideoBench Long 的伤害最大，从 59.40 降到 54.08，支撑作者关于 narrative-heavy 内容必须“listen”的论点。

| Model Variant | LVB Long | LVB Med. | LVB Short | Video-MME Long | Video-MME Med. | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **Full Model (Q-Gate)** | **59.40** | 63.11 | **70.59** | **61.19** | 66.13 | **79.41** |
| w/o Contextual Align. ($S_c$) | 54.08 | 58.01 | 67.06 | 58.79 | 63.17 | 76.31 |
| w/o Visual Grounding ($S_g$) | 58.33 | 61.89 | 64.71 | 59.36 | **66.40** | 78.43 |
| w/o Global Matching ($S_m$) | 57.45 | **64.81** | 63.53 | 60.73 | 65.32 | 78.59 |

#### Efficacy of Query-Aware Gating

Dynamic 表示 Q-Gate 的 Query-Aware Gating；Static 表示 Equal Weights $w_g=w_m=w_c=1/3$。

| VLM | K | Strategy | LVB Long | LVB Med. | LVB Short | Video-MME Long | Video-MME Med. | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| GPT-4o | 8 | Static | 47.70 | 53.64 | 55.56 | 54.44 | **60.00** | 66.67 |
| GPT-4o | 8 | **Dynamic** | **50.71** | **56.55** | **65.41** | **54.78** | 59.68 | **67.16** |
| Qwen3-VL | 32 | Static | 57.73 | 62.62 | 55.67 | 60.05 | **66.80** | 78.92 |
| Qwen3-VL | 32 | **Dynamic** | **59.40** | **63.11** | **70.59** | **61.19** | 66.13 | **79.41** |

#### Robustness of the Gating Mechanism

下游 QA backbone 固定为 Qwen3-VL-32B；只替换 gater。GPT-4o 在 $K=8$ 更强，但 $K=32$ 时 Qwen3-VL gater 缩小差距。

| K | Gater Model | LVB Long | LVB Med. | LVB Short | Video-MME Long | Video-MME Med. | Video-MME Short |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 8 | GPT-4o | **58.69** | **63.11** | **68.24** | **57.19** | **61.29** | **73.04** |
| 8 | Qwen3-VL | 56.38 | 61.17 | 63.53 | 53.77 | 61.02 | 72.39 |
| 32 | GPT-4o | **59.40** | 63.11 | **70.59** | **61.19** | **66.13** | **79.41** |
| 32 | Qwen3-VL | 58.16 | **63.35** | 65.88 | 59.47 | 64.78 | 78.95 |

#### Temperature Sensitivity

Qwen3-VL-32B, $K=8$, LongVideoBench。作者报告 $\tau=0.5$ 达到峰值，解释为过低温度近似 one-hot、损失 temporal diversity；过高温度过于平滑，接近 uniform sampling。

| Temperature $\tau$ | LVB Long | LVB Medium | LVB Short |
| ---- | ---- | ---- | ---- |
| 0.1 | 57.61 | 60.19 | 62.89 |
| 0.3 | 54.61 | 59.95 | 56.70 |
| 0.5 | **58.69** | **63.11** | **68.24** |
| 0.7 | 56.21 | 61.17 | 58.76 |
| 0.9 | 55.85 | 61.41 | 58.76 |

#### Heuristic Gating Algorithm

Appendix 里作者还给了一个 zero-latency Heuristic Gating：通过 keyword matching 给 grounding / matching / context 的 potential score 加权，再 softmax 成 $[w_g,w_m,w_c]$。它强于 static fusion，但仍弱于 LLM Agent。

| Strategy | LVB Long | LVB Medium | LVB Short |
| ---- | ---- | ---- | ---- |
| Static (Equal Weights) | 47.70 | 53.64 | 55.56 |
| **Dynamic (Heuristic)** | 49.50 | 54.80 | 59.20 |
| **Dynamic (LLM Agent)** | **50.71** | **56.55** | **65.41** |

#### Method Landscape Comparison

| Method | Training-free | Query-aware | Multimodal | Fine-grained Grounding | Narrative Context | Selection Mechanism |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Uniform | yes | no | no | no | no | Static |
| AKS | yes | yes | no | no | no | Similarity |
| T* | yes | yes | no | yes | no | Iterative |
| VSLS | yes | yes | no | yes | no | Semantic |
| Q-Frame | yes | yes | no | no | no | Resolution |
| FOCUS | yes | yes | no | no | no | MAB-Bandit |
| Frame-Voyager | no | yes | no | no | no | Agentic |
| **Q-Gate (Ours)** | yes | yes | yes | yes | yes | **Gated** |

## Limitations & Caveats

- **Audio-Visual Temporal Misalignment**: 真实视频中 subtitle cue 与视觉高潮可能存在自然延迟；仅定位字幕时间点可能错过真正相关画面。
- **Downstream Reasoning Bottleneck**: 作者观察到 Q-Gate 有时已经选中包含证据的 ground-truth keyframes，但下游 VLM 仍回答错误，说明瓶颈会转移到 MLLM 的 multi-hop reasoning。
- **Beyond Textual Audio Cues**: 当前 “Listen” 只使用 textual subtitles，没有建模 sound effects、background music 等 non-speech audio cues。
- **Latency Distillation**: 使用 GPT-4o 作为 gater 仍有成本与隐私问题；作者建议未来把 routing 能力蒸馏到 lightweight student model。
- **公平比较边界**: 主表中的灰色 SOTA reference block 与受控复现实验并不完全同条件；不同模型参数、frame 输入数量和 API 能力会显著影响结果。
- **代码未开放**: arXiv 源码里只写了 acceptance 后开放代码，因此目前复现细节仍依赖论文描述。

## Concrete Implementation Ideas

1. 在现有 video QA pipeline 里把 Q-Gate 做成一个前置 retriever：输入 video frames、subtitles、query，输出 top-$K$ timestamped frames 与 subtitle snippets。
2. 先实现 Heuristic Gating 版本作为低延迟 baseline，再用 GPT-4o / Qwen3-VL 生成 routing weights 做性能上限对比。
3. 对 subtitle-heavy 数据加入 temporal expansion window，例如在 $S_c$ 峰值附近额外采样 $\pm n$ 秒的视觉帧，缓解 dialogue-action lag。
4. 记录每个 query 的 $[w_g,w_m,w_c]$、top-$K$ frame timestamps 和最终答案，做一个 routing audit dashboard，快速发现 modal noise 与 missed evidence。
5. 如果部署环境不能调用 proprietary LLM，可收集 LLM Gater 的权重输出，训练一个 lightweight classifier/regressor 做 gater distillation。

## Open Questions / Follow-ups

- Q-Gate 在没有高质量字幕、ASR 错误较多、或者多说话人重叠的长视频中会下降多少？
- $S_g$ 使用 YOLO-World 的 object-centric grounding；如果问题涉及细粒度动作、关系或状态变化，是否需要额外 action/scene graph expert？
- LLM Gater 的 prompt 是否对不同语言 query 稳定？中文问题、混合语言字幕、跨语言视频会不会改变 routing behavior？
- Top-$K$ 是否足够？对于剧情类问题，是否应该把 sampling 从独立 top-$K$ 改成 segment-aware 或 evidence-chain-aware selection？
- 作者的 “modal noise” 能否被更形式化地度量，例如 stream-level negative transfer score 或 query-conditioned mutual information？

## Citation

```bibtex
@misc{wang2026focusquerymodulatedmultimodalkeyframe,
      title={Where to Focus: Query-Modulated Multimodal Keyframe Selection for Long Video Understanding}, 
      author={Shaoguang Wang and Weiyu Guo and Ziyang Chen and Xuming Hu and Hui Xiong},
      year={2026},
      eprint={2604.17422},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2604.17422}, 
}
```
