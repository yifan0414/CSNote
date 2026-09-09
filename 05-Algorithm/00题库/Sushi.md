---
创建时间: 2024-09-24 14:46
难度: 普及+/提高
URL: https://www.luogu.com.cn/problem/AT_dp_j
tags:
  - 动态规划/期望DP
intro:
---
### 问题陈述

有 $N$ 道菜，编号为 $1, 2, \ldots, N$。最初，对于每个 $i$ ($1 \leq i \leq N$)，菜肴 $i$ 上有 $a_i$ ($1 \leq a_i \leq 3$) 块寿司。

太郎将重复执行以下操作，直到所有的寿司都被吃掉：

-   摇一个显示 $1, 2, \ldots, N$ 的骰子，结果为 $i$。如果菜肴 $i$ 上有寿司，则吃掉其中一块；如果没有，则不做任何操作。

找出在所有寿司被吃掉之前，操作执行的期望次数。

### 约束条件

-   输入中的所有值为整数。
-   $1 \leq N \leq 300$
-   $1 \leq a_i \leq 3$

### 样例

```docker title=input
3
1 1 1
```

```docker title=output
5.5
```

## 思路

如何表示状态？
由于骰子的随机性，也就是摇到某个数字 $i$ 的概率相同，因此这 $n$ 个盘子可以随机排列。
使用 $f[i][j][k]$ 表示寿司为 $1$ 的盘子数为 $i$，寿司为 $2$ 的盘子数为 $j$，寿司为 $3$ 的盘子数为 $k$ 的期望次数。
我们可以找到 $f[i][j][k]$ 是由谁转移而来的
$$
f[i][j][k] = \frac{n-i-j-k}{n}f[i][j][k] + \frac{i}{n}f[i-1][j][k]+ \frac{j}{n}f[i+1][j-1][k] + \frac{k}{n}f[i][j+1][k-1]+1
$$
移项可得
$$
f[i][j][k] = \frac{n}{i+j+k} + \frac{i}{i+j+k}f[i-1][j][k]+\frac{j}{i+j+k}f[i+1][j-1][k]+\frac{k}{i+j+k}f[i][j+1][k-1]
$$

因为要保证状态的无后效性，我们要从 $k,j,i$ 枚举

## 代码
```cpp
#include <bits/stdc++.h>
using namespace std;

int n;
double f[303][303][303];

int main() {
    vector<int> num(4, 0);
    int n;
    cin >> n;
    for (int i = 1; i <= n; i++) {
        int a;
        cin >> a;
        num[a]++;
    }

    for (int k = 0; k <= n; k++) {
        for (int j = 0; j <= n; j++) {
            for (int i = 0; i <= n; i++) {
                if (i or j or k) {
                    if (i)
                        f[i][j][k] += f[i - 1][j][k] * i / (i + j + k);
                    if (j)
                        f[i][j][k] += f[i + 1][j - 1][k] * j / (i + j + k);
                    if (k)
                        f[i][j][k] += f[i][j + 1][k - 1] * k / (i + j + k);
                    f[i][j][k] += (double)n / (i + j + k);
                }
            }
        }
    }
    cout << setprecision(15);
    cout << f[num[1]][num[2]][num[3]];

    return 0;
}
```