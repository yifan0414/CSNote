---
title: "Large Language Monkeys: Scaling Inference Compute with Repeated Sampling"
authors: ["Bradley Brown", "Jordan Juravsky", "Ryan Ehrlich", "Ronald Clark", "Quoc V. Le", "Christopher Ré", "Azalia Mirhoseini"]
conference: ""
year: 2024
arxiv_url: "https://arxiv.org/abs/2407.21787"
pdf_link: "[[assets/paper_2407.21787.pdf]]"
cover: "[[assets/pipeline_2407.21787.png]]"
updated: 2026-09-03
tags: ["paper/arxiv", "efficient-inference", "reasoning"]
status: "unread"
priority:
rating:
topics: ["LLM"]
code: "https://github.com/ScalingIntelligence/large_language_monkeys"
---

<!-- READ_PAPER_GENERATED_START -->
## TL;DR

- 论文把 **repeated sampling** 作为扩展 inference compute 的最简单基线：对同一问题独立采样许多候选解，再交给 verifier 选出最终答案。真正决定端到端收益的是两个量：能否生成正确答案的 **coverage**，以及能否从大量候选中找出它的 **precision**。
- 在五类 math、formal proof、competitive programming 与 software engineering 任务上，coverage 随样本数增长可持续到 $10{,}000$ 次采样；不少曲线可由 $c \approx \exp(a k^b)$ 近似，但 MiniF2F-MATH 等明显偏离，因而这只是经验性 inference-time scaling law，而非普适定律。
- 自动 verifier 能把 coverage 直接转化为成功率：DeepSeek-Coder-V2-Instruct 在 SWE-bench Lite 上由单次尝试的 $15.9\%$ 提升到 250 次尝试的 $56\%$，高于论文对照的单次尝试 SOTA $43\%$。
- 无可靠自动 verifier 时，生成更多候选并不等于最终性能持续提高。MATH 上 Llama-3-8B-Instruct 的 oracle coverage 从 100 次采样的 $82.9\%$ 增至 10,000 次的 $98.44\%$，但 majority voting / reward-model 系列方法中最大的提升仅为 $40.50\% \rightarrow 41.41\%$。
- “小模型多采样”是否更划算取决于任务、模型、真实系统吞吐与 verifier；论文既给出成本优势案例，也显示 CodeContests 在固定 FLOPs 下更偏向较大的 70B 模型。

## Key Contributions

1. **系统刻画 repeated sampling。** 在 GSM8K、MATH、MiniF2F-MATH、CodeContests、SWE-bench Lite 上覆盖 Llama 3、Gemma、Pythia、DeepSeek-Coder-V2-Instruct，并将样本预算扩展四个数量级。
2. **区分 coverage 与 precision。** Coverage 是候选集合中至少存在一个正确解的比例；precision 则是从集合中可靠识别正确解的能力。前者是 oracle 上界，只有后者足够强时才能变成实际成功率。
3. **提出经验性 scaling-law 描述。** 多数 coverage 曲线可由 exponentiated power law 拟合；同一 model family 在同一任务上的 S-curve 经 log-space 水平平移后形状近似对齐。
4. **揭示 verification bottleneck。** Majority Vote、Reward Model + Best-of-N、Reward Model + Majority Vote 在约 100 个样本附近趋于饱和，无法利用后续出现的稀有正确解。
5. **给出成本与评测可靠性的实证案例。** 论文同时分析模型大小与采样次数的 FLOPs 权衡、SWE-bench Lite 的 API 成本，以及 flaky tests、CodeContests false negatives 和一条 GSM8K 错误标注。

## Method

### Problem formulation

对每个问题独立生成 $N$ 个样本，其中 $C_i$ 个通过任务的正确性判断。论文使用无偏 pass@$k$ 估计量来降低 coverage 估计的方差：

