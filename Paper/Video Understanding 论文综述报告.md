---
title: "Video Understanding 论文综述报告"
created: 2026-04-26
updated: 2026-04-26
tags:
  - paper/survey
  - survey/video-understanding
  - video-qa
  - long-video
topics:
  - Video Understanding
status: draft
source_notes:
  - "[[Paper/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding.md]]"
  - "[[Paper/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and.md]]"
  - "[[Paper/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms.md]]"
  - "[[Paper/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question.md]]"
  - "[[Paper/文本视频/TOPA.md]]"
  - "[[Paper/实时视频描述/LiveCC.md]]"
  - "[[Paper/实时视频描述/Dense-Captioning Events in Videos.md]]"
  - "[[Paper/视频理解/DYTO.md]]"
  - "[[Paper/1月8日汇报.md]]"
  - "[[Paper/视频理解/12 月 25 日汇报.md]]"
  - "[[Paper/1月23日.md]]"
---

# Video Understanding 论文综述报告

> 基于当前 `Paper/` 下的论文笔记整理。核心比较对象是 **TOPA、DyTo、D-CoDe、KTV、HiCrew**；**LiveCC / DDVC** 作为 streaming / dense captioning 任务线索补充。  
> 注意：不同论文的 backbone、任务、是否使用 GPT-4o / GPT-3.5、硬件和评测设置不完全一致，下表数值用于理解趋势，不应直接当作严格同设置排名。

## 0. 结论先行

当前 video understanding 的几条路线可以概括为一句话：

> 研究重心正在从“如何把更多视频帧塞进 LLM”，转向“在有限 token / latency 预算下，如何组织最小充分视觉证据，并让模型进行可控推理”。

最重要的判断：

1. **DyTo / KTV 代表感知压缩路线**：核心是 training-free 地解决 temporal redundancy 和 spatial token redundancy。DyTo 更强调动态聚类 + token merging；KTV 更强调极低 token budget 下的 keyframe/key token selection。
2. **D-CoDe / HiCrew 代表推理编排路线**：D-CoDe 证明 EgoSchema 这类 long-form VideoQA 的瓶颈不只是“看没看到”，还有“怎么消费看到的信息”；HiCrew 进一步把视频组织成 Hybrid Tree，并用 question-aware caption + multi-agent evidence integration 做复杂推理。
3. **Question-aware 不是越早越好**：直接在 frame selection 阶段用问题语义筛帧容易掉进 semantic trap，破坏全局事件结构；更稳的策略是“时间覆盖先保持 question-agnostic，多样性优先；问题感知放到 token budget、证据检索、推理编排层”。
4. **如果目标是 EgoSchema / NExT-QA 这类长视频多选 QA**，最有潜力的主线不是再做一个单纯采样器，而是做 **option-contrast evidence gathering**：把每个候选选项当成假设，分别检索支持/反驳证据，再自适应分配 token budget。
5. **TOPA 的启发价值大于直接路线价值**：它说明语言时序预对齐有用，但 text-only video 本质上缺少真实运动、姿态和空间连续性，不适合作为细粒度视频理解主线。
6. **LiveCC / DDVC 是另一个任务轴**：它们更适合引出 Streaming Dense Video Captioning / Dual-speed VL Modeling，而不是直接与 VideoQA 压缩路线比较。

---

## 1. 论文定位总览

