---
title: "VideoTree: Adaptive Tree-based Video Representation for LLM Reasoning on Long Videos"
authors:
  - Ziyang Wang
  - Shoubin Yu
  - Elias Stengel-Eskin
  - Jaehong Yoon
  - Feng Cheng
  - Gedas Bertasius
  - Mohit Bansal
conference: CVPR 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2405.19209
pdf_link: "[[assets/paper_2405.19209.pdf]]"
cover: "[[assets/pipeline_2405.19209.png]]"
updated: 2026-04-27
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: unread
priority: "1"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/Ziyang412/VideoTree
---

## TL;DR

- VideoTree 是一个 training-free 的 long-form video QA 框架，用 query-adaptive 的树结构替代固定抽帧或密集 caption。
- 核心想法是先用 Adaptive Breadth Expansion 找到 query-relevant keyframes，再对高相关区域做 Relevance-guided Depth Expansion，形成 coarse-to-fine 的 VideoTree。
- 推理前只 caption 被树结构选中的 keyframes 或 clips，并按时间顺序整理成文本描述交给 LLM reasoner。
- 在 EgoSchema full test 和 NExT-QA 上分别达到 **61.1%** 和 **75.6%** accuracy，优于同类 training-free 方法。
- 在 Video-MME long split 上达到 **54.2%**，比 LLoVi 高 5.4%，也略高于 GPT-4V 的 53.5%，但仍低于 GPT-4o 与 Gemini 1.5 Pro。
- 主要限制是依赖 captioner 识别被采样帧的能力，并且仍有少量 hyperparameters 需要选择。

## Key Contributions

1. 提出 query-adaptive hierarchical video representation，把长视频组织成与问题相关的树结构，而不是线性 frame caption list。
2. Adaptive Breadth Expansion 通过 visual clustering、cluster captioning、LLM relevance scoring 的循环，自适应决定第一层需要多少 keyframes。
3. Relevance-guided Depth Expansion 根据 cluster relevance 分数只在中高相关区域继续细化，避免 irrelevant details 淹没 LLM。
4. 在 EgoSchema、NExT-QA、Video-MME、IntentQA 等长视频 QA 场景中展示了 accuracy 与 inference efficiency 的共同提升。

## Method

VideoTree 的输入是视频 $V=(F_1,F_2,\dots,F_n)$ 与 query $Q$，输出是用于 LLM reasoning 的 query-relevant caption sequence。

1. **Visual Clustering**: 用预训练 visual encoder $E$ 提取每帧特征 $f_i=E(F_i)$，再做 K-Means：

$$
(C_1,\dots,C_k),(c_1,\dots,c_k)=\operatorname{KMeans}((f_1,\dots,f_n),k)
$$

2. **Cluster Captioning**: 对每个 cluster 取最接近 centroid 的 keyframe 或 key clip，用 VLM captioner 得到 caption $t_i=Cap(F_i)$。
3. **Relevance Scoring**: 把 captions 和 query 交给 LLM，输出每个 cluster 的 relevance score $r_i \in \{1,2,3\}$，其中 3 表示 highly relevant。
4. **Adaptive Breadth Expansion**: 如果 highly relevant clusters 数量低于 $rele\_num\_thresh$，就把 cluster 数 $k$ 翻倍并重复上述过程，直到满足阈值或达到 $max\_breadth$。
5. **Relevance-guided Depth Expansion**: 对 somewhat relevant cluster 继续 re-cluster 成 branch width 为 $w$ 的子节点；对 highly relevant cluster 构造两层更细粒度树；低相关区域不继续展开。
6. **LLM Video Reasoning**: 遍历树节点，caption 选中的 keyframes 或 clips，按 temporal order 重排，拼成 text video description，再连同 query 输入 LLM 得到答案。

紧凑版 pseudocode：

```text
Initialize k and an empty VideoTree
repeat:
  clusters = KMeans(E(sampled_frames), k)
  captions = Caption(cluster_centroids)
  relevance = LLMScore(captions, query)
  if count(relevance == 3) < rele_num_thresh:
    k = 2 * k
until enough highly relevant clusters or k reaches max_breadth

for each first-level cluster:
  if relevance == 2: add one finer level with branch width w
  if relevance == 3: add two finer levels with branch width w

selected = traverse(VideoTree)
description = Caption(selected keyframes/clips) sorted by time
answer = LLM(description, query, options)
```

