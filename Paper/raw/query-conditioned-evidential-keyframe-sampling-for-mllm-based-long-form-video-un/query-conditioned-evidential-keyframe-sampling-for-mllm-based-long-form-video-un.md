---
title: "Query-Conditioned Evidential Keyframe Sampling for MLLM-Based Long-Form Video Understanding"
authors:
  - "Yiheng Wang"
  - "Lichen Zhu"
  - "Yueqian Lin"
  - "Yudong Liu"
  - "Jingyang Zhang"
  - 'Hai "Helen" Li'
  - "Yiran Chen"
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2604.01002"
pdf_link: "[[assets/paper_2604.01002.pdf]]"
cover: "[[_assets/images/pipeline_2604.01002.png]]"
updated: 2026-05-12
tags:
  - "paper/arxiv"
  - "video-qa"
  - "long-video"
  - "temporal-reasoning"
  - "question-aware"
  - "video-llm"
status: "unread"
priority:
rating:
topics:
  - "Video Understanding"
code: ""
---

## TL;DR

- 这篇论文把 long-form video QA 中的 keyframe sampling 重新表述为 query-conditioned evidence selection：选帧目标不是语义相似，而是最大化给定问题 $Q$ 时 selected frames 与答案/输出 $O$ 的 conditional mutual information。
- 直接在所有 frame subset 上优化 $I(S; O \mid Q)$ 是组合爆炸；作者利用 monotone submodular objective 的 modular upper bound，把 subset selection 分解成 frame-level scoring，再在 temporal bins 内做 top-$k$ 选择。
- 方法训练一个 query-conditioned evidence scoring network $g_\theta(f_i, Q)$，包含 frozen CLIP/SigLIP-style vision-language encoder、local temporal aggregator、query-guided gating 和多子空间 evidence score head。
- 训练不需要 MLLM-in-the-loop RL，而是用 annotated evidence segments 构造 positive/negative frames，并用 InfoNCE 排序学习；作者报告在同硬件上比 TSPO 训练高效得多：0.6 hours / 264K samples vs. 78 hours / 10K samples。
- 在 LVBench 与 VideoMME 上，方法在相同 base MLLM 与相近 frame budget 下普遍优于 uniform sampling 和多种 keyframe sampling baselines；但对 audio-centric 和 timestamp-grounded questions 仍有明显局限。

## Key Contributions

1. 提出 evidence bottleneck 视角：将 keyframe selection 目标定义为
   $$
   \max_S I(S; O \mid Q) \quad \text{s.t.} \quad |S| \leq m
   $$
   其中 frame 的价值取决于 query，而不是单纯视觉/文本语义相似度。
2. 证明/利用 evidence objective 的 monotone submodular structure，并用 modular upper bound 将组合优化转为独立 frame-level evidence scoring：
   $$
   F(S) \leq \sum_{f_i \in S} F(\{f_i\}) = \sum_{f_i \in S} I(f_i; O \mid Q)
   $$
3. 设计轻量级 query-conditioned scoring network，用 temporal evidence aggregator 与 query-guided evidence gating 建模局部时序上下文和问题相关通道。
4. 用 evidence segment annotations 构造 positive/negative frames，通过 InfoNCE 学习排序，避免 RL 方法中的 sparse reward、credit assignment 和 combinatorial exploration。
5. 在 LVBench、VideoMME、frame budget ablation、encoder ablation 和 evidence coverage 分析中展示性能与效率收益。

## Method

核心流程可以理解为从“问题相关证据”而不是“语义相关画面”出发选帧：

1. 输入视频帧序列 $V = \{f_1,\ldots,f_n\}$ 与自然语言问题 $Q$。
2. 通过 shared vision-language encoder 得到 frame embeddings $\mathbf{v}_i = \mathcal{E}_v(f_i)$ 与 query embedding $\mathbf{q} = \mathcal{E}_t(Q)$；默认实现中 CLIP-ViT-L frozen。
3. 用 causal window temporal aggregator 给每个 frame 加入局部时序上下文：
   $$
   \mathbf{h}_\tau = \mathcal{T}\left(\mathbf{v}_\tau \mid \{\mathbf{v}_j : f_j \in \mathcal{W}_\tau\}\right)
   $$
