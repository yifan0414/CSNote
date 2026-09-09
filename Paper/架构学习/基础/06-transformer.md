---
title: Transformer 基础知识与例题
aliases:
  - Transformer 完整基础讲义
tags:
  - video-mllm
  - transformer
  - tutorial
  - examples
type: learning-note
stage: 1
status: active
created: 2026-08-17
updated: 2026-09-09
---

> [!abstract] 学习目标
> 本讲义为 [[Paper/架构学习/Video-MLLM/01-transformer-练习题|Transformer 纸笔练习题]] 配套资料。读完后，应能从 shape 推导 self-attention，解释 mask、位置编码、Pre-LN DecoderBlock、训练与生成流程，并估算 attention 和 KV cache 的资源开销。

## 导航

- 学习路线：[[Paper/架构学习/Video-MLLM/01-transformer|Transformer 学习与实现]]
- 配套测试：[[Paper/架构学习/Video-MLLM/01-transformer-练习题|Transformer 纸笔练习题]]
- 前置速查：[[Paper/架构学习/Video-MLLM/00-shape-cheatsheet|Video MLLM Shape Cheatsheet]]
- 下一阶段：[[Paper/架构学习/Video-MLLM/02-vit|ViT]]

## 建议学习顺序

1. 先掌握符号、Linear、softmax、LayerNorm 和 residual。
2. 理解自回归语言模型、teacher forcing 和 causal mask 的动机。
3. 沿 shape 完整推导每个 head 内部的 attention 计算和完整 multi-head attention。
4. 将 attention、MLP、LayerNorm 和 residual 组合成 DecoderBlock。
5. 区分训练 forward、逐 token 生成和 KV cache。
6. 最后做复杂度与显存估算，再完成配套练习题。

---

# 一、统一符号与 Shape 思维

## 1.1 常用符号

| 符号 | 含义 |
| --- | --- |
| $B$ | batch size |
| $N$ | 序列中的 token 数 |
| $D$ | hidden dimension，也叫 model dimension |
| $H$ | query attention head 数 |
| $H_{KV}$ | Key/Value head 数；普通 MHA 中 $H_{KV}=H$ |
| $d_h$ | 每个 attention head 的维度 |
| $D_{ff}$ | MLP 中间层维度 |
| $L$ | Transformer block 数 |
| $V$ | 词表大小 |
| $N_q$ | query 序列长度 |
| $N_k$ | key/value 序列长度 |

普通 Multi-Head Attention 通常满足：

$$
D=H d_h.
$$

模型主干最常见的 hidden state shape 为：

$$
X\in\mathbb{R}^{B\times N\times D}.
$$

> [!important] Shape 推导原则
> 每次遇到一个算子，都先回答三个问题：输入 shape 是什么、运算发生在哪个维度、输出 shape 是什么。不要只记最终答案。

## 1.2 维度的语义

对于 $X[b,n,d]$：

- $b$ 选择 batch 中的第几个样本；
- $n$ 选择序列中的第几个 token；
- $d$ 选择该 token 表示中的第几个特征。

改变 $N$ 与改变 $D$ 的意义完全不同：

| 改变项 | 直接含义              | 对 attention 的主要影响               |
| --- | ----------------- | ------------------------------- |
| $N$ | token 变多或变少       | score 的两个序列轴随之变化，形成 $N\times N$ |
| $D$ | 每个 token 的表示变宽或变窄 | 投影矩阵、head 数或 $d_h$ 发生变化         |

## 1.3 Batch 矩阵乘法

矩阵乘法只收缩相邻的内积维度。例如：

$$
A\in\mathbb{R}^{B\times M\times K},\qquad
B\in\mathbb{R}^{B\times K\times N},
$$

则：

$$
AB\in\mathbb{R}^{B\times M\times N}.
$$

attention 中最关键的收缩维是 $d_h$：

$$
[B,H,N_q,d_h]\times[B,H,d_h,N_k]
\longrightarrow[B,H,N_q,N_k].
$$

> [!note]- 为什么 Attention 会收缩 $d_h$？
> 矩阵乘法的本质，就是沿着一个共同维度做内积，然后把这个维度求和消掉。Attention 中的“收缩维度”就是这个意思。
>
> ## 1. 从普通矩阵乘法开始
>
> 设
>
> $$
> A\in\mathbb{R}^{M\times K},\qquad
> B\in\mathbb{R}^{K\times N},
> $$
>
> 则 $C=AB$ 的 shape 为：
>
> $$
> C\in\mathbb{R}^{M\times N}.
> $$
>
> 其中每个元素都是一条长度为 $K$ 的内积：
>
> $$
> C_{ij}=\sum_{k=1}^{K}A_{ik}B_{kj}.
> $$
>
> 索引 $k=1,\ldots,K$ 被遍历并求和，因此 $K$ 这个维度被**收缩**，最后只保留 $M$ 和 $N$：
>
> $$
> (M,K)\times(K,N)\longrightarrow(M,N).
> $$
>
> ### 一个具体例子
>
> $$
> A=
> \begin{bmatrix}
> 1&2&3\\
> 4&5&6
> \end{bmatrix}\in\mathbb{R}^{2\times3},\qquad
> B=
> \begin{bmatrix}
> 7&8\\
> 9&10\\
> 11&12
> \end{bmatrix}\in\mathbb{R}^{3\times2}.
> $$
>
> 因此 $AB\in\mathbb{R}^{2\times2}$。例如左上角元素为：
>
> $$
> C_{11}=1\times7+2\times9+3\times11=58.
> $$
>
> 这里的 $3$ 不是结果中的一个维度，而是每个内积要遍历的长度：
>
> $$
> (2,\,\boxed{3})\times(\boxed{3},\,2)\longrightarrow(2,2).
> $$
>
> ## 2. Batch Matrix Multiplication
>
> 若有 $B$ 组独立的矩阵乘法，可以写成：
>
> $$
> A\in\mathbb{R}^{B\times M\times K},\qquad
> C\in\mathbb{R}^{B\times K\times N}.
> $$
>
> 最前面的 batch 维 $B$ 不参与矩阵乘法，它表示要分别计算：
>
> $$
> A_1C_1,\ A_2C_2,\ \ldots,\ A_BC_B.
> $$
>
> 每一组都是 $(M,K)\times(K,N)\to(M,N)$，所以整体 shape 为：
>
> $$
> (B,M,K)\times(B,K,N)\longrightarrow(B,M,N).
> $$
>
> batch 维原封不动地保留下来。
>
> ## 3. Attention 是同一种收缩
>
> 先忽略 batch 和 head 维，Attention 的核心乘法只是：
>
> $$
> [N_q,d_h]\times[d_h,N_k]\longrightarrow[N_q,N_k].
> $$
>
> 其中 $d_h$ 是每个 head 中 token 表示的特征维度。一个 query token 的表示为 $q_i\in\mathbb{R}^{d_h}$，一个 key token 的表示为 $k_j\in\mathbb{R}^{d_h}$。它们的相关性由点积给出：
>
> $$
> q_i^\top k_j=\sum_{r=1}^{d_h}q_{ir}k_{jr}.
> $$
>
> 例如 $d_h=128$ 时：
>
> $$
> q_i=\begin{bmatrix}
> q_{i1}\\
> q_{i2}\\
> \vdots\\
> q_{i128}
> \end{bmatrix},\qquad
> k_j=\begin{bmatrix}
> k_{j1}\\
> k_{j2}\\
> \vdots\\
> k_{j128}
> \end{bmatrix},
> $$
>
> 因此：
>
> $$
> q_i^\top k_j
> =q_{i1}k_{j1}+q_{i2}k_{j2}+\cdots+q_{i128}k_{j128}.
> $$
>
> $d_h$ 被求和掉后，原来的两个 $d_h$ 维向量只产生一个标量，这个标量就是 $\operatorname{score}_{ij}$。
> **<font color="#205867">这个标量表示第 $i$ 个 query token 与第 $j$ 个 key token 的相关性。</font>**
>
> 如果有 $N_q$ 个 query 和 $N_k$ 个 key，并且计算所有两两组合，就会得到：
>
> $$
> S=
> \begin{bmatrix}
> q_1^\top k_1&q_1^\top k_2&\cdots&q_1^\top k_{N_k}\\
> q_2^\top k_1&q_2^\top k_2&\cdots&q_2^\top k_{N_k}\\
> \vdots&\vdots&\ddots&\vdots\\
> q_{N_q}^\top k_1&q_{N_q}^\top k_2&\cdots&q_{N_q}^\top k_{N_k}
> \end{bmatrix}\in\mathbb{R}^{N_q\times N_k}.
> $$
>
> 行对应 query token，列对应 key token，每个元素对应一对 token 的相关性。
> 这就是 Attention Matrix：行表示 query，列表示 key。
> 例如 $N_q=3$、$N_k=4$ 时，关系矩阵为：
>
> $$
> \begin{bmatrix}
> q_1^\top k_1&q_1^\top k_2&q_1^\top k_3&q_1^\top k_4\\
> q_2^\top k_1&q_2^\top k_2&q_2^\top k_3&q_2^\top k_4\\
> q_3^\top k_1&q_3^\top k_2&q_3^\top k_3&q_3^\top k_4
> \end{bmatrix}\in\mathbb{R}^{3\times4}.
> $$
>
> 也就是说，每个 query 都会与全部 $N_k$ 个 key 比较一次，最后得到 $N_q\times N_k$ 个分数。
>
> ## 4. 为什么是 $QK^\top$
>
> 原始的 $Q$ 和 $K$ 都把每个 token 放在一行：
>
> $$
> Q=
> \begin{bmatrix}
> q_1^\top\\
> q_2^\top\\
> \vdots\\
> q_{N_q}^\top
> \end{bmatrix}\in\mathbb{R}^{N_q\times d_h},\qquad
> K=
> \begin{bmatrix}
> k_1^\top\\
> k_2^\top\\
> \vdots\\
> k_{N_k}^\top
> \end{bmatrix}\in\mathbb{R}^{N_k\times d_h}.
> $$
>
> 直接计算 $QK$ 时，两个中间维度是 $d_h$ 和 $N_k$，通常并不相等，因此不能相乘。转置 $K$ 的最后两个维度后：
>
> $$
> K^\top\in\mathbb{R}^{d_h\times N_k},\qquad
> QK^\top\in\mathbb{R}^{N_q\times N_k}.
> $$
>
> 于是 Scaled Dot-Product Attention 的 score 与权重为：
>
> $$
> S=\frac{QK^\top}{\sqrt{d_h}},\qquad
> A=\operatorname{softmax}(S),
> $$
>
> softmax 不改变 shape，只沿最后一个 key 维进行归一化。
>
> ## 5. 加回 batch 和 head 维
>
> 多 batch、多 head 时：
>
> $$
> Q\in\mathbb{R}^{B\times H\times N_q\times d_h},\qquad
> K\in\mathbb{R}^{B\times H\times N_k\times d_h}.
> $$
>
> 将 $K$ 的最后两个维度转置：
>
> $$
> K^\top\in\mathbb{R}^{B\times H\times d_h\times N_k}.
> $$
>
> 因此：
>
> $$
> [B,H,N_q,d_h]\times[B,H,d_h,N_k]
> \longrightarrow[B,H,N_q,N_k].
> $$
>
> 结果中的一个元素 $A_{b,h,i,j}$ 表示：第 $b$ 个样本、第 $h$ 个 head 中，第 $i$ 个 query token 对第 $j$ 个 key token 的注意力权重。
> 这里 $B$ 和 $H$ 只是两组独立计算的索引：
>
> - $B$：第几个样本；
> - $H$：第几个 attention head；
> - $N_q$：第几个 query token；
> - $N_k$：第几个 key token。
>
> 例如 $B=8$、$H=32$、$N_q=N_k=4096$、$d_h=128$ 时：
>
> $$
> Q:[8,32,4096,128],\qquad
> K^\top:[8,32,128,4096].
> $$
>
> $$
> \require{cancel}
> [8,32,\boxed{4096},\cancel{128}]
> \times
> [8,32,\cancel{128},\boxed{4096}]
> \longrightarrow
> [8,32,\boxed{4096},\boxed{4096}].
> $$
>
> 最后的 $4096\times4096$ 是所有 query-key 两两关系的矩阵，也是 self-attention 对序列长度呈 $O(N^2)$ 复杂度的原因。
>
> ## 核心直觉
>
> 矩阵乘法可以看作批量计算向量内积。Attention 中，$QK^\top$ 一次性计算所有 query token 与所有 key token 的点积；每次点积沿 $d_h$ 个特征求和，因此 $d_h$ 被收缩，最终留下的 $N_q\times N_k$ 正好表示“谁和谁进行了比较”：
>
> $$
> \boxed{[N_q,\,d_h]\times[d_h,\,N_k]\longrightarrow[N_q,\,N_k]}.
> $$
>
> $d_h$ 描述“拿哪些特征来比较”，而 $N_q\times N_k$ 描述“哪些 query 和哪些 key 进行了比较”。


