---
title: M-LLM Based Video Frame Selection for Efficient Video Understanding
authors:
  - Kai Hu
  - Feng Gao
  - Xiaohan Nie
  - Peng Zhou
  - Son Tran
  - Tal Neiman
  - Lingyun Wang
  - Mubarak Shah
  - Raffay Hamid
  - Bing Yin
  - Trishul Chilimbi
conference:
year: 2025
arxiv_url: https://arxiv.org/abs/2502.19680v1
pdf_link: "[[assets/paper_2502.19680v1.pdf]]"
cover: "[[_assets/images/pipeline_2502.19680v1.png]]"
updated: 2026-05-19
tags:
  - paper/arxiv
  - video-qa
  - long-video
  - temporal-reasoning
  - question-aware
  - token-pruning
  - video-llm
status: unread
priority:
rating:
topics:
  - Video Understanding
code: ""
---

## TL;DR

- 论文针对 video M-LLM 常用 uniform sampling 在长视频里容易漏掉关键瞬间的问题，提出一个 question-aware、lightweight 的 frame selector。
- Selector 先从视频中 dense uniform sample 128 frames，再把每帧视觉 tokens 通过 spatial pooling 压到 $3\times3$，由 Qwen2.5 1.5B LLM backbone 输出每帧 importance score。
- 训练监督来自两个 pseudo-label signals：Qwen2-VL-7B 对单帧做 spatial relevance scoring，GPT-4o mini 在全部 frame captions 上做 temporal frame selection。
- 选出的 frames 送入冻结的 downstream video M-LLM；在 ActivityNet-QA、NExT-QA、EgoSchema、LongVideoBench 上，多种 downstream models 都有小幅但稳定提升。
- 长视频实验最有价值：在 LongVideoBench 上，selector 用 $n$ input frames 往往超过 uniform sampling 用 $2n$ input frames，支持“先看更密集候选，再按问题选择”的路线。

## Key Contributions

- 提出一个 plug-and-play 的 M-LLM based frame selector：不改 downstream video M-LLM 参数，只替换输入 frames 的选择方式。
- 把 frame selection 做成 question-aware：输入是 video frames 与 question，输出 $n$ 维 frame importance scores，而不是 query-agnostic 的固定 keyframe 选择。
- 用极强的 token compression 降低 selector 成本：每帧只保留 $3\times3$ visual tokens，假设“判断帧是否重要”不需要完整高分辨率视觉细节。
- 设计 spatial + temporal pseudo-labeling，在缺少人工 frame-level importance annotations 的情况下构造训练信号。
- 用 NMS-Greedy 从 importance scores 中选 $k$ 个非冗余 frames，避免 top-k 都落在相邻时间片段。

## Method

论文先重述常见的 $n$-frame video LLM 框架：从总帧数 $T$ 中 uniform sample $n$ frames，经 visual encoder $f_v$、alignment projector $g_a$ 和 optional spatial pooling 后送入 LLM：

$$
h_i = \textit{AvgPooling}(g_a(f_v(x_i))),\quad h_i\in\mathbb{R}^{m\times d}
$$

$$
r = \textit{LLM}(h_1, \cdots, h_n, Q)
$$

作者认为 uniform sampling 的核心问题是：$n$ 小会漏掉关键事件，$n$ 大会增加 video M-LLM 的 token cost，而且许多问题只依赖少量关键 frames。

Frame selector 的输入是 $n$ 个候选 frames 和问题 $Q$，输出每个 frame 的重要性分数：

$$
s = \textit{FrameSelector}(x_1, \cdots, x_n, Q)\in\mathbb{R}^{n}
$$

实现上，selector 在输入序列末尾加入 learnable score query $q_{score}$。由于 causal attention，score query 的 hidden state $e^q$ 可以聚合前面的 visual/text tokens，再用 MLP 映射到 $n$ 维 importance vector：

$$
e_1, \cdots, e_n, e^Q, e^q = \textit{LLM}(x_1, \cdots, x_n, Q, q_{score})
$$

$$
s = \textit{MLP}(e^q),\quad s\in\mathbb{R}^{n}
$$

选帧时不用 naive top-k，而是 NMS-Greedy：每次取最高分 frame，并把距离它不超过 $\delta=\mathrm{int}(n/(4k))$ 的邻近 frames 分数置为 $-1$，最后按时间顺序返回选中 indices。

```text
Input: importance scores s in R^n, target frame count k
Initialize delta = int(n / (4k))
Initialize selected list I_s = []
For step = 1..k:
  i = argmax(s)
  append i to I_s
  for every frame j with |i - j| <= delta:
    s[j] = -1
Sort I_s and return it
```