4. 用 query-guided evidence gating 过滤 query-irrelevant channels：
   $$
   \mathbf{g}_i = \sigma(\mathbf{W}_h \mathbf{h}_i + \mathbf{W}_q \mathbf{q} + \mathbf{b}), \quad
   \mathbf{u}_i = \mathbf{h}_i \odot \mathbf{g}_i
   $$
5. 将 evidence score 分解到 $K$ 个 semantic subspaces，并和 pretrained VLM cosine similarity prior 加权融合：
   $$
   g_\theta(f_i, Q) =
   \lambda \frac{\mathbf{v}_i^\top \mathbf{q}}{\|\mathbf{v}_i\|_2 \|\mathbf{q}\|_2}
   + (1-\lambda)\frac{1}{K}\sum_{k=1}^{K} s_{i,k}
   $$
6. 选择阶段把视频切成 $B$ 个 temporal bins，每个 bin 内按 evidence score 选 top-$k$：
   $$
   S^* = \bigcup_{b=1}^{B} \operatorname*{top-}k_{f_i \in BIN_b} I(f_i; O \mid Q)
   $$
   VideoMME 采用 temporal-diverse regime：$k=1, B=m$；LVBench 采用 global top-$m$：$k=m, B=1$。
7. 训练阶段用 evidence segments 作为正样本区域，segment 外作为负样本，用 multi-positive InfoNCE：
   $$
   \mathcal{L} =
   - \log
   \frac{\sum_{x \in \mathcal{F}^+} \exp g_\theta(x,Q)}
   {\sum_{x \in \mathcal{F}^+} \exp g_\theta(x,Q) + \sum_{x \in \mathcal{F}^-} \exp g_\theta(x,Q)}
   $$

## Pipeline Figure

![[_assets/images/pipeline_2604.01002.png]]

Caption: Overview of the query-conditioned evidence scoring network. The input video is uniformly sampled into frames, which are encoded into frame embeddings and scored to obtain frame-level evidence scores conditioned on the query. Frames with the highest evidence scores are then selected and fed into an MLLM to generate the final response.

Source: TeX includegraphics from `main.tex`, converted from `assets/model.pdf` using `pdftoppm -cropbox` at 250 DPI.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Seek-173K / LLaVA-Video subset | Training data for evidence scoring | not reported | InfoNCE training signal from evidence segments | evidence segments verified sufficient for MLLMs; inside segment as positive frames, outside as negative frames |
| LVBench | Long-form video question answering | not reported | accuracy; Overall, ER, EU, KIR, TG, Rea, Sum | average video duration 4101 seconds; ER = entity recognition, EU = event understanding, KIR = key information retrieval, TG = temporal grounding, Rea = reasoning, Sum = summarization |
| VideoMME | Video understanding / long-video subset | not reported | Long accuracy, Average accuracy | VideoMME uses temporal-diverse selection with $k=1, B=m$ |

### Main Results: LVBench

