---
title: Video MLLM Profiler 实验模板
tags:
  - video-mllm
  - experiment
  - profiling
type: experiment-template
status: active
created: 2026-08-15
updated: 2026-09-09
---

# Video MLLM Profiler 实验模板

## 导航

- [[05-onevision-trace|OneVision Trace 与 Profiling]]
- [[trace-实验模板|Trace 模板]]
- [[compression-实验模板|Compression 模板]]
- [PyTorch Profiler Recipe](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)

## 运行环境

| 字段 | 值 |
| --- | --- |
| Date |  |
| GPU / driver / CUDA |  |
| PyTorch / Transformers |  |
| Model / revision / dtype |  |
| Input / prompt / seed |  |
| Command / commit |  |
| Power / clock mode |  |

## 测量协议

- [ ] 固定输入、generation 参数与随机种子。
- [ ] 分离 model load、video decode 与 GPU forward。
- [ ] 至少 warmup 3 次，再测量至少 10 次。
- [ ] CUDA Event 计时前后 record，并在读取前 synchronize。
- [ ] 报告 median 与 p90 / min-max，不只报告单次结果。
- [ ] latency benchmark 与 torch.profiler 分开运行。
- [ ] 每个 memory run 前 reset_peak_memory_stats。
- [ ] 记录 `memory_allocated`、`memory_reserved` 与 peak allocated。

## 输入规模

| Frames | Resolution | Tokens / frame | Visual tokens | Text tokens | Output tokens | Batch |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |  |  |

## Latency Breakdown

| Stage | Warmup | Repeats | Median ms | p90 / range | 占比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Decode / preprocess |  |  |  |  |  |
| Host-to-device |  |  |  |  |  |
| Vision tower |  |  |  |  |  |
| Reduction / projector |  |  |  |  |  |
| Packing |  |  |  |  |  |
| LLM prefill |  |  |  |  |  |
| Decode first token |  |  |  |  |  |
| Decode per token |  |  |  |  |  |
| End-to-end |  |  |  |  |  |

## Memory

| Checkpoint | Allocated MiB | Reserved MiB | Peak allocated MiB | 说明 |
| --- | ---: | ---: | ---: | --- |
| Model loaded |  |  |  |  |
| Processor output on GPU |  |  |  |  |
| Vision complete |  |  |  |  |
| Prefill complete |  |  |  |  |
| Generation complete |  |  |  |  |

## KV Cache 估算

$$
\mathrm{bytes}\approx
2LBH_{kv}Nd_h\times\mathrm{dtype\ bytes}
$$

| $L$ | $B$ | $H_{kv}$ | $N$ | $d_h$ | dtype bytes | Estimated MiB | Measured delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |  |  |  |

## Profiler 摘要

| Operator / kernel | CPU total | CUDA total | Calls | Input shape | Memory | 判断 |
| --- | ---: | ---: | ---: | --- | ---: | --- |
|  |  |  |  |  |  |  |

- [ ] 导出 Chrome / TensorBoard trace，并记录文件名。
- [ ] 检查是否有隐式 CPU-GPU synchronization。
- [ ] 检查 dtype conversion、copy、padding 与小 kernel 开销。
- [ ] 区分 compute-bound、memory-bound 与 launch-bound 段。

## 结论

- [ ] 最大 latency stage 是什么？
- [ ] 最大 peak-memory 来源是什么？
- [ ] Token 减少的理论收益与实测收益差多少？
- [ ] 瓶颈是否转移到 preprocess、vision、prefill 或 decode？
- [ ] 下一轮实验只改变哪个变量？
