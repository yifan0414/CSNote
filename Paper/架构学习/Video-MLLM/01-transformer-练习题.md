---
title: Transformer 纸笔练习题
aliases:
  - Transformer Practice Test
tags:
  - video-mllm
  - transformer
  - exercise
type: exercise
stage: 1
status: active
created: 2026-08-17
---

# Transformer 纸笔练习题

依据：[[Paper/架构学习/Video-MLLM/01-transformer|01-transformer]]。

配套讲义：[[Paper/架构学习/Video-MLLM/01-transformer-基础知识与例题|Transformer 基础知识与例题]]。

> [!abstract] 使用方式
> 这是一套不依赖运行程序的纸笔测试。建议先独立完成“题目”部分，再看文末“参考答案与评分要点”。除非题目另有说明，所有 shape 都按 $[B,N,D]$ 或 $[B,H,N,d_h]$ 的顺序书写。

## 考试说明

- 基础卷满分 100 分，建议用时 90--120 分钟。
- 加分题 10 分，考查笔记中提到的 CS336 延伸内容。
- 计算题可以保留精确表达式；需要近似值时，题目会明确说明。
- 记号：$B$ 为 batch size，$N$ 为序列 token 数，$D$ 为 hidden dimension，$H$ 为 query attention heads，$d_h$ 为单头维度，$L$ 为 Transformer 层数，$V$ 为词表大小。

---

# 第一部分：基础理解（20 分）

### 1. 自回归语言模型（4 分）

1. 写出长度为 $N$ 的序列 $x_1,\ldots,x_N$ 的自回归概率分解。
2. 说明 RNN 语言模型相对于 Transformer 训练时的主要串行瓶颈。

### 2. Teacher forcing 与错位关系（4 分）

给定完整序列：

`<BOS> 我 喜欢 猫 <EOS>`

在 teacher forcing 下，写出训练输入 `input` 和监督目标 `target`。指出二者为什么必须错开一个 token。

### 3. Causal mask 的必要性（4 分）

训练时 Transformer 可以并行计算整段序列，为什么 decoder-only Transformer 仍然需要 causal mask？回答中同时说明：

1. 第 $t$ 个位置可以看到哪些 token；
2. 推理生成第 $t$ 个 token 时，计算方式与训练有什么不同。

### 4. MLP 与残差（4 分）

1. 写出一个 position-wise MLP 的一般形式，并说明它是否在 token 维度上混合信息。
2. 写出 Pre-LN residual block 中 attention 子层和 MLP 子层的一种合法顺序（用 $\operatorname{LN}$、$\operatorname{MHA}$、$\operatorname{MLP}$ 和残差表示）。
3. 残差相加的两个张量需要满足什么 shape 条件？

### 5. Encoder 与 decoder attention（4 分）

比较 encoder 的 bidirectional self-attention 和 decoder 的 causal self-attention，至少写出两点差异，并说明这对信息可见性有什么影响。

---

# 第二部分：Shape 推导与参数（25 分）

### 6. Multi-Head Self-Attention 全链路（10 分）

设 $B=2,N=6,D=12,H=3,d_h=4$，且 $D=H d_h$。输入为 $X\in\mathbb{R}^{2\times6\times12}$。

1. 若 $W_Q,W_K,W_V$ 都把最后一维从 $D$ 投影到 $D$，分别写出线性投影后的 shape。
2. 将投影结果拆成多头后，写出 $Q,K,V$ 的 shape。
3. 写出 $QK^\top$、缩放后的 score、softmax 权重、每头 context 的 shape。
4. 拼接多头后恢复成 $[B,N,D]$，再经过 output projection，写出最终 shape。
5. 假设四个 Linear 都带 bias，计算 Q/K/V 三个投影和 output projection 一共含有多少个可训练参数？

### 7. Cross-attention 的矩形 score（5 分）

query 序列长度为 $N_q=5$，key/value 序列长度为 $N_k=7$，$B=2,H=4,d_h=8$。

1. 写出 $Q$、$K$、$V$ 和 score tensor 的 shape。
2. 解释为什么 score 不是 $[B,H,5,5]$。
3. softmax 应沿 score 的哪一维进行？该维度在语义上代表什么？

### 8. Mask 的 broadcast shape（5 分）

对于 self-attention，设 score 为 $[B,H,N,N]$。分别给出下列 mask 的一种常见 broadcast shape，并说明它屏蔽的是哪一类位置：

