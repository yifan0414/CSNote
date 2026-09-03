---
title: (frame)CoSeLECT
authors:
  - Anonymous
conference: ICLR 2026×
year: 2026
paper_url: https://openreview.net/forum?id=Pr3I3ewBFU
source_pdf: https://openreview.net/pdf/85bab755c7254aed0b86d31707b4fac0a92d777d.pdf
pdf_link: "[[assets/paper_85bab755c7254aed0b86d31707b4fac0a92d777d.pdf]]"
cover: "[[assets/pipeline_85bab755c7254aed0b86d31707b4fac0a92d777d.png]]"
updated: 2026-05-19
tags:
  - paper/pdf
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: read
priority: "3"
rating: "3"
topics:
  - Video Understanding
code: ""
---

## TL;DR

- CoSeLECT 是一个 training-free、plug-and-play 的 query-guided frame selection 方法，用来在 MLLM 的 token budget 下为长视频挑选更有用的帧。
- 方法同时使用两类信号：frame-query semantic relevance 和 inter-frame visual continuity；前者找与问题相关的帧，后者把视频切成视觉连续的 subclips，避免只盯着局部高相似度片段。
- 核心选择策略是先根据 scene boundaries 得到 subclips，再用 $R_i=\max(S_{\text{text}}\mid C_i)+\mathrm{mean}(S_{\text{text}}\mid C_i)$ 与 $\sqrt{D_i}$ 做预算分配，最后在每个 subclip 内分段选最高 text relevance 的帧。
- 在 VideoMME、MLVU、MVBench、EgoSchema、LongVideoBench、NextQA 等 benchmark 上，CoSeLECT 在多个 backbone 上稳定提升，尤其在 long-horizon / long-video 场景里更明显。
- PDF 声称 CoSeLECT 相比 LongVU 在 MLVU 上提升 +3.8%，相比 AKS 在 EgoSchema 上提升 +4.5%；但论文仍是 ICLR 2026 under review，作者匿名，结论应按未正式发表版本看待。
- **Limitations section**
![[Pasted image 20260606134112.png]]
## Key Contributions

- 提出 CoSeLECT（Continuity-aware Semantic Localization and Extraction of Candidate Tokens），把 keyframe selection 作为 frame-level token reduction，避免训练额外 compression module。
- 用同一套简单信号融合 frame-text similarity 与 frame-frame similarity：既保留 query-relevant frames，也保证 temporal / scene coverage。
- 设计 duration-aware adaptive allocation：长 subclip 可以得到更多帧，但通过 $\sqrt{D_i}$ 避免长片段过度占用 frame budget。
- 在多个 MLLM family / model size 上验证，包括 LLaVA-OneVision、Qwen2.5-VL、GPT-4o-mini，以及 Qwen2-7B / Qwen2-0.5B decoder 设置。
- 提供较完整的 ablation：composite relevance、duration weighting、similarity threshold、pre-Eim pool size、post-Eim selected frames、encoder choice 都有测试。

## Method

CoSeLECT 的目标是在输入视频候选帧 $V=\{f_1,\dots,f_N\}$、query $Q$、目标输出帧数 $K$ 下，选择一组既 relevant 又 diverse 的 frames。论文中 $N$ 记作 pre-Eim，$K$ 记作 post-Eim。

1. Uniformly sample $N$ candidate frames from the video.
2. 用 image encoder $E_{\text{im}}$ 和 text encoder $E_{\text{text}}$ 计算 frame embedding 与 query embedding。
3. Text relevance signal：

$$
S_{\text{text}}(t)=E_{\text{im}}(f_t)\odot E_{\text{text}}(Q)
$$

这里 $\odot$ 表示 normalized embeddings 的 cosine similarity，随后沿时间维做 Gaussian smoothing。

4. Visual continuity signal：

$$
S_{\text{frame}}(t)=E_{\text{im}}(f_t)\odot E_{\text{im}}(f_{t+1})
$$

再根据阈值切 scene：

$$
\mathrm{SceneBoundaries}=\{k\mid S_{\text{frame}}(k)<\tau_{\text{sim}}\},\quad \tau_{\text{sim}}=0.8
$$

5. 对每个 subclip $C_i$ 计算 composite relevance：

$$
R_i=\max(S_{\text{text}}\mid C_i)+\mathrm{mean}(S_{\text{text}}\mid C_i)
$$

6. 用 duration-aware weight 分配帧预算：

$$
W_i=R_i\sqrt{D_i},\quad
k_i=\left\lfloor K\cdot \frac{W_i}{\sum_{j=1}^{M}W_j}\right\rfloor
$$

