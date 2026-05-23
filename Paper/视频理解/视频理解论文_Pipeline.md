---
title: 视频理解论文 Pipeline 与工作位置综述（Emoji 重点版）
created: 2026-05-14
updated: 2026-05-14
tags:
  - video-understanding
  - paper-review
  - pipeline
  - long-video
  - vlm
  - token-compression
  - evidence-selection
  - emoji-enhanced
source: "[[Paper/视频理解/视频理解论文_Pipeline与工作位置综述_结构化修订版.md]]"
---


> 1. 每篇论文到底在视频理解系统的哪个位置起作用？
> 2. 每个环节解决什么问题、会带来什么风险？

> [!tip] Emoji 速读图例
> - ⭐ 强 query-aware；◑ 中等；⚪ 弱/基本无；🟢 易接入/training-free；🟡 有条件可用；🔴 训练或内部改造成本高；⚠️ 主要风险。

## 0. 核心观点先行


```text
原始视频 → 采样/切分 → 特征/语义提取 → visual token 形成/压缩
       → VLM 内部编码/缓存/记忆 → 外部检索/工具/上下文组织
       → 推理与答案生成 → 评测/校准
```

不同论文的贡献通常只覆盖其中一到两个环节。例如：

- **DIG、HiMu、Evidential Sampling** 主要作用在“采样/选帧/证据选择”环节。
- **KTV、DyTo、D-CoDe、Explore-then-Select** 主要作用在“视觉 token 输入前的压缩/选择”环节。
- **VideoRouter、XComp、FlexMem** 更接近“VLM 内部或半内部的 token/KV/memory 机制”。
- **VideoTree、DVD、HiCrew** 主要作用在“外部表示、检索、agent/tool use、语义上下文组织”环节。
- **BOLD、Video-MME-v2** 主要属于“评测、校准、诊断”环节。

所以，后面讨论“压缩是否重复”时，必须先问：压缩的对象是什么？压缩发生在哪里？压缩的目标是 coverage、evidence selection、token budget reduction，还是 reasoning context organization？

---

## 1. 一个统一的 Video Understanding Pipeline

下面这条 pipeline 可以覆盖大多数 Video-LLM / MLLM 视频理解论文。

```text
A. 原始输入层
   原始视频 / 音频 / 字幕 / OCR 文本 / 元数据
   ↓
B. 时间结构处理层
   视频切分、shot boundary、clip split、uniform sampling、temporal bins、segment/keyframe selection
   ↓
C. 多模态特征与语义抽取层
   CLIP / DINO / SigLIP / ASR / OCR / OVD / CLAP / captioner / video database
   ↓
D. 输入侧 visual token 形成与压缩层
   frame-level token、patch token、token pruning、token merging、token budget allocation
   ↓
E. VLM 内部编码与记忆层
   vision encoder/projector、LLM prefill、attention、KV cache、early-layer routing、visual memory
   ↓
F. 外部上下文组织层
   caption tree、RAG、memory bank recall、agent tools、frame inspect、multi-granular retrieval
   ↓
G. 推理与答案生成层
   direct decoding、question decomposition、multi-agent reasoning、confidence selection、post-hoc calibration
   ↓
H. 评测、校准与数据协议层
   benchmark construction、option bias calibration、group metrics、consistency/coherence scoring
```

这条 pipeline 的价值在于：**每篇论文可以被定位到一个或多个环节，而不是笼统地说它是“视频压缩方法”或“视频理解方法”。**

---

## 2. 每个 pipeline 环节的作用

### 2.1 A. 原始输入层：视频、音频、字幕和文本线索

这一层的核心问题是：视频理解不只是 RGB frame 理解。长视频 QA 往往依赖多个信息源：

- 视觉画面：人物、物体、动作、场景变化；
- 音频：声音事件、说话内容、背景声；
- 字幕/ASR：口语信息、事件解释、叙事线索；
- OCR：屏幕文字、路牌、PPT、视频中的文本；
- 元数据：时间戳、片段边界、视频标题等。

大多数传统 frame selection 或 token compression 方法主要使用视觉信息；但 HiMu、DVD、Video-MME-v2 等工作提醒我们，长视频问题经常需要 audio/OCR/ASR/字幕等外部线索。因此，如果一个方法只压缩 RGB frame，而忽略字幕和音频，它可能在纯视觉问题上有效，但在多模态证据问题上不稳定。

### 2.2 B. 时间结构处理层：采样、切分、选帧、选 segment

这一层处理的是**哪些时间片段值得进入后续模型**。

常见操作包括：

- uniform sampling；
- shot boundary detection；
- clip split / temporal bins；
- keyframe selection；
- query-aware segment/frame selection；
- global/local query routing。

这个环节的目标不是直接回答问题，而是控制输入规模，并决定后续模型能看到哪些证据。它的优势是成本低、迁移性强；风险是 **early discard**：如果关键帧在这里被丢掉，后面的 VLM、RAG、agent、reasoning 基本无法恢复。

代表方法：

- **DIG**：先判断问题是 global query 还是 localized query。global query 走 uniform sampling；localized query 才启用 query-aware frame selection。
- **HiMu**：把问题分解成 logic tree，用 CLIP、OVD、OCR、ASR、CLAP 等专家信号生成 satisfaction curve，再选帧。
- **Query-Conditioned Evidential Keyframe Sampling**：训练一个 query-conditioned evidence scoring network，在 token budget 严格时选最有证据贡献的帧。
- **KTV 第一阶段**：question-agnostic keyframe selection，用视觉特征聚类选代表性帧。
- **DyTo 第一阶段**：hierarchical frame selection，用于减少视频冗余。
- **VideoTree 的 early step**：也会根据 query relevance 做 coarse-to-fine 的 frame/cluster selection，但它更偏外部表示构建。

