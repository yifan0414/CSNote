---
title: Confidence-guided Refinement Reasoning for Zero-shot Question Answering
authors:
  - Youwon Jang
  - Woo Suk Choi
  - Minjoon Jung
  - Minsu Lee
  - Byoung-Tak Zhang
conference: EMNLP 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2509.20750
pdf_link: "[[assets/paper_2509.20750.pdf]]"
cover: "[[_assets/images/pipeline_2509.20750.png]]"
updated: 2026-05-10
tags:
  - paper/arxiv
  - vlm
  - video-llm
  - reasoning
  - video-qa
  - long-video
status: unread
priority:
rating:
topics:
  - MLLM
code: ""
---

# TL;DR

- C2R（Confidence-guided Refinement Reasoning）是一个 training-free QA 推理框架，适用于 text-only、image QA 和 video QA；它不训练新模型，而是在 inference time 利用模型自己的 confidence score 做答案选择。
- 核心问题是：sub-QA 不总是有帮助。错误或不相关的 sub-question / sub-answer 会让模型被噪声带偏，而且还可能造成 **confidence inflation**。
- 方法先生成 $N=5$ 个 sub-QAs，再由 Refiner 抽取每条 reasoning path 的 $M=2$ 个 sub-QAs，形成 $K=4$ 条候选路径；最后 Answer Selector 在 base answer 和 refined answer 之间按阈值选择。
- 主结果显示 C2R 在 Qwen2.5、LLaVA-Onevision、Gemma 3、Qwen2 和 GPT-4o 上基本都带来提升；Qwen2.5-VL-7B 上从 MMLU 到 EgoSchema 的提升为 +1.7 到 +5.7 个点。
- 论文最有价值的洞察不是“多步推理一定更好”，而是要把 sub-QA 当作有风险的中间证据，并用 calibrated confidence / threshold 来避免盲目信任 refined answer。

# Key Contributions

- 提出 **Confidence-guided Refinement Reasoning (C2R)**：一个 model-agnostic、training-free 的 QA wrapper，可以接在现有 autoregressive LLM / VLM 上，只要求能读到生成 token 的概率或等价 confidence。
- 用 **Generator / Refiner / Answer Selector** 三段式设计替代“生成所有 sub-QA 后直接喂回模型”的 naive multi-step reasoning。
- 将 confidence 定义为答案 token 序列中最低的 token probability：$c(\hat{A})=\min_i p_i$。作者认为最低概率 token 往往暴露了生成链条中最脆弱的点。
- 系统比较了 SingleSubQA、EverySubQA、LLM-as-judge 式 sub-QA verification、CoT / CoT-SC 与 C2R，说明直接验证 intermediate steps 并不稳定。
- 发现并分析 **confidence inflation**：使用 sub-QAs 后 refined answer 的平均 confidence 会明显上升，即使 accuracy 并没有同步提升；因此需要 $\tau_2$ 来校正 base/refined confidence 分布差异。

# Method

C2R 的输入是 content $V$（可以是 image / video，也可以没有视觉输入）和主问题 $Q$。对 multiple-choice QA，还会把 answer options 一起输入模型。

- **Base inference**：先直接得到 base answer $\hat{A}_\text{base}=f(V,Q)$，并计算 $c(\hat{A}_\text{base})$。
- **Early exit**：如果 $c(\hat{A}_\text{base})\ge\tau_1$，直接返回 base answer，避免简单问题被过度推理干扰。
- **Generator**：当 base confidence 不够高时，生成 $N$ 个 sub-questions，并分别回答得到 sub-QA bank：$S_{qa}=\{(q_i,a_i)\}_{i=1}^N$。
- **Refiner**：从 $S_{qa}$ 中抽取 $K$ 个不同 subset；每个 subset 含 $M$ 个不重复 sub-QAs，作为一条 reasoning path 的额外 context $s_j$。
- **Candidate generation**：对每条 path 生成候选答案 $\hat{A}_j=f(V,Q\mid s_j)$，并计算 confidence；取最高 confidence 的候选为 $\hat{A}_\text{refined}$。
- **Answer Selector**：只有当 $c(\hat{A}_\text{refined})\ge c(\hat{A}_\text{base})+\tau_2$ 时才接受 refined answer，否则回退到 base answer。

默认实验设置：$N=5$，$M=2$，$K=4$。阈值 $\tau_1$ 和 $\tau_2$ 在 validation set 上 grid search；作者也报告了固定阈值 $\tau_1=0.7,\tau_2=0.1$ 的鲁棒性。

# Pipeline Figure

![[_assets/images/pipeline_2509.20750.png]]

