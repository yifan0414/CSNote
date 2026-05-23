---
title: "A.I.R.: Enabling Adaptive, Iterative, and Reasoning-based Frame Selection For Video Question Answering"
authors:
  - Yuanhao Zou
  - Shengji Jin
  - Andong Deng
  - Youpeng Zhao
  - Jun Wang
  - Chen Chen
conference: ICLR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2510.04428
pdf_link: "[[Paper/raw/a-i-r-adaptive-iterative-and-reasoning-based-frame-selection-for-video-question/assets/paper_2510.04428.pdf]]"
cover: "[[Paper/raw/a-i-r-adaptive-iterative-and-reasoning-based-frame-selection-for-video-question/assets/pipeline_2510.04428.png]]"
updated: 2026-05-21
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: https://ucf-air.github.io/
---

## TL;DR

- **A.I.R.** 是一个 training-free 的 VideoQA frame selection 方法，目标是在不把整段视频全部送入 VLM 的前提下，选出足够覆盖答案证据的少量 frames。
- 方法把轻量级 CLIP 相似度只作为粗筛信号，再用 Analysis VLM 对小批量高潜力 frames 做 reasoning-based relevance scoring，避免纯 CLIP 的语义误判，也避免全量 VLM analysis 的成本爆炸。
- 核心流程是两段式：Adaptive Initial Sampling 找 query-relevant events；Iterative Frame Selection 用 Interval Potential Ranking、VLM Analysis、Early Stop 和 Localized Density Sampling 反复收敛到关键时刻。
- 在 Video-MME、MLVU、LongVideoBench、EgoSchema、NextQA 上，A.I.R. 对 VILA-1.5、QwenVL-2.5、InternVL3、LLaVA-OneVision 都有稳定提升；InternVL3-8B + A.I.R. 在 Video-MME w/o subtitle 达到 **68.2**，NextQA 达到 **82.6**。
- 效率上，默认设置 $C=12,\mathcal{I}_{\max}=6,V_{\max}=32$，理论最坏 VLM analysis workload 为 $72$ frames；在 Video-MME 上平均只分析 **36.5** frames，用 **42.31s**，低于直接分析 128 frames 的 **162.03s**。

## Key Contributions

1. 提出 **Adaptive Initial Sampling**：用每个视频自己的 query-frame similarity 分布拟合二组分 GMM，得到自适应阈值 $T$，先定位潜在事件区间，再按事件持续时间分配 sampling budget。
2. 提出 **Iterative Frame Selection**：每轮只把少量 high-potential candidates 送入 Analysis VLM 做细粒度语义判断，并用 Early Stop 控制预算。
3. 提出 **Localized Density Sampling (LDS)**：被 VLM 验证为 positive 的 frames 会触发局部搜索，从原始高帧率视频中补充邻近 frames，弥补初始 CLIP 相似度可能漏掉的关键证据。
4. 给出清晰的 efficiency bound：相比一次性分析 $n_{\mathrm{base}}$ 个 frames，A.I.R. 的 Analysis VLM workload 满足 $C \leq n_{\mathrm{A.I.R.}} \leq C\cdot\mathcal{I}_{\max}$。
5. 以 plug-and-play 形式验证多种 foundation VLM 和多个 VideoQA / temporal grounding benchmark，证明方法不是绑定某个 backbone 的 trick。

## Method

**整体 pipeline**

1. 输入视频共有 $N$ frames，先以固定 FPS 采样得到 $n$ frames。
2. 使用 EVA-CLIP-L 计算 query-frame similarity，得到稀疏信号 $S\in\mathbb{R}^{N}$；没有计算过的位置标记为 `NaN`，后续跳过。
3. **Adaptive Initial Sampling**：
   - 用二组分 GMM 建模 similarity 分布，阈值为：

$$
T=\max(\mu_1,\mu_2)-\gamma\cdot\max(\sigma_1,\sigma_2)
$$

   - 把 $S_i\geq T$ 的连续片段视作 candidate events，再做短间隔 merge 和短事件 prune。
   - 根据事件长度分配每个 event 的 frame budget，并在每个 event 内取 similarity 最高的 frames，得到 $\mathcal{F}_{\mathrm{initial}}$。
4. **Iterative Frame Selection**：
   - **Interval Potential Ranking**：把当前 sampled frames 划分出的 temporal intervals 排序。离散 potential 是 relevance、complexity、length 三项的乘积：

