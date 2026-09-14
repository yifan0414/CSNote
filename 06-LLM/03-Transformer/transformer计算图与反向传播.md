---
updated: 2026-09-13
---

# Transformer 计算图与反向传播

**Transformer 的反向传播，就是每个算子用自己的局部 VJP，把输出梯度传回输入；多条路径回到同一个变量时，再将贡献相加。**

本文先固定前向模型，再介绍推导 VJP 所需的 trace 技巧，最后从 Block 输出一路推回输入。每一步都按同一个顺序阅读：**前向是什么 → 微分怎么写 → 如何读出输入梯度。** 参数梯度在经过对应算子时一起得到。

## 1. 固定前向模型与反向目标

采用 **Pre-LN、单头 Attention**，省略 mask、dropout 和多头拼接。主线与配图一致，暂不含 Attention 输出投影；第 4.6 节补上它。令序列长度为 $n$，模型维度为 $d$，Query / Key 维度为 $d_k$，FFN 中间维度为 $d_{ff}$。由于直接做残差相加，主线取 Value 维度 $d_v=d$。

### 1.1 完整前向

Attention 子层先归一化，再计算注意力，最后加回输入：

$$
\begin{aligned}
\tilde X&=\operatorname{LN}_1(X),\\[4pt]
Q&=\tilde XW_Q,\qquad K=\tilde XW_K,\qquad V=\tilde XW_V,\\[4pt]
R&=QK^\top,\qquad S=R/\sqrt{d_k},\\[4pt]
A&=\operatorname{softmax}(S),\\[4pt]
O&=AV,\\[4pt]
Y_1&=X+O.
\end{aligned}
$$

Softmax 沿每行计算：$A_{ij}$ 是第 $i$ 个 token 汇总第 $j$ 个 token 内容时的权重。

FFN 子层对每个 token 独立变换特征，再加回子层输入：

$$
\begin{aligned}
Z&=\operatorname{LN}_2(Y_1),\\[4pt]
M&=ZW_1+b_1,\\[4pt]
H&=\phi(M),\\[4pt]
F&=HW_2+b_2,\\[4pt]
Y&=Y_1+F.
\end{aligned}
$$

$\phi$ 是逐元素激活，偏置沿 token 维广播。两处 LayerNorm 各有自己的仿射参数。

> [!note]- 形状速查
> 梯度与其所属变量同形状。全文用 $\mathbb{R}^{\cdots}$ 表示形状，省略 batch 维。
>
> | 变量 | 形状 |
> | --- | --- |
> | $X,\tilde X,Y_1,Z,V,O,F,Y$ | $\mathbb{R}^{n\times d}$ |
> | $Q,K$ | $\mathbb{R}^{n\times d_k}$ |
> | $R,S,A$ | $\mathbb{R}^{n\times n}$ |
> | $M,H$ | $\mathbb{R}^{n\times d_{ff}}$ |
> | $W_Q,W_K$ | $\mathbb{R}^{d\times d_k}$ |
> | $W_V$ | $\mathbb{R}^{d\times d}$ |
> | $W_1,W_2$ | $\mathbb{R}^{d\times d_{ff}}$、$\mathbb{R}^{d_{ff}\times d}$ |
> | $b_1,b_2$ | $\mathbb{R}^{d_{ff}}$、$\mathbb{R}^{d}$ |

### 1.2 反向从哪里开始，到哪里结束？

后续网络已经传回 $\dfrac{\partial L}{\partial Y}$，其中 $L$ 是标量损失。我们要先穿过 FFN 子层得到完整的 $\dfrac{\partial L}{\partial Y_1}$，再穿过 Attention 子层得到 $\dfrac{\partial L}{\partial X}$，同时得到各参数的梯度。

> [!example]- 完整计算图
> ![[_assets/images/transformer-01-前向与局部VJP总览.svg|900]]

## 2. 推导工具：通过 trace 读出局部 VJP

### 2.1 VJP 要做什么？

