---
title: Word2Vec 表征原理
tags:
  - cs224n
  - nlp
  - word2vec
created: 2026-09-04
updated: 2026-09-09
---

> From: https://chatgpt.com/g/g-p-69e1418a1fe08191ad16139121982e76-ke-yan/c/6a9a1e23-f22c-83ee-9827-ea8d3db90478

# you asked

message time: 2026-09-04 09:26:08

word2vec，是如何表征的

---

# chatgpt response

Word2Vec 的“表征”可以抓住一句话：

> **它把每个离散的词，表征成一个低维、稠密、可学习的向量；这个向量的位置由“它经常和哪些词一起出现”决定。**

比如词表有 100,000 个词。最原始的表示其实可以是 one-hot：

$$
\text{king}=[0,0,\dots,1,\dots,0]\in\mathbb R^{100000}
$$

这个表示的问题是：**不同词之间没有任何天然关系**。  
“king”和“queen”的 one-hot 距离，和“king”与“banana”的距离其实一样。

Word2Vec 要做的就是把它变成类似：

$$
\mathbf v_{\text{king}}
=
[0.21,-0.73,0.15,\dots,0.48]
\in \mathbb R^{300}
$$

这里的 300 维向量，就是这个词的 **representation / embedding / 表征**。

---

### 1. Word2Vec 的表征本质上来自一个矩阵

假设：

- 词表大小 $V=100000$
- embedding 维度 $d=300$

Word2Vec 会学习一个矩阵：

$$
E\in\mathbb R^{V\times d}
$$

例如：

$$
E=
\begin{bmatrix}
- & \mathbf v_{\text{apple}} & -\\
- & \mathbf v_{\text{king}} & -\\
- & \mathbf v_{\text{queen}} & -\\
&\vdots&
\end{bmatrix}
$$

严格地说，每一行对应一个词。

所以：

$$
\mathbf v_{\text{king}}
=E[\text{king}]
$$

也可以把 embedding lookup 理解成：

$$
\mathbf v_{\text{king}}
=
\mathbf x_{\text{king}}^\top E
$$

其中 $\mathbf x_{\text{king}}$ 是 one-hot。

因此 Word2Vec 最直接的“表征过程”就是：

$$
\boxed{
\text{word ID}
\rightarrow
\text{embedding table}
\rightarrow
\text{dense vector}
}
$$

---

### 2. 关键问题：这个向量为什么能表达语义？

并不是因为某一维被人为规定成：

> 第 1 维 = 性别  
> 第 2 维 = 国家  
> 第 3 维 = 动物

不是这样的。

它的语义是**训练出来的**。

Word2Vec 背后的核心假设是经典的 distributional hypothesis：

> **You shall know a word by the company it keeps.**

也就是：

> 一个词的含义，可以由它周围经常出现的词来刻画。

例如：

> The **king** rules the country.  
> The **queen** rules the country.

“king”和“queen”周围经常出现：

- royal
- palace
- rule
- throne
- country

所以训练过程中，两者的向量会逐渐靠近。

而：

> I ate a **banana**.

banana 的上下文通常是：

- eat
- fruit
- yellow
- food

所以它会落到另一个区域。

最终 embedding 空间可能大致形成：

$$
\text{king}\approx\text{queen}
$$

$$
\text{dog}\approx\text{cat}
$$

$$
\text{Paris}\approx\text{London}
$$

这就是所谓：

> **语义关系被编码进向量空间的几何结构中。**

---

## 3. Skip-gram 是怎么逼着它学出这种表征的？

比如有一句：

> I love deep learning very much

窗口大小设为 2。

如果中心词是：

$$
\text{deep}
$$

上下文可能是：

$$
\{\text{I},\text{love},\text{learning},\text{very}\}
$$

Skip-gram 的任务就是：

$$
\boxed{
\text{给定 deep，预测周围出现什么词}
}
$$

即学习：

$$
P(w_{\text{context}}\mid w_{\text{center}})
$$

于是：

$$
\mathbf v_{\text{deep}}
$$

必须包含足够的信息，使模型能够预测：

- love
- learning
- very

如果两个词总是拥有相似的上下文，它们为了完成预测任务，就会学出相似的 embedding。

所以非常重要的一点是：

> **Word2Vec 没有直接告诉模型“king 和 queen 很相似”。**

它只是不断给模型做：

$$
\text{中心词}\rightarrow\text{预测上下文}
$$

但是作为这个任务的副产品，语义结构自己出现了。

---

## 4. CBOW 刚好反过来

CBOW：

$$
\text{上下文}
\rightarrow
\text{中心词}
$$

比如：

> I love ___ learning

给：

$$
\text{I},\text{love},\text{learning}
$$

预测：

$$
\text{deep}
$$

所以：

$$
P(w_{\text{center}}\mid w_{\text{context}})
$$

Skip-gram 和 CBOW 的训练目标不一样，但最后我们真正想要的东西都是那个：

$$
\boxed{\text{embedding matrix}}
$$

也就是词的向量表征。

---

## 5. 为什么 famous 的

$$
king-man+woman\approx queen
$$

会出现？

假设向量空间中存在某种隐含的“性别方向”。

比如：

$$
\mathbf v_{\text{king}}
-
\mathbf v_{\text{man}}
$$

留下来的大致是：

$$
\text{royalty}
$$

那么再加：

$$
\mathbf v_{\text{woman}}
$$

就可能得到：

$$
\text{female royalty}
$$

于是：

$$
\mathbf v_{\text{king}}
-
\mathbf v_{\text{man}}
+
\mathbf v_{\text{woman}}
\approx
\mathbf v_{\text{queen}}
$$

注意这不是人为规定的，而是大量统计共现关系在向量空间里的结果。

---

# 6. 最值得理解的一点：Word2Vec 的“表征”到底表征了什么？

它并不是完整地表征“这个词的真正含义”。

更准确地说，它表征的是：

$$
\boxed{
\text{这个词在整个训练语料中的使用模式 / 上下文统计模式}
}
$$

所以可以把它想成：

$$
\text{word}
\rightarrow
\text{context pattern}
\rightarrow
\text{vector}
$$

例如“cat”的向量里没有一张猫的照片，也没有一句：

> cat is an animal

而是通过大量：

> cat eats ...  
> pet cat ...  
> cat sleeps ...  
> dog and cat ...

这些上下文统计，逐渐形成了一个位置。

---

## 7. 这也是 Word2Vec 和今天 LLM 表征的一个关键区别

Word2Vec 的一个词只有一个固定向量：

$$
\text{bank}
\rightarrow
\mathbf v_{\text{bank}}
$$

不管：

> I deposited money in the **bank**.

还是：

> I sat on the river **bank**.

都是同一个向量。

所以叫：

$$
\boxed{\text{static embedding}}
$$

而 Transformer 里面：

$$
\text{bank}
$$

经过 self-attention 后，其 hidden state 会依赖上下文：

$$
\mathbf h_{\text{bank}}^{(\text{money})}
\neq
\mathbf h_{\text{bank}}^{(\text{river})}
$$

这就是：

$$
\boxed{\text{contextual representation}}
$$

所以从 Word2Vec 到 Transformer，可以理解成一次很重要的升级：

$$
\boxed{
\text{一个词一个固定表征}
\rightarrow
\text{一个词在不同上下文里拥有不同表征}
}
$$

---

如果把它和你前面一直在问的“**什么叫表征**”联系起来，Word2Vec 其实是非常经典的例子：

$$
\text{离散符号 king}
$$

本来机器只知道它是 vocabulary 里的第 528 号词。

经过训练后变成：

$$
\mathbf v_{\text{king}}\in\mathbb R^{300}
$$

此时，“king”与其他词的**语义关系，已经被编码进这个连续向量以及整个向量空间的几何关系里**。

这就是“学到一个表征”。🧠

如果你愿意，我下一步可以直接给你画清楚：

$$
\boxed{\text{one-hot}\rightarrow Word2Vec\rightarrow RNN hidden state\rightarrow Transformer representation}
$$

这条“**表征是怎么一步步演化的**”主线，其实正好能把 Word2Vec、Seq2Seq、Attention、Transformer 串成一条线。

---

# you asked

message time: 2026-09-04 09:27:10

如何训练的

---

# chatgpt response

Word2Vec 的训练本质上是在做一件很简单的事：

> **让真实上下文词的向量更接近，让随机无关词的向量更远。**

以最经典的 **Skip-gram + Negative Sampling** 为例。

假设有一句话：

> I love deep learning very much

窗口大小为 2，中心词是：

$$
\text{deep}
$$

那么真实上下文可以是：

$$
\{\text{I},\text{love},\text{learning},\text{very}\}
$$

于是会构造训练样本：

$$
(\text{deep}, \text{love})
$$

$$
(\text{deep}, \text{learning})
$$

这些是正样本。

---

### 1. Word2Vec 实际上维护两套向量

设词表大小为 $V$，embedding 维度为 $d$。

它会有两个矩阵：

$$
W\in\mathbb R^{V\times d}
$$

$$
W'\in\mathbb R^{V\times d}
$$

一个是：

$$
\boxed{\text{input embedding}}
$$

另一个是：

$$
\boxed{\text{output/context embedding}}
$$

比如：

$$
\mathbf v_{\text{deep}}
$$

来自 $W$。

而：

$$
\mathbf u_{\text{learning}}
$$

来自 $W'$。

训练时两者都更新。

---

### 2. 怎么判断 deep 和 learning 是否应该靠近？

直接算点积：

$$
s=
\mathbf v_{\text{deep}}^\top
\mathbf u_{\text{learning}}
$$

如果两个词关系强，希望：

$$
s \text{ 很大}
$$

然后经过 sigmoid：

$$
\sigma(s)
=
\frac{1}{1+e^{-s}}
$$

把它理解成：

$$
P(\text{learning 是 deep 的上下文})
$$

因此正样本：

$$
(\text{deep},\text{learning})
$$

希望：

$$
\sigma(
\mathbf v_{\text{deep}}^\top
\mathbf u_{\text{learning}}
)
\rightarrow 1
$$

---

## 3. 但是只有正样本不行

如果只告诉模型：

> deep 和 learning 应该靠近

最后所有词都靠在一起，也能得到很高分。

所以 Word2Vec 会随机抽一些负样本。

比如：

$$
(\text{deep},\text{banana})
$$

$$
(\text{deep},\text{chair})
$$

$$
(\text{deep},\text{car})
$$

这些并不是真实上下文。

希望：

$$
\sigma(
\mathbf v_{\text{deep}}^\top
\mathbf u_{\text{banana}}
)
\rightarrow 0
$$

也就是说：

$$
\mathbf v_{\text{deep}}^\top
\mathbf u_{\text{banana}}
$$

应该变小。

---

# 4. 所以一个训练样本长这样

正样本：

$$
(\text{deep},\text{learning}), y=1
$$

负样本：

$$
(\text{deep},\text{banana}), y=0
$$

$$
(\text{deep},\text{chair}), y=0
$$

$$
(\text{deep},\text{car}), y=0
$$

损失函数本质上就是二分类。

对于正样本：

$$
-\log
\sigma(
\mathbf v_c^\top\mathbf u_o
)
$$

对于负样本：

$$
-\log
\sigma(
-\mathbf v_c^\top\mathbf u_n
)
$$

合起来：

$$
\boxed{
L=
-\log\sigma(\mathbf v_c^\top\mathbf u_o)
-
\sum_{i=1}^{K}
\log\sigma(-\mathbf v_c^\top\mathbf u_{n_i})
}
$$

其中：

- $c$：center word
- $o$：真实 context word
- $n_i$：负样本
- $K$：负样本数量

---

# 5. 梯度下降到底在干什么？

假设：

$$
(\text{king},\text{queen})
$$

是真实上下文。

训练会调整：

$$
\mathbf v_{\text{king}}
$$

和：

$$
\mathbf u_{\text{queen}}
$$

让它们点积变大：

$$
\mathbf v_{\text{king}}^\top
\mathbf u_{\text{queen}}
\uparrow
$$

也就是：

$$
\text{king 和 queen 更“对得上”}
$$

而如果负样本是：

$$
\text{banana}
$$

就让：

$$
\mathbf v_{\text{king}}^\top
\mathbf u_{\text{banana}}
\downarrow
$$

所以你可以非常直观地理解成：

$$
\boxed{
\text{正样本：拉近}
}
$$

$$
\boxed{
\text{负样本：推远}
}
$$

大量句子训练以后，相似上下文的词就会形成类似的向量。

---

# 6. 为什么 king 和 queen 最后会相似？

不一定是因为训练数据里总有：

$$
(\text{king},\text{queen})
$$

直接同时出现。

更重要的是它们经常和相似的词共同出现。

例如：

$$
\text{king}
\rightarrow
\{
\text{royal},\text{palace},\text{rule},\text{throne}
\}
$$

$$
\text{queen}
\rightarrow
\{
\text{royal},\text{palace},\text{rule},\text{throne}
\}
$$

于是训练过程中：

$$
\mathbf v_{\text{king}}
$$

要对这些 context vector 都有较高点积。

同时：

$$
\mathbf v_{\text{queen}}
$$

也要对这些 context vector 有较高点积。

所以它们最终自然会落到相似的位置：

$$
\boxed{
\mathbf v_{\text{king}}
\approx
\mathbf v_{\text{queen}}
}
$$

这非常关键：

> **Word2Vec 不是直接训练“词和词相似度”，而是通过预测上下文，间接得到语义表征。**

---

# 7. 整个训练流程

可以概括成：

$$
\text{原始文本}
$$

↓

滑动窗口产生：

$$
(\text{center},\text{context})
$$

↓

例如：

$$
(\text{deep},\text{learning})
$$

↓

查 embedding：

$$
\mathbf v_{\text{deep}},
\mathbf u_{\text{learning}}
$$

↓

算点积：

$$
s=\mathbf v_{\text{deep}}^\top\mathbf u_{\text{learning}}
$$

↓

加负样本：

$$
\text{banana},\text{car},\text{chair}
$$

↓

计算 loss：

$$
L
$$

↓

反向传播：

