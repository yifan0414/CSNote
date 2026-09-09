---
数据集: VideoMME
git commit:
创建时间: 2026-05-13T08:08:00
tags:
---
> [!note] Beyond Keyframes: Query-Conditioned Evidence Acquisition for Long-Form Video Reasoning
## EVID 方法理解

EVID 目前是在 DIG 的“reward 找片段”前后各加了一层：

```text
前面：先看 question，判断这题到底需要什么 evidence
后面：按 evidence type 重新分配 local evidence / DIG / uniform 的采样预算
```

整体流程现在这样：

```text
video + question
 -> CAFS 切 content segments，取 r-frame
 -> LMM 给每个 r-frame 打 reward
 -> question-only evidence planner 判断证据类型
 -> evidence-aware refinement 选 evidence intervals
 -> evidence / DIG / uniform 混合采 k 帧
```

### 1. Evidence planning

这一步不看视频，只看 `question + options + task_type`。目的不是直接回答问题，而是先判断这题需要哪类视觉证据。

```text
summary_global        整体理解
single_moment         某个关键瞬间
multi_event_temporal  多个事件 / 多个时间点
counting              计数，需要扫得更全
ocr_detail            文字、字幕、数字、小细节
negative_absence      判断出没出现，需要全局覆盖
```

planner 输出的东西是下面这样作为采帧策略：

```json
{
  "query_type": "multi_event_temporal",
  "evidence_need": "multiple_clips",
  "coverage": "medium",
  "clip_context": "wide",
  "density": "medium",
  "requires_ocr": false
}
```



| 字段            | 意义                            | 可选值                                                                                         |
| ------------- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| query_type    | 决定整体采样策略。                     | summary_global, single_moment, multi_event_temporal, counting, ocr_detail, negative_absence |
| evidence_need | 需要什么形态的证据                     | global_coverage, single_clip, multiple_clips, dense_scan, detail_frames                     |
| coverage      | 需要多大强度全局覆盖                    | low, medium, high                                                                           |
| clip_context  | 每个高 reward 片段前后要扩多宽           | narrow, medium, wide                                                                        |
| density       | 选中的 evidence interval 内，采样要多密 | sparse, medium, dense                                                                       |
| requires_ocr  | 是否需要读文字、数字、字幕、屏幕内容            | true, false                                                                                 |

默认映射：

| query_type | evidence_need | coverage | clip_context | density | requires_ocr |
|---|---|---|---|---|---|
| summary_global | global_coverage | high | wide | sparse | false |
| single_moment | single_clip | low | medium | sparse | false |
| multi_event_temporal | multiple_clips | medium | wide | medium | false |
| counting | dense_scan | high | wide | dense | false |
| ocr_detail | detail_frames | medium | wide | dense | true |
| negative_absence | global_coverage | high | wide | sparse | false |


我觉得这里真正有用的不是 分类 本身，而是它给后面的采样策略提供条件。不同问题需要的 evidence budget 本来就不一样：

```text
整体题：不能只盯最高 reward，uniform 要多
动作题：可以更相信局部高 reward
时序题：需要多个片段，还要带上下文
OCR：高分细节区 + 一点全局补充
counting / absence：最怕漏，coverage 比 peak 更重要
```

### 2. CAFS 和 reward 

CAFS 基本没变，还是用 DINOv2 的特征差找内容边界：

```python
chunk_features = DINOv2(frame).mean(dim=1)
diffs = 1 - cosine_similarity(feature[t], feature[t+1])
peaks = find_peaks(diffs, prominence=0.1)
```

输出还是这两个：

```text
boundaries = [0, cut1, cut2, ..., last_frame]
r_frame_idx = 每个 segment 的代表帧
```

reward assignment 也沿用 DIG：

```text
question + r-frame + timestamp -> LMM -> reward
```

这里要注意：`r_frame` 只是 segment 的探针。也就是说，`reward[i]` 实际上是在粗略评价 `boundaries[i] ~ boundaries[i+1]` 这个片段和问题的相关性。

### 3. refinement 怎么用 reward

DIG 更像是固定地用 reward 选相关片段；EVID 多了一个 question-conditioned policy：

```python
policy = {
  "query_type": ...,
  "coverage": ...,
  "clip_context": ...,
  "density": ...,
  "requires_ocr": ...
}
```

不同类型对应的直觉大概是：

