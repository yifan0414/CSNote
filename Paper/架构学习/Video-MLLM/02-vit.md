---
title: ViT 学习与 Trace
aliases:
  - Video MLLM Stage 2 ViT
tags:
  - video-mllm
  - vit
  - vision-transformer
type: learning-note
stage: 2
status: planned
created: 2026-08-15
updated: 2026-08-15
---

# ViT 学习与 Trace

> [!abstract] 阶段目标
> 对应 [[Paper/架构学习/RoadMap#阶段 2：ViT|RoadMap 阶段 2]]。掌握 pixels 如何变成 patch tokens，以及分辨率、patch size 和特殊 token 如何决定 $N$。

## 导航

- 前置：[[Paper/架构学习/Video-MLLM/01-transformer|01 Transformer]]
- 下一阶段：[[Paper/架构学习/Video-MLLM/03-clip-siglip|03 CLIP 与 SigLIP]]
- Trace 目录：[[Paper/架构学习/Video-MLLM/experiments/traces/README|Trace 实验模板]]

## 学习资料

| 类型 | 文件 | 阅读范围 |
| --- | --- | --- |
| 原始论文 | [[Paper/架构学习/Video-MLLM/resources/papers/2010.11929-vit.pdf\|ViT PDF]] | Figure 1、§3、§3.1、§3.2、§4.5 |
| 官方代码 | [[Paper/架构学习/Video-MLLM/resources/code/google-vision-transformer-main.zip\|Google Vision Transformer Snapshot]] | Config、patch embedding、position embedding |
| 模型文档 | [Hugging Face ViT Docs](https://huggingface.co/docs/transformers/model_doc/vit) | ViTConfig、ViTModel、hidden states |
| 课程复习 | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture17-multimodality.py\|CS336 Lecture 17 Source]] | ViT / encoding images |

## 核心推导

$$
N_{\text{patch}}=\frac{H}{P}\frac{W}{P}
$$

$$
X_0\in\mathbb{R}^{B\times N_{\text{patch}}\times D}
$$

若加入 CLS：

$$
N=N_{\text{patch}}+1
$$

- [ ] 从论文 Equation (1)-(4) 标注每个 tensor 的 shape。
- [ ] 解释 patch projection 为什么等价于 kernel=$P$、stride=$P$ 的卷积。
- [ ] 解释高分辨率 fine-tuning 为什么需要 position embedding interpolation。
- [ ] 区分 patch hidden states 与 global / CLS representation。

## 代码 Trace

- [ ] 记录 pixel_values。
- [ ] 记录 patch embedding。
- [ ] 记录加入 position / CLS 后的序列。
- [ ] 记录第 1、中间、最后一个 ViT block。
- [ ] 记录 last_hidden_state 与 pooler output。
- [ ] 使用两个分辨率重复实验。

| 节点 | 预期 Shape | 实际 Shape | 备注 |
| --- | --- | --- | --- |
| Pixels | $[B,C,H,W]$ |  |  |
| Patch embedding | $[B,N,D]$ |  |  |
| With special token | $[B,N+s,D]$ |  |  |
| Block 1 | $[B,N+s,D]$ |  |  |
| Middle block | $[B,N+s,D]$ |  |  |
| Last hidden | $[B,N+s,D]$ |  |  |
| Global representation | $[B,D]$ |  |  |

## Token 预算练习

| Resolution | Patch | Patch tokens | + CLS |
| --- | ---: | ---: | ---: |
| $224\times224$ | 16 | 196 | 197 |
| $384\times384$ | 14 |  |  |
| 自选 |  |  |  |

## 压缩判断

- [ ] ViT 输入前 patch selection：说明可节省哪些层。
- [ ] ViT 中间层 prune / merge：记录剩余 block 数。
- [ ] ViT 输出后 pruning：说明为什么不能回收已经发生的 vision 计算。
- [ ] 对三个位置分别写出位置编码和 special token 风险。

## 阶段产物

- [ ] 一份 ViT forward trace。
- [ ] 一张 resolution / patch size / token count 表。
- [ ] 一页 global representation vs patch representation 对比。
- [ ] 一段关于 mid-ViT 与 post-ViT 压缩收益差异的结论。
