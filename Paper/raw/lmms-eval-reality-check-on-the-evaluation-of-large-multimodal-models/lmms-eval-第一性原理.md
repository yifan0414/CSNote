---
创建时间: 2026-05-31 22:18
tags: []
---

# 论文定位

**LMMs-Eval: Reality Check on the Evaluation of Large Multimodal Models** 不是一篇“提出新 LMM 架构”的论文，而是一篇**评测范式 / benchmark 基础设施 / 评测可靠性分析**论文。核心问题是：随着多模态大模型能力上升，静态、零散、不可复现、可能被污染的 benchmark 已经不能可靠回答“哪个模型真的更强”。论文基于 arXiv v 2，最后修订于 2025-05-05。([arXiv][1])

作者的核心抽象是一个 **evaluation trilemma**：理想评测同时需要 **wide coverage、low cost、zero contamination**，但三者很难同时满足。因此论文给出三件东西：**LMMs-Eval** 负责标准化和广覆盖，**LMMs-Eval Lite** 负责低成本近似，**LiveBench** 负责动态、低污染评测。([ar5iv][2])

---

# 1. Task：形式化定义

## 1.1 被研究任务

给定一个多模态模型：

$$
f_\theta: (I, T, c) \rightarrow y
$$

其中：

- $I$：图像、网页截图、图表、文档图像等视觉输入；
- $T$：问题、指令、选项、上下文；
- $c$：模型聊天模板、system prompt、评测协议、输出格式约束；
- $y$：模型生成的答案；
- $m(y, y^*)$：某 benchmark 对输出的打分函数。

论文真正要优化的不是模型参数，而是一个评测系统：

$$
E = (\mathcal{D}, \mathcal{P}, \mathcal{M}, \mathcal{J})
$$

其中：

- $\mathcal{D}$：评测数据集合；
- $\mathcal{P}$：数据预处理、prompt 构造、模型调用、输出解析协议；
- $\mathcal{M}$：指标计算方式；
- $\mathcal{J}$：LLM-as-judge / 人工验证等裁判机制。

目标不是最大化某个模型分数，而是让评测结果同时满足：

$$
\text{Coverage}(E) \uparrow,\quad \text{Cost}(E) \downarrow,\quad \text{ContaminationRisk}(E) \downarrow
$$

这就是论文所谓的三角约束。

## 1.2 论文把问题拆成三个子任务

### 子任务 A：标准化评测

过去 LMM 评测常常由各模型发布方自定义脚本，数据准备、输出后处理、指标计算都可能不同，导致分数不可直接比较。作者指出，有的评测用 PPL-based choice scoring，有的用 generation-based matching；即便 benchmark 相同，评测协议不同也会改变结果。([ar5iv][2])

所以 **LMMs-Eval** 的任务是：

$$
E_{\text{std}} = \text{统一模型接口} + \text{统一数据源} + \text{统一输出解析} + \text{日志可复现}
$$

论文声称 LMMs-Eval 支持超过 50 个任务、10 多个模型，并提供统一接口和详细日志。([ar5iv][2])

### 子任务 B：低成本近似评测

完整评测太贵。论文构建 **LMMs-Eval Lite**，把 90,223 个样本压缩到 9,134 个样本，同时尽量保持与完整集的分数趋势一致。([ar5iv][2])

形式化看，就是从全集 $\mathcal{D}$ 中选子集 $S$，使得：

$$
\operatorname{Rank}_{S}(f_1,\dots,f_n) \approx \operatorname{Rank}_{\mathcal{D}}(f_1,\dots,f_n)
$$

作者把这个问题近似为 **k-center coreset selection**：在嵌入空间中选择覆盖全集的代表样本。具体做法是用 CLIP 提取图像 embedding，用 BGE-M3 提取文本 embedding，然后拼接，使用 greedy k-center 选择代表点。([ar5iv][2])

### 子任务 C：动态抗污染评测

静态 benchmark 可能进入训练数据。论文观察到多模态 contamination 不只是文本重复，还包括重复图像、相似图像、相似问题模板。作者用文本 n-gram 和图像 token n-gram 检测重叠，并报告 ChartQA、DocVQA、COCO 2014、VQAv2 等在 LLaVA-NeXT 训练数据中有较高图像重叠比例。([ar5iv][2])

因此 **LiveBench** 的任务是：

$$
\mathcal{D}_t = \text{近期网页 / 新闻 / 论坛内容生成的动态评测集}
$$

