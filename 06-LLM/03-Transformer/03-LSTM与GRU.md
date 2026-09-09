---
title: "LSTM 与 GRU：门控循环神经网络"
aliases:
  - "LSTM"
  - "GRU"
  - "Long Short-Term Memory"
  - "Gated Recurrent Unit"
  - "门控循环神经网络"
tags:
  - nlp
  - rnn
  - lstm
  - gru
  - sequence-modeling
  - gated-recurrent-network
type: learning-note
topic: lstm-gru
content_status: complete
learning_status: not-started
created: 2026-09-05
updated: 2026-09-05
---

> [!abstract] 笔记定位
> 本节承接 [[02-RNN|02-RNN]]，从 vanilla RNN 的状态覆盖与梯度长链出发，逐步推导 LSTM 和 GRU 为什么需要 gate、candidate 与加法式状态更新。全文用“保存主语单复数，跨过干扰词，直到预测谓语”作为贯穿例子；重点不是背门的名字，而是理解信息怎样被**写入、保留、读取与替换**。

> [!important] 核心结论
> Vanilla RNN 每一步都用矩阵变换与非线性重新计算状态；LSTM 和 GRU 则给旧状态增加一条受 gate 控制的加法式保留路径：
> $$
> \boxed{
> \text{new state}
> =
> \text{保留的旧状态}
> +
> \text{写入的新候选}
> }
> $$
> 当保留系数接近 $1$、写入系数接近 $0$ 时，信息和梯度都可以更直接地跨过多个时间步。这是“缓解长期依赖困难”，不是获得无限、无损记忆。


## 学习目标

- [ ] 从前向信息覆盖和反向梯度长链两个角度解释 vanilla RNN 的困难
- [ ] 解释 sigmoid gate 为什么是逐维软控制，而不是硬开关
- [ ] 从“保留旧内容、写入新内容、控制对外输出”推导 LSTM
- [ ] 写出 LSTM 的完整前向公式并检查 shape
- [ ] 解释 LSTM cell path 为什么更利于长期信用分配
- [ ] 从“单一状态上的受控插值”推导 GRU
- [ ] 区分 GRU reset gate 与 update gate 的职责
- [ ] 按本文约定解释 GRU update gate 的方向与 reset-after 计算位置
- [ ] 比较 LSTM、GRU 与 vanilla RNN 的状态接口和能力边界
- [ ] 说明换用门控 cell 后，任务目标、BPTT 与时间串行性为何仍然存在

> [!info]+ 参考资料
> | 类型 | 资料与本地文件 | 说明 |
> | --- | --- | --- |
> | 前置知识 | [[02-RNN\|02-RNN]] | Vanilla RNN、BPTT、梯度消失与梯度爆炸 |
> | 课程讲义 | [[cs224n-2019-notes05-LM_RNN.pdf\|CS224N: Language Models, RNN, GRU and LSTM]] | LSTM/GRU 公式与结构图，本节主要参考资料 |
> | 课程课件 | [[cs224n-2026-lecture04-rnnlm.pdf\|CS224N 2026 Lecture 4: RNNLM]] | RNN、梯度问题与 Seq2Seq 背景 |
> | 下一阶段 | [[04-Seq2Seq\|04-Seq2Seq]] | 将 recurrent cell 组织成 Encoder 与 Decoder |


## 0. 先建立完整心智模型

### 0.1 一条需要跨时间保存的信息

考虑语言模型正在读取：

```text
The keys to the old cabinet are ...
```

为了预测 `are` 而不是 `is`，模型需要完成四件事：

1. 读到 `keys` 时，提取“主语是复数”；
2. 把这条信息写入某些状态维度；
3. 经过 `to the old cabinet` 时，保护它不被局部词覆盖；
4. 需要预测谓语时，让它影响 next-token 输出。

可以把理想化过程想成：

| 时间位置 | 当前需要的状态操作 | 门控直觉 |
| --- | --- | --- |
| `keys` | 写入“复数主语” | 允许新候选进入 |
| `to the old` | 保持原信息 | 保留旧状态，减少无关写入 |
| `cabinet` | 抵抗“单数名词”干扰，并预测下一个词 | 保护旧信息，同时让它影响 `are` 的概率 |

这不是说某个固定神经元一定等于“复数”。它只是把门控 RNN 要解决的计算问题具体化：

$$
\boxed{
\text{什么时候写？}
\quad
\text{什么时候保留？}
\quad
\text{什么时候读出？}
}
$$

