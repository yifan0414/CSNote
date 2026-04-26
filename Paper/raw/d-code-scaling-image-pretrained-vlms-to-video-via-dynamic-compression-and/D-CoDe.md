---
title: "D-CoDe: Scaling Image-Pretrained VLMs to Video via Dynamic Compression and Question Decomposition"
authors:
  - Yiyang Huang
  - Yizhou Wang
  - Yun Fu
conference: EMNLP 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2510.08818
pdf_link: "[[paper_2510.08818.pdf]]"
cover: "[[pipeline_2510.08818.png]]"
pipeline_figure: assets/pipeline_2510.08818.png
pipeline_caption: D-CoDe 将 dynamic compression 与 question decomposition 串联起来：先用补充帧选择、低价值 token 丢弃和相似 token 合并压缩视频，再把复杂问题拆成 focused sub-questions，用 sub-answers 支持最终回答。
pipeline_source: TeX includegraphics from figs/pipeline.tex -> images/pipeline.pdf; rasterized to PNG with pdftoppm at 250 dpi
updated: 2026-04-26
tags:
  - paper/arxiv
status: unread
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/hukcc/D-CoDe
datasets:
  - NExT-QA
  - EgoSchema
  - IntentQA
  - MSVD-QA
  - MSRVTT-QA
  - TGIF-QA
  - ActivityNet-QA
---

## TL;DR

- 论文关注如何把 <font color="#d83931">image-pretrained</font> VLMs 以 training-free 的方式扩展到 video understanding，核心障碍是 perception bottleneck 与 token overload。
- D-CoDe 包含两个模块：dynamic compression 用内容自适应的 temporal frame selection 与 spatial token pruning/merging 保留关键信息；question decomposition 把原问题拆成 sub-questions，再用 sub-answers 辅助最终回答。
- 方法基于 LLaVA-NeXT 7B，不做额外视频训练；实验使用 RoPE scaling factor 2 将上下文扩展到 8192 tokens。
- 在 Multiple Choice VideoQA 上，D-CoDe 在 NExT-QA、EgoSchema、IntentQA 分别达到 **68.3**、**58.0**、**64.2** accuracy，EgoSchema 上超过 MovieChat+ 1.6 个点。
- 在 Open-Ended VideoQA 中，作者只使用 dynamic compression；D-CoDe 在 MSVD-QA 与 TGIF-QA 达到最高 accuracy，但 MSRVTT-QA 低于 SF-LLaVA 和 TS-LLaVA。
- 代价主要来自 question decomposition：EgoSchema 上从 baseline 的 3.927 s/sample 增至 37.395 s/sample。

## Key Contributions

1. 论文把 image-pretrained VLM 适配视频时的两个关键问题明确化：static compression 容易造成 perception bottleneck，压缩后仍然大量存在的 visual tokens 会造成 token overload。
2. 提出 D-CoDe，一个不需要额外训练的 video adaptation framework，将 dynamic compression 与 question decomposition 组合起来。
3. 在多种 VideoQA benchmarks 上验证方法，尤其在 EgoSchema 这种 long-form egocentric video benchmark 上表现强，显示 question decomposition 对复杂视频理解有帮助。

## Method

D-CoDe 的输入是视频 $\mathcal{V} = \{ I_t \}_{t=1}^{T}$ 与 query $Q$。每帧由 image encoder 提取 visual features $\mathbf{F}_t = \text{VisualEnc}(I_t)$，最后将压缩后的 visual tokens 与问题送入 LLM。

Dynamic compression 分 temporal 与 spatial 两步：

- Temporal supplementary frame selection：先按比例 $\alpha$ uniform sampling，得到粗粒度覆盖；再从未选帧里迭代选择与已选帧平均 CLIP cosine similarity 最低的帧，补充语义差异最大的片段。
- Spatial token pruning：对每个 selected frame 的 visual tokens 计算 $\ell_2$ norm 作为 salience proxy，仅保留 top-$\lfloor \beta M \rfloor$ tokens。
- Spatial token merging：按 activation magnitude 从高到低遍历 token，将 cosine similarity 超过阈值 $\tau$ 的未合并 tokens 聚成 cluster，并平均成代表 token。

