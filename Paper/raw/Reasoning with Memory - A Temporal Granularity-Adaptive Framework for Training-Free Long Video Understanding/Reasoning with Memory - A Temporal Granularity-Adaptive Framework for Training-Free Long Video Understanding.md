---
title: "Reasoning with Memory: A Temporal Granularity-Adaptive Framework for Training-Free Long Video Understanding"
authors:
  - Linghao Meng
  - Qiankun Li
  - Junyuan Mao
  - Pujin Liao
  - Zhicheng He
  - Enbo Zhang
  - Kun Wang
  - Yang Liu
  - Huazhu Fu
  - Yueming Jin
conference: ECCV 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2607.24794
pdf_link: "[[assets/paper_2607.24794.pdf]]"
cover: "[[_assets/images/pipeline_2607.24794.png]]"
updated: 2026-09-05
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - option-aware
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/jinlab-imvr/ReMem
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

- **问题**：长视频的全部帧无法装入 MLLM 的上下文。Uniform Sampling 容易漏掉关键证据，按问题与单帧的静态相似度取 Top-K 又容易集中在同一段高分片段，缺少回答计数、先后关系和跨事件问题所需的时间覆盖。
- **方法**：ReMem 先用 GPT-4o 判断问题需要的时间跨度、从问题与选项中提取视觉实体，再融合 CLIP 静态相关性和视频记忆图传播分数，最后通过时空事件聚类分配固定帧预算。它是置于 Video-LLM 前端的 training-free 选帧框架。
- **Memory 的具体含义**：query level 使用 LLM 已有的知识与语义联想能力；video level 使用当前视频的代表帧及其语义、时间连接构成显式图。论文没有描述跨视频累积的持久记忆库。
- **主要证据**：在四个无字幕选择题基准、三个 Video-LLM 上评估。作者报告，LLaVA-Video 使用 64 帧时，LVBench 达到 54.5%，LongVideoBench 达到 67.1%，相对其基线分别提高 12.3 和 8.2 个百分点。
- **阅读判断**：结构化选帧的实验收益值得关注，但要区分性能证据与机制解释。融合权重公式和正文的时长变化解释相反；若要复现，还需核对投影矩阵来源和若干未给定的超参数。

## Key Contributions

1. **把问题的时间粒度显式引入选帧**。连续变量 $g$ 区分局部视觉事实与需要较大时间覆盖的问题，尝试让同一视频针对不同问题采用不同的证据组合。
2. **结合两种帧相关性**。Static Visual-Semantic Alignment（VSA）提供直接的视觉定位；Memory Augmented Temporal-Semantic Alignment（TSA）通过代表帧图传播问题相关信号，将跨场景联系纳入评分。
3. **从逐帧排序推进到事件级预算分配**。Structure-Aware Dynamic Frame Routing（FR）在候选池内同时考虑语义和时间位置，先划分事件，再决定每个事件保留多少帧，最后按时间排序交给 MLLM。

作者将贡献定位为无需任务专属训练的即插即用框架。Related Work 将它与学习式 selector、扩展 Video-LLM 上下文的方法，以及 AKS、Q-Frame、FlexSelect、BOLT、MDP3 等 training-free 选帧方法对照；“既有方法忽略时序”的概括属于作者的研究定位，不能据此认定所有比较方法完全没有时间建模。

## Method

### Task and notation

输入是长视频、问题 $Q$ 和候选答案 $\{C_i\}$，输出是选择题答案。先以 **1 fps** 均匀采样，得到 $M$ 帧，再提取 CLIP 特征。以下数量分别控制不同阶段：$M$ 是初始帧数，$K=\sqrt M$ 是记忆锚点数，$N=150$ 是候选池容量，$L$ 是候选池中的事件数，$B$ 是最终送入 MLLM 的帧预算。

论文的整体处理顺序可概括为：问题解析 → 文本增强与视频记忆图 → 双语义评分 → Top-$N$ 候选池 → 事件聚类 → 预算分配 → 按时间排序 → Video-LLM 回答。候选池容量 $N$ 与最终输入帧数 $B$ 不能混用。