| Group | Method | Frames | Overall | ER | EU | KIR | TG | Rea | Sum |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Agentic MLLMs | VideoTree | - | 28.8 | 30.3 | 25.1 | 26.5 | 27.7 | 31.9 | 25.5 |
| Agentic MLLMs | VideoAgent | - | 29.3 | 28.0 | 30.3 | 28.0 | 29.3 | 28.0 | 36.4 |
| Agentic MLLMs | VCA | - | 41.3 | 43.7 | 40.7 | 37.8 | 38.0 | 46.2 | 27.3 |
| SFT/RL MLLMs | MovieChat-7B | &gt;10000 | 22.5 | 21.3 | 23.1 | 25.9 | 22.3 | 24.0 | 17.2 |
| SFT/RL MLLMs | TimeMarker-8B | $\leq 128$ | 41.3 | 42.8 | 39.1 | 34.9 | 38.7 | 38.2 | 48.8 |
| SFT/RL MLLMs | VideoLLaMA3-7B | - | 45.3 | - | - | - | - | - | - |
| SFT/RL MLLMs | Video-R1-7B | 32 | 37.4 | - | - | - | - | - | - |
| SFT/RL MLLMs | Video-Thinker-7B | 32 | 38.4 | - | - | - | - | - | - |
| SFT/RL MLLMs | Video-o3 | $\leq 768$ | 47.6 | - | - | - | - | - | - |
| Keyframe Sampling | Qwen2-VL-7B$^\dagger$ | 32 | 39.1 | 38.7 | 39.0 | 36.8 | 37.3 | 39.8 | 29.3 |
| Keyframe Sampling | + ReTaKe | $\leq 2048$ | 47.8 | - | - | - | - | - | - |
| Keyframe Sampling | + TSPO | 64 | 46.4 | - | - | - | - | - | - |
| Keyframe Sampling | **+ Ours** | 32 | 46.6 | 47.9 | 44.5 | 55.0 | 42.7 | 43.8 | 25.9 |
| Keyframe Sampling | Qwen2.5-VL-7B$^\dagger$ | 32 | 37.6 | 36.8 | 38.6 | 40.6 | 32.7 | 37.3 | 29.3 |
| Keyframe Sampling | + FrameThinker | 23.9 | 36.6 | - | - | - | - | - | - |
| Keyframe Sampling | **+ Ours** | 32 | 47.7 | 49.8 | 44.5 | 57.0 | 37.3 | 41.8 | 34.5 |
| Keyframe Sampling | LLaVA-Video-7B$^\dagger$ | 64 | 41.7 | 41.5 | 40.2 | 42.3 | 33.2 | 49.8 | 29.3 |
| Keyframe Sampling | + ReTaKe | $\leq 1024$ | 48.5 | - | - | - | - | - | - |
| Keyframe Sampling | + TSPO | 64 | 45.3 | - | - | - | - | - | - |
| Keyframe Sampling | **+ Ours** | 64 | 49.4 | 52.4 | 45.9 | 54.6 | 39.0 | 46.8 | 32.8 |

注：$^\dagger$ 表示作者复现实验。LVBench 主表中作者重点标出 Ours 行；subtask 层面尤其是 KIR 提升明显，但 Qwen2-VL-7B 和 LLaVA-Video-7B 在 Rea/Sum 上存在下降或不稳定。

### Main Results: VideoMME

| Base MLLM | Sampling Method | Architecture | Frames | Long | Average |
| --- | --- | --- | ---: | ---: | ---: |
| Qwen2-VL-7B$^\dagger$ | uniform / reproduced baseline | - | 32 | 48.7 | 58.0 |
| Qwen2-VL-7B | AKS | BLIP-0.5B | 32 | - | 59.9 |
| Qwen2-VL-7B | FOCUS | BLIP-0.5B | 32 | - | 59.7 |
| Qwen2-VL-7B | Q-Frame | CLIP-0.4B | 44 | 48.3 | 58.3 |
| Qwen2-VL-7B | MLLM-Selector | MLLM-1.5B | 32 | - | 58.7 |
| Qwen2-VL-7B | **Ours** | CLIP-0.4B | 32 | **51.4** | **60.1** |
| Qwen2-VL-7B | ReTaKe | - | $\leq 2048$ | 56.2 | 63.9 |
| Qwen2.5-VL-7B$^\dagger$ | uniform / reproduced baseline | - | 32 | 50.6 | 60.7 |
| Qwen2.5-VL-7B | K-Frames | MLLM-3B | 32 | - | 62.1 |
| Qwen2.5-VL-7B | AKS | CLIP-0.4B | 32 | - | 62.4 |
| Qwen2.5-VL-7B | BOLT | CLIP-0.4B | 32 | - | 62.0 |
| Qwen2.5-VL-7B | ASCS | CLIP-0.4B | 32 | - | 63.1 |
| Qwen2.5-VL-7B | **Ours** | CLIP-0.4B | 32 | **55.0** | **63.6** |