Question decomposition 用 `gpt-3.5-turbo-0125` 把原问题 $Q$ 拆成 $\{Q_1, Q_2, \dots, Q_n\}$。每个 sub-question 独立基于共享 visual input 生成 $A_i$，然后把 sub-answers 与原问题一起送回 LLM 生成最终答案：

$$
A_{\text{final}} = \text{LLM}(\mathbf{F}_{\text{final}}, \texttt{Concat}(A_1, \dots, A_n), Q)
$$

Compact pipeline:

```text
1. Uniformly sample floor(alpha * N) frames.
2. Iteratively add supplementary frames with low average CLIP similarity to selected frames.
3. For each selected frame:
   - keep top beta visual tokens by L2 activation magnitude;
   - greedily merge semantically similar tokens above threshold tau.
4. Use a decomposition LLM to generate focused sub-questions.
5. Answer each sub-question with the same compressed visual input.
6. Concatenate sub-answers and answer the original question.
```

Implementation details reported by the paper:

| Item | Value |
| --- | --- |
| Base model | LLaVA-NeXT 7B |
| Training | Training-free adaptation |
| Context extension | RoPE scaling factor 2, context length 8192 |
| Frame resolution | $336 \times 336$ |
| Frame count $N$ | Empirically determined by average video length per dataset |
| Uniform sampling ratio $\alpha$ | 0.85 |
| Token retention ratio $\beta$ | 0.625 |
| Merge threshold $\tau$ | 0.9 |
| Decomposition LLM | `gpt-3.5-turbo-0125` |
| Decomposition temperature $t$ | 0.5 |
| Sub-question count $n$ | Not constrained |
| Compute | Single NVIDIA RTX A6000 GPU |

## Pipeline Figure

![[pipeline_2510.08818.png]]

Caption: D-CoDe 将 dynamic compression 与 question decomposition 串联起来：先用补充帧选择、低价值 token 丢弃和相似 token 合并压缩视频，再把复杂问题拆成 focused sub-questions，用 sub-answers 支持最终回答。

Source: TeX includegraphics from `figs/pipeline.tex` -> `images/pipeline.pdf`; rasterized to PNG with `pdftoppm` at 250 dpi.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| NExT-QA | Multiple Choice VideoQA | not reported | Accuracy | causal and temporal understanding |
| EgoSchema | Multiple Choice VideoQA | not reported | Accuracy | long-form egocentric videos and schema-level interpretation |
| IntentQA | Multiple Choice VideoQA | not reported | Accuracy | intention recognition from subtle cues |
| MSVD-QA | Open-Ended VideoQA | not reported | GPT-Accuracy, GPT-Score 0-5 | short clips based on textual descriptions |
| MSRVTT-QA | Open-Ended VideoQA | not reported | GPT-Accuracy, GPT-Score 0-5 | diverse web videos with complex scenes |
| TGIF-QA | Open-Ended VideoQA | not reported | GPT-Accuracy, GPT-Score 0-5 | repetition counting and state transitions in GIFs |
| ActivityNet-QA / ANet-QA | Open-Ended VideoQA | not reported | GPT-Accuracy, GPT-Score 0-5 | long videos with rich activity semantics |

### Main Results - Multiple Choice VideoQA

