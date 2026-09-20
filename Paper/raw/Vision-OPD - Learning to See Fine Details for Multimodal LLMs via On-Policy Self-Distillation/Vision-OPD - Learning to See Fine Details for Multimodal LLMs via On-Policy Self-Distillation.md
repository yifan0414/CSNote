---
title: "Vision-OPD: Learning to See Fine Details for Multimodal LLMs via On-Policy Self-Distillation"
authors: ["Qianhao Yuan", "Jie Lou", "Xing Yu", "Hongyu Lin", "Le Sun", "Xianpei Han", "Yaojie Lu"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2605.18740"
pdf_link: "[[assets/paper_2605.18740.pdf]]"
cover: "[[assets/pipeline_2605.18740.png]]"
updated: 2026-09-20
tags: ["paper/arxiv", "vlm", "distillation", "image-text"]
status: "unread"
priority:
rating:
topics: ["MLLM"]
code: "https://github.com/VisionOPD/Vision-OPD"
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

- 多模态大模型（MLLM）在细粒度视觉理解上的失败，很多时候并非「看不清」，而是无法在整幅图像的视觉 token 中聚焦到那块小而决定性的证据。
- 论文把这一现象量化成 regional-to-global gap：同一个模型在只看到证据区域的裁剪图时，准确率稳定高于看到对应全图时，ZoomBench 上差距为 $18$ ~ $22$ 个百分点，且该差距在更大参数量的开源模型和闭源模型上同样存在。
- 提出 Vision-OPD：用同一个 MLLM 实例化两个条件策略——以证据裁剪图为输入的 teacher 与以全图为输入的 student，在 student 自己生成的 rollout 上逐 token 对齐二者分布，把「放大看」的收益内化进全图推理。
- 具备五个属性：on-policy 采样、token 级稠密监督、无外部 teacher、无 ground-truth 标签、无 verifier；推理时仍是单次前向、不需要视觉工具调用。训练数据仅 $6.2$K，由全自动流程合成。
- 在 Qwen3.5-4B/9B 上做自蒸馏后，Vision-OPD-9B 在六个细粒度基准上平均 $79.68$，超过 Qwen3.5-397B、Kimi-K2.6、GLM-4.6V、GPT-5.4，以及 Gemini-3.1-Pro、Gemini-3.5-Flash 与各类 Thinking-with-Images agentic 模型。
- 训练过程中 regional-to-global gap 持续收窄；在 MMVP / CV-Bench / MMStar / POPE 等 holdout 任务上能力不退化，而 SFT on Self-Teacher、GRPO、DAPO 等训练策略都出现了明显遗忘。

## Key Contributions

- **问题重构**：作者指出细粒度视觉理解的瓶颈不在局部识别能力，而在「全图条件下证据不显著」。他们用「同一问题、同一模型、裁剪图 vs. 全图」的对照实验把这一点变成可度量的 gap，并显示参数缩放（更大模型、闭源模型）并不能消除该 gap。
- **regional-to-global 自蒸馏范式**：把模型自己的裁剪图条件行为（privileged regional perception）当作对全图条件策略的监督信号，训练目标沿着 student 自己生成的前缀计算 teacher/student 的 next-token 分布散度。
- **无需外部依赖的 on-policy 算法**：与依赖更强 teacher 或可验证奖励的 OPD/RLVR 方法不同，Vision-OPD 只用同一个 checkpoint、合成三元组数据和 token 级散度，就同时获得 on-policy 的状态分布对齐与稠密的逐 token 梯度。
- **实验结论**：$6.2$K 合成数据即可让 $9$B 模型在细粒度视觉理解上超过体量远大于它的开源模型与闭源模型；作者同时验证 on-policy 采样、稠密 token 级监督、teacher 正则化都是必要的，并显示自蒸馏能显著缩小 regional-to-global gap。

## Method

### 动机：regional-to-global gap

以 Qwen3.5-9B 为例的定性案例中，问题是「耳罩的颜色是什么」：输入全图时模型答 black（错），输入只包含该区域的裁剪图时答 green（对）。作者在 ZoomBench 上做了系统性对照，发现**同一个模型**在 regional 输入下的准确率一致高于 global 输入，差距约 $18$--$22$ 个百分点；GLM-4.6V、GPT-5.4、Gemini-3.5-Flash、Gemini-3.1-Pro 等更大或闭源模型也存在明显差距。结论是：模型已经能识别证据，只是难以在全图语境下把注意力落到证据上，因此区域条件行为可以充当全图策略的 privileged supervision。

### 数据合成：三元组 $(x, x', q)$

- 对原始图像 $I$ 先做 object identification 与 segmentation，得到候选 bounding box，只保留面积占比小于阈值 $\tau$ 的小区域 $R$（更可能藏着被淹没的细节）。
- 用 Qwen3.5-397B 作为 question generator，为每个保留区域 $R$ 生成一个「仅凭 $R$ 就能回答」的问题 $q$。
- 为了把问题 grounding 回全图并避免指代歧义，把 $R$ 的 bounding box 以红框叠加到 $I$ 上得到 $x$，并在问题后附加空间约束，例如 "Only focus on the objects inside the red bounding box in the image to answer this question."
- 把 $I$ 按 $R$ 的 bounding box 裁剪并放大 $2\times$，得到 $x'$。
- 同一问题在两种视觉条件下出现：student 看带红框的全图，teacher 只看孤立裁剪图，二者差距就是学习信号。
- 为与其他训练策略（SFT / RLVR / OPSD）公平对比，作者还用 Qwen3.5-397B 生成答案标签：对区域 $R$ 采样多个回答，只有多数答案达到严格共识（$> 0.75$）时才保留该问题。最终合成 $6.2$K 训练样本。

### 两个条件策略

同一个参数化模型 $p_\theta$ 因视觉条件不同而扮演两个角色：

- teacher（特权视角，只看裁剪图）：$p_T(\cdot \mid x', q) = p_\theta(\cdot \mid x', q)$
- student（标准推理视角，看全图）：$p_S(\cdot \mid x, q) = p_\theta(\cdot \mid x, q)$

给定样本 $(x, x', q)$，student 先采样 on-policy 回答 $y = (y_1, \dots, y_{|y|}) \sim p_S(\cdot \mid x, q)$；两个策略在**同一条 student 前缀** $y_{<n}$ 上分别给出 next-token 分布 $p_S(y_n \mid x, q, y_{<n})$ 与 $p_T(y_n \mid x', q, y_{<n})$。由于 teacher 在更干净的局部视角下重算了同一轨迹，它的分布天然更尖锐地指向细粒度证据，且不需要额外解码。

### 目标函数

平均逐 token 散度：

$$D(p_T \| p_S)(y \mid x, x', q) = \frac{1}{|y|}\sum_{n=1}^{|y|} D\Big(p_T(\cdot \mid x', q, y_{<n}) \,\Big\|\, p_S(\cdot \mid x, q, y_{<n})\Big)$$

