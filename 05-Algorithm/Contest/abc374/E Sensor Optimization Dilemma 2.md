---
创建时间: 2024-10-07 19:36
难度: 普及+/提高
URL: https://atcoder.jp/contests/abc374/tasks/abc374_e
tags:
  - 二分查找
  - 数学
状态: "#inprogress"
intro:
---
### 问题描述

某种产品的制造需要 $N$ 个过程，编号为 $1, 2, \dots, N$。

对于每个过程 $i$，可供购买的机器有两种类型：$S_i$ 和 $T_i$。

- 机器 $S_i$：每台每天可以处理 $A_i$ 个产品，成本为每台 $P_i$ 日元。
- 机器 $T_i$：每台每天可以处理 $B_i$ 个产品，成本为每台 $Q_i$ 日元。

你可以购买任意数量的每种机器，甚至可以不购买。

假设过程 $i$ 引入机器后每天可以处理 $W_i$ 个产品。  
在这里，我们将生产能力定义为 $W$ 的最小值，即 $\displaystyle \min^{N}_{i=1} W_i$。
给定总预算 $X$ 日元，找出可以实现的最大生产能力。
### 约束条件

- 所有输入值均为整数。
- $1 \le N \le 100$
- $1 \le A_i, B_i \le 100$
- $1 \le P_i, Q_i, X \le 10^7$

## 思路

这是一个二元问题，通过常识来看，我们肯定是优先选择单价小的机器，也就是如果 $\dfrac{P[i]}{A[i]} < \dfrac{Q[i]}{B[i]}$ 我们会优先选择机器 $S[i]$。
值得注意的是，假设我们的目标产量为 $m$，如果 $A[i] \mid m$，那么我们可以贪心的都选择 $S[i]$ 机器。但如果没有那么恰好，全都选择 $S[i]$ 得到的产量会落在 $[m + 1, m + A[i] - 1]$，**此时就不一定得到是最优解了**，因为我们可以通过少选择 $S[i]$，多选择 $Q[i]$，来减少产量并减少成本。
那么我们应该选择多少 $T[i]$ 呢，通过分析可以知道，当 $m=\mathrm{lcm}(A[i], B[i])=\dfrac{A[i]\cdot B[i]}{\gcd(A[i],B[i])}$ 时，$A[i] \mid m$ 和 $B[i] \mid m$ 恒成立，但因为 $P[i] < Q[i]$ 我们应该都选择 $S[i]$。因此对 $T[i]$ 我们只需枚举到 $\dfrac{A[i]}{\gcd(A[i],B[i])}$ 即可，如果更多的话就可以转换到 $S[i]$ ，这样更省钱

```cpp showLineNumbers
#include <bits/stdc++.h>

using i64 = long long;

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n, x;

    std::cin >> n >> x;
    std::vector<int> A(n), P(n), B(n), Q(n);
    for (int i = 0; i < n; i++) {
        std::cin >> A[i] >> P[i] >> B[i] >> Q[i];
        if (A[i] * Q[i] < B[i] * P[i]) {
            std::swap(A[i], B[i]);
            std::swap(P[i], Q[i]);
        }
    }

    auto check = [&](int m) {
        // 每个过程至少达到m的生产能力
        i64 tot = 0;
        for (int i = 0; i < n; i++) {
            i64 ans = 1E18;
            for (int j = 0; j < A[i] / std::gcd(A[i], B[i]); j++) {
                i64 v = j * Q[i];
                // 用A填补的价格
                if (m - j * B[i] > 0)
                    v += (1LL * m - j * B[i] + A[i] - 1) / A[i] * P[i];
                ans = std::min({ans, v});
            }
            tot += ans;
        }
        return tot <= x;
    };

    int l = 0, r = 1E9;
    while (l < r) {
        int m = l + (r - l + 1) / 2;
        if (check(m)) {
            l = m;
        } else {
            r = m - 1;
        }
    }

    std::cout << l;

    return 0;
}
```