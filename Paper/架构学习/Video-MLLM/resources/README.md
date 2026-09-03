---
title: Video MLLM 资料索引
aliases:
  - Video MLLM Resources Index
tags:
  - video-mllm
  - resources
type: resource-index
status: active
created: 2026-08-15
updated: 2026-08-15
sources_verified: 2026-08-15
---

# Video MLLM 资料索引

> [!info] 归档范围
> 本目录保存 [[Paper/架构学习/RoadMap|RoadMap]] 所需的公开论文、课程 slides / handout / PPTX、课程源码和官方代码仓库快照。课程网页、技术文档、Notebook 与视频使用原始官网链接，不在 vault 中保存副本。

## 快速导航

- [[Paper/架构学习/Video-MLLM/00-shape-cheatsheet|00 Shape Cheatsheet]]
- [[Paper/架构学习/Video-MLLM/01-transformer|01 Transformer]]
- [[Paper/架构学习/Video-MLLM/02-vit|02 ViT]]
- [[Paper/架构学习/Video-MLLM/03-clip-siglip|03 CLIP 与 SigLIP]]
- [[Paper/架构学习/Video-MLLM/04-blip-llava|04 BLIP 与 LLaVA]]
- [[Paper/架构学习/Video-MLLM/05-onevision-trace|05 OneVision Trace]]
- [[Paper/架构学习/Video-MLLM/06-compression-map|06 Compression Map]]
- [[Paper/架构学习/Video-MLLM/resources/SHA256SUMS.txt|SHA-256 清单]]

## 论文

### 基础架构与视觉语言模型

| 年份 | 论文 | 本地 PDF | 使用阶段 |
| ---: | --- | --- | --- |
| 2016 | Layer Normalization | [[Paper/架构学习/Video-MLLM/resources/papers/1607.06450-layer-normalization.pdf\|PDF]] | Transformer |
| 2017 | Attention Is All You Need | [[Paper/架构学习/Video-MLLM/resources/papers/1706.03762-attention-is-all-you-need.pdf\|PDF]] | Transformer |
| 2020 | An Image is Worth 16x16 Words | [[Paper/架构学习/Video-MLLM/resources/papers/2010.11929-vit.pdf\|PDF]] | ViT |
| 2021 | Learning Transferable Visual Models From Natural Language Supervision | [[Paper/架构学习/Video-MLLM/resources/papers/2103.00020-clip.pdf\|PDF]] | CLIP |
| 2022 | BLIP | [[Paper/架构学习/Video-MLLM/resources/papers/2201.12086-blip.pdf\|PDF]] | BLIP |
| 2023 | BLIP-2 | [[Paper/架构学习/Video-MLLM/resources/papers/2301.12597-blip2.pdf\|PDF]] | Q-Former / bottleneck |
| 2023 | Sigmoid Loss for Language Image Pre-Training | [[Paper/架构学习/Video-MLLM/resources/papers/2303.15343-siglip.pdf\|PDF]] | SigLIP |
| 2023 | Visual Instruction Tuning | [[Paper/架构学习/Video-MLLM/resources/papers/2304.08485-llava.pdf\|PDF]] | LLaVA |
| 2024 | LLaVA-OneVision | [[Paper/架构学习/Video-MLLM/resources/papers/2408.03326-llava-onevision.pdf\|PDF]] | OneVision |
| 2026 | LLaVA-OneVision-2 | [[Paper/架构学习/Video-MLLM/resources/papers/2605.25979-llava-onevision2.pdf\|PDF]] | 后续架构对照 |

### Visual Token / Video Compression

| 年份 | 论文 | 本地 PDF | 压缩位置 |
| ---: | --- | --- | --- |
| 2021 | DynamicViT | [[Paper/架构学习/Video-MLLM/resources/papers/2106.02034-dynamicvit.pdf\|PDF]] | ViT 中间层 pruning |
| 2022 | Token Merging: Your ViT But Faster | [[Paper/架构学习/Video-MLLM/resources/papers/2210.09461-tome.pdf\|PDF]] | ViT token merging |
| 2024 | FastV | [[Paper/架构学习/Video-MLLM/resources/papers/2403.06764-fastv.pdf\|PDF]] | LMM 中间层 pruning |
| 2024 | LLaVA-PruMerge | [[Paper/架构学习/Video-MLLM/resources/papers/2403.15388-llava-prumerge.pdf\|PDF]] | Vision 输出 merge |
| 2024 | LongVU | [[Paper/架构学习/Video-MLLM/resources/papers/2410.17434-longvu.pdf\|PDF]] | 长视频时空压缩 |

