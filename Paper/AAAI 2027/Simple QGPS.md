---
创建时间: 2026-07-20 21:03
tags:
---
是的，我认为这个版本的思路明显更清晰，也更合理。它把三个原本有些纠缠的概念分工得很干净：

| 核心问题 | 对应机制 |
|---|---|
| 哪些帧与问题直接相关？ | 候选相关性 $r_i$ |
| 哪些尚未覆盖的位置更重要？ | 目标权重 $w_j=\operatorname{softmax}(r_j/\tau)$ |
| 哪些证据已经被覆盖、后续应降低优先级？ | 动态残余协方差 $\Sigma^{(b)}$ |

这样，整个方法可以用一句非常自然的话讲清楚：

> **固定的时间协方差描述候选帧之间的冗余关系，查询相关性确定哪些证据值得获取，而 progressive update 在每次选择后抑制已经解释的证据。**

相比原版本，它有几个实质性优势。
**相比原版本，它有几个实质性优势。**
第一，模块职责更明确。原版本让 $r$ 同时决定 spectral density、target weights 和 candidate acquisition，审稿人很容易问：“为什么同一个 relevance signal 要进入三个位置？是不是重复使用、甚至重复计算相关性？”简化后，$r$ 只保留两个语义不同且容易解释的作用：

$$
w_j=\operatorname{softmax}(r_j/\tau)
$$

回答“覆盖哪里重要”，而

$$
a_b(i)=r_i g_b(i)
$$

回答“当前被选中的帧本身是否相关”。两者一个作用于 coverage target，一个作用于 acquisition candidate，分工清楚，不再显得重复。

第二，时间结构与查询语义被合理解耦。固定的 temporal basis $U_m$ 负责描述长视频候选序列中的平滑时间结构：

$$
\Sigma^{(0)}
=
\frac{N}{m}U_mU_m^\top,
$$

它只回答候选帧之间“谁和谁可能提供重叠证据”。查询相关性则回答“这些证据对当前问题是否有价值”。这比让 relevance 同时承担结构建模和语义筛选更自然：

$$
\underbrace{\text{Temporal covariance}}_{\text{redundancy structure}}
+
\underbrace{\text{Relevance}}_{\text{query utility}}
+
\underbrace{\text{Progressive update}}_{\text{residual coverage}}.
$$

第三，核心创新更突出。现在 reviewer 一眼就能看出 Q-GPS 与静态排序的区别不在于一个复杂的 spectral weighting trick，而在于：

$$
\Sigma^{(0)}
\rightarrow
\Sigma^{(1)}
\rightarrow
\cdots
\rightarrow
\Sigma^{(B)},
$$

即每次选帧以后更新 residual coverage state，重新评估剩余候选帧。这样论文可以集中讲：

> **Frame utility should depend on what has already been selected.**

这正是 progressive residual coverage 的核心动机，也是比 spectral density 更容易被理解和认可的创新点。

第四，理论链条更短、更扎实。新的方法只需要建立下面这条推导：

$$
\Sigma^{(0)}
=
\frac{N}{m}U_mU_m^\top
$$

提供 temporal coverage structure；

$$
g_b(i)
=
\frac{
\sum_{j\in\mathcal U_b}
w_j\bigl(\Sigma_{ji}^{(b)}\bigr)^2
}{
\Sigma_{ii}^{(b)}+\nu
}
$$

是选择 $i$ 带来的精确 weighted variance reduction；

$$
a_b(i)=r_i g_b(i)
$$

保证被获取的帧自身与问题相关；

$$
\Sigma^{(b+1)}
=
\Sigma^{(b)}
-
\frac{
\Sigma_{:,i}^{(b)}\Sigma_{i,:}^{(b)}
}{
\Sigma_{ii}^{(b)}+\nu
}
$$

更新后续 residual coverage。

原来的 graph-periodogram、modal activation、spectral floor $\eta_s$ 和 query-conditioned modal variance 都可以删除。Method 更短，但核心数学反而更突出。

第五，这种简化与实验完全一致。Strict Uniform spectral density 与论文 Full 的九格平均分别是：

$$
62.7662\%
\quad\text{和}\quad
62.7356\%,
$$

说明删除 relevance-conditioned modal weights 没有造成性能损失。与此同时，取消 candidate relevance calibration 会明显降低准确率。这意味着实验真正支持的故事就是：

> relevance 的关键作用是引导 progressive coverage，而不是调制 temporal spectrum。

所以这不是为了写作方便而主观简化，而是依据消融结果进行的 method refinement。

第六，模型复杂度和超参数也更合理。简化后可以删除：

- spectral activation $\alpha_\ell=\mathbf u_\ell^\top\mathbf r$；
- modal density $p_\ell$；
- spectral floor $\eta_s$；
- spectral-floor sensitivity analysis；
- `w/o spectral shaping` 这一缺乏严格支持的主消融。