Caption: C2R 的 overview。给定 content $V$ 和 main question $Q$，Generator 构建 $N$ 个 sub-QAs；Refiner 组合出 $K$ 个 subset，每个 subset 含 $M$ 个 sub-QAs，用来生成带 confidence score 的 answer candidates；Answer Selector 最后在 $\hat{A}_\text{base}$ 与 $\hat{A}_\text{refined}$ 之间，用 $\tau_1$ 和 $\tau_2$ 选择 final answer。原 caption 还说明 Vision-Language Model (VLM) 是 frozen 的。

Source: TeX includegraphics from `sec/2_related.tex`, original asset `figures/framework.pdf`; rendered with `pdftoppm -cropbox` at 250 dpi. Original vector copy: `assets/pipeline_2509.20750.pdf`.

# Experiments

## Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| MMLU | Text-only QA | validation set | Accuracy | 57 个 academic / professional tasks，测试 world knowledge 与 problem solving。 |
| MMLU-Pro | Text-only QA | test set | Accuracy | validation 只有 70 个样本，作者改用 test set；10 个 answer choices，更偏 complex reasoning。 |
| StrategyQA | Text-only QA | training set | Accuracy | 由于 leaderboard 无法提交，作者报告 training set；implicit multi-hop reasoning。 |
| MMMU | ImageQA | validation set | Accuracy | college-level multimodal questions，覆盖 Science、Engineering、Art & Design 等学科。 |
| EgoSchema | VideoQA | validation set | Accuracy | long-form egocentric video QA，测试 extended temporal context 与复杂行为理解。 |

## Training / Compute

| Item | Value |
| --- | --- |
| Framework | Training-free inference-time wrapper |
| Backbones | Qwen2.5-VL-7B, Gemma-3-4B, LLaVA-Onevision-7B, Qwen2-VL-2B, GPT-4o |
| Decoding | Greedy search |
| Main hyperparameters | $N=5$, $M=2$, $K=4$ |
| Confidence score | Minimum selected-token probability over generated answer tokens |
| Threshold tuning | Grid search step 0.1; $\tau_1\in[0,1]$, $\tau_2\in[-1,1]$ |
| Video sampling | 1 fps; videos longer than 32 seconds use 32 uniformly sampled frames |
| Hardware | Single A6000 GPU except closed-source model experiments |
| GPT-4o setting | `gpt-4o-2024-08-06` with `logprobs` enabled |

## Main Results

Scores are reported as accuracy / benchmark score in the paper. Bold and underline follow the source table: **best**, <u>second-best</u> within a comparable block.

| Backbone | Size | Reasoning Method | N | M | K | MMLU | MMLU-Pro | StrategyQA | MMMU | EgoSchema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5 | 7B | Baseline | - | - | - | 67.1 | 38.6 | 62.6 | <u>50.2</u> | 68.0 |
| Qwen2.5 | 7B | SingleSubQA | 1 | 1 | 1 | 67.5 | 42.9 | 62.6 | 47.6 | <u>69.2</u> |
| Qwen2.5 | 7B | EverySubQA | 5 | 5 | 1 | <u>67.7</u> | 42.6 | <u>65.3</u> | 47.6 | 69.0 |
| Qwen2.5 | 7B | SubQAJudge (sub-A) | 5 | 2 | 1 | 67.3 | <u>43.2</u> | 64.5 | 49.4 | 67.0 |
| Qwen2.5 | 7B | **C2R (Ours)** | 5 | 2 | 4 | **69.2** | **44.3** | **65.7** | **51.9** | **71.5** |
| Qwen2.5 | 7B | Delta vs. Baseline | - | - | - | +2.1 | +5.7 | +3.1 | +1.7 | +3.5 |
| LLaVA-Onevision | 7B | Baseline | - | - | - | <u>66.2</u> | 35.7 | 64.5 | 45.1 | 43.0 |
| LLaVA-Onevision | 7B | SingleSubQA | 1 | 1 | 1 | 64.3 | 36.6 | 67.8 | 44.1 | 40.2 |
| LLaVA-Onevision | 7B | EverySubQA | 5 | 5 | 1 | 63.4 | <u>37.0</u> | 67.6 | 46.1 | 39.8 |
| LLaVA-Onevision | 7B | SubQAJudge (sub-A) | 5 | 2 | 1 | 65.1 | 36.9 | <u>68.2</u> | <u>47.2</u> | <u>45.2</u> |
| LLaVA-Onevision | 7B | **C2R (Ours)** | 5 | 2 | 4 | **67.3** | **38.4** | **68.3** | **47.4** | **46.0** |
| LLaVA-Onevision | 7B | Delta vs. Baseline | - | - | - | +1.1 | +2.7 | +3.8 | +2.3 | +3.0 |
| Gemma 3 | 4B | Baseline | - | - | - | 58.9 | 27.3 | 45.9 | 40.1 | 50.5 |
| Gemma 3 | 4B | **C2R (Ours)** | 5 | 2 | 4 | **60.0** | **30.5** | **50.1** | **42.1** | **53.2** |
| Gemma 3 | 4B | Delta vs. Baseline | - | - | - | +1.1 | +3.2 | +4.2 | +2.0 | +2.7 |
| Qwen2 | 2B | Baseline | - | - | - | 50.0 | 23.6 | **55.0** | 41.4 | 56.8 |
| Qwen2 | 2B | **C2R (Ours)** | 5 | 2 | 4 | **50.8** | **24.7** | **55.0** | **42.4** | **61.0** |
| Qwen2 | 2B | Delta vs. Baseline | - | - | - | +0.8 | +1.1 | +0.0 | +1.0 | +4.2 |
| GPT-4o | - | Baseline | - | - | - | 85.0 | - | - | 56.1 | 75.0 |
| GPT-4o | - | **C2R (Ours)** | 5 | 2 | 4 | **86.2** | - | - | **58.3** | **78.2** |
| GPT-4o | - | Delta vs. Baseline | - | - | - | +1.2 | - | - | +2.2 | +3.2 |

