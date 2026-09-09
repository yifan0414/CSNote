---
title: "CS224N 12 Agent、工具调用与 RAG"
aliases:
  - "Agents, Tool Use, and RAG"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 12
date_text: "Thu Feb 5"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 12：Agent、工具调用与 RAG

> [!abstract] 本节定位
> 从问答和检索增强生成出发，组织检索、规划、记忆、工具、环境反馈与 Agent 评测。

## 学习目标

- [ ] 画出 RAG 从索引到生成的数据流
- [ ] 区分参数记忆、上下文记忆和外部记忆
- [ ] 识别 Agent 中的规划、工具错误与安全风险

## 知识笔记

> [!info] 课件范围
> 对应 RAG and Language Agents PPT 第 10–72 页：开放域问答、稀疏/稠密检索、RAG、引用与幻觉，以及 Agent 的 reasoning、memory、tool use、数据和评测。

## 1. 从阅读理解到开放域问答

阅读理解给定一个短 passage，模型从中回答问题。

开放域问答只给问题，系统必须：

1. 从大语料找证据；
2. 阅读证据；
3. 生成或抽取答案。

这将问题拆成：

$$
\text{Question}
\xrightarrow{\text{Retriever}}
\text{Documents}
\xrightarrow{\text{Reader/Generator}}
\text{Answer}.
$$

## 2. 为什么需要检索

语言模型参数中的知识：

- 更新慢；
- 来源不透明；
- 容量有限；
- 可能过时或错误；
- 很难给出可核验出处。

检索提供外部、可更新、可访问控制的记忆。

但 RAG 不是自动消除幻觉：系统可能检索错、读错或引用不支持结论的文档。

## 3. Sparse Retriever

BM25 一类方法依赖词项重叠。

直觉：

- 查询词在文档出现越多，相关性越高；
- 在整个语料越罕见，信息量越大；
- 长文档需做长度归一化。

简化形式：

$$
\operatorname{score}(q,d)
=
\sum_{t\in q}
\operatorname{IDF}(t)
\frac{f(t,d)(k_1+1)}
{f(t,d)+k_1(1-b+b|d|/\operatorname{avgdl})}.
$$

优势：

- 无需训练；
- 可解释；
- 精确实体和关键词很强；
- 索引成熟。

缺点是同义改写和语义匹配较弱。

## 4. Dense Retriever

分别编码 query 与 document：

$$
q=f_\theta(x),
\qquad
d=g_\phi(z).
$$

相似度：

$$
s(x,z)=q^\top d
$$

或 cosine。文档向量可离线索引，查询时做最大内积或近似最近邻搜索。

### 训练

给定正文档 $d^+$ 和负文档 $d^-$：

$$
L
=
-\log
\frac{\exp s(q,d^+)}
{\exp s(q,d^+)+\sum_j\exp s(q,d_j^-)}.
$$

in-batch negatives 可把同 batch 的其他正例作为负例，提高效率。

### 难负例

随机负例太容易。可从 BM25 或旧 retriever 的高分错误结果中选 hard negatives，使模型学到更细边界。

## 5. Retriever–Reader

典型系统：

1. retriever 返回 top-$k$ passages；
2. reader 分别编码或联合编码问题与 passage；
3. 聚合答案分数；
4. 选择 span 或生成答案。

系统误差至少分两类：

- retrieval error：正确证据不在 top-$k$；
- reading error：证据存在但 reader 回答错。

诊断时可给 reader oracle document，估计两者上限。

## 6. 联合训练

把文档视作潜变量：

$$
P(y\mid x)
=
\sum_{z\in\mathcal Z}
P_\eta(z\mid x)
P_\theta(y\mid x,z).
$$

只对 top-$k$ 近似求和。生成 loss 可以反向影响 retriever，使其寻找对答案有用而不仅是词义相似的文档。

难点：

- 离散 top-$k$ 不可微；
- 文档索引更新成本高；
- retriever 和 generator 同时变化会不稳定；
- 训练时文档与上线文档可能不同。

## 7. RAG 的开放问题

### Chunking

切块过短：

- 语境不足；
- 关系跨块断裂。

切块过长：

- embedding 混合多个主题；
- top-$k$ 占用更多上下文；
- 相关信息比例降低。

### 召回与上下文预算

提高 $k$ 增加 recall，却不保证答案更好：

- 无关文档干扰；
- 模型存在位置偏好；
- “lost in the middle”；
- 更长 prompt 增加成本。

### Reranking

双编码器适合大规模召回；cross-encoder 让 query 与文档 token 交互，精度更高但无法对全库逐个运行。

常用两阶段：

$$
\text{Bi-encoder top-}K
\to
\text{Cross-encoder top-}k.
$$

## 8. 引用不等于事实支持

评估带引用回答至少分开：

1. **Citation correctness**：引用文档是否蕴含对应陈述；
2. **Citation completeness**：需要证据的陈述是否都有引用；
3. **Citation quality**：来源是否可靠、原始、最新；
4. **Answer correctness**：最终答案是否正确。

模型可能引用真实文档，却让文档支持一个它没有说过的结论。

## 9. 从语言模型到 Agent

Agent 不只输出文本，而是在环境中循环：

$$
o_t
\to
\text{reason/state}
\to
a_t
\to
o_{t+1}.
$$

关键组件：

- reasoning/planning；
- memory；
- tools/actions；
- environment feedback；
- stopping criterion。

## 10. Reasoning 与 Acting

### Chain-of-Thought

先生成推理文本再给答案。对需要分解的问题有帮助，但没有外部行动。

### ReAct

交替：

1. Thought；
2. Action；
3. Observation。