$$
\frac{\partial L}{\partial W},
\frac{\partial L}{\partial W'}
$$

↓

更新 embedding matrix

↓

重复几十亿个词对。

最终得到：

$$
\boxed{W}
$$

作为词向量。

---

这里还有一个非常有意思的地方：**Word2Vec 几乎没有传统意义上的“深层神经网络”**。

Skip-gram 可以近似理解成：

$$
\text{one-hot}
\rightarrow
\text{embedding}
\rightarrow
\text{dot product}
\rightarrow
\text{loss}
$$

真正有价值的东西，就是训练过程中学出来的那个 embedding matrix。

所以 Word2Vec 是非常纯粹的一个例子：

> **为了完成一个代理任务——预测上下文，逼着模型学习出有用的表征。**

而这套思想后来其实贯穿了整个深度学习：

$$
\text{Word2Vec：预测上下文}
$$

$$
\downarrow
$$

$$
\text{BERT：预测被 mask 的词}
$$

$$
\downarrow
$$

$$
\text{GPT：预测下一个 token}
$$

最终真正想要的，都不仅是“预测答案”，而是让模型在预测过程中学到好的内部表征。🧠

---

# you asked

message time: 2026-09-04 09:41:22

那word2vec中相似的词的向量相似度是一定比较大吗接近1？

---

# chatgpt response

不一定，而且通常**不会“相似词就接近 1”**。

关键是先区分你说的“相似度”是哪一种。Word2Vec 里做词相似性时，最常用的是余弦相似度：

$$
\cos(\mathbf v_i,\mathbf v_j)
=
\frac{\mathbf v_i^\top \mathbf v_j}
{\|\mathbf v_i\|\|\mathbf v_j\|}
$$

它的范围是：

$$
[-1,1]
$$

但“两个词语义相似”只意味着它们的 cosine **往往比无关词更大**，并不意味着：

$$
\cos(\mathbf v_i,\mathbf v_j)\approx 1
$$

---

比如可能出现这种情况：

$$
\cos(\text{king},\text{queen})=0.65
$$

$$
\cos(\text{king},\text{prince})=0.58
$$

$$
\cos(\text{king},\text{banana})=0.12
$$

这已经说明：

$$
\text{king 和 queen 更相似}
$$

完全没必要接近 1。

如果真的：

$$
\cos(\mathbf v_i,\mathbf v_j)\approx 1
$$

意味着两个向量方向几乎完全一样，也就是它们在 Word2Vec 看来几乎拥有完全相同的上下文分布。这通常是非常强的条件。

---

还有一个你刚才的理解里特别容易混淆的地方：

### Word2Vec 训练时，并不是直接让两个“相似词”的 cosine 接近 1

Skip-gram + Negative Sampling 优化的是：

$$
\mathbf v_{\text{center}}^\top
\mathbf u_{\text{context}}
$$

也就是：

> **中心词向量和上下文词向量之间的点积。**

例如：

$$
\mathbf v_{\text{king}}^\top
\mathbf u_{\text{throne}}
$$

应该比较大。

而训练中并没有直接写一个 loss：

$$
\cos(
\mathbf v_{\text{king}},
\mathbf v_{\text{queen}}
)
\rightarrow 1
$$

没有这一项。

---

那为什么 king 和 queen 的向量最后还是会相似？

因为它们有类似的上下文。

假设：

$$
\text{king}
\rightarrow
\{
\text{throne},\text{palace},\text{royal},\text{rule}
\}
$$

而：

$$
\text{queen}
\rightarrow
\{
\text{throne},\text{palace},\text{royal},\text{rule}
\}
$$

训练要求：

$$
\mathbf v_{\text{king}}
$$

同时和这些 context vectors 匹配；

也要求：

$$
\mathbf v_{\text{queen}}
$$

和差不多这些 context vectors 匹配。

于是二者自然会学到相似方向：

$$
\mathbf v_{\text{king}}
\approx
\mathbf v_{\text{queen}}
$$

这是**间接产生的**，不是直接优化的。

---

还有一个更有意思的现象：**Word2Vec 的“相似”更准确地说是“分布相似”，不一定是人类理解中的同义词。**

比如：

$$
\text{good}
$$

和：

$$
\text{bad}
$$

语义是反义的，但它们经常出现在非常类似的句型里：

> This is a good movie.

> This is a bad movie.

所以 Word2Vec 可能会认为：

$$
\cos(\text{good},\text{bad})
$$

也不低。

因为它学的是：

$$
\boxed{
\text{上下文使用模式是否相似}
}
$$

而不是严格的：

$$
\boxed{
\text{两个词是不是同义词}
}
$$

这点特别重要。

所以可以把它总结成：

$$
\boxed{
\text{语义/用法相似}
\Rightarrow
\text{cosine 通常较大}
}
$$

但不是：

$$
\boxed{
\text{语义相似}
\Rightarrow
\cos\approx1
}
$$

更不是数学上的“一定”。

如果你继续往下学 Transformer，这里其实正好能引出一个很重要的问题：**为什么 embedding 相似度并不等于 attention 权重？** 这两个虽然都涉及向量点积，但含义完全不同。

---

# you asked

message time: 2026-09-04 09:43:42

介绍信skip-gram model

---

# chatgpt response

这张图画的就是 **Word2Vec 里的 Skip-gram**。它的核心任务可以一句话概括：

> **给定中心词 $w_t$，预测它周围可能出现哪些词。**

所以图右边的结构：

$$
w(t)
\rightarrow
\text{projection}
\rightarrow
\{w(t-2),w(t-1),w(t+1),w(t+2)\}
$$

就是 Skip-gram 的基本思想。

### 先看一个具体例子

假设语料中有一句：

> I like **deep** learning very much

设窗口大小 $m=2$，中心词是：

$$
w_t=\text{deep}
$$

那么上下文词是：

$$
w_{t-2}=\text{I}
$$

$$
w_{t-1}=\text{like}
$$

$$
w_{t+1}=\text{learning}
$$

$$
w_{t+2}=\text{very}
$$

Skip-gram 就会产生这些训练对：

$$
(\text{deep},\text{I})
$$

$$
(\text{deep},\text{like})
$$

$$
(\text{deep},\text{learning})
$$

$$
(\text{deep},\text{very})
$$

也就是说：

$$
\boxed{\text{center word}\rightarrow\text{context word}}
$$

这也是为什么叫 **Skip-gram**：用一个词去预测周围跨越一定距离的词。

---

## 图里的 Input 是什么？

图里的：

$$
w(t)
$$

就是中心词。

假设词表有：

$$
V=10000
$$

个词。

那么 deep 可以先表示成 one-hot：

$$
\mathbf x_{\text{deep}}
=
[0,0,\dots,1,\dots,0]
\in\mathbb R^{10000}
$$

比如 deep 是词表里的第 521 个词，那么第 521 位为 1。

---

## projection 是什么？

这是 Skip-gram 最重要的一层。

有一个可学习矩阵：

$$
W\in\mathbb R^{V\times d}
$$

例如：

$$
10000\times300
$$

然后：

$$
\mathbf h
=
\mathbf x_{\text{deep}}^\top W
$$

因为 $\mathbf x$ 是 one-hot，这个乘法实际上就是：

> **从 $W$ 中取出 deep 对应的那一行。**

所以：

$$
\mathbf h
=
\mathbf v_{\text{deep}}
\in\mathbb R^{300}
$$

这就是图中的：

$$
\boxed{\text{projection}}
$$

也就是我们一直说的：

$$
\boxed{\text{word embedding}}
$$

所以这里甚至没有什么复杂的神经网络运算：

$$
\text{one-hot}
\rightarrow
\text{embedding lookup}
$$

而已。

---

## 然后怎么预测上下文？

还会有第二个矩阵：

$$
W'\in\mathbb R^{d\times V}
$$

把中心词 embedding：

$$
\mathbf v_{\text{deep}}
$$

和每个候选上下文词的向量比较。

例如候选词 learning 对应：

$$
\mathbf u_{\text{learning}}
$$

然后计算：

$$
s_{\text{learning}}
=
\mathbf u_{\text{learning}}^\top
\mathbf v_{\text{deep}}
$$

如果这个值很大，就意味着：

> learning 很可能出现在 deep 周围。

理论上，对词表中所有词都计算：

$$
s_j
=
\mathbf u_j^\top\mathbf v_{\text{deep}}
$$

然后做 softmax：

$$
P(w_o\mid w_c)
=
\frac{
\exp(\mathbf u_o^\top\mathbf v_c)
}{
\sum_{j=1}^{V}
\exp(\mathbf u_j^\top\mathbf v_c)
}
$$

这里：

- $w_c$：center word
- $w_o$：outside/context word

所以：

$$
P(\text{learning}\mid\text{deep})
$$

如果很高，模型就预测对了。

---

## 训练目标是什么？

假设真实语料是：

> I like **deep learning** very much

那么我们希望：

$$
P(\text{learning}\mid\text{deep})
$$

尽可能大。

也希望：

$$
P(\text{like}\mid\text{deep})
$$

比较大。

因此单个词对的 loss 可以写成：

$$
L
=
-\log P(w_o\mid w_c)
$$

整个语料的目标就是：

$$
\boxed{
\max
\sum_t
\sum_{\substack{-m\le j\le m\\j\neq0}}
\log
P(w_{t+j}\mid w_t)
}
$$

这个公式其实就是 Skip-gram 的完整定义。

翻译成人话：

> 遍历语料中的每一个词，把它作为中心词，让模型尽可能正确地预测它窗口里的所有邻居。

---

### 对应你这张图

图右边：

$$
w(t)
\rightarrow
\text{projection}
\rightarrow
w(t-2)
$$

$$
\rightarrow w(t-1)
$$

$$
\rightarrow w(t+1)
$$

$$
\rightarrow w(t+2)
$$

不要误解成一次真正输出“四个位置上的四个不同网络分支”。

更准确地理解是：

$$
(w_t,w_{t-2})
$$

$$
(w_t,w_{t-1})
$$

$$
(w_t,w_{t+1})
$$

$$
(w_t,w_{t+2})
$$

是 **4 个训练样本，共享同一套参数**。

也就是说：

$$
\text{deep}\rightarrow\text{I}
$$

训练一次，

$$
\text{deep}\rightarrow\text{like}
$$

再训练一次，

等等。

这张图只是为了表达：

> **一个中心词负责预测整个窗口里的上下文。**

---

## 为什么这样能学到好的词向量？

这就是 Skip-gram 最漂亮的地方。

假设：

> king rules the kingdom  
> queen rules the kingdom

那么 king 经常需要预测：

$$
\text{royal},\text{palace},\text{rule},\text{throne},\dots
$$

queen 也经常需要预测：

$$
\text{royal},\text{palace},\text{rule},\text{throne},\dots
$$

也就是说：

$$
\mathbf v_{\text{king}}
$$

和

$$
\mathbf v_{\text{queen}}
$$

要完成非常类似的预测任务。

因此优化过程中，它们自然会逐渐变成相似的向量。

所以：

$$
\boxed{
\text{相似上下文}
\Rightarrow
\text{相似预测需求}
\Rightarrow
\text{相似 representation}
}
$$

这就是 Word2Vec 能得到语义向量的根本原因。

---

还有一个细节特别值得注意：**原始 Skip-gram 理论上要做完整 softmax，但词表可能有几十万、上百万个词，计算太贵。**

因此实际 Word2Vec 最著名的版本使用的是：

$$
\boxed{\text{Skip-gram + Negative Sampling}}
$$

把“预测整个词表”改造成：

> 这个词是不是中心词的真实上下文？

也就是我们上一轮聊到的：

$$
(\text{deep},\text{learning})\rightarrow 1
$$

$$
(\text{deep},\text{banana})\rightarrow0
$$

这才使 Word2Vec 训练变得非常高效。

所以你可以把整个 Skip-gram 记成这一张核心流程：

$$
\boxed{
\text{center word}
\xrightarrow{\text{embedding lookup}}
\mathbf v_c
\xrightarrow{\text{与 context vector 做点积}}
\text{score}
\xrightarrow{\text{softmax / negative sampling}}
\text{预测 context}
}
$$

训练时真正被我们留下来的，就是中间那个 **embedding matrix $W$**。这就是最后所谓的 **word representation**。🧠

---

# chatgpt response

这张图是在把 **Skip-gram 的“预测上下文词”这一步正式写成数学公式**。核心公式就是：

$$
P(o\mid c)
=
\frac{\exp(u_o^\top v_c)}
{\sum_{w\in V}\exp(u_w^\top v_c)}
$$

意思是：

> 已知中心词 $c$，计算词表中每个词 $o$ 成为它上下文词的概率。

这里最重要的是把这个公式拆成三步看。

### 1. 先计算中心词和候选上下文词的匹配分数

假设中心词是：

$$
c=\text{deep}
$$

中心词向量是：

$$
v_c=v_{\text{deep}}
$$

现在我们想判断：

$$
o=\text{learning}
$$

是不是它的上下文。

learning 作为“上下文词”时有一个向量：

$$
u_o=u_{\text{learning}}
$$

于是先算：

$$
u_o^\top v_c
$$

比如：

$$
u_{\text{learning}}^\top v_{\text{deep}}=3.2
$$

而：

$$
u_{\text{banana}}^\top v_{\text{deep}}=0.3
$$

那么模型就倾向于认为：

$$
\text{learning}
$$

比 banana 更可能出现在 deep 附近。

图上写：

> Dot product compares similarity of $o$ and $c$

这里的 “similarity” 是比较宽松的说法。严格来说，这是一个**匹配分数 score**，不是我们之前说的 cosine similarity。

因为点积：

$$
u^\top v
=
\|u\|\|v\|\cos\theta
$$

它不仅受方向影响，也受向量长度影响。

所以：

$$
\boxed{\text{Word2Vec训练直接优化的是点积分数，不是cosine}}
$$

---

### 2. 为什么要取指数 $\exp$？

点积可以是任意实数：

$$
-5,\quad0,\quad2,\quad10
$$

但概率必须：

$$
P>0
$$

所以先做：

$$
\exp(u_o^\top v_c)
$$

例如：

$$
3.2\rightarrow e^{3.2}\approx24.5
$$

$$
0.3\rightarrow e^{0.3}\approx1.35
$$

这样有两个作用。

第一，所有值都变成正数。

第二，大的 score 会被明显放大。例如：

$$
e^3\gg e^1
$$

所以模型更偏向高分的候选词。

---

### 3. 但这些还不是概率，所以要归一化

假设整个词表只有三个词：

$$
V=\{
\text{learning},
\text{banana},
\text{machine}
\}
$$

中心词是 deep。

点积结果：

$$
u_{\text{learning}}^\top v_{\text{deep}}=3
$$

$$
u_{\text{machine}}^\top v_{\text{deep}}=2
$$

$$
u_{\text{banana}}^\top v_{\text{deep}}=0
$$

取指数：

$$
e^3=20.09
$$

$$
e^2=7.39
$$

$$
e^0=1
$$

加起来：

$$
20.09+7.39+1=28.48
$$

因此：

$$
P(\text{learning}\mid\text{deep})
=
\frac{20.09}{28.48}
\approx0.705
$$

$$
P(\text{machine}\mid\text{deep})
\approx0.259
$$

$$
P(\text{banana}\mid\text{deep})
\approx0.035
$$

于是得到一个真正的概率分布：

$$
0.705+0.259+0.035=1
$$

这就是 **softmax**。

---

## 所以 softmax 到底干了什么？

给一组任意实数：

$$
[x_1,x_2,\dots,x_n]
$$

通过：

$$
p_i=
\frac{e^{x_i}}
{\sum_j e^{x_j}}
$$

变成：

$$
[p_1,p_2,\dots,p_n]
$$

满足：

$$
0<p_i<1
$$

以及：

$$
\sum_i p_i=1
$$

所以：

$$
\boxed{
\text{scores}
\xrightarrow{\text{softmax}}
\text{probability distribution}
}
$$

这和今天 Transformer 最后一层预测 next token 是完全同一类操作：

$$
\text{hidden state}
\rightarrow
\text{logits}
\rightarrow
\text{softmax}
\rightarrow
P(\text{next token})
$$

---

## 为什么名字叫 soft-max？

假设：

$$
x=[1,2,5]
$$

如果是 hard max，相当于直接：

$$
[0,0,1]
$$

只保留最大的。

但 softmax 可能得到：

$$
[0.017,0.047,0.936]
$$

最大的 $5$ 获得最大概率，但其他位置仍然有概率。

所以：

$$
\text{max}
$$

表示偏向最大的值；

$$
\text{soft}
$$

表示不是硬选一个。

因此叫：

$$
\boxed{\text{softmax}}
$$

---

## 再回到 Skip-gram

假设真实语料：

> I love **deep learning**

中心词：

$$
c=\text{deep}
$$

真实 outside word：

$$
o=\text{learning}
$$

模型产生：

$$
P(w\mid\text{deep})
$$

覆盖整个词表：

$$
\begin{array}{c|c}
w & P(w\mid\text{deep})\\
\hline
learning & 0.10\\
banana & 0.02\\
machine & 0.08\\
love & 0.05\\
\vdots&\vdots
\end{array}
$$

真实答案是 learning。

所以训练目标就是提高：

$$
P(\text{learning}\mid\text{deep})
$$

也就是最小化：

$$
L=-\log P(\text{learning}\mid\text{deep})
$$

如果原来：

$$
P=0.1
$$

训练后：

$$
P=0.5
$$

loss 就下降了。

而为了让这个概率上升，模型会调整：

$$
v_{\text{deep}}
$$

以及：

$$
u_{\text{learning}}
$$

让：

$$
u_{\text{learning}}^\top v_{\text{deep}}
$$

变得更大。

---

这里还有一个特别重要的细节，你现在应该开始注意了：

Word2Vec 实际有 **两套词向量**：

$$
\boxed{v_w:\text{词作为 center 时的向量}}
$$

和：

$$
\boxed{u_w:\text{词作为 context 时的向量}}
$$

所以公式才不是：

$$
v_o^\top v_c
$$

而是：

$$
\boxed{u_o^\top v_c}
$$

例如 deep：

$$
v_{\text{deep}}
$$

是 deep 作为中心词时的 representation。

learning：

$$
u_{\text{learning}}
$$

是 learning 作为上下文候选时的 representation。

这两套矩阵：

$$
V\in\mathbb R^{|V|\times d}
$$

$$
U\in\mathbb R^{|V|\times d}
$$

都会在训练过程中学习。

最后使用 Word2Vec embedding 时，通常主要取其中一套（经典实现里常取 input embeddings $v_w$），也有做法会组合两套。

---

### 把整张图压缩成一条链

你可以这样记：

$$
\boxed{
c
\rightarrow
v_c
\rightarrow
u_w^\top v_c
\rightarrow
\text{对整个词表得到 scores}
\rightarrow
softmax
\rightarrow
P(w\mid c)
}
$$

例如：

$$
\boxed{
\text{deep}
\rightarrow
v_{\text{deep}}
\rightarrow
\begin{bmatrix}
u_{\text{I}}^\top v_{\text{deep}}\\
u_{\text{love}}^\top v_{\text{deep}}\\
u_{\text{learning}}^\top v_{\text{deep}}\\
\vdots
\end{bmatrix}
\rightarrow
\operatorname{softmax}
\rightarrow
P(w\mid\text{deep})
}
$$

这其实已经非常接近现代语言模型的基本思想了：**一个向量与一整套候选向量做点积，再通过 softmax 得到概率分布。**

而后面的 Transformer 里你会反复看到这个模式，例如 attention：

$$
QK^\top\rightarrow\operatorname{softmax}
$$

本质上也是“**点积打分 → softmax 归一化**”，只是 softmax 后的含义从“哪个词最可能是上下文”变成了“应该从哪些 token 获取多少信息”。这两者的联系很值得抓住。

---

# you asked

message time: 2026-09-04 09:51:29

单独取用哪一套有影响吗

---

# chatgpt response

有影响，但通常不是“一个有语义、一个没语义”的区别。**两套向量都学到了信息，只是角色不同，因此几何结构不会完全一样。**

在 Skip-gram 中，同一个词 $w$ 有：

$$
v_w \quad\text{center/input embedding}
$$

和

$$
u_w \quad\text{context/output embedding}
$$

训练直接约束的是：

$$
\boxed{u_o^\top v_c}
$$

而不是：

$$
v_o^\top v_c
$$

也不是：

$$
u_o^\top u_c
$$

所以训练结束后，没有任何机制要求：

$$
v_w=u_w
$$

甚至也没有要求两套空间内部的词间距离完全一致。

---

举个例子，训练后可能是：

$$
\cos(v_{\text{king}},v_{\text{queen}})=0.72
$$

但：

$$
\cos(u_{\text{king}},u_{\text{queen}})=0.63
$$

甚至最近邻排序也可能有些不同。

原因是：

- $v_w$：学习的是“**我作为中心词时，应该预测什么上下文**”
- $u_w$：学习的是“**我作为上下文时，应该被哪些中心词预测到**”

这两个统计角色非常相关，但并不完全相同。

---

### 那 Word2Vec 最后一般取哪一个？

经典用法通常直接取：

$$
\boxed{v_w}
$$

也就是 **input/center embedding**。

例如我们说：

$$
\cos(v_{\text{king}},v_{\text{queen}})
$$

或者：

$$
v_{\text{king}}
-v_{\text{man}}
+v_{\text{woman}}
\approx v_{\text{queen}}
$$

一般指的就是这一套词向量。

但 $u_w$ 也不是“训练完就没用了”。它同样包含语义信息。

---

### 甚至可以把两套合起来

例如：

$$
e_w=v_w+u_w
$$

或者：

$$
e_w=\frac{v_w+u_w}{2}
$$

再用：

$$
\cos(e_i,e_j)
$$

做词相似度。

在一些任务和实现中，这样甚至会比单独使用 $v_w$ 更好，因为两边学到的是互补的信息。

不过要注意一个关键区别：

如果你想衡量的是 **两个词本身的语义相似性**，最好统一使用：

$$
v_a \leftrightarrow v_b
$$

或者：

$$
u_a \leftrightarrow u_b
$$

或者组合后的：

$$
e_a \leftrightarrow e_b
$$

而不是随便拿：

$$
v_a^\top u_b
$$

然后把它叫做“词语义相似度”。

因为：

$$
\boxed{v_a^\top u_b}
$$

在 Word2Vec 训练中真正表示的是：

> **$b$ 作为 context 出现在 $a$ 周围的匹配程度。**

它更接近 **center-context compatibility**，而不是严格意义上的两个词“是不是相似”。

---

其实这里有一个很漂亮的区别：

$$
\boxed{
u_{\text{learning}}^\top v_{\text{deep}}
}
$$

问的是：

> learning 适不适合作为 deep 的上下文？

而：

$$
\boxed{
\cos(v_{\text{deep}},v_{\text{machine}})
}
$$

问的是：

> deep 和 machine 的整体上下文使用模式是否相似？

这是**两个不同的问题**。

所以你前面问“Word2Vec 中相似词向量是不是接近 1”，这里就能进一步看到：**训练本身甚至都没有直接优化同一套词向量之间的 cosine similarity；相似词聚在一起，是预测上下文这个训练目标间接产生出来的。** 🧠

---

# you asked

message time: 2026-09-04 09:52:29

一个word的维度是多少

---

# chatgpt response

在 Word2Vec 里，**一个 word 最终的向量维度是人为设定的超参数 $d$**，不是固定的。

例如你设置：

$$
d=300
$$

那么每个词都会被表示成：

$$
v_w\in\mathbb R^{300}
$$

也就是 **300 维向量**。

常见设置有：

$$
d=50,\ 100,\ 200,\ 300
$$

经典 Word2Vec 里很常见的是：

$$
\boxed{d=300}
$$

比如：

$$
v_{\text{king}}
=
[0.12,-0.37,0.81,\dots]
$$

一共 300 个数。

要注意不要和 **one-hot 维度**混淆。假设词表大小：

$$
|V|=100000
$$

那么：

- one-hot 表示维度是 $100000$
- Word2Vec embedding 维度可能是 $300$

即：

$$
\boxed{
\mathbb R^{100000}
\rightarrow
\mathbb R^{300}
}
$$

如果词表有 10 万个词，embedding 维度是 300，那么输入 embedding 矩阵就是：

$$
W\in\mathbb R^{100000\times300}
$$

每一行就是一个词的 300 维向量。

而且前面提到 Word2Vec 有两套向量，所以实际上训练时通常有：

$$
W_{\text{input}}\in\mathbb R^{V\times d}
$$

$$
W_{\text{output}}\in\mathbb R^{V\times d}
$$

如果 $d=300$，那么**无论 center embedding 还是 context embedding，每个 word 都是 300 维**。

---

# chatgpt response

这张图是在把 **Skip-gram 的整体训练目标**正式写出来。你可以把它理解成：前面我们只看了一个中心词 $c$ 和一个上下文词 $o$，现在把它扩展到**整个语料库所有位置**。

最上面的式子是：

$$
L(\theta)
=
\prod_{t=1}^{T}
\prod_{\substack{-m\le j\le m\\j\neq0}}
P(w_{t+j}\mid w_t;\theta)
$$

它的意思其实非常直白：

> **遍历语料中的每一个中心词 $w_t$，希望它周围真实出现的所有上下文词 $w_{t+j}$ 的概率都尽可能大。**

---

假设一句话是：

$$
w_1,w_2,w_3,w_4,w_5
$$

例如：

> I love deep learning very

设：

$$
t=3
$$

那么：

$$
w_t=\text{deep}
$$

如果窗口大小：

$$
m=2
$$

那么 $j$ 可以取：

$$
-2,-1,1,2
$$

注意不能取 $j=0$，因为：

$$
w_{t+0}=w_t
$$

就是自己，不需要预测自己。

所以对 deep 来说，要预测：

$$
w_{3-2}=w_1=\text{I}
$$

$$
w_{3-1}=w_2=\text{love}
$$

$$
w_{3+1}=w_4=\text{learning}
$$

$$
w_{3+2}=w_5=\text{very}
$$

于是这一小部分目标就是：

$$
P(\text{I}\mid\text{deep})
\cdot
P(\text{love}\mid\text{deep})
\cdot
P(\text{learning}\mid\text{deep})
\cdot
P(\text{very}\mid\text{deep})
$$

Skip-gram 希望这个乘积尽可能大。

---

## 两层乘积分别是什么意思？

第一层：

$$
\prod_{t=1}^{T}
$$

意思是：

> 遍历整个语料中的所有中心位置。

这里 $T$ 是语料中的 token 总数。

比如：

$$
t=1,2,3,\dots,T
$$

---

第二层：

$$
\prod_{\substack{-m\le j\le m\\j\neq0}}
$$

意思是：

> 对每一个中心词，再遍历它窗口中的上下文词。

如果：

$$
m=2
$$

那么就是：

$$
j=-2,-1,1,2
$$

因此整个目标就是：

$$
\boxed{
\text{所有 center-context 真实词对概率的乘积}
}
$$

---

## 那 $\theta$ 是什么？

这里的：

$$
\theta
$$

代表 Word2Vec 所有需要学习的参数。

本质上就是前面说的两套 embedding：

$$
v_w
$$

以及：

$$
u_w
$$

也就是：

$$
\theta=
\{v_w,u_w\}_{w\in V}
$$

或者从矩阵角度：

$$
\theta=\{W_{\text{input}},W_{\text{output}}\}
$$

训练就是不断调整这些向量。

---

## 下面这个式子就是单个词对的概率

对于一个 center：

$$
c
$$

以及真实 context：

$$
o
$$

有：

$$
P(o\mid c)
=
\frac{
\exp(u_o^\top v_c)
}{
\sum_{w\in V}
\exp(u_w^\top v_c)
}
$$

这就是前面讲过的 softmax。

所以整个逻辑其实是：

$$
\boxed{
\text{一个词对的概率}
\rightarrow
P(o\mid c)
}
$$

然后：

$$
\boxed{
\text{把整个语料所有词对的概率乘起来}
\rightarrow
L(\theta)
}
$$

最后选择参数：

$$
\theta
$$

让：

$$
L(\theta)
$$

最大。

---

# 但是实际训练不会直接优化这个乘积

这是非常重要的一步。

因为假设每个概率都小于 1：

$$
0.1\times0.2\times0.05\times\cdots
$$

乘几百万、几十亿次以后，会变成一个极小的数字：

$$
10^{-1000000}
$$

计算机很容易数值下溢。

所以我们取 log。

原来的目标：

$$
\max_\theta
\prod P
$$

因为 log 是单调递增的，所以等价于：

$$
\max_\theta
\log\prod P
$$

利用：

$$
\log(ab)=\log a+\log b
$$

得到：

$$
\max_\theta
\sum_{t=1}^{T}
\sum_{\substack{-m\le j\le m\\j\neq0}}
\log
P(w_{t+j}\mid w_t;\theta)
$$

这就是 **log-likelihood**。

而机器学习通常习惯“最小化 loss”，于是再加一个负号：

$$
\boxed{
J(\theta)
=
-
\sum_{t=1}^{T}
\sum_{\substack{-m\le j\le m\\j\neq0}}
\log
P(w_{t+j}\mid w_t;\theta)
}
$$

然后做：

$$
\boxed{
\min_\theta J(\theta)
}
$$

这就是 Skip-gram 的训练目标。

---

举个特别简单的例子。

假设：

> I love deep learning

中心词：

$$
c=\text{deep}
$$

真实上下文是：

$$
o=\text{learning}
$$

模型一开始预测：

$$
P(\text{learning}\mid\text{deep})=0.01
$$

那么 loss：

$$
-\log0.01\approx4.605
$$

训练一段时间后：

$$
P(\text{learning}\mid\text{deep})=0.5
$$

loss 变成：

$$
-\log0.5\approx0.693
$$

因此：

$$
4.605\rightarrow0.693
$$

loss 降低。

为了做到这一点，模型会调整：

$$
v_{\text{deep}}
$$

和：

$$
u_{\text{learning}}
$$

使：

$$
u_{\text{learning}}^\top v_{\text{deep}}
$$

变大。

---

所以这一页你真正需要记住的是：

$$
\boxed{
\text{Skip-gram}
=
\text{让真实上下文的条件概率最大}
}
$$

即：

$$
\boxed{
\max
\prod_{\text{所有真实 center-context pair}}
P(\text{context}\mid\text{center})
}
$$

实际计算则写成：

$$
\boxed{
\min
-
\sum
\log P(\text{context}\mid\text{center})
}
$$

也就是经典的 **negative log-likelihood / cross-entropy**。

这里其实已经和今天训练 GPT 非常像了：

$$
\text{Word2Vec: }
-\log P(\text{context}\mid\text{center})
$$

而 GPT：

$$
\text{GPT: }
-\log P(\text{next token}\mid\text{previous tokens})
$$

差别主要在于“给定什么信息去预测什么”，但背后的最大似然训练思想是一脉相承的。

---

# chatgpt response

这页是在把前面讲的 Word2Vec 进一步归纳成一个“算法家族”。核心其实有三层：

> **模型结构选什么？训练目标怎么定义？损失函数怎么高效算？**

你可以把整页理解成这三个问题。

---

### 第一层：为什么一个词要有两套向量？

前面 Skip-gram 里我们写过：

$$
P(o\mid c)
=
\frac{\exp(u_o^\top v_c)}
{\sum_{w\in V}\exp(u_w^\top v_c)}
$$

这里同一个词有两种角色：

$$
v_w:\quad \text{作为 center word 的向量}
$$

$$
u_w:\quad \text{作为 context/outside word 的向量}
$$

所以训练时实际上有两套 embedding matrix：

$$
V\in\mathbb R^{|V|\times d}
$$

$$
U\in\mathbb R^{|V|\times d}
$$

这页说：

> Why two vectors? → Easier optimization.

也就是说，两套参数让模型更容易分别承担“作为输入词”和“作为输出词”这两个角色，优化更灵活。

如果强行只用一套：

$$
u_w=v_w
$$

也是可以定义模型的，但约束更强。

这页还说：

> Average both at the end.

也就是说训练完之后，可以构造：

$$
e_w=\frac{u_w+v_w}{2}
$$

作为最终 word embedding。

不过不同实现习惯不同：有的只用 $v_w$，有的取平均或求和。

---

# 第二层：Word2Vec 有两个模型变体

## 1. Skip-gram

就是我们前面一直讲的：

$$
\boxed{
\text{center word}
\rightarrow
\text{predict context words}
}
$$

比如：

> I really like **deep** learning very much

中心：

$$
c=\text{deep}
$$

上下文窗口：

$$
\{\text{really},\text{like},\text{learning},\text{very}\}
$$

Skip-gram 构造：

$$
(\text{deep},\text{really})
$$

$$
(\text{deep},\text{like})
$$

$$
(\text{deep},\text{learning})
$$

$$
(\text{deep},\text{very})
$$

也就是：

$$
\boxed{1\rightarrow many}
$$

---

这页还特别写了一句：

> position independent

这个很重要。

Skip-gram 通常只关心某个词是不是在窗口里，不特别区分：

$$
t-1
$$

还是：

$$
t+1
$$

比如：

$$
P(w_{t-1}\mid w_t)
$$

和：

$$
P(w_{t+1}\mid w_t)
$$

用的是同一套预测机制。

所以它并不像 Transformer 那样显式建模：

> “这个词是在左边第 1 个位置，还是右边第 2 个位置”。

这也是 Word2Vec 的一个明显局限。

---

# 2. CBOW

CBOW 正好反过来：

$$
\boxed{
\text{context words}
\rightarrow
\text{predict center word}
}
$$

比如：

> I really like **deep** learning very much

给模型：

$$
\{\text{really},\text{like},\text{learning},\text{very}\}
$$

预测：

$$
\text{deep}
$$

所以：

$$
\boxed{many\rightarrow1}
$$

这就是 Continuous Bag of Words。

“Bag of Words” 的意思就是：

> **把上下文当成一个词袋，而不太关心它们的顺序。**

通常先把上下文词 embedding 做平均：

$$
h=
\frac{1}{2m}
\sum_{j\neq0}v_{w_{t+j}}
$$

然后用 $h$ 去预测中心词：

$$
P(w_t\mid context)
$$

---

所以 Skip-gram 和 CBOW 的区别非常简单：

$$
\boxed{
\text{Skip-gram: center }\rightarrow\text{ context}
}
$$

$$
\boxed{
\text{CBOW: context }\rightarrow\text{ center}
}
$$

你甚至可以画成：

$$
\text{Skip-gram:}
\qquad
w_t
\rightarrow
\begin{cases}
w_{t-2}\\
w_{t-1}\\
w_{t+1}\\
w_{t+2}
\end{cases}
$$

而：

$$
\text{CBOW:}
\qquad
\begin{cases}
w_{t-2}\\
w_{t-1}\\
w_{t+1}\\
w_{t+2}
\end{cases}
\rightarrow
w_t
$$

---

# 第三层：Loss 怎么计算？

这页下面列了三个：

$$
1.\ \text{Naive Softmax}
$$

$$
2.\ \text{Hierarchical Softmax}
$$

$$
3.\ \text{Negative Sampling}
$$

注意：

> **这三个不是三个 Word2Vec 模型，而是训练 Skip-gram / CBOW 时的不同优化方式。**

所以不要把它和 Skip-gram、CBOW 混在一起。

完整结构应该理解成：

$$
\boxed{
\text{Word2Vec}
}
$$

下面先选：

$$
\begin{cases}
\text{Skip-gram}\\
\text{CBOW}
\end{cases}
$$

然后训练时再选：

$$
\begin{cases}
\text{Naive Softmax}\\
\text{Hierarchical Softmax}\\
\text{Negative Sampling}
\end{cases}
$$

---

## Naive Softmax

就是前面讲过的：

$$
P(o\mid c)
=
\frac{
e^{u_o^\top v_c}
}{
\sum_{w\in V}e^{u_w^\top v_c}
}
$$

最大的问题就在分母：

$$
\sum_{w\in V}
$$

如果词表：

$$
|V|=1,000,000
$$

那么每训练一个：

$$
(c,o)
$$

都要和 **100 万个词**算：

$$
u_w^\top v_c
$$

复杂度大约：

$$
O(|V|d)
$$

非常贵。

---

## Hierarchical Softmax

它的思想是：

> 不直接在 100 万个词里做一次 100 万分类，而是把词表组织成一棵树。

例如二叉树。

原来：

$$
O(|V|)
$$

变成大约：

$$
O(\log |V|)
$$

比如：

$$
|V|=1,000,000
$$

那么：

$$
\log_2(1,000,000)\approx20
$$

就从“比较 100 万个候选”变成沿树走大约 20 步。

---

## Negative Sampling

这个最重要，也是 Word2Vec 最经典的技巧之一。

它直接放弃：

$$
P(o\mid c)
$$

这种完整的多分类问题。

改成：

> **判断某个 $c,o$ 词对是不是真实出现过的。**

例如真实词对：

$$
(\text{deep},\text{learning})
$$

标记：

$$
y=1
$$

然后随机抽几个词：

$$
(\text{deep},\text{banana})
$$

$$
(\text{deep},\text{car})
$$

$$
(\text{deep},\text{chair})
$$

标记：

$$
y=0
$$

于是只需要计算：

$$
u_{\text{learning}}^\top v_{\text{deep}}
$$

以及几个负样本：

$$
u_{\text{banana}}^\top v_{\text{deep}}
$$

等等。

如果只抽：

$$
K=5
$$

个负样本，那么每个训练 pair 只处理：

$$
1+5=6
$$

个词，而不是：

$$
1,000,000
$$

个词。

计算量直接大幅下降。

---

所以这页最值得你建立的是这个**层次结构**：

$$
\boxed{
\text{Word2Vec}
}
$$

第一层，决定**预测方向**：

$$
\boxed{
\begin{array}{ll}
\text{Skip-gram}: & center\rightarrow context\\
\text{CBOW}: & context\rightarrow center
\end{array}
}
$$

第二层，决定**训练时怎么高效算概率/loss**：

$$
\boxed{
\begin{array}{l}
\text{Naive Softmax}\\
\text{Hierarchical Softmax}\\
\text{Negative Sampling}
\end{array}
}
$$

而最终目标始终没有变：

> **通过局部上下文预测任务，让词向量自己学出语义结构。**

如果你继续看下一页，大概率就会正式进入 **Negative Sampling**。这一部分很重要，因为它能让你第一次很清楚地看到：

$$
\boxed{
\text{“预测整个词表”}
\rightarrow
\text{“正负样本二分类”}
}
$$

这个思想后来在表示学习、对比学习里会反复出现。

---

# you asked

message time: 2026-09-04 09:57:21

Negative Sampling是要比Naive softmax好吗

---

# chatgpt response

如果你问的是 **“训练 Word2Vec 时 Negative Sampling 是否整体上优于 Naive Softmax”**，更准确的答案是：

> **在大词表的 Word2Vec 训练里，Negative Sampling 通常更实用，也往往是更好的工程选择；但它并不是在所有意义上都“更好”。**

最关键的区别是：**它们优化的目标其实不完全一样。**

Naive Softmax 真正在学：

$$
P(o\mid c)
=
\frac{\exp(u_o^\top v_c)}
{\sum_{w\in V}\exp(u_w^\top v_c)}
$$

也就是说，给定中心词 $c$，它希望得到一个**真正归一化的整个词表概率分布**。

例如：

$$
P(\text{learning}\mid\text{deep})=0.12
$$

$$
P(\text{machine}\mid\text{deep})=0.08
$$

等等，并且：

$$
\sum_{w\in V}P(w\mid c)=1
$$

所以如果你的目标真的是：

> **准确建模“某个 context word 出现的条件概率”**

那么 Naive Softmax 的目标更加直接、严格。

---

而 Negative Sampling 不再计算这个完整概率。

它把问题改成：

> 给我一个 $(c,o)$ 词对，判断它是不是来自真实语料。

正样本：

$$
(\text{deep},\text{learning}),\quad y=1
$$

负样本：

$$
(\text{deep},\text{banana}),\quad y=0
$$

于是优化：

$$
\log \sigma(u_o^\top v_c)
+
\sum_{i=1}^K
\log \sigma(-u_{n_i}^\top v_c)
$$

它本质上是在做：

$$
\boxed{\text{real pair vs noise pair}}
$$

而不是直接做：

$$
\boxed{\text{整个词表上的多分类}}
$$

---

## 为什么 Word2Vec 里大家更喜欢 Negative Sampling？

主要是因为计算量差距非常大。

假设：

$$
|V|=1,000,000
$$

embedding 维度：

$$
d=300
$$

Naive Softmax 每处理一个 center-context pair，都要和整个词表的 100 万个 output vectors 做点积：

$$
O(|V|d)
$$

也就是数量级：

$$
10^6\times300
$$

而 Negative Sampling 如果：

$$
K=5
$$

那么只需要算：

- 1 个正样本
- 5 个负样本

一共 6 个点积：

$$
O(Kd)
$$

也就是：

$$
6\times300
$$

差距可以非常夸张。

所以从工程角度：

$$
\boxed{
\text{Negative Sampling} \gg \text{Naive Softmax}
}
$$

尤其是在大规模语料和大词表下。

---

## 那 embedding 质量呢？

有意思的地方就在这里。

虽然 Negative Sampling 是一种“近似/替代训练目标”，但 Word2Vec 最终通常不是为了得到非常精确的：

$$
P(o\mid c)
$$

而是为了得到好的：

$$
\boxed{\text{word representation}}
$$

例如用于：

- word similarity
- analogy
- downstream NLP

在这些任务上，Negative Sampling 往往表现很好，有时甚至比完整 softmax 更适合学语义 embedding。

原因之一是：

> 它明确要求模型把真实共现词对拉近，把噪声词对推远。

所以它非常直接地塑造了 embedding space 的几何结构。

可以粗略理解成：

$$
\text{positive pair}
\Rightarrow
u_o^\top v_c\uparrow
$$

$$
\text{negative pair}
\Rightarrow
u_n^\top v_c\downarrow
$$

这和后来很多 representation learning / contrastive learning 的思想其实很相似。

---

## 但是有一个重要代价

Negative Sampling 训练出来以后：

$$
\sigma(u_o^\top v_c)
$$

**不能直接理解成**

$$
P(o\mid c)
$$

它不是完整词表上的真实归一化概率。

所以如果你关心的是：

> “deep 后面/周围出现 learning 的真正概率是多少？”

那 Negative Sampling 并没有直接给你这个东西。

而 Naive Softmax 的：

$$
P(o\mid c)
$$

则确实是一个完整概率分布。

所以可以这样对比：

| | Naive Softmax | Negative Sampling |
|---|---|---|
| 目标 | 预测整个词表 | 区分真实词对和噪声词对 |
| 是否输出完整概率 | ✅ | ❌ |
| 每步计算量 | $O(|V|d)$ | $O(Kd)$ |
| 大词表效率 | 很差 | 很高 |
| 学 embedding | 可以 | 非常适合 |
| Word2Vec 实践 | 少直接用 | 非常常用 |

所以如果你的核心目标是：

$$
\boxed{\text{我要一个好的 Word2Vec 词向量}}
$$

那么一般可以认为：

$$
\boxed{\text{Negative Sampling 是更好的选择}}
$$

但如果目标是：

$$
\boxed{\text{我要严格建模 }P(o\mid c)}
$$

那不能简单说 Negative Sampling 比 Softmax 好。

一个很值得你注意的历史联系是：**Word2Vec 的 Negative Sampling 已经非常接近后来“对比学习”的思想了**——不一定非要精确建模整个分布，只需要通过“正样本 vs 负样本”就可以逼着模型学出很好的表征。🧠

---

# you asked

message time: 2026-09-04 09:58:30

有点像对比学习？

---

# chatgpt response

对，很像，而且可以把 **Word2Vec 的 Negative Sampling 看成后来对比学习思想的早期雏形之一**。核心直觉几乎一致：

$$
\boxed{
\text{正样本拉近，负样本推远}
}
$$

在 Skip-gram + Negative Sampling 里，一个真实共现词对：

$$
(c,o)
$$

比如：

$$
(\text{deep},\text{learning})
$$

是正样本，希望：

$$
u_o^\top v_c \uparrow
$$

也就是：

$$
\sigma(u_o^\top v_c)\rightarrow 1
$$

而随机采样的：

$$
(\text{deep},\text{banana})
$$

是负样本，希望：

$$
u_n^\top v_c \downarrow
$$

也就是：

$$
\sigma(u_n^\top v_c)\rightarrow 0
$$

它的目标：

$$
\log \sigma(u_o^\top v_c)
+
\sum_{i=1}^{K}
\log \sigma(-u_{n_i}^\top v_c)
$$

本质就是：

> 让真实 pair 的表示更匹配，让噪声 pair 的表示更不匹配。

这和今天对比学习的直觉非常接近。

---

比如现代对比学习里可能有：

$$
\text{image}
\leftrightarrow
\text{its caption}
$$

是正样本，

而：

$$
\text{image}
\leftrightarrow
\text{other captions}
$$

是负样本。

像 CLIP 就是：

$$
\boxed{
\text{匹配图文拉近，不匹配图文推远}
}
$$

Word2Vec 则是：

$$
\boxed{
\text{真实 center-context 拉近，随机词对推远}
}
$$

所以结构上非常像：

$$
\text{Word2Vec:}
\quad
\text{word}\leftrightarrow\text{context}
$$

$$
\text{CLIP:}
\quad
\text{image}\leftrightarrow\text{text}
$$

---

不过两者还是有一个重要区别。

Word2Vec Negative Sampling 通常是**独立二分类**：

$$
\text{这个 pair 是真的还是噪声？}
$$

每个负样本分别经过 sigmoid。

而很多现代对比学习，比如 InfoNCE / CLIP，更像是在一堆候选中做 softmax：

$$
L
=
-\log
\frac{
\exp(s(q,k^+)/\tau)
}{
\exp(s(q,k^+)/\tau)
+
\sum_j
\exp(s(q,k_j^-)/\tau)
}
$$

也就是：

> 在这么多候选里面，真正匹配的是哪一个？

所以可以粗略区分：

$$
\boxed{
\text{Word2Vec Negative Sampling}
\approx
\text{多个 sigmoid 二分类}
}
$$

而：

$$
\boxed{
\text{现代 InfoNCE}
\approx
\text{正样本 vs 一组负样本的 softmax 竞争}
}
$$

---

还有一个细节：你刚才说的“拉近、推远”是非常好的直觉，但严格来说 Word2Vec 直接优化的是：

$$
u_o^\top v_c
$$

也就是**点积匹配分数**。

它并不是明确写着：

$$
\|\mathbf v_c-\mathbf u_o\|\rightarrow0
$$

所以“拉近”是几何上的直观理解，不是 loss 里真的直接最小化欧氏距离。

---

你可以把这一条发展线记成：

$$
\boxed{
\text{Word2Vec Negative Sampling}
\rightarrow
\text{Noise Contrastive Estimation / contrastive ideas}
\rightarrow
\text{InfoNCE}
\rightarrow
\text{SimCLR / CLIP 等现代对比学习}
}
$$

它们背后的共同思想都是：

> **我未必需要显式告诉模型“语义是什么”，只要设计好正负关系，就能逼着模型学出有结构的表示空间。**

这也是为什么 Word2Vec 在表示学习历史上特别重要。🧠

---

# you asked

message time: 2026-09-04 09:59:30

不理解

---

# chatgpt response

可以把它想成：**Word2Vec 的 Negative Sampling 不再问“下一个词到底是哪一个？”；而是把每一对词单独拿出来，问一句“这对是真的还是假的？”**

假设中心词是：

$$
c=\text{deep}
$$

真实上下文是：

$$
o=\text{learning}
$$

我们再随机抽 3 个负样本：

$$
\text{banana},\text{car},\text{chair}
$$

于是得到 4 个 pair：

$$
(\text{deep},\text{learning}) \quad y=1
$$

$$
(\text{deep},\text{banana}) \quad y=0
$$

$$
(\text{deep},\text{car}) \quad y=0
$$

$$
(\text{deep},\text{chair}) \quad y=0
$$

然后，**每一对都独立做一次二分类**。

对于：

$$
(\text{deep},\text{learning})
$$

先算：

$$
s_1=u_{\text{learning}}^\top v_{\text{deep}}
$$

假设：

$$
s_1=2
$$

经过 sigmoid：

$$
\sigma(2)\approx0.88
$$

意思就是：

> 模型认为这对词有 88% 的可能是“真实共现词对”。

而：

$$
(\text{deep},\text{banana})
$$

假设：

$$
s_2=-1.5
$$

那么：

$$
\sigma(-1.5)\approx0.18
$$

意思就是：

> 模型认为这对只有 18% 的可能是真的。

训练希望：

$$
\boxed{
\text{正样本 sigmoid}\rightarrow1
}
$$

$$
\boxed{
\text{负样本 sigmoid}\rightarrow0
}
$$

所以：

$$
\text{deep-learning}:0.88
$$

很好；

$$
\text{deep-banana}:0.18
$$

也不错，因为它应该接近 0。

---

关键来了：为什么叫“独立二分类”？

因为这几个概率：

$$
0.88,\quad0.18,\quad0.12,\quad0.05
$$

**不要求加起来等于 1**。

每一对都在单独回答：

> “你是真的吗？”

所以可以同时出现：

$$
P(\text{deep,learning是真})=0.9
$$

$$
P(\text{deep,machine是真})=0.8
$$

完全没问题。

因为 deep 本来就可以同时和很多词构成真实上下文。

这就是：

$$
\boxed{\text{independent binary classification}}
$$

---

而 Softmax 完全不一样。

如果候选是：

$$
\{\text{learning},\text{banana},\text{car},\text{chair}\}
$$

softmax 是问：

> **这四个词里面，哪个是正确答案？**

所以会得到：

$$
P(\text{learning}\mid\text{deep})=0.75
$$

$$
P(\text{banana}\mid\text{deep})=0.10
$$

$$
P(\text{car}\mid\text{deep})=0.08
$$

$$
P(\text{chair}\mid\text{deep})=0.07
$$

并且：

$$
0.75+0.10+0.08+0.07=1
$$

它们是**互相竞争的**。

learning 的概率高了，其他几个的概率就会被压低。

---

所以你可以这样记：

$$
\boxed{
\text{Sigmoid / Negative Sampling：}
\text{这一对是真是假？}
}
$$

而：

$$
\boxed{
\text{Softmax：}
\text{这一群候选里面，哪个是真的？}
}
$$

这就是我上一条说的“每个负样本分别经过 sigmoid”的意思。

Word2Vec Negative Sampling 实际在做的是：

$$
\text{deep-learning}
\rightarrow \boxed{\text{真/假}}
$$

$$
\text{deep-banana}
\rightarrow \boxed{\text{真/假}}
$$

$$
\text{deep-car}
\rightarrow \boxed{\text{真/假}}
$$

各判各的。

而 CLIP / InfoNCE 更像：

$$
\text{一张图}
\rightarrow
\{\text{caption}_1,\text{caption}_2,\text{caption}_3,\dots\}
$$

然后问：

$$
\boxed{\text{这一堆 caption 里哪个和图片最匹配？}}
$$

所以两者都有“正样本拉近、负样本推远”的味道，但**分类方式不一样**：一个是很多独立的 yes/no，一个是一群候选一起竞争。

---

# chatgpt response

这页就是把我们刚才说的 **“正样本是真，负样本是假”** 正式写成 loss。

先抓住最核心的一件事：

> 对一个中心词 $c$，真实上下文词 $o$ 要判成 1；随机采样出来的 $k$ 个词，要判成 0。

---

假设中心词是：

$$
c=\text{deep}
$$

真实上下文：

$$
o=\text{learning}
$$

然后随机采 3 个负样本：

$$
\text{banana},\text{car},\text{table}
$$

于是：

$$
(\text{deep},\text{learning})\rightarrow y=1
$$

而：

$$
(\text{deep},\text{banana})\rightarrow y=0
$$

$$
(\text{deep},\text{car})\rightarrow y=0
$$

$$
(\text{deep},\text{table})\rightarrow y=0
$$

---

## 1. 先看正样本这一项

幻灯片里：

$$
-\log\sigma(u_o^Tv_c)
$$

这里：

$$
u_o^Tv_c
$$

就是中心词和真实上下文词的匹配分数。

例如：

$$
u_{\text{learning}}^Tv_{\text{deep}}=3
$$

那么：

$$
\sigma(3)\approx0.95
$$

sigmoid：

$$
\sigma(x)=\frac{1}{1+e^{-x}}
$$

会把任意实数映射到：

$$
(0,1)
$$

所以我们可以把：

$$
\sigma(u_o^Tv_c)
$$

理解成：

> “这个 pair 是真实 pair”的模型分数。

对正样本，我们希望：

$$
\sigma(u_o^Tv_c)\rightarrow1
$$

因此希望：

$$
u_o^Tv_c\rightarrow+\infty
$$

直觉上：

$$
\boxed{\text{正样本匹配分数变大}}
$$

也就是所谓“拉近”。

---

## 2. 为什么前面有个 $-\log$？

因为我们是在**最小化 loss**。

如果预测很好：

$$
\sigma(u_o^Tv_c)=0.99
$$

那么：

$$
-\log0.99\approx0.01
$$

loss 很小。

如果预测很差：

$$
\sigma(u_o^Tv_c)=0.01
$$

那么：

$$
-\log0.01\approx4.6
$$

loss 很大。

所以：

$$
\boxed{
-\log\sigma(u_o^Tv_c)
}
$$

就是在逼着正样本预测成 1。

---

# 3. 再看负样本这一项

幻灯片是：

$$
-\sum_k\log\sigma(-u_k^Tv_c)
$$

注意这里多了一个：

$$
-
$$

即：

$$
\sigma(-u_k^Tv_c)
$$

为什么？

因为对于负样本：

$$
(\text{deep},\text{banana})
$$

我们希望原始匹配分数：

$$
u_{\text{banana}}^Tv_{\text{deep}}
$$

变得很小、最好是很负。

比如：

$$
u_{\text{banana}}^Tv_{\text{deep}}=-3
$$

那么：

$$
-u_{\text{banana}}^Tv_{\text{deep}}=3
$$

于是：

$$
\sigma(3)\approx0.95
$$

loss：

$$
-\log0.95
$$

很小。

所以：

$$
\boxed{
\sigma(-u_k^Tv_c)
}
$$

实际上是在衡量：

> “这个 pair 是负样本”的正确程度。

---

可以把整个 loss 写成：

$$
\boxed{
J=
-\log\sigma(u_o^Tv_c)
-
\sum_{k=1}^{K}
\log\sigma(-u_k^Tv_c)
}
$$

含义就是：

$$
\boxed{
\text{正样本 score 大}
}
$$

同时：

$$
\boxed{
\text{负样本 score 小}
}
$$

---

# 4. 它为什么比 softmax 快？

Naive Softmax 对中心词 deep，需要和整个词表比较：

$$
u_1^Tv_c,\,
u_2^Tv_c,\,
\dots,\,
u_{|V|}^Tv_c
$$

如果：

$$
|V|=1,000,000
$$

就是 100 万次比较。

Negative Sampling 只看：

$$
1\text{ 个正样本}+K\text{ 个负样本}
$$

例如：

$$
K=5
$$

那么就只算 6 个点积。

所以：

$$
O(|V|d)
$$

变成：

$$
O(Kd)
$$

这就是它最大的意义。

---

# 5. 最后一行 $P(w)=U(w)^{3/4}/Z$ 是什么意思？

这个也很重要。

负样本不是简单“完全均匀随机抽”。

设：

$$
U(w)
$$

表示一个词在语料中的 unigram frequency，也就是出现频率。

比如：

- the：非常高频
- computer：中频
- aardvark：很低频

原始频率可能是：

$$
P(\text{the})=0.1
$$

$$
P(\text{computer})=0.001
$$

如果直接按照原始词频采负样本，那么：

> the、of、a、is

这种高频词会被抽爆。

所以 Word2Vec 用：

$$
\boxed{
P_{\text{neg}}(w)
=
\frac{U(w)^{3/4}}
{\sum_{w'}U(w')^{3/4}}
}
$$

关键就是这个：

$$
\frac34
$$

---

为什么是 $3/4$？

因为：

$$
0<x<1
$$

时：

$$
x^{3/4}>x
$$

而且小概率词提升得相对更多。

举个例子：

高频词：

$$
0.1^{0.75}\approx0.178
$$

低频词：

$$
0.0001^{0.75}=0.001
$$

原本两者比例：

$$
\frac{0.1}{0.0001}=1000
$$

经过 $3/4$ 次方：

$$
\frac{0.178}{0.001}\approx178
$$

所以高频词依然更容易被抽到，但优势没那么夸张。

也就是说：

$$
\boxed{
\text{压低超高频词的统治地位}
}
$$

同时：

$$
\boxed{
\text{让中低频词更有机会成为负样本}
}
$$

---

## 整页你可以压缩成一句话

Skip-gram + Negative Sampling：

$$
\boxed{
\text{真实 center-context pair}
\rightarrow \text{score 大}
}
$$

$$
\boxed{
\text{随机 noise pair}
\rightarrow \text{score 小}
}
$$

其 loss：

$$
\boxed{
-\log\sigma(\text{正样本分数})
-
\sum\log\sigma(-\text{负样本分数})
}
$$

所以你之前说“**有点像对比学习**”其实直觉是对的：这里已经非常明显了——**一个正样本，对若干负样本，通过表示空间里的匹配分数把它们区分开。** 🧠

---

# you asked

message time: 2026-09-04 10:01:54

负样本的数量K是超参数吗

---

# chatgpt response

对，**$K$ 就是超参数**。

它表示：

$$
\boxed{\text{每个正样本对应采多少个负样本}}
$$

比如真实 pair 是：

$$
(\text{deep},\text{learning})
$$

如果设：

$$
K=5
$$

那就额外采 5 个负样本，例如：

$$
(\text{deep},\text{banana})
$$

$$
(\text{deep},\text{car})
$$

$$
(\text{deep},\text{chair})
$$

$$
(\text{deep},\text{river})
$$

$$
(\text{deep},\text{apple})
$$

于是一个正样本会对应：

$$
1+K=6
$$

个 pair 参与 loss 计算。

---

$K$ 越大，模型每次看到的“错误候选”越多，通常区分能力会更充分，但计算量也更大：

$$
\text{complexity}\approx O(Kd)
$$

所以它是在 **效果和效率之间做权衡**。

经典 Word2Vec 里常见的 $K$ 大概是：

$$
5\sim20
$$

Mikolov 的原始实践中，小数据集可能会取更大的 $K$，大规模语料通常取较小的 $K$。

所以你可以直接记：

$$
\boxed{
K=\text{negative samples per positive pair}
}
$$

是一个需要人为设定的超参数。

---

# chatgpt response

这页其实是在提出一个非常自然的问题：

> **Word2Vec 为什么要一遍遍扫描语料、做预测、做梯度下降？既然我们真正关心的是“哪些词经常一起出现”，为什么不直接把共现次数统计出来？**

答案是：**可以，而且这就是 Word2Vec 之外另一大类经典词表示方法——count-based methods（基于计数的方法）。**

先看最直接的做法。假设词表里有：

$$
\{\text{dog},\text{cat},\text{eat},\text{car}\}
$$

我们统计每两个词在一定窗口内共同出现了多少次：

$$
X_{ij}
=
\text{word }i
\text{ 与 word }j
\text{ 的共现次数}
$$

就可以得到一个共现矩阵：

$$
X=
\begin{array}{c|cccc}
 & dog & cat & eat & car\\
\hline
dog & 0&80&60&2\\
cat &80&0&55&1\\
eat &60&55&0&10\\
car &2&1&10&0
\end{array}
$$

那么：

$$
X_{\text{dog},:}
=
[0,80,60,2]
$$

其实就已经是一种 **dog 的表示**。

而：

$$
X_{\text{cat},:}
=
[80,0,55,1]
$$

和 dog 的这一行很像。

所以：

$$
\boxed{
\text{上下文分布相似}
\Rightarrow
\text{共现向量相似}
}
$$

这和 Word2Vec 的核心思想其实是一样的。

---

## 这页说的第一个选择：Window-based co-occurrence

就和 Word2Vec 一样，定义一个局部窗口。

比如：

> I like **deep learning** very much

窗口：

$$
m=2
$$

那么对于 deep，就统计：

$$
\text{deep--I}
$$

$$
\text{deep--like}
$$

$$
\text{deep--learning}
$$

$$
\text{deep--very}
$$

每出现一次，相应矩阵元素：

$$
X_{ij}\leftarrow X_{ij}+1
$$

整个语料扫完以后，就得到了：

$$
X\in\mathbb R^{|V|\times |V|}
$$

或者更一般是：

$$
X\in\mathbb R^{|\text{word}|\times|\text{context}|}
$$

这种局部窗口会比较容易捕获：

$$
\boxed{\text{词法、句法、局部语义关系}}
$$

例如：

- dog 和 cat
- king 和 queen
- eat 和 food

所以 slide 里叫它：

> **word space**

---

# 第二种：Document-based

另一种思路不是看“附近几个词”，而是看：

> **某个词出现在哪些文档里。**

假设有 3 篇文章：

- $D_1$：足球
- $D_2$：篮球
- $D_3$：计算机

可以构造：

$$
X=
\begin{array}{c|ccc}
 &D_1&D_2&D_3\\
\hline
football&30&2&0\\
basketball&1&40&0\\
player&20&25&1\\
computer&0&0&50
\end{array}
$$

那么 football 和 basketball 虽然不一定经常紧挨着出现，但：

$$
[30,2,0]
$$

和

$$
[1,40,0]
$$

都集中出现在体育类文档。

所以这种矩阵更容易捕获：

$$
\boxed{\text{topic / document-level semantics}}
$$

比如：

- football
- basketball
- tennis
- player
- coach

都会因为经常出现在类似文档里而变得相关。

这就是 slide 里说的：

> general topics

也就是 **document space**。

---

# 那为什么不能直接把共现矩阵的一行当 embedding？

其实可以，但问题很大。

假设词表：

$$
|V|=100000
$$

那么每个词的表示就是：

$$
x_w\in\mathbb R^{100000}
$$

这就有三个明显问题。

第一，**维度特别高**：

$$
100000\text{维}
$$

而 Word2Vec 可能只需要：

$$
300\text{维}
$$

第二，**非常稀疏**。

一个词只和很少一部分词共同出现，因此可能是：

$$
[0,0,0,17,0,0,3,0,\dots]
$$

绝大多数都是 0。

第三，**原始次数受高频词影响太大**。

例如：

> the, of, is, a

几乎和什么词都会大量共现。

所以直接使用：

$$
X_{ij}
$$

并不一定是一个很好的语义表示。

---

## 怎么解决？

一个经典做法就是：

$$
\boxed{\text{构造共现矩阵}\rightarrow\text{降维}}
$$

例如 SVD：

$$
X=U\Sigma V^\top
$$

然后只保留最大的前 $d$ 个奇异值：

$$
X\approx
U_d\Sigma_dV_d^\top
$$

如果：

$$
d=300
$$

那么：

$$
U_d\Sigma_d
$$

就可以给每个词一个：

$$
300\text{维 dense vector}
$$

这就和 Word2Vec 最终得到的 embedding 很像了。

如果做的是 **word-document matrix + SVD**，就是经典的：

$$
\boxed{\text{Latent Semantic Analysis, LSA}}
$$

也就是你 slide 最后一行说的东西。

---

所以现在你可以看到，词向量历史上其实存在两条主要路线：

$$
\boxed{\text{Count-based}}
$$

直接统计：

$$
\text{word-context co-occurrence}
$$

然后：

$$
\text{PPMI / weighting}
\rightarrow
\text{SVD}
\rightarrow
\text{embedding}
$$

与：

$$
\boxed{\text{Prediction-based}}
$$

也就是 Word2Vec：

$$
\text{center word}
\rightarrow
\text{预测 context}
\rightarrow
\text{梯度下降}
\rightarrow
\text{embedding}
$$

---

更有意思的是，这两条路**并没有想象中那么不同**。

Count-based 方法说：

$$
\boxed{
\text{直接把上下文统计关系存进矩阵}
}
$$

Word2Vec 说：

$$
\boxed{
\text{通过预测上下文，间接把统计关系压缩进低维向量}
}
$$

它们都建立在同一个核心假设上：

$$
\boxed{
\text{You shall know a word by the company it keeps}
}
$$

也就是：

> **一个词的意义，可以从它和哪些词共同出现来推断。**

所以这页并不是在说“Word2Vec 有问题”，而是在为后面的 **co-occurrence matrix、SVD、LSA，以及很可能马上要讲到的 GloVe** 做铺垫。GloVe 正是试图把“全局共现统计”和“低维词向量学习”结合起来。

---

# you asked

message time: 2026-09-04 10:05:34

介绍下GloVe，这是在干什么

---

# chatgpt response

GloVe 可以理解成：**既然 Word2Vec 最终学到的是“哪些词经常一起出现”的统计规律，那我为什么不直接从全局共现统计出发，学习低维词向量？**

所以 GloVe 的全名是：

$$
\boxed{\text{Global Vectors for Word Representation}}
$$

它想做的事情就是：

> **把整个语料库的 word-word 共现矩阵，压缩成低维、稠密的词向量。**

这正好接上你上一页看到的“Why not capture co-occurrence counts directly?”。

---

假设我们先统计一个共现矩阵：

$$
X_{ij}
=
\text{word }j\text{ 出现在 word }i\text{ 附近的次数}
$$

例如：

$$
X=
\begin{array}{c|cccc}
 & ice & steam & water & fashion\\
\hline
solid &100&2&30&1\\
gas &1&90&25&0\\
\end{array}
$$

这里：

$$
X_{\text{solid},\text{ice}}
$$

很大，

而：

$$
X_{\text{solid},\text{steam}}
$$

很小。

说明：

$$
\text{solid}
$$

跟 ice 的关系比跟 steam 强很多。

GloVe 就希望：

> **词向量之间的点积，能够反映这种共现强度。**

---

更具体地说，GloVe 给每个词也学习两套向量：

$$
w_i
$$

和：

$$
\tilde w_j
$$

然后希望：

$$
w_i^\top \tilde w_j
$$

能够近似：

$$
\log X_{ij}
$$

所以核心关系可以先粗略记成：

$$
\boxed{
w_i^\top \tilde w_j
\approx
\log X_{ij}
}
$$

比如：

$$
X_{ij}=1000
$$

那么：

$$
\log X_{ij}\approx6.9
$$

如果：

$$
X_{ij}=2
$$

那么：

$$
\log X_{ij}\approx0.69
$$

于是高共现词对，希望点积大；低共现词对，希望点积小。

---

## 为什么要取 log？

因为原始共现次数差距太夸张。

例如：

$$
X_{ij}=1
$$

和：

$$
X_{kl}=100000
$$

差了 10 万倍。

但：

$$
\log1=0
$$

$$
\log100000\approx11.5
$$

这样就把巨大的频率差距压缩掉了，不至于让超高频词完全支配训练。

---

实际 GloVe 的 loss 是：

$$
\boxed{
J
=
\sum_{i,j}
f(X_{ij})
\left(
w_i^\top \tilde w_j
+
b_i+\tilde b_j
-
\log X_{ij}
\right)^2
}
$$

你可以先不要被公式吓到，它其实就一句话：

> **让词向量点积 + bias，尽量拟合 log 共现次数。**

其中：

$$
b_i,\tilde b_j
$$

是 bias。

而：

$$
f(X_{ij})
$$

是一个 weighting function。

它的作用是：

> 共现 1 次的数据可能只是噪声，不要太相信；共现很多次的数据更可信，但也不要让超级高频词权重无限大。

所以 GloVe 会给不同共现次数不同权重。

---

## GloVe 最核心的 insight 其实不只是“共现次数”

原论文里一个非常漂亮的想法是：

> **两个词与其他词的共现概率之比，比单独的共现概率更能表达语义关系。**

例如看：

$$
\text{ice}
$$

和：

$$
\text{steam}
$$

对于词：

$$
\text{solid}
$$

可能：

$$
P(\text{solid}\mid\text{ice})
$$

很大，

但：

$$
P(\text{solid}\mid\text{steam})
$$

很小。

所以比值：

$$
\frac{
P(\text{solid}\mid\text{ice})
}{
P(\text{solid}\mid\text{steam})
}
\gg1
$$

而对于：

$$
\text{gas}
$$

刚好反过来：

$$
\frac{
P(\text{gas}\mid\text{ice})
}{
P(\text{gas}\mid\text{steam})
}
\ll1
$$

但对于：

$$
\text{water}
$$

ice 和 steam 都有关系，所以：

$$
\frac{
P(\text{water}\mid\text{ice})
}{
P(\text{water}\mid\text{steam})
}
\approx1
$$

所以这种“ratio”非常容易表达：

> ice 和 steam 到底在哪些语义维度上不同。

GloVe 就是希望词向量空间把这种关系编码进去。

---

## 它和 Word2Vec 到底有什么区别？

你可以这样理解：

$$
\boxed{
\text{Word2Vec：边读语料边预测}
}
$$

比如：

$$
\text{deep}\rightarrow\text{learning}
$$

一个窗口一个窗口训练。

属于：

$$
\boxed{\text{prediction-based}}
$$

而 GloVe：

$$
\boxed{
\text{先统计整个语料的共现矩阵，再拟合这个矩阵}
}
$$

属于：

$$
\boxed{\text{count-based + embedding learning}}
$$

所以：

$$
\text{Word2Vec}
$$

更像：

> “我不断观察局部样本，然后通过预测任务学习统计规律。”

而：

$$
\text{GloVe}
$$

更像：

> “我先把全局统计规律汇总出来，然后直接学习一个低维表示来解释这些统计规律。”

---

但是最后得到的东西非常像：

$$
w_{\text{king}}\in\mathbb R^{300}
$$

$$
w_{\text{queen}}\in\mathbb R^{300}
$$

都可以做：

$$
\cos(w_{\text{king}},w_{\text{queen}})
$$

以及著名的：

$$
w_{\text{king}}
-
w_{\text{man}}
+
w_{\text{woman}}
\approx
w_{\text{queen}}
$$

---

你可以把这几代方法连起来看：

$$
\boxed{
\text{原始共现矩阵}
}
$$

问题：高维、稀疏。

于是：

$$
\downarrow
$$

$$
\boxed{
\text{LSA / SVD}
}
$$

直接对共现矩阵降维。

另一条路：

$$
\boxed{
\text{Word2Vec}
}
$$

不显式保存整个共现矩阵，通过预测上下文来学低维 embedding。

然后：

$$
\boxed{
\text{GloVe}
}
$$

某种程度上把两边结合：

> **利用全局共现统计，但不是简单 SVD，而是设计一个专门的目标函数直接学习词向量。**

所以 GloVe 其实可以理解成：

$$
\boxed{
\text{“共现统计” + “神经式低维 embedding 学习”}
}
$$

这也是为什么它叫 **Global Vectors**：Word2Vec 看起来更像从一个个局部窗口学习，而 GloVe 明确利用整个语料汇总出来的 **global co-occurrence statistics**。🧠

---

# you asked

message time: 2026-09-04 10:06:23

为什么后续GloVe方法发展不好

---

# chatgpt response

不是因为 GloVe “不好”，而是因为它所代表的整条 **静态词向量路线很快撞到了天花板**。GloVe 当年其实非常成功，问题在于后来的主战场从“给每个词学一个好向量”变成了“根据上下文动态地产生表示”。

最核心的原因有几个。

第一，GloVe 的最大限制是：

$$
\boxed{\text{一个词永远只有一个向量}}
$$

比如：

> I went to the **bank** to deposit money.

和：

> I sat on the **bank** of the river.

GloVe 都只能给：

$$
v_{\text{bank}}
$$

同一个向量。

它只能把“银行”和“河岸”两种含义平均揉在一起。

这不是 GloVe loss 调一调就能真正解决的问题，而是模型范式本身的问题：

$$
\boxed{
\text{static representation}
}
$$

而后来的 ELMo、BERT、GPT 直接变成：

$$
\boxed{
h_{\text{bank}}
=
f(\text{bank},\text{context})
}
$$

于是：

$$
h_{\text{bank}}^{\text{money}}
\neq
h_{\text{bank}}^{\text{river}}
$$

这一下就把表示能力提升了一个层级。

---

第二，GloVe 很擅长做“词级统计”，但不擅长**组合语义**。

它知道：

$$
v_{\text{king}}
$$

$$
v_{\text{queen}}
$$

是什么。

但如果输入：

> The movie was not good.

GloVe 本身并不能很好表达：

$$
\text{not good}
$$

和：

$$
\text{good}
$$

意义相反。

因为它主要解决的是：

$$
\boxed{
\text{word}\rightarrow\text{vector}
}
$$

而真正的 NLP 任务需要的是：

$$
\boxed{
\text{sentence / paragraph / document}
\rightarrow
\text{contextual representation}
}
$$

这一点 RNN、LSTM、Transformer 天然更强。

---

第三，GloVe 需要显式构造全局共现统计。

它先统计：

$$
X_{ij}
$$

也就是词 $i$ 和词 $j$ 的共现次数。

词表如果是：

$$
|V|=100000
$$

理论上的共现矩阵规模：

$$
100000\times100000
=
10^{10}
$$

当然实际会做稀疏存储，但工程上依然需要：

$$
\text{扫描语料}
\rightarrow
\text{构造共现统计}
\rightarrow
\text{存储稀疏矩阵}
\rightarrow
\text{训练 embedding}
$$

相比之下，Word2Vec 这种在线/流式训练：

$$
\text{text}
\rightarrow
\text{window samples}
\rightarrow
\text{SGD}
$$

工程上更自然。

不过这并不是 GloVe 被淘汰的最根本原因，因为大规模共现矩阵其实也完全能做。真正的问题还是**最终产物仍然只是 static embedding**。

---

第四，GloVe 的 global statistics 优势，后来被神经网络直接“吸收”了。

GloVe 当年的一个卖点是：

> Word2Vec 一个个局部窗口训练，看起来没有显式利用全局统计；GloVe 直接利用整个 corpus 的共现统计。

但后来人们逐渐发现：

即便一个神经模型是：

$$
\text{local prediction objective}
$$

只要：

- 数据足够大
- 模型容量足够大
- 训练次数足够多

它同样会把全局统计规律吸收到参数里。

比如 GPT 表面上的训练目标极其简单：

$$
P(x_t\mid x_{<t})
$$

只是预测下一个 token。

但它扫描万亿 token 后，参数本身就成了某种巨大的：

$$
\boxed{\text{compressed corpus statistics}}
$$

根本不需要显式构造一个：

$$
X_{ij}
$$

共现矩阵。

---

第五，也是最致命的一点：**下游任务开始要求端到端训练。**

GloVe 时代常见流程是：

$$
\text{GloVe}
\rightarrow
\text{固定 embedding}
\rightarrow
\text{LSTM/CNN}
\rightarrow
\text{classification}
$$

也就是说：

> 先单独把 word representation 学好，再拿去做任务。

而 BERT 以后：

$$
\text{token}
\rightarrow
\text{Transformer}
\rightarrow
\text{contextual representation}
\rightarrow
\text{task}
$$

整个表示系统可以：

$$
\boxed{\text{end-to-end optimize}}
$$

于是“单独设计一个完美的词向量”这件事本身就没那么重要了。

---

所以你可以把 NLP representation 的演化理解成：

$$
\text{One-hot}
$$

↓

$$
\text{Count / PPMI / LSA}
$$

↓

$$
\boxed{\text{Word2Vec / GloVe}}
$$

解决：

> 单词应该有一个有语义的低维向量。

然后：

$$
\text{ELMo / RNN contextual representation}
$$

↓

$$
\boxed{\text{BERT / Transformer}}
$$

问题升级成：

> **同一个 token 在当前上下文中应该是什么表示？**

最后 GPT/LLM 又进一步：

$$
\boxed{
\text{表示不再是最终目的，而是完成 next-token prediction 时自然产生的内部状态}
}
$$

---

所以我会说，GloVe 不是“后续发展不好”，而是：

$$
\boxed{
\text{它非常好地解决了上一代问题，
但下一代直接换了问题。}
}
$$

它要解决的是：

$$
\text{How to represent a word?}
$$

而 Transformer 时代问的是：

$$
\boxed{
\text{How to represent this token in this context?}
}
$$

后者严格包含了前者，因此 GloVe 很难再成为主干路线。

顺便说一句，**Word2Vec 其实也经历了完全一样的命运**。不是 GloVe 输给了 Word2Vec，而是：

$$
\boxed{
\text{Word2Vec + GloVe 这一整代 static embeddings}
\rightarrow
\text{被 contextual embeddings 取代}
}
$$

这才是历史主线。

---

# you asked

message time: 2026-09-04 10:08:51

讲一讲

---

# chatgpt response

可以。把这条线真正串起来以后，你会发现 **Word2Vec、RNN、Seq2Seq、Attention、Transformer 并不是一堆孤立的方法，它们其实是在不断回答同一个问题：**

> **“一个词/token 到底应该被表示成什么样的向量，才能包含我们当前真正需要的信息？”**

整条演化主线可以先记成：

$$
\boxed{
\text{one-hot}
\rightarrow
\text{static embedding}
\rightarrow
\text{contextual hidden state}
\rightarrow
\text{attention-based contextual representation}
\rightarrow
\text{Transformer representation}
}
$$

也就是：

$$
\boxed{
\text{One-hot}
\rightarrow
\text{Word2Vec/GloVe}
\rightarrow
\text{RNN/LSTM}
\rightarrow
\text{Seq2Seq + Attention}
\rightarrow
\text{Transformer}
}
$$

关键不是网络越来越复杂，而是 **“表征里包含的信息越来越丰富”**。

---

# 1. One-hot：我只知道“你是谁”

最早，一个词最直接的表示就是 one-hot。

假设词表：

$$
V=\{
\text{cat},
\text{dog},
\text{apple},
\text{king}
\}
$$

那么：

$$
\text{cat}
=
[1,0,0,0]
$$

$$
\text{dog}
=
[0,1,0,0]
$$

$$
\text{apple}
=
[0,0,1,0]
$$

它唯一表达的信息是：

> **这个词是词表中的哪一个 ID。**

所以 one-hot 是一种 representation，但它只有**身份信息**。

它没有：

$$
\text{cat}\approx\text{dog}
$$

这种概念。

因为任意两个不同 one-hot：

$$
x_i^\top x_j=0
$$

它们之间完全正交。

所以：

$$
\boxed{
\text{One-hot 表征的是 identity，而不是 semantics}
}
$$

---

# 2. Word2Vec：我不只知道“你是谁”，还知道“你通常意味着什么”

Word2Vec 解决的就是这个问题。

它把：

$$
x_w\in\mathbb R^{|V|}
$$

映射成：

$$
v_w\in\mathbb R^d
$$

例如：

$$
100000\text{维 one-hot}
\rightarrow
300\text{维 embedding}
$$

于是：

$$
v_{\text{cat}}
\approx
v_{\text{dog}}
$$

因为它们拥有相似上下文。

这里发生了一个非常大的变化：

$$
\boxed{
\text{离散 ID}
\rightarrow
\text{连续语义空间}
}
$$

词与词之间第一次有了可学习的几何关系。

所以：

$$
\text{cat}
$$

不再只是“词表编号 1287”，而变成一个带语义结构的向量：

$$
v_{\text{cat}}
=
[0.2,-0.7,\dots]
$$

这就是 **distributed representation**。

---

但 Word2Vec 有一个非常大的问题。

假设：

> I deposited money in the **bank**.

以及：

> I sat on the river **bank**.

Word2Vec 永远只有：

$$
v_{\text{bank}}
$$

一个向量。

也就是说：

$$
\boxed{
\text{bank 在所有上下文中的 representation 都一样}
}
$$

这叫：

$$
\boxed{\text{static representation}}
$$

它表征的是：

> bank 在整个语料库中的“平均意义”。

但语言中的真正含义是由上下文决定的。

于是下一代问题出现了：

> **能不能让一个词的表示依赖它前面出现了什么？**

---

# 3. RNN：一个词的表征开始包含“历史”

于是出现 RNN。

假设输入：

> I deposited money in the bank

Word embedding 先给每个词一个静态向量：

$$
x_t=v_{w_t}
$$

然后 RNN 递归：

$$
h_t=f(x_t,h_{t-1})
$$

例如：

$$
h_1=f(x_{\text{I}},h_0)
$$

$$
h_2=f(x_{\text{deposited}},h_1)
$$

$$
h_3=f(x_{\text{money}},h_2)
$$

一直到 bank：

$$
h_{\text{bank}}
=
f(x_{\text{bank}},h_{\text{money}})
$$

注意，这时候真正有意思的已经不是：

$$
x_{\text{bank}}
$$

而是：

$$
\boxed{h_{\text{bank}}}
$$

因为 $h_{\text{bank}}$ 包含：

$$
\text{bank 自己}
+
\text{前面的上下文}
$$

所以：

> deposited money in the **bank**

得到：

$$
h_{\text{bank}}^{(\text{money})}
$$

而：

> sat by the river **bank**

得到：

$$
h_{\text{bank}}^{(\text{river})}
$$

二者：

$$
\boxed{
h_{\text{bank}}^{(\text{money})}
\neq
h_{\text{bank}}^{(\text{river})}
}
$$

这就是一个巨大飞跃：

$$
\boxed{
\text{static word representation}
\rightarrow
\text{contextual representation}
}
$$

---

所以你现在可以这样区分：

Word2Vec：

$$
\text{bank}
\rightarrow
v_{\text{bank}}
$$

RNN：

$$
(\text{context},\text{bank})
\rightarrow
h_{\text{bank}}
$$

前者问：

> bank 通常是什么意思？

后者问：

> **bank 在当前这句话里是什么意思？**

---

# 4. Seq2Seq：既然 hidden state 能表示历史，那能不能表示整句话？

这就到了你之前问过的 Seq2Seq。

机器翻译例如：

> I love you

翻译：

> 我爱你

早期 Seq2Seq 的想法非常自然：

既然 RNN 的：

$$
h_t
$$

能不断总结历史，那么最后一个状态：

$$
h_T
$$

是不是可以把整句话的信息都压进去？

于是 encoder：

$$
x_1
\rightarrow
h_1
$$

$$
x_2,h_1
\rightarrow
h_2
$$

$$
\cdots
$$

$$
x_T,h_{T-1}
\rightarrow
h_T
$$

然后直接把：

$$
\boxed{h_T}
$$

作为整个输入句子的 representation。

所以：

$$
\boxed{
\text{整句话}
\rightarrow
\text{一个固定长度向量 }h_T
}
$$

Decoder 再根据这个向量生成翻译。

这就是早期 Seq2Seq 最关键的思想：

$$
\text{sequence}
\rightarrow
\boxed{context vector}
\rightarrow
\text{sequence}
$$

---

但马上遇到一个严重问题：

> 你让一个固定维度的向量 $h_T$，记住几十甚至上百个词的全部信息。

比如：

$$
h_T\in\mathbb R^{512}
$$

无论输入是：

> Hello

还是一本很长的句子，都要压成：

$$
512\text{维}
$$

这就是著名的：

$$
\boxed{\text{information bottleneck}}
$$

特别是长句的时候，前面的信息很容易丢。

---

# 5. Attention：为什么非要把所有东西塞进一个向量？

这就是 Attention 最关键的思想转折。

Attention 实际上是在问：

> **为什么 decoder 每一步都只能看最终的 $h_T$？为什么不能直接回头看 encoder 的所有 hidden states？**

Encoder 明明已经产生：

$$
h_1,h_2,\dots,h_T
$$

这些 hidden states 分别包含不同位置的信息。

比如：

> I ate an apple yesterday

可能：

$$
h_1
$$

更相关 I，

$$
h_4
$$

更相关 apple，

$$
h_5
$$

更相关 yesterday。

那 decoder 要生成“苹果”时，就重点看：

$$
h_4
$$

要生成“昨天”时，就重点看：

$$
h_5
$$

于是 Attention 做：

$$
e_{t,i}
=
\operatorname{score}(s_{t-1},h_i)
$$

然后：

$$
\alpha_{t,i}
=
\operatorname{softmax}(e_{t,i})
$$

最后：

$$
c_t
=
\sum_i
\alpha_{t,i}h_i
$$

这里：

$$
c_t
$$

就是 decoder 当前这一步所需的 context representation。

所以最大的思想变化是：

过去：

$$
\boxed{
\text{整个序列}
\rightarrow
\text{一个固定 representation}
}
$$

Attention：

$$
\boxed{
\text{整个序列}
\rightarrow
\text{一组 representations}
\rightarrow
\text{按当前需求动态组合}
}
$$

这是非常重要的。

---

你甚至可以把 Attention 理解成：

> **representation 不应该一次性提前决定，而应该根据“我现在要解决什么问题”动态构造。**

比如翻译一个句子时：

生成第一个词：

$$
c_1
=
\sum_i\alpha_{1i}h_i
$$

生成第二个词：

$$
c_2
=
\sum_i\alpha_{2i}h_i
$$

通常：

$$
c_1\neq c_2
$$

因为每一步需要的信息不同。

所以 attention 引入的是：

$$
\boxed{\text{query-dependent representation}}
$$

这也是后来 Transformer 的真正核心。

---

# 6. 但是这时候 Attention 还是依附在 RNN 上

早期 Attention 架构实际上还是：

$$
\boxed{
\text{RNN Encoder}
+
\text{Attention}
+
\text{RNN Decoder}
}
$$

也就是说：

$$
h_t=f(h_{t-1},x_t)
$$

这个 sequential recurrence 还存在。

于是有两个问题。

第一：

$$
h_t
$$

必须等：

$$
h_{t-1}
$$

算完。

所以不能充分并行：

$$
h_1\rightarrow h_2\rightarrow h_3\rightarrow\cdots
$$

第二，长距离依赖还是需要经过 RNN 链：

$$
x_1
\rightarrow
h_1
\rightarrow
h_2
\rightarrow
\cdots
\rightarrow
h_{100}
$$

即便有 Attention，encoder 内部的信息传播仍然是逐步的。

于是一个更加激进的问题出现：

> **既然 Attention 已经可以让任意两个位置直接交换信息，那 RNN 还有必要存在吗？**

---

# 7. Transformer：直接让所有 token 彼此看

这就是：

> **Attention Is All You Need**

真正的革命点。

Transformer 说：

$$
\boxed{
\text{不要 RNN recurrence 了}
}
$$

每一个 token 都直接和其他 token 做 attention。

假设：

> The animal didn't cross the street because it was tired.

对于 token：

$$
\text{it}
$$

Transformer 可以直接计算：

$$
Q_{\text{it}}K_{\text{animal}}^\top
$$

$$
Q_{\text{it}}K_{\text{street}}^\top
$$

$$
Q_{\text{it}}K_{\text{tired}}^\top
$$

等等。

然后：

$$
\operatorname{softmax}
$$

得到权重：

$$
\alpha_{\text{it},j}
$$

最后：

$$
h_{\text{it}}
=
\sum_j
\alpha_{\text{it},j}V_j
$$

于是 it 的新 representation 直接从整个句子里收集信息。

---

这和 RNN 有本质区别。

RNN：

$$
h_t
=
f(h_{t-1},x_t)
$$

也就是说：

$$
\boxed{
\text{通过前一个状态间接获得上下文}
}
$$

Transformer：

$$
h_t
=
\sum_j\alpha_{tj}V_j
$$

也就是说：

$$
\boxed{
\text{直接从所有 token 获取上下文}
}
$$

---

# 8. Transformer 中一个 token 的 representation 到底是什么？

这是你现在理解“表征”最关键的一步。

假设输入：

> I deposited money in the bank

最开始 bank 还是一个普通 embedding：

$$
x_{\text{bank}}
=
e_{\text{bank}}+p_{\text{bank}}
$$

这里包括：

$$
\text{token embedding}
+
\text{position embedding}
$$

此时它仍然基本是静态的。

经过第一层 Self-Attention：

$$
x_{\text{bank}}
\rightarrow
h_{\text{bank}}^{(1)}
$$

它可能开始融合：

- deposited
- money
- in

的信息。

第二层：

$$
h_{\text{bank}}^{(1)}
\rightarrow
h_{\text{bank}}^{(2)}
$$

再融合更复杂的关系。

一直：

$$
h_{\text{bank}}^{(L)}
$$

最后这个向量就不再只是“bank 的 embedding”。

而是：

$$
\boxed{
\text{bank 在这句话、这个位置、经过多层上下文交互后的 representation}
}
$$

所以 LLM 中我们常说 hidden representation：

$$
h_i^{(l)}
$$

其中：

- $i$：第几个 token
- $l$：第几层

它的含义是：

> 第 $l$ 层网络对第 $i$ 个 token 当前所理解的信息。

---

# 9. 用 bank 一下子串起来

这条历史线可以用同一个词看得特别清楚。

### One-hot

$$
\text{bank}
\rightarrow
[0,0,\dots,1,\dots]
$$

表达：

> “我是 bank。”

---

### Word2Vec

$$
\text{bank}
\rightarrow
v_{\text{bank}}
$$

表达：

> “根据整个语料来看，我通常与 money、river、finance 等概念有关。”

但所有上下文一样。

---

### RNN

$$
\text{money in the bank}
\rightarrow
h_{\text{bank}}
$$

表达：

> “我现在知道这里的 bank 很可能是金融机构。”

于是：

$$
h_{\text{bank}}^{money}
\neq
h_{\text{bank}}^{river}
$$

---

### Seq2Seq

整个：

$$
h_1,h_2,\dots,h_T
$$

最终被浓缩到：

$$
h_T
$$

表达：

> “用一个向量总结整句话。”

---

### Attention

不再只依赖：

$$
h_T
$$

而可以：

$$
c_t
=
\sum_i\alpha_{ti}h_i
$$

表达：

> “我现在需要哪个信息，就从对应位置取。”

---

### Transformer

甚至不需要先用 RNN 生成：

$$
h_1,h_2,\dots,h_T
$$

直接让所有 token：

$$
\boxed{
\text{彼此 attention}
}
$$

每个 token 都动态构建自己的上下文表示：

$$
h_i^{(l)}
=
f(
h_1^{(l-1)},\dots,h_n^{(l-1)}
)
$$

---

# 10. 所以“表征”真正经历了什么演化？

我觉得你可以记住下面这条，而不是死记模型名字：

$$
\boxed{
\text{身份}
\rightarrow
\text{静态语义}
\rightarrow
\text{上下文语义}
\rightarrow
\text{动态信息选择}
\rightarrow
\text{全局交互后的上下文表征}
}
$$

对应：

$$
\text{One-hot}
$$

只知道：

$$
\boxed{\text{Who am I?}}
$$

↓

Word2Vec / GloVe：

$$
\boxed{\text{What do I generally mean?}}
$$

↓

RNN：

$$
\boxed{\text{What do I mean given the history?}}
$$

↓

Attention：

$$
\boxed{\text{Which previous information matters right now?}}
$$

↓

Transformer：

$$
\boxed{\text{What should every token mean after interacting with every relevant token?}}
$$

---

而且这里有一个特别深的变化：

Word2Vec 时代我们认为：

$$
\boxed{
\text{一个词}
\rightarrow
\text{一个好的向量}
}
$$

是目标。

Transformer 时代则变成：

$$
\boxed{
\text{representation 是计算过程中的动态状态}
}
$$

一个 token 在：

$$
L=1,2,3,\dots,32
$$

不同层拥有：

$$
h_i^{(1)},
h_i^{(2)},\dots,h_i^{(32)}
$$

每一层都在重新回答：

> **“基于目前获得的信息，这个 token 现在应该如何被表示？”**

所以现代大语言模型里的“表征”已经不是一个固定 embedding，而是一条不断演化的轨迹：

$$
\boxed{
e_i
\rightarrow
h_i^{(1)}
\rightarrow
h_i^{(2)}
\rightarrow
\cdots
\rightarrow
h_i^{(L)}
}
$$

这其实就是从 Word2Vec 理解 Transformer 最关键的一座桥。🧠

你如果再往下一步学，我建议紧接着理解一个问题：**既然 Transformer 的 hidden state 本来已经是一个表征，为什么 Self-Attention 还要把它分别投影成 $Q,K,V$ 三套东西？** 这个问题一旦想通，Attention 的机制基本就彻底通了。

---

# you asked

message time: 2026-09-04 10:11:12

为什么

---

# chatgpt response

因为 **同一个 token 在 attention 里要同时扮演三种不同角色**，而这三种角色需要的信息并不完全一样，所以不能简单拿同一个 hidden state 直接做所有事情。

你可以把一个 token 当前的 hidden state 记成：

$$
h_i
$$

它包含的是这个 token 当前的综合表征。Self-Attention 不直接拿 $h_i$ 去做全部计算，而是分别投影成：

$$
q_i=W_Q h_i
$$

$$
k_i=W_K h_i
$$

$$
v_i=W_V h_i
$$

也就是：

$$
\boxed{
h_i
\rightarrow
Q,\ K,\ V
}
$$

关键在于，这三者回答的是三个不同问题。

---

### $Q$：我现在想找什么？

Query 表示：

> **当前这个 token 想从其他 token 那里寻找什么信息？**

比如句子：

> The animal didn't cross the street because **it** was tired.

对于 `it`：

$$
q_{\text{it}}
$$

可能包含一种需求：

> “我现在需要找到，我到底指代前面的哪个实体？”

所以 Query 更像：

$$
\boxed{\text{information need}}
$$

---

### $K$：我有什么信息值得别人找到？

每个其他 token 都有 Key：

$$
k_j
$$

比如：

- animal 有自己的 $k_{\text{animal}}$
- street 有自己的 $k_{\text{street}}$
- tired 有自己的 $k_{\text{tired}}$

Key 可以理解成：

> **“我的信息具有什么特征，别人什么时候应该关注我？”**

于是 `it` 会拿自己的 Query 去和所有 Key 比：

$$
q_{\text{it}}^\top k_{\text{animal}}
$$

$$
q_{\text{it}}^\top k_{\text{street}}
$$

如果：

$$
q_{\text{it}}^\top k_{\text{animal}}
>
q_{\text{it}}^\top k_{\text{street}}
$$

那就说明：

> `animal` 更符合 `it` 当前正在寻找的信息。

所以：

$$
\boxed{
QK^\top
=
\text{匹配需求和索引}
}
$$

---

### $V$：真正传给我的内容是什么？

注意，Key 只是用来**决定看谁**。

真正拿过来的信息是 Value：

$$
v_j
$$

所以：

$$
\alpha_{ij}
=
\operatorname{softmax}
\left(
\frac{q_i^\top k_j}{\sqrt{d_k}}
\right)
$$

决定：

> 我应该给第 $j$ 个 token 多大权重。

然后：

$$
o_i
=
\sum_j \alpha_{ij}v_j
$$

才真正把信息取回来。

所以：

$$
\boxed{
K=\text{用来匹配}
}
$$

$$
\boxed{
V=\text{真正传输的信息}
}
$$

---

## 为什么 Key 和 Value 还要分开？

这是最关键的地方。

你可以类比搜索引擎。

假设一篇文章里面有：

> 标题：Transformer Tutorial  
> 内容：一整篇 Transformer 介绍

搜索时，你可能根据：

$$
\boxed{\text{标题 / 标签}}
$$

判断这篇文章是否相关。

但真正点进去以后，你读取的是：

$$
\boxed{\text{文章内容}}
$$

所以：

$$
K \approx \text{索引/标签}
$$

$$
V \approx \text{内容}
$$

你不会要求：

> “用来检索我的东西”和“真正返回给你的内容”必须完全一样。

Attention 也是一样。

一个 token 某些维度可能非常适合**判断相关性**，但真正应该传给其他 token 的信息可能是另一部分。

---

# 为什么不能直接用 $h_i$？

假设不用 QKV，直接：

$$
\alpha_{ij}
=
\operatorname{softmax}(h_i^\top h_j)
$$

再：

$$
o_i=\sum_j\alpha_{ij}h_j
$$

数学上当然可以。

但这相当于强迫：

$$
\boxed{
\text{用来查询的信息}
=
\text{用来匹配的信息}
=
\text{实际传输的信息}
}
$$

这限制太强了。

而有了：

$$
W_Q,\ W_K,\ W_V
$$

模型就可以自己学习：

> hidden state 的哪些方向适合用来“问问题”？

> 哪些方向适合用来“被检索”？

> 哪些方向是真正应该传递的内容？

于是：

$$
h_i
$$

虽然是同一个基础 representation，但经过不同投影后承担不同功能。

---

## 举一个特别直观的例子

假设一个 hidden state 为了直觉，可以想成里面混着：

$$
h_{\text{animal}}
=
[
\text{名词信息},
\text{单复数},
\text{语义类别},
\text{情感},
\text{句法角色},
\dots
]
$$

现在 `it` 想解决指代问题。

那么 $W_Q,W_K$ 可能更关注：

$$
\text{名词性、单复数、句法位置、实体信息}
$$

所以：

$$
q_{\text{it}}^\top k_{\text{animal}}
$$

很高。

但真正把 animal 的信息传给 `it` 时，$W_V$ 可能提取：

$$
\text{animal 的语义内容}
$$

所以：

$$
v_{\text{animal}}
$$

和：

$$
k_{\text{animal}}
$$

不必一样。

这就是 Q/K/V 分开的意义。

---

## 还有一个更深的原因：它允许学习“非对称关系”

如果直接用：

$$
h_i^\top h_j
$$

那么：

$$
h_i^\top h_j=h_j^\top h_i
$$

这是对称的。

也就是说：

> $i$ 对 $j$ 的相关性

和：

> $j$ 对 $i$ 的相关性

完全一样。

但语言关系经常不是这样的。

用了：

$$
q_i^\top k_j
=
(W_Qh_i)^\top(W_Kh_j)
$$

以后，一般：

$$
q_i^\top k_j
\neq
q_j^\top k_i
$$

于是模型可以表达：

> `it` 很需要从 `animal` 获取信息，

但并不意味着：

> `animal` 同样程度需要从 `it` 获取信息。

这个能力非常重要。

---

所以你可以把 QKV 一句话记住：

$$
\boxed{
Q:\text{我需要什么}
}
$$

$$
\boxed{
K:\text{我能不能满足你的需求}
}
$$

$$
\boxed{
V:\text{如果你选中我，我真正给你什么}
}
$$

然后 Attention：

$$
\underbrace{QK^\top}_{\text{决定看谁}}
\rightarrow
\operatorname{softmax}
\rightarrow
\underbrace{V}_{\text{取什么内容}}
$$

也就是：

$$
\boxed{
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}
\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)V
}
$$