Pseudo labels 分两类生成：

- Spatial pseudo labels：对每个 frame 独立 prompt Qwen2-VL-7B，要求先解释再输出 `Evaluation: True/False`，用生成 True/False 的概率得到 frame score：

$$
s = p_{\text{True}}/(p_{\text{True}} + p_{\text{False}})
$$

- Temporal pseudo labels：先让 Qwen2-VL-7B 给 128 个 frames 生成 concise captions，再把全部 captions 和 question 交给 GPT-4o mini，要求输出最有帮助的 frame index list。入选 frames 记 1，否则记 0。

最终 pseudo labels 是 spatial 与 temporal scores 的平均。训练分两阶段：Stage 1 冻结 vision / LLM backbones，交替训练 visual instruction tuning 与 importance score prediction；Stage 2 只做 importance score prediction，并加入 LLM 的 LoRA weights。

## Pipeline Figure

![[_assets/images/pipeline_2502.19680v1.png]]

Caption: An illustration of the conventional n-frame video M-LLM framework and the proposed video M-LLM framework with frame selection.

Source: TeX `\includegraphics` from `sec/related.tex`, rendered from `sec/figures/figure2_new.pdf` with PDF crop bounds.

## Experiments

### Datasets / Benchmarks

| Dataset | Task | Split | Metric(s) | Notes |
| ---- | ---- | ---- | ---- | ---- |
| ActivityNet-QA | Open-ended video QA | not reported | GPT-3.5-evaluated accuracy / correctness | 中等长度 video QA；表中写作 `ActivityNet-QA` 或 `ANet-QA`。 |
| NExT-QA | Multi-choice video QA | not reported | Accuracy | 每题 5 个 options；作者 prefill `Option` 并用下一个生成 token 作为预测。 |
| EgoSchema | Long-form egocentric multi-choice QA | not reported | Accuracy | 每题 5 个 options；强调长视频理解。 |
| LongVideoBench | Long-context video-language understanding | not reported | Accuracy | 平均视频时长 473 seconds；用于 long-video QA 分析。 |

### Training / Compute

| Item | Value |
| ---- | ---- |
| Training data | VideoChat2 800K + TimeIT 125K + LLaVA-Video-178K 178K |
| Importance-score training subset | 400K video QA samples with video length longer than 5 seconds |
| Spatial pseudo-label model | Qwen2-VL-7B |
| Temporal pseudo-label caption model | Qwen2-VL-7B |
| Temporal pseudo-label selector | GPT-4o mini over all frame captions |
| Visual encoder | Pre-trained SigLIP ViT-Large |
| Selector LLM backbone | Qwen2.5 1.5B by default |
| Candidate frames | Uniformly sample $n=128$ frames |
| Visual tokens before pooling | $128\times16\times16$ |
| Visual tokens after pooling | $128\times3\times3$ |
| Stage 1 training | Batch size 128, learning rate $10^{-3}$, warm-up ratio 0.03, 2 epochs |
| Stage 2 training | Batch size 128, learning rate $10^{-5}$, first 3% warm-up, cosine LR scheduler, 5 epochs |
| Speed measurement | float16, batch size 1, single A100 GPU, Hugging Face implementation |

### Main Results

下表把论文中最核心的“同一 downstream model，uniform frames vs. selected frames”摘出来。`Reported Δ` 按原表保留；ActivityNet-QA 的 score 是 accuracy / correctness。

| Dataset | Downstream model | Size | Baseline / Uniform score | + Selector score | Reported Δ | Metric |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| ActivityNet-QA | PLLaVA | 7B | 56.3 / 3.5 | 57.6 / 3.5 | 1.3 ↑ | accuracy / correctness |
| ActivityNet-QA | PLLaVA | 34B | 60.9 / 3.7 | 62.3 / 3.6 | 1.4 ↑ | accuracy / correctness |
| ActivityNet-QA | LLaVA-NeXT-Video | 7B | 53.5 / 3.2 | 55.1 / 3.4 | 1.6 ↑ | accuracy / correctness |
| ActivityNet-QA | LLaVA-NeXT-Video | 34B | 58.8 / 3.4 | 60.2 / 3.5 | 1.4 ↑ | accuracy / correctness |
| NExT-QA | LLaVA-NeXT-Video | 7B | 62.4 | 63.4 | 1.0 ↑ | accuracy |
| NExT-QA | LLaVA-NeXT-Video | 34B | 68.1 | 69.3 | 1.2 ↑ | accuracy |
| NExT-QA | Idefics2 | 8B | 68.0 | 69.1 | 1.1 ↑ | accuracy |
| NExT-QA | Qwen2-VL | 7B | 77.6 | 78.4 | 0.8 ↑ | accuracy |
| EgoSchema | LLaVA-NeXT-Video | 7B | 45.8 | 47.2 | 1.3 ↑ | accuracy |
| EgoSchema | LLaVA-NeXT-Video | 34B | 48.6 | 50.6 | 2.0 ↑ | accuracy |
| EgoSchema | Idefics2 | 8B | 56.6 | 57.9 | 1.3 ↑ | accuracy |
| EgoSchema | Qwen2-VL | 7B | 64.6 | 65.9 | 1.1 ↑ | accuracy |