## 1.4 Broadcasting

Broadcasting 允许 size 为 $1$ 的维度扩展到目标大小。设 attention score 为 $[B,H,N,N]$：

| Mask | 常见 shape | 广播方式 |
| --- | --- | --- |
| Key padding mask | $[B,1,1,N]$ | 复制到所有 head 和 query |
| Causal mask | $[1,1,N,N]$ | 复制到所有 batch 和 head |
| Batch-specific full mask | $[B,1,N,N]$ | 只复制到所有 head |

> [!warning] 常见错误
> “元素数量相同”不等于“维度语义相同”。$[B,N,H,d_h]$ 和 $[B,H,N,d_h]$ 虽含相同元素，但若直接做矩阵乘法，会得到完全不同的结果。

### 例题 1：Linear 后的 shape

设 $X\in\mathbb{R}^{3\times20\times64}$，Linear 的权重为 $W\in\mathbb{R}^{64\times128}$，bias 为 $b\in\mathbb{R}^{128}$。求输出 shape，并判断 token 数是否改变。

> [!success]- 解答
> Linear 只作用于最后一维：
> $$
> Y=XW+b\in\mathbb{R}^{3\times20\times128}.
> $$
> 输出 shape 为 $[3,20,128]$。$N=20$ 没有改变，只有 hidden dimension 从 $64$ 变为 $128$。

---

# 二、神经网络基础模块

## 2.1 Linear 层

对单个 token 表示 $x\in\mathbb{R}^{D_{in}}$，Linear 为：

$$
y=xW+b,
$$

其中：

$$
W\in\mathbb{R}^{D_{in}\times D_{out}},\qquad
b\in\mathbb{R}^{D_{out}}.
$$

参数量为：

$$
D_{in}D_{out}+D_{out}.
$$

对于整段输入 $X\in\mathbb{R}^{B\times N\times D_{in}}$，同一个 Linear 被独立应用于每个 token，输出为 $[B,N,D_{out}]$。

## 2.2 激活函数与 MLP

如果只有多个 Linear 层而没有非线性激活，多层线性变换仍可合并成一个线性变换。激活函数让网络能够表达非线性关系。

Transformer 中的 position-wise MLP 常写为：

$$
\operatorname{MLP}(x)
=W_2\,\sigma(W_1x+b_1)+b_2,
$$

其中：

$$
W_1\in\mathbb{R}^{D\times D_{ff}},\qquad
W_2\in\mathbb{R}^{D_{ff}\times D}.
$$

因此：

$$
[B,N,D]\rightarrow[B,N,D_{ff}]\rightarrow[B,N,D].
$$

“Position-wise”表示每个 token 使用同一套 MLP 参数独立计算。MLP 会混合 hidden/channel 维的信息，但不会直接混合不同 token。

## 2.3 Residual connection

Residual connection 的形式是：

$$
y=x+f(x).
$$

其作用包括：

- 保留一条接近恒等映射的信息通路；
- 改善深层网络中的梯度传播；
- 让每个子层学习对当前表示的增量修正。

残差相加要求：

$$
\operatorname{shape}(x)=\operatorname{shape}(f(x)).
$$

因此 Transformer block 的 attention 和 MLP 子层最终都会输出 $[B,N,D]$。

## 2.4 LayerNorm

LayerNorm 对每个 token 的完整特征向量独立做归一化，也就是沿 $[B,N,D]$ 的最后一轴一次性统计全部 $D$ 个特征。对 $x\in\mathbb{R}^{D}$：

$$
\mu=\frac{1}{D}\sum_{i=1}^{D}x_i,
$$

$$
\sigma^2=\frac{1}{D}\sum_{i=1}^{D}(x_i-\mu)^2,
$$

$$
\operatorname{LN}(x)
=\gamma\odot\frac{x-\mu}{\sqrt{\sigma^2+\epsilon}}+\beta.
$$

LayerNorm 不改变 shape：

$$
[B,N,D]\rightarrow[B,N,D].
$$

> [!note]- LayerNorm 为什么沿特征轴 $D$ 归一化？
> **一句话：**$X_{b,n,:}$ 是一个 token 的完整表示。LayerNorm 要稳定的是这个表示自身的数值尺度，因此只在它内部的 $D$ 个特征之间计算统计量，不混入其他样本或其他 token。
>
> ### 1. 到底归一化哪些数？
>
> 对 $X\in\mathbb{R}^{B\times N\times D}$，固定样本索引 $b$ 和 token 索引 $n$，取出：
>
> $$
> X_{b,n,:}
> =[X_{b,n,1},X_{b,n,2},\ldots,X_{b,n,D}]
> \in\mathbb{R}^{D}.
> $$
>
> LayerNorm 用这 $D$ 个数计算该 token 自己的均值和方差：
>
> $$
> \begin{aligned}
> \mu_{b,n}
> &=\frac{1}{D}\sum_{d=1}^{D}X_{b,n,d},\\
> \sigma_{b,n}^{2}
> &=\frac{1}{D}\sum_{d=1}^{D}
> (X_{b,n,d}-\mu_{b,n})^2.
> \end{aligned}
> $$
>
> 然后归一化同一个 token 的全部特征：
>
> $$
> \widehat{X}_{b,n,d}
> =\frac{X_{b,n,d}-\mu_{b,n}}
> {\sqrt{\sigma_{b,n}^{2}+\epsilon}},
> \qquad d=1,\ldots,D.
> $$
>
> 因此共有 $B\times N$ 个独立的归一化组，每组包含 $D$ 个数。例如 shape 为 $[2,3,4]$ 时，共有 $2\times3=6$ 组，每组归一化 $4$ 个特征。
>
> **注意：**“沿最后一轴归一化”不是只处理最后一个数 $X_{b,n,D}$，而是处理最后一轴上的全部 $D$ 个数。
>
> ### 2. 为什么选择 $D$，而不是 $B$ 或 $N$？
>
> | 统计轴 | 会把哪些值放在一起 | 结果 |
> | --- | --- | --- |
> | 特征轴 $D$ | 同一个 token 的全部特征 | 只稳定当前 token，不引入额外的信息混合 |
> | batch 轴 $B$ | 不同样本的对应特征 | 输出依赖 batch 的组成与大小 |
> | 序列轴 $N$ | 不同 token 的对应特征 | 输出依赖序列长度、padding 和其他位置 |
>
> Transformer 把 $X_{b,n,:}$ 当作最基本的表示单位。选择 $D$ 轴有三个直接好处：
>
> - 每个 token 使用自己的统计量，不受 batch 中其他样本影响；
> - 不同 token 的归一化互不依赖，兼容变长序列和 padding；
> - 不读取其他位置的统计量，因此不会绕过 causal mask 混入未来信息。
>
> Attention 负责在 mask 控制下有目的地混合 token；LayerNorm 只负责稳定数值尺度，不应额外执行一次不受 mask 控制的 token 混合。
>
> ### 3. LayerNorm 得到了什么？
>
> 忽略 $\gamma$ 和 $\beta$ 时，对每个 token 都有：
>
> $$
> \begin{aligned}
> \frac{1}{D}\sum_{d=1}^{D}\widehat{X}_{b,n,d}
> &=0,\\
> \frac{1}{D}\sum_{d=1}^{D}\widehat{X}_{b,n,d}^{\,2}
> &=\frac{\sigma_{b,n}^{2}}
> {\sigma_{b,n}^{2}+\epsilon}
> \approx1.
> \end{aligned}
> $$
>
> 这会减少 token 表示在整体偏移和尺度上的差异，使送入 Attention 或 MLP 的激活更稳定，并改善深层网络的优化与梯度传播。
>
> 但 LayerNorm **不会把特征变成正态分布**。例如：
>
> $$
> [0,0,0,10]
> \longrightarrow
> [-0.577,-0.577,-0.577,1.732].
> $$
>
> 结果的均值为 $0$、方差为 $1$，但分布形状仍然不是正态分布。均值和方差只控制中心与尺度，不能决定分布形状。
>
> 完整 LayerNorm 最后还会执行：
>
> $$
> Y_{b,n,d}
> =\gamma_d\widehat{X}_{b,n,d}+\beta_d,
> $$
>
> 其中 $\gamma_d$、$\beta_d$ 是逐特征的可学习参数，用来恢复模型需要的缩放和平移能力。因此最终输出也不要求均值严格为 $0$、方差严格为 $1$。
>
> “最后一轴”只是布局 $[B,N,D]$ 下的实现结果，真正应归一化的是 **feature axis**。如果布局改为 $[B,D,N]$，特征轴就不再是最后一轴。

> [!tip]- LayerNorm 与 Attention 缩放为什么都讨论方差？
> 两者都希望数值保持在稳定的 $O(1)$ 尺度，但处理对象不同：
>
> | 对比项 | LayerNorm | Attention 的 $1/\sqrt{d_h}$ |
> | --- | --- | --- |
> | 对象 | 单个 token 的 hidden vector | query-key 点积得到的 logit |
> | 操作 | 计算 $\mu,\sigma^2$，先中心化再缩放 | 只除以固定常数 $\sqrt{d_h}$ |
> | 目的 | 稳定 token representation | 抵消 $d_h$ 项求和造成的方差膨胀 |
>
> Attention 缩放不会计算或减去 score 的均值。即使 Q、K 的各分量已经是零均值、单位方差，点积仍满足：
>
> $$
> \operatorname{Var}(q^\top k)
> =\operatorname{Var}\left(\sum_{r=1}^{d_h}q_rk_r\right)
> \approx d_h.
> $$
>
> 因此还需要：
>
> $$
> \operatorname{Var}\left(
> \frac{q^\top k}{\sqrt{d_h}}
> \right)\approx1.
> $$
>
> LayerNorm 稳定 **token representation**，$1/\sqrt{d_h}$ 稳定 **attention logits**；它们不是重复操作，也都不要求张量服从 $\mathcal{N}(0,1)$。

它与 BatchNorm 的关键区别是：LayerNorm 不依赖 batch 内其他样本的统计量，因此适合变长序列和自回归模型。

## 2.5 Pre-LN 与 Post-LN

Pre-LN 在子层之前归一化：

$$
y=x+f(\operatorname{LN}(x)).
$$

Post-LN 在残差相加之后归一化：

$$
y=\operatorname{LN}(x+f(x)).
$$

现代大语言模型常采用 Pre-LN，因为深层训练通常更稳定。具体模型可能在最后再加一个 final norm。

### 例题 2：MLP 参数量

设 $D=512$，$D_{ff}=2048$，两个 Linear 都带 bias。求标准两层 MLP 的参数量。

> [!success]- 解答
> 第一层参数量为：
> $$
> 512\times2048+2048=1{,}050{,}624.
> $$
> 第二层参数量为：
> $$
> 2048\times512+512=1{,}049{,}088.
> $$
> 总参数量为：
> $$
> 2{,}099{,}712.
> $$
> MLP 的输入和输出仍是 $[B,N,512]$；中间激活是 $[B,N,2048]$。

---

# 三、自回归语言模型与 RNN 动机

## 3.1 自回归概率分解

语言模型要为序列 $x_1,\ldots,x_N$ 分配概率。根据概率链式法则：

$$
P(x_1,\ldots,x_N)
=\prod_{t=1}^{N}P(x_t\mid x_1,\ldots,x_{t-1})
=\prod_{t=1}^{N}P(x_t\mid x_{<t}).
$$

这意味着预测第 $t$ 个 token 时，只能使用它之前的 token。decoder-only Transformer 训练和推理都必须遵守这个因果约束。

## 3.2 Teacher forcing

训练时已经知道完整正确序列，因此可以把真实前缀作为每个位置的输入。以序列：

`<BOS> 我 喜欢 猫 <EOS>`

为例：

| 训练输入 | 监督目标 |
| --- | --- |
| `<BOS>` | `我` |
| `我` | `喜欢` |
| `喜欢` | `猫` |
| `猫` | `<EOS>` |

整体写成：

- `input = [<BOS>, 我, 喜欢, 猫]`
- `target = [我, 喜欢, 猫, <EOS>]`

输入和目标必须错开一个位置，否则当前位置会直接看到待预测答案。

## 3.3 RNN 的串行瓶颈

RNN 的 hidden state 满足：

$$
h_t=f(h_{t-1},x_t).
$$

计算 $h_t$ 前必须先得到 $h_{t-1}$，所以时间维上存在严格依赖链，难以并行处理整个序列。长距离信息还必须经过多个时间步传播。

Transformer 不使用时间递归。训练时可同时构造所有位置的 $Q,K,V$，并行计算所有 token 的表示。但是并行不代表可以看未来：因果限制由 causal mask 保证。