### 2.3 C. 多模态特征与语义抽取层：从 raw frame 到可用 evidence
> [!note] C 层关心的是“把原始模态变成什么证据表示”；

这一层负责把原始帧、音频、文本转成模型可以处理的特征或语义表示。

常见形式包括：

- visual features：CLIP、DINOv2、SigLIP；
- audio/text features：ASR、CLAP、OCR；
- object/event features：open-vocabulary detection、scene graph、action detector；
- textual captions：frame caption、clip caption、question-aware caption；
- database：multi-granular clip/frame/caption/embedding database。

这一层的本质是 **evidence extraction**。它可以服务于后面的 token selection、caption retrieval、agent search 或 reasoning。这里容易出现两类问题：

1. **文本化损失**：caption 会过滤掉视觉细节；
2. **特征偏置**：CLIP similarity 可能更偏静态语义，而不擅长细粒度动作、时间顺序和局部证据。

代表方法：

- **Video-ChatGPT**：作为早期 Video-LLM，把 video-adapted visual representation 接到 LLM 上，并构造 video instruction data。
- **HiMu**：显式使用 CLIP、OVD、OCR、ASR、CLAP 等多模态专家。
- **VideoTree**：构建 hierarchical video representation，依赖 keyframe/cluster caption 和 query relevance。
- **DVD**：构建 multi-granular video database，供 agent 通过工具检索。
- **HiCrew**：用 question-aware captioning 生成更贴近问题意图的语义描述。

### 2.4 D. 输入侧 visual token 形成与压缩层：LLM 前的 token pruning/merging/allocation

这一层是很多 efficient video understanding 方法的核心。它处理的是：

> 已经选出的帧进入视觉编码器后，会产生大量 visual tokens。哪些 token 应该保留？哪些可以剪枝、合并、降分辨率或低预算表示？

常见操作包括：

- token pruning；
- token merging；
- top-k token selection；
- static/dynamic token allocation；
- frame-level token budget allocation；
- representative token selection。

注意：**token 压缩不等于选帧。**

选帧决定“看哪些时间点”；token 压缩决定“每个时间点保留多少空间细节”。一个方法可以同时做两者，例如 KTV、DyTo、D-CoDe；也可以只做 token allocation，例如 Explore-then-Select 更强调 static/dynamic token 配比。

代表方法：

- **KTV 第二阶段**：在 keyframes 内做 key visual token selection，按 importance 和 redundancy 去掉不重要或冗余 token。
- **DyTo**：hierarchical frame selection 后，用 bipartite token merging 压缩 token sequence。
- **D-CoDe**：通过 representative frame selection 和 content-aware spatial token aggregation 缓解 perception bottleneck 和 token overload。
- **Explore-then-Select / Static or Dynamic**：根据问题需求在 key/static frames 和 delta/dynamic frames 之间探索不同 token allocation，再用 query-aware attention metric 选择最优组合。
- **VideoRouter**：虽然更接近 VLM 半内部/内部方法，但它把 long-video token compression 显式建模为 budgeted evidence allocation，因此也应放入 token 压缩对比。

### 2.5 E. VLM 内部编码与记忆层：attention、KV cache、early layer、visual memory

这一层已经不只是外部处理输入，而是进入 VLM 的 forward 流程。

常见介入对象包括：

- vision encoder hidden states；
- projector；
- early LLM layers；
- attention maps；
- past_key_values / KV cache；
- visual memory bank；
- layer-wise token compression。

这类方法的优点是能利用模型内部语义，对 token/memory 的处理更贴近最终回答；缺点是工程门槛高，通常不能直接用于闭源 API，也不如纯外部方法容易迁移。

代表方法：

- **FlexMem**：把 visual KV cache 作为 memory source，通过 dual-pathway compression 写入 memory bank，再按任务进行 memory reading。
- **XComp**：在 LLM layer 内做 learnable progressive token compression，目标是逐层压缩到 one token per frame，并用 QC-Comp 做 question-conditioned frame compression。
- **VideoRouter**：复用 early multimodal LLM layers 做 frame relevance 估计，再进行 query-adaptive token budget allocation。
- **Video-ChatGPT**：早期模型架构层工作，把视频特征与 LLM 对齐。
- **ROS-DVC**：更偏 dense video captioning decoder/query 设计，不是 VideoQA 压缩主线，但属于模型内部 query/decoder 结构设计。

### 2.6 F. 外部上下文组织层：caption tree、RAG、agent、tool use、memory recall

这一层不一定直接减少 visual tokens，而是把视频转换成更适合 LLM 推理的外部上下文。

它的核心问题是：

> 长视频太长，不能一次性输入；那能不能先构建一个可检索、可展开、可检查的视频证据结构？

常见形式包括：

- caption tree；
- clip database；
- frame inspect tool；
- global browse / local search；
- external memory retrieval；
- multi-agent collaboration；
- hierarchical reasoning structure。

代表方法：

- **VideoTree**：query-adaptive hierarchical tree representation，coarse-to-fine 地抽取 query-relevant information。
- **DVD**：构建 multi-granular video database，由 agent 使用 Global Browse、Clip Search、Frame Inspect 等工具逐步搜证。
- **HiCrew**：Hybrid Tree + question-aware captions + planning layer + multi-agent collaboration。
- **FlexMem**：虽然 memory 是内部 KV cache，但 reading/retrieval 的思想和外部 memory recall 有相似性；区别是它检索的是 visual KV/memory，而不是 caption/text database。

### 2.7 G. 推理与答案生成层：decomposition、multi-agent、confidence、calibration

这一层处理的是：在已有证据基础上如何推理和输出答案。

常见操作包括：

- direct decoding；
- question decomposition；
- sub-question answering；
- multi-path reasoning；
- confidence-guided refinement；
- answer reranking；
- MCQA option bias calibration。

代表方法：