## Pipeline Figure

![[assets/pipeline_2405.19209.png]]

Caption: A detailed view of VideoTree. To construct the tree structure, the method begins with Adaptive Breadth Expansion, dynamically extracting query-relevant key information from video and question inputs. It then performs Relevance-guided Depth Expansion from highly relevant root nodes, re-clustering at each level to capture finer visual cues. Finally, selected keyframes are captioned, temporally ordered, and used for LLM reasoning.

Source: TeX includegraphics from `sec/3_method.tex`, rendered from `figures/pipeline_iclr_v1.pdf` using PDF crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| EgoSchema | Long-range multiple-choice video QA | Full test; official validation subset with 500 questions for ablations | Accuracy | 5K QA pairs over 250 hours of egocentric video; average video length around 180s in the subset |
| NExT-QA | Causal, temporal, descriptive video QA | Validation/test reporting by question type | Accuracy | 5,440 videos, about 52K questions, average video length 44s |
| Video-MME | Long-video multimodal QA | Long split | Accuracy | Average video length 44 minutes, range 30 to 60 minutes |
| IntentQA | Intent-oriented multiple-choice video QA | Test set, zero-shot | Accuracy | 4,303 videos and 16K QA pairs; test set has 2K questions |
| MLVU | Long video understanding benchmark | Avg. score reported in supplement | Accuracy / benchmark average | Additional result with LLaVA-OV-7B captioner |

### Main Results

EgoSchema 与 NExT-QA 主表如下，保留论文中对 VideoTree 的加粗标记。LangRepo 与 LVNet 的部分结果在原文中以 light gray 弱化，因为评测设置不同或使用更强 GPT-4o MLLM。

| Method | Model / Setting | EgoSchema Sub. | EgoSchema Full | NExT-QA Tem. | NExT-QA Cau. | NExT-QA Des. | NExT-QA Avg. |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| *Based on Open-source Captioners and LLMs* |  |  |  |  |  |  |  |
| MVU | Mistral-13B | 60.3 | 37.6 | 55.4 | 48.1 | 64.1 | 55.2 |
| LangRepo | Mixtral-8x7B | 66.2 | 41.2 | 51.4 | 64.4 | 69.1 | 60.9 |
| Video-LLaVA+INTP | Vicuna-7B v1.5 | - | 38.6 | 58.6 | 61.9 | 72.2 | 62.7 |
| *Based on Proprietary MLLMs* |  |  |  |  |  |  |  |
| IG-VLM | GPT-4V | 59.8 | - | 63.6 | 69.8 | 74.7 | 68.6 |
| LVNet | GPT-4o | 68.2 | 61.1 | 65.5 | 75.0 | 81.5 | 72.9 |
| *Based on Open-source Captioners and Proprietary LLMs* |  |  |  |  |  |  |  |
| ProViQ | GPT-3.5 | 57.1 | - | - | - | - | 64.6 |
| LLoVi | GPT-3.5 | 57.6 | 50.3 | - | - | - | - |
| MoReVQA | PaLM-2 | - | 51.7 | 64.6 | 70.2 | - | 69.2 |
| Vamos | GPT-4 | 51.2 | 48.3 | - | - | - | - |
| LLoVi | GPT-4 | 61.2 | - | 61.0 | 69.5 | 75.6 | 67.7 |
| VideoAgent | GPT-4 | 60.2 | 54.1 | 64.5 | 72.7 | 81.1 | 71.3 |
| VideoAgent | GPT-4 with video-specific models | 62.8 | 60.2 | - | - | - | - |
| LifelongMemory | GPT-4 | 64.1 | 58.6 | - | - | - | - |
| **VideoTree (Ours)** | GPT-4 | **66.2** | **61.1** | **70.6** | **76.5** | **83.9** | **75.6** |

Video-MME long split 结果：

