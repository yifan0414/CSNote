---
title: "Deep Video Discovery: Agentic Search with Tool Use for Long-form Video Understanding"
authors:
  - Xiaoyi Zhang
  - Zhaoyang Jia
  - Zongyu Guo
  - Jiahao Li
  - Bin Li
  - Houqiang Li
  - Yan Lu
conference: NeurIPS
year: 2025
arxiv_url: https://arxiv.org/abs/2505.18079
pdf_link: "[[paper_2505.18079.pdf]]"
cover: "[[pipeline_2505.18079.png]]"
updated: 2026-04-26
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - video-llm
  - agent
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/microsoft/DeepVideoDiscovery
---

## TL;DR

- 这篇论文提出 **Deep Video Discovery (DVD)**，把 long-form video understanding 重新表述为一个由 LLM 驱动的 agentic search 问题，而不是一次性把长视频塞进 VLM 上下文。
- DVD 先把视频构造成 multi-granular video database：全局 subject registry、clip captions/embeddings、以及可回到像素级的 indexed frames。
- 推理阶段使用 `Global Browse`、`Clip Search`、`Frame Inspect` 三个工具，让 reasoning model 在 observe-reason-act loop 中自适应选择工具链，最后用 `Answer` 停止。
- 在 LVBench 上，DVD 达到 **74.2%** overall accuracy；加入 auxiliary transcripts 后达到 **76.0%**，显著高于论文中列出的 prior video agents 和 strong VLM baselines。
- Ablation 显示 Clip Search 最关键：移除后 LVBench w/ transcripts 从 **71.9%** 降到 **59.6%**；reasoning model 也很关键，GPT-4o 作为 $M_{reasoning}$ 时降到 **62.3%**。
- 主要 caveat 是迭代式 agent 带来更高 API/token 成本，并受 Azure OpenAI image-count limit 与 content filtering 影响。

## Key Contributions

1. 提出 **Deep Video Discovery (DVD)**：一个面向 ultra-long videos 的 agentic search framework，用 search-centric tools 让 LLM 自主规划、检索、检查和回答。
2. 设计 multi-granular video database，将长视频分解为 5 秒 clips，并同时保留 subject-centric global summary、clip-level caption embeddings、frame-level visual evidence。
3. 设计三类工具：`Global Browse` 用于全局上下文，`Clip Search` 用于语义检索相关 clips，`Frame Inspect` 用于在指定时间段做细粒度 VQA。
4. 在多个 long-video benchmarks 上系统评估，尤其在 LVBench、LongVideoBench Long、EgoSchema 上取得论文报告的 strong/SOTA results。
5. 通过 model/tool ablations、step-limit analysis、agent behavior taxonomy 解释为什么 adaptive tool use 比手工固定 workflow 更有效。

## Method

DVD 分成两个 stage：先离线构建视频数据库，再在线进行 agentic search and answer。

**Stage 1: Multi-granular Video Database Construction**

- 输入长视频 $V$，按 $t=5$ seconds 均匀切成 non-overlapping clips：$N=\lceil \frac{\text{len}(V)}{t} \rceil$。
- 每个 clip 以 2 fps 解码为 frames $f_i$。
- 使用 large VLM 逐 clip 生成 caption $c_i$，并维护 progressive subject registry $S_i$：$S_i, c_i = VLM(f_i, S_{i-1})$。
- 用 language embedding model 将 caption 编码为 $e_i \in \mathbb{R}^d$，供 Clip Search 做 cosine similarity retrieval。
- 最终数据库为：

$$
\mathcal{D} = \{S, \{f_i, c_i, e_i\}_{i=1}^{N}\}
$$

**Stage 2: Agentic Search and Answer with Tool Use**