## 3.4 训练并行与推理串行

| 阶段  | 是否知道完整目标序列 | 主要计算方式                                 |
| :-- | :--------- | :------------------------------------- |
| 训练  | 是          | 一次 forward 并行得到所有位置的 next-token logits |
| 推理  | 否          | 每次生成一个 token，再把它加入上下文                  |

训练阶段并行的是“不同位置的计算”，而每个位置的可见信息仍受 causal mask 限制。推理阶段未来 token 尚不存在，因此天然需要逐步生成。

### 例题 3：Teacher forcing 对齐

给定序列 `天气 很 好 <EOS>`，假设使用 `<BOS>`。写出训练输入与目标，并说明会得到几个 next-token 监督位置。

> [!success]- 解答
> 输入为 `input = [<BOS>, 天气, 很, 好]`，目标为 `target = [天气, 很, 好, <EOS>]`。两者长度均为 $4$，因此得到 $4$ 个监督位置。

---

# 四、Attention 核心计算与 Shape 推导

## 4.1 Query、Key、Value 的直觉

对某个 query token：

- Query 表示“**我正在寻找什么**”；
- Key 表示“**我可以被怎样匹配**”；
- Value 表示“**如果关注我，应读取什么内容**”。

Query 与 Key 的相似度决定权重，权重再对 Value 做加权求和。

## 4.2 从输入到 Q、K、V

设：

$$
X\in\mathbb{R}^{B\times N\times D}.
$$

三个投影为：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V.
$$

实际实现通常并行存储 $H$ 个 head。先投影到 $D=Hd_h$，再 reshape 和 transpose：

$$
[B,N,D]\rightarrow[B,N,H,d_h]\rightarrow[B,H,N,d_h].
$$

因此，后续推导每个 head 内部的核心计算时仍保留 $H$ 轴：

$$
Q,K,V\in\mathbb{R}^{B\times H\times N\times d_h}.
$$

固定任意 head 索引 $h$ 后，就是该 head 内部的一次 attention 计算；不同 head 之间独立执行相同运算。

## 4.3 Score 矩阵

对每个 head：

$$
S=QK^\top.
$$

若 $Q,K\in\mathbb{R}^{B\times H\times N\times d_h}$，则：

$$
S\in\mathbb{R}^{B\times H\times N\times N}.
$$

其中 $S[b,h,i,j]$ 表示第 $b$ 个样本、第 $h$ 个 head 中，query 位置 $i$ 对 key 位置 $j$ 的匹配分数。

## 4.4 为什么除以 $\sqrt{d_h}$

若 query 和 key 各维近似独立、均值为 $0$、方差为 $1$，那么它们的点积：

$$
q\cdot k=\sum_{r=1}^{d_h}q_rk_r
$$

的方差会随 $d_h$ 增大。较大的 logits 会让 softmax 过度饱和，使梯度变小。因此使用：

$$
\widetilde{S}=\frac{QK^\top}{\sqrt{d_h}}.
$$

> [!note]- 概率论详细推导：为什么除以 $\sqrt{d_h}$？
> **结论：**点积由 $d_h$ 个近似独立的随机量相加而成。独立随机量之和的方差按 $d_h$ 增长，因此标准差按 $\sqrt{d_h}$ 增长。除以 $\sqrt{d_h}$ 能将 logits 的方差恢复到 $O(1)$，避免 softmax 过早饱和。
>
> ### 1. 概率论预备：独立随机变量之和
>
> 设 $X_1,\ldots,X_d$ 是随机变量，并令：
>
> $$
> S_d=\sum_{r=1}^{d}X_r.
> $$
>
> 期望具有线性性，不要求随机变量独立：
>
> $$
> \mathbb{E}[S_d]
> =\mathbb{E}\left[\sum_{r=1}^{d}X_r\right]
> =\sum_{r=1}^{d}\mathbb{E}[X_r].
> $$
>
> 方差的展开则包含协方差项：
>
> $$
> \begin{aligned}
> \operatorname{Var}(S_d)
> &=\mathbb{E}\left[
> \left(\sum_{r=1}^{d}(X_r-\mathbb{E}[X_r])\right)^2
> \right]\\
> &=\sum_{r=1}^{d}\operatorname{Var}(X_r)
> +2\sum_{1\le r<s\le d}\operatorname{Cov}(X_r,X_s).
> \end{aligned}
> $$
>
> 若 $X_1,\ldots,X_d$ 相互独立，则任意 $r\ne s$ 都有：
>
> $$
> \operatorname{Cov}(X_r,X_s)
> =\mathbb{E}[X_rX_s]-\mathbb{E}[X_r]\mathbb{E}[X_s]
> =0.
> $$
>
> 因此，若这些变量还具有相同方差 $\sigma^2$：
>
> $$
> \operatorname{Var}(S_d)=d\sigma^2,\qquad
> \operatorname{Std}(S_d)=\sqrt{d}\,\sigma.
> $$
>
> 例如，若 $X_1,\ldots,X_{100}$ 独立同分布且 $X_r\sim\mathcal{N}(0,1)$，正态变量之和仍然是正态变量，所以这里有精确结果：
>
> $$
> S_{100}=\sum_{r=1}^{100}X_r
> \sim\mathcal{N}(0,100),
> $$
>
> $$
> \operatorname{Std}(S_{100})=\sqrt{100}=10.
> $$
>
> $100$ 个单位尺度的随机波动相加后，典型大小约为 $10$，而不是 $100$。正负项之间会发生抵消，但总波动仍会随项数增加。
>
> 这里的关键是：**方差相加，但标准差是方差的平方根**。当 $\mathbb{E}[S_d]=0$ 时，均方根正好等于标准差：
>
> $$
> \sqrt{\mathbb{E}[S_d^2]}
> =\operatorname{Std}(S_d)
> =\sqrt{d}\,\sigma.
> $$
>
> 所以“典型波动尺度”按 $\sqrt d$ 增长，而不是按 $d$ 增长。
>
> ### 2. 随机游走直觉
>
> 令每一步 $X_r$ 以相同概率取 $+1$ 或 $-1$。此时：
>
> $$
> \mathbb{E}[X_r]=0,\qquad
> \operatorname{Var}(X_r)=1.
> $$
>
> 走 $d$ 步后的位置 $S_d=X_1+\cdots+X_d$ 满足：
>
> $$
> \mathbb{E}[S_d]=0,\qquad
> \operatorname{Var}(S_d)=d,\qquad
> \sqrt{\mathbb{E}[S_d^2]}=\sqrt d.
> $$
>
> 正负步长会互相抵消，所以走 $100$ 步后的典型距离约为 $10$，而不是 $100$。Attention 点积中的各维乘积相加具有相同的尺度规律。
>
> ### 3. 把结论应用到 $q^\top k$
>
> 对一个 query 和一个 key：
>
> $$
> s=q^\top k=\sum_{r=1}^{d_h}q_rk_r.
> $$
>
> 为了只研究维度带来的尺度变化，先作如下简化假设：
>
> 1. 对每个坐标 $r$，$q_r$ 与 $k_r$ 相互独立；
> 2. 不同坐标对 $(q_r,k_r)$ 之间相互独立；
> 3. 各分量均值为 $0$、方差为 $1$：
>
> $$
> \mathbb{E}[q_r]=\mathbb{E}[k_r]=0,\qquad
> \operatorname{Var}(q_r)=\operatorname{Var}(k_r)=1.
> $$
>
> 令每一维对点积的贡献为：
>
> $$
> Z_r=q_rk_r.
> $$
>
> ### 4. 逐步计算乘积 $Z_r=q_rk_r$ 的均值与方差
>
> 因为 $q_r$ 与 $k_r$ 独立，乘积的期望可以拆开：
>
> $$
> \begin{aligned}
> \mathbb{E}[Z_r]
> &=\mathbb{E}[q_rk_r]\\
> &=\mathbb{E}[q_r]\mathbb{E}[k_r]\\
> &=0.
> \end{aligned}
> $$
>
> 所以每一维的贡献有正有负，在总体上没有偏向。再由方差定义：
>
> $$
> \operatorname{Var}(Z_r)
> =\mathbb{E}[Z_r^2]-\bigl(\mathbb{E}[Z_r]\bigr)^2.
> $$
>
> 代入 $Z_r=q_rk_r$ 和 $\mathbb{E}[Z_r]=0$：
>
> $$
> \begin{aligned}
> \operatorname{Var}(Z_r)
> &=\mathbb{E}[q_r^2k_r^2]\\
> &=\mathbb{E}[q_r^2]\mathbb{E}[k_r^2].
> \end{aligned}
> $$
>
> 最后一步仍然使用了 $q_r$ 与 $k_r$ 的独立性。又因为：
>
> $$
> \mathbb{E}[X^2]
> =\operatorname{Var}(X)+\bigl(\mathbb{E}[X]\bigr)^2,
> $$
>
> 所以：
>
> $$
> \mathbb{E}[q_r^2]=1+0^2=1,\qquad
> \mathbb{E}[k_r^2]=1+0^2=1.
> $$
>
> 因此每一维乘积的方差为：
>
> $$
> \boxed{\operatorname{Var}(Z_r)=1}.
> $$
>
> 更一般地，若 $q_r$、$k_r$ 的方差分别是 $\sigma_q^2$、$\sigma_k^2$，且均值仍为 $0$，则：
>
> $$
> \operatorname{Var}(q_rk_r)=\sigma_q^2\sigma_k^2.
> $$
>
> ### 5. 计算完整点积的均值与方差
>
> 点积就是这些逐维贡献之和：
>
> $$
> s=q^\top k=\sum_{r=1}^{d_h}Z_r.
> $$
>
> 先计算均值：
>
> $$
> \mathbb{E}[s]
> =\sum_{r=1}^{d_h}\mathbb{E}[Z_r]
> =0.
> $$
>
> 再计算方差。由于不同坐标对 $(q_r,k_r)$ 相互独立，$Z_r$ 之间也相互独立，交叉协方差项为 $0$：
>
> $$
> \begin{aligned}
> \operatorname{Var}(s)
> &=\operatorname{Var}\left(\sum_{r=1}^{d_h}Z_r\right)\\
> &=\sum_{r=1}^{d_h}\operatorname{Var}(Z_r)\\
> &=\sum_{r=1}^{d_h}1\\
> &=d_h.
> \end{aligned}
> $$
>
> 所以：
>
> $$
> \boxed{
> \begin{aligned}
> \mathbb{E}[q^\top k]&=0,\\
> \operatorname{Var}(q^\top k)&=d_h,\\
> \operatorname{Std}(q^\top k)&=\sqrt{d_h}.
> \end{aligned}
> }.
> $$
>
> 这并不是说 $q^\top k$ 恒等于 $\sqrt{d_h}$，而是说它围绕 $0$ 的**典型波动尺度**约为 $\sqrt{d_h}$。增大的是方差，不是均值。
>
> 若 $Z_r$ 满足中心极限定理所需的条件，那么当 $d_h$ 较大时：
>
> $$
> \frac{\sum_{r=1}^{d_h}Z_r}{\sqrt{d_h}}
> \xrightarrow{d}\mathcal{N}(0,1),
> $$
>
> 因而可以近似写成：
>
> $$
> q^\top k\approx\mathcal{N}(0,d_h).
> $$
>
> 即使 $q_r$ 和 $k_r$ 本身服从标准正态分布，单个乘积 $q_rk_r$ 也不服从正态分布；这里的正态近似来自大量乘积项之和的中心极限定理。
>
> 不同维度下，未缩放点积的标准差为：
>
> | $d_h$ | $1$ | $16$ | $64$ | $128$ | $1024$ |
> | ---: | ---: | ---: | ---: | ---: | ---: |
> | $\operatorname{Std}(q^\top k)$ | $1$ | $4$ | $8$ | $\sqrt{128}\approx11.3$ | $32$ |
>
> ### 6. 方差增大为什么会使 softmax 饱和？
>
> softmax 对第 $i$ 个 logit 的定义为：
>
> $$
> p_i=\frac{e^{s_i}}{\sum_j e^{s_j}}.
> $$
>
> 当 logits 为 $[0.2,0.5,1.0]$ 时：
>
> $$
> \operatorname{softmax}([0.2,0.5,1.0])
> \approx[0.22,0.30,0.48].
> $$
>
> 若维度增大使相同的相对波动放大 $10$ 倍：
>
> $$
> \operatorname{softmax}([2,5,10])
> \approx[0.0003,0.0067,0.9930].
> $$
>
> 指数函数放大了 logits 的差距，使分布接近 one-hot。此时模型难以平滑地组合多个 value。softmax 的雅可比矩阵为：
>
> $$
> \frac{\partial p_i}{\partial s_j}
> =p_i(\delta_{ij}-p_j).
> $$
>
> 当各概率接近 $0$ 或 $1$ 时，雅可比矩阵中的多数元素接近 $0$，反向传播到 logits 的梯度容易变小。
>
> ### 7. 严格推出除以 $\sqrt{d_h}$ 后的方差
>
> 定义缩放后的分数：
>
> $$
> \widetilde{s}=\frac{q^\top k}{\sqrt{d_h}}.
> $$
>
> 对常数 $a$ 和随机变量 $X$：
>
> $$
> \begin{aligned}
> \operatorname{Var}(aX)
> &=\mathbb{E}\left[(aX-a\mathbb{E}[X])^2\right]\\
> &=a^2\mathbb{E}\left[(X-\mathbb{E}[X])^2\right]\\
> &=a^2\operatorname{Var}(X).
> \end{aligned}
> $$
>
> 取 $a=1/\sqrt{d_h}$，得到：
>
> $$
> \begin{aligned}
> \operatorname{Var}(\widetilde{s})
> &=\operatorname{Var}\left(\frac{q^\top k}{\sqrt{d_h}}\right)\\
> &=\frac{1}{d_h}\operatorname{Var}(q^\top k)\\
> &=\frac{1}{d_h}\cdot d_h\\
> &=1.
> \end{aligned}
> $$
>
> 因此：
>
> $$
> \boxed{
> \begin{aligned}
> q^\top k&\approx\mathcal{N}(0,d_h),\\
> \frac{q^\top k}{\sqrt{d_h}}&\approx\mathcal{N}(0,1).
> \end{aligned}
> }.
> $$
>
> 无论 $d_h$ 是 $64$、$128$ 还是 $256$，缩放后的 logits 都维持在相近的数值尺度。这是一种 **variance normalization（方差归一化）**。
>
> ### 8. 为什么不是除以 $d_h$？
>
> 若改为除以 $d_h$，则：
>
> $$
> \begin{aligned}
> \operatorname{Var}\left(\frac{q^\top k}{d_h}\right)
> &=\frac{1}{d_h^2}\operatorname{Var}(q^\top k)\\
> &=\frac{1}{d_h},\\
> \operatorname{Std}\left(\frac{q^\top k}{d_h}\right)
> &=\frac{1}{\sqrt{d_h}}
> \longrightarrow0.
> \end{aligned}
> $$
>
> 随着 $d_h$ 增大，所有 logits 都趋近于 $0$，softmax 因而趋近于均匀分布：
>
> $$
> \left[\frac{1}{N_k},\frac{1}{N_k},\ldots,\frac{1}{N_k}\right].
> $$
>
> 除以 $\sqrt{d_h}$ 恰好避免两个极端：既不会因 logits 尺度过大而太尖锐，也不会因尺度趋近于 $0$ 而太平坦。
>
> 核心推导链条为：
>
> $$
> \boxed{
> \begin{gathered}
> \operatorname{Var}(q_rk_r)=1\\
> \Downarrow\\
> \operatorname{Var}\left(\sum_{r=1}^{d_h}q_rk_r\right)=d_h\\
> \Downarrow\\
> \operatorname{Var}\left(\frac{q^\top k}{\sqrt{d_h}}\right)=1.
> \end{gathered}
> }.
> $$
>
> 缩放不会改变 tensor shape，只改变 score 的数值范围。实际模型中的 Q/K 分量不一定严格独立、零均值且单位方差，因此上述等式是用于解释设计动机的理想化推导；在存在相关性时，还会出现协方差项。但核心目的不变：抵消点积尺度随 head dimension 增长的趋势。


