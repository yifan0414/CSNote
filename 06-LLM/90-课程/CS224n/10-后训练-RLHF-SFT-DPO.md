---
title: "CS224N 10 后训练：SFT、RLHF 与 DPO"
aliases:
  - "Post-training (RLHF, SFT, DPO)"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 10
date_text: "Thu Jan 29"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 10：后训练：SFT、RLHF 与 DPO

> [!abstract] 本节定位
> 从指令微调到偏好学习，理解奖励建模、PPO/RLHF 与 DPO 的数据流、目标和限制。

## 学习目标

- [ ] 画出 SFT 到 RLHF 的完整管线
- [ ] 解释奖励模型为何只是人类偏好的代理
- [ ] 比较 PPO 式 RLHF 与 DPO 的优化对象

## 知识笔记

> [!info] 课件范围
> 对应 Post-training PPT 第 8–64 页：instruction fine-tuning、偏好数据、reward model、policy gradient、PPO/RLHF、InstructGPT、限制、DPO 以及人类反馈与 AI 反馈。

## 1. 为什么预训练模型不是天然助手

预训练优化：

$$
\max_\theta
\sum_t\log P_\theta(x_t\mid x_{<t}).
$$

它学习“互联网文本接下来像什么”，而不是：

- 用户希望完成什么；
- 回答是否有帮助；
- 不知道时是否应该拒答；
- 哪些内容有风险；
- 输出应遵循什么格式。

因此，language modeling 与 assisting users 不是同一个目标。

## 2. Instruction Fine-Tuning

构造指令–回答数据：

$$
\mathcal D_{\text{SFT}}
=
\{(x_i,y_i)\}.
$$

训练：

$$
L_{\text{SFT}}
=
-\sum_i\log P_\theta(y_i\mid x_i).
$$

通常只在回答 token 上计算 loss，prompt token 被 mask。

### 数据来源

- 人工编写指令和示范；
- 将已有 NLP 数据集改写成自然语言指令；
- 多任务混合；
- 强模型生成再人工筛选；
- 自举式 instruction generation。

### 为什么有效

SFT 不一定加入大量新事实，更多是在学习：

- 任务识别；
- 对话角色；
- 输出格式；
- 风格；
- 何时使用已有预训练知识。

### 多任务扩展

任务多样性往往比单任务重复样本更重要。统一指令格式使模型能在训练任务间共享策略，并提高未见任务的 zero-shot 泛化。

## 3. SFT 的局限

示范只告诉模型“一个可接受答案”，不容易表达：

- 两个答案谁更好；
- 帮助性与安全性的权衡；
- 多个都正确但风格不同的答案；
- 边界情况下应该拒答还是回答。

此外，最大似然会模仿示范中的全部性质，包括冗长、偏见和标注错误。

## 4. 从人类反馈学习

给同一 prompt $x$ 采样两个回答：

$$
y_w\succ y_l,
$$

其中 $y_w$ 是偏好回答，$y_l$ 是不偏好回答。

偏好数据比标量打分更容易获得稳定判断，因为标注者只需比较。

## 5. Reward Model

奖励模型输出：

$$
r_\phi(x,y)\in\mathbb{R}.
$$

Bradley–Terry 模型将得分差变成偏好概率：

$$
P(y_w\succ y_l\mid x)
=
\sigma
\left(
r_\phi(x,y_w)-r_\phi(x,y_l)
\right).
$$

损失：

$$
L_{\text{RM}}
=
-\mathbb E
\log\sigma
\left(
r_\phi(x,y_w)-r_\phi(x,y_l)
\right).
$$

只约束相对差，因此奖励的绝对零点没有唯一意义。

### Reward model 学到的不是“真价值”

它近似的是：

- 某组标注者；
- 在某套规范下；
- 对某类 prompt；
- 在给定候选回答分布中

表现出的偏好。

分布变化后，reward model 可能被利用。

## 6. Policy Gradient

目标：

$$
J(\theta)
=
\mathbb E_{y\sim\pi_\theta(\cdot\mid x)}
[R(x,y)].
$$

REINFORCE：

$$
\nabla_\theta J
=
\mathbb E
\left[
R(x,y)
\nabla_\theta\log\pi_\theta(y\mid x)
\right].
$$

含义：高奖励样本的 log probability 被提高，低奖励样本被降低。

### Baseline

减去与动作无关的 baseline 不改变期望梯度：

$$
A=R-b.
$$

它降低方差。PPO 中通常训练 value model 估计 baseline。

## 7. KL 约束

若 policy 只最大化 learned reward，可能偏离自然语言分布并 reward hack。

典型目标：

$$
\max_\theta
\mathbb E_{y\sim\pi_\theta}
\left[
r_\phi(x,y)
-\beta
\log
\frac{\pi_\theta(y\mid x)}
{\pi_{\text{ref}}(y\mid x)}
\right].
$$

KL 项让 policy 不要过度偏离 SFT/reference model。

$\beta$：

- 太小：容易利用 reward 漏洞；
- 太大：几乎无法改变行为。

## 8. PPO 式 RLHF 流程

1. 预训练 base LM；
2. 用示范数据训练 SFT model；
3. 从 SFT/policy 采样候选回答；
4. 收集人类排序；
5. 训练 reward model；
6. policy 在线采样；
7. reward model 打分；
8. 加 KL penalty；
9. 用 PPO 更新 policy；
10. 重复并独立评测。

PPO 常同时维护：

- policy；
- reference policy；
- reward model；
- value model。

因此显存、采样系统和超参数都很复杂。

## 9. PPO 为什么需要 clipping

重要性比率：

$$
r_t(\theta)
=
\frac{\pi_\theta(a_t\mid s_t)}
{\pi_{\theta_{\text{old}}}(a_t\mid s_t)}.
$$