它用最新网页截图构造问题，经过强多模态模型生成 Q&A、另一个模型审查、人类验证，再用 judge model 打分。论文称其每月收集约 500 个问题，最终选择 100–300 个进入当月 LiveBench。([ar5iv][2])

---

# 2. Challenge：为什么过去范式不够

## 2.1 表面问题：评测不可复现

过去每个模型团队都有自己的评测 pipeline。看似都在报 AI2D、ChartQA、MMMU、MME 分数，但具体 prompt、chat template、输出解析、choice scoring 可能不同。论文强调这种差异会导致分数不可比。([ar5iv][2])

本质上，benchmark 不是单独的数据集，而是：

$$
\text{Benchmark} = \text{Data} + \text{Prompt} + \text{Inference} + \text{Parsing} + \text{Metric}
$$

只固定 data 不固定其他部分，评测结论仍然不稳定。

## 2.2 本质问题：评测本身是一个资源受限的估计问题

真实能力空间很大：

$$
\Omega = \{\text{OCR, chart, document, VQA, science, math, webpage, grounding, dialogue, reasoning, hallucination, ...}\}
$$

任何 benchmark 只是从 $\Omega$ 中采样。要覆盖更多能力维度，就要更多数据、更多模型调用、更高成本。要低成本，就必须减少样本，但减少样本会降低覆盖。要抗污染，就要动态或私有数据，但动态数据构建和人工验证又增加成本。

所以作者提出的 trilemma 不是口号，而是一个评测系统的基本约束：**覆盖率、成本、污染风险三者互相牵制**。论文明确说不能真正打破这个三角，只能寻找 trade-off。([ar5iv][2])

## 2.3 多模态污染比纯文本污染更难

LLM contamination 多数关注文本 n-gram、题目泄漏、答案泄漏。LMM 还多一层视觉污染：

- 同一张图进入训练集；
- 相似图像进入训练集；
- 图像不同但问题模板高度相似；
- 图文 pair 被重标注后变成 instruction data。

论文用 SEED-tokenizer 把图像变成 32 个 token，再用 8-gram 检测图像重叠，这个设计说明作者把“图像污染”也转化成一种序列重叠问题。([ar5iv][2])

## 2.4 静态 benchmark 容易奖励“题库适配”

论文的 LiveBench 结果很关键：在很多静态学术 benchmark 中，开源模型可能追上甚至超过商业模型；但在 LiveBench 中，GPT-4-Turbo、GPT-4o、Claude-3.5-Sonnet 等商业模型明显领先，GPT-4-Turbo 总分 93.0，GPT-4o 92.4，Claude-3.5-Sonnet 92.3，而较强开源模型如 LLaVA-NeXT-72B、InternVL-1.5-26B 在 80 左右。([ar5iv][2])

这说明静态 benchmark 的高分不一定等价于真实世界泛化能力。论文中的失败案例也显示，开源模型会把网页上相邻但无关的标题或图片错误关联到当前问题，暴露出网页布局理解和上下文绑定能力不足。([ar5iv][2])

---

# 3. Insight & Novelty：真正的新想法是什么

## 3.1 创新一：把 LMM 评测从“跑榜”变成“标准化测量系统”

**要解决的问题**：
不同模型、不同论文、不同脚本报出来的 benchmark 分数不可比。

**Insight**：
评测不是简单地“模型 + 数据集 = 分数”，而是一个测量系统。测量系统自身必须标准化，否则分数方差里混入了 pipeline 方差。

**具体设计**：
LMMs-Eval 提供统一模型接口、统一数据处理、统一输出解析、统一日志，并尊重 instruction-tuned 模型的 chat template。([ar5iv][2])

**为什么有效**：
它控制了非模型因素。这样模型差异更可能来自模型本身，而不是来自 prompt 模板、后处理脚本或指标实现差异。

**我的判断**：
这不是算法创新，而是 evaluation infrastructure 创新。它的价值类似 `lm-eval-harness` 在 LLM 领域的作用：降低评测噪声，让社区分数更可复现。

---

## 3.2 创新二：用 coreset 思想构造 Lite benchmark

**要解决的问题**：
完整 LMM 评测覆盖广，但成本高，不适合作为训练过程中的频繁反馈信号。

**Insight**：
很多 benchmark 样本是冗余的。如果一个子集在语义空间中覆盖全集，那么它可能保留模型排序和主要能力信号。

**具体设计**：
作者用 CLIP 图像 embedding + BGE-M3 文本 embedding 表示每个样本，再用 k-center greedy 选择代表样本。Lite 集把 90,223 个样本压缩到 9,134 个样本，并在多个数据集上报告 Lite 分数与 full 分数的高相关性，例如 AI2D、ChartQA、DocVQA 等相关性大多在 0.94–0.99 区间。([ar5iv][2])

