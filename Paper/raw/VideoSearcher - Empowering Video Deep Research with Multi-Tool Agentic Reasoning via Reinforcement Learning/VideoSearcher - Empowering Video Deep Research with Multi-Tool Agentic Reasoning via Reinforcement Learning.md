---
title: "VideoSearcher: Empowering Video Deep Research with Multi-Tool Agentic Reasoning via Reinforcement Learning"
authors: ["Zhenkun Gao", "Yicheng Bao", "Jinlong Peng", "Xueheng Li", "Theo Huang", "Bangwei Liu", "Kunquan Li", "Zhenye Gan", "Tao Hu", "Chengjun Xie", "Mingqian Yang", "Xuanhua He", "Zhizhong Zhang", "Xin Tan", "Chengjie Wang", "Yuan Xie"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2607.02927"
pdf_link: "[[assets/paper_2607.02927.pdf]]"
cover: "[[assets/pipeline_2607.02927.png]]"
updated: 2026-09-20
tags: ["paper/arxiv", "video-qa", "long-video", "agent", "rl-reasoning"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://github.com/Stephen-gzk/VideoSearcher"
---

<!-- READ_PAPER_GENERATED_START -->

## TL;DR

- 论文把 **Video Deep Research（VDR）** 定义为：视频只提供视觉锚点（logo、人物、地点、事件场景），答案必须到开放网络上检索与验证，而不是全部藏在视频内部。作者认为这是从 closed-evidence 视频理解走向 open-world 证据探索的范式转变。
- 现有工作不足在于两点：多模态搜索 agent 基本面向静态图像（无法跨帧追踪线索、无法同时决定时间定位与空间聚焦）；唯一的 VDR benchmark（VideoDR）是 text-centric 的——先把视觉线索转成文字描述再检索，丢掉了原始视觉信息。
- 提出 **VideoSearcher**：把五个工具（`choose_frames`、`find_frame`、`zoom_in`、`image_search`、`web_search`）放进同一条闭环推理轨迹，让模型在视频时间轴上逐步收窄、锁定关键帧、放大区域、发起文本/图像检索，最后综合多模态证据作答。
- 提出 **BiSPO（Bi-branch Sequence Policy Optimization）**：在 GSPO 的序列级重要性采样之上，把「答对」和「会用工具」拆成两个奖励分支——准确率分支对全部 rollout 做组内归一化，工具分支只在答对的 rollout 子集内比较，并用 correctness gate 屏蔽错误轨迹的工具行为。
- 工具奖励采用 **bell-shaped** 的边际收益：每类检索的第 $1$–$5$ 次有效搜索给 $[0.35,0.20,0.10,-0.10,-0.25]$，之后每次 $-0.60$，鼓励「够用的检索」而抑制重复、失败与无效调用。
- 数据侧构建了 video-centric 合成 pipeline（实体驱动的视频采集 → 归一化与 QA 对齐 → hard sample mining → 分层轨迹合成 → 质量过滤），得到 $3{,}811$ 条 SFT 轨迹与 $3{,}285$ 条 RL 实例；并开源 **VideoSearch-QA（VSQA）**，$278$ 条人工标注、覆盖 $8$ 个领域的视频-问题对。
- 结果：VideoSearcher-8B 在 VideoDR 上 $53.00$、VSQA 上 $51.80$、八个搜索类基准平均 $57.66$，显著超过开源 agentic 基线（如 zero-shot Qwen3-VL-8B 平均 $41.95$），同时在 MMVU / TempCompass / VideoMMMU / VideoMathQA 等通用视频理解基准上不退化（平均 $60.39$）。

## Key Contributions

- **面向动态视频的闭环 VDR agent**：作者强调 VideoSearcher 是第一个把 temporal localization、spatial focusing 与 multimodal search 统一在一条推理轨迹里的 Video Deep Research agent，而不是把视频理解与图像搜索拼成两段流水线。
- **BiSPO 双分支 RL 算法**：把 answer accuracy 与 tool invocation behavior 的优化解耦。动机是 VDR 轨迹长、工具密集，单一把「答对」和「用工具好」混在一个奖励里时，较弱的工具行为信号会被答案正确性信号淹没，甚至让策略学出「少调用工具的低成本轨迹」。
- **VideoSearch-QA benchmark**：$278$ 条人工标注样本，覆盖 Landmarks、Geography、Natural Scenes、Culture、Sports & Games、Leisure、Technology、Business 八个领域；题目必须结合视频中的视觉锚点与外部检索才能回答，且刻意包含 $2026$ 年的事件类视频以降低预训练记忆的影响。
- **数据合成方法论**：把知识密集型图文 QA 数据集（FVQA、DeepEyes、DeepEyesV2 等）改造成视频形态的 VDR 实例，并用双模型交叉验证实体、visual-QA 对齐校验、hard sample mining、LLM-as-verifier 过滤来保证轨迹质量。
- **实验结论**：在 VideoDR、VSQA 与 MMSearch / HR-MMSearch / FVQA-test / InfoSeek / SimpleVQA / LiveVQA 上全面领先开源 agentic 基线；消融显示「解耦优势估计」与「bell-shaped 工具奖励」两者都必要。

## Method

### 任务形式化

VDR 被建模为开放世界的视频问答：给定视频 $\mathcal{V}$、问题 $q$ 与外部网络证据空间 $\mathcal{W}$，策略 $\pi_\theta$ 需要生成一条多步轨迹 $\tau=(a_1,o_1,\ldots,a_T,o_T)$。每一步先产生 reasoning state，再从动作空间 $\mathcal{A}$ 中选一个动作：`choose_frames`（选粗粒度时间段）、`find_frame`（定位单帧）、`zoom_in`（放大帧内区域）、`web_search`（文本检索）、`image_search`（以帧或裁剪区域做视觉检索）、`answer`（给出最终答案）。观测空间被拆成视频侧观测 $\mathcal{O}^v$ 与网络侧观测 $\mathcal{O}^w$，历史按 $\mathcal{H}_{t+1}=(\mathcal{H}_t,a_t,o_t)$ 累积。轨迹诱导的联合证据集 $\mathcal{E}_\tau=\mathcal{E}^v_\tau\cup\mathcal{E}^w_\tau$ 是最终答案的依据——这一点与传统 video QA 的关键差别是：答案可能根本不在视频里。

合法性与依赖关系被显式约束：`zoom_in` / `image_search` / `web_search` 必须先 `find_frame` 锁定帧；每次 `choose_frames` 会重置帧锁；`zoom_in` 等空间工具使用 $0$–$1000$ 归一化 `xyxy` 坐标；最后一步不能是 `choose_frames`。训练与推理使用同一套 `<think>` / `<tool_call>` / `<answer>` 结构化输出格式，以减少 observation 分布漂移。

### 数据构建：把图文 QA 变成 VDR 实例

pipeline 的五个阶段：

1. **Entity-driven Video Acquisition**：从 FVQA、DeepEyes、DeepEyesV2 等知识密集型图文 QA 数据集（外加人工种子问题）出发，抽取回答问题所必需的核心视觉实体（landmark、logo、person、product、scene 等）。为降低实体歧义，同时询问 Qwen3.5-397B 与 Kimi-K2.5，只保留两者一致识别的实体，再用这些实体去 YouTube、Bilibili 等平台检索相关视频。
2. **Video Normalization and QA Alignment**：所有视频重采样到 $1$ fps，在每帧左上角烧入 ``Frame $N$`` 作为时间参考；把原始图像问题改写成视频语境的问题（同一视频出现多个相似实体时补上区分性的时间或视觉描述）；再做 visual-QA 对齐校验，剔除关键实体缺失、答案被 OCR 直接暴露、视觉锚点不一致、或不需要视频证据就能作答的样本。
3. **Hard Sample Mining**：用 Qwen3-VL-8B-Instruct 在 agentic 设置下多次 rollout，只保留「成功 rollout 数不超过一次」的样本，得到需要时间定位、细粒度观察与外部检索的困难样本。其中 $3{,}285$ 条视频实例留作 RL online rollout，其余用于 SFT 轨迹合成。
4. **Hierarchical Trajectory Synthesis**：用两个专有模型分层生成轨迹——轻量模型用 `choose_frames` 做粗筛，能力更强的模型负责 `find_frame`、可选 `zoom_in`、`image_search`、`web_search` 与证据推理；生成时采用增量视觉上下文策略，每轮只注入新获得的视觉观测，文本推理历史完整保留，以控制视觉 token 成本。
5. **Quality Control**：规则过滤（畸形工具调用、非法帧引用、非法 bbox、失败检索、重复查询、退化重复推理）加 Kimi-K2.5 作为质量验证器（拒绝幻觉证据、结论无支撑、工具观测不一致、推理链断裂），最终得到 $3{,}811$ 条高质量 SFT 轨迹。

### VideoSearch-QA 的构造

与 VideoDR 的 text-centric 评测不同，VSQA 要求 agent 直接从动态视频中识别视觉锚点、用它发起 web / image search 并在多模态证据上推理。视频来源优先「信息量大、动态、多实体、含可检索视觉锚点（landmark、logo、招牌、商品、公众人物、地图、事件场景）」的公开网络视频，并特意收录 $2026$ 年的事件视频。人工标注出 grounded 在具体视频证据上的问题，并独立复核视觉-QA 对齐、难度、多跳推理与「是否真的必须外部检索」；锚点含糊、仅靠识别即可作答、答案无支撑或不需要检索的样本会被修改或剔除。

### 两阶段训练与 BiSPO

**Cold-start SFT**：在 $\mathcal{D}_{\mathrm{SFT}}=\{(x_i,\tau_i^\star)\}$ 上做标准监督微调 $\mathcal{L}_{\mathrm{SFT}}=-\sum_i \log \pi_\theta(\tau_i^\star\mid x_i)$，轨迹包含交错 reasoning、tool call、tool observation 与最终答案，**观测 token 不计入 loss**，只监督模型自己生成的 reasoning / tool-call / answer token。冻结 vision encoder 与 multimodal projector，只微调语言模型，学习率 $1\times10^{-5}$。

**RL 阶段**：旧策略对每个 prompt 采样 $G$ 条轨迹，在同一个 VDR 环境里做在线优化。

- 准确率分支：$R_i^{\mathrm{acc}} = R_i^{\mathrm{judge}} + \lambda_f R_i^{\mathrm{fmt}} + \lambda_d R_i^{\mathrm{dep}}$；附录给出实例化系数被吸收后的形式 $R_i^{\mathrm{acc}} = R_i^{\mathrm{judge}} + R_i^{\mathrm{fmt}} + R_i^{\mathrm{dep}}$，其中 $R_i^{\mathrm{judge}}\in\{0,1\}$ 来自 LLM judge，$R_i^{\mathrm{fmt}}=0.5$ 表示格式合规且没有模型导致的工具错误，$R_i^{\mathrm{dep}}=-\min(0.1N_i^{\mathrm{dep}},0.5)$ 惩罚「未锁定帧就调用 detail/search 工具」的错误顺序。
- 工具分支（correctness-gated）：

$$R_i^{\mathrm{tool}} = \mathbb{I}\!\left[R_i^{\mathrm{judge}} > \delta\right]\cdot \operatorname{clip}\!\left(b+\gamma \sqrt{T_i^{\mathrm{vid}}}+\sum_{m \in \mathcal{M}}\sum_{k=1}^{U_{i,m}}\Delta_k,\ r_{\min},\ 1\right)$$

其中 $T_i^{\mathrm{vid}}$ 是有效视频 grounding 动作数，$\mathcal{M}=\{\mathrm{image},\mathrm{web}\}$，$U_{i,m}$ 是模态 $m$ 下唯一且成功的检索次数，$\Delta_k$ 是第 $k$ 次有效检索的边际奖励。$\Delta_k$ 呈 bell-shaped：早期的有效检索提升工具奖励，过量检索获得负边际收益；失败、空结果或重复的调用不计入也不推进计数。

- 解耦优势估计：$A_i^{\mathrm{acc}} = (R_i^{\mathrm{acc}}-\mu^{\mathrm{acc}})/(\sigma^{\mathrm{acc}}+\epsilon)$ 在全部 $G$ 条 rollout 上做组内归一化；而令 $\mathcal{Q}=\{j \mid R_j^{\mathrm{judge}}>\delta\}$，则

$$A_i^{\mathrm{tool}} = \mathbf{1}\{i\in\mathcal{Q},\ |\mathcal{Q}|\ge 2\}\frac{R_i^{\mathrm{tool}}-\mu_{\mathcal{Q}}^{\mathrm{tool}}}{\sigma_{\mathcal{Q}}^{\mathrm{tool}}+\epsilon}$$

只在答对的子集内比较工具行为。当正确 rollout 少于 $2$ 条时跳过工具分支，只更新准确率分支——避免把错误轨迹里的工具行为与真正支撑正确答案的证据获取行为放在一起比较。

- 序列级目标：长 VDR 轨迹含大量 reasoning token 与工具条件上下文，token 级裁剪不稳定，因此沿用 GSPO 的序列级重要性比

$$s_i(\theta)=\exp\!\left(\bar{\ell}_i(\theta)\right),\quad \bar{\ell}_i(\theta)=\frac{1}{|y_i|}\sum_t\!\left[\log \pi_\theta\!\left(y_{i,t}\mid x_i,y_{i,<t}\right)-\log \pi_{\theta_{\mathrm{old}}}\!\left(y_{i,t}\mid x_i,y_{i,<t}\right)\right]$$

$$\mathcal{L}_{\mathrm{GSPO}}(A)=-\mathbb{E}_i\!\left[\min\!\left(s_i(\theta)A_i,\,\tilde{s}_i(\theta)A_i\right)\right],\quad \tilde{s}_i(\theta)=\operatorname{clip}\!\left(s_i(\theta),1-\epsilon_{\mathrm{low}},1+\epsilon_{\mathrm{high}}\right)$$

两个分支只在损失层面合并：

$$\mathcal{L}_{\mathrm{BiSPO}} = w_{\mathrm{acc}}\mathcal{L}_{\mathrm{GSPO}}\!\left(A^{\mathrm{acc}}\right) + w_{\mathrm{tool}}\mathcal{L}_{\mathrm{GSPO}}\!\left(A^{\mathrm{tool}}\right)$$

论文设定 $w_{\mathrm{acc}}=1.0$、$w_{\mathrm{tool}}=0.15$。

### 关键超参与评测设置（附录）

- SFT：bf16，学习率 $1\times10^{-5}$，冻结 vision encoder 与 multimodal projector。
- RL：prompt batch size $64$，每 prompt $4$ 条 rollout，actor 学习率 $1\times10^{-5}$，最大响应长度 $16{,}384$ token，最大上下文长度 $49{,}152$ token，最多 $12$ 个 assistant turn；非对称裁剪 $\epsilon_{\mathrm{low}}=0.2$、$\epsilon_{\mathrm{high}}=0.28$；**不使用额外的 KL reward / KL loss**；RL 阶段冻结 vision tower，训练 $1$ 个 epoch。
- 工具奖励：非检索的视频 grounding 项取 $b=0.3$、$\gamma=0.35$；image search 与 web search 分别计数，每类第 $k=1,\dots,5$ 次有效检索的边际奖励为 $[0.35,0.20,0.10,-0.10,-0.25]$，此后每次 $-0.60$；最终工具分裁剪到 $[-1.0,1.0]$；correctness gate 阈值 $\delta=0$。
- 评测：VideoDR 与 VSQA 开放全部五个工具；图像类多模态搜索基准只给 `zoom_in` / `image_search` / `web_search`；通用视频理解基准沿用五工具环境。推理时初始给 $64$ 帧均匀采样，解码用 temperature $0.7$、top-$p=0.8$、top-$k=20$，最多 $12$ 轮。开放式答案用 Qwen3.5-27B 作为自动 judge，选择题用 exact match。

## Pipeline Figure

![[assets/pipeline_2607.02927.png]]

左侧是 agent 侧：输入视频被归一化到 $1$ fps 后，`choose_frames` 先粗选一段（例中 start frame $7$ / end frame $18$），`find_frame` 锁定关键帧（例中 frame id $9$），`zoom_in` 放大帧内区域，必要时对裁剪区域做 `image_search`、对已识别实体做 `web_search`，最后在 `<think>` 中综合证据并输出 `<answer>`。右侧是训练侧：$G$ 条 rollout 的 Answer 正确性经 Correct-answer Gate 分成两支，Accuracy Branch 对全部 $G$ 条做 Group Normalization 得到 $A_i^{\mathrm{acc}}$ 与 $\mathcal{L}_{\mathrm{GSPO}}(A^{\mathrm{acc}})$，Tool Behavior Branch 只在答对的 $N$ 条上做 Group Normalization 得到 $A_i^{\mathrm{tool}}$ 与 $\mathcal{L}_{\mathrm{GSPO}}(A^{\mathrm{tool}})$，按 $w_{\mathrm{acc}}=1.0$、$w_{\mathrm{tool}}=0.15$ 合并成 BiSPO total loss 回传更新 policy VLM；图中示意的那条先升后降曲线即 bell-shaped 检索边际奖励。

## Experiments

### 设置

- 骨干与训练：VideoSearcher 初始化自 Qwen3-VL-8B-Instruct（论文主表同时报告 4B 与 8B 两个版本，其 $\Delta$ 行分别标注为对照 Qwen3-VL-4B-Instruct 与 Qwen3-VL-8B-Instruct）。SFT 用 LLaMA-Factory，在线 RL 用 veRL，RL 从 SFT checkpoint 出发训练 $1$ 个 epoch。
- 基准：VDR 类为 VideoDR（评测使用 $2026.01.14$ 发布的 $100$ 条子集）与自建 VSQA；多模态搜索类为 MMSearch（$171$ 条图像题）、HR-MMSearch、FVQA-test、InfoSeek、SimpleVQA、LiveVQA；通用视频理解为 MMVU、TempCompass、VideoMMMU、VideoMathQA。
- 对照设置：搜索类基准区分 *Direct Answer*（不给工具）与 *Agentic Model*（给工具、由模型自行决定调用）；通用视频理解中基线用均匀采样的 Direct Answer 设置，VideoSearcher 走 agentic 设置。

### 主结果：搜索类基准

![[assets/experiment_table_2607.02927_t1.png]]

作者的文字结论是：VideoSearcher 在 VideoDR 与 VSQA 上大幅优于既有 agentic 基线，说明它在需要「视频 grounding + 工具使用 + 开放网络证据推理」联合能力的场景有效；并且**只用视频数据训练**的模型在通用多模态搜索基准上也明显超过 Qwen3-VL agentic 基线，作者将其解释为「从动态视频语境中学习检索」可以迁移到更广的多模态信息检索任务。表中最直接可核对的数字：VideoSearcher-8B 在 VideoDR 为 $53.00$、VSQA 为 $51.80$、MMSearch 为 $67.84$、HR-MMSearch 为 $43.61$、平均 $57.66$，相对 zero-shot Qwen3-VL-8B agentic 的提升分别为 $+25.00$、$+20.86$、$+20.47$、$+15.74$，平均 $+15.71$。

### 一般视频理解

![[assets/experiment_table_2607.02927_t2.png]]

作者关注的是「检索能力是否以牺牲通用视频理解为代价」。结论是 VideoSearcher 在 MMVU、TempCompass、VideoMMMU、VideoMathQA 上保持竞争力（8B 平均 $60.39$，略高于 Qwen3-VL-8B-Instruct 的 $58.87$），并解释为 agentic 训练不仅优化了检索行为，也保留了可迁移的视频理解能力——尽管检索回来的证据本身可能带来干扰信息。注意这张表的设置与搜索类基准不同：基线与 Qwen3-VL 均按 Direct Answer（均匀采样帧）评测，而 VideoSearcher 是 agentic 评测，作者在正文中明确说明了这一点。

### RL 算法消融

![[assets/experiment_table_2607.02927_t3.png]]

作者对结果的解读是：(1) 只用 $R_{\mathrm{acc}}$ 时，GSPO 相对 GRPO 在 VideoDR 与 VSQA 上更好，说明序列级优化对长 VDR 轨迹有价值，但混合的增益说明仅靠答案级监督并不能可靠地诱导工具使用；(2) 单调工具奖励 $R_{\mathrm{tool\text{-}mono}}$（奖励每一次有效调用）不如 bell-shaped 设计；(3) 解耦 $R_{\mathrm{acc}}$ 与工具奖励后，BiSPO 把 VideoDR 从 $47.00\%$ 提升到 $50.00\%$（配 $R_{\mathrm{tool\text{-}mono}}$），再加上完整的 bell-shaped 奖励达到最佳（$53.00$）。结论是解耦优化与 bell-shaped 工具奖励缺一不可。

### 工具消融

![[assets/experiment_table_2607.02927_t4.png]]

- 只有 Locate（`choose_frames` / `find_frame` / `zoom_in`）：VideoDR $12.00$、VSQA $19.78$、MMSearch $12.28$、HR-MMSearch $3.93$。作者的解释是：没有外部知识时，仅凭 grounded 的视觉证据不足以回答开放世界问题。
- 只有 Search（`web_search` / `image_search`）：VideoDR $43.00$、VSQA $47.48$、MMSearch $66.67$、HR-MMSearch $40.98$；在视频中心的基准上退化明显，因为检索需要先在视频里定位到锚点。
- 两者结合：四项全部最佳（$53.00$ / $51.80$ / $67.84$ / $43.61$），作者据此认为两类工具互补——localization 把问题锚定在视觉证据上，search 补充外部知识。

### 工具调用行为与训练曲线（附录）

- **工具调用分析**：相比 Qwen3-VL-8B-Instruct，VideoSearcher-8B 在 VSQA 与 VideoDR 上显著增加 `find_frame` 与 `choose_frames` 的调用次数，同时 `web_search` 与 `image_search` 也明显增多，作者认为这说明模型学会了「先在地面视频里定位、再连接开放网络」。在视频基准上 `zoom_in` 使用较少，作者推测原因是视频输入分辨率中等，锁定相关帧后往往可以直接进入 image/web search。在 HR-MMSearch 这类高分辨率图像基准上 `zoom_in` 使用显著增加，作者解释为模型能按视觉特征自适应调整工具策略。
- **奖励曲线**：VideoSearcher-4B 的训练平均奖励从约 $0.84$ 升到 $1.03$ 以上，8B 从约 $0.88$ 升到约 $1.05$；原始曲线噪声较大（多轮决策、外部工具观测与 LLM judge 都会引入方差），EMA 平滑后呈稳定上升趋势。作者据此认为 search-aware 的奖励塑形没有阻断有效探索。
- **案例研究**：成功案例展示了「收窄时段 → 锁定关键帧 → 识别视觉线索（如机器人身上的 ``MOONSHOT``）→ image search 关联到日本 Moonshot 养老机器人项目 → web search 验证实体」的多跳链路；失败案例中模型流程完全合理，但 image search 把视觉实体误识别为 Zinnowitz Diving Gondola（真值为 Grömitz Diving Gondola），错误检索结果沿推理链传播，最终答成 $2006$ 而非 $2009$。

## Limitations & Caveats

**作者明确陈述的局限性：**

- **依赖外部工具环境**：答案质量受 image/web search 的延迟、覆盖度与稳定性影响，可复现性弱于 closed-book 视频问答。
- **在线 RL 计算昂贵**：多轮工具使用带来长上下文与反复 rollout，训练成本与工程复杂度都显著上升。
- **覆盖范围有限**：训练与评测集中在 search-oriented 视觉/视频 QA，未充分覆盖稠密时间定位、音频理解、具身交互、专业领域知识与短视频运动线索；$1$ fps 的帧表示本身就可能漏掉短事件与细粒度运动。
- **评测依赖 LLM judge**：开放式答案由 LLM judge 打分，对语义等价或含糊答案会引入噪声；更强的 human evaluation 与校准过的自动指标仍是后续方向。

**从正文与附录可核对的额外保留意见：**

- **失败模式来自检索噪声而非策略**：作者给出的失败案例表明，即使工具轨迹完全合理，错误的外部检索结果也会沿推理链传播——这是一种当前奖励设计（只惩罚无效/重复调用，不建模检索正确性）无法直接纠正的错误。
- **4B 版本的训练配置未在正文给出**：Implementation Details 只描述了从 Qwen3-VL-8B-Instruct 初始化与对应的 SFT/RL 细节，但主表同时报告了 VideoSearcher-4B 的结果；其具体骨干、超参与两个规模共享的奖励设置需要参照官方代码与模型卡才能确认。
- **训练数据与评测数据的分布差异**：训练实例由图文 QA 数据集经实体抽取与视频检索得到，而 VSQA 面向真实网络视频与 $2026$ 年事件；两者在实体类型与视频来源上的重合度论文未做定量分析。
- **跨方法比较口径不同**：主表中 Direct Answer、Agentic Model (zero-shot) 与 Agentic Model 三组分隔开列出，VideoSearcher 属于经过 VDR 训练的一档，且主表的 average 是八个基准的算术平均，各基准样本量差异很大（如 MMSearch $171$ 条、VideoDR $100$ 条、InfoSeek $2{,}000$ 条），平均分应谨慎解读。
- **通用视频理解的不完全公平对照**：Tab. 2 中 VideoSearcher 使用 agentic 设置而基线使用 uniform-sampling Direct Answer，作者在正文中说明了这一点，但两者并非完全同条件的比较。

## Concrete Implementation Ideas

- **工具接口最小约定**：把 `find_frame` 视为「空间工具的前置锁」，`zoom_in` / `image_search` 都必须携带当前 locked frame 索引，bbox 统一用 $0$–$1000$ 归一化 `xyxy`；`choose_frames` 会重置帧锁。这套依赖规则可以直接编码成环境侧的合法性检查，并同时作为 $R^{\mathrm{dep}}$ 的判定依据（$N^{\mathrm{dep}}$ 统计未锁帧就调用 detail/search 的次数，$\min(0.1N^{\mathrm{dep}},0.5)$ 封顶）。
- **双分支 advantage 的实现要点**：先用 LLM judge 得到 $R^{\mathrm{judge}}\in\{0,1\}$；准确率分支在全部 $G$ 条上做组内归一化；工具分支先过滤出 $\mathcal{Q}$，再要求 $|\mathcal{Q}|\ge 2$ 才参与更新，否则该 prompt 只回传准确率分支的梯度。两个分支分别计算 `L_GSPO`，最后按 $1.0:0.15$ 加权——注意合并只发生在 loss 层面，advantage 本身不混。
- **bell-shaped 检索奖励的可复用实现**：按模态（image / web）分开计数，维护「唯一且成功」的调用序号 $k$：先对查询做去重（重复文本查询、重复视觉区域直接跳过），再对失败调用与空结果跳过计数，然后查表 $[0.35,0.20,0.10,-0.10,-0.25]$，$k>5$ 取 $-0.60$；视频侧 grounding 项用 $b+\gamma\sqrt{T^{\mathrm{vid}}}$（$b=0.3$、$\gamma=0.35$）给边际递减的正向信号；最终 clip 到 $[-1,1]$。
- **视觉上下文成本控制**：轨迹合成与 RL 环境都采用「每轮只注入新增视觉观测、文本推理历史完整保留」的增量策略；推理时初始只给 $64$ 帧均匀采样，配合 $12$ 轮上限与 $49{,}152$ token 的上下文预算。
- **数据合成可复用配方**：双模型（Qwen3.5-397B + Kimi-K2.5）交叉验证实体抽取结果 → 以实体为检索词爬视频 → $1$ fps 归一化并在帧上烧入 ``Frame $N$`` → 改写问题为视频语境并做 visual-QA 对齐校验 → 用 Qwen3-VL-8B-Instruct 做 hard sample mining（成功 rollout $\le 1$ 才保留）→ 分层教师模型合成轨迹 → 规则过滤 + LLM 质量验证器。
- **训练稳定性选项**：论文明确不使用 KL reward / KL loss，靠 GSPO 的序列级裁剪（$\epsilon_{\mathrm{low}}=0.2$、$\epsilon_{\mathrm{high}}=0.28$）与冻结 vision tower 稳定训练；若迁移到新环境，可先复现这一组合再考虑加入 KL 项。

## Open Questions / Follow-ups

- 检索正确性没有被显式建模：失败案例显示一次错误的 image search 会污染整条推理链。是否可以把「跨来源交叉验证」「检索不确定性估计」「视觉一致性检查」写进奖励或动作空间（例如允许 agent 对同一实体发起多个检索并投票）？
- 工具分支的 $w_{\mathrm{tool}}=0.15$ 与 bell-shaped 表 $[0.35,0.20,0.10,-0.10,-0.25]$ 是如何选定的？论文未给出这两者的敏感性分析。
- 论文只在 $1$ fps 与冻结 vision tower 的设置下训练。更密的帧率、音频输入、稀疏采样策略或对 vision tower 做部分适配，是否能改善作者自己指出的「短事件与运动线索缺失」问题？
- VideoSearcher-4B 与 8B 之间的差异（表 1 中 4B 平均 $52.75$、8B 平均 $57.66$）有多少来自骨干能力、多少来自二者的训练配置差异？正文未说明 4B 的训练细节。
- 训练分布与 VSQA 的领域分布（Landmarks / Geography / Natural Scenes / Culture 等八类）之间的匹配度如何影响结果？是否存在只在某个领域上受益的情况？论文未按领域报告细分结果。
- 在 $12$ 轮上限内，停止检索的时机（evidence-aware stopping）是由工具奖励边际递减间接学到的；能否显式地对「证据已足够」做建模，从而减少 token 与检索开销？

## Citation

```bibtex
@misc{gao2026videosearcher,
  title  = {VideoSearcher: Empowering Video Deep Research with Multi-Tool Agentic Reasoning via Reinforcement Learning},
  author = {Zhenkun Gao and Yicheng Bao and Jinlong Peng and Xueheng Li and Theo Huang and Bangwei Liu and Kunquan Li and Zhenye Gan and Tao Hu and Chengjun Xie and Mingqian Yang and Xuanhua He and Zhizhong Zhang and Xin Tan and Chengjie Wang and Yuan Xie},
  year   = {2026},
  eprint = {2607.02927},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV},
  url    = {https://arxiv.org/abs/2607.02927}
}
```

<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
