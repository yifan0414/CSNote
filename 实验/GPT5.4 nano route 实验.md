---
创建时间: 2026-04-28 22:37
数据集: EgoSchema
性能: 49.2
git commit:
---
**总体**

`GPT-5.4-nano routing adaptive_llm`: `246 / 500 = 49.20%`

对比已有结果：

| 方法                          | 正确率                |
| :-------------------------- | :----------------- |
| `adaptive_rule`             | `250/500 = 50.00%` |
| `adaptive_llm_gpt54_nano`   | `246/500 = 49.20%` |
| 旧 `adaptive_llm_gpt4o-mini` | `240/500 = 48.00%` |
| `uniform100`                | `237/500 = 47.40%` |
| `uniform_motion_hybrid100`  | `233/500 = 46.60%` |

所以这版比旧 LLM routing 提升 `+6` 题，比 100 帧 uniform 提升 `+9` 题，但还比规则版 adaptive 少 `4` 题。

**按 Route**

| route                   | 样本数 | 正确数 | 正确率      |
| :---------------------- | :-- | :-- | :------- |
| `uniform`               | 372 | 185 | `49.73%` |
| `uniform_motion_hybrid` | 14  | 7   | `50.00%` |
| `single_frame`          | 8   | 4   | `50.00%` |
| `segment_motion`        | 106 | 50  | `47.17%` |

这里最意外的是 `segment_motion` 没有表现好。按同一批 `segment_motion` ID 对齐，规则版 adaptive / fixed segment_motion run 1 是 `54/106 = 50.94%`，而这次只有 `50/106 = 47.17%`。

**按 Question Type**

|   question_type    | 样本数 | 正确数 |   正确率    |
| :----------------: | :-: | :-: | :------: |
| `global_temporal`  | 87  | 48  | `55.17%` |
|    `ambiguous`     | 12  |  9  | `75.00%` |
| `procedure_causal` | 274 | 128 | `46.72%` |
|   `action_local`   | 109 | 53  | `48.62%` |
|     `counting`     |  9  |  4  | `44.44%` |
| `static_attribute` |  9  |  4  | `44.44%` |

我们之前把 `procedure_causal -> uniform` 的方向是有效的：这版 `procedure_causal` 在自己的 274 条上是 `128/274 = 46.72%`，旧 LLM 在同一批题上是 `125/274 = 45.62%`，`uniform100` 是 `120/274 = 43.80%`。

**主要结论**

这版提升主要来自 `procedure_causal` 改走 `uniform`，方向是对的。  
但是 `action_local/segment_motion` 这部分偏弱，拖住了它超过规则版 adaptive。规则版在新 cache 的 `action_local` 这 109 条上有 `57/109 = 52.29%`，这版是 `53/109 = 48.62%`。

还有一个偏置值得注意：

| 选项  | 预测次数 | GT 次数 | 预测该项时正确率 |
| :-: | :--: | :---: | :------: |
|  A  | 131  |  101  | `35.88%` |
|  B  |  87  |  108  | `54.02%` |
|  C  | 114  |  91   | `46.49%` |
|  D  | 109  |  83   | `51.38%` |
|  E  |  59  |  117  | `72.88%` |

模型明显少选 `E`，多选 `A`；这不是 route 本身能完全解决的问题，更像底层 VLM 的答案偏置。

**建议**

这版可以作为目前最好的 LLM routing 结果保留。下一步如果想冲过 `50%`，我会优先改 `action_local` 的 prompt/route 判定，而不是再动 `procedure_causal`。`procedure_causal -> uniform` 已经比旧方向更合理；真正的短板现在变成了 `segment_motion/action_local`。
