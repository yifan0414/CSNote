---
created: 2025-04-01 20:33
updated: 2026-09-09
aliases:
  - 梯度归一化 .sum().backward()
tags:
  - PyTorch
  - 反向传播
  - 梯度累积
---

# PyTorch 损失归约与梯度累积：先确定平均什么，再决定在哪里除

> [!abstract] 这篇笔记怎样读
> `l.sum().backward()` 把一批损失加起来，为什么还可以正确训练？不清空梯度，又为什么会把不同批次的结果加在一起？
>
> 两个问题共享一条逻辑：**先定义训练目标 → 把多个损失归约成标量 → 利用求导的线性性 → 在参数保持不变时累积 → 用目标对应的分母归一化 → 执行一次更新。**
>
> 数学更新规则见 [[梯度下降与 SGD]]。本文把这条规则与 PyTorch 的 `backward()`、`.grad`、`zero_grad()` 和 `step()` 对齐。

## 1. 从一个样本到一批样本：反向传播应该对哪个数求导

假设一批有 $B$ 个样本，每个样本得到一个标量损失 $\ell_i(\theta)$。它们构成一组数，但训练最终需要一个明确的标量目标。

两种常见定义是：

$$
L_{\mathrm{sum}}=\sum_{i=1}^{B}\ell_i,
\qquad
L_{\mathrm{mean}}=\frac1B\sum_{i=1}^{B}\ell_i.
$$

这叫**损失归约（reduction）**。`sum` 和 `mean` 都能定义可求导的标量，区别在于我们希望优化总量还是平均量。

