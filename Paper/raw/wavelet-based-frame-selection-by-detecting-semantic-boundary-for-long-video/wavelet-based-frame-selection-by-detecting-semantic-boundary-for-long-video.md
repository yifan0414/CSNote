---
title: WFS-SB(frame)
authors:
  - Wang Chen
  - Yuhui Zeng
  - Yongdong Luo
  - Tianyu Xie
  - Luojun Lin
  - Jiayi Ji
  - Yan Zhang
  - Xiawu Zheng
conference: CVPR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2603.00512
pdf_link: "[[assets/paper_2603.00512.pdf]]"
cover: "[[assets/pipeline_2603.00512.png]]"
updated: 2026-05-21
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: unread
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/MAC-AutoML/WFS-SB
---

## TL;DR

- 这篇论文提出 WFS-SB，一个 training-free 的 long-video frame selection 框架，核心不是只选和 query 最相关的帧，而是先找 query-frame relevance signal 中的 semantic boundary。
- 方法把 1 FPS 采样后的 BLIP-2 ITM 分数看成时间信号，用 Daubechies-4 Discrete Wavelet Transform 去掉高频噪声，再用最粗尺度 detail coefficients 的重构信号找语义变化峰值。
- 找到边界后，视频被切成 temporal semantic segments；每个 segment 根据时长、平均相关性、峰值相关性、方差得到 importance score，再用 softmax 分配总帧预算 $K$。
- segment 内部使用 localized Maximal Marginal Relevance (MMR) 选择帧，兼顾 query relevance 和视觉多样性，避免全局 top-k 把帧集中在少数相似片段里。
- 在 VideoMME、MLVU、LongVideoBench 上，WFS-SB 对多个 LVLM backbone 都有稳定增益；例如 LLaVA-Video-7B, $K=8$ 时分别提升 5.5、9.5、6.2 accuracy points。
- 主要代价在 ITM score extraction，平均 19.4s，占 preprocessing 时间约 79%；wavelet 和 selection 本身几乎不重。

## Key Contributions

1. 提出一个 semantic-shift-first 的 frame selection 视角：长视频理解不应只问“哪些帧最相关”，还要问“故事章节什么时候变化”。
2. 将 query-frame relevance 序列建模为 noisy non-stationary temporal signal，并用 DWT 的 multi-resolution analysis 从粗尺度变化中提取 semantic boundary。
3. 提出完整的 WFS-SB pipeline：semantic segmentation、adaptive budget allocation、localized MMR selection，整体无需训练，也不改 LVLM 架构。
4. 在三类 long-video QA benchmark 和四个 backbone 上展示 plug-and-play 增益，并通过 component ablation 证明 DWT、budget allocation、MMR 都有贡献。

## Method

给定视频 $\mathcal{V}$ 的 $T$ 帧和 query $q$，目标是选择按时间排序的 $K$ 帧子集 $\mathcal{F}=\{f_1,\dots,f_K\}$，使 LVLM 在这些视觉上下文和 query 下回答更准确。论文先以 1 FPS 采样得到 $N$ 帧，并用 BLIP-2 的 ITM head 得到 query-frame score：

$$
s_t = \mathcal{M}(q, f_t), \quad t = 1, \dots, N.
$$

WFS-SB 的 pipeline 可以压缩成下面几步：

1. **Temporal relevance signal**：把 $\{s_t\}_{t=1}^{N}$ 视为随时间变化的 query relevance signal，而不是独立分数。
2. **Adaptive DWT**：使用 db4 wavelet 分解，分解层数按视频长度自适应：

$$
J = \max\left(1, \left\lfloor \log_2 N \right\rfloor - l\right), \quad l=3.
$$

3. **Semantic change extraction**：只保留最粗尺度 detail coefficients $d_J$，其余 coefficients 置零后做 IDWT，得到粗粒度变化信号：

$$
\tilde{s}_t = \text{IDWT}(\{\mathbf{0}, d_J, \mathbf{0}, \dots, \mathbf{0}\}).
$$

