# 本讲概述

> 就算理解了构建的过程，NEMU 代码依然很难读？

-   NEMU 代码导读
    -   浏览源代码
    -   启动代码选讲
    -   编辑器配置

# RTFSC

## 拿到源代码，先做什么？

> NEMU 对大部分同学来说是一个 “前所未有大” 的 project。

先大致了解一下

-   项目总体组织
    -   `tree` 要翻好几个屏幕
    -   `find . -name "*.c" -o -name "*.h"` (110+ 个文件)
-   项目规模

>[!command] 统计代码行数 
> ```bash
> find . -name "*.c" -o -name "*.h" | xargs cat | wc -l
> ```
> nemu: 5,000+ 行 (其实很小了)



## 尝试阅读代码：从 main 开始

C 语言代码，都是从 `main()` 开始运行的。那么<font color="#ff0000">哪里</font>才有 `main` 呢？

-   浏览代码：发现 `main.c`，估计在里面
-   使用 IDE (vscode: Edit → Find in files)
-  <font color="#ff0000">另外的方式?</font>
	- 在 main 上打一个断点, 然后使用调试器进行调试


**The UNIX Way (无须启动任何程序，直接查看)**

```shell
grep -n main $(find . -name "*.c") # 有太多噪声? 使用更为强大的regex
find . | xargs grep --color -nse '\<main\>'
```

>[!note] Unix中对话的方式
>使用正则表达式!


>[!tip] Unix中打开文件的方式
> 还在使用 `vim xx/xx/xx/xx/xxx.c` 来打开文件吗? 这样效率太低了! 试一试其他的选择
> -  `vim **/xxx.c` 可以直接通过命令行缓存打开文件
> - 使用 fzf 查找文件, 并通过 Unix 的方式打开他
> 	- `vim $(fzf)`

**Vim 当然也支持**

```vim
:vimgrep /\<main\>/ **/*.c
```

-   浏览 `:cn`, `:cp`, ...

>[!note] grep的由来
> g/re/p , 其中 g 是对于所有的行, re 代表 **r**egular **e**xpression, p 代表 print

## main()

比想象中短很多……

```c
int main(int argc, char *argv[]) {
  init_monitor(argc, argv);
  engine_start();
  return is_exit_status_bad();
}
```

Comments

-   把 argc, argv 传递给另一个函数是 C 的 idiomatic use
-   `init_monitor` 代码在哪里？
    -   每次都 grep 效率太低
    -   需要更先进的工具 (稍候介绍)

## [[parse_args()]]: 命令行工具的设计

>[!todo] Unix API 标准的设计
>大部分命令行工具的设计都是这样子的, 需要仔细回顾 #todo 

这个函数的名字起的很好，看了就知道要做什么

-   满足好代码不言自明的特性
    -   的确是用来解析命令行参数的，`-b`, `-l`, ...
    -   使用了 `getopt` → RTFM!

失败的尝试：`man getopt` → getopt (1)

成功的尝试

-   捷径版：STFW “C getopt” → 网页/博客/...
-   专业版：`man -k getopt` → `man 3 getopt`

>[!note] man 的用法
> - `man 1 xx`: 可执行程序或者shell命令
>- `man 2 xx`: **系统调用**（内核可以调用的函数，运行在核心态，内核空间，系统核心可直接呼叫的函数与工具等，通过这个，可以很方便的查到调用某个函数，需要加什么头文件，例如open,write函数）
>- `man 3 xx`: **库函数**（运行在用户态，用户空间，一些常用的函数与函数库,大部分为c的函数库，例如print,fread）
>- `man 4 xx`:  **特殊设备**（一般是/dev下的各种设备，例如硬盘设备，光盘等）
>- `man 5 xx`:  **文件格式**（说明这个文件中的各个字段的含义，例如/etc/passwd）
>- `man 6 xx`:  **游戏**（保留给游戏使用，由各个游戏自己定义）
>- `man 7 xx`:  杂项，例如Linux文件系统，网络协议等，变量说明等
>- `man 8 xx`:  系统管路员命令（只有管理员才能使用的命令，例如ifconfig，reboot等）
>- `man 9 xx`:  跟kernel内核有关的文件

意外之喜：man 还送了个例子！跟 `parse_args` 的用法一样耶

>[!question]
>为什么我们在启动 nemu 时没有使用这些选项呢?
>
>- 我们会怎样启动 nemu?
>	- `make run`
>- 但我们的框架代码给出了细节