| Action / Tool | Parameters | Role |
| --- | --- | --- |
| `Global Browse` | video database $\mathcal{D}$; user query $Q$ | 返回 subject-centric 与 event-centric global summaries，帮助建立全局语义和长程事件线索。 |
| `Clip Search` | video database $\mathcal{D}$; agent synthesized query $\hat{Q}$; top-$k$ | 基于 caption embedding 做 clip-level retrieval，默认 top-$k=16$，LLM 可调整。 |
| `Frame Inspect` | video database $\mathcal{D}$; sub-query $\hat{Q}$; temporal range $[t_s,t_e]$ | 对指定时间段的原始 frames 做 open-format VQA；最多处理 50 frames，超过则均匀采样。 |
| `Answer` | answer to user query | 停止 agent loop 并输出最终答案。 |

Compact pseudocode:

```text
Input: query Q, max step N, LLM M, tools T = {GlobalBrowse, ClipSearch, FrameInspect}
Initialize H_0 = {Q, action_space}
for i = 1..N:
    R_i = M.reason(H_{i-1})
    A_i, P_i = M.call(R_i, H_{i-1})
    if A_i == Answer:
        break
    O_i = A_i(P_i)
    H_i = H_{i-1} union {(R_i, A_i, O_i)}
    if i == N:
        P_i = M.answer(H_i)
return Answer(P_i)
```

实现细节：LVBench 的 database captioning 使用 GPT-4.1，其他 benchmarks 使用 GPT-4.1-mini 降低成本；agentic search and answer 使用 OpenAI o3 作为 $M_{reasoning}$，Frame Inspect 也使用 o3；frames resize 到 720p；最大 reasoning step 设置为 $N=15$。

## Pipeline Figure

![[pipeline_2505.18079.png]]

Caption: Deep Video Discovery consists of two stages: 1) Multi-granular Video Database Construction, extracting information at multiple levels for understanding, retrieval, and original-content preservation; 2) Agentic Search and Answer, where the agent iteratively reasons over the user query and uses tools to gather information for answering.

Source: TeX includegraphics from `arxiv_main.tex`, figure file `figures/pipeline2.pdf`; converted to PNG with PDF crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| LVBench | multiple-choice long-form video QA | 1,549 questions over 103 hour-long videos | Accuracy (%) | Primary evaluation benchmark; categories include ER, EU, KIR, TG, Rea, Sum. |
| LongVideoBench | long-video QA | Val Overall; Long subset $(900s, 3600s]$ with 564 questions from 188 videos | Accuracy (%) | 论文重点报告 longest-duration subset。 |
| Video MME | long-video understanding | Long subset without subtitles; 300 videos, 900 questions | Accuracy (%) | 使用 no-subtitle setting 以隔离视觉长视频理解。 |
| EgoSchema | diagnostic long-video QA | validation split, 500 videos / 500 questions | Accuracy (%) | 论文指出 DVD 超过 reported human-level $\sim$76%。 |

### Main Results: LVBench Question Categories

