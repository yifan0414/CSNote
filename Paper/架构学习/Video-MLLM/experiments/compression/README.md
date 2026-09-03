---
title: Video MLLM Compression 实验模板
tags:
  - video-mllm
  - experiment
  - token-compression
type: experiment-template
status: active
created: 2026-08-15
updated: 2026-08-15
---

# Video MLLM Compression 实验模板

## 导航

- [[Paper/架构学习/Video-MLLM/06-compression-map|Compression Map]]
- [[Paper/架构学习/Video-MLLM/experiments/traces/README|Trace 模板]]
- [[Paper/架构学习/Video-MLLM/experiments/profiler/README|Profiler 模板]]

## 实验问题

| 字段 | 值 |
| --- | --- |
| Hypothesis |  |
| Compression position |  |
| Baseline method |  |
| Proposed / comparison method |  |
| Fixed budget |  |
| Quality metric |  |
| System metric |  |

## 可复现设置

| 字段 | 值 |
| --- | --- |
| Model / revision |  |
| Code commit / patch |  |
| Video / SHA-256 |  |
| Questions / labels |  |
| Frames / resolution |  |
| Prompt / generation config |  |
| Hardware / dtype |  |
| Seed |  |

## 方法定义

| 项目 | 记录 |
| --- | --- |
| Input token semantics |  |
| Selection / merge signal |  |
| $N_{before}\rightarrow N_{after}$ |  |
| Per-frame / global budget |  |
| Query-aware or query-free |  |
| Training required |  |
| Special token handling |  |
| Position handling |  |
| Added operator cost |  |

## 公平性检查

- [ ] 所有方法使用同一视频、问题、checkpoint 与 generation 参数。
- [ ] 最终 visual token budget 相同或明确报告差异。
- [ ] Frame、resolution 与 text length 等非研究变量固定。
- [ ] 不使用 answer / label 泄漏，除非实验明确研究 oracle upper bound。
- [ ] 同时报告 compression overhead 与端到端时间。
- [ ] 质量评估包含需要时间、空间和细节证据的问题。

## 结果

| Run | Position | Frames | $N_{before}$ | $N_{after}$ | Overhead ms | Vision ms | Prefill ms | Peak MiB | Quality |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | None |  |  |  | 0 |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

## Token 保留分析

| Frame / region | Baseline evidence | Retained? | Score / merge target | Failure mode |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 结论

- [ ] 压缩实际节省了哪些 stage？
- [ ] 哪些理论收益没有转化为端到端收益，原因是什么？
- [ ] 失败来自 frame、patch、位置、packing 还是 LLM 推理？
- [ ] 与同预算 baseline 相比，质量差异是否稳定？
- [ ] 下一轮应该改变位置、信号还是预算？

