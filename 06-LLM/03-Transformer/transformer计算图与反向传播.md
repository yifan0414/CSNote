---
updated: 2026-09-10
---

# Transformer 计算图与反向传播

反向传播并不是把前向公式倒着读，而是**沿依赖关系逐节点传递梯度，并在共享输入处累加不同路径的贡献**。本文先明确残差节点的规则，再从输出 $Y$ 出发，依次穿过 FFN 和 Self-Attention，最后得到输入 $X$ 的梯度。

正文保留计算顺序、关键结论和路径之间的关系；每节的折叠 callout 给出完整的局部推导。计算图采用高清图片，公式已通过数学排版引擎渲染，可点击图片放大查看。

## 1. 先明确前向模型和反向目标

本文沿用草稿中的简化 **Pre-LN、单头 Attention** 模型。前向先经过 Attention 残差子层，再经过 FFN 残差子层：

$$
\begin{aligned}
\tilde X&=\operatorname{LayerNorm}(X),
&Q&=\tilde XW_Q,\quad K=\tilde XW_K,\quad V=\tilde XW_V,\\
R&=QK^\top,
&S&=R/\sqrt{d_k},\quad A=\operatorname{softmax}(S),\\
O&=AV,
&Y_1&=X+O,\\
Z&=\operatorname{LayerNorm}(Y_1),
&M&=ZW_1+b_1,\\
H&=\phi(M),
&F&=HW_2+b_2,\quad Y=Y_1+F.
\end{aligned}
$$

全文直接使用偏导数形式：$L$ 是标量损失，$\dfrac{\partial L}{\partial U}$ 与变量 $U$ 的形状相同；$\left.\dfrac{\partial L}{\partial U}\right|_{\text{branch}}$ 表示某一支路对 $U$ 的梯度贡献。

$n$ 表示序列长度，$d$ 表示模型维度，$d_{ff}$ 表示 FFN 中间维度，$d_k$、$d_v$ 分别表示 Key 和 Value 的维度。由于这里直接令 $O=AV$ 并与 $X$ 相加，取 $d_v=d$，从而 $X,Y_1,Y\in\mathbb{R}^{n\times d}$。

> [!info]- 模型边界与 Jacobian 记法
> 本文不展开多头拼接、输出投影、mask 和 dropout；偏置保留在前向中，但不推导其参数梯度。两处 LayerNorm 均保留整体 Jacobian 形式，不展开内部及仿射参数求导。
>
> $J_f(U)^\top\dfrac{\partial L}{\partial f(U)}$ 是展平后的 Jacobian–向量乘积简写：严格操作为先将矩阵梯度向量化，乘以转置 Jacobian，再恢复输入形状。$\operatorname{tr}$ 表示迹，$\odot$ 表示逐元素乘法。

## 2. 残差节点：分出去的梯度，还要在输入处加回来

先看靠近输出的残差 $Y=Y_1+F$。**加法节点将上游梯度原样传给两个输入**，因此 $\dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}$，直接支路也收到 $\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y}$。

但 $F$ 又依赖 $Y_1$：它由 $Y_1$ 经过 LayerNorm 和 FFN 计算得到。所以直接支路的贡献只是暂存结果，必须等 FFN 支路返回后再相加。一般地，若 $Y=U+f(U)$，则：

$$
\boxed{\dfrac{\partial L}{\partial U}=\dfrac{\partial L}{\partial Y}+J_f(U)^\top \dfrac{\partial L}{\partial Y}.}
$$

这解释了反向传播中两种看似相反的操作：**前向相加的节点在反向分流；前向被多个算子共用的变量在反向接收各路贡献之和。**

![[_assets/images/transformer-02-残差分流与汇合.png|900]]