| 工作                                                                                                                                                                       | 主要任务                                                           |                                      是否真实视觉输入 |                        是否 training-free | 核心机制                            | 最强点                                                             | 主要短板                                         |                                               |                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- | --------------------------------------------: | --------------------------------------: | ------------------------------- | --------------------------------------------------------------- | -------------------------------------------- | --------------------------------------------- | --------------------------- |
| [[Paper/文本视频/TOPA.md]]                                                                                                                                                   | TOPA]]                                                         | Text-only video understanding / pre-alignment |                                ❌ 文本模拟视频 | 部分依赖预训练                         | 用文本帧模拟视频，借 CLIP text-image space 做预对齐                           | 数据成本低，启发“语言时序推理”                             | 模态 gap 大，缺真实 motion / spatial continuity      |                             |
| [[Paper/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding.md]]             | DyTo]]                                                         |                             Zero-shot VideoQA |                                       ✅ | ✅                               | `[CLS]` 层级聚类选帧 + dynamic bipartite token merging                | training-free 强基线，视觉覆盖较好                     | query-agnostic；EgoSchema 上推理结构不足              |                             |
| [[Paper/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and.md]]         | D-CoDe]]                                                       |              Image-pretrained VLM 扩展到 VideoQA |                                       ✅ | ✅                               | dynamic compression + question decomposition                    | EgoSchema 提升显著，说明推理瓶颈真实存在                    | question decomposition 延迟极高；open-ended QA 不稳定 |                             |
| [[Paper/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms.md]] | KTV]]                                                          |              Efficient training-free VideoLLM |                                       ✅ | ✅                               | DINOv2 KMeans keyframes + importance/redundancy token selection | token 极省，效率/精度 Pareto 好                      | 主要验证 MC VideoQA；长视频全帧 DINOv2 预处理仍有成本          |                             |
| [[Paper/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question.md]]   | HiCrew]]                                                       |                             Long-form VideoQA |                                       ✅ | 系统层 training-free，但依赖 GPT-4o/工具 | Hybrid Tree + Q-aware Captioning + multi-agent planning         | long-form reasoning 最完整，EgoSchema/NExT-QA 很强 | 成本、复现细节、模块误差级联未充分报告                           |                             |
| [[Paper/实时视频描述/LiveCC.md]]                                                                                                                                               | LiveCC]] / [[Paper/实时视频描述/Dense-Captioning Events in Videos.md |                                        DDVC]] | Streaming caption / dense event caption | ✅                               | 通常需要训练或专门系统                                                     | 流式 ASR+frames / 事件定位+描述                      | 适合实时解说与事件结构化                                  | 任务不同，不能直接替代 VideoQA 压缩/推理方法 |

---

## 2. 方法层面对比：从“压缩”到“证据链”

### 2.1 Temporal selection：哪些帧/片段值得保留？

| 方法 | temporal 处理 | 是否 question-aware | 评价 |
|---|---|---:|---|
| TOPA | 没有真实视频帧，用 text frames 模拟时序 | 文本层面可控 | 适合语言时序预训练，不适合视觉细节 |
| DyTo | 从 $N=100$ 均匀采样帧出发，用 `[CLS]` token 构图、1-NN connected components / hierarchical clustering 分段 | ❌ | 保留视觉事件结构，但不管问题是什么都生成同一套压缩 token |
| D-CoDe | uniform sampling + supplementary frame selection：从未选帧中补充与已选帧平均 CLIP similarity 最低的帧 | ❌ | 用“多样性”避免 perception bottleneck；没有早期 question trap |
| KTV | DINOv2 提全视频 frame features，K-Means 选 $m=6$ 个 representative keyframes | ❌ frame selection；✅ token budget allocation | 明确反对 CLIP text-frame similarity 直接选关键帧，因为容易 semantic trap |
| HiCrew | 先 shot boundary detection 保持时间拓扑，再对 question-relevant shots 做 KMeans depth expansion | ✅ | 比全局聚类更保留时间结构，也比纯 question-aware 选帧更稳 |
| LiveCC | causal streaming，不能访问完整未来视频 | ✅/任务驱动 | 面向实时任务，但与离线 VideoQA 评测逻辑不同 |

**关键观察**：  
你的 [[Paper/1月8日汇报.md|1月8日汇报]] 中，question-aware frame selection 在 EgoSchema 上下降，而 question-aware token merging 上升；KTV 的 ablation 也显示 `Question-relevant Keyframes` 替代 cluster keyframes 会明显变差。这说明：

> 在长视频理解中，问题语义应该指导“证据消费”和“预算分配”，不宜过早破坏全局事件覆盖。

### 2.2 Spatial token compression：每帧内保留哪些视觉 token？

