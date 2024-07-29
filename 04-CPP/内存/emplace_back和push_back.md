在 C++中，使用 `std::vector` 的 `push_back` 和 `emplace_back` 方法添加元素，效率上通常 `emplace_back` 会更优，尤其是当涉及到复杂对象或需要构造参数的情况。这里来详细解析两者的差异以及为什么 `emplace_back` 通常更有效率。

### push_back

`push_back` 方法将元素添加到 `vector` 的末尾。当你使用 `push_back` 时，这个方法会接收一个元素的副本（或者右值引用），然后将其复制（或移动）到 `vector` 的内部存储中。

例如：
```cpp
std::vector<std::pair<int, int>> v;
v.push_back({1, 2});
```
在这个例子中，`{1, 2}` 首先创建了一个临时的 `std::pair<int, int>` 对象，然后 `push_back` 通过拷贝构造或移动构造将这个临时对象放入 `vector`。

### emplace_back 

`emplace_back` 方法则是直接在 `vector` 的末尾构造元素，而不是先构造一个临时元素再将其复制或移动到 `vector` 中。这通过接收构造函数的参数，而不是元素本身，来达到更直接的构造。

例如：
```py
std::vector<std::pair<int, int>> v;
v.emplace_back(1, 2);
```
在这里，`emplace_back(1, 2)` 直接在 `vector` 的存储空间中构造了 `std::pair<int, int>`，使用给定的参数 `1` 和 `2`。没有临时对象的创建和复制/移动操作，这减少了构造和析构调用的数量。

### 效率比较

- **减少临时对象**：`emplace_back` 通常更有效率，因为它省去了创建临时对象和随后的拷贝或移动操作。直接在容器的存储位置构造对象意味着更少的函数调用和内存操作。
- **直接构造**：在 `emplace_back` 中，元素是直接在容器的内存中构造的，使用的是元素的构造函数，允许就地构造，而不需要额外的复制或移动。

### 结论

因此，对于需要构造参数的类型，如 `std::pair<int, int>` 或任何复杂的用户定义类型，`emplace_back` 通常提供了更好的性能，特别是在对象构造代价较高时。然而，对于简单的数据类型（如 `int`、`float`），`push_back` 和 `emplace_back` 的性能差异可能不大。但是，在设计要求效率的代码时，倾向于使用 `emplace_back` 可以作为一种更好的通用实践。