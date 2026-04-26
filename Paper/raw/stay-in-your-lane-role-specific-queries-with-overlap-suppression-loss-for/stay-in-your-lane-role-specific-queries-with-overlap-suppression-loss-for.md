---
title: "Stay in your Lane: Role Specific Queries with Overlap Suppression Loss for Dense Video Captioning"
authors:
  - Seung Hyup Baek
  - Jimin Lee
  - Hyeongkeun Lee
  - Jae Won Cho
conference: ""
year: 2026
paper_url: https://arxiv.org/abs/2603.11439v1
source_pdf: /Users/yifan/Downloads/Stay in your Lane Role Specific Queries with Overlap Suppression Loss for Dense Video Captioning.pdf
pdf_link: "[[assets/paper_arxiv_2603_11439v1.pdf]]"
cover: "[[assets/pipeline_arxiv_2603_11439v1.png]]"
updated: 2026-04-27
tags:
  - paper/arxiv
  - long-video
  - temporal-reasoning
  - DVC
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/MMAI-Konkuk/ROS-DVC
---

## TL;DR

- 这篇论文提出 ROS-DVC，用于 Dense Video Captioning 中同时做 event localization 和 caption generation。
- 核心观察是 query-based DVC 中共享 query 容易产生 multi-task interference，并且多个 query 会定位到重叠时间段，生成重复 caption。
- 方法把 localization queries 和 caption queries 显式分开，并用 Cross-Task Contrastive Alignment (CTCA) 让两类 query 在语义上保持匹配。
- Overlap Suppression Loss (OSL) 通过 query 间 temporal IoU 惩罚冗余重叠，同时用 ground-truth-aware 权重避免过度压制合理事件。
- Concept Guider 用轻量 MLP 预测 event-level concepts，作为训练期辅助目标增强 caption query 的语义表达。
- 在 YouCook2 和 ActivityNet Captions 上，ROS-DVC 在非预训练方法中取得有竞争力的 captioning 与 localization 结果。

## Key Contributions

1. 提出 Role Specific Query Initialization，将 localization 与 captioning 的 query 空间分离，减少共享 query 带来的任务干扰。
2. 提出 Cross-Task Contrastive Alignment (CTCA)，把匹配到同一事件的 localization query 和 caption query 拉近，并把不相关 query 推远。
3. 提出 Overlap Suppression Loss (OSL)，显式惩罚不同预测边界之间过大的 temporal overlap，缓解 DVC 中重复事件和重复 caption。
4. 加入 Concept Guider 辅助头，用训练 caption 中抽取的 noun/verb concepts 监督 caption query，提升语义丰富度，不依赖 external memory bank。

## Method

ROS-DVC 仍采用 query-based encoder-decoder DVC 框架：视频先经 pretrained visual encoder 和 transformer encoder 得到 frame-level features，decoder 中的 query 与视频特征交互，输出若干 event-caption pairs。

**Pipeline bullets**

1. 输入视频以 1 FPS 采样，使用 CLIP ViT-L/14 提取视觉特征，再经过 transformer encoder。
2. Decoder 使用两组独立 learnable embeddings：$\{q_{\text{loc}}^j\}_{j=1}^{K}$ 和 $\{q_{\text{cap}}^j\}_{j=1}^{K}$。
3. Localization queries 学习边界与 event count，caption queries 学习描述语义。
4. Hungarian matching 选择与 ground truth 对齐的事件，CTCA 将匹配的 query 对作为 positive pair。
5. OSL 基于不同预测边界之间的 temporal IoU 抑制冗余 overlap。
6. Caption Head 使用 LSTM 生成文本，Concept Guider 只在训练时作为 auxiliary concept prediction head。

CTCA 的核心形式为：

$$
\mathcal{L}_{\text{CTCA}} =
- \sum_{j \in \mathcal{M}}
\log
\frac{
\exp(\text{sim}(\tilde q_{\text{cap}}^j, \tilde q_{\text{loc}}^j)/\tau)
}{
\sum_{j'} \exp(\text{sim}(\tilde q_{\text{cap}}^j, \tilde q_{\text{loc}}^{j'})/\tau)
}
$$

OSL 先计算两个预测边界 $B_i, B_j$ 的重叠：

$$
P_o(i,j) = \operatorname{IoU}(B_i, B_j), \quad i \neq j
$$