| 方法 | token 处理 | 优势 | 风险 |
|---|---|---|---|
| DyTo | dynamic bipartite token merging；按 visual token budget $Z$ 控制输出长度 | 比 average pooling 更保留局部结构 | merge 可能吞掉小物体/OCR/细粒度状态 |
| D-CoDe | top-$\beta M$ by token norm + cosine similarity cluster merge | 简单、模块化、易接到 LLaVA-NeXT | $\ell_2$ norm 是否稳定依赖 encoder 和层级 |
| KTV | [CLS] attention importance + intra-frame redundancy score；再按 question-frame CLIP similarity 分配 $\beta_i$ | 明确区分“重要”和“冗余”，token budget 可稀疏/普通/密集切换 | 仍可能受 CLIP question similarity 偏差影响 |
| HiCrew | 更多转成 caption/tree/evidence，而非直接保留 patch tokens | 大幅降低 LLM 输入视觉 token 负担，便于推理 | caption bottleneck 可能丢失视觉细节 |

### 2.3 Reasoning：LLM 如何消费视频证据？

| 方法 | 推理形式 | 对复杂问题的适配 |
|---|---|---|
| DyTo | single-pass：`VideoTokens + Q -> Answer` | 感知强，但复杂跨时序因果问题容易“看到了但不会用” |
| KTV | single-pass 为主 | 更像高效输入构造器，不专门解决 multi-hop reasoning |
| D-CoDe | 把原问题拆成 sub-questions，先得到 sub-answers，再回答原问题 | 对 EgoSchema 这类 schema-level / long-form MC QA 有明显收益 |
| HiCrew | planning layer 动态选择 agents；Text Agent / Visual Agent / Evidence Integrator / Answer Generator 协同 | 最接近“证据链 + 复杂推理”完整系统 |
| LiveCC/DDVC | 实时 caption 或 dense event caption | 更偏连续生成和事件定位，不是选择题推理 |

**最重要的分界**：

- DyTo / KTV 主要在解决 **perception bottleneck**；
- D-CoDe / HiCrew 主要在解决 **reasoning / evidence consumption bottleneck**；
- 对 EgoSchema，这两者都需要，但当前增益更像是后者更关键。

---

## 3. 结果对比：不能严格横比，但趋势很清楚

### 3.1 Multiple-choice VideoQA 主表

| 方法 | Setting | NExTQA | EgoSchema | IntentQA | VideoMME | MVBench | 备注 |
|---|---:|---:|---:|---:|---:|---:|---|
| DyTo | 7B | 65.7 | 48.6 | 61.6 | 41.2 | 45.2 | training-free，dynamic frame/token compression |
| KTV-sparse | 7B / 504 tokens | 64.5 | 49.6 | 61.2 | 43.6 | 46.2 | 极省 token，很多指标已超过 DyTo-7B |
| KTV-normal | 7B / 936 tokens | 65.1 | 50.4 | 61.3 | 43.7 | 46.4 | 效率/精度较平衡 |
| KTV-dense | 7B / 1872 tokens | 65.8 | 51.0 | 62.0 | 44.0 | 46.0 | 7B 下总体强于 DyTo |
| D-CoDe | LLaVA-NeXT 7B | 68.3 | 58.0 | 64.2 | - | - | Q decomposition 带来 EgoSchema 大幅提升 |
| DyTo | 34B | 72.9 | 56.8 | 67.5 | 53.4 | 52.9 | 大模型下较强 |
| KTV-dense | 34B / 1872 tokens | 72.7 | 57.0 | 68.0 | 53.2 | 51.5 | 与 DyTo-34B 接近，Ego/Intent 更高 |
| HiCrew | GPT-4o | NExT-QA Avg 79.5 | Full 64.6 / Sub 71.6 | - | - | - | agent/system 设置，不宜与 7B/34B 直接比较 |

**读表方式**：

1. **D-CoDe 的 EgoSchema 58.0 很关键**：同为 7B 级 setting，它远高于 DyTo/KTV，说明 EgoSchema 的主要瓶颈并不只是采样和压缩，而是推理结构。
2. **KTV 的价值在效率**：504/936/1872 tokens 三档下表现都很强，说明“少而关键”的 token 构造可行。
3. **HiCrew 是上限式系统设计**：它把视频结构化、caption、tool/agent 推理全部串起来，结果强，但成本和复现风险也最高。

### 3.2 Efficiency / latency 对比

