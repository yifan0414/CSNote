# Example

在 `am-kernel/test/cpu-tests/` 中执行下面的命令

```bash
make ARCH=x86-nemu ALL=dummy run -B | vim -
# -B是强制重新构建所有目标，即使它们似乎是最新的，因为我们在该文件夹
```

我们得到了一个 `Makefile.dummy` 文件

```bash
NAME = dummy
SRCS = tests/dummy.c
LIBS += klib
include /home/suyi/ics2020/abstract-machine/Makefile
```

可以看到我们包含了 `$(AM_HOME)/Makefile`，下面就是执行该 Makefile 的规则（注意我们传递的是 `run`）。

我们会依次进行下面的步骤

```txt
1. Building dummy-run [x86-nemu]
2. Building am-archive [x86-nemu] # 在 am 的递归 makefile 中
3. Building klib-archive [x86-nemu] # 在 klib 的递归 makefile 中
4. Creating image [x86-nemu]  # 在 nemu.mk 中
5. Building x86-nemu-interpreter # 在 nemu/Makefile 中

./build/x86-nemu-interpreter 
-b 
-l 
/home/suyi/ics2020/am-kernels/tests/cpu-tests/build/nemu-log.txt
/home/suyi/ics2020/am-kernels/tests/cpu-tests/build/dummy-x86-nemu.bin
--diff=/home/suyi/ics2020/nemu/tools/kvm-diff/build/x86-kvm-so 

```






# Makefile for AbstractMachine Kernels and Libraries

> [!quote]
> ### *Get a more readable version of this Makefile* by `make html` (requires python-markdown)
> 
> ~~~makefile
> html:
>     cat Makefile | sed 's/^\([^#]\)/    \1/g' | markdown_py > Makefile.html
> .PHONY: html
> ~~~
> 
> ~~~ad-chatgpt
> 这个Makefile的目标是创建一个HTML版本的Makefile，以使其更易于阅读。这可以通过`make html`命令来完成，并且需要有`python-markdown`库。具体来看：
> 
> 1. `html:`：定义了一个新的目标（也就是你希望`make`命令完成的任务），这个目标的名字是`html`。
> 
> 2. `cat Makefile | sed 's/^\([^#]\)/    \1/g' | markdown_py > Makefile.html`：这是一个命令管道，它的工作原理是这样的：
> 
>    - `cat Makefile`：将Makefile文件的内容打印到标准输出。
> 
>    - `sed 's/^\([^#]\)/    \1/g'`：这是`sed`命令，用于流编辑器。这里，它搜索每一行的开始不是`#`（也就是不是注释）的部分，并在这些部分前加上四个空格，这是Markdown语法中表示代码块的方式。
> 
>    - `markdown_py > Makefile.html`：最后，`markdown_py`命令将经过`sed`命令处理的Makefile的内容转换为HTML格式，并保存到`Makefile.html`文件中。
> 
> 3. `.PHONY: html`：`.PHONY`是一个特殊的目标，用于声明其他的目标是"假"的，也就是说，即使文件系统中存在一个名为`html`的文件，`make html`命令也会执行上面定义的`html`目标。如果没有这行，当`Makefile.html`文件存在时，`make html`命令就不会再重新生成它。
> 
> 总的来说，这个Makefile的目标是将Makefile文件转换为一个更易于阅读的HTML文件。在终端中运行`make html`，如果你的系统中已经安装了`python-markdown`，就会生成一个名为`Makefile.html`的文件，你可以在浏览器中打开它来查看。
> ~~~

## 1. Basic Setup and Checks

### Default to create a bare-metal kernel image

```makefile
ifeq ($(MAKECMDGOALS),)
  MAKECMDGOALS  = image
  .DEFAULT_GOAL = image
endif
```

这里的 `MAKECMDGOALS` 是由 `cpu-test` 中的 Makefile 传递过来的，如下图所示：

![uNDrOG](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/uNDrOG.png)

这里的意思是如果命令行未指定 `MAKECMDGOALS` 的值，那么默认是 img。这里决定了 nemu 的运行规则，在 `nemu.mk` 中定义

![CmA973](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/CmA973.png)

