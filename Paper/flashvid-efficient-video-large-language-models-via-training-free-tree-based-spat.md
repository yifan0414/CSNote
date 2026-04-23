---
title: "FlashVID: Efficient Video Large Language Models via Training-free Tree-Based Spatiotemporal Token Merging"
authors: ["Ziyang Fan", "Keyu Chen", "Ruilong Xing", "Yulin Li", "Li Jiang", "Zhuotao Tian"]
arxiv_id: "2602.08024"
arxiv_url: "https://arxiv.org/abs/2602.08024"
pdf_url: "https://arxiv.org/pdf/2602.08024.pdf"
published: 2026-02-08
updated: 2026-02-19
categories: ["cs.CV", "cs.AI", "cs.CL", "cs.LG"]
tags: ["paper/arxiv", "status/read", "video-llm", "token-compression"]
status: "read"
code: "https://github.com/Fanziyang-v/FlashVID"
datasets: ["VideoMME", "EgoSchema", "LongVideoBench", "MVBench", "MLVU"]
pipeline_figure: "assets/pipeline_2602.08024.pdf"
pipeline_caption: "Overview of our FlashVID. FlashVID compresses visual tokens with ADTS and TSTM."
pipeline_source: "TeX includegraphics from sections/3_method.tex (figures/method.pdf)"
---

## TL;DR
- FlashVID is a training-free, plug-and-play VLLM acceleration method that combines ADTS (informative/diverse token selection) and TSTM (tree-based spatiotemporal token merging).
- Core claim: jointly modeling spatial and temporal redundancy works better than decoupled compression strategies for videos.
- At 10% retention on LLaVA-OneVision, FlashVID reports 58.4 average score with 99.1% relative accuracy vs vanilla.
- Under fixed token budget on Qwen2.5-VL, FlashVID enables up to 10x more frames and reports +8.6% relative average score (108.6 vs 100 baseline).
- Efficiency on LLaVA-OneVision: 6.3x prefilling speedup and 2.1x TTFT speedup at comparable accuracy.

## Key Contributions
- Proposes **FlashVID**, a 2-stage training-free compression framework for video LLM inference.
- Introduces **ADTS** (Attention and Diversity-based Token Selection), framing selection as calibrated max-min diversity.
- Introduces **TSTM** (Tree-based Spatiotemporal Token Merging), constructing cross-frame redundancy trees to merge correlated tokens.
- Demonstrates strong empirical results across 3 VLLMs and 5 video benchmarks.

## Method
Pipeline:
1. Input video features from vision encoder.
2. **ADTS** per frame: select representative tokens using pairwise diversity plus [CLS]-attention and event-relevance calibration.
3. **TSTM** across frames: connect each token to the most similar previous-frame token if similarity >= threshold \(T_\tau\), then aggregate each redundancy tree.
4. Optional inner-LLM pruning to satisfy token-budget alignment.

Compact pseudocode:
\[\hat{\mathcal{X}} = \text{TSTM}(E_v \setminus \text{ADTS}(E_v)) \cup \text{ADTS}(E_v)\]

## Pipeline Figure
![[assets/pipeline_2602.08024.pdf]]
Caption: Overview of FlashVID with ADTS + TSTM.
Source: TeX includegraphics from `sections/3_method.tex` using `figures/method.pdf`.

## Experiments

### Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---|---|---|
| VideoMME | Video QA / understanding | not reported | Overall score (accuracy-style benchmark score) | 900 videos, 2,700 MCQA pairs |
| EgoSchema | Egocentric long-video QA | not reported | Subset/Total score | ~5,000 MC questions over 250h egocentric video |
| LongVideoBench | Long-context interleaved video-language reasoning | not reported | Benchmark score | 3,763 videos, 6,678 MC questions |
| MVBench | Temporal multi-modal reasoning | not reported | Benchmark score | 20 tasks |
| MLVU | Long-video understanding | not reported | Benchmark score | 3,102 MC questions, 9 tasks |

### Main Results
| Dataset / Setting | Metric | Baseline | Ours | Δ |
|---|---|---:|---:|---:|
| LLaVA-OneVision, R=10% | Avg. Score | 58.4 (Vanilla, 100%) | 57.9 (FlashVID) | -0.5 |
| LLaVA-Video, R=10% | Avg. Score | 60.7 (Vanilla, 100%) | 58.2 (FlashVID) | -2.5 |
| Qwen2.5-VL, R=10% | Avg. Score | 61.6 (Vanilla, 100%) | 58.9 (FlashVID) | -2.7 |
| Qwen2.5-VL fixed budget, 16 -> 160 frames | Avg. Score | 52.6 (Vanilla 16f) | 57.1 (FlashVID, 160f @10%) | +4.5 |

### Training / Compute
| Item | Value |
|---|---|
| Training/inference mode | Training-free (inference-time acceleration) |
| Eval hardware (main) | NVIDIA A800 80G |
| Eval framework | LMMs-Eval |
| Efficiency study hardware | Single NVIDIA A100 (reported for LLaVA-OneVision efficiency table) |
| LLaVA-OneVision frame sampling | 32 frames, 32x196 visual tokens |
| LLaVA-Video frame sampling | 64 frames, 64x169 visual tokens |
| FlashVID default inner-LLM pruning layer | K = 20 |
| Expansion factor | f_e = 1.25 |
| Video partition threshold/min segments | S_tau = 0.9, M_s = 8 |

### Ablations / Analysis
| Setting | Key result |
|---|---|
| ADTS vs ATS/DTS | ADTS best relative accuracy (99.1) vs ATS (96.9), DTS (97.1) |
| ADTS-TSTM tradeoff alpha | Best at alpha=0.7 (rel. acc 99.1) |
| TSTM threshold T_tau | Best/near-best around T_tau=0.8 across tested VLLMs |
| Expansion factor f_e | Best reported around f_e in {1.25, 1.30}; paper uses 1.25 |

## Limitations & Caveats
- No explicit failure-case taxonomy in the main paper beyond qualitative appendix examples.
- Strong results rely on careful token-budget alignment; cross-paper comparisons can be sensitive to matching assumptions.
- Some benchmark details (official split/metric naming per benchmark) are summarized at high level in the paper text.
- Method adds multiple hyperparameters (thresholds/ratios/layer index), though authors claim shared defaults in most experiments.

## Concrete Implementation Ideas
- Implement ADTS as a pluggable pre-LLM module in an existing VLLM stack, then reuse TSTM for cross-frame merge.
- Start with published defaults (`K=20`, `f_e=1.25`, `S_tau=0.9`) and tune only retention ratio `R` for deployment latency targets.
- Reproduce fixed-budget frame expansion first (e.g., 16->80/160 frames) to validate long-context gains under equal compute.
- Add observability: log per-stage token counts and TTFT/prefill timings to verify budget alignment in production.

## Open Questions / Follow-ups
- How robust is ADTS calibration under domain shift (e.g., surveillance, medical, robotics videos)?
- Does TSTM remain stable for very long clips (>2h) with large scene discontinuities?
- Can the same tree-merging principle be adapted for streaming/online inference without full-video access?
- What is the best policy to auto-select `R` per input video complexity at runtime?

## Citation
```bibtex
@misc{fan2026flashvidefficientvideolarge,
  title={FlashVID: Efficient Video Large Language Models via Training-free Tree-based Spatiotemporal Token Merging},
  author={Ziyang Fan and Keyu Chen and Ruilong Xing and Yulin Li and Li Jiang and Zhuotao Tian},
  year={2026},
  eprint={2602.08024},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2602.08024}
}
```
