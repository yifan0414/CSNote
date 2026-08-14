---
title: "EarlyTom: Early Token Compression Completes Fast Video Understanding"
authors: ["Hesong Wang", "Xin Jin", "Lu Lu", "Chenhaowen Li", "Jian Chen", "Qiang Liu", "Huan Wang"]
conference: ""
year: 2026
arxiv_url: "https://arxiv.org/abs/2605.30010"
pdf_link: "[[assets/paper_2605.30010.pdf]]"
cover: "[[assets/pipeline_2605.30010.png]]"
updated: 2026-06-01
tags: ["paper/arxiv", "video-qa", "long-video", "temporal-reasoning", "question-aware", "token-pruning", "video-llm"]
status: "unread"
priority:
rating:
topics: ["Video Understanding"]
code: "https://viridisgreen.github.io/EarlyTom"
---

## TL;DR

- EarlyTom 针对 Video-LLMs 的 TTFT bottleneck：不是只在 LLM prefill 前后压缩 token，而是把压缩提前到 vision encoder 内部。
- 方法是 training-free，两阶段：Stage I 做 inner-vision encoder frame merging，Stage II 做 decoupled spatial token selection，避免 attention sink 让全局 Top-K 偏向静态位置。
- 在 LLaVA-OneVision-7B 上，10% token retention 时 TTFT 从 889.9 ms 降到 336.2 ms，约 $2.65\times$；prefilling FLOPs 从 82.6T 降到 32.2T。
- 准确率保持接近 full-token baseline：LLaVA-OneVision-7B 的 10% retention 平均分为 56.2，约为 baseline 的 96.2%。
- 额外实验显示 EarlyTom 可迁移到 LLaVA-OneVision-0.5B、LLaVA-Video-7B 和 Qwen2.5-VL-7B，但阈值、retention ratio 和具体插入层仍需要按模型/任务调节。

## Key Contributions

1. 提出 **inner vision encoder frame merge**：在 vision encoder 中根据 frame similarity 做 streaming segmentation、middle frame merge 和 weighted frame merge，从源头减少后续 encoder 与 prefill 负担。
2. 提出 **decoupled spatial token selection**：把 frame 分成 dynamic/static 两类，dynamic frames 用 global Top-K，static frames 用 local-window Top-K，缓解 video attention sink 导致的 token selection bias。
3. 将算法与系统实现一起考虑：static token selection 部分可放到 CPU，dynamic token selection 留在 GPU，论文实现中还使用 custom Triton kernel。
4. 在多个 Video-LLM backbones 与 benchmarks 上验证 latency、FLOPs、throughput 和 accuracy 的 trade-off，尤其强调 TTFT 而不仅是理论 FLOPs。

## Method

EarlyTom 的关键假设是：Video-LLM 的 inference latency 中，vision encoding 仍然占很大比例；如果 token compression 只发生在 vision encoder 之后，TTFT 的主要部分没有被真正优化。

**Pipeline bullets**

1. **Profiling**：把 TTFT 拆成 vision encoding、visual token processing、LLM prefill、system overhead。baseline 中 vision encoding 占 36.3%；HoliTom 和 VisionZip 这类已压缩 prefill 的方法中，这一比例升到 55.8% 和 68.4%。
2. **Stage I: Inner-Vision Encoder Frame Merging**
   - 对相邻 frames 的对应 spatial tokens 求平均 cosine similarity。
   - 用 EMA 平滑相似度：$\hat{s}_t = \alpha s_t + (1 - \alpha)\hat{s}_{t-1}$；当 $\hat{s}_t < \tau_{\mathrm{seg}}$ 时切分 segment。
   - 在 segment 内只对中间帧做 merge：当 $s_i > \tau_{\mathrm{merge}}$ 且 $s_i > s_{i+1}$ 时合并 $F_i,F_{i+1}$。
   - weighted merge 使用 $\hat{F}=\frac{s_iF_i+s_{i+1}F_{i+1}}{s_i+s_{i+1}}$。
