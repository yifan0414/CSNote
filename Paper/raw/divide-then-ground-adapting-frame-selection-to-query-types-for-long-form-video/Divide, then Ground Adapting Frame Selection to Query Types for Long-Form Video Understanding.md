---
title: (frame)DIG
authors:
  - Jialuo Li
  - Bin Li
  - Jiahao Li
  - Yan Lu
conference: CVPR 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2512.04000
pdf_link: "[[assets/paper_2512.04000.pdf]]"
cover: "[[assets/pipeline_2512.04000.png]]"
updated: 2026-05-12
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - question-aware
  - video-llm
  - temporal-reasoning
status: read
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/Jialuo-Li/DIG
---

## TL;DR

- 这篇论文提出 **DIG**，核心判断是：long-form video understanding 里的 frame selection 不该对所有 query 一刀切。
- 作者把问题分成 **Global Query (GQ)** 与 **Localized Query (LQ)**：GQ 需要整体理解，uniform sampling 已经足够；LQ 需要定位具体片段，query-aware selection 才更有价值。
- DIG 是 training-free framework：先用 LLM 做 Query Identification；如果是 GQ 就直接 uniform sampling；如果是 LQ，则走 CAFS + LMM reward assignment + video refinement。
- 主实验覆盖 MLVU、LongVideoBench、VideoMME medium/long；DIG 在 Qwen2.5-VL-7B/32B 上整体优于 UNI、AKS、Q-Frame，并且在高帧数输入下更稳定。
- 主要代价来自 reward assignment，但相比 AKS 的搜索成本，DIG 仍有明显效率优势；Query Identification 在 MLVU 和 VideoMME 上还能减少不必要的 selection 开销。

## Key Contributions

1. **Query typology**：明确区分 Global Query 与 Localized Query，并用实验说明 uniform sampling 在两类 query 上表现不同。随着输入帧数增加，GQ 相对稳定，LQ 更容易被无关帧污染。

2. **DIG framework**：提出 training-free 的 adaptive frame selection。GQ 走 uniform sampling，LQ 走更昂贵但更有针对性的 CAFS、reward assignment、video refinement。

3. **CAFS**：用 DINOv2 frame feature 的相邻帧距离峰值来切分视频，并选择 stable segment 的 midpoint 作为 representative frame，也就是论文里的 r-frame。

4. **LMM-as-reward**：不用 CLIPScore 或 detector 做浅层匹配，而是让 LMM 根据 query 给 r-frame 评分，考虑当前帧是否直接有用，以及邻近帧是否可能包含补充信息。

5. **Scale-aware evaluation**：不像很多 work 只在低帧数下比较，论文把输入帧数扩展到 192/256，并在 appendix 里进一步报告 Qwen3-VL-8B 到 768 frames 的结果。

## Method

DIG 的关键是先判断 query 类型，再决定 selection 策略：

1. **Query Type Identification**  
   使用 LLM 将 query $Q$ 分为 Global Query 或 Localized Query。GQ 认为需要整体视频语义，LQ 认为答案集中在某些具体 segment。

2. **Global Query path**  
   对整段视频做 uniform sampling，直接把采样帧送入 LMM。作者的实验证据表明，GQ 上复杂 query-aware search 通常收益不大。

3. **Localized Query path: CAFS**  
   先以 2 fps 抽帧，得到 $M$ 个 frame feature $\{V_{I_i}\}_{i=1}^{M}$。相邻帧距离定义为：

   $$
   d_i = 1 - \mathrm{sim}(V_{I_i}, V_{I_{i+1}})
   $$

   其中 $\mathrm{sim}(\cdot,\cdot)$ 是 cosine similarity。CAFS 找出距离序列中的 prominent peaks，用这些峰值作为内容边界，再取相邻边界之间的 midpoint 作为 r-frame。

4. **Reward Assignment**  
   对每个 r-frame，用 LMM 根据 query 打 $0$ 到 $100$ 的 reward。评分 prompt 要求模型描述与问题相关的视觉内容，并判断该帧及其相邻帧对回答问题的帮助程度。