| Method                          | Group                   |       ER |       EU |      KIR |       TG |      Rea |      Sum |  Overall |
| ------------------------------- | ----------------------- | -------: | -------: | -------: | -------: | -------: | -------: | -------: |
| Gemini-1.5-Pro                  | Commercial VLMs         |     32.1 |     30.9 |     39.3 |     31.8 |     27.0 |     32.8 |     33.1 |
| Gemini-2.0-Flash                | Commercial VLMs         |     47.4 |     48.5 |     56.8 |     39.3 |     44.4 |     41.4 |     48.6 |
| GLM-4V-Plus                     | Commercial VLMs         |     46.2 |     47.8 |     54.1 |     42.7 |     46.5 |     37.9 |     48.7 |
| GPT-4o                          | Commercial VLMs         |     48.9 |     49.5 |     48.1 |     40.9 |     50.3 |     50.0 |     48.9 |
| OpenAI o3                       | Commercial VLMs         |     57.6 |     56.4 |     62.9 |     46.8 |     50.8 |     67.2 |     57.1 |
| InternVL2.5-78B                 | Open-Source VLMs        |     43.8 |     42.0 |     42.1 |     36.8 |     51.0 |     37.9 |     43.6 |
| VideoLLaMA3-7B                  | Open-Source VLMs        |     45.8 |     42.4 |     47.8 |     35.9 |     45.8 |     36.2 |     45.3 |
| Qwen2.5-VL-72B                  | Open-Source VLMs        |        - |        - |        - |        - |        - |        - |     47.7 |
| VideoChat-Flash                 | Open-Source VLMs        |     51.1 |     46.0 |     49.0 |     38.9 |     48.5 |     34.5 |     48.2 |
| AdaReTaKe                       | Open-Source VLMs        |     53.0 |     50.7 |     62.2 |     45.5 |     54.7 |     37.9 |     53.3 |
| VideoTree                       | Video Agents and Others |     30.3 |     25.1 |     26.5 |     27.7 |     31.9 |     25.5 |     28.8 |
| VideoAgent                      | Video Agents and Others |     28.0 |     30.3 |     28.0 |     29.3 |     28.0 |     36.4 |     29.3 |
| VCA                             | Video Agents and Others |     43.7 |     40.7 |     37.8 |     38.0 |     46.2 |     27.3 |     41.3 |
| MR. Video                       | Video Agents and Others |     59.8 |     57.4 |     71.4 |     58.8 |     57.7 |     50.0 |     60.8 |
| **Deep Video Discovery (Ours)** | DVD                     | **73.4** | **73.3** | **80.4** | **72.3** | **70.7** | **74.1** | **74.2** |
| **+ Auxiliary transcripts**     | DVD                     | **75.5** | **77.1** | **79.0** | **72.7** | **68.7** | **84.5** | **76.0** |

论文解读：DVD 在 LVBench overall 上比 MR. Video 高 13.4 points，比 VCA 高 32.9 points；相对 OpenAI o3 baseline 高 17.1 points；transcripts 额外带来 1.8 points。

### Main Results: Long Video Benchmarks

| Method | Group | LVBench Overall | LongVideoBench Overall | LongVideoBench Long | Video MME Long (w/o sub) | EgoSchema Val |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Gemini-1.5-Pro | Commercial VLMs | 33.1 | 64.0 | 58.6 | **67.4** | - |
| Gemini-2.0-Flash | Commercial VLMs | 48.3 | - | 45.7 | 63.0 | 71.2 |
| GPT-4o | Commercial VLMs | 48.9 | 66.7 | 60.9 | 65.3 | 70.4 |
| OpenAI o3 | Commercial VLMs | 57.1 | 67.5 | 60.6 | 64.7 | 63.2 |
| mPLUG-Owl3 | Open-Source VLMs | 43.5 | 59.8 | - | 50.1 | - |
| InternVL2.5-78B | Open-Source VLMs | 43.6 | 63.6 | - | 62.6 | - |
| Qwen2.5-VL-72B | Open-Source VLMs | 47.7 | 60.7 | - | 63.9 | - |
| AdaReTaKe | Open-Source VLMs | 53.3 | 67.0 | - | 65.0 | - |
| VideoTree | Video Agents and Others | 28.8 | - | - | - | 67.0 |
| VideoAgent | Video Agents and Others | 29.3 | - | - | - | 63.2 |
| VCA | Video Agents and Others | 41.3 | - | - | - | 73.6 |
| MR. Video | Video Agents and Others | 60.8 | - | 61.6 | 61.8 | 73.0 |
| **Deep Video Discovery (Ours)** | DVD | **74.2** | **71.6** | **68.6** | 67.3 | **76.6** |

论文解读：DVD 在 LongVideoBench overall 上比 prior SOTA 高 4.1 points，在 Long subset 高 7.0 points；Video MME Long 接近 Gemini-1.5-Pro；EgoSchema 超过 previous best 3.0 points。

### Ablations / Analysis: Model Choices

| $M_{database}$ | $M_{reasoning}$ | $M_{tool}$ | LVBench w/ transcripts |
| --- | --- | --- | ---: |
| 4.1 | o3 | 4.1-mini | 72.3 |
| 4.1 | o4-mini | o3 | 70.2 |
| 4.1 | 4o | o3 | 62.3 |
| 4.1-mini | o3 | o3 | 71.9 |
| 4.1 | o3 | o3 | **76.0** |

