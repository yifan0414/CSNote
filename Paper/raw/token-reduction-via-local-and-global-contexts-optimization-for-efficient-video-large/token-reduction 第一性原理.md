---
创建时间: 2026-06-01 08:08
tags:
---
# EarlyTom：第一性原理论文拆解

论文：**EarlyTom: Early Token Compression Completes Fast Video Understanding**，CVPR 2026，核心目标是让 Video-LLM 在不训练、不明显掉精度的情况下更快产生首 token。论文指出：现有视频 token 压缩大多发生在 vision encoder 之后或 LLM 内部，但 vision encoding 本身已经占据 TTFT 的大头；EarlyTom 因此把压缩提前到 vision encoder 内部，并结合后续空间 token 选择。论文报告在 LLaVA-OneVision-7 B 上最高可实现 **2.65× TTFT 降低**、**61% FLOPs 降低**，同时保持接近 full-token baseline 的精度。([arXiv][1])

---

## 1. Task：任务本质与形式化定义

### 1.1 输入、输出、目标

给定：

* 视频帧序列：$V=\{I_1,\dots,I_B\}$  
  其中 $B$ 是采样帧数，例如 LLaVA-OneVision 中使用 32 帧。
* 每帧经 vision encoder 某层表示为：$F_i \in \mathbb{R}^{L\times D}$  
  其中 $L$ 是每帧 visual token 数，$D$ 是隐藏维度。
* 文本 prompt：$x$
* Video-LLM 输出：

  $$
  y = \text{LLM}(\text{Projector}(\text{VisionEncoder}(V)), x)
  $$

优化目标不是“提高视频理解能力”，而是：

$$
\min \ \text{TTFT}, \text{FLOPs}, \text{token processing overhead}
$$

subject to：

$$
\text{Acc}(\hat{V}, x) \approx \text{Acc}(V, x)
$$

也就是在近似保持视频语义充分性的前提下，尽早减少视觉 token 数量。

### 1.2 问题类别

这篇论文属于：

> **training-free inference-time token compression for Video-LLMs**

更具体地说，它不是做模型训练、不是做新 benchmark、不是做新的 video reasoning 架构，而是做：

> **视频视觉 token 的系统级瓶颈重定位 + 早期压缩 + 空间选择偏置修正**

它的核心变量是：压缩发生在 pipeline 的哪个位置。

传统方法多在：

$$
\text{Vision Encoder} \rightarrow \text{Token Compression} \rightarrow \text{LLM Prefill}
$$

EarlyTom 改成：

$$
\text{Vision Encoder 内部压缩} \rightarrow \text{空间 token selection} \rightarrow \text{LLM Prefill}
$$

这使它优化的不只是 LLM prefill token 数，也包括 vision encoder 自身的计算量。

---

## 2. Challenge：传统方法为什么不够

### 2.1 表面问题：视频 token 太多

Video-LLM 的视频输入天然有双重膨胀：

$$
\text{tokens} \propto B \times L
$$

视频越长，帧越多；每帧分 patch 后又产生大量 spatial token。因此推理开销主要来自：

* vision encoder 对每帧/每 token 的编码；
* projector 和 visual token processing；
* LLM prefill 中长视觉上下文的 attention；
* decoder 阶段 KV cache 与自回归生成。

过去很多方法只看到“LLM 输入 token 太多”，于是把压缩点放在 vision encoder 之后。

### 2.2 本质问题：压缩太晚，省不到前面的计算

论文的关键 profiling 发现是：vision encoding 本身已经占 TTFT 的很大部分。在 baseline 中 vision encoding 占 **36.3%** TTFT；而当 HoliTom、VisionZip 等方法已经压缩了 LLM prefill 后，vision encoding 反而变成更突出的瓶颈，分别占 **55.8%** 和 **68.4%**。([CVF 开放获取][2])

从第一性原理看：

$$
\text{Total TTFT} =
T_{\text{vision}} + T_{\text{token-process}} + T_{\text{LLM-prefill}} + T_{\text{overhead}}
$$

如果只优化：

$$
T_{\text{LLM-prefill}}
$$

那么当 $T_{\text{vision}}$ 不变时，总体加速会受 Amdahl’s Law 限制。也就是说，late-stage compression 会遇到一个硬上限：

$$
\text{Speedup} \leq \frac{1}{\text{unoptimized fraction}}
$$

所以 EarlyTom 的根本判断是：

> 真正的瓶颈已经不是“LLM 看到多少 visual token”，而是“这些 visual token 在进入 LLM 前已经花了多少不可回收的计算”。

### 2.3 第二个隐性问题：attention Top-K 会被 vision sink token 欺骗

