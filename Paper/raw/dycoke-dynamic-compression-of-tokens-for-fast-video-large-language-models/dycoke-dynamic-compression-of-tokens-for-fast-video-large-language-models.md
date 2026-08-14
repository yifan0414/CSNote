---
title: DyCoke(token)
authors:
  - Keda Tao
  - Can Qin
  - Haoxuan You
  - Yang Sui
  - Huan Wang
conference: CVPR 2025
year: 2024
arxiv_url: https://arxiv.org/abs/2411.15024
pdf_link: "[[assets/paper_2411.15024.pdf]]"
cover: "[[assets/pipeline_2411.15024.png]]"
updated: 2026-05-26
tags:
  - paper/arxiv
  - video-llm
  - long-video
  - token-pruning
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/KD-TAO/DyCoke
---

## TL;DR

- DyCoke 是面向 Video Large Language Models (VLLMs) 的 training-free、plug-and-play visual token 压缩方法，目标是在不微调模型的前提下降低长视频推理成本。
- 核心观察是：生成不同输出 token 时，模型关注的视频 token 会变化；因此 image-LLM 中常见的 one-shot pruning 容易过早删除之后仍重要的信息。
- 方法分两阶段：prefilling 时用 Token Temporal Merging (TTM) 合并跨帧冗余 token；decoding 时用 dynamic KV cache pruning 与 DP cache 动态保留或召回关键 token。
- 在 LLaVA-OV-7B、32 帧 MVBench 上，DyCoke ($K=0.7$) 报告 59.56 accuracy、1.49 s/example，相对 Full Tokens 的 58.81 与 2.30 s/example 达到 $1.54\times$ speedup，并将 GPU memory 从 34G 降至 24G。
- 代价边界很清晰：极强压缩会破坏表现，且快速场景切换或关键时刻变化仍可能造成信息损失。

## Key Contributions

1. 提出面向 VLLMs 的 temporal-spatial dynamic token compression：将视频中的 temporal redundancy 与解码期间变化的 spatial attention 分开处理。
2. 引入轻量 TTM 模块，在 4-frame sliding window 内基于 cosine similarity 合并相似视觉 token；论文报告 32 帧输入的 TTM 处理时间小于 $10^{-3}$ 秒。
3. 引入 dynamic KV cache pruning 与 DP cache：不是永久丢弃低注意力 token，而是在后续解码中允许重新评估并召回。
4. 在三种 LLaVA-OneVision 尺度与多个视频 QA / description benchmark 上验证 training-free 推理加速、内存降低与性能保持能力。

## Method

给定 $M_v$ 帧视频，每帧经视觉编码器与 projector 产生 $N_v$ 个 visual tokens；实验默认 $N_v=196$。原始输入为

