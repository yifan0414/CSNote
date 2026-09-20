---
title: "BLIP-2：用Q-Former连接冻结视觉编码器与大语言模型"
authors: ["Junnan Li", "Dongxu Li", "Silvio Savarese", "Steven Hoi"]
conference: "ICML"
year: 2023
arxiv_url: "https://arxiv.org/abs/2301.12597"
pdf_link: "[[07-MultiModal/Video-MLLM/assets/paper_2301.12597.pdf]]"
cover: "[[_assets/images/BLIP-2-2301.12597-01-qformer-attention-masks.png]]"
created: 2026-09-12
updated: 2026-09-15
tags: ["paper/arxiv", "vlm", "image-text", "pretraining"]
status: "unread"
priority:
rating:
topics: ["MLLM"]
code: "https://github.com/salesforce/LAVIS/tree/main/projects/blip2"
---

![[_assets/images/blip-2-01-qformer-two-stage-framework.drawio.svg|900]]

<!-- READ_PAPER_GENERATED_START -->

> **BLIP-2 先冻结视觉骨干，训练 Q-Former 从图像中读取与语言有关的信息；再把这些信息投影成连续视觉提示，接入冻结 LLM，用生成损失继续训练中间的连接模块。**

前置阅读：[[05-BLIP：从图文对齐到理解、生成与数据自举|BLIP：从图文对齐到理解、生成与数据自举]]。如果刚从 CLIP 过来，也可以先回看 [[01-CLIP：从图文配对到共享语义空间|CLIP 笔记]]。

本文沿着一条主线展开：**为什么换架构 → 配对数据提供什么监督 → query 怎样读图 → ITC / ITM / ITG 怎样训练它 → 如何接入 LLM → 冻结时梯度怎样回传 → 数据准备与下游使用。**

| 读这一篇，要解决什么问题？ | 先给一句话答案 |
| --- | --- |
| 为什么不直接沿用 BLIP？ | 希望复用现成视觉模型和大语言模型，而不是重新训练两个大模块 |
| Q-Former 到底是什么？ | 用可学习查询向量读取视觉特征的可训练 Transformer 模块 |
| 为什么分两个阶段？ | 先学会提取语言相关视觉信息，再适配特定冻结 LLM 的输入空间 |
| 谁提供训练答案？ | 图文配对关系与真实配对文本，而不是让 LLM 自己出伪标签 |
| 冻结两端后还有谁在学？ | Queries、Q-Former 有效分支和相应投影等适配参数 |

以下讨论原始 **BLIP-2**，不是后续 InstructBLIP 等扩展。狗图片、展开公式和类比用于解释机制；实验数字与实现差异另附来源。文中“冻结两端”默认指**两阶段预训练**，不默认适用于所有下游微调。

## 1. 从 BLIP 出发：为什么要换成“冻结两端，中间接桥”？

### 1.1 不是原来的任务消失了，而是想复用更强的现成模型

在 BLIP 中，我们训练一套 MED：能对齐、能匹配、能生成，在线视觉编码器也跟着三个任务学习。

BLIP-2 问的是另一个问题：

> 已经有会提取视觉特征的 ViT，也有会处理和生成语言的 LLM，能不能保留它们的能力，只训练中间的连接部分？

难点是：**图像特征不是 LLM 天然理解的文本输入。** 即使线性层把向量维度改对，也不等于 LLM 已经学会把这组数值解释为“狗在草地上跑”。

> [!example] 设计的因果链
> 想复用已有视觉与语言能力 → 冻结大型骨干 → 两端表示空间仍不匹配 → 增加可训练桥接模块 → 先训练它取出有用信息，再训练它把信息传给 LLM。
>
> BLIP-2 选择的桥接模块是 **Q-Former（Querying Transformer）**。这是一种设计，不是说任何只用线性投影的连接方式都必然无效。

### 1.2 同一对图文，仍然可以提供多种监督

还是这对数据：

- 图片 $I_1$：狗在草地上跑。
- 描述 $T_1$：`a dog running on grass`。

对包含 $B$ 对图文的 batch：

$$
\mathcal{B}=\{(I_i,T_i)\}_{i=1}^{B},
\qquad T_i=(t_{i,1},\dots,t_{i,L_i}).
$$

| 训练任务 | 要回答什么？ | 答案从哪里来？ |
| --- | --- | --- |
| 第一阶段 ITC：对齐 | 候选中哪个是配对对象？ | 图文配对关系 |
| 第一阶段 ITM：匹配 | 当前这对是否匹配？ | 原始配对与采样错配 |
| 第一阶段 ITG：图像条件文本生成 | 看图后，下一个 token 是什么？ | 配对描述的真实下一 token |
| 第二阶段 LLM 生成 | 接收视觉提示后，应该生成什么文本？ | 真实配对文本或其后缀 |

**不需要为这些目标分别人工标注不同的数据集。** 但数据中仍包含 COCO、Visual Genome 等人工标注来源；“配对文本可以自动构造目标”不等于“完全没有人工监督”。

### 1.3 先分清两个阶段：谁负责生成，发生了变化

| | 第一阶段：表征学习 | 第二阶段：生成接口学习 |
| --- | --- | --- |
| 图像由谁提取？ | 冻结视觉骨干 | 同样使用冻结视觉骨干 |
| 中间谁在学习？ | Q-Former 与 queries、任务输出模块 | 第一阶段的 Q-Former 继续训练，新增到 LLM 的投影 |
| 文本生成发生在哪里？ | Q-Former 自己的文本分支 | 外部冻结 LLM |
| 训练目标 | ITC + ITM + ITG 联合优化 | 对应 LLM 的文本生成目标 |

> [!warning] 不是把四个 loss 从头到尾一起相加
> **第一阶段内部**，三个任务共同训练 Q-Former；**第一阶段结束后**，再接入 LLM 做第二阶段。
>
> 可以先记成：第一阶段练“取什么”，第二阶段练“怎样传给 LLM”。两者都会改变视觉接口，这不是把信息选择与表达完全分开的数学保证。

## 2. Q-Former：可学习 queries 怎样从图片里读取信息？

### 2.1 先看视觉骨干：提供一串特征，不只提供一个 CLS

视觉编码器输出：

$$
H^I=E_{\theta_v}(I)\in\mathbb{R}^{P\times d_v}.
$$

其中 $P$ 是视觉 token 数量，$d_v$ 是每个 token 的特征维度，$\theta_v$ 是预训练期间保持固定的视觉骨干参数。

论文使用 CLIP ViT-L/14 或 EVA-CLIP ViT-g/14，并采用倒数第二层输出。

