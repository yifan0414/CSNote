---
创建时间: 2026-04-28 02:47
难度: NOI/NOI+/CTSC
URL:
tags:
状态: "#inprogress"
intro:
---
# P 16330 Just Because!

## 题目背景

> 瑛太把刚才拍的樱花树的照片发了上去。写到“大学很普通”。
> 
> ——看起来就是这样的感觉啊。这是来自她的回答，很疑惑，“看什么”，这到底是怎么回事。
> 
> 然后 line 画面上发来一张照片。像是在哪里见过的景色，在散落了一半的樱花树下有一个驼背男大学生的后背。瑛太的背包，瑛太的衣服，照片里的是瑛太本人。
>
>怀着惊讶和确信的心情，慢慢地回头看。她在后面，十步左右的距离，恶作剧似地笑着。
>
> “我并不是为了追求泉来这的，是因为这里的教育系比较有名。”
> 她开心地告诉了我不知道的事情，有很多想说的话。
> 
>我有很多想说的话，想听的事情也很多。但在她面前，瑛太想要传达的就只剩下，那天没有说出口的话，那天最想传达的想法...
>
> “夏目，我喜欢你。”
> 
> 在林荫大道上刮起大风，稍强的风把樱花吹得飘落下来，落在两人身上。
> 
> “我也是，泉。”
> 
> 在樱吹雪的风中，她害羞地笑了起来。

## 题目描述

你有 $n$ 棵树，第 $i$ 棵树位于位置 $p_i$，高度为 $h_i$，保证 $p$ 单调递增。

给定 $q$ 次询问。对于第 $i$ 次询问，只保留 $[l_i,r_i]$ 子区间，你要选择最多的树，使得存在一种砍倒方式使得每棵树都不碰到另一棵树的树桩。

形式化地，设 $S = \{s_1, s_2, \dots, s_k\} \subseteq \{l_i, l_i+1, \dots, r_i\}$ 且 $s_1 < s_2 < \cdots < s_k$。  

要求对任意 $1 < j < k$，都有 $p_{s_j} + h_{s_j} < p_{s_{j+1}} \lor p_{s_j} - h_{s_j} > p_{s_{j-1}} $。求 $\max k$。

询问之间互相独立。

## 输入格式

第一行两个正整数 $n,q$。

第二行一个长度为 $n$ 的严格递增正整数序列 $p_i$。

第三行 $n$ 个正整数表示 $h_i$。

接下来 $q$ 行，每行两个正整数 $l_i,r_i$ 表示询问的区间。

## 输出格式

共 $q$ 行，每行一个整数表示每个询问的答案。

## 输入输出样例 #1

### 输入 #1

```
5 3
3 5 8 9 10 
2 7 5 9 9 
4 5
1 5
1 4
```

### 输出 #1

```
2
2
2

```

## 输入输出样例 #2

### 输入 #2

```
17 16
7 8 15 20 24 27 30 37 40 44 48 52 56 60 64 68 72 
5 1 1 4 1 2 1 2 3 2 2 5 7 4 7 6 7 
2 12
10 12
4 14
4 8
3 3
3 16
3 13
1 16
3 15
15 16
1 15
3 16
2 14
5 16
4 17
4 14

```

### 输出 #2

```
11
3
10
5
1
12
10
14
12
2
14
12
12
10
12
10

```

## 说明/提示

**【数据范围】**

**本题使用子任务捆绑**。

对于所有测试数据，$1\le n,q \le 5\times 10^5$，$1\le p_i,h_i \le 10^9$，$l_i\le r_i$。对于所有 $1\le i< n$，保证 $p_i < p_{i+1}$。

|子任务编号| $n\le$ | $q \le$ |特殊性质|分值|
|:-:|:-:|:-:|:-:|:-:|
| $1$ | $18$ | $18$ |无| $10$ |
| $2$ | $300$ | $300$ |无| $20$ |
| $3$ | $3000$ | $3000$ |无| $20$ |
| $4$ | $10^5$ | $10^5$ |有| $10$ |
| $5$ | $5\times 10^5$ | $5 \times 10^5$ |无| $40$ |

