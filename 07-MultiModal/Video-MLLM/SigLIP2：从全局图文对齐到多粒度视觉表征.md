---
created: 2026-09-12
updated: 2026-09-12
aliases:
  - SigLIP2
  - SigLIP 2
arxiv: https://arxiv.org/abs/2502.14786
tags:
  - multimodal
  - vision-encoder
---

![[_assets/images/siglip2-01-2502.14786-training-overview.png|900]]

上图为原论文 Figure 1：在原有 SigLIP 双塔之外，训练时增加 LocCa decoder、EMA teacher 和辅助表示头。图中的 $100\%$ 与 $20\%$ 表示相应目标覆盖的训练进程比例，**不是 loss 权重，也不是样本准确率**。图片来源：[SigLIP 2 原论文](https://arxiv.org/html/2502.14786v1#S1.F1)，作者 Michael Tschannen 等，CC BY 4.0。

> **SigLIP 2 保留 SigLIP 的双塔结构与逐对 sigmoid loss，但不再只训练“整张图片与整段文本是否匹配”：它同时引入描述与定位任务、局部到全局的自蒸馏、掩码位置的特征预测，并改进多语言数据与小模型的数据选择，让同一个视觉编码器既能形成全局语义，也能提供更有用的局部视觉特征。**

本文承接 [[07-MultiModal/Video-MLLM/SigLIP：从逐对二分类到共享语义空间.md|SigLIP：从逐对二分类到共享语义空间]]，沿用“**监督信号 → 网络架构 → 损失构造 → 参数更新 → 下游使用**”的组织方式。原论文中的正式名称是 **SigLIP 2**，本文标题使用 SigLIP2 方便检索。

理解 SigLIP 2，可以沿着五个问题展开：

| 核心问题 | 简要答案 |
| --- | --- |
| SigLIP 已经会图文匹配，为什么还要改？ | 全局匹配不充分约束局部位置、区域细节与稠密视觉特征 |
| 监督信号增加了什么？ | 图文配对之外，增加自动生成的区域—描述对应关系，以及图像自身构造的教师目标 |
| 网络推理时变复杂了吗？ | 标准版本仍可作为双塔编码器使用；训练用的 decoder 与自监督辅助分支不必带到推理中 |
| 多个 loss 如何共同学习？ | 它们从不同路径更新共享视觉编码器，但文本塔、decoder 和 teacher 的更新方式不同 |
| 对 MLLM 有什么意义？ | 改进的不只是整图 embedding，也包括接入语言模型的未池化视觉 tokens |

最重要的区别先记住：

> **CLIP → SigLIP，主要改变“图文配对这道题怎么算 loss”；SigLIP → SigLIP 2，主要改变“除了图文配对，还让视觉编码器做哪些题，以及给它看什么数据”。**

## 1. 监督信号：从一道全局判断题，扩展到多种互补任务

### 1.1 原始 SigLIP 擅长什么，又没有直接要求什么？

继续使用前篇的例子：

- 图片 $I$：一只狗在草地上跑。
- 文本 $T$：“a dog running on grass”。

原始 SigLIP 主要要求：

$$
\operatorname{score}(I,T)\quad\text{足够高},
$$

并降低与不匹配文本的分数。

但“整张图与这句话匹配”没有直接给出以下监督：

- 狗位于图片的哪个区域？
- 哪些视觉 tokens 对应狗，哪些对应草地？
- 把狗的一部分遮住，剩余上下文是否仍能支持合理的局部表示？
- 图片中有文字、小物体或多个相似对象时，特征是否保留了足够细节？

这不是说原始 SigLIP **完全没有**局部信息。全局 loss 也会通过 pooling 向 patch tokens 回传梯度；问题是，**全局匹配做好了，并不自动保证局部表示也最适合定位、分割或下游视觉语言理解**。

### 1.2 SigLIP 2 增加了哪些监督来源？

| 训练任务 | 监督从哪里来？ | 主要约束什么？ |
| --- | --- | --- |
| Sigmoid image-text loss | 原始图文配对及 batch 内交叉负配对 | 整图与整段文本的语义对应 |
| LocCa captioning / localization | 图片描述，以及自动标注的区域—描述配对 | 图像内容、区域语言与位置的联系 |
| Local-to-global self-distillation | 同一张图的全局视图与局部视图，目标由 EMA teacher 生成 | 局部视图与整体语义的一致性 |
| Masked prediction | 未遮挡 teacher 在相应 patch 位置的特征 | 遮挡情况下的局部特征预测 |

另外两项改进作用于**数据**，不能混成新的 loss：

- **多语言混合与去偏过滤**：改变基础训练数据的组成。
- **ACID 在线数据筛选**：为部分小模型动态选择更值得学习的训练样本。

NaFlex 则主要改变**输入预处理、位置编码适配与分辨率训练方式**，也不是另一种图文损失。上述模块及其分阶段组合见 [论文第 2 节](https://arxiv.org/html/2502.14786v1#S2)。

## 2. 网络架构：区分发布时的双塔与训练时的辅助分支

### 2.1 保留下来的主干：图像编码器与文本编码器

仍将图文编码成同维度向量：

$$
I_i\xrightarrow{f_{\theta_v}}z_i^I,
\qquad
T_j\xrightarrow{g_{\theta_t}}z_j^T,
\qquad
z_i^I,z_j^T\in\mathbb{R}^{d}.
$$

这里的 $f$、$g$ 包括各自的编码器、整体表示提取与必要的输出映射，与前篇的记账方式一致。

标准固定分辨率版本继续使用带可学习位置编码的 ViT。官方发布说明指出，这些 checkpoint 与原 SigLIP 的标准 ViT、双塔实现兼容；文本侧需要配套更换词表和 tokenizer。**这种兼容不表示任意大小、任意分辨率的权重都能直接塞进同一个配置。** 参见 [官方 checkpoint 说明](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/README_siglip2.md)。

### 2.2 图像侧：一套 patch 特征，服务多个训练目标

图像经过 ViT 后得到未池化特征：

$$
I_i\rightarrow\text{patches}\rightarrow\text{ViT}\rightarrow H_i^I,
\qquad
H_i^I\in\mathbb{R}^{N_I\times d_v}.
$$

其中 $N_I$ 是视觉 patch 数量，$d_v$ 是视觉 hidden dimension。本文统一使用 $\mathbb{R}^{\cdots}$ 表示 shape。

这份 $H_i^I$ 有不同用途：

1. **全局图文匹配**：经过 MAP（Multihead Attention Pooling）等表示处理，得到整图向量 $z_i^I$。
2. **LocCa 辅助任务**：decoder 通过 cross-attention 读取未池化的 $H_i^I$。
3. **自监督辅助任务**：在额外视图上提取整体或逐 patch 表示，经辅助头计算匹配目标。
4. **下游 MLLM**：可以保留多个空间位置的 hidden states，再交给下游 projector 或其他连接模块。

这里有两种不同的 attention：

- **MAP pooling**：图像分支内部，用可学习 query 聚合视觉 tokens。
- **Decoder cross-attention**：辅助 decoder 的查询读取视觉 tokens。

后者确实引入训练时的图文交互，**但不等于把用于检索的双塔改成了每比较一对图文就要运行一次的 cross-encoder**。

### 2.3 文本侧：新的 tokenizer，不是把 Gemma LLM 当作文本塔

论文采用 multilingual Gemma tokenizer，词表大小为 $256{,}000$，文本序列长度设为 $64$，tokenization 前将文本转为小写。

要区分：

> **使用 Gemma tokenizer，不等于使用完整 Gemma 语言模型作为文本编码器。**

SigLIP 2 的文本塔仍是自己的 Transformer 编码分支；它不是负责对话的自回归大语言模型，也不是下一节的 LocCa decoder。

此外，pooling 细节应以具体实现为准：论文第 2.1 节把图文表示池化概括为 MAP head，但官方演示仅显式将图像侧设为 `pool_type='map'`；其文本实现默认使用 `pool_type='last'`，配合 EOS padding 取最后位置，再经过输出 head。**不要据此认定所有发布模型的文本侧都改成了 MAP pooling。** 参见 [官方演示配置](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/SigLIP2_demo.ipynb) 与 [官方文本编码器](https://github.com/google-research/big_vision/blob/main/big_vision/models/proj/image_text/text_transformer.py)。

### 2.4 模型大小：名称描述的是视觉骨干，不是整个训练系统

论文发布四种视觉模型规模：

| 视觉模型 | 论文给出的视觉参数量 | 需要注意 |
| --- | --- | --- |
| ViT-B | 约 $8{,}600$ 万 | 固定分辨率 B/16、B/32 还使用小模型数据筛选微调 |
| ViT-L | 约 $3.03$ 亿 | 文本塔采用对应规模配置 |
| ViT-So400m | 约 $4$ 亿 | 既有固定分辨率，也有 NaFlex 发布版本 |
| ViT-g | 约 $10$ 亿 | 搭配 So400m 规模文本塔，而非同样大小的 g 文本塔 |

这些数值不是“双塔 + decoder + teacher”的总参数量。是否使用 NaFlex、patch size 和输入分辨率，都要另外看 checkpoint 名称与配置。参见 [论文模型说明](https://arxiv.org/html/2502.14786v1#S2.SS1)。

## 3. 全局对齐损失：SigLIP 的逐对二分类没有被替换

### 3.1 相似度、尺度与 bias 保持同一个逻辑

对图文向量进行 $L_2$ 归一化：

$$
\bar z_i^I=\frac{z_i^I}{\lVert z_i^I\rVert_2},
\qquad
\bar z_j^T=\frac{z_j^T}{\lVert z_j^T\rVert_2}.
$$

然后计算：

$$
c_{ij}=(\bar z_i^I)^\top\bar z_j^T,
\qquad
s_{ij}=\alpha c_{ij}+b,
\qquad
\alpha=\operatorname{exp}(a)>0.
$$

其中 $a$ 与 $b$ 是可学习参数。全文沿用前篇和官方实现的**加性 bias** 约定。

### 3.2 配对标签与 BCE 仍然相同

对于包含 $B$ 对图文的 batch，定义：

$$
y_{ij}=\begin{cases}
1,&i=j,\\
0,&i\ne j,
\end{cases}
\qquad
p_{ij}=\operatorname{sigmoid}(s_{ij}).
$$

全局图文损失为：

$$
\boxed{
\mathcal{L}_{\mathrm{sig}}
=-\frac{1}{B}\sum_{i=1}^{B}\sum_{j=1}^{B}
\left[
y_{ij}\operatorname{log}p_{ij}
+(1-y_{ij})\operatorname{log}(1-p_{ij})
\right]
}
$$

这里仍然是所有配对求和后除以 $B$，不是 $B^2$。论文明确沿用原 SigLIP 实现，参见 [论文第 2.2 节](https://arxiv.org/html/2502.14786v1#S2.SS2)。

因此，前篇的重要结论全部保留：

- 每个候选配对分别计算 sigmoid，不要求一行输出之和为 $1$。
- 不需要另算一个“反方向 BCE”。
- 负配对仍然重要，false negatives 不会自动消失。
- 逐项 loss 天然可加，但完整配对仍有 $B^2$ 项。
- Sigmoid 输出不能未经校准就当成现实场景中的匹配概率。

单看这个目标，对 logit 的梯度仍为：

$$
\frac{\partial\mathcal{L}_{\mathrm{sig}}}{\partial s_{ij}}
=\frac{p_{ij}-y_{ij}}{B}.
$$

**SigLIP 2 的变化不在这条梯度公式里，而在视觉编码器还会收到其他任务的梯度。**

## 4. LocCa：让视觉特征同时支持“说出内容”和“指出位置”

### 4.1 为什么要接一个 decoder？

一个全局图文分数只回答“匹不匹配”。如果要求模型逐 token 预测描述，或根据描述预测区域坐标，视觉表示就需要为这些更具体的输出提供依据。

SigLIP 2 为此接入 LocCa（Location-aware Captioners）式辅助任务：

$$
H_i^I\xrightarrow{\text{cross-attention}}\text{Transformer Decoder}
\rightarrow\text{目标序列}.
$$

Decoder 读取的是 **MAP pooling 之前的视觉 tokens**，不是只读取整图 embedding。它是额外模块，与用于 sigmoid loss 的 Text Encoder 分开；其形状参考文本编码器，但增加 cross-attention，层数减半。

### 4.2 三种题型分别是什么？

下面仍以“草地上的狗”为例。示例只解释条件与目标的关系，不是官方控制 token 的逐字格式。

| 任务 | 给 decoder 什么条件？ | 要预测什么？ |
| --- | --- | --- |
| Image captioning | 图像 | 整图描述：“a dog running on grass” |
| Automatic referring expression prediction | 图像 + 区域描述：“the dog on the left” | 对应区域的 bounding box 坐标 |
| Grounded captioning | 图像 + 某个 bounding box 坐标 | 该区域的描述：“a brown dog” |

可以将后两项理解为两个方向：

$$
\text{图像} + \text{区域描述}\rightarrow\text{区域位置},
$$

$$
\text{图像} + \text{区域位置}\rightarrow\text{区域描述}.
$$

其中“automatic referring expression prediction”容易因名称被误读；在本文讨论的训练配方中，它对应的是**根据描述预测框坐标**，不是只生成一句指代表达。

区域—描述配对由自动标注产生：从 alt-text 中抽取 n-grams，结合开放词汇检测构造区域信息，同时还使用固定对象类别集合。因此，这不等于为全部训练图片新增人工绘制的框，也不表示伪标注完全没有噪声。参见 [论文 LocCa 训练说明](https://arxiv.org/html/2502.14786v1#S2.SS2)。

### 4.3 Loss 怎么理解？

令 $u_1,\dots,u_L$ 是一个目标序列，$C$ 表示当前任务条件。对自回归形式，可以写出教学性表达：

$$
\mathcal{L}_{\mathrm{AR}}
=-\sum_{t=1}^{L}
\operatorname{log}P_{\theta_d}
\left(u_t\mid u_{<t},C,H_i^I\right).
$$

这里预测的序列可以表达描述，也可以表达区域坐标；$\theta_d$ 是辅助 decoder 参数。

但不能把所有 captioning 步骤都说成标准自回归训练：论文以 $50\%$ 的概率对整图 caption 使用 **parallel prediction**，从 mask tokens 并行预测所有 caption tokens，且不使用 causal attention mask。

论文对每个样本训练上述三种目标，相当于进行 $3$ 次 decoder 前向；由于词表较大，还对 decoder loss 采用分块实现。这里将三种任务组成的整体目标记为：

$$
\mathcal{L}_{\mathrm{LocCa}}.
$$

这个符号表示论文采用的 LocCa 目标，不把上面的简化求和冒充包含全部归一化、任务控制与并行预测细节的官方实现。

### 4.4 为什么推理时可以不要这个 decoder？

训练时，梯度沿着：

$$
\mathcal{L}_{\mathrm{LocCa}}
\rightarrow\text{Decoder}
\rightarrow H_i^I
\rightarrow\theta_v
$$

更新视觉编码器。

因此，即使之后移除 decoder，已经学到的视觉参数仍然保留了这些训练任务带来的影响。**Decoder 是训练视觉表示的工具，不是 SigLIP 2 编码器在每次推理时必须运行的组件。**

原论文明确说明，该 decoder 不包含在模型发布中。所以下载 SigLIP 2 双塔权重后，不能仅凭它曾经训练过 captioning，就认为它已经是可直接生成描述、坐标或对话的完整模型。

## 5. 自蒸馏与掩码预测：从图像自身构造局部学习目标

### 5.1 第一项：局部视图向全局 teacher 学习

考虑同一张图片的两种观察方式：

- **Teacher**：看全局视图，能看到更完整的对象与上下文。
- **Student**：看局部裁剪，只能看到一部分内容。

这里的 student 就是正在训练的视觉编码器。Teacher 不是一个额外从头联合优化的独立模型，而是 student 参数的指数移动平均版本：

$$
\boxed{
\theta_{\mathrm{teacher}}
\leftarrow
\mu\theta_{\mathrm{teacher}}
+(1-\mu)\theta_{\mathrm{student}}
}
$$

其中 $\mu$ 为 EMA 系数。Teacher 分支提供目标，不通过该匹配损失的反向传播直接更新。

论文使用 $1$ 个全局 teacher 视图与 $8$ 个局部 student 视图，在额外 MLP head 形成的高维表示空间中进行匹配。

为了突出监督关系，将这个目标抽象写为：

$$
\mathcal{L}_{\mathrm{SD}}
=\frac{1}{K}\sum_{k=1}^{K}
\mathcal{D}\left(
\operatorname{sg}(q_{\mathrm{teacher}}(I^{\mathrm{global}})),
q_{\mathrm{student}}(I_k^{\mathrm{local}})
\right),
\qquad K=8.
$$

其中：

- $q$ 表示经过辅助 head 与相应目标处理后的表示。
- $\operatorname{sg}$ 表示 stop-gradient。
- $\mathcal{D}$ 代指论文沿用的自蒸馏一致性损失；这里不把它简化成“原始 embedding 的均方误差”。

这不是让每个原始 patch 向量都等于整图向量，而是让**局部视图经过编码与辅助头后，能够预测 teacher 的整体语义目标**。具体增强、损失与超参数沿用 SILC，参见 [论文第 2.3 节](https://arxiv.org/html/2502.14786v1#S2.SS3)。

### 5.2 第二项：遮住 patch，预测 teacher 在该位置的特征

Masked prediction 使用不同的视图关系：

- Teacher 和 student 看同一个全局视图。
- Teacher 输入不遮挡。
- Student 将 $50\%$ 的 embedded image patches 替换为 mask tokens。
- 只在被遮挡的位置上，要求 student 匹配 teacher 的逐 patch 特征目标。

设被遮挡的位置集合为 $\mathcal{M}$，可以抽象写为：

$$
\boxed{
\mathcal{L}_{\mathrm{MP}}
=\frac{1}{|\mathcal{M}|}
\sum_{p\in\mathcal{M}}
\mathcal{D}\left(
\operatorname{sg}(q_{\mathrm{teacher},p}(I)),
q_{\mathrm{student},p}(\widetilde I)
\right)
}
$$

这里 $\widetilde I$ 表示 patch embedding 层面经过遮挡的输入，不是把原始图片像素简单涂黑。

这项任务需要区分三件事：

1. **目标是 teacher 特征，不是原始 RGB 像素。** 不应直接解释成 MAE 式像素重建。
2. **比较的是对应空间位置。** 不是任意 student patch 与任意 teacher patch 两两做图文匹配。
3. **被 mask 的位置仍有表示槽位。** 不应把它理解为推理时永久删除这些视觉 tokens。

### 5.3 两种自监督项互补在哪里？

| 维度 | Local-to-global self-distillation | Masked prediction |
| --- | --- | --- |
| Student 看什么？ | 局部裁剪视图 | 带 patch masks 的全局视图 |
| Teacher 看什么？ | 全局视图 | 同一个未遮挡全局视图 |
| 匹配粒度 | 视图级整体表示 | 被遮挡位置的逐 patch 表示 |
| 直观任务 | 看局部，理解整体语义 | 借助上下文，预测缺失位置的语义特征 |

Teacher 目标来自图像自身，而不是新增的分割类别或人工深度标签。**“自监督”说的是这两项新增目标的构造方式，不是说整个 SigLIP 2 不再使用图文监督。**

### 5.4 为什么给自监督分支单独做数据增强？

一个局部裁剪可能不再包含原 caption 描述的主体。例如，原 caption 写的是“狗在草地上跑”，但裁剪只剩草地。

如果仍强行把该裁剪与原 caption 当作完整正配对，可能破坏图文对齐。

因此，论文用原图分支计算 SigLIP 与 LocCa loss，把额外增强视图留给自蒸馏和掩码预测。**它不是把所有任务都改成在同一组随机局部 crop 上训练。**

## 6. 总损失与参数更新：不同分支，不同训练阶段

### 6.1 先训练全局对齐与 LocCa，再加入自监督

对标准固定分辨率路线，论文采用分阶段训练，而不是第一步就打开所有目标。

前 $80\%$ 的训练进程：

$$
\boxed{
\mathcal{L}_{\mathrm{early}}
=\mathcal{L}_{\mathrm{sig}}
+\mathcal{L}_{\mathrm{LocCa}}
}
$$

两项使用相同权重。

最后 $20\%$ 加入自监督项：

$$
\boxed{
\mathcal{L}_{\mathrm{late}}
=\mathcal{L}_{\mathrm{sig}}
+\mathcal{L}_{\mathrm{LocCa}}
+\gamma\left(
\mathcal{L}_{\mathrm{SD}}
+0.25\mathcal{L}_{\mathrm{MP}}
\right)
}
$$

不同视觉模型规模对应：

$$
\gamma=
\begin{cases}
0.25,&\text{B},\\
0.5,&\text{L},\\
1.0,&\text{So400m},\\
0.5,&\text{g}.
\end{cases}
$$

注意，$0.25$ 是掩码预测相对于自蒸馏的基础系数，$\gamma$ 再整体缩放这两项。它们不是两种互斥的权重表。

到 $80\%$ 进度时，teacher 从当前 student 初始化；新增辅助 heads、mask token 及相应优化器状态再进行初始化。上述公式按论文权重关系整理，各 loss 的内部归一化仍需与原方法配套。参见 [论文自监督训练配方](https://arxiv.org/html/2502.14786v1#S2.SS3)。

### 6.2 哪些参数实际更新？

| 参数或模块 | 主要更新来源 | 标准双塔推理是否需要？ |
| --- | --- | --- |
| Student 视觉编码器 | Sigmoid、LocCa、自蒸馏、masked prediction，取决于阶段 | 需要 |
| 文本编码器及输出 head | 图文 sigmoid loss | 做文本编码与图文匹配时需要 |
| 全局图文表示头、logit scale 与 bias | 图文 sigmoid loss | 取决于是否计算全局匹配分数 |
| LocCa decoder | LocCa loss 的梯度 | 不需要，且不随编码器发布 |
| Student 自监督辅助 heads、mask token | 对应的自监督 loss | 不需要 |
| EMA teacher 分支 | 按 EMA 规则跟随 student，而非直接接受匹配目标的梯度更新 | 不需要 |

特别注意：**LocCa decoder 不等于 Text Encoder。** Captioning loss 通过 decoder 更新视觉塔，并不会因此自动成为原文本塔的训练目标。

### 6.3 共享视觉参数如何接收多任务梯度？

在自监督项已经开启的阶段：

$$
\nabla_{\theta_v}\mathcal{L}_{\mathrm{late}}
=\nabla_{\theta_v}\mathcal{L}_{\mathrm{sig}}
+\nabla_{\theta_v}\mathcal{L}_{\mathrm{LocCa}}
+\gamma\nabla_{\theta_v}\mathcal{L}_{\mathrm{SD}}
+0.25\gamma\nabla_{\theta_v}\mathcal{L}_{\mathrm{MP}}.
$$

不同目标共享视觉编码器，但要求它保留不同类型的信息：

- Sigmoid：哪些内容与整段文本对应。
- LocCa：哪些内容支持描述生成与位置预测。
- Self-distillation：局部观察如何关联全局语义。
- Masked prediction：空间位置的表示如何利用上下文。

**这不是分别训练四个互不相关的视觉编码器，再把输出拼起来。** 梯度会在同一组视觉参数上汇合，也可能相互牵制，所以权重、训练阶段和增强策略都重要。

## 7. 多语言与基础数据：能力不只由 loss 决定

### 7.1 数据池与采样比例是两件事

论文使用 WebLI，描述的数据池包含约 $100$ 亿张图片、$120$ 亿条 alt-text，覆盖 $109$ 种语言。

实际训练 mixture 不是按这些语言均匀采样，而是：

- $90\%$ 的图文配对来自英语网页。
- $10\%$ 来自非英语网页。

该比例用于兼顾英语任务与多语言任务表现。严格说，这是按**来源网页语言**构造的混合比例，不应改写成“每个 batch 都有精确比例的中文样本”，也不能据此推断每种语言的效果相同。

更大的多语言词表解决了文本表示的入口问题；多语言图文配对则提供了学习信号。**仅替换 tokenizer、但不进行相应训练，并不能把原模型自动变成多语言模型。** 参见 [论文数据与架构设置](https://arxiv.org/html/2502.14786v1#S2.SS1)。

### 7.2 去偏过滤不等于“已经没有偏见”

论文还对训练数据应用去偏方法，缓解敏感属性的表示不平衡及其与其他概念的偏置关联。

作者报告了一些文化多样性与 representation bias 指标的改善，但在按收入、地理区域细分的部分表现差异指标上，收益很小或没有明显收益。

因此，应说“**在论文评估的部分指标上有所改善**”，不能写成“已经实现所有语言、地区和群体之间的公平”。参见 [论文第 3.5 节](https://arxiv.org/html/2502.14786v1#S3.SS5)。

### 7.3 训练规模中的“样本数”不要误读

基础训练设置包括：

- Batch size：论文记为 $32$ k。
- 总训练量：$400$ 亿次样本呈现。
- 基础学习率：$10^{-3}$。
- Decoupled weight decay：$10^{-4}$。
- Cosine schedule，包含 $20{,}000$ 个 warmup steps。
- 初始视觉输入为 $256\times256$，patch size 为 $16$，产生 $256$ 个视觉 tokens。

这里的 $400$ 亿是训练累计看到的 examples，**不是说收集了 $400$ 亿张互不重复的新图片**；也不是 sigmoid loss 中交叉组合出来的候选配对数。

## 8. ACID：给小模型选好练习题，而不是直接模仿 teacher logits

### 8.1 这里的 teacher 与 EMA teacher 不是同一回事

为了加强最小的固定分辨率 B/16、B/32 模型，论文在额外微调阶段采用 ACID（Active Curation as Implicit Distillation），即把主动数据筛选视作隐式蒸馏。名称与机制见 [ACID 原论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Udandarao_Active_Data_Curation_Effectively_Distills_Large-Scale_Multimodal_Models_CVPR_2025_paper.pdf)。

其基本流程是：

1. 先取一个比实际训练 batch 更大的候选 super-batch。
2. 用较强的 reference teacher 和当前 learner 评估样本的 learnability。
3. 联合选择更值得当前 learner 学习的样本，组成训练 batch。
4. Learner 在被选中的样本上继续使用**原 sigmoid image-text loss**训练。

典型设置从 $64$ k 的 super-batch 选择 $32$ k 的训练 batch；B/32 使用更强的数据过滤设置。不能把这里的 learnability 简化成“只选 teacher 分数最高的图片”，也不能理解成“只选 learner loss 最大的噪声样本”。

### 8.2 为什么叫 implicit distillation？

常见显式蒸馏直接构造：

$$
\text{student 输出}\longleftrightarrow\text{teacher 输出}
$$

之间的蒸馏 loss。

这里 teacher 主要通过**决定 student 看到哪些数据**传递知识，而不是再要求 student 直接拟合 teacher 的 logits。

论文为此使用一个 SigLIP 2 So400m reference model，并先在高质量筛选数据上额外训练 $10$ 亿次样本呈现，再用于 ACID。小模型额外微调 $40$ 亿次样本呈现，学习率降到 $10^{-5}$，移除 weight decay，只使用 sigmoid loss。

| 维度 | 第 5 节的 EMA teacher | ACID reference teacher |
| --- | --- | --- |
| 从哪里来？ | 当前 student 的指数移动平均 | 经过额外数据训练的强模型 |
| 做什么？ | 产生图像级与 patch 级自监督目标 | 帮助给候选训练数据评分和筛选 |
| Student 学什么？ | 匹配教师表示目标 | 在筛选后的图文配对上训练 |
| 是否显式增加表示匹配 loss？ | 是 | 该小模型微调阶段不增加此类显式蒸馏目标 |

这项额外优化不是所有尺寸、所有变体的共同步骤，尤其不能自动套到 NaFlex 上。参见 [论文第 2.5 节](https://arxiv.org/html/2502.14786v1#S2.SS5)。

## 9. 分辨率与 NaFlex：把视觉 token 预算和图片长宽比拆开考虑

### 9.1 标准版本：每个固定分辨率对应自己的 checkpoint

对 patch size 为 $P$、输入为 $H\times W$ 且边长可被 $P$ 整除的图像：

$$
N_I=\frac{H}{P}\frac{W}{P}.
$$

以 $P=16$ 为例：

| 输入尺寸 | Patch 网格 | 视觉 token 数 |
| --- | --- | --- |
| $256\times256$ | $16\times16$ | $256$ |
| $384\times384$ | $24\times24$ | $576$ |
| $512\times512$ | $32\times32$ | $1{,}024$ |

论文在训练进度 $95\%$ 处恢复 checkpoint，将位置编码调整到目标网格，再在目标分辨率继续完成训练；部分版本还将 patch size 从 $16$ 适配为 $14$。

这与“推理时把任意图片直接调成任意大小，完全不用训练适配”不是一回事。固定分辨率模型的不同分辨率版本是**不同 checkpoint**。参见 [论文第 2.4.1 节](https://arxiv.org/html/2502.14786v1#S2.SS4.SSS1)。

### 9.2 NaFlex：固定 patch 大小，灵活选择网格形状和长度

NaFlex 结合了两个方向的思想：

- **NaViT**：尽量保持图片原始长宽比。
- **FlexiViT**：让一个模型支持不同的序列长度 / 分辨率设置。

给定 patch size $P$ 与目标序列长度预算 $N_{\max}$，NaFlex 选择处理后的尺寸 $H'\times W'$，满足：

$$
H'=n_hP,\qquad W'=n_wP,
\qquad
N_I=n_hn_w\le N_{\max},
$$

同时尽量保持：

$$
\frac{H'}{W'}\approx\frac{H}{W}.
$$

因此，“目标序列长度”更适合理解为**这次处理的 token 预算**，实际有效 patch 数可以更少。

### 9.3 一个长图例子：相同 token 数，不同空间网格

假设原图是 $256\times1{,}024$ 的横向图片，patch size 为 $16$，预算为 $256$ 个 tokens。下面是用于理解预处理约束的理想整除例子，不是额外实验结果。

**强制缩放为正方形：**

$$
256\times1{,}024
\rightarrow256\times256
\rightarrow16\times16\text{ 网格}
\rightarrow256\text{ 个 tokens}.
$$

横向内容被明显压缩，文字和物体形状发生变化。

**保留长宽比的一种可行方案：**

$$
256\times1{,}024
\rightarrow128\times512
\rightarrow8\times32\text{ 网格}
\rightarrow256\text{ 个 tokens}.
$$

两者的 token 数相同，但空间采样方式不同。NaFlex 的意义不是凭空多出细节，而是**在既定预算下，尽量减少长宽比扭曲，并允许任务需要时使用更大的预算**。

“Native aspect ratio”也不是严格零形变：为了让尺寸成为 patch size 的整数倍，仍可能存在小幅取整误差。

### 9.4 位置编码、padding 与 attention mask 如何配套？

只有可变尺寸输入还不够，模型也必须知道每个 patch 在哪里、哪些位置是补齐的。

NaFlex 会：

1. 将图像拆为 patch 序列，保留 patch 坐标与 padding 信息。
2. 将可学习的二维位置编码，通过带抗混叠的双线性插值，调整到实际非方形网格。
3. 当有效长度小于目标长度时进行补齐。
4. 在 attention 层和 MAP head 中屏蔽 padding tokens。

论文的基础位置编码对应 $16\times16$ 网格，即 $256$ 个位置。对前面的长图例子，需要适配到 $8\times32$ 网格，而不是仅看“序列长度同为 $256$”就照搬位置排列。

因此，NaFlex 需要专门的图像预处理与 ViT 实现，不能仅在标准 SigLIP 2 配置上改一个 `image_size` 就视作等价。参见 [论文第 2.4.2 节](https://arxiv.org/html/2502.14786v1#S2.SS4.SSS2) 与 [官方 NaFlex 使用说明](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/README_siglip2.md)。

### 9.5 NaFlex 的训练路线与标准版并不完全相同

论文从 $90\%$ 训练进度处的 checkpoint 开始进行 NaFlex 适配，按 mini-batch 均匀采样目标长度：

$$
N_{\max}\in\{128,256,576,784,1{,}024\}.
$$

同时，将对应最后 $10\%$ 的学习率 schedule 拉长 $3.75$ 倍；对最大长度减半 batch，并增加步数以控制内存开销。

**一个重要例外：论文的 NaFlex 路线不采用前文的 self-distillation 与 masked prediction。** 作者明确这样做是为了控制实现和计算复杂度；也不能默认它包含固定分辨率 B 模型的 ACID 微调。

所以，不应把 SigLIP 2 家族概括成“所有 checkpoint 都开启完全相同的四个 loss，只是输入尺寸不同”。

论文还指出，NaFlex 在训练长度之间的插值表现较好，但训练范围之外的外推并不好。**支持可变长度不等于可以任意增加 token 数而保证质量。**

## 10. 实验应该怎样读：区分整图能力与局部特征能力

### 10.1 零样本分类与图文检索：原有核心能力仍然重要

![[_assets/images/siglip2-02-2502.14786-classification-retrieval.png|900]]

上表保留原论文 Table 1 的完整结果。分类侧包括 ImageNet 及其相关测试，检索侧包括 COCO、Flickr 与多语言 XM3600；检索指标为 Recall@1。

以同为 B/16、输入 $256\times256$ 的两行作例子：

- ImageNet 零样本准确率：SigLIP 为 $76.7\%$，SigLIP 2 为 $79.1\%$。
- COCO 文本到图像 Recall@1：$47.4\%$ 与 $53.2\%$。
- XM3600 文本到图像 Recall@1：$22.5\%$ 与 $40.7\%$。

这些结果支持“新的配方改善了全局匹配与多语言表示”，但不是对每项技术单独贡献的消融。B 模型还包含额外 ACID 微调，不能把所有提升都归给某一个 loss。

论文总体上观察到 SigLIP 2 相对 SigLIP 的改进，尤其是小模型；但不要把作者的总体结论扩大成“每个模型在每一列都超过所有基线”。例如，多语言专用 mSigLIP 在部分 XM3600 指标上仍更高。参见 [论文第 3.1 节与 Table 1](https://arxiv.org/html/2502.14786v1#S3.SS1)。

### 10.2 稠密预测：不是只看 pooled embedding

![[_assets/images/siglip2-03-2502.14786-dense-prediction.png|900]]

这里测试冻结的视觉表示，通过线性层或 DPT decoder 进行稠密任务评估：

- 语义分割看 mIoU，越高越好。
- 深度估计看 RMSE，越低越好。
- 表面法线估计看 angular RMSE，越低越好。

例如，So400m/14、输入 $384\times384$ 时，ADE20k 分割 mIoU 从 SigLIP 的 $40.8$ 到 SigLIP 2 的 $45.4$；NYUv2 深度 RMSE 分别为 $0.563$ 与 $0.466$。

这类结果更直接地支持“视觉表示对局部任务更有用”，但**输出分割图、深度图的仍是额外训练的下游预测头，不是裸 SigLIP 2 编码器自动输出这些结果**。同时，它也没有在所有指标上胜过所有模型。参见 [论文第 3.3 节](https://arxiv.org/html/2502.14786v1#S3.SS3)。

### 10.3 MLLM 与定位：看完整评估协议，别只看模型名字

论文还做了几类迁移评估：

| 评估方向 | 如何使用视觉编码器？ | 能支持什么结论？ |
| --- | --- | --- |
| VLM / MLLM | 连接 Gemma 2 的 $20$ 亿参数 LLM，先冻结视觉塔进行多模态训练，再做下游微调 | 在论文配方中，SigLIP 2 是更有效的视觉特征来源 |
| Referring expression comprehension | 冻结视觉编码器，连接从头训练的 $6$ 层 decoder | 未池化特征对语言条件下的区域定位更有帮助 |
| Open-vocabulary detection | 通过 OWL-ViT 方式进行适配和微调 | 编码器可作为开放词汇检测的更好初始化 |
| NaFlex 检索 | 在不同 token 预算下比较自然图像与 OCR / 文档 / 屏幕数据 | 保持长宽比的收益与图像类型、预算有关 |

VLM 评估的初始多模态训练使用 $5{,}000$ 万个 examples；这是样本数，不应误写成同样数量的 optimizer steps。论文总体上报告相对 SigLIP 的改善，但部分下游数据集并非处处提升。

定位任务中，LocCa 专门训练的模型在部分对比中仍优于 SigLIP 2；NaFlex 在自然图像任务上也不保证优于标准版本。更准确的总结是：**SigLIP 2 改善了多种能力之间的整体平衡，不是把所有专门模型在所有设置下都替代了。** 参见 [VLM 评估](https://arxiv.org/html/2502.14786v1#S3.SS2)、[定位评估](https://arxiv.org/html/2502.14786v1#S3.SS4) 与 [NaFlex 评估](https://arxiv.org/html/2502.14786v1#S3.SS1.SSS1)。

## 11. 用在 Video-MLLM 中：更好的视觉塔，不是自动完成时序理解

### 11.1 先问自己：要全局分数，还是空间 tokens？

**做帧级语义检索：**

$$
I_f\rightarrow z_f^I,
\qquad
Q\rightarrow z^T,
\qquad
\operatorname{score}(I_f,Q)
=\alpha(\bar z_f^I)^\top\bar z^T+b.
$$

这里 $I_f$ 是第 $f$ 帧，$Q$ 是检索文本。使用的是图文共享空间，适合比较“哪一帧整体更符合这段描述”。

**做 MLLM 的视觉输入：**

$$
I_f\rightarrow H_f^I
\xrightarrow{\text{Projector}}X_f
\rightarrow\text{LLM},
$$

其中：

$$
H_f^I\in\mathbb{R}^{N_f\times d_v},
\qquad
X_f\in\mathbb{R}^{N_f\times d_{\mathrm{LLM}}}.
$$

这是一种常见的逐 token projector 示意；如果下游另有 resampler 或压缩模块，token 数也可以改变。

两条路径不同：接入 MLLM 时，往往不需要原始文本塔、全局匹配 bias，或预训练的 LocCa decoder，而是使用自己的语言模型和连接模块。

### 11.2 Dense features 更好，不代表任意 patch 都是已校准的文本 embedding

前篇已经强调：

> 整图与 query 很相关，不等于已经知道该保留哪些 patch。

SigLIP 2 增强了局部表示，但这条区分依然成立：

- 自监督辅助头的表示空间，不应与双塔最终共享 embedding 空间直接混同。
- 未池化视觉 hidden states，不一定与最终文本 embedding 具有相同维度、尺度或训练语义。
- 即使维度恰好相同，直接做 patch–text 点积也不等于获得经过验证的定位或剪枝分数。

因此，要用它做 query-aware token pruning，仍需要明确特征层、对齐方式、评分模块与下游验证。**“局部特征更强”是可以进一步研究的条件，不是论文已经证明某种剪枝策略有效。**

### 11.3 NaFlex 不等于免费减少计算

如果一个视频保留 $F$ 帧，第 $f$ 帧有 $N_f$ 个视觉 tokens，那么未压缩的视觉 token 总数为：

$$
N_{\mathrm{video}}=\sum_{f=1}^{F}N_f.
$$

例如，$32$ 帧、每帧 $256$ 个 tokens，共有：

$$
32\times256=8{,}192
$$

个视觉 tokens。若改成每帧 $1{,}024$ 个，则增加到：

$$
32\times1{,}024=32{,}768.
$$

这只是 token 计数示例，不是论文实测的吞吐或显存数据。更多 tokens 会增加视觉编码与下游处理负担；在普通全注意力的分数计算中，长度的影响还包含二次项。

NaFlex 提供的是**按输入和任务调节预算的能力**，不是在不损失信息的前提下自动剪掉无用 tokens。若使用 NaFlex 产生不同空间网格，还要让下游正确处理有效位置、padding 与坐标，而不是始终假设每帧都是方形网格。

### 11.4 图像模型的能力边界仍然存在

以上视频用法是基于编码器接口的下游分析，不是 SigLIP 2 论文直接验证的视频结论。

SigLIP 2 的这些预训练目标并没有直接解决：

- 帧之间的时间顺序。
- 动作先后与事件因果关系。
- 跨帧对象跟踪。
- 长视频记忆与跨片段推理。

逐帧使用 SigLIP 2，可以提供更好的单帧视觉表示；时序建模、帧选择、压缩与多模态对齐，仍由下游视频系统负责。相关学习入口见 [[07-MultiModal/Video-MLLM/03-clip-siglip.md|CLIP 与 SigLIP 学习]]。

## 12. 最后串起来：SigLIP 2 的完整心智模型

1. **保留全局对齐**：仍用双塔、归一化 embedding、scale 与 bias，对图文候选配对计算 sigmoid + BCE。
2. **增加语言与位置监督**：训练时让 LocCa decoder 读取未池化视觉 tokens，学习整图描述、描述到区域、区域到描述。
3. **增强局部表示**：标准路线后期通过 EMA teacher，引入局部到全局自蒸馏与掩码位置的特征预测。
4. **改进训练数据**：多语言 tokenizer、英语与非英语混合、去偏过滤；部分小模型再通过 ACID 筛选训练样本。
5. **区分输入路线**：固定分辨率版本分别适配 checkpoint；NaFlex 使用不同的预处理与位置编码适配，支持一个 checkpoint 下的可变网格与长度，但训练配方并不完全相同。
6. **按下游需要取表示**：整图 embedding 用于匹配，未池化视觉 tokens 用于 MLLM 或稠密任务；辅助训练模块不必随推理保留。

把三代方法放在一起：

| 维度 | CLIP | SigLIP | SigLIP 2 |
| --- | --- | --- | --- |
| 全局图文题型 | 候选集合中的互斥选择 | 逐对匹配判断 | 保留逐对匹配判断 |
| 全局图文 loss | 双向 softmax CE | Sigmoid BCE | 仍为 sigmoid BCE |
| 核心推理结构 | 双塔 | 双塔 | 标准版本仍为双塔 |
| 额外描述与定位任务 | 原始配方不包含 | 原始配方不包含 | LocCa 辅助 decoder |
| 额外视觉自监督 | 原始配方不包含 | 原始配方不包含 | 标准路线后期加入自蒸馏与 masked prediction |
| 多语言能力来源 | 取决于训练数据与文本系统 | 另有 mSigLIP 等多语言设置 | 多语言 tokenizer 与明确的数据混合配方 |
| 小模型优化 | 非本文讨论重点 | 非本文讨论重点 | 部分固定分辨率 B 模型使用 ACID |
| 原生长宽比与可变长度 | 原始标准版本不以此为核心 | 原始标准版本不以此为核心 | 另有 NaFlex 路线 |
| 是否自动成为完整 MLLM | 否 | 否 | 否 |

可以把 SigLIP 2 的总体思路概括为：

$$
\boxed{
\text{全局图文对齐}
+\text{描述与定位监督}
+\text{视觉自监督}
+\text{数据与输入适配}
}
$$

这是一张**家族配方的概念清单**，不是说每个 checkpoint 都启用了全部步骤。

真正要记住的是：

> **SigLIP 学会判断“整张图与这段话是否匹配”；SigLIP 2 在保留这个能力的同时，让视觉编码器学习更多关于内容、位置与局部上下文的约束。它的价值不只是更高的整图匹配分数，而是更适合被不同视觉语言系统复用的表示。**

## 13. 原始资料与延伸阅读

- [SigLIP 2 原论文：arXiv:2502.14786](https://arxiv.org/abs/2502.14786)。本文训练配方与实验以其公开版本为依据。
- [原论文 HTML 全文](https://arxiv.org/html/2502.14786v1)。包含训练细节、结果与附录。
- [官方模型与 checkpoint 说明](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/README_siglip2.md)。用于核对模型尺寸、固定分辨率与 NaFlex 兼容性。
- [官方 SigLIP 2 演示](https://github.com/google-research/big_vision/blob/main/big_vision/configs/proj/image_text/SigLIP2_demo.ipynb)。用于核对 tokenizer、模型配置与双塔使用方式。
- [[07-MultiModal/Video-MLLM/SigLIP：从逐对二分类到共享语义空间.md|前篇：SigLIP 的逐对 BCE、bias、梯度与 batch 机制]]。
- [[07-MultiModal/Video-MLLM/CLIP：从图文配对到共享语义空间.md|前篇：CLIP 的双塔与共享语义空间]]。

本文的训练概览与实验表图片均来自 Michael Tschannen 等作者的 SigLIP 2 论文，按原文的 CC BY 4.0 许可保留署名与来源；正文的示例、符号展开与 Video-MLLM 联系用于帮助理解，不作为论文额外报告的实验结论。