> [!note]- 推导｜标量加法、矩阵加法与局部偏导
> 设 $y=a+b$，损失为 $L=L(y)$。先计算局部偏导，再应用链式法则：
>
> $$
> \begin{aligned}
> \dfrac{\partial y}{\partial a}&=1,
> &\dfrac{\partial y}{\partial b}&=1,\\
> \dfrac{\partial L}{\partial a}
> &=\dfrac{\partial L}{\partial y}\dfrac{\partial y}{\partial a}
> =\dfrac{\partial L}{\partial y},
> &\dfrac{\partial L}{\partial b}
> &=\dfrac{\partial L}{\partial y}\dfrac{\partial y}{\partial b}
> =\dfrac{\partial L}{\partial y}.
> \end{aligned}
> $$
>
> 推广到 $Y=Y_1+F$，其中 $Y,Y_1,F\in\mathbb{R}^{n\times d}$。逐元素有：
>
> $$
> \begin{aligned}
> Y_{ij}&=(Y_1)_{ij}+F_{ij}\\
> \dfrac{\partial Y_{ij}}{\partial(Y_1)_{ij}}&=1\\
> \dfrac{\partial Y_{ij}}{\partial F_{ij}}&=1.
> \end{aligned}
> $$
>
> 其他位置的局部偏导为零，所以每个元素只接收相同位置的上游梯度：
>
> $$
> \begin{aligned}
> \left.\dfrac{\partial L}{\partial(Y_1)_{ij}}\right|_{\text{direct}}
> &=\dfrac{\partial L}{\partial Y_{ij}},\\
> \dfrac{\partial L}{\partial F_{ij}}&=\dfrac{\partial L}{\partial Y_{ij}}.
> \end{aligned}
> $$
>
> 把元素重新组成矩阵，得到 $\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y}$、$\dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}$。以展平后的 Jacobian 表示，就是 $\dfrac{\partial Y}{\partial Y_1}=I$、$\dfrac{\partial Y}{\partial F}=I$。这里求的是**输出对输入**的局部偏导，不能用反方向的 $\dfrac{\partial Y_1}{\partial Y}$ 替代。
>
> 若 $F=f(Y_1)$，则前向存在 $Y_1\to Y\to L$ 与 $Y_1\to F\to Y\to L$ 两条路径。第二条路径先得到 $\dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}$，再沿 $F\to H\to M\to Z\to Y_1$ 反传。因此：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial Y_1}
> &=\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}+\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}\\
> &=\dfrac{\partial L}{\partial Y}+J_f(Y_1)^\top \dfrac{\partial L}{\partial Y}.
> \end{aligned}
> $$
>
> $\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y}$ 只描述加法节点分出的那一份贡献，不是 $Y_1$ 的最终总梯度。

## 3. 先完成 FFN：从输出梯度回到中间状态

从 $Y=Y_1+F$ 分流后，我们暂存直接贡献 $\dfrac{\partial L}{\partial Y}$，沿 $F\to H\to M\to Z\to Y_1$ 逐步回传。每个线性层都产生两类结果：一类是继续向前一节点传播的**输入梯度**，另一类是用于更新权重的**参数梯度**。

![[_assets/images/transformer-03-FFN反向传播.png|900]]

### 3.1 输出线性层：同时求输入梯度与权重梯度

对于 $F=HW_2+b_2$，已知 $\dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}$。沿输入方向回传要右乘 $W_2^\top$；对权重求导则使用前向保存的 $H$：

$$
\begin{aligned}
\dfrac{\partial L}{\partial H}&=\dfrac{\partial L}{\partial F}W_2^\top=\dfrac{\partial L}{\partial Y}W_2^\top\\
\dfrac{\partial L}{\partial W_2}&=H^\top \dfrac{\partial L}{\partial F}=H^\top \dfrac{\partial L}{\partial Y}.
\end{aligned}
$$

这两个转置的位置不是记忆规则，而是将损失微分整理成标准迹形式后的结果。

> [!note]- 推导｜输出线性层对输入 $H$ 的梯度
> $H\in\mathbb{R}^{n\times d_{ff}}$，$W_2\in\mathbb{R}^{d_{ff}\times d}$，$F\in\mathbb{R}^{n\times d}$。偏置固定时，$F=HW_2+b_2$ 的微分为：
>
> $$
> dF=(dH)W_2+H(dW_2).
> $$
>
> 先固定 $W_2$、只改变 $H$，于是 $dF=(dH)W_2$。矩阵梯度通过损失的微分定义：
>
> $$
> \begin{aligned}
> dL
> &=\operatorname{tr}(\left(\dfrac{\partial L}{\partial F}\right)^\top  dF)\\
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial F}\right)^\top (dH)W_2\bigr)\\
> &=\operatorname{tr}\bigl(W_2\left(\dfrac{\partial L}{\partial F}\right)^\top  dH\bigr).
> \end{aligned}
> $$
>
> 最后一步使用迹的循环性质 $\operatorname{tr}(ABC)=\operatorname{tr}(CAB)$。与标准形式 $dL=\operatorname{tr}(\left(\dfrac{\partial L}{\partial H}\right)^\top  dH)$ 比较，再转置：
>
> $$
> \begin{aligned}
> \left(\dfrac{\partial L}{\partial H}\right)^\top &=W_2\left(\dfrac{\partial L}{\partial F}\right)^\top ,\\
> \dfrac{\partial L}{\partial H}&=\dfrac{\partial L}{\partial F}W_2^\top,\\
> \dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}\quad&\Longrightarrow\quad \dfrac{\partial L}{\partial H}=\dfrac{\partial L}{\partial Y}W_2^\top.
> \end{aligned}
> $$

