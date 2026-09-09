---
title: 最大似然估计（MLE）
tags:
  - math
  - probability
  - mle
created: 2026-09-08
updated: 2026-09-09
---

继续把这条链闭环。

你现在已经知道：

$$
D_{\mathrm{KL}}(p\|q)
=
H(p,q)-H(p)
$$

于是对固定真实分布 $p$ 来说：

$$
H(p)
$$

是常数，所以：

$$
\boxed{
\min_q D_{\mathrm{KL}}(p\|q)
\iff
\min_q H(p,q)
}
$$

而 cross entropy 是：

$$
H(p,q)
=
-\mathbb E_{x\sim p}\log q(x)
$$

接下来只差一步：

> **为什么最大似然 MLE 恰好也是在最小化这个东西？**

---

## 从 MLE 的问题开始

假设真实世界会生成数据：

$$
x _1,x_ 2,\dots,x_N
$$

我们不知道真实分布 $p_{\text{data}}$。

现在有一个参数化模型：

$$
q_\theta(x)
$$

比如一个神经网络。

我们的目标是找到一组参数 $\theta$，让模型尽可能解释这些已经观察到的数据。

MLE 说：

$$
\boxed{
\theta^*
=
\arg\max_\theta
P(x _1,x_ 2,\dots,x_N\mid \theta)
}
$$

意思就是：

> 找一个模型，使“我们手头这批数据出现”这件事尽可能合理。

如果样本近似独立同分布：

$$
P(x _1,\dots,x_N\mid\theta)
=
\prod_{i=1}^{N}q_\theta(x_i)
$$

所以：

$$
\theta^*
=
\arg\max_\theta
\prod_{i=1}^{N}q_\theta(x_i)
$$

---

# 为什么要取 log？

因为乘积很麻烦。

取 log：

$$
\log
\prod_i q_\theta(x_i)
=
\sum_i\log q_\theta(x_i)
$$

而且 log 单调递增，所以最大化的位置不会变化：

$$
\boxed{
\theta^*
=
\arg\max_\theta
\sum_{i=1}^{N}
\log q_\theta(x_i)
}
$$

这就是 **log-likelihood**。

如果除以 $N$：

$$
\theta^*
=
\arg\max_\theta
\frac 1 N
\sum_{i=1}^{N}
\log q_\theta(x_i)
$$

再乘一个负号：

$$
\boxed{
\theta^*
=
\arg\min_\theta
-\frac 1 N
\sum_{i=1}^{N}
\log q_\theta(x_i)
}
$$

你有没有觉得这个形式已经非常眼熟了？

---

# 关键一步：这其实就是期望

考虑真实数据分布：

$$
p_{\text{data}}(x)
$$

如果我们真的知道它，那么：

$$
\mathbb E_{x\sim p_{\text{data}}}
[-\log q_\theta(x)]
$$

就是：

$$
-\sum_x
p_{\text{data}}(x)
\log q_\theta(x)
$$

这不就是：

$$
\boxed{
H(p_{\text{data}},q_\theta)
}
$$

吗？

所以理论上：

$$
\boxed{
\text{MLE}
\iff
\min_\theta
H(p_{\text{data}},q_\theta)
}
$$

---

# 但问题来了：我们不知道 $p_{\text{data}}$

这才是机器学习最有意思的地方。

我们并不知道：

$$
p_{\text{data}}
$$

否则也就不用训练模型了。

我们只有一堆样本：

$$
x _1,\dots,x_N
$$

所以我们用样本平均近似期望：

$$
\mathbb E_{x\sim p_{\text{data}}}
[-\log q_\theta(x)]
\approx
-\frac 1 N\sum_i\log q_\theta(x_i)
$$

这就是大数定律带来的经验近似。

于是：

$$
\boxed{
-\frac 1 N\sum_i\log q_\theta(x_i)
}
$$

既可以解释为：

> negative log-likelihood

也可以解释为：

> empirical cross entropy

它们其实是同一个东西。

---

# 现在把 KL 接进来

你已经知道：

$$
H(p_{\text{data}},q_\theta)
=
H(p_{\text{data}})
+
D_{\mathrm{KL}}
(p_{\text{data}}\|q_\theta)
$$

其中：

$$
H(p_{\text{data}})
$$

不依赖 $\theta$。

所以：

$$
\arg\min_\theta
H(p_{\text{data}},q_\theta)
$$

等价于：

$$
\boxed{
\arg\min_\theta
D_{\mathrm{KL}}
(p_{\text{data}}\|q_\theta)
}
$$

于是终于得到：

$$
\boxed{
\text{Maximum Likelihood}
\iff
\text{Minimum Cross Entropy}
\iff
\text{Minimum Forward KL}
}
$$

也就是：

$$
\boxed{
\max_\theta
\sum_i\log q_\theta(x_i)
\iff
\min_\theta
H(p_{\text{data}},q_\theta)
\iff
\min_\theta
D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta)
}
$$

这就是完整闭环。

---

# 但你可能还会问：为什么“最大化样本概率”会等价于“逼近真实分布”？

这里其实有个非常深的直觉。

假设真实世界：

$$
p_{\text{data}}=
[0.8,0.2]
$$

你不断从这个世界采样。

采 $10000$ 次以后，大约会看到：

