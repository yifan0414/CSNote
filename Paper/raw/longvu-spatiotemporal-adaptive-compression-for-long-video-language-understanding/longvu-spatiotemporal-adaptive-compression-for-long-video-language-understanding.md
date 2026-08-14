---
title: LongVU(token compression)
authors:
  - Xiaoqian Shen
  - Yunyang Xiong
  - Changsheng Zhao
  - Lemeng Wu
  - Jun Chen
  - Chenchen Zhu
  - Zechun Liu
  - Fanyi Xiao
  - Balakrishnan Varadarajan
  - Florian Bordes
  - Zhuang Liu
  - Hu Xu
  - Hyunwoo J. Kim
  - Bilge Soran
  - Raghuraman Krishnamoorthi
  - Mohamed Elhoseiny
  - Vikas Chandra
conference: ICML 2025
year: 2024
arxiv_url: https://arxiv.org/abs/2410.17434
pdf_link: "[[assets/paper_2410.17434.pdf]]"
cover: "[[assets/pipeline_2410.17434.png]]"
updated: 2026-05-26
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
code: https://github.com/Vision-CAIR/LongVU
---

## TL;DR

- LongVU 面向 hour-long video understanding，核心目标是在常用的 8k LLM context length 内尽量保留长视频视觉细节，而不是只做稀疏 uniform sampling。
- 方法是三段式 spatiotemporal adaptive compression：DINOv2 做 temporal frame reduction，text query 做 selective high-resolution frame selection，最后用 inter-frame dependency 做 Spatial Token Compression (STC)。
- 7B LongVU 在 8k context、1fps 输入下，报告了 EgoSchema **67.6**、MVBench **66.9**、MLVU **65.4**、VideoMME Overall **60.6**、VideoMME Long **59.5**。
- 长视频收益最明显：论文称 LongVU 在 VideoMME Long 上比 LLaVA-OneVision 高 12.8 个百分点，并且在 MLVU/VideoMME 这类长视频 benchmark 上更能体现 token compression 的价值。
- 代价和 caveat 也很清楚：训练使用 64 NVIDIA H100，且 video-only SFT 会让 image understanding benchmark 明显下降。

## Key Contributions

1. 提出 LongVU，一种面向 long video-language understanding 的 MLLM token compression 方案，在 8k context 内处理 1fps 长视频输入。
2. 用 DINOv2 feature similarity 做 temporal reduction。作者认为 DINOv2 的 self-supervised visual representation 比 CLIP/SigLIP 这类 language-aligned feature 更适合捕捉 frame-level subtle differences。
3. 提出 query-aware selective feature reduction：用 text query 与 visual tokens 的 cross-modal attention 选择少量相关帧保留高分辨率 token，其余帧降到低分辨率 token。
4. 提出 Spatial Token Compression (STC)：在 window 内用第一帧作为 anchor，剪掉后续帧中与 anchor 同位置高度相似的 spatial tokens，以利用视频背景和静态区域的冗余。
5. 系统验证 LongVU 在 EgoSchema、MVBench、VideoMME、MLVU 上的效果，并给出 component ablation、MLVU subtask analysis、Video Needle-in-a-Haystack 和 compression ratio analysis。

## Method

LongVU 的 pipeline 可以压缩成下面几步：

1. **Temporal Reduction with DINOv2**  
   对 1fps sampled frames $I=\{I^1,\ldots,I^N\}$ 提取 DINOv2 features $\{V_{\text{dino}}^1,\ldots,V_{\text{dino}}^N\}$。在非重叠 window 内，作者设 $J=8$，计算每帧和其他帧的平均相似度：

   $$
   \text{sim}^i = \frac{1}{J-1}\sum_{j=1,j\neq i}^{J}\text{sim}(V_{\text{dino}}^i,V_{\text{dino}}^j)
   $$

   高相似帧被移除，原始 $N$ 帧压缩成 $T$ 帧。论文的 compression analysis 中报告 temporal reduction 后平均保留约 $45.9\%$ 的 frames。

2. **SigLIP + DINOv2 Feature Fusion**  
   temporal reduction 后，剩余 $T$ 帧再用 SigLIP vision encoder 提取 features，并参考 Cambrian 的 Spatial Vision Aggregator (SVA) 融合 SigLIP 与 DINOv2 features，得到 $V=\{V^1,\ldots,V^T\}$。

