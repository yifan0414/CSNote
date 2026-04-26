---
title: DYTO-OCG 方法草稿与实验计划
created: 2026-04-27
updated: 2026-04-27
tags:
  - paper/idea
  - paper/draft
  - video-understanding
  - video-qa
  - egoschema
  - dyto
status: draft
related:
  - "[[Paper/Video Understanding 论文综述报告]]"
  - "[[Paper/raw/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/DYTO|DYTO]]"
  - "[[Paper/raw/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/D-CoDe|D-CoDe]]"
  - "[[Paper/raw/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/KTV|KTV]]"
  - "[[Paper/raw/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question|HiCrew]]"
  - "[[Paper/组会汇报/1月8日汇报]]"
  - "[[Paper/组会汇报/12 月 25 日汇报]]"
---

# DYTO-OCG 方法草稿与实验计划

> 核心判断：对于 EgoSchema 这类 long-form multiple-choice VideoQA，DYTO 的主要短板不再是“怎么再多看一点”，而是“如何围绕候选答案组织证据并完成反证式推理”。

## 0. 目标定位

本文希望把 [[Paper/raw/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/DYTO|DYTO]] 从一个强感知压缩前端，扩展成一个面向长视频多选问答的 **training-free evidence reasoning framework**。

一句话概括：

> **DYTO 负责看全，OCG 负责找证据、排干扰、再决策。**

建议方法名：

- **DyTo-OCG**
- 全称：**Dynamic Token Optimization with Option-Contrast Evidence Gathering**

方法的叙事重点不是“改进选帧”，而是：

1. 保留 DYTO 的 question-agnostic 全局覆盖能力；
2. 利用多选题的 option structure 做 hypothesis-driven evidence retrieval；
3. 用 support / refute 双证据机制替代单步直接回答；
4. 在冲突片段上做第二轮 token re-allocation。

---

## 1. 方法章节草稿

## 1.1 Motivation

现有 training-free video understanding 方法大致可以分成两类：

- **Perception compression**：如 [[Paper/raw/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/DYTO|DYTO]]、[[Paper/raw/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/KTV|KTV]]，重点在 temporal redundancy 和 spatial token redundancy；
- **Reasoning orchestration**：如 [[Paper/raw/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/D-CoDe|D-CoDe]]、[[Paper/raw/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question|HiCrew]]，重点在如何消费已有视觉证据。

从 [[Paper/组会汇报/1月8日汇报]] 的实验现象看：

- 直接做 question-aware frame selection 会下降；
- 做 question-aware token merging 虽有提升，但距离 D-CoDe 仍有明显差距；
- 因此 EgoSchema 的主要瓶颈更像是 **reasoning bottleneck** 而非纯粹的 perception bottleneck。

与此同时，EgoSchema 是 5 选 1 的 multiple-choice long-video QA。对这类任务，仅仅回答“哪个选项最像对的”是不够的，模型还需要：

1. 找到支持某个选项的时间片段；
2. 找到反驳其他干扰项的时间片段；
3. 在高冲突片段上投入更多 token 预算；
4. 最终根据支持/反驳证据完成决策。

因此，本文提出一种 training-free 的 **Option-Contrast Evidence Gathering** 框架。

## 1.2 Overview

整体流程如下：

```text
Video
-> DYTO question-agnostic compression
-> Event Bank {e_j, t_j, z_j}

Question Q + options {o_1, ..., o_5}
-> hypothesis construction h_i = [Q ; o_i]
-> support / refute evidence retrieval
-> conflict-aware token re-allocation
-> evidence integration
-> final answer
```

其中：

- $e_j$ 表示第 $j$ 个事件单元；
- $t_j$ 表示对应时间戳或时间段；
- $z_j$ 表示该事件单元的压缩视觉 token。

## 1.3 Stage I: Question-Agnostic Event Bank Construction

第一阶段完全沿用 DYTO 的核心思想，不在早期引入强 question-aware 约束。

目标是得到一个覆盖全局事件结构的 **Event Bank**，避免因为问题语义过早介入而破坏视频的整体时序拓扑。

具体做法：

1. 从原视频中均匀采样初始帧；
2. 使用 DYTO 的时序聚类机制构建粗粒度事件簇；
3. 在每个事件簇内部执行 dynamic token merging，获得压缩后的视觉 token；
4. 为每个事件单元保存：
   - 代表帧；
   - 时间戳；
   - 压缩 token；
   - 可选的简要 caption / summary。

这一阶段的核心原则是：

> **先覆盖，后聚焦。**

## 1.4 Stage II: Option-as-Hypothesis Evidence Retrieval

对每个候选答案 $o_i$，构造一个假设查询：

$$
h_i = [Q; o_i]
$$

然后基于 $h_i$ 对 Event Bank 进行证据检索，而不是直接把所有 token 一次性喂给 LLM。

