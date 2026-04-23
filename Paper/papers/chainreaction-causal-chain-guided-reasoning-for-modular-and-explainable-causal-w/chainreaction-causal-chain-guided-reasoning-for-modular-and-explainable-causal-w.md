---
title: "ChainReaction: Causal Chain-Guided Reasoning for Modular and Explainable Causal-Why Video Question Answering"
authors: ["Paritosh Parmar", "Eric Peh", "Basura Fernando"]
arxiv_id: "2508.21010v2"
arxiv_url: "https://arxiv.org/abs/2508.21010"
pdf_url: "https://arxiv.org/pdf/2508.21010.pdf"
published: 2025-08-28
updated: 2025-12-24
categories: ["cs.CV", "cs.AI", "cs.CL", "cs.HC", "cs.LG"]
tags: ["paper/arxiv", "status/read", "video-qa", "causal-reasoning", "explainability"]
status: "read"
code: ""
datasets: ["NextQA", "CausalVidQA", "CausalChaos!QA"]
pipeline_figure: "assets/pipeline_2508.21010.png"
pipeline_caption: "(Top) Concept figure: SCM factorization from monolithic V-Q-A to two-stage causal trace pipeline (CCE then CCDA)."
pipeline_source: "TeX includegraphics from Sections/Introduction.tex (Figs/approach_2-1_cropped.pdf), rasterized via pdftoppm"
---

## TL;DR
- Proposes a modular Causal-Why VideoQA pipeline: `CCE (video+question -> causal chain)` then `CCDA (question+chain+options -> answer)`.
- Uses natural-language causal chains as explicit intermediate reasoning traces for interpretability and debuggability.
- Builds a new human-verified causal-chain supervision set (46,024 samples) from NextQA, CausalVidQA, and CausalChaos!QA.
- Introduces CauCo (causal coherence score) to evaluate causal validity of generated chains.
- Reports stronger weighted-average QA accuracy than listed baselines/VLMs (71.22 vs 70.73 best baseline in their table) plus better human-rated explainability/trust.

## Key Contributions
- Structured decomposition of causal video QA with SCM + CoT motivation, replacing a black-box monolithic predictor.
- Two-stage training protocol with explicit separation boundary to avoid answer-loss gradients corrupting chain extraction.
- Human-in-the-loop chain construction pipeline: oracle LLM draft, programmatic checks, cross-LLM verification, manual video-grounded correction.
- Causality-oriented chain evaluation metric (CauCo).
- Empirical gains on QA, chain quality, out-of-domain chain transfer, and human study axes (explainability/trust/preference/debug utility).

## Method
Pipeline bullets:
- Input: video `V`, causal-why question `Q`, candidate options `O`.
- Stage 1 (CCE): fine-tuned VILA-3B generates causal chain `C` from `(V, Q)`.
- Stage 2 (CCDA): fine-tuned LLaMA-3.1-8B predicts answer `A` from `(Q, C, O)`.
- Training: stage-wise; CCE trained on chain supervision, then frozen while CCDA is trained.
- Inference: predicted chain (not GT) is passed to CCDA.

Compact pseudocode:
```text
C = CCE(V, Q)
A = CCDA(Q, C, O)
return A
```

## Pipeline Figure
![[assets/pipeline_2508.21010.png]]
Caption: (Top) Concept: factorize monolithic `V,Q -> A` into causal-trace-mediated reasoning with intermediate `C`.
Source: TeX includegraphics from `Sections/Introduction.tex` (`Figs/approach_2-1_cropped.pdf`), rasterized to PNG.

## Experiments
### Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
|---|---|---|---|---|
| NextQA | Causal-Why multiple-choice VideoQA | not reported | Accuracy | Source dataset for chain construction and QA eval |
| CausalVidQA | Causal-Why multiple-choice VideoQA | not reported | Accuracy | Source dataset for chain construction and QA eval |
| CausalChaos!QA | Causal-Why multiple-choice VideoQA | not reported | Accuracy | Source dataset for chain construction and QA eval |