1. 对每个样本、每个 key 位置都相同的 padding mask；
2. 对所有样本和 head 都相同的 causal mask；
3. 同时依赖 batch 和 query/key 位置、但不依赖 head 的通用 mask。

### 9. Shape 排错（5 分）

某实现打印出：

```text
X       [4, 128, 512]
Q       [4, 128, 8, 64]
K       [4, 128, 8, 64]
scores  [4, 128, 8, 8]
```

已知 $D=512,H=8,d_h=64$。指出至少两处 shape/维度语义问题，并写出你期望的 $Q/K$ 与 score shape。

---

# 第三部分：手算 Attention 与 Mask（20 分）

### 10. 单头 attention 手算（10 分）

设 $H=1,d_h=1,N=3$：

$$
Q=K=\begin{bmatrix}1\\2\\1\end{bmatrix},\qquad
V=\begin{bmatrix}10\\20\\30\end{bmatrix}.
$$

1. 写出未缩放的 $QK^\top$。
2. 因为 $d_h=1$，缩放因子是多少？
3. 加上 causal mask 后，哪些 score 元素应变成 $-\infty$？写出 masked score 矩阵。
4. 第 1 个位置的 context 是多少？
5. 第 2 个位置的 context 用 $e^2$ 和 $e^4$ 表示（不必计算小数）。
6. 解释为什么不能把 mask 加在 softmax 之后。

### 11. Padding mask 与 causal mask（10 分）

一个 batch 中有两条序列，真实长度分别为 4 和 2，统一 padding 到 $N=4$。约定 $1$ 表示可见，$0$ 表示 padding。

1. 写出 batch 维度上的 key padding mask。
2. 对第二条序列，写出同时满足“不能看未来”和“不能看 padding key”的可见性矩阵（行是 query，列是 key）。
3. 如果 query 本身是 padding 位置，是否还需要额外屏蔽该行？说明一种合理处理方式。
4. mask 应在 softmax 前还是后应用？为什么？

---

# 第四部分：位置、完整 Block 与生成（20 分）

### 12. 位置信息（5 分）

1. 如果只使用 token embedding 而不加入任何位置信息，self-attention 对输入 token 顺序有什么潜在问题？
2. 写出“token embedding 加 position embedding”的 shape 关系。
3. 区分“改变 token 数 $N$”和“改变 hidden dimension $D$”对后续 attention shape 的影响。

### 13. Pre-LN DecoderBlock（7 分）

给定输入 $X\in\mathbb{R}^{B\times N\times D}$，写出一个包含 causal MHA、MLP 和两个残差的 Pre-LN DecoderBlock 公式，并标注每一步的 shape。要求说明 attention 子层和 MLP 子层各自负责什么。

### 14. Decoder-only Transformer 的 forward（4 分）

词表大小为 $V$，输入 token ids 为 $[B,N]$。

1. token embedding 后的 shape 是什么？
2. 经过 $L$ 个 decoder block 后，最终 hidden state 和 logits 的 shape 是什么？
3. 为什么训练时通常只需要一次 forward 就能得到所有位置的 next-token logits？

### 15. Generate 流程（4 分）

不写代码，用 4--6 个步骤描述 decoder-only Transformer 的自回归生成流程。至少包含：当前上下文、causal mask、logits 取法、选 token、停止条件。说明为什么推理时可以使用 KV cache。

---

# 第五部分：复杂度、显存与实验解读（15 分）

### 16. Attention score tensor 资源量（6 分）

设 $B=4,H=8,d_h=64$，只计算 score tensor，不考虑其他中间量。分别计算 $N\in\{64,128,256,512\}$ 时 score tensor 的元素数量，并写出相邻两档的增长倍数。

若实测 $N$ 翻倍时 forward latency 没有严格变成 4 倍，写出至少两个合理原因（不得只回答“测量有误”）。

### 17. N 减半的影响（5 分）

在 hidden dimension 和层数不变时，$N$ 减半会如何影响：

1. self-attention 的 score 计算量和 score 显存；
2. position-wise MLP 的计算量；
3. 忽略 GQA/MQA 时 KV cache 的元素数量。

请分别写出“约减少为原来的多少”。

### 18. KV cache 数值估算（4 分）