5. **Reward-guided Video Refinement**  
   给定 reward 集合 $\{R_j\}$，DIG 迭代执行均值阈值化：

   $$
   R'_j = \max(R_j - \overline{R}, 0)
   $$

   当正 reward index 集合稳定后，保留这些 r-frame 对应的 segment，并向左右扩展 window length $wlen$。主实验设 $wlen=2$。最终对 refined video 再做 uniform sampling，作为 LMM 的输入。

## Pipeline Figure

![[assets/pipeline_2512.04000.png]]

Caption: **Overview of DIG.** The LLM first classifies the query type. Global queries utilize uniform sampling across the entire video, while localized queries employ CAFS and reward assignment to construct a refined video prior to sampling. The selected frames are subsequently processed by the LMM for final inference.

DIG 的 pipeline 可以理解成一句话：**先判断问题需不需要看全局，再只对局部型问题做有目标的帧筛选**。

整体分 5 步：

1. **Query Identification**
   用 LLM 把问题分成 `global` 或 `local`。
   代码在 query_identification.py，prompt 在 utils.py。
   - `global`：例如总结、整体主题、全视频比较。
   - `local`：答案集中在某些人物、物体、事件、时间段。

2. **CAFS: Content-Aware Frame Selection**
   只对 `local` query 做。代码在 cafs.py。
   它用 `DINOv2` 提取视频帧特征，计算相邻采样帧的视觉差异，找出内容变化峰值作为边界，然后在边界区间中取代表帧，也就是 `r_frame_idx`。同时保存 `boundaries`。

3. **Reward Assignment**
   对每个 localized query 的 r-frame，让 LMM 根据“这帧对回答问题有没有用”打 `0-100` 分。
   代码在 reward_assignment.py。
   输出保存在 `rewards/<MODEL>\_<dataset>.json`，里面包含：
   - `query_type`
   - `r_frame_idx`
   - `boundaries`
   - `reward`

4. **Video Refinement**
   根据 reward 分布缩小视频范围。代码在 video_refinement.py。
   - 对 `local` query：归一化 reward，筛出高相关 r-frame，向前后扩展 `wlen=2` 个边界区间，合并区间，再在这些 refined intervals 里均匀采样 `k` 帧。
   - 对 `global` query：直接在整段视频上均匀采样 `k` 帧。
   输出到 `keyframes/`，格式是 `videoid -> question -> frame_indices`。

5. **Final Inference / Evaluation**
   评测脚本在 scripts/eval/qwen25vl.sh 和 scripts/eval/qwen3vl.sh。
   `DIG` 模式会传：
   ```bash
   use_uniform=False,data_path=keyframes/...
   ```
   Qwen 模型加载器会根据 `video_id + question/options` 找到 DIG 选出的帧索引，只把这些帧送给 LMM。`UNI` baseline 则是普通全视频均匀采样。

所以更抽象地说：

```text
question + video
    -> classify query: global / local
    -> if global: uniform sample whole video
    -> if local:
        DINOv2 找内容边界和 r-frames
        LMM 给 r-frames 打相关性 reward
        reward 分布决定 refined video intervals
        在 refined intervals 里采样最终帧
    -> LMM answer / lmms-eval evaluation
```

DIG 的关键点不是单纯“多取关键帧”，而是 **query-adaptive frame selection**：全局问题保留全局覆盖，局部问题先定位相关区间，再把有限帧预算集中用在更可能回答问题的地方。


## Experiments

### Datasets

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MLVU | Long video multiple-choice VQA | Dev multiple-choice subset; open-ended questions excluded | Accuracy | Avg. duration 636.2s; 2174 QA pairs |
| LongVideoBench-val | Long video QA with fine-grained referring/relation reasoning | Validation set | Accuracy | Avg. duration 732.2s; 1337 QA pairs |
| VideoMME-short | Multi-domain video QA | Short split; visual-only in this paper | Accuracy | Avg. duration 80.7s; 900 QA pairs; used in some ablations |
| VideoMME-medium | Multi-domain video QA | Medium split; no subtitles/audio | Accuracy | Avg. duration 516.8s; 900 QA pairs |
| VideoMME-long | Multi-domain video QA | Long split; no subtitles/audio | Accuracy | Avg. duration 2466.3s; 900 QA pairs |

