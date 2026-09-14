---
title: "BLIP：从图文对齐到理解、生成与数据自举"
authors: ["Junnan Li", "Dongxu Li", "Caiming Xiong", "Steven Hoi"]
conference: "ICML"
year: 2022
arxiv_url: "https://arxiv.org/abs/2201.12086"
pdf_link: "[[07-MultiModal/Video-MLLM/assets/paper_2201.12086.pdf]]"
cover: "[[_assets/images/BLIP-2201.12086-01-med-architecture.png]]"
created: 2026-09-12
updated: 2026-09-12
tags: ["paper/arxiv", "vlm", "image-text", "pretraining"]
status: "unread"
priority:
rating:
topics: ["MLLM"]
code: "https://github.com/salesforce/BLIP"
---

![[_assets/images/blip-01-med-capfilt-framework.drawio.svg|900]]

<!-- READ_PAPER_GENERATED_START -->

> **BLIP 用同一套部分共享参数的模型，分别学习“图文是否语义接近”“这对图文是否真正匹配”“看图后下一个词是什么”；再把学到的生成与匹配能力用于补写、过滤训练文本，用改进后的数据预训练新模型。**

理解 BLIP，可以沿着四个问题展开：

| 核心问题 | 简要答案 |
| --- | --- |
| 监督信号从哪里来？ | 图文配对关系，以及配对文本自身的 token 序列；同时使用人工标注数据与网络图文数据 |
| 网络如何表示图文？ | ViT 图像编码器 + MED 文本侧，在独立编码、图文融合编码、图像条件解码之间切换 |
| Loss 如何构造？ | ITC 做跨样本对比，ITM 做图文配对二分类，LM 做图像条件下的 next-token prediction |
| 哪些参数与数据会更新？ | 在线模型联合训练，动量分支通过 EMA 更新；CapFilt 在另一阶段生成、筛选文本，构造新训练集 |

下文依次解释：**配对监督 → 三种运行模式 → ITC 对齐 → ITM 匹配 → LM 生成 → 梯度与参数更新 → CapFilt 数据自举 → 下游使用 → 完整心智模型**。

前置阅读：[[07-MultiModal/Video-MLLM/CLIP：从图文配对到共享语义空间.md]]。

本文讨论的是原始 **BLIP**，不是 BLIP-2。论文全名为 *Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation*。下文的小例子与展开公式用于解释机制；涉及动量分支、参数共享和损失实现的细节，结合原论文与官方代码核对。

## 1. 监督信号：同一对图文，可以构造三种学习任务

### 1.1 从 CLIP 的问题继续往前走

假设数据中有一对 $(I_1,T_1)$：

- 图片 $I_1$：一只狗在草地上跑。
- 文本 $T_1$：“a dog running on grass”。

CLIP 主要问：

> 给定这张图片，在一批文本里，哪段文字是它的配对文本？

BLIP 保留这种**全局对齐**，但还增加两个问题：

> 把图片与某段文字放在一起仔细看，它们是否真正匹配？
>
> 不给完整描述，只给图片和已经写出的前缀，接下来应该写什么？

前一个问题要求模型学习跨模态交互；后一个问题要求模型拥有生成文本的能力。仅仅得到两个相似的向量，并不会自动得到能逐词生成句子的解码器。

### 1.2 三个目标的标签分别是什么？

对于包含 $B$ 对图文的 batch：

$$
\mathcal{B}=\{(I_i,T_i)\}_{i=1}^{B},
\qquad
T_i=(t_{i,1},t_{i,2},\dots,t_{i,L_i}).
$$

可以从同一批数据构造：

| 训练目标 | 给模型什么？ | 要预测什么？ | 标签从哪里来？ |
| --- | --- | --- | --- |
| ITC：Image-Text Contrastive | 图片或文本，以及另一模态的候选集合 | 正确配对对象在候选集合中的位置 | 数据中的配对关系；原始 BLIP 还混入动量模型的软目标 |
| ITM：Image-Text Matching | 一对完整的图片和文本 | matched / unmatched | 原始配对作为正例，采样得到的错配作为负例 |
| LM：Language Modeling | 图片与文本前缀 | 下一个 token | 配对文本中紧随前缀的真实 token |

例如，把 $I_1$ 与另一张图片的文本 “a dog sleeping on a sofa” 配在一起，可以构造一个 ITM 负例；把 “a dog running on grass” 右移一位，就能构造 LM 的输入与目标。

因此，**不需要分别为三个目标人工标注三套标签**。不过，这也不意味着完全没有人工监督：原始 BLIP 的训练数据包含 COCO、Visual Genome 等人工标注图文数据，CapFilt 也会在 COCO 上微调。

### 1.3 天然配对，不等于文本一定正确

网络图片的 alt-text 可能是：

- 与画面相关的描述：“a dog running on grass”。
- 只与网页背景相关的文字：“my weekend diary”。
- 广告、文件名、模板文字，甚至错误描述。

即使数据告诉模型 $I_i\leftrightarrow T_i$，也不能保证 $T_i$ 精确描述了 $I_i$。同样，错配的 $T_j$ 也可能在语义上适用于 $I_i$，形成 false negative。

BLIP 从两个层面处理这个问题：

- **训练目标层面**：ITC 使用动量模型产生软标签，缓和“所有非配对文本都绝对错误”的假设。
- **数据层面**：CapFilt 为图片生成新描述，并过滤原始描述和生成描述中的噪声。