## 4.5 Softmax 的维度

对固定的 query 位置 $i$，要在所有 key 位置 $j$ 上归一化：

$$
A_{ij}
=\frac{\exp(\widetilde{S}_{ij})}
{\sum_{j'=1}^{N}\exp(\widetilde{S}_{ij'})}.
$$

因此 softmax 沿 score 的最后一维，也就是 key 维进行。每个 query 对所有可见 key 的权重之和为 $1$：

$$
\sum_{j=1}^{N}A_{ij}=1.
$$

## 4.6 Context

attention 权重对 Value 加权：

$$
C=AV.
$$

Shape 为：

$$
[B,H,N,N]\times[B,H,N,d_h]
\longrightarrow[B,H,N,d_h].
$$

这一步才真正把其他 token 的信息聚合到每个 query token 中。

## 4.7 每个 Head 内的 Attention 计算（保留 $H$ 维）

从数学上看，每个 head 都独立执行一次 scaled dot-product attention。实际实现不会逐个循环计算，而是把 $H$ 个 head 放进同一个张量中并行处理。因此，下面的 shape 始终保留 $H$ 轴；固定任意 head 索引 $h$ 后，才得到某一个 head 内部的计算。

> [!important] $H$ 轴表示并行的独立计算
> 在计算 attention score 和 context 时，不同 head 之间不会交换信息。它们只是在同一个张量中并行执行相同的运算；各 head 的结果要到后续 concat 和 output projection 时才会合并。

设已经完成 Q/K/V 投影和 head 拆分：

$$
Q\in\mathbb{R}^{B\times H\times N_q\times d_h},
$$

$$
K,V\in\mathbb{R}^{B\times H\times N_k\times d_h}.
$$

对于固定的样本 $b$ 和 head $h$，核心计算只是：

$$
Q_{b,h}\in\mathbb{R}^{N_q\times d_h},\qquad
K_{b,h},V_{b,h}\in\mathbb{R}^{N_k\times d_h}.
$$

$B$ 和 $H$ 都是批量计算的前导维度；真正发生矩阵乘法的是最后两个轴。

### 第一步：转置 Key

只交换 $K$ 的最后两个轴，batch 轴和 head 轴保持不变：

$$
K:[B,H,N_k,d_h]
\longrightarrow
K^T:[B,H,d_h,N_k].
$$

### 第二步：计算所有 query–key 分数

$$
\underbrace{[B,H,N_q,d_h]}_Q
\times
\underbrace{[B,H,d_h,N_k]}_{K^T}
\longrightarrow
\underbrace{[B,H,N_q,N_k]}_S.
$$

$d_h$ 是内积维，在矩阵乘法中被收缩；$N_q$ 和 $N_k$ 分别成为 score 矩阵的行轴和列轴：

$$
S=\frac{QK^T}{\sqrt{d_h}}
\in\mathbb{R}^{B\times H\times N_q\times N_k}.
$$

其中：

$$
S_{b,h,i,j}
=\frac{q_{b,h,i}^Tk_{b,h,j}}{\sqrt{d_h}},
$$

表示第 $b$ 个样本、第 $h$ 个 head 中，query $i$ 与 key $j$ 的匹配分数。

### 第三步：加入 Mask

设 additive mask $M$ 可以广播到 $[B,H,N_q,N_k]$，则：

$$
\widehat S=S+M
\in\mathbb{R}^{B\times H\times N_q\times N_k}.
$$

Mask 只改变部分 score 的数值，不改变 tensor shape，也不会让不同 head 之间发生信息混合。

### 第四步：沿 key 维做 Softmax

$$
A=\operatorname{softmax}(\widehat S,\ \mathrm{dim}=-1)
\in\mathbb{R}^{B\times H\times N_q\times N_k}.
$$

最后一维是 key 轴，因此对固定的 $b,h,i$：

$$
\sum_{j=1}^{N_k}A_{b,h,i,j}=1.
$$

也就是说，每个样本、每个 head、每个 query 都有一组独立的 key 权重。

### 第五步：对 Value 加权求和

$$
\underbrace{[B,H,N_q,N_k]}_A
\times
\underbrace{[B,H,N_k,d_h]}_V
\longrightarrow
\underbrace{[B,H,N_q,d_h]}_C.
$$

这里收缩的是 key 维 $N_k$；query 维 $N_q$ 和 head 维 $H$ 都会保留：

$$
C=AV
\in\mathbb{R}^{B\times H\times N_q\times d_h}.
$$

对单个位置展开就是：

$$
C_{b,h,i,:}
=\sum_{j=1}^{N_k}A_{b,h,i,j}V_{b,h,j,:}.
$$

完整 shape 数据流为：

$$
\begin{gathered}
Q:[B,H,N_q,d_h],\qquad
K,V:[B,H,N_k,d_h]\\
K\xrightarrow{\;\text{转置最后两个轴}\;}
K^{\mathsf T}:[B,H,d_h,N_k]\\
\xrightarrow{\;QK^T/\sqrt{d_h}\;}
S:[B,H,N_q,N_k]\\
\xrightarrow{\;+M\;}
\widehat S:[B,H,N_q,N_k]\\
\xrightarrow{\;\operatorname{softmax}_{N_k}\;}
A:[B,H,N_q,N_k]\\
\xrightarrow{\;AV\;}
C:[B,H,N_q,d_h].
\end{gathered}
$$

因此，每个 head 内部都执行同一个核心公式：

$$
\operatorname{Attention}(Q,K,V)
=\operatorname{softmax}\left(
\frac{QK^T}{\sqrt{d_h}}+M
\right)V.
$$

其中 $M$ 是 additive mask：允许的位置加 $0$，禁止的位置加 $-\infty$。Multi-head attention 会在此基础上进一步合并 $H$ 个 head，并执行 output projection。

### 例题 4：固定一个 Head 的 Attention 手算

固定某个样本 $b$ 和 head $h$，设该 head 内：

$$
Q=K=\begin{bmatrix}1\\2\end{bmatrix},\qquad
V=\begin{bmatrix}10\\30\end{bmatrix},\qquad d_h=1.
$$

使用 causal mask，求两个位置的 context。

> [!success]- 解答
> 未加 mask 的 score 为：
> $$
> QK^\top=
> \begin{bmatrix}
> 1&2\\
> 2&4
> \end{bmatrix}.
> $$
> 因为 $\sqrt{d_h}=1$，缩放不改变数值。加 causal mask 后：
> $$
> \widetilde{S}=
> \begin{bmatrix}
> 1&-\infty\\
> 2&4
> \end{bmatrix}.
> $$
> 第 $1$ 行 softmax 为 $[1,0]$，所以：
> $$
> c_1=10.
> $$
> 第 $2$ 行 softmax 权重为：
> $$
> \left[
> \frac{e^2}{e^2+e^4},
> \frac{e^4}{e^2+e^4}
> \right].
> $$
> 因此：
> $$
> c_2=\frac{10e^2+30e^4}{e^2+e^4}.
> $$

---

# 五、Mask：控制哪些信息可见

Attention 先为每一对 query 和 key 计算分数：

$$
S=\frac{QK^\top}{\sqrt{d_h}}
\in\mathbb{R}^{B\times H\times N_q\times N_k}.
$$

固定样本 $b$ 和 head $h$ 后，$S_{b,h,:,:}$ 就是一张 $N_q\times N_k$ 的表：

- 行 $i$：第 $i$ 个 query；
- 列 $j$：第 $j$ 个 key；
- 元素 $S_{ij}$：query $i$ 对 key $j$ 的关注分数。

**Mask 的作用，就是在这张表上删除不允许使用的 query–key 连接。** 它不改变 $Q/K/V$ 的 shape，只改变哪些 score 能进入 softmax。

> [!important] 先建立一个核心直觉
> Mask 回答的是：“对当前 query，这个 key 是否可见？”
>
> - causal mask：屏蔽**未来 key**；
> - padding mask：屏蔽**无效的 `<PAD>` key**。
>
> 两者解决的是不同问题，不是二选一。

## 5.1 Mask 如何作用在 Attention 中

先用二值矩阵 $A$ 描述“是否可见”：

$$
A_{ij}=
\begin{cases}
1,&\text{key }j\text{ 对 query }i\text{ 可见},\\
0,&\text{key }j\text{ 对 query }i\text{ 不可见}.
\end{cases}
$$

实际计算时，通常把它转换成 additive mask：

$$
M_{ij}=
\begin{cases}
0,&A_{ij}=1,\\
-\infty,&A_{ij}=0.
\end{cases}
$$

然后沿 key 维做 softmax：

$$
P=\operatorname{softmax}(S+M,\ \mathrm{dim}=-1),
\qquad
C=PV.
$$

完整数据流可以记成：

$$
\begin{gathered}
S
\xrightarrow{\text{加上 }M}
\widetilde{S}=S+M\\
\widetilde{S}
\xrightarrow{\text{沿 key 维 softmax}}
P=\operatorname{softmax}(\widetilde{S},\ \mathrm{dim}=-1)\\
P
\xrightarrow{\text{乘 }V}
C=PV.
\end{gathered}
$$

因为 $e^{-\infty}=0$，被屏蔽位置的 attention weight 会变为 $0$。Mask 必须在 softmax **之前**应用；如果先 softmax 再把某些权重清零，非法位置已经占用了概率质量，剩余合法权重之和将不再是 $1$。