clipped objective：

$$
L^{\text{clip}}
=
\mathbb E_t
\left[
\min
\left(
r_tA_t,
\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)A_t
\right)
\right].
$$

它限制一次更新把新 policy 推得过远，改善训练稳定性。

## 10. InstructGPT 的意义

课件用 InstructGPT 说明：

- 较小但经过人类反馈训练的模型，可能比更大纯预训练模型更受用户偏好；
- alignment 改变的不只是准确率，还包括格式、礼貌、拒答和解释风格；
- 需要同时评估 helpful、honest、harmless，而不能只看 reward。

后训练因此是行为塑形，不只是额外知识训练。

## 11. RLHF 的失败模式

### Reward hacking

policy 找到 reward model 高分但人类不真正喜欢的输出。

### 分布外

reward model 只见过有限回答分布，policy 更新后生成的新模式可能超出训练范围。

### 长度与风格偏见

标注者或 judge 可能偏爱：

- 更长；
- 更自信；
- 更正式；
- 更多列表

的回答，即使事实质量没有提高。

### Sycophancy

若标注者倾向同意自己的立场，模型会学习迎合用户而非坚持事实。

### Alignment tax

过强行为约束可能降低某些原始任务能力、多样性或校准。

## 12. Direct Preference Optimization

DPO 从 KL 正则化的最优 policy 关系出发，把隐式 reward 写成：

$$
r_\theta(x,y)
=
\beta
\log
\frac{\pi_\theta(y\mid x)}
{\pi_{\text{ref}}(y\mid x)}
+C(x).
$$

代入成对偏好模型，$C(x)$ 抵消：

$$
L_{\text{DPO}}
=
-\mathbb E
\log\sigma
\left[
\beta
\left(
\log\frac{\pi_\theta(y_w\mid x)}
{\pi_{\text{ref}}(y_w\mid x)}
-
\log\frac{\pi_\theta(y_l\mid x)}
{\pi_{\text{ref}}(y_l\mid x)}
\right)
\right].
$$

它直接：

- 提高 chosen 相对 reference 的概率；
- 降低 rejected 相对 reference 的概率；
- 不显式训练 reward/value model；
- 不需要在线 RL rollout。

## 13. DPO 与 PPO 的比较

| 维度 | PPO/RLHF | DPO |
| --- | --- | --- |
| 数据 | 在线或迭代采样 | 固定偏好对 |
| Reward model | 显式 | 隐式在偏好损失中 |
| Value model | 通常需要 | 不需要 |
| 稳定性 | 系统与超参数复杂 | 更接近监督学习 |
| 探索 | 可由当前 policy 探索 | 受离线数据覆盖限制 |
| 分布更新 | 可在线跟随 | 易产生 off-policy mismatch |

DPO 去掉了显式 RL 组件，但没有消除偏好数据、reference model 和分布覆盖问题。

## 14. 人类反馈与 AI 反馈

### 人类反馈

优势：

- 能判断开放式质量；
- 可表达规范与语境。

限制：

- 贵且慢；
- 标注者之间分歧；
- 复杂领域需要专家；
- 劳动条件与心理风险。

### AI Feedback

使用强模型生成、批评或排序。优势是规模大、成本低；风险：

- 复制 judge 偏见；
- 自举导致错误强化；
- 偏爱相似模型风格；
- 对新风险缺少独立判断。

可靠流程应保留人类校准和独立 holdout。

## 15. 小结

- 预训练预测互联网文本，SFT 将模型调整为遵循指令。
- 偏好数据通过相对比较表达回答质量。
- Reward model 是有限人群与数据下的代理，不是真实价值函数。
- PPO/RLHF 用在线采样、价值估计、clipping 和 KL 约束优化行为。
- DPO 把偏好优化改写为相对 reference model 的监督损失。
- 后训练必须独立评估 reward hacking、迎合、校准、公平和能力退化。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[cs224n-2026-lecture08-posttraining.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture08-posttraining.pdf>) |
| 链接 | Aligning language models to follow instructions（仅在线） | [原始链接](<https://openai.com/research/instruction-following>) |
| 论文 / 阅读 | [[2210.11416-scaling-instruction-finetuned-language-models.pdf\|Scaling Instruction-Finetuned Language Models]] | [原始链接](<https://arxiv.org/abs/2210.11416>) |
| 论文 / 阅读 | [[2305.14387-alpacafarm-a-simulation-framework-for-methods-that-learn-from-human-feedback.pdf\|AlpacaFarm: A Simulation Framework for Methods that Learn from Human Feedback]] | [原始链接](<https://arxiv.org/abs/2305.14387>) |
| 论文 / 阅读 | [[2306.04751-how-far-can-camels-go-exploring-the-state-of-instruction-tuning-on-open-resources.pdf\|How Far Can Camels Go? Exploring the State of Instruction Tuning on Open Resources]] | [原始链接](<https://arxiv.org/abs/2306.04751>) |
| 论文 / 阅读 | [[2305.18290-direct-preference-optimization-your-language-model-is-secretly-a-reward-model.pdf\|Direct Preference Optimization: Your Language Model is Secretly a Reward Model]] | [原始链接](<https://arxiv.org/abs/2305.18290>) |
| 项目文档 | [[Project_Proposal_Instructions.pdf\|handout]] | [原始链接](<https://web.stanford.edu/class/cs224n/project/Project_Proposal_Instructions.pdf>) |
| 项目文档 | [[DFP_Instructions.pdf\|handout]] | [原始链接](<https://web.stanford.edu/class/cs224n/project/DFP_Instructions.pdf>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. SFT 与偏好数据分别提供什么信号？
2. KL 惩罚在 RLHF 中防止什么？
3. DPO 去掉 RL 后保留了哪个参考约束？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
