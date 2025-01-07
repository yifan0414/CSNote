---
创建时间: 2024-10-13 17:52
难度: 
URL: 
tags: 
状态: "#inprogress"
intro:
---
### 问题陈述

### 问题陈述

给定一个由大写英文字母组成的字符串 $S$。

找到满足以下两个条件的整数三元组 $(i, j, k)$ 的数量：

-   $1 \leq i < j < k \leq |S|$
-   由 $S_i$、$S_j$ 和 $S_k$ 按此顺序连接形成的长度为 $3$ 的字符串是一个回文。

这里，$|S|$ 表示字符串 $S$ 的长度，$S_x$ 表示 $S$ 的第 $x$ 个字符。

### 约束条件

-   $S$ 是一个长度在 $1$ 到 $2 \times 10^5$ 之间（含）的字符串，由大写英文字母组成。


## Solution 1
```cpp showLineNumbers
#include <bits/stdc++.h>
using namespace std;

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    string s;
    cin >> s;
    int n = s.size();

    vector v(26, vector<int>(n + 2, 0));

    for (int i = 1; i <= n; i++) {
        for (int j = 0; j < 26; j++) {
            if (s[i - 1] - 'A' == j) {
                v[j][i] = v[j][i - 1] + 1;
            } else {
                v[j][i] = v[j][i - 1];
            }
        }
    }

    long long ans = 0;

    for (int i = 1; i <= n; i++) {
        char t = s[i - 1];
        for (int j = 0; j < 26; j++) {
            // if (v[j][i - 1] * (v[j][n] - v[j][i]) != 0) {
            //     cout << i << " " << (char)('A' + j) << " ";
            //     cout << v[j][i - 1]  << " " <<  (v[j][n] - v[j][i]) << "\n";
            // }
            ans += (long long) v[j][i - 1] * (v[j][n] - v[j][i]);
        }
    }

    cout << ans << "\n";

    return 0;
}
```


## Solution 2

这是一个算法问题，请你将其翻译成中文，行内公式用$包围起来。

官方

[D - ABA](/contests/abc375/tasks/abc375_d) 编辑由 [en\_translator](/users/en_translator)
----------------------------------------------------------------------------------------------

* * *

设 $N \coloneqq |S|$，$\sigma$ 为可能出现的字符数。在我们的题目中，$\sigma = 26$。

将 $S_i$、$S_j$ 和 $S_k$ 按顺序连接得到的字符串是回文，当且仅当 $S_i = S_k$。

经过这样的重述，有多种可能的方法。这里我们介绍其中两种。

(1) 关注 $j$

让我们为每个固定的 $j$ 找出计数。$(i, k)$ 的数量是满足 $S_i = S_k$ 且 $1 \leq i < j$，$j < k \leq N$ 的对数。

当我们固定 $c \coloneqq S_i$（注意我们固定的是字符，而不是索引，字符仅有 $26$ 种），我们想要的是满足 $S_i = c$ 的 $1 \leq i < j$ 的数量，以及满足 $S_k = c$ 的 $j < k \leq N$ 的数量。

通过累计和的方式，我们可以先手动计算 $1, 2, \ldots , i$ 中 $c$ 的出现次数，这样所需的计数可以在常数时间内获得；因此，总的处理时间为 $O(\sigma N)$。

还可以利用这样一个事实：所需的计数，即满足 $S_i = c$ 的 $1 \leq i < j$ 和满足 $S_k = c$ 的 $j < k \leq N$ 的数量，对于 $j$ 和 $j + 1$ 是几乎相同的。通过应用适当的差分更新，复杂度可以从 $O(\sigma N)$ 优化到 $O(N)$ 时间。

(2) 关注 $i$ 和 $k$

如果 $S_i = S_k$，那么任何 $j$ 满足 $i < j < k$ 都是适用的；选择的数量为 $k - i - 1$。因此，答案是所有满足 $S_i = S_k$ 的对 $(i, k)$ 上 $k - i - 1$ 的总和。

如果我们定义 $X_c$ 为满足 $S_i = c$ 的索引 $i$ 的序列，答案是对于 $c =$ `A`、`B`、$\ldots$、`Z`，$\displaystyle\sum_{s = 1}^{|X_c|}\displaystyle\sum_{t = s + 1}^{|X_c|} (X_{c, t} - X_{c, s} - 1)$ 的总和。
通过考虑每个 $X_{c, s}$ 的贡献，或者计算累计和 $\displaystyle\sum_{s = 1}^{s'}X_{c,s}$，可以在 $O(|X_c|)$ 时间内评估。因此，通过对每个 $c =$ `A`、`B`、$\ldots$、`Z` 应用这种方法，答案可以在总共 $O(N)$ 时间内找到。

示例代码 (1)

示例代码 (2)

发布：大约 19 小时前  
最后更新：大约 19 小时前