---
创建时间: 2024-09-30 21:02
难度: 普及/提高-
URL: https://www.luogu.com.cn/problem/P2895
tags:
  - BFS
状态: "#inprogress"
intro:
---
## Description
贝茜听说一场特别的流星雨即将到来：这些流星会撞向地球，并摧毁它们所撞击的任何东西。她为自己的安全感到焦虑，**发誓要找到一个安全的地方（一个永远不会被流星摧毁的地方）。**

如果将牧场放入一个直角坐标系中，贝茜现在的位置是原点，并且，贝茜不能踏上一块被流星砸过的土地。

根据预报，一共有 $M$ 颗流星 $(1\leq M\leq 50,000)$ 会坠落在农场上，其中第 $i$ 颗流星会在时刻 $T_i$（$0 \leq T _ i \leq 1000$）砸在坐标为 $(X_i,Y_i)(0\leq X_i\leq 300$，$0\leq Y_i\leq 300)$ 的格子里。流星的力量会将它所在的格子，以及周围 $4$ 个相邻的格子都化为焦土，当然贝茜也无法再在这些格子上行走。

贝茜在时刻 $0$ 开始行动，她只能在会在横纵坐标 $X,Y\ge 0$ 的区域中，平行于坐标轴行动，每 $1$ 个时刻中，她能移动到相邻的（一般是 $4$ 个）格子中的任意一个，当然目标格子要没有被烧焦才行。如果一个格子在时刻 $t$ 被流星撞击或烧焦，那么贝茜只能在 $t$ 之前的时刻在这个格子里出现。贝茜一开始在 $(0,0)$。

请你计算一下，贝茜最少需要多少时间才能到达一个安全的格子。如果不可能到达输出 $−1$。
## 输入格式
共 $M+1$ 行，第 $1$ 行输入一个整数 $M$，接下来的 $M$ 行每行输入三个整数分别为 $X_i, Y_i, T_i$。
## 输出格式
贝茜到达安全地点所需的最短时间，如果不可能，则为 $-1$。

## 样例 #1

### 样例输入 #1

```
4
0 0 2
2 1 2
1 1 2
0 3 5
```

### 样例输出 #1

```
5
```


## Idea

>[!notice] 坑点
>注意 300 之外是安全地点

永远不会被陨石砸中的位置，需要贝茜最少时间内到达，有两个关键的要素
- 这个位置永远不会被陨石砸中
- 贝茜能否到达

## code

```cpp showLineNumbers
#include <bits/stdc++.h>
using namespace std;

int area[311][311];
bool safe[311][311];

int dx[4] = {-1, 1, 0, 0};
int dy[4] = {0, 0, 1, -1};
vector<pair<int, int>> star[1011];
int m;

bool check(int x, int y) {
    if (x < 0 or y < 0) {
        return false;
    }
    return true;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    cin >> m;
    for (int i = 1; i <= m; i++) {
        int x, y, t;
        cin >> x >> y >> t;
        star[t].emplace_back(x, y);
    }

    for (int i = 0; i <= 1000; i++) {
        for (auto [x, y] : star[i]) {
            safe[x][y] = true;
            for (int j = 0; j < 4; j++) {
                if (check(x + dx[j], y + dy[j])) {
                    safe[x + dx[j]][y + dy[j]] = true;
                }
            }
        }
    }
    queue<pair<int, int>> q;
    q.emplace(0, 0);
    for (int i = 0; i <= 1000; i++) {
        for (auto [x, y] : star[i]) {
            area[x][y] = -1;
            for (int j = 0; j < 4; j++) {
                if (check(x + dx[j], y + dy[j])) {
                    area[x + dx[j]][y + dy[j]] = -1;
                }
            }
        }

        while (true) {
            if (q.empty()) {
                cout << -1 << endl;
                return 0;
            }
            auto [x, y] = q.front();
            if (area[x][y] == -1) {
                q.pop();
                continue;
            }
            if (safe[x][y] == false) {
                cout << area[x][y] << endl;
                return 0;
            }
            if (area[x][y] != i) {
                break;
            }
            q.pop();
            for (int j = 0; j < 4; j++) {
                if (check(x + dx[j], y + dy[j]) and
                    area[x + dx[j]][y + dy[j]] == 0) {
                    if (x + dx[j] == 0 and y + dy[j] == 0)
                        continue;
                    q.emplace(x + dx[j], y + dy[j]);
                    area[x + dx[j]][y + dy[j]] = area[x][y] + 1;
                }
            }
        }
    }
    cout << -1 << endl;
    return 0;
}
```