> [!info] 这两个视觉骨干是什么？先拆名字，再看区别
> **ViT（Vision Transformer）**把图片切成 patches，再用 Transformer 编码。`L` 表示 Large，`g` 表示 giant 级别的更大配置；`/14` 表示每个 patch 为 $14\times14$ 像素，**不是网络只有 $14$ 层，也不是一张图片只有 $14$ 个 patch**。
>
> | 名称 | 预训练来源与主要区别 | 这里提供的视觉特征维度 |
> | --- | --- | --- |
> | **CLIP ViT-L/14** | 原始 CLIP 的 Large 视觉塔，通过图文对比学习获得与文本相关的视觉表示 | $d_v=1{,}024$ |
> | **EVA-CLIP ViT-g/14** | 更大的视觉塔：先用 EVA 的掩码视觉学习初始化，再做 CLIP 式图文对比训练；不是只把原始 CLIP 改个名字 | $d_v=1{,}408$ |
>
> EVA 的掩码学习可以理解为：**遮住部分图像 patches，根据可见部分预测被遮住位置的 CLIP 视觉特征**，而不是直接恢复原始像素。这样先学好视觉表示，再用于初始化更大的 CLIP 视觉塔。[EVA 原论文](https://arxiv.org/abs/2211.07636)
>
> **在 BLIP-2 里，两者是二选一的预训练视觉骨干，不是串联使用，也不把它们原来的 CLIP 文本塔一起接进来。** 两者 patch 大小相同，但模型容量、特征宽度和预训练方式不同；Q-Former 负责从它们输出的视觉 token 中读取信息。维度参见 [CLIP 官方配置](https://huggingface.co/openai/clip-vit-large-patch14/blob/main/config.json)与 [LAVIS 的 EVA 视觉骨干实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/eva_vit.py)。
>
> 例如，$224\times224$ 的图片按 $14\times14$ 切块，得到 $16\times16=256$ 个 patch token，加上一个 CLS，就是下面公式里的 $257$ 个视觉 token；$1{,}024$ 则是 ViT-L 的特征宽度，**不是最终 CLIP 对比空间的投影维度**。

以论文的 ViT-L/14 示例为例：

$$
H^I\in\mathbb{R}^{257\times1024}.
$$

这串视觉 token 供 Q-Former 读取。它不需要把图片先转成文字，也不需要先把所有视觉 token 平均成一个全局向量。

### 2.2 Learnable queries：先把它理解成一组可训练的“读取位置”

Q-Former 不直接要求每个文本位置去读图，而是先准备一组向量，用它们读取视觉特征：

$$
Q_0\in\mathbb{R}^{N_q\times d_q}.
$$

论文设置 $N_q=32$、$d_q=768$。先别被名字绕住：

| 常见疑问 | 正确理解 |
| --- | --- |
| Query 是用户问的自然语言问题吗？ | 不是，这里首先指模型内部可学习的向量 |
| 每张图片有一套单独的 query 参数吗？ | 不是，不同图片使用同一组初始 query embeddings |
| 每个 query 固定对应一个 patch 吗？ | 不是，每个 query 可以对视觉序列分配读取权重 |
| 同一组 query 会让所有图片输出相同吗？ | 不会，输入图片特征不同，交互后的输出会不同 |

可以把它们类比为“固定数量、但会通过训练学会怎样读取信息的位置”。**类比不意味着每个位置都必然拥有‘狗、草地、动作’这样的可命名分工。**

记没有候选文本条件时的 query 输出为：

$$
Z(I)=F_{\theta_q}(Q_0,H^I)\in\mathbb{R}^{N_q\times d_q}.
$$

> [!tip] 最重要的区分：参数固定使用，不等于输出固定
> $Q_0$ 是所有图片共用的可学习参数；$Z(I)$ 是这些参数经过当前图片特征计算后的输出。前者随训练更新，后者还随输入图片变化。

### 2.3 Cross-attention：query 提出读取需求，视觉 token 提供内容

Queries 之间先通过 self-attention 交换信息，再在相应层通过 cross-attention 读取图像。

设当前 query 隐状态为 $X_Q\in\mathbb{R}^{N_q\times d_q}$，省略残差、LayerNorm 与多头细节：

$$
Q=X_QW_Q,\qquad K=H^IW_K,\qquad V=H^IW_V,
$$

$$
\operatorname{CA}(X_Q,H^I)
=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V.
$$

读法与普通 attention 一样，只是来源不同：

- **Q 来自当前 query 状态**：用什么特征去查询？
- **K、V 来自图片特征**：匹配哪些视觉内容，读取哪些信息？
- 权重矩阵属于 $\mathbb{R}^{N_q\times P}$：每个 query 对整串视觉 token 分配读取权重。

这里有三个不同的“查询”概念：初始 query embeddings $Q_0$、attention 里的投影矩阵 $Q$、用户的自然语言 question。**它们不能因为名字相近就画等号。**

### 2.4 为什么只输出少量 query：把视觉信息压进短序列

论文示例中，较长的视觉序列经过 Q-Former，产生 $32$ 个输出向量：

$$
H^I\in\mathbb{R}^{257\times1024}
\quad\longrightarrow\quad
Z(I)\in\mathbb{R}^{32\times768}.
$$

这就是 **信息瓶颈（information bottleneck）** 的结构直觉：后面只能通过有限数量的向量获得图像信息，训练便需要学会选择对语言任务有用的内容。

**瓶颈由结构提供，“哪些信息有用”由训练目标塑造。** 只放一组 queries 而不训练，并不会自动知道该保留狗、动作还是背景。

输出数量固定，不表示信息无损，也不表示视觉计算量恒定。输入分辨率提高、视觉 token 增多时，视觉骨干与 Q-Former 读取这些 token 的开销仍可能增加。

### 2.5 第一阶段的文本分支在哪里？为什么需要 mask？

第一阶段还要对齐、判断匹配、生成描述，所以 Q-Former 也有文本处理路径。它来自 BERT-base 初始化，**不是第二阶段要接入的 OPT / FlanT5**。

| 交互 | 用什么实现？ |
| --- | --- |
| Query 与 query 交换信息 | Self-attention |
| Query 读取图片 | Cross-attention |
| Query 与文本交换信息 | 共享的 self-attention，是否允许由任务 mask 决定 |

Q-Former 图像侧与文本侧共享 self-attention，但不是所有子层都共享：官方实现保留 query 专用 FFN。新增视觉 cross-attention 随机初始化，每 $2$ 个 Transformer block 中有一个执行视觉读取。

> [!warning] 与 BLIP 最容易记反的地方
> 原始 BLIP 的 MED：文本通过 cross-attention 直接读视觉 token，encoder 与 decoder 的 self-attention 参数分开。
>
> BLIP-2 的 Q-Former：**query 通过 cross-attention 读图；文本经 self-attention 与 query 交互，不能直接 cross-attend 到图像。** Query 与文本共享 self-attention，用不同 mask 控制可见性。

为什么不能对所有任务都开放相同信息？因为**对齐时不能先看答案，匹配时需要一起看，生成时不能偷看未来**。接下来的三个任务分别解释这些限制，读完后在第 5.5 节统一看 mask 表。参见 [Q-Former 官方实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/Qformer.py)。

## 3. ITC：让多个 query 输出与文本进入可比较的空间

> [!note] 先抓住主线
> 想保留快速图文检索能力 → 图像与候选文本必须独立编码 → 禁止 query–text 相互读取 → 比较各 query 与文本 CLS → 取最高相似度 → 做双向候选分类。
>
> 目标仍与 CLIP / BLIP 的 ITC 相通，但图像侧不再只有一个 CLS 对比向量。

### 3.1 为什么 ITC 不能让 query 提前看候选文本？

如果编码狗图片时，query 已经看过“狗在草地上跑”，再拿输出与这句话比较，就不再是两个独立表示之间的对齐。

因此 ITC 模式下：

- Query 能读其他 query，也能经 cross-attention 读取图片。
- 文本内部使用双向 self-attention，取 `[CLS]` 输出表示整段文本。
- **Query 不读文本，文本也不读 query。**

同一张图片面对不同候选文本，其独立 query 输出 $Z(I)$ 不需要重新计算。这与第 4 节的 ITM 不同。

### 3.2 多个 query 怎么与一个文本向量比较？逐个算，再取最大

图像侧输出 $N_q$ 个 query，文本侧取一个 CLS 表示。两侧分别投影到同一维度并归一化：

$$
u_{i,k}=\operatorname{normalize}(W_Iz_{i,k}+b_I),
\qquad
v_j=\operatorname{normalize}(W_Th_j^T+b_T),
\qquad u_{i,k},v_j\in\mathbb{R}^{d}.
$$

这里 $z_{i,k}$ 是图片 $I_i$ 的第 $k$ 个 query 输出。接下来**不是先平均 query**，而是分别与文本 $T_j$ 比较，再取最高相似度：

$$
\boxed{s_{ij}=\frac{1}{\tau}\max_{1\le k\le N_q}u_{i,k}^{\top}v_j}.
$$

为演示，只看三个 query 与某段文本的余弦相似度：

| Query | 相似度 |
| --- | --- |
| 第 $1$ 个 | $0.2$ |
| 第 $2$ 个 | $0.8$ |
| 第 $3$ 个 | $0.4$ |

这对图文取 $0.8$，再除以温度 $\tau$。原论文仍使用 $32$ 个 query；表格只是小例子。

**换一段候选文本，获最高分的 query 可以改变。** 这提供了多个匹配位置，但不保证每个 query 已经对应一个独立物体。

### 3.3 候选从哪里来：这次不是 BLIP 的动量队列

BLIP-2 使用当前 batch 内的负例，官方实现可跨设备汇集当前候选；**不沿用原始 BLIP 的动量编码器队列方案**。论文解释，冻结视觉骨干后每张 GPU 能容纳更多样本，因此采用 in-batch negatives。

| 对比 | 原始 BLIP ITC | BLIP-2 ITC |
| --- | --- | --- |
| 图像侧比较表示 | 全局 CLS 投影 | 多个 query 投影，与文本比较后取 max |
| 主要候选来源 | 当前动量特征 + 历史队列 | 当前 batch，可跨设备汇集 |
| 目标的额外处理 | 动量软判断与硬标签混合 | 常规预训练实现用均匀 label smoothing |

不要因为前一篇刚学过 EMA，就把它默认带入本篇。

### 3.4 最后再看损失：依然是双向 softmax 选择题

为展示基本机制，暂时忽略 label smoothing，并设每个样本只有一个已知正配对。令 $B$ 为当前参与对比的图文对数，图像找文本、文本找图像两个方向为：

$$
\mathcal{L}_{\mathrm{ITC}}
=-\frac{1}{2B}\sum_{i=1}^{B}
\left[
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ij})}
+
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ji})}
\right].
$$

