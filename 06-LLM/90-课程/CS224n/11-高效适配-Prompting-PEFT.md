---
title: "CS224N 11 高效适配：Prompting 与 PEFT"
aliases:
  - "Efficient Adaptation (Prompting + PEFT)"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 11
date_text: "Week 5 Tue Feb 3"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 11：高效适配：Prompting 与 PEFT

> [!abstract] 本节定位
> 比较 prompting、剪枝、LoRA、prompt tuning 与 adapter，理解效果、显存、存储和服务成本的权衡。

## 学习目标

- [ ] 区分上下文 prompting 与参数高效微调
- [ ] 推导 LoRA 低秩更新的 shape 和参数量
- [ ] 从训练、存储、服务和质量四方面选方法

## 知识笔记

> [!info] 课件范围
> 对应 Efficient Adaptation PPT 第 10–67 页：in-context learning、prompting、PEFT 的参数/输入/函数视角、稀疏子网络、LoRA、prompt tuning、adapter 与部署权衡。

## 1. 什么叫“适配”

预训练模型学习通用分布，适配让它服务特定：

- 任务；
- 领域；
- 语言；
- 用户；
- 输出格式；
- 安全策略。

可改变的对象不只模型全部参数。课件从三个角度组织适配：

1. **参数视角**：改变哪些权重；
2. **输入视角**：学习或设计怎样的 prompt；
3. **函数视角**：在网络中插入怎样的新函数。

## 2. In-Context Learning

将任务描述和示例放进上下文：

$$
\mathcal P
=
[(x_1,y_1),\ldots,(x_k,y_k),x_q].
$$

模型预测：

$$
P(y_q\mid\mathcal P).
$$

### Zero-shot、one-shot、few-shot

- zero-shot：只有任务描述；
- one-shot：一个示例；
- few-shot：少量示例。

参数不更新，适配只在当前上下文中存在。

### ICL 的可能来源

课件讨论“涌现”现象：某些任务在较小模型上接近随机，规模增大后迅速变好。但要谨慎：

- 离散指标可把平滑概率改进显示成突然跳变；
- 模型能力可能早已存在，只是 prompt 未能调用；
- 不同模型系列和训练数据会改变曲线；
- 某些任务还会出现 inverse scaling。

## 3. Prompting

Prompt 可以控制：

- 任务定义；
- 输入输出格式；
- 示例分布；
- 推理步骤；
- 角色和约束。

### Chain-of-Thought

让模型先生成中间步骤，再输出答案，可使复杂任务获得更多计算路径。

但中间文本不必是模型真实内部因果过程。正确答案、可读解释与忠实解释是不同评价目标。

### Prompt 敏感性

模型可能对以下变化敏感：

- 示例顺序；
- 标签词；
- 空格和标点；
- 任务措辞；
- 示例类别分布；
- 是否出现答案格式。

因此 prompt 也是超参数。公平实验必须在 dev set 上选择，再对 test set 固定。

## 4. 为什么需要 PEFT

全参数 fine-tuning 对每个任务保存完整模型，并维护：

- 参数；
- 梯度；
- optimizer 一阶矩；
- optimizer 二阶矩；
- 激活。

对大模型和多任务，这会造成：

- GPU 内存高；
- checkpoint 存储高；
- 每个用户一份模型难以管理；
- 训练和回滚成本高。

PEFT 冻结大部分基座参数，只训练小量任务特定状态。

## 5. 参数视角：稀疏子网络

一个假设是：预训练网络中存在能完成任务的稀疏子网络。

### Lottery Ticket Hypothesis

稠密随机初始化网络中可能包含某个子网络，使用其原始初始化即可独立训练到接近完整网络的性能。

典型过程：

1. 训练稠密网络；
2. 剪掉小权重；
3. 将保留权重重置到早期初始化；
4. 重新训练；
5. 迭代剪枝。

它说明“所需自由度”可能远小于全部参数量，但找到子网络本身可能昂贵。

### 稀疏不等于硬件高效

非结构化 90% 稀疏若仍使用稠密矩阵内核：

- 内存访问不规则；
- FLOPs 未必真正下降；
- 加速器利用率变差。

应分别报告理论非零参数和真实端到端延迟。

## 6. 全参数更新可能是低秩的

全参数 fine-tuning：

$$
W'=W_0+\Delta W.
$$

LoRA 假设任务更新 $\Delta W$ 具有低内在秩：

$$
\Delta W=BA,
$$

其中：

$$
A\in\mathbb{R}^{r\times d_{\text{in}}},
\qquad
B\in\mathbb{R}^{d_{\text{out}}\times r},
\qquad
r\ll\min(d_{\text{in}},d_{\text{out}}).
$$

前向：

$$
y
=
W_0x
+\frac{\alpha}{r}BAx.
$$

$W_0$ 冻结，只训练 $A,B$。

## 7. LoRA 参数量

原层参数：

$$
d_{\text{out}}d_{\text{in}}.
$$

LoRA 参数：

$$
r(d_{\text{in}}+d_{\text{out}}).
$$

若方阵宽度为 $d$：

$$
\frac{\text{LoRA}}{\text{full}}
=
\frac{2rd}{d^2}
=
\frac{2r}{d}.
$$

当 $r\ll d$ 时显著减少可训练参数。

### 初始化

常见做法：

- $A$ 随机初始化；
- $B=0$。

于是训练开始时：

$$
\Delta W=0,
$$

模型行为与基座完全一致。

### 作用层

常见目标：