$$
H=\operatorname{concat}[H_{v'}, H_q].
$$

DyCoke 的处理流程如下：

1. **Prefilling / TTM**：将连续视频 token 按 4 帧窗口分组为 Odd 与 Even frames，使用

   $$
   \mathcal{S}(h_i,h_j)=\frac{h_i\cdot h_j}{\lVert h_i\rVert\lVert h_j\rVert}
   $$

   衡量对应 token 的相似度，并按第一阶段 pruning rate $K$ 合并高度相似的跨帧 token，得到 $\operatorname{TTM}(H_{v'})$。

2. **Compressed input**：向 LLM 输入

   $$
   H=\operatorname{concat}[\operatorname{TTM}(H_{v'}), H_q].
   $$

3. **Decoding / attention evaluation**：在指定 transformer layer $L$，按当前预测 token 与 visual keys 的注意力评分识别重要 visual tokens：

   $$
   \mathbf{A}^{(L)}=\operatorname{Softmax}\left(\frac{\mathbf{Q}^{(L)}(\mathbf{K}^{(L)})^\top}{\sqrt{D}}\right).
   $$

4. **Dynamic pruning**：第二阶段由 $P$ 控制 pruning；高注意力 token 保持在 KV cache，当前低重要度 token 放入 DP cache，而不是不可逆删除。
5. **Refocus / restore**：当后续 decoding iteration 的关注分布发生变化，模型重新评估并把 DP cache 中重新重要的 token 换回 KV cache，同时移出已不重要的 token。

主要比较设置为 $L=3$、$P=0.7$，并改变 $K$。论文强调该方案不增加训练参数，也不需要 fine-tuning。

## Pipeline Figure

![[assets/pipeline_2411.15024.png]]

Caption: **Detailed overview of our DyCoke method.** DyCoke 通过两阶段压缩 visual tokens：左侧为 prefilling 阶段的 visual token temporal merging (TTM)，右侧为 decoding 阶段的 KV cache dynamic pruning；后者利用 DP cache 动态交换当前重要和不重要的 tokens。

Source: TeX `\includegraphics` from `sec/3_Med.tex` (`Images/method_final.pdf`); PNG rendered from the PDF CropBox at 250 DPI.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split / Protocol | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| ActivityNet-QA (ActNet-QA) | Action-related VideoQA | Generated single-word responses | Acc.; GPT-4o-mini score (0-5) | LMMs-Eval |
| NeXTQA | VideoQA | `mc` | Accuracy | LMMs-Eval |
| PerceptionTest | Video perception | `val` | Accuracy | LMMs-Eval |
| VideoDetailCaption (VideoDC) | Detailed video description | `test` | GPT-4o-mini score; decoding latency | Long-form output |
| VideoMME | Multi-domain, multi-duration VideoQA | `wo`, `w-subs` | Accuracy | Includes short / medium / long analysis |
| MVBench | Multi-choice temporal video understanding | 20 tasks, 200 samples/task | Accuracy; latency; GPU memory | Official evaluation code; averages over multiple experiments |

### Main Results

以下表格保留论文表 1 中作者对 token pruning methods 标注的 **best** 与 <u>second best</u>；Full Tokens 是未压缩参照，不参与该标注规则。

**LLaVA-OV-7B: video QA and description benchmarks**

| Method | Retained Ratio | FLOPs (T) | FLOPs Ratio | ActNet-QA Acc. | ActNet-QA Sco. | NeXTQA mc | PercepTest val | VideoDC test | VideoMME wo | VideoMME w-subs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Full Tokens | 100% | 41.4 | 100% | 51.93 | 2.86 | 79.4 | 57.1 | 3.30 | 58.5 | 61.3 |
| FastV | 35% | 17.9 | 43% | 50.93 | 2.80 | 78.2 | 56.7 | 3.09 | 57.3 | 60.5 |
| PruMerge | 55% | 21.1 | 51% | 50.45 | 2.78 | 76.0 | 54.3 | 2.88 | 52.9 | 57.0 |
| DyCoke ($K=0.3,L=3,P=0.7$) | 23.25% | 30.8 | 75% | <u>51.80</u> | <u>2.85</u> | **79.1** | <u>57.2</u> | 3.19 | <u>58.8</u> | <u>61.0</u> |
| DyCoke ($K=0.5,L=3,P=0.7$) | 18.75% | 24.1 | 59% | **52.08** | **2.88** | <u>78.5</u> | **57.6** | **3.29** | **59.5** | **61.4** |
| DyCoke ($K=0.7,L=3,P=0.7$) | 14.25% | 17.9 | 43% | <u>51.80</u> | <u>2.85</u> | 78.2 | **57.6** | <u>3.20</u> | 58.3 | 60.7 |

**Scale check: representative $K=0.5$ DyCoke setting versus Full Tokens**

| Model | Method | Retained Ratio | FLOPs (T) | ActNet-QA Acc. | NeXTQA mc | PercepTest val | VideoDC test | VideoMME wo | VideoMME w-subs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OV-0.5B | Full Tokens | 100% | 3.4 | 47.93 | 57.2 | 49.1 | 2.86 | 44.1 | 43.5 |
| LLaVA-OV-0.5B | DyCoke ($K=0.5,L=3,P=0.7$) | 18.75% | 1.8 | <u>47.80</u> | <u>57.2</u> | **49.5** | <u>2.62</u> | 45.1 | <u>43.4</u> |
| LLaVA-OV-72B | Full Tokens | 100% | 436.1 | 52.96 | 80.2 | 66.9 | 3.34 | 66.2 | 69.5 |
| LLaVA-OV-72B | DyCoke ($K=0.5,L=3,P=0.7$) | 18.75% | 262.5 | **52.81** | **79.1** | **60.2** | **3.35** | **66.3** | **69.7** |

在 72B 表格中，粗体仍表示压缩方法间最优，而不是相对 Full Tokens 的绝对最优；例如 PercepTest 上 Full Tokens 的 66.9 高于 DyCoke 的 60.2。

**MVBench average accuracy**

| Input Frames | Method | FLOPs Ratio (FR) | Avg. Accuracy |
| ---: | --- | ---: | ---: |
| 16 | Full Tokens | 100% | 58.0 |
| 16 | PruMerge | 51% | 52.6 |
| 16 | FastV | 43% | 56.1 |
| 16 | DyCoke ($K=0.5$) | 59% | **58.0** |
| 16 | DyCoke ($K=0.7$) | 43% | <u>57.5</u> |
| 32 | Full Tokens | 100% | 58.8 |
| 32 | PruMerge | 51% | 53.9 |
| 32 | FastV | 43% | 58.4 |
| 32 | DyCoke ($K=0.5$) | 59% | <u>59.1</u> |
| 32 | DyCoke ($K=0.7$) | 43% | **59.6** |

**Actual inference efficiency on MVBench, LLaVA-OV-7B, 32 frames**

| Method | Total Latency | GPU Mem. | Accuracy | Latency / Example |
| --- | ---: | ---: | ---: | ---: |
| Full Tokens | 2:33:30 | 34G | 58.81 ($\pm 0.14$) | 2.30 s ($1.00\times$) |
| PruMerge | 3:48:59 | 28G | 53.93 ($\pm 0.06$) | 3.43 s ($0.64\times$) |
| FastV | 1:55:20 | <u>30G</u> | 58.36 ($\pm 0.09$) | 1.73 s ($1.32\times$) |
| DyCoke ($K=0.5$) | <u>1:53:17</u> | 28G | <u>59.09 ($\pm 0.23$)</u> | <u>1.69 s ($1.36\times$)</u> |
| DyCoke ($K=0.7$) | **1:39:49** | **24G** | **59.56 ($\pm 0.19$)** | **1.49 s ($1.54\times$)** |

**VideoDC long-form generation latency, LLaVA-OV-7B, 32 frames**

| Method | Decoding Latency | VideoDC Acc. |
| --- | ---: | ---: |
| Full Tokens | 42 ms/token | 3.30 |
| DyCoke ($K=0.5$) | 35 ms/token | 3.29 |
| DyCoke ($K=0.7$) | 31 ms/token | 3.20 |

**VideoMME cost-effectiveness**

| Method | FLOPs | Input Frames | Short Video Acc. | Medium Video Acc. | Long Video Acc. | Avg. Acc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full Token | 18.99T | 16 | 67.9 | 52.8 | 47.9 | 56.2 |
| DyCoke | 17.91T | 32 | 71.0 | 55.6 | 48.3 | 58.3 |
| Full Token | 41.40T | 32 | 71.0 | 55.0 | 49.7 | 58.5 |

### Ablations / Analysis

**LLaVA-OV-7B ablation: dynamic pruning and compression strength**

| Variant / Setting | $K$ | $L$ | $P$ | Retained Ratio | ActNet-QA Acc. | NeXTQA mc | PercepTest val | VideoDC test | VideoMME wo | VideoMME w-subs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Full Tokens | - | - | - | 100% | 51.93 | 79.4 | 57.1 | 3.30 | 58.5 | 61.3 |
| w/o DP | 0.7 | 3 | 0.7 | 14.25% | 51.06 | 77.2 | 56.6 | 3.01 | 58.1 | 60.2 |
| Random Pruning | 0.7 | 3 | 0.7 | 14.25% | 50.90 | 77.9 | 56.4 | 2.98 | 55.8 | 59.3 |
| DyCoke | 0.7 | 3 | 0.7 | 14.25% | 51.80 | 78.2 | 57.6 | 3.20 | 58.3 | 60.7 |
| DyCoke | 0.7 | 10 | 0.7 | 14.25% | 51.81 | 78.2 | 57.5 | 3.20 | 58.4 | 60.7 |
| DyCoke | 0.7 | 3 | 0.9 | 4.75% | 51.48 | 78.2 | 57.5 | 2.86 | 58.3 | 60.7 |
| DyCoke (over-pruned) | 0.9 | 0 | 0.9 | 3.25% | 40.21 | 79.1 | 57.4 | 2.76 | 57.8 | 60.1 |

消融结果显示：在相同 14.25% retained ratio 下，DyCoke 相比 `w/o DP` 尤其改善 VideoDC (`3.20` vs. `3.01`)；用 random pruning 替代 TTM 的相似度选择会在多数任务上进一步退化。极端 3.25% retained ratio 使 ActNet-QA accuracy 从 `51.80` 急跌到 `40.21`。

### Training / Compute

| Item | Value |
| --- | --- |
| Backbone models | LLaVA-OneVision-0.5B, LLaVA-OneVision-7B, LLaVA-OneVision-72B |
| Hardware | RTX 4090 (0.5B), A6000 (7B), A100 (72B) |
| Framework | PyTorch |
| Default video input | 32 frames, $N_v=196$ tokens/frame unless otherwise stated |
| DyCoke comparison setting | $L=3$, $P=0.7$; $K$ varied |
| Compared pruning methods | FastV and LLaVA-PruMerge, both training-free |
| Fairness metric | Total calculated FLOPs; supplementary FLOPs calculation uses $R=100$ decoding iterations |

| Model | Hidden Size $d$ | FFN Size $m$ | Layers $T$ | Tokens / Frame |
| --- | ---: | ---: | ---: | ---: |
| LLaVA-OV-0.5B | 896 | 4,864 | 24 | 196 |
| LLaVA-OV-7B | 3,584 | 18,944 | 28 | 196 |
| LLaVA-OV-72B | 8,192 | 29,568 | 80 | 196 |

论文仅进行 inference-time compression，不报告新训练过程或额外训练算力。其 FLOPs 比较采用：

$$
\begin{aligned}
\operatorname{FLOPs} &= T(4nd^2+2n^2d+2ndm) \\
&\quad + TR\left((4d^2+2dm)+2\left(dn+\frac{d(R+1)}{2}\right)\right),
\end{aligned}
$$

其中 $R=100$ 用于统一估算 decoding iterations。作者也明确指出 FLOPs 是 token computation 的公平比较指标，而不直接等同于实际 latency。

## Limitations & Caveats

- 作者在 supplementary future work 中指出，rapid scene changes 或 critical time shifts 等视频内容仍可能因压缩导致少量信息损失；dynamic selection 只能缓解而不能消除该问题。
- 压缩强度必须针对输入冗余调整：少帧视频的 redundancy 较低，论文的补充分析观察到压缩更可能降低性能；极强 pruning 在 ActNet-QA 上有明显失败案例。
- 论文主要在 LLaVA-OneVision 系列与 training-free baselines 上验证；其动态缓存策略迁移到不同 VLLM 架构、Flash Attention 实现或更长生成任务时仍需要独立测试。
- 虽然 token compression 降低 memory 与 latency，作者认为仅凭该方法仍不足以让大模型完整部署到移动设备，后续需结合 quantization 或 distillation。

## Concrete Implementation Ideas

1. 在现有 LLaVA-OneVision inference path 中先实现纯 inference hook：prefilling 后插入 4-frame TTM，并将 $K$, $L$, $P$ 设计为可配置参数，以复现实验中 $K=0.5/0.7$, $L=3$, $P=0.7$ 的工作点。
2. 将 KV cache 拆为 active visual KV 与 DP cache 两个 buffer，记录每次 token swap 的 index、attention score 与 latency；首先用 MVBench 单-token 输出验证动态交换的准确性与加速收益。
3. 增加根据视频 temporal change 自动调整 $K$ 的策略：用帧间 embedding similarity 或 scene-cut signal 避免在快速场景切换视频中过度 TTM。
4. 对长文本生成任务单独 profile decoding：比较 Full Tokens、one-shot pruning 与 DyCoke 的 ms/token、peak memory 和输出质量，以验证 DP cache 对持续生成的必要性。

## Open Questions / Follow-ups

- 论文何时触发 DP cache 的重新评估只描述为跨 iteration attention distribution 的低相似度；实际阈值、更新频率与其 latency trade-off 需要从代码或复现实验中确认。
- 当 video 中存在短暂但决定答案的稀有事件时，TTM 是否会在 decoding 动态召回之前就于 prefilling 阶段不可逆地合并掉关键信息？
- 对 Flash Attention 或 paged KV cache serving 后端，获取中间层 attention 与执行动态 token index update 的工程成本是否会抵消部分 speedup？
- 在与 quantization、distillation、frame selection 联合使用时，DyCoke 的最优 $K/P$ 是否需要重新标定？

## Citation

最新 arXiv 版本为 v3，修订日期为 2025-03-28；论文页面未列出正式会议或期刊发表信息。

```bibtex
@misc{tao2024dycoke,
  title         = {DyCoke: Dynamic Compression of Tokens for Fast Video Large Language Models},
  author        = {Tao, Keda and Qin, Can and You, Haoxuan and Sui, Yang and Wang, Huan},
  year          = {2024},
  eprint        = {2411.15024},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV},
  url           = {https://arxiv.org/abs/2411.15024}
}
```