> [!note]- 推导｜输出线性层对参数 $W_2$ 的梯度
> 仍从 $dF=(dH)W_2+H(dW_2)$ 出发。这次固定 $H$，只改变 $W_2$，于是 $dF=H(dW_2)$：
>
> $$
> dL=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial F}\right)^\top  H(dW_2)\bigr).
> $$
>
> 与 $dL=\operatorname{tr}(\left(\dfrac{\partial L}{\partial W_2}\right)^\top  dW_2)$ 比较，得到：
>
> $$
> \begin{aligned}
> \left(\dfrac{\partial L}{\partial W_2}\right)^\top &=\left(\dfrac{\partial L}{\partial F}\right)^\top  H,\\
> \dfrac{\partial L}{\partial W_2}&=H^\top \dfrac{\partial L}{\partial F},\\
> \dfrac{\partial L}{\partial F}=\dfrac{\partial L}{\partial Y}\quad&\Longrightarrow\quad \dfrac{\partial L}{\partial W_2}=H^\top \dfrac{\partial L}{\partial Y}.
> \end{aligned}
> $$
>
> 这份梯度用于更新参数；$\dfrac{\partial L}{\partial H}$ 则继续沿计算图向输入传播，两者来自同一个乘积微分的不同项。

### 3.2 激活与输入线性层：沿主链继续回传

$H=\phi(M)$ 是逐元素激活，因此只需把 $\dfrac{\partial L}{\partial H}$ 与局部导数逐元素相乘。随后穿过 $M=ZW_1+b_1$，再次应用线性层规则：

$$
\begin{aligned}
\dfrac{\partial L}{\partial M}&=\dfrac{\partial L}{\partial H}\odot\phi'(M),\\
\dfrac{\partial L}{\partial Z}&=\dfrac{\partial L}{\partial M}W_1^\top,\qquad
\dfrac{\partial L}{\partial W_1}=Z^\top \dfrac{\partial L}{\partial M}.
\end{aligned}
$$

此时拿到的是 $Z$ 的梯度，而不是 $Y_1$ 的梯度：两者之间还有一层 LayerNorm。

> [!note]- 推导｜逐元素激活与链式代入
> 由于 $H=\phi(M)$ 是逐元素操作，对任意位置有：
>
> $$
> \begin{aligned}
> H_{ij}&=\phi(M_{ij})\\
> \dfrac{\partial H_{ij}}{\partial M_{ij}}&=\phi'(M_{ij}).
> \end{aligned}
> $$
>
> 应用链式法则，再把各元素组成矩阵：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial M_{ij}}
> &=\dfrac{\partial L}{\partial H_{ij}}\phi'(M_{ij}),\\
> \dfrac{\partial L}{\partial M}&=\dfrac{\partial L}{\partial H}\odot\phi'(M)\\
> &=(\dfrac{\partial L}{\partial F}W_2^\top)\odot\phi'(M)\\
> &=(\dfrac{\partial L}{\partial Y}W_2^\top)\odot\phi'(M).
> \end{aligned}
> $$
>
> 这里 $\odot$ 是逐元素乘法，不是矩阵乘法。