作者还把方法放在 SOTA context 中比较：ActivityNet-QA 表里 Tarsier 34B 为 61.6 / 3.7，PLLaVA + Selector 34B 为 62.3 / 3.6；NExT-QA 表里 Tarsier 34B 为 79.2，Qwen2-VL + Selector 7B 为 78.4；EgoSchema 表里 Tarsier 34B 为 68.6，Qwen2-VL + Selector 7B 为 65.9。也就是说，论文的主张重点不是全面刷新 SOTA，而是证明 selector 可以 plug-and-play 提升不同 downstream models。

### Ablations / Analysis

**Frame selection method.** LLaVA-NeXT-Video 7B 上，temporal reasoning pseudo labels 比单帧 spatial labels 更强；训练出的 lightweight selector 接近 pseudo labels 直接选帧的效果。

| Selection Method | ANet-QA | NExT-QA |
| ---- | ---- | ---- |
| Uniform sampling | 53.5 | 62.4 |
| Scores from CLIP similarity | 53.7 | 62.2 |
| Pseudo labels from SeViLA | 54.0 | 63.2 |
| Spatial pseudo labels | 54.2 | 63.6 |
| Spatial & temporal pseudo | 55.5 | 63.9 |
| Scores from trained selector | 55.1 | 63.4 |

**Frame budget and speed.** LLaVA-NeXT-Video 34B on NExT-QA。前四行是 uniform sampling，后四行是从 128 candidates 中用 selector 选帧。

| # frames | Acc@C | Acc@T | Acc@D | Acc | Speed (s) |
| ---- | ---- | ---- | ---- | ---- | ---- |
| 4 | 67.2 | 61.2 | 73.9 | 66.4 | 0.56 |
| 8 | 68.7 | 62.5 | 76.9 | 68.1 | 0.92 |
| 16 | 69.1 | 63.6 | 76.8 | 68.7 | 1.71 |
| 32 | 69.5 | 64.3 | 78.4 | 69.3 | 3.40 |
| $128\rightarrow4$ | 68.5 | 64.5 | 75.7 | 68.5 | 0.76 |
| $128\rightarrow8$ | 69.3 | 64.9 | 77.5 | 69.3 | 1.12 |
| $128\rightarrow16$ | 69.4 | 64.8 | 78.5 | 69.5 | 1.91 |
| $128\rightarrow32$ | 69.2 | 65.6 | 78.7 | 69.6 | 3.50 |

关键结论是：selector 的 $n$-frame input 可以接近或超过 uniform 的 $2n$-frame input。例如 $128\rightarrow4$ 的 Acc 为 68.5，高于 8-frame uniform 的 68.1，且 speed 为 0.76s，快于 8-frame uniform 的 0.92s。

**Tokens per frame in selector.** Default 是 9 tokens/frame；25 tokens/frame 只带来很小提升，支持 aggressive pooling 的设计。

| # tokens / frame | ActivityNet-QA | NExT-QA | EgoSchema |
| ---- | ---- | ---- | ---- |
| no selector | 53.5 | 62.4 | 45.8 |
| 1 | 53.2 | 62.7 | 46.6 |
| 9 | 55.1 | 63.4 | 47.2 |
| 25 | 55.3 | 63.6 | 47.3 |

**Selector backbone size.** 更大的 selector LLM 更好，但 1.5B 已经带来主要收益。

| Backbone size | ActivityNet-QA | NExT-QA | EgoSchema |
| ---- | ---- | ---- | ---- |
| no selector | 53.5 | 62.4 | 45.8 |
| 0.5B | 53.8 | 62.8 | 46.4 |
| 1.5B | 55.1 | 63.4 | 47.2 |
| 7B | 55.5 | 64.0 | 47.9 |

**LongVideoBench.** 两个 downstream video-LLMs 上，selector 在相同 frame budget 下明显强于 uniform，并且常常超过 uniform 的更大 frame budget。

