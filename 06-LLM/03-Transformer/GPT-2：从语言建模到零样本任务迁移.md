---
title: "GPT-2：从语言建模到零样本任务迁移"
aliases: ["GPT2", "GPT-2", "Language Models are Unsupervised Multitask Learners"]
authors: ["Alec Radford", "Jeffrey Wu", "Rewon Child", "David Luan", "Dario Amodei", "Ilya Sutskever"]
conference: "OpenAI Technical Report"
year: 2019
paper_url: "https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf"
pdf_link: "[[06-LLM/03-Transformer/assets/paper_gpt2_2019.pdf]]"
cover: "[[_assets/images/gpt-2-01-language-model-zero-shot.drawio.svg]]"
created: 2026-09-13
updated: 2026-09-13
tags: ["paper/technical-report", "llm", "pretraining", "causal-lm", "zero-shot", "transfer-learning"]
status: "unread"
priority:
rating:
topics: ["LLM"]
code: "https://github.com/openai/gpt-2"
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

> **GPT-2 把 decoder-only 语言模型扩展到更大规模、更多样的网页文本：训练仍然只做“预测下一个 token”，但使用时不再必须先接任务 head 并监督微调，而是把任务线索与输入放进上下文，用同一个 LM head 生成后续文本，或比较候选文本的概率，从而观察无需目标任务参数更新的迁移能力。**

**下面几条把论文实际改了什么、以及容易被读错的地方分开列。**

- **训练目标没有变成显式的多任务 loss**：网页里的真实后续 token 就是监督；没有分别训练摘要 head、翻译 head 和问答 head。
- **重要变化不只是参数更多**：WebText、byte-level BPE、更长上下文，以及 Pre-LN 和最终 LayerNorm，共同构成这次模型升级。
- **任务条件可以由文本表达**：文档、问题、历史问答、`TL;DR:` 或翻译示例，都会改变同一个语言模型的后续分布。
- **论文重点是无任务微调的使用方式**：评测时不更新模型参数；这不意味着 GPT-2 不能微调，也不意味着所有任务都达到了实用水平。
- **“zero-shot”需要看具体设置**：论文的翻译与 Natural Questions 设置包含上下文示例；若按是否提供输入—输出示例区分，它们更接近 few-shot prompting，但仍然没有目标任务梯度更新。
- **要区分四件事**：续写流畅、语言模型指标更好、任务答案正确、完全没有训练数据重叠，并不是同一结论。

前置阅读：[[06-LLM/03-Transformer/GPT-1：从生成式预训练到语言理解微调.md]]、[[06-LLM/03-Transformer/06-transformer.md]]；输入输出 embedding 复用可结合 [[06-LLM/04-训练与推理/权重共享.md]]。

本文沿用 GPT-1 笔记的 **监督信号 → 网络表示 → 各个 loss → 任务输入与输出 → 梯度与参数更新 → 数据处理 → 下游使用 → 完整心智模型** 组织方式。

本文讨论的论文是 *Language Models are Unsupervised Multitask Learners*。它是 OpenAI 于 $2019$ 年发布的技术报告。

## 框架总览

![[_assets/images/gpt-2-01-language-model-zero-shot.drawio.svg|900]]

**读图顺序**：左侧通过语言模型损失学习参数；右侧保持训练后的权重不变，让输入上下文决定当前任务，并通过条件生成或候选似然评分获得输出。金色箭头表示训练后参数的复用，不表示还要进行一次任务微调。

读图时重点检查：

- **训练端只有 LM 目标**，不是一个显式的摘要、翻译、问答联合多头系统。
- **使用端没有任务参数更新**，但输入文本、隐状态与 KV cache 可以变化。
- **Pre-LN 后仍有最终 LayerNorm**，不能照搬 GPT-1 的 Post-LN block。
- **生成与候选评分都来自同一个词表分布**，不是为每个任务训练一个新的 head。
- **部分上下文包含示例**，不应把无梯度更新自动等同于无示例输入。

## Key Contributions

### 从 GPT-1 继续往前走：核心问题变了什么？

GPT-1 的主路线可以概括成：

> 先用语言建模获得好的初始化，再用带标签的任务数据调整整个模型。

GPT-2 进一步追问：

> 如果语言模型足够大，训练文本足够丰富，能否不为每个任务再训练参数，仅通过合适的上下文，就让它表现出完成任务的能力？

这并不是宣布“监督学习从此不需要了”。它改变的是**研究迁移能力的入口**：不仅检查预训练表示经过微调后是否有用，也检查预训练模型本身是否已经能执行某些任务。

| 核心问题               | GPT-2 的回答                    |
| ------------------ | ---------------------------- |
| 多任务监督从哪里来？         | 作者假设，多样自然文本中包含任务行为的自然示范      |
| 实际训练目标是什么？         | 对连续文本进行自回归语言建模               |
| 网络是否仍然单向？          | 是，仍然使用 causal self-attention |
| 当前要执行什么任务，怎样告诉模型？  | 通过任务线索、输入排列和上下文示例表达          |
| 是否要给每个任务新增输出 head？ | 论文的零样本路线不需要，复用同一个 LM head    |
| 输出一定是自由生成吗？        | 不一定，也可以比较候选文本的语言模型概率         |
| 测试时更新参数吗？          | 不更新；输入上下文、隐状态和缓存可以变化         |
| 更大模型是否解决了所有任务？     | 没有；任务收益不均匀，摘要、翻译和知识问答仍有明显短板  |

