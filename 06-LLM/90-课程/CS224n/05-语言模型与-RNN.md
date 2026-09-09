---
title: "CS224N 05 语言模型与 RNN"
aliases:
  - "Language Models and RNNs"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 5
date_text: "Thu Jan 15"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
updated: 2026-09-09
---
# CS224N 05：语言模型与 RNN

> [!abstract] 本节定位
> 用自回归分解定义语言模型，再用 RNN 建模可变长上下文，分析 BPTT 中的梯度消失与爆炸。

## 学习目标

- [ ] 用概率链式法则分解序列概率
- [ ] 推导 RNN 的时间展开与 BPTT
- [ ] 解释长距离依赖为何导致梯度问题

## 知识笔记

> [!info] 课件范围
> 对应 Language Models and RNNs PPT 第 3–58 页：语言模型、n-gram、固定窗口神经语言模型、RNN、训练与生成、困惑度、梯度消失/爆炸和神经机器翻译。

## 1. 语言模型

语言模型的基本任务是：给定前缀 $w_{1:t-1}$，预测下一个词：

$$
P(w_t\mid w_{1:t-1}).
$$

利用概率链式法则，整段文本的概率为：

$$
P(w_{1:T})
=
\prod_{t=1}^{T}P(w_t\mid w_{1:t-1}).
$$

因此，“预测下一词”和“给一段文本打分”是同一个模型的两种用途。

### 应用

- 自动补全；
- 语音识别；
- 拼写与语法纠错；
- 机器翻译；
- 文本生成；
- 作为预训练目标学习通用表示。

## 2. n-gram 语言模型

n-gram 使用 Markov 假设，只保留最近 $n-1$ 个词：

$$
P(w_t\mid w_{1:t-1})
\approx
P(w_t\mid w_{t-n+1:t-1}).
$$

最大似然估计：

$$
P(w_t\mid h)
=
\frac{\operatorname{count}(h,w_t)}
{\operatorname{count}(h)}.
$$

### 两个核心问题

1. **稀疏性**：许多合理 n-gram 在训练语料中从未出现。
2. **存储**：上下文组合数随 $n$ 和词表大小快速增长。

平滑、backoff 与插值能缓解零概率，但仍不能共享语义相似词之间的统计强度。

## 3. 固定窗口神经语言模型

将前 $m$ 个 token 的 embedding 拼接：

$$
x_t=[e_{t-m};\ldots;e_{t-1}]
\in\mathbb{R}^{md}.
$$

再通过 MLP：

$$
h_t=f(W_hx_t+b_h),
$$

$$
z_t=W_oh_t+b_o,
$$

$$
\hat y_t=\operatorname{softmax}(z_t).
$$

相较 n-gram，它能让相似词共享统计，且参数量不随观察到的 n-gram 数量增长。

主要限制：

- 窗口长度固定；
- 更长历史被完全丢弃；
- 不同位置使用不同拼接槽，参数利用不够自然。

## 4. RNN 的核心递归

RNN 用同一组参数更新隐藏状态：

$$
h_t
=
\tanh(W_hh_{t-1}+W_xx_t+b).
$$

输出：

$$
z_t=W_oh_t+b_o,
$$

$$
\hat y_t=\operatorname{softmax}(z_t).
$$

### Shape

若：

$$
x_t\in\mathbb{R}^{d_x},\quad
h_t\in\mathbb{R}^{d_h},\quad
z_t\in\mathbb{R}^{|V|},
$$

则：

$$
W_x\in\mathbb{R}^{d_h\times d_x},
\quad
W_h\in\mathbb{R}^{d_h\times d_h},
\quad
W_o\in\mathbb{R}^{|V|\times d_h}.
$$

> [!important]
> “循环”不是每个时间步有一套参数，而是同一参数在时间上重复使用。参数共享使模型能处理不同长度序列。

## 5. RNN 语言模型的训练

给定真实序列，训练时每个时间步输入真实前一个 token，预测真实下一个 token。

序列损失：

$$
L
=
\sum_{t=1}^{T}
-\log P(w_t\mid w_{<t}).
$$

训练数据中的所有位置都提供监督信号。虽然隐藏状态必须按时间顺序计算，但得到状态后，各时间步的输出投影与交叉熵可以批量实现。

### Teacher forcing

训练时喂入真实历史，生成时喂入模型自己采样出的历史。这会造成 exposure bias：

- 训练状态来自真实分布；
- 推理状态可能包含模型早先的错误；
- 错误会改变后续输入并继续累积。

## 6. 生成

自回归生成流程：

1. 输入起始 token；
2. 更新 $h_t$；
3. 得到 $P(w_{t+1}\mid w_{\le t})$；
4. 选取或采样下一个 token；
5. 将其作为下一步输入；
6. 直到 EOS 或长度上限。

生成策略不同会产生不同分布：

- argmax/greedy 更确定；
- sampling 更多样；
- 温度改变分布尖锐度。

这些解码方法将在后续推理课程中展开。

## 7. 困惑度

平均负对数似然：

$$
\operatorname{NLL}
=
-\frac{1}{T}\sum_{t=1}^{T}\log P(w_t\mid w_{<t}).
$$

困惑度：

$$
\operatorname{PPL}
=
\exp(\operatorname{NLL}).
$$

可理解为模型在每一步等效面对的候选分支数。

比较 PPL 时必须使用相同：

- 分词器；
- 词表；
- token 计数方式；
- 测试集；
- 是否包含特殊 token。

不同 tokenization 下的 PPL 通常不能直接比较。

## 8. BPTT：跨时间反向传播