### Main Results

下面两张表转写自 paper Table 1。数值是 accuracy (%)；粗体沿用论文中标出的 best performance。

**Qwen2.5-VL-32B**

| Method | #Frames | MLVU | LVB | VideoMME Medium | VideoMME Long |
| ---- | ---- | ---- | ---- | ---- | ---- |
| UNI | 8 | 55.93 | 53.40 | 53.89 | **<u>51.56</u>** |
| Q-Frame | 8 | 56.03 | 53.78 | 54.03 | 49.63 |
| **<u>DIG (Ours)</u>** | 8 | **<u>61.55</u>** | **<u>56.77</u>** | **<u>54.12</u>** | 51.21 |
| UNI | 16 | 58.79 | 54.67 | 55.44 | **<u>53.33</u>** |
| Q-Frame | 16 | 57.73 | 56.62 | 55.09 | 51.11 |
| **<u>DIG (Ours)</u>** | 16 | **<u>66.21</u>** | **<u>58.86</u>** | **<u>58.62</u>** | 52.18 |
| UNI | 32 | 61.91 | 57.89 | 57.89 | 53.33 |
| AKS | 32 | 66.42 | 59.31 | 59.89 | 56.00 |
| Q-Frame | 32 | 60.95 | 57.37 | 60.43 | 55.90 |
| **<u>DIG (Ours)</u>** | 32 | **<u>70.69</u>** | **<u>61.86</u>** | **<u>60.87</u>** | **<u>57.76</u>** |
| UNI | 64 | 66.24 | 59.01 | 64.33 | 55.67 |
| AKS | 64 | 69.41 | 61.41 | 64.67 | **<u>58.44</u>** |
| Q-Frame | 64 | 66.05 | 59.61 | 62.80 | 57.72 |
| **<u>DIG (Ours)</u>** | 64 | **<u>74.19</u>** | **<u>63.65</u>** | **<u>66.24</u>** | 58.19 |
| UNI | 128 | 70.24 | 61.78 | 68.89 | 59.67 |
| AKS | 128 | 72.77 | 62.00 | 68.33 | 61.44 |
| Q-Frame | 128 | 70.10 | 60.06 | 68.21 | 59.28 |
| **<u>DIG (Ours)</u>** | 128 | **<u>75.20</u>** | **<u>65.60</u>** | **<u>69.00</u>** | **<u>62.29</u>** |
| UNI | 192 | 71.76 | 63.80 | 69.56 | 62.00 |
| AKS | 192 | 73.46 | 62.45 | 69.89 | 61.00 |
| **<u>DIG (Ours)</u>** | 192 | **<u>76.66</u>** | **<u>66.42</u>** | **<u>70.11</u>** | **<u>63.42</u>** |

**Qwen2.5-VL-7B**