对于每个事件 $e_j$，计算两类分数：

- **support score**：该事件对选项 $o_i$ 的支持程度；
- **refute score**：该事件对选项 $o_i$ 的反驳程度。

可以用轻量的相似度或 prompt-based scoring 实现，例如：

$$
s^{sup}_{ij} = \text{Sim}(e_j, h_i), \qquad
s^{ref}_{ij} = \text{Contradict}(e_j, h_i)
$$

其中 `Sim` 可由视觉-文本相似度近似，`Contradict` 可由小规模 prompt 验证或“support-minus-others”近似得到。

最终为每个选项检索两组片段：

- top-$k$ support events
- top-$k$ refute events

这样做的好处是：

1. 支持多选题的 hypothesis-style reasoning；
2. 不只是找“最像对的证据”，还显式寻找“为什么别的选项不对”；
3. 更贴合 EgoSchema 中常见的干扰项排除过程。

## 1.5 Stage III: Conflict-Aware Token Re-allocation

第一轮检索后，并不是对所有选项和所有事件做同样精度的处理，而是只对 **高冲突选项** 与 **高争议事件** 做第二轮细化。
定义两类冲突：
1. **option conflict**：前两名候选选项分数接近；
2. **event conflict**：某些事件同时对多个选项具有高相关度，区分性不足。

基于此，对事件单元重新分配 token budget：

$$
b_{ij} = b_0 + \lambda_1 \cdot s^{rel}_{ij} + \lambda_2 \cdot s^{conf}_{ij}
$$

其中：

- $b_0$ 是基础预算；
- $s^{rel}_{ij}$ 是事件对当前选项的相关性；
- $s^{conf}_{ij}$ 是该事件对区分竞争选项的重要性。

对于高预算事件：

- 保留更细粒度 patch tokens；
- 降低 token merging 强度；
- 必要时回到原始帧做局部复查。

对于低预算事件：

- 仅保留 summary token 或 caption。

这一阶段的核心思想是：

> **token 不该平均分，而应花在最能拉开选项差异的证据上。**

## 1.6 Stage IV: Evidence Integration and Final Decision

对每个选项，整合其 support / refute 证据，得到最终的 evidence score：

$$
S_i = \sum_j \alpha \, s^{sup}_{ij} - \beta \, s^{ref}_{ij}
$$

然后将高置信证据片段与原问题一起输入 LLM，生成最终判断：

```text
[Question]
[Option_i]
[Support evidence: timestamps + captions/tokens]
[Refute evidence: timestamps + captions/tokens]
-> option-level verdict
```

最后在 5 个选项中选出 evidence score 最高者作为答案。

该过程相对于 DYTO 的单步推理：

```text
VideoTokens + Q -> Answer
```

升级为：

```text
VideoTokens + Q + option-wise support/refute evidence -> Answer
```

## 1.7 Claimed Contributions

如果写成论文，贡献点可以表述为：

1. **提出一种 training-free 的 option-contrast evidence framework**，将 long-form multiple-choice VideoQA 从单步回答转化为 hypothesis-driven evidence gathering。
2. **提出 conflict-aware token re-allocation 机制**，在不破坏全局时序覆盖的前提下，将视觉预算集中到最具判别性的时间片段。
3. **将 DYTO 从纯感知压缩器扩展为可插拔的证据前端**，并可与其他 training-free 压缩方法（如 KTV）兼容。

## 1.8 与已有工作的区别

### 相比 DYTO

- DYTO：主要解决 frame / token compression；
- DyTo-OCG：解决 option-aware evidence acquisition 与 final reasoning。

### 相比 D-CoDe

- D-CoDe：question decomposition；
- DyTo-OCG：option-contrast evidence gathering。

### 相比 HiCrew

- HiCrew：multi-agent heavy system；
- DyTo-OCG：lightweight、training-free、可接现有前端压缩器。

---

## 2. 实验计划表

## 2.1 研究问题

需要优先回答以下问题：

### RQ1
**只改变推理结构，不改变 DYTO 压缩前端，是否就能超过当前 question-aware token merging 的 50.4？**

### RQ2
**option-conditioned evidence retrieval 是否优于 question-only retrieval？**

### RQ3
**support + refute 是否优于 support-only？**

### RQ4
**adaptive token budget 是否优于 fixed budget？**

### RQ5
**该框架是否对 KTV 这类其他前端同样有效？**

## 2.2 数据集与评测

### 主数据集

- **EgoSchema**：主战场，long-form、multiple-choice、schema-level reasoning

### 辅助数据集

- **NExT-QA**：可按 Temporal / Causal / Descriptive 分析
- **IntentQA**：验证意图与因果推理

### 可选泛化集

- VideoMME
- MVBench

### 指标

- Accuracy
- Visual token count
- Inference latency
- Accuracy / token Pareto

