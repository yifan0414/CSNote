---
创建时间: 2026-05-08T11:13:00
tags:
---

## 0. 总览
> [!note] Video Multiple-Choice QA (VMCQA) 即 VQA 的一种，也是视频理解的主要评测数据集，另一种是 Video open-ended QA

选项偏置相关工作大致可以分成四条线：

1. **诊断线**：证明模型在多选题中会偏向某些选项位置、选项符号或选项顺序，而不完全依据题目内容。
2. **推理时去偏线**：不训练模型，通过 prior calibration、logit correction、permutation / voting、post-processing 等方式减少偏置。
3. **训练去偏线**：通过 SFT、蒸馏、LoRA、symbol binding 增强等方式，让模型内部学会更稳定地绑定选项内容和选项符号。
4. **benchmark / 数据线**：构造更干净的 MCQA / VQA / VideoQA benchmark，过滤 text shortcut、easy option bias、vision-answer / question-answer spurious correlation 等。

整体上，**文字 LLM MCQA 领域最早、最系统；LVLM / VideoQA 领域正在快速跟进；视频理解里目前更偏 benchmark 清洗、bias 诊断和后处理校准。**


## 1. 基本概念区分

### 1.1 Selection bias

**Selection bias** 是一个总称，指模型在选择题中不是纯粹根据选项内容做决定，而受到一些无关因素影响，例如：

- 喜欢选某个选项 ID：A、B、C、D、E；
- 喜欢选某个位置：第一个、最后一个、中间；
- 对选项顺序敏感；
- 对 option token 的概率先验不均衡；
- 只看选项文本或视觉相似性就能猜答案。

