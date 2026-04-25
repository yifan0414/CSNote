---
title: "Toolformer: Language Models Can Teach Themselves to Use Tools"
authors:
  - Timo Schick
  - Jane Dwivedi-Yu
  - Roberto Dessi
  - Roberta Raileanu
  - Maria Lomeli
  - Luke Zettlemoyer
  - Nicola Cancedda
  - Thomas Scialom
arxiv_id: "2302.04761"
arxiv_url: https://arxiv.org/abs/2302.04761
pdf_url: https://arxiv.org/pdf/2302.04761.pdf
published: 2023-02-09
updated: 2023-02-09
categories:
  - cs.CL
tags:
  - paper/arxiv
  - status/read
  - topic/tool-use
  - topic/language-models
status: read
code: ""
datasets:
  - CCNet
  - LAMA
  - ASDiv
  - SVAMP
  - MAWPS
  - Web Questions
  - Natural Questions
  - TriviaQA
  - MLQA
  - TempLAMA
  - Dateset
  - WikiText
pipeline_figure: assets/pipeline_2302.04761.png
pipeline_caption: "Figure 2: Key steps in Toolformer's approach: sample candidate API calls, execute them, filter calls that do not reduce future-token loss, then interleave useful calls into the training text."
pipeline_source: TeX includegraphics from figures/approach.pdf
experiment_tables:
  - path: assets/experiment_table_2302.04761_1_main_results_lama.png
    type: main_results
    caption: "Table 3: Results on subsets of LAMA. Toolformer uses the question answering tool for most examples, clearly outperforming all baselines of the same size and achieving results competitive with GPT-3 (175B)."
    source: PDF fallback crop from arXiv PDF page 6; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_2_main_results_math.png
    type: main_results
    caption: "Table 4: Results for various benchmarks requiring mathematical reasoning. Toolformer makes use of the calculator tool for most examples, clearly outperforming even OPT (66B) and GPT-3 (175B)."
    source: PDF fallback crop from arXiv PDF page 6; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_3_main_results_qa.png
    type: main_results
    caption: "Table 5: Results for various question answering dataset. Using the Wikipedia search tool for most examples, Toolformer clearly outperforms baselines of the same size, but falls short of GPT-3 (175B)."
    source: PDF fallback crop from arXiv PDF page 7; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_4_main_results_mlqa.png
    type: main_results
    caption: "Table 6: Results on MLQA for Spanish (Es), German (De), Hindi (Hi), Vietnamese (Vi), Chinese (Zh) and Arabic (Ar). While using the machine translation tool to translate questions is helpful across all languages, further pretraining on CCNet deteriorates performance; consequently, Toolformer does not consistently outperform GPT-J. The final two rows correspond to models that are given contexts and questions in English."
    source: PDF fallback crop from arXiv PDF page 7; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_5_main_results_temporal.png
    type: main_results
    caption: "Table 7: Results for the temporal datasets. Toolformer outperforms all baselines, but does not make use of the calendar tool for TempLAMA."
    source: PDF fallback crop from arXiv PDF page 8; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_6_other_experimental_perplexity.png
    type: other_experimental
    caption: "Table 8: Perplexities of different models on WikiText and the validation subset of CCNet. Adding API calls comes without a cost in terms of perplexity for language modeling without any API calls."
    source: PDF fallback crop from arXiv PDF page 8; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_7_ablation_analysis_decoding_k.png
    type: ablation_analysis
    caption: "Table 9: Toolformer results on the T-REx subset of LAMA and on WebQS for different values of k used during decoding. Numbers shown are overall performance, performance on the subset where the model decides to make an API call, all remaining examples, and the percentage of examples for which the model decides to call an API."
    source: PDF fallback crop from arXiv PDF page 9; TeX source table caption/label in main.tex
  - path: assets/experiment_table_2302.04761_8_ablation_analysis_data_quality.png
    type: ablation_analysis
    caption: "Table 10: Examples of API calls for different tools, sorted by the filtering score. High values typically correspond to API calls that are intuitively useful for predicting future tokens."
    source: PDF fallback crop from arXiv PDF page 10; TeX source table caption/label in main.tex
