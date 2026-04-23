---
title: "Video Evidence to Reasoning: Efficient Video Understanding via Explicit Evidence Grounding"
authors:
  - Yanxiang Huang
  - Guohua Gao
  - Zhaoyang Wei
  - Jianyuan Ni
arxiv_id: "2601.07761"
arxiv_url: https://arxiv.org/abs/2601.07761
pdf_url: https://arxiv.org/pdf/2601.07761.pdf
published: 2026-01-12
updated: 2026-02-19
categories:
  - cs.CV
tags:
  - paper/arxiv
  - video-understanding
  - video-vqa
  - status/read
status: read
code: ""
datasets:
  - Video-MME
  - MVBench
  - VSI-Bench
  - VidHal
  - EventHall
  - CoE-Instruct
pipeline_figure: assets/pipeline_2601.07761.png
pipeline_caption: The framework of CoE, where the EGM first extracts compact visual evidence based on the query, enabling the LLM to perform efficient and grounded reasoning.
pipeline_source: "TeX includegraphics from icme2025_template_anonymized.tex (label: fig:framework)"
cssclass: academia
---

## TL;DR
- 提出 CoE（Chain of Evidence），把视频理解拆成“先证据、后推理”，缓解长视频推理中的高成本与幻觉问题。
- 核心模块 EGM（Evidence Grounding Module）用 query-guided cross-attention 从长视频帧中压缩出少量高价值证据。
- 推理阶段强制输出 `Temporal Anchors -> Reasoning Draft -> Answer`，让结论可回溯到时间证据。
- 训练采用 SFT + RL，RL 奖励同时约束答案正确性和“草稿是否引用预测锚点”。
- 在 Video-MME、MVBench、VSI-Bench、VidHal、EventHall 上报告显著提升，CoE-8B(RL) 为论文最优版本。

## Key Contributions
- 提出显式证据链框架 CoE，架构上解耦感知与推理，并联合优化。
- 设计轻量 EGM，在视觉编码器与 LLM 之间做证据过滤，降低推理 token/时延负担。
- 设计 Evidence-Anchoring Protocol，把黑盒 CoT 变为可解释白盒流程。
- 构建 CoE-Instruct（164k）双标注数据（关键帧监督 + 推理监督），并配合证据反馈 RL。

## Method
Pipeline:
1. 视频编码得到帧特征 `V = {v1...vN}`。
2. EGM 用问题特征生成 `K` 个 evidence queries，对 `V` 做 cross-attention，得到压缩证据 `Eg`。
3. LLM 按协议生成：`Temporal Anchors`、`Reasoning Draft`、`Answer`。
4. 训练损失：`L_CoE = L_grounding + lambda * L_reasoning`。
5. RL 奖励融合锚点 F1、草稿-锚点时间 IoU、答案正确性，使用 GRPO 优化。

Compact pseudocode:
```text
V = ViT(video)
Eg, A = EGM(V, Q)
Y = LLM([Anchors, Draft, Answer] | Eg, Q)
L = BCE(pool(A), key_frame_labels) + lambda * NLL(Y)
RL reward = w_g*F1(anchors) + w_p*IoU(draft_timestamps, anchors) + w_a*Acc(answer)
```

## Pipeline Figure
![[assets/pipeline_2601.07761.png]]

Caption: The framework of CoE, where the EGM first extracts compact visual evidence based on the query, enabling the LLM to perform efficient and grounded reasoning.

Source: TeX includegraphics from `icme2025_template_anonymized.tex` (label: `fig:framework`).

## Experiments
### Datasets table
| Dataset      | Task        | Split        | Metric(s) | Notes                                          |
| ------------ | ----------- | ------------ | --------- | ---------------------------------------------- |
| Video-MME    | 通用/长上下文视频理解 | not reported | Accuracy  | 按短/中/长视频报告                                     |
| MVBench      | 多维视频理解      | not reported | Accuracy  | 与多开源/闭源模型对比                                    |
| VSI-Bench    | 视频推理（强调证据链） | not reported | Accuracy  | 论文重点评测之一                                       |
| VidHal       | 视频幻觉评估      | not reported | Accuracy  | 评估幻觉抑制能力                                       |
| EventHall    | 事件级幻觉评估     | not reported | Accuracy  | 评估事实一致性                                        |
| CoE-Instruct | 训练数据        | 164k samples | n/a       | 含 Key_Frame_Indices + Reasoning_Draft + Answer |