3. **Stage II: Decoupled Spatial Token Selection**
   - 每个 segment 的 head/tail frames 视为 dynamic，中间 frames 视为 static。
   - dynamic frames 用 global Top-K 保留 motion-sensitive tokens。
   - static frames 用 local-window Top-K，避免 sink tokens 垄断注意力排序，同时保持空间分布。
   - 最后按原时间顺序 gather dynamic/static selected tokens，送入 LLM decoding。
4. **System co-design**：论文把一部分 static token selection offload 到 CPU，GPU 负责更重的 dynamic token selection，以降低额外 overhead。

## Pipeline Figure

![[assets/pipeline_2605.30010.png]]

Caption: **Overall pipeline of EarlyTom.** The method has Stage I inner-vision encoder frame merging for temporal compression and Stage II decoupled spatial selection for dynamic/static spatial token reduction.

Source: TeX `\includegraphics` from `secs/3_method.tex`, original asset `figs/method.pdf`; exported to PNG with `pdftoppm -cropbox` from the figure PDF. The PDF CropBox and MediaBox are both `995 x 357 pts`, so the render uses the visible figure bounds rather than a full paper page.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| MVBench | Video understanding / QA | not reported | Score / accuracy ↑ | 主实验四个 benchmark 之一。 |
| EgoSchema | Long-form video QA | not reported | Score / accuracy ↑ | 用于检验长视频理解能力。 |
| LongVideoBench | Long-video understanding | not reported | Score / accuracy ↑ | 主表中写作 LongVideoBench。 |
| VideoMME | Multi-duration video understanding | not reported | Score / accuracy ↑ | Qwen2.5-VL 补充实验还拆成 Short / Medium / Long。 |
| Efficiency suite | Inference efficiency | LLaVA-OneVision / LLaVA-Video / Qwen2.5-VL settings | TTFT ↓, throughput ↑, prefilling FLOPs ↓ | 效率结果主要在单张 NVIDIA A100 上测量；实现也报告使用 RTX 4090。 |

### Main Results: LLaVA-OneVision-7B

主表关注 LLaVA-OneVision-7B。下表保留论文中最关键的效率与准确率列；TTFT / FLOPs 越低越好，throughput / benchmark score 越高越好。