Rating: "4"
---

# TL;DR

- Toolformer teaches a pretrained LM to call external tools through plain-text API calls without large human-labeled tool-use traces.
- The method samples possible API calls with in-context prompts, executes them, keeps calls that improve future-token prediction, and finetunes on the resulting augmented corpus.
- The paper tests tools for question answering, Wikipedia search, calculation, calendar/date handling, and machine translation.
- Its main claim is that a GPT-J-sized model can gain broad zero-shot task improvements from self-supervised tool-use training while preserving ordinary language-modeling ability.
- The approach is attractive because it is tool-agnostic, but it is limited to mostly single-step, non-interactive tool calls.

# Key Contributions

- Proposes a self-supervised pipeline for creating tool-use supervision from a raw language-modeling corpus plus a few demonstrations per tool.
- Introduces a loss-based filter: keep an API call only when the API response makes the next tokens easier for the model to predict than no call or an unanswered call.
- Shows that tool-use examples can be inserted back into the same kind of pretraining text, reducing the risk that the LM becomes a narrow task-specific system.
- Evaluates the idea across factual completion, math reasoning, open QA, multilingual QA, temporal/date reasoning, language modeling, scaling behavior, and decoding-strategy analysis.

# Method

1. Start with a plain-text corpus and a pretrained LM.
2. For each tool, write a few-shot prompt that asks the LM to insert candidate API calls into text.
3. Execute the sampled API calls with the actual external tool.
4. Compare future-token loss with the tool result, without the result, and without a tool call.
5. Keep only calls whose result reduces loss by the chosen threshold.
6. Merge retained calls from all tools into an augmented corpus and finetune the LM.
7. During inference, let the model generate until it asks for a tool result, execute the call, insert the result, and continue decoding.

# Pipeline Figure

![[assets/pipeline_2302.04761.png]]

Caption: Figure 2: Key steps in Toolformer's approach: sample candidate API calls, execute them, filter calls that do not reduce future-token loss, then interleave useful calls into the training text.

Source: TeX includegraphics from `figures/approach.pdf`.

# Experiments

Evaluation setup summary: the main model is based on GPT-J and is compared with GPT-J, GPT-J finetuned on CCNet, Toolformer with API calls disabled, OPT, and GPT-3 where reported. The benchmark suite covers factual completion, math reasoning, question answering, multilingual QA, temporal/date tasks, language modeling perplexity, scaling behavior, and decoding-strategy analysis. Metrics are task-specific accuracy-style scores or perplexity; exact result values are preserved in the original table crops below.

## Main Results

![[assets/experiment_table_2302.04761_1_main_results_lama.png]]

Caption: Table 3: Results on subsets of LAMA. Toolformer uses the question answering tool for most examples, clearly outperforming all baselines of the same size and achieving results competitive with GPT-3 (175B).

Source: PDF fallback crop from arXiv PDF page 6; TeX source table caption/label in main.tex

![[assets/experiment_table_2302.04761_2_main_results_math.png]]

Caption: Table 4: Results for various benchmarks requiring mathematical reasoning. Toolformer makes use of the calculator tool for most examples, clearly outperforming even OPT (66B) and GPT-3 (175B).

Source: PDF fallback crop from arXiv PDF page 6; TeX source table caption/label in main.tex

![[assets/experiment_table_2302.04761_3_main_results_qa.png]]

Caption: Table 5: Results for various question answering dataset. Using the Wikipedia search tool for most examples, Toolformer clearly outperforms baselines of the same size, but falls short of GPT-3 (175B).

Source: PDF fallback crop from arXiv PDF page 7; TeX source table caption/label in main.tex

![[assets/experiment_table_2302.04761_4_main_results_mlqa.png]]