## 2.3 必须比较的 Baselines

| 类型          | Baseline                                                                                                                                                                        | 作用                        |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| 简单采样        | SlowFast-LLaVA                                                                                                                                                                  | 基础 training-free baseline |
| 动态压缩        | [[Paper/raw/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/DYTO\|DYTO]]                                                                                | 主对比对象                     |
| 高效 token 选择 | [[Paper/raw/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/KTV\|KTV]]                                                                            | 效率对比                      |
| 推理增强        | [[D-CoDe]]                                                                                                                                                                      | reasoning upper reference |
| 系统上限        | [[Paper/raw/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question\|HiCrew]] | 高成本参考上限                   |

## 2.4 最小可行实验路线

### V0：Option-wise prompting

不改压缩，只改推理：

- 同一组 DYTO video tokens
- 分别对 5 个 option 做独立判断
- 再汇总最终答案

目标：

- 验证“单步回答”是否真的是当前瓶颈。

### V1：Option-conditioned retrieval

在 V0 基础上加入：

- 每个选项只检索 top-$k$ 相关事件
- 不做反驳证据，仅做 support evidence

目标：

- 验证 option-as-hypothesis 是否有效。

### V2：Support + Refute

在 V1 基础上加入：

- 对每个 option 同时收集 support / refute 事件

目标：

- 验证反证机制能否帮助排除干扰项。

### V3：Conflict-aware re-budgeting

在 V2 基础上加入：

- 对 top-2 冲突选项及高争议事件做第二轮 token 分配

目标：

- 验证 adaptive budget 是否带来额外提升。

## 2.5 关键消融实验

| Ablation | 目的 |
|---|---|
| single-pass vs option-wise reasoning | 证明推理结构收益 |
| question-only vs option-conditioned retrieval | 证明 option structure 被有效利用 |
| support-only vs support+refute | 证明反证机制有效 |
| fixed budget vs adaptive budget | 证明预算分配有效 |
| DYTO front-end vs KTV front-end | 证明框架可插拔 |
| with / without second-pass zoom-in | 证明局部复查有价值 |

## 2.6 诊断分析

建议重点画以下图：

1. **Accuracy vs visual tokens**  
   展示与 DYTO / KTV 的 Pareto 对比。

2. **按证据链长度分桶的 EgoSchema 准确率**  
   证明提升主要来自长证据链样本。

3. **Option-level evidence timeline**  
   用时间轴展示 support / refute 片段。

4. **Error transition analysis**  
   展示 baseline 的错误有多少被“排除干扰项”修正。

5. **Budget allocation heatmap**  
   展示第二轮 token 分配聚焦到了哪些时间段。

## 2.7 预期风险

| 风险 | 表现 | 规避方式 |
|---|---|---|
| evidence retrieval 偏移 | 找到相关但非判别性片段 | 保留全局 event bank，必要时扩大 top-k |
| refute scoring 不稳定 | 反证噪声大 | 先做 support-only，再逐步加入 refute |
| 二轮推理过贵 | latency 上升明显 | 只对 top-2 竞争选项触发 zoom-in |
| 与 D-CoDe 过近 | 被认为只是 decomposition 变体 | 强调 option-contrast 而非 sub-question decomposition |

## 2.8 按周拆解任务

### Week 1：复现实验底座

- 整理 DYTO 当前 EgoSchema 复现脚本
- 固化 baseline：48.0 / 50.4 两个版本
- 统一日志记录：accuracy、tokens、latency

### Week 2：V0 实现

- 实现 option-wise prompting
- 完成 single-pass vs option-wise 对比
- 判断“只改推理结构”是否带来第一波增益

### Week 3：V1 实现

- 构建 event bank 索引
- 实现 option-conditioned retrieval
- 调 top-$k$、不同相似度策略

### Week 4：V2 实现

- 加入 support / refute 双证据
- 分析哪些题主要靠反证收益提升
- 保存可视化 case

### Week 5：V3 实现

- 加入 conflict-aware re-budgeting
- 做 top-2 option 二轮 zoom-in
- 跑 accuracy / tokens / latency Pareto

### Week 6：整理论文素材

- 完成主表、消融表、案例图
- 总结与 DYTO / D-CoDe / KTV 的差异叙事
- 写出方法章节初稿与实验章节框架

---

## 3. 当前最值得先验证的两个点

如果只做最小代价验证，优先顺序如下：

1. **V0：只改推理结构，看能否超过 50.4**
2. **V1：加入 option-conditioned retrieval，看是否继续上涨**

如果这两步成立，说明这条线值得继续投入。

---

## 4. 一句话结论

> DYTO 后续最值得做的创新，不是继续深挖 question-aware frame selection，而是把它作为前端压缩器，向上做 **option-aware evidence gathering + conflict-aware token allocation + support/refute reasoning**。
