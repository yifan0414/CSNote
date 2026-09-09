---
title: Video MLLM Trace 实验模板
tags:
  - video-mllm
  - experiment
  - trace
type: experiment-template
status: active
created: 2026-08-15
updated: 2026-09-09
---

# Video MLLM Trace 实验模板

## 导航

- [[00-shape-cheatsheet|Shape Cheatsheet]]
- [[05-onevision-trace|OneVision Trace]]
- [[profiler-实验模板|Profiler 模板]]

## 实验身份

| 字段 | 值 |
| --- | --- |
| Date |  |
| Model / checkpoint |  |
| Revision / commit |  |
| Framework versions |  |
| Device / dtype |  |
| Input asset / SHA-256 |  |
| Prompt |  |
| Script / command |  |
| Random seed |  |

## 配置快照

| 项目 | 值 |
| --- | --- |
| Vision image / patch size |  |
| Vision hidden / layers / heads |  |
| Feature layer / selection strategy |  |
| Projector type |  |
| LLM hidden / layers / Q heads / KV heads |  |
| Max frames / sampling rule |  |
| Generation parameters |  |

## Forward Trace

| # | Module / stage | Input shape | Output shape | dtype | device | $N$ 变化原因 | Source location |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Decode / sample |  |  |  |  |  |  |
| 2 | Processor |  |  |  |  |  |  |
| 3 | Patch embedding |  |  |  |  |  |  |
| 4 | Vision early block |  |  |  |  |  |  |
| 5 | Selected vision feature |  |  |  |  |  |  |
| 6 | Spatial reduction |  |  |  |  |  |  |
| 7 | Projector |  |  |  |  |  |  |
| 8 | Visual token packing |  |  |  |  |  |  |
| 9 | Text embeddings |  |  |  |  |  |  |
| 10 | LLM inputs_embeds |  |  |  |  |  |  |
| 11 | Prefill output / KV |  |  |  |  |  |  |
| 12 | Decode step |  |  |  |  |  |  |

## Token Layout

| Span | Start | End | Count | 含义 |
| --- | ---: | ---: | ---: | --- |
| System / user text |  |  |  |  |
| Frame 0 |  |  |  |  |
| Frame 1 |  |  |  |  |
| Frame delimiters / newline |  |  |  |  |
| Assistant prefix |  |  |  |  |

## Mask 与 Position

- [ ] 保存 attention_mask shape 与有效 token 数。
- [ ] 保存 position_ids / cache_position shape 和首尾值。
- [ ] 检查 padding side 与 padding token。
- [ ] 检查 image / video special token 的展开位置。
- [ ] 检查 generation 第一步与后续步骤的输入长度。

## Hook 检查

- [ ] Hook 没有修改 tensor 或破坏 autograd / cache。
- [ ] 对 tuple / dataclass 输出取到正确字段。
- [ ] Batch、frame 与 head 维没有因 reshape 被误读。
- [ ] 记录 config 与真实 shape 的差异。
- [ ] 对关键节点保存最小可复现输出。

## 结论

- [ ] Token 在哪里产生？
- [ ] $N$ 在哪些位置变化，为什么？
- [ ] 模态在哪里融合？
- [ ] 哪些位置可插入压缩？
- [ ] 各位置能节省哪些计算，可能损失什么？