| Method         | #Frames | MLVU      | LVB       | VideoMME Medium | VideoMME Long |
| -------------- | ------- | --------- | --------- | --------------- | ------------- |
| UNI            | 8       | 53.64     | 51.23     | 51.36           | 45.84         |
| Q-Frame        | 8       | 54.42     | 54.23     | 50.81           | **<u>49.21</u>**     |
| **<u>DIG (Ours)</u>** | 8       | **<u>58.64</u>** | **<u>55.20</u>** | **<u>54.23</u>**       | 46.88         |
| UNI            | 16      | 56.43     | 54.45     | 55.94           | 48.12         |
| Q-Frame        | 16      | 56.81     | 57.37     | 53.78           | 49.02         |
| **<u>DIG (Ours)</u>** | 16      | **<u>63.98</u>** | **<u>57.89</u>** | **<u>56.81</u>**       | **<u>51.93</u>**     |
| UNI            | 32      | 59.52     | 56.92     | 59.08           | 52.02         |
| AKS            | 32      | 65.07     | 59.31     | 59.22           | 53.11         |
| Q-Frame        | 32      | 60.03     | 56.39     | 56.64           | 51.57         |
| **<u>DIG (Ours)</u>** | 32      | **<u>67.20</u>** | **<u>60.43</u>** | **<u>61.62</u>**       | **<u>53.24</u>**     |
| UNI            | 64      | 63.61     | 58.94     | 61.01           | 51.27         |
| AKS            | 64      | 66.59     | 60.66     | **<u>62.94</u>**       | 53.44         |
| Q-Frame        | 64      | 63.43     | 57.52     | 61.32           | 53.70         |
| **<u>DIG (Ours)</u>** | 64      | **<u>70.65</u>** | **<u>61.41</u>** | 62.61           | **<u>55.30</u>**     |
| UNI            | 128     | 67.31     | 61.86     | 65.89           | 54.84         |
| AKS            | 128     | 68.68     | 60.36     | 65.67           | **<u>55.93</u>**     |
| Q-Frame        | 128     | 68.03     | 59.76     | 65.91           | 54.81         |
| **<u>DIG (Ours)</u>** | 128     | **<u>71.40</u>** | **<u>63.13</u>** | **<u>66.78</u>**       | 55.69         |
| UNI            | 192     | 69.03     | 61.93     | 67.01           | 55.82         |
| AKS            | 192     | 69.93     | 61.26     | **<u>68.22</u>**       | 54.41         |
| **<u>DIG (Ours)</u>** | 192     | **<u>72.32</u>** | **<u>64.32</u>** | 68.00           | **<u>58.24</u>**     |
| UNI            | 256     | 69.15     | 61.48     | 66.31           | 57.12         |
| AKS            | 256     | 71.50     | 61.03     | 67.56           | 55.11         |
| **<u>DIG (Ours)</u>** | 256     | **<u>72.46</u>** | **<u>64.62</u>** | **<u>67.66</u>**       | **<u>57.76</u>**     |

### Ablations / Analysis

**Reward Assignment: LMM vs. CLIPScore**

下表选取 Table 2 中 32/128/256 frames 的代表性行。Base LMM 是 Qwen2.5-VL-7B；reward assigner 可以是 CLIPScore、Qwen2.5-VL-7B 或 Qwen2.5-VL-32B。

| Reward Assigner | #Frames | MLVU | LVB | VideoMME Short | VideoMME Medium | VideoMME Long |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| CLIPScore | 32 | 65.4 | 56.2 | 70.0 | 58.6 | 51.2 |
| Qwen2.5-VL-7B | 32 | 67.2 | 60.4 | 70.3 | **<u>61.6</u>** | **<u>53.2</u>** |
| Qwen2.5-VL-32B | 32 | **<u>67.9</u>** | **<u>60.6</u>** | **<u>72.6</u>** | 61.4 | 53.1 |
| CLIPScore | 128 | 69.6 | 61.0 | 73.3 | 64.0 | 55.8 |
| Qwen2.5-VL-7B | 128 | 71.4 | 63.1 | 74.9 | 66.8 | 55.7 |
| Qwen2.5-VL-32B | 128 | **<u>72.6</u>** | **<u>65.2</u>** | **<u>75.4</u>** | **<u>69.2</u>** | **<u>57.1</u>** |
| CLIPScore | 256 | 71.2 | 61.9 | 75.0 | 64.7 | 57.0 |
| Qwen2.5-VL-7B | 256 | 72.5 | **<u>64.6</u>** | 76.3 | 67.7 | 57.8 |
| Qwen2.5-VL-32B | 256 | **<u>74.3</u>** | 64.5 | **<u>76.8</u>** | **<u>68.9</u>** | **<u>59.1</u>** |

结论：LMM reward 普遍优于 CLIPScore，尤其在高帧数设置中更明显；更强的 Qwen2.5-VL-32B reward assigner 通常进一步提升 downstream accuracy。

**Query Identification Accuracy**

| LLM | MLVU LQ | MLVU GQ | MLVU Overall | LVB LQ | LVB GQ | LVB Overall | VideoMME LQ | VideoMME GQ | VideoMME Overall |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen3-Next-80B-A3B-Instruct | 87.02 | 38.26 | 78.52 | 97.53 | N/A | 97.53 | 89.13 | 65.76 | 83.90 |
| Llama-3.1-8B-Instruct | 93.65 | 24.01 | 81.50 | 98.20 | N/A | 98.20 | 96.99 | 34.24 | 82.95 |
| GPT-OSS-20B | 82.00 | 74.93 | 80.77 | 93.04 | N/A | 93.04 | 89.20 | 69.97 | 84.90 |
| DeepSeek-R1-Distill-Qwen-32B | 93.03 | 26.38 | 81.42 | 99.18 | N/A | 99.18 | 97.21 | 52.85 | 87.28 |

