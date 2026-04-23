# Paper metadata
- Title: Video Evidence to Reasoning: Efficient Video Understanding via Explicit Evidence Grounding
- Authors: Yanxiang Huang, Guohua Gao, Zhaoyang Wei, Jianyuan Ni
- arXiv ID: 2601.07761
- Primary category: cs.CV
- Submitted: 2026-01-12
- Links:
  - Abs: https://arxiv.org/abs/2601.07761
  - PDF: https://arxiv.org/pdf/2601.07761
  - Source: https://arxiv.org/src/2601.07761
  - DOI: https://doi.org/10.48550/arXiv.2601.07761

# Executive summary
- 论文目标是解决视频推理中的核心矛盾: 更长更细的推理链会带来高 token 成本，而压缩推理又容易幻觉。
- 提出 Chain of Evidence (CoE): 把“感知证据抽取”和“语言推理”显式解耦，并联合优化。
- 核心模块包括:
  - Evidence Grounding Module (EGM): query-guided 的轻量跨注意力过滤器，从长视频特征中提取少量高价值证据。
  - Evidence-Anchoring Protocol: 先输出时间锚点，再输出必须引用锚点的 reasoning draft，最后给答案。
- 训练上结合 SFT + RL:
  - SFT 阶段用双标注数据（关键帧索引 + 推理草稿 + 答案）分别监督 grounding 与 reasoning。
  - RL 阶段用“答案正确 + 锚点准确 + 草稿引用一致性”复合奖励进一步抑制幻觉。
- 报告结果显示 CoE 在五个视频理解/幻觉相关基准上全面提升，尤其在 MVBench 和 VSI-Bench 提升明显。

# Core technical ideas
1. EGM（证据抽取）
- 输入: 视频帧特征 `V in R^{N x Dv}` 与问题特征 `Q`。
- 用浅层 cross-attention 生成 `K` 个 evidence query，对全部帧做注意力聚合，得到压缩证据 `Eg in R^{K x Dv}`。
- 作用: 把“长视频序列 N”压缩成“短证据序列 K”，降低后续 LLM 推理负担。

2. CoE 推理协议（证据约束推理）
- 输出结构强制为:
  - `<Temporal Anchors>`
  - `<Reasoning Draft>`（必须引用锚点）
  - `<Answer>`
- 与普通 CoT 的区别: 把“隐式记忆式推理”变成“可追踪、可验证的证据驱动推理”。

3. 解耦联合训练
- 总损失: `L_CoE = L_grounding + lambda * L_reasoning`。
- `L_grounding`: 由注意力矩阵池化得到帧重要度，与关键帧标签做 BCE。
- `L_reasoning`: 在 `Eg` 条件下生成锚点+草稿+答案的自回归损失。

4. 证据反馈强化学习
- 奖励函数由三部分组成:
  - 锚点匹配 F1（预测锚点 vs GT 锚点）
  - 草稿中时间引用与锚点一致性的 IoU
  - 最终答案正确性指示
- 用 GRPO 进行偏好优化，鼓励“因为证据而正确”，而不是“偶然答对”。

5. 数据构建（CoE-Instruct）
- 论文声明构建了 164k 样本数据，采用 perception/reasoning 双标注。
- 每条样本含 Question、Key_Frame_Indices、Reasoning_Draft、Answer。

# Evidence and results
1. 消融（InternVL2.5-4B，表 `reasoning_methods`）
- Original: VSI 31.8 / VideoMME 54.9 / MVBench 70.8 / VidHal 74.0 / EventHall 62.5
- Original + CoT prompting: 33.5 / 54.7 / 71.5 / 77.0 / 67.4
- SFT w/ QA only: 31.8 / 54.5 / 73.4 / 64.1 / 57.7
- SFT w/ CoT: 34.3 / 58.6 / 73.7 / 77.9 / 53.1
- RL w/ CoE (best): 37.8 / 60.7 / 76.5 / 80.2 / 72.2
- 结论: 仅 CoT 或仅 QA 都不稳定，显式证据链监督 + RL 才是最稳增益来源。

2. 与 SOTA 对比（表 `summary_results`）
- CoE-8B(RL):
  - VSI-Bench 52.1
  - Video-MME 76.3
  - MVBench 91.2
  - VidHal 81.3
  - EventHall 79.2
