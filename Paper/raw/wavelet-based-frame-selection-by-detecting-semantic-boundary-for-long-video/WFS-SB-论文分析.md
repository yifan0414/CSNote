> From: https://chatgpt.com/g/g-69d10e462cc081919fff4a3d0c786ca5-di-yi-xing-lun-wen-fen-xi-shi/c/6a1639a2-3504-83a5-8fca-bd35777e37e5

# you asked

message time: 2026-05-27 08:24:02

https://arxiv.org/abs/2603.00512

---

# chatgpt response

我会先抓取 arXiv 页面和 PDF，确认论文题目、任务、方法与实验，再按“Task/Challenge/Insight/Flaw/Motivation”的第一性框架拆解。

# 论文分析：WFS-SB — Wavelet-based Frame Selection by Detecting Semantic Boundary for Long Video Understanding

论文核心问题：**长视频不能全帧喂给 LVLM，如何在固定帧预算下选出最有利于回答问题的帧？** 作者提出的答案不是“选最相关帧”，而是“先找语义章节边界，再在每个章节里选代表帧”。论文已被 CVPR 2026 接收。([arXiv](https://arxiv.org/abs/2603.00512))

---

## 1. Task：从第一性原理形式化任务

给定：

- 视频：  
  $$
  V=\{x_1,x_2,\dots,x_T\}
  $$
- 用户问题 / 查询：  
  $$
  q
  $$
- LVLM 可接受的最大帧数预算：  
  $$
  K \ll T
  $$

目标是选择一个按时间排序的帧子集：

$$
F=\{f_1,\dots,f_K\}
$$

使得 LVLM 在输入 $(F,q)$ 后，对视频问答任务给出尽可能正确、信息充分的答案。论文实际操作中，先以 1 FPS 对视频采样得到 $N$ 个候选帧，再用 BLIP-2 ITM head 计算每帧和查询的匹配分数：

$$
s_t=M(q,f_t), \quad t=1,\dots,N
$$

这些分数被视为一个随时间变化的 **temporal relevance signal**，后续所有选择都基于这个信号展开。([arXiv](https://arxiv.org/pdf/2603.00512))

这个任务本质上是：

> **query-conditioned、training-free、budgeted temporal subset selection under LVLM context constraint**

更抽象地说，它是一个 **信息瓶颈问题**：

$$
\text{Long video} \rightarrow \text{K frames} \rightarrow \text{answer}
$$

选择器要在强压缩下保留对问题有用的视觉证据。

---

## 2. Challenge：为什么传统方法不够？

### 2.1 表面问题：帧太多，上下文太短

长视频存在大量冗余帧，而 LVLM 的视觉上下文窗口和算力预算有限，直接处理所有帧不可行。因此必须做关键帧选择。作者认为，相比扩展上下文、视频转文本摘要、视觉 token 压缩，frame selection 是更轻量、直接的前处理策略。([arXiv](https://arxiv.org/pdf/2603.00512))

### 2.2 传统范式：把帧当作 IID 检索对象

很多方法隐含假设是：

$$
\text{good frame} = \text{high query relevance frame}
$$

于是直接选 top-K 相关帧，或在相关性和覆盖度之间做优化。

问题是：视频不是图片集合，而是一个时间过程。单帧相关性高，不代表它在故事结构中重要。比如“眼妆过程”里，许多帧都包含眼睛，但只选这些高相关帧会错过“画眼线 → 修眉 → 涂睫毛”等步骤关系。论文图 1 正是用这个例子说明：top relevance 会得到相关但割裂的帧，WFS-SB 则试图得到相关且连贯的片段覆盖。([arXiv](https://arxiv.org/pdf/2603.00512))

### 2.3 本质问题：需要保留的是“状态转移”，不是静态相关性

对长视频理解而言，尤其是过程、因果、顺序、事件发展类问题，真正关键的是：

$$
\text{what changed? when did it change?}
$$

而不是：

$$
\text{which frames look most similar to the query?}
$$

因此，帧选择的基本单位不应该是孤立帧，而应该是：

$$
\text{semantic segment / narrative chapter}
$$

作者的关键转向是：**先检测语义边界，再在语义段内选帧**。([arXiv](https://arxiv.org/pdf/2603.00512))

### 2.4 为什么不能直接用梯度或阈值找边界？

query-frame relevance signal 有三个性质：

1. **非平稳**：不同时间段的分布会变化；
2. **多尺度**：短动作可能持续几帧，长过程可能持续几百帧；
3. **低信噪比**：VLM 不确定性、跨模态歧义、光照、遮挡、相机运动都会导致分数抖动。

因此，直接对原始 $s_t$ 做局部极值、梯度、阈值检测会把噪声误判为语义变化。作者明确把这个问题重构为信号处理问题。([arXiv](https://arxiv.org/pdf/2603.00512))

---

## 3. Insight & Novelty：真正的新想法是什么？

### 创新 1：把 query-frame relevance 从“打分列表”改写成“时间信号”

**要解决的问题**：  
传统方法把每帧的相关性分数 $s_t$ 当作独立样本，导致 top-K 选择忽略时间结构。

**Insight**：  
如果把 $\{s_t\}_{t=1}^N$ 看成一个随时间变化的信号，那么语义章节变化会表现为 relevance signal 的低频 / 粗尺度结构变化，而不是单点高分。

**具体设计**：  
用 BLIP-2 ITM 得到每帧与 query 的相关性分数，形成 temporal relevance signal：

$$
s_1,s_2,\dots,s_N
$$

再对它做多层离散小波变换：

$$
DWT(s_t)=\{a_J,d_J,d_{J-1},\dots,d_1\}
$$

其中分解层数自适应设为：

$$
J=\max(1,\lfloor \log_2 N \rfloor-l)
$$

论文默认 $l=3$，小波基用 Daubechies-4。([arXiv](https://arxiv.org/pdf/2603.00512))

**为什么有效**：  
小波变换同时保留时间位置和频率尺度。高频细节 $d_1,d_2$ 更容易包含局部噪声，最粗尺度细节 $d_J$ 更可能对应宏观语义变化。因此作者只保留 $d_J$，其余系数置零，再通过 IDWT 重构出语义变化信号：

$$
\tilde{s}_t=IDWT(\{0,d_J,0,\dots,0\})
$$

然后定义变化强度：

$$
c_t=|\tilde{s}_t|
$$

局部峰值被视为语义边界。([arXiv](https://arxiv.org/pdf/2603.00512))

**我的判断**：  
这一步是全文真正的核心。它不是简单“用小波做平滑”，而是把帧选择的对象从 **relevance maxima** 变成了 **semantic change maxima**。换句话说，作者不再问“哪里最像问题”，而是问“哪里发生了和问题相关的状态变化”。

---

### 创新 2：语义边界检测后，把视频切成 query-aware semantic segments

**要解决的问题**：  
如果直接全局选 K 帧，容易被某个高相关片段垄断预算，导致其他重要阶段缺失。

**Insight**：  
长视频理解需要“章节覆盖”。一旦找到语义边界，就可以把视频变成若干相对连贯的段：

$$
G=\{G_1,G_2,\dots,G_{M+1}\}
$$

每个段是一个局部稳定的语义单元。

**具体设计**：  
作者在变化强度信号 $c_t$ 上做 peak detection，并用 adaptive height、prominence、minimum distance 过滤伪峰。补充材料中给出的阈值包括：

$$
\tau_{height}=\bar{c}+\alpha\sigma_c
$$

$$
\tau_{prom}=\beta(\max c_t-\min c_t)
$$

$$
\delta_{min}=\max(5,\lfloor 0.02N \rfloor)
$$

默认 $\alpha=0.5,\beta=0.05$。([arXiv](https://arxiv.org/pdf/2603.00512))

**为什么有效**：  
它把“找帧”变成了“先找章节，再在章节内找帧”。这等价于给选择过程加入一个强归纳偏置：

$$
\text{selected frames should cover semantic transitions and coherent temporal units}
$$

这比单纯相关性 top-K 更适合顺序、过程、因果类视频问答。

---

### 创新 3：Adaptive Budget Allocation，把帧预算分给语义段而非全局竞争

**要解决的问题**：  
不同语义段重要性不同。平均分配会浪费预算，纯 top-K 又会过度集中。

**Insight**：  
一个段的重要性不只由最高相关帧决定，还取决于持续时间、平均相关性、峰值相关性、内部变化程度。

**具体设计**：  
对每个 segment $G_i$ 计算复合重要性：

$$
Imp(G_i)=w_d\frac{|G_i|}{N}+w_a\bar{s}_i+w_m s_i^{max}+w_v\frac{\sigma_i^2}{\sigma^2_{global}}
$$

默认权重为：

$$
w_d=0.4,\quad w_a=0.2,\quad w_m=0.3,\quad w_v=0.1
$$

然后过滤低重要性段，并用 softmax 按重要性分配总帧预算 $K$。([arXiv](https://arxiv.org/pdf/2603.00512))

**为什么有效**：

- duration：长段可能需要更多覆盖；
- mean relevance：持续相关的段应被保留；
- max relevance：短暂但关键的高相关事件不能被忽略；
- variance：段内变化大，说明可能包含更多信息状态。

**隐含机制**：  
这本质上是一个 handcrafted prior，而不是学习出来的策略。它有效的原因不是公式本身多精确，而是它把预算分配从：

$$
\text{frame-level competition}
$$

改成：

$$
\text{segment-level stratified allocation}
$$

这种分层采样减少了单一视觉模式对预算的垄断。

---

### 创新 4：Segment-local MMR，避免段内冗余

**要解决的问题**：  
即使已经分段，段内仍可能有大量相似帧。如果只选最高分，还是会重复。

**Insight**：  
每个语义段内需要同时保证 relevance 和 diversity。

**具体设计**：  
每个段先选最高相关帧作为 anchor：

$$
t_{anchor}=\arg\max_{t\in G_i}s_t
$$

剩余帧用局部 MMR 迭代选择：

$$
t^*=\arg\max_{t\in G_i\setminus T_i}
\left[
\lambda s_t-(1-\lambda)\max_{t'\in T_i}sim(f_t,f_{t'})
\right]
$$

默认 $\lambda=0.5$。([arXiv](https://arxiv.org/pdf/2603.00512))

**为什么有效**：  
全局 MMR 可能让不同语义段互相压制；局部 MMR 只在段内去冗余，因此既保留章节覆盖，又提升段内多样性。

---

## 4. 实验：证据支持到什么程度？

论文在 VideoMME、MLVU、LongVideoBench 三个长视频 QA benchmark 上评估，并接入 LLaVA-OneVision-7B、LLaVA-Video-7B、Qwen2.5-VL-7B、InternVL3-8B 等 LVLM。实验不使用字幕。([arXiv](https://arxiv.org/pdf/2603.00512))

主结果中，WFS-SB 在多个模型和数据集上带来稳定提升。例如 LLaVA-Video-7B、8 帧预算下，VideoMME 提升 +5.5，MLVU 提升 +9.5，LongVideoBench 提升 +6.2；Qwen2.5-VL-7B、32 帧预算下，MLVU 提升 +10.7，LongVideoBench 提升 +5.5。论文还报告跨配置平均提升为 VideoMME +3.9、MLVU +8.8、LongVideoBench +5.4。([arXiv](https://arxiv.org/pdf/2603.00512))

组件消融也比较关键：完整方法在 Qwen2.5-VL-7B、K=16 下达到 VideoMME 61.9、MLVU 67.9；去掉 DWT 改用 raw local minima 会降到 60.8 / 64.6，改用 raw gradient 为 61.2 / 66.8；去掉 MMR 后也明显下降，尤其 uniform selection 降到 59.2 / 62.7。这个结果支持作者的主张：真正起作用的不是任意分段，而是 wavelet-based boundary detection + segment-local diversity。([arXiv](https://arxiv.org/pdf/2603.00512))

效率上，瓶颈不在小波，而在 dense ITM score extraction。论文报告在 VideoMME 平均 $N=1040$、K=32 时，ITM signal extraction 约 19.4 秒，占总预处理时间约 79%；DWT、边界检测、预算分配几乎可忽略，MMR 约 0.7 秒。([arXiv](https://arxiv.org/pdf/2603.00512))

---

## 5. Potential Flaw：局限与脆弱点

### 5.1 核心假设不总成立：query relevance shift ≠ semantic boundary

WFS-SB 的中心假设是：

$$
\text{semantic boundary} \approx \text{coarse-scale change in query-frame relevance}
$$

这个假设在过程型、事件顺序型问题上很合理。但在以下问题上可能弱：

- 问题关注一个持续存在的对象，例如“视频中桌上的杯子是什么颜色？”
- 答案依赖一个低显著、短暂、但 relevance 分数不高的细节；
- 语义变化主要由音频、对白、字幕表达，而视觉帧变化不明显；
- query 太抽象，ITM score 无法形成可靠时间信号。

作者也承认方法依赖底层 VLM 的 ITM score 质量与校准，domain shift、OOD 内容或对抗扰动可能导致错过真正语义转移。([arXiv](https://arxiv.org/pdf/2603.00512))

### 5.2 计算上不是“免费”的 training-free

WFS-SB 不训练模型，但需要对候选帧密集计算 query-frame ITM 分数。对多小时视频或实时场景，这可能比直接 uniform sampling 昂贵很多。作者补充实验显示 adaptive FPS 可把 ITM 时间从 19.4 秒降到 5.8 秒，同时保持类似甚至略优性能，但这说明原始 1 FPS dense scoring 的确是瓶颈。([arXiv](https://arxiv.org/pdf/2603.00512))

### 5.3 手工先验较强

重要性分数中的四项权重、过滤阈值、分解层数、峰值阈值、MMR $\lambda$ 都是人工设定。论文展示了超参鲁棒性，但这不等于这些先验在新领域一定成立。比如医学手术视频、监控视频、体育转播、影视剪辑，语义节奏差异很大。

### 5.4 可能存在“下游指标解释不足”

论文主要用 QA accuracy 证明有效，但没有直接验证检测到的 semantic boundaries 是否符合人类标注的事件边界。也就是说，实验强烈支持“它提升 QA”，但对“它真的找到了语义边界”这一机制，证据更多是间接的。

### 5.5 极端时间结构脆弱

作者自己指出，快速剪辑广告 / montage 可能导致过度分段；长时间低相关背景中夹杂短暂高相关事件时，segment filtering 可能误删关键短段。([arXiv](https://arxiv.org/pdf/2603.00512))

---

## 6. Motivation：如果从零推导，作者为什么会想到这个方法？

可以把思考链条重建成：

1. 长视频不能全输入 LVLM，那么必须压缩。
2. 压缩什么？不是压缩像素，而是压缩对问题有用的信息。
3. 什么信息对长视频问答最关键？很多问题不是问“是否出现某物”，而是问过程、顺序、因果。
4. 过程、顺序、因果的本质是什么？是状态转移。
5. 状态转移在 observable signal 中怎么体现？如果有 query-frame relevance score，它应该在语义阶段切换时发生趋势变化。
6. 但 raw relevance 很噪，直接求梯度会误检。
7. 什么工具适合处理非平稳、多尺度、低信噪比时间信号？小波变换。
8. 找到边界后怎么选帧？先把预算分给不同语义段，再在段内选相关且多样的帧。
9. 因此得到 WFS-SB：  
   $$
   \text{ITM signal} \rightarrow \text{wavelet semantic boundary} \rightarrow \text{segment budget} \rightarrow \text{local MMR}
   $$

---

## 7. 显式贡献 vs 真正起作用的机制

论文显式贡献是：

- 提出 semantic-shift-first 的 frame selection 视角；
- 用 wavelet transform 检测 semantic boundaries；
- training-free、plug-and-play，多个 benchmark 上优于现有方法。([arXiv](https://arxiv.org/pdf/2603.00512))

但我认为真正起作用的机制是：

> **用小波把 noisy relevance signal 转成低频语义变化信号，然后把全局 top-K 选择问题改造成 segment-stratified sampling 问题。**

换句话说，方法的强点不只是“小波去噪”，而是它改变了选择的归纳偏置：

$$
\text{from selecting salient isolated frames}
$$

变成：

$$
\text{selecting evidence across semantic chapters}
$$

这就是为什么它在小帧预算 $K=8,16$ 时收益尤其明显：预算越紧，越需要避免被单一高相关片段占满。

---

## A. 一句话总结核心贡献

**WFS-SB 把长视频帧选择从“选最相关的 K 帧”重构为“用小波检测 query-conditioned 语义边界，再按章节分配预算并做段内多样化选择”，从而更好保留视频的叙事结构。**

---

## B. 下一篇论文最自然做什么？

最自然的下一步是：

> **Learnable Multimodal Semantic Boundary Selection**

具体研究方向：

把 WFS-SB 中手工的小波基、单一视觉 ITM 信号、固定权重预算分配，扩展成一个可学习但仍轻量的模块：

$$
\text{visual relevance} + \text{audio} + \text{subtitle} + \text{motion} 
\rightarrow 
\text{learned multi-scale boundary signal}
$$

然后用少量事件边界标注或 QA reward 进行弱监督训练。

这样可以直接补上 WFS-SB 的三个短板：

1. 视觉 ITM score 不可靠；
2. 手工 wavelet 和预算权重不一定适配所有领域；
3. 语义变化常常由对白、声音或动作节奏触发，而不只体现在画面-query 相似度里。

---

# you asked

message time: 2026-05-27 08:32:09

BLIP-2 ITM 和CLIP、BLIP、SigLIP2有什么区别

---

# chatgpt response

我会把它们放在同一个“图文匹配/检索/理解”的坐标系里比较：训练目标、架构交互方式、输出分数含义，以及为什么论文会选 BLIP-2 ITM 而不是 CLIP/SigLIP2。

# 核心区别一句话

**CLIP / SigLIP2 是“先分别编码图和文，再算相似度”的双塔检索模型；BLIP / BLIP-2 ITM 是“让图文在模型内部交互后，再判断是否匹配”的 cross-modal matching 模型。**

所以在 WFS-SB 这类方法里，**BLIP-2 ITM 分数更像“这帧是否真的回答这个 query”的匹配概率**，而 CLIP / SigLIP2 分数更像“这帧和 query 在全局语义向量空间里近不近”。

---

## 1. 从信息流看：最大区别是有没有图文交互

设图像帧为 $I$，问题文本为 $q$。

### CLIP / SigLIP2：dual encoder

$$
v = E_I(I), \quad t = E_T(q)
$$

$$
score(I,q)= sim(v,t)
$$

图像和文本 **分别编码**，最后只在 embedding 空间做点积 / cosine / logit 相似度。CLIP 官方实现中，模型返回的是 image feature 和 text feature 的 cosine similarity 乘以温度系数后的 logits。([GitHub](https://github.com/openai/CLIP))

这类方法优点是快：

- 所有视频帧的 image embedding 可以预计算；
- query 来了只算 text embedding；
- 然后矩阵乘法即可得到所有帧分数。

但缺点是：图文没有细粒度 token-level 交互，容易只捕捉全局语义。

---

### BLIP / BLIP-2 ITM：fusion / cross encoder

$$
score(I,q)= Head(Fusion(I,q))
$$

图像和文本不是各算各的，而是在模型中通过 cross-attention / self-attention 交互，再由一个 ITM head 判断：

$$
p(\text{matched}\mid I,q)
$$

BLIP 的 ITM 目标就是让 image-grounded text encoder 学习细粒度图文对齐，用线性 ITM head 判断 image-text pair 是 matched 还是 unmatched。([ar5iv](https://ar5iv.org/pdf/2201.12086))

BLIP-2 的 ITM 也类似，但它通过 Q-Former 做图文桥接。论文中 BLIP-2 的 ITM 使用双向 self-attention mask，使 query embeddings 和 text tokens 可以互相 attend，然后把每个 query 输出送入二分类线性层，最后平均 logits 作为 matching score。([ar5iv](https://ar5iv.org/html/2301.12597v3))

所以 BLIP-2 ITM 更像：

> “模型看着这张图和这句话，经过交互后判断它们是否匹配。”

而 CLIP / SigLIP2 更像：

> “图和文分别变成向量，看两个向量离得近不近。”

---

## 2. 四者对比表

| 模型 | 架构范式 | 主要输出分数 | 图文是否交互 | 训练目标核心 | 适合什么 |
|---|---|---|---|---|---|
| **CLIP** | 双塔 dual encoder | embedding 相似度 | 否 | contrastive / InfoNCE | 快速检索、zero-shot 分类、大规模排序 |
| **SigLIP2** | 双塔 dual encoder | sigmoid-style 图文匹配 logit / 相似度 | 否 | SigLIP sigmoid loss + SigLIP2 多任务增强 | 更强的多语种、检索、dense/localization 表征 |
| **BLIP** | multimodal encoder-decoder | ITC 分数、ITM 分数、生成概率 | 是 | ITC + ITM + LM | 图文检索、caption、VQA、过滤噪声图文对 |
| **BLIP-2 ITM** | frozen image encoder + Q-Former | ITM match score | 是 | Q-Former 阶段的 ITC + ITM + ITG | 更强的图文匹配、VQA、caption、作为 relevance scorer |

---

## 3. BLIP-2 ITM vs CLIP

### CLIP 的本质

CLIP 训练目标是：在一个 batch 里，让真实图文对相似度高，错误图文对相似度低。它学习的是一个共享语义空间：

$$
E_I(I) \approx E_T(q)
$$

CLIP 非常适合：

- text-image retrieval；
- zero-shot classification；
- 快速从大量图片中找相关图。

但 CLIP 的分数是全局 embedding 相似度，不一定能精细判断复杂关系，例如：

- “左边的人是否正在把红色杯子递给右边的人？”
- “这一步是不是发生在涂睫毛之后？”
- “画面中哪个动作和 query 中的事件转移对应？”

因为它没有在推理时让文本 token 和视觉 patch/token 充分交互。

---

### BLIP-2 ITM 的本质

BLIP-2 ITM 是一个 binary matching head：

$$
p(y=1 \mid I,q)
$$

其中 $y=1$ 表示图文匹配。它通过 Q-Former 让 learnable queries 从 frozen image encoder 中抽取与文本相关的视觉信息，再和文本进行交互。BLIP-2 的 Q-Former 被设计成冻结图像编码器和冻结 LLM 之间的桥梁，第一阶段学习图文表示，第二阶段学习视觉到语言生成。([ar5iv](https://ar5iv.org/html/2301.12597v3))

因此，BLIP-2 ITM 的分数通常更适合作为：

$$
\text{frame-query relevance score}
$$

也就是“这帧是否和问题语义匹配”。

代价是慢：  
每个 $(frame, query)$ pair 都要跑一次图文融合，而 CLIP 可以预先算好所有 frame embeddings。

---

## 4. BLIP-2 ITM vs BLIP

BLIP 是 BLIP-2 的前一代。BLIP 的核心是 **Multimodal Mixture of Encoder-Decoder, MED**，一个模型可以切换成三种功能：

1. unimodal encoder：做 ITC；
2. image-grounded text encoder：做 ITM；
3. image-grounded text decoder：做 caption generation。

BLIP 还提出 CapFilt：captioner 生成 synthetic captions，filter 用 ITM 去掉 noisy captions。([ar5iv](https://ar5iv.org/pdf/2201.12086))

BLIP-2 的关键变化是：

$$
\text{不再端到端训练整个大 VLP 模型}
$$

而是使用：

$$
\text{frozen image encoder} + \text{Q-Former} + \text{frozen LLM}
$$

BLIP-2 论文明确说，它通过 lightweight Q-Former 连接冻结的视觉模型和冻结的大语言模型，以更低训练成本获得强视觉语言能力。([arXiv](https://arxiv.org/abs/2301.12597))

所以：

- **BLIP ITM**：经典 cross-modal matching；
- **BLIP-2 ITM**：用 Q-Former 做信息瓶颈后的 cross-modal matching；
- **BLIP-2 更模块化、更省训练成本，也更容易借用强视觉 encoder 和 LLM。**

但注意：在 WFS-SB 里用的是 **BLIP-2 ITM matching score**，不是让 BLIP-2 LLM 去完整回答问题。它只是一个 frame-query scorer。

---

## 5. BLIP-2 ITM vs SigLIP2

SigLIP2 本质上仍然属于 CLIP-like dual encoder，只是训练 recipe 更强。

原始 SigLIP 的主要区别是：它不用 CLIP 那种 batch softmax contrastive loss，而是用 pairwise sigmoid loss。SigLIP 论文指出，sigmoid loss 只在 image-text pair 上操作，不需要对全局 pairwise similarity 做 softmax normalization。([arXiv](https://arxiv.org/abs/2303.15343?utm_source=chatgpt.com))

SigLIP2 在此基础上加入更多训练技术，包括 captioning-based pretraining、self-distillation、masked prediction、online data curation，并提升多语种理解、localization 和 dense prediction 能力。([arXiv](https://arxiv.org/abs/2502.14786))

所以 SigLIP2 相比 CLIP：

- 仍是双塔；
- 更强、更现代；
- 多语种和 dense feature 更好；
- 检索和 zero-shot 分类更强；
- 但默认仍不是 BLIP-2 ITM 这种 cross-attention matching classifier。

换句话说：

$$
\text{SigLIP2 是更强的 embedding model}
$$

而

$$
\text{BLIP-2 ITM 是更强的 pairwise matching scorer}
$$

---

## 6. 为什么 WFS-SB 会用 BLIP-2 ITM？

WFS-SB 需要的是每一帧和 query 的时间相关性信号：

$$
s_t = M(q, f_t)
$$

然后对这个信号做小波分析，找语义边界。

这里 $M(q,f_t)$ 最好满足两个条件：

1. 分数要和 query 语义强相关；
2. 分数波动要能反映视频中 query-relevant semantic state 的变化。

BLIP-2 ITM 比 CLIP/SigLIP2 更适合这个设定，因为它输出的是图文 pair 的匹配判断，而不是单纯的全局 embedding 相似度。

但代价也很明显：

$$
\text{BLIP-2 ITM 更准但更慢；CLIP/SigLIP2 更快但更粗。}
$$

---

## 7. 第一性总结

如果从“图文匹配”本质看，四者的差别是：

### CLIP

$$
\text{alignment by geometry}
$$

把图和文投到同一个空间，用距离表示匹配。

### SigLIP2

$$
\text{stronger alignment by sigmoid pair objective + better recipe}
$$

仍是几何对齐，但训练目标和数据/任务 recipe 更强。

### BLIP

$$
\text{alignment by interaction + generation}
$$

不仅对齐，还让图文交互，并能生成文本。

### BLIP-2 ITM

$$
\text{alignment by Q-Former-mediated interaction}
$$

用 Q-Former 从冻结视觉模型里抽取和文本最相关的信息，再判断图文是否匹配。

**所以，在帧选择任务中：CLIP/SigLIP2 是高效 coarse scorer；BLIP-2 ITM 是较慢但更细的 semantic matching scorer。**

---

# you asked

message time: 2026-05-27 08:36:18

那BLIP-2 ITM和Qwen2.5 VL 7B 打分相比谁更好

---

# chatgpt response

我会按“作为 frame-query scorer”的目标来比较，而不是泛泛比较两个模型能力：看分数语义、校准性、速度、可复现性、对长视频边界信号的适配。

没有绝对“谁更好”。**如果目标是给每一帧产生一个稳定、连续、可用于小波边界检测的 relevance signal，BLIP-2 ITM 更合适；如果目标是对少量候选帧做复杂语义判断或最终回答，Qwen2.5-VL-7B 更强。**

---

## 1. 第一性区别：两者优化目标不一样

### BLIP-2 ITM：天生是打分器

BLIP-2 的 ITM 是一个 **image-text matching 二分类头**。它被训练来判断：

$$
(I, q) \rightarrow \text{matched or unmatched}
$$

论文中，BLIP-2 ITM 使用双向 self-attention，让 query embeddings 和 text tokens 可以互相交互；然后把每个 query embedding 输入二分类 linear classifier，并平均 logits 得到 matching score。也就是说，它天然输出一个 pairwise matching 分数。([ar5iv](https://ar5iv.org/html/2301.12597v3))

所以它适合做：

$$
s_t = M(f_t, q)
$$

这种逐帧相关性信号。

---

### Qwen2.5-VL-7B：天生是生成式 LVLM，不是打分器

Qwen2.5-VL-7B-Instruct 是 image/video-text-to-text 模型，默认接口是输入图像/视频和文本，然后生成回答。官方 model card 也是通过 `model.generate(...)` 来调用，而不是给出一个专门的 ITM score。([Hugging Face](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct))

如果你想用 Qwen2.5-VL 打分，通常只能构造代理目标，例如：

$$
score(f_t,q)=P(\text{“Yes”}\mid f_t,q,\text{prompt})
$$

或者：

$$
score(f_t,q)=\log P(\text{某个判断句}\mid f_t,q)
$$

这不是它原生训练出来的、校准过的匹配分数，而是从生成概率里“挤”出来的 proxy score。

---

## 2. 用作 frame-query scorer：BLIP-2 ITM 通常更优

对于 WFS-SB 这种方法，关键不是让 scorer 回答问题，而是得到一个时间序列：

$$
s_1,s_2,\dots,s_N
$$

然后检测其中的 coarse semantic shift。

这种场景下，好的 scorer 需要满足：

1. **分数连续**
2. **跨帧可比较**
3. **prompt 不敏感**
4. **计算成本低**
5. **噪声不能太大**
6. **能形成稳定的 temporal signal**

BLIP-2 ITM 比 Qwen2.5-VL 更符合这些要求，因为它本来就是 image-text pair matching classifier。Qwen2.5-VL 虽然语义能力更强，但如果用 yes/no prompt 或 log-likelihood 打分，分数会受到 prompt wording、输出格式、语言先验、解码设置、tokenization 的影响。

简单说：

$$
\text{BLIP-2 ITM score} \approx \text{matching score}
$$

$$
\text{Qwen score} \approx \text{prompt-conditioned self-judgment score}
$$

前者更适合做信号处理，后者更适合做语义推理。

---

## 3. 但 Qwen2.5-VL-7B 的语义能力更强

Qwen2.5-VL-7B 在复杂视觉理解上明显更现代。官方说明它增强了图像、文本、图表、布局理解，也支持长视频理解、事件定位、视觉定位和结构化输出。([Hugging Face](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct))

它还在视频输入上引入 dynamic FPS sampling，并在时间维度上加入 absolute time alignment，使模型能学习 temporal sequence 和 speed，从而定位具体时刻。([Hugging Face](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)) 官方 benchmark 中，Qwen2.5-VL-7B 在 Video-MME、MVBench、PerceptionTest、MLVU 等视频任务上也给出了强结果。([Hugging Face](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct))

所以如果 query 是复杂的，例如：

- “哪一帧能证明他先打开冰箱再拿出牛奶？”
- “这一步是不是在擦掉眼影，而不是重新上妆？”
- “哪一帧包含表格里金额变化的证据？”
- “哪一帧能回答屏幕上弹窗的具体内容？”

Qwen2.5-VL 可能比 BLIP-2 ITM 判断得更准，因为它更会读文字、理解动作、处理空间关系和进行多步语义判断。

---

## 4. 更准确的结论：分工不同

| 使用场景 | 更推荐 |
|---|---|
| 对几百/几千帧逐帧打分 | **BLIP-2 ITM** |
| 构造平滑 temporal relevance signal | **BLIP-2 ITM** |
| 小波边界检测、峰值检测、segment allocation | **BLIP-2 ITM** |
| 需要可复现、低 prompt 敏感的 scalar score | **BLIP-2 ITM** |
| 对 top-20 / top-50 候选帧重排序 | **Qwen2.5-VL-7B** |
| 判断复杂动作、OCR、图表、屏幕、空间关系 | **Qwen2.5-VL-7B** |
| 直接回答视频问题 | **Qwen2.5-VL-7B** |
| 端到端 long video understanding | **Qwen2.5-VL-7B** |

---

## 5. 最合理的系统设计：BLIP-2 粗筛，Qwen 重排

我会把它设计成两阶段：

### Stage 1：BLIP-2 ITM 生成 dense signal

$$
s_t^{BLIP}=ITM(f_t,q)
$$

用途：

- 全视频逐帧打分；
- 做 wavelet transform；
- 找 semantic boundary；
- 选出每个 segment 的候选帧。

### Stage 2：Qwen2.5-VL rerank 少量候选帧

对候选帧集合：

$$
C=\{f_{c_1},\dots,f_{c_m}\}, \quad m \ll N
$$

用 Qwen2.5-VL 判断：

> “这些帧中哪些最能帮助回答问题？”

或者用 constrained yes/no logit：

$$
s_t^{Qwen} = \log P(\text{Yes}\mid f_t,q) - \log P(\text{No}\mid f_t,q)
$$

最终分数可以融合：

$$
s_t = \alpha \cdot norm(s_t^{BLIP}) + (1-\alpha)\cdot norm(s_t^{Qwen})
$$

其中 Qwen 只在少量候选帧上运行，避免把 7B LVLM 用成昂贵的逐帧 scorer。

---

## 6. 为什么 WFS-SB 用 BLIP-2 ITM 是合理的？

WFS-SB 的核心不是“让 scorer 自己理解长视频”，而是要得到：

$$
\text{query-conditioned temporal signal}
$$

然后通过小波找语义变化。这个信号最好来自一个稳定的 matching head，而不是来自生成式模型的 prompt-based 判断。

如果直接用 Qwen2.5-VL-7B 逐帧打分，可能出现三个问题：

1. **成本高**：每帧都跑 7B 生成式模型，长视频很贵。
2. **分数不稳定**：yes/no 概率受 prompt 和语言 token 影响。
3. **信号不一定平滑**：Qwen 的判断可能是离散的、解释型的，不一定适合小波分解。

所以在 WFS-SB 框架里：

$$
\text{BLIP-2 ITM} = \text{good signal generator}
$$

$$
\text{Qwen2.5-VL} = \text{good downstream reasoner}
$$

---

## 7. 最终判断

**做 dense frame scoring：BLIP-2 ITM 更好。**

**做复杂语义 reranking / final QA：Qwen2.5-VL-7B 更好。**

最自然的改进不是二选一，而是：

$$
\text{BLIP-2 ITM 找边界和候选帧} 
\rightarrow 
\text{Qwen2.5-VL 对候选帧重排 / 验证}
\rightarrow
\text{Qwen2.5-VL 或其他 LVLM 回答}
$$

这比单独用 BLIP-2 或单独用 Qwen2.5-VL 都更合理。

---

# you asked


> [!chatgpt]+
> 那如果我先让LLM把问题分解成相关的证据结构，然后再用BLIP-2ITM逐帧打分这样，和直接对问题用Qwen2.5-VL-7B打分相比，你有什么看法


---

# chatgpt response

我会把你的方案视为“先把推理问题转成可检索证据图，再做 dense visual matching”，核心比较点是：可分解性、分数可组合性、成本和错误传播。

# 我的看法

你的方案 **比直接用 Qwen2.5-VL-7B 对原问题逐帧打分更有研究价值**，尤其适合长视频帧选择。它的本质优势是：

$$
\text{复杂问题} \rightarrow \text{结构化证据需求} \rightarrow \text{多个可匹配的视觉信号}
$$

而不是直接让一个生成式 LVLM 对每一帧回答：

$$
\text{这一帧是否有助于回答原问题？}
$$

前者更像 **evidence-aware frame selection**，后者更像 **prompt-based relevance scoring**。

---

## 1. 两种方案本质上在做不同的事情

### 方案 A：LLM 分解问题 + BLIP-2 ITM 逐证据打分

假设问题是：

> “视频里男子在倒入牛奶之前做了什么？”

LLM 可以分解成证据结构：

```text
目标答案：倒入牛奶之前的动作
需要证据：
1. 找到“倒入牛奶”的时刻
2. 找到该时刻之前的动作片段
3. 判断前一个动作是什么
时间关系：action_before(pour_milk)
```

然后构造多个 atomic evidence query：

$$
e_1=\text{person pouring milk}
$$

$$
e_2=\text{person opening fridge}
$$

$$
e_3=\text{person taking bottle}
$$

$$
e_4=\text{person holding cup}
$$

对每个证据做 BLIP-2 ITM 打分：

$$
s_i(t)=ITM(f_t,e_i)
$$

最后得到多个时间信号：

$$
s_1(t),s_2(t),...,s_m(t)
$$

再根据证据结构组合这些信号。

这不是简单 frame scoring，而是：

$$
\text{structured temporal evidence retrieval}
$$

---

### 方案 B：Qwen2.5-VL-7B 直接对原问题逐帧打分

你可能会 prompt：

> “Does this frame help answer the question: What did the man do before pouring milk?”

然后得到：

$$
s(t)=P(\text{Yes}\mid f_t,q)
$$

问题是，单帧本身通常无法回答“before”。单帧没有完整时间上下文，所以 Qwen 的逐帧判断会变成一种模糊语义估计：

$$
\text{frame relevance} \neq \text{answer sufficiency}
$$

也就是说，它可能知道这帧和“milk”有关，但不知道它是不是“之前”的关键证据。

---

## 2. 为什么“先分解证据结构”可能更好？

### 2.1 它把复杂问题拆成 BLIP-2 ITM 更擅长的子问题

BLIP-2 ITM 不擅长复杂推理，但擅长判断：

$$
(image, text) \rightarrow matched?
$$

所以不要让它判断：

> “这帧是否能回答一个带时间约束的问题？”

而应该让它判断：

> “这帧里是否有人倒牛奶？”  
> “这帧里是否有人打开冰箱？”  
> “这帧里是否有人拿出瓶子？”

这些是更接近 ITM 训练目标的 atomic matching。

因此你的方法把任务从：

$$
ITM(f_t, complex\ question)
$$

改成：

$$
\{ITM(f_t, atomic\ evidence_i)\}_{i=1}^{m}
$$

这通常更稳定。

---

### 2.2 它可以显式建模时间关系

直接 Qwen 单帧打分很难表达：

- before
- after
- during
- first
- last
- cause
- result
- transition
- repeated action
- missing step

但证据结构可以表达：

$$
e_a \prec e_b
$$

例如：

$$
\text{open fridge} \prec \text{take milk} \prec \text{pour milk}
$$

于是你可以不只看单点分数，而是看时间序列模式：

$$
s_{open}(t), s_{take}(t), s_{pour}(t)
$$

如果某段满足：

$$
t_1 < t_2 < t_3
$$

且：

$$
s_{open}(t_1), s_{take}(t_2), s_{pour}(t_3)
$$

都高，那么这组帧比单个高分帧更有意义。

这正是长视频理解需要的东西：**不是最高相关帧，而是证据链。**

---

### 2.3 它更适合和 WFS-SB 结合

原 WFS-SB 只有一个 relevance signal：

$$
s(t)=ITM(f_t,q)
$$

你的方案可以得到多个 evidence signals：

$$
S(t)=
\begin{bmatrix}
s_1(t)\\
s_2(t)\\
...\\
s_m(t)
\end{bmatrix}
$$

然后可以检测多种边界：

### 单证据边界

$$
c_i(t)=Wavelet(s_i(t))
$$

表示某个证据概念何时出现 / 消失。

### 组合边界

$$
c(t)=Wavelet(Aggregate(s_1(t),...,s_m(t)))
$$

表示整体证据状态何时发生变化。

### 证据转移边界

例如从 “拿瓶子” 到 “倒牛奶”：

$$
transition(t)=s_{take}(t-\Delta)\cdot s_{pour}(t)
$$

这比原论文的单信号小波边界更丰富。

---

## 3. 相比直接 Qwen 打分，你的方案优势在哪里？

| 维度 | LLM 分解 + BLIP-2 ITM | Qwen2.5-VL 直接打分 |
|---|---|---|
| dense scoring 成本 | 较低，可批量逐帧打分 | 高，每帧跑 7B 代价大 |
| 分数稳定性 | 较稳定，ITM 是匹配分数 | 受 prompt、yes/no token、生成偏置影响 |
| 可解释性 | 强，知道每帧匹配哪个证据 | 弱，只知道模型觉得有用 |
| 时间关系建模 | 可显式建模 before/after | 单帧打分很难建模 |
| 复杂语义理解 | 受 BLIP-2 能力限制 | Qwen 更强 |
| OCR / 小物体 / 复杂空间关系 | 较弱 | 较强 |
| 错误来源 | LLM 分解错、ITM 匹配错 | prompt 打分不稳、成本高 |
| 适合角色 | dense evidence retriever | reranker / verifier / final reasoner |

我的判断是：

$$
\text{LLM decomposition + BLIP-2 ITM}
$$

更适合作为 **第一阶段长视频帧选择器**。

$$
\text{Qwen2.5-VL direct scoring}
$$

更适合作为 **少量候选帧的精排器或验证器**。

---

## 4. 但你的方案有一个关键风险：分解质量决定上限

LLM 分解会引入新的错误模式。

### 风险 1：过度分解

问题：

> “Why did the woman smile?”

LLM 可能分解成：

```text
1. woman sees gift
2. woman receives compliment
3. woman feels happy
```

但视频里真实原因可能是别人讲了笑话。过度假设会导致 BLIP-2 去找不存在的证据。

---

### 风险 2：抽象证据不可视觉匹配

有些证据是心理、因果、意图层面的：

```text
the man is confused
the woman is embarrassed
the dog is waiting for permission
the child realizes the mistake
```

BLIP-2 ITM 对这些抽象状态打分可能很不稳定。

更好的做法是让 LLM 把抽象证据进一步转成可观察证据：

$$
\text{confused}
\rightarrow
\{\text{looking around}, \text{hesitating}, \text{scratching head}, \text{frowning}\}
$$

也就是：

$$
\text{latent state} \rightarrow \text{observable visual proxies}
$$

---

### 风险 3：证据组合不能只靠平均分

假设问题是：

> “Did the person put the red cup into the bag?”

证据包括：

$$
e_1=\text{red cup}
$$

$$
e_2=\text{bag}
$$

$$
e_3=\text{putting object into bag}
$$

不能简单平均：

$$
s(t)=\frac{s_1(t)+s_2(t)+s_3(t)}{3}
$$

因为只看到红杯但没有袋子，不算关键帧；只看到袋子但没有动作，也不够。

更合理的是根据逻辑结构聚合：

### AND 证据

$$
s(t)=\min(s_1(t),s_2(t),s_3(t))
$$

或：

$$
s(t)=s_1(t)\cdot s_2(t)\cdot s_3(t)
$$

### OR 证据

$$
s(t)=\max_i s_i(t)
$$

### Temporal 证据

$$
s(t_1,t_2)=s_{before}(t_1)\cdot s_{after}(t_2),\quad t_1<t_2
$$

所以你的方法真正难点不是“让 LLM 分解”，而是：

> **如何把证据结构转成可计算的时序打分函数。**

这会是论文里最关键的 technical contribution。

---

## 5. 我会怎么设计这个系统？

### Step 1：问题分解成 Evidence Graph

让 LLM 输出结构化形式：

```json
{
  "answer_type": "temporal_action",
  "evidence_nodes": [
    {
      "id": "E1",
      "text": "person pouring milk",
      "type": "visual_action",
      "observability": "high"
    },
    {
      "id": "E2",
      "text": "person taking milk bottle",
      "type": "visual_action",
      "observability": "high"
    },
    {
      "id": "E3",
      "text": "person opening refrigerator",
      "type": "visual_action",
      "observability": "medium"
    }
  ],
  "relations": [
    {"type": "before", "source": "E3", "target": "E2"},
    {"type": "before", "source": "E2", "target": "E1"}
  ]
}
```

重点：让 LLM 标注每个 evidence node 的 **observability**。

不可视觉观察的节点不要直接送给 BLIP-2 ITM。

---

### Step 2：对每个 evidence node 逐帧打分

$$
s_i(t)=ITM(f_t,e_i)
$$

得到 evidence score matrix：

$$
S\in \mathbb{R}^{m\times N}
$$

其中 $m$ 是证据数，$N$ 是候选帧数。

---

### Step 3：根据证据逻辑构造组合信号

例如：

#### 对象 + 动作共同出现

$$
s_{joint}(t)=\min(s_{object}(t),s_{action}(t))
$$

#### 事件转移

$$
s_{transition}(t)=s_A(t-\Delta)\cdot s_B(t)
$$

#### 顺序证据链

$$
score(t_1,t_2,t_3)=s_A(t_1)s_B(t_2)s_C(t_3),\quad t_1<t_2<t_3
$$

#### 证据覆盖度

$$
coverage(G)=\sum_i \max_{t\in G}s_i(t)
$$

这一步可以替代原 WFS-SB 的单一 importance score。

---

### Step 4：用小波 / peak detection 找证据边界

不是只对原问题的 signal 做 wavelet：

$$
Wavelet(ITM(f_t,q))
$$

而是对多个 evidence signals 做：

$$
Wavelet(s_i(t))
$$

再合并边界：

$$
c(t)=\sum_i w_i |Wavelet(s_i(t))|
$$

这样边界对应的是：

> 哪些证据状态发生了变化？

而不只是：

> 原问题整体相关性是否变化？

---

### Step 5：Qwen2.5-VL 只做 rerank / verify

对最终候选帧或候选片段，让 Qwen 判断：

```text
Given the question and the selected evidence frames,
which frames are most useful for answering the question?
```

或者让它验证 evidence graph：

```text
Do these frames support the temporal relation:
opening refrigerator before pouring milk?
```

这样 Qwen 的使用位置从：

$$
\text{dense scorer}
$$

变成：

$$
\text{semantic verifier}
$$

这更符合它的强项。

---

## 6. 这个想法相比 WFS-SB 的潜在 novelty

WFS-SB 是：

$$
q \rightarrow s(t) \rightarrow semantic boundary
$$

你的方向是：

$$
q \rightarrow EvidenceGraph(q) \rightarrow \{s_i(t)\}_{i=1}^m \rightarrow evidence-aware boundary
$$

所以创新点可以写成：

### 创新 1：从 query-level relevance 到 evidence-level relevance

不是问：

$$
\text{which frames match the question?}
$$

而是问：

$$
\text{which frames support each required evidence node?}
$$

### 创新 2：从单信号边界到多证据状态转移

不是检测：

$$
Wavelet(s_q(t))
$$

而是检测：

$$
Wavelet(S(t))
$$

其中 $S(t)$ 是 evidence state vector。

### 创新 3：从帧级 relevance 到证据链覆盖

目标不只是 top-K relevance，而是最大化：

$$
\text{Evidence Coverage} + \text{Temporal Consistency} + \text{Diversity}
$$

可以形式化为：

$$
F^*=\arg\max_F 
\left[
\sum_i \max_{t\in F}s_i(t)
+
\lambda \cdot TempConsistency(F,E)
-
\gamma \cdot Redundancy(F)
\right]
$$

这就比 WFS-SB 更像一个新方法，而不是简单替换 scorer。

---

## 7. 最关键的实验对比应该怎么做？

为了证明你的方法强，需要至少比较这些设置：

| Variant | 含义 |
|---|---|
| Raw BLIP-2 ITM | 直接用原问题打分 |
| Raw Qwen scoring | Qwen 对原问题逐帧 yes/no 打分 |
| LLM decomposition + BLIP-2 average | 分解后简单平均 |
| LLM decomposition + BLIP-2 structured aggregation | 分解后按证据逻辑聚合 |
| LLM decomposition + BLIP-2 + Qwen rerank | 完整方法 |
| Oracle decomposition | 人工证据分解上限 |

最重要的 ablation 是：

$$
\text{decomposition 有用，还是只是多 prompt ensemble 有用？}
$$

所以必须比较：

1. LLM 结构化分解；
2. 随机 paraphrase 多 prompt；
3. 直接把原问题改写成多个 query；
4. 人工 oracle evidence。

否则容易被质疑：提升只是 prompt augmentation，不是 evidence structure。

---

## 8. 什么时候你的方案会明显优于 Qwen 直接打分？

### 更适合的问题类型

- “之前 / 之后发生了什么？”
- “某个动作导致了什么结果？”
- “视频中完成某任务用了哪些步骤？”
- “对象从哪里被移动到哪里？”
- “哪一步出错了？”
- “人物先做 A 还是先做 B？”
- “最终状态和初始状态有什么不同？”

这些都需要证据链，而不是单帧语义判断。

---

### 不一定适合的问题类型

- OCR-heavy：屏幕文字、表格、菜单、字幕；
- 细粒度空间关系：左上角、小物体、遮挡关系；
- 情绪、意图、反讽、社会互动；
- 问题本身很简单：例如“视频里有没有狗？”
- 需要世界知识推理，而不是视觉证据检索。

这些场景 Qwen 可能更有优势。

---

## 9. 我的最终建议

不要把它设计成：

$$
\text{LLM 分解 + BLIP-2}
\quad \text{vs} \quad
\text{Qwen 打分}
$$

更好的论文定位是：

$$
\text{LLM 分解 + BLIP-2 dense evidence retrieval + Qwen verification}
$$

具体结论：

1. **dense 阶段不要用 Qwen**：太贵，分数也不够稳定。
2. **不要直接把原问题丢给 BLIP-2**：复杂问题会超出 ITM 的匹配能力。
3. **先用 LLM 把问题拆成可视觉观察的 evidence graph**：这是你的核心价值。
4. **用 BLIP-2 ITM 为每个 evidence node 产生时间信号**。
5. **用结构化聚合，而不是简单平均**。
6. **最后让 Qwen 对少量候选帧做验证和重排**。

一句话：

> **你的方案更像把长视频问答转化为“证据图驱动的时序检索”；相比直接 Qwen 逐帧打分，它更便宜、更可解释、更适合长视频边界检测，但成败取决于证据分解是否可观察、以及证据分数是否被正确组合。**