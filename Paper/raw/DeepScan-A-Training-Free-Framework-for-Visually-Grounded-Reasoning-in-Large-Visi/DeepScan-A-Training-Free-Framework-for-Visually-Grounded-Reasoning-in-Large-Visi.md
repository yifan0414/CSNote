---
title: DeepScan
authors:
  - Yangfu Li
  - Hongjian Zhan
  - Jiawei Chen
  - Yuning Gong
  - Qi Liu
  - Yue Lu
conference: CVPR
year: 2026
arxiv_url: https://arxiv.org/abs/2603.03857
pdf_link: "[[assets/paper_2603.03857.pdf]]"
cover: "[[_assets/images/pipeline_2603.03857.png]]"
updated: 2026-05-19
tags:
  - paper/arxiv
  - vlm
  - image-text
  - question-aware
status: unread
priority:
rating:
topics:
  - MLLM
code: https://github.com/YChenL/DeepScan
---

## TL;DR

- DeepScan 是一个 training-free 的 visually grounded reasoning 框架，用在 LVLM 回答前显式完成证据定位、视野校准和多粒度证据整合。
- 核心思想是把传统 top-down / one-shot evidence localization 改成 bottom-up：先在局部 patch 中找 cue，再回到整图尺度恢复 evidence。
- 方法由三段组成：Hierarchical Scanning、Refocusing、Evidence-Enhanced Reasoning；外部专家使用 BLIP-ITM base 作为 search expert，LangSAM 作为 visual expert。
- 在 Qwen2.5-VL-7B 上，DeepScan 在 V* Overall 达到 90.6%，相对原模型表中提升 +16；在 TreeBench Overall 达到 42.5%，相对 Qwen2.5-VL-7B 提升 +5.5。
- 代价是推理延迟更高；作者把它定位为 test-time scaling，并通过 top-$k$ smallest evidence candidates、patch size 和 Refocusing 搜索空间来控制性能-效率权衡。

## Key Contributions

1. 提出 **DeepScan**：一个不需要训练或适配 LVLM 参数的 visual grounding wrapper，先定位证据再回答，从而提高可解释性和准确率。
2. 提出 **Hierarchical Scanning**：用局部 cue exploration 和整图 multi-scale evidence extraction 形成 bottom-up localization，降低 noisy context、attention sink 和 attention drift 的影响。
3. 提出 **Refocusing**：在初始 evidence view 周围做轻量搜索，通过 LVLM 判断完整性，并用 visual expert 的 Zoom-In / Zoom-Out 操作选择上下文最合适的视野。
4. 提出 **Evidence-Enhanced Reasoning**：把细粒度 evidence crop 和 Refocusing 得到的粗粒度 view 组成 Hybrid Evidence Memory，让 LVLM 同时看属性细节和关系上下文。
5. 通过 V* Bench、HR-Bench、TreeBench，以及多种 LVLM backbone 和专家尺度消融，展示训练自由框架的泛化性。

## Method

DeepScan 接收图像 $I$ 和问题 $q$，在不更新 LVLM 参数的情况下构造一个多图证据提示。整体流程可以压缩为：

1. **Search Expert**：对 patch $p$ 和问题 $q$ 生成 attention map：

$$
S = \textsc{Search}(p, q)
$$

2. **Local Cue Exploration**：对 $S_p$ 使用 Otsu threshold 得到高响应区域 $S_p^+$，将 connected components 作为 cue。每个 cue 的 proxy point 由语义响应和几何中心性共同决定：

$$
c_p^k = \arg\max_{c \in G_p^k} \tilde S_p(c)\,\tilde d(c, \partial G_p^k)
$$

这里 $\tilde S_p(c)$ 是归一化 attention score，$\tilde d(c, \partial G_p^k)$ 是到 cue 边界距离的归一化值。这个设计融合了 Attention Peak 和 Chebyshev Center 的优势。

3. **Multi-scale Evidence Extraction**：把 patch 内 proxy lift 到整图坐标，再用 LangSAM 的 point-prompt segmentation 得到 evidence mask $m$。随后用 morphological closing 和 dilation 改善 mask：

$$
m^+ = (m \bullet \mathcal K) \oplus \mathcal S_r
$$

其中 $\mathcal K$ 是 $5\times5$ flat structuring element，$\mathcal S_r$ 是半径 $r=20$ 的 disk。候选 evidence 经过面积排序，只保留 top-$k$ smallest candidates 以降低 LVLM 判断次数；论文默认 $k=10$。

