---
数据集:
git commit:
创建时间: 2026-05-17 13:20
tags:
---
# EVI 相比 DIG 的改动记录

记录时间：2026-05-16 21:23 CST  
当前基准：`main` 分支 `fbdb0b2 add snapshot for every run`，叠加当前工作区未提交的 EVI/evidence_next 实验产物、`pipeline/evidence_refinement.py` 调整，以及当前文件系统中的 `logs/DIG-baseline` 对照结果。  
命名说明：本文里的 EVI 指当前仓库中以 `EVIDENCE` mode、`evidence_*` keyframes 和 `evidence_refinement.py` 实现的证据感知版本。

## 1. 总体差异

DIG 原始流程是两段式 query routing：

1. LLM 先把问题分为 `global` 或 `local`。
2. `global` 走全视频均匀采样。
3. `local` 走 CAFS r-frame、reward assignment、reward 区间裁剪，再在裁剪区间内均匀采样。

EVI 保留 DIG 的 CAFS 和 reward 基础，但把“是否 localized”扩展成更细的证据规划：

1. 新增 evidence planning：对每个问题输出结构化 `evidence_plan`。
2. 新增 6 类 evidence query type：`summary_global`、`single_moment`、`multi_event_temporal`、`counting`、`ocr_detail`、`negative_absence`。
3. 新增 policy knobs：`evidence_need`、`coverage`、`clip_context`、`density`、`requires_ocr`。
4. 新增 evidence-aware refinement：根据 evidence plan、DIG reward interval 和 uniform sampling 做混合预算。
5. 新增 `EVIDENCE` 评测模式：和 `DIG` / `UNI` 并列，通过 suffix 选择对应 keyframe JSON。
6. 新增 run artifact snapshot：把每次评测依赖的 keyframes 和 rewards 复制到 run 目录下，便于复现实验。

核心变化不是替换 DIG，而是在 DIG 的 reward distribution 上增加“问题需要什么证据”的控制层。EVI 会按问题类型决定更偏全局覆盖、多个片段、密集扫描、OCR 细节帧，还是回退到 DIG 的 reward interval。

## 2. 新增与修改的关键文件

| 文件 | 作用 | 与 DIG 的关系 |
|---|---|---|
| `utils.py` | 新增 `EVIDENCE_PLANNING_PROMPT`，`VideoDataset` 支持 evidence 字段 | 在原 DIG prompt/data loader 上扩展证据规划输入输出 |
| `pipeline/evidence_planning.py` | 调 LLM 生成并规范化 evidence plan | 替代 DIG 的二分类 query type，输出更细粒度策略 |
| `pipeline/evidence_refinement.py` | 按 evidence plan + DIG interval + uniform 生成 keyframes | 是 EVI 的核心选帧实现 |
| `scripts/evidence_planning.sh` | 运行 evidence planning，输出 `data/<dataset>_evidence_meta.json` | 新增离线规划步骤 |
| `scripts/evidence_refinement.sh` | 运行 evidence refinement，输出 `keyframes/*_<suffix>.json` | 新增 EVI keyframe 生成入口 |
| `scripts/eval/qwen25vl.sh` | 支持 `DIG`、`EVIDENCE`、`UNI` 三种模式 | 评测入口从 DIG/UNI 扩展到 EVI |
| `scripts/eval/snapshot_run_artifacts.py` | 复制 keyframes/rewards 到 run artifacts | 新增实验追踪能力 |
| `scripts/eval/summarize_run.py` | 汇总 run 结果和 breakdown | 新增结果记录能力 |
| `scripts/analysis/compare_videomme_samples.py` | 对比 DIG/EVI 每个样本的预测和正确性 | 新增误差分析工具 |
| `data/videomme_evidence_meta.json` | VideoMME 的 evidence plan 缓存 | EVI 的规划输入 |

## 3. Evidence Planning

EVI 新增 `pipeline/evidence_planning.py`，用 LLM 只根据题目、选项和数据集 task type 预测需要的视觉证据类型。

规划输出字段：