- **D-CoDe 的 question decomposition**：不是单纯压缩，它还把复杂问题拆成子问题，缓解 token overload 和感知瓶颈。
- **C2R**：base answer/confidence → sub-QA generation → refined answers → confidence selector。
- **HiCrew**：planning layer 根据问题复杂度组织不同 agent 角色和执行路径。
- **DVD**：agent 根据当前 observation 规划下一步工具使用和检索动作。
- **BOLD**：post-processing calibration，抑制 MCQA blind guessing / option selection bias。

### 2.8 H. 评测、校准与数据协议层

这一层不改变推理 pipeline，但决定我们如何判断方法是否真的有效。

代表方法：

- **Video-MME-v2**：提出 progressive tri-level hierarchy 和 group-based non-linear evaluation，不只看单题 accuracy，而是看相关问题的一致性和推理连贯性。
- **BOLD**：指出 Video MCQA 中存在 option selection bias，并用后处理校准抑制 blind guessing。
- **Video-ChatGPT**：早期构造 video instruction data 和 GPT-assisted evaluation，对后续 VideoLLM 评测有影响。

这一层对你的工作尤其重要：如果你的方法在 MCQA 上提升 1–3 个点，需要排除是否来自选项位置偏置、prompt 格式变化、answer extraction 差异、单题 lucky guess，而不仅仅是 evidence selection 真的更好。

---

## 3. 总览表：每篇论文在 pipeline 中的位置

| 📄 论文 | 📍 主要 pipeline 位置 | 🔁 核心流程 | 🎯 压缩/选择对象 | Query-aware 程度 | ⚙️ 是否训练/是否内部 | ✍️ 适合怎么引用 |
|---|---|---|---|---|---|---|
| **DIG** | B：时间结构处理 / frame selection | Query type 判断 → GQ uniform / LQ query-aware selection → LMM 回答 | 🖼️ 帧/segment | ⭐ 强，但只对 localized query 启用 | 🟢 Training-free，外部 selector | 说明“不是所有问题都需要 query-aware 检索” |
| **HiMu** | B-C：多模态选帧 | Query logic tree → CLIP/OVD/OCR/ASR/CLAP experts → fuzzy composition → frame selection | 🖼️ 帧 + 多模态 evidence | ⭐ 强 | 🟢 Training-free，外部 selector | 说明复杂问题需要结构化、多模态证据选择 |
| **Evidential Sampling** | B-C：训练式 keyframe scoring | Query-conditioned evidence scoring network → temporal bins top-k → MLLM | 🖼️ keyframes | ⭐ 强 | 🟡 训练轻量 scorer，不训练 MLLM | 说明 evidence selection 可以被学习，而不只是 heuristic |
| **KTV** | B-D：keyframe + key token | Question-agnostic keyframe clustering → key visual token selection → LLaVA/Image VLM | 帧 + visual tokens | ⚪ 弱/基本 question-agnostic | 🟡 Training-free，需访问 visual tokens | 作为 DYTO/KTV 线的核心 baseline |
| **DyTo** | B-D：frame selection + token merging | hierarchical frame selection → bipartite token merging → MLLM | 帧 + visual tokens | ⚪ 弱 | 🟢 Training-free，输入侧/半内部 | 说明 image-MLLM 到 video 的 training-free token compression |
| **D-CoDe** | B-D + G：dynamic compression + decomposition | representative frames → spatial token aggregation → question decomposition → answer | 帧 + spatial tokens + query | ◑ 中：compression 偏内容，reasoning 用 question | 🟢 Training-free | 说明压缩和推理分解可以组合 |
| **Explore-then-Select** | D：query-adaptive token selection | 探索 static/dynamic token allocation → shallow/query-aware attention metric 选组合 | visual token subsequence | ⭐ 强 | 🟡 Training-free，但需要 attention/模型中间信号 | 说明问题类型决定 static/dynamic token budget |
| **VideoRouter** | D-E：budgeted token allocation / early-layer routing | Semantic Router 选 coverage/adaptive policy → Image Router 估 frame relevance → token budget allocation | frame-level token budget | ⭐ 强 | 🔴 需要训练 routers，半内部/内部 | 说明 token compression 可建模为 budgeted evidence allocation |
| **XComp** | E：LLM layer 内 token compression | LP-Comp 逐层 token compression → QC-Comp question-conditioned frame compression | LLM layer 内 visual tokens | ⭐ 强 | 🔴 需要 supervised compression tuning，内部 | 说明内部压缩能做到 one token per frame，但不可黑盒 |
| **FlexMem** | E/F：visual KV memory | clip-by-clip prefill → visual KV cache 写入 memory → memory reading → answer | visual KV cache / memory fragments | ◑ 中：reading 阶段按任务/query 召回 | 🟢 Training-free，但需改 forward / 访问 KV | 说明 memory 压缩不是选帧，而是内部视觉记忆管理 |
| **VideoTree** | B-C-F：tree representation / external context | visual clustering → query relevance scoring → tree expansion → captions → LLM reasoning | frame clusters + captions | ⭐ 强 | 🟢 Training-free，外部 representation | 说明外部语义压缩和 coarse-to-fine retrieval |
| **DVD** | C-F-G：agentic search / tools | offline video database → Global Browse/Clip Search/Frame Inspect → agent reasoning | captions / embeddings / raw frame inspection | ⭐ 强，由 agent 动态决定 | 🟢 外部工具系统，Training-free/Prompt-based | 说明 ultra-long video 可以走 tool-use search |
| **HiCrew** | C-F-G：hybrid tree + multi-agent | shot tree → question-aware captions → planning layer → multi-agent reasoning | captions / tree / agent context | ⭐ 强 | 🟢 外部 agent pipeline，Prompt-based | 说明 temporal topology + question-aware captioning 对 causal reasoning 重要 |
| **Video-ChatGPT** | C-E + H：基础 Video-LLM 架构和评测 | sampled frames → visual features → temporal/spatial aggregation → projection → Vicuna | video features | ⚪ 弱 | 🔴 训练 projection / instruction tuning | 作为早期 Video-LLM pipeline baseline |
| **C2R** | G：reasoning wrapper | base answer/confidence → sub-QA → refined answers → confidence selector | answer candidates / reasoning paths | ◑ 中 | 🟡 Training-free，但需要 confidence/logprob | 说明后处理推理编排不是视频压缩 |
| **BOLD** | G-H：MCQA bias calibration | 原始预测 → option prior / blind guessing bias estimate → calibrated answer | answer probabilities/options | 🚫 与视频 query 无关 | 🟢 Training-free post-processing | 说明 MCQA 提升需排除 option bias |
| **Video-MME-v2** | H：benchmark/evaluation | tri-level hierarchy → group-based non-linear evaluation → consistency/coherence | 数据和指标 | ➖ N/A | 数据集/评测协议 | 说明单题 accuracy 不足以衡量视频理解 |
| **ROS-DVC** | E/G：DVC decoder/query 设计 | role-specific queries + overlap suppression loss → dense video captions | 🎬 decoder queries/events | 任务相关 | 🔴 需要训练 | 不属于 VideoQA 压缩主线，但可作为内部 query 设计参考 |

