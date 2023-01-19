# 南京大学 计算机科学与技术系 计算机系统基础 课程实验 2022

## 实验前阅读

> [!info] 最新消息(请每天至少关注一次)
> -   [学术诚信(什么事情能做, 什么不能)](http://integrity.mit.edu/)
> -   [常见问题(对PA的各种困惑)](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/FAQ.html)
> -   如何正确求助: [提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)和[别像弱智一样提问](https://github.com/tangx/Stop-Ask-Questions-The-Stupid-Ways/blob/master/README.md)
> - 外部资源
> 	-   PA习题课 (2022 秋季学期, [王慧妍](https://cocowhy1013.github.io/)老师): [课程资料](http://why.ink:8080/ICS/2022/)
> 	-   中国大学MOOC的ICS理论课 (袁春风老师): [上](https://www.icourse163.org/course/NJU-1001625001), [中](https://www.icourse163.org/course/NJU-1001964032), [下](https://www.icourse163.org/course/NJU-1002532004)
>	- [南大SICP编程课](https://nju-sicp.bitbucket.io/)
> 		-    如果你觉得自己的编程基础不过关, 墙裂推荐自学这门课
> 		-   虽然它教的是python, 但语言的语法是次要的, 对编程思维的锻炼才是最重要的
> 	-   [OS课](http://jyywiki.cn/OS/2022/) (2022 春季学期, [蒋炎岩](http://ics.nju.edu.cn/~jyy)老师)
>	- PA往期习题课
>		-   2021 秋季学期, [王慧妍](https://cocowhy1013.github.io/)老师: [课程资料](http://jyywiki.cn/ICS/2021/)
>		-   2020 秋季学期, [蒋炎岩](http://ics.nju.edu.cn/~jyy)老师: [课程资料](http://jyywiki.cn/ICS/2020/), [B站录播](https://www.bilibili.com/video/BV1qa4y1j7xk/)

> [!info] 离线阅读实验讲义
> 实验讲义页面通过github page发布, 但其网络可能不稳定. 你可以把[这个仓库](https://github.com/NJU-ProjectN/ics-pa-gitbook)克隆到本地, 然后通过浏览器来离线阅读讲义.
> 
> 但随着讲义内容的更新, 你将无法自动地阅读到最新版本的内容. 你需要在仓库路径中手动执行 `bash update.sh` 来将最新版本的内容同步到本地. 再次强调, 如果你选择了离线阅读方式, 将由你来负责获取最新的讲义内容.

> [!tip] 如何求助
>  -   实验前请先仔细阅读[本页面](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/)以及[为什么要学习计算机系统基础](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/why.html).
>-   如果你在实验过程中遇到了困难, 并打算向我们寻求帮助, 请先阅读[提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)和[别像弱智一样提问](https://github.com/tangx/Stop-Ask-Questions-The-Stupid-Ways/blob/master/README.md)这两篇文章.
>-   如果你发现了实验讲义和材料的错误或者对实验内容有疑问或建议, 请通过邮件的方式联系余子濠(zihaoyu.x#gmail.com)

> [!tip] 小百合系版"有像我一样不会写代码的cser么?"回复节选
> -   我们都是活生生的人, 从小就被不由自主地教导用最小的付出获得最大的得到, 经常会忘记我们究竟要的是什么. 我承认我完美主义, 但我想每个人心中都有那一份求知的渴望和对真理的向往, "大学"的灵魂也就在于超越世俗, 超越时代的纯真和理想 -- 我们不是要讨好企业的毕业生, 而是要寻找改变世界的力量. -- jyy
> 
> -   教育除了知识的记忆之外, 更本质的是能力的训练, 即所谓的training. 而但凡training就必须克服一定的难度, 否则你就是在做重复劳动, 能力也不会有改变. 如果遇到难度就选择退缩, 或者让别人来替你克服本该由你自己克服的难度, 等于是自动放弃了获得training的机会, 而这其实是大学专业教育最宝贵的部分. -- etone
> 
> -   这种"只要不影响我现在survive, 就不要紧"的想法其实非常的利己和短视: 你在专业上的技不如人, 迟早有一天会找上来, 会影响到你个人职业生涯的长远的发展; 更严重的是, 这些以得过且过的态度来对待自己专业的学生, 他们的survive其实是以透支南大教育的信誉为代价的 -- 如果我们一定比例的毕业生都是这种情况, 那么过不了多久, 不但那些混到毕业的学生也没那么容易survive了, 而且那些真正自己刻苦努力的学生, 他们的前途也会受到影响. -- etone

## 实验方案
理解"程序如何在计算机上运行"的根本途径是从"零"开始实现一个完整的计算机系统. 南京大学计算机科学与技术系 `计算机系统基础` 课程的小型项目 (Programming Assignment, PA)将提出 x86/mips32/riscv32(64)架构相应的教学版子集, 指导学生实现一个经过简化但功能完备的x86/mips32/riscv32(64)模拟器NEMU(NJU EMUlator), 最终在NEMU上运行游戏"仙剑奇侠传", 来让学生探究"程序在计算机上运行"的基本原理. NEMU受到了[QEMU](http://www.qemu.org/)的启发, 并去除了大量与课程内容差异较大的部分. PA包括一个准备实验(配置实验环境)以及5部分连贯的实验内容:

-   图灵机与简易调试器
-   冯诺依曼计算机系统
-   批处理系统
-   分时多任务
-   程序性能优化

## 实验环境

-   CPU架构: x64
-   操作系统: GNU/Linux
-   编译器: GCC
-   编程语言: C语言

##  [如何获得帮助](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/index.html#%E5%A6%82%E4%BD%95%E8%8E%B7%E5%BE%97%E5%B8%AE%E5%8A%A9)

在学习和实验的过程中, 你会遇到大量的问题. 除了参考课本内容之外, 你需要掌握如何获取其它参考资料.

但在此之前, 你需要适应查阅英文资料. 和以往程序设计课上遇到的问题不同, 你会发现你不太容易搜索到相关的中文资料. 回顾计算机科学层次抽象图, 计算机系统基础处于程序设计的下层. 这意味着, 懂系统基础的人不如懂程序设计的人多, 相应地, 系统基础的中文资料也会比程序设计的中文资料少.

如何适应查阅英文资料? 方法是<font color="#ff0000">尝试并坚持查阅英文资料</font>.

### 搜索引擎, 百科和问答网站

为了查找英文资料, 你应该使用下表中推荐的网站:

|            | 搜索引擎                                       | 百科                                                | 问答网站 |
| ---------- | ---------------------------------------------- | --------------------------------------------------- | -------- |
| 推荐使用   | [这里](https://dir.scmor.com/)有google搜索镜像 | [http://en.wikipedia.org](http://en.wikipedia.org/) |[http://stackoverflow.com](http://stackoverflow.com/) |
| 不推荐使用 | ~~[http://www.baidu.com](http://www.baidu.com/)~~  | ~~[http://baike.baidu.com](http://baike.baidu.com/)~~   | ~~[http://zhidao.baidu.com](http://zhidao.baidu.com/)~~ <br>~~[http://bbs.csdn.net](http://bbs.csdn.net/)~~ |

一些说明:

-   一般来说, 百度对英文关键词的处理能力比不上Google.
-   通常来说, 英文维基百科比中文维基百科和百度百科包含更丰富的内容. 为了说明为什么要使用英文维基百科, 请你对比词条`前束范式`分别在[百度百科](http://baike.baidu.com/view/143343.htm), [中文维基百科](http://zh.wikipedia.org/wiki/%E5%89%8D%E6%9D%9F%E8%8C%83%E5%BC%8F)和[英文维基百科](http://en.wikipedia.org/wiki/Prenex_normal_form)中的内容.
-   stackoverflow是一个程序设计领域的问答网站, 里面除了技术性的问题([What is ":-!!" in C code?](http://stackoverflow.com/questions/9229601/what-is-in-c-code/9229793))之外, 也有一些学术性([Is there a regular expression to detect a valid regular expression?](http://stackoverflow.com/questions/172303/is-there-a-regular-expression-to-detect-a-valid-regular-expression)) 和一些有趣的问题([What is the “-->” operator in C++?](https://stackoverflow.com/questions/1642028/what-is-the-operator-in-c)).

### 官方手册

官方手册包含了查找对象的所有信息, 关于查找对象的一切问题都可以在官方手册中找到答案. 通常官方手册的内容十分详细, 在短时间内通读一遍基本上不太可能, 因此你需要懂得"如何使用目录来定位你所关心的问题". 如果你希望寻找一些用于快速入门的例子, 你应该使用搜索引擎.

这里列出一些本课程中可能会用到的手册:

-   x86
    -   Intel 80386 Programmer's Reference Manual ([PDF](http://css.csail.mit.edu/6.858/2013/readings/i386.pdf))([HTML](https://nju-projectn.github.io/i386-manual/toc.htm))
    -   [System V ABI for i386](http://math-atlas.sourceforge.net/devel/assembly/abi386-4.pdf)
-   mips32
    -   MIPS32 Architecture For Programmers ([Volume I](http://www.cs.cornell.edu/courses/cs3410/2008fa/MIPS_Vol1.pdf), [Volume II](http://www.cs.cornell.edu/courses/cs3410/2008fa/MIPS_Vol2.pdf), [Volume III](http://www.cs.cornell.edu/courses/cs3410/2008fa/MIPS_Vol3.pdf))
    -   [System V ABI for mips32](http://math-atlas.sourceforge.net/devel/assembly/mipsabi32.pdf)
-   riscv32(64)
    -   The RISC-V Instruction Set Manual ([Volume I](https://github.com/riscv/riscv-isa-manual/releases/download/draft-20210813-7d0006e/riscv-spec.pdf), [Volume II](https://github.com/riscv/riscv-isa-manual/releases/download/draft-20210813-7d0006e/riscv-privileged.pdf))
    -   [ABI for riscv](https://github.com/riscv-non-isa/riscv-elf-psabi-doc)
-   ISA无关的手册
    -   [System V generic ABI](https://refspecs.linuxfoundation.org/elf/gabi41.pdf)
    -   [C99 Standard](http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)
    -   [GCC 10.3.0 Manual](https://gcc.gnu.org/onlinedocs/gcc-10.3.0/gcc.pdf)
    -   [GDB User Manual](https://sourceware.org/gdb/current/onlinedocs/gdb)
    -   [GNU Make Manual](http://www.gnu.org/software/make/manual/make.pdf)
    -   On-line Manual Pager (即man, [这里](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/man.html)有一个入门教程)

### GNU/Linux入门教程

jyy为我们准备了一些GNU/Linux入门教程, 如果你是第一次使用GNU/Linux, 请阅读以下材料

-   [流传自远古时代的OS实验课程网站中的Linux入门教程](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/linux.html)
-   [The Missing Semester of Your CS Education(墙裂推荐)](https://missing.csail.mit.edu/)