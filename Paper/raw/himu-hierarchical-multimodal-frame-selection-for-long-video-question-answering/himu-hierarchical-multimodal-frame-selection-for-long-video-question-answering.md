---
title: HiMu(frame)
authors:
  - Dan Ben-Ami
  - Gabriele Serussi
  - Kobi Cohen
  - Chaim Baskin
conference:
year: 2026
arxiv_url: https://arxiv.org/abs/2603.18558
pdf_link: "[[assets/paper_2603.18558.pdf]]"
cover: "[[assets/pipeline_2603.18558.png]]"
updated: 2026-05-13
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - option-aware
  - video-llm
status: reading
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- HiMu 是一个 training-free 的 long-video QA frame selection 框架：先用一次 text-only LLM call 把问题解析成 hierarchical logic tree，再把叶子谓词路由到 CLIP、OVD、OCR、ASR、CLAP 等轻量专家。
- 核心不是“多看更多帧”，而是先把 query 的组合结构显式化：AND / OR / SEQ / RIGHT_AFTER 在时间轴上组合专家信号，得到每帧的 satisfaction curve $T(t)$。
- 在 Qwen3-VL-8B、$K{=}16$ 的受控设置下，HiMu 在 Video-MME Overall 达到 **73.22%**，高于 Uniform 66.36、BOLT 68.74、T* 69.77、AKS 67.98；LongVideoBench$_\text{val}$ 也达到 **64.19%**。
- Ablation 显示最大贡献来自 hierarchical composition：把 logic tree 换成 Flat Fusion 会从 **73.22%** 掉到 67.73，比去掉任一单个 expert 的影响更大。
- 代价是 selector latency 高于纯 similarity 方法；论文报告 10 分钟视频、1 FPS、$K{=}16$、8×A100 下 HiMu first-query selector latency 为 **13.3s**，amortized per-query 为 **9.0s**。
- 这篇文章的真正价值在于把 frame selection 做成可审计的 neuro-symbolic layer：每个 selected frame 都能追溯到具体 expert-predicate activation，而不是单个 opaque similarity score。

## Key Contributions

1. 提出 **HiMu (Hierarchical Multimodal Frame Selection)**，把 long-video QA 的 frame selection 从 flat query-frame similarity 改成 hierarchical logic tree evaluation。
2. 首次把 audio experts 明确放入 query-aware frame selection：ASR 用于 spoken content，CLAP 用于 environmental audio events，和 visual experts 一起参与 selection，而不是只把 audio/subtitle 喂给最终 LVLM。
3. 使用 fuzzy-logic composition 在时间轴上组合 expert signals，支持 co-occurrence、disjunction、temporal sequencing 和 immediate temporal adjacency。
4. 引入 **PASS (Peak-And-Spread Selection)**，从 satisfaction curve 中先找多个峰，再在每个峰附近扩展邻帧，避免 naive top-$K$ 把 budget 全部集中在单个高峰片段。
5. 在 Video-MME、LongVideoBench$_\text{val}$、HERBench-Lite 上展示了更好的 efficiency-accuracy Pareto trade-off，尤其是在低帧预算 $K{=}16$ 下。

## Method

HiMu 的输入是 video $\mathcal{V}=\{v_1,\dots,v_T\}$、问题 $Q$、可选 answer options 和 frame budget $K$。输出是给 downstream LVLM 的 $K$ 个 query-relevant frames。

```text
HiMu pipeline
1. Parse Q with one text-only LLM call into a hierarchical logic tree T.
2. Route each LEAF(expert, query) to CLIP / OVD / OCR / ASR / CLAP.
3. Convert raw expert scores u_i(t) into normalized, smoothed signals.
4. Compose signals bottom-up with AND / OR / SEQ / RIGHT_AFTER.
5. Run PASS on satisfaction curve T(t) and pass selected frames to the LVLM.
```

