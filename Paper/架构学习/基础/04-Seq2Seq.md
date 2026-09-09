---
title: "Seq2Seq 与 Encoder-Decoder"
aliases:
  - "Seq2Seq"
  - "Sequence-to-Sequence"
  - "Encoder-Decoder"
  - "序列到序列"
  - "编码器-解码器"
tags:
  - nlp
  - seq2seq
  - encoder-decoder
  - conditional-language-model
  - sequence-modeling
  - machine-translation
type: learning-note
topic: seq2seq
content_status: complete
learning_status: not-started
created: 2026-09-05
updated: 2026-09-05
---

> [!abstract] 笔记定位
> 本节承接 [[Paper/架构学习/基础/02-RNN.md|02-RNN]] 与 [[Paper/架构学习/基础/03-LSTM与GRU.md|03-LSTM与GRU]]，用单层经典 RNN 推导最早期的 fixed-vector Seq2Seq。全文围绕同一个翻译样本展开：先定义 $P(y\mid x)$，再走完 Encoder → source summary → Decoder 的前向过程，随后分别完成训练和生成，最后从固定向量瓶颈自然引出 Attention。Padding、mask 与 shape 放在核心主线之后，作为工程实现层单独说明。

> [!important] 核心结论
> Seq2Seq 把“输入一条序列、输出另一条序列”写成条件自回归建模：
> $$
> \boxed{
> P(y\mid x)
> =
> \prod_{t=1}^{N_{\mathrm{tgt}}}
> P(y_t\mid y_{<t},x)
> }
> $$
> Encoder 负责把源序列变成条件信息；Decoder 则是一个被源序列条件化的语言模型，根据源条件与已有目标前缀逐步预测下一个 token。


## 学习目标

- [ ] 区分 Seq2Seq 任务、条件概率模型与 Encoder-Decoder 架构
- [ ] 推导 $P(y\mid x)$ 的自回归分解
- [ ] 解释 `<BOS>` 与 `<EOS>` 如何定义生成的开始和结束
- [ ] 写出经典 RNN Encoder、source summary、bridge 与 Decoder 的前向公式
- [ ] 用一个翻译样本走完 Encoder 到每个目标 token 的数据流
- [ ] 正确构造 shift-right 后的 Decoder input 与 target
- [ ] 区分 Teacher Forcing、target shifting 与 BPTT
- [ ] 从每步正确 token 的概率计算 sequence NLL
- [ ] 区分训练时的真实前缀与推理时的模型前缀
- [ ] 比较 greedy、sampling 与 beam search，并手算一个反例
- [ ] 解释 fixed-vector bottleneck 为什么引出 Attention
- [ ] 在核心概念之后处理 variable-length batch、padding、mask 与 shape

> [!info]+ 参考资料
> | 类型 | 资料与本地文件 | 说明 |
> | --- | --- | --- |
> | 前置知识 | [[Paper/架构学习/基础/02-RNN.md\|02-RNN]] | RNN-LM、Teacher Forcing、BPTT 与生成 |
> | 前置知识 | [[Paper/架构学习/基础/03-LSTM与GRU.md\|03-LSTM与GRU]] | LSTM/GRU 及其状态接口 |
> | 课程课件 | [[Paper/架构学习/CS224n/resources/slides/cs224n-2026-lecture04-rnnlm.pdf\|CS224N Lecture 4: RNNLM]] | 经典 RNN Encoder-Decoder、训练与 bottleneck |
> | 课程讲义 | [[Paper/架构学习/CS224n/resources/notes/cs224n-2019-notes05-LM_RNN.pdf\|CS224N: Language Models, RNN, GRU and LSTM]] | RNN 与机器翻译背景 |
> | 下一阶段 | [[Paper/架构学习/基础/05-Attention.md\|05-Attention]] | 从固定摘要到动态读取，推导 Q/K/V 与 Self-Attention |
> | 延伸笔记 | [[Paper/架构学习/从 Seq2Seq 到 Attention 再到 Transformer.md\|从 Seq2Seq 到 Attention 再到 Transformer]] | 从 fixed-vector 模型过渡到 Attention |


## 0. 先建立完整心智模型

### 0.1 贯穿全文的翻译任务

给定法语源句：

```text
source: il / m' / a / entarté
```

生成英语目标句：

```text
target: he / hit / me / with / a / pie / <EOS>
```

这个例子立即说明：

- 源长度 $N_{\mathrm{src}}$ 与目标长度 $N_{\mathrm{tgt}}$ 可以不同；
- 源 token 和目标 token 不需要逐位置一一对应；
- 输出可能发生重排、一对多或多对一转换；
- 模型还必须决定何时产生 `<EOS>` 并停止。

因此它不是“给每个源位置做一次分类”，而是：

$$
\boxed{
\text{读完整个输入条件}
\quad\Longrightarrow\quad
\text{生成一条新的序列}
}
$$

### 0.2 一次完整运行包含三条链

**模型计算链：**

$$
\boxed{
x_{1:N_{\mathrm{src}}}
\xrightarrow{\text{Encoder}}
z
\xrightarrow{\text{bridge}}
s_0
\xrightarrow{\text{Decoder}}
P_1,P_2,\ldots
}
$$

**训练输入链：**

$$
\langle\mathrm{BOS}\rangle,y_1,y_2,\ldots
\quad\text{来自真实目标序列。}
$$

**推理输入链：**

$$
\langle\mathrm{BOS}\rangle,\tilde y_1,\tilde y_2,\ldots
\quad\text{来自模型自己的预测。}
$$

前者说明“源序列怎样影响输出”，后两者说明“Decoder 每一步读到的前一个 token 从哪里来”。不要把架构和运行阶段混成同一个问题。

