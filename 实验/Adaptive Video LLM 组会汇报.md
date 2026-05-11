---
title: Adaptive Video LLM 组会汇报
创建时间: 2026-05-07 00:37
更新日期: 2026-05-07
tags:
  - meeting/report
  - experiment/adaptive-video-llm
---

## 1. 本阶段实验问题

本阶段主要围绕两个问题展开：

1. **Adaptive evidence routing 是否能提升 VideoQA？**  
   即根据问题类型，为不同样本选择不同 evidence profile / frame selection，例如 `uniform`、`segment_motion`、`uniform_motion_hybrid` 等。

2. **多选题选项位置是否会影响 Video LLM 的答案？**  
   如果模型对 A/B/C/D/E 的位置有偏置，那么即使视频证据不变，仅改变选项排列也可能改变预测结果。

> [!summary]+
> **cyclic option rotation 在 NExTQA 和 EgoSchema 上都带来了稳定提升**。
> 
> 但对 adaptive routing 本身还不能下最终结论
> - 因为目前还没有完成 oracle headroom 实验，尚不能判断问题是 router 是不是选错了 profile 导致准确度不高
> - 其次 adaptive routing 的帧采样(48/64/96，平均 55 帧)小于 baseline 的 100 frame
> - 设计的分类不够好


## 2. 当前最好结果

| Dataset | Best setting | Correct / Total | Acc |
| --- | --- | ---: | ---: |
| NExTQA | Uniform 100f + cyclic5 ensemble | 3416 / 4996 | **68.37%** |
| EgoSchema | Adaptive LLM no-single + cyclic5 ensemble | 260 / 500 | **52.00%** |

从结果上看，NExTQA 的当前最高结果来自 `uniform_100f` 加 cyclic ensemble；EgoSchema 的当前最高结果来自 adaptive LLM no-single 加 cyclic ensemble。两者的共同点是都使用了 **ABCDE cyclic rotation + ensemble**。

## 3. 与 DYTO / KTV 的结果位置

这里先按 7B / training-free 压缩方法这一组进行对比。这个对比相对公平，因为 DYTO 和 KTV 都是 training-free video token / frame compression 方法。

| Method        | NExTQA Acc | EgoSchema Acc | 备注                     |
| :------------ | :--------- | :------------ | :--------------------- |
| DYTO-7B       | 65.7       | 48.6          | dynamic token merging  |
| KTV-7B-sparse | 64.5       | 49.6          | 504 tokens             |
| KTV-7B-normal | 65.1       | 50.4          | 936 tokens             |
| KTV-7B-dense  | 65.8       | 51.0          | 1872 tokens            |
| **Ours**      | **68.37**  | **52.00**     | cyclic option ensemble |

相对 DYTO / KTV 7B 的提升为：

| 对比对象            | NExTQA    | EgoSchema |
| :-------------- | :-------- | :-------- |
| vs DYTO-7B      | **+2.67** | **+3.40** |
| vs KTV-7B-dense | **+2.57** | **+1.00** |

## 4. 实验一：Adaptive routing 的阶段性结果

### 4.1 NExTQA

| Setting | Correct / Total | Acc |
| --- | ---: | ---: |
| Uniform 100f no-shuffle | 3336 / 4996 | 66.77% |
| Uniform 100f + cyclic5 ensemble | 3416 / 4996 | **68.37%** |
| Adaptive LLM no-shuffle | 3293 / 4996 | 65.91% |
| Adaptive LLM + cyclic5 ensemble | 3384 / 4996 | 67.73% |

在 NExTQA 上，当前 adaptive LLM routing 没有超过 `uniform_100f`。但是这只能说明**当前这个 router 的实际分配结果还不够好**，不能直接说明 adaptive routing 这个方向没有价值。

原因是：如果 `segment_motion`、`uniform_motion_hybrid` 等 profile 与 `uniform_100f` 存在样本级互补，那么理论上仍然可能通过更好的 router 获得提升。这个问题需要 oracle headroom 实验来判断。

### 4.2 EgoSchema

| Setting                   | Correct / Total |        Acc |
| ------------------------- | --------------: | ---------: |
| Rule adaptive             |       250 / 500 |     50.00% |
| GPT-5.4-nano route        |       247 / 500 |     49.40% |
| Random shuffle 5 ensemble |       241 / 500 |     48.20% |
| Cyclic5 ensemble          |       260 / 500 | **52.00%** |