整体损失在 on-policy 样本上取期望：

$$\mathcal{L}_{\text{Vision-OPD}}(\theta) = \mathbb{E}_{(x,x',q)\sim\mathcal{D}}\Big[\mathbb{E}_{y \sim p_S(\cdot \mid x, q)}\big[D(p_T \| p_S)(y \mid x, x', q)\big]\Big]$$

其中 $D$ 可以是任意分布散度，例如广义 Jensen--Shannon 散度 $\mathrm{JSD}_\beta(p_T \| p_S) = \beta\, D_{\mathrm{KL}}(p_T \| m) + (1-\beta)\, D_{\mathrm{KL}}(p_S \| m)$，$m = \beta\, p_T + (1-\beta)\, p_S$ 为插值混合分布。

梯度只回传到 student，teacher 作为固定目标（算法中写作 `stopgrad`）。因为训练前缀来自 student 自己的生成结果，训练与推理的状态分布一致，避免了 off-policy 蒸馏的 exposure bias 与误差累积；同时每个 token 都获得有意义的梯度，不会像 GRPO / DAPO 那样在整批样本都对或都错时没有信号。

### 训练配置与实现细节

- 在 Qwen3.5-4B/9B（non-thinking 模式）上用 $6.2$K 合成数据训练。
- 散度取 JSD（$\beta = 0.5$），并用 top-$K$ 蒸馏近似：只算 student 的 top-$K$ 个 logits 及 teacher 对应 logits，再加一个 tail-probability 项覆盖剩余概率质量；$K=100$ 时被截断的尾部概率小于 $1\times10^{-13}$。
- teacher 用指数滑动平均（EMA）正则化，更新系数 $\alpha = 0.05$。
- on-policy 最大生成长度 $1024$，训练 $1$ 个 epoch。
- 与候选基线的关系：SFT 在特权裁剪图输入的轨迹上训练（off-policy，有分布错配）；GRPO / DAPO 只有序列级二元奖励且需要真值标签与 verifier；OPSD 同样做 on-policy 自蒸馏，但依赖 ground-truth 标签提供奖励信号。

## Pipeline Figure

![[assets/pipeline_2605.18740.png]]

左：在证据裁剪图上生成细粒度问题，再通过 bounding box 叠加 grounded 回全图；右：同一 MLLM 实例化出 teacher 策略 $p_T(\cdot \mid x_{\text{crop}})$ 与 student 策略 $p_S(\cdot \mid x_{\text{global}})$，student 生成 on-policy rollout $y \sim p_S$，沿线逐 token 的 $D(p_T \| p_S)$ 提供稠密监督，梯度只穿过 student 的 logits。

