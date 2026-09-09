---
title: CLIP 与 SigLIP 学习
aliases:
  - Video MLLM Stage 3-4 CLIP SigLIP
tags:
  - video-mllm
  - clip
  - siglip
type: learning-note
stage:
  - 3
  - 4
status: planned
created: 2026-08-15
updated: 2026-09-09
---

# CLIP 与 SigLIP 学习

> [!abstract] 阶段目标
> 对应 [[RoadMap#阶段 3：CLIP|RoadMap 阶段 3]] 与 [[RoadMap#阶段 4：SigLIP|阶段 4]]。重点区分 global frame relevance、patch features 和两种训练目标。

## 导航

- 前置：[[02-vit|02 ViT]]
- 下一阶段：[[04-blip-llava|04 BLIP 与 LLaVA]]
- Compression Map：[[06-compression-map|06 Compression Map]]

## 学习资料

### CLIP

| 类型 | 文件 | 阅读范围 |
| --- | --- | --- |
| 原始论文 | [[2103.00020-clip.pdf\|CLIP PDF]] | Figure 1、§2.3-2.5、Figure 3 |
| 官方代码 | [[openai-clip-main.zip\|OpenAI CLIP Snapshot]] | load、tokenize、encode_image、encode_text |
| 课程复习 | [[lecture17-multimodality.py\|CS336 Lecture 17 Source]] | CLIP / ViT 部分 |

### SigLIP

| 类型 | 文件 | 阅读范围 |
| --- | --- | --- |
| 原始论文 | [[2303.15343-siglip.pdf\|SigLIP PDF]] | Algorithm 1、§3.1-3.3、§4.1-4.2 |
| 官方代码 | [[google-big-vision-main.zip\|Google Big Vision Snapshot]] | SigLIP configs / image-text models |
| 模型文档 | [Hugging Face SigLIP Docs](https://huggingface.co/docs/transformers/model_doc/siglip) | VisionConfig、VisionModel、hidden states |

## CLIP 数据流

~~~text
Image → Vision Encoder → Global Image Embedding ┐
                                                  ├→ Normalize → Dot Product / Temperature
Text  → Text Encoder   → Global Text Embedding  ┘
~~~

- [ ] 写出 image / text embedding 的归一化公式。
- [ ] 解释 symmetric cross-entropy。
- [ ] 找到 logit_scale / temperature。
- [ ] 确认经典 CLIP 双塔内部没有 image-text cross-attention。

## CLIP 实验

- [ ] 手动复现 image / text encode → normalize → dot product。
- [ ] 对 8 帧视频计算 query relevance 并排序。
- [ ] 绕过 global pooling，获取 patch hidden states。
- [ ] 对比最后层与倒数第二层 patch features。

| Frame | Global similarity | Rank | Patch tokens | 观察 |
| ---: | ---: | ---: | ---: | --- |
| 0 |  |  |  |  |
| 1 |  |  |  |  |
| 2 |  |  |  |  |

> [!warning]
> Global frame score 只能说明整帧与 query 的相关性，不能直接说明帧内哪个 patch 应保留。

## SigLIP 对比

| 项目 | CLIP | SigLIP |
| --- | --- | --- |
| 对齐骨架 | Dual encoder | Dual encoder |
| 主要目标 | Batch 内 softmax contrastive loss | Pairwise sigmoid loss |
| 全局归一化 | 需要 | 不需要 |
| 额外标量 | Temperature / logit scale | Temperature + bias |
| 下游关注 | Global embedding / patch hidden | Global embedding / vision hidden |

- [ ] 从 Algorithm 1 写出 pairwise positive / negative label。
- [ ] 解释 sigmoid loss 为何便于 chunked implementation。
- [ ] 读取 image_size、patch_size、hidden_size、layers 和 heads。
- [ ] 输出 vision tower 的每层 hidden state。
- [ ] 在同一视频上比较 CLIP 与 SigLIP frame ranking。

## 与 OneVision 的连接

- [ ] 记录 OneVision checkpoint 使用的 SigLIP vision config。
- [ ] 确认取最后层还是倒数层 feature。
- [ ] 确认 CLS / special token 是否被移除。
- [ ] 记录 feature grid 如何恢复为空间布局。

## 阶段产物

- [ ] 最小 CLIP frame scorer。
- [ ] CLIP global vs patch-level 笔记。
- [ ] CLIP / SigLIP loss 与 inference data-flow 对比表。
- [ ] SigLIP vision tower shape trace。