> [!quote]- Makefile中可以直接判断变量是否为空吗，需要预先定义吗
> 在 Makefile 中，你可以直接检查一个变量是否为空，无需预先定义。如果你尝试使用一个未定义的变量，Makefile 会把它当作一个空字符串处理。
> 
> 以下是一个例子：
> 
> ~~~Makefile
> ifeq ($(MY_VARIABLE),)
>     $(info MY_VARIABLE is empty)
> else
>     $(info MY_VARIABLE is not empty)
> endif
> ~~~
> 
> 在这个例子中，`ifeq ($(MY_VARIABLE),)` 检查 `MY_VARIABLE` 是否为空。如果它未定义或为空，那么 Makefile 就会打印 "MY_VARIABLE is empty"。否则，它就会打印 "MY_VARIABLE is not empty"。
> 
> 你可以通过命令行传入 `MY_VARIABLE` 的值来改变这个结果，如 `make MY_VARIABLE=test`。这将导致 Makefile 打印 "MY_VARIABLE is not empty"。
> 
> 注意，当比较字符串或者变量是否为空时，应该使用 `ifeq ($(VARIABLE),)` 或 `ifeq ("$(VARIABLE)","")`，而不是 `ifeq ($(VARIABLE),"")`，否则可能会产生错误的结果。例如，如果 `VARIABLE` 的值包含空格，`ifeq ($(VARIABLE),"")` 的结果将是假，尽管 `VARIABLE` 并不为空。

> [!chatgpt] MAKECMDGOALS是什么
> `MAKECMDGOALS` 是一个特殊变量，它标识了用户输入的 make 目标列表。在 Makefile 中，可以使用 `${MAKECMDGOALS}` 来引用用户输入的目标列表。
> 
> 比如，如果用户在终端输入了以下命令：
> 
> ~~~
> make target1 target2
> ~~~
> 
> 则 `${MAKECMDGOALS}` 的值就是 `target1 target2`，可以使用它来定义 Makefile 中的规则。例如：
> 
> ~~~
> all: ${MAKECMDGOALS}
> 
> ${MAKECMDGOALS}:
>     @echo "Building $@..."
> ~~~
> 
> 这样，运行上述 Makefile 文件，就会输出：
> 
> ~~~
> Building target1...
> Building target2...
> ~~~
> 

### Override checks when `make clean/clean-all/html`

```makefile
ifeq ($(findstring $(MAKECMDGOALS),clean|clean-all|html),)
```

> [!note]
> 如果 `$(MAKECMDGOALS)` 中包含 "clean"，"clean-all" 或 "html"，那么 `findstring` 函数会返回一个非空的结果（即，它会返回 "clean"，"clean-all" 或 "html"，取决于 `$(MAKECMDGOALS)` 中包含哪个），然后 `ifeq` 判断结果非空字符串与空字符串是否相等，结果为否，所以接下来的代码块不会被执行。

### Print build info message

```makefile
$(info # Building $(NAME)-$(MAKECMDGOALS) [$(ARCH)])
```

`NAME`、`MAKECMDGOALS` 和 `ARCH` 都是由 `cpu-test/Makefile` 传递而来

### Check: environment variable `$AM_HOME` looks sane

```makefile
ifeq ($(wildcard $(AM_HOME)/am/include/am.h),)
  $(error $AM_HOME must be an AbstractMachine repo)
endif
```

> [!note]
> 检查 `$AM_HOME` 是否存在，但是为什么要用 `am.h` 呢？

### Check: environment variable `$ARCH` must be in the supported list

```makefile
ARCHS = $(basename $(notdir $(shell ls $(AM_HOME)/scripts/*.mk)))
ifeq ($(filter $(ARCHS), $(ARCH)), )
  $(error Expected $ARCH in {$(ARCHS)}, Got "$(ARCH)")
endif
```

