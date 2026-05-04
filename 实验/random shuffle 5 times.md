---
创建时间: 2026-04-29 06:24
数据集: EgoSchema
性能: 48.2
git commit:
---

# Random Shuffle 5 Times 实验结果

五轮 shuffle 跑完后，结论比较明确：**全量 5-shuffle majority ensemble 不如 no-shuffle，但它对 `action_local` / `segment_motion` 很有帮助。**

## 整体结果

| 方法                            | Accuracy           |
| :---------------------------- | :----------------- |
| `adaptive_rule`               | `250/500 = 50.00%` |
| `no_single no-shuffle`        | `247/500 = 49.40%` |
| `shuffle5 ensemble`           | `241/500 = 48.20%` |
| `old adaptive_llm gpt4o-mini` | `240/500 = 48.00%` |
| `uniform100`                  | `237/500 = 47.40%` |

五个单独 variant：

| Variant | Accuracy           |
| :------ | :----------------- |
| v0      | `242/500 = 48.40%` |
| v1      | `225/500 = 45.00%` |
| v2      | `238/500 = 47.60%` |
| v3      | `230/500 = 46.00%` |
| v4      | `216/500 = 43.20%` |

多数投票没有把结果救回来，最终为 `241/500 = 48.20%`，比 no-shuffle 少对 `6` 题。

## 按 Route 分析

| Route                   | shuffle5 ensemble  | no-shuffle         |
| :---------------------- | :----------------- | :----------------- |
| `segment_motion`        | `59/106 = 55.66%`  | `50/106 = 47.17%`  |
| `uniform_motion_hybrid` | `8/13 = 61.54%`    | `7/13 = 53.85%`    |
| `uniform`               | `174/381 = 45.67%` | `190/381 = 49.87%` |

关键点：shuffle5 对非 `uniform` route 明显有帮助，但对占比最大的 `uniform` 明显有伤害。

## 按 Question Type 分析

| Type               | shuffle5 ensemble  | no-shuffle         |
| :----------------- | :----------------- | :----------------- |
| `action_local`     | `62/109 = 56.88%`  | `53/109 = 48.62%`  |
| `counting`         | `5/9 = 55.56%`     | `4/9 = 44.44%`     |
| `static_attribute` | `6/9 = 66.67%`     | `5/9 = 55.56%`     |
| `procedure_causal` | `119/274 = 43.43%` | `128/274 = 46.72%` |
| `global_temporal`  | `43/87 = 49.43%`   | `48/87 = 55.17%`   |
| `ambiguous`        | `6/12 = 50.00%`    | `9/12 = 75.00%`    |

> [!idea]+
> 这说明 shuffle ensemble 更适合局部动作类问题，不适合全局/过程类问题。


## 选项偏置变化

shuffle5 后，E 的召回确实有所改善：

| True Option | shuffle5 recall   | no-shuffle recall |
| :---------- | :---------------- | :---------------- |
| B           | `56/108 = 51.85%` | `47/108 = 43.52%` |
| E           | `52/117 = 44.44%` | `43/117 = 36.75%` |
| D           | `39/83 = 46.99%`  | `57/83 = 68.67%`  |

它提升了 B/E，但严重伤害了 D，所以整体准确率下降。

## 投票一致性

| Vote Pattern | 数量  | Accuracy |
| :----------- | :-- | :------- |
| `5-0`        | 158 | `67.72%` |
| `4-1`        | 97  | `48.45%` |
| `3-2`        | 95  | `42.11%` |
| `3-1-1`      | 67  | `38.81%` |
| `2-2-1`      | 62  | `29.03%` |

模型 5 次都同意时很可靠；一旦分歧变大，准确率明显变差。总共有 `63` 个 tie。

## 最重要发现

如果做选择性策略，而不是所有题都用 ensemble：

```text
uniform route 用 no-shuffle
segment_motion / uniform_motion_hybrid 用 shuffle5 ensemble
```

按当前结果可以达到：

```text
257/500 = 51.40%
```

如果按 question type 选择：

```text
action_local / counting / static_attribute 用 shuffle5
其他用 no-shuffle
```

可以达到：

```text
258/500 = 51.60%
```

更激进一点：

```text
非 uniform route 且 vote 最大票数 >= 3 时用 ensemble，否则 no-shuffle
```

当前可到：

```text
261/500 = 52.20%
```

> 这个是探索性后处理结果，不建议直接当严格最终结论，但它给出了明确的优化方向。

## 结论

**不要全量使用 option shuffle ensemble；应该只对 `action_local` / `segment_motion` 这类局部动作问题使用。**

## 下一步

做一个正式的 mixed prediction 脚本：

- `uniform` 走 no-shuffle；
- `segment_motion` / `uniform_motion_hybrid` 走 shuffle5 ensemble；
- 生成一个可复现实验文件。
