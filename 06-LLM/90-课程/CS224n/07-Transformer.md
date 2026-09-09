---
title: "CS224N 07 Attention 与 Transformer"
aliases:
  - "Transformers"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 7
date_text: "Week 3 Tue Jan 20"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
updated: 2026-09-09
---
# CS224N 07：Attention 与 Transformer

> [!abstract] 本节定位
> 从 RNN 的序列瓶颈过渡到 self-attention，按 shape 推导多头注意力、mask、位置表示和 Transformer 组件。

## 学习目标

- [ ] 推导 scaled dot-product attention 的每个 shape
- [ ] 区分 encoder、causal decoder 和 encoder-decoder
- [ ] 说明注意力的并行优势、二次复杂度与位置问题

## 知识笔记

> [!info] 课件范围
> 对应 Attention and Transformers PPT 第 14–70 页。正文从 seq2seq 的固定向量瓶颈出发，依次推导 encoder–decoder attention、self-attention、multi-head attention、位置编码、Transformer encoder/decoder 与复杂度。

## 1. 从 RNN 瓶颈到 Attention

传统 encoder–decoder 把整个源句压缩进一个固定向量。长句中：

- 早期信息需要经历很长递归路径；
- 单个向量容量有限；
- 解码器每一步都拿到同一个摘要。

Attention 允许解码器在每个目标时间步重新选择源序列信息。

## 2. Attention 是可学习的加权查表

给定 query $q$、keys $k_i$ 和 values $v_i$：

1. 计算 query 与每个 key 的相似度；
2. 将分数归一化为权重；
3. 对 values 做加权平均。

$$
e_i=\operatorname{score}(q,k_i),
$$

$$
\alpha_i
=
\frac{\exp(e_i)}
{\sum_j\exp(e_j)},
$$

$$
a
=
\sum_i\alpha_i v_i.
$$

### 在机器翻译中

- query：当前 decoder hidden state；
- key：每个 encoder hidden state；
- value：通常也是 encoder hidden state；
- 输出 $a_t$：当前目标词所需的源端摘要。

每个目标时间步有不同 attention 分布，模型可形成软对齐。

> [!note] Soft alignment
> 权重通常不是 one-hot。模型可以同时参考多个源位置，且整个过程可微。

## 3. Attention 的三个角色

将 key 与 value 分开后，可以把 attention 看作数据库查询：

- **Query**：现在想找什么；
- **Key**：每条记录如何被匹配；
- **Value**：匹配后真正读出的内容。

key 和 value 可以来自同一输入，但经过不同线性投影，因此匹配特征与内容特征不必相同。

## 4. Self-Attention

Self-attention 中 query、key、value 都由同一序列投影得到。

输入：

$$
X\in\mathbb{R}^{N\times D}.
$$

投影：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V.
$$

若单头维度为 $d_h$：

$$
Q,K,V\in\mathbb{R}^{N\times d_h}.
$$

分数：

$$
S
=
\frac{QK^\top}{\sqrt{d_h}}
\in\mathbb{R}^{N\times N}.
$$

归一化：

$$
A=\operatorname{softmax}(S)
\in\mathbb{R}^{N\times N}.
$$

输出：

$$
O=AV
\in\mathbb{R}^{N\times d_h}.
$$

### 行列语义

$$
A_{ij}
$$

表示第 $i$ 个 query token 对第 $j$ 个 key/value token 的权重：

- 行：谁在读取；
- 列：从谁读取。

## 5. 为什么除以 $\sqrt{d_h}$

若 query 与 key 各维独立、均值 0、方差 1，则点积：

$$
q^\top k=\sum_{r=1}^{d_h}q_rk_r
$$

的方差约为 $d_h$。

$d_h$ 大时 logits 绝对值变大，softmax 变尖，梯度容易进入接近 one-hot 的区域。除以 $\sqrt{d_h}$ 将方差缩回常数量级。

## 6. Mask

### 6.1 Padding mask

对 padding key 位置，将 logit 设为负无穷：

$$
S_{ij}\leftarrow-\infty.
$$

softmax 后权重为 0。

