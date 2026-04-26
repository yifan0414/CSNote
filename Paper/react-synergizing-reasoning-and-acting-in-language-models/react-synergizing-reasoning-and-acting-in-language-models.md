---
title: "ReAct: Synergizing Reasoning and Acting in Language Models"
authors: ["Shunyu Yao", "Jeffrey Zhao", "Dian Yu", "Nan Du", "Izhak Shafran", "Karthik Narasimhan", "Yuan Cao"]
conference: "ICLR"
year: 2023
arxiv_url: "https://arxiv.org/abs/2210.03629"
pdf_link: "[[assets/paper_2210.03629.pdf]]"
cover: "[[assets/pipeline_2210.03629.png]]"
updated: 2026-04-26
tags: ["paper/arxiv", "reasoning", "agent"]
status: "unread"
priority:
rating:
topics: ["LLM"]
code: "https://react-lm.github.io/"
---

## TL;DR

- ReAct 提出一种 prompting 范式，让 LLM 在同一条轨迹里交替生成 `Thought` 和 task-specific `Action`，把 reasoning trace 与环境交互绑定起来。
- 核心直觉是：reasoning trace 用来制定、追踪和修正行动计划，action 用来从 Wikipedia API、ALFWorld、WebShop 等外部环境拿回新 observation。
- 在 HotpotQA 和 FEVER 上，ReAct 比 acting-only 更稳，能降低 CoT 常见的 hallucination 与错误传播；最佳结果来自 ReAct 与 `CoT-SC` 的互补组合。
- 在 ALFWorld 和 WebShop 上，ReAct 只用很少 in-context examples 就超过 imitation learning / reinforcement learning baseline，说明 sparse thoughts 对长程交互任务很关键。
- 主要 caveat 是 prompting 版本对 context length、示例覆盖和搜索反馈质量敏感；复杂任务可能需要更多高质量轨迹和 finetuning。

## Key Contributions

1. 提出 `ReAct`，把 reasoning 和 acting 统一到一个 LLM agent trajectory 中，而不是分别研究 CoT reasoning 或 action generation。
2. 将 agent 的 action space 扩展为 $\hat{\mathcal{A}} = \mathcal{A} \cup \mathcal{L}$，其中 $\mathcal{L}$ 是 language thought space；thought 不直接改变环境，但会更新后续决策上下文。
3. 在 knowledge-intensive reasoning 与 interactive decision making 两类任务上展示通用性：HotpotQA、FEVER、ALFWorld、WebShop。
4. 通过 human study、ReAct-IM ablation、finetuning experiment 分析什么时候需要外部 action，什么时候需要内部 reasoning。
5. 指出 ReAct trajectory 更可解释、可诊断，也更适合 human-in-the-loop thought editing。

## Method

ReAct 的 setup 是一个 agent 在 time step $t$ 收到 observation $o_t \in \mathcal{O}$，并根据上下文 $c_t = (o_1, a_1, \cdots, o_{t-1}, a_{t-1}, o_t)$ 选择下一步。普通 agent 只在 task action space $\mathcal{A}$ 里行动；ReAct 加入 language space $\mathcal{L}$，允许模型输出不会改变环境的 `Thought`，以及会触发环境反馈的 `Action`。

```text
For each task instance:
  observe current context
  if reasoning is useful:
    generate Thought to decompose goal, track state, revise plan, or synthesize evidence
  generate Action in the task-specific action space
  receive Observation from environment
  repeat until Finish / success / step limit
```

在 HotpotQA / FEVER 中，ReAct 使用 dense thought-action-observation 格式，并通过简单 Wikipedia API 交互：

| Action | Function |
| --- | --- |
| `search[entity]` | 返回对应 Wikipedia 页面前 5 句，或相似 entity 建议 |
| `lookup[string]` | 在当前页面里查找包含 string 的下一句，模拟 Ctrl+F |
| `finish[answer]` | 提交最终答案或 label |

在 ALFWorld / WebShop 中，任务 horizon 更长，因此 thought 是 sparse 的，由模型在关键位置生成，用于 goal decomposition、subgoal tracking、commonsense search、buy/no-buy 判断等。

## Pipeline Figure

![[assets/pipeline_2210.03629.png]]

Caption: (1) Comparison of 4 prompting methods, Standard, Chain-of-thought / CoT, Act-only, and ReAct, solving a HotpotQA question. (2) Comparison of Act-only and ReAct prompting to solve an AlfWorld game. In both domains, the figure omits in-context examples and shows model-generated task-solving trajectories (`Act`, `Thought`) plus environment observations (`Obs`).