忽略 padding 和 allocator 开销，模型参数为 $L=12,B=2,H_{KV}=4,N=1024,d_h=64$，dtype 为 fp16（每元素 2 bytes）。

1. 使用 $2LBH_{KV}Nd_h$ 计算 Key+Value 的元素总数。
2. 换算成 bytes 和约 MiB（$1\,\mathrm{MiB}=2^{20}$ bytes）。
3. 如果改用 8 个 KV heads，显存约变为多少？

---

# 第六部分：实现设计与综合题（选做基础卷最后一题，或作为口试题）

### 19. 从模块到训练闭环（不计分，建议完成）

请设计一条从 token ids 到训练 loss 的完整数据流，至少包括：

1. embedding、position information、$L$ 个 Pre-LN DecoderBlock；
2. logits 与 vocabulary 的关系；
3. teacher forcing 下 input/target 的对齐；
4. padding loss 的处理；
5. 记录 loss 曲线和 gradient norm 曲线时，你会观察什么现象来判断训练是否正常。

### 20. Assignment 3 代码阅读题（不运行程序）

将下列组件与它们的职责连线，并为每项写一个应检查的 shape 或行为：

| 组件 | 职责 |
| --- | --- |
| `MLP` | A. 堆叠 decoder blocks 并产出词表 logits |
| `CausalAttention` | B. 逐位置的非线性变换 |
| `DecoderBlock` | C. 训练/推理时按序列生成 token |
| `Transformer.forward` | D. 计算带因果约束的 attention |
| `generate` | E. 组合 attention、MLP、LayerNorm 和残差 |

---

# 加分题：CS336 延伸（10 分）

### 21. RMSNorm、RoPE、SwiGLU（10 分）

1. RMSNorm 与 LayerNorm 相比，少了哪类统计/变换？它仍然试图解决什么问题？（3 分）
2. RoPE 的核心作用是什么？它主要注入哪类位置信息？（3 分）
3. 写出 $\operatorname{SwiGLU}(x)$ 的典型形式，并指出其中的门控分支。（2 分）
4. resource accounting 时，为什么要同时记录 token 数、dtype、batch size 和 head 数，而不能只看参数量？（2 分）

---

# 参考答案与评分要点

> [!warning] 建议
> 做完题后再展开本节。答案中的公式只给出一种标准写法；只要 shape、信息流和因果关系正确，等价写法均可得分。

## 第一部分

### 1.

1. $P(x_1,\ldots,x_N)=\prod_{t=1}^{N}P(x_t\mid x_{<t})$（若含 `<BOS>`，它也作为条件序列的一部分）。
2. RNN 在时间维递归，$h_t$ 依赖 $h_{t-1}$，训练时难以在时间步上完全并行；Transformer 的 self-attention 可并行算整段，但单层 score 仍有 $O(N^2)$ 成本。

### 2.

`input = [<BOS>, 我, 喜欢, 猫]`，`target = [我, 喜欢, 猫, <EOS>]`。第 $t$ 个输入用于预测第 $t$ 个目标，错开后才是 next-token prediction；否则会把待预测 token 泄漏给模型。

### 3.

第 $t$ 个位置只能看 $1,\ldots,t$（包括自身，具体边界按实现约定）；不能看未来 token。训练可对所有位置并行算 logits，但 mask 保证每个位置使用的条件与生成时一致。推理时每次只根据已有上下文产生一个新 token，再把它追加到上下文中。

### 4.

1. 例如 $\operatorname{MLP}(x)=W_2\,\sigma(W_1x+b_1)+b_2$，对每个 token 独立应用，不在 token 维度混合信息。
2. 一种 Pre-LN 写法：$Y=X+\operatorname{MHA}(\operatorname{LN}(X))$，$Z=Y+\operatorname{MLP}(\operatorname{LN}(Y))$。
3. 残差相加要求两项 shape 完全一致，通常都是 $[B,N,D]$。

### 5.

Encoder 通常允许任意位置互相注意（bidirectional，无未来约束），适合理解完整输入；decoder self-attention 使用上三角 causal mask，只允许看当前及过去，适合自回归生成。二者的可见性矩阵不同。

## 第二部分

### 6.