**为什么有效**：
k-center 的目标是最小化任一点到最近中心的最大距离：

$$
\min_{S:\ |S|=k} \max_{x \in \mathcal{D}} d(x,S)
$$

这等价于让子集尽量覆盖全集的语义区域。若模型错误模式主要随语义区域变化，那么 coreset 可以保留大部分评测信号。

**但要注意**：
Lite 不是“最终排行榜”的替代品。论文自己也强调 LMMs-Eval Lite 更适合训练和 ablation 时提供低成本信号，而不是完整比较不同模型家族。([ar5iv][2])

---

## 3.3 创新三：把 contamination 检测扩展到多模态空间

**要解决的问题**：
静态 benchmark 可能已经进入训练数据，导致模型分数虚高。

**Insight**：
多模态污染不能只查文本，还要查图像；而图像可以被离散化成 token 序列，再用类似文本 n-gram 的方法检测重叠。

**具体设计**：
文本端用 n-gram overlap；图像端用 SEED-tokenizer 把图像转成 1D token 序列，再用 8-gram 查重。作者发现三类污染：重复图像、相似图像、相似问题。([ar5iv][2])

**为什么有效**：
它把异质模态统一到“离散片段重叠”的检测框架里，比单纯 embedding cosine similarity 更可解释，也更容易定位具体重叠片段。

**关键证据**：
论文报告 ChartQA 图像重叠 68.64%、DocVQA 36.08%、COCO 2014 46.05%、VQAv2 46.21%，并指出这些数据集被包含在 LLaVA-NeXT 训练数据中，因此污染较严重。([ar5iv][2])

---

## 3.4 创新四：LiveBench 用“时间”作为反污染机制

**要解决的问题**：
只靠静态 benchmark 很难保证零污染；而人类 Arena 虽然更真实，但需要大量用户偏好，成本高且流量噪声大。

**Insight**：
如果评测数据来自模型训练截止之后的最新网页、新闻、论坛内容，那么污染风险自然下降。同时网页截图保留了真实世界的多模态复杂性：布局、图片、标题、上下文、相邻干扰项。

**具体设计**：
LiveBench 从新闻和论坛等动态网站收集截图，强模型生成多维度 Q&A，包括 basic understanding、contextual analysis、deeper implications、broader implications、further insights；另一个模型审查，再由人类验证；最终用 GPT-4o 等 judge model 打分。([ar5iv][2])

**为什么有效**：
它同时攻击两个问题：

1. **污染问题**：最新内容更不容易进入训练集；
2. **真实分布问题**：网页截图比人工合成题更接近真实 LMM 使用场景。

**隐含机制**：
LiveBench 实际上测试的不只是视觉问答，而是：

$$
\text{视觉定位} + \text{网页布局理解} + \text{上下文绑定} + \text{时事语义推理} + \text{抗干扰}
$$

这解释了为什么某些静态 benchmark 高分模型在 LiveBench 上会出现“把相邻标题当成相关上下文”的 hallucination。([ar5iv][2])

---

# 4. Potential Flaw：局限与脆弱点

## 4.1 Trilemma 是有启发性的抽象，但不是严格定理

论文把 wide coverage、low cost、zero contamination 描述为 impossible triangle，但这更像一个经验性系统约束，而不是被形式证明的理论下界。它合理，但仍需要更精确的定义：

$$
\begin{aligned}
&\text{Coverage 如何量化？} \\
&\text{ContaminationRisk 如何估计？} \\
&\text{Cost 是 GPU 时间、API 钱、人工标注，还是总延迟？}
\end{aligned}
$$

下一步如果要做得更硬，需要把三者转成可优化指标。

## 4.2 Lite benchmark 的代表性依赖 embedding 假设

LMMs-Eval Lite 的核心假设是：

$$
d_{\text{CLIP+BGE}}(x_i,x_j) \approx \text{模型错误模式差异}
$$

但这不一定成立。CLIP/BGE embedding 能捕捉语义相似，却未必捕捉：

- OCR 极小字体；
- 图表细粒度坐标读取；
- 多跳数学推理；
- 反事实视觉推理；
- adversarial layout；
- rare corner cases。

所以 Lite 可能保留平均趋势，却丢掉最有诊断价值的尾部失败模式。

## 4.3 Lite 的验证模型族偏窄