关键读法：SingleSubQA / EverySubQA 有时提升，但不稳定，尤其会在 MMMU / EgoSchema 上掉分；C2R 的优势来自“多路径探索 + confidence selector”，而不是单纯加入更多 sub-QAs。

## Ablations / Analysis

### Number of curated sub-QAs $M$ (Qwen2.5-VL, $N=5$)

| M | MMLU | MMMU | EgoSchema |
| --- | --- | --- | --- |
| Baseline | 67.1 | 50.2 | 68.0 |
| 1 | +1.3 | +0.9 | +1.0 |
| 2 | +2.1 | **+1.7** | **+3.5** |
| 3 | **+2.2** | +1.1 | +3.0 |
| 4 | +2.1 | +1.4 | +1.5 |

作者选择 $M=2$，因为它在 multimodal benchmarks 上最好，且在 MMLU 上与 $M=3$ 几乎持平。直觉上，$M$ 太小可能信息不足，$M$ 太大更容易把错误 sub-QA 带进 context。

### Number of reasoning paths $K$ (Qwen2.5-VL)

| Setting | K | MMLU | MMMU | EgoSchema |
| --- | --- | --- | --- | --- |
| Baseline | - | 67.1 | 50.2 | 68.0 |
| C2R | 1 | +1.6 | +1.1 | +2.2 |
| C2R | 2 | +1.7 | +1.2 | +2.5 |
| C2R | 4 | +2.1 | **+1.7** | **+3.5** |
| C2R | 8 | **+2.2** | **+1.7** | +3.2 |

$K=4$ 是论文主实验的效率/效果折中。$K=8$ 在 MMLU 略好、MMMU 持平，但 EgoSchema 下降到 +3.2。

### Visual input impact

| Model | Method | MMMU Blind | MMMU Std. | EgoSchema Blind | EgoSchema Std. |
| --- | --- | --- | --- | --- | --- |
| Qwen2.5-VL-7B | Baseline | 38.9 | 50.2 | 27.3 | 68.0 |
| Qwen2.5-VL-7B | **C2R (Ours)** | 41.0 | 51.9 | 30.3 | 71.5 |
| Qwen2.5-VL-7B | Delta | +2.1 | +1.7 | +3.0 | **+3.5** |
| LLaVA-Onevision-7B | Baseline | 43.2 | 45.1 | 35.5 | 42.0 |
| LLaVA-Onevision-7B | **C2R (Ours)** | 43.4 | 47.4 | 38.0 | 45.8 |
| LLaVA-Onevision-7B | Delta | +0.2 | **+2.3** | +2.5 | **+3.8** |
| Gemma-3-4B | Baseline | 34.0 | 40.1 | 23.3 | 50.5 |
| Gemma-3-4B | **C2R (Ours)** | 35.9 | 42.1 | 24.5 | 53.2 |
| Gemma-3-4B | Delta | +1.9 | **+2.0** | +1.2 | **+2.7** |

除了 Qwen2.5 的 MMMU 外，大多数 standard setting 的增益比 blind setting 更大，说明 sub-QAs 不是只在语言侧“自我解释”，而是能利用 visual content。

### CoT / cost comparison (Qwen2.5-VL)

| Method | avg. # path | MMLU | MMMU | EgoSchema |
| --- | --- | --- | --- | --- |
| Baseline | 1 | 67.1 | 50.2 | 68.0 |
| CoT | 1 | 65.3 | 49.8 | 62.3 |
| CoT-SC | 5 | 68.3 | <u>51.9</u> | 67.0 |
| CoT-SC | 40 | **71.0** | **56.6** | <u>69.0</u> |
| **C2R (Ours)** | 2.3 | <u>69.2</u> | <u>51.9</u> | **71.5** |
| **C2R (Ours*)** | 1.7 | <u>69.2</u> | 51.8 | **71.5** |