4. **Refocusing**：先将 evidence set 合并成初始 view $V_1$，再构造四个候选状态：

$$
V_2=\textsc{In}(V_1,q),\quad
V_3=\textsc{Out}(V_1,s),\quad
V_4=\textsc{In}(V_3,q)
$$

选择策略用 LVLM 判断 view 是否包含回答问题所需对象，并偏好满足条件的更小 view：

$$
R(V)=\mathbb I_{V\leadsto q}\cdot \frac{HW}{hw}
$$

5. **Evidence-Enhanced Reasoning**：把细粒度 evidence crops 和最佳 Refocused view $V^*$ 组成 Hybrid Evidence Memory，再作为 ordered multi-image prompt 交给 LVLM 生成最终答案。

Compact pseudocode：

```text
for patch p in Partition(I, selected_patch_size):
  S_p = Search(p, q)
  cues = ConnectedComponents(Otsu(S_p))
  proxy points = argmax normalized_attention * normalized_boundary_distance
  lift proxy points to image coordinates

for proxy point c:
  m = Segment(I, c)
  m_plus = Close(m, K) then Dilate(m, S_r)
  crop candidate evidence e from BBox(m_plus)
  skip duplicate / already visited evidence

E_k = top-k smallest candidate evidence crops
E = LVLM-verified evidence from E_k
V_star = best of {V1, In(V1), Out(V1), In(Out(V1))}
answer = LVLM([e_1, ..., V_star], q)
```

## Pipeline Figure

![[_assets/images/pipeline_2603.03857.png]]

Caption: 该图概括了 DeepScan 的整体架构：Hierarchical Scanning 从局部 cue 恢复视觉证据，Refocusing 调整证据周围上下文，Evidence-Enhanced Reasoning 用 Hybrid Evidence Memory 组织多粒度视图并交给 LVLM 回答。

