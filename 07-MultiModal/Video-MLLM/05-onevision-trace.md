---
title: LLaVA-OneVision 端到端 Trace 与 Profiling
aliases:
  - Video MLLM Stage 7-8 OneVision Trace
tags:
  - video-mllm
  - llava-onevision
  - tracing
  - profiling
type: learning-note
stage:
  - 7
  - 8
status: planned
created: 2026-08-15
updated: 2026-09-09
---

# LLaVA-OneVision 端到端 Trace 与 Profiling

> [!abstract] 阶段目标
> 对应 [[RoadMap#阶段 7：LLaVA-OneVision|RoadMap 阶段 7]] 与 [[RoadMap#阶段 8：代码追踪与性能剖析|阶段 8]]。以真实 checkpoint 与代码为准，追踪 video processor → frame sampling → SigLIP → spatial reduction → projector → Qwen2，并分段测量成本。

## 导航

- 前置：[[04-blip-llava|04 BLIP 与 LLaVA]]
- Shape 速查：[[00-shape-cheatsheet|00 Shape Cheatsheet]]
- Trace 模板：[[trace-实验模板|Trace 实验模板]]
- Profiler 模板：[[profiler-实验模板|Profiler 实验模板]]
- 下一阶段：[[06-compression-map|06 Compression Map]]

## 学习资料

### 模型、论文与代码

| 类型 | 文件 | 必读 / 检查范围 |
| --- | --- | --- |
| 原始论文 | [[2408.03326-llava-onevision.pdf\|LLaVA-OneVision PDF]] | Figure 2-3、§3.1、§3.2、Appendix C.1；§5 选读 |
| 后续架构 | [[2605.25979-llava-onevision2.pdf\|LLaVA-OneVision-2 PDF]] | 后续对照，不作为原始 OneVision trace 的定义依据 |
| 官方代码 | [[llava-next-main.zip\|LLaVA-NeXT / OneVision Snapshot]] | OneVision README、video inference、mm_utils、vision tower、projector |
| 模型文档 | [Hugging Face OneVision Docs](https://huggingface.co/docs/transformers/model_doc/llava_onevision) | Config、Processor、ForConditionalGeneration、video inputs |
| 课程复习 | [[lecture17-multimodality.py\|CS336 Lecture 17 Source]] | SigLIP、AnyRes、OneVision single / multi-image / video |

### Profiling 与成本分析

| 类型 | 文件 | 使用范围 |
| --- | --- | --- |
| PyTorch | [Profiler Recipe](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html) | activities、schedule、record_shapes、profile_memory、key_averages |
| PyTorch | [CUDA Event API](https://docs.pytorch.org/docs/stable/generated/torch.cuda.Event.html) | GPU 分段计时、synchronize |
| PyTorch | [CUDA Memory Management](https://docs.pytorch.org/docs/stable/notes/cuda.html#memory-management) | allocated、reserved、peak stats、caching allocator |
| CS336 | [[lecture02-resource-accounting.py\|Lecture 2 Source]] | dtype memory、FLOPs、arithmetic intensity、roofline |
| CS336 | [[lecture10-inference.py\|Lecture 10 Source]] | TTFT、prefill / decode、KV cache、PagedAttention |
| CS336 作业 | [[assignment2-systems.pdf\|A2 Systems Handout]] | §2 profiling / benchmarking、§4.1 attention benchmark |
| CS336 代码 | [[cs336-assignment2-systems-main.zip\|A2 Systems Code Snapshot]] | 复用 benchmark 结构 |

## 论文先行

原始 OneVision 由 Qwen2、SigLIP vision encoder 与两层 MLP projector 组成，并统一处理 single-image、multi-image 与 video。

- [ ] 阅读 §3.1，画出 Qwen2 / SigLIP / MLP 三个核心模块。
- [ ] 阅读 §3.2，分别画出 single-image、multi-image、video token 路径。
- [ ] 阅读 Appendix C.1，整理每种模态的 token allocation。
- [ ] 选读 §5，只记录各训练阶段的 trainable modules 与模态混合。
- [ ] 对照当前 checkpoint config，不把论文中的示例数字当成固定实现。

> [!warning] 数量不一致
> 论文描述 SO400M 对 $384\times384$ 输入产生 729 个视觉 token；video frame 经过 vision encoder 后做 $2\times2$ bilinear interpolation，并写作 196 tokens / frame、最多 32 帧。同一部分的 maximum 表达存在不一致。实验结论必须引用当前 processor、checkpoint 与 forward trace 的实际 shape。

## Video 数据流

~~~text
Video file
  → Decode / Frame Sampling
  → Resize / Normalize
  → pixel_values_videos [B, T, C, H, W]
  → flatten B,T when required
  → SigLIP Vision Tower [B*T, N1, Dv]
  → Feature Layer / Special-token Selection
  → Spatial Reduction [B*T, N2, Dv]
  → MLP Projector [B*T, N2, Dl]
  → Frame Packing / Newline Tokens
  → Replace <video> Marker in Text Embeddings
  → Qwen2 inputs_embeds [B, Nvideo + Ntext, Dl]
  → Prefill / KV Cache
  → Autoregressive Decode
~~~

## Day 1：配置与模型身份

- [ ] 记录 model id、revision / commit、Transformers 版本和 dtype。
- [ ] 保存 vision_config 与 text_config。
- [ ] 记录 image_size、patch_size、vision hidden size、layers、heads。
- [ ] 记录 vision_feature_layer、vision_feature_select_strategy。
- [ ] 记录 projector 类型与 LLM hidden size。
- [ ] 记录 image / video token id 和相关 special tokens。

## Day 2：Processor 与 Frame Sampling

- [ ] 找到视频 backend、FPS / uniform sampling 和最大帧数逻辑。
- [ ] 记录原视频 duration、FPS、总帧数与采样索引。
- [ ] 记录 resize、crop、rescale、normalize 和 channel order。
- [ ] 记录 processor 输出的 pixel_values、image_sizes、modalities 与 text tokens。
- [ ] 确认 batch 内不同视频长度使用 padding、packing 还是逐样本处理。

| 项目 | 实际值 |
| --- | --- |
| Video path / SHA-256 |  |
| Duration / source FPS |  |
| Source frames |  |
| Sampled frame indices |  |
| Sampled $T$ |  |
| Resize / crop |  |
| pixel_values shape |  |

## Day 3：SigLIP → Spatial Reduction

- [ ] 在 vision embeddings、首层、中间层、选定 feature layer 和输出处记录 shape。
- [ ] 确认 CLS / special token 是否移除。
- [ ] 将 token sequence 恢复为空间网格，记录 grid height / width。
- [ ] 找到 bilinear interpolation / pooling 的确切函数与参数。
- [ ] 记录 $N_1\rightarrow N_2$，解释 floor / ceil / rounding 行为。

| 节点 | Shape | $N$ | dtype | device | 代码位置 |
| --- | --- | ---: | --- | --- | --- |
| Vision input |  |  |  |  |  |
| Patch embedding |  |  |  |  |  |
| Selected hidden state |  |  |  |  |  |
| Without special token |  |  |  |  |  |
| Spatial grid |  |  |  |  |  |
| Reduced grid |  |  |  |  |  |

## Day 4：Projector 与 Packing

- [ ] 记录 projector 前后的 $N$ 与 $D$，验证它是否只改变最后一维。
- [ ] 确认每帧 token 的排列顺序。
- [ ] 确认 frame / image newline token 插入位置。
- [ ] 找到 video visual embeddings 替换文本 special token 的代码。
- [ ] 记录最终 visual token span 与 text token span。

| 节点 | Shape | Token 变化原因 |
| --- | --- | --- |
| Reduced vision features |  | Spatial reduction |
| Projector output |  | 通常只改变 $D$ |
| Per-frame packed tokens |  | 可能加入 newline / delimiter |
| All video tokens |  | 跨帧拼接 |
| Text embeddings |  | Tokenization |
| Final inputs_embeds |  | 替换 video marker |

## Day 5：Qwen2 输入与 KV Cache

- [ ] 保存 inputs_embeds、attention_mask、position_ids / cache_position 的 shape。
- [ ] 记录 prefill 的总序列长度与视觉 token 占比。
- [ ] 确认 GQA 下 query heads 与 KV heads。
- [ ] 检查每层 key / value cache 的真实 shape。
- [ ] 生成第 1 个和后续 token 时分别记录输入长度。

忽略实现布局与 padding 时：

$$
\mathrm{KV\ bytes}\approx
2\times L\times B\times H_{kv}\times N\times d_h\times\mathrm{dtype\ bytes}
$$

## Day 6-7：分段 Profiling

### 测量协议

- [ ] 固定硬件、软件版本、model revision、输入和随机种子。
- [ ] warmup 后再重复测量，报告 median 与 p90 / range。
- [ ] CUDA Event 前后正确 record，并在读取时间前 synchronize。
- [ ] 分开 preprocess、vision、reduction / projector、prefill 与 decode。
- [ ] latency 测量与 profiler trace 分开运行，避免 profiler 开销污染基线。
- [ ] reset peak stats 后记录 allocated、reserved、max allocated。

| Stage | Median ms | p90 / range | Peak allocated | Tokens in → out |
| --- | ---: | ---: | ---: | --- |
| Video decode / preprocess |  |  |  |  |
| Vision tower |  |  |  |  |
| Spatial reduction |  |  |  |  |
| Projector / packing |  |  |  |  |
| LLM prefill |  |  |  |  |
| Decode per token |  |  |  |  |
| End-to-end |  |  |  |  |

### 实验矩阵

| 变量 | 档位 | 需要回答 |
| --- | --- | --- |
| Frames $T$ | 4 / 8 / 16 / 32 | Vision 与 prefill 如何增长？ |
| Tokens / frame | 原始 / $1/2$ / $1/4$ | LLM prefill 与 KV 如何变化？ |
| Text length | 短 / 中 / 长 | 视觉 prefix 占比如何变化？ |
| Compression position | Frame / mid-ViT / post-vision | 各自节省哪些 stage？ |
| Batch | 1 / 2（显存允许时） | Latency、throughput 与 padding 如何变化？ |

## 可插入压缩的位置

| 位置 | 可用信号 | 理论节省 | 风险 |
| --- | --- | --- | --- |
| Frame sampling 前 | 时间、motion、global relevance | 全部后续 vision + LLM | 丢失短时关键事件 |
| ViT 输入 / 中间层 | Patch / intermediate features | 后续 vision blocks + LLM | 位置与局部结构破坏 |
| Spatial reduction 后 | Vision features | Projector + LLM | Vision 成本已发生 |
| Projector 后 | LLM-space features | LLM prefill + KV | 模态边界和 position 处理 |
| LLM 内部 | Attention / hidden state | 剩余 LLM layers | 后端侵入较大 |

## 阶段产物

- [ ] Single-image、multi-image 与 video token strategy 对照图。
- [ ] 一份 processor 与 frame sampling 记录。
- [ ] 一份 SigLIP → reduction → projector → Qwen2 完整 shape trace。
- [ ] 一份 visual token span、mask、position 与 KV cache 记录。
- [ ] 一份可重复的 latency / memory breakdown。
- [ ] 标出至少三个 compression insertion points，并说明节省与损失。
