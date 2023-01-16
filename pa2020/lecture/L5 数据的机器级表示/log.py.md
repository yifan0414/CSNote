#python

>[!abstract]
>使用查表的方法 (字符串映射）快速找到 64 位 bit 中 `+++++++++++++++++++++++++++++x++++++++++++++++++++++++++++++++++`   
>x 的位置，如果使用传统的方法需要使用到循环，时间耗费较高


```python import json
n, base = 64, '0'
for m in range(n, 10000):
  if len({ (2**i) % m for i in range(n) }) == n:
    M = { j: chr(ord(base) + i)
      for j in range(0, m)
        for i in range(0, n)
          if (2**i) % m == j }
    break

magic = json.dumps(''.join(
  [ M.get(j, '-') for j in range(0, m) ]
  )).strip('"')

print(f'#define LOG2(x) ("{magic}"[(x) % {m}] - \'{base}\')')
```

写一段代码，首先要考虑其目的，然后考虑用什么算法和数据结构去实现它。

建表：最重要的就是找到映射关系，我们需要把 2^0 2^1 ... 2^63 映射到一个表中。实现映射表的方法有很多，只要满足**一一对应**即可。这里使用的是<font color="#ff0000">字符串映射</font>。

映射很常见的一个操作就是模数，下面一段代码就是找到**一一映射**的模数
```python
n, base = 64, '0'
for m in range(n, 10000):
  if len({ (2**i) % m for i in range(n) }) == n:
# {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66}
```

这样就找到了模数 m = 67，我们根据下面简单了解到映射关系，顺序不一，但总是一一对应的。

```txt
2^0 mod 67 -> 1
2^1 mod 67 -> 2
2^2 mod 67 -> 4
2^3 mod 67 -> 8
2^4 mod 67 -> 16
2^5 mod 67 -> 32
2^6 mod 67 -> 64
2^7 mod 67 -> 61
2^8 mod 67 -> 55
2^9 mod 67 -> 43
...
2^63 mod 67 -> 42
```

下面就是完成字符串映射的关键一步，将得到的余数作为基的偏移量映射到新的字符上去

```python
M = { j: chr(ord(base) + i)
  for j in range(0, m)
    for i in range(0, n)
      if (2**i) % m == j }
```

下面就是一些 python 的特性以及构造出 C 语言中的宏定义。

```python
magic = json.dumps(''.join(
  [ M.get(j, '-') for j in range(0, m) ]
  )).strip('"')

print(f'#define LOG2(x) ("{magic}"[(x) % {m}] - \'{base}\')')
```

`M.get(j, '-')` 用于给在表中找不到（比如没有余数是 0, 17, 34）而返回的 None 赋值，具体差别如下：

```txt
In [21]: [ M.get(j) for j in range(0, m) ]
Out[21]:[None, '0', '1', 'W', '2', '?', 'X', 'G', '3', '<', '@', 'k', 'Y', 'C', 'H', 'f', '4', None, '=', ':', 'A', 'n', 'l', 'L', 'Z', 'N', 'D', 'c', 'I', '\', 'g', '_', '5', 'P', None, 'V', '>', 'F', ';', 'j', 'B', 'e', 'o', '9', 'm', 'K', 'M', 'b', '[', '^', 'O', 'U', 'E', 'i', 'd', '8', 'J', 'a', ']', 'T', 'h', '7', '`', 'S', '6', 'R', 'Q']

In [22]: [ M.get(j, '-') for j in range(0, m) ]
Out[22]:['-', '0', '1', 'W', '2', '?', 'X', 'G', '3', '<', '@', 'k', 'Y', 'C', 'H', 'f', '4', '-', '=', ':', 'A', 'n', 'l', 'L', 'Z', 'N', 'D', 'c', 'I', '\', 'g', '_', '5', 'P', '-', 'V', '>', 'F', ';', 'j', 'B', 'e', 'o', '9', 'm', 'K', 'M', 'b', '[', '^', 'O', 'U', 'E', 'i', 'd', '8', 'J', 'a', ']', 'T', 'h', '7', '`', 'S', '6', 'R', 'Q']

```

`json.dumps`  用于将 Python 对象编码成 JSON 字符串，具体差别如下

```python
In [27]: (''.join(
    ...:   [ M.get(j, '-') for j in range(0, m) ]
    ...:   ))
Out[27]: '-01W2?XG3<@kYCHf4-=:AnlLZNDcI\\g_5P-V>F;jBeo9mKMb[^OUEid8Ja]Th7`S6RQ'

In [28]: json.dumps(''.join(
    ...:   [ M.get(j, '-') for j in range(0, m) ]
    ...:   ))
Out[28]: '"-01W2?XG3<@kYCHf4-=:AnlLZNDcI\\\\g_5P-V>F;jBeo9mKMb[^OUEid8Ja]Th7`S6RQ"'
```

这样我们就构造出了 C 语言的查表宏定义代码

```c
#define LOG2(x) ("-01W2?XG3<@kYCHf4-=:AnlLZNDcI\g_5P-V>F;jBeo9mKMb[^OUEid8Ja]Th7`S6RQ"[(x) % 67] - '0')
```

**More Reading**

[算法-求二进制数中1的个数 - 翰墨小生 - 博客园 (cnblogs.com)](https://www.cnblogs.com/graphics/archive/2010/06/21/1752421.html)