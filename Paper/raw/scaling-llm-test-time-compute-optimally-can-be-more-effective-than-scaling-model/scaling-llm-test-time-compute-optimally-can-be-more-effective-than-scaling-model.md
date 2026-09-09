---
title: Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters
authors:
  - Charlie Snell
  - Jaehoon Lee
  - Kelvin Xu
  - Aviral Kumar
conference:
year: 2024
arxiv_url: https://arxiv.org/abs/2408.03314
pdf_link: "[[assets/paper_2408.03314.pdf]]"
cover: "[[_assets/images/pipeline_2408.03314.png]]"
updated: 2026-05-19
tags:
  - paper/arxiv
  - reasoning
  - efficient-inference
status: unread
priority:
rating:
topics:
  - LLM
code: ""
---

## TL;DR

- 这篇论文系统研究 LLM 的 test-time compute scaling：在固定推理预算下，是否能比单纯增大模型参数更有效地提升数学推理准确率。
- 作者把 test-time compute 归纳成两条轴线：用 PRM/ORM 等 verifier 做候选搜索，以及通过 revision model 在测试时自适应改变 proposal distribution。
- 核心观察是：最优推理策略强依赖题目难度。容易题更适合 sequential revisions 或保守的 best-of-N；中等偏难题更适合搜索；最难题上现有方法收益很小。
- 基于 difficulty bin 的 compute-optimal 策略可以比 best-of-N 更省推理预算：revision 设置中可用约 $4\times$ 更少 compute 超过 best-of-N；PRM search 设置中也接近 $4\times$ 的效率收益。
- FLOPs-matched 比较显示，小模型加 test-time compute 在容易/中等题或低 inference workload 时可优于约 $14\times$ 更大的模型；但高难题或高 inference/pretraining 比例时，pretraining scale 仍更划算。

## Key Contributions

1. 提出一个统一视角：test-time compute 可以看成在测试时自适应地修改 LLM 的输出分布，主要通过 proposal distribution refinement 和 verifier-guided search 两类机制实现。
2. 定义并实证研究 test-time compute-optimal scaling strategy，即按题目难度和预算选择最佳超参数/搜索策略，而不是对所有题目使用固定 best-of-N。
3. 在 MATH 上分析 PRM search、beam search、lookahead search、best-of-N weighted、revision model、majority/ORM selection 等多种推理时计算分配方式。
4. 证明题目难度是一个有效的策略选择统计量：difficulty-conditioned 策略在 revision 和 search 两条路线中都明显提升 compute efficiency。
5. 做了 pretraining FLOPs 与 inference FLOPs 的 exchange-rate 分析，说明 test-time compute 与参数规模不是 1:1 可替换，收益取决于题目难度和 $R = D_{\text{inference}} / D_{\text{pretrain}}$。

## Method

论文的核心 pipeline 可以压缩成下面几个步骤：

1. 给定 prompt $q$ 和 test-time compute budget $N$，先估计题目相对于当前 base LLM 的 difficulty bin。
2. 在验证折上为每个 difficulty bin 和预算选择最优策略 $\theta$，例如 best-of-N、beam search、lookahead search，或 sequential/parallel revisions 的比例。
3. verifier 路线：用 PaLM 2-S* 生成候选解；PRM 给每一步打 reward-to-go 分数；最终使用 last-step score 和 best-of-N weighted 聚合选择答案。
4. revision 路线：训练 revision model，使其基于前几次错误尝试生成新的修正版；推理时生成 sequential revision chains，再用 ORM verifier 或 majority voting 选择最终答案。
5. FLOPs 分析路线：用 $X = 6ND_{\text{pretrain}}$ 近似 pretraining FLOPs，用 $Y = 2ND_{\text{inference}}$ 近似 inference FLOPs，比较小模型加推理时计算和约 $14\times$ 参数规模模型的预算等价点。

论文给出的 compute-optimal 目标是：

$$
\theta^{*}_{q,a^*(q)}(N) = \operatorname{argmax}_{\theta}\, \mathbb{E}_{y \sim \operatorname{Target}(\theta, N, q)} \left[ \mathbbm{1}_{y = y^*(q)} \right]
$$

这里 $\operatorname{Target}(\theta,N,q)$ 表示在 prompt $q$、预算 $N$、策略超参数 $\theta$ 下诱导出的输出分布。

## Pipeline Figure

![[_assets/images/pipeline_2408.03314.png]]

Caption: 论文没有一个覆盖全部贡献的单一 global pipeline 图；这里选取最接近 pipeline/framework 的方法图。它展示 parallel sampling / best-of-N 与 sequential revisions 的差异，以及如何在同一预算下混合 parallel 和 sequential allocation，并用 verifier 选择最终答案。