Source: TeX includegraphics from `sec/2_background.tex`, `fig/fig3.pdf`; rendered with `pdftoppm -cropbox` to `assets/pipeline_2603.03857.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| V* Bench | Fine-grained visual understanding | 191 images; Direct Attribute 115, Spatial Relationship 76 | Multiple-choice accuracy | 平均分辨率 $2246\times1582$，目标平均面积 $<0.05\%$，强调极小目标。 |
| HR-Bench 4K / 8K | High-resolution perception | 每个版本 200 images; Single-Instance 100, Cross-Instance 100 | Multiple-choice accuracy | 使用 cyclic-permutation protocol；论文分别报告 HR-4K 和 HR-8K。 |
| TreeBench | Thinking-with-images / traceable visual evidence | 405 images | Multiple-choice accuracy, mIoU | 平均分辨率 $2152\times1615$；覆盖 localization、subtle target perception、second-order reasoning。 |

### Main Results: V* and HR-Bench

表中 `†` 表示论文自收集结果；视觉 grounding methods 都基于 Qwen2.5-VL-7B 开发，除 general LVLM rows 外可直接看作同一基础模型上的 test-time / reasoning wrapper 对比。

| Method | Model / Setting | V* Avg | V* Att | V* Spa | HR-4K Avg | HR-4K Sin | HR-4K Cro | HR-8K Avg | HR-8K Sin | HR-8K Cro |
| ---- | ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| GPT-4o-1120 | Private LVLM | 66.0 | -- | -- | 59.0 | 70.0 | 48.0 | 55.5 | 62.0 | 49.0 |
| LLaVA-OV-7B | General LVLM | 70.7 | 73.0 | 60.5 | 64.3 | 74.8 | 53.8 | 59.8 | 65.3 | 54.3 |
| LLaVA-OV-72B | General LVLM | 73.8 | 80.9 | 63.2 | 66.3 | 76.5 | 56.0 | 60.9 | 68.8 | 53.0 |
| InternVL3-8B | General LVLM | 72.3 | 73.0 | 71.1 | 70.8 | 79.3 | 62.3 | 62.0 | 64.3 | 59.8 |
| InternVL3-38B | General LVLM | 77.5 | 77.4 | 77.6 | 76.3 | 83.5 | 69.0 | 67.0 | 71.3 | 62.8 |
| InternVL3-78B | General LVLM | 76.4 | 75.7 | 77.6 | 75.5 | 84.5 | 66.5 | 67.3 | 71.8 | 62.8 |
| Qwen2.5-VL-7B | General LVLM | 74.3 | 77.4 | 69.7 | 72.1 | 88.8 | 55.5 | 68.8 | 83.5 | 54.0 |
| Qwen2.5-VL-32B | General LVLM | 85.9 | 83.5 | 89.5 | 74.8 | 89.3 | 60.3 | 71.6 | 86.5 | 56.8 |
| Qwen2.5-VL-72B | General LVLM | 84.8 | 90.8 | 80.9 | 79.4 | 88.8 | 70.0 | 76.3 | 84.3 | 68.3 |
| PixelReasoner | RL-based VGR | 80.6 | 83.5 | 76.3 | 72.9 | 86.0 | 60.3 | 66.9 | 80.0 | 54.3 |
| DeepEyes | RL-based VGR | 90.0 | 92.1 | 86.8 | 75.1 | 91.3 | 59.0 | 72.6 | 86.8 | 58.5 |
| Thyme-VL | RL-based VGR | 82.2 | 83.5 | 80.3 | 77.0 | 91.0 | 63.0 | 72.0 | 86.5 | 57.5 |
| TreeVGR† | RL-based VGR | 85.9 | 86.1 | 85.5 | 72.7 | 89.5 | 61.5 | 69.8 | 84.4 | 57.2 |
| ZoomRefine† | Training-free VGR | 82.2 | 85.3 | 77.6 | 71.5 | 88.5 | 55.3 | 68.6 | 83.9 | 54.0 |
| Dyfo† | Training-free VGR | 84.3 | 82.6 | 86.8 | 71.3 | 89.2 | 53.5 | 69.8 | 86.5 | 53.2 |
| **DeepScan** | Training-free VGR | 90.6 | 93.0 | 86.8 | 75.0 | 90.1 | 59.7 | 72.4 | 87.2 | 57.6 |
| Δ vs Qwen2.5-VL-7B | Source table delta | +16 | +16 | +17 | +2.8 | +1.3 | +4.2 | +3.6 | +3.7 | +3.6 |

要点：V* 上 DeepScan 的提升最明显，符合论文主张：bottom-up grounding 对极小目标和细粒度属性尤其有效。HR-Bench 上提升较小，但在 HR-8K Single-Instance 上仍从 83.5 到 87.2。

### Main Results: TreeBench

| Method | Overall | mIoU | Attributes | Material | Phy. State | Obj. Retr. | OCR | Per. Trans. | Ordering | Con. & Oc. | Spa. Cont. | Comparison |
| ---- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ----: |
| Qwen2.5-VL-7B | 37.0 | -- | 55.2 | 53.8 | 56.5 | 62.5 | 27.9 | 20.0 | 35.1 | 39.0 | 44.8 | 43.2 |
| DeepEyes | 37.5 | 30.0 | 62.1 | 53.8 | 65.2 | 68.8 | 51.5 | 11.8 | 24.6 | 36.6 | 51.7 | 47.7 |
| Pixel-Reasoner | 39.0 | 35.7 | 58.6 | 61.5 | 65.2 | 50.0 | 48.5 | 14.1 | 31.6 | 39.0 | 44.8 | 40.9 |
| TreeVGR† | 41.0 | 31.8 | 55.2 | 61.5 | 65.2 | 50.0 | 61.7 | 15.3 | 24.6 | 46.3 | 44.8 | 40.9 |
| ZoomRefine† | 38.0 | -- | 48.3 | 61.5 | 56.5 | 62.5 | 39.7 | 18.8 | 29.8 | 46.3 | 44.8 | 38.6 |
| Dyfo† | 39.3 | -- | 58.6 | 69.2 | 56.5 | 62.5 | 35.3 | 21.2 | 35.1 | 41.5 | 44.8 | 40.9 |
| **DeepScan** | 42.5 | 37.3 | 62.1 | 69.2 | 60.9 | 68.8 | 44.1 | 21.2 | 36.8 | 43.9 | 48.3 | 43.2 |
| Δ vs Qwen2.5-VL-7B | +5.5 | -- | +6.9 | +15.4 | +4.4 | +6.3 | +16.2 | +1.2 | +1.7 | +4.9 | +3.5 | ±0.0 |

要点：TreeBench 上 DeepScan 的 Overall 和 mIoU 都强，说明 Hierarchical Scanning 确实改善了 traceable evidence localization；但 `Comparison` 上没有相对 Qwen2.5-VL-7B 的提升。

### Scaling Results on V*

补充实验显示 DeepScan 能直接迁移到更强 backbone。

| Method | Setting | Overall | Attribute | Spatial |
| ---- | ---- | ----: | ----: | ----: |
| Qwen2.5-VL-7B | baseline | 74.3 | 77.4 | 69.7 |
| **DeepScan** | Qwen2.5-VL-7B, $k=10$ | 90.6 | 93.0 | 86.8 |
| **DeepScan** | Qwen2.5-VL-7B, $k=\infty$ | 91.1 | 93.9 | 86.8 |
| Qwen2.5-VL-72B | baseline | 84.8 | 90.8 | 80.9 |
| **DeepScan-72B** | $k=10$ | 93.7 | 93.9 | 93.4 |
| **DeepScan-72B** | $k=\infty$ | 94.2 | 94.8 | 93.4 |

### Ablations / Analysis

**External experts on V***

| Expert | Variant | Overall | Attribute | Spatial | Mem | Time |
| ---- | ---- | ----: | ----: | ----: | ----: | ----: |
| BLIP-ITM | base | **90.6** | **93.0** | 86.8 | 29.4G | 24.5s |
| BLIP-ITM | large | 90.1 | 92.2 | **86.8** | 32.8G | 25.8s |
| LangSAM | small | 89.5 | **93.0** | 84.2 | 31.5G | 23.2s |
| LangSAM | base+ | 89.5 | 91.3 | **86.8** | 31.9G | 24.0s |
| LangSAM | large | **90.6** | **93.0** | **86.8** | 32.8G | 24.5s |

论文结论是专家尺度不敏感：更大的 search expert 或 visual expert 没有稳定带来收益，说明主要增益来自流程设计。

**Hierarchical Scanning on V***

| Variant / Setting | Overall | Attribute | Spatial | Time |
| ---- | ----: | ----: | ----: | ----: |
| Detection | 82.2 | 81.7 | 82.9 | 13.0s |
| Hierarchical Scanning | **90.6** | **93.0** | **86.8** | 24.5s |
| w/o Post-Processing | 87.4 | 89.6 | 85.5 | 32.1s |

Post-processing 同时提升准确率和速度：它减少 mask holes 与重复 evidence processing。

**Local Cue Exploration on V***

| Proxy | Uses semantic S | Uses topological T | Att | Spa |
| ---- | ---- | ---- | ----: | ----: |
| Centroid | no | yes | 84.3 | 80.3 |
| Chebyshev Center | no | yes | **91.3** | 82.9 |
| Attention Peak | yes | no | 87.8 | **85.5** |
| **Ours** | yes | yes | **93.0** | **86.8** |

| Patch Size | Avg | Att | Spa |
| ---- | ----: | ----: | ----: |
| 384 | 87.4 | 90.4 | 82.9 |
| 576 | 90.1 | **94.0** | 84.2 |
| 768 | 88.5 | 88.7 | **88.2** |
| 576 / 768 | **90.6** | 93.0 | 86.8 |

作者用 LVLM 先做 question / object decomposition，再为 single-object 和 multi-object 场景分别使用 $576\times576$ 与 $768\times768$ patch size。

**Refocusing on V***

| In | Out | Att | Spa |
| ---- | ---- | ----: | ----: |
| yes | no | 89.6 | 73.7 |
| no | yes | 87.8 | 72.4 |
| yes | yes | **93.0** | **86.8** |

| Search Method | State Count | Search Length | Budget |
| ---- | ----: | ----: | ----: |
| MCTS | 7 | 2.24 | 4 |
| A* | 7 | 3.07 | 4 |
| **Ours** | 4 | **1.87** | 4 |

**Grounding paradigm on V***

| Variant / Setting | Overall | Attribute | Spatial | Time |
| ---- | ----: | ----: | ----: | ----: |
| One-shot Localization | 83.8 | 83.5 | 84.2 | 20.4s |
| **Bottom-up Localization** | **90.6** | **93.0** | **86.8** | 24.5s |

这张表直接支撑论文的核心论点：不是单纯多调用专家就够了，bottom-up 证据恢复比 image-level one-shot localization 更稳。

### Training / Compute

| Item | Value |
| ---- | ---- |
| Search expert | BLIP-ITM base |
| Visual expert | LangSAM |
| LVLMs evaluated | LLaVA-1.5-7B, Qwen2-VL-7B, Qwen2.5-VL-7B / 32B / 72B |
| Candidate budget | $k=10$ in practice; $k=\infty$ reported for upper-bound style comparison |
| Patch sizes | $576\times576$ for single-object scenes; $768\times768$ for multi-object scenes |
| Local cue area threshold | $50$ pixels |
| Morphological post-processing | $5\times5$ flat structuring element $\mathcal K$; disk $\mathcal S_r$ with radius $r=20$ |
| Duplicate filtering | IoU threshold $\theta_{\rm IoU}=0.3$ |
| Refocusing padding / scale | Detection padding $28$ pixels; Zoom-Out scale $s=1.5$ |
| LVLM generation settings | temperature $t=0$, random seed $13$; beam search and top-$k$ sampling disabled |
| Max output length | 50 for decomposition / judgment / completeness; 1024 for final reasoning |
| Hardware | 4 × NVIDIA L20 GPUs |

## Limitations & Caveats

- **Latency 更高**：相比 one-shot evidence detection，DeepScan 需要 patch scanning、expert calls、LVLM evidence judgment 和 Refocusing；这是典型 test-time scaling 代价。
- **简单样本可能过度处理**：论文默认较小 patch size 来捕捉细粒度 cue，但对显著目标或简单样本会产生不必要开销。
- **Grounding failure**：当多个外观相似对象处在 evidence neighborhood 内，专家可能选错证据，LVLM 的二分类判断也会被误导。
- **Reasoning failure**：多个 evidence 相距很远时，minimal enclosing box 会把大量 inter-evidence noisy context 带入 merged view，影响空间关系推理。
- **依赖外部专家质量**：虽然不训练 LVLM，但仍继承 BLIP-ITM / LangSAM 和基础 LVLM 的偏差与失败模式；安全关键场景不能只依赖此类 wrapper。

## Concrete Implementation Ideas

1. **作为 LVLM inference wrapper 实现**：把 DeepScan 做成可插拔 pipeline，接口为 `(image, question, base_vlm) -> evidence_views, answer, traces`，便于接入不同 LVLM。
2. **缓存 expert outputs**：对 image patches 的 Search attention、LangSAM masks、BBox crops 建 cache，尤其适合同一图像多问题或离线 benchmark。
3. **轻量模型做 judge，大模型做 final reasoning**：论文分析提示 precise grounding 后感知差距缩小，可以用较小 LVLM 做 Evidence Judgment / View Completeness，把大模型预算留给 Evidence-Enhanced Reasoning。
4. **改进 separated evidence composition**：针对 limitations 中的 widely separated evidence，可用 layout composition 或 masked collage 代替 minimal enclosing box，以减少 inter-evidence noise。
5. **自适应 patch policy**：先估计 evidence saliency / question complexity，再动态决定 patch size 和 $k$，避免简单样本的过度 test-time scaling。

## Open Questions / Follow-ups

- 如果把 BLIP-ITM 换成更强的 open-vocabulary grounding / retrieval model，DeepScan 的收益来自专家能力还是 bottom-up 流程的比例会如何变化？
- Refocusing 的四状态搜索是否足够覆盖多对象、强遮挡、跨区域空间关系？是否需要针对多 evidence 图构造 compositional view search？
- Evidence Judgment 依赖 LVLM 的 Yes/No 判断，是否会在 hard negatives 上产生 confirmation bias？能否引入 calibrated confidence 或 self-consistency？
- 对 GUI agents、medical images、remote sensing 等高分辨率场景，patch size、top-$k$ 和 mask post-processing 是否需要 domain-specific tuning？
- 当前方法主要报告 accuracy / mIoU / latency；如果用于可解释性，是否需要评估 evidence faithfulness 或 human agreement？

## Citation

```bibtex
@misc{li2026deepscan,
  title={DeepScan: A Training-Free Framework for Visually Grounded Reasoning in Large Vision-Language Models},
  author={Li, Yangfu and Zhan, Hongjian and Chen, Jiawei and Gong, Yuning and Liu, Qi and Lu, Yue},
  year={2026},
  eprint={2603.03857},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  doi={10.48550/arXiv.2603.03857}
}
```

