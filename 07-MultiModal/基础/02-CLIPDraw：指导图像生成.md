这篇 **CLIPDraw** 很适合用来理解“CLIP 如何指导生成”。关键点是：

$$
\boxed{\text{CLIP 本身不生成图像，它充当一个可微分的语义评分器}}
$$

也就是说，CLIP 告诉生成过程：

> “你现在画出来的东西，和用户输入的文字像不像？”

然后利用这个“像不像”的分数反向传播，直接修改正在生成的图像。CLIPDraw 本身甚至不需要再训练一个生成模型。

### 1. 先回忆一下 CLIP 做什么

CLIP 有两个 encoder：

$$
\text{text}\xrightarrow{E_T}z_t
$$

$$
\text{image}\xrightarrow{E_I}z_i
$$

例如输入：

> “a red apple”

得到文本 embedding：

$$
z_t=E_T(\text{``a red apple''})
$$

一张图片 $I$ 得到：

$$
z_i=E_I(I)
$$

然后比较 cosine similarity：

$$
s(I,T)
=
\frac{z_i^\top z_t}
{\|z_i\|\|z_t\|}
$$

如果图片真的是红苹果，这个 similarity 通常比较高。

所以 CLIP 已经给了我们一个非常有用的函数：

$$
\boxed{
f(I,T)=\text{“图片 }I\text{ 和文字 }T\text{ 有多匹配”}
}
$$

它原本用于图文匹配、zero-shot classification，但现在可以反过来利用。

---

## 2. CLIPDraw 的核心想法：那我直接“优化图片”不就行了吗？

假设我们想画：

> “a red apple”

先随机放一些线条：

$$
\theta_0
$$

这里 $\theta$ 不是神经网络参数，而是**画笔参数**。

CLIPDraw 使用一组 RGBA Bézier curves，也就是很多可微分的矢量曲线；$\theta$ 可以包含曲线控制点、位置、颜色、透明度等。论文通过 differentiable renderer 把这些曲线渲染成图片。

所以：

$$
\theta
\xrightarrow{\text{renderer}}
I_\theta
$$

然后：

$$
I_\theta
\xrightarrow{E_I}
z_i
$$

文字则：

$$
T
\xrightarrow{E_T}
z_t
$$

接下来定义 loss：

$$
\boxed{
\mathcal L(\theta)
=
1-\cos(E_I(I_\theta),E_T(T))
}
$$

如果当前画出来的东西跟 “red apple” 完全不像：

$$
\cos(\cdot)\downarrow
$$

于是：

$$
\mathcal L\uparrow
$$

然后最有意思的地方来了。

---

## 3. 直接反向传播到“画笔”

因为整个路径都是可微的：

$$
\theta
\rightarrow
I_\theta
\rightarrow
E_I(I_\theta)
\rightarrow
\mathcal L
$$

所以可以直接计算：

$$
\frac{\partial\mathcal L}{\partial\theta}
$$

然后梯度下降：

$$
\boxed{
\theta
\leftarrow
\theta-\eta
\frac{\partial\mathcal L}{\partial\theta}
}
$$

注意这里**不是更新 CLIP**。

CLIP：

$$
\boxed{\textcolor{blue}{\text{Frozen}}}
$$

被更新的是：

$$
\boxed{\text{Bezier 曲线的参数}}
$$

于是就出现：

$$
\text{随机线条}
\rightarrow
\text{稍微像苹果}
\rightarrow
\text{越来越像苹果}
\rightarrow
\text{CLIP 认为非常像“red apple”}
$$

整个过程本质上就是：

$$
\boxed{
\underset{\theta}{\arg\max}
\;
\operatorname{sim}
\left(
E_I(R(\theta)),
E_T(T)
\right)
}
$$

其中 $R$ 就是 renderer。

---

# 4. 这其实是一个非常漂亮的“反用 CLIP”

你之前一直在理解：

> CLIP 训练时不是在做“正确图文拉近，错误图文推远”吗？

没错。

训练 CLIP 时：

$$
\text{image,text}
\rightarrow
\text{调整 }E_I,E_T
$$

让正确图文：

$$
\cos(E_I(I),E_T(T))\uparrow
$$

但 CLIPDraw 时，CLIP 已经训练完了。

所以现在固定：

$$
E_I,E_T
$$

反过来调整：

$$
I
$$

于是：

$$
\boxed{
\text{CLIP training: 调模型，使 embedding 对齐}
}
$$

而：

$$
\boxed{
\text{CLIP-guided generation: 固定模型，调输入，使 embedding 对齐}
}
$$

这两个过程其实是镜像关系。

---

## 5. 可以把 CLIP 看成一个“语义损失函数”

传统图像生成很难直接定义：

> “这张图片有多像一只戴帽子的猫？”

因为像素 MSE 完全没法表达这种语义。

