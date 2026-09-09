---
title: "Video MLLM 学习路线：从 Transformer 到视频 Token 压缩"
aliases:
  - Video MLLM Learning Roadmap
  - 多模态视频压缩学习路线
tags:
  - roadmap
  - video-mllm
  - transformer
  - visual-token-compression
type: learning-roadmap
status: active
created: 2026-08-15
updated: 2026-09-09
sources_verified: 2026-08-15
estimated_duration: 10 weeks
---

# Video MLLM 学习路线

> [!abstract] 最终目标
> 从“会调用多模态模型”进阶到“能沿 forward pass 定位视觉 token、解释计算成本，并独立设计和评估视频压缩方法”。

> [!note] 资料核验说明
> - 课程官网、讲义、作业和官方代码入口已于 **2026-08-15** 逐项检查。
> - 课程表可能继续更新；本路线记录的是核验当日官网公开版本。
> - “必看”表示必须完成指定章节或题目，不等于从头到尾看完整门课。
> - 论文链接优先指向原始论文，代码链接优先指向作者或课程官方仓库。

> [!info] 贯穿全程的主线
> **Pixels / Frames → Patch Tokens → Vision Transformer → Visual Features → Projector / Resampler → LLM Input Tokens → Prefill → KV Cache → Generation**
>
> 学习每个模型时，都要回答五个问题：
> 1. Token 从哪里产生？
> 2. 关键 tensor 的 shape 是什么？
> 3. 模态在哪里融合，信息在哪里丢失？
> 4. 哪些位置可以压缩？
> 5. 压缩后具体节省哪一段计算和显存？

~~~mermaid
flowchart LR
    A[Transformer] --> B[ViT]
    B --> C[CLIP / SigLIP]
    C --> D[BLIP / BLIP-2]
    D --> E[LLaVA]
    E --> F[LLaVA-OneVision]
    F --> G[Forward Trace]
    G --> H[Profiling]
    H --> I[Video / Token Compression]
    I --> J[Efficiency Research]
~~~

## 快速导航