## Experiments

### 设置

- **细粒度视觉理解基准**：V* Bench（复杂场景中定位并识别极小目标）、ZoomBench（问题依赖不同 zoom 层级的细节）、HR-Bench 4K/8K（高分辨率感知）、MME-RealWorld EN/CN（真实场景高分辨率照片）。
- **holdout 任务**：MMVP、CV-Bench、MMStar、POPE，用于检查细粒度专门化之后是否保留通用多模态能力。
- **对照基线**：一是 SOTA 模型，包括 Thinking-with-Images 的 agentic 方法（DeepEyes、Thyme、DeepEyesV2、SenseNova-MARS）、闭源模型（GPT-5.2、GPT-5.4、Gemini-3.5-Flash、Gemini-3.1-Pro）以及不同规模的开源模型（MiMo-VL-7B-RL、Qwen3-VL-Instruct、ZwZ、MiniCPM-V-4.5、GLM-4.6V、Qwen3.5、Kimi-K2.6）；二是同数据同骨干的替代训练策略（SFT on Self-Teacher、GRPO、DAPO、OPSD）。
- 所有对比都使用 Qwen3.5 系列的 non-thinking 模式；agentic 基线需要多次裁剪/搜索迭代，而 Vision-OPD 只有一次前向。

### 与 SOTA 模型的主结果

![[assets/experiment_table_2605.18740_t1.png]]

作者的结论：Vision-OPD 相对同尺寸 Qwen3.5 基线在所有基准上都提升；Vision-OPD-9B 平均分 $79.68$，超过 Qwen3.5-397B（$77.44$）、Kimi-K2.6、GLM-4.6V、GPT-5.4 与 Gemini-3.1-Pro，并在 V* Bench 与 ZoomBench 上取得最高值；$4$B 版本平均 $77.07$，同样超过大多数更大的开源模型和 GPT-5.4，可与 Gemini 系列相比。同时可以看到，在 HR-Bench 4K 与 MME-RealWorld EN 上 Gemini-3.1-Pro / 3.5-Flash 仍然更高。附录的推理速度对比显示，Vision-OPD-9B 在 ZoomBench 上的推理速度是所比方法中最快的，因为它只需单次前向。

### 与替代训练策略的对比及泛化性

![[assets/experiment_table_2605.18740_t2.png]]

作者强调两点：其一，Vision-OPD 在细粒度任务上一致优于 SFT on Self-Teacher、GRPO、DAPO 与 OPSD；其二，它避免了「性能--遗忘」权衡——SFT on Self-Teacher 出现严重遗忘，GRPO / DAPO 也让 holdout 指标下降，而 Vision-OPD 在 MMVP、CV-Bench、MMStar、POPE 上保持或改善原有能力。与同样做 on-policy 自蒸馏、但依赖真值标签的 OPSD 相比，Vision-OPD 在细粒度任务和 holdout 任务上都更强。

### 消融与分析

![[assets/experiment_table_2605.18740_t3.png]]

**teacher 正则化是必需的。** 不加任何正则化、直接用当前策略当 teacher 时训练完全发散，各基准接近零（平均 $0.59$）；冻结初始策略作为 teacher 已经能给出强信号（平均 $79.40$）；trust-region 正则化平均 $79.22$；EMA 正则化最好（平均 $79.68$），因此后续实验统一取 $\alpha = 0.05$ 的 EMA。

![[assets/experiment_table_2605.18740_t4.png]]

**散度选择。** JSD（$\beta = 0.5$）优于 forward KL 与 reverse KL（平均 $79.68$ vs. $78.70$ / $78.53$）。

![[assets/experiment_table_2605.18740_t5.png]]

**生成长度影响监督量。** 目标函数作用在 token 级，每个样本生成的 token 数直接决定可用监督信号的多少；从 $512$ 提升到 $1024$ token 带来一致的性能提升（平均 $78.62 \to 79.68$），因此最终采用 $1024$。

![[assets/experiment_table_2605.18740_t6.png]]

**稠密 logit 监督优于标量 shaping。** 把 per-token 散度换成只在 student 采样 token 上评估 teacher/student log-prob 比的 policy-gradient 式目标后，整体性能下降（平均 $78.62$ vs. $79.68$），说明 logit 级 credit assignment 比把 teacher log-prob 当作标量 advantage 更有效。

**regional-to-global gap 在训练中持续收窄。** 作者在每个 checkpoint 上用同一问题分别以全图和证据裁剪图为输入作答，跟踪二者的准确率差；差距稳步下降，最终 Vision-OPD 模型的 gap 小于许多更大或闭源模型，说明模型学会了直接在全图中恢复裁剪图可见的证据。

## Limitations & Caveats

