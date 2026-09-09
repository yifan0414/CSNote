---
created: 2026-09-09
tags:
  - 深度学习
  - 信息论
  - 数学
  - 生成模型
sources:
---

# Forward KL 与 Reverse KL：交换 p 和 q 到底改变了什么

> [!abstract] 这篇笔记解决什么问题
> KL 散度是不对称的。把 $p$ 和 $q$ 的位置交换一下，就得到两个不同的优化目标，训练出来的模型行为也截然不同：一个倾向于**覆盖真实分布的所有模式**，另一个倾向于**抓住一个模式然后紧紧抱住**。
>
> 全文只围绕一个问题：**为什么仅仅交换两个符号，就会产生这么不同的学习行为？**
>
> 阅读路径：先记住唯一的区别（在谁的分布上取平均）→ 看代数上谁被优化 → 用双峰例子看行为差异 → 用支撑集给出严格解释 → 最后看它们分别出现在哪些场景。

> [!note] 符号约定
> - $p$ 是**目标分布**（真实数据分布 $p_{\text{data}}$，或需要近似的后验 $p(z\mid x)$）；$q$（也写作 $q_\theta$、$q_\phi$）是**我们要学的近似分布**。本文始终用 $q$ 去逼近 $p$。
> - $D_{\mathrm{KL}}(p\|q)$ 读作“从 $p$ 到 $q$”，其中 $p$ 是参考分布。
> - 全文 $\log$ 为自然对数。KL 恒非负、恒不对称，且 $D_{\mathrm{KL}}(p\|q)=0$ 当且仅当 $p=q$。

## 学习路线