### 0.2 从完整重算到受控更新

> [!note] 本篇符号
> 沿用 [[06-transformer|Transformer 基础知识与例题]] 与 [[02-RNN|02-RNN]]：$X_t$ 是查表后的输入行向量，$h_t,c_t$ 是 hidden/cell 状态，维度分别为 $D_{\mathrm{emb}}$ 与 $D_{\mathrm{rnn}}$。所有线性变换均右乘权重，batch-first 输入为 $[B,N,D_{\mathrm{emb}}]$。
>
> 保留 LSTM 的 $f_t,i_t,o_t$ 与 GRU 的 $r_t,z_t$ 等门控符号。$o_t$ 只表示 output gate；词表 logits 统一记为 $Z_t$。Attention 读取结果用大写 $C$，与 cell state $c_t$ 区分。

Vanilla RNN 的状态更新是：

$$
h_t
=
\tanh(
h_{t-1}W_h
+
X_tW_x
+
b
).
$$

旧状态没有显式的“复制通道”，而是每一步都进入新的矩阵变换和非线性。门控 RNN 增加一种更容易保留信息的结构：

$$
\boxed{
s_t
=
\alpha_t\odot s_{t-1}
+
\beta_t\odot\tilde{s}_t
}
$$

其中：

- $s_{t-1}$：已有状态；
- $\tilde{s}_t$：根据当前输入形成的新候选；
- $\alpha_t$：旧状态保留多少；
- $\beta_t$：新候选写入多少；
- $\odot$：逐元素乘法。

LSTM 和 GRU 的主要差异，就在于它们怎样组织 $s_t$、怎样产生这些控制量，以及是否把内部记忆与对外表示分开。

### 0.3 三种 cell 的最短对照

| Cell | 跨时间状态 | 核心更新方式 |
| --- | --- | --- |
| Vanilla RNN | $h_t$ | 用仿射变换和非线性完整重算 |
| LSTM | $c_t,h_t$ | 更新内部 cell，再筛选出对外 hidden state |
| GRU | $h_t$ | 在旧 hidden state 与新 candidate 之间插值 |

> [!important] 阅读顺序
> 先跟踪“旧状态走哪条路、新候选走哪条路”，再记 forget、input、output、reset、update 等名字。门名只是标签，数据流才是结构。


## 1. Vanilla RNN 为什么难以长期保留信息

### 1.1 前向：早期信息要反复经历重写

较早信息每向前传一步，都要与新输入混合，并再次经过 $W_h$ 和 $\tanh$。递归定义保证当前状态是历史输入的函数，却不保证其中的重要信息仍可恢复。对 `keys ... cabinet` 的例子，本节要解决的是怎样保护主语数信息，同时继续处理后面的词。

### 1.2 反向：远距离学习信号要经过 Jacobian 连乘

晚期 loss 要训练早期状态，必须经过许多 recurrent Jacobian。相关方向上的反复收缩会削弱远距离学习信号，反复放大则可能使训练不稳定。

