---
title: "Logic-in-Frames: Dynamic Keyframe Search via Visual Semantic-Logical Verification for Long Video Understanding"
authors:
  - Weiyu Guo
  - Ziyang Chen
  - Shaoguang Wang
  - Jianxiang He
  - Yijie Xu
  - Jinhui Ye
  - Ying Sun
  - Hui Xiong
conference: NIPS 2025
year: 2025
arxiv_url: https://arxiv.org/abs/2503.13139
pdf_link: "[[assets/paper_2503.13139.pdf]]"
cover: "[[assets/pipeline_2503.13139.png]]"
updated: 2026-05-20
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
  - benchmark
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- 论文提出 **Visual Semantic-Logical Search (VSLS)**，把 long video QA 的 keyframe selection 重新表述为 query-aware 的视觉语义逻辑搜索问题。
- VSLS 从问题和选项中解析 key objects、cue objects 与四类关系：spatial co-occurrence、temporal proximity、attribute dependency、causal order，再用这些关系动态更新 frame sampling distribution。
- 方法是 training-free / plug-and-play：用 LLM/VLM 做 query grounding，用 YOLO-World 做 object detection，用 relation verification 与 spline-based distribution update 找到 top-K keyframes。
- 在 LV-Haystack / Haystack-Ego4D 风格的 keyframe search 评测中，VSLS 只采样约 **1.4%** frames，却提升 semantic similarity、temporal coverage 与 downstream QA accuracy。
- 主要收益集中在 long-video 场景：例如 LongVideoBench 上 GPT-4o 8-frame long split 从 47.1 提升到 **51.2**，InternVL 2.5-78B 8-frame long split 从 55.7 提升到 **58.0**。

## Key Contributions

1. 定义并系统使用四类 visual semantic-logical relations：spatial、temporal/time、attribute、causal，用于补齐 text query 与 video frames 之间的逻辑缺口。
2. 提出一个 training-free keyframe search framework：从 query 解析对象与关系，稀疏采样视频帧，检测对象，验证关系，更新 sampling distribution，最终选出 top-K keyframes。
3. 在 search utility 指标上验证 VSLS：在 LVB 32-frame 设置下达到 Precision **74.5**、Recall **92.5**、Temporal Coverage **41.4**。
4. 在 downstream video QA 上验证 plug-and-play 性：VSLS 可接入 GPT-4o 与 InternVL 2.5-78B 等 VLM pipeline，在 LongVideoBench 与 VideoMME 多个长度 split 上带来增益。
5. 给出 query grounding prompt、QA prompt、system specifications 与 limitation discussion，有利于复现核心 pipeline。

## Method

VSLS 的核心假设是：回答长视频问题所需的关键帧，不只由“有没有目标物体”决定，也由 query 中隐含的视觉逻辑关系决定。方法把问题 $Q$ 解析为对象集合 $\mathcal{O}$ 与关系集合 $\mathcal{R}$，其中关系可写作三元组 $r=(o_i,\delta,o_j)$，$\delta$ 属于 spatial、temporal/time、attribute、causal。

紧凑流程如下：

```text
Input: video V, query Q, top-K target, search budget and relation parameters
1. ParseQuestion(Q) -> key objects, cue objects, relation triplets
2. Initialize a uniform frame sampling distribution P
3. Repeat until budget is exhausted or key objects are found:
   a. sample k^2 frames from P and arrange them into a grid
   b. run YOLO-World to detect key/cue objects
   c. compute base object confidence per sampled frame
   d. verify spatial / temporal / attribute / causal relations
   e. add relation-specific confidence bonuses
   f. diffuse high frame scores to temporal neighbors
   g. normalize scores into the next sampling distribution
4. Return top-K frames by final confidence
```

关键 score 设计来自论文公式：

- Object detection base score:
  $C_t = \max_{o \in \Omega_t}(c_o \cdot w_o)$
- Relation verification bonus:
  $C_t^{(r)} = C_t + \alpha \cdot \gamma_{r_{\text{type}}}$
- Temporal diffusion:
  $S_{f \pm \delta} \leftarrow \max(S_{f \pm \delta}, \frac{S_f}{1 + |\delta|})$