| Method | Model / Setting | NExT-QA Acc. (%) | EgoSchema Acc. (%) | IntentQA Acc. (%) |
| --- | --- | ---: | ---: | ---: |
| *Training-Required Methods* |  |  |  |  |
| Video-LLaVA | training-required | 60.5 | 37.0 | N/A |
| Video-LLaMA2 | training-required | N/A | 51.7 | N/A |
| MovieChat+ | training-required | 54.8 | 56.4 | N/A |
| Vista-LLaMA | training-required | 60.7 | N/A | N/A |
| *Training-Free Methods* |  |  |  |  |
| DeepStack-L | training-free | 61.0 | 38.4 | N/A |
| $M^3$ | training-free | 63.1 | 36.8 | 58.8 |
| IG-VLM | training-free | 63.1 | 35.8 | 60.3 |
| SF-LLaVA | training-free | 64.2 | 47.2 | 60.1 |
| TS-LLaVA | training-free | 66.5 | 50.2 | 61.7 |
| **D-CoDe (Ours)** | training-free | **68.3** | **58.0** | **64.2** |

作者强调 EgoSchema 上 D-CoDe 比 second-best training-free method TS-LLaVA 高 7.8 个点，也比 best training-required method MovieChat+ 高 1.6 个点。

### Main Results - Open-Ended VideoQA

表中数值为 Accuracy / GPT-Score。论文说明 open-ended benchmarks 的问题通常更简单，多为 what/who/yes-no，因此此处只应用 dynamic compression，没有使用 question decomposition。

| Method | Model / Setting | MSVD Acc./Score | MSRVTT Acc./Score | TGIF Acc./Score | ANet Acc./Score |
| --- | --- | ---: | ---: | ---: | ---: |
| *Training-Required Methods* |  |  |  |  |  |
| Video-LLaMA | training-required | 51.6/2.5 | 29.6/1.8 | N/A | 12.4/1.1 |
| Video-LLaMA2 | training-required | 70.9/3.8 | N/A | N/A | 50.2/3.3 |
| Video-ChatGPT | training-required | 64.9/3.3 | 49.3/2.8 | 51.4/3.0 | 35.2/2.7 |
| VideoGPT+ | training-required | 72.4/3.9 | 60.6/3.6 | 74.6/4.1 | 50.6/3.6 |
| Video-LLaVA | training-required | 70.7/3.9 | 59.2/3.5 | 70.0/4.0 | 45.3/3.3 |
| MovieChat | training-required | 75.2/3.8 | 52.7/2.6 | N/A | 45.7/3.4 |
| MovieChat+ | training-required | 76.5/3.9 | 53.9/2.7 | N/A | 48.1/3.4 |
| VideoChat | training-required | 56.3/2.8 | 45.0/2.5 | 34.4/2.3 | 26.5/2.2 |
| VideoChat2 | training-required | 70.0/3.9 | 54.1/3.3 | N/A | 49.1/3.3 |
| Vista-LLaMA | training-required | 65.3/3.6 | 60.5/3.3 | N/A | 48.3/3.3 |
| LLaMA-VID | training-required | 69.7/3.7 | 57.7/3.2 | N/A | 47.4/3.3 |
| PLLaVA | training-required | 76.6/4.1 | 62.0/3.5 | 77.5/4.1 | 56.3/3.5 |
| *Training-Free Methods* |  |  |  |  |  |
| FreeVA | training-free | 73.8/4.1 | 60.0/3.5 | N/A | 51.2/3.5 |
| DeepStack-L | training-free | 76.0/4.0 | N/A | N/A | 49.3/3.1 |
| IG-VLM | training-free | 78.8/4.1 | 63.7/3.5 | 73.0/4.0 | 54.3/3.4 |
| SF-LLaVA | training-free | 79.1/4.1 | 65.8/3.6 | 78.7/4.2 | 55.5/3.4 |
| TS-LLaVA | training-free | 79.0/4.1 | 65.1/3.6 | 77.7/4.1 | 56.7/3.4 |
| **D-CoDe (Ours)** | training-free | **80.0/4.1** | **64.2/3.5** | **79.1/4.1** | **56.4/3.4** |

MSRVTT-QA 上 D-CoDe 低于 SF-LLaVA 与 TS-LLaVA，作者认为可能因为该数据集频繁 scene transitions，更有利于 slow-fast processing structures。

### Ablations / Analysis

Module ablation on EgoSchema:

