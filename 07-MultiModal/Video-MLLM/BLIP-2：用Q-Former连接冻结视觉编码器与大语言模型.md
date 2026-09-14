---
title: "BLIP-2：用Q-Former连接冻结视觉编码器与大语言模型"
authors: ["Junnan Li", "Dongxu Li", "Silvio Savarese", "Steven Hoi"]
conference: "ICML"
year: 2023
arxiv_url: "https://arxiv.org/abs/2301.12597"
pdf_link: "[[07-MultiModal/Video-MLLM/assets/paper_2301.12597.pdf]]"
cover: "[[_assets/images/BLIP-2-2301.12597-01-qformer-attention-masks.png]]"
created: 2026-09-12
updated: 2026-09-12
tags: ["paper/arxiv", "vlm", "image-text", "pretraining"]
status: "unread"
priority:
rating:
topics: ["MLLM"]
code: "https://github.com/salesforce/LAVIS/tree/main/projects/blip2"
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

> **BLIP-2 不再把视觉编码器与语言模型一起重新训练，而是冻结两端，用一个可训练的 Q-Former 学会“从图像中取出适合语言表达的信息”，再把这些信息变成冻结大语言模型能够利用的连续视觉提示。**

- **监督仍来自图文配对**：配对关系提供对比与匹配标签，配对文本提供生成目标；基础预训练不要求为每张图片准备问答标注。
- **Q-Former 是桥，不是另一个大语言模型**：一组可学习的 query embeddings 读取视觉 token，输出固定数量的视觉表示。
- **第一阶段学习视觉语言表征**：联合优化 ITC、ITM、ITG，通过不同 attention masks 控制 query 与文本能否互相读取。
- **第二阶段学习接入 LLM**：将 query 输出线性投影为 soft visual prompts，交给冻结 LLM 生成文本；更新的是桥接模块，不是 LLM 权重。
- **少量可训练参数，不等于整个模型很小**：冻结的视觉骨干和 LLM 仍占据存储与计算资源；下游微调时也可能解冻视觉编码器。

前置阅读：[[07-MultiModal/Video-MLLM/BLIP：从图文对齐到理解、生成与数据自举.md]]；更早的对齐基础见 [[07-MultiModal/Video-MLLM/CLIP：从图文配对到共享语义空间.md]]。

本文沿用 BLIP 笔记的组织方式：**监督信号 → 网络表示 → 各个 loss → 梯度与参数更新 → 数据处理 → 下游使用 → 完整心智模型**。内容以 BLIP-2 原论文为主；展开公式和狗图片示例是机制解释，不是原论文的样本或新实验。涉及实际损失、模块裁剪的地方另附官方代码来源。

## Key Contributions

### 从 BLIP 继续往前走：核心问题变了什么？

原始 BLIP 解决的是：

> 怎样用一套兼顾编码与解码的模型，同时学习图文对齐、细粒度匹配和文本生成，并用 CapFilt 改进训练数据？

BLIP-2 则进一步问：

> 既然已经有很强的视觉模型，也有很强的大语言模型，能不能不重新训练这两个大模块，只训练中间的连接部分，就得到视觉语言能力？

困难在于：**图像编码器的输出空间，不天然等于 LLM 的输入语义空间。** 即使把向量维度改成相同，LLM 也不一定知道这些数值代表狗、草地还是奔跑。因此，问题不只是“接口 shape 对上了没有”，还包括“送过去的信息是否有用、是否能被解释”。

| 核心问题 | BLIP-2 的回答 |
| --- | --- |
| 图像特征由谁提取？ | 现成且冻结的预训练视觉编码器 |
| 如何从大量视觉 token 中取信息？ | Q-Former 用可学习 queries 做 cross-attention，输出短视觉序列 |
| 如何让这段序列与语言有关？ | 第一阶段使用 ITC + ITM + ITG 进行表征学习 |
| 如何让 LLM 读懂这段序列？ | 第二阶段通过线性投影接入冻结 LLM，用文本生成目标训练接口 |
| 大语言能力从哪里来？ | 复用预训练 LLM，而不是完全由图文 caption 数据重新学会 |

