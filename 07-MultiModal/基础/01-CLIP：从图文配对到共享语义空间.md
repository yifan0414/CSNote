---
updated: 2026-09-13
---

![[_assets/images/clip-01-training-framework.drawio.svg|900]]

> **CLIP 用天然的图文配对作为监督信号，通过图像编码器和文本编码器得到共享空间中的向量，再用 batch 内的双向对比交叉熵联合训练两个编码器、投影层和温度参数。**

理解 CLIP，可以沿着四个问题展开：

| 核心问题       | 简要答案                                                                |
| ---------- | ------------------------------------------------------------------- |
| 监督信号从哪里来？  | 互联网中“哪张图片和哪段文字天然配对”的关系                                              |
| 网络如何表示图文？  | Image Encoder + Text Encoder，各自经过 projection，映射到同一个 embedding space |
| Loss 如何构造？ | 把 batch 内的配对识别转成双向分类，使用 softmax + cross entropy                     |
| 哪些参数会更新？   | 两个编码器、两个投影层，以及 temperature / logit scale，全部联合训练                     |

下文依次解释：**配对监督 → 双编码器 → 相似度矩阵 → 双向损失 → 梯度与参数更新 → batch 大小与语义学习**。

## 1. 监督信号：图文配对，而不是固定类别标签

假设从互联网收集到一对数据 $(I_1,T_1)$：

- 图片 $I_1$：一只狗在草地上跑。
- 文本 $T_1$：“a dog running on grass”。

监督信号就是它们的**配对关系**：$I_1\leftrightarrow T_1$。不需要额外给图片标注 `class = dog`，只需要知道“这张图片和这段文字本来就在一起”。

因此，CLIP 与传统 ImageNet 式监督的区别是：

- **CLIP：image–text correspondence**，学习图片与自然语言描述的对应关系。
- **传统分类：image–class label**，学习图片与固定类别标签的对应关系。

对于包含 $B$ 对图文的 batch：

$$
(I_1,T_1),(I_2,T_2),\dots,(I_B,T_B),
$$

训练目标将候选配对分为：

$$
\begin{aligned}
I_i\leftrightarrow T_i &\quad \text{正样本},\\
I_i\leftrightarrow T_j,\quad j\ne i &\quad \text{负样本}.
\end{aligned}
$$

这里的“负样本”是指**训练中被当作不匹配的候选**，不代表它们在语义上一定无关。例如，同一个 batch 中也可能出现两张狗的图片及相近描述。

## 2. 网络架构：两个编码器，映射到同一个空间

### 2.1 整体结构与符号

CLIP 包含图像编码器 $f_{\theta_{\mathrm{vision}}}$ 和文本编码器 $g_{\theta_{\mathrm{text}}}$，两侧分别经过线性投影：

$$
\begin{aligned}
I_i
&\xrightarrow{f_{\theta_{\mathrm{vision}}}} h_i^I
\xrightarrow{W_I} z_i^I,\\
T_j
&\xrightarrow{g_{\theta_{\mathrm{text}}}} h_j^T
\xrightarrow{W_T} z_j^T.
\end{aligned}
$$

其中：

- $h_i^I$、$h_j^T$：各自编码器输出的整体表示。
- $W_I$、$W_T$：图像侧与文本侧的投影参数。
- $z_i^I,z_j^T\in\mathbb{R}^{d}$：投影后的 embedding，处于同一个 $d$ 维空间，供后续比较。

### 2.2 图像侧：以 ViT 为例

原始 CLIP 的图像编码器有 ResNet 和 ViT 两类版本。以 ViT 为例，简化流程为：

$$
\text{Image}
\rightarrow \text{patches}
\rightarrow \text{ViT}
\rightarrow h_{\mathrm{CLS}}
\xrightarrow{W_I} z_i^I.
$$

也就是：将图片切成 patches，经过 ViT 后取代表整张图片的 CLS 表示，再投影得到图像 embedding。

### 2.3 文本侧：Transformer 编码整体文本

例如，“a dog running”经过 tokenizer 得到 token 序列，再由 Text Transformer 编码：

$$
\text{“a dog running”}
\xrightarrow{\text{tokenizer}} (t_1,t_2,\dots,t_N)
\xrightarrow{\text{Text Transformer}} (h_1,h_2,\dots,h_N).
$$