> [!note]- 推导｜输入线性层的输入梯度、参数梯度及展开式
> 固定偏置，$M=ZW_1+b_1$ 给出 $dM=(dZ)W_1+Z(dW_1)$。分别收集两项，并对第一项使用迹的循环性质：
>
> $$
> \begin{aligned}
> dL
> &=\operatorname{tr}(\left(\dfrac{\partial L}{\partial M}\right)^\top  dM)\\
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial M}\right)^\top (dZ)W_1\bigr)
>  +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial M}\right)^\top  Z(dW_1)\bigr)\\
> &=\operatorname{tr}\bigl(W_1\left(\dfrac{\partial L}{\partial M}\right)^\top  dZ\bigr)
>  +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial M}\right)^\top  Z\,dW_1\bigr).
> \end{aligned}
> $$
>
> 与 $\operatorname{tr}(\left(\dfrac{\partial L}{\partial Z}\right)^\top  dZ)+\operatorname{tr}(\left(\dfrac{\partial L}{\partial W_1}\right)^\top  dW_1)$ 比较、分别转置：
>
> $$
> \begin{aligned}
> \left(\dfrac{\partial L}{\partial Z}\right)^\top &=W_1\left(\dfrac{\partial L}{\partial M}\right)^\top ,
> &\dfrac{\partial L}{\partial Z}&=\dfrac{\partial L}{\partial M}W_1^\top,\\
> \left(\dfrac{\partial L}{\partial W_1}\right)^\top &=\left(\dfrac{\partial L}{\partial M}\right)^\top  Z,
> &\dfrac{\partial L}{\partial W_1}&=Z^\top \dfrac{\partial L}{\partial M}.
> \end{aligned}
> $$
>
> 这与 $F=HW_2$ 的推导完全对应。代入上一节的 $\dfrac{\partial L}{\partial M}$，保留完整的链式展开：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial Z}&=\bigl[(\dfrac{\partial L}{\partial Y}W_2^\top)\odot\phi'(M)\bigr]W_1^\top,\\
> \dfrac{\partial L}{\partial W_1}&=Z^\top\bigl[(\dfrac{\partial L}{\partial Y}W_2^\top)\odot\phi'(M)\bigr].
> \end{aligned}
> $$

### 3.3 穿过 LayerNorm，完成第一次梯度汇合

将 $\dfrac{\partial L}{\partial Z}$ 经过 $Z=\operatorname{LayerNorm}(Y_1)$ 反传，才得到 FFN 支路对 $Y_1$ 的贡献。然后加上从残差节点直接传来的 $\dfrac{\partial L}{\partial Y}$：

$$
\boxed{
\begin{aligned}
\dfrac{\partial L}{\partial Y_1}&=\dfrac{\partial L}{\partial Y}+\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}\\
\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}&=J_{\operatorname{LayerNorm}}(Y_1)^\top \dfrac{\partial L}{\partial Z}.
\end{aligned}
}
$$

**只有这个汇合后的 $\dfrac{\partial L}{\partial Y_1}$，才是下一阶段 Attention 子层的上游梯度。** 不能只使用 FFN 支路返回的部分，也不能在穿过 LayerNorm 之前提前相加。

> [!note]- 推导｜穿过 LayerNorm，再累加直接残差贡献
> 前向 $Z=\operatorname{LayerNorm}(Y_1)$，所以 FFN 支路返回的梯度为：
>
> $$
> \left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}=J_{\operatorname{LayerNorm}}(Y_1)^\top \dfrac{\partial L}{\partial Z}.
> $$
>
> 这表示 $\dfrac{\partial L}{\partial Z}$ 仍须穿过 LayerNorm 才能成为对 $Y_1$ 的贡献，不能直接把 $\dfrac{\partial L}{\partial Z}$ 与 $\dfrac{\partial L}{\partial Y}$ 相加。另一条直接路径早已得到 $\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y}$，现在两者才在同一变量处汇合：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial Y_1}
> &=\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{direct}}+\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}\\
> &=\dfrac{\partial L}{\partial Y}+\left.\dfrac{\partial L}{\partial Y_1}\right|_{\text{FFN}}\\
> &=\dfrac{\partial L}{\partial Y}+J_{\operatorname{LayerNorm}}(Y_1)^\top \dfrac{\partial L}{\partial Z}.
> \end{aligned}
> $$
>
> LayerNorm 在这里仍作为整体函数，其内部求导不在本稿范围内。

## 4. 再完成 Attention：处理权重支路与 Value 支路

现在回到前一个残差 $Y_1=X+O$。同样先分流：$\dfrac{\partial L}{\partial O}=\dfrac{\partial L}{\partial Y_1}$ 进入 Attention，$\left.\dfrac{\partial L}{\partial X}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y_1}$ 暂存，等待稍后在 $X$ 汇合。

Attention 内部不是一条直线。$O=AV$ 首先分出 $A$、$V$ 两条路径：**$A$ 路径穿过 Softmax、缩放和 $QK^\top$，再分出 $Q$、$K$；$V$ 路径不经过这些算子。** 最后 $Q$、$K$、$V$ 三路都回到共同输入 $\tilde X$。

![[_assets/images/transformer-04-Attention反向传播.png|900]]

> [!note]- 推导｜第一个残差节点的局部梯度
> 前向 $Y_1=X+O$ 与 $Y=Y_1+F$ 具有相同的加法结构。在该节点内将两个输入视为独立输入：
>
> $$
> \begin{aligned}
> \dfrac{\partial Y_1}{\partial X}&=I\\
> \dfrac{\partial Y_1}{\partial O}&=I.
> \end{aligned}
> $$
>
> 因此：
>
> $$
> \begin{aligned}
> \left.\dfrac{\partial L}{\partial X}\right|_{\text{direct}}&=\dfrac{\partial L}{\partial Y_1}\\
> \dfrac{\partial L}{\partial O}&=\dfrac{\partial L}{\partial Y_1}.
> \end{aligned}
> $$
>
> 直接贡献暂时保留；$\dfrac{\partial L}{\partial O}$ 则穿过 Attention 和第一层 LayerNorm 后，才产生 $\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}$。