这两个机制相关，但不是同一件事。参见 [BLIP 论文第 3 节](https://arxiv.org/abs/2201.12086)。

## 2. 网络架构：一个视觉编码器，三种文本侧运行模式

### 2.1 MED 不是三个完全独立的模型

BLIP 的核心架构叫 **MED：Multimodal Mixture of Encoder-Decoder**。

它可以运行成：

1. **Unimodal encoder**：图像和文本分别编码，用于 ITC。
2. **Image-grounded text encoder**：文本通过 cross-attention 读取图像，用于 ITM。
3. **Image-grounded text decoder**：文本通过 causal self-attention 和 cross-attention 逐步生成，用于 LM。

![[_assets/images/BLIP-2201.12086-01-med-architecture.png|900]]

上图来自原论文 Figure 2；相同颜色表示共享参数。理解时重点看：**是否启用 cross-attention，以及文本 self-attention 是双向还是因果的。**

| 模式 | 文本 self-attention | 文本是否读取图像 token？ | 主要输出 |
| --- | --- | --- | --- |
| 独立编码 | 双向 | 否 | 图像、文本各自的全局向量 |
| 图文融合编码 | 双向 | 是，通过 cross-attention | 依赖当前图文配对的融合表示 |
| 图像条件解码 | 因果 | 是，通过 cross-attention | 每个位置对下一个 token 的预测分布 |

这里的 mixture 指组合不同编码、解码功能，**不是带路由器的 MoE 专家混合架构**。

### 2.2 图像侧：既保留全局表示，也保留 token 序列

ViT 将图片编码成：

$$
H_i^I=f_{\theta_{\mathrm{vision}}}(I_i)
\in\mathbb{R}^{P\times d_v},
$$

其中 $P$ 表示包含 CLS 在内的视觉 token 总数，$d_v$ 为视觉 hidden size。

它有两种用途：

- **ITC**：取 CLS 表示 $h_{i,\mathrm{CLS}}^I$，投影成全局图像向量。
- **ITM / LM**：把整个 $H_i^I$ 作为 cross-attention 的视觉输入，不只是提供一个 CLS 向量。

因此，BLIP 并不是把所有任务都压缩成“比较两个全局 embedding”。需要检查细节或生成描述时，文本侧能够读取视觉 token 序列。

### 2.3 独立编码：先各自理解，再比较向量

ITC 分支的文本编码与 BERT 类似：

$$
T_j
\xrightarrow{\text{双向 Text Encoder}}
H_j^T\in\mathbb{R}^{L_j\times d_t}
\rightarrow h_{j,\mathrm{CLS}}^T.
$$

这一分支关闭 cross-attention。因此，编码 $T_j$ 时不需要指定它对应哪张图片，编码 $I_i$ 时也不需要指定候选文本。

这正是独立编码适合大规模检索的原因：**候选库里的图片或文本向量可以提前计算，再用向量相似度快速搜索。**

注意与原始 CLIP 的文本侧区分：BLIP 在这里取文本 CLS 表示，而不是 CLIP 的 EOT 表示；BLIP 的这一文本编码模式使用双向注意力。

### 2.4 融合编码：cross-attention 到底融合了什么？

在图文融合模式中，每个文本 Transformer block 的主体可简化为：

$$
\text{双向 Self-Attention}
\rightarrow\text{Cross-Attention}
\rightarrow\text{FFN}.
$$

省略多头拼接、残差和 LayerNorm，单个 cross-attention head 可以写成：

$$
Q_T=H^T W_Q,
\qquad
K_I=H^I W_K,
\qquad
V_I=H^I W_V,
$$

$$
\operatorname{CA}(H^T,H^I)
=\operatorname{softmax}
\left(\frac{Q_TK_I^\top}{\sqrt{d_k}}\right)V_I.
$$

其中 $H^T$ 是当前层文本 self-attention 后的状态，$H^I$ 是视觉编码器输出。若文本长度为 $L$，注意力权重矩阵属于 $\mathbb{R}^{L\times P}$，每个文本位置都可以对视觉 token 分配权重。

- **Query 来自文本**：当前词及其上下文需要什么视觉信息？
- **Key / Value 来自图像**：视觉序列提供哪些可供读取的内容？

例如，要区分 “running on grass” 与 “sleeping on a sofa”，模型可以结合动词、地点和图片细节，而不仅仅确认“图里有狗、句子里也有 dog”。这是架构提供的交互能力，不保证注意力图天然就是准确的目标定位图。

在序列起始处使用任务 token `[Encode]`，其输出表示：

$$
h_{ij}^{\mathrm{fuse}}
=\operatorname{MED}_{\mathrm{enc}}(T_j,H_i^I)_{\mathrm{Encode}}
\in\mathbb{R}^{d_t}.
$$

这个表示同时依赖 $I_i$ 和 $T_j$：**同一句话换一张图片，融合表示也可能变化。** 它不能像独立文本 embedding 那样，对所有图片只预计算一次。

### 2.5 条件解码：不是只把 encoder 换一个名字

LM 分支将文本侧换成 causal self-attention：

$$
\text{Causal Self-Attention}
\rightarrow\text{Cross-Attention}
\rightarrow\text{FFN}.
$$

生成第 $t$ 个 token 时，只能使用此前的文本 token，但可以读取整张图片的视觉特征：

$$
p_\Theta(t_t\mid t_{<t},I).
$$

因果限制针对**文本序列**，并不是要求图像 patch 也按顺序逐个开放。

论文用 `[Decode]` 表示序列起始 token。官方 tokenizer 对应的实际字符串为 `[DEC]`，融合编码的任务 token 为 `[ENC]`；图中的 `[Encode]` / `[Decode]` 是功能记法。参见 [官方 tokenizer 定义](https://github.com/salesforce/BLIP/blob/main/models/blip.py#L186-L191)。

### 2.6 参数如何共享？

MED 的预训练设计是：**文本 encoder 与 decoder 共享除 self-attention 层之外的参数**，包括公共的 embedding、cross-attention 和 FFN 等部分；任务输出头承担各自职责。

- ITC 与 ITM 使用文本 encoder 的双向 self-attention，ITC 不执行 cross-attention。
- LM 使用独立参数的 causal self-attention。
- ITM 与 LM 共享 cross-attention；文本模式之间共享公共的 embedding 和 FFN。

所以，不应把 BLIP 理解成“同一个 self-attention 只换一个 mask，所有权重完全不变”，也不应理解成“三套互不相关的完整网络”。论文的共享策略位于两者之间。参见 [BLIP 论文第 3.1–3.2 节](https://arxiv.org/abs/2201.12086)与[官方参数绑定实现](https://github.com/salesforce/BLIP/blob/main/models/blip_pretrain.py)。

## 3. ITC：先把图文放进可以比较的共享空间

### 3.1 投影、归一化和温度：与 CLIP 相通的部分

两侧分别取全局表示，经过可学习投影：

$$
z_i^I=W_I h_{i,\mathrm{CLS}}^I+b_I,
\qquad
z_j^T=W_T h_{j,\mathrm{CLS}}^T+b_T,
\qquad
z_i^I,z_j^T\in\mathbb{R}^{d}.
$$

然后进行 $L_2$ 归一化：

$$
\bar z_i^I=\frac{z_i^I}{\lVert z_i^I\rVert_2},
\qquad
\bar z_j^T=\frac{z_j^T}{\lVert z_j^T\rVert_2}.
$$

如果暂时只考虑当前 batch，并忽略动量分支，logit 为：

$$
s_{ij}=\frac{(\bar z_i^I)^\top\bar z_j^T}{\tau},
\qquad \tau>0.
$$

与 CLIP 一样，归一化后的点积是余弦相似度；温度控制 softmax 的尖锐程度。

以 $B=3$ 为例，纯 batch 版本的图像到文本分数为：

$$
S=
\begin{bmatrix}
s_{11}&s_{12}&s_{13}\\
s_{21}&s_{22}&s_{23}\\
s_{31}&s_{32}&s_{33}
\end{bmatrix}.
$$

若只用硬标签，正确配对位于对角线；图像到文本方向的单样本损失就是：

$$
\ell_i^{I\rightarrow T}
=-\operatorname{log}
\frac{\operatorname{exp}(s_{ii})}
{\sum_{j=1}^{B}\operatorname{exp}(s_{ij})}.
$$

**这只是帮助从 CLIP 过渡的简化版本，不是原始 BLIP ITC 的全部实现。**

### 3.2 原始 BLIP 还使用动量编码器与特征队列

BLIP 沿用 ALBEF 的思路：

1. **在线编码器**：通过反向传播学习。
2. **动量编码器**：通过在线参数的指数移动平均更新，生成较平滑的特征与软目标。
3. **特征队列**：保存过去 batch 的动量特征，扩充对比候选集合。

为解释形状，考虑单个对比计算中的 $B$ 个在线 query 和长度为 $M$ 的队列。候选集合包含当前 batch 的动量 key 与队列中的历史 key，因此：

$$
S^{I\rightarrow T},S^{T\rightarrow I}
\in\mathbb{R}^{B\times(B+M)}.
$$

这里的 query / key 指**对比学习中的锚点和候选特征**，不是在说这一分支执行了 cross-attention。

记动量侧归一化特征为 $\widetilde z$：

$$
\begin{aligned}
s_{ij}^{I\rightarrow T}
&=\frac{(\bar z_i^I)^\top\widetilde z_j^T}{\tau},\\
s_{ij}^{T\rightarrow I}
&=\frac{(\bar z_i^T)^\top\widetilde z_j^I}{\tau}.
\end{aligned}
$$

由于在线分支、动量分支和历史队列并不相同，**这两个矩阵一般不是同一个矩阵的转置**。不能把 CLIP 的“对同一个方阵按行、按列分类”原封不动套到这里。

官方预训练类默认投影维度为 $256$，队列长度为 $57{,}600$。这些是该实现的设置，不是 BLIP 的数学定义。参见 [官方 ITC 与队列实现](https://github.com/salesforce/BLIP/blob/main/models/blip_pretrain.py)。

### 3.3 软标签：不把所有非配对对象都当成绝对错误

假设某张狗的图片有三个候选描述：

- $T_1$：原始配对描述，讲狗在草地上跑。
- $T_2$：来自另一张图片，但语义非常相近。
- $T_3$：讲飞机起飞。

硬标签为：

$$
y=[1,0,0].
$$

若动量模型给出的候选分布为：

$$
r=[0.7,0.25,0.05],
$$

BLIP 将硬配对标签与该分布混合，构造训练目标：

$$
\widehat y=(1-\alpha)y+\alpha r,
\qquad 0\le\alpha\le1.
$$

例如，为演示取 $\alpha=0.4$：

$$
\widehat y=[0.88,0.10,0.02].
$$

这仍然最偏好天然配对的 $T_1$，但给语义相近的 $T_2$ 留下了一定概率质量。这里的数值只是教学例子，不是论文报告的某个样本。

这个机制并不保证识别所有 false negative；它只是用动量模型的判断缓和纯 one-hot 监督。**动量模型自己也可能判断错误。**

### 3.4 双向软目标交叉熵

令 $p_i^{I\rightarrow T}$ 为在线图像 query 对所有文本 key 的 softmax 分布，$p_i^{T\rightarrow I}$ 为反方向分布；对应软目标分别为 $\widehat y_i^{I\rightarrow T}$ 和 $\widehat y_i^{T\rightarrow I}$。

则损失可展开为：

$$
\boxed{
\mathcal{L}_{\mathrm{ITC}}
=-\frac{1}{2B}\sum_{i=1}^{B}\sum_{j=1}^{B+M}
\left[
\widehat y_{ij}^{I\rightarrow T}\operatorname{log}p_{ij}^{I\rightarrow T}
+\widehat y_{ij}^{T\rightarrow I}\operatorname{log}p_{ij}^{T\rightarrow I}
\right]
}
$$

可以直接读成：

> 两个方向都在候选集合中做分类，但监督分布不再必须是 one-hot，候选也不只来自当前 batch。

另一个实现差异是：BLIP 官方代码直接学习温度参数 `self.temp`，初始化为 $0.07$，并限制在 $0.001$--$0.5$；不是像 CLIP 那样存储 `logit_scale` 再取指数。两者都控制相似度尺度，但参数化方式不同。

## 4. ITM：把图文放在一起，判断是否真正匹配

### 4.1 ITC 已经会匹配，为什么还需要 ITM？

关键区别不是 loss 名字，而是**分数如何产生**：

$$
\begin{aligned}
\text{ITC:}\quad
&(I,T)\rightarrow
\text{两个独立全局向量}
\rightarrow\text{相似度},\\
\text{ITM:}\quad
&(I,T)\rightarrow
\text{带 cross-attention 的联合编码}
\rightarrow\text{匹配分类头}.
\end{aligned}
$$

例如，“狗在草地上跑”和“狗在沙发上睡觉”共享 dog 这一概念，但动作与场景不同。ITM 通过联合编码为这种细粒度区分提供条件。

这不表示 ITC 完全学不到细节，或 ITM 总能判断正确；区别在于，**ITM 的分数直接依赖当前图文之间的 token 级交互**。

### 4.2 从融合表示到二分类

将第 2.4 节的融合表示送入线性分类头：

$$
u_{ij}=W_{\mathrm{ITM}}h_{ij}^{\mathrm{fuse}}+b_{\mathrm{ITM}}
\in\mathbb{R}^{2}.
$$

它输出 unmatched 与 matched 的两个 logits。定义 matched 概率为：

$$
\pi_{ij}
=\operatorname{softmax}(u_{ij})_{\mathrm{matched}}.
$$

若标签 $y_{ij}\in\{0,1\}$，单对图文的交叉熵可以写成二分类形式：

$$
\ell_{ij}^{\mathrm{ITM}}
=-y_{ij}\operatorname{log}\pi_{ij}
-(1-y_{ij})\operatorname{log}(1-\pi_{ij}).
$$

- 正配对的 $y_{ij}=1$，希望 $\pi_{ij}$ 较高。
- 负配对的 $y_{ij}=0$，希望 $\pi_{ij}$ 较低。

例如，模型对一个负配对给出 $\pi_{ij}=0.9$，说明它过于相信两者匹配，负例损失 $-\operatorname{log}(1-0.9)$ 就会很大。

官方实现使用**两个 logits 的 softmax + CE**；上面的二分类写法与它等价，不表示代码使用单个 logit 的 BCE。

### 4.3 Hard negatives：更经常选择那些看起来很像的错配

如果负文本全是“飞机起飞”，模型可能只要看到“狗”就能轻松排除。更有训练价值的负例可能是“狗在沙发上睡觉”：概念相近，却与当前画面不匹配。

BLIP 用 ITC 相似度引导 ITM 的负例采样。在当前 batch 内排除已知正配对后，可以把图像 $I_i$ 的负文本采样分布理解为：

$$
P(j\mid i,\mathrm{negative})
=\frac{\operatorname{exp}(s_{ij}^{I\rightarrow T})}
{\sum_{k\ne i}\operatorname{exp}(s_{ik}^{I\rightarrow T})},
\qquad j\ne i.
$$

这是忽略实现中数值稳定项后的写法。**相似度越高，越可能被抽到；不是每次确定性地选择分数最高的那个负例。** 反方向也可以为文本采样负图片。

在官方预训练实现中，每个 batch 构造：

- $B$ 对正配对 $(I_i,T_i)$。
- $B$ 对“负图片 + 当前文本”。
- $B$ 对“当前图片 + 负文本”。

于是 ITM 对 $3B$ 对图文计算分类损失，而不是对所有 $B^2$ 个组合逐一进行融合编码。这样既利用难负例，又避免对每个候选都运行昂贵的 cross-attention。参见 [官方 ITM 与负例采样实现](https://github.com/salesforce/BLIP/blob/main/models/blip_pretrain.py)。

### 4.4 ITC 与 ITM 的分类对象并不相同

| 对比维度 | ITC | ITM |
| --- | --- | --- |
| 分类问题 | 候选集合中的哪一个更应该配对？ | 当前这对图文是否匹配？ |
| 类别含义 | 不同候选样本 | matched / unmatched |
| 分数来源 | 独立向量相似度 | 图文融合表示 + 分类头 |
| 是否需要图文交互编码 | 否 | 是 |
| 主要使用方式 | 全局对齐、快速召回、负例采样依据 | 精细匹配、候选重排、CapFilt 过滤 |

因此，“它们都在学匹配”不等于“它们做了两遍同一件事”。

## 5. LM：给定图片和前缀，预测下一个 token

### 5.1 生成目标不是再判断一次配对

图像条件语言建模将整段文本的概率分解为：

$$
p_\Theta(T\mid I)
=\prod_{t=1}^{L}p_\Theta(t_t\mid t_{<t},I),
$$

其中目标序列包括结束 token，但不把起始 token 当作要预测的正文。

每一步都在词表 $\mathcal{V}$ 上做分类。例如，已知图片与前缀 “a dog”，模型要预测下一步是 running、sleeping，还是其他 token。

> **ITC 的类别是候选样本，ITM 的类别是匹配状态，LM 的类别是词表 token。它们都能用 CE，但监督问题不同。**

### 5.2 Teacher forcing：训练时前缀来自真实文本

为方便理解，先把单词近似看成 token；真实 tokenizer 还可能把单词拆成 subword。

| 已知图片与真实前缀 | 下一个目标 token |
| --- | --- |
| 图片 + `[Decode]` | a |
| 图片 + `[Decode] a` | dog |
| 图片 + `[Decode] a dog` | running |
| 图片 + `[Decode] a dog running` | on |
| 图片 + `[Decode] a dog running on` | grass |
| 图片 + 完整描述 | 结束 token |

训练时把右移后的输入与目标对齐，在 causal mask 下可以并行计算多个位置的损失；不是必须生成一个词、调用一次网络，再训练下一个词。

推理时没有真实的后续文本，才需要使用模型已经生成的 token 作为下一步前缀。

### 5.3 从词表概率到 LM loss

假设目标 token 是 running，其预测概率为：

$$
p_\Theta(\text{running}\mid\text{a dog},I)=0.2.
$$

忽略 label smoothing，该位置的损失为：

$$
\ell_t^{\mathrm{LM}}=-\operatorname{log}0.2.
$$

如果模型结合图片，把正确 token 的概率提高到 $0.8$，这一项损失就会减小。

设 batch 内所有有效目标 token 的位置集合为 $\Omega$，其大小为 $N_{\mathrm{tok}}$，则基础版本为：

$$
\boxed{
\mathcal{L}_{\mathrm{LM}}
=-\frac{1}{N_{\mathrm{tok}}}
\sum_{(i,t)\in\Omega}
\operatorname{log}p_\Theta(t_{i,t}\mid t_{i,<t},I_i)
}
$$

padding 不参与计算。官方实现先把 padding 目标设为忽略值，再将输出 logits 与目标文本错开一个位置，完成 next-token prediction。

### 5.4 原始 BLIP 还使用 label smoothing

原论文与官方实现对 LM 使用 $\varepsilon=0.1$ 的 label smoothing。设词表为 $\mathcal{V}$，目标 token 对应 one-hot 向量为 $y_t$，则平滑后的目标可写为：

$$
\widetilde y_{t,v}
=(1-\varepsilon)y_{t,v}+\frac{\varepsilon}{\lvert\mathcal{V}\rvert}.
$$

每个位置实际优化的是：

$$
\ell_t^{\mathrm{LM}}
=-\sum_{v\in\mathcal{V}}
\widetilde y_{t,v}\operatorname{log}p_{t,v}.
$$

注意与 ITC 的软目标区分：

- **ITC**：软目标来自动量模型对图文候选的预测，并与硬配对标签混合。
- **LM**：这里的 label smoothing 是把少量概率质量分到整个词表，不是由动量模型提供下一词答案。

### 5.5 LM 不是 MLM，也不是无条件语言模型

- **MLM**：遮住部分 token，通常允许从左右文本上下文恢复它们。
- **BLIP 的 LM**：不能偷看未来文本，但可以看图片，学习从左到右生成。
- **无条件文本 LM**：只依赖文本前缀，没有这里的视觉条件。

所以，BLIP 不是“把图片旁边的句子做一遍 BERT 填空”就获得了 caption 能力，而是明确训练了图像条件下的自回归解码。参见 [论文第 3.2 节](https://arxiv.org/abs/2201.12086)与[官方 LM 损失实现](https://github.com/salesforce/BLIP/blob/main/models/med.py)。

## 6. 梯度与参数更新：三个目标共同塑造同一套能力

### 6.1 最终训练目标

官方预训练代码直接相加三个损失：

$$
\boxed{
\mathcal{L}_{\mathrm{BLIP}}
=\mathcal{L}_{\mathrm{ITC}}
+\mathcal{L}_{\mathrm{ITM}}
+\mathcal{L}_{\mathrm{LM}}
}
$$

这是**同一轮 MED 预训练中的联合目标**，不是先单独训练完 ITC，再训练 ITM，最后才训练 LM。在线 ViT 计算出的视觉 token 可以被多个任务复用；文本侧按不同模式计算相应损失，动量视觉分支则另有无梯度前向。CapFilt 的多阶段流程是另一层组织方式，见第 7 节。参见 [官方预训练循环](https://github.com/salesforce/BLIP/blob/main/pretrain.py)。

### 6.2 CE 的基本梯度仍然是“预测减目标”

对于 softmax logits $u$、预测分布 $p$ 和归一化目标分布 $y$：

$$
\frac{\partial\ell}{\partial u_j}=p_j-y_j.
$$

因此，将停止梯度的 ITC 软目标视为固定分布，并忽略 batch 平均系数：

- **ITC**：梯度是 $p_{ij}-\widehat y_{ij}$。候选获得的概率低于软目标时，会受到增大 logit 的推动。
- **ITM**：匹配类 logit 的梯度是 $\pi_{ij}-y_{ij}$。正配对被推动判为匹配，负配对被推动判为不匹配。
- **LM**：词表 logit 的梯度是 $p_{t,v}-\widetilde y_{t,v}$，推动 token 分布接近平滑后的真实目标。

这也解释了为什么 BLIP 的 ITC 不能一概描述成“所有非对角线都一定被推远”：当某个候选的目标概率不是零时，其直接梯度方向取决于**预测概率与目标概率之差**。

这里说的是损失对 logit 的直接倾向。实际更新的是共享网络参数，不保证每一步更新后每个样本的分数都按单独分析的方向变化。

### 6.3 哪些参数收到哪些损失的梯度？

以下讨论原始 BLIP 的联合预训练，而不是某个下游冻结策略。

| 参数部分 | ITC | ITM | LM |
| --- | --- | --- | --- |
| 在线视觉编码器 ViT | 通过图像对比特征 | 通过视觉 token 被融合读取 | 通过视觉 token 被解码器读取 |
| 文本公共 embedding、FFN 等 | 是 | 是 | 是 |
| 文本 encoder 的双向 self-attention | 是 | 是 | 否 |
| 文本 decoder 的 causal self-attention | 否 | 否 | 是 |
| 共享 cross-attention | 不启用 | 是 | 是 |
| ITC 图像、文本投影层及温度 | 是 | 不通过离散采样反传 | 否 |
| ITM 分类头 | 否 | 是 | 否 |
| LM 输出头 | 否 | 否 | 是，公共绑定权重按共享关系累计梯度 |
| 动量编码器及其投影层 | 不由优化器反传更新 | 不参与该融合分支 | 不参与该生成分支 |

ITM 的负例选择虽然参考 ITC 分数，但官方实现中的采样在无梯度路径中完成。不能因此画出一条“ITM loss → 负例采样概率 → ITC 温度”的可微训练路径。

### 6.4 梯度如何回到图像？

最容易忽略的是：LM 虽然预测的是文本 token，**图像编码器也会收到梯度**。

$$
\begin{aligned}
\mathcal{L}_{\mathrm{ITC}}
&\rightarrow\text{相似度}
\rightarrow\text{在线全局表示与投影}
\rightarrow\text{在线编码器},\\
\mathcal{L}_{\mathrm{ITM}}
&\rightarrow\text{ITM head}
\rightarrow\text{融合表示}
\rightarrow\text{Cross-Attention}
\rightarrow H^I\rightarrow\text{ViT},\\
\mathcal{L}_{\mathrm{LM}}
&\rightarrow\text{词表预测}
\rightarrow\text{条件解码器}
\rightarrow\text{Cross-Attention}
\rightarrow H^I\rightarrow\text{ViT}.
\end{aligned}
$$

例如，模型要预测 running，就需要利用与动作有关的视觉信息；预测错误产生的梯度可以同时调整解码器的读取方式与视觉编码器的表示方式。

但要特别区分 ITC 的实现：图像到文本分支中的**文本 key 是停止梯度的动量特征**，并不在该分支直接更新在线文本编码器；反方向的在线文本 query 分支负责给在线文本编码器提供 ITC 梯度。双向合起来，在线图像与文本编码器都被训练。

### 6.5 动量分支更新，不等于冻结全部编码器

记在线编码器参数为 $\theta$，对应动量参数为 $\theta_m$，则：

$$
\theta_m\leftarrow m\theta_m+(1-m)\theta.
$$

官方预训练类的默认动量系数为 $m=0.995$。

- 在线模型通过优化器更新。
- 动量模型不通过梯度更新，而是通过 EMA 跟随在线参数。
- 特征队列存储特征缓存，不是需要优化器学习的一组参数。

因此，“动量分支不参与反向传播”不意味着“BLIP 的视觉编码器是冻结的”。原始 BLIP 会训练在线视觉编码器；也不是 [BLIP-2](https://arxiv.org/abs/2301.12597) 那种冻结视觉编码器和大语言模型、训练桥接模块的设置。

对于共享参数 $\theta_s$，来自不同任务的梯度按计算图相加：

$$
\nabla_{\theta_s}\mathcal{L}_{\mathrm{BLIP}}
=\nabla_{\theta_s}\mathcal{L}_{\mathrm{ITC}}
+\nabla_{\theta_s}\mathcal{L}_{\mathrm{ITM}}
+\nabla_{\theta_s}\mathcal{L}_{\mathrm{LM}}.
$$

某个任务未使用该参数时，对应项为零。这才是“理解与生成共同训练”的具体含义：不只是三个结果并排输出，而是它们确实约束了部分相同的参数。

## 7. CapFilt：用已经学会的能力，改进下一轮训练数据

### 7.1 为什么光加大数据规模还不够？

更多图文配对可以提供更多概念和场景，但如果文本大量与图片无关，模型仍在用不准确的监督学习。

BLIP 的另一项核心贡献是 **CapFilt：Captioning and Filtering**：

- **Captioner**：看图片，补写新的 caption。
- **Filter**：判断 caption 是否匹配图片，删除不可靠配对。

这利用了前面学到的两种能力：**LM 能写，ITM 能判。** 但不能把它们简单理解成联合预训练网络里的两个 head 当场互相打分；论文会先构造、微调独立的 captioner 与 filter。

### 7.2 完整阶段：先训练能力，再处理数据，再训练新模型

设人工标注数据为 $\mathcal{D}_h$，网络图文数据为 $\mathcal{D}_w$。

1. **初始预训练**：在原始人工标注与网络图文数据上，用 ITC + ITM + LM 训练一个 MED。
2. **构造 Captioner**：从这个预训练 MED 初始化图像条件解码模型，在 COCO 上用 LM 目标微调。
3. **构造 Filter**：从同一个预训练 MED 初始化匹配模型，在 COCO 上用 ITC + ITM 目标独立微调。
4. **生成描述**：Captioner 为每张网络图片生成一条 synthetic caption。
5. **过滤描述**：Filter 检查原始网络文本和 synthetic caption，删除被 ITM head 判为 unmatched 的配对。
6. **重新预训练**：把保留下来的图文对与人工标注图文对合并，预训练一个新的 BLIP 模型。

可以概括为：

$$
\text{原始图文数据}
\rightarrow\text{初始 MED}
\rightarrow\text{独立微调 Captioner / Filter}
\rightarrow\text{改进后的图文数据}
\rightarrow\text{新的 MED}.
$$

“新模型”意味着不直接沿用生成教师的整套 BLIP checkpoint 继续训练；但视觉与文本骨干仍可以使用论文规定的 ImageNet 预训练 ViT、BERT 初始化，**不是说所有权重都必须随机初始化**。论文还比较了继续训练旧模型的方案，其实验没有显示这种做法比重新训练新模型更有优势。

CapFilt 是数据集级的离线处理流程，不是每个 mini-batch 都要重新生成整个数据集，也不是第 $4$ 个直接加到总损失里的 loss。参见 [论文第 3.3 节与第 6 节](https://arxiv.org/abs/2201.12086)。

### 7.3 原始文本与生成文本，都要过滤

对一张网络图片 $I_w$，有：

$$
T_w=\text{原始网页文本},
\qquad
T_s=\operatorname{Captioner}(I_w).
$$

再分别检查：

$$
\operatorname{Filter}(I_w,T_w),
\qquad
\operatorname{Filter}(I_w,T_s).
$$

可能出现：

| 原始文本 | 生成文本 | 进入新训练集的配对 |
| --- | --- | --- |
| 通过 | 通过 | 两种描述都保留 |
| 不通过 | 通过 | 仅保留生成描述 |
| 通过 | 不通过 | 仅保留原始描述 |
| 不通过 | 不通过 | 这张网络图片没有保留下来的这两类文本配对 |

因此，CapFilt 不是“用生成文本一律覆盖原始文本”，也不是“生成出来的内容天然可信”。

若用 $\operatorname{keep}(I,T)\in\{0,1\}$ 表示过滤决定，令 $\mathcal{D}_s$ 为合成配对集合，则新数据可写为：

$$
\mathcal{D}_{\mathrm{boot}}
=\mathcal{D}_h
\cup\{(I,T)\in\mathcal{D}_w:\operatorname{keep}(I,T)=1\}
\cup\{(I,T)\in\mathcal{D}_s:\operatorname{keep}(I,T)=1\}.
$$

这里的并集表示汇集训练样本，不要求每张图片只有唯一的一段文字。

### 7.4 为什么 Captioner 和 Filter 要独立微调？

MED 预训练中的参数共享有助于让理解与生成共同学习；但在 CapFilt 中，captioner 与 filter 是从同一模型初始化后，**分别端到端微调的两个模块**。

如果两者在这一阶段仍紧密共享参数，captioner 产生的错误可能恰好也是 filter 倾向于相信的错误。作者将共享版本表现下降主要归因于 **confirmation bias（确认偏差）**。

要注意，这是一项有实验支持的作者解释，不是证明“独立微调就能消除所有偏差”。它也说明：

> **预训练时共享参数，与数据筛选时让生成器和过滤器解耦，解决的是不同阶段的问题，并不矛盾。**

### 7.5 为什么使用 nucleus sampling，而不只保留最安全的句子？

原论文用 nucleus sampling 为网络图片生成描述，阈值设为 $p=0.9$。它从累积概率达到阈值的高概率 token 集合中采样，而不是固定选择最高概率的完整句子。

论文发现：在该实验中，nucleus sampling 比 beam search 带来更好的下游结果，即使它产生了更多被过滤器拒绝的描述。作者的解释是，较多样的描述可能带来更多新的语义信息。

这不是说“噪声越大越好”，而是说：**在过滤的帮助下，多样性可能比反复生成最常见、最保守的描述更有价值。** 也不能把 filter 的拒绝率直接等同于人工测量的真实错误率。

### 7.6 实验证据：补写与过滤是否真的互补？

![[_assets/images/BLIP-2201.12086-02-capfilt-ablation.png|900]]

阅读上面的 Table 1 时，先固定同一组数据规模与视觉骨干，再比较是否使用 captioner 和 filter。

- 作者报告：仅使用 captioner 或仅使用 filter，都能带来收益；两者结合时效果进一步改善。
- 这支持 CapFilt 的设计：补写描述增加可用监督，过滤则控制原始与合成文本中的噪声。
- 论文还用重复原始文本、对齐训练样本量的消融检查“只是训练更久”的解释，结果支持收益不只是来自延长训练。

这些结论对应论文的特定训练与评测设置，不代表任意数据集、任意生成器都必然得到同样提升。参见 [BLIP 论文第 4 节与第 6 节](https://arxiv.org/abs/2201.12086)。

## 8. 从预训练到使用：对齐、理解和生成如何分工？

### 8.1 Batch 与候选数量：不能只照搬 CLIP 的大 batch 解释

CLIP 的基本对比候选来自当前 batch；BLIP 的 ITC 还使用动量特征队列。因此，要区分：

- 当前一起处理多少对图文。
- ITC 的分母中有多少个候选 key。
- ITM 实际抽取了多少个负配对。
- LM 中有多少个有效目标 token。

这四个数量不是同一个量。以单个对比计算中的 $B$ 和队列长度 $M$ 表示：

- ITC：每个 query 对应 $B+M$ 个候选 key。
- ITM：官方预训练实现构造 $3B$ 个配对分类样本。
- LM：对有效文本 token 求平均，padding 不算。

原论文报告的全局预训练 batch size 为：ViT-B 版本 $2{,}880$，ViT-L 版本 $2{,}400$；预训练 $20$ 个 epoch。其基础数据包含约 $14$ million 张图片，加入额外 LAION 数据后约为 $129$ million 张图片。

这些是论文设置，不要把单卡公式中的 $B$、全局 batch 与队列长度混为一谈；队列保存的是历史特征，也不等价于让所有历史样本同时参与在线反向传播。参见 [论文第 4.1 节](https://arxiv.org/abs/2201.12086)。

### 8.2 图文检索：ITC 先召回，ITM 再重排

图文检索可以分两步：

1. **快速召回**：用独立图像、文本向量的相似度，找出 top-$k$ 候选。
2. **精细重排**：对选出的候选进行图文融合编码，利用 ITM 分数重新排序。

这样不必对整个候选库逐对运行 cross-attention。原论文在 COCO 上使用 $k=256$，在 Flickr30K 上使用 $k=128$；检索微调使用 ITC + ITM。

![[_assets/images/BLIP-2201.12086-03-retrieval-results.png|900]]

上面的 Table 5 是经过对应检索数据集微调后的比较，而不是“所有模型在完全相同设置下直接零样本检索”的结果。它展示了这套预训练及下游使用方式的实际表现，但不能单凭一张表将收益全部归因于某一个 loss。

另外，图中的 `BLIP_CapFilt-L` 表示用更大的 captioner / filter 处理数据，再训练 ViT-B 学生；不要误读成学生模型一定也换成了 ViT-L。

### 8.3 Image captioning：启用图像条件解码器

Captioning 的输入只有图片和可选文本提示，不需要给出完整候选描述：

$$
I\rightarrow H^I
\rightarrow\operatorname{MED}_{\mathrm{dec}}
\rightarrow(t_1,t_2,\dots,t_L).
$$

下游 captioning 微调主要使用 LM loss。训练中的 ITC 与 ITM 并不会在每一步生成时都作为额外的分类程序执行；它们的影响已部分体现在预训练参数里。

还要区分两个场景：CapFilt 生成训练数据时，论文选择 nucleus sampling；下游 captioning 评测则使用 beam search。**制造训练数据的解码策略，不必与最终评测的解码策略相同。**

### 8.4 VQA：先融合图片与问题，再解码答案

VQA 不只是把 question 当作一条 caption 送去做相似度比较。

原论文在微调时重新组织模型：

$$
(I,Q)
\rightarrow\text{图像条件的问题编码器}
\rightarrow\text{图文融合表示}
\rightarrow\text{答案解码器}
\rightarrow A.
$$

训练时用真实答案构造 LM 目标。这个建模方式支持答案生成，但论文报告的 VQA 推理设置还使用解码器对 $3{,}128$ 个候选答案进行排序；不能把“采用生成式建模”直接等同于“所有实验都无约束地自由生成答案”。

这也说明，BLIP 是能灵活迁移到多个任务的预训练框架，不是一个无需任务适配、天然完成所有指令的通用聊天助手。参见 [论文第 5 节与附录](https://arxiv.org/abs/2201.12086)。

### 8.5 视频迁移与能力边界

原论文也测试了从图文任务向视频任务的迁移：均匀采样多帧，将帧特征拼接为序列。检索使用 $8$ 帧，视频问答使用 $16$ 帧。

但作者明确指出，这个简单做法**忽略时序信息**。因此，视频任务上的结果不能说明原始 BLIP 已经显式学会了复杂的动作顺序或长视频推理。

理解其能力时，还要保留几条边界：

- **对齐不等于完全理解**：ITC 与 ITM 都受数据和模型能力限制，可能误判细节。
- **能生成不等于不会幻觉**：LM 学到的是条件文本分布，不提供“每个生成词都可被画面验证”的保证。
- **过滤不等于绝对干净**：filter 的判断仍来自学习到的模型，可能漏掉错误或误删正确描述。
- **原始 BLIP 没有 Q-Former**：不要将其 cross-attention 与 BLIP-2 的桥接结构混为一谈。

这些边界不是否定 BLIP，而是提醒我们：**训练目标提供的是学习方向，不能把方向直接当成无限制的能力保证。**

## 9. 最后串起来：一个完整的心智模型

### 9.1 跟着同一张狗图片走一遍

1. **取得监督**：图片与描述配对，描述本身还提供逐 token 的训练目标。
2. **独立编码并对齐**：ViT 与文本 encoder 产生全局向量，ITC 结合动量特征、队列与软目标，让两种模态进入可比较的空间。
3. **联合编码并判断**：构造正配对与 hard negatives，文本通过 cross-attention 读取视觉 token，ITM 学习判断配对是否匹配。
4. **以图片为条件生成**：decoder 在不能偷看未来文本的条件下，利用图片与真实前缀预测下一个 token，学习描述画面。
5. **联合更新参数**：三个 loss 回传到各自使用的模块，共享参数累计多任务梯度；动量副本通过 EMA 更新。
6. **用模型改进数据**：独立微调 captioner 与 filter，生成新 caption，筛除原始与合成文本中的噪声，再用新数据训练新模型。
7. **按任务选用能力**：检索用独立编码与匹配重排，captioning 用条件解码，VQA 则组合问题编码与答案解码。

### 9.2 与 CLIP 对照，变化发生在哪里？

| 维度 | 原始 CLIP | 原始 BLIP |
| --- | --- | --- |
| 核心表征路径 | 图像、文本独立编码后比较 | 保留独立编码，并增加图文融合与条件解码 |
| 预训练目标 | 双向对比交叉熵 | ITC + ITM + LM |
| 图文交互 | 主要通过全局向量相似度形成训练联系 | ITM / LM 中文本直接 cross-attend 到视觉 token |
| 文本生成 | 原始模型不包含 caption 解码训练 | 明确训练图像条件自回归生成 |
| 对比监督实现 | 当前 batch 的双向配对分类 | 在线 / 动量分支、特征队列、硬软目标混合 |
| 数据改进 | 核心机制是从配对数据学习 | CapFilt 用生成与过滤改进后续预训练数据 |

BLIP 的模型训练可以记成：

$$
\boxed{
\text{ITC：在候选中找对应}
+\text{ITM：看细节判匹配}
+\text{LM：看图片续写文本}
}
$$

而完整框架还必须加上数据层面的：

$$
\boxed{
\text{训练模型}
\rightarrow\text{生成并过滤描述}
\rightarrow\text{构造更好的数据}
\rightarrow\text{训练新模型}
}
$$

所以，BLIP 不只是“CLIP 后面接一个 decoder”。它真正增加的是：**一套兼顾对齐、融合与生成的多任务架构，以及用这些能力反过来改进监督数据的流程。**

如果继续深入，最值得追问的三个问题是：软目标如何影响 false negatives，参数共享如何平衡理解与生成，以及 CapFilt 如何在描述多样性和事实准确性之间取得平衡。它们分别对应监督、模型和数据三个层面。

## 参考资料

- [原始 BLIP 论文与 arXiv 版本](https://arxiv.org/abs/2201.12086)：Junnan Li、Dongxu Li、Caiming Xiong、Steven Hoi，*Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation*。
- [ICML 正式论文页面](https://proceedings.mlr.press/v162/li22n.html)：会议发表信息与正式版本。
- [官方预训练模型实现](https://github.com/salesforce/BLIP/blob/main/models/blip_pretrain.py)：ITC、动量分支、队列、ITM 负例采样、参数共享与三个 loss 的计算。
- [官方 MED 实现](https://github.com/salesforce/BLIP/blob/main/models/med.py)与[预训练循环](https://github.com/salesforce/BLIP/blob/main/pretrain.py)：causal decoding、目标右移、label smoothing 与损失相加。
- 本地原论文：[[07-MultiModal/Video-MLLM/assets/paper_2201.12086.pdf]]。

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
