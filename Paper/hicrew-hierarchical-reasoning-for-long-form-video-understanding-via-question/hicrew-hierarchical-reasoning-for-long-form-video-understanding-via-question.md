---
title: "HiCrew: Hierarchical Reasoning for Long-Form Video Understanding via Question-Aware Multi-Agent Collaboration"
authors: ["Yuehan Zhu", "Jingqi Zhao", "Jiawen Zhao", "Xudong Mao", "Baoquan Zhao"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2604.21444"
pdf_link: "[[assets/paper_2604.21444.pdf]]"
cover: "[[assets/pipeline_2604.21444.png]]"
updated: 2026-04-26
tags: ["paper/arxiv", "video-qa", "long-video", "temporal-reasoning", "question-aware", "video-llm"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://github.com/SYSUzzz/HiCrew"
---

## TL;DR

- HiCrew 面向 long-form video understanding，核心问题是长视频中的 spatiotemporal redundancy 与跨长时间跨度的 narrative / causal dependencies。
- 方法把视频先按 shot boundary 分成时间连续的 shots，再只在 question-relevant shots 内做 K-Means hierarchical clustering，避免 VideoTree 式 global clustering 打乱时间拓扑。
- Question-Aware Captioning 先按问题类型生成 intent-driven visual prompt，再让 VLM 产出更贴近问题的 captions / segment summaries。
- Planning Layer 会按问题复杂度动态选择 agent roles 和 workflow，避免简单问题过度推理、复杂问题推理不足。
- 在 EgoSchema 与 NExT-QA 上报告了强结果：EgoSchema subset/full 为 **71.6 / 64.6**，NExT-QA average 为 **79.5**。

## Key Contributions

1. 提出 **Hybrid Tree**：以 shot boundary detection 初始化第一层节点，保持视频 temporal topology；只在高相关 shot 中做更深层级展开，兼顾压缩与局部细节。
2. 提出 **Question-Aware Captioning**：根据 Causal / Temporal / Descriptive 问题类型生成 targeted visual guidance prompt，使 caption 更关注答案所需证据。
3. 提出 **HiCrew hierarchical multi-agent framework**：通过 Planning Layer 动态编排 Text Agent、Visual Analysis Agent、Evidence Integration Agent 与 Answer Generation Agent。
4. 实验上在 EgoSchema 和 NExT-QA 上超过若干 GPT-4 / GPT-4o agent 或 structured representation baseline，尤其强调 temporal / causal reasoning 的收益。

## Method

HiCrew 可以拆成三层：structured video representation、question-aware semantic extraction、adaptive multi-agent reasoning。

**Hybrid Tree Construction**

- 输入视频 $V$ 被切成 ordered shots：$S = \{s_1, s_2, \ldots, s_N\}$。
- 每个 shot 选一个靠近视觉质心的 representative frame $f_i$，并配合 caption $c_i$ 与问题 $Q$ 计算相关性：

$$
score_i = f_{score}(f_i, c_i, Q)
$$

- 若 $score_i > \tau$，该 shot 被视为 high-relevance，使用 CLIP features 与 K-Means 做 hierarchical clustering，生成更细粒度 sub-event nodes。
- 若相关性低，则保留为 leaf node，减少噪声并节省上下文预算。

**Question-Aware Captioning**

- 系统先将问题分为 Causal、Temporal、Descriptive 三类。
- LLM 根据同一视频的问题集合与问题类型模板生成视觉提示：

$$
P_t = \text{LLM}(\mathcal{Q}_V^t, \mathcal{T}_t), \quad t \in \{\mathcal{C}_{cau}, \mathcal{C}_{tem}, \mathcal{C}_{des}\}
$$

- 若 high-relevance shots 占比超过 $\gamma$，VTSearch 从 breadth-expansion layer 取代表帧以覆盖全局时间上下文；否则从 high-relevance clips 的 depth-expansion layer 取局部细节。
- VLM 根据 $P_t$ 生成 targeted captions，随后聚合成 segment summaries $S_i^t$。

**Hierarchical Multi-Agent Collaboration**

```text
Question Q
  -> Problem Analysis Agent: classify question type, select minimal agent set
  -> Task Planning Agent: build question-specific workflow
  -> Text Agent: retrieve question-aware captions and summaries from Hybrid Tree
  -> Visual Analysis Agent: inspect key frames / segments when visual verification is needed
  -> Evidence Integration Agent: fuse evidence with question-type-aware weights
  -> Answer Generation Agent: choose valid option and produce explanation trace
```

Evidence Integration Agent 使用加权证据聚合：

$$
\text{Score}_{option} = \sum_i w_i \cdot conf_i \cdot \text{Evidence}_i
$$

其中 $conf_i \in [0,1]$ 表示证据源置信度。论文举例说 descriptive questions 更依赖视觉证据，可设置较高 $w_{visual}$；causal questions 会做 bidirectional consistency verification。

## Pipeline Figure

![[assets/pipeline_2604.21444.png]]

Caption: Architecture of HiCrew framework showing Hybrid Tree construction (left) and hierarchical multi-agent collaboration (right).

Source: TeX includegraphics from `main.tex`, `Method.pdf` converted to `assets/pipeline_2604.21444.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| EgoSchema | Long-form egocentric video multiple-choice QA | Subset / Full | Accuracy | over 5,000 questions, 250+ hours, each question based on a 180-second clip |
| NExT-QA | Video QA for causal, temporal, descriptive reasoning | Temporal / Causal / Descriptive categories | Accuracy | 5,440 videos, nearly 52,000 QA pairs |

### Main Results

| Method | Model / Setting | EgoSchema Sub acc. (%) | EgoSchema Full acc. (%) | NExT-QA Tem acc. (%) | NExT-QA Cau acc. (%) | NExT-QA Des acc. (%) | NExT-QA Avg acc. (%) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AKeyS | GPT-4 | 68.0 | 63.1 | 72.3 | 78.2 | 85.4 | 77.4 |
| VideoTree | GPT-4 | 66.2 | 61.1 | 70.6 | 76.5 | 83.9 | 75.6 |
| LifelongMemory | GPT-4 | 64.1 | 58.6 | - | - | - | - |
| VideoAgent | GPT-4 | 60.2 | 54.1 | 68.3 | 68.3 | 74.3 | 71.3 |
| VideoChat2 | Mistral-7B | 63.6 | 54.4 | - | - | - | 78.6 |
| VideoLLaMA3-7B | - | 63.3 | - | - | - | - | - |
| LLoVi | GPT-4 | 57.6 | 50.3 | 73.7 | 70.2 | 81.9 | 73.8 |
| LLaMA-VID-7B | Vicuna-13B | 38.5 | - | - | - | - | - |
| Mobile-VideoGPT | - | 36.7 | - | - | - | - | 73.7 |
| InternVideo | VideoChat2-HD-F16 | - | 60.0 | - | - | - | - |
| LVNet | GPT-4o | 68.2 | 61.1 | 65.5 | 75.0 | 81.5 | 72.9 |
| AKeyS | GPT-4o | 68.6 | 63.6 | 72.9 | 79.0 | 86.1 | 78.1 |
| **HiCrew** | **GPT-4o** | **71.6** | **64.6** | **74.3** | **80.4** | **87.1** | **79.5** |

### Training / Compute

| Item | Value |
| --- | --- |
| Backbone LLM | GPT-4o |
| Visual encoder | EVACLIP-8B |
| Caption generator | BLIP-2 for EgoSchema; LaViLa for NExT-QA |
| Video sampling | 1 FPS |
| Shot expansion threshold | $\tau = 2.5$ |
| Robustness range for threshold | performance stable across $\tau \in [2.0, 3.0]$ |
| K-Means setting | $K=2$ |
| Maximum tree depth | 3 |
| Global context threshold | $\gamma = 40\%$ |
| Agent rounds | average 1.3 rounds, hard maximum 15 iteration rounds |

### Ablations / Analysis

| Variant / Setting | EgoSchema Sub acc. (%) | $\Delta$ | Notes |
| --- | ---: | ---: | --- |
| **HiCrew (Full)** | **71.6** | - | full system |
| w/o Hybrid Tree | 58.7 | -12.9 | uniform frame sampling replaces $T_{hyb}$ |
| w/o Q-Aware Captioning | 59.2 | -12.4 | question-agnostic captions |
| w/o Planning Layer | 62.0 | -9.6 | fixed agent workflow |

论文的 qualitative case 是 NExT-QA Causal question: “Why is the man on the bench looking up?” HiCrew 把视频切成 $s_1$ 到 $s_4$，识别 $s_3$ 高相关并深度展开；question-aware caption 捕捉到 “children playing near a fountain”，最后选择 “overlooking the children”。作者用这个例子说明 global clustering 可能漏掉关键环境上下文。

## Limitations & Caveats

- 论文主要报告 benchmark accuracy，没有给出完整 token / latency / dollar cost 分析；multi-agent orchestration 的真实部署成本还需要进一步确认。
- Hybrid Tree 依赖 shot boundary detection、CLIP features、LLM scoring 与 VLM captions，多个上游模块的误差会级联到推理阶段。
- 论文中 $\tau$ 和 $\gamma$ 的鲁棒性有简述，但没有看到更细的 per-dataset sensitivity table。
- 结果集中在 EgoSchema 与 NExT-QA，尚不清楚对更开放式、非选择题、或者需要音频/字幕/外部知识的视频任务泛化如何。
- Planning Layer 的 agent selection 与 workflow synthesis 描述偏系统层，复现实作可能还需要代码细节和 prompt / config 文件。

## Concrete Implementation Ideas

1. 在现有 long-video QA pipeline 中先做 shot boundary detection，再把每个 shot 的 representative frame、caption、question relevance score 存入可检索索引。
2. 给问题分类器加一个轻量 taxonomy：Causal / Temporal / Descriptive，然后为每类维护不同 caption prompt 与 evidence weighting policy。
3. 将 Hybrid Tree 节点设计为统一 schema：`shot_id`, `time_range`, `depth`, `parent_id`, `caption_by_question_type`, `relevance_score`, `frame_refs`。
4. 对 causal questions 实现 bidirectional temporal search：从目标事件向前找 triggers，向后找 consequences，再让 LLM 做 consistency check。
5. 用 ablation-first 的方式验证收益：uniform sampling baseline、global clustering baseline、question-agnostic captions、fixed workflow 四组最关键。

## Open Questions / Follow-ups

- HiCrew 的 Planning Layer 是如何定义 minimal agent subset 的？是否有可复现的规则、prompt，还是完全交给 GPT-4o 决策？
- Question-Aware Captioning 中的 semantic templates $\mathcal{T}_t$ 具体内容是什么？不同数据集是否需要重写？
- 对 long videos，shot boundary detection 错误会多大程度影响 Hybrid Tree？是否有 fallback 到 uniform temporal segments？
- 如果 backbone 从 GPT-4o 换成较小开源 LLM，Planning Layer 和 Evidence Integration 的性能是否稳定？
- 论文代码仓库发布后，可以优先检查 config files、prompt templates、tree serialization 与 retrieval implementation。

## Citation

```bibtex
@misc{zhu2026hicrew,
  title        = {HiCrew: Hierarchical Reasoning for Long-Form Video Understanding via Question-Aware Multi-Agent Collaboration},
  author       = {Yuehan Zhu and Jingqi Zhao and Jiawen Zhao and Xudong Mao and Baoquan Zhao},
  year         = {2026},
  eprint       = {2604.21444},
  archivePrefix = {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2604.21444}
}
```
