我们举两个 `mov` 指令的例子, 它们是 NEMU 自带的客户程序 `mov` 中的两条指令:

```
100000:    b8 34 12 00 00        mov    $0x1234,%eax
......
100017:    66 c7 84 99 00 e0 ff    movw   $0x1,-0x2000(%ecx,%ebx,4)
10001e:    ff 01 00
```

## 简单mov指令的执行

我们先来剖析第一条 `mov $0x1234, %eax` 指令的执行过程.

### 取指(instruction fetch, IF)

首先通过 `instr_fetch()` 取得这条指令的第一个字节 `0xb8`.

### 译码(instruction decode, ID)

在 `fetch_decode_exec()` 函数中用这条指令的第一个字节 `0xb8` 来查找 `switch-case` 的分支, 发现这一指令的操作数宽度是 `4` 字节的 `mov` 指令, 形式是将立即数移入寄存器 (move immediate to register).

事实上, 一个字节最多只能区分 256种不同的指令形式. 当指令形式的数目大于256时, 我们需要使用另外的方法来识别它们. x86中有主要有两种方法来解决这个问题 (在 PA2中你都会遇到这两种情况):

- 一种方法是使用转义码 (escape code), x86 中有一个2字节转义码 `0x0f`, 当指令 `opcode` 的第一个字节是 `0x0f` 时, 表示需要再读入一个字节才能决定具体的指令形式 (部分条件跳转指令就属于这种情况). 后来随着各种 SSE 指令集的加入, 使用2字节转义码也不足以表示所有的指令形式了, x86在2字节转义码的基础上又引入了3字节转义码, 当指令 `opcode` 的前两个字节是 `0x0f` 和 `0x38` 时, 表示需要再读入一个字节才能决定具体的指令形式.
- 另一种方法是使用 `ModR/M` 字节中的扩展 opcode 域来对 `opcode` 的长度进行扩充. 有些时候, 读入一个字节也还不能完全确定具体的指令形式, 这时候需要读入紧跟在 `opcode` 后面的 `ModR/M` 字节, 把其中的 `reg/opcode` 域当做 `opcode` 的一部分来解释, 才能决定具体的指令形式. x86把这些指令划分成不同的指令组 (instruction group), 在同一个指令组中的指令需要通过 `ModR/M` 字节中的扩展 opcode 域来区分.

接下来还需要识别指令的操作数. 对于 `mov $0x1234, %eax` 指令来说, 识别操作数其实就是识别寄存器 `%eax` 和立即数 `$0x1234`. 在 x86中, 通用寄存器都有自己的编号, `I2r` 形式的指令把寄存器编号也放在指令的第一个字节里面, 我们可以通过位运算将寄存器编号抽取出来; 立即数存放在指令的第二个字节, 可以很容易得到它. 需要说明的是, 由于立即数是指令的一部分, 我们还需要通过 `instr_fetch()` 函数来获得它.

### 执行(execute, EX)

对于 `mov $0x1234, %eax` 指令来说, 执行阶段的工作就是把立即数 `$0x1234` 送到寄存器 `%eax` 中. 由于 `mov` 指令的功能可以统一成"把源操作数的值传送到目标操作数中", 而译码阶段已经把操作数都准备好了, 所以只需要针对 `mov` 指令编写一个执行辅助函数即可. 这个函数就是 `exec_mov()`, 它是通过 `def_EHelper` 宏来定义的:

```c
def_EHelper(mov) {
    write_operand(s, id_dest, dsrc1);
    print_asm_template2(mov);
}
```

其中 `write_operand()` 函数会根据第二个参数中记录的类型的不同进行相应的写操作, 包括写寄存器和写内存. `print_asm_template2()` 是个宏, 用于输出带有两个操作数的指令的汇编形式.

### 更新PC

调用`update_pc()`即可.

## 复杂mov指令的执行

对于第二个例子 `movw $0x1, -0x2000(%ecx,%ebx,4)`, 执行这条执行还是分取指, 译码, 执行三个阶段.

