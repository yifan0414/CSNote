# 源文件
```makefile
NAME = nemu

ISA ?= x86 
# ?= 是 Makefile 中的一个操作符，它的意思是，如果这个变量没有被定义过，
# 那么就赋值为等号后面的内容。如果变量已经定义了，那么就沿用之前的值不变。
ISAS = $(shell ls src/isa/)
ifeq ($(filter $(ISAS), $(ISA)), ) # ISA must be valid
$(error Invalid ISA. Supported: $(ISAS))
endif

ENGINE ?= interpreter
ENGINES = $(shell ls src/engine/)
ifeq ($(filter $(ENGINES), $(ENGINE)), ) # ENGINE must be valid
$(error Invalid ENGINE. Supported: $(ENGINES))
endif

$(info Building $(ISA)-$(NAME)-$(ENGINE))
# 向命令行中输出信息

INC_DIR += ./include ./src/engine/$(ENGINE)
BUILD_DIR ?= ./build

ifdef SHARE
SO = -so
SO_CFLAGS = -fPIC -D_SHARE=1
SO_LDLAGS = -shared -fPIC
else
# 通过下面的分析, 暂时走的这个路
LD_LIBS = -lSDL2 -lreadline -ldl
endif

ifndef SHARE
DIFF ?= kvm
ifneq ($(ISA),x86)
ifeq ($(DIFF),kvm)
DIFF = qemu
$(info KVM is only supported with ISA=x86, use QEMU instead)
endif
endif

ifeq ($(DIFF),qemu)
DIFF_REF_PATH = $(NEMU_HOME)/tools/qemu-diff
DIFF_REF_SO = $(DIFF_REF_PATH)/build/$(ISA)-qemu-so
CFLAGS += -D__DIFF_REF_QEMU__
else ifeq ($(DIFF),kvm)
DIFF_REF_PATH = $(NEMU_HOME)/tools/kvm-diff
DIFF_REF_SO = $(DIFF_REF_PATH)/build/$(ISA)-kvm-so
CFLAGS += -D__DIFF_REF_KVM__
else ifeq ($(DIFF),nemu)
DIFF_REF_PATH = $(NEMU_HOME)
DIFF_REF_SO = $(DIFF_REF_PATH)/build/$(ISA)-nemu-interpreter-so
CFLAGS += -D__DIFF_REF_NEMU__
MKFLAGS = ISA=$(ISA) SHARE=1 ENGINE=interpreter
else
$(error invalid DIFF. Supported: qemu kvm nemu)
endif
endif

# 这段代码是用GNU make工具编写的，它是一种自动构建工具，可以解析Makefile文件来自动化软件编译和测试过程。下面是对这段代码的解释：

# 这段代码首先检查是否定义了名为`SHARE`的变量，如果没有定义（`ifndef SHARE`），那么就会执行括号内的代码。

# - 这里首先设置一个默认的`DIFF`值为`kvm`，这是假设没有明确设置`DIFF`的情况下的默认值。

# - 接下来，如果`ISA`不是`x86`，并且`DIFF`被设置为`kvm`，那么将`DIFF`设置为`qemu`，并输出信息"KVM is only supported with ISA=x86, use QEMU instead"，表明只有在`ISA`是`x86`的情况下才支持使用`kvm`，否则建议使用`qemu`。

# - 在之后的代码中，根据`DIFF`的值分别设定`DIFF_REF_PATH`，`DIFF_REF_SO`以及`CFLAGS`的值。这里主要处理了三种情况，即`DIFF`为`qemu`、`kvm`、`nemu`的情况。

# - 最后，如果`DIFF`的值不在`qemu`、`kvm`、`nemu`这三个中，那么将会触发一个错误，错误信息为："invalid DIFF. Supported: qemu kvm nemu"，表示`DIFF`的值不正确，只支持`qemu`、`kvm`、`nemu`这三种。

# 这段代码的主要作用是根据不同的设定来设定不同的编译参数。如果你使用了不支持的选项，那么这段代码就会引发错误。

OBJ_DIR ?= $(BUILD_DIR)/obj-$(ISA)-$(ENGINE)$(SO)
BINARY ?= $(BUILD_DIR)/$(ISA)-$(NAME)-$(ENGINE)$(SO)

include Makefile.git

.DEFAULT_GOAL = app

# Compilation flags
CC = gcc
LD = gcc
INCLUDES  = $(addprefix -I, $(INC_DIR))
CFLAGS   += -O2 -MMD -Wall -Werror -ggdb3 $(INCLUDES) \
            -D__ENGINE_$(ENGINE)__ \
            -D__ISA__=$(ISA) -D__ISA_$(ISA)__ -D_ISA_H_=\"isa/$(ISA).h\"

# Files to be compiled
SRCS = $(shell find src/ -name "*.c" | grep -v "isa\|engine")
SRCS += $(shell find src/isa/$(ISA) -name "*.c")
SRCS += $(shell find src/engine/$(ENGINE) -name "*.c")
OBJS = $(SRCS:src/%.c=$(OBJ_DIR)/%.o)

# Compilation patterns 最重要的部分
# 对于每一个 .o 我们都如此执行
$(OBJ_DIR)/%.o: src/%.c
	@echo + CC $<
	@mkdir -p $(dir $@)
	@$(CC) $(CFLAGS) $(SO_CFLAGS) -c -o $@ $<


# Depencies
-include $(OBJS:.o=.d)

# Some convenient rules

.PHONY: app run gdb clean run-env $(DIFF_REF_SO)
app: $(BINARY)

override ARGS ?= --log=$(BUILD_DIR)/nemu-log.txt
override ARGS += --diff=$(DIFF_REF_SO)

# Command to execute NEMU
IMG :=
NEMU_EXEC := $(BINARY) $(ARGS) $(IMG)

$(BINARY): $(OBJS)
	$(call git_commit, "compile")
	@echo + LD $@
	@$(LD) -O2 -rdynamic $(SO_LDLAGS) -o $@ $^ $(LD_LIBS)

run-env: $(BINARY) $(DIFF_REF_SO)

run: run-env
	$(call git_commit, "run")
	$(NEMU_EXEC)

gdb: run-env
	$(call git_commit, "gdb")
	gdb -s $(BINARY) --args $(NEMU_EXEC)

$(DIFF_REF_SO):
	$(MAKE) -C $(DIFF_REF_PATH) $(MKFLAGS)

clean:
	-rm -rf $(BUILD_DIR)
	$(MAKE) -C tools/gen-expr clean
	$(MAKE) -C tools/qemu-diff clean
	$(MAKE) -C tools/kvm-diff clean
```