这里 $M_{reasoning}$ 最敏感：换成 o4-mini 下降 5.8 points，换成 GPT-4o 下降 13.7 points。作者认为这是因为 DVD 的核心收益来自 reasoning model 对工具使用轨迹的自主规划。

### Ablations / Analysis: Search-centric Tools

| Global Browse | Clip Search | Frame Inspect | LVBench w/ transcripts |
| --- | --- | --- | ---: |
|  | yes | yes | 69.0 |
| yes |  | yes | 59.6 |
| yes | yes |  | 63.5 |
| **yes** | yes | yes | **71.9** |

工具消融显示：移除 Clip Search 的伤害最大，下降 12.3 points；移除 Frame Inspect 下降 8.4 points；移除 Global Browse 下降 2.9 points。直觉上，Clip Search 是定位证据时间段的核心，Frame Inspect 则补足 caption 无法覆盖的细节。

### Ablations / Analysis: Reasoning Models

| Category | Model | LVBench Accuracy (%) |
| --- | --- | ---: |
| DVD w/ closed-sourced | OpenAI o3 | **76.0** |
| DVD w/ closed-sourced | GPT-4o | 62.3 |
| DVD w/ open-sourced | DeepSeek-R1 | **68.5** |
| DVD w/ open-sourced | DeepSeek-V3 | 57.5 |
| DVD w/ open-sourced | Qwen3-32B-Thinking | 57.3 |

开源 reasoning model 也能提升 DVD：DeepSeek-R1 + DVD 在 LVBench 达到 68.5%，超过论文中列出的所有 prior methods。

### Ablations / Analysis: Efficiency and Step Limit

| Variant | Max Step Limit | Avg. Actual Steps | LVBench Accuracy (%) |
| --- | ---: | ---: | ---: |
| Ours | 8 | 6.7 | 72.3 |
| Ours | 12 | 7.2 | 73.8 |
| Ours | 15 | 7.3 | 74.2 |
| Ours w/ VideoAgent workflow | 8 | 5.0 | 48.4 |
| Ours w/ VideoAgent workflow | 12 | 8.3 | 66.3 |
| Ours w/ VideoAgent workflow | 15 | 11.1 | 70.2 |

固定 VideoAgent-style workflow 即使平均步骤更多，仍低于 DVD adaptive workflow：在 step limit 15 下低 4.0 points，且平均步骤多 52%。

### Training / Compute

| Item | Value |
| --- | --- |
| Temporal segmentation | 5-second non-overlapping clips |
| Frame decoding | 2 fps |
| Frame resolution | resized to 720p |
| Clip Search default top-$k$ | 16 |
| Maximum reasoning step | $N=15$ |
| Frame Inspect maximum input | 50 frames; uniform sampling when exceeding limit |
| Global Browse image composition under Azure limit | up to 250 frames via 50 images x 5 horizontally spliced frames |
| OpenAI o3 baseline image composition | 256 frames via 32 composite images, each in a 2 x 4 layout |
| LVBench average API cost | \$0.213 per question with 0.15M tokens, priced at 2025-11-03 |
| Statistical significance | LVBench w/ auxiliary transcripts: average 74.0, variance 0.125 over 3 runs |

### API Filtering Analysis

| Method | Metric | LVBench Overall | LongVideoBench Overall | LongVideoBench Long | Video MME Long (w/o sub) | EgoSchema Val |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI o3 | Score | 57.1 | 66.7 | 59.6 | 64.7 | 63.2 |
| OpenAI o3 | Unfiltered Ratio | 83% | 90% | 85% | 83% | 75% |
| OpenAI o3 | Unfiltered Subset Score | 63.3 | 71.5 | 72.6 | 73.2 | 77.5 |
| Deep Video Discovery (Ours) | Score | 71.9 | 70.5 | 68.4 | 66.8 | 76.6 |
| Deep Video Discovery (Ours) | Unfiltered Ratio | 24% | 61% | 40% | 24% | 54% |
| Deep Video Discovery (Ours) | Unfiltered Subset Score | 70.5 | 71.6 | 70.5 | 69.7 | 77.0 |

