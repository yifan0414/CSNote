---
title: "ReAct: Synergizing Reasoning and Acting in Language Models"
authors: ["Shunyu Yao", "Jeffrey Zhao", "Dian Yu", "Nan Du", "Izhak Shafran", "Karthik Narasimhan", "Yuan Cao"]
arxiv_id: "2210.03629"
arxiv_url: "https://arxiv.org/abs/2210.03629"
pdf_url: "https://arxiv.org/pdf/2210.03629.pdf"
published: 2022-10-06
updated: 2023-03-10
categories: ["cs.CL", "cs.AI", "cs.LG"]
tags: ["paper/arxiv", "status/read", "reasoning", "agents", "llm"]
status: "read"
code: "https://react-lm.github.io/"
datasets: ["HotpotQA", "FEVER", "ALFWorld", "WebShop"]
pipeline_figure: "assets/pipeline_2210.03629.pdf"
pipeline_caption: "Comparison of prompting methods (Standard, CoT, Act-only, ReAct) and ALFWorld trajectories."
pipeline_source: "TeX includegraphics from iclr2023/figuretext/teaser.tex (file: iclr2023/figure/teaser-new.pdf)"
---

## TL;DR
- ReAct interleaves reasoning traces (Thought) and environment actions (Act), rather than using reasoning-only (CoT) or action-only prompting.
- On knowledge tasks with Wikipedia API interaction, ReAct improves over Act-only and is competitive with CoT; hybrid switching between ReAct and CoT-SC gives the best prompting results.
- **On interactive decision tasks, sparse reasoning gives large gains: +34 points success on ALFWorld (best ReAct 71 vs best Act 45) and +9.9 points on WebShop SR (40.0 vs 30.1).**
- Human analysis shows ReAct reduces hallucination compared with CoT, but can fail when search is uninformative or when trajectories loop.
- Fine-tuning on ReAct trajectories (3k examples) scales better than prompting-only for smaller PaLM models.

## Key Contributions
- Introduces ReAct, a prompting paradigm that augments the action space with natural-language reasoning steps.
- Demonstrates a unified method across both knowledge-intensive reasoning and sequential decision-making tasks.
- Provides controlled ablations against Standard prompting, CoT/CoT-SC, and Act-only baselines.
- Analyzes interpretability/trustworthiness tradeoffs and proposes ReAct<->CoT-SC switching heuristics.

## Method (with compact pseudocode or pipeline bullets)
Pipeline bullets:
1. Given current context $c_t = (o_1,a_1,\dots,o_t)$, prompt LLM to output either `Thought` (language action) or `Act` (environment action).
2. If output is `Thought`, append it to context; environment state is unchanged.
3. If output is `Act`, execute in environment/API and append returned observation `Obs`.
4. Repeat until `finish[...]` or step budget reached.
5. For knowledge tasks, optionally switch between ReAct and CoT-SC:
   - ReAct -> CoT-SC when no answer within step limit.
   - CoT-SC -> ReAct when self-consistency majority is weak.

## Pipeline Figure
![[assets/pipeline_2210.03629.pdf]]
Caption: Comparison of prompting trajectories for Standard/CoT/Act/ReAct on HotpotQA and Act vs ReAct on ALFWorld.
Source: TeX includegraphics from `iclr2023/figuretext/teaser.tex`.

## Experiments
### Datasets / Benchmarks
| Dataset | Task | Split | Metric(s) | Notes |
| --- | --- | --- | --- | --- |
| HotpotQA | Multi-hop QA | Question-only setup | Exact Match (EM) | Uses Wikipedia API with `search/lookup/finish` actions |
| FEVER | Fact verification | Claim-only setup | Accuracy | Labels: SUPPORTS/REFUTES/NOT ENOUGH INFO |
| ALFWorld | Text-based embodied decision making | 134 unseen eval games | Success Rate (%) | Task-specific prompts; 6 controlled prompt trials |
| WebShop | Web navigation/shopping | 500 test instructions | Score, Success Rate (SR) | 1.18M products; instruction-following purchase |