7. 对每个 $k_i>0$ 的 subclip，将其时间范围均分为 $k_i$ 个 segment，并在每个 segment 里选 $S_{\text{text}}$ 最高的帧。这样可以减少 relevance peak 附近的重复采样。

## Pipeline Figure

![[assets/pipeline_85bab755c7254aed0b86d31707b4fac0a92d777d.png]]

Caption: CoSeLECT 是一个 query-aware frame selection 方法，选择同时具备 semantic relevance 与 visual narrative representativeness 的帧，以适配 token-budget constrained MLLM 的长视频理解。

Source: PDF page 4 cropped Figure 1 render.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| VideoMME | Video understanding / video QA | not specified in extracted text | Accuracy / score (%) | 多模态视频分析综合 benchmark |
| MLVU | Long video understanding | dev split | Accuracy / score (%) | 长视频多任务理解 |
| MVBench | Video understanding | not specified in extracted text | Accuracy / score (%) | 多模态视频理解 benchmark |
| EgoSchema | Egocentric long video QA | subset split | Accuracy / score (%) | 长时序 egocentric 场景 |
| LongVideoBench | Very long video-language understanding | validation set | Accuracy / score (%) | 长视频 benchmark，论文也报告 subtask breakdown |
| NextQA | Video QA | test set | Accuracy / score (%) | 用于与 trained frame-selection 方法比较 |

### Main Results

Table 1（PDF page 6）比较 training-free frame selection / token reduction 方法，backbone 为 LLaVA-OneVision（LLaVA-OV）。表中数值为 PDF 报告值；CoSeLECT 行使用粗体标出其报告结果。

| Method | Context Length | Frames pre-Eim | VideoMME | MVBench | LongVideoBench | EgoSchema |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OV (Baseline) | 8k | N/A | 58.4 | 57.8 | 56.8 | 62.8 |
| SlowFast-LLaVA | 3.6k | 32 | 56.1 | 56.4 | 55.1 | 61.4 |
| LLaVA-OV + Static or Dynamic | 8k | 128 | 59.9 | - | - | 60.5 |
| LLaVA-OV + QuoTA | 8k | 64 | 60.7 | - | 57.4 | - |
| LLaVA-OV + BOLT | 8k | fps | 59.9 | - | 59.6 | 64.0 |
| LLaVA-OV + AKS | 8k | 64 | 58.2 | 57.4 | 56.4 | 62.6 |
| LLaVA-OV + AKS | 8k | 400 | 60.2 | 56.6 | 57.4 | 61.4 |
| LLaVA-OV + AKS | 8k | 1600 | 61.8 | 58.1 | 57.9 | 62.0 |
| **LLaVA-OV + CoSeLECT (ours)** | 8k | 32 | **57.7** | **57.8** | **57.1** | **63.4** |
| **LLaVA-OV + CoSeLECT (ours)** | 8k | 64 | **58.6** | **57.6** | **57.7** | **64.8** |
| **LLaVA-OV + CoSeLECT (ours)** | 8k | 400 | **59.7** | **58.1** | **59.3** | **64.0** |
| **LLaVA-OV + CoSeLECT (ours)** | 8k | 1600 | **61.1** | **58.2** | **58.8** | **63.0** |

Table 2（PDF page 7）把 CoSeLECT 与 trained frame selection / token reduction 方法对比。由于 backbone 不完全一致，论文按 block 比较；这里保留关键 rows。

| Method | Training Free | LLM Size | Vision Encoder Size | Context Length | Frames pre-Eim | NextQA | MLVU |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| SeViLA | no | 3B | 1.1B | 2K | 32 | 73.8 | - |
| ViLA | no | 3B | 1.4B | 2K | 32 | 74.8 | - |
| **CoSeLECT + Qwen2.5-VL-3B-Instruct** | yes | 3B | 0.4B | 2K | 32 | **74.6** | - |
| GCG | no | 7B | 0.4B | 1K | 32 | 74.6 | - |
| **CoSeLECT + LLaVA-OV** | yes | 7B | 0.4B | 1K | 32 | **76.9** | - |
| Frame-Voyager | no | 7B | 0.4B | 2K | 32 | 73.9 | 65.6 |
| **CoSeLECT + LLaVA-OV** | yes | 7B | 0.4B | 2K | 32 | **78.0** | **66.1** |
| LongVA | no | 7B | 0.4B | 224K | 32 | 69.3 | 56.3 |
| VideoChat2 | no | 7B | 0.3B | 8K | 16 | - | 47.9 |
| **CoSeLECT + LLaVA-OV** | yes | 7B | 0.4B | 8K | 32 | **80.0** | **63.5** |
| LongVU | no | 7B | 0.4B | 8K | 1fps | - | 65.4 |
| **CoSeLECT + LLaVA-OV** | yes | 7B | 0.4B | 8K | 1600 | **80.1** | **67.9** |

