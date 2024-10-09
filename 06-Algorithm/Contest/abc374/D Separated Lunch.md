---
创建时间: 2024-10-06 20:04
难度: 
URL: https://atcoder.jp/contests/abc374/tasks/abc374_c
tags:
  - 搜索
  - 二进制
状态: "#complete"
intro:
---
### 问题描述

随着 KEYENCE 总部的员工越来越多，他们决定将总部的部门分成两组，并错开他们的午餐时间。

KEYENCE总部有 $N$ 个部门，第 $i$ 个部门的人数为 $K_i$ $(1\leq i\leq N)$。

在将每个部门分配给组 $A$ 或组 $B$ 时，要求两个组的午餐时间同时进行，并确保组 $A$ 和组 $B$ 的午餐时间不重叠，找到在同一时间吃午餐的人数的最大值的最小可能值。换句话说，找出以下两者中的较大者的最小可能值：分配给组 $A$ 的部门的总人数，以及分配给组 $B$ 的部门的总人数。

### 约束条件

-   $2 \leq N \leq 20$
-   $1 \leq K_i \leq 10^8$
-   所有输入值均为整数。



### 样例

```docker title="input"
5
2 3 5 10 12
```

```docker title="output"
17
```


## 思路

我的思路是使用搜索，遍历所有的可能性，然后得到最小可能性的最大值。

```ad-sc
title: 搜索代码
collapse: true
~~~cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    int n;
    cin >> n;

    vector<int> v(n);
    for (int i = 0; i < n; i++) cin >> v[i];

    long long minn = accumulate(v.begin(), v.end(), 0);

    // 修正了递归调用方式
    auto dfs = [&](auto &&self, int k, long long a, long long b) {
        if (k == n) {
            minn = min(minn, max(a, b));
            return;
        }

        self(self, k + 1, a + v[k], b);
        self(self, k + 1, a, b + v[k]);
    };

    dfs(dfs, 0, 0, 0);
    cout << minn;

    return 0;
}
~~~
```


```cpp showLineNumbers {"二进制递推":20-29}
#include <bits/stdc++.h>

using i64 = long long;
using u64 = unsigned long long;
using u32 = unsigned;

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    
    int N;
    std::cin >> N;
    
    std::vector<int> K(N);
    for (int i = 0; i < N; i++) {
        std::cin >> K[i];
    }
    
    int tot = std::accumulate(K.begin(), K.end(), 0);
    
    int ans = tot;
    std::vector<int> sum(1 << N);
    for (int s = 0; s < (1 << N); s++) {
        if (s > 0) {
            int u = __builtin_ctz(s);
            sum[s] = K[u] + sum[s ^ (1 << u)];
        }
        ans = std::min(ans, std::max(sum[s], tot - sum[s]));
    }
    std::cout << ans << "\n";
    
    return 0;
}
```