1. 三个投影均为 $[2,6,12]$。
2. $Q,K,V$ 的 shape 均为 $[2,3,6,4]$。
3. $QK^\top$ 为 $[2,3,6,6]$；缩放不改变 shape；softmax 权重为 $[2,3,6,6]$；context 为 $[2,3,6,4]$。
4. 拼接为 $[2,6,12]$，output projection 后仍为 $[2,6,12]$。
5. 每个 Q/K/V Linear：$12\times12+12=156$，三个共 $468$；output projection 为 $156$；总计 $624$ 个参数。

### 7.

1. $Q:[2,4,5,8]$，$K,V:[2,4,7,8]$，score $QK^\top:[2,4,5,7]$。
2. 每个 query 要与 7 个 key 比较，所以最后一维是 $N_k=7$，不是 query 长度 5。
3. 沿最后一维 key 维 softmax；每一行表示一个 query 对所有可见 key 的概率分布，行和为 1。

### 8.

1. padding mask 可写成 $[B,1,1,N]$，在 query 和 head 维广播，按 key 屏蔽 padding。
2. causal mask 可写成 $[1,1,N,N]$，屏蔽 $\text{key\_index}>\text{query\_index}$ 的上三角。
3. 通用 batch 相关 mask 可写成 $[B,1,N,N]$，在 head 维广播。

### 9.

$Q/K$ 把 head 维放在了错误位置，且 score 将 $N=128$ 当成了 head/序列维。常见正确写法是 $Q,K:[4,8,128,64]$，score $[4,8,128,128]$。若采用 $[B,N,H,d_h]$ 的内部布局，也必须在矩阵乘法前明确转置，不能把 $[4,128,8,64]$ 直接当作标准 attention 布局。

## 第三部分

### 10.

1.

$$
QK^\top=
\begin{bmatrix}
1&2&1\\
2&4&2\\
1&2&1
\end{bmatrix}.
$$

2. $\sqrt{d_h}=1$，所以缩放不改变数值。
3.

$$
\begin{bmatrix}
1&-\infty&-\infty\\
2&4&-\infty\\
1&2&1
\end{bmatrix}.
$$

4. 第 1 行 softmax 后权重为 $[1,0,0]$，context 为 $10$。
5. 第 2 行 context 为 $\dfrac{e^2\cdot10+e^4\cdot20}{e^2+e^4}$。
6. 若在 softmax 后才屏蔽，原本分给未来位置的概率质量已经参与归一化，剩余概率不再正确归一；应在 softmax 前将非法位置设为 $-\infty$（或足够小的数）。

### 11.

1. key padding mask（按 batch）可写为：

$$
\begin{bmatrix}
1&1&1&1\\
1&1&0&0
\end{bmatrix}.
$$

2. 第二条序列的可见性矩阵为：

$$
\begin{bmatrix}
1&0&0&0\\
1&1&0&0\\
1&1&0&0\\
1&1&0&0
\end{bmatrix}.
$$

其中第 3、4 行是 padding query；如果保留这些行，至少必须保证它们不影响有效 token 的输出或 loss。
3. 常见做法是同时屏蔽 padding query 的输出/损失（例如 loss 只在非-padding target 上计算），也可以在 attention 后将 padding query 的 hidden state 清零；关键是 padding 不应贡献训练信号。
4. 在 softmax 前应用，将非法位置置为 $-\infty$，使其概率为 0 且不参与归一化。

## 第四部分

### 12.

1. 没有位置信息时，self-attention 本身对 token 集合的排列近似置换等变，难以区分不同顺序的相同 token。
2. token embedding 与 position embedding 都是 $[B,N,D]$，逐元素相加后仍为 $[B,N,D]$。
3. 改变 $N$ 会改变 score 的 $[N,N]$ 两个轴以及序列长度；改变 $D$ 会改变 Q/K/V 投影的最后一维和 head 划分，但不直接改变 token 数。

### 13.

一种完整写法：

$$
\begin{aligned}
U&=X+\operatorname{MHA}(\operatorname{LN}(X)) &&\in\mathbb{R}^{B\times N\times D},\\
Y&=U+\operatorname{MLP}(\operatorname{LN}(U)) &&\in\mathbb{R}^{B\times N\times D}.
\end{aligned}
$$

MHA 在 token 之间混合上下文，MLP 对每个 token 独立做通道维非线性变换；两次残差保持主干 shape 不变。

### 14.

1. embedding 后为 $[B,N,D]$。
2. 最后一层 hidden state 为 $[B,N,D]$，词表投影后的 logits 为 $[B,N,V]$。
3. causal mask 使位置 $t$ 的 logits 只依赖 $x_{<t}$（或实现中的当前可见前缀），因此所有位置可在一次并行 forward 中同时得到各自的 next-token 分布。