特殊性质：对于所有 $1\le i\le q$，保证 $l_i=1$。

可以，下面我把上一版完整改成只用 `$...$` 的格式。

---

## 题意转化

设一次询问只保留区间 $[l,r]$。

如果我们选出的树下标是 $s_1<s_2<\cdots<s_k$，那么题目要求对每个中间位置 $1<j<k$，都有：

- 要么第 $s_j$ 棵树向右倒，不碰到下一棵，即 $p_{s_j}+h_{s_j}<p_{s_{j+1}}$
- 要么它向左倒，不碰到前一棵，即 $p_{s_j}-h_{s_j}>p_{s_{j-1}}$

也就是说，相邻选中的两棵树只会影响中间那棵树是否能“朝某个方向安全倒下”。

---

## 关键性质 1：最优解一定可以包含两端

对于询问 $[l,r]$，设某个最优方案选了：

$s_1<s_2<\cdots<s_k$

如果 $s_1\neq l$，把第一棵直接换成 $l$：

- 新的第一棵没有左邻居，肯定合法
- 原来的 $s_2$ 的前驱变得更靠左了，所以它若想向左倒只会更容易

所以不会变差。

同理，如果 $s_k\neq r$，把最后一棵换成 $r$ 也不会变差。

所以答案等价于：

> 从 $l$ 开始选，尽量多选树，并且最后一棵的位置不超过 $r$。

因为最后总可以把最后一棵替换成 $r$。

---

## 关键性质 2：只需要两个辅助数组

定义：

- $A_i$：满足 $p_j<p_i-h_i$ 的最大下标 $j$
- $B_i$：满足 $p_j>p_i+h_i$ 的最小下标 $j$

那么如果当前选中相邻两棵是 $i<j$，有：

- 若 $i$ 向右倒，则需要 $j\ge B_i$
- 若 $j$ 向左倒，则需要 $i\le A_j$

这两个条件正好就是后面转移的基础。

---

## 状态压缩

固定左端点 $l$。

我们考虑“已经选了若干棵树以后，最后一棵可能落在哪”。

把“最后一棵的倒向”分成两类：

- 最后一棵是“向左倒”的结尾
- 最后一棵是“向右倒”的结尾

然后只保留最有用的信息：

- $L$：当前能作为“向左倒结尾”的最小下标
- $R$：当前能作为“向右倒结尾”的最小下标

初始时只选了第 $l$ 棵树：

- 它作为左倒结尾一定可行
- 右倒结尾不需要保留

所以初始状态是 $(L,R)=(l,\infty)$，其中 $\infty=n+1$。

---

## 一步转移

先定义两个中间量：

- $LL_i=\min\{j>i\mid A_j\ge i\}$
- $RL_i=\min\{j\ge B_i\mid A_j\ge i\}$

再定义两个后缀最小值：

- $sufB_i=\min_{x\ge i} B_x$
- $sufRL_i=\min_{x\ge i} RL_x$

---

### 转移到新的左倒结尾

如果当前状态是 $(L,R)$，下一棵作为左倒结尾有两种来源：

1. 从当前左倒结尾 $L$ 转移  
   需要最小的 $j>L$，并满足 $A_j\ge L$，这就是 $LL_L$

2. 从当前右倒结尾转移  
   若当前最后一棵是某个 $x\ge R$，那么下一棵 $j$ 要满足：
   - $j\ge B_x$
   - $A_j\ge x$

   最小值就是 $RL_x$，对所有 $x\ge R$ 取最小，就是 $sufRL_R$

所以：

$L'=\min(LL_L,\ sufRL_R)$

---

### 转移到新的右倒结尾

同样分两种来源：