作者的解读是：LQ 识别通常比 GQ 更稳定，而这对最终性能更关键，因为把 LQ 错分成 GQ 会跳过 selection pipeline；把 GQ 错分成 LQ 更多是增加计算开销。

**CAFS Analysis**

| Observation | Value / Evidence | Implication |
| ---- | ---- | ---- |
| LongVideoBench 0-10 min videos | Avg. 47.9 r-frames | 视频信息量不随时长线性增长，固定帧数或固定 fps 都可能不合适 |
| LongVideoBench 10-20 min videos | Avg. 226.4 r-frames | CAFS 会根据 content density 动态增加候选帧 |
| MLVU 10-20 min videos | Avg. 12.7 min reduced to 180.8 r-frames | 约每 4.22s 一个 r-frame，说明 CAFS 有较强 context compression |
| CAFS vs. UNI inside DIG | Figure `qwen_dino.pdf` reports CAFS robustly outperforms uniform r-frame replacement | 说明收益不只是来自 reward/search，也来自内容自适应 candidate construction |

**Compute**

Inference latency 使用 Qwen2.5-VL-7B + uniform sampling，在 8 A100 节点上测得，单位是 minutes。

| Dataset | 8 frames | 16 frames | 32 frames | 64 frames | 128 frames | 192 frames | 256 frames |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| MLVU | 3.2 | 5.0 | 9.3 | 17.6 | 29.1 | 37.3 | 43.4 |
| LongVideoBench | 1.4 | 2.2 | 4.3 | 8.3 | 14.0 | 19.9 | 25.6 |
| VideoMME | 3.1 | 4.7 | 8.7 | 15.8 | 26.1 | 36.7 | 46.3 |

Frame selection overhead 单位也是 minutes。DIG 的最大成本来自 Reward Assignment (RA)。

| Dataset | AKS | Q-Frame | DIG QI | DIG CAFS | DIG RA | DIG VR | DIG Sum |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| MLVU | >=720 | 122.1 | 11.3 | 25.9 | 218.9 | 0.2 | 256.3 |
| LongVideoBench | >=720 | 34.5 | 7.6 | 20.8 | 110.4 | 0.1 | 138.9 |
| VideoMME | >=720 | 94.2 | 11.6 | 31.2 | 264.8 | 0.3 | 307.9 |

Query Identification 的效率收益：

| Dataset | Localized Query Percent | w/o QI | w/ QI | Change |
| ---- | ---- | ---- | ---- | ---- |
| MLVU | 82.8 | 295.7 | 256.3 | down 13.3% |
| LongVideoBench | 97.8 | 134.1 | 138.9 | up 3.6% |
| VideoMME | 77.0 | 384.2 | 307.9 | down 19.9% |

## Limitations & Caveats

- **Query classifier 并非完全可靠**：例如 Qwen3-Next-80B-A3B-Instruct 在 MLVU 的 GQ accuracy 只有 38.26%，说明 GQ/LQ 边界并不总是容易被 prompt-only LLM 捕捉。
- **RA 成本仍然不低**：DIG 虽然显著快于 AKS，但 RA 在 MLVU、LongVideoBench、VideoMME 上分别占 218.9、110.4、264.8 minutes，是主要瓶颈。
- **对强 reward LMM 有依赖**：LMM reward 明显优于 CLIPScore，但这也意味着方法收益依赖 reward assigner 的视觉推理能力与运行成本。
- **主实验排除了字幕和音频**：VideoMME 只使用视觉输入；对真实 multimodal video QA，音频、字幕和 OCR-like side information 可能改变 frame selection 的最优策略。
- **个别设置不总是最佳**：例如 Qwen2.5-VL-32B 在 8/16 frames 的 VideoMME Long 上，DIG 低于 UNI；Qwen2.5-VL-7B 在 128 frames 的 VideoMME Long 上，AKS 略高于 DIG。