3. **Selective Feature Reduction via Cross-modal Query**  
   若 $T\times H_h\times W_h$ 超过 context budget，LongVU 用 text query embedding $Q\in\mathbb{R}^{L_q\times D_q}$ 选择 $N_h$ 个 query-relevant frames 保留高分辨率 token，其他帧用 spatial pooling 降到 $H_l\times W_l$：

   $$
   \mathbf{Top}_{N_h}\left(\frac{1}{H_hW_hL_q}\sum_{h,w,l}\mathcal{F}(V)Q^T\right),\quad
   N_h=\max\left(0,\frac{L_{\text{max}}-L_q-TH_lW_l}{H_hW_h-H_lW_l}\right)
   $$

   这里 $\mathcal{F}(\cdot)$ 是把 visual feature 对齐到 LLM input space 的 MLP-based multimodal adapter。

4. **Spatial Token Compression (STC)**  
   如果低分辨率 token 仍超过 budget，即 $T\times H_l\times W_l \geq L_{\text{max}}$，LongVU 在 sliding window 内进一步做 spatial token pruning。窗口大小 $K=8$，默认用窗口第一帧作为 anchor，若后续帧同一空间位置 token 与 anchor 相似度超过阈值 $\theta=0.8$，则剪掉该 token：

   $$
   v_i^* \leftarrow
   \begin{cases}
   v_i(h,w) & \text{sim}(v_1(h,w), v_i(h,w)) \leq \theta \\
   \emptyset & \text{otherwise}
   \end{cases},
   \quad \forall h\in[1,H_l], w\in[1,W_l], i\in[2,K]
   $$

5. **Training Setup**  
   训练分成 image-language pre-training 和 video-language finetuning 两阶段。image stage 使用 LLaVA-OneVision single-image data；video stage 使用 VideoChat2-IT subset，加上 MovieChat 作为 long video complementary data。训练目标是 autoregressive text generation 的 cross-entropy loss。

## Pipeline Figure

![[assets/pipeline_2410.17434.png]]

Caption: Architecture of LongVU. Given densely sampled video frames, the model first uses DINOv2 prior to remove redundant frames, fuses remaining frame features from SigLIP and DINOv2, selectively reduces visual tokens via cross-modal query, and finally performs spatial token compression based on temporal dependencies to fit the LLM context length.

Source: TeX includegraphics from `sections/3-methods.tex`, rendered from `assets/main.pdf` with visible crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| EgoSchema | Long-form egocentric video QA | Evaluation benchmark | Accuracy | 平均时长约 179.8 sec |
| MVBench | Multi-modal video understanding | Evaluation benchmark | Accuracy | 平均时长约 16 sec |
| VideoMME | Long video understanding | Overall, Long subset | Accuracy | 视频长度 1 min 到 1 hour；Long subset 为 30 到 60 min |
| MLVU | Long video understanding | Multiple subtasks | Accuracy / Avg | 视频长度 3 min 到 2 hours，含 count、needle、order、plotQA 等 subtasks |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Vision encoders | SigLIP so400m-patch14-384 + DINOv2 |
| Language backbones | Qwen2-7B, Llama3.2-3B |
| Loss | Cross-entropy loss for autoregressive text generation |
| Optimizer | AdamW with cosine schedule |
| Image-language pre-training | 1 epoch, global batch size 128, learning rate 1e-5, warmup rate 0.03, 576 tokens per image |
| Video-language finetuning | 1 epoch, global batch size 64, learning rate 1e-5, warmup rate 0.03 |
| Token settings | Max 144 tokens per frame, adaptively reduced to $\leq 64$ low-resolution tokens with $H_l=W_l=8$ |
| STC settings | Threshold $\theta=0.8$, sliding window size $K=8$ |
| Hardware | 64 NVIDIA H100 GPUs |

### Training Data

| Modality | Task | # Samples | Dataset |
| ---- | ---- | ---- | ---- |
| Image-Text | Single-Image | 3.2M | LLaVA-OneVision |
| Video-Text | Captioning | 43K | TextVR, MovieChat, YouCook2 |
| Video-Text | Classification | 1K | Kinetics-710 |
| Video-Text | VQA | 424K | NExTQA, CLEVRER, EgoQA, TGIF, WebVidQA, DiDeMo |
| Video-Text | Instruction | 85K | ShareGPT4Video |

### Main Results

论文主表强调 LongVU 在 open-source video MLLMs 中的优势。下表保留 source table 的 author-marked bold。

