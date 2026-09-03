---
title: Video MLLM Compression Map
aliases:
  - 视频多模态模型压缩知识地图
tags:
  - video-mllm
  - token-compression
  - inference
  - systems
type: research-map
stage:
  - 9
  - 10
status: planned
created: 2026-08-15
updated: 2026-08-15
---

# Video MLLM Compression Map

> [!abstract] 阶段目标
> 对应 [[Paper/架构学习/RoadMap#阶段 9：视频压缩知识地图|RoadMap 阶段 9]] 与 [[Paper/架构学习/RoadMap#阶段 10：推理系统基础|阶段 10]]。按压缩发生位置统一比较方法，并把 token reduction 映射到真实的 vision、prefill、KV cache 与 decode 成本。

## 导航

- Baseline：[[Paper/架构学习/Video-MLLM/05-onevision-trace|05 OneVision Trace]]
- Shape 速查：[[Paper/架构学习/Video-MLLM/00-shape-cheatsheet|00 Shape Cheatsheet]]
- 压缩实验：[[Paper/架构学习/Video-MLLM/experiments/compression/README|Compression 实验模板]]
- 性能实验：[[Paper/架构学习/Video-MLLM/experiments/profiler/README|Profiler 实验模板]]

## 总地图

| 压缩位置 | 典型操作 | Vision 节省 | Projector 节省 | LLM Prefill / KV 节省 | 主要风险 |
| --- | --- | --- | --- | --- | --- |
| 视频输入前 | Frame / keyframe selection | 全部 | 全部 | 全部 | 丢失短时事件或时序证据 |
| 像素级 | Resize / crop / adaptive resolution | 全部或大部 | 是 | 是 | 小目标和文字变糊 |
| ViT 输入 | Patch selection | 全部或大部 | 是 | 是 | 编码前重要性估计不准 |
| ViT 中间层 | Token pruning / merging | 后续 blocks | 是 | 是 | 位置和局部结构被改变 |
| Vision 输出 | Token prune / merge | 否 | 是 | 是 | vision 成本已经发生 |
| Resampler | Latent queries / pooling | 通常否 | 视实现而定 | 是 | 固定瓶颈限制细粒度证据 |
| Projector 后 | LLM-space pruning | 否 | 否或部分 | 是 | 模态边界与 position 风险 |
| LLM 内部 | Hidden / attention / KV sparsity | 否 | 否 | 剩余 layers / cache | 实现侵入和后端支持 |

> [!important] 判断顺序
> 看到“visual tokens 减少 $x\%$”时，先确认压缩位置、压缩前后 $N$、已发生的计算、是否改变 token 语义，再看端到端 latency。Token reduction ratio 不能直接等同于加速比。

## 论文阅读队列

| 顺序 | 位置 / 方法 | 本地论文 | 精读范围 | 核心问题 |
| ---: | --- | --- | --- | --- |
| 1 | Mid-ViT pruning | [[Paper/架构学习/Video-MLLM/resources/papers/2106.02034-dynamicvit.pdf\|DynamicViT]] | Token sparsification module、stage-wise pruning、训练目标 | 哪些 block 后选择？是否真的减少后续 ViT 计算？ |
| 2 | Mid-ViT merging | [[Paper/架构学习/Video-MLLM/resources/papers/2210.09461-tome.pdf\|Token Merging / ToMe]] | Bipartite soft matching、proportional attention、training-free 应用 | Merge 相比 delete 保留什么？ |
| 3 | LLM 内 pruning | [[Paper/架构学习/Video-MLLM/resources/papers/2403.06764-fastv.pdf\|FastV]] | Layer 2 后的 visual token pruning、attention-based selection | 为什么在 LLM layer 2 后？节省哪些 LLM layers？ |
| 4 | Vision 输出 merge | [[Paper/架构学习/Video-MLLM/resources/papers/2403.15388-llava-prumerge.pdf\|LLaVA-PruMerge]] | Adaptive reduction、重要 token 与相似 token merging | Selection / merging 信号是什么？是否训练？ |
| 5 | 长视频时空压缩 | [[Paper/架构学习/Video-MLLM/resources/papers/2410.17434-longvu.pdf\|LongVU]] | Temporal redundancy、spatial reduction、adaptive compression | Frame 与 patch 两级预算如何配合？ |
| 6 | Learned bottleneck | [[Paper/架构学习/Video-MLLM/resources/papers/2301.12597-blip2.pdf\|BLIP-2]] | §3.1-3.3 Q-Former | 与 training-free pruning 如何在相同预算下比较？ |

## 每篇论文固定记录

### 方法卡片

| 字段 | 记录 |
| --- | --- |
| Paper / code revision |  |
| Base model / dataset |  |
| Compression position |  |
| $N_{before}\rightarrow N_{after}$ |  |
| Selection / merge signal |  |
| Query / answer / label leakage |  |
| Trainable parameters |  |
| Position / special-token handling |  |
| Vision savings |  |
| Projector / prefill / KV savings |  |
| Reported quality metric |  |
| Reported system metric |  |
| Fair-budget baseline |  |

- [ ] 压缩发生在哪个模块、哪一层之前或之后？
- [ ] 输入与输出 token 的语义是否相同？
- [ ] 方法是否需要训练，训练哪些参数？
- [ ] 推理时是否使用 query、候选 answer 或 label？
- [ ] 它节省 vision encoder、projector、LLM prefill、KV cache 中的哪些部分？
- [ ] 重要性来自 global frame feature、patch feature、attention 还是 LLM hidden state？
- [ ] position、CLS、newline 与 modality delimiter 如何处理？
- [ ] 比较是否使用相同 token / FLOPs / resolution / frame budget？

## Prune、Merge 与 Resample

| 维度 | Pruning | Merging | Learned Resampling |
| --- | --- | --- | --- |
| 输出含义 | 原 token 子集 | 多个 token 的聚合 | 新的 latent query representation |
| 预算 | Top-k / ratio | Merge ratio | 固定或配置的 query 数 |
| 信息处理 | 删除 | 聚合 | Cross-attention 重编码 |
| 训练要求 | 可训练或 training-free | 常可 training-free | 通常需要训练 |
| 位置风险 | 被删位置不可恢复 | 坐标 / size 需维护 | Query bottleneck 可能丢细节 |

## Capstone 对照实验

固定同一个 30-60 秒、事件变化明显的视频和同一组问题。

### A. Baseline

- [ ] 固定视频文件、frame 数、分辨率、prompt 和 generation 参数。
- [ ] 保存完整 shape trace 与 baseline answer。
- [ ] 分段测量 vision、projector、prefill、decode 和 peak memory。

### B. Frame-level Compression

- [ ] 将 uniform sampling 从 $T$ 减为 $T/2$，或用 CLIP / SigLIP relevance 选 Top-k。
- [ ] 保持其他设置不变，重新测量 vision 与 LLM 成本。
- [ ] 检查关键事件是否仍有被采样帧覆盖。

### C. Post-vision Token Compression

- [ ] 保持 frame 数不变，对每帧使用 pooling、similarity Top-k 或 spatial subsampling。
- [ ] 使用与 B 可比的最终 visual token budget。
- [ ] 验证 vision encoder 时间基本不因 post-vision 操作而降低。
- [ ] 记录 prefill、KV cache 和回答质量变化。

### D. Mid-ViT Compression（可选）

- [ ] 在指定 vision block 后插入 token selection 或 merging。
- [ ] 明确保留 special token，并修正 position / token size 信息。
- [ ] 在相同最终 token budget 下与 post-vision 方法比较。

| Run | 位置 | Frames | Tokens / frame | Vision ms | Prefill ms | Peak memory | Quality |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | 无 |  |  |  |  |  |  |
| Frame | 输入前 |  |  |  |  |  |  |
| Post-vision | Vision 后 |  |  |  |  |  |  |
| Mid-ViT | Vision 中间 |  |  |  |  |  |  |

## 推理系统资料

### 李宏毅 ML 2026 Spring

| 主题 | 本地材料 | 需要完成 |
| --- | --- | --- |
| Fast Inference | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/inference-slides.pdf\|Slides PDF]] · [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/inference-slides.pptx\|Slides PPTX]] | FlashAttention I/O、prefill / decode、KV cache |
| Positional Embedding | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/positional-embedding-slides.pdf\|Slides PDF]] · [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/positional-embedding-slides.pptx\|Slides PPTX]] | Absolute / relative position、RoPE、long context |
| HW3 Fast Inference | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/hw3-fast-inference-handout.pdf\|Handout]] · [Official Colab](https://colab.research.google.com/drive/1vZNo6_PlaP2fvMqr3g5KoQA0rN79m24O?usp=sharing) | Q1-Q10 论文；Q11-Q20 speculative decoding、FlashAttention、KV / PagedAttention、offloading |
| HW4 Transformer | [[Paper/架构学习/Video-MLLM/resources/courses/ntu-ml-2026/hw4-training-transformer-handout.pdf\|Handout]] · [Official Colab](https://colab.research.google.com/drive/1G9CgvnhqQ5AwHc6nbVzVGCoe-xUXdSWB?usp=sharing) | 选做 decoder-only next-token training |

> [!note] 课程视频
> 视频、课程网页与 Notebook 不在本地归档中。官方公开视频链接保留在 [[Paper/架构学习/RoadMap#李宏毅 Machine Learning 2026 Spring|RoadMap 阶段 10]]，Notebook 使用上表中的 Official Colab；本地只保存 slides、作业 PDF 与 PPTX。

### HW3 Q1-Q10 本地论文

| 主题 | 本地论文 |
| --- | --- |
| Speculative Decoding | [[Paper/架构学习/Video-MLLM/resources/papers/2211.17192-speculative-decoding.pdf\|Fast Inference via Speculative Decoding]] |
| Speculative Sampling | [[Paper/架构学习/Video-MLLM/resources/papers/2302.01318-speculative-sampling.pdf\|Speculative Sampling]] |
| Reference-based Decoding | [[Paper/架构学习/Video-MLLM/resources/papers/2304.04487-inference-with-reference.pdf\|Inference with Reference]] |
| Tree Verification | [[Paper/架构学习/Video-MLLM/resources/papers/2305.09781-specinfer.pdf\|SpecInfer]] |
| FlashAttention | [[Paper/架构学习/Video-MLLM/resources/papers/2205.14135-flashattention.pdf\|FlashAttention]] |
| FlashAttention-2 | [[Paper/架构学习/Video-MLLM/resources/papers/2307.08691-flashattention2.pdf\|FlashAttention-2]] |
| FlashAttention-3 | [[Paper/架构学习/Video-MLLM/resources/papers/2407.08608-flashattention3.pdf\|FlashAttention-3]] |

- [ ] 为 HW3 Q1-Q10 的每道题记录证据所在论文与章节。
- [ ] 补全 Q11-Q20 Notebook 中的 TODO，并保存关键输出。
- [ ] 比较 manual speculative decoding 的 prompt、acceptance rate 与 $\gamma$。
- [ ] 比较 standard / tiled attention 的 HBM I/O，而不声称 exact attention FLOPs 被消除。
- [ ] 将 KV cache、PagedAttention 和 prefix reuse 连接到 OneVision 视觉前缀。

### CS336 2026 精选

| 内容 | 本地文件 | 路线范围 |
| --- | --- | --- |
| Resource Accounting | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture02-resource-accounting.py\|Lecture 2 Source]] | dtype memory、FLOPs、MFU、arithmetic intensity、roofline |
| Architectures | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture03-architectures.pdf\|Lecture 3 PDF]] | Pre-Norm、RMSNorm、RoPE、SwiGLU、维度与成本 |
| Attention / MoE | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture04-attention-alternatives-moe.pdf\|Lecture 4 PDF]] | 选看 sparse / linear attention、SSM、MoE |
| GPUs / TPUs | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture05-gpus-tpus.pdf\|Lecture 5 PDF]] | Memory hierarchy、Tensor Cores、性能上限 |
| Kernels / Triton | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture06-kernels-triton.py\|Lecture 6 Source]] | Launch、coalescing、tiling、fusion；代码选做 |
| Inference | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture10-inference.py\|Lecture 10 Source]] | TTFT、prefill / decode、KV、speculation、continuous batching |
| Multimodality | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/lecture17-multimodality.py\|Lecture 17 Source]] | ViT → CLIP / SigLIP → LLaVA / OneVision 复盘 |
| Assignment 1 | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/assignment1-basics.pdf\|A1 Handout]] · [[Paper/架构学习/Video-MLLM/resources/code/cs336-assignment1-basics-main.zip\|Code]] | 只做 §3 Transformer architecture 与 resource accounting |
| Assignment 2 | [[Paper/架构学习/Video-MLLM/resources/courses/cs336/assignment2-systems.pdf\|A2 Handout]] · [[Paper/架构学习/Video-MLLM/resources/code/cs336-assignment2-systems-main.zip\|Code]] | §2 profiling / memory、§4.1 attention benchmark |

- [ ] 区分 TTFT、single-request latency 与 multi-request throughput。
- [ ] 解释 prefill 常较 compute-bound、逐 token decode 常较 memory-bound 的原因。
- [ ] 写出 KV cache 对 batch、sequence、layers、KV heads 与 head dimension 的依赖。
- [ ] 比较 GQA、MLA、CLA、local attention 对 KV cache 的影响。
- [ ] 区分 lossy shortcut 与 lossless speculative sampling。
- [ ] 解释 continuous batching 与 PagedAttention 解决的不同问题。

## 最终交付

- [ ] 一张完整 data flow + shape 图。
- [ ] 一张 token count vs stage 图。
- [ ] 一张压缩前后 latency breakdown 图。
- [ ] 一张 answer quality vs token budget 图。
- [ ] 每篇压缩论文的方法卡片。
- [ ] 一页结论：哪个压缩位置最值得采用，测量证据是什么？
