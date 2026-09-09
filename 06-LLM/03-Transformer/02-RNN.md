---
title: "RNN 与循环语言模型"
aliases:
  - "RNN"
  - "Recurrent Neural Network"
  - "RNN Language Model"
  - "循环神经网络"
tags:
  - nlp
  - rnn
  - language-model
  - sequence-modeling
  - bptt
type: learning-note
topic: rnn
content_status: complete
learning_status: not-started
created: 2026-09-05
updated: 2026-09-05
---

> [!abstract] 笔记定位
> 本节从**语言模型**出发，说明 n-gram 与固定窗口神经语言模型为什么需要截断上下文，再推导 vanilla RNN 如何用共享参数和递归 hidden state 处理任意长度序列。重点覆盖 RNN-LM 的前向计算、Teacher Forcing、BPTT、梯度消失/爆炸与困惑度。LSTM/GRU 和 Seq2Seq 只负责建立下一阶段接口，具体结构分别放在 [[03-LSTM与GRU|03-LSTM与GRU]] 与 [[04-Seq2Seq|04-Seq2Seq]]。

> [!important] 核心结论
> RNN 的关键不是“网络画成了环”，而是同一个状态转移函数在时间上反复复用：
> $$
> \boxed{h_t=f_\theta(h_{t-1},X_t)}
> $$
> 它用固定规模参数压缩可变长度历史，但信息与梯度都必须穿过一条长链；这既带来顺序建模能力，也导致难以并行、长程依赖难学以及梯度消失/爆炸。


## 学习目标

- [ ] 用链式法则写出自回归语言模型的联合概率
- [ ] 解释 n-gram 的 Markov 假设、稀疏问题与存储问题
- [ ] 说明固定窗口神经语言模型为何仍不能处理任意长上下文
- [ ] 写出 vanilla RNN-LM 的 embedding、状态更新、输出与 loss
- [ ] 解释“参数共享”和“展开计算图”为什么并不矛盾
- [ ] 区分 Teacher Forcing、自由生成与 Truncated BPTT
- [ ] 从 Jacobian 连乘解释梯度消失和梯度爆炸
- [ ] 说明 gradient clipping 能解决什么、不能解决什么
- [ ] 正确解释 perplexity，并知道何时不能直接横向比较
- [ ] 说明 RNN 为什么既能作为 Seq2Seq Encoder，也能作为自回归 Decoder

> [!info]+ 参考资料
> 主线按 Language Modeling → n-gram → fixed-window neural LM → RNN-LM → BPTT → 梯度问题组织，并在结尾衔接门控 RNN 与 Seq2Seq。
>
> | 类型 | 资料与本地文件 | 说明 |
> | --- | --- | --- |
> | 课程课件 | [[cs224n-2026-lecture04-rnnlm.pdf\|CS224N Lecture 4: Language Models and Recurrent Neural Networks]] | 本笔记的主要参考资料 |
> | 前置知识 | [[00-分词\|00-分词]] | 文本到 token IDs |
> | 前置知识 | [[01-词向量\|01-词向量]] | token IDs 到 embedding |
> | 下一阶段 | [[03-LSTM与GRU\|03-LSTM与GRU]] | 用门控改善递归记忆 |
> | 下一阶段 | [[04-Seq2Seq\|04-Seq2Seq]] | Encoder-Decoder 条件序列生成 |


## 0. 先建立完整心智模型

### 0.1 从 Token 到下一个 Token

一个 RNN 语言模型的主数据流是：

$$
\boxed{
x_t
\xrightarrow{E}
X_t
\xrightarrow{h_{t-1},\,f_\theta}
h_t
\xrightarrow{W_U,\,\operatorname{softmax}}
P(x_{t+1}\mid x_{\le t})
}
$$

其中：

- $x_t$：第 $t$ 个 token ID；
- $X_t$：当前 token 的 embedding；
- $h_t$：读完 $x_{\le t}$ 后的 hidden state；
- $P_t$：对下一个 token $x_{t+1}$ 的概率分布；
- 同一组 $E,W_h,W_x,W_U$ 在每个时间步重复使用。

> [!note] 两条链同时存在
> - **前向信息链**：历史信息通过 $h_0\to h_1\to\cdots\to h_N$ 传播；
> - **反向梯度链**：训练信号沿展开后的计算图从后向前传播。
>
> 前者让 RNN 能利用历史，后者让 RNN 能学习如何保存历史；梯度消失时，模型即使“看过”很早的 token，也未必能学会如何使用它。

### 0.2 五个阶段不要混淆