**分数怎么产生变了，分类问题没有变：仍然是在候选中找对应，不是 SigLIP 式逐对 sigmoid 二分类。**

实现细节放在主线之后：常规预训练 ITC 使用 $0.1$ 的 label smoothing；带 `image_id` 的检索微调路径还会处理同一图片的多个正配对。均匀平滑并非来自动量教师，也不会自动解决所有假负样本。参见 [官方 ITC 实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)。

## 4. ITM：让 query 和完整文本一起看，再判断匹配

> [!note] 先抓住主线
> 独立相似度之外，还想检查当前图文的细节 → 开放 query–text 双向交互 → query 输出包含当前配对信息 → 各 query 做二分类打分 → 平均 logits 后判断匹配。
>
> 与 BLIP 一样，ITC 可帮助挑选难负例；但最终分类不再取文本 `[Encode]`，而是使用 query 输出。

### 4.1 为什么切换可见性：判断配对时，不必禁止图文交流

面对“狗在草地上跑”的图片，判断候选“狗在沙发上睡觉”是否匹配，需要结合完整文本与画面。

ITM 允许：

- Query 与其他 query 交流，并读取视觉特征。
- Query 读取完整文本，文本也读取 query。
- 文本内部双向读取上下文。

于是融合后的 query 输出变为：

$$
Z^{\mathrm{ITM}}(I_i,T_j)\in\mathbb{R}^{N_q\times d_q}.
$$

它不仅依赖图片，也依赖当前文本。**换一段候选文本，融合计算就要相应改变，不能像 ITC 那样对所有文本只缓存一份 query 输出。** 图像骨干特征仍可以复用。

### 4.2 正负标签和难负例：沿用熟悉的配对监督

原始图文配对作正例；为图片换文本、或为文本换图片，构造负例。ITC 相似度高的错配更容易被抽中，让模型练习区分容易混淆的内容，而不是只排除明显无关的飞机描述。

| 构造类型 | 数量，设本地 batch 为 $b$ |
| --- | --- |
| 原图 + 原配对文本 | $b$ |
| 负图 + 当前文本 | $b$ |
| 当前图片 + 负文本 | $b$ |
| 合计 | $3b$ |

这里的本地样本数 $b$ 与跨设备对比候选数 $B$ 要分开。不是对所有 $B^2$ 个候选组合都做融合；采样是按相似度引导的随机选择，不是固定取最高分，也不是可微操作。错误配对仍可能在语义上适用，所以标签有噪声的风险没有消失。

### 4.3 Query 如何给出匹配结果：先平均 logits，再 softmax

每个输出 query 经过同一个二分类线性 head：

$$
g_{ij,k}=W_{\mathrm{ITM}}z_{ij,k}^{\mathrm{ITM}}+b_{\mathrm{ITM}}
\in\mathbb{R}^{2}.
$$

每个向量包含 unmatched、matched 两个分数。把所有 query 的分数平均：