- 论文声称其在开源模型中达到最强，并在部分推理任务上超过闭源模型（如 Gemini-1.5-Pro 的 VSI 指标）。

3. 长视频鲁棒性（表 `mme-details`）
- InternVL3-8B 原始 + CoT: Short 75.3 / Medium 65.3 / Long 59.0 / Avg 66.6
- InternVL3-8B + CoE(SFT): Short 86.9 / Medium 71.4 / Long 68.4 / Avg 72.3
- 观察: CoE 在长视频段（Long）提升显著，说明证据锚定在长时序上更稳。

4. 额外 baseline 对比（表 `additional_baseline`）
- 与 VoT、M-LLM 对比时，CoE 在 Video-MME / NextQA 的增益幅度更大（在 InternVL2.5/3 骨干上均明显提升）。

5. 训练与评测范围
- 骨干: InternVL2.5-4B、InternVL3-8B
- 评测: Video-MME、MVBench、VSI-Bench、VidHal、EventHall
- 微调: 4B 全参数微调；8B 使用 LoRA

# Limitations and caveats
- 论文强调效率收益，但主表未统一给出端到端 latency、吞吐、token 消耗的完整统计分解。
- CoE-Instruct 为关键资产（164k），但公开性、标注质量控制与可复现实操细节需要进一步核验。
- 评测集中在 InternVL 系列，跨架构泛化（Qwen2-VL/LLaVA-NeXT-Video）尚未系统展示。
- 证据锚点质量依赖关键帧监督，若标注噪声高，可能误导 reasoning draft。
- 文中有部分数字版本与早期注释表存在差异（同一方法在不同表述区块出现过不同数值），复现时应以最终表格为准。

# Relevance to Video Understanding
- 与视频理解项目高度相关，尤其适合“长视频 + 多步推理 + 可解释性”场景。
- CoE 的价值不只在精度，还在于可审计: 每个结论可回溯到时间锚点，便于错误分析和人类校验。
- 对当前主流 VideoLLM 实践很实用: 可以不改主干架构，先在视觉-语言接口加一个轻量 EGM，再改推理输出协议。

# Concrete experiments or implementation ideas for Video Understanding
1. 在 InternVL/LLaVA-NeXT-Video 上复现轻量版 EGM
- 固定主干，仅在视觉 token 到 LLM 之间插入 1-2 层 cross-attention 过滤器。
- 对比 `K`（证据槽位数）与精度/时延曲线，验证是否存在最优压缩点。

2. 先做“协议级”最小可行实验（无新模块）
- 仅改推理模板为 `anchors -> draft -> answer`，并加 post-check（draft 必须引用 anchors）。
- 评估是否在无参数改动下也能减少 hallucination。

3. 构建小规模 CoE-style 数据
- 从已有视频 QA 数据自动生成 pseudo keyframe labels（ASR 对齐 + 检索 + 人审小样本）。
- 做 `SFT with CoT` vs `SFT with CoE` 对照，验证“显式锚定监督”的净收益。

4. RL 奖励替换实验
- 把 IoU(草稿时间引用, 预测锚点) 换成更严格的 span-F1 或 temporal edit distance。
- 比较不同过程奖励对“答对但不可信”样本的抑制效果。

5. 长视频专项评测
- 按时长分桶（short/medium/long）复刻 Video-MME 风格评测。
- 增加“证据覆盖率”和“锚点-答案一致性”两个可解释指标。

# Risks, unknowns, and follow-up reading
- 风险
  - 若证据锚点抽取失败，推理会被错误证据系统性牵引。
  - RL 奖励权重不当可能导致“过度对齐格式”而非真正语义理解。
- 未知点
  - CoE-Instruct 是否完全可获得；若不可得，复现实验可能显著缩水。
  - 在弱监督/无关键帧标注场景下，EGM 是否仍稳定。
- 后续阅读建议
  - VideoCoT (video chain-of-thought data generation)
  - VideoEspresso / key-frame selection line
  - VidHal / EventHall（视频幻觉评估）
  - GRPO / DPO 系列偏好优化方法

- BibTeX:
```bibtex
@misc{huang2026videoevidencereasoningefficient,
      title={Video Evidence to Reasoning Efficient Video Understanding via Explicit Evidence Grounding},
      author={Yanxiang Huang and Guohua Gao and Zhaoyang Wei and Jianyuan Ni},
      year={2026},
      eprint={2601.07761},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2601.07761},
}
```
