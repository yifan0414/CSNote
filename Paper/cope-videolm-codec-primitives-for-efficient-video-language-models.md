---
title: "CoPE-VideoLM: Codec Primitives For Efficient Video Language Models"
authors: ["Sayan Deb Sarkar", "Rémi Pautrat", "Ondrej Miksik", "Marc Pollefeys", "Iro Armeni", "Mahdi Rad", "Mihai Dusmanu"]
arxiv_id: "2602.13191v1"
arxiv_url: "https://arxiv.org/abs/2602.13191"
pdf_url: "https://arxiv.org/pdf/2602.13191.pdf"
published: 2026-02-13
updated: 2026-02-19
categories: ["cs.CV", "cs.AI", "cs.CL"]
tags: ["paper/arxiv", "status/read", "videolm", "video-compression"]
status: "read"
code: "https://sayands.github.io/cope"
datasets: ["PerceptionTest", "NextQA", "ActivityNet-QA", "VideoMME", "TempCompass", "TOMATO", "CVRR-ES", "MVBench", "LongVideoBench", "LVBench", "Video-TT", "Video-MMMU", "ScanQA", "SQA3D"]
pipeline_figure: "assets/pipeline_2602.13191.pdf"
pipeline_caption: "Overview of the pipeline: I-frames are encoded by a frozen RGB encoder, while P-frames are encoded into compact Delta-tokens from motion vectors and residuals."
pipeline_source: "TeX includegraphics from sec/3_method.tex (fig/pipeline.pdf)"
---

## 1. TL;DR
- CoPE-VideoLM replaces dense RGB encoding on most frames with codec primitives (motion vectors + residuals).
- I-frames use a standard frozen vision encoder; P-frames use a lightweight Delta-Encoder to produce compact Delta-tokens.
- Reported gains: **up to 86% lower TTFT and up to 93% lower token usage vs standard VideoLM setups.**
- Across 14 benchmarks, the method maintains or exceeds competitive open-source performance with much lower compute.
- The LLM architecture is unchanged; improvements come from codec-aware visual tokenization and training strategy.

## 2. Key Contributions
- Introduces codec-aware tokenization for VideoLMs, using compressed-domain signals directly.
- Proposes a dual-branch Delta-Encoder for motion/residual compression into a small token set.
- Uses **two-stage training** to align Delta-tokens with image-token space before end-to-end VideoLM fine-tuning.
- Demonstrates strong accuracy-efficiency trade-offs on general QA, temporal reasoning, long-form, and spatial tasks.

## 3. Method
- Frame representation:
  - I-frame: `X_I^(t) = phi_RGB(I^(t))`
  - P-frame: `X_P^(t) = phi_Delta(tau^(t), delta^(t))`
- Delta-Encoder:
  - Motion branch: MLP + transformer with `K_tau` learnable queries.
  - Residual branch: lightweight ResNet-18 + transformer with `K_delta` queries.
  - Default setting: `K_tau = K_delta = 4` so `N = 8` Delta-tokens per P-frame group.
- Token stream: interleave I-frame and P-frame tokens chronologically, then feed to the LLM.
- Training:
  - Stage 1: pretrain Delta-Encoder with patch-wise MSE alignment to frozen RGB encoder tokens.
  - Stage 2: end-to-end instruction fine-tune in VideoLM; pretraining-only branches are removed at this stage.

Compact pseudocode:
```text
for each frame t:
  if I-frame:
    tokens_t = phi_RGB(frame_t)
  else:
    tokens_t = phi_Delta(motion_vectors_t, residuals_t)
  append(tokens_t)

LLM(tokens_visual_interleaved, text_prompt)
```

## 4. Pipeline Figure
![[assets/pipeline_2602.13191.pdf]]
Caption: Overview of the pipeline: I-frames are encoded by a frozen RGB encoder, while P-frames are encoded into compact Delta-tokens from motion vectors and residuals.
Source: TeX includegraphics from `sec/3_method.tex` (`fig/pipeline.pdf`).

## 5. Experiments
### Datasets / Benchmarks
| Dataset        | Task                    | Split          | Metric(s)       | Notes                         |
| -------------- | ----------------------- | -------------- | --------------- | ----------------------------- |
| PerceptionTest | General video QA        | val            | Accuracy (%)    | Main and ablations            |
| NextQA         | General/temporal QA     | mc/test        | Accuracy (%)    | Main and ablations            |
| ActivityNet-QA | General video QA        | test           | GPT-based score | Main table uses GPT-4o        |
| VideoMME       | General video QA        | w/o sub, w sub | Accuracy (%)    | Broad comparison              |
| TempCompass    | Temporal reasoning      | test MCQ       | Accuracy (%)    | Temporal focus                |
| TOMATO         | Temporal reasoning      | test           | Accuracy (%)    | Temporal focus                |
| CVRR-ES        | Temporal reasoning      | test           | Accuracy (%)    | Temporal focus                |
| MVBench        | Temporal reasoning      | test           | Accuracy (%)    | Temporal/action understanding |
| LongVideoBench | Long-form understanding | val            | Accuracy (%)    | Long context                  |
| LVBench        | Long-form understanding | test           | Accuracy (%)    | Long context                  |
| Video-TT       | Instruction-following   | mc             | Accuracy (%)    | Long-form + instruction       |
| Video-MMMU     | Instruction-following   | test           | Accuracy (%)    | Long-form + instruction       |
| ScanQA         | Spatial QA              | test           | Accuracy (%)    | Supplementary                 |
| SQA3D          | Spatial QA              | test           | Accuracy (%)    | Supplementary                 |

