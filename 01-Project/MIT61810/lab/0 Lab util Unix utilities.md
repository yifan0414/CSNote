# 0 Manual

[Lab: Xv6 and Unix utilities (mit.edu)](https://pdos.csail.mit.edu/6.S081/2023/labs/util.html)
# 1 Question

- [ ] 为什么使用 `Ctrl-p` 可以显示每个进程的信息^[xv6 has no ps command, but, if you type Ctrl-p, the kernel will print information about each process. If you try it now, you'll see two lines: one for init, and one for sh.] 
- [ ] xv6 中文件描述符的定义在哪？换句话说，我应用程序中的 `write() ` 是如何通过系统调用并被 kernel 解析的呢？（xv6 和编译器的交互） ⏫ ^[在 PA 中，我们是通过定义了一个 ` file_table `，其中包含了 ` stdin `, ` stdout `, ` stderror `, 以及通过暴力拼接得到的 file 列表]
- [x] xv6 中的文件重定向是如何实现的？ ✅ 2024-01-14
- [ ] **xv6 中 user 程序是如何加载的？首先，xv6 是如何运行 shell 的？shell 是不是第一个用户程序？程序运行是完成用户空间和内核空间的切换的？** ⏫
- [ ] 为什么每次 make clean 会清除创建的文件
# 2 Trace

## 2.1 sleep

>[!target] 
>Implement a user-level `sleep` program for xv6, along the lines of the UNIX sleep command. Your `sleep` should pause for a user-specified number of ticks. A *tick* is a notion of time defined by the xv6 kernel, namely the time between two *interrupts* from the timer chip. Your solution should be in the file `user/sleep.c`.

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
	- 在内核中实际执行的是 `sys_sleep`，执行顺序在 #xv6/lec06 
	
## 2.2 pingpong

> [!target]
> Write a user-level program that uses xv6 system calls to ''ping-pong'' a byte between two processes over a pair of pipes, one for each direction. The parent should send a byte to the child; the child should print "<pid>: received ping", where <pid> is its process ID, write the byte on the pipe to the parent, and exit; the parent should read the byte from the child, print "<pid>: received pong", and exit. Your solution should be in the file `user/pingpong.c`.

```c
#include "kernel/types. h"
#include "user/user. h"
int
main (int argc, char* argv[])
{
  int pid;
  char buf[100];
  int fds[2];

  pipe (fds);

  pid = fork ();

  if (pid == 0) {
    // child process
    write (fds[1], "1", 1);
    printf ("%d: received ping\n", getpid ());
  } else {
    wait (0);
    read (fds[0], buf, 1);
    printf ("%d: received pong\n", getpid ());
  }

  exit (0);
}
```

- 值得注意的是父进程要等待子进程完成 wrtie 后再 read，否则将会输出错序

## 2.3 primes 🌟

> [!target]
> Write a concurrent prime sieve program for xv6 using pipes and the design illustrated in the picture halfway down [this page](http://swtch.com/~rsc/thread/) and the surrounding text. This idea is due to Doug McIlroy, inventor of Unix pipes. Your solution should be in the file user/primes. c.

![image.png | 700](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/20240114153742.png)


```c
#include "kernel/types. h"
#include "user/user. h"


void sieve (int left_fd) {
    int prime;
    if (read (left_fd, &prime, sizeof (prime))) {
        printf ("prime %d\n", prime);
        int right_fd[2];
        pipe (right_fd);
        if (fork () == 0) {
            close (right_fd[1]);
            sieve (right_fd[0]);
        } else {
            int num;
            while (read (left_fd, &num, sizeof (num))) {
                if (num % prime != 0) {
                    write (right_fd[1], &num, sizeof (num));
                }
            }
            close (right_fd[1]);
        }
    }
    close (left_fd);
}

int main () {
    int fd[2];
    pipe (fd);
    if (fork () == 0) {
        close (fd[1]);
        sieve (fd[0]);
    } else {
        close (fd[0]); // 关闭父进程的读端
        for (int i = 2; i != 36; i++) {
            write (fd[1], &i, sizeof (i));
        }
        close (fd[1]);
    }
    wait (0); // 等待所有子进程结束
    exit (0);
}
```
1. **一个进程 B 需要从与父进程 A 的 pipe 中读出数据，需要与其子进程 C 的 pipe 中写数据**
2. HINT: 只有当管道的写入端关闭时，read 返回零。
	- 如果不关闭写端的话，则会造成死循环

### 2.3.1 不关闭写端
```c
#include "kernel/types. h"
#include "user/user. h"


void sieve (int left_fd) {
    int prime;
    if (read (left_fd, &prime, sizeof (prime))) {
        if (fork () == 0) {
            // close (right_fd[1]); // 保证关闭所有的写端
            sieve (right_fd[0]);
        }
    }
}

int main () {
    if (fork () == 0) {
        // close (fd[1]);
        sieve (fd[0]);
    }
}
```

![image.png|600](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/20240114163317.png)

> [!chatgpt]-
> 程序陷入死循环并持续输出 "prime 0" 的原因在于管道的写端没有被及时关闭，导致 `read` 函数无法正确地检测到管道末尾（EOF），进而无法退出读取循环。让我们详细分析下代码中的关键部分：
> 
> - 关于 `sieve` 函数
> 
> 在 `sieve` 函数中，您注释掉了子进程中关闭写端管道的代码 (`close (right_fd[1])`)。这意味着即使父进程已经完成了写入并关闭了它的写端，子进程中的写端仍然是打开的。由于管道的写端没有完全关闭（即在所有进程中都关闭），`read` 函数将不会返回 0 来指示管道末尾，即使没有更多的数据可读。
> 
> * 关于 `main` 函数
> 
> 在 `main` 函数中，您也注释掉了父进程中关闭读端管道的代码 (`close (fd[0])`)。通常，这个操作不是必需的，因为父进程只负责写入数据。但是，关键在于子进程中相应的写端需要被关闭。
> 
> * 结果
> 
> 由于在 `sieve` 函数的递归调用中，每个子进程都保持着它的写端打开，这就造成了一个情况：`read` 函数在等待可能永远不会到来的数据，因为它预期管道的写端最终会关闭。然而，由于写端从未关闭，`read` 函数继续等待数据，导致程序无法正常退出循环。
> 
> 当 `read` 在管道中不再有新数据时返回 0 字节，意味着它已经读到了管道末尾。但在您的代码中，由于写端一直开着，`read` 始终等待新数据，导致它一直在读取状态，即使实际上没有数据。这可能导致它读取到未初始化的内存，或者简单地返回一个不正确的值（如 0），这就是为什么程序一直输出 "prime 0"。
> 
> * 解决方法
> 
> 要解决这个问题，您需要确保每个子进程在不需要写入数据时关闭其写端文件描述符。这将允许 `read` 函数正确地接收到 EOF 信号，从而避免死循环。即，在 `sieve` 函数中取消注释 `close (right_fd[1])`，确保每个递归调用的子进程都关闭了它们不需要的写端。

- [ ] 为什么最后会出现 `usertrap` 错误 #xv6 

## 2.4 find（涉及到文件系统）

>[!target]
>Write a simple version of the UNIX find program for xv6: find all the files in a directory tree with a specific name. Your solution should be in the file user/find.c.

- Look at [[xv6中的ls|user/ls. c]] to see how to read directories.
- Use **recursion** to allow find to descend into sub-directories.
- **Don't recurse into "." and "..".**
- Changes to the file system persist across runs of qemu; to get a clean file system run `make clean` and then `make qemu`. #xv6/todo why?
- You'll need to use C strings. Have a look at K&R (the C book), for example Section 5.5.
- Note that == does not compare strings like in Python. Use `strcmp()` instead.
- Add the program to UPROGS in Makefile.

```c
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fs.h"
#include "kernel/fcntl.h"

void
find(char* path, char* filename)
{
  int fd;
  struct dirent de;
  struct stat st;

  char* p;

  if((fd = open(path, O_RDONLY)) < 0){
    fprintf(2, "ls: cannot open %s\n", path);
    return;
  }

  if(fstat(fd, &st) < 0){
    fprintf(2, "ls: cannot stat %s\n", path);
    close(fd);
    return;
  }
  
  if (st.type != T_DIR) exit(-1);

  p = path + strlen(path);
  *p++ = '/';
  
  while (read(fd, &de, sizeof(de)) == sizeof(de)) {
    if (de.inum == 0 || strcmp(de.name, ".") == 0 || strcmp(de.name, "..") == 0) 
      continue;

    memmove(p , de.name, sizeof(de.name));
    p[sizeof(de.name)] = 0;

    if (stat (path, &st) < 0){
      printf("find: cannot stat %s\n", path);
      continue;
    }
    if (st.type == T_FILE && strcmp(de.name, filename) == 0) {
      printf("%s\n", path);
    } else if (st.type == T_DIR) {
      find(path, filename);
    }
  }


  close(fd);

}

int 
main(int argc, char* argv[]) 
{
  if (argc != 3) {
    printf("argument error\n");
    exit(-1);
  }
  
  char buf[512];
  strcpy(buf, argv[1]);
  // find . b
  find(buf, argv[2]);
  
  exit(0);
}
```

## 2.5 xargs

> [!target]
> Write a simple version of the UNIX xargs program for xv6: its arguments describe a command to run, it reads lines from the standard input, and it runs the command for each line, appending the line to the command's arguments. Your solution should be in the file user/xargs.c.

The following example illustrates xarg's behavior:

							  
### 2.5.1 关于 cat 的命令
![image.png|300](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/20240114225901.png)

而 cat 的实现是这样的

```c file:cat.c
#include "kernel/types. h"
#include "kernel/stat. h"
#include "kernel/fcntl. h"
#include "user/user. h"

char buf[512];

void cat(int fd) {
  int n;
  while((n = read (fd, buf, sizeof(buf))) > 0) {
    if (write (1, buf, n) != n) {
      fprintf (2, "cat: write error\n");
      exit (1);
    }
  }
  if (n < 0){
    fprintf (2, "cat: read error\n");
    exit (1);
  }
}

int main (int argc, char *argv[]) {
  int fd, i;

  if (argc <= 1){
    cat (0);
    exit (0);
  }

  for (i = 1; i < argc; i++){
    if ((fd = open(argv[i], O_RDONLY)) < 0){
      fprintf (2, "cat: cannot open %s\n", argv[i]);
      exit (1);
    }
    cat (fd);
    close(fd);
  }
  exit (0);
}
```

也就是对于 cat 来说，其并不知道 pipe 和重定向，这一切都是由 shell 做的。因此我们在实现 xargs 时，也不必关系前面命令的输出是什么，我们只需知道从管道中读就行了

### 2.5.2 HINT

要求实现的功能举例如下：

```
    $ echo hello too | xargs echo bye
    bye hello too
    $
```

```
    $ (echo 1 ; echo 2) | xargs echo
    1
    2
    $
```

### 2.5.3 code

```c
#include "kernel/types. h"
#include "user/user. h"
#include "kernel/param. h"

int
main (int argc, char* argv[])
{
  // left | right
  // 从标准输入中读取 left
  char* args[MAXARG];
  char  buf[MAXPATH];
  memset (args, 0, sizeof (args));
  for (int i = 1; i < argc; i++) {
    args[i - 1] = argv[i];
  }
  args[argc - 1] = buf;
  // 构建 char* args[] = {"echo", "b", "buf", NULL};
  int pid;
  while (1) {
    for (int j = 0; j < MAXPATH; j++) {
      if (read (0, &buf[j], 1) != 1) {
        goto quit;
      }
      if (buf[j] == '\n' || buf[j] == '\r') {
        buf[j] = 0;
        break;
      }
    }
    pid = fork ();
    if (pid == 0) {
      exec (args[0], args); // 对于 left 的每一行，都创建一个子进程执行
    } else {
      wait (0);
    }
  }

quit:

  exit (0);
}
```


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

代码第 16 行一定会返回 1，这是因为第 14 行使用了 `close(1)` ， [[xv6中的open#1.2 why open always use the lowest num for fd|open 会返回当前进程未使用的最小文件描述序号]]。之后，文件描述符 1 则与文件 `out` 关联。


> [!tip] 为什么要通过使用 fork 和 exec 来完成输入/输出的重定向
> 在 Linux 中，使用 `fork` 和 `exec` 来完成命令的重定向主要是为了保护父进程的环境，包括它的文件描述符和其他系统资源。这种做法遵循了操作系统中的一项基本原则，即进程隔离。下面解释为什么这么做：
> 
> 1. **进程隔离与环境保护**：当你在父进程中直接进行重定向并执行另一个程序时，你会改变父进程的状态（例如，更改其标准输入、输出和错误的文件描述符）。这意味着父进程会失去对其原始输入和输出的控制。通过在子进程中进行重定向，父进程的环境保持不变，而所有更改只影响子进程。
> 
> 2. **并发执行**：使用 `fork` 创建子进程允许父进程和子进程并发执行。父进程可以继续执行其他任务，甚至可以监控或控制多个这样的子进程。如果在父进程中直接更改文件描述符并执行另一个程序，则父进程的执行将被替换为新程序的执行，失去了并发性。
> 
> 3. **安全性**：如果在父进程中进行重定向，需要在执行完毕后将文件描述符改回原来的状态。这增加了错误发生的可能性，例如在程序异常退出时可能无法恢复原状态。而在子进程中进行重定向，则不需要担心这个问题，因为子进程结束时，所有更改都会随之消失。
> 
> 4. **简化错误处理**：如果新启动的程序执行失败，它不会影响到父进程的状态。在子进程中进行所有设置，然后执行新程序，意味着父进程可以在子进程失败时更容易地进行错误处理。
> 
> 总之，使用 `fork` 和 `exec` 来处理重定向是一种更安全、更可靠且符合 Unix 哲学的做法。它保持了父进程的独立性和稳定性，同时提供了执行新程序的灵活性。