> [!note] 本篇符号
> 沿用 [[06-transformer|Transformer 基础知识与例题]]：$V$ 是词表大小，$N$ 是序列 token 数，$B$ 是 batch size。RNN 的输入维度为 $D_{\mathrm{emb}}$，隐藏维度为 $D_{\mathrm{rnn}}$；$d_h$ 留给后续注意力头维度。
>
> $x_t$ 始终是 token ID，$X_t=E[x_t,:]$ 是查表后的输入行向量；$h_t$ 是状态行向量。单样本输入和状态分别为 $[1,D_{\mathrm{emb}}]$、$[1,D_{\mathrm{rnn}}]$，batch 时将第一维换成 $B$。输出 logits 记为 $Z_t$，概率向量记为 $P_t=\operatorname{softmax}(Z_t)$。

| 阶段 | 给模型什么 | 模型做什么 | 典型关键词 |
| --- | --- | --- | --- |
| Tokenization | raw text | 生成 token IDs | vocabulary、subword |
| Embedding | token ID $x_t$ | 查表得到 $X_t$ | $X_t=E[x_t,:]$ |
| Recurrent update | $X_t,h_{t-1}$ | 更新记忆 $h_t$ | parameter sharing |
| Next-token prediction | $h_t$ | 产生 $P_t$ | logits、softmax |
| Sequence training | 全序列目标 | 累加损失并反向传播 | Teacher Forcing、BPTT |


## 1. 语言模型：把文本写成条件概率的乘积

### 1.1 两种等价视角

语言模型既可以被看作“预测下一个 token”的系统：

$$
P(x_{t+1}\mid x_1,\ldots,x_t),
$$

也可以被看作“给整段文本分配概率”的系统。由概率链式法则：

$$
\begin{aligned}
P(x_1,\ldots,x_N)
&=P(x_1)P(x_2\mid x_1)\cdots P(x_N\mid x_{<N})\\
&=\prod_{t=1}^{N}P(x_t\mid x_{<t}).
\end{aligned}
$$

![[_assets/images/01-语言模型链式分解.png|900]]

*图 1：语言模型通过链式分解为整段文本分配概率；真正需要建模的是每一步的 next-token distribution。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=4|CS224N Lecture 4，PDF 第 4 页]]。*

> [!important] 链式法则不是模型假设
> $P(x_{1:N})=\prod_tP(x_t\mid x_{<t})$ 对任意联合分布都成立。真正的建模选择在于：如何参数化这些条件概率，以及是否主动丢弃一部分历史。

### 1.2 为什么 next-token prediction 能学到很多能力

为了预测下一个 token，模型可能需要同时利用：

- 局部语法：冠词、数的一致、搭配；
- 指代关系：代词应该回指谁；
- 词汇语义与主题：哪些词在当前语境下合理；
- 情感与语用：上下文表达的是赞扬还是批评；
- 一部分事实知识、模式归纳和简单推理。

语言模型目标并不直接标注这些能力，而是把它们都变成“降低下一个 token 的预测损失”所需的中间结构。


## 2. n-gram 语言模型：用 Markov 假设截断历史

### 2.1 定义与计数估计

$n$-gram 是连续 $n$ 个 token 的片段。一个 $n$-gram LM 假设：预测 $x_{t+1}$ 时，只看前面的 $n-1$ 个 token：

$$
P(x_{t+1}\mid x_{1:t})
\approx
P(x_{t+1}\mid x_{t-n+2:t}).
$$

最大似然计数估计为：

$$
\hat P(x_{t+1}\mid x_{t-n+2:t})
=
\frac{C(x_{t-n+2:t+1})}{C(x_{t-n+2:t})}.
$$

例如在 4-gram 模型中，若 `students opened their` 出现 1000 次，`students opened their books` 出现 400 次，则：

$$
\hat P(\text{books}\mid\text{students opened their})=\frac{400}{1000}=0.4.
$$

### 2.2 两类稀疏问题

| 问题 | 现象 | 传统缓解方式 |
| --- | --- | --- |
| 完整 $n$-gram 未见过 | 分子计数为 0，候选词概率变成 0 | smoothing：为未见事件保留概率质量 |
| 上下文本身未见过 | 分母为 0，整条条件分布无法估计 | backoff/interpolation：退回更短上下文 |

增大 $n$ 可以看到更长的局部上下文，却会迅速放大数据稀疏与存储成本。语料越大，见过的不同 $n$-gram 也越多，需要存储的计数表越大。

> [!warning] “多看几个词”不能根治问题
> n-gram 把序列记忆放进显式计数表。$n$ 越大，可能的上下文组合按词表规模组合爆炸；模型并没有学到不同上下文之间可共享的连续表示。

### 2.3 生成方式

给定初始上下文，重复执行：

1. 查询下一个 token 的条件分布；
2. 从该分布采样或取最大概率项；
3. 把生成 token 接到上下文后；
4. 继续，直到生成结束标记。

n-gram 可能生成局部语法尚可、整体却不连贯的文本，因为超出窗口的信息已经被模型显式丢弃。


## 3. 固定窗口神经语言模型：连续表示仍不等于无限上下文