| Method | Retained Ratio | FLOPs (T) ↓ | FLOPs Ratio ↓ | TTFT (ms) ↓ | Throughput ↑ | MVBench | EgoSchema | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-OV-7B | 100% | 82.6 | 100% | 889.9 | 24.4 | 58.3 | 60.4 | 56.4 | 58.6 | 58.4 | 100 |
| FastV | 100% | 51.1 | 61.9% | 820.0 | 28.4 | 55.9 | 57.5 | 56.7 | 56.1 | 56.5 | 96.7 |
| PyramidDrop | 100% | 51.8 | 62.7% | 813.4 | 28.3 | 56.1 | 58.0 | 54.1 | 56.4 | 56.2 | 96.2 |
| DyCoke | 25% | 50.5 | 61.1% | 905.6 | 21.1 | 53.1 | 59.5 | 49.5 | 54.3 | 54.1 | 92.6 |
| VisionZip | 25% | 50.5 | 61.1% | 516.6 | 29.4 | 57.9 | 60.3 | 56.5 | 58.2 | 58.2 | 99.7 |
| PruneVid | 25% | 50.5 | 61.1% | 703.6 | 29.4 | 57.4 | 59.9 | 55.7 | 57.4 | 57.6 | 98.6 |
| FastVID | 25% | 50.5 | 61.1% | <u>581.6</u> | 26.9 | 56.5 | 58.2 | 56.3 | 58.0 | 57.3 | 98.1 |
| HoliTom | 25% | <u>49.0</u> | <u>59.3%</u> | 661.3 | <u>29.9</u> | 58.4 | 61.2 | 56.7 | 58.9 | 58.8 | 100.7 |
| **EarlyTom** | 25% | **36.5** | **44.2%** | **426.3** | **32.9** | 57.4 | 60.5 | 56.3 | 58.5 | 58.2 | 99.7 |
| VisionZip | 20% | 48.7 | 58.9% | <u>495.0</u> | 29.8 | 57.7 | 59.8 | 55.2 | 57.9 | 57.7 | 98.8 |
| PruneVid | 20% | 49.0 | 59.3% | 662.1 | 29.5 | 57.2 | 59.7 | 54.7 | 56.9 | 57.1 | 97.8 |
| FastVID | 20% | 48.7 | 58.9% | 546.6 | 27.6 | 56.3 | 57.9 | 57.1 | 57.9 | 57.3 | 98.1 |
| HoliTom | 20% | <u>47.5</u> | <u>57.5%</u> | 622.3 | <u>30.0</u> | 58.7 | 61.0 | 57.1 | 58.6 | 58.8 | 100.7 |
| **EarlyTom** | 20% | **35.1** | **42.4%** | **415.3** | **33.4** | 57.8 | 60.6 | 55.6 | 58.0 | 58.1 | 99.3 |
| VisionZip | 15% | 46.9 | <u>56.8%</u> | <u>475.9</u> | **32.1** | 56.5 | 59.8 | 54.4 | 56.1 | 56.7 | 97.1 |
| PruneVid | 15% | 47.5 | 57.5% | 574.1 | 27.1 | 56.8 | 59.7 | 55.4 | 56.6 | 57.1 | 97.8 |
| FastVID | 15% | 46.9 | 56.8% | 530.8 | 28.7 | 56.0 | 57.4 | 56.2 | 57.7 | 56.8 | 97.3 |
| HoliTom | 15% | <u>46.0</u> | 55.7% | 572.7 | 27.5 | 58.1 | 61.2 | 56.4 | 57.3 | 58.2 | 99.7 |
| **EarlyTom** | 15% | **33.6** | **40.7%** | **390.6** | <u>30.4</u> | 57.5 | 60.2 | 54.4 | 56.9 | 57.3 | 98.1 |
| VisionZip | 10% | 45.2 | 54.7% | <u>458.5</u> | 28.5 | 53.5 | 58.0 | 49.3 | 53.4 | 53.5 | 91.6 |
| PruneVid | 10% | 45.9 | 55.6% | 592.2 | 28.6 | 56.2 | 59.8 | 54.5 | 56.0 | 56.6 | 96.9 |
| FastVID | 10% | 45.2 | 54.7% | 502.1 | 28.3 | 55.9 | 56.5 | 56.3 | 57.3 | 56.5 | 96.7 |
| HoliTom | 10% | <u>44.6</u> | <u>54.0%</u> | 556.6 | <u>29.0</u> | 57.3 | 61.2 | 56.3 | 56.8 | 57.9 | 99.1 |
| **EarlyTom** | 10% | **32.2** | **39.0%** | **336.2** | **31.6** | 56.5 | 60.1 | 52.4 | 55.8 | 56.2 | 96.2 |

解读：EarlyTom 在所有 retained ratios 下都给出最低 TTFT 和最低 prefilling FLOPs；accuracy 不总是最高，但 10% retention 仍保留 96.2% baseline average score。

### Cross-Backbone: LLaVA-OneVision-0.5B