论文的贡献可以概括为：**冻结两端的模块化框架、Q-Former 信息瓶颈、先表征后生成的两阶段训练策略**。这里的 bootstrapping 更强调复用已有模型能力；BLIP 的数据自举思想仍被用于数据准备，但不再是理解整个方法的唯一主线。参见 [BLIP-2 原论文](https://arxiv.org/abs/2301.12597)。

## Method

### 1. 监督信号：同一对图文，在两个阶段承担不同职责

#### 1.1 仍然从“一只狗在草地上跑”开始

设一批数据包含 $B$ 对图文：

$$
\mathcal{B}=\{(I_i,T_i)\}_{i=1}^{B},
\qquad
T_i=(t_{i,1},\dots,t_{i,L_i}).
$$

例如，图片 $I_1$ 中是一只狗在草地上跑，文本 $T_1$ 是 “a dog running on grass”。

| 阶段与目标 | 模型被要求做什么？ | 标签来自哪里？ |
| --- | --- | --- |
| 第一阶段 ITC | 从候选文本或图片中找配对对象 | 数据集中的图文配对关系 |
| 第一阶段 ITM | 判断当前这对图文是否匹配 | 正配对，以及采样得到的负配对 |
| 第一阶段 ITG | Q-Former 根据图像生成配对文本 | caption 自身的真实 token |
| 第二阶段生成学习 | 冻结 LLM 根据视觉提示生成文本或文本后缀 | 同样来自配对文本，而不是 LLM 自己生成的伪标签 |

所以，第一阶段和第二阶段不一定使用不同类型的数据，**变化主要发生在计算路径与接受生成监督的模块上**。

也不要把“无需为三个目标单独标注”理解成“没有人工监督”：预训练数据包含 COCO、Visual Genome 等人工标注来源，FlanT5 本身也经过文本指令训练。

#### 1.2 两个阶段，不是把四个 loss 一次性相加

第一阶段：

$$
\boxed{
\mathcal{L}_{\mathrm{stage1}}
=\mathcal{L}_{\mathrm{ITC}}
+\mathcal{L}_{\mathrm{ITM}}
+\mathcal{L}_{\mathrm{ITG}}
}
$$

它们是联合目标，不是先训练完 ITC、再训练 ITM、最后训练 ITG。第二阶段从已经训练好的 Q-Former 继续，接上 LLM，优化对应的生成目标。

关键区别是：**第一阶段的文本生成发生在 Q-Former 文本分支；第二阶段的文本生成发生在外部冻结 LLM。** 不能因为两者都预测下一个 token，就认为第二阶段只是第一阶段多训练一会儿。

### 2. 网络架构：冻结视觉编码器 + Q-Former + 冻结 LLM

#### 2.1 视觉编码器提供完整 token 序列

对单张图片，记视觉输出为：

$$
H^I=E_{\theta_v}(I)
\in\mathbb{R}^{P\times d_v}.
$$

其中 $P$ 为视觉 token 数量，$d_v$ 为视觉特征维度。两阶段预训练中，视觉骨干参数 $\theta_v$ 固定。

论文使用 CLIP 的 ViT-L/14 和 EVA-CLIP 的 ViT-g/14；实际采用倒数第二层的输出特征。以论文给出的 ViT-L/14 示例为例：

$$
H^I\in\mathbb{R}^{257\times1024}.
$$

这不是只取一个 CLS 向量。Q-Former 可以读取视觉 token 序列中的不同内容，但不会因此反向更新被冻结的 ViT。

#### 2.2 Learnable queries：不是用户问题，也不是固定图像 patch

定义一组可训练的输入向量：

$$
Q_0\in\mathbb{R}^{N_q\times d_q}.
$$

原论文使用 $N_q=32$、$d_q=768$。这些 query embeddings：

- 是模型参数，随训练一起更新。
- 对不同图片使用同一组初始向量，不是每张图片拥有独立的一套参数。
- 经过与当前图片的交互后，产生随图片变化的输出。
- 不是用户输入的自然语言 question，也没有预先规定“某个 query 专门负责狗，另一个负责草地”。

它们更像一组**可学习的信息读取位置**：训练决定每个位置怎样查询视觉特征，而不是人工划定 $32$ 个图像区域。

记图像侧 query 输出为：

$$
Z(I)=F_{\theta_q}(Q_0,H^I)
\in\mathbb{R}^{N_q\times d_q}.
$$

在原论文配置中，输出属于 $\mathbb{R}^{32\times768}$。**固定的是输出序列长度，不是输出内容。** 若视觉 token 数因分辨率而变化，Q-Former 仍可输出 $32$ 个向量；但处理更多视觉 token 的计算开销不会凭空消失。

#### 2.3 Q-Former 内部：query 读图，query 与文本共享 self-attention

Q-Former 包含相互配合的图像侧与文本侧 Transformer 子模块：

- **图像侧**：queries 之间通过 self-attention 交换信息，通过 cross-attention 读取冻结视觉特征。
- **文本侧**：根据任务作为文本 encoder 或 decoder；通过共享 self-attention 与 queries 交互。

论文以 BERT-base 权重初始化 Q-Former，新增 cross-attention 层随机初始化，并且每隔一个 Transformer block 插入 cross-attention，即每 $2$ 个 block 中有一个执行视觉读取。

这里与原始 BLIP 有一个容易记反的差异：

> **BLIP 的 MED 文本 encoder 与 decoder 不共享 self-attention 参数；BLIP-2 的 Q-Former 则让图像侧与文本侧共享 self-attention，并通过任务 mask 控制信息流。**

这不意味着 Q-Former 所有子层都完全共享。官方实现保留了 query 专用的 FFN 分支；图中的 query 与文本 FFN 也采用不同颜色。参见 [官方 Q-Former 实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/Qformer.py)。

#### 2.4 Cross-attention 的 Query、Key、Value 分别来自哪里？

记某层 query 隐状态为 $X_Q\in\mathbb{R}^{N_q\times d_q}$。省略多头拼接、残差与 LayerNorm，视觉 cross-attention 可以写成：

$$
Q=X_QW_Q,\qquad K=H^IW_K,\qquad V=H^IW_V,
$$

$$
\operatorname{CA}(X_Q,H^I)
=\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V.
$$

注意力权重属于 $\mathbb{R}^{N_q\times P}$。每个 query 可以对整段视觉序列分配读取权重。

必须区分三个概念：

1. **Learnable queries $Q_0$**：模型最初输入的可学习向量。
2. **Attention 中的 $Q$**：当前层隐状态经投影得到的查询矩阵。
3. **VQA question**：用户的自然语言问题。

三者相关，但不是同一个对象。**Q-Former 中的 Q 首先指 querying，而不是自动把用户问题当作 query embeddings。**

### 3. 三种 attention masks：控制信息能从哪里流向哪里

Q-Former 的三个目标，核心差异不仅是输出 head，还包括 query 与文本是否能相互读取。

下表中的“文本”指 Q-Former 的文本分支，不是第二阶段的 LLM：

| 目标 | query 能读其他 query？ | query 能读文本？ | 文本能读 query？ | 文本能读哪些文本位置？ |
| --- | --- | --- | --- | --- |
| ITC | 能 | 不能 | 不能 | 双向读取有效文本位置 |
| ITM | 能 | 能 | 能 | 双向读取有效文本位置 |
| ITG | 能 | 不能 | 能 | 当前输入位置及此前位置，不能读取未来目标 |

所有视觉读取仍经过 **query → image cross-attention**。Q-Former 的文本 token 不直接 cross-attend 到图像 token。

如果用“行读取列”表示注意力，按 query、文本排列序列，允许关系可概括为：

$$
A_{\mathrm{ITC}}=
\begin{bmatrix}
\mathbf{1}&\mathbf{0}\\
\mathbf{0}&\mathbf{1}
\end{bmatrix},
\qquad
A_{\mathrm{ITM}}=
\begin{bmatrix}
\mathbf{1}&\mathbf{1}\\
\mathbf{1}&\mathbf{1}
\end{bmatrix},
\qquad
A_{\mathrm{ITG}}=
\begin{bmatrix}
\mathbf{1}&\mathbf{0}\\
\mathbf{1}&C
\end{bmatrix}.
$$

这里 $\mathbf{1}$ 与 $\mathbf{0}$ 分别表示相应大小的全允许、全禁止块，$C$ 是包含对角线的下三角允许矩阵；这是布尔可见性示意，不是直接加到 attention logits 上的数值 mask。实际还需处理 padding。

- ITC 阻断 query–text 交互，避免“看过配对文本后再声称自己完成独立对齐”。
- ITM 开放双向交互，让表示依赖当前图文配对。
- ITG 允许文本读 query，但不允许 query 读文本，防止未来文本先流入 query、再被前面的文本位置间接偷看。

**ITG 不是给整段 query + text 序列简单套一个普通下三角 mask**：query 内部是双向可见的。参见 [原论文第 3.2 节与 Figure 2](https://arxiv.org/abs/2301.12597)。

### 4. ITC：多 query 图像表示，怎样和一个文本表示做对比？

#### 4.1 不先平均所有 query，而是取最高相似度

ITC 模式下，图片产生 $N_q$ 个 query 输出；文本独立编码，取 `[CLS]` 表示 $h_j^T$。

分别投影到共同空间并做 $L_2$ 归一化：

$$
u_{i,k}=\operatorname{normalize}(W_Iz_{i,k}+b_I),
\qquad
v_j=\operatorname{normalize}(W_Th_j^T+b_T),
\qquad u_{i,k},v_j\in\mathbb{R}^{d}.
$$

其中 $z_{i,k}$ 是图片 $I_i$ 的第 $k$ 个输出 query。图文相似度为：

$$
\boxed{
s_{ij}=\frac{1}{\tau}\max_{1\le k\le N_q}u_{i,k}^{\top}v_j
}
$$

即先计算各个 query 与文本的相似度，再取最大值；不是先把所有 query 平均成一个图像向量。

为演示，假设某张图片只保留 $3$ 个 query，它们与同一文本的相似度为 $0.2$、$0.8$、$0.4$，则聚合后的相似度是 $0.8$，再除以温度 $\tau$。这个例子只解释 max 聚合，原论文配置仍是 $32$ 个 query。

由此还可以看出：**同一张图片面对不同候选文本，获得最高相似度的 query 可以不同。** 这不等于每个 query 已经拥有可命名、互不重叠的物体语义。

#### 4.2 双向对比损失，与 BLIP 的队列版本区分

为展示配对监督，暂时忽略 label smoothing，并假设每个 batch 样本只有一个已知正配对：

$$
\mathcal{L}_{\mathrm{ITC}}
=-\frac{1}{2B}\sum_{i=1}^{B}
\left[
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ij})}
+
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ji})}
\right].
$$