```text
single_moment        少量高 reward 片段
multi_event_temporal 多个高 reward 片段 + 上下文
counting             多一些 coverage，避免漏数
ocr_detail           细节片段 + 全局补充
summary / absence    更偏 uniform
```

高 reward 片段会根据 `clip_context` 往前后扩：

```python
CONTEXT_WINDOWS = {
    "narrow": (0, 1),
    "medium": (1, 1),
    "wide": (1, 2),
}
```

所以最后不是只取一个 r-frame，而是把它扩成一个 evidence interval。

### 4. 最后采样：evidence + DIG + uniform

最终 `k` 帧分三路来：

```text
evidence frames：按 evidence plan 选出的区间
DIG frames：原 DIG refinement 的高 reward 区间
uniform frames：兜底全局覆盖
```

目前固定比例是：

```python
BASE_HYBRID_RATIOS = {
    "summary_global":       evidence 0.00, DIG 0.25, uniform 0.75
    "negative_absence":     evidence 0.00, DIG 0.15, uniform 0.85
    "single_moment":        evidence 0.55, DIG 0.20, uniform 0.25
    "multi_event_temporal": evidence 0.60, DIG 0.20, uniform 0.20
    "counting":             evidence 0.30, DIG 0.15, uniform 0.55
    "ocr_detail":           evidence 0.35, DIG 0.15, uniform 0.50
}
```

![[_assets/images/Pasted image 20260514095548.png]]

所以我现在对 EVID 的一句话理解是：**它不是让 reward 更准，而是承认不同题型对 local peak 和 global coverage 的需求不同，然后按题型重新分采样预算。**

## VideoMME实验

| frames | split  | UNI  |       DIG       |     EVID 最新     | EVID-UNI | EVID-DIG |
| :----: | :----: | :--: | :-------------: | :-------------: | :------: | :------: |
|   8    | short  | 60.0 | <u>**63.4**</u> |      62.8       |   +2.8   |   -0.7   |
|   8    | medium | 51.3 | <u>**54.7**</u> |      54.1       |   +2.8   |   -0.6   |
|   8    |  long  | 45.1 |      47.2       | <u>**48.7**</u> |   +3.6   |   +1.4   |
|   16   | short  | 66.3 | <u>**68.1**</u> |      66.0       |   -0.3   |   -2.1   |
|   16   | medium | 55.3 | <u>**56.9**</u> |      55.7       |   +0.3   |   -1.2   |
|   16   |  long  | 48.1 | <u>**51.4**</u> |      50.6       |   +2.4   |   -0.9   |
|   32   | short  | 70.9 |      70.2       | <u>**71.2**</u> |   +0.3   |   +1.0   |
|   32   | medium | 58.8 | <u>**61.4**</u> |      59.6       |   +0.8   |   -1.9   |
|   32   |  long  | 51.9 | <u>**53.0**</u> |      51.2       |   -0.7   |   -1.8   |
|   64   | short  | 73.2 |      73.2       | <u>**74.4**</u> |   +1.2   |   +1.2   |
|   64   | medium | 61.7 |      62.7       | <u>**64.1**</u> |   +2.4   |   +1.4   |
|   64   |  long  | 50.6 |      55.6       | <u>**56.4**</u> |   +5.9   |   +0.9   |
|  128   | short  | 76.2 |      75.1       | <u>**77.1**</u> |   +0.9   |   +2.0   |
|  128   | medium | 66.0 |      66.2       | <u>**67.4**</u> |   +1.4   |   +1.2   |
|  128   |  long  | 54.7 |      55.3       | <u>**55.4**</u> |   +0.7   |   +0.1   |
|  192   | medium | 67.0 |      68.0       | <u>**69.0**</u> |   +2.0   |   +1.0   |
|  192   |  long  | 55.8 |      58.2       | <u>**58.6**</u> |   +2.8   |   +0.4   |
|  256   | medium | 66.3 |      67.6       |        -        |    -     |    -     |
|  256   |  long  | 57.1 |      57.7       |        -        |    -     |    -     |

Overall ：

| frames | UNI  |       DIG       |     EVID 最新     |
| :----: | :--: | :-------------: | :-------------: |
|   8    | 52.1 |      55.1       | <u>**55.2**</u> |
|   16   | 56.6 | <u>**58.8**</u> |      57.4       |
|   32   | 60.5 | <u>**61.6**</u> |      60.7       |
|   64   | 61.8 |      63.8       | <u>**65.0**</u> |
|  128   | 65.6 |      65.6       | <u>**66.6**</u> |
|  192   |  -   |        -        | <u>**68.1**</u> |

