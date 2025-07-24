---
created: 2025-04-03 20:32
tags:
---
# 0 学习率的起源

## 直观解释
梯度下降顾名思义，我们沿着“最陡”的方向望下走，而**走多远**则取决于另一个参数：学习率 $\eta$
![[Gradient Descent (v2).pdf#page=3&rect=13,26,711,503|Gradient Descent (v2), p.3]]

而 $\eta$ 的取值直接影响了梯度下降的最终结果。
- 如果 $\eta$ 取的恰当：可以很快的收敛，并到达 Global Minimum.
- 如果 $\eta$ 取的不恰当
	- 如果取的值很小，则收敛很慢，消耗资源太大
	- 如果取的值很大，则来回震荡，甚至无法到达 Local Minimum.


![[Gradient Descent (v2).pdf#page=5&rect=14,13,704,527|Gradient Descent (v2), p.5]]

# 1 单参数的梯度下降

对于梯度下降问题，一般都有多个参数，如果把其他参数看做常数，只把剩下的一个参数看做变量，**问题就变成了一个二次优化问题**。尤其是损失函数在二次函数的情况下。

是的，对于梯度下降问题，如果我们只关注单个参数，并且假设其他参数保持不变，那么问题通常会变成一个二次优化问题，尤其是在损失函数是二次函数的情况下。

  

假设损失函数 $L(\mathbf{w})$ 是关于参数 $\mathbf{w}$ 的函数，且我们只关注其中一个参数 $w_i$，将其他参数视为常数。假设损失函数 $L(\mathbf{w})$ 对 $w_i$ 的导数（即梯度）是一个关于 $w_i$ 的线性函数，那么损失函数通常可以表示为一个二次曲线的形式：

$$
L(w_i) = a w_i^2 + b w_i + c
$$
其中，a、b、c 是常数，且 a 是二次项的系数。

在这种情况下，梯度下降方法的目标就是找到使得损失函数最小化的 $w_i$ 值。梯度下降的更新规则是：

$$
w_i \leftarrow w_i - \eta \nabla L(w_i)
$$
对于这个二次函数，梯度是线性的，即：

$$
\nabla L(w_i) = a w_i + b
$$
  然后，梯度下降的更新式变为：

$$
w_i \leftarrow w_i - \eta (a w_i + b)
$$
  

这个更新会沿着 $w_i$ 轴的方向迭代，直到达到损失函数的最小值。在二次函数的情况下，梯度下降方法最终会收敛到全局最优解。
  

总结：当只考虑一个参数并且损失函数是二次函数时，梯度下降问题确实变成了一个二次优化问题。在这种情况下，损失函数通常是一个开口向上的抛物线（如果二次项系数 a > 0），所以梯度下降最终会收敛到该二次曲线的最小值点。

> [!hint] 最优解的解析解
> 是的，您说得对，对于一个二次函数，最佳的步长（即一次更新的步长）可以通过一次微分和二次微分来确定。
> 
> 假设我们有一个二次损失函数：
> 
> $$
> L(w_i) = a w_i^2 + b w_i + c
>$$
> 
> 其中 $a$, $b$, $c$ 是常数，且 $a > 0$ 使得损失函数有一个唯一的最小值。
> 
> ### 1. 一阶导数（梯度）
> 
> 首先，我们计算该函数的梯度（对 $w_i$ 求一阶导数）：
> 
> $$
> \nabla L(w_i) = a w_i + b
>$$
> 
> ### 2. 二阶导数（Hessian）
> 
> 然后，我们计算该函数的二阶导数（对 $w_i$ 求二阶导数）：
> 
> $$
> \frac{d^2 L(w_i)}{d w_i^2} = a
>$$
> 
> ### 3. 求最优解
> 
> 最优解通常出现在梯度为零的点，即：
> 
> $$
> a w_i + b = 0
>$$
> 
> 解得：
> 
> $$
> w_i = -\frac{b}{2a}
>$$
> 
> 这个点就是损失函数的最小值所在的 $w_i$ 值。
> 
> ### 4. 最优的步长
> 
> 为了进行优化，最佳的步长（或者一次更新的步长）可以由二次函数的性质来确定。通过梯度下降法更新参数时，我们使用梯度信息来更新 $w_i$：
> 
> $$
> w_i^{(new)} = w_i^{(old)} - \eta \nabla L(w_i)
>$$
> 
> 其中 $\eta$ 是学习率。如果我们选择最佳的步长，那么每次更新后，$w_i$ 应该正好到达最小值点。最佳步长 $\eta^*$ 可以通过二阶导数来确定。对于二次函数，理想的步长是：
> 
> $$
> \eta^* = \frac{1}{2a}
>$$
> 
> 这是因为，二次函数的更新步长的最佳选择正是二阶导数的倒数，保证了每次更新能够最快地收敛到最小值。
> 
> ### 结论
> 
> 对于一个二次曲线最优化问题（即损失函数是二次函数），最佳的步长确实可以通过一次微分（梯度）和二次微分（Hessian，即二阶导数）来确定，理想的步长就是 $\eta^* = \frac{1}{2a}$。通过选择合适的步长，我们可以确保每次更新都有效地向最优解收敛。
> ![[Gradient Descent (v2).pdf#page=14&rect=28,13,717,497|Gradient Descent (v2), p.14]]


# 2 adagrad 的起源
由最佳步长 $\frac{|First\; derivative|}{second\; derivative}$ 启发，我们使用下图模拟：

![[Gradient Descent (v2).pdf#page=16&rect=30,19,680,512|Gradient Descent (v2), p.16]]


> [!note]- adagrad 的数学含义
> 在 **Adagrad** 优化算法中，分母的设计通过累积每个参数的历史梯度平方来调整学习率，从而使得不同参数的更新步长根据它们梯度的大小进行自适应调整。这种调整机制间接反映了梯度的二阶信息。
> 
> 具体地，Adagrad 使用的更新公式如下：
> 
> $$
> \mathbf{w} \leftarrow \mathbf{w} - \frac{\eta}{\sqrt{G_t + \epsilon}} \nabla L(\mathbf{w})
>$$
> 
> 其中：
> - $\mathbf{w}$ 是模型的参数。
> - $\eta$ 是学习率（通常为一个较小的常数）。
> - $\nabla L(\mathbf{w})$ 是损失函数关于模型参数 $\mathbf{w}$ 的梯度。
> - $G_t$ 是一个累积的平方梯度（即 $G_t = \sum_{i=1}^t \nabla L(\mathbf{w}_i)^2$，它是从训练开始以来，所有梯度的平方的累计和）。
> - $\epsilon$ 是一个非常小的常数（通常是 $10^{-8}$），用于防止分母为零。
> 
> ### 分母的意义：反映二阶信息
> 
> 在梯度下降法中，更新步长通常与梯度的大小成反比。但是，对于某些参数来说，可能会有非常大的梯度波动，这会导致较大的更新步长，进而造成训练不稳定或学习率过大。Adagrad 通过使用累积的梯度平方来调整每个参数的学习率，反映了梯度的“二阶信息”。
> 
> #### 为什么它反映了二阶信息：
> 
> 1. **梯度的大小与学习率的关系**：
>    - ***通过累计历史梯度的平方，Adagrad 实际上在调整每个参数的学习率时，考虑了梯度的变化速率，即梯度的二阶信息。大的梯度会导致较大的平方累积值，从而降低后续的学习率；而小的梯度累积值则会保持学习率较大，促进参数更新。***
>    
> 2. **反映了曲率信息**：
>    - 从二阶导数的角度来看，二阶导数反映了损失函数在某一点的曲率。较大的二阶导数通常意味着该方向上损失函数变化较快，因此学习率应适当降低，以防止步长过大，导致不稳定的更新。
>    - Adagrad 通过累积梯度的平方（等价于某种程度上对梯度变化的积分）来模拟这种效果。如果一个参数的梯度变化较大（即存在较大的梯度），它的累计平方 $G_t$ 会较大，从而减小该参数的更新步长。反之，如果梯度较小，更新步长保持较大。
> 
> 3. **累积历史梯度的平方**：
>    - $G_t = \sum_{i=1}^t \nabla L(\mathbf{w}_i)^2$ 中的每个梯度平方项，随着时间推移会累积，导致对梯度大小的“记忆”。这类似于梯度的二阶信息，表明某个方向上梯度的波动或稳定程度。通过调整每个方向的学习率，Adagrad 可以在梯度较大的方向减小步长，在梯度较小的方向增大步长，从而适应不同的曲率。
> 
> ### 总结：
> Adagrad 的分母 $\sqrt{G_t + \epsilon}$ 通过累积梯度的平方，调整了每个参数的学习率，使得较大梯度的方向得到较小的更新步长，而较小梯度的方向得到较大的更新步长。这种机制间接地反映了梯度的二阶信息（即梯度的变化率或曲率），从而使得每个参数的学习率根据其历史梯度的大小进行自适应调整。这种方法帮助优化过程更稳定，尤其是在训练深度神经网络时。


# 代码
```python showLineNumbers {"adagrad":46-53}
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
%matplotlib inline
import random as random
import numpy as np
import csv

x_data = [ 338.,  333.,  328. , 207. , 226.  , 25. , 179. ,  60. , 208.,  606.]
y_data = [  640.  , 633. ,  619.  , 393.  , 428. ,   27.  , 193.  ,  66. ,  226. , 1591.]

x = np.arange(-200,-100,1) #bias
y = np.arange(-5,5,0.1) #weight
Z =  np.zeros((len(x), len(y)))
X, Y = np.meshgrid(x, y)
for i in range(len(x)):
    for j in range(len(y)):
        b = x[i]
        w = y[j]
        Z[j][i] = 0
        for n in range(len(x_data)):
            Z[j][i] = Z[j][i] +  (y_data[n] - b - w*x_data[n])**2
        Z[j][i] = Z[j][i]/len(x_data)
        
# ydata = b + w * xdata 
b = -120 # initial b
w = -4 # initial w
lr = 1 # learning rate
iteration = 100000

b_lr = 0.0
w_lr = 0.0

# Store initial values for plotting.
b_history = [b]
w_history = [w]

# Iterations
for i in range(iteration):
    
    b_grad = 0.0
    w_grad = 0.0
    for n in range(len(x_data)):        
        b_grad = b_grad  - 2.0*(y_data[n] - b - w*x_data[n])*1.0
        w_grad = w_grad  - 2.0*(y_data[n] - b - w*x_data[n])*x_data[n]
    
    b_lr = b_lr + b_grad**2
    w_lr = w_lr + w_grad**2
    
    # Update parameters.
    b = b - lr/np.sqrt(b_lr) * b_grad 
    w = w - lr/np.sqrt(w_lr) * w_grad
    
    # Store parameters for plotting
    b_history.append(b)
    w_history.append(w)

# plot the figure
plt.contourf(x,y,Z, 50, alpha=0.5, cmap=plt.get_cmap('jet'))
plt.plot([-188.4], [2.67], 'x', ms=12, markeredgewidth=3, color='orange')
plt.plot(b_history, w_history, 'o-', ms=3, lw=1.5, color='black')
plt.xlim(-200,-100)
plt.ylim(-5,5)
plt.xlabel(r'$b$', fontsize=16)
plt.ylabel(r'$w$', fontsize=16)
plt.show()
```

![[output.png]]