很多 token selection 方法用 attention score 选 Top-K。但论文观察到视频中存在 **vision sink tokens**：某些固定空间位置在不同帧中持续获得异常高 attention，形成跨帧竖条模式。论文认为这说明 raw attention score 不一定等价于语义重要性，因为部分 attention 被结构性吸引子吸收。([CVF 开放获取][2])

这导致：

$$
\text{TopK}(A) \neq \text{TopK}(\text{semantic importance})
$$

尤其在视频中，真正有用的信息往往是动态变化、局部运动、短时事件，而不是持续高 attention 的静态 sink token。

---

## 3. Insight & Novelty：真正的新想法是什么

### 3.1 创新一：把压缩点前移到 vision encoder 内部

**要解决的问题：**
后处理式压缩只能减少 LLM prefill，无法减少 vision encoder 已经消耗掉的计算。

**Insight：**
如果视频帧之间有大量 temporal redundancy，那么 redundancy 不必等到完整 vision encoding 后才消除；它可以在 encoder 中间层就被消除。

**具体设计：**
EarlyTom 在 vision encoder 的若干层内做 **inner-vision encoder frame merging**。也就是对中间视觉特征帧进行合并，而不是等全部视觉特征算完再压缩。论文整体 pipeline 分为 Stage I 的 encoder 内帧合并和 Stage II 的 decoupled spatial selection。([CVF 开放获取][2])

**为什么有效：**
因为被合并掉的帧后续不再参与后面 vision encoder 层计算，也不再进入 LLM prefill，因此同时减少：

$$
T_{\text{vision}}, \quad T_{\text{LLM-prefill}}, \quad \text{FLOPs}
$$

这是它区别于 VisionZip、HoliTom 等 late-stage 压缩的核心机制。

---

### 3.2 创新二：基于 streaming similarity 的帧分段与局部合并

**要解决的问题：**
视频并不是均匀冗余的。静止片段可以强压缩，转场或动作片段不能盲目合并。

**Insight：**
相邻帧特征相似度可以作为 temporal redundancy 的近似代理；但视频是流式序列，因此需要在线、低开销、局部稳定的分段方式。

**具体设计：**

对相邻帧 $F_t, F_{t-1}$，计算对应空间位置 token 的平均 cosine similarity，并用 EMA 平滑：

$$
\hat{s}_t = \alpha s_t + (1-\alpha)\hat{s}_{t-1}
$$

当：

$$
\hat{s}_t < \tau_{\text{seg}}
$$

则切分 segment。论文将这称为 streaming frame segmentation。([CVF 开放获取][2])

在 segment 内，首尾帧保留，中间帧做局部最优合并。两个中间帧 $F_i, F_{i+1}$ 只有在满足：

$$
s_i > \tau_{\text{merge}}
$$

且：

$$
s_i > s_{i+1}
$$

时才合并。然后使用 similarity-weighted merge：

$$
\hat{F}=\frac{s_iF_i+s_{i+1}F_{i+1}}{s_i+s_{i+1}}
$$

论文声称这样能移除冗余同时保持 temporal consistency。([CVF 开放获取][2])

**为什么有效：**

这相当于把视频分成两类区域：

* 低变化区域：可以合并，减少 encoder 计算；
* 高变化边界：保留，避免破坏事件转折。

从信息论角度看，EarlyTom 不是均匀降采样，而是在估计：

$$
I(F_i; F_{i+1})
$$

如果两帧互信息很高，则其中一部分信息是重复的，可以合并；如果相似度骤降，则说明可能出现新事件或场景变化，应当保留边界。

---

### 3.3 创新三：dynamic/static 解耦的空间 token 选择

**要解决的问题：**
直接对所有帧做 attention Top-K，会偏向 sink tokens，导致空间分布偏移，并可能忽略动态语义区域。

**Insight：**
视频中的帧并不等价。segment 的首尾帧更可能包含状态变化，属于 dynamic frames；中间帧更稳定，属于 static frames。两类帧应该采用不同选择策略。

**具体设计：**

After frame merging，EarlyTom 将帧分为：

$$
\hat{F}^d \in \mathbb{R}^{T\times L\times D}
$$

dynamic part：每个 segment 的 head/tail frames。

$$
\hat{F}^s \in \mathbb{R}^{(N-T)\times L\times D}
$$

static part：segment 中间帧。论文明确说明 head/tail frames 被视为更具判别力。([CVF 开放获取][2])

对 dynamic frames：

$$
I_i=\text{TopK}(A_i,\hat{r})
$$

做 global Top-K，因为动态帧中高 attention token 更可能对应动作或转折信息。

对 static frames：
不是全局 Top-K，而是把 token 序列划分为 local windows，每个 window 选 attention 最高的 token。这样保留空间覆盖，避免所有名额被 sink token 吃掉。论文称 local-window selection 使压缩后的 static frames 分布更接近原始分布。([CVF 开放获取][2])