论文报告的实验设置中，attribute overlap threshold $\tau=0.5$，temporal threshold $\Delta_t=5$ frames，超参数搜索后采用 $\alpha=0.3$ 与 $\gamma_{r_{\text{type}}}=0.5$。

四类关系的含义如下：

| Relation | Meaning | Example |
| --- | --- | --- |
| Spatial Co-occurrence | 两个对象出现在同一帧，表示共现或空间邻近 | `(person, spatial, vase)` |
| Attribute Dependency | 对象与属性共享视觉区域或属性约束 | `(person, attribute, black shirt)` |
| Temporal Proximity | 两个对象在相近时间帧出现，连接事件序列 | `(dog, temporal, cat)` |
| Causal Order | 一个对象/事件在另一个之前出现，表示因果或先决顺序 | `(little girl, causal, pieces)` |

## Pipeline Figure

![[assets/pipeline_2503.13139.png]]

Caption: Our VSLS Framework for Efficient Keyframe Selection. VSLS sparsely samples frames and selects key ones via object detection and logic verification. Steps: 1) use LLM & VLM to extract cue/target objects and four logic types; 2) adaptive sampling with evolving confidence; 3) detect objects via YOLO-World; 4) fuse scores with a spline function to identify high-confidence frames for downstream tasks.

Source: TeX includegraphics from `sec/Method.tex`, original asset `image/Pipeline14.pdf`, rendered with `pdftoppm -cropbox`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| LongVideoBench (LVB) | long video QA | Short / Medium / Long video length groups | QA accuracy | 用于评估下游 video QA performance |
| VideoMME | multimodal video QA | Short / Medium / Long duration groups | QA accuracy | 视频长度从短片到 1 hour，论文按 duration split 报告 |
| Haystack-LVBench (HLVB) | keyframe selection | human-annotated frame index answers | Precision, Recall, Temporal Coverage | 基于 LVB 扩展，提供 keyframe annotations |
| Haystack-Ego4D / Ego4D | keyframe selection / egocentric long video | long egocentric videos | Precision, Recall, Temporal Coverage | 用于评估 long video temporal search accuracy |

### Search Efficiency on LV-Haystack

| Group | Method | Training Required | Matching | Iteration | TFLOPs ↓ | Search Latency (sec) ↓ | Overall Latency (sec) ↓ | Acc ↑ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Static Frame Sampling | Uniform-8 | Training-Based | N/A | N/A | N/A | 0.2 | 3.8 | 53.7 |
| Dense Retrieval | VideoAgent | Training-Based | CLIP-1B | 840 | 536.5 | 30.2 | 34.9 | 49.2 |
| Dense Retrieval | T*-Retrieval | Training-Based | YOLO-World-110M | 840 | 216.1 | 28.6 | 32.2 | 57.3 |
| Temporal Search | T*-Attention | Training-Based | N/A | N/A | 88.9 | 13.7 | 17.3 | 59.3 |
| Temporal Search | T*-Detector | **Training-Free** | YOLO-World-110M | 43 | 31.7 | 7.3 | 11.1 | 59.8 |
| Temporal Search | **VSLS-Detector (ours)** | **Training-Free** | YOLO-World-110M | 49 | 33.3 | 7.8 | 11.6 | **61.5** |

作者的解读是：VSLS 比 T*-Detector 多引入 relation verification，iteration 从 43 增加到 49，搜索延迟从 7.3s 到 7.8s，但 accuracy 从 59.8 提升到 **61.5**，因此更像是“少量额外搜索换更强 query alignment”。

### Search Utility on LVB

表中保留论文的标注：8-frame setting 的最佳值用 underline，32-frame setting 的最佳值用 bold。