它分别问：图片对应哪段文本，文本对应哪张图片？

BLIP-2 明确使用 **in-batch negatives，而不是原始 BLIP 的动量队列**。冻结视觉编码器后，训练可以容纳更大的 batch；官方实现会跨设备汇集当前 batch 的候选特征。

实现上，常规预训练 ITC 使用 $0.1$ 的 label smoothing；带 `image_id` 的检索微调路径还会处理同一图片对应多个正样本。因此，上面的 one-hot 公式是机制展开，不是逐行复刻所有训练分支。**均匀 label smoothing 也不是 BLIP 中由动量教师产生的软目标。** 参见 [官方第一阶段模型](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)。

### 5. ITM：联合看图文，但分类的是 query 输出

#### 5.1 为什么不能直接复用 ITC 的输出？

ITC 中 $Z(I)$ 不读取候选文本；ITM 中开放 query–text 双向 self-attention，得到：

$$
Z^{\mathrm{ITM}}(I_i,T_j)
\in\mathbb{R}^{N_q\times d_q}.
$$

现在 query 可以结合 “running on grass” 或 “sleeping on a sofa” 去读取图片，所以输出依赖当前图文配对，不能对所有候选文本只预计算一次。

与原始 BLIP 取 `[Encode]` 文本表示不同，BLIP-2 把**每个输出 query**送入二分类线性 head，再平均 logits：

$$
g_{ij,k}=W_{\mathrm{ITM}}z_{ij,k}^{\mathrm{ITM}}+b_{\mathrm{ITM}}
\in\mathbb{R}^{2},
\qquad
\bar g_{ij}=\frac{1}{N_q}\sum_{k=1}^{N_q}g_{ij,k}.
$$

$$
\pi_{ij}=\operatorname{softmax}(\bar g_{ij})_{\mathrm{matched}},
\qquad
\ell_{ij}^{\mathrm{ITM}}
=-y_{ij}\operatorname{log}\pi_{ij}
-(1-y_{ij})\operatorname{log}(1-\pi_{ij}).
$$