**为什么有效：**

这相当于同时优化两个目标：

$$
\max \text{importance}
$$

和：

$$
\max \text{spatial diversity}
$$

传统 Top-K 只优化 importance，但在存在 sink token 时 importance estimate 有偏。Local-window Top-K 引入了空间均匀性的归纳偏置：

$$
\text{selected tokens} \sim \text{cover original spatial distribution}
$$

因此它不是单纯追求 attention 大，而是在 attention 与 diversity 之间做折中。

---

### 3.4 创新四：CPU-GPU 异构 co-design

**要解决的问题：**
token selection 本身也可能成为额外开销，尤其是 late-stage 方法会引入 non-trivial token processing overhead。

**Insight：**
static token selection 的计算结构较规则，可以部分转移到 CPU；GPU 保留更关键、更重的 dynamic selection。这样利用原本空闲的 CPU，减少 GPU pipeline 阻塞。

**具体设计：**
论文将部分 static token selection offload 到 CPU，而 GPU 负责 dynamic token 的保留决策。([CVF 开放获取][2])

**为什么有效：**
它不是单纯算法压缩，而是系统调度优化。核心不是减少理论 FLOPs，而是减少 wall-clock latency。对于 TTFT 来说，真实系统时间比 FLOPs 更重要。

---

## 4. 实验结果：它到底赢在哪里

### 4.1 LLaVA-OneVision-7 B 主结果

在 LLaVA-OneVision-7 B 上，baseline 100% token 的 TTFT 是 **889.9 ms**，FLOPs 是 **82.6 T**，平均分 **58.4**。EarlyTom 在 10% retained ratio 下达到 **336.2 ms TTFT**、**32.2 T FLOPs**、平均分 **56.2**，即 score ratio 为 **96.2%**。在 25% retained ratio 下，EarlyTom 平均分 **58.2**，几乎接近 baseline，同时 TTFT 降到 **426.3 ms**。([CVF 开放获取][2])

这说明它的优势主要在：

$$
\text{latency/computation} \gg \text{accuracy gain}
$$

它不是让模型更聪明，而是让模型更早省掉无效计算。

### 4.2 与 HoliTom / VisionZip 的关系

在 10% retained ratio 下：

* VisionZip：TTFT **458.5 ms**，平均分 **53.5**
* HoliTom：TTFT **556.6 ms**，平均分 **57.9**
* EarlyTom：TTFT **336.2 ms**，平均分 **56.2**

所以 EarlyTom 的位置很清楚：它不是在所有压缩率下都最高精度，而是在速度-精度 Pareto frontier 上更偏向低 TTFT。([CVF 开放获取][2])

更准确地说：

> EarlyTom 的核心贡献不是“压缩后精度最高”，而是“在保持可接受精度时，端到端首 token 延迟显著更低”。

### 4.3 Ablation 说明了什么

论文的 ablation 显示，在 20% retain ratio 下，Random sampling 吞吐更高但平均分较低；Top-K 精度较好但吞吐较低；EarlyTom 的 local-window / decoupled sampling 在吞吐和精度之间取得更好折中。([CVF 开放获取][2])

这支持一个隐含结论：

> 空间 token 压缩不能只看 importance，还必须控制 selection distribution。

另外，Stage-I frame merging 单独使用时保留约 **73.9%** token，平均分 **58.4**；Stage-II spatial selection 单独使用时 retain ratio 为 **20%**，平均分 **58.4**；两者结合后平均分 **58.8**。

这说明两个模块并不是简单叠加压缩，而是互补：

* Stage I 减 temporal redundancy；
* Stage II 减 spatial redundancy；
* decoupling 机制缓解 attention sink 带来的 selection bias。

---

## 5. Potential Flaw：局限与脆弱点

### 5.1 “接近 baseline”并不等于无损

在 10% retained ratio 下，EarlyTom 平均分从 baseline 的 **58.4** 降到 **56.2**；LongVideoBench 从 **56.4** 降到 **52.4**。这说明强压缩下长视频理解仍有明显损失。([CVF 开放获取][2])

这类损失可能来自：

$$
\text{rare event} \quad \text{or} \quad \text{middle-frame evidence}
$$

被误合并或误删。

### 5.2 hyperparameter 可能依赖数据集

补充材料给出了不同 retained ratio、不同 benchmark 下的 $\tau_{\text{seg}}$、层位置等配置；这暗示方法虽然 training-free，但不是完全 parameter-free。

问题在于：真实部署时不知道输入视频属于 MVBench、EgoSchema 还是 LongVideoBench 风格。若阈值对视频类型敏感，线上系统可能需要 adaptive threshold，而不是固定表格调参。

### 5.3 dynamic/static 的划分是启发式的