### Main Results (QA)
| Dataset | Metric | Baseline | Ours | Delta |
|---|---|---:|---:|---:|
| NeXT-QA | Accuracy (%) | 70.75 (QwenVL 2.5-7B) | 63.95 | -6.80 |
| CausalVidQA | Accuracy (%) | 76.22 (QwenVL 2.5-7B) | 76.18 | -0.04 |
| CausalChaos!QA | Accuracy (%) | 62.80 (VILA 1.5-3B) | 67.65 | +4.85 |
| Average | Accuracy (%) | 65.05 (VILA 1.5-3B) | 69.26 | +4.21 |
| Weighted Avg | Accuracy (%) | 70.73 (QwenVL 2.5-7B) | 71.22 | +0.49 |

### Additional Results (Chain quality and upper bound)
| Dataset | Metric | Baseline | Ours | Delta |
|---|---|---:|---:|---:|
| Overall (GT chain upper bound) | CCDA Accuracy (%) | not applicable | 99.40 | not applicable |
| Overall chain generation | CCS | 0.75 (QwenVL2.5-3B oneshot) | 0.89 | +0.14 |
| OOD chain generation (CausalChaos! -> NextQA) | CCS | 0.42 (zero-shot VILA 1.5 baseline) | 0.84 | +0.42 |

### Human Studies
| Axis | Blackbox (%) | Ours (%) | No Preference (%) |
|---|---:|---:|---:|
| Explainability | 1.33 | 69.33 | 29.33 |
| Trustworthy | 1.33 | 62.67 | 36.00 |
| Human Preferred | 14.81 | 85.18 | not applicable |

### Training / Compute
| Item | Value |
|---|---|
| Framework | PyTorch |
| CCE backbone | VILA-3B |
| CCDA backbone | LLaMA-3.1-8B |
| QA setup | Multiple choice (5 options, 1 correct) |
| Training strategy | Stage-wise (CCE then CCDA; CCE frozen in CCDA stage) |
| CCE supervision size | 46,024 human-verified causal chains |
| Compute budget / GPUs | not reported |

## Limitations & Caveats
- Chain quality remains a bottleneck: the paper notes extractor mistakes (e.g., role/action misinterpretation) can degrade final QA.
- Some gains are concentrated in weighted average and CausalChaos; per-dataset best score is not uniformly achieved.
- Experimental details are deferred to appendix for some reproducibility-critical settings (full hyperparameters/compute).
- Human studies use six participants; useful signal, but still a small sample size.

## Concrete Implementation Ideas
- Reproduce the two-stage boundary explicitly in code: train `CCE` with chain loss, then freeze `CCE` and train `CCDA` only.
- Add automatic chain integrity stress-tests (mask/perturb links) as regression checks for reasoning dependence.
- Integrate a `CauCo`-style verifier in evaluation CI so chain-quality regressions are caught before QA evaluation.
- Build a failure-analysis dashboard separating errors into visual grounding vs language/decision stages.
- Extend OOD chain transfer experiments with additional domain shifts (e.g., real-world -> animated and vice versa).

## Open Questions / Follow-ups
- How robust is performance if chain quality drops incrementally under realistic noise (not synthetic perturbation)?
- Can joint but constrained training outperform strict stage-wise while preserving explainability?
- What is the annotation cost profile for expanding chain supervision beyond 46K samples?
- Does the method retain benefits with stronger 2026-era multimodal backbones in both stages?

## Citation
```bibtex
@article{parmar2025chainreaction,
  title={ChainReaction: Causal Chain-Guided Reasoning for Modular and Explainable Causal-Why Video Question Answering},
  author={Paritosh Parmar and Eric Peh and Basura Fernando},
  journal={arXiv preprint arXiv:2508.21010},
  year={2025},
  url={https://arxiv.org/abs/2508.21010}
}
```
