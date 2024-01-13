# 0 Manual

[Lab: Xv6 and Unix utilities (mit.edu)](https://pdos.csail.mit.edu/6.S081/2023/labs/util.html)
# 1 Question

- [ ] 为什么使用 `Ctrl-p` 可以显示每个进程的信息^[xv6 has no ps command, but, if you type Ctrl-p, the kernel will print information about each process. If you try it now, you'll see two lines: one for init, and one for sh.] 
- [ ] xv6 中文件描述符的定义在哪？换句话说，我应用程序中的 `write() ` 是如何通过系统调用并被 kernel 解析的呢？（xv6 和编译器的交互） ⏫ ^[在 PA 中，我们是通过定义了一个 ` file_table `，其中包含了 ` stdin `, ` stdout `, ` stderror `, 以及通过暴力拼接得到的 file 列表]
- [ ] xv6 中的文件重定向是如何实现的？
- [ ] **xv6 中 user 程序是如何加载的？首先，xv6 是如何运行 shell 的？shell 是不是第一个用户程序？程序运行是完成用户空间和内核空间的切换的？**⏫ 

# 2 Trace

## 2.1 sleep

>[!target] Implement a user-level `sleep` program for xv6, along the lines of the UNIX sleep command. Your `sleep` should pause for a user-specified number of ticks. A *tick* is a notion of time defined by the xv6 kernel, namely the time between two *interrupts* from the timer chip. Your solution should be in the file `user/sleep.c`.

```c
#include "kernel/types.h"
#include "user/user.h"
int
main(int argc, char *argv[]) 
{
  if (argc == 1) {
    printf("error, need a argument\n");
    exit(-1);
  }
  int t = atoi(argv[0]);
  sleep(t);
  exit(0);
}
```

虽然实现很简单，但是有几个需要注意的点
1. Add your sleep program to UPROGS in Makefile. 只有这样，我们的 Makefile 才会将 sleep 编译成可执行文件
2. See `kernel/sysproc.c` for the xv6 kernel code that implements the `sleep` system call (look for `sys_sleep`), `user/user.h` for the C definition of `sleep` callable from a user program, and `user/usys.S` for the assembler code that jumps from user code into the kernel for sleep.
	- 我们调用的是 `user/usys.S` 中的 sleep，他会通过 `ecall` 指令让我们进入内核代码
	- 在内核中实际执行的是 `sys_sleep`

# 3 Answer

## 3.2 应用程序中的 write 是如何通过系统调用被 kernel 解析的？

例如我们的 `echo.c` 程序
```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int
main(int argc, char *argv[])
{
  int i;

  for(i = 1; i < argc; i++){
    write(1, argv[i], strlen(argv[i]));
    if(i + 1 < argc){
      write(1, " ", 1);
    } else {
      write(1, "\n", 1);
    }
  }
  exit(0);
}
```

经过编译器编译后生成的汇编文件是这样的

```
user/_echo:     file format elf64-littleriscv
Disassembly of section .text:
0000000000000000 <main>:
#include "kernel/stat.h"
#include "user/user.h"
int
main(int argc, char *argv[])
...
...
...
    write(1, argv[i], strlen(argv[i]));
  32:	0004b903          	ld	s2,0(s1)
  36:	854a                	mv	a0,s2
  38:	00000097          	auipc	ra,0x0
  3c:	0ae080e7          	jalr	174(ra) # e6 <strlen>
  40:	0005061b          	sext.w	a2,a0
  44:	85ca                	mv	a1,s2
  46:	4505                	li	a0,1
  48:	00000097          	auipc	ra,0x0
  4c:	2e2080e7          	jalr	738(ra) # 32a <write>
...
...
000000000000032a <write>:
.global write
write:
 li a7, SYS_write
 32a:	48c1                	li	a7,16
 ecall
 32c:	00000073          	ecall
 ret
 330:	8082                	ret
```

- [ ] 此时 ecall 指令是如何与操作系统交互的，或者说 ecall 是如何跳转到内核的呢 #xv6/lec06
## 3.3 xv6 中的文件重定向是如何实现的？

```c
#include "kernel/types.h"
#include "user/user.h"
#include "kernel/fcntl.h"

// ex6.c: run a command with output redirected

int
main()
{
  int pid;

  pid = fork();
  if(pid == 0){
    close(1);
    // open 会返回当前进程未使用的最小文件描述符号
    open("out", O_WRONLY | O_CREATE | O_TRUNC); 

    char *argv[] = { "echo", "this", "is", "redirected", "echo", 0 };
    exec("echo", argv);
    printf("exec failed!\n");
    exit(1);
  } else {
    wait((int *) 0);
  }

  exit(0);
}
```

代码第 16 行一定会返回 1，这是因为第 14 行使用了 `close(1)` ， [[xv6中的open是如何实现的#1.2 why open always use the lowest num for fd|open 会返回当前进程未使用的最小文件描述序号]]。之后，文件描述符 1 则与文件 `out` 关联。


```ad-tip
title: 为什么要通过使用 fork 和 exec 来完成输入/输出的重定向
在 Linux 中，使用 `fork` 和 `exec` 来完成命令的重定向主要是为了保护父进程的环境，包括它的文件描述符和其他系统资源。这种做法遵循了操作系统中的一项基本原则，即进程隔离。下面解释为什么这么做：

1. **进程隔离与环境保护**：当你在父进程中直接进行重定向并执行另一个程序时，你会改变父进程的状态（例如，更改其标准输入、输出和错误的文件描述符）。这意味着父进程会失去对其原始输入和输出的控制。通过在子进程中进行重定向，父进程的环境保持不变，而所有更改只影响子进程。

2. **并发执行**：使用 `fork` 创建子进程允许父进程和子进程并发执行。父进程可以继续执行其他任务，甚至可以监控或控制多个这样的子进程。如果在父进程中直接更改文件描述符并执行另一个程序，则父进程的执行将被替换为新程序的执行，失去了并发性。

3. **安全性**：如果在父进程中进行重定向，需要在执行完毕后将文件描述符改回原来的状态。这增加了错误发生的可能性，例如在程序异常退出时可能无法恢复原状态。而在子进程中进行重定向，则不需要担心这个问题，因为子进程结束时，所有更改都会随之消失。

4. **简化错误处理**：如果新启动的程序执行失败，它不会影响到父进程的状态。在子进程中进行所有设置，然后执行新程序，意味着父进程可以在子进程失败时更容易地进行错误处理。

总之，使用 `fork` 和 `exec` 来处理重定向是一种更安全、更可靠且符合 Unix 哲学的做法。它保持了父进程的独立性和稳定性，同时提供了执行新程序的灵活性。
```