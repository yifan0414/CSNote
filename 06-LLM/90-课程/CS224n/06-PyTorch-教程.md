---
title: "CS224N 06 PyTorch 教程"
aliases:
  - "PyTorch Tutorial Session"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 6
date_text: "Fri Jan 16"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 06：PyTorch 教程

> [!abstract] 本节定位
> 用 tensor、autograd、Module 与 optimizer 搭建可训练的神经网络。

## 学习目标

- [ ] 区分 tensor 数据、计算图和 parameter
- [ ] 使用 Module 组织模型与子层
- [ ] 写出完整且不泄漏梯度的训练和验证循环

## 知识笔记

> [!info] 资料范围
> 本节官网提供 PyTorch Tutorial Notebook。正文依次覆盖 Notebook 中的 tensor、索引、autograd、Module、optimizer、DataLoader，以及完整 Word Window Classifier 示例。

## 1. Tensor 是什么

PyTorch tensor 是带有：

- shape；
- dtype；
- device；
- 可选梯度历史

的多维数组。

创建方式包括：

```python
torch.tensor(data)
torch.zeros(shape)
torch.ones(shape)
torch.arange(start, end)
torch.randn(shape)
```

### 常用 dtype

- 浮点参数与激活：通常为 `torch.float32`；
- token id 与类别索引：通常为 `torch.long`；
- mask：通常为 `torch.bool`。

Embedding 的索引输入必须是整数类型，分类标签对 CrossEntropyLoss 通常也使用 long。

## 2. Shape 与基本运算

若：

```python
a.shape == (3, 2)
b.shape == (2, 4)
```

则：

```python
c = a @ b
c.shape == (3, 4)
```

常用变形：

- `reshape`：按元素总数重排；
- `unsqueeze(dim)`：增加长度 1 的轴；
- `squeeze(dim)`：移除长度 1 的轴；
- `transpose`/`permute`：交换轴；
- `view`：要求兼容内存布局。

`permute` 后张量可能 non-contiguous；需要依赖连续内存的 view 前，可调用 `contiguous()` 或使用 `reshape`。

## 3. 索引与广播

PyTorch 索引规则与 NumPy 接近：

```python
x[0]
x[:, 1]
x[..., -1]
x[index_tensor]
```

广播仍从尾维对齐。例如：

$$
[B,N,D]+[D]\to[B,N,D].
$$

调试时不要只问“是否能广播”，还要问“语义上希望沿哪个轴共享”。

## 4. NumPy 与 Tensor 转换

```python
t = torch.from_numpy(array)
array = t.detach().cpu().numpy()
```

CPU tensor 与 NumPy 数组可能共享底层内存，原地修改会相互影响。

带梯度或位于 GPU 的 tensor 不能直接转 NumPy：

1. `detach()` 脱离计算图；
2. `cpu()` 移到 CPU；
3. `numpy()` 转换。

## 5. Autograd

### 5.1 建图

```python
x = torch.tensor([2.0], requires_grad=True)
y = 3 * x * x
y.backward()
```

数学上：

$$
y=3x^2,
\qquad
\frac{dy}{dx}=6x.
$$

结果写入：

```python
x.grad
```

### 5.2 梯度默认累加

重复 backward 会把新梯度加到 `.grad`：

$$
g\leftarrow g+g_{\text{new}}.
$$

训练循环每次更新前通常要：

```python
optimizer.zero_grad()
```

有意跨多个 micro-batch 累加梯度时才不清零，但需要按累加步数正确缩放 loss。

### 5.3 关闭梯度记录

验证和推理：

```python
with torch.no_grad():
    ...
```

或使用 inference mode。它们减少图和激活存储，但不会自动切换 dropout、batch norm 等模块行为。

## 6. Module 与参数注册

### 6.1 线性层

```python
layer = nn.Linear(H_in, H_out)
```

对输入：

$$
X:[N,\ldots,H_{\text{in}}],
$$

输出：

$$
Y:[N,\ldots,H_{\text{out}}].
$$

线性层只变换最后一维。

### 6.2 Sequential

```python
block = nn.Sequential(
    nn.Linear(input_dim, hidden_dim),
    nn.ReLU(),
    nn.Linear(hidden_dim, output_dim),
)
```

适合简单串行数据流。存在分支、残差、多个输入或 mask 时，显式写 forward 更清晰。

### 6.3 自定义 Module

```python
class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.linear1 = nn.Linear(input_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        return self.linear2(torch.relu(self.linear1(x)))
```

只有注册为 Module 属性或 Parameter 的对象会出现在：

```python
model.parameters()
model.state_dict()
```

把可训练层放进普通 Python list 可能导致参数无法注册；应使用 ModuleList。

