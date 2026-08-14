---
title: "LMMs-Eval: Reality Check on the Evaluation of Large Multimodal Models"
authors:
  - Kaichen Zhang
  - Bo Li
  - Peiyuan Zhang
  - Fanyi Pu
  - Joshua Adrian Cahyono
  - Kairui Hu
  - Shuai Liu
  - Yuanhan Zhang
  - Jingkang Yang
  - Chunyuan Li
  - Ziwei Liu
conference: NAACL 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2407.12772
pdf_link: "[[assets/paper_2407.12772.pdf]]"
cover: "[[assets/pipeline_2407.12772.png]]"
updated: 2026-05-31
tags:
  - paper/arxiv
  - benchmark
  - evaluation
  - leaderboard
status: unread
priority:
rating:
topics:
  - Dataset & Benchmark
code: https://github.com/EvolvingLMMs-Lab/lmms-eval
---


## TL;DR

- 这篇论文把 Large Multimodal Models (LMMs) 的评测问题归纳为一个 evaluation trilemma：wide coverage、low cost、zero contamination 很难同时满足。
- 作者提出 `LMMs-Eval`，一个统一、标准化、可复现的 multimodal benchmark suite，覆盖 50+ tasks、10+ models 以及约 30 个 model variants。
- `LMMs-Eval Lite` 用 coreset / $k$-Center Greedy 思路从大规模 benchmark 中选 representative samples，把 90,223 个样本压到 9,134 个，同时尽量保持 full-set 排名信号。
- `LiveBench` 用持续更新的新闻与论坛网页构造动态 QA，目标是降低数据污染风险，并用 GPT-4o / Claude / Gemini / human judges 等进行评测。
- 论文的核心价值不是宣称“解决”评测，而是把统一评测、低成本 proxy、动态防污染三条路线放在同一框架下，给 LMM 开发提供更现实的评测组合。

## Key Contributions

1. `LMMs-Eval`：统一多模态评测流程，覆盖数据准备、generation-based / perplexity-based setup、输出后处理、metric calculation、日志记录和模型/数据集接口。
2. `LMMs-Eval Lite`：用 CLIP image embeddings 与 BGE-M3 text embeddings 做 representative subset selection，在保留 broad domain coverage 的同时显著降低评测成本。
3. `LiveBench`：从 latest news / online forums 采集网页截图与文本，自动生成、检查、评分并人工筛选 QA，形成动态、低污染的 LMM benchmark。
4. Reality check：论文明确指出当前静态 benchmark 可能存在 image overlap、text overlap、similar question contamination，并给出基于 text 8-gram 与 image token 8-gram 的分析工具。
5. 评测实践建议：full benchmark 用于正式报告，Lite 用于开发周期内的快速信号，LiveBench 用于检查真实世界动态信息与 zero-shot generalization。

## Method

`LMMs-Eval` 的基础设计是把原本分散在 model-specific scripts 与 dataset-specific scripts 中的流程收敛到一个统一 harness 中。它固定数据源、评测设置、chat template、后处理和日志格式，避免不同论文或项目中同名 benchmark 分数不可比。

`LMMs-Eval Lite` 把 full benchmark 写成 $D = \{(x_i, y_i)\}_{i=1}^{n}$，模型 $f$ 对样本 $x_i$ 的回答是 $\hat{y}_i$，benchmark scoring function 是 $S$。目标是选择一个 subset $V \subset D$，让 subset score 尽量近似 full-set score：

$$
\min_{V: |V| \le |D|}
\left|
\frac{1}{|D|}\sum_{i=1}^{|D|}S(y_i, \hat{y}_i)
-
\frac{1}{|V|}\sum_{i=1}^{|V|}S(y_i, \hat{y}_i)
\right|
$$

作者将它转化为 $k$-Center selection 问题，用 greedy algorithm 做近似。样本 embedding 由 CLIP image embeddings 与 BGE-M3 text embeddings 拼接得到。

