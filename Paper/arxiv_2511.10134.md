---
title: "Explicit Temporal-Semantic Modeling for Dense Video Captioning via Context-Aware Cross-Modal Interaction"
authors:
  - "Mingda Jia"
  - "Weiliang Meng"
  - "Zenghuang Fu"
  - "Yiheng Li"
  - "Qi Zeng"
  - "Yifan Zhang"
  - "Ju Xin"
  - "Rongtao Xu"
  - "Jiguang Zhang"
  - "Xiaopeng Zhang"
arxiv_id: "2511.10134"
arxiv_url: "https://arxiv.org/abs/2511.10134"
pdf_url: "https://arxiv.org/pdf/2511.10134.pdf"
published: 2025-11-13
updated: 2026-02-19
categories: ["cs.CV"]
tags: ["paper/arxiv", "video-understanding", "dense-video-captioning", "status/read"]
status: "read"
code: ""
datasets: ["ActivityNet Captions", "YouCook2"]
---

## TL;DR
- 提出 CACMI（Context-Aware Cross-Modal Interaction），用于密集视频描述中的显式时序-语义建模。
- 核心由两部分组成：CFA（跨模态帧聚合）和 CFE（上下文感知特征增强）。
- CFA 先做伪事件聚类，再从句子库检索与事件对齐的文本语义；CFE 用 query-guided attention 融合视觉动态与检索语义。
- 在 ActivityNet Captions 和 YouCook2 上，论文报告 captioning 与 localization 都优于非预训练基线，并达到/刷新 SOTA。
- 消融显示：`N_cluster=10`、`top-k=40` 最优，说明“检索语义量”与“事件粒度”都需要平衡。

## Key Contributions
- 提出显式 temporal-semantic 建模框架，缓解现有 RAG DVC 方法中“固定窗口导致时序割裂”和“视觉-文本模态鸿沟”。
- 设计 CFA：
  - Event Context Clustering：按时序与语义一致性聚合帧级特征为伪事件。
  - Event Semantic Retrieval：用聚合后的事件特征到文本记忆库进行检索，获得事件对齐语义。
- 设计 CFE：通过上下文 query 引导的跨模态注意力进行特征增强，提升事件定位与描述一致性。
- 在两个 DVC 基准上提供系统实验与消融，验证方法有效性。

## Method
Pipeline（紧凑版）:
1. 逐帧采样并通过预训练 CLIP 图像编码器提取帧特征。
2. CFA: 对帧特征做事件上下文聚类，得到伪事件中心；再从句子库检索 top-k 语义。
3. CFE: 用查询引导注意力融合视觉特征与检索文本特征，生成增强帧特征。
4. 将增强特征送入 Deformable Transformer encoder-decoder。
5. 多任务头联合预测：
   - Localization Head: 回归事件边界 `(t_s, t_e, c)`；
   - Captioning Head: LSTM + deformable soft attention 解码描述；
   - Event Counter: 预测事件个数。
6. Hungarian matching 对齐预测与 GT 事件，联合优化分类、定位、计数与描述损失。

Compact pseudocode:
```text
V -> CLIP frame features F
F -> CFA clustering -> pseudo events E
E + sentence bank -> retrieval top-k text features T
(F, T, queries) -> CFE -> enhanced features F'
F' -> deformable transformer -> event queries Q
Q -> {localization, captioning, event counting}
Train with L = a_cls*L_cls + a_loc*L_loc + a_count*L_count + a_cap*L_cap
```

## Experiments
### Datasets table
| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---|---|---|
| ActivityNet Captions | Dense Video Captioning | Train 10,024 / Val 4,926 / Test 5,044 | Captioning: BLEU4, METEOR, CIDEr, SODA_c; Localization: F1/Recall/Precision (IoU 0.3/0.5/0.7/0.9 平均) | ~20k 视频, >700h, 平均 3.7 captions/video |
| YouCook2 | Dense Video Captioning | 标准划分（论文未给精确三段计数） | 同上 | 2,000 视频, 176h, 平均 7.7 captions/video；仅使用仍可访问视频（比原始少约 7%） |

### Main results table(s)
| Dataset              | Metric |     Baseline |  Ours |     Δ |
| -------------------- | ------ | -----------: | ----: | ----: |
| ActivityNet Captions | BLEU4  | E²DVC:  2.43 |  2.44 | +0.01 |
| ActivityNet Captions | METEOR | E²DVC:  8.57 |  8.68 | +0.11 |
| ActivityNet Captions | CIDEr  | E²DVC: 33.63 | 33.80 | +0.17 |
| ActivityNet Captions | SODA_c |  E²DVC: 6.13 |  6.39 | +0.26 |
| YouCook2             | BLEU4  |  E²DVC: 1.68 |  1.70 | +0.02 |
| YouCook2             | METEOR |  E²DVC: 6.11 |  6.21 | +0.10 |
| YouCook2             | CIDEr  | E²DVC: 34.26 | 34.83 | +0.57 |
| YouCook2             | SODA_c |  E²DVC: 5.39 |  5.57 | +0.18 |