论文用多个 LLaVA 版本验证 Lite 与 full 的相关性。这个证据说明 Lite 对 LLaVA family 有效，但不能完全证明它对 GPT、Gemini、Claude、InternVL、Qwen-VL 等异构模型家族都同样可靠。论文也承认 Lite 主要用于训练和 ablation 信号，而非完整模型家族比较。([ar5iv][2])

## 4.4 LiveBench 的 judge model 可能引入偏置

LiveBench 用 GPT-4o 作为默认 judge，并提供 Claude-3-Opus、Gemini 1.5 Pro 作为替代 judge。([ar5iv][2])
问题是：如果 judge model 的偏好与某些商业模型输出风格更接近，那么评分可能部分反映“回答风格对齐”，而不仅是事实正确性。

更稳健的做法应当包括：

$$
\text{multi-judge ensemble} + \text{human calibration} + \text{judge disagreement analysis}
$$

否则 LiveBench 可能把 evaluator bias 误认为 model capability。

## 4.5 动态网页数据也有分布偏差

LiveBench 的网站来源包括 BBC、CNN、Bloomberg、WSJ、Reuters 等新闻源，覆盖新闻、商业、科技、国际事务等类别。([ar5iv][2])
这提升了真实性，但也会引入媒体地域、语言、政治、文化偏差。模型在 LiveBench 上高分，可能意味着它擅长西方主流新闻网页布局和时事语境，不一定代表所有真实世界多模态任务都强。

## 4.6 contamination 检测需要训练数据访问

论文自己指出，他们的 contamination 方法相对简单，并且需要访问训练数据；但大多数模型并不开源训练数据。未来需要只依赖模型行为、输出分布或黑盒查询来估计 contamination。([ar5iv][2])

---

# 5. Motivation：站在作者还没想到方法时，最自然的问题链

1. 我们为什么需要新的 LMM 评测？
   因为模型越来越强，旧 benchmark 分数越来越接近饱和，且不同论文分数不可复现。

2. 分数不可复现的根源是什么？
   不是数据集本身，而是数据准备、prompt、chat template、输出解析、metric 实现都不统一。

3. 那第一步是不是应该统一 pipeline？
   是，于是得到 LMMs-Eval。

4. 统一之后问题解决了吗？
   没有。覆盖 50+ benchmark 后，完整评测成本太高。

5. 成本高能不能直接随机采样？
   随机采样可能破坏能力覆盖，尤其对长尾任务不稳定。

6. 那如何保留覆盖？
   把样本放到语义空间中，选择能覆盖全集的代表点，于是得到 k-center coreset，也就是 LMMs-Eval Lite。

7. Lite 解决 contamination 吗？
   不解决。它只是低成本近似，数据仍然可能在训练集中出现。

8. 那如何减少污染？
   用持续更新的新数据，最好来自模型训练之后的真实世界网页。

9. 仅仅收集最新网页够吗？
   不够，还要把网页变成可评分问题，并控制问题质量。

10. 所以需要什么 pipeline？
    动态网页采集 → Q&A 生成 → 模型审查 → 人类验证 → judge 打分，于是得到 LiveBench。

---

# A. 一句话总结核心贡献

这篇论文的核心贡献是：**把 LMM 评测从零散跑榜推进为一个受“覆盖率—成本—污染风险”三角约束的系统工程，并分别用标准化框架、coreset 低成本子集、动态 LiveBench 给出三个方向的 practical trade-off。**

# B. 下一篇论文最自然做什么

最自然的下一步是做一个 **model-agnostic contamination-aware dynamic evaluation framework**：

$$
\text{黑盒污染估计} + \text{动态样本生成} + \text{多裁判一致性校准} + \text{不确定性报告}
$$

具体来说，可以研究：

1. **无需训练数据的 contamination 检测**：只通过模型输出置信度、异常一致性、重述鲁棒性、答案记忆痕迹来估计题目是否被见过。
2. **LiveBench 的 judge 校准**：用多 judge + 少量人工 gold labels 估计 judge bias。
3. **从平均分转向能力剖面**：不只报告 overall accuracy，而是报告 layout grounding、context binding、visual-text disambiguation、temporal reasoning 等能力向量。
4. **动态 benchmark 的分布控制**：让 LiveBench 不只是“最新”，还要可控地覆盖地区、语言、网站类型、任务类型和难度。

[1]: https://arxiv.org/abs/2407.12772 "[2407.12772] LMMs-Eval: Reality Check on the Evaluation of Large Multimodal Models"
[2]: https://ar5iv.org/html/2407.12772v2 "[2407.12772] LMMs-Eval: Reality Check on the Evaluation of Large Multimodal Models"