Source: TeX source `template_content.tex`, `\includegraphics{figures/Revisions_descriptive_fig.pdf}`；已用 `pdftoppm -cropbox` 从 PDF figure 转成 PNG。

## Experiments

论文没有在 TeX 中提供传统 Markdown 可转换的数值表格；主要结果来自 figure curves 和 captions。下面的表保留作者明确报告的设置、比较关系和结论，不从图中反推未给出的数值。

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MATH | High-school competition math reasoning | 12k train / 500 test, following Lightman et al. | pass@1, final-answer correctness / accuracy | 主实验 benchmark；题目 difficulty 由 base LLM 的 pass@1 估计并分成 5 个 quantile bins。 |
| PRM800k questions / released process data | Process reward model reference data | Released PRM training data plus generated PaLM 2 samples | PRM step-value supervision | 作者发现直接使用 released PRM800k labels 对 PaLM 2 分布不理想，因此改用 Monte Carlo rollout 生成 soft per-step value labels。 |
| Generated revision trajectories | Revision model SFT | 64 outputs per question; contexts include 0-4 incorrect answers before a correct answer | Final-answer correctness; revision pass@1 | 用 parallel samples 后处理构造 revision trajectories；按 character edit distance 选相关的错误答案进入上下文。 |

### Main Results

| Result Area | Compared Setting | Reported Finding | Evidence |
| ---- | ---- | ---- | ---- |
| PRM search | Best-of-N weighted vs beam search vs lookahead search | 小预算下 beam search 最强；预算继续增加后收益递减甚至低于 best-of-N；lookahead search 因额外 rollout 成本通常不占优。 | Figure `comparing_search_and_beam_difficulty` |
| Difficulty-conditioned search | Compute-optimal PRM search vs PRM best-of-N | 按题目难度选择 search strategy 可在低预算区间接近用约 $4\times$ 更少 compute 达到 best-of-N 效果，例如 16 vs 64 generations。 | Figure `compute_optimal_search` |
| Revision model | Sequential revisions vs parallel sampling | revision step 的 pass@1 会逐步提高；在 verifier selection 和 majority voting 下，sequential revisions 都略优于同预算 parallel sampling。 | Figure `revision_model_results` |
| Difficulty-conditioned revisions | Compute-optimal sequential/parallel ratio vs parallel best-of-N | 按 difficulty 和预算选择 sequential/parallel ratio 后，compute-optimal revisions 可用约 $4\times$ 更少 test-time compute 超过 best-of-N，例如 64 vs 256 samples。 | Figure `compute_optimal_revisions` |
| Pretraining vs test-time compute | PaLM 2-S* + compute-optimal inference vs about $14\times$ larger pretrained model | 容易/中等题、或 $R \ll 1$ 的低 inference workload 场景中，test-time compute 常更划算；高难题或 $R \gg 1$ 时，扩大 pretraining/model scale 更有效。 | Figure `pretrain_exchange` |
| Overall efficiency | Difficulty-conditioned strategies vs fixed baselines | 论文总结 compute-optimal test-time scaling 带来约 $2\times$ 到 $4\times$ 的 compute efficiency gain。 | Discussion |

### Ablations / Analysis

