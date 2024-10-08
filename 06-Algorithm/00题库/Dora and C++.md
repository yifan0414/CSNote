---
创建时间: 2024-09-23 22:01
难度: ⭐️⭐️⭐️
URL: https://codeforces.com/problemset/problem/2007/C
tags:
  - 数学
intro:
---

## 题目
Dora 刚刚学习了编程语言 C++！

然而，她完全误解了C++的含义。她将其视为对一个包含 $n$ 个元素的数组 $c$ 进行两种加法操作。Dora有两个整数 $a$ 和 $b$。在一次操作中，她可以选择以下任一项进行操作：

- 选择一个整数 $i$，使得 $1 \leq i \leq n$，并将 $c_i$ 增加 $a$。
- 选择一个整数 $i$，使得 $1 \leq i \leq n$，并将 $c_i$ 增加 $b$。

注意，$a$ 和 $b$ 是**常量**，它们可以是相同的。

我们定义数组 $d$ 的范围为 $\max(d_i) - \min(d_i)$。例如，数组 $[1, 2, 3, 4]$ 的范围是 $4 - 1 = 3$，数组 $[5, 2, 8, 2, 2, 1]$ 的范围是 $8 - 1 = 7$，而数组 $[3, 3, 3]$ 的范围是 $3 - 3 = 0$。

在进行任意次数的操作（可能为 $0$）后，Dora 计算新的数组的范围。你需要帮助 Dora 最小化这个值，但由于 Dora 喜欢自己探索，你只需要告诉她最小化后的值。

**输入**
每个测试由多个测试案例组成。第一行包含一个整数 $t$ ($1 \leq t \leq 10^4$) — 测试案例的数量。测试案例的描述如下。

每个测试案例的第一行包含三个整数 $n$, $a$, 和 $b$ ($1 \leq n \leq 10^5$, $1 \leq a, b \leq 10^9$) — 数组 $c$ 的长度和常数值。

每个测试案例的第二行包含 $n$ 个整数 $c_1, c_2, \ldots, c_n$ ($1 \leq c_i \leq 10^9$) — 数组 $c$ 的初始元素。

可以保证所有测试案例中 $n$ 的总和不超过 $10^5$。

**输出**
对于每个测试用例，输出一个整数 — 在进行任意次数操作后，数组的最小可能范围。

```docker showLineNumbers title="INPUT"
10
4 5 5
1 3 4 4
4 2 3
1 3 4 6
4 7 7
1 1 2 6
3 15 9
1 9 5
3 18 12
1 4 5
7 27 36
33 13 23 12 35 24 41
10 6 9
15 5 6 9 8 2 12 15 3 8
2 1 1000000000
1 1000000000
6 336718728 709848696
552806726 474775724 15129785 371139304 178408298 13106071
6 335734893 671469786
138885253 70095920 456876775 9345665 214704906 375508929
```

```docker showLineNumbers title="OUTPUT"
3
0
3
2
3
5
1
0
17
205359241
```

**注意**

在第一个测试案例中，我们可以将 $c_1 = 1$ 增加 $a = 5$。数组 $c$ 将变为 $[6, 3, 4, 4]$，范围为 $3$。请注意，达到答案的方式不止一种。

在第二个测试案例中，我们可以将 $c_1 = 1$ 增加 $a = 2$，然后将 $c_1 = 3$ 增加 $b = 3$。我们也可以将 $c_2 = 3$ 增加 $b = 3$，并将 $c_3 = 4$ 增加 $a = 2$。数组 $c$ 将变为 $[6, 6, 6, 6]$，范围为 $0$。
## 代码

