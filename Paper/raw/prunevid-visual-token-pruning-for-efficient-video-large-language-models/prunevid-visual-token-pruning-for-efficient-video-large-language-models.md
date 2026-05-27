---
title: "PruneVid: Visual Token Pruning for Efficient Video Large Language Models"
authors:
  - Xiaohu Huang
  - Hao Zhou
  - Kai Han
conference: ACL 2025
year: 2024
arxiv_url: https://arxiv.org/abs/2412.16117
pdf_link: "[[assets/paper_2412.16117.pdf]]"
cover: "[[assets/pipeline_2412.16117.png]]"
updated: 2026-05-26
tags:
  - paper/arxiv
  - video-llm
  - video-qa
  - token-pruning
  - question-aware
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/Visual-AI/PruneVid
---
> First-principles analysis: [[prunevid-visual-token-pruning-for-efficient-video-large-language-models-first-principles]]

## TL;DR

- PruneVid 是面向 Video LLM 的 training-free visual token pruning 方法，不需要重新训练或微调现有模型。
- 它先消除视频自身冗余：在 temporal segments 内合并 static tokens，再以 DPC-KNN 聚合空间相似 tokens。
- 它再利用 LLM 中间层的 question-to-video attention，仅保留与问题相关的 top-$\alpha$ visual tokens，并据此压缩早期层 KV cache。
- 在 PLLaVA、ST-LLM、LLaVA-OneVision 上，作者报告保留比例为 $15.1\%$--$17.0\%$ 时，效果仍接近或优于对应未剪枝模型/其他 pruning 方法。
- PLLaVA 的效率诊断中，PruneVid 将 visual-token FLOPs 降至 $0.23\times$，TTFT speed-up 达到 $1.55\times$，GPU memory 从 20G 降至 17G，同时 MVBench accuracy 从 46.6 提至 47.6。

## Key Contributions

1. 提出可插入已有 Video LLM 的 training-free PruneVid，将视频 token 压缩从依赖额外训练变为推理阶段方法。
2. 将压缩拆成两个互补问题：基于运动/相似度的 spatial-temporal redundancy removal，以及基于问题语义的 relevance-aware token selection。
3. 把选出的 visual token indices 同步用于压缩前 $M$ 层 KV cache，从而不仅减少后续 prefill token，也降低 decoding 阶段的 memory 与 attention 开销。
4. 在四个类型不同的视频 benchmark 和三种 backbone 上报告效果/效率比较，并给出关键超参数和 attention selection 的诊断研究。

## Method

给定 $T$ 帧视频，每帧视觉 token 为 $\bm{X}_v^{(t)} \in \mathbb{R}^{N_v \times C}$，问题 token 为 $\bm{X}_q \in \mathbb{R}^{N_q \times C}$。PruneVid 的流程如下：

1. 对每帧 token 平均池化得到 frame feature，用 DPC-KNN 将视频分成 $B$ 个连续 temporal segments，其中 $B$ 与 $T$ 由比例 $\gamma$ 控制。
2. 在每个 segment 的同一空间位置上计算跨帧 cosine similarity；若平均相似度满足 $\bar{s}_i \geq \tau$，该位置被视为 static，并沿时间平均为一个表示；dynamic tokens 保留时序变化。
3. 分别对 static 与 dynamic token 做 spatial DPC-KNN clustering，以比例 $\beta$ 合并相似空间 token，得到输入 LLM 的压缩序列 $\tilde{\bm{X}}_v$。
4. 在 LLM 第 $M$ 层提取 question-to-video attention $\bm{A}_{qv}^{(M)}$，对 question 维度做 max pooling：

$$
\bm{a}_v = \max_{i=1}^{N_q} \bm{A}_{qv}^{(M)}(i, :)
$$

5. 保留 attention score 最高的 top-$\alpha$ visual tokens，后续 $L-M$ 层仅处理这些 token 与问题 token。
6. 对前 $M$ 层已形成的 KV cache 按相同 token index 做裁剪，使 decoding 的序列长度由 $N_q + N'_v$ 变为 $N_q + |\mathcal{S}|$。

作者采用的统一 PruneVid 配置为 $\tau=0.8$、$\gamma=0.25$、$\beta=0.5$、$\alpha=0.4$、$M=10$。

## Pipeline Figure

![[assets/pipeline_2412.16117.png]]

Caption: PruneVid 先进行 temporal clustering 与 static/dynamic token 区分，再依次执行 static temporal merge 和 spatial merge；进入 Video LLM 后，由问题 token 对 visual token 的 attention 指导筛选，并压缩对应 KV cache。