### 推理系统

| 年份 | 论文 | 本地 PDF | 主题 |
| ---: | --- | --- | --- |
| 2022 | FlashAttention | [[Paper/架构学习/Video-MLLM/resources/papers/2205.14135-flashattention.pdf\|PDF]] | IO-aware exact attention |
| 2022 | Fast Inference via Speculative Decoding | [[Paper/架构学习/Video-MLLM/resources/papers/2211.17192-speculative-decoding.pdf\|PDF]] | Speculative decoding |
| 2023 | Speculative Sampling | [[Paper/架构学习/Video-MLLM/resources/papers/2302.01318-speculative-sampling.pdf\|PDF]] | Lossless sampling acceleration |
| 2023 | Inference with Reference | [[Paper/架构学习/Video-MLLM/resources/papers/2304.04487-inference-with-reference.pdf\|PDF]] | Reference-based decoding |
| 2023 | SpecInfer | [[Paper/架构学习/Video-MLLM/resources/papers/2305.09781-specinfer.pdf\|PDF]] | Tree verification |
| 2023 | FlashAttention-2 | [[Paper/架构学习/Video-MLLM/resources/papers/2307.08691-flashattention2.pdf\|PDF]] | Parallelism / work partitioning |
| 2024 | FlashAttention-3 | [[Paper/架构学习/Video-MLLM/resources/papers/2407.08608-flashattention3.pdf\|PDF]] | Asynchrony / low precision |

## CS224N Winter 2026

课程官网：[CS224N Winter 2026](https://web.stanford.edu/class/cs224n/)

| 内容 | Slides / Handout | Notes / Code |
| --- | --- | --- |
| Lecture 3: Neural Network Basics | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture03-neuralnets-slides.pdf\|Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture03-neuralnets-notes.pdf\|Notes]] |
| Lecture 4: Language Models and RNNs | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture04-rnnlm-slides.pdf\|Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture04-rnnlm-notes.pdf\|Notes]] |
| Lecture 5: Transformers | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/lecture05-transformers-slides.pdf\|Slides]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/transformer-notes.pdf\|Transformer Notes]] |
| PyTorch Tutorial Session |  | [Official Colab](https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing) |
| Jurafsky & Martin Chapter 9 |  | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/jurafsky-martin-ch09-transformer.pdf\|PDF]] |
| Assignment 2 | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment2-handout.pdf\|Handout]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment2-code.zip\|Code ZIP]] |
| Assignment 3 | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment3-handout.pdf\|Handout]] | [[Paper/架构学习/Video-MLLM/resources/courses/cs224n/assignment3-code.zip\|Code ZIP]] |

> [!note]
> Winter 2026 课程录像只在 Stanford Canvas 对选课学生开放。公开自学视频仍使用官网指向的 2024 YouTube playlist，链接见 [[Paper/架构学习/RoadMap#CS224N Winter 2026 官方核验|RoadMap]]。

## NTU Machine Learning 2026 Spring

课程官网：[Machine Learning 2026 Spring](https://speech.ee.ntu.edu.tw/~hylee/ml/2026-spring.php)

| 内容 | PDF / PPTX | 作业入口 |
| --- | --- | --- |
| Fast Inference | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/inference-slides.pdf\|PDF]] · [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/inference-slides.pptx\|PPTX]] |  |
| Positional Embedding | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/positional-embedding-slides.pdf\|PDF]] · [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/positional-embedding-slides.pptx\|PPTX]] |  |
| HW3: LLM Fast Inference | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/hw3-fast-inference-handout.pdf\|Handout]] | [Official Colab](https://colab.research.google.com/drive/1vZNo6_PlaP2fvMqr3g5KoQA0rN79m24O?usp=sharing) |
| HW4: Training Transformers | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/hw4-training-transformer-handout.pdf\|Handout]] | [Official Colab](https://colab.research.google.com/drive/1G9CgvnhqQ5AwHc6nbVzVGCoe-xUXdSWB?usp=sharing) |

> [!note]
> FlashAttention、KV Cache、Positional Embedding 与作业说明视频没有下载；官方 YouTube / Colab / Kaggle 链接见 [[Paper/架构学习/RoadMap#李宏毅 Machine Learning 2026 Spring|RoadMap]]。

## CS336 Spring 2026

课程官网：[CS336 Spring 2026](https://cs336.stanford.edu/)

| 内容 | 本地文件 | 本路线范围 |
| --- | --- | --- |
| Lecture 1: Tokenization | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture01-tokenization.py\|Source]] | 选看 |
| Lecture 2: Resource Accounting | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture02-resource-accounting.py\|Source]] | 必读 |
| Lecture 3: Architectures | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture03-architectures.pdf\|PDF]] | 必读 |
| Lecture 4: Attention Alternatives and MoE | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture04-attention-alternatives-moe.pdf\|PDF]] | 选看 |
| Lecture 5: GPUs / TPUs | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture05-gpus-tpus.pdf\|PDF]] | 必读 |
| Lecture 6: Kernels / Triton | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture06-kernels-triton.py\|Source]] | 概念必看、代码选做 |
| Lecture 10: Inference | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture10-inference.py\|Source]] | 必读 |
| Lecture 17: Multimodality | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture17-multimodality.py\|Source]] | 必读 |
| Assignment 1: Basics | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/assignment1-basics.pdf\|Handout]] | §3 Transformer architecture 子集 |
| Assignment 2: Systems | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/assignment2-systems.pdf\|Handout]] | §2 profiling / memory、§4.1 attention benchmark |