对当前算子 $T=f(U)$，已知输出梯度 $\dfrac{\partial L}{\partial T}$，计算经这个算子传回 $U$ 的梯度贡献，就是它的局部 VJP。如果 $U$ 还有其他使用路径，需要累加这些路径的贡献，才得到总梯度 $\dfrac{\partial L}{\partial U}$。在当前前向取值固定时，记传入的输出梯度为 $v$：

$$
\boxed{\operatorname{VJP}_f(v)=J_f(U)^\top v.}
$$

这里采用列向量梯度约定，矩阵变量需先展平理解该式，再将结果恢复为输入形状。**实际推导可以直接使用矩阵微分，无需构造 Jacobian。** 正文用完整偏导数表示梯度，只在通用规则中使用 $v$。

### 2.2 为什么 trace 中能读出梯度？

对矩阵 $U$，损失的一阶微分就是各元素的“梯度乘变化量”之和：

$$
\mathrm{d}L
=\sum_{i,j}\frac{\partial L}{\partial U_{ij}}\,\mathrm{d}U_{ij}
=\operatorname{tr}\!\left[
\left(\frac{\partial L}{\partial U}\right)^\top\mathrm{d}U
\right].
$$

$\operatorname{tr}$ 是方阵对角元素之和；$\operatorname{tr}(B^\top\mathrm{d}U)=\sum_{i,j}B_{ij}\mathrm{d}U_{ij}$，只是将逐元素内积写成矩阵形式。$\mathrm{d}U$ 是微小变化，$\partial L/\partial U$ 是梯度，两者含义不同。

因此，只要将损失微分整理为下面的标准形式，就能读出梯度：

$$
\boxed{
\mathrm{d}L=\operatorname{tr}(B^\top\mathrm{d}U)
\quad\Longrightarrow\quad
\frac{\partial L}{\partial U}=B.
}
$$

该等式须对任意 $\mathrm{d}U$ 成立。注意读出的是 $B$，不是 $B^\top$。多个输入时，分别整理出每个输入的微分项。

### 2.3 只需掌握这些整理规则

乘法与转置的微分为：

$$
\mathrm{d}(UW)=\mathrm{d}U\,W+U\,\mathrm{d}W,
\qquad
\mathrm{d}(U^\top)=(\mathrm{d}U)^\top.
$$

在维度相容时，trace 可以拆开求和、循环移位，也可以对整体转置：

$$
\begin{aligned}
\operatorname{tr}(C+D)&=\operatorname{tr}(C)+\operatorname{tr}(D),\\[4pt]
\operatorname{tr}(ABC)&=\operatorname{tr}(BCA)=\operatorname{tr}(CAB),\\[4pt]
\operatorname{tr}(C)&=\operatorname{tr}(C^\top),\qquad (AB)^\top=B^\top A^\top.
\end{aligned}
$$

循环移位不能任意交换因子顺序。处理输入的转置时，常用：

$$
\operatorname{tr}(B\,\mathrm{d}U^\top)
=\operatorname{tr}(B^\top\mathrm{d}U).
$$

后面始终重复同一个过程：**写输出微分 → 代入损失微分 → 整理成输入微分的标准形式 → 读出梯度。** trace 是推导工具，backward 实际执行的是化简后的公式。

> [!note]- 为什么 trace 读出的结果就是 $J^\top v$？
> 用 $\operatorname{vec}$ 表示按固定顺序展平矩阵，前向微分满足：
>
> $$
> \operatorname{vec}(\mathrm{d}T)=J_f(U)\operatorname{vec}(\mathrm{d}U).
> $$
>
> 将输出梯度 $v$ 与输出微分配对：
>
> $$
> \begin{aligned}
> \mathrm{d}L
> &=\operatorname{vec}(v)^\top J_f(U)\operatorname{vec}(\mathrm{d}U)\\[4pt]
> &=\left[J_f(U)^\top\operatorname{vec}(v)\right]^\top\operatorname{vec}(\mathrm{d}U).
> \end{aligned}
> $$
>
> 而 $\operatorname{tr}(B^\top\mathrm{d}U)=\operatorname{vec}(B)^\top\operatorname{vec}(\mathrm{d}U)$，所以 $\operatorname{vec}(B)=J_f(U)^\top\operatorname{vec}(v)$。trace 推导直接求出了这个乘积。