| Method | Retained Ratio | FLOPs (T) ↓ | TTFT (ms) ↓ | Throughput ↑ | MVBench | EgoSchema | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-OV-0.5B | 100% | 45.3 | 413.7 | 42.7 | 45.5 | 26.8 | 45.8 | 43.7 | 40.5 | 100 |
| FastVID | 25% | 42.4 | 409.9 | 25.9 | 44.7 | 25.3 | 44.9 | 42.1 | 39.3 | 97.0 |
| VisionZip | 25% | 42.4 | <u>368.6</u> | <u>41.1</u> | 45.6 | 27.7 | 45.9 | 42.9 | 40.5 | 100.0 |
| HoliTom | 25% | <u>42.3</u> | 519.4 | 35.2 | 45.8 | 27.6 | 46.2 | 44.4 | 41.0 | 101.2 |
| **EarlyTom** | 25% | **29.9** | **331.5** | **47.8** | 45.5 | 27.4 | 46.3 | 43.4 | 40.7 | 100.4 |
| FastVID | 20% | 42.3 | 412.6 | 28.8 | 43.8 | 25.7 | 44.3 | 41.6 | 38.9 | 96.0 |
| VisionZip | 20% | 42.3 | <u>368.5</u> | **42.3** | 45.1 | 27.5 | 44.8 | 42.7 | 40.0 | 98.8 |
| HoliTom | 20% | <u>42.2</u> | 499.4 | 38.3 | 45.5 | 27.7 | 45.9 | 44.1 | 40.8 | 100.7 |
| **EarlyTom** | 20% | **29.8** | **313.1** | <u>40.6</u> | 45.2 | 27.5 | 44.7 | 43.7 | 40.3 | 99.5 |
| FastVID | 15% | 42.1 | 411.3 | 29.4 | 43.1 | 25.3 | 44.7 | 40.7 | 38.5 | 95.1 |
| VisionZip | 15% | <u>42.1</u> | <u>367.1</u> | **37.8** | 44.6 | 26.9 | 44.9 | 42.3 | 39.7 | 98.0 |
| HoliTom | 15% | 42.1 | 473.9 | 34.1 | 45.4 | 27.6 | 46.4 | 43.4 | 40.7 | 100.4 |
| **EarlyTom** | 15% | **29.7** | **311.1** | <u>35.1</u> | 44.8 | 27.0 | 44.9 | 42.3 | 39.8 | 98.3 |
| FastVID | 10% | 42.0 | 408.5 | 31.9 | 42.7 | 24.7 | 44.2 | 40.7 | 38.1 | 94.1 |
| VisionZip | 10% | <u>42.0</u> | <u>366.1</u> | 38.7 | 43.2 | 25.8 | 42.6 | 40.0 | 37.9 | 93.6 |
| HoliTom | 10% | 42.0 | 457.1 | <u>39.6</u> | 45.0 | 27.3 | 44.5 | 43.3 | 40.0 | 98.8 |
| **EarlyTom** | 10% | **29.6** | **280.1** | **43.9** | 44.3 | 26.8 | 44.5 | 41.8 | 39.4 | 97.3 |

0.5B 上 EarlyTom 同样显著降低 TTFT 和 FLOPs；不过 accuracy advantage 不总是绝对领先，说明更小模型下 compression 的质量/效率 trade-off 更敏感。

### Supplementary Generalization: LLaVA-Video-7B and Qwen2.5-VL-7B

| Model | Method | Retained Ratio | FLOPs (T) ↓ | TTFT (ms) ↓ | Throughput ↑ | MVBench | EgoSchema | LongVideoBench | VideoMME | Avg Score | Avg % |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| LLaVA-Video-7B | Vanilla | 100% | 246.2 | 6429.3 | 8.1 | 60.4 | 57.2 | 58.9 | 64.3 | 60.2 | 100 |
| LLaVA-Video-7B | FastV | 100% | 158.2 | 3494.3 | 10.0 | 54.3 | 54.1 | 55.0 | 58.8 | 55.6 | 92.4 |
| LLaVA-Video-7B | PyramidDrop | 100% | 159.4 | 3494.8 | 10.1 | 55.9 | 54.3 | 54.7 | 61.9 | 56.7 | 94.2 |
| LLaVA-Video-7B | VisionZip | 15% | 159.4 | 3241.4 | 14.2 | 56.7 | 54.7 | 54.7 | 60.7 | 56.7 | 94.2 |
| LLaVA-Video-7B | HoliTom | 15% | <u>156.6</u> | <u>1669.5</u> | **17.1** | 57.7 | 54.8 | 56.2 | 62.1 | 57.7 | 95.8 |
| LLaVA-Video-7B | **EarlyTom** | 15% | **86.4** | **947.4** | <u>16.7</u> | 55.8 | 54.7 | 53.9 | 61.3 | 56.4 | 93.7 |

