---
title: (frame)QCA
authors:
  - Jun Peng
  - Baiyang Song
  - Jie Li
  - Hui Li
  - Yiyi Zhou
  - Rongrong Ji
  - Yonghong Tian
conference: ECCV 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2607.00983
pdf_link: "[[assets/paper_2607.00983.pdf]]"
cover: "[[_assets/images/pipeline_2607.00983.png]]"
updated: 2026-08-23
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - video-llm
status: read
priority:
rating:
topics:
  - Video Understanding
code: https://github.com/hktk07/QCA
---

## TL;DR

- QCA 面向长视频中的严重时间冗余，在固定帧预算下根据问题和视频内容选择紧凑、信息密度高的关键帧。
- 方法先综合 query relevance 与 content deviation，为不同时间段动态分配帧预算，再在段内兼顾语义相关性和内容多样性进行选择。
- QCA 是 training-free、plug-and-play 的预处理框架，不修改 Video-LLM 架构，可接入不同 MLLM 与 Vision-Language embedding。
- 作者报告 QCA 在多个长视频理解基准和不同 Video-LLM backbone 上具有稳定泛化能力；具体实验结果保留在下方原始表格截图中。

## Key Contributions

- 将 query-conditioned 长视频关键帧选择表述为有限预算下的相关性、多样性与跨时间段资源分配问题。
- 提出 Inter-Segment Keyframe Allocation，根据语义匹配与片段内容偏离程度估计每个时间段的信息贡献，并动态分配关键帧数量。
- 提出 Intra-Segment Keyframe Selection，以最相关帧为 anchor，在相关性约束后的候选集中贪心选择与当前集合差异最大的帧。
- 整体流程无需额外训练，可作为 Video-LLM 前端独立部署。

## Method

给定以 1 FPS 预采样的视频帧集合 $\mathcal{X}=\{x_1,\ldots,x_N\}$ 和问题 $q$，目标是在 $N'\ll N$ 的预算内构造关键帧集合 $\mathcal{K}$，再交给 Video-LLM 完成推理：

$$
\mathrm{answer}=\mathrm{MLLM}(\mathcal{K},q).
$$

### Temporal Segmentation

QCA 默认将视频均匀划分为 $S=12$ 个互不重叠的时间段 $\mathcal{X}_s$。这一层先建立粗粒度时间结构，再决定每个时间段获得多少帧预算。

### Inter-Segment Keyframe Allocation

对每个时间段，使用 Image-Text Matching 计算平均 query relevance：

$$
M_s=\frac{1}{|\mathcal{X}_s|}\sum_{x_i\in\mathcal{X}_s}\mathrm{ITM}(x_i,q).
$$

同时用片段均值相对全视频均值的偏离，以及片段内部协方差的迹，衡量 content deviation：

$$
D_s=\|\mu_{\mathcal{X}_s}-\mu_{\mathcal{X}}\|_2^2+\mathrm{Tr}(\Sigma_{\mathcal{X}_s}).
$$

经过归一化后，二者组合为片段贡献分数 $c_s=\alpha M_s+\beta D_s$，再通过温度控制的权重分配总帧预算：

$$
w_s=\frac{c_s^\tau}{\sum_{j=1}^{S}c_j^\tau},\qquad
q_s=\lfloor w_sN'\rfloor.
$$

取整产生的剩余预算继续分配给贡献分数最高的时间段，使最终关键帧总数满足 $N'$。

### Intra-Segment Keyframe Selection

每个时间段先选择 ITM 分数最高的帧作为 semantic anchor。随后用 anchor 分数 $R^*$ 和阈值 $\gamma$ 构造候选集：

$$
\mathcal{C}_s=\{x_j\in\mathcal{X}_s\mid \mathrm{ITM}(x_j,q)\geq\gamma R^*\}.
$$

在候选集中，算法反复选择与当前关键帧集合具有最大聚合距离的帧，直到达到该时间段的预算 $q_s$。这样既保留与问题相关的证据，也避免选择大量语义重复帧。

## Pipeline Figure

![[_assets/images/pipeline_2607.00983.png]]

