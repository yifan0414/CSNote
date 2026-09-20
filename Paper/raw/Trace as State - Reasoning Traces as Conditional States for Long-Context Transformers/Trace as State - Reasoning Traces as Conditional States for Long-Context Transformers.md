---
title: "Trace as State: Reasoning Traces as Conditional States for Long-Context Transformers"
authors: ["Xu Zou", "Jie Tang"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2609.02702v1"
pdf_link: "[[assets/paper_2609.02702.pdf]]"
cover: "[[assets/pipeline_2609.02702.png]]"
updated: 2026-09-15
tags: ["paper/arxiv", "reasoning", "long-context"]
status: "unread"
priority:
rating:
topics: ["LLM"]
code: ""
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

- **核心问题是信息到达顺序。** 因果 Transformer 读过上下文后才发现的目标、指代关系或搜索前沿，不能回头改变本轮早先位置已经形成的表示。
- **Trace as State（TaS）** 收集同一问题的第一轮 reasoning traces，作为不完美的任务状态代理 $T$，再以 $[T,x,q]$ 开启全新一轮推理。对照 Trace Append 使用完全相同的 $T$，顺序为 $[x,T,q]$；$x$ 是长上下文，$q$ 始终在末尾。
- 作者在三种模型、三类长上下文任务的 27 个模型—任务—指标组合中报告，TaS 有 26 项高于 Trace Append。GraphWalks Parents 上，DeepSeek 的 EM 从 First Pass 的 29.2%、Trace Append 的 43.0% 升至 TaS 的 81.8%。
- 理论给出确定性、精确、单遍条件状态更新的**最坏情况内存分离**，属于方法动机；它没有证明真实长上下文任务或 Transformer 必然获得指数级节省。
- 代价是收集轨迹、重新读取长上下文以及可能减少 KV cache 复用；配对区间和小样本小说评测也要求谨慎解读“普遍获益”。

## Key Contributions

1. **条件状态更新的形式化。** 区分“知道初始条件后只追踪一个实际状态”和“条件未知时保留所有可能条件对应的响应”，刻画输入顺序造成的最坏情况内存差异。
2. **跨轮反馈、轮内保持因果结构。** 用模型已暴露的 reasoning traces 作为状态接口，修改下一轮输入布局；实验使用固定模型，没有额外训练目标、微调或架构改造。
3. **同轨迹的位置控制。** 核心对照固定模型、上下文、序列化器和实际轨迹文本，仅调整轨迹与上下文的先后；另用问题前置、答案反馈、随机轨迹、重复上下文与 Trace Only 检验替代解释。

与文中相关工作相比，TaS 的重点是让上一轮发现的信息参与下一轮上下文处理。Re2 依靠重复输入；架构递归与 latent recurrence 则可能改变训练或推理结构。作者把 reasoning trace 看成可利用的信息载体，并不要求它忠实反映内部计算。

## Method

### Conditional state updates

设信息序列 $C=(c_1,\ldots,c_n)$、有限状态集合 $\mathcal S$，处理器按固定规则更新：

$$
s_0=z,\qquad s_i=U(s_{i-1},c_i).
$$

令 $b=\log_2|\mathcal S|$。当输入为 $[z,C]$，处理器先知道条件 $z$，随后只需保存当前状态，$\lceil b\rceil$ bits 足够。若输入为 $[C,z]$，处理器读完 $C$ 时还不知道应传播哪个初始状态，必须区分不同序列诱导的 residual map：

$$
\phi_C(z)=t(C,z),\qquad
\mathcal K=\left|\{\phi_C:C\in\mathcal C^n\}\right|.
$$

如果两个不同映射共享相同的内存配置，总能找到一个 $z$ 使它们应输出不同结果；此时精确处理器无法区分，因此晚条件顺序需要至少 $\lceil\log_2\mathcal K\rceil$ bits。

附录构造 $n=1$，把每个函数 $f:\mathcal S\to\mathcal S$ 编码为输入符号 $c_f$，并固定 $U(s,c_f)=f(s)$。于是所有自映射均可实现：

$$
\mathcal K=|\mathcal S|^{|\mathcal S|},\qquad
\lceil\log_2\mathcal K\rceil=\lceil b2^b\rceil.
$$

作者给出的直观例子是 $|\mathcal S|=4$：条件前置需 2 bits，条件后置需区分 256 个映射、即 8 bits。这里计数的是持久、输入相关的工作状态，所有辅助可写存储都计入，固定转换规则已知。构造使用能实现所有自映射的对抗性字母表；若更新族受限，$\mathcal K$ 可以小很多。

**与 Transformer 的关系：** 有限最大上下文和有限精度使位置、各层 KV 与其他持久推理缓冲共同构成有限状态。但这只是抽象上的兼容性，不能把人工构造中的下界直接当作模型实际内存或准确率规律。

### Read, compute, feedback, reread

对同一问题执行 $n_{\mathrm{tr}}$ 次 source runs，分别得到推理字段 $r_j$ 和可见答案 $a_j$：

$$
(r_j,a_j)\sim\mathcal M(\cdot\mid[x,q]),\qquad
T=\pi(r_1,\ldots,r_{n_{\mathrm{tr}}}).
$$

实验中的 $\pi$ 按 repeat-index 顺序保留推理文本，加上固定引导说明、编号与分隔符。单条超过 50,000 **字符**的轨迹保留开头 50,000 字符并附省略号，之后去除首尾空白。独立返回的 visible answer 字段不进入 $T$；但这不意味着推理文本内部不含答案线索。

新的推理分别使用：

$$
(r'_{\mathrm{TaS}},a'_{\mathrm{TaS}})\sim\mathcal M(\cdot\mid[T,x,q]),
$$
$$
(r'_{\mathrm{Append}},a'_{\mathrm{Append}})\sim\mathcal M(\cdot\mid[x,T,q]).
$$

前置 $T$ 时，上下文 token 在形成表示时即可利用轨迹；后置 $T$ 仍可帮助后续推理和答案生成，但不能更新本轮先前位置已形成的表示。轨迹可以包含错误、遗漏和损失，因此它是 **textual task-state proxy**，不等同于形式化条件 $z$ 或模型内部真实状态。

主实验用五次第一轮轨迹构造一个共享 $T$，两种反馈条件各执行五次新的第二轮推理。GraphWalks 中，Trace Append 把 $T$ 插在原提示最后一个 `Operation:` 块之前；TaS 把整个 $T$ 放在原提示之前。任务问题和答案格式要求留在末尾。轨迹块的引导语要求把轨迹当作可能出错的草稿提示，并回到原图或原对话核验。

## Pipeline Figure

![[assets/pipeline_2609.02702.png]]

原文总览依次连接因果状态更新、顺序相关内存、轨迹作为状态代理，以及两种共享 $T$ 的跨轮反馈布局。图中采用省略末尾问题的简写，实验实际保留 $q$ 在最后。

## Experiments

### Setup and scoring

- **模型：** DeepSeek V4 Pro Preview、Qwen 3.7 Max、GLM-5.2，均使用作者实验时的官方供应商接口。DeepSeek 具体是作者标注的 2026-04-24 版本；不应直接用同名后续版本等同复现。
- **推理配置：** DeepSeek 与 GLM 使用 `max`；Qwen 的 `xhigh` 是固定提示文本，**不是**供应商侧 `reasoning_effort` 参数。Qwen 在 MRCRv2 用 system message，在其余两类任务用 user message，且每个数据集内保持一致。
- **预算：** 配置表列出的 Qwen 输入/输出预算为 983,616/65,536 tokens，DeepSeek 为 1,048,576/131,072，GLM 为 1,048,576/65,536。作者没有显式传自定义最大输出值，因此日志不能确定当时有效的供应商默认上限。
- **GraphWalks 256K：** 共 200 题，BFS 与 Parents 各 100，考察长边列表上的遍历与父节点集合。每题五次，按节点集合计算 EM 和 set F1；输出必须有可解析的末尾答案行。
- **MRCRv2 8-needle：** 256K、512K 两档共 200 题，各档 100，要求把最终请求与早先正确的请求—回答实例绑定。验证并去掉指定随机前缀后，计算 EM 和 Python `difflib.SequenceMatcher` ratio；后者不同于 set F1。
- **NUB-1M Season 2：** 一部长约 400–700K tokens 的新小说，20 个问题，各五次。DeepSeek V4 Pro 对照人工维护的参考答案作布尔判分；judge 看不到 solver 身份和反馈顺序。作者称人工复核未发现判分错误。
- **失败口径：** 被阻止、超长、缺失、格式错误、非正常终止或内容过滤的样本计失败，保留在分母中。GraphWalks 合法空集按正常集合规则评分；MRCRv2 前缀缺失或无效则两项均为零。

作者因 tokenizer 差异导致 1M 档超长而选择较短档位，并为轨迹预留空间；不能把这些实验概括为所有任务均在完整 1M tokens 上验证。

### Main results

![[assets/experiment_table_2609.02702_t2.png]]

作者报告 TaS 在 27 个组合中有 26 项高于 Trace Append，全部报告项高于 First Pass。唯一反例是 GLM-5.2 的 GraphWalks BFS F1：Trace Append 75.8%，TaS 75.0%，但 TaS 的 EM 更高。

最突出的结果来自 Parents：DeepSeek 的 EM 为 First Pass 29.2%、Trace Append 43.0%、TaS 81.8%；Qwen 的 First Pass/TaS EM 为 60.8%/96.4%；GLM 在 TaS 下 EM 与 F1 均为 100.0%。作者也报告 MRCRv2 的同方向优势；NUB-1M 作为长小说阅读理解的支持性证据，样本量更小。

### Placement and feedback controls

![[assets/experiment_table_2609.02702_t3.png]]

控制实验限于 **DeepSeek V4 Pro Preview + GraphWalks 256K**。以下是作者的比较解释，不能自动外推到其他模型或领域：

- **Question First $[q,x,q]$：** Parents 有明显改善，BFS 接近基线，说明有些任务仅把问题先交给模型就有帮助。
- **Re2 $[x,q,x,q]$：** 重读本身有益，但仍低于 TaS，尤其是 Parents；支持轨迹提供了重复提示以外的信息。
- **Answer Feedback $[a,x,q]$：** 反馈五个可见答案有所改善，但远低于反馈完整 reasoning traces。
- **Random Trace $[T_{\mathrm{rand}},x,q]$：** 换为同一子任务其他题的轨迹后，比 First Pass 更差，削弱“只有通用轨迹格式就有用”的解释。
- **Trace Only $[T,q]$：** 单靠轨迹已能回答部分问题，但低于 TaS，说明重新访问原始上下文仍有价值。
- **Majority@5 / Oracle@5：** 附录把 Majority 定义为保留五个预测集合中至少出现三次的元素；Oracle 按各评价指标回看五个答案的最高分，属于事后选择对照。作者报告 TaS 超过 Oracle@5，说明反馈轮不只是挑出已有最优答案。

这些控制共同削弱了答案反馈、简单重复、通用格式和纯文本近因效应的解释，但尚未直接测出模型内部表征变化。

### Trace count and uncertainty

轨迹数量消融从 $n_{\mathrm{tr}}=1$ 到 5，按重复顺序取前若干条可用轨迹，形成嵌套集合；每个数量下前置与后置共享同一份 $T$。作者报告 BFS F1 与 Parents F1 总体随轨迹增加而上升，且每个正轨迹数下 TaS 均高于 Trace Append。实验没有证明无限增加轨迹仍会持续获益。

![[assets/experiment_table_2609.02702_t5.png]]

配对分析先在每题内平均五次重复，再按问题做 20,000 次 cluster bootstrap，seed 为 0，给出**未做多重比较校正**的 95% percentile intervals。GraphWalks 与 MRCRv2 的 24 项对比中，20 项区间完全高于零；跨零的四项为：

- DeepSeek：MRCRv2 512K EM。
- Qwen：GraphWalks BFS F1。
- GLM：GraphWalks BFS EM、F1。

因此，26/27 是均值方向计数，不能改写为“26 项显著提升”。NUB-1M 不在这张 24 项配对表里；作者另给逐条件区间，并强调 20 题导致区间较宽。

难度分组分析按 BFS 深度和 Parents 标准父节点数观察收益差异。作者明确说明分箱和高亮区域是在查看结果后确定，只用于生成假设；它们不能证明某个难度阈值、容量限制或中介机制。

### Inference cost

![[assets/experiment_table_2609.02702_t6.png]]

成本表来自有供应商 usage 的保留响应，区分 cached input、missed input 和 output；reasoning tokens 计入 output。反馈条件的 Total tokens 逐项加上共享的 First Pass 消耗，不能只把第二轮输出长度当作方法总成本。

作者明确指出额外 source runs 和完整重读会增加延迟与 token 开销，前缀变化也可能减少 KV cache 复用。论文给出的总量统计不等于固定价格下的费用，也不是等墙钟时间或等总预算比较。原表 Qwen MRCRv2 512K 带有 dagger 标记，但正文与该表没有给出对应释义，不能自行补充其含义。

## Limitations & Caveats

1. **理论与实验之间仍是定性连接。** 定理要求确定性、所有输入精确、单遍且不可重读，并使用能实现所有自映射的任务族。真实任务可近似、轨迹可能错误，TaS 本身又允许跨轮重读，不能据此宣称真实模型必有指数级内存收益。
2. **需要暴露的状态接口。** 本文实现需要 raw reasoning traces；只返回最终答案的接口不能原样复现。其他可访问状态接口是作者提出的扩展，而非本实验已验证的替代品。
3. **泛化范围有限。** 仅三模型、三任务族，控制与轨迹数消融只覆盖一个模型的 GraphWalks；没有多轮 agent 任务评估。
4. **模型与运行配置会影响复现。** 版本别名、Qwen 提示形式、字符截断、供应商输出默认值和内容过滤均要记录。Question First 中 181 个输出被按 length-limited 处理，另一个已停止输出缺少要求的格式，共 182 个记零；该控制的低分包含运行与格式失败因素。
5. **统计与机制证据有边界。** 多指标相关，区间未校正，小说样本仅 20 题；事后难度分析没有确证机制。位置干预的结果支持“前置轨迹更有用”，不等于证明轨迹忠实表示内部状态。
6. **源码细节未完全展开。** 附录给出 GraphWalks 插入边界和 MRCRv2 引导语，但未同等详细列出 NUB-1M 的完整专用模板；不能自行补写为作者的精确实现。

## Concrete Implementation Ideas

以下为依据论文提出的复现与扩展建议，尚非新增实验结论：

1. **先建立可审核的 same-$T$ 对照。** 保存 source runs 的 reasoning 与 answer 为独立字段；只构造一次序列化 $T$，两个第二轮分支直接复用。把 $x$、$q$ 的分界固定，记录模型版本、提示和终止原因。
2. **原样复现后再做压缩。** 基线按原顺序保留每条前 50,000 字符；之后可另设“只保留目标、候选集合、已排除假设”的压缩变体，与全文轨迹在相同输入预算下比较，防止把压缩质量与位置收益混在一起。
3. **同时记录准确率与完整成本。** 分开统计轨迹生成、第二轮输入缓存命中、输出 tokens 和端到端延迟。按问题配对比较，失败样本保留分母；对多轮场景单独测前缀变动的缓存影响。

## Open Questions / Follow-ups

- 能否用更短、更可靠的状态摘要保留前置收益，同时降低输入长度和重读成本？作者将选择、压缩轨迹与学习状态接口列为后续方向。
- 对 restricted update families、近似或随机处理器，顺序相关内存下界如何变化，能否更贴近实际图推理与检索任务？
- 在等总 tokens 或等延迟预算下，TaS 相比更多独立采样、答案聚合和重复上下文是否仍有优势？
- 多轮 agent 中何时刷新状态、何时重读上下文、何时保留缓存最合适？论文没有验证这一场景。
- 能否在预先定义的难度分层和留出题上重做分析，并直接检查前置状态是否改变上下文表示？

## Citation

Xu Zou（Z.ai）、Jie Tang（Tsinghua University）. *Trace as State: Reasoning Traces as Conditional States for Long-Context Transformers*. arXiv preprint, 2026，v1 发布于 2026-09-02。

- [arXiv v1](https://arxiv.org/abs/2609.02702v1)
- 原文 PDF：[[assets/paper_2609.02702.pdf]]

```bibtex
@misc{zou2026traceasstate,
  title={Trace as State: Reasoning Traces as Conditional States for Long-Context Transformers},
  author={Xu Zou and Jie Tang},
  year={2026},
  eprint={2609.02702},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2609.02702v1}
}
```

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
