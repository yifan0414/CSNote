>[!chatgpt] core dump 是什么
>"Core dump" 是指计算机程序崩溃时，操作系统将程序在内存中的状态和数据保存到一个特殊文件中，以便开发人员进行调试和分析。这个文件通常称为"core dump"文件，也可以简称为"core"。
>
>"Core dump"包含了程序崩溃时的内存快照，包括程序计数器、寄存器状态、堆栈跟踪、堆和栈的内存内容以及其他相关信息。这些信息对于识别程序崩溃的原因以及修复程序中的错误非常有用。
>
>开发人员可以使用调试工具分析"core dump"文件，以确定程序在崩溃时的状态，查找错误的根本原因，并最终修复程序中的问题。这对于开发大型和复杂的软件应用程序尤其重要，因为它可以帮助开发人员识别和解决潜在的问题，提高软件的稳定性和可靠性。

测试如下：
![oLCtWp|500](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/oLCtWp.png)

默认情况下并不生成 core dump 的文件（保存了错误状态信息），以防止生成大量冗余文件，可以通过 `ulimit -a` 查看。

![e85XIw|500](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/e85XIw.png)

我们可以通过 `ulimit -c` 修改 `core file size` 这个值

![KT7jBI|500](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/KT7jBI.png)

还需要用到 `sudo sysctl -w kernel.core_pattern=core` 来修改 `/proc/sys/kernel/core_pattern` 的值。
![eDkozR](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/eDkozR.png)

![LimgQC](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/LimgQC.png)

此时就可以使用 gdb 进行调试了。