最终核心超参数只剩：

- relevance temperature $\tau$；
- rank multiplier $c_{\mathrm{rank}}$；
- observation noise $\nu$。

这会减少审稿人对“为什么需要这么多设计选择”的疑问。

更重要的是，Q-GPS 这个名字仍然成立。虽然 covariance initialization 不再由 query 调制，但 selection 仍然是 query-guided：

$$
w_j=w_j(\mathbf r),
\qquad
a_b(i)=r_i g_b(i).
$$

因此方法仍然可以叫：

> **Query-Guided Progressive Selection**

最终最简洁的论文故事可以是：

> Q-GPS represents temporal redundancy with a fixed low-rank covariance and performs relevance-grounded progressive selection. At each step, it selects a directly relevant frame that maximally reduces the query-weighted residual variance of the unselected candidates, then updates the covariance to suppress already covered evidence.

我唯一要强调的条件是：这必须成为真正的最终方法，而不能只修改论文文字。也就是说：

- `Uniform spectral density` 应当升级为新的 canonical Full Q-GPS；
- 论文 Full 行应替换成这组结果；
- `w/o progressive update`、`w/o covered-target masking`、`Uniform target weights` 和 `w/o candidate relevance calibration` 都必须基于相同的 uniform temporal covariance；
- 不能再拿保留 query-conditioned spectrum 的旧消融直接与新 Full 比较。

只要把这层实验一致性补齐，我认为新的版本在方法逻辑、实验证据和 reviewer-facing presentation 三方面都优于原来的 query-conditioned spectral-density 版本。

可以。当前代码中，这个简化方法对应的可运行 strategy 仍然是：

```text
qgps_uniform_spectral_density
```

也就是：

- 固定的 uniform temporal spectral covariance；
- 保留 target relevance weighting；
- 保留 candidate relevance calibration；
- 保留 progressive covariance update；
- 使用 low-rank backend。

下面两组命令都使用：

- GPU `0,1,2,3,4,5,6,7`
- BLIP 2-ITM scored resources
- uniform `512f` candidate pool
- K= `8/16/32`
- $\tau=0.15$
- temporal-only 1-hop
- rank multiplier `2`
- observation noise `0.05`
- `INPUT_STAGE=scored`，不会重新运行 BLIP 2 scoring
- 三个数据集顺序为 VideoMME → LongVideoBench → MLVU
- 不手动设置 `RUN_ID`，由仓库命名逻辑生成 canonical run ID

我已经对两个 backend × 三个数据集全部执行过 `DRY_RUN`，6/6 均通过。

## LLaVA-OneVision，8 卡，三个数据集

结果将写入：

```text
logs/llava-onevision-qwen2-7b-ov/runs/
```

汇总写入：

```text
logs/llava-onevision-qwen2-7b-ov/summary.tsv
```

直接运行：

```bash
bash <<'BASH'
set -euo pipefail

RUN_TAG="${RUN_TAG:-$(date -u +%Y%m%d_%H%M%S)}"

COMMON_ENV=(
  INPUT_STAGE=scored
  REQUIRE_REUSE_SCORED=true
  RUN_SELECTION=true
  RUN_INFERENCE=true
  QGPS_SELECTION_STRATEGY=qgps_uniform_spectral_density
  QGPS_RELEVANCE_BACKEND=blip2-itm-vit-g
  CANDIDATE_POOL=512f
  FRAMES_LIST="8 16 32"
  QGPS_RELEVANCE_TAU=0.15
  QGPS_TEMPORAL_EDGE_WEIGHT=1.0
  QGPS_TEMPORAL_HOPS=1
  QGPS_TEMPORAL_HOP_WEIGHTING=normalized_inverse_hop
  QGPS_SPECTRAL_RANK_MULTIPLIER=2
  QGPS_SPECTRAL_ETA=1e-4
  QGPS_OBSERVATION_NOISE=0.05
  INFERENCE_BACKEND=llava_onevision
  MODEL_NAME=/ssd2_4t/yifan/shared/models/llava-onevision-qwen2-7b-ov
  PIPELINE_GPU_IDS=0,1,2,3,4,5,6,7
  INFERENCE_GPU_IDS=0,1,2,3,4,5,6,7
  NUM_PROCESSES=8
  LOGS_DIR=logs/llava-onevision-qwen2-7b-ov/runs
  SUMMARY_BASELINE_DIR=logs/llava-onevision-qwen2-7b-ov/baseline
  SUMMARY_COMPARE_ALL_BASELINES=1
  SKIP_COMPLETED_FRAMES=true
)

echo "[INFO] LLaVA-OneVision sweep RUN_TAG=${RUN_TAG}"

for DATASET in videomme longvideobench mlvu; do
  echo "[INFO] Starting LLaVA-OneVision ${DATASET}"
  env \
    "${COMMON_ENV[@]}" \
    RUN_TAG="${RUN_TAG}" \
    RESOURCE_DIR="resources/${DATASET}/uniform_512f/blip2-itm-vit-g" \
    bash pipeline/runners/run_qgps_end_to_end.sh "${DATASET}"
done

echo "[INFO] LLaVA-OneVision three-dataset sweep complete"
BASH
```