Caption: Table 6: Results on MLQA for Spanish (Es), German (De), Hindi (Hi), Vietnamese (Vi), Chinese (Zh) and Arabic (Ar). While using the machine translation tool to translate questions is helpful across all languages, further pretraining on CCNet deteriorates performance; consequently, Toolformer does not consistently outperform GPT-J. The final two rows correspond to models that are given contexts and questions in English.

Source: PDF fallback crop from arXiv PDF page 7; TeX source table caption/label in main.tex

![[assets/experiment_table_2302.04761_5_main_results_temporal.png]]

Caption: Table 7: Results for the temporal datasets. Toolformer outperforms all baselines, but does not make use of the calendar tool for TempLAMA.

Source: PDF fallback crop from arXiv PDF page 8; TeX source table caption/label in main.tex

## Ablations / Analysis

![[assets/experiment_table_2302.04761_7_ablation_analysis_decoding_k.png]]

Caption: Table 9: Toolformer results on the T-REx subset of LAMA and on WebQS for different values of k used during decoding. Numbers shown are overall performance, performance on the subset where the model decides to make an API call, all remaining examples, and the percentage of examples for which the model decides to call an API.

Source: PDF fallback crop from arXiv PDF page 9; TeX source table caption/label in main.tex

![[assets/experiment_table_2302.04761_8_ablation_analysis_data_quality.png]]

Caption: Table 10: Examples of API calls for different tools, sorted by the filtering score. High values typically correspond to API calls that are intuitively useful for predicting future tokens.

Source: PDF fallback crop from arXiv PDF page 10; TeX source table caption/label in main.tex

## Other Experimental Checks

![[assets/experiment_table_2302.04761_6_other_experimental_perplexity.png]]

Caption: Table 8: Perplexities of different models on WikiText and the validation subset of CCNet. Adding API calls comes without a cost in terms of perplexity for language modeling without any API calls.

Source: PDF fallback crop from arXiv PDF page 8; TeX source table caption/label in main.tex

# Limitations & Caveats

- Toolformer cannot naturally chain tools because each tool call is generated independently during data creation.
- The method is not interactive: search-style tools return a result, but the LM does not browse, refine, or iteratively query.
- The model is sensitive to input wording when deciding whether to call a tool.
- Some tools are sample-inefficient under the paper's heuristics; useful calls can be sparse even after processing a large corpus.
- Tool-use decisions do not account for the computational or latency cost of calling a tool.
- Experimental table assets in this note are PDF fallback crops because the local environment did not provide a LaTeX compiler for direct TeX table rendering.

# Concrete Implementation Ideas

- Recreate the data-generation pipeline as a modular tool registry: each tool provides prompt examples, execution code, validation rules, and a cost model.
- Replace the single-step API insertion scheme with a trace format that supports multi-hop calls and tool chaining.
- Add a learned call-cost penalty during filtering so the LM learns when tool use is worth the expense.
- Use modern instruction-tuned models to generate candidate calls, then keep the paper's loss-based filter as a grounding mechanism.
- Build an evaluation harness that separates gains from tool execution, finetuning side effects, and decoding-time API-call thresholds.

# Open Questions / Follow-ups

- How much of the gain comes from better decoding-time access to tools versus representation changes from finetuning on tool traces?
- Would interactive retrieval or browser-like tools substantially improve the QA/search cases?
- Can the loss filter be made tool-aware, e.g. by accounting for latency, money, freshness, or reliability?
- Does the method still work when the base model is already instruction-tuned or tool-call-aware?
- What failure modes appear when API outputs are stale, adversarial, incomplete, or probabilistic?

# Citation

```bibtex
@article{schick2023toolformer,
  title={Toolformer: Language Models Can Teach Themselves to Use Tools},
  author={Schick, Timo and Dwivedi-Yu, Jane and Dessi, Roberto and Raileanu, Roberta and Lomeli, Maria and Zettlemoyer, Luke and Cancedda, Nicola and Scialom, Thomas},
  journal={arXiv preprint arXiv:2302.04761},
  year={2023}
}
```
