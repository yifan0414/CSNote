---
title: Transformer 学习与实现
aliases:
  - Video MLLM Stage 1 Transformer
tags:
  - video-mllm
  - transformer
  - cs224n
type: learning-note
stage: 1
status: planned
created: 2026-08-15
updated: 2026-08-15
---

# Transformer 学习与实现

> [!abstract] 阶段目标
> 对应 [[Paper/架构学习/RoadMap#阶段 1：Transformer|RoadMap 阶段 1]]。完成后应能从 shape 推导 self-attention，独立实现 decoder-only Transformer，并解释 token 数对计算量的影响。

## 导航

- 前置：[[Paper/架构学习/Video-MLLM/00-shape-cheatsheet|00 Shape Cheatsheet]]
- 下一阶段：[[Paper/架构学习/Video-MLLM/02-vit|02 ViT]]
- Trace 模板：[[Paper/架构学习/Video-MLLM/experiments/traces/README|Trace 实验模板]]

## CS224N 资料

| 顺序 | 内容 | Slides | Notes / Notebook |
| --- | --- | --- | --- |
| 1 | Backpropagation and Neural Network Basics | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture03-neuralnets-slides.pdf\|Lecture 3 Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture03-neuralnets-notes.pdf\|Lecture 3 Notes]] |
| 2 | Language Models and RNNs | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture04-rnnlm-slides.pdf\|Lecture 4 Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture04-rnnlm-notes.pdf\|Lecture 4 Notes]] |
| 3 | Transformers | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture05-transformers-slides.pdf\|Lecture 5 Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/transformer-notes.pdf\|Transformer Notes]] |
| 辅助 | PyTorch Tutorial |  | [Official Colab](https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing) |
| 辅助 | Jurafsky & Martin Chapter 9 |  | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/jurafsky-martin-ch09-transformer.pdf\|Transformer Chapter]] |

### 原始论文

- [[Paper/架构学习/Video-MLLM/resources/papers/1706.03762-attention-is-all-you-need.pdf|Attention Is All You Need]]
- [[Paper/架构学习/Video-MLLM/resources/papers/1607.06450-layer-normalization.pdf|Layer Normalization]]

### 作业

| 作业 | Handout | Code | 本路线范围 |
| --- | --- | --- | --- |
| A2 | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment2-handout.pdf\|PDF]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment2-code.zip\|ZIP]] | 选做 Adam、Dropout 和 PyTorch 网络 |
| A3 | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment3-handout.pdf\|PDF]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment3-code.zip\|ZIP]] | Attention、position embedding、从零实现 Transformer |

## CS336 补充资料

- [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture02-resource-accounting.py|Lecture 2 Resource Accounting Source]]
- [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture03-architectures.pdf|Lecture 3 Architectures]]
- [[Paper/架构学习/Video-MLLM/resources/courses/cs336/assignment1-basics.pdf|Assignment 1 Handout]]
- [[Paper/架构学习/Video-MLLM/resources/code/cs336-assignment1-basics-main.zip|Assignment 1 Code Snapshot]]

> [!note]
> 先完成 CS224N A3，再按需做 CS336 A1 §3。两份作业都实现 Transformer，但 CS336 进一步覆盖 RMSNorm、RoPE、SwiGLU 和 resource accounting。

## Day 1：神经网络模块

- [ ] 看 Lecture 3 slides / notes。
- [ ] 实现 Linear → activation → Linear 的 MLP。
- [ ] 实现 Pre-LN residual block。
- [ ] 为每个中间 tensor 添加 shape assertion。

## Day 2：LM 与 RNN 动机

- [ ] 看 Lecture 4，只理解 autoregressive LM 与 RNN 串行瓶颈。
- [ ] 写出 teacher forcing 下输入和 target 的错位关系。
- [ ] 能解释为什么 Transformer 仍需 causal mask。

## Day 3-4：Self-Attention

- [ ] 看 Lecture 5 slides 与 Transformer notes。
- [ ] 精读 *Attention Is All You Need* §3。
- [ ] 手推 Q / K / V、score、softmax、context 和 output projection 的 shape。
- [ ] 实现 padding mask 与 causal mask。
- [ ] 比较 $N=64,128,256,512$ 的 latency 和 score tensor 大小。

## Day 5：完整 Block

- [ ] 实现 Multi-Head Self-Attention。
- [ ] 实现 Pre-LN DecoderBlock。
- [ ] 加入 positional information。
- [ ] 说明 encoder bidirectional attention 与 decoder causal attention 的区别。

## Day 6：Assignment 3

- [ ] Q1 Attention Exploration。
- [ ] Q2 Position Embeddings Exploration。
- [ ] Q3(a) MLP、CausalAttention、DecoderBlock、Transformer.forward、generate。
- [ ] Q3(b) Batch loss 和 100 batches 训练。
- [ ] 保存 loss / gradient norm 曲线。

## 实验记录

| 配置 | $N$ | Heads | dtype | Forward ms | Peak memory | 备注 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
|  | 64 |  |  |  |  |  |
|  | 128 |  |  |  |  |  |
|  | 256 |  |  |  |  |  |
|  | 512 |  |  |  |  |  |

## 阶段产物

- [ ] Attention 实现与单元测试。
- [ ] Shape cheat sheet 已更新。
- [ ] A3 loss / gradient norm 图。
- [ ] 一页总结：$N$ 减半后 attention、MLP 和 KV cache 如何变化。