Source: TeX `\includegraphics{fig/method_in_one.pdf}` in `main.tex`, whose caption explicitly identifies it as an illustration of the PruneVid framework; the PNG above was rendered from the source PDF using its visible crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| MVBench | Generic Multi-Choice VideoQA | 20 tasks, each with 200 test samples | Accuracy | 强调 temporal reasoning，单帧不足以回答 |
| Video-MME | Long-form Multi-Choice VideoQA | not reported in paper text | Accuracy | 长视频评测 |
| EgoSchema | Long-form Multi-Choice VideoQA | Subset / Fullset | Accuracy | 论文同时报告两个 split |
| VideoChatGPT-Bench | Text generation evaluation | not reported in paper text | TU, CU, CO, DO, CI, Avg | 由 `GPT-3.5-Turbo-0125` 评分 |

### Setting / Compute

| Item | Value |
| --- | --- |
| Hardware | NVIDIA A100 GPU, 80GB |
| Backbones | PLLaVA, ST-LLM, LLaVA-OneVision |
| Input frames | PLLaVA: 16; ST-LLM: 16, but VideoChatGPT-Bench: 64; LLaVA-OneVision: 32 |
| PruneVid hyperparameters | $\tau=0.8$, $\gamma=0.25$, $\beta=0.5$, $\alpha=0.4$, $M=10$ |
| Baselines | LLaVA-PruMerge, Look-M, FastV |
| Baseline compatibility | LLaVA-PruMerge is not applied to ST-LLM because it is incompatible |
| FastV comparison setting | Prunes at layer 2 and retains ratio 0.3 to obtain roughly comparable FLOPs |
| FLOPs scope | Measured relative to visual tokens in the LLM |

### Main Results

下列表格的粗体完全保留论文原表的标注：作者将粗体用于 pruning methods 之间的最佳结果，而不是重新对包含未剪枝 baseline 的所有行排序；对原表中看似不一致的加粗也不做修正。

**PLLaVA**

| Method | Retained Ratio | FLOPs | MVBench | VideoMME | EgoSchema Subset / Fullset | TU | CU | CO | DO | CI | Avg |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PLLaVA | 100.0% | 1.00x | 46.6 | 44.4 | 47.8 / 42.6 | 2.33 | 3.62 | 2.93 | 2.86 | 3.21 | 2.99 |
| PLLaVA w/ FastV | 30.0% | 0.33x | 46.1 | 43.6 | 46.2 / 41.0 | 2.38 | 3.49 | 2.89 | 2.76 | 3.14 | 2.93 |
| PLLaVA w/ Prumerge | 55.7% | 0.53x | 45.6 | 43.8 | 45.2 / 40.4 | 2.34 | 3.52 | 2.90 | 2.76 | 3.15 | 2.93 |
| PLLaVA w/ Look-M | 20.0% | 1.00x | 46.6 | 44.3 | 47.0 / 42.3 | 2.28 | 3.41 | 2.75 | 2.65 | 3.00 | 2.82 |
| PLLaVA w/ Ours | **16.2%** | **0.23x** | **47.6** | **45.0** | **49.0** / **42.6** | **2.44** | **3.51** | **2.99** | **2.78** | **3.20** | **2.98** |

**ST-LLM**

| Method | Retained Ratio | FLOPs | MVBench | VideoMME | EgoSchema Subset / Fullset | TU | CU | CO | DO | CI | Avg |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ST-LLM | 100.0% | 1.00x | 54.9 | 42.0 | 56.2 / 45.6 | 2.46 | 3.46 | 2.66 | 2.63 | 3.08 | 2.86 |
| ST-LLM w/ FastV | 30.0% | 0.37x | 42.9 | 34.5 | 48.0 / 38.5 | 2.01 | 2.23 | 1.55 | 1.94 | 1.69 | 1.88 |
| ST-LLM w/ Look-M | 20.0% | 1.00x | 54.0 | 40.6 | 54.0 / 44.5 | 2.35 | 3.41 | 2.60 | 2.51 | 3.01 | 2.78 |
| ST-LLM w/ Ours | **15.1%** | **0.26x** | **54.3** | **41.4** | **54.6** / **44.7** | **2.40** | **3.43** | **2.63** | **2.60** | **3.04** | **2.82** |

**LLaVA-OneVision**

| Method | Retained Ratio | FLOPs | MVBench | VideoMME | EgoSchema Subset / Fullset | TU | CU | CO | DO | CI | Avg |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-OneVision | 100.0% | 1.00x | 58.0 | 58.2 | 62.0 / 60.0 | 2.75 | 3.70 | 3.39 | 2.97 | 3.50 | 3.26 |
| LLaVA-OneVision w/ FastV | 30.0% | 0.30x | 57.2 | 57.6 | 62.6 / 60.0 | 2.65 | 3.61 | 3.28 | 2.85 | 3.39 | 3.16 |
| LLaVA-OneVision w/ Prumerge | 55.2% | 0.49x | 52.9 | 56.7 | 62.2 / 60.0 | 2.72 | 3.64 | **3.32** | **2.94** | 3.44 | 3.21 |
| LLaVA-OneVision w/ Look-M | 20.0% | 1.00x | 57.0 | 58.0 | 62.0 / **59.8** | 2.71 | 3.70 | 3.29 | 2.89 | 3.44 | 3.21 |
| LLaVA-OneVision w/ Ours | **17.0%** | **0.20x** | **57.5** | **58.6** | **62.6** / 59.5 | **2.73** | **3.72** | 3.28 | **2.94** | **3.51** | **3.24** |