$$
\bar g_{ij}=\frac{1}{N_q}\sum_{k=1}^{N_q}g_{ij,k},
\qquad
\pi_{ij}=\operatorname{softmax}(\bar g_{ij})_{\mathrm{matched}}.
$$

再计算熟悉的正负交叉熵：

$$
\ell_{ij}^{\mathrm{ITM}}
=-y_{ij}\operatorname{log}\pi_{ij}
-(1-y_{ij})\operatorname{log}(1-\pi_{ij}),
\qquad y_{ij}\in\{0,1\}.
$$

正例希望 matched 输出高，负例希望它低；最后汇总配对损失。

> [!warning] 两个容易混淆的平均
> **ITC：各 query–text 相似度取最大值。ITM：各 query 的分类 logits 取平均。**
>
> ITM 是先平均 logits 再 softmax，不是先对每个 query 得到概率再平均；softmax 非线性，两种操作通常不等价。

参见 [官方 ITM、负例采样与聚合实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)。

## 5. ITG：让 query 保留足以支持描述生成的信息

> [!note] 先抓住主线
> 只让表示适合比较，还不一定保留生成描述所需的信息 → 要求 Q-Former 看图写 caption → 文本不能直接读图，只能经过 query 通道 → 用下一 token 监督训练 query 保留语言相关内容。
>
> **ITG（Image-grounded Text Generation）是第一阶段的生成任务，此时外部 LLM 还没有接入。**

### 5.1 从 BLIP 的 LM 接过来：监督相似，视觉信息的入口不同

同样预测 `a dog` 后面的 `running`：

| | 原始 BLIP 的 LM | BLIP-2 第一阶段的 ITG |
| --- | --- | --- |
| 下一 token 答案 | 真实配对描述 | 真实配对描述 |
| 文本能直接 cross-attend 到视觉 token 吗？ | 能 | 不能 |
| 视觉信息怎样进入文本？ | 文本通过 cross-attention 直接读图 | Query 先读图，文本通过 self-attention 读 query |
| 为什么训练生成？ | 学会图像条件描述生成 | 同时约束 query 通道保留描述所需信息 |

可以概括为：**图像特征 → query 隐状态 → 文本隐状态 → 下一 token。**

这条“经过 query”的路径发生在 Q-Former 各层的交互中，不是只把最终输出 $Z$ 送进一个完全独立的小文本网络。下文用 $Z(I)$ 表示视觉信息通道时，是帮助理解的概括。

### 5.2 只挡住未来文本还不够：还要防止从 query 绕路偷看

ITG 使用的可见性规则是：

1. Query 之间双向可见，可以读取图像。
2. Query **不能读取文本**。
3. 文本可以读取所有 query，以及当前位置及之前的文本输入。
4. 文本不能读取未来文本位置。

为什么还要加第 $2$ 条？如果 query 先读完整描述，再把信息传给前面的文本位置，答案就可能经 query 间接泄漏。

> [!example] 防泄漏的因果链
> 预测下一 token 不能提前看到答案 → 文本遮住未来位置 → 还要切断“未来文本 → query → 当前文本”的绕行路径 → 禁止 query 读取文本。
>
> 因而不能给整个 query + text 序列简单套一个普通下三角 mask：**query 内部仍然是双向可见的。**

### 5.3 Teacher forcing：训练时前缀由真实描述提供

以单词近似 token 作演示，实际 tokenizer 可能拆分 subword：

| 文本可见前缀 | 可读取的视觉信息 | 预测目标 |
| --- | --- | --- |
| `[DEC]` | Query 通道 | `a` |
| `[DEC] a` | Query 通道 | `dog` |
| `[DEC] a dog` | Query 通道 | `running` |
| `[DEC] a dog running` | Query 通道 | `on` |
| `[DEC] a dog running on` | Query 通道 | `grass` |
| 完整描述前缀 | Query 通道 | 结束 token |

Teacher forcing 表示训练时喂入真实前缀，而不是必须接上模型刚猜出的词。通过任务 mask，可以并行计算多个文本位置的损失；真正生成时，才需要用自己生成的 token 继续下一步。

### 5.4 最后看生成损失：正确 token 概率越低，惩罚越大

若目标 `running` 的预测概率只有 $0.2$，忽略标签平滑，该位置损失是 $-\operatorname{log}0.2$；概率提高到 $0.8$，损失就会减小。

基础条件生成可概括为：

$$
p_{\theta_q}(T\mid I)
=\prod_{t=1}^{L}p_{\theta_q}(t_t\mid t_{<t},Z(I)).
$$

记有效目标位置集合为 $\Omega$，数量为 $N_{\mathrm{tok}}$，基础交叉熵为：

$$
\mathcal{L}_{\mathrm{ITG}}
=-\frac{1}{N_{\mathrm{tok}}}
\sum_{(i,t)\in\Omega}
\operatorname{log}p_{\theta_q}(t_{i,t}\mid t_{i,<t},I_i).
$$

这里展示不含标签平滑、忽略具体实现归约差异的基础形式；padding 不作目标，起始标记用于输入，结束 token 需要学习预测。

**损失会训练 Q-Former 与 queries，但不更新冻结视觉骨干。** 这与原始 BLIP 的 LM 能更新在线 ViT 不同。文本前缀也提供语言先验，因此生成目标只是鼓励保留和利用视觉信息，不保证每个词都来自可靠视觉证据。参见 [官方第一阶段生成路径](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)。

### 5.5 现在再把三种 attention masks 放到一起

理解各自为什么需要限制后，再看表格。这里的“文本”都是 **Q-Former 内的文本分支**：

| 目标 | Query 读 query？ | Query 读文本？ | 文本读 query？ | 文本内部可见性 |
| --- | --- | --- | --- | --- |
| ITC | 能 | 不能 | 不能 | 双向 |
| ITM | 能 | 能 | 能 | 双向 |
| ITG | 能 | 不能 | 能 | 因果，不能读取未来目标 |

所有任务中，直接读取视觉 token 的都是 query 路径。

如果用“行读取列”，并按 query、文本的顺序排列，布尔可见性可写成：

$$
A_{\mathrm{ITC}}=
\begin{bmatrix}\mathbf{1}&\mathbf{0}\\\mathbf{0}&\mathbf{1}\end{bmatrix},
\qquad
A_{\mathrm{ITM}}=
\begin{bmatrix}\mathbf{1}&\mathbf{1}\\\mathbf{1}&\mathbf{1}\end{bmatrix},
\qquad
A_{\mathrm{ITG}}=
\begin{bmatrix}\mathbf{1}&\mathbf{0}\\\mathbf{1}&C\end{bmatrix}.
$$

其中 $\mathbf{1}$ 表示对应块全允许，$\mathbf{0}$ 表示全禁止，$C$ 是含对角线的下三角允许矩阵。**这是可见性示意，不是直接加到 attention logits 上的数值 mask**；实际还需处理 padding。