Source: TeX includegraphics from `iclr2023/figuretext/teaser.tex`, rendered from `iclr2023/figure/teaser-new.pdf` via `pdftoppm`. I selected it as the pipeline/framework figure because the caption directly compares ReAct against Standard, CoT, and Act-only trajectories across QA and interactive decision making.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| HotpotQA | multi-hop question answering | question-only setup; validation subset/table results | EM | 不提供 support paragraphs；模型只能靠内部知识或 Wikipedia API 检索 |
| FEVER | fact verification | claim-only setup; dev/eval results | Accuracy | label 为 SUPPORTS / REFUTES / NOT ENOUGH INFO；同样使用 Wikipedia API |
| ALFWorld | text-based interactive game | 134 unseen evaluation games | Success rate | 6 类 household tasks；每类构造 6 个 prompt permutations |
| WebShop | webpage navigation / online shopping | 500 test instructions | Score, Success rate | 环境含 1.18M products 与 12k human instructions |

### Main Results: HotpotQA and FEVER

PaLM-540B prompting results. `CoT-SC -> ReAct` 表示当 CoT-SC 多数票不够自信时切到 ReAct；`ReAct -> CoT-SC` 表示 ReAct 超过 step limit 未完成时回退到 CoT-SC。

| Method | Model / Setting | HotpotQA EM | FEVER Acc |
| --- | --- | ---: | ---: |
| Standard | PaLM-540B prompting | 28.7 | 57.1 |
| CoT | PaLM-540B prompting | 29.4 | 56.3 |
| CoT-SC | 21 samples, temperature 0.7 | 33.4 | 60.4 |
| Act | acting-only prompt | 25.7 | 58.9 |
| **ReAct** | thought-action-observation prompt | **27.4** | **60.9** |
| **CoT-SC -> ReAct** | combined internal/external knowledge | **34.2** | **64.6** |
| **ReAct -> CoT-SC** | combined internal/external knowledge | **35.1** | **62.0** |
| Supervised SoTA | task-specific supervised systems | 67.5 | 89.5 |

要点：ReAct 比 Act 在两个任务上都更好，说明 reasoning trace 能帮助检索和最终答案合成；单独 ReAct 在 FEVER 上超过 CoT，但在 HotpotQA 上略低于 CoT。最强 prompting 结果来自 ReAct 与 CoT-SC 的互补组合。

### Main Results: ALFWorld

ALFWorld task-specific success rates (%). `ReAct-IM` 是 Inner Monologue-style ablation，使用更受限的 dense external feedback thought。

| Method | Pick | Clean | Heat | Cool | Look | Pick 2 | All |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Act (best of 6) | 88 | 42 | 74 | 67 | 72 | 41 | 45 |
| **ReAct (avg)** | **65** | **39** | **83** | **76** | **55** | **24** | **57** |
| **ReAct (best of 6)** | **92** | **58** | **96** | **86** | **78** | **41** | **71** |
| ReAct-IM (avg) | 55 | 59 | 60 | 55 | 23 | 24 | 48 |
| ReAct-IM (best of 6) | 62 | 68 | 87 | 57 | 39 | 33 | 53 |
| BUTLER_g (best of 8) | 33 | 26 | 70 | 76 | 17 | 12 | 22 |
| BUTLER (best of 8) | 46 | 39 | 74 | 100 | 22 | 24 | 37 |

要点：best ReAct overall success rate 为 71%，明显高于 Act best-of-6 的 45% 和 BUTLER 的 37%。ReAct-IM 低于 ReAct，说明 thought 不能只描述外部反馈，还需要 goal decomposition、subgoal transition 和 commonsense reasoning。

### Main Results: WebShop

| Method | Model / Setting | Score | SR |
| --- | --- | ---: | ---: |
| Act | one-shot acting prompt | 62.3 | 30.1 |
| **ReAct** | one-shot sparse reasoning + acting | **66.6** | **40.0** |
| IL | 1,012 human trajectories | 59.9 | 29.1 |
| IL + RL | +10,587 training instructions | 62.4 | 28.7 |
| Human Expert | human exploration | 82.1 | 59.6 |

要点：WebShop 中 Act 已经接近 IL/IL+RL，但加上 sparse reasoning 后 ReAct 的 success rate 提升到 40.0%，比先前最好结果高约 10 个百分点。

### Ablations / Analysis: Human Error Study on HotpotQA

作者从 ReAct 和 CoT 的 correct / incorrect trajectories 中各随机采样 50 条，人工标注 success 和 failure modes。