### 4.1 加权求和：从 $O$ 分出 $A$ 和 $V$ 的梯度

对 $O=AV$ 使用乘积微分，可以同时得到注意力权重和 Value 的梯度：

$$
\boxed{
\begin{aligned}
\dfrac{\partial L}{\partial A}&=\dfrac{\partial L}{\partial O}V^\top\\
\dfrac{\partial L}{\partial V}&=A^\top \dfrac{\partial L}{\partial O}.
\end{aligned}
}
$$

$\dfrac{\partial L}{\partial V}$ 已可以进入 Value 投影的反向传播；接下来先沿 $\dfrac{\partial L}{\partial A}$ 继续，计算决定注意力权重的打分梯度。

> [!note]- 推导｜$O=AV$ 的微分及 $A$、$V$ 两个梯度
> 设 $A\in\mathbb{R}^{n\times n}$、$V\in\mathbb{R}^{n\times d_v}$，则 $O\in\mathbb{R}^{n\times d_v}$。由乘积微分：
>
> $$
> dO=d(AV)=(dA)V+A(dV).
> $$
>
> 代入损失的微分，并展开两项：
>
> $$
> \begin{aligned}
> dL
> &=\operatorname{tr}(\left(\dfrac{\partial L}{\partial O}\right)^\top  dO)\\
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial O}\right)^\top [(dA)V+A(dV)]\bigr)\\
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial O}\right)^\top (dA)V\bigr)
>  +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial O}\right)^\top  A(dV)\bigr).
> \end{aligned}
> $$
>
> **先求 $A$ 的梯度。** 第一项要整理为 $\operatorname{tr}(\left(\dfrac{\partial L}{\partial A}\right)^\top  dA)$。利用 $\operatorname{tr}(ABC)=\operatorname{tr}(CAB)$：
>
> $$
> \begin{aligned}
> \operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial O}\right)^\top (dA)V\bigr)
> &=\operatorname{tr}\bigl(V\left(\dfrac{\partial L}{\partial O}\right)^\top  dA\bigr),\\
> \left(\dfrac{\partial L}{\partial A}\right)^\top &=V\left(\dfrac{\partial L}{\partial O}\right)^\top ,\\
> \dfrac{\partial L}{\partial A}&=\dfrac{\partial L}{\partial O}V^\top.
> \end{aligned}
> $$
>
> **再求 $V$ 的梯度。** 第二项直接与 $\operatorname{tr}(\left(\dfrac{\partial L}{\partial V}\right)^\top  dV)$ 比较：
>
> $$
> \begin{aligned}
> \operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial O}\right)^\top  A(dV)\bigr)
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial V}\right)^\top  dV\bigr),\\
> \left(\dfrac{\partial L}{\partial V}\right)^\top &=\left(\dfrac{\partial L}{\partial O}\right)^\top  A,\\
> \dfrac{\partial L}{\partial V}&=A^\top \dfrac{\partial L}{\partial O}.
> \end{aligned}
> $$
>
> 因此 $O=AV$ 的反向结果同时包含 $\dfrac{\partial L}{\partial A}=\dfrac{\partial L}{\partial O}V^\top$ 与 $\dfrac{\partial L}{\partial V}=A^\top \dfrac{\partial L}{\partial O}$，不能只沿 $A$ 一路继续而丢掉 $V$ 的贡献。

### 4.2 Softmax 与缩放：从注意力权重回到原始打分

Softmax 按行归一化，同一行元素通过分母互相耦合。因此，与 FFN 中的逐元素激活不同，不能只乘一个逐元素导数。对第 $i$ 行（用列向量表示），其反向为：

$$
\dfrac{\partial L}{\partial\mathbf s_i}
=\bigl[\operatorname{diag}(\mathbf a_i)-\mathbf a_i\mathbf a_i^\top\bigr]\dfrac{\partial L}{\partial\mathbf a_i}.
$$

逐行得到 $\dfrac{\partial L}{\partial S}$ 后，再穿过 $S=R/\sqrt{d_k}$，得到 $\dfrac{\partial L}{\partial R}=\dfrac{\partial L}{\partial S}/\sqrt{d_k}$。至此才回到未缩放的点积打分 $R$。