---

## 4. 按 pipeline 环节详细比较

### 4.1 B 层：Frame / Segment / Evidence Selection

这一类方法回答的是：**哪些时间点/片段应该被送入模型？**

#### DIG

DIG 的关键贡献不是“做了一个更复杂的 query-aware selector”，而是提出：问题类型不同，选帧策略也应该不同。

- Global Query：需要整体覆盖，uniform sampling 往往足够。
- Localized Query：需要找到局部证据，query-aware selection 更有效。

因此 DIG 对你的启发是：**query-aware 不应该被无脑启用，而应该根据 evidence requirement 触发。**

#### HiMu

HiMu 解决的是 DIG 没有充分覆盖的问题：很多长视频问题不是单一视觉概念匹配，而是组合式、多模态、带时间顺序的问题。

例如：

- “某人说完一句话之后发生了什么？”需要 ASR + visual temporal relation；
- “画面中出现某个文字后，人物做了什么？”需要 OCR + visual action；
- “听到某种声音后是否出现某对象？”需要 CLAP/ASR + OVD/CLIP。

HiMu 的优势是可解释、结构化、多模态；风险是 pipeline 复杂，专家信号失败会传导。

#### Evidential Sampling

Evidential Sampling 更像训练式证据选择器。它试图从理论上把 keyframe selection 建模成最大化 selected frames 与 query/answer 之间的条件互信息，然后训练 scoring network 估计 evidential importance。

它比 DIG/HiMu 更“可学习”，推理时可能更便宜；但代价是需要训练数据和 evidence supervision/contrastive objective，跨数据集泛化需要验证。

#### KTV / DyTo 的 frame selection

KTV 和 DyTo 的选帧更偏去冗余和代表性，而不是强 query-conditioned evidence retrieval。

- KTV 第一阶段是 question-agnostic visual feature clustering，目标是选多样且代表性的 keyframes。
- DyTo 也强调 hierarchical frame selection，配合后续 token merging。

它们适合做 efficient training-free image-VLM-to-video adaptation，但如果问题需要很局部的 evidence，纯代表性选帧可能会错过关键瞬间。

#### 本组方法对比

| 🔬 方法 | 选择依据 | 🎯 主要目标 | ✅ 优点 | ⚠️ 风险 |
|---|---|---|---|---|
| DIG | Query type + localized grounding | 区分 global/local 问题 | ✅ 简洁，适合解释为什么不总是 query-aware | ⚠️ GQ/LQ 分类错会影响策略 |
| HiMu | Logic tree + multimodal experts | 组合式、多模态 evidence selection | ✅ 可解释，支持 OCR/ASR/audio | ⚠️ pipeline 复杂，专家质量影响大 |
| Evidential Sampling | learned evidence score | 学习 query-conditioned evidence | ✅ 推理可能高效，目标更原则化 | ⚠️ 依赖训练和标注/构造数据 |
| KTV | visual clustering | 🖼️ 去时间冗余、选代表帧 | ✅ training-free、简单稳定 | ⚠️ 不直接针对 query |
| DyTo | hierarchical clustering | 🖼️ 保留语义丰富帧并减冗余 | ✅ 与 token merging 结合自然 | ⚠️ query-specific evidence 较弱 |

### 4.2 C-F 层：External Representation / Caption / Tree / Agent

这一类方法回答的是：**能不能不把所有视觉 token 喂给 VLM，而是先构建一个外部证据结构？**

#### VideoTree

VideoTree 把长视频组织成 query-adaptive hierarchical tree。它不是简单 caption 全视频，而是通过 coarse-to-fine 的 tree expansion，把 query-relevant details 逐步展开，再交给 LLM 推理。

优势：

- 外部结构清晰；
- 可解释性强；
- 适合长视频；
- 不需要改 VLM 内部。

风险：

- 依赖 captioner 和 relevance scoring；
- 视觉细节会被文本化；
- 对细粒度空间问题可能不如直接保留 visual tokens。

#### DVD

DVD 更偏 agentic search：先构建 multi-granular video database，再让 agent 使用工具检索、浏览、检查 frame。它适合 ultra-long video，因为 agent 不需要一次性读完所有视频，而是按问题逐步搜证。

优势：

- 能处理很长的视频；
- 可回到局部 frame inspect；
- agent 可以动态规划搜索路径。

风险：

- 成本高；
- 工具链复杂；
- prompt/agent 稳定性问题；
- 如果 database/caption 构建质量差，agent 会在错误信息上搜索。

#### HiCrew