先看 split 维度：

- `64/128/192` 是比较舒服的区间，short / medium / long 都赢。
- `8` 帧时 EVID 和 DIG 很接近，long 有收益，但 short / medium 还是 DIG 更强。
- `16/32` 的 medium / long 还压不过 DIG，说明这个版本在中低帧数下的分配不够好。
- 相比 UNI 基本都有收益，主要例外是 `16 short` 和 `32 long`。


### 按照 query_type 分类实验结果
**8 Frames**

|      query_type      |  n   |       UNI       |       DIG       |      ※EVID      | ΔUNI | ΔDIG |
| :------------------: | :--: | :-------------: | :-------------: | :-------------: | :--: | :--: |
|    summary_global    | 487  |      63.7       |      66.1       | <u>**66.9**</u> | +3.3 | +0.8 |
|    single_moment     | 514  |      61.3       |      63.2       | <u>**66.3**</u> | +5.1 | +3.1 |
| multi_event_temporal | 1037 |      48.4       |      51.5       | <u>**51.9**</u> | +3.5 | +0.4 |
|       counting       | 278  |      35.3       | <u>**39.9**</u> |      33.8       | -1.4 | -6.1 |
|      ocr_detail      | 243  |      49.4       | <u>**55.1**</u> |      52.7       | +3.3 | -2.5 |
|   negative_absence   | 141  | <u>**44.7**</u> |      44.0       | <u>**44.7**</u> | +0.0 | +0.7 |

**16 Frames**

|      query_type      |  n   | UNI  |       DIG       |      ※EVID      | ΔUNI | ΔDIG |
| :------------------: | :--: | :--: | :-------------: | :-------------: | :--: | :--: |
|    summary_global    | 487  | 68.8 | <u>**70.6**</u> |      69.8       | +1.0 | -0.8 |
|    single_moment     | 514  | 66.1 |      67.9       | <u>**68.1**</u> | +1.9 | +0.2 |
| multi_event_temporal | 1037 | 52.9 | <u>**54.6**</u> |      53.1       | +0.2 | -1.4 |
|       counting       | 278  | 36.3 | <u>**41.4**</u> |      34.5       | -1.8 | -6.8 |
|      ocr_detail      | 243  | 56.4 | <u>**60.5**</u> |      59.7       | +3.3 | -0.8 |
|   negative_absence   | 141  | 46.8 |      47.5       | <u>**48.2**</u> | +1.4 | +0.7 |

**32 Frames**

|      query_type      |  n   |       UNI       |       DIG       |      ※EVID      | ΔUNI | ΔDIG |
| :------------------: | :--: | :-------------: | :-------------: | :-------------: | :--: | :--: |
|    summary_global    | 487  |      72.5       | <u>**73.1**</u> |      71.0       | -1.4 | -2.1 |
|    single_moment     | 514  | <u>**71.8**</u> |      71.6       | <u>**71.8**</u> | +0.0 | +0.2 |
| multi_event_temporal | 1037 |      56.0       | <u>**57.0**</u> |      55.7       | -0.3 | -1.3 |
|       counting       | 278  | <u>**40.6**</u> |      40.3       |      39.9       | -0.7 | -0.4 |
|      ocr_detail      | 243  |      59.3       | <u>**65.4**</u> |      64.2       | +4.9 | -1.2 |
|   negative_absence   | 141  |      52.5       |      53.9       | <u>**55.3**</u> | +2.8 | +1.4 |

**64 Frames**

|      query_type      |  n   | UNI  |       DIG       |      ※EVID      | ΔUNI | ΔDIG |
| :------------------: | :--: | :--: | :-------------: | :-------------: | :--: | :--: |
|    summary_global    | 487  | 72.5 |      73.7       | <u>**74.9**</u> | +2.5 | +1.2 |
|    single_moment     | 514  | 71.4 |      73.7       | <u>**75.3**</u> | +3.9 | +1.6 |
| multi_event_temporal | 1037 | 57.7 |      58.4       | <u>**60.8**</u> | +3.2 | +2.4 |
|       counting       | 278  | 40.6 | <u>**46.4**</u> |      46.0       | +5.4 | -0.4 |
|      ocr_detail      | 243  | 65.0 | <u>**69.1**</u> |      68.7       | +3.7 | -0.4 |
|   negative_absence   | 141  | 56.7 | <u>**58.2**</u> |      54.6       | -2.1 | -3.5 |