## 3. FFN 反向：从 $Y$ 回到 $Y_1$

![[_assets/images/transformer-03-FFN局部VJP.svg|900]]

### 3.1 残差加法：分别向两个输入原样回传

前向 $Y=Y_1+F$，因此：

$$
\mathrm{d}Y=\mathrm{d}Y_1+\mathrm{d}F,
$$

$$
\mathrm{d}L
=\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial Y}\right)^\top\mathrm{d}Y_1\right]
+\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial Y}\right)^\top\mathrm{d}F\right].
$$

分别读出加法节点对两个输入的贡献：

$$
\boxed{
\frac{\partial L}{\partial F}=\frac{\partial L}{\partial Y},
\qquad
\left.\frac{\partial L}{\partial Y_1}\right|_{\text{direct}}
=\frac{\partial L}{\partial Y}.
}
$$

**先保留对 $Y_1$ 的直接贡献，另一份梯度继续穿过 FFN。** 此时还没得到 $Y_1$ 的总梯度，因为 $F$ 也依赖 $Y_1$。加法的局部 VJP 是 $(v,v)$，两个输入都收到完整梯度，不是各拿一半。

### 3.2 输出线性层：完整示范 trace 推导

前向 $F=HW_2+b_2$。先固定偏置 $b_2$，即令 $\mathrm{d}b_2=0$，只求关于 $H,W_2$ 的局部梯度：

$$
\mathrm{d}F=\mathrm{d}H\,W_2+H\,\mathrm{d}W_2.
$$

代入损失微分，将 $\mathrm{d}H$ 和 $\mathrm{d}W_2$ 分别整理到末尾：

$$
\begin{aligned}
\mathrm{d}L
&=\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial F}\right)^\top\mathrm{d}H\,W_2\right]
+\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial F}\right)^\top H\,\mathrm{d}W_2\right]\\[6pt]
&=\operatorname{tr}\!\left[W_2\left(\frac{\partial L}{\partial F}\right)^\top\mathrm{d}H\right]
+\operatorname{tr}\!\left[\left(H^\top\frac{\partial L}{\partial F}\right)^\top\mathrm{d}W_2\right]\\[6pt]
&=\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial F}W_2^\top\right)^\top\mathrm{d}H\right]
+\operatorname{tr}\!\left[\left(H^\top\frac{\partial L}{\partial F}\right)^\top\mathrm{d}W_2\right].
\end{aligned}
$$

读出输入梯度与权重梯度：

$$
\boxed{
\frac{\partial L}{\partial H}=\frac{\partial L}{\partial F}W_2^\top,
\qquad
\frac{\partial L}{\partial W_2}=H^\top\frac{\partial L}{\partial F}.
}
$$

再固定 $H,W_2$，单独改变偏置。由于偏置沿 token 维广播，有 $\mathrm{d}F_{ij}=\mathrm{d}(b_2)_j$，因此：

$$
\mathrm{d}L
=\sum_j\left(\sum_{i=1}^{n}\frac{\partial L}{\partial F_{ij}}\right)\mathrm{d}(b_2)_j.
$$

偏置 $(b_2)_j$ 被所有 token 共享，读出的梯度沿 token 维累加：

$$
\frac{\partial L}{\partial(b_2)_j}
=\sum_{i=1}^{n}\frac{\partial L}{\partial F_{ij}}.
$$

这一推导给出后面反复使用的矩阵乘法规则：

$$
\boxed{
T=UW
\quad\Longrightarrow\quad
\operatorname{VJP}_{(U,W)\mapsto UW}(v)
=(vW^\top,\;U^\top v).
}
$$

**一次 VJP 可以返回多个输入的梯度。** 参数梯度留给优化器，特征输入的梯度继续向前传播。