HiCrew 相比 VideoTree 更强调 temporal topology 和 causal reasoning。它用 Hybrid Tree 保留 shot boundary 和时间结构，再用 question-aware captioning 和 planning layer 组织 multi-agent collaboration。

它适合用来说明：外部语义压缩不能只追求“少”，还要保留时间拓扑，否则 causal/temporal reasoning 会受损。

#### 外部表示方法对比

| 🔬 方法 | 外部结构 | 👁️ 是否回到视觉 | 是否保 temporal topology | 🎯 适合问题 | ⚠️ 主要风险 |
|---|---|---|---|---|---|
| VideoTree | hierarchical caption/tree | ↪️ 间接 | ◑ 中 | 长视频、多粒度 query | ⚠️ caption 损失视觉细节 |
| DVD | multi-granular database + tools | ✅ 是，Frame Inspect | 取决于数据库设计 | ultra-long search | ⚠️ 成本高、agent 不稳定 |
| HiCrew | Hybrid Tree + question-aware captions + agents | ◑ 部分 | ⭐ 强 | temporal/causal reasoning | ⚠️ 系统复杂 |

### 4.3 D 层：Input-side Visual Token Compression

这一类方法回答的是：**已经选出的帧产生了太多 visual tokens，如何在进入 LLM 前减少 token？**

#### KTV

KTV 是典型的两级 training-free efficient video understanding：

1. keyframe selection：question-agnostic，减少时间冗余；
2. key visual token selection：减少每帧内部空间 token 冗余。

它特别适合作为你沿 DYTO/KTV 路线时的 baseline。它的不足也很明显：问题相关性不是核心机制，因此更像“高效代表性压缩”，不是“证据需求路由”。

#### DyTo

DyTo 的重点是 dynamic token merging。它不是单纯丢帧，而是在 selected frames 上进一步做 bipartite token merging，试图保留语义丰富信息，同时减少 token 数量。

它的贡献点更接近：**如何让 image-trained MLLM 在 zero-shot video understanding 上处理更长、更密的视频输入。**

#### D-CoDe

D-CoDe 把两个问题放在一起：

- perception bottleneck：视频帧多且细节多，image VLM 感知不过来；
- token overload：输入 token 太多，LLM 上下文和注意力负担过高。

因此它一边做 dynamic compression，一边做 question decomposition。它不是纯 token compression baseline，而是“压缩 + 推理组织”的混合方法。

#### Explore-then-Select

Explore-then-Select 的重点是：不同问题需要不同 static/dynamic 信息比例。

- static/key frames 保留空间细节；
- dynamic/delta frames 捕捉时间变化；
- query-aware attention metric 决定哪种 token combination 最适合当前问题。

它和 DIG 的思路相似之处是：都反对“一种策略打所有问题”。不同之处是：DIG 主要在 frame selection 层做 GQ/LQ routing；Explore-then-Select 在 token allocation 层做 static/dynamic routing。

#### 输入侧 token compression 对比

| 🔬 方法 | 🖼️ 是否选帧 | 是否 token 压缩 | 是否 query-aware | ⚙️ 是否训练 | 🔑 核心区别 |
|---|---:|---:|---:|---:|---|
| KTV | ✅ 是 | ✅ 是 | ⚪ 弱 | 🟢 否 | 代表性 keyframe + key token selection |
| DyTo | ✅ 是 | ✅ 是 | ⚪ 弱 | 🟢 否 | hierarchical frame selection + bipartite token merging |
| D-CoDe | ✅ 是 | ✅ 是 | ◑ 中 | 🟢 否 | dynamic compression + question decomposition |
| Explore-then-Select | ✅/◑ 是/候选分配 | ✅ 是 | ⭐ 强 | 🟢 否 | query-adaptive static/dynamic token allocation |
| VideoRouter | ↪️ 间接 | ✅ 是 | ⭐ 强 | 🔴 是 | trained dual-router 做 budgeted evidence allocation |

### 4.4 E 层：VLM Internal Compression / Memory / Routing

这一类方法回答的是：**能不能在 VLM 内部更聪明地压缩、分配、记忆视觉信息？**

#### FlexMem

FlexMem 的关键不是“选哪些帧”，而是“如何把长视频的 visual KV cache 写入和读取为 memory”。它模仿人类持续观看视频并回忆相关片段的过程。

因此 FlexMem 更像 memory mechanism，而不是 frame selector。它需要访问 visual KV cache，所以基本不是闭源 API 可用方法。

#### XComp

XComp 是内部 token compression 的极端路线：目标是到最终 LLM layer 时把每帧压缩到 one token。它包含：

- LP-Comp：learnable progressive token-level compression；
- QC-Comp：用 LLM layer 内 attention 做 question-conditioned frame compression。

它的好处是压缩更贴近模型内部语义；缺点是需要 supervised compression tuning，工程上不能直接套到黑盒模型。

#### VideoRouter

VideoRouter 把 long-video token compression 明确建模为 budgeted evidence allocation：

- Semantic Router：判断当前问题更需要 broad temporal coverage 还是 adaptive high-resolution preservation；
- Image Router：复用 early LLM layers 估计 frame relevance；
- 最后对不同帧分配不同 token budget。

它非常适合用来和你的方向对比：如果你的方法是 training-free 外部 evidence router，那么 VideoRouter 是“训练式、半内部、token budget allocation”的相邻路线。

#### 内部压缩方法对比

| 🔬 方法 | 📍 介入位置 | 🎯 压缩对象 | ⚙️ 是否训练 | 🔐 是否黑盒可用 | ✅ 核心优点 | ⚠️ 核心风险 |
|---|---|---|---:|---:|---|---|
| FlexMem | KV cache / memory bank | visual KV cache | 🟢 否 | 🔴 否 | ✅ 长视频 memory 写入/召回 | ⚠️ 需改 forward，依赖开源模型 |
| XComp | LLM layers | layer-wise visual tokens | 🔴 是 | 🔴 否 | ✅ 极限压缩，one token/frame | ⚠️ 训练和模型绑定强 |
| VideoRouter | early LLM layers + token budget | frame-level visual token budget | 🔴 是 | 🔴 很难 | ✅ query-adaptive budget allocation | ⚠️ 需训练 router，工程复杂 |

