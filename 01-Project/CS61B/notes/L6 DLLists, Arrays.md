# 1 Resource

- Book: https://joshhug.gitbooks.io/hug61b/content/chap2/chap23.html
- Video: https://www.youtube.com/playlist?list=PL8FaHk7qbOD4cp06tWA8i9m20pQLvcgE7
- Slide: https://docs.google.com/presentation/d/1itxVVyJTxKaDod3L8_jasnlZ1LHu-KDeV6Njbqqgbfs/edit?usp=sharing
- Guide: https://sp21.datastructur.es/materials/lectures/lec5/lec5

# 2 Overview

**SLList Drawbacks** `addLast()` is slow! We can’t add to the middle of our list. In addition, if our list is really large, we have to start at the front, and loop all the way to the back of our list before adding our element.

**A Naive Solution** Recall that we cached the size of our list as an instance variable of `SLList`. What if we cached the `last` element in our list as well? All of a sudden, `addLast()` is fast again; we access the last element immediately, then add our element in. But `removeLast()` is still slow. In `removeLast()`, we have to know what our second-to-last element is, so we can point our cached `last` variable to it. We could then cache a `second-to-last` variable, but now if I ever want to remove the second-to-last element, I need to know where our third-to-last element is. How to solve this problem?

**DLList** The solution is to give each `IntNode` a `prev` pointer, pointing to the previous item. This creates a doubly-linked list, or `DLList`. With this modification, adding and removing from the front and back of our list becomes fast (although adding/removing from the middle remains slow).

**Incorporating the Sentinel** Recall that we added a sentinel node to our `SLList`. For `DLList`, we can either have two sentinels (one for the front, and one for the back), or we can use a circular sentinel. A `DLList` using a circular sentinel has one sentinel. The sentinel points to the first element of the list with `next` and the last element of the list with `prev`. In addition, the last element of the list’s `next` points to the sentinel and the first element of the list’s `prev` points to the sentinel. For an empty list, the sentinel points to itself in both directions.

**Generic DLList** How can we modify our `DLList` so that it can be a list of whatever objects we choose? Recall that our class definition looks like this:

```java
public class DLList { ... }
```

We will change this to

```java
public class DLList<T> { ... }
```

where `T` is a placeholder object type. Notice the angle bracket syntax. Also note that we don’t have to use `T`; any variable name is fine. In our `DLList`, our item is now of type `T`, and our methods now take `T` instances as parameters. We can also rename our `IntNode` class to `TNode` for accuracy.

**Using Generic DLList** Recall that to create a `DLList`, we typed:

```java
DLList list = new DLList(10);
```

If we now want to create a `DLList` holding `String` objects, then we must say:

```java
DLList<String> list = new DLList<>("bone");
```

On list creation, the compiler replaces all instances of `T` with `String`! We will cover generic typing in more detail in later lectures.

**Arrays** Recall that variables are just boxes of bits. For example, `int x;` gives us a memory box of 32 bits. Arrays are a special object which consists of a numbered sequence of memory boxes! To get the ith item of array `A`, use `A[i]`. The length of an array cannot change, and all the elements of the array must be of the same type (this is different from a Python list). The boxes are zero-indexed, meaning that for a list with N elements, the first element is at `A[0]` and the last element is at `A[N - 1]`. Unlike regular classes, **arrays do not have methods!** Arrays do have a `length` variable though.

**Instantiating Arrays** There are three valid notations for creating arrays. The first way specifies the size of the array, and fills the array with default values:

```java
int[] y = new int[3];
```

The second and third ways fill up the array with specific values.

```java
int[] x = new int[]{1, 2, 3, 4, 5};
int[] w = {1, 2, 3, 4, 5};
```

We can set a value in an array by using array indexing. For example, we can say `A[3] = 4;`. This will access the **fourth** element of array `A` and sets the value at that box to 4.

**Arraycopy** In order to make a copy of an array, we can use `System.arraycopy`. It takes 5 parameters; the syntax is hard to memorize, so we suggest using various references online such as [this](https://www.tutorialspoint.com/java/lang/system_arraycopy.htm).

**2D Arrays** We can declare multidimensional arrays. For 2D integer arrays, we use the syntax:

```java
int[][] array = new int[4][];
```

This creates an array that holds integer arrays. Note that we have to manually create the inner arrays like follows:

```java
array[0] = new int[]{0, 1, 2, 3};
```

Java can also create multidemensional arrays with the inner arrays created automatically. To do this, use the syntax:

```java
int[][] array = new int[4][4];
```

We can also use the notation:

```java
int[][] array = new int[][]{{1}, {1, 2}, {1, 2, 3}}
```

to get arrays with specific values.

**Arrays vs. Classes**

-   Both are used to organize a bunch of memory.
-   Both have a fixed number of “boxes”.
-   Arrays are accessed via square bracket notation. Classes are accessed via dot notation.
-   Elements in the array must be all be the same type. Elements in a class may be of different types.
-   Array indices are computed at runtime. We cannot compute class member variable names.

# 3 Note

本节课继续深入了对链表的研究，我们发现 SSList 在末尾添加 node 是非常低效率的（每次都要遍历），所以选择定义一个 last 变量永远指向末尾节点。但 add，get，remove 中 removeLastNode 的操作依然很慢，所以进化为了双向链表，为了摆脱 special case 的判定，在双向链表的末尾添加了尾结点。另一种方法是使用循环列表（recommended）。

然后学习了泛型技术，减少了重复工作，使代码变得更简洁易用。

最后学习了 JAVA 中的数组，这也许是这一课最大收获，与 C 的数组不同的是，JAVA 数组是一个对象。他有他自己的属性和方法，最重要的一点是当数组内是 reference type 时，这些引用数据并不是按照内存顺序排列的而是分布在不同的地址。

![18NmiX](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/18NmiX.png)

![ypERfa](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/ypERfa.png)

对于 C 而言，二维数组，结构体数组在内存中都是顺序排列的，都可以用指针精确的控制。