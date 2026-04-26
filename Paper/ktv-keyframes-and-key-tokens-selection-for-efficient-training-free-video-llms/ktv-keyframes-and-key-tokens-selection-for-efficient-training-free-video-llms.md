---
title: "KTV: Keyframes and Key Tokens Selection for Efficient Training-Free Video LLMs"
authors:
  - Baiyang Song
  - Jun Peng
  - Yuxin Zhang
  - Guangyao Chen
  - Feidiao Yang
  - Jianyuan Guo
conference: AAAI 2026
year: 2026
arxiv_url: https://arxiv.org/abs/2602.03615
pdf_link: "[[assets/paper_2602.03615.pdf]]"
cover: "[[assets/pipeline_2602.03615.png]]"
updated: 2026-04-26
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority: "5"
rating: "5"
topics:
  - Video Understanding
code: https://github.com/songbaiyang07-star/KTV
---

## TL;DR

- KTV 是一个面向 training-free Video LLMs 的两阶段压缩框架：先做 question-agnostic keyframe selection，再做 key visual token selection。
- 论文认为基于 CLIP text-frame similarity 的 question-relevant keyframe selection 容易掉进 “semantic traps”，即只抓住问题关键词相关画面，却漏掉因果/时间线索。
- 第一阶段用 DINOv2 提取全视频帧特征，再用 K-means 选出 $m=6$ 个代表性 keyframes，以降低 temporal redundancy。
- 第二阶段在每个 keyframe 内按 [CLS] attention importance 与 token redundancy 组合打分，并按 question-frame CLIP similarity 分配不同的 token budget。
- 在 NExT-QA、EgoSchema、IntentQA、STAR、VideoMME、MVBench、MLVU-Test 等 Multiple-Choice VideoQA benchmarks 上，KTV 在显著减少 visual tokens 的同时优于或接近 training-free baselines。
- 典型效率结果：KTV-sparse 只用 504 visual tokens；论文报告 60 分钟、10800 帧视频在 MLVU-Test 上可用 504 tokens 达到 44.8% accuracy。

## Key Contributions

1. 提出 KTV，一种无需 video-specific training 或 fine-tuning 的 training-free video understanding 框架，目标是同时减少 temporal redundancy 和 spatial redundancy。
2. 用 DINOv2 frame-level features + K-means 做 question-agnostic keyframe selection，避免 CLIP 文本相关筛帧对问题关键词过拟合。
3. 提出 key visual token selection：每个 token 的最终分数融合 [CLS] token attention importance 与 intra-frame token redundancy，并通过 $\alpha$ 控制二者权重。
4. 通过 $\beta^{\text{sparse}}$、$\beta^{\text{normal}}$、$\beta^{\text{dense}}$ 三组 token budget 控制推理成本，对应 504、936、1872 visual tokens。
5. 在多个 Multiple-Choice VideoQA benchmarks 上验证：KTV 用更少 tokens 达到 stronger 或 competitive accuracy，尤其在 long-video 场景中体现效率优势。

## Method

KTV 的输入是一段视频 $\mathcal{V}=\{I_1,I_2,\cdots,I_T\}$、question $Q$ 和候选答案。整体流程如下：

1. **Question-Agnostic Keyframe Selection**
   - 使用 DINOv2 提取每一帧的 visual feature：
     $$
     \{f_1,f_2,\ldots,f_T\}=\mathcal{E}_{dinov2}(\mathcal{V})
     $$
   - 对 frame features 做 K-means clustering，得到 $m$ 个 clusters。
   - 每个 cluster 选择距离 centroid 最近的 frame：
     $$
     j^*=\arg\min_{f_j\in C_i}\|f_j-c_i\|,\quad i\in[1,m]
     $$
   - 论文实验中设置 $m=6$，并按时间顺序重排选出的 keyframes。