- attention 的 $W_Q,W_K,W_V,W_O$；
- MLP 投影；
- 有时只作用于 query/value。

不同任务和模型的最佳位置可能不同，必须做消融。

## 8. LoRA 的训练与服务

### 训练收益

- 梯度只存 LoRA 参数；
- optimizer state 大幅减少；
- checkpoint 很小；
- 可为多个任务保存不同 adapter。

### 不会自动消失的成本

- 基座参数仍要参与前向和反向传播；
- 激活仍需保存或重计算；
- 大矩阵乘法仍存在；
- batch 和序列长度仍主导部分成本。

### 合并

推理前可：

$$
W_{\text{merged}}
=
W_0+\frac{\alpha}{r}BA.
$$

合并后不增加线性层推理分支；但动态服务多个 adapter 时不能把所有版本都永久合入同一基座。

## 9. QLoRA

QLoRA 的基本组合：

- 基座权重量化并冻结；
- 用较高精度计算 LoRA；
- 只更新 LoRA 参数。

量化降低基座存储，但不代表训练中的全部计算都在低比特执行。还需区分：

- 权重存储 dtype；
- 计算 dtype；
- optimizer dtype；
- 量化误差和反量化开销。

## 10. 输入视角：Prompt Tuning

学习 $m$ 个连续虚拟 token：

$$
P\in\mathbb{R}^{m\times D}.
$$

将它们拼到输入 embedding：

$$
X'=[P;X].
$$

模型参数冻结，只训练 $P$。

### 与离散 prompt 的区别

- 离散 prompt 是自然语言 token；
- soft prompt 是自由连续向量；
- soft prompt 不必对应可读词；
- 每个任务只需保存一个小矩阵。

### 局限

- 占用上下文长度；
- 小模型上容量可能不足；
- 不容易解释；
- prompt 长度和初始化影响结果。

Prefix tuning 可进一步在多层 attention 的 key/value 中加入可训练前缀。

## 11. 函数视角：Adapter

在 Transformer 层中插入瓶颈网络：

$$
f_\phi(x)
=
W_{\text{up}}
\sigma(W_{\text{down}}x).
$$

其中：

$$
W_{\text{down}}\in\mathbb{R}^{r\times D},
\qquad
W_{\text{up}}\in\mathbb{R}^{D\times r}.
$$

通常与残差组合：

$$
y=x+f_\phi(x).
$$

Adapter 容量通常高于单纯 soft prompt，但会在每层增加真实串行计算，若不融合可能增加延迟。

## 12. 语言 Adapter

课件展示将任务知识与语言知识拆分：

- 用 MLM 在某语言上训练 language adapter；
- 用任务数据训练 task adapter；
- 组合两者支持低资源语言任务。

这是一种模块化迁移思想，但组合是否有效取决于：

- 表示是否兼容；
- tokenizer 是否覆盖；
- 语言与任务 adapter 的训练分布；
- 组合顺序。

## 13. 方法比较

| 方法 | 更新参数 | 上下文成本 | 推理额外路径 | 可切换任务 |
| --- | ---: | ---: | ---: | ---: |
| 离散 Prompt | 0 | 高 | 无 | 很容易 |
| Prompt Tuning | 极少 | 有 | 无额外层 | 容易 |
| LoRA | 少 | 无 | 可合并 | 容易 |
| Adapter | 少 | 无 | 有 | 容易 |
| Full FT | 全部 | 无 | 无 | 需整模型副本 |

不能只比较参数百分比，还要比较：

- 质量；
- 训练峰值显存；
- token/s；
- checkpoint 大小；
- 推理延迟；
- 多租户切换成本。

## 14. 小结

- ICL 通过上下文适配，参数不更新，但对 prompt 很敏感。
- PEFT 可从参数、输入和新增函数三个角度理解。
- LoRA 用低秩矩阵表达权重更新，显著减少训练状态。
- Prompt tuning 学习连续输入，adapter 在层内加入瓶颈函数。
- 参数更少不必然意味着更快；真实系统需要同时测质量、显存、吞吐和延迟。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[cs224n-2026-lecture09-peft.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture09-peft.pdf>) |
| 论文 / 阅读 | [[2005.14165-language-models-are-few-shot-learners.pdf\|Language Models are Few-Shot Learners]] | [原始链接](<https://arxiv.org/abs/2005.14165>) |
| 论文 / 阅读 | [[2201.11903-chain-of-thought-prompting-elicits-reasoning-in-large-language-models.pdf\|Chain-of-Thought Prompting Elicits Reasoning in Large Language Models]] | [原始链接](<https://arxiv.org/abs/2201.11903>) |
| 论文 / 阅读 | [[1803.03635-the-lottery-ticket-hypothesis-finding-sparse-trainable-neural-networks.pdf\|The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks]] | [原始链接](<https://arxiv.org/abs/1803.03635>) |
| 论文 / 阅读 | [[2106.09685-lora-low-rank-adaptation-of-large-language-models.pdf\|LoRA: Low-Rank Adaptation of Large Language Models]] | [原始链接](<https://arxiv.org/abs/2106.09685>) |
| 论文 / 阅读 | [[1902.00751-parameter-efficient-transfer-learning-for-nlp.pdf\|Parameter-Efficient Transfer Learning for NLP]] | [原始链接](<https://arxiv.org/abs/1902.00751>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 一个 dout 乘 din 权重使用秩 r 的 LoRA 时新增多少参数？
2. 可训练参数减少为何更显著影响训练显存而非前向 FLOPs？
3. 何时 prompting 比 PEFT 更合适？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
