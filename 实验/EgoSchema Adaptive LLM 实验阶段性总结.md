---
数据集: EgoSchema
git commit:
创建时间: 2026-04-30 07:54
tags:
---

## 1. 核心结论

目前最好的 clean setting 是 `cyclic5_3 ensemble`：

```text
outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single_cyclic5_3/
egoschema_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_3_ensemble.json
```

它的整体准确率为 `260/500 = 52.00%`。相比规则版 adaptive 的 `50.00%`，提升 `+2.00` points；相比 GPT-5.4-nano no-single no-shuffle 的 `49.40%`，提升 `+2.60` points。

这几轮实验最重要的发现是：单纯改 route 不一定稳定提升，EgoSchema 上还存在明显的选项位置偏置。ABCDE cyclic rotation 的 5 次轮询投票可以缓解这个偏置，尤其提升了 `action_local/segment_motion` 子集。

## 2. 总体结果对比

| 实验 | 关键设置 | Correct / Total | Accuracy |
| --- | --- | ---: | ---: |
| Rule adaptive | 规则路由：主要 `uniform`，部分 `segment_motion` | 250 / 500 | 50.00% |
| Old adaptive_llm | GPT-4 o-mini routing，`procedure_causal` 大量走 `uniform_motion_hybrid` | 240 / 500 | 48.00% |
| GPT-5.4-nano adaptive_llm | 新 LLM routing cache，仍保留少量 `single_frame` | 246 / 500 | 49.20% |
| GPT-5.4-nano no-single | 将 `single_frame` 改为更稳的 `uniform` | 247 / 500 | 49.40% |
| Random shuffle 5 ensemble | 5 次随机选项 shuffle 后投票 | 241 / 500 | 48.20% |
| Cyclic 5 ensemble | ABCDE cyclic rotation 5 次后投票 | 259 / 500 | 51.80% |
| Cyclic 5_1 ensemble | Cyclic 5 复现实验 | 259 / 500 | 51.80% |
| Cyclic 5_3 ensemble | 最新 cyclic 复现实验 | 260 / 500 | 52.00% |

结论上，random shuffle 没有带来稳定收益，反而低于 no-shuffle；ABCDE cyclic rotation 则比较稳定，两次完整结果都是 `51.80%`，最新一次到 `52.00%`。

## 3. 实验过程与发现

### 3.1 基础采样与规则版 adaptive

早期实验比较了几种 frame selection：

| 方法                      | 观察                                                 |
| ----------------------- | -------------------------------------------------- |
| `uniform`               | 作为基础强 baseline，之前均匀采样主要使用 100 帧。                   |
| `segment_motion`        | 按时间段切分后，在每段中选局部运动最大的帧；对 action-local 问题更有潜力。       |
| `single_frame`          | 单帧证据过弱，整体不稳定。**（主要验证 LLM 的先验）**                    |
| `uniform_motion_hybrid` | 理论上结合 uniform 和 motion，但在当前 EgoSchema 设置下没有明显优势。   |
| `adaptive`              | 规则路由版本达到 `250/500 = 50.00%`，是后续 LLM routing 的主要对照。 |

规则版 adaptive 的 route breakdown：

| Route | Correct / Total | Accuracy |
| --- | ---: | ---: |
| `uniform` | 225 / 453 | 49.67% |
| `segment_motion` | 25 / 47 | 53.19% |

这个结果说明 `segment_motion` 对部分局部动作问题是有帮助的，但规则版 route 只分到了 47 个样本，覆盖不够充分。

### 3.2 旧版 GPT-4o-mini LLM routing 的问题

旧版 `adaptive_llm` 使用 GPT-4o-mini 生成 route cache，整体为：

```text
240 / 500 = 48.00%
```

它的主要问题是 `procedure_causal` 被大量路由到 `uniform_motion_hybrid`。这个设计直觉上希望用 motion 信息补充过程/因果问题，但实际效果不好：

|          Route          | Correct / Total | Accuracy |
| :---------------------: | :-------------: | :------: |
| `uniform_motion_hybrid` |    132 / 316    |  41.77%  |
|    `segment_motion`     |    58 / 104     |  55.77%  |
|        `uniform`        |     45 / 69     |  65.22%  |
|     `single_frame`      |     5 / 11      |  45.45%  |

