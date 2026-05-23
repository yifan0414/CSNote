---
创建时间: 2026-05-13 22:53
tags:
---
这两篇都在解决 **long-video VQA 里“怎么少看但看对”** 的问题，但侧重点不同：

- [[Divide, then Ground Adapting Frame Selection to Query Types for Long-Form Video Understanding]]：做 **query-adaptive frame selection**，重点是“选哪些帧/片段送进模型”。
- [[Paper/raw/videorouter-query-adaptive-dual-routing-for-efficient-long-video-understanding/videorouter-query-adaptive-dual-routing-for-efficient-long-video-understanding.md|VideoRouter]]：做 **query-adaptive visual token routing/compression**，重点是“固定 token 预算下，哪些帧保留高分辨率 token”。

## 对比

**DIG 是 training-free 的外部帧选择框架；VideoRouter 是需要训练 router 的内部 token 分配框架。**

DIG 更像一个 **pre-processing / retrieval module**；VideoRouter 更像一个 **model-side efficiency module**。


## 核心思想对比

| 维度 | DIG | VideoRouter |
|---|---|---|
| 核心问题 | 长视频应该如何根据 query 类型选帧 | 固定 visual-token budget 下，如何根据 query 分配 token |
| Query 分类 | Global Query / Localized Query | Global policy / Fragment policy |
| Global 情况 | 直接 uniform sampling | 所有帧 uniform spatial pooling |
| Localized 情况 | CAFS 找候选 segment，再用 LMM reward 选相关片段 | Image Router 给每帧打 relevance score，相关帧保留高保真 token |
| 粒度 | frame / segment selection | frame-level token allocation |
| 是否训练 | 不训练，training-free | 需要训练 Semantic Router + Image Router |
| 依赖 | 依赖外部 LMM 做 reward assignment | 依赖构造的 Video-QTR-10 K / Video-FLR-200 K 监督 |
| 主要成本 | LMM reward assignment 昂贵 | router 额外 forward，但减少 LLM prefill |
| 部署形态 | 可插到任何 Video-LMM 前面 | 需要和 backbone/token pipeline 更深集成 |

## 方法层面的关键差异

### 1. Query routing 的相似性

两篇都认为 query 不能一刀切：

- DIG：  
  - **GQ**：需要全局理解，uniform sampling 够用。  
  - **LQ**：答案集中在局部片段，需要 query-aware selection。

- VideoRouter：  
  - **Global policy**：保留广覆盖。  
  - **Fragment policy**：集中预算到关键帧。

所以它们的高层判断几乎一致：  
**holistic query 要覆盖，localized query 要聚焦。**

区别是 DIG 用 prompt/LLM 判断 query type；VideoRouter 训练一个 Semantic Router 判断 allocation policy。

### 2. “选帧” vs “分配 token”

DIG 最终还是在决定：  
> 哪些 video segment 值得留下，然后再 uniform sample。

VideoRouter 决定的是：  
> 所有 sampled frames 里，哪些帧值得高分辨率保留，哪些帧可以 aggressive pooling。

所以 VideoRouter 比 DIG 更细：它不是简单丢帧，而是在 **frame 保留与 token 压缩之间做 budget allocation**。

这点很重要，因为长视频里有些“背景帧”虽然不是核心证据，但完全丢掉可能会破坏上下文。VideoRouter 的 Fragment policy 允许 irrelevant frames 仍然以低 token 形式保留。

### 3. 训练需求不同

DIG 的优点是 **training-free**：

- 不需要构造训练集；
- 不需要改 backbone；
- 适合快速部署和 benchmark-time adaptation。

但缺点是 reward assignment 很贵，尤其要用 LMM 给 r-frame 打分。

VideoRouter 相反：

- 前期要构造 Video-FLR-200 K / Video-QTR-10 K；
- 要训练 Image Router 和 Semantic Router；
- 但推理时 router 成本可控，且能真正降低 TTFT / memory。