### Memory-Driven Question Parsing

**Granularity Analysis** 用 reasoning LLM 将问题映射到 $g\in[0,1]$。较小 $g$ 表示只需在较窄时间窗口内寻找密集证据；较大 $g$ 表示需要跨较长时间整合信息。例如，论文将“太阳在视频中出现多少次”设为 $g=0.90$。这个值由问题解析得到，并非通过额外监督训练的分类器预测。

**Entity Extraction（EE）** 同时读取 $Q$ 与 $\{C_i\}$，提取更容易视觉匹配的对象、动作或特征。因此选帧具有 option-aware 属性。论文的足球计数例子将抽象问题扩展成庆祝动作、球网变化、球衣号码等线索；这些是 LLM 建议用于检索的视觉特征，并不表示模型已经在视频中确认了它们。

### Query enhancement and static alignment

CLIP 分别编码问题向量 $\mathbf v_q$ 和实体向量集合 $\mathbf v_e$。Query Enhancement 以 cross-attention 将实体信息注入问题表示：问题经 $W_q$ 投影作为 query，实体经 $W_k,W_v$ 投影作为 key/value；attention 输出与原问题拼接，经 $W_f$ 融合，再通过残差与 Layer Normalization 得到增强查询锚点 $\mathbf v_{anc}$。作者希望借此减少抽象问句对视觉检索的干扰。

对每一帧 $\mathbf v_i$，VSA 的原式为：

$$
\mathcal S_v(\mathbf v_i,\mathbf v_{anc})=
\alpha\frac{(W_s\mathbf v_{anc})^\top(W_s\mathbf v_i)}
{\|W_s\mathbf v_{anc}\|_2\|W_s\mathbf v_i\|_2}
+\beta\left(\frac{\mathbf v_{anc}^\top W_c\mathbf v_i}{\sqrt D}\right)^2.
$$

第一项是投影后的余弦相似度，第二项加入平方形式的双线性相关性。论文称 $W_s,W_c$ 继承自预训练 CLIP；其具体参数对应关系以及 query enhancement 各投影权重的来源没有充分展开。原文还在不同模块复用 $\alpha,\beta$，下列公式保留这种记号，但复现时需要核对各处参数是否共用。

### Memory Augmented Temporal-Semantic Alignment

先对 $M$ 个视觉特征做 K-Means，得到 $K=\sqrt M$ 个簇。每个簇选择距离质心最近的**真实帧**作为锚点，避免直接以抽象均值充当视频证据。锚点按时间排序，堆叠成矩阵 $V\in\mathbb R^{K\times D}$。

图中有两类边：

$$
e_{sem}^{i,j}=\max(\mathbf V_i^\top\mathbf V_j,0),
\qquad
e_{tem}^{i,j}=\mathbf 1[|i-j|\leq1].
$$

语义边连接视觉上相关的锚点；时间边连接按时间排序后的相邻锚点，并包含自连接。这里的邻接依据是锚点序号，不是直接用实际时间间隔加权。对两类边分别作 $L_1$ 归一化，得到 $W_{sem}$ 和 $W_{tem}$。

用增强查询初始化种子分布 $\mathbf p^{(0)}=\operatorname{Softmax}(V\mathbf v_{anc})$，随后做带 restart 的图传播。为区分视频时长，下面仅将原文的扩散步下标改记为 $r$：

$$
\mathbf p^{(r+1)}=(1-\gamma)
\bigl(\alpha W_{sem}+(1-\alpha)W_{tem}\bigr)\mathbf p^{(r)}
+\gamma\mathbf p^{(0)}.
$$

$\gamma\in(0,1)$ 是 restart probability；每次传播都保留一部分由问题直接激活的分布。论文固定传播 **2 步**，再将锚点的重要性映射回原始帧：

$$
\mathcal S_t(\mathbf v_i,\mathbf v_{anc})
=\sum_{k=1}^{K}(\mathbf v_i^\top\mathbf V_k)p_k^{(2)}.
$$