### 3.1 前向计算

设窗口大小为 $k$，取最近 $k$ 个 token 的 embedding 并拼接：

$$
X
=
\operatorname{Concat}(X_{t-k+1},\ldots,X_t),
\qquad
X_i=E[x_i,:].
$$

拼接沿特征维进行，$X\in\mathbb R^{1\times kD_{\mathrm{emb}}}$，$W\in\mathbb R^{kD_{\mathrm{emb}}\times D_{\mathrm{rnn}}}$。再经过前馈网络：

$$
h=f(XW+b_1),
\qquad
P
=\operatorname{softmax}(hW_U+b_2).
$$

![[_assets/images/02-固定窗口神经语言模型.png|900]]

*图 2：固定窗口神经语言模型把若干位置的 embedding 拼接后预测下一个词。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=21|CS224N Lecture 4，PDF 第 21 页]]。*

### 3.2 相比 n-gram 的改进

- embedding 让相似 token 共享统计强度，缓解离散计数稀疏；
- 不必保存每个出现过的 $n$-gram 及其计数；
- 神经网络可以学习上下文 token 的组合特征；
- 输出不再局限于少数有非零计数的候选词。

### 3.3 仍然存在的结构性限制

1. **窗口固定**：窗口外的 token 无论多重要都不可见；
2. **扩大窗口会扩大参数矩阵**：输入维度从 $D_{\mathrm{emb}}$ 增至 $kD_{\mathrm{emb}}$；
3. **不同位置使用不同输入行块的权重**：同一个词出现在不同相对位置，处理方式不对称；
4. **无法原生接收任意长度输入**。

> [!summary] 从固定窗口走向 RNN 的动机
> 我们需要一个函数：
> - 可以处理任意长度序列；
> - 每一步都使用同一套参数；
> - 把过去压缩成固定维度状态，并随输入逐步更新。


## 4. Vanilla RNN：重复应用同一个状态转移函数

### 4.1 单步公式

令词表大小为 $V$，embedding 维度为 $D_{\mathrm{emb}}$，hidden size 为 $D_{\mathrm{rnn}}$。一种简单 RNN-LM 写作：

$$
\begin{aligned}
X_t &= E[x_t,:],\\
a_t &= h_{t-1}W_h+X_tW_x+b_h,\\
h_t &= \phi(a_t),\\
Z_t &= h_tW_U+b_U,\\
P_t &= \operatorname{softmax}(Z_t).
\end{aligned}
$$

这里 $\phi$ 常取 $\tanh$；$P_t\in\mathbb R^{1\times V}$ 表示：

$$
P_{t,w}=P_\theta(x_{t+1}=w\mid x_{\le t}).
$$

![[_assets/images/03-简单RNN语言模型.png|900]]

*图 3：RNN-LM 在时间上重复使用同一套 embedding、状态转移和输出参数。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=24|CS224N Lecture 4，PDF 第 24 页]]。*

### 4.2 Shape 检查

单样本时，输入 token ID $x_t$ 是一个整数，查表后才进入矩阵运算：

| 参数 / 变量 | Shape | 作用 |
| --- | --- | --- |
| $E$ | $[V,D_{\mathrm{emb}}]$ | 每行存一个 token embedding |
| $X_t=E[x_t,:]$ | $[1,D_{\mathrm{emb}}]$ | 当前输入行向量 |
| $W_x$ | $[D_{\mathrm{emb}},D_{\mathrm{rnn}}]$ | input-to-hidden |
| $W_h$ | $[D_{\mathrm{rnn}},D_{\mathrm{rnn}}]$ | hidden-to-hidden |
| $h_t$ | $[1,D_{\mathrm{rnn}}]$ | 历史摘要 |
| $W_U$ | $[D_{\mathrm{rnn}},V]$ | hidden-to-logits |
| $Z_t,P_t$ | $[1,V]$ | logits 与概率分布 |

> [!tip]- 从单样本扩展到 Batch
> 若同一时间步有 $B$ 个 token IDs，查表得到 $X_t\in\mathbb R^{B\times D_{\mathrm{emb}}}$，状态为 $h_t\in\mathbb R^{B\times D_{\mathrm{rnn}}}$。
> $$
> [B,D_{\mathrm{emb}}][D_{\mathrm{emb}},D_{\mathrm{rnn}}]
> \to[B,D_{\mathrm{rnn}}],
> $$
> $$
> [B,D_{\mathrm{rnn}}][D_{\mathrm{rnn}},V]\to[B,V].
> $$
> Batch 维保留，每个样本执行相同的状态更新。

### 4.3 初始状态 $h_0$

常见选择包括：

- 全零向量；
- 一个可训练参数；
- 由另一个网络产生，例如 Seq2Seq 中由 Encoder 提供 Decoder 初始状态。

