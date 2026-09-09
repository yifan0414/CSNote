---
title: "CS224N 13 Hugging Face Transformers 教程"
aliases:
  - "Hugging Face Transformers Tutorial Session"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 13
date_text: "Fri Feb 6"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 13：Hugging Face Transformers 教程

> [!abstract] 本节定位
> 使用 tokenizer、Auto classes、pipeline 与训练接口进行预训练模型推理和微调。

## 学习目标

- [ ] 使用与 checkpoint 匹配的 tokenizer 和 model
- [ ] 正确处理 padding、truncation、mask 与 batch
- [ ] 在高层 API 和手写循环之间做选择

## 知识笔记

> [!info] 资料范围
> 本节综合 Hugging Face Transformers Tutorial 的 20 页课件与配套 Notebook：tokenizer、Auto classes、模型头、推理、Datasets、Trainer、文本生成、pipeline 和 masked language modeling。

## 1. Hugging Face 生态

Transformers 提供：

- 预训练模型实现；
- tokenizer；
- 配置；
- 任务特定 head；
- 生成工具；
- Trainer。

常配合：

- Hugging Face Hub：模型和数据版本；
- Datasets：数据加载与变换；
- Evaluate：指标；
- Accelerate：设备与分布式执行。

## 2. 通用工作流

1. 选择 checkpoint；
2. 加载 tokenizer；
3. 加载与任务匹配的 model class；
4. 预处理输入；
5. 前向或 generate；
6. 将 token id 解码为文本；
7. 根据任务评测。

```python
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint)
```

Tokenizer 与 model 必须来自兼容 checkpoint，否则 token id 的语义和 embedding 行不匹配。

## 3. Tokenizer

### 编码

```python
encoded = tokenizer(
    texts,
    padding=True,
    truncation=True,
    return_tensors="pt",
)
```

常见输出：

- `input_ids`；
- `attention_mask`；
- 某些模型的 `token_type_ids`。

### 特殊 token

- BOS/CLS；
- EOS/SEP；
- PAD；
- MASK；
- UNK。

不要假设所有模型都有同一组特殊 token。例如 GPT-2 原本没有独立 pad token。

### 子词对齐

token classifier 中，一个原始单词可能拆为多个 subtoken。必须决定：

- 标签复制到全部 subtoken；
- 只标第一个；
- 其余位置以 ignore index 屏蔽。

## 4. Padding、Truncation 与 Batching

动态 padding 将每个 batch 补到该 batch 最长长度，比全数据补到固定上限节省计算。

Attention mask：

$$
M_{b,t}
=
\begin{cases}
1,& \text{真实 token},\\
0,& \text{padding}.
\end{cases}
$$

截断需要明确：

- 最大长度；
- 从左还是从右；
- 长文档是否使用 stride 和 overflow；
- 被截部分是否包含答案。

Decoder-only 批量生成常要特别检查 left padding 与 position ids。

## 5. 模型架构与任务头

### Base model

- `AutoModel` 返回 hidden states；
- 不自带任务 loss。

### Task-specific model

- `AutoModelForSequenceClassification`；
- `AutoModelForTokenClassification`；
- `AutoModelForQuestionAnswering`；
- `AutoModelForCausalLM`；
- `AutoModelForMaskedLM`；
- `AutoModelForSeq2SeqLM`。

任务头决定 logits shape 和 label 格式。

例如序列分类：

$$
\text{logits}:[B,C].
$$

token 分类：

$$
\text{logits}:[B,L,C].
$$

Causal LM：

$$
\text{logits}:[B,L,|V|].
$$

## 6. 输出对象

模型通常返回 ModelOutput，可通过属性读取：

- `loss`；
- `logits`；
- `hidden_states`；
- `attentions`；
- `past_key_values`。

只有传入正确 labels 时才会自动计算 loss。不同任务的 labels 语义不同，不能只看 shape 相同。

## 7. 推理模式

```python
model.eval()
with torch.no_grad():
    outputs = model(**encoded)
```

- `eval()` 切换 dropout 等模块；
- `no_grad()` 关闭梯度图。

输入应移动到与模型相同 device。输出 logits 还不是概率；分类时可按需要 softmax，生成时通常交给 `generate`。