首先是取指. 这条 mov 指令比较特殊, 它的第一个字节是 `0x66`, 如果你查阅 i386手册, 你会发现 `0x66` 是一个 `operand-size prefix`. 因为这个前缀的存在, 本例中的 `mov` 指令才能被 CPU 识别成 `movw`. NEMU 通过一个 ISA 相关的译码信息成员 `s->isa.is_operand_size_16` 来记录操作数宽度前缀是否出现, `switch-case` 语句中的 `case 0x66` 分支实现了这个功能. `case 0x66` 分支对 `s->isa.is_operand_size_16` 成员变量做了标识之后, 通过 `goto` 语句回到函数的开头重新取出操作码, 此时取得了真正的操作码 `0xc7`. 由于 `s->isa.is_operand_size_16` 成员变量进行过标识, 在 `set_width()` 函数中将会确定操作数长度为 `2` 字节.

接下来是识别操作数. 根据操作码 `0xc7` 查找相应的 `case` 分支, 调用译码辅助函数 `decode_mov_I2E()`, 这个译码辅助函数又分别调用 `decode_op_I()` 和 `operand_rm()` 这两个操作数译码辅助函数来取出操作数. 阅读代码, 你会发现 `operand_rm()` 最终会调用 `read_ModR_M()` 函数. 由于本例中的 `mov` 指令需要访问内存, 因此除了要识别出立即数之外, 还需要确定好要访问的内存地址. x86通过 `ModR/M` 字节来指示内存操作数, 支持各种灵活的寻址方式. 其中最一般的寻址格式是

> displacement(R[base_reg], R[index_reg], scale_factor)

相应内存地址的计算方式为

> addr = R[base_reg] + R[index_reg] * scale_factor + displacement

其它寻址格式都可以看作这种一般格式的特例, 例如

> displacement(R[base_reg])

可以认为是在一般格式中取 `R[index_reg] = 0, scale_factor = 1` 的情况. 这样, 确定内存地址就是要确定 `base_reg`, `index_reg`, `scale_factor` 和 `displacement` 这4个值, 而它们的信息已经全部编码在 `ModR/M` 字节里面了.

我们以本例中的 `movw $0x1, -0x2000(%ecx,%ebx,4)` 说明如何识别出内存地址:

```c
100017:    66 c7 84 99 00 e0 ff    movw   $0x1,-0x2000(%ecx,%ebx,4)
10001e:    ff 01 00
```

根据 `mov_I2E` 的指令形式, `0xc7` 是 `opcode`, `0x84` 是 `ModR/M` 字节. 在 i386手册中查阅表格17-3得知, `0x84` 的编码表示在 `ModR/M` 字节后面还跟着一个 `SIB` 字节, 然后跟着一个32位的 `displacement`. 于是读出 `SIB` 字节, 发现是 `0x99`. 在 i386手册中查阅表格17-4得知, `0x99` 的编码表示 `base_reg = ECX, index_reg = EBX, scale_factor = 4`. 在 `SIB` 字节后面读出一个32位的 `displacement`, 发现是 `00 e0 ff ff`, 在小端存储方式下, 它被解释成 `-0x2000`. 于是内存地址的计算方式为

> addr = R[ECX] + R[EBX] * 4 - 0x2000

框架代码已经实现了 `load_addr()` 函数和 `read_ModR_M()` 函数 (在 `nemu/src/isa/x86/decode.c` 中定义), 它们的函数原型为

```c
void load_addr(DecodeExecState *s, ModR_M *m, Operand *rm);
void read_ModR_M(DecodeExecState *s, Operand *rm, bool load_rm_val, Operand *reg, bool load_reg_val);
```

它们将 `s->seq_pc` 所指向的内存位置解释成 `ModR/M` 字节, 根据上述方法对 `ModR/M` 字节和 `SIB` 字节进行译码, 把译码结果存放到参数 `rm` 和 `reg` 指向的变量中. 虽然 i386手册中的表格17-3和表格17-4内容比较多, 仔细看会发现, `ModR/M` 字节和 `SIB` 字节的编码都是有规律可循的, 所以 `load_addr()` 函数可以很简单地识别出计算内存地址所需要的4个要素 (当然也处理了一些特殊情况). 不过你现在可以不必关心其中的细节, 框架代码已经为你封装好这些细节, 并且提供了各种用于译码的接口函数.

本例中的执行阶段就是要把立即数写入到相应的内存位置. 译码阶段已经把操作数准备好了, 执行辅助函数 `exec_mov()` 会完成数据移动的操作, 最终在 `update_pc()` 函数中更新 PC.