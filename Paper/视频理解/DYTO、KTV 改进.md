---
创建时间: 2026-05-17 17:40
tags:
---
我觉得最值得做的方向是：

**端到端成本感知的自适应 Keyframe + Token Compression**

也就是专门打 KTV 的弱点：它 LLM 推理快，但 DINOv 2 5400 帧预处理很重；同时吸收 DYTO 的优点：动态 token merging 更在线、更轻，但 token budget 仍偏大。

可以把论文动机写成：

```text
KTV is fast after keyframes are cached, but expensive before inference.
DYTO is more online-friendly, but retains more visual tokens.
We target true end-to-end efficient video LLM inference.
```

**我最推荐的具体方向**

做一个 **adaptive budget scheduler**：

```text
视频 + 问题
 -> 低成本初筛帧，不固定 5400
 -> 动态决定需要看多少帧
 -> 选 keyframes
 -> 对关键帧做 prune + merge 混合压缩
 -> 如果模型不确定，再补充视觉 token 或额外帧
 -> LLM 输出答案
```

核心创新点可以是三块。

**1. 不固定 5400 帧，而是自适应候选池**

KTV 固定最多 5400 帧，这是复现可以，但做新方法时就是明显突破口。

你可以设计：

```text
easy video: 128/256 candidate frames
medium video: 512/1024 candidate frames
hard video: 2048/5400 candidate frames
```

难度由低成本信号判断，比如：

```text
scene change density
frame feature novelty
motion magnitude
question type
initial VLM confidence
```

这样你的卖点就是：

```text
same or better accuracy, much lower end-to-end latency than KTV
```

这比单纯“我也选关键帧”更有论文价值。

**2. 把 KTV 的 pruning 和 DYTO 的 merging 合起来**

KTV 是直接丢 token：

```text
important + non-redundant -> keep
others -> drop
```

DYTO 是合并 token：

```text
similar tokens -> merge
```

一个自然的新方法是：

```text
salient tokens: keep
redundant but useful tokens: merge
low-value tokens: prune
```

这样比 KTV 少丢信息，比 DYTO 更省 token。

可以叫成类似：

```text
select-then-merge
prune-merge hybrid
recoverable token compression
```

**3. 问题感知 token/frame budget**

不是所有问题都需要同样多的视频信息。

比如：

```text
"What color is the object?" -> 少帧，高空间分辨率
"What happened before/after?" -> 多帧，低空间 token
"What is the main goal?" -> 少量 representative keyframes
"Count / OCR / fine detail" -> 保留更多局部 token
```

这可以做成 training-free，也可以做一个很小的 learned controller。  
如果你想保持和 KTV/DYTO 一样的 training-free 设定，那就用规则或 LLM question parser。

**一个比较完整的论文题目方向**

可以是：

```text
End-to-End Adaptive Visual Token Scheduling for Training-Free Video LLMs
```

或者：

```text
Beyond Cached Keyframes: Latency-Aware Adaptive Frame and Token Compression for Video LLMs
```

**对比 baseline 时的亮点**

你可以这样定位：

| 方法 | 帧选择 | token 压缩 | 是否考虑端到端耗时 |
|---|---|---|---|
| DYTO | 100 帧内动态选择 | token merging | 部分考虑 |
| KTV | DINOv 2 5400 候选池 KMeans | token pruning | 主要强调 cached inference |
| 你的方法 | adaptive candidate pool | prune + merge + budget scheduler | 明确优化 end-to-end |

**我不建议做的方向**

不建议只做：

```text
把 KTV 的 DINOv2 换成 CLIP
把 KMeans 换成别的聚类
把 token score 改一个公式
```

这些容易显得 incremental，而且 KTV 已经强调 CLIP 选帧有 semantic trap。除非你能证明新 selector 同时更快、更准、更稳，否则贡献不够硬。

**最有胜算的实验设计**

你应该同时报：

```text
DINO/selector time
CLIP/ranking time
vision encoder time
LLM generation time
total end-to-end time
accuracy
visual token count
GPU memory
```

然后证明：

```text
比 KTV 端到端快很多
比 DYTO token 更少或精度更高
在 cached-keyframe 和 raw-video 两种设置下都公平比较
```

我个人最看好的是这个方向：

```text
Adaptive candidate pool + hybrid prune/merge + uncertainty-triggered extra visual evidence
```

它正好站在 KTV 和 DYTO 的中间，而且能抓住 KTV 当前最明显的漏洞：**只说推理快，但关键帧预处理太重**。


能，但前提是你不能只追求“更快”。如果设计得好，它有机会同时提高准确度；如果只是把 `5400` 降到 `512` 或粗暴压 token，大概率会掉点。

我觉得最有希望提高准确度的部分是这三个。

**1. 自适应候选池可能提高准确度**

KTV 固定从最多 5400 帧里 KMeans 选 6 帧，但它是 question-agnostic 的。问题是：代表性强的帧，不一定对当前问题最有用。

比如问题问：

```text
Why did the person pick up the phone?
What happened right before the object fell?
```

KMeans 可能选到场景代表帧，但漏掉短暂动作或因果事件。

你的方法如果先用低成本方式识别：

```text
动作变化点
场景转折点
question-relevant temporal windows
high-motion segments
```

再选关键帧，有机会比 KTV 更准。

**2. prune + merge hybrid 也可能提高准确度**

KTV 是直接 prune token。直接丢 token 的风险是：一些细节 token 不够“重要”，但它们组合起来对答案有用。

DYTO 的 merge 会保留一部分被压缩的信息，但 token 数更多。