$$
\operatorname{pass@k}
= \frac{1}{|\mathcal{D}|}
\sum_{i=1}^{|\mathcal{D}|}
\left(1-\frac{\binom{N-C_i}{k}}{\binom{N}{k}}\right).
$$

- **Coverage:** 在 $k$ 个候选里至少生成一个正确解的题目比例；在 coding 场景中等价于 pass@$k$。
- **Precision:** verifier 从候选集合中识别正确解的可靠程度。
- **Success rate:** 两者共同作用后的实际解题率。Lean proof checker、unit tests 等自动工具较可靠时，coverage 能较直接地转化为 success rate；GSM8K/MATH 则只能把 oracle coverage 当作上界。

### Repeated-sampling procedure

论文的基础设置刻意简单：所有 attempt 使用相同 prompt 与 hyperparameters，以正 temperature 相互独立地采样；随后使用 domain-specific verifier，例如 Lean4 proof checker、代码测试、majority voting 或 reward model，选出最终答案。SWE-bench Lite 的一次 attempt 指完整的多轮 agent trajectory，而不是单条 completion。

### Empirical scaling model

令 $c$ 为 coverage、$k$ 为样本数，论文先拟合

$$
\log c \approx a k^b,
$$

从而得到

$$
c \approx \exp(a k^b), \qquad a,b\in\mathbb{R}.
$$

作者从 coverage curve 上选取 40 个近似 log-space 的点并去重，再用 SciPy `curve_fit` 求 $a,b$。该模型对许多 task/model 配置拟合较好，但并非所有曲线都服从它。

### Cost model

对 dense Llama-3，论文用下式近似 token-level inference FLOPs：

$$
\operatorname{FLOPsPerToken}(L)
\approx 2\left(P+2n_{\text{layers}}dL\right),
$$

其中 $P$ 是参数量、$d$ 是 token dimension、$L$ 是 context length。作者明确提醒：FLOPs 忽略 batching、硬件利用率与共享 prompt 的 attention 优化，因此不能替代真实系统成本。

## Pipeline Figure

![[assets/pipeline_2407.21787.png]]

论文的核心流程：先通过独立采样提高“生成至少一个正确解”的机会，再依赖 verifier 解决“从候选中识别正确解”的问题。两阶段分别对应 coverage 与 precision，任一阶段不足都会限制最终收益。

## Experiments

### Evaluation setup

- **GSM8K / MATH:** 各随机抽取 128 个 test problems；temperature $0.6$、不使用 nucleus sampling、每题 10,000 个样本、最大生成长度 512 tokens。两者均使用 5-shot；MATH 固定示例，GSM8K 每题随机抽取示例。
- **MiniF2F-MATH:** 130 个由 MATH formalize 而来的 Lean4 test problems；temperature $0.5$、5-shot、每题 10,000 个样本、最大 200 tokens；使用 lean-dojo 1.1.2、Lean 4.3.0-rc2，并给每个 tactic step 10 秒超时。
- **CodeContests:** 140 个描述中不含 image tag 的 test problems；要求 Python 3；temperature $0.6$、top-$p=0.95$、每题两个随机 few-shot examples、10,000 个样本、最大 1,024 tokens；以 public、private 与 generated tests 的并集判定。
- **SWE-bench Lite:** DeepSeek-Coder-V2-Instruct 搭配 Moatless Tools（commit `a1017b78e3e69e7d205b1a3faa83a7d19fce3fa6`）和 Voyage AI embeddings；每题 250 条独立 agent trajectories。Temperature 在 50 个随机问题上从 $\{1.0,1.4,1.6,1.8\}$ 中选择，主实验使用 $1.6$。
- MiniF2F-MATH、CodeContests、SWE-bench Lite 有自动 verifier；GSM8K 与 MATH 的 coverage 使用 oracle final-answer checker 计算。

### Coverage scaling