> [!note]- 前置回顾：需要时再展开梯度推导
> 完整矩阵顺序与三步数值手算见 [[02-RNN#6.2 一条远距离梯度路径|02-RNN：远距离梯度路径]]；前向遗忘与梯度消失的区别见 [[02-RNN#7.2 梯度消失为什么伤害长程依赖|02-RNN：长程依赖]]。
>
> 进入本节只需记住设计要求：旧状态应有一条能接近恒等映射的保留路径，使信息与梯度减少反复经过完整矩阵变换和饱和非线性。

### 1.3 前向遗忘与梯度消失不是同一件事

| 问题 | 所在路径 | 直接含义 |
| --- | --- | --- |
| 前向信息覆盖 | $h_k\to h_t$ | 早期内容难以从当前状态恢复 |
| 反向梯度消失 | $J_t\to h_k$ | 后期误差信号难以训练早期计算 |

二者相互关联：如果模型收不到远距离训练信号，就很难学会怎样保护早期信息；但“当前状态丢了信息”和“梯度太小”仍是两个不同判断。

> [!summary] 由问题推出设计目标
> 一个更适合长期依赖的 recurrent cell，至少应允许：
> 1. 旧状态可以近似原样向前传；
> 2. 无关输入不会被迫覆盖旧状态；
> 3. 新信息可以在需要时写入；
> 4. 误差信号拥有更容易接近恒等映射的反向路径；跨越的时间步数仍然不变。


## 2. Gate 与 Candidate：先理解两个基础部件

### 2.1 Gate 是逐维软控制向量

一个典型 gate 为：

$$
g_t
=
\sigma(
X_tW_g
+
h_{t-1}U_g
+
b_g
).
$$

由于 sigmoid 的输出位于 $(0,1)$，逐元素乘法：

$$
g_t\odot v
$$

可以控制 $v$ 的每个维度保留多少。例如：

$$
g_t=(0.98,0.04,0.63)
$$

表示三个维度分别近似保留、近似抑制和部分通过。Gate 不是控制全部状态的一个标量，也不是不可微的 0/1 开关。

### 2.2 Candidate 决定“可能写什么”

Candidate 通常写成：

$$
\tilde{s}_t
=
\tanh(
X_tW_s
+
h_{t-1}U_s
+
b_s
).
$$

它是根据当前输入与过去状态计算出的新内容：

$$
\underbrace{\tilde{s}_t}_{\text{写什么}}
\qquad
\underbrace{g_t\odot\tilde{s}_t}_{\text{实际写多少}}.
$$

### 2.3 为什么使用加法更新

考虑最简单的插值：

$$
s_t
=
g_t\odot s_{t-1}
+
(1-g_t)\odot\tilde{s}_t.
$$

若某维 $g_{t,j}\approx1$，则 $s_{t,j}\approx s_{t-1,j}$。该维度无需反复通过完整的 recurrent matrix，就能近似复制到下一步。LSTM 与 GRU 都保留了这种“旧状态分支 + 新候选分支”的结构。


## 3. LSTM：把内部记忆与对外表示分开

### 3.1 为什么需要两种状态

LSTM 在每个时间步接收：

$$
(X_t,h_{t-1},c_{t-1}),
$$

输出：

$$
(h_t,c_t).
$$

- $c_t$（cell state）：承担加法式的跨时间记忆更新；
- $h_t$（hidden state）：当前对外可见的表示，同时参与下一步 gate 和 candidate 的计算。

不要把二者机械地翻译成“长期记忆”和“短期记忆”。更准确的区别是：$c_t$ 有显式加法式时间路径，$h_t$ 是从当前 cell 中筛选出来的可见表示。

### 3.2 第一步：决定旧记忆保留多少

Forget gate：

$$
\boxed{
f_t
=
\sigma(
X_tW_f
+
h_{t-1}U_f
+
b_f)
}
$$

旧 cell 的保留部分为：

$$
f_t\odot c_{t-1}.
$$

- $f_{t,j}\approx1$：第 $j$ 维旧内容近似保留；
- $f_{t,j}\approx0$：第 $j$ 维旧内容被清除。

在贯穿例子中，跨过 `to the old cabinet` 时，保存主语数信息的维度可以让 forget gate 保持接近 $1$。

### 3.3 第二步：生成候选，并决定写入多少

先生成新候选：

$$
\boxed{
\tilde{c}_t
=
\tanh(
X_tW_c
+
h_{t-1}U_c
+
b_c)
}
$$

再用 input gate 决定写入比例：

$$
\boxed{
i_t
=
\sigma(
X_tW_i
+
h_{t-1}U_i
+
b_i)
}
$$

实际写入量是 $i_t\odot\tilde{c}_t$，于是：

$$
\boxed{
c_t
=
\underbrace{f_t\odot c_{t-1}}_{\text{保留旧记忆}}
+
\underbrace{i_t\odot\tilde{c}_t}_{\text{写入新候选}}
}
$$

标准 LSTM 没有要求 $f_t+i_t=1$。模型可以同时保留和写入，也可以同时减少两者。

### 3.4 第三步：决定当前对外暴露什么

Output gate：

$$
\boxed{
o_t
=
\sigma(
X_tW_o
+
h_{t-1}U_o
+
b_o)
}
$$

Hidden state 为：

$$
\boxed{
h_t
=
o_t\odot\tanh(c_t)
}
$$

Cell 中保存的信息不必每一步都全部暴露。例如主语数信息可以在中间词处继续保留在 $c_t$，到预测谓语时才通过 $o_t$ 影响 $h_t$ 和输出分布。

### 3.5 把完整 LSTM 放回一张图

$$
\boxed{
\begin{aligned}
f_t&=\sigma(X_tW_f+h_{t-1}U_f+b_f),\\
i_t&=\sigma(X_tW_i+h_{t-1}U_i+b_i),\\
o_t&=\sigma(X_tW_o+h_{t-1}U_o+b_o),\\
\tilde{c}_t&=\tanh(X_tW_c+h_{t-1}U_c+b_c),\\
c_t&=f_t\odot c_{t-1}+i_t\odot\tilde{c}_t,\\
h_t&=o_t\odot\tanh(c_t).
\end{aligned}
}
$$

![[_assets/images/02-LSTM内部结构.png|900]]

*图 1：LSTM 的内部数据流。左下 forget gate 控制旧 cell，左上 input gate 控制 candidate 写入，右上 output gate 控制 cell 对 hidden state 的暴露。来源：[[cs224n-2019-notes05-LM_RNN.pdf#page=13|CS224N 讲义，PDF 第 13 页]]。*

### 3.6 贯穿例子：一次理想化的门控轨迹

假设某个 cell 维度的正值倾向表示“当前主语为复数”。下面不是训练后必然出现的数值，而是展示 LSTM 机制允许怎样的信息操作：

| 输入 | $f_t$ | $i_t$ | $\tilde c_t$ | 主要效果 |
| --- | ---: | ---: | ---: | --- |
| `The` | 0.5 | 0.1 | 0.0 | 暂无关键信息 |
| `keys` | 0.2 | 0.95 | $+0.9$ | 写入“复数” |
| `to` | 0.99 | 0.01 | $-0.1$ | 几乎原样保留 |
| `the old` | 0.99 | 0.01 | $0.0$ | 继续保护 |
| `cabinet` | 0.98 | 0.02 | $-0.8$ | 抑制临近单数名词的干扰，并通过较大的 $o_t$ 让该信息影响下一个词 `are` |

关键不是 gate 人工知道语法，而是预测 `are` 的 loss 可以通过 BPTT 调整这些 gate，使有用的时间路径逐渐形成。

> [!example]- 展开：手算一个二维 LSTM 时间步
> 已知：
> $$
> \begin{aligned}
> c_{t-1}&=(0.8,-0.4),&
> f_t&=(0.9,0.1),\\
> i_t&=(0.3,0.8),&
> \tilde{c}_t&=(0.2,0.7),\\
> o_t&=(0.6,0.5).
> \end{aligned}
> $$
> 保留旧记忆：
> $$
> f_t\odot c_{t-1}=(0.72,-0.04).
> $$
> 写入新候选：
> $$
> i_t\odot\tilde{c}_t=(0.06,0.56).
> $$
> 因而：
> $$
> c_t=(0.78,0.52),
> $$
> $$
> h_t
> =(0.6,0.5)\odot\tanh(0.78,0.52)
> \approx(0.392,0.239).
> $$
> Cell 保存的数值与当前暴露的 hidden state 并不相同。

> [!note]- 展开：Shape、合并矩阵与参数量
> 单样本输入 $X_t\in\mathbb R^{1\times D_{\mathrm{emb}}}$，状态 $h_t,c_t\in\mathbb R^{1\times D_{\mathrm{rnn}}}$。对每组 gate/candidate：
> $$
> W_g\in\mathbb R^{D_{\mathrm{emb}}\times D_{\mathrm{rnn}}},\qquad
> U_g\in\mathbb R^{D_{\mathrm{rnn}}\times D_{\mathrm{rnn}}}.
> $$
> 实现中可沿最后一维拼接输入与旧状态，用一次右乘生成四组 pre-activation：
> $$
> a_t=\operatorname{Concat}(h_{t-1},X_t),\qquad
> [u_f,u_i,u_o,u_c]=a_tW+b,
> $$
> $$
> W\in\mathbb R^{(D_{\mathrm{rnn}}+D_{\mathrm{emb}})\times4D_{\mathrm{rnn}}},\qquad
> b\in\mathbb R^{1\times4D_{\mathrm{rnn}}}.
> $$
> 对 batch，$[B,D_{\mathrm{rnn}}+D_{\mathrm{emb}}]$ 右乘 $W$ 后得到 $[B,4D_{\mathrm{rnn}}]$，再沿特征维拆成四组。按一份 bias 计算，参数量为：
> $$
> \boxed{4D_{\mathrm{rnn}}(D_{\mathrm{emb}}+D_{\mathrm{rnn}}+1)}.
> $$

## 4. 为什么 LSTM 更利于长期信用分配

### 4.1 Cell 提供显式的直接路径

只看 $c_{t-1}\to c_t$ 的直接边，把本步已经算出的 gate 暂时视作固定值：

$$
\left.
\frac{\partial c_t}{\partial c_{t-1}}
\right|_{\mathrm{direct}}
=
\operatorname{diag}(f_t).
$$

跨越多个时间步：

$$
\left.
\frac{\partial c_t}{\partial c_k}
\right|_{\mathrm{direct}}
=
\prod_{j=k+1}^{t}
\operatorname{diag}(f_j).
$$

若某些维度上的 $f_j$ 长期接近 $1$，对应 cell 分量可以近似复制，梯度也能沿直接路径较少衰减。相比 vanilla RNN 每一步都必须经过 $W_h$ 和饱和非线性，这条路径更容易接近恒等映射。

### 4.2 “直接路径”不等于完整导数只有 forget gate

$f_t,i_t,\tilde{c}_t$ 仍通过 $h_{t-1}$ 间接依赖过去状态，所以完整 total derivative 还包含其他路径。上式是在解释 LSTM 新增的关键结构，不是在声称所有梯度都严格等于 forget gate 的乘积。

### 4.3 它改善了什么，又没有保证什么

LSTM 更容易学出：

- 长时间保留某些状态维度；
- 抵抗无关输入覆盖；
- 在需要时再写入或暴露信息；
- 让远距离 loss 更有效地训练较早时间步。

但仍不能说它“彻底解决梯度消失”：

- 若大量 $f_j<1$，乘积仍会衰减；
- sigmoid gate 自身可能进入饱和区；
- loss 到 cell 还要经过 output gate 和其他网络；
- 梯度爆炸仍可能发生；
- 有限维状态仍可能形成信息瓶颈。

> [!important] 准确表述
> LSTM 提供了一条**可学习、可接近恒等映射**的时间路径，从结构上缓解 vanilla RNN 的长期依赖优化困难；它不保证任意距离上的信息和梯度都无损。

> [!note]- Forget-gate bias 为什么常初始化为正值？
> 正的 forget-gate bias 会使训练初期 $f_t$ 更偏向 $1$，先提供一条较通畅的时间路径，再由训练学习何时遗忘。这是常见初始化策略，不是 LSTM 的定义。

> [!example]- 自检：Forget gate 接近 1，能保留多久？
> 只看一个 cell 维度，设初值 $c_0=1$，后续输入写入项为 $0$，forget 系数恒为 $f$，则：
> $$
> c_N=f^Nc_0,\qquad
> \left.\frac{\partial c_N}{\partial c_0}\right|_{\mathrm{direct}}=f^N.
> $$
> 经过 100 步，$0.99^{100}\approx0.366$，而 $0.999^{100}\approx0.905$。两者单步都“接近 1”，长期保留量却明显不同。
>
> 再令某一步 $o_t=0$：此时 $h_t=0$，但已存储的 $c_t$ 不会因此直接清零。真实 sigmoid gate 只能趋近这些理想极值；这里暂时把控制量固定，用于区分“保存”和“暴露”。
>
> **学习记录：**我算出的 100 步保留量：____；完整模型中 gate 随输入变化后，还需考虑：____。


## 5. GRU：在单一状态上完成受控更新

### 5.1 从 LSTM 简化到一个状态

GRU 不保留独立 cell state，而是直接更新一个 hidden state：

$$
h_{t-1}\longrightarrow h_t.
$$

它仍要解决两个问题：

1. 生成新候选时，应参考多少旧状态？
2. 最终状态应保留多少旧内容、采用多少新候选？

对应的控制量分别是 reset gate 和 update gate。

### 5.2 Reset gate：生成 candidate 时参考多少过去

本文采用与下方结构图一致的 reset-after 写法：

$$
r_t
=
\sigma(
X_tW_r
+
h_{t-1}U_r
+
b_r),
$$

$$
\boxed{
\tilde{h}_t
=
\tanh\left(
X_tW_h
+
r_t\odot(h_{t-1}U_h)
+
b_h
\right)
}.
$$

- $r_t\approx0$：candidate 较少使用过去状态；
- $r_t\approx1$：candidate 充分参考过去状态。

Reset gate 只控制“新候选怎样形成”，并不直接决定最终旧状态保留多少。

### 5.3 Update gate：在旧状态和新候选之间插值

本文令 $z_t$ 表示“旧状态保留比例”：

$$
z_t
=
\sigma(
X_tW_z
+
h_{t-1}U_z
+
b_z),
$$

$$
\boxed{
h_t
=
\underbrace{z_t\odot h_{t-1}}_{\text{保留旧状态}}
+
\underbrace{(1-z_t)\odot\tilde{h}_t}_{\text{采用新候选}}
}.
$$

- $z_t\approx1$：近似复制旧状态；
- $z_t\approx0$：主要采用新候选。

在 `keys ... cabinet ... are` 的例子中，保存主语数信息的维度可以在 `keys` 处取较小的 $z_t$ 以写入新候选，在中间词处取接近 $1$ 的 $z_t$ 以保护旧状态。

> [!example]- 展开：手算一次 GRU 状态插值
> 已知：
> $$
> h_{t-1}=(0.8,-0.4),
> \qquad
> z_t=(0.9,0.2),
> \qquad
> \tilde{h}_t=(0.1,0.6).
> $$
> 按本文“$z_t$ 表示旧状态保留比例”的约定：
> $$
> \begin{aligned}
> h_t
> &=z_t\odot h_{t-1}
> +(1-z_t)\odot\tilde{h}_t\\
> &=(0.9\times0.8+0.1\times0.1,
> \;0.2\times(-0.4)+0.8\times0.6)\\
> &=(0.73,0.40).
> \end{aligned}
> $$
> 第一维主要保留旧状态，第二维主要采用新 candidate；同一个时间步的不同维度可以执行不同更新策略。

![[_assets/images/01-GRU内部结构.png|900]]

*图 2：GRU 内部数据流。Reset gate 调节旧 hidden state 参与 candidate 的程度；update gate 在旧 state 与 candidate 之间插值。图与正文均采用 reset-after、$z_t$ 表示旧状态保留比例的写法。来源：[[cs224n-2019-notes05-LM_RNN.pdf#page=12|CS224N 讲义，PDF 第 12 页]]。*

### 5.4 固定本篇的 GRU 约定

本文固定采用 $z_t$ 控制旧状态保留比例：$z_t\approx1$ 表示保留，$z_t\approx0$ 表示采用新 candidate。阅读本篇时始终按这一含义解释，不在推导中切换门的定义。

> [!note]- 实现约定与参数量
> 本文采用 reset-after：先计算 $h_{t-1}U_h$，再用 $r_t$ 逐维控制其参与 candidate 的程度。框架可能采用其他 reset 位置或 bias 拆分方式，迁移权重时需要核对，但本篇公式只使用这一种定义。
>
> 对 $X_t\in\mathbb R^{1\times D_{\mathrm{emb}}}$、$h_t\in\mathbb R^{1\times D_{\mathrm{rnn}}}$，三组仿射变换按一份 bias 计算，参数量为：
> $$
> \boxed{3D_{\mathrm{rnn}}(D_{\mathrm{emb}}+D_{\mathrm{rnn}}+1)}.
> $$

## 6. LSTM 与 GRU：同一设计思想的两种组织方式

### 6.1 结构对照

| 问题 | LSTM | GRU |
| --- | --- | --- |
| 跨时间状态 | $c_t,h_t$ | $h_t$ |
| 旧信息保留 | forget gate 控制 cell 旧分支 | update gate 控制旧 hidden 分支 |
| 新信息写入 | input gate $\times$ candidate | update gate 的互补分支 $\times$ candidate |
| Candidate 是否调节过去 | 直接读取 $h_{t-1}$ | reset gate 调节过去参与度 |
| 对外暴露 | 独立 output gate | 没有独立 output gate |
| 典型仿射变换组数 | 4 | 3 |

### 6.2 把共同结构并排写出来

LSTM：

$$
c_t
=
f_t\odot c_{t-1}
+
i_t\odot\tilde{c}_t.
$$

GRU：

$$
h_t
=
z_t\odot h_{t-1}
+
(1-z_t)\odot\tilde{h}_t.
$$

共同思想是：

1. 旧状态拥有显式保留分支；
2. 新内容先形成 candidate；
3. gate 决定保留与写入比例；
4. 所有 gate 都由任务 loss 学习，而不是人工规则。

### 6.3 怎样选择

不存在普遍成立的“LSTM 一定优于 GRU”或相反结论。

- GRU 状态接口更紧凑，典型参数量更少；
- LSTM 将 cell 与 hidden 分开，并提供独立 output gate；
- 相同 hidden size 不代表相同参数量或相同计算量；
- 实际速度还取决于 kernel、硬件、batch 和序列长度；
- 最终应在相同数据、训练预算和评价标准下比较。


## 7. 换用门控 Cell 后，哪些东西没有改变

### 7.1 它们仍然是 RNN

LSTM 与 GRU 仍满足：

$$
\text{state}_t
=
f_\theta(\text{state}_{t-1},X_t).
$$

因此它们仍然沿时间递归、跨时间共享参数、难以在单层内跨时间完全并行，并使用 BPTT 或 TBPTT 训练。

门控 cell 也不会自动改变任务目标。例如语言模型仍计算：

$$
h_t
\xrightarrow{\text{projection + softmax}}
P(x_{t+1}\mid x_{\le t}),
$$

$$
J(\theta)
=-
\sum_{t=1}^{N-1}
\log P_\theta(x_{t+1}\mid x_{\le t}).
$$

### 7.2 BPTT 与 gradient clipping 仍有各自职责

| 机制 | 回答的问题 |
| --- | --- |
| Gate + 加法式更新 | 状态怎样保存和修改信息？ |
| BPTT/TBPTT | 梯度怎样沿展开图传播？ |
| Gradient clipping | 已计算出的梯度过大时怎样限制范数？ |

门控结构不保证梯度永不爆炸，所以 gradient clipping 仍是常见稳定化手段；gradient clipping 又不能创造新的前向记忆路径。

### 7.3 在 Seq2Seq 中传递什么状态

在普通单向模型中常从零状态开始：

$$
h_0=0,
\qquad
c_0=0\quad\text{(LSTM)}.
$$

经典 Seq2Seq 可以用 Encoder 最终状态初始化 Decoder：

| Cell | Encoder 最终状态 | Decoder 初始状态 |
| --- | --- | --- |
| GRU | $h_{N_{\mathrm{src}}}^{\mathrm{enc}}$ | $h_0^{\mathrm{dec}}$ |
| LSTM | $(h_{N_{\mathrm{src}}}^{\mathrm{enc}},c_{N_{\mathrm{src}}}^{\mathrm{enc}})$ | $(h_0^{\mathrm{dec}},c_0^{\mathrm{dec}})$ |

门控 cell 可以改善 Encoder 和 Decoder 内部的长递归链，却不会自动消除两者之间的 fixed-vector bottleneck。完整接口见 [[04-Seq2Seq|04-Seq2Seq]]。

> [!note]- 展开：Batch、堆叠、双向与 padding
> **Batch shape**：若输入为 $X\in\mathbb R^{B\times N\times D_{\mathrm{emb}}}$，单步 LSTM 状态 $h_t,c_t\in\mathbb R^{B\times D_{\mathrm{rnn}}}$；GRU 只有 $h_t\in\mathbb R^{B\times D_{\mathrm{rnn}}}$。Batch 内样本并行，但时间步仍有依赖。
>
> **Stacked RNN**：每一层都维护自己的时间状态；下层当前输出作为上层当前输入。
>
> **Bidirectional RNN**：正向与反向分别编码后拼接。它适合 Encoder、分类与序列标注，但反向分支读取未来 token，不能直接用于严格左到右生成。
>
> **Padding**：不仅要忽略 padding 位置的 loss，还要避免 padding 继续修改短序列的最终 state；可使用真实长度、packing 或显式 state mask。
>
> **Stateful + TBPTT**：前一 chunk 的最终状态可以传给下一 chunk，但通常在边界 detach。前向状态能够携带更早信息，反向信用分配仍受截断长度限制。


## 8. 常见混淆与能力边界

| 容易混淆的说法 | 更准确的理解 |
| --- | --- |
| Gate 是某事件的概率 | Gate 首先是确定性的逐维乘法系数 |
| Cell state 一定在 $[-1,1]$ | Candidate 受 $\tanh$ 限制，累加后的 cell 不受此范围限制 |
| Forget 与 input gate 互补 | 标准 LSTM 独立学习二者，不要求和为 $1$ |
| Reset gate 决定最终遗忘 | 它调节 candidate 使用多少过去；最终插值由 update gate 决定 |
| LSTM 彻底解决梯度消失 | 它提供更好的路径，但没有无损传播保证 |
| 门控意味着无限上下文 | 状态容量、训练信号与时间长度仍有限 |
| GRU 一定比 LSTM 快 | 参数通常更少，但实际速度依赖实现与硬件 |
| 门控 RNN 可以跨时间并行 | 当前 state 仍依赖上一 state |


## 9. 总结：从问题回到结构

| 问题 | Vanilla RNN | LSTM / GRU 的结构性回答 |
| --- | --- | --- |
| 旧信息容易被覆盖 | 每步完整重算 | 给旧状态增加显式保留分支 |
| 不知道何时写入 | 新输入必然参与重算 | Candidate 与写入比例分开 |
| 远距离梯度路径复杂 | 矩阵与非线性反复连乘 | 加法路径可接近恒等映射 |
| 内部保存与当前输出耦合 | 只有一个 hidden state | LSTM 用 cell/hidden 分开；GRU 保持紧凑单状态 |

两条最重要的公式是：

$$
\boxed{
c_t
=
f_t\odot c_{t-1}
+
i_t\odot\tilde{c}_t,
\qquad
h_t
=
o_t\odot\tanh(c_t)
}
$$

$$
\boxed{
h_t
=
z_t\odot h_{t-1}
+
(1-z_t)\odot\tilde{h}_t
}
$$

> [!important] 最终心智模型
> LSTM 与 GRU 的本质不是“多了几个门”，而是把状态更新改造成可学习的信息路由：**旧信息走保留分支，新信息先成为 candidate，再受控写入。**LSTM 额外区分内部 cell 与对外 hidden，GRU 则在一个 hidden state 上完成受控插值。


## 建议学习顺序

1. 用 `The keys ... cabinet are` 解释模型需要保存什么；
2. 区分前向信息覆盖与反向梯度消失；
3. 理解 gate 是逐维系数、candidate 是待写入内容；
4. 按“忘多少 → 写什么 → 写多少 → 暴露多少”推导 LSTM；
5. 手算一次 $c_t$ 和 $h_t$；
6. 沿 direct cell path 推导 forget gate 的梯度作用；
7. 按“candidate 怎样生成 → 新旧状态怎样插值”推导 GRU；
8. 检查当前资料中 $z_t$ 的方向和 reset 位置；
9. 对照 LSTM/GRU 的状态接口；
10. 进入 [[04-Seq2Seq|04-Seq2Seq]]，观察它们怎样成为 Encoder 与 Decoder。


## 自测问题

1. 在 `The keys to the old cabinet are` 中，模型为什么需要抵抗最近单数名词的干扰？
2. Vanilla RNN 的前向信息覆盖和反向梯度消失有什么区别？
3. 为什么 gate 是向量而不是一个标量开关？
4. Candidate 与 gate 分别回答“写什么”和“写多少”中的哪一个？
5. LSTM 为什么同时维护 $c_t$ 与 $h_t$？
6. 写出 LSTM 三个 gate、candidate、cell 和 hidden 的完整公式。
7. Forget、input、output gate 分别控制哪条数据流？
8. 为什么标准 LSTM 不要求 $f_t+i_t=1$？
9. Cell state 为什么不一定落在 $[-1,1]$？
10. LSTM 的 direct cell path 为什么更容易接近恒等映射？
11. 为什么不能把完整梯度简单说成 forget gate 的乘积？
12. 为什么 LSTM 只能说“缓解”而不是“彻底解决”梯度消失？
13. GRU reset gate 与 update gate 分别控制什么？
14. 本文中 $z_t$ 接近 1 或 0 时，分别保留哪一部分？
15. 本文的 reset-after 先进行哪一步矩阵乘法，再由哪个 gate 控制？
16. LSTM 和 GRU 共同的核心结构是什么？
17. 换用门控 cell 后，为什么仍需要 BPTT 和 gradient clipping？
18. 为什么门控 cell 不能消除时间串行性和 Seq2Seq fixed-vector bottleneck？


## 学习记录

- [ ] 已用贯穿例子解释写入、保留和读取
- [ ] 已区分前向遗忘与反向梯度消失
- [ ] 已独立写出 LSTM 完整公式
- [ ] 已手算一个 LSTM 时间步
- [ ] 已解释 direct cell path 的梯度作用及其边界
- [ ] 已独立写出本文约定下的 GRU 公式
- [ ] 已检查 update gate 的方向与 reset 位置
- [ ] 已比较 LSTM、GRU 与 vanilla RNN
- [ ] 已说明门控 cell 为什么仍需 BPTT
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前置章节 [[02-RNN|02-RNN]] 的联系：
- 与下一章节 [[04-Seq2Seq|04-Seq2Seq]] 的联系：
