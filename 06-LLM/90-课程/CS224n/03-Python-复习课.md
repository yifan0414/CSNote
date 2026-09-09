---
title: "CS224N 03 Python 复习课"
aliases:
  - "Python Review Session"
tags:
  - cs224n
  - nlp
  - course-note
type: learning-note
course: Stanford CS224N
term: Winter 2026
session: 3
date_text: "Fri Jan 9"
status: complete
created: 2026-09-04
source: https://web.stanford.edu/class/cs224n/index.html
---
# CS224N 03：Python 复习课

> [!abstract] 本节定位
> 面向 CS224N 作业的 Python、NumPy、Notebook 与调试实践入门。

## 学习目标

- [ ] 熟练使用 NumPy 数组、索引和 broadcasting
- [ ] 用向量化计算替代不必要的 Python 循环
- [ ] 能在 Jupyter 或 Colab 中运行、调试和复现实验

## 知识笔记

> [!info] 课件范围
> 对应 Python Review Session 的 66 页课件：解释器与环境、Python 基础、集合与类、NumPy、索引和 broadcasting，以及面向课程作业的调试方法。

## 1. Python 的执行模型

Python 是解释执行语言。当前解释器决定：

- Python 版本；
- 已安装的包；
- 包从哪个环境加载；
- Notebook 内核实际运行在哪里。

### 常见环境

| 环境 | 优点 | 易错点 |
| --- | --- | --- |
| 系统 Python | 开箱即用 | 不适合随意修改依赖 |
| venv | 标准库自带、轻量 | 需要明确激活 |
| Conda | 能管理 Python 与非 Python 依赖 | 环境与 pip 可能混用 |
| Colab | 无需本地配置、可用云端硬件 | 运行时会重置，文件不持久 |

遇到“已经安装却无法 import”，先检查：

```python
import sys
print(sys.executable)
print(sys.version)
```

再确认安装命令使用的是同一解释器。

## 2. 变量、对象与类型

Python 变量是指向对象的名称，而不是预先声明类型的内存槽：

```python
x = 5
x = "five"
```

可变对象有别名问题：

```python
a = [1, 2]
b = a
b.append(3)
# a 也变为 [1, 2, 3]
```

若需要独立列表，应显式复制。对于嵌套可变对象，浅复制仍共享内部对象，还要区分 shallow copy 与 deep copy。

## 3. 比较、布尔逻辑与控制流

### 3.1 相等与同一性

- `==` 比较值；
- `is` 比较是否为同一对象；
- 与 `None` 比较使用 `is None`。

### 3.2 Truthiness

以下对象在布尔上下文中通常为假：

- `False`；
- `None`；
- 数值 0；
- 空字符串；
- 空 list、tuple、dict、set。

不要在需要区分“0”和“缺失值”的代码中只写 `if x`。

### 3.3 循环与迭代

优先直接遍历对象；需要索引时使用 `enumerate`，并行遍历使用 `zip`。

需要所有两两组合时，应先估算复杂度，避免无意构造 $O(N^2)$ 中间列表。

## 4. Python 集合

### 4.1 List

List 有顺序、可变、允许重复。

常用操作：

- `append(x)`：加入一个元素；
- `extend(xs)`：加入多个元素；
- `pop()`：移除并返回元素；
- `xs[a:b:c]`：切片；
- `x in xs`：线性成员查询。

负索引从末尾开始，切片右端不包含。

### 4.2 Tuple

Tuple 有顺序但不可变，可用于：

- 返回多个值；
- 作为 dict key；
- 表示不应原地修改的结构。

### 4.3 Dict

Dict 存储 key–value 映射，平均成员查询为常数时间。课程中常用于：

- `word_to_id`；
- 配置与超参数；
- 频次统计；
- 保存指标。

频次统计可使用 `collections.Counter`，缺省值可使用 `defaultdict`。

### 4.4 Set

Set 无重复元素，适合建立词表、去重、快速成员测试以及集合的交、并、差。

若输出顺序影响可复现性，应先排序，不能依赖集合显示顺序。

## 5. 函数与作用域

函数参数可以是位置参数、关键字参数和带默认值参数。

### 可变默认参数陷阱

错误写法中的默认列表只在函数定义时创建一次：

```python
def add_item(x, bucket=[]):
    bucket.append(x)
    return bucket
```

安全写法：

```python
def add_item(x, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(x)
    return bucket
```

## 6. 类与模块

类把状态与行为放在一起。课程代码中尤其要理解：

- `self` 指当前对象；
- `__init__` 初始化状态；
- 继承允许扩展父类；
- 模型类通常继承 PyTorch 的 `nn.Module`；
- `import module` 与 `from module import name` 对命名空间影响不同。

> [!tip]
> 不要把脚本命名为 `torch.py`、`numpy.py` 等包名，否则 Python 可能优先导入当前文件。

## 7. NumPy ndarray

### 7.1 三个核心属性

- `shape`：每个轴的长度；
- `dtype`：元素类型；
- `ndim`：轴的数量。