## 官方代码快照

代码仓库以 ZIP 保存，避免在 iCloud vault 中展开大量小文件。文件名中的 `main` 表示下载时的默认分支快照；精确内容可用 SHA-256 清单固定。

| 项目 | 本地 ZIP | 对应笔记 |
| --- | --- | --- |
| Google Vision Transformer | [[Paper/架构学习/Video-MLLM/resources/code/google-vision-transformer-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/02-vit\|02 ViT]] |
| OpenAI CLIP | [[Paper/架构学习/Video-MLLM/resources/code/openai-clip-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/03-clip-siglip\|03 CLIP 与 SigLIP]] |
| Google Big Vision | [[Paper/架构学习/Video-MLLM/resources/code/google-big-vision-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/03-clip-siglip\|03 CLIP 与 SigLIP]] |
| Salesforce LAVIS | [[Paper/架构学习/Video-MLLM/resources/code/salesforce-lavis-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/04-blip-llava\|04 BLIP 与 LLaVA]] |
| LLaVA | [[Paper/架构学习/Video-MLLM/resources/code/llava-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/04-blip-llava\|04 BLIP 与 LLaVA]] |
| LLaVA-NeXT / OneVision | [[Paper/架构学习/Video-MLLM/resources/code/llava-next-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/05-onevision-trace\|05 OneVision Trace]] |
| CS336 Assignment 1 | [[Paper/架构学习/Video-MLLM/resources/code/cs336-assignment1-basics-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/01-transformer\|01 Transformer]] |
| CS336 Assignment 2 | [[Paper/架构学习/Video-MLLM/resources/code/cs336-assignment2-systems-main.zip\|ZIP]] | [[Paper/架构学习/Video-MLLM/05-onevision-trace\|05 OneVision Trace]] |

## 在线文档

### PyTorch

- [Tensors Tutorial](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)
- [Building Models with PyTorch](https://docs.pytorch.org/tutorials/beginner/introyt/modelsyt_tutorial.html)
- [torch.einsum API](https://docs.pytorch.org/docs/stable/generated/torch.einsum.html)
- [Profiler Recipe](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)
- [torch.cuda.Event API](https://docs.pytorch.org/docs/stable/generated/torch.cuda.Event.html)
- [CUDA Memory Management](https://docs.pytorch.org/docs/stable/notes/cuda.html#memory-management)

### Hugging Face Transformers

- [ViT Docs](https://huggingface.co/docs/transformers/model_doc/vit)
- [SigLIP Docs](https://huggingface.co/docs/transformers/model_doc/siglip)
- [BLIP-2 Docs](https://huggingface.co/docs/transformers/model_doc/blip-2)
- [LLaVA Docs](https://huggingface.co/docs/transformers/model_doc/llava)
- [LLaVA-OneVision Docs](https://huggingface.co/docs/transformers/model_doc/llava_onevision)

## 完整性

- `PDF`：使用 `pdfinfo` 验证可解析。
- `ZIP / PPTX`：使用 `unzip -t` 验证归档完整。
- 所有文件的哈希：[[Paper/架构学习/Video-MLLM/resources/SHA256SUMS.txt|SHA256SUMS.txt]]。
