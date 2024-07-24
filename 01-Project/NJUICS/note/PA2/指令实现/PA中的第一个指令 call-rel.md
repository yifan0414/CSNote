## 理论

我们首先通过反汇编代码可以看到这个指令的**二进制代码**：
```txt
00100000 <_start>:
  100000:	bd 00 00 00 00       	mov    $0x0,%ebp
  100005:	bc 00 90 10 00       	mov    $0x109000,%esp
  10000a:	e8 05 00 00 00       	call   100014 <_trm_init>
  10000f:	90                   	nop

00100010 <main>:
  100010:	31 c0                	xor    %eax,%eax
  100012:	c3                   	ret    
  100013:	90                   	nop

00100014 <_trm_init>:
  100014:	55                   	push   %ebp
  100015:	89 e5                	mov    %esp,%ebp
  100017:	83 ec 14             	sub    $0x14,%esp
  10001a:	68 2a 00 10 00       	push   $0x10002a
  10001f:	e8 ec ff ff ff       	call   100010 <main>
  100024:	d6                   	(bad)  
  100025:	83 c4 10             	add    $0x10,%esp
  100028:	eb fe                	jmp    100028 <_trm_init+0x14>
```

即 `e8 05 00 00 00` 对应汇编指令 `call 100014`，也就是说 `e8` 是 opcode，我们通过查询 x86 手册可以知道后面是 32 位的偏移量（因为这是 32 位模拟器）。
```

Opcode    Instruction     Clocks          Description
E8  cd    CALL rel32       7+m            Call near, displacement relative
                                          to next instruction
IF rel16 or rel32 type of call
THEN (* near relative call *)
   IF OperandSize = 16
   THEN
      Push(IP);
      EIP := (EIP + rel16) AND 0000FFFFH;
   ELSE (* OperandSize = 32 *)
      Push(EIP);
      EIP := EIP + rel32;
   FI;
FI;
```

根据上面的规则，我们可以知道该命令是首先将**返回地址 push 到栈**中，然后跳转到 `EIP + rel32` 的地方，也就是 PA 中 `s->seq_pc + rel32` 的地方。

## 实践

我们首先要在 `fetch_decode_exec` 入口函数的 `switch` 语句中添加 `opcode=e8` 相应的规则：

```git
diff --git a/nemu/src/isa/x86/exec/exec.c b/nemu/src/isa/x86/exec/exec.c
index 10c3750..8f252f3 100644
--- a/nemu/src/isa/x86/exec/exec.c
+++ b/nemu/src/isa/x86/exec/exec.c
@@ -72,7 +73,7 @@ static inline void fetch_decode_exec(DecodeExecState *s) {
   uint8_t opcode;
 again:
   opcode = instr_fetch(&s->seq_pc, 1);
   s->opcode = opcode; // 为什么这里的 opcode 是 32 位呢
   switch (opcode) {
     EX   (0x0f, 2byte_esc)
     IDEXW(0x80, I2E, gp1, 1)
@@ -111,6 +112,7 @@ again:
     IDEXW(0xd2, gp2_cl2E, gp2, 1)
     IDEX (0xd3, gp2_cl2E, gp2)
     EX   (0xd6, nemu_trap)
+    IDEX (0xe8, call_rel, call)
     IDEXW(0xf6, E, gp3, 1)
     IDEX (0xf7, E, gp3)
     IDEXW(0xfe, E, gp4, 1)
```

通过宏定义展开我们可以得到下面的代码：

```c
// IDEX (0xe8, call_rel, call)

set_width(s, 0);
decode_call_rel(s);
exec_call(s);
break;
```

其中 `decode_xxx` 都是通过 `def_DHelper` 定义的，`exec_xxx` 都是通过 `def_EHelper` 定义的。

```diff
diff --git a/nemu/src/isa/x86/local-include/decode.h b/nemu/src/isa/x86/local-include/decode.h
index 1728713..d57bc53 100644
--- a/nemu/src/isa/x86/local-include/decode.h
+++ b/nemu/src/isa/x86/local-include/decode.h
@@ -291,6 +291,11 @@ static inline def_DHelper(out_a2dx) {
   operand_reg(s, id_dest, true, R_DX, 2);
 }

+// call
+static inline def_DHelper(call_rel) {
+  decode_I(s);
+}
+
```

我们这里是使用了 `decode_I(s)`，这是一个解析**立即数**的辅助函数，我们现在展开该函数

```c
// decode_I(s);

decode_op_I(s, &s->dest, true);

// 其中 decode_op_I 的函数定义如下

static inline void decode_op_I(DecodeExecState *s, Operand *op, bool load_val) {
  /* pc here is pointing to the immediate */
  word_t imm = instr_fetch(&s->seq_pc, op->width);
  operand_imm(s, op, load_val, imm, op->width);
}
```

此时我们已经将**偏移量**放到 `DecodeExecState s` 的 `Operand dest` 中了，下面要进行的是**执行**操作。

```git
diff --git a/nemu/src/isa/x86/exec/control.h b/nemu/src/isa/x86/exec/control.h
index 089fb00..8fd682e 100644
--- a/nemu/src/isa/x86/exec/control.h
+++ b/nemu/src/isa/x86/exec/control.h
@@ -1,4 +1,5 @@
 #include "cc.h"
+#include "rtl/rtl.h"

 static inline def_EHelper(jmp) {
   // the target address is calculated at the decode stage
@@ -24,7 +25,7 @@ static inline def_EHelper(jmp_rm) {

 static inline def_EHelper(call) {
   // the target address is calculated at the decode stage
-  TODO();
+  rtl_push(s, &s->seq_pc);
+  rtl_j(s, s->seq_pc + id_dest->imm);
   print_asm("call %x", s->jmp_pc);
 }
```

可以看到框架代码还贴心的给出了 `TODO()` ，我们使用 `rtl.h` 中的辅助函数设置 `DecodeExecState s` 中的 `s->jmp_pc` 和 `s->is_jmp`。

```c
static inline def_rtl(j, vaddr_t target) {
  s->jmp_pc = target;
  s->is_jmp = true;
}
```