| 字段 | 含义 |
|---|---|
| `query_type` | 六类证据问题类型之一 |
| `evidence_need` | 下游选帧需求：`global_coverage`、`single_clip`、`multiple_clips`、`dense_scan`、`detail_frames` |
| `coverage` | 覆盖范围：`low`、`medium`、`high` |
| `clip_context` | 片段上下文窗口：`narrow`、`medium`、`wide` |
| `density` | 片段内部采样密度：`sparse`、`medium`、`dense` |
| `requires_ocr` | 是否需要 OCR/细节文字能力 |
| `brief_reason` | 简短理由，便于后续分析 |
| `policy_source` / `policy_rule` / `policy_version` | 记录 plan 是否被规则修正，以及规则来源 |

规划逻辑有两层：

1. LLM 先基于 prompt 输出初始 plan。
2. 规则层再做保守修正，例如：
   - `OCR Problems` 或题目含 text/sign/subtitle/label 等 cue 时，强制 `ocr_detail`。
   - `Counting Problem` 强制 `counting`。
   - `Information Synopsis` 强制 `summary_global`。
   - temporal cue 或 temporal task 中，如果 LLM 给了 `single_moment`，会提升为 `multi_event_temporal`。
   - reasoning/comparison/change 类问题也倾向提升为 `multi_event_temporal`。

当前 `data/videomme_evidence_meta.json` 共 2700 条，分布如下：

| evidence_query_type | 数量 |
|---|---:|
| `multi_event_temporal` | 1037 |
| `single_moment` | 514 |
| `summary_global` | 487 |
| `counting` | 278 |
| `ocr_detail` | 243 |
| `negative_absence` | 141 |

policy 来源分布：

| policy_source | 数量 |
|---|---:|
| `task_type` | 1133 |
| `llm` | 1111 |
| `question_cue` | 456 |

## 4. Evidence Refinement

DIG 的 `pipeline/video_refinement.py` 只根据 `query_type == local/global` 分支：

| DIG 分支 | 选帧行为 |
|---|---|
| `global` | 全视频 `np.linspace` 均匀采样 |
| `local` | 对 reward 归一化，找非零/高分 reward 区间，用 `wlen=2` 扩展，再在合并区间内采样 |

EVI 的 `pipeline/evidence_refinement.py` 则拆成三种 frame source：

| frame source | 来源 | 用途 |
|---|---|---|
| `evidence` | 按 evidence policy 从 reward 中挑 top interval | 服务具体证据需求，如单片段、多事件、OCR、计数 |
| `dig` | 复用 DIG 的 reward interval 逻辑 | 保留 DIG 已验证的局部定位能力 |
| `uniform` | 全视频均匀采样 | 保留全局覆盖，降低局部过拟合 |

### 4.1 默认混合预算

EVI 的 hybrid strategy 会按 `query_type` 分配 `k` 帧预算：

| query_type | evidence | dig | uniform | 说明 |
|---|---:|---:|---:|---|
| `summary_global` | 0.00 | 0.25 | 0.75 | 以全局覆盖为主，少量保留 reward 定位 |
| `negative_absence` | 0.00 | 0.15 | 0.85 | 排除/缺失类问题更依赖全局覆盖 |
| `single_moment` | 0.55 | 0.20 | 0.25 | 以证据片段为主，保留 DIG 和全局兜底 |
| `multi_event_temporal` | 0.60 | 0.20 | 0.20 | 多事件/时序问题增加多个片段覆盖 |
| `counting` | 0.30 | 0.15 | 0.55 | 计数需要密集扫描和全局覆盖 |
| `ocr_detail` | 0.35 | 0.15 | 0.50 | OCR 需要细节帧，也保留较多上下文 |

特殊规则：

- `single_moment` 且 `k <= 8` 时，预算改为 `evidence=0.75`、`dig=0.00`、`uniform=0.25`，让小帧数更集中在最相关片段。
- 当前工作区新增规则：`counting` 和 `ocr_detail` 在 `k < 128` 时直接使用 `dig=1.00`，避免小帧数下 dense/OCR policy 过度分散帧预算。
- 如果 `requires_ocr=true`，budget 计算时按 `ocr_detail` 处理。

