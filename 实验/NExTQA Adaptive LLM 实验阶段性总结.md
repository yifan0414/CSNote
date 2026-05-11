---
数据集: NExTQA
git commit:
创建时间: 2026-05-06 12:14
tags:
---


## 1. 核心结论

目前 NExTQA 上最好的 clean setting 是 `uniform_100f cyclic5 ensemble`：

```text
outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/
nextqa_dyto_uniform_100f_cyclic5_shuffle5_ensemble.json
```

它的整体准确率为 `3416/4996 = 68.37%`。相比 no-shuffle 的 `uniform_100f` baseline：

```text
3336/4996 = 66.77%
```

提升 `+80` 题，也就是 `+1.60` points。

当前 `adaptive_llm_gpt54_nano_no_single_cyclic5_1 ensemble` 的准确率为 `3384/4996 = 67.73%`。它比自己的 v0/no-shuffle 等价设置提升 `+91` 题，但仍然低于 `uniform_100f cyclic5 ensemble` 的 `68.37%`。

这几轮 NExTQA 实验最重要的发现是：**ABCDE cyclic rotation 依然有效，但 adaptive LLM routing 暂时没有超过强 uniform 100f baseline。** NExTQA 上的 no-shuffle 模型明显过度预测 C/D，少预测 A/B/E；cyclic 5 轮询投票把预测分布拉回更均衡的状态，是当前主要收益来源。

> [!tip] 当然 Adaptive LLM routing 的帧采样数量小于 Uniform 100
> segment_motion / 48
> uniform / 64
> uniform_motion_hybrid / 96
> 

## 2. 总体结果对比

| 实验 | 关键设置 | Correct / Total | Accuracy |
| --- | --- | ---: | ---: |
| Uniform 100f | no-shuffle，100 帧均匀采样 | 3336 / 4996 | 66.77% |
| Uniform cyclic5 v0 | cyclic v0，原始 ABCDE 顺序，等价 no-shuffle | 3336 / 4996 | 66.77% |
| Uniform cyclic5 ensemble | 100f uniform + ABCDE cyclic rotation 5 次投票 | 3416 / 4996 | 68.37% |
| Adaptive LLM cyclic5_1 v0 | GPT-5.4-nano routing，cyclic v0 | 3293 / 4996 | 65.91% |
| Adaptive LLM cyclic5_1 ensemble | GPT-5.4-nano routing + ABCDE cyclic rotation 5 次投票 | 3384 / 4996 | 67.73% |

结论上，cyclic ensemble 在 NExTQA 上同样稳定带来收益：

- `uniform_100f`: `66.77% -> 68.37%`，提升 `+1.60` points。
- `adaptive_llm`: `65.91% -> 67.73%`，提升 `+1.82` points。

但 route 本身没有贡献正收益。和 `uniform_100f cyclic5 ensemble` 对齐到同一批 id 后，`adaptive_llm cyclic5_1 ensemble` 少对 `32` 题：

```text
uniform_only correct: 209
adaptive_only correct: 177
both correct: 3207
both wrong: 1403
net gain adaptive - uniform: -32
```

## 3. 实验过程与发现

### 3.1 Uniform 100f 是很强的基础 baseline

NExTQA 的 `uniform_100f` no-shuffle baseline 为：

```text
3336 / 4996 = 66.77%
```

对应结果文件：

```text
outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f/merge.jsonl
```

这个结果已经明显高于 EgoSchema 上的绝对准确率区间，因此后续 adaptive routing 的门槛更高。当前最好的结果并不是来自更复杂的 route，而是在强 uniform baseline 上加 cyclic option ensemble。

按 keyword router 的问题类型粗分，`uniform_100f cyclic5 ensemble` 的结果如下：

|   Question type    | Correct / Total | Accuracy |
| :----------------: | :-------------: | :------: |
|     `default`      |   1820 / 2590   |  70.27%  |
| `global_temporal`  |   762 / 1261    |  60.43%  |
|   `action_local`   |    527 / 728    |  72.39%  |
| `static_attribute` |    184 / 227    |  81.06%  |
|     `counting`     |    123 / 190    |  64.74%  |