再用预测边界与 ground-truth boundary $G_j$ 的 IoU 形成 ground-truth-aware 权重：

$$
P_g(i,j) = \operatorname{IoU}(B_i, G_j)
$$

$$
\alpha = \gamma \cdot P_g + (1-\gamma)\cdot(1-P_g)
$$

最终：

$$
\mathcal{L}_{\text{OSL}} = -\alpha \cdot \log(\beta - P_o)
$$

总损失为 standard DVC losses 加上 CTCA、OSL 与 Concept Guider：

$$
\mathcal{L}_{\text{total}} =
\lambda_{\text{giou}}\mathcal{L}_{\text{giou}} +
\lambda_{\text{cls}}\mathcal{L}_{\text{cls}} +
\lambda_{\text{cap}}\mathcal{L}_{\text{cap}} +
\lambda_{\text{ec}}\mathcal{L}_{\text{ec}} +
\lambda_{\text{CTCA}}\mathcal{L}_{\text{CTCA}} +
\lambda_{\text{OSL}}\mathcal{L}_{\text{OSL}} +
\lambda_{\text{CG}}\mathcal{L}_{\text{CG}}
$$

## Pipeline Figure

![[assets/pipeline_arxiv_2603_11439v1.png]]

Caption: Figure 2. An overview of our proposed ROS-DVC framework. The input video is first fed into the pretrained encoder, and a transformer encoder processes it to generate frame-level features. In the decoding stage, two types of queries are independently initialized and retrieve their role-specific information from the frame-level features. The output localization queries are trained with the Overlap Suppression Loss to minimize mutual overlap and are matched with ground truths via the Hungarian algorithm. Subsequently, the CTCA loss is employed to semantically align the caption queries with their corresponding localization queries. Finally, these processed queries are fed into respective heads to obtain the predictions for event-number, localize timestamps, event captions, and event-level concepts.

Source: PDF page 3 render, cropped to Figure 2 and its caption.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| YouCook2 | Dense Video Captioning | 1,333 train / 457 validation / 210 test | CIDEr, METEOR, BLEU-4, SODA_c, Recall, Precision, F1 | 2k untrimmed cooking videos, average length about 320s, average 7.7 annotated segments. |
| ActivityNet Captions | Dense Video Captioning | 10,009 train / 4,925 validation / 5,044 test | CIDEr, METEOR, BLEU-4, SODA_c, Recall, Precision, F1 | 20k untrimmed videos, average length about 120s, average 3.65 temporally localized sentences. Paper reports about 7% fewer usable videos due to unavailable YouTube videos. |

### Main Results: Captioning

PDF page 6 的 Table 1 和 Table 2。`#PT` 表示是否使用 pretrained / pretraining setting；论文说明 DDVC 使用 GPT-2 captioning head，因此不直接公平比较。

| Method | #PT | YouCook2 CIDEr | YouCook2 METEOR | YouCook2 BLEU4 | YouCook2 SODA_c | ActivityNet CIDEr | ActivityNet METEOR | ActivityNet BLEU4 | ActivityNet SODA_c |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vid2Seq | ✓ | 47.10 | 9.30 | - | 7.90 | 30.10 | 8.50 | - | 5.80 |
| DIBS | ✓ | 44.40 | 7.51 | - | 6.39 | 31.89 | 8.93 | - | 5.85 |
| DDVC | ✗ | 38.75 | 6.92 | 1.92 | 6.68 | 35.48 | 8.62 | 2.44 | 6.55 |
| PDVC | ✗ | 29.69 | 5.56 | 1.40 | 4.92 | 29.97 | 8.06 | 2.21 | 5.92 |
| CM2 | ✗ | 31.66 | 6.08 | 1.63 | 5.34 | 33.01 | 8.55 | 2.38 | 6.18 |
| MCCL | ✗ | 36.09 | 6.53 | 2.04 | 5.21 | 34.92 | 9.05 | 2.68 | 6.16 |
| E2 DVC | ✗ | 34.26 | 6.11 | 1.68 | 5.39 | 33.63 | 8.57 | 2.43 | 6.13 |
| **Ours** | ✗ | **39.18** | **6.14** | **2.10** | **7.06** | **35.04** | **8.45** | **2.36** | **6.45** |

### Main Results: Localization

PDF page 7 的 Table 3。YouCook2 上 ROS-DVC 在非预训练方法中 Recall、Precision、F1 均强；ActivityNet 上 Recall 最高，但 Precision 和 F1 不超过 DDVC / E2 DVC。