### 4.2 各类型 interval 策略

EVI 仍然使用 reward 分数作为定位基础，但不同证据类型的 top interval 数量、间距和上下文不同：

| 类型 | interval 策略 |
|---|---|
| `ocr_detail` | 选高分细节帧，窗口默认较窄，优先保留相邻上下文 |
| `multi_event_temporal` | 选多个高分点，设置 min_gap，避免只落在同一小片段 |
| `single_moment` | 小 `k` 只选最核心片段，大 `k` 允许更多局部片段 |
| `counting` | 选较多高分点，配合 dense/high coverage |
| `summary_global` / `negative_absence` | 不直接构造 evidence interval，主要走 DIG 少量 interval + uniform |

最后通过 `clamp_and_fill` 保证：

- frame index 不越界；
- 去重后不足 `k` 时用 uniform 补齐；
- 超过 `k` 时按均匀下采样保留；
- 最终输出长度稳定为 `k`。

### 4.3 当前未提交的 refinement 调整

当前工作区相对 `fbdb0b2` 修改了 `pipeline/evidence_refinement.py`：

1. 对 `counting` / `ocr_detail` 且 `k < 128` 的问题，hybrid budget 改为 100% DIG。
2. `hybrid_evidence_refine_item` 中先累计 `targeted_frames`，只有存在 evidence/DIG 目标帧后才追加 uniform budget。
3. 如果没有任何 targeted evidence，则直接用全视频 uniform 的完整 `k` 帧兜底。

这次调整的直觉是：当证据策略找不到可靠目标片段时，不应只花掉一个局部预算后再隐式补齐，而应明确退回全局覆盖；同时，小帧数的 OCR/counting 更容易因为密集扫描导致预算被打散，所以暂时回退到 DIG。

## 5. 评测入口变化

`scripts/eval/qwen25vl.sh` 现在支持：

| mode | keyframes |
|---|---|
| `UNI` | 不使用 keyframe JSON，`use_uniform=True` |
| `DIG` | `keyframes/<model>_<dataset>_<frames>.json` |
| `EVIDENCE` | `keyframes/<model>_<dataset>_<frames>_<EVIDENCE_KEYFRAMES_SUFFIX>.json` |

默认 `EVIDENCE_KEYFRAMES_SUFFIX=evidence`。当前最新运行显式使用了 `evidence_next`：

```text
logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_082343/
keyframes/Qwen2.5-VL-7B-Instruct_videomme_{8,16,32,64,128,192,256}_evidence_next.json
```

每次非 UNI 评测会调用 `scripts/eval/snapshot_run_artifacts.py`，把当次使用的 keyframes 和 reward 文件快照到：

```text
<run_root>/artifacts/keyframes/
<run_root>/artifacts/rewards/
<run_root>/artifacts/manifest.json
```

这样即使根目录 keyframes 后续被覆盖，run 目录仍保留当次输入。

## 6. 当前工作区状态

当前 `git status --short` 中与 EVI 相关的变化：

| 类型 | 路径/模式 | 说明 |
|---|---|---|
| modified | `pipeline/evidence_refinement.py` | 当前 `evidence_next` 策略调整 |
| deleted | `keyframes/*_evidence_guarded.json` for 8/16/32/64/128 | 旧 guarded 版本被移除 |
| untracked | `keyframes/*_evidence_next.json` for 8/16/32/64/128/192/256 | 新一轮 EVI keyframes |
| untracked | `logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_082343/` | 最新 EVI VideoMME 评测日志、samples、artifacts |
| modified/untracked | `logs/DIG-baseline/` | 当前用于对比的 DIG baseline，包含 8/16/32/64/128/192/256 完整结果 |
| modified | `pipeline/__pycache__/*.pyc` | Python 缓存文件变化，不属于方法设计 |

建议后续如果要提交代码，只提交源码、文档和必要实验产物；`__pycache__` 一般不应进入方法记录。

## 7. VideoMME 最新结果对比