| Group | Method | Frame | Precision ↑ | Recall ↑ | Time / TC ↑ |
| --- | --- | --- | --- | --- | --- |
| Static Frame Sampling | Uniform (reported) | 8 | 56.0 | 72.0 | 6.3 |
| Static Frame Sampling | Uniform | 8 | 60.7 | 80.4 | 4.7 |
| Static Frame Sampling | Uniform (reported) | 32 | 58.7 | 81.6 | 24.9 |
| Static Frame Sampling | Uniform | 32 | 60.2 | 85.0 | 8.1 |
| Dense Retrieval | VideoAgent (reported) | 10.1 | 58.8 | 73.2 | 8.5 |
| Dense Retrieval | Retrieval-based (reported) | 8 | 63.1 | 65.5 | 6.3 |
| Dense Retrieval | Retrieval-based (reported) | 32 | 59.9 | 80.8 | 21.8 |
| Temporal Searching | T* (reported) | 8 | 58.4 | 72.7 | 7.1 |
| Temporal Searching | T* | 8 | 75.3 | 88.2 | 26.2 |
| Temporal Searching | **VSLS (ours)** | 8 | <u>75.6</u> | <u>88.6</u> | <u>26.3</u> |
| Temporal Searching | T* (reported) | 32 | 58.3 | 83.2 | 28.2 |
| Temporal Searching | T* | 32 | 74.0 | 90.3 | 36.5 |
| Temporal Searching | **VSLS (ours)** | 32 | **74.5** | **92.5** | **41.4** |

这里的核心结果是：VSLS 不只是提高视觉相似性 Precision/Recall，也明显提高 Temporal Coverage，说明 query-guided relations 帮助模型覆盖更接近人工标注的时间位置。

### Downstream Video QA

| Benchmark | Model / Setting | Frame | Long | Medium | Short |
| --- | --- | --- | --- | --- | --- |
| LVB | GPT-4o | 8 | 47.1 | 49.4 | 67.3 |
| LVB | GPT-4o + T* | 8 | 49.1 | 56.2 | 68.0 |
| LVB | **GPT-4o + VSLS (ours)** | 8 | **51.2** | **58.9** | **74.0** |
| LVB | InternVL 2.5-78B | 8 | 55.7 | 57.3 | 74.0 |
| LVB | **InternVL 2.5-78B + VSLS (ours)** | 8 | **58.0** | **61.5** | **74.0** |
| LVB | GPT-4o | 32 | 53.8 | 56.5 | 74.0 |
| LVB | GPT-4o + T* | 32 | 55.3 | 58.8 | 72.0 |
| LVB | **GPT-4o + VSLS (ours)** | 32 | **54.2** | **60.0** | **76.0** |
| VideoMME | GPT-4o | 8 | 55.2 | 60.2 | **69.6** |
| VideoMME | GPT-4o + T* | 8 | 55.2 | **61.2** | 68.9 |
| VideoMME | **GPT-4o + VSLS (ours)** | 8 | **56.9** | 60.7 | 68.2 |
| VideoMME | InternVL 2.5-78B | 8 | 52.6 | 55.5 | 55.9 |
| VideoMME | **InternVL 2.5-78B + VSLS (ours)** | 8 | **57.7** | **57.5** | **59.0** |
| VideoMME | GPT-4o | 32 | 55.2 | 61.0 | 71.4 |
| VideoMME | GPT-4o + T* | 32 | 55.2 | 61.6 | **72.6** |
| VideoMME | **GPT-4o + VSLS (ours)** | 32 | **55.2** | **61.9** | 71.9 |

论文还引用了一组灰色 SOTA 结果作为透明比较，但设置不同且不保证可复现，因此上表优先保留作者自己 replication 的黑色结果。

### Ablations / Analysis

| Logic Type | Method | LVB Precision ↑ | LVB Recall ↑ | LVB TC ↑ |
| --- | --- | --- | --- | --- |
| Spatial | T* | 72.9 | 88.7 | 37.5 |
| Spatial | **VSLS (ours)** | **73.6** | **91.4** | **45.5** |
| Attribute | T* | 71.8 | 87.6 | 38.5 |
| Attribute | **VSLS (ours)** | **72.7** | **90.9** | **42.1** |
| Time | T* | 76.7 | 89.2 | **37.3** |
| Time | **VSLS (ours)** | **77.5** | **92.5** | 36.1 |
| Causal | T* | 74.7 | 92.4 | 38.6 |
| Causal | **VSLS (ours)** | 74.7 | **93.8** | **39.6** |