$$
\mathrm{Potential}(\mathrm{I}_i)=
\mathrm{Mean}(S_{f_i:f_{i+1}})
\cdot
\left(1+\frac{\sum_{j=f_i}^{f_{i+1}}|S_{j+1}-S_j|}{f_{i+1}-f_i}\right)
\cdot
\left(1+c_{\mathrm{len}}\cdot\lg(f_{i+1}-f_i)\right)
$$

   - **Reasoning-Based VLM Analysis**：每轮选 top-$C$ candidates，Analysis VLM 给 1 到 5 的 relevance score 和一句 reasoning；score $>\theta$ 的 frames 进入 validated set。
   - **Early Stop**：若累计选中 frames 已达到 adaptive budget $B$，停止迭代。
   - **Localized Density Sampling**：若未达到预算，在 positive frames 周围以指数增长 stride 搜索更多 frames：

$$
\mathrm{LDS}(f_i^*)=\{\mathrm{round}(f_i^*\pm\alpha\cdot\beta^{(m-1)})\mid m=1,2,\ldots,D\}
$$

5. **QA Stage**：把最终 frames $\mathcal{F}_{\mathrm{final}}^*$ 送入 Answering VLM 做一次 VideoQA 推理。

**关键超参数 / 训练细节**

| Item | Value |
| --- | --- |
| VLM backbones | VILA-1.5-8B, QwenVL-2.5-7B, InternVL3-8B, LLaVA-OneVision-7B |
| Similarity model | EVA-CLIP-L |
| Initial sampling | 1 FPS |
| Adaptive budget | $B=\max(\min(\lfloor V_{\max}\cdot n/300\rfloor,V_{\max}),V_{\min})$ |
| Minimum budget | $V_{\min}=8$ |
| GMM coefficient | $\gamma=0.7$ |
| Event merge / prune | $d_{\min}=2\times24$ frames, $l_{\min}=3\times24$ frames in main text; appendix comprehensive ablation uses normalized $l_{\min}=20,d_{\min}=2.0s$ |
| Initial candidate count | $K=2\cdot\max(B,C)$ |
| Candidate pool | $C=12$ |
| Max iterations | $\mathcal{I}_{\max}=6$ |
| VLM score threshold | score range 1-5, positive threshold $\theta=3$ |
| LDS | $\alpha=\max(0.05\cdot\lvert\mathrm{I}_i\rvert,15)$, $\beta=1.5$ |
| Experimental environment | NVIDIA GH200 GPUs, PyTorch 2.5, CUDA 11.6, GCC 11.4.0, lmms-eval |

## Pipeline Figure

![[Paper/raw/a-i-r-adaptive-iterative-and-reasoning-based-frame-selection-for-video-question/assets/pipeline_2510.04428.png]]

Caption: 图中展示 A.I.R. 的两个核心阶段：先用 GMM threshold 与 event-wise sampling 生成 $\mathcal{F}_{\mathrm{initial}}$，再通过 Interval Potential Ranking、Reasoning-Based VLM Analysis、Early Stop 和 LDS 逐轮细化最终 frames。

Source: TeX `\includegraphics{detail_pipeline.pdf}` from `iclr2026_conference.tex` figure label `fig:detail pipeline`; exported to `assets/pipeline_2510.04428.png` from the source PDF using crop-box rendering at 250 DPI.

## Experiments

**Datasets / Benchmarks**

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| Video-MME | Long-video VideoQA | w/o subtitle, w/ subtitle | Accuracy | 主要长视频 benchmark，另有 question type radar analysis |
| MLVU | Long-video understanding / VideoQA | dev | Accuracy | 长视频 benchmark |
| LongVideoBench (LVB) | Long-video VideoQA | val | Accuracy | 长视频 benchmark |
| EgoSchema | VideoQA | Full, Subset | Accuracy | 短视频 / ego-centric benchmark |
| NextQA | VideoQA | not specified | Accuracy | 短视频 benchmark，常用于效率对比 |
| Charades-STA | Temporal grounding | not specified | R1@0.3, R1@0.5, R1@0.7, mIoU | 用于验证 frame selection 泛化到 temporal grounding |

**Main Results: Long-Video Benchmarks**