对比对象：

| 项 | DIG | EVI |
|---|---|---|
| run | `logs/DIG-baseline` | `logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_082343` |
| model | `Qwen2.5-VL-7B-Instruct` | `Qwen2.5-VL-7B-Instruct` |
| dataset | `videomme` | `videomme` |
| samples | 2700 | 2700 |
| keyframe suffix | none | `evidence_next` |

说明：`logs/DIG-baseline/manifest.json` 的 `paths.run_root` 仍保留原始 run 名 `logs/Qwen2.5-VL-7B-Instruct_DIG_videomme_20260515_013814`，但本次文档对比以当前 `logs/DIG-baseline` 目录下的结果文件为准。

整体分数：

| frames | DIG | EVI | EVI - DIG |
|---:|---:|---:|---:|
| 8 | 55.1111 | 55.8519 | +0.7407 |
| 16 | 58.8148 | 58.1852 | -0.6296 |
| 32 | 61.5556 | 61.1852 | -0.3704 |
| 64 | 63.8148 | 64.9259 | +1.1111 |
| 128 | 65.5926 | 66.8148 | +1.2222 |
| 192 | 66.7407 | 68.0000 | +1.2593 |
| 256 | 67.2593 | 68.0000 | +0.7407 |

Video Type 对比，256 帧：

| video type @256 | DIG | EVI | EVI - DIG |
|---|---:|---:|---:|
| short | 76.8% | 77.1% | +0.3 |
| medium | 66.8% | 68.1% | +1.3 |
| long | 58.2% | 58.8% | +0.6 |

Task category 对比，256 帧：

| task category @256 | DIG | EVI | EVI - DIG |
|---|---:|---:|---:|
| Temporal Perception | 67.3% | 72.7% | +5.4 |
| Spatial Perception | 66.7% | 66.7% | +0.0 |
| Attribute Perception | 79.7% | 80.2% | +0.5 |
| Action Recognition | 66.8% | 68.4% | +1.6 |
| Object Recognition | 72.9% | 72.3% | -0.6 |
| OCR Problems | 74.1% | 76.3% | +2.2 |
| Counting Problem | 48.1% | 48.5% | +0.4 |
| Temporal Reasoning | 54.8% | 58.8% | +4.0 |
| Spatial Reasoning | 78.6% | 78.6% | +0.0 |
| Action Reasoning | 61.8% | 60.0% | -1.8 |
| Object Reasoning | 62.6% | 63.9% | +1.3 |
| Information Synopsis | 82.4% | 82.7% | +0.3 |

目前结果的直接观察：

- EVI 在 7 个帧数设置中有 5 个超过 DIG：8/64/128/192/256 分别为 +0.74、+1.11、+1.22、+1.26、+0.74。
- 小帧数并非稳定收益：8 帧有提升，但 16/32 帧略低于 DIG。
- 256 帧下提升最明显的是 Temporal Perception（+5.4）和 Temporal Reasoning（+4.0），说明多事件/时序类 evidence policy 在高帧数下开始吃到更多上下文预算。
- OCR Problems 在 256 帧有 +2.2，说明 `k >= 128` 后 `ocr_detail` 不再回退纯 DIG，细节帧策略可能开始带来收益。
- Action Reasoning 在 256 帧回退 -1.8，Object Recognition 回退 -0.6；后续需要看 per-sample case，判断是 evidence plan 误分，还是 hybrid budget 稀释了 DIG 原本命中的局部片段。
- Counting Problem 在 192 帧曾有 +3.7，但 256 帧只剩 +0.4；计数类策略可能不是越多帧越稳定，需要单独做 budget ablation。

## 8. 复现实验命令备忘

Evidence planning：

```bash
export MODEL_NAME=<planner_model>
bash scripts/evidence_planning.sh videomme
```

Evidence keyframe generation：

```bash
export MODEL_NAME=/ssd_2t/yifan/shared/models/Qwen2.5-VL-7B-Instruct
export FRAMES_LIST="8 16 32 64 128 192 256"
export OUTPUT_SUFFIX=evidence_next
bash scripts/evidence_refinement.sh videomme
```

