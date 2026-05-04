---
title: "Addressing Blind Guessing: Calibration of Selection Bias in Multiple-Choice Question Answering by Video Language Models"
authors: ["Olga Loginova", "Oleksandr Bezrukov", "Ravi Shekhar", "Alexey Kravets"]
conference: ""
year: 2024
arxiv_url: "https://arxiv.org/abs/2410.14248"
pdf_link: "[[assets/paper_2410.14248.pdf]]"
cover: "[[assets/pipeline_2410.14248.png]]"
updated: 2026-04-29
tags: ["paper/arxiv", "video-qa", "temporal-reasoning", "option-aware", "question-aware", "video-llm", "benchmark"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://github.com/ologin/BOLD"
---

## TL;DR

- 这篇论文研究 Video Language Models 在 MCQA 视频问答中的 selection bias：模型会偏向某些选项位置，而不是稳定依赖视频、问题和答案内容。
- 作者构造 11 种 dataset modification，把 video、question、answer options 分别扰动或移除，用来定位 bias 在哪些 task component 下最明显。
- 论文提出 BOLD（Bias Optimisation Leveraging Decomposition）：在 ill-defined task 上估计 option prior bias，再用 post-processing 校准原始预测概率。
- Weighted_BOLD 进一步给不同 decomposition prior 加权，论文报告在 $k=0.5$ 且 $w_i \geq 0$ 时取得较好的性能与 debiasing 平衡。
- 在 Video-LLaMA 与 Video-LLaVA 上，BOLD/Weighted_BOLD 通常同时提升 Accuracy、F1_mean，并降低 Recall_std、F1_std、JS_std；SeViLA 本身更接近均匀，收益较小，STAR 上还有轻微性能下降。

## Key Contributions

1. 首次系统性分析 video-to-text LLM-powered models 在 video MCQA 中的 selection bias，覆盖 Video-LLaMA、Video-LLaVA、SeViLA 与多个视频推理 benchmark。
2. 设计 11 种 task modification，从 video、question、answer option 三个 component 分解 MCQA，观察模型是否依赖 answer position 等 superficial cues。
3. 将 fairness bias metrics 迁移到 MCQA option-level bias 监测，使用 Recall_std、F1_std、JS_std 衡量不同选项之间的性能/概率分布不均衡。
4. 提出 BOLD 与 Weighted_BOLD：无需重新训练、无需 exhaustive answer shuffling，仅通过少量 decomposed samples 估计 global prior 并校准预测。
5. 结果显示 selection bias reduction 不只是让分布更公平，也常常提升实际 Accuracy 与 F1_mean，尤其对 bias 更强的 Video-LLaVA 收益最大。

## Method

论文把 video MCQA task $T$ 看作由 video context、question、answer options 三个关键 component 组成。若移除任一 component，任务变成 ill-defined；合理且无偏的模型此时应接近 uniform choice。偏离 uniform 的部分被视作 selection prior bias。

核心概率分解是：

$$
P_o(d_i \mid T) = \frac{1}{Z_T} P_p(d_i \mid T) \times P_d(d_i \mid T)
$$

其中 $P_o$ 是 observed prediction distribution，$P_p$ 是 prior bias，$P_d$ 是 debiased distribution。对 ill-defined attack $A(T)$，作者假设：

$$
P_p(d_i \mid A(T)) = P_o(d_i \mid A(T))
$$

BOLD 使用三类 attack 估计 bias projection：

- $A_{v=0}$：video 变为空/黑帧。
- $A_{q=0}$：question 置为空字符串。
- $A_{o=0}$：answer options 只保留 option IDs 或置空。

sample-specific prior 估计为：

$$
\tilde{P}_p(d_i \mid T) =
\operatorname{softmax}\left(\sum_j P_p(d_i \mid A_j(T))\right)
$$

再对 $K = k \times \lVert D \rVert$ 个样本平均得到 global prior $\tilde{P}_p(d_i)$。最后校准原始预测：

$$
P_d(d_i \mid T) =
\operatorname{softmax}\left(\log P_o(d_i \mid T) - \log \tilde{P}_p(d_i)\right)
$$

Weighted_BOLD 将 prior aggregation 扩展为：

$$
\tilde{P}_p(d_i \mid T) =
\operatorname{softmax}\left(\sum_j w_j P_p(d_i \mid A_j(T))\right)
$$

权重 $\{w_i\}$ 通过 5-fold cross-validation 与 COBYLA 优化得到，论文尝试 $0 \leq w_i \leq 1$ 与 $\lvert w_i \rvert \leq 1$ 两种约束；主文重点报告 $k=0.5$、positive weights 的结果。

Pipeline bullets:

1. 对原始 MCQA 数据运行模型，得到 $P_o(d_i \mid T)$。
2. 采样 $D_k$，分别构造 empty video、empty question、empty options 三个 decomposed datasets。
3. 在 decomposed datasets 上运行模型，估计每个 option ID 的 prior bias。
4. 将 sample prior 平均成 dataset-level global prior。
5. 对完整数据的 logits/probabilities 做 prior subtraction，输出校准后的 option prediction。

## Pipeline Figure

![[assets/pipeline_2410.14248.png]]

Caption: Decomposition approach in 3 steps: key-component decomposition, rearrangement into pairs, applying probability debiasing to the aggregated data.

Source: TeX includegraphics from `introduction.tex`, file `images/Decomposition.png`.

## Experiments

Datasets / Benchmarks:

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| NExT-QA | Video MCQA; causal, temporal, descriptive QA | Test | Accuracy, F1_mean, option-level bias metrics | 8564 QA pairs, 1000 videos, 5 options |
| NExT-GQA | Temporal localization subset/extension of NExT-QA | Test | Accuracy, F1_mean, option-level bias metrics | 4962 QA pairs, 971 videos, 5 options; used where timestamp labels are needed |
| STAR | Situated video reasoning: sequence, interaction, prediction, feasibility | Validation | Accuracy, F1_mean, option-level bias metrics | 7098 QA pairs, 914 videos, 4 options |
| Video-MME | Broad video understanding, including temporal, OCR, counting, spatial perception | Test | Accuracy, F1_mean, option-level bias metrics | 2700 QA pairs, 900 videos, 4 options |
| Perception Test | Video perception/reasoning: physics, semantics, abstraction, memory | Validation | Accuracy, F1_mean, option-level bias metrics | 7656 QA pairs, 3926 videos, 3 options |

Baseline inference results reported in the main empirical-analysis table:

| Model | NExT-QA Acc | NExT-QA F1_mean | STAR Acc | STAR F1_mean | Perception Test Acc | Perception Test F1_mean | Video-MME Acc | Video-MME F1_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Video-LLaMA | 40.85 | 40.85 | 36.59 | 31.86 | 41.59 | 37.19 | 32.67 | 28.15 |
| Video-LLaVA | 49.96 | 49.81 | 34.71 | 31.83 | 40.73 | 35.69 | 34.22 | 30.99 |
| SeViLA | 63.78 | 63.88 | 46.28 | 46.14 | 45.30 | 45.11 | 39.85 | 39.82 |

Main results for BOLD / Weighted_BOLD with $k=0.5$ and positive weights:

| Model | Dataset | Configuration | Accuracy | F1_mean | Recall_std | F1_std | JS_std |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Video-LLaMA | NExT-QA | BOLD | 45.88 (↑2.43%) | 42.15 (↑3.18%) | 22.98 (↓3.53%) | 15.53 (↓2.11%) | 15.55 (↓3.31%) |
| Video-LLaMA | NExT-QA | Weighted_BOLD | 45.91 (↑2.51%) | 42.20 (↑3.29%) | 22.83 (↓4.19%) | 15.51 (↓2.20%) | 15.56 (↓3.27%) |
| Video-LLaMA | STAR | BOLD | 37.19 (↑1.82%) | 33.02 (↑3.65%) | 22.29 (↓7.50%) | 14.55 (↓5.75%) | 14.58 (↓4.66%) |
| Video-LLaMA | STAR | Weighted_BOLD | 37.34 (↑2.24%) | 33.50 (↑5.16%) | 21.13 (↓12.30%) | 14.05 (↓8.98%) | 14.14 (↓7.54%) |
| Video-LLaMA | Perception Test | BOLD | 41.90 (↑1.24%) | 38.68 (↑4.01%) | 24.05 (↓11.11%) | 9.87 (↓13.45%) | 14.45 (↓10.01%) |
| Video-LLaMA | Perception Test | Weighted_BOLD | 42.06 (↑1.62%) | 39.36 (↑5.86%) | 21.80 (↓19.45%) | 9.11 (↓20.06%) | 13.02 (↓18.94%) |
| Video-LLaMA | Video-MME | BOLD | 32.73 (↑2.13%) | 29.23 (↑3.85%) | 19.29 (↓6.45%) | 11.96 (↓4.46%) | 13.10 (↓4.73%) |
| Video-LLaMA | Video-MME | Weighted_BOLD | 32.20 (↑0.47%) | 28.98 (↑2.94%) | 17.65 (↓14.38%) | 11.69 (↓6.56%) | 12.64 (↓8.04%) |
| Video-LLaVA | NExT-QA | BOLD | 51.81 (↑3.72%) | 51.71 (↑3.82%) | 13.27 (↓18.63%) | 2.67 (↓18.42%) | 4.58 (↓15.06%) |
| Video-LLaVA | NExT-QA | Weighted_BOLD | 52.15 (↑4.39%) | 52.04 (↑4.49%) | 12.72 (↓22.02%) | 2.62 (↓19.83%) | 4.49 (↓16.83%) |
| Video-LLaVA | STAR | BOLD | 37.21 (↑7.01%) | 35.76 (↑12.37%) | 18.28 (↓26.85%) | 4.97 (↓27.15%) | 4.54 (↓21.39%) |
| Video-LLaVA | STAR | Weighted_BOLD | 37.53 (↑7.94%) | 36.18 (↑13.69%) | 17.45 (↓30.15%) | 4.91 (↓28.03%) | 4.26 (↓26.24%) |
| Video-LLaVA | Perception Test | BOLD | 41.62 (↑2.22%) | 38.69 (↑8.40%) | 21.75 (↓20.90%) | 10.92 (↓25.97%) | 3.78 (↓28.40%) |
| Video-LLaVA | Perception Test | Weighted_BOLD | 41.95 (↑3.02%) | 39.46 (↑10.58%) | 19.73 (↓28.26%) | 10.24 (↓30.53%) | 3.40 (↓35.51%) |
| Video-LLaVA | Video-MME | BOLD | 34.70 (↑1.19%) | 32.79 (↑5.81%) | 18.19 (↓24.51%) | 6.16 (↓23.63%) | 3.84 (↓19.93%) |
| Video-LLaVA | Video-MME | Weighted_BOLD | 34.63 (↑0.97%) | 32.97 (↑6.38%) | 16.36 (↓32.07%) | 6.01 (↓25.43%) | 3.43 (↓28.50%) |
| SeViLA | NExT-QA | BOLD | 63.92 (↑0.02%) | 63.89 (↑0.02%) | 2.03 (↓5.47%) | 1.18 (↓10.40%) | 1.99 (↓0.17%) |
| SeViLA | NExT-QA | Weighted_BOLD | 63.93 (↑0.04%) | 63.91 (↑0.04%) | 1.99 (↓7.64%) | 1.19 (↓9.83%) | 1.99 (↓0.04%) |
| SeViLA | STAR | BOLD | 46.22 (↓0.12%) | 46.10 (↓0.08%) | 4.13 (↓7.46%) | 2.26 (↓1.78%) | 2.10 (↓6.64%) |
| SeViLA | STAR | Weighted_BOLD | 46.20 (↓0.18%) | 46.08 (↓0.13%) | 4.01 (↓10.17%) | 2.20 (↓4.36%) | 2.07 (↓8.20%) |
| SeViLA | Perception Test | BOLD | 45.32 (↑0.06%) | 45.18 (↑0.16%) | 5.18 (↓16.61%) | 2.95 (↓2.43%) | 1.30 (↓18.42%) |
| SeViLA | Perception Test | Weighted_BOLD | 45.31 (↑0.03%) | 45.20 (↑0.21%) | 4.56 (↓26.58%) | 2.83 (↓6.43%) | 1.08 (↓31.92%) |
| SeViLA | Video-MME | BOLD | 40.19 (↑0.84%) | 40.17 (↑0.88%) | 4.11 (↓12.03%) | 1.41 (↓16.19%) | 0.73 (↓12.52%) |
| SeViLA | Video-MME | Weighted_BOLD | 40.04 (↑0.46%) | 40.03 (↑0.54%) | 3.78 (↓19.14%) | 1.44 (↓14.60%) | 0.69 (↓17.22%) |

Ablations / Analysis:

| Component | Modification | Purpose / Bias Signal |
| --- | --- | --- |
| Video | Correct Frames | 只给包含答案的 frames，测试去除无关视觉信息是否提升 performance；仅适用于带 timestamp 的 NExT-GQA 与 STAR |
| Video | Empty Frames | 用黑帧替代 video，观察无视觉信息时模型是否靠 option position 或语言 prior 猜测 |
| Question | Rephrased Questions | 用 Llama3 生成 rephrasing，测试 wording/token bias 是否影响选择 |
| Question | Empty Questions | 清空 question，测试模型能否仅靠 video 和 options 推断答案，以及 position bias 是否显现 |
| Answer Options | Answer Shuffling | 随机打乱 options，测试模型是否对 answer order 鲁棒 |
| Answer Options | Correct Answer in Each Option | 把正确答案固定放入每个位置，观察该位置 selection rate 是否上升 |
| Answer Options | Correct Answer with Shuffling | 固定正确答案位置并打乱其他 options，测试 position preference 与 content signal 的组合 |
| Answer Options | Additional Empty Option | 在末尾加入 empty option，检查模型是否过拟合固定 option count |
| Answer Options | All Identical Answers | 所有 options 内容相同，若不接近 uniform 则说明存在 blind guessing / position bias |
| Answer Options | All Correct Answers | 所有 options 都正确，理论上也应接近 uniform |
| Answer Options | Empty Answers | options 为空，模型只能根据 option ID 和位置选择，是最直接的 position-bias probe |

Training / Compute:

| Item | Value |
| --- | --- |
| Video-LLaMA setting | 7B model; 8 uniformly sampled frames; number of beams 2; temperature 0.8; up to 30 attempts to output parseable answer ID |
| Video-LLaVA setting | Video-LLaVA-7B; 8 uniformly sampled frames; temperature 1; half-precision via Torch autocast |
| SeViLA setting | Localizer samples 32 frames and selects 4 key frames; Localizer/Answerer use Flan-T5; MCQA-specific answer mapping |
| Debiasing budget | $K = k \times \lVert D \rVert$; main result uses $k=0.5$ |
| Weighted_BOLD optimization | 5-fold cross-validation; COBYLA; constraints $0 \leq w_i \leq 1$ or $\lvert w_i \rvert \leq 1$ |

## Limitations & Caveats

- BOLD 假设 ill-defined task 下合理模型应产生 uniform distribution；如果 dataset 本身的 correct-answer positions 并不均匀，或 task 有合理的非均匀先验，JS-based bias 可能会低估或高估问题。
- 三个 decomposition directions（empty video、empty question、empty options）不一定穷尽所有 bias projection；作者也承认 latent space 中可能有更优方向。
- 当前 evaluation 主要验证校准后在原始 datasets 上的表现，没有系统覆盖所有 11 种 modifications 的 post-calibration 结果。
- SeViLA 的 bias profile 与 Video-LLaMA/Video-LLaVA 很不同：它是 MCQA-specific，且使用 argmax；因此 BOLD 对其 performance 提升很小，STAR 上甚至轻微下降。
- 论文不同表格中的部分 baseline 口径可能不完全一致；本 note 保留各表作者报告的原始数值，没有跨表重算 delta。

## Concrete Implementation Ideas

1. 在自己的 video MCQA eval pipeline 中增加 three-plane probes：empty frames、empty question、empty options，并记录 option distribution。
2. 对每个 model-dataset pair 先估计 global option prior，再把原始 logits 做 $-\log \tilde{P}_p(d_i)$ 校准，作为 cheap post-processing baseline。
3. 将 Recall_std、F1_std、JS_std 加入评估 dashboard，不只看 aggregate Accuracy，尤其关注低编号/高编号 option 的 recall gap。
4. 对 prompt 做 answer-ID normalization，例如统一使用 a0/a1/a2 而非 A/B/C，减少常见 token bias 后再测 position bias。
5. 在 release benchmark 时强制检查 answer option balance，并公开 option-position distribution，避免评测集本身把模型推向某个位置。

## Open Questions / Follow-ups

- BOLD 的 global prior 是否能跨 dataset 或跨 question type transfer，还是必须每个 dataset 单独估计？
- 对 closed-source VLM 或只返回 text 而不返回 logits/probabilities 的 API 模型，如何稳健近似 $P_o(d_i \mid T)$？
- 如果 answer option 数量变化较大，global prior 是否需要按 option count 分桶估计？
- Weighted_BOLD 只优化 Recall_std 时可能损害其他 metrics；是否可以做 multi-objective optimization，同时约束 Accuracy/F1 不下降？
- 对 long video benchmark，empty frames 与 correct frames 的 bias projection 是否会随视频长度、temporal localization 难度而系统变化？

## Citation

```bibtex
@misc{loginova2024addressingblindguessing,
  title = {Addressing Blind Guessing: Calibration of Selection Bias in Multiple-Choice Question Answering by Video Language Models},
  author = {Loginova, Olga and Bezrukov, Oleksandr and Shekhar, Ravi and Kravets, Alexey},
  year = {2024},
  eprint = {2410.14248},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  doi = {10.48550/arXiv.2410.14248},
  url = {https://arxiv.org/abs/2410.14248}
}
```

arXiv:2410.14248 [cs.CL]. Submitted on 2024-10-18; last revised version v2 on 2025-05-30.
