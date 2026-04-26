---
title: "DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence"
authors:
  - DeepSeek-AI
conference:
year: 2026
paper_url: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/DeepSeek_V4.pdf
source_pdf: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/DeepSeek_V4.pdf
pdf_link: "[[assets/paper_deepseek-v4-f4cbe4fc.pdf]]"
cover: "[[assets/pipeline_deepseek-v4-f4cbe4fc.png]]"
updated: 2026-04-27
tags:
  - paper/pdf
  - long-context
  - reasoning
  - agent
  - efficient-inference
status: unread
priority:
rating:
topics:
  - LLM
code: https://huggingface.co/collections/deepseek-ai/deepseek-v4
---

## TL;DR

- DeepSeek-V4 是 DeepSeek-AI 发布的 preview 系列，包含 DeepSeek-V4-Pro 和 DeepSeek-V4-Flash，目标是把 open LLM 推到原生 1M-token context，并显著降低长上下文推理成本。
- 核心方法是 hybrid attention：Compressed Sparse Attention (CSA) 负责压缩后稀疏检索，Heavily Compressed Attention (HCA) 负责更激进压缩下的 dense attention；同时保留 DeepSeekMoE 和 Multi-Token Prediction，并引入 mHC 与 Muon optimizer。
- DeepSeek-V4-Pro 规模为 1.6T total / 49B activated parameters，DeepSeek-V4-Flash 为 284B total / 13B activated parameters；预训练分别使用 33T 和 32T tokens。
- 在 1M-token context 下，论文声称 DeepSeek-V4-Pro 只需要 DeepSeek-V3.2 的 27% single-token inference FLOPs 和 10% KV cache；DeepSeek-V4-Flash 进一步降到 10% FLOPs 和 7% KV cache。
- Post-training 从 mixed RL 改成 domain specialists + On-Policy Distillation (OPD)，并提供 Non-think / Think High / Think Max 三档 reasoning effort。
- 主要 caveat 是架构复杂度较高，部分稳定性技巧仍是经验性方案；大量 real-world 结果来自 internal evaluation，需要独立复现。

## Key Contributions

- **Million-token native context**：通过 CSA/HCA 的混合注意力和压缩 KV cache 设计，把 1M context 变成常规可服务能力，而不只是实验性长上下文扩展。
- **Hybrid CSA/HCA attention**：CSA 将 KV cache 按序列维压缩后做 top-k sparse attention；HCA 用更高压缩率保留 dense attention，用于极长上下文下的低成本全局信息访问。
- **mHC residual upgrade**：用 Manifold-Constrained Hyper-Connections 强化传统 residual connection，试图在大深度网络中提升表示能力和训练稳定性。
- **Muon optimizer at scale**：多数参数使用 Muon，embedding / prediction head / RMSNorm 使用 AdamW；论文还实现了面向 Muon 的 hybrid ZeRO bucket 策略。
- **System stack for long context**：包括 fine-grained EP communication-computation overlap、TileLang kernel development、batch-invariant deterministic kernels、FP4 QAT、contextual parallelism、on-disk KV cache。
- **Post-training consolidation**：先训练 math / coding / agent / instruction following 等 specialist，再用 multi-teacher OPD 合并到统一模型。

## Method

整体 pipeline 可以理解为：

1. 预训练阶段构建更长、更高质量的 32T+ token corpus，包含 math、code、web、long documents、scientific papers 和 technical reports。
2. 模型主体保留 Transformer + DeepSeekMoE + MTP，但把 attention 层替换为 interleaved CSA / HCA，并在 residual path 中加入 mHC。
3. 训练时从 4K context 开始，逐步扩展到 16K、64K、1M；先用 dense attention warmup，再引入 CSA sparse attention。
4. 为稳定训练，出现 loss spike 时动态启用 Anticipatory Routing，并对 SwiGLU 的 linear / gate 分量做 clamping。
5. Post-training 先对各领域进行 SFT + GRPO specialist training，再通过 OPD 让统一 student model 学习多个 teacher 的输出分布。
6. Serving 阶段使用压缩 KV layout、state cache、on-disk KV cache 和 prefix reuse 支撑长上下文推理。

关键组件：

