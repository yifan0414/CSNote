---
创建时间: 2026-05-25 03:51
tags:
---
对。可以借鉴内部 Video-LLM，但要把它们“翻译”为外置、免训练、黑盒兼容的版本。关键原则是：**别只是选帧 + top-k token，要做分层 memory、全局预算、跨帧冗余建模和位置保护。**

我建议优先做这 5 个模块：

1. **Segment Memory，不是直接喂散帧**

内部模型现在常做 hierarchical compression。VideoChat-Flash 的 HiCo 就是 clip-level 到 video-level 的分层压缩；Video-XL 也给每个 video interval 引入视觉摘要 token。外置版本可以这样做：

```text
每 8/16 个采样帧 -> 一个 segment
segment 内选 1-2 个 evidence frame
segment 额外产生少量 memory tokens:
  - mean/cluster pooled visual tokens
  - high-change residual tokens
  - representative background token
最后输入:
  [segment memory tokens] + [少量关键帧细节 tokens]
```

这比 KTV 的 “6 张关键帧独立 token pruning” 更像 video representation。它保留了长视频全局结构，也不需要训练 summary token。参考 VideoChat-Flash 的层次压缩和 Video-XL 的 interval summary 思路。([VideoChat-Flash](https://arxiv.org/abs/2501.00574), [Video-XL](https://arxiv.org/abs/2409.14485))

2. **Temporal EMA Memory 做预算分配**

不要每帧单独算 novelty。内部/近年方法明显在做 memory：DynaTok 用 EMA memory 给新颖帧更多 token、冗余帧更少 token；空间上也用 memory 避免反复选同一位置。这个很适合外置实现。([DynaTok](https://arxiv.org/abs/2605.19322))

外置版本：

```text
memory_t = EMA(previous selected frame features)

frame_score =
  novelty_to_memory
+ local_transition
+ segment_boundary_score
+ patch_diversity
- redundancy_to_memory
```

然后把总 token budget 分给不同帧。你当前代码里 [llava_arch.py](/hdd1_4t/yifan/KTV/ktv/llava/model/llava_arch.py:231) 已经有 `video_intrinsic` budget 入口，可以直接升级成 `video_intrinsic_memory`。

3. **全局 spatiotemporal token pool，不要 per-frame top-k**

KTV 现在基本是每帧内 top-k。这个有个问题：如果某一帧很重要但预算少，它选不到足够 evidence；如果某帧很冗余，仍然会保底选很多。

更好的实现：

```text
把所有 keyframes 的 patch tokens 放进一个 global pool
每个 token 有分数:
  saliency + temporal_residual + novelty - redundancy
全局选 top-B
加约束:
  每个 segment 至少 m 个 token
  每个 selected frame 至少 anchor tokens
  每个空间区域不能过度集中
未选 tokens 聚类成少量 refill/summary tokens
```

这对应内部 Video-LLM 里的 unified spatiotemporal allocation 思路，也能和 per-frame KTV 拉开。2026 的 unified compression 已经明确往这个方向走，所以如果你做，必须强调 **外置、图像模型兼容、question-agnostic、可预计算**。([Unified Spatiotemporal Token Compression](https://arxiv.org/abs/2603.21957))

4. **跨帧 token merging，专门压背景**

DYTO 做 bipartite token merging；DyCoke 也强调跨帧合并冗余 token 和动态 KV cache reduction。([DYTO](https://arxiv.org/abs/2411.14401), [DyCoke](https://openaccess.thecvf.com/content/CVPR2025/html/Tao_DyCoke_Dynamic_Compression_of_Tokens_for_Fast_Video_Large_Language_CVPR_2025_paper.html))

外置 KTV/DYTO 路线里，我建议做得更具体：

```text
对相邻/同 segment frames 的 patch tokens:
  如果 cosine 高 + 位置接近 + 多帧稳定 -> merge 成 background memory token
  如果相似度低或位置变化大 -> 保留为 residual token
```

卖点不要写“token merging”，太泛。写成：

> temporal residual preserving compression

即重复背景合并，变化区域保留。

5. **位置和时间不要压坏**

很多 training-free 压缩掉点，是因为 token 重要性高但位置覆盖很差。Qwen 2.5-VL 这类模型很重视动态 FPS、绝对时间编码、mRoPE 这类时空位置设计。外置压缩虽然不能改 RoPE，但可以保留结构。([Qwen2.5-VL docs](https://huggingface.co/docs/transformers/v4.51.3/en/model_doc/qwen2_5_vl))

实际建议：

```text
每帧固定保留:
  CLS/global token
  2x2 或 3x3 grid anchor tokens
  high-res evidence tokens

每个 segment 固定保留:
  start/middle/end temporal anchor
  boundary memory token
```

同时别把 token 乱序拼接。保持：

```text
segment order -> frame order -> spatial order
```

否则 image LLM 很容易丢时间结构。

**我最建议你现在落地的版本**

做一个 `VIC`：Video-Intrinsic Compressor。

```text
Stage 1: segment-aware frame selection
- dense sample 32/64 frames
- segment into clips
- 每段选 representative + boundary + novelty
- 输出 variable K frames，而不是固定 6

Stage 2: memory-based token compression
- 先算 temporal EMA memory
- 给每帧分配 token budget
- 全局 token pool 选择 residual/salient/diverse tokens
- redundant background tokens merge 成 segment memory tokens
- 保留 temporal/spatial anchors
```

实验路径可以很清楚：

```text
KTV KMeans6 + fixed_rank budget
-> hybrid frame selection
-> video_intrinsic_memory budget
-> global token pool
-> background merge + segment memory
```

最重要的定位是：**内部 Video-LLM 的压缩模块通常依赖训练、attention/KV、特殊 token 或模型结构；你的方法把这些思想外置化，用 DINO/CLIP/vision-tower features 在输入侧完成，仍然能喂给 LLaVA/InternVL/Qwen-VL 这类图像模型。**

![[Pasted image 20260525035731.png]]