**128 Frames**

|      query_type      |  n   | UNI  |       DIG       |      ※EVID      | ΔUNI | ΔDIG |
| :------------------: | :--: | :--: | :-------------: | :-------------: | :--: | :--: |
|    summary_global    | 487  | 76.0 |      76.2       | <u>**76.6**</u> | +0.6 | +0.4 |
|    single_moment     | 514  | 75.3 |      77.6       | <u>**78.8**</u> | +3.5 | +1.2 |
| multi_event_temporal | 1037 | 61.5 |      60.2       | <u>**61.8**</u> | +0.3 | +1.6 |
|       counting       | 278  | 45.7 |      45.3       | <u>**46.8**</u> | +1.1 | +1.4 |
|      ocr_detail      | 243  | 68.3 | <u>**69.1**</u> |      68.3       | +0.0 | -0.8 |
|   negative_absence   | 141  | 59.6 |      57.4       | <u>**61.0**</u> | +1.4 | +3.5 |

按 query type 看：

- `single_moment` 最稳，所有帧数都不输 DIG。这说明 evidence planning 对局部动作题确实有帮助。
- `multi_event_temporal` 要到 `64/128` 才明显起来；低帧数下可能是多片段预算不够，也可能是上下文扩得还不对。
- `counting` 是最大问题，`8/16` 帧比 DIG 低很多。这里可能不是“多一点 coverage”就够，counting 需要更 dense 的扫描策略。
- `ocr_detail` 也不稳，尤其低帧数下经常输 DIG。现在的 OCR policy 还没有真正照顾到文字细节。
- `negative_absence` 在 `64` 掉得比较明显，但 `128` 又回来，感觉还是覆盖率不足导致的。

## 目前判断


```text
DIG pipeline
+ question taxonomy
+ 手写 evidence budget
```

问题是 policy 这块太像人工规则。`query_type` 是 LLM prompt 分出来的，`evidence / DIG / uniform` 的比例也是手写的，所以很容易被看成 prompt classification + heuristic sampling。

我现在的判断：

```text
可以作为 motivation / analysis / strong baseline
但还不能直接当顶会主贡献
```

### 后面要补的东西

**1. 固定比例改成 adaptive budget**

现在最弱的是固定 ratio。下一版最好根据 reward 分布和视频属性动态调：

```text
reward 很尖 -> 多给 local evidence
reward 很平 -> 多给 uniform
视频长 / counting / absence -> 多给 coverage
OCR -> 多保留细节帧
```

这样贡献点可以从“按题型手写比例”变成：

```text
question-conditioned + reward-distribution-aware frame budget allocation
```

**2. 加 evidence-level 分析**

只报 accuracy 不够，最好再补几个 evidence 维度的指标：

```text
coverage       选中帧有没有覆盖答案片段
concentration  无关帧少不少
sufficiency    只看选中帧能不能答
redundancy     选帧是否重复
```

这样问题会更像是在研究 long-video QA 里什么样的 evidence 才够，而不是单纯做一个采帧 trick。

**3. Reward 从单帧升级到片段**

现在是：

```text
question + r-frame -> reward
```

但时序、因果、counting 很多时候单帧不够。可以考虑变成：

```text
question + neighboring r-frames / mini clip
 -> temporal role / evidence type / reward
```

例如把片段标成：

```text
setup / action / outcome / OCR detail / counting candidate / irrelevant
```

这样会更像 evidence structure modeling，而不是单纯 frame scoring。

**4. Router 最好可学习**

如果能从实验结果或 pseudo-label 里学一个轻量 router：

```text
input:
  question embedding
  task type
  reward statistics
  video duration
  segment number

output:
  evidence / DIG / uniform ratio
  context window
  number of intervals
```

哪怕只是小模型或者 bandit，也比固定规则更站得住。

### 一句话

当前 EVID 证明了“按题型分配 evidence budget”这件事是有潜力的，但方法还停在工程规则层。下一版要把重点从 `LLM 分类 + 手写比例` 往 `自适应 / 可学习的 evidence policy` 上推，同时补 evidence coverage / sufficiency 分析，这样才更像一个完整的研究贡献。
