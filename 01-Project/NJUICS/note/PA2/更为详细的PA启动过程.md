我们在 [[0 init_monitor结构]] 和 [[NEMU-Makefile]] 中详细分析了 NEMU 的启动过程。但这只是普通的 NEMU 启动过程，解释执行的的是程序内部的默认镜像文件（[[0 init_monitor结构#5 load_img]]），我们下面要分析的是给定镜像文件的 NEMU 启动过程。 

我们知道 PA 已经给出了大量的测试程序，在 `am-kernels/tests/cpu-tests/` 中  ([[2-2 RTFSC(2)#运行更多的程序]]），我们可以使用下面的命令执行这些程序：

```bash
make ARCH=$ISA-nemu ALL=xxx run
```

仅仅如此，我们并不清楚具体的细节，包括但不限于镜像文件的处理等。因此我们使用了分析 NEMU-Makefile 的同样的方法分析了`am-kernels/tests/cpu-tests/`中的 Makefile。

## 1 cpu-test 的 Makefile 分析（x86-nemu）

```makefile
.PHONY: all run clean latest $(ALL)

ALL = $(basename $(notdir $(shell find tests/. -name "*.c")))

all: $(addprefix Makefile., $(ALL))
	@echo "" $(ALL)

$(ALL): %: Makefile.%

Makefile.%: tests/%.c latest
	@/bin/echo -e "NAME = $*\nSRCS = $<\nLIBS += klib\ninclude $${AM_HOME}/Makefile" > $@
	-@make -s -f $@ ARCH=$(ARCH) $(MAKECMDGOALS)
	-@rm -f Makefile.$*

# cancel rules included by $(AM_HOME)/Makefile.check
image: ;
default $(MAKECMDGOALS): all ;

clean:
	rm -rf Makefile.* build/

latest:
```

```ad-command
~~~txt
❯ make ARCH=x86-nemu ALL=dummy run -n
/bin/echo -e "NAME = dummy\nSRCS = tests/dummy.c\nLIBS += klib\ninclude ${AM_HOME}/Makefile" > Makefile.dummy
make -s -f Makefile.dummy ARCH=x86-nemu run -nB
# -@rm -f Makefile.dummy
echo "" dummy
~~~
```

```ad-chatgpt
这是一个GNU make的Makefile文件，用于管理和自动化代码的编译、链接等过程。下面是对代码的详细解释：

- `.PHONY: all run clean latest $(ALL)`
	- 声明了几个伪目标，这些目标不会生成对应名称的文件，但可以作为make命令的参数使用。

- `ALL = $(basename $(notdir $(shell find tests/. -name "*.c")))`
	- 这行寻找`tests/`目录下所有的`.c`文件，然后提取出文件名（不包括目录），再去除`.c`后缀，结果保存在变量`ALL`中。

- `all: $(addprefix Makefile., $(ALL))`
	- 定义了一个目标`all`，它的依赖是变量`ALL`中的每个文件名前加上`Makefile.`前缀的文件。

- `$(ALL): %: Makefile.%`
	- 一个模式规则，定义了如何生成`ALL`中的每一个目标，这些目标依赖于对应的`Makefile.*`文件。

~~~ad-important
- `Makefile.%: tests/%.c latest`
	- 这是一个模式规则，其中 `%` 是一个通配符，它可以匹配任何字符串。此规则表明，如果存在一个 `Makefile.xxx` 文件，而且在 `tests/` 目录下也存在一个名为 `xxx.c` 的文件，且 `latest` 是最新的（即没有任何依赖项比它新），那么就可以执行后面的命令。

- `@/bin/echo -e "NAME = $*\nSRCS = $<\nLIBS += klib\ninclude $${AM_HOME}/Makefile" > $@`
	- 这个命令使用 `echo` 生成一个新的 Makefile 文件，文件名是当前目标（`$@`）。在这个新的 Makefile 中，`NAME` 被设置为当前模式的 `%` 部分（`$*`），`SRCS` 被设置为依赖项（`$<`，即 `tests/%.c`），`LIBS` 添加了一个库 `klib`，然后包含了一个位于 `$AM_HOME` 目录下的 Makefile。

- `-@make -s -f $@ ARCH=$(ARCH) $(MAKECMDGOALS)`
	- 使用生成的`Makefile.*`文件运行另一个make进程，`-s`参数使make进程静默运行，`-f`参数指定使用的Makefile文件，`$(ARCH)`和`$(MAKECMDGOALS)`是传递给新make进程的变量。
	- 这个命令执行 `make`，用新生成的 Makefile（`$@`）作为文件，并设置 `ARCH` 变量和目标。`-s` 参数使 `make` 在执行时不输出任何信息。`-f` 参数用于指定 Makefile 文件。

- `-@rm -f Makefile.$*`
	- 删除生成的`Makefile.*`文件。
~~~

- `image: ; default $(MAKECMDGOALS): all ;`
	- 定义了`image`和`default`目标，这两个目标没有命令和依赖，目的是取消在`$(AM_HOME)/Makefile.check`文件中定义的同名规则。

- `clean:`
	- 定义了`clean`目标，用于清理生成的文件，命令`rm -rf Makefile.* build/`将删除所有`Makefile.*`文件和`build/`目录。

- `latest:`
	- 定义了一个`latest`目标，没有提供命令或依赖，可能在其他地方使用。

```


通过上面的分析我们可以知道这个 Makefile 文件的主要目的是从 `tests/` 目录中找出所有的 `.c` 文件，并为每个 `.c` 文件生成一个对应的 Makefile，然后使用这个 Makefile 来编译和链接 `.c` 文件。这样可以方便地对多个 `.c` 文件进行并行编译，并且每个 `.c` 文件都可以有自己的编译和链接选项。因此我们可以把 `-@rm -f Makefile.$*` 注释掉来观察 `Makefile.$*` 的内容，如下图所示：

![EUbr1d](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/EUbr1d.png)

我们可以看到重点在第 4 行包含了 `abstract-machine` 的 Makefile。

为了更清晰的看到 Makefile 执行过程中发生了什么，我们在**child make** 命令后加入 `-nB` 选项

![QBvZqZ](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/QBvZqZ.png)

现在我们使用下面的命令删除掉 echo 和 mkdir 开头的行并传入 vim 中。

```bash
make ARCH=x86-nemu ALL=dummy run -B \
| grep -ve '^\(\#\|echo\|mkdir\)' \
| vim -
```

在 vim 中使用 `set nowrap` 得到下面的结果

![m8fQQf](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/m8fQQf.png)

### Building dummy-run

```bash
gcc -std=gnu11 -O2 -MMD -Wall -Werror -ggdb
 -I/home/suyi/ics2020/am-kernels/tests/cpu-tests/include
 -I/home/suyi/ics2020/abstract-machine/am/include/ 
 -I/home/suyi/ics2020/abstract-machine/klib/include/ 
 -D__ISA__=\"x86\" 
 -D__ISA_X86__ 
 -D__ARCH__=x86-nemu 
 -D__ARCH_X86_NEMU 
 -D__PLATFORM__=nemu 
 -D__PLATFORM_NEMU 
 -DISA_H=\"x86.h\" 
 -DARCH_H=\"arch/x86-nemu.h\" 
 -fno-asynchronous-unwind-tables
 -fno-builtin 
 -fno-stack-protector
 -Wno-main 
 -m32 
 -fno-pic 
 -fno-omit-frame-pointer
 -march=i386 
 -fcf-protection=none
 -mstringop-strategy=loop
 -fdata-sections
 -ffunction-sections 
 -DMAINARGS=\"\" 
 -I/home/suyi/ics2020/abstract-machine/am/src/nemu/include 
 -c -o 
 /home/suyi/ics2020/am-kernels/tests/cpu-tests/build/x86-nemu/tests/dummy.o
 /home/suyi/ics2020/am-kernels/tests/cpu-tests/tests/dummy.c
make -s -C /home/suyi/ics2020/abstract-machine/am archive
```

```ad-sq 
title: 自己的运行时环境
通过上面那么多的编译选项生成的 dummy.o 和直接在 Linux 平台上生成的 dummy.o 有什么不同？
```

### am 的静态库归档

```ad-chatgpt
title: make -s -C /home/suyi/ics2020/abstract-machine/am archive
这个命令是在 Linux 系统中使用的，它指示系统在路径 `/home/suyi/ics2020/abstract-machine/am` 中执行 `make` 命令并生成一个静态库文件 (`.a` 格式)。

- `-s` 参数会使 `make` 命令在执行时减少大量的输出信息，让输出更加简洁。
- `-C` 参数指定了 `make` 命令的工作目录。生成的静态库文件将包含在一个归档文件 (`.ar` 格式)中。

因此，这个命令的意思是将 `/home/suyi/ics2020/abstract-machine/am` 目录中的文件编译成一个静态库，并将静态库打包成一个归档文件。
```

下面是 building am-archive 的过程（删除了不必要的编译选项）

![l5GJt7](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/l5GJt7.png)

```ad-chatgpt
title: ar rcs 是什么意思
"ar rcs" 是一个Unix/Linux命令，它用于创建静态库文件。 

'r' 选项表示将模块插入到静态库文件中（或替换掉已有的同名模块），'c' 选项表示创建新的静态库文件， 's' 选项表示在插入之前对模块进行预处理，以便生成（可选的）符号表。

因此，ar rcs命令创建一个静态库，使得其成为归档文件，并在将文件添加到库中之前对目标文件进行符号表处理。
```


### klib 的静态库归档

![bX5da7](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/bX5da7.png)


### 链接&运行

![gKliRA](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/gKliRA.png)

```ad-chatgpt
title: 链接的过程
这是一个链接命令，用于将三个对象文件链接起来生成一个可执行文件：`/home/suyi/ics2020/am-kernels/tests/cpu-tests/build/dummy-x86-nemu.elf`。具体参数含义如下：

- `-melf_i386` 表示链接格式为 ELF i386
- `-L` 表示指定库文件搜索路径
- `-T` 指定链接脚本
- `--gc-sections` 表示删除不被引用的段，以减小可执行文件大小
- `-e` 表示指定链接时的入口地址
- `-o` 表示输出的可执行文件路径和名称
- 最后三个参数是要链接的三个对象文件（.o 文件）、am-x86-nemu 库文件和 klib-x86-nemu 库文件。
```

>[!abstract] 目的是什么 #todo
> 宏观来看，我们通过一系列的编译选项使得 `dummy.c -> dummy.o`，然后打包了两个待链接的静态库，最后通过链接脚本将这三者链接起来生成 `dummy.elf` 文件。那么我们为什么要这样做呢？目前我只知道两个静态库是为了提供更多的功能

后面的过程与 NEMU-Makefile 中类似。在这个过程中，我们可以看到静态库以及 `ELF` 文件的生成过程。


## 2 native 的启动过程

```ad-command
我们这次使用的是 `make ARCH=native SRC=dummy -B` 命令来观察 native 架构下的启动过程
```


### Building dummy.o

```bash
gcc
-std=gnu11
-O2
-MMD
-Wall
-Werror
-ggdb
-I/home/yifansu/ics2020/am-kernels/tests/cpu-tests/include
-I/home/yifansu/ics2020/abstract-machine/am/include/
-I/home/yifansu/ics2020/abstract-machine/klib/include/
-D__ISA__=\"native\"   //注意这里不同
-D__ISA_NATIVE__
-D__ARCH__=native
-D__ARCH_NATIVE
-D__PLATFORM__=
-D__PLATFORM_
-DISA_H=\"native.h\"
-DARCH_H=\"arch/native.h\"
-fno-asynchronous-unwind-tables
-fno-builtin
-fno-stack-protector
-Wno-main
-fpie
-c
-o
/home/yifansu/ics2020/am-kernels/tests/cpu-tests/build/native/tests/dummy.o
/home/yifansu/ics2020/am-kernels/tests/cpu-tests/tests/dummy.c
```

### am 的静态库归档

```makefile
### Rule (recursive make): build a dependent library (am, klib, ...)
$(LIBS): %:
	@$(MAKE) -s -C $(AM_HOME)/$* archive

archive: $(ARCHIVE)

### Rule (archive): objects (`*.o`) -> `ARCHIVE.a` (ar)
$(ARCHIVE): $(OBJS)
	@echo + AR "->" $(shell realpath $@ --relative-to .)
	@ar rcs $(ARCHIVE) $(OBJS)

AM_SRCS := native/trm.c \
           native/ioe.c \
           native/cte.c \
           native/trap.S \
           native/vme.c \
           native/mpe.c \
           native/platform.c \
           native/native-input.c \
           native/native-timer.c \
           native/native-gpu.c \
           native/native-audio.c \

CFLAGS  += -fpie
ASFLAGS += -fpie -pie
```

```bash
ar
rcs
/home/yifansu/ics2020/abstract-machine/am/build/am-native.a
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/trm.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/ioe.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/cte.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/trap.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/vme.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/mpe.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/platform.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/native-input.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/native-timer.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/native-gpu.o
/home/yifansu/ics2020/abstract-machine/am/build/native/src/native/native-audio.o
```


### klib 的静态库归档

![AYyum3](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/AYyum3.png)


### 链接&运行

```bash
g++
-pie
-o
/home/yifansu/ics2020/am-kernels/tests/cpu-tests/build/string-native
-Wl,--whole-archive
/home/yifansu/ics2020/am-kernels/tests/cpu-tests/build/native/tests/string.o
/home/yifansu/ics2020/abstract-machine/am/build/am-native.a
/home/yifansu/ics2020/abstract-machine/klib/build/klib-native.a
-Wl,-no-whole-archive
-lSDL2

/home/yifansu/ics2020/am-kernels/tests/cpu-tests/build/add-native ## 绝对路径直接执行
```

```ad-chatgpt
这个命令行语句使用的是g++编译器来链接生成一个可执行文件。具体来说，这个命令做了以下几件事情：

1. `g++`：这是C++的编译器，但在这里它被用来做链接操作。

2. `-pie`：这是一个编译器选项，它会生成一个位置无关的可执行文件（Position-Independent Executable），这样的文件可以被加载到内存的任何位置。

3. `-o /home/suyi/ics2020/am-kernels/tests/cpu-tests/build/string-native`：这个选项指定了输出的文件名和位置。

4. `-Wl,--whole-archive /home/suyi/ics2020/am-kernels/tests/cpu-tests/build/native/tests/string.o /home/suyi/ics2020/abstract-machine/am/build/am-native.a /home/suyi/ics2020/abstract-machine/klib/build/klib-native.a -Wl,-no-whole-archive`：这个选项用来链接对象文件和库。`-Wl,--whole-archive` 选项告诉链接器将之后的静态库文件中的所有对象文件都链接进来，直到遇到 `-Wl,-no-whole-archive` 为止。**即使这些对象文件中的某些符号没有被使用到。**

5. `-lSDL2`：这是一个库链接选项，用来链接名为 `SDL2` 的库。

所以这个命令的整体目标是链接指定的对象文件和库，生成一个位置无关的可执行文件。**特别注意的是📢，这里使用的是g++链接命令，与ld链接不同的是，其可以链接c++标准库。而ld是更底层的命令，可以通过链接脚本处理更为复杂的链接情况或者自制自己想要的链接文件**
```


```ad-chatgpt
title: 其中 klib-native.a 中实现了自己库函数，那么这个编译命令是调用自己的库函数还是调用glibc的库函数
这个链接命令会优先链接你的`klib-native.a`中的函数，只有当需要的函数在你的库中找不到时，才会去链接glibc中的函数。

原因如下：链接器在解析符号时，会按照它们在命令行中出现的顺序进行。当链接器遇到一个未解析的符号时，它会查找在此符号之后出现的库中是否有相应的符号。如果在后面的库中找到了这个符号，链接器就会使用这个符号的定义。如果在后面的库中找不到这个符号，链接器就会报错。

在你的命令中，`-Wl,--whole-archive`告诉链接器，`am-native.a`和`klib-native.a`中的所有对象文件都会被链接到最终的可执行文件中。因此，你的库函数会被优先链接，只有当你的库中找不到所需的函数时，链接器才会去链接glibc中的函数。
```