Robustness across backbones（Table 4, PDF page 8）：pre-Eim=800，post-Eim=32。

| Method | LLM | Context Length | VideoMME | MVBench | MLVU | LongVideoBench | EgoSchema | Average |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-4o-mini | GPT-4o-mini | 8k | - | - | 64.9 | - | - | 64.9 |
| **+ CoSeLECT** | GPT-4o-mini | 8k | - | - | **66.1** | - | - | **66.1** |
| LLaVA-OV | Qwen2-7B | 8k | 58.4 | 57.8 | 62.4 | 56.8 | 62.8 | 59.6 |
| **+ CoSeLECT** | Qwen2-7B | 8k | **59.7** | **58.1** | **67.3** | **59.3** | **64.0** | **61.6** |
| LLaVA-OV | Qwen2-0.5B | 8k | 43.7 | 46.3 | 46.5 | 46.8 | 26.6 | 42.0 |
| **+ CoSeLECT** | Qwen2-0.5B | 8k | **45.6** | **46.5** | **49.5** | **47.8** | **26.6** | **43.2** |
| Qwen2.5-VL-7B-Inst | Qwen2.5-7B | 8k | 61.3 | 68.3 | 59.5 | 58.9 | 59.8 | 61.6 |
| **+ CoSeLECT** | Qwen2.5-7B | 8k | **63.3** | **69.5** | **63.4** | **59.2** | **59.6** | **63.0** |

### Ablations / Analysis

Frame selection strategy（Table 5, PDF page 8）：CoSeLECT 同时用 text similarity 和 visual continuity，平均分最高。

| Frame selection method | Frames pre-Eim | Frames post-Eim | VideoMME | MVBench | MLVU | LongVideoBench | EgoSchema | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Uniform sampling | 32 | 32 | 58.4 | 57.8 | 62.4 | 56.8 | 62.8 | 59.6 |
| 32 top text similarity frames | 400 | 32 | 60.7 | 57.6 | 65.7 | 57.7 | 61.8 | 60.7 |
| Only Visual Continuity | 400 | 32 | 59.1 | 57.9 | 64.9 | 57.6 | 63.0 | 60.5 |
| **CoSeLECT (ours)** | 400 | 32 | **59.7** | **58.1** | **65.9** | **59.3** | **64.0** | **61.4** |

Composite relevance 与 duration weighting（Table 7, PDF page 16）：完整设计在平均分上最高。

| Variant / Setting | VideoMME | MVBench | MLVU | LongVideoBench | EgoSchema | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| $D_i$ instead of $\sqrt{D_i}$ | 60.1 | 58.1 | 66.2 | 58.6 | 63.6 | 61.3 |
| $R_i=\max(S_{\text{text}}\mid C_i)$ only | 60.1 | 57.7 | 66.0 | 58.0 | 63.6 | 61.1 |
| $R_i=\mathrm{mean}(S_{\text{text}}\mid C_i)$ only | 60.5 | 58.1 | 66.0 | 58.8 | 63.8 | 61.4 |
| **CoSeLECT** | **60.6** | **58.3** | **66.2** | **59.3** | **64.5** | **61.8** |

Frame-to-frame similarity threshold（Table 8, PDF page 17）：论文在测试集上选择 $\tau_{\text{sim}}=0.8$。

| Threshold | VideoMME | MVBench | MLVU | LongVideoBench | EgoSchema | Average |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | 60.0 | 58.2 | 67.1 | 58.4 | 64.2 | 61.6 |
| 0.4 | 60.0 | 58.0 | 66.8 | 57.3 | 63.8 | 61.2 |
| 0.6 | 60.0 | 57.9 | 66.8 | 58.0 | 63.8 | 61.3 |
| **0.8** | **60.1** | **58.1** | **67.3** | **59.3** | **64.0** | **61.8** |

Candidate frame pool size（Table 9, PDF page 17）：pre-Eim 越大通常越好，但有 diminishing returns，且 MVBench 增益较小。

