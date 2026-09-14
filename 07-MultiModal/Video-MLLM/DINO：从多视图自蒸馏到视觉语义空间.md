---
created: 2026-09-12
updated: 2026-09-12
---

![[_assets/images/dino-01-multiview-self-distillation.drawio.svg|900]]

> **DINO 用同一张图片的不同增强视图构造监督：教师网络对全局视图生成概率分布，学生网络从其他全局或局部视图预测这个分布；交叉熵只反向更新学生，教师由学生参数的 EMA 更新，并结合 centering 与 sharpening 避免表示塌缩。**

本文讨论原始 **DINO（self-distillation with no labels）**，即 ICCV 2021 论文 [Emerging Properties in Self-Supervised Vision Transformers](https://arxiv.org/abs/2104.14294) 中的视觉自监督方法；不是后续的 [DINOv2](https://github.com/facebookresearch/dinov2)，也不是同名的 [DINO 目标检测模型](https://arxiv.org/abs/2203.03605)。组织方式沿用 [[07-MultiModal/Video-MLLM/CLIP：从图文配对到共享语义空间.md|CLIP 笔记]]。

理解 DINO，可以沿着四个问题展开：

| 核心问题 | 简要答案 |
| --- | --- |
| 监督信号从哪里来？ | 同一张图片的不同增强视图应表达相容的信息；具体软目标由教师在线生成 |
| 网络如何表示图片？ | Student 与 Teacher 都由视觉 backbone 和 DINO projection head 组成，输出相同维数的 logits |
| Loss 如何构造？ | 在同一图片的不同视图之间，用交叉熵让学生分布匹配教师分布，不构造 batch 内负样本 |
| 哪些参数会更新？ | 学生通过梯度更新；教师通过学生参数的 EMA 更新；center 通过教师 logits 的统计量更新 |

下文依次解释：**多视图监督 → 师生网络 → 输出分布与温度 → 跨视图损失 → 梯度与参数更新 → 防塌缩与语义学习**。

## 1. 监督信号：同一图片的不同视图，而不是类别或文本标签

### 1.1 从一张图片生成训练关系

假设有一张图片 $I$：一只狗在草地上跑。对它做随机裁剪、缩放、颜色扰动、模糊等数据增强，可以得到：

- 全局视图 $x_1$：狗和较大范围的草地。
- 全局视图 $x_2$：另一种裁剪与颜色变化下的狗和背景。
- 局部视图 $x_3$：狗的头部附近。
- 局部视图 $x_4$：狗的身体附近。

这里的具体裁剪内容只是示意；实际随机裁剪也可能只包含背景，并不保证每个视图都看得到完整对象。

我们不知道图片的类别，也不需要配套文本，但知道这些视图的来源相同：

$$
x_1,x_2,x_3,x_4\quad\text{都由同一张图片 }I\text{ 生成}.
$$

因此，可以构造这样的学习要求：

> **学生即使看到不同裁剪、颜色变化或局部内容，也要尽量预测教师从另一全局视图得到的表示分布。**

“这些视图来自同一张图片”是已知关系；“应该输出怎样的概率分布”则由教师在训练过程中不断生成。后者不是人工提供的固定标签。

### 1.2 Global crops 与 local crops 各自做什么？

对于 batch 中的第 $i$ 张图片 $I_i$，生成 $2$ 个全局视图与 $M$ 个局部视图：

$$
V_i=\{x_{i,1},x_{i,2},x_{i,3},\dots,x_{i,M+2}\}.
$$

其中，$x_{i,1},x_{i,2}$ 是全局视图，其余是局部视图。

| 视图 | 输入哪个网络？ | 作用 |
| --- | --- | --- |
| 全局视图 | Teacher 和 Student 都看 | 教师生成相对完整的目标，学生也学习全局到全局的一致性 |
| 局部视图 | 只有 Student 看 | 让学生从局部信息预测全局视图的目标，即 local-to-global learning |

官方增强实现将全局裁剪缩放为 $224\times224$ 像素，局部裁剪缩放为 $96\times96$ 像素。**“全局视图”仍然可以是随机裁剪，不等于未经裁剪的完整原图。** 参见 [官方实现：DataAugmentationDINO](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L419-L464)。

还要区分两个尺度：

- **Crop / view**：数据增强生成的一张输入图片。
- **Patch / token**：ViT 在某个输入视图内部切出的图像块。

一个 local crop 内部仍包含多个 patches；DINO 并不是把每个 patch 都直接当作一个独立的 local crop。

### 1.3 与 CLIP 的监督差别

- **CLIP：image–text correspondence**，知道“这张图与这段文本配对”。
- **DINO：cross-view consistency**，知道“这些视图来自同一张图”，再由教师提供跨视图预测目标。

所以，DINO 的“无标签”不是“完全没有学习信号”，而是**不使用人工类别标签或图文配对标签，把数据增强关系与在线教师输出变成监督**。

## 2. 网络架构：两个视觉网络，而不是图文双编码器

### 2.1 整体结构与符号

DINO 包含学生网络和教师网络，两侧都由视觉编码器与 projection head 组成：

$$
\begin{aligned}
x_{i,b}
&\xrightarrow{f_{\theta_s}}h^s(x_{i,b})
\xrightarrow{g_{\phi_s}}z^s(x_{i,b}),\\
x_{i,a}
&\xrightarrow{f_{\theta_t}}h^t(x_{i,a})
\xrightarrow{g_{\phi_t}}z^t(x_{i,a}).
\end{aligned}
$$

其中：

- 下标 $s$、$t$ 分别表示 student、teacher，不表示训练步数。
- $a\in\{1,2\}$：教师只看全局视图。
- $b\in\{1,\dots,M+2\}$：学生看全部视图；构造损失时排除 $b=a$。
- $h^s,h^t\in\mathbb{R}^{d}$：视觉 backbone 输出的图像表示。
- $z^s,z^t\in\mathbb{R}^{K}$：DINO head 输出的 logits，之后还要经过温度缩放与 softmax。

两侧参数集合分别为：

$$
\Theta_s=\{\theta_s,\phi_s\},
\qquad
\Theta_t=\{\theta_t,\phi_t\}.
$$

**两侧结构相同，但不是共用同一份可训练参数。** 教师初始时复制学生权重，此后通过 EMA 跟随学生；教师也不是预先训练好的大模型。参见 [官方实现：网络构建与初始化](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L182-L211)。

### 2.2 视觉 backbone：以 ViT 为例

DINO 是一种训练方法，不是一种限定死的网络结构；原始工作同时研究了 ViT 和 ResNet。以 ViT 为例，图像级训练表示的简化流程是：

$$
\text{View}
\rightarrow\text{patches}
\rightarrow\text{ViT}
\rightarrow h_{\mathrm{CLS}}
\rightarrow\text{DINO head}.
$$

这里使用 CLS 表示，不意味着训练时提供了 class label。CLS 只是用于汇聚整张输入视图信息的 token。参见 [DINO 论文第 3.2 节](https://arxiv.org/html/2104.14294v2#S3.SS2)。

### 2.3 DINO head：把表示变成可蒸馏的输出

以学生侧为例，head 可以拆成：

$$
\begin{aligned}
u^s(x)&=\operatorname{MLP}_{\phi_s}(h^s(x)),\\
\bar u^s(x)&=\frac{u^s(x)}{\lVert u^s(x)\rVert_2},\\
z^s(x)&=W_s\bar u^s(x).
\end{aligned}
$$

这里 $W_s$ 也属于 head 参数 $\phi_s$；MLP 下标用于表示其属于学生 head，不表示它独占全部 $\phi_s$。

官方 `DINOHead` 的默认配置是：

- $3$ 层 MLP，隐藏维数为 $2{,}048$。
- MLP 输出一个 $256$ 维 bottleneck 向量，再做 $L_2$ 归一化。
- 最后接带 weight normalization 的线性层，映射到 $K$ 维。
- 训练脚本中默认 $K=65{,}536$。

参见 [官方实现：DINOHead](https://github.com/facebookresearch/dino/blob/main/vision_transformer.py#L257-L291) 与 [输出维度配置](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L55-L56)。这些是实现配置，不是理解 DINO 所必需的固定数值。

**$K$ 既不是 batch size，也不是人工类别数。** 可以把输出维度理解为网络学习到的原型方向或“潜在类别槽位”，但不能直接说“第 $1$ 维就是 dog，第 $2$ 维就是 cat”；原始训练没有赋予这些维度固定的文字含义。

还要区分：**训练用的 $K$ 维 head 输出，不等于下游通常提取的 $d$ 维 backbone 特征。** Head 用来组织自监督目标，迁移使用时通常取 head 之前的视觉表示。

## 3. 输出分布：softmax、温度与教师中心化

### 3.1 学生分布：在输出维度之间归一化

学生的第 $k$ 个输出概率为：

$$
P_s(x)_k
=\frac{\operatorname{exp}(z^s(x)_k/\tau_s)}
{\sum_{j=1}^{K}\operatorname{exp}(z^s(x)_j/\tau_s)}.
$$

其中 $\tau_s>0$ 是学生温度，且：

$$
\sum_{k=1}^{K}P_s(x)_k=1.
$$

这回答的是：“这个视图在网络学习到的 $K$ 个输出方向上，应如何分配概率？”

**与 CLIP 不同，softmax 的分母不是当前 batch 的其他图片或文本，而是同一个视图的 $K$ 个输出维度。** 若把一个固定视图位置的 batch 输出堆起来，得到的是 $Z_s\in\mathbb{R}^{B\times K}$，而不是 CLIP 的图文相似度矩阵 $S\in\mathbb{R}^{B\times B}$。

### 3.2 教师分布：先减 center，再用温度缩放

教师在 softmax 之前减去一个中心向量 $c\in\mathbb{R}^{K}$：

$$
P_t(x)_k
=\frac{\operatorname{exp}((z^t(x)_k-c_k)/\tau_t)}
{\sum_{j=1}^{K}\operatorname{exp}((z^t(x)_j-c_j)/\tau_t)}.
$$

因此两侧的处理不是完全对称的：

| 部分 | Student | Teacher |
| --- | --- | --- |
| 输入视图 | 全局与局部视图 | 只有全局视图 |
| 减去 center | 不做 | 在 logits 上减去 $c$ |
| Temperature | 使用 $\tau_s$ | 使用 $\tau_t$，用于目标锐化 |
| 输出分布参与反向传播 | 是 | 否，作为 stop-gradient 的目标 |

Center 是**跨样本统计得到的逐维向量**，不是把每张图片的 logits 减去一个共同标量。减去共同标量不会改变 softmax；减去不同的 $c_k$ 才能调整各维度长期存在的偏置。它也不是对 softmax 概率做减法。参见 [官方实现：DINOLoss.forward](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L380-L404)。

### 3.3 Temperature：让教师目标更有区分性

暂时固定中心化后的 logits，用一个 $K=3$ 的教学例子：

$$
z^t(x)-c=[0.2,0.1,0].
$$

若温度分别取 $0.1$ 与 $0.04$：

$$
\begin{aligned}
\operatorname{softmax}([0.2,0.1,0]/0.1)
&\approx[0.6652,0.2447,0.0900],\\
\operatorname{softmax}([0.2,0.1,0]/0.04)
&\approx[0.9184,0.0754,0.0062].
\end{aligned}
$$

温度越低，已有的分数差异越明显，分布越尖锐。它不改变这些固定 logits 的排序，也不是必须把目标变成 one-hot。

在官方损失实现中，学生温度默认 $\tau_s=0.1$；教师温度由配置与预设 schedule 控制，训练脚本默认值为 $0.04$。**这两个温度不是像 CLIP 的 logit scale 那样通过梯度学习的参数。** 不同实验可以采用不同的教师温度调度，不能把默认参数等同于所有论文实验的配置。参见 [教师温度配置](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L67-L75) 与 [DINOLoss 初始化](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L363-L378)。

为什么要对教师做 centering 和 sharpening，而不只是随意调概率？第 7 节将用“表示塌缩”解释。

## 4. 跨视图蒸馏损失：让学生匹配教师的软标签

### 4.1 单个视图对：从分布到交叉熵

让教师看全局视图 $x_1$，学生看另一个视图 $x_2$。记：

$$
q=P_t(x_1),
\qquad
p=P_s(x_2).
$$

教师提供的是软标签 $q$，单个视图对的交叉熵为：

$$
\boxed{
\ell(x_1,x_2)
=H(q,p)
=-\sum_{k=1}^{K}q_k\operatorname{log}p_k
}
$$

这仍然是熟悉的 softmax + cross entropy，但目标不再是人工给出的 one-hot 类别，而是**教师对另一视图输出的完整分布**。

### 4.2 一个具体数值例子

为便于计算，继续用 $K=3$，假设：

$$
q=[0.7,0.2,0.1],
\qquad
p=[0.3,0.4,0.3].
$$

学生分给第 $1$ 维的概率太低，分给第 $2$、$3$ 维的概率太高。损失为：

$$
\begin{aligned}
\ell
&=-0.7\operatorname{log}0.3
-0.2\operatorname{log}0.4
-0.1\operatorname{log}0.3\\
&\approx1.1464.
\end{aligned}
$$

若学生刚好匹配教师：

$$
p=q=[0.7,0.2,0.1],
$$

则损失降至：

$$
H(q,q)
=-0.7\operatorname{log}0.7
-0.2\operatorname{log}0.2
-0.1\operatorname{log}0.1
\approx0.8018.
$$

**已经完全匹配，交叉熵却不是零。** 因为目标本身是软分布，其熵不为零。不能像 one-hot 分类那样，一概把“训练正确”理解成“正确类别概率趋近 $1$、CE 趋近 $0$”。上述数值使用自然对数，都是教学示例，不是论文实验结果。

### 4.3 为什么匹配分布可以用 CE？

对于固定的教师分布 $q$：

$$
\begin{aligned}
H(q,p)&=H(q)+D_{\mathrm{KL}}(q\Vert p),\\
H(q)&=-\sum_{k=1}^{K}q_k\operatorname{log}q_k,\\
D_{\mathrm{KL}}(q\Vert p)
&=\sum_{k=1}^{K}q_k\operatorname{log}\frac{q_k}{p_k}.
\end{aligned}
$$

当前反向传播中，教师被 stop-gradient，$H(q)$ 对学生参数是常数。因此：

$$
\min_{\Theta_s}H(q,p)
\quad\Longleftrightarrow\quad
\min_{\Theta_s}D_{\mathrm{KL}}(q\Vert p).
$$

也就是让学生的概率分布接近教师，而不是只抄教师概率最大的一维。跨训练步时，教师目标会变化，因此完整训练不是在拟合一份永远固定的标签集。

### 4.4 两个全局视图：交换视图，但不交换师生角色

如果只有 $2$ 个全局视图，损失写成：

$$
\mathcal{L}_{\mathrm{two\text{-}view}}
=\frac{1}{2}\left[
H(\operatorname{sg}(P_t(x_1)),P_s(x_2))
+H(\operatorname{sg}(P_t(x_2)),P_s(x_1))
\right].
$$

其中 $\operatorname{sg}$ 表示 stop-gradient：数值保持不变，但梯度不穿过该分支。

- 第一项：教师看 $x_1$，监督看 $x_2$ 的学生。
- 第二项：教师看 $x_2$，监督看 $x_1$ 的学生。

这里的“两个方向”是**交换哪一个视图作为教师输入**，不是让教师和学生互相通过梯度学习。两个方向中，被反向更新的始终只有学生。

### 4.5 Multi-crop：全局教师监督其他所有视图

加入 $M$ 个局部视图后，每个教师全局视图都监督学生的其他视图，跳过相同视图的配对。

以 $M=2$ 为例：

| 教师目标来源 | 学生 $x_1$ | 学生 $x_2$ | 学生 $x_3$（局部） | 学生 $x_4$（局部） |
| --- | --- | --- | --- | --- |
| 教师 $x_1$（全局） | 跳过 | 计算 CE | 计算 CE | 计算 CE |
| 教师 $x_2$（全局） | 计算 CE | 跳过 | 计算 CE | 计算 CE |

共有 $2\times3=6$ 个有方向的视图配对项。一般情况下，每张图片有：

$$
2\bigl((M+2)-1\bigr)=2(M+1)
$$

个损失项。对 $B$ 张图片及其视图配对取平均：

$$
\boxed{
\mathcal{L}_{\mathrm{DINO}}
=\frac{1}{2B(M+1)}
\sum_{i=1}^{B}
\sum_{a=1}^{2}
\sum_{\substack{b=1\\b\ne a}}^{M+2}
H\!\left(
\operatorname{sg}(P_t(x_{i,a})),
P_s(x_{i,b})
\right)
}
$$

这里始终使用相同的图片索引 $i$，没有要求学生视图去匹配另一张图片的教师目标。“跳过相同视图”是为了把目标放在跨增强预测上；相同视图的 CE 并非数学上无法计算。

上述平均方式对应官方实现：遍历教师全局视图与学生全部视图、跳过同视图，然后平均有效项。参见 [官方实现：视图配对与损失平均](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L392-L404)。

### 4.6 为什么它不是 CLIP 那样的对比分类？

| 问题 | CLIP | DINO |
| --- | --- | --- |
| 当前预测对象是什么？ | 哪个文本或图片是正确配对对象 | 另一个视图对应怎样的教师分布 |
| softmax 在哪里竞争？ | 当前 batch 的 $B$ 个候选样本之间 | 同一视图的 $K$ 个输出维度之间 |
| 目标是什么？ | 正确配对索引，对应 one-hot 标签 | 教师生成的软分布 |
| 是否显式推开其他图片？ | 其他 batch 配对被当作负样本 | 没有这种样本级负配对项 |

**“用了 softmax + CE”不自动等于“用了负样本对比学习”。** 要看 softmax 的维度是什么、标签从哪里来，以及损失究竟在比较哪些对象。

## 5. 梯度机制：学生如何学会预测教师？

### 5.1 对 logit 的梯度仍然是“预测减目标”

对一个固定教师目标 $q$，令学生温度缩放后的 logits 为：

$$
a_k=\frac{z^s(x)_k}{\tau_s},
\qquad
p=\operatorname{softmax}(a).
$$

则：

$$
\boxed{
\frac{\partial\ell}{\partial a_k}=p_k-q_k
}
\qquad
\boxed{
\frac{\partial\ell}{\partial z^s(x)_k}
=\frac{p_k-q_k}{\tau_s}
}
$$

要注意：**如果求导对象是缩放前的 logits，就不能漏掉 $1/\tau_s$。**

继续看上一节的例子：

$$
p-q=[0.3,0.4,0.3]-[0.7,0.2,0.1]
=[-0.4,0.2,0.2].
$$

暂时把 $a_k$ 当成可独立更新的量，梯度下降会推动：

$$
\begin{aligned}
a_1&\leftarrow a_1-\eta(-0.4)
&&\Rightarrow a_1\uparrow,\\
a_2&\leftarrow a_2-\eta(0.2)
&&\Rightarrow a_2\downarrow,\\
a_3&\leftarrow a_3-\eta(0.2)
&&\Rightarrow a_3\downarrow.
\end{aligned}
$$

因此学生会提高自己低估的维度，降低自己高估的维度。与 CLIP 的 one-hot 目标不同，这里不是机械地把某一维推到 $1$、其余维度推到 $0$，而是追随教师分配的概率质量。

实际更新的是共享网络参数，不是逐个独立修改 logits；不同视图的损失也会共同作用，因此这些箭头表示直接优化倾向，不保证每次参数更新后每一项都严格如此变化。

### 5.2 梯度回到哪一侧？

学生侧的梯度路径为：

$$
\mathcal{L}_{\mathrm{DINO}}
\rightarrow P_s
\rightarrow z^s
\rightarrow\text{DINO head}
\rightarrow h^s
\rightarrow\text{Student ViT}.
$$

教师分布则被当作当前步骤中的常量目标：

$$
q=\operatorname{sg}(P_t),
\qquad
\left.\frac{\partial\mathcal{L}_{\mathrm{DINO}}}{\partial\Theta_t}\right|_{\text{反向传播路径}}
=0.
$$

数学上的交叉熵本来依赖 $q$；这里梯度为零是**训练实现主动截断教师分支**的结果。Center 也不通过这个损失获得梯度。

### 5.3 这是不是直接“拉近两个 embedding”？

可以直观地说 DINO 让同图不同视图的表示趋于一致，但严格地说，它直接约束的是：

$$
P_s(x_2)\approx P_t(x_1),
$$

而不是显式最小化：

$$
\lVert h^s(x_2)-h^t(x_1)\rVert_2^2.
$$

匹配 head 后的分布会通过梯度影响 backbone，但不能据此断言两个 backbone 向量必须逐元素相等。DINO 也没有一项要求“所有不同图片的 embedding 都互相远离”。

> **CLIP 的直观重点是配对样本之间的相对相似度；DINO 的直观重点是不同视图之间的预测一致性。**

## 6. 参数更新：学生反向传播，教师做 EMA

### 6.1 原始 DINO 训练时，哪些量会改变？

| 部分 | 具体内容 | 如何更新？ |
| --- | --- | --- |
| 学生视觉编码器 | Patch projection、CLS embedding、位置编码、注意力与 MLP 等可学习参数 | 对蒸馏损失反向传播，由优化器更新 |
| 学生 DINO head | MLP 与最终线性层的可训练参数 | 由优化器更新 |
| 教师视觉编码器与 head | 对应的教师参数 | 对学生参数做 EMA，不接受 loss 梯度 |
| 教师 center $c$ | 每个输出维度的长期 logits 均值估计 | 对当前 batch 的教师 logits 均值做 EMA |
| 温度 $\tau_s,\tau_t$ | softmax 温度 | 人工配置或预设 schedule，不通过梯度学习 |
| EMA 系数 | 教师动量 $\lambda$、center 动量 $m$ | 人工配置或预设 schedule |

“学生 head 可训练”指其可训练分量。官方实现还包含输出层初期冻结，以及按配置固定 weight normalization 尺度的稳定训练细节，并非每个 head 参数从第一步起都一定更新。参见 [训练脚本的输出层冻结配置](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L93-L95) 与 [head 尺度设置](https://github.com/facebookresearch/dino/blob/main/vision_transformer.py#L276-L279)。

### 6.2 教师 EMA：不反向传播，不代表不更新

用上标 $(n)$ 表示训练步数。学生先通过优化器更新；为说明关系，简写成梯度下降形式：

$$
\Theta_s^{(n+1)}
=\Theta_s^{(n)}
-\eta_n\nabla_{\Theta_s^{(n)}}\mathcal{L}_{\mathrm{DINO}}^{(n)}.
$$

实际使用 AdamW 等优化器时还有相应的动量、预条件与权重衰减机制，上式只表达学生由梯度驱动。

随后，教师参数更新为：

$$
\boxed{
\Theta_t^{(n+1)}
=\lambda_n\Theta_t^{(n)}
+(1-\lambda_n)\Theta_s^{(n+1)}
}
$$

例如 $\lambda_n=0.996$ 时：

$$
\Theta_t^{(n+1)}
=0.996\Theta_t^{(n)}+0.004\Theta_s^{(n+1)}.
$$

教师保留大部分历史参数，只吸收一小部分最新学生参数。因此它是学生历史状态的平滑版本，而不是每一步都立即复制最新学生。官方默认教师动量从 $0.996$ 开始，并随训练调度趋近 $1$。参见 [教师动量配置](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L61-L63) 与 [EMA 更新代码](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L326-L350)。

需要同时记住：

- **一个反向传播步骤内**：教师固定，是学生的目标。
- **跨训练步骤**：教师持续变化，变化来自学生参数的 EMA。

EMA 平滑的是参数，不等于对非线性网络的所有历史预测做精确算术平均，也不保证教师对每一张图片都一定比学生更正确。

### 6.3 Center EMA：更新的是统计量，不是网络参数

假设 $B$ 是跨所有设备的全局图片数，对每张图片的 $2$ 个教师全局视图，计算当前步骤的原始 logits 均值：

$$
\mu^{(n)}
=\frac{1}{2B}
\sum_{i=1}^{B}\sum_{a=1}^{2}
z^{t,(n)}(x_{i,a}).
$$

然后：

$$
\boxed{
c^{(n+1)}=m c^{(n)}+(1-m)\mu^{(n)}
}
$$

官方实现的 center 动量默认 $m=0.9$，并对分布式训练中的教师输出求全局均值。这里统计的是**未经减中心、未经温度缩放、未经 softmax 的教师 logits**。参见 [官方实现：center 初始化与更新](https://github.com/facebookresearch/dino/blob/main/main_dino.py#L363-L416)。

两个 EMA 不要混为一谈：

- 教师 EMA：平均的是**学生参数**，改变教师怎样编码图片。
- Center EMA：平均的是**教师输出统计量**，改变目标分布的逐维校正。

### 6.4 一个完整训练步骤的顺序

1. 取一个图片 batch，为每张图片生成全局与局部视图。
2. 教师处理全局视图，学生处理全部视图，得到各自 logits。
3. 用当前 center 与教师温度构造教师分布，并 stop-gradient。
4. 用学生温度构造学生分布，对同图、不同视图计算并平均 CE。
5. 根据损失反向传播，更新学生的可训练参数。
6. 用更新后的学生参数对教师做 EMA。
7. 用本步前向时保存的教师原始 logits 更新 center，供下一步使用。

这是便于理解的顺序；官方代码在 loss 的 forward 末尾就执行 center 更新。两种写法的关键相同：**本步目标用旧 center，本步教师 logits 用于更新下一步的 center**，不能先覆盖 center 再拿它重算本步目标。

## 7. 没有负样本：为什么不会让所有图片都变得一样？

### 7.1 只要求一致性，会出现平凡解

假设不管输入什么图片，教师和学生都输出同一个常量分布：

$$
P_t(x)=P_s(x)=q_0,\qquad\forall x.
$$

那么同图不同视图的分布当然一致，但模型已经不区分狗、猫或汽车。这就是 **representation collapse（表示塌缩）**。

常见的两种输出塌缩形式是：

| 形式 | 以 $K=3$ 为例 | 丢失了什么？ |
| --- | --- | --- |
| 单维主导 | 所有图片都输出接近 $[1,0,0]$ | 不同图片被分配到同一个方向 |
| 均匀分布 | 所有图片都输出 $[1/3,1/3,1/3]$ | 每张图片都没有任何区分性偏好 |

前一种形式下 CE 甚至可以接近 $0$。所以，**蒸馏损失很低，不足以证明学到了有用特征**。

### 7.2 Centering：抑制某个维度长期统治所有样本

假设教师在很多图片上都给第 $1$ 维很高的原始 logit，那么这个维度的长期均值 $c_1$ 也会升高。后续形成目标时，要计算：

$$
z^t(x)_1-c_1.
$$

因此，“对所有图片都普遍偏高”的部分会被扣除，削弱单一维度的持续主导。

但这不是把每个 batch 的类别使用率强制变成完全均匀，也不是给每张图片指定不同编号。Centering 只是在 logits 上进行逐维、带历史平滑的统计校正。

### 7.3 Sharpening：避免目标总是过于平坦

Centering 抑制全局偏置，却可能使目标趋于缺少区分性的均匀分布。较低的教师温度则放大当前 logits 的差别，让教师对单个样本给出更明确的偏好。

两者的作用可以直观概括为：

- **Centering**：不要让所有图片总被同一个输出维度主导。
- **Sharpening**：不要让每张图片都对所有维度毫无偏好。

原论文在 momentum teacher 的设置下分析了这两种作用的互补性。参见 [DINO 论文第 5.3 节：Avoiding collapse](https://arxiv.org/html/2104.14294v2#S5.SS3)。

不过，若 logits 已经严格相等，降低温度也不会凭空创造差异；EMA 与 stop-gradient 本身也不是“数学上保证永不塌缩”的万能机制。DINO 的有效性来自这些设计与增强、初始化及优化过程的共同作用。

### 7.4 Batch 大小仍然重要，但不是因为负样本数量

在 CLIP 中，改变 $B$ 会直接改变 softmax 的候选数量；DINO 的 softmax 始终在 $K$ 个输出维度上进行。

| 改变的量 | 对 DINO 的直接影响 | 不应误解成什么？ |
| --- | --- | --- |
| 增大 batch size $B$ | 每步平均更多图片的梯度，center 统计通常更充分 | 增加 $B-1$ 个负样本 |
| 增大局部视图数 $M$ | 增加跨视图预测约束与计算量 | 增加新的独立原始图片 |
| 改变输出维度 $K$ | 改变 head 的输出空间与 softmax 维数 | 改变人工类别标签的数量 |

所以，“不依赖 batch 内负样本”不等于“batch size 完全无关”。Batch 大小仍影响统计估计、优化噪声、计算效率以及合适的动量和学习率设置；不能直接套用 CLIP 中“batch 越大，候选负样本越多”的解释。

## 8. 语义从哪里来：跨视图预测中的稳定视觉因素

### 8.1 从同一图片的不同视图，学习什么不该变？

回到狗的图片。训练中，学生可能只看到局部内容，却需要预测教师从更大视野得到的分布。

一种直观解释是：为了在裁剪、颜色、尺度等变化下持续完成预测，网络需要寻找比具体像素更稳定的视觉因素，例如形状、部件与对象结构，而不是只记住某个固定位置的颜色。

大量图片共享同一套网络参数，这些可复用的视觉规律就可能形成特征空间中的语义邻近关系：

$$
h(\text{狗的图片 A})
\approx h(\text{狗的图片 B}).
$$

这里的 $\approx$ 表示特征在语义上可能邻近，不表示向量严格相等。**这是理解学习过程的直觉，不是训练标签显式规定“所有狗都必须聚到一起”，也不是对所有数据集都成立的保证。** 增强是否保留语义、图片本身的分布与训练是否稳定都会影响结果。

### 8.2 为什么经常看到 DINO 的对象注意力图？

原始论文发现，DINO 训练的 ViT 中，CLS 对 patch tokens 的注意力可以呈现对象或部件区域，patch 特征也保留了空间信息。这是论文观察到的涌现性质，不是因为预训练 loss 中使用了分割 mask。参见 [DINO 论文第 4.2.2 节](https://arxiv.org/html/2104.14294v2#S4.SS2.SSS2)。

要区分：

- **训练目标**：不同视图的图像级输出分布一致。
- **可视化现象**：某些注意力头关注对象或部件。
- **下游任务**：可以利用预训练特征进一步做检索、分类或密集预测。

“注意力图看起来像分割”不代表 DINO 已经是带完整类别体系的分割模型，也不代表它对每张图都能输出准确 mask。原始 DINO 的目标也不是逐 patch 重建像素，不能把后续方法的 patch-level 训练目标直接套回来。

### 8.3 训练后用什么？能像 CLIP 一样输入文字吗？

训练完成后，通常去掉用于蒸馏的 head，提取 backbone 特征：

$$
I\xrightarrow{f_\theta}h(I).
$$

对于 ViT，CLS 可以作为图像级表示；patch tokens 可以提供空间位置相关的表示。具体使用教师还是学生权重、怎样组合 token，应与所选 checkpoint 和下游评估设置一致。

- **图像检索**：比较图片特征之间的相似性。
- **$k$-NN 分类**：根据有标签参考样本的邻居投票；标签在下游参考集中，不是 DINO 预训练目标。
- **Linear probing**：冻结 backbone，用标签训练一个线性分类器。
- **其他下游任务**：按任务需求提取局部特征或进行微调。

DINO 本身没有文本编码器，也没有通过训练把图片与 “a dog” 这样的字符串对齐。因此它可以学到视觉语义，却**不能仅凭原始 DINO 模型就像 CLIP 一样，把任意文字类别描述直接拿来做图文相似度分类**。

> **DINO 学习的是从图像中组织出的视觉语义空间；CLIP 学习的是由图文配对约束出的跨模态共享语义空间。**

## 9. 最后串起来：一个完整的心智模型

1. **构造监督**：从每张图片生成不同全局与局部视图，利用“同图不同视图”的关系建立预测任务。
2. **生成教师目标**：教师只看全局视图，输出经 centering 与 sharpening 的概率分布，并 stop-gradient。
3. **跨视图匹配**：学生看全部视图，用 soft-target CE 匹配另一视图的教师分布；softmax 在 $K$ 个输出维度上进行。
4. **分工更新**：损失梯度更新学生，学生参数的 EMA 更新教师，教师 logits 的统计 EMA 更新 center。
5. **避免平凡解**：结合平滑教师、中心化与目标锐化，避免只学到“所有图片输出一样”的塌缩表示。
6. **形成视觉特征**：在大量跨视图预测中学习稳定、可迁移的视觉结构，下游通常使用 backbone 而不是蒸馏 head。

从损失构造看，DINO 仍然使用熟悉的：

$$
\boxed{\text{Softmax}+\text{Soft-target Cross Entropy}}
$$

但完整训练机制不能漏掉目标如何产生与更新：

$$
\boxed{
\text{Multi-view Self-distillation}
+\text{EMA Teacher}
+\text{Centering / Sharpening}
}
$$

如果只记住一句与 CLIP 的区别：

> **CLIP 问：“这一批候选里，谁与我配对？”DINO 问：“只看到另一个视图时，我能否预测同一张图的教师表示？”**