2. **Key Visual Tokens Selection**
   - 对每个 keyframe $I_i'$，用 frozen VLM visual encoder 提取 token-level features：
     $$
     F_i=\mathcal{E}_{vis}(I_i')=\{t_{i,1},\ldots,t_{i,L}\},\quad i\in[1,m]
     $$
   - 计算 token 对 [CLS] token 的 importance score：
     $$
     S_{i,j}^{cls}=S^{cls}(t_{i,j})=\mathrm{softmax}\left(\frac{W_Q\cdot t_i^{cls}\cdot (W_K\cdot t_{i,j})^T}{\sqrt{d}}\right)
     $$
   - 计算 token 与同帧其他 tokens 的平均 cosine similarity 作为 redundancy score：
     $$
     S_{i,j}^{sim}=S^{sim}(t_{i,j})=\frac{1}{L-1}\sum_{k=1,k\neq j}^{L}\frac{f_{i,j}\cdot f_{i,k}}{\|f_{i,j}\|\cdot\|f_{i,k}\|}
     $$
   - 对两个分数归一化后，用 $\alpha$ 融合：
     $$
     S_{i,j}=\text{Norm}(S_{i,j}^{cls})\times\alpha+(1-\text{Norm}(S_{i,j}^{sim}))\times(1-\alpha)
     $$
   - 按最终分数保留 top-$k$ tokens；$k=\beta_i\cdot L$。
   - 用 CLIP-SIM 计算每个 keyframe 与 question 的相关性，把更高的 $\beta_i$ 分配给更 question-relevant 的 keyframe。

3. **LLM Input**
   - 保留的 visual tokens 经过 projection layer 对齐到 text embedding space。
   - 将 visual tokens 与 prompt/question text tokens 拼接后输入 LLaVA-v1.6，让 LLM 输出答案。

## Pipeline Figure

![[assets/pipeline_2602.03615.png]]

> *Caption: Framework of KTV, which is a two-stage method of training-free video understanding built upon LLaVA-v1.6. First, the method extracts video-frame visual features and clusters them into $m$ clusters, selecting centroid frames as keyframes to reduce temporal redundancy. Second, for each frame, it selects top-$k=\beta\cdot L$ key visual tokens by importance and redundancy, prunes the others, then concatenates remaining visual tokens with text tokens for the LLM answer generation.*

Source: TeX includegraphics from `Formatting-Instructions-LaTeX-2026.tex`, figure label `Fig_2`, copied from source asset `framework_png.png`.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| NExT-QA | Multiple-Choice VideoQA | not reported | Accuracy | 覆盖 causal/temporal reasoning 等问题类型 |
| EgoSchema | Multiple-Choice VideoQA | not reported | Accuracy | long-video understanding benchmark |
| IntentQA | Multiple-Choice VideoQA | not reported | Accuracy | 关注意图/因果相关理解 |
| STAR | Multiple-Choice VideoQA | not reported | Accuracy | 关注时序与情节理解 |
| VideoMME | Multiple-Choice VideoQA | not reported | Accuracy | 视频理解评测；论文排除 subtitles 等额外 reference data |
| MVBench | Multi-task VideoQA | not reported | Accuracy | 多任务视频理解 benchmark；细分结果在附录/补充材料 |
| MLVU-Test | Multi-task long-video understanding | not reported | Subcategory Accuracy, M-Avg | 包含 Holistic LVU、Single-Detail LVU、Multi-Detail LVU 子任务 |

### Main Results

Table 1 展示 KTV 在 Multiple-Choice VideoQA benchmarks 上的整体 accuracy。KTV rows 为论文提出方法；数值按论文表格抄录，`-` 表示 not reported。

| Method                   | Model / Setting   | Vis Encoder | NExTQA acc. (%) | EgoSchema acc. (%) | IntentQA acc. (%) | STAR acc. (%) | VideoMME acc. (%) | MVBench acc. (%) |
| ------------------------ | ----------------- | ----------- | --------------: | -----------------: | ----------------: | ------------: | ----------------: | ---------------: |
| *Training-Based Methods* |                   |             |                 |                    |                   |               |                   |                  |
| Video-LLaVA              | 7B                | ViT-L       |               - |                  - |                 - |             - |              39.9 |             41.0 |
| VideoLLaMA2              | 46.7B             | CLIP-L      |               - |               53.3 |                 - |             - |                 - |             53.9 |
| *Training-Free Methods*  |                   |             |                 |                    |                   |               |                   |                  |
| IG-VLM                   | 7B                | CLIP-L      |            63.1 |               35.8 |              60.3 |          48.6 |              39.7 |             42.9 |
| SF-LLaVA-7B              | 7B                | CLIP-L      |            64.0 |               44.2 |              60.5 |          48.8 |              39.4 |             43.3 |
| DYTO                     | 7B                | CLIP-L      |            65.7 |               48.6 |              61.6 |          50.7 |              41.2 |                - |
| **KTV-7B-sparse**        | 7B / 504 tokens   | CLIP-L      |        **64.5** |           **49.6** |          **61.2** |      **52.3** |          **43.6** |         **46.2** |
| **KTV-7B-normal**        | 7B / 936 tokens   | CLIP-L      |        **65.1** |           **50.4** |          **61.3** |      **52.5** |          **43.7** |         **46.4** |
| **KTV-7B-dense**         | 7B / 1872 tokens  | CLIP-L      |        **65.8** |           **51.0** |          **62.0** |      **52.7** |          **44.0** |         **46.0** |
| IG-VLM                   | 34B               | CLIP-L      |            70.7 |               53.4 |              64.5 |          50.5 |              50.3 |             49.0 |
| SF-LLaVA-7B              | 34B               | CLIP-L      |            70.9 |               55.0 |              66.1 |          51.3 |              51.9 |             49.6 |
| DYTO                     | 34B               | CLIP-L      |            72.9 |               56.8 |              66.4 |          51.1 |              53.4 |                - |
| **KTV-34B-sparse**       | 34B / 504 tokens  | CLIP-L      |        **71.2** |           **55.6** |          **65.9** |      **54.2** |          **52.2** |         **51.9** |
| **KTV-34B-normal**       | 34B / 936 tokens  | CLIP-L      |        **72.3** |           **55.6** |          **66.6** |      **54.6** |          **53.0** |         **52.1** |
| **KTV-34B-dense**        | 34B / 1872 tokens | CLIP-L      |        **72.7** |           **57.0** |          **68.0** |      **54.7** |          **53.2** |         **51.5** |

MLVU-Test 细分结果如下。TR/AR 属于 Holistic LVU，NQA/ER/PQA/SQA 属于 Single-Detail LVU，AO/AC/TQA 属于 Multi-Detail LVU。M-Avg 是平均准确率。

| Method | Model / Setting | Encoder | TR | AR | NQA | ER | PQA | SQA | AO | AC | TQA | M-Avg |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| *Training-Based Methods* |  |  |  |  |  |  |  |  |  |  |  |  |
| Video-LLaVA | 7B | CLIP-L | 70.3 | 38.5 | 13.3 | 26.4 | 26.0 | 38.9 | 20.0 | 21.7 | 20.9 | 30.7 |
| Video-LLaMA2 | 13B | CLIP-L | 52.7 | 12.8 | 13.3 | 17.0 | 12.0 | 19.4 | 15.7 | 8.3 | 18.6 | 18.9 |
| Video-LLaMA2 | 72B | CLIP-L | 80.2 | 53.8 | 36.7 | 54.7 | 54.0 | 38.9 | 42.9 | 16.7 | 32.6 | 45.6 |
| InternVL2 | 76B | InternViT-6B | 85.7 | 51.3 | 48.3 | 47.2 | 52.0 | 44.4 | 32.9 | 15.0 | 34.9 | 45.7 |
| *Training-Free Methods* |  |  |  |  |  |  |  |  |  |  |  |  |
| IG-VLM-7B | 7B | CLIP-L | 74.7 | 33.3 | 26.7 | 18.9 | 24.0 | 33.3 | 17.1 | 15.0 | 27.9 | 32.1 |
| SF-LLaVA-7B | 7B | CLIP-L | 68.1 | 23.1 | 25.0 | 34.0 | 24.0 | 33.3 | 22.9 | 16.7 | 16.3 | 32.7 |
| **KTV-7B-sparse** | 7B | CLIP-L | **73.6** | **43.6** | **35.0** | **41.5** | **34.0** | **36.1** | **27.1** | **18.3** | **20.9** | **36.5** |
| **KTV-7B-normal** | 7B | CLIP-L | **72.5** | **51.3** | **35.0** | **41.5** | **34.0** | **38.9** | **24.3** | **21.7** | **25.6** | **36.1** |
| **KTV-7B-dense** | 7B | CLIP-L | **69.2** | **48.9** | **33.3** | **39.6** | **34.0** | **38.9** | **27.1** | **23.3** | **27.9** | **36.9** |
| IG-VLM-34B | 34B | CLIP-L | 68.1 | 35.9 | 21.7 | 30.1 | 34.0 | 50.0 | 20.0 | 6.7 | 20.1 | 33.3 |
| SF-LLaVA-34B | 34B | CLIP-L | 76.9 | 43.6 | 36.7 | 39.6 | 44.0 | 47.2 | 27.1 | 8.3 | 32.6 | 43.6 |
| **KTV-34B-sparse** | 34B | CLIP-L | **81.3** | **51.3** | **53.3** | **47.2** | **50.0** | **52.8** | **37.1** | **11.7** | **34.9** | **44.8** |
| **KTV-34B-normal** | 34B | CLIP-L | **81.3** | **56.4** | **46.7** | **45.3** | **46.0** | **52.8** | **32.9** | **8.3** | **41.9** | **44.2** |
| **KTV-34B-dense** | 34B | CLIP-L | **85.7** | **51.3** | **48.7** | **47.2** | **48.0** | **58.3** | **35.7** | **10.0** | **37.2** | **45.0** |

### Ablations / Analysis

KTV-7B-normal 的 ablation 说明 CK、IS、RS 都有贡献，其中完整组合 CK+IS+RS 最优。CK: Cluster Keyframes; QK: Question-relevant Keyframes; IS: Importance Score; RS: Redundancy Score。

| Variant / Setting | NExTQA acc. (%) | EgoSchema acc. (%) | IntentQA acc. (%) | Notes |
| --- | ---: | ---: | ---: | --- |
| **CK+IS+RS** | **65.1** | **50.4** | **61.3** | full KTV-7B-normal |
| QK+IS+RS | 63.5 | 46.1 | 60.3 | 用 question-relevant keyframes 替代 cluster keyframes |
| CK+IS | 64.8 | 49.4 | 61.0 | 去掉 redundancy score |
| CK+RS | 64.6 | 48.6 | 60.9 | 去掉 importance score |
| RS+IS | 64.1 | 48.0 | 60.7 | 相当于没有 CK 的 keyframe selection setting |

关于 $\alpha$，论文报告 accuracy 随 $\alpha$ 增大整体上升，并在 0.8 或 0.9 附近达到峰值；同时组合 importance 与 redundancy 的方案持续优于 importance-only 或 redundancy-only。

### Training / Compute

| Item | Value |
| --- | --- |
| Base VLM | LLaVA-v1.6 |
| Visual encoder for keyframe clustering | DINOv2 |
| Visual encoder in reported tables | CLIP-L / ViT-L / InternViT-6B depending on method; KTV uses CLIP-L in reported rows |
| Keyframes | $m=6$ clusters/keyframes |
| Token budgets | KTV-sparse: 504 tokens; KTV-normal: 936 tokens; KTV-dense: 1872 tokens |
| Hardware | two Huawei Ascend 910C NPUs, 64 GB memory each |
| Extra reference data | subtitles and other external reference data are excluded |
| Efficiency examples | KTV-7B-sparse: 1.19s on NExTQA, 36.4% of SF-LLaVA-7B time; KTV-7B-dense: 1.35s, 41.3% of SF-LLaVA-7B time; KTV-34B-sparse: 1.23s, 28.0% of SF-LLaVA-34B time |

## Limitations & Caveats

- 论文主要评估 Multiple-Choice VideoQA；对于开放式 video captioning、free-form QA、dialogue-style video reasoning 的泛化仍需要额外验证。
- KTV 是 training-free，但不是 computation-free：它仍然需要对全视频帧提取 DINOv2 features 并做 clustering，长视频预处理成本需要单独评估。
- 第二阶段的 token budget 分配仍依赖 CLIP-SIM$(I_i',Q)$；如果问题文本与视觉内容存在 domain mismatch，question-aware token allocation 可能仍会有偏差。
- $\alpha$、$\beta$、$m=6$ 都是重要超参数；论文给出 ablation，但不同 video domains、不同 VLM backbone 下是否稳定还需要进一步测试。
- 表格中部分 baseline 数值来自不同方法/设置，硬件差异也可能影响推理时间比较；论文也提到在 Ascend 910C 上复现 IG-VLM 与 SF-LLaVA 时观察到精度差异。

## Concrete Implementation Ideas

1. 在现有 VideoQA pipeline 里先做一个 drop-in KTV sampler：输入 video frames 和 question，输出 selected keyframes + retained token indices。
2. 把 DINOv2 frame features 缓存到本地，避免每次 question 重跑全视频 frame encoding；keyframe clustering 可按视频级别复用。
3. 对 $\beta$ 做 task-aware 配置：短视频或细节型问题使用 dense，长视频检索/粗粒度理解使用 sparse 或 normal。
4. 做一个可视化 debug 面板：显示 cluster-selected keyframes、question-relevant ranking、每帧 token mask，方便排查 semantic traps。
5. 在开放式 QA 上增加 answer consistency check：比较 KTV-sparse/normal/dense 输出是否一致，以动态决定是否升级 token budget。

## Open Questions / Follow-ups

- DINOv2 clustering 选出的 keyframes 是否对镜头切换、字幕密集视频、第一人称视频同样稳定？
- 如果用 SigLIP、EVA-CLIP 或更强的 video encoder 替代 DINOv2/CLIP-L，keyframe selection 与 token pruning 的收益会如何变化？
- $\alpha$ 是否可以按 question type 或 frame content 自适应，而不是全局固定？
- KTV 的 token pruning 是否会影响 fine-grained OCR、small object、multi-person interaction 等需要局部细节的任务？
- 对 very long videos，是否可以做 hierarchical clustering 或 streaming clustering，降低全帧 feature extraction 与 K-means 的预处理成本？

## Citation

```bibtex
@misc{song2026ktvkeyframeskeytokens,
      title={KTV: Keyframes and Key Tokens Selection for Efficient Training-Free Video LLMs},
      author={Baiyang Song and Jun Peng and Yuxin Zhang and Guangyao Chen and Feidiao Yang and Jianyuan Guo},
      year={2026},
      eprint={2602.03615},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2602.03615},
}
```