这也是为什么 Transformer 不直接把 hidden state 彼此做相似度然后相加，而要额外学习 $W_Q,W_K,W_V$：**它是在把“表征是什么”与“当前如何使用这个表征”分离开。** 🧠

---

# you asked

message time: 2026-09-04 10:12:20

Transformer为什么需要很多层

---

# chatgpt response

因为 **一层 Self-Attention 虽然可以让每个 token 一次性“看到”所有 token，但“看到所有信息”不等于“已经把复杂关系算出来了”**。

这是理解 Transformer 为什么需要深层的关键。

设第 $l$ 层某个 token 的表示为：

$$
h_i^{(l)}
$$

一层 Transformer 本质上是在做：

$$
h_i^{(l)}
\rightarrow
h_i^{(l+1)}
$$

也就是：

> 根据当前所有 token 的表示，重新计算一次这个 token 的表示。

多层就是不断重复这个过程：

$$
h_i^{(0)}
\rightarrow
h_i^{(1)}
\rightarrow
h_i^{(2)}
\rightarrow
\cdots
\rightarrow
h_i^{(L)}
$$

每一层都在前一层已经加工过的信息上继续计算。🧠

---

### 一个很重要的误区

你可能会想：

> Self-Attention 一层不就已经能让第一个词直接看到最后一个词了吗？为什么还需要 32 层、80 层？