### 0.3 三个层次不要混淆

| 层次 | 回答的问题 | 本文实例 |
| --- | --- | --- |
| 任务 | 输入输出是什么？ | 法语序列 → 英语序列 |
| 概率模型 | 给什么分布建模？ | $P(y\mid x)$ |
| 架构实现 | 怎样参数化该分布？ | fixed-vector RNN Encoder-Decoder |

Seq2Seq 任务并不要求使用 RNN；Encoder-Decoder 也不等于“必须把输入压成一个向量”。本文先学习历史上最简单的 fixed-vector 实现，因为它能清楚暴露后来 Attention 要解决的问题。


## 1. 从语言模型到条件序列模型

### 1.1 目标不是 $P(y)$，而是 $P(y\mid x)$

普通语言模型为目标序列本身建模：

$$
P(y).
$$

机器翻译要在给定源句之后，对可能的译文建模：

$$
P(y\mid x).
$$

仅仅生成流畅英语还不够；输出必须与 `il m'a entarté` 的内容相符。

> [!warning] 流畅不等于完成条件生成
> 若 Decoder 忽略 $x$，它仍可能学到一个不错的目标语言模型，却没有完成翻译、摘要或对话等条件任务。

### 1.2 用链式法则分解目标序列

令：

$$
x=(x_1,\ldots,x_{N_{\mathrm{src}}}),
\qquad
y=(y_1,\ldots,y_{N_{\mathrm{tgt}}}).
$$

对目标序列使用概率链式法则：

$$
\begin{aligned}
P(y\mid x)
&=P(y_1\mid x)
P(y_2\mid y_1,x)\cdots
P(y_{N_{\mathrm{tgt}}}\mid y_{<N_{\mathrm{tgt}}},x)\\
&=\prod_{t=1}^{N_{\mathrm{tgt}}}
P(y_t\mid y_{<t},x).
\end{aligned}
$$

于是 Decoder 每一步只需回答：

> 已知完整源序列 $x$ 和已经产生的目标前缀 $y_{<t}$，下一个 token 是什么？

这就是“conditional language model”的含义：

$$
\underbrace{P(y_t\mid y_{<t})}_{\text{普通 LM}}
\quad\longrightarrow\quad
\underbrace{P(y_t\mid y_{<t},x)}_{\text{Seq2Seq Decoder}}.
$$

### 1.3 `<BOS>` 启动生成，`<EOS>` 把长度变成预测问题

定义：

$$
y_0=\langle\mathrm{BOS}\rangle,
$$

并把结束标记作为最后一个真实目标：

$$
y=
(y_1,\ldots,y_{N_{\mathrm{tgt}}-1},\langle\mathrm{EOS}\rangle).
$$

- `<BOS>` 是统一的第一个 Decoder 输入，不是需要预测的正文；
- `<EOS>` 是模型必须预测的有效 target；
- 生成 `<EOS>` 就是在预测“序列现在结束”。

因此输出长度不需要预先固定，而是进入概率模型本身。


## 2. 模型前向：源序列怎样影响每个目标 token

本章先处理一条没有 padding 的样本，并使用单层 vanilla RNN。这样可以只关注模型计算；LSTM、batch 与 mask 稍后再扩展。

> [!note] 本篇符号
> 沿用 [[06-transformer|Transformer 基础知识与例题]]：$N_{\mathrm{src}},N_{\mathrm{tgt}}$ 是源、目标长度，$D_{\mathrm{enc}},D_{\mathrm{dec}}$ 是两端 hidden size，$V_{\mathrm{src}},V_{\mathrm{tgt}}$ 是两端词表大小。
>
> $x_i,y_t$ 始终是 token ID；查表得到输入行向量 $X_i^{\mathrm{src}},X_t^{\mathrm{tgt}}$，其维度为 $D_{\mathrm{emb,src}},D_{\mathrm{emb,tgt}}$。Encoder 状态为 $h_i^{\mathrm{enc}}$，Decoder 状态为 $s_t$，固定源摘要为 $z$。
>
> 线性层统一右乘；目标 logits 为 $Z_t$，概率为 $P_t=\operatorname{softmax}(Z_t)$。Attention context 用大写 $C_t$；LSTM cell state 保留小写 $c_t$。

### 2.1 Encoder：逐步读取源序列

源 token $x_i$ 先查表得到 embedding：

$$
X_i^{\mathrm{src}}
=
E_{\mathrm{src}}[x_i,:]
\in\mathbb R^{1\times D_{\mathrm{emb,src}}}.
$$

Encoder 递归更新：

$$
\boxed{
h_i^{\mathrm{enc}}
=
\tanh\left(
X_i^{\mathrm{src}}W_x^{\mathrm{enc}}
+
h_{i-1}^{\mathrm{enc}}W_h^{\mathrm{enc}}
+
b_h^{\mathrm{enc}}
\right)
}
$$

其中 $E_{\mathrm{src}}\in\mathbb R^{V_{\mathrm{src}}\times D_{\mathrm{emb,src}}}$，$W_x^{\mathrm{enc}}\in\mathbb R^{D_{\mathrm{emb,src}}\times D_{\mathrm{enc}}}$，$W_h^{\mathrm{enc}}\in\mathbb R^{D_{\mathrm{enc}}\times D_{\mathrm{enc}}}$。通常令 $h_0^{\mathrm{enc}}=0$。对贯穿例子：

