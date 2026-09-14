---
title: "GPT-1：从生成式预训练到语言理解微调"
aliases: ["GPT1", "GPT-1", "Improving Language Understanding by Generative Pre-Training"]
authors: ["Alec Radford", "Karthik Narasimhan", "Tim Salimans", "Ilya Sutskever"]
conference: "OpenAI Technical Report"
year: 2018
paper_url: "https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf"
pdf_link: "[[06-LLM/03-Transformer/assets/paper_gpt1_2018.pdf]]"
cover: "[[_assets/images/gpt-1-01-pretraining-finetuning.drawio.svg]]"
created: 2026-09-13
updated: 2026-09-13
tags: ["paper/technical-report", "llm", "pretraining", "causal-lm", "transfer-learning"]
status: "unread"
priority:
rating:
topics: ["LLM", "Transformer", "预训练与微调"]
code: "https://github.com/openai/finetune-transformer-lm"
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

> **GPT-1 先让一个只有 Transformer decoder 的模型，在大量连续文本上学习“预测下一个 token”；再把不同语言理解任务整理成它能读取的文本序列，用少量新增输出参数和有监督数据微调整个模型，将生成式预训练获得的表示迁移到分类、推理与选择题。**

- **预训练标签来自文本自身**：给定前面的 token，预测后面的真实 token；不需要为每句话额外标注情感或推理关系。
- **主体是单向 Transformer，而不是完整 encoder–decoder**：使用 causal self-attention，没有额外的 encoder，也没有读取 encoder 输出的 cross-attention。
- **迁移的不只是词向量**：token embeddings、位置 embeddings 和多层 Transformer 一起提供预训练初始化，随后继续适应目标任务。
- **主要下游结果依赖有监督微调**：新增任务 head，并更新语言模型骨干；不是冻结 GPT 后，仅靠自然语言 prompt 就完成所有任务。
- **生成目标与判别目标可以共同训练**：微调时加入辅助语言模型损失，但消融表明它不是对每个任务都有效。

前置阅读：[[06-LLM/03-Transformer/06-transformer.md]]；涉及输入输出 embedding 复用的部分可结合 [[06-LLM/04-训练与推理/权重共享.md]]。后续阅读：[[06-LLM/03-Transformer/GPT-2：从语言建模到零样本任务迁移.md|GPT-2：从语言建模到零样本任务迁移]]。

本文沿着 **监督信号 → 网络表示 → 各个 loss → 任务输入与输出 → 梯度与参数更新 → 数据处理 → 下游使用 → 完整心智模型** 展开；[[06-LLM/03-Transformer/GPT-2：从语言建模到零样本任务迁移.md|GPT-2 笔记]] 沿用同一条组织线。

这里的 GPT-1 指通常如此称呼的初代 GPT，即 *Improving Language Understanding by Generative Pre-Training*，不是后来的对话助手。

## 框架总览

![[_assets/images/gpt-1-01-pretraining-finetuning.drawio.svg|900]]

**读图顺序**：左侧先用连续文本进行下一 token 预测，右侧再用任务标签微调整个骨干与新增 head；下方补充 Post-LN 结构、任务输入变换和推理路径。金色箭头表示 **embeddings 与 Transformer 的参数迁移**，不是前向数据流；虚线表示可选的辅助 LM 分支。

![[_assets/images/gpt-1-02-architecture-and-task-inputs.png|900]]

原论文 Figure 1：左侧是网络与两类输出，右侧是分类、蕴含、相似度与多选题的输入变换。读图时注意：

- **两个输出的用途不同**：Text Prediction 与 Task Classifier 不是同一条路径；无标签预训练阶段并没有可训练的情感标签。
- **Layer Norm 位于残差相加之后**，对应 GPT-1 的 Post-LN 结构。
- **Extract 是表示提取位置**，不是把正确答案附加到输入。
- **Similarity 的两条路径共享模型、末端表示相加**；Multiple Choice 的各条路径共享打分方式，最后比较候选分数。

## Key Contributions

### 从 Transformer 继续往前走：核心问题变了什么？

原始 Transformer 为序列建模提供了一种不依赖循环网络的架构。GPT-1 进一步关心：

> 如果先让 Transformer 大量阅读没有任务标签的文本，它学到的东西能否复用于不同的语言理解任务，而不必为每个任务重新设计并从头训练一套复杂网络？

困难在于：**“把下一词预测准确”与“把情感、蕴含关系或正确答案判断准确”，并不是同一个训练目标。**

预训练只有连续文本，而下游输入可能是一句话、一对有方向的句子，或“文章 + 问题 + 多个候选答案”。因此，既要回答“学什么”，也要回答“怎样迁移”。

| 核心问题 | GPT-1 的回答 |
| --- | --- |
| 大规模训练的监督从哪里来？ | 连续文本中的真实后续 token |
| 预训练什么网络？ | 使用因果掩码的 decoder-only Transformer |
| 迁移的是词向量还是整个网络？ | 预训练的 embeddings 与 Transformer 层 |
| 结构不同的任务怎样输入同一骨干？ | 用特殊标记与任务相关顺序，将输入序列化 |
| 怎样获得目标任务的输出？ | 提取序列末端表示，接轻量任务 head |
| 微调时更新谁？ | 更新骨干与新增任务参数，而非默认冻结骨干 |
| 是否完全放弃语言建模？ | 可以把它保留为辅助目标，与监督任务共同优化 |

论文的重要性在于：**将生成式预训练、Transformer 骨干和简单的任务输入变换结合起来，并在多类理解任务上验证迁移效果。** 它不是首次提出预训练或迁移学习；原文明确讨论了更早的语言模型预训练、ULMFiT 和表示迁移工作。参见 [原论文第 1–3 节](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)。

## Method

### 1. 监督信号：先从原始文本学习，再从任务标签学习

#### 1.1 用同一句影评区分两种监督

假设看到一句影评：

> The movie was surprisingly good.

在预训练时，它只是一段文本。模型需要根据 “The movie was surprisingly” 预测后续 token，不需要知道它属于正面评价。