### Main results
| Dataset | Metric | Baseline | Ours | Δ |
| --- | --- | --- | --- | --- |
| HotpotQA | EM | Act-only: 25.7 | ReAct: 27.4 | +1.7 |
| FEVER | Acc | Act-only: 58.9 | ReAct: 60.9 | +2.0 |
| HotpotQA | EM | CoT-SC: 33.4 | CoT-SC->ReAct: 34.2 | +0.8 |
| HotpotQA | EM | CoT-SC: 33.4 | ReAct->CoT-SC: 35.1 | +1.7 |
| FEVER | Acc | CoT-SC: 60.4 | CoT-SC->ReAct: 64.6 | +4.2 |
| ALFWorld (All) | Success Rate (%) | Act-only best: 45 | ReAct best: 71 | +26 |
| WebShop | Success Rate (%) | Act-only: 30.1 | ReAct: 40.0 | +9.9 |

### Ablations / Analysis tables
| Study | Item | Value |
| --- | --- | --- |
| Human study (HotpotQA success) | True positive rate: ReAct vs CoT | 94% vs 86% |
| Human study (HotpotQA success) | False positive rate: ReAct vs CoT | 6% vs 14% |
| Human study (HotpotQA failure) | ReAct failure breakdown | Reasoning error 47%, search-result error 23%, label ambiguity 29% |
| Human study (HotpotQA failure) | CoT failure breakdown | Reasoning error 16%, hallucination 56%, label ambiguity 28% |

### Training / Compute (reported)
| Item | Value |
| --- | --- |
| Base prompting model | PaLM-540B |
| CoT-SC sampling | 21 samples, temperature 0.7 |
| ReAct few-shot exemplars | HotpotQA: 6; FEVER: 3 |
| ReAct step cap (hybrid heuristic) | HotpotQA: 7; FEVER: 5 |
| Fine-tuning data | 3,000 ReAct-generated correct trajectories |
| Fine-tuned model sizes | PaLM-8B and PaLM-62B |
| Decision task prompting | ALFWorld: 2-shot (from 3 annotated trajectories per task type), WebShop: 1-shot |

## Limitations & Caveats
- Prompting ReAct can be harder for smaller models; without fine-tuning it may underperform simpler prompting formats.
- In knowledge tasks, ReAct is sensitive to retrieval quality; non-informative search can derail trajectories.
- ReAct can enter repetitive loops in thought-action generation under greedy decoding.
- In-context learning has context-length constraints for long-horizon tasks with large action spaces.
- Reported prompting numbers remain far below domain-specific supervised SOTA on HotpotQA/FEVER.

## Concrete Implementation Ideas
- Build an explicit controller that monitors trajectory confidence and triggers ReAct<->CoT-SC switching dynamically.
- Add anti-loop decoding constraints (state hashing, repetition penalties, or beam search with diversity) for long-horizon environments.
- Improve retrieval grounding with stronger retrievers/tool APIs while preserving explicit thought-action traces.
- Fine-tune a smaller open model on mixed ReAct traces from QA + interactive domains for better transfer.
- Add trajectory validators that check factual claims against retrieved evidence before `finish[...]`.

## Open Questions / Follow-ups
- What is the best policy for deciding when to think vs act (learned scheduler vs prompting)?
- How much of ReAct’s gain comes from better retrieval queries vs better answer synthesis?
- Can ReAct traces be distilled into compact latent plans without sacrificing interpretability?
- How robust are gains with modern LLMs and stronger web/retrieval tools than the paper’s simple API?

## Citation
```bibtex
@article{yao2022react,
  title={ReAct: Synergizing Reasoning and Acting in Language Models},
  author={Yao, Shunyu and Zhao, Jeffrey and Yu, Dian and Du, Nan and Shafran, Izhak and Narasimhan, Karthik and Cao, Yuan},
  journal={arXiv preprint arXiv:2210.03629},
  year={2022},
  url={https://arxiv.org/abs/2210.03629}
}
```