# make过程中的信息
通过使用 `make -nB` 查看make过程中的信息
这里使用的是 `make -nB | sed G` 为每一个行后添加空白行

>[!note] 同样的，我们可以使用 `make run -nB` 查看运行参数
> ![VCks6c](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/VCks6c.png) ^tdabqo


```shell hl:echo
Building x86-nemu-interpreter

echo + CC src/monitor/debug/ui.c

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/debug/ui.o src/monitor/debug/ui.c

echo + CC src/monitor/debug/watchpoint.c

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/debug/watchpoint.o src/monitor/debug/watchpoint.c

echo + CC src/monitor/debug/log.c

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/debug/log.o src/monitor/debug/log.c

echo + CC src/monitor/debug/expr.c

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/debug/expr.o src/monitor/debug/expr.c

echo + CC src/monitor/monitor.c

mkdir -p build/obj-x86-interpreter/monitor/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/monitor.o src/monitor/monitor.c

echo + CC src/monitor/difftest/dut.c

mkdir -p build/obj-x86-interpreter/monitor/difftest/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/difftest/dut.o src/monitor/difftest/dut.c

echo + CC src/monitor/cpu-exec.c

mkdir -p build/obj-x86-interpreter/monitor/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/monitor/cpu-exec.o src/monitor/cpu-exec.c

echo + CC src/main.c

mkdir -p build/obj-x86-interpreter/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/main.o src/main.c

echo + CC src/memory/paddr.c

mkdir -p build/obj-x86-interpreter/memory/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/memory/paddr.o src/memory/paddr.c

echo + CC src/device/device.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/device.o src/device/device.c

echo + CC src/device/alarm.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/alarm.o src/device/alarm.c

echo + CC src/device/serial.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/serial.o src/device/serial.c

echo + CC src/device/vga.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/vga.o src/device/vga.c

echo + CC src/device/intr.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/intr.o src/device/intr.c

echo + CC src/device/keyboard.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/keyboard.o src/device/keyboard.c

echo + CC src/device/io/port-io.c

mkdir -p build/obj-x86-interpreter/device/io/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/io/port-io.o src/device/io/port-io.c

echo + CC src/device/io/map.c

mkdir -p build/obj-x86-interpreter/device/io/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/io/map.o src/device/io/map.c

echo + CC src/device/io/mmio.c

mkdir -p build/obj-x86-interpreter/device/io/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/io/mmio.o src/device/io/mmio.c

echo + CC src/device/timer.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/timer.o src/device/timer.c

echo + CC src/device/audio.c

mkdir -p build/obj-x86-interpreter/device/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/device/audio.o src/device/audio.c

echo + CC src/isa/x86/exec/exec.c

mkdir -p build/obj-x86-interpreter/isa/x86/exec/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/exec/exec.o src/isa/x86/exec/exec.c

echo + CC src/isa/x86/exec/special.c

mkdir -p build/obj-x86-interpreter/isa/x86/exec/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/exec/special.o src/isa/x86/exec/special.c

echo + CC src/isa/x86/decode.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/decode.o src/isa/x86/decode.c

echo + CC src/isa/x86/logo.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/logo.o src/isa/x86/logo.c

echo + CC src/isa/x86/mmu.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/mmu.o src/isa/x86/mmu.c

echo + CC src/isa/x86/intr.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/intr.o src/isa/x86/intr.c

echo + CC src/isa/x86/reg.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/reg.o src/isa/x86/reg.c

echo + CC src/isa/x86/init.c

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/init.o src/isa/x86/init.c

echo + CC src/isa/x86/difftest/dut.c

mkdir -p build/obj-x86-interpreter/isa/x86/difftest/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/isa/x86/difftest/dut.o src/isa/x86/difftest/dut.c

echo + CC src/engine/interpreter/init.c

mkdir -p build/obj-x86-interpreter/engine/interpreter/

gcc -D__DIFF_REF_KVM__ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D__ENGINE_interpreter__ -D__ISA__=x86 -D__ISA_x86__ -D_ISA_H_="isa/x86.h" -c -o build/obj-x86-interpreter/engine/interpreter/init.o src/engine/interpreter/init.c

echo + LD build/x86-nemu-interpreter

gcc -O2 -rdynamic -o build/x86-nemu-interpreter build/obj-x86-interpreter/monitor/debug/ui.o build/obj-x86-interpreter/monitor/debug/watchpoint.o build/obj-x86-interpreter/monitor/debug/log.o build/obj-x86-interpreter/monitor/debug/expr.o build/obj-x86-interpreter/monitor/monitor.o build/obj-x86-interpreter/monitor/difftest/dut.o build/obj-x86-interpreter/monitor/cpu-exec.o build/obj-x86-interpreter/main.o build/obj-x86-interpreter/memory/paddr.o build/obj-x86-interpreter/device/device.o build/obj-x86-interpreter/device/alarm.o build/obj-x86-interpreter/device/serial.o build/obj-x86-interpreter/device/vga.o build/obj-x86-interpreter/device/intr.o build/obj-x86-interpreter/device/keyboard.o build/obj-x86-interpreter/device/io/port-io.o build/obj-x86-interpreter/device/io/map.o build/obj-x86-interpreter/device/io/mmio.o build/obj-x86-interpreter/device/timer.o build/obj-x86-interpreter/device/audio.o build/obj-x86-interpreter/isa/x86/exec/exec.o build/obj-x86-interpreter/isa/x86/exec/special.o build/obj-x86-interpreter/isa/x86/decode.o build/obj-x86-interpreter/isa/x86/logo.o build/obj-x86-interpreter/isa/x86/mmu.o build/obj-x86-interpreter/isa/x86/intr.o build/obj-x86-interpreter/isa/x86/reg.o build/obj-x86-interpreter/isa/x86/init.o build/obj-x86-interpreter/isa/x86/difftest/dut.o build/obj-x86-interpreter/engine/interpreter/init.o -lSDL2 -lreadline -ldl

```