确实，一层 Attention 就可以建立：

$$
\text{token}_1
\leftrightarrow
\text{token}_{1000}
$$

所以 Transformer 多层的主要原因**不是为了传播距离更远**。

RNN 里：

$$
x_1\rightarrow h_1\rightarrow h_2\rightarrow\cdots\rightarrow h_{100}
$$

长距离信息确实需要很多步。

但 Transformer 一层就可以全局通信。

它需要很多层，是为了：

$$
\boxed{\text{进行多步计算，而不是多步传递}}
$$

---

## 举个例子

比如：

> The animal didn't cross the street because it was too tired.

模型要理解 `it` 指的是 `animal`。

第一层可能首先形成一些基础表示：

$$
h_{\text{animal}}^{(1)}
$$

包含：

- animal 是名词
- 是一个实体
- 单数

同时：

$$
h_{\text{it}}^{(1)}
$$

包含：

- it 是代词
- 单数
- 可能指代某个实体

第二层可以利用这些已经加工后的表示，建立：

$$
\text{it}
\leftrightarrow
\text{animal}
$$

的指代关系。

于是：

$$
h_{\text{it}}^{(2)}
$$

可能已经融合了：

> it = animal

的信息。

然后第三层再利用这个新表示理解：

> “谁 tired？”

因为现在 `it` 的表示已经含有 animal 信息：