- 五个任务的 coverage 都随样本预算平滑提升，重复采样的较弱模型最终均超过论文报告的 GPT-4o 单次尝试结果。
- CodeContests 上 Gemma-2B 从 pass@1 的 $0.02\%$ 增至 pass@10k 的 $7.1\%$，作者称提升超过 300 倍；MATH 上 Pythia-160M 从 $0.27\%$ 增至 $57\%$。
- 反例同样重要：所有 Pythia 模型在 CodeContests 上即使采样 10,000 次，coverage 仍为 0。作者推测原因是 Pythia 的 coding-specific training data 较少，但未对此做因果验证。
- 同一 family 的模型往往呈现斜率相似、水平位置不同的 S-curve；这暗示提升同一段 coverage 所需的样本预算乘数可能近似稳定，但结论只在作者测试的 family/task 内成立。

### Performance–cost trade-off

固定估算 FLOPs 时，Llama-3-8B-Instruct 在 MiniF2F-MATH、GSM8K 与 MATH 上始终比 70B 模型获得更高 coverage；CodeContests 上则几乎总是 70B 更具成本效率，说明最优的 model-size / sample-count 组合具有明显任务依赖性。

论文按当时 API 价格、固定 Moatless Tools 框架所做的 SWE-bench Lite case study 如下；这些数字是论文实验条件下的历史成本，不能直接当作当前报价：

![[assets/experiment_table_2407.21787_t1.png]]

### Verification bottleneck

作者在 GSM8K 和 MATH 的 10,000-sample collections 上比较 Majority Vote、Reward Model + Best-of-N、Reward Model + Majority Vote；reward model 为 ArmoRM-Llama3-8B-v0.1。每个 $k$ 随机抽取 100 个 subsets，报告均值与一个标准差。三种方法最初随 $k$ 改善，但约在 100 个样本附近饱和，而 oracle coverage 继续上升并超过 $95\%$。

直觉上，majority voting 偏好高频答案，后来出现的“needle in the haystack”式稀有正确解不会改变众数。Reward model 在这组实验中也没能可靠找出这些稀有正确解。因此，大样本预算首先扩大的是可解题集合，而不是自动提升 final-answer accuracy。

作者还人工检查了 105 条来自 Llama-3-8B-Instruct、最终答案正确的 GSM8K Chain-of-Thought。超过 $90\%$ 的 CoT 被判断为逻辑有效，说明正确样本的中间推理中存在可供更强 verifier 利用的信号：

![[assets/experiment_table_2407.21787_t2.png]]

### Verifier reliability checks

- **SWE-bench Lite:** 发现 34 个问题（$11.3\%$）的 test suite 存在 flakiness，其中 30 个连 dataset gold solution 都会偶发失败。作者对这些问题运行 test suite 11 次并以 majority vote 判定；去掉 34 个问题后的 266-question subset 仍呈现相同趋势。
- **CodeContests:** 在有 Python 3 reference solutions 的 122 个测试题中，35 题存在“标为正确的解却无法通过对应测试”的情况，来源包括多合法输出未被测试器接受、mutated tests 违反输入约束等 false negatives。
- **GSM8K:** 人工核验发现 test index 1042 的 ground-truth arithmetic 错误；这也是 Llama-3-70B-Instruct 在 10,000 次尝试中唯一没有生成数据集所谓“正确”答案的问题。

## Limitations & Caveats

- **Coverage 不是部署性能。** 它假设 oracle verifier；没有高 precision 的 verifier，更多生成只会让正确解更稀疏地混入大量错误解。
- **Scaling law 是经验拟合。** 样本预算最高为 10,000，且 MiniF2F-MATH 已出现明显失配；不能据此外推任意更大预算、模型或任务。
- **Sampling 策略非常基础。** 各 attempt 完全独立、使用相同 prompt/hyperparameters，没有利用 execution feedback、先前尝试或高层次 solution diversity。
- **任务覆盖偏向 pass/fail reasoning。** 结论主要来自可判定数学、formal proof、coding 与 issue-resolution；creative writing 等主观任务的 verifier 更难构造。
- **评测器自身会出错。** Flaky tests、false negatives 与错误 ground truth 会同时扭曲 coverage 和 precision；重复采样甚至可能放大“撞上测试器漏洞”的概率。
- **成本结论依赖测量口径。** FLOPs 近似忽略系统效率，API case study 又依赖论文当时的价格、agent framework 与 workload；不能直接泛化成“小模型多采样总是更便宜”。
- **人工 CoT 检查规模有限。** 105 条样本只来自 GSM8K 与 Llama-3-8B-Instruct，且表中的“faithful”实质上指人工判断的推理步骤有效性，不足以证明更一般的 process verifier 一定可行。

