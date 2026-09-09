---
title: KL 散度
tags:
  - math
  - probability
  - kl-divergence
created: 2026-09-08
updated: 2026-09-09
---

KL Divergence 最自然的推导方式，就是从你刚刚理解的 **Cross Entropy** 往下走。

先把三个量放在一起：

$$
H(p)=-\sum_x p(x)\log p(x)
$$

$$
H(p,q)=-\sum_x p(x)\log q(x)
$$

我们问：

> **如果真实世界是 $p$，但我错误地用 $q$ 来描述它，我比“知道真实分布 $p$”多付出了多少代价？**

答案就是：

$$
\boxed{
H(p,q)-H(p)
}
$$

把它展开：

$$
H(p,q)-H(p)
=
-\sum_xp(x)\log q(x)
+
\sum_xp(x)\log p(x)
$$

合并：

$$
=
\sum_xp(x)\left[
\log p(x)-\log q(x)
\right]
$$

利用：

$$
\log a-\log b=\log\frac ab
$$

得到：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
\sum_xp(x)\log\frac{p(x)}{q(x)}
}
$$

这就是 KL Divergence。

---

# 1. 所以 KL 到底是什么？

最简单的心智模型是：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
\text{用错误模型 }q\text{ 描述真实世界 }p
\text{ 所付出的额外代价}
}
$$

也就是：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
H(p,q)-H(p)
}
$$

其中：

- $H(p)$：如果你知道真实世界 $p$，最理想的平均信息代价
- $H(p,q)$：真实世界是 $p$，但你按 $q$ 去预测/编码时的平均代价
- 差值：因为模型错了而浪费掉的部分

因此：

$$
\boxed{
H(p,q)=H(p)+D_{\mathrm{KL}}(p\|q)
}
$$

这个关系非常重要。

---

# 2. 为什么 KL 里面是 $\log \frac{p}{q}$？

我们可以从单个事件看。

假设某事件 $x$。

如果你知道真实概率 $p(x)$，它的信息代价是：

$$
-\log p(x)
$$

但你错误地认为它概率是 $q(x)$，于是你付出的代价是：

$$
-\log q(x)
$$

那么对这个事件，你额外浪费：

$$
-\log q(x)-[-\log p(x)]
$$

也就是：

$$
\log p(x)-\log q(x)
$$

即：

$$
\boxed{
\log\frac{p(x)}{q(x)}
}
$$

所以这个 ratio：

$$
\frac{p(x)}{q(x)}
$$

其实在问：

> 模型 $q$ 相对于真实分布 $p$，把这个事件估错了多少？

然后因为事件真正是按照 $p(x)$ 出现的，我们对所有事件取真实概率**加权平均**：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
E_{x\sim p}
\left[
\log\frac{p(x)}{q(x)}
\right]
}
$$

这是我觉得最值得记住的形式：

$$
\boxed{
KL
=
\mathbb E_p
\left[
\log\frac{p}{q}
\right]
}
$$

---

# 3. 举个很具体的例子

假设真实世界：

$$
p=[0.9,0.1]
$$

但是你的模型认为：

$$
q=[0.5,0.5]
$$

用 $\log_2$。

首先真实 entropy：

$$
H(p)
=
-0.9\log_2 0.9
-0.1\log_2 0.1
$$

约等于：

$$
H(p)\approx 0.469
$$

而 cross entropy：

$$
H(p,q)
=
-0.9\log_2 0.5
-0.1\log_2 0.5
$$

因为：

$$
-\log_2 0.5=1
$$

所以：

$$
H(p,q)=1
$$

于是：

$$
D_{\mathrm{KL}}(p\|q)
=
1-0.469
$$

$$
\boxed{
D_{\mathrm{KL}}\approx 0.531\text{ bit}
}
$$

意思就是：

> 因为你错误地把真实的 $90/10$ 世界理解成了 $50/50$，所以平均每次观测会多浪费约 $0.531$ bit。

---

# 4. 为什么 KL 一定 $\ge 0$？

这个性质很核心：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)\ge 0
}
$$

而且只有：

$$
p=q
$$

时等于 0。

直觉上很好理解：

> 如果 $p$ 就是真实分布，那么没有哪个错误的 $q$ 能在平均意义上，比直接使用 $p$ 描述 $p$ 自己还更省。

也就是：

$$
H(p,q)\ge H(p)
$$

因此：

$$
H(p,q)-H(p)\ge 0
$$

所以：

$$
D_{\mathrm{KL}}(p\|q)\ge 0
$$

---

## 数学上也可以证明

从：

$$
D_{\mathrm{KL}}(p\|q)
=
-\sum_xp(x)\log\frac{q(x)}{p(x)}
$$

因为 $\log$ 是 concave function，根据 Jensen：

$$
\sum_xp(x)\log\frac{q(x)}{p(x)}
\le
\log
\left(
\sum_xp(x)\frac{q(x)}{p(x)}
\right)
$$

里面：

$$
\sum_xp(x)\frac{q(x)}{p(x)}
=
\sum_xq(x)=1
$$

所以：

$$
\sum_xp(x)\log\frac{q(x)}{p(x)}
\le\log 1=0
$$

加负号：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)\ge 0
}
$$

---

# 5. 为什么 KL 不对称？

这是非常容易误解的一点。

一般来说：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
\neq
D_{\mathrm{KL}}(q\|p)
}
$$

所以 KL 不是数学意义上的距离。

因为两者问的问题不同。

