---
title: 从 Seq2Seq 到 Attention 再到 Transformer
aliases:
  - Seq2Seq → Attention → Transformer
  - Attention 演变史
tags:
  - deep-learning
  - nlp
  - seq2seq
  - attention
  - transformer
  - representation-learning
  - study-notes
status: evergreen
created: 2026-09-03
---

> [!summary] 一句话主线
> 这段历史真正改变的不是“RNN 被 Attention 替代”，而是**信息访问方式**：
>
> **RNN：用状态顺序搬运信息 → Seq2Seq：把整个输入压进一个状态 → Attention：保留所有状态并按需读取 → Transformer：让任意位置直接通信，因此不再需要 RNN 逐步传递信息。**

### 目录

- [[#1. 演变总览]]
- [[#2. RNN 为什么自然走向 Seq2Seq]]
- [[#3. Seq2Seq 的 fixed-vector bottleneck]]
- [[#4. Bahdanau Attention：从压缩到检索]]
- [[#5. Self-Attention：从顺序传递到直接通信]]
- [[#6. Transformer 的完整设计]]
- [[#7. Representation 如何变化]]
- [[#8. 信息系统视角与长上下文]]
- [[#9. 时间线与对比速记]]
- [[#10. 继续阅读与追问]]

## 1. 演变总览

这条路线可以压缩成一个问题：**模型应该把信息压缩后再使用，还是保留信息、在需要时检索？**

| 阶段 | 信息载体 | 访问方式 | 主要收益 | 新瓶颈 |
| --- | --- | --- | --- | --- |
| RNN | 当前 hidden state $h_t$ | 沿时间顺序传递 | 能处理变长序列 | 长距离依赖、无法并行 |
| Seq2Seq | 单个向量 $v=h_T$ | 先压缩，再生成 | 统一变长输入与输出 | fixed-vector bottleneck |
| Bahdanau Attention | 全部 encoder states $[h_1,\ldots,h_T]$ | decoder 按步检索 | 不必把信息提前压成一个向量 | encoder、decoder 仍是 RNN |
| Self-Attention | 全部 token 表示 | 序列内部按内容寻址 | 任意位置直接通信 | 注意力计算通常为 $O(T^2)$ |
| Transformer | 多层上下文化表示 | Self-Attention + FFN | 高并行、短信息路径 | 长上下文成本、位置表示等 |

三个关键公式：

**Seq2Seq：先压缩，再生成**

$$
(x_1,\ldots,x_T)\rightarrow\boxed{v}\rightarrow(y_1,\ldots,y_{T'})
$$

**Attention：保留全部状态，按当前需求读取**

$$
(h_1,\ldots,h_T)\xrightarrow{\text{query-dependent attention}}c_t\rightarrow y_t
$$

**Transformer：序列内任意位置直接通信**

$$
h_i\xleftrightarrow{\text{Self-Attention}}h_j,\qquad\forall i,j
$$

## 2. RNN 为什么自然走向 Seq2Seq

### 2.1 Hidden state 是历史摘要

标准 RNN 的更新为：

$$
h_t=f(h_{t-1},x_t)
$$

- $x_t$：当前输入
- $h_{t-1}$：截至上一步的历史信息
- $h_t$：读入 $x_t$ 后的新状态

不断展开可得：

$$
h_T=F(x_1,x_2,\ldots,x_T)
$$

因此，把最终状态记作：

$$
\boxed{v=h_T}
$$

是 RNN “状态机”思维的自然延伸。$v$ 不是最后一个词的表征，而是递归更新后对整个输入的压缩表示。

### 2.2 为什么需要 Encoder–Decoder

传统前馈网络常处理固定维度映射：

$$
x\in\mathbb R^n\rightarrow y\in\mathbb R^m
$$

机器翻译却是变长到变长：

$$
(x_1,\ldots,x_T)\rightarrow(y_1,\ldots,y_{T'}),\qquad T\neq T'
$$

早期深度学习又很习惯把复杂对象映射到一个固定维向量，例如文档的词袋向量、图像的 CNN 特征或单词 embedding。因此，一个自然的模块化方案是：

$$
\text{Variable Length}\rightarrow\boxed{\text{Fixed Vector}}\rightarrow\text{Variable Length}
$$

#### Encoder

$$
(x_1,\ldots,x_T)\rightarrow v
$$

Encoder 逐步读取输入，并把序列信息汇总到 $v$。

#### Decoder

$$
v\rightarrow(y_1,\ldots,y_{T'})
$$

Decoder 根据 $v$ 和已经生成的目标词逐步生成输出：

$$
p(y_1,\ldots,y_{T'}\mid x_1,\ldots,x_T)
=\prod_{t=1}^{T'}p(y_t\mid v,y_1,\ldots,y_{t-1})
$$

例如，输入 `I love you` 经过 Encoder 得到 $v$，Decoder 再生成“我 → 爱 → 你 → `<EOS>`”。

### 2.3 Seq2Seq 中的 representation

以 LSTM Encoder 为例：

$$
x_1,x_2,\ldots,x_T\rightarrow h_1,h_2,\ldots,h_T\rightarrow v=h_T
$$

这里的 $v$ 是整个 source sequence 的 **fixed-dimensional representation**。它是 global representation，但不是一个“最后 token 向量”。

## 3. Seq2Seq 的 fixed-vector bottleneck

Seq2Seq 的根本限制是：无论输入多长，所有信息都必须压进同样大小的向量：

$$
v\in\mathbb R^d
$$

例如，10 个 token 和 1000 个 token 最终都要映射到同一个 $\mathbb R^{1000}$ 空间。输入越长，压缩压力越大。

> [!important] Fixed-vector bottleneck
> 所有 source information 都必须先汇总到单个向量 $v$，Decoder 无法在生成过程中直接回看输入的某个位置。

这个瓶颈会带来三类后果：

1. **信息丢失**：不容易保留长句中的细节。
2. **梯度路径变长**：输入早期位置对输出的影响都要经过同一个压缩状态。
3. **解码时不可回看**：一旦信息没有进入 $v$，后续步骤无法重新取回。

关键转折是：Encoder 明明已经产生了 $h_1,h_2,\ldots,h_T$，为什么 Decoder 只能看到最后的 $h_T$？

## 4. Bahdanau Attention：从压缩到检索

### 4.1 核心想法

Attention 保留全部 Encoder states，让 Decoder 在每个生成步骤动态选择最相关的输入信息：

$$
(x_1,\ldots,x_T)\rightarrow(h_1,\ldots,h_T)\rightarrow c_t\rightarrow y_t
$$

$c_t$ 是当前生成步骤专属的 context vector；不同输出位置通常有不同的 $c_t$，不再整句共用一个 $v$。

### 4.2 计算过程

假设 Decoder 正在生成第 $t$ 个词，当前状态为 $s_{t-1}$。

**1. 计算匹配分数**

$$
e_{ti}=a(s_{t-1},h_i)
$$

其中 $s_{t-1}$ 表示“我现在需要什么”，$h_i$ 表示“输入第 $i$ 个位置保存了什么”。

**2. Softmax 归一化**

$$
\alpha_{ti}=\frac{\exp(e_{ti})}{\sum_j\exp(e_{tj})}
$$

**3. 加权汇聚**

$$
c_t=\sum_i\alpha_{ti}h_i
$$

再由 $c_t$、Decoder state 和历史输出共同预测 $y_t$。

### 4.3 翻译例子

Source：`The black cat sat on the table.`

当 Decoder 生成“猫”时，注意力可能集中在 `cat`：

| Source token     | The  | black | cat  | sat  | table |
| :--------------- | :--- | :---- | :--- | :--- | :---- |
| Attention weight | 0.02 | 0.12  | 0.78 | 0.04 | 0.04  |

此时：

$$
c_t\approx0.78h_{\text{cat}}+0.12h_{\text{black}}+\cdots
$$

当生成“桌子”时，权重会重新分布到 `table` 附近。这种 query-dependent context 是 Attention 的关键。

### 4.4 真正改变的是信息访问模式

| 架构 | Encoder 要做什么 | 信息访问方式 |
| --- | --- | --- |
| Seq2Seq | 提前判断什么值得压进 $v$ | **Compress First** |
| Attention | 保留局部状态，等待 decoder 查询 | **Retrieve When Needed** |

所以 Attention 不只是“给 token 加权”，而是把固定压缩改成了按需检索。

### 4.5 最初的 Attention 仍然依赖 RNN

Bahdanau Attention 并没有移除 recurrence：

$$
h_t=f(h_{t-1},x_t),\qquad s_t=f(s_{t-1},y_{t-1},c_t)
$$

当时的结构仍然是 **RNN Encoder → Attention → RNN Decoder**。Attention 先解决的是信息访问问题，而不是顺序计算问题。

## 5. Self-Attention：从顺序传递到直接通信

### 5.1 为什么还要去掉 RNN

RNN 的信息链是：

$$
h_1\rightarrow h_2\rightarrow h_3\rightarrow\cdots\rightarrow h_T
$$

若位置 1 的信息要影响位置 1000，必须经过约 1000 个中间步骤。这造成：

- **长路径依赖**：信息和梯度传播路径为 $O(T)$。
- **无法并行**：计算 $h_t$ 前必须先得到 $h_{t-1}$。

GPU 擅长大规模矩阵运算，却不擅长严格的逐步依赖链。

Attention 已经允许 Decoder 直接访问 Encoder 的任意位置，于是自然会追问：**一个序列内部的 token，为什么不能直接互相访问？**

### 5.2 Self-Attention 的本质

Self-Attention 让每个位置根据自身内容，从整个序列读取信息：

$$
x_i\rightarrow(x_1,\ldots,x_T)
$$

这把通信方式从：

$$
\boxed{\text{Sequential Communication}}
\quad\rightarrow\quad
\boxed{\text{Content-Addressable Communication}}
$$

例如句子 `The animal didn't cross the street because it was tired.` 中，处理 `it` 时可以直接关注 `animal`，不必沿着中间 token 逐步传递。

### 5.3 Q、K、V：可微分的内容寻址

给定输入表示 $X$：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V
$$

缩放点积注意力为：

$$
\operatorname{Attention}(Q,K,V)
=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

对位置 $i$ 而言：

- **Query $q_i$**：我现在想找什么？
- **Key $k_j$**：我是什么信息，是否值得被关注？
- **Value $v_j$**：如果关注我，我真正提供什么内容？

匹配分数 $q_i^\top k_j$ 经过 softmax 得到权重 $\alpha_{ij}$，再汇聚 Value：

$$
z_i=\sum_j\alpha_{ij}v_j
$$

因此，Attention 可以看成一个可微分的内容寻址系统：

> Query → 与所有 Key 匹配 → 得到权重 → 汇聚对应 Value。

### 5.4 为什么 Key 和 Value 要分开

一个 token 用来“被检索”的属性，和它真正要传递的内容不一定相同：

$$
K\Rightarrow\text{Match / Address},\qquad V\Rightarrow\text{Content}
$$

分开后，模型可以用一种表示决定“该不该读”，再用另一种表示决定“读到什么”。这也是 Attention 与 memory/retrieval 思想相近的原因。

### 5.5 Multi-Head Attention

语言关系有多种类型：主谓、修饰、指代、语义相似、局部组合和长距离依赖。单一注意力空间难以同时表达这些关系，因此 Transformer 使用多个 head：

$$
\text{head}_i=\operatorname{Attention}(QW_i^Q,KW_i^K,VW_i^V)
$$

$$
\operatorname{MultiHead}(Q,K,V)
=\operatorname{Concat}(\text{head}_1,\ldots,\text{head}_h)W^O
$$

> [!note] 直觉
> Multi-Head Attention 让模型在多个关系子空间中同时观察同一个序列。

### 5.6 去掉 RNN 后，顺序信息怎么办

纯 Self-Attention 对输入位置本身没有顺序概念。没有额外信息时，`dog bites man` 和 `man bites dog` 的排列不易区分。

因此需要把 token 表示与位置表示结合：

$$
x_i=e_i+p_i
$$

- $e_i$：token embedding
- $p_i$：position representation

这体现了一个重要变化：

| 架构 | 顺序写在哪里 |
| --- | --- |
| RNN | 写在计算结构中：$x_1\rightarrow x_2\rightarrow x_3$ |
| Transformer | 写在输入表示中：$e_i+p_i$ |

## 6. Transformer 的完整设计

### 6.1 一层 Transformer 做什么

Transformer 一层至少包含两种核心操作：

#### Self-Attention：token 之间交换信息

$$
H^{(l)}\rightarrow\operatorname{SelfAttn}(H^{(l)})
$$

可以记为 **Communication**：每个 token 从其他 token 获取相关信息。

#### FFN：每个 token 内部加工信息

$$
\operatorname{FFN}(x)=W_2\sigma(W_1x)
$$

可以记为 **Computation**：对已经汇聚好的信息做非线性变换。

经典实现还会用残差连接与 LayerNorm 稳定深层训练，可抽象为：

$$
H'=\operatorname{LN}(H+\operatorname{MHA}(H))
$$

$$
H^{\text{next}}=\operatorname{LN}(H'+\operatorname{FFN}(H'))
$$

> [!tip]+ 一句话记忆
> **Attention 负责通信，FFN 负责加工。**


### 6.2 Transformer 为什么适合 GPU

RNN 的更新：

$$
h_t=f(h_{t-1},x_t)
$$

有严格的 sequential dependency。Self-Attention 则可以一次性完成：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V
$$

核心矩阵乘法 $QK^\top$ 可以在整个 sequence 上并行执行。若 $Q\in\mathbb R^{T\times d}$，则：

$$
QK^\top\in\mathbb R^{T\times T}
$$

标准全注意力的计算复杂度通常为 $O(T^2d)$，显存也会随 $T^2$ 增长。但在相同序列长度下，矩阵运算的高并行性通常比 RNN 的逐步执行更适合 GPU/TPU。

> [!important] 复杂度与硬件效率不是一回事
> *Transformer* 不一定具有更低的理论复杂度；它的关键优势是把工作转换成硬件擅长的并行矩阵运算。

### 6.3 信息路径长度

若位置 1 的信息要影响位置 $T$：

|       架构       |                           信息路径                            |  路径长度  |
| :------------: | :-------------------------------------------------------: | :----: |
|      RNN       | $1\rightarrow2\rightarrow3\rightarrow\cdots\rightarrow T$ | $O(T)$ |
| Self-Attention |                     $1\rightarrow T$                      | $O(1)$ |

更短的路径让长距离依赖更容易被优化，但并不意味着模型自动理解所有关系；注意力权重、层数、训练数据和位置表示仍然重要。

### 6.4 Transformer 的激进之处

2017 年 Transformer 的关键不只是“Attention 很有用”，而是证明：

> **Attention 本身可以承担原来由 recurrence 负责的主要序列建模功能。**

因此经典架构可以概括为：

$$
\boxed{\text{Remove Recurrence}+\text{Self-Attention}+\text{FFN}+\text{Position Information}}
$$

## 7. Representation 如何变化

这条历史也可以理解为 representation 形态的变化：

| 阶段          | 主要表示                                              | 表示的含义                              |
| :---------- | :------------------------------------------------ | :--------------------------------- |
| RNN         | $h_t$                                             | 截至时刻 $t$ 的历史摘要                     |
| Seq2Seq     | $v=h_T$                                           | 整个输入的单一 global representation      |
| Attention   | $[h_1,\ldots,h_T]$ 与 $c_t$                        | 保留局部表示，再按 decoder query 形成 context |
| Transformer | $h_i^{(0)}\rightarrow\cdots\rightarrow h_i^{(L)}$ | 每个 token 在全局上下文中的多层表示              |

在 Transformer 中，最终的 $h_i^{(L)}$ 不再只是第 $i$ 个 token 本身，而是它与整个上下文交互后的表示。

## 8. 信息系统视角与长上下文

### 8.1 从 state-based memory 到 retrieval-based memory

**RNN：state-based**

过去发生的内容不断更新 hidden state，当前状态承载所有历史的浓缩结果：

$$
\boxed{\text{State-Based Memory}}
$$

**Attention：memory + retrieval**

局部表示全部保留，当前查询再动态检索相关位置：

$$
\boxed{\text{Memory + Retrieval}}
$$

所以整段演变可概括为：

$$
\boxed{\text{Compression}\rightarrow\text{Retrieval}}
$$

### 8.2 为什么和今天的 LLM、长上下文仍然相关

Attention 当年解决的是：不要把所有 source information 过早压成一个 fixed vector。现代 Transformer 因此倾向于保留大量 token representation，并在需要时通过 Attention 读取。

但上下文长度 $T$ 增大后，标准全注意力的成本也增大：

$$
T\uparrow\quad\Rightarrow\quad\text{Attention Cost}\uparrow\quad\text{(通常为 }O(T^2)\text{)}
$$

于是今天仍在研究：

- Token Compression
- KV Cache Compression
- Retrieval
- Sparse Attention
- Memory 与 Long-Context Routing
- Visual Token Pruning

这又回到了一个老问题：

> [!question] 长上下文的核心取舍
> 我们应该保留多少信息？什么时候压缩？由谁判断哪些信息重要？需要时如何找到关键 evidence？

### 8.3 和长视频理解的对应关系

假设有 512 帧，每帧编码为 $z_i$：

$$
z_1,z_2,\ldots,z_{512}
$$

#### 路线 A：全部保留

$$
[z_1,\ldots,z_{512}]\rightarrow\text{MLLM}
$$

优点是信息完整；代价是 visual token、encoder cost、prefill latency、KV cache 和 attention cost 都会上升。

#### 路线 B：先压缩或选帧

$$
[z_1,\ldots,z_{512}]\rightarrow[z_{i_1},\ldots,z_{i_B}]
$$

优点是效率高；风险是关键 evidence 可能在下游查询前就被丢弃。

因此，query-aware frame selection 可以看作在“全部保留”和“过早压缩”之间寻找一个 **query-conditioned information bottleneck**。

## 9. 时间线与对比速记

### 9.1 时间线

1. **RNN**：$h_t$ 作为历史摘要；问题是长依赖与顺序计算。
2. **LSTM**：改进状态机制，使长期信息更容易保存。
3. **Seq2Seq**：$(x_1,\ldots,x_T)\rightarrow v\rightarrow(y_1,\ldots,y_{T'})$，统一变长输入与输出；问题是 fixed-vector bottleneck。
4. **Bahdanau Attention**：$(h_1,\ldots,h_T)\rightarrow c_t$，Decoder 按当前需求动态访问 Encoder states；本质是从提前压缩转向按需检索。
5. **Self-Attention**：$\text{Token}_i\leftrightarrow\text{Token}_j$，同一序列内直接通信；本质是从顺序传递转向按内容寻址。
6. **Transformer**：去掉 recurrence，以 Self-Attention 建模关系，以 FFN 做 token 内加工，并显式注入位置。

### 9.2 一张对比表

| 问题 | RNN | Seq2Seq | Attention | Transformer |
| --- | --- | --- | --- | --- |
| 信息保存 | 当前 state | 单个 $v$ | 全部 $h_i$ | 多层 token 表示 |
| 读取方式 | 顺序读取 | 只读 $v$ | decoder 动态读取 | token 之间直接读取 |
| 长距离路径 | $O(T)$ | 经过 bottleneck | decoder 到各 $h_i$ | 通常 $O(1)$ |
| 训练并行性 | 低 | 低 | 仍受 RNN 限制 | 高 |
| 主要代价 | 长依赖 | 信息压缩损失 | 仍需 recurrence | 全注意力的 $O(T^2)$ |

### 9.3 一页速记

> [!abstract] Seq2Seq → Attention → Transformer
> **RNN**：用 hidden state 不断浓缩历史。
>
> $$h_t=f(h_{t-1},x_t)$$
>
> **Seq2Seq**：把整个输入浓缩成 $v=h_T$，再由 Decoder 生成目标序列。
>
> $$X\rightarrow v\rightarrow Y$$
>
> **Attention**：保留所有 Encoder states，在每个 Decoder step 计算 $c_t=\sum_i\alpha_{ti}h_i$。
>
> **Self-Attention**：让同一序列内的 token 直接互相访问，$z_i=\sum_j\alpha_{ij}v_j$。
>
> **Transformer**：去掉 RNN；Attention 负责通信，FFN 负责加工，位置表示补回顺序信息。
>
> $$\operatorname{Attention}(Q,K,V)=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$

## 10. 继续阅读与追问

### 10.1 核心论文

1. Sutskever et al., 2014，*Sequence to Sequence Learning with Neural Networks*
2. Cho et al., 2014，*Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation*
3. Bahdanau et al., 2014/2015，*Neural Machine Translation by Jointly Learning to Align and Translate*
4. Vaswani et al., 2017，*Attention Is All You Need*

### 10.2 相关笔记

- [[为什么 Q K V 必须分开？]]
- [[Multi-Head Attention 到底学到了什么？]]
- [[为什么 Transformer 还需要 FFN？]]
- [[Positional Encoding 为什么不可缺少？]]
- [[Decoder-only LLM 是怎样从原始 Transformer 演化来的？]]
- [[为什么 KV Cache 只缓存 K 和 V？]]
- [[Attention 的 O(T^2) 到底从哪里来？]]
- [[长上下文为什么又重新需要 Compression 和 Retrieval？]]
- [[Visual Token Compression 与早期 Seq2Seq bottleneck 有什么联系？]]

### 10.3 最后一句总结

> [!quote]
> **Seq2Seq 认为：把过去压缩好，再使用。**  
> **Attention 认为：先保留过去，需要时再查。**  
> **Transformer 进一步认为：既然所有信息都能直接查，就没有必要再沿着 RNN 的时间链一站一站地传递。**