| Group | Method | Size | Context Length | #Frames | EgoSchema | MVBench | MLVU | VideoMME Overall | VideoMME Long |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Proprietary | GPT4-V | - | - | 1fps | 55.6 | 43.7 | - | 60.7 | 56.9 |
| Proprietary | GPT4-o | - | - | 1fps | 72.2 | 64.6 | 66.2 | 77.2 | 72.1 |
| Open-Source | Video-LLaVA | 7B | 4k | 8 | 38.4 | 41.0 | 47.3 | 40.4 | 38.1 |
| Open-Source | LLaMA-VID | 7B | 4k | 1fps | 38.5 | 41.9 | 33.2 | - | - |
| Open-Source | Chat-UniVi | 7B | 4k | 64 | - | - | - | 45.9 | 41.8 |
| Open-Source | ShareGPT4Video | 8B | 8k | 16 | - | 51.2 | 46.4 | 43.6 | 37.9 |
| Open-Source | LLaVA-NeXT-Video | 7B | 8k | 32 | 43.9 | 33.7 | - | 46.5 | - |
| Open-Source | VideoLLaMA2 | 7B | 8k | 32 | 51.7 | 54.6 | 48.5 | 46.6 | 43.8 |
| Open-Source | LongVA | 7B | 224k | 128 | - | - | 56.3 | 54.3 | 47.6 |
| Open-Source | VideoChat2 | 7B | 8k | 16 | 54.4 | 60.4 | 47.9 | 54.6 | 39.2 |
| Open-Source | LLaVA-OneVision | 7B | 8k | 32 | 60.1 | 56.7 | 64.7 | 58.2 | 46.7 |
| Open-Source | **LongVU (Ours)** | 7B | 8k | 1fps | **67.6** | **66.9** | **65.4** | **60.6** | **59.5** |

注意：正文主表报告 LongVU 的 VideoMME Overall 为 `60.6`，而补充材料中的 VideoMME comparison table 与 STC strategy table 报告为 `60.9`。此处按各 source table 原样保留，不对差异做推断性修正。

### Small Model Results

| Method | Base / Size | EgoSchema | MVBench | VideoMME Overall | VideoMME Long | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| InternVL2 | InternLM2-1.8B | - | 60.2 | 47.3 | 42.6 | - |
| VideoChat2 | Phi-3-mini-4B | 56.7 | 55.1 | - | - | - |
| Phi-3.5-vision-instruct | Phi-3-mini-4B | - | - | 50.8 | 43.8 | - |
| **LongVU (Ours)** | Llama3.2-3B | **59.1** | **60.9** | **51.5** | **47.2** | 55.9 |

### Ablations / Analysis

#### Compression Components

| Methods | Context Length | #Tokens | EgoSchema | VideoMME | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Uniform | 16k | 144 | 67.12 | 60.01 | 64.70 |
| DINO | 16k | 144 | 67.34 | 61.25 | 64.83 |
| Uniform | 8k | 64 | 66.84 | 57.56 | 60.87 |
| Uniform | 8k | 144 | 66.28 | 58.84 | 63.28 |
| SigLIP | 8k | 64 | 66.04 | 58.63 | 62.17 |
| DINO | 8k | 64 | 66.20 | 59.90 | 62.54 |
| DINO + Query | 8k | 64/144 | 67.30 | 60.08 | 65.05 |
| DINO + Query + STC (default) | 8k | dynamic | **67.62** | **60.56** | **65.44** |

#### MLVU Subtasks

| Strategy | count | ego | needle | order | plotQA | anomaly | reasoning | Avg |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| DINO | 24.15 | 59.09 | 68.16 | 52.89 | 71.24 | 74.00 | 86.36 | 62.54 |
| DINO+Query | 28.98 | 55.39 | **78.87** | 56.37 | **72.35** | 75.50 | **87.87** | 65.05 |
| DINO+Query+STC (default) | **28.98** | **59.37** | 76.33 | **58.30** | 71.61 | **76.00** | 87.50 | **65.44** |

#### STC Anchor Strategy on VideoMME

| Model | Short | Medium | Long | Overall | Reduction rate |
| ---- | ---- | ---- | ---- | ---- | ---- |
| $1^{st}$ frame in sliding window (default) | 64.7 | 58.2 | 59.5 | 60.9 | 55.47% |
| $(K/2)^{th}$ frame in sliding window | 64.7 | 58.7 | 58.6 | 60.7 | 54.97% |
| Frame with high changes | 64.7 | 58.2 | 58.3 | 60.4 | 55.62% |

作者结论是第一帧 anchor 的策略性能略好，并且 reduction rate 与其他策略接近，因此默认采用最简单的 first-frame strategy。

#### Frame-level Position Encoding

| Methods | Context Length | #Tokens | EgoSchema | VideoMME | MLVU |
| ---- | ---- | ---- | ---- | ---- | ---- |
| DINO + Query | 8k | 64/144 | 67.30 | 60.08 | 65.05 |
| DINO + Query + STC (default) | 8k | dynamic | 67.62 | 60.56 | 65.44 |
| DINO + Query + STC + FPE | 8k | dynamic | 67.87 | 60.89 | 64.56 |