### Main results table(s)
| Dataset | Metric | Baseline | Ours | Δ |
|---|---|---:|---:|---:|
| Video-MME | Accuracy | InternVL3-8B: 66.5 | CoE-8B(RL): 76.3 | +9.8 |
| MVBench | Accuracy | InternVL3-8B: 74.4 | CoE-8B(RL): 91.2 | +16.8 |
| VSI-Bench | Accuracy | InternVL3-8B: 41.0 | CoE-8B(RL): 52.1 | +11.1 |
| VidHal | Accuracy | InternVL3-8B: 80.9 | CoE-8B(RL): 81.3 | +0.4 |
| EventHall | Accuracy | InternVL3-8B: 72.1 | CoE-8B(RL): 79.2 | +7.1 |


| Dataset | Metric | Baseline | Ours | Δ |
|---|---|---:|---:|---:|
| VSI-Bench | Accuracy | InternVL2.5-4B Original: 31.8 | RL with CoE: 37.8 | +6.0 |
| Video-MME | Accuracy | InternVL2.5-4B Original: 54.9 | RL with CoE: 60.7 | +5.8 |
| MVBench | Accuracy | InternVL2.5-4B Original: 70.8 | RL with CoE: 76.5 | +5.7 |
| VidHal | Accuracy | InternVL2.5-4B Original: 74.0 | RL with CoE: 80.2 | +6.2 |
| EventHall | Accuracy | InternVL2.5-4B Original: 62.5 | RL with CoE: 72.2 | +9.7 |

### Training / Compute
| Item | Value |
|---|---|
| Backbones | InternVL2.5-4B, InternVL3-8B |
| 4B tuning | full fine-tuning on LLM + projection modules |
| 8B tuning | LoRA-based fine-tuning |
| Training objective | `L_grounding + lambda * L_reasoning` + GRPO RL |
| CoE-Instruct size | 164k samples |
| Key hyperparameters | `K` (evidence pieces), `lambda` (loss balance), reward weights `w_g,w_p,w_a` |
| Hardware / batch / lr / epochs | not reported |

### Ablations/Analysis tables
| Ablation           | Setting                  | VSI-Bench | VideoMME |  MVBench |   VidHal | EventHall |
| ------------------ | ------------------------ | --------: | -------: | -------: | -------: | --------: |
| Reasoning variants | Original                 |      31.8 |     54.9 |     70.8 |     74.0 |      62.5 |
| Reasoning variants | Original + CoT Prompting |      33.5 |     54.7 |     71.5 |     77.0 |      67.4 |
| Reasoning variants | SFT with QA only         |      31.8 |     54.5 |     73.4 |     64.1 |      57.7 |
| Reasoning variants | SFT with CoT             |      34.3 |     58.6 |     73.7 |     77.9 |      53.1 |
| Reasoning variants | SFT with CoE             |      36.3 |     59.5 |     75.4 |     78.9 |      71.2 |
| Reasoning variants | RL with CoE              |  **37.8** | **60.7** | **76.5** | **80.2** |  **72.2** |



| Ablation | Setting | Short | Medium | Long | Avg |
|---|---|---:|---:|---:|---:|
| Video-MME length | InternVL3-8B Original + CoT | 75.3 | 65.3 | 59.0 | 66.6 |
| Video-MME length | InternVL3-8B SFT w/ CoE | **86.9** | **71.4** | **68.4** | **72.3** |

## Limitations & Caveats
- 训练细节不完整，缺少 batch size、lr、epoch、GPU 数量等复现关键配置。
- 论文强调效率，但主结果表未系统给出 token 成本/延迟的完整对照。
- CoE 强依赖关键帧监督质量，标注噪声可能把推理链带偏。
- 主要在 InternVL 系列验证，跨架构泛化仍需补充。

## Concrete Implementation Ideas
- 在 InternVL/LLaVA-NeXT 视频管线中先加轻量 EGM adapter（1-2 层 cross-attn），优先验证长视频场景。
- 先做“协议最小改动”实验：不改模型，仅强制 `anchors->draft->answer` 输出并做一致性检查。
- 构建小规模 CoE-style 数据子集（关键帧 + 草稿）做 SFT 对照 `CoT` vs `CoE`。
- 在 RL 阶段增加“锚点-答案一致性”惩罚，专门压制答对但证据错误的样本。

## Open Questions / Follow-ups
- CoE-Instruct 是否完全公开？标注流程与质检标准是否可复现？
- EGM 的 `K` 对精度/效率 trade-off 的最优区间在不同 benchmark 是否一致？
- 在无关键帧标注的弱监督场景下，CoE 还能否稳定提升？
- 是否能把证据锚点扩展到对象级/动作级 grounding，而非仅时间区间？

## Citation
```bibtex
@misc{huang2026videoevidencereasoningefficient,
      title={Video Evidence to Reasoning Efficient Video Understanding via Explicit Evidence Grounding},
      author={Yanxiang Huang and Guohua Gao and Zhaoyang Wei and Jianyuan Ni},
      year={2026},
      eprint={2601.07761},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2601.07761},
}
```
