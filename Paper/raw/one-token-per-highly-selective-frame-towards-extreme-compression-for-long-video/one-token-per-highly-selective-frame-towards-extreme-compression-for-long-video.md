---
title: "One Token per Highly Selective Frame: Towards Extreme Compression for Long Video Understanding"
authors:
  - Zheyu Zhang
  - Ziqi Pang
  - Shixing Chen
  - Xiang Hao
  - Vimal Bhat
  - Yu-Xiong Wang
conference:
year: 2026
arxiv_url: https://arxiv.org/abs/2604.14149
pdf_link: "[[assets/paper_2604.14149.pdf]]"
cover: "[[assets/pipeline_2604.14149.png]]"
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
priority: "1"
rating: "3"
topics:
  - Video Understanding
code: https://github.com/ZheyuAqaZhang/XComp
---

## TL;DR

- 这篇论文提出 **XComp**：在 long video VLM 里把 token-level compression 推到接近“每个被选中帧只保留 1 个 token”的极限，同时再用 frame-level selection 只保留和问题最相关的帧。
- **LP-Comp** 不是 training-free heuristic，而是通过 **supervised compression tuning (SCT)** 让 LLM layer 学会逐层、渐进地压缩视觉 token；核心设计是 suffix-preservation，适配 decoder-only LLM 的 causal attention。
- **QC-Comp** 在推理时用 question token 与 video token 的内部 attention score 给帧打分，并用 segmented local attention 缓解长上下文里的 position bias / lost-in-the-middle。
- 在 VideoChat-Flash-2B 上，XComp 只用 VideoChat-Flash SFT 数据的 2.5% 做 SCT，却把 LVBench 从 42.9 提到 46.2，把 LongVideoBench 从 58.3 提到 59.7。
- 效率上，在 LVBench query 的 1k-4k frames 设置中，论文报告 XComp 降低 LLM TFLOPs 约 53%-58%，latency 降低约 45%-58%。

## Key Contributions

1. **Learnable token compression**：指出极高压缩比下，单纯依赖 attention/token selection/pooling 这类 heuristic 会丢信息；因此让 LLM layer 在继续训练中学习“把被删 token 的上下文压进保留 token”。
2. **Progressive compression schedule**：不用某几层突然砍 token，而是按 cosine schedule 在所有 LLM layers 中平滑压缩，最终达到每帧 1 token。
3. **Question-conditioned frame compression**：用 query-video internal attention 选择相关帧，并把全局长序列注意力改成分段局部注意力，减少开头/结尾 bias 对中间关键帧的压制。
4. **Data-efficient SCT**：基于 VideoChat-Flash-2B，用 71,927 个样本，也就是 VideoChat-Flash SFT 数据的 2.5%，完成压缩能力适配。
5. **跨 backbone 初步验证**：在 LLaVA-Next-Video 上也报告了 XComp 的收益，说明设计不完全绑定于 VideoChat-Flash。

## Method

**Backbone and token flow**

- Backbone：VideoChat-Flash-2B。
- Visual encoder：UMT-L。
- Connector：token merging 后接 two-layer MLP，把视觉 token 投到 LLM hidden space。
- LLM：Qwen2-1.5B。
- 视频先切成 8-frame clips；每个 clip 压成 128 visual tokens，平均每帧 16 tokens。
- LP-Comp 在 LLM layers 内继续压缩 token；QC-Comp 在推理阶段选择更相关的帧。

**LP-Comp: Learnable & Progressive Compression**

目标是从初始每帧 $N^{(1)}=16$ 个 visual tokens，逐层压到最终 $N^{(L)}=1$。论文采用 cosine schedule：

$$
N^{(\ell)} =
\left\lceil
\frac{N^{(1)}-1}{2}\cos\left(\frac{\ell}{L}\pi\right)
+\frac{N^{(1)}+1}{2}
\right\rceil,\quad \ell=1,\dots,L.
$$

当某层需要从 $N^{(\ell)}$ 压到 $N^{(\ell+1)}$ 时，它保留每帧的 suffix tokens，删除前面的 token。直觉是 decoder-only LLM 的 causal attention 允许后面的 token 吸收前面 token 的信息，反过来则不自然。

**QC-Comp: Question-Conditioned Frame Compression**

QC-Comp 只在 inference 使用。它用 LLM 内部 attention map 衡量 query tokens 与 video tokens 的相关性，再选择 top-k frames。为了避免长视频中 attention 偏向序列开头和结尾，论文不用全局 attention 直接打分，而是把视频切成局部 segment：

- segment length：64 frames；
- stride：32 frames；
- 每个 segment 独立计算 query-video attention；
- 同一帧出现在多个 segment/chunk 时，对相关性分数做聚合；
- 最后保留 $n_{\mathrm{selected\_frames}}$ 个高分帧进入回答生成。