### 4.5 G-H 层：Reasoning / Calibration / Evaluation

这一类方法不直接解决视觉输入太长，而是解决：模型如何推理、输出是否可靠、评测是否真实。

#### C2R

C2R 属于 reasoning wrapper。它通过 confidence-guided refinement 生成和选择答案路径。它的问题是依赖 confidence/logprob，闭源 API 未必稳定支持。

#### BOLD

BOLD 不是视频压缩方法，而是 MCQA selection bias calibration。它指出模型可能在看不懂视频时仍然偏向某些选项，导致 accuracy 有虚高或不稳定成分。

对你尤其重要：如果你的 cyclic voting 或 option-position debiasing 有提升，需要把它和 evidence selection 的提升分开汇报。

#### Video-MME-v2

Video-MME-v2 的意义在于：传统 per-question accuracy 可能高估模型能力。它用 group-based non-linear evaluation 强调一致性和多步推理连贯性。

对你来说，如果方法主要提升 localized evidence question，最好不要只报告总 accuracy，还要分问题类型、证据位置、时间跨度、是否字幕相关、是否选项偏置敏感等维度分析。

---

## 5. 压缩类型拆解：外部、输入侧、内部不是同一个概念

这是最容易混淆的地方。建议把“压缩”拆成四类。

### 5.1 时间压缩：frame / segment selection

```text
原始视频很多帧 → 只选择部分时间点/片段
```

对象是时间轴。

代表方法：DIG、HiMu、Evidential Sampling、KTV stage 1、DyTo stage 1。

优点：便宜、直观、容易接黑盒 VLM。

风险：选错帧后不可恢复。

### 5.2 外部语义压缩：caption / tree / database / agent context

```text
原始视频 → caption/tree/database → LLM 读文本化/结构化证据
```

对象是语义上下文，而不一定是 visual tokens。

代表方法：VideoTree、DVD、HiCrew。

优点：适合超长视频，可解释，能用强 LLM 推理。

风险：caption 文本化会丢失视觉细节；database/tool 质量决定上限。

### 5.3 输入侧 visual token 压缩：LLM 前 token pruning/merging/allocation

```text
selected frames → vision encoder tokens → pruning/merging/selection → LLM
```

对象是 LLM 输入前的 visual tokens。

代表方法：KTV stage 2、DyTo、D-CoDe、Explore-then-Select。

优点：直接减少上下文长度和 attention 成本；比单纯选帧更细。

风险：需要访问 token/feature；如果 token importance heuristic 不准，会丢空间细节。

### 5.4 VLM 内部压缩：LLM layer / attention / KV cache / memory

```text
visual tokens 已进入 VLM → 在 layer/KV/memory 中压缩、写入、读取、分配
```

对象是模型内部状态。

代表方法：FlexMem、XComp、VideoRouter。

优点：更接近模型真正使用的信息，可能保留语义更好。

风险：不黑盒、工程复杂、模型绑定强。

### 5.5 四类压缩横向对比

| 类型 | 📍 发生位置 | 🎯 压缩对象 | 📚 代表论文 | 🔐 黑盒 API 可用性 | 🛠️ 主要解决 | ⚠️ 最大风险 |
|---|---|---|---|---:|---|---|
| 时间压缩 | VLM 前 | 🖼️ 帧/片段 | DIG、HiMu、Evidential、KTV stage 1、DyTo stage 1 | 🟢 高 | 输入太长、时间冗余 | ⚠️ evidence 被提前丢掉 |
| 外部语义压缩 | VLM 外部 | caption/tree/database | VideoTree、DVD、HiCrew | 🟢/🟡 高/中 | 超长视频上下文组织 | ⚠️ 文本化损失、caption 错误 |
| 输入侧 token 压缩 | vision encoder 后、LLM 前 | visual tokens | KTV、DyTo、D-CoDe、Explore-then-Select | 🟡/🔴 中/低 | token overload、空间冗余 | ⚠️ 需访问 token，heuristic 失效 |
| 内部压缩 | VLM forward 内 | hidden states / attention / KV cache | FlexMem、XComp、VideoRouter | 🔴 低 | 内部记忆、细粒度预算分配 | ⚠️ 工程复杂、模型绑定 |

---

## 6. 压缩之间是否重复？应该看职责是否重叠

不要问“能不能同时用前压缩和内部压缩”，而要问：它们是不是都在做同一件事？

### 6.1 合理组合：coverage → compression → recall → reasoning

比较合理的层级是：

```text
coverage-oriented sampling
  → coarse segment/keyframe selection
  → visual token pruning/merging/allocation
  → memory/retrieval
  → reasoning/calibration
```

每一层职责不同：

- 前面保证时间覆盖；
- 中间减少视觉 token 冗余；
- 内部或外部 memory 负责召回；
- 后面负责推理、校准和答案稳定性。

### 6.2 容易重复的组合：多层都做强 query-aware evidence selection

如果系统是：

```text
query-aware keyframe top-k
  → query-aware token top-k
  → query-aware memory top-k
  → query-aware answer rerank
```

就可能出现两个问题：

1. **职责重复**：每层都在根据 query 找 evidence，但没有明确 coarse/fine 分工；
2. **错误放大**：前面 selector 一旦错，后面所有 query-aware 模块都只能在错误子集上继续优化。

因此最好的写法不是“我们又做了 query-aware selection”，而是：