这里 $y_{ij}\in\{0,1\}$。注意是**先平均 logits，再 softmax**，不是把各 query 的 matched 概率平均；由于 softmax 非线性，两种操作通常不等价。

#### 5.2 Hard negatives：仍然优先采样容易混淆的错配

对狗图片而言，“狗在沙发上睡觉”通常比“飞机起飞”更容易混淆。

BLIP-2 沿用 ITC 相似度引导的难负例采样：排除已知正例，让相似度高的错误配对更容易被抽中，而不是总选最高分负例。官方代码为每个本地 batch 样本构造正配对、负图片配对、负文本配对；若本地 batch size 为 $b$，ITM 共处理 $3b$ 个配对。

这里 $b$ 不要与跨设备对比候选数 $B$ 混为一谈；ITM 也不是对全部 $B^2$ 个组合都执行联合编码。参见 [官方 ITM 与采样实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)。

### 6. ITG：为什么“让 Q-Former 写 caption”能训练视觉瓶颈？

#### 6.1 文本不能绕过 query 直接读图

ITG 的概率分解为：

$$
p_{\theta_q}(T\mid I)
=\prod_{t=1}^{L}p_{\theta_q}(t_t\mid t_{<t},Z(I)).
$$

这里 $Z(I)$ 是对 query 视觉信息通道的简写；实际交互发生在 Q-Former 各层的 self-attention 中，并不是只把最后一层 $Z$ 再送入一个完全独立的文本网络。

ITG 的重要约束是：

$$
\text{图像特征}
\rightarrow\text{query 隐状态}
\rightarrow\text{文本隐状态}
\rightarrow\text{下一个 token}.
$$

文本不能直接读取冻结视觉编码器输出。于是，要正确生成 running、grass 等内容，query 通道就需要保留相应视觉信息。这也是为什么 ITG 不只是附带训练一个小 captioner：**它在约束输出给后续 LLM 的视觉表示应该包含什么。**

不过，文本前缀本身也能提供语言先验，因此训练目标只是在鼓励利用图像，不能保证每个词都严格由视觉证据决定。

#### 6.2 Teacher forcing 与 ITG loss

用 `[DEC]` 标记解码任务，训练过程可以理解为：

| 已知条件 | 下一个目标 |
| --- | --- |
| 图片 + `[DEC]` | a |
| 图片 + `[DEC] a` | dog |
| 图片 + `[DEC] a dog` | running |
| 图片 + `[DEC] a dog running` | on |
| 图片 + `[DEC] a dog running on` | grass |

这里仍将单词近似看成 token，实际 tokenizer 可能拆分子词。

忽略实现中的平滑与具体归约方式，基础生成交叉熵为：

$$
\mathcal{L}_{\mathrm{ITG}}
=-\frac{1}{N_{\mathrm{tok}}}
\sum_{(i,t)\in\Omega}
\operatorname{log}p_{\theta_q}(t_{i,t}\mid t_{i,<t},I_i),
$$

其中 $\Omega$ 是有效目标 token 位置集合，$N_{\mathrm{tok}}=|\Omega|$，padding 不作为目标。

与 BLIP 相通的是 next-token prediction；不同的是，**视觉信息必须先经过 query 瓶颈，文本侧不再直接 cross-attend 到全部视觉 token。**

### 7. 第二阶段：将 query 输出变成 LLM 的 soft visual prompts

#### 7.1 线性投影只负责接入口，语义对齐需要训练

设 LLM 的 token embedding 维度为 $d_\ell$，将最终 query 输出投影为：

$$
U=ZW_P+\mathbf{1}_{N_q}b_P^\top
\in\mathbb{R}^{N_q\times d_\ell},
\qquad
W_P\in\mathbb{R}^{d_q\times d_\ell},
\qquad b_P\in\mathbb{R}^{d_\ell}.
$$

若文本 token embeddings 为 $E_T\in\mathbb{R}^{L\times d_\ell}$，则沿序列维度拼接：

$$
X_{\mathrm{LLM}}=\operatorname{Concat}_{\mathrm{seq}}(U,E_T)
\in\mathbb{R}^{(N_q+L)\times d_\ell}.
$$

$U$ 就是 **soft visual prompts**：

- 是连续向量，不是先解码成 “dog、grass” 再转为 token IDs。
- 不要求每个向量对应词表中的某个单词。
- 数量是 query 数量，不是所有原始图像 patch 的数量。
- 拼接位置在 LLM 输入 embedding 层，不是在输出 logits 后面。

可以把第一阶段理解成学习“哪些视觉信息值得传过去”，第二阶段理解成学习“怎样表达这些信息，冻结 LLM 才能利用”。**维度相同只是接口条件，生成 loss 才提供适配这个特定 LLM 的训练信号。**

#### 7.2 Decoder-only LLM：以 OPT 为例

OPT 接收视觉前缀与文本，使用自回归语言建模：

$$
\mathcal{L}_{\mathrm{stage2}}^{\mathrm{OPT}}
=-\sum_{t=1}^{L}
\operatorname{log}p_{\theta_\ell}(t_t\mid U,t_{<t}).
$$

公式省略 batch 与 token 平均。$\theta_\ell$ 是冻结的 LLM 参数；$U$ 则依赖可训练的 Q-Former 与投影层。

视觉前缀没有要预测的离散 token ID，因此不对这些位置构造词表分类标签。官方实现把视觉前缀、padding，以及配置中不需要预测的文本 prompt 的目标设为忽略值，训练后面的目标文本。参见 [官方 OPT 接入实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_opt.py)。