| Method on Qwen2.5-VL-7B | FLOPs (T) ↓ | FLOPs Ratio ↓ | TTFT (ms) ↓ | MVBench | VideoMME Short | VideoMME Medium | VideoMME Long | VideoMME Avg | Avg Score |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen2.5-VL-7B | 554.7 | 100% | 6842 | 67.1 | 76.0 | 66.0 | 55.1 | 65.7 | 66.4 |
| Average Pooling | 91.9 | 16.6% | 4609 | 56.8 | 66.4 | 57.3 | 51.1 | 58.3 | 57.6 |
| Uniform Subsampling | <u>91.9</u> | <u>16.6%</u> | <u>4578</u> | 57.7 | 68.6 | 59.6 | **55.0** | 60.8 | 59.3 |
| EarlyTom w/o Decoupled Spatial Token Selection | 67.7 | 12.2% | 3667 | <u>60.7</u> | **71.0** | <u>61.6</u> | <u>53.6</u> | **62.0** | <u>61.4</u> |
| EarlyTom w/o Weighted Frame Merging | 67.7 | 12.2% | 3667 | <u>60.7</u> | 70.5 | **62.3** | 52.7 | 61.8 | 61.3 |
| **EarlyTom** | **67.7** | **12.2%** | **3667** | **62.5** | <u>70.7</u> | <u>61.6</u> | <u>53.6</u> | <u>61.9</u> | **62.2** |

### Ablations / Analysis

**Compression modules on LLaVA-OneVision-7B**

| Method | Retained Ratio | MVBench | VideoMME | EgoSchema | Avg ↑ |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Vanilla | 100% | 58.3 | 58.6 | 60.4 | 59.1 |
| Only stage-1 | 73.9% | **57.9** | 57.0 | 60.3 | 58.4 |
| Only stage-2 | 20% | 57.3 | 57.6 | 60.4 | 58.4 |
| **EarlyTom** | 20% | 57.8 | **58.1** | **60.6** | **58.8** |

**Frame merging initial layer, compression ratio 0.2**

| #Layer | TTFT ↓ | Throughput ↑ | MVBench | VideoMME | EgoSchema | Avg ↑ |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Layer 4 | **380.0** | 31.6 | 57.4 | 57.9 | 60.4 | 58.6 |
| Layer 6 | 387.1 | **32.3** | **57.8** | **58.1** | 60.4 | **58.9** |
| Layer 8 | 421.1 | 30.7 | 57.5 | 58.0 | 60.4 | 58.6 |
| Layer 10 | 436.9 | 31.1 | 57.4 | 58.0 | **60.6** | 58.7 |

**Token sampling strategies, retain ratio 0.2**

| Sampling | Throughput ↑ | MVBench | VideoMME | EgoSchema | Avg ↑ |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Random | **35.3** | 57.0 | 56.6 | 59.8 | 57.8 |
| Top-K | 31.5 | 57.5 | 57.3 | 60.4 | 58.4 |
| **EarlyTom** | 33.4 | **57.8** | **58.1** | **60.6** | **58.8** |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Base models | LLaVA-OneVision-0.5B/7B; supplementary: LLaVA-Video-7B, Qwen2.5-VL-7B |
| Vision encoder | Pretrained SigLIP in official LLaVA-OneVision configuration |
| Video frames | LLaVA-OneVision uses 32 uniformly sampled frames; Qwen2.5-VL experiment uses maximum 768 frames |
| Efficiency hardware | Single NVIDIA A100 for reported main efficiency tables; experiments also conducted on NVIDIA A100 and RTX 4090 GPUs |
| TTFT measurement | NVIDIA Nsight Systems profiler |
| Throughput | Average over ten inference runs after warm-up; paper mentions two warm-up passes in the throughput formula paragraph |
| FLOPs scope | Vision encoding + LLM prefilling FLOPs, following HoliTom-style protocol but including vision encoder cost |
| Implementation | Incorporates HoliTom inner-LLM merging technique; custom Triton kernel for computational efficiency |
| Hyperparameters | EMA factor $\alpha=0.9$ in reported LLaVA-OneVision hyperparameter table; $\tau_{\mathrm{seg}}$ and selected layers vary by model, retained ratio, and benchmark |