## Concrete Implementation Ideas

1. 在现有 Video-LMM pipeline 前加一个轻量 **Query Router**：先判断 GQ/LQ，GQ 直接走 uniform sampling，LQ 才触发昂贵 selection。
2. 给 long-video indexing 系统预计算 DINOv2 相邻帧距离和 CAFS r-frame，在线只做 query-specific reward 和 refinement。
3. 把 reward assignment 做成可缓存的 frame-query scoring service，返回 JSON `{description, reward}`，并记录 reward distribution 方便调试错误案例。
4. 对高吞吐场景训练一个小模型近似 LMM reward，先用 LMM 离线生成 supervision，再用轻量 scorer 替代在线 RA。
5. 将 $wlen$ 从固定值改成 adaptive：根据 reward 峰值宽度、neighbor similarity 或 query type 子类动态决定扩展窗口。

## Open Questions / Follow-ups

- GQ/LQ 二分是否足够？一些 query 可能需要 sparse global evidence 加 localized detail，适合更细的 multi-label routing。
- 如果加入 subtitles、audio、ASR transcript，frame selection 是否还应由 visual feature peaks 主导？
- RA 能否用 temporal segment 而不是单帧评分，减少 single-frame bias？
- CAFS 的 prominence threshold 0.1 是否能跨 domain 稳定，还是需要按视频类型或 feature model 自适应？
- 在真实部署中，DIG 的额外 compute 与 accuracy gain 在什么用户场景下最划算？

> [!note]+
> DIG 启发性的地方主要在：**它没有学习一个最优采样策略，而是用一组经验规则把长视频压缩成更可能有用的帧。**

### 1. Query 二分本身是启发式

DIG 先把问题分成：

```text
Global Query：需要整体视频理解
Localized Query：答案集中在某些片段
```

然后规定：

```text
GQ -> uniform sampling
LQ -> CAFS + reward selection
```

这个判断很合理，但它不是严格理论推出来的，而是基于观察：

> 全局问题需要覆盖，局部问题需要定位。

所以这里是一个 high-level heuristic。

### 2. CAFS 切片也是启发式

CAFS 用 DINOv2 相邻帧特征差：

```text
相邻帧变化大 -> 可能是内容边界
```

然后取每个 segment 的 midpoint 作为代表帧。

这里有几个经验假设：

- DINOv2 feature distance 能反映内容变化；
- peak 可以作为 segment boundary；
- segment midpoint 可以代表整个片段；

### 3. Reward assignment 是 LMM-based heuristic

DIG 让 LMM 根据 query 给 r-frame 打 0–100 分。

这个 reward 不是 ground truth，也不是训练出来的 reward model，而是：

```text
LMM 根据语义理解判断这个帧/片段对回答问题有没有帮助
```

### 4. Reward refinement 规则也是启发式

DIG 后面用类似均值阈值化：

```text
R'_j = max(R_j - mean(R), 0)
```

保留正 reward 的片段，再向左右扩展固定窗口 `wlen=2`。

这里也有经验假设：

- 高于平均分的片段更有用；
- 迭代均值阈值化能筛掉噪声；
- 固定左右扩展窗口足够补上下文。


### 5. 最后 refined video 再 uniform sampling 也是折中启发

DIG 没有直接选最高分帧，而是先得到 refined video，再 uniform sampling。

这个设计隐含的想法是：

> 先用 reward 缩小范围，再用 uniform 保留局部时间覆盖。

这也是一个经验折中：既不完全相信 reward，也不完全 uniform。

## Citation

```bibtex
@misc{li2025dividethenground,
  title = {Divide, then Ground: Adapting Frame Selection to Query Types for Long-Form Video Understanding},
  author = {Li, Jialuo and Li, Bin and Li, Jiahao and Lu, Yan},
  year = {2025},
  eprint = {2512.04000},
  archivePrefix = {arXiv},
  primaryClass = {cs.CV},
  url = {https://arxiv.org/abs/2512.04000}
}
```
