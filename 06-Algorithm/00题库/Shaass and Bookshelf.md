---
创建时间: 2024-09-18 17:16
难度: NOI/NOI+/CTSC
URL: https://www.luogu.com.cn/problem/CF294B
tags:
  - 动态规划/背包DP
intro: 这个的最优做法非常难理解，[[2742. 给墙壁刷油漆]]
---
# 题目描述
Shaass 拥有 $n$ 本书。他想为他的所有书制作一个书架，并想让书架的长宽尽量小。第 $i$ 本书的厚度是 $t[i]$，且这本书的纸张宽度是 $w[i]$。书的厚度是 $1$ 或 $2$，所有书都有同样的高度（即书架的高是均匀的）。

Shaass 以以下的方式摆放这些书籍。

1.他选择了一些书并竖直摆放它们。

2.他将剩余的书籍水平纺织于竖直的书上面。
水平放置的书的宽度和不能多于竖直放置的书的总厚度。图中描绘了书籍的样本排列。
![image.png](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/img/20240919140225.png)

帮助 Shaass 找到可以达到的书架长度最小值。

# 输入格式：

输入的第一行包含一个 `int` 型的整数 $n (1 \leqslant n \leqslant 100)$。
下面的 $n$ 行分别为 $v[i]$和 $w[i]$，对应了书的长度和宽度（即书籍竖直放置与水平放置所占的空间）。
$(1 \leqslant t[i]\leqslant 2,1\leqslant w[i]\leqslant 100)$
# 输出格式：

一个整数，为可以达到的最小的长度。

## 样例 #1

### 样例输入 #1

```
5
1 12
1 3
2 15
2 5
2 1
```

### 样例输出 #1

```
5
```

## 样例 #2

### 样例输入 #2

```
3
1 10
2 1
2 4
```

### 样例输出 #2

```
3
```

## 代码

### 最优解

```cpp
#include <bits/stdc++.h>
using namespace std;
long long a, b, n, f[1000], v[1000], w[1000], sum;
int main() {
    cin >> n;
    for (int i = 1; i <= n; i++) {
        cin >> a >> b;
        w[i] = a + b;
        v[i] = a;
        sum += a;
    }
    for (int i = 1; i <= n; i++) {
        for (int j = sum; j >= w[i]; j--) {
            f[j] = max(f[j], f[j - w[i]] + v[i]);
        }
    }
    cout << sum - f[sum];
}
```


## 比较好理解的解法

```cpp showLineNumbers {"状态转移":23-40}
#include <bits/stdc++.h>
using namespace std;

// 怎么表示状态
// 第i本书有两种状态：横放，竖放
// 横放的书的宽度和 <= 竖放书的厚度和
// 求最小的厚度

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    
    int n;
    cin >> n;
    vector<int> v(n + 1), w(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> v[i] >> w[i];

    int thick = accumulate(v.begin(), v.end(), 0);
    int width = accumulate(w.begin(), w.end(), 0);
    vector<vector<vector<int>>> f(
        2, vector<vector<int>>(thick + 1, vector<int>(width + 1, 0)));

    f[0][0][0] = 1;
    for (int i = 1; i <= n; i++) {
        for (int j = 0; j <= thick; j++) {
            for (int k = 0; k <= width; k++) {
                if (j >= v[i]) {
                    f[i % 2][j][k] =
                        f[i % 2][j][k] | f[(i - 1) % 2][j - v[i]][k];
                }
                if (k >= w[i]) {
                    f[i % 2][j][k] =
                        f[i % 2][j][k] | f[(i - 1) % 2][j][k - w[i]];
                }
            }
        }
        vector<vector<int>> t(thick + 1, vector<int>(width + 1, 0));
        f[(i - 1) % 2] = t;
    }

    for (int i = 0; i <= thick; i++) {
        for (int j = 0; j <= i; j++) {
            if (f[n % 2][i][j]) {
                cout << i << endl;
                return 0;
            }
        }
    }
    return 0;
}

```