这里的 question type 来自 uniform 跑法里保留的 keyword router 字段；它只作为分析标签，不代表实际 frame selection，因为该实验实际全部使用 `uniform`。

### 3.2 GPT-5.4-nano adaptive LLM routing

完整 routing cache：

```text
outputs/artifacts/nextqa_llm_routing_cache_gpt54_nano.json
```

route 分布如下：

| Route | Count | Ratio |
| --- | ---: | ---: |
| `segment_motion` | 3078 | 61.6% |
| `uniform` | 1734 | 34.7% |
| `uniform_motion_hybrid` | 184 | 3.7% |

question type 分布如下：

| Question type | Count | Ratio |
| --- | ---: | ---: |
| `action_local` | 3094 | 61.9% |
| `static_attribute` | 778 | 15.6% |
| `procedure_causal` | 656 | 13.1% |
| `ambiguous` | 253 | 5.1% |
| `counting` | 180 | 3.6% |
| `global_temporal` | 35 | 0.7% |


### 3.3 Adaptive LLM cyclic5_1

`adaptive_llm_gpt54_nano_no_single_cyclic5_1` 的 5 个单独 variant 与 ensemble 如下：

| Variant | Correct / Total | Accuracy |
| :------ | :-------------- | :------- |
| v0 | 3293 / 4996 | 65.91% |
| v1 | 3286 / 4996 | 65.77% |
| v2 | 3295 / 4996 | 65.95% |
| v3 | 3268 / 4996 | 65.41% |
| v4 | 3312 / 4996 | 66.29% |
| Ensemble | 3384 / 4996 | 67.73% |

单个 adaptive variant 都没有超过 uniform 100f baseline 的 `66.77%`。但是 ensemble 后达到 `67.73%`，说明 cyclic 投票仍然能纠正一批位置诱导错误。

样本级差异：

```text
adaptive_ensemble_only correct: 247
adaptive_v0_only correct: 156
both correct: 3137
both wrong: 1456
net gain: +91
```

### 3.4 发现选项位置偏置※

NExTQA 的正确选项分布本身非常均衡，每个选项大约 1000 个样本：

| Option | GT Count |
| :----: | :------: |
|   A    |   1013   |
|   B    |   1013   |
|   C    |   991    |
|   D    |   967    |
|   E    |   1012   |

但 no-shuffle 的 `uniform_100f` 预测分布明显偏向 C/D，尤其是 D：

| Option | GT Count | No-shuffle Pred | No-shuffle Recall |
| :----: | :------: | :-------------: | :---------------: |
|   A    |   1013   |       846       |      61.50%       |
|   B    |   1013   |       868       |      63.28%       |
|   C    |   991    |      1101       |      71.75%       |
|   D    |   967    |      1332       |      77.25%       |
|   E    |   1012   |       849       |      60.67%       |

最明显的问题是：D 的真实数量只有 967，但模型预测了 1332 次；A/B/E 则都被低估。也就是说，NExTQA 上的主要偏置不是像 EgoSchema 那样单独少选 E，而是**明显偏向后中段位置 C/D，尤其 D**。

这也是 cyclic rotation 在 NExTQA 上有效的直接原因。

### 3.5 ABCDE cyclic rotation 的收益

使用与 EgoSchema 相同的 5 次 cyclic rotation：

| Variant | Option order |
| :-----: | :----------: |
|   v0    |  A B C D E   |
|   v1    |  B C D E A   |
|   v2    |  C D E A B   |
|   v3    |  D E A B C   |
|   v4    |  E A B C D   |

`uniform_100f cyclic5` 的 5 个 variant 与 ensemble 如下：

| Variant | Correct / Total | Accuracy |
| :------ | :-------------- | :------- |
| v0 | 3336 / 4996 | 66.77% |
| v1 | 3308 / 4996 | 66.21% |
| v2 | 3318 / 4996 | 66.41% |
| v3 | 3333 / 4996 | 66.71% |
| v4 | 3350 / 4996 | 67.05% |
| Ensemble | 3416 / 4996 | 68.37% |

单个 variant 差异不大，最高的 v4 是 `67.05%`；真正的最好结果来自 5 次投票后的 ensemble。说明 cyclic 的收益主要来自跨位置一致性投票，而不是某个固定选项顺序本身更好。