## NEMU: 一个命令行工具

The friendly source code

-   命令行可以控制 NEMU 的行为
-  ![eWaaTO](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/eWaaTO.png)
-   我们甚至看到了 `--help` 帮助信息


如何让我们的 NEMU 打印它？

-   问题等同于：`make run` 到底做了什么
    -   方法 1: 阅读 Makefile
    -   方法 2: 借助 GNU Make 的 `-n` 选项


> 开始痛苦的代码阅读之旅：<font color="#ff0000">坚持！</font>

## 自动化测试的例子 #important
>[魔法时空门](https://www.bilibili.com/video/BV1qa4y1j7xk/?p=4&share_source=copy_web&vd_source=587965785c97101d90acb761204e6795&t=2009)


- 在做 OJ 时, 我们怎么测试我们的代码呢? 复制输入→测试→比对输出
	- 有没有更好的办法呢? 
- 在 PA1 中, 我们会频繁的测试我们的表达式求值, 这会造成一遍又一遍的输入样例.
	- 有没有更好的办法呢?

>[!note] Nemu是一个命令行工具
>命令行工具就意味着他可以和 Unix 世界中的其他工具进行 Unix 的独特操作: 管道, 重定向..
>
>Unix 中的程序都是从标准输入/输出

![46Atez](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/46Atez.png)

更进一步我们可以把标准输入输出重定向到文件中
```shell
./build/riscv32-nemu-interpreter < in.txt
```

这是一个小的脚本, 我们可以把他写进 make 中, 只需要添加额外一个 make 目标.

![2HDKBM](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/2HDKBM.png)

>[!danger] 工业界的测试
>这种自动化测试的作用不仅仅是为了减少浪费的时间, 更重要的是当我们为我们的项目添加了新的 feature 后, 我们还可以根据之前的自动化测试代码一键重新测试.


# 代码选讲
## static inline

```c
static inline void parse_args(int argc, char *argv[]) { ... }
```

`parse_args` 函数是 static, inline 的，这是什么意思？

-   inline (C99 6.7.4 #5): Making a function an inline function suggests that calls to the function be as fast as possible. The extent to which such suggestions are effective is implementation-defined. (inline更多有趣的行为请大家RTFM)
-   static (C99 6.2.2 #3): If the declaration of a file scope identifier for an object or a function contains the storage- class specifier **static**, the identifier has internal linkage.

联合使用

-   告诉编译器符号不要泄露到文件 (_translation unit_) 之外。

## 更多关于 static inline (1)
我们都知道，如果在两个文件里定义了重名的函数，能够分别编译，但链接会出错：
```c
/* a.c */ int f() { return 0; }
/* b.c */ int f() { return 1; }
```

b.c:(.text+0x0): multiple definition of <em>f</em>; a.c:(.text+0xb): first defined here


这也是为什么不在头文件里定义函数的原因

-   两个 translation unit 同时引用，就导致 multiple definition
-   思考题：为什么 C++ 能把 class 都定义到头文件里？？？像 `vector` 的实现就是直接粘贴进去的

## 更多关于 static inline (2)
如果你的程序较短且性能攸关，则可以使用 static inline 函数定义在头文件中。例子 (`**/x86/**/reg.h`)：

```c
static inline int check_reg_index(int index) {
  assert(index >= 0 && index < 8);
  return index;
}
```

`check_reg_index`完全可以单独放在一个 C 文件里，头文件中只保留声明：

```c
int check_reg_index(int index);
```

-   但这样会导致在编译时，编译出一条额外的 call 指令 (假设没有 [LTO](http://gcc.gnu.org/wiki/LinkTimeOptimization))
-   使用 inline 可以在调用 `check_reg_index(0)` 编译优化成<font color="#ff0000">零开销</font>

## 新的问题：啥是 assert？

```c
#define assert(cond) if (!(cond)) panic(...);
```

注意特殊情况：

```c
if (...) assert(0); // 上面的assert对么？
else ...
```

```c
#define assert(cond) \
  do { \
    if (!(cond)) { \
      fprintf(stderr, "Fail @ %s:%d", __FILE__, __LINE__); \
      exit(1); \
    } \
  } while (0)

#define assert(cond) ({ ... })
```

## 千辛万苦……
之后的历程似乎就比较轻松了。有些东西不太明白(比如 `init_device()`)，但好像也不是很要紧，到了 `welcome()`:

```c
static inline void welcome() {
  ...
  printf("Welcome to \33[1;41m\33[1;33m%s\33[0m-NEMU!\n",
    str(__ISA__)); // bad code! jyy doesn't like it.
}
```

哇，还能顺带打印出编译的时间日期，奇怪的知识又增加了！

-   初始化终于完成
-   啊……根本没碰到核心代码

# 理解代码：更进一步

## 来自同学的反馈

> “我决定挑战自己，坚持在命令行中工作、使用 Vim 编辑代码。但在巨多的文件之间切换真是一言难尽。”

上手以后还在用 grep 找代码？

-   你刚拿到项目的时候，grep 的确不错
-   但如果你要一学期在这个项目上，效率就太低了
    -   <font color="#ff0000">曾经有无数的同学选择容忍这种低效率</font>


## Vim: [这都搞不定还引发什么编辑器圣战](https://www.bilibili.com/video/BV13s41167z8)



Marks (文件内标记)

-   `ma`, `'a`, `mA`, `'A`, ...

Tags (在位置之间跳转)

-   `:jumps`, `C-]`, `C-i`, `C-o`, `:tjump`, ...

Tabs/Windows (管理多文件)

-   `:tabnew`, `gt`, `gT`, ...

Folding (浏览大代码)

-   `zc`, `zo`, `zR`, ...

更多的功能/插件

-   (RTFM, STFW)



## VSCode: 现代工具来一套？

刚拿到手，VSCode 的体验并不是非常好

-   满屏的红线/蓝线
    -   因为 Code 并知道 NEMU 是怎么编译的
    -   IDE “编译运行” 背后没有魔法

-   另一方面，这些东西一定是可以[[vscode configuration | 配置]]的
    -   配置解析选项: `c_cpp_properties.json`
        -   解锁正确的代码解析
    -   配置构建选项: `tasks.json`
        -   解锁 make (可跟命令行参数)
    -   配置运行选项: `launch.json`
        -   解锁单步调试 (我们并不非常推荐单步调试)

## 插入福利：调试 Segmentation Fault

听说你的程序又 Segmentation Fault 了？

-   ~~百度 Segmentation Fault 得到的首个回答的解释是完全错误的~~
-   正确的解释
    -   指令越权访问内存 (r/w/x)
        -   原因很多，数组越界、memory corruption, ...
    -   指令未被执行，进程收到 SIGSEGV 信号
        -   默认的信号处理程序会 core dump 退出

## 好的编辑器：也许不是万能的

`exec.c` 也太难读了吧 (~~元编程，害死人~~)

```c
static inline def_EHelper(gp1) { // ???
  ...
  EMPTY(0) 
    // EMPTY(idx)  =>  EX(idx, inv)
    // EX(idx, inv)  =>  EXW(idx, inv, 0)
    // !@%#&%^!#@&%!^@%#$%*^!#@*
}
```

产生 “这是什么操作” 的困惑：

-   办法 1: RTFM + RTFSC + 写小程序尝试
-   办法 2: 预编译以后的代码应该好理解！
    -   还记得我们对 Makefile 的导读吗？
        -   (说的容易做得难。直接 `gcc -E` 不是编译错误吗……)

## Don't Give Up Easy

我们既然知道 Makefile 里哪一行是 .o → .c 的转换

-   我们添一个一模一样的 `gcc -E` 是不是就行了？

```makefile
$(OBJ_DIR)/%.o: src/%.c
    @$(CC) $(CFLAGS) $(SO_CFLAGS) -c -o $@ $<
    @$(CC) $(CFLAGS) $(SO_CFLAGS) -E -MF /dev/null $< | \
      grep -ve '^#' | \
      clang-format - > $(basename $@).i
```

>敲黑板：征服你畏惧的东西，就会有意想不到的收获。

# 总结

## 怎样读代码？

读代码 ≠ “读” 代码

-   用正确的工具，使自己感到舒适
-   但这个过程本身可能是不太舒适的 (走出你的舒适区)
    -   我们看到太多的同学，到最后都没有学会使用编辑器/IDE
        -   <font color="#ff0000">要相信一切不爽都有办法解决</font>

信息来源

-   在 `/etc/hosts` 中屏蔽百度
-   去开源社区找 tutorials
    -   例子：[vim-galore](https://github.com/mhinz/vim-galore), [awesome-c](https://github.com/kozross/awesome-c)

# End.