| 模块 | 内容 |
| --- | --- |
| 使用说明 | [[#如何使用这份路线]] |
| 基础架构 | [[#阶段 0：准备与前置检查]] · [[#阶段 1：Transformer]] · [[#阶段 2：ViT]] |
| 视觉语言模型 | [[#阶段 3：CLIP]] · [[#阶段 4：SigLIP]] · [[#阶段 5：BLIP 与 BLIP-2]] |
| 主目标模型 | [[#阶段 6：LLaVA]] · [[#阶段 7：LLaVA-OneVision]] |
| 研究能力 | [[#阶段 8：代码追踪与性能剖析]] · [[#阶段 9：视频压缩知识地图]] · [[#阶段 10：推理系统基础]] |
| 执行与验收 | [[#10 周执行计划]] · [[#阶段验收清单]] · [[#研究型 Capstone]] |
| 辅助信息 | [[#暂缓学习的内容]] · [[#参考资料]] |

## 如何使用这份路线

### 任务状态

- `- [ ]`：尚未完成。
- `- [x]`：已经完成，并留下了可复查的产物。
- 不要因为“看过”就勾选。只有完成对应输出或通过验收，任务才算结束。

> [!todo]- 当前未完成任务
> ~~~query
> path:"07-MultiModal/Video-MLLM/RoadMap.md" task-todo:/./
> ~~~

### 每个阶段的固定工作流

将下面的模板复制到对应的实验笔记中：

~~~md
- [ ] 概念：能解释结构与设计动机
- [ ] Tensor：写出关键节点的 shape，并标记 token 数 N 在哪里变化
- [ ] 源码：沿真实 forward 路径完成一次追踪
- [ ] 实验：记录至少一个可复现结果
- [ ] 研究判断：说明在此处压缩会节省什么、损失什么
~~~

### 掌握标准

| 层级     | 判断标准                                        | 是否进入下一阶段 |
| ------ | ------------------------------------------- | -------- |
| A. 会解释 | 能看图说明结构，但说不清 shape 和代码位置                    | 暂不进入     |
| B. 会追踪 | 能沿 forward 说明 token、shape、mask 和 projection | 可以进入     |
| C. 会改动 | 能插入 hook、prune 或 pooling，并测量成本变化            | 研究阶段目标   |

### 建议目录

~~~text
07-MultiModal/Video-MLLM/
├── RoadMap.md
├── 00-shape-cheatsheet.md
├── 01-transformer.md
├── 01-transformer-练习题.md
├── 02-vit.md
├── 03-clip-siglip.md
├── 04-blip-llava.md
├── 05-onevision-trace.md
├── 06-compression-map.md
├── experiments/
│   ├── traces/trace-实验模板.md
│   ├── profiler/profiler-实验模板.md
│   └── compression/compression-实验模板.md
└── resources/
    ├── 资料索引.md
    ├── papers/
    ├── code/
    └── courses/
~~~

---

## 阶段 0：准备与前置检查

**预计用时**：0.5-1 天  
**阶段目标**：确认自己能够无障碍阅读 Transformer 和 PyTorch 的 forward。

### 参考资料与具体范围

| 优先级 | 官方资料                                                                                                                        | 具体学习内容                                           | 完成方式                       |
| --- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------- |
| 必读  | [PyTorch Tensors Tutorial](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)                       | Tensor shape、dtype、device、索引、拼接、矩阵乘法、与 NumPy 的转换 | 跑通示例，并给每个 tensor 写 shape   |
| 必读  | [Building Models with PyTorch](https://docs.pytorch.org/tutorials/beginner/introyt/modelsyt_tutorial.html)                  | Module、参数注册、forward、Linear、activation、模型层级       | 手写两层 MLP 和 residual block  |
| 查阅  | [torch.einsum API](https://docs.pytorch.org/docs/stable/generated/torch.einsum.html)                                        | Einstein notation、batch 维和 contraction 维         | 用 einsum 重写一次 batch matmul |
| 选看  | [CS224N 2026 PyTorch Tutorial Colab](https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing) | 2026-01-16 官方 tutorial session 的 PyTorch 实践      | PyTorch 不熟时完整跑一遍           |

### 学习任务

- [ ] 能推理矩阵乘法维度，例如 $[B,N,D]\times[D,H]\rightarrow[B,N,H]$。
- [ ] 能解释 Linear、MLP、activation、residual connection 和 LayerNorm 的基本作用。
- [ ] 熟悉 reshape、view、transpose、permute、matmul 和 einsum。
- [ ] 能解释 module、parameter、hidden state、forward 和 gradient。
- [ ] 用 PyTorch 建立一个输入为 $[B,N,D]$ 的两层 MLP，并打印每一步 shape。

### 暂不要求

- 完整手推反向传播。
- 分布式训练、FSDP 和 ZeRO。
- CUDA 或 Triton kernel 编程。
- 从零训练大语言模型。
- 完整 NLP 历史。

> [!success] 阶段验收
> - [ ] 看到 `x.shape = [2, 196, 768]` 时，能立即说明 batch=2、tokens=196、hidden=768。
> - [ ] 看到 `Linear(768, 3072)` 时，能判断输出 shape。

---

## 阶段 1：Transformer

**预计用时**：4-6 天  
**学习入口**：CS224N 的 NN Basics、Language Models / RNN、Transformers，以及 Assignment 3 的核心部分。[[#R1|R1]] [[#R2|R2]]

### CS224N Winter 2026 官方核验

**课程官网**：[CS224N Winter 2026](https://web.stanford.edu/class/cs224n/)

> [!warning] 视频版本
> 官网明确说明：Winter 2026 课堂录像只在 Stanford Canvas 对选课学生开放；公开自学视频仍是 [CS224N 2024 YouTube Playlist](https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D)。因此本路线以 **2026 slides、notes 和 assignments** 为准，公开视频只用于辅助理解。

| 日期 | 官方课程内容 | 官方材料 | 本路线要掌握 |
| --- | --- | --- | --- |
| 2026-01-13 | Backpropagation and Neural Network Basics | [Slides](https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture03-neuralnets.pdf) · [Notes](https://web.stanford.edu/class/cs224n/readings/cs224n-2019-notes03-neuralnets.pdf) | Vectorization、计算图、Linear / MLP、activation、反向传播、参数与 shape |
| 2026-01-15 | Language Models and RNNs | [Slides](https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture04-rnnlm.pdf) · [Notes](https://web.stanford.edu/class/cs224n/readings/cs224n-2019-notes05-LM_RNN.pdf) | Autoregressive LM、RNN 串行依赖、vanishing gradient；LSTM 只看动机 |
| 2026-01-20 | Transformers | [Slides](https://web.stanford.edu/class/cs224n/slides_w26/cs224n-2026-lecture05-transformers.pdf) · [Notes](https://web.stanford.edu/class/cs224n/readings/cs224n-self-attention-transformers-2023_draft.pdf) | Q / K / V、scaled dot-product attention、multi-head、mask、position、Transformer block |
| 2026-01-16 | PyTorch Tutorial Session | [Official Colab](https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing) | Module、tensor 操作和训练循环；不熟 PyTorch 时必做 |

**配套论文和讲义**

- [ ] 精读 [Attention Is All You Need](https://arxiv.org/abs/1706.03762) 的 §3 Model Architecture，重点是 §3.2 Attention、§3.4 Embeddings and Softmax、§3.5 Positional Encoding。
- [ ] 精读 CS224N 2026 Transformer notes 中 self-attention、multi-head、mask 和 positional representation。
- [ ] 选读 [Jurafsky & Martin, Chapter 9: The Transformer](https://web.stanford.edu/~jurafsky/slp3/9.pdf)，用于补足 decoder-only LM 视角。
- [ ] LayerNorm 不清楚时查阅 [Layer Normalization](https://arxiv.org/abs/1607.06450)。

### CS224N 作业范围

> [!info]- CS224N 2026 四次作业全表
> | 作业 | 官网说明 | 与本路线的关系 |
> | --- | --- | --- |
> | A1 | Introduction to word vectors | 当前跳过 |
> | A2 | Neural network foundations、tensor derivatives、dependency parsing | 只选做 optimizer / dropout 与 PyTorch 网络部分 |
> | A3 | Self-attention and Transformers | 本阶段核心作业 |
> | A4 | Large language model benchmarking and evaluation | 当前跳过，做 benchmark 时再回看 |

**Assignment 2（选做）**

- 官方材料：[Handout](https://web.stanford.edu/class/cs224n/assignments_w26/a2.pdf) · [Code](https://web.stanford.edu/class/cs224n/assignments_w26/a2.zip)
- 题目组成：Q1 Understanding Word2Vec（20 分）、Q2 Neural Networks Optimization（8 分，Adam + Dropout）、Q3 Neural Transition-Based Dependency Parsing（40 分）。
- [ ] 只完成 Q2 的 Adam 与 Dropout。
- [ ] PyTorch 不熟时阅读 Q3(e) 的网络训练部分；dependency parsing 其余题目不作为前置。

**Assignment 3（必做）**

- 官方材料：[Handout](https://web.stanford.edu/class/cs224n/assignments_w26/a3.pdf) · [Code](https://web.stanford.edu/class/cs224n/assignments_w26/a3.zip)
- 官网时间：2026-01-22 发布，2026-02-05 截止。

| 部分 | 官方题目 | 具体内容 | 路线要求 |
| --- | --- | --- | --- |
| Q1，14 分 | Attention Exploration | Attention copying、同时聚合两个 value、single-head 的不稳定性、multi-head 的收益 | 全做 |
| Q2，6 分 | Position Embeddings Exploration | 无位置编码时的 permutation equivariance、sinusoidal position embedding | 全做 |
| Q3(a)，20 分 | Coding a Transformer from Scratch | 依次实现 MLP、CausalAttention、DecoderBlock、Transformer.forward、greedy generate | 全做并打印 shape |
| Q3(b)，10 分 | Training | 实现 batch loss，训练 100 batches，提交 loss 和 gradient norm 曲线 | 全做 |
| Q3(c)，9 分 bonus | Speed up Learning | 修改 learning rate、optimizer 或架构，比较 100 steps 后 loss | 选做 |

### Day 1：神经网络最低基础

- [ ] 快速学习 vectorization、Linear、MLP、LayerNorm 和 residual。
- [ ] 用 PyTorch 手写一个两层 MLP，确认它只改变最后一维，不改变 token 数 $N$。
- [ ] 实现 $y=x+f(\operatorname{LN}(x))$，并验证 residual 两侧 shape 一致。
- [ ] 产出一页 shape 表，记录上述模块的输入、输出和作用。

### Day 2：理解 Transformer 出现的动机

- [ ] 理解 autoregressive language modeling：根据前缀预测下一个 token。
- [ ] 理解 RNN 的串行依赖和长距离依赖问题。
- [ ] 能解释 attention 为什么允许每个位置直接访问其他位置。

> [!warning] 停止点
> 能说明“为什么需要 attention / Transformer”后就进入下一部分，不要在 LSTM 门结构上消耗过多时间。

### Day 3-4：精学 Self-Attention

设输入为 $X\in\mathbb{R}^{B\times N\times D}$：

$$
Q=XW_Q,\qquad K=XW_K,\qquad V=XW_V
$$

$$
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_h}}\right)V
$$

当 head 数为 $H$ 且 $D=Hd_h$ 时：

$$
Q,K,V\in\mathbb{R}^{B\times H\times N\times d_h}
$$

$$
QK^\top\in\mathbb{R}^{B\times H\times N\times N}
$$

| 节点 | Shape |
| --- | --- |
| 输入 $X$ | $[B,N,D]$ |
| Q / K / V projection | $[B,N,D]$ |
| 拆分多头 | $[B,H,N,d_h]$ |
| Attention score | $[B,H,N,N]$ |
| 加权后的 context | $[B,H,N,d_h]$ |
| 合并多头并输出投影 | $[B,N,D]$ |

- [ ] 能从任意一行独立推出下一行的 shape。
- [ ] 能解释 $S_{b,h,i,j}$ 的含义。
- [ ] 能解释 softmax 为什么通常沿最后一维进行。
- [ ] 能解释为什么 $N\times N$ 部分随 token 数二次增长。
- [ ] 能解释为什么由 $V$ 承载被加权聚合的信息。
- [ ] 区分 padding mask 和 causal mask。
- [ ] 理解 token 数减半时，attention 核心计算近似降至四分之一，而逐 token 的 MLP 计算近似减半。

### Day 5：完整 Transformer Block

- [ ] 理解 Multi-Head Self-Attention。
- [ ] 理解 Residual + LayerNorm，并知道 Pre-LN / Post-LN 的区别。
- [ ] 理解 Feed-Forward / MLP 通常对每个 token 独立计算。
- [ ] 理解位置信息为什么不可缺少。
- [ ] 区分 encoder 的 bidirectional attention 与 decoder 的 causal attention。

> [!tip] 与多模态模型的连接
> ViT / CLIP vision encoder 通常使用双向 self-attention；Qwen / LLaMA 等 decoder-only LLM 使用 causal self-attention。LLaVA 把这两类 Transformer 串联在同一系统中。

### Day 6：实现 Attention 核心

- [ ] 自己实现 scaled dot-product attention。
- [ ] 自己实现 causal mask。
- [ ] 自己实现 multi-head 的 reshape、transpose 和 merge。
- [ ] 打印所有中间 tensor 的 shape。
- [ ] 对 $N\in\{64,128,256,512\}$ 做简单耗时实验并记录增长趋势。

> [!success] 阶段验收
> 给定 $X=[2,196,768]$ 且 heads=12：
> - [ ] 推出 $d_h=64$。
> - [ ] 推出 $Q/K/V=[2,12,196,64]$。
> - [ ] 推出 $QK^\top=[2,12,196,196]$。
> - [ ] 推出 attention 输出合并后为 $[2,196,768]$。
> - [ ] 说明 $N$ 从 196 降到 98 后，attention score 元素数为什么变为原来的 $1/4$。

---

## 阶段 2：ViT

**预计用时**：3-4 天  
**核心资料**：*An Image is Worth 16x16 Words*。[[#R3|R3]]

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要提取的信息 |
| --- | --- | --- | --- |
| 必读 | [ViT 原始论文](https://arxiv.org/abs/2010.11929) | Figure 1、§3 Method、§3.1 Vision Transformer、§3.2 Fine-Tuning and Higher Resolution、§4.5 Inspecting Vision Transformer | Patchify、CLS、position embedding、Pre-LN block、分辨率与 token 数、内部 representation |
| 实践 | [Google Research Vision Transformer](https://github.com/google-research/vision_transformer) | README、model configs、ViT implementation | 对照 patch size、hidden size、layers、heads 和 position embedding |
| 实践 | [Hugging Face ViT Docs](https://huggingface.co/docs/transformers/model_doc/vit) | ViTConfig、ViTModel、output_hidden_states | 完成可直接 hook 的最小 forward |
| 复习 | [CS336 2026 Lecture 17: Multimodal Models](https://cs336.stanford.edu/lectures/?trace=lecture_17) | Encoding images / ViT 部分 | 从“所有模态都要转成 token”的角度复述 ViT |

> [!note] 阅读边界
> 当前不需要精读 ViT 的大规模预训练数据、所有下游 benchmark 和完整消融实验。重点是 Figure 1、Equation (1)-(4)、token 数以及高分辨率时的位置插值。

### 核心结构

对于图像 $I\in\mathbb{R}^{H\times W\times C}$ 与 patch size $P$：

$$
N_{\text{patch}}=\frac{H}{P}\cdot\frac{W}{P}
$$

经过 patch projection 后：

$$
X_0\in\mathbb{R}^{B\times N_{\text{patch}}\times D}
$$

如果模型使用一个 [CLS] token，进入 Transformer 的序列长度为 $N_{\text{patch}}+1$。

~~~text
Image [B, 3, H, W]
  → Patchify / Conv2d(kernel=P, stride=P)
  → Patch Embeddings [B, N, D]
  → Position Embedding
  → Transformer Encoder × L
  → Patch-level Hidden States
  → CLS / Pooling
  → Global Image Representation
~~~

### 学习任务

- [ ] 能根据 $H$、$W$ 和 $P$ 计算 patch token 数。
- [ ] 理解 patch embedding 与 Conv2d(kernel=P, stride=P) 的等价关系。
- [ ] 理解普通 ViT block 通常保持 token 数 $N$ 不变。
- [ ] 区分 CLS / global embedding 与 patch-level features。
- [ ] 解释为何中间层 pruning 与 ViT 全部运行后再 pruning 的计算收益不同。

### 代码实践

- [ ] 加载一个公开 ViT，启用 output_hidden_states 或注册 forward hook。
- [ ] 打印 pixel_values、patch embedding、中间层、最后层和 pooled representation 的 shape。
- [ ] 改变输入分辨率或选择不同 patch size 的模型，手算并验证 token 数。
- [ ] 保存一份 shape trace。

| 节点 | 必须记录 | 需要回答的问题 |
| --- | --- | --- |
| Pixels | $B,C,H,W$ | 分辨率如何影响 $N$？ |
| Patch embedding | $B,N,D$ | Patch size 如何影响 $N$？ |
| ViT block $k$ | $B,N,D$ | $N$ 是否变化？ |
| Last hidden | $B,N,D$ | Patch features 在哪里被取出？ |
| Global representation | $B,D$ | Pooling 丢失了什么粒度？ |

> [!success] 阶段验收
> - [ ] 给定任意 ViT 配置，仅凭 $H$、$W$、patch size 和是否含 CLS，就能预测 token 数。
> - [ ] 能指出在哪一层减少 token 才会节省后续 vision blocks。

---

## 阶段 3：CLIP

**预计用时**：3-4 天  
**核心资料**：CLIP 原始论文。[[#R4|R4]]

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要完成 |
| --- | --- | --- | --- |
| 必读 | [CLIP 原始论文](https://arxiv.org/abs/2103.00020) | Figure 1、§2.3 Efficient Pre-Training、§2.4 Choosing and Scaling a Model、§2.5 Training、Figure 3 pseudocode | 写出双塔、normalize、temperature、symmetric cross-entropy 的完整数据流 |
| 查阅 | 同一论文 | §2.1 Natural Language Supervision、§2.2 Dataset、§3 Experiments | 只理解训练信号来源和 zero-shot 用法，不深挖数据收集 |
| 实践 | [OpenAI CLIP 官方仓库](https://github.com/openai/CLIP) | README usage、clip.load、clip.tokenize、encode_image、encode_text、logits_per_image | 实现 frame scorer，并绕过 global pooling 取 patch features |
| 复习 | [CS336 2026 Lecture 17](https://cs336.stanford.edu/lectures/?trace=lecture_17) | CLIP 部分 | 对照课程中的 batch 内图文配对和 ViT-L/14 表示 |

> [!warning] 代码边界
> OpenAI CLIP 的公开 API 主要返回 global embedding。Patch hidden states 需要进入 visual encoder 内部或使用支持 hidden states 的实现，不能把 logits_per_image 当作 patch importance。

### 双塔结构

CLIP 分别得到图像和文本的全局表示。归一化后的相似度可写为：

$$
s(I,T)=
\frac{f_I(I)^\top f_T(T)}
{\lVert f_I(I)\rVert_2\lVert f_T(T)\rVert_2}
$$

~~~text
Image → Vision Encoder → Global Image Embedding ┐
                                                ├→ Normalize → Similarity / Temperature
Text  → Text Encoder   → Global Text Embedding  ┘
~~~

经典 CLIP 是 dual encoder。图像和文本不会在各自 encoder 内通过 cross-attention 融合。

### 学习任务

- [ ] 理解 vision tower：patch tokens → Transformer → global representation → projection。
- [ ] 理解 text tower：token / position embedding → Transformer → sentence representation → projection。
- [ ] 理解归一化后的点积为何接近 cosine similarity。
- [ ] 理解 logit_scale / temperature 对相似度分布的影响。
- [ ] 理解 batch 内正负图文对和 softmax-style contrastive objective。
- [ ] 区分 frame-level global score 与单帧内部 patch token 的重要性。

> [!important] 与视频压缩的关键区别
> Frame relevance 常用一个 global vector 表示整帧；visual-token compression 处理的是单帧内部
> $Z_i=[z_{i1},\ldots,z_{iN}]$。
> “这帧重要”不能直接推出“这帧中的哪个 patch 重要”。

### 代码实践

- [ ] 手动复现 encode_image / encode_text → normalize → dot product。
- [ ] 绕过最终 global pooling，提取 vision tower 的 patch hidden states。
- [ ] 比较最后层与倒数第二层 patch features。
- [ ] 对一个 8 帧视频计算每帧与 query 的相似度并排序。
- [ ] 选择其中一帧，说明 frame score 为什么不能直接给出 patch importance。
- [ ] 产出一个最小 CLIP frame scorer 和一份 global-vs-local 对比笔记。

---

## 阶段 4：SigLIP

**预计用时**：2-3 天  
**核心资料**：SigLIP 原始论文。[[#R5|R5]]

SigLIP 保留图像与文本双编码器的整体结构，但使用 pairwise sigmoid loss，不依赖 CLIP 式的全局 softmax normalization。

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要提取的信息 |
| --- | --- | --- | --- |
| 必读 | [SigLIP 原始论文](https://arxiv.org/abs/2303.15343) | Algorithm 1、§3.1 Softmax loss、§3.2 Sigmoid loss、§3.3 Efficient chunked implementation、§4.1-4.2 | Pairwise labels、temperature 与 bias、为何不需要 global normalization、batch-size 行为 |
| 实践 | [Google Big Vision 官方仓库](https://github.com/google-research/big_vision) | SigLIP / image-text configs 和 model implementation | 确认训练目标与 vision tower 输出不是同一层问题 |
| 实践 | [Hugging Face SigLIP Docs](https://huggingface.co/docs/transformers/model_doc/siglip) | SiglipVisionConfig、SiglipVisionModel、hidden_states | 读取 OneVision 上游 vision config 并完成 trace |
| 复习 | [CS336 2026 Lecture 17](https://cs336.stanford.edu/lectures/?trace=lecture_17) | SigLIP 部分 | 比较 CLIP multiclass-style objective 与 SigLIP binary objective |

### 学习任务

- [ ] 复用 CLIP 的“视觉塔 / 文本塔 / 相似度”框架，不重复学习全部基础。
- [ ] 比较 sigmoid loss 与 CLIP contrastive softmax。
- [ ] 理解 SigLIP vision tower 仍是 ViT-style patch tokenizer + Transformer。
- [ ] 能读取 image_size、patch_size、hidden_size、num_hidden_layers 和 num_attention_heads。
- [ ] 能定位 vision encoder 输出的 token 网格、hidden dimension 和下游使用的 feature layer。
- [ ] 比较 CLIP 与 SigLIP 在同一图片 / query 上的 global similarity 和排序稳定性。

> [!tip] 与 OneVision 的连接
> 原始 LLaVA-OneVision 使用 SigLIP 作为 Vision Encoder，并用两层 MLP 将视觉 features 投影到 Qwen2 的 embedding space。[[#R9|R9]]

> [!success] 阶段验收
> - [ ] 能解释 CLIP 与 SigLIP 最关键的 loss 差别。
> - [ ] 能根据 vision config 预测主要输出 shape。

---

## 阶段 5：BLIP 与 BLIP-2

**预计用时**：4-5 天  
**核心资料**：BLIP 与 BLIP-2 原始论文。[[#R6|R6]] [[#R7|R7]]

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要完成 |
| --- | --- | --- | --- |
| 必读 | [BLIP 原始论文](https://arxiv.org/abs/2201.12086) | Figure 2、§3 Method、§3.1 Model Architecture | 画出 image encoder、image-grounded text encoder / decoder，区分 ITC、ITM、LM 的 attention mask 和输出 |
| 选读 | BLIP §3.2 Captioning and Filtering | CapFilt 的 captioner、filter 和数据清洗流程 | 只理解它为何改善预训练数据，不复现 |
| 必读 | [BLIP-2 原始论文](https://arxiv.org/abs/2301.12597) | Figure 1-3、§3.1 Q-Former、§3.2 Representation Learning、§3.3 Generative Learning | 写出 32 queries、cross-attention、三种第一阶段目标和连接 frozen LLM 的第二阶段 |
| 实践 | [Salesforce LAVIS 官方仓库](https://github.com/salesforce/LAVIS) | BLIP / BLIP-2 model configs、predict / generate examples | 找到 Q-Former、query_tokens、vision encoder 和 LLM projection |
| 查阅 | [Hugging Face BLIP-2 Docs](https://huggingface.co/docs/transformers/model_doc/blip-2) | Blip2QFormerModel、Blip2VisionModel、Blip2ForConditionalGeneration | 用标准接口输出 hidden states 并注册 hook |

> [!note] BLIP-2 必须读清的数字
> 原论文 §3.1 使用 32 个、维度 768 的 queries；示例 frozen image features 为 $257\times1024$，Q-Former 输出为 $32\times768$。这些数字用于理解固定瓶颈，不代表所有实现都必须使用相同配置。

### BLIP：从对齐到跨模态交互

| 目标 | 直觉 | 与后续学习的关系 |
| --- | --- | --- |
| ITC | 对齐图像与文本的全局表示 | 理解 CLIP-style relevance |
| ITM | 判断图文对是否匹配，允许更深的跨模态交互 | 理解 ITM scorer 与 cosine scorer 的差别 |
| LM | 以视觉信息为条件生成文本 | 连接到多模态生成 |

- [ ] 在结构图中标出 image encoder、text encoder / decoder 和 cross-modal interaction。
- [ ] 比较 ITC、ITM 和 LM 的输入、输出与训练目标。
- [ ] 运行一次 image-text matching，并比较其分数与 CLIP cosine 的排序。
- [ ] 暂时跳过 CapFilt 数据清洗细节。

### BLIP-2：精读 Q-Former

设 vision encoder 输出：

$$
Z\in\mathbb{R}^{B\times N_v\times D_v}
$$

Q-Former 使用固定数量 $M$ 个 latent queries：

$$
Q=Q_{\text{latent}}W_Q,\qquad K=ZW_K,\qquad V=ZW_V
$$

当 $M\ll N_v$ 时，cross-attention 把大量视觉 features 重新聚合为固定数量的输出 token。这是 learned information bottleneck，不是简单删除原 token。

~~~text
Frozen Vision Encoder → Many Visual Features ┐
                                              ├→ Q-Former → Fixed-size Outputs → LLM
Learnable Queries → Query Self-Attention     ┘
~~~

- [ ] 理解 learnable queries 不是来自输入图像的 patch tokens。
- [ ] 理解 cross-attention 中 Q 来自 queries，K / V 来自 image features。
- [ ] 理解固定数量 latent queries 为什么构成信息瓶颈。
- [ ] 区分 Q-Former resampling、hard token pruning 和 token merging。

### 代码实践

- [ ] 为 Q-Former 的 query self-attention 和 cross-attention 注册 hook。
- [ ] 打印 image features 数量和 query outputs 数量。
- [ ] 在模型允许范围内改变输入分辨率，观察 image token 数与 query output 数。
- [ ] 写一份 Top-k pruning / token merging / Q-Former resampling 对比表。

> [!success] 阶段验收
> - [ ] 看到 resampler / latent queries / query tokens 时，能立即指出 query 数、K / V 来源、输出 token 数和压缩位置。

---

## 阶段 6：LLaVA

**预计用时**：3-4 天  
**核心资料**：LLaVA 原始论文。[[#R8|R8]]

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要提取的信息 |
| --- | --- | --- | --- |
| 必读 | [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) | Figure 1、§4 Visual Instruction Tuning、§4.1 Architecture、§4.2 Training | CLIP ViT-L/14、projection $W$、visual tokens 与 language instruction 的拼接、两阶段训练 |
| 选读 | 同一论文 §3 GPT-assisted Visual Instruction Data Generation | Conversation、detailed description、complex reasoning 三类数据 | 只理解 instruction tuning 数据从哪里来 |
| 实践 | [LLaVA 官方仓库](https://github.com/haotian-liu/LLaVA) | README、model builder、multimodal encoder / projector、conversation template | 定位 vision tower、mm_projector、image token replacement 和 generate |
| 查阅 | [Hugging Face LLaVA Docs](https://huggingface.co/docs/transformers/model_doc/llava) | LlavaConfig、LlavaProcessor、LlavaForConditionalGeneration | 用统一 API 对照官方仓库的 forward |
| 复习 | [CS336 2026 Lecture 17](https://cs336.stanford.edu/lectures/?trace=lecture_17) | LLaVA 部分 | 核对课程总结的 Stage 1 alignment 与 Stage 2 fine-tuning |

~~~text
Image
  → Vision Encoder
  → Patch-level Visual Features [B, Nv, Dv]
  → Projector / MLP
  → LLM-space Visual Embeddings [B, Nv, Dl]
  → Merge with Text Embeddings
  → Decoder-only LLM Prefill
  → Autoregressive Generation
~~~

### 模态桥接

$$
Z_v\in\mathbb{R}^{B\times N_v\times D_v}
\xrightarrow{\text{Projector}}
\widetilde{Z}_v\in\mathbb{R}^{B\times N_v\times D_l}
$$

Projector 通常负责将 feature dimension 从 $D_v$ 映射到 $D_l$，并不必然减少视觉 token 数 $N_v$。

### 学习任务

- [ ] 理解 vision hidden size 与 LLM hidden size 不同，因此需要 projector。
- [ ] 区分“改变 feature dimension”和“改变 token 数”。
- [ ] 理解视觉 embeddings 如何与文本 embeddings 组成 LLM 输入序列。
- [ ] 理解视觉 token 为什么增加 LLM prefill 和 KV cache 成本。
- [ ] 了解 alignment / projector training 与 instruction tuning 的基本分工。
- [ ] 能从论文中确认哪些模块 frozen、哪些模块 trainable。

### 代码实践

- [ ] 输入 1 张图和 1 个问题，完成一次 multimodal forward。
- [ ] 在 vision tower 输出处记录 $[B,N_v,D_v]$。
- [ ] 在 projector 后记录 $[B,N_v,D_l]$。
- [ ] 找到 visual embeddings 与 text embeddings 拼接或替换特殊 image token 的代码。
- [ ] 在 LLM 入口记录 inputs_embeds、attention_mask 和 position 信息。
- [ ] 比较纯文本与图像 + 文本的 prefill 时间。

> [!warning] 必须形成的判断
> 如果 vision encoder 已经处理完 576 个 token，之后才 prune 到 128，就不会节省已经发生的 vision tower 计算。它主要减少 projector 后续、LLM prefill 和 KV cache 成本。若在 ViT 中间层降到 128，才会进一步节省后续 vision blocks。

> [!success] 阶段验收
> - [ ] 能定位 vision tower → projector → LLM 的完整代码路径。
> - [ ] 能准确说明 post-vision pruning 节省和不节省的部分。

---

## 阶段 7：LLaVA-OneVision

**预计用时**：5-7 天  
**阶段定位**：主目标模型  
**核心资料**：LLaVA-OneVision 原始论文。[[#R9|R9]]

原始 OneVision 使用 Qwen2、SigLIP Vision Encoder 和两层 MLP projector，统一处理 single-image、multi-image 与 video。

### 参考资料与精读范围

| 优先级 | 资料 | 必看位置 | 需要完成 |
| --- | --- | --- | --- |
| 必读 | [LLaVA-OneVision 原始论文](https://arxiv.org/abs/2408.03326) | Figure 2-3、§3.1 Network Architecture、§3.2 Visual Representations、Appendix C.1 Token Strategy | 写出 single-image、multi-image、video 三条 token 路径及最大 token budget |
| 选读 | 同一论文 §5 Training Strategies | Stage 1、Stage 1.5、Single-Image、OneVision training | 只记录 trainable modules 和模态混合，不复现训练 |
| 实践 | [LLaVA-NeXT / OneVision 官方仓库](https://github.com/LLaVA-VL/LLaVA-NeXT) | OneVision README、video inference、mm_utils、vision tower 和 projector | 从 processor 一直追到 Qwen2 inputs_embeds |
| 实践 | [Hugging Face LLaVA-OneVision Docs](https://huggingface.co/docs/transformers/model_doc/llava_onevision) | LlavaOnevisionConfig、LlavaOnevisionProcessor、LlavaOnevisionForConditionalGeneration | 建立可复现的 image / video forward trace |
| 复习 | [CS336 2026 Lecture 17](https://cs336.stanford.edu/lectures/?trace=lecture_17) | LLaVA-OneVision 部分 | 核对 SigLIP、AnyRes、三种输入模态和 bilinear interpolation |

> [!warning] 论文与代码的优先级
> 论文 Figure 3 和 Appendix C.1 给出 token strategy，但 video 的文字描述存在数量表达不一致。研究实验中始终以所用 checkpoint、processor 和 forward trace 的实际 shape 为准。

### Day 1：论文主干

- [ ] 阅读 Section 3.1，画出 Qwen2 / SigLIP / MLP 三个核心模块。
- [ ] 阅读 Section 3.2，理解 single-image、multi-image 和 video 的视觉表示路径。
- [ ] 阅读 Appendix C.1，将不同模态的 token allocation 整理成表。
- [ ] 暂时跳过训练数据规模和大部分 benchmark 结果。

### Day 2：单独画出视频路径

~~~text
Video
  → Frame Sampling
  → Per-frame SigLIP Encoding
  → Per-frame Visual Feature Grid
  → Spatial Interpolation / Pooling
  → Projector
  → Pack Video Visual Tokens
  → Qwen2 Prefill with Question Tokens
  → Generation
~~~

论文写到：SO400M 对 $384\times384$ 输入产生 729 个视觉 token；视频帧经过 vision encoder 后再进行 $2\times2$ bilinear interpolation，文中描述为 196 tokens / frame，并最多采样 32 帧。论文同一部分的 maximum 表达与 196 tokens / frame 存在文字不一致，因此实际研究必须以当前代码 trace 的 shape 为准，而不是死背乘法结果。[[#R9|R9]]

- [ ] 标出 frame sampling、vision encoding、spatial reduction、projector 和 packing 的位置。
- [ ] 写出每一步的预期 token 数与 feature dimension。

### Day 3：追踪 Preprocessing

- [ ] 找到视频解码与 frame sampling 的实现。
- [ ] 记录 resize、normalize 和分辨率处理策略。
- [ ] 记录 processor 输出的 pixel_values、image_sizes 和 modality metadata。
- [ ] 确认 batch 内不同视频长度如何 pad 或 pack。
- [ ] 确认问题文本中的 image / video special token 如何表示。

### Day 4：追踪 Vision Tower → Projector

- [ ] 确认使用 SigLIP 的哪一层 feature。
- [ ] 记录每帧 encoder 前、encoder 后、spatial reduction 后的 token 数。
- [ ] 确认 projector 改变 $D$ 还是 $N$。
- [ ] 确认各帧 token 何时组成一个长序列。

### Day 5：追踪 LLM 输入与 Causal Attention

- [ ] 记录最终序列中视觉 token 与文本 token 的排列方式。
- [ ] 追踪 attention_mask 和 position_ids。
- [ ] 记录 prefill 阶段一次处理的总 sequence length。
- [ ] 理解 generation 时 KV cache 如何复用视觉和文本前缀。

### Day 6-7：完成端到端 Trace

| 阶段 | 建议记录格式 | 核心问题 |
| --- | --- | --- |
| Frames | $T\times H\times W$ | $T$ 在哪里决定？ |
| Vision input | $T\times N_0\times D_v$ | $N_0$ 与分辨率 / patch 的关系？ |
| Vision output | $T\times N_1\times D_v$ | $N_1$ 是否等于 $N_0$？ |
| Spatial reduction | $T\times N_2\times D_v$ | $N_1\rightarrow N_2$ 如何发生？ |
| Projector | $T\times N_2\times D_l$ | 是否只改变 $D$？ |
| LLM prefix | $N_{\text{video}}+N_{\text{text}}$ | 总 context 多长？ |
| KV cache | $L\times H\times N\times d_h$ | 视觉 token 占用多少？ |

- [ ] 保存完整 shape trace。
- [ ] 保存 visual token 在最终 LLM sequence 中的位置。
- [ ] 标出至少三个可插入 training-free compression 的位置。
- [ ] 为每个位置写出可节省的计算阶段和潜在信息损失。

> [!success] 阶段验收
> - [ ] 不依赖论文框图，仅看 forward 代码就能定位 frame sampling、vision encoder、spatial reduction、projector、visual embedding packing 和 Qwen2 输入。

---

## 阶段 8：代码追踪与性能剖析

**预计用时**：4-5 天  
**阶段目标**：把“知道架构”升级为“知道成本在哪里”。

### 参考资料与具体范围

| 优先级 | 官方资料 | 具体内容 | 本阶段产物 |
| --- | --- | --- | --- |
| 必读 | [PyTorch Profiler Recipe](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html) | Profiler activities、record_shapes、profile_memory、schedule、key_averages | 一份 vision / prefill / decode operator 表 |
| 必读 | [torch.cuda.Event API](https://docs.pytorch.org/docs/stable/generated/torch.cuda.Event.html) | enable_timing、record、elapsed_time、synchronize | 稳定的分段 GPU latency |
| 必读 | [PyTorch CUDA Memory Management](https://docs.pytorch.org/docs/stable/notes/cuda.html#memory-management) | memory_allocated、memory_reserved、peak stats、caching allocator | 峰值显存记录 |
| 课程 | [CS336 Lecture 2](https://cs336.stanford.edu/lectures/?trace=lecture_02) | dtype / tensor memory、FLOPs、FLOP/s、MFU、arithmetic intensity、roofline、gradient accumulation、activation checkpointing | 为每个 compression position 写理论成本 |
| 课程 | [CS336 Assignment 2](https://github.com/stanford-cs336/assignment2-systems) | §2 Profiling and Benchmarking；§4.1 PyTorch Attention Benchmarking | 复用 benchmark 方法，不要求做完整分布式部分 |
| 课程 | [CS336 Lecture 10](https://cs336.stanford.edu/lectures/?trace=lecture_10) | Prefill / generation、KV cache、latency / throughput、continuous batching、PagedAttention | 把视觉前缀映射到推理指标 |

### CS336 Assignment 2 推荐题目

官方 handout：[CS336 Assignment 2: Systems PDF](https://github.com/stanford-cs336/assignment2-systems/blob/main/cs336_assignment2_systems.pdf)

| Handout 部分 | 官方内容 | 本路线要求 |
| --- | --- | --- |
| §2.1.3 | End-to-End Benchmarking | 必做：warmup、重复测量、同步 GPU、比较不同 size |
| §2.1.4 | Nsight Systems Profiler | 选做：能读 CPU / CUDA timeline 即可 |
| §2.1.5 | Mixed Precision | 必做概念，选做实验 |
| §2.1.6 | Profiling Memory | 必做：peak memory 与 allocator 统计 |
| §4.1 | Benchmarking PyTorch Attention | 必做：改变 sequence length，记录 forward latency |
| §4.2 | torch.compile 与 FlashAttention-2 | 选做：理解 kernel fusion 和 tiled attention |
| §5-8 | DDP、optimizer sharding、FSDP、parallelism | 当前跳过 |

> [!note] 作业适配
> CS336 A2 原作业主要围绕训练模型、forward + backward 和多 GPU 系统。本路线只复用其 profiling、memory 和 attention benchmark 方法，并把测量对象替换成 OneVision inference。

### 必测指标

对于标准 multi-head self-attention，忽略 GQA / MQA 时：

$$
\#\mathrm{KV}\approx 2LBHNd_h
$$

其中 $L$ 为 LLM 层数，$B$ 为 batch size，$H$ 为 KV heads 数，$N$ 为已缓存序列长度，$d_h$ 为 head dimension。估算显存时还要乘 dtype 字节数，并考虑 padding、batching 和 allocator。

- [ ] **Token**：记录每个关键节点的 $N$。
- [ ] **Latency**：分别记录 preprocess、vision tower、pooling / projector、LLM prefill 和 decode。
- [ ] **Memory**：记录峰值显存、prefill 前后分配和 KV cache 估算。
- [ ] **Theoretical cost**：粗算 attention 与 MLP 随 $N$ 的变化趋势。

### 实验矩阵

| 变量 | 建议档位 | 重点观察 |
| --- | --- | --- |
| Frames $T$ | 4 / 8 / 16 / 32 | Vision 成本如何随 $T$ 增长 |
| Tokens / frame | 原始 / $1/2$ / $1/4$ | Prefill 如何变化 |
| Text length | 短 / 中 / 长 | 视觉 token 在总 context 中的占比 |
| Compression position | Frame / post-vision / mid-ViT | 各自节省哪一段 |
| Batch | 1 / 2（显存允许时） | 吞吐与峰值显存 |

### 工具顺序

- [ ] 使用 torch.cuda.Event + synchronize 获得可信 GPU latency。
- [ ] 使用 torch.profiler 分析 operator 和 CUDA kernel 时间。
- [ ] 使用 forward hooks 记录真实 shape。
- [ ] 使用 memory_allocated / max_memory_allocated 粗测显存。
- [ ] 需要分析 kernel 与 memory bandwidth 时，再使用 Nsight Systems / Compute。

> [!warning] 测量原则
> 不要只报告总推理时间。至少分开 vision encoder、LLM prefill 和 decode，否则无法判断压缩机制影响了哪一段。

> [!success] 阶段验收
> - [ ] 在相同输入和硬件条件下，得到可重复的 latency breakdown。
> - [ ] 能解释理论 token reduction 与实际端到端加速不一致的原因。

---

## 阶段 9：视频压缩知识地图

**阶段目标**：按压缩发生的位置理解论文，而不是按方法名称记忆。

### 建议论文与阅读顺序

| 压缩位置 | 论文 | 精读内容 | 要回答的问题 |
| --- | --- | --- | --- |
| ViT 中间层：pruning | [DynamicViT](https://arxiv.org/abs/2106.02034) | Token sparsification module、stage-wise pruning、训练目标 | 动态选择发生在哪些 block？是否真正减少后续 ViT 计算？ |
| ViT 中间层：merging | [Token Merging: Your ViT But Faster](https://arxiv.org/abs/2210.09461) | Bipartite soft matching、proportional attention、training-free 应用 | Merge 与 delete 的信息损失有何不同？ |
| LMM 中后层：pruning | [FastV](https://arxiv.org/abs/2403.06764) | Layer 2 之后的 visual token pruning、attention-based selection | 为什么发生在 LLM layer 2 后？省的是 vision 还是 LLM？ |
| Vision 输出：merge | [LLaVA-PruMerge](https://arxiv.org/abs/2403.15388) | Adaptive token reduction、重要 token 与相似 token merging | 选择与合并依据是什么？是否需要训练？ |
| 长视频：时空压缩 | [LongVU](https://arxiv.org/abs/2410.17434) | Temporal redundancy、spatial token reduction、adaptive compression | Frame 与 patch 两级压缩如何配合？ |
| 固定 bottleneck | [BLIP-2](https://arxiv.org/abs/2301.12597) | Q-Former §3.1-3.3 | Learned resampling 与 training-free pruning 如何公平比较？ |

### 阅读顺序

- [ ] 先读 DynamicViT 和 ToMe，建立 prune 与 merge 的差别。
- [ ] 再读 FastV 和 LLaVA-PruMerge，定位 LMM 中实际压缩位置。
- [ ] 最后读 LongVU，把空间 token 压缩扩展到时间维。
- [ ] 每篇论文都填写下方八个固定问题，不只记录 benchmark 数字。

| 位置 | 典型操作 | 主要节省 | 能否节省 Vision Encoder | 核心问题 |
| --- | --- | --- | --- | --- |
| 视频输入前 | Frame / keyframe selection | Vision + LLM | 是 | 哪些帧包含证据？ |
| 像素级 | Resize / crop / adaptive resolution | Vision + LLM | 是 | 哪些区域值得高分辨率？ |
| ViT 输入 | Patch selection | Vision + LLM | 是 | 能否在编码前估计重要性？ |
| ViT 中间层 | Token prune / merge | 后续 ViT + LLM | 是 | 如何用中间语义动态压缩？ |
| Vision 输出 | Visual token pruning | Projector + LLM | 否 | 如何保留语义证据？ |
| Resampler | Latent queries / pooling | 主要为 LLM | 通常否 | 固定预算如何聚合信息？ |
| Projector 后 | LLM-space token pruning | 主要为 LLM | 否 | 能否利用 LLM-compatible features？ |
| LLM 内部 | KV / attention sparsity | LLM | 否 | 对推理后端的侵入有多大？ |

### 阅读每篇压缩论文时固定回答

- [ ] 压缩发生在哪个位置？
- [ ] 压缩前后 $N$ 分别是多少？
- [ ] 方法是否需要训练？训练哪些参数？
- [ ] 方法是否使用 query、answer 或 label？
- [ ] 它节省 vision encoder、LLM prefill、KV cache 中的哪些部分？
- [ ] 选择依据是 global frame feature、patch token、attention 还是 LLM hidden state？
- [ ] 它是否改变 token 语义或位置编码？
- [ ] 比较是否在相同 token / FLOPs / resolution budget 下进行？

> [!important] 研究判断
> 看到“减少 80% visual tokens”时，先确认压缩发生在 encoder 前还是后，再分析 vision tower 占比、prefill / decode 比例，以及 kernel、padding 和 batch 效应。Token 减少 80% 不等于端到端时间减少 80%。

---

## 阶段 10：推理系统基础

### 李宏毅 Machine Learning 2026 Spring

**课程官网**：[Machine Learning 2026 Spring](https://speech.ee.ntu.edu.tw/~hylee/ml/2026-spring.php)  
**核验范围**：官网 Content 表、Homework 表、讲义 PDF、作业 PDF 和公开 Colab。

#### 与本路线直接相关的课程

| 日期 | 官网课题 | 官方材料 | 需要掌握 |
| --- | --- | --- | --- |
| 2026-03-20 | 深入模型内部架构：如何加快模型推论速度 | [FlashAttention 视频](https://youtu.be/vXb2QYOUzl4) · [KV Cache 视频](https://youtu.be/fDQaadKysSA) · [PDF](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/inference.pdf) · [PPTX](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/inference.pptx) | Standard attention 的 HBM 读写、FlashAttention tiling、prefill / decode、KV cache |
| 2026-03-27 | 深入模型内部架构：模型如何处理超长输入 | [Positional Embedding 视频](https://youtu.be/Ll-wk8x3G_g) · [PDF](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/pos.pdf) · [PPTX](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/pos.pptx) | Absolute / relative position、RoPE 直觉、长 context 的位置问题 |

- [ ] 看完 3/20 两段视频，并用自己的话解释“FlashAttention 不改变 exact attention 结果，主要减少 HBM I/O”。
- [ ] 看完 3/27 Positional Embedding，并说明视觉长前缀为什么会影响 position 和 context。

#### HW3：LLM Fast Inference（必做）

**官方材料**：[作业说明视频](https://youtu.be/rXfp9Yo5HwU) · [HW3 PDF](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/hw3.pdf) · [官方 Colab](https://colab.research.google.com/drive/1vZNo6_PlaP2fvMqr3g5KoQA0rN79m24O?usp=sharing)

> [!info] 官网核验结果
> HW3 共 20 道选择题，每题 0.5 分：Q1-Q10 为论文阅读，Q11-Q20 为填补 Colab 中 TODO 后分析实验。作业说明要求先看 [2025 第 3 讲：解剖大型语言模型](https://www.youtube.com/watch?v=8iFvM7WUUs8)，提交入口是 NTU COOL；自学者可直接使用公开 PDF 和 Colab。

**Q1-Q10 论文阅读**

| 主题 | 官方指定论文 |
| --- | --- |
| Speculative Decoding | [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) |
| Speculative Sampling | [Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318) |
| Reference-based Decoding | [Inference with Reference: Lossless Acceleration of Large Language Models](https://arxiv.org/abs/2304.04487) |
| Tree Verification | [SpecInfer: Accelerating Generative LLM Serving with Tree-based Speculative Inference and Verification](https://arxiv.org/abs/2305.09781) |
| FlashAttention | [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) |
| FlashAttention-2 | [Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) |
| FlashAttention-3 | [Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) |

**Q11-Q20 代码与分析**

- Manual speculative decoding：补全 probability correction，比较 prompt、acceptance rate 和 $\gamma$。
- FlashAttention：比较 standard / tiled attention 的 HBM read-write 数量和理论速度。
- KV Cache：运行 multi-turn prefix reuse 和 cache invalidation 实验。
- vLLM / PagedAttention：理解 block-based KV memory management。
- Weight offloading：分析参数搬运为何拖慢逐 token generation。

- [ ] 完成 Q1-Q10 对应论文定位，至少写出每题证据所在章节。
- [ ] 跑通 Colab 的 Q11-Q20，并保存关键输出。
- [ ] 把 KV Cache 与 FlashAttention 实验结果连接到 OneVision 的视觉前缀。

#### HW4：Training Transformers（选做）

**官方材料**：[作业说明视频](https://youtu.be/QrqdoGf35Iw) · [HW4 PDF](https://speech.ee.ntu.edu.tw/~hylee/ml/ml2026-course-data/hw4.pdf) · [官方 Colab](https://colab.research.google.com/drive/1G9CgvnhqQ5AwHc6nbVzVGCoe-xUXdSWB?usp=sharing) · [Kaggle Notebook](https://www.kaggle.com/code/stevenlunar/ml2026-spring-hw4-training-transformer)

| 项目 | 官网作业内容 |
| --- | --- |
| Task | 训练 decoder-only Transformer 做 next-token prediction |
| Data | 792 张 $20\times20$ Pokémon 小图，每个 pixel 是 token，共 167 个颜色类别 |
| Split | Train 632 / Validation 80 / Test 80 |
| Test | 给定图像前 60%，生成剩余部分 |
| Metric | FID + Pokémon Detection Rate |
| Baseline | GPT-2 simple；调 epoch / LR / heads / embedding 的 medium；Llama / Mistral strong |

- [ ] PyTorch 训练不熟时完成 simple baseline。
- [ ] 修改 heads、embedding dimension 和 layers，记录质量与成本变化。
- [ ] 不把 HW4 当作 OneVision 训练前置；它只用于巩固 decoder-only next-token prediction。

### CS336 Spring 2026 官方核验与详细范围

**课程官网**：[CS336: Language Modeling from Scratch, Spring 2026](https://cs336.stanford.edu/)  
**官方材料仓库**：[stanford-cs336/lectures](https://github.com/stanford-cs336/lectures)

> [!warning] 课程前置与版本
> 官网要求熟练 Python / software engineering、PyTorch、deep learning 和 memory hierarchy，并明确说明作业代码量很大、scaffolding 很少。另一个版本细节是：Spring 2026 官网目前链接的 Assignment 1 官方仓库，其 README 和 handout 标题仍写 **Spring 2025**；A2 和 A5 已明确标为 Spring 2026。本路线按官网当前链接使用，不擅自改写版本。

#### 课程内容

| Lecture / 日期 | 官网标题与材料 | 详细学习范围 | 优先级 |
| --- | --- | --- | --- |
| L1 / 03-30 | [Overview, Tokenization](https://cs336.stanford.edu/lectures/?trace=lecture_01) | 课程全景、Unicode、BPE、tokenizer | 选看 |
| L2 / 04-01 | [PyTorch, Resource Accounting](https://cs336.stanford.edu/lectures/?trace=lecture_02) | einops / einsum、dtype memory、FLOPs / FLOP/s / MFU、arithmetic intensity、roofline、训练 memory、gradient accumulation、activation checkpointing | 必读 |
| L3 / 04-06 | [Architectures, Hyperparameters](https://github.com/stanford-cs336/lectures/blob/main/lecture_03.pdf) | Pre-Norm Transformer、RMSNorm、RoPE、SwiGLU、head / hidden / MLP dimension、参数与计算量 | 必读 |
| L4 / 04-08 | [Attention Alternatives and Mixture of Experts](https://github.com/stanford-cs336/lectures/blob/main/lecture_04.pdf) | Sparse / linear attention、SSM、MoE；建立替代架构地图 | 选看 |
| L5 / 04-13 | [GPUs, TPUs](https://github.com/stanford-cs336/lectures/blob/main/lecture_05.pdf) | GPU memory hierarchy、Tensor Cores、并行执行与性能上限 | 必读 |
| L6 / 04-15 | [Kernels, Triton](https://cs336.stanford.edu/lectures/?trace=lecture_06) | Kernel launch、memory coalescing、tiling、fusion、Triton 编程 | 先看概念，代码选做 |
| L10 / 04-29 | [Inference](https://cs336.stanford.edu/lectures/?trace=lecture_10) | TTFT / latency / throughput、prefill vs generation、KV cache、GQA / MLA / CLA、quantization、pruning / distillation、speculative sampling、continuous batching、PagedAttention | 必读 |
| L17 / 05-27 | [Alignment - Multimodality](https://cs336.stanford.edu/lectures/?trace=lecture_17) | ViT、CLIP、SigLIP、LLaVA、LLaVA-OneVision、AnyRes、Qwen-VL、统一离散视觉 token | 必读并作为阶段 2-7 总复习 |

#### Lecture 10 必须完成的推导

- [ ] 区分 TTFT、single-request latency 和 multi-request throughput。
- [ ] 推导为什么 prefill 较易 compute-bound，而逐 token generation 常 memory-bound。
- [ ] 写出 KV cache 对 batch、sequence、layers、KV heads 和 head dimension 的依赖。
- [ ] 解释 GQA、MLA、CLA 和 local attention 如何减少 KV cache。
- [ ] 区分 lossy shortcut（quantization / pruning）与 lossless speculative sampling。
- [ ] 解释 continuous batching 和 PagedAttention 分别解决什么 serving 问题。

#### Lecture 17 必须完成的复盘

- [ ] 复述 image → patch tokens → global / local representation。
- [ ] 比较 CLIP softmax objective 与 SigLIP sigmoid objective。
- [ ] 复述 LLaVA 的 CLIP + projection + LLM 两阶段训练。
- [ ] 复述 OneVision 的 SigLIP、AnyRes、single / multi-image / video token strategy。
- [ ] 对照课程代码中的 OneVision 描述与自己的真实 forward trace。

#### CS336 官方作业全表

| 作业 | 官网描述 | 本路线处理 |
| --- | --- | --- |
| [A1 Basics](https://github.com/stanford-cs336/assignment1-basics) | 实现 BPE tokenizer、Transformer architecture、optimizer、training loop，训练一个最小 LM | 只做 §3 Transformer Architecture 与 transformer resource accounting；训练部分选做 |
| [A2 Systems](https://github.com/stanford-cs336/assignment2-systems) | Profiling / benchmarking、mixed precision、memory、Triton FlashAttention-2、DDP、optimizer sharding、FSDP、parallelism | §2 与 attention benchmark 必读；分布式部分当前跳过 |
| [A3 Scaling](https://github.com/stanford-cs336/assignment3-scaling) | 理解 Transformer 组件并调用 training API 拟合 scaling law | 当前跳过 |
| [A4 Data](https://github.com/stanford-cs336/assignment4-data) | Common Crawl 清洗、filtering、deduplication | 当前跳过 |
| [A5 Alignment and Reasoning RL](https://github.com/stanford-cs336/assignment5-alignment) | SFT + RL 训练数学推理，optional safety / DPO | 当前跳过 |

#### Assignment 1 推荐子集

官方 handout：[Assignment 1: Basics PDF](https://github.com/stanford-cs336/assignment1-basics/blob/main/cs336_assignment1_basics.pdf)

- [ ] §3.3：实现 Linear 与 Embedding。
- [ ] §3.4：实现 RMSNorm、position-wise FFN、RoPE、softmax、scaled dot-product attention 和 causal multi-head self-attention。
- [ ] §3.5：实现 Transformer block、完整 Transformer LM，并完成 resource accounting。
- [ ] §4-7 训练、生成和 ablation 仅在需要更强训练直觉时完成。

#### 学习顺序

**第一次：OneVision 之前或同时**

- [ ] L2 Resource Accounting。
- [ ] L3 Architectures / Hyperparameters。
- [ ] A1 §3 Transformer Architecture 子集。
- [ ] L17 的 ViT / CLIP / SigLIP / LLaVA / OneVision。

**第二次：OneVision trace 完成之后**

- [ ] L5 GPUs / TPUs。
- [ ] L6 Kernels / Triton 概念。
- [ ] L10 Inference。
- [ ] A2 §2 Profiling and Benchmarking + §4.1 Attention Benchmarking。

> [!note] 当前可以跳过
> L7-L9 parallelism / scaling laws、L11 scaling laws、L12 evaluation、L13-L14 data、L15-L16 post-training，以及 A2 的 DDP / FSDP 部分。只有研究开始触及训练扩展或在线 serving 时再补。

---

## 10 周执行计划

默认每周学习 6 天，每天 2.5-3 小时；第 7 天休息或补缺。完成标准是通过阶段验收，不是看完指定页数。

| 周次 | 主题 | 主要任务 | 周末产物 |
| --- | --- | --- | --- |
| W1 | Transformer | NN basics、RNN 动机、Transformer、A3 核心 | Attention 实现 + shape cheat sheet |
| W2 | ViT | Patchify、ViT blocks、hidden states、token count | ViT forward trace |
| W3 | CLIP | 双塔、contrastive、global vs patch | Frame scorer + patch feature 笔记 |
| W4 | SigLIP | Sigmoid objective、vision tower、CLIP 对照 | CLIP / SigLIP 对比表 |
| W5 | BLIP / BLIP-2 | ITC / ITM / LM、Q-Former、cross-attention | Q-Former bottleneck trace |
| W6 | LLaVA | Vision → projector → LLM、causal prefix | 单图端到端 trace |
| W7 | OneVision I | 论文主干、video preprocessing、vision tower | Video token flow 图 |
| W8 | OneVision II | LLM input、prefill / KV、完整 trace | 端到端 profiler 表 |
| W9 | Compression | Frame / patch / token / resampler 分类与实验 | 两个压缩位置的对照实验 |
| W10 | Systems | 李宏毅 inference + CS336 精选内容 | Capstone 报告 + 研究问题 |

### 每天 3 小时模板

| 时间 | 内容 |
| --- | --- |
| 00:00-00:45 | 课程 / 论文：只看当天核心 |
| 00:45-01:45 | 源码 / Notebook：将概念对应到真实 tensor |
| 01:45-02:30 | 实验：shape、hook、profiler 或小改动 |
| 02:30-03:00 | 总结：回答“在哪里压缩、能节省什么” |

### 进度记录

- [ ] W1：完成 Transformer 阶段验收与产物。
- [ ] W2：完成 ViT 阶段验收与产物。
- [ ] W3：完成 CLIP 阶段验收与产物。
- [ ] W4：完成 SigLIP 阶段验收与产物。
- [ ] W5：完成 BLIP / BLIP-2 阶段验收与产物。
- [ ] W6：完成 LLaVA 阶段验收与产物。
- [ ] W7：完成 OneVision 视频路径与 preprocessing trace。
- [ ] W8：完成 OneVision 端到端 trace 和 profiling。
- [ ] W9：完成两个压缩位置的对照实验。
- [ ] W10：完成系统课程精选内容与 Capstone。

> [!example]- 其他节奏
> **6 周压缩版**：Transformer + ViT / CLIP + SigLIP / BLIP-2 / LLaVA + OneVision 论文 / OneVision trace + profiling / Compression + inference。仅适合每天投入 4-5 小时且 PyTorch 基础较熟的情况。
>
> **14 周稳健版**：为前 8 周的每个阶段增加 2-3 天代码阅读与复盘，并在系统部分增加 GPU、kernel 和 FlashAttention 实践。

---

## 阶段验收清单

### Transformer

- [ ] 为什么 $QK^\top$ 是 $N\times N$？
- [ ] Causal mask 屏蔽哪一部分？
- [ ] MLP 为什么通常不在 token 维进行 mixing？
- [ ] $N$ 减半后，attention 与 MLP 的理论计算量分别如何变化？

### ViT

- [ ] $224\times224$、patch size 为 16 时有多少 patch？
- [ ] CLS / global representation 与 patch hidden states 有什么区别？
- [ ] 在哪一层 prune 才能节省后续 vision blocks？

### CLIP 与 SigLIP

- [ ] Image-text similarity 由哪两个向量计算？
- [ ] 为什么 global frame score 不等于 patch importance？
- [ ] Logit scale 有什么作用？
- [ ] SigLIP 与 CLIP 最关键的 loss 差别是什么？

### BLIP 与 BLIP-2

- [ ] ITC 与 ITM 的 scorer 含义为什么不同？
- [ ] Q-Former 的 Q / K / V 分别来自哪里？
- [ ] 固定 query 数为什么是一种信息瓶颈？

### LLaVA 与 OneVision

- [ ] Projector 通常改变 $D$ 还是 $N$？
- [ ] Visual embeddings 如何进入 decoder-only LLM？
- [ ] Post-vision pruning 能否节省 vision encoder？
- [ ] 一帧从 pixels 到 LLM prefix 经历哪些变换？
- [ ] Video token 数由哪些因素决定？
- [ ] Frame compression 与 token compression 的节省路径有何不同？

### Systems

- [ ] Prefill 和 decode 有什么区别？
- [ ] KV cache 保存什么？
- [ ] FlashAttention 为什么不能简单理解为“减少 attention FLOPs”？

---

## 研究型 Capstone

**输入建议**：一个 30-60 秒且事件变化明显的视频。  
**目标**：证明自己能够对模型内部进行可解释、可测量的干预，而不是刷 benchmark。

### A. Baseline Trace

- [ ] 固定 frame 数和分辨率。
- [ ] 记录每个 stage 的 $N$、$D$、dtype 和 device。
- [ ] 分别测量 vision、projector、prefill 和 decode latency。
- [ ] 测量 peak memory 并估算 KV cache。
- [ ] 保存 baseline answer。

### B. Frame-level Compression

- [ ] 将 uniform sampling 从 $T$ 减到 $T/2$，或用 CLIP / SigLIP relevance 选择 Top-k。
- [ ] 重新测量 vision 与 LLM latency。
- [ ] 解释为什么它理论上同时减少 vision 和 LLM 输入成本。

### C. Post-vision Token Compression

- [ ] 对每帧 visual tokens 使用 pooling、similarity Top-k 或 uniform spatial subsampling。
- [ ] 保持 frame 数不变。
- [ ] 验证 vision encoder 时间基本不因 post-vision pruning 本身下降。
- [ ] 观察 LLM prefill 和显存变化。

### D. Mid-ViT Compression（可选）

- [ ] 在某个中间 block 后插入 token selection 或 merging。
- [ ] 确认 position 和 special token 处理正确。
- [ ] 与 post-vision 方法在相同 token budget 下比较端到端速度。

### 最终交付

- [ ] 一张完整 data flow + shape 图。
- [ ] 一张 token count vs stage 图。
- [ ] 一张压缩前后的 latency breakdown 图。
- [ ] 一张 answer quality vs token budget 图。
- [ ] 一页结论：什么位置最值得压缩，测量证据是什么？

> [!success] Capstone 完成标准
> 你能够定位模型内部效率瓶颈、实施干预，并区分理论节省与真实端到端收益。此后可以用同一坐标系阅读 visual token pruning、merging、adaptive resolution 和 KV compression 论文。

---

## 暂缓学习的内容

### 当前不要做

- 完整刷完 CS224N 后才开始 ViT。
- 完整刷完 CS336 后才接触 LLaVA。
- 一开始就复现 BLIP-2 / OneVision 的大规模训练。
- 花大量时间背 RNN / LSTM 门结构。
- 把每篇压缩论文当作孤立技巧记忆。
- 只看论文框图，不记录真实 tensor shape。
- 只报告 token reduction ratio，不测压缩位置与端到端 latency。

### 以后按需补充

- RoPE、YaRN 和 long-context extrapolation。
- FlashAttention kernel 与 Triton 实现。
- GQA、MQA、paged KV cache 和 continuous batching。
- Quantization。
- Tensor / Sequence / Context Parallelism。
- 训练型 token selector 与 RL-based compression。
- LLaVA-OneVision-1.5 / OneVision-2 等后续架构。

> [!tip] 优先级判断
> 如果一个知识点不能帮助回答“token 在哪里、shape 是什么、计算发生在哪里、压缩能省什么”，当前优先级就可以降低。

---

## 参考资料

以下优先使用官方课程页和原始论文。课程页面可能更新；本路线按 2026-08-15 可访问的资料整理。

### R1

[Stanford CS224N, Winter 2026 - Course Schedule & Assignments](https://web.stanford.edu/class/cs224n/)

> NN basics、LM / RNN、Transformers；Assignment 3 为 Self-Attention and Transformers。

### R2

[CS224N 2026 Assignment 3: Self-Attention and Transformers](https://web.stanford.edu/class/cs224n/assignments_w26/a3.pdf)

> 用于 self-attention、positional properties 和 Transformer 的理论与编程练习。

### R3

[An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929)

> ViT 原始论文；重点阅读 patch embedding 和 Transformer encoder。

### R4

[Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)

> CLIP 双编码器和图文对比学习。

### R5

[Sigmoid Loss for Language Image Pre-Training](https://arxiv.org/abs/2303.15343)

> Pairwise sigmoid loss 和 language-image pre-training。

### R6

[BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation](https://arxiv.org/abs/2201.12086)

> ITC / ITM / LM 与统一理解、生成框架。

### R7

[BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models](https://arxiv.org/abs/2301.12597)

> Q-Former、固定 query output 和 information bottleneck。

### R8

[Visual Instruction Tuning](https://arxiv.org/abs/2304.08485)

> LLaVA 的视觉 instruction-tuning 范式。

### R9

[LLaVA-OneVision: Easy Visual Task Transfer](https://arxiv.org/abs/2408.03326)

> Qwen2 + SigLIP + 两层 MLP；覆盖 single-image、multi-image 和 video。

### R10

[李宏毅 Machine Learning 2026 Spring](https://speech.ee.ntu.edu.tw/~hylee/ml/2026-spring.php)

> FlashAttention、KV Cache、Positional Embedding 和 Fast Inference。

### R11

[Stanford CS336: Language Modeling from Scratch, Spring 2026](https://cs336.stanford.edu/)

> Resource accounting、architecture、GPU、Triton、inference 和 multimodality。

### R12

[LLaVA-OneVision-2: Towards Next-Generation Perceptual Intelligence](https://arxiv.org/abs/2605.25979)

> 完成原始 OneVision 后的可选演进阅读，包含新的 video tokenization 和 efficiency 设计。

---

> [!quote] 路线完成后的下一步
> 不要立即再学一门完整课程。选择 3-5 篇 visual-token / video-compression 论文，用同一套 OneVision profiler 复现它们的压缩位置、token budget、answer quality 和真实 latency。
