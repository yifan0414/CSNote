---
标题: "FlashVID: Efficient Video Large Language Models via Training-free Tree-Based Spatiotemporal Token Merging"
作者: Ziyang Fan, Keyu Chen, Ruilong Xing, Yulin Li, Li Jiang, Zhuotao Tian
arXiv: 2602.08024v1
PDF: https://arxiv.org/pdf/2602.08024v1
源码: https://arxiv.org/src/2602.08024v1
代码仓库: https://github.com/Fanziyang-v/FlashVID
---
## 2) Executive summary
- 目标: 在不训练（training-free）的前提下，压缩 VLLM 的视觉 token，降低 prefilling/TTFT 成本，同时尽量不掉点。
- 核心观点: 视频冗余不是“同一空间位置跨帧重复”这么简单；时空冗余是耦合的，物体会运动、变形、尺度变化。
- 方法: 两阶段压缩。
  - ADTS（Attention + Diversity Token Selection）先保留“信息量高且多样”的 token。
  - TSTM（Tree-based Spatiotemporal Token Merging）再用跨帧树结构合并冗余 token。
- 主结果: 在 LLaVA-OneVision 上仅保留 10% 视觉 token 时，相对精度仍有 99.1%；在固定算力预算下可让 Qwen2.5-VL 从 16 帧扩到 160 帧（10x），平均分相对提升到 108.6%。

## 3) Core technical ideas
### 3.1 ADTS: 先选“代表性+多样性” token
- 把每帧 token 选择建模为 Max-Min Diversity Problem（MMDP）。
- 基础目标是保持 token 间最小距离尽可能大（避免都选相似区域）。
- 再用两类校准信号增强“重要性”:
  - [CLS] attention（或无 CLS 编码器下的等价 attention 统计）
  - event relevance（token 与视频事件上下文相关性）
- 这样 ADTS 不只“分散取样”，还能偏向关键语义区域。

### 3.2 TSTM: 用树建模时空冗余
- 对相邻帧 token 做两两相似度计算。
- 每个 token 连接到上一帧最相似 token（相似度超过阈值才连接）。
- 逐帧形成“时空冗余树”，每棵树聚合成一个代表 token（如 mean pooling）。
- 与传统 TTM（固定空间位置对齐）相比，TSTM 更适配运动场景。

### 3.3 混合压缩（before-LLM + inner-LLM）
- 作者不是只做 pre-LLM 压缩，还在 LLM 内部高层做 pruning（K=20）。
- 通过 token budget alignment 保证不同方法对比时算力预算一致。

## 4) Evidence and results
### 4.1 LLaVA-OneVision（主表）
- Vanilla 平均分: 58.4。
- FlashVID:
  - R=25%: 58.6（100.3% rel. acc）
  - R=20%: 58.7（100.5% rel. acc）
  - R=15%: 58.5（100.2% rel. acc）
  - R=10%: 57.9（99.1% rel. acc）
- 观察: 在中高保留率下出现“less is more”（超过 vanilla）。

### 4.2 LLaVA-Video
- Vanilla 平均分: 60.7。
- FlashVID:
  - R=20%: 59.3（97.7%）
  - R=10%: 58.2（95.9%）
- 在同 retention 下整体优于 FastV / VisionZip / FastVID。

### 4.3 Qwen2.5-VL
- Vanilla 平均分: 61.6。
- FlashVID:
  - R=20%: 60.2（97.7%）
  - R=10%: 58.9（95.6%）

### 4.4 固定预算下扩帧（关键）
- 基线: Qwen2.5-VL 16 帧，平均分 52.6。
- FlashVID:
  - 80 帧（5x）@R=20%: 56.2（106.8%）
  - 160 帧（10x）@R=10%: 57.1（108.6%）
- 结论: 压缩换长时序上下文，收益显著。

### 4.5 效率
- LLaVA-OneVision 上（单 A100）:
  - Vanilla prefill: 1220.8ms，TTFT: 2005.8ms
  - FastVID(25%): prefill 301.8ms（4.0x），TTFT 1086.8ms（1.8x）
  - FlashVID(10%): prefill 193.3ms（6.3x），TTFT 978.3ms（2.1x）
- 同时 FlashVID 的相对精度（99.1%）高于 FastVID（98.5%）。

## 5) Limitations and caveats
- 论文展示了 TSTM 失败案例: 语义相近但实体不同时，可能被错误合并。
- TSTM 依赖相似度阈值，分布变化（新域视频）下阈值稳健性需要额外验证。
- 方法强调 training-free，但工程复杂度不低（分段、ADTS、TSTM、inner-LLM pruning 组合）。
- “less is more” 可能与特定模型和数据分布相关，不一定普适。

## 6) Relevance to Video Understanding
- 对视频问答/长视频理解直接相关，尤其适合“算力固定但希望看更多帧”的场景。
- 对 InternVL/LLaVA-NeXT/Qwen2.5-VL 这类框架都具备迁移潜力（论文已跨 3 类 VLLM 验证）。
- 若当前瓶颈在 prefilling + KV cache 压力，此类 pre-LLM 压缩收益大于纯解码优化。

## 7) Concrete experiments for this project
1. 扩帧收益曲线
- 目标: 验证“压缩换时长”在你数据上的拐点。
- 设计: 固定总 token budget，比较 (16, 32, 64, 128, 160 帧)；每个帧数配对应 retention。
- 输出: accuracy/latency/TTFT 三维 Pareto 曲线。

2. 模块拆分消融（可快速做）
- 组别: 仅 ADTS、仅 TSTM、ADTS+TSTM。
- 关注: 细粒度动作题、时序因果题是否更依赖 TSTM。

3. 失败样本归因
- 对错误样本统计“错误合并”比例：
  - 不同实体被并到同树
  - 快速运动/遮挡场景下的误合并
- 输出: 可视化+错误类型占比，决定是否引入实体一致性约束。

4. 轻量鲁棒性改造（低成本）
- 在 TSTM 连接规则中加上双向一致性或 top-k mutual match 约束。
- 比较是否减少语义混淆合并。

## 8) Risks, unknowns, follow-up reading
- 未知点:
  - 在超长视频（>160 帧）和高动态 egocentric 视频上的稳定性。
  - 对不同视觉编码器（如 SigLIP 变体）的通用性边界。
- 实施风险:
  - token budget 对齐若处理不严，方法间对比会失真。
  - 压缩本身耗时不能过高，否则吞掉一部分 LLM 加速收益。
- 建议后续阅读:
  - FastVID（NeurIPS 2025）
  - PruneVID（ACL 2025）
  - VisionZip（CVPR 2025）
  - ToMe / DivPrune（理解树合并与多样性选择的理论基础）
