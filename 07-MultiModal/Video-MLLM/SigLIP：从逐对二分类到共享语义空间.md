---
created: 2026-09-12
updated: 2026-09-12
---

![[_assets/images/siglip-01-pairwise-bce-framework.drawio.svg|900]]

> **SigLIP 保留图像编码器与文本编码器组成的双塔结构，但不再让每张图片在 batch 内做一次 softmax 分类，而是把每个图文候选配对分别当作一道“匹配 / 不匹配”的二分类题，用 sigmoid + binary cross entropy 联合训练两个编码器、表示头、尺度参数和 bias。**

本文沿用 [[07-MultiModal/Video-MLLM/CLIP：从图文配对到共享语义空间.md|CLIP：从图文配对到共享语义空间]] 的组织方式，讨论原始 **SigLIP（Sigmoid Loss for Language Image Pre-Training）**，不展开 SigLIP 2 的后续改动。

理解 SigLIP，也可以沿着四个问题展开：

| 核心问题 | 简要答案 |
| --- | --- |
| 监督信号从哪里来？ | 仍然来自图文天然配对：配对为正，其余候选在训练中被当作负 |
| 网络如何表示图文？ | Image Encoder + Text Encoder，输出同维度、归一化后的 embedding |
| Loss 如何构造？ | 对每个图文候选配对独立计算 sigmoid + BCE，再汇总损失 |
| 哪些参数会更新？ | 两个编码器及其表示头、logit scale，以及新增的可学习 bias |

下文依次解释：**配对监督 → 双编码器 → 相似度、尺度与 bias → 逐对损失 → 梯度与参数更新 → batch 大小与语义学习**。

最重要的区别先记住：

> **CLIP 问：“这些候选里，哪个是正确配对？”SigLIP 问：“眼前这一对，是否匹配？”**

## 1. 监督信号：仍然是图文配对，而不是固定类别标签

假设从互联网得到一对数据 $(I_1,T_1)$：

- 图片 $I_1$：一只狗在草地上跑。
- 文本 $T_1$：“a dog running on grass”。

监督信号仍然是它们的**配对关系**：$I_1\leftrightarrow T_1$。与 CLIP 一样，不需要额外给图片标注 `class = dog`。

对于包含 $B$ 对图文的 batch：

$$
(I_1,T_1),(I_2,T_2),\dots,(I_B,T_B),
$$

将图片与文本两两组合，得到 $B^2$ 个候选配对。用二元标签表示：

$$
y_{ij}=
\begin{cases}
1,&i=j,\quad\text{正样本},\\
0,&i\ne j,\quad\text{负样本}.
\end{cases}
$$

当 $B=3$ 时：

$$
Y=
\begin{bmatrix}
1&0&0\\
0&1&0\\
0&0&1
\end{bmatrix}.
$$

其中共有 $3$ 个正配对和 $6$ 个负配对。注意，原始数据只有 $3$ 对，**不是额外收集了 $9$ 对人工标注数据**；其余候选来自 batch 内的交叉组合。

这里有两个容易混淆的地方：

- **标签来源没有变**：SigLIP 不是把图文配对监督换成了其他监督。
- **标签的用法变了**：CLIP 把一行或一列理解为一道选择题；SigLIP 把矩阵中的每个元素理解为一道判断题。

与 CLIP 一样，非配对不代表语义上一定无关。如果同一个 batch 中有两张狗的图片与相近描述，交叉组合仍可能被标成负样本。因此，**sigmoid loss 不会自动消除 false negatives（假负样本）**。

## 2. 网络架构：仍然是双塔，但不要照搬 CLIP 的所有细节

### 2.1 整体结构与符号

先把完整的图像分支与文本分支写成：

$$
I_i\xrightarrow{f_{\theta_{\mathrm{vision}}}}z_i^I,
\qquad
T_j\xrightarrow{g_{\theta_{\mathrm{text}}}}z_j^T,
$$

其中：

$$
z_i^I,z_j^T\in\mathbb{R}^{d}.
$$

这里的 $f$、$g$ **包含各自的编码器、整体表示提取，以及必要的输出映射**。与前篇把投影层单独写出来的方式相比，这只是记账方式不同。

如果展开，可以抽象为：

$$
\begin{aligned}
\text{Image}
&\rightarrow\text{Vision Transformer}
\rightarrow\text{Pooling / Head}
\rightarrow z_i^I,\\
\text{Text}
&\rightarrow\text{Text Transformer}
\rightarrow\text{Pooling / Head}
\rightarrow z_j^T.
\end{aligned}
$$

关键要求是两侧最终输出相同维度的 embedding，**并不要求每侧都额外放置一个独立的线性 projection**。例如，官方发布模型的演示配置采用图像侧 MAP pooling，并将图像侧额外输出投影设为 `None`；文本侧则映射到对应的 embedding 维度。参见 [官方 SigLIP 演示：模型配置](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/SigLIP_demo.ipynb)。

### 2.2 图像侧：ViT 与整体图像表示

图像先切成 patches，再经过 ViT，得到视觉 token 表示：