生成的 run 名大致为：

```text
videomme_blip2_itm_vit_g_qgps_uniform_spectral_density_tau0p15_512f_<RUN_TAG>
longvideobench_blip2_itm_vit_g_qgps_uniform_spectral_density_tau0p15_512f_<RUN_TAG>
mlvu_blip2_itm_vit_g_qgps_uniform_spectral_density_tau0p15_512f_<RUN_TAG>
```

## InternVL 3-8 B，8 卡，三个数据集

结果将写入：

```text
logs/InternVL3-8B/runs/
```

汇总写入：

```text
logs/InternVL3-8B/summary.tsv
```

直接运行：

```bash
bash <<'BASH'
set -euo pipefail

RUN_TAG="${RUN_TAG:-$(date -u +%Y%m%d_%H%M%S)}"

COMMON_ENV=(
  INPUT_STAGE=scored
  REQUIRE_REUSE_SCORED=true
  RUN_SELECTION=true
  RUN_INFERENCE=true
  QGPS_SELECTION_STRATEGY=qgps_uniform_spectral_density
  QGPS_RELEVANCE_BACKEND=blip2-itm-vit-g
  CANDIDATE_POOL=512f
  FRAMES_LIST="8 16 32"
  QGPS_RELEVANCE_TAU=0.15
  QGPS_TEMPORAL_EDGE_WEIGHT=1.0
  QGPS_TEMPORAL_HOPS=1
  QGPS_TEMPORAL_HOP_WEIGHTING=normalized_inverse_hop
  QGPS_SPECTRAL_RANK_MULTIPLIER=2
  QGPS_SPECTRAL_ETA=1e-4
  QGPS_OBSERVATION_NOISE=0.05
  INFERENCE_BACKEND=internvl3
  MODEL_NAME=/ssd2_4t/yifan/shared/models/InternVL3-8B
  PIPELINE_GPU_IDS=0,1,2,3,4,5,6,7
  INFERENCE_GPU_IDS=0,1,2,3,4,5,6,7
  NUM_PROCESSES=8
  LOGS_DIR=logs/InternVL3-8B/runs
  SUMMARY_BASELINE_DIR=logs/InternVL3-8B/baseline
  SUMMARY_COMPARE_ALL_BASELINES=1
  SKIP_COMPLETED_FRAMES=true
  LMMS_EVAL_RERAISE_ERRORS=1
)

echo "[INFO] InternVL3-8B sweep RUN_TAG=${RUN_TAG}"

for DATASET in videomme longvideobench mlvu; do
  echo "[INFO] Starting InternVL3-8B ${DATASET}"
  env \
    "${COMMON_ENV[@]}" \
    RUN_TAG="${RUN_TAG}" \
    RESOURCE_DIR="resources/${DATASET}/uniform_512f/blip2-itm-vit-g" \
    bash pipeline/runners/run_qgps_end_to_end.sh "${DATASET}"
done

echo "[INFO] InternVL3-8B three-dataset sweep complete"
BASH
```

## 运行说明

两组命令都会占用全部 8 张 GPU，因此不要同时启动。建议执行顺序：

1. 先运行 LLaVA-OneVision；
2. LLaVA 三个数据集全部结束后，再运行 InternVL 3。

如果中途失败，需要续跑同一个 run，不要生成新的时间戳。例如第一次日志中显示：

```text
RUN_TAG=20260720_150000
```

续跑前执行：

```bash
export RUN_TAG=20260720_150000
```

然后重新粘贴对应命令。由于已经设置：

```text
SKIP_COMPLETED_FRAMES=true
```

同一个 run 中已经生成结果的 K 会被跳过。

需要特别注意：这里的 `QGPS_SPECTRAL_ETA=1e-4` 只是保留统一 manifest/default 参数；`qgps_uniform_spectral_density` 的实现不会把 $\eta_s$ 应用到 modal density，实际仍然严格使用：

$$
p_\ell=\frac 1 m.
$$

当前 strategy 名仍带有 `uniform_spectral_density`，是因为我们还没有把它正式提升为 canonical Full Q-GPS；但这两组命令运行的选帧机制就是刚才确定的 simplified pipeline。