### Efficiency Analysis

该表是作者在 PLLaVA-based diagnostic study 中报告的比较，accuracy 对应 MVBench。

| Method | FLOPs | TTFT Speed Up | GPU Mem | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 1.00x | 1.00x | 20G | 46.6 |
| Baseline w/ FastV | 0.33x | 1.15x | 19G | 46.1 |
| Baseline w/ Prumerge | 0.53x | 1.32x | 19G | 45.6 |
| Baseline w/ Look-M | 1.00x | 0.15x | 35G | 46.6 |
| Baseline w/ Ours | **0.23x** | **1.55x** | **17G** | **47.6** |

### Ablations / Analysis

| Variable(s) | Evidence stated in paper | Selected Setting |
| --- | --- | --- |
| Token selection layer $M$ and retained ratio $\alpha$ | 从第 10 层后开始 pruning 时 accuracy 基本趋于饱和；在 $M=10$ 时，$\alpha=0.4$ 优于 $\alpha=0.5$，作者认为额外 token 可能带来无关信息 | $M=10$, $\alpha=0.4$ |
| Static threshold $\tau$ and temporal segment ratio $\gamma$ | 从 $\tau=0.6$ 到 $0.8$ 表现持续改善，$\tau=0.8$ 与 $0.9$ 近似；$\gamma=0.25$ 与 $1.0$ 都表现良好，但 $\gamma=1.0$ 不利于 temporal merge | $\tau=0.8$, $\gamma=0.25$ |
| Static threshold $\tau$ and spatial merging ratio $\beta$ | $\tau=0.8$ 略优于 $0.9$；$\beta=0.5$ 最优，过小会过度合并，$\beta=1.0$ 无法去除空间冗余 | $\tau=0.8$, $\beta=0.5$ |

注：消融结果在论文中以曲线图呈现，正文未逐点给出数值，故这里只转录正文可核验的比较结论与选定配置。

## Limitations & Caveats

- 论文明确给出三个 backbone 的 benchmark 表，但详细 TTFT/GPU memory 效率表仅在 PLLaVA diagnostic setting 下展示；对更大 backbone 的端到端 wall-clock 收益仍缺完整报告。
- PruneVid 以一组固定 $\tau,\gamma,\beta,\alpha,M$ 覆盖全部 benchmark。作者展示其可行性，但不同视频长度、问题类型或 backbone 是否需要动态 token budget 尚未验证。
- 作者以 attention visualization 支撑“LLM reasoning 能发现相关区域”的论点；这些定性样例说明相关性，但未单独建立 attention score 与因果必要 visual evidence 之间的严格关系。
- 方法在第 $M$ 层做一次保留决策。以下属于结构性推断：若问题需要晚期组合推理、细粒度短暂事件或低 attention 但关键的视觉证据，早期剪除可能无法恢复。

## Concrete Implementation Ideas

1. 在现有 Video LLM inference pipeline 中插入可开关的 PruneVid module，并记录每一阶段 token count、prefill latency、decode latency 和 KV memory，复现 efficiency accounting。
2. 实现 $\alpha$ 的 per-query adaptive policy，例如以 attention concentration 或累计 attention mass 决定保留预算，和固定 $\alpha=0.4$ 对比 accuracy-latency Pareto curve。
3. 为短暂事件、计数、顺序推理分别建立 error buckets，检查 static temporal merge 是否会误合并答案所需的微小变化。
4. 将一次性第 $M$ 层选择扩展为两阶段 selection：早层粗筛加晚层小规模复核，评估能否挽回被早期 attention 低估的证据。

## Open Questions / Follow-ups

- token selection 的增益来自 question conditioning 本身，还是来自它与 spatial-temporal merge 的组合？需要组件级量化消融。
- 对 long-video 输入，segment 数量、场景切换密度和 token reduction/accuracy 之间的关系是否稳定？
- 以 attention 为重要性 proxy 时，是否存在保留率很低但答案被偶然猜对的情况；能否加入 evidence coverage 或 counterfactual masking 检查？
- 该方法在包含 audio、OCR text 或多轮对话条件的 Video LLM 上是否仍能用同一 relevance signal？

## Citation

```bibtex
@article{huang2024prunevid,
  title   = {PruneVid: Visual Token Pruning for Efficient Video Large Language Models},
  author  = {Huang, Xiaohu and Zhou, Hao and Han, Kai},
  journal = {arXiv preprint arXiv:2412.16117},
  year    = {2024},
  url     = {https://arxiv.org/abs/2412.16117}
}
```