![[_assets/images/BLIP-2-2301.12597-01-qformer-attention-masks.png|900]]

原论文 Figure 2。左侧展示 Q-Former，右侧灰色表示禁止、白色表示允许。注意图中顺序为 **ITM → ITG → ITC**，与正文讲解顺序不同。文本分支不是外部 OPT / FlanT5。

> [!success] 第一阶段最后学到什么？
> **ITC 让 query 表示适合对齐；ITM 让融合 query 适合判断当前配对；ITG 让 query 通道保留支持文本生成的信息。**
>
> 三个目标联合训练同一个 Q-Former，不是三个完全独立的模型。第一阶段结束后，还需要学习怎样把视觉信息交给特定 LLM。

## 6. 第二阶段：把 query 输出变成冻结 LLM 能利用的输入

> [!note] 这里换阶段了，不是继续第一阶段的小文本生成
> Q-Former 已经学会提取语言相关视觉信息 → 输出仍不天然属于 LLM 输入空间 → 增加线性投影 → 形成连续视觉提示 → 用外部冻结 LLM 的生成损失继续训练接口。
>
> **第二阶段继承并继续训练第一阶段的 Q-Former，不是丢掉它重新随机训练，也不是把四个任务一直联合优化。**

### 6.1 Soft visual prompts：直接传向量，不先把图片翻译成单词

假设 Q-Former 输出了 $32$ 个视觉向量。我们希望把它们作为 LLM 的一段额外输入，而 LLM 原本接收的是文本 token embeddings。

因此，用线性投影把维度对齐：

$$
U=ZW_P+\mathbf{1}_{N_q}b_P^\top
\in\mathbb{R}^{N_q\times d_\ell},
\qquad
W_P\in\mathbb{R}^{d_q\times d_\ell},
\quad b_P\in\mathbb{R}^{d_\ell}.
$$

| 符号 | 含义 |
| --- | --- |
| $Z$ | Q-Former 输出的视觉 query 表示 |
| $W_P,b_P$ | 可训练的投影参数 |
| $d_\ell$ | LLM 的输入 embedding 维度 |
| $U$ | 投影后的连续视觉提示，即 soft visual prompts |

**“Soft”指连续向量，不是离散 token ID。** 每个向量不必对应词表中的某个单词；也不是先生成 `dog`、`grass` 再让 tokenizer 编码。

设要输入的文本 embeddings 为 $E_T\in\mathbb{R}^{L\times d_\ell}$，沿序列维度拼接：

$$
X_{\mathrm{in}}=\operatorname{Concat}_{\mathrm{seq}}(U,E_T)
\in\mathbb{R}^{(N_q+L)\times d_\ell}.
$$

拼接发生在**输入 embedding 层**，不是输出 logits 后面。它进入 LLM 的哪个部分，则取决于采用 OPT 还是 FlanT5。

### 6.2 OPT：视觉前缀进入 decoder-only 模型

OPT 的输入可以理解为“视觉向量前缀 + 已有文本”。模型根据它们预测后面的文本 token：

$$
\mathcal{L}_{\mathrm{stage2}}^{\mathrm{OPT}}
=-\sum_{t=1}^{L}\operatorname{log}p_{\theta_\ell}(t_t\mid U,t_{<t}).
$$

公式省略 batch 与 token 平均。$\theta_\ell$ 是冻结 LLM 的参数，$U$ 则来自可训练接口。

- 真实配对 caption 提供目标，不是要求模仿 LLM 自己写出的伪标签。
- 视觉前缀是向量，没有对应的离散词表标签，不对这些位置要求预测“正确视觉 token ID”。
- 官方实现忽略视觉前缀、padding，以及配置中不需要预测的文本 prompt 位置；训练目标文本位置。

参见 [官方 OPT 接入实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_opt.py)。

### 6.3 FlanT5：视觉提示进入 encoder，decoder 生成后缀

FlanT5 本来就有 encoder 和 decoder，不能照搬 OPT 的入口。论文采用 **prefix language modeling（前缀语言建模）**：把描述分为前缀与后缀。

例如，仅作教学拆分：

| 放在哪里？ | 示例内容 |
| --- | --- |
| Encoder 输入 | 视觉提示 $U$ + `a dog` 的文本 embeddings |
| Decoder 生成目标 | `running on grass` 及结束标记 |

记 $T=(T_{\mathrm{prefix}},T_{\mathrm{suffix}})$，则：

$$
\mathcal{L}_{\mathrm{stage2}}^{\mathrm{T5}}
=-\sum_{t=1}^{L_s}\operatorname{log}p_{\theta_\ell}
\left(t_t^s\mid U,T_{\mathrm{prefix}},t_{<t}^s\right).
$$

$L_s$ 是后缀长度。训练时 decoder 使用真实后缀的右移输入，encoder 不接收目标后缀。