如果是研究原型或离线评测，DIG 更方便；如果是长期系统部署，VideoRouter 更系统化。

---

## 实验结论对比

### DIG 的实验证据

DIG 主要证明：

1. GQ 和 LQ 确实需要不同 frame selection 策略。
2. 对 LQ，uniform sampling 容易被无关帧污染。
3. LMM reward assignment 比 CLIPScore 更好。
4. 在 Qwen 2.5-VL-7 B / 32 B 上，DIG 在 MLVU、LongVideoBench、VideoMME medium/long 上大多优于 UNI、Q-Frame、AKS。
5. 在高帧数如 128/192/256 frames 下仍然有效。

### VideoRouter 的实验证据

VideoRouter 主要证明：

1. 在相同视觉 token budget 下，query-adaptive token routing 优于 uniform pooling 和 CLIP relevance pooling。
2. 能在更低 visual tokens 下提升或保持 accuracy。
3. 在 InternVL 3 和 Qwen 2.5-VL 上都有收益。
4. 最高报告 67.9% token reduction。
5. router 虽有额外 0.5 s 左右开销，但由于 LLM prefill 下降，总体 TTFT 和 peak memory 下降。

两者的实验目标不完全一样：

- DIG 更关心 **accuracy under frame budget**。
- VideoRouter 更关心 **accuracy-efficiency tradeoff under token budget**。

---

## 谁更强？

不能直接说谁绝对更强，因为评测设置不同。

但可以这样判断：

### 如果你的目标是“提高长视频 QA 准确率”

优先看 DIG。  
它直接优化 frame/segment selection，尤其适合 localized query、多帧输入、高帧数场景。

### 如果你的目标是“降低 token、显存、TTFT，同时保持准确率”

优先看 VideoRouter。  
它更适合真实部署里的 efficiency constraint。

### 如果你的系统已经有固定 Video-LMM，不能训练或改模型

DIG 更合适。  
因为它是 model-agnostic pre-processing。

### 如果你能改模型 pipeline，并愿意训练轻量 router

VideoRouter 更合适。  
它能做更细粒度 token budget control。

---

## 局限性对比

| 方面 | DIG 的问题 | VideoRouter 的问题 |
|---|---|---|
| Query 分类 | GQ/LQ prompt classifier 不稳定，尤其 GQ accuracy 有时低 | Semantic Router 训练集可能有 teacher bias |
| 成本 | LMM reward assignment 很贵 | 需要训练与集成 router |
| 粒度 | 最终仍偏 segment/frame selection，可能丢上下文 | frame relevance label 可能受相邻帧冗余影响 |
| 泛化 | 依赖 reward LMM 能力 | 主要在 InternVL 3/Qwen 2.5-VL 验证 |
| 部署 | 离线 selection 成本大 | 需要访问模型 token pipeline |

---

## 我觉得最有价值的综合观点

这两篇其实可以组合：

1. **DIG 做 coarse segment retrieval**  
   先用 CAFS + reward 找出 query-relevant segment。

2. **VideoRouter 做 fine-grained token allocation**  
   在保留下来的 segment 内，对关键帧保留高分辨率 token，对背景帧 aggressive pooling。

组合后就是：

> Query type routing → segment-level retrieval → frame-level relevance scoring → token-level budget allocation

这会比单独 frame selection 或单独 token routing 更完整。

---

## 总结

DIG 和 VideoRouter 都说明 long-video understanding 的核心不是“看更多帧”，而是：

> 根据问题类型决定应该广覆盖，还是聚焦关键证据。

DIG 的贡献在于 **training-free query-adaptive frame selection**；VideoRouter 的贡献在于 **trained dual-router token budget allocation**。

如果把两篇放在一个研究脉络里，DIG 更偏 **retrieval / selection**，VideoRouter 更偏 **compression / allocation**。两者互补性很强。