| Method | #PT | YouCook2 Rec. | YouCook2 Pre. | YouCook2 F1 | ActivityNet Rec. | ActivityNet Pre. | ActivityNet F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Vid2Seq | ✓ | 27.90 | 27.80 | 27.84 | 52.70 | 53.90 | 53.29 |
| DIBS | ✓ | 26.24 | 39.18 | 31.43 | 53.14 | 58.31 | 55.61 |
| DDVC | ✗ | 30.81 | 37.25 | 33.73 | 54.77 | 57.54 | 56.12 |
| PDVC | ✗ | 22.89 | 32.37 | 26.81 | 53.27 | 56.38 | 54.78 |
| CM2 | ✗ | 24.76 | 33.38 | 28.43 | 53.71 | 56.81 | 55.21 |
| MCCL | ✗ | - | - | - | 53.19 | 57.36 | 55.23 |
| E2 DVC | ✗ | 24.36 | 34.75 | 28.64 | 54.67 | 57.70 | 56.14 |
| **Ours** | ✗ | **29.34** | **35.26** | **32.03** | **55.35** | **55.65** | **55.50** |

### Ablations / Analysis

PDF page 7 的 Table 4。RSQI、CTCA、OSL、CG 都加入时取得最高 CIDEr、METEOR、BLEU4、SODA_c 和 F1。

| RSQI | CTCA | OSL | CG | CIDEr | METEOR | BLEU4 | SODA_c | F1 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ✗ | ✗ | ✗ | ✗ | 29.69 | 5.56 | 1.40 | 5.39 | 26.81 |
| ✓ | ✗ | ✗ | ✗ | 32.33 | 5.66 | 1.66 | 5.43 | 27.00 |
| ✗ | ✗ | ✓ | ✗ | 33.60 | 5.41 | 1.46 | 6.79 | 31.22 |
| ✗ | ✗ | ✗ | ✓ | 31.40 | 5.58 | 1.58 | 5.62 | 27.69 |
| ✓ | ✓ | ✗ | ✗ | 34.48 | 5.82 | 1.88 | 5.58 | 27.59 |
| ✓ | ✗ | ✓ | ✗ | 32.72 | 5.60 | 1.49 | 6.73 | 31.98 |
| ✓ | ✗ | ✗ | ✓ | 33.36 | 5.63 | 1.63 | 6.03 | 28.94 |
| ✗ | ✗ | ✓ | ✓ | 33.11 | 5.32 | 1.58 | 6.91 | 31.63 |
| ✓ | ✗ | ✓ | ✓ | 34.92 | 5.66 | 1.62 | 6.83 | 30.58 |
| ✓ | ✓ | ✓ | ✗ | 36.63 | 5.80 | 1.87 | 6.95 | 30.62 |
| ✓ | ✓ | ✗ | ✓ | 36.93 | 5.73 | 2.02 | 6.05 | 28.59 |
| **✓** | **✓** | **✓** | **✓** | **39.18** | **6.14** | **2.10** | **7.06** | **32.03** |

PDF page 7 的 Table 5。$\gamma=0.25$ 取得最高 CIDEr，$\gamma=0.35$ 的 SODA_c 和 F1 更高，说明 OSL 的 overlap 惩罚存在 captioning 与 localization 平衡。

| γ | CIDEr | SODA_c | Rec. | Pre. | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.15 | 37.00 | 6.69 | 29.65 | 35.44 | 32.28 |
| **0.25** | **39.18** | **7.06** | **29.34** | **35.26** | **32.03** |
| 0.35 | 37.49 | 7.16 | 30.80 | 35.28 | 32.88 |
| 0.45 | 35.76 | 6.94 | 30.40 | 34.43 | 32.28 |

PDF page 8 的 Table 6。加入 $\alpha$ 后 CIDEr 和 Precision 提升，但 Recall / F1 略降。

| α Setting | CIDEr | SODA_c | Rec. | Pre. | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| W/o α | 34.81 | 7.20 | 31.01 | 33.82 | 32.35 |
| **W/ α** | **39.18** | **7.06** | **29.34** | **35.26** | **32.03** |

PDF page 8 的 Table 7。论文认为 $N_q=50$ 在 captioning quality 和 event localization 之间最均衡。