### 15.

示例步骤：

1. 取当前 token 前缀作为上下文；
2. 用 causal mask（首次可处理完整前缀）运行模型；
3. 取最后一个位置的 logits；
4. 按 argmax、temperature、top-k/top-p 等策略选下一个 token；
5. 将 token 追加到上下文，更新/复用 KV cache；
6. 遇到 `<EOS>` 或达到最大长度时停止。

KV cache 保存过去层的 K/V，追加新 token 时无需重复计算历史 K/V。

## 第五部分

### 16.

score 元素数为 $BH N^2=32N^2$：

| $N$ | 元素数量 |
| ---: | ---: |
| 64 | 131,072 |
| 128 | 524,288 |
| 256 | 2,097,152 |
| 512 | 8,388,608 |

每次将 $N$ 翻倍，元素数量和理论 attention 计算量约变为 4 倍；相邻档位也是 4 倍。

实际 latency 还会受到 kernel 是否饱和、GPU 并行度、固定启动开销、显存读写、padding、编译/缓存状态以及其他线性复杂度模块的影响，因此不必严格呈现 4 倍。

### 17.

1. self-attention 的 $N^2$ 部分约变为 $1/4$；score 显存也约变为 $1/4$。
2. position-wise MLP 对每个 token 做相同计算，约变为 $1/2$。
3. $2LBHNd_h$ 中只有 $N$ 变化，KV cache 约变为 $1/2$。

### 18.

1. 元素总数：$2\times12\times2\times4\times1024\times64=12{,}582{,}912$。
2. bytes：$12{,}582{,}912\times2=25{,}165{,}824$ bytes，约 $24\,\mathrm{MiB}$。
3. KV heads 从 4 变为 8，其他不变，显存约翻倍，为 $48\,\mathrm{MiB}$。

## 第六部分

### 19.

合理答案应包含：$[B,N]$ ids $\to$ embedding/position 得 $[B,N,D]$ $\to$ $L$ 个 Pre-LN block $\to$ hidden $[B,N,D]$ $\to$ vocabulary projection 得 logits $[B,N,V]$；input 与 target 错开一位；padding target 不计入 loss；loss 应总体下降，gradient norm 不应持续爆炸或长期为零。能指出 teacher forcing 只在训练时使用真实历史 token，可得完整分。

### 20.

连线：`MLP-B`，`CausalAttention-D`，`DecoderBlock-E`，`Transformer.forward-A`，`generate-C`。

可检查项示例：$\operatorname{MLP}:[B,N,D]\to[B,N,D]$；attention score 为 $[B,H,N,N]$ 且未来位置为 0 概率；block 输入输出 shape 相同；forward logits 为 $[B,N,V]$；generate 每步序列长度增加 1、遇到 EOS 停止并正确处理 cache。

## 加分题

### 21.

1. RMSNorm 通常不减均值，只按 root mean square 对特征缩放并配合可学习 gain；仍用于稳定激活尺度和训练。
2. RoPE 通过对 Q/K 做依赖位置的旋转，将相对位置信息编码进 attention 的内积关系。
3. 典型形式：$\operatorname{SwiGLU}(x)=(\operatorname{SiLU}(xW)\odot(xV))W_o$（不同资料可能交换符号或把投影写成转置）；$xV$ 是门控分支，逐元素乘 $\odot$。
4. token 数决定 attention 的平方级成本和 KV cache 的线性成本；dtype 决定每元素 bytes；batch/head 数影响并行计算和中间张量规模；参数量不能单独反映一次 forward 的激活与缓存资源。

---

## 自我评分建议

| 得分 | 说明 |
| ---: | --- |
| 90--100 | 能独立完成 shape、mask、复杂度和生成流程，已具备从零实现 decoder-only Transformer 的推导基础 |
| 75--89 | 主干概念基本掌握；重点复查 broadcast、teacher forcing 和 KV cache |
| 60--74 | 能背出模块名称但 shape 或信息流不稳定；建议重做第 6、8、10、13、17 题 |
| <60 | 先回看 [[Paper/架构学习/Video-MLLM/00-shape-cheatsheet|Shape Cheatsheet]]，再按第一至第三部分分段重做 |
