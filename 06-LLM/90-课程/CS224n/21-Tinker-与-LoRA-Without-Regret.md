---
title: "CS224N 21 Tinker 与 LoRA Without Regret"
aliases:
  - "Guest Lecture: Tinker and LoRA Without Regret (by John Schulman )"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 21
date_text: "Thu Mar 5"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 21：Tinker 与 LoRA Without Regret

> [!abstract] 本节定位
> 官网没有公开课件或指定阅读；本页依据讲者发布的 Tinker、Tinker Docs 与 LoRA Without Regret 一手资料，整理训练 API 与 LoRA 低遗憾区间。

> [!warning] 资料范围
> 官网对本节只列出标题和讲者，没有公开 PPT、讲义或指定阅读。知识正文使用讲者在 Thinking Machines Lab 发布的 Tinker、Tinker Docs 与 LoRA Without Regret 一手资料，不声称是未公开讲座的逐页内容。

## 学习目标

- [ ] 区分算法接口与训练基础设施接口
- [ ] 识别 LoRA 与全参数微调比较中的混杂因素
- [ ] 设计同数据和同计算预算下的适配实验

## 知识笔记

> [!warning] 资料边界
> CS224N 官网只给出本节标题和讲者，没有发布 PPT 或指定阅读。以下笔记使用讲者 John Schulman 在 Thinking Machines Lab 发布的一手资料：[Tinker](https://thinkingmachines.ai/tinker/)、[Tinker Docs](https://tinker-docs.thinkingmachines.ai/) 和 [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/)。产品支持模型和接口细节可能随时间变化，本节只整理稳定方法论。

## 1. Tinker 要抽象什么

大模型后训练同时包含两个层面：

### 算法层

- SFT；
- DPO；
- policy gradient；
- GRPO/PPO；
- distillation；
- continual learning。

### 基础设施层

- 分布式 GPU；
- 模型并行；
- rollout serving；
- 权重同步；
- checkpoint；
- 故障恢复；
- 资源调度。

Tinker 的设计目标是让研究者在本地写训练循环，由远程基础设施执行大模型计算。

## 2. 四个核心原语

官方页面用四个函数描述接口。

### forward_backward

执行前向与反向，累加梯度：

$$
g
\leftarrow
g+\nabla_\theta L.
$$

这允许：

- 多 micro-batch 累加；
- 自定义 loss；
- SFT、DPO 和 distillation 共用底层接口。

### optim_step

根据已累积梯度更新权重：

$$
\theta\leftarrow\operatorname{Optimizer}(\theta,g).
$$

将“计算梯度”和“何时更新”分开，便于 gradient accumulation 和非标准训练。

### sample

从当前模型生成 token，用于：

- 交互；
- 评测；
- RL rollout；
- on-policy distillation；
- 合成数据。

### save_state

保存 adapter、optimizer 或训练状态，用于恢复、比较和部署。

## 3. 为什么小原语很重要

若 API 只提供固定的 `train(dataset)`：

- 很难交替采样与更新；
- 很难实现自定义 reward；
- 很难读取 log probabilities；
- 无法实验 off-policy correction；
- 算法研究被平台预设限制。

小原语让上层算法由用户组合，同时基础设施仍由服务管理。

## 4. LoRA 回顾

全参数微调：

$$
W'=W+\Delta W.
$$

LoRA：

$$
W'
=
W+\gamma BA,
$$

其中：

$$
A\in\mathbb{R}^{r\times d_{\text{in}}},
\qquad
B\in\mathbb{R}^{d_{\text{out}}\times r}.
$$

常用：

$$
\gamma=\frac{\alpha}{r}.
$$

基座 $W$ 冻结，只更新 $A,B$。

## 5. 为什么后训练特别适合 LoRA

预训练要从海量 token 吸收广泛知识，需要巨大参数容量。

后训练通常：

- 数据小得多；
- 领域更窄；
- 主要改变行为；
- 新信息量远小于基座参数量。

因此用完整 trillion-parameter 权重表示较小更新可能浪费。

## 6. LoRA 的三个系统优势

### 6.1 Multi-Tenant Serving

一个基座模型同时服务多个 adapter：

$$
W_i'
=
W+\Delta W_i.
$$

服务器共享 $W$，按请求选择 $\Delta W_i$，可在同 batch 服务多个任务。

### 6.2 训练 Layout

FullFT 需为全部参数保存：

- weight；
- gradient；
- optimizer moments；
- master precision copy。

训练内存常远高于纯采样。

LoRA 只为少量参数保存训练状态，使训练布局更接近推理布局。

### 6.3 传输与版本

小 adapter：

- 上传下载快；
- checkpoint 频繁；
- 回滚容易；
- 每个实验只保存增量。

## 7. 核心问题：LoRA 能否匹配 FullFT

“参数少”只说明存储效率，不保证：

- sample efficiency；
- compute efficiency；
- 最终性能；
- 优化稳定性。

官方研究系统改变：

- LoRA rank；
- 数据集大小；
- 模型大小；
- learning rate；
- batch size；
- LoRA 作用层；
- SFT 与 RL。

并用 log loss 等连续指标比较学习曲线，而非只看单个采样评测。

## 8. Rank 与容量

高 rank LoRA 在小到中等后训练数据上可与 FullFT 有相近学习曲线。

当训练信息超过 adapter 容量，表现不是突然撞到一个硬 loss floor，而是：

- 学习效率逐渐下降；
- 较低 rank 更早偏离最优曲线；
- 最终 loss 更高。

因此 rank 应与：

- 数据量；
- 任务复杂度；
- 模型层数；
- 作用矩阵数量

共同考虑。

## 9. Capacity 与 Dataset Size

LoRA 可训练参数：

$$
P_{\text{LoRA}}
=
\sum_{\ell}
r_\ell
\left(
d_{\text{in},\ell}
+d_{\text{out},\ell}
\right).
$$

“低遗憾区间”的直觉条件：

$$
\text{adapter capacity}
\gtrsim
\text{training data 中需要吸收的有效信息}.
$$

有效信息不等于文件字节数或 token 数，但数据规模可作经验代理。

## 10. Batch Size 效应

研究发现某些设置下 LoRA 对大 batch 比 FullFT 更敏感：

- batch 增大后 loss penalty 更大；
- 提高 rank 不一定消除；
- 可能来自 $BA$ 乘积参数化的优化动力学。

这说明：

> [!important]
> 容量足够不等于优化轨迹与 FullFT 相同。

比较时要对两者分别调 batch 和 learning rate，不能直接复用 FullFT 超参数。

## 11. LoRA 应作用于哪些层

Attention-only 是常见旧默认，但研究发现：

- 只作用 attention 明显较弱；
- MLP-only 可明显更好；
- all layers 与 MLP-only 常接近或更优；
- 在参数量匹配后，attention-only 仍可能落后；
- MoE 中 expert MLP 也需要 LoRA。

原因可能是：

- 大部分参数和函数容量位于 MLP/MoE；
- attention-only 限制了可更新特征变换；
- 参数位置比参数总数本身重要。

## 12. RL 为什么低 Rank 也可能足够

监督学习每个输出 token 都提供目标 token 信息，单个序列可包含 $O(T)$ 级训练信号。

Outcome-based policy gradient 常只给每个 episode 一个或少数 reward/advantage：

$$
R(y)\in\mathbb{R}.
$$

有效信息密度可能低很多。

官方实验中，低 rank LoRA 在数学 RL 上也可匹配 FullFT，甚至 rank 1 仍有足够参数容纳奖励提供的有限信息。

这不是“RL 永远只需 rank 1”，因为：

- process reward 更稠密；
- 多领域任务信息量更高；
- 长训练可能耗尽容量；
- reward 和 policy 分布会变化。

## 13. $\alpha/r$ 与 Rank

参数化：

$$
W'
=
W+\frac{\alpha}{r}BA.
$$

若 $B$ 初始化为 0，训练初期只有 $B$ 的变化直接影响 $BA$。

$1/r$ 缩放使不同 rank 的多个 rank-1 更新取平均，预期初始更新尺度对 rank 较稳定。

因此最佳 learning rate 对 rank 可能近似不变，尤其在训练早期。

## 14. LoRA Learning Rate

官方实验观察到：

- LoRA 的最佳 LR 通常高于 FullFT；
- 在测试的 Llama/Qwen SFT 与 RL 条件中，经验比例约为 10 倍；
- 短训练可能需要更高比例；
- 这是实验规律，不是通用数学常数。

公平比较必须为每个方法独立 sweep LR。用同一 LR 比较常会错误地得出 LoRA 性能较差。

## 15. 初始化动力学

常见：

$$
A\sim\text{random},
\qquad
B=0.
$$

开始时：

$$
BA=0.
$$

早期 $B$ 先增长，$A$ 的更新对输出影响较小；随着 $B$ 变大，$A$ 更新的有效作用增强。

所以 LoRA 的有效学习率存在隐式时间变化，短跑与长跑的最优超参数可能不同。

## 16. Low-Regret Regime

LoRA 接近 FullFT 的两个主要条件：

1. **覆盖正确层**：尤其 MLP/MoE，而非只更新 attention；
2. **容量未耗尽**：trainable parameters 足以吸收数据中的有效信息。

在该区间：

- 学习曲线接近；
- 样本效率接近；
- 最终性能接近；
- 系统和部署优势显著。

超出区间时，应提高 rank、扩大作用层或选择 FullFT。

## 17. 推荐实验流程

1. 先定义 FullFT baseline；
2. 两者分别 sweep LR；
3. LoRA 至少覆盖 MLP，并测试 all-layer；
4. 从中等 rank 开始；
5. 绘制 loss vs steps，而不只看最后 benchmark；
6. 改变数据量，观察何时偏离；
7. 测 batch sensitivity；
8. 报告 trainable parameters、峰值内存和真实吞吐；
9. RL 中同时测 reward、held-out benchmark 和行为。

## 18. Tinker 与 LoRA 的关系

LoRA 使云训练 API 更容易：

- 基座权重共享；
- 用户状态小；
- checkpoint 轻；
- 训练布局接近 rollout；
- 多模型版本可快速切换。

Tinker 提供的采样、梯度和更新原语，又允许用户在 LoRA 参数空间实现不同后训练算法。

## 19. API 使用时仍需负责什么

基础设施抽象不会替研究者决定：

- 数据是否合法和高质量；
- reward 是否可被利用；
- rollout 是否 stale；
- loss 是否正确；
- 评测是否污染；
- adapter 是否泄露训练数据；
- 费用和停止条件。

抽象减少的是集群管理，不是实验方法责任。

## 20. 小结

- Tinker 以 forward/backward、optimizer step、sample 和 save state 组合后训练算法。
- LoRA 的优势包括多租户服务、更小训练状态和快速传输。
- LoRA 能否匹配 FullFT 取决于容量、作用层和优化条件。
- Attention-only LoRA 可能明显弱于 MLP/all-layer LoRA。
- 大 batch 对 LoRA 的惩罚可能无法靠提高 rank 解决。
- Outcome RL 的信息密度低，低 rank LoRA 也可能足够。
- “LoRA without regret”是有条件区间，不是对所有数据规模与任务的无条件保证。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| 链接 | John Schulman（仅在线） | [原始链接](<http://joschu.net/>) |

> [!note] PPT 状态
> 官网课表没有提供本节 PPT 链接；当前目录不存在可下载的官方课件。

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 比较 LoRA 时还要报告哪些成本？
2. 如何保证 LoRA 与全参数微调获得同等调参机会？
3. 训练 API 需暴露哪些原语才能支持 SFT、DPO 和 RL？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