| 方法 | 报告的效率信息 | 解释 |
|---|---|---|
| KTV | sparse 504 tokens；NExTQA 约 1.19s，约 SF-LLaVA-7B 时间的 36.4% | 最适合作为高效 training-free sampler/token selector |
| DyTo | EgoSchema 500 samples，LLaVA-NeXT-34B，单 A100：6.22s/item；SlowFast-LLaVA 5.74s/item | 压缩质量更好，但不一定更快 |
| D-CoDe | EgoSchema baseline 3.927s/sample；dynamic compression 6.115s；full D-CoDe 37.395s | 主要成本来自 question decomposition 多轮推理 |
| HiCrew | 未给完整 token / latency / dollar cost | 结果强，但部署成本需要自己重测 |
| LiveCC | 目标是低延迟 streaming caption | 任务目标本来就以 latency-aware 为核心 |

---

## 4. 核心争议与共识

### 4.1 “Question-aware” 应该放在哪一层？

从这些论文和你的实验笔记看，最合理的分层是：

1. **Temporal coverage 层**：尽量 question-agnostic，优先保证事件结构和多样性。  
   - 对应 D-CoDe 的 supplementary frame selection；
   - KTV 的 DINOv2 KMeans keyframes；
   - DyTo 的 `[CLS]` clustering；
   - HiCrew 的 shot boundary 保拓扑。
2. **Token budget / evidence routing 层**：可以 question-aware。  
   - KTV 根据 question-frame CLIP similarity 分配 token budget；
   - D-CoDe 根据问题拆子问题；
   - HiCrew 根据问题类型生成 targeted captions / workflows。
3. **Reasoning 层**：必须 question-aware，甚至 option-aware。  
   - D-CoDe 的 sub-answers；
   - HiCrew 的 evidence integration；
   - 你的潜在方向：option-contrast evidence gathering。

结论：

> 不建议做“纯 CLIP(Q, frame) 选帧”作为主创新；更建议做“问题/选项驱动的证据检索 + 自适应 token budget”。

### 4.2 EgoSchema 的主要瓶颈是什么？

EgoSchema 是 long-form egocentric multiple-choice QA。它的题目往往不是问单帧对象，而是问长时间跨度内的事件结构、意图、因果和状态变化。

因此它的瓶颈至少有三层：

1. **稀疏关键事件可能被漏掉**：这是 DyTo/KTV 关心的感知覆盖问题；
2. **看到关键事件但没有形成证据链**：这是 D-CoDe/HiCrew 解决的问题；
3. **干扰选项需要被反证**：这是普通 question decomposition 尚未充分利用的多选结构。

你的 [[Paper/1月8日汇报.md|1月8日汇报]] 判断很对：

> D-CoDe 的选帧不一定比 DyTo 全面，但它让模型更会消费已有帧；EgoSchema 很可能是推理瓶颈大于感知瓶颈。

### 4.3 TOPA 为什么没有成为主流？

TOPA 的价值在于提出“文本视频”预对齐，但它没有真实视觉连续性：

- 文本帧描述的是语义变化，不是姿态、速度、轨迹、空间关系的连续变化；
- CLIP text/image alignment 是 coarse semantic alignment，不是 fine-grained motion alignment；
- 因此 TOPA 更像 **语言时间逻辑模型**，不是完整的视觉时序理解模型。

它适合作为低成本预训练/数据增强启发，但不适合作为解决 EgoSchema、VideoMME、MVBench 等真实视觉 benchmark 的主路线。

### 4.4 LiveCC / DDVC 与 VideoQA 路线是什么关系？

LiveCC 和 DDVC 更像另一条任务轴：

- LiveCC：低延迟、流式、多模态解说；
- DDVC：事件定位 + dense caption，强调时间戳和生成质量。

它们对当前 VideoQA 路线的启发是：

> 如果未来要做 Streaming Dense Video Understanding，可以把 LiveCC 的 causal streaming 与 DDVC 的 event-level structure 结合；但如果当前目标是 EgoSchema / NExT-QA，优先做 evidence gathering / reasoning 更直接。

---

## 5. 对后续研究的建议：最值得做的主线

### 5.1 推荐主线：Option-Contrast Evidence Gathering

建议把主线定义为：

> 面向 long-form multiple-choice VideoQA 的 training-free option-contrast evidence framework：用候选选项作为假设，检索支持/反驳证据，并自适应分配视觉 token 预算。