4. **Boundary detection**：计算 $c_t = |\tilde{s}_t|$，用 adaptive height、prominence、minimum distance 找 local maxima，得到边界集合 $\mathcal{B}=\{b_1,\dots,b_M\}$，并切出 $M+1$ 个 temporal semantic segments。
5. **Adaptive budget allocation**：每个 segment $\mathcal{G}_i$ 的 importance score 为：

$$
\text{Imp}(\mathcal{G}_i) = w_d \cdot \frac{|\mathcal{G}_i|}{N} + w_a \cdot \bar{s}_i + w_m \cdot s_i^{\max} + w_v \cdot \frac{\sigma_i^2}{\sigma_{\text{global}}^2}.
$$

默认权重为 $w_d=0.4, w_a=0.2, w_m=0.3, w_v=0.1$。低 importance segment 会按 $\tau=\text{mean}(\text{Imp})-\eta\cdot\text{std}(\text{Imp})$ 过滤，默认 $\eta=1.2$。

6. **Localized MMR selection**：每个 segment 先选最相关 anchor，再迭代选择：

$$
t^* = \underset{t \in \mathcal{G}_i \setminus \mathcal{T}_i}{\operatorname{argmax}} \left[ \lambda \cdot s_t - (1-\lambda) \cdot \max_{t' \in \mathcal{T}_i} \text{sim}(f_t, f_{t'}) \right],
$$

其中 $\lambda=0.5$，最后合并所有 segment 内选出的帧并按时间排序。

## Pipeline Figure

![[assets/pipeline_2603.00512.png]]

Caption: WFS-SB framework overview，包括 wavelet-based semantic boundary identification、adaptive budget allocation、diversity-aware intra-segment selection 三个阶段。