在 EgoSchema 上，rule adaptive 曾达到 50.00%，GPT-5.4-nano route 为 49.40%，最后 cyclic5 ensemble 达到 52.00%。
[[EgoSchema Adaptive LLM 实验阶段性总结#4 Egoschema 最新 cyclic 5_3 详细分析]]

## 5. 实验二：选项位置偏置与 cyclic rotation

### 5.1 方法

对每个样本做 5 次结构化选项轮换：

| Variant | Option order |
| --- | --- |
| v0 | A B C D E |
| v1 | B C D E A |
| v2 | C D E A B |
| v3 | D E A B C |
| v4 | E A B C D |

每次推理后，将预测选项映射回原始 ABCDE，再进行 **majority vote**。这个操作不改变视频帧，也不改变问题语义，只改变候选答案的位置。因此，如果它带来稳定提升，说明模型确实受到选项位置的影响。

### 5.2 NExTQA 结果

| Setting                         | Correct / Total |        Acc |      Gain |
| ------------------------------- | --------------: | ---------: | --------: |
| baseline                        |               - |     65.70% |         - |
| Uniform 100f + cyclic5 ensemble |     3416 / 4996 | **68.37%** | **+2.67** |
| Adaptive LLM no-shuffle         |     3293 / 4996 |     65.91% | **+0.21** |
| Adaptive LLM + cyclic5 ensemble |     3384 / 4996 |     67.73% | **+2.03** |

NExTQA 上，cyclic ensemble 对 uniform 和 adaptive 两条线都有提升。uniform 100f 从 66.77% 提升到 68.37%，净增 80 题；adaptive LLM 从 65.91% 提升到 67.73%，净增 91 题。

### 5.3 EgoSchema 结果

| Setting                           | Correct / Total |        Acc |      Gain |
| --------------------------------- | --------------: | ---------: | --------: |
| baseline                          |       240 / 500 |     48.00% |         - |
| Adaptive LLM no-shuffle           |       247 / 500 |     49.40% | **+1.40** |
| Random shuffle 5 ensemble         |       241 / 500 |     48.20% | **+0.20** |
| Uniform 100 f + cyclic 5 ensemble |       257 / 500 |     51.40% | **+3.60** |
| Adaptive LLM + cyclic 5 ensemble  |       260 / 500 | **52.00%** | **+4.00** |
EgoSchema 上，Adaptive LLM 单独使用带来小幅提升（48.0% → 49.4%），随机 shuffle ensemble 基本无效。  
最好的 setting 是 Adaptive LLM + cyclic 5 ensemble，达到 52.0%，相比 baseline 提升 4.0 个百分点。

## 6. 选项分布分析

### 6.1 EgoSchema：主要问题是少选 E

| Option | GT Count | No-shuffle Pred | Cyclic5 Pred |     Recall 变化     |
| :----: | :------: | :-------------: | :----------: | :---------------: |
|   A    |   101    |       131       |     120      |   46.53 → 47.52   |
|   B    |   108    |       86        |     114      |   43.52 → 53.70   |
|   C    |    91    |       113       |      84      |   58.24 → 49.45   |
|   D    |    83    |       111       |      93      |   68.67 → 63.86   |
|   E    |   117    |       59        |      89      | **36.75 → 47.86** |

EgoSchema 的 no-shuffle 结果中，E 是最明显被低估的位置。GT 中 E 有 117 个，但模型只预测 59 次。cyclic 后预测 E 的次数增加到 89，E recall 从 36.75% 提升到 47.86%。

这说明 EgoSchema 的一部分错误不是由视觉证据不足直接导致，而是和候选答案的位置呈现有关。

### 6.2 NExTQA：主要问题是偏向 C/D

| Option | GT Count | No-shuffle Pred | Cyclic5 Pred |   Recall 变化   |
| :----: | :------: | :-------------: | :----------: | :-----------: |
|   A    |   1013   |       846       |     977      | 61.50 → 68.11 |
|   B    |   1013   |       868       |     977      | 63.28 → 68.41 |
|   C    |   991    |      1101       |     1000     | 71.75 → 68.11 |
|   D    |   967    |      1332       |     1028     | 77.25 → 68.15 |
|   E    |   1012   |       849       |     1014     | 60.67 → 69.07 |

NExTQA 的 GT 选项分布基本均衡，但 no-shuffle 预测明显偏向 C/D，尤其是 D。D 的 GT 数量只有 967，但 no-shuffle 预测了 1332 次。cyclic 后各选项预测数更接近 GT 分布，整体准确率也提升。

这个结果说明，cyclic rotation 的作用不是单纯增加推理次数，而是在缓解模型对候选答案位置的偏置。

## 7. Oracle headroom：adaptive routing 还需要的关键诊断

当前还不能判断 adaptive routing 的理论上限。下一步需要做 oracle headroom 实验。

`oracle headroom` 的定义是：假设有一个上帝视角 router，每个样本都知道哪个 evidence profile 会答对，则 adaptive routing 最多能达到多少准确率。

公式如下：

```text
oracle_correct(sample) = any(profile_i_correct(sample) for profile_i in profiles)
oracle_accuracy = mean(oracle_correct)
headroom = oracle_accuracy - best_single_profile_accuracy
```

`oracle headroom` 可以理解成：**假设你有一个“上帝视角 router”，每个样本都能提前知道哪种 evidence profile 会答对，那么 adaptive route 理论上最多能提升多少。**

它不是实际可用方法，而是用来回答一个关键问题：

> 这件事有没有提升空间？问题是 router 没选好，还是所有 route 都差不多？

举个例子。假设你给同一批 NExTQA 样本都跑 4 种 evidence profile：

```text
uniform_100f
segment_motion
broad_temporal
detail_static
```

对每个样本，你检查这 4 个结果里有没有至少一个答对。

如果普通 `uniform_100f` 是：

```text
66.77%
```

而 oracle 是：

```text
78.00%
```

这说明 headroom 很大：**不同 evidence profile 确实互补，只是当前 router 没把样本分给正确 profile。** 这时继续研究 routing 是值得的。

但如果 oracle 只有：

```text
68.00%
```

那就说明 headroom 很小：**换 evidence profile 本身没带来多少互补性**，继续调 route 可能收益有限，瓶颈更可能在模型理解能力、选项偏置、答案语言歧义或视觉编码压缩。

公式上很简单：

```text
oracle_correct(sample) = any(profile_i_correct(sample) for profile_i in profiles)
oracle_accuracy = mean(oracle_correct)
headroom = oracle_accuracy - best_single_profile_accuracy
```

比如 5 个样本，4 个 profile 的对错是：

| Sample | Uniform | Motion | Static | Temporal | Oracle                         |
| ------ | ------- | ------ | ------ | -------- | ------------------------------ |
| 1      | ✓       | ✗      | ✗      | ✗        | <font color="#ff0000">✓</font> |
| 2      | ✗       | ✓      | ✗      | ✗        | <font color="#ff0000">✓</font> |
| 3      | ✗       | ✗      | ✓      | ✗        | <font color="#ff0000">✓</font> |
| 4      | ✓       | ✓      | ✗      | ✗        | <font color="#ff0000">✓</font> |
| 5      | ✗       | ✗      | ✗      | ✗        | <font color="#ff0000">✗</font> |

如果最好的单 profile 只对 2/5，但 oracle 对 4/5，那说明 profile 之间互补很强，route 有很大潜力。

计划比较的 profile 包括：

```text
uniform_100f
segment_motion
broad_temporal
detail_static
uniform_motion_hybrid
```

这个实验要回答三个问题：

1. 是否存在大量 `uniform_100f` 错、其他 profile 对的样本？
2. 如果存在，这些样本能否被 question type、LLM routing、vote confidence 等特征预测出来？
3. oracle accuracy 相比 best single profile 的 headroom 有多大？

如果 headroom 很大，说明不同 evidence profile 之间互补性强，当前问题主要是 router 没选好；如果 headroom 很小，说明单纯切换 evidence profile 的收益有限，瓶颈更可能在模型理解、选项偏置、语言歧义或视觉编码压缩。

## 8. 阶段性结论

1. **cyclic option rotation 是目前最稳定的增益来源。**  
   NExTQA 从 66.77% 提升到 68.37%，EgoSchema 从 49.40% 提升到 52.00%。

2. **两个数据集的选项偏置形态不同。**  
   EgoSchema 主要是少选 E；NExTQA 主要是偏向 C/D。cyclic rotation 在两种偏置形态下都有效。

3. **adaptive routing 目前还不能下结论。**  
   当前 router 的实际结果没有超过最强 uniform + cyclic baseline，但还没有 oracle headroom，因此不能判断是 router 不够好

4. **与 7B training-free 压缩方法相比，当前结果已经处在更高位置。**  
   当前 NExTQA / EgoSchema 分别为 68.37% / 52.00%，高于 DYTO-7B 和 KTV-7B-dense。但在更大模型或 agent setting 下，仍有更高结果。
## 9. 后续实验
1. 做对齐实验

| Setting                     | 目的                                           |
| --------------------------- | -------------------------------------------- |
| `uniform_48f`               | 看 48 帧 uniform 本身掉多少                         |
| `uniform_64f`               | 和 adaptive 里 uniform route 的 budget 对齐       |
| `uniform_96f`               | 和 hybrid/counting budget 对齐                  |
| `adaptive_same_budget_100f` | route 不变，但每个 route 尽量用 100 帧或等价 token budget |
| `adaptive_original_budget`  | 当前结果                                         |

2. 补 oracle headroom，判断 adaptive routing 的理论上限。
3. 分析 `uniform` 错但其他 profile 对的样本，检查其 question type、选项分布和 vote confidence。
4. 对 cyclic ensemble 做 tie case 和 confidence-based voting 分析。
5. 对齐 DYTO / KTV 的同模型、同 token budget 设置，补充效率和准确率对比。
6. 在更多 multiple-choice VideoQA 数据集上验证 option-position debiasing 是否通用。

## 10. 参考

- DYTO: https://arxiv.org/abs/2411.14401
- KTV: https://arxiv.org/abs/2602.03615
- D-CoDe: https://arxiv.org/abs/2510.08818
- ProVCA: https://arxiv.org/abs/2604.02891
- VideoAgent2: https://arxiv.org/abs/2504.04471
- 参考实验记录：[[实验/NExTQA Adaptive LLM 实验阶段性总结]]、[[实验/EgoSchema Adaptive LLM 实验阶段性总结]]