在情感分类微调时，同一句话附带任务标签 `positive`，模型需要判断整句话的情感类别。

| 阶段与目标 | 模型被要求做什么？ | 标签来自哪里？ |
| --- | --- | --- |
| 生成式预训练 | 根据左侧上下文预测下一个 token | 原始文本自身 |
| 有监督微调的任务目标 | 判断情感、句间关系或正确选项 | 目标任务的数据标注 |
| 微调中的辅助 LM 目标 | 继续预测任务输入序列中的后续 token | 微调输入文本自身 |

所以，**“预训练不需要任务标签”不等于“整个 GPT-1 训练流程没有人工监督”。** 论文主要的下游成绩来自有标注数据上的适配。

原论文使用 unsupervised pre-training 一词；用现在常见的术语描述，其 next-token prediction 属于自监督学习，因为预测目标由输入文本自动构造。

#### 1.2 两个阶段，不是从头把所有数据和目标混在一起

记无任务标签的文本语料为 $\mathcal U$，某个下游任务的数据为：

$$
\mathcal C=\{(x_i,y_i)\}_{i=1}^{N}.
$$

训练顺序为：

$$
\theta_0
\xrightarrow{\text{在 }\mathcal U\text{ 上进行语言建模}}
\theta_{\mathrm{pre}}
\xrightarrow{\text{在 }\mathcal C\text{ 上进行监督微调}}
\theta_{\mathrm{task}}.
$$

- 第一阶段获得可迁移的语言模型初始化。
- 第二阶段从这个初始化出发，训练特定任务。
- 不同任务通常各自从同一份预训练模型开始微调，得到各自的任务模型。

**“task-agnostic model”主要描述通用骨干与预训练，不表示论文把全部任务共同训练成一个无需切换参数的统一助手。** 论文在 RTE 分析中还明确把多任务训练留作未探索的方向。

### 2. 网络架构：单向 Transformer 与词表输出

#### 2.1 输入不是 one-hot 向量直接参与 attention

设输入 token IDs 为：

$$
x=(x_1,\dots,x_T),
\qquad x_t\in\{1,\dots,V\}.
$$

其中 $V$ 为词表大小，$T$ 为有效输入长度。记 token embedding 矩阵与可学习位置 embedding 矩阵为：

$$
E\in\mathbb R^{V\times d},
\qquad
P\in\mathbb R^{T_{\max}\times d}.
$$

第 $t$ 个输入位置的初始表示为：

$$
h_t^{(0)}=E_{x_t,:}+P_{t,:},
\qquad
H^{(0)}\in\mathbb R^{T\times d}.
$$

原论文使用**可学习的绝对位置 embeddings**，不是原始 Transformer 中的正弦位置编码，也不是 RoPE。

输入 embeddings 相加后进入多层 Transformer：

$$
H^{(\ell)}
=\operatorname{Block}_{\ell}\!\left(H^{(\ell-1)}\right),
\qquad \ell=1,\dots,L.
$$

每一层都保留序列位置；不是进入模型后立刻把整句话平均成一个向量。

#### 2.2 Decoder-only：有 causal self-attention，没有 encoder cross-attention

GPT-1 的基本配置为：

| 配置项 | 原始设置 |
| --- | --- |
| Transformer block 数量 | $L=12$ |
| 隐藏维度 | $d=768$ |
| Attention heads | $12$ 个 |
| 单个 head 的维度 | $d_h=64$，由 $768/12$ 得到 |
| FFN 中间维度 | $3{,}072$ |
| 上下文长度上限 | $512$ 个 token |
| 激活函数 | GELU |
| 位置表示 | 可学习的绝对位置 embeddings |

“decoder-only”表示保留适合自回归建模的单向结构，**并不表示这里还藏着一个 encoder 为 decoder 提供输入**。整条路径只处理当前文本序列，不需要额外源序列。

