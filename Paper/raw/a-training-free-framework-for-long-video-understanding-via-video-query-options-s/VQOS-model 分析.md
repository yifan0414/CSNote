---
创建时间: 2026-05-27 22:23
tags:
---


## 1. 最终答题的 MLLM backbone

论文把 VQOS 框架接到两个长视频多模态大模型上：

| 模型 | 用途 |
|---|---|
| **LLaVA-Video-7 B / 72 B** | 最终 video QA；也用于生成候选答案 options |
| **Qwen 2.5-VL-7 B / 72 B** | 最终 video QA；也用于生成候选答案 options |

区别：

- **LLaVA-Video**：固定输入分辨率 $384 \times 384$，所以只用 VQOS + AFS，不用 DRA。
- **Qwen 2.5-VL**：支持动态分辨率，所以使用 VQOS + AFS + DRA。


## 2. video-text retrieval 模型

这是 VQOS 的核心检索模型，用来计算视频片段和文本的相似度。

主实验使用：

| 模型 | 用途 |
|---|---|
| **PerceptionEncoder PE-G/14** | 主力 VTR 模型，用于 video segment 和 `question + option` 的相似度计算 |
| **PerceptionEncoder PE-L/14** | 轻量版本，用于效率/成本消融 |

默认设置是：

```text
16-second video segments
+ PE-G/14
+ retrieval FPS = 1
```

也就是用 PE-G/14 对每个 16 秒视频片段做 embedding，再和文本 embedding 算 cosine similarity。


## 3. VTR / image-text retrieval 消融模型

论文还比较了不同 retrieval encoder：

| 模型 | 类型 | 作用 |
|---|---|---|
| **CLIP-B/32** | image-text retrieval | 消融对比 |
| **CLIP-B/16** | image-text retrieval | 消融对比 |
| **CLIP-L/14** | image-text retrieval | 消融对比 |
| **CLIP-L/14-336** | image-text retrieval | 消融对比 |
| **PE-L/14** | video-text retrieval | 较轻量 VTR |
| **PE-G/14** | video-text retrieval | 最强主配置 |
| **SigLIP-LLaVA** | 复用 LLaVA-Video 的视觉 encoder | 尝试不额外引入 VTR 模型 |

其中 **SigLIP-LLaVA** 比较有意思：作者尝试复用 LLaVA-Video 内部的 SigLIP visual encoder，再加回 SigLIP pooling head 和 text encoder，来避免额外跑一个 VTR 模型。


## 4. option generation 模型

VQOS 需要候选答案 options。论文有两种方式：

### Ours-PO

直接使用数据集给定的选择题选项，不需要额外模型生成。

### Ours-GO

由 MLLM 自己生成候选答案。

主要使用：

| 模型 | 用途 |
|---|---|
| **LLaVA-Video-7 B** | 为 LLaVA-Video setting 生成 options |
| **Qwen 2.5-VL-7 B** | 为 Qwen 2.5-VL setting 生成 options |

附录中还测试了更强 option generator：

| 模型 | 用途 |
|---|---|
| **Seed 1.5 VL** | 测试更强 MLLM 生成 options 是否更好 |
| **GPT-5-2025-08-07** | 测试强模型无视频/有视频生成 options 的影响 |

结论是：**生成 options 时带视频上下文更重要**，单纯用强语言/多模态模型但不给视频，收益有限。


## 5. 对比 / 组合的方法

这些不是 backbone 模型，但论文中作为方法对照或组合使用：

| 方法 | 作用 |
|---|---|
| **AKS** | training-free retrieval-based baseline |
| **AdaReTake** | token-level compression 方法 |
| **Ours + AdaReTake** | 证明 VQOS 和 token compression 可以叠加 |


## 一句话总结

VQOS 主要用了三类模型：

> **LLaVA-Video / Qwen 2.5-VL 负责理解和回答，PE-G/14 负责 video-text retrieval，原始 MLLM 或给定选项负责生成/提供 candidate options。**

更完整地说：

```text
MLLM backbone:
  LLaVA-Video-7B/72B
  Qwen2.5-VL-7B/72B

VTR model:
  PE-G/14 as main retriever
  PE-L/14, CLIP variants, SigLIP-LLaVA as ablations

Option generator:
  original MLLM itself
  Seed1.5VL / GPT-5 in appendix ablations
```
