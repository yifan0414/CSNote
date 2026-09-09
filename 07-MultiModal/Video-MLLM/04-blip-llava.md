---
title: BLIP、BLIP-2 与 LLaVA 学习
aliases:
  - Video MLLM Stage 5-6 BLIP LLaVA
tags:
  - video-mllm
  - blip
  - blip-2
  - llava
type: learning-note
stage:
  - 5
  - 6
status: planned
created: 2026-08-15
updated: 2026-09-09
---

# BLIP、BLIP-2 与 LLaVA 学习

> [!abstract] 阶段目标
> 对应 [[RoadMap#阶段 5：BLIP 与 BLIP-2|RoadMap 阶段 5]] 与 [[RoadMap#阶段 6：LLaVA|阶段 6]]。先理解跨模态交互和固定 query bottleneck，再沿 LLaVA 的 vision tower → projector → LLM 路径完成单图 trace。

## 导航

- 前置：[[03-clip-siglip|03 CLIP 与 SigLIP]]
- 下一阶段：[[05-onevision-trace|05 OneVision Trace]]
- Trace 模板：[[trace-实验模板|Trace 实验模板]]
- Compression Map：[[06-compression-map|06 Compression Map]]

## 学习资料

### BLIP 与 BLIP-2

| 类型 | 文件 | 阅读 / 检查范围 |
| --- | --- | --- |
| 原始论文 | [[2201.12086-blip.pdf\|BLIP PDF]] | Figure 2、§3、§3.1；区分 ITC / ITM / LM |
| 原始论文 | [[2301.12597-blip2.pdf\|BLIP-2 PDF]] | Figure 1-3、§3.1-3.3；Q-Former 与两阶段训练 |
| 官方代码 | [[salesforce-lavis-main.zip\|Salesforce LAVIS Snapshot]] | BLIP / BLIP-2 config、Q-Former、query_tokens、generate |
| 模型文档 | [Hugging Face BLIP-2 Docs](https://huggingface.co/docs/transformers/model_doc/blip-2) | VisionModel、QFormerModel、ConditionalGeneration |

### LLaVA

| 类型 | 文件 | 阅读 / 检查范围 |
| --- | --- | --- |
| 原始论文 | [[2304.08485-llava.pdf\|Visual Instruction Tuning PDF]] | Figure 1、§4、§4.1-4.2；projection 与两阶段训练 |
| 官方代码 | [[llava-main.zip\|LLaVA Official Snapshot]] | model builder、vision tower、mm_projector、image token replacement |
| 模型文档 | [Hugging Face LLaVA Docs](https://huggingface.co/docs/transformers/model_doc/llava) | Config、Processor、ForConditionalGeneration |
| 课程复习 | [[lecture17-multimodality.py\|CS336 Lecture 17 Source]] | LLaVA 与 multimodal token 部分 |

## Part A：BLIP

### 三种训练目标

| 目标 | 输入与交互 | 输出 / 损失 | 需要形成的判断 |
| --- | --- | --- | --- |
| ITC | 图像与文本分别编码 | Global image-text similarity | 类似 CLIP 的粗粒度对齐 |
| ITM | 文本可以读取图像特征 | Match / mismatch probability | 分数来自跨模态交互，不等于 cosine similarity |
| LM | 文本按因果顺序读取视觉信息 | Next-token likelihood | 连接到视觉条件生成 |

- [ ] 阅读 BLIP Figure 2 和 §3.1，标出 image encoder、text encoder、image-grounded text encoder / decoder。
- [ ] 分别写出 ITC、ITM、LM 的 attention mask 和训练信号。
- [ ] 比较同一批 image-text pairs 的 ITC similarity 与 ITM score 排序。
- [ ] 选读 §3.2，只解释 CapFilt 的 captioner 与 filter，不复现数据清洗。

## Part B：BLIP-2 与 Q-Former

设冻结 vision encoder 的输出为：

$$
Z\in\mathbb{R}^{B\times N_v\times D_v}
$$

使用 $M$ 个 learnable queries 与 image features 做 cross-attention：

$$
Q=Q_{\mathrm{latent}}W_Q,\qquad K=ZW_K,\qquad V=ZW_V
$$

输出为固定长度：

$$
Z_q\in\mathbb{R}^{B\times M\times D_q}
$$

> [!note] 论文示例配置
> 原论文 §3.1 使用 32 个、维度 768 的 queries，并给出 $257\times1024$ image features → $32\times768$ Q-Former outputs 的示例。真实实验以所用 checkpoint config 和 trace 为准。

### 两阶段学习

| 阶段 | 冻结模块 | Q-Former 的工作 | 必读内容 |
| --- | --- | --- | --- |
| Stage 1 | Image encoder | 从 image-text pairs 学习视觉语言表示 | ITC、ITG、ITM 三种目标及各自 mask |
| Stage 2 | Image encoder + LLM | 将固定 query outputs 接入 frozen LLM | FC projection、decoder-only / encoder-decoder 接法 |

- [ ] 确认 latent queries 不是输入图像中的 patch tokens。
- [ ] 标出 query self-attention 与每隔一个 block 插入的 cross-attention。
- [ ] 为 Q-Former query self-attention 和 cross-attention 注册 hook。
- [ ] 记录 image features 的 $N_v,D_v$ 与 query outputs 的 $M,D_q$。
- [ ] 改变图像分辨率，确认 $N_v$ 可变而 $M$ 固定。
- [ ] 比较 Q-Former resampling、hard pruning 与 token merging。

| 方法 | 输出 token 来源 | Token 数 | 是否删除输入 token | 是否需要学习 |
| --- | --- | ---: | --- | --- |
| Q-Former | Latent queries 聚合全部 image features | 固定 $M$ | 否，重新聚合 | 是 |
| Top-k pruning | 被选中的原 token | $k$ | 是 | 可选 |
| Token merging | 多个相似 token 的合并表示 | 预算决定 | 不直接删除信息，但有聚合损失 | 可选 |

## Part C：LLaVA

~~~text
Image
  → CLIP Vision Encoder
  → Patch Features [B, Nv, Dv]
  → Projector [B, Nv, Dl]
  → Replace / Merge at <image> Position
  → LLM Inputs [B, Nv + Nt, Dl]
  → Prefill → KV Cache → Generation
~~~

### Projector 只解决什么

$$
Z_v:[B,N_v,D_v]
\xrightarrow{\mathrm{Projector}}
\widetilde{Z}_v:[B,N_v,D_l]
$$

通常 projector 改变 feature dimension $D_v\rightarrow D_l$，不自动改变 token 数 $N_v$。

- [ ] 阅读论文 Figure 1、§4.1 与 §4.2。
- [ ] 记录 Stage 1 feature alignment 与 Stage 2 visual instruction tuning 中的 frozen / trainable modules。
- [ ] 选读 §3，区分 conversation、detailed description、complex reasoning 三类数据。
- [ ] 从 model builder 找到 vision tower、projector 和 language model。
- [ ] 找到 image special token 被 visual embeddings 替换 / 展开的代码。
- [ ] 对照官方仓库与 Hugging Face 实现的 inputs_embeds、attention_mask 和 position_ids。

### 单图 Forward Trace

| 节点 | 预期 Shape | 实际 Shape | Token 是否变化 | 代码位置 |
| --- | --- | --- | --- | --- |
| Pixel values | $[B,C,H,W]$ |  |  |  |
| Vision patch features | $[B,N_v,D_v]$ |  |  |  |
| Selected feature layer | $[B,N_v,D_v]$ |  |  |  |
| Projector output | $[B,N_v,D_l]$ |  | 通常否 |  |
| Text embeddings | $[B,N_t,D_l]$ |  |  |  |
| LLM inputs_embeds | $[B,N_v+N_t,D_l]$ |  | 是，模态合并 |  |
| KV cache | 每层 K / V |  | 随 prefix 长度增长 |  |

- [ ] 对同一个问题分别运行纯文本与 image + text forward。
- [ ] 固定 warmup / repeat，比较两者 prefill latency。
- [ ] 估算视觉 prefix 增加的 KV cache 字节数。
- [ ] 说明 post-vision pruning 能节省 projector / LLM 的哪些部分。
- [ ] 说明它为什么不能回收已完成的 vision encoder 计算。

## 阶段产物

- [ ] BLIP ITC / ITM / LM 对比表。
- [ ] 一份 Q-Former bottleneck shape trace。
- [ ] Q-Former / pruning / merging 对比结论。
- [ ] 一份 LLaVA 单图端到端 forward trace。
- [ ] 纯文本与 image + text 的 prefill / KV cache 对照。
- [ ] 能独立说明“改变 $D$”与“改变 $N$”对成本的不同影响。