1. 从左倒结尾 $L$ 转移  
   下一棵只要在它右边即可，所以最小是 $L+1$

2. 从右倒结尾转移  
   当前最后一棵是某个 $x\ge R$，下一棵只要满足 $j\ge B_x$  
   对所有 $x\ge R$ 取最小，就是 $sufB_R$

所以：

$R'=\min(L+1,\ sufB_R)$

---

## 得到一个二元自动机

一步转移就是：

- $L'=\min(LL_L,\ sufRL_R)$
- $R'=\min(L+1,\ sufB_R)$

它只依赖当前的 $(L,R)$，所以可以直接倍增。

---

## 倍增设计

设当前状态是 $(x,y)$。

定义四个数组 `f00,f01,f10,f11`，表示走 $2^k$ 步后的转移：

- 新的左状态是 `min(f00[k][x], f01[k][y])`
- 新的右状态是 `min(f10[k][x], f11[k][y])`

---

### 初值 $k=0$

一步转移对应：

- `f00[0][i] = LL_i`
- `f01[0][i] = sufRL_i`
- `f10[0][i] = i+1`
- `f11[0][i] = sufB_i`

---

### 倍增合并

连续走两段 $2^k$，直接代入即可：

```cpp
f00[k + 1][i] = min(f00[k][f00[k][i]], f01[k][f10[k][i]]);
f01[k + 1][i] = min(f00[k][f01[k][i]], f01[k][f11[k][i]]);
f10[k + 1][i] = min(f10[k][f00[k][i]], f11[k][f10[k][i]]);
f11[k + 1][i] = min(f10[k][f01[k][i]], f11[k][f11[k][i]]);
```

---

## 如何回答询问

对于询问 $[l,r]$：

- 初始状态 $(x,y)=(l,\infty)$
- 当前已经选了 `ans=1` 棵树
- 从大到小枚举 $k$
- 试着跳 $2^k$ 步，得到 `(nx, ny)`

如果 `min(nx, ny) <= r`，说明还能在区间内继续选这么多棵，于是接受这次跳跃：

- `x = nx`
- `y = ny`
- `ans += (1 << k)`

最后 `ans` 就是答案。

---

## 预处理怎么做

### 1. 预处理 $A_i,B_i$

因为 $p_i$ 单调递增，直接二分：

- $A_i$ 用 `lower_bound`
- $B_i$ 用 `upper_bound`

复杂度 $O(n\log n)$。

---

### 2. 预处理 $LL_i$

我们按 $A_j$ 把所有 $j$ 挂到桶里。

从右往左扫，当扫到 $i$ 时，所有满足 $A_j\ge i$ 的点都已经“加入候选集”，维护这些点的最小值即可。

复杂度 $O(n)$。

---

### 3. 预处理 $RL_i$

同样从右往左扫，并把所有满足 $A_j\ge i$ 的点 $j$ 插入线段树。

此时查询区间 $[B_i,n]$ 上的最小值，就是 $RL_i$。

复杂度 $O(n\log n)$。

---

## 总复杂度

- 预处理：$O(n\log n)$
- 建倍增表：$O(n\log n)$
- 每次询问：$O(\log n)$

总复杂度：$O((n+q)\log n)$

可以通过 $n,q\le 5\times 10^5$。

---

# C++ 代码