### 3.3 激活与输入线性层：继续回到 $Z$

前向 $H=\phi(M)$，由于激活逐元素作用：

$$
\mathrm{d}H=\phi'(M)\odot\mathrm{d}M.
$$

将它与输出梯度逐元素配对，就得到：

$$
\boxed{\frac{\partial L}{\partial M}
=\frac{\partial L}{\partial H}\odot\phi'(M).}
$$

接着，前向 $M=ZW_1+b_1$ 与第 3.2 节结构相同，直接复用线性层规则：

$$
\begin{aligned}
\frac{\partial L}{\partial Z}&=\frac{\partial L}{\partial M}W_1^\top,\\[4pt]
\frac{\partial L}{\partial W_1}&=Z^\top\frac{\partial L}{\partial M},\\[4pt]
\frac{\partial L}{\partial(b_1)_j}&=\sum_{i=1}^{n}\frac{\partial L}{\partial M_{ij}}.
\end{aligned}
$$

### 3.4 LayerNorm 与汇合：得到完整的 $Y_1$ 梯度

前向 $Z=\operatorname{LN}_2(Y_1)$。当前只有对 $Z$ 的梯度，还要穿过 LayerNorm 才能回到 $Y_1$：

$$
\left.\frac{\partial L}{\partial Y_1}\right|_{\text{FFN}}
=\operatorname{VJP}_{\operatorname{LN}_2}\!\left(\frac{\partial L}{\partial Z}\right).
$$

这里的 LayerNorm VJP 指关于特征输入的梯度；第 5 节统一推导具体公式与仿射参数梯度。现在将这份贡献与第 3.1 节保留的直接贡献相加：

$$
\boxed{
\frac{\partial L}{\partial Y_1}
=\frac{\partial L}{\partial Y}
+\operatorname{VJP}_{\operatorname{LN}_2}\!\left(\frac{\partial L}{\partial Z}\right).
}
$$

**梯度必须回到同一个变量才能相加。** $\partial L/\partial Z$ 即使与 $\partial L/\partial Y_1$ 同形状，也不能跳过 LayerNorm 直接相加。下一节使用的是这里已经汇合完整的 $\partial L/\partial Y_1$。

> [!example]- 残差路径：加法处回传，共同输入处累加
> ![[_assets/images/transformer-02-残差分流与汇合-大公式.png|900]]

## 4. Attention 反向：从 $Y_1$ 回到 $X$

![[_assets/images/transformer-04-Attention局部VJP.svg|900]]

### 4.1 残差加法：保留直接贡献，进入 Attention

前向 $Y_1=X+O$。复用加法的 VJP：

$$
\frac{\partial L}{\partial O}=\frac{\partial L}{\partial Y_1},
\qquad
\left.\frac{\partial L}{\partial X}\right|_{\text{direct}}
=\frac{\partial L}{\partial Y_1}.
$$

保留对 $X$ 的直接贡献，接下来计算 Attention 分支贡献。

### 4.2 加权求和：同时得到 $A$ 与 $V$ 的梯度

前向 $O=AV$，微分为：

$$
\mathrm{d}O=\mathrm{d}A\,V+A\,\mathrm{d}V.
$$

与第 3.2 节一样，将微分代入 trace 并整理：

$$
\mathrm{d}L
=\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial O}V^\top\right)^\top\mathrm{d}A\right]
+\operatorname{tr}\!\left[\left(A^\top\frac{\partial L}{\partial O}\right)^\top\mathrm{d}V\right].
$$

因此：

$$
\boxed{
\frac{\partial L}{\partial A}=\frac{\partial L}{\partial O}V^\top,
\qquad
\frac{\partial L}{\partial V}=A^\top\frac{\partial L}{\partial O}.
}
$$

**这次分叉不是复制梯度，而是矩阵乘法的 VJP 返回分别对应两个输入的结果。** 对 $V$ 的梯度直接进入 Value 投影；下面先沿 $A$ 路径继续。Value 路径不经过 Softmax 或 Query–Key 点积。