> [!note]- 推导｜按行 Softmax 的 Jacobian 与反向传播
> 将第 $i$ 行写成列向量 $\mathbf s_i=[s_{i1},\ldots,s_{in}]^\top$，并令 $\mathbf a_i=\operatorname{softmax}(\mathbf s_i)$。每个元素为：
>
> $$
> a_{ij}=\dfrac{e^{s_{ij}}}{\sum_{k=1}^{n}e^{s_{ik}}}.
> $$
>
> $a_{i1}$ 不仅依赖 $s_{i1}$，还通过分母依赖同一行所有其他元素，因此不能像逐元素激活那样只保留对角导数。记 $D_i=\sum_k e^{s_{ik}}$，商法则给出：
>
> $$
> \begin{aligned}
> \dfrac{\partial a_{ij}}{\partial s_{i\ell}}
> &=\dfrac{\delta_{j\ell}e^{s_{ij}}D_i-e^{s_{ij}}e^{s_{i\ell}}}{D_i^2}\\
> &=a_{ij}\delta_{j\ell}-a_{ij}a_{i\ell}.
> \end{aligned}
> $$
>
> 其中 $\delta_{j\ell}$ 为 Kronecker delta。把所有元素组成 Jacobian：
>
> $$
> J_i=\dfrac{\partial\mathbf a_i}{\partial\mathbf s_i}
> =\operatorname{diag}(\mathbf a_i)-\mathbf a_i\mathbf a_i^\top.
> $$
>
> 分别对行向量对应的列表示求损失的偏导。向量链式法则先给出 $\dfrac{\partial L}{\partial\mathbf s_i}=J_i^\top\dfrac{\partial L}{\partial\mathbf a_i}$；由于 $J_i^\top=J_i$，于是：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial\mathbf s_i}
> &=\bigl[\operatorname{diag}(\mathbf a_i)-\mathbf a_i\mathbf a_i^\top\bigr]\dfrac{\partial L}{\partial\mathbf a_i}\\
> &=\mathbf a_i\odot\dfrac{\partial L}{\partial\mathbf a_i}
>  -\mathbf a_i(\mathbf a_i^\top\dfrac{\partial L}{\partial\mathbf a_i}).
> \end{aligned}
> $$
>
> 逐行计算后恢复矩阵排列，即得到 $\dfrac{\partial L}{\partial S}$。

> [!note]- 推导｜缩放因子如何传到梯度中
> $d_k$ 是固定维度。由 $S=R/\sqrt{d_k}$ 得 $dS=dR/\sqrt{d_k}$。代入损失微分：
>
> $$
> \begin{aligned}
> dL
> &=\operatorname{tr}(\left(\dfrac{\partial L}{\partial S}\right)^\top  dS)\\
> &=\operatorname{tr}\left(\left(\dfrac{\partial L}{\partial S}\right)^\top \dfrac{1}{\sqrt{d_k}}dR\right)\\
> &=\operatorname{tr}\left[\left(\dfrac{\frac{\partial L}{\partial S}}{\sqrt{d_k}}\right)^\top dR\right].
> \end{aligned}
> $$
>
> 与 $dL=\operatorname{tr}(\left(\dfrac{\partial L}{\partial R}\right)^\top  dR)$ 比较，得到 $\dfrac{\partial L}{\partial R}=\dfrac{\partial L}{\partial S}/\sqrt{d_k}$。

### 4.3 点积打分：从 $R$ 分出 $Q$ 和 $K$ 的梯度

对 $R=QK^\top$ 求导，关键是保留前向中 $K$ 的转置关系：

$$
\boxed{
\begin{aligned}
\dfrac{\partial L}{\partial Q}&=\dfrac{\partial L}{\partial R}K\\
\dfrac{\partial L}{\partial K}&=\left(\dfrac{\partial L}{\partial R}\right)^\top  Q.
\end{aligned}
}
$$

现在 $\dfrac{\partial L}{\partial Q}$、$\dfrac{\partial L}{\partial K}$ 和此前得到的 $\dfrac{\partial L}{\partial V}$ 都已就绪。它们分别回传到各自的投影权重，同时向同一个输入 $\tilde X$ 提供梯度贡献。

