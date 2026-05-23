---
数据集:
git commit:
创建时间: 2026-05-18 12:46
tags:
---
我分析了这批 `20260517_135218` 消融结果。15 个实验都完整：每个都是 `500` 条，`budget_trace` 都存在，token sum 也都严格等于 `504/936/1872`。

**总结果**
```text
variant             504        936       1872
fixed            245 49.0   252 50.4   252 50.4
rank_only        251 50.2   257 51.4   247 49.4
rank_novelty     248 49.6   253 50.6   244 48.8
rank_diversity   251 50.2   257 51.4   255 51.0
rank_transition  249 49.8   255 51.0   248 49.6
full             247 49.4   255 51.0   247 49.4
```

**最关键结论**
当前最好的不是 `full`，而是 `rank_diversity`。

`rank_diversity` 在三个 budget 上分别是：

```text
504:  251/500 = 50.2
936:  257/500 = 51.4
1872: 255/500 = 51.0
```

它是唯一一个三个 budget 都不差的 variant。相比 fixed：

```text
504:  +6 samples
936:  +5 samples
1872: +3 samples
```

**组件解释**
`rank_only` 很强，说明原来的 fixed bucket 分配太粗。比如 936 的 fixed 是：

```text
288, 144, 144, 144, 144, 72
```

而 `rank_only` 平均是：

```text
311, 249, 187, 125, 63, 1
```

也就是更强地相信 keyframe rank，尤其压低 rank 5。这在 504/936 上很有效。

但 `rank_only` 到 1872 会掉到 `247/500`，因为它过度集中在高 rank，rank 0 还会大量触顶。`rank_diversity` 在 1872 反而最好，说明帧内 token diversity 能缓解高预算下的过度集中问题。

`rank_novelty` 和 `rank_transition` 不太好：

```text
rank_novelty:    504/936/1872 都弱于 rank_only
rank_transition: 只有 936 还可以，但整体不稳定
full:            被 novelty/transition 拖累
```

所以论文方向上，我建议不要再主推当前 `full`，而是改成：

> Rank-guided token allocation with intra-frame visual diversity.

也就是主方法用 `rank_diversity`，然后把 `rank_only` 作为强 baseline。这样论证会更干净：不是问题相关，不改选帧，只在视觉 token budget 层做有意义的重分配。

下一步最值得做的是扫 `rank + λ * diversity` 的 λ，而不是继续加 novelty/transition。当前 `rank_diversity` 已经说明 diversity 有价值，但权重还没找最优。