$$
h_{\text{it}}^{(2)}
$$

下一层就可以进一步把：

$$
\text{tired}
$$

和：

$$
\text{animal}
$$

联系起来。

也就是说：

$$
\boxed{
\text{第一步识别对象}
\rightarrow
\text{第二步建立关系}
\rightarrow
\text{第三步利用关系继续推理}
}
$$

这就是“深度”的价值。

---

# 一层 Attention 有什么限制？

Attention 的核心：

$$
\operatorname{softmax}(QK^\top)V
$$

本质是：

> 根据当前 representation 决定从哪些 token 取信息，然后做加权组合。

问题是：

$$
Q,K,V
$$

都是从**当前层输入的 $h^{(l)}$** 产生的。

所以这一层只能根据：

$$
h^{(l)}
$$

当前已经知道的东西来决定 attention。

但如果某个复杂关系本身需要先计算出来呢？

那就必须：

第一层：

$$
h^{(0)}
\rightarrow h^{(1)}
$$

先发现某种关系。

第二层再基于：

$$
h^{(1)}
$$

重新计算：

$$
Q^{(2)},K^{(2)},V^{(2)}
$$

于是第二层的 Attention 可以做出第一层做不到的判断。

所以：

$$
\boxed{
\text{后一层的 Attention，
是在前一层理解结果的基础上重新搜索信息}
}
$$