> [!note]- 推导｜$QK^\top$ 的乘积微分及 $Q$、$K$ 梯度中的转置
> 从 $R=QK^\top$ 出发，先应用乘积法则，再使用转置与微分可交换的性质：
>
> $$
> \begin{aligned}
> dR&=d(QK^\top)\\
> &=(dQ)K^\top+Q\,d(K^\top),\\
> d(K^\top)&=(dK)^\top,\\
> dR&=(dQ)K^\top+Q(dK)^\top.
> \end{aligned}
> $$
>
> 代入 $dL=\operatorname{tr}(\left(\dfrac{\partial L}{\partial R}\right)^\top  dR)$，分开两项：
>
> $$
> dL=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial R}\right)^\top (dQ)K^\top\bigr)
> +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial R}\right)^\top  Q(dK)^\top\bigr).
> $$
>
> **对 $Q$ 求梯度。** 固定 $K$，第一项利用迹的循环性质变形：
>
> $$
> \begin{aligned}
> dL\big|_{dK=0}
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial R}\right)^\top (dQ)K^\top\bigr)\\
> &=\operatorname{tr}\bigl(K^\top \left(\dfrac{\partial L}{\partial R}\right)^\top  dQ\bigr)\\
> &=\operatorname{tr}\bigl((\dfrac{\partial L}{\partial R}K)^\top dQ\bigr).
> \end{aligned}
> $$
>
> 其中 $K^\top \left(\dfrac{\partial L}{\partial R}\right)^\top =(\dfrac{\partial L}{\partial R}K)^\top$。与标准形式 $\operatorname{tr}(\left(\dfrac{\partial L}{\partial Q}\right)^\top  dQ)$ 比较，得到 $\dfrac{\partial L}{\partial Q}=\dfrac{\partial L}{\partial R}K$。
>
> **对 $K$ 求梯度。** 固定 $Q$，第二项使用 $\operatorname{tr}(B(dK)^\top)=\operatorname{tr}(B^\top dK)$：
>
> $$
> \begin{aligned}
> dL\big|_{dQ=0}
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial R}\right)^\top  Q(dK)^\top\bigr)\\
> &=\operatorname{tr}\bigl((\left(\dfrac{\partial L}{\partial R}\right)^\top  Q)^\top dK\bigr).
> \end{aligned}
> $$
>
> 与 $\operatorname{tr}(\left(\dfrac{\partial L}{\partial K}\right)^\top  dK)$ 比较，得到 $\dfrac{\partial L}{\partial K}=\left(\dfrac{\partial L}{\partial R}\right)^\top  Q$。这里转置的是 $\dfrac{\partial L}{\partial R}$，来源是前向中 $K$ 以 $K^\top$ 的形式参与乘法。

### 4.4 投影层：参数分别求导，输入贡献三路相加

$Q$、$K$、$V$ 都是对 $\tilde X$ 的线性投影，所以仍使用已经在 FFN 中推导过的线性层规则。权重各有自己的梯度：

$$
\begin{aligned}
\dfrac{\partial L}{\partial W_Q}&=\tilde X^\top \dfrac{\partial L}{\partial Q}\\
\dfrac{\partial L}{\partial W_K}&=\tilde X^\top \dfrac{\partial L}{\partial K}\\
\dfrac{\partial L}{\partial W_V}&=\tilde X^\top \dfrac{\partial L}{\partial V}.
\end{aligned}
$$

但输入是共享的，必须把三路贡献相加：

$$
\boxed{\dfrac{\partial L}{\partial \tilde X}=\dfrac{\partial L}{\partial Q}W_Q^\top+\dfrac{\partial L}{\partial K}W_K^\top+\dfrac{\partial L}{\partial V}W_V^\top.}
$$

这就是“前向一分为三，反向三路相加”。特别要注意，Value 支路虽然绕过了 Softmax，仍然必须出现在这个总和中。

> [!note]- 推导｜$Q$、$K$、$V$ 投影的参数梯度与输入贡献
> 前向 $\tilde X=\operatorname{LayerNorm}(X)$，且 $Q=\tilde XW_Q$、$K=\tilde XW_K$、$V=\tilde XW_V$。对 $Q$ 路径，乘积微分为：
>
> $$
> dQ=(d\tilde X)W_Q+\tilde X(dW_Q).
> $$
>
> 与 FFN 线性层相同，代入迹形式并循环移位：
>
> $$
> \begin{aligned}
> dL\big|_{Q\text{ 路径}}
> &=\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial Q}\right)^\top (d\tilde X)W_Q\bigr)
> +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial Q}\right)^\top \tilde X(dW_Q)\bigr)\\
> &=\operatorname{tr}\bigl(W_Q\left(\dfrac{\partial L}{\partial Q}\right)^\top  d\tilde X\bigr)
> +\operatorname{tr}\bigl(\left(\dfrac{\partial L}{\partial Q}\right)^\top \tilde X\,dW_Q\bigr).
> \end{aligned}
> $$
>
> 比较微分系数并转置，得到 $\dfrac{\partial L}{\partial W_Q}=\tilde X^\top \dfrac{\partial L}{\partial Q}$ 与 $\left.\dfrac{\partial L}{\partial \tilde X}\right|_{Q}=\dfrac{\partial L}{\partial Q}W_Q^\top$。对另外两条路径分别应用同一规则：
>
> $$
> \begin{aligned}
> Q=\tilde XW_Q:&\quad \dfrac{\partial L}{\partial W_Q}=\tilde X^\top \dfrac{\partial L}{\partial Q},
> &&\left.\dfrac{\partial L}{\partial \tilde X}\right|_{Q}=\dfrac{\partial L}{\partial Q}W_Q^\top,\\
> K=\tilde XW_K:&\quad \dfrac{\partial L}{\partial W_K}=\tilde X^\top \dfrac{\partial L}{\partial K},
> &&\left.\dfrac{\partial L}{\partial \tilde X}\right|_{K}=\dfrac{\partial L}{\partial K}W_K^\top,\\
> V=\tilde XW_V:&\quad \dfrac{\partial L}{\partial W_V}=\tilde X^\top \dfrac{\partial L}{\partial V},
> &&\left.\dfrac{\partial L}{\partial \tilde X}\right|_{V}=\dfrac{\partial L}{\partial V}W_V^\top.
> \end{aligned}
> $$
>
> 前向中同一个 $\tilde X$ 被三条路径共同使用，因此反向不能任选一条，而要相加：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial \tilde X}
> &=\left.\dfrac{\partial L}{\partial \tilde X}\right|_{Q}+\left.\dfrac{\partial L}{\partial \tilde X}\right|_{K}+\left.\dfrac{\partial L}{\partial \tilde X}\right|_{V}\\
> &=\dfrac{\partial L}{\partial Q}W_Q^\top+\dfrac{\partial L}{\partial K}W_K^\top+\dfrac{\partial L}{\partial V}W_V^\top.
> \end{aligned}
> $$