Caption: The proposed QCA consists of: (a) Inter-Segment Keyframe Allocation, where the frame budget for each segment is dynamically determined by considering semantic alignment and visual content deviation; (b) Intra-Segment Keyframe Selection, which iteratively adds the frame with the maximum aggregate distance to the current keyframe set $\mathcal{K}_s$ from a relevance-filtered candidate set $\mathcal{C}_s$.

## Experiments

评测覆盖 LongVideoBench、Video-MME（不使用字幕）、MLVU 和 LVBench。Backbone 包括 LLaVA-Video、InternVL-3.5 和 Qwen3-VL；统一从原视频以 $1$ FPS 预采样，并在主要对比中采用 $64$ 帧预算。默认 Vision-Language embedding 为 BLIP-2，设置 $\alpha=\beta=0.5$、$\tau=0.5$，候选阈值 $\gamma=0.7$。论文报告实验运行于 $8\times$A800 80G GPU。

### Main Results - Table 1

![[_assets/images/experiment_table_2607.00983_t1.png]]

### State-of-the-Art Comparison - Table 2

![[_assets/images/experiment_table_2607.00983_t2.png]]

### Ablation Study - Table 3

![[_assets/images/experiment_table_2607.00983_t3.png]]

### VL Embeddings - Table 4

![[_assets/images/experiment_table_2607.00983_t4.png]]

### Keyframe Budget - Table 5

![[_assets/images/experiment_table_2607.00983_t5.png]]

### Token-Pruning Comparison - Table 6

![[_assets/images/experiment_table_2607.00983_t6.png]]

## Limitations & Caveats

- 论文采用均匀时间分段以换取简单性与效率，但固定时间段不一定对应视频中的真实语义边界；作者将 content-aware segmentation 或 shot boundary detection 视为后续方向。
- 关键帧选择依赖 ITM 与视觉 embedding 的质量。若预训练表示不能识别问题中的细粒度实体或动作，相关帧可能在候选集构造前被过滤。
- $\gamma$、$S$、$\alpha$、$\beta$ 和 $\tau$ 控制相关性、多样性与时间粒度之间的权衡，不同视频领域可能需要重新校准。
- 1 FPS 的初始预采样降低了计算成本，但极短暂事件可能在进入 QCA 之前已经丢失。
- QCA 是 query-conditioned 方法；同一视频面对不同问题时需要重新计算匹配与选择过程，适合通过缓存视觉特征降低重复开销。

## Concrete Implementation Ideas

1. 将 QCA 实现为独立于 Video-LLM 的预处理器，输入视频、问题和 frame budget，输出帧索引及对应图像，先接入 Qwen3-VL 或 LLaVA-Video 验证端到端流程。
2. 对视频的 1 FPS 帧特征、片段统计量和视觉 embedding 建立持久化缓存；新问题只重新计算 query-dependent ITM 与后续选择。
3. 将均匀分段替换为 shot boundary detection，并设置每个 shot 的最小预算，比较语义分段与固定 $S$ 的稳定性。
4. 在服务端记录每个时间段的 $M_s$、$D_s$、$q_s$ 和最终帧索引，构建可视化诊断页面以定位漏选关键证据的阶段。
5. 在相同视觉 token 预算下同时测试 frame selection 与 token pruning，分别统计预处理延迟、Video-LLM 推理延迟和显存占用。

## Open Questions / Follow-ups

- 能否学习或动态预测 $S$，使时间分段更贴近事件边界，同时保持 training-free 特性？
- 对需要多跳时间推理的问题，单帧相关性是否足以分配预算，还是需要显式建模跨片段关系？
- 如何在极低帧预算下避免某些时间段因取整而完全失去预算？
- 候选集阈值能否依据问题类型、片段熵或匹配分布自适应调整？
- 对同一视频的大量查询，怎样联合选择共享上下文帧与 query-specific 帧，以降低重复计算？

## Citation

```bibtex
@article{peng2026qca,
  title={QCA: Query- and Content-Aware Keyframe Selection for Long Video Understanding},
  author={Peng, Jun and Song, Baiyang and Li, Jie and Li, Hui and Zhou, Yiyi and Ji, Rongrong and Tian, Yonghong},
  journal={arXiv preprint arXiv:2607.00983},
  year={2026}
}
```