| Nq | CIDEr | METEOR | BLEU4 | SODA_c | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 28.72 | 4.78 | 1.17 | 6.79 | 29.64 |
| 20 | 35.21 | 5.69 | 1.60 | 7.16 | 32.55 |
| 30 | 34.29 | 5.65 | 1.56 | 7.03 | 31.96 |
| 40 | 34.59 | 5.77 | 1.58 | 7.19 | 33.56 |
| **50** | **39.18** | **6.14** | **2.10** | **7.06** | **32.02** |
| 60 | 36.71 | 5.90 | 1.77 | 6.53 | 30.64 |
| 70 | 36.24 | 5.88 | 1.83 | 6.81 | 32.01 |
| 80 | 34.44 | 5.75 | 1.65 | 6.66 | 31.32 |
| 90 | 36.83 | 5.96 | 1.94 | 6.28 | 29.34 |
| 100 | 34.82 | 5.66 | 1.79 | 6.47 | 27.83 |

### Training / Compute

| Item | Value |
| --- | --- |
| Frame sampling | 1 FPS |
| Feature extractor | CLIP ViT-L/14 |
| Fixed frame length | 200 for YouCook2, 100 for ActivityNet |
| Decoder | 2-layer deformable transformer decoder with multi-scale deformable attention across four feature levels |
| Query count | 50 localization + 50 caption queries for YouCook2; 10 + 10 for ActivityNet Captions |
| OSL hyperparameters | $\gamma=0.25$, $\beta=1.0$ |
| Concept count | $N_C=30$ |

## Limitations & Caveats

- 论文没有报告训练成本、GPU 配置、训练时长或参数量，因此难以判断新增 query sets、CTCA、OSL、Concept Guider 的实际计算开销。
- ActivityNet localization 的 F1 并不是最优，说明 overlap suppression 对不同数据集的收益不完全一致。
- DDVC 使用 GPT-2 captioning head，论文也指出不直接公平比较；因此 captioning 对比需要区分是否使用额外语言模型能力。
- OSL 依赖 $\gamma$、$\beta$ 等超参数；Table 5 显示不同 $\gamma$ 会在 CIDEr、SODA_c、F1 之间产生 trade-off。
- Concept Guider 的 concepts 来自训练 caption 中 top nouns/verbs，可能受数据集语言分布影响，跨域泛化仍需验证。

## Concrete Implementation Ideas

1. 在现有 DETR-style temporal grounding / DVC 框架中，把共享 query 替换成 `loc_queries` 和 `cap_queries` 两个 embedding table，并保持 decoder cross-attention 输入结构一致。
2. 复现 CTCA 时先只对 Hungarian matched indices 计算 InfoNCE-style loss，避免对 unmatched queries 引入不稳定监督。
3. OSL 可以作为通用 temporal proposal regularizer，先在 validation 上扫 $\gamma \in \{0.15, 0.25, 0.35, 0.45\}$，同时观察 caption metrics 与 localization F1。
4. Concept Guider 可用 spaCy / dataset preprocessing 从训练 captions 中抽取 top nouns 和 verbs，训练时加 BCE / multi-label loss，推理时移除。
5. 对长视频 captioning 或 event segmentation 任务，可以把 OSL 改成 class-aware 或 confidence-aware overlap penalty，避免压制真实相邻事件。

## Open Questions / Follow-ups

- CTCA 是 asymmetric caption-to-localization contrastive objective；双向对齐是否会进一步改善 caption query 的 temporal grounding？
- OSL 是否会在事件高度密集、真实 overlap 较多的数据集上损伤 recall？
- Concept Guider 的 top noun/verb concepts 是否可以替换为开放词表 visual concepts 或 CLIP text prototypes？
- 与 LLM-based caption head 结合时，role-specific queries 和 OSL 的收益是否仍然明显？
- 论文代码已给出，值得检查实现中 OSL 的 pairwise query selection、masking、以及 unmatched queries 的处理方式。

## Citation

```bibtex
@misc{baek2026staylane,
  title = {Stay in your Lane: Role Specific Queries with Overlap Suppression Loss for Dense Video Captioning},
  author = {Baek, Seung Hyup and Lee, Jimin and Lee, Hyeongkeun and Cho, Jae Won},
  year = {2026},
  eprint = {2603.11439},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  doi = {10.48550/arXiv.2603.11439},
  url = {https://arxiv.org/abs/2603.11439v1}
}
```
