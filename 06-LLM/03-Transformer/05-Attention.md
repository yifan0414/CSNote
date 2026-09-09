---
title: "Attention：根据查询加权读取信息"
aliases:
  - "Attention"
  - "注意力机制"
  - "Cross-Attention 与 Self-Attention"
tags:
  - nlp
  - attention
  - seq2seq
  - cross-attention
  - self-attention
type: learning-note
topic: attention
content_status: complete
learning_status: not-started
created: 2026-09-05
updated: 2026-09-09
---

Attention（注意力机制）是一种**根据当前需求，从一组向量中提取信息**的计算方法。它先衡量每个候选与当前需求的匹配程度，再把匹配分数转成权重，最后汇聚候选的内容。

> [!tip] 阅读路线
> 本篇承接 [[04-Seq2Seq|Seq2Seq]]，重点回答三个问题：**为什么要按需读取、一次读取怎样计算、读取规则怎样学出来。**
>
> 首次阅读可按第 $1$—$8$ 节顺序前进：第 $1$—$4$ 节建立计算过程，第 $5$、$6$ 节讲训练与推理，第 $7$ 节用代码核对手算，第 $8$ 节说明构建 Transformer 还需要解决的问题。[[#附录 A：复制、平均与混合稳定性（选读）|附录 A]] 收录读取能力与噪声分析习题，[[#附录 B：Self-Attention 的排列等变性（证明）|附录 B]] 给出位置问题的数学证明，可在第二遍阅读时再看。

## 1. 为什么需要 Attention：从固定摘要到按需读取

### 1.1 传统 Seq2Seq 的固定向量瓶颈

机器翻译需要把一条源序列变成另一条目标序列。经典的 RNN Seq2Seq 使用 Encoder 逐步读取源句，将整句信息压缩成一个固定维度的向量 $z$，再让 Decoder 根据它生成目标句：

$$
\underbrace{x_1,\ldots,x_n}_{\text{源序列}}
\xrightarrow{\text{Encoder}}
\underbrace{z}_{\text{整句摘要}}
\xrightarrow{\text{Decoder}}
\underbrace{y_1,\ldots,y_m}_{\text{目标序列}}.
$$

这种方式为不同长度的输入提供了统一的接口，但也把所有源信息集中到同一个向量里。句子越长，需要保留的人物、动作、修饰和位置关系越多，而摘要的维度始终相同。Encoder 必须在读取过程中保留这些细节，Decoder 则要从这份摘要中恢复每个生成步骤需要的信息。

例如，将“她把书放在桌上”译为“She put the book on the table”时，生成 `She` 需要动作发出者的信息，生成 `book` 需要物体的信息，生成 `on the table` 需要位置关系。**不同目标步骤需要不同的源信息，而固定摘要在解码开始前就已经形成。** 一旦某个细节没有被充分保留，Decoder 便无法返回对应的源位置重新读取它。

### 1.2 Attention 的改变：保留源表示，每一步重新读取

Encoder 在处理源句时已经计算了每个位置的表示 $h_1,\ldots,h_n$。Attention 将这些表示全部保留下来，让 Decoder 根据当前状态决定各位置的读取比例：

$$
\boxed{c_t=\sum_{i=1}^n a_{t,i}h_i,\qquad a_{t,i}\ge0,\qquad\sum_{i=1}^n a_{t,i}=1.}
$$

其中 $a_{t,i}$ 是生成步骤 $t$ 对源位置 $i$ 的权重，$c_t$ 是这一步读到的上下文向量。Decoder 在生成下一个词时，同时使用自己的状态和这份上下文。

这样，摘要从预先固定的 $z$ 变成了随生成需求变化的 $c_t$。每次读取仍返回一个固定维度的向量，但完整的源表示始终可供访问：需要人物信息时重新读取人物相关位置，需要位置关系时再形成另一份摘要。源位置到当前预测之间也因此增加了一条直接的信息通路。[Bahdanau et al.](https://arxiv.org/abs/1409.0473)

由此得到 Attention 的基本思路：

$$
\boxed{\text{提出查询}\;\longrightarrow\;\text{计算匹配}\;\longrightarrow\;\text{分配权重}\;\longrightarrow\;\text{汇聚内容}}
$$

### 1.3 将按需读取写成通用的加权操作

从翻译场景中抽象出来，这个过程可以用于任意一组内容向量。

假设有 $n$ 个内容向量 $v_1,\ldots,v_n\in\mathbb R^{d_v}$。最简单的汇聚方法是取平均：

$$
c=\frac1n\sum_{i=1}^n v_i.
$$

平均给每个候选相同的比例。若当前任务更需要其中某些内容，可以改用加权和：

$$
c=\sum_{i=1}^n a_i v_i,\qquad a_i\ge0,\qquad\sum_{i=1}^n a_i=1.
$$

Attention 的关键在于：**权重随当前查询和候选内容而变化。** 同一组向量可以被反复读取，每次得到不同的汇聚结果 $c$。这个结果也称为 context vector（上下文向量）。

为了计算这些权重，需要给每个候选准备一个用于匹配的表示，并用一个查询向量表达当前需求。

## 2. Query、Key、Value：一次 Attention 的三个角色

Attention 将当前需求称为 **Query**，将候选的匹配表示称为 **Key**，将被读取的内容称为 **Value**。

| 角色 | 符号 | 作用 |
| --- | --- | --- |
| Query | $q\in\mathbb R^{d_k}$ | 表达这次读取需要什么 |
| Key | $k_i\in\mathbb R^{d_k}$ | 与 query 比较，决定候选 $i$ 的权重 |
| Value | $v_i\in\mathbb R^{d_v}$ | 提供候选 $i$ 被读取时传递的内容 |

每个 key 与一个 value 对应。一次查询面对 $n$ 组 key/value，计算 $n$ 个权重，返回一个 $d_v$ 维向量。

![[_assets/images/01-加权查表与QKV.png|900]]

图左展示一次加权读取：query 与所有 keys 匹配，得到的权重分别乘到对应的 values 上，再求和得到输出。图右的普通查表则直接返回匹配项的 value。图中“权重通过学习得到”指模型学会了计算权重的规则；具体权重仍由每次输入重新计算。

下面的单向量公式采用列向量记法。

### 2.1 打分：Query 与各个 Key 有多匹配？

最简单的打分函数是点积：

$$
s_i=q^\top k_i.
$$

Query 与 key 都有 $d_k$ 个分量，点积得到一个标量。它同时受到方向和模长的影响：

$$
q^\top k_i=\|q\|\,\|k_i\|\cos\theta_i.
$$

分数越大，表示该候选在当前匹配规则下越值得读取。

### 2.2 归一化：把分数变成读取比例

用 softmax 将分数归一化：

$$
\boxed{a_i=\frac{e^{s_i}}{\sum_{j=1}^n e^{s_j}}.}
$$

得到的权重均为正，且总和为 $1$。分数较大的候选会获得更多权重；所有分数相等时，权重都是 $1/n$。

权重之间的比例由分数差决定：

$$
\frac{a_i}{a_j}=e^{s_i-s_j}.
$$

因此 Attention 是在当前候选集合中分配读取比例。某个候选的分数保持不变时，其他候选分数的变化也会影响它的权重。

### 2.3 汇聚：根据权重读取 Values

将权重乘到对应的 values 上：

$$
\boxed{c=\sum_{i=1}^n a_i v_i.}
$$

**Query 与 keys 决定怎样读，values 决定读到什么。** Query/key 的匹配维度是 $d_k$，输出的内容维度是 $d_v$。

### 2.4 手算：同一张表，两次不同的查询

有三组二维 key/value，使用前面的未缩放点积打分：

| 候选 | Key | Value |
| --- | --- | --- |
| $1$ | $k_1=(1,0)^\top$ | $v_1=(2,0)^\top$ |
| $2$ | $k_2=(0,1)^\top$ | $v_2=(0,2)^\top$ |
| $3$ | $k_3=(1,1)^\top$ | $v_3=(1,1)^\top$ |

取 $q=(\ln2,0)^\top$，按“打分 → 归一化 → 汇聚”的顺序计算：

$$
\begin{aligned}
(s_1,s_2,s_3)&=(\ln2,0,\ln2),\\
(e^{s_1},e^{s_2},e^{s_3})&=(2,1,2),\\
(a_1,a_2,a_3)&=(0.4,0.2,0.4).
\end{aligned}
$$

读取结果为：

$$
c=0.4\begin{bmatrix}2\\0\end{bmatrix}
+0.2\begin{bmatrix}0\\2\end{bmatrix}
+0.4\begin{bmatrix}1\\1\end{bmatrix}
=\begin{bmatrix}1.2\\0.8\end{bmatrix}.
$$

将 query 改成 $q'=(0,\ln2)^\top$，得到：

$$
\begin{aligned}
(s'_1,s'_2,s'_3)&=(0,\ln2,\ln2),\\
(a'_1,a'_2,a'_3)&=(0.2,0.4,0.4),\\
c'&=\begin{bmatrix}0.8\\1.2\end{bmatrix}.
\end{aligned}
$$

两次读取使用相同的 key/value 表；query 改变了匹配分数，进而改变权重和结果。这里先手动指定 Q/K/V，下一节再说明模型怎样从输入中生成它们。

## 3. Q/K/V 怎样从输入表示中产生？

在神经网络中，Q/K/V 通常由输入表示经过可学习的线性投影得到。

设当前查询的输入表示为 $x_q\in\mathbb R^{d_q}$，第 $i$ 个候选的输入表示为 $x_i\in\mathbb R^{d_x}$：

$$
q=W_Q^\top x_q,\qquad
k_i=W_K^\top x_i,\qquad
v_i=W_V^\top x_i,
$$

其中：

$$
W_Q\in\mathbb R^{d_q\times d_k},\qquad
W_K\in\mathbb R^{d_x\times d_k},\qquad
W_V\in\mathbb R^{d_x\times d_v}.
$$

同一个候选通过 $W_K$ 生成匹配特征，通过 $W_V$ 生成内容特征。这使模型能够分别学习“什么信息适合用来寻找它”和“找到它之后应该传递什么”。最简单的形式也可以直接让 key 和 value 使用同一个输入表示。

这里的 $W_Q,W_K,W_V$ 是模型参数；$q,k_i,v_i$ 和权重 $a_i$ 是每次前向计算产生的数值。训练后，模型面对新的输入仍会计算新的读取权重。

### 3.1 Cross-Attention：从另一组表示中读取

当 query 来自一组表示，key/value 来自另一组表示时，称为 **Cross-Attention**。

在机器翻译中，Encoder 提供源句表示 $h_1,\ldots,h_n$，Decoder 提供查询。为了接上上一篇 Seq2Seq，这里采用一种简单的接入方式：**先用目标前缀更新 Decoder 状态，再读取源表示，最后预测当前目标词。**

![[_assets/images/02-Attention接入Decoder.png|900]]

图中绿色 Decoder 状态用于查询红色 Encoder 表示；蓝色 attention distribution 是读取权重，加权汇聚得到的 attention output 再与 Decoder 状态拼接，用于预测。图中的 `<START>` 对应本文的 `<BOS>`。

**准备：编码源句，保存可读取的内容。**

Encoder 完成一次编码后，为每个源位置生成 key/value，并通过 Bridge 初始化 Decoder：

$$
k_i=W_K^\top h_i,\qquad
v_i=W_V^\top h_i,\qquad
s_0=\operatorname{Bridge}(h_n).
$$

同一次源句编码得到的 key/value 可以在各个目标步骤中复用。Bridge 延续上一篇的初始化方式，Attention 则让后续步骤能够继续访问所有源位置。

**第一步：读取前一个目标词，形成当前查询。**

在第 $t$ 步，先计算：

$$
s_t=\operatorname{RNN}_{\mathrm{dec}}\bigl(s_{t-1},\operatorname{Embed}(y_{t-1})\bigr),\qquad
q_t=W_Q^\top s_t.
$$

起始输入为 $y_0=\texttt{<BOS>}$。此时 $s_t$ 已经包含目标前缀 $y_{<t}$ 的信息，因此能够提出查询；$y_t$ 将在后面预测。使用 teacher forcing 训练时，$y_{t-1}$ 来自真实译文；推理时，它来自前一步的生成结果。

**第二步：用查询读取源句。**

继续使用未缩放点积，以 $e_{t,i}$ 表示匹配分数，避免与 Decoder 状态 $s_t$ 混淆：

$$
e_{t,i}=q_t^\top k_i,\qquad
a_{t,i}=\frac{\exp(e_{t,i})}{\sum_{j=1}^n\exp(e_{t,j})},\qquad
c_t=\sum_{i=1}^n a_{t,i}v_i.
$$

**第三步：结合状态和读取结果，预测当前目标词。**

$$
p_t=\operatorname{softmax}\bigl(W_U^\top[s_t;c_t]+b_U\bigr),\qquad
p_t(w)=P(y_t=w\mid y_{<t},x_{1:n}).
$$

这里 $[s_t;c_t]$ 表示向量拼接，$p_t$ 是目标词表上的概率分布。推理时从该分布选择 $y_t$，再把它送入下一步。

将 Decoder 内的计算串起来：

$$
\boxed{\begin{aligned}
(s_{t-1},y_{t-1})&\longrightarrow s_t\longrightarrow q_t
\longrightarrow a_{t,:}\longrightarrow c_t,\\
[s_t;c_t]&\longrightarrow p_t\longrightarrow y_t.
\end{aligned}}
$$

例如，在前缀为 `She put the` 时，Decoder 先读入 `the` 更新状态，再查询源句中与当前预测有关的内容，最后预测 `book`。进入下一步时，key/value 表仍相同，新的状态会产生新的 query 和 context。源句中的同一位置可以在多个目标步骤中获得较高权重。

Attention 的 softmax 在**候选位置**之间分配读取权重；输出层的 softmax 在**目标词表**之间分配预测概率。

> [!note]- 与经典 RNN Attention 的关系
> 上述顺序采用先形成当前 Decoder 状态、再计算 Attention 的思路，便于与 [Luong et al.](https://aclanthology.org/D15-1166/) 的结构联系起来；投影和输出层使用了教学上的简化。不同 RNN Attention 也可以用前一状态计算 context，再让 context 参与当前状态更新。阅读具体模型时，需要确认查询来自哪个状态，以及 context 接入哪一步。

### 3.2 Self-Attention：让同一组表示互相读取

当 query、key 和 value 都来自同一组输入 $x_1,\ldots,x_N$ 时，称为 **Self-Attention**：

$$
q_i=W_Q^\top x_i,\qquad
k_i=W_K^\top x_i,\qquad
v_i=W_V^\top x_i.
$$

每个位置提出自己的 query，读取这组输入中的 values：

$$
c_i=\sum_{j=1}^N a_{ij}v_j.
$$

这样，每个位置的输出都能融合其他位置的内容，得到上下文化的表示。

例如，对于句子“The animal was tired, so it rested”，`it` 对应的 query 可以通过读取 `animal` 的内容获得实体信息，通过读取 `tired` 的内容获得状态信息。它们会按同一行权重汇聚到 `it` 的输出向量中。

| 类型 | Query 来源 | Key / Value 来源 |
| --- | --- | --- |
| Cross-Attention | 一组表示 | 另一组表示 |
| Self-Attention | 当前输入序列 | 同一个输入序列 |

两者使用相同的打分、归一化和汇聚过程，区别在于表示的来源。

## 4. 用矩阵一次完成多个查询

将所有向量转置后按行堆叠：

$$
Q=\begin{bmatrix}q_1^\top\\\vdots\\q_{N_q}^\top\end{bmatrix}
\in\mathbb R^{N_q\times d_k},\qquad
K=\begin{bmatrix}k_1^\top\\\vdots\\k_{N_k}^\top\end{bmatrix}
\in\mathbb R^{N_k\times d_k},\qquad
V=\begin{bmatrix}v_1^\top\\\vdots\\v_{N_k}^\top\end{bmatrix}
\in\mathbb R^{N_k\times d_v}.
$$

矩阵的行对应位置，列对应特征。所有 query 与 key 的点积可以一起计算：

$$
S=QK^\top\in\mathbb R^{N_q\times N_k},\qquad S_{ij}=q_i^\top k_j.
$$

沿每行的 key 轴做 softmax，再乘 value 矩阵：

$$
\boxed{A=\operatorname{softmax}_{\mathrm{row}}(S),\qquad C=AV.}
$$

$A$ 的第 $i$ 行是第 $i$ 个 query 的读取权重，$C$ 的第 $i$ 行是它的读取结果。

| 张量 | Shape | 含义 |
| --- | --- | --- |
| $Q$ | $N_q\times d_k$ | $N_q$ 个查询 |
| $K$ | $N_k\times d_k$ | $N_k$ 个匹配表示 |
| $V$ | $N_k\times d_v$ | $N_k$ 个内容表示 |
| $S,A$ | $N_q\times N_k$ | 每个 query 对各候选的分数、权重 |
| $C$ | $N_q\times d_v$ | 每个 query 读回的内容 |

**输出向量的数量由 query 数决定，输出向量的维度由 value 维度决定。** 例如，$3$ 个 queries 读取 $7$ 个六维 values，会得到 $3$ 个六维输出。

若输入矩阵 $X$ 也将 token 表示按行存放，self-attention 的投影就写成 $Q=XW_Q$、$K=XW_K$、$V=XW_V$。

### 4.1 缩放点积：控制匹配分数的尺度

随着匹配维度 $d_k$ 增大，点积的典型波动幅度也可能增大。较大的分数差容易使 softmax 接近饱和：一个权重接近 $1$，其余权重接近 $0$，此时权重对分数的导数变小，经过 softmax 传回打分网络的梯度也容易变小。

缩放点积用 $\sqrt{d_k}$ 调整分数尺度，缓解维度增大带来的这一问题：[Vaswani et al., §3.2.1](https://arxiv.org/html/1706.03762v7#S3.SS2.SSS1)

$$
\boxed{\operatorname{Attention}(Q,K,V)
=\operatorname{softmax}_{\mathrm{row}}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V.}
$$

> [!note]- 推导：为什么是 $\sqrt{d_k}$？
> 假设 $q,k$ 的各分量彼此独立，均值为 $0$、方差为 $1$。对 $u_r=q_rk_r$：
> $$
> \mathbb E[u_r]=0,\qquad
> \operatorname{Var}(u_r)=\mathbb E[q_r^2]\mathbb E[k_r^2]=1.
> $$
> 不同乘积项的协方差为零，因此：
> $$
> \operatorname{Var}(q^\top k)=\operatorname{Var}\left(\sum_{r=1}^{d_k}u_r\right)=d_k.
> $$
> 点积的标准差是 $\sqrt{d_k}$，除以它后方差变为 $1$。这给出了按维度缩放的依据。
>
> 训练动机可以从 softmax 的导数看出：
> $$
> \frac{\partial a_i}{\partial s_j}=a_i(\delta_{ij}-a_j).
> $$
> 当一项权重接近 $1$、其余项接近 $0$ 时，这些导数都接近零。这里的独立性与单位方差是假设，用于解释缩放因子的来源；实际训练中的 Q/K 不必严格满足它们，缩放也不保证权重始终分散。

> [!note]- 打分函数的其他选择
> 除点积外，也可以用可学习的双线性形式 $q^\top Wk$，或加性打分：
> $$
> s(q,k)=w_a^\top\tanh(U_q q+U_k k+b_a).
> $$
> 加性打分先把 query 与 key 映射到同一个隐藏空间，再输出一个标量。更换打分函数后，softmax 与 value 加权汇聚的过程仍然相同。

### 4.2 Mask：限定可读取的范围

有些位置不应参与读取，例如批处理中用于补齐长度的 padding。可以在 softmax 之前加入 mask：

$$
M_{ij}=\begin{cases}0,&\text{允许 query }i\text{ 读取位置 }j,\\-\infty,&\text{禁止读取},\end{cases}
$$

$$
A=\operatorname{softmax}_{\mathrm{row}}\left(\frac{QK^\top}{\sqrt{d_k}}+M\right).
$$

被屏蔽位置的指数值为零，其余位置在允许的范围内归一化。每个参与计算的 query 应至少有一个可读取位置。

在自回归 self-attention 中，还可以用 causal mask 将可见范围限制为当前及之前的输入位置。

> [!example]- 手算：一个候选被屏蔽后，权重怎样变化？
> 沿用第 $2.4$ 节的例子，本例仍使用未缩放点积，以便单独观察 mask 的作用。三个分数为 $(\ln2,0,\ln2)$，对应 values 为 $(2,0)^\top,(0,2)^\top,(1,1)^\top$。
>
> 屏蔽第三个候选后：
> $$
> S+M=(\ln2,0,-\infty),\qquad A=(2/3,1/3,0),\qquad
> c=(4/3,2/3)^\top.
> $$
> 如果只将第三个 value 设为零，权重仍为 $(0.4,0.2,0.4)$，结果会是 $(0.8,0.4)^\top$。区别来自第三个候选是否仍然参与 softmax 的分母。

## 5. 训练：用正确目标序列学会读取

第 $3.1$ 节给出了一步预测的前向计算。本章把这些步骤串成一次训练：给定源句和正确译文，逐步计算预测分布，将预测误差反向传播到整个模型。

以下沿用第 $3.1$ 节的 **RNN Encoder–Decoder + Cross-Attention**。用 $y_t^*$ 表示真实目标词，目标序列 $y_{1:m}^*$ 包含末尾的 `<EOS>`；令 $y_0^*=\texttt{<BOS>}$。

### 5.1 准备输入和答案：目标序列错开一位

仍以“她把书放在桌上”及其译文为例。为便于展示，英文按词切分，模型需要学习以下八步预测：

| 步骤 $t$ | Decoder 输入 $y_{t-1}^*$ | 本步监督目标 $y_t^*$ |
| --- | --- | --- |
| $1$ | `<BOS>` | `She` |
| $2$ | `She` | `put` |
| $3$ | `put` | `the` |
| $4$ | `the` | `book` |
| $5$ | `book` | `on` |
| $6$ | `on` | `the` |
| $7$ | `the` | `table` |
| $8$ | `table` | `<EOS>` |

这就是 target shifting：Decoder 的输入从 `<BOS>` 开始，监督目标从第一个真实词开始，两列错开一位。`<EOS>` 也贡献一项训练损失，用来学习何时结束。

训练时，每一步使用真实的前一个词作为输入，称为 **teacher forcing**。例如第 $3$ 步即使把 `the` 预测成了 `a`，第 $4$ 步仍输入真实的 `the`。当前答案 `book` 用于评价第 $4$ 步的预测，并在第 $5$ 步成为输入。

### 5.2 前向计算：真实前缀产生 Query，再读取源句

先编码源句一次，保存 $h_1,\ldots,h_n$，计算所有 keys/values，并初始化 $s_0$。将源表示按行堆成矩阵 $H$，即第 $i$ 行为 $h_i^\top$，就有 $K=HW_K$、$V=HW_V$。随后每个目标步骤执行相同的计算：

$$
\begin{aligned}
s_t&=\operatorname{RNN}_{\mathrm{dec}}\bigl(s_{t-1},\operatorname{Embed}(y_{t-1}^*)\bigr),\\
q_t&=W_Q^\top s_t,\\
c_t&=\sum_{i=1}^n a_{t,i}v_i,\\
\ell_t&=W_U^\top[s_t;c_t]+b_U,\qquad p_t=\operatorname{softmax}(\ell_t).
\end{aligned}
$$

其中 $a_{t,:}$ 由 $q_t$ 与源 keys 的匹配分数归一化得到，$\ell_t$ 是目标词表上的 logits。用 $\theta$ 统称模型参数，此时预测分布的条件是：

$$
p_t(w)=P_\theta(y_t=w\mid y_{<t}^*,x_{1:n}).
$$

例如，第 $4$ 步的状态由真实前缀 `She put the` 形成，query 据此读取源句，得到用于预测 `book` 的 context。模型会自行学习读取比例，训练数据只需提供源句与正确译文。

**完整源句在所有目标步骤中都可读取。** 批处理中要屏蔽源端 padding；目标端的因果性则由 Decoder 每步只读取前一个目标词、状态沿时间传递来保证。

### 5.3 计算 Loss：评价词表预测，并区分两种 Mask

每一步取真实目标词的负对数概率，再对整句求和：

$$
\begin{aligned}
J_t&=-\log p_t(y_t^*),\\
J&=\sum_{t=1}^m J_t
=-\sum_{t=1}^m\log P_\theta(y_t^*\mid y_{<t}^*,x_{1:n}).
\end{aligned}
$$

若第 $4$ 步给 `book` 的概率为 $0.2$，则该步损失为 $-\ln0.2\approx1.61$；概率提高到 $0.8$ 后，损失降为约 $0.22$。这里衡量的是目标词表中的正确词概率。

批量训练时，不同译文可能需要补齐长度。常见做法是只对有效目标位置取平均：

$$
J_{\mathrm{batch}}
=-\frac{\sum_{b,t}r_{b,t}\log p_{b,t}(y_{b,t}^*)}
{\sum_{b,t}r_{b,t}},
$$

其中 $b$ 是样本索引，$r_{b,t}=1$ 表示有效目标词，包括 `<EOS>`；目标 padding 的 $r_{b,t}=0$。两种 mask 的职责不同：

| Mask | 作用位置 | 解决的问题 |
| --- | --- | --- |
| 源端 attention padding mask | 匹配分数进入 softmax 之前 | 读取权重只分配给有效源位置 |
| 目标端 loss mask | 汇总各步损失时 | 训练目标只包含有效目标词 |

### 5.4 反向传播：翻译误差怎样教会 Attention 匹配？

从 $J_t$ 沿计算图反向求导，梯度先经过输出层传到 $s_t$ 和 $c_t$。经过 context 的梯度又分成两条路径：

- **内容路径：**经过加权和传到 $v_i$，更新 $W_V$ 和生成源表示的 Encoder。
- **匹配路径：**经过 $a_{t,i}$、softmax 和匹配分数传到 $q_t,k_i$，更新 $W_Q,W_K$ 以及 Decoder、Encoder。

Decoder 的递归状态还会把梯度传到更早的目标步骤。因此一次反向传播可以共同训练词嵌入、Encoder、Bridge、Decoder、Q/K/V 投影和输出层。

**标准训练不要求给出“每个目标词应该关注哪个源词”的标签。** 读取方式影响最终词概率，翻译损失就能为读取规则提供学习信号。同一份源 K/V 被多个目标步骤使用，这些使用位置的梯度会累加回它们；复用前向结果时仍需保留训练计算图。

> [!note]- 推导：损失怎样调整某个候选的分数？
> 考虑一次读取 $c=\sum_i a_i v_i$，其中 $a=\operatorname{softmax}(s)$。记 $g=\nabla_cJ$，则：
> $$
> \frac{\partial J}{\partial a_i}=g^\top v_i,\qquad
> \frac{\partial a_j}{\partial s_i}=a_j(\delta_{ij}-a_i).
> $$
> 链式法则给出：
> $$
> \begin{aligned}
> \frac{\partial J}{\partial s_i}
> &=\sum_j(g^\top v_j)a_j(\delta_{ij}-a_i)\\
> &=a_i g^\top v_i-a_i g^\top\sum_j a_jv_j\\
> &=\boxed{a_i g^\top(v_i-c)}.
> \end{aligned}
> $$
> 分数怎样调整，取决于该 value 相对当前混合结果的差异，以及下游希望输出改变的方向。经过 value 直接路径的梯度为 $\nabla_{v_i}J=a_i g$。

### 5.5 一次参数更新：前向、汇总损失、反向、更新

将第 $3.1$ 节的一步计算记为 `DecodeStep`：输入前一个 token、旧状态和源 K/V，返回新状态、词表 logits 及读取权重。下面是单样本、无 padding、全程 teacher forcing 的流程伪代码：

```text
使用训练模式，开启梯度记录
清空模型参数的旧梯度
H = Encoder(x)
K = H W_K，V = H W_V
s = Bridge(h_n)
prev = <BOS>
loss = 0

对 t = 1, ..., m：
    s, logits, weights = DecodeStep(prev, s, K, V)
    loss += CrossEntropy(logits, y_star[t])
    prev = y_star[t]

loss = loss / m
对 loss 反向传播
优化器更新模型参数
```

伪代码中的 `CrossEntropy` 对应 [PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)：接收未归一化的 logits，内部计算真实目标词的负对数概率。一次前向中的所有目标步骤使用同一组模型参数，汇总损失后再进行这次参数更新。参数更新后，下次前向会重新生成表示和读取权重。[PyTorch 训练示例](https://docs.pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html#training-the-model)

已知完整目标序列使每个位置的输入和答案都已确定；**RNN 的 $s_t$ 仍依赖 $s_{t-1}$，因此 teacher forcing 不会消除状态计算的时间依赖。** 对于本文不把 context 反馈进状态的简化结构，可以在得到所有状态后批量计算 Attention，但状态之间的递归依赖仍然存在。

## 6. 推理：用已经生成的前缀逐步读取

实际翻译时，模型只收到源句。记它自行生成的目标词为 $\hat y_t$，并令 $\hat y_0=\texttt{<BOS>}$。推理继续使用训练好的计算规则，区别在于下一步输入来自模型刚生成的词。

### 6.1 初始化：编码源句，准备可以复用的 K/V

对当前源句计算 $H$、$K$、$V$ 和 $s_0$，然后从 `<BOS>` 开始。一次译文生成过程中，模型参数保持固定，这组源表示也保持固定。

| 量 | 一次生成过程中的变化 |
| --- | --- |
| 模型参数 $W_Q,W_K,W_V$ 等 | 使用训练后的数值 |
| 源表示 $H$ 与源 $K,V$ | 编码当前源句后复用 |
| Decoder 状态 $s_t$ 与 query $q_t$ | 随生成前缀逐步更新 |
| 读取权重 $a_{t,:}$ 与 context $c_t$ | 每一步重新计算 |
| 词表分布 $p_t$ 与生成词 $\hat y_t$ | 每一步产生新的结果 |

这里复用的是源句的 K/V。即使源句没有变化，新的 query 也可能产生不同的权重和 context。

### 6.2 每一步：更新状态、读取源句、选择下一个词

当前输入改为前一步生成的 $\hat y_{t-1}$：

$$
s_t=\operatorname{RNN}_{\mathrm{dec}}\bigl(s_{t-1},\operatorname{Embed}(\hat y_{t-1})\bigr).
$$

接着按相同的 Q/K/V 匹配和汇聚过程计算 $c_t$，得到：

$$
p_t(w)=P_\theta(y_t=w\mid\hat y_{<t},x_{1:n}).
$$

最简单的 greedy decoding 每次选择概率最大的目标词：

$$
\hat y_t=\operatorname*{arg\,max}_{w\in\mathcal V_{\mathrm{tgt}}}p_t(w).
$$

下表展示一个恰好生成正确译文前四个词的过程；它是计算流程示例，实际输出取决于训练后的模型：

| 步骤 | 已生成前缀 | 本步送入 Decoder | 本步读取 | 本步生成 |
| --- | --- | --- | --- | --- |
| $1$ | 空 | `<BOS>` | $q_1$ 查询源 K/V，得到 $c_1$ | `She` |
| $2$ | `She` | `She` | $q_2$ 查询同一组 K/V，得到 $c_2$ | `put` |
| $3$ | `She put` | `put` | $q_3$ 查询同一组 K/V，得到 $c_3$ | `the` |
| $4$ | `She put the` | `the` | $q_4$ 查询同一组 K/V，得到 $c_4$ | `book` |

读到的 context 是一个向量，输出层需要结合它与 Decoder 状态形成词表分布，再选择目标词。Attention 权重最大的源位置也不直接决定输出哪个目标词。

### 6.3 自回归循环：把生成词送回模型，直到结束

每次选出 $\hat y_t$ 后，若它是 `<EOS>`，就结束当前样本的生成；否则把它作为下一步输入。还应设置最大生成长度，处理始终没有生成 `<EOS>` 的情况。

```text
使用评估模式，关闭梯度记录
H = Encoder(x)
K = H W_K，V = H W_V
s = Bridge(h_n)
prev = <BOS>
output = []

最多重复 max_new_tokens 次：
    s, logits, weights = DecodeStep(prev, s, K, V)
    token = argmax(logits)
    如果 token 是 <EOS>：结束循环
    把 token 加入 output
    prev = token

返回 output
```

这里直接对 logits 取 argmax，与对其 softmax 概率取 argmax 得到的结果相同。生成时使用固定参数执行前向计算，不进行损失反向传播或参数更新；每一步仍要计算新的 Attention 权重。[PyTorch 生成示例](https://docs.pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html#evaluation)

在 PyTorch 中，`model.eval()` 切换 Dropout 等模块的行为，`torch.no_grad()` 关闭梯度记录，两者作用不同。[PyTorch Autograd 文档](https://docs.pytorch.org/docs/stable/notes/autograd.html#evaluation-mode-nn-module-eval) 批量生成时，每个样本还需单独记录是否完成；已生成 `<EOS>` 的样本停止追加 token，其余样本可以继续。

若用 sampling，可以按 $p_t$ 采样下一个词；若用 beam search，需要为每条候选前缀维护各自的 Decoder 状态、累计分数和 query。不同候选可以共享源 K/V，但会形成各自的 Attention 权重。选择策略沿用 [[04-Seq2Seq|Seq2Seq]] 中的解码方法。

### 6.4 训练与推理：同一读取规则，不同的前缀来源

| 环节 | Teacher forcing 训练 | 自回归生成 |
| --- | --- | --- |
| 已知信息 | 源句与真实目标序列 | 源句与当前生成前缀 |
| 第 $t$ 步输入 | 真实的 $y_{t-1}^*$ | 已生成的 $\hat y_{t-1}$ |
| Query 的依据 | 真实前缀形成的状态 | 生成前缀形成的状态 |
| 源端读取 | 对有效源位置重新计算权重 | 对有效源位置重新计算权重 |
| 本步词表分布的用途 | 计算真实目标词的损失 | 选择下一个词 |
| 参数更新 | 汇总损失后反向传播并更新 | 参数保持固定 |
| 结束依据 | 处理完真实目标序列，包括 `<EOS>` | 生成 `<EOS>` 或达到长度上限 |

例如，模型若在第 $3$ 步生成了 `a`，推理的第 $4$ 步就会读入 `a`；teacher forcing 训练的第 $4$ 步则仍读入 `the`。不同前缀会改变 $s_t$，进一步改变 query、源端读取权重和后续预测。

因此，Attention 提供了重新访问源句的能力，但生成错误仍可能沿前缀传播。评估时，可以分别观察真实前缀条件下的验证损失和自由生成的译文质量。

### 6.5 迁移到 Self-Attention：区分训练并行与生成依赖

上面两章具体讲的是带 Cross-Attention 的 RNN Seq2Seq。换成自回归 Transformer 后，训练和推理仍使用不同来源的目标前缀，但表示的计算方式发生变化：

- **训练时：**右移后的真实目标输入已知，同一层各目标位置的 Q/K/V 可以一起计算；causal mask 限制每个位置只读取当前及之前的输入位置。各层仍依次计算。
- **生成时：**已有 prompt 可以批量处理，后续 token 需要逐个选出并反馈。实现中可缓存各层的历史 Self-Attention K/V，并随新 token 追加，参见 [KV Cache 说明](https://huggingface.co/docs/transformers/en/cache_explanation)。Encoder–Decoder Cross-Attention 的源 K/V 则来自固定的源表示。

这些机制将在下一篇展开。若 Self-Attention 用于编码一段完整输入，例如 Encoder 的双向表示，训练和推理都可以读取整段有效输入；这里的 causal mask 要求来自自回归预测任务。

## 7. 最小实现：核对一次 Attention 的计算

前两章用 `DecodeStep` 串起了训练和生成。本节把其中的 Attention 计算写成最小函数：接收 Q/K/V，返回 context 和读取权重；Decoder 再用 context 与自身状态预测目标词。

下面的代码对应第 $4$ 节的矩阵公式。`Q`、`K`、`V` 已经是投影后的表示；`key_valid` 指定每个样本中哪些 key/value 可读取，在该样本的所有 queries 之间共享。这个最小例子实现 padding mask，causal mask 则还需要按 query 位置限制可见范围。

先用 `scaled=False` 重现第 $2.4$ 节的手算，再屏蔽第三个候选，核对第 $4.2$ 节的结果。

> [!example]- 可运行的 PyTorch 代码
> ```python
> import math
> import torch
>
> def attention(Q, K, V, key_valid, *, scaled=True):
>     # Q: [B, Nq, dk], K: [B, Nk, dk], V: [B, Nk, dv]
>     # key_valid: [B, Nk]，True 表示可读取
>     if not bool(key_valid.any(dim=-1).all()):
>         raise ValueError("每个样本至少需要一个有效候选")
>     scores = Q @ K.transpose(-2, -1)
>     if scaled:
>         scores = scores / math.sqrt(Q.shape[-1])
>     scores = scores.masked_fill(~key_valid[:, None, :], -torch.inf)
>     weights = scores.softmax(dim=-1)
>     return weights @ V, weights
>
> dtype = torch.float64
> Q = torch.tensor([[[math.log(2), 0.], [0., math.log(2)]]], dtype=dtype)
> K = torch.tensor([[[1., 0.], [0., 1.], [1., 1.]]], dtype=dtype)
> V = torch.tensor([[[2., 0.], [0., 2.], [1., 1.]]], dtype=dtype)
> valid = torch.tensor([[True, True, True]])
>
> C, A = attention(Q, K, V, valid, scaled=False)
> expected = torch.tensor([[[1.2, .8], [.8, 1.2]]], dtype=dtype)
> assert torch.allclose(C, expected)
> print("weights:", A)
> print("output:", C)
>
> valid = torch.tensor([[True, True, False]])
> C, A = attention(Q, K, V, valid, scaled=False)
> expected = torch.tensor([[[4/3, 2/3], [2/3, 4/3]]], dtype=dtype)
> assert torch.allclose(C, expected)
> assert bool((A[..., 2] == 0).all())
> print("masked output:", C)
> ```
>
> 两次查询分别得到 $(1.2,0.8)$ 与 $(0.8,1.2)$。屏蔽第三个候选后，分别得到 $(4/3,2/3)$ 与 $(2/3,4/3)$。将 `scaled` 改成 `True`，就会先调整点积分数的尺度，再计算权重。

## 8. 从 Attention 到 Transformer：还需要解决什么？

到这里，我们已经知道一次 Attention 怎样计算，以及它怎样参与训练和生成。接下来的问题是：**如果希望用 Self-Attention 来构建整个序列模型，还需要补上哪些能力？** 本章从前面的 RNN Seq2Seq 出发，为下一篇 Transformer 建立动机。

### 8.1 序列表示：能否用 Self-Attention 替代 RNN 的逐步传递？

前面的模型仍由 Encoder RNN 生成源表示 $h_i$，由 Decoder RNN 根据目标前缀更新状态 $s_t$。Cross-Attention 让 Decoder 能在每一步重新读取源句，但这些源表示和查询状态仍依赖 RNN 的递归计算。

第 $3.2$ 节的 Self-Attention 提供了另一种交互方式：让每个位置从自己的输入产生 query，直接读取其他位置的内容，再用读取结果形成新的表示。对于一层已知的输入，各位置的 Q/K/V 可以一起计算，相距很远的两个位置也可以在一次读取中建立联系。

如果以这种交互方式组织网络，就可以进一步构建 Transformer。生成时仍需逐个选择后续 token；去掉 RNN 改变的是层内形成表示的方式，第 $6.5$ 节已说明它对训练与推理计算的影响。[Vaswani et al.](https://arxiv.org/abs/1706.03762)

### 8.2 多种关系：一个位置需要几份不同的读取结果？

回到第 $3.2$ 节的句子“The animal was tired, so it rested”。为了形成 `it` 的表示，模型可能需要从 `animal` 获取实体信息，也需要从 `tired` 获取状态信息。

单头 Attention 已经可以同时读取这两个位置：

$$
c_i=\sum_j a_{ij}v_j.
$$

它对当前 query 使用一行权重，返回一份混合结果。若希望按不同的匹配规则分别读取内容，并保留多份结果供后续组合，就可以引入多头注意力：

$$
c_i^{(1)}=\sum_j a_{ij}^{(1)}v_j^{(1)},\qquad
c_i^{(2)}=\sum_j a_{ij}^{(2)}v_j^{(2)}.
$$

每个头学习各自的 Q/K/V 投影，因此可以形成不同的读取权重和内容表示。各头的输出随后拼接，再经过输出投影。这里的实体与状态只是说明“为什么可能需要不同的读取方式”；各个头在训练中实际学到什么，由任务损失决定。

**多头的动机是提供多套可学习的读取方式。** 至于一套权重怎样实现近似查表、怎样平均两个 values，可以通过手工构造 query 来分析；这些是进一步理解公式的练习，放在 [[#附录 A：复制、平均与混合稳定性（选读）|附录 A]]。

### 8.3 位置关系：去掉 RNN 后，词序从哪里来？

前面的 RNN 按顺序读取 token，因此 $h_i$ 和 $s_t$ 的计算过程已经包含序列顺序。改用 Self-Attention 后，如果输入只有 token 的内容表示，就需要重新考虑怎样提供位置信息。

例如，“狗 咬 人”和“人 咬 狗”包含相同的三个词，但动作发出者不同。如果只有词嵌入、所有位置共享投影、且所有位置都能互相读取，那么两句话中“狗”的 query 面对的是同一组 keys/values。它读回的结果相同，只是出现在输出序列的不同行。

形式上，输入按排列矩阵 $P$ 重排，输出也会按相同方式重排：

$$
\operatorname{SA}(PX)=P\operatorname{SA}(X).
$$

这称为**排列等变性**。在上述条件下，内容匹配本身没有说明某个词位于哪个位置、两个词相距多远。为此，可以把位置表示加入输入，或让匹配过程依赖相对位置；下一篇将介绍具体方法。完整的等变性证明放在 [[#附录 B：Self-Attention 的排列等变性（证明）|附录 B]]。

这里的条件很关键：RNN 产生的输入表示可以已经携带顺序信息，causal mask 也会让不同位置具有不同的可见范围。上面的等变性结论讨论的是无位置项、无 mask 的纯内容 Self-Attention。

### 8.4 完整计算层：读取之后怎样加工表示？

Attention 完成了位置之间的信息汇聚。得到每个位置的读取结果后，网络还需要加工它的特征，并把多个计算层有效地堆叠起来。Transformer 因此进一步使用逐位置的前馈网络、残差连接与归一化。

下一篇 [[06-transformer|Transformer]] 将沿着这些问题展开：用 Self-Attention 建立位置之间的联系，用多头提供多种读取方式，用位置信息表达顺序，再把这些操作组织成可训练的完整网络。

## 附录 A：复制、平均与混合稳定性（选读）

这组题围绕一个逐步加深的问题展开：**一次 Attention 能取回一个 value；如果希望同时取回两个，并且每次都按一半一半的比例混合，需要满足什么条件？**

下面参考 [[dive-to-attention|dive-to-attention]] 的讲解顺序，沿着“希望得到的输出 → 所需权重 → 怎样产生这些分数 → key 变化后会发生什么”展开。A.1、A.2 先分析固定 keys，A.3 引入混合比例问题，A.4 补充概率知识，A.5、A.6 比较两种噪声，最后在 A.7 连接到多头注意力。

本附录统一使用**未缩放点积**，把向量写成列向量：

$$
s_i=q^\top k_i,\qquad
a_i=\frac{e^{s_i}}{\sum_{j=1}^n e^{s_j}},\qquad
c=\sum_{i=1}^n a_i v_i.
$$

其中 $a_i$ 始终表示 attention 权重。原题用 $\alpha$ 表示噪声方差，下面改用 $\eta$，避免把噪声与权重混在一起。所有 values 都视为固定向量；随机实验改变的是 keys，query 按题目给定的规则构造。

### A.1 取回一个 Value：为什么一个显著高分就够了？

**原题 1(a)：Copying in attention** · [[a3.pdf#page=2|PDF 第 2 页]]

![[_assets/images/a3-1a-copying.png|900]]

#### 希望得到什么输出？

希望输出 $c$ 接近某个指定的 $v_j$。因为输出是加权和，只要：

$$
a_j\approx1,\qquad a_i\approx0\quad(i\ne j),
$$

就有：

$$
c=a_jv_j+\sum_{i\ne j}a_i v_i\approx v_j.
$$

这里的“复制”就是把一个 value 向量近似取回到输出。Key 决定读取权重，对应的 value 提供内容。

#### 怎样让一个权重接近 $1$？

把 softmax 的分子、分母同时除以 $e^{s_j}$：

$$
a_j
=\frac{e^{s_j}}{e^{s_j}+\sum_{i\ne j}e^{s_i}}
=\frac{1}{1+\sum_{i\ne j}e^{s_i-s_j}}.
$$

若 $s_j$ 比每个其他分数都高很多，那么 $s_i-s_j$ 是较大的负数，各个指数项就接近零，因而 $a_j$ 接近 $1$。**关键是目标分数相对其他分数的优势。** 如果所有分数一起增大，权重并不会因此改变。

点积同时取决于方向和模长，因此“目标分数显著最高”比“query 与目标 key 的夹角最小”更准确：

$$
q^\top k_j=\|q\|\,\|k_j\|\cos\theta_j.
$$

#### 分数领先多少才够？

设有 $n\ge2$ 个候选，目标分数至少领先其他分数 $\gamma$，即 $s_j-s_i\ge\gamma$。于是：

$$
a_j\ge\frac{1}{1+(n-1)e^{-\gamma}}.
$$

若希望 $a_j\ge1-\varepsilon$，其中 $0<\varepsilon<1$，一个充分条件是：

$$
\gamma\ge\log\frac{(n-1)(1-\varepsilon)}{\varepsilon}.
$$

例如，有 $4$ 个候选，希望目标权重至少达到 $0.99$，只需保证分数优势至少为 $\ln297\approx5.69$。候选数越多，需要压低的指数项越多，对分数优势的要求也会相应提高。

对于固定的 values，输出误差可以进一步控制：

$$
\begin{aligned}
\|c-v_j\|
&=\left\|\sum_{i\ne j}a_i(v_i-v_j)\right\|\\
&\le(1-a_j)\max_{i\ne j}\|v_i-v_j\|.
\end{aligned}
$$

因此，目标权重越接近 $1$，读取结果就越接近目标 value。下一问把目标从“取回一个”改为“同时取回两个并求平均”。

### A.2 平均两个 Values：为什么 Query 要取两个 Key 的和？

**原题 1(b)：An average of two** · [[a3.pdf#page=2|PDF 第 2 页]]

![[_assets/images/a3-1b-average-two.png|900]]

#### 把输出目标转成权重目标

这次希望：

$$
c\approx\bar v,\qquad \bar v=\frac12(v_a+v_b),\qquad a\ne b.
$$

一种直接实现它的方式是，让两个目标各占一半权重，其余位置的权重接近零：

$$
a_a\approx a_b\approx\frac12,\qquad
a_i\approx0\quad(i\ne a,b).
$$

这要求分数满足两件事：**两个目标都胜过其他候选，同时它们彼此的分数相等或足够接近。**

#### 利用正交性构造 Query

本题假设 keys 是两两正交的单位向量：

$$
k_i^\top k_j=
\begin{cases}
1,&i=j,\\
0,&i\ne j.
\end{cases}
$$

要容纳 $n$ 个这样的 keys，匹配空间维度至少为 $n$。在这组理想条件下，取：

$$
q=\lambda(k_a+k_b),\qquad \lambda>0.
$$

$k_a+k_b$ 同时包含两个目标方向。由于两个 keys 的模长相同且互相正交，query 与它们的点积相同；它与其余正交 keys 的点积为零。展开计算：

$$
\begin{aligned}
s_a&=k_a^\top q
=\lambda(k_a^\top k_a+k_a^\top k_b)
=\lambda(1+0)=\lambda,\\
s_b&=k_b^\top q
=\lambda(k_b^\top k_a+k_b^\top k_b)
=\lambda(0+1)=\lambda,\\
s_i&=k_i^\top q
=\lambda(k_i^\top k_a+k_i^\top k_b)
=0\quad(i\ne a,b).
\end{aligned}
$$

因此，$\lambda$ 控制两个目标相对其他候选的分数优势，而求和方向保证两个目标分数相等。

#### 从分数算到权重和输出

两个目标的指数值都是 $e^\lambda$，其余 $n-2$ 个候选的指数值都是 $1$，所以：

$$
a_a=a_b=\frac{e^\lambda}{2e^\lambda+n-2},\qquad
a_i=\frac{1}{2e^\lambda+n-2}\quad(i\ne a,b).
$$

例如，取 $4$ 个候选：

| $\lambda$ | $a_a$ | $a_b$ | 每个其他候选的权重 |
| --- | --- | --- | --- |
| $1$ | $0.3655$ | $0.3655$ | $0.1345$ |
| $4$ | $0.4910$ | $0.4910$ | $0.0090$ |

随着 $\lambda\to\infty$，两个目标仍保持平衡，其余候选的总权重趋于零：

$$
a_a,a_b\longrightarrow\frac12,\qquad
c\longrightarrow\frac12(v_a+v_b).
$$

若只有两个候选，两个分数相等就能精确平均，不需要再增大 $\lambda$。在相同的正交假设下，要平均一个含 $r$ 个位置的集合 $\mathcal I$，也可以构造 $q=\lambda\sum_{i\in\mathcal I}k_i$。

到这里，单头 Attention 已经能读取多个位置。接下来要检查的是：**当 keys 不再恰好位于这些理想位置时，原来的混合比例还能否保持？**

### A.3 从固定 Keys 到随机 Keys：为什么要关注两个分数之差？

前一问的构造同时满足“目标分数高”和“两个目标分数相等”。Key 的变化可能保留第一点，却破坏第二点。

将两个目标的分数差记为：

$$
\Delta=s_a-s_b.
$$

它们的权重比为：

$$
\frac{a_a}{a_b}=e^\Delta.
$$

即使还有其他候选，$a$ 在这两个目标内部所占的份额也恰好等于：

$$
\frac{a_a}{a_a+a_b}
=\frac{e^{s_a}}{e^{s_a}+e^{s_b}}
=\frac{1}{1+e^{-\Delta}}
=\sigma(\Delta).
$$

这里 $\sigma$ 是 sigmoid 函数。它把分数差转换成两个目标之间的分配比例：

| 分数差 $\Delta$ | $a$ 在两目标内部的份额 | $b$ 在两目标内部的份额 |
| --- | --- | --- |
| $0$ | $50\%$ | $50\%$ |
| $2$ | 约 $88\%$ | 约 $12\%$ |
| $-2$ | 约 $12\%$ | 约 $88\%$ |

当其他候选的权重已经很小时，$a_a+a_b\approx1$，因此：

$$
c\approx\sigma(\Delta)v_a+[1-\sigma(\Delta)]v_b.
$$

例如，两个目标分数从 $(10,10)$ 变成 $(10,8)$，可能仍然远高于其他候选，但混合比例已经明显偏离一半一半。**选中这两个位置之后，还要让它们的分数差保持接近零。**

接下来的题用 $k_i=\mu_i+\epsilon_i$ 描述 key 的变化：$\mu_i$ 是已知的理想位置，$\epsilon_i$ 是本次采样的偏移。Query 根据均值和噪声尺度构造，不随本次采样出的具体 keys 重新调整。这样就能检验同一种读取规则在不同样本上的表现。

为了区分“小幅偏移”和“沿一个方向持续波动”，需要先理解协方差矩阵。

### A.4 数学准备：协方差怎样描述 Key 的波动？

#### 从一个变量的方差，到两个变量的协方差

对标量随机变量 $U$，$U-\mathbb E[U]$ 表示某次取值偏离平均值多少，方差衡量这种偏移的平方平均：

$$
\operatorname{Var}(U)=\mathbb E[(U-\mathbb E[U])^2].
$$

如果还要描述 $U$ 与另一个变量 $W$ 怎样一起变化，可以计算协方差：

$$
\operatorname{Cov}(U,W)
=\mathbb E[(U-\mathbb E[U])(W-\mathbb E[W])].
$$

两者经常同时高于或低于各自均值时，偏差乘积倾向于为正；一个偏高、另一个偏低时，乘积倾向于为负。令 $W=U$，就得到 $\operatorname{Cov}(U,U)=\operatorname{Var}(U)$。

#### 向量有多个坐标，因此需要一张矩阵

若二维随机向量 $k=(U,W)^\top$，需要同时记录两个坐标各自的方差，以及它们的协方差：

$$
\Sigma=
\begin{bmatrix}
\operatorname{Var}(U)&\operatorname{Cov}(U,W)\\
\operatorname{Cov}(W,U)&\operatorname{Var}(W)
\end{bmatrix}.
$$

一般地，若均值为 $\mu=\mathbb E[k]$，则：

$$
\Sigma=\mathbb E[(k-\mu)(k-\mu)^\top].
$$

对角元素记录各坐标自身的波动，非对角元素记录不同坐标的共同变化。对于本题中的高斯分布，可以把 $\mu$ 看成随机点云的中心，把 $\Sigma$ 看成描述点云伸展方向和尺度的矩阵。

#### 题目中的两种协方差分别是什么意思？

第一种是 $\Sigma=\eta I$。任意单位方向上的投影方差都是 $\eta$；当 $\eta\to0$ 时，key 的各个方向都逐渐收缩到均值附近。在二维中，等密度轮廓是逐渐缩小的圆。

第二种是：

$$
\Sigma=\eta I+\frac12\mu_a\mu_a^\top,\qquad \|\mu_a\|=1.
$$

外积 $\mu_a\mu_a^\top$ 给 $\mu_a$ 方向增加波动。取一个具体例子 $\mu_a=(1,0)^\top$：

$$
\mu_a\mu_a^\top
=\begin{bmatrix}1\\0\end{bmatrix}
\begin{bmatrix}1&0\end{bmatrix}
=\begin{bmatrix}1&0\\0&0\end{bmatrix},
$$

因此：

$$
\Sigma=
\begin{bmatrix}
\eta+1/2&0\\
0&\eta
\end{bmatrix}.
$$

即使 $\eta\to0$，横向方差仍接近 $1/2$，只有纵向方差趋于零。点云会变成沿 $\mu_a$ 轴分布的细长形状，而不会收缩成一个点。

#### Key 的波动怎样变成匹配分数的波动？

Attention 最终使用的是标量 $s=q^\top k$。对一个固定 query：

$$
\begin{aligned}
s-\mathbb E[s]&=q^\top(k-\mu),\\
\operatorname{Var}(s)
&=\mathbb E[q^\top(k-\mu)(k-\mu)^\top q]\\
&=q^\top\Sigma q.
\end{aligned}
$$

因此，分数的波动同时取决于 key 的协方差和 query 的方向、模长：

$$
\begin{aligned}
\Sigma=\eta I
&\quad\Longrightarrow\quad
\operatorname{Var}(q^\top k)=\eta\|q\|^2,\\
\Sigma=\eta I+\tfrac12\mu_a\mu_a^\top
&\quad\Longrightarrow\quad
\operatorname{Var}(q^\top k)
=\eta\|q\|^2+\tfrac12(q^\top\mu_a)^2.
\end{aligned}
$$

下面两问就用这两个式子，分析放大 query 后，两个目标的分数差会缩小还是扩大。

### A.5 各向同性小噪声：怎样同时压低其他权重、保持两个目标平衡？

**原题 1(c)(i)：各向同性小扰动** · [[a3.pdf#page=2|PDF 第 2 页]]

![[_assets/images/a3-1c-i-small-noise.png|900]]

#### 把理想 Key 换成均值加噪声

设各 key 独立采样：

$$
k_i=\mu_i+\epsilon_i,\qquad
\epsilon_i\sim\mathcal N(0,\eta I).
$$

各均值 $\mu_i$ 两两正交且为单位向量，候选数、维度及 values 固定，令 $\eta\to0$。原题中的方差 $\alpha$ 对应这里的 $\eta$。

沿用 A.2 的构造思路，但用已知均值代替实际 keys：

$$
q=\lambda(\mu_a+\mu_b).
$$

为了看清噪声影响，记 $\zeta_i=q^\top\epsilon_i$。展开三个类型的分数：

$$
\begin{aligned}
s_a&=q^\top(\mu_a+\epsilon_a)=\lambda+\zeta_a,\\
s_b&=q^\top(\mu_b+\epsilon_b)=\lambda+\zeta_b,\\
s_i&=q^\top(\mu_i+\epsilon_i)=\zeta_i\quad(i\ne a,b).
\end{aligned}
$$

没有噪声时，仍然是两个 $\lambda$ 和其余的零。噪声造成了两个变化：目标与其他候选之间的差距会波动，两个目标原本相等的分数也会出现偏差。

#### 为什么不能只说“把 $\lambda$ 取得很大”？

因为 query 放大时，噪声投影也会放大。由正交性：

$$
\|q\|^2=\lambda^2\|\mu_a+\mu_b\|^2=2\lambda^2.
$$

结合 A.4 的投影方差公式：

$$
\operatorname{Var}(\zeta_i)=\eta\|q\|^2=2\eta\lambda^2,\qquad
\operatorname{Std}(\zeta_i)=\sqrt{2\eta}\,\lambda.
$$

注意 $\eta$ 是**方差**，噪声的标准差按 $\sqrt\eta$ 缩小。两个目标的分数差为：

$$
\Delta=s_a-s_b=\zeta_a-\zeta_b.
$$

由于各 key 的噪声独立，差的方差是两项方差之和：

$$
\operatorname{Var}(\Delta)=4\eta\lambda^2,\qquad
\operatorname{Std}(\Delta)=2\lambda\sqrt\eta.
$$

即使目标分数都很高，只要 $\Delta$ 仍有明显波动，A.3 中的 sigmoid 就会让混合比例偏离 $50\%/50\%$。所以要同时照顾两个尺度：

| 想实现的效果 | 对构造的要求 |
| --- | --- |
| 让两个目标逐渐压过其他候选 | 令 $\lambda\to\infty$ |
| 让两个目标的分数差逐渐消失 | 令 $\lambda\sqrt\eta\to0$ |

这些是一个足够的构造条件。它们要求 $\lambda$ 增大，但增长速度慢于 $\eta^{-1/2}$。

#### 一个同时满足两项要求的选择

取：

$$
\lambda=\eta^{-1/4}.
$$

于是：

$$
\lambda\to\infty,\qquad
\lambda\sqrt\eta
=\eta^{-1/4}\eta^{1/2}
=\eta^{1/4}\to0.
$$

例如，$\eta=10^{-8}$ 时，$\lambda=100$。两个目标的平均分数都是 $100$，其他候选的平均分数是 $0$，而两个目标分数差的标准差只有：

$$
2\lambda\sqrt\eta=2\times100\times10^{-4}=0.02.
$$

这个例子展示了两种尺度可以兼顾：目标分数有很大的优势，目标之间的差异却很小。

#### 输出和方差会怎样变化？

随着 $\eta\to0$，每个 $\zeta_i$ 都依概率趋于零，两个目标分数差也趋于零；同时，它们相对其他候选的优势增大。因此：

$$
a_a,a_b\xrightarrow{p}\frac12,\qquad
a_i\xrightarrow{p}0\quad(i\ne a,b).
$$

把此时的输出记为 $c_\eta$，就有：

$$
c_\eta\xrightarrow{p}\bar v=\frac12(v_a+v_b).
$$

“依概率收敛”在这里表示：给定任意固定误差范围，输出落在中点附近这个范围内的概率趋于 $1$。因为所有输出都在固定 values 的有界凸包内，输出的均值趋于 $\bar v$，协方差也趋于零。

这次能够保持稳定，依靠的是 key 噪声持续缩小，并且 query 的放大速度受到控制。下一问保留相同的 query 构造，只改变一个 key 的噪声。

### A.6 沿均值方向持续波动：为什么平均正确，单次读取却不稳定？

**原题 1(c)(ii)：沿 Key 方向的扰动** · [[a3.pdf#page=2|PDF 第 2 页题干]]

![[_assets/images/a3-1c-ii-axis-noise.png|900]]

**Figure 1 与续题** · [[a3.pdf#page=3|PDF 第 3 页]]

![[_assets/images/a3-1c-ii-figure-and-question.png|900]]

#### 改变的只有一个 Key 的协方差

仍让均值两两正交且为单位向量、values 固定，并假设 $v_a\ne v_b$。其余 keys 的协方差都是 $\eta I$，但 $k_a$ 改为：

$$
\Sigma_a=\eta I+\frac12\mu_a\mu_a^\top.
$$

如 A.4 所示，$\eta\to0$ 只会消除各向同性的小噪声，沿 $\mu_a$ 轴的额外方差仍为 $1/2$。可以把这种采样显式写成：

$$
\begin{aligned}
k_a&=\left(1+\frac{z}{\sqrt2}\right)\mu_a+\epsilon_a,\\
k_i&=\mu_i+\epsilon_i\quad(i\ne a),\\
z&\sim\mathcal N(0,1),\qquad
\epsilon_i\sim\mathcal N(0,\eta I).
\end{aligned}
$$

所有随机项相互独立。因为 $z$ 的均值为 $0$、方差为 $1$，随机项 $(z/\sqrt2)\mu_a$ 恰好贡献协方差 $\frac12\mu_a\mu_a^\top$。

忽略逐渐消失的 $\epsilon_a$ 后，$k_a$ 沿 $\mu_a$ 所在轴前后变化。系数 $1+z/\sqrt2$ 可以大于 $1$、小于 $1$，甚至为负；因此“沿轴波动”比“方向始终相同、只有长度改变”更准确。

#### 相同的 Query，现在产生怎样的分数差？

继续取：

$$
q=\lambda(\mu_a+\mu_b),\qquad
\lambda=\eta^{-1/4}.
$$

仍记 $\zeta_i=q^\top\epsilon_i$，则：

$$
\begin{aligned}
s_a&=\lambda\left(1+\frac z{\sqrt2}\right)+\zeta_a,\\
s_b&=\lambda+\zeta_b,\\
s_i&=\zeta_i\quad(i\ne a,b).
\end{aligned}
$$

两个目标的分数差变成：

$$
\boxed{\Delta=s_a-s_b
=\frac{\lambda z}{\sqrt2}+\zeta_a-\zeta_b.}
$$

上一问只有后面两个小噪声项，它们随 $\eta\to0$ 消失。这一问多出的 $\lambda z/\sqrt2$ 却随 query 的放大而增大：

$$
\operatorname{Var}(\Delta)
=\frac{\lambda^2}{2}+4\eta\lambda^2.
$$

当 $\lambda=\eta^{-1/4}$ 时，第二项趋于零，第一项趋于无穷。**目标之间的随机分数差没有被压小，反而越来越大。**

与此同时，$s_b$ 依概率趋于正无穷，其余非目标分数趋于零，因此 $a_a+a_b$ 仍趋于 $1$。模型仍主要从 $a,b$ 两个位置读取，但它们之间的份额发生了变化。

#### Softmax 怎样把分数差变成两端的选择？

根据 A.3：

$$
\frac{a_a}{a_a+a_b}
=\sigma(\Delta)
\approx\sigma\left(\frac{\lambda z}{\sqrt2}\right).
$$

下面忽略 $\zeta_a,\zeta_b$，用几组数值看两目标内部的份额：

| $\lambda$ | 本次 $z$ | 分数差 $\lambda z/\sqrt2$ | $a$ 的内部份额      |
| --------- | ------ | ---------------------- | -------------- |
| $10$      | $0.2$  | 约 $1.41$               | 约 $80.4\%$     |
| $10$      | $−0.2$ | 约 $−1.41$              | 约 $19.6\%$     |
| $100$     | $0.2$  | 约 $14.14$              | 大于 $99.9999\%$ |
| $100$     | $−0.2$ | 约 $−14.14$             | 小于 $0.0001\%$  |

当两个目标已经占据几乎全部权重时，这些比例就近似决定了输出：

- 对固定的 $z>0$，随着 $\eta\to0$，$\Delta$ 趋于正无穷，输出趋近 $v_a$。
- 对固定的 $z<0$，$\Delta$ 趋于负无穷，输出趋近 $v_b$。

因此，多次采样后，输出会分别聚集到两个端点附近。中点虽然是希望得到的结果，却没有成为单次输出的集中位置。

#### 为什么期望仍然等于中点？

由于标准正态分布对称，$P(z>0)=P(z<0)=1/2$。将极限分布对应的输出记为 $c_\infty$：

$$
c_\eta\xrightarrow{d}c_\infty,\qquad
c_\infty=
\begin{cases}
v_a,&\text{概率 }1/2,\\
v_b,&\text{概率 }1/2.
\end{cases}
$$

这里 $\xrightarrow{d}$ 表示分布收敛。极限输出的均值为：

$$
\mathbb E[c_\infty]
=\frac12v_a+\frac12v_b
=\bar v.
$$

例如，若 $v_a=(2,0)^\top$、$v_b=(0,2)^\top$，目标中点就是 $(1,1)^\top$。一半输出为 $(2,0)^\top$，另一半为 $(0,2)^\top$，长期平均确实是 $(1,1)^\top$，但这两种单次结果都偏离了中点。

#### 用协方差和均方偏差衡量这种不稳定

记 $r=(v_a-v_b)/2$。极限输出相对中点的偏差分别为 $r$ 和 $-r$，各有一半概率。因此：

$$
\begin{aligned}
\operatorname{Cov}(c_\infty)
&=\frac12rr^\top+\frac12(-r)(-r)^\top\\
&=\frac14(v_a-v_b)(v_a-v_b)^\top.
\end{aligned}
$$

在刚才的二维例子中：

$$
\operatorname{Cov}(c_\infty)
=\begin{bmatrix}1&-1\\-1&1\end{bmatrix}.
$$

对角元素表明两个坐标都有波动，负的非对角元素表明一个坐标升高时，另一个会降低。若只想用一个标量表示偏离中点的大小，可以计算均方偏差：

$$
\mathbb E\|c_\infty-\bar v\|^2
=\frac14\|v_a-v_b\|^2.
$$

二维例子中这个值是 $2$；两个端点距离越远，单次读取相对中点的偏差越大。

以上等式描述的是极限分布。由于有限 $\eta$ 下的输出同样位于固定 values 的有界凸包内，它的一、二阶矩也收敛到上述结果：

$$
\begin{aligned}
\mathbb E[c_\eta]&\longrightarrow\bar v,\\
\operatorname{Cov}(c_\eta)&\longrightarrow
\frac14(v_a-v_b)(v_a-v_b)^\top,\\
\mathbb E\|c_\eta-\bar v\|^2&\longrightarrow
\frac14\|v_a-v_b\|^2>0.
\end{aligned}
$$

两种噪声在同一个 query 构造下的结果可以直接对照：

| 比较项 | A.5：各向同性小噪声 | A.6：额外的轴向波动 |
| --- | --- | --- |
| $\eta\to0$ 后的 key 波动 | 各方向都消失 | $\mu_a$ 轴上的波动保留 |
| 两目标分数差的方差 | $4\eta\lambda^2\to0$ | $\lambda^2/2+4\eta\lambda^2\to\infty$ |
| 单次输出 | 越来越集中在中点附近 | 越来越集中在两个端点附近 |
| 极限均值 | 中点 $\bar v$ | 中点 $\bar v$ |
| 相对中点的均方偏差 | 趋于零 | 趋于非零常数 |

这里始终采用 $\lambda=\eta^{-1/4}$。这组比较说明，评价混合是否稳定，需要同时观察输出的平均位置和单次输出的波动。

### A.7 这些例题怎样连接到多头注意力？

A.2 用一套 softmax 权重实现了平均，但需要两个目标分数保持平衡。A.6 展示了一个具体情形：额外噪声破坏了这种平衡，即使其他候选被压低，输出仍不能稳定接近目标平均。

这为正文第 $8.2$ 节提供了一个设计动机：**把“分别读取内容”和“组合读取结果”分成两步。** 假设两个头分别可靠地取回：

$$
c^{(1)}\approx v_a,\qquad c^{(2)}\approx v_b,
$$

后续线性组合就可以得到：

$$
o=\frac12c^{(1)}+\frac12c^{(2)}
\approx\frac12(v_a+v_b).
$$

此时，一半一半的组合比例由后续线性层实现，每个头的 softmax 可以专注于自己的读取任务。Transformer 的多头注意力为各头提供不同的 $Q/K/V$ 投影，再通过输出投影组合各头结果。

这个解释以“各头能可靠取回各自内容”为前提。前面的随机例题分析的是指定单头构造的敏感性，并没有证明任意多头结构都能抵抗同样的噪声。各头如何建立可靠匹配，仍取决于表示、参数和训练。

## 附录 B：Self-Attention 的排列等变性（证明）

正文第 $8.3$ 节用“狗 咬 人”和“人 咬 狗”说明：只有内容匹配时，同一个词读回的结果会跟着这个词一起换位置。下面逐步证明这个结论，关键是追踪“输入换行”怎样传递到分数、权重和输出。

**原题 2(a)：Permuting the input** · [[a3.pdf#page=4|PDF 第 4 页]]

![[_assets/images/a3-2a-permutation.png|900]]

这里展开原题中 Self-Attention 部分的证明。

### B.1 先明确输入和条件

设输入矩阵 $X$ 按行存放 token 表示。所有位置共享投影矩阵，采用无位置项、无 mask、无 dropout 的 self-attention：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V,
$$

$$
S=QK^\top/\sqrt{d_k},\qquad
A=\operatorname{softmax}_{\mathrm{row}}(S),\qquad
C=AV.
$$

用排列矩阵 $P$ 重排输入行，即 $X'=PX$。排列不会删除或复制位置，因此 $P^\top P=I$。我们要证明，重新计算的输出恰好是 $C'=PC$。

### B.2 输入换行，Q/K/V 也一起换行

因为线性投影对所有输入行使用相同参数：

$$
Q'=X'W_Q=PXW_Q=PQ,
$$

同理有 $K'=PK$、$V'=PV$。于是：

$$
S'=\frac{Q'K'^\top}{\sqrt{d_k}}
=\frac{(PQ)(PK)^\top}{\sqrt{d_k}}
=PSP^\top.
$$

左乘 $P$ 重排 query 对应的行，右乘 $P^\top$ 重排 key 对应的列。每一对 query/key 的分数没有改变，只是所在的行、列发生了变化。

### B.3 Softmax 为什么保留这种重排关系？

Softmax 沿每一行计算。重排输入的行，就会重排输出的行；重排同一行的列，会重排各个指数项，但分母仍然是相同指数项的总和。

因此，softmax 之后也有相同的行列重排：

$$
A'=\operatorname{softmax}_{\mathrm{row}}(PSP^\top)
=PAP^\top.
$$

这一步说明：每个 query 对各个 key 的权重，只是跟着那些位置一起移动。

### B.4 乘上 Values，得到输出的排列等变性

将新的权重乘以新的 value 矩阵：

$$
C'=A'V'=(PAP^\top)(PV)=PA(P^\top P)V=PAV=PC.
$$

因此：

$$
\boxed{\operatorname{SA}(PX)=P\operatorname{SA}(X).}
$$

输入中的一个 token 移到另一行，它的输出也移到对应的新行，所以这个性质称为**排列等变性**。“排列不变性”则要求重排之后整个输出不变，即 $\operatorname{SA}(PX)=\operatorname{SA}(X)$，含义不同。

这个证明解释了正文的位置问题：在给定条件下，内容交互保留了 token 之间的内容关系，但没有为匹配过程提供先后次序。加入位置项或固定的 causal mask 后，重排输入通常会改变位置关系或可见范围，上面的推导条件也随之改变。

## 参考资料

- [[dive-to-attention|dive-to-attention]]：附录讲解思路的参考，按输出目标、分数构造与扰动影响逐步展开。
- [[a3.pdf|CS224N Winter 2026 Assignment 3]]：第 1(a)、1(b)、1(c) 题及第 2(a) 题的原始题干与截图。
- [Bahdanau et al. — Neural Machine Translation by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473)：通过动态 context 联合学习翻译与对齐。
- [PyTorch — Translation with a Sequence to Sequence Network and Attention](https://docs.pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html)：teacher forcing、训练循环与自回归生成的实现参考；教程中的 Attention 接入状态更新的顺序与本文第 $3.1$ 节不同。
- [Luong et al. — Effective Approaches to Attention-based Neural Machine Translation](https://aclanthology.org/D15-1166/)：基于 Decoder 状态的 Attention 与打分函数。
- [Vaswani et al. — Attention Is All You Need](https://arxiv.org/abs/1706.03762)：Q/K/V 的矩阵形式与缩放点积。