这一分数衡量帧与“经过问题激活及图传播后的代表状态”的关联。作者用它解释跨事件证据覆盖；单凭这种语义与邻接图，尚不能将边直接解释为已识别的因果关系。

### Granularity Guided Dual-Semantic Fusion

原文将静态分数与图传播分数结合：

$$
\alpha=1-0.5g e^{-\lambda t},
\qquad
\mathcal S=\alpha\mathcal S_v+(1-\alpha)\mathcal S_t,
$$

其中 $t$ 是视频时长，$\lambda=10^{-4}$。固定时长时，较大的 $g$ 会降低 $\alpha$，增加 temporal-semantic 分量，这与作者对问题粒度的解释相符。随后按 $\mathcal S$ 选 Top-$N$ 帧，形成候选池。

**但对视频时长的解释存在冲突**：原文称视频越长，$\alpha$ 越低，而上述公式在 $g>0,\lambda>0$ 时给出相反趋势。此处忠实保留原式，不能将作者描述的时长自适应行为视为已由公式实现；详细核对见 Limitations & Caveats。

### Structure-Aware Dynamic Frame Routing

**事件聚类**：在候选池内联合优化软分配矩阵 $U\in[0,1]^{N\times L}$、语义中心 $\mathbf c_l$ 和时间中心 $\tau_l$：

$$
\min_{U,\mathbf c,\boldsymbol\tau}\mathcal L_{cluster}
=\sum_{i=1}^{N}\sum_{l=1}^{L}U_{i,l}
\left(1-\mathbf v_i^\top\mathbf c_l+\beta(t_i-\tau_l)^2\right)
-\epsilon\mathcal H(U),
$$

$$
\mathcal H(U)=-\sum_{i,l}U_{i,l}\log U_{i,l}.
$$

语义项鼓励视觉相近，时间项鼓励事件在时间上紧凑，熵项控制软分配。随后用 $\arg\max_l U_{i,l}$ 得到事件集合 $G_l$。这里优化的是当前输入的聚类变量；论文没有将该过程描述为更新 Video-LLM 的模型参数。

**预算分配**：按事件内累积的双语义分数与规模项计算 $I_l$，再经 softmax 分配 $B$ 帧：

$$
I_l=\sum_{i\in G_l}\mathcal S_i+\eta\log(1+|G_l|),
\qquad
m_l=B\frac{\exp(I_l/\theta)}{\sum_{j=1}^{L}\exp(I_j/\theta)}.
$$

$\theta$ 控制分配的集中程度。论文将 $m_l$ 四舍五入，并在每个事件内按 $\mathcal S$ 取 Top-$m_l$ 帧。所有保留帧最终按时间顺序排列，与 system prompt 和 query 一起送入 MLLM。作者将 $\eta$ 项称作冗余采样惩罚，但若 $\eta>0$，原式的规模项会随簇大小增加；其符号与实际作用仍需核对。

## Pipeline Figure

![[_assets/images/pipeline_2607.24794.png]]

图中左侧由问题与选项得到时间粒度和实体，中部构造并激活视频记忆图，下方按事件重分配帧预算，右侧调用 MLLM 回答。框架图也使用了与正文相同、需要核对时长趋势的融合权重公式。

## Experiments

### Evaluation setup

评估覆盖 **LVBench、MLVU、LongVideoBench、Video-MME**，任务统一为不提供字幕的 multiple-choice QA，指标为答案选择准确率。Video-MME 还分别报告 Short、Medium、Long 子集。作者希望通过去掉字幕侧重考察视觉理解，但实体提取仍使用问题和答案选项。

- **LLaVA-Video-7B-Qwen2**：最终输入预算 $B=64$。
- **Qwen2-VL-7B-Instruct、Qwen3-VL-8B-Instruct**：最终输入预算 $B=32$。
- **选择器配置**：GPT-4o 负责问题解析，OpenAI CLIP-L-14 提取视觉和文本表示，初始采样 1 fps，候选池 $N=150$，衰减常数 $\lambda=10^{-4}$。作者报告实验为 zero-shot、training-free，使用 $8\times$ NVIDIA H200；这不是对最低部署硬件的证明。

