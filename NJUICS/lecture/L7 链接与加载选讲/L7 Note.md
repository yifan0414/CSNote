### 1 为什么用 gcc 链接而不是 ld 链接

```ad-chatgpt
title: 为什么用gcc链接而不是ld链接
通常情况下，可以使用 ld 链接器来连接目标文件，生成可执行文件。但使用 gcc 来链接的好处在于，它可以自动地为我们链接一些依赖的库文件。 

例如，如果我们的目标文件需要链接 math 库，我们可以通过指定链接选项链接 math 库，像这样：

~~~
ld -o output file1.o file2.o -lm
~~~

但是，如果只使用 ld 链接器，我们需要手动添加和管理所有的依赖库文件，这可能非常麻烦。使用 gcc 链接器，我们只需要指定我们的源文件，然后 gcc 会自动为我们链接所有需要的库文件，简化了我们的工作流程。
```

### 2 gcc -static 是什么，有什么好处

```ad-chatgpt
title: gcc -static是什么，有什么好处
gcc -static是指在编译时使用静态链接库，也就是把所需的函数库和执行文件捆绑在一起生成一个单一的可执行文件。

使用静态链接库的好处是可以让程序运行更加稳定可靠，因为程序所需的所有库都已经打包在一起，而不需要依赖系统环境或其他的动态链接库。这使得程序在不同的平台上都能够执行，而不需要担心目标机器是否安装了所需的库。

另一方面，使用静态库的缺点是生成的可执行文件大小会变大，因为库的所有内容都需要复制到可执行文件中。而且如果静态链接库有更新，需要重新编译整个程序。
```

```ad-question
title: 为什么 `.out` 不是字节序列
```

# 2 NEMU 中 objcopy 的作用
由于 NEMU 解析的是字节序列，不能直接识别 `.elf` 文件，所以我们使用 `objcopy` 将其中的代码和数据拿出来。
```makefile
image: $(IMAGE).elf
	@$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt
	@echo + OBJCOPY "->" $(IMAGE_REL).bin
	@$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin
```

```ad-chatgpt
title: objcopy的作用
这段代码是一个命令，用于将文件\$(IMAGE).elf转换为$(IMAGE).bin格式的二进制文件。具体含义如下：

- `@$(OBJCOPY)`：调用objcopy命令进行操作。
- `-S`：丢弃源文件中所有的符号信息。
- `--set-section-flags .bss=alloc,contents`：将名为.bss的节(section)标记为可分配和包含内容的。
- `-O binary`：指定输出格式为二进制文件。
- `$(IMAGE).elf`：输入的可执行文件。
- `$(IMAGE).bin`：输出的二进制文件。
```



### 4 可重定位符号的填充

```ad-quote
【[完结] 2020 南京大学计算机系统基础习题课 (蒋炎岩)】 【精准空降到 22:39】 https://www.bilibili.com/video/BV1qa4y1j7xk/?p=7&share_source=copy_web&vd_source=587965785c97101d90acb761204e6795&t=1359
```

![OJcIkZ](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/OJcIkZ.png)

当我们谈 PC 指针或者 rip 的时候，我们总是谈下一条指针的 PC。

```ad-quote
As these examples illustrate, the value of the program counter when performing PC-relative addressing is the address of the instruction following the jump, not that of the jump itself. This convention dates back to early implementations, when the processor would update the program counter as its first step in executing an instruction.

正如这些例子所说明的那样，在执行相对于程序计数器（PC）的寻址时，程序计数器的值是跳转指令后面一条指令的地址，而不是跳转指令本身的地址。**这个约定可以追溯到早期实现中，当处理器执行一条指令时，它会首先更新程序计数器。**

[CSAPP 3.6.4](marginnote3app://note/D78B95D4-3FF3-474D-8A69-B1DD1FA73050)

```

```ad-danger
title: 有时候提出问题比解决问题更重要
我们直接对 main.o 进行 objdump, 得到的就是待填充的汇编代码。那么这些待填充的汇编代码什么时候填充呢？应该填充什么呢？这些问题需要仔细思考下。
```