### 6.2 Causal mask

自回归位置 $i$ 不能读取未来 $j>i$：

$$
M_{ij}
=
\begin{cases}
0, & j\le i,\\
-\infty, & j>i.
\end{cases}
$$

$$
A=\operatorname{softmax}(S+M).
$$

> [!warning]
> Mask 必须在 softmax 前作用于 logits。softmax 后再乘 0 会破坏行和为 1，除非重新归一化。

## 7. Multi-Head Attention

对 $H$ 个 head：

$$
Q_h=XW_Q^{(h)},\quad
K_h=XW_K^{(h)},\quad
V_h=XW_V^{(h)}.
$$

$$
O_h
=
\operatorname{softmax}
\left(
\frac{Q_hK_h^\top}{\sqrt{d_h}}
\right)V_h.
$$

拼接：

$$
O
=
\operatorname{Concat}(O_1,\ldots,O_H)W_O.
$$

通常：

$$
D=Hd_h.
$$

### Batch shape

$$
X:[B,N,D],
$$

$$
Q,K,V:[B,H,N,d_h],
$$

$$
S,A:[B,H,N,N],
$$

$$
O:[B,H,N,d_h]
\to[B,N,D].
$$

多头并不是简单重复。不同投影让各 head 可学习句法关系、指代、局部搭配或位置模式等不同子空间。

## 8. Self-Attention 的优势与缺陷

### 优势

- 任意两个 token 的路径长度为 1；
- 训练时所有 token 可并行；
- 每个位置可动态选择上下文；
- 权重提供一定的关系可视化。

### 缺陷

- 本身不包含顺序；
- 分数矩阵是 $N\times N$；
- 对大数据和正则化较敏感；
- attention weight 不等于完整因果解释。

## 9. 位置表示

Self-attention 对输入排列是等变的。若不加入位置，模型无法区分相同 token 集合的不同顺序。

### 9.1 正弦位置编码

$$
PE(pos,2i)
=
\sin\left(
\frac{pos}{10000^{2i/D}}
\right),
$$

$$
PE(pos,2i+1)
=
\cos\left(
\frac{pos}{10000^{2i/D}}
\right).
$$

不同维度对应不同频率，可提供绝对位置，并允许模型通过线性组合近似相对位移关系。

### 9.2 Learned position embedding

为每个位置学习一个向量：

$$
X_0=E_{\text{token}}+E_{\text{position}}.
$$

优点是灵活；缺点是训练长度外的位置缺少直接参数。

后续长上下文课程还会介绍 RoPE 等相对位置方法。

## 10. Feed-Forward Network

每个 token 独立通过相同 MLP：

$$
\operatorname{FFN}(x)
=
W_2f(W_1x+b_1)+b_2.
$$

它不在 token 之间交换信息，token 交互由 attention 完成；FFN 在特征维上进行非线性变换。

典型中间维：

$$
D_{\text{ff}}>D.
$$

## 11. Residual 与 LayerNorm

### 11.1 Residual

$$
y=x+F(x).
$$

残差提供短梯度路径，使深层网络更易优化。相加要求 $F(x)$ 与 $x$ shape 相同。

### 11.2 LayerNorm

对单个 token 的特征维归一化：

$$
\mu
=
\frac{1}{D}\sum_{d=1}^{D}x_d,
$$

$$
\sigma^2
=
\frac{1}{D}\sum_{d=1}^{D}(x_d-\mu)^2,
$$

$$
\operatorname{LN}(x)
=
\gamma\odot
\frac{x-\mu}{\sqrt{\sigma^2+\epsilon}}
+\beta.
$$

LayerNorm 不依赖 batch 统计，适合变长序列。

## 12. Transformer Decoder Block

课件中的 decoder block 包含：

1. causal self-attention；
2. residual + LayerNorm；
3. feed-forward；
4. residual + LayerNorm。

堆叠多个 block 后：

$$
H^L:[B,N,D].
$$

语言模型头：

$$
\text{logits}=H^LW_{\text{vocab}}^\top
\in\mathbb{R}^{B\times N\times |V|}.
$$