| Component | Role | Notes |
| --- | --- | --- |
| CSA | 压缩 KV 后做 sparse attention | compression rate $m=4$；top-k 为 Flash 512 / Pro 1024 |
| HCA | 更激进压缩后做 dense attention | compression rate $m'=128$ |
| SWA branch | 补偿局部邻近信息 | sliding window size $n_{win}=128$ |
| DeepSeekMoE | FFN / expert routing | Flash: 256 routed experts；Pro: 384 routed experts |
| mHC | residual connection 增强 | expansion factor $n_{hc}=4$，Sinkhorn-Knopp iterations 为 20 |
| Muon | 主要优化器 | momentum 0.95，weight decay 0.1 |
| OPD | specialist capability merging | student 在自己的 on-policy trajectory 上学习 teacher distributions |

## Pipeline Figure

![[assets/pipeline_deepseek-v4-f4cbe4fc.png]]

Caption: Figure 2 | Overall architecture of DeepSeek-V4 series. We use hybrid CSA (Compressed Sparse Attention) and HCA (Heavily Compressed Attention) for attention layers, DeepSeekMoE for feed-forward layers, and strengthen conventional residual connections with mHC.

Source: PDF page 6 cropped render.

## Experiments

### Datasets / Benchmarks

| Dataset / Benchmark Group | Task | Split / Setting | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| AGIEval, MMLU, MMLU-Redux, MMLU-Pro, MMMLU, C-Eval, CMMLU, MultiLoKo, Simple-QA, SuperGPQA, FACTS Parametric, TriviaQA | World knowledge | Base-model evaluation | EM / Pass@1 | Table 1，统一 internal framework |
| BBH, DROP, HellaSwag, WinoGrande, CLUEWSC | Language understanding & reasoning | Base-model evaluation | EM / F1 | Table 1 |
| BigCodeBench, HumanEval, GSM8K, MATH, MGSM, CMath | Code & math | Base-model evaluation | Pass@1 / EM | Table 1 |
| LongBench-V2, MRCR 1M, CorpusQA 1M | Long context | 1-shot / 1M-token setting | EM / MMR / ACC | Table 1、Table 6、Table 7、Figure 9 |
| MMLU-Pro, GPQA Diamond, HLE, LiveCodeBench, Codeforces, HMMT, IMOAnswerBench, Apex | Knowledge & reasoning after post-training | Non-think / High / Max | EM / Pass@1 / rating | Table 6、Table 7 |
| Terminal Bench 2.0, SWE Verified, SWE Pro, SWE Multilingual, BrowseComp, HLE w/ tools, GDPval-AA, MCPAtlas, Toolathlon | Agentic capability | Internal / public agent harnesses | Acc / Resolved / Pass@1 / Elo | Table 6、Table 7 |
| Chinese writing, search Q&A, white-collar tasks, R&D coding | Real-world usage | Internal evaluations | win rate / pass rate / human preference | Table 8-14、Figure 11-15 |

### Main Results

Base model results below are manually reconstructed from Table 1 on PDF page 28.

| Method | Activated Params | Total Params | MMLU-Pro EM | Simple-QA EM | FACTS Parametric EM | HumanEval Pass@1 | LongBench-V2 EM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DeepSeek-V3.2-Base | 37B | 671B | 65.5 | 28.3 | 27.1 | 62.8 | 40.2 |
| **DeepSeek-V4-Flash-Base** | **13B** | **284B** | **68.3** | **30.1** | **33.9** | **69.5** | **44.7** |
| **DeepSeek-V4-Pro-Base** | **49B** | **1.6T** | **73.5** | **55.2** | **62.6** | **76.8** | **51.5** |

Selected post-training comparison below is manually reconstructed from Table 6 on PDF page 38.

| Method / Mode | MMLU-Pro EM | SimpleQA Pass@1 | GPQA Pass@1 | HLE Pass@1 | LiveCodeBench Pass@1 | Codeforces Rating | MRCR 1M MMR | CorpusQA 1M ACC | Terminal Bench 2.0 Acc | SWE Verified Resolved | Toolathlon Pass@1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Opus 4.6 Max | 89.1 | 46.2 | 91.3 | 40.0 | 88.8 | - | 92.9 | 71.7 | 65.4 | 80.8 | 47.2 |
| GPT-5.4 xHigh | 87.5 | 45.3 | 93.0 | 39.8 | - | 3168 | - | - | 75.1 | - | 54.6 |
| Gemini-3.1-Pro High | 91.0 | 75.6 | 94.3 | 44.4 | 91.7 | 3052 | 76.3 | 53.8 | 68.5 | 80.6 | 48.8 |
| K2.6 Thinking | 87.1 | 36.9 | 90.5 | 36.4 | 89.6 | - | - | - | 66.7 | 80.2 | 50.0 |
| GLM-5.1 Thinking | 86.0 | 38.1 | 86.2 | 34.7 | - | - | - | - | 63.5 | - | 40.7 |
| **DeepSeek-V4-Pro Max** | **87.5** | **57.9** | **90.1** | **37.7** | **93.5** | **3206** | **83.5** | **62.0** | **67.9** | **80.6** | **51.8** |

