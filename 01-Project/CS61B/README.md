# 一、初识

距离上次学习数据结构和算法已经过去两年了，大二上学期的「数据结构」用的是浙大陈越姥姥的书，书中数据结构代码是使用纯 C 语言实现的，一般一个数据结构只在一个文件中，可维护性和可读性不太好。但其代码与数据结构相结合的思想仍然让我受益匪浅。大二下学期的「算法」用的是经典著作 Algorithm 4th，这确实是一本好书，在使用 JAVA 具有良好模块化的基础上，兼顾了算法设计分析与算法工程实际应用。特别是对算法的过程进行了详尽的图解，还有课后练习让你使用 JAVA 模拟算法的运行过程，加深印象。这本书段段续续的读完了前四章，有大量内容没有消化掉。偶然从 csdiy 上得知了 CS62B 的存在，大概浏览了课程的 Calendar，貌似课程本身难度比 Algorithm 要小，但其中的 Project 广受好评。所以我决定先花一个月左右的时间利用这门课复习一下数据结构。

# 二、环境配置

课程网页：[Main | CS 61B Spring 2021 (datastructur.es)](https://sp21.datastructur.es/index.html)

我这里使用的是 sp21 版，因为这是最新的有 autograde 的版本，因为本人对 Linux cmdline、git、Java 等都有一定的了解，所以环境配置没有费多大力气。

一开始看到 [Lab 1: IntelliJ, Java, git | CS 61B Spring 2021 (datastructur.es)](https://sp21.datastructur.es/materials/lab/lab1/lab1) 的内容有非常多感觉到了一丝紧张，但仔细阅读后发现这个 Lab 就不是给校外蹭课的人的看的。

**Important:**

从 [Berkeley-CS61B/skeleton-sp21: starter code for spring 21 (github.com)](https://github.com/Berkeley-CS61B/skeleton-sp21) clone 到本地

![VfRBf1](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/VfRBf1.png)

1. 使用 `rm -rf .git` 命令把原有的 git 配置删除掉
2. 在根目录使用 `mv skeleton-sp21 cs61b` 将仓库改名
3. 在 `cs61b` 中使用 `git init`、`git add .`、`git commit -m "First commit"`
4. 在自己的 Github 上新建一个远程仓库（名字也叫 `cs61b`），然后在 `cs61b` 中使用 `git remote add origin https://github.com/yourname/cs61b.git`，最后使用 `git push -u origin master` 推送即可

**Auto grade:**

在 [Your Courses | Gradescope](https://www.gradescope.com/) 网站上注册账号
1. 课程码：MB7ZPY
2. 学校：UC Berkeley
3. 邮箱：自己邮箱

然后就会看到 Spring 2021 的 CS 61B (Public) 的课程入口，进入后就可以看到待评测的 Lab 和 Project 了。

# 三、Process record

## 3. 1 Labs

- [x] Lab01 ✅ 2023-01-21
- [x] Lab02 ✅ 2023-01-23
- [x] Lab03 ✅ 2023-01-24
- [ ] Lab04
- [ ] Lab05
- [ ] Lab06
- [ ] Lab07
- [ ] Lab10
- [ ] Lab11
- [ ] Lab12
- [ ] Lab13
- [ ] Lab14

## 3.2 Projects

- [x] Project0 ✅ 2023-01-22
- [ ] Project1
- [ ] Project2
- [ ] Project3