```text
Encode video into 8-frame clips.
Merge each clip to 128 visual tokens, then project into LLM space.
For each LLM layer:
  run normal transformer layer over video + query tokens
  apply LP-Comp according to the cosine token schedule
  optionally collect query-to-video attention for QC-Comp scoring
During inference:
  score frames with segmented local attention
  keep top-ranked frames
  run the final answer generation on the selected frames
```

## Pipeline Figure

![[assets/pipeline_2604.14149.png]]

Caption: 该 overview 图展示 XComp 的两个压缩维度：token-level 的 LP-Comp 通过 supervised compression tuning 让 LLM layer 学习渐进压缩；frame-level 的 QC-Comp 用 question-conditioned relevance 选择相关帧。两者合起来实现 “one token per highly selective frame”。

Source: TeX `\includegraphics` in `secs/3_method_v2.tex`, source asset `figs/slides_with_pdf/overview-v2.pdf`; rendered to PNG with `pdftoppm -cropbox -r 250`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| LongVideoBench | Long video QA | not reported; average duration 473s | Accuracy | 主结果与 QC/LP ablation 都使用。 |
| MLVU | Long video QA | not reported; average duration 651s | Accuracy | 主结果与 attention ablation 使用。 |
| VideoMME (Long) | Long video QA | Long subset; w/o subtitles; average duration 2386s | Accuracy | 主结果与 attention ablation 使用。 |
| LVBench | Extreme long video QA | not reported; average duration 4101s | Accuracy | 论文最强调的长视频 benchmark 之一。 |
| VideoChat-Flash SFT mixture | SCT training data | 71,927 instances; 2.5% of VideoChat-Flash SFT data | Training loss not reported | 来自 publicly available image/video instruction datasets。 |
| CLEVRER | Video reasoning | not reported | Expl/Pred/Cntrf metrics | 作为补充实验，检查压缩是否伤害基础 reasoning。 |
| VDC | Video captioning | not reported | BLEU@1, BLEU@4 | 作为补充 dense-output 任务。 |
| MME-VideoOCR | Video OCR | Overall and >30s subset | Benchmark score | 检查细粒度文本感知能力。 |
| Multi-Hop NIAH | Long-context video QA | 2,000-10,000 total frames; sequence length 6,144 for keyframe selection | Keyframe selection acc.; QA average acc. | 检查极长上下文中的 needle retrieval。 |

### Main Results

Average duration in the main table: LongVideoBench 473s, MLVU 651s, VideoMME (Long) 2386s, LVBench 4101s. Higher is better. 粗体保留论文原表内的 best 标注；不同规模与 proprietary/open-source 组之间不应直接等价比较。

| Group | Method | Size | LongVideoBench | MLVU | VideoMME (Long) | LVBench |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Proprietary | GPT-4V | - | 59.1 | 49.2 | 53.5 | -- |
| Proprietary | GPT-4o | - | **66.7** | **64.6** | 65.3 | 30.8 |
| Proprietary | Gemini-1.5-Pro | - | 64.0 | -- | **67.4** | **33.1** |
| 3-9B VLMs | Qwen2.5VL-3B | 3B | 43.3 | 68.2 | -- | -- |
| 3-9B VLMs | mPLUG-Owl3 | 7B | 52.1 | -- | 50.1 | 43.5 |
| 3-9B VLMs | VideoChat-Flash-7B | 7B | 64.7 | 74.7 | **55.4** | **48.2** |
| 3-9B VLMs | Eagle2.5-8B | 8B | **66.4** | **77.6** | -- | -- |
| 3-9B VLMs | Kangaroo | 8B | 54.8 | 61.0 | 46.7 | 39.4 |
| 3-9B VLMs | TimeMarker | 8B | 56.3 | -- | 46.4 | 41.3 |
| 3-9B VLMs | InternVL3-9B | 9B | 62.5 | 70.8 | -- | -- |
| 2B VLMs | InternVL3-2B | 2B | 55.4 | 64.2 | -- | -- |
| 2B VLMs | VideoChat-Flash-2B | 2B | 58.3 | 65.7 | 44.9 | 42.9 |
| 2B VLMs | XComp | 2B | **59.7** | **66.7** | **45.6** | **46.2** |

### Ablations / Analysis

**LP-Comp: learnable vs. training-free, progressive vs. step-wise.** 该表使用 LVBench，1024 frames。Higher is better。

| Method | Training-free | Learnable |
| --- | ---: | ---: |
| Baseline (w/o compression) | 41.8 | - |
| + Heuristic | 41.1 | - |
| + Step-wise | 38.4 | 42.3 |
| + Progressive | 39.7 | **44.3** |