可以把贡献理解为：**扩大语言模型与数据的规模，并用一组不做任务微调的评测，检验“语言建模是否已经隐含地学到任务行为”。** 这里的“隐含多任务学习”是作者对现象的解释与研究假设，不是已经识别出模型内部某个独立的“任务路由器”。参见 [原论文第 1–2 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

## Method

### 1. 监督信号：仍然预测后续文本，但文本中可能包含任务示范

#### 1.1 从一个条件分布，走向带任务条件的分布

单个任务通常写成：

$$
p(y\mid x).
$$

若同一个输入既可以要求翻译，也可以要求总结，那么仅有 $x$ 不足以确定期望输出；还需要任务条件 $\tau$：

$$
p(y\mid x,\tau).
$$

GPT-2 的思路是：**不一定通过新增网络模块来提供 $\tau$，也可以把它变成输入文本的一部分。**

例如，文章后面的 `TL;DR:` 可以暗示简短总结；已有的双语句对可以暗示继续完成翻译。这是把“要做什么”编码到上下文，而不是调用模型内部一个已知名称的摘要函数。

#### 1.2 “无监督多任务”不等于“训练时完全没有答案文本”

假设一段自然文本包含如下内容：

> Mia walked home in the rain without an umbrella. She got wet.

语言模型不需要额外的“常识推理任务”标签，也可以用前文预测后面的 `wet`。如果另一些文本包含问题与回答、原文与译文、正文与总结，模型同样需要预测这些序列中的后续部分。

因此要区分：

- **没有显式任务监督**：训练器不必知道这段文字属于翻译、摘要还是问答。
- **自然文本中包含人类行为示范**：文本作者可能已经写出了答案、译文、解释或摘要。
- **测试时的正确答案不能泄漏**：评测当前问题时，不能把它的真实答案直接放到待预测位置之前。

原论文称其为 unsupervised learning；按监督目标由文本自身构造的含义，也可以把 next-token prediction 称为自监督学习。**“无任务标签”不能被改写成“语料里没有任何问答或翻译信息”。**

#### 1.3 训练和使用：一次学习参数，多种上下文调用

记训练语料为 $\mathcal U$，参数初始化为 $\theta_0$：

$$
\theta_0
\xrightarrow{\text{在 }\mathcal U\text{ 上优化语言模型目标}}
\theta^*.
$$

在论文的无任务微调评测中：

$$
\theta_{\mathrm{QA}}
=\theta_{\mathrm{summary}}
=\theta_{\mathrm{translation}}
=\theta^*.
$$

这里表示不同任务使用**同一份权重**；任务输入格式和解码规则可以不同。它与 GPT-1 为不同任务得到各自的微调模型不同。

这也是本文使用“零样本任务迁移”时的主要含义。至于上下文里有没有示例，要到具体任务设置中另行检查，不能仅凭 zero-shot 这个词判断。参见 [原论文第 2 节与第 3.5–3.8 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 2. 网络架构：更大的单向 Transformer

#### 2.1 Token 与可学习绝对位置 embeddings

设输入 token IDs 为：

$$
x=(x_1,\dots,x_T),
\qquad x_t\in\{1,\dots,V\}.
$$

为便于公式书写，这里使用从 $1$ 开始的 token 索引；实际代码中的 token IDs 从 $0$ 开始。

记 token embedding 与位置 embedding 为：

$$
E\in\mathbb R^{V\times d},
\qquad
P\in\mathbb R^{T_{\max}\times d}.
$$

初始表示为：

$$
h_t^{(0)}=E_{x_t,:}+P_{t,:},
\qquad
H^{(0)}\in\mathbb R^{T\times d}.
$$

GPT-2 的词表大小为 $V=50{,}257$，上下文上限为 $T_{\max}=1{,}024$。位置表示仍然是**可学习的绝对位置 embeddings**，不是 RoPE，也不是原始 Transformer 的正弦位置编码。

官方代码中的 `wte` 对应 token embeddings，`wpe` 对应位置 embeddings；输入通过查表后相加进入 Transformer。参见 [官方网络实现](https://github.com/openai/gpt-2/blob/master/src/model.py)。

#### 2.2 四档规模：先区分原论文标注与发布权重名称

下表采用官方发布权重的目录名称；FFN 中间维度按官方实现的 $4d$ 给出：

| 发布权重名称 | Transformer 层数 $L$ | 隐藏维度 $d$ | Attention heads | FFN 中间维度 |
| --- | --- | --- | --- | --- |
| `124M` | $12$ | $768$ | $12$ | $3{,}072$ |
| `355M` | $24$ | $1{,}024$ | $16$ | $4{,}096$ |
| `774M` | $36$ | $1{,}280$ | $20$ | $5{,}120$ |
| `1558M` | $48$ | $1{,}600$ | $25$ | $6{,}400$ |

这些配置中，单个 head 的维度均为 $d_h=64$。

**原论文的表格和曲线使用 `117M`、`345M`、`762M`、`1542M` 作为模型标签。官方 README 后来明确说明原参数量统计有误。** 下文保留论文截图的原始标注；这些标签与发布名称的差异不是另一组独立实验。

报告将最大的约 $1.5$ billion 参数模型称为 GPT-2；在后续发布语境中，GPT-2 也常指整个模型家族。参见 [官方参数量更正](https://github.com/openai/gpt-2)、[模型卡](https://github.com/openai/gpt-2/blob/master/model_card.md)，以及发布配置 [124M](https://openaipublic.blob.core.windows.net/gpt-2/models/124M/hparams.json)、[355M](https://openaipublic.blob.core.windows.net/gpt-2/models/355M/hparams.json)、[774M](https://openaipublic.blob.core.windows.net/gpt-2/models/774M/hparams.json)、[1558M](https://openaipublic.blob.core.windows.net/gpt-2/models/1558M/hparams.json)。

#### 2.3 一个 block 内部：先归一化，再计算子层，最后残差相加

省略不影响主干说明的实现细节，GPT-2 的一个 block 可以写为：

$$
\widetilde H^{(\ell)}
=H^{(\ell-1)}
+\operatorname{MHA}_{\mathrm{causal},\ell}
\left(\operatorname{LN}_{\ell,1}(H^{(\ell-1)})\right),
$$

$$
H^{(\ell)}
=\widetilde H^{(\ell)}
+\operatorname{FFN}_{\ell}
\left(\operatorname{LN}_{\ell,2}(\widetilde H^{(\ell)})\right).
$$

其中：

$$
\operatorname{FFN}(H)
=\operatorname{GELU}(HW_1+b_1)W_2+b_2,
$$

$$
W_1\in\mathbb R^{d\times4d},
\qquad
W_2\in\mathbb R^{4d\times d}.
$$

> [!info] LayerNorm 到底在归一化什么？
> 在这里，LayerNorm 对**每个 token 自己的隐藏向量**，沿 $d$ 个特征维度计算均值与方差，而不是把整段文本或整个 batch 混在一起统计。对 $u\in\mathbb R^d$，有：
>
> $$
> \operatorname{LN}(u)_i
> =\gamma_i\frac{u_i-\mu(u)}{\sqrt{\sigma^2(u)+\epsilon}}+\beta_i.
> $$
>
> $\mu(u)$、$\sigma^2(u)$ 是该向量的均值和方差，$\epsilon$ 用于数值稳定，$\gamma_i$、$\beta_i$ 是可学习的缩放与偏移。因此，最终输出不必严格保持零均值、单位方差；**LayerNorm 本身也不会让当前位置读取未来 token**。参见 [官方 `norm` 实现](https://github.com/openai/gpt-2/blob/master/src/model.py)。

关键在 LayerNorm 的位置：

- **GPT-1 的 Post-LN**：$\operatorname{LN}(H+F(H))$。
- **GPT-2 的 Pre-LN**：$H+F(\operatorname{LN}(H))$。

这是计算图的变化，不只是把同一个框挪到图的另一侧。对于后者，残差主路径没有在每次相加后立即再经过一次 LayerNorm；归一化作用于子层的输入。

官方 `block` 明确对应 `attn(norm(x))`、残差相加、`mlp(norm(x))`、残差相加。它仍然没有独立的 encoder，也没有读取 encoder 输出的 cross-attention。参见 [官方 `block` 与 `mlp`](https://github.com/openai/gpt-2/blob/master/src/model.py)。

#### 2.4 不能漏掉最后的 LayerNorm

全部 Transformer blocks 之后，GPT-2 还有一个最终归一化：

$$
H^f=\operatorname{LN}_f(H^{(L)}).
$$

再通过共享 token embedding 映射回词表：

$$
Z=H^fE^\top\in\mathbb R^{T\times V},
$$

$$
p_\theta(x_{t+1}=v\mid x_{\le t})
=\operatorname{softmax}(h_t^fE^\top)_v.
$$

因此，“GPT-2 使用 Pre-LN”不意味着输出处完全没有 LayerNorm。官方代码中的 `ln_f` 位于所有 blocks 之后、词表投影之前。

同样，$h_t^f$ 是隐藏表示，$h_t^fE^\top$ 是词表 logits，softmax 后才是下一 token 的概率分布。三者不能混用。输入查表与输出投影复用 $E$，不表示 $E$ 在训练时被冻结。

> [!question] 为什么 Pre-LN 之后还要 Final Norm？它不会破坏第 3 节的梯度通路吗？
> **分支每次读取了归一化后的输入，不等于主 residual stream 也一直保持归一化。** 每层结束时做的是 $X_{j+1}=X_j+\Delta X_j$，所以最终的 $X_S$ 是初始表示与许多增量累加的结果，其尺度并没有被每个分支内部的 LN 固定住。
>
> 这在输出端很重要：对于固定的词表投影，如果隐藏向量整体放大，logits 也会随之放大，softmax 的分布就可能变得更尖锐。**Final LN 的作用，是在把最终表示交给 LM head 之前，再整理一次尺度，并施加可学习的缩放与偏移。** 这就是上面的 $H^f=\operatorname{LN}_f(H^{(L)})$，随后才计算 $H^fE^\top$。
>
> 它当然仍参与反向传播：梯度从 LM head 传回时，先经过这一次 Final LN，再进入内部残差堆叠。但**在整段堆叠末尾经过一次 LN**，不等于**在每个残差子层的主干上都经过一次 LN**。第 3 节推导的恒等通路指的是堆叠内部、最终 LN 之前的 $X_0\rightarrow X_S$，不是从输入一直到 logits 都没有任何变换。参见[官方 `block`、`ln_f` 与词表投影](https://github.com/openai/gpt-2/blob/master/src/model.py)。

### 3. 归一化布局：从 Post-LN 到 Pre-LN

> 两种布局的差别不只是把归一化挪了个位置。这一节接着讲三件事：**这个改动在深层网络里改变了什么**、**训练时为什么要配套 warmup**、**残差初始化为什么要按深度缩放**。推导可以跳过，结论要记住：**Pre-LN 让残差主干不必在每个子层都穿过一次 LN，深层网络因此保留了更直接的信号与梯度通路。**

#### 3.1 前向与反向：梯度通路改变了什么

> [!question]- 为什么 GPT-1 使用 Post-LN，GPT-2 改用 Pre-LN？
> **主要原因不是“Post-LN 不对”，而是 GPT-1 继承了原始 Transformer 的设计；随着模型向更深的网络扩展，保留更直接的残差与梯度通路，成为更重要的优化考虑。**
>
> **先看历史继承。** $2017$ 年的 Transformer 在子层计算与残差相加之后做 LayerNorm；$2018$ 年的 GPT-1 沿用这一布局，保留因果 self-attention 和 FFN，不使用 encoder–decoder cross-attention。GPT-1 的 $12$ 层网络，配合初始化、学习率 warmup 等训练设置，可以有效训练。因此，不能倒过来说“既然后来常用 Pre-LN，GPT-1 当时就选错了”。参见[原始 Transformer 第 3.1 节](https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf)、[GPT-1 第 4.1 节](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)与[GPT-1 官方实现](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。
>
> **再看扩展时的变化。** 到了 $2019$ 年，GPT-2 最大模型扩展到 $48$ 层，并已经采用 **Pre-LN blocks + Final LayerNorm**。报告把这种改动类比于预激活残差网络：归一化移到分支内部，而残差主路径保留直接相加的形式。它不是后来才加到 GPT-2 上的技巧。参见[GPT-2 第 2.3 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。
>
> **真正要理解的不是“LN 往前挪了一格”，而是：旧表示向前传、上游梯度向后传时，是否必须在每个子层都穿过一次 LN。** 下面从前向计算与反向传播把这条因果链展开。

> [!tip]- 先看前向：Pre-LN 归一化的是给子层的输入，不是残差主干本身
> 下面用 $X_j$ 表示第 $j$ 个残差子层的输入（该子层读到的 residual stream），用 $F_j$ 表示 Attention 或 FFN。它与第 2.3 节的 $H^{(\ell)}$ 是同一组量，只是这里按残差子层逐个编号；大写 $X_j$ 是整段序列的隐藏表示，与 token ID 的小写 $x_t$ 不同。求导时把整个序列的隐藏表示展平成向量，但 LN 仍然逐 token 计算。这里按**残差子层**计数，一个 GPT-2 block 包含 Attention、FFN 共 $2$ 个这样的子层。
>
> **Post-LN：先把新信息加进主干，再归一化整个结果。**
>
> $$
> X_{j+1}=\operatorname{LN}_j\bigl(X_j+F_j(X_j)\bigr).
> $$
>
> 因此，下一子层收到的不只是“旧表示加一个增量”，而是这个和**再经过 LN 变换**的结果。
>
> **Pre-LN：先读取主干的归一化版本，算出增量，再写回原主干。**
>
> $$
> \widehat X_j=\operatorname{LN}_j(X_j),
> \qquad
> \Delta X_j=F_j(\widehat X_j),
> \qquad
> X_{j+1}=X_j+\Delta X_j.
> $$
>
> Attention 和 FFN 因而可以理解成：**读取 residual stream → 处理归一化后的输入 → 写回一个增量**。所谓“归一化一个副本”，只是说计算图分成主干和分支，并不是要求复制物理内存，更不是把分支的梯度切断。
>
> 做一个最直观的检查：假设把分支设成恒为零的函数 $F_j\equiv0$，Pre-LN 就是 $X_{j+1}=X_j$；Post-LN 却仍是 $X_{j+1}=\operatorname{LN}_j(X_j)$。**两者都有加号，但只有前者在分支关闭时直接退化成恒等映射。**

> [!example]- 从偏导数看 Pre-LN：上游梯度如何分成两路？
> 先把分支合写成 $g_j(X_j)=F_j(\operatorname{LN}_j(X_j))$，则：
>
> $$
> X_{j+1}=X_j+g_j(X_j).
> $$
>
> 下面把隐藏状态之间的梯度写成偏导数 $\partial\mathcal L/\partial(\cdot)$，并按**列向量**理解：反向传播时偏导矩阵要转置，作用在从上层传来的梯度上。参数上的梯度仍按惯例写成 $\nabla_\theta\mathcal L$；其中 $I$ 是单位矩阵，对应主干上那条恒等通路。
>
> $$
> \begin{aligned}
> \frac{\partial\mathcal L}{\partial X_j}
> &=\left(\frac{\partial X_{j+1}}{\partial X_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_{j+1}}\\
> &=\underbrace{\frac{\partial\mathcal L}{\partial X_{j+1}}}_{\text{沿恒等主干直接传回}}
> +\underbrace{\left(\frac{\partial g_j}{\partial X_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_{j+1}}}_{\text{经过分支后传回}}.
> \end{aligned}
> $$
>
> 这正是残差加法的反向规则：
>
> 1. 上游梯度到达加号，分别传给主干输入和分支输出。
> 2. **主干是恒等映射，所以原样收到 $\partial\mathcal L/\partial X_{j+1}$。**
> 3. 分支先经过 $F_j$ 的反向，再经过 LN 的反向，最后在共同输入 $X_j$ 处与主干梯度相加：
>
> $$
> \left(\frac{\partial g_j}{\partial X_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_{j+1}}
> =\left(\frac{\partial\operatorname{LN}_j}{\partial X_j}\right)^{\!\top}
> \left(\frac{\partial F_j}{\partial\widehat X_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_{j+1}},
> \qquad
> \widehat X_j=\operatorname{LN}_j(X_j).
> $$
>
> **“梯度高速公路”指的就是第一项：它不必先经过 Attention、FFN 或这一子层的 LN，便能到达前一层。** 关键不是 LN 的导数变得完美了，而是梯度不再只有穿过这些变换这一条路。

> [!example]- 再看 Post-LN：为什么有 shortcut，仍然绕不过 LN？
> 令 $u_j=X_j+F_j(X_j)$，则 $X_{j+1}=\operatorname{LN}_j(u_j)$。现在从上往下反传时，**先遇到 LN，然后才到达残差加号**。到达加号处的梯度已经变成：
>
> $$
> \frac{\partial\mathcal L}{\partial u_j}
> =\left(\frac{\partial\operatorname{LN}_j}{\partial u_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_{j+1}}.
> $$
>
> 之后才分成两路：
>
> $$
> \frac{\partial\mathcal L}{\partial X_j}
> =\underbrace{\frac{\partial\mathcal L}{\partial u_j}}_{\text{沿 shortcut 传回}}
> +\underbrace{\left(\frac{\partial F_j}{\partial X_j}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial u_j}}_{\text{经过子层传回}}.
> $$
>
> 对照 Pre-LN，shortcut 收到的已经不是原封不动的 $\partial\mathcal L/\partial X_{j+1}$，而是先被 $\left(\partial\operatorname{LN}_j/\partial u_j\right)^{\!\top}$ 变换过的结果。LN 的均值、方差又依赖输入，它的导数并不是一个固定的缩放常数。
>
> **所以问题不在于“Post-LN 没有残差连接”，而在于“残差两路之外还有一次 LN，连 shortcut 都必须经过它”。**

> [!note]- 堆很多层以后：为什么“残差流”这个心智模型特别有用？
> 设共有 $S$ 个残差子层；对于本文每个 block 含 Attention 和 FFN 的结构，$S=2L$。在最终 LN 之前，Pre-LN 的前向关系可以逐层展开为：
>
> $$
> X_S=X_0+\sum_{j=0}^{S-1}g_j(X_j).
> $$
>
> 也就是：**一个持续向前的主 residual stream，各个子层依次向里面写入新的贡献。** 这不是说所有分支独立或能跨层同时计算：后面的 $g_j$ 仍然读取已经包含前面增量的 $X_j$。
>
> 再看从 $X_0$ 到 $X_S$ 的偏导链（沿用列向量约定）。为突出结构，下面省略各偏导的求值位置，只保留链式相乘的顺序：
>
> $$
> \frac{\partial\mathcal L}{\partial X_0}
> =\left(\frac{\partial X_S}{\partial X_0}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_S}
> =\left(I+\frac{\partial g_0}{\partial X_0}\right)^{\!\top}
> \cdots
> \left(I+\frac{\partial g_{S-1}}{\partial X_{S-1}}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_S}.
> $$
>
> 把乘积展开，其中总有一项是在每个括号都选 $I$，它就是 $\frac{\partial\mathcal L}{\partial X_S}$ 本身。这对应**一路沿所有 shortcut 传递**的路径。
>
> Post-LN 则是：
>
> $$
> \frac{\partial\mathcal L}{\partial X_0}
> =\left(I+\frac{\partial F_0}{\partial X_0}\right)^{\!\top}
> \left(\frac{\partial\operatorname{LN}_0}{\partial u_0}\right)^{\!\top}
> \cdots
> \left(I+\frac{\partial F_{S-1}}{\partial X_{S-1}}\right)^{\!\top}
> \left(\frac{\partial\operatorname{LN}_{S-1}}{\partial u_{S-1}}\right)^{\!\top}
> \frac{\partial\mathcal L}{\partial X_S}.
> $$
>
> 即使每层都选 shortcut，剩下的也仍是 $\left(\frac{\partial\operatorname{LN}_0}{\partial u_0}\right)^{\!\top}\cdots\left(\frac{\partial\operatorname{LN}_{S-1}}{\partial u_{S-1}}\right)^{\!\top}$ 这类因子，而不是恒等映射。因此，随着深度增加，信号和梯度更依赖这些变换的共同尺度与方向；控制不好时，容易出现梯度过大、过小或层间不均衡。
>
> **Pre-LN 的优势是少了一项“每层主干都必须经过归一化导数”的约束，从而让深层网络通常更容易优化。** 但恒等项只是一条路径的贡献，其他路径仍可能放大它，或与它在某些方向上抵消；不能据此推出整体梯度范数永远稳定。
#### 3.2 训练稳定性：warmup 与后续研究

> [!question]- 这为什么又会变成“Post-LN 对 warmup 更敏感”？
> 上面解释的是隐藏状态之间的梯度路径；继续反传到参数后，真正影响训练的是更新量。用梯度下降形式说明：
>
> $$
> \Delta\theta=-\eta\nabla_\theta\mathcal L.
> $$
>
> 如果初始化时某些参数的梯度很大，一开始就使用较大学习率 $\eta$，就可能把参数推得太远，使后续激活和梯度更加不稳定。**Warmup 的作用，是先用较小学习率限制早期更新，再逐步升高学习率。** 它不是让 LN 先积累一批运行均值或方差；这里的 LN 统计来自当前 token 的特征。
>
> [Xiong 等的研究](https://proceedings.mlr.press/v119/xiong20b.html)（ICML，$2020$）进一步在其理论假设下分析了这一点：Post-LN 在初始化时，靠近输出端的参数梯度较大；Pre-LN 的初始化梯度尺度更平稳，并在文中实验中可以省去 warmup。
>
> 这为“Pre-LN 更容易稳定训练”的经验提供了后续解释，**不是 GPT-2 在 $2019$ 年已经完成的理论证明，也不意味着所有 Pre-LN 模型都应该去掉 warmup**。GPT-2 的变化应连同残差初始化、深度和学习率一起理解，而不是只看 LN 的位置。

> [!info]- 后来的模型为什么会出现 Pre-RMSNorm？
> 这里有两个独立的问题：**归一化放在哪里**，以及**用什么函数归一化**。从 Post-LN 到 Pre-LN，改变的是前者；从 LayerNorm 换成 RMSNorm，改变的是后者。
>
> 对一个 token 的向量 $u\in\mathbb R^d$，常见的无偏置 RMSNorm 写法是：
>
> $$
> \operatorname{RMSNorm}(u)_i
> =\gamma_i\frac{u_i}{\sqrt{\frac{1}{d}\sum_{k=1}^{d}u_k^2+\epsilon}}.
> $$
>
> 与 LayerNorm 相比，它不减去均值，而是直接用均方根控制尺度，省去了中心化等计算。其设计动机是：不一定要同时获得平移不变性和尺度控制，保留后者也可能足以支持有效训练。具体加速还取决于实现，不能把某个实验的收益当成所有模型固定的加速比例。参见 [RMSNorm 原论文](https://papers.neurips.cc/paper_files/paper/2019/hash/1e8a19426224ca89e83cef47f1e7f53b-Abstract.html)。
>
> 例如，[LLaMA 第 2.2 节](https://arxiv.org/pdf/2302.13971)明确采用子层输入归一化，并使用 RMSNorm；对应的布局仍然是：
>
> $$
> X_{j+1}=X_j+F_j(\operatorname{RMSNorm}_j(X_j)).
> $$
>
> 所以其恒等主路径仍然存在。**Pre-Norm 是这类布局的统称；GPT-2 本身用的是 LayerNorm，不应把后来的 RMSNorm 写成 GPT-2 原始结构。**

> [!warning]- 那么 Pre-LN 是否在所有方面都优于 Post-LN？
> **更容易优化，不等于所有训练预算、深度和任务下的最终效果都更好。** 恒等通路解决的是深层网络中的一类优化困难，不会自动保证每层都学到了同样有用的变换。
>
> 从残差加和式还可以提出一个要检查的问题：如果某些层的分支增量相对主干很小，即 $\lVert g_j(X_j)\rVert/\lVert X_j\rVert\ll1$，那么相邻两层的表示在相对尺度上就很接近。但这只说明更新较小，**不能直接推出这些层没有作用，或模型的“有效深度”必然下降**；一个小增量也可能改动任务相关的关键方向，需要结合逐层分析或消融验证。
>
> 反过来，Post-LN 每层都做归一化，也不意味着它“强制每层学到新的语义”，更不能据此证明其表示质量必然更好。实际比较要同时考虑初始化、残差缩放、优化器与训练预算。
>
> 例如，[DeepNet / DeepNorm](https://arxiv.org/abs/2203.00555)通过调整残差连接和初始化，稳定训练了更深的 Transformer；文中一些翻译设置下，收敛的 Post-LN 基线也优于基础 Pre-LN。这说明 **Pre-LN 不是深层训练的唯一可行路线**，后续研究仍在联合改进归一化、残差与初始化，而不是已经宣布某种布局在所有方面胜出。

#### 3.3 残差初始化：为什么会出现平方根

原论文还说明，残差层初始化考虑了深度累积效应，按 $1/\sqrt{N_{\mathrm{res}}}$ 缩放相应权重，其中 $N_{\mathrm{res}}$ 表示论文所说的 residual layers 数量。

它不宜直接等同于 Transformer block 数量 $L$。**加载已训练 checkpoint 时使用的是 checkpoint 权重；公开推理代码里 `conv1d` 的默认初始化参数不等于原始训练配方。** 参见 [原论文第 2.3 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)与[官方网络代码](https://github.com/openai/gpt-2/blob/master/src/model.py)。

> [!example]- 为什么初始化缩放会出现平方根？
> 做一个**理想化的方差估算**：假设同一坐标上，各残差分支的新增量 $\Delta_i$ 均值为零、方差为 $\sigma^2$，且彼此不相关。那么：
>
> $$
> \operatorname{Var}\left(\sum_{i=1}^{N_{\mathrm{res}}}\Delta_i\right)
> =N_{\mathrm{res}}\sigma^2,
> \qquad
> \operatorname{Var}\left(\sum_{i=1}^{N_{\mathrm{res}}}\frac{\Delta_i}{\sqrt{N_{\mathrm{res}}}}\right)
> =\sigma^2.
> $$
>
> 所以，分支数量增加时，按平方根缩小每次加入的量，可以抵消这个简化模型中的方差累积。这帮助理解论文为何关注残差初始化；**真实分支并不独立，缩放权重也不能不加条件地等同于缩放整个分支输出**，因此它不是对 GPT-2 全部训练动态的精确推导。

**把这一节收束成一句话**：GPT-1 沿用了“残差相加后，归一化整个结果”的布局；GPT-2 则让子层读取归一化后的 residual stream、把增量写回原主干，并在堆叠末尾做 Final LN。**重要的演化是让深层网络保留更直接的信号与梯度通路，而不只是 LN 的摆放风格变了。**

### 4. Causal mask：有问题和答案的文本，也不能偷看未来

#### 4.1 Query、Key、Value 都来自当前序列

对某个 attention head，记归一化后的子层输入为 $G$，省略投影偏置：

$$
Q=GW_Q,\qquad K=GW_K,\qquad V_H=GW_V.
$$

使用 $V_H$ 表示 value 矩阵，避免与词表大小 $V$ 混淆。注意力为：

$$
\operatorname{Attention}(G)
=\operatorname{softmax}
\left(\frac{QK^\top}{\sqrt{d_h}}+M\right)V_H,
$$

$$
M_{t,j}=
\begin{cases}
0,&j\le t,\\
-\infty,&j>t.
\end{cases}
$$

某个问题后面即使有真实答案，问题位置的表示也不能读取后面的答案 token。答案位置只能在自身左侧已知文本的基础上继续预测。

#### 4.2 为什么训练可以并行，生成却要逐步继续？

训练时真实文本已经存在，可以同时计算各位置的条件分布，掩码保证依赖关系正确；这通常称为 teacher forcing。

生成时后续 token 尚不存在，需要先得到一个 token，再把它加入上下文。因此，自由生成存在序列依赖。

任务上下文里加入 `TL;DR:` 或多个问答示例，不会把这套 mask 自动变成双向 attention。整个序列仍然通过同一条因果路径处理。参见 [官方 `attention_mask` 与 `attn`](https://github.com/openai/gpt-2/blob/master/src/model.py)。

> [!example] 为什么 mask 允许看当前位置，却不算偷看答案？
> 暂时把每个词当作一个 token，用 `She got wet` 举例：
>
> - 输入位置上的 `She` 负责预测 `got`；它可以看 `She`，但不能看右侧的 `got`。
> - 输入位置上的 `got` 负责预测 `wet`；它可以看 `She got`，但不能看右侧的 `wet`。
>
> 因此，mask 保留对角线，是允许模型读取**当前已知 token**；label shift 才决定它要预测的是**下一个 token**。若把输入 `got` 对齐到目标 `got`，即使保留 causal mask，也会把任务变成可直接复制当前输入的问题。这里的按词切分只用于说明对齐，不是实际 BPE 结果；错位计算可对照 [GPT-1 官方 LM loss 实现](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。

### 5. 语言模型 loss：单一目标怎样可能包含多种任务？

#### 5.1 自回归分解与交叉熵

忽略上下文窗口截断，一段文本的联合概率可以分解为：

$$
p_\theta(x_1,\dots,x_T)
=p_\theta(x_1)
\prod_{t=1}^{T-1}p_\theta(x_{t+1}\mid x_{\le t}).
$$

以单条序列为例，省略首 token 的边界约定，采用平均负对数似然记法：

$$
\mathcal L_{\mathrm{LM}}(x)
=-\frac{1}{T-1}
\sum_{t=1}^{T-1}
\operatorname{log}p_\theta(x_{t+1}\mid x_{\le t}).
$$

这是对训练目标的教学写法，不是在声称公开了论文原始训练器的全部 batch 归约细节。有效位置、边界和 padding 的处理都需要在实现中明确。

与 GPT-1 的监督微调目标不同，这里没有额外的：

$$
\mathcal L_{\mathrm{task}}
+\lambda\mathcal L_{\mathrm{LM}}.
$$

**GPT-2 原论文的主要训练路线不是“给 GPT-1 的任务 loss 再加大一个 LM 系数”，而是以语言建模本身为训练目标，检查它能否直接迁移。**

#### 5.2 输入与标签需要错位

训练位置 $t$ 的职责是：

$$
\boxed{
h_t^f\text{ 可以利用 }x_{\le t},
\quad\text{目标是 }x_{t+1}.
}
$$

例如，在 `She got` 后预测 `wet`，不能让负责预测 `wet` 的表示先读取 `wet` 自身。

两个条件缺一不可：

1. causal mask 阻止读取未来输入。
2. label shift 把当前位置的输出与下一个 token 对齐。

因此，**“把整段文本交给模型”是训练时的计算方式，不表示每个位置都看到了整段文本。**

#### 5.3 答案 token 的 loss，本来就是整段文本 loss 的一部分

为解释机制，假设一条文本经过排列后包含：任务说明、输入、答案。记“预测目标 $x_{t+1}$ 属于答案部分”的预测位置 $t$ 的集合为 $\mathcal A$，则可以把未归一化的 token 损失拆开：

$$
\sum_t\ell_t
=\sum_{t\in\mathcal A}\ell_t
+\sum_{t\notin\mathcal A}\ell_t,
$$

$$
\ell_t=-\operatorname{log}p_\theta(x_{t+1}\mid x_{\le t}).
$$

其中，预测答案部分的误差已经包含在整段语言建模误差中。训练器不必显式拿到集合 $\mathcal A$，也可以对这些答案 token 进行学习。

这提供了一种理解：如果文本中足够多地出现某种任务结构，模型为了预测后续内容，可能学会利用这种结构。

但还要回答三个问题：

- 相关任务结构在语料中是否足够常见？
- 有限模型容量是否愿意把表示能力分配给它？
- 优化过程是否真的学到了可迁移规律，而不是局部共现或记忆？

#### 5.4 不要把理想化论证读成真实世界的充分保证

原论文讨论了一个理想化设置：明确排列的任务样例本身也是文本，任务输出位置上的预测可以被全序列语言建模覆盖。

但对于有限容量、有限数据和未收敛的模型，**总 loss 降低，并不保证每个任务子集上的 loss 都降低，更不保证最终任务指标同步提高。** 上面的拆分式只是说明监督信号可以存在，不是对任务能力的充分证明。

把这个思想推广到真实网页中的无显式标签任务，是作者提出并通过实验检验的假设。它不能仅靠“都是 next-token prediction”一句话完成证明。参见 [原论文第 2 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 6. 无需任务微调：Prompt 改变的是条件，不是模型参数

#### 6.1 把任务组织成上下文与后续文本

记输入为 $x$，任务线索为 $\tau$，可选的上下文示例集合为 $\mathcal D$，构造上下文：

$$
c=\operatorname{Serialize}(\tau,x,\mathcal D).
$$

若目标输出是 token 序列 $a=(a_1,\dots,a_m)$，语言模型为它赋予：

$$
p_{\theta^*}(a\mid c)
=\prod_{j=1}^{m}
p_{\theta^*}(a_j\mid c,a_{<j}).
$$

这里的 $\operatorname{Serialize}$ 是本文用来统一描述不同输入构造的记号，**不是 GPT-2 官方提供的一套统一指令模板**。

同一个模型可以因为 $c$ 不同而改变输出。例如，文章后继续正文与文章后跟上 `TL;DR:`，对应的条件分布不同；模型参数仍然都是 $\theta^*$。

#### 6.2 GPT-2 的任务输出通常仍在词表空间

GPT-1 的分类微调会新增任务输出参数，把末端表示映射到类别空间。GPT-2 论文的生成式任务路径则继续使用：

$$
h_t^f\longrightarrow h_t^fE^\top
\longrightarrow \text{下一 token 概率}.
$$

因此，答案可以包含多个 token，需要多步生成；不是把一个隐状态送入新训练的问答分类器，就一次返回答案类别。

| 路线 | 输出空间 | 目标任务参数更新 |
| --- | --- | --- |
| GPT-1 的监督分类微调 | 新增 head 定义的类别空间 | 更新骨干与任务 head |
| GPT-2 的条件生成 | 原有词表，逐步形成输出文本 | 不更新 |
| GPT-2 的候选评分 | 从同一 LM 的文本概率得到候选分数 | 不更新 |

#### 6.3 不需要机械照搬 `[EXTRACT]`

GPT-1 笔记中的 `[START]`、`[DELIM]`、`[EXTRACT]` 用于解释其任务输入变换与末端表示提取。

GPT-2 的主要零样本路线没有要求为每个任务新增这组结构标记，也没有默认新增一个接在 `[EXTRACT]` 表示后的分类 head。

`A:` 和 `TL;DR:` 在这里是文本模式。**不能因为论文称某段内容为 prompt 或提示，就假设它一定对应一个专门注册的单独 token。** 它们仍要经过 tokenizer，可能被切成多个 token。

#### 6.4 Zero-shot、few-shot 与 fine-tuning 是不同维度

判断一个设置时，至少问两个问题：

1. 是否通过目标任务的数据更新了模型参数？
2. 是否在当前上下文中提供了任务输入—输出示例？

| 使用方式 | 目标任务梯度更新 | 上下文示例 |
| --- | --- | --- |
| 只给任务线索与待处理输入 | 无 | 无 |
| 用示例对帮助模型识别格式 | 无 | 有 |
| 监督微调后执行任务 | 有 | 是否提供示例是另一选择 |

原论文强调第一列的“无参数或架构修改”，但翻译和 Natural Questions 明确使用示例对作为上下文。按第二列严格区分，这些不是“上下文里一个示例都没有”的设置。

**上下文学习与参数学习的区别，不在于有没有看到答案字符串，而在于答案属于哪个样本、以何种方式进入计算，以及是否触发权重更新。** 不能把已完成的示例答案与当前测试问题的答案泄漏混为一谈。

### 7. 两种读出方式：生成答案，或比较候选文本的似然

#### 7.1 条件生成：答案原本还不存在

给定上下文 $c$，先预测 $a_1$，再预测 $a_2$，直到达到停止条件或生成长度限制。

语言模型提供每一步的条件分布，解码算法决定如何从分布中选择 token。贪心选择、随机采样与截断采样不是不同的任务 head，也不是不同的预训练 loss。

#### 7.2 贪心生成不等于找到概率最大的整段答案

贪心解码逐步选择当前概率最大的 token：

$$
\hat a_j
=\operatorname*{arg\,max}_{v}
p_{\theta^*}(v\mid c,\hat a_{<j}).
$$

每一步局部最优，不保证整段输出的联合概率全局最优；更不保证任务指标最优。论文在阅读理解与翻译中使用这一简单读出方式，是具体实验设置，而不是普遍最佳的生成规则。

#### 7.3 Temperature 与 top-k 改变采样分布，不改变参数

记当前词表 logits 为 $z$，温度为 $\tau_{\mathrm{temp}}>0$，保留的 top-k token 集合为 $\mathcal V_k$。一种截断采样分布为：

$$
q(v)=
\begin{cases}
\dfrac{\operatorname{exp}(z_v/\tau_{\mathrm{temp}})}
{\sum_{u\in\mathcal V_k}\operatorname{exp}(z_u/\tau_{\mathrm{temp}})},&v\in\mathcal V_k,\\
0,&v\notin\mathcal V_k.
\end{cases}
$$

这里用 $q$ 而不是继续写 $p_\theta$，是为了区分**解码时处理后的分布**与原语言模型分布。

- 截断限制候选集合。
- 温度调整 logits 的相对尖锐程度。
- 随机采样决定本次选中哪个 token。
- 三者都不是对参数进行一次训练。

原论文摘要实验采用 $k=2$，附录的一些文本生成分析使用 $k=40$，不能把它们混写成所有实验共用的唯一设置。官方仓库后续代码中还可见其他采样选项，但不能据此倒推它们都属于原论文的实验配置。参见 [原论文第 3.6 节与附录](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)及[官方采样代码](https://github.com/openai/gpt-2/blob/master/src/sample.py)。

#### 7.4 候选评分：答案选项已经给出

对于填空任务，设空缺前的文本为 $l$，后面的文本为 $r$，某个候选为 $c_k$。一个基本的完整条件评分可以写为：

$$
s_k
=\operatorname{log}p_{\theta^*}(c_k,r\mid l)
=\operatorname{log}p_{\theta^*}(c_k\mid l)
+\operatorname{log}p_{\theta^*}(r\mid l,c_k).
$$

再选择：

$$
\hat k=\operatorname*{arg\,max}_k s_k.
$$

这意味着：**不仅看候选词本身是否常见，也看填入它之后，后面的文本是否更符合语言模型。**

上式用于说明评分思想，不是所有 benchmark 的统一复现公式。候选可能由不同数量的 BPE token 组成；是否只评分后缀、是否归一化长度、如何还原原始文本，都会改变结果。

#### 7.5 能使用右侧文本，不等于每个 token 都有双向 attention

评分时，右侧文本 $r$ 已经作为待评估的观测文本给出。模型根据左侧与候选预测右侧文本的概率，从而间接比较候选。

这与“候选所在位置的隐状态直接看到了右侧文本”不同：

- 因果模型仍然只读取当前位置与左侧。
- 候选的影响会传播到后续位置。
- 后续位置对真实后缀的预测概率，被用来评价候选是否合适。

因此，单向 LM 可以通过**整段文本的似然**利用后续约束，而不需要把 causal mask 改成双向。

> [!example] 用右侧文本选候选，究竟是怎么做到的？
> 假设要补全 `She put the ___ on her head.`，候选是 `hat` 和 `apple`。
>
> 模型在候选位置预测时仍看不到 `on her head.`；但把候选填进去后，可以继续计算这段后缀的条件概率。若候选自身的概率相近，而填入 `hat` 后模型认为后缀更可能出现，那么完整评分就会更偏向 `hat`。
>
> **不是让空缺位置“向右看”，而是检查“选了这个候选，后面的已知文本是否更容易被预测”。** 右侧文本参与的是候选的总体评价，不是候选位置的双向编码。这个例子展开的是第 7.4 节的概率分解，对应[原论文第 3.2 节的评分思路](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

#### 7.6 与 GPT-1 多选题 head 的差别

GPT-1 的监督多选题路径是：候选输入 → 末端表示 → 学习到的共享打分 head → 监督损失。

GPT-2 的这类零样本评分路径是：候选填入文本 → 原有 LM 给出 token 概率 → 按评测规则组成分数 → 选择候选。

二者都可以最终选择某个候选，但**分数的来源不同**。不能把 GPT-2 的似然分数写成已经通过任务标签训练好的判别 head 输出。原论文在 CBT 中评价候选及后续句子的概率，在 Winograd 中比较 full scoring 与 partial scoring；具体复现要遵循相应任务定义。参见 [原论文第 3.2 与第 3.4 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 8. 任务输入变换：具体怎样告诉 GPT-2 “现在做什么”？

#### 8.1 阅读理解：文档、历史问答与待续写的回答位置

CoQA 路径的主要信息包括：

- 当前文档。
- 围绕文档已经发生的问答历史。
- 当前问题，以及等待补全的回答提示 `A:`。

模型从这个前缀继续生成答案。历史问答帮助解释“为什么？”等依赖对话上下文的问题，但当前问题的真实答案不应作为输入的一部分。

论文使用 greedy decoding。输出是生成文本，不是模型必须从文档中选择一个连续区间的 span pointer；这也使它可能生成文档中不存在或与文档不符的细节。

#### 8.2 摘要：文章后加入 `TL;DR:`

可以把结构理解成：

`文章正文 → TL;DR: → 待生成摘要`

原论文在 CNN / Daily Mail 上的设置是：

- 加上 `TL;DR:` 提示。
- 使用 top-k 随机采样，$k=2$。
- 生成 $100$ 个 token。
- 取生成内容中的前 $3$ 个句子作为摘要。

所以，论文的摘要结果不仅取决于模型，还取决于**提示、解码与结果截取方式**。不能把它理解成“直接取语言模型后面的任意一段续写”。

这个提示能使输出更像摘要，不保证摘要覆盖要点，也不保证数字、人物和事件关系正确。参见 [原论文第 3.6 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

#### 8.3 翻译：先给对应句对，再留下待完成的等号

原论文使用类似以下形式的示例对：

`源语言句子 = 目标语言句子`

最后提供：

`待翻译句子 =`

然后贪心生成，并取第一个生成句子作为译文。这里的等号和句对顺序帮助模型推断后续应是什么语言、采用什么格式。

这是**上下文包含示例的任务调用**，不是对这些例子进行反向传播。它也不等于预训练时专门优化了一个独立的翻译 loss。

#### 8.4 知识问答：示例帮助限定短答案格式

Natural Questions 评测也用问题—答案示例作为前缀，帮助模型理解短答案的风格，再对新问题生成答案。

这条路径主要检查模型在参数中存储的信息和当前上下文组织出的回答能力，不是连接搜索引擎后的检索增强问答。**不要把它与 CoQA 中已经提供相关文档的阅读理解混为一谈。**

一个回答听起来具体、自然，仍可能是错误的人名、地点或年份；应以 exact match 等规定指标判断，而不是只靠流畅度判断。

#### 8.5 填空与指代：不必调用开放式生成

- **CBT**：在给定候选中，比较候选及其后续文本的概率。
- **Winograd Schema Challenge**：通过替换歧义指代的候选并评分，选择更符合语言模型的解释。
- **LAMBADA**：预测依赖长上下文的最后一个词；论文报告的最好 accuracy 还包含 stop-word filter，不是完全不加限制的原始续写准确率。

这些任务说明，“统一成语言建模”不意味着评测脚本完全相同。输入准备、候选构造、评分范围和输出约束都属于结果的一部分。参见 [原论文第 3.2–3.8 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 9. 梯度与参数更新：训练学权重，推理改状态

#### 9.1 训练时：LM loss 更新整个模型

记全部可训练参数为 $\theta$，用梯度下降形式说明更新关系：

$$
\theta\leftarrow\theta-\eta\nabla_\theta\mathcal L_{\mathrm{LM}}.
$$

这里是梯度更新的概念式，不是在声称原论文使用最朴素的 SGD。token embeddings、位置 embeddings、attention、FFN 和 LayerNorm 参数都属于语言模型的可训练部分。

输入输出权重共享意味着同一个 $E$ 同时参与查表和词表投影，它可以从相应计算路径接收梯度；不是固定的外部词典。

#### 9.2 零样本评测时：参数不变，但可以计算概率与评价指标

| 参数或状态 | 语言模型训练 | 论文的零样本任务使用 |
| --- | --- | --- |
| Token embeddings | 更新 | 不更新 |
| 可学习位置 embeddings | 更新 | 不更新 |
| Transformer 与 LayerNorm | 更新 | 不更新 |
| 与 embedding 共享的 LM 投影 | 参与训练 | 使用已有权重 |
| 新增任务 head | 该路线不需要 | 该路线不需要 |
| 输入 token、隐状态 | 随样本变化 | 随任务上下文变化 |
| KV cache | 不是需要学习的模型参数 | 可随已处理前缀逐步扩展 |

这里的“不更新”指不进行目标任务优化。评测语言模型时仍然可以计算负对数似然、PPL 或候选分数；**“不反向传播”不等于“不能计算一个长得像 loss 的评价量”**；PPL 与 BPB 的口径见第 11 节。

同样，模型对不同 prompt 产生不同答案，只说明输入条件改变了计算结果，不能据此断言参数已经发生了在线学习。

#### 9.3 KV cache：重复使用计算结果，不是给模型增加长期记忆

官方代码使用 `past` 和 `present` 传递 attention 的 key、value。用本文统一的 shape 记法，一个完整缓存可表示为：

$$
\mathcal K\mathcal V
\in\mathbb R^{B\times L\times2\times n_h\times T_p\times d_h}.
$$

其中 $B$ 是 batch size，$n_h$ 是 head 数量，$T_p$ 是已经缓存的前缀长度；大小为 $2$ 的那一维区分 key 与 value。

生成下一 token 时，新 query 可以与历史 key、value 进行 attention。缓存减少了对旧位置投影与表示的重复计算，但不消除新 token 对历史前缀的依赖。

尤其注意：

- 缓存的是本次输入对应的中间结果，不是对权重进行写入。
- 换一段无关上下文，不能把旧缓存不加处理地当成通用知识。
- 缓存不把 GPT-2 的原始位置表和上下文上限自动扩展到任意长度。

这些细节来自公开推理实现，是计算机制的补充说明，不是原论文新增的“记忆模块”贡献。参见 [官方 `past_shape`、`positions_for` 与 `attn`](https://github.com/openai/gpt-2/blob/master/src/model.py)及[采样循环](https://github.com/openai/gpt-2/blob/master/src/sample.py)。

> [!question] 为什么 KV cache 通常只存 K、V，不存历史 Q？
> 新位置要计算的是**新 query 对历史 keys 的匹配，再用这些权重汇总历史 values**。历史 queries 用于计算旧位置的 attention 输出；旧位置已经算完，生成新位置时不需要再使用那些 queries。
>
> 在参数、已有前缀和位置编号不变的确定性因果推理中，追加未来 token 不会改变旧位置的表示，所以每层的旧 K、V 可以复用。**缓存节省的是旧位置的重复计算，不是让新 token 不再计算 attention，也不是让生成变成完全并行。** 这可从[官方 `attn` 中新 Q 与拼接后的 K、V 的计算](https://github.com/openai/gpt-2/blob/master/src/model.py)直接看出。

### 10. 数据准备：WebText 与 byte-level BPE

#### 10.1 WebText 不是“直接拿 Reddit 评论训练”

数据获取的起点是 Reddit 上获得至少 $3$ karma 的**外部链接**，再抓取链接指向的网页正文。这个筛选信号用于近似判断网页是否值得阅读，不是对文本真伪或所有质量维度的保证。

论文提到约 $45$ million 个候选链接；经过正文提取、去重与启发式清洗，使用的初步 WebText 版本包含超过 $8$ million 篇文档，约 $40$ GB 文本。**候选链接数不等于最终训练文档数。**

数据不包含 $2017$ 年 $12$ 月之后创建的链接，并移除了 Wikipedia 文档以减轻与常见评测数据源重叠的问题。官方模型卡也明确区分：WebText 来源于 Reddit 的出站链接，不是直接由 Reddit 本站文本构成。参见 [原论文第 2.1 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)与[官方模型卡](https://github.com/openai/gpt-2/blob/master/model_card.md)。

#### 10.2 为什么数据多样性与任务迁移有关？

如果语料只有同一种文体，模型主要学习那种文体中的续写规律；更丰富的网页文本则可能同时出现解释、问答、列表、译文、引用和总结。

作者希望这些自然出现的结构，能在同一个语言模型目标下提供多种任务行为的示范。

这里有一个重要边界：**这是数据分布如何可能支持任务学习的解释，不是“网页越多就必然更好”的定理。** 噪声、重复、偏差和错误信息同样会被带入训练。

#### 10.3 Byte-level BPE：以字节覆盖文本，再把常见片段合并

GPT-1 的 tokenizer 包含文本清洗、spaCy 分词、小写化与子词 BPE。GPT-2 改用基于字节的可逆表示，其核心流程是：

1. 用正则表达式对文本做预切分，区分字母、数字、标点与空白等模式。
2. 将每段文本编码为 UTF-8 字节。
3. 将 $256$ 种字节值映射为可操作的 Unicode 符号。
4. 按已学习的 BPE merge 排序合并常见片段。
5. 将最终片段映射为 token IDs。

因此，**byte-level BPE 不等于“每个 token 永远只有一个字节”**。常见字符串可以合并成较大的 token；不常见字符串可以拆回较小的字节片段表示。

基础字节集合提供了对普通 Unicode 输入文本的覆盖，不需要像有限单词词表那样遇到未收录词就统一替换为 `<UNK>`。但“能编码某种语言的字符”与“模型在这种语言上表现很好”是两回事。

> [!tip] 字节已经能覆盖文本，为什么还需要 BPE？
> **基础字节解决“能不能表示”，BPE 合并解决“需要多少个 token 才能表示”。** 如果始终一个字节对应一个 token，文本序列往往较长；把常见字节片段合并，可以用较少的位置表示它们，让有限上下文容纳更多原文。
>
> 但“字节”“字符”“token”不能互换：例如汉字 `中` 的 UTF-8 编码占 $3$ 个字节，最终占多少个 token 还取决于已学到的合并规则。因此，$1{,}024$ 个 token 不等于 $1{,}024$ 个字，也不代表不同语言能放入同样多的内容。参见[原论文第 2.2 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)与[官方 tokenizer](https://github.com/openai/gpt-2/blob/master/src/encoder.py)。

#### 10.4 空格、大小写和标点不是无关装饰

官方 tokenizer 不像 GPT-1 路径那样统一将文本转成小写；它的预切分规则允许某些前导空格与后面的内容一起参与编码。

这意味着：

- 同一个词在句首与在空格之后，tokenization 可能不同。
- 大小写与标点变化可以改变 token 序列。
- 候选评分时应对完整构造的字符串正确分词，不能随意把独立编码的片段相加，就假设等于整体编码结果。

byte 到 Unicode 的映射是实现中便于 BPE 操作的中间表示，不应把显示出来的内部符号误读成原文真的包含奇怪字符。参见 [官方 `bytes_to_unicode`、`Encoder.encode` 与正则模式](https://github.com/openai/gpt-2/blob/master/src/encoder.py)。

#### 10.5 长网页仍然受到计算窗口限制

模型最多使用 $1{,}024$ 个位置的原始上下文。任务说明、示例、文档、问题与生成中的答案都要放进这个预算。

因此，“训练语料来自长网页”不等于“模型一次读完整篇网页”，也不等于“对话历史可以无限增长”。推理时需要控制输入与输出长度；不能仅凭 KV cache 就忽略位置范围。

### 11. 评测口径：指标为什么不能跨任务直接比较

> 读出方式确定之后，最后要分开的是指标本身：语言模型的概率指标、按单位归一化的指标和任务准确率不能互相替代。

#### 11.1 PPL、BPB 与任务准确率不是同一个指标

若采用 token 作为归一化单位，perplexity 可以写为：

$$
\operatorname{PPL}
=\operatorname{exp}\left(
-\frac{1}{N_{\mathrm{tok}}}
\sum_t\operatorname{log}p_\theta(x_t\mid x_{<t})
\right).
$$

但比较不同 tokenizer 时，直接比较“每个模型自己的平均 token loss”会改变分母的含义。原论文跨数据集评测时，按 benchmark 规定的单位，如 word、byte 或 character，对整段文本的对数概率归一化。

以 bits per byte 为例：

$$
\operatorname{BPB}
=-\frac{\operatorname{log}p_\theta(\text{文本})}
{N_{\mathrm{byte}}\operatorname{log}2}.
$$

此外，PPL 衡量观测文本的概率，不是“有多少道问题回答正确”。准确率、F1、BLEU、ROUGE 各自衡量不同任务与输出性质，不能跨列直接比较数值大小。

> [!example] $\operatorname{PPL}=10$ 应该怎样直观理解？
> 假设在每个预测位置，模型都给真实下一个 token 分配 $0.1$ 的概率，那么平均负对数似然为 $\operatorname{log}10$，PPL 就是 $10$。它相当于“每一步在 $10$ 个等概率选项中猜中真实项”所产生的对数损失，**不是说模型真的每次只考虑 $10$ 个词**。
>
> 更一般地，PPL 是各位置真实 token 概率的**几何平均数的倒数**；单个位置的概率可以差别很大。它也不意味着准确率为 $10\%$：模型给真实项 $0.1$ 的概率时，该项是否排名第一，还取决于其他候选的概率。这个解释由上面的 PPL 定义直接得到，比较时仍必须统一文本与归一化单位。

#### 11.2 无微调不代表没有预处理与评测设计

原论文针对一些 LM benchmark 使用可逆的 de-tokenizer，尽量去掉数据集预处理产生的空格和标点伪影，再按标准单位评价概率。

因此，结果需要连同文本恢复、上下文设置、输出过滤和解码方式一起阅读。**只下载同名模型并随意写一个 prompt，不足以保证复现论文数值。** 参见 [原论文第 3.1 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 12. 最后串起来：从一段雨天文本到一个任务答案

#### 12.1 一个完整的心智模型

继续用这段文本：

> Mia walked home in the rain without an umbrella. She got wet.

训练路径可以理解成：

1. 把文本进行 byte-level BPE 编码。
2. 相加 token embeddings 与可学习位置 embeddings。
3. 通过多层带 causal mask 的 Pre-LN Transformer。
4. 做最终 LayerNorm，再投影到词表。
5. 用真实后续 token 计算交叉熵，更新整个模型。

使用路径则可以构造文档和问题：

`Document: Mia walked home in the rain without an umbrella. Q: Did Mia stay dry? A:`

然后：

1. 保持训练后的模型权重不变。
2. 把整个任务上下文送入同一个模型。
3. 从原有 LM head 的词表分布中逐步生成答案。
4. 将输出与任务规定的答案和指标比较。

这个例子的合理答案应表达“没有保持干燥”；它只用来说明数据流与任务构造。

#### 12.2 与 GPT-1 的主要路线对照

| 维度 | GPT-1 的主要路线 | GPT-2 原论文的研究重点 |
| --- | --- | --- |
| 基础训练目标 | 自回归语言建模 | 自回归语言建模 |
| 训练语料 | BooksCorpus | WebText |
| 下游适配方式 | 监督微调整个骨干与新增任务 head | 权重不变，构造任务上下文并读取 LM 输出 |
| 任务差异放在哪里？ | 输入序列化与轻量任务输出层 | 文本上下文、候选评分和解码规则 |
| Block 的归一化 | Post-LN | Pre-LN，并有最终 LayerNorm |
| 上下文上限 | $512$ 个 token | $1{,}024$ 个 token |
| Tokenizer 的重要特点 | 小写化、spaCy 与 BPE | Byte-level BPE，保留更完整的文本形式 |
| 零样本研究 | 已有一组启发式分析，不是完全没有 | 成为主要研究对象 |
| 是否能微调？ | 可以，且是主要下游路线 | 可以，但不能把后续微调结果算作原论文零样本结果 |

最值得记住的两行是：

$$
\boxed{\text{GPT-1：预训练提供初始化，再用任务标签更新模型}}
$$

$$
\boxed{\text{GPT-2：预训练后不改权重，用任务上下文调用同一个语言模型}}
$$

这个对照描述的是两篇论文的重点，而不是给模型能力画互斥的边界：GPT-1 也研究了 zero-shot，GPT-2 也并非不能监督微调。

## Experiments

### 1. 训练与规模设置：哪些信息已公开，哪些没有？

原论文比较了 $4$ 档规模，使用 $512$ 的 batch size，并在 WebText 的 $5\%$ 留出样本上，以 perplexity 为依据手工调节各模型的学习率。

论文指出，当时所有模型在 WebText 上仍表现为欠拟合，继续训练仍能改善留出集 perplexity。

**不要把 GPT-1 笔记中的学习率、epochs、GPU 数量和训练时长直接复制过来。** GPT-2 技术报告与公开推理仓库没有给出可据此完整复现原始预训练的全部配置，这里不补写未经确认的训练预算与固定超参数。

发布模型可用于分析与实验，但“推理代码可运行”与“原始 WebText 预训练完全可复现”不是同一件事。参见 [原论文第 2.3–3 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)、[最初发布说明](https://openai.com/index/better-language-models/)与[官方仓库](https://github.com/openai/gpt-2)。

### 2. 跨域语言建模：主要优势明确，但不是所有数据集领先

![[_assets/images/gpt-2-03-language-model-benchmarks.png|900]]

Table 3 同时包含 PPL、accuracy、BPB 和 BPC，不能把所有列都当成准确率。

- 最大模型在 WikiText-2 上的 PPL 为 $18.34$，在 WikiText-103 上为 $17.48$，在 PTB 上为 $35.76$。
- enwik8 的 BPB 为 $0.93$，text8 的 BPC 为 $0.98$；这些是不同规范化单位的指标。
- **1BW 是重要反例**：GPT-2 的 PPL 为 $42.16$，表中此前最好结果为 $21.8$，而 PPL 越低越好。

论文所说的“在 $8$ 个语言建模数据集中，$7$ 个达到当时最优”指这里的评测范围，**不是说它在所有自然语言任务上都超过专门训练的系统**。

作者认为 1BW 的规模及句子级打乱等预处理可能解释迁移较差，但这是对结果的分析，不是一个独立实验已经把这些因素逐项隔离。

#### 2.1 LAMBADA：最好 accuracy 包含额外过滤

论文报告的 LAMBADA PPL 为 $8.63$。必须区分两种准确率口径：

- 原始语言模型预测的 accuracy 为 $52.66\%$。
- 加入 stop-word filter 后达到表中的 $63.24\%$。

过滤近似利用了“这里需要的是句子最后一个词”的约束。因此，不能把 $63.24\%$ 直接写成完全不加后处理的自由续写准确率。

#### 2.2 CBT：报告的是经过重叠检查的验证集

Table 3 中，最大模型的 CBT-CN 为 $93.30\%$，CBT-NE 为 $89.05\%$。论文发现测试集中的一本书与 WebText 重叠，因此使用没有显著重叠的验证集报告这部分结果。

这不是“模型在所有原始测试数据上无污染地得到同一个数字”。数据划分、候选评分和 de-tokenization 都属于结果口径。参见 [原论文第 3.1–3.3 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 3. 阅读理解、常识与知识问答：不要混淆有文档和无文档

#### 3.1 CoQA：与若干监督基线有竞争力，不等于达到人类水平

在提供文档、对话历史并贪心生成的设置下，GPT-2 在 CoQA 开发集达到约 $55$ F1。论文指出，这匹配或超过了所列 $4$ 个基线中的 $3$ 个，而没有利用该任务超过 $127{,}000$ 个人工问答训练样本来更新参数。

但当时更强的监督系统已接近人类约 $89$ F1 的水平。作者也观察到模型可能采用“问题问谁，就从文档里取一个名字”等简单启发式。

所以，这个结果支持无任务微调的阅读理解迁移值得研究，不能直接推出模型已经具有与人类相当的完整阅读推理能力。

#### 3.2 Winograd：需要结合样本量和评分方式阅读

论文报告 Winograd Schema Challenge 的最好 accuracy 为 $70.70\%$。该数据集只有 $273$ 个例子，且论文图中区分 full scoring 与 partial scoring。

因此，不应只保留一个百分数而省去评分方法，也不宜把小样本 benchmark 的提升扩展为“常识推理已经解决”。

#### 3.3 Natural Questions：少量高置信答案不能代表整体能力

GPT-2 在该知识问答设置下的整体 exact match 为 $4.1\%$。模型最有把握的 $1\%$ 问题上，准确率为 $63.1\%$。

这两个数的分母完全不同：

- $4.1\%$ 是整体问题集合上的结果。
- $63.1\%$ 只针对按模型置信程度筛出的很小子集。

不能把后者写成 GPT-2 的总体知识问答准确率，也不能从论文在该设置下的校准观察推导出“生成概率就是一般意义上的事实置信度”。参见 [原论文第 3.4–3.5 与第 3.8 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 4. 摘要：任务提示有效，但结果仍然很弱

![[_assets/images/gpt-2-04-summarization-results.png|900]]

有 `TL;DR:` 提示时，GPT-2 的 R-1、R-2、R-L 分别为 $29.34$、$8.27$、$26.58$，R-AVG 为 $21.40$；去掉提示后，R-AVG 为 $15.03$。

这支持“文本提示能够改变任务行为”，但不能只看有无提示的差异而忽略绝对水平：

- GPT-2 的 R-AVG 仅略高于 Random-3 的 $20.98$。
- Random-3 的 R-2 为 $8.63$，高于 GPT-2 的 $8.27$；不是每个分项都胜过随机抽句。
- Lede-3 与更强的摘要系统仍明显领先。

作者观察到摘要可能过度关注文章后部，或混淆数量和细节。**“输出像摘要”与“准确、完整地概括原文”必须分开评价。** 参见 [原论文第 3.6 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 5. 翻译：方向不对称，也没有接近强专用系统

在包含上下文示例的 WMT-14 设置中：

- 英译法为约 $5$ BLEU。
- 法译英为 $11.5$ BLEU。
- 原论文所比较的更强无监督翻译方法，法译英达到 $33.5$ BLEU。

作者将较强的法译英表现与 GPT-2 的英语语言建模能力联系起来，并报告 WebText 中经检测的法语数据只有约 $10$ MB。

这里支持的是：即使没有针对翻译任务更新参数，模型也开始表现出某种跨语言映射能力。它不支持“GPT-2 已是高质量通用翻译器”，也不能把任务前缀中的翻译示例省略后仍声称沿用原设置。参见 [原论文第 3.7 节](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 6. 规模分析：更大的模型更会做任务，但不是严格的单因素归因

![[_assets/images/gpt-2-02-zero-shot-scaling.png|900]]

Figure 1 分别展示阅读理解、翻译、摘要与问答随模型规模变化的表现。纵轴使用各自任务的指标，因此不要把四张子图的高度直接相互比较。

总体趋势支持模型容量与这些任务的迁移表现有关；但摘要曲线并不是每个规模点都严格增加。这里只有有限规模点、不同任务也有噪声，不能仅凭这张图推导一个精确的通用 scaling law。

![[_assets/images/gpt-2-06-webtext-scaling.png|900]]

Figure 4 中，WebText 训练集与留出集的 perplexity 随规模增加一起改善。结合继续训练仍有收益的观察，作者认为最大模型仍有欠拟合现象。

需要保留两个边界：

1. 训练和留出表现接近，不等于模型从不记忆训练文本。
2. 与 GPT-1 比较时，语料、词表、上下文和结构细节也发生变化，不能把全部差异只归因于参数数量。

这些曲线是规模与迁移关系的证据，不是对数据质量、容量、计算预算和优化方式贡献的完整拆分。参见 [原论文第 3–4 节与 Figure 1、Figure 4](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

### 7. 泛化与记忆：无任务微调，不代表训练语料与测试内容完全隔离

![[_assets/images/gpt-2-05-train-test-overlap.png|900]]

Table 6 比较的是测试文本的 $8$-gram 与不同训练语料的重叠比例。它不是重复文档比例，也不是“模型记住了多少知识”的直接测量。

作者的核查包括：

- 对多个 LM benchmark 检查规范化后的 $8$-gram 重叠。
- 对 CBT 改用没有显著重叠的验证集。
- 检查 CoQA 文档重叠对指标的影响。
- 在 LAMBADA 上排除有重叠的样本后重新评估。

论文发现 CoQA 新闻域有约 $15\%$ 的文档已经出现在 WebText 中；综合不同领域，重叠带来的增益约为 $0.5$--$1.0$ F1。这里主要是**文档重叠**，不能直接改写成完整问答对泄漏。

附录也观察到：对反复出现的知名文本，模型能够表现出逐字记忆。生成样本整体的较低重叠率，并不否定这种特定条件下的记忆行为。

因此，较稳妥的结论是：**这些分析支持结果不只是简单重复训练集，但也说明重叠与记忆是真实存在的，不能用 zero-shot 标签替代数据污染检查。** $n$-gram 方法能发现一部分问题，不保证找出所有近义改写、近重复或事实层面的重合。参见 [原论文第 4 节与附录 A](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)。

## Limitations & Caveats

### 论文与官方资料报告或讨论的限制

- **任务收益不均匀**：语言建模的强结果，不等于摘要、翻译、阅读理解和知识问答都同样强。
- **零样本能力仍不成熟**：论文明确将这类结果定位为研究上的潜力，而不是普遍可直接使用的系统能力。
- **生成内容可能不准确、不连贯或重复**：合理的语言续写不是事实核验，模型也可能切换主题或混淆关系。
- **训练文本包含偏差和错误**：官方模型卡强调，模型可能继承数据中的社会偏差，不能依靠自然流畅的输出判断其可靠性。
- **存在记忆与评测重叠**：不做目标任务微调，并不能排除在广泛预训练语料中见过相关内容。
- **原始预训练复现不完整**：发布权重与推理代码，并不等于同时发布完整 WebText、原始训练器及所有实验评测脚本。

参见 [原论文第 4、6 节与附录](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)、[官方发布说明](https://openai.com/index/better-language-models/)和[模型卡](https://github.com/openai/gpt-2/blob/master/model_card.md)。

### 根据方法与实验范围应保留的理解边界

- **不是现代指令对齐助手**：原始路线没有把指令微调、偏好优化或 RLHF 作为这里的训练阶段。
- **不是双向编码器**：Pre-LN 改的是归一化位置，不是 attention 的信息方向。
- **不是无限上下文模型**：原始可学习位置表与窗口只有 $1{,}024$ 个位置，KV cache 不会自动解除限制。
- **不是“完全没有示例”的统一评测**：翻译和知识问答的上下文里明确有示例。
- **没有证明自然语料能可靠教会所有任务**：文本中的任务示范是否充分、模型是否学到了可泛化规律，都需要具体检验。
- **概率、可信度与事实正确性不同**：一个错误答案也可能获得较高的语言模型概率。
- **精选样例不能代表平均质量**：原论文附录中不同表格的抽样方式不同；例如独角兽新闻例子注明是从 $10$ 个样本中挑选的，不能当成随机样本成功率。

### 发布历史不要写成永久状态

GPT-2 采用分阶段发布：最初没有立即开放最大模型，但官方后来在 $2019$ 年 $11$ 月 $5$ 日发布了最大的约 $1.5$ billion 参数版本。

因此，“最初没有发布最大模型”是历史事实；“GPT-2 最大模型始终没有公开”则不准确。模型发布策略与论文中的训练方法、实验结论也应分开讨论。参见 [最终模型发布说明](https://openai.com/index/gpt-2-1-5b-release/)。

## Open Questions / Follow-ups

下面是由本文方法与结果引出的验证方向，不是原论文已经证明的结论：

1. **自然文本中的哪些结构真正提供了任务监督？** 能否在控制语料规模的条件下，分别移除问答、译文或摘要类文本，检查相应任务迁移怎样变化？
2. **容量、数据多样性和训练计算各自贡献多少？** 如果固定其中两个因素，只改变另一个，是否仍能观察到类似的任务收益？
3. **模型是理解任务，还是匹配常见文本模式？** 改变提示措辞、示例顺序、无关上下文和答案格式，结果是否稳定？
4. **评分规则改变了多少结论？** 同一模型采用 full scoring、partial scoring、不同长度归约和 stop-word filter 时，候选排序会怎样变化？
5. **怎样更可靠地区分泛化与记忆？** 除 $n$-gram 重叠，还需要哪些近重复、时间切分或新构造数据检查？
6. **从可续写的基础模型到可靠任务系统，还缺什么？** 哪些短板能靠规模改善，哪些需要更好的数据、明确监督、检索或额外验证机制？

最后可以把 GPT-2 的核心记成：

> **训练：让一个大语言模型尽量预测好丰富自然文本。**
>
> **迁移：不改模型权重，用上下文表达任务，再从文本概率中读出结果。**

它的重要启发不是“语言建模已经解决了所有理解任务”，而是：**预训练模型本身就可能成为一个可通过文本上下文调用的任务执行器，而不只是等待微调的表示初始化。**

## Citation

- [GPT-2 原论文](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf)：Alec Radford、Jeffrey Wu、Rewon Child、David Luan、Dario Amodei、Ilya Sutskever，*Language Models are Unsupervised Multitask Learners*，OpenAI，$2019$。
- [官方首次发布说明](https://openai.com/index/better-language-models/)：发布背景、语言模型与零样本结果、失败模式和初始发布策略。
- [官方代码仓库](https://github.com/openai/gpt-2)：模型与代码入口，并明确更正原论文及早期博客的参数量统计。
- [官方网络实现](https://github.com/openai/gpt-2/blob/master/src/model.py)：Pre-LN、最终 LayerNorm、causal attention、可学习位置、FFN、权重共享与 KV cache。
- [Attention Is All You Need](https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf)：原始 Transformer，$2017$；核对 Post-LN 布局、decoder 子层与 warmup 的历史背景。
- [GPT-1 原论文](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)与[官方训练代码](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)：核对其 Transformer 设计沿用、Post-LN 计算顺序与 warmup 配置。
- [On Layer Normalization in the Transformer Architecture](https://proceedings.mlr.press/v119/xiong20b.html)：Xiong 等，ICML，$2020$；补充 Pre-LN / Post-LN 的初始化梯度与 warmup 分析，属于后续研究，不是 GPT-2 原报告的理论结论。
- [Root Mean Square Layer Normalization](https://papers.neurips.cc/paper_files/paper/2019/hash/1e8a19426224ca89e83cef47f1e7f53b-Abstract.html)与[LLaMA](https://arxiv.org/pdf/2302.13971)：区分归一化函数与 Pre-Norm 布局，并给出采用 Pre-RMSNorm 的后续模型实例。
- [DeepNet: Scaling Transformers to 1,000 Layers](https://arxiv.org/abs/2203.00555)：补充残差缩放与初始化的替代设计，以及不同归一化布局的实验比较；不属于 GPT-2 原始训练方法。
- [官方 tokenizer](https://github.com/openai/gpt-2/blob/master/src/encoder.py)：UTF-8 字节映射、预切分、BPE 与解码。
- [官方采样代码](https://github.com/openai/gpt-2/blob/master/src/sample.py)：基于 LM logits 的生成、温度、采样与缓存推进；仓库后续选项不应全部倒推为原论文配置。
- [官方模型卡](https://github.com/openai/gpt-2/blob/master/model_card.md)：模型家族规模、训练数据来源、用途和可靠性边界。
- [最大模型最终发布](https://openai.com/index/gpt-2-1-5b-release/)：分阶段发布结束时的历史记录。
- 本地原论文：[[06-LLM/03-Transformer/assets/paper_gpt2_2019.pdf]]。
- 结构参考与前置对照：[[06-LLM/03-Transformer/GPT-1：从生成式预训练到语言理解微调.md]]。

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