按官方公开的参数 shape 文件求和，基础预训练权重共有 $116{,}534{,}784$ 个参数，约为 $117$ million；这是对发布文件的统计，不包含微调时新增的特殊 token embeddings 与任务 head。参见 [官方参数形状](https://github.com/openai/finetune-transformer-lm/blob/master/model/params_shapes.json)。

#### 2.3 一个 block 内部：注意 GPT-1 使用 Post-LN

省略 dropout 后，官方实现中的残差与归一化顺序可写为：

$$
\widetilde H^{(\ell)}
=\operatorname{LN}_{\ell,1}
\left(
H^{(\ell-1)}
+\operatorname{MHA}_{\mathrm{causal},\ell}
\left(H^{(\ell-1)}\right)
\right),
$$

$$
H^{(\ell)}
=\operatorname{LN}_{\ell,2}
\left(
\widetilde H^{(\ell)}
+\operatorname{FFN}_{\ell}
\left(\widetilde H^{(\ell)}\right)
\right).
$$

其中：

$$
\operatorname{FFN}(H)
=\operatorname{GELU}(HW_1+b_1)W_2+b_2,
$$

$$
W_1\in\mathbb R^{768\times3{,}072},
\qquad
W_2\in\mathbb R^{3{,}072\times768}.
$$

这里的 LayerNorm 在“子层输出 + 残差”之后，即 **Post-LN**。GPT-1 沿用原始 Transformer 的这一布局，后来的模型才普遍改为 Pre-LN，改动的动机与梯度路径见 [[06-LLM/03-Transformer/GPT-2：从语言建模到零样本任务迁移.md#3. 归一化布局：从 Post-LN 到 Pre-LN|GPT-2 笔记第 3 节]]。

官方 `block` 的顺序就是 attention → 残差相加与归一化 → FFN → 残差相加与归一化。参见 [官方网络实现](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。

#### 2.4 语言模型输出：在词表上分类，并复用输入 embedding

按照论文公式，最终隐状态通过共享的 embedding 矩阵映射回词表：

$$
Z_{\mathrm{LM}}=H^{(L)}E^\top
\in\mathbb R^{T\times V}.
$$

第 $t$ 个位置给出的下一 token 分布为：

$$
p_\theta(x_{t+1}=v\mid x_{\le t})
=\operatorname{softmax}
\left(h_t^{(L)}E^\top\right)_v.
$$

这里有两个不同空间：

- $h_t^{(L)}$ 是隐藏表示，维度为 $d$。
- $h_t^{(L)}E^\top$ 是词表 logits，维度为 $V$。

**隐藏表示不是单词概率；经过词表投影与 softmax 后，才得到下一个 token 的概率分布。** 输入查表与输出投影复用同一组 token embeddings，也不意味着预训练时 embedding 被固定。

### 3. Causal mask：模型为什么不会在训练时偷看答案？

#### 3.1 Query、Key、Value 都来自当前文本隐状态

对某一层、某一个 attention head，省略偏置：

$$
Q=HW_Q,\qquad K=HW_K,\qquad V_H=HW_V.
$$

这里用 $V_H$ 表示 value 矩阵，避免与词表大小 $V$ 混淆。注意力为：

$$
\operatorname{Attention}(H)
=\operatorname{softmax}
\left(
\frac{QK^\top}{\sqrt{d_h}}+M
\right)V_H.
$$

因果掩码为：

$$
M_{t,j}=
\begin{cases}
0,&j\le t,\\
-\infty,&j>t.
\end{cases}
$$

若用“行读取列”表示可见性，长度为 $4$ 时：

$$
A=
\begin{bmatrix}
1&0&0&0\\
1&1&0&0\\
1&1&1&0\\
1&1&1&1
\end{bmatrix}.
$$

$A$ 只是允许关系示意；实际加到 attention logits 上的是 $M$，不是直接加这个布尔矩阵。

#### 3.2 允许看当前位置，为什么仍然没有泄漏？

关键在于输入与目标的错位：

$$
h_t^{(L)}\text{ 可以使用 }x_{\le t},
\quad
\text{但它负责预测 }x_{t+1}.
$$

例如，输入位置当前是 “surprisingly”，该位置可以读取 “surprisingly” 本身，但目标是接下来的 “good”。

如果没有 causal mask，前面的隐状态可能读取后面的真实输入 token，预测就退化为偷看答案；如果不做 label shift，则可能错误地让模型用当前 token 预测当前 token。

因此，**因果掩码与输入、目标的错位配合，才构成正确的 next-token prediction。**

#### 3.3 单向依赖，不等于训练必须逐 token 执行

训练时整段真实文本已知，可以通过矩阵运算一次计算多个位置，再用 causal mask 限制依赖关系。

- **训练**：真实前缀可用，各位置的预测可以并行计算。
- **自由生成**：后续 token 还不存在，需要先生成一个 token，再把它加入上下文继续预测。

计算能否并行与信息是否单向，是两个不同问题。下游微调时，GPT-1 也不会自动把 causal mask 换成双向 mask。

### 4. 生成式预训练：只预测下一个 token，究竟在优化什么？

#### 4.1 自回归概率分解

忽略窗口截断，一段文本的概率可分解为：

$$
p_\theta(x_1,\dots,x_T)
=p_\theta(x_1)
\prod_{t=1}^{T-1}
p_\theta(x_{t+1}\mid x_{\le t}).
$$

实际训练只使用上下文窗口内可见的前文，而不是无条件读取一本书从开头到当前位置的全部内容。

以一段长度为 $T$ 的训练序列为例，省略首 token 的预测约定，基础语言模型交叉熵为：

$$
\mathcal L_{\mathrm{LM}}(x)
=-\frac{1}{T-1}
\sum_{t=1}^{T-1}
\operatorname{log}
p_\theta(x_{t+1}\mid x_{\le t}).
$$

批训练时再对样本归约；padding 不应成为有效目标。具体窗口切分、有效位置与归约方式属于实现细节。

原论文的 $L_1$ 是**要最大化的对数似然**，这里的 $\mathcal L_{\mathrm{LM}}$ 是**要最小化的负对数似然**。阅读公式时不要漏掉两种写法之间的负号。

#### 4.2 Teacher forcing：真实后续文本就是监督

仍用影评作示意，暂时将单词近似看成 token：

| 可读取的真实输入前缀 | 当前预测目标 |
| --- | --- |
| The | movie |
| The movie | was |
| The movie was | surprisingly |
| The movie was surprisingly | good |
| The movie was surprisingly good | . |

> [!tip]- 这些行不是要求重复做多次完整前向
> 表中每一行对应同一段文本的一个位置，行与行共享同一次前向计算。实际 tokenizer 使用子词，真实切分也不一定与单词边界相同。

官方公开微调代码中的辅助 LM 使用 `h[:, :-1]` 对齐 `X[:, 1:, 0]`，并使用有效位置 mask 排除 padding，直接体现了这种错位监督。参见 [官方 LM loss](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。

#### 4.3 为什么生成目标可能帮助理解任务？

要区分 “The movie was surprisingly good” 和 “The movie was not good” 的后续分布，模型可能需要利用否定、评价对象、局部语法与更长的语境。

因此，语言建模不只是在最后一层学习词频；它通过误差反向传播，调整多层上下文表示，使其更适合预测真实文本。

但应保留边界：

> **下一词预测提供了学习任务相关结构的机会，不保证每个隐状态都对应明确概念，也不保证预测准确就等于拥有可靠推理能力。**

“预训练有用”由下游迁移实验支持；“这些能力具体如何存储、各占多少贡献”则不是仅靠目标函数就能证明的。

### 5. 有监督微调：怎样从语言模型得到情感类别或推理关系？

#### 5.1 在序列末端加入表示提取位置

对于单句分类，可以把输入理解成：

`[START] The movie was surprisingly good. [EXTRACT]`

这里 `[START]` 与 `[EXTRACT]` 是讲解用标记，对应论文图中的 Start 与 Extract。官方 Story Cloze 代码使用 `_start_`、`_delimiter_`、`_classify_`，这些特殊 token embeddings 在任务适配时随机初始化。

记末端提取位置为 $e$，取最后一层的表示：

$$
r(x)=h_e^{(L)}\in\mathbb R^d.
$$

> [!question] 为什么把提取位置放在末端？
> 在因果注意力下，末端位置能读取前面所有有效输入；若把一个普通的汇总 token 放在最前面并维持同样的 mask，它看不到后面的句子。

**提取的是末端特殊 token 的上下文表示，不是最后一个 padding 位置，也不是把每个 token 的 LM 概率相加。**

#### 5.2 任务 head 与 LM head 不是同一个分类空间

对有 $C$ 个离散类别的任务，新增：

$$
W_{\mathrm{cls}}\in\mathbb R^{d\times C},
\qquad
b_{\mathrm{cls}}\in\mathbb R^C.
$$

用行向量约定，类别概率为：

$$
p_{\theta,\phi}(y\mid x)
=\operatorname{softmax}
\left(r(x)W_{\mathrm{cls}}+b_{\mathrm{cls}}\right)_y,
$$

其中 $\phi$ 表示任务输出参数。分类损失为：

$$
\mathcal L_{\mathrm{task}}
=-\frac{1}{N}
\sum_{i=1}^{N}
\operatorname{log}
p_{\theta,\phi}(y_i\mid x_i).
$$

| 输出路径 | 读取什么？ | 在什么集合上分配概率？ |
| --- | --- | --- |
| LM head | 各输入位置的隐状态 | 词表中的下一 token |
| 分类 head | 序列提取位置的隐状态 | 情感或推理等任务类别 |
| 多选题打分 head | 各候选输入的提取表示 | 经候选间 softmax，得到选项概率 |

因此，情感分类输出 `positive` 可以只是**类别名称**，不是要求 LM 在词表中生成这个英文单词。

上式针对离散分类。STS-B 评估连续语义相似度，不能把它机械理解成相同的二分类标签设置。

#### 5.3 标签在哪里？不要把答案偷偷塞进输入

在普通有监督情感分类中：

- 输入是影评和必要的结构标记。
- `positive` 作为损失函数使用的真实标签。
- `[EXTRACT]` 只是表示提取位置，不携带该样本的正确类别。

模型必须从输入表示预测标签。**“在句尾加入特殊 token”不等于“把正确答案作为句尾 token 输入”。**

### 6. 联合微调目标：任务学习与语言建模怎样共存？

#### 6.1 第二阶段可以同时优化两种损失

将论文最大化目标改写为最小化损失：

$$
\mathcal L_{\mathrm{FT}}
=\mathcal L_{\mathrm{task}}(\mathcal C)
+\lambda\mathcal L_{\mathrm{LM}}(\mathcal C).
$$

论文默认使用 $\lambda=0.5$。

这里的辅助 LM 目标计算在**目标任务的输入文本**上，不是说每个微调 batch 都必须同时重新抽取 BooksCorpus 数据。

两个目标可以共享一次骨干计算：

- 序列中间各位置用于预测后续 token。
- 末端提取位置用于预测任务标签。

作者认为辅助 LM 有助于泛化与收敛，但它是否改善最终任务指标，需要实验判断。

#### 6.2 这个系数不是“语言模型占一半训练量”

> [!warning] 系数不等于训练量占比
> $\lambda=0.5$ 只表示对某个已归约的 loss 乘以这个系数。实际影响还与以下因素有关：
>
> - 两种损失的数值尺度。
> - LM 对 token、序列与候选的归约方式。
> - 各条路径对共享参数产生的梯度大小与方向。
>
> 官方 Story Cloze 实现先在每条候选序列内，对有效 LM 目标做平均，再对候选序列做平均；任务分类 loss 则按样本平均。因此，把任意求和的 LM loss 直接乘以同样系数，并不等于复现原实现。

#### 6.3 错误候选也可以参与辅助 LM，不等于它成了分类正例

在官方 Story Cloze 路径中，一道题的两个候选结局分别形成输入序列，**两条序列都计算辅助 LM loss**；任务 loss 再要求正确候选获得更高的分类分数。

这两种监督回答不同的问题：

- LM：这段输入文本在语言建模意义下怎样续写？
- 任务 head：两个候选中，标注认为哪一个适合当前故事？

它们不是同一种真假判断，也可能产生不同的优化倾向。这进一步说明，辅助 LM 不能被解释成“额外告诉模型哪个答案正确”。参见 [官方 `model` 与 `mgpu_train`](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。

### 7. 任务输入变换：用同一骨干处理不同结构

GPT-1 尽量把任务差异放在**输入排列与末端输出**，而不是为每个任务增加复杂的中间网络。

| 任务类型 | 示意输入 | 输出方式 |
| --- | --- | --- |
| 单句分类 | `[START] 文本 [EXTRACT]` | 末端表示 → 类别 |
| 文本蕴含 | `[START] 前提 [DELIM] 假设 [EXTRACT]` | 末端表示 → 关系 |
| 句子相似度 | 分别输入“句子甲 → 句子乙”和反向顺序 | 两个末端表示相加 → 任务输出 |
| 多选问答 / 故事补全 | 每个候选各构造一条“上下文 → 候选答案” | 每条一个分数 → 候选间 softmax |

这些标记用代码形式展示，避免与正文公式混淆；它们不是自然语言 instruction，也不意味着不同任务的全部输出层参数相同。

#### 7.1 文本蕴含：有方向的句子对不能随意交换

例如：

- 前提：`A dog is running on grass.`
- 假设：`An animal is outdoors.`

构造：

`[START] 前提 [DELIM] 假设 [EXTRACT]`

假设一侧的位置可以读取前提，末端提取位置可以读取整对句子；前提位置仍不能读取后面的假设。

因此，它通过**串联后的单向 self-attention** 建立句间联系，而不是增加一个独立的双向句间 cross-attention 模块。

蕴含有方向：前提支持假设，不代表假设反过来也支持原前提。输入顺序在这里包含任务语义。

#### 7.2 句子相似度：处理两个顺序，但不是把模型改成双向 attention

对句子 $a$ 与 $b$，独立编码：

$$
r_{ab}
=r\!\left(\operatorname{Serialize}(a,b)\right),
\qquad
r_{ba}
=r\!\left(\operatorname{Serialize}(b,a)\right).
$$

两个序列使用同一个 Transformer，再逐元素相加：

$$
r_{\mathrm{sim}}=r_{ab}+r_{ba}.
$$

最后将 $r_{\mathrm{sim}}$ 送入任务输出层。

> [!note] 三点不要混
> 1. 是分别处理两种顺序，不是把两个顺序无条件拼成一条更长输入。
> 2. 是合并隐藏表示，不是默认平均两次 softmax 概率。
> 3. 每次前向内部仍是 causal attention；交换顺序并不等价于让每个 token 同时看到左右上下文。

在确定性推理、输入处理一致时，交换 $a$ 与 $b$ 只会交换这两个加数，使最终合并表示保持一致。这是输入变换与聚合带来的性质。

#### 7.3 多选问答：每个候选一条序列，共享模型打分

给定文档 $z$、问题 $q$ 和候选答案 $a_1,\dots,a_K$，构造：

$$
s_k
=\operatorname{Serialize}
\left(
\texttt{[START]},z,q,\texttt{[DELIM]},a_k,\texttt{[EXTRACT]}
\right).
$$

每条序列经过同一个骨干，提取表示并用共享打分 head 得到标量：

$$
r_k=r(s_k)\in\mathbb R^d,
\qquad
g_k=r_kw_{\mathrm{mc}}+b_{\mathrm{mc}},
\qquad
w_{\mathrm{mc}}\in\mathbb R^d.
$$

然后在候选集合上归一化：

$$
p(y=k\mid z,q,a_{1:K})
=\frac{\operatorname{exp}(g_k)}
{\sum_{j=1}^{K}\operatorname{exp}(g_j)}.
$$

若正确答案索引为 $y$：

$$
\mathcal L_{\mathrm{MC}}
=-\operatorname{log}p(y\mid z,q,a_{1:K}).
$$

**这里的 softmax 覆盖 $K$ 个候选，不是覆盖整个词表；选项分数来自学习到的任务 head，也不是直接使用答案文本的 LM 似然。**

候选之间共享权重，但各自前向时不读取其他候选序列。它们最终通过候选间归一化与监督损失进行比较。

#### 7.4 用一个雨天故事走一遍

> [!example] 两个候选中比较分数
> 上下文是 `Tom walked in heavy rain without an umbrella.`，候选结局分别是 `He got wet.` 与 `He stayed completely dry.`。
>
> 假设这个示例的标注选择候选甲，则：
>
> 1. 为“上下文 + 候选甲”与“上下文 + 候选乙”各构造一条序列。
> 2. 分别读取末端提取表示。
> 3. 共享 head 输出 $g_{\text{甲}}$ 与 $g_{\text{乙}}$。
> 4. 用交叉熵要求候选甲的相对分数更高。
> 5. 梯度同时更新任务 head 和 Transformer。
>
> 它只说明训练机制；真实 Story Cloze 使用多句故事和候选结局。

### 8. 梯度与参数更新：GPT-1 微调不是冻结特征提取

#### 8.1 两条损失路径汇入同一骨干

记 $\theta$ 为预训练骨干参数，$\psi$ 为新增特殊 token embeddings，$\phi$ 为任务 head 参数。对骨干：

$$
\nabla_\theta\mathcal L_{\mathrm{FT}}
=\nabla_\theta\mathcal L_{\mathrm{task}}
+\lambda\nabla_\theta\mathcal L_{\mathrm{LM}}.
$$

对只用于任务预测的 head：

$$
\nabla_\phi\mathcal L_{\mathrm{FT}}
=\nabla_\phi\mathcal L_{\mathrm{task}}.
$$

特殊 token embeddings 在其参与的计算路径上也能接收梯度。

模型不是“先冻结 GPT 生成一个句向量，再单独训练分类器”。任务误差可以改变 embeddings、attention、FFN 和归一化参数，使表示适合当前任务。

#### 8.2 哪些参数更新？按阶段区分

| 参数或模块 | 生成式预训练 | 有监督微调 | 任务推理 |
| --- | --- | --- | --- |
| 原有 token embeddings | 更新 | 继续更新 | 不更新 |
| 可学习位置 embeddings | 更新 | 继续更新 | 不更新 |
| Transformer blocks | 更新 | 继续更新 | 不更新 |
| LM 词表投影 | 与 token embeddings 共享并训练 | 辅助 LM 启用时参与该损失；共享权重也受骨干路径影响 | 仅在需要 LM 输出时使用 |
| 新增结构标记 embeddings | 尚未加入对应任务标记 | 随机初始化后训练 | 不更新 |
| 任务分类 / 打分 head | 不需要 | 新增并训练 | 只执行前向 |

**“新增参数很少”与“可训练参数很少”不是同一句话。** GPT-1 微调新增的部件小，但原有骨干通常也参与训练。

这与参考笔记中的 BLIP-2 不同：BLIP-2 的基础预训练冻结两端模型、训练桥接模块；GPT-1 将预训练骨干本身继续更新到目标任务。

#### 8.3 Weight tying：共享的是参数，不是固定的词义

token embedding 矩阵既用于输入查表，也用于语言模型输出投影。若启用 LM loss，同一矩阵会从两种用途接收梯度。

因此不能把它想象成一份永远不动的外部词典。预训练与微调都可以调整这组参数，后续 Transformer 又会把输入表示变成依赖上下文的隐状态。

同样，`eval()` 主要切换 dropout 等运行行为，不等于冻结权重。训练或推理的梯度设置，应与是否需要参数更新分开理解。

### 9. 数据准备：连续书籍文本、清洗与 BPE

#### 9.1 BooksCorpus 的价值不只是“文本很多”

论文使用 BooksCorpus，包含超过 $7{,}000$ 本未出版书籍，题材包括冒险、奇幻与爱情等。

作者强调它包含**连续的长段文本**。相较于按句子打乱的语料，连续片段保留了人物、事件与跨句关系，能够为基于上下文的预测提供信号。

但“训练数据来自整本书”不等于“模型一次读完整本书”：

- 预训练使用连续文本片段。
- 每条训练序列长度为 $512$ 个 token。
- 超出窗口的信息不会自动保存在一个跨整本书持续更新的循环状态里。

所以，论文所说的长程依赖，应放在当时的模型与窗口设置下理解，而不是现代长上下文模型的无限延伸。

#### 9.2 从原始文本到 token IDs

论文与官方 tokenizer 对应的主要处理流程是：

1. 使用 `ftfy` 清理文本编码等问题。
2. 规范部分标点与空白。
3. 使用 spaCy 做初步分词。
4. 官方实现将 token 文本转为小写，再执行 BPE 子词切分。
5. 将子词映射为 token IDs。

论文描述的是 **$40{,}000$ 次 BPE merges**；官方基础 encoder 文件包含 $40{,}478$ 个词表条目。两者不相等，因为 merge 次数不等于最终词表大小。

也不要把 GPT-1 的这套清洗、spaCy 分词与 BPE 流程，直接写成后续模型常见的 byte-level BPE tokenizer。参见 [官方 tokenizer](https://github.com/openai/finetune-transformer-lm/blob/master/text_utils.py)与[基础词表](https://github.com/openai/finetune-transformer-lm/blob/master/model/encoder_bpe_40000.json)。

#### 9.3 任务序列化之后，还需要正确处理长度

拼接文档、问题、答案与特殊 token 后，总长度仍受到上下文窗口限制。

> [!example]- 官方 Story Cloze 的截断与提取位置
> 官方代码对上下文与候选分别截断，再构造有效位置 mask；提取位置通过 `_classify_` 的 token ID 查找，而不是无条件取张量最后一列。
>
> 这属于具体任务实现，截断比例不是论文中所有任务的统一预处理规则。参见 [官方 `transform_roc`](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)。

### 10. 从训练到使用：生成、任务预测与 zero-shot 要分开

#### 10.1 语言模型生成：在词表上逐步选择后续 token

给定文本前缀，使用 LM head 获得后续 token 的分布，再将选出的 token 加入上下文继续计算。

这条路径体现 GPT-1 的生成式建模能力，但它本身不是论文中情感分类、NLI 或多选问答的统一评测方式。

#### 10.2 微调后的任务预测：通常不需要生成标签文本

- **情感分类**：序列化输入 → 提取末端表示 → 分类 head → 类别。
- **文本蕴含**：前提与假设按顺序输入 → 关系 head → 蕴含、矛盾或中立等任务标签。
- **多选问答**：每个候选单独打分 → 选取得分最高的候选。

正常任务推理不需要计算训练 loss，也不需要先生成一段推理过程。LM head 可以不作为这条任务预测路径的输出模块。

#### 10.3 原论文也研究 zero-shot，但那是一组启发式分析

论文第 5 节直接利用预训练 LM 设计了不做监督微调的任务规则，例如：

- **CoLA**：用句子的平均 token 对数概率打分，再通过阈值作判断。
- **SST-2**：在影评后追加 `very`，比较后续 `positive` 与 `negative` 的预测概率。
- **RACE**：给定文档与问题，比较模型对候选答案赋予的平均 token 对数概率。
- **DPRD**：将代词替换为候选指代对象，比较替换之后剩余序列的平均 token 对数概率。

这些实验用来观察语言模型预训练是否逐渐获得任务相关能力，不等同于主要实验表中的监督微调结果。

尤其要区分：

$$
\boxed{
\text{监督多选题：学习到的任务 head 为候选打分}
}
$$

$$
\boxed{
\text{零样本启发式：直接使用语言模型概率构造候选分数}
}
$$

因此，“GPT-1 完全没有研究 zero-shot”和“GPT-1 主要靠零样本指令完成任务”都不准确。参见 [原论文第 5 节](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)。

### 11. 最后串起来：一个完整的心智模型

#### 11.1 跟着同一句影评走一遍

1. **获得原始文本**：影评或书籍片段本身就能构造 next-token 标签。
2. **编码输入**：清洗与分词后，token embeddings 加上可学习位置 embeddings。
3. **进行单向上下文建模**：多层 causal Transformer 只允许当前位置读取此前与当前输入。
4. **预测后续 token**：使用共享 embedding 投影回词表，计算语言模型交叉熵。
5. **更新整个语言模型**：词表预测误差塑造多层上下文表示。
6. **接入目标任务**：为带情感标签的影评加入结构标记，新增分类 head。
7. **读取末端表示**：末端位置汇集前方输入信息，输出类别分布。
8. **联合微调**：任务 loss 与可选辅助 LM loss 共同更新骨干；分类 head 学习情感决策。
9. **执行任务推理**：输入一条未见影评，直接输出类别，而不是必须续写 `positive`。

#### 11.2 与两种常见做法对照

| 维度 | 目标任务从头训练 | 冻结预训练特征后训练 head | GPT-1 的主要路线 |
| --- | --- | --- | --- |
| 是否先利用无任务标签文本？ | 不要求 | 是 | 是 |
| 预训练能力怎样使用？ | 没有对应初始化 | 固定表示作为输入特征 | 初始化 embeddings 与 Transformer |
| 任务训练时骨干是否更新？ | 从随机初始化训练 | 不更新 | 从预训练权重继续更新 |
| 任务差异主要放在哪里？ | 可为任务专门设计网络 | 特征后的任务网络 | 输入序列化与轻量输出层 |
| 是否可保留 LM 辅助目标？ | 不属于该描述的必要步骤 | 通常不用于更新冻结骨干 | 原论文明确采用并做消融 |

最值得记住的两行是：

$$
\boxed{
\text{第一阶段：用生成目标学习可迁移的语言表示}
}
$$

$$
\boxed{
\text{第二阶段：用任务标签将整个模型适配到具体判断}
}
$$

所以，GPT-1 不是“给 Transformer 加一个文本生成按钮”，也不是“只训练一个句向量分类器”。**它用生成式预训练提供初始化，再通过简单输入变换和端到端微调获得多种理解能力。**

顺着这条线往下问就是：如果语言模型足够大、训练文本足够丰富，能否不再更新权重，只用上下文调用同一个模型？[[06-LLM/03-Transformer/GPT-2：从语言建模到零样本任务迁移.md|GPT-2 笔记]] 接着回答这个问题。

## Experiments

### 1. 训练配置：昂贵预训练，较快任务适配

原论文的主要配置为：

| 配置项 | 生成式预训练 | 大多数任务的微调 |
| --- | --- | --- |
| 优化器 | Adam，配合论文所述权重衰减 | 默认沿用相关优化设置 |
| 学习率 | 峰值 $2.5\times10^{-4}$ | $6.25\times10^{-5}$ |
| Warmup | 前 $2{,}000$ 次更新线性升温 | 训练进度的 $0.2\%$ |
| 后续学习率调度 | Cosine 衰减到零 | 线性衰减 |
| Batch size | $64$ 条连续序列 | $32$ |
| 训练轮数 | $100$ epochs | 多数任务 $3$ epochs |
| 辅助 LM 系数 | 此阶段只做 LM | 默认 $\lambda=0.5$ |

预训练序列长度为 $512$；embedding、attention 与 residual dropout 均为 $0.1$，微调分类器额外使用 $0.1$ 的 dropout。参见 [原论文第 4.1 节](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)。

官方介绍还报告，预训练约需在 $8$ 张 GPU 上运行 $1$ 个月。这个成本属于当时的实现与硬件条件；“下游微调快”不等于“从零获得预训练模型很便宜”。参见 [官方发布说明](https://openai.com/index/language-unsupervised/)。

### 2. 自然语言推理：有广泛收益，但不是所有数据集都领先

![[_assets/images/gpt-1-03-natural-language-inference.png|900]]

Table 2 的指标都是 accuracy；其中 `MNLI-m` 与 `MNLI-mm` 分别是 matched 与 mismatched 测试设置。

- GPT-1 在 MNLI 两个设置上分别得到 $82.1$ 与 $81.4$，在 SNLI 上得到 $89.9$。
- 在 SciTail 与 QNLI 上也取得论文报告的领先结果。
- **RTE 是重要反例**：GPT-1 为 $56.0$，表中 Multi-task BiLSTM + Attn 为 $61.7$。

论文指出 RTE 的训练样本较少，并提出多任务训练可能有帮助，但未在该工作中验证。因此，不能把其他 NLI 数据集的提升概括为“这种预训练在每个小样本任务上都必然更好”。

表中的部分基线是模型集成，必须连同对应标记一起阅读。

### 3. 问答与故事补全：生成式预训练帮助判别式选择

![[_assets/images/gpt-1-04-story-cloze-and-race.png|900]]

Table 3 中：

- Story Cloze 得分为 $86.5$，比较基线为 $77.6$；论文报告绝对提升 $8.9$ 个百分点。
- RACE 整体得分为 $59.0$，比较基线为 $53.3$；论文报告绝对提升 $5.7$ 个百分点。

这些结果来自**有监督微调后的候选打分**，不是直接让基础语言模型开放式生成答案，也不是只凭候选的原始 LM 概率。

另外，官方仓库说明：它公开实现的是 ROCStories / Story Cloze 路径，默认设置运行 $10$ 次的准确率中位数为 $85.8\%$，略低于论文单次报告的 $86.5\%$，并提示部分 GPU 运算具有非确定性。**论文表格数值与公开代码重复运行统计不能混成同一个口径。** 参见 [官方仓库说明](https://github.com/openai/finetune-transformer-lm)。

### 4. 分类、相似度与 GLUE：先看清各列的指标

![[_assets/images/gpt-1-05-similarity-classification-and-glue.png|900]]

Table 4 同时包含不同类型的评测：

- CoLA 的 $45.4$ 是 Matthews correlation 的表中得分，不是分类准确率。
- SST-2 使用 accuracy；MRPC 与 QQP 使用 F1。
- STS-B 的 $82.0$ 是 Pearson correlation 的表中得分。
- GLUE 总分为 $72.8$，表中此前最佳基线为 $68.9$。

不能因为一列更高，就认为所有任务都领先：SST-2 与 MRPC 都存在比 GPT-1 更高的表中基线。论文总体结论是在评估的 $12$ 个数据集中，有 $9$ 个取得当时最优结果，而不是全部任务领先。

**GLUE 总分也不等于下一张消融表中的 Avg. Score。** 两者的汇总口径不同，不能将 $72.8$ 与 $74.7$ 当成同一指标下的两次结果。

### 5. 消融：预训练很关键，辅助 LM 则依赖任务

![[_assets/images/gpt-1-06-pretraining-and-auxiliary-lm-ablation.png|900]]

Table 5 回答的是三个不同问题。

#### 5.1 如果取消预训练，会发生什么？

完整配置的 Avg. Score 为 $74.7$，去掉预训练后为 $59.9$。论文原文写作 “a $14.8\%$ decrease”；按这两行的数值，它是 $14.8$ 个平均分点的绝对差（相对降幅约 $19.8\%$），不应改写成“准确率相对下降 $14.8\%$”。

表中各任务均受到影响，支持“性能不只是来自 Transformer 结构本身，预训练初始化也很重要”。

#### 5.2 辅助 LM 是否一定提高最终指标？

不是。去掉辅助 LM 的 Avg. Score 为 $75.0$，反而略高于完整配置的 $74.7$。

逐列看，辅助 LM 帮助了 NLI 任务与 QQP，但在 CoLA、SST-2、MRPC、STS-B 上并未带来更高结果。作者观察到较大数据集更可能受益，较小数据集不一定如此。

因此，正确结论是：

> **辅助语言建模是一个有任务依赖性的微调选择，而不是 GPT-1 所有收益的必要来源。**

尤其不能把“去掉预训练”与“微调时去掉辅助 LM”混淆。后者仍然使用语言模型预训练得到的初始化。

#### 5.3 换成 LSTM 会怎样？

论文以同一训练框架中的单层、$2{,}048$ 单元 LSTM 作比较，Avg. Score 为 $69.1$，低于 Transformer 完整配置；MRPC 是该表中 LSTM 表现更好的例外。

这个实验支持论文所比较配置下 Transformer 的迁移优势，但它不是所有参数规模、所有训练预算下，Transformer 必然优于任意 LSTM 的普遍证明。

### 6. 层迁移与零样本分析：有效信息不只存在于 embedding

原论文 Figure 2 左侧改变从预训练模型迁移的层数，在 MultiNLI 与 RACE 上观察到：仅迁移 embeddings 已有帮助，迁移更多 Transformer 层进一步带来收益。

这支持“预训练的多层计算也具有可迁移价值”，而不是只有底部词向量值得保留。

Figure 2 右侧追踪不同训练进度下的 zero-shot 启发式表现，观察到这些规则的效果随 LM 预训练推进而改善。图中分数经过随机猜测基线与当时单模型最优表现之间的归一化，**不是可以直接当作任务准确率读取的纵轴**。

这些是分析证据：说明 LM 训练与任务相关能力共同发展，但没有证明所有能力都由同一种机制产生，也没有消除监督微调与 zero-shot 之间的差距。参见 [原论文第 5 节与 Figure 2](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)。

## Limitations & Caveats

### 论文与官方介绍报告或讨论的限制

- **迁移收益不均匀**：RTE、MRPC、SST-2 等结果提醒我们，预训练不是对所有数据集都自动取得最优成绩。
- **辅助 LM 并非普遍有效**：是否保留、怎样设置权重，需要依据任务与验证集判断。
- **预训练有显著成本**：模型能够较快微调，不代表最初的模型训练无需大量计算。
- **文本知识有缺失和偏差**：官方介绍指出，书籍与网络文本不包含完整、可靠的世界知识，模型也可能学习并利用数据偏差。
- **泛化仍然脆弱**：官方介绍明确讨论了对抗、系统性与分布外评测下的局限。参见 [官方 Drawbacks](https://openai.com/index/language-unsupervised/)。

### 根据架构与实验范围应保留的理解边界

- **不是双向编码器**：末端位置能汇集整个前缀，不意味着前面的每个 token 都能看到右侧内容。
- **不是现代指令对齐助手**：本文训练流程不包含指令数据上的通用对话适配或 RLHF，不能把判别任务微调直接等同于聊天训练。
- **上下文仍有窗口限制**：长书籍语料与 $512$ 个 token 的计算窗口是两个层面的事实。
- **预训练目标不保证事实正确**：语言概率高、候选分数高与陈述真实，不是同一性质。
- **“通用”有实验范围**：论文验证的是多种语言理解任务，不能仅凭这些结果推出多语言、多模态或任意开放式任务能力。
- **公开代码覆盖有限**：官方仓库主要公开 Story Cloze 的复现路径，不宜把其中所有实现细节都当成其他任务已公开验证的同一套逻辑。

## Open Questions / Follow-ups

下面是值得继续验证的问题，而不是原论文已经给出的结论：

1. **生成式预训练究竟贡献了什么？** 怎样区分词汇知识、句法结构、跨句依赖、世界知识与较好优化初始化的作用？
2. **哪些任务适合辅助 LM？** 除了数据量，输入分布、标签类型、候选构造与 loss 归约是否也会改变收益？
3. **单向模型怎样有效处理结构化输入？** 句对顺序、末端提取位置与双顺序聚合分别解决了什么，又留下哪些限制？
4. **从任务微调走向不改参数的使用，还缺什么？** 预训练规模、数据构造与评测方式应怎样变化，才能减少对任务专用 head 和监督更新的依赖？

最后可以把 GPT-1 的核心记成：

> **生成式预训练：先学会利用上下文预测语言。**
>
> **判别式微调：再把这些表示调整为完成具体任务的决策依据。**

它最重要的启发不是“生成与理解从此完全相同”，而是：**生成目标能够训练出对理解任务有用的表示，而简单、端到端的迁移方式就能把这种价值释放出来。**

## Citation

- [GPT-1 原论文](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf)：Alec Radford、Karthik Narasimhan、Tim Salimans、Ilya Sutskever，*Improving Language Understanding by Generative Pre-Training*，OpenAI，$2018$。
- [官方发布说明](https://openai.com/index/language-unsupervised/)：发布背景、计算成本、零样本分析与限制讨论。
- [官方代码仓库与复现说明](https://github.com/openai/finetune-transformer-lm)：公开的 Story Cloze 实现范围与重复运行统计。
- [网络、损失、特殊 token 与候选构造](https://github.com/openai/finetune-transformer-lm/blob/master/train.py)：Post-LN、causal mask、LM label shift、末端表示提取、联合微调与候选打分。
- [官方 tokenizer](https://github.com/openai/finetune-transformer-lm/blob/master/text_utils.py)：清洗、spaCy、小写化与 BPE。
- [基础词表](https://github.com/openai/finetune-transformer-lm/blob/master/model/encoder_bpe_40000.json)与[预训练参数形状](https://github.com/openai/finetune-transformer-lm/blob/master/model/params_shapes.json)：词表规模与基础参数量的核对来源。
- 本地原论文：[[06-LLM/03-Transformer/assets/paper_gpt1_2018.pdf]]。
- 结构参考：[[07-MultiModal/Video-MLLM/BLIP-2：用Q-Former连接冻结视觉编码器与大语言模型.md]]；后续对照：[[06-LLM/03-Transformer/GPT-2：从语言建模到零样本任务迁移.md|GPT-2 笔记]]。

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
