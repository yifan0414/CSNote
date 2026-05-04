---
创建时间: 2026-04-28 20:30
数据集: EgoSchema
性能: 48
git commit:
---
我按当前完整的 [egoschema_pred_adaptive_llm.json](/hdd1_4t/yifan/DYTO-main/outputs/artifacts/egoschema_adaptive_llm/egoschema_pred_adaptive_llm.json) 重新算了，已经是 `500/500` 条，后台推理也不在跑了。

**总体结果**

`adaptive_llm`: `240 / 500 = 48.00%`

和已有结果对比：

| 方法                         | 正确率             |
| ---------------------------- | ------------------:|
| `egoschema_adaptive` 规则版   | `250/500 = 50.00%` |
| `adaptive_llm`                | `240/500 = 48.00%` |
| 之前 100 帧 uniform           | `237/500 = 47.40%` |
| `uniform_motion_hybrid`       | `233/500 = 46.60%` |

**按 Route 分**

| route / frame_selection                            | 样本数 | 正确数 |      正确率 |
| -------------------------------------------------- | --: | --: | -------: |
| `uniform` （因为 llm 提前做了 route，对于非常典型的问题才会用 uniform） |  69 |  45 | `65.22%` |
| `segment_motion`                                   | 104 |  58 | `55.77%` |
| `single_frame`                                     |  11 |   5 | `45.45%` |
| `uniform_motion_hybrid`                            | 316 | 132 | `41.77%` |

主要瓶颈是 `uniform_motion_hybrid`：它占了 `316/500 = 63.2%` 的样本，但正确率只有 `41.77%`，直接拉低整体结果。

**按问题类型分**

| question_type       | 样本数 | 正确数 | 正确率   |
| ------------------- | -----: | -----: | -------: |
| `global_temporal`   |     65 |     43 | `66.15%` |
| `action_local`      |    104 |     58 | `55.77%` |
| `ambiguous`         |      4 |      2 | `50.00%` |
| `static_attribute`  |     11 |      5 | `45.45%` |
| `procedure_causal`  |    298 |    126 | `42.28%` |
| `counting`          |     18 |      6 | `33.33%` |

这里也能看到问题集中在 `procedure_causal` 和 `counting`。LLM router 大量把样本分到 `procedure_causal -> uniform_motion_hybrid, 64 frames`，但这个组合表现一般。

**按实际帧数分**

| num_frames_used | 样本数 | 正确数 | 正确率   |
| --------------: | -----: | -----: | -------: |
|              64 |    367 |    171 | `46.59%` |
|              48 |    104 |     58 | `55.77%` |
|              96 |     18 |      6 | `33.33%` |
|               1 |     11 |      5 | `45.45%` |

结论：`adaptive_llm` 最终是 `48.00%`，略高于 100 帧 uniform 的 `47.40%` 和 `uniform_motion_hybrid` 的 `46.60%`，但低于规则版 `adaptive` 的 `50.00%`。当前 LLM 路由真正有效的是 `global_temporal -> uniform` 和 `action_local -> segment_motion`；主要需要优化的是 `procedure_causal/counting` 这两类的路由策略或帧数预算。
