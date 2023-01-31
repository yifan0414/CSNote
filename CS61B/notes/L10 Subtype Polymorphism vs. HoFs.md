# 0 Note

## 0.1 Comparable 和 Comparator 的区别


| Comparable   | Comparator   |
| ------------ | ------------ |
| `java.util`  | `java.lang`  |
| 定义在类内部 | 定义在类外部 |
| 由设计者决定 | 由使用者决定 |


# 1 Resource

-   Book: https://joshhug.gitbooks.io/hug61b/content/chap4/chap43.html
-   Video: https://www.youtube.com/playlist?list=PL8FaHk7qbOD56r1sGUGifsfC0KRDAsuZ3
-   Slide: https://docs.google.com/presentation/d/13SVUU8oeTch0ex42hBQLGTZ4XAaMKDJmuXMqegEoVqM/edit?usp=sharing
-   Guide: https://sp21.datastructur.es/materials/lectures/lec10/lec10

# 2 Overview

## 2.1 Review: Typing Rules

-   Compiler allows the memory box to hold any subtype.
-   Compiler allows calls based on static type.
-   Overriden non-static methods are selected at runtime based on dynamic type.
-   For overloaded methods, the method is selected at compile time.

## 2.2 Subtype Polymorphism

Consider a variable of static type `Deque`. The behavior of calling `deque.method()` depends on the dynamic type. Thus, we could have many subclasses the implement the `Deque` interface, all of which will be able to call `deque.method()`.

## 2.3 Subtype Polymorphism Example

Suppose we want to write a function `max()` that returns the max of any array regardless of type. If we write a method `max(Object[] items)`, where we use the ‘>’ operator to compare each element in the array, this will **not work**! Why is this the case?

Well, this makes the assumption that all objects **can be compared**. But some objects cannot! Alternatively, we could write a `max()` function inside the Dog class, but now we have to write a `max()` function for **each class** that we want to compare!（Which is a sad thing） Remember, our goal is to write a “one true max method” that works for **all comparable objects**.

## 2.4 Solution: OurComparable Interface

The solution is to create an interface that contains a `compareTo(Object)` method; let’s call this interface `OurComparable`. Now, our `max()` method can take a `OurComparable[]` parameter, and since we guarantee that any object which extends the interface has all the methods inside the interface, we guarantee that we will always be able to call a `compareTo` method, and that this method will correctly return some ordering of the objects.

Now, we can specify a “one true max method”. Of course, any object that needs to be compared must implement the `compareTo` method. However, instead of re-implementing the `max` logic in every class, we only need to implement the logic for picking the ordering of the objects, given two objects.

## 2.5 Even Better: Java’s In-Built Comparable

Java has an in-built `Comparable` interface that uses generics to avoid any weird casting issues. Plus, Comparable already works for things like `Integer`, `Character`, and `String`; moreover, these objects have already implemented a `max`, `min`, etc. method for you. Thus you do not need to re-do work that’s already been done!

## 2.6 Comparators

The term “Natural Order” is used to refer to the ordering implied by a `Comparable`’s `compareTo` method. However, what if we want to order our `Dog` objects by something other than `size`? We will instead pass in a `Comparator<T>` interface, which demands a `compare()` method. We can then implement the `compare()` method anyway we want to achieve our ordering.