> [!command] $(shell ls $(AM_HOME)/scripts/*.mk)
> ![d0H2lm](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/d0H2lm.png)

> [!chatgpt]
> 这段代码主要是在检查 `$(ARCH)` 变量的值是否在特定的一组预定义的架构中。让我们逐行解析。
> 
> 1. `ARCHS = $(basename $(notdir $(shell ls $(AM_HOME)/scripts/*.mk)))`
> 
>    这行代码首先使用 `ls $(AM_HOME)/scripts/*.mk` 命令获取 `$(AM_HOME)/scripts/` 目录下所有 `.mk` 结尾的文件的列表。然后，`$(notdir ...)` 函数将所有文件的目录部分删除，只留下文件名。最后，`$(basename ...)` 函数将所有文件的扩展名 `.mk` 删除，只留下基本的文件名。
> 
>    举个例子，如果 `$(AM_HOME)/scripts/` 目录下有两个文件：`mips32-nemu.mk` 和 `x86-nemu.mk`，那么 `$(ARCHS)` 的值就会是 `mips32-nemu x86-nemu`。
> 
> 2. `ifeq ($(filter $(ARCHS), $(ARCH)), )`
> 
>    这行代码使用 `filter` 函数检查 `$(ARCH)` 的值是否在 `$(ARCHS)` 列表中。如果在，`filter` 函数会返回 `$(ARCH)` 的值；如果不在，`filter` 函数会返回一个空的结果。
> 
>    `ifeq ($(filter $(ARCHS), $(ARCH)), )` 语句检查 `filter` 函数的结果是否为空。如果结果为空（也就是说，`$(ARCH)` 的值不在 `$(ARCHS)` 列表中），那么下一行的 `error` 指令就会被执行。
> 
> 3. `$(error Expected $ARCH in {$(ARCHS)}, Got "$(ARCH)")`
> 
>    这行代码使用 `error` 指令显示一个错误消息，并停止 `make` 进程。错误消息是 `"Expected $ARCH in {$(ARCHS)}, Got "$(ARCH)""`，其中 `$ARCH` 和 `$(ARCHS)` 分别会被替换为它们的值。
> 
> 总的来说，这段代码的目的是检查 `$(ARCH)` 的值是否在 `$(AM_HOME)/scripts/` 目录下的 `.mk` 文件（不包括 `.mk` 扩展名）列表中。如果不在，就停止 `make` 进程，并显示一个错误消息。

### Extract instruction set architecture (`ISA`) and platform from `$ARCH`. Example: `ARCH=x86_64-qemu -> ISA=x86_64; PLATFORM=qemu`

```makefile
ARCH_SPLIT = $(subst -, ,$(ARCH))
ISA        = $(word 1,$(ARCH_SPLIT))
PLATFORM   = $(word 2,$(ARCH_SPLIT))
```

> [!chatgpt]
> 这段代码是在使用 `$(ARCH)` 变量来设定两个新的变量 `$(ISA)` 和 `$(PLATFORM)`。`$(ARCH)` 变量通常用于指定一个体系结构，它可能包含一些连字符（-）。这段代码的目的是分解 `$(ARCH)` 变量的值，并分别获取连字符前的部分（第一个词）和连字符后的部分（第二个词）。让我们来逐行看看。
> 
> 1. `ARCH_SPLIT = $(subst -, ,$(ARCH))`
> 
>    `$(subst -, ,$(ARCH))` 是一个 `subst` 函数，它会把 `$(ARCH)` 变量的值中的所有连字符 `-` 替换为空格。新的值被赋给 `ARCH_SPLIT` 变量。
> 
>    例如，如果 `$(ARCH)` 的值是 `mips32-nemu`，那么 `$(subst -, ,$(ARCH))` 的结果就是 `mips32 nemu`，这个结果会被赋给 `$(ARCH_SPLIT)`。
> 
> 2. `ISA = $(word 1,$(ARCH_SPLIT))`
> 
>    `$(word 1,$(ARCH_SPLIT))` 是一个 `word` 函数，它会获取 `$(ARCH_SPLIT)` 的第一个词（在这里，词是由空格分隔的）。新的值被赋给 `ISA` 变量。
> 
>    例如，如果 `$(ARCH_SPLIT)` 的值是 `mips32 nemu`，那么 `$(word 1,$(ARCH_SPLIT))` 的结果就是 `mips32`，这个结果会被赋给 `$(ISA)`。
> 
> 3. `PLATFORM = $(word 2,$(ARCH_SPLIT))`
> 
>    `$(word 2,$(ARCH_SPLIT))` 是一个 `word` 函数，它会获取 `$(ARCH_SPLIT)` 的第二个词。新的值被赋给 `PLATFORM` 变量。
> 
>    例如，如果 `$(ARCH_SPLIT)` 的值是 `mips32 nemu`，那么 `$(word 2,$(ARCH_SPLIT))` 的结果就是 `nemu`，这个结果会被赋给 `$(PLATFORM)`。
> 
> 所以，如果 `$(ARCH)` 的值是 `mips32-nemu`，那么经过这段代码后，`$(ISA)` 的值会是 `mips32`，`$(PLATFORM)` 的值会是 `nemu`。

### Checks end here

```makefile
endif
```

## 2. General Compilation Targets

### Create the destination directory (`build/$ARCH`)

```makefile
WORK_DIR  = $(shell pwd)
DST_DIR   = $(WORK_DIR)/build/$(ARCH)
$(shell mkdir -p $(DST_DIR))
```

### Compilation targets (image or archive)

```makefile
IMAGE_REL = build/$(NAME)-$(ARCH)
IMAGE     = $(abspath $(IMAGE_REL))
ARCHIVE   = $(WORK_DIR)/build/$(NAME)-$(ARCH).a
```

### Files to be linked: object files (`.o`) and libraries (`.a`)

```makefile
OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS))))
LIBS     := $(sort $(LIBS) am klib) # lazy evaluation ("=") causes infinite recursions
LINKAGE   = $(OBJS) \
  $(addsuffix -$(ARCH).a, $(join \
	$(addsuffix /build/, $(addprefix $(AM_HOME)/, $(LIBS))), \
	$(LIBS) \
))
```

> [!question]
> ~~~
> SRCS      = $(addprefix src/, $(AM_SRCS))
> OBJS      = $(addprefix $(DST_DIR)/, $(addsuffix .o, $(basename $(SRCS))))
> LIBS     := $(sort $(LIBS) am klib) # lazy evaluation ("=") causes infinite recursions
> LINKAGE   = $(OBJS) \
>   $(addsuffix -$(ARCH).a, $(join \
>     $(addsuffix /build/, $(addprefix $(AM_HOME)/, $(LIBS))), \
>     $(LIBS) \
> ))
> $(info SRCS = $(SRCS))
> -include $(AM_HOME)/scripts/nemu.mk
> $(info SRCS = $(SRCS))
> 其中nemu.mk定义了AM_SRCS := nemu/trm.c \
>            nemu/ioe/ioe.c \
> 为什么第一次$(info SRCS = $(SRCS)) 中 $(SRCS) 为空，第二次不为空
> ~~~
> 
> 这个问题与Makefile的变量延迟评估特性有关。在Makefile中，变量可以有两种赋值方式：立即赋值（使用 `:=`）和延迟赋值（使用 `=`）。
> 
> 当你使用单等号 `=` 进行赋值时，该变量的值会在它被引用的时候才进行评估，这就是所谓的延迟评估或者懒惰评估。这意味着如果你在定义变量的值的表达式中使用了其他变量，那么这些其他变量的值会在这个变量真正被使用时才求值。
> 
> 在你给出的Makefile代码片段中，变量 `SRCS` 的值取决于变量 `AM_SRCS` 的值，而你在定义 `SRCS` 时使用了 `=`，所以这是一个延迟评估的变量。
> 
> `nemu.mk` 在定义 `AM_SRCS` 的时候，使用了 `:=`，即立即评估。
> 
> 所以，在包含 `nemu.mk` 之前，变量 `AM_SRCS` 还没有定义，所以 `SRCS` 为空。在包含 `nemu.mk` 之后，`AM_SRCS` 被赋值，所以 `SRCS` 不再为空。这就解释了为什么第一次 `$(info SRCS = $(SRCS))` 打印的 `SRCS` 为空，而第二次不为空。
> 
> 如果希望 `SRCS` 在 `AM_SRCS` 定义之后立即更新，你需要使用 `:=` 进行赋值。


## 3. General Compilation Flags

### (Cross) compilers, e.g., mips-linux-gnu-g++

```makefile
AS        = $(CROSS_COMPILE)gcc
CC        = $(CROSS_COMPILE)gcc
CXX       = $(CROSS_COMPILE)g++
LD        = $(CROSS_COMPILE)ld
OBJDUMP   = $(CROSS_COMPILE)objdump
OBJCOPY   = $(CROSS_COMPILE)objcopy
READELF   = $(CROSS_COMPILE)readelf
```

### Compilation flags

```makefile
INC_PATH += $(WORK_DIR)/include $(addsuffix /include/, $(addprefix $(AM_HOME)/, $(LIBS)))
INCFLAGS += $(addprefix -I, $(INC_PATH))

CFLAGS   += -O2 -MMD -Wall -Werror -ggdb $(INCFLAGS) \
			-D__ISA__=\"$(ISA)\" -D__ISA_$(shell echo $(ISA) | tr a-z A-Z)__ \
			-D__ARCH__=$(ARCH) -D__ARCH_$(shell echo $(ARCH) | tr a-z A-Z | tr - _) \
			-D__PLATFORM__=$(PLATFORM) -D__PLATFORM_$(shell echo $(PLATFORM) | tr a-z A-Z | tr - _) \
			-DISA_H=\"$(ISA).h\" \
			-DARCH_H=\"arch/$(ARCH).h\" \
			-fno-asynchronous-unwind-tables -fno-builtin -fno-stack-protector \
			-Wno-main
CXXFLAGS +=  $(CFLAGS) -ffreestanding -fno-rtti -fno-exceptions
ASFLAGS  += -MMD $(INCFLAGS)

```
## 4. Arch-Specific Configurations

### Paste in arch-specific configurations (e.g., from `scripts/x86_64-qemu.mk`)

```makefile
-include $(AM_HOME)/scripts/$(ARCH).mk
```

## 5. Compilation Rules

### Rule (compile): a single `.c` -\> `.o` (gcc)

```makefile
$(DST_DIR)/%.o: %.c
	@mkdir -p $(dir $@) && echo + CC $<
	@$(CC) -std=gnu11 $(CFLAGS) -c -o $@ $(realpath $<)
```

### Rule (compile): a single `.cc` -\> `.o` (g++)

```makefile
$(DST_DIR)/%.o: %.cc
	@mkdir -p $(dir $@) && echo + CXX $<
	@$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)
```

### Rule (compile): a single `.cpp` -\> `.o` (g++)

```makefile
$(DST_DIR)/%.o: %.cpp
	@mkdir -p $(dir $@) && echo + CXX $<
	@$(CXX) -std=c++17 $(CXXFLAGS) -c -o $@ $(realpath $<)
```

### Rule (compile): a single `.S` -\> `.o` (gcc, which calls as)

```makefile
$(DST_DIR)/%.o: %.S
	@mkdir -p $(dir $@) && echo + AS $<
	@$(AS) $(ASFLAGS) -c -o $@ $(realpath $<)
```

### Rule (recursive make): build a dependent library (am, klib, \...)

```makefile
$(LIBS): %:
	@$(MAKE) -s -C $(AM_HOME)/$* archive
```

根据上面的 `LIBS := $(sort $(LIBS) am klib) # lazy evaluation ("=") causes infinite recursions` 可以得知 `$(LIBS) = [am, klib]`。
因此这里分别在 am 和 klib 中进行 make archive
```shell
make -s -C $(AM_HOME)/am archive

make -s -C $(AM_HOME)/klib archive
```

### Rule (link): objects (`*.o`) and libraries (`*.a`) -\> `IMAGE.elf`, the final ELF binary to be packed into image (ld)

```makefile
$(IMAGE).elf: $(OBJS) am $(LIBS)
	@echo + LD "->" $(IMAGE_REL).elf
	@$(LD) $(LDFLAGS) -o $(IMAGE).elf $(LINKAGE)
```

> [!chatgpt]- 为什么同时有 am 和 $(LIBS)
> 在这个Makefile规则中，`\$(OBJS) am \$(LIBS)` 是 `\$(IMAGE).elf`的依赖项，也就是说，只有当所有这些依赖项都被正确构建后，才会开始构建`\$(IMAGE).elf`。
> 
> 在这个规则中，`am`和`$(LIBS)`同时出现可能有两种原因。一种可能的原因是`am`库在构建过程中有特殊的地位，即使它已经包含在`$(LIBS)`中，但仍然单独列出来以强调它的重要性或保证它被优先构建。另一种可能的原因是这可能是一个错误或冗余，因为如果`am`已经在`$(LIBS)`中，那么就没有必要再单独列出。
> 
> 然而，这个Makefile规则的行为取决于如何定义和使用`$(LIBS)`。如果在定义`$(LIBS)`的时候没有包含`am`，那么`am`就需要单独列出来作为依赖项。反过来，如果在使用`$(LIBS)`的时候排除了`am`，那么在这个规则中就需要单独添加`am`。
> 
> 总的来说，`am`和`$(LIBS)`同时出现在这个Makefile规则的依赖项中，可能是为了强调`am`的重要性，也可能是因为在其他地方对`$(LIBS)`的定义或使用造成的冗余或错误。

### Rule (archive): objects (`*.o`) -\> `ARCHIVE.a` (ar)

```makefile
$(ARCHIVE): $(OBJS)
	@echo + AR "->" $(shell realpath $@ --relative-to .)
	@ar rcs $(ARCHIVE) $(OBJS)
```

### Rule (`#include` dependencies): paste in `.d` files generated by gcc on `-MMD`

```makefile
-include $(addprefix $(DST_DIR)/, $(addsuffix .d, $(basename $(SRCS))))
```

## 6. Miscellaneous

### Build order control

```makefile
image: image-dep
archive: $(ARCHIVE)
image-dep: $(OBJS) am $(LIBS)
	@echo \# Creating image [$(ARCH)]
.PHONY: image image-dep archive run $(LIBS)
```

### Clean a single project (remove `build/`)

```makefile
clean:
	rm -rf Makefile.html $(WORK_DIR)/build/
.PHONY: clean
```

### Clean all sub-projects within depth 2 (and ignore errors)

```makefile
CLEAN_ALL = $(dir $(shell find . -mindepth 2 -name Makefile))
clean-all: $(CLEAN_ALL) clean
$(CLEAN_ALL):
	-@$(MAKE) -s -C $@ clean
.PHONY: clean-all $(CLEAN_ALL)
```


# nemu.mk

```makefile
AM_SRCS := nemu/trm.c \
           nemu/ioe/ioe.c \
           nemu/ioe/timer.c \
           nemu/ioe/input.c \
           nemu/ioe/gpu.c \
           nemu/ioe/audio.c \
           nemu/isa/$(ISA)/cte.c \
           nemu/isa/$(ISA)/trap.S \
           nemu/isa/$(ISA)/vme.c \
           nemu/mpe.c \
           nemu/isa/$(ISA)/boot/start.S

CFLAGS    += -fdata-sections -ffunction-sections
LDFLAGS   += -L $(AM_HOME)/am/src/nemu/scripts
LDFLAGS   += -T $(AM_HOME)/am/src/nemu/isa/$(ISA)/boot/loader.ld
LDFLAGS   += --gc-sections -e _start
NEMUFLAGS += -b -l $(shell dirname $(IMAGE).elf)/nemu-log.txt $(IMAGE).bin
# 这是传递给 NEMU 的参数，可以把 -b 去掉来单步调试

CFLAGS += -DMAINARGS=\"$(mainargs)\"
CFLAGS += -I$(AM_HOME)/am/src/nemu/include
.PHONY: $(AM_HOME)/am/src/nemu/trm.c

image: $(IMAGE).elf
	@$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt
	@echo + OBJCOPY "->" $(IMAGE_REL).bin
	@$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin

run: image
	$(MAKE) -C $(NEMU_HOME) ISA=$(ISA) run ARGS="$(NEMUFLAGS)"

gdb: image
	$(MAKE) -C $(NEMU_HOME) ISA=$(ISA) gdb ARGS="$(NEMUFLAGS)"

```