| Method | Frames pre-Eim | Frames post-Eim | VideoMME | MVBench | MLVU | LongVideoBench | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OV + Uniform Sampling | 32 | 32 | 58.4 | 57.8 | 62.4 | 56.8 | 58.9 |
| **LLaVA-OV + CoSeLECT** | 32 | 32 | **57.7** | **57.8** | **63.5** | **57.1** | **59.0** |
| **LLaVA-OV + CoSeLECT** | 64 | 32 | **58.6** | **57.6** | **65.1** | **57.7** | **59.8** |
| **LLaVA-OV + CoSeLECT** | 100 | 32 | **59.0** | **57.9** | **64.5** | **56.5** | **59.5** |
| **LLaVA-OV + CoSeLECT** | 200 | 32 | **58.9** | **57.8** | **65.2** | **58.3** | **60.1** |
| **LLaVA-OV + CoSeLECT** | 400 | 32 | **59.7** | **58.1** | **67.3** | **59.3** | **61.1** |
| **LLaVA-OV + CoSeLECT** | 800 | 32 | **60.6** | **58.3** | **66.2** | **59.3** | **61.1** |
| **LLaVA-OV + CoSeLECT** | 1600 | 32 | **61.1** | **58.1** | **67.9** | **58.8** | **61.5** |

### Training / Compute

| Item | Value |
| --- | --- |
| Main image/text encoder | SigLIP-ViT-SO400M-patch14-384 associated with LLaVA-OneVision |
| Input image preprocessing | resize to 384 x 384; patch size 14 x 14 |
| Default selected frames | post-Eim = 32 unless specified |
| Candidate pool sizes | pre-Eim = 32, 64, 400, 1600 in main experiments; appendix also tests 100, 200, 800 |
| Hardware | single 40G A40 nodes with 8 GPUs |
| Latency observation | Encoding 1600 frames is 32x FLOPs vs 50 frames, but only 4.1x wall-clock latency under 8-GPU parallel execution |
| Similarity overhead | Appendix C.1 reports only 0.08% of time spent on inter-frame and text-frame embedding comparisons |

## Limitations & Caveats

- 论文仍处于 ICLR 2026 under review，作者匿名，实验与表述可能还会变化。
- 方法继承底层 vision-language encoder 的 biases 与 failure modes，例如 SigLIP、Qwen2.x 的视觉语义偏差。
- 当前方法只处理 RGB frames，没有使用 audio 或 motion-specific features；对于需要声音、动作速度、细粒度运动模式的问题可能不够。
- 大 pre-Eim pool 需要先 encode 很多候选帧，虽然 wall-clock 可以通过并行降低，但资源占用仍取决于 vision encoder 与硬件。
- $\tau_{\text{sim}}=0.8$ 是论文测试集经验选择，新任务、新数据域可能需要 validation tuning。
- 论文没有提供公开 code 链接；复现实验需要自行实现 frame sampling、embedding、scene segmentation 与预算分配细节。

## Concrete Implementation Ideas

- 做一个 drop-in frame selector：输入 video frames + query + target frame count，输出 selected frame indices，并保持与现有 LLaVA-OneVision / Qwen2.5-VL preprocessing 解耦。
- 先用轻量 encoder（如 CLIP-B）实现快速版本，再切换到 SigLIP / DINO-ViT 做准确率对照；论文 Table 6 暗示轻量 encoder 已有竞争力。
- 给实际业务任务加一个 validation sweep：搜索 pre-Eim、post-Eim、$\tau_{\text{sim}}$，因为不同 benchmark 对候选池大小的收益不一致。
- 扩展到 audio-visual selection：把 audio event score 或 motion saliency 加入 subclip weight，补上论文限制中未覆盖的声音/运动信息。
- 在 serving 侧缓存 frame embeddings；同一视频的多 query 场景下只重新计算 text relevance 与 allocation。

## Open Questions / Follow-ups

- CoSeLECT 在不同 video domain（surveillance、sports、medical、instructional videos）中的最佳 $\tau_{\text{sim}}$ 是否稳定？
- 当 query 需要非常短暂的 motion cue，而不是静态 semantic cue 时，frame-text similarity 是否足够？
- 如果同一视频有多个 queries，是否可以联合选择一个 shared frame set，还是每个 query 都应单独选择？
- 与 token-level pruning 结合时，frame-level selection 和 token-level pruning 的先后顺序是否影响性能？
- 是否可以用 uncertainty 或 answer confidence 反馈来二次选择 frames，形成 test-time adaptive loop？

## Citation

Anonymous. "CoSeLECT: Adaptive Frame Selection for Video-Language Understanding." Under review as a conference paper at ICLR 2026. OpenReview PDF: https://openreview.net/pdf/85bab755c7254aed0b86d31707b4fac0a92d777d.pdf