样本级差异：

```text
cyclic_ensemble_only correct: 246
uniform_v0_only correct: 166
both correct: 3170
both wrong: 1414
net gain: +80
```

## 4. 最新 uniform cyclic5 详细分析

### 4.1 按 keyword question type 划分

| Question type | v0 No-shuffle | Cyclic5 Ensemble | Change |
| --- | ---: | ---: | ---: |
| `default` | 1792 / 2590 = 69.19% | 1820 / 2590 = 70.27% | +28 |
| `global_temporal` | 735 / 1261 = 58.29% | 762 / 1261 = 60.43% | +27 |
| `action_local` | 515 / 728 = 70.74% | 527 / 728 = 72.39% | +12 |
| `static_attribute` | 181 / 227 = 79.74% | 184 / 227 = 81.06% | +3 |
| `counting` | 113 / 190 = 59.47% | 123 / 190 = 64.74% | +10 |

主要增益来自 `default` 和 `global_temporal`，而不是单一 action-local 子集。这一点和 EgoSchema 不同：EgoSchema 的 cyclic 收益主要集中在 `action_local/segment_motion`，NExTQA 的收益更像是全局选项位置偏置被纠正。

### 4.2 选项分布变化

| Option | GT Count | No-shuffle Pred | Cyclic5 Pred | No-shuffle Recall | Cyclic5 Recall |
| :----- | -------: | --------------: | -----------: | ----------------: | -------------: |
| A | 1013 | 846 | 977 | 61.50% | 68.11% |
| B | 1013 | 868 | 977 | 63.28% | 68.41% |
| C | 991 | 1101 | 1000 | 71.75% | 68.11% |
| D | 967 | 1332 | 1028 | 77.25% | 68.15% |
| E | 1012 | 849 | 1014 | 60.67% | 69.07% |

Cyclic rotation 基本把预测分布拉回到和 GT 分布接近的状态。A/B/E 的 recall 明显提升，C/D 的 recall 回落，但 overall 净收益为正：

```text
3336 -> 3416
net gain: +80
```

这个结果很干净地支持了“模型对选项位置敏感”的判断。

### 4.3 Ensemble tie 与置信度线索
Tie 指的是 ensemble 投票时最高票数出现并列，没有唯一赢家。
`uniform_100f cyclic5 ensemble` 中：

| Vote state | Correct / Total | Accuracy |
| :--------: | :-------------: | :------: |
|  Non-tie   |   3351 / 4793   |  69.91%  |
|    Tie     |    65 / 203     |  32.02%  |

top vote count 分布：

| Top vote count | Samples |
| :------------: | :-----: |
|       1        |    9    |
|       2        |   254   |
|       3        |   790   |
|       4        |   732   |
|       5        |  3211   |

Tie 或低票数样本 accuracy 很低，可以作为下一阶段 selective re-query / stronger reasoning 的候选集合。

## 5. Adaptive LLM 详细分析

### 5.1 按 route 划分

`adaptive_llm_gpt54_nano_no_single_cyclic5_1 ensemble` 的 route 结果：

|          Route          | Correct / Total | Accuracy |
| :---------------------: | :-------------: | :------: |
|    `segment_motion`     |   1994 / 3078   |  64.78%  |
|        `uniform`        |   1272 / 1734   |  73.36%  |
| `uniform_motion_hybrid` |    118 / 184    |  64.13%  |

对比同一实验的 v0：

|          Route          |    v0 No-shuffle     |   Cyclic5 Ensemble   | Change |
| :---------------------: | :------------------: | :------------------: | :----: |
|    `segment_motion`     | 1947 / 3078 = 63.26% | 1994 / 3078 = 64.78% |  +47   |
|        `uniform`        | 1238 / 1734 = 71.40% | 1272 / 1734 = 73.36% |  +34   |
| `uniform_motion_hybrid` |  108 / 184 = 58.70%  |  118 / 184 = 64.13%  |  +10   |