## 8. Datasets

典型数据管线：

1. load_dataset；
2. 查看 split 与字段；
3. tokenize/map；
4. 删除无用文本列；
5. rename label；
6. 设置格式；
7. data collator 动态组成 batch。

```python
tokenized = dataset.map(
    tokenize_function,
    batched=True,
)
```

`batched=True` 让 tokenizer 批量执行，但传入函数的是字段列表而非单条样本。

## 9. Fine-Tuning

### TrainingArguments

常见配置：

- learning rate；
- batch size；
- epochs；
- weight decay；
- warmup；
- evaluation/save strategy；
- mixed precision；
- best model metric。

### Trainer

Trainer 管理：

- DataLoader；
- optimizer 与 scheduler；
- gradient accumulation；
- evaluation；
- checkpoint；
- callback；
- 日志。

高层接口减少样板代码，但仍需理解实际 batch、loss 和评测。

## 10. IMDB 情感分类流程

1. 加载 IMDB；
2. tokenizer 对文本编码；
3. 使用 sequence classification model；
4. 训练；
5. 计算 accuracy；
6. 对自定义文本预测。

关键 shape：

$$
\text{input ids}:[B,L],
$$

$$
\text{labels}:[B],
$$

$$
\text{logits}:[B,2].
$$

不能在 test set 上挑 learning rate 或 epoch。

## 11. 文本生成

```python
output_ids = model.generate(
    **inputs,
    max_new_tokens=...,
    do_sample=True,
    temperature=...,
    top_p=...,
)
```

### 关键参数

- `max_new_tokens`：新生成长度；
- `temperature`：logits 缩放；
- `top_k`：只保留最高 $k$；
- `top_p`：保留累计概率达到 $p$ 的最小集合；
- `num_beams`：beam search；
- `repetition_penalty`：启发式重复惩罚；
- `eos_token_id`：停止 token。

`max_length` 包含 prompt，`max_new_tokens` 只控制新输出，后者通常更直观。

## 12. Pipeline

```python
classifier = pipeline("sentiment-analysis")
generator = pipeline("text-generation")
```

Pipeline 适合：

- 快速试验；
- 演示；
- 标准任务默认预处理。

不适合：

- 需要精确 batch 和显存控制；
- 读取内部状态；
- 自定义 loss；
- 复杂后处理；
- 可复现实验需固定所有参数。

## 13. Masked Language Modeling

Masked LM 使用 MASK 恢复 token：

```python
fill_mask = pipeline("fill-mask", model=checkpoint)
```

它输出候选 token 及分数。不要把 MLM checkpoint 当作标准自回归生成器，因为训练时的信息可见方式不同。

## 14. 常见失败

> [!warning] 模型类选错
> Base model 没有任务 head，CausalLM、MaskedLM 与 Seq2SeqLM 的标签和生成接口也不同。

> [!warning] Padding 进入 loss
> token 级任务应把无效标签设为 ignore index，生成任务要屏蔽 prompt 或 padding 的 loss。

> [!warning] Tokenizer 与 checkpoint 不匹配
> 即使词表大小巧合相同，token id 的语义也可能不同。

> [!warning] 只保存权重
> 可复现 checkpoint 还应保存 tokenizer、config、label mapping 和生成参数。

## 15. 小结

- Hugging Face 的核心抽象是 checkpoint + tokenizer + config + task head。
- Padding、truncation、mask 和 label 对齐决定数据语义。
- Auto classes 简化加载，但 model class 必须与任务一致。
- Trainer 自动化训练流程，却不能替代对 loss、split 和指标的理解。
- Pipeline 用于快速调用，严谨实验应显式控制预处理、模型和解码。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[hf_transformers_tutorial.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/materials/hf_transformers_tutorial.pdf>) |
| Notebook | [[session-13-hugging-face-transformers-tutorial-session.ipynb\|colab]] | [原始链接](<https://colab.research.google.com/drive/1FyCMNTXfirWbJ18GuIT_JiTW0gwrxI3O?usp=sharing>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 为何 tokenizer 不能随意换成另一个同语言 tokenizer？
2. padding token 在 loss 中应如何处理？
3. 何时应离开 pipeline 使用底层接口？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