Evidence evaluation：

```bash
export MODEL_NAME=/ssd_2t/yifan/shared/models/Qwen2.5-VL-7B-Instruct
export LOG_SAMPLES=1
export FRAMES_LIST_OVERRIDE="8 16 32 64 128 192 256"
export EVIDENCE_KEYFRAMES_SUFFIX=evidence_next
bash scripts/eval/qwen25vl.sh videomme EVIDENCE
```

DIG baseline evaluation：

```bash
export MODEL_NAME=/ssd_2t/yifan/shared/models/Qwen2.5-VL-7B-Instruct
export LOG_SAMPLES=1
export FRAMES_LIST_OVERRIDE="8 16 32 64 128 192 256"
bash scripts/eval/qwen25vl.sh videomme DIG
```

Per-sample 对比：

```bash
python scripts/analysis/compare_videomme_samples.py \
  --dig logs/DIG-baseline/samples/256/samples_videomme.jsonl \
  --evidence logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_082343/samples/256/samples_videomme.jsonl \
  --evidence_meta data/videomme_evidence_meta.json \
  --output_prefix outputs/analysis/videomme_DIG_vs_EVIDENCE_256_evidence_next
```

## 9. 后续记录建议

1. 单独做 ablation：`legacy`、`hybrid`、`evidence_next`、`guarded`、纯 DIG budget。
2. 对 16/32 帧回退样本做 per-sample 对比，确认负收益来自 policy 误分还是预算切分。
3. 重点看 `multi_event_temporal`、`counting`、`ocr_detail` 三类的 EVI-only 和 DIG-only case。
4. 对 192 和 256 的 counting case 做单独分析，因为 192 提升明显但 256 提升变小。
5. 如果 EVI 继续保留 `evidence_next`，建议把 suffix、策略版本和主要 policy 改动写进 manifest，避免后续只凭文件名区分实验。

## 10. Evidence Confidence-Aware Budgeting

新增 `adaptive` refinement strategy，用于验证“固定 hybrid budget 是否导致小帧数不稳”。旧 `hybrid` / `legacy` 保持可复现，脚本默认仍是 `hybrid`；新实验需要显式设置：

```bash
export MODEL_NAME=/ssd_2t/yifan/shared/models/Qwen2.5-VL-7B-Instruct
export FRAMES_LIST="8 16 32 64 128 192 256"
export EVIDENCE_STRATEGY=adaptive
export OUTPUT_SUFFIX=evidence_adaptive
export DEBUG_DIR=outputs/debug/evidence_adaptive
bash scripts/evidence_refinement.sh videomme
```

`adaptive` 会为每个样本从 reward 分布计算 confidence：

| 字段 | 含义 |
|---|---|
| `has_reward` | 是否存在 reward 且 boundaries 可用于定位 |
| `top_gap` | 归一化 reward 的 top 1-top 2 gap |
| `entropy` | 归一化 reward 分布熵 |
| `active_count` | 非零 reward 段数 |
| `high_peak_count` | 归一化 reward >= 0.70 的高峰段数 |
| `bucket` | `missing`、`flat`、`weak`、`moderate`、`clear` |

初始阈值：

| bucket | 规则 |
|---|---|
| `missing` | 无 reward 或 boundaries 不匹配 |
| `flat` | `top_gap < 0.03` 且 `entropy > 0.95` |
| `clear` | `top_gap >= 0.12` 或 `entropy <= 0.88` |
| `moderate` | `top_gap >= 0.05` 或 `entropy <= 0.94` |
| `weak` | 其他情况 |

预算策略：