$$
I_i
\rightarrow\text{patches}
\rightarrow\text{ViT}
\rightarrow H_i^I,
\qquad
H_i^I\in\mathbb{R}^{N_I\times d_v}.
$$

其中 $N_I$ 是 patch 数量，$d_v$ 是视觉 hidden dimension。

以官方发布模型采用的 **MAP（Multihead Attention Pooling）** 为例，它使用一个可学习的 probe 作为 query，从视觉 tokens 中聚合整张图片的信息，再经过表示头中的处理得到全局向量。参见 [官方 ViT 实现：MAPHead](https://github.com/google-research/big_vision/blob/main/big_vision/models/vit.py#L150-L169)。

因此，不应直接把前篇 ViT 版 CLIP 的“取 CLS，再线性投影”原封不动套过来。需要区分：

- **损失函数层面**：SigLIP 的核心是逐对 sigmoid loss，不由某一种 pooling 定义。
- **具体 checkpoint 层面**：pooling、是否存在 CLS、输出头和 hidden dimension，都要看模型配置。

这里的 pooling attention 发生在**图像侧内部**，不是图片与文本之间的 cross-attention；图文仍然分别编码，到最后才通过向量分数比较。

### 2.3 文本侧：Transformer 编码整体文本

例如，“a dog running”经过 tokenizer 与 Text Transformer：

$$
\text{“a dog running”}
\xrightarrow{\text{tokenizer}}(t_1,t_2,\dots,t_N)
\xrightarrow{\text{Text Transformer}}(h_1,h_2,\dots,h_N).
$$

官方文本实现默认采用 `pool_type="last"`，取序列最后一个位置的表示，再经过输出 head。配套预处理使用 sticky EOS 与 EOS padding，保证该位置承担文本结束位置的表示作用。参见 [官方文本编码器实现](https://github.com/google-research/big_vision/blob/main/big_vision/models/proj/image_text/text_transformer.py#L50-L90)。

所以，不要把它理解为“随便取最后一个有效单词”，也不要直接套用 CLIP 的 EOT 索引查找逻辑。**tokenizer、padding 与 pooling 是配套的**。

到这里，图文已经被编码成两个可以比较的向量；SigLIP 还没有进行任何图文生成或对话。

## 3. 相似度：归一化、尺度与新增的 bias

### 3.1 先归一化，再计算余弦相似度

与 CLIP 一样，对输出 embedding 做 $L_2$ 归一化：

$$
\bar z_i^I=\frac{z_i^I}{\lVert z_i^I\rVert_2},
\qquad
\bar z_j^T=\frac{z_j^T}{\lVert z_j^T\rVert_2}.
$$

归一化后，点积就是余弦相似度：

$$
c_{ij}=(\bar z_i^I)^\top\bar z_j^T,
\qquad
-1\le c_{ij}\le1.
$$

接下来，加入可学习的正尺度 $\alpha$ 和可学习的全局标量 bias $b$：

$$
\boxed{
s_{ij}=\alpha c_{ij}+b,
\qquad
\alpha=\operatorname{exp}(a)>0
}
$$

其中，实际被优化的尺度参数是 $a$；若沿用温度记法，则：

$$
\alpha=\frac{1}{\tau},
\qquad
\tau=\operatorname{exp}(-a).
$$

**全文统一采用论文 Algorithm 1 和官方代码的加性 bias 约定：`logits = similarity * scale + bias`。** 参见 [官方双塔实现：归一化、尺度与 bias](https://github.com/google-research/big_vision/blob/main/big_vision/models/proj/image_text/two_towers.py#L45-L82)。

要区分三个量：

| 量 | 含义 |
| --- | --- |
| $c_{ij}$ | 图文 embedding 的余弦相似度 |
| $s_{ij}=\alpha c_{ij}+b$ | 输入二分类损失的 logit |
| $p_{ij}=\operatorname{sigmoid}(s_{ij})$ | 模型对这个候选配对给出的正类输出 |

### 3.2 一个 batch 仍然可以形成相似度矩阵

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

- 第 $i$ 行：图片 $I_i$ 与所有候选文本的 logits。
- 第 $j$ 列：文本 $T_j$ 与所有候选图片的 logits。
- 对角线：正配对。
- 非对角线：训练中当作负样本的候选配对。

矩阵的布局与 CLIP 相同。真正变化的是**后面如何计算概率与损失**，而不是有没有这张矩阵。

同时，数学上写出完整矩阵，不代表实现时必须一次性把它全部放进显存；第 7 节会解释分块计算。

### 3.3 Sigmoid：每个配对分别得到一个输出

Sigmoid 函数定义为：

$$
\operatorname{sigmoid}(s)
=\frac{1}{1+\operatorname{exp}(-s)}.
$$

于是：

$$
p_{ij}=\operatorname{sigmoid}(s_{ij}).
$$

仍然使用前篇的第一行 logits：

$$
[s_{11},s_{12},s_{13}]=[2.0,1.0,0.2].
$$

逐元素经过 sigmoid 后：

$$
[p_{11},p_{12},p_{13}]
\approx[0.881,0.731,0.550].
$$

它们的和约为 $2.162$，**不需要等于 $1$**。

| 处理方式 | 同一组 logits 的输出 | 含义 |
| --- | --- | --- |
| CLIP 的行 softmax | 约 $[0.65,0.24,0.11]$ | 在当前候选集合中，哪个文本是正确答案？ |
| SigLIP 的逐元素 sigmoid | 约 $[0.881,0.731,0.550]$ | 每个图文候选配对分别有多像正样本？ |

这也说明，**第一项排名最高，不代表 SigLIP 的损失已经很小**：$T_2$、$T_3$ 是负样本，但模型仍分别给了较高的正类输出。

这里的 $p_{ij}$ 是训练任务下的二分类输出，不能未经验证就当成任意真实场景中已校准的“语义匹配概率”。负样本采样、训练先验与数据分布都会影响它的解释。

### 3.4 Scale 与 bias：控制区分强度和判定基线

由：

$$
s_{ij}=\alpha c_{ij}+b,
$$

可以直观看到：

- **Scale $\alpha$**：余弦相似度每变化一点，logit 会变化多少。
- **Bias $b$**：所有 logits 整体向正方向或负方向平移多少。

例如，固定 $\alpha=10$、$b=-5$，得到下面的数值，其中 sigmoid 输出取近似值：

$$
\begin{array}{c|c|c}
c_{ij}&s_{ij}&p_{ij}\\\hline
0.8&3&0.953\\
0.5&0&0.500\\
0.2&-3&0.047
\end{array}
$$

在以 $p_{ij}=0.5$ 为分界时，对应的余弦阈值为：

$$
\alpha c_{ij}+b=0
\quad\Longrightarrow\quad
c_{ij}=-\frac{b}{\alpha}.
$$

这个分界是解释 logit 的工具，**不表示训练要先把输出阈值化，也不表示下游必须使用 $0.5$ 阈值**。实际 BCE 直接作用于连续 logits。

为什么 CLIP 通常没有这个全局 bias？因为给所有候选加同一个 $b$，softmax 会把它消掉：

$$
\frac{\operatorname{exp}(u_j+b)}{\sum_k\operatorname{exp}(u_k+b)}
=\frac{\operatorname{exp}(u_j)}{\sum_k\operatorname{exp}(u_k)}.
$$

但是：

$$
\operatorname{sigmoid}(u+b)
\ne\operatorname{sigmoid}(u)
\quad\text{一般成立}.
$$

所以，**CLIP 的 softmax 只关心候选之间的相对差异；SigLIP 的 BCE 还关心经过尺度与 bias 调整后，每个 logit 本身处于什么位置。**

### 3.5 为什么 bias 通常从负数开始？

完整候选矩阵中：

$$
\text{正样本数}=B,
\qquad
\text{负样本数}=B(B-1).
$$

因此正样本比例为：

$$
\pi=\frac{B}{B^2}=\frac{1}{B}.
$$

当 batch 很大时，大部分候选配对都是负样本。如果所有初始 logits 都接近 $0$，就相当于对海量负配对都预测 $p\approx0.5$，容易产生很大的初始纠偏梯度。

可以做一个**用于理解先验的简化推导**：假设所有余弦相似度都近似为 $0$，并希望常数预测与正样本比例一致，则：

$$
\operatorname{sigmoid}(b)=\frac{1}{B}
\quad\Longrightarrow\quad
b=\operatorname{log}\frac{1/B}{1-1/B}
=-\operatorname{log}(B-1),
\qquad B>1.
$$

这解释了为何负 bias 是合理起点，**但它不是论文要求随 batch 精确设置的公式**。论文采用的初始化是：

$$
a_0=\operatorname{log}10,
\qquad
\alpha_0=10,
\qquad
b_0=-10.
$$

注意，初始化为 $10$ 的是实际尺度 $\alpha$，不是对数参数 $a$；$b=-10$ 也不是冻结不变的阈值。参见 [SigLIP 论文第 3.2 节与 Algorithm 1](https://arxiv.org/pdf/2303.15343#page=3)。

## 4. 逐对二分类损失：把每个候选配对变成判断题

### 4.1 单个配对：从 sigmoid 到 BCE

对于一个图文候选配对 $(I_i,T_j)$，真实标签是 $y_{ij}\in\{0,1\}$，模型输出为 $p_{ij}$。二元交叉熵是：

$$
\boxed{
\ell_{ij}
=-y_{ij}\operatorname{log}p_{ij}
-(1-y_{ij})\operatorname{log}(1-p_{ij})
}
$$

分别看两种情况：

**正样本，$y_{ii}=1$：**

$$
\ell_{ii}=-\operatorname{log}p_{ii}.
$$

希望 $p_{ii}\rightarrow1$，也就是让正样本 logit 变大。

**负样本，$y_{ij}=0$：**

$$
\ell_{ij}=-\operatorname{log}(1-p_{ij}),
\qquad i\ne j.
$$

希望 $p_{ij}\rightarrow0$，也就是让负样本 logit 变小。

所以“sigmoid loss”不是只套一个 sigmoid 函数就结束，而是**用 sigmoid 参数化二分类输出，再计算对应的交叉熵**。

### 4.2 一个数值例子：正负样本分别贡献损失

继续看图片 $I_1$：

$$
[s_{11},s_{12},s_{13}]=[2.0,1.0,0.2],
\qquad
[y_{11},y_{12},y_{13}]=[1,0,0].
$$

每个候选配对都有自己的损失：

| 候选配对 | 标签 | 正类输出 | BCE |
| --- | --- | --- | --- |
| $(I_1,T_1)$ | $1$ | $p_{11}\approx0.881$ | $-\operatorname{log}p_{11}\approx0.127$ |
| $(I_1,T_2)$ | $0$ | $p_{12}\approx0.731$ | $-\operatorname{log}(1-p_{12})\approx1.313$ |
| $(I_1,T_3)$ | $0$ | $p_{13}\approx0.550$ | $-\operatorname{log}(1-p_{13})\approx0.798$ |

第一行的损失和约为：

$$
0.127+1.313+0.798\approx2.238.
$$

虽然 $T_1$ 已经排名最高，但 $T_2$、$T_3$ 的假阳性输出仍带来明显惩罚。

如果将负样本 logits 降为 $-1$、$-2$，保持正样本 logit 为 $2$，则：

$$
[p_{11},p_{12},p_{13}]
\approx[0.881,0.269,0.119],
$$

第一行的损失和降为约 $0.567$。这正是“正的判为正，负的判为负”。

### 4.3 整个 batch：对所有配对求和，再除以 batch size

采用论文与官方实现的归一化方式：

$$
\boxed{
\mathcal{L}_{\mathrm{SigLIP}}
=\frac{1}{B}\sum_{i=1}^{B}\sum_{j=1}^{B}\ell_{ij}
}
$$

展开为：

$$
\mathcal{L}_{\mathrm{SigLIP}}
=-\frac{1}{B}\sum_{i=1}^{B}
\left[
\operatorname{log}p_{ii}
+\sum_{j\ne i}\operatorname{log}(1-p_{ij})
\right].
$$

可以读成：

> 对每张图片，把它与所有文本候选的二分类损失加起来，再对图片取平均。

**这里除以的是 $B$，不是 $B^2$。** 如果调用 BCE 时直接对矩阵所有元素取 `mean`，得到的是：

$$
\mathcal{L}_{\mathrm{mean}}
=\frac{1}{B^2}\sum_{i,j}\ell_{ij}
=\frac{1}{B}\mathcal{L}_{\mathrm{SigLIP}}.
$$

固定 $B$ 时，两者只差一个正的常数倍，单独看这个目标的极小点不变，但**损失值与梯度尺度不一致**，也会影响它与正则项或其他损失的相对权重；不能当成完全相同的训练配置。参见 [官方训练代码：逐行求和，再对 batch 求平均](https://github.com/google-research/big_vision/blob/main/big_vision/trainers/proj/image_text/siglip.py)。

### 4.4 论文里的正负号标签：为什么写成 $+1$ 与 $-1$？

为了把正负样本写进同一个紧凑公式，可以定义：

$$
r_{ij}=2y_{ij}-1
=\begin{cases}
+1,&i=j,\\
-1,&i\ne j.
\end{cases}
$$

当 $B=3$ 时：

$$
R=
\begin{bmatrix}
+1&-1&-1\\
-1&+1&-1\\
-1&-1&+1
\end{bmatrix}.
$$

于是，单个配对的 BCE 等价于：

$$
\ell_{ij}
=-\operatorname{log}\operatorname{sigmoid}(r_{ij}s_{ij})
=\operatorname{log}\left(1+\operatorname{exp}(-r_{ij}s_{ij})\right).
$$

检查一下符号：

- 正样本 $r_{ii}=+1$：损失是 $-\operatorname{log}\operatorname{sigmoid}(s_{ii})$。
- 负样本 $r_{ij}=-1$：损失是 $-\operatorname{log}\operatorname{sigmoid}(-s_{ij})$，等价于 $-\operatorname{log}(1-p_{ij})$。

最终得到：

$$
\boxed{
\mathcal{L}_{\mathrm{SigLIP}}
=-\frac{1}{B}\sum_{i=1}^{B}\sum_{j=1}^{B}
\operatorname{log}\operatorname{sigmoid}
\left[r_{ij}\left(\alpha(\bar z_i^I)^\top\bar z_j^T+b\right)\right]
}
$$

因此，$\{0,1\}$ 标签的 BCE 与 $\{-1,+1\}$ 标签的 log-sigmoid 是**同一个目标的两种写法**。不要把 $-1$ 直接作为普通 BCE 的目标标签。

### 4.5 为什么不需要图像到文本、文本到图像各算一次？

CLIP 的两个方向不同，是因为：

- 图像到文本的 softmax 分母来自同一行。
- 文本到图像的 softmax 分母来自同一列。

但 SigLIP 的单项损失 $\ell_{ij}$ 只依赖当前配对的 $s_{ij}$ 与标签，没有行方向或列方向的归一化分母。

对同一组配对来说：

$$
\frac{1}{B}\sum_i\sum_j\ell_{ij}
=\frac{1}{B}\sum_j\sum_i\ell_{ij}.
$$

所以，同时转置 logits 与标签，只是在调整遍历顺序。再计算一个“反方向 BCE”并取平均，会得到相同的目标；直接相加则只是把损失放大 $2$ 倍。

这里的“不需要双向”**不等于少算一半非对角线**：

$$
(I_1,T_2)\ne(I_2,T_1).
$$

它们是不同的图文候选配对，完整目标中都要计算。对称的是交换图文角色后的**整体损失**，不是说矩阵必须满足 $s_{12}=s_{21}$。

### 4.6 “独立计算”到底独立在哪里？

固定 embedding、尺度和 bias 后，单项损失：

$$
\ell_{ij}=\ell(s_{ij},y_{ij})
$$

不需要知道其他候选的分数。增加一个新文本候选，不会直接改变已有配对的 sigmoid 输出；相比之下，softmax 会因为分母增加而重新分配已有候选的概率。

但这**不表示所有配对各自拥有独立参数**：

- $I_i$ 的 embedding 同时出现在这一行的所有配对中。
- $T_j$ 的 embedding 同时出现在这一列的所有配对中。
- 所有配对共享图像编码器、文本编码器、尺度和 bias。

因此，独立的是**给定 logits 后的逐项损失计算**，不是整个学习系统。候选集合改变后，新增损失仍会改变总梯度和后续参数更新。

### 4.7 最小实现：稳定地计算完整配对损失

下面是对应上述公式的单设备教学实现；输入是两个编码器输出的、尚未归一化的 embedding，且两侧顺序一一对应。

```python
import math
import torch
import torch.nn.functional as F


class SigLIPLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.logit_scale = torch.nn.Parameter(torch.tensor(math.log(10.0)))
        self.logit_bias = torch.nn.Parameter(torch.tensor(-10.0))

    def forward(self, image_emb, text_emb):
        assert image_emb.ndim == text_emb.ndim == 2
        assert image_emb.shape == text_emb.shape
        image_emb = F.normalize(image_emb.float(), dim=-1)
        text_emb = F.normalize(text_emb.float(), dim=-1)
        batch_size = image_emb.shape[0]

        logits = self.logit_scale.exp() * (image_emb @ text_emb.T)
        logits = logits + self.logit_bias
        targets = torch.eye(batch_size, device=logits.device, dtype=logits.dtype)

        return F.binary_cross_entropy_with_logits(
            logits, targets, reduction="sum"
        ) / batch_size
```

`binary_cross_entropy_with_logits` 接收原始 logits，并在内部使用数值稳定的形式；**不要先调用 sigmoid 再把结果传进去**。参见 [PyTorch 官方文档：BCEWithLogitsLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html)。训练时，还需要把这个 loss 模块里的尺度与 bias 参数一并加入 optimizer，并让它与 embedding 位于同一设备。

这段代码只展示损失构造，会显式生成完整候选矩阵；不是第 7 节的多设备分块实现。

## 5. 梯度机制：BCE 如何拉近正样本、推远负样本？

### 5.1 从 BCE 对 logit 的梯度看

对于 sigmoid + BCE，仍然有熟悉的形式：

$$
\boxed{
\frac{\partial\ell_{ij}}{\partial s_{ij}}
=p_{ij}-y_{ij}
}
$$

也就是“**模型预测 − 真实标签**”。不过，这里的 $p_{ij}$ 是该配对的 sigmoid 输出，不是行或列上的 softmax 概率。

**正样本：**

$$
\frac{\partial\ell_{ii}}{\partial s_{ii}}
=p_{ii}-1<0.
$$

**负样本：**

$$
\frac{\partial\ell_{ij}}{\partial s_{ij}}
=p_{ij}>0,
\qquad i\ne j.
$$

对完整损失，还要乘上归一化因子：

$$
\frac{\partial\mathcal{L}_{\mathrm{SigLIP}}}{\partial s_{ij}}
=\frac{p_{ij}-y_{ij}}{B}.
$$

为了理解方向，暂时把每个 logit 当成可以独立更新的量，令学习率为 $\eta>0$：

$$
\begin{aligned}
s_{ii}&\leftarrow s_{ii}-\frac{\eta}{B}(p_{ii}-1)
&&\Rightarrow s_{ii}\uparrow,\\
s_{ij}&\leftarrow s_{ij}-\frac{\eta}{B}p_{ij}
&&\Rightarrow s_{ij}\downarrow.
\end{aligned}
$$

实际更新的是共享网络参数，不是逐项独立修改 logits；上式只解释每个分数的直接优化倾向，不保证一次更新后所有分数都严格按箭头变化。

### 5.2 为什么难负样本的作用更强？

对于负样本，其单项梯度大小为 $p_{ij}$：

- 已经明显不匹配的负样本：例如 $p_{ij}=0.01$，梯度较小。
- 被误判为匹配的负样本：例如 $p_{ij}=0.9$，梯度较大。

对于正样本，其单项梯度绝对值为 $1-p_{ii}$：

- 正配对已经识别得很好：梯度较小。
- 正配对仍被认为不匹配：梯度较大。

因此，即使没有 softmax 的候选竞争，SigLIP 也会通过 BCE 的梯度自然强调难例，**不需要额外手工构造一套 pull / push loss**。

但单个容易负样本的梯度小，不代表很多容易负样本加起来可以忽略；负样本数量仍影响总损失与总梯度。

### 5.3 分数变化，为什么对应向量的“拉近 / 推远”？

因为：

$$
s_{ij}=\alpha(\bar z_i^I)^\top\bar z_j^T+b,
\qquad\alpha>0,
$$

在 $\alpha$、$b$ 固定时，提高正样本 logit，就对应提高余弦相似度、减小两个向量的夹角；降低负样本 logit，则对应相反的方向。

还可以直接对余弦相似度求导：

$$
\frac{\partial\mathcal{L}_{\mathrm{SigLIP}}}{\partial c_{ij}}
=\frac{\alpha}{B}(p_{ij}-y_{ij}).
$$

由于 $\alpha>0$，正负样本的优化方向不会被尺度翻转。

不过，训练同时会更新 $\alpha$ 与 $b$。因此，**logit 增大不一定意味着 embedding 夹角减小**；尺度变大或 bias 上移，也可能改变分数。判断几何上的靠近与远离，应看归一化 embedding 的余弦相似度。

## 6. 参数更新：双塔共同学习，尺度和 bias 也参与

### 6.1 SigLIP 预训练会训练哪些参数？

在两侧均未冻结的 SigLIP 图文预训练中，可训练部分包括：

| 部分 | 参与训练的参数 |
| --- | --- |
| 图像输入表示 | Patch projection、positional embeddings |
| 图像 Transformer | 注意力、MLP、LayerNorm 等可学习参数 |
| 图像整体表示头 | 采用 MAP 时的 probe、pooling attention、MLP，以及配置中存在的其他输出层 |
| 文本输入表示 | Token embeddings、positional embeddings |
| 文本 Transformer 与输出头 | 注意力、FFN、LayerNorm、输出映射等参数 |
| 相似度尺度 | 对数尺度 $a$，实际使用 $\alpha=\operatorname{exp}(a)$ |
| 匹配基线 | 全局标量 bias $b$ |

本篇将表示头包含在各自分支参数内，因此整体参数集合可以写为：

$$
\Theta=
\left\{
\theta_{\mathrm{vision}},
\theta_{\mathrm{text}},
a,b
\right\}.
$$

两侧的 Transformer 结构相似，不表示它们共享同一套权重。

### 6.2 梯度如何同时流向两个编码器？

定义：

$$
\delta_{ij}=\frac{p_{ij}-y_{ij}}{B}.
$$

将归一化后的 embedding 暂时视为中间变量，则：

$$
\begin{aligned}
\frac{\partial\mathcal{L}}{\partial\bar z_i^I}
&=\alpha\sum_{j=1}^{B}\delta_{ij}\bar z_j^T,\\
\frac{\partial\mathcal{L}}{\partial\bar z_j^T}
&=\alpha\sum_{i=1}^{B}\delta_{ij}\bar z_i^I.
\end{aligned}
$$

这说明：

- 一张图片的表示，会汇总它与所有文本候选的梯度。
- 一段文本的表示，会汇总它与所有图片候选的梯度。
- 不需要再构造“反方向 loss”，文本编码器也能获得训练信号。

梯度继续经过 $L_2$ 归一化及各自表示头，回到两个编码器。尺度和 bias 也有梯度：

$$
\frac{\partial\mathcal{L}}{\partial b}
=\sum_{i,j}\delta_{ij},
\qquad
\frac{\partial\mathcal{L}}{\partial a}
=\alpha\sum_{i,j}\delta_{ij}c_{ij}.
$$

例如，如果整体上预测为正的程度过高，$\sum_{i,j}(p_{ij}-y_{ij})>0$，梯度下降就会推动 $b$ 减小，把整体匹配基线往下调。

> **仍然不是让 image embedding 单方面追着固定的 text embedding 跑，而是两个表示空间共同调整；bias 与尺度则调节这些向量如何转成二分类 logits。**

### 6.3 不要混淆 SigLIP、SigLiT 与下游冻结

| 场景 | 图像编码器 | 文本编码器 |
| --- | --- | --- |
| 两侧联合训练的 SigLIP | 参与更新 | 参与更新 |
| SigLiT：sigmoid loss + Locked-image Tuning | 使用预训练图像表示并冻结 | 学习与固定图像表示对齐 |
| 下游使用 SigLIP 视觉塔 | 是否冻结由下游训练策略决定 | 可能根本不使用原文本塔 |

原论文同时研究了 SigLIP 与 SigLiT；其中“少量芯片、冻结视觉骨干”的 SigLiT 结果，不能理解成“两侧从零训练的 SigLIP”结果。参见 [SigLIP 论文第 4.1、4.2 节](https://arxiv.org/pdf/2303.15343#page=4)。

## 7. Batch 大小：不需要全局 softmax，不等于不需要负样本

### 7.1 候选配对仍然随 batch 增长

在完整配对目标中：

| Batch size | 正配对数 | 负配对数 | 每张图片的负文本数 |
| --- | --- | --- | --- |
| $B=3$ | $3$ | $6$ | $2$ |
| $B=4$ | $4$ | $12$ | $3$ |
| 一般的 $B$ | $B$ | $B(B-1)$ | $B-1$ |

SigLIP 的负样本依然参与学习。它只是**不通过 softmax 分母将同一行或同一列的 logits 绑在一起归一化**。

一个极端例子是 $B=1$，且不引入任何额外负样本。此时只有一个正配对：

$$
\mathcal{L}=-\operatorname{log}\operatorname{sigmoid}(s_{11}).
$$

单纯把 bias 不断增大，就能把损失降下去，却不必学习区分不同图文。因此，**“支持逐对计算”不等于“只训练正配对也足够”**。

### 7.2 为什么 sigmoid loss 适合分块计算？

把全部候选配对索引划分成互不重叠的块 $\mathcal{C}_1,\dots,\mathcal{C}_K$，覆盖全部 $B^2$ 个配对，则：

$$
\mathcal{L}_{\mathrm{SigLIP}}
=\frac{1}{B}\sum_{k=1}^{K}
\sum_{(i,j)\in\mathcal{C}_k}\ell_{ij}.
$$

每个块不需要其他块的分数来构造自己的 sigmoid 或 BCE，所以可以：

1. 计算一个图像 embedding 块与一个文本 embedding 块的分数。
2. 根据**全局配对索引**构造标签，计算该块的损失贡献。
3. 在正确管理反向传播的前提下，分块累积贡献，并释放或重算中间结果。
4. 多设备时交换所需 embedding 块，直到覆盖目标中的所有配对。

注意，**不是每个块的局部对角线都是正样本**。只有图像与文本的全局配对索引相同时才为正；包含其他设备负文本的块，可能全是负样本。

论文用设备间循环交换表示的方式实现这一过程，避免一次性 all-gather 所有 embedding，并只显式保存当前相似度块。参见 [SigLIP 论文第 3.3 节与 Figure 1](https://arxiv.org/pdf/2303.15343#page=3)。

### 7.3 分块节省什么，又没有节省什么？

假设当前分数块大小为 $m\times m$：

- 完整分数矩阵需要保存 $B^2$ 个元素。
- 逐块处理时，当前分数块只需要保存 $m^2$ 个元素。

但有三点不能混淆：

1. **分数矩阵的峰值存储减少，不代表总显存只剩 $O(m^2)$。** 参数、优化器状态、编码器激活和 embedding 仍占内存。
2. **如果完整覆盖全部候选，配对数量仍是 $B^2$。** 点积部分的总计算量仍约为 $O(B^2d)$，不会因 sigmoid 自动变成线性计算。
3. **不需要全局 softmax 归一化，不等于多设备之间完全不用通信。** 跨设备负样本仍需交换表示，参数梯度通常也需要同步。

此外，简单地把所有块的 loss 累加成一个保留全部计算图的张量、最后才反向传播，可能仍保存大量中间激活。真正的显存收益需要与分块反向、重计算或其他实现策略配合。

也不应说 CLIP 在数学上“绝对不能分块”：softmax 可以用流式归约等方式处理，但要正确维护跨候选的归一化信息。**SigLIP 的优势是损失项天然可加，分块逻辑更直接。**

### 7.4 “样本数量”与“配对数量”可以分开研究

标准完整 batch 同时改变了两件事：

- $B$ 增大：这一步看到更多原始图文样本。
- $B^2$ 增大：候选配对更多，正负比例也随之变化。

由于 SigLIP 的目标由逐对损失相加组成，可以在固定样本集合时，单独研究使用多少负配对、如何采样负配对。这不是说抽掉任意负样本后目标完全不变；如果不做相应的重加权，通常就是换了目标或正负权重。

同样，普通梯度累积只是累积多个小 batch 的梯度，**不会自动生成不同小 batch 之间的交叉负配对**。如果不额外交换或缓存 embedding，它不等价于一次完整的大 batch 配对损失。

### 7.5 论文关于 batch 大小的结论应如何理解？

原论文在其受控实验中观察到：较小 batch 下 sigmoid 相比 softmax 更有优势；继续增加 batch 后，收益逐渐减弱，约 $32$ k 的 batch 已能达到较好的效果。更大的 batch 并不保证继续提升。这里的 $32$ k 是原论文的规模记法。参见 [SigLIP 论文 Figure 2 与第 4.2 节](https://arxiv.org/pdf/2303.15343#page=4)。

正确的理解是：

> **SigLIP 改善了损失的计算组织方式，并在论文实验中提高了较小 batch 的训练表现；不是证明 batch size 从此无关紧要。**

最终表现仍与训练数据、模型容量、负样本构造、学习率和训练时长有关。论文里的规模结论不是对所有数据集和硬件的通用最优配置。

## 8. 语义从哪里来：同样来自大量配对中的共享因素

### 8.1 判断题为什么也能学出语义空间？

训练数据仍会反复出现：

- 狗图片 ↔ “a dog”。
- 不同品种的狗 ↔ “a dog”。
- 狗跑步的图片 ↔ “a dog running”。
- 汽车图片 ↔ “a car”。

为了把大量正配对判为正、把负配对判为负，图像编码器需要提取有助于匹配描述的视觉因素；文本编码器也需要把不同表达组织成有利于图文判断的表示。

因此，共享空间中可能逐渐形成：

$$
\text{dog image}
\approx\text{“a dog”}
\approx\text{“a puppy”},
$$

并与不相关描述保持较低相似度。这里的 $\approx$ 表示可能形成的语义邻近，不是严格相等，也不是损失对每组同义表达都给出的直接约束。

SigLIP 与 CLIP 的共同点在于：

> **监督来自图文对应关系，语义来自能够持续解释这些对应关系的跨模态共享因素。**

Sigmoid 只改变“如何把配对关系写成损失”，不会凭空补足训练数据中没有的概念，也不会自动解决错误配对、细粒度关系或所有组合泛化问题。

### 8.2 推理时：仍然可以做图文检索与零样本分类

给定图片 $I$，把候选类别写成文本，例如：

- “a photo of a dog”。
- “a photo of a cat”。
- “a photo of a car”。

分别编码后计算：

$$
c_j=(\bar z^I)^\top\bar z_j^T,
\qquad
s_j=\alpha c_j+b.
$$

对于同一模型、同一组全局 $\alpha>0$ 与 $b$，由单调性可知：

$$
\operatorname*{arg\,max}_j c_j
=\operatorname*{arg\,max}_j s_j
=\operatorname*{arg\,max}_j\operatorname{sigmoid}(s_j).
$$

所以，**只做排序时，余弦相似度、logit 与 sigmoid 输出的排序相同**；若要按阈值判定或解释数值，则必须考虑尺度、bias 与校准。

推理阶段可以根据任务选择只取一个最高分类别，也可以分别查看多个描述的 sigmoid 输出；输出本身不强制互斥。官方演示使用逐对 sigmoid 分数展示图文匹配，参见 [官方 SigLIP 演示](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/SigLIP_demo.ipynb)。

但是，训练时非对角线仍被标为负，**不能因为 sigmoid 允许多个高输出，就认为训练数据已经自动变成了正确的多标签监督**。

### 8.3 用作多模态模型视觉塔时，要区分全局分数与 patch 特征

结合本目录的 Video-MLLM 学习，需要区分：

- **Global image embedding**：聚合整张图片，用于整图与文本的相似度比较。
- **Patch hidden states**：保留多个空间位置的视觉表示，可以被下游模型进一步处理。

SigLIP 的全局图文训练会通过 pooling 向视觉 tokens 回传梯度，但这不等于每个 patch 都有独立、经过验证的文本匹配分数。

因此，“这一帧与 query 很相关”不能直接推出“这一帧的哪些 patch 应当保留”。如果下游只拿视觉塔的 hidden states 接入自己的 projector 与语言模型，也不意味着还要原样保留 SigLIP 的文本塔、全局 pooling 或 sigmoid loss。相关学习任务见 [[07-MultiModal/Video-MLLM/03-clip-siglip.md|CLIP 与 SigLIP 学习]]。

## 9. 最后串起来：一个完整的心智模型

1. **构造监督**：取 $B$ 对图文，组成 $B^2$ 个候选配对；配对为正，其余候选在训练中被当作负。
2. **编码与比较**：双塔得到同维度 embedding，归一化后计算余弦相似度，再乘可学习尺度、加可学习 bias。
3. **逐对判断**：每个候选配对分别计算 sigmoid + BCE，不做行或列上的 softmax 归一化。
4. **汇总与更新**：按原始约定将所有配对损失求和后除以 $B$，梯度同时回传到两个编码器、表示头、尺度与 bias。
5. **形成语义空间**：通过大量配对中的共同规律，学习跨模态共享表示；可将可加的损失项分块处理，但负样本与训练规模仍然重要。

把前后两篇放在一起：

| 维度 | CLIP | SigLIP |
| --- | --- | --- |
| 核心监督 | 天然图文配对 | 天然图文配对 |
| 核心题型 | 在候选中找正确配对 | 判断当前配对是否为正 |
| 网络骨架 | 双编码器 | 双编码器，具体表示头需看配置 |
| 输出处理 | 行 / 列 softmax | 逐元素 sigmoid |
| 概率是否必须和为 $1$ | 每个归一化方向内必须 | 不要求 |
| 损失组织 | 两个方向的 CE 取平均 | 所有候选配对的 BCE 汇总 |
| 全局标量 | Logit scale | Logit scale + bias |
| 配对分数是否需要其他候选参与归一化 | 需要 | 不需要 |
| 是否仍需要负样本 | 需要 | 需要 |
| 标准完整配对数量 | $B^2$ | $B^2$ |

从损失构造看：

$$
\boxed{\text{CLIP：Similarity}+\text{Softmax}+\text{Cross Entropy}}
$$

$$
\boxed{\text{SigLIP：Similarity}+b+\text{Sigmoid}+\text{BCE}}
$$

上式中的 Similarity 包含归一化后的点积与可学习尺度。真正要记住的不是“把一个激活函数换成另一个”，而是：

> **SigLIP 把图文对齐从 batch 内的互斥选择题，改写成了逐对的二分类判断题；损失不再依赖全局候选归一化，但共享参数、正负样本和共同形成语义空间的学习机制仍然存在。**