例如：

$$
X\in\mathbb{R}^{B\times N\times D}
$$

对应 shape `(B,N,D)`。shape 是深度学习调试的第一信息，dtype 决定数值语义与内存成本。

### 7.2 元素运算与矩阵运算

- `a * b`：逐元素乘；
- `a @ b`：矩阵乘。

若：

$$
A\in\mathbb{R}^{M\times K},\qquad
B\in\mathbb{R}^{K\times N},
$$

则：

$$
AB\in\mathbb{R}^{M\times N}.
$$

不要用逐元素乘代替线性代数中的矩阵乘。

## 8. 索引

### 8.1 基本索引

- `x[0]`：第一个元素或第一行；
- `x[:,2]`：所有行的第 3 列；
- `x[...,-1]`：最后一维的最后一个元素。

整数索引通常会消去维度，切片会保留：

$$
\operatorname{shape}(x[0])
\ne
\operatorname{shape}(x[0:1]).
$$

### 8.2 Advanced indexing

整数数组可按指定顺序取多个元素，布尔数组按 mask 选择。

高级索引通常返回副本，普通切片常返回 view。原地修改前要确认是否共享内存。

## 9. Broadcasting

从最后一维向前比较两个 shape。每对维度必须满足：

1. 两者相等；或
2. 其中一个为 1；或
3. 较短 shape 在该位置没有维度。

例如：

$$
X:[B,N,D],\qquad b:[D]
$$

可以相加：

$$
Y_{b,n,d}=X_{b,n,d}+b_d.
$$

但 `[B,N,D]+[N]` 通常失败，因为尾维是 $D$ 与 $N$。若要沿序列维加偏置，应显式 reshape 为 `[1,N,1]`。

> [!warning] 广播不等于总是免费
> 广播视图可以不复制数据，但后续逐元素运算仍可能产生完整的 $B\times N\times D$ 结果。

## 10. 沿轴归约

`sum`、`mean`、`max` 等操作的 axis 表示被消去的维：

$$
X:[B,N,D]
\xrightarrow{\operatorname{sum}(\text{axis}=1)}
[B,D].
$$

若保留维度，结果为 `[B,1,D]`，更容易继续广播。

## 11. 向量化

向量化将 Python 循环交给底层优化内核：

```python
y = x + bias
```

优势包括：

- 循环在编译代码中执行；
- 内存访问更连续；
- 可调用 BLAS；
- 表达更接近数学公式。

但不要为了“没有循环”构造巨大两两张量。例如 `[N,N,D]` 中间量可能比分块循环更昂贵。

## 12. 面向作业的调试流程

1. 从 traceback 最底部找到实际异常。
2. 打印相关张量的 shape、dtype、最小值和最大值。
3. 使用极小输入手算期望输出。
4. 检查是否误用了 view、副本或原地运算。
5. 固定随机种子。
6. 先跑单元测试，再跑完整训练。
7. Notebook 重启内核并 Run All。

常见错误：

- `TypeError`：对象类型或调用方式错误；
- `IndexError`：索引越界或维数不符；
- `KeyError`：词表或字典缺键；
- `ValueError`：无法广播或解包数量错误；
- `ModuleNotFoundError`：解释器环境不一致。

## 13. 小结

- Python 变量指向对象，必须注意可变对象共享。
- NumPy 的核心是 shape、dtype、索引、矩阵运算和 broadcasting。
- 向量化通常更快，但也要考虑中间张量大小。
- 对 CS224N 作业，最有效的调试顺序通常是：最小样例 → shape → 数值 → 单元测试 → 完整训练。

## 官方资料与本地文件

| 类型 | 资料与本地文件 | 官网 / 原始页 |
| --- | --- | --- |
| PPT / 课件 | [[2024 CS224N Python Review Session Slides.pptx.pdf\|slides]] | [原始链接](<https://web.stanford.edu/class/cs224n/slides_w25/2024 CS224N Python Review Session Slides.pptx.pdf>) |
| Notebook | [[session-03-python-review-session.ipynb\|colab]] | [原始链接](<https://colab.research.google.com/drive/1hxWtr98jXqRDs_rZLZcEmX_hUcpDLq6e?usp=sharing>) |

## 建议学习流程

1. 带着学习目标快速浏览 PPT、讲义或 Notebook，先建立本节地图。
2. 第二遍按核心提纲停下推导公式、追踪 shape 或复现代码。
3. 在指定阅读中寻找课件结论的实验依据、假设和适用边界。
4. 不看资料回答自测题，将答不清的点写入学习记录。

## 自测问题

1. 形状 (B,N,D) 与 (D,) 相加时发生什么？
2. 向量化何时会意外创建巨大中间张量？
3. 如何确认 Notebook 从头运行仍得到相同结果？

## 学习记录

- [ ] 已通读 PPT / 主资料
- [ ] 已完成指定阅读
- [ ] 已回答自测问题
- 我仍不清楚的点：
- 与前后课的联系：