> 我们将 coverage、compression 和 evidence allocation 解耦。coverage 保证视频时间轴不被过早截断，compression 减少视觉冗余，evidence allocation 根据问题类型分配有限预算。

---

## 7. 按研究路线重新组织这些论文

### 7.1 路线一：Training-free frame/evidence selection

代表：DIG、HiMu、KTV stage 1、DyTo stage 1。

适合目标：黑盒或半黑盒 VLM，成本低，希望不训练模型。

核心问题：如何在不训练的情况下找到有用帧？

- DIG：问题类型路由；
- HiMu：logic tree + multimodal experts；
- KTV/DyTo：去冗余代表帧；
- Evidential Sampling：虽然是 evidence selection，但属于训练式 scorer，可作为对比路线。

### 7.2 路线二：Training-free image VLM → video adaptation

代表：KTV、DyTo、D-CoDe。

适合目标：用 image-pretrained VLM 处理视频，不做视频专门训练。

核心问题：image VLM 不能承受太多帧和 token，如何压缩后仍保留足够视频信息？

- KTV：keyframes + key tokens；
- DyTo：dynamic token merging；
- D-CoDe：dynamic compression + question decomposition。

### 7.3 路线三：Query-adaptive token budget allocation

代表：Explore-then-Select、VideoRouter、XComp 的 QC-Comp。

适合目标：不是简单减少 token，而是把 token budget 分给最需要的位置。

核心问题：不同问题需要不同证据密度。

- Explore-then-Select：static/dynamic token allocation；
- VideoRouter：coverage vs adaptive high-resolution preservation；
- XComp QC-Comp：内部 attention 驱动 question-conditioned frame compression。

### 7.4 路线四：VLM 内部 memory / layer-wise compression

代表：FlexMem、XComp、VideoRouter。

适合目标：开源 VLM、可改 forward、追求更高上限。

核心问题：能否利用内部 attention/KV/hidden states 更有效地记忆和压缩长视频？

- FlexMem：visual KV cache memory；
- XComp：progressive token compression；
- VideoRouter：early-layer relevance + token budget routing。

### 7.5 路线五：External representation / RAG / agentic video search

代表：VideoTree、DVD、HiCrew。

适合目标：超长视频、可解释检索、闭源强 LLM 推理。

核心问题：不让模型一次性看完视频，而是构建外部证据结构。

- VideoTree：hierarchical tree representation；
- DVD：multi-granular database + tool use；
- HiCrew：temporal-topology-preserving Hybrid Tree + multi-agent reasoning。

### 7.6 路线六：Reasoning/calibration/evaluation

代表：C2R、BOLD、Video-MME-v2。

适合目标：提升答案稳定性，诊断模型是否真的理解视频。

核心问题：accuracy 提升是不是来自真实理解？

- C2R：confidence-guided reasoning refinement；
- BOLD：selection bias calibration；
- Video-MME-v2：group-based non-linear evaluation。

---

## 8. 这些论文之间的关键差异

### 8.1 DIG vs Explore-then-Select vs VideoRouter

三者都关心“不同问题需要不同策略”，但发生层级不同。

| 🔬 方法 | 🚦 路由发生位置 | 🎯 路由对象 | ⚙️ 是否训练 | 💡 关键思想 |
|---|---|---|---:|---|
| DIG | frame selection 前 | global/local selection strategy | 🟢 否 | global 用 uniform，localized 用 query-aware |
| Explore-then-Select | token selection 前 | static/dynamic token allocation | 🟢 否 | 不同问题需要不同静态/动态信息比例 |
| VideoRouter | early-layer/token budget | coverage vs high-res token budget | 🔴 是 | 把 token compression 变成 budgeted evidence allocation |

### 8.2 KTV vs DyTo vs D-CoDe

这三篇最接近 DYTO/KTV 这条 training-free image VLM adaptation 线。

| 🔬 方法 | ① 第一阶段 | ② 第二阶段 | 是否推理增强 | 📌 核心定位 |
|---|---|---|---:|---|
| KTV | question-agnostic keyframe clustering | key visual token selection | ❌ 否 | keyframes + key tokens |
| DyTo | hierarchical frame selection | bipartite token merging | ❌ 否 | dynamic token merging |
| D-CoDe | representative frame selection | spatial token aggregation | ✅ 是，question decomposition | compression + decomposition |

如果你的工作要沿这条线做，最自然的差异化不是“我也压缩 token”，而是：

> 现有 KTV/DyTo 更偏代表性/冗余压缩，而我关注的是不同问题的 evidence requirement 如何决定 frame selection、token budget 和 compression strategy。

### 8.3 VideoTree vs DVD vs HiCrew

三者都属于外部上下文组织，但强弱不同。

| 🔬 方法 | 结构 | 推理方式 | 适合场景 | ⚠️ 风险 |
|---|---|---|---|---|
| VideoTree | hierarchical tree | LLM over selected captions/tree | 长视频问答 | ⚠️ caption 损失细节 |
| DVD | multi-granular database + tools | autonomous agentic search | ultra-long video / search-heavy QA | ⚠️ 成本高、工具链复杂 |
| HiCrew | Hybrid Tree + agents | planning layer 组织 multi-agent | temporal/causal reasoning | ⚠️ 系统复杂、prompt 稳定性 |

### 8.4 FlexMem vs XComp vs VideoRouter

三者都不是普通 VLM 前处理，而是进入模型内部或半内部。

| 🔬 方法 | 内部对象 | 🎯 压缩目标 | ⚙️ 是否训练 | ⚖️ 适合对比点 |
|---|---|---|---:|---|
| FlexMem | visual KV cache | 长视频 memory write/read | 🟢 否 | memory 机制，不是选帧方法 |
| XComp | LLM layer visual tokens | one token per frame | 🔴 是 | 极限内部 token compression |
| VideoRouter | early-layer relevance + token budget | query-adaptive budget allocation | 🔴 是 | 训练式 router，与外部 routing 对比 |