`LiveBench` pipeline 更像一个动态评测生产线：

- 从 60+ news outlets / forums 中抓取最新网页截图与内容。
- 用 Claude-3.5-Sonnet 做 OCR、significant image detection、image-text relation extraction 与 newsworthiness extraction。
- 用 quiz model 生成四类问题：Concrete Recognition、Real-world Application、Analytical Understanding、Divergent Thinking & Creation。
- 用 Checker / Finalizer 模型重写、验证和格式化 QA。
- 用 scorer 按 Authenticity、Logical Coherence、Clarity and Precision 对候选 QA 打 1-10 分，每月约生成 500 个候选，再筛选 100-300 个进入最终 problem set。
- 用 GPT-4o 作为主 judge model，也讨论 Claude-3.5-Sonnet、Gemini 1.5 Pro 与 human judges。

污染检测部分使用两条简单但可复现的路线：text overlap 用 8-gram string matching，并过滤训练集中出现超过 10 次的 meaningless n-grams；image overlap 则用 pretrained SEED-tokenizer 将图像转为 32-token sequence，再用 image token 8-gram 检测重叠。

## Pipeline Figure

![[assets/pipeline_2407.12772.png]]

Caption: Overview pipeline for LiveBench. The paper describes collecting latest information from actively updated websites, organizing Q&A with multimodal model assistance, verifying Q&A with human annotators, evaluating models with judge models including human judges, and finally reporting the problem set.

Source: TeX includegraphics from `sections/livebench.tex`, `figures/livebench.png`.

## Experiments

### Datasets / Benchmarks

| Dataset / Benchmark | Task | Split / Scale | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| LMMs-Eval | Unified multimodal evaluation | 50+ tasks, 10+ models, around 30 variants | Dataset-specific metrics | 用统一 pipeline 做 transparent and reproducible evaluation。 |
| LMMs-Eval Lite | Affordable broad-coverage evaluation | 15 datasets; Full 90,223 samples -> Lite 9,134 samples | Correlation with full-set scores, aggregated normalized score | 用 representative subset selection 降低开发期评测成本。 |
| LMMs-Eval Lite+ | Expanded Lite variant | Full 340,226 samples -> Lite 13,734 samples | Same as Lite | 追加 COCO、VQA、GQA、OKVQA、VizWiz-VQA、MM-Bench 等。 |
| LiveBench | Dynamic webpage/news/forum understanding | Dynamic monthly test set; about 100-300 selected questions from about 500 candidates | Judge score scaled to 0-100 | 用最新网页信息减少静态 benchmark contamination 风险。 |
| Contamination analysis set | Image/text overlap probing | 20+ existing benchmarks | Image overlap %, text overlap % | 以 LLaVA-NeXT training data 为参照分析 benchmark overlap。 |

### Main Results: Selected LMMs-Eval Scores

下表来自论文 TeX 表格 `tables/lmms_eval_results.tex`。除 MME 使用其原 benchmark score 外，其余列为相应 benchmark 的分数/准确率；加粗保留原文标记。

