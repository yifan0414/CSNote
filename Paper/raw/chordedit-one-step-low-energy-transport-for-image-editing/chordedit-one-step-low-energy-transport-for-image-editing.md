---
title: "ChordEdit: One-Step Low-Energy Transport for Image Editing"
authors:
  - Liangsi Lu
  - Xuhang Chen
  - Minzhe Guo
  - Shichu Li
  - Jingchao Wang
  - Yang Shi
conference: CVPR 2026🏆
year: 2026
arxiv_url: https://arxiv.org/abs/2602.19083
pdf_link: "[[assets/paper_2602.19083.pdf]]"
cover: "[[_assets/images/pipeline_2602.19083.png]]"
updated: 2026-06-06
tags:
  - paper/arxiv
  - diffusion
  - image-editing
  - efficient-inference
status: unread
priority:
rating:
topics:
  - Generative AI
code: https://github.com/ChordEdit/ChordEdit
---

## TL;DR

- ChordEdit 研究的是一个很具体但困难的场景：让 one-step T2I 模型在**不训练、不反演**的情况下完成 text-guided real-image editing。
- 核心观察是，直接使用 target/source 条件场之差会形成高能量、剧烈变化的控制场；当它被一次大步 Euler integration 穿越时，容易造成主体扭曲和背景崩坏。
- 方法把编辑改写为 dynamic optimal transport，并用两个时间点的 observable residual field 构造时间平滑的 **Chord Control Field (CCF)**：
  $$
  \hat u_t(x_\tau)=
  \frac{t\,\mathbf{R}(x_\tau,t-\delta)+\delta\,\mathbf{R}(x_\tau,t)}
  {t+\delta}.
  $$
- 纯 transport 版本为 1 NFE，强调背景与结构保持；默认完整版本再加 1 NFE 的 proximal refinement，以部分一致性换取更强的目标语义。
- 在 PIE-bench 上，ChordEdit 的完整 SD-Turbo 配置运行时间为 **0.38 s**，纯 transport 配置为 **0.20 s**；但跨方法比较使用了不同 backbone，最强的 CLIP 或 preservation 数值仍由部分多步/少步基线取得。

## Key Contributions

1. **将 one-step editing 解释为低能量 transport 问题。** 作者不再把编辑视为瞬时 drift difference 的直接外推，而是从 Benamou-Brenier dynamic OT 的 kinetic-energy objective 出发寻找稳定控制场。
2. **提出 Chord Control Field。** CCF 对可观测 residual field 做 causal temporal smoothing，目标是降低能量、方差、时间变化与一次大步积分误差。
3. **解耦结构保持与语义增强。** 1-NFE Chord transport 负责稳定搬运，optional proximal refinement 再用一次 target-conditioned forward pass 增强编辑语义。
4. **支持多种 one-step model parameterization。** 通过 time-only linear map $\mathcal{B}_t$，把 noise prediction、velocity/flow matching、$x_0$ prediction 和 consistency-model output 映射到统一比较域。
5. **展示效率与模型适配性。** 在 InstaFlow、SwiftBrush-v2、SD-Turbo 上，相比 naive one-step residual baseline 均提升 PSNR 与 CLIP-Edited；单噪声样本 $n=1$ 已表现出较强 seed robustness。

## Method

### Problem Formulation

给定 source prompt $c_{\rm src}$、target prompt $c_{\rm tar}$ 和 source image $x_{\rm src}$，naive editor 使用条件 drift difference：

$$
\Delta v(x_t,t)=v(x_t,t,c_{\rm tar})-v(x_t,t,c_{\rm src}).
$$

在 one-step distilled model 中，这个差分场可能具有高能量和高非线性，直接一次积分会累计较大的离散化误差。

模型在 noisy proxy $z\sim K_t(\cdot\mid x_\tau)$ 上输出 $Q(z,t,c)$。作者用 time-only linear map $\mathcal{B}_t$ 将不同模型输出映射到统一 velocity/control domain：