## Concrete Implementation Ideas

1. **可信自动 verifier 场景采用 streaming best-of-$k$。** 并行生成候选，完成一个就立刻验证；一旦通过强 verifier 即 early stop。对共享长 prompt 使用 prefix caching / batched decoding，并用真实 latency、throughput 与费用记录替代仅看 FLOPs。
2. **按任务联合搜索 model size 与 $k$。** 先在验证集测量 coverage–cost curve，再在目标预算下选择组合；不要从 MATH 的“小模型多采样”经验直接推断 CodeContests。
3. **先审计 verifier，再扩大采样。** 对 unit tests 做 gold-solution replay 与多次重跑，单独标记 flaky cases；对允许多种输出的题目检查 checker 是否做 semantic comparison，而非严格字符串匹配。
4. **无自动 verifier 时优先提升 selection。** 利用 intermediate reasoning 训练或校准 process-level verifier，并专门构造“低频正确解混在高频错误解中”的 hard-negative sets；评估指标应随 $k$ 展示，而不是只报固定 best-of-N。
5. **探索非独立 sampling。** 依据作者提出的方向，引入 prompt-level diversity、execution feedback、多轮修复，以及让新 attempt 显式参考已验证的失败尝试；同时比较每次尝试变贵与成功概率提高之间的净收益。

一个只适用于 verifier 足够可靠时的最小执行框架是：

```text
for problem in workload:
    launch k independent samples with temperature > 0
    for candidate as it finishes:
        if trusted_verifier(candidate):
            return candidate      # early stop
    return abstain_or_fallback()
```

## Open Questions / Follow-ups

- 能否在没有大规模先验采样的情况下，预测某个 task/model 的 coverage curve 与最佳 $k$？
- 如何按问题难度自适应分配 sample budget，而不是每题固定生成 10,000 次？
- Verifier 怎样在 candidate pool 增大、正确解比例下降时保持 calibration，并同时控制 false positive 与 false negative？
- Exponentiated power law 在 $k>10{,}000$、更新模型、adaptive search 或多轮 agent 上是否仍成立？
- Prefix sharing、batching、energy、wall-clock latency 与验证成本加入后，最优 model-size / sample-count frontier 如何变化？
- 对主观或开放式任务，应该训练 learned verifier，还是先把任务转换成可形式验证的表示？

## Citation

```bibtex
@article{brown2024large,
  title   = {Large Language Monkeys: Scaling Inference Compute with Repeated Sampling},
  author  = {Brown, Bradley and Juravsky, Jordan and Ehrlich, Ryan and Clark, Ronald and Le, Quoc V. and R{\'{e}}, Christopher and Mirhoseini, Azalia},
  journal = {arXiv preprint arXiv:2407.21787},
  year    = {2024}
}
```

- Paper: https://arxiv.org/abs/2407.21787
- Local PDF: [[assets/paper_2407.21787.pdf]]
- Code: https://github.com/ScalingIntelligence/large_language_monkeys
- Data: https://huggingface.co/datasets/ScalingIntelligence/monkey_business
- Project page: https://scalingintelligence.stanford.edu/pubs/large_language_monkeys/
<!-- READ_PAPER_GENERATED_END -->

<!-- USER_NOTES_START -->
<!-- USER_NOTES_END -->