$$
h_0^{\mathrm{enc}}
\xrightarrow{\texttt{il}}
h_1^{\mathrm{enc}}
\xrightarrow{\texttt{m'}}
h_2^{\mathrm{enc}}
\xrightarrow{\texttt{a}}
h_3^{\mathrm{enc}}
\xrightarrow{\texttt{entarté}}
h_4^{\mathrm{enc}}.
$$

每个位置都有一个 Encoder output：

$$
X_{\mathrm{enc}}
=
\begin{bmatrix}
h_1^{\mathrm{enc}}\\
\vdots\\
h_{N_{\mathrm{src}}}^{\mathrm{enc}}
\end{bmatrix}\in\mathbb R^{N_{\mathrm{src}}\times D_{\mathrm{enc}}}.
$$

### 2.2 Fixed-vector source summary：只取最后状态

经典 fixed-vector 模型把最后一个 Encoder state 当作整句摘要：

$$
\boxed{
z
=
h_{N_{\mathrm{src}}}^{\mathrm{enc}}
}
$$

需要区分：

| 量 | 内容 | 当前模型是否直接交给 Decoder |
| --- | --- | --- |
| $X_{\mathrm{enc}}$ | 所有源位置的 states | 否 |
| $z$ | 最后一个 Encoder state | 是 |

$z$ 在函数上依赖所有源 token，但“依赖全部输入”不等于“无损保存全部信息”。所有内容都必须竞争同一个固定维度接口。

### 2.3 Bridge：把源摘要变成 Decoder 初始状态

若 Encoder 与 Decoder hidden size 相同，最简单地令：

$$
s_0=z.
$$

若状态空间不同，可以使用可学习 projection：

$$
\boxed{
s_0
=
\tanh(
zW_{\mathrm{bridge}}
+
b_{\mathrm{bridge}})
}
$$

若 $z\in\mathbb R^{1\times D_{\mathrm{enc}}}$、$s_0\in\mathbb R^{1\times D_{\mathrm{dec}}}$，则：

$$
W_{\mathrm{bridge}}
\in\mathbb R^{D_{\mathrm{enc}}\times D_{\mathrm{dec}}}.
$$

Bridge 不是第三个序列模型，只是 Encoder 输出空间到 Decoder 状态空间的接口。

> [!tip] 从 Bridge 预览多模态 Encoder–Projector–Decoder
> 这里的 Bridge 可以看作后续多模态架构中 **projector** 的早期原型：视觉、音频等 Encoder 先把原始输入编码为特征，projector 再把这些特征映射到 Decoder 能接收的维度与表示空间，最后由语言 Decoder 自回归生成文本。
> $$
> \begin{aligned}
> \text{image/audio}
> &\xrightarrow{\text{modality Encoder}}
> \text{features} \\
> &\xrightarrow{\text{projector}}
> \text{decoder-compatible representations} \\
> &\xrightarrow{\text{language Decoder}}
> \text{text}
> \end{aligned}
> $$
> 二者的共同思想都是“**对齐模块两侧的表示接口**”；区别在于，此处 Bridge 只用单个摘要初始化 RNN Decoder，而现代多模态 projector 往往会保留一串模态特征，并将其映射成可被语言模型读取的 token-like embeddings，而不只是生成一个初始 hidden state。

### 2.4 Decoder：读取前一个目标 token，预测当前 token

第 $t$ 步读取前一个目标 token $y_{t-1}$：

$$
X_{t-1}^{\mathrm{tgt}}
=
E_{\mathrm{tgt}}[y_{t-1},:].
$$

Decoder 更新状态：

$$
\boxed{
s_t
=
\tanh\left(
X_{t-1}^{\mathrm{tgt}}W_x^{\mathrm{dec}}
+
s_{t-1}W_h^{\mathrm{dec}}
+
b_s
\right)
}
$$

其中 $E_{\mathrm{tgt}}\in\mathbb R^{V_{\mathrm{tgt}}\times D_{\mathrm{emb,tgt}}}$，$W_x^{\mathrm{dec}}\in\mathbb R^{D_{\mathrm{emb,tgt}}\times D_{\mathrm{dec}}}$，$W_h^{\mathrm{dec}}\in\mathbb R^{D_{\mathrm{dec}}\times D_{\mathrm{dec}}}$。再用 $W_U\in\mathbb R^{D_{\mathrm{dec}}\times V_{\mathrm{tgt}}}$ 投影到目标词表：

$$
Z_t
=
s_tW_U+b_U,
$$

$$
\boxed{
P_t
=
\operatorname{softmax}(Z_t)
}
$$

其中第 $w$ 个分量为：

$$
P_{t,w}
=
P(y_t=w\mid y_{<t},x).
$$

源序列没有显式写在 Decoder 单步公式里，是因为它已经通过初始状态进入依赖链：

$$
\boxed{
x
\to z
\to s_0
\to s_t
\to P_t
}
$$

### 2.5 贯穿例子：逐步生成目标句

下表假设此前 token 都已正确产生；训练与推理的区别在于这些前缀来自真实目标还是模型预测，将在第 3、4 章分别说明。

| 时间步 | Decoder 读取 | 当前预测 | 源条件怎样存在 |
| ---: | --- | --- | --- |
| 1 | `<BOS>` | `he` | $s_0$ 由整句源摘要初始化 |
| 2 | `he` | `hit` | $s_1$ 继承源条件和目标前缀 |
| 3 | `hit` | `me` | $s_2$ 继续递归传递条件 |
| 4 | `me` | `with` | 同上 |
| 5 | `with` | `a` | 同上 |
| 6 | `a` | `pie` | 同上 |
| 7 | `pie` | `<EOS>` | 模型预测序列结束 |

这张图展示了同一计算过程：

![[_assets/images/01-Seq2Seq机器翻译.png|900]]

*图 1：Encoder 读完整个源句后，用最终状态条件化 Decoder；Decoder 从 `<START>`（即本文的 `<BOS>`）开始逐步生成。粉色反馈连线表示推理时把模型预测作为下一步输入。来源：[[Paper/架构学习/CS224n/resources/slides/cs224n-2026-lecture04-rnnlm.pdf#page=53|CS224N Lecture 4，PDF 第 53 页]]。*

> [!important] 为什么不需要逐位置对齐
> Decoder 第 $t$ 步依赖源摘要与整个目标前缀，不是只读取第 $t$ 个源 token。因此模型允许源/目标不等长、顺序重排以及多对多对应。


## 3. 训练：已知正确译文时怎样计算 Loss

### 3.1 Target shifting：输入与答案错开一位

目标正文为：

```text
he / hit / me / with / a / pie
```

训练时构造：

```text
decoder_input : <BOS> / he / hit / me / with / a / pie
decoder_target: he / hit / me / with / a / pie / <EOS>
```

| $t$ | 当前输入 $y_{t-1}$ | 监督目标 $y_t$ |
| :-: | :------------: | :--------: |
|  1  |    `<BOS>`     |    `he`    |
|  2  |      `he`      |   `hit`    |
|  3  |     `hit`      |    `me`    |
|  4  |      `me`      |   `with`   |
|  5  |     `with`     |    `a`     |
|  6  |      `a`       |   `pie`    |
|  7  |     `pie`      |  `<EOS>`   |

> [!important] 为什么必须 shift right
> 在位置 $t$，模型只能读取 $y_{<t}$，然后预测 $y_t$。若把 $y_t$ 本身放进当前位置输入，模型会在预测前直接看到答案，造成 target leakage。

### 3.2 Teacher Forcing：训练时使用真实前缀

训练集已经给出正确目标序列，因此第 $t$ 步通常输入真实的 $y_{t-1}$：

$$
s_t
=
\operatorname{RNN}_{\mathrm{dec}}
(s_{t-1},E_{\mathrm{tgt}}[y_{t-1},:]).
$$

即使模型在第 1 步最可能预测成 `she`，训练第 2 步仍输入真实 token `he`。这就是 Teacher Forcing。

它决定的是**前向输入来源**，不是梯度传播算法。

### 3.3 每个目标位置贡献一项 NLL

单样本负对数似然为：

$$
\boxed{
J(\theta)
=-
\sum_{t=1}^{N_{\mathrm{tgt}}}
\log P_\theta(y_t\mid y_{<t},x)
}
$$

由于 $N_{\mathrm{tgt}}$ 包含 `<EOS>`，模型也会因为错误的终止时机受到惩罚。

> [!example]- 展开：从正确 token 概率手算 sequence loss
> 为简化，只考虑目标 `he / hit / <EOS>`。假设模型在三个位置给正确 token 的概率分别为：
> $$
> 0.60,\qquad0.50,\qquad0.80.
> $$
> 正确序列在 Teacher-Forced 路径上的概率为：
> $$
> P(y\mid x)
> =0.60\times0.50\times0.80
> =0.24.
> $$
> Sequence NLL 为：
> $$
> J=-\log0.24\approx1.427.
> $$
> 若按三个有效目标 token 求平均：
> $$
> \bar J
> =\frac{1.427}{3}
> \approx0.476.
> $$
> 任何一步降低正确 token 的概率，都会增大总 NLL；取 log 把概率乘积变成可累加的逐 token loss。

### 3.4 为什么没有 source-summary 标签也能训练 Encoder

训练图如下：

![[_assets/images/02-Seq2Seq端到端训练.png|900]]

*图 2：每个 Decoder 时间步产生一项 loss，梯度通过 Decoder、初始状态接口与 Encoder 端到端传播。图中下方目标 token 是 Teacher-Forced 输入。来源：[[Paper/架构学习/CS224n/resources/slides/cs224n-2026-lecture04-rnnlm.pdf#page=56|CS224N Lecture 4，PDF 第 56 页]]。*

梯度路径为：

$$
\text{target loss}
\to
\text{output projection}
\to
\text{Decoder}
\to
\text{bridge}
\to
\text{Encoder}.
$$

不需要人为规定“正确的 $z$ 应该是什么”。只要某种源表示能够提高正确目标序列的概率，反向传播就会推动 Encoder 学到这种表示。这就是端到端训练。

### 3.5 三个训练概念的分工

| 概念 | 回答的问题 |
| --- | --- |
| Target shifting | Decoder 输入与监督标签如何错位对齐？ |
| Teacher Forcing | 当前步输入真实前一 token，还是模型预测？ |
| BPTT | 梯度怎样沿展开后的 recurrent states 回传？ |

它们经常同时出现，但处于不同层次。


## 4. 推理：没有正确目标前缀时怎样生成

训练时有完整目标序列；推理时只有源序列。模型必须把自己的选择反馈给下一步，直到产生 `<EOS>` 或达到最大长度。

### 4.1 Autoregressive rollout

```text
z = Encoder(source_tokens)
state = Bridge(z)
prev = <BOS>
result = []

while prev != <EOS> and len(result) < max_length:
    state = RNNDecoder(state, Embed(prev))
    logits = OutputProjection(state)
    token = Decode(logits)
    result.append(token)
    prev = token
```

这里维护一条生成路径，`Decode(logits)` 可以执行 greedy 或 sampling。Beam search 需要改写外层循环，同时维护多条候选路径，见第 4.4 节。

### 4.2 Greedy decoding 与 Sampling

Greedy 每一步取当前最大概率 token：

$$
\tilde y_t
=
\arg\max_w
P(w\mid\tilde y_{<t},x).
$$

它快速、确定，但只保证每一步局部最优，不保证完整序列概率最高。

Sampling 则从当前分布采样：

$$
\tilde y_t
\sim
P(\cdot\mid\tilde y_{<t},x).
$$

它能产生更多样的输出，也会引入随机性。两者都属于自回归 rollout，区别只是每一步怎样从分布中选 token。

### 4.3 为什么逐步最大不等于整句最大

考虑一个两步玩具例子：

| 第一步候选 | $P(y_1\mid x)$ | 最佳结束概率 $P(\mathrm{EOS}\mid y_1,x)$ |         完整序列概率         |
| :---: | :-------------------: | :----------------------------------------: | :--------------------: |
|  `A`  |        $0.55$         |                   $0.60$                   | $0.55\times0.60=0.33$  |
|  `B`  |        $0.45$         |                   $0.90$                   | $0.45\times0.90=0.405$ |

Greedy 第一步会选择 `A`，但完整序列 `B <EOS>` 的概率更高。一次局部领先可能把搜索带进较差的后续分布。

### 4.4 Beam search：同时保留多个前缀

Beam search 在每一步保留分数最高的 $K$ 个前缀。常用累计 log-probability：

$$
S(y_{1:t})
=
\sum_{j=1}^{t}
\log P(y_j\mid y_{<j},x).
$$

每一步执行：

1. 用词表中的候选扩展当前前缀；
2. 把旧分数与新 token 的 log-probability 相加；
3. 在所有扩展结果中保留 top-$K$；
4. 将产生 `<EOS>` 的前缀放入完成集合；
5. 满足停止条件后返回最高分完成序列。

在上面的例子中，若 $K=2$，第一步会同时保留 `A` 和 `B`，第二步即可发现：

$$
\log0.45+\log0.90
>
\log0.55+\log0.60.
$$

当 $K=1$ 时，beam search 退化为 greedy。即使 $K>1$，它仍会剪掉暂时落后的前缀，因此只是近似搜索，不保证找到全局最优序列。

> [!note]- 实现接口：Beam search 需要维护什么？
> 第 4.1 节只有一份 `prev`、`state` 和 `result`；beam search 则为每条活跃候选维护 **prefix、累计 log-score、对应的 Decoder state**，并另存已完成的序列。
>
> 以 `A` 和 `B` 两个前缀为例，下一轮必须分别读取各自的最后一个 token，计算各自的下一步分布。扩展并选取 top-$K$ 后，需要按所选父候选同步重排或复制 state；不能让所有候选继续使用同一份状态。
>
> 生成 `<EOS>` 的候选停止扩展，后续比较使用约定的长度评分与停止规则。因此 beam search 包含**候选管理、状态更新和跨路径剪枝**，不能只替换单个 `Decode(logits)` 函数。概念流程可对照 [《动手学深度学习》：束搜索](https://zh.d2l.ai/chapter_recurrent-modern/beam-search.html)。

### 4.5 终止、长度偏置与安全边界

累计 log-probability 通常为负，序列越长累积项越多，直接比较可能偏好较短输出。实践中常使用长度归一化或 length penalty：

$$
S_{\mathrm{norm}}(y)
=
\frac{S(y)}{\operatorname{lp}(|y|)}.
$$

推理还需要 `max_length`，防止模型始终不生成 `<EOS>`。

### 4.6 Train–Inference discrepancy

| 阶段 | 第 $t$ 步输入 | 早期错误是否进入后续前缀 |
| --- | --- | --- |
| Teacher-Forced 训练 | 真实 $y_{t-1}$ | 否 |
| 自回归推理 | 模型预测 $\tilde y_{t-1}$ | 是 |

若正确开头是 `he hit`，模型却先生成 `she`，下一步实际计算：

$$
P(y_2\mid\texttt{she},x),
$$

而训练时常见的是：

$$
P(y_2\mid\texttt{he},x).
$$

因此错误可能逐步累积，Teacher-Forced NLL 与最终生成质量也不完全等价。


## 5. Fixed-vector Bottleneck：为什么需要 Attention

### 5.1 所有源信息只能通过一个接口

当前模型的数据流是：

$$
x_{1:N_{\mathrm{src}}}
\xrightarrow{\text{Encoder}}
\underbrace{z}_{\text{固定维度}}
\xrightarrow{\text{Decoder}}
y_{1:N_{\mathrm{tgt}}}.
$$

![[_assets/images/03-Seq2Seq瓶颈.png|900]]

*图 3：无论源句多长，全部源信息都必须先通过固定大小的最终 Encoder state，再进入 Decoder。来源：[[Paper/架构学习/CS224n/resources/slides/cs224n-2026-lecture04-rnnlm.pdf#page=58|CS224N Lecture 4，PDF 第 58 页]]。*

源序列越长，越多位置的信息要竞争同一个固定维度向量。困难不只是“维度可能太小”，还包括 Decoder 无法在不同生成步骤重新读取不同源位置。

### 5.2 早期源 token 到晚期目标 token 要走两段长链

若第一个源 token 要影响很晚的目标 token，信息必须经历：

1. 沿 Encoder 从早期位置传到最后状态 $z$；
2. 再沿 Decoder 从 $s_0$ 传到较晚目标位置。

即使 Encoder/Decoder 都换成 LSTM，信息接口仍只有固定数量的最终 states。门控可以改善两段递归链，但没有取消中间压缩。

### 5.3 每一步重复输入同一个 $z$ 仍是 fixed-vector

一种变体让 Decoder 每一步都读取 $z$：

$$
s_t
=
f_{\mathrm{dec}}
(s_{t-1},\operatorname{Concat}(X_{t-1}^{\mathrm{tgt}},z)).
$$

这能让条件信号更直接，却仍然只读取同一个压缩结果。

> [!important] “反复读取”不等于“按需读取”
> Fixed-vector 的核心限制不是多久看一次 $z$，而是不同源位置的信息已经在接口处被统一压缩。

### 5.4 Attention 改变的是 Encoder-Decoder 接口

Attention 保留全部 Encoder outputs：

$$
h_1^{\mathrm{enc}},\ldots,
h_{N_{\mathrm{src}}}^{\mathrm{enc}},
$$

并让 Decoder 在每个目标时间步得到不同的加权摘要：

$$
C_t
=
\sum_{i=1}^{N_{\mathrm{src}}}
A_{t,i}h_i^{\mathrm{enc}}.
$$

于是预测 `he`、`hit` 和 `pie` 时，可以关注不同的源位置。

> [!summary] 从 Seq2Seq 到 Attention
> - Fixed-vector：所有目标步共享一个源摘要 $z$；
> - Attention：每个目标步根据当前需要读取一组 source states；
> - 改变的是信息接口，不是条件概率分解 $P(y\mid x)$。


## 6. 工程实现：从单样本扩展到 Variable-length Batch

到这里，模型、训练、推理与瓶颈的主线已经完整。下面再处理 batch 带来的 padding、mask 与 shape，避免把存储对齐问题误当成 Seq2Seq 定义。

### 6.1 为什么需要 Padding

假设一个 batch 中有两条样本：

| 样本  | 源长度 | 目标长度（含 `<EOS>`） |
| :-: | :-: | :-------------: |
|  A  |  4  |        7        |
|  B  |  2  |        4        |

张量需要统一长度，因此短序列补 `<PAD>`：

```text
source A: x1 / x2 / x3    / x4
source B: x1 / x2 / <PAD> / <PAD>
```

Padding 只是存储对齐，不是真实序列内容，由此产生两个不同问题：

1. 源端：Encoder 不应把 `<PAD>` 当成新输入继续改变短序列状态；
2. 目标端：补出的 `<PAD>` 不应计入预测 loss。

### 6.2 源端长度决定从哪里取得 summary

对第 $b$ 条样本，正确摘要是：

$$
\boxed{
z^{(b)}
=
h_{N_{\mathrm{src}}^{(b)}}^{\mathrm{enc}}
}
$$

而不是统一取 padded 长度 $N_{\mathrm{src}}^{\max}$ 处的 state。常见方法包括：

- 向 RNN 提供真实长度；
- 使用 packed sequence；
- 对 state update 做显式 mask；
- 从最后一个有效位置 gather state。

> [!warning] Target loss mask 修复不了错误的源状态
> 若 Encoder 已经读取源端 `<PAD>` 并改变了 hidden state，传给 Decoder 的 $z$ 已经不对。之后忽略目标端 padding loss，不能还原源摘要。

### 6.3 目标端 mask 决定哪些位置进入 loss

定义目标有效位置：

$$
m_{b,t}^y
=
\mathbb{1}[t\le N_{\mathrm{tgt}}^{(b)}].
$$

Batch loss 通常按有效目标 token 平均：

$$
\boxed{
J_{\mathrm{batch}}
=-
\frac{
\sum_{b,t}m_{b,t}^y
\log P_\theta(y_{b,t}\mid y_{b,<t},x_b)
}{
\sum_{b,t}m_{b,t}^y
}
}
$$

| 特殊 token | 是否属于模型序列 | 是否通常作为 target 计入 loss |
| --- | --- | --- |
| `<BOS>` | 是，作为启动输入 | 否 |
| `<EOS>` | 是，表示真实结束 | 是 |
| `<PAD>` | 否，只用于对齐 | 否 |

### 6.4 Shape 来自计算链，而不是孤立背诵

设：

- batch size：$B$；
- 最大源长度：$N_{\mathrm{src}}$；
- 最大目标长度：$N_{\mathrm{tgt}}$；
- 源、目标 embedding 维度：$D_{\mathrm{emb,src}},D_{\mathrm{emb,tgt}}$；
- Encoder hidden size：$D_{\mathrm{enc}}$；
- Decoder hidden size：$D_{\mathrm{dec}}$；
- 目标词表大小：$V_{\mathrm{tgt}}$。

Batch-first 下：

| 张量 | Shape | 来源 |
| --- | --- | --- |
| `source_ids` | $[B,N_{\mathrm{src}}]$ | padding 后的源 token IDs |
| `source_mask` | $[B,N_{\mathrm{src}}]$ | 有效源位置 |
| `source_emb` | $[B,N_{\mathrm{src}},D_{\mathrm{emb,src}}]$ | 源 embedding lookup |
| `encoder_outputs` | $[B,N_{\mathrm{src}},D_{\mathrm{enc}}]$ | 每个源位置的 state |
| `source_summary` | $[B,D_{\mathrm{enc}}]$ | 每条样本最后有效 state |
| `decoder_init` | $[B,D_{\mathrm{dec}}]$ | bridge 输出 |
| `decoder_input_ids` | $[B,N_{\mathrm{tgt}}]$ | shift-right 目标输入 |
| `decoder_emb` | $[B,N_{\mathrm{tgt}},D_{\mathrm{emb,tgt}}]$ | 目标 embedding lookup |
| `decoder_states` | $[B,N_{\mathrm{tgt}},D_{\mathrm{dec}}]$ | 每个目标位置的 state |
| `logits` | $[B,N_{\mathrm{tgt}},V_{\mathrm{tgt}}]$ | 目标词表分数 |
| `target_mask` | $[B,N_{\mathrm{tgt}}]$ | 有效 target 位置 |

一条 shape 主线是：

$$
\boxed{
[B,N_{\mathrm{src}}]
\to[B,N_{\mathrm{src}},D_{\mathrm{emb,src}}]
\to[B,N_{\mathrm{src}},D_{\mathrm{enc}}]
\to[B,D_{\mathrm{enc}}]
\to[B,D_{\mathrm{dec}}]
\to[B,N_{\mathrm{tgt}},D_{\mathrm{dec}}]
\to[B,N_{\mathrm{tgt}},V_{\mathrm{tgt}}]
}
$$

本文后续 shape 均采用 batch-first，序列维位于 batch 维之后。


## 7. 定义边界与常见扩展

### 7.1 Seq2Seq、Encoder-Decoder 与 RNN 不是同义词

| 概念 | 最短定义 |
| --- | --- |
| Seq2Seq | 一条序列条件化地产生另一条序列 |
| Encoder-Decoder | 先编码输入条件，再由 Decoder 产生输出 |
| RNN | 一种递归更新状态的具体模型族 |
| Fixed-vector | Encoder-Decoder 之间只传固定数量的摘要状态 |

Transformer 也可以实现 Seq2Seq Encoder-Decoder；RNN 也可以用于分类、标注或普通语言模型。

### 7.2 换成 LSTM 后，Bridge 要处理两种状态

若两端都使用 LSTM，Encoder 最终状态包含：

$$
(h_{N_{\mathrm{src}}}^{\mathrm{enc}},
c_{N_{\mathrm{src}}}^{\mathrm{enc}}).
$$

Decoder 通常需要分别初始化：

$$
h_0^{\mathrm{dec}}
=g_h(h_{N_{\mathrm{src}}}^{\mathrm{enc}}),
\qquad
c_0^{\mathrm{dec}}
=g_c(c_{N_{\mathrm{src}}}^{\mathrm{enc}}).
$$

多层或双向 Encoder 还要明确层、方向和 hidden size 怎样映射。它们改变状态接口，不改变 $P(y\mid x)$ 的分解。

### 7.3 Encoder 可以双向，生成 Decoder 必须遵守因果性

源序列在生成前已经完整给定，因此 Encoder 可以同时读取左右上下文。自回归 Decoder 预测 $y_t$ 时只能读取目标前缀 $y_{<t}$，不能读取答案 $y_t$ 本身及更晚的目标 token；训练时也要通过 target shifting 等机制遵守这一约束。

### 7.4 Seq2Seq 与 Sequence Labeling

序列标注通常为每个输入位置预测标签：

$$
x_1,\ldots,x_N
\to
\ell_1,\ldots,\ell_N,
$$

输入输出大致等长并位置对齐。Seq2Seq 则允许不等长和重排，并显式依赖已生成的目标前缀。

### 7.5 Seq2Seq 不只用于机器翻译

| 任务 | Encoder 条件 | Decoder 输出 |
| --- | --- | --- |
| 机器翻译 | 源语言文本 | 目标语言文本 |
| 摘要 | 文档 | 摘要 |
| 对话 | 对话历史 | 下一轮回复 |
| 语音识别 | 声学特征 | 文本 token |
| 图像描述 | 图像特征 | 描述文本 |
| 代码生成 | 自然语言需求 | 程序 token |

Encoder 输入不一定是离散 token；只要能形成条件表示，就可以驱动序列 Decoder。

### 7.6 训练指标与生成指标不在同一层

训练直接优化 token-level NLL，也可以报告条件 perplexity：

$$
\operatorname{PPL}
=
\exp\left(
-\frac{1}{N_{\mathrm{tok}}}
\sum_{b,t}m_{b,t}^y
\log P(y_{b,t}\mid y_{b,<t},x_b)
\right).
$$

生成质量还可能用 BLEU、ROUGE、exact match、测试通过率或人工评价。NLL 更低不保证任务指标一定更高，因为生成结果还受搜索、长度策略和评价标准影响。


## 8. 常见混淆

| 错误说法 | 正确理解 |
| --- | --- |
| Encoder-Decoder 就是两个相同网络 | 两端可以有不同参数、层数、cell 与 hidden size |
| Encoder 最终 state 就是目标概率 | 还要经过 bridge、Decoder、词表投影和 softmax |
| `<BOS>` 是第一个正文 token | 它是启动输入，读取后才预测第一个正文 token |
| `<EOS>` 与 `<PAD>` 都是补位符 | `<EOS>` 是真实预测目标；`<PAD>` 只用于对齐 |
| Teacher Forcing 破坏了自回归建模 | 概率分解仍自回归，只是训练前缀来自数据 |
| Teacher Forcing 就是 BPTT | 前者决定前向输入，后者决定反向梯度计算 |
| Greedy 能找到概率最高的整句 | 它只做每一步局部选择 |
| Beam search 是精确搜索 | 它会剪枝，是近似搜索 |
| 最终 state 完全不依赖早期 token | 它在函数上依赖全部输入，困难在长路径和有限压缩 |
| LSTM 能消除 fixed-vector bottleneck | 它改善递归状态，未改变 Encoder-Decoder 接口 |
| 只 mask target loss 就处理了所有 padding | 源端最终 state 也必须停在真实长度处 |


## 9. 总结：按因果链重新串一次

### 9.1 建模链

$$
\boxed{
P(y\mid x)
=
\prod_{t=1}^{N_{\mathrm{tgt}}}
P(y_t\mid y_{<t},x)
}
$$

Seq2Seq Decoder 是以源序列为额外条件的自回归语言模型。

### 9.2 前向链

$$
\boxed{
x_{1:N_{\mathrm{src}}}
\xrightarrow{\text{Encoder}}
z
\xrightarrow{\text{bridge}}
s_0
\xrightarrow[\langle\mathrm{BOS}\rangle,y_{<t}]{\text{Decoder}}
P_t
}
$$

### 9.3 训练与推理链

| 阶段 | 已知内容 | Decoder 前缀 | 完整输出怎样得到 |
| --- | --- | --- | --- |
| 训练 | 源序列 + 完整目标序列 | shift-right 的真实目标 | 每个位置计算 NLL |
| 推理 | 只有源序列 | `<BOS>` 后接模型预测 | greedy、sampling 或 beam search |

### 9.4 局限与下一步

$$
\boxed{
\text{单个固定摘要 }z
\quad\Longrightarrow\quad
\text{源信息压缩与长路径瓶颈}
\quad\Longrightarrow\quad
\text{Attention 动态读取 source states}
}
$$

> [!important] 最终心智模型
> 1. **建模**：把 $P(y\mid x)$ 拆成一系列条件 next-token predictions；
> 2. **实现**：Encoder 产生源条件，Decoder 在该条件下从 `<BOS>` 生成到 `<EOS>`；
> 3. **训练**：用真实目标前缀和逐 token NLL 端到端更新整个系统；
> 4. **推理**：模型必须消费自己的预测，搜索完整输出序列；
> 5. **局限**：fixed-vector 接口迫使所有源信息先压入同一个摘要，由此引出 Attention。


## 建议学习顺序

1. 用法语→英语例子说明为什么源/目标不必等长或对齐；
2. 从条件链式法则写出 $P(y\mid x)$；
3. 沿 Encoder → $z$ → bridge → Decoder 走一遍前向；
4. 用 `he hit me` 手写 shift-right 的 input 与 target；
5. 从正确 token 概率乘积计算一次 sequence NLL；
6. 区分 target shifting、Teacher Forcing 与 BPTT；
7. 对照训练和推理的前缀来源；
8. 用两步反例解释 greedy 为什么不保证整句最优；
9. 从 fixed-vector bottleneck 推出 Attention 的动态读取；
10. 最后处理 padding、source length、target mask 与 batch shape。


## 自测问题

> [!todo]- 最小实践：用序列反转检查数据流
> 用小词表 `{A, B, C}` 构造长度 1–5 的源序列，目标是源序列反转后接 `<EOS>`，例如 `A B C → C B A <EOS>`。这用于检查机制，不用于评价真实翻译能力。
>
> 1. 手写这一样本的 Decoder input 与 target，检查两者错开一位。
> 2. 加入较短样本 `A B → B A <EOS>`，检查 source summary 来自最后有效位置，目标 `<PAD>` 不进入 loss，`<EOS>` 进入 loss。
> 3. 跑通单层 RNN Encoder–Decoder，先尝试拟合一个固定的小 batch，检查 loss 是否能明显下降。
> 4. 分别记录 Teacher-Forced 预测与从 `<BOS>` 开始的自由生成；只有后者用于判断整条序列是否正确。
>
> **完成后填写：**样本数与随机种子：____；关键 tensor shapes：____；训练前后 loss：____；自由生成成功/失败样例：____。本项是待完成实验，不能仅凭公式推导勾选。

1. Seq2Seq 为什么建模 $P(y\mid x)$ 而不是 $P(y)$？
2. 用链式法则展开一个三 token 目标序列的条件概率。
3. 为什么源长度和目标长度不需要相等？
4. `<BOS>` 与 `<EOS>` 分别承担什么职责？
5. 写出经典 RNN Encoder 的 embedding 与状态更新公式。
6. Encoder outputs 与 fixed-vector summary $z$ 有什么区别？
7. Bridge 为什么可能需要 projection？
8. 源序列如何在没有显式出现在 Decoder 单步公式时仍影响 $P_t$？
9. 给定目标正文 `A B C`，写出 Decoder input 与 target。
10. Target shifting、Teacher Forcing 与 BPTT 分别决定什么？
11. 给定正确 token 概率 $0.5,0.4,0.8$，sequence NLL 是多少？
12. 为什么 target loss 能端到端训练 Encoder？
13. 推理时为什么不能继续使用真实目标前缀？
14. 构造一个 greedy 局部最优但整句非最优的两步例子。
15. Beam width $K=1$ 等价于什么？Beam search 为什么仍不是精确搜索？
16. 为什么累计 log-probability 可能产生长度偏置？
17. Teacher-Forced NLL 与实际生成质量为什么不完全等价？
18. Fixed-vector bottleneck 不只是“向量维度太小”，还限制了什么？
19. 每一步都拼接同一个 $z$ 为什么仍不是按需读取？
20. Attention 怎样改变 Encoder-Decoder 的信息接口？
21. 为什么 source length/mask 与 target loss mask 不能互相替代？
22. 两端换成 LSTM 后，bridge 通常要处理哪些状态？


## 学习记录

- [ ] 已写出条件概率分解 $P(y\mid x)$
- [ ] 已沿贯穿翻译例子走完一次前向
- [ ] 已区分 Encoder outputs、$z$ 与 $s_t$
- [ ] 已手工构造 shift-right Decoder input 与 target
- [ ] 已从正确 token 概率计算 sequence NLL
- [ ] 已区分 Teacher Forcing、target shifting 与 BPTT
- [ ] 已比较训练与推理的前缀来源
- [ ] 已手算 greedy 与 beam search 反例
- [ ] 已解释 fixed-vector bottleneck 与 Attention 动机
- [ ] 已区分源端长度处理与目标端 loss mask
- [ ] 已完成一次 batch-first shape 检查
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前置章节 [[Paper/架构学习/基础/02-RNN.md|02-RNN]]、[[Paper/架构学习/基础/03-LSTM与GRU.md|03-LSTM与GRU]] 的联系：
- 与下一阶段 [[Paper/架构学习/基础/05-Attention.md|05-Attention]] 的联系：