$$
\mathbf{R}(x_\tau,t)=
\mathbb{E}_{z\sim K_t(\cdot\mid x_\tau)}
\left[
\mathcal{B}_t
\left(
Q(z,t,c_{\rm tar})-Q(z,t,c_{\rm src})
\right)
\right].
$$

### Chord Control Field

作者先定义一个局部二次目标，在短时间窗 $[t-\delta,t]$ 内平衡历史估计与当前观测；再采用一阶 causal approximation，得到可实际计算的 CCF：

$$
\hat u_t(x_\tau)=
\frac{t\,\mathbf{R}(x_\tau,t-\delta)+
\delta\,\mathbf{R}(x_\tau,t)}
{t+\delta}.
$$

它可看作对 naive field $\mathbf{R}$ 的 causal smoothing。论文在 non-negative、unit-mass kernel 等假设下证明 $L^2$ energy contraction：

$$
\int_0^1 \|\hat u(t)\|^2\,dt
\le
\int_0^1 \|\mathbf{R}(t)\|^2\,dt.
$$

### Compact Pipeline

```text
Input: source image x_src, source/target prompts, t, delta, lambda, optional t_c
1. Encode x_src into the model/VAE working space.
2. With shared noise, query source/target outputs at t and t-delta.
3. Map output differences through B_t to obtain R(x, t) and R(x, t-delta).
4. Compute chord field:
      u_hat = [t R(x,t-delta) + delta R(x,t)] / (t + delta)
5. One-step transport:
      x_pred = x_src + lambda u_hat
6. Optional semantic refinement:
      x_tar = prox(x_pred, t_c, c_tar)
7. Decode and return x_tar.
```

纯 transport 为 1 NFE。论文默认报告的完整 ChordEdit 包含 optional refinement，因此为 2 NFE。

## Pipeline Figure

![[_assets/images/pipeline_2602.19083.png]]

**Caption:** Comparison of editing field stability. 多步 Simple Drift 可通过小步迭代保持稳定；one-step Simple Drift 的高能量场在一次大步中偏离目标；ChordEdit 对 $\mathbf{R}(x_\tau,t)$ 与 $\mathbf{R}(x_\tau,t-\delta)$ 做时间加权，得到稳定低能量的 Chord Control Field。

**Source:** TeX `\includegraphics` from `main.tex` (`img/chord_method.pdf`), rendered with the PDF crop box at 250 DPI.

## Experiments

### Datasets / Benchmarks

| Dataset / Study | Task | Split / Size | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| PIE-bench | Instruction-based real-image editing | 700 samples, 10 editing categories, 512×512 | PSNR, MSE, SSIM, LPIPS, Structure Distance, CLIP-Whole, CLIP-Edited | 每个样本含 source image、文本 prompts 和 edit-region ground-truth mask；论文评估时不使用 protective mask |
| User Study | 四方法 blind preference comparison | 150 participants × 30 prompts = 4,500 votes per criterion | Semantic Alignment preference, Preservation Quality preference | 比较 ChordEdit、InfEdit、FlowEdit、SwiftEdit |

### Main Results: PIE-bench

下表摘录论文主表中的代表性方法。不同方法通常绑定不同 backbone，因此这些数值适合展示质量/效率 trade-off，不应视为严格的同模型消融。

| Method | Type / Backbone | PSNR ↑ | MSE ×10³ ↓ | LPIPS ×10³ ↓ | CLIP-Whole ↑ | CLIP-Edited ↑ | Runtime (s) ↓ | NFE ↓ | VRAM (MiB) ↓ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DDIM + MasaCtrl | Multi-step | 21.25 | 8.58 | 106.59 | 24.13 | 21.13 | 55.20 | 100 | 12272 |
| FlowEdit | Multi-step / SD3 | 22.17 | 7.69 | 104.81 | 26.64 | 23.69 | 7.22 | 33 | 17140 |
| InfEdit | Few-step / SD1.4 | 24.14 | 6.82 | 55.69 | 24.89 | 21.88 | 1.41 | 4 | 6502 |
| InstantEdit | Few-step / PeRFlow-SD1.5 | 23.80 | 4.21 | 60.92 | 24.97 | 21.82 | 1.30 | 8 | 16270 |
| SwiftEdit | One-step / SwiftBrush-v2 | 21.71 | 8.22 | 91.22 | 24.93 | 21.85 | 0.54 | 2 | 15060 |
| **ChordEdit** | One-step / SwiftBrush-v2 | 22.04 | 7.13 | 111.22 | 25.12 | 22.58 | **0.38** | 2 | 6988 |
| **ChordEdit w/o prox** | One-step / SD-Turbo | 23.89 | 5.05 | 88.36 | 24.97 | 21.87 | **0.20** | 1 | 6988 |
| **ChordEdit** | One-step / SD-Turbo | 22.20 | 6.84 | 128.25 | 25.58 | 22.96 | **0.38** | 2 | 6988 |