| Method | Model Group | Acc. |
| --- | --- | ---: |
| *Proprietary MLLM* |  |  |
| GPT-4V | Proprietary MLLM | 53.5 |
| GPT-4o | Proprietary MLLM | 65.3 |
| Gemini 1.5 Pro | Proprietary MLLM | **67.4** |
| *Open-Source MLLM* |  |  |
| LongVA | Open-Source MLLM | 46.2 |
| VITA | Open-Source MLLM | 48.6 |
| InternVL2-34B | Open-Source MLLM | 52.6 |
| VILA-1.5-40B | Open-Source MLLM | 53.8 |
| Oryx-1.5-34B | Open-Source MLLM | 59.3 |
| LLaVA-NeXT-Video-72B | Open-Source MLLM | 61.5 |
| Qwen2-VL-72B | Open-Source MLLM | **62.2** |
| *Training-free Approach* |  |  |
| LLoVi | Training-free | 48.8 |
| **VideoTree (Ours)** | Training-free | **54.2** |

Additional quantitative results:

| Method | Benchmark / Setting | Metric |
| --- | --- | ---: |
| VideoTree | IntentQA zero-shot accuracy | 66.9 |
| VideoTree | Video-MME Short | **67.8** |
| VideoTree | Video-MME Medium | **59.9** |
| VideoTree | MLVU-Avg | **60.4** |

### Efficiency / Analysis

#### Efficiency-effectiveness comparison on EgoSchema subset：

| Method | Captions | Captioner (s) | Keyfr. (s) | QA (s) | Overall (s) | Acc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLoVi-fast | 16 | 2.0 | 0 | 1.9 | **3.9** | 57.8 |
| LLoVi-best | 180 | 22.4 | 0 | 2.4 | 24.8 | 61.2 |
| VideoTree-fast | **13.6** | **1.6** | 4.4 | **1.8** | 7.8 | 63.6 |
| VideoTree-best | 62.4 | 7.8 | 10.2 | 2.1 | 20.1 | **66.2** |

#### Open-source LLM reasoner setting：

| Method | LLM / Setting | # Caption | Acc. | Inf Time (s) |
| --- | --- | ---: | ---: | ---: |
| LLoVi | Mistral-7B | 180 | 50.8 | - |
| LangRepo | Mistral-7B | 180 | 60.8 | 87.2 |
| **VideoTree (Ours)** | Mistral-7B | 32 | **63.0** | **24.3** |
| LangRepo | Mistral-8x7B (12B) | 180 | 66.2 | 162.1 |
| **VideoTree (Ours)** | Mistral-8x7B (12B) | 32 | **71.0** | **50.3** |

#### Component ablation on EgoSchema subset：

| Variant / Setting | ES Acc. |
| --- | ---: |
| VideoTree | 66.2 |
| - Depth Expansion | 64.4 |
| - Adaptive Breadth Expansion | 61.2 |

#### Average LLM calls under similar caption settings：

| Method | Caption Number | Avg LLM Calls | ES Subset Acc |
| --- | ---: | ---: | ---: |
| VideoAgent | 6.4 | 10.2 | 58.4 |
| VideoAgent | 8.4 | 10.2 | 60.2 |
| VideoAgent | 11.0 | 9.0 | 57.4 |
| **VideoTree (Ours)** | 7.1 | **2.3** | **61.0** |
| **VideoTree (Ours)** | 9.7 | **2.5** | **61.6** |
| **VideoTree (Ours)** | 11.3 | **2.8** | **62.2** |

#### Hyperparameter ablations on EgoSchema subset：

| Variant / Setting | ES Acc. | #Frame | Notes |
| --- | ---: | ---: | --- |
| Branch width = 2 | 64.4 | 43.5 | smaller tree, fewer frames |
| Branch width = 3 | 65.0 | 54.6 |  |
| Branch width = 4 | **66.2** | 62.4 | best reported branch width |
| Branch width = 5 | 64.2 | 72.5 | more frames but worse accuracy |
| Max breadth = 8 | 63.0 | 26.9 |  |
| Max breadth = 16 | 64.0 | 49.0 |  |
| Max breadth = 32 | **66.2** | 62.4 | best reported max breadth |
| Max breadth = 64 | 63.2 | 94.6 | more frames but worse accuracy |
| Threshold = 2 | 63.6 | 13.9 | fewer highly relevant clusters required |
| Threshold = 3 | 64.4 | 32.2 |  |
| Threshold = 4 | **66.2** | 62.4 | best reported threshold |
| Threshold = 5 | 64.8 | 79.2 | more frames but worse accuracy |
| Uniform Baseline | 61.2 | 180 | reported baseline for these ablations |