| Models | Parameters | AI2D | ChartQA | DocVQA | LLaVA-W | MathVista | MME | MMMU | RealWorldQA |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LLaVA-1.5-7B | 7B | 54.8 | 18.2 | 28.1 | 59.6 | 26.7 | 1859.0 | 35.3 | 55.8 |
| LLaVA-NeXT-Vicuna-7B | 7B | 66.6 | 54.8 | 74.4 | 72.3 | 34.4 | 1841.8 | 35.1 | 57.8 |
| LLaVA-NeXT-Mistral-7B | 7B | 60.8 | 38.8 | 72.2 | 71.7 | 37.4 | 1823.4 | 33.4 | 59.3 |
| Qwen-VL-Chat | 7B | 45.9 | 60.1 | 66.3 | 21.2 | 24.6 | 1890.8 | 27.7 | 1.7 |
| InstructBLIP-Vicuna-7B | 7B | 33.8 | 12.5 | 13.9 | 55.2 | 23.4 | 1508.7 | 28.4 | 37.4 |
| LLaVA-NeXT-LLaMA3-8B | 8B | 71.6 | 69.5 | 78.2 | 80.1 | 37.5 | 1971.5 | 41.7 | 60.0 |
| XComposer4K-HD | 8B | 78.1 | 80.6 | 90.8 | 74.2 | 57.3 | 2189.8 | 42.6 | 62.6 |
| Idefics2-8B | 8B | 69.2 | 26.4 | 73.4 | 43.7 | 48.0 | 1792.1 | 39.7 | 25.5 |
| LLaVA-1.5-13B | 13B | 59.5 | 18.2 | 30.3 | 66.1 | 26.4 | 1818.3 | 34.8 | 54.9 |
| LLaVA-NeXT-Vicuna-13B | 13B | 70.0 | 62.2 | 77.5 | 72.3 | 35.1 | 1891.9 | 35.9 | 58.7 |
| InstructBLIP-Vicuna-13B | 13B | 36.8 | 12.7 | 13.6 | 54.4 | 25.0 | 1529.6 | 33.7 | 42.4 |
| InternVL-1.5 | 26B | 79.0 | 83.8 | 92.4 | 90.2 | 61.5 | 2183.6 | 43.1 | 65.0 |
| LLaVA-NeXT-34B | 34B | 74.9 | 68.7 | 84.0 | 88.8 | 46.0 | 2030.4 | 46.7 | 62.0 |
| LLaVA-NeXT-72B | 72B | 77.4 | 77.0 | 84.4 | 89.2 | 46.6 | 2158.9 | 46.4 | 65.4 |
| LLaVA-NeXT-110B | 110B | 80.4 | 79.7 | 85.7 | 90.4 | 49.0 | 2200.4 | 49.1 | 63.1 |
| LLaVA-OV-0.5B | 0.5B | 57.1 | 61.4 | 73.7 | 74.2 | 34.8 | 1478.0 | 31.4 | 55.6 |
| LLaVA-OV-0.5B(SI) | 0.5B | 54.2 | 61.0 | 75.0 | 71.2 | 34.6 | 1489.0 | 31.2 | 53.7 |
| LLaVA-OV-7B | 7B | 81.4 | 80.0 | 90.2 | 90.7 | 63.2 | 1998.0 | 48.8 | 66.3 |
| LLaVA-OV-7B(SI) | 7B | 81.6 | 78.8 | 89.3 | 86.9 | 56.1 | 2109.0 | 47.3 | 65.5 |
| LLaVA-OV-72B | 72B | **85.6** | 83.7 | 93.1 | 93.5 | **67.5** | 2261.0 | 56.8 | 71.9 |
| LLaVA-OV-72B(SI) | 72B | 85.1 | **84.9** | **93.5** | **93.7** | 66.5 | **2269.0** | **57.4** | **73.8** |

### Main Results: LiveBench-2024-09

该表来自 `sections/livebench.tex`。原文结论是 GPT-4 series、Claude、Gemini 等闭源/商业模型整体仍领先多数 open-source LMM；Open-source models 在传统静态 benchmark 上看似强，但在动态真实世界内容上仍有明显差距。