通过查看make过程中信息, 我们可以发现+ CC 和+ LD是通过echo命令打印出来的.

# 冗余信息的优化

但是这样会有大量的冗余信息, 因此我们通过执行命令删除掉以echo和mkdir开头的行并传入到vim中
```bash
make -nB \
 | grep -ve '^\(\#\|echo\|mkdir\)' \
 | vim -
```

可以得到以下结果
![gNBfeL](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/gNBfeL.png)

仍然看的不爽. 可以用 `set nowrap` 关掉换行

![77ZMWv](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/77ZMWv.png)

好像有点清晰了, 但那么多编译选项是干什么的呢?
- `-O2` 是编译优化选项
- `-MMD` 是生成makefile的依赖文件?  #todo 
- `-Wall -Werror -ggdb3` 是生成调试信息

我们可以通过 `ctrl + v` 块选择删除掉这些信息让其变得更清晰

![QwLW0R](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/QwLW0R.png)

- `-I` 的作用是控制 include path
	- 比如 `#include <a.h>` 可以去 `-I.` 后面的目录中找

![bpaCGT](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/bpaCGT.png)

下面就是很多 `-D` 编译选项, 这是**编译时宏定义命令**. Nemu代码中有很多, If 宏定义 .., 定义在这里.

最后会变成这样

![zeoPoU](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/zeoPoU.png)

好像最后一行还是不如人意

>[!tip] vim 中可以只对选中的文本进行处理
>![V9RCj8](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/V9RCj8.png)


我们通过正则表达式把最后一行的空格换成换行符号 `:'<,'>s/ /\r /g`

![MbH1RC](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/MbH1RC.png)

