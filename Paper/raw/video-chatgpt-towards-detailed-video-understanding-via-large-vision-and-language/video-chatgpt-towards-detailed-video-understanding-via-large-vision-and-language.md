---
title: "Video-ChatGPT: Towards Detailed Video Understanding via Large Vision and Language Models"
authors: ["Muhammad Maaz", "Hanoona Rasheed", "Salman Khan", "Fahad Shahbaz Khan"]
conference: "ACL"
year: 2024
paper_url: "https://aclanthology.org/2024.acl-long.679/"
source_pdf: "https://aclanthology.org/2024.acl-long.679.pdf"
pdf_link: "[[assets/paper_2024.acl-long.679.pdf]]"
cover: "[[assets/pipeline_2024.acl-long.679.png]]"
updated: 2026-04-27
tags: ["paper/pdf", "video-qa", "video-llm", "temporal-reasoning", "benchmark"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://github.com/mbzuai-oryx/Video-ChatGPT"
---

## TL;DR

- Video-ChatGPT 是一个面向视频对话的 multimodal model，把 CLIP ViT-L/14 的视频化视觉特征对齐到 Vicuna-v1.1 7B 的输入空间，用于开放式视频问答和描述。
- 核心建模很轻量：冻结 visual encoder 和 LLM，只训练一个 linear projection layer，把 temporal features 和 spatial features 映射为 language embedding tokens。
- 论文贡献不只在模型，还包括 100K video-instruction pairs。数据来自 human-assisted annotation 与 semi-automatic annotation，再用 GPT-3.5 做 QA/instruction 生成与后处理。
- 评估上提出 video-based text generation benchmark，从 Correctness、Detail Orientation、Contextual Understanding、Temporal Understanding、Consistency 五个维度打分。
- 结果显示 Video-ChatGPT 在 GPT-3.5 评价、Vicuna-1.5 评价和 zero-shot VideoQA 上整体优于 Video Chat、Video-LLaMA、LLaMA Adapter 等 contemporaneous baselines；但长视频细粒度时间关系和小物体细节仍是弱点。

## Key Contributions

1. 提出 Video-ChatGPT，将 image-based LLaVA 适配到 video conversation：使用 CLIP ViT-L/14 提取帧级特征，聚合成 spatial/temporal video representations，再接入 Vicuna language decoder。
2. 构建 100,000 条 video-instruction pairs，结合人工丰富标注和可扩展的 semi-automatic annotation pipeline，覆盖描述、总结、QA、创意生成和多轮对话任务。
3. 设计 GPT-assisted quantitative evaluation framework，用五个维度比较视频对话模型生成质量，而不仅是传统 QA accuracy。
4. 在 MSVD-QA、MSRVTT-QA、TGIF-QA、ActivityNet-QA 和开放式 generation benchmark 上验证模型，并用 ablation 说明 human + automatic data 的组合效果最好。

## Method

Video-ChatGPT 从 LLaVA 出发，保留 CLIP visual encoder 与 Vicuna language decoder 的能力，把视频拆成 $T$ 帧并批量输入 image encoder。设视频样本为 $V_i \in \mathbb{R}^{T \times H \times W \times C}$，visual encoder 输出帧级 patch embedding：

$$
x_i \in \mathbb{R}^{T \times h \times w \times D}, \quad N = h \times w
$$

然后用两种平均池化形成 video-level features：

- temporal representation：对空间维度平均，得到 $t_i \in \mathbb{R}^{T \times D}$，保留跨帧变化。
- spatial representation：对时间维度平均，得到 $z_i \in \mathbb{R}^{N \times D}$，保留整体空间布局。
- 拼接两者：

$$
v_i = [t_i\ z_i] \in \mathbb{R}^{(T+N)\times D}
$$

训练一个线性层 $g$ 将视频特征投影到 LLM embedding space：

$$
Q_v = g(v_i) \in \mathbb{R}^{(T+N)\times K}
$$

文本 query 被 tokenized 为 $Q_t \in \mathbb{R}^{L\times K}$，随后与 $Q_v$ 拼接后送入 language decoder。训练时 visual encoder 与 LLM 均冻结，只更新 projection layer，并用 autoregressive objective 预测回答 token。

紧凑流程：

```text
Input video -> sample frames
CLIP ViT-L/14 -> frame-level embeddings
Spatial pooling -> temporal features
Temporal pooling -> spatial features
Concatenate features -> linear projection
Projected video tokens + user instruction -> Vicuna decoder
Generate video-grounded answer
```

训练 prompt 模板：

```text
USER: <Instruction> <Vid-tokens>
Assistant: <Answer>
```

数据构建流程：

- Human-assisted annotation：从 ActivityNet-200 等 video-caption 数据出发，由人工补充物体关系、空间位置、时间顺序、scene details 和 reasoning context。
- Semi-automatic annotation：用 Katna 抽 keyframes，用 BLIP-2 生成 frame captions，用 GRiT 生成 dense captions，用 Tag2Text 生成 tags 并过滤噪声。
- GPT-assisted postprocessing：用 GPT-3.5 基于丰富后的 captions 生成 instruction QA、summarization、creative/generative 和 conversation 数据。

## Pipeline Figure

![[assets/pipeline_2024.acl-long.679.png]]

Caption: Figure 1: Architecture of Video-ChatGPT. Video-ChatGPT uses CLIP-L/14 to extract spatial and temporal video features, averages frame-level features across temporal/spatial dimensions, projects them through a learnable linear layer, and feeds them into Vicuna-v1.1 7B initialized from LLaVA.

Source: PDF page 4 embedded image, extracted from Figure 1 and composited with its soft mask onto a white background for readable Obsidian rendering.

## Experiments

### Datasets / Benchmarks

| Dataset / Benchmark | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| ActivityNet-200 | video-caption enrichment, instruction data creation | subset used for training data generation | not reported | 人工标注与 semi-automatic pipeline 都从 video-caption pairs 出发；论文最终得到 100K video-instruction pairs。 |
| ActivityNet-200 based test set | open-ended video text generation benchmark | curated test set | 1-5 relative score over five aspects | 使用 GPT-3.5 评价 Correctness、Detail Orientation、Contextual Understanding、Temporal Understanding、Consistency。 |
| MSVD-QA | zero-shot open-ended VideoQA | not reported | Accuracy, GPT-assisted score | 与 FrozenBiLM、Video Chat、LLaMA Adapter、Video-LLaMA 比较。 |
| MSRVTT-QA | zero-shot open-ended VideoQA | not reported | Accuracy, GPT-assisted score | 同上。 |
| TGIF-QA FrameQA | zero-shot open-ended VideoQA | not reported | Accuracy, GPT-assisted score | 部分 baseline 未报告。 |
| ActivityNet-QA | zero-shot open-ended VideoQA | not reported | Accuracy, GPT-assisted score | 同上。 |

### Training / Compute

| Item | Value |
| --- | --- |
| Base model | LLaVA initialized model with CLIP ViT-L/14 visual encoder and Vicuna-v1.1 7B language decoder |
| Trainable parameters | linear projection layer only |
| Frozen components | visual encoder and LLM |
| Instruction data | 100K video-instruction pairs |
| Epochs | 3 |
| Learning rate | $2 \times 10^{-5}$ |
| Batch size | 32 |
| Hardware | 8 A100 40GB GPUs |
| Training time | around 3 hours |
| Inference precision | FP16 |
| Semi-automatic extraction | Katna keyframes, Tag2Text Swin-B input size $384 \times 384$, confidence threshold 0.7, GRiT ViT-B with CenterNet2 |

### Main Results

Table 1 来自 PDF page 7。它比较开放式视频文本生成的五个维度，分数范围是 1-5。

| Method | Correctness | Detail Orientation | Contextual Understanding | Temporal Understanding | Consistency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Video Chat | 2.23 | 2.50 | 2.53 | 1.94 | 2.24 |
| LLaMA Adapter | 2.03 | 2.32 | 2.30 | 1.98 | 2.15 |
| Video-LLaMA | 1.96 | 2.18 | 2.16 | 1.82 | 1.79 |
| **Video-ChatGPT** | **2.40** | **2.52** | **2.62** | **1.98** | **2.37** |

Table 2 来自 PDF page 8。论文说明所有可比模型使用 7B variants；FrozenBiLM 没有报告 score。

| Method | MSVD-QA Acc. | MSVD-QA Score | MSRVTT-QA Acc. | MSRVTT-QA Score | TGIF-QA Acc. | TGIF-QA Score | ActivityNet-QA Acc. | ActivityNet-QA Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FrozenBiLM | 32.2 | - | 16.8 | - | 41.0 | - | 24.7 | - |
| Video Chat | 56.3 | 2.8 | 45.0 | 2.5 | 34.4 | 2.3 | 26.5 | 2.2 |
| LLaMA Adapter | 54.9 | 3.1 | 43.8 | 2.7 | - | - | 34.2 | 2.7 |
| Video-LLaMA | 51.6 | 2.5 | 29.6 | 1.8 | - | - | 12.4 | 1.1 |
| **Video-ChatGPT** | **64.9** | **3.3** | **49.3** | **2.8** | **51.4** | **3.0** | **35.2** | **2.8** |

### Ablations / Analysis

Table 3 来自 PDF page 9。它比较只用 human data、只用 automatic data、以及两者结合的训练结果。Combined 是最终推荐设置。

| Variant / Setting | Correctness | Detail Orientation | Contextual Understanding | Temporal Understanding | Consistency | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Human only | 2.27 | 2.49 | 2.50 | 1.85 | 2.21 | 2.28 |
| Automatic only | 2.35 | 2.49 | 2.56 | 1.92 | 2.38 | 2.34 |
| **Combined** | **2.40** | **2.52** | **2.62** | **1.98** | **2.37** | **2.38** |

Table 4 来自 PDF page 9。作者用 open-source Vicuna-1.5 13B 替代 GPT-3.5 做评价，趋势与 GPT-3.5 评价相近。

| Method | Correctness | Detail Orientation | Contextual Understanding | Temporal Understanding | Consistency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Video Chat | 2.32 | 2.50 | 2.76 | 2.27 | 2.95 |
| Video-LLaMA | 2.10 | 2.18 | 2.41 | 2.17 | 2.67 |
| **Video-ChatGPT** | **2.49** | **2.52** | **2.85** | **2.38** | **3.09** |

作者还做了一个 human vs semi-automatic QA 来源盲测：从 50 个随机视频抽样，人类区分两类 QA pair 的准确率为 52%，接近随机，作者据此认为 semi-automatic data 与人工数据在主观质量上较接近。

## Limitations & Caveats

- 长视频中的 subtle temporal relationships 仍然困难，尤其是超过 2 分钟的视频，模型预测性能会受影响。
- 小物体和细节识别较弱，容易漏掉局部信息。
- 自动标注 pipeline 依赖 BLIP-2、GRiT、Tag2Text 和 GPT-3.5，训练数据可能继承这些模型的偏差或错误。
- 评估本身依赖 GPT-assisted scoring。虽然作者补充了 Vicuna-1.5 13B 评价，但这类 LLM-as-judge 仍可能带来评分偏差。
- PDF table extraction 没有识别出表格网格；上面的数值根据 PDF layout text 在 page 7-9 手工重建。

## Concrete Implementation Ideas

1. 用同样的 lightweight adapter 思路快速适配新 video encoder：先冻结 backbone，只训练 video-to-LLM projection，作为低成本 baseline。
2. 数据侧可以复用 human-assisted + semi-automatic 的混合策略：人工标一小部分高质量样本，自动扩展大规模样本，再用 tag filtering 降低 caption hallucination。
3. 评估视频对话模型时不要只看 VideoQA accuracy，可以加入五维 rubric：correctness、detail、context、temporal、consistency。
4. 针对长视频弱点，可尝试 hierarchical temporal memory、event segmentation 或 retrieval over temporal chunks，再把检索到的片段作为 video tokens/context。
5. 针对小物体弱点，可在 keyframe selection 后加入 region-level detector/dense captioner，或把 high-resolution crops 作为额外视觉 token。

## Open Questions / Follow-ups

- 只训练 linear layer 的上限在哪里？如果解冻部分 visual encoder 或加入 temporal transformer，长视频 temporal understanding 是否会明显提升？
- GPT-assisted evaluation 与人工评价的一致性如何量化？论文只报告了数据来源盲测，没有完整的人类偏好评分相关性。
- 100K instruction data 的具体类别分布、prompt 模板和质量过滤阈值会多大程度影响模型能力？
- Video-ChatGPT 对真实多轮对话中的上下文累积、指代消解和纠错能力如何？
- 如果换成更强的 LLM 或 video foundation model，性能提升来自语言能力、视频表征，还是 instruction data？

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
