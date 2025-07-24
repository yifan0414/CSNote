---
created: 2025-03-29 21:35
tags:
---
最早的神经网络（如感知机和多层感知机，MLP）确实是使用 **Sigmoid** 或 **Tanh** 作为激活函数，而不是 **ReLU**。主要有以下几个历史和技术上的原因：

---

**1. 受生物神经元模型的启发**

最早的人工神经网络是受到生物神经元的启发设计的。生物神经元的激活行为类似于 “**非线性激活**”，即：

• 当输入电信号较弱时，神经元不激活（输出接近 0）。

• 当输入电信号较强时，神经元被激活（输出接近 1）。
  

Sigmoid 函数的输出范围是 **(0,1)**，非常符合这种生物学上的 “全有全无” 现象，因此最初的神经网络选择了 Sigmoid 作为激活函数。

  

**同时，Sigmoid 还能被看作概率的输出**，因为它将输入映射到 0 到 1 之间，适合作为分类任务的输出层。

---

**2. 早期对非线性函数的理解有限**

  

在 20 世纪 80-90 年代，**神经网络的数学理论还不成熟**，研究人员主要使用的是：

• Sigmoid

• Tanh（双曲正切函数）

  

当时的主要关注点是 **如何让神经网络具备非线性能力**，而 **ReLU（Rectified Linear Unit）** 这种简单的线性-非线性组合在当时并未被深入研究。

  

**Tanh 也被广泛使用，因为它的值域是 (-1,1)，比 Sigmoid 具有更好的梯度特性**，但梯度仍然可能消失。

---

**3. 计算机硬件和优化技术的限制**

  

在早期的计算机硬件上：

• 计算 **指数运算（e^x）** 需要较高的计算量。

• 但由于 Sigmoid 和 Tanh 的计算仍然是 **连续可导的**，可以方便地用于梯度下降优化。

  

而 ReLU 具有**非光滑点**（即 $x=0$ 处不可导），在早期研究中，人们普遍认为 **不可导的激活函数可能不利于优化**，所以 ReLU 没有被广泛采用。

---

**4. ReLU 在 2010 年后才流行起来**

  

ReLU 其实很早就被提出了，但直到 **2010 年 Hinton 等人的论文《Rectified Linear Units Improve Restricted Boltzmann Machines》** 才让 ReLU 被广泛应用于深度学习。

  

研究发现：

• **ReLU 不受梯度消失问题的影响**（在 $x > 0$ 时梯度恒为 1）。

• **计算简单高效**，相比 Sigmoid 和 Tanh，ReLU 只需要计算 $\max(0, x)$，大幅减少计算量。

• **能更好地支持深度网络训练**，帮助解决梯度消失问题。

  

之后，ReLU 迅速成为 **深度学习的默认激活函数**，尤其是在 CNN（卷积神经网络）中广泛使用。

---

**总结**

|**激活函数**|**早期使用原因**|**问题**|**现代使用情况**|
|---|---|---|---|
|**Sigmoid**|生物学启发，概率解释，易优化|梯度消失|主要用于输出层|
|**Tanh**|范围 (-1,1)，梯度稍好|仍然有梯度消失|较少使用|
|**ReLU**|计算简单，梯度不消失|$x=0$ 处不可导，可能出现“神经元死亡”|现代深度学习的默认选择|

最早人们选择 **Sigmoid 是因为直观符合生物神经元、容易优化、可以输出概率**，但随着研究的进展，发现 ReLU 更适合深度神经网络，因此逐渐成为主流。


reasoning performance. Finally, we provide insights into future research directions from the following two perspectives: (i) from visual-language reasoning to omnimodal reasoning and (ii) from multimodal reasoning to multimodal agents. This survey aims to provide a structured overview that will inspire further advancements in multimodal reasoning research.


[reasoning performance. Finally, we provide insights into future research directions from the following two perspectives: (i) from visual-language reasoning to omnimodal reasoning and (ii) from multimodal reasoning to multimodal agents. This survey aims to provide a structured overview that will inspire further advancements in multimodal reasoning research.$$\lim_{1} a^2 = 10$$

[As AI systems increasingly interact with dynamic, uncertain, and multimodal settings, the ability to perform right reasoning under various environments becomes essential for achieving robust and adaptive intelligence
](marginnote4app://note/0019BD7A-2B13-4611-862F-F5199C125C57)
](marginnote4app://note/676217EF-0EBB-459F-9F17-D948F35AA9EA)
$$
\lim_{1} a^2 = 10
$$
[Research in multimodal reasoning has progressed rapidly. Early efforts relied on perception-driven, modular pipelines, while recent advances leverage large language models to unify multimodal understanding and reasoning (Huang et al., 2023b; Driess et al., 2023). Instruction tuning (Liu et al., 2023a) and reinforcement learning (DeepSeek-AI et al., 2025) further enhance models’ reasoning performance, bringing them closer to human-like deliberative behaviour. Despite this rapid progress, multimodal reasoning is still a core bottleneck of large multimodal models, where they show limiting generalization, depth of reasoning, and agent-like behavior (Yue et al., 2024; Zhang et al., 2024f; Liu et al., 2024f).

](marginnote4app://note/491ADDCA-637C-4BAE-840B-40D0FA4F19F4)


[∃ xa∈ Vcandidate∧ i ∈ (0, N], p(xa|x<s)i− p(xh|x<s)i≥ threshold,
](marginnote4app://note/E331F24D-0F5B-44F1-B616-E578AECC03B9)