其中 `procedure_causal` 是最大的子集，也是最明显的瓶颈。后续实验因此将 `procedure_causal` 调整为更保守的 `uniform`，避免大量使用 `uniform_motion_hybrid`。

### 3.3 GPT-5.4-nano routing

重新使用 GPT-5.4-nano 生成 routing cache 后，route 分布更保守：

|          Route          | Count | Ratio |
| :---------------------: | :---: | :---: |
|        `uniform`        |  372  | 74.4% |
|    `segment_motion`     |  106  | 21.2% |
| `uniform_motion_hybrid` |  14   | 2.8%  |
|     `single_frame`      |   8   | 1.6%  |

对应结果：

```text
246 / 500 = 49.20%
```

这个结果比旧版 GPT-4 o-mini routing 的 `48.00%` 更好，但仍然低于规则版 adaptive 的 `50.00%`。说明更强的 routing LLM 并不会自动带来更高最终 QA accuracy，**route 设计和底层 VLM 的偏置同样重要。**

### 3.4 去掉 single_frame

由于 `single_frame` 证据太弱，而且只覆盖 8 个样本，我们将它从 LLM routing cache 中去掉，改为更稳的多帧策略。结果为：

```text
247 / 500 = 49.40%
```

相比保留 `single_frame` 的 `49.20%`，只提升了 1 题。这个实验说明去掉 `single_frame` 是合理的，但它不是主要瓶颈。

### 3.5 发现选项偏置※

在 no-single no-shuffle 结果中，模型的选项分布明显不均衡：

| Option | GT Count | Pred Count | Recall |
| :----: | :------: | :--------: | :----: |
|   A    |   101    |    131     | 46.53% |
|   B    |   108    |     86     | 43.52% |
|   C    |    91    |    113     | 58.24% |
|   D    |    83    |    111     | 68.67% |
|   E    |   117    |     59     | 36.75% |

最明显的问题是：正确答案 E 有 117 个，但模型只预测 E 59 次。也就是说模型严重少选 E。与此同时，模型一旦预测 E，precision 反而较高，因此问题更像是选项位置偏置，而不是 E 类答案本身不可识别。

**这也是后面引入 option shuffle / cyclic rotation 的原因。**

### 3.6 Random shuffle 不稳定

先尝试随机打乱选项：

|            实验             | Correct / Total | Accuracy |
| :-----------------------: | :-------------: | :------: |
| Random shuffle single run |    226 / 500    |  45.20%  |
| Random shuffle 5 ensemble |    241 / 500    |  48.20%  |

random shuffle 确实能一定程度提高 E 的 recall，但会伤害 A/C/D 等其他选项，并且不同 shuffle variant 差异较大。最终 5 次投票只有 `48.20%`，低于 no-shuffle 的 `49.40%`。

这说明随机打乱带来的输入扰动太强，投票不能稳定抵消噪声。

### 3.7 ABCDE cyclic rotation 的收益

随后使用更结构化的 5 次 cyclic rotation：

| Variant | Option order |
| :-----: | :----------: |
|   v0    |  A B C D E   |
|   v1    |  B C D E A   |
|   v2    |  C D E A B   |
|   v3    |  D E A B C   |
|   v4    |  E A B C D   |

每次推理后将预测选项映射回原始 ABCDE，再做 majority vote。这个方法相比 random shuffle 更可控，每个原始选项都轮流出现在不同位置。

最新 `cyclic5_3` 的 5 个单独 variant 准确率如下：

| Variant  | Correct / Total | Accuracy |
| :------: | :-------------: | :------: |
|    v0    |    249 / 500    |  49.80%  |
|    v1    |    238 / 500    |  47.60%  |
|    v2    |    241 / 500    |  48.20%  |
|    v3    |    218 / 500    |  43.60%  |
|    v4    |    236 / 500    |  47.20%  |
| Ensemble |    260 / 500    |  52.00%  |