比较对象既包含 Video-LLM，也包含 Uniform Sampling、AKS、FlexSelect-Lite、Q-Frame、BOLT，以及需训练的 GenS、Selector、FrameOracle 等。各方法的帧数并不全部相同，应结合原表的帧预算理解比较。

### Main comparisons

![[_assets/images/experiment_table_2607.24794_t1.png]]

以下是作者明确报告且与表中数值一致的主要比较；“提升”使用准确率百分点，不能读成相对百分比增长：

- **LLaVA-Video**：LVBench 从 42.2% 到 54.5%，LongVideoBench 从 58.9% 到 67.1%；作者分别报告提高 12.3、8.2 个百分点。MLVU 达到 77.3%，作者报告相对基线提高 6.5 个百分点。
- **Qwen2-VL**：在 MLVU 上，ReMem 为 72.8%，GenS 为 66.9%；作者报告 5.9 个百分点优势。不过两者在表中分别使用 32 帧和 54 帧。
- **Qwen3-VL**：MLVU 的基线为 63.6%，接入 ReMem 后为 77.6%；LVBench 达到 53.3%，作者报告相对基线提高 10.6 个百分点。
- **较长视频上的证据**：LLaVA-Video 在 Video-MME Long 子集上，AKS 为 54.1%，ReMem 为 61.8%；作者报告提高 7.7 个百分点。这是与表格对应的 Long 子集比较。

正文还用 Qwen2-VL 的 Q-Frame 57.1% 和 ReMem 65.7% 讨论扩展时长的表现。**两者在原表中属于 Medium 列**，不应转述为 Long 子集成绩；相应 Long 列的数值是 48.3% 和 55.8%。

### Component ablations

![[_assets/images/experiment_table_2607.24794_t2.png]]

四个消融因素分别为 EE、VSA、TSA 和 FR。表中每行去掉一个模块，完整配置作为参照；绿色上箭头表示与完整配置对照的恢复幅度，而不是被删除的模块带来了提升。

作者将 VSA 视为核心 grounding 机制：LLaVA-Video 在 LVBench 上去掉 VSA 后为 41.6%，完整配置为 54.5%，表中标注 12.9 个百分点差距。加入 EE 的收益较小但持续存在，作者报告 LVBench 和 MLVU 分别提高 2.2、1.5 个百分点。TSA 与 FR 的消融也支持保留跨帧关联及事件级预算分配的价值。

Qwen2-VL 的图示消融提供跨模型佐证：作者报告加入 TSA 后，Video-MME、MLVU、LVBench 分别提高 5.8、5.4、7.3 个百分点；用 FR 替代全局 Top-K 后，MLVU 提高 6.8 个百分点。这些结果支持模块在已测设置中的作用，不能单凭单模块删除实验推导所有模块组合的交互机制。

### Candidate pool and sensitivity

![[_assets/images/experiment_table_2607.24794_t3.png]]

这里改变的是**路由之前的候选池容量**，最终输入预算保持不变。作者在测试范围内选择 $N=150$：Video-MME 准确率为 69.2%，选帧预处理耗时 18.7 秒；LongVideoBench 为 67.1%，预处理耗时 15.2 秒。作者认为过大的候选池会引入低相关帧、干扰聚类；表格支持“继续增大候选池并不必然更好”，但没有独立测量这一噪声机制。

衰减常数实验考察 $10^{-5}$ 至 $10^{-2}$，作者最终采用 $\lambda=10^{-4}$。其解释涉及“时长增加时静态权重衰减”，但这一解释受前述公式冲突影响。连续粒度还与固定二分类权重进行比较：短期问题取 $\alpha=0.9$，长期问题取 $\alpha=0.5$；作者报告连续机制在 LongVideoBench 上分别使 Qwen2-VL、LLaVA-Video 提高 3.3、2.6 个百分点。