| Method | Model / Setting | #Frames | Video-MME w/o sub. | Video-MME w/ sub. | MLVU_dev | LVB_val |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| VILA-1.5<sup>†</sup> | 8B | 8 | 48.9 | 54.2 | 44.7 | 47.9 |
| +Frame-Voyager<sup>*</sup> | 8B | 8 | 50.5 | 53.6 | 49.8 | - |
| +MDP3<sup>†</sup> | 8B | 8 | 53.3 | 57.8 | 52.3 | 52.3 |
| +Q-Frame<sup>*</sup> | 8B | 8 | 50.7 | 55.0 | **54.4** | 51.6 |
| **+Ours** | 8B | 8 | **53.7** | **58.6** | 54.2 | **52.9** |
| QwenVL-2.5<sup>†</sup> | 7B | 32 | 60.8 | 62.7 | 59.3 | 58.1 |
| +MDP3<sup>†</sup> | 7B | 32 | 63.8 | 65.7 | 66.2 | 60.0 |
| **+Ours** | 7B | $\leq32$ | **65.0** | **66.3** | **67.5** | **61.4** |
| InternVL3<sup>†</sup> | 8B | 32 | 65.6 | 67.3 | 68.4 | 58.3 |
| +MDP3<sup>†</sup> | 8B | 32 | 66.8 | 69.0 | 74.0 | 60.9 |
| **+Ours** | 8B | $\leq32$ | **68.2** | **69.2** | **74.5** | **62.8** |
| LLaVA-OneVision<sup>†</sup> | 7B | 32 | 58.5 | 61.7 | 62.4 | 56.6 |
| +AKS<sup>*</sup> | 7B | 32 | 58.4 | - | - | 59.3 |
| +MDP3<sup>†</sup> | 7B | 32 | 60.5 | 64.0 | 68.3 | 59.0 |
| +BOLT<sup>*</sup> | 7B | 32 | 59.9 | - | 66.8 | 59.6 |
| **+Ours** | 7B | $\leq32$ | **61.4** | **65.1** | **69.3** | **60.7** |

**Main Results: EgoSchema / NextQA**

| Method                            | Model / Setting |  #Frames | EgoSchema Full | EgoSchema Subset |   NextQA |
| --------------------------------- | --------------- | -------: | -------------: | ---------------: | -------: |
| LLoVi<sup>*</sup>                 | GPT-3.5         |  0.5 FPS |           52.2 |                - |     66.3 |
| VideoAgent<sup>*</sup>            | GPT-4           |    1 FPS |           54.1 |             60.2 |     71.3 |
| M-LLM-based selection<sup>*</sup> | 8.5B            |       32 |              - |             65.9 |     78.4 |
| SeViLA<sup>*</sup>                | 4.1B            |        4 |              - |                - |     73.8 |
| VideoTree<sup>*</sup>             | GPT-4           |        - |           61.1 |             66.2 |     75.6 |
| MVU<sup>*</sup>                   | 13B             |       16 |           37.6 |             60.3 |     55.2 |
| DrVideo                           | GPT-4           |        - |           61.0 |             66.4 |        - |
| T<sup>*</sup>                     | 7B              |        8 |              - |             66.6 |     80.4 |
| VILA-1.5<sup>†</sup>              | 8B              |        8 |           49.5 |             52.8 |     65.9 |
| **+Ours**                         | 8B              |        8 |       **50.7** |         **53.6** | **70.3** |
| QwenVL-2.5<sup>†</sup>            | 7B              |       32 |           57.6 |             59.4 |     74.3 |
| **+Ours**                         | 7B              | $\leq32$ |       **58.8** |         **62.4** | **81.3** |
| InternVL3<sup>†</sup>             | 8B              |       32 |           62.5 |             71.6 |     82.3 |
| **+Ours**                         | 8B              | $\leq32$ |       **63.3** |         **72.2** | **82.6** |
| LLaVA-OneVision<sup>†</sup>       | 7B              |       32 |           60.2 |             61.8 |     79.3 |
| +BOLT<sup>*</sup>                 | 7B              |       32 |           60.7 |         **64.0** |     79.5 |
| **+Ours**                         | 7B              | $\leq32$ |       **61.4** |             63.2 | **81.6** |

**Generalization: Charades-STA Temporal Grounding**

| Method | R1@0.3 | R1@0.5 | R1@0.7 | mIoU |
| --- | ---: | ---: | ---: | ---: |
| VTimeLLM | 51.0 | 27.5 | 11.4 | 31.2 |
| HawkEye | 50.6 | 31.4 | 14.5 | 33.7 |
| TimeChat | - | 32.2 | 13.4 | 30.6 |
| TimeSuite | **69.9** | **48.7** | **24.0** | - |
| GPT-4o | 55.0 | 32.0 | 11.5 | 35.4 |
| Qwen2.5-VL-7B | 44.5 | 30.3 | 15.2 | 30.1 |
| GenS | 62.9 | 38.7 | 15.2 | 38.0 |
| **A.I.R. (Qwen2.5-VL-7B)** | 59.5 | 39.5 | 18.0 | **38.8** |