#### Training / compute details reported by the paper：

| Item | Value |
| --- | --- |
| Training | Training-free, no additional video-specific training |
| Main LLM reasoner | GPT-4 version 1106 |
| Open-source LLM ablation | Mistral-7B and Mistral-8x7B (12B) |
| Visual encoder | EVA-CLIP-8B for main results |
| NExT-QA captioner | CogAgent |
| EgoSchema captioner | LaViLa |
| Video-MME captioner | LLaVA1.6-7B |
| Frame sampling | 1 FPS for EgoSchema and NExT-QA; 0.125 FPS for Video-MME |
| Best average # captions | EgoSchema subset 62.4; NExT-QA 12.6; Video-MME 128 |

## Limitations & Caveats

- Captioner bottleneck：VideoTree 仍然依赖 captioner 准确描述被选中的 keyframes 或 clips；论文的 failure case 指出，当 captioner 未捕获关键物体或动作时，树结构也会沿着错误信息继续展开。
- Hyperparameter sensitivity：虽然 training-free，但仍需要设置 $max\_depth$、branch width、$rele\_num\_thresh$、$max\_breadth$ 等少量参数；补充实验显示 sub-optimal 设置仍优于 uniform baseline，但最佳效果依赖合适配置。
- Reasoner strength matters：主结果使用 GPT-4，open-source LLM 实验也有效但绝对性能不同，说明强 LLM reasoning module 仍是重要前提。
- 与强 proprietary long-context MLLMs 仍有差距：Video-MME long split 上 VideoTree 高于 GPT-4V，但低于 GPT-4o 与 Gemini 1.5 Pro。
- Evaluation mostly MCQA：实验以 multiple-choice QA accuracy 为主，对开放式生成、grounded temporal localization、multi-hop evidence trace 的评估较少。

## Concrete Implementation Ideas

1. 做一个可复现的 VideoTree prototype：用 CLIP 或 DINOv2 提 frame embeddings，K-Means 建第一层，再用一个 lightweight VLM captioner 生成 cluster captions。
2. 把 relevance scoring prompt 设计成 JSON 输出：每个 cluster 返回 `{score, rationale, needed_detail}`，方便 debug 与后续 depth expansion。
3. 存储树节点时保留 `frame_idx`、`timestamp`、`cluster_id`、`parent_id`、`relevance_score`、`caption`，便于可视化与 temporal re-ordering。
4. 对业务长视频可以加 cache：frame embedding、cluster assignment、caption、LLM relevance score 都能缓存，query 改变时只重算 relevance 与后续 expansion。
5. 用 tree traversal 生成两种 prompt 版本做 ablation：一种按时间顺序线性化，一种保留层级结构缩进，比较 LLM 是否真的利用 hierarchy。

## Open Questions / Follow-ups

- VideoTree 的 tree structure 是否应该显式喂给 LLM，而不仅仅是把 selected captions 按时间排序？
- 对开放式问答或需要精确 timestamp 的任务，relevance-guided expansion 能否同时输出 evidence localization？
- 如果 captioner 是现代 video-native MLLM，而不是 image/clip captioner，是否还能保持同样的 efficiency advantage？
- Relevance scoring 使用 discrete 1/2/3 是否足够，还是 continuous score 或 uncertainty-aware expansion 更稳？
- 对信息密度极高的视频，depth expansion 是否会错过多个并行事件，是否需要 multi-root budget allocation？

## Citation

```bibtex
@inproceedings{wang2025videotree,
  title = {VideoTree: Adaptive Tree-based Video Representation for LLM Reasoning on Long Videos},
  author = {Wang, Ziyang and Yu, Shoubin and Stengel-Eskin, Elias and Yoon, Jaehong and Cheng, Feng and Bertasius, Gedas and Bansal, Mohit},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year = {2025},
  eprint = {2405.19209},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2405.19209}
}
```