Cyclic 对 adaptive 的三个 route 都有帮助，但 route 选择本身仍然没有超过 uniform 100f。尤其 `segment_motion` 覆盖了 3078 个样本，占比 61.6%，但准确率只有 `64.78%`。

### 5.2 按 LLM question type 划分

|   Question type    | Correct / Total | Accuracy |
| :----------------: | :-------------: | :------: |
|   `action_local`   |   2009 / 3094   |  64.93%  |
| `static_attribute` |    632 / 778    |  81.23%  |
| `procedure_causal` |    415 / 656    |  63.26%  |
|    `ambiguous`     |    186 / 253    |  73.52%  |
|     `counting`     |    116 / 180    |  64.44%  |
| `global_temporal`  |     26 / 35     |  74.29%  |


NExTQA 的 LLM routing 将绝大多数样本归到 `action_local`，但这个最大子集只有 `64.93%`，低于整体平均。`static_attribute` 仍然是最容易的子集，达到 `81.23%`。

### 5.3 与 uniform cyclic5 的同 id 对比

将 `uniform_100f cyclic5 ensemble` 和 `adaptive_llm cyclic5_1 ensemble` 按相同 id 对齐，并使用 adaptive LLM 的 route/type 标签分组：

|   Adaptive group   |   Uniform cyclic5    |   Adaptive cyclic5   | Change |
| :----------------: | :------------------: | :------------------: | :----: |
|   `action_local`   | 2022 / 3094 = 65.35% | 2009 / 3094 = 64.93% |  -13   |
| `static_attribute` |  639 / 778 = 82.13%  |  632 / 778 = 81.23%  |   -7   |
| `procedure_causal` |  416 / 656 = 63.41%  |  415 / 656 = 63.26%  |   -1   |
|    `ambiguous`     |  196 / 253 = 77.47%  |  186 / 253 = 73.52%  |  -10   |
|     `counting`     |  115 / 180 = 63.89%  |  116 / 180 = 64.44%  |   +1   |
| `global_temporal`  |   28 / 35 = 80.00%   |   26 / 35 = 74.29%   |   -2   |

route 维度也是类似：

|  Adaptive route group   |   Uniform cyclic5    |   Adaptive cyclic5   | Change |
| :---------------------: | :------------------: | :------------------: | :----: |
|    `segment_motion`     | 2009 / 3078 = 65.27% | 1994 / 3078 = 64.78% |  -15   |
|        `uniform`        | 1290 / 1734 = 74.39% | 1272 / 1734 = 73.36% |  -18   |
| `uniform_motion_hybrid` |  117 / 184 = 63.59%  |  118 / 184 = 64.13%  |   +1   |

这说明当前 adaptive 策略并没有找到一个比 100f uniform 更稳的证据选择方案。`uniform_motion_hybrid` 有极小正收益，但覆盖太少；`segment_motion` 覆盖最大，却略低于 uniform 100f 对同一批样本的结果。

### 5.4 Adaptive 的选项分布同样被 cyclic 修正

| Option | GT Count | Adaptive v0 Pred | Adaptive Cyclic5 Pred | Adaptive v0 Recall | Adaptive Cyclic5 Recall |
| :----: | :------: | :--------------: | :-------------------: | :----------------: | :---------------------: |
|   A    |   1013   |       850        |          979          |       60.61%       |         67.32%          |
|   B    |   1013   |       855        |          977          |       61.70%       |         67.03%          |
|   C    |   991    |       1123       |         1010          |       72.15%       |         68.52%          |
|   D    |   967    |       1332       |         1025          |       76.53%       |         67.63%          |
|   E    |   1012   |       836        |         1005          |       59.19%       |         68.18%          |

这和 uniform 的现象一致：no-shuffle 明显过度预测 C/D，cyclic ensemble 后分布变得更均衡。

## 6. 当前理解

### 6.1 cyclic 的核心作用仍然是缓解选项位置偏置

NExTQA 的 GT 选项分布几乎均匀，因此 no-shuffle 下预测分布偏向 C/D 的现象很明显。Cyclic rotation 不改变视频帧和问题语义，只改变选项位置；它能在 uniform 和 adaptive 两条线上分别带来 `+80` 和 `+91` 题提升，说明选项位置偏置是当前可稳定利用的误差来源。