**Ablations / Analysis: Components**

| # | Variant / Setting | Avg. Frames | Video-MME Acc. |
| ---: | --- | ---: | ---: |
| 1 | Uniform Sampling | 32.0 | 65.6 |
| 2 | **A.I.R. full method** | 24.8 | 68.2 |
| 3 | w/ Fixed 32 frames, no adaptive budget | 32.0 | **68.3** |
| 4 | w/o Adaptive Similarity Thresholding | 25.5 | 67.3 |
| 5 | w/o Adaptive Initial Sampling | 25.1 | 66.9 |
| 6 | w/o Iterative Frame Selection | 32.0 | **65.2** |
| 7 | w/o Interval Potential Ranking | 26.2 | 66.7 |
| 8 | w/o Reasoning-based VLM Analysis | 32.0 | 66.0 |
| 9 | w/o Localized Density Sampling | 24.5 | 67.2 |

注：表中保留了原论文对数值的强调；第 6 行的加粗来自源表。

**Ablations / Analysis: CLIP Variants**

| Variant / Setting | Video-MME Acc. |
| --- | ---: |
| Uniform Sampling (32 frames) | 65.6 |
| A.I.R. + CLIP-ViT-B | 66.8 |
| **A.I.R. + EVA-CLIP-L (default)** | **68.2** |
| A.I.R. + LongCLIP-L | 67.4 |
| A.I.R. + CLIP-ViT-L | 67.8 |
| A.I.R. + SigLIP-large | 67.1 |

**Efficiency: VLM Analysis-Based Frame Selection**

| Method | Benchmark / Setting | #Analyzed | Training-Free | Acc. / Time |
| --- | --- | ---: | --- | ---: |
| Frame-Voyager | NextQA, InternVL3-8B | 128 | No | 67.3 |
| M-LLM-based selection | NextQA, InternVL3-8B | 128 | No | 78.4 |
| VideoTree | NextQA, InternVL3-8B | 128 | Yes | 75.6 |
| VideoAgent | NextQA, InternVL3-8B | 48 | Yes | 71.3 |
| **A.I.R. ($w_{\mathrm{worst}}=72$)** | NextQA, InternVL3-8B | **32.2** | Yes | **82.6** |
| SeViLA | NextQA, InternVL3-8B | 32 | Yes | 73.8 |
| MVU | NextQA, InternVL3-8B | 16 | Yes | 55.2 |
| **A.I.R. ($w_{\mathrm{worst}}=16$)** | NextQA, InternVL3-8B | **12.4** | Yes | **81.7** |
| Direct VLM Analysis | Video-MME, 128 frames | 128 | - | 162.03s |
| **A.I.R. ($w_{\mathrm{worst}}=72$)** | Video-MME | **36.5** | - | **42.31s** |
| Direct VLM Analysis | Video-MME, 32 frames | 32 | - | 42.47s |
| **A.I.R. ($w_{\mathrm{worst}}=32$)** | Video-MME | **20.3** | - | **21.92s** |
| Direct VLM Analysis | Video-MME, 16 frames | 16 | - | 20.39s |
| **A.I.R. ($w_{\mathrm{worst}}=16$)** | Video-MME | **14.1** | - | **14.61s** |

**Hyperparameter Trade-off on NextQA**

| # | $V_{\max}$ | $C$ | $\mathcal{I}_{\max}$ | Time (s) / analyzed frames | Accuracy (%) |
| ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 16 | 8 | 2 | 14.87 (13.6f) | 81.61 |
| 2 | 16 | 4 | 4 | 12.62 (12.4f) | 81.68 |
| 3 | 16 | 8 | 4 | 18.92 (20.3f) | 81.92 |
| 4 | 32 | 8 | 4 | 29.17 (27.2f) | 82.20 |
| 5 | **32** | **12** | **6** | **34.24 (32.2f)** | **82.63** |
| 6 | 32 | 16 | 8 | 36.52 (35.6f) | **82.91** |

作者选择第 5 行作为默认配置：相比第 6 行只少约 0.28 accuracy，但 VLM workload 更低。

**Frame Budget Scaling**