关键解读：

- 纯 Chord transport 的 SD-Turbo 配置在 1 NFE 下达到 23.89 PSNR，明显高于完整配置的 22.20，说明 refinement 会牺牲 preservation。
- 完整 SD-Turbo 配置把 CLIP-Edited 从 21.87 提升到 22.96，但 LPIPS 从 88.36 增至 128.25。
- FlowEdit 在摘录表中仍有更高 CLIP-Whole/Edited；InfEdit 和 InstantEdit 在部分 preservation metric 上更强。ChordEdit 的主要优势是速度、低 NFE、training-free/inversion-free 和较低显存占用的组合。

### Ablation: Transport and Refinement

| Variant | Naive PSNR ↑ | Naive CLIP-Edited ↑ | ChordEdit PSNR ↑ | ChordEdit CLIP-Edited ↑ | NFE |
| --- | ---: | ---: | ---: | ---: | ---: |
| w/o prox | 21.89 | 20.83 | **23.89** | 21.87 | 1 |
| w/ prox | 21.38 | 21.96 | 22.20 | **22.96** | 2 |

### Ablation: Model-Agnostic Behavior

| T2I Model | Naive PSNR ↑ | Ours PSNR ↑ | Naive CLIP-Edited ↑ | Ours CLIP-Edited ↑ |
| --- | ---: | ---: | ---: | ---: |
| InstaFlow | 22.05 | 23.05 | 20.19 | 21.39 |
| SwiftBrush-v2 | 20.52 | 22.04 | 21.06 | 22.58 |
| SD-Turbo | 21.38 | **22.20** | 21.96 | **22.96** |

### Analysis: Noise and User Preference

| Analysis | Result |
| --- | --- |
| Number of noise samples | ChordEdit 的 $n=1,2,3,4$ Pareto fronts 几乎重合；增加样本的边际收益很小 |
| Seed robustness at $n=1$ | 20 seeds 上 CLIP CoV 为 0.20%，PSNR CoV 为 0.07% |
| User study: Semantic Alignment | ChordEdit 42.5%, FlowEdit 25.3%, InfEdit 19.6%, SwiftEdit 12.6% |
| User study: Preservation Quality | ChordEdit 48.3%, InfEdit 35.4%, SwiftEdit 9.2%, FlowEdit 7.1% |

### Training / Compute

| Item | Value |
| --- | --- |
| Training | 无额外训练；training-free |
| Inversion | 无 per-image inversion；inversion-free |
| Evaluation hardware | Single NVIDIA Titan 24GB GPU |
| Default backbone in main full result | SD-Turbo |
| Default noise samples | $n=1$ |
| Default hyperparameters | $t=0.90$, $\delta=0.15$, $\lambda=1.00$, $t_c=0.30$ |
| Transport cost | 1 NFE |
| Optional proximal refinement | +1 NFE |
| Default full-method runtime | 0.38 s |
| Transport-only runtime | 0.20 s |

## Limitations & Caveats

