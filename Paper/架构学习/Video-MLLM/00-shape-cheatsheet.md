---
title: Video MLLM Shape Cheatsheet
aliases:
  - Video MLLM 张量形状速查表
tags:
  - video-mllm
  - tensor-shape
  - cheatsheet
type: reference
stage: 0
status: active
created: 2026-08-15
updated: 2026-08-15
---

# Video MLLM Shape Cheatsheet

> [!abstract] 用途
> 这份笔记是 [[Paper/架构学习/RoadMap|RoadMap]] 阶段 0 的速查表。沿模型 forward 追踪时，先记录 shape，再解释语义和成本。

## 导航

- 下一阶段：[[Paper/架构学习/Video-MLLM/01-transformer|01 Transformer]]
- Trace 模板：[[Paper/架构学习/Video-MLLM/experiments/traces/README|Trace 实验模板]]
- 全部资料：[[Paper/架构学习/Video-MLLM/resources/README|Resources Index]]

## 学习资料

| 资料                           | 本地文件                                                                                | 使用范围                       |
| ---------------------------- | ----------------------------------------------------------------------------------- | -------------------------- |
| PyTorch Tensors Tutorial     | [官方文档](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html) | Shape、dtype、device、索引和矩阵乘法 |
| Building Models with PyTorch | [官方文档](https://docs.pytorch.org/tutorials/beginner/introyt/modelsyt_tutorial.html) | Module、parameter 和 forward |
| torch.einsum API             | [官方文档](https://docs.pytorch.org/docs/stable/generated/torch.einsum.html) | Batch / contraction 维 |
| CS224N PyTorch Tutorial      | [Official Colab](https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing) | PyTorch 实践 |

## 统一符号

| 符号 | 含义 |
| --- | --- |
| $B$ | Batch size |
| $T$ | 视频帧数或时间步 |
| $N$ | 当前序列中的 token 数 |
| $N_v$ | Visual token 数 |
| $N_t$ | Text token 数 |
| $D$ | 当前 hidden dimension |
| $D_v$ | Vision encoder hidden dimension |
| $D_l$ | LLM hidden dimension |
| $H$ | Attention heads 或 KV heads，按上下文区分 |
| $d_h$ | 单个 head 的维度，通常 $D=Hd_h$ |
| $L$ | Transformer 层数 |
| $P$ | ViT patch size |

## 基础模块

| 模块 | 输入 | 输出 | Token 数是否变化 |
| --- | --- | --- | --- |
| Linear$(D,H)$ | $[B,N,D]$ | $[B,N,H]$ | 否 |
| LayerNorm$(D)$ | $[B,N,D]$ | $[B,N,D]$ | 否 |
| Position-wise MLP | $[B,N,D]$ | $[B,N,D]$ | 否 |
| Residual | $x,f(x):[B,N,D]$ | $[B,N,D]$ | 否 |
| Pooling | $[B,N,D]$ | $[B,M,D]$ | 是，通常 $M<N$ |
| Projector | $[B,N,D_v]$ | $[B,N,D_l]$ | 通常否 |

## Self-Attention

$$
X:[B,N,D]
$$

$$
Q,K,V:[B,H,N,d_h]
$$

$$
S=\frac{QK^\top}{\sqrt{d_h}}:[B,H,N,N]
$$

$$
\operatorname{softmax}(S)V:[B,H,N,d_h]
$$

$$
\operatorname{Concat}+\operatorname{Proj}:[B,N,D]
$$

- [ ] 每次看到 attention 都确认 softmax 维度。
- [ ] 区分 query length 与 key/value length，cross-attention 不一定是 $N\times N$。
- [ ] 记录 mask 的 broadcast shape。
- [ ] 确认 GQA / MQA 下 query heads 与 KV heads 是否相同。

## ViT

对于输入 $[B,C,H,W]$ 和 patch size $P$：

$$
N_{\text{patch}}=\frac{H}{P}\frac{W}{P}
$$

| 节点 | Shape |
| --- | --- |
| Pixels | $[B,C,H,W]$ |
| Patchify | $[B,N_{\text{patch}},P^2C]$ |
| Patch projection | $[B,N_{\text{patch}},D_v]$ |
| 加 CLS 后 | $[B,N_{\text{patch}}+1,D_v]$ |
| ViT hidden state | $[B,N,D_v]$ |
| Global representation | $[B,D_v]$ |

## Video MLLM

| 节点 | 通用 Shape | 必问问题 |
| --- | --- | --- |
| Sampled frames | $[B,T,C,H,W]$ | $T$ 在哪里决定？ |
| Per-frame ViT input | $[BT,N_0,D_v]$ | Batch 与 frame 是否展平？ |
| Vision output | $[BT,N_1,D_v]$ | 是否移除 CLS？ |
| Spatial reduction | $[BT,N_2,D_v]$ | Pool / interpolate / prune / merge？ |
| Projector | $[BT,N_2,D_l]$ | 是否只改变 $D$？ |
| Packed visual prefix | $[B,TN_2,D_l]$ | 帧边界如何表示？ |
| Text embeddings | $[B,N_t,D_l]$ | Special token 在哪里？ |
| LLM input | $[B,TN_2+N_t,D_l]$ | Padding / packing / mask？ |

## KV Cache

忽略 GQA / MQA 时，Key + Value 的元素数量近似：

$$
\#\mathrm{KV}=2LBHNd_h
$$

显存估算：

$$
\mathrm{bytes}\approx2LBHNd_h\times\mathrm{dtype\ bytes}
$$

> [!warning]
> 使用 GQA / MQA 时，$H$ 应填写 KV heads，而不是 query heads。实际显存还受 padding、batching、allocator 和实现布局影响。

## Trace 最小记录

| Stage | Shape | dtype | device | Token 变化原因 |
| --- | --- | --- | --- | --- |
| Input |  |  |  |  |
| Vision embedding |  |  |  |  |
| ViT middle |  |  |  |  |
| Vision output |  |  |  |  |
| Spatial reduction |  |  |  |  |
| Projector |  |  |  |  |
| LLM input |  |  |  |  |
| KV cache |  |  |  |  |

## 完成检查

- [ ] 能从 $[B,N,D]$ 推出多头 Q / K / V 和 attention score。
- [ ] 能从图像分辨率与 patch size 算出视觉 token 数。
- [ ] 能区分改变 $N$ 与改变 $D$。
- [ ] 能说明 frame-level、mid-ViT 和 post-vision 压缩分别影响哪些 shape。