| Method | avg. # path | Input / Generate tokens | Relative cost |
| --- | --- | --- | --- |
| Baseline | 1 | 132 / 13 | 1 |
| CoT | 1 | 168 / 286 | 7.2 |
| CoT-SC | 5 | 830 / 1427 | 35.7 |
| **C2R (Ours)** | 2.3 | 708 / 84 | 5.7 |
| **C2R (Ours*)** | 1.7 | 442 / 52 | 3.5 |

`Ours*` 表示当 refined answer confidence 超过 0.85 时提前停止继续探索。作者报告这能降低约 39% 成本，同时几乎保持性能。

### Fixed threshold robustness

| Model | MMLU | MMMU | EgoSchema |
| --- | --- | --- | --- |
| Baseline | 67.1 | 62.6 | 68.0 |
| C2R (Optimal $\tau$) | 69.2 | 65.7 | 71.5 |
| C2R (Fixed $\tau$) | 69.1 | 65.6 | 71.2 |

Caveat: 原文这张 fixed-threshold 表的第二列标为 MMMU，但数值 62.6 / 65.7 与主表中的 StrategyQA 列一致，而不是 MMMU 列；这里保留原表数值，不额外改写为作者未明说的列名。

# Limitations & Caveats

- C2R 降低了使用低质量 sub-QAs 的概率，但不直接阻止低质量 sub-QAs 被生成；如果所有候选路径都被噪声污染，selector 仍可能失败。
- 论文只探索了两层结构：main question → sub-QA → refined answer；更深的 multi-level refinement 没有实验。
- 方法依赖模型可提供 token probability / logprobs。对不暴露 logprob 的 API 或 calibration 很差的模型，需要替代 confidence estimator。
- 阈值 $\tau_1,\tau_2$ 需要 validation tuning；固定阈值表现接近 optimal，但跨任务迁移仍需要更系统的证据。
- StrategyQA 报告 training set，MMLU-Pro 报告 test set；不同 benchmark 的 split choice 不是完全统一，比较时要留意。
- Fixed-threshold 表疑似存在列名/数值不一致，见 Experiments 中的 caveat。

# Concrete Implementation Ideas

- 做一个 `C2RSelector` wrapper：输入 `model.generate_with_logprobs(V,Q)`，输出 `(answer, confidence, trace)`，trace 记录 base answer、sub-QA bank、每条 path 的 subset、candidate answer 与 confidence。
- 在现有 VLM QA pipeline 中先实现 cheap mode：$N=5,M=2,K=4$，默认 $\tau_1=0.7,\tau_2=0.1$；再按 dataset 做小规模 calibration。
- 对长视频 QA，把 C2R 与 keyframe / segment selector 结合：先减少 visual context，再在 selected frames 上生成 sub-QAs，避免 sub-QA 生成阶段读入太长视频。
- 把 confidence inflation 作为监控指标：记录 $c(\hat{A}_\text{refined})-c(\hat{A}_\text{base})$ 的分布，并单独审查 high-confidence wrong refined answers。
- 在无法获取 token logprob 的模型上，可实验替代分数：self-rated confidence、answer consistency、small verifier model，但要复现论文中的 calibration analysis，避免把 verifier bias 当成可靠信号。

# Open Questions / Follow-ups

- 如果 sub-QA generator 本身 prompt-tuned 或轻量 fine-tuned，C2R 的 gains 是否会更稳定，还是会进一步放大 confidence inflation？
- $\tau_1,\tau_2$ 能否用无监督 calibration 或在线统计自动估计，而不是依赖 validation set？
- 对 open-ended generation、math proof、medical QA 这类答案空间更复杂的任务，minimum token probability 是否仍然是好 confidence？
- 更深层的 sub-QA tree / graph 是否值得做，还是成本和误差传播会抵消收益？
- 当 visual evidence 很弱或 retrieval/frame selection 错误时，C2R 是会更快回退到 base answer，还是会被 refined path 的 confidence inflation 误导？

# Citation

Jang, Youwon, Woo Suk Choi, Minjoon Jung, Minsu Lee, and Byoung-Tak Zhang. 2025. "Confidence-guided Refinement Reasoning for Zero-shot Question Answering." arXiv:2509.20750v1.

```bibtex
@article{jang2025confidenceguided,
  title={Confidence-guided Refinement Reasoning for Zero-shot Question Answering},
  author={Jang, Youwon and Choi, Woo Suk and Jung, Minjoon and Lee, Minsu and Zhang, Byoung-Tak},
  journal={arXiv preprint arXiv:2509.20750},
  year={2025},
  eprint={2509.20750},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2509.20750}
}
```