| Group | Type | Definition | ReAct | CoT |
| --- | --- | --- | ---: | ---: |
| Success | True positive | Correct reasoning trace and facts | 94% | 86% |
| Success | False positive | Hallucinated reasoning trace or facts | 6% | 14% |
| Failure | Reasoning error | Wrong reasoning trace, including repetitive-step recovery failures | 47% | 16% |
| Failure | Search result error | Search returns empty or unhelpful information | 23% | - |
| Failure | Hallucination | Hallucinated reasoning trace or facts | 0% | 56% |
| Failure | Label ambiguity | Right prediction but label mismatch | 29% | 28% |

解读：ReAct 的 hallucination 更少，因为它被 observation grounding；但它可能因为检索不到信息、反复生成旧动作、或结构约束导致 reasoning error。CoT 更灵活，但失败时 hallucination 占比高。

### Additional Results: GPT-3

Appendix 报告 `text-davinci-002` greedy decoding 结果，说明 ReAct prompting 不只依赖 PaLM。

| Benchmark | PaLM-540B | GPT-3 |
| --- | ---: | ---: |
| HotpotQA EM | 29.4 | 30.8 |
| ALFWorld success rate (%) | 70.9 | 78.4 |

### Training / Compute

| Item | Value |
| --- | --- |
| Main prompting LLM | PaLM-540B |
| GPT-3 appendix model | `text-davinci-002`, greedy decoding |
| HotpotQA ReAct prompt examples | 6 manually composed trajectories |
| FEVER ReAct prompt examples | 3 manually composed trajectories |
| ALFWorld prompts | 3 annotated trajectories per task type; 6 permutations using 2 trajectories |
| WebShop prompts | Act actions plus ReAct sparse thoughts for exploration and buying decisions |
| HotpotQA finetuning data | 3,000 correct-answer trajectories generated by each method |
| Finetuning batch size | 64 |
| PaLM-8B finetuning steps | ReAct/Act 4,000; Standard/CoT 2,000 |
| PaLM-62B finetuning steps | ReAct/Act 4,000; Standard/CoT 1,000 |

## Limitations & Caveats

- ReAct prompting 依赖有限的 in-context examples；复杂 action space 需要更多 demonstrations，容易超过 context length。
- 在 HotpotQA 中，ReAct 的 search result error 占失败样本 23%，说明外部工具质量和检索策略会直接限制 agent。
- ReAct 有一种特有失败模式：模型可能重复前面的 thoughts/actions，无法跳出错误循环。论文猜测更好的 decoding，如 beam search，可能改善。
- 单独 ReAct 在 HotpotQA EM 上低于 CoT / CoT-SC；结构化交互提升 factuality，但可能牺牲部分 reasoning flexibility。
- WebShop 和 ALFWorld 仍明显低于 human expert，尤其在更充分探索、query reformulation、复杂商品选项匹配方面。
- 论文的主要实验使用 PaLM-540B，当时并非开放模型；可复现性依赖 appendix prompts、GPT-3 结果和公开项目代码。

## Concrete Implementation Ideas

1. 在 agent 框架里显式区分 `Thought`、`Action`、`Observation`，并把 `Thought` 作为可审计日志，而不是直接隐藏在模型内部。
2. 对 RAG/工具调用任务加入 fallback policy：当 internal CoT 不自信时调用工具，当工具轨迹卡住时回退到自洽推理或改写 query。
3. 给 long-horizon environment 加 sparse thought trigger，例如 subgoal changed、observation contradicts plan、step budget low、tool result empty。
4. 做 human-in-the-loop editing UI：允许用户编辑某一步 thought，然后从该步继续 rollout，以低成本纠正 agent belief。
5. 用成功 ReAct trajectories bootstrap finetuning data，但要过滤 hallucinated thought、repeated action 和 uninformative search cases。

## Open Questions / Follow-ups

- ReAct 的 thought 什么时候应该 dense，什么时候应该 sparse？能否通过 learned controller 自动决定？
- 如何区分有益的 internal reasoning 与会污染轨迹的 hallucinated thought？
- 对现代 tool-use LLM，ReAct + function calling + retrieval confidence 是否能系统性优于简单 tool planner？
- 在多工具环境中，是否需要显式训练 tool-selection thought，而不只是自然语言 reasoning？
- ReAct trajectories 是否适合作为 agent finetuning / preference learning 的中间监督信号？

## Citation

```bibtex
@inproceedings{yao2023react,
  title = {ReAct: Synergizing Reasoning and Acting in Language Models},
  author = {Yao, Shunyu and Zhao, Jeffrey and Yu, Dian and Du, Nan and Shafran, Izhak and Narasimhan, Karthik and Cao, Yuan},
  booktitle = {International Conference on Learning Representations},
  year = {2023},
  url = {https://arxiv.org/abs/2210.03629}
}
```