> [!note] 数值实现
> 实际代码可能使用数据类型能表示的极小值，而不是真正的 $-\infty$；也可能直接调用 `masked_fill` 或框架提供的 attention 接口。数学含义相同。

## 5.2 Causal mask：不能看未来

自回归模型预测当前位置之后的 token 时，query $i$ 只能读取当前及更早的 key：

$$
j\le i.
$$

当 $N_q=N_k=4$ 时，二值可见性矩阵为：

$$
A^{\text{causal}}=
\begin{bmatrix}
1&0&0&0\\
1&1&0&0\\
1&1&1&0\\
1&1&1&1
\end{bmatrix}.
$$

行表示 query，列表示 key。因此：

- 第 $1$ 个 query 只能看第 $1$ 个 key；
- 第 $3$ 个 query 可以看第 $1$～$3$ 个 key；
- 上三角区域对应“未来”，必须被屏蔽。

对应的 additive mask 为：

$$
M^{\text{causal}}_{ij}=
\begin{cases}
0,&j\le i,\\
-\infty,&j>i.
\end{cases}
$$

所有样本和所有 head 通常共享同一套因果规则，所以常见 shape 是：

$$
[1,1,N_q,N_k].
$$

## 5.3 Padding mask：不能读取占位 token

batch 中的序列长度可能不同，需要用 `<PAD>` 补齐到相同长度：

```text
序列 1：[我, 喜欢, 小, 猫]
序列 2：[你, 好, <PAD>, <PAD>]
```

补齐后，两条序列的 key 有效性向量分别是：

$$
A^{\text{padding}}=
\begin{bmatrix}
1&1&1&1\\
1&1&0&0
\end{bmatrix}
\in\mathbb{R}^{B\times N_k}.
$$

这里 $1$ 表示真实 token，$0$ 表示 `<PAD>`。对第二条序列来说，**无论 query 位于哪一行，第 $3$、$4$ 列都不能被读取**。因此它不是一张随 query 改变的下三角矩阵，而是一把对所有 query 共用的“key 列屏蔽尺”。

例如，某个 query 的原始 score 为：

$$
[2,1,5,4].
$$

屏蔽后再做 softmax：

$$
[2,1,-\infty,-\infty]
\xrightarrow{\operatorname{softmax}}
[0.731,0.269,0,0].
$$

这样 context 就只会聚合真实 token 的 value。

Key padding mask 从 $[B,N_k]$ 显式扩维后，常见 shape 为：

$$
[B,1,1,N_k].
$$

- $B$：每个样本的有效长度可能不同；
- 第一个 $1$：同一 mask 广播给所有 head；
- 第二个 $1$：同一 key 有效性向量广播给所有 query；
- $N_k$：逐列标记 key 是否有效。

> [!warning] Key padding 与 padding query 不要混淆
> Attention padding mask 的首要任务是阻止任何 query 读取 padding **key**。如果 query 本身位于 `<PAD>` 位置，它仍可能产生输出；训练时通常通过忽略 padding target、清零相应输出等方式，使这些位置不影响 loss。
>
> Batch 中的不同样本本来就是分别计算 Attention 的，不会跨样本互相读取。Padding mask 带有 $B$ 维，只是因为每个样本的 `<PAD>` 位置可能不同。

## 5.4 两种 mask 的区别与 shape

| 对比项 | Causal mask | Key padding mask |
| --- | --- | --- |
| 屏蔽什么 | 当前 query 之后的未来 key | 序列中的 `<PAD>` key |
| 是否随 query 改变 | 是 | 否，同一样本的所有 query 共用一组有效 key |
| 是否随样本改变 | 通常否 | 通常是 |
| 常见原始形式 | $[N_q,N_k]$ 下三角矩阵 | $[B,N_k]$ key 有效性向量 |
| 常见广播 shape | $[1,1,N_q,N_k]$ | $[B,1,1,N_k]$ |
| 典型用途 | 自回归 attention | batch 中存在 padding |

### 什么是 Broadcasting

Broadcasting（广播）允许两个 shape 不完全相同、但彼此兼容的张量进行逐元素运算。它不会改变运算的数学含义，而是把 size 为 $1$ 的轴**视为重复使用**，从而在概念上扩展到目标大小；框架通常不需要真的复制这些数据。

判断两个 shape 能否广播时，要**从右向左对齐**各个轴。每一对轴至少满足一个条件：

1. 两个轴的 size 相同；
2. 其中一个轴的 size 为 $1$；
3. 某个张量缺少该轴，此时将缺失的前导轴视为 $1$。

