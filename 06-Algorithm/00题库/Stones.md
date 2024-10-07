---
创建时间: 2024-09-24 15:41
难度: 普及/提高-
URL: https://atcoder.jp/contests/dp/tasks/dp_k
tags:
  - 动态规划/博弈DP
  - 博弈论
intro:
---
### 问题陈述

有一个集合 $A = \{ a_1, a_2, \ldots, a_N \}$，由 $N$ 个正整数组成。太郎和次郎将互相进行以下游戏。

最开始，我们有一堆由 $K$ 块石头构成的堆。两个玩家交替进行以下操作，从太郎开始：
-   选择集合 $A$ 中的一个元素 $x$，并从堆中移除正好 $x$ 块石头。
当一名玩家无法进行操作时，他将输掉比赛。假设两名玩家都以最优策略进行游戏，确定胜者。

### 约束条件

-   输入中的所有值都是整数。
-   $1 \leq N \leq 100$
-   $1 \leq K \leq 10^5$
-   $1 \leq a_1 < a_2 < \cdots <a_N \leq K$ 

### Input
Input is given from Standard Input in the following format:
$N$ $K$
$a_1$ $a_2$ $\ldots$ $a_N$
### Output

If Taro will win, print `First` i; if Jiro will win, print `Second`.
## 思路

在动态规划算法中，状态转移可以是由 $A \gets B$，也可以是 $B\to A$。
我们这样设计状态，$f[i]$ 表示还剩 $i$ 个石头时的先取一方的胜负（$0$ 代表乙方必赢，$1$ 代表甲方必赢），显而易见的 $f[0]=0$，第一个玩家无法进行任何操作。对于 $A[j]$ 来说，$f[A[j]]=1$ 恒成立。
那么对于 $f[i]$ 来说，$f[i]$ 的值取决于 $f[i-A[j]]$ 的值
- 如果 $f[i-A[j]]=0$ ，意味着在 $i-A[j]$ 时先取的必败，**此时我们可以让甲先取 $A[j]$，这样乙方就变成了 $i-A[j]$ 的先取者，必败。**
- 如果 $f[i-A[j]]  =1$ 恒成立，意味着无论甲先取什么，乙方都可以必胜

```cpp showLineNumbers {10-16}
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k;
    cin >> n >> k;
    vector<int> a(n + 1, 0);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    vector<int> f(k + 1, 0);
    for (int i = 1; i <= k; i++) {
        for (int j = 1; j <= n and i >= a[j]; j++) {
            if (f[i - a[j]] == 0) {
                f[i] = 1;
            }
        }
    }
    cout << (f[k] ? "First" : "Second");
    return 0;
}
```