| Variant / Setting | Finding | Notes |
| ---- | ---- | ---- |
| Difficulty bins from oracle pass@1 | 可很好预测不同 strategy 的收益区域。 | 需要 ground-truth correctness function，部署时不可直接获得。 |
| Predicted difficulty from PRM scores | 与 oracle bins 表现趋势相近。 | 作者用 2048 samples 的 averaged PRM final-answer score 估计 difficulty；成本很高。 |
| PRM aggregation: min / product / last | last-step score 表现最好。 | 与一些早期 process-supervision work 的 min aggregation 结论不同，作者认为和 soft MC return label 的训练方式有关。 |
| PRM vs ORM for base model outputs | PRM 优于 ORM。 | PRM 的 step-level training 可能更多起到 representation learning 效果。 |
| ORM for revision model outputs | 针对 revision outputs 训练的 ORM 优于 base PRM。 | 分布迁移会让 base PRM 对 revision model outputs 不够稳。 |
| Correct answers during naive revisions | 约 38% 的正确答案会被下一步 revision 改错。 | 因此需要 verifier 或 majority voting 从 revision chain 中选择答案。 |
| $\text{ReST}^{\text{EM}}$ optimized revision model | 增加 sequential revisions 反而明显伤害性能。 | 作者推测 online data 加剧了 revision data 的 spurious correlation。 |
| Hardest difficulty bin | 现有 search/revision 方法都很难取得显著收益。 | 这支持“test-time compute 不是 pretraining scale 的 1:1 替代品”的结论。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Base model | PaLM 2-S* (Codey) |
| Main benchmark | MATH, 12k train / 500 test split |
| Difficulty estimate | Base LLM pass@1 from 2048 samples, binned into 5 quantiles; predicted difficulty uses averaged PRM final-answer scores over 2048 samples. |
| Cross-validation | Two-fold cross validation within each difficulty bin to avoid selecting strategy and measuring performance on the exact same fold. |
| PRM training labels | 16 samples per question; 16 Monte Carlo rollouts per step to estimate soft reward-to-go values. |
| PRM objective / optimizer | Binary cross entropy over soft values; AdamW, lr 3e-5, batch size 128, dropout 0.05, betas $(0.9, 0.95)$. |
| PRM validation | Early stopping on a random held-out validation set consisting of 10% of questions from the original PRM800k training split. |
| Search methods | Best-of-N weighted, beam search, lookahead search; beam expansion capped at 40 rounds. |
| Search budget accounting | Beam / best-of-N budget is number of generations; lookahead cost is counted as $N \times (k+1)$ samples. |
| Search sweep | Max budget 256; beam width $\sqrt{N}$ or fixed 4; lookahead with $k=1$ or $k=3$ in reported sweeps. |
| Revision data | 64 responses per question; up to 4 incorrect answers in context; closest incorrect answer chosen by character edit distance. |
| Revision model optimizer | AdamW, lr 1e-5, batch size 128, dropout 0.0, betas $(0.9, 0.95)$. |
| Revision inference | Context truncated to the most recent four revised responses; final answer selected by ORM verifier or majority voting. |
| FLOPs exchange | Pretraining $X = 6ND_{\text{pretrain}}$; inference $Y = 2ND_{\text{inference}}$; experiments compare $R \in \{0.16, 0.79, 22\}$ and about $14\times$ parameter scaling. |

## Limitations & Caveats

- difficulty-conditioned routing 的关键依赖是 difficulty estimation；oracle difficulty 不可部署，predicted difficulty 又需要大量采样，完整成本未计入主曲线。
- 实验集中在 MATH 和 PaLM 2-S*，结论对其他任务、模型家族、tool-augmented settings、open-ended agent tasks 的迁移仍需验证。
- 在最难题上，search 和 revision 都没有带来显著进展；当 base model 完全缺乏能力时，test-time compute 很难弥补 pretraining/model capacity。
- PRM search 存在 over-optimization 风险，例如过短答案、低信息重复步骤、利用 verifier spurious features 等。
- revision model 需要 capability-specific finetuning；论文也承认未来模型可能通过预训练直接获得 verification/revision 能力。
- 作者没有实验 PRM tree-search 与 revisions 的组合，也没有系统覆盖 critique-and-revise、tool use、MCTS with exploration 等更多 test-time compute 机制。

## Concrete Implementation Ideas

1. 为推理服务加一个 lightweight difficulty router：先用少量 samples、verifier confidence、answer entropy 或 self-consistency 信号估计难度，再动态选择 best-of-N、beam search、revision chain 或直接 greedy。
2. 在 PRM/ORM verifier 上加入 anti-exploitation guardrails，例如答案长度范围、重复检测、step information density、calibration checks，避免 beam search 优化出 verifier 喜欢但人类不信的答案。
3. 把 compute-optimal 生成出的高置信解蒸馏回 base model，形成“test-time compute → training data → better proposal distribution”的闭环。
4. 针对 production workload 估算 $R = D_{\text{inference}} / D_{\text{pretrain}}$，再决定预算应该投向更大模型、更多并行采样、sequential revisions，还是 verifier training。
5. 建一个 per-domain strategy table：按任务类型、难度、预算、latency SLA 映射到不同 test-time compute policy，避免所有请求都套同一种 best-of-N。

## Open Questions / Follow-ups

- 能否用远少于 2048 samples 的信号估计 difficulty，并保持接近 oracle bins 的策略选择收益？
- PRM search 与 revision model 如果组合在同一 tree 或 graph search 中，会互相增强还是放大 verifier exploitation？
- 这些结论在代码生成、tool-use agent、multi-step planning、scientific reasoning 等非 MATH 任务上是否成立？
- 什么样的 stopping rule 可以在预算未用完时提前停止，并保留 compute-optimal 的大部分收益？
- 当把 difficulty estimation 的成本完整纳入 FLOPs/latency 后，compute-optimal routing 的净收益还剩多少？

## Citation

```bibtex
@misc{snell2024scalingllmtesttimecompute,
  title={Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters},
  author={Charlie Snell and Jaehoon Lee and Kelvin Xu and Aviral Kumar},
  year={2024},
  eprint={2408.03314},
  archivePrefix={arXiv},
  primaryClass={cs.LG},
  doi={10.48550/arXiv.2408.03314},
  url={https://arxiv.org/abs/2408.03314}
}
```