## 7. 优化器与训练循环

典型流程：

```python
model.train()
for x, y in loader:
    optimizer.zero_grad()
    logits = model(x)
    loss = loss_fn(logits, y)
    loss.backward()
    optimizer.step()
```

顺序含义：

1. 清除上一步梯度；
2. 前向建立当前图；
3. 计算标量 loss；
4. backward 填充参数梯度；
5. optimizer 根据梯度更新参数。

### SGD 与 Adam

SGD：

$$
\theta_{t+1}
=
\theta_t-\eta g_t.
$$

Adam 对一阶和二阶矩做移动平均，为每个参数自适应缩放更新。Adam 更易快速得到可用结果，但并不免除学习率、权重衰减和验证集调参。

## 8. Dataset、DataLoader 与 collate_fn

序列样本长度不同，不能直接 stack。

DataLoader 负责：

- 按 batch 取样；
- shuffle；
- 多进程加载；
- 调用 collate_fn。

自定义 collate_fn 通常：

1. 将 token 序列转 long tensor；
2. 记录原始长度；
3. 用 pad_sequence 补齐；
4. 生成标签和 mask；
5. 返回 batch。

若最长序列为 $L_{\max}$：

$$
\text{token ids}:[B,L_{\max}].
$$

Padding 不应被当作真实 token 参与 loss 或池化。

## 9. Embedding

```python
embedding = nn.Embedding(
    num_embeddings=V,
    embedding_dim=D,
    padding_idx=pad_id,
)
```

本质是可训练矩阵：

$$
E\in\mathbb{R}^{V\times D}.
$$

输入：

$$
I:[B,L]
$$

输出：

$$
E[I]:[B,L,D].
$$

同一个词多次出现时，对应行的梯度会累加。设置 padding_idx 可避免 padding 行被正常更新。

## 10. Word Window Classifier

Notebook 最终将前面组件组合成窗口分类器。

### 10.1 数据流程

1. 文本小写和分词；
2. 建立 vocabulary；
3. 加入 UNK 和 PAD；
4. token 转 id；
5. 补齐 batch；
6. 为每个中心位置提取左右窗口；
7. embedding lookup；
8. 拼接窗口表示；
9. MLP 与二分类。

若窗口半径为 $m$：

$$
\text{window width}=2m+1.
$$

Embedding 后：

$$
X:[B,L,2m+1,D].
$$

展平窗口：

$$
X_{\text{flat}}:[B,L,(2m+1)D].
$$

再经隐藏层与输出层：

$$
H:[B,L,H_d],
\qquad
\hat y:[B,L,1].
$$

### 10.2 Padding 与窗口

句首句尾没有完整上下文，应加入 PAD 使每个中心词都有同样宽度窗口。

需要区分：

- 用于补足窗口边界的 PAD；
- 用于 batch 长度对齐的 PAD；
- 对应标签是否应计入 loss。

通常对无效位置生成 mask，计算 loss 时排除。

## 11. 二分类 loss

若模型输出概率：

$$
\hat y=\sigma(z),
$$

可用 binary cross-entropy：

$$
L
=
-y\log\hat y
-(1-y)\log(1-\hat y).
$$

实际更推荐直接输出 logits，并使用 BCEWithLogitsLoss，以提高数值稳定性。

## 12. 训练与评估模式

- `model.train()`：启用训练行为；
- `model.eval()`：启用推理行为；
- `torch.no_grad()`：关闭梯度记录。

正确验证：

```python
model.eval()
with torch.no_grad():
    ...
```

二者不能互相替代。

## 13. 实践检查清单

> [!check] 每个 batch
> - token id 是 long；
> - 浮点输入和参数 dtype 相容；
> - 所有张量位于同一 device；
> - logits 和 label shape 与 loss 要求一致；
> - padding 被 mask；
> - loss 是标量或被正确 reduction；
> - 更新前已按预期清梯度。

## 14. 小结

- Tensor 在 ndarray 基础上增加 device 和自动微分。
- Module 负责组织并注册参数，forward 定义数据流。
- DataLoader 与 collate_fn 解决批处理、补齐和动态预处理。
- Embedding 是按整数 id 查表的可训练矩阵。
- 完整训练循环必须正确处理模式、梯度累加、loss shape 和 padding mask。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| Notebook | [[session-06-pytorch-tutorial-session.ipynb\|colab]] | [原始链接](<https://colab.research.google.com/drive/1Pz8b_h-W9zIBk1p2e6v-YFYThG1NkYeS?usp=sharing>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 为什么连续两次反向默认会累加梯度？
2. 评估模式与关闭梯度记录各解决什么？
3. 如何快速定位 device 或 dtype 不匹配？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