为什么这条线最有潜力：

1. **与 D-CoDe 区分开**：D-CoDe 是 question decomposition；你的方法可以是 option-as-hypothesis，不只是把问题拆小。
2. **与 KTV / DyTo 区分开**：它们主要优化 token 输入；你的方法优化“证据链生成与消费”。
3. **与 HiCrew 区分开**：HiCrew 是 GPT-4o multi-agent 重系统；你可以做更轻、更可复现、training-free、可接 DyTo/KTV 的框架。
4. **贴合 EgoSchema 多选结构**：干扰项往往需要反证，而不仅是找到一个支持片段。

### 5.2 一个可写成论文的框架草案

可以命名为 **OCG-Video** / **Option-Contrast Video Reasoner** / **Contrastive Evidence VideoQA**。

```text
Video
  -> question-agnostic event index
     - shot boundary / DINOv2 KMeans / DyTo CLS clustering
     - 每个 event 保存 representative frames, timestamps, summary tokens

Question + Options
  -> option-as-query
     - h_i = concat(Q, option_i)
     - 对每个 h_i 检索支持 evidence 和反驳 evidence

Evidence-aware token allocation
  -> 对高争议/高相关 event 分配更高 token budget
  -> 对低相关 event 只保留 summary token / caption

Sub-answer / verification
  -> 每个 option 生成 support/refute score
  -> evidence integrator 汇总

Final answer
  -> 选择最被支持、最少被反驳的选项
```

核心口号：

> 从 “Question-aware compression” 升级为 “Option-aware evidence acquisition”。

### 5.3 关键设计原则

1. **先覆盖，后聚焦**  
   temporal index 尽量不被问题过早干扰，避免 semantic trap。

2. **支持证据和反驳证据都要找**  
   多选题的错误往往来自干扰项；只找支持证据容易 confirmation bias。

3. **token budget 要服务 evidence uncertainty**  
   对容易区分的选项少分 token；对高混淆选项/争议片段多分 token。

4. **保留 timestamps 和 event order**  
   不能只把 token 当 bag-of-visual-features；EgoSchema 的因果/时序问题需要事件顺序。

5. **尽量做成 plug-in**  
   前端可以接 DyTo/KTV，后端可以接 LLaVA-NeXT / InternVL / Qwen-VL，降低工程风险。

---

## 6. 实验计划建议

### 6.1 必须复现/比较的 baselines

| 类型 | Baseline | 目的 |
|---|---|---|
| 固定/简单采样 | IG-VLM, SlowFast-LLaVA | 证明不是普通采样收益 |
| 动态视觉压缩 | DyTo | 对比 dynamic clustering + token merging |
| 高效 token selection | KTV sparse/normal/dense | 对比 token efficiency Pareto |
| 推理分解 | D-CoDe | 对比 question decomposition |
| 系统上限 | HiCrew | 作为高成本 agent upper reference，不一定严格复现 |

### 6.2 数据集选择

| 数据集 | 为什么需要 |
|---|---|
| EgoSchema | 主战场；long-form、multi-choice、schema-level reasoning |
| NExT-QA | 可以按 Temporal / Causal / Descriptive 分析 |
| IntentQA | 检验意图/因果推理 |
| VideoMME / MVBench | 多任务泛化 |
| MLVU-Test | 如果强调 long-video scalability，可以加入 |
| MSVD-QA / MSRVTT-QA / TGIF-QA | 用来证明方法是否只适合 MC QA；注意 open-ended 上推理分解可能不稳 |

### 6.3 关键 ablations

| Ablation | 要证明什么 |
|---|---|
| 去掉 option-contrast，只用原问题检索 | 证明多选结构被有效利用 |
| 只找 support，不找 refute | 证明反证对排除干扰项有价值 |
| question-aware frame selection vs question-agnostic clustering | 复现/验证 semantic trap |
| fixed token budget vs evidence-aware budget | 证明预算分配是核心贡献 |
| single-pass answer vs sub-answer/evidence integration | 证明不是 prompt trick，而是推理结构收益 |
| DyTo front-end vs KTV front-end | 证明框架对不同视觉压缩器可插拔 |
| 按 temporal certificate length / video length 分桶 | 证明长证据链问题收益更大 |

