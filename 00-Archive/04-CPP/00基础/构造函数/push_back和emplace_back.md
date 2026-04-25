
# 引子

```cpp hl:24,25,26
#include <bits/stdc++.h>
using namespace std;

class Student {
public:
    string name;
    int age;

    Student(string name, int age) : name(name), age(age) {}

    Student(const Student& s) : name(s.name), age(s.age) {
        std::cout << "Copy constructor called" << std::endl;
    }

    Student(Student &&s) noexcept : name(std::move(s.name)), age(s.age) {
        std::cout << "Move constructor called" << std::endl;
    }
};

int main() {
    vector<Student> vec;
    vec.reserve(5); // 避免因为vector的扩容而引起的移动构造函数

    vec.push_back({"Suer", 18}); // 会使用move construct
    vec.emplace_back("Suer", 18); // 使用 emplace_back 直接在末尾构造

    for (auto &it : vec) {
        cout << it.name << " " << it.age << endl;
    }

    return 0;
}

/*
Move constructor called
Suer 18
Suer 18
*/
```