例如：

$$
\mathcal L_\text{pixel}
=
\|I-I^*\|^2
$$

要求有 target image $I^*$。

但 CLIP 给了你：

$$
\mathcal L_{\text{semantic}}
=
1-\cos(E_I(I),E_T(T))
$$

不需要目标图片。

只需要一句：

> “a cat wearing a hat”

就有一个优化目标。

这件事情非常重要：

$$
\boxed{
\text{Natural language}
\rightarrow
\text{Differentiable semantic objective}
}
$$

可以把 CLIP 理解为把一句自然语言“编译”成了一个可以优化的 objective。

---

# 6. 为什么不能直接优化每个 pixel？

理论上当然可以：

$$
I\in\mathbb R^{H\times W\times 3}
$$

直接：

$$
I
\leftarrow
I-\eta
\frac{\partial\mathcal L}{\partial I}
$$

但是很容易产生一种东西：

> CLIP 觉得非常像，  
> 人却看不懂。

也就是典型的 adversarial / feature exploitation。

因此 CLIPDraw 加了两个非常重要的 inductive bias。

第一，它不直接优化 pixels，而优化少量的 **vector strokes**：

$$
\theta
=
\{\text{Bezier curves}\}
$$

这样生成空间天然偏向：

$$
\text{线条、轮廓、简单结构}
$$

而不是奇怪的高频噪声。论文也明确把 vector-stroke representation 视为促使结果变得更简单、更容易被人识别的约束。

第二，它会对当前绘图做随机 crop、perspective 等数据增强，然后要求多个增强版本都与文本匹配：

$$
I_\theta
\rightarrow
A _1(I_\theta),A _2(I_\theta),\dots,A_D(I_\theta)
$$

loss 类似：

$$
\mathcal L
=
\frac 1 D
\sum_{d=1}^D
\left[
1-
\cos
\left(
E_I(A_d(I_\theta)),
E_T(T)
\right)
\right]
$$

目的就是避免只找到一个 CLIP 的“作弊解”；论文特别指出 augmentation 可以降低优化产生人类不可识别 adversarial image 的问题。

---

# 7. 所以整个 CLIPDraw 可以压成这一张逻辑图

```text
            "a red apple"
                  │
                  ▼
          CLIP Text Encoder
                  │
                  ▼
             Text embedding
                  │
                  │
                  │ cosine similarity
                  │
                  ▼
Random strokes → Renderer → Image → CLIP Image Encoder
     ▲                                      │
     │                                      │
     └──────────── gradient ────────────────┘
```

反复循环：

$$
\boxed{
\text{画}
\rightarrow
\text{CLIP 看}
\rightarrow
\text{发现不像}
\rightarrow
\text{梯度告诉你往哪里改}
\rightarrow
\text{继续画}
}
$$

所以你完全可以把它想成：

$$
\boxed{
\text{CLIP = 一个懂自然语言的“美术老师”}
}
$$

但更准确地说：

$$
\boxed{
\text{CLIP = differentiable semantic critic / reward}
}
$$

---

## 8. 这和今天 Diffusion 中的 guidance 有什么关系？

这个思想非常关键，因为它代表了一类更一般的方法：

$$
\boxed{
\text{Generator}+\text{Frozen semantic model}+\text{Gradient guidance}
}
$$

CLIPDraw 的 generator 极其简单：

$$
\theta=\text{Bezier strokes}
$$

后来可以变成：

$$
\theta=\text{GAN latent}
$$

或者：

$$
\theta=\text{diffusion latent/noisy image}
$$

CLIP 负责：

$$
\text{“方向对不对？”}
$$

真正负责产生图片的是另外的生成机制。

因此一定不要形成这个心智模型：

$$
\text{Text}\rightarrow\boxed{\text{CLIP}}\rightarrow\text{Image}
$$

这是错的。

正确的是：

$$
\boxed{
\begin{array}{c}
\text{Generator produces candidate}\\
\downarrow\\
\text{CLIP evaluates semantic match}\\
\downarrow\\
\text{gradient guides generator}\\
\downarrow\\
\text{better candidate}
\end{array}}
$$

这也是为什么 **CLIP 是 encoder-only 模型，明明没有 decoder，却仍然能够“指导生成”**：它根本不需要学会“怎么画”，只需要学会一个很好的语义空间，然后把这个语义空间变成 loss/reward 即可。🌚

而且这恰好把你前面讨论的 **Representation** 补全了一块：

$$
\boxed{
\text{好的 representation 不仅可以用来分类，
还可以直接定义一个优化空间。}
}
$$

CLIP 真正强大的地方之一，就是它学到的 joint vision-language representation 后来可以拿来当 **classifier、retrieval metric、reward、guidance signal、semantic loss**。这比“CLIP 是一个图文分类器”这个理解要深一层。