训练可并行计算所有位置，但 causal mask 确保每个位置只用前缀。

## 13. Encoder 与 Encoder–Decoder

### Encoder

移除 causal mask，每个 token 双向读取上下文。适合理解、分类和抽取表示。

### Encoder–Decoder

- encoder：双向编码源序列；
- decoder causal self-attention：读取目标前缀；
- cross-attention：decoder state 作 query，encoder outputs 作 key/value。

Cross-attention shape：

$$
Q:[B,H,N_{\text{target}},d_h],
$$

$$
K,V:[B,H,N_{\text{source}},d_h],
$$

$$
A:[B,H,N_{\text{target}},N_{\text{source}}].
$$

## 14. 复杂度

标准 self-attention 的主要项：

$$
O(N^2D)
$$

并需要存储：

$$
O(HN^2)
$$

的 attention 权重或中间量。

FFN 复杂度约为：

$$
O(NDD_{\text{ff}}).
$$

序列较短、模型很宽时，线性投影和 FFN 可能占主导；序列很长时，$N^2$ 项占主导。

## 15. Transformer 解决了什么，又留下什么

### 解决

- RNN 的时间串行训练；
- 长依赖的路径长度；
- 固定向量 encoder bottleneck；
- 不同位置只能通过递归逐步通信。

### 留下

- 二次 attention 成本；
- 位置外推；
- 大规模数据和计算需求；
- 对分布外输入和事实可靠性的限制；
- attention 权重与真实推理机制之间的差距。

## 16. 小结

- Attention 是 query 对 key 匹配后读取 value 的可微查表。
- Self-attention 的行是读取者，列是被读取位置。
- 缩放项稳定 softmax，多头提供不同投影子空间。
- mask、位置表示、FFN、残差和 LayerNorm 共同构成 Transformer。
- Encoder、decoder 与 encoder-decoder 的主要差异在信息可见范围和 cross-attention。
- Transformer 缩短依赖路径并提高训练并行性，但长序列成本为二次量级。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[cs224n-2026-lecture05-transformers.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture05-transformers.pdf>) |
| 课程讲义 | [[cs224n-self-attention-transformers-2023_draft.pdf\|notes]] | [原始链接](<https://web.stanford.edu/class/cs224n/readings/cs224n-self-attention-transformers-2023_draft.pdf>) |
| 论文 / 阅读 | [[06-LLM/90-课程/CS224n/resources/readings/1706.03762-attention-is-all-you-need.pdf\|Attention Is All You Need]] | [原始链接](<https://arxiv.org/abs/1706.03762.pdf>) |
| 链接 | The Illustrated Transformer（仅在线） | [原始链接](<https://jalammar.github.io/illustrated-transformer/>) |
| 链接 | Transformer (Google AI blog post)（仅在线） | [原始链接](<https://ai.googleblog.com/2017/08/transformer-novel-neural-network.html>) |
| 论文 / 阅读 | [[06-LLM/90-课程/CS224n/resources/readings/1607.06450-layer-normalization.pdf\|Layer Normalization]] | [原始链接](<https://arxiv.org/pdf/1607.06450.pdf>) |
| 论文 / 阅读 | [[1802.05751-image-transformer.pdf\|Image Transformer]] | [原始链接](<https://arxiv.org/pdf/1802.05751.pdf>) |
| 论文 / 阅读 | [[1809.04281-music-transformer-generating-music-with-long-term-structure.pdf\|Music Transformer: Generating music with long-term structure]] | [原始链接](<https://arxiv.org/pdf/1809.04281.pdf>) |
| 论文 / 阅读 | [[jurafsky-and-martin-chapter-9-the-transformer.pdf\|Jurafsky and Martin Chapter 9 (The Transformer)]] | [原始链接](<https://web.stanford.edu/~jurafsky/slp3/9.pdf>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. Q 为 B,H,Nq,dh 且 K 为 B,H,Nk,dh 时分数 shape 是什么？
2. causal mask 应在 softmax 前还是后加入？
3. 没有位置信息时 self-attention 对排列有何性质？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