随后，取代表整段文本的位置的 hidden state，并经过 $W_T$ 得到 $z_j^T$。原始实现具体取 **EOT（文本结束 token）位置**的表示，而不是随意取某个 token。参见 [CLIP 官方实现：encode_text](https://github.com/openai/CLIP/blob/main/clip/model.py#L312-L324)。

到这里，图文已经变成可以直接比较的两个向量；两侧不需要使用相同的编码器结构。

## 3. 相似度：归一化、矩阵与温度

### 3.1 归一化后，用余弦相似度比较

先对投影后的 embedding 做 $L_2$ 归一化：

$$
\bar z_i^I=\frac{z_i^I}{\lVert z_i^I\rVert_2},
\qquad
\bar z_j^T=\frac{z_j^T}{\lVert z_j^T\rVert_2}.
$$

此时两个向量的模长都是 $1$，因此点积就是余弦相似度。将其除以温度 $\tau>0$，得到用于分类的 logit：

$$
s_{ij}
=\frac{(\bar z_i^I)^\top\bar z_j^T}{\tau}
=\frac{\operatorname{cos}\theta_{ij}}{\tau},
$$

其中 $\theta_{ij}$ 是两个 embedding 的夹角。

**注意区分：余弦相似度是 $(\bar z_i^I)^\top\bar z_j^T$；$s_{ij}$ 是经过温度缩放后的分数。** 下文将由 $s_{ij}$ 组成的矩阵简称为相似度矩阵。

### 3.2 一个 batch 形成相似度矩阵

$B$ 张图片与 $B$ 段文字两两比较，得到 $S\in\mathbb{R}^{B\times B}$。

以 $B=3$ 为例：

$$
S=
\begin{bmatrix}
s_{11}&s_{12}&s_{13}\\
s_{21}&s_{22}&s_{23}\\
s_{31}&s_{32}&s_{33}
\end{bmatrix}.
$$

- 第 $i$ 行：图片 $I_i$ 与所有候选文本的匹配分数。
- 第 $j$ 列：文本 $T_j$ 与所有候选图片的匹配分数。
- $s_{12}$：图片 $I_1$ 与文本 $T_2$ 的分数。
- 对角线 $s_{11},s_{22},s_{33}$：天然配对的正样本分数。

训练希望得到的**相对大小关系**是：

$$
\begin{bmatrix}
\boxed{\text{高}}&\text{低}&\text{低}\\
\text{低}&\boxed{\text{高}}&\text{低}\\
\text{低}&\text{低}&\boxed{\text{高}}
\end{bmatrix}.
$$

若 $B=4$，矩阵就扩展为：

$$
S=
\begin{bmatrix}
\boxed{s_{11}}&s_{12}&s_{13}&s_{14}\\
s_{21}&\boxed{s_{22}}&s_{23}&s_{24}\\
s_{31}&s_{32}&\boxed{s_{33}}&s_{34}\\
s_{41}&s_{42}&s_{43}&\boxed{s_{44}}
\end{bmatrix},
$$

正确配对仍然是对角线 $s_{11},s_{22},s_{33},s_{44}$。例如，给定 $I_1$，在 $T_1,T_2,T_3,T_4$ 中应选出 $T_1$。下面统一用 $B=3$ 演示损失计算。

### 3.3 Temperature：控制 softmax 有多尖锐

假设一张图片与候选文本的余弦相似度为：

$$
[0.8,0.7,0.5].
$$

- 当 $\tau=1$ 时，logits 仍是 $[0.8,0.7,0.5]$，softmax 分布比较平缓。
- 当 $\tau=0.1$ 时，logits 变成 $[8,7,5]$，softmax 分布会更尖锐。

因此，**在余弦相似度固定时，较小的温度会放大分数差异**，使模型更强烈地区分正样本与难负样本（hard negatives）。它不会改变候选的排序，但会改变概率分布和训练梯度。

CLIP 通过可学习的对数尺度参数 $a$ 实现温度缩放：

$$
\alpha=\operatorname{exp}(a)=\frac{1}{\tau},
\qquad
s_{ij}=\alpha(\bar z_i^I)^\top\bar z_j^T.
$$

在官方代码中，参数 `self.logit_scale` 存储的是 $a$，真正乘到相似度上的是 `self.logit_scale.exp()`，即 $1/\tau$。所以“对比得多尖锐”也会被学习；不能直接把存储的对数参数与 $1/\tau$ 混为一谈。参见 [CLIP 官方实现：forward](https://github.com/openai/CLIP/blob/main/clip/model.py#L325-L338)。

## 4. 双向对比损失：把配对识别变成分类

### 4.1 为什么对比学习可以看成分类？

先看图片 $I_1$ 对应的第一行：

$$
[s_{11},s_{12},s_{13}].
$$

它回答的是：“给定 $I_1$，$T_1,T_2,T_3$ 中哪段文字与它匹配？”

可以把候选文本暂时当成类别：类别 $1$ 对应 $T_1$，类别 $2$ 对应 $T_2$，类别 $3$ 对应 $T_3$。由于 $I_1\leftrightarrow T_1$，正确的类别索引为 $1$，one-hot 标签为 $y_1=[1,0,0]$。

与普通分类相比：

- **普通分类**：候选类别是固定的 cat、dog、car 等，模型输出各类别的 logits。
- **CLIP 的 batch 内分类**：候选“类别”是当前 batch 的文本 $T_1,T_2,T_3$，logits 来自图片与候选文本的相似度。

两者都可以使用 softmax + CE；区别在于**类别如何定义，以及 logits 如何产生**。因此，图像到文本的对比学习可以理解为 **in-batch classification：在当前 batch 的 $B$ 个文本中识别正确配对**，也可以解释为用图片检索文本。

### 4.2 单个样本：从 logits 到 softmax，再到 CE

假设第一行的分数是：

$$
[s_{11},s_{12},s_{13}]=[2.0,1.0,0.2].
$$

经过行方向的 softmax：

$$
p_{1j}=P(T_j\mid I_1)
=\frac{\operatorname{exp}(s_{1j})}
{\operatorname{exp}(s_{11})+\operatorname{exp}(s_{12})+\operatorname{exp}(s_{13})},
$$

得到：

$$
[p_{11},p_{12},p_{13}]
\approx[0.65,0.24,0.11],
\qquad
p_{11}+p_{12}+p_{13}=1.
$$

即模型在当前候选集合中，给 $T_1,T_2,T_3$ 分配的概率约为 $65\%$、$24\%$、$11\%$。

真实标签是 $y_1=[1,0,0]$，因此单个样本的交叉熵为：

$$
\ell_1=-\operatorname{log} p_{11}.
$$

- 若 $p_{11}=0.65$，则 $\ell_1=-\operatorname{log} 0.65$，仍然不够小。
- 若 $p_{11}=0.99$，则 $\ell_1=-\operatorname{log} 0.99$，损失就很小。

降低损失会推动 $p_{11}\rightarrow1$，也就是让 $s_{11}$ **相对于** $s_{12},s_{13}$ 更大。

> **CLIP 不要求正确配对的分数达到某个固定值，而是要求它明显高于其他候选。这就是“对比”的含义。**

### 4.3 图像到文本：每一行做分类

对于任意图片 $I_i$，正确文本都是 $T_i$：

$$
p_{ii}=P(T_i\mid I_i)
=\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ij})}.
$$