| Dataset              | Metric    |     Baseline |  Ours |     Δ |
| -------------------- | --------- | -----------: | ----: | ----: |
| ActivityNet Captions | F1        | E²DVC: 56.42 | 57.10 | +0.68 |
| ActivityNet Captions | Recall    | E²DVC: 55.14 | 55.89 | +0.75 |
| ActivityNet Captions | Precision | E²DVC: 57.77 | 58.05 | +0.28 |
| YouCook2             | F1        | E²DVC: 28.87 | 29.34 | +0.47 |
| YouCook2             | Recall    | E²DVC: 25.01 | 25.54 | +0.53 |
| YouCook2             | Precision | E²DVC: 34.13 | 34.63 | +0.50 |

### Training / Compute
| Item | Value |
|---|---|
| Visual backbone | CLIP image encoder |
| Frame sampling | 1 FPS |
| Input frames F | ActivityNet: 100, YouCook2: 200 |
| Event queries | ActivityNet: 10, YouCook2: 100 |
| #clusters (CFA) | ActivityNet: 10, YouCook2: 20 |
| Retrieval top-k | 40 |
| Other hyperparameters | 与 CM² 对齐 |
| Hardware | NVIDIA RTX A6000（论文写法为单数，具体 GPU 数量未报告） |

### Ablations/Analysis tables
| Ablation | Setting | BLEU4 | METEOR | CIDEr | SODA_c | F1 |
|---|---|---:|---:|---:|---:|---:|
| Components | No CFA / No CFE | 2.38 | 8.55 | 33.01 | 6.18 | 55.21 |
| Components | CFA only | 2.37 | 8.63 | 33.62 | 6.26 | 56.07 |
| Components | CFE only | 2.41 | 8.59 | 33.48 | 6.31 | 56.95 |
| Components | CFA + CFE | **2.44** | **8.68** | **33.80** | **6.39** | **57.10** |

| Ablation | Setting | BLEU4 | METEOR | CIDEr | SODA_c | F1 |
|---|---|---:|---:|---:|---:|---:|
| #event clusters | 3 | 2.32 | 8.53 | 32.84 | 6.12 | 54.91 |
| #event clusters | 5 | 2.35 | 8.58 | 33.15 | 6.21 | 54.87 |
| #event clusters | 7 | 2.36 | 8.63 | 33.24 | 6.28 | 56.02 |
| #event clusters | **10** | **2.44** | **8.68** | **33.80** | **6.39** | **57.10** |
| #event clusters | 15 | 2.28 | 8.49 | 32.98 | 6.19 | 55.15 |
| #event clusters | γ (adaptive) | 2.34 | 8.60 | 33.43 | 6.29 | 56.23 |

| Ablation | Setting | BLEU4 | METEOR | CIDEr | SODA_c | F1 |
|---|---|---:|---:|---:|---:|---:|
| top-k retrieval | 10 | 2.23 | 8.49 | 32.20 | 6.32 | 55.95 |
| top-k retrieval | 20 | 2.31 | 8.60 | 32.26 | 6.21 | 55.50 |
| top-k retrieval | **40** | **2.44** | **8.68** | **33.80** | **6.39** | **57.10** |
| top-k retrieval | 60 | 2.27 | 8.50 | 32.25 | 6.25 | 56.39 |
| top-k retrieval | 80 | 2.25 | 8.53 | 32.57 | 6.27 | 56.15 |

## Limitations & Caveats
- 论文将性能提升部分归因于显式时序-语义建模，但缺少更细粒度的误差分解（如不同事件时长/语义类型分桶分析）。
- 依赖外部句子记忆库质量；若检索语料域偏移，可能影响跨模态对齐效果。
- 计算/资源报告不完整（如训练轮数、batch size、学习率、GPU 数量未明确报告）。
- YouCook2 上与预训练方法（如 Vid2Seq）相比仍有差距，说明在小数据高语义多样场景下仍有改进空间。

## Concrete Implementation Ideas
- 在 InternVL 或 LLaVA-NeXT 的视频问答推理阶段，引入“伪事件聚类 + 每事件检索 top-k 文本”作为前处理，再让模型逐事件回答并汇总。
- 把 CFE 思路改写为轻量 inference-time cross-attention adapter：视觉 token 作为 query，检索文本作为 key/value，只在推理时插入。
- 对长视频先做自适应事件聚类（类似 `N_cluster=gamma`）再分段问答，减少固定窗口截断带来的上下文丢失。
- 做“检索数量扫描”（top-k=10/20/40/60）与答案一致性评估，选择任务最优 k，而不是固定默认值。

## Open Questions / Follow-ups
- 句子记忆库具体来源与构建细节（数据过滤、去重、质量控制）是否可复现？
- 如果替换 CLIP 为更强视觉编码器，增益主要来自检索模块还是编码器本身？
- 在极长视频（>30min）与高事件密度视频上，聚类与检索成本如何扩展？
- 该方法是否能迁移到 zero-shot video QA 的“事件级证据检索 + 答案生成”流程中，并保持延迟可接受？

## Citation
```bibtex
@misc{jia2025explicittemporalsemanticmodelingdense,
      title={Explicit Temporal-Semantic Modeling for Dense Video Captioning via Context-Aware Cross-Modal Interaction}, 
      author={Mingda Jia and Weiliang Meng and Zenghuang Fu and Yiheng Li and Qi Zeng and Yifan Zhang and Ju Xin and Rongtao Xu and Jiguang Zhang and Xiaopeng Zhang},
      year={2025},
      eprint={2511.10134},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2511.10134}, 
}
```
