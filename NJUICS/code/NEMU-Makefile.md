# 源文件
```makefile
NAME = nemu

ISA ?= x86
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

Building x86-nemu-interpreter

<span style="background:#fff88f">echo + CC src/monitor/debug/ui.c</span>

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/debug/ui.o src/monitor/debug/ui.c

<span style="background:#fff88f">echo + CC src/monitor/debug/watchpoint.c</span>

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/debug/watchpoint.o src/monitor/debug/watchpoint.c

<span style="background:#fff88f">echo + CC src/monitor/debug/log.c</span>

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/debug/log.o src/monitor/debug/log.c

<span style="background:#fff88f">echo + CC src/monitor/debug/expr.c</span>

mkdir -p build/obj-x86-interpreter/monitor/debug/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/debug/expr.o src/monitor/debug/expr.c

<span style="background:#fff88f">echo + CC src/monitor/monitor.c</span>

mkdir -p build/obj-x86-interpreter/monitor/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/monitor.o src/monitor/monitor.c

<span style="background:#fff88f">echo + CC src/monitor/difftest/dut.c</span>

mkdir -p build/obj-x86-interpreter/monitor/difftest/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/difftest/dut.o src/monitor/difftest/dut.c

<span style="background:#fff88f">echo + CC src/monitor/cpu-exec.c</span>

mkdir -p build/obj-x86-interpreter/monitor/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/monitor/cpu-exec.o src/monitor/cpu-exec.c

<span style="background:#fff88f">echo + CC src/main.c</span>

mkdir -p build/obj-x86-interpreter/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/main.o src/main.c

<span style="background:#fff88f">echo + CC src/memory/paddr.c</span>

mkdir -p build/obj-x86-interpreter/memory/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/memory/paddr.o src/memory/paddr.c

<span style="background:#fff88f">echo + CC src/device/device.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/device.o src/device/device.c

<span style="background:#fff88f">echo + CC src/device/alarm.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/alarm.o src/device/alarm.c

<span style="background:#fff88f">echo + CC src/device/serial.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/serial.o src/device/serial.c

<span style="background:#fff88f">echo + CC src/device/vga.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/vga.o src/device/vga.c

<span style="background:#fff88f">echo + CC src/device/intr.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/intr.o src/device/intr.c

<span style="background:#fff88f">echo + CC src/device/keyboard.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/keyboard.o src/device/keyboard.c

<span style="background:#fff88f">echo + CC src/device/io/port-io.c</span>

mkdir -p build/obj-x86-interpreter/device/io/

gcc <span style="background:#d2cbff">-D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"</span>  -c -o <span style="background:#affad1">build/obj-x86-interpreter/device/io/port-io.o src/device/io/port-io.c</span>

<span style="background:#fff88f">echo + CC src/device/io/map.c</span>

mkdir -p build/obj-x86-interpreter/device/io/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/io/map.o src/device/io/map.c

<span style="background:#fff88f">echo + CC src/device/io/mmio.c</span>

mkdir -p build/obj-x86-interpreter/device/io/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/io/mmio.o src/device/io/mmio.c

<span style="background:#fff88f">echo + CC src/device/timer.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/timer.o src/device/timer.c

<span style="background:#fff88f">echo + CC src/device/audio.c</span>

mkdir -p build/obj-x86-interpreter/device/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/device/audio.o src/device/audio.c

<span style="background:#fff88f">echo + CC src/isa/x86/exec/exec.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/exec/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/exec/exec.o src/isa/x86/exec/exec.c

<span style="background:#fff88f">echo + CC src/isa/x86/exec/special.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/exec/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/exec/special.o src/isa/x86/exec/special.c

<span style="background:#fff88f">echo + CC src/isa/x86/decode.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/decode.o src/isa/x86/decode.c

<span style="background:#fff88f">echo + CC src/isa/x86/logo.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/logo.o src/isa/x86/logo.c

<span style="background:#fff88f">echo + CC src/isa/x86/mmu.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/mmu.o src/isa/x86/mmu.c

<span style="background:#fff88f">echo + CC src/isa/x86/intr.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/intr.o src/isa/x86/intr.c

<span style="background:#fff88f">echo + CC src/isa/x86/reg.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/reg.o src/isa/x86/reg.c

<span style="background:#fff88f">echo + CC src/isa/x86/init.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/init.o src/isa/x86/init.c

<span style="background:#fff88f">echo + CC src/isa/x86/difftest/dut.c</span>

mkdir -p build/obj-x86-interpreter/isa/x86/difftest/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/isa/x86/difftest/dut.o src/isa/x86/difftest/dut.c

<span style="background:#fff88f">echo + CC src/engine/interpreter/init.c</span>

mkdir -p build/obj-x86-interpreter/engine/interpreter/

gcc -D\_\_DIFF\_REF\_KVM\_\_ -O2 -MMD -Wall -Werror -ggdb3 -I./include -I./src/engine/interpreter -D\_\_ENGINE\_interpreter\_\_ -D\_\_ISA\_\_=x86 -D\_\_ISA\_x86\_\_ -D\_ISA\_H\_=\"isa/x86.h\"  -c -o build/obj-x86-interpreter/engine/interpreter/init.o src/engine/interpreter/init.c

<span style="background:#fff88f">echo + LD build/x86-nemu-interpreter</span>

gcc -O2 -rdynamic  -o build/x86-nemu-interpreter build/obj-x86-interpreter/monitor/debug/ui.o build/obj-x86-interpreter/monitor/debug/watchpoint.o build/obj-x86-interpreter/monitor/debug/log.o build/obj-x86-interpreter/monitor/debug/expr.o build/obj-x86-interpreter/monitor/monitor.o build/obj-x86-interpreter/monitor/difftest/dut.o build/obj-x86-interpreter/monitor/cpu-exec.o build/obj-x86-interpreter/main.o build/obj-x86-interpreter/memory/paddr.o build/obj-x86-interpreter/device/device.o build/obj-x86-interpreter/device/alarm.o build/obj-x86-interpreter/device/serial.o build/obj-x86-interpreter/device/vga.o build/obj-x86-interpreter/device/intr.o build/obj-x86-interpreter/device/keyboard.o build/obj-x86-interpreter/device/io/port-io.o build/obj-x86-interpreter/device/io/map.o build/obj-x86-interpreter/device/io/mmio.o build/obj-x86-interpreter/device/timer.o build/obj-x86-interpreter/device/audio.o build/obj-x86-interpreter/isa/x86/exec/exec.o build/obj-x86-interpreter/isa/x86/exec/special.o build/obj-x86-interpreter/isa/x86/decode.o build/obj-x86-interpreter/isa/x86/logo.o build/obj-x86-interpreter/isa/x86/mmu.o build/obj-x86-interpreter/isa/x86/intr.o build/obj-x86-interpreter/isa/x86/reg.o build/obj-x86-interpreter/isa/x86/init.o build/obj-x86-interpreter/isa/x86/difftest/dut.o build/obj-x86-interpreter/engine/interpreter/init.o -lSDL2 -lreadline -ldl


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

>[!tips] vim 中可以只对选中的文本进行处理
>![V9RCj8](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/V9RCj8.png)


我们通过正则表达式把最后一行的空格换成换行符号 `:'<,'>s/ /\r \g`

![MbH1RC](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/MbH1RC.png)