1. [[#1. 唯一的区别：在谁的分布上取平均]]——一句话抓住全部差异。
2. [[#2. 代数视角：谁在被优化，谁只是常数]]——把两种 KL 拆成可比较的项。
3. [[#3. 行为差异：双峰分布上的经典例子]]——mode covering 与 mode seeking 从哪来。
4. [[#4. 严格版本：支撑集与零概率]]——无穷代价的数学来源。
5. [[#5. 心智模型：谁拥有否决权]]——一个比 mode-covering / mode-seeking 更好记的说法。
6. [[#6. 它们分别出现在哪里]]——MLE、变分推断、生成模型、语言模型。
7. [[#7. 速查表与自测]]——表格、两句话和检查理解的问题。

---

## 1. 唯一的区别：在谁的分布上取平均

两种 KL 的定义分别是：

$$
D_{\mathrm{KL}}(p\|q)=\sum_x p(x)\log\frac{p(x)}{q(x)}
$$

$$
D_{\mathrm{KL}}(q\|p)=\sum_x q(x)\log\frac{q(x)}{p(x)}
$$

把求和改写成期望，差别立刻暴露出来：

$$
\boxed{
D_{\mathrm{KL}}(p\|q)=\mathbb E_{x\sim p}\!\left[\log\frac{p(x)}{q(x)}\right]
}
\qquad\text{(Forward KL)}
$$

$$
\boxed{
D_{\mathrm{KL}}(q\|p)=\mathbb E_{x\sim q}\!\left[\log\frac{q(x)}{p(x)}\right]
}
\qquad\text{(Reverse KL)}
$$

**唯一的区别就是下标：一个在 $p$ 上取平均，一个在 $q$ 上取平均。**

| | Forward KL | Reverse KL |
| --- | --- | --- |
| 定义 | $D_{\mathrm{KL}}(p\|q)$ | $D_{\mathrm{KL}}(q\|p)$ |
| 在谁的分布上取平均 | $x\sim p$ | $x\sim q$ |
| 谁负责“出题” | 真实世界 $p$ | 模型自己 $q$ |
| 直觉 | 去 $p$ 常出现的地方，检查 $q$ 表现如何 | 去 $q$ 常出现的地方，检查 $p$ 认不认可 |

> [!note] 命名习惯的提醒
> forward / reverse 的叫法在不同领域偶尔有不同习惯。本文按机器学习里最常见的约定：**用 $q$ 拟合 $p$ 时，$D_{\mathrm{KL}}(p\|q)$ 称为 Forward KL**。
>
> 遇到别的文献时不要只信名字，直接看公式里的期望下标即可——那才是唯一可靠的信息。

---

## 2. 代数视角：谁在被优化，谁只是常数

上面两个期望还可以拆开，看清“哪部分依赖待优化的 $q$”。这一步是后面所有行为差异的代数来源。

### 2.1 Forward KL

$$
\begin{aligned}
D_{\mathrm{KL}}(p\|q)
&=\sum_x p(x)\log p(x)-\sum_x p(x)\log q(x)\\[2pt]
&=\underbrace{-H(p)}_{\text{与 }q\text{ 无关}}-\mathbb E_{x\sim p}[\log q(x)].
\end{aligned}
$$

因为 $H(p)$ 不依赖 $q$，所以：

$$
\boxed{
\arg\min_q D_{\mathrm{KL}}(p\|q)
=\arg\max_q \mathbb E_{x\sim p}[\log q(x)]
}
$$

$\mathbb E_{x\sim p}[-\log q(x)]$ 就是交叉熵 $H(p,q)$。因此 **最小化 Forward KL = 最小化交叉熵 = 最大似然**：真实数据不断拿样本给模型看，要求 $q$ 对这些真实样本都给出较高概率。

### 2.2 Reverse KL

$$
\begin{aligned}
D_{\mathrm{KL}}(q\|p)
&=\sum_x q(x)\log q(x)-\sum_x q(x)\log p(x)\\[2pt]
&=-H(q)-\mathbb E_{x\sim q}[\log p(x)].
\end{aligned}
$$

所以：

$$
\boxed{
\arg\min_q D_{\mathrm{KL}}(q\|p)
=\arg\max_q\Big(\;H(q)+\mathbb E_{x\sim q}[\log p(x)]\;\Big)
}
$$

### 2.3 关键对比

| | Forward KL | Reverse KL |
| --- | --- | --- |
| 展开 | $-H(p)-\mathbb E_p[\log q]$ | $-H(q)-\mathbb E_q[\log p]$ |
| 与 $q$ 有关的项 | $\mathbb E_p[\log q]$ | $\mathbb E_q[\log p]+H(q)$ |
| 等价于 | 最大化真实数据上的对数似然（MLE / 交叉熵） | 最大化「熵 + 质量落在 $p$ 高概率处」 |

> [!important] 一个容易被忽略的差别
> **Forward KL 里完全没有 $H(q)$ 这一项**，也就是说 $q$ 铺得宽、把概率摊到很多地方，并不直接受罚。
>
> **Reverse KL 里 $H(q)$ 出现在目标中**，它与 $\mathbb E_q[\log p]$ 相互拉扯：熵项想让 $q$ 分散，而 $\log p$ 这一项对「把概率放在 $p\approx 0$ 的地方」惩罚极重（$\log p\to-\infty$）。两者竞争的结果，通常就是“挑一个模式、紧紧抱住”。
>
> 这个代数差别，是下一节所有图形直觉的根源。

---

## 3. 行为差异：双峰分布上的经典例子

### 3.1 设定

假设真实分布是双峰的：

$$
p(x)=0.5\,p_A(x)+0.5\,p_B(x)
$$

也就是真实数据一半来自模式 A，一半来自模式 B：

![[_assets/images/kl-01-p-bimodal.svg|720]]

（左峰是模式 A，右峰是模式 B，中间谷底处 $p(x)\approx 0$。纵轴为示意：每条曲线都按自身峰值归一化，重点看形状和位置，不是高度。）

现在让模型 $q$ 偷懒，只学了左边，完全漏掉模式 B。接下来分别看两个目标会怎么评价这件事。

### 3.2 Forward KL：漏掉一个模式 → 无穷代价

Forward KL 的代价是 $\mathbb E_{x\sim p}[-\log q(x)]$，而样本是从 $p$ 里采的：

![[_assets/images/kl-02-reverse-mode-seeking.svg|720]]

- **50% 的概率采到模式 A**：$q(x)$ 较大，代价很小。
- **另外 50% 会采到模式 B**：但模型在 B 那里 $q(x)\approx 0$，于是

$$
-\log q(x)\to\infty.
$$

每次采到 B，损失都会爆掉。所以 Forward KL 会不断向模型喊：

> **B 这里是真实存在的，你不能假装没看见。**

这就是 **mode covering**：

$$
\boxed{\text{宁可覆盖宽一点，也不要漏掉真实数据的模式。}}
$$

### 3.3 为什么 Forward KL 不介意“多覆盖一点”

假设 $q$ 受模型能力限制，只能是一个单峰 Gaussian，无法同时画出两个峰。Forward KL 往往倾向于搞一个较宽的 Gaussian，把两个模式都盖住：

![[_assets/images/kl-03-forward-mode-covering.svg|720]]

这样做的代价是：两个峰之间的谷底本来 $p(x)\approx 0$，而宽 Gaussian 在那里必然 $q(x)>0$。

但 Forward KL 并不会在这里狠狠处罚它，原因是期望在 $p$ 上取：

$$
D_{\mathrm{KL}}(p\|q)=\mathbb E_{x\sim p}[\cdots]
$$

**只有 $p(x)$ 大的地方才会被频繁采样**，谷底几乎采不到，所以对总损失的贡献很小。

当然，概率必须归一化，谷底多放一点，别处就少一点，所以仍然存在**间接**代价。但比起“完全漏掉一个真实模式”，这个代价通常温和得多。于是：

$$
\boxed{\text{Forward KL：宁可多覆盖，不要漏。}}
$$

### 3.4 Reverse KL：漏掉一个模式几乎无感

Reverse KL 的代价是 $\mathbb E_{x\sim q}[\log(q(x)/p(x))]$，样本从 $q$ 里采。还是那个只学了左边的 $q$：

- $q$ 几乎只会采到左边，右边永远采不到；
- 右边虽然 $p(x)\gg 0$，但 $q(x)\approx 0$，模型根本不去那里；
- 那个区域对期望的贡献几乎为零。

所以：

$$
\boxed{\text{Reverse KL 不会因为“真实世界那里有东西而我没去”而直接惩罚自己。}}
$$

### 3.5 Reverse KL 只怕跑出真实分布

Reverse KL 真正害怕的是另一件事：**模型认为某处可能出现，但真实世界认为那里几乎不可能。**

如果 $q(x)>0$ 而 $p(x)\approx 0$，那么

$$
\frac{q(x)}{p(x)}\ \text{巨大},\qquad \log\frac{q(x)}{p(x)}\gg 0,
$$

KL 迅速变大。极端情形 $p(x)=0,\ q(x)>0$ 时：

$$
\boxed{D_{\mathrm{KL}}(q\|p)=\infty.}
$$

用一句话概括 Reverse KL 的态度：

> **你可以不覆盖所有真实可能性，但千万别幻想一个真实世界根本不存在的东西。**

### 3.6 只能用一个 Gaussian 时的取舍

这是最能体现 mode-seeking 的地方。真实分布仍是双峰，模型 $q$ 被限制为**单个 Gaussian**，于是只有两种选择：

![[_assets/images/kl-04-two-options.svg|880]]

**方案 A：把两个峰都盖住**

覆盖了 A 和 B，但中间谷底必然 $q(x)>0$。Reverse KL 采到这些中间样本，去查 $p(x)$，发现真实世界几乎不产生它们，于是 $\log(q/p)$ 非常大。**方案 A 在 Reverse KL 下代价很高。**

**方案 B：只抱住一个峰**

它完全漏掉 B，但 Reverse KL 的问题是：

> “我从 $q$ 采出来的东西，真实分布支持吗？”

答案是“支持”——A 本来就是 $p$ 的高概率区，所以损失可以很低。至于 B，因为 $q(B)\approx 0$，模型根本不采，**Reverse KL 基本不在乎**。

于是它自然倾向：

$$
\boxed{\text{挑一个模式，紧紧抱住}}\quad\Longrightarrow\quad\text{mode seeking.}
$$

### 3.7 小结

| | Forward KL | Reverse KL |
| --- | --- | --- |
| 单峰 $q$ 面对双峰 $p$ | 选宽 Gaussian，覆盖两个峰 | 选窄 Gaussian，抱住一个峰 |
| 原因 | 漏掉模式代价无穷大 | 跑出 $p$ 的代价无穷大 |
| 名称 | mode covering | mode seeking |

---

## 4. 严格版本：支撑集与零概率

上一节的“无穷代价”，在数学上就是支撑集（support）的条件。

### 4.1 Forward KL

若存在 $x$ 使 $p(x)>0$ 而 $q(x)=0$，则

$$
D_{\mathrm{KL}}(p\|q)=\infty.
$$

所以要让 Forward KL 有限，必须：

$$
\boxed{\mathrm{supp}(p)\subseteq\mathrm{supp}(q)}
$$

即 **$q$ 不能漏掉 $p$ 的支撑集**。

### 4.2 Reverse KL

若存在 $x$ 使 $q(x)>0$ 而 $p(x)=0$，则

$$
D_{\mathrm{KL}}(q\|p)=\infty.
$$

所以要让 Reverse KL 有限，必须：

$$
\boxed{\mathrm{supp}(q)\subseteq\mathrm{supp}(p)}
$$

即 **$q$ 不能跑出 $p$ 的支撑集**。

> [!note] 更严格的说法
> 支撑集包含关系是直觉版本。对一般分布，$D_{\mathrm{KL}}(p\|q)<\infty$ 的准确条件是**绝对连续** $p\ll q$（即 $q$ 为零的地方 $p$ 也必须为零）。对离散分布或密度存在的情形，两者基本一致。

这两个条件几乎就是 mode-covering / mode-seeking 最干净的数学解释。

---

## 5. 心智模型：谁拥有否决权

把两个期望的“下标”翻译成权力的语言，会很好记。

**Forward KL：$\mathbb E_p[\cdots]$——真实数据拥有否决权。**

> 只要我 $p$ 会产生这个东西，你 $q$ 就最好也覆盖。

因此 $p(x)>0,\ q(x)=0$ 非常危险。

**Reverse KL：$\mathbb E_q[\cdots]$——模型自己拥有注意力分配权。**

> 我 $q$ 不去的地方，我基本不用管；但我一旦去了，就必须接受 $p$ 的审查。

因此 $q(x)>0,\ p(x)\approx 0$ 非常危险。

$$
\boxed{
\begin{array}{ccc}
D_{\mathrm{KL}}(p\|q) & & D_{\mathrm{KL}}(q\|p)\\[6pt]
\text{Don't miss reality} & & \text{Don't invent reality}\\
\text{别漏掉真实世界} & & \text{别跑出真实世界}
\end{array}
}
$$

---

## 6. 它们分别出现在哪里

### 6.1 MLE 与交叉熵 → Forward KL

第 2 节已经说明：

$$
\text{MLE}\iff\min_q H(p_{\text{data}},q_\theta)\iff\min_q D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta).
$$

MLE 的训练方式就是“数据集每拿出一个真实样本，你就必须给它高概率”。训练集里出现猫、狗、鸟、汽车、飞机，模型就不能说“我只擅长猫，其他模式不管”：

- 狗样本来的时候，$-\log q(\text{dog})$ 直接打你；
- 鸟来的时候又打你；
- 飞机来的时候继续打你。

数据不断逼迫 $q_\theta$ 覆盖 $p_{\text{data}}$ 的各种模式，所以 **MLE 通常具有 mode-covering 倾向**。

相关推导见 [[交叉熵系统整理]] 与 [[从概率建模统一理解机器学习损失 MLE、NLL、Cross-Entropy、KL、MSE 与 MAE]]，KL 的完整整理见 [[KL 散度]]。

### 6.2 变分推断 → Reverse KL

假设要逼近一个算不出来的复杂后验 $p(z\mid x)$，就找一个简单分布 $q_\phi(z\mid x)$ 去近似。经典变分推断优化的正是 Reverse KL：

$$
D_{\mathrm{KL}}\big(q_\phi(z\mid x)\,\|\,p(z\mid x)\big).
$$

它和常见的 ELBO 是同一件事：

$$
\log p(x)=\underbrace{\mathbb E_q[\log p(x,z)-\log q(z)]}_{\text{ELBO}}+D_{\mathrm{KL}}(q\|p(\cdot\mid x)).
$$

因为 $\log p(x)$ 与 $q$ 无关，**最小化 Reverse KL 等价于最大化 ELBO**。

如果真实后验是双峰而 $q$ 只能是单峰 Gaussian，Reverse KL 往往宁愿选一个峰，也不愿意把很多概率放在真实后验的低概率谷底。这就是变分推断里经典的：

$$
\boxed{\text{under-dispersion / mode seeking——估计出的分布容易比真实分布更窄。}}
$$

### 6.3 生成模型与 mode collapse

一个生成模型 $q_\theta$ 想逼近真实图片分布 $p_{\text{data}}$（狗、猫、鸟、汽车、房子、各种姿态与背景）：

- 采用 Forward KL / MLE 风格的目标，会倾向于“尽量别漏掉数据中的各种情况”，coverage 更重要；
- 采用更偏 Reverse KL 性质的优化，则容易“找到一个非常高概率、非常安全的区域，然后集中在那里”。

这就是 mode collapse 常与 KL 方向一起讨论的原因。

> [!warning] 不要过度推广
> **不能简单说“用了 Reverse KL 就一定 mode collapse”。** 真实神经网络训练还受模型结构、优化器、采样方式和正则化等因素影响。
>
> mode-covering / mode-seeking 是一种非常有用的**倾向性解释**，不是绝对定理。

### 6.4 语言模型：训练与解码方向相反

假设真实文本分布 $p_{\text{text}}$ 中，句子开头 `I went to the bank to ...` 有很多合理延续：

$$
p:\quad
\begin{cases}
\text{deposit money} & 0.35\\
\text{withdraw cash} & 0.25\\
\text{open an account} & 0.15\\
\text{ask about a loan} & 0.10\\
\cdots
\end{cases}
$$

MLE / 交叉熵训练相当于 $D_{\mathrm{KL}}(p_{\text{data}}\|q_\theta)$：训练数据每次给出一个真实延续，模型要对**所有真实出现过的延续**都给出合理概率。这是 mode-covering 风格——不要只学一个最常见回答。

但生成阶段我们又常用 greedy decoding、低 temperature、beam search，这些操作会主动偏向概率最高的模式。于是出现一个有意思的错位：

$$
\boxed{
\text{训练目标可能偏向 mode-covering，但 decoding 可以非常 mode-seeking。}
}
$$

这也解释了一个现象：语言模型“内部知道很多可能答案”，但 greedy decoding 每次只吐出最典型的那个。

---

## 7. 速查表与自测

### 7.1 总表

| | Forward KL | Reverse KL |
| --- | --- | --- |
| 形式 | $D_{\mathrm{KL}}(p\|q)$ | $D_{\mathrm{KL}}(q\|p)$ |
| 在谁上取平均 | $x\sim p$ | $x\sim q$ |
| 谁负责出题 | 真实世界 | 模型自己 |
| 与 $q$ 有关的项 | $\mathbb E_p[\log q]$ | $\mathbb E_q[\log p]+H(q)$ |
| 最怕 | $p>0,\ q\approx 0$ | $q>0,\ p\approx 0$ |
| 支撑集条件 | $\mathrm{supp}(p)\subseteq\mathrm{supp}(q)$ | $\mathrm{supp}(q)\subseteq\mathrm{supp}(p)$ |
| 直觉 | 别漏掉真实数据 | 别生成不真实数据 |
| 常见倾向 | mode covering | mode seeking |
| 典型场景 | MLE / 交叉熵 | 变分推断 |

### 7.2 两句话

$$
\boxed{
D_{\mathrm{KL}}(p\|q):\quad
\text{“真实世界去过的地方，你最好都去。”}
}
$$

$$
\boxed{
D_{\mathrm{KL}}(q\|p):\quad
\text{“你自己要去的地方，最好都是真实世界认可的地方。”}
}
$$

这就是为什么仅仅交换 KL 里 $p,q$ 的位置，最后能产生完全不同的学习行为。

### 7.3 自测问题

1. 为什么 Forward KL 里看不到 $H(q)$，而 Reverse KL 里有？
2. 面对双峰 $p$ 和单峰 $q$，两个目标分别会选“宽而覆盖”还是“窄而集中”？各自动机是什么？
3. 如果 $q$ 在某个点 $x_0$ 取 $q(x_0)=0$ 而 $p(x_0)>0$，哪个 KL 会变成无穷？反过来呢？
4. 为什么说最小化 Forward KL 等价于 MLE？这一步用到了什么“与 $q$ 无关”的项？
5. 变分推断为什么用 Reverse KL 而不是 Forward KL？这带来了什么典型现象？
6. 语言模型训练和解码在 KL 方向上为什么是相反的？