**Suffix-preservation vs. uniform drop.** 两者使用相同 cosine compression schedule 与 continual training。Higher is better。

| Strategy | LVBench | MLVU |
| --- | ---: | ---: |
| Uniform | 43.6 | 64.1 |
| Suffix | **44.3** | **65.2** |

**QC-Comp attention scoring.** Segment-wise local attention 比 global attention 略好，支持论文关于 position bias 的动机。Higher is better。

| Attention | LongVideoBench | MLVU | VideoMME (Long) |
| --- | ---: | ---: | ---: |
| Global | 59.5 | 66.3 | 44.8 |
| Segment Local (Ours) | **59.7** | **66.7** | **45.7** |

**LP-Comp and QC-Comp combined.** 该表把主要 design choices 放到同一个视角下比较。Higher is better。

| Model Name | LP-Comp | LP Variant | QC-Comp | QC Variant | LongVideoBench | LVBench |
| --- | --- | --- | --- | --- | ---: | ---: |
| VideoChat-Flash | No | - | No | - | 58.3 | 42.9 |
| XComp | Yes | Uniform | No | - | 58.2 | 43.6 |
| XComp | Yes | Suffix | No | - | 58.8 | 44.3 |
| XComp | Yes | Suffix | Yes | Global | 59.5 | 45.6 |
| XComp | Yes | Suffix | Yes | Segment Local | **59.7** | **46.2** |

**Generalization to LLaVA-Next-Video.** 论文用 2.5% LLaVA-Video-178K 训练数据，显示 XComp 不只对 VideoChat-Flash 有效。Higher is better。

| Model Version | VideoMME (Long) | LVBench |
| --- | ---: | ---: |
| LLaVA-Next-Video | 62.7 | 40.6 |
| LLaVA-Next-Video + FT | 61.4 | 41.4 |
| LLaVA-Next-Video + XComp | **63.2** | **43.1** |

**Fine-tuning control.** 单纯用同等 2.5% 数据 fine-tune VideoChat-Flash-2B 并不能解释 XComp 的收益。Higher is better。

| Method | Size | LongVideoBench | MLVU | VideoMME (Long) | LVBench |
| --- | --- | ---: | ---: | ---: | ---: |
| VideoChat-Flash-2B | 2B | 58.3 | 65.7 | 44.9 | 42.9 |
| VideoChat-Flash-2B + FT | 2B | 57.4 | 65.6 | 44.7 | 43.2 |
| XComp | 2B | **59.7** | **66.7** | **45.6** | **46.2** |

**Efficiency on LVBench queries.** 单个 NVIDIA H200，10 runs，query 含 863 text tokens。论文报告的是 inference-stage LLM cost。

| Frames | Model | TFLOPs | Latency |
| ---: | --- | ---: | ---: |
| 1,024 | VideoChat-Flash | 43 | 0.22 s |
| 1,024 | XComp | 20 (**53%↓**) | 0.12 s (**45%↓**) |
| 2,048 | VideoChat-Flash | 132 | 0.54 s |
| 2,048 | XComp | 58 (**56%↓**) | 0.25 s (**54%↓**) |
| 4,096 | VideoChat-Flash | 448 | 1.56 s |
| 4,096 | XComp | 187 (**58%↓**) | 0.66 s (**58%↓**) |

**Additional tasks.** XComp 在 CLEVRER/VDC 上接近 backbone，但 MME-VideoOCR 有一定下降；论文认为主要来自训练数据差异，而不完全是压缩结构本身。

| Model | CLEVRER Expl (Opt) | CLEVRER Expl (Q) | CLEVRER Pred (Opt) | CLEVRER Pred (Q) | CLEVRER Cntrf (Opt) | CLEVRER Cntrf (Q) | VDC BLEU@1 | VDC BLEU@4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VideoChat-Flash-2B | **0.9463** | **0.8497** | **0.7789** | **0.5738** | **0.7775** | **0.4007** | **7.1** | **1.6** |
| XComp | 0.9398 | 0.8406 | 0.7697 | 0.5600 | 0.7625 | 0.3652 | 7.0 | **1.6** |

| Model | MME-VideoOCR (Overall) | MME-VideoOCR (>30s) |
| --- | ---: | ---: |
| VideoChat-Flash-2B | **37.1** | **49.1** |
| VideoChat-Flash-2B + FT | 34.9 | 46.0 |
| XComp | 35.4 | 46.4 |

**Multi-Hop NIAH.** 在 QC-Comp 设置 $n_{\mathrm{selected\_frames}}=1$、$n_{\mathrm{repeat}}=8$ 时，论文报告 sequence length 6,144 下 keyframe selection accuracy 为 65%；在 2,000-10,000 total frames 范围内，VideoChat-Flash+QC-Comp 与 XComp 的 QA average accuracy 分别为 72.6 与 72.2。