### Efficiency and qualitative evidence

作者承认 ReMem 的端到端时延高于 Uniform Sampling 与 AKS。效率图中，LLaVA-Video 在 Video-MME 上的每题时延分别为 11.1、17.4、25.8 秒；在 LongVideoBench 上分别为 7.1、15.7、21.8 秒。这里是端到端时间，不能与候选池实验的选帧预处理时间混为一谈。作者强调准确率与时延的取舍，以及相同视频问题的选帧索引在不同 backbone 间复用的可能性；论文没有展开不同帧预算之间具体如何复用。

定性案例展示了两种时间推理需求：一是仅关注陶瓷烧制完成之后的操作，ReMem 保留了上色绘画的关键证据；二是对多个事件排序，完整方法保留了老人面部、儿童互动、墙上昆虫和跳舞等锚点。后一个案例里去掉 EE 仍回答正确，说明整体平均收益与单题是否必需是不同问题。案例说明了作者希望改善的失败模式，并非系统性的错误类型统计。

## Limitations & Caveats

论文未单列 Limitations 节。以下将作者已讨论的取舍与依据原文可直接核对的问题分开说明。

### Reported trade-offs and evaluation scope

作者明确报告额外选帧时延，以及候选池过大时准确率下降。当前证据范围是三个既有 Video-LLM、四个无字幕选择题基准；不能直接外推为开放式问答、在线流式视频、音频推理或任意新 backbone 的保证。论文使用 GPT-4o 解析问题，但没有单独隔离解析模型强弱或选项信息的贡献。

初始 $1$ fps 采样也是方法的证据入口：后续选择器只能在已经采到的帧内检索。因此，采样阶段未记录的短暂事件无法仅靠后续路由恢复。这是由流程得到的边界判断，不是论文另行测得的失败率。

### Formula and interpretation mismatch

**融合权重的时长趋势不一致**。公式（6）以及框架图都写为 $\alpha=1-0.5g e^{-\lambda t}$，正文却称视频越长，$\alpha$ 越低，TSA 占比越高。直接对原式求导可得：

$$
\frac{\partial\alpha}{\partial t}=0.5g\lambda e^{-\lambda t}\geq0,
\qquad \lim_{t\to\infty}\alpha=1.
$$

也就是说，按印刷公式，时间分量 $1-\alpha$ 随时长减弱；当 $g=0$ 时，$\alpha$ 恒为 $1$。敏感性分析关于较大 $\lambda$ 令 $\alpha$ 提前趋近 $0.5$ 的解释也与该式不符。这里的推导只是对原式的一致性检查，无法据此判断作者实验代码究竟实现了哪一种函数，不能擅自给出“修正版”。

**事件容量项的作用不明确**。公式（8）使用正号加入 $\eta\log(1+|G_l|)$，正文称其为冗余惩罚。若 $\eta>0$，这部分会提高较大事件的容量分数。由于未明确其取值与实现，不能直接将该项描述为已证明会减少冗余的惩罚。

### Reproducibility gaps

Query Enhancement 的 $W_q,W_k,W_v,W_f$ 只给出结构和维度，未说明完整的参数来源；VSA 虽称 $W_s,W_c$ 来自 CLIP，也没有明确映射到哪些预训练参数。因此，training-free 是作者声明的实验设定，仍需实现细节支持其完整复现，不能反向臆测这些权重经过训练。

论文没有完整列出 $L,\gamma,\beta,\epsilon,\eta,\theta$ 的数值、时间尺度归一化、聚类优化与停止条件、$K=\sqrt M$ 的整数处理、GPT-4o 的完整解析提示和采样配置。对 $m_l$ 独立四舍五入也不自动保证总和恰为 $B$，或保证每个事件有足够帧可取；预算修正与容量不足的处理未展开。复现需要把这些问题显式解决。

### Strength of the claims

主表中比较方法的帧预算不同，报告也没有提供重复运行方差或置信区间。“SOTA”应理解为作者所报告的比较范围，不能延伸成对全部同等算力设置的结论。作者进一步将结果解释为数学建模优于强监督训练，但这些实验尚不足以推出训练范式的一般性优劣。