论文正文没有单列 limitations 章节，以下是论文陈述与表格数据支持的限制与保留意见：

- **数据构造仍依赖外部大模型**：训练目标本身不依赖外部 teacher，但问题生成（以及为基线生成伪标签）都使用 Qwen3.5-397B，因此整条 pipeline 并非完全自足；合成数据的分布也受该模型能力约束。
- **并非在所有子集上都最强**：在 HR-Bench 4K 与 MME-RealWorld EN 上，Gemini 系列（闭源、单次前向）仍高于 Vision-OPD-9B，作者也只在「平均分与部分基准」上声称超越。
- **稳定性依赖 teacher 正则化**：不使用正则化时训练完全崩溃（平均 $0.59$），说明该自蒸馏目标本身不稳定，需要 EMA 或 trust-region 这类机制来防止 teacher 与 student 共同漂移。
- **训练输入需要红框与空间提示词**：student 训练时看的是叠加 bounding box 的全图并附带空间约束，这与纯自然图像推理仍存在细微输入差异（推理时不再需要该提示）。
- **超参与规模敏感性未覆盖**：区域面积比阈值 $\tau$、裁剪放大倍数 $2\times$、top-$K$ 的 $K$、合成数据量等都缺少敏感性分析；论文未报告训练算力开销，也只在 Qwen3.5-4B/9B 的 non-thinking 模式上验证。
- **对比口径**：与闭源模型及 agentic 方法的对比建立在各自默认配置之上，agentic 基线还额外消耗多次前向；这类跨方法比较应谨慎解读。

## Concrete Implementation Ideas

- **top-$K$ JSD 实现**：对 student logits 取 top-$K$（$K=100$）做 partial softmax，再取出 teacher 对应 token 的 logits 参与同一归一化，并补一个 tail-probability 项处理剩余概率质量；这样避免全词表 logit 蒸馏的显存开销，同时保留近乎完整的分布信息。
- **teacher 更新**：teacher 与 student 从同一 checkpoint 初始化，teacher 只做 EMA（$\alpha = 0.05$）并 `stopgrad`；如果拟合不稳定，可先把 teacher 冻结在初始权重（论文中它已有平均 $79.40$ 的表现）作为退路。
- **监督密度优先于训练步数**：由于目标是 token 级，先保证 rollout 长度（$1024$ 优于 $512$）比增加 epoch 更划算；论文只用 $1$ 个 epoch、$6.2$K 样本。
- **训练监控指标**：训练过程中同时用全图与证据裁剪图评测同一批问题，把 regional-to-global gap 当作直接对齐目标，而不仅看最终 benchmark 分数。
- **数据侧可复用点**：object identification + segmentation 生成候选框，按面积占比 $\tau$ 过滤小区域，用强模型生成区域可回答问题，再用红框叠加 + 空间约束把问题 grounded 回全图；标签侧用多数投票共识（$>0.75$）过滤。
- **可迁移场景**：任何「局部证据 + 全局输入」的形态都适用同一模板，例如文档细节问答、工业缺陷检测问答、医疗影像局部病灶描述，只要能为同一问题构造出「干净局部视角」与「完整输入视角」两种条件。

## Open Questions / Follow-ups

- 区域面积阈值 $\tau$、裁剪放大倍数（$2\times$）与红框叠加形式对最终效果有多敏感？是否存在比「单边框 + 空间提示」更好的 privileged view 构造方式？
- 目前每个样本只对应一个证据区域。扩展到多区域、多步 zoom 的自蒸馏（即把 agentic 的多轮裁剪轨迹内化）该如何定义 teacher 的条件视角？
- Vision-OPD 与 RLVR（GRPO / DAPO）在信号上是互补的（稠密 token 监督 vs. 序列级可验证奖励），二者结合是否能同时提升细粒度性能与通用能力？
- 该方法是否在更大骨干（$>9$B）与 thinking 模式下同样有效？论文只在 Qwen3.5-4B/9B 的 non-thinking 模式上验证。
- 训练数据量从 $6.2$K 继续放大是否有持续收益？数据合成的质量（问题是否真的只能由该区域回答）如何量化与控制？
- 论文提到 teacher 不加正则会崩溃，但未给出稳定性分析；EMA 系数 $\alpha$ 与 trust-region 半径的理论依据仍然开放。

## Citation

```bibtex
@misc{yuan2026visionopd,
  title  = {Vision-OPD: Learning to See Fine Details for Multimodal LLMs via On-Policy Self-Distillation},
  author = {Qianhao Yuan and Jie Lou and Xing Yu and Hongyu Lin and Le Sun and Xianpei Han and Yaojie Lu},
  year   = {2026},
  eprint = {2605.18740},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV},
  url    = {https://arxiv.org/abs/2605.18740}
}
```

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