这是非常重要的。

---

## 可以把它想成多轮读文章

假设给你一篇论文。

第一遍：

> 哪些概念出现了？

第二遍：

> 哪些概念之间有关系？

第三遍：

> 哪个结论依赖哪个假设？

第四遍：

> 作者的 main claim 是否成立？

虽然你每一遍都能看到**整篇论文**，但第一遍看到全部文字，不代表第一遍就已经完成所有推理。

Transformer 的多层有点类似：

$$
\boxed{
\text{每层都能看全局，
但每层只完成一次新的信息加工}
}
$$

---

# MLP 也非常重要

Transformer layer 并不只是 Attention。

通常是：

$$
\boxed{
\text{Attention}
\rightarrow
\text{MLP}
}
$$

可以粗略理解成：

Attention：

$$
\boxed{\text{从哪里获取信息？}}
$$

MLP：

$$
\boxed{\text{拿到信息之后怎么加工？}}
$$

然后下一层再次：

$$
\text{Attention}
\rightarrow
\text{MLP}
$$

于是形成：

$$
\text{获取信息}
\rightarrow
\text{加工信息}
\rightarrow
\text{再次获取}
\rightarrow
\text{再次加工}
\rightarrow\cdots
$$

这才形成复杂计算。

---

## 比如做一道推理题