EarlyTom 假设 segment 的 head/tail frames 更动态、更重要，中间帧更静态。但很多任务恰好依赖中间帧，例如：

* “人是否在中间某一刻拿起杯子？”
* “车牌在哪一帧出现？”
* “视频中短暂出现的文字是什么？”
* “动作完成前的关键准备动作是什么？”

这些信息可能位于 segment 中部，并且不一定导致高相似度突变。

### 5.4 attention sink 的处理仍然依赖 attention score

EarlyTom 识别出 attention sink 会污染 Top-K，但最终仍然使用 attention 分数，只是通过 local window 限制其空间偏置。这是一个工程上有效的修补，但还不是彻底的 semantic importance estimator。

更本质的问题是：

$$
A_i \text{ high} \not\Rightarrow \text{semantically necessary}
$$

下一步可能需要 query-conditioned、counterfactual 或 gradient-free semantic scoring。

### 5.5 TTFT 优化还不是完整服务延迟优化

论文主要优化 TTFT。补充材料也指出，未来仍需考虑 system-algorithm co-design，以及 reasoning models 中 lengthy generation steps 的 decoding-stage 加速问题。

也就是说，EarlyTom 解决的是：

$$
T_{\text{first token}}
$$

而不是完整的：

$$
T_{\text{end-to-end response}} = T_{\text{prefill}} + T_{\text{decode}}
$$

对于长回答、复杂推理、多轮交互，decoding 阶段仍可能成为主要瓶颈。

---

## 6. Motivation：如果我是作者，会如何一步步想到这个方法

1. Video-LLM 慢，到底慢在哪里？
   不是先假设 LLM 慢，而是拆 TTFT。

2. 如果 visual token compression 已经把 LLM prefill 降下来了，为什么整体还不够快？
   因为 vision encoder 的开销没动。

3. 那能不能在 vision encoder 之前压缩？
   原始图像帧级压缩太粗，会丢失空间语义。

4. 能不能在 vision encoder 内部压缩？
   可以，因为中间层特征已经有语义，又还没完成全部计算，压缩收益最大。

5. 压什么最安全？
   视频最大冗余首先来自时间维度，相邻帧高度相似，因此先做 frame merging。

6. 怎么避免把动作边界合并掉？
   用 streaming similarity 分段，保留 segment 的 head/tail，只合并中间相似帧。

7. 时间压完还不够，空间 token 怎么压？
   用 attention score 选重要 token。

8. 但 attention Top-K 为什么会失败？
   因为 vision sink token 持续占据高 attention，导致选择偏置。

9. 怎么既保留重要动态区域，又不被 sink token 支配？
   dynamic frames 用 global Top-K，static frames 用 local-window Top-K 保持空间分布。

10. 算法压缩会不会自己引入额外 overhead？
    会，所以把 static selection 部分 offload 到 CPU，减少 GPU 侧延迟。

这条思路的本质是：

> 先通过 profiling 找真正瓶颈，再根据视频冗余结构设计最早可安全压缩的位置，最后修正 attention-based selection 的结构性偏差。

---

## A. 一句话总结核心贡献

**EarlyTom 的核心贡献是：把 Video-LLM 的 token 压缩从“vision encoder 之后”前移到“vision encoder 内部”，用时间冗余合并 + 动静态解耦空间选择，同时减少 vision encoding 和 LLM prefill 的计算。**

---

## B. 下一篇论文最自然做什么

最自然的下一篇是：

> **Query-aware Early Token Compression for Video-LLMs**

也就是让压缩策略不只看视频自身相似度，还看用户问题。

当前 EarlyTom 是 query-agnostic：无论 prompt 问“整体发生了什么”还是“第 17 秒左下角写了什么”，压缩策略基本相同。更合理的目标应是：

$$
\min \text{tokens}
\quad
\text{s.t.}
\quad
I(\hat{V}; y \mid x) \approx I(V; y \mid x)
$$

也就是保留对当前问题 $x$ 有用的视频信息，而不是保留通用重要信息。

可以做成三步：

1. 用轻量 text-video relevance scorer 估计哪些 segment 与 query 相关；
2. 对 query-relevant segment 降低压缩率，对无关 segment 提高压缩率；
3. 对 spatial token selection 引入 text-conditioned attention，而不是纯 vision attention。

这会直接补上 EarlyTom 最大的设定局限：**它优化的是平均视频理解，而不是问题条件下的信息保真。**

[1]: https://arxiv.org/abs/2605.30010 "[2605.30010] EarlyTom: Early Token Compression Completes Fast Video Understanding"
[2]: https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_EarlyTom_Early_Token_Compression_Completes_Fast_Video_Understanding_CVPR_2026_paper.pdf "EarlyTom: Early Token Compression Completes Fast Video Understanding"