| Variant / Setting | EgoSchema Acc. (%) | Notes |
| --- | ---: | --- |
| Baseline | 44.8 | naive training-free extension of LLaVA-NeXT with uniform sampling and spatial average pooling |
| + dynamic spatial token compression | 50.6 | removes redundancy while preserving salient visual cues |
| + dynamic temporal frame selection | 51.8 | prioritizes semantically diverse frames |
| + question decomposition | **58.0** | full D-CoDe; strongest gain from decomposition |

Sampling strategy ablation on EgoSchema, D-CoDe without question decomposition:

| Variant / Setting | EgoSchema Acc. (%) | Notes |
| --- | ---: | --- |
| Uniform Sampling | 50.6 | baseline sampling strategy |
| Question-aware Sampling | 51.4 | selects frames most semantically similar to the question using CLIP |
| Supplementary Frame Selection (Ours) | **51.8** | preserves more diverse visual information |

Compression range ablation on EgoSchema, D-CoDe without question decomposition:

| Variant / Setting | EgoSchema Acc. (%) | Notes |
| --- | ---: | --- |
| $\leq 4$ neighboring tokens | 51.4 | distance-constrained merging |
| $\leq 5$ neighboring tokens | 51.4 | distance-constrained merging |
| $\leq 6$ neighboring tokens | 52.0 | best reported value in this ablation |
| no constraint (Ours) | **51.8** | paper's default setting |

Prompt ablation on EgoSchema:

| Variant / Setting | EgoSchema Acc. (%) | Notes |
| --- | ---: | --- |
| Default (Ours) | **58.0** | prompt from Table 1 |
| No task/background explanation | 53.2 | contextual guidance matters |
| Removed "temporal and dynamic aspects" | 54.8 | temporal cues matter |
| Rephrased (same meaning, different wording) | 58.4 | wording variation can slightly improve |

Decomposed content ablation on EgoSchema:

| Variant / Setting | EgoSchema Acc. (%) | Notes |
| --- | ---: | --- |
| None (w/o Question Decomposition) | 51.8 | dynamic compression only |
| Sub-Questions | 50.4 | sub-questions alone reduce performance |
| Sub-Answers (Ours) | **58.0** | gain mainly comes from intermediate answers |

Module ablation on other benchmarks:

| Variant / Setting | NExT-QA Acc. (%) | IntentQA Acc. (%) | MSVD Acc./Score | MSRVTT Acc./Score | TGIF Acc./Score | ANet Acc./Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 65.4 | 61.3 | 77.8/4.0 | 62.8/3.5 | 76.9/4.0 | 54.2/3.3 |
| + Dynamic Spatial Token Compression | 66.7 | 62.2 | 79.4/4.0 | 63.6/3.5 | 78.9/4.1 | 55.4/3.3 |
| + Dynamic Temporal Frame Selection | 67.0 | 62.9 | **80.0**/4.1 | **64.2**/3.5 | **79.1**/4.1 | **56.4**/3.4 |
| + Question Decomposition | **68.3** | **64.2** | 72.4/3.8 | 62.2/3.5 | 75.7/4.0 | 53.8/3.3 |

Hyperparameter ablations on EgoSchema:

| Hyperparameter | Value | EgoSchema Acc. (%) |
| --- | ---: | ---: |
| $\alpha$ | 0.80 | 57.2 |
| $\alpha$ | 0.85 | **58.0** |
| $\alpha$ | 0.90 | 57.0 |
| $\alpha$ | 0.95 | 56.2 |
| $\beta$ | 0.575 | 56.6 |
| $\beta$ | 0.600 | 56.4 |
| $\beta$ | 0.625 | **58.0** |
| $\beta$ | 0.650 | 56.2 |
| $\tau$ | 0.80 | 55.0 |
| $\tau$ | 0.85 | 55.6 |
| $\tau$ | 0.90 | **58.0** |
| $\tau$ | 0.95 | 57.0 |
| $t$ | 0.3 | 56.0 |
| $t$ | 0.5 | **58.0** |
| $t$ | 0.7 | 56.2 |
| $t$ | 0.9 | 56.4 |