| Model | Overall | Recognition | Analysis | Thinking | Realworld |
| --- | ---: | ---: | ---: | ---: | ---: |
| LLaVA-1.5-7B | 30.2 | 9.4 | 36.4 | 45.4 | 29.4 |
| LLaVA-OV-0.5B | 32.4 | 25.1 | 33.6 | 40.2 | 30.6 |
| LLaVA-OV-7B | 64.9 | 57.2 | 67.0 | 76.2 | 59.0 |
| LLaVA-OV-7B-Chat | 65.6 | 48.8 | 75.8 | 84.0 | 53.6 |
| LLaMA-3.2-V-11B-Instruct | 65.8 | 51.9 | 65.2 | 71.4 | 74.7 |
| InternVL2-8B | 69.6 | 65.6 | 74.8 | 77.5 | 60.4 |
| LLaVA-OV-72B-Chat | 75.0 | 62.0 | 87.8 | 83.8 | 66.6 |
| Qwen2-VL-7B | 79.2 | 74.2 | 82.8 | 87.4 | 75.2 |
| Gemini-1.5-Flash | 81.6 | 77.1 | 82.4 | 89.0 | 77.9 |
| Gemini-1.5-Pro | 84.5 | 85.4 | 83.8 | 88.6 | 80.1 |
| Qwen2-VL-72B | 85.9 | 86.7 | 88.8 | 89.0 | 79.2 |
| Claude-3.5-sonnet | 90.3 | 94.6 | 93.4 | 95.3 | 85.8 |
| GPT4o-mini | 91.9 | **94.6** | 93.4 | **95.3** | 84.3 |
| GPT4o | **92.0** | 91.7 | **93.8** | 94.8 | **87.6** |

### Ablations / Analysis: LMMs-Eval Lite Selection

| Dataset | Quire | k-means | Lite(Ours) |
| --- | ---: | ---: | ---: |
| Flickr30k | 0.97 | 0.79 | 0.91 |
| AI2D | 0.45 | 0.87 | **0.98** |
| SeedBench | 0.27 | 0.87 | **0.87** |
| TextVQA | 0.99 | 0.98 | **0.99** |

这里的相关性实验只覆盖六个 LLaVA versions。作者也特别说明 `LMMs-Eval Lite` 更适合作为 model development / ablation 的快速信号，不应被理解为完全替代 full benchmark 的跨模型家族 leaderboard。

### Ablations / Analysis: Lite Dataset Sizes

| Task Domain | Dataset | Split | Full Size | Lite Size |
| --- | --- | --- | ---: | ---: |
| Doc & Infographic Understanding | ChartQA | test | 2500 | 400 |
| Doc & Infographic Understanding | DocVQA | val | 5349 | 400 |
| Doc & Infographic Understanding | InfoVQA | val | 2801 | 200 |
| Image Understanding & Captioning | Flickr30k | val | 31784 | 400 |
| Image Understanding & Captioning | NoCaps | val | 4500 | 400 |
| Image Understanding & Captioning | TextCaps | val | 3166 | 300 |
| Image Understanding & Captioning | RefCOCO | val | 8811 | 500 |
| Visual Question Answering | TextVQA | val | 5000 | 300 |
| Math & Science | MathVista | testmini | 1000 | 1000 |
| Math & Science | AI2D | test | 3088 | 300 |
| Visual Dialogue | LLaVA-W | test | 60 | 60 |
| Multi-discipline | MME | cog. & percep. | 2374 | 2374 |
| Multi-discipline | MMMU | val | 900 | 900 |
| Multi-discipline | CMMMU | val | 900 | 900 |
| Multi-discipline | Seed-Bench | test | 17990 | 700 |
| Total | Total | - | **90223** | **9134** |

### Ablations / Analysis: Contamination Signals

下表摘自 source 中的 `tables/contamination_results.tex`，用于说明论文的 data contamination concern。数值是相对 LLaVA-NeXT Data 的 overlap percentage。

| Dataset | Split | Image overlap (%) | Text overlap (%) |
| --- | --- | ---: | ---: |
| AI2D | test | 6.09 | 25.97 |
| ChartQA | test | 68.64 | 26.52 |
| DocVQA | val | 36.08 | 4.06 |
| COCO2014 | val | 46.05 | 22.19 |
| NoCaps | val | 2.53 | 19.98 |
| GQA | testdev-balanced | 13.91 | 9.50 |
| VQAv2 | val | 46.21 | 2.90 |
| POPE | val | 42.20 | 0.00 |

### Training / Compute