- `missing` 由于没有可定位 reward，直接 full uniform 兜底。
- `flat` 在 `k < 64` 时不再显式引入 uniform，而是 full DIG guard；`k >= 64` 仍 full uniform。
- `summary_global` / `negative_absence` 在 `k >= 64` 时以 uniform 为主，weak reward 时 full uniform；`k < 64` 时改为 DIG guard。
- `k < 64` 时不主动分配 uniform 预算：除 `missing` 兜底外，所有可定位样本都在 evidence/DIG 之间分配，避免小帧数被 UNI 稀释。
- `multi_event_temporal` 只有在 `moderate/clear` 且 `high_peak_count >= 2` 时多片段 evidence-heavy，否则 DIG-heavy。
- `single_moment` 只有 clear peak 才使用 evidence-heavy budget；moderate 降低 evidence 比例；low-budget weak 退回 DIG。
- `counting` / `ocr_detail` 只有 `k >= 128` 且 reward 至少 moderate 时启用 evidence；否则使用 DIG/UNI guard。

如果设置 `DEBUG_DIR`，每个 `k` 会额外输出 JSONL sidecar，记录：

```text
videoid/question/query_type/k/confidence/budgets/fallback_reason/selected_strategy
```

首轮验收目标：`evidence_adaptive` 在 16/32 帧不低于当前 `evidence_next`，64/128/192 继续保持正收益，256 不明显回退。该版本不使用 DIG/EVI 正误标签拟合阈值，避免变成 VideoMME-specific calibration。

## 11. adaptive 20260516_235720 完整评测记录

记录时间：2026-05-17 CST  
run：`logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_235720`  
模式：`EVIDENCE`，keyframe suffix 为 `evidence_adaptive`。  
说明：该 run 使用低帧数 no-uniform 修正版 adaptive keyframes；`64/128/192/256` 仍沿用当前 adaptive 高帧策略，其中 `flat` bucket 在 `k >= 64` 仍为 full uniform。

### 11.1 对 DIG baseline 的整体结果

| frames | DIG | adaptive | adaptive - DIG | oracle | evidence-only | DIG-only |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 55.1111 | 55.4815 | +0.3704 | 59.0370 | 106 | 96 |
| 16 | 58.8148 | 59.4074 | +0.5926 | 62.3333 | 95 | 79 |
| 32 | 61.5556 | 60.8519 | -0.7037 | 64.1852 | 71 | 90 |
| 64 | 63.8148 | 63.8519 | +0.0371 | 68.7778 | 134 | 133 |
| 128 | 65.5926 | 67.2222 | +1.6296 | 71.0370 | 147 | 103 |
| 192 | 66.7407 | 67.0370 | +0.2963 | 71.0741 | 117 | 109 |
| 256 | 67.2593 | 68.0370 | +0.7778 | 71.8889 | 125 | 104 |

直接观察：

- adaptive 在 7 个帧数中有 6 个超过 DIG，平均提升约 +0.43。
- 最强收益在 128 帧：+1.63，且 evidence-only 147 vs DIG-only 103，是本轮最稳定的正向信号。
- 8/16 帧相比上一轮低帧数 uniform 混合策略明显恢复，说明 `k < 64` 不主动引入 uniform 是正确方向。
- 32 帧仍然低于 DIG -0.70，说明 32 帧不能简单复用 8/16 的 low-budget policy。
- 64/192 只有轻微正收益，且低于上一版 `evidence_next`，主要需要看高帧 fallback 和 `flat` bucket。

### 11.2 与上一版 evidence_next 的对比

上一版对照 run：`logs/Qwen2.5-VL-7B-Instruct_EVIDENCE_videomme_20260516_082343`。

| frames | evidence_next | adaptive | adaptive - evidence_next |
|---:|---:|---:|---:|
| 8 | 55.8519 | 55.4815 | -0.3704 |
| 16 | 58.1852 | 59.4074 | +1.2222 |
| 32 | 61.1852 | 60.8519 | -0.3333 |
| 64 | 64.9259 | 63.8519 | -1.0741 |
| 128 | 66.8148 | 67.2222 | +0.4074 |
| 192 | 68.0000 | 67.0370 | -0.9630 |
| 256 | 68.0000 | 68.0370 | +0.0370 |

结论：adaptive 不是全面优于 `evidence_next`。它改善了 16 和 128，256 基本持平，但 64/192 明显回退。因此目前 adaptive 更像一个有价值的诊断方向，而不是最终策略。