Efficiency and trade-off analysis on EgoSchema:

| Variant / Setting | EgoSchema Acc. (%) | s/sample | Notes |
| --- | ---: | ---: | --- |
| Baseline | 44.8 | 3.927 | baseline |
| + Dynamic Compression | 51.8 | 6.115 | accuracy gain with moderate latency increase |
| + Question Decomposition | **58.0** | 37.395 | full D-CoDe; much higher latency |
| D-CoDe | **58.0** | 37.395 | default |
| w/ smaller CLIP (35% params) | 58.2 | 35.466 | slightly faster and slightly higher reported accuracy |
| w/ Limit sub-question count = 5 | 56.0 | 26.273 | faster but lower accuracy |
| w/ Limit sub-question count = 7 | 57.8 | 33.704 | near-default accuracy with lower latency |

## Limitations & Caveats

- D-CoDe 在 frequent scene transitions 的视频上相对弱，尤其 MSRVTT-QA 上低于 SF-LLaVA 与 TS-LLaVA。作者认为 slow-fast structures 更适合这类场景。
- Dynamic compression 仍然存在 temporal retention 与 spatial retention 的 trade-off，未来可能需要与 slow-fast architecture 结合。
- Question decomposition 带来明显 latency overhead，EgoSchema 上 full D-CoDe 为 37.395 s/sample，而 baseline 为 3.927 s/sample。
- 精确理解 durations 和 timestamps 仍然困难；作者指出这也是 Vid-LLMs 的 common challenge，可能需要 task-specific training 或 architecture modification。
- Open-ended benchmarks 中 question decomposition 反而使多个结果下降，因此该模块不是对所有 VideoQA 设置都稳定有效。
- 论文使用 GPT-based metrics 评估 open-ended response quality，这类指标本身可能引入评估模型偏差。

## Concrete Implementation Ideas

1. 如果已有 image-pretrained VLM，需要快速加 video 能力，可以先实现 dynamic compression：CLIP global features 做 diverse frame selection，再按 visual token norm 做 top-$k$ pruning。
2. Question decomposition 更适合 long-form、multi-hop、schema-level 的 multiple-choice VideoQA；对简单 open-ended QA 应该默认关闭或用路由器判断是否启用。
3. 在系统实现里缓存 sub-question/sub-answer，避免重复推理造成延迟失控。
4. 可以把 sub-question count 限制为 7，论文报告 EgoSchema accuracy 57.8、33.704 s/sample，接近 full D-CoDe 的 58.0、37.395 s/sample。
5. 对频繁 scene transitions 的数据，可尝试加入 slow-fast pathway 或 memory bank，补足 D-CoDe 对快速场景切换的短板。

## Open Questions / Follow-ups

- Supplementary frame selection 依赖 CLIP global feature 的 semantic diversity，但是否会错过与问题强相关、但视觉上不够“多样”的片段？
- Spatial token pruning 用 $\ell_2$ norm 作为 salience proxy，是否在不同 image encoders 或视觉层级上都稳定？
- Question decomposition 的收益来自 sub-answers 而不是 sub-questions 本身；这些 sub-answers 是否会引入 hallucination 并污染最终答案？
- 是否可以训练一个 lightweight decomposition/router model，减少对 `gpt-3.5-turbo-0125` 这类外部 LLM 的调用成本？
- 在 timestamp-sensitive tasks 上，dynamic compression 是否需要显式保留时间索引或相对位置编码？

## Citation

```bibtex
@article{huang2025dcode,
  title={D-CoDe: Scaling Image-Pretrained VLMs to Video via Dynamic Compression and Question Decomposition},
  author={Huang, Yiyang and Wang, Yizhou and Fu, Yun},
  journal={arXiv preprint arXiv:2510.08818},
  year={2025}
}
```