$h_0$ 的选择不会改变 RNN 的递归本质，但会改变序列开始前模型拥有的信息。

### 4.4 参数共享与展开图

RNN 只有一组 $W_h$，但为了分析计算，会把它沿时间展开：

$$
h_0
\xrightarrow[X_1]{W_h}
h_1
\xrightarrow[X_2]{W_h}
\cdots
\xrightarrow[X_N]{W_h}
h_N.
$$

图上出现多份 $W_h$，表示**同一个参数在不同时间步被调用多次**，不是复制出了 $N$ 组独立参数。因此：

- 序列变长时，参数量不随 $N$ 增长；
- 每个时间步使用同一状态转移规律；
- 梯度必须汇总该参数所有“出现位置”的贡献。

### 4.5 优点与代价

| 优点 | 代价 |
| --- | --- |
| 接受任意长度输入 | 时间步之间有依赖，训练和推理难以沿序列完全并行 |
| 参数量不随上下文长度增长 | 所有历史被压入固定维度 hidden state |
| 同一权重处理所有位置 | 早期信息要经过很多次状态更新才能到达后面 |
| 理论上可利用很远的历史 | 实践中长程依赖受到优化与容量限制 |

> [!warning] “任意长度输入”不等于“无限记忆”
> RNN 的公式可以运行任意多步，但 $h_t$ 维度固定，而且每一步都被重写。可运行长度、可表达记忆与可训练的有效依赖长度是三个不同概念。

### 4.6 时间深度与层深度

RNN 沿时间展开已经形成很深的计算图，还可以把多个 RNN layer 纵向堆叠。令第 $\ell$ 层状态为 $h_t^{(\ell)}$：

$$
h_t^{(\ell)}
=\phi\left(
h_{t-1}^{(\ell)}W_h^{(\ell)}
+h_t^{(\ell-1)}W_x^{(\ell)}
+b^{(\ell)}
\right),
$$

其中第一层的 $h_t^{(0)}$ 可视为输入 embedding $X_t$。必须区分：

- **时间深度**：同一层从 $t-1$ 递归到 $t$；
- **网络深度**：同一时间步从第 $\ell-1$ 层传到第 $\ell$ 层。

堆叠层增加表示能力，但不会消除 recurrent time dependency；训练时梯度既要跨层传播，也要跨时间传播。


## 5. 训练 RNN 语言模型

### 5.1 每一步的 Cross-Entropy

若输入 $x_t$ 后要预测真实下一个 token $x_{t+1}$，单步损失为：

$$
J_t(\theta)
=-\log P_{t,x_{t+1}}
=-\log P_\theta(x_{t+1}\mid x_{\le t}).
$$

对序列 $x_{1:N}$，若输入 $x_t$ 预测 $x_{t+1}$，则共有 $N-1$ 个转移目标：

$$
J(\theta)
=\frac{1}{N-1}\sum_{t=1}^{N-1}J_t(\theta)
=-\frac{1}{N-1}\sum_{t=1}^{N-1}
\log P_\theta(x_{t+1}\mid x_{\le t}).
$$

若在序列前加入 `<s>`，也可以把 $x_1$ 纳入预测目标。无论采用哪种索引约定，最小化 NLL 都等价于最大化训练文本的条件概率乘积。

### 5.2 Teacher Forcing

训练时，第 $t$ 步的输入通常使用语料中的真实 token $x_t$，而不是模型上一步自己生成的 token：

$$
\underbrace{x_t^{\text{gold}}}_{\text{输入模型}}
\longrightarrow
\hat P(x_{t+1}\mid x_{\le t}^{\text{gold}}).
$$

![[_assets/images/04-Teacher-Forcing训练.png|900]]

*图 4：Teacher Forcing 用真实语料 token 驱动每个时间步，并把所有 next-token loss 汇总。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=31|CS224N Lecture 4，PDF 第 31 页]]。*

> [!important] Teacher Forcing 不是 BPTT
> - **Teacher Forcing**决定前向计算时，下一个时间步喂真实 token 还是模型生成 token；
> - **BPTT**决定如何在时间展开图上计算梯度；
> - **Truncated BPTT**决定梯度向前传播多少步。
>
> 三者处在不同维度，可以组合使用，不能互相当作同义词。

### 5.3 为什么按句子或 chunk 训练

在整个语料的所有时间步上一次性保存计算图，内存成本过高。实践中通常：

1. 取一批句子、文档片段或定长 chunks；
2. 前向计算每个时间步的预测与 loss；
3. 对 batch 的 loss 求平均或求和；
4. 反向传播并更新参数；
5. 继续下一批。

padding 位置必须通过 mask 排除，否则模型会把补齐符号当作真实训练目标。


## 6. BPTT：对展开后的共享计算图做反向传播

### 6.1 为什么共享参数的梯度要相加

同一个 $W_h$ 在每个时间步都参与计算。根据多变量链式法则：