### $D_{\mathrm{KL}}(p\|q)$

意思是：

> 数据实际来自 $p$，但我用 $q$ 描述它，损失多少？

权重是：

$$
p(x)
$$

---

### $D_{\mathrm{KL}}(q\|p)$

意思变成：

> 数据实际来自 $q$，但我用 $p$ 描述它，损失多少？

权重变成：

$$
q(x)
$$

这是两个不同问题。

---

# 6. 一个很典型的“不对称”例子

假设：

$$
p=[0.99,0.01]
$$

$$
q=[0.5,0.5]
$$

对于：

$$
D_{\mathrm{KL}}(p\|q)
$$

真实世界几乎总是第一个事件，因此第二个事件权重很低。

但对于：

$$
D_{\mathrm{KL}}(q\|p)
$$

$q$ 认为第二个事件有 50% 概率，可是 $p$ 只给了它 1%。

于是项：

$$
0.5\log\frac{0.5}{0.01}
$$

会很大。

所以方向不同，惩罚完全不同。

---

# 7. 极端情况特别能说明 KL 的含义

如果：

$$
p(x)>0
$$

但是：

$$
q(x)=0
$$

那么：

$$
\log\frac{p(x)}{q(x)}
=
\log\frac{p(x)}0
\to\infty
$$

因此：

$$
D_{\mathrm{KL}}(p\|q)=\infty
$$

为什么这么狠？

因为：

> 一个真实有可能发生的事件，你的模型居然宣称“绝对不可能”。

从编码角度，$q(x)=0$ 意味着你根本没有为这个事件准备编码。

所以一旦它真的发生，代价无限大。

这其实也解释了为什么概率模型里 **过度自信地给 $0$ 概率** 是非常危险的。

---

# 8. KL 和 Cross Entropy 在机器学习里的关系

这是最实用的一点。

训练时我们常常最小化：

$$
H(p,q)
$$

但是：

$$
H(p,q)
=
H(p)+D_{\mathrm{KL}}(p\|q)
$$

对于给定数据集来说，真实分布 $p$ 是固定的，所以：

$$
H(p)
$$

跟模型参数无关。

因此：

$$
\boxed{
\min_q H(p,q)
\iff
\min_q D_{\mathrm{KL}}(p\|q)
}
$$

也就是说：

> **训练 Cross Entropy，本质上就是在让模型分布 $q$ 靠近真实数据分布 $p$。**

这个结论非常重要。

---

# 9. 为什么普通分类里你看不到 KL？

假设是 one-hot 标签：

$$
p=[0,1,0]
$$

这种情况下：

$$
H(p)=0
$$

为什么？

因为真实标签完全确定，没有不确定性：

$$
-1\log 1=0
$$

因此：

$$
H(p,q)
=
H(p)+D_{\mathrm{KL}}(p\|q)
$$

变成：

$$
H(p,q)
=
D_{\mathrm{KL}}(p\|q)
$$

而 cross entropy 又是：

$$
-\log q(y)
$$

所以在 one-hot 分类情况下：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
H(p,q)
=
-\log q(y)
}
$$

这也是为什么它们在分类里看起来几乎揉成了一个东西。

---

# 10. 再给你一个非常重要的“概率比”视角

KL 还可以理解成：

$$
D_{\mathrm{KL}}(p\|q)
=
E_p
\left[
\log\frac{p(x)}{q(x)}
\right]
$$

其中：

$$
\frac{p(x)}{q(x)}
$$

叫 likelihood ratio / density ratio。

如果：

$$
p(x)>q(x)
$$

则：

$$
\log\frac{p(x)}{q(x)}>0
$$

说明：

> 这个事件真实世界比模型认为的更常见，模型低估了它。

如果：

$$
p(x)<q(x)
$$

则这一项是负的：

> 模型高估了这个事件。

注意：**单个事件的 contribution 可以是负数。**

但对真实分布 $p$ 求平均之后：

$$
D_{\mathrm{KL}}(p\|q)\ge 0
$$

这是一个很微妙但很重要的点。

---

# 11. 一条线把 Entropy / Cross Entropy / KL 全串起来

现在可以这样记：

### 第一步：单个事件有多惊讶

$$
\boxed{
I_p(x)=-\log p(x)
}
$$

### 第二步：世界自己平均有多不可预测

$$
\boxed{
H(p)=E_p[-\log p(x)]
}
$$

### 第三步：如果我错误地用 $q$ 理解这个世界

$$
\boxed{
H(p,q)=E_p[-\log q(x)]
}
$$

### 第四步：我因为搞错分布额外损失了多少

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
H(p,q)-H(p)
}
$$

因此：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)
=
E_p
\left[
\log\frac{p(x)}{q(x)}
\right]
}
$$

所以如果只让我用一句话解释 KL：

> **KL Divergence 衡量：当真实世界服从 $p$，而你却用 $q$ 来理解或编码它时，相比使用正确的 $p$，平均多付出了多少信息代价。**

你现在其实已经把这几个概念的底层逻辑串起来了：

$$
\boxed{
\text{surprisal}
\rightarrow
\text{entropy}
\rightarrow
\text{cross entropy}
\rightarrow
\text{KL divergence}
}
$$

再往下一步就是一个特别有意思的连接：**为什么 Maximum Likelihood Estimation（MLE）等价于最小化 $D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta)$**。这一步一通，Cross Entropy 为什么会成为神经网络和 LLM 的核心训练目标就彻底闭环了。