### 4.3 Softmax：从整行权重的梯度回到打分

前向 $A=\operatorname{softmax}(S)$，按行计算。为清楚展示微分，取任意一行，将其写成列向量 $a=\operatorname{softmax}(s)$。由 $a_j=e^{s_j}/\sum_k e^{s_k}$ 可得：

$$
\mathrm{d}a_j
=a_j\left(\mathrm{d}s_j-\sum_k a_k\,\mathrm{d}s_k\right),
$$

即：

$$
\mathrm{d}a=a\odot\mathrm{d}s-a(a^\top\mathrm{d}s).
$$

将输出梯度与微分配对，整理出 $\mathrm{d}s$：

$$
\begin{aligned}
\mathrm{d}L
&=\left(\frac{\partial L}{\partial a}\right)^\top\mathrm{d}a\\[4pt]
&=\left[
 a\odot\frac{\partial L}{\partial a}
-a\left(a^\top\frac{\partial L}{\partial a}\right)
\right]^\top\mathrm{d}s.
\end{aligned}
$$

因此，恢复为矩阵逐行计算的公式是：

$$
\boxed{
\frac{\partial L}{\partial S_{ij}}
=A_{ij}\left(
\frac{\partial L}{\partial A_{ij}}
-\sum_{k=1}^{n}A_{ik}\frac{\partial L}{\partial A_{ik}}
\right).
}
$$

**一个打分影响整行权重，所以要减去整行梯度的加权和。** 实现只需逐行求和与逐元素运算。这就是 $J_{\operatorname{softmax}}^\top v$ 的化简结果，和矩阵乘法一样属于局部 VJP。

> [!note]- 一个自检性质
> 每行 $\partial L/\partial S$ 的元素之和为零。因为给一行全部打分加上相同常数，不会改变 Softmax 输出。

### 4.4 缩放与点积：回到 $Q$ 与 $K$

前向 $S=R/\sqrt{d_k}$，维度 $d_k$ 固定，因此：

$$
\mathrm{d}S=\frac{\mathrm{d}R}{\sqrt{d_k}},
\qquad
\boxed{\frac{\partial L}{\partial R}
=\frac{1}{\sqrt{d_k}}\frac{\partial L}{\partial S}.}
$$

接着，前向 $R=QK^\top$，微分为：

$$
\mathrm{d}R=\mathrm{d}Q\,K^\top+Q\,\mathrm{d}K^\top.
$$

对 Query 的项，循环移动 $K^\top$；对 Key 的项，用第 2.3 节处理输入转置的规则：

$$
\begin{aligned}
\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial R}\right)^\top\mathrm{d}Q\,K^\top\right]
&=\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial R}K\right)^\top\mathrm{d}Q\right],\\[6pt]
\operatorname{tr}\!\left[\left(\frac{\partial L}{\partial R}\right)^\top Q\,\mathrm{d}K^\top\right]
&=\operatorname{tr}\!\left[\left(\left(\frac{\partial L}{\partial R}\right)^\top Q\right)^\top\mathrm{d}K\right].
\end{aligned}
$$

读出：

$$
\boxed{
\frac{\partial L}{\partial Q}=\frac{\partial L}{\partial R}K,
\qquad
\frac{\partial L}{\partial K}=\left(\frac{\partial L}{\partial R}\right)^\top Q.
}
$$

加上第 4.2 节保留的 Value 梯度，现在三个投影的输出梯度都已得到。

### 4.5 投影、LayerNorm 与残差：完成两次汇合

前向 $Q=\tilde XW_Q$、$K=\tilde XW_K$、$V=\tilde XW_V$。各自使用线性层的 VJP，向共同输入 $\tilde X$ 返回一份贡献：

$$
\left.\frac{\partial L}{\partial\tilde X}\right|_Q
=\frac{\partial L}{\partial Q}W_Q^\top,
\quad
\left.\frac{\partial L}{\partial\tilde X}\right|_K
=\frac{\partial L}{\partial K}W_K^\top,
\quad
\left.\frac{\partial L}{\partial\tilde X}\right|_V
=\frac{\partial L}{\partial V}W_V^\top.
$$