$$
\boxed{
\frac{\partial J}{\partial W_h}
=
\sum_{t}
\left.
\frac{\partial J}{\partial W_h}
\right|_{\text{第 }t\text{ 次使用}}
}
$$

这与卷积核在不同空间位置共享参数后累加梯度是同一原则：一个参数节点有多条通向 loss 的路径，所有路径贡献相加。

![[_assets/images/05-BPTT.png|900]]

*图 5：Backpropagation Through Time 沿时间展开 RNN，并把共享权重在各时间步的梯度贡献累加。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=35|CS224N Lecture 4，PDF 第 35 页]]。*

### 6.2 一条远距离梯度路径

若较晚的损失 $J_t$ 要影响较早状态 $h_k$，$k<t$，先写出单步前向：

$$
a_j=h_{j-1}W_h+X_jW_x+b_h,
\qquad h_j=\phi(a_j).
$$

令 $G_j=\operatorname{diag}(\phi'(a_j))$，它把激活导数放到对角线上。对行向量的微小变化，有：

$$
\mathrm dh_j=\mathrm dh_{j-1}W_hG_j.
$$

因此前向的局部 Jacobian 因子记为 $F_j=W_hG_j$。令 $g_j=\partial J_t/\partial h_j$，梯度与 $h_j$ 一样按行排列，则单步反向为：

$$
\boxed{g_{j-1}=g_jG_jW_h^\top=g_jF_j^\top}.
$$

连续回传到较早位置：

$$
\boxed{
\frac{\partial J_t}{\partial h_k}
=\frac{\partial J_t}{\partial h_t}
F_t^\top F_{t-1}^\top\cdots F_{k+1}^\top
}.
$$

远距离梯度必须经过许多局部因子的连乘，这正是梯度消失与爆炸的数学来源。

> [!note]- 右乘前向怎样对应反向与参数梯度？
> 前向为 $h_{j-1}W_h$；反向先逐维乘激活导数，再右乘 $W_h^\top$。转置来自链式法则，前向权重始终按“输入维度 × 输出维度”定义。
>
> 对序列总损失 $J$，令 $\delta_j=\partial J/\partial a_j$，其中已累加本步及后续损失的贡献，则：
> $$
> \frac{\partial J}{\partial W_h}
> =\sum_j h_{j-1}^\top\delta_j.
> $$
> 每项的 shape 是 $[D_{\mathrm{rnn}},1][1,D_{\mathrm{rnn}}]\to[D_{\mathrm{rnn}},D_{\mathrm{rnn}}]$，与 $W_h$ 相同。矩阵乘法不能随意交换次序。

> [!example]- 三步标量 RNN：从前向到共享参数梯度
> 为隔离递归链，暂时用平方误差替代语言模型的 softmax loss：
> $$
> a_t=h_{t-1}w+X_t,\qquad h_t=\tanh(a_t),\qquad
> L=\tfrac12(h_3-1)^2.
> $$
> 设 $h_0=0,w=0.5,(X_1,X_2,X_3)=(1,0,0)$，这里只训练共享参数 $w$，$X_t$ 是已给定的标量输入。
>
> **前向：**
> $$
> h_1\approx0.761594,\qquad
> h_2\approx0.363399,\qquad
> h_3\approx0.179726.
> $$
> **反向：**记 $\delta_t=\partial L/\partial a_t$。因为只有最后一步有 loss：
> $$
> \begin{aligned}
> \delta_3&=(h_3-1)(1-h_3^2)\approx-0.793778,\\
> \delta_2&=\delta_3w(1-h_2^2)\approx-0.344476,\\
> \delta_1&=\delta_2w(1-h_1^2)\approx-0.072336.
> \end{aligned}
> $$
> 同一个 $w$ 被调用三次，因此它的总梯度是：
> $$
> \frac{\partial L}{\partial w}
> =\delta_1h_0+\delta_2h_1+\delta_3h_2
> \approx-0.550809.
> $$
> 其中每个 $\delta_t$ 已包含后续路径的贡献；这里再汇总 $w$ 在各时间步的局部使用贡献，不能只取最后一项 $\delta_3h_2$。
>
> **自检：**固定输入，将 $w$ 分别改成 $w\pm\epsilon$，重新计算完整前向。取 $\epsilon=10^{-5}$，中央差分 $[L(w+\epsilon)-L(w-\epsilon)]/(2\epsilon)$ 应接近 $-0.550809$。
>
> **学习记录：**我的手算梯度：____；数值差分：____；若只取最后一步，漏掉了：____。

### 6.3 Truncated BPTT

完整 BPTT 会让反向传播长度随序列增长。Truncated BPTT（TBPTT）只让梯度回传最近 $K$ 步：

$$
\frac{\partial J_t}{\partial h_{t-K-1}}
\approx 0.
$$

> [!note] Forward state 与 gradient horizon 可以不同
> 实现可以把上一 chunk 的 hidden state 传给下一 chunk，让前向状态继续携带历史；同时对该状态执行 detach，使梯度不跨越 chunk 边界。模型“前向看过更久”不等于训练信号也回传了同样久。

TBPTT 节省内存和计算，但主动截断了跨 chunk 的精确信用分配。课件提到约 20 步只是示意，不是适用于所有任务的固定超参数。


## 7. 梯度消失与梯度爆炸

### 7.1 Jacobian 连乘直觉

由次乘性：

$$
\left\|
\frac{\partial J_t}{\partial h_k}
\right\|
\le
\left\|
\frac{\partial J_t}{\partial h_t}
\right\|
\prod_{j=k+1}^{t}
\left\|F_j\right\|.
$$

- 如果这些 Jacobian 在相关方向上反复收缩，梯度随距离指数衰减；
- 如果它们在相关方向上反复放大，梯度可能迅速增长；
- 真正行为还取决于奇异值、方向对齐、激活饱和与具体序列，不能只用某一个标量机械判断。

![[_assets/images/06-梯度消失.png|900]]

*图 6：远处训练信号必须穿过一连串 recurrent Jacobian；当每一步都缩小时，信号越传越弱。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=45|CS224N Lecture 4，PDF 第 45 页]]。*