作者说明 Azure OpenAI content filtering 会误判 benchmark 中一部分数据。OpenAI o3 baseline 被 blocked 时随机选剩余候选；DVD 不做额外错误处理，而是把 failure message 留给 agent 自行处理，captioning 被 blocked 时对应 database entry 留空。

## Limitations & Caveats

- 迭代式 tool-use reasoning 带来较高 computational/API overhead；论文自己的 appendix 报告 LVBench 平均每题约 \$0.213 与 0.15M tokens。
- DVD 的 database construction 依赖 VLM caption 质量；caption 压缩会造成信息损失，所以系统必须保留 frames 并通过 Frame Inspect 回查像素证据。
- `Frame Inspect Trap` 与 `Clip Search Trap` 是主要失败模式：前者会陷入连续细粒度检查，后者在 database 缺少相关 caption/subject 时反复检索无效结果。
- Azure OpenAI Service 的 50 images/request limit 与 safety content filtering 会影响评估；表中 unfiltered ratio 显示 DVD 的一些调用链更容易遭遇过滤。
- 论文使用强闭源模型（GPT-4.1、OpenAI o3）作为核心组件；迁移到本地/开源栈时，reasoning model 与 VQA model 能力可能成为瓶颈。
- Broader impact 中提到：大模型继承训练数据 bias，可能对视频内容产生不准确或不公平解释；agentic search 的资源消耗也有可持续性与可访问性问题。

## Concrete Implementation Ideas

1. 做一个可复用的 `VideoDatabaseBuilder`：按 5 秒切 clip、2 fps 抽帧、批量 caption、embedding index、subject registry 全部落盘；每条 caption 记录 clip time range 与 frame paths。
2. 给 agent 增加 evidence ledger：每次 `Clip Search` 与 `Frame Inspect` 输出结构化 evidence，包括时间段、source type、confidence、是否直接支持某个 answer option。
3. 针对 trap behavior 加 stopping/repair heuristics：连续 3 次同类工具无新增证据时，强制切换工具、扩大/缩小时间窗口、或要求 answer with uncertainty。
4. 做成本优化：先用 cheap VLM/embedding 建 database，再对高不确定样本触发 expensive `Frame Inspect`；也可以缓存 query-conditioned global browse summaries。
5. 如果用于真实长视频检索产品，界面应展示 answer + supporting timestamps + inspected frames，而不是只返回文本答案。

## Open Questions / Follow-ups

- DVD 的 subject registry 在长视频中如何处理同一人物跨场景 re-identification 的错误累积？论文没有给出专门的 quantitative analysis。
- Clip Search 只基于 caption embeddings 是否足够？加入 visual embeddings、ASR embeddings、scene/object tracks 会不会减少 Clip Search Trap？
- Agent 自由规划工具链是否可以通过 learned policy 或 verifier 降低成本，同时保留 adaptive behavior？
- 对 non-multiple-choice、开放式摘要/检索任务，DVD 的 evaluation protocol 和 answer grounding 应如何设计？
- Content filtering 对 DVD 调用链影响明显；如果换成本地模型或不同 API provider，结果是否会稳定提升？

## Citation

```bibtex
@misc{zhang2025deepvideodiscoveryagenticsearch,
  title = {Deep Video Discovery: Agentic Search with Tool Use for Long-form Video Understanding},
  author = {Xiaoyi Zhang and Zhaoyang Jia and Zongyu Guo and Jiahao Li and Bin Li and Houqiang Li and Yan Lu},
  year = {2025},
  eprint = {2505.18079},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  doi = {10.48550/arXiv.2505.18079},
  url = {https://arxiv.org/abs/2505.18079},
  note = {Accepted to NeurIPS 2025}
}
```