假设：

> Alice is Bob's mother.  
> Bob is Charlie's father.  
> Who is Alice to Charlie?

需要两步关系组合：

$$
Alice\xrightarrow{mother}Bob
$$

以及：

$$
Bob\xrightarrow{father}Charlie
$$

然后组合：

$$
Alice\rightarrow Bob\rightarrow Charlie
$$

得到：

$$
Alice=\text{Charlie's grandmother}
$$

即使一层 Attention 能看到 Alice、Bob、Charlie 全部，它仍然需要完成：

$$
\boxed{\text{关系提取}\rightarrow\text{关系组合}}
$$

这种多步计算。

多层非常适合实现这种：

$$
\text{intermediate representation}
$$

第一层可能得到：

$$
R_1=(Alice,mother,Bob)
$$

第二层得到：

$$
R_2=(Bob,father,Charlie)
$$

再进一步组合。

当然真实 Transformer 并不会如此整齐地“一层一个逻辑步骤”，但这个直觉是对的。

---

# 从“表征”的角度看更加漂亮

你前面一路问的其实正好连到这里。

Word2Vec：

$$
\boxed{
w\rightarrow v_w
}
$$

一个词一个固定 representation。

Transformer 第 0 层：

$$
h_i^{(0)}
$$

还是比较接近 token embedding。

经过一层：

$$
h_i^{(1)}
$$

开始包含上下文。

再经过：

$$
h_i^{(2)}
$$

已经是“上下文化后的上下文”。

再经过：

$$
h_i^{(3)}
$$

又是在前面的关系基础上继续加工。

所以：

$$
\boxed{
h_i^{(0)}
\rightarrow
h_i^{(1)}
\rightarrow
h_i^{(2)}
\rightarrow
\cdots
\rightarrow
h_i^{(L)}
}
$$

可以理解成：

> **同一个 token 的 representation 被不断重写、丰富和抽象。**

---

比如 `bank`：

第 0 层：

$$
h_{\text{bank}}^{(0)}
$$

大概是静态的“bank”概念。

看到：

> deposited money in the bank

之后，第几层开始融入 money/deposited 的信息。

再往后可能形成：

$$
\text{bank = financial institution}
$$

更深层还可以形成：

> 这个 bank 在当前句子中是某个事件里的地点/对象。

所以 representation 从：

$$
\boxed{\text{词是什么}}
$$

逐渐变成：

$$
\boxed{\text{这个词在当前整个问题中的作用是什么}}
$$

---

不过要小心一个常见说法：

> “第一层学词法，第二层学句法，第三层学语义……”

不能这么机械理解。

真实大模型中，各层的信息是高度分布式和混合的，不存在如此干净的一层一功能。

更准确地说：

$$
\boxed{
\text{随着深度增加，模型获得更多连续计算步骤，
可以形成越来越复杂的中间表示。}
}
$$

---

所以如果让我用一句话回答：

> **Transformer 为什么需要很多层？**

就是：

$$
\boxed{
\text{Attention 解决“信息可以直接从哪里来”，
深度解决“这些信息需要经过多少步计算才能变成答案”。}
}
$$

一层 Self-Attention 已经解决了：

$$
\boxed{\text{全局通信}}
$$

但多层 Transformer 提供的是：

$$
\boxed{\text{迭代表示更新 + 多步组合计算}}
$$

这也是为什么“大模型更深”并不是单纯为了让 token 看得更远——**它是在增加模型的计算深度**。