**第一次汇合：在 $\tilde X$ 处累加三个投影的贡献。**

$$
\boxed{
\frac{\partial L}{\partial\tilde X}
=\frac{\partial L}{\partial Q}W_Q^\top
+\frac{\partial L}{\partial K}W_K^\top
+\frac{\partial L}{\partial V}W_V^\top.
}
$$

各权重的梯度分别为：

$$
\frac{\partial L}{\partial W_Q}=\tilde X^\top\frac{\partial L}{\partial Q},
\qquad
\frac{\partial L}{\partial W_K}=\tilde X^\top\frac{\partial L}{\partial K},
\qquad
\frac{\partial L}{\partial W_V}=\tilde X^\top\frac{\partial L}{\partial V}.
$$

前向 $\tilde X=\operatorname{LN}_1(X)$，因此 Attention 分支继续返回：

$$
\left.\frac{\partial L}{\partial X}\right|_{\text{Attn}}
=\operatorname{VJP}_{\operatorname{LN}_1}\!\left(\frac{\partial L}{\partial\tilde X}\right).
$$

**第二次汇合：在 $X$ 处加上第 4.1 节保留的残差贡献。**

$$
\boxed{
\frac{\partial L}{\partial X}
=\frac{\partial L}{\partial Y_1}
+\operatorname{VJP}_{\operatorname{LN}_1}\!\left(\frac{\partial L}{\partial\tilde X}\right).
}
$$

到这里，整个 Block 的输入梯度已计算完整。

### 4.6 如果 Attention 还有输出投影

含输出投影时，前向将 $Y_1=X+O$ 换成：

$$
O_{\text{proj}}=OW_O,
\qquad Y_1=X+O_{\text{proj}}.
$$

反向将第 4.1 节的 Attention 分支入口改为 $O_{\text{proj}}$，再经过一次线性层 VJP；此时 $\partial L/\partial O$ 由下面的第二式计算：

$$
\begin{aligned}
\frac{\partial L}{\partial O_{\text{proj}}}&=\frac{\partial L}{\partial Y_1},\\[4pt]
\frac{\partial L}{\partial O}&=\frac{\partial L}{\partial O_{\text{proj}}}W_O^\top,\\[4pt]
\frac{\partial L}{\partial W_O}&=O^\top\frac{\partial L}{\partial O_{\text{proj}}}.
\end{aligned}
$$

随后从第 4.2 节继续。此时可取 $V,O\in\mathbb{R}^{n\times d_v}$，并相应令 $W_V\in\mathbb{R}^{d\times d_v}$、$W_O\in\mathbb{R}^{d_v\times d}$，由输出投影保证残差两端同形状。残差直接贡献仍是 $\partial L/\partial Y_1$。

## 5. 补全 LayerNorm 的局部 VJP

前面两次用到 LayerNorm，现在统一给出它的具体公式。**每次只在当前 token 的特征维内计算，且两层分别使用自己的输入统计量与参数。**

取一个 token 的特征为列向量 $x\in\mathbb{R}^{d}$，局部前向为：

$$
\begin{aligned}
\mu&=\frac{1}{d}\sum_{j=1}^{d}x_j,
\qquad \sigma^2=\frac{1}{d}\sum_{j=1}^{d}(x_j-\mu)^2,\\[4pt]
\hat x&=\frac{x-\mu\mathbf 1}{\sqrt{\sigma^2+\epsilon}},
\qquad z=\gamma\odot\hat x+\beta.
\end{aligned}
$$

$\epsilon>0$ 固定，$\gamma,\beta\in\mathbb{R}^{d}$ 是仿射参数。先穿过仿射变换：

$$
\frac{\partial L}{\partial\hat x}
=\frac{\partial L}{\partial z}\odot\gamma.
$$

再穿过标准化，得到：