Reasoning-mode comparison below is manually reconstructed from Table 7 on PDF page 39.

| Model / Mode | MMLU-Pro EM | SimpleQA Pass@1 | HLE Pass@1 | LiveCodeBench Pass@1-COT | Codeforces Rating | MRCR 1M MMR | CorpusQA 1M ACC | Terminal Bench 2.0 Acc | SWE Verified Resolved | Toolathlon Pass@1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DeepSeek-V4-Flash Non-Think | 83.0 | 23.1 | 8.1 | 55.2 | - | 37.5 | 15.5 | 49.1 | 73.7 | 40.7 |
| DeepSeek-V4-Flash High | 86.4 | 28.9 | 29.4 | 88.4 | 2816 | 76.9 | 59.3 | 56.6 | 78.6 | 43.5 |
| **DeepSeek-V4-Flash Max** | **86.2** | **34.1** | **34.8** | **91.6** | **3052** | **78.7** | **60.5** | **56.9** | **79.0** | **47.8** |
| DeepSeek-V4-Pro Non-Think | 82.9 | 45.0 | 7.7 | 56.8 | - | 44.7 | 35.6 | 59.1 | 73.6 | 46.3 |
| DeepSeek-V4-Pro High | 87.1 | 46.2 | 34.5 | 89.8 | 2919 | 83.3 | 56.5 | 63.3 | 79.4 | 49.0 |
| **DeepSeek-V4-Pro Max** | **87.5** | **57.9** | **37.7** | **93.5** | **3206** | **83.5** | **62.0** | **67.9** | **80.6** | **51.8** |

Real-world and internal task results below are selected from Table 8-14 on PDF pages 44, 55, 57, and 58.

| Evaluation | Compared Systems | Main Result | Notes |
| --- | --- | --- | --- |
| R&D Coding Benchmark | DeepSeek-V4-Pro-Max vs Claude family | DeepSeek-V4-Pro-Max pass rate 67%; Opus 4.5 70%; Opus 4.6 Thinking 80% | Table 8，30 retained tasks from ~200 internal tasks |
| Developer survey | DeepSeek developers / researchers, $N=85$ | 52% yes, 39% leaned yes, fewer than 9% no | Whether V4-Pro is ready as default primary coding model |
| Agentic Search vs RAG | DeepSeek-V4-Pro | Agentic Search wins 61.7%, RAG wins 18.3%, tie 20.0% | Table 9，总计 869 examples |
| Agentic Search cost | DeepSeek-V4-Pro | Agentic: 16.2 tool calls, 13649 prefill tokens, 1526 output tokens; RAG: 10453 prefill, 1308 output | Table 10 |
| Search Q&A vs V3.2 | DeepSeek-V4-Pro vs DeepSeek-V3.2 | V4 win 28.1%, V3.2 win 10.4%, tie 61.5% | Table 11，总计 956 examples |
| Chinese functional writing | DeepSeek-V4-Pro vs Gemini-3.1-Pro | Prose claims overall win rate 62.7% vs 34.1% | Table 12 |
| Chinese creative writing | DeepSeek-V4-Pro vs Gemini-3.1-Pro | Instruction following 60.03% vs 39.44%; writing quality 77.48% vs 22.35% | Table 13 |
| Complex instruction / multi-turn writing | DeepSeek-V4-Pro vs Claude Opus 4.5 | DeepSeek 45.9%, Opus 52.0%, tie 2.0% | Table 14，hard subset where Claude leads |

### Ablations / Analysis

- **Reasoning effort scaling**：Table 7 显示 Max mode 在 HLE、Codeforces、Apex Shortlist、MRCR 1M、Terminal Bench 2.0 等任务上通常优于 High / Non-think；论文把收益归因于更长 context 与 RL 中更低 length penalty。
- **Long-context degradation**：Figure 9 显示 MRCR 在 128K 内较稳定，超过 128K 后有可见下降；但 1M 时仍保持较强 retrieval。
- **Flash vs Pro**：Flash 以 13B activated parameters 取得较强 reasoning cost-performance，但知识类任务明显弱于 Pro；Pro 在 SimpleQA、FACTS Parametric、LongBench-V2 等更依赖知识和长上下文的任务上提升更大。
- **Search agent**：Appendix Table 9-10 显示 agentic search 比 RAG 更准，但平均 prefill/output tokens 更高；论文强调多数 tool calls 可并行，因此成本增加相对有限。