### 6.4 需要画的图

1. **Accuracy vs visual tokens / latency Pareto curve**：对比 KTV、DyTo、你的方法。
2. **EgoSchema 按问题类型/证据长度分桶柱状图**：证明收益来自长时序/因果问题。
3. **Case study evidence timeline**：每个选项对应支持/反驳片段，用时间轴展示。
4. **Error transition matrix**：baseline 错误中，有多少被你的 evidence framework 修正；又引入了哪些新错。
5. **Budget allocation visualization**：展示模型把 token 花在了哪些时间段/选项上。

---

## 7. 风险与规避

| 风险 | 表现 | 规避方式 |
|---|---|---|
| 检索错过关键证据 | option-as-query 找错片段 | 保留 question-agnostic 全局 index；低置信度时扩大检索范围 |
| sub-answer hallucination | 中间答案污染最终选择 | 要求每个 sub-answer 绑定 timestamp / frame evidence；加入 refute check |
| 成本过高 | 每个选项都跑多轮 VLM | 先用 caption/summary 粗筛，只对 top-conflict options 做视觉复查 |
| 与 D-CoDe 重复 | 被认为只是 question decomposition | 强调 option contrast、support/refute evidence、budget allocation |
| 与 HiCrew 重复 | 被认为也是 agent system | 强调 lightweight training-free plug-in，不依赖 GPT-4o multi-agent |
| open-ended QA 下降 | 过度结构化不适合简单问题 | 加 route：MC/long-form 开启，简单 open-ended 关闭 |

---

## 8. 最终判断

如果按“最值得借鉴”的维度排序：

1. **工程可落地的压缩前端**：KTV > DyTo > D-CoDe compression。
2. **复杂问题推理启发**：HiCrew > D-CoDe > DyTo/KTV。
3. **EgoSchema 直接相关性**：D-CoDe / HiCrew 最相关，KTV/DyTo 是必要 baseline。
4. **创新空间**：Option-contrast evidence gathering > 单纯 question-aware frame selection > 单纯 token merging 改进。
5. **不建议作为主线**：纯 TOPA-style text-only video；除非加入真实 motion grounding 或混合视觉约束。

一句话建议：

> 你的下一步不应只是“改 DyTo 怎么选帧”，而应把 DyTo/KTV 当作感知压缩器，向上做 **question/option-aware evidence chain**：在不破坏全局时序覆盖的前提下，用候选答案驱动证据检索、反证和 token 预算分配。

---

## Appendix: Pipeline Figures

> [!example]- DyTo / D-CoDe / KTV / HiCrew pipeline figures
> ![[Paper/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/assets/pipeline_2411.14401.png|600]]
>
> ![[Paper/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/assets/pipeline_2510.08818.png|600]]
>
> ![[Paper/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/assets/pipeline_2602.03615.png|600]]
>
> ![[Paper/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/assets/pipeline_2604.21444.png|600]]

## Source notes

- [[Paper/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding/beyond-training-dynamic-token-merging-for-zero-shot-video-understanding.md|Beyond Training: Dynamic Token Merging for Zero-Shot Video Understanding / DyTo]]
- [[Paper/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and/d-code-scaling-image-pretrained-vlms-to-video-via-dynamic-compression-and.md|D-CoDe]]
- [[Paper/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms/ktv-keyframes-and-key-tokens-selection-for-efficient-training-free-video-llms.md|KTV]]
- [[Paper/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question/hicrew-hierarchical-reasoning-for-long-form-video-understanding-via-question.md|HiCrew]]
- [[Paper/文本视频/TOPA.md|TOPA]]
- [[Paper/实时视频描述/LiveCC.md|LiveCC]]
- [[Paper/实时视频描述/Dense-Captioning Events in Videos.md|Dense-Captioning Events in Videos / DDVC discussion]]
- [[Paper/视频理解/DYTO.md|DYTO vs D-CoDe 实现对比]]
- [[Paper/1月8日汇报.md|1月8日汇报]]
- [[Paper/视频理解/12 月 25 日汇报.md|12月25日汇报]]
- [[Paper/1月23日.md|1月23日项目会议]]