### 4.5 回到 $X$：穿过 LayerNorm，再加上直接残差

三路在 $\tilde X$ 汇合后，一起穿过第一层 LayerNorm，形成 $\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}$。最后与本节开头暂存的直接贡献相加：

$$
\boxed{
\begin{aligned}
\dfrac{\partial L}{\partial X}&=\dfrac{\partial L}{\partial Y_1}+\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}\\
\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}&=J_{\operatorname{LayerNorm}}(X)^\top \dfrac{\partial L}{\partial \tilde X}.
\end{aligned}
}
$$

到这里，从输出 $Y$ 到输入 $X$ 的反向传播才完整结束。

> [!note]- 推导｜第一层 LayerNorm 与最后一次残差累加
> 前向 $\tilde X=\operatorname{LayerNorm}(X)$，其反向把已经汇合的 $\dfrac{\partial L}{\partial \tilde X}$ 变成 Attention 支路对 $X$ 的贡献：
>
> $$
> \left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}=J_{\operatorname{LayerNorm}}(X)^\top \dfrac{\partial L}{\partial \tilde X}.
> $$
>
> 最初的 $Y_1=X+O$ 还分出了 $\left.\dfrac{\partial L}{\partial X}\right|_{\text{direct}}=\dfrac{\partial L}{\partial Y_1}$。因此最后的总梯度为：
>
> $$
> \begin{aligned}
> \dfrac{\partial L}{\partial X}
> &=\left.\dfrac{\partial L}{\partial X}\right|_{\text{direct}}+\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}\\
> &=\dfrac{\partial L}{\partial Y_1}+\left.\dfrac{\partial L}{\partial X}\right|_{\text{Attn}}\\
> &=\dfrac{\partial L}{\partial Y_1}+J_{\operatorname{LayerNorm}}(X)^\top
> \bigl(\dfrac{\partial L}{\partial Q}W_Q^\top+\dfrac{\partial L}{\partial K}W_K^\top+\dfrac{\partial L}{\partial V}W_V^\top\bigr).
> \end{aligned}
> $$
>
> 这一步之后，本文简化 Block 的输入梯度计算才结束。

## 5. 回看整条反向链

整个过程可以按三个层次理解：**局部算子决定梯度如何变换，分支依赖决定梯度去往哪里，共享输入决定梯度在哪里累加。** FFN 主要是一条连续主链；Attention 则先分出 Value 路径，再从打分路径分出 Query 和 Key，最后重新汇合。

检查推导时，最重要的不是孤立记住某个转置，而是确认以下几次累加都没有遗漏：

- 在 $Y_1$：直接残差贡献与 FFN 支路贡献相加。
- 在 $\tilde X$：$Q$、$K$、$V$ 三条投影路径的输入贡献相加。
- 在 $X$：直接残差贡献与 Attention 支路贡献相加。

参数梯度在经过相应线性层时分别产生，不参与这些输入节点的累加。掌握这条组织逻辑后，矩阵微分、迹的循环变换和 Jacobian 链式法则就都落在了明确的计算位置上。

> [!example]- 原始计算图参考
> ![[_assets/images/transformer-01-计算图与反向传播.png|900]]