```cpp
#include <iostream>
#include <algorithm>
#include <cstring>
using namespace std;

static const int MAXN = 500000 + 5;
static const int LG = 19; // 2^19 = 524288 > 5e5

int n, q;
int p[MAXN], h[MAXN];
int A_[MAXN], B_[MAXN];

int head[MAXN], nxtEdge[MAXN];
int nxtLL[MAXN], nxtRL[MAXN], sufB[MAXN], sufRL[MAXN];

int baseSize, seg[1 << 21];

int f00[LG][MAXN], f01[LG][MAXN], f10[LG][MAXN], f11[LG][MAXN];

void seg_init(int inf) {
    baseSize = 1;
    while (baseSize < n) baseSize <<= 1;
    fill(seg, seg + (baseSize << 1), inf);
}

void seg_update(int pos, int val) {
    int x = pos + baseSize - 1;
    seg[x] = val;
    x >>= 1;
    while (x) {
        seg[x] = min(seg[x << 1], seg[x << 1 | 1]);
        x >>= 1;
    }
}

int seg_query(int l, int r, int inf) {
    if (l > r) return inf;
    int res = inf;
    int L = l + baseSize - 1;
    int R = r + baseSize - 1;
    while (L <= R) {
        if (L & 1) res = min(res, seg[L++]);
        if (!(R & 1)) res = min(res, seg[R--]);
        L >>= 1;
        R >>= 1;
    }
    return res;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cin >> n >> q;
    const int INF = n + 1;

    for (int i = 1; i <= n; ++i) cin >> p[i];
    for (int i = 1; i <= n; ++i) cin >> h[i];

    fill(head, head + n + 1, 0);

    for (int i = 1; i <= n; ++i) {
        A_[i] = int(lower_bound(p + 1, p + n + 1, p[i] - h[i]) - p) - 1;
        B_[i] = int(upper_bound(p + 1, p + n + 1, p[i] + h[i]) - p);

        nxtEdge[i] = head[A_[i]];
        head[A_[i]] = i;
    }

    // nxtLL[i] = min { j > i | A[j] >= i }
    int cur = INF;
    for (int i = n; i >= 1; --i) {
        for (int e = head[i]; e; e = nxtEdge[e]) cur = min(cur, e);
        nxtLL[i] = cur;
    }
    nxtLL[INF] = INF;

    // nxtRL[i] = min { j >= B[i] | A[j] >= i }
    seg_init(INF);
    for (int i = n; i >= 1; --i) {
        for (int e = head[i]; e; e = nxtEdge[e]) seg_update(e, e);
        nxtRL[i] = seg_query(B_[i], n, INF);
    }
    nxtRL[INF] = INF;

    // suffix minima
    sufB[INF] = sufRL[INF] = INF;
    for (int i = n; i >= 1; --i) {
        sufB[i] = min(B_[i], sufB[i + 1]);
        sufRL[i] = min(nxtRL[i], sufRL[i + 1]);
    }

    // 2^0 transitions
    for (int i = 1; i <= INF; ++i) {
        f00[0][i] = (i <= n ? nxtLL[i] : INF);
        f01[0][i] = sufRL[i];
        f10[0][i] = (i < n ? i + 1 : INF);
        f11[0][i] = sufB[i];
    }

    // doubling
    for (int k = 0; k + 1 < LG; ++k) {
        for (int i = 1; i <= INF; ++i) {
            f00[k + 1][i] = min(f00[k][f00[k][i]], f01[k][f10[k][i]]);
            f01[k + 1][i] = min(f00[k][f01[k][i]], f01[k][f11[k][i]]);
            f10[k + 1][i] = min(f10[k][f00[k][i]], f11[k][f10[k][i]]);
            f11[k + 1][i] = min(f10[k][f01[k][i]], f11[k][f11[k][i]]);
        }
    }

    while (q--) {
        int l, r;
        cin >> l >> r;

        int x = l, y = INF;
        int ans = 1;

        for (int k = LG - 1; k >= 0; --k) {
            int nx = min(f00[k][x], f01[k][y]);
            int ny = min(f10[k][x], f11[k][y]);
            if (min(nx, ny) <= r) {
                x = nx;
                y = ny;
                ans += (1 << k);
            }
        }

        cout << ans << '\n';
    }

    return 0;
}
```

如果你愿意，我还可以继续给你压缩成一版 **ICPC/CCPC 风格赛场题解**，只保留最核心的 5 个结论，方便你赛时复盘。