FPE 对 EgoSchema 和 VideoMME 有小幅提升，但 MLVU 下降；作者因此没有把 frame-level position encoding 放入默认设置。

#### Compression Statistics and Needle Test

| Analysis | Reported Observation |
| ---- | ---- |
| Temporal frame reduction | 平均保留约 $45.9\%$ frames |
| Spatial token compression | 平均减少约 $40.4\%$ tokens |
| Needle-in-a-Haystack | adaptive token compression 将 hour-long video 中定位 needle frame 的平均分数从 0.80 提升到 0.88 |

## Limitations & Caveats

1. **Image understanding regression**  
   论文明确指出 video SFT stage 只用 video-only data，导致 image understanding benchmark 下降。

   | Setting | SQA-IMG | MMVP | POPE | RealWorldQA |
   | ---- | ---- | ---- | ---- | ---- |
   | Before video SFT | 95.44 | 51.33 | 86.65 | 61.06 |
   | After video SFT | 83.94 | 32.00 | 81.23 | 47.65 |

2. **Training cost high**  
   默认训练使用 64 NVIDIA H100 GPUs。虽然 inference-side token compression 很有价值，但完整复现训练并不轻量。

3. **Temporal reduction 的精确 selection threshold 未充分展开**  
   论文描述用 DINOv2 similarity 在 $J=8$ window 中移除 high-similarity frames，但没有在正文中给出所有实现细节，例如 exact threshold 或 ranking rule。复现时需要查代码确认。

4. **Query-aware selection 依赖问题质量**  
   LongVU 的 selective high-resolution retention 与 text query 强相关。若 query 很模糊、多意图、或 multi-turn context 中 query representation 不稳定，可能影响帧选择质量。这是基于方法机制的实现风险，论文未专门系统评估。

5. **Compression 假设视频存在可利用冗余**  
   STC 假设相邻或窗口内帧存在大量 static background / pixel-level redundancy。快速运动、镜头切换密集、或细粒度局部事件可能对 token pruning 更敏感。

## Concrete Implementation Ideas

1. 把 LongVU 的 compression pipeline 做成独立 video preprocessor：输入视频和 query，输出按时间戳排列的 high-res / low-res / pruned token plan，方便接入不同 Video-LLM。
2. 在现有 MLLM inference 里先实现 DINOv2 temporal reduction，作为最小可复现版本；先记录被删除帧的 timestamp，方便 debug 误删关键帧。
3. 做一个 token budget scheduler：给定 $L_{\text{max}}$、query length、system prompt length、frame count，自动计算 $N_h$、low-res frame budget 和是否触发 STC。
4. 用 VideoMME Long、MLVU needle/order/count subtasks 做 regression suite，因为这些 task 更能暴露 long-context 和 temporal reasoning 失误。
5. 若要继续训练模型，可混入 image / multi-image replay data，避免论文中观察到的 video SFT 后 image benchmark regression。

## Open Questions / Follow-ups

1. DINOv2 temporal reduction 的 exact frame removal rule 在代码里如何实现？是否是固定比例、固定 threshold，还是 window 内排序删除？
2. 对 1-hour 1fps 视频，DINOv2 + SigLIP 双 encoder 的 inference latency 和显存开销是多少？论文主表更强调 accuracy，没有给出完整吞吐分析。
3. Query-aware selection 是否能支持 multi-turn video chat？如果后续问题变化，是否需要重新计算 frame selection？
4. STC 的 first-frame anchor 在高运动场景、镜头切换密集场景中是否会误剪关键 token？
5. LongVU 与更长 context LLM 结合时，最优策略是少压缩保真，还是继续压缩以扩大 frame coverage？

## Citation

```bibtex
@article{shen2024longvu,
  title={LongVU: Spatiotemporal Adaptive Compression for Long Video-Language Understanding},
  author={Shen, Xiaoqian and Xiong, Yunyang and Zhao, Changsheng and Wu, Lemeng and Chen, Jun and Zhu, Chenchen and Liu, Zechun and Xiao, Fanyi and Varadarajan, Balakrishnan and Bordes, Florian and Liu, Zhuang and Xu, Hu and Kim, Hyunwoo J. and Soran, Bilge and Krishnamoorthi, Raghuraman and Elhoseiny, Mohamed and Chandra, Vikas},
  journal={arXiv preprint arXiv:2410.17434},
  year={2024}
}
```