$$
\boxed{
\frac{\partial L}{\partial x}
=\frac{1}{\sqrt{\sigma^2+\epsilon}}
\left[
\frac{\partial L}{\partial\hat x}
-\operatorname{mean}\!\left(\frac{\partial L}{\partial\hat x}\right)\mathbf 1
-\hat x\,\operatorname{mean}\!\left(\hat x\odot\frac{\partial L}{\partial\hat x}\right)
\right].
}
$$

$\operatorname{mean}$ 只对当前 token 的 $d$ 个特征求平均。括号内三项依次对应：直接改变分子的影响、均值变化的修正、方差变化的修正。

> [!note]- 从微分读出 LayerNorm 的 VJP
> 固定仿射参数，标准化部分的微分为：
>
> $$
> \begin{aligned}
> \mathrm{d}\mu&=\frac{1}{d}\mathbf 1^\top\mathrm{d}x,\\[4pt]
> \mathrm{d}\sigma^2&=\frac{2}{d}(x-\mu\mathbf 1)^\top\mathrm{d}x,\\[4pt]
> \mathrm{d}\hat x
> &=\frac{1}{\sqrt{\sigma^2+\epsilon}}
> \left[\mathrm{d}x-\frac{\mathbf 1^\top\mathrm{d}x}{d}\mathbf 1
> -\hat x\frac{\hat x^\top\mathrm{d}x}{d}\right].
> \end{aligned}
> $$
>
> 代入 $\mathrm{d}L=(\partial L/\partial\hat x)^\top\mathrm{d}\hat x$，将所有项整理成关于 $\mathrm{d}x$ 的内积：
>
> $$
> \mathrm{d}L
> =\left\{\frac{1}{\sqrt{\sigma^2+\epsilon}}
> \left[
> \frac{\partial L}{\partial\hat x}
> -\frac{\mathbf 1^\top(\partial L/\partial\hat x)}{d}\mathbf 1
> -\hat x\frac{\hat x^\top(\partial L/\partial\hat x)}{d}
> \right]\right\}^\top\mathrm{d}x.
> $$
>
> 读出大括号中的向量，就是正文的输入梯度。这里仍然没有构造 Jacobian。

最后，仿射参数被各 token 共享。恢复 token 索引 $i$ 后：

$$
\frac{\partial L}{\partial\gamma_j}
=\sum_{i=1}^{n}\frac{\partial L}{\partial z_{ij}}\hat x_{ij},
\qquad
\frac{\partial L}{\partial\beta_j}
=\sum_{i=1}^{n}\frac{\partial L}{\partial z_{ij}}.
$$

## 6. 回看计算图：局部回传与路径累加

整篇推导只用了两种动作：

- **算子内部做 VJP：** 由输出梯度计算各输入梯度。加法返回 $(v,v)$，矩阵乘法返回 $(vW^\top,U^\top v)$，Softmax 和 LayerNorm 使用各自的化简公式。
- **共同变量处做累加：** 将这个变量经不同使用路径得到的贡献相加，得到它的总梯度，再继续向前传播。

主线中，特征梯度有三处关键汇合：

| 共同变量 | 需要相加的贡献 |
| --- | --- |
| $Y_1$ | FFN 分支经过 $\operatorname{LN}_2$ 的贡献，加残差直接贡献 |
| $\tilde X$ | Query、Key、Value 三个投影的贡献 |
| $X$ | Attention 分支经过 $\operatorname{LN}_1$ 的贡献，加残差直接贡献 |

固定分支参数，将完整分支记为 $f$，残差子层 $U\mapsto U+f(U)$ 的整体 VJP 为：

$$
\boxed{\operatorname{VJP}_{U\mapsto U+f(U)}(v)
=v+\operatorname{VJP}_f(v).}
$$

分支内部的“大 VJP”由前面逐步推导的局部 VJP 组合而成。显式写成 $J^\top v$，或化简为矩阵乘法、求和与逐元素运算，表达的都是同一个输出梯度到输入梯度的映射。