| Item | Value |
| --- | --- |
| Hardware for runtime estimates | 8 x A100 GPUs with flash attention enabled |
| Default parallelism | Data parallel; model weights replicated across GPUs |
| Large-model parallelism | Pipeline parallelism for models larger than 72B |
| LLaVA-NeXT-vicuna-7B runtime | Full 40 hrs; Lite 0.25 hrs |
| LLaVA-NeXT-LLaMA-8B runtime | Full 42 hrs; Lite 0.25 hrs |
| LLaVA-NeXT-34B runtime | Full 200 hrs; Lite 1 hr |
| LLaVA-NeXT-72B runtime | Full 1200 hrs; Lite 7.75 hrs |
| LLaVA-NeXT-110B runtime | Full 1450 hrs; Lite 9 hrs |

## Limitations & Caveats

- 论文假设 evaluation trilemma 很难被彻底解决，因此提出的是 trade-off，而不是一个 single best benchmark。
- Contamination detection 依赖训练数据访问；对 closed-source models 或未公开训练集的模型，方法不能直接使用。
- Text/image 8-gram overlap 是相对简单的启发式方法，能发现显式重叠，但未必覆盖语义级污染或经过改写的数据泄漏。
- `LMMs-Eval Lite` 的设计目标是降低开发周期评测成本；作者明确提醒它不适合作为完全公平的跨 model family 排行榜。
- `LiveBench` 的 QA 由模型辅助生成，即使有人审和 scorer，质量仍可能低于高成本人工 benchmark，也可能引入 judge model bias。
- LiveBench 的动态性带来复现压力：不同月份的问题集不同，需要明确 snapshot/version 才能做长期可比分析。

## Concrete Implementation Ideas

1. 在本地 model development pipeline 中使用两级评测：PR / nightly 用 `LMMs-Eval Lite`，release candidate 再跑 full `LMMs-Eval`。
2. 给每次评测保存完整 artifacts：prompt、chat template、generation、post-processing result、metric breakdown、model commit/hash，避免“同名 benchmark 不可比”。
3. 做一个轻量 contamination scanner：text 侧先用 normalized 8-gram lookup；image 侧如果没有 SEED-tokenizer，可先用 perceptual hash / CLIP embedding 近邻作为 proxy，再升级到 token overlap。
4. 如果要构造领域内部的 LiveBench，可以固定 monthly snapshot、source whitelist、QA generator prompt、judge prompt 和 human review rubric，让动态评测仍可审计。
5. 对 leaderboard 分数添加 cost metadata，例如 GPU hours、API cost、评测样本量和 judge model，这能让“高分”与“可负担”同时可见。

## Open Questions / Follow-ups

- 能否在没有 training data 的情况下可靠估计 multimodal contamination，尤其是 closed-source LMM？
- Lite subset 的 representative property 是否能跨 model family 泛化，还是主要对 LLaVA 系列可靠？
- 动态 benchmark 如何平衡 freshness 与 longitudinal comparability？每月更新会不会让历史分数难以解释？
- GPT-4o judge 与 human judges 的一致性如何量化？不同 judge model 会不会改变 LiveBench leaderboard 排序？
- 对 multimodal tasks 的 normalized aggregation 是否会掩盖某些关键能力退化，例如 OCR、chart reasoning、math reasoning、hallucination？

## Citation

```bibtex
@misc{zhang2025lmmseval,
  title = {LMMs-Eval: Reality Check on the Evaluation of Large Multimodal Models},
  author = {Zhang, Kaichen and Li, Bo and Zhang, Peiyuan and Pu, Fanyi and Cahyono, Joshua Adrian and Hu, Kairui and Liu, Shuai and Zhang, Yuanhan and Yang, Jingkang and Li, Chunyuan and Liu, Ziwei},
  year = {2025},
  eprint = {2407.12772},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  doi = {10.18653/v1/2025.findings-naacl.51},
  url = {https://arxiv.org/abs/2407.12772}
}
```

arXiv first version: 2024-07-17. Latest version checked here: v2, updated 2025-05-05.