### 11.3 关键 task category 信号

128 帧的主要正收益：

| task category @128 | adaptive - DIG |
|---|---:|
| Temporal Perception | +14.5 |
| Temporal Reasoning | +2.8 |
| Action Recognition | +2.2 |
| Object Reasoning | +2.4 |
| OCR Problems | +2.2 |
| Counting Problem | +2.6 |

256 帧的主要正负收益：

| task category @256 | adaptive - DIG |
|---|---:|
| Temporal Perception | +5.4 |
| Temporal Reasoning | +4.0 |
| Action Recognition | +3.5 |
| OCR Problems | +3.6 |
| Action Reasoning | -3.2 |

32 帧的主要回退：

| task category @32 | adaptive - DIG |
|---|---:|
| Action Recognition | -3.8 |
| Spatial Reasoning | -5.4 |
| Temporal Perception | +9.1 |

32 帧虽然 Temporal Perception 很强，但 Action Recognition 和 Spatial Reasoning 的回退抵消了收益。

### 11.4 按 evidence query type 的信号

| evidence query type @128 | adaptive - DIG |
|---|---:|
| `multi_event_temporal` | +2.80 |
| `negative_absence` | +2.13 |
| `counting` | +1.80 |
| `single_moment` | +1.36 |
| `ocr_detail` | +0.82 |
| `summary_global` | -0.41 |

| evidence query type @256 | adaptive - DIG |
|---|---:|
| `ocr_detail` | +2.47 |
| `negative_absence` | +2.13 |
| `single_moment` | +1.56 |
| `multi_event_temporal` | +0.48 |
| `counting` | +0.36 |
| `summary_global` | -0.41 |

总结：adaptive 的主要有效区域是 temporal、OCR/detail、single moment 和 negative/absence；`summary_global` 基本没有收益，甚至略负。

### 11.5 Debug bucket 观察

按 debug bucket 对比 DIG：

| bucket | 关键现象 |
|---|---|
| `clear` | 128 帧 +3.8，192 帧 +2.4，256 帧 +1.4，是 adaptive 的主要收益来源 |
| `moderate` | 128 帧 +0.8，256 帧 +1.7，但 32 帧 -2.2，低帧数仍不稳 |
| `missing` | 与 DIG 完全一致，因为该分支 full uniform 兜底，evidence-only/DIG-only 都为 0 |
| `flat` | 高帧数明显伤害：64 帧 -4.6，192 帧 -2.8，256 帧 -2.5 |
| `weak` | 样本少，128/256 有小幅正收益，但不应作为主要策略依据 |

最重要的问题是 `reward_flat`：

| frames | reward_flat adaptive - DIG |
|---:|---:|
| 64 | -4.6 |
| 192 | -2.8 |
| 256 | -2.5 |

当前高帧数 `flat -> full uniform` 的策略是明显坏分支。flat 不应简单解释为“需要全局均匀覆盖”，更可能表示 reward model 分不出可靠峰值；此时应该优先保留 DIG guard。

### 11.6 当前结论和下一步

当前结论：

- confidence-aware budgeting 是有潜力的，尤其 128 帧结果证明它能增强 temporal 和局部证据类问题。
- 低帧数 no-uniform 修正有效，8/16 从旧 adaptive 的明显掉分恢复到超过 DIG。
- adaptive 目前仍不是最终版本：32、64、192 不稳定，且没有整体超过 `evidence_next`。

下一步建议：

1. 把 `flat` 的高帧数策略从 full uniform 改为 DIG-heavy，例如 `evidence=0.00, dig=0.75, uniform=0.25`，或直接 full DIG。
2. 单独为 32 帧设计 policy，不要和 8/16 共用：对 `multi_event_temporal` 和 `single_moment` 的 moderate 分支降低 evidence 比例。
3. 保留 128 帧现有策略作为强正向参考，避免一刀切改坏。
4. 后续论文叙事可以强调：fixed evidence budget 不稳定，reward confidence 可以发现何时 evidence policy 有效，但 flat/ambiguous reward 需要 conservative fallback。