$$
8000\text{ 次 A}
$$

$$
2000\text{ 次 B}
$$

MLE 的目标：

$$
\prod_i q_\theta(x_i)
$$

就近似变成：

$$
q_\theta(A)^{8000}
q_\theta(B)^{2000}
$$

取 log：

$$
8000\log q_\theta(A)
+
2000\log q_\theta(B)
$$

除以 $10000$：

$$
0.8\log q_\theta(A)
+
0.2\log q_\theta(B)
$$

前面的：

$$
0.8,\ 0.2
$$

不就是：

$$
p_{\text{data}}(A),\ p_{\text{data}}(B)
$$

吗？

所以大量样本会把真实分布“显露”出来。

MLE 看起来只是在说：

> 给训练样本高概率。

但当数据足够多时，它实际上是在说：

> **按照真实数据出现的频率，给这些事件分配对应的概率。**

所以最后自然逼近：

$$
q_\theta\approx p_{\text{data}}
$$

---

# 分类任务里，这件事更直观

假设数据：

$$
(x_i,y_i)
$$

模型：

$$
q_\theta(y\mid x)
$$

MLE 是：

$$
\max_\theta
\prod_i
q_\theta(y_i\mid x_i)
$$

取 log：

$$
\max_\theta
\sum_i
\log q_\theta(y_i\mid x_i)
$$

等价于：

$$
\boxed{
\min_\theta
-\sum_i
\log q_\theta(y_i\mid x_i)
}
$$

这就是我们上一页看到的：

$$
\boxed{
-\log q(y_i\mid x_i)
}
$$

也就是 Cross Entropy Loss。

所以神经网络分类训练根本不是“碰巧用了 cross entropy”。

它实际上是在做：

$$
\boxed{
\text{Maximum Likelihood Estimation}
}
$$

---

# LLM 也是完全一样

给定上下文：

$$
x_{<t}
$$

真实下一个 token：

$$
x_t
$$

LLM 输出：

$$
q_\theta(x_t\mid x_{<t})
$$

整个序列概率：

$$
q_\theta(x_ 1,\dots,x_T)
=
\prod_{t=1}^{T}
q_\theta(x_t\mid x_{<t})
$$

MLE 就是最大化：

$$
\prod_t
q_\theta(x_t\mid x_{<t})
$$

取 log：

$$
\sum_t
\log q_\theta(x_t\mid x_{<t})
$$

取负：

$$
\boxed{
-\sum_t
\log q_\theta(x_t\mid x_{<t})
}
$$

这就是 LLM 的 next-token cross-entropy loss。

所以 GPT 预训练可以同时从三种角度理解：

$$
\boxed{
\begin{aligned}
&\text{概率角度：}&
&\text{最大化真实 token 的 likelihood}\\
&\text{信息论角度：}&
&\text{最小化 cross entropy}\\
&\text{分布角度：}&
&\text{最小化 }D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta)
\end{aligned}
}
$$

它们不是三个训练目标。

**它们是同一个目标的三种语言。**

---

# 还有一个非常值得注意的地方

这里最小化的是：

$$
\boxed{
D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta)
}
$$

而不是：

$$
D_{\mathrm{KL}}(q_\theta\|p_{\text{data}})
$$

这叫 **forward KL**。

方向其实会影响模型行为。

因为：

$$
D_{\mathrm{KL}}(p\|q)
=
\sum_xp(x)\log\frac{p(x)}{q(x)}
$$

如果真实分布某个区域：

$$
p(x)>0
$$

而模型：

$$
q(x)\approx 0
$$

KL 会非常大。

所以 forward KL 特别讨厌：

> **真实世界里存在的模式，被模型漏掉。**

这会推动模型去覆盖真实数据的各种 mode。

因此它常被描述为偏 **mode-covering**。

相反：

$$
D_{\mathrm{KL}}(q\|p)
$$

更惩罚模型把概率放到真实分布概率很低的地方，常表现得更 **mode-seeking**。

这也是为什么 KL 的“方向”不是小细节。

---

## 最后用一条链收住

从你最早问的“为什么 cross entropy 是这样定义的”，现在已经可以一路推到 LLM：

$$
\text{概率}
$$

$$
\downarrow
$$

$$
\text{surprisal}
=
-\log p(x)
$$

$$
\downarrow
$$

$$
H(p)=E_p[-\log p]
$$

$$
\downarrow
$$

$$
H(p,q)=E_p[-\log q]
$$

$$
\downarrow
$$

$$
D_{\mathrm{KL}}(p\|q)
=
H(p,q)-H(p)
$$

$$
\downarrow
$$

$$
\min D_{\mathrm{KL}}
\iff
\min H(p,q)
$$

$$
\downarrow
$$

$$
\min H
\iff
\max \log\text{-likelihood}
$$

$$
\downarrow
$$

$$
\boxed{
\text{LLM next-token Cross Entropy Training}
}
$$

最核心的一句话就是：

$$
\boxed{
\text{MLE 看起来是在“让训练数据概率更大”，
本质上是在用样本逼近真实分布，并让模型分布靠近它。}
}
$$

这条线一旦通了，**NLL、Cross Entropy、MLE、KL Divergence 其实就不是四个知识点了，而是同一个东西从四个角度看的结果。**