若 `losses` 中恰好每个样本一个损失，`losses.sum().backward()` 对总损失求导，`losses.mean().backward()` 对平均损失求导。非标量张量也能通过显式传入上游梯度调用 `backward(gradient=...)`；默认不传时，需要标量输出。[PyTorch backward 文档](https://docs.pytorch.org/docs/2.14/generated/torch.Tensor.backward.html)

## 2. 先求和再反传，为什么就是把样本梯度相加

求导对加法与固定常数倍满足线性性，因此：

$$
\nabla_\theta L_{\mathrm{sum}}
=\sum_{i=1}^{B}\nabla_\theta\ell_i,
\qquad
\nabla_\theta L_{\mathrm{mean}}
=\frac1B\sum_{i=1}^{B}\nabla_\theta\ell_i.
$$

所以将损失先加起来不会丢掉它们对参数的贡献。反向传播会沿计算图，把这些贡献汇总到同一个参数的梯度中。

对**同一批数据、同一组参数**，总损失梯度严格等于平均损失梯度的 $B$ 倍。对普通 SGD，下面两种方式因此等价：

| 计算梯度 | 更新时使用什么 |
|---|---|
| 对平均损失反传 | 直接使用得到的梯度 |
| 对总损失反传 | 把梯度除以实际的 $B$ 后再更新 |

**只能归一化一次。** 如果损失已经取 `mean`，更新时又除以 $B$，就把梯度额外缩小了 $B$ 倍。

> [!note] 平均消除的是显式倍数，不是所有批量效应
> “批量越大，总梯度绝对值一定越大”并不正确，样本梯度可能互相抵消。平均损失消除了总和中的显式数量因子，但不同样本、抽样噪声和批量相关层仍会影响梯度。
>
> 对 Adam 等带历史状态的优化器，临时更改梯度尺度也不能简单视为同一次 SGD 学习率缩放。应先统一目标的归约方式，再比较优化器行为。

## 3. 回到最初代码：为什么 `sum` 后的手写 SGD 要除以批量大小

设线性模型给每个样本输出一个标量，损失定义为半平方误差。原来的计算意图可以写成：

```python
import torch

def sgd(params, lr, normalizer):
    """params 为可重复遍历的参数列表，normalizer 是实际归一化分母。"""
    if normalizer <= 0:
        raise ValueError("normalizer must be positive")
    with torch.no_grad():
        for param in params:
            if param.grad is not None:
                param.add_(param.grad, alpha=-lr / normalizer)
                param.grad.zero_()

def train_linear_epoch(data_iter, w, b, lr):
    # X: (B, D)，y: (B, 1)，w: (D, 1)，b: (1,)
    params = [w, b]
    for param in params:
        param.grad = None
    for X, y in data_iter:
        prediction = X @ w + b
        assert prediction.shape == y.shape  # 避免广播悄悄改变目标
        losses = 0.5 * (prediction - y).square()
        losses.sum().backward()
        sgd(params, lr, normalizer=X.shape[0])
```

这里先对总损失反传，再在手写更新中除以实际批量大小。最后一批不足预设大小时，必须使用 `X.shape[0]`，否则尾批梯度会被错误缩小。手写函数还负责清空 `.grad`，所以这里不会跨批累积。

> [!info]- 补充：怎样记录一轮结束后的训练损失
>
> 原训练循环还在每轮结束后记录整份数据的平均损失。对于这里没有 Dropout、BatchNorm 的线性模型，可以在关闭梯度记录后统一计算：
>
> ```python
> with torch.no_grad():
>     prediction = features @ w + b
>     assert prediction.shape == labels.shape
>     epoch_loss = (0.5 * (prediction - labels).square()).mean().item()
> print(epoch_loss)
> ```
>
> 这里报告的是半均方误差，与训练时定义的目标一致。若数据太大需要分批评估，应累计损失总和与样本总数后再相除，避免将大小不同的批次均值直接平均。

> [!info]- 补充：`mean` 究竟平均了哪些元素
>
> `torch.nn.MSELoss(reduction="mean")` 会平均输入与目标对应的**全部元素**。若预测与标签均属于 $\mathbb R^{B\times D}$，默认分母是 $BD$，不只是 $B$。[MSELoss 文档](https://docs.pytorch.org/docs/2.14/generated/torch.nn.MSELoss.html)
>
> 如果希望“每个样本先把 $D$ 个输出的误差求和，再平均 $B$ 个样本”，就应该显式表达这个目标：
>
> ```python
> element_losses = (prediction - target).square()
> per_sample = element_losses.reshape(element_losses.shape[0], -1).sum(dim=1)
> loss = per_sample.mean()
> ```
>
> 两种目标差一个输出维度因子。它们都可以有意义，关键是先说明希望每个样本、每个输出还是每个 token 占怎样的权重。

## 4. 批内相加与跨批累积，是两层不同的加法

上面讲的是一次 `backward()` 内部把多个损失的贡献相加。PyTorch 还有另一个行为：**新计算出的参数梯度会加到已有的 `.grad` 上。** `backward()` 不会自动把旧值覆盖掉。[PyTorch backward 文档](https://docs.pytorch.org/docs/2.14/generated/torch.Tensor.backward.html)

三个操作因此各司其职：

| 操作 | 改变什么 |
|---|---|
| `loss.backward()` | 计算梯度，并累加到叶子参数的 `.grad` |
| `optimizer.step()` | 根据现有梯度更新参数与优化器状态 |
| `optimizer.zero_grad()` | 重置优化器管理的参数梯度 |

`optimizer.step()` 通常不会替你清空梯度。`zero_grad(set_to_none=True)` 将梯度设为 `None`，与写入全零张量在部分优化器行为上有区别；对未获得梯度的参数，`None` 可能使该参数跳过更新。[zero_grad 文档](https://docs.pytorch.org/docs/2.14/generated/torch.optim.Optimizer.zero_grad.html)

> [!example]- 运行一个小实验，看见 $10\to30\to5$ 的来源
>
> ```python
> import torch
>
> w = torch.tensor(1.0, requires_grad=True)
> (w * torch.ones(10)).sum().backward()
> print(w.grad.item())  # 10.0
>
> (w * torch.ones(20)).sum().backward()
> print(w.grad.item())  # 30.0：旧的 10 加上新的 20
>
> w.grad = None
> (w * torch.ones(5)).sum().backward()
> print(w.grad.item())  # 5.0
> ```
>
> 三次前向分别建立新的计算图，参数 $w$ 保持不变。跨批累积的是叶子参数保存的梯度数值，不需要为了累积而设置 `retain_graph=True`。

## 5. 显存放不下一大批时：在同一组参数上分段计算

假设想优化一个包含 $K$ 个微批次的有效批量，但一次只能放下一个微批次。第 $k$ 个微批次有 $n_k$ 个有效损失项，总数为 $M=\sum_kn_k$。如果目标是每个有效项等权平均：

$$
J(\theta)=\frac1M\sum_{k=1}^{K}\sum_{i=1}^{n_k}\ell_{k,i}(\theta).
$$

其梯度为：

$$
\boxed{\nabla J(\theta)=\frac1M\sum_{k=1}^{K}
\nabla\left(\sum_{i=1}^{n_k}\ell_{k,i}(\theta)\right).}
$$

这给出一种不必事先知道总分母的实现：**每个微批次对总损失反传；累积期间保持参数不变；等一组处理完，按总有效项数除梯度；最后只更新一次。**

如果每个微批次大小相同且恰好累积 $K$ 次，也可以对每个微批次的平均损失再除以 $K$。但尾组不足 $K$ 次，或者各微批次大小不同时，固定除以 $K$ 就不再一般正确。

> [!example]- 不等批量为什么不能把各自的平均值直接平均
>
> 两个微批次分别有 $2$ 和 $6$ 个样本，平均损失分别为 $1$ 和 $3$。所有样本的正确平均是：
>
> $$
> \frac{2\times1+6\times3}{8}=2.5.
> $$
>
> 直接平均两个批次均值会得到 $(1+3)/2=2$，相当于让较小批次中的每个样本获得更大的权重。
>
> 正确的另一种写法是把第 $k$ 个微批次的平均损失乘 $n_k/M$。对梯度也完全一样，因为这些计数不依赖模型参数。

数学上的等价还要求各部分确实组成同一个目标。BatchNorm 使用批内统计，跨样本对比损失依赖同批负样本；把这类批量拆开可能改变前向计算。Dropout 等随机操作也可能使具体数值轨迹不同。因此“梯度累积等价大批量”需要说明模型、损失与随机性的条件。

## 6. 变长序列：分母通常应该是有效 token 数

语言模型里，同样数量的序列可能包含不同数量的有效 token。如果目标是所有非 padding token 等权平均，就不能只除以序列数，也不能把每个微批次的 token 平均值等权再平均。

对于无类别权重、类别索引标签的交叉熵，`ignore_index` 可标记忽略的位置；`mean` 按未忽略的位置平均。若设置了类别权重，分母规则也会随之变化，需要遵循所选目标的定义。[CrossEntropyLoss 文档](https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html)

下面给出一个单设备、普通精度的例子。假设 `model(inputs)` 输出的 logits 属于 $\mathbb R^{B\times T\times C}$；标签含 $B\times T$ 个整数索引，且已与预测位置对齐。代码覆盖不等长度、全忽略微批次和不足累积次数的尾组：

```python
import torch
import torch.nn.functional as F

def train_token_epoch(model, loader, optimizer, accumulation_steps=4,
                      ignore_index=-100):
    if accumulation_steps < 1:
        raise ValueError("accumulation_steps must be positive")
    model.train()
    optimizer.zero_grad(set_to_none=True)
    valid_total = 0
    pending = 0

    def finish_group(count):
        if count > 0:
            # 先归一化完整组的梯度，再执行一次优化器更新。
            with torch.no_grad():
                for group in optimizer.param_groups:
                    for param in group["params"]:
                        if param.grad is not None:
                            param.grad.div_(count)
            # 若需要梯度裁剪，应放在归一化之后、step 之前。
            optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    for inputs, targets in loader:
        pending += 1
        valid_count = int(targets.ne(ignore_index).sum().item())
        if valid_count > 0:
            logits = model(inputs)
            loss_sum = F.cross_entropy(
                logits.reshape(-1, logits.shape[-1]),
                targets.reshape(-1),
                reduction="sum",
                ignore_index=ignore_index,
            )
            loss_sum.backward()
            valid_total += valid_count

        if pending == accumulation_steps:
            finish_group(valid_total)
            valid_total = 0
            pending = 0

    if pending:
        finish_group(valid_total)
```

这里没有在微批次之间调用 `optimizer.step()`，所以一组中的梯度都在同一组参数处计算。全忽略的一组不更新参数，尾组用自己的真实有效 token 数归一化。

> [!info]- 扩展到其他训练配置时，保留同一个目标再调整实现
>
> - **按序列等权**：先分别平均每条序列的有效 token 损失，再对序列求平均；它与按 token 等权是不同目标。
> - **带固定权重的样本**：先确定分母是样本数还是权重和，不能看到 `mean` 就默认除 batch size。
> - **混合精度**：需要把梯度缩放、取消缩放、归一化与裁剪的顺序协调起来；以上代码没有使用 AMP。
> - **分布式训练**：还存在跨进程梯度通信与平均，需要用所有进程的有效项总数推导尺度，不能直接照搬单设备的分母。
> - **学习率调度与动量状态**：通常跟随实际的优化器更新前进；微批次完成一次 `backward()`，不代表完成了一次优化器更新。

理解这段代码的关键只有一个：先把目标写成“需要相加的损失 / 正确的分母”，再检查每一次 `backward()`、每一次除法和每一次 `step()` 是否与它一一对应。