Source: TeX includegraphics from `sec/3_method.tex`, `figure/method_v2.pdf`; converted with `pdftoppm -cropbox` to `assets/pipeline_2603.00512.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| VideoMME | Long-video QA | 900 videos, 2,700 QA pairs | Accuracy (%) | 平均 17 min；不使用 subtitles。 |
| MLVU | Multiple-choice long-video QA | 2,174 questions, 7 categories | Accuracy (%) | 平均 11 min；不使用 subtitles。 |
| LongVideoBench (LVB) | Long-context interleaved video-language QA | 1,337-pair validation set | Accuracy (%) | 平均 12 min；不使用 subtitles。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Method type | Training-free frame selection |
| Candidate sampling | 1 FPS by default |
| Query-frame scorer | BLIP-2-ITM-ViT-g ITM head |
| Wavelet | Daubechies-4 (db4), drift factor $l=3$ |
| Budget weights | $w_d=0.4$, $w_a=0.2$, $w_m=0.3$, $w_v=0.1$ |
| Segment filtering | $\eta=1.2$ |
| MMR | $\lambda=0.5$ |
| Frame budgets | $K \in \{8,16,32,64\}$ |
| Hardware | NVIDIA A800 80GB GPUs |
| Evaluation toolkit | LMMs-Eval |

### Main Results

下表重排自 main paper Table 1。数值为 accuracy (%)；保留论文原始 bold / underline 语义，`+Method` 是使用对应 selection method 后的结果。

| Model | Method | Size | Frame | VideoMME Base | VideoMME +Method | VideoMME Δ | MLVU Base | MLVU +Method | MLVU Δ | LVB Base | LVB +Method | LVB Δ |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-OV | Frame-Voyager | 7B | 8 | 53.3 | 57.5 | +4.2 | 58.5 | 65.6 | +7.1 | - | - | - |
| LLaVA-OV | KFC | 7B | 8 | 53.3 | 55.4 | +2.1 | 58.5 | <u>66.2</u> | <u>+7.7</u> | 54.5 | 55.6 | +1.1 |
| LLaVA-OV | BOLT | 7B | 8 | 53.8 | 56.1 | +2.3 | 58.9 | 63.4 | +4.5 | 54.2 | 55.6 | +1.4 |
| LLaVA-OV | AKS | 7B | 8 | 54.1 | <u>58.2</u> | <u>+4.1</u> | 58.6 | 62.9 | +4.3 | 54.2 | <u>58.4</u> | <u>+4.2</u> |
| LLaVA-OV | FrameOracle | 7B | 8 | 53.8 | 57.5 | +3.7 | 58.4 | 62.9 | +4.5 | 54.3 | 56.0 | +1.7 |
| LLaVA-OV | **WFS-SB** | 7B | 8 | 54.1 | **59.3** | **+5.2** | 58.6 | **67.2** | **+8.6** | 54.2 | **59.8** | **+5.6** |
| LLaVA-Video | KFC | 7B | 8 | 55.9 | 57.6 | +1.7 | 60.5 | **66.9** | +6.4 | 54.2 | 56.5 | +2.3 |
| LLaVA-Video | BOLT | 7B | 8 | 56.0 | 58.6 | +2.6 | - | - | - | - | - | - |
| LLaVA-Video | AKS | 7B | 8 | 56.2 | <u>60.1</u> | <u>+3.9</u> | 57.4 | 64.2 | <u>+6.8</u> | 54.9 | <u>59.6</u> | <u>+4.7</u> |
| LLaVA-Video | FrameOracle | 7B | 8 | 55.9 | 58.9 | +3.0 | 60.5 | 63.4 | +2.9 | 54.2 | 56.9 | +2.7 |
| LLaVA-Video | **WFS-SB** | 7B | 8 | 56.2 | **61.7** | **+5.5** | 57.4 | **66.9** | **+9.5** | 54.9 | **61.1** | **+6.2** |
| Qwen2.5-VL | AKS | 7B | 32 | 61.2 | 64.0 | +2.8 | 59.7 | 67.2 | +7.5 | 58.9 | <u>63.2</u> | <u>+4.3</u> |
| Qwen2.5-VL | MDP$^3$ | 7B | 32 | 60.8 | 63.8 | +3.0 | 59.3 | 66.2 | +6.9 | 58.1 | 60.0 | +1.9 |
| Qwen2.5-VL | A.I.R. | 7B | ≤32 | 60.8 | **65.0** | **+4.2** | 59.3 | <u>67.5</u> | <u>+8.2</u> | 58.1 | 61.4 | +3.3 |
| Qwen2.5-VL | **WFS-SB** | 7B | 32 | 61.2 | <u>64.4</u> | <u>+3.2</u> | 59.7 | **70.4** | **+10.7** | 58.9 | **64.4** | **+5.5** |
| InternVL-3 | AKS | 8B | 32 | 65.6 | 66.3 | +0.7 | **68.4** | 74.2 | +5.8 | 58.5 | 61.5 | +3.0 |
| InternVL-3 | MDP$^3$ | 8B | 32 | 65.6 | 66.8 | +1.2 | 68.4 | 74.0 | +5.6 | 58.3 | 60.9 | +2.6 |
| InternVL-3 | A.I.R. | 8B | ≤32 | 65.6 | **68.2** | **+2.6** | 68.4 | <u>74.5</u> | <u>+6.1</u> | 58.3 | <u>62.8</u> | **+4.5** |
| InternVL-3 | **WFS-SB** | 8B | 32 | 65.6 | <u>67.4</u> | <u>+1.8</u> | 68.4 | **74.8** | **+6.4** | 58.5 | **62.9** | <u>+4.4</u> |

作者总结的整体趋势是：WFS-SB 平均在 VideoMME、MLVU、LongVideoBench 上分别带来 3.9、8.8、5.4 points 的增益；对于 tight frame budget 尤其明显。

### Ablations / Analysis

**Different LVLM Scales.** Qwen2.5-VL 在 VideoMME 上跨模型规模的结果，表中为 $K=16/K=32$。

| Model Scale | Baseline | +WFS-SB | Δ |
| ---- | ---- | ---- | ---- |
| Qwen2.5-VL-3B | 54.1/57.8 | 58.4/60.0 | +4.3/+2.2 |
| Qwen2.5-VL-7B | 57.7/61.2 | 61.9/64.4 | +4.2/+3.2 |
| Qwen2.5-VL-32B | 60.2/62.9 | 63.0/66.1 | +2.8/+3.2 |
| Qwen2.5-VL-72B | 63.3/66.2 | 66.1/68.9 | +2.8/+2.7 |

**VLM Scorer.** 用 Qwen2.5-VL-7B, $K=16$ 测 query-frame similarity scorer。

| VLM Scorer | VideoMME | MLVU | LVB |
| ---- | ---- | ---- | ---- |
| Uniform | 57.7 | 56.2 | 57.0 |
| BLIP-ITM | **62.8** | 67.7 | **63.2** |
| CLIP-VIT-B | 61.7 | 66.5 | 60.6 |
| SigLIP-so400m | 61.9 | 66.4 | 61.9 |
| BLIP-2-ITM (Ours) | 61.9 | **67.9** | 62.5 |

**Component Ablation.** Qwen2.5-VL-7B, $K=16$。

| Configuration | VideoMME | MLVU |
| ---- | ---- | ---- |
| Uniform Sampling | 57.7 | 56.2 |
| **WFS-SB (full)** | **61.9** | **67.9** |
| w/o DWT (raw local minima) | 60.8 | 64.6 |
| w/o DWT (raw gradient) | 61.2 | 66.8 |
| w/o Adaptive B.A. (Average B.A.) | 61.6 | 67.4 |
| w/o MMR (topK selection) | 60.9 | 66.7 |
| w/o MMR (uniform selection) | 59.2 | 62.7 |

这个 ablation 直接支撑论文核心论点：raw local minima / raw gradient 都不如 DWT，说明粗尺度 wavelet decomposition 确实在抑制 high-frequency noise 和抽取 semantic transitions。

**Wavelet Family and Decomposition Level.** Qwen2.5-VL-7B, $K=16$。

| Metric | Db4, $l=3$ | Db4, $l=4$ | Db8, $l=3$ | Haar, $l=3$ | Sym4, $l=3$ | Bior3.3, $l=3$ |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| VideoMME | **61.9** | 60.4 | **61.9** | 61.3 | **61.9** | **61.9** |
| MLVU | 67.9 | **68.3** | 66.4 | 68.1 | 67.6 | 68.2 |

**Hyperparameters.** Qwen2.5-VL-7B, $K=16$。

| $w_d,w_a,w_m,w_v$ | $\lambda$ | VideoMME | MLVU |
| ---- | ---- | ---- | ---- |
| 0.4, 0.2, 0.3, 0.1 | 0.5 | 61.9 | **67.9** |
| 0.0, 0.3, 0.3, 0.2 | 0.5 | 61.6 | 64.8 |
| 0.5, 0.0, 0.3, 0.2 | 0.5 | 61.8 | 66.8 |
| 0.5, 0.3, 0.0, 0.2 | 0.5 | 62.0 | 66.8 |
| 0.5, 0.2, 0.3, 0.0 | 0.5 | **62.1** | 67.4 |
| 0.4, 0.2, 0.3, 0.1 | 0.3 | 61.2 | 67.5 |
| 0.4, 0.2, 0.3, 0.1 | 0.7 | 61.6 | 66.5 |

**Efficiency.** VideoMME, Qwen2.5-VL-7B, avg. $N=1040$, $K=32$。

| Component | Time (s) | Complexity |
| ---- | ---- | ---- |
| ITM Signal Extraction | 19.4 | $O(N)$ |
| DWT and Boundary Detection | $\sim 0$ | $O(N \log N)$ |
| Budget Allocation | $\sim 0$ | $O(M)$ |
| MMR Selection | 0.7 | $O(NK^2)$ |
| LVLM Inference | 4.4 | - |

**Adaptive FPS.** Supplementary 在 VideoMME + Qwen2.5-VL-7B 上测试降低长视频采样率来减少 ITM 开销。

| Sampling Rate | 8 F. | 16 F. | 32 F. | ITM Time (s) |
| ---- | ---- | ---- | ---- | ---- |
| Uniform Sampling | 53.2 | 57.7 | 61.2 | - |
| 1 fps | 59.3 | 61.9 | 64.4 | 19.4 |
| 1-0.75-0.5 fps | 58.9 | **62.0** | 64.5 | 10.5 |
| 1-0.5-0.25 fps | **59.4** | 61.9 | **64.6** | 5.8 |

这个结果很实用：从 1 fps 改为 1-0.5-0.25 fps 后，ITM time 从 19.4s 降到 5.8s，同时准确率没有明显损失。

## Limitations & Caveats

1. **ITM extraction overhead**：主要瓶颈是 dense query-frame ITM scores，平均 19.4s，占 preprocessing 约 79%；对 multi-hour videos 或 real-time 应用可能太慢。
2. **依赖 VLM scorer 质量**：WFS-SB 的 semantic boundaries 由 ITM signal 诱导，若底层 VLM 对某领域校准差、domain shift 强，边界会受影响。
3. **极端 temporal structure 敏感**：快速剪辑、广告、montage 可能过度切分；长时间低相关、短时间高相关的内容可能被 segment filtering 漏掉。
4. **不是端到端学习方法**：training-free 很轻巧，但也意味着 wavelet kernel、importance weights、thresholds 都是手工设计，可能无法适配所有任务分布。
5. **评估仍以 multiple-choice / benchmark accuracy 为主**：对 open-ended generation、复杂多轮 query、需要字幕或音频的场景，论文只给出 future work 而不是完整实验。

## Concrete Implementation Ideas

1. 在现有 Video-LLM inference pipeline 前加一个 `FrameSelector` 模块：输入 video path + query + K，输出按时间排序的 selected frame timestamps，保持下游 LVLM 完全不变。
2. 用便宜 scorer 做两级筛选：先用 CLIP/SigLIP 或低 FPS BLIP-2 粗扫，再只对疑似边界附近补算更密集的 ITM scores，降低 19.4s bottleneck。
3. 把 DWT boundary detector 做成可视化调试工具：画出 raw ITM signal、$\tilde{s}_t$、$c_t$、detected peaks 和 final selected frames，方便分析失败样例。
4. 对超长视频使用 adaptive FPS：短视频 1 fps，中等 0.5 fps，长视频 0.25 fps；supplementary 结果显示这条路线可能大幅省时。
5. 在多 query 场景中合并多个 relevance signals：对多个问题分别找 boundary，再做 union / weighted merge，得到一个共享 frame set。

## Open Questions / Follow-ups

1. WFS-SB 在 open-ended video captioning 或 event summarization 中是否仍然有效，还是只对 question-aware QA 最合适？
2. BLIP-2 ITM score 对不同视频域的校准如何？例如 egocentric、medical、surveillance、sports 中是否需要 domain-specific scorer？
3. importance score 中 duration、average relevance、max relevance、variance 的手工权重能否由 validation-free heuristic 或 learned policy 自动设置？
4. semantic boundaries 是否可以融合 audio / subtitles / ASR，例如将 speech topic shifts 和 visual relevance shifts 一起做 wavelet decomposition？
5. 和 token pruning / video token compression 方法叠加时，frame-level selection 和 token-level selection 的最优预算分配是什么？

## Citation

Chen et al. Wavelet-based Frame Selection by Detecting Semantic Boundary for Long Video Understanding. CVPR 2026 / arXiv:2603.00512.

```bibtex
@article{chen2026wavelet,
  title={Wavelet-based Frame Selection by Detecting Semantic Boundary for Long Video Understanding},
  author={Chen, Wang and Zeng, Yuhui and Luo, Yongdong and Xie, Tianyu and Lin, Luojun and Ji, Jiayi and Zhang, Yan and Zheng, Xiawu},
  journal={arXiv preprint arXiv:2603.00512},
  year={2026}
}
```
