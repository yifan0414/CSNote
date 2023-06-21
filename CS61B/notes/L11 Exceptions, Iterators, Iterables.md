# 0 Note

## 0.1 Iterators 和 Iterable 的区别

An `Iterable` is a simple **representation** of a series of elements that can be iterated over. It does not have any iteration state such as a "current element". Instead, it has one method that produces an `Iterator`.

An `Iterator` is the object with iteration state. It lets you check if it has more elements using `hasNext()` and move to the next element (if any) using `next()`.

Typically, an `Iterable` should be able to produce any number of valid `Iterator`s.


# 1 Resource

-   Book: https://joshhug.gitbooks.io/hug61b/content/chap6/chap61.html
-   Video: https://www.youtube.com/watch?v=DWr8YNXPH6k&list=PL8FaHk7qbOD4vPE_Bd8QagarKi3kPw8rB
-   Slide: https://docs.google.com/presentation/d/1f6hTbVBk4FzVPSfMrx0nHKJpFBrRbdD2elioMmYktvg/edit?usp=sharing
-   Guide: https://sp21.datastructur.es/materials/lectures/lec10/lec10

# 2 Overview

## 2.1 Exceptions

翻译：Most likely you have encountered an exception in your code such as a `NullPointerException` or an `IndexOutOfBoundsException`. Now we will learn about how we can “throw” exceptions ourselves, and also handle thrown exceptions. Here is an example of an exception that we throw:

```java
throw new RuntimeException("For no reason.");
```

_Note: Try/Catch is out of scope for now!_

Throwing exceptions is useful to notify your user of something wrong they have done. On the other hand, we can also “catch” exceptions that happen in our code! Here is an example:

```java
try {
    dog.run()
} catch (Exception e) {
    System.out.println("Tried to run: " + e);
}
System.out.println("Hello World!");
```

There are a few key things to note. Firstly, the entirety of the `try` section is run until/if there is an exception thrown. If there never is an exception, the entire catch block is skipped. If there is an exception, the code immediately jumps into the catch block with the corresponding exception, and executes from there.

## 2.2 Iterators and Iterables

These two words are very closely related, but have two different meanings that are often easy to confuse. The first thing to know is that these are both Java interfaces, with different methods that need to be implemented. Here is a simplified interface for Iterator:

```java
public interface Iterator<T> {
  boolean hasNext();
  T next();
}
```

Here is a simplified interface for Iterable:

```java
public interface Iterable<T> {
    Iterator<T> iterator();
}
```

Notice that in order for an object (for example an ArrayList or LinkedList) to be _iterable_, it must include a method that returns an _iterator_. The iterator is the object that iterates over an iterable object. Keep this relationship and distinction in mind as you work with these two interfaces.

## 2.3 toString

The `toString()` method returns a string representation of objects.

## 2.4 == vs .equals

We have two concepts of equality in Java- “=\=” and the “. equals ()” method. The key difference is that when using =\=, we are checking if two objects have the same address in memory (that they point to the same object). On the other hand, .equals () is a method that can be overridden by a class and can be used to define some custom way of determining equality.

For example, say we wanted to check if two stones are equal:

```java
public class Stone{
  public Stone(int weight){...}
}
Stone s = new Stone(100);
Stone r = new Stone(100);
```

If we want to consider s and r equal because they have the same weight. If we do check equality using =\=, these Stones would not be considered equal because they do not have the same memory address.

On the other hand, if you override the equals method of Stone as follows

```java
public boolean equals(Object o){
  return this.weight == ((Stone) o).weight
}
```

We would have that the stones would be considered equal because they have the same weight.