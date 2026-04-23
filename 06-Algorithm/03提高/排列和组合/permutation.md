>[!quote]
>[STL next_permutation和prev_permutation 算法原理和自行实现_next permutation-CSDN博客](https://blog.csdn.net/myRealization/article/details/104803834)


`std::next_permutation` 和 `std::prev_permutation` 是 C++ 标准库中的两个算法，用于生成序列的下一个和上一个排列。这两个函数都定义在 `<algorithm>` 头文件中。

# std::next_permutation

`std::next_permutation` 用于生成序列的下一个字典序排列。如果当前序列是字典序的最后一个排列，它会生成第一个排列（即将序列按升序排列）。函数原型如下：

```cpp
template< class BidirIt >
bool next_permutation( BidirIt first, BidirIt last );

template< class BidirIt, class Compare >
bool next_permutation( BidirIt first, BidirIt last, Compare comp );
```

- **参数**：
  - `first`：序列的起始迭代器。
  - `last`：序列的结束迭代器。
  - `comp`：一个可选的二元比较函数对象，用于定义元素的排序规则。

- **返回值**：
  - 如果存在下一个排列，返回 `true`，并将序列改为下一个排列。
  - 如果当前排列是字典序的最后一个排列，返回 `false`，并将序列改为第一个排列。

### 参考实现

```cpp
#include <iostream>
#include <algorithm>
using namespace std;

template<typename T>
bool myNextPermutation(T *start, T *end) { //[start,end)
  T *cur = end - 1, *pre = cur - 1; //pre指向partitionNumber 
  while (cur > start && *pre >= *cur) 
    --cur, --pre; //从右到左进行扫描，发现第一个递减的数字
  
  if (cur <= start) return false; //整个排列逆序, 不存在更大的排列
  
  //从右到左进行扫描，发现第一个比partitionNumber大的数
  for (cur = end - 1; *cur <= *pre; --cur); //cur指向changeNumber  
  
  swap(*pre, *cur);
  reverse(pre + 1, end); //将尾部的逆序变成正序 
  return true; 
}

int main() { 
  
  char data[] = "aabc";
  do {
    puts(data);
  } while (myNextPermutation(data, data + 4));
  return 0;  
}

```
### 分析
要从数学上分析 `myNextPermutation` 函数的正确性，可以分为以下几个步骤：

1. **寻找 Partition Point**：
   ```cpp
   T *cur = end - 1, *pre = cur - 1;
   while (cur > start && *pre >= *cur) 
     --cur, --pre;
   ```
   这段代码从右向左扫描，寻找第一个递减的元素对 $(pre, cur)$，即找到一个位置 `pre` 使得 `*pre < *cur`。这个位置 `pre` 被称为分割点（Partition Point）。如果整个序列是降序排列的，那么 `pre` 将会指向 `start - 1`，表示当前排列是字典序的最后一个排列。

2. **检查是否为最后一个排列**：
   ```cpp
   if (cur <= start) return false;
   ```
   如果 `cur <= start`，说明整个序列是降序排列的，即当前排列是字典序的最后一个排列，因此不存在下一个排列，函数返回 `false`。

3. **寻找 Change Point**：
   ```cpp
   for (cur = end - 1; *cur <= *pre; --cur);
   ```
   这段代码从右向左扫描，寻找第一个比 `*pre` 大的元素 `*cur`。这个位置 `cur` 被称为交换点（Change Point）。

4. **交换 Partition Point 和 Change Point**：
   ```cpp
   swap(*pre, *cur);
   ```
   交换 `*pre` 和 `*cur`，使得 `*pre` 变得稍大一点，从而得到一个比当前排列稍大的排列。

5. **反转 Partition Point 右侧的序列**：
   ```cpp
   reverse(pre + 1, end);
   ```
   反转 `pre` 右侧的序列，使其变成最小的升序排列。因为 `pre` 右侧的序列在交换前是降序排列的，所以反转后变成升序排列。

#### 数学证明
假设当前序列是 $a_1, a_2, \ldots, a_n$，我们通过以下步骤证明该算法的正确性。

1. **寻找分割点**：
   - 找到第一个位置 `i` 使得 $a_i < a_{i+1}$。
   - 此时，$a_{i+1}, a_{i+2}, \ldots, a_n$ 是一个非递增序列。

2. **检查是否为最后一个排列**：
   - 如果找不到这样的 `i`，说明整个序列是非递增的，即当前排列是字典序的最后一个排列。

3. **寻找交换点**：
   - 从右到左找到第一个位置 `j` 使得 $a_j > a_i$。
   - 由于 $a_{i+1}, a_{i+2}, \ldots, a_n$ 是非递增的，且 $a_i < a_{i+1}$，所以 $a_j$ 是 `i` 右侧第一个比 $a_i$ 大的元素。

4. **交换 $a_i$ 和 $a_j$**：
   - 交换 $a_i$ 和 $a_j$ 后，得到的新序列依然保持 $a_1, a_2, \ldots, a_{i-1}$ 和 $a_{i+1}, a_{i+2}, \ldots, a_n$ 的相对顺序不变，但 $a_i$ 变大了一点。

5. **反转 $a_{i+1}, a_{i+2}, \ldots, a_n$**：
   - 由于 $a_{i+1}, a_{i+2}, \ldots, a_n$ 是非递增的，反转后变为非递减序列，即最小的排列。

通过上述步骤，可以保证得到的排列是当前排列的下一个字典序排列。

#### 例子
假设当前排列是 `1, 3, 5, 4, 2`：

1. **寻找分割点**：
   - 从右向左扫描，找到 `3 < 5`，即 `3` 是分割点。

2. **寻找交换点**：
   - 从右向左扫描，找到 `4 > 3`，即 `4` 是交换点。

3. **交换**：
   - 交换 `3` 和 `4`，得到 `1, 4, 5, 3, 2`。

4. **反转**：
   - 反转 `5, 3, 2`，得到 `1, 4, 2, 3, 5`。

最终结果 `1, 4, 2, 3, 5` 是 `1, 3, 5, 4, 2` 的下一个字典序排列。

通过上述分析，可以证明 `myNextPermutation` 函数的正确性。

# std::prev_permutation

`std::prev_permutation` 用于生成序列的上一个字典序排列。如果当前序列是字典序的第一个排列，它会生成最后一个排列（即将序列按降序排列）。函数原型如下：

```cpp
template< class BidirIt >
bool prev_permutation( BidirIt first, BidirIt last );

template< class BidirIt, class Compare >
bool prev_permutation( BidirIt first, BidirIt last, Compare comp );
```

- **参数**：
  - `first`：序列的起始迭代器。
  - `last`：序列的结束迭代器。
  - `comp`：一个可选的二元比较函数对象，用于定义元素的排序规则。

- **返回值**：
  - 如果存在上一个排列，返回 `true`，并将序列改为上一个排列。
  - 如果当前排列是字典序的第一个排列，返回 `false`，并将序列改为最后一个排列。

### 示例

```cpp
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> vec = {3, 2, 1};

    do {
        for (int x : vec) {
            std::cout << x << " ";
        }
        std::cout << std::endl;
    } while (std::prev_permutation(vec.begin(), vec.end()));

    return 0;
}
```

# 总结

- `std::next_permutation` 和 `std::prev_permutation` 都用于生成排列。
- `std::next_permutation` 生成下一个字典序排列，而 `std::prev_permutation` 生成上一个字典序排列。
- 如果当前排列是最后一个或第一个排列，函数会将序列重置为第一个或最后一个排列，并返回 `false`。