视频记忆图由语义相似和时间邻接构建，没有因果边监督或显式因果识别目标。作者关于“preserving causal structures”的表述应视为机制解释；更稳妥的结论是，它在已测任务中改善了时序相关证据的选取与最终答题准确率。

## Concrete Implementation Ideas

以下是基于论文流程的复现建议，尚未在本次阅读中执行实验或核对代码实现。

1. **先固定证据与配置**：缓存每个视频的 $1$ fps 帧索引、时间戳和 CLIP 特征；对每个问题保存 GPT-4o 的粒度、实体、提示及模型配置。这样可以将问题解析的变化与视觉路由的变化分开比较。
2. **逐阶段保存可检查输出**：记录代表锚点、两类归一化图、种子分布、两步传播结果、VSA/TSA 分数、Top-$N$ 候选帧、事件划分及配额。首先核对所有投影参数的来源，再比较最终准确率。
3. **先解决公式冲突再做消融**：核对作者实现中 $\alpha(g,t)$ 的函数、时长单位及极限行为。若后续选择测试不同函数，应明确标为实验变体，不能将自行修改的函数称为论文原实现。
4. **把帧预算约束做成显式检查**：确保保留帧无重复、每事件配额不超过容量、总数符合 $B$、输出时间单调。若实现需要补余数或重新分配，应记录所采用的规则，因为这些规则并未由论文完整指定。
5. **拆开计时并控制比较条件**：分别记录问题解析、视频编码、图构建与路由、MLLM 推理的时间。在同一 backbone 和相同 $B$ 下比较 Uniform Sampling、静态评分、加入 TSA、加入 FR 的差异，再讨论跨模型复用。

## Open Questions / Follow-ups

- 作者实现中的时长权重到底对应公式还是文字解释？不同模块复用的 $\alpha,\beta$ 是否同一参数，投影权重来自哪里？
- 在相同预算下，只用问题提取实体、同时使用选项、以及去掉 GPT-4o 推理，分别会怎样影响选帧？当前消融没有完全分开这些因素。
- 当关键动作短于初始采样间隔，或问题要求精确计数重复事件时，$1$ fps 入口与两步图传播的覆盖边界在哪里？
- 若按问题类型系统评估事件覆盖、时间顺序和答案准确率，FR 的收益主要来自减少同段冗余、扩大事件覆盖，还是其他因素？
- 在不同长度的视频和不同最终预算下，固定 $N=150$、固定扩散步数及未知事件数 $L$ 的选择如何扩展？不同 $B$ 的 backbone 之间可以复用到哪一层中间结果？

## Citation

Linghao Meng, Qiankun Li, Junyuan Mao, Pujin Liao, Zhicheng He, Enbo Zhang, Kun Wang, Yang Liu, Huazhu Fu, and Yueming Jin. **Reasoning with Memory: A Temporal Granularity-Adaptive Framework for Training-Free Long Video Understanding**. 2026. arXiv:2607.24794，当前获取版本为 v1；arXiv 元数据注明 Accepted by ECCV 2026。

[arXiv](https://arxiv.org/abs/2607.24794) · [作者代码链接](https://github.com/jinlab-imvr/ReMem) · [[assets/paper_2607.24794.pdf|Local PDF]]

```bibtex
@article{meng2026reasoningmemory,
  title = {Reasoning with Memory: A Temporal Granularity-Adaptive Framework for Training-Free Long Video Understanding},
  author = {Meng, Linghao and Li, Qiankun and Mao, Junyuan and Liao, Pujin and He, Zhicheng and Zhang, Enbo and Wang, Kun and Liu, Yang and Fu, Huazhu and Jin, Yueming},
  journal = {arXiv preprint arXiv:2607.24794},
  year = {2026},
  doi = {10.48550/arXiv.2607.24794},
  url = {https://arxiv.org/abs/2607.24794}
}
```

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