### Training / Compute

| Item | Value |
| --- | --- |
| Base model | VideoChat-Flash-2B |
| Visual encoder | UMT-L |
| LLM | Qwen2-1.5B |
| Clip size | 8 frames per clip |
| Tokens before LP-Comp | 128 tokens per 8-frame clip; 16 tokens per frame |
| Final LP-Comp target | 1 token per frame at the final LLM layer |
| SCT data | 71,927 instances, 2.5% of VideoChat-Flash SFT data |
| Training frames | mixture of 128-1024 frames per video |
| Sampling | dynamic FPS, 8 FPS by default |
| Optimizer details reported | learning rate $1\times10^{-5}$, weight decay 0.0, warmup ratio 0.03, cosine scheduler |
| Trainable parts | Large Language Model |
| Training cost | about 24 hours on 8 NVIDIA H100 GPUs |
| QC-Comp segment | 64 frames, stride 32 frames |
| Evaluation decoding | temperature 0.0, do_sample False, num_beams 1 |
| Evaluation repeat | $n_{\mathrm{repeat}}=2$ for main evaluation |
| Selected frames | 256 LongVideoBench, 512 VideoMME, 1024 MLVU, 2048 LVBench |

## Limitations & Caveats

- 实验规模有限：主实验集中在 VideoChat-Flash-2B，另有 LLaVA-Next-Video 验证；更大 VLM、更多 backbone、pre-training 阶段集成仍是 future work。
- 没有多 seed 或统计显著性分析。NeurIPS checklist 中作者明确说明受计算预算限制，没有运行 multiple seeds/statistical analysis。
- QC-Comp 目前是 inference-time selection；论文也把“把 question-conditioned frame selection 纳入训练并 jointly optimize”列为后续方向。
- 对 fine-grained OCR 类任务，XComp 比原始 VideoChat-Flash-2B 低，但略高于同数据 FT baseline；实际部署如果依赖文字细节，需要单独测试。
- 主表中 VideoMME (Long) 的 XComp 数字是 45.6，而 QC attention ablation 表中 Segment Local 是 45.7；引用时建议回查作者代码或最终 camera-ready。
- 代码可访问性有一个小不一致：abstract 写 Code and Model available；checklist 里仍写 planned to release code。当前 GitHub `main` branch 可访问，但复现实验前仍应检查 release/checkpoint 是否完整。

## Concrete Implementation Ideas

1. 在现有 video-LLM pipeline 中先复现 LP-Comp 的 suffix-preserving schedule，只改 LLM layer 间的 visual token slicing，保持 vision encoder/projector 不动，降低集成风险。
2. 把 QC-Comp 做成两阶段 inference：先用低成本 pass 计算 frame/clip scores，再对 top frames 做正常生成；同时缓存 video encoding，避免重复 encoder cost。
3. 为 OCR-heavy 或 fine-grained visual QA 增加 fallback：当问题包含 text/read/sign/subtitle 等关键词时，降低压缩强度或保留更高分辨率/更多 tokens。
4. 做一组 own-domain ablations：global attention vs. segmented local attention、suffix vs. uniform、1/2/4 tokens per frame，确认论文里的趋势是否迁移到你的数据分布。
5. 如果上下文预算允许，可以把 QC-Comp 的 segment score 和 answer confidence 一起 log，建立可视化 debug 面板，检查模型是否真的选中了与问题相关的 frames。

## Open Questions / Follow-ups

- LP-Comp 的“suffix token 吸收信息”在不同 decoder-only LLM、不同 visual token order 下是否稳定？如果 visual token ordering 改变，suffix-preservation 可能需要重新验证。
- SCT 只用 2.5% 数据能有效，是否因为 VideoChat-Flash 已经具备较强压缩先验？从更弱或未做 hierarchical compression 的 backbone 开始是否仍然成立？
- QC-Comp 使用 attention score 作为 relevance proxy，但 attention 是否总是对应视觉证据仍有争议；是否需要加 supervised frame relevance loss？
- 对 OCR、细粒度动作、短暂事件等任务，1 token/frame 的下限在哪里？是否应使用 adaptive per-frame token budget？
- 训练阶段如果把 QC-Comp 纳入 objective，是否会让 frame selection 与 token compression 共同优化，还是会引入不可微 top-k/selection 的训练不稳定？

## Citation

```bibtex
@article{zhang2026one,
  title={One Token per Highly Selective Frame: Towards Extreme Compression for Long Video Understanding},
  author={Zhang, Zheyu and Pang, Ziqi and Chen, Shixing and Hao, Xiang and Bhat, Vimal and Wang, Yu-Xiong},
  journal={arXiv preprint arXiv:2604.14149},
  year={2026},
  url={https://arxiv.org/abs/2604.14149}
}
```