| Backbone | Budget / Method | Video-MME w/o sub. | Video-MME w/ sub. | MLVU_dev | LVB_val | EgoSchema Full | EgoSchema Subset | NextQA |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QwenVL-2.5 | 32 | 60.8 | 62.7 | 59.3 | 58.1 | 57.6 | 59.4 | 74.3 |
| QwenVL-2.5 | **A.I.R. $\leq32$** | **65.0** | **66.3** | **67.5** | **61.4** | **58.8** | **62.4** | **81.3** |
| QwenVL-2.5 | 64 | 61.2 | 65.0 | 63.8 | 59.0 | 58.8 | 62.0 | 75.9 |
| QwenVL-2.5 | **A.I.R. $\leq64$** | **65.9** | **67.2** | **69.7** | **62.5** | **59.8** | **63.2** | **82.5** |
| QwenVL-2.5 | 256 | 63.4 | 67.3 | 67.8 | 60.2 | 58.8 | 62.6 | 74.3 |
| QwenVL-2.5 | **A.I.R. $\leq256$** | **66.4** | **67.9** | **71.7** | **62.8** | **59.9** | **63.6** | **83.3** |
| LLaVA-OneVision | 32 | 58.5 | 61.7 | 62.4 | 56.6 | 60.2 | 61.8 | 79.3 |
| LLaVA-OneVision | +BOLT 32 | 59.9 | - | 66.8 | 59.6 | 60.7 | 64.0 | 79.5 |
| LLaVA-OneVision | **A.I.R. $\leq32$** | **61.4** | **65.1** | **69.3** | **60.7** | **61.4** | **64.2** | **81.6** |

## Limitations & Caveats

- A.I.R. 的上限受 Analysis VLM 自身能力限制；同样大小附近的模型中，InternVL3-8B 明显强于 VILA-1.5。
- 对 fine-grained counting 任务仍然偏弱：Video-MME question type analysis 中 Counting Problem 是 A.I.R. 最低的一类，分数为 49.3。
- 当前只处理 visual track，没有利用 audio；如果答案证据来自声音、语音或背景音，方法可能漏掉关键线索。
- 虽然比 brute-force VLM analysis 高效很多，iterative loop 仍引入额外 latency，不一定适合严格 real-time 场景。
- CLIP feature cache 能降低重复视频上的相似度计算成本；在首次处理新视频时，CLIP preprocessing / resizing 仍可能成为额外开销。
- 论文说 supplementary 会提供两个核心阶段的 partial code；公开项目页是否已经发布完整可复现实作需要后续确认。

## Concrete Implementation Ideas

1. 在现有 VideoQA evaluation pipeline 中做一个 `FrameSelector` interface，让 Uniform、CLIP Top-K、A.I.R. 共享同一输入输出：query、frames、similarity cache、selected indices。
2. 先实现 Adaptive Initial Sampling 与 Interval Potential Ranking，使用 NumPy / scikit-learn GMM；把 $S$ 作为 sparse array，未计算位置保持 `NaN`。
3. Analysis VLM prompt 可以独立封装成 batch scoring API，输出 `{frame_id, score, reasoning}`；score 校验失败时回退到 CLIP similarity 排序。
4. 把 LDS 的 $\alpha,\beta,D$ 与 budget schedule 配置化，按 short / medium / long video 自动选择 conservative 或 aggressive strategy。
5. 为 counting / audio-dependent queries 加一个 query classifier：如果问题含 “how many”、声音线索或 subtitles 依赖，优先提高 budget 或加入 audio/subtitle evidence retrieval。

## Open Questions / Follow-ups

- A.I.R. 对包含强 audio cue 的 VideoQA 数据集表现会怎样？audio-aware LDS 是否能显著补强？
- Counting 类问题的弱点来自 frame selection 还是 Answering VLM 对多目标计数的能力？需要 oracle frames 对照实验。
- Analysis VLM 的 1-5 relevance score 是否需要 calibration？不同 VLM 的 $\theta=3$ 是否同样合理？
- CLIP 初筛若在某些 query 上完全偏离，GMM threshold 是否会让真实事件在第一阶段就被排除？能否加入 diversity 或 subtitle prior 降低风险？
- 实际部署中，iterative VLM analysis 的 latency 能否通过 speculative batch、early confidence stop 或 multi-resolution frame pyramid 进一步降低？

## Citation

```bibtex
@misc{zou2026airenablingadaptiveiterative,
  title={A.I.R.: Enabling Adaptive, Iterative, and Reasoning-based Frame Selection For Video Question Answering},
  author={Yuanhao Zou and Shengji Jin and Andong Deng and Youpeng Zhao and Jun Wang and Chen Chen},
  year={2026},
  eprint={2510.04428},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2510.04428}
}
```