### 7.2 梯度消失为什么伤害长程依赖

假设句末目标依赖很早出现的 `tickets`。若来自句末 loss 的梯度传回早期时已经接近 0，则参数更新主要由附近 token 决定，模型很难学到“很久以前的信息必须保留到现在”。

> [!warning] 表征消失与梯度消失相关，但不完全等价
> - **前向遗忘**：旧信息在反复状态更新中被覆盖；
> - **梯度消失**：远端 loss 无法有效教会早期状态应该保存什么。
>
> 二者常共同导致长程依赖困难，但一个描述前向信号，另一个描述优化信号。

### 7.3 梯度爆炸的后果

SGD 更新为：

$$
\theta_{\text{new}}
=\theta_{\text{old}}-\eta\nabla_\theta J.
$$

若 $\|\nabla_\theta J\|$ 极大，一次更新就可能把参数推到高损失区域，甚至产生 `Inf` 或 `NaN`。

### 7.4 Gradient Clipping

global norm clipping 常写为：

$$
g_{\text{clip}}
=
g\cdot
\min\left(1,\frac{\tau}{\|g\|_2}\right).
$$

当 $\|g\|_2>\tau$ 时，它保留梯度方向，只缩小步长。

![[_assets/images/07-梯度裁剪.png|900]]

