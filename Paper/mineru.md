---
title: "Video-ChatGPT: Towards Detailed Video Understanding via Large Vision and Language Models"
authors: ["Muhammad Maaz", "Hanoona Rasheed", "Salman Khan", "Fahad Shahbaz Khan"]
conference: "ACL"
year: 2024
paper_url: "https://aclanthology.org/2024.acl-long.679/"
source_pdf: "https://aclanthology.org/2024.acl-long.679.pdf"
pdf_link: "[[assets/paper_2024_acl_long_679.pdf]]"
cover: "[[assets/pipeline_2024_acl_long_679.png]]"
updated: 2026-04-27
tags: ["paper/pdf", "video-llm", "video-qa", "temporal-reasoning"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://github.com/mbzuai-oryx/Video-ChatGPT"
---

## TL;DR

- Video-ChatGPT 把 CLIP ViT-L/14 visual encoder 和 Vicuna-v1.1 7B LLM 连接起来，用一个线性投影层把视频的 spatiotemporal features 对齐到 LLM embedding space。
- 论文构建了 100,000 video-instruction pairs，来源是 human-assisted annotation 与 semi-automatic annotation 的组合，用来训练视频对话模型。
- 方法只训练 video feature 到 LLM token space 的 linear adapter，visual encoder 与 LLM 保持冻结，因此训练成本相对低：论文报告 8 张 A100 40GB 上约 3 小时。
- 论文提出了 video conversation 的 quantitative evaluation framework，覆盖 correctness、detail orientation、contextual understanding、temporal understanding、consistency 五个维度。
- 在 zero-shot VideoQA 上，Video-ChatGPT 在 MSVD-QA、MSRVTT-QA、TGIF-QA、ActivityNet-QA 的 accuracy/score 上整体优于对比模型。

## Key Contributions

1. 提出 Video-ChatGPT，一个面向 video-based conversation 的 multimodal model，核心是把视频表示通过 adapter 接到 Vicuna LLM。
2. 构建 100K video-instruction 数据，结合人工增强 caption 与半自动 caption/QA 生成流程，覆盖 temporal、spatial、reasoning、creative generation 等视频问答场景。
3. 设计 video conversation 的定量评测框架，使用 GPT-assisted evaluation 从五个维度评价开放式视频回答质量。
4. 给出较完整的实验、ablation 与风险说明，特别关注 semi-automatic annotation、evaluation LLM 替换、long-video temporal reasoning 等问题。

## Method

Video-ChatGPT 从 LLaVA 出发，把 image-based visual encoder 改造成视频输入的 spatiotemporal feature extractor：

- 输入视频 $V_i \in \mathbb{R}^{T \times H \times W \times C}$，CLIP visual encoder 按帧产生 frame-level embeddings $x_i \in \mathbb{R}^{T \times h \times w \times D}$。
- 对 spatial dimension 平均池化得到 temporal representation $t_i \in \mathbb{R}^{T \times D}$。
- 对 temporal dimension 平均池化得到 spatial representation $z_i \in \mathbb{R}^{N \times D}$。
- 拼接得到 video-level features：

$$
v_i = \left[\begin{array}{c c} t_i & z_i \end{array}\right] \in \mathbb{R}^{(T + N) \times D}.
$$

- 使用 trainable linear layer $g$ 投影到 language decoder embedding space：

$$
Q_v = g(v_i) \in \mathbb{R}^{(T + N) \times K}.
$$

- 将 video tokens $Q_v$ 与 text query tokens $Q_t$ 拼接后输入 Vicuna decoder。训练时冻结 video encoder 与 LLM，只更新 linear adapter。

Compact pipeline:

```text
video frames -> CLIP ViT-L/14 -> temporal pooling + spatial pooling
-> concatenate spatiotemporal features -> linear projection
-> Vicuna token space -> video-grounded response
```

## Pipeline Figure

![[assets/pipeline_2024_acl_long_679.png]]

Caption: Figure 1, Architecture of Video-ChatGPT. Video-ChatGPT 使用 CLIP-L/14 visual encoder 提取 spatial 与 temporal video features，经 learnable linear layer 投影到 Vicuna-v1.1 7B 的输入空间。

Source: MinerU extracted image from ACL PDF, Figure 1.

## Experiments

Datasets / Benchmarks:

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| 100K video-instruction pairs | Instruction tuning | train | training data quality | 30% human-assisted annotation, 70% semi-automatic annotation |
| ActivityNet-200 | Video-based text generation benchmark | test set curated by authors | 5 aspect scores | 使用 dense descriptive captions 与 human QA pairs |
| MSVD-QA | Zero-shot VideoQA | evaluation | Accuracy, Score | GPT-assisted evaluation |
| MSRVTT-QA | Zero-shot VideoQA | evaluation | Accuracy, Score | GPT-assisted evaluation |
| TGIF-QA | Zero-shot VideoQA | evaluation | Accuracy, Score | FrameQA setting |
| ActivityNet-QA | Zero-shot VideoQA | evaluation | Accuracy, Score | open-ended QA |

Main results: video conversation quality benchmark.

| Evaluation Aspect | Video Chat | LLaMA Adapter | Video-LLaMA | Video-ChatGPT |
| --- | ---: | ---: | ---: | ---: |
| Correctness of Information | 2.23 | 2.03 | 1.96 | **2.40** |
| Detail Orientation | 2.50 | 2.32 | 2.18 | **2.52** |
| Contextual Understanding | 2.53 | 2.30 | 2.16 | **2.62** |
| Temporal Understanding | 1.94 | 1.98 | 1.82 | **1.98** |
| Consistency | 2.24 | 2.15 | 1.79 | **2.37** |

Main results: zero-shot question answering.

| Model | MSVD-QA Acc. | MSVD-QA Score | MSRVTT-QA Acc. | MSRVTT-QA Score | TGIF-QA Acc. | TGIF-QA Score | ActivityNet-QA Acc. | ActivityNet-QA Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FrozenBiLM | 32.2 | - | 16.8 | - | 41.0 | - | 24.7 | - |
| Video Chat | 56.3 | 2.8 | 45.0 | 2.5 | 34.4 | 2.3 | 26.5 | 2.2 |
| LLaMA Adapter | 54.9 | 3.1 | 43.8 | 2.7 | - | - | 34.2 | 2.7 |
| Video LLaMA | 51.6 | 2.5 | 29.6 | 1.8 | - | - | 12.4 | 1.1 |
| **Video-ChatGPT** | **64.9** | **3.3** | **49.3** | **2.8** | **51.4** | **3.0** | **35.2** | **2.8** |

Ablations: annotation source.

| Metric | Human only | Automatic only | Combined |
| --- | ---: | ---: | ---: |
| Correctness | 2.27 | 2.35 | **2.40** |
| Detail Orientation | 2.49 | 2.49 | **2.52** |
| Contextual Understanding | 2.50 | 2.56 | **2.62** |
| Temporal Understanding | 1.85 | 1.92 | **1.98** |
| Consistency | 2.21 | **2.38** | 2.37 |
| Average | 2.28 | 2.34 | **2.38** |

Ablations: evaluation with Vicuna-1.5 13B instead of GPT-3.5-Turbo.

| Metric | Video Chat | Video-LLaMA | Video-ChatGPT |
| --- | ---: | ---: | ---: |
| Correctness | 2.32 | 2.10 | **2.49** |
| Detail Orientation | 2.50 | 2.18 | **2.52** |
| Contextual Understanding | 2.76 | 2.41 | **2.85** |
| Temporal Understanding | 2.27 | 2.17 | **2.38** |
| Consistency | 2.95 | 2.67 | **3.09** |

Training / Compute:

| Item | Value |
| --- | --- |
| Visual encoder | CLIP ViT-L/14 from LLaVA |
| LLM | Vicuna-v1.1 7B |
| Trainable module | Linear projection layer / adapter |
| Frozen modules | Visual encoder and LLM |
| Epochs | 3 |
| Learning rate | $2e^{-5}$ as reported |
| Batch size | 32 |
| Hardware | 8 A100 40GB GPUs |
| Training time | around 3 hours |
| Inference precision | FP16 |

## Limitations & Caveats

- 对 subtle temporal relationships in long videos $(>2\mathrm{min})$ 仍然困难，长视频细粒度时间关系可能削弱预测质量。
- 对 small objects 的细节识别不稳定，可能漏掉小物体携带的关键信息。
- 训练数据构建和评测都使用了 GPT 系列模型，虽然论文用 Vicuna-1.5 做了替代评测，但 GPT-assisted pipeline 仍可能带来评测偏差。
- 数据创建过程中作者强调尽量减少 bias，但仍承认 residual bias 可能存在。
- 论文的 open-ended video conversation 评测依赖 LLM judge，分数应理解为相对评估，而不是完全客观的任务指标。

## Concrete Implementation Ideas

1. 复现时优先把 adapter-only training 作为最小可行版本：冻结 CLIP 与 Vicuna，仅训练 linear projector，验证成本较低。
2. 在长视频任务上加入 chunking 或 temporal memory，再对比原始 temporal pooling 方案，专门检验 $>2\mathrm{min}$ 场景。
3. 把论文的五维 evaluation rubric 做成可替换 judge 模块，同时跑 GPT、Vicuna、Qwen/InternVL 类 judge，观察分数稳定性。
4. 对 100K video-instruction 数据做 provenance / difficulty tagging，区分 human-assisted 与 semi-automatic 样本对不同能力的贡献。
5. 在 RAG 或 agent 场景中，将 Video-ChatGPT 输出作为 video event retrieval 的自然语言接口，而不是单独做 QA demo。

## Open Questions / Follow-ups

- Temporal pooling 是否足够表达复杂事件顺序？对于多阶段、长跨度 action 的 failure case 需要更多可视化。
- Semi-automatic annotation 中 GPT-3.5 后处理是否会引入语言模式偏置，导致模型更擅长回答“像 GPT 生成的问题”？
- Video-ChatGPT 与后续更强 video-LLM 的差距主要来自 backbone、data scale、temporal modeling，还是 evaluation protocol？
- 表格中的 score 是 GPT-assisted 1-5 相对分，跨论文比较时需要确认 judge prompt 与 test set 是否一致。

## Citation

```bibtex
@inproceedings{maaz-etal-2024-video,
    title = "Video-{C}hat{GPT}: Towards Detailed Video Understanding via Large Vision and Language Models",
    author = "Maaz, Muhammad  and
      Rasheed, Hanoona  and
      Khan, Salman  and
      Khan, Fahad",
    editor = "Ku, Lun-Wei  and
      Martins, Andre  and
      Srikumar, Vivek",
    booktitle = "Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
    month = aug,
    year = "2024",
    address = "Bangkok, Thailand",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2024.acl-long.679/",
    doi = "10.18653/v1/2024.acl-long.679",
    pages = "12585--12602"
}
```