<font color="#ff0000">NExTQA 上，cyclic 的收益比 route 的收益更稳定。</font>

### 6.2 Adaptive route 暂时不是主结果

EgoSchema 上 `segment_motion` 是受益明显的 route；但 NExTQA 当前不是这样。GPT-5.4-nano routing 把 61.6% 的样本放到 `segment_motion`，最终该 route 只有 `64.78%`，低于 adaptive 内部 `uniform` route 的 `73.36%`。

这不一定说明 `segment_motion` 本身无效，更可能说明当前 NExTQA 的 route 定义过于激进：

- `action_local` 覆盖 3094 个样本，范围太大。
- 很多 NExTQA 问题虽然包含动作词，但答案可能依赖整体上下文或常识排除，而不是局部 motion peak。
- adaptive 跑法中 `uniform` route 只用 64 帧，而强 baseline 是 100 帧；这也会影响对比。

### 6.3 当前最稳汇报口径

汇报时建议把 `uniform_100f cyclic5 ensemble = 68.37%` 作为 NExTQA 当前主结果，同时说明：

- `uniform_100f` no-shuffle baseline 是 `66.77%`。
- `uniform_100f cyclic5 ensemble` 提升到 `68.37%`。
- `adaptive_llm cyclic5_1 ensemble` 是 `67.73%`，低于 uniform cyclic，但证明 cyclic 对 adaptive 也有效。

## 7. 总结

1. NExTQA 当前最好结果是 `uniform_100f cyclic5 ensemble = 3416/4996 = 68.37%`。
2. Cyclic rotation 把 no-shuffle 的 C/D 位置偏置拉回均衡分布，是主要收益来源。
3. `adaptive_llm cyclic5_1 ensemble = 67.73%`，比 adaptive v0 提升明显，但仍低于 uniform cyclic。
4. 下一阶段重点不是继续全量 route，而是重新设计 NExTQA-specific evidence selection，并优先利用 cyclic vote confidence 找难例。

## 9. 主要结果文件

| 内容 | 路径 |
| --- | --- |
| Uniform 100f no-shuffle | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f/merge.jsonl` |
| Uniform 100f cyclic5 ensemble | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/nextqa_dyto_uniform_100f_cyclic5_shuffle5_ensemble.json` |
| Uniform 100f cyclic5 v0 | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/variant_0/nextqa_dyto_uniform_100f_cyclic5_shuffle5_v0.json` |
| Uniform 100f cyclic5 v1 | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/variant_1/nextqa_dyto_uniform_100f_cyclic5_shuffle5_v1.json` |
| Uniform 100f cyclic5 v2 | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/variant_2/nextqa_dyto_uniform_100f_cyclic5_shuffle5_v2.json` |
| Uniform 100f cyclic5 v3 | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/variant_3/nextqa_dyto_uniform_100f_cyclic5_shuffle5_v3.json` |
| Uniform 100f cyclic5 v4 | `outputs/artifacts/NExTQA/nextqa_dyto_uniform_100f_cyclic5_shuffle5/variant_4/nextqa_dyto_uniform_100f_cyclic5_shuffle5_v4.json` |
| Adaptive LLM cyclic5_1 ensemble | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_ensemble.json` |
| Adaptive LLM cyclic5_1 v0 | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/variant_0/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_v0.json` |
| Adaptive LLM cyclic5_1 v1 | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/variant_1/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_v1.json` |
| Adaptive LLM cyclic5_1 v2 | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/variant_2/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_v2.json` |
| Adaptive LLM cyclic5_1 v3 | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/variant_3/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_v3.json` |
| Adaptive LLM cyclic5_1 v4 | `outputs/artifacts/NExTQA/nextqa_adaptive_llm_gpt54_nano_no_single_cyclic5_1/variant_4/nextqa_pred_adaptive_llm_gpt54_nano_no_single_cyclic5_1_v4.json` |
| GPT-5.4-nano routing cache | `outputs/artifacts/nextqa_llm_routing_cache_gpt54_nano.json` |
| 15-sample keyword routing smoke cache | `outputs/artifacts/nextqa_llm_routing_keyword.json` |