**Query decomposition.** 叶子节点是 $\ell=(\texttt{expert}, \texttt{query})$，其中 expert 来自 $\{\text{clip},\text{ovd},\text{ocr},\text{asr},\text{clap}\}$。内部节点使用四类 operators：$\operatorname{And}$、$\operatorname{Or}$、$\operatorname{Seq}$、$\operatorname{RightAfter}$。MCQ 通常被组织成 $\operatorname{And}(\text{shared\_context}, \operatorname{Or}(\text{option}_1,\dots,\text{option}_n))$。

**Expert signals.** CLIP 处理 actions、scenes、visual states；OVD 处理 physical objects / people；OCR 处理 on-screen text；ASR 处理 spoken content；CLAP 处理 non-speech audio。CLIP、ASR、CLAP、OCR features 按 video cache；OVD 是 query-conditioned，因此每个 query 重新运行。

**Normalization and smoothing.** 原始 expert 分数尺度不同，先用 median/MAD 做 robust normalization：

$$
\tilde{u}_i(t) = \sigma\left(\gamma \cdot \frac{u_i(t)-\mathrm{med}(u_i)}{\mathrm{MAD}(u_i)+\delta}\right)
$$

然后按 modality 用 Gaussian kernel 平滑：

$$
\hat{u}_i(t)=\sum_{t'=1}^{T}\tilde{u}_i(t')\,\mathcal{G}(t-t';\sigma_m)
$$

visual signals 使用较窄 bandwidth，ASR / CLAP 使用更宽 bandwidth 来对齐 audio temporal uncertainty。

**Fuzzy composition.** 基本逻辑组合为：

$$
\operatorname{And}(A,B)(t)=A(t)B(t)
$$

$$
\operatorname{Or}(A,B)(t)=A(t)+B(t)-A(t)B(t)
$$

$\operatorname{Seq}$ 用 running max 的 has-occurred signal $H_j(t)=\max_{s<t}u_j(s)$ 和 yet-to-occur signal $F_j(t)=\max_{s>t}u_j(s)$ 来约束顺序，同时允许每个 event step 自己贡献峰值。$\operatorname{RightAfter}$ 用指数衰减权重衡量 cause-effect 的近邻关系。

**PASS.** PASS 先选择 $N_p$ 个 local maxima，并设置最小峰间距 $\Delta$；再为每个 peak 在 local window $w$ 中补充 $N_n$ 个高分邻帧；最后用 satisfaction curve 中剩余最高分帧填满 budget。

## Pipeline Figure

![[assets/pipeline_2603.18558.png]]

Caption: The HiMu pipeline. (1) An LLM parses the question into a logic tree of modality-specific experts. (2) Experts (CLIP, ASR, OVD, CLAP) extract raw signals, which are then normalized and smoothed. (3) Fuzzy logic operators compose signals into a temporal satisfaction curve. (4) Top frames are sampled for the LVLM using PASS.

Source: TeX-first extraction from `sections/03_method.tex`, `\includegraphics{figures/himu_pipe3_with_vid_streams2.png}`.

## Experiments

### Datasets / Benchmarks

| Dataset                      | Task                                              | Split                                                                                       | Metric(s) | Notes                                                                      |
| ---------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------- |
| Video-MME                    | Long-form multiple-choice VideoQA                 | 900 videos, 2,700 expert-annotated questions; Short <2 min, Medium 4-15 min, Long 30-60 min | Accuracy  | 包含 audio tracks 和 duration splits，适合评估 multimodal expert pathways。         |
| LongVideoBench<sub>val</sub> | Moment-level long-video QA with referring queries | validation split, about 1.3K questions, 17 categories                                       | Accuracy  | 使用 original subtitles 或 Whisper transcripts 作为 speech proxy。               |
| HERBench-Lite                | Highly compositional VideoQA                      | 2K-question subset, 12 compositional tasks                                                  | Accuracy  | $m{\geq}3$ non-overlapping cues；无 audio / subtitles，是 visual-only setting。 |

### Main Results

论文主表把两类比较放在一起：第一组是 Qwen3-VL-8B、$K{=}16$ 的受控 selector comparison；后面是对不同 LVLM 的 plug-and-play generalization。灰色文献结果在原表中表示不同 frame budgets，这里用 Frames/Setting 标出。

| Method | Model / Setting | Frames / Setting | Video-MME Short | Video-MME Medium | Video-MME Long | Video-MME Overall | LVB$_\text{val}$ | HERBench-Lite |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Uniform Sampling | Qwen3-VL-8B | 16 | 76.34 | 66.31 | 55.58 | 66.36 | 55.74 | 41.70 |
| BOLT | Qwen3-VL-8B | 16 | 69.58 | 67.87 | 68.73 | 68.74 | 54.55 | 42.20 |
| T* | Qwen3-VL-8B | 16 | 73.66 | 67.39 | 68.12 | 69.77 | 57.49 | 39.10 |
| AKS | Qwen3-VL-8B | 16 | 70.05 | 65.10 | 68.73 | 67.98 | 57.14 | 40.25 |
| **HiMu (Ours)** | Qwen3-VL-8B | 16 | **78.55** | **71.00** | **69.90** | **73.22** | **64.19** | **43.22** |
| Uniform | LLaVA-OV-1.5-8B | 16 | **72.26** | 62.33 | 54.85 | 63.55 | 54.33 | 35.75 |
| **HiMu (Ours)** | LLaVA-OV-1.5-8B | 16 | 71.87 | **66.99** | **63.94** | **67.65** | **57.85** | **35.87** |
| Uniform | InternVL-3.5-8B | 16 | 75.41 | 67.39 | 56.55 | 66.63 | 59.23 | 38.30 |
| **HiMu (Ours)** | InternVL-3.5-8B | 16 | **76.92** | **70.40** | **66.50** | **71.35** | **64.11** | **38.32** |
| Uniform | Qwen2.5-VL-7B | 16 | 72.49 | 61.01 | 53.82 | 62.57 | 54.58 | 34.05 |
| VideoZoomer | Qwen2.5-VL-7B$^\dagger$ | 128 | not reported | not reported | 55.8 | 65.2 | 57.7 | not reported |
| VideoChat-A1 | Qwen2.5-VL-7B | 512 | not reported | not reported | not reported | 69.7 | 55.6 | not reported |
| **HiMu (Ours)** | Qwen2.5-VL-7B | 16 | **73.08** | **65.10** | **62.86** | **67.09** | **57.51** | **35.17** |
| Uniform | Gemma-3-12B | 16 | **73.31** | 60.29 | 55.83 | 62.99 | 47.59 | 31.20 |
| **HiMu (Ours)** | Gemma-3-12B | 16 | 71.56 | **65.70** | **67.48** | **68.28** | **53.92** | **31.47** |
| Uniform | Gemini-2.5-Flash | stratified 25% subset | 78.43 | 67.11 | 61.22 | 68.95 | 56.33 | 37.27 |
| **HiMu (Ours)** | Gemini-2.5-Flash | stratified 25% subset | **78.92** | **75.00** | **74.49** | **76.11** | **70.13** | **37.68** |
| Uniform | GPT-4o | stratified 25% subset | 76.96 | 73.03 | 71.43 | 73.81 | 55.58 | 37.47 |
| VSLS | GPT-4o | 32 | 71.9 | 61.9 | 55.2 | 63.0 | 63.4 | not reported |
| VideoChat-A1 | not specified | 384 | not reported | not reported | not reported | 77.2 | 66.7 | not reported |
| **HiMu (Ours)** | GPT-4o | stratified 25% subset | **80.88** | **77.19** | **76.53** | **78.18** | **65.10** | **40.68** |

$^\dagger$ Finetuned model in the source table.

主要观察：在严格受控的 Qwen3-VL-8B / 16-frame setting 下，HiMu 对所有 benchmark 都是最优；LongVideoBench$_\text{val}$ 上相对 T* 的差距是 +6.70pp，说明 query-aware, cross-modal moment localization 是关键场景。

### Selector Comparison / Efficiency Context

| Method | Train-Free | Query Representation | Selection Evidence | E2E Latency | Amort. Latency | Interpretability |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| BOLT | yes | Global embedding | Vis. | 3.0s | 0.3s | Per-frame score |
| AKS | yes | Global embedding | Vis. | 2.7s | 1.4s | Per-frame score |
| MDP$^3$ | yes | Global embedding | Vis. | 1.8s | 0.7s | Per-frame score |
| T$^\ast$ | yes | Flat object queries | Vis. (OVD) | 13.0s | 13.0s | Detection logs |
| VSLS | yes | Fixed relation triplets | Vis. (OVD) | 13.3s | 13.3s | Detection logs |
| NeuS-QA | yes | Temporal logic spec. | Vis. | 6.7s | 6.7s | Verification trace |
| VideoAgent | no | Implicit iterative LLM | Vis. | 44.7s | 12.3s | None |
| SeViLA | no | Implicit per-frame VLM | Vis. | 60.0s | 60.0s | None |
| VideoZoomer | no | Implicit iterative VLM | Vis. | 16.0s | 16.0s | None |
| Frame-Voyager | no | Learned score fn. | Vis. | 1.6s | 0.2s | None |
| FFS | no | Learned policy | Vis. | 0.1s | 0.1s | None |
| VidF4 | no | Learned score fn. | Vis. | 1.1s | 0.7s | None |
| **HiMu (ours)** | yes | Hierarchical logic tree | Vis.+Aud. | **13.3s** | **9.0s** | Frame×Expert scores |

这张表的重点不是 HiMu 最快，而是它在 structured reasoning 和 amortized cost 之间取到折中：比 BOLT/AKS 慢，但有 compositional query representation；比 agentic / per-frame VLM selector 更便宜，并且可审计。

### Ablations / Analysis

**Expert and composition ablation (Video-MME, Qwen3-VL-8B, $K{=}16$).**

| Configuration | Short | Med. | Long | Overall |
| ---- | ---- | ---- | ---- | ---- |
| **HiMu** | **78.55** | **71.00** | **69.90** | **73.22** |
| Flat Fusion | 68.65 | 66.06 | 68.45 | 67.73 |
| w/o ASR | 76.34 | 69.07 | 68.08 | 71.23 |
| w/o CLAP | 77.97 | 69.43 | 69.05 | 72.22 |
| w/o CLIP | 76.46 | 69.55 | 69.17 | 71.79 |
| w/o OCR | 77.39 | 69.92 | 69.05 | 72.18 |
| w/o OVD | 77.39 | 70.64 | 69.17 | 72.46 |

关键结论：Flat Fusion 的 -5.49pp 是最大掉点，说明 tree structure / fuzzy composition 比任一单个 modality expert 更关键。单个 expert 中，ASR 移除导致 Overall -1.99pp，是最大单项专家贡献。

**Frame budget analysis (Video-MME).**

| # Frames | Method | Short | Med. | Long | Overall |
| ---- | ---- | ---- | ---- | ---- | ---- |
| 8 | Uniform | **73.54** | 63.42 | 54.67 | 64.00 |
| 8 | HiMu | **73.54** | **68.71** | **68.81** | **70.39** |
| 16 | Uniform | 76.34 | 66.31 | 55.58 | 66.36 |
| 16 | **HiMu** | **78.55** | **71.00** | **69.90** | **73.22** |
| 32 | Uniform | **81.35** | 69.19 | 58.67 | 69.89 |
| 32 | HiMu | 80.77 | **73.29** | **70.02** | **74.77** |
| 64 | Uniform | **82.87** | 71.12 | 60.61 | 71.68 |
| 64 | HiMu | 82.40 | **73.53** | **71.12** | **75.77** |

HiMu at $K{=}16$ 的 Overall 73.22 高于 Uniform at $K{=}64$ 的 71.68，支持“更准地找 evidence frames 比机械增加帧数更有效”的主张。

**Hyperparameter sensitivity (50% Video-MME subset, Qwen3-VL-8B, $K{=}16$).**

| Configuration | Accuracy | $\Delta$ |
| ---- | ---- | ---- |
| **HiMu (default)** | **73.31** | --- |
| All smoothing disabled | 73.23 | -0.08 |
| Visual $\sigma$ (CLIP/OVD/OCR, default: 0.5) $\to$ 0 | 73.23 | -0.08 |
| Visual $\sigma$ (CLIP/OVD/OCR, default: 0.5) $\to$ 2 | 72.27 | -1.04 |
| Speech $\sigma$ (ASR, default: 1.5) $\to$ 0 | 73.07 | -0.24 |
| Speech $\sigma$ (ASR, default: 1.5) $\to$ 4 | 72.51 | -0.80 |
| $\kappa{=}0.5$ | 72.83 | -0.48 |
| $\kappa{=}4.0$ | 72.67 | -0.64 |
| $\gamma{=}1.0$ | 73.07 | -0.24 |
| $\gamma{=}5.0$ | 72.99 | -0.32 |

**Expert backbone / selection strategy ablation (50% Video-MME subset).**

| Configuration | Accuracy | $\Delta$ |
| ---- | ---- | ---- |
| **HiMu (default)** | **73.31** | --- |
| CLIP-dfn $\rightarrow$ SigLIP2 | 72.59 | -0.72 |
| YOLO-World v2 $\rightarrow$ Grounding DINO | 73.71 | +0.40 |
| docTR $\rightarrow$ EasyOCR | 72.35 | -0.96 |
| faster-whisper large-v3-turbo $\rightarrow$ whisper-large | 72.67 | -0.64 |
| LAION CLAP $\rightarrow$ CLAP music-speech | 72.75 | -0.56 |
| PASS $\rightarrow$ Vanilla top-$K$ | 72.59 | -0.72 |

**LLM tree parser comparison (50% Video-MME subset, Qwen3-VL-8B answerer).**

| Tree Parser LLM | Accuracy | $\Delta$ |
| ---- | ---- | ---- |
| Qwen3-VL-8B (default) | 73.31 | --- |
| **LLaVA-OV-1.5-8B** | **74.17** | **+0.86** |
| Gemini-2.5-Flash | 73.31 | 0.00 |
| InternVL-3.5-8B | 73.22 | -0.09 |

这个结果暗示 tree parsing 更像 schema-guided decomposition，而不是需要 frontier-level open-ended reasoning 的任务；较弱 answerer 也可能是足够好的 parser。

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training | Training-free；不训练 selector，本质是 prompt + expert bank + deterministic composition。 |
| Experiment hardware | 8× NVIDIA RTX Pro 6000 GPUs。 |
| Default frame budget | $K{=}16$ frames。 |
| Sampling | 1 FPS candidate frames。 |
| Default experts | CLIP-dfn, YOLO-World v2, docTR, faster-whisper large-v3-turbo, LAION CLAP。 |
| Cached video-level features | CLIP, ASR, CLAP, OCR are query-independent and cached per video。 |
| Query-conditioned expert | OVD / YOLO-World v2 reruns per query if OVD leaves appear。 |
| Normalization | $\gamma=3.0$, $\delta=10^{-6}$。 |
| RightAfter decay | $\kappa=2.0$。 |
| Smoothing bandwidths | $\sigma_\text{clip}=0.5$, $\sigma_\text{ovd}=0.5$, $\sigma_\text{ocr}=0.5$, $\sigma_\text{asr}=1.5$, $\sigma_\text{clap}=2.0$。 |
| PASS parameters | $N_p=\lfloor\sqrt{K}\rfloor$, $N_n=\lfloor\sqrt{K}/2\rfloor$, $w=\lfloor\sqrt{K}\rfloor$, $\Delta=\lfloor\sqrt{K}\rfloor$。 |

**Latency breakdown reported for 10-minute video, 1 FPS, 600 candidate frames, $K{=}16$, 8×A100 (80GB).**

| Component | Hardware | Latency (s) |
| ---- | ---- | ---- |
| Video / audio I/O | CPU | 1.3 |
| CLIP-dfn ViT-L/14 (600 frames) | 1 GPU | 2.1 |
| LAION CLAP (300 windows) | 1 GPU | 0.9 |
| docTR OCR (~300 frames) | 4 GPUs (DP) | 3.0 |
| faster-whisper lv3-turbo (10 min) | 3 GPUs | 2.8 |
| **Preprocessing total (parallel)** |  | **4.3** |
| Query planning (8B parser) | 1 GPU, CPU | 6.7 |
| OVD / YOLOv8x-worldv2 (600 frames) | 6 GPUs (DP) | 2.1 |
| Per-query scoring (text matching) | 1 GPU | <0.2 |
| Composition + PASS | CPU | <0.1 |
| **Per-query total** |  | **9.0** |
| **E2E total (preprocess + per-query)** |  | **13.3** |

## Limitations & Caveats

- 相比 BOLT/AKS/MDP$^3$ 这类 similarity selectors，HiMu first-query latency 明显更高；它更适合 compositional / multimodal query，或同一视频有多 query、可 amortize cache 的场景。
- OVD 是 query-conditioned，每个 query 仍要重新跑检测；当问题包含很多 object leaves 时，这会成为 per-query bottleneck。
- LLM parser 的 tree decomposition 质量是关键依赖：过浅、错误路由、错误 temporal operator 都会直接破坏 selection。
- ASR 受底层 speech model 语言覆盖限制；multilingual / low-resource audio 可能让 spoken-cue selection 退化。
- 论文表 1 中其他方法 latency 是从公开报告估计并调整到 8×A100 reference，没有全部重新测量；跨系统 latency 可比性需要谨慎。
- 主文关于 Qwen2.5-VL-7B 的一段叙述和 Table 2 数字存在疑似不一致：表中 HiMu Qwen2.5-VL-7B Overall 是 67.09，而正文出现 69.70 这一数字。做引用时建议以表格原值为准并注明来源。
- arXiv source 提到完整 prompt examples 在 code repository，但 source 中没有给出明确 code URL；frontmatter 的 `code` 暂留空。

## Concrete Implementation Ideas

1. 把 tree parser 做成 constrained JSON generation + schema validation：每个 LEAF 必须有 `expert` 和 `query`，每个 internal node 必须有合法 `op` 和 `children`。
2. 构建 per-video feature cache：CLIP frame embeddings、OCR text boxes、ASR timestamped words、CLAP audio windows 都按 video key cache；query 阶段只做 text matching / similarity lookup。
3. 对每个 benchmark 配置 active experts：Video-MME 打开 ASR+CLAP，LongVideoBench 打开 ASR、关闭 CLAP，HERBench 用 visual-only experts。
4. 实现 frame×expert activation heatmap，让每个 selected frame 都能显示是哪些 predicates 在支撑，便于 debug parser、expert 和 temporal composition。
5. 做一个 budget-aware fallback：若 parser 输出只有单个视觉叶子且无 temporal operator，可以走 fast similarity selector；若 tree 复杂再启用完整 HiMu。

## Open Questions / Follow-ups

- 如果 downstream LVLM 本身能处理更长视频或有 stronger audio understanding，HiMu 的最优 $K$ 和 expert mix 会如何变化？
- Tree parser 的错误模式需要更细粒度统计：错误主要来自 expert routing、operator choice、option factoring，还是 temporal cue interpretation？
- 能否用 smaller / distilled parser 把 6.7s query planning latency 降下来，同时保持相同 tree quality？
- ASR / CLAP 对 multilingual、music-heavy、noisy speech videos 的鲁棒性如何？论文当前没有展开。
- HiMu 与 token compression / visual token pruning 结合时，是先选帧再压 token，还是联合优化 frame budget 与 token budget 更好？
- 对 open-ended QA 而非 MCQ，缺少 answer options 时 tree structure 会不会更容易过宽或过泛？

## Citation

```bibtex
@article{benami2026himu,
  title = {HiMu: Hierarchical Multimodal Frame Selection for Long Video Question Answering},
  author = {Ben-Ami, Dan and Serussi, Gabriele and Cohen, Kobi and Baskin, Chaim},
  journal = {arXiv preprint arXiv:2603.18558},
  year = {2026},
  url = {https://arxiv.org/abs/2603.18558}
}
```