对整个 batch 的单样本损失取平均：

$$
\boxed{
\mathcal{L}_{I\rightarrow T}
=-\frac{1}{B}\sum_{i=1}^{B}
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ij})}
}
$$

这个式子可以直接读成：

> 对每一张图片 $I_i$，在当前 batch 的 $B$ 段文字中，把自己的正确文本 $T_i$ 分类出来。

其 softmax 分母来自**同一行**，目标是让对角元素相对于该行其他元素更大。这既是 Image → Text classification，也是 Image → Text retrieval。

### 4.4 文本到图像：每一列再做分类

反过来看文本 $T_1$，候选图片的分数是第一列：

$$
[s_{11},s_{21},s_{31}],
$$

正确答案是 $I_1$。一般地：

$$
q_{ii}=P(I_i\mid T_i)
=\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ji})}.
$$

因此：

$$
\boxed{
\mathcal{L}_{T\rightarrow I}
=-\frac{1}{B}\sum_{i=1}^{B}
\operatorname{log}\frac{\operatorname{exp}(s_{ii})}{\sum_{j=1}^{B}\operatorname{exp}(s_{ji})}
}
$$

这次 softmax 分母来自**同一列**，目标是让每段文本在所有候选图片中找回自己的正确图片。

| 方向 | 条件与候选 | softmax 范围 | 优化目标 |
| --- | --- | --- | --- |
| $I\rightarrow T$ | 给定图片，在文本中选择 | 同一行 | 对角元素相对于该行其他元素更大 |
| $T\rightarrow I$ | 给定文本，在图片中选择 | 同一列 | 对角元素相对于该列其他元素更大 |

### 4.5 为什么两个方向不重复？

**按行选对，不等于按列也能选对。** 行方向损失直接约束“图片找文本”，列方向损失则补上“文本找图片”。双向不是构造对比损失的数学必要条件，而是原始 CLIP 为对称地学习两种检索方向所采用的设计。

先看一个“某个文本对很多图片都很高”的例子：

$$
S=
\begin{bmatrix}
10&0&0\\
9&8&0\\
9&0&8
\end{bmatrix}.
$$

$T_1$ 对多张图片都得到高分，像一个“万能匹配文本”。不过，这个例子中第 $2$、$3$ 行本来就已经选错了，因为 $9>8$；因此它**不能单独证明行方向正确、列方向仍可能错误**。

更直接的反例是：

$$
S=
\begin{bmatrix}
10&0&0\\
11&20&0\\
0&0&20
\end{bmatrix}.
$$

- **按行看**：每一行的最大值都在对角线上，所有图片都能找到正确文本。
- **按列看**：第一列为 $[10,11,0]$，文本 $T_1$ 会错误地选中图片 $I_2$，而不是 $I_1$。

