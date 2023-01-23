一个程序如果不进行严格的测试，那么这个程序可以被认为毫无保障。就比如快速排序算法，如果自己按照分治的思想可以很容易写出一个算法原型，但并不意味着 100%正确，特别是面对许多边界情况的条件下。因此，我们必须抱着严谨的态度去对待测试。正确的构造测试样例意味着你对软件或者算法的工作方式十分熟悉，进而产生了一种测试驱动发展 **_Test-Driven Development (TDD)_** 的编程思想。

但构造测试样例的过程是繁琐且不容易维护的，如果我们仅仅是在 main 函数中构造输入以及目标输出，会造成程序混乱难以复用。因此在 JAVA 中使用 Junit 进行单元测试是一个好主意。

以下摘自 [Hug61B 3.1](https://joshhug.gitbooks.io/hug61b/content/chap3/chap31.html)

##### Correctness Tool #1 : Autograder

Let's go back to ground zero. The autograder was likely the first correctness tool you were exposed to. Our autograder is in fact based on JUnit plus some extra custom libraries.

There are some great benefits to autograders. Perhaps most importantly, it verifies correctness for you, saving you from the tedious and non-instructive task of writing all of your own tests. It also gamifies the assessment process by providing juicy points as an incentive to acheiving correctness. This can also backfire if students spend undue amounts of time chasing final points that won't actually affect their grade or learning.

However, autograders don't exist in the real world and relying on autograders can build bad habits. One's workflow is hindered by sporadically uploading your code and waiting for the autograder to run. _Autograder Driven Development_ is an extreme version of this in which students write all their code, fix their compiler errors, and then submit to the autograder. After getting back errors, students may try to make some changes, sprinkle in print statements, and submit again. And repeat. Ultimately, you are not in control of either your workflow or your code if you rely on an autograder.

##### Correctness Tool #2: JUnit Tests

JUnit testing, as we have seen, unlocks a new world for you. Rather than relying on an autograder written by someone else, you write tests for each piece of your program. We refer to each of these pieces as a unit. This allows you to have confidence in each unit of your code - you can depend on them. This also helps decrease debugging time as you can isolate attention to one unit of code at a time (often a single method). Unit testing also forces you to clarify what each unit of code should be accomplishing.

There are some downsides to unit tests, however. First, writing thorough tests takes time. It's easy to write incomplete unit tests which give a false confidence to your code. It's also difficult to write tests for units that depend on other units (consider the `addFirst` method in your `LinkedListDeque`).

**_Test-Driven Development (TDD)_**

TDD is a development process in which we write tests for code before writing the code itself. The steps are as follows:

1.  Identify a new feature.
2.  Write a unit test for that feature.
3.  Run the test. It should fail.
4.  Write code that passes the test. Yay!
5.  Optional: refactor code to make it faster, cleaner, etc. Except now we have a reference to tests that should pass.

Test-Driven Development is not required in this class and may not be your style but unit testing in general is most definitely a good idea.

##### Correctness Tool #3: Integration Testing

Unit tests are great but we should also make sure these units work properly together ([unlike this meme](https://media.giphy.com/media/3o7rbPDRHIHwbmcOBy/giphy.gif)). Integration testing verifies that components interact properly together. JUnit can in fact be used for this. You can imagine unit testing as the most nitty gritty, with integration testing a level of abstraction above this.

The challenge with integration testing is that it is tedious to do manually yet challenging to automate. And at a high level of abstraction, it's easy to miss subtle or rare errors.

As a summary, you should **definitely write tests but only when they might be useful!** Taking inspiration from TDD, writing your tests before writing code can also be very helpful in some cases.