注：VideoMME 表中 source 明确 bold 了 Ours 在相同 32-frame budget 下的 Long/Average。ReTaKe 的 Qwen2-VL 行使用高得多的 frame budget，因此不与 32-frame 方法直接等价比较。

### Ablations / Analysis: Pretrained Encoder

| Method | Sampling | Encoder | VideoMME | LVBench |
| --- | --- | --- | ---: | ---: |
| Qwen2-VL-7B | Uniform | - | 58.0 | 39.1 |
| Qwen2-VL-7B | Ours | CLIP | **60.1** | **46.6** |
| Qwen2-VL-7B | Ours | SigLIP | 59.9 | 45.8 |
| Qwen2-VL-7B | Ours | SigLIP2 | 59.0 | 44.2 |
| Qwen2.5-VL-7B | Uniform | - | 60.7 | 37.6 |
| Qwen2.5-VL-7B | Ours | CLIP | 63.6 | 47.7 |
| Qwen2.5-VL-7B | Ours | SigLIP | **64.4** | **48.5** |
| Qwen2.5-VL-7B | Ours | SigLIP2 | 61.8 | 43.6 |

作者结论是：sampling framework 对 encoder choice 有一定鲁棒性，但不同 encoder 与不同 downstream MLLM 的 alignment 会影响最终结果。

### Ablations / Analysis: Frame Budget

| Frames | Uniform LVBench | Ours LVBench |
| ---: | ---: | ---: |
| 8 | 35.8 | 45.1 ($\uparrow 9.3$) |
| 16 | 37.1 | 46.0 ($\uparrow 8.9$) |
| 32 | 40.9 | 48.3 ($\uparrow 7.4$) |
| 64 | 41.7 | 49.4 ($\uparrow 7.7$) |

该 ablation 使用 LLaVA-Video-7B on LVBench。一个重要观察是：只用 8 frames 的 Ours 已经超过 uniform sampling 使用更多 frames 的多种设置，说明 evidence-aware selection 对稀疏证据问题很有帮助。

### Ablations / Analysis: Evidence Coverage and Hallucination

| Sampling Budget | Uniform Evidence Coverage | Ours Evidence Coverage | Gain |
| ---: | ---: | ---: | ---: |
| 32 frames | 33.64% | 50.26% | +16.62% |
| 64 frames | 45.35% | 57.85% | +12.50% |

作者在 supplementary 中把 hallucination 解释为 evidence availability 问题：三个模型 refusal rates 接近 0，错误时通常不是拒答，而是在缺少视觉证据时自信猜测。Ours 提高了至少命中一个 ground-truth evidence segment frame 的概率，但即使 64 frames 仍有大量样本未覆盖证据，说明 long-video QA 的证据稀疏性仍然很强。

### Training / Compute

| Item | Value |
| --- | --- |
| Default encoder | CLIP-ViT-L, frozen |
| Trainable modules | approximately 10M parameters |
| Training objective | InfoNCE over positive evidence frames and negative non-evidence frames |
| Training data | LLaVA-Video subset of Seek-173K; evidence segments used as supervision |
| Training schedule | 5 epochs |
| Batch size | 128 |
| Training hardware | 8 NVIDIA RTX A5000 GPUs |
| Evaluation framework | `lmms-eval` |
| Evaluation hardware | NVIDIA L40S GPUs |
| Training efficiency comparison | TSPO: 78 hours on 10K samples using 8 NVIDIA L40 GPUs; Ours: 0.6 hours on 264K samples under same hardware setting |

### Inference Latency