| Model | # frames | Uniform | Selector |
| ---- | ---- | ---- | ---- |
| LLaVA-NeXT-Video 34B | 4 | 45.3 | 49.5 |
| LLaVA-NeXT-Video 34B | 8 | 46.9 | 49.9 |
| LLaVA-NeXT-Video 34B | 16 | 48.1 | 49.8 |
| LLaVA-NeXT-Video 34B | 32 | 49.7 | 50.0 |
| Qwen2-VL 7B | 4 | 48.0 | 55.0 |
| Qwen2-VL 7B | 8 | 50.9 | 56.0 |
| Qwen2-VL 7B | 16 | 53.6 | 56.5 |
| Qwen2-VL 7B | 32 | 53.3 | 57.0 |

**Spatial pseudo-label source.** Appendix 显示，更强的 prompting M-LLM 会给出更好的 spatial pseudo labels。

| Spatial pseudo-label M-LLM | ANet-QA | NExT-QA |
| ---- | ---- | ---- |
| No pseudo-labels | 53.5 | 62.4 |
| LLaVA-NeXT 7B | 53.9 | 62.8 |
| Idefics2 8B | 53.8 | 63.2 |
| Qwen2-VL 7B | 54.2 | 63.6 |

**Candidate pool size before selection.** Appendix 强调先密集采样 128 candidates 很重要，尤其是长视频场景。

| Candidate setting | EgoSchema | LongVideoBench |
| ---- | ---- | ---- |
| Uniform 4 frames | 45.8 | 45.3 |
| $16\rightarrow4$ | 47.8 | 46.0 |
| $32\rightarrow4$ | 48.2 | 48.9 |
| $128\rightarrow4$ | 49.0 | 49.5 |

## Limitations & Caveats

- 训练信号依赖 expensive pseudo-label generation：spatial labels 需要 dense prompt M-LLM，temporal labels 还要先生成 frame captions 再调用 text LLM。
- Temporal pseudo labels 通过 captions 间接推理，可能丢失视觉细节，也可能引入 caption model hallucination。
- 实验主要覆盖 video QA；对于 dense captioning、temporal grounding、retrieval、multi-turn video dialogue 等任务，selector 的收益形态还未验证。
- Main result 的提升幅度多在 0.8 到 2.0 points；在严格低延迟系统里，selector overhead 是否值得需要按部署场景重新评估。
- 方法仍需要先 dense sample 128 candidate frames；如果视频解码、I/O、feature extraction 是瓶颈，端到端收益会小于表中只测 M-LLM inference 的数字。

## Concrete Implementation Ideas

- 在现有 video QA pipeline 中，把 selector 放在 downstream video M-LLM 前：先从视频抽 128 candidate frames，按 question 得到 frame scores，再只把选中 frames 送给冻结 M-LLM。
- 对长视频库可以缓存 candidate frames、SigLIP features 和 selector scores；同一视频多问题场景下，只需要重新跑 question-conditioned score head 或轻量 reranking。
- Multi-choice QA 可以进一步加入 option-aware selection：selector 输入 question + candidate options，比较是否比只看 question 更能定位判别性 frames。
- 给产品界面加 score timeline：显示 selected timestamps、NMS-suppressed neighbors 和 score curve，方便人工诊断模型为什么选这些 frames。
- 把 selector 与 high-resolution re-encoding 结合：先用低 token/frame 找关键片段，再对少量 selected frames 或短 clips 做更高分辨率视觉编码。

## Open Questions / Follow-ups

- Spatial 与 temporal pseudo labels 的最佳融合是否只是 averaging？是否可以学习一个 reliability-aware weighting？
- Selector 对 question wording 是否敏感？如果同一语义问题换表达，selected frames 是否稳定？
- 在 hour-level 或 streaming video 中，固定 128 candidate frames 是否足够，还是需要 hierarchical selection？
- NMS-Greedy 的邻域半径 $n/(4k)$ 是否能自适应 video motion / scene cuts？
- 如果 downstream M-LLM 已经有 strong temporal modeling 或 memory module，frame selector 的边际收益会不会下降？

## Citation

```bibtex
@misc{hu2025mllmbasedvideoframe,
      title={M-LLM Based Video Frame Selection for Efficient Video Understanding}, 
      author={Kai Hu and Feng Gao and Xiaohan Nie and Peng Zhou and Son Tran and Tal Neiman and Lingyun Wang and Mubarak Shah and Raffay Hamid and Bing Yin and Trishul Chilimbi},
      year={2025},
      eprint={2502.19680},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2502.19680}, 
}
```
