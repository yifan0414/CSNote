---
title: "Video-MME-v2: Towards the Next Stage in Benchmarks for Comprehensive Video Understanding"
authors: ["Chaoyou Fu", "Haozhi Yuan", "Yuhao Dong", "Yi-Fan Zhang", "Yunhang Shen", "Xiaoxing Hu", "Xueying Li", "Jinsen Su", "Chengwu Long", "Xiaoyao Xie", "Yongkang Xie", "Xiawu Zheng", "Xue Yang", "Haoyu Cao", "Yunsheng Wu", "Ziwei Liu", "Xing Sun", "Caifeng Shan", "Ran He"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2604.05015"
pdf_link: "[[assets/paper_2604.05015.pdf]]"
cover: "[[assets/pipeline_2604.05015.png]]"
updated: 2026-04-27
tags: ["paper/arxiv", "benchmark", "dataset", "evaluation", "video-llm", "long-video", "temporal-reasoning"]
status: "unread"
priority:
rating:
topics: ["Dataset & Benchmark"]
code: ""
---

## TL;DR

- Video-MME-v2 是一个面向 video MLLMs 的高难度综合 benchmark，强调 robustness 和 faithfulness，而不是只看单题 accuracy。
- 数据集包含 800 个视频、3,200 个问题；每个视频配 4 个相关问题，每题 8 个选项，随机猜测概率降到 12.5%。
- 核心设计是 progressive tri-level hierarchy：Level 1 做 Visual Information Aggregation，Level 2 做 Temporal Dynamics，Level 3 做 Complex Reasoning。
- 论文提出 group-based non-linear evaluation：Consistency group 用二次惩罚压低零散猜中的分数，Coherence group 用 first-error truncation 检查推理链是否连贯。
- 实验显示最强模型 Gemini-3-Pro 的 Non-Lin Score 为 49.4，而 Human Expert 为 90.7；传统 Avg Acc 会明显高估模型能力。
- Thinking mode 对字幕/文本线索依赖很强：有 subtitle/audio 时更容易提升，无 textual cues 时部分模型会退化。

## Key Contributions

- 提出 Video-MME-v2，用 800 个新近公开视频和 3,200 个高质量多选问题，构建一个更难、更贴近真实视频理解的 evaluation benchmark。
- 设计三层 progressive capability hierarchy，把能力从基础视觉/音频聚合推进到 temporal dynamics，再到 narrative、social、physical world 等复杂推理。
- 引入 group-based evaluation strategy，将问题组织成 capability consistency 和 reasoning coherence 两类 group，用相关问题共同衡量模型是否真的稳定理解视频。
- 提出 Non-Lin Score：Consistency groups 使用 $(\mathcal{N}/4)^2$，Coherence groups 使用 first-error truncation，避免模型靠孤立猜中或后验撞对拿高分。
- 通过 12 annotators、50 reviewers、3,300 human-hours 和最多 5 轮质量保证，控制语言捷径、数据污染、弱 distractor 和主观歧义。

## Method

Video-MME-v2 的方法更像一套 benchmark construction + evaluation protocol：

1. **Video curation**：从互联网收集新近视频，超过 80% 发布于 2025 年或之后，接近 40% 发布于 2025 年 10 月之后；同时人工排除经典影视和头部网红内容，降低 pretraining leakage 风险。
2. **Capability hierarchy**：把任务分成 Level 1 Visual Information Aggregation、Level 2 Temporal Dynamics、Level 3 Complex Reasoning，共 12 个 sub-categories 和 30+ task types。
3. **Group-QA design**：每个视频有 4 个相关问题。Consistency groups 检查同一能力在不同方面/粒度上的稳定性；Coherence groups 检查从线索定位到最终结论的多步推理链。
4. **Option construction**：每题 8 个选项，并要求至少一个 adversarial distractor；选项长度被控制，减少长度偏置和语言捷径。
5. **Quality assurance**：使用 Gemini-3-Pro text-only baseline 过滤只靠文本能答的问题；再做三轮 cross-review、independent blind testing 和 Correction-Reverification。

核心指标如下：

$$
\mathrm{AvgAcc} = \frac{1}{|\mathcal{Q}|}\sum_{q \in \mathcal{Q}} \mathbb{I}[\hat{y}_q = y_q].
$$

$$
\mathrm{Overall} = \frac{1}{|\mathcal{G}|}\sum_{g \in \mathcal{G}} S(g).
$$

其中 consistency group 若 4 个相关问题中答对 $\mathcal{N}$ 个，则 $S(g)=(\mathcal{N}/4)^2$；coherence group 从第一个推理步骤开始计分，一旦出现错误，后续即使答对也不计入最长正确前缀。

```text
for each video group:
  evaluate four linked QA items
  record the correctness pattern
  if consistency group:
    reward only stable correctness across related questions
  if coherence group:
    keep only the correct prefix before the first error
average group scores into Non-Lin Score
```

## Pipeline Figure

![[assets/pipeline_2604.05015.png]]

Caption: Left: The three-level capability hierarchy of Video-MME-v2: distribution of capability dimensions across Level 1 (information retrieval and aggregation), Level 2 (temporal understanding), and Level 3 (complex reasoning). Right: Models are ranked by their group-based non-linear scores, while average accuracy is provided for reference only. Due to API limitations, Gemini models are tested by extracting and compressing video frames to 60M, while GPT-5 is tested with an input of 50 frames.

Source: TeX includegraphics from `secs/3_benchmark.tex`, using `figs/teaser.pdf`; converted to PNG with PDF crop bounds for Obsidian embedding.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME-v2 | Comprehensive video understanding for video MLLMs; includes information aggregation, temporal dynamics, and complex reasoning | 800 videos / 3,200 QA pairs; paper does not report a train/dev/test split | Non-Lin Score, Avg Acc, Level 1/2/3, Consistency, Coherence | 每个视频 4 个 linked questions，每题 8 options；12 annotators、50 reviewers、3,300 human-hours；视频平均 10.4 min，99% under 20 min，53% under 10 min |
| Level 1 | Visual Information Aggregation | Same benchmark | Level 1 score | Visual Recognition, Cross-Modal Consistency, Basic Counting & Calculation |
| Level 2 | Temporal Dynamics | Same benchmark | Level 2 score | Action & Motion Analysis, Sequential Ordering, Causal Reasoning |
| Level 3 | Complex Reasoning | Same benchmark | Level 3 score | Narrative Understanding, Social Dynamics, Physical World Reasoning |

### Main Results

下表保留 leaderboard 中的关键/代表性行；完整 leaderboard 见本地 PDF。排序依据是 paper 的 `w. sub` Non-Lin Score。

| Group | Method | Frames | Non-Lin w. sub | Non-Lin wo sub | Level 1 w. sub | Level 2 w. sub | Level 3 w. sub | Consistency w. sub | Coherence w. sub | Avg Acc w. sub |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Human Baseline | Human Expert | - | **90.7** | - | **94.8** | **91.1** | **87.9** | **91.7** | **88.9** | **94.9** |
| Commercialization | Gemini-3-Pro | 1fps | **49.4** | **38.2** | **64.0** | **50.0** | **40.6** | **50.8** | **47.0** | **66.1** |
| Commercialization | Doubao-Seed-2.0-Pro-260215 | 1fps | 43.3 | 35.2 | 54.4 | 47.0 | 34.1 | 43.7 | 42.5 | 60.5 |
| Commercialization | Gemini-3-Flash | 1fps | 42.5 | 32.9 | 58.3 | 44.8 | 31.7 | 44.9 | 38.2 | 61.1 |
| Commercialization | MiMo-v2-Omni | 1fps | 38.6 | 29.9 | 52.6 | 43.1 | 27.4 | 39.7 | 36.6 | 56.1 |
| Commercialization | GPT-5 | 50 | 37.0 | 26.4 | 44.5 | 39.1 | 31.1 | 37.4 | 36.3 | 55.6 |
| Commercialization | Kimi-K2.5 | 64 | 36.1 | 27.3 | 44.3 | 40.0 | 28.5 | 36.0 | 36.2 | 54.4 |
| Open-Source Instruct | Qwen3-VL-235B-A22B-Instruct | 64 | **25.0** | 16.5 | **30.7** | 25.2 | 21.6 | **25.0** | 25.0 | **43.3** |
| Open-Source Instruct | Qwen3.5-397B-A17B-Instruct | 64 | 24.5 | **16.9** | 27.3 | **25.9** | **21.9** | 23.9 | **25.7** | 42.1 |
| Open-Source Instruct | Qwen3.5-27B-Instruct | 64 | 23.9 | 14.0 | 28.9 | 23.2 | 21.5 | 23.4 | 24.8 | 41.9 |
| Open-Source Thinking | Qwen3.5-397B-A17B-Think | 512 | **39.1** | **30.3** | **50.3** | **41.8** | **30.7** | **39.0** | **39.4** | **55.9** |
| Open-Source Thinking | Qwen3.5-27B-Think | 512 | 31.4 | 19.5 | 34.4 | 36.4 | 26.2 | 31.5 | 31.3 | 49.6 |
| Open-Source Thinking | Qwen3-VL-235B-A22B-Think | 512 | 28.1 | 19.0 | 32.6 | 30.3 | 23.9 | 28.3 | 27.8 | 47.2 |
| Open-Source Thinking | Qwen3.5-9B-Think | 512 | 26.2 | 19.5 | 30.5 | 30.1 | 20.9 | 25.8 | 26.8 | 44.5 |
| Open-Source Instruct | LLaVA-Video-7B-Qwen2 | 64 | 9.7 | 7.2 | 15.9 | 7.4 | 7.5 | 9.9 | 9.0 | 24.0 |

主要实验结论：

- Human Expert 的 Non-Lin Score 是 90.7，而最强模型 Gemini-3-Pro 只有 49.4，差距为 41.3 points。
- 从 Level 1 到 Level 3，模型表现呈明显递减；论文将其解释为 perception 和 temporal grounding 的错误会向 complex reasoning 传播。
- Commercialization models 整体领先。Gemini-3-Pro 的 49.4 明显高于最佳开源模型 Qwen3.5-397B-A17B-Think 的 39.1。
- Native audio 对 omni models 带来明显收益：Gemini-3-Pro 从 wo sub 38.2 提升到 w. sub 49.4，MiMo-v2-Omni 从 29.9 提升到 38.6。
- 同一模型增加 frame/context 能提升表现：Qwen3.5-397B-A17B-Think 从 64 frames 的 30.6 提升到 512 frames 的 39.1。

### Ablations / Analysis

**Avg Acc vs. Non-Lin Score.** 这张表展示传统 per-question accuracy 如何高估能力：模型可能单题答对较多，但在同一 group 内无法稳定连续答对。

| Model | Avg Acc (%) | Non-Lin Score | Non-Lin / Avg Acc |
| --- | ---: | ---: | ---: |
| Gemini-3-Pro | 66.1 | 49.4 | 74.7% |
| Doubao-Seed-2.0-Pro-260215 | 60.5 | 43.3 | 71.6% |
| Gemini-3-Flash | 61.1 | 42.5 | 69.6% |
| Qwen3.5-397B-A17B-Think (512) | 55.9 | 39.1 | 69.9% |
| MiMo-v2-Omni | 56.1 | 38.6 | 68.8% |
| GPT-5 | 55.6 | 37.0 | 66.5% |
| Qwen3.5-27B-Think (512) | 49.6 | 31.4 | 63.3% |
| LLaVA-Video-7B-Qwen2 | 24.0 | 9.7 | 40.4% |

**Capability profiling.** 论文把强视频理解抽象成 C1/C2/C3 三类能力：C1 = omni-modal joint perception，C2 = long-context/long-range temporal modeling，C3 = complex reasoning / Thinking。

| Model | Non-Lin Score | C1 | C2 | C3 |
| --- | ---: | --- | --- | --- |
| Gemini-3-Pro | 49.4 | Yes | Yes | Yes |
| Gemini-3-Flash | 42.5 | Yes | Yes | Yes |
| Qwen3.5-397B-A17B-Think (512) | 39.1 | No | Yes | Yes |
| MiMo-v2-Omni | 38.6 | Yes | Yes | Yes |
| Qwen3.5-397B-A17B-Think (64) | 30.6 | No | Yes | Yes |
| Qwen3-VL-235B-A22B-Think (512) | 28.1 | No | Yes | Yes |
| Qwen3-Omni-30B-A3B-Think | 19.5 | Yes | Yes | Yes |
| Qwen3-Omni-30B-A3B-Instruct | 17.1 | Yes | Yes | No |

**Thinking mode effect.** 论文没有给出完整 Markdown 表格，但在正文中报告了以下关键数值：

| Model / Setting | Reported change | Notes |
| --- | ---: | --- |
| Qwen3.5-122B-A10B-Think (64 frames) | +3.8 / +5.8 | 分别为 wo. subtitle / w. subtitle；subtitle 放大 Thinking mode 的收益 |
| Qwen3-VL-8B | -0.6 | wo. subtitle 下出现退化 |
| KimiVL-16B | -3.3 / -3.3 | overall 在 wo. subtitle / w. subtitle 都退化 |
| KimiVL-16B, Level 3 | -4.0 / -3.9 | reasoning-intensive Level 3 退化更明显 |

## Limitations & Caveats

- Video-MME-v2 用 recency-oriented curation 和 manual decontamination 降低污染风险，但论文没有证明所有样本都绝对不在未来/现有模型训练数据中。
- 评测是 8-option multiple-choice；它更适合标准化比较和抗随机猜测，但不等同于开放式生成、长期交互或 agentic video understanding。
- `w. sub` 在不同模型上含义不完全一致：omni models 可使用 raw audio，其他模型可能使用 subtitles/ASR transcripts，因此跨模型比较时需要注意输入模态差异。
- Non-Lin Score 更强调 group 内稳定性和推理链有效性，但也会更强烈惩罚部分正确；如果应用到业务场景，需要确认这种惩罚是否符合真实风险。
- 论文主要报告 benchmark construction 和 evaluation，未提供训练集或模型训练方法；它更适合作为诊断工具，而不是直接提供提升模型的训练 recipe。

## Concrete Implementation Ideas

- 在本地 video-LLM evaluation harness 中实现两套 scorer：Avg Acc 作为 sanity check，Non-Lin Score 作为主指标，并按 consistency/coherence group 分开记录。
- 评估模型时同时跑 `visual-only` 与 `visual+subtitle/audio`，把 gap 作为 text reliance / audio-visual fusion 的诊断信号。
- 为每个失败样本记录 Level、Parent Category、Leaf Category 和 Q1-Q4 correctness pattern，用来定位是 perception、temporal ordering，还是 high-level reasoning 出错。
- 在构造自有视频 QA benchmark 时复用 adversarial distractor 规则：至少一个 distractor 应基于部分证据看起来合理，但与关键细节冲突。
- 对 reasoning 模型单独做 subtitle ablation：如果 Thinking 只在有字幕时提升、无字幕时退化，说明模型可能在用语言先验替代视觉 grounding。

## Open Questions / Follow-ups

- Video-MME-v2 的数据和 leaderboard 是否会持续更新？如果更新，Non-Lin Score 排名是否稳定。
- 对开放式回答模型，如何把 group-based coherence 评测扩展到非多选场景，而不依赖 option elimination。
- 是否可以用 Video-MME-v2 的 leaf categories 作为训练数据采样/课程学习信号，专门补齐 Level 1 和 Level 2 的短板。
- Native audio 的提升来自语义内容、语气情绪，还是 temporal localization cue？需要更细的 audio ablation。
- Human Expert 90.7 与模型 49.4 的差距中，多少来自视觉感知失败，多少来自跨段记忆和推理链失败。

## Citation

ArXiv cite line: Chaoyou Fu et al., "Video-MME-v2: Towards the Next Stage in Benchmarks for Comprehensive Video Understanding," arXiv:2604.05015 [cs.CV], 2026.

```bibtex
@misc{fu2026videommev2,
  title = {Video-MME-v2: Towards the Next Stage in Benchmarks for Comprehensive Video Understanding},
  author = {Chaoyou Fu and Haozhi Yuan and Yuhao Dong and Yi-Fan Zhang and Yunhang Shen and Xiaoxing Hu and Xueying Li and Jinsen Su and Chengwu Long and Xiaoyao Xie and Yongkang Xie and Xiawu Zheng and Xue Yang and Haoyu Cao and Yunsheng Wu and Ziwei Liu and Xing Sun and Caifeng Shan and Ran He},
  year = {2026},
  eprint = {2604.05015},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  doi = {10.48550/arXiv.2604.05015},
  url = {https://arxiv.org/abs/2604.05015}
}
```