---

## 9. 对你自己的研究定位的启发

如果你想沿 DYTO/KTV 这条线做，建议不要把定位写成：

> 我们提出一种新的视频压缩方法。

这个说法太宽，容易被问：和 KTV/DyTo/D-CoDe/VideoRouter/XComp 有什么区别？

更好的定位是：

> 我们研究 training-free image-VLM-to-video adaptation 中的 evidence-aware budget allocation 问题。不同于 KTV/DyTo 主要依据视觉代表性和冗余进行压缩，我们显式建模问题对证据类型的需求，将 video understanding pipeline 中的 coverage、frame selection、token compression 和 reasoning context 分工解耦。

或者更像论文摘要的表述：

```text
Existing training-free video adaptation methods mainly reduce redundancy through representative frame selection or visual token merging. However, they often treat all questions with a fixed compression policy, ignoring that different questions require different evidence granularity, temporal coverage, and spatial fidelity. We propose an evidence-aware routing framework that first preserves temporal coverage, then allocates frame/token budgets according to the evidence requirement of the query, enabling efficient video understanding without training the backbone VLM.
```

这样你的工作可以和几条线同时区分：

- 相比 DIG：你不只做 frame selection，还考虑 token compression / budget allocation；
- 相比 KTV/DyTo：你不是纯 visual redundancy compression，而是 evidence-aware；
- 相比 D-CoDe：你可以更系统地区分 evidence routing 和 question decomposition；
- 相比 VideoRouter/XComp：你保持 training-free / 更外部可插拔，不依赖训练 router 或改 LLM layers；
- 相比 VideoTree/DVD/HiCrew：你不把视频完全文本化为外部 agent/RAG，而是仍保留 visual-token-level 输入给 VLM。

---

## 10. 推荐的最终 related work 组织方式

如果后面写论文 related work，可以按下面结构组织，而不是按论文逐个罗列。

### 10.1 Long Video Understanding with MLLMs

介绍 Video-ChatGPT、Video-MME / Video-MME-v2、长视频 benchmark 的背景，说明问题来自长视频 token 数量、时间依赖、多模态证据和评测不充分。

### 10.2 Frame and Segment Selection for Efficient Video QA

放 DIG、HiMu、Evidential Sampling、KTV/DyTo 的 frame selection 部分。重点讨论 coverage vs localized evidence selection。

### 10.3 Visual Token Compression and Budget Allocation

放 KTV、DyTo、D-CoDe、Explore-then-Select、VideoRouter、XComp。这里要强调 token compression 的粒度差异：LLM 前 pruning/merging vs LLM 内 progressive compression。

### 10.4 External Video Representation and Agentic Retrieval

放 VideoTree、DVD、HiCrew。强调它们把视频变成 caption/tree/database/tool context，而不是直接优化 visual token 输入。

### 10.5 Reasoning, Calibration, and Evaluation

放 C2R、BOLD、Video-MME-v2。强调 answer selection、MCQA bias、group-level consistency。

---

## 11. 参考论文与链接

- KTV: Keyframes and Key Tokens Selection for Efficient Training-Free Video LLMs. arXiv:2602.03615. https://arxiv.org/abs/2602.03615
- Divide, then Ground: Adapting Frame Selection to Query Types for Long-Form Video Understanding. arXiv:2512.04000. https://arxiv.org/abs/2512.04000
- Beyond Training: Dynamic Token Merging for Zero-Shot Video Understanding. arXiv:2411.14401 / ICCV 2025. https://arxiv.org/abs/2411.14401
- D-CoDe: Scaling Image-Pretrained VLMs to Video via Dynamic Compression and Question Decomposition. arXiv:2510.08818. https://arxiv.org/abs/2510.08818
- Static or Dynamic: Towards Query-Adaptive Token Selection for Video Question Answering. EMNLP 2025. https://aclanthology.org/2025.emnlp-main.545/
- FlexMem: Scaling the Long Video Understanding of Multimodal Large Language Models via Visual Memory Mechanism. arXiv:2603.29252. https://arxiv.org/abs/2603.29252
- VideoRouter: Query-Adaptive Dual Routing for Efficient Long-Video Understanding. arXiv:2605.05848. https://arxiv.org/abs/2605.05848
- One Token per Highly Selective Frame: Towards Extreme Compression for Long Video Understanding. arXiv:2604.14149. https://arxiv.org/abs/2604.14149
- VideoTree: Adaptive Tree-based Video Representation for LLM Reasoning on Long Videos. arXiv:2405.19209 / CVPR 2025. https://arxiv.org/abs/2405.19209
- HiMu: Hierarchical Multimodal Frame Selection for Long Video Question Answering. arXiv:2603.18558. https://arxiv.org/abs/2603.18558
- Deep Video Discovery: Agentic Search with Tool Use for Long-form Video Understanding. arXiv:2505.18079. https://arxiv.org/abs/2505.18079
- HiCrew: Hierarchical Reasoning for Long-Form Video Understanding via Question-Aware Multi-Agent Collaboration. arXiv:2604.21444. https://arxiv.org/abs/2604.21444
- Query-Conditioned Evidential Keyframe Sampling for MLLM-Based Long-Form Video Understanding. arXiv:2604.01002. https://arxiv.org/abs/2604.01002
- Addressing Blind Guessing: Calibration of Selection Bias in Multiple-Choice Question Answering by Video Language Models. ACL 2025. https://aclanthology.org/2025.acl-long.162/
- Video-MME-v2: Towards the Next Stage in Benchmarks for Comprehensive Video Understanding. arXiv:2604.05015. https://arxiv.org/abs/2604.05015
- Video-ChatGPT: Towards Detailed Video Understanding via Large Vision and Language Models. ACL 2024 / arXiv:2306.05424. https://arxiv.org/abs/2306.05424