关系类型分析显示，VSLS 在 spatial、attribute、causal 上提升 TC，time relation 的 TC 略低于 T*。作者认为这可能与 dataset 中 time relation samples 较少有关，但 Precision/Recall 仍有提升。

### Training / Compute

| Item | Value |
| --- | --- |
| Training | Training-free keyframe search; no end-to-end model training reported for VSLS |
| Query grounding | LLM/VLM parse key objects, cue objects, and relation triplets |
| Object detector | YOLO-World-110M in main efficiency comparison |
| QA models | GPT-4o, InternVL 2.5-78B, plus cited SOTA models |
| Hyperparameters | $\tau=0.5$, $\Delta_t=5$ frames, $\alpha=0.3$, $\gamma_{r_{\text{type}}}=0.5$ |
| Search budget | Stops when targets are found or iteration budget is exhausted; paper mentions cap $\min(1000,\ 0.1 \times V_t)$ |
| Hardware | Intel Xeon Platinum 8378A / 8358P CPU, 1TB RAM, 4/6 NVIDIA A800 80GB |
| Software | Python 3.11, PyTorch 2.4, NCCL 2.21.5 |
| Code | Paper states code will be publicly available, but no repository URL is listed in the source / arXiv page |

## Limitations & Caveats

- VSLS 仍有搜索开销：虽然只采样约 1.4% frames，但论文报告约 7.8s search overhead，对 real-time / low-latency 应用可能偏高。
- 方法依赖 YOLO-World 这类 object detector；在 poor lighting、occlusion、unusual camera angles 等视觉条件下，检测错误会直接影响 relation verification 与 temporal coverage。
- 四类关系具有较强启发式意义，但不是完整的视觉逻辑体系；论文也把 more logical relations、learnable search methods、interpretability 作为未来方向。
- Downstream QA 增益并非每个 split 都单调领先：例如 VideoMME short split 上 GPT-4o + VSLS 低于 GPT-4o baseline / T*，需要结合视频长度与任务类型分析。
- 论文说 code will be publicly available，但当前材料没有可用代码链接，复现需要等待实现或自行重建 pipeline。

## Concrete Implementation Ideas

1. 在现有 long-video QA pipeline 前加一个 VSLS-style retriever：先用 prompt 提取 key/cue objects 与 relations，再只把 top-K frames 传给 GPT-4o / Gemini / InternVL。
2. 把 relation verification 做成可替换模块：spatial 用 box co-occurrence，attribute 用 box overlap + CLIP attribute score，temporal/causal 用 ordered detections + timestamp constraints。
3. 为每个 query 保存 search trace：sampled frame ids、object scores、relation bonuses、distribution updates，这会让 long-video answer 更可解释。
4. 在 domain-specific videos 上重新调 $\Delta_t$、$\tau$、$\alpha$、$\gamma$；例如 surveillance / sports / lecture videos 的 temporal granularity 很可能不同。
5. 将 VSLS 与 caption retrieval 混合：object-relation search 找关键帧，dense caption retrieval 找补充证据，最后统一交给 VLM 做 QA。

## Open Questions / Follow-ups

- 四类 relation 是否足以覆盖更复杂的 instructional videos、multi-agent interactions 或 movie plots？
- Relation extraction 当前依赖 LLM/VLM prompt，错误解析会怎样影响后续 search？是否需要 self-check 或 structured parser？
- VSLS 的 sampling distribution update 是否能学习化，比如用 reinforcement learning 或 differentiable search policy 替代 heuristic update？
- 对 VideoMME short split 这类较短视频，relation-guided search 可能会过度筛选吗？是否需要根据视频长度切换策略？
- 如果 object detector 找不到 query 中的抽象目标，是否应回退到 caption-level retrieval 或 dense VLM embedding retrieval？

## Citation

```bibtex
@misc{guo2025logicinframes,
  title={Logic-in-Frames: Dynamic Keyframe Search via Visual Semantic-Logical Verification for Long Video Understanding},
  author={Guo, Weiyu and Chen, Ziyang and Wang, Shaoguang and He, Jianxiang and Xu, Yijie and Ye, Jinhui and Sun, Ying and Xiong, Hui},
  year={2025},
  eprint={2503.13139},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2503.13139}
}
```