### Main Results
| Dataset                                                     | Metric       | Baseline | Ours |       Δ |
| ----------------------------------------------------------- | ------------ | -------: | ---: | ------: |
| PerceptionTest (1 keyframe/GOP)                             | Accuracy (%) |     60.4 | 64.7 |    +4.3 |
| NextQA (1 keyframe/GOP)                                     | Accuracy (%) |     77.9 | 78.3 |    +0.4 |
| ActNet-QA (1 keyframe/GOP)                                  | Accuracy (%) |     61.7 | 62.3 |    +0.6 |
| PerceptionTest (2 keyframes/GOP)                            | Accuracy (%) |     62.1 | 67.8 |    +5.7 |
| NextQA (2 keyframes/GOP)                                    | Accuracy (%) |     79.2 | 80.3 |    +1.1 |
| ActNet-QA (2 keyframes/GOP)                                 | Accuracy (%) |     62.9 | 63.3 |    +0.4 |
| PerceptionTest (4 keyframes/GOP)                            | Accuracy (%) |     63.6 | 70.5 |    +6.9 |
| NextQA (4 keyframes/GOP)                                    | Accuracy (%) |     80.5 | 81.8 |    +1.3 |
| ActNet-QA (4 keyframes/GOP)                                 | Accuracy (%) |     63.6 | 64.1 |    +0.5 |
| Runtime (TTFT, 64-keyframe baseline vs Ours 1-keyframe/GOP) | Seconds      |     2.39 | 0.33 |  -86.2% |
| Runtime (E2EL, 64-keyframe baseline vs Ours 1-keyframe/GOP) | Seconds      |     3.78 | 1.66 | -56.01% |

### Training / Compute
| Item | Value |
|---|---|
| Base model | LLaVA-Video-7B (SigLIP + Qwen2) |
| Video preprocessing | MPEG-4, 30 FPS, GOP size 240 |
| P-frame fusion | `s = 30` (effective 1 FPS) |
| Delta pretraining data | PerceptionTest training videos (0-30s) |
| Fine-tuning data | LLaVA-Video-178K, 1.39M QA samples |
| Optimization (fine-tune) | LR `1e-5`, global batch size 128 |
| Main training compute | 64× A100-80G for 14 days (~21K GPU hours) |
| Delta pretraining compute (supp.) | 16× A100 for ~2 days, 113K iterations |

### Ablations / Analysis
| Setting                             | Observation                                                                                                |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Token-compression baselines vs CoPE | CoPE reports better benchmark scores at similar token budgets and avoids full RGB encoding for P-frames.   |
| Controlled ablation (8I vs 4I + 4P) | 4I+4P attains higher PerceptionTest accuracy with roughly half GOP tokens than 8I baseline setup in table. |
| Higher FPS scaling (1→3 FPS)        | Denser temporal coverage improves TempCompass and MVBench in supplementary analysis.                       |

## 6. Limitations & Caveats
- Method currently targets I/P-frames; B-frame handling is not integrated.
- Uses tensorized codec primitives; more native block/frequency-domain modeling may further improve efficiency.
- Fixed P-frame fusion window may be suboptimal across varied motion patterns.
- Some benchmark gaps vs larger-scale alternatives may be affected by training data scale/composition.

## 7. Concrete Implementation Ideas
- Build a pluggable `CodecTokenizer` module with drop-in compatibility for current VideoLM samplers.
- Expose `keyframes_per_gop` and `p_fusion_s` as first-class runtime knobs for latency/token budgeting.
- Reproduce two-stage training (alignment pretrain -> end-to-end tune) before scaling experiments.
- Add asynchronous serving path: RGB encoder for I-frames and codec branch for P-frames in parallel.
- Evaluate hybrid strategy: codec tokens + post-hoc token pruning for extra compression.

## 8. Open Questions / Follow-ups
- How to add B-frame support while preserving causal inference properties?
- Can direct DCT/block-level primitive modeling reduce Delta-Encoder overhead further?
- Should `K_tau` and `K_delta` be adaptive per video/task instead of fixed?
- Does two-stage pretraining remain beneficial at much larger training scales (>3M samples)?
- What is the best adaptive policy for GOP/keyframe density under strict latency SLAs?

## 9. Citation
```bibtex
@article{debsarkar2026cope,
  title={CoPE-VideoLM: Codec Primitives For Efficient Video Language Models},
  author={Sayan Deb Sarkar and Rémi Pautrat and Ondrej Miksik and Marc Pollefeys and Iro Armeni and Mahdi Rad and Mihai Dusmanu},
  journal={arXiv preprint arXiv:2602.13191},
  year={2026}
}
```

arXiv: https://arxiv.org/abs/2602.13191