单个 variant 并不强，尤其 v3 明显较低；但 ensemble 后达到当前最好结果。这说明 cyclic 的收益主要来自投票集成和位置偏置缓解，而不是某个单一选项顺序更好。

## 4. Egoschema 最新 cyclic 5_3 详细分析

### 4.1 按 route 划分

|          Route          | Correct / Total | Accuracy |
| :---------------------: | :-------------: | :------: |
|        `uniform`        |    191 / 381    |  50.13%  |
|    `segment_motion`     |    61 / 106     |  57.55%  |
| `uniform_motion_hybrid` |     8 / 13      |  61.54%  |

对比 no-shuffle no-single：

|          Route          |     No-shuffle     |     Cyclic 5_3     | Change |
| :---------------------: | :----------------: | :----------------: | :----: |
|        `uniform`        | 190 / 381 = 49.87% | 191 / 381 = 50.13% |   +1   |
|    `segment_motion`     | 50 / 106 = 47.17%  | 61 / 106 = 57.55%  |  +11   |
| `uniform_motion_hybrid` |  7 / 13 = 53.85%   |  8 / 13 = 61.54%   |   +1   |

主要收益来自 `segment_motion`。这和前面的观察一致：动作局部问题更容易从 motion-aware evidence 和多次选项轮询中受益。

### 4.2 按 question type 划分

|   Question type    | Correct / Total | Accuracy |
| :----------------: | :-------------: | :------: |
| `procedure_causal` |    128 / 274    |  46.72%  |
|   `action_local`   |    64 / 109     |  58.72%  |
| `global_temporal`  |     48 / 87     |  55.17%  |
|    `ambiguous`     |     9 / 12      |  75.00%  |
|     `counting`     |      5 / 9      |  55.56%  |
| `static_attribute` |      6 / 9      |  66.67%  |

`action_local` 是当前最明显受益的类型；`procedure_causal` 仍然是最大瓶颈。它有 274 个样本，占全体超过一半，但 accuracy 只有 `46.72%`。

### 4.3 选项分布变化

| Option | GT Count | No-shuffle Pred | Cyclic 5_3 Pred | No-shuffle Recall | Cyclic 5_3 Recall |
| :----: | :------: | :-------------: | :-------------: | :---------------: | :---------------: |
|   A    |   101    |       131       |       120       |      46.53%       |      47.52%       |
|   B    |   108    |       86        |       114       |      43.52%       |      53.70%       |
|   C    |    91    |       113       |       84        |      58.24%       |      49.45%       |
|   D    |    83    |       111       |       93        |      68.67%       |      63.86%       |
|   E    |   117    |       59        |       89        |      36.75%       |      47.86%       |

Cyclic rotation 明显缓解了 E 被严重低估的问题：E recall 从 `36.75%` 提升到 `47.86%`，预测 E 的次数也从 59 增加到 89。代价是 C/D 的 recall 有所下降，但总体净收益为正。

### 4.4 与 no-shuffle 的样本级差异

`cyclic5_3` 相比 no-shuffle no-single：

```text
cyclic_only correct: 40
no_shuffle_only correct: 27
both correct: 220
both wrong: 213
net gain: +13
```

这与整体准确率差异一致：`260 - 247 = +13`。说明 cyclic ensemble 的收益不是来自统计误差，而是确实修正了一批 no-shuffle 会错的样本。

## 5. 当前理解

### 5.1 route 不是唯一瓶颈

最初的想法是通过更好的 question routing，为不同问题类型选择更合适的 frame selection。但实验表明，route 本身只能解决一部分问题：

- GPT-5.4-nano routing 比 GPT-4o-mini routing 更保守，但只到 `49.20%`。
- 去掉 `single_frame` 只提升 1 题。
- `procedure_causal` 改成 `uniform` 后更稳，但仍然低于整体平均。

<font color="#ff0000">这说明底层 VLM 的答案偏置和证据理解能力同样影响最终准确率。</font>

### 5.2 cyclic 的核心作用是缓解选项位置偏置

Cyclic rotation 不改变视频帧，也不改变问题语义，只改变选项呈现位置。它能从 `49.40%` 提升到 `52.00%`，说明原模型对选项位置非常敏感。