外部 observation 能修正参数知识不足，推理则决定下一步查什么。

### Self-Consistency

采样多条 reasoning path：

$$
y^{(1)},\ldots,y^{(M)}
\sim P_\theta(y\mid x),
$$

再多数投票或聚合。

它用测试时计算换稳定性，只有错误不完全相关时才有效。

### Reflexion

任务失败后生成自然语言反馈并写入记忆，下次尝试时作为条件。它不一定更新模型参数，属于上下文中的策略改进。

### 多 Agent 与 Orchestrator

多个模型可：

- 独立提出答案；
- 相互批评；
- 分工处理子任务；
- 由 orchestrator 汇总。

风险是成本、通信误差和群体性错误；“更多 agent”不等于独立证据更多。

## 11. Agent Memory

课件区分多种记忆：

| 类型 | 内容 | 例子 |
| --- | --- | --- |
| Semantic | 事实和抽象知识 | 用户偏好、世界知识 |
| Episodic | 过去事件 | 上次行动与结果 |
| Procedural | 技能与步骤 | 可复用代码、计划模板 |
| Working | 当前任务状态 | 当前页面、变量、子目标 |

### 写入策略

- append-only 事件流；
- LLM 归纳摘要；
- 将成功行为变成代码技能；
- 基于重要性、相关性和时间衰减选择记忆。

### MemGPT 的层次记忆

将有限上下文视作主存，外部存储视作长期记忆。模型需要决定：

- 何时换入；
- 何时换出；
- 何时总结；
- 如何避免旧摘要永久丢失细节。

## 12. Tool Use

工具调用将自然语言意图转为结构化动作：

```json
{
  "name": "search",
  "arguments": {"query": "..."}
}
```

### Toolformer

大致流程：

1. 在文本中候选位置插入 API 调用；
2. 执行工具；
3. 比较调用是否降低后续语言模型 loss；
4. 只保留有帮助的调用；
5. 用筛选后数据训练模型。

它使用自监督信号学习“何时调用”。

### Gorilla 与大规模 API

目标是从大量文档中找到正确 API，并生成符合签名的调用。

难点：

- API 版本变化；
- 参数约束；
- 文档冲突；
- 不存在 API 的幻觉；
- 工具返回错误。

## 13. Agent 应用

课件列出：

- coding agents；
- web/app agents；
- computer-use agents；
- 游戏与模拟环境；
- 科学、教育、医疗等领域 agent。

每种环境的 action space、可观测性、风险和评价方式不同。不能只把所有任务当作聊天。

## 14. 扩展 Agent 数据

真实轨迹昂贵且包含失败。可通过：

- 人类示范；
- 强模型生成；
- 环境模拟；
- 代码仓库合成任务；
- 失败轨迹修复；
- curriculum

扩展。

SWE-smith 类思路从代码库生成问题和修复轨迹，为 coding agent 提供可执行验证。

## 15. Agent 评测

至少记录：

- task success；
- 工具选择准确率；
- 参数正确性；
- 环境步骤数；
- token 和 API 成本；
- 延迟；
- 是否可恢复；
- 安全违规；
- 对环境或测试集的过拟合。

开放环境容易变化，必须保存环境版本和可重放轨迹。

## 16. 安全边界

> [!warning]
> 模型输出文本与执行外部动作的风险不同。写文件、付款、发消息、删除数据和修改生产系统必须使用最小权限、参数验证、sandbox、幂等设计与人工确认。

还要防止：

- prompt injection；
- 恶意网页或工具返回；
- 记忆污染；
- 凭证泄漏；
- 无限循环和成本失控。

## 17. 小结

- RAG 把知识访问拆为检索与阅读，不能自动保证事实或引用正确。
- 稀疏检索擅长精确词项，稠密检索擅长语义匹配，常配合 reranker。
- Agent 是观察–行动闭环，而不是更长的单次生成。
- Reasoning、memory 与 tools 各有独立故障模式。
- Agent 评测必须包含成功率、步骤、成本、恢复与安全，不只看最终文本。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[cs224n-2026-lecture10-rag-agents.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture10-rag-agents.pdf>) |
| 论文 / 阅读 | [[2210.03629-react-synergizing-reasoning-and-acting-in-language-models.pdf\|ReAct: Synergizing Reasoning and Acting in Language Models]] | [原始链接](<https://arxiv.org/abs/2210.03629>) |
| 链接 | Language Agents: Foundations, Prospects, and Risks（仅在线） | [原始链接](<https://language-agent-tutorial.github.io/>) |
| 论文 / 阅读 | [[2005.11401-retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks.pdf\|Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks]] | [原始链接](<https://arxiv.org/abs/2005.11401>) |
| 论文 / 阅读 | [[2302.04761-toolformer-language-models-can-teach-themselves-to-use-tools.pdf\|Toolformer: Language Models Can Teach Themselves to Use Tools]] | [原始链接](<https://arxiv.org/abs/2302.04761>) |
| 作业 | [[a4.zip\|code]] | [原始链接](<https://web.stanford.edu/class/cs224n/assignments_w26/a4.zip>) |
| 作业 | [[a4.pdf\|handout]] | [原始链接](<https://web.stanford.edu/class/cs224n/assignments_w26/a4.pdf>) |
| 作业 | [[a4_tex.zip\|latex template]] | [原始链接](<https://web.stanford.edu/class/cs224n/assignments_w26/a4_tex.zip>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 如何判断 RAG 失败来自 retriever 还是 generator？
2. 增加更多工具为何不一定提高 Agent 成功率？
3. 哪些外部动作应在执行前要求人类确认？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