## Limitations & Caveats

- 论文没有单独的 limitation section；这里的 caveats 来自实验设置和方法假设。
- EarlyTom 依赖 vision encoder hidden states 的 frame similarity 与 attention scores；如果 backbone 的 attention sink 行为、frame redundancy 或 token layout 不同，阈值和层选择可能需要重新调。
- LLaVA-OneVision 的 hyperparameter table 显示 $\tau_{\mathrm{seg}}$ 和 compression layers 按 benchmark / retained ratio 调整，说明开箱即用的统一配置还不是论文重点。
- Accuracy 对 aggressive compression 仍有下降：LLaVA-OneVision-7B 在 10% retention 下 avg score 为 56.2，相当于 baseline 的 96.2%，不是无损压缩。
- 主要优化 prefill / vision encoding；supplementary future work 明确指出 decoding stage 的 lengthy generation steps 仍值得进一步加速。
- 部分 baseline accuracy 结果来自 HoliTom 报告，跨方法比较依赖相同 benchmark protocol 与实现细节的一致性。

## Concrete Implementation Ideas

1. 在本地 Video-LLM inference stack 中先做 TTFT decomposition，确认 vision encoding 是否真的是主要瓶颈；如果不是，EarlyTom 的收益可能小于论文报告。
2. 先复现 Stage I：在 vision encoder 的第 6 层附近尝试 frame merging，记录 token count、TTFT 和 benchmark score，再逐步扫 layer 4/6/8/10。
3. 对 dynamic/static split 做可视化诊断：检查 head/tail frames 是否确实包含更多 motion-sensitive content，static frames 是否受 attention sinks 影响明显。
4. 为 static local-window Top-K 写单独 kernel 或 CPU path；对比 pure GPU Top-K、random sampling、local-window sampling 的 overhead。
5. 把 retained ratio 配置成 per-dataset/per-video-length policy，而不是单一全局阈值；长视频可更 aggressive，短而高动态视频保守一些。

## Open Questions / Follow-ups

- 是否能自动学习或估计 $\tau_{\mathrm{seg}}$、$\tau_{\mathrm{merge}}$ 和 layer positions，而不是按 benchmark 手动设定？
- 在大量 scene cuts、camera motion 或快速动作视频中，frame similarity segmentation 是否会过度保守或误 merge？
- 对非 SigLIP vision encoder、不同 patch size、或端到端训练过的 video encoder，attention sink 现象是否同样稳定？
- EarlyTom 与 KV cache pruning、speculative decoding、或 decoding-stage multimodal acceleration 能否组合成完整低延迟 pipeline？
- 如果把 decoupled spatial selection 作为可训练模块微调，是否能进一步恢复 10% retention 下的 accuracy？

## Citation

```bibtex
@article{wang2026earlytom,
  title = {EarlyTom: Early Token Compression Completes Fast Video Understanding},
  author = {Wang, Hesong and Jin, Xin and Lu, Lu and Li, Chenhaowen and Chen, Jian and Liu, Qiang and Wang, Huan},
  journal = {arXiv preprint arXiv:2605.30010},
  year = {2026},
  url = {https://arxiv.org/abs/2605.30010},
  eprint = {2605.30010},
  archivePrefix = {arXiv}
}
```