### Training / Compute

| Item | DeepSeek-V4-Flash | DeepSeek-V4-Pro |
| --- | --- | --- |
| Total / activated params | 284B / 13B | 1.6T / 49B |
| Transformer layers / hidden dim | 43 / 4096 | 61 / 7168 |
| Context schedule | 4K -> 16K -> 64K -> 1M | 4K -> 16K -> 64K -> 1M |
| Pre-training tokens | 32T | 33T |
| Max batch size | 75.5M tokens | 94.4M tokens |
| Peak / end learning rate | $2.7 \times 10^{-4}$ / $2.7 \times 10^{-5}$ | $2.0 \times 10^{-4}$ / $2.0 \times 10^{-5}$ |
| CSA compression / top-k | $m=4$ / 512 | $m=4$ / 1024 |
| HCA compression | $m'=128$ | $m'=128$ |
| SWA window | $n_{win}=128$ | $n_{win}=128$ |
| MoE experts | 1 shared + 256 routed, 6 active | 1 shared + 384 routed, 6 active |
| Optimizer | Muon for most params; AdamW for embedding, prediction head, RMSNorm | Same |
| Stability tricks | Anticipatory Routing, SwiGLU Clamping | Same |

## Limitations & Caveats

- 论文明确称 DeepSeek-V4 是 preview version，因此当前结果应视为阶段性报告，而不是最终架构定稿。
- 为追求极端长上下文效率，架构使用 CSA、HCA、mHC、FP4 QAT、on-disk KV cache 等多种组件；作者也承认许多 preliminarily validated components and tricks 让整体设计相对复杂，后续需要 distill 到更 essential 的方案。
- Anticipatory Routing 与 SwiGLU Clamping 对训练稳定性有效，但其底层机制仍不充分理解；这意味着训练稳定性还偏工程经验驱动。
- 多个 real-world 结果来自 internal evaluations 或 in-house harness，需要外部复现；部分对照模型存在 API 忙碌或长上下文请求失败导致的空缺。
- 1M-context MRCR 在超过 128K 后出现下降，说明超长上下文并非无损扩展。
- 多模态能力仍在未来计划中，本报告主要覆盖 text LLM、agent、search、coding、long-context。
- 本 note 基于 PDF-only extraction；表格为人工从 PDF 文本和页面渲染中重构，复杂表格的排版信息可能不如 TeX source 精确。

## Concrete Implementation Ideas

- 把 KV cache 抽象成三类 storage：SWA state cache、CSA compressed KV、HCA compressed KV，并显式支持 prefix reuse 与 on-disk paging。
- 在 agent framework 中区分 tool-calling context path 和 ordinary chat path：只有工具调用场景保留长程 reasoning state，普通多轮对话仍裁掉历史 thinking。
- 用 Quick Instruction token 复用已计算 KV cache，替代小模型做 search trigger、query generation、authority/domain classification 等低延迟辅助任务。
- 训练 pipeline 可采用 domain specialist -> GRPO -> OPD 的结构，把 math / code / agent / instruction following 分开拉能力，再用 on-policy distillation 合并。
- 对 MoE 训练加入 loss spike 监控：触发时短 rollback 并启用 Anticipatory Routing，而不是一直付出额外 routing 开销。

## Open Questions / Follow-ups

- CSA/HCA 的 interleaving pattern 是否有更系统的 scaling law？不同层位置、压缩率、top-k 对长上下文任务的影响如何分解？
- mHC 的收益在多大程度上来自 residual manifold constraint，而不是额外参数、额外 mixing 或训练 trick？
- OPD 合并多个 specialist 时，如何避免某些领域能力被 teacher conflicts 或 reverse KL objective 稀释？
- 1M context 下，retrieval degradation 从 128K 以后开始明显，瓶颈主要来自 attention compression、position encoding、training data 还是 evaluation noise？
- Agentic Search 的并行 tool calls 在真实服务中如何调度，延迟、成本和答案质量之间有没有稳定 Pareto frontier？
- FP4 QAT 的收益在现有硬件和未来硬件上差异很大，实际 serving stack 需要怎样的 kernel/runtime 才能吃满理论收益？

## Citation

DeepSeek-AI. "DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence." PDF hosted on Hugging Face, 2026. https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/DeepSeek_V4.pdf