- **“One-step”需要区分 transport 与完整结果。** 核心 Chord transport 确实为 1 NFE，但论文默认的最佳语义配置包含 proximal refinement，总计 2 NFE。
- **跨方法主表存在 backbone confound。** FlowEdit、InfEdit、InstantEdit、ChordEdit 等使用各自官方模型；这能反映系统级最佳表现，但不能单独归因于 editing algorithm。论文提供了 SwiftBrush-v2 上的统一模型对比，但范围仍有限。
- **模型适配性只在三个 one-step backbone 上验证。** “Model agnostic”依赖为各模型正确实现 $\mathcal{B}_t$、schedule derivative 和统一 comparison domain；尚未覆盖更广泛的生成架构或高分辨率设置。
- **只在 PIE-bench 上进行核心自动指标评估。** 数据集有 700 个 512×512 样本与 10 类编辑，尚不足以证明对复杂局部几何、文本渲染、多人关系、超高分辨率或 domain shift 的普遍稳健性。
- **平滑会引入 bias 与可见 trade-off。** $\delta$ 过小退化到 unstable naive field；$\delta$ 过大可能过度保守并削弱目标语义。增大 $\lambda$ 或 $t_c$ 会增强语义，但也更容易 over-edit。
- **理论与实际 estimator 之间有近似。** 连续 kernel smoothing 的 contraction/error 分析依赖 non-negative unit-mass kernel、平滑性和局部假设；实际实现使用两个离散时间点与一阶 approximation。
- **数值稳定仍需实现层面的保护。** 对 noise-prediction model，$\mathcal{B}_t$ 中含有 schedule-dependent denominator；当 $\alpha(t)\to0$、即 $t\approx1$ 时可能不稳定。论文通过选择 $t=0.90,\delta=0.15$ 避开端点。
- **安全与偏差问题未被方法本身解决。** 实时高保真编辑可被用于 deceptive content；方法继承并可能放大 backbone 中与 race、gender、culture 等相关的偏差。

## Concrete Implementation Ideas

1. **实现统一 residual adapter。** 为 noise prediction、velocity、$x_0$ prediction 分别实现 `to_control_domain(Q, t, schedule)`，并用 finite-difference 检查 $\dot\alpha(t)$、$\dot\sigma(t)$ 与 denominator 的数值范围。
2. **把四次条件查询合并为一个 batch。** 对 $(c_{\rm src},c_{\rm tar})\times(t,t-\delta)$ 使用 shared noise 和 batched forward，一次获得两个 residual field，保持作者所述的 parallel-computable transport。
3. **把 fidelity/semantics 暴露为显式模式。** 提供 `transport_only`（1 NFE，高 preservation）和 `refined`（2 NFE，高 semantic alignment）两个 preset，而不是只暴露一个模糊的 edit-strength slider。
4. **加入自适应 $\delta$ 与安全诊断。** 根据 $\|\mathbf R(t)-\mathbf R(t-\delta)\|$、field energy 或 schedule conditioning 自动调整 $\delta$，并在接近不稳定时间端点时拒绝或裁剪参数。
5. **建立同-backbone benchmark。** 固定 SwiftBrush-v2 或 SD-Turbo，比较 naive residual、Chord transport、prox refinement 和其他可兼容 editor，以隔离算法增益并测量不同编辑类别的失败率。

## Open Questions / Follow-ups

- 是否可以从局部 field variation 或估计方差自动选择每张图的 $\delta$、$\lambda$ 和 $t_c$，而不是使用全局固定值？
- 两点 causal estimator 是否是质量/计算最优的离散形式？使用三点或高阶但仍可并行的 estimator 能否改善 bias，而不增加不可接受的 NFE？
- 在更现代的 one-step/consistency/rectified-flow backbone、高分辨率生成器和 video editing 中，低能量 transport 是否仍能保持相同优势？
- 如何将 spatially localized constraint、identity preservation 或 geometry-aware control 融入 CCF，同时不依赖 protective mask？
- 论文的理论界限与实际视觉 artifact、LPIPS、CLIP 改善之间能否建立更直接的可测量关系？

## Citation

```bibtex
@inproceedings{lu2026chordedit,
  title     = {ChordEdit: One-Step Low-Energy Transport for Image Editing},
  author    = {Liangsi Lu and Xuhang Chen and Minzhe Guo and Shichu Li and Jingchao Wang and Yang Shi},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year      = {2026},
  url       = {https://arxiv.org/abs/2602.19083}
}
```