所以 hybrid 策略有潜力：

```text
核心 token：保留
相似但仍有信息的 token：merge
明显无用 token：drop
```

这样理论上比 KTV 少丢信息，比 DYTO 更省 token。这个方向不仅能提速，也可能提准确率。

**3. uncertainty-triggered extra evidence 最可能涨点**

这个我认为最有价值。

第一轮用少量关键帧和 token 快速回答。  
如果模型低置信、不确定、候选答案概率接近，才追加更多帧或更多 token。

这样简单问题不会浪费计算，困难问题能获得额外视觉证据。

它可能带来两种收益：

```text
easy samples: 速度快，准确率不变
hard samples: 多看一些，准确率上升
```

这个比固定 budget 的 KTV/DYTO 更合理。

**但也有风险**

要提高准确度，必须避免这几个坑：

```text
1. 自适应策略错判难度，导致重要帧没看
2. question-aware 选帧被文本先验带偏
3. token merging 把小目标、文字、手部动作等细节抹掉
4. LLM confidence 不可靠，低置信检测不准
```

所以这类工作最关键的不是“提出 adaptive”，而是证明它真的能发现 hard samples，并且追加视觉证据后能改对。

**我会把目标定成这样**

不要只承诺：

```text
更快且不掉点
```

而是争取：

```text
同等 token budget 下，比 KTV/DYTO 更准
同等准确率下，比 KTV/DYTO 更快
困难样本上有明显提升
```

如果你能做到这三点中的两点，就已经是比较强的论文故事了。

我会把这一步做成 **“先低成本回答，再按不确定性追加证据”**，而不是一开始就给所有样本加帧。

核心流程：

```text
Stage 0: 6 keyframes + 936 tokens 快速推理
 -> 判断是不是 hard sample
 -> 如果 easy，直接输出
 -> 如果 hard，追加视觉证据再推理
```

**1. 怎么判断 hard sample**

我建议用 4 个信号，不要只靠一个。

**信号 A：多选答案 margin**

不要只看生成文本，最好对 5 个 candidate 做 log-likelihood 打分：

```text
score(A), score(B), score(C), score(D), score(E)
```

如果 top 1 和 top 2 很接近，就是 hard：

```text
margin = score_top1 - score_top2
margin < threshold => hard
```

这是最直接、最稳定的信号。

**信号 B：多视角答案不一致**

用两套便宜 evidence 各跑一次：

```text
KTV 6 keyframes
uniform 6 frames
```

如果两个答案不一致：

```text
KTV says B, uniform says D => hard
```

这类样本通常确实需要更多 temporal evidence。

**信号 C：问题类型 prior**

有些问题天然更难，应该更容易触发追加帧：

```text
before / after / sequence / why / cause / purpose / overall / throughout
```

这些问题依赖时间顺序或长程因果，6 帧容易漏。

相反：

```text
color / object / scene / where
```

可能更需要空间 token，不一定需要更多帧。

**信号 D：关键帧覆盖质量**

KTV 的 KMeans 如果选出来的 6 帧覆盖不均，或者某些 cluster 方差很大，说明视频内容变化复杂。

可以用 DINOv 2 特征算：

```text
cluster variance 高
adjacent feature change 高
selected frames temporal gap 太大
```

这些也可以标成 hard。

**2. hard 之后追加什么视觉证据**

不要盲目追加均匀帧。我建议按优先级加：

```text
1. top keyframe 的 temporal neighbors
2. KMeans 每个 cluster 的 second-nearest frame
3. DINOv2 feature change 最大的位置
4. CLIP 对 question 最相关的补充帧
```

比如第一轮 KTV 选了 6 帧：

```text
[f1, f2, f3, f4, f5, f6]
```

hard 后追加：

```text
每个高 rank keyframe 周围 +/- 1 个邻近采样点
高方差 cluster 的 runner-up frame
视频中 DINO feature 突变最大的 frames
```

这样比直接从 5400 里重新选 12 帧更稳，因为它既保留 KTV 的 representative frames，也补充了可能被漏掉的动作转折。

**3. token budget 怎么追加**

我会做成两级：

```text
Easy:
6 frames, 936 tokens

Hard level 1:
8-12 frames, 1872 tokens

Hard level 2:
12 frames + local temporal neighbors, 1872/2500 tokens
```

不要无限加，最多一到两轮，否则速度优势没了。

**4. 一个可写成论文算法的版本**

```text
Input: video V, question q

1. KTV selects 6 keyframes.
2. Run VLM with sparse visual budget.
3. Compute hardness H:
   H = low answer margin
     + answer disagreement
     + temporal-question prior
     + visual coverage uncertainty
4. If H < threshold:
   return answer.
5. Else:
   retrieve extra visual evidence from:
   temporal neighbors, high-change frames, cluster runner-ups.
6. Increase token budget only for retrieved frames.
7. Re-run VLM and return final answer.
```

**我最推荐的实现优先级**

先做最简单、最容易出效果的版本：

```text
hard = top1/top2 candidate score margin 小
追加 = KTV keyframes 的 temporal neighbors + DINO change 最大帧
```

这个版本工程成本不高，而且容易证明：

```text
hard samples 上准确率提升
easy samples 不增加计算
整体端到端比固定大 budget 更省
```

这个思路和 Self-RAG 的“on-demand retrieval”精神类似，只是把文本检索换成了视觉证据检索；也能自然对比 KTV 和 DYTO。KTV/DYTO 是固定或一次性压缩，你的方法是 **按不确定性动态补证据**。