# 1 Resource

- Book: https://joshhug.gitbooks.io/hug61b/content/chap2/chap22.html
- Video: https://www.youtube.com/playlist?list=PL8FaHk7qbOD4cp06tWA8i9m20pQLvcgE7
- Slide: https://docs.google.com/presentation/d/1q6p0spGPmj8rFrQnWKp_QZJRFHg-IkHE1L9BfZc0f0Q/edit#slide=id.g5f6f34a2e_131
- Guide: https://sp21.datastructur.es/materials/lectures/lec4/lec4

![[cs61b lec5 2021 lists2, sllists.pdf]]

# 2 Overview

**Naked Data Structures** `IntLists` are hard to use. In order to use an `IntList` correctly, the programmer must understand and utilize recursion even for simple list related tasks.

**Adding Clothes** First, we will turn the `IntList` class into an `IntNode` class. Then, we will delete any methods in the `IntNode` class. Next, we will create a new class called `SLList`, which contains the instance variable `first`, and this variable should be of type `IntNode`. In essence, we have “wrapped” our `IntNode` with an `SLList`.

**Using SLList** As a user, to create a list, I call the constructor for `SLList`, and pass in the number I wish to fill my list with. The `SLList` constructor will then call the `IntList` constructor with that number, and set `first` to point to the `IntList` it just created.

**Improvement** Notice that when creating a list with one value, we wrote `SLList list = new SLList(1)`. We did not have to worry about passing in a null value like we did with our `IntList`. Essentially, the SLList class acts as a **middleman** between the list user and the naked `IntList`.

**Public vs. Private** We want users to modify our list via `SLList` methods only, and not by directly modifying `first`. We can prevent other users from doing so by setting our variable access to `private`. Writing `private IntNode first;` prevents code in other classes from accessing and modifying `first` (while the code inside the class can still do so).

**Nested Classes** We can also move classes into classes to make nested classes! You can also declare the nested classes to be private as well; this way, other classes can never use this nested class.

**Static Nested Classes** If the `IntNode` class never uses any variable or method of the `SLList` class, we can turn this class static by adding the “static” keyword.

**Recursive Helper Methods** If we want to write a recursive method in `SLList`, how would we go about doing that? After all, the `SLList` is not a naturally recursive data structure like the `IntNode`. A common idea is to write an outer method that users can call. This method calls a private helper method that takes `IntNode` as a parameter. This helper method will then perform the recursion, and return the answer back to the outer method.

**Caching** Previously, we calculated the size of our `IntList` recursively by returning 1 + the size of the rest of our list. This becomes really slow if our list becomes really big, and we repeatedly call our size method. Now that we have an `SLList`, lets simply cache the size of our list as an instance variable! Note that we could not do this before with out `IntList`.

**Empty Lists** With an`SLList`, we can now represent an empty list. We simply set `first` to `null` and `size` to `0`. However, we have introduced some bugs; namely, because `first` is now `null`, any method that tries to access a property of `first` (like `first.item`) will return a `NullPointerException`. Of course, we can fix this bug by writing code that handles this **special case**. But there may be many special cases. Is there a better solution?

**Sentinel Nodes** Lets make all `SLList` objects, even empty lists, the same. To do this, lets give each SLList a sentinel node, a node that is always there. Actual elements go after the sentinel node, and all of our methods should respect the idea that sentinel is always the first element in our list.

**Invariants** An invariant is a fact about a data structure that is guaranteed to be true (assuming there are no bugs in your code). This gives us a convenient checklist every time we add a feature to our data structure. Users are also guaranteed certain properties that they trust will be maintained. For example, an `SLList` with a sentinel node has at least the following invariants:

-   The sentinel reference always points to a sentinel node.
-   The front item (if it exists), is always at sentinel.next.item.
-   The size variable is always the total number of items that have been added.

# Notes

这一课时，Josh 带着我们从一个简单的 `IntList` 逐步的变为较为完善的 `SLList`。在这个过程中，我对面向对象程序设计有了一个初步的了解，`SLList` 相比于 `IntList` 是如此的优雅、简洁且易用。我们只需要把最外层的接口 public 就可以了，这也是所保证的 use forver。

回到单链表，我们只需要关心其操作，比如**addFirst**、**getFirst**、**size**、**addLast**。对于其到底是用递归实现还是循环实现亦或者有没有头结点都不重要，甚至单链表并不需要是链表结构实现，我们在意的是其功能是否 workable and concise。

![BAJuAx](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/BAJuAx.png)


在实现内部，我们必须考虑其可复用性，可维护性，性能等一系列东西。因此如何组织数据结构变得尤为重要。