代表论文：  
- [Large Language Models Are Not Robust Multiple Choice Selectors / PriDe (ICLR 2024)](https://openreview.net/forum?id=shr9PXz7T0)  
- [Unveiling Selection Biases: Exploring Order and Token Sensitivity in Large Language Models (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.333/)

### 1.2 Option-position bias / positional bias

指模型偏好某个**位置**，例如第一项、最后一项、C 位、D 位。  
它不一定等同于 A/B/C/D token bias，因为有些 prompt 可能不用字母，而是用编号或自然语言列表。

代表论文：  
- [Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions (Findings of NAACL 2024)](https://aclanthology.org/2024.findings-naacl.130/)  
- [Addressing Blind Guessing: Calibration of Selection Bias in Multiple-Choice Question Answering by Video Language Models / BOLD (ACL 2025)](https://aclanthology.org/2025.acl-long.162/)

### 1.3 Option-token bias / option-ID bias

指模型对 **A/B/C/D/E 这些符号本身** 有先验偏好。  
例如在没有足够语义证据时，模型可能更容易生成 “C” 或 “D”。

代表论文：  
- [Large Language Models Are Not Robust Multiple Choice Selectors (ICLR 2024)](https://arxiv.org/abs/2309.03882)  
- [Benchmarking and Mitigating MCQA Selection Bias of Large Vision-Language Models (EMNLP 2025)](https://arxiv.org/abs/2509.16805)

### 1.4 Option-order sensitivity / permutation sensitivity

指同一道题仅仅改变选项顺序，模型输出和准确率就明显变化。  
这说明模型没有保持选择题天然需要的 permutation invariance。

代表论文：  
- [Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions (Findings of NAACL 2024)](https://aclanthology.org/2024.findings-naacl.130/)  
- [Teacher-Student Training for Debiasing: General Permutation Debiasing for Large Language Models (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.81/)

### 1.5 Multiple-choice symbol binding

指模型能否稳定理解：

> “选项符号 A/B/C/D” 和 “对应的选项内容” 之间的绑定关系。

如果 symbol binding 能力弱，模型可能看似在回答 A/B/C/D，实际上并没有正确绑定当前题目里的选项内容。

代表论文： 
- [Strengthened Symbol Binding Makes Large Language Models Reliable Multiple-Choice Selectors (ACL 2024)](https://aclanthology.org/2024.acl-long.237/)

### 1.6 Easy option bias / option-content shortcut

这不是位置偏置，而是**选项内容本身太容易**。  
例如 VLM 只看视频和选项，不看问题，也能选出正确答案，因为正确选项和视觉内容更相似，错误选项太弱。

代表论文：  
- [Mitigating Easy Option Bias in Multiple-Choice Question Answering (arXiv 2025)](https://arxiv.org/abs/2508.13428)

### 1.7 Vision-answer / question-answer bias

这是 VideoQA / VQA benchmark 中更传统的 spurious correlation 问题。  
例如模型只看答案和视觉内容，或只看问题和答案，就可以利用数据集统计偏差猜答案。

代表论文：  
- [NExT-OOD: Overcoming Dual Multiple-choice VQA Biases (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD)


## 2. 按任务目的分类

### 2.1 目的一：诊断模型是否真的鲁棒选择

这类工作主要问：

> 模型在选择题上到底是在理解题目，还是在利用选项位置、选项符号、选项顺序等 shortcut？

典型做法包括：

- 对同一道题做选项重排；
- 比较不同 option ID 下的预测分布；
- 去掉题目中的部分信息，看模型是否仍然有固定选择倾向；
- 统计预测分布与真实答案分布的偏差；
- 分析模型在不确定样本上的 top-2 / top-3 选项变化。

代表论文：

| 论文 | 场景 | 主要诊断对象 | 核心发现 |
|---|---|---|---|
| [Large Language Models Are Not Robust Multiple Choice Selectors (ICLR 2024)](https://openreview.net/forum?id=shr9PXz7T0) | Text-only LLM MCQA | option ID / token bias | LLM 会偏好特定 option ID；token bias 是重要来源 |
| [Sensitivity to The Order of Options (Findings of NAACL 2024)](https://aclanthology.org/2024.findings-naacl.130/) | Text-only LLM MCQA | option order sensitivity | 改变选项顺序会造成大幅性能波动 |
| [Unveiling Selection Biases (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.333/) | LLM selection tasks | order bias + token bias | 选项顺序和 token 使用都会影响决策 |
| [BOLD (ACL 2025)](https://aclanthology.org/2025.acl-long.162/) | Video MCQA | answer position bias / blind guessing | Video VLM 在 MCQA 中也会偏好某些答案位置 |
| [Benchmarking MCQA Selection Bias of LVLMs (EMNLP 2025)](https://arxiv.org/abs/2509.16805) | LVLM / image MCQA | option token / position bias | 视觉选择题难度越高，selection bias 越明显 |
| [NExT-OOD (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD) | VideoQA benchmark | VA bias / QA bias | 多选 VideoQA 模型可能依赖数据集 spurious correlation |

这一类工作通常不以训练新模型为主，而是为了说明现有评测不够可靠。

### 2.2 目的二：推理时校正模型偏置

这类工作主要问：

> 在不改模型参数的情况下，能不能让模型少受选项偏置影响？

典型方法包括：

- 估计模型对 A/B/C/D 的 prior，然后从预测中扣除；
- 构造 ill-defined task 暴露盲猜偏置；
- 对 logits 进行 bias correction；
- 对多个 permutation 的输出投票；
- 用 self-consistency marginalize 掉输入顺序影响；
- 用缓存或批处理降低多次推理成本。

代表论文：

| 论文 | 是否训练 | 是否需要 logits / probability | 方法概括 |
|---|---:|---:|---|
| [PriDe (ICLR 2024)](https://arxiv.org/abs/2309.03882) | 否 | 较依赖概率分布 | label-free inference-time prior debiasing |
| [BOLD (ACL 2025)](https://arxiv.org/abs/2410.14248) | 否 | 更适合能拿到分布或可做后处理的设置 | 通过 decomposition 估计 blind guessing bias，再做 post-processing calibration |
| [Benchmarking and Mitigating MCQA Selection Bias of LVLMs (EMNLP 2025)](https://arxiv.org/abs/2509.16805) | 否 | 是，logit-level | 估计 bias vector，对 MCQ option logits 做 confidence-adaptive correction |
| [Permutation Self-Consistency (NAACL 2024)](https://aclanthology.org/2024.naacl-long.129/) | 否 | 不一定 | 多次重排列表并聚合输出，减少顺序偏置 |
| [Quantifying and Mitigating Selection Bias in LLMs (Findings of IJCNLP-AACL 2025)](https://aclanthology.org/2025.findings-ijcnlp.127/) | 混合 | 视具体模块而定 | 提出 PBM 指标、efficient majority voting、以及 LoRA 去偏 |

这类方法的优势是 deployment 友好，尤其适合 frozen model、API model 或 black-box 模型。缺点是可能增加推理成本，或者需要校准样本、logits、概率分布。


### 2.3 目的三：训练或微调模型，使其内部更鲁棒

这类工作主要问：

> 能不能通过训练让模型本身减少 selection bias，而不是每次推理时做额外校正？

典型做法包括：

- 在 SFT 中增强 option symbol 和 option content 的绑定；
- 构造负样本，迫使模型学会当前题目的符号-内容对应关系；
- 用 permutation-debiased teacher 蒸馏 student；
- 用 LoRA 或轻量微调降低 permutation inconsistency；
- 训练 permutation-equivariant network 学会处理或利用位置偏置。

代表论文：

| 论文 | 训练类型 | 主要思想 |
|---|---|---|
| [Strengthened Symbol Binding / PIF (ACL 2024)](https://aclanthology.org/2024.acl-long.237/) | SFT | 通过负样本和 point-wise loss 增强 MC symbol binding |
| [General Permutation Debiasing (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.81/) | teacher-student distillation | 把高成本 permutation-debiased teacher 的能力蒸馏到 student |
| [Quantifying and Mitigating Selection Bias in LLMs (Findings of IJCNLP-AACL 2025)](https://arxiv.org/abs/2511.21709) | LoRA | 用 label-free metric 与 LoRA-1 fine-tuning 减少 selection bias |
| [EMBER / Embracing Positional Bias (AAAI 2026)](https://ojs.aaai.org/index.php/AAAI/article/view/40401) | permutation-equivariant network | 不完全消除偏置，而是学习有利 permutation 并利用 bias |

这类方法的优点是推理时更高效，缺点是需要训练资源、训练数据或额外模型组件；如果研究目标是 training-free / zero-shot，就不能直接归入这类。


### 2.4 目的四：构造更可靠的 benchmark 或清洗数据

这类工作主要问：

> 现有 benchmark 的准确率是否被 shortcut、选项偏置、答案统计偏差虚高了？

典型做法包括：

- 使用选项排列过滤 text shortcut；
- 构造 OOD split 分离不同 spurious correlation；
- 自动生成更强的 hard negative options；
- 降低随机猜测概率；
- 控制选项长度、语义相似度和视觉相关性。

代表论文：

| 论文 | 场景 | Benchmark / 数据贡献 |
|---|---|---|
| [AVUT (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.333/) | audio-centric video understanding | 使用 cyclic answer permutations 过滤 shortcut，构造更可靠音频中心视频理解 benchmark |
| [Easy Option Bias / GroundAttack (arXiv 2025)](https://arxiv.org/abs/2508.13428) | VQA / VideoQA | 发现 V+O 即可猜答案的问题，自动生成 visually plausible hard negatives |
| [NExT-OOD (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD) | VideoQA | 构造 NExT-OOD-VA、NExT-OOD-QA、NExT-OOD-VQA 评估 OOD 泛化 |
| [BOLD (ACL 2025)](https://aclanthology.org/2025.acl-long.162/) | Video MCQA | 虽主要是校准方法，但也从评测角度揭示现有 Video MCQA 的 blind guessing 问题 |
贡献常常是评测协议、数据清洗方法、benchmark 设计或偏置度量。


## 3. 按任务场景分类

### 3.1 Text-only LLM MCQA

这是 selection bias 研究最成熟的场景。  
常见 benchmark 包括 MMLU、commonsense reasoning、knowledge QA、reading comprehension 等。

核心问题：

- 选项顺序变了，模型答案会不会变？
- 模型是否偏好 A/B/C/D？
- few-shot 示例顺序是否放大偏置？
- 模型不确定时是否更依赖位置先验？
- 选项 ID token 的概率是否天然不均衡？

代表论文：

1. [Large Language Models Are Not Robust Multiple Choice Selectors (ICLR 2024)](https://openreview.net/forum?id=shr9PXz7T0)  
   - 重点：option ID selection bias；PriDe inference-time debiasing。
   - 类型：诊断 + 免训练推理时去偏。

2. [Large Language Models Sensitivity to The Order of Options (Findings of NAACL 2024)](https://aclanthology.org/2024.findings-naacl.130/)  
   - 重点：选项顺序敏感性。
   - 类型：诊断 + 校准思路。

3. [Unveiling Selection Biases (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.333/)  
   - 重点：order bias 与 token bias。
   - 类型：诊断 + mitigation。

4. [Strengthened Symbol Binding / PIF (ACL 2024)](https://aclanthology.org/2024.acl-long.237/)  
   - 重点：symbol binding。
   - 类型：训练 / SFT。

5. [General Permutation Debiasing (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.81/)  
   - 重点：把 permutation-invariant teacher 的能力蒸馏到 student。
   - 类型：训练 / 蒸馏。


### 3.2 LVLM / image-based VQA / MCQA

这个场景关注视觉语言模型在 image MCQA 中的选择偏置。  
相比 text-only，额外问题是：

- 当视觉证据不充分时，模型是否退化成文本选择偏置？
- 选项之间视觉相似度高时，偏置是否增强？
- 是否可以通过 logit correction 改善 frozen LVLM？
- benchmark 中正确选项是否比错误选项视觉上更容易匹配图像？

代表论文：

1. [Benchmarking and Mitigating MCQA Selection Bias of Large Vision-Language Models (EMNLP 2025)](https://arxiv.org/abs/2509.16805)  
   - 场景：LVLM fine-grained MCQA。
   - 方法：构造不同难度的 MCQA benchmark；提出 inference-time logit correction。
   - 类型：benchmark / 诊断 + 免训练 logit 校正。

2. [Mitigating Easy Option Bias in Multiple-Choice Question Answering (arXiv 2025)](https://arxiv.org/abs/2508.13428)  
   - 场景：VQA / VideoQA benchmark。
   - 方法：发现 V+O shortcut；用 GroundAttack 生成 hard negative options。
   - 类型：benchmark 修正 / 数据构造。


### 3.3 VideoQA / Video MCQA

这是和视频理解最直接相关的场景。  
视频 MCQA 中 selection bias 更复杂，因为模型可能同时受到：

- 选项位置偏置；
- 视觉证据不足；
- 视频帧采样或压缩导致的信息缺失；
- 文本选项 shortcut；
- 问题-答案统计相关；
- 视频-答案统计相关。

代表论文：

1. [Addressing Blind Guessing / BOLD (ACL 2025)](https://aclanthology.org/2025.acl-long.162/)  
   - 场景：Video Language Models 的 MCQA。
   - 方法：把 MCQA 分解成 video / question / answer content 的 ill-defined variants，估计 blind guessing bias，并做 post-processing calibration。
   - 类型：VideoQA 诊断 + 免训练后处理校准。

2. [NExT-OOD (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD)  
   - 场景：VideoQA OOD benchmark。
   - 方法：构造 VA bias、QA bias、VA&QA bias 的 OOD 数据集。
   - 类型：benchmark / OOD 评测。

3. [Easy Option Bias / GroundAttack (arXiv 2025)](https://arxiv.org/abs/2508.13428)  
   - 场景：VQA / VideoQA MCQ。
   - 方法：发现只用 V+O 就能猜中的 easy-option shortcut。
   - 类型：benchmark 修正 / hard negative construction。

4. [AVUT (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.333/)  
   - 场景：audio-centric video understanding。
   - 方法：使用 cyclic answer permutations 过滤 text shortcut。
   - 类型：benchmark 构造 / 数据清洗。

视频理解领域目前的特点是：

- **诊断和 benchmark 工作多于训练去偏工作**；
- **post-processing / calibration 比训练新模型更常见**；
- **选项排列常被用作 shortcut 检测或评测鲁棒性工具**；
- **如何在 video compression / frame selection setting 下系统分析 option bias 仍有空间**。


### 3.4 Listwise ranking / 排序任务

虽然不是 MCQA，但和 option-position bias 思想相通。  
排序任务中，LLM 也会受到候选列表顺序影响。

代表论文：

- [Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in Large Language Models (NAACL 2024)](https://aclanthology.org/2024.naacl-long.129/)

核心思想：

- 多次打乱候选列表；
- 让 LLM 输出多个排序；
- 聚合得到更接近 order-independent 的 ranking；
- 本质是对 input order 做 marginalization。

它适合作为 permutation-based debiasing 的相关思想，而不是 VideoQA 直接 baseline。

## 4. 按方法类型分类

### 4.1 Permutation / shuffling / voting 类

核心思想：

> 如果模型受到选项顺序影响，就通过多个不同顺序的输入来平均掉或暴露这种影响。

常见形式：

- random shuffle；
- full permutation；
- cyclic permutation；
- permutation self-consistency；
- majority voting；
- central ranking aggregation；
- permutation bias metric。

代表论文：

- [Sensitivity to The Order of Options (Findings of NAACL 2024)](https://aclanthology.org/2024.findings-naacl.130/)
- [General Permutation Debiasing (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.81/)
- [Permutation Self-Consistency (NAACL 2024)](https://aclanthology.org/2024.naacl-long.129/)
- [Quantifying and Mitigating Selection Bias in LLMs (Findings of IJCNLP-AACL 2025)](https://aclanthology.org/2025.findings-ijcnlp.127/)
- [AVUT (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.333/)

优点：

- 概念简单；
- 黑盒友好；
- 不需要训练；
- 对 order bias 很直接。

缺点：

- 多次推理成本高；
- aggregation 策略会影响结果；
- 如果选项内容本身有 shortcut，重排不能完全解决；
- 如果模型始终错误理解视频/问题，排列平均也不能解决。


### 4.2 Prior estimation / calibration 类

核心思想：

> 先估计模型在“没有有效信息”或“只看选项符号”时的选择先验，再对正常预测做校正。

代表方法：

- PriDe：估计 option ID prior，分离 prior bias 和 prediction distribution。
- BOLD：通过 decomposed MCQA 任务估计 blind guessing bias。
- 一些 calibration 方法：基于 validation set 或 unlabeled test subset 估计偏置向量。

代表论文：

- [PriDe (ICLR 2024)](https://arxiv.org/abs/2309.03882)
- [BOLD (ACL 2025)](https://arxiv.org/abs/2410.14248)
- [Quantifying and Mitigating Selection Bias in LLMs (Findings of IJCNLP-AACL 2025)](https://arxiv.org/abs/2511.21709)

优点：

- 推理成本可能低于多排列；
- 可以解释为校正模型先验；
- 对系统性 option ID bias 有针对性。

缺点：

- 往往需要概率分布、logits 或校准样本；
- global prior 未必适合每个样本；
- 如果偏置是上下文相关的，简单全局校准可能不足。


### 4.3 Logit-level correction 类

核心思想：

> 直接在模型输出 logits 层面对 A/B/C/D/E 等选项 token 进行校正。

代表论文：

- [Benchmarking and Mitigating MCQA Selection Bias of Large Vision-Language Models (EMNLP 2025)](https://arxiv.org/abs/2509.16805)

方法特点：

- 估计 bias vector；
- 对模型输出分布做 confidence-adaptive correction；
- 不需要重训模型；
- 适合 white-box 或能访问 logits 的 LVLM。

优点：

- 比多次 permutation 更省推理；
- 对 option-token bias 很直接；
- frozen model 也可用。

缺点：

- 黑盒 API 不一定能用；
- 需要能可靠拿到 option logits；
- 对生成式长回答格式的模型不一定稳定。

### 4.4 Decomposition / ablation 类

核心思想：

> 把完整 MCQA 输入拆掉一部分，观察模型是否仍然有偏向，从而暴露 shortcut 或 blind guessing。

典型拆法：

- 去掉 video；
- 去掉 question；
- 去掉 answer content；
- 只保留 video + options；
- 只保留 question + options；
- 只保留 option IDs。

代表论文：

- [BOLD (ACL 2025)](https://aclanthology.org/2025.acl-long.162/)
- [Easy Option Bias / GroundAttack (arXiv 2025)](https://arxiv.org/abs/2508.13428)
- [NExT-OOD (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD)

优点：

- 诊断性强；
- 能区分不同 shortcut 来源；
- 特别适合 benchmark analysis。

缺点：

- 不一定直接给出最优推理方法；
- 构造异常输入可能改变模型行为；
- 需要谨慎解释“去掉某部分后”的实验结论。

### 4.5 Symbol binding / 训练增强类

核心思想：

> 模型偏置不是简单的输出先验问题，而是模型没有学好“当前题目中 A 对应哪个答案内容”。

代表论文：

- [Strengthened Symbol Binding Makes Large Language Models Reliable Multiple-Choice Selectors (ACL 2024)](https://aclanthology.org/2024.acl-long.237/)

方法特点：

- 在 SFT 阶段显式增强 option symbol 和 content 的绑定；
- 构造 negative instances；
- 使用 point-wise loss；
- 改善 MCQ accuracy 和 selection bias。

优点：

- 从模型能力层面解决问题；
- 推理时不需要多次排列或校准；
- 对 MCQA 专用模型可能有效。

缺点：

- 需要训练；
- 需要可控训练数据；
- 对 closed-source model / black-box VLM 不适用。

### 4.6 Teacher-student / distillation 类

核心思想：

> 高成本 debiased teacher 可以通过多排列或校正得到更鲁棒结果，然后把这个能力蒸馏给轻量 student。

代表论文：

- [General Permutation Debiasing (Findings of ACL 2024)](https://aclanthology.org/2024.findings-acl.81/)

优点：

- 试图解决 permutation debiasing 推理成本高的问题；
- student 推理成本低；
- 思想上可以推广到多个任务。

缺点：

- 需要训练 student；
- 对纯 black-box deployment 不直接适用；
- distillation 能否迁移到多模态 VideoQA 需要额外验证。

### 4.7 Benchmark cleaning / hard negative construction 类

核心思想：

> 与其只修模型，不如修 benchmark，减少 shortcut 题目和弱负选项。

代表论文：

- [AVUT (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.333/)
- [Easy Option Bias / GroundAttack (arXiv 2025)](https://arxiv.org/abs/2508.13428)
- [NExT-OOD (TPAMI 2023)](https://github.com/zhangxi1997/NExT-OOD)

优点：

- 能提高评测可信度；
- 能暴露模型是否真的理解视频；
- 对整个社区有长期价值。

缺点：

- 不一定提升现有模型；
- 数据构造成本高；
- benchmark 修正和推理方法是不同贡献类型。

## 5. 按“是否训练 / 是否 benchmark”分类总表

| 工作                                        | 场景                        |                                   主要贡献 |      免训练推理时方法 | 训练方法 | Benchmark / 数据 |
| ----------------------------------------- | ------------------------- | -------------------------------------: | ------------: | ---: | -------------: |
| PriDe / LLMs Are Not Robust MC Selectors (ICLR 2024) | Text MCQA                 |                   诊断 + prior debiasing |             ✅ |    ❌ |              ❌ |
| Sensitivity to Option Order (Findings of NAACL 2024) | Text MCQA                 |                                诊断顺序敏感性 |          部分校准 |    ❌ |              ❌ |
| Unveiling Selection Biases (Findings of ACL 2024) | LLM selection tasks       |                    诊断 order/token bias | 部分 mitigation |  ❌/弱 |              ❌ |
| General Permutation Debiasing (Findings of ACL 2024) | LLM general tasks         |              teacher-student debiasing |             ❌ |    ✅ |              ❌ |
| PIF / Strengthened Symbol Binding (ACL 2024) | Text MCQA                 |                     symbol binding SFT |             ❌ |    ✅ |              ❌ |
| BOLD (ACL 2025) | Video MCQA                |             blind guessing calibration |             ✅ |    ❌ |          诊断属性强 |
| LVLM Selection Bias Logit Correction (EMNLP 2025) | Image MCQA / LVLM         |                  logit-level debiasing |             ✅ |    ❌ |           ✅/诊断 |
| Quantifying and Mitigating Selection Bias (Findings of IJCNLP-AACL 2025) | Text MCQA                 |                    PBM + voting + LoRA |             ✅ |    ✅ |              ❌ |
| Permutation Self-Consistency (NAACL 2024) | Listwise ranking          |                  order marginalization |             ✅ |    ❌ |              ❌ |
| AVUT (EMNLP 2025) | Audio-video understanding |            shortcut-filtered benchmark |      ❌/作为过滤流程 |    ❌ |              ✅ |
| Easy Option Bias / GroundAttack (arXiv 2025) | VQA / VideoQA             |             hard negative construction |             ❌ |    ❌ |              ✅ |
| NExT-OOD (TPAMI 2023) | VideoQA                   |           OOD benchmark for VA/QA bias |             ❌ |    ❌ |              ✅ |
| EMBER (AAAI 2026) | Text MCQA                 | 利用 positional bias 的 equivariant model |             ❌ |    ✅ |              ❌ |


## 6. 代表论文简要卡片

### 6.1 Large Language Models Are Not Robust Multiple Choice Selectors / PriDe (ICLR 2024)

- **场景**：Text-only LLM MCQA。
- **问题**：LLM 在 MCQ 中会偏好某些 option IDs。
- **偏置类型**：selection bias、option-ID bias、token bias。
- **方法**：PriDe，label-free inference-time debiasing；通过小部分样本估计 option ID prior，再对剩余样本校正。
- **是否训练**：否。
- **是否 benchmark**：不是 benchmark，主要是诊断 + 方法。
- **价值**：selection bias 方向最核心的基础论文之一。

链接： https://openreview.net/forum?id=shr9PXz7T0
### 6.2 Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions (Findings of NAACL 2024)

- **场景**：Text-only LLM MCQA。
- **问题**：只改变选项顺序，模型准确率和预测会显著变化。
- **偏置类型**：option-order sensitivity、positional bias。
- **方法**：系统重排选项并分析性能波动；进一步讨论 top-2/top-3 不确定性与位置影响。
- **是否训练**：否。
- **是否 benchmark**：不是新 benchmark，偏 evaluation analysis。
- **价值**：非常适合放在 related work 的“选项顺序敏感性”段落。

链接： https://aclanthology.org/2024.findings-naacl.130/
### 6.3 Unveiling Selection Biases: Exploring Order and Token Sensitivity in Large Language Models (Findings of ACL 2024)

- **场景**：LLM selection tasks。
- **问题**：LLM 在从有序候选中选择时，会受到候选顺序和 token 表示影响。
- **偏置类型**：order bias、token bias。
- **方法**：跨多个模型和任务量化 order/token sensitivity，并提出缓解策略。
- **是否训练**：主要不是训练。
- **是否 benchmark**：偏诊断分析。
- **价值**：帮助把 selection bias 拆成 order 和 token 两个维度。

链接： https://aclanthology.org/2024.findings-acl.333/
### 6.4 Teacher-Student Training for Debiasing: General Permutation Debiasing for LLMs (Findings of ACL 2024)

- **场景**：LLM 中一般 permutation sensitivity 问题。
- **问题**：多排列 debiasing 有效但推理成本高。
- **偏置类型**：permutation sensitivity。
- **方法**：先用高成本 debiased teacher，再蒸馏 compact student。
- **是否训练**：是。
- **是否 benchmark**：不是 benchmark。
- **价值**：代表“训练/蒸馏去偏”路线。

链接： https://aclanthology.org/2024.findings-acl.81/

### 6.5 Strengthened Symbol Binding Makes LLMs Reliable Multiple-Choice Selectors / PIF (ACL 2024)

- **场景**：Text MCQA 的 SFT。
- **问题**：LLM 在 SFT 中仍可能有 selection bias，因为 Multiple Choice Symbol Binding 能力不足。
- **偏置类型**：symbol binding failure、selection bias。
- **方法**：PIF，通过负样本和 point-wise loss 加强选项符号与选项内容绑定。
- **是否训练**：是，SFT。
- **是否 benchmark**：不是 benchmark。
- **价值**：从“模型内部能力”角度解释 selection bias。

链接： https://aclanthology.org/2024.acl-long.237/

### 6.6 Addressing Blind Guessing / BOLD (ACL 2025)
> [!note] cyclic option 通常是把同一道题的选项做循环移位/重排，用来检查或过滤“答案是否随位置变化”的 shortcut。BOLD 是构造缺失 video、question 或 answer content 的 ill-defined variants 来估计模型在信息不足时的盲猜分布，并把这个估计用于后处理校准；因此它更像一种 bias decomposition + calibration 方法，而不是单纯的 cyclic permutation/voting 策略。

- **场景**：Video Language Models 的 MCQA。
- **问题**：Video MCQA accuracy 可能被模型的 answer-position blind guessing 污染。
- **偏置类型**：selection bias、answer position bias、blind guessing。
- **方法**：把 MCQA 拆成 video/question/answer content 的 ill-defined variants，估计 bias，再做 post-processing calibration。
- **是否训练**：否。
- **是否 benchmark**：不是新 benchmark，但 benchmark 诊断属性很强。
- **价值**：目前 Video MCQA selection bias 最直接相关的工作之一。
- **与 cyclic option 的区别**：

链接： https://aclanthology.org/2025.acl-long.162/

### 6.7 Benchmarking and Mitigating MCQA Selection Bias of Large Vision-Language Models (EMNLP 2025)

- **场景**：LVLM / image MCQA。
- **问题**：LVLM 在 MCQA 中存在 option token / position bias，且难题中更明显。
- **偏置类型**：option token bias、position bias。
- **方法**：构造 fine-grained MCQA benchmark；提出 inference-time logit correction。
- **是否训练**：否。
- **是否 benchmark**：有 benchmark / evaluation 属性。
- **价值**：把 selection bias 从 text LLM 推到 LVLM。

链接： https://arxiv.org/abs/2509.16805

### 6.8 Quantifying and Mitigating Selection Bias in LLMs (Findings of IJCNLP-AACL 2025)

- **场景**：Text MCQA。
- **问题**：已有指标依赖标签，majority voting 成本高，calibration 泛化差。
- **偏置类型**：permutation inconsistency、selection bias。
- **方法**：提出 label-free PBM；提出 efficient majority voting；提出 LoRA-1 fine-tuning。
- **是否训练**：混合，既有免训练 voting，也有 LoRA。
- **是否 benchmark**：不是 benchmark。
- **价值**：适合引用其对 majority voting / calibration 局限性的总结。

链接： https://aclanthology.org/2025.findings-ijcnlp.127/

### 6.9 Permutation Self-Consistency Improves Listwise Ranking (NAACL 2024)

- **场景**：LLM listwise ranking。
- **问题**：LLM 排序会受候选列表位置影响。
- **偏置类型**：positional bias。
- **方法**：多次 shuffle 输入列表，再聚合排名，marginalize order bias。
- **是否训练**：否。
- **是否 benchmark**：不是 benchmark。
- **价值**：不是 MCQA，但和 permutation-based debiasing 思想接近。

链接： https://aclanthology.org/2024.naacl-long.129/

### 6.10 AVUT: Audio-centric Video Understanding Benchmark without Shortcuts (EMNLP 2025)

- **场景**：音频中心的视频理解 benchmark。
- **问题**：视频理解 benchmark 可能存在 text shortcut，导致模型不用真实理解视频也能答题。
- **偏置类型**：text shortcut、positional bias 风险。
- **方法**：对每个 MCQ 构造 cyclic answer permutations，用于过滤 shortcut。
- **是否训练**：否。
- **是否 benchmark**：是。
- **价值**：视频理解领域中“cyclic permutation 用于数据过滤/shortcut 检测”的代表。

链接： https://aclanthology.org/2025.emnlp-main.333/



### 6.11 Mitigating Easy Option Bias / GroundAttack (arXiv 2025)

- **场景**：VQA / VideoQA MCQ。
- **问题**：正确选项和视觉内容太容易匹配，模型只看 Video+Option、不看 Question 也能猜对。
- **偏置类型**：easy option bias、option-content shortcut。
- **方法**：GroundAttack 自动生成更视觉可行的 hard negative options。
- **是否训练**：否。
- **是否 benchmark**：是，修正 benchmark / 数据。
- **价值**：说明 MCQA 偏置不仅来自位置，也来自选项内容本身。

链接： https://arxiv.org/abs/2508.13428

### 6.12 NExT-OOD (TPAMI 2023)

- **场景**：VideoQA。
- **问题**：多选 VideoQA 存在 vision-answer bias 和 question-answer bias。
- **偏置类型**：VA bias、QA bias、VA&QA bias。
- **方法**：构造 NExT-OOD-VA、NExT-OOD-QA、NExT-OOD-VQA。
- **是否训练**：否。
- **是否 benchmark**：是。
- **价值**：VideoQA benchmark bias / OOD generalization 的重要参考。

链接： https://github.com/zhangxi1997/NExT-OOD

### 6.13 EMBER: Embracing Positional Bias in MCQA via Permutation Equivariant Neural Networks (AAAI 2026)

- **场景**：Text MCQA。
- **问题**：已有方法多把 positional bias 当作必须消除的问题，但某些排列反而可能提升表现。
- **偏置类型**：positional bias。
- **方法**：训练 permutation-equivariant network，学习有利的选项排列。
- **是否训练**：是。
- **是否 benchmark**：不是 benchmark。
- **价值**：提供一种不同视角：不是单纯消除偏置，而是建模并利用偏置。

链接： https://ojs.aaai.org/index.php/AAAI/article/view/40401
## 7. 研究趋势总结

### 7.1 从 text-only LLM 扩展到 LVLM / VideoQA

早期 selection bias 主要在 text-only MCQA 中研究。  
最近开始进入：

- LVLM image MCQA；
- Video Language Model MCQA；
- audio-video understanding benchmark；
- VQA / VideoQA benchmark cleaning。

这说明多模态评测中的 MCQ accuracy 正在被重新审视。

### 7.2 从“证明有偏置”转向“区分偏置来源”

现在不只是问“有没有偏置”，而是进一步区分：

- 是 option ID token bias？
- 是位置 bias？
- 是顺序 bias？
- 是 symbol binding 失败？
- 是视觉证据不足后的 blind guessing？
- 是正确选项本身太容易？
- 是 benchmark 的 QA / VA spurious correlation？

这对方法设计很重要，因为不同偏置需要不同方法。

### 7.3 从 full permutation 转向低成本校正

> [!note] 这里的 full permutation 在之前的论文中一般意味着全排列，比如 5 项全排列是 5! = 120

多排列投票通常有效，但成本高。  
因此后续工作在寻找更便宜的方法：

- prior calibration；
- logit correction；
- decomposed task calibration；
- efficient majority voting；
- KV caching；
- student distillation；
- LoRA fine-tuning；
- learned permutation policy。


### 7.4 从模型去偏转向 benchmark 去偏

尤其在 VQA / VideoQA 中，很多问题不是模型一个人的问题，而是 benchmark 本身存在 shortcut：

- 选项太容易；
- 错误选项太弱；
- 问题-答案统计相关；
- 视频-答案统计相关；
- 文本 shortcut；
- 音频/视频信息没有被真正使用。

因此 benchmark cleaning 和 hard negative construction 是非常重要的一条线。

### 7.5 从 global bias 转向 context-dependent bias

早期方法常把偏置看成全局选项先验，例如模型整体偏 A 或 C。  
但越来越多工作暗示偏置可能和上下文相关：

- 不确定样本更容易受选项顺序影响；
- 选项语义相似度越高，bias 越明显；
- 多模态证据越弱，blind guessing 越明显；
- 不同模型、不同 prompt、不同数据集的偏置方向不同。

这意味着未来方法可能需要 sample-level 或 context-aware debiasing。

## 8. related work组织

### 8.1 Selection bias in LLM multiple-choice evaluation

- PriDe；
- Sensitivity to Option Order；
- Unveiling Selection Biases；
- PIF；
- General Permutation Debiasing；
- Quantifying and Mitigating Selection Bias。


> MCQA 虽然是 LLM 评测的主流形式，但模型在选择题中存在 option ID、option order、option token、symbol binding 等偏置，因此直接使用 accuracy 可能高估或低估真实能力。

### 8.2 Selection bias in multimodal and video QA


- BOLD；
- LVLM selection bias logit correction；
- NExT-OOD；
- Easy Option Bias；
- AVUT。


> 多模态 MCQA 中，偏置不仅来自文本选项顺序，还来自视觉证据不足、视觉-答案相关、问题-答案相关、选项内容容易程度、以及 benchmark shortcut。

### 8.3 Inference-time debiasing methods


- PriDe；
- BOLD；
- LVLM logit correction；
- permutation self-consistency；
- efficient majority voting。


> 免训练方法适合 frozen / black-box / API 模型，但常在推理成本、logit 可访问性、校准泛化之间权衡。

### 8.4 Training-based debiasing methods


- PIF；
- General Permutation Debiasing；
- LoRA-1；
- EMBER。


> 训练型方法试图将去偏能力内化到模型中，降低推理开销，但需要训练数据和额外参数更新，不适合严格 zero-shot / training-free 设置。


### 8.5 Benchmark and data debiasing

- NExT-OOD；
- GroundAttack；
- AVUT。

> 除了修正模型，修正 benchmark 本身也很关键，因为 MCQA 任务容易被文本 shortcut、视觉 shortcut、弱负选项和 spurious correlation 污染。


## 10. 总结

它其实包括三层问题：

1. **评测可靠性问题**：MCQA accuracy 是否真的反映模型能力？
2. **模型行为问题**：模型是否具有 option-order invariance、symbol binding、视觉证据利用能力？
3. **方法设计问题**：应该用推理时校正、训练去偏，还是 benchmark 清洗？

从当前文献看：

- **文字 LLM MCQA**：偏置诊断和方法最多，已经形成 option ID / order / token / symbol binding 体系。
- **LVLM / VQA**：开始关注 option token、视觉难度、hard negative、logit correction。
- **VideoQA**：BOLD、NExT-OOD、Easy Option Bias、AVUT 等说明视频 MCQA 中存在多种 shortcut 和偏置，但系统性方法仍在发展。
- **训练方法**：PIF、General Permutation Debiasing、LoRA、EMBER 等代表把去偏能力内化到模型中的路线。
- **免训练方法**：PriDe、BOLD、logit correction、permutation self-consistency、majority voting 等更适合 frozen / black-box / training-free 场景。
- **benchmark 方法**：NExT-OOD、GroundAttack、AVUT 说明很多问题需要从数据构造和评测协议层面解决。

更细分一点，
- 偏置来自哪里；
- 是位置、符号、顺序、内容，还是数据集 shortcut；
- 目标是诊断、校正、训练去偏，还是修 benchmark；
- 方法是否需要训练、logits、校准集、多次推理；
- 适用场景是 text LLM、image LVLM，还是 VideoQA / MC VideoQA。

## 参考文献与链接

1. Zheng et al. **Large Language Models Are Not Robust Multiple Choice Selectors**. ICLR 2024.  https://openreview.net/forum?id=shr9PXz7T0

2. Pezeshkpour and Hruschka. **Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions**. Findings of NAACL 2024. 
    https://aclanthology.org/2024.findings-naacl.130/

3. Wei et al. **Unveiling Selection Biases: Exploring Order and Token Sensitivity in Large Language Models**. Findings of ACL 2024. 
  https://aclanthology.org/2024.findings-acl.333/

4. Liusie et al. **Teacher-Student Training for Debiasing: General Permutation Debiasing for Large Language Models**. Findings of ACL 2024.  
   https://aclanthology.org/2024.findings-acl.81/

5. Xue et al. **Strengthened Symbol Binding Makes Large Language Models Reliable Multiple-Choice Selectors**. ACL 2024.  https://aclanthology.org/2024.acl-long.237/

6. Loginova et al. **Addressing Blind Guessing: Calibration of Selection Bias in Multiple-Choice Question Answering by Video Language Models**. ACL 2025. https://aclanthology.org/2025.acl-long.162/

7. Atabuzzaman et al. **Benchmarking and Mitigating MCQA Selection Bias of Large Vision-Language Models**. EMNLP 2025. https://arxiv.org/abs/2509.16805

8. Guda et al. **Quantifying and Mitigating Selection Bias in LLMs: A Transferable LoRA Fine-Tuning and Efficient Majority Voting Approach**. Findings of IJCNLP-AACL 2025.  https://aclanthology.org/2025.findings-ijcnlp.127/

9. Tang et al. **Found in the Middle: Permutation Self-Consistency Improves Listwise Ranking in Large Language Models**. NAACL 2024.  
   https://aclanthology.org/2024.naacl-long.129/

10. Yang et al. **Audio-centric Video Understanding Benchmark without Shortcuts**. EMNLP 2025.  
    https://aclanthology.org/2025.emnlp-main.333/

11. Zhang et al. **Mitigating Easy Option Bias in Multiple-Choice Question Answering**. arXiv 2025. https://arxiv.org/abs/2508.13428

12. Zhang et al. **NExT-OOD: Overcoming Dual Multiple-choice VQA Biases**. TPAMI 2023. 
    https://github.com/zhangxi1997/NExT-OOD

13. Jiao et al. **Embracing Positional Bias in Multiple-Choice Question Answering via Permutation Equivariant Neural Networks**. AAAI 2026.  
    https://ojs.aaai.org/index.php/AAAI/article/view/40401