把递归网络按时间展开后，它是一个参数共享的深层计算图。

共享参数 $W_h$ 的梯度是所有时间步贡献之和：

$$
\frac{\partial L}{\partial W_h}
=
\sum_{t=1}^{T}
\frac{\partial L}{\partial W_h}\bigg|_t.
$$

某个早期状态 $h_k$ 对后期损失 $L_t$ 的影响包含 Jacobian 连乘：

$$
\frac{\partial h_t}{\partial h_k}
=
\prod_{j=k+1}^{t}
\frac{\partial h_j}{\partial h_{j-1}}.
$$

对 vanilla RNN：

$$
\frac{\partial h_j}{\partial h_{j-1}}
=
\operatorname{diag}\left(
1-\tanh^2(a_j)
\right)W_h.
$$

这就是梯度稳定性问题的来源。

## 9. 梯度消失

若连乘 Jacobian 的有效范数长期小于 1，梯度随距离指数衰减：

$$
\left\|
\frac{\partial h_t}{\partial h_k}
\right\|
\to 0.
$$

后果：

- 早期 token 几乎得不到后期损失信号；
- 模型偏向短期依赖；
- 训练 loss 可能正常下降，却学不到远距离关系。

### 为什么不仅是优化速度慢

长程信息和近程信息同时存在时，近程梯度通常更强，会主导更新。模型并不是“多训练一会就一定学到”长程依赖。

### 缓解方法

- LSTM/GRU 的加法式记忆路径和门控；
- 残差连接；
- 更合适的初始化；
- normalization；
- attention 直接建立远距离连接。

## 10. 梯度爆炸

若有效 Jacobian 范数大于 1，梯度可能指数增长，导致：

- 参数更新过大；
- loss 突然变成 NaN；
- 不同 batch 之间训练极不稳定。

梯度裁剪：

$$
g
\leftarrow
\frac{\tau}{\|g\|}g,
\qquad
\text{if }\|g\|>\tau.
$$

它控制更新幅度，但不能解决梯度消失。

## 11. 神经机器翻译

### 11.1 Encoder–Decoder

编码器读取源句：

$$
h_t^{\text{enc}}
=f(h_{t-1}^{\text{enc}},x_t).
$$

最终状态形成源句表示 $c$。解码器以 $c$ 为条件生成目标句：

$$
h_t^{\text{dec}}
=f(h_{t-1}^{\text{dec}},y_{t-1},c).
$$

$$
P(y_t\mid y_{<t},x)
=
\operatorname{softmax}(W_oh_t^{\text{dec}}).
$$

训练目标：

$$
L
=
-\sum_{t=1}^{T_y}
\log P(y_t^\ast\mid y_{<t}^\ast,x).
$$

### 11.2 双向编码器

源句不是在线生成任务，可以同时从左右读取：

$$
h_t=[\overrightarrow h_t;\overleftarrow h_t].
$$

目标端必须保持因果生成。

### 11.3 固定向量瓶颈

将整个源句压入一个固定向量 $c$：

- 长句信息容易丢失；
- 解码每一步只能依赖同一个摘要；
- 无法显式选择当前最相关的源位置。

这直接引出下一课的 attention。

## 12. RNN 的优缺点

### 优点

- 原生处理任意长度序列；
- 参数在时间上共享；
- 隐状态理论上可汇总全部历史；
- 适合流式、在线场景。

### 缺点

- 时间依赖限制训练并行；
- 长路径带来梯度消失/爆炸；
- 固定状态是信息瓶颈；
- 很难扩展到极长上下文。

## 13. 小结

- 语言模型通过链式法则给序列分配概率。
- RNN 用共享递归状态替代固定窗口，但引入时间串行与长程梯度问题。
- PPL 是 token 级平均负对数似然的指数，只能在相同 tokenization 下比较。
- BPTT 的 Jacobian 连乘解释了梯度消失与爆炸。
- 固定向量 encoder-decoder 的瓶颈为 attention 提供了直接动机。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[cs224n-2026-lecture04-rnnlm.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture04-rnnlm.pdf>) |
| 课程讲义 | [[cs224n-2019-notes05-LM_RNN.pdf\|notes]] | [原始链接](<https://web.stanford.edu/class/cs224n/readings/cs224n-2019-notes05-LM_RNN.pdf>) |
| 论文 / 阅读 | [[learning-long-term-dependencies-with-gradient-descent-is-difficult.pdf\|Learning long-term dependencies with gradient descent is difficult]] | [原始链接](<https://ieeexplore.ieee.org/document/279181>)<br>[PDF 下载源](<https://www.comp.hkbu.edu.hk/~markus/teaching/comp7650/tnn-94-gradient.pdf>) |
| 论文 / 阅读 | [[1211.5063-on-the-difficulty-of-training-recurrent-neural-networks.pdf\|On the difficulty of training Recurrent Neural Networks]] | [原始链接](<https://arxiv.org/pdf/1211.5063.pdf>) |
| 链接 | [[vanishing-gradient-demo.html\|Vanishing Gradients Jupyter Notebook]] | [原始链接](<https://web.stanford.edu/class/archive/cs/cs224n/cs224n.1174/lectures/vanishing_grad_example.html>) |
| 论文 / 阅读 | [[06-LLM/90-课程/CS224n/resources/readings/1706.03762-attention-is-all-you-need.pdf\|Attention Is All You Need]] | [原始链接](<https://arxiv.org/abs/1706.03762.pdf>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 为何语言模型既能预测下一词又能给整段文本评分？
2. RNN 的哪部分难以按时间并行？
3. 梯度裁剪能解决梯度消失吗？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