#### 7.3 Encoder-decoder LLM：以 FlanT5 为例

FlanT5 的输入路径不能照搬 OPT。论文采用 prefix language modeling，将配对文本分为：

$$
T=(T_{\mathrm{prefix}},T_{\mathrm{suffix}}).
$$

- **Encoder 输入**：视觉提示 $U$ + 文本前缀的 embeddings。
- **Decoder 目标**：生成文本后缀。

$$
\mathcal{L}_{\mathrm{stage2}}^{\mathrm{T5}}
=-\sum_{t=1}^{L_s}
\operatorname{log}p_{\theta_\ell}
\left(t_t^{s}\mid U,T_{\mathrm{prefix}},t_{<t}^{s}\right).
$$

其中 $t_t^s$ 是后缀的第 $t$ 个 token，$L_s$ 是后缀长度。训练时 decoder 使用真实后缀的右移序列，encoder 则不接收目标后缀。

所以，**不是所有 BLIP-2 都在 decoder 的输入端拼同一条视觉 + 文本序列**：OPT 的视觉提示进入 decoder-only 模型；FlanT5 的视觉提示进入 encoder。参见 [原论文第 3.3 节](https://arxiv.org/abs/2301.12597)与[官方 FlanT5 接入实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_t5.py)。

#### 7.4 第一阶段的小文本分支，不等于第二阶段的大语言模型

第一阶段 Q-Former 的文本分支来自 BERT-base 初始化；第二阶段接入的是 OPT 或 FlanT5，它们是另一套独立的模型，也有自己的 tokenizer 与词表。

在官方基础生成实现中，第二阶段只保留 Q-Former 的 query 视觉提取路径，移除不使用的文本 embedding、文本 FFN 与语言输出 head。**被移除的是不用的分支，不是把整个 Q-Former 冻结或丢弃。** query 专用路径和投影层仍要继续训练。

这也解释了为什么论文写完整 Q-Former 约有 $188$ million 参数，但 Table 2 中不同生成模型的可训练参数约为 $103$--$108$ million：应区分完整第一阶段模块与具体第二阶段生成配置，不能把 $188$ million 无条件写成每个 BLIP-2 checkpoint 的训练参数量。参见上述 [OPT 实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_opt.py)和[FlanT5 实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_t5.py)。

### 8. 梯度与参数更新：冻结 LLM，为什么还能训练 Q-Former？

#### 8.1 冻结参数，不等于阻断对输入的梯度

以第二阶段为例，计算路径是：

$$
I\rightarrow E_{\theta_v}(I)
\rightarrow F_{\theta_q}(Q_0,H^I)
\rightarrow U
\rightarrow\operatorname{LLM}_{\theta_\ell}
\rightarrow\mathcal{L}.
$$

即使 $\theta_\ell$ 固定，损失仍然会随输入 $U$ 变化，因此可以计算：

$$
\frac{\partial\mathcal{L}}{\partial\theta_q}
=\frac{\partial\mathcal{L}}{\partial U}
\frac{\partial U}{\partial Z}
\frac{\partial Z}{\partial\theta_q}.
$$

冻结的 LLM 相当于一个固定但可微的函数。训练改变的是“怎样给这个固定函数提供输入”，不是“这个函数内部的权重”。对 query embeddings $Q_0$ 和投影参数也同样回传梯度。

这里应说 **LLM 参数不参与优化器更新**，而不是声称它对参数的数学导数必然为零。

#### 8.2 实现中的关键陷阱：不要把训练用 LLM 放进 `no_grad`

- 视觉骨干之前没有需要训练的图像输入模块时，可将冻结视觉骨干前向视为不需要构建反向图的特征提取。
- 但第二阶段的 LLM 前面有可训练的 Q-Former 与投影层，必须保留损失对视觉提示的梯度。
- 因此，**把 LLM 权重设为 `requires_grad=False`，不等于给整个训练用 LLM 前向套 `torch.no_grad()`。** 后者会切断回到桥接模块的路径。

另外，`eval()` 主要控制 dropout 等运行行为，不等同于冻结参数或关闭 autograd。这些是上述计算图直接带来的实现含义；官方生成训练路径也没有用 `no_grad` 包住 LLM 前向，而推理用 `generate` 可以关闭梯度。

#### 8.3 哪些模块会更新？必须说清训练阶段

| 模块 | 第一阶段预训练 | 第二阶段预训练 | 论文中的下游微调 |
| --- | --- | --- | --- |
| 视觉编码器骨干 | 冻结 | 冻结 | Captioning、VQA、检索中会更新 |
| Query embeddings | 更新 | 更新 | 更新 |
| Q-Former 有效分支 | 更新 | 更新 query 视觉提取路径 | 按任务更新相应分支 |
| ITC / ITM / ITG 输出模块 | 按目标更新 | 不作为基础 LLM 生成路径的输出模块 | 检索会使用第一阶段相关模块 |
| Q-Former 到 LLM 的投影 | 尚未用于这一阶段 | 更新 | 在使用 LLM 的任务中参与适配 |
| 外部 LLM | 不接入 | 冻结 | Captioning、VQA 中仍冻结；检索不需要 LLM |

实现中还要留意视觉骨干外侧的 LayerNorm 等小型适配参数：官方 `ln_vision` 不在冻结 ViT 参数的循环内。因此，“冻结视觉编码器”首先指其预训练骨干，不代表视觉路径上的每一个附加参数都不更新。

**不要把“BLIP-2 预训练冻结两端”扩展成“BLIP-2 在任何阶段都冻结视觉编码器”。** 原论文明确在下游任务微调中更新视觉骨干。

#### 8.4 冻结节省什么，又不节省什么？

冻结大模型能减少对应的参数梯度、优化器状态和权重更新开销，但：

- 冻结权重仍要载入设备，仍要执行前向计算。
- 第二阶段仍需要通过 LLM 计算输入梯度，训练并不是只运行一个小 Q-Former。
- $32$ 个视觉提示缩短了 LLM 所需接收的视觉序列，但并未删掉图像编码器，也未免除 Q-Former 读取视觉特征的工作。

因此，论文的“更少可训练参数”不能直接换算成相同比例的推理加速、显存降低或总参数减少。

### 9. 数据准备：BLIP-2 仍用 CapFilt，但实现不是照搬原始 BLIP

论文使用约 $129$ million 张图片，来源包括 COCO、Visual Genome、CC3M、CC12M、SBU，以及 LAION400M 中的 $115$ million 张图片。

针对网络图片，数据处理流程为：

1. 用 BLIP-large captioning 模型为每张图片生成 $10$ 条描述。
2. 将生成描述与原始网络描述放到一起。
3. 用 CLIP ViT-L/14 的图文相似度排序。
4. 每张图片保留排名最高的 $2$ 条描述。
5. 每次预训练使用该图片时，从保留描述中随机取一条。

这仍属于“生成更多可用描述，再筛选监督”的思路，但**这里用的是 CLIP 相似度排序保留，不是原始 BLIP 中独立 ITM filter 的 matched / unmatched 二分类流程**。

还要区分两个层面：

- **数据自举**：用已有 captioner 和相似度模型准备训练图文对。
- **模型能力自举**：用冻结视觉模型与冻结 LLM，通过 Q-Former 建立跨模态连接。

前者发生在数据准备阶段，不是第二阶段每次调用 LLM 时重新执行的在线步骤。参见 [原论文第 3.4 节](https://arxiv.org/abs/2301.12597)。

### 10. 从预训练到使用：不是所有任务都调用 LLM

#### 10.1 零样本图像问答：视觉提示后接自然语言问题

基础零样本生成路径可概括为：

$$
I\rightarrow H^I\rightarrow Z(I)\rightarrow U(I),
\qquad
(U(I),\text{问题 prompt})\rightarrow\text{LLM 答案}.
$$

论文对 OPT 使用 `Question: {} Answer:`，对 FlanT5 使用 `Question: {} Short answer:`。

**在这里，问题主要作为 LLM 的文本输入；不能默认问题已经输入 Q-Former，指导它重新找图像区域。** “LLM 根据问题使用视觉信息”与“Q-Former 根据问题提取视觉信息”是不同位置的条件化。

这里的 zero-shot 指没有用对应 VQA 任务标注来微调这一生成模型；不是说视觉模型和 LLM 没有经过任何预训练，也不是说 FlanT5 没有文本指令训练。

#### 10.2 有监督 VQA 微调：额外让 Q-Former 读取问题

论文在 VQA 微调时，为了提取更相关的视觉信息，额外把问题 token 送入 Q-Former，使它们通过 self-attention 与 queries 交互：

$$
Z(I,T_{\mathrm{question}})
=F_{\theta_q}(Q_0,H^I,T_{\mathrm{question}}).
$$

然后，LLM 同时接收投影后的 query 输出与问题，生成答案。此时更新视觉编码器与 Q-Former，LLM 保持冻结。

所以，“Q-Former 不能读任何文本”也是错误的：**能否读文本，要看任务路径；第一阶段 ITM 和论文 VQA 微调都允许文本参与 query 交互。** 参见 [原论文 VQA 微调部分及附录架构](https://arxiv.org/abs/2301.12597)。

#### 10.3 Image captioning：让 LLM 生成描述

论文在 COCO 上微调 captioning，使用 `a photo of` 作为文本提示，以真实 caption 构造生成交叉熵，更新视觉编码器与 Q-Former，同时保持 LLM 冻结。

生成阶段不需要每个 token 都额外计算 ITC 或 ITM。这些目标主要塑造第一阶段的表示，不是最终写 caption 时必须同步执行的筛选器。

#### 10.4 图文检索：使用第一阶段模型，不需要外接 LLM

检索任务直接使用第一阶段预训练模型，在 COCO 上联合微调视觉编码器与 Q-Former，训练目标仍是 ITC + ITM + ITG。

推理分两步：

1. 用独立 query 图像表示与文本表示的相似度召回候选。
2. 对 $k=128$ 个候选执行 ITM 联合编码重排。

虽然最终输出不是句子，ITG 在检索微调中仍有帮助，因为它继续约束 query 保留与文本有关的信息。后面的消融截图专门检验了这一点。

### 11. 最后串起来：一个完整的心智模型

#### 11.1 跟着同一张狗图片走一遍

1. **取监督**：图片与 “a dog running on grass” 配对，配对关系提供 ITC / ITM 标签，文本提供生成目标。
2. **冻结视觉提取**：ViT 输出视觉 token，骨干权重不更新。
3. **训练 query 读取信息**：同一组可学习 query embeddings 进入 Q-Former，与当前图像特征交互，产生这张图片的 query 表示。
4. **ITC 学可比性**：query 不看文本，文本不看 query，利用最高 query–text 相似度辨认配对。
5. **ITM 学细粒度匹配**：query 与完整文本双向交互，区分奔跑与睡觉、草地与沙发。
6. **ITG 学信息保留**：文本不能直接读图，必须利用 query 通道预测 caption。
7. **连接冻结 LLM**：投影 query 输出，变成 LLM 输入空间中的连续视觉前缀。
8. **通过 LLM 训练接口**：LLM 生成真实 caption 或后缀的 loss，沿输入梯度更新 Q-Former 与投影层。
9. **按任务选择路径**：生成任务用 LLM；检索用第一阶段表示与匹配能力；有监督 VQA 还可加入问题条件化。

#### 11.2 与原始 BLIP 对照：保留了什么，替换了什么？

| 维度 | 原始 BLIP | BLIP-2 |
| --- | --- | --- |
| 主要问题 | 统一图文理解与生成，并改进数据 | 高效复用现成视觉模型与 LLM |
| 核心结构 | ViT + MED | 冻结 ViT + Q-Former，生成阶段再接冻结 LLM |
| 预训练视觉骨干 | 在线分支通过梯度更新 | 两阶段预训练均冻结 |
| 图文对齐 | 图像 CLS 与文本 CLS 对齐 | 多个 query 输出与文本 CLS 比较，取最高相似度 |
| 对比候选 | 动量特征与队列 | 当前 batch 候选，可跨设备汇集 |
| 细粒度匹配 | 文本任务 token 的融合表示分类 | 融合后的各 query logits 平均再分类 |
| 生成时读取图像 | MED 文本通过 cross-attention 直接读视觉 token | Q-Former 先读图；文本或 LLM 经 query 通道获得视觉信息 |
| 外部大语言模型 | 不作为原始框架的核心组件 | 第二阶段明确复用冻结 LLM |
| 数据处理 | Captioner + ITM Filter | BLIP 生成描述 + CLIP 相似度排序保留 |

最值得记住的两行是：

$$
\boxed{
\text{第一阶段：让 query 学会提取与语言有关的视觉信息}
}
$$

$$
\boxed{
\text{第二阶段：让这些信息能被冻结 LLM 用来生成文本}
}
$$

所以，BLIP-2 不是简单的“BLIP 后面接一个更大的 decoder”，也不是“ViT 后面加一层线性投影就结束”。**Q-Former 的视觉瓶颈与两阶段训练共同承担跨模态适配。**

## Pipeline Figure

![[_assets/images/BLIP-2-2301.12597-01-qformer-attention-masks.png|900]]

原论文 Figure 2，展示 Q-Former 架构与第一阶段的三种训练模式。左侧雪花表示视觉编码器冻结，query 通过 cross-attention 读取图像；右侧灰色表示禁止读取，白色表示允许读取。

读图时注意右边的顺序是 **ITM → ITG → ITC**。图中的文本分支属于 Q-Former，**不是外部 OPT / FlanT5**；第二阶段才会把 query 输出投影后接到 LLM。

## Experiments

### 1. 预训练配置：高效是相对大规模端到端训练而言

原论文报告：

- 第一阶段训练 $250{,}000$ steps；第二阶段训练 $80{,}000$ steps。
- 第一阶段 ViT-L / ViT-g 的 batch size 分别为 $2{,}320$ / $1{,}680$。
- 第二阶段 OPT / FlanT5 的 batch size 分别为 $1{,}920$ / $1{,}520$。
- 预训练图片分辨率为 $224\times224$。
- 最大配置 ViT-g + FlanT5-XXL 在一台含 $16$ 张 A100、每张 $40$ GB 的机器上，第一阶段少于 $6$ 天，第二阶段少于 $3$ 天。

这些数字是论文特定硬件与实现的报告，不是任意机器上的训练承诺，也不是说整个预训练可以忽略大型模型的算力成本。

### 2. 零样本 VQA：视觉接口有效，但收益依赖任务与骨干

![[_assets/images/BLIP-2-2301.12597-02-zero-shot-vqa.png|900]]

阅读 Table 2 时，先区分 `#Trainable Params` 与 `#Total Params`。例如 ViT-g + FlanT5-XXL 的可训练参数为 $108$ million，而总参数为 $12.1$ billion。

- 该配置的 VQAv2 test-dev 得分为 $65.0$，Flamingo80B 为 $56.3$。论文将其差距报告为 $8.7\%$；按表中的评分尺度，应理解为 **$8.7$ 个百分点**，不是相对提升百分比。
- 论文摘要的“少 $54$ 倍可训练参数”使用完整第一阶段 Q-Former 的约 $188$ million 与 Flamingo 的 $10.2$ billion 对比；它不是依据上述 $108$ million 直接得到的，也不是总参数或推理延迟对比。
- 在 OK-VQA 上，BLIP-2 该配置为 $45.9$，Flamingo80B 为 $50.6$，因此不能说 BLIP-2 在所有视觉问答测试上都领先。

作者观察到更强视觉骨干、更大同系列 LLM、经过指令训练的 FlanT5 往往有利于 VQA。但表中也有个别指标不是单调增加，不能推广成“任何任务只要换更大 LLM 就必然更好”。所有比较均指论文发表时的实验设置。参见 [原论文第 4.1 节](https://arxiv.org/abs/2301.12597)。

### 3. 为什么要第一阶段，而不是从一开始只用 LLM loss？

论文 Figure 5 比较了是否先做视觉语言表征学习。去掉第一阶段后，OPT 与 FlanT5 的零样本 VQA 表现都明显更低；OPT 路径还出现训练继续进行、VQA 表现反而下降的现象。

这支持两阶段设计的动机：**先把 query 训练成有语言相关性的视觉接口，再让它适配冻结 LLM，比仅依赖生成监督从头打通接口更有效。**

作者将 OPT 的退化称为 catastrophic forgetting，但这里 LLM 权重仍然冻结。解读时应区分“视觉条件下系统表现退化”与“LLM 权重被更新而遗忘”：不能仅凭曲线认定 LLM 内部权重受到了破坏，也不能把这个消融扩展成“所有单阶段生成式连接方法都无效”。

### 4. Captioning：NoCaps 的 zero-shot，是在 COCO 微调之后迁移

![[_assets/images/BLIP-2-2301.12597-03-captioning-results.png|900]]

Table 3 同时展示 COCO 微调后的测试，以及向 NoCaps 的零样本迁移。FlanT5-XL 配置在 NoCaps overall 上报告 CIDEr $121.6$、SPICE $15.8$。

这里的 `NoCaps Zero-shot` **不表示模型从未做过 captioning 微调**：模型先在 COCO 上微调，只是没有再用 NoCaps 训练。

表中的可训练参数约为 $1.1$ billion，也不与前面“冻结两端”矛盾，因为 captioning 微调解冻了视觉编码器。看效率数字时必须先确认它属于预训练还是下游微调。

### 5. 检索与 ITG 消融：生成监督也能帮助非生成任务

![[_assets/images/BLIP-2-2301.12597-04-retrieval-results.png|900]]

Table 5 中的 BLIP-2 检索路径先在 COCO 微调，再迁移到 Flickr30K，不需要外接 LLM。评测同时包含图像到文本、文本到图像两个方向，R@1、R@5、R@10 分别检查正确对象能否出现在相应数量的前排候选中。

![[_assets/images/BLIP-2-2301.12597-05-itg-ablation.png|900]]

Table 6 比较的是 **COCO 检索微调阶段的训练目标**。在 ITC + ITM 基础上加入 ITG，论文展示的检索指标得到改善。

它支持“生成目标有助于 query 保留语言相关视觉信息”的解释，但不是直接证明每个 query 都学会了独立概念，也不是针对两个预训练阶段是否都必要的消融。**ITG 微调消融与 Figure 5 的第一阶段消融，回答的是两个不同问题。**

## Limitations & Caveats

### 论文明确报告的限制

- **多模态 in-context learning 没有自然出现**：作者给 LLM 提供上下文 VQA 示例后，没有观察到 VQA 提升，并将其与预训练样本只包含单个图文配对、缺少多图文交错序列联系起来。
- **生成可能出错**：LLM 的知识错误、不恰当的推理过程，以及未能识别新图像内容等，都可能造成不可靠输出。
- **继承冻结 LLM 的风险**：包括偏见、冒犯性语言与潜在隐私泄露；冻结本身不是安全保证。参见 [原论文 Limitation](https://arxiv.org/abs/2301.12597)。

### 根据架构应保留的理解边界

- **信息瓶颈不保证无损**：固定数量的 queries 强迫选择信息，并不保证细小文字、密集物体或所有空间关系都被完整保存。
- **能跟随文本提示，不等于经过完整多模态指令对齐**：这里主要复用 LLM 原有的语言能力，不能直接把示例中的对话表现理解成可靠的通用视觉助手。
- **Q-Former 不是必然的目标定位器**：注意力能分配视觉读取权重，不等于每个 query 对应一个真实对象。
- **这是图像语言预训练论文**：虽然笔记位于 Video-MLLM 目录，其实验不能直接证明原始 BLIP-2 已具备显式时序建模或长视频理解能力。

这些边界用于防止过度解读，不是在没有实验的情况下断言 BLIP-2 在某个具体数据集上一定失败。

## Open Questions / Follow-ups

下面是值得继续验证的问题，而不是原论文已经给出的结论：

1. **Query 数量如何影响信息损失与开销？** 固定 $32$ 个向量面对高分辨率、密集文字或复杂场景时，应怎样评估是否构成过强瓶颈？
2. **在哪一层加入问题条件最有效？** 只让 LLM 读取 question，与让 Q-Former 提前根据 question 取图像信息，各自改变了什么？
3. **两阶段收益来自哪些因素？** 应分别检查 ITC、ITM、ITG 的贡献，而不能把所有收益都归因于结构中出现了 cross-attention。
4. **从单图走向视频还缺什么？** 除了逐帧提取 query 表示，还需要检验帧顺序、时间位置与跨帧交互是否被模型真正利用。

最后可以把 BLIP → BLIP-2 的变化记成：

> **BLIP：训练一套能对齐、能判断、能生成的图文模型，再让它改进数据。**
>
> **BLIP-2：保留已有视觉与语言模型的能力，先训练一个会取信息的桥，再训练这个桥与冻结 LLM 沟通。**

## Citation

- [BLIP-2 原论文](https://arxiv.org/abs/2301.12597)：Junnan Li、Dongxu Li、Silvio Savarese、Steven Hoi，*BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models*。
- [ICML 正式论文页面](https://proceedings.mlr.press/v202/li23q.html)：会议发表信息与正式版本。
- [官方 LAVIS / BLIP-2 项目](https://github.com/salesforce/LAVIS/tree/main/projects/blip2)。
- [第一阶段模型与损失](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_qformer.py)：query–text 相似度、label smoothing、ITM 采样与聚合、ITG、总损失。
- [Q-Former 网络实现](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/Qformer.py)：self-attention、query 视觉 cross-attention 与 query 专用子层。
- [OPT 接入](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_opt.py)与[FlanT5 接入](https://github.com/salesforce/LAVIS/blob/main/lavis/models/blip2_models/blip2_t5.py)：冻结 LLM、分支裁剪、线性投影和生成监督。
- 本地原论文：[[07-MultiModal/Video-MLLM/assets/paper_2301.12597.pdf]]。
- 衔接笔记：[[07-MultiModal/Video-MLLM/BLIP：从图文对齐到理解、生成与数据自举.md]]。

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