| Video Duration | Frames | Sampling Latency | MLLM Latency |
| --- | ---: | ---: | ---: |
| 2 min | 64 | 3.0 | 2.1 |
| 8 min | 64 | 7.6 | 2.1 |
| 30 min | 64 | 18.6 | 2.1 |

注：paper 说明 MLLM latency 是 single-token response 的 minimal setting，因此更像下界。Sampling latency 随 video duration 增长，主要来自 dense frame sequence 上的 CLIP feature extraction；MLLM 由于固定 64-frame budget，延迟保持常数。

## Limitations & Caveats

- **Audio-centric questions**：方法只基于 visual frames 和 vision-language encoder，不直接处理 speech、sound effects、background music。作者给出的例子是需要听第八位选手唱歌类型的问题；这类问题 visual evidence score 会系统性缺失音频证据。
- **Timestamp-grounded questions**：$g_\theta$ 没有显式学习 absolute timestamps 或 temporal intervals，因此类似 “What happens from 02:45-04:00?” 的问题会受影响。作者建议未来加入 temporal position embeddings 或 timestamp-aware supervision。
- **Global understanding / summarization**：supplementary failure case 显示，当问题需要全局视频理解时，Ours 可能把 sampled frames 聚集在局部高分片段，降低全局覆盖；uniform sampling 反而可能更稳。
- **Evidence annotation dependency**：训练依赖带 evidence segments 的数据。若新领域没有可靠 evidence interval annotations，需要额外生成、弱监督或迁移策略。
- **Modular relaxation 的冗余风险**：frame-level scoring 让推理高效，但不能完全建模 selected frames 之间的互补性与冗余；作者用 temporal bins 缓解，但没有彻底解决 subset-level diversity。

## Concrete Implementation Ideas

1. 做长视频 QA pipeline 时，可以先离线抽取 1 FPS CLIP/SigLIP embeddings，再训练一个轻量 query-conditioned scorer；这样把 MLLM 调用留到 fixed-budget selected frames 上。
2. 根据问题类型动态选择 sampling regime：localized evidence questions 使用 global top-$m$；需要覆盖全程的 summarization/global reasoning 使用 per-bin top-$k$ 或混合策略。
3. 在现有 selector 上加入 audio embedding branch，将 visual-positive evidence segments 扩展为 audio-visual evidence supervision，优先修复 audio-centric failure。
4. 给 scorer 增加 timestamp / relative position features，并在训练中加入 timestamp-grounded questions 的监督，避免所有 evidence 都被视作无时间坐标的 frame-level relevance。
5. 评估时不要只看 QA accuracy，也记录 evidence coverage：sampled frames 是否至少命中 ground-truth evidence segment。这能更直接地区分 selector failure 和 MLLM reasoning failure。

## Open Questions / Follow-ups

- $B$ 和 $k$ 是否可以由 query type 自适应决定，而不是在 LVBench / VideoMME 上手动设置？
- 如果没有人工 evidence segments，能否用 MLLM self-consistency、counterfactual frame removal 或 weak timestamp labels 构造足够干净的 positive/negative supervision？
- Modular upper bound 简化了训练和推理，但是否会在多步 temporal reasoning 中错过“单帧不强、组合才强”的证据？
- 该 scorer 与 token pruning / visual token compression 是否互补？例如先 evidence-aware keyframe sampling，再对 selected frames 做 token pruning。
- Evidence coverage 提升后仍不到 60%，下一步瓶颈是更好的 scoring、更多 frames，还是 downstream MLLM 对稀疏 evidence 的利用能力？

## Citation

```bibtex
@misc{wang2026queryconditionedevidentialkeyframesampling,
  title={Query-Conditioned Evidential Keyframe Sampling for MLLM-Based Long-Form Video Understanding},
  author={Yiheng Wang and Lichen Zhu and Yueqian Lin and Yudong Liu and Jingyang Zhang and Hai "Helen" Li and Yiran Chen},
  year={2026},
  eprint={2604.01002},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  doi={10.48550/arXiv.2604.01002}
}
```