> [!warning] 两种 LLM，是可选路径，不是串联模块
> **OPT：视觉提示进入 decoder-only LLM。FlanT5：视觉提示进入 encoder，decoder 生成后缀。**
>
> 因此，“BLIP-2 都在 decoder 输入端拼视觉 token”是不准确的。FlanT5 接入方式见 [论文第 3.3 节](https://arxiv.org/abs/2301.12597)与[官方实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_t5.py)。

### 6.4 原来的小文本分支去哪了？为什么参数量会变？

第一阶段 Q-Former 内的 BERT 初始化文本分支，和第二阶段 OPT / FlanT5 是独立模型，各有 tokenizer 与词表。

官方基础生成实现会裁剪 Q-Former 中不用的文本 embedding、文本 FFN 与语言输出 head，**保留并继续训练 query 视觉提取路径**。所以不是两个文本模型先后把 caption 重写一遍。

这也解释了数字差异：完整第一阶段 Q-Former 约有 $188$ million 参数；Table 2 的具体生成模型可训练参数约为 $103$--$108$ million。看参数量必须确认阶段、裁剪与配置，不能把 $188$ million 无条件套到每个生成 checkpoint。

## 7. 梯度与参数更新：冻结 LLM，为什么中间还能学？

> [!note] 先区分“固定权重”和“切断计算路径”
> 生成结果出错 → 损失依赖 LLM 的视觉输入 → 梯度穿过固定的 LLM 计算 → 回到投影、Q-Former 与 queries → 优化器更新这些接口参数。
>
> **冻结表示不更新权重，不表示这个模块对输入没有导数。**

### 7.1 先确认谁在学，再看反向传播

| 模块 | 第一阶段预训练 | 第二阶段预训练 |
| --- | --- | --- |
| 视觉骨干 ViT | 冻结 | 冻结 |
| Query embeddings | 更新 | 更新 |
| Q-Former | 按 ITC / ITM / ITG 更新有效分支 | 继续更新 query 视觉提取路径 |
| 第一阶段任务输出模块 | 按各自目标更新 | 不作为基础 LLM 生成路径的输出模块 |
| 到 LLM 的投影 | 尚未用于这一阶段 | 更新 |
| 外部 LLM | 不接入 | 冻结 |

这里的冻结视觉编码器指骨干。官方 `ln_vision` 在冻结 ViT 参数的循环之外，视觉路径上仍可能有可训练的附加 LayerNorm，不能把每个视觉相关参数都当成冻结。

### 7.2 跟着一次生成错误走：固定函数也能传回输入梯度

假设 LLM 没有正确生成 `running`。视觉提示 $U$ 变了，LLM 的输出概率就可能变，因此可以计算损失对 $U$ 的导数，再沿输入来源继续回传：

$$
I\rightarrow E_{\theta_v}(I)
\rightarrow F_{\theta_q}(Q_0,H^I)
\rightarrow U
\rightarrow\operatorname{LLM}_{\theta_\ell}
\rightarrow\mathcal{L}.
$$

将外部 LLM 看作一个固定但可微的函数，接口参数的梯度满足：

$$
\frac{\partial\mathcal{L}}{\partial\theta_q}
=\frac{\partial\mathcal{L}}{\partial U}
\frac{\partial U}{\partial Z}
\frac{\partial Z}{\partial\theta_q}.
$$

**训练调整的是“给固定 LLM 什么输入”，而不是“把 LLM 内部权重改成什么”。** Query embeddings 和投影参数也通过对应路径获得梯度。

这不应说成 LLM 对参数的数学导数必然为零；正确表述是 LLM 参数不参与优化器更新。

### 7.3 实现陷阱：冻结权重不等于套上 `no_grad`

| 操作 | 作用 | 在这里要注意什么？ |
| --- | --- | --- |
| `requires_grad=False` | 不为相应参数计算训练梯度 | 仍可保留对需要梯度的输入的计算路径 |
| `torch.no_grad()` | 不记录该上下文内的反向计算图 | 包住训练用 LLM 会切断到视觉提示的梯度 |
| `eval()` | 改变 dropout 等运行行为 | 不等于冻结参数，也不等于关闭 autograd |

冻结视觉骨干之前没有可训练输入模块时，可把它当作不需要反向图的特征提取器；但 **LLM 前面有可训练接口**，训练时不能把整个 LLM 前向放进 `no_grad`。推理时不训练接口，`generate` 可以关闭梯度。

### 7.4 两阶段更新怎么串起来？

第一阶段把三个任务的损失相加：

$$
\mathcal{L}_{\mathrm{stage1}}
=\mathcal{L}_{\mathrm{ITC}}+\mathcal{L}_{\mathrm{ITM}}+\mathcal{L}_{\mathrm{ITG}}.
$$

共享 Q-Former 参数收到的梯度按计算图相加，再由优化器更新；哪个任务不用某参数，对应贡献就是零。冻结 ViT 不跟着更新。

第二阶段从这份 Q-Former 继续，用 LLM 生成损失更新有效 query 路径与投影等接口参数，冻结视觉与 LLM 骨干。**没有原始 BLIP ITC 的 EMA / 历史队列维护步骤。**

### 7.5 冻结节省什么，不节省什么？

冻结能减少对应的参数梯度、优化器状态和权重更新开销，但大模型权重仍要载入、前向仍要执行，第二阶段还需要通过 LLM 计算输入梯度。

$32$ 个视觉提示减少了送入 LLM 的视觉序列长度，但不免除 ViT 提取图片特征、Q-Former 读取视觉 token 的工作。

> [!warning] 少量可训练参数 ≠ 小模型，也 ≠ 同比例提速
> 要分开看**总参数、可训练参数、输入序列长度、前向计算、输入反向计算**。论文的效率优势不能直接换算成任意硬件上的延迟或显存比例。

## 8. 数据准备：也叫 CapFilt，但不要照搬原始 BLIP 的 filter

> [!note] 再次换层次：这里讲训练数据怎样准备
> 前面是模型接口的两阶段训练；这里是给这些训练准备更可靠的图文配对。**离线准备描述，不是每次 LLM 生成时现场重新筛选数据。**

### 8.1 为什么还需要生成和筛选？

网络描述可能是文件名、广告或模糊网页语境。延续 BLIP 的思路，可以先补写描述，再挑选更相关的配对。

但本篇的具体做法不是“captioner 写一条，独立 ITM filter 判正负”：

| 步骤 | BLIP-2 论文中的操作 |
| --- | --- |
| 生成 | 用 BLIP-large 为每张网络图片生成 $10$ 条描述 |
| 合并 | 把生成描述与原始网页描述放在一起 |
| 排序 | 用 CLIP ViT-L/14 的图文相似度打分 |
| 保留 | 每张图保留排名最高的 $2$ 条 |
| 训练取样 | 每次使用该图时，从保留描述中随机取一条 |

比如狗图片的原始文本只是 `my weekend diary`，补写后可能出现更具体的狗与草地描述；实际保留哪些由 CLIP 排序决定，不保证每次都正确。

### 8.2 两种“自举”，分别发生在什么地方？

| 概念 | 本篇具体指什么？ |
| --- | --- |
| 数据自举 | 借助已有 BLIP captioner 和 CLIP，准备描述监督 |
| 模型能力自举 | 借助冻结视觉模型与冻结 LLM，训练 Q-Former 建立连接 |

前者改数据，后者训练接口。BLIP-2 的核心主线更强调后者，但没有完全丢掉前者。

论文使用约 $129$ million 张图片，来源包括 COCO、Visual Genome、CC3M、CC12M、SBU，以及 LAION400M 中的 $115$ million 张图片。参见 [原论文第 3.4 节](https://arxiv.org/abs/2301.12597)。

## 9. 从预训练到使用：先问任务需要哪条路径

> [!note] 不要默认“每个任务都经过 LLM”
> **生成与问答可以使用外部 LLM；图文检索可以直接使用第一阶段 Q-Former。** 问题是否输入 Q-Former、视觉骨干是否解冻，也要按具体任务区分。

### 9.1 基础零样本问答：问题主要进入 LLM

基础生成路径中，Q-Former 根据图片提取视觉信息，投影后和问题 prompt 一起输入 LLM：

$$
I\rightarrow H^I\rightarrow Z(I)\rightarrow U(I),
\qquad
(U(I),\text{问题 prompt})\rightarrow\text{LLM 答案}.
$$

论文对 OPT 使用 `Question: {} Answer:`，对 FlanT5 使用 `Question: {} Short answer:`。

**不能默认问题已经进入 Q-Former，让它根据问题重新读取图像。** “LLM 根据问题使用视觉信息”和“Q-Former 根据问题提取视觉信息”是两个不同位置的条件化。

这里 zero-shot 指没有用对应 VQA 任务标注微调该生成模型，不表示各组件从未训练；FlanT5 本身已有文本指令训练。

### 9.2 有监督 VQA：可以额外让 Q-Former 读问题

论文 VQA 微调时，将问题 token 也送入 Q-Former，让 queries 与问题通过 self-attention 交互：

$$
Z(I,T_{\mathrm{question}})
=F_{\theta_q}(Q_0,H^I,T_{\mathrm{question}}).
$$

此时提取的信息可以依赖问题，再投影并与问题一起供 LLM 生成答案。微调会更新视觉编码器与 Q-Former，LLM 仍冻结。

所以既不能说“queries 就是问题”，也不能说“Q-Former 永远不能读文本”。第一阶段 ITM 和这一 VQA 微调路径都允许文本参与 query 交互。

### 9.3 Captioning：让 LLM 生成描述

论文在 COCO 上微调 captioning，使用 `a photo of` 作为文本提示，以真实 caption 构造生成交叉熵；更新视觉编码器与 Q-Former，同时保持 LLM 冻结。

生成时不必对每个 token 再同步运行 ITC / ITM。它们主要塑造第一阶段的表示，不是每次写词都要调用的判别器。

### 9.4 图文检索：使用第一阶段模型，不需要 LLM

检索使用第一阶段模型，在 COCO 上联合微调视觉编码器与 Q-Former，目标仍是 ITC + ITM + ITG。

1. **召回**：独立 query 图像表示与文本表示计算相似度，找到候选。
2. **重排**：对 $k=128$ 个候选做 ITM 联合编码，细判当前配对。

ITG 即使不是检索的最终输出任务，也可以在训练中帮助 query 保留语言相关信息；其消融见第 10.5 节。

| 阶段 / 任务 | 视觉骨干 | Q-Former 与相关适配模块 | 外部 LLM |
| --- | --- | --- | --- |
| 第一阶段预训练 | 冻结 | 更新 | 不接入 |
| 第二阶段预训练 | 冻结 | 更新有效 query 路径与投影 | 冻结 |
| 论文 captioning / VQA 微调 | 更新 | 更新任务相关部分 | 冻结 |
| 论文检索微调 | 更新 | 更新第一阶段相关部分 | 不需要 |

**预训练冻结两端，不代表下游始终冻结视觉编码器。** 参见 [原论文下游任务与附录](https://arxiv.org/abs/2301.12597)。

## 10. 实验证据：先确认比较条件，再看收益

### 10.1 预训练配置：高效是相对大规模端到端训练而言

先看实验的规模背景，再分别看零样本问答、两阶段消融、描述生成与检索。这里保留原论文表格，避免只记住一个最高分。

原论文报告：

- 第一阶段训练 $250{,}000$ steps；第二阶段训练 $80{,}000$ steps。
- 第一阶段 ViT-L / ViT-g 的 batch size 分别为 $2{,}320$ / $1{,}680$。
- 第二阶段 OPT / FlanT5 的 batch size 分别为 $1{,}920$ / $1{,}520$。
- 预训练图片分辨率为 $224\times224$。
- 最大配置 ViT-g + FlanT5-XXL 在一台含 $16$ 张 A100、每张 $40$ GB 的机器上，第一阶段少于 $6$ 天，第二阶段少于 $3$ 天。

这些数字是论文特定硬件与实现的报告，不是任意机器上的训练承诺，也不是说整个预训练可以忽略大型模型的算力成本。

### 10.2 零样本 VQA：视觉接口有效，但收益依赖任务与骨干

![[_assets/images/BLIP-2-2301.12597-02-zero-shot-vqa.png|900]]

阅读 Table 2 时，先区分 `#Trainable Params` 与 `#Total Params`。例如 ViT-g + FlanT5-XXL 的可训练参数为 $108$ million，而总参数为 $12.1$ billion。

- 该配置的 VQAv2 test-dev 得分为 $65.0$，Flamingo80B 为 $56.3$。论文将其差距报告为 $8.7\%$；按表中的评分尺度，应理解为 **$8.7$ 个百分点**，不是相对提升百分比。
- 论文摘要的“少 $54$ 倍可训练参数”使用完整第一阶段 Q-Former 的约 $188$ million 与 Flamingo 的 $10.2$ billion 对比；它不是依据上述 $108$ million 直接得到的，也不是总参数或推理延迟对比。
- 在 OK-VQA 上，BLIP-2 该配置为 $45.9$，Flamingo80B 为 $50.6$，因此不能说 BLIP-2 在所有视觉问答测试上都领先。

作者观察到更强视觉骨干、更大同系列 LLM、经过指令训练的 FlanT5 往往有利于 VQA。但表中也有个别指标不是单调增加，不能推广成“任何任务只要换更大 LLM 就必然更好”。所有比较均指论文发表时的实验设置。参见 [原论文第 4.1 节](https://arxiv.org/abs/2301.12597)。

### 10.3 为什么要第一阶段，而不是从一开始只用 LLM loss？

论文 Figure 5 比较了是否先做视觉语言表征学习。去掉第一阶段后，OPT 与 FlanT5 的零样本 VQA 表现都明显更低；OPT 路径还出现训练继续进行、VQA 表现反而下降的现象。

这支持两阶段设计的动机：**先把 query 训练成有语言相关性的视觉接口，再让它适配冻结 LLM，比仅依赖生成监督从头打通接口更有效。**

作者将 OPT 的退化称为 catastrophic forgetting，但这里 LLM 权重仍然冻结。解读时应区分“视觉条件下系统表现退化”与“LLM 权重被更新而遗忘”：不能仅凭曲线认定 LLM 内部权重受到了破坏，也不能把这个消融扩展成“所有单阶段生成式连接方法都无效”。

### 10.4 Captioning：NoCaps 的 zero-shot，是在 COCO 微调之后迁移

![[_assets/images/BLIP-2-2301.12597-03-captioning-results.png|900]]

Table 3 同时展示 COCO 微调后的测试，以及向 NoCaps 的零样本迁移。FlanT5-XL 配置在 NoCaps overall 上报告 CIDEr $121.6$、SPICE $15.8$。

这里的 `NoCaps Zero-shot` **不表示模型从未做过 captioning 微调**：模型先在 COCO 上微调，只是没有再用 NoCaps 训练。

表中的可训练参数约为 $1.1$ billion，也不与前面“冻结两端”矛盾，因为 captioning 微调解冻了视觉编码器。看效率数字时必须先确认它属于预训练还是下游微调。

### 10.5 检索与 ITG 消融：生成监督也能帮助非生成任务

![[_assets/images/BLIP-2-2301.12597-04-retrieval-results.png|900]]

Table 5 中的 BLIP-2 检索路径先在 COCO 微调，再迁移到 Flickr30K，不需要外接 LLM。评测同时包含图像到文本、文本到图像两个方向，R@1、R@5、R@10 分别检查正确对象能否出现在相应数量的前排候选中。

![[_assets/images/BLIP-2-2301.12597-05-itg-ablation.png|900]]

Table 6 比较的是 **COCO 检索微调阶段的训练目标**。在 ITC + ITM 基础上加入 ITG，论文展示的检索指标得到改善。

它支持“生成目标有助于 query 保留语言相关视觉信息”的解释，但不是直接证明每个 query 都学会了独立概念，也不是针对两个预训练阶段是否都必要的消融。**ITG 微调消融与 Figure 5 的第一阶段消融，回答的是两个不同问题。**


## 11. 能力边界：冻结、瓶颈与生成都不是保证

### 11.1 论文明确报告的限制

- **多模态 in-context learning 没有自然出现**：作者给 LLM 提供上下文 VQA 示例后，没有观察到 VQA 提升，并将其与预训练样本只包含单个图文配对、缺少多图文交错序列联系起来。
- **生成可能出错**：LLM 的知识错误、不恰当的推理过程，以及未能识别新图像内容等，都可能造成不可靠输出。
- **继承冻结 LLM 的风险**：包括偏见、冒犯性语言与潜在隐私泄露；冻结本身不是安全保证。参见 [原论文 Limitation](https://arxiv.org/abs/2301.12597)。

### 11.2 根据架构应保留的理解边界

- **信息瓶颈不保证无损**：固定数量的 queries 强迫选择信息，并不保证细小文字、密集物体或所有空间关系都被完整保存。
- **能跟随文本提示，不等于经过完整多模态指令对齐**：这里主要复用 LLM 原有的语言能力，不能直接把示例中的对话表现理解成可靠的通用视觉助手。
- **Q-Former 不是必然的目标定位器**：注意力能分配视觉读取权重，不等于每个 query 对应一个真实对象。
- **这是图像语言预训练论文**：虽然笔记位于 Video-MLLM 目录，其实验不能直接证明原始 BLIP-2 已具备显式时序建模或长视频理解能力。

这些边界用于防止过度解读，不是在没有实验的情况下断言 BLIP-2 在某个具体数据集上一定失败。


## 12. 最后串起来：从同一张狗图片走完 BLIP-2

### 12.1 一次完整的理解顺序

1. **看清问题**：已有视觉模型与 LLM 很强，但表示空间不天然兼容。
2. **取得监督**：配对关系支持对齐与匹配，配对描述提供生成目标。
3. **冻结提取**：ViT 输出视觉 token，骨干不更新。
4. **Queries 读图**：共用的可学习初始向量与当前图像交互，输出固定长度、内容随图变化的表示。
5. **第一阶段联合学习**：ITC 保持独立并对齐，ITM 开放交互判匹配，ITG 限制泄漏并练习生成。
6. **接入外部 LLM**：将 query 输出投影为连续视觉前缀，进入 OPT decoder 或 FlanT5 encoder。
7. **第二阶段继续学习**：真实文本提供生成监督，梯度穿过冻结 LLM，更新接口而非 LLM 权重。
8. **按任务适配**：检索不必调用 LLM，基础问答与问题条件化 VQA 要区分，下游也可能解冻视觉骨干。

### 12.2 与 BLIP 对照：不要只记住多了一个 Q-Former

| 维度 | 原始 BLIP | BLIP-2 |
| --- | --- | --- |
| 核心诉求 | 统一对齐、匹配、生成，并改进数据 | 高效复用现成视觉与语言模型 |
| 主要架构 | ViT + MED | 冻结 ViT + Q-Former，第二阶段再接冻结 LLM |
| 预训练视觉骨干 | 在线分支更新 | 两阶段均冻结 |
| 视觉信息怎样进入文本 | 文本直接 cross-attend 到视觉 token | Query 先读图，文本 / LLM 经 query 通道取信息 |
| ITC 图像表示 | 图像 CLS 投影 | 多 query 与文本 CLS 比较，取最高相似度 |
| ITC 候选 | 动量特征 + 历史队列 | 当前 batch，可跨设备汇集 |
| ITM 聚合 | 文本 `[Encode]` 融合表示分类 | 各 query 的分类 logits 平均 |
| 生成模型 | MED 图像条件 decoder | 第一阶段 Q-Former 文本分支；第二阶段外部 LLM |
| 数据筛选 | 独立 ITM filter 判断 matched / unmatched | BLIP 补写，CLIP 相似度排序保留 |

> [!success] 两句话记住两阶段，而不是背四个 loss
> **第一阶段：训练一个会提取语言相关视觉信息的桥。**
>
> **第二阶段：继续训练这个桥，让冻结 LLM 能利用它送来的信息。**
>
> BLIP-2 不是“BLIP 后面接一个更大的 decoder”，也不是“ViT 后加一层投影就结束”。Q-Former 的信息瓶颈与两阶段监督共同承担适配工作。

### 12.3 继续深入时，值得追问什么？

下面是值得继续验证的问题，而不是原论文已经给出的结论：

1. **Query 数量如何影响信息损失与开销？** 固定 $32$ 个向量面对高分辨率、密集文字或复杂场景时，应怎样评估是否构成过强瓶颈？
2. **在哪一层加入问题条件最有效？** 只让 LLM 读取 question，与让 Q-Former 提前根据 question 取图像信息，各自改变了什么？
3. **两阶段收益来自哪些因素？** 应分别检查 ITC、ITM、ITG 的贡献，而不能把所有收益都归因于结构中出现了 cross-attention。
4. **从单图走向视频还缺什么？** 除了逐帧提取 query 表示，还需要检验帧顺序、时间位置与跨帧交互是否被模型真正利用。


## 参考资料

- [BLIP-2 原论文](https://arxiv.org/abs/2301.12597)：Junnan Li、Dongxu Li、Silvio Savarese、Steven Hoi，*BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models*。
- [ICML 正式论文页面](https://proceedings.mlr.press/v202/li23q.html)：会议发表信息与正式版本。
- [官方 LAVIS / BLIP-2 项目](https://github.com/salesforce/LAVIS/tree/main/projects/blip2)。
- [第一阶段模型与损失](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)：query–text 相似度、label smoothing、ITM 采样与聚合、ITG、总损失。
- [Q-Former 网络实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/Qformer.py)：self-attention、query 视觉 cross-attention 与 query 专用子层。
- [OPT 接入](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_opt.py)与[FlanT5 接入](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_t5.py)：冻结 LLM、分支裁剪、线性投影和生成监督。
- 本地原论文：[[07-MultiModal/Video-MLLM/assets/paper_2301.12597.pdf]]。
- 衔接笔记：[[05-BLIP：从图文对齐到理解、生成与数据自举]]。

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