*图 7：梯度范数超过阈值时，按比例缩放后再执行参数更新。来源：[[cs224n-2026-lecture04-rnnlm.pdf#page=49|CS224N Lecture 4，PDF 第 49 页]]。*

> [!important] Gradient clipping 的能力边界
> Gradient clipping 是对**爆炸梯度**的直接保护措施；它不会让已经接近 0 的梯度重新变大，因此不能解决梯度消失，也不能自动赋予模型长期记忆。

### 7.5 梯度消失的结构性缓解方向

课件给出两条主线：

1. **显式、可控的记忆通路**：LSTM/GRU 用门控决定写入、保留与读取；
2. **更直接、更线性的跨位置通路**：Attention、residual connections 等减少信息和梯度必须逐步穿越的链长。

这解释了后续架构的动机，但不意味着任何单一技巧都能消除所有长程建模问题。


## 8. 从训练到生成

### 8.1 自回归 rollout

推理时没有真实的未来 token。模型从开始标记 `<s>` 出发，重复：

$$
\begin{aligned}
P_t&=P_\theta(\,\cdot\mid x_{\le t}),\\
\tilde x_{t+1}&\sim P_t
\quad\text{或}\quad
\tilde x_{t+1}=\arg\max_w P_{t,w},\\
\tilde x_{t+1}&\text{ 作为下一步输入。}
\end{aligned}
$$

直到生成 `</s>` 或达到最大长度。

| 阶段 | 第 $t+1$ 步输入来自哪里 | 目的 |
| --- | --- | --- |
| Teacher-forced training | 真实 token $x_{t+1}$ | 稳定、高效地计算监督损失 |
| Autoregressive generation | 模型生成 token $\tilde x_{t+1}$ | 在没有答案的情况下自由生成 |

> [!note] 训练/推理分布差异
> 训练时模型通常只见到正确前缀；生成时一个错误会进入后续上下文并继续影响状态。这种差异常被称为 exposure bias。它与 RNN 特别相关，但也是一般自回归模型的问题。

### 8.2 采样与 argmax

- **argmax/greedy**：每步选择最高概率 token，确定性强，但不保证整句联合概率最优；
- **sampling**：按分布随机采样，更多样，但可能引入低概率错误；
- 解码策略改变输出行为，却不改变模型训练出的条件分布本身。


## 9. 语言模型评估：Perplexity

### 9.1 定义

测试序列 $x_{1:N}$ 上的平均负对数似然为：

$$
J
=-\frac{1}{N}\sum_{t=1}^{N}\log P_\theta(x_t\mid x_{<t}).
$$

Perplexity 定义为：

$$
\boxed{
\operatorname{PPL}(x_{1:N})
=\exp(J)
=\left(
\prod_{t=1}^{N}
\frac{1}{P_\theta(x_t\mid x_{<t})}
\right)^{1/N}
}
$$

因此在相同数据和相同 token 单位下：

$$
\text{cross-entropy 越低}
\Longleftrightarrow
\text{perplexity 越低}
\Longleftrightarrow
\text{模型给真实序列的平均概率越高}.
$$

### 9.2 如何理解

PPL 是真实 token 条件概率倒数的几何平均。若模型在一个理想化任务中每一步都像在 $k$ 个等概率选项中选择，则 PPL 为 $k$；但真实模型的分布不均匀，不能把 PPL 字面解释为每步“固定有几个候选词”。

> [!warning] PPL 的可比性条件
> 只有在**相同测试集、相同 tokenization、相同边界与计数规则**下，PPL 才能直接比较。word-level、character-level 与不同 subword tokenizer 改变了 $N$ 和预测单位，因此其 token-level PPL 不能简单横向排名。


## 10. 衔接：从 RNN-LM 到 Seq2Seq

RNN 不只可以做无条件语言模型，也可以分别承担“读取输入序列”和“生成输出序列”两种角色：

$$
\boxed{
x_{1:N_{\mathrm{src}}}
\xrightarrow{\text{Encoder RNN}}
\text{source representation}
\xrightarrow{\text{Decoder RNN}}
y_{1:N_{\mathrm{tgt}}}
}
$$

Decoder 仍然逐步预测 next token，只是预测还要条件于源序列：

$$
P(y\mid x)
=
\prod_{t=1}^{N_{\mathrm{tgt}}}
P(y_t\mid y_{<t},x).
$$

因此可以先建立一个最短理解：

- Encoder RNN 把可变长度输入变成连续表示；
- Decoder RNN 是由该表示条件化的自回归语言模型；
- 输入与输出长度不必相等；
- 经典模型若只传递 Encoder 最终状态，会形成 fixed-vector bottleneck。

> [!note] 本节只负责建立接口
> Seq2Seq 的状态连接、`<BOS>/<EOS>`、target shifting、Teacher Forcing、端到端训练、padding/masking、greedy/beam search 与固定向量瓶颈，统一放在 [[04-Seq2Seq|04-Seq2Seq]] 中展开。本节只需知道：RNN 可以成为 Encoder，也可以成为 Decoder 的 recurrent backbone。

## 11. 常见混淆与能力边界

### 11.1 Hidden state 不等于概率分布

$h_t$ 是模型内部的连续表示；必须先映射到 vocabulary logits，再经 softmax 才得到 next-token probability：

$$
h_t
\xrightarrow{h_tW_U+b_U}
Z_t
\xrightarrow{\operatorname{softmax}}
P_t.
$$

### 11.2 RNN 不等于 RNN-LM

- **RNN**：一类序列神经架构；
- **RNN-LM**：把 RNN hidden state 接到 vocabulary softmax，用于 next-token prediction；
- 同一 RNN 也可用于序列分类、标注、编码等任务。

### 11.3 “最后状态包含所有历史”只是建模目标

递归定义保证 $h_t$ 是 $x_{1:t}$ 的函数，但不保证它无损保存每个 token，也不保证训练能找到这种参数。有限维度、非线性饱和、噪声与长链优化都会限制有效记忆。

### 11.4 梯度裁剪不改变前向记忆结构

clipping 只在参数更新前处理梯度范数。它不会为 hidden state 添加门控，也不会缩短依赖路径；所以“训练不再 NaN”不代表“已经学会长程依赖”。

### 11.5 TBPTT 不等于只读取 $K$ 个 token

如果 hidden state 跨 chunk 传递，前向表示仍可能包含更早历史；但梯度只回到最近 $K$ 步。它与固定窗口 LM 的“输入根本不可见”不同。

### 11.6 单向 RNN-LM 与双向 RNN

自回归生成要求第 $t$ 步只能使用过去：

$$
P(x_t\mid x_{<t}).
$$

双向 RNN 可以同时利用左右上下文，适合序列标注或表示学习；但若它在预测 $x_t$ 时已经看到未来 token，就不能直接作为严格的左到右生成式语言模型。


## 12. 总结

| 概念 | 最短定义 | 关键限制 |
| --- | --- | --- |
| Language Model | 为下一个 token 或整段序列分配概率 | 质量取决于条件分布建模方式 |
| n-gram LM | 只条件于最近 $n-1$ 个 token 的计数模型 | 稀疏、存储大、窗口固定 |
| Fixed-window neural LM | 拼接固定窗口 embedding 的前馈网络 | 参数随窗口扩大，仍丢弃远端历史 |
| Vanilla RNN | 重复使用同一状态转移函数 | 串行、固定状态瓶颈、长程依赖难 |
| Teacher Forcing | 训练时喂真实上一步 token | 与自由生成的输入分布不同 |
| BPTT | 在时间展开图上反向传播并累加共享参数梯度 | 长序列内存/计算大 |
| TBPTT | 只回传有限时间步 | 截断长期信用分配 |
| Vanishing Gradient | 远距离梯度经 Jacobian 连乘后衰减 | 难学长期依赖 |
| Exploding Gradient | 梯度范数快速增长 | 更新不稳定、Inf/NaN |
| Gradient Clipping | 超阈值时缩放梯度范数 | 只治爆炸，不治消失 |
| Perplexity | 平均 NLL 的指数 | 跨 tokenizer 不可直接比较 |
| Seq2Seq 衔接 | RNN 可作为 Encoder 或条件自回归 Decoder | 详细机制见 [[04-Seq2Seq\|04-Seq2Seq]] |

> [!important] 最终心智模型
> $$
> \boxed{
> \text{历史 token}
> \xrightarrow{\text{共享递归更新}}
> h_t
> \xrightarrow{\text{softmax}}
> P(x_{t+1}\mid x_{\le t})
> }
> $$
> RNN 用固定参数处理可变长度序列，但把信息和梯度都限制在逐步传递的链上。BPTT 让这条链可训练，梯度消失/爆炸揭示其优化困难；下一步先在 [[03-LSTM与GRU|03-LSTM与GRU]] 中学习可控记忆，再在 [[04-Seq2Seq|04-Seq2Seq]] 中学习如何把 Encoder 与条件自回归 Decoder 连接起来。


## 建议学习顺序

1. 先能从链式法则写出 $P(x_{1:N})$；
2. 手算一个 3-gram 条件概率，观察未见上下文问题；
3. 对照固定窗口与 RNN，确认“窗口参数增长”如何被“共享状态转移”替代；
4. 按 shape 手写一次 RNN 单步前向；
5. 画 4 个时间步的展开图，标出共享的 $W_h$；
6. 从 $\partial J_t/\partial h_k$ 推出 Jacobian 连乘；
7. 区分 Teacher Forcing、autoregressive rollout、BPTT 与 TBPTT；
8. 最后只需理解 RNN 可以成为 Encoder 或条件自回归 Decoder，完整 Seq2Seq 留到 [[04-Seq2Seq|04-Seq2Seq]]。


## 自测问题

1. 概率链式法则与 n-gram Markov 假设有什么本质区别？
2. n-gram 的 smoothing 和 backoff 分别处理哪一种稀疏问题？
3. 固定窗口神经 LM 相比 n-gram 改进了什么，又保留了什么限制？
4. 为什么 RNN 能处理任意长度输入，而参数量不随序列长度增加？
5. 在展开图中出现多个 $W_h$，为什么模型仍只有一组 recurrent weights？
6. 写出 $x_t\to X_t\to h_t\to P_t$ 的完整公式与 shape。
7. Teacher Forcing、BPTT 和 Truncated BPTT 分别决定什么？
8. 为什么共享参数的总梯度是各时间步贡献之和？
9. Jacobian 连乘为什么可能造成梯度消失或爆炸？
10. 前向遗忘与梯度消失为什么不能完全画等号？
11. Gradient clipping 为什么能限制爆炸梯度，却不能恢复消失梯度？
12. Perplexity 与 cross-entropy 有什么精确关系？为什么跨 tokenizer 比较不公平？
13. RNN-LM 训练和自由生成时，下一步输入分别来自哪里？
14. RNN 为什么既能作为序列 Encoder，也能作为自回归 Decoder？
15. 为什么双向 RNN 不能直接用于严格的左到右自回归生成？


## 学习记录

- [ ] 已通读主线与总结表
- [ ] 已手算 n-gram 条件概率
- [ ] 已完成一次 RNN 前向 shape 检查
- [ ] 已画出 4 步展开图并标注共享参数
- [ ] 已独立推导远距离梯度的 Jacobian 连乘
- [ ] 已区分 Teacher Forcing、BPTT 与 TBPTT
- [ ] 已计算一个小序列的 cross-entropy 与 perplexity
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前置章节 [[01-词向量|01-词向量]] 的联系：
- 与下一阶段 [[03-LSTM与GRU|03-LSTM与GRU]]、[[04-Seq2Seq|04-Seq2Seq]] 的联系：