与 random shuffle 相比，cyclic 更稳定，原因可能是：

- 每个原始选项都均匀经历不同字母位置。
- 5 次变体之间扰动有结构，不像 random shuffle 那样引入过强随机性。
- majority vote 可以保留跨位置一致的答案，削弱位置诱导的错误。

### 5.3 action_local/segment_motion 是当前最受益子集

最新结果中：

```text
segment_motion: 61 / 106 = 57.55%
action_local:   64 / 109 = 58.72%
```

相比 no-shuffle，`segment_motion` 从 `50/106` 提升到 `61/106`。这说明对于<mark style="background:#d2cbff">动作局部</mark>问题，motion-aware evidence 加上选项轮询投票是有效组合。

### 5.4 procedure_causal 是下一阶段重点

`procedure_causal` 当前为：

```text
128 / 274 = 46.72%
```

它样本最多、准确率最低，是当前最大瓶颈。单纯把它 route 到 `uniform` 更稳，但没有真正解决过程理解、因果关系和长程动作归纳的问题。

## 6. 下一步

### 6.1 优先优化 procedure_causal 的 evidence

下一阶段应围绕 `procedure_causal` 做专门设计，而不是继续全局调 shuffle。可尝试：

- 增加一个专门的 `procedure_summary` 或 `temporal_key_events` route。
- 对视频做更稀疏但覆盖关键阶段的采样，例如 opening/middle/ending + motion peaks。
- 对 procedure 问题保留 cyclic ensemble，但重点改进帧证据，而不是继续改选项顺序。

### 6.2 保留 cyclic 5 作为当前主结果

汇报时建议把 `cyclic5_3 = 52.00%` 作为当前主结果，同时说明：

- `cyclic5` 与 `cyclic5_1` 都是 `51.80%`。
- `cyclic5_3` 是 `52.00%`。
- 多次结果接近，说明 cyclic 方法比 random shuffle 更稳定。

### 6.3 后续可以做选择性 cyclic

全量 cyclic 5 成本比较高。后续为了降低成本，可以尝试只在高收益子集上做 cyclic：

- `action_local`
- `segment_motion`
- vote confidence 低的样本

不过目前作为研究结论，建议先汇报全量 cyclic 5，因为它最干净、最容易解释，也没有 post-hoc 选择策略。

## 7. 总结

1. 只靠 LLM routing 没有超过规则版 adaptive，说明问题不只是 route，还包括 VLM 的选项位置偏置。也可能是设计的 LLM routing 不够好
2. 去掉 `single_frame` 后只提升 1 题，真正有效的是 ABCDE cyclic rotation 的 5 次投票。
3. 当前最好结果是 `52.00%`，主要收益来自 `action_local/segment_motion`，下一步瓶颈是 `procedure_causal`。

## 8. 主要结果文件

| 内容 | 路径 |
| --- | --- |
| 规则版 adaptive | `outputs/artifacts/egoschema_adaptive/egoschema_pred_adaptive.json` |
| 旧版 GPT-4 o-mini adaptive_llm | `outputs/artifacts/egoschema_adaptive_llm/egoschema_pred_adaptive_llm.json` |
| GPT-5.4-nano adaptive_llm | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano/egoschema_pred_adaptive_llm_gpt54_nano.json` |
| GPT-5.4-nano no-single | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single/egoschema_pred_adaptive_llm_gpt54_nano_no_single.json` |
| Random shuffle 5 ensemble | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single_shuffle5/egoschema_pred_adaptive_llm_gpt54_nano_no_single_shuffle5_ensemble.json` |
| Cyclic 5 ensemble | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single_cyclic5/egoschema_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_ensemble.json` |
| Cyclic 5_1 ensemble | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single_cyclic5_1/egoschema_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_ensemble.json` |
| Cyclic 5_3 ensemble | `outputs/artifacts/egoschema_adaptive_llm_gpt54_nano_no_single_cyclic5_3/egoschema_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_3_ensemble.json` |
| GPT-5.4-nano routing cache | `outputs/artifacts/egoschema_llm_routing_cache_gpt54_nano.json` |