只要有一对轴既不相等、也都不为 $1$，就不能广播。更一般的介绍见 [[#1.4 Broadcasting]]。

在 Attention 中，mask 要与 score 做逐元素相加。三者的常见 shape 为：

$$
\begin{aligned}
\operatorname{shape}(S)
&=[B,H,N_q,N_k],\\
\operatorname{shape}\!\left(M^{\text{causal}}\right)
&=[1,1,N_q,N_k],\\
\operatorname{shape}\!\left(M^{\text{padding}}\right)
&=[B,1,1,N_k].
\end{aligned}
$$

以 key padding mask 为例：

$$
\underbrace{[B,H,N_q,N_k]}_{\text{score}}
+
\underbrace{[B,1,1,N_k]}_{\text{key padding mask}}
\longrightarrow
[B,H,N_q,N_k].
$$

两个 size 为 $1$ 的轴分别扩展为 $H$ 和 $N_q$。若原始二维 mask 记为 $m^{\text{padding}}\in\mathbb{R}^{B\times N_k}$，那么广播后：

$$
\widehat{M}^{\text{padding}}_{b,h,i,j}
=m^{\text{padding}}_{b,j}.
$$

因此，对固定样本 $b$，同一组 key 屏蔽规则会被所有 head 和所有 query 共用。

Causal mask 的广播过程则是：

$$
\underbrace{[B,H,N_q,N_k]}_{\text{score}}
+
\underbrace{[1,1,N_q,N_k]}_{\text{causal mask}}
\longrightarrow
[B,H,N_q,N_k].
$$

前两个 size 为 $1$ 的轴扩展为 $B$ 和 $H$。若原始二维 mask 记为 $m^{\text{causal}}\in\mathbb{R}^{N_q\times N_k}$，那么广播后：

$$
\widehat{M}^{\text{causal}}_{b,h,i,j}
=m^{\text{causal}}_{i,j}.
$$

因此，所有样本、所有 head 共用同一张因果可见性矩阵。

> [!warning] Broadcasting 只检查 shape，不理解轴的语义
> 原始 padding mask 的 shape 是 $[B,N_k]$。它与四维 score 右对齐时会被视为 $[1,1,B,N_k]$，其中 $B$ 错误地落在 query 轴上。因此应先显式扩维：
> $$
> [B,N_k]\longrightarrow[B,1,1,N_k].
> $$
> 即使某次计算中恰好有 $B=N_q$、数值上能够广播，其语义仍然是错误的。

## 5.5 合并 causal mask 与 padding mask

当两种约束同时存在时，一个 key 只有同时满足以下条件才可见：

1. 它不是 padding key；
2. 它不位于当前 query 的未来。

若使用二值可见性矩阵，就做逻辑与：

$$
A=A^{\text{causal}}\land A^{\text{padding}}.
$$

若使用 additive mask，就直接相加：

$$
M=M^{\text{causal}}+M^{\text{padding}}.
$$

对于 `[你, 好, <PAD>, <PAD>]`，合并后的二值可见性为：

$$
A=
\begin{bmatrix}
1&0&0&0\\
1&1&0&0\\
1&1&0&0\\
1&1&0&0
\end{bmatrix}.
$$

- 第 $1$、$2$ 行遵守因果约束；
- 第 $3$、$4$ 列始终为 $0$，因为它们是 padding key；
- 第 $3$、$4$ 行是 padding query，其输出需要在后续忽略或清零。

> [!warning] 避免整行全部被屏蔽
> 如果某个 query 对应的一整行都是 $-\infty$，softmax 可能产生 NaN。实现时应保证有效 query 至少能看到一个 key，并单独处理 padding query。

> [!warning] 不同 API 的布尔约定可能相反
> Hugging Face 中常见的 `attention_mask` 使用 `1=有效 token、0=padding`；部分 PyTorch 接口则使用 `True=需要屏蔽`。不要只凭变量名判断，应查看具体接口文档。

## 5.6 到底使用哪种 mask

| 场景 | Causal mask | Padding mask | 原因 |
| --- | --- | --- | --- |
| Decoder-only 训练，batch 内有 padding | 使用 | 使用 | 既不能看未来，也不能读取 `<PAD>` |
| Decoder-only 训练，所有序列等长且无 padding | 使用 | 不需要 | 只需防止偷看未来 |
| 双向 Transformer Encoder，如 BERT | 不使用 | 有 padding 时使用 | 可以看左右上下文，但不应读取 `<PAD>` |
| Encoder–Decoder 的 Decoder self-attention | 使用 | 有 padding 时使用 | 与自回归 Decoder 相同 |
| Decoder 到 Encoder 的 cross-attention | 通常不使用 | 屏蔽 Encoder 中的 padding key | Decoder 可以读取全部有效 Encoder token |

> [!summary] Decoder-only 记忆规则
> 先用 causal mask 防止“看未来”；如果 batch 中存在 `<PAD>`，再叠加 key padding mask。

### 例题 5：Mask broadcasting

设 score shape 为 $[8,12,128,128]$。判断下列 mask 是否能广播，并说明语义：

1. $[8,1,1,128]$
2. $[1,1,128,128]$
3. $[8,128]$

> [!success]- 解答
> Broadcasting 只比较 shape，并不理解 $B$、$H$、$N_q$、$N_k$ 的语义。它从右向左对齐维度，每对维度必须相等，或其中一个为 $1$。
>
> 1. $[8,1,1,128]$ 可以广播：
>    ```text
>    score: [8, 12, 128, 128]
>    mask:  [8,  1,   1, 128]
>    ```
>    batch 维的 $8$ 相等，head 维的 $1$ 广播为 $12$，query 维的 $1$ 广播为 $128$，key 维的 $128$ 相等。它表示每个样本各有一个长度为 $128$ 的 key 有效性向量，然后将该向量共享给该样本的所有 head 和 query。这是典型 key padding mask。
>
> 2. $[1,1,128,128]$ 可以广播：
>    ```text
>    score: [8, 12, 128, 128]
>    mask:  [1,  1, 128, 128]
>    ```
>    两个前导 $1$ 分别广播到 $8$ 个样本和 $12$ 个 head。该 mask 保存一张完整的 $N_q\times N_k$ 可见性表，并让所有样本、所有 head 共用。所有样本都遵守同一因果规则，所以这是 causal mask 的典型 shape。
>
> 3. $[8,128]$ 不能直接按 $[B,N_k]$ 的预期广播。从右向左对齐后：
>    ```text
>    score: [8, 12, 128, 128]
>    mask:  [1,  1,   8, 128]
>    ```
>    mask 中的 $8$ 被对齐到了 query 维，而不是 batch 维。因为 $8$ 与 $128$ 不相等，且二者都不是 $1$，所以广播失败。应先显式扩维：
>    $$
>    [8,128]\longrightarrow[8,1,1,128].
>    $$
>    PyTorch 中可写为 `mask[:, None, None, :]`。

---

# 六、Multi-Head Attention 与 Cross-Attention

## 6.1 为什么使用多个 head

单个 attention 分布只能在一个表示子空间中建立匹配。多个 head 可以并行学习不同关系，例如局部依赖、长距离依赖、语法关系或指代关系。

不同 head 是否真的形成可解释的固定功能，不应当作硬性保证；核心是模型拥有多个独立的 attention 子空间。

## 6.2 Multi-Head Self-Attention 的完整 shape

Multi-head attention 将 $D$ 维表示拆成 $H$ 个 $d_h$ 维子空间，并在每个 head 中独立执行一次 scaled dot-product attention。设：

$$
X\in\mathbb{R}^{B\times N\times D},\qquad D=Hd_h.
$$

### 第一步：Q/K/V 投影

使用三个 $D\to D$ 的线性投影：

$$
W_Q,W_K,W_V\in\mathbb{R}^{D\times D}.
$$

Shape 推导为：

$$
\underbrace{[B,N,D]}_X
\times
\underbrace{[D,D]}_{W_Q,W_K,W_V}
\longrightarrow
\underbrace{[B,N,D]}_{Q_{raw},K_{raw},V_{raw}}.
$$

即：

$$
Q_{raw}=XW_Q,\quad K_{raw}=XW_K,\quad V_{raw}=XW_V,
$$

$$
Q_{raw},K_{raw},V_{raw}\in\mathbb{R}^{B\times N\times D}.
$$

### 第二步：拆分 head

$$
[B,N,D]
\xrightarrow{\;D=Hd_h\;}
[B,N,H,d_h]
\xrightarrow{\;\text{交换 }N,H\text{ 轴}\;}
[B,H,N,d_h].
$$

所以：

$$
Q,K,V\in\mathbb{R}^{B\times H\times N\times d_h}.
$$

这里的 reshape 只是把最后一个 $D$ 维拆成 $H\times d_h$；随后交换轴，是为了让 batch 和 head 成为批量矩阵乘法的前导维度。

### 第三步：每个 head 独立计算 score

只转置 $K$ 的最后两个轴：

$$
K:[B,H,N,d_h]
\longrightarrow
K^{\mathsf T}:[B,H,d_h,N].
$$

因此：

$$
\underbrace{[B,H,N,d_h]}_Q
\times
\underbrace{[B,H,d_h,N]}_{K^{\mathsf T}}
\longrightarrow
\underbrace{[B,H,N,N]}_S.
$$

前导的 $B,H$ 维被保留，每个样本的每个 head 都独立完成一次 $[N,d_h]\times[d_h,N]$ 的矩阵乘法：

$$
S=\frac{QK^{\mathsf T}}{\sqrt{d_h}}
\in\mathbb{R}^{B\times H\times N\times N}.
$$

### 第四步：加入 Mask 并做 Softmax

Mask $M$ 先广播到 $[B,H,N,N]$：

$$
\widehat S=S+M
\in\mathbb{R}^{B\times H\times N\times N}.
$$

$$
A=\operatorname{softmax}(\widehat S,\ \mathrm{dim}=-1)
\in\mathbb{R}^{B\times H\times N\times N}.
$$

Softmax 沿最后的 key 维进行，不会合并不同样本、head 或 query。

### 第五步：每个 head 聚合 Value

$$
\underbrace{[B,H,N,N]}_A
\times
\underbrace{[B,H,N,d_h]}_V
\longrightarrow
\underbrace{[B,H,N,d_h]}_C.
$$

$$
C=AV\in\mathbb{R}^{B\times H\times N\times d_h}.
$$

这里收缩的是 key 维 $N$；输出中的 $N$ 仍然是 query 维。

### 第六步：合并所有 head

$$
[B,H,N,d_h]
\xrightarrow{\;\text{交换 }H,N\text{ 轴}\;}
[B,N,H,d_h]
\xrightarrow{\;Hd_h=D\;}
[B,N,D].
$$

记合并后的张量为：

$$
C_{\text{concat}}\in\mathbb{R}^{B\times N\times D}.
$$

### 第七步：Output projection

设：

$$
W_O\in\mathbb{R}^{D\times D},\qquad b_O\in\mathbb{R}^{D}.
$$

则：

$$
Y=C_{concat}W_O+b_O\in\mathbb{R}^{B\times N\times D}.
$$

Output projection 让来自不同 head 的信息重新在线性层中混合，并确保输出能够与 residual 主干相加。

完整 shape 数据流为：

$$
\begin{gathered}
X:[B,N,D]\\
\xrightarrow{\;W_Q,W_K,W_V\;}
Q_{raw},K_{raw},V_{raw}:[B,N,D]\\
\xrightarrow{\;\text{拆成 }H\text{ 个 head}\;}
Q,K,V:[B,H,N,d_h]\\
\xrightarrow{\;QK^{\mathsf T}/\sqrt{d_h}\;}
S:[B,H,N,N]\\
\xrightarrow{\;+M\;}
\widehat S:[B,H,N,N]\\
\xrightarrow{\;\operatorname{softmax}_{N_k}\;}
A:[B,H,N,N]\\
\xrightarrow{\;AV\;}
C:[B,H,N,d_h]\\
\xrightarrow{\;\text{transpose + concat}\;}
C_{\text{concat}}:[B,N,D]\\
\xrightarrow{\;W_O\;}
Y:[B,N,D].
\end{gathered}
$$

> [!summary] 逐 Head 计算与完整 Multi-Head Attention 的区别
> 第 $4.7$ 节描述的是每个 head 内部的 attention 运算，并用 $H$ 轴将这些独立运算并行表示。完整的 Multi-Head Attention 还包括 Q/K/V 投影、拆分 head、将各 head 的 $d_h$ 维结果拼接回 $D=Hd_h$，以及通过 output projection 混合不同 head 的信息。

## 6.3 Q/K/V/O 投影参数量

若四个 Linear 都是 $D\to D$ 且带 bias，则总参数量为：

$$
4(D^2+D).
$$

head 数改变通常不会改变这四个投影的总参数量，因为它只是把 $D$ 重新拆成 $H\times d_h$。

## 6.4 Self-attention 与 Cross-attention

Self-attention 的 Q/K/V 来自同一序列，所以 query 和 key 长度相同：

$$
S_{self}\in\mathbb{R}^{B\times H\times N\times N}.
$$

Cross-attention 中，Q 来自 query 序列，K/V 来自另一序列：

$$
Q\in\mathbb{R}^{B\times H\times N_q\times d_h},
$$

$$
K,V\in\mathbb{R}^{B\times H\times N_k\times d_h},
$$

所以：

$$
S_{cross}\in\mathbb{R}^{B\times H\times N_q\times N_k}.
$$

score 的倒数第二维永远对应 query，最后一维永远对应 key。

## 6.5 Encoder 与 decoder attention

| 类型 | 可见范围 | 常见用途 |
| --- | --- | --- |
| Encoder bidirectional self-attention | 每个位置可看全部有效输入 | 表示理解、编码完整输入 |
| Decoder causal self-attention | 每个位置只能看当前及过去 | 自回归 next-token prediction |
| Cross-attention | query 读取另一组 key/value | Encoder-Decoder、部分多模态架构 |

### 例题 6：完整 shape 与参数量

设 $B=2,N=6,D=12,H=3,d_h=4$，Q/K/V/O 四个 Linear 都带 bias。

1. 写出拆头后的 Q/K/V、score、context 和最终输出 shape。
2. 计算四个 Linear 的总参数量。

> [!success]- 解答
> Shape 链路为：
>
> | Tensor | Shape |
> | --- | --- |
> | $X$ | $[2,6,12]$ |
> | $Q,K,V$ | $[2,3,6,4]$ |
> | score | $[2,3,6,6]$ |
> | context | $[2,3,6,4]$ |
> | concat | $[2,6,12]$ |
> | output | $[2,6,12]$ |
>
> 每个 Linear 的参数量为：
> $$
> 12\times12+12=156.
> $$
> 四个 Linear 总计：
> $$
> 4\times156=624.
> $$

### 例题 7：Cross-attention shape

设 $B=2,H=4,d_h=8,N_q=5,N_k=7$。求 Q/K/V、score 与 context shape。

> [!success]- 解答
> $$
> Q:[2,4,5,8],\qquad K,V:[2,4,7,8].
> $$
> $$
> \text{score}:[2,4,5,7],\qquad \text{context}:[2,4,5,8].
> $$
> 每个 query 对 $7$ 个 key 归一化，所以 softmax 沿最后一维进行。

---

# 七、位置信息

## 7.1 为什么必须加入位置

如果没有任何位置信息，self-attention 主要根据 token 内容建立关系。对同一组 token 进行排列，attention 会以对应方式重排输出，却无法仅凭内容可靠地区分“谁先谁后”。

语言含义高度依赖顺序，因此模型必须获得位置信息。

## 7.2 Learned absolute position embedding

设 token embedding 为：

$$
E_{tok}\in\mathbb{R}^{B\times N\times D},
$$

位置表为：

$$
P\in\mathbb{R}^{N_{max}\times D}.
$$

选取前 $N$ 个位置并广播到 batch：

$$
H^{(0)}=E_{tok}+P_{1:N}\in\mathbb{R}^{B\times N\times D}.
$$

优点是简单、位置表示可学习；限制是通常受训练时最大长度 $N_{max}$ 约束。

## 7.3 Sinusoidal position encoding

原始 Transformer 使用固定正弦位置编码：

$$
\operatorname{PE}(pos,2i)
=\sin\left(\frac{pos}{10000^{2i/D}}\right),
$$

$$
\operatorname{PE}(pos,2i+1)
=\cos\left(\frac{pos}{10000^{2i/D}}\right).
$$

不同通道对应不同频率，使位置具有多尺度表示。它不增加可训练参数，并可计算训练长度之外的位置，但长度外推效果仍取决于模型和训练方式。

## 7.4 RoPE 概览

> [!quote] RoPE 原论文
> *“RoPE encodes the absolute position with a rotation matrix and meanwhile incorporates the explicit relative position dependency in self-attention formulation.”*
>
> — Jianlin Su, Yu Lu, Shengfeng Pan, Ahmed Murtadha, Bo Wen, and Yunfeng Liu, [*RoFormer: Enhanced Transformer with Rotary Position Embedding*](https://arxiv.org/abs/2104.09864), arXiv:2104.09864 (2021).


Rotary Position Embedding 不直接把位置向量加到 hidden state，而是对 Q/K 的二维通道对进行位置相关旋转。可抽象写为：

$$
q_m'=R_mq_m,\qquad k_n'=R_nk_n.
$$

二者内积为：

$$
(q_m')^\top k_n'=q_m^\top R_m^\top R_n k_n,
$$

其中 $R_m^\top R_n$ 与相对位置 $n-m$ 有关，因此 attention score 能自然包含相对位置信息。


> [!important] Shape 不变
> 无论使用 absolute embedding、sinusoidal encoding 还是 RoPE，通常都不会改变 $B$、$N$、$D$。位置方法改变的是表示数值和注入位置，而不是 token 数。

### 例题 8：位置与 shape

token ids 为 $[4,128]$，embedding dimension 为 $512$。加入 learned position embedding 后 shape 是什么？如果把序列截断到 $64$ 个 token，哪些 attention shape 会变化？

> [!success]- 解答
> token embedding 和 position embedding 相加前后均为 $[4,128,512]$。截断后 hidden state 变为 $[4,64,512]$；若 $H=8,d_h=64$，Q/K/V 变为 $[4,8,64,64]$，score 变为 $[4,8,64,64]$。hidden dimension $D=512$ 不变。

---

# 八、Pre-LN DecoderBlock

## 8.1 Block 的两个核心子层

一个标准 decoder block 包含：

1. causal multi-head self-attention：在 token 之间传递信息；
2. position-wise MLP：在每个 token 内混合和变换通道信息。

两者分别解决“token 间通信”和“单 token 非线性计算”。只使用其中一个都无法得到完整 Transformer block 的能力。

## 8.2 Pre-LN 公式

给定：

$$
X\in\mathbb{R}^{B\times N\times D},
$$

attention 子层为：

$$
U=X+\operatorname{MHA}_{causal}(\operatorname{LN}_1(X)),
$$

MLP 子层为：

$$
Y=U+\operatorname{MLP}(\operatorname{LN}_2(U)).
$$

每一步 shape 都保持不变：

$$
X,U,Y\in\mathbb{R}^{B\times N\times D}.
$$

LayerNorm 的参数通常不共享，$\operatorname{LN}_1$ 和 $\operatorname{LN}_2$ 是两个独立模块。

## 8.3 Dropout 的常见位置

训练小模型时可能在以下位置加入 dropout：

- attention 权重之后；
- attention output projection 之后、残差相加之前；
- MLP 输出之后、残差相加之前；
- embedding 或 position embedding 之后。

Dropout 训练时随机置零部分激活，推理时关闭。它不改变 tensor shape。

## 8.4 堆叠多个 block

设第 $\ell$ 层输出为 $H^{(\ell)}$：

$$
H^{(\ell)}
=\operatorname{DecoderBlock}_{\ell}(H^{(\ell-1)}),
\qquad \ell=1,\ldots,L.
$$

所有层都保持主干 shape $[B,N,D]$，但每层参数通常独立。最后常加 final LayerNorm：

$$
H^{final}=\operatorname{LN}_f(H^{(L)}).
$$

### 例题 9：Block shape 检查

某 DecoderBlock 输入为 $[2,64,256]$，attention 输出为 $[2,64,256]$，MLP 中间激活为 $[2,64,1024]$，MLP 最终输出为 $[2,64,256]$。哪些张量可以直接做 residual addition？

> [!success]- 解答
> 输入可以与 attention 最终输出相加，因为二者都是 $[2,64,256]$。attention 残差结果可以与 MLP 最终输出相加，因为二者也是 $[2,64,256]$。MLP 中间激活 $[2,64,1024]$ 不能直接与主干相加，它必须先经过第二个 Linear 投影回 $D=256$。

---

# 九、完整 Decoder-only Transformer

## 9.1 从 token ids 到 hidden states

输入 token ids：

$$
T\in\{0,\ldots,V-1\}^{B\times N}.
$$

通过词嵌入表：

$$
E\in\mathbb{R}^{V\times D},
$$

查表得到：

$$
H_{tok}\in\mathbb{R}^{B\times N\times D}.
$$

加入位置信息后：

$$
H^{(0)}=H_{tok}+H_{pos}.
$$

若使用 RoPE，位置操作主要作用在每层 attention 的 Q/K 上，而不是在输入处简单相加。

## 9.2 经过 $L$ 个 DecoderBlock

$$
H^{(L)}
=\operatorname{Block}_{L}\circ\cdots\circ
\operatorname{Block}_{1}(H^{(0)}),
$$

且：

$$
H^{(L)}\in\mathbb{R}^{B\times N\times D}.
$$

## 9.3 Vocabulary projection

将每个位置的 hidden state 投影到词表：

$$
Z=H^{final}W_U+b_U,
$$

其中：

$$
W_U\in\mathbb{R}^{D\times V},\qquad
Z\in\mathbb{R}^{B\times N\times V}.
$$

$Z[b,t,v]$ 是样本 $b$、位置 $t$ 对词表 token $v$ 的未归一化 logit。

有些模型会让 output projection 与 token embedding 权重共享，即 weight tying。这样可减少参数量，但两处仍承担不同的数据流职责。

## 9.4 Next-token probability

对词表维做 softmax：

$$
P(x_{t+1}=v\mid x_{\le t})
=\frac{e^{Z_{t,v}}}{\sum_{v'=1}^{V}e^{Z_{t,v'}}}.
$$

注意这里的 softmax 沿词表维 $V$，不同于 attention 中沿 key 维做 softmax。

## 9.5 为什么一次训练 forward 能预测所有位置

causal mask 保证位置 $t$ 只依赖合法前缀。虽然所有位置同时计算，但每个位置的条件分布仍符合自回归分解。因此一次 forward 可以得到 $N$ 个位置的 next-token logits：

$$
Z\in\mathbb{R}^{B\times N\times V}.
$$

这正是 Transformer 相比时间递归模型的训练并行优势。

### 例题 10：端到端 shape

设 $B=4,N=32,D=256,L=6,V=10{,}000$。写出 token ids、embedding、每层主干和 logits 的 shape。

> [!success]- 解答
> | Stage | Shape |
> | --- | --- |
> | Token ids | $[4,32]$ |
> | Token/position hidden | $[4,32,256]$ |
> | 每个 DecoderBlock 输出 | $[4,32,256]$ |
> | Final hidden | $[4,32,256]$ |
> | Vocabulary logits | $[4,32,10{,}000]$ |
>
> $L=6$ 表示同 shape 的主干依次经过 $6$ 个参数独立的 block；它不会让 tensor 多出一个层维。

---

# 十、训练目标、Loss 与梯度

## 10.1 Cross-entropy loss

设目标 token 为 $y_{b,t}$，对应预测分布为 $p_{b,t}$，单位置负对数似然为：

$$
\ell_{b,t}=-\log p_{b,t}(y_{b,t}).
$$

对所有有效位置求平均：

$$
\mathcal{L}
=\frac{\sum_{b,t}m_{b,t}\ell_{b,t}}
{\sum_{b,t}m_{b,t}},
$$

其中 $m_{b,t}\in\{0,1\}$ 表示该 target 是否有效。padding target 对应 $m_{b,t}=0$。

## 10.2 Padding loss 与 attention padding mask 不同

二者解决不同问题：

| 机制 | 防止的问题 |
| --- | --- |
| Attention padding mask | 有效 query 读取 padding key |
| Loss ignore mask | padding target 产生训练梯度 |

通常两者都需要。只屏蔽 attention 并不能自动阻止 padding 位置进入 loss。

## 10.3 Teacher forcing 的训练数据流

完整流程为：

$$
\text{input ids }[B,N]
\rightarrow\text{hidden }[B,N,D]
\rightarrow\text{logits }[B,N,V]
\rightarrow\text{targets }[B,N]
\rightarrow\mathcal{L}.
$$

第 $t$ 个 logits 与错位后的第 $t$ 个 target 配对。

## 10.4 Loss 曲线

训练正常时，loss 通常总体下降，但 mini-batch 噪声会造成短期波动。需要警惕：

- loss 长期不降：学习率、target 对齐、mask 或数据可能有问题；
- loss 突然变成 NaN：数值溢出、全 mask 行、学习率过高等；
- 训练 loss 很低但生成极差：可能存在信息泄漏、评估流程不一致或过拟合。

## 10.5 Gradient norm

全局梯度范数常定义为：

$$
\lVert g\rVert_2
=\sqrt{\sum_{p}\lVert\nabla_p\mathcal{L}\rVert_2^2}.
$$

观察重点：

- 持续极大或突然爆炸：可能学习率过高或训练不稳定；
- 长期接近 $0$：可能梯度消失、参数未参与计算或错误 detach；
- 偶尔出现尖峰：需结合 loss 和 batch 内容判断，不一定是 bug。

Gradient clipping 可限制梯度范数，但不应掩盖数据、mask 或公式错误。

### 例题 11：Loss 对齐

输入是 `input = [<BOS>, A, B]`，目标是 `target = [A, B, <EOS>]`。模型输出 logits shape 为 $[1,3,V]$。分别说明三个位置在预测什么。

> [!success]- 解答
> 第 $1$ 个 logits 使用 `<BOS>` 预测 `A`；第 $2$ 个 logits 使用前缀 `<BOS>, A` 预测 `B`；第 $3$ 个 logits 使用前缀 `<BOS>, A, B` 预测 `<EOS>`。三个位置可在同一次 masked forward 中并行得到。

---

# 十一、自回归生成与 KV Cache

## 11.1 基本生成流程

给定 prompt，decoder-only 生成流程为：

1. 将当前上下文转换为 token ids；
2. 运行 causal Transformer；
3. 取最后一个有效位置的 logits；
4. 按选定策略得到下一个 token；
5. 把 token 追加到上下文；
6. 遇到 `<EOS>` 或最大长度时停止，否则回到第 $2$ 步。

## 11.2 Token 选择策略

### Greedy decoding

$$
x_{t+1}=\arg\max_v Z_{t,v}.
$$

结果确定、速度简单，但可能缺乏多样性。

### Temperature

$$
p_v=\operatorname{softmax}\left(\frac{Z_v}{\tau}\right).
$$

- $\tau<1$：分布更尖锐；
- $\tau>1$：分布更平坦；
- $\tau\to0$：趋近 greedy。

### Top-k 与 top-p

- top-k：只在概率最高的 $k$ 个 token 中采样；
- top-p：选择累计概率至少为 $p$ 的最小候选集合后采样。

## 11.3 为什么需要 KV cache

若每生成一个 token 都重新处理完整前缀，历史 token 的 K/V 会被重复计算。KV cache 保存每层已经算出的历史 K/V。

Prefill 阶段处理完整 prompt；decode 阶段每次只对新 token 计算 Q/K/V，并把新的 K/V 追加到 cache。

单步 decode 时常见 shape 为：

$$
Q_{new}\in\mathbb{R}^{B\times H\times1\times d_h},
$$

$$
K_{cache},V_{cache}
\in\mathbb{R}^{B\times H_{KV}\times N_{current}\times d_h}.
$$

新 query 仍需与所有历史 key 比较，因此单步 attention score 与当前上下文长度线性相关；KV cache 省去的是历史 K/V 的重复投影和历史层计算，并没有消除读取长上下文的成本。

## 11.4 KV cache 元素量

忽略 GQA/MQA 和实现细节时，Key 与 Value 总元素量约为：

$$
\#\operatorname{KV}=2LBHNd_h.
$$

更一般地，应使用 KV head 数：

$$
\#\operatorname{KV}=2LBH_{KV}Nd_h.
$$

显存估算为：

$$
\operatorname{bytes}
\approx2LBH_{KV}Nd_h\times\text{dtype bytes}.
$$

## 11.5 MHA、GQA 与 MQA

| 机制 | Query heads | KV heads | KV cache 特征 |
| --- | ---: | ---: | --- |
| MHA | $H$ | $H$ | 最大 |
| GQA | $H$ | $1<H_{KV}<H$ | 多个 query heads 共享一组 K/V head |
| MQA | $H$ | $1$ | 最小 |

计算 KV cache 时必须代入 $H_{KV}$，不能机械使用 query head 数 $H$。

### 例题 12：KV cache 显存

设 $L=12,B=2,H_{KV}=4,N=1024,d_h=64$，dtype 为 fp16，每元素 $2$ bytes。估算 K+V cache 显存。

> [!success]- 解答
> 元素总数为：
> $$
> 2\times12\times2\times4\times1024\times64
> =12{,}582{,}912.
> $$
> bytes 为：
> $$
> 12{,}582{,}912\times2
> =25{,}165{,}824\ \text{bytes}.
> $$
> 因为 $1\,\mathrm{MiB}=2^{20}$ bytes，所以约为：
> $$
> 24\,\mathrm{MiB}.
> $$
> 若 $H_{KV}$ 从 $4$ 增到 $8$，其他不变，cache 约翻倍到 $48\,\mathrm{MiB}$。

---

# 十二、复杂度与 Resource Accounting

## 12.1 Attention 各部分复杂度

Q/K/V 和 output projection 的计算量约为：

$$
O(BND^2).
$$

QK score 与 $AV$ 的核心计算量约为：

$$
O(BHN^2d_h)=O(BN^2D).
$$

score tensor 元素量为：

$$
BHN^2.
$$

因此 attention 对长序列最敏感的是 $N^2$ 项。

## 12.2 MLP 复杂度

标准两层 MLP 计算量约为：

$$
O(BNDD_{ff}).
$$

在 $D$ 和 $D_{ff}$ 固定时，MLP 对 $N$ 是线性的。

## 12.3 $N$ 减半的结论

当其他配置不变，$N\to N/2$：

| 项目 | 变化 |
| --- | --- |
| Attention score 元素量 | 变为 $1/4$ |
| Attention 的 $N^2$ 计算部分 | 变为 $1/4$ |
| Q/K/V 投影 | 变为 $1/2$ |
| Position-wise MLP | 变为 $1/2$ |
| KV cache | 变为 $1/2$ |

> [!important]
> “Attention 变为四分之一”特指由 $N^2$ 主导的 score 和加权部分。完整 attention 还包含随 $N$ 线性变化的投影，因此实测总 latency 不一定精确变为四分之一。

## 12.4 Score tensor 数值表

当 $B=4,H=8$ 时：

$$
\#S=BHN^2=32N^2.
$$

| $N$ | Score 元素量 | 相对上一档 |
| ---: | ---: | ---: |
| $64$ | $131{,}072$ | - |
| $128$ | $524{,}288$ | $4\times$ |
| $256$ | $2{,}097{,}152$ | $4\times$ |
| $512$ | $8{,}388{,}608$ | $4\times$ |

若 score 以 fp16 显式保存，$N=512$ 时仅该 tensor 的理论大小为：

$$
8{,}388{,}608\times2
=16{,}777{,}216\ \text{bytes}
=16\,\mathrm{MiB}.
$$

实际 peak memory 还会包含 Q/K/V、context、MLP 激活、梯度、优化器状态、临时 workspace 和 allocator 开销。

## 12.5 为什么实测 latency 不严格按理论倍数变化

常见原因包括：

- 小 tensor 时 kernel launch 固定开销占比高；
- GPU 并行单元在不同 $N$ 下利用率不同；
- memory bandwidth 与计算吞吐的瓶颈可能切换；
- FlashAttention 等融合 kernel 不显式保存完整 score；
- 编译、warm-up、cache 和异步计时影响测量；
- 完整 block 还包含复杂度对 $N$ 线性的投影、LayerNorm 和 MLP；
- padding 与实际有效 token 数不同。

## 12.6 Resource accounting 应记录什么

至少记录：

| 项目 | 为什么重要 |
| --- | --- |
| $B,N,D,L$ | 决定主干激活与大部分计算规模 |
| $H,H_{KV},d_h$ | 决定 score 布局和 KV cache |
| $D_{ff}$ | 决定 MLP 计算与激活 |
| dtype | 决定每元素 bytes 和数值范围 |
| train/inference | 训练需要保存反向传播激活；推理常有 KV cache |
| kernel/attention backend | 决定是否物化 score 及实际效率 |
| padding/packing | 决定计算中有多少无效 token |

参数量不能单独代表运行成本。相同参数量的模型，序列长度不同会有完全不同的 attention 和 KV cache 开销。

### 例题 13：$N$ 翻倍

固定 $B,H,D,D_{ff},L$，将 $N$ 从 $256$ 增加到 $512$。理论上 score 元素量、MLP 计算量和 KV cache 如何变化？

> [!success]- 解答
> Score 依赖 $N^2$，所以变为 $4$ 倍。MLP 对 $N$ 线性，所以变为 $2$ 倍。KV cache 对 $N$ 线性，所以变为 $2$ 倍。

---

# 十三、模块职责与 Shape 排错

## 13.1 五个核心组件

| 组件 | 核心职责 | 最关键的检查项 |
| --- | --- | --- |
| `MLP` | 对每个 token 做非线性通道变换 | $[B,N,D]\to[B,N,D]$ |
| `CausalAttention` | 计算不能访问未来的 self-attention | score 为 $[B,H,N,N]$，未来位置概率为 $0$ |
| `DecoderBlock` | 组合 norm、attention、MLP 和 residual | 输入输出 shape 相同 |
| `Transformer.forward` | embedding、堆叠 blocks、输出词表 logits | $[B,N]\to[B,N,V]$ |
| `generate` | 反复选取并追加 next token | 每步长度增加 $1$，正确停止和复用 cache |

## 13.2 推荐的 shape trace

给定输入 $[B,N]$，按顺序记录：

| Stage | 期望 shape |
| --- | --- |
| Token ids | $[B,N]$ |
| Token embedding | $[B,N,D]$ |
| Position-added hidden | $[B,N,D]$ |
| Q/K/V before split | $[B,N,D]$ |
| Q/K/V after split | $[B,H,N,d_h]$ |
| Attention score | $[B,H,N,N]$ |
| Per-head context | $[B,H,N,d_h]$ |
| Concatenated context | $[B,N,D]$ |
| DecoderBlock output | $[B,N,D]$ |
| Vocabulary logits | $[B,N,V]$ |

## 13.3 常见错误一：head 维与 token 维颠倒

若 Q 的内部布局是 $[B,N,H,d_h]$，必须先 transpose 成 $[B,H,N,d_h]$，再让最后两个维度参与矩阵乘法。

例如输入打印为：

| Tensor | 错误/中间 shape |
| --- | --- |
| $X$ | $[4,128,512]$ |
| $Q$ | $[4,128,8,64]$ |
| score | $[4,128,8,8]$ |

这说明矩阵乘法把 $8$ 个 head 当成了序列轴。正确的标准布局应为：

$$
Q,K:[4,8,128,64],
$$

$$
\text{score}:[4,8,128,128].
$$

## 13.4 常见错误二：softmax 维度错误

score shape 为 $[B,H,N_q,N_k]$ 时，softmax 应沿最后的 $N_k$ 维进行。若沿 query 维归一化，得到的是“所有 query 对某个 key 的分布”，不符合每个 query 从 key/value 中读取信息的定义。

## 13.5 常见错误三：Mask 方向反了

行是 query、列是 key。Causal 可见区域应是主对角线及其下方。若屏蔽了下三角，当前 token 反而只能看未来。

快速检查：第 $1$ 行应只有第 $1$ 列可见；最后一行应能看到所有过去和当前有效 key。

## 13.6 常见错误四：训练目标没有 shift

若 input 与 target 完全相同，模型可能在当前位置直接读取答案，造成虚假的低 loss。应明确检查：

$$
\text{input}=x_{0:N-1},\qquad
\text{target}=x_{1:N}.
$$

## 13.7 常见错误五：Padding 进入 loss

即使 attention mask 正确，如果 padding target 仍参与 cross-entropy，模型也会被迫学习无意义的 padding 预测。需要设置 ignore index 或显式 loss mask。

## 13.8 常见错误六：Generate 使用了错误位置的 logits

生成时应取每条样本最后一个有效 token 位置的 logits。若 batch 中存在不同长度和 padding，直接固定取最后一列可能拿到 padding query 的 logits。

### 例题 14：Shape 排错

设 $B=4,N=128,D=512,H=8,d_h=64$。某实现得到 Q 为 $[4,128,8,64]$，score 为 $[4,128,8,8]$。指出原因和修复后的 shape。

> [!success]- 解答
> Q 仍处于 $[B,N,H,d_h]$ 布局，直接与 K 做了最后两维矩阵乘法，因此把 head 轴当成序列轴，得到 $8\times8$ score。应将 Q/K transpose 为 $[B,H,N,d_h]=[4,8,128,64]$，再计算 $QK^\top$，得到 score $[4,8,128,128]$。

---

# 十四、CS336 延伸模块

## 14.1 RMSNorm

RMSNorm 不减去均值，只根据均方根缩放。对 $x\in\mathbb{R}^{D}$：

$$
\operatorname{RMS}(x)
=\sqrt{\frac{1}{D}\sum_{i=1}^{D}x_i^2+\epsilon},
$$

$$
\operatorname{RMSNorm}(x)
=\gamma\odot\frac{x}{\operatorname{RMS}(x)}.
$$

与 LayerNorm 相比：

| 项目 | LayerNorm | RMSNorm |
| --- | --- | --- |
| 减均值 | 是 | 否 |
| 按尺度归一化 | 是 | 是 |
| 可学习 gain | 通常有 | 通常有 |
| 可学习 bias | 通常有 | 常见实现没有 |

两者都不改变 shape，目标都是稳定激活尺度和训练。

## 14.2 SwiGLU

一种常见写法为：

$$
\operatorname{SwiGLU}(x)
=\left(\operatorname{SiLU}(xW_g)\odot xW_v\right)W_o.
$$

$xW_g$ 经 SiLU 后形成门控，逐元素调节 $xW_v$ 分支。不同实现可能交换两个分支的命名。

若两个输入投影都从 $D$ 到 $D_{ff}$：

$$
xW_g,xW_v\in\mathbb{R}^{B\times N\times D_{ff}},
$$

逐元素相乘后 shape 不变，再由 $W_o$ 投影回 $D$。

## 14.3 RoPE 回顾

RoPE 作用于 Q/K 而非 V，通过位置相关旋转让点积依赖相对位置。需要检查：

- Q/K 的 head dimension 是否按二维通道对旋转；
- position index 是否与 cache 中历史 token 连续；
- 使用 KV cache 解码时，新 token 的 position 是否正确递增；
- RoPE 不应改变 Q/K shape。

### 例题 15：RMSNorm 与 SwiGLU

1. 输入为 $[2,128,512]$，RMSNorm 输出 shape 是什么？
2. SwiGLU 两个门控投影输出均为 $[2,128,1536]$，逐元素相乘后再投影到 $512$，最终 shape 是什么？

> [!success]- 解答
> RMSNorm 只归一化最后一维，输出仍为 $[2,128,512]$。SwiGLU 两个分支逐元素相乘后仍为 $[2,128,1536]$，经 output projection 后为 $[2,128,512]$，从而能返回 residual 主干。

---

# 十五、综合例题：从输入到资源估算

设一个 decoder-only Transformer 具有：

$$
B=2,\quad N=128,\quad D=512,\quad H=8,\quad d_h=64,
$$

$$
D_{ff}=2048,\quad L=12,\quad V=32{,}000.
$$

假设普通 MHA，即 $H_{KV}=H$，dtype 为 fp16。

## 题目

1. 写出 token ids、embedding、拆头后 Q/K/V、score、context 和 logits 的 shape。
2. 写出一个 Pre-LN DecoderBlock 的公式。
3. 计算单层四个 attention Linear 的参数量，均带 bias。
4. 计算单层标准两层 MLP 的参数量，均带 bias。
5. 估算 $12$ 层 KV cache 的元素量和 fp16 bytes。
6. 若把 $N$ 减半到 $64$，score、MLP 和 KV cache 分别约变为多少？

> [!success]- 完整解答
> **1. Shape**
>
> | Tensor | Shape |
> | --- | --- |
> | Token ids | $[2,128]$ |
> | Embedding/主干 | $[2,128,512]$ |
> | Q/K/V | $[2,8,128,64]$ |
> | Score | $[2,8,128,128]$ |
> | Per-head context | $[2,8,128,64]$ |
> | Concatenated context | $[2,128,512]$ |
> | Logits | $[2,128,32{,}000]$ |
>
> **2. Pre-LN DecoderBlock**
> $$
> U=X+\operatorname{MHA}_{causal}(\operatorname{LN}_1(X)),
> $$
> $$
> Y=U+\operatorname{MLP}(\operatorname{LN}_2(U)).
> $$
>
> **3. Attention 投影参数量**
>
> 每个 $512\to512$ Linear 含：
> $$
> 512^2+512=262{,}656
> $$
> 个参数。四个共：
> $$
> 4\times262{,}656=1{,}050{,}624.
> $$
>
> **4. MLP 参数量**
> $$
> (512\times2048+2048)
> +(2048\times512+512)
> =2{,}099{,}712.
> $$
>
> **5. KV cache**
> $$
> 2LBH_{KV}Nd_h
> =2\times12\times2\times8\times128\times64
> =3{,}145{,}728
> $$
> 个元素。fp16 bytes 为：
> $$
> 3{,}145{,}728\times2=6{,}291{,}456\ \text{bytes}
> =6\,\mathrm{MiB}.
> $$
>
> **6. $N$ 减半**
>
> Score 的 $N^2$ 部分变为 $1/4$；MLP 变为 $1/2$；KV cache 变为 $1/2$。

---

# 十六、迁移例题：Video MLLM 中的 Token 数

Transformer 的 $N^2$ 成本也是 Video MLLM 必须压缩视觉 token 的核心原因。

假设每个样本采样 $T=8$ 帧，每帧保留 $N_v=64$ 个视觉 token，文本有 $N_t=128$ 个 token。视觉 token 作为前缀拼接到 LLM：

$$
N=TN_v+N_t=8\times64+128=640.
$$

若不做视觉压缩，每帧有 $256$ 个视觉 token：

$$
N'=8\times256+128=2176.
$$

在其他配置相同的情况下，attention score 元素量之比约为：

$$
\left(\frac{N'}{N}\right)^2
=\left(\frac{2176}{640}\right)^2
\approx11.56.
$$

也就是说，每帧视觉 token 增加 $4$ 倍后，因为还存在固定的文本 token，总序列 attention score 约增加到 $11.56$ 倍，而不是简单的 $4$ 倍。

> [!tip] 分析多模态模型时
> 不要只看“每帧 token 数”。应先算出最终送入 LLM 的总长度 $N=TN_v+N_t$，再分析 attention 与 KV cache。

---

# 十七、知识点与练习题对应表

| 讲义章节 | 对应练习题 |
| --- | --- |
| 自回归 LM、RNN、Teacher forcing | 第 $1$--$3$ 题 |
| MLP、LayerNorm、Residual、Pre-LN | 第 $4$、$13$ 题 |
| Encoder 与 decoder attention | 第 $5$ 题 |
| Multi-Head Attention shape 与参数 | 第 $6$、$9$、$10$ 题 |
| Cross-attention | 第 $7$ 题 |
| Padding/Causal mask 与 broadcast | 第 $8$、$11$ 题 |
| 位置信息 | 第 $12$ 题 |
| Forward、logits 与 generate | 第 $14$、$15$、$19$、$20$ 题 |
| Score、复杂度与 latency | 第 $16$、$17$ 题 |
| KV cache | 第 $15$、$17$、$18$ 题 |
| RMSNorm、RoPE、SwiGLU | 第 $21$ 题 |

---

# 十八、完成前自检

## 概念

- [ ] 能写出自回归概率分解。
- [ ] 能解释 teacher forcing 为什么需要 input/target shift。
- [ ] 能解释训练并行为什么不等于允许看未来。
- [ ] 能区分 encoder bidirectional attention 与 decoder causal attention。

## Shape

- [ ] 能从 $[B,N,D]$ 推到 $Q/K/V:[B,H,N,d_h]$。
- [ ] 能推出 self-attention score 为 $[B,H,N,N]$。
- [ ] 能推出 cross-attention score 为 $[B,H,N_q,N_k]$。
- [ ] 知道 softmax 沿 key 维进行。
- [ ] 知道 residual 两侧 shape 必须一致。

## Mask

- [ ] 能画出 causal 下三角可见性矩阵。
- [ ] 能写出 padding mask 和 causal mask 的 broadcast shape。
- [ ] 能解释 mask 为什么在 softmax 前应用。
- [ ] 能处理 padding query 和 padding loss。

## 完整模型

- [ ] 能写出 Pre-LN DecoderBlock 两个残差公式。
- [ ] 能从 token ids 推到 $[B,N,V]$ logits。
- [ ] 能描述 generate 的完整循环和停止条件。
- [ ] 能解释 KV cache 保存了什么、没有省掉什么。

## 资源

- [ ] 知道 score 元素量为 $BHN^2$。
- [ ] 知道 MLP 对 $N$ 线性，attention score 对 $N$ 平方。
- [ ] 能使用 $2LBH_{KV}Nd_h$ 估算 KV cache。
- [ ] 能解释理论复杂度与实测 latency 不完全一致的原因。

> [!success] 下一步
> 完成上述自检后，独立作答 [[Paper/架构学习/Video-MLLM/01-transformer-练习题|Transformer 纸笔练习题]]。遇到错误时，不要只抄答案：回到对应章节重新从 shape 和信息可见性推导。