所以需要区分两个问题：

> 不仅图片要找到自己的文本，文本也要找到自己的图片。

双向损失促使对角元素同时在各自行、列中占优，从两个方向强化 batch 中的一一配对关系；它并不是显式的一对一分配算法。

### 4.6 最终损失与标签矩阵

CLIP 将两个方向的损失取平均：

$$
\boxed{
\mathcal{L}_{\mathrm{CLIP}}
=\frac{1}{2}
\left(\mathcal{L}_{I\rightarrow T}+\mathcal{L}_{T\rightarrow I}\right)
}
$$

因此称为 **symmetric contrastive loss（对称对比损失）**。原始论文描述了这一双向交叉熵目标，参见 [CLIP 论文第 2.3 节](https://arxiv.org/html/2103.00020v1#S2.SS3)。

当 $B=3$ 时，配对标签可以写成单位矩阵：

$$
Y=
\begin{bmatrix}
1&0&0\\
0&1&0\\
0&0&1
\end{bmatrix}.
$$

这表示“对角线是正确配对”，**不表示相似度矩阵 $S$ 本身必须等于单位矩阵**。实际优化的是行、列 softmax 后的分类概率。

## 5. 梯度机制：CE 如何自动拉近正样本、推远负样本？

### 5.1 从交叉熵对 logit 的梯度看

对于 softmax + CE，有熟悉的梯度形式：

$$
\frac{\partial\ell}{\partial s_j}=\hat y_j-y_j.
$$

也就是“**模型预测 − 真实标签**”。这与用 softmax + CE 理解 Word2Vec 或普通分类 loss 时的数学结构相通。

继续看图片 $I_1$：

$$
y_1=[1,0,0],
\qquad
\hat y_1=[p_{11},p_{12},p_{13}].
$$

**正样本 $T_1$：**

$$
\frac{\partial\ell_1}{\partial s_{11}}=p_{11}-1<0.
$$

**负样本 $T_2$、$T_3$：**

$$
\frac{\partial\ell_1}{\partial s_{12}}=p_{12}>0,
\qquad
\frac{\partial\ell_1}{\partial s_{13}}=p_{13}>0.
$$

为直观理解梯度方向，暂时把 logits 看成可以独立更新的量，令学习率为 $\eta>0$：

$$
\begin{aligned}
s_{11}&\leftarrow s_{11}-\eta(p_{11}-1)
&&\Rightarrow s_{11}\uparrow,\\
s_{12}&\leftarrow s_{12}-\eta p_{12}
&&\Rightarrow s_{12}\downarrow,\\
s_{13}&\leftarrow s_{13}-\eta p_{13}
&&\Rightarrow s_{13}\downarrow.
\end{aligned}
$$

因此，正配对分数被推动增大，负配对分数被推动减小。负样本进入 softmax 的分母后，自然参与竞争，**不需要再额外构造 $\mathcal{L}_{\mathrm{pull}}$ 或 $\mathcal{L}_{\mathrm{push}}$**。

实际训练更新的是共享网络参数，而不是逐项独立修改 $s_{ij}$；上面的写法用于解释损失对每个 logit 的直接优化倾向，不保证一次参数更新后所有分数都严格按箭头变化。

### 5.2 分数变化，为什么对应向量的“拉近 / 推远”？

归一化后：

$$
\lVert\bar z_i^I\rVert_2=\lVert\bar z_j^T\rVert_2=1,
\qquad
(\bar z_i^I)^\top\bar z_j^T=\operatorname{cos}\theta_{ij}.
$$

**在温度 $\tau$ 固定时**：

$$
\begin{aligned}
s_{ii}\uparrow
&\Longleftrightarrow\operatorname{cos}\theta_{ii}\uparrow
\Longleftrightarrow\theta_{ii}\downarrow,\\
s_{ij}\downarrow
&\Longleftrightarrow\operatorname{cos}\theta_{ij}\downarrow
\Longleftrightarrow\theta_{ij}\uparrow,
\quad j\ne i.
\end{aligned}
$$

因此，“拉近 / 推远”具体指的是 **embedding 方向与夹角的变化**，而不是靠增大向量模长来提高点积。

例如，狗图片与对应的狗文本匹配分数偏低时，损失会推动它们的 embedding 方向更接近；同一 batch 内的 car、cat 等负文本也参与竞争，使狗图片与这些负文本的匹配受到抑制。

由于 CLIP 同时学习温度，**logit 增大并不总能单独证明夹角减小**：尺度变化也能改变 logit。几何上的拉近与推远，应看归一化 embedding 的余弦相似度。

## 6. 参数更新：两侧共同学习，而不是单方面追赶

### 6.1 原始 CLIP 预训练会训练哪些参数？

需要区分：

- **CLIP 自身预训练**：图像编码器和文本编码器都参与训练。
- **下游使用预训练 CLIP**：例如 LLaVA 的常见训练设置中，可以冻结 CLIP 视觉编码器；这是下游的训练策略，不能反推 CLIP 自身预训练时也是冻结的。

以 ViT 版 CLIP 为例，参与学习的参数包括：

| 部分 | 参与训练的参数 |
| --- | --- |
| 图像输入表示 | Patch projection $W_{\mathrm{patch}}$、CLS embedding $x_{\mathrm{CLS}}$、positional embeddings |
| 图像 Transformer | 注意力中的 $W_Q,W_K,W_V$，MLP 中的 $W_1,W_2$，以及编码器内其他可学习参数 |
| 图像投影 | Image projection $W_I$ |
| 文本输入表示 | Token embedding $E_{\mathrm{token}}$、positional embeddings |
| 文本 Transformer | 注意力中的 $W_Q,W_K,W_V$、FFN 参数，以及编码器内其他可学习参数 |
| 文本投影 | Text projection $W_T$ |
| 相似度缩放 | 对数尺度参数 $a$，等价地控制 $\tau=\operatorname{exp}(-a)$ |

表中两侧的同名符号是各自参数的通用记法，**不表示图像和文本编码器共享这些权重**。

整体可训练参数集合写为：

$$
\Theta=
\left\{
\theta_{\mathrm{vision}},
\theta_{\mathrm{text}},
W_I,W_T,a
\right\}.
$$

若按温度来描述，也可以用 $\tau$ 代替 $a$；二者只是参数化方式不同，不是两个独立的温度参数。这里 $\theta_{\mathrm{vision}}$、$\theta_{\mathrm{text}}$ 分别表示投影层之外的编码器参数。

### 6.2 梯度如何同时流向两个编码器？

因为：

$$
s_{ij}=\frac{(\bar z_i^I)^\top\bar z_j^T}{\tau},
$$

损失对 $s_{ij}$ 的梯度会同时传给图像和文本 embedding，再经过归一化操作、投影层，回到各自编码器：

$$
\begin{aligned}
\mathcal{L}_{\mathrm{CLIP}}
&\rightarrow S
\rightarrow \bar z_i^I
\rightarrow z_i^I
\rightarrow W_I
\rightarrow \text{ViT},\\
\mathcal{L}_{\mathrm{CLIP}}
&\rightarrow S
\rightarrow \bar z_j^T
\rightarrow z_j^T
\rightarrow W_T
\rightarrow \text{Text Transformer}.
\end{aligned}
$$

温度对应的对数尺度参数 $a$ 也通过分数计算获得梯度。

> **不是让 image embedding 单方面追着固定的 text embedding 跑，而是图像空间和文本空间一起调整，共同形成 shared semantic space。**

## 7. Batch 大小：为什么负样本数量重要？

CLIP 的负样本来自 batch 内部。对于每张图片，候选文本共有 $B$ 段，其中 $1$ 段是配对文本，其余 $B-1$ 段被当作负样本；文本到图像方向同理。

| Batch size | 每张图片的候选文本数 | 每张图片的负文本数 |
| --- | --- | --- |
| $B=4$ | $4$ | $3$ |
| $B=32{,}768$ | $32{,}768$ | $32{,}767$ |

当任务从“在 $4$ 段文字中找出正确文本”，变成“在 $32{,}768$ 段文字中找出正确文本”时，候选竞争更充分，也更可能遇到难负样本，从而推动模型学习更有区分力的语义表示。

原始 CLIP 采用了 $32{,}768$ 的大 batch，这与其 batch 内对比学习机制密切相关。参见 [CLIP 论文第 2.5 节](https://arxiv.org/html/2103.00020v1#S2.SS5)。

这也是理解后续 SigLIP 修改损失函数的重要背景：SigLIP 改用逐对的 sigmoid loss，不需要 softmax 式的全局相似度归一化，并研究了 batch 大小与训练效果的关系；其结果也表明，在较小 batch 下可以获得更好的表现。参见 [SigLIP 论文](https://arxiv.org/abs/2303.15343)。

## 8. 语义从哪里来：配对任务中的共享因素

训练数据会不断出现类似关系：

- 狗图片 ↔ “dog”。
- 不同品种的狗 ↔ “dog”。
- 狗跑步的图片 ↔ “dog running”。

为了持续降低图文匹配损失，视觉编码器需要从毛发、背景、视角等变化中，找出更稳定、更有助于匹配文本的信息，例如“狗”这一语义因素。文本编码器也会在这样的训练过程中学习 dog、puppy、golden retriever 等表达之间的关系。

于是，共享空间中可能出现如下**语义邻近关系**：

$$
\text{dog image}
\approx \text{“a dog”}
\approx \text{“a puppy”},
$$

同时与 “airplane” 等不相关描述保持较远距离。这里的 $\approx$ 表示 embedding 在语义上接近，而不是向量严格相等；这是大量数据和共同训练形成的可能结构，不是每个 batch 都直接规定的标签。

所以，CLIP 真正学习的是：

> **通过 image–text correspondence，寻找两种模态之间共享的语义因素。**

这不等于训练中没有人类语义：文字本身就承载了人类提供的信息。关键在于，CLIP 不需要额外拿到固定类别的 `dog` 标签，而是从“这张图片对应这句话”的海量监督中，学出可用于图文匹配的语义结构。

## 9. 最后串起来：一个完整的心智模型

1. **构造监督**：取 $B$ 对天然配对的图文，对角线是正样本，其余候选被当作负样本。
2. **编码与比较**：两个编码器分别生成表示，经投影、归一化和温度缩放，形成 $S\in\mathbb{R}^{B\times B}$。
3. **双向分类**：每一行做一次 $B$ 分类，每一列再做一次 $B$ 分类，然后平均两个方向的交叉熵。
4. **联合更新**：CE 对 logits 的梯度产生拉近正样本、推远负样本的倾向，并回传到两个编码器、投影层和尺度参数。
5. **形成语义空间**：图像与文本表示共同调整，从大量配对关系中学习跨模态共享的语义。

从损失构造看，CLIP 并没有神秘的“对比算子”，而是熟悉的：

$$
\boxed{\text{Similarity}+\text{Softmax}+\text{Cross Entropy}}
$$

真正的变化在于，它把“类别”重新定义成了：**当前 batch 里，哪个样本才是我的正确配对对象？** 这也说明，理解这类训练方法的关键，首先是理解监督信号如何构造。

---

## 附录 A. Prior、Bias 与 Variance：理解 CLIP 的 zero-shot / few-shot

正文解释了 CLIP 如何通过图文配对学出共享语义空间。接下来的问题是：**已有这个空间后，为什么直接用文本构造分类器，有时比用少量标注图片训练分类器还好？**

可以借助 prior、bias 与 variance 理解，但它们不是同一层面的概念：

| 概念 | 回答的问题 | 最简记法 |
| --- | --- | --- |
| Prior（先验） | 接触当前任务的训练数据之前，已经拥有什么知识或假设？ | 以前知道什么 |
| Bias（统计偏差） | 换很多批训练数据、重复训练后，平均预测是否偏离目标？ | 平均来说偏不偏 |
| Variance（估计方差） | 换一批训练数据，学出来的预测函数会变化多大？ | 换数据以后抖不抖 |

**Prior 描述已有的信息或约束；bias 与 variance 描述学习方法在重复采样下的统计性质。** 强 prior 不等于高 bias，也不自动保证低 variance；关键是先验是否匹配任务，以及方法如何使用它。

### A.1 Prior：下游任务开始之前，CLIP 已经知道什么？

假设当前任务要识别 dog。随机初始化的模型尚未从数据中学会“狗长什么样”；预训练 CLIP 则已经通过大量图文配对，学到了狗的视觉特征与相关词语之间的联系。

因此，对当前下游任务而言，预训练得到的知识就是一种 **learned prior（学得的先验）**：它来自过去的训练，而不是当前任务新提供的少量标注图片。

沿用正文的符号，令 $P(c)$ 表示类别 $c$ 的文本 prompt。例如，$P(\mathrm{dog})$ 是 “a photo of a dog”。经过文本编码器、投影和归一化，得到：

$$
w_c=\bar z^T(P(c))\in\mathbb{R}^{d}.
$$

这里 $\bar z^T(P(c))$ 就是正文的归一化文本 embedding，只是把输入文本明确写成了类别描述。它可以直接充当类别 $c$ 的分类权重。对图片 $I$：

$$
s_c(I)=\frac{(\bar z^I(I))^\top w_c}{\tau},
\qquad
\hat c(I)=\operatorname{argmax}_{c}s_c(I).
$$

这仍然是正文第 3 节的图文相似度计算，只不过候选文本不再来自预训练 batch，而是来自**下游类别名称与描述**。这种用文本生成分类器的方式，参见 [CLIP 论文第 3.1.2 节](https://arxiv.org/html/2103.00020v1#S3.SS1.SSS2)。

所以，$w_{\mathrm{dog}}$ 不是用当前任务的 dog 标注图片拟合出来的，而是借助预训练知识和类别描述构造出来的：

> **Zero-shot 不是没有知识，而是不需要用当前任务的标注图片训练分类器。**

这里的 prior 是迁移学习语境中的宽泛说法，不意味着 CLIP 显式维护了贝叶斯参数先验分布 $p(\Theta)$。另外，随机初始化也不等于完全没有先验：网络结构、损失函数等仍然包含归纳偏置，只是尚未学得上述语义知识。

### A.2 Bias：平均预测是否系统性地偏离目标？

先用标量预测说明。固定输入 $x$，设目标函数为 $f_*(x)$；从同一目标分布反复抽取相同规模的训练集 $D$，每次按同一学习流程得到 $\hat f_D(x)$。统计偏差定义为：

$$
\operatorname{Bias}(x)
=\mathbb{E}_D[\hat f_D(x)]-f_*(x).
$$

它关心的不是“某一次实验碰巧预测错了”，而是：**重复很多次后，平均预测仍然往某个方向偏。**

放回 CLIP，可以用一个假设性的歧义例子理解：当前任务中的 crane 专指鸟类“鹤”，但 prompt “a photo of a crane” 没有消除 crane 的“起重机”词义。如果这种歧义让文本 embedding 系统性地偏离所需的鸟类概念，换一批下游训练图片也不会自动修正固定的 zero-shot 分类器。

另一个可能来源是细粒度类别：即使 prompt 写成 “a photo of a Siberian husky”，语言描述对应的语义方向，也未必准确匹配当前数据集区分相近犬种所需要的视觉决策边界。

这两个例子用于说明**语义先验与目标任务不匹配时可能产生的系统性误差**，不是对具体类别错误的实测结论，也不能只凭一个错误样本就断定统计偏差的大小。

> **这里的 bias 指统计偏差，不是线性层中的偏置参数，也不是社会公平语境中的偏见；归纳偏置则是方法预先采用的假设，与统计偏差也不完全是一回事。**

### A.3 Variance：换一批训练样本，预测会抖多大？

在相同的重复采样设定下，固定输入 $x$ 的估计方差为：

$$
\operatorname{Var}_D[\hat f_D(x)]
=\mathbb{E}_D\left[
\left(\hat f_D(x)-\mathbb{E}_D[\hat f_D(x)]\right)^2
\right].
$$

注意，这里**固定的是待预测输入，变化的是训练集**。它不是比较不同测试图片上的输出差异，也不是查看一次预测的类别概率分布有多分散。

例如，做 $1$-shot 分类，即**每个类别只有 $1$ 张标注训练图片**。其他设置不变，只替换 dog 类的那张图片：

- 第一次：草地上的金毛。
- 第二次：沙发上的黑色贵宾犬。
- 第三次：雪地里的哈士奇。

单张图片同时包含品种、颜色、背景与姿态等信息。仅凭这一张图，学习方法可能难以判断哪些因素真正代表 dog，哪些只是偶然共现。因此，新学出的 dog 类权重 $w_{\mathrm{dog},D}^{\mathrm{LP}}$ 可能随抽样明显变化，同一张测试图片的分类结果也可能随之改变。

这就是 **few-shot 学习可能具有较高 variance** 的直觉：

$$
\text{少量样本的偶然性}
\longrightarrow \text{拟合出的决策边界变化}
\longrightarrow \text{固定测试输入上的预测波动}.
$$

权重变化只是辅助观察，定义上更应关注预测函数的变化；不同权重并不必然导致不同的分类结果。

### A.4 靶子比喻：偏不偏，与稳不稳，是两个问题

把靶心看作目标值，每一箭看作“重新抽训练集、重新训练后，对同一个输入给出的预测”：

| 情况 | 箭的分布 | 直觉 |
| --- | --- | --- |
| Low bias + low variance | 集中在靶心附近 | 准且稳 |
| High bias + low variance | 很集中，但远离靶心 | 稳定地偏 |
| Low bias + high variance | 很分散，但平均位置靠近靶心 | 平均没偏，单次不稳 |
| High bias + high variance | 既偏离靶心，又很分散 | 又偏又不稳 |

因此，“结果很稳定”不等于“结果很准确”；一个固定但不匹配任务的分类器，也可以稳定地出错。

### A.5 回到 CLIP：zero-shot 与 few-shot linear probe 分别依赖什么？

**Zero-shot CLIP：直接使用文本生成的分类权重。**

$$
w_c=\bar z^T(P(c)).
$$

固定预训练 checkpoint、类别集合、prompt、预处理与确定性推理过程后，分类器不使用下游训练集 $D$。因此，仅仅重新抽取下游训练样本，不会改变它：

$$
\operatorname{Var}_D[s_c(I)]=0.
$$

所以这里说“zero-shot variance 很低”，更严格地说，是**相对于下游训练集的重新抽样，固定 zero-shot 预测没有这部分方差**。这不意味着更换预训练数据、checkpoint、prompt，或者重新抽取测试集时，模型或测得的准确率也不变；若用下游样本选择 prompt，这一不依赖 $D$ 的前提也不再成立。

与此同时，文本语义和预训练表示未必完全匹配目标任务，所以低 variance 不排除系统性误差。

**Few-shot linear probe：冻结图像表示，用标注图片拟合新的分类头。**

为了与上面的 zero-shot 形式直接比较，在固定图像特征 $\bar z^I(I)$ 上写成：

$$
\ell_D(I)=W_D^{\mathrm{LP}}\bar z^I(I)+b_D,
\qquad
W_D^{\mathrm{LP}}\in\mathbb{R}^{C\times d},
\quad b_D\in\mathbb{R}^{C},
$$

其中 $C$ 是下游类别数，$\ell_D(I)$ 是各类别的 logits；$W_D^{\mathrm{LP}}$ 是新训练的分类头，**不是正文中预训练的图像投影 $W_I$**。这里使用归一化特征便于解释，具体 linear-probe 实现也可能采用不同的特征预处理。

它仍然保留了 CLIP 图像编码器的视觉先验，并不是从零学习视觉识别；区别在于，普通 linear probe 不直接把文本生成的 $w_c$ 当作类别权重，而是依赖少量标注图片估计 $W_D^{\mathrm{LP}}$ 与 $b_D$。

因此，$1$-shot 时分类头可能对样本选择很敏感。当每类样本数从 $1$ 增加到 $2$、$4$、$8$、$16$ 时，在相同目标分布与合理训练设置下，更多样本通常有助于覆盖类内变化、降低估计的不稳定性并改善泛化；**不保证每次抽样的准确率都单调上升，也不保证所有设置下方差都严格下降**。

| 方法 | 继承的先验 | 分类权重从哪里来？ | 对下游训练集抽样的敏感性 |
| --- | --- | --- | --- |
| Zero-shot CLIP | 预训练视觉表示、文本语义及图文对齐 | 类别名称与 prompt 经文本侧生成 | 固定设置且不使用下游样本时，不随抽样变化 |
| Few-shot linear probe | 预训练视觉表示，以及分类头的模型与正则化假设 | 从各类别的少量标注图片拟合 | 可能较高，取决于样本、特征与正则化等 |

关键不是“有 prior”与“没有 prior”的对比，而是：**类别含义由语言直接指定，还是主要靠少量图片间接推断。**

### A.6 为什么合适的 prior 能像稳定器一样工作？

如果只看到“草地上的金毛”，缺少合适约束的学习方法可能过度依赖草地或毛色。若已有“不同背景、颜色和品种都可能属于 dog”的语义知识，并在学习中保留这种约束，就不容易因为一个特殊样本而大幅改变分类规则。

这就是 prior 可以起到 **regularizer（正则化约束）** 作用的直觉：减少少量样本能够任意推动模型变化的空间。

但需要区分两种情况：

- **Prior 与任务匹配**：既可能降低 variance，也可能改善系统性偏差。
- **Prior 与任务不匹配，且约束过强**：模型虽然更稳定，却可能难以根据新数据纠正错误方向，增加 bias。

因此，经典 bias–variance trade-off 可以作为定性提醒：

$$
\begin{aligned}
\text{更强的约束}
&\Rightarrow \text{variance 往往降低，bias 可能增大},\\
\text{更多的拟合自由度}
&\Rightarrow \text{bias 可能减小，variance 可能增大}.
\end{aligned}
$$

这里说的是**在可比较的学习设置中改变约束强度的常见倾向**，不是“预训练越强，bias 必然越大”的定律；更高质量的先验完全可能让两方面一起改善。

### A.7 如何用这个心智模型读 Figure 6？

CLIP 论文的 Figure 6 比较了 zero-shot 与 few-shot linear probe：在参与该分析的 $20$ 个数据集上，zero-shot CLIP 的平均表现与同一特征空间中的 $4$-shot 线性分类器相当。它是**跨数据集的平均结果**，不能直接读成“ImageNet 上等于 $4$-shot”或“每个数据集上 zero-shot 都更好”。参见 [CLIP 论文 Figure 6 及第 3.1.5 节](https://arxiv.org/html/2103.00020v1#S3.F6)。

本附录给出的定性解释是：**文本提供了有用的类别语义约束，而极少量图片可能不足以稳定地确定类别边界**。这有助于理解“多了少量标注数据，为什么不一定立刻优于 zero-shot”，但不能据此断言观察到的性能差距全部由 variance 导致。

严格的 bias–variance 分解最经典地用于平方误差回归。这里将其用于理解 CLIP 分类，是统计学习的心智模型；Figure 6 展示的是分类性能，**并没有直接计算和分解统计 bias 与 variance，也不能把分类错误率直接写成回归中的平方偏差加方差**。

最后用 dog 例子记住：

> **Prior：在当前任务之前，CLIP 已学得哪些关于 dog 的知识？**  
> **Bias：这些知识与学习方法是否让平均预测系统性地偏离当前任务的目标？**  
> **Variance：把那张 $1$-shot dog 图片换掉，学出的模型对同一测试输入的预测会抖多大？**
