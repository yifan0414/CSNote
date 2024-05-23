## 理论

>[!quote] 查手册
> ```
> 50 + rd    PUSH r32      2        Push register dword
>
>      0         1         2         3         4         5         6         7
>  +---------+---------+---------+---------+---------+---------+--------+--------+
>  |                               PUSH general register                         |
>5|---------+---------+---------+---------+---------+---------+--------+--------+
>  |   eAX   |   eCX   |   eDX   |   eBX   |   eSP   |   eBP   |  eSI   |  eDI   |
>  +---------+---------+---------+---------+---------+---------+--------+--------+
>```

## 实践

### 译码

我们首先在 `fetch_decode_exec` 中入口，如下所示：

```git
diff --git a/nemu/src/isa/x86/exec/exec.c b/nemu/src/isa/x86/exec/exec.c
index 8f252f3..a56c35f 100644
--- a/nemu/src/isa/x86/exec/exec.c
+++ b/nemu/src/isa/x86/exec/exec.c
@@ -76,6 +76,14 @@ again:
   s->opcode = opcode; // 为什么这里的 opcode 是 32 位呢
   switch (opcode) {
     EX   (0x0f, 2byte_esc)
+    IDEX (0x50, push_r, push)
+    IDEX (0x51, push_r, push)
+    IDEX (0x52, push_r, push)
+    IDEX (0x53, push_r, push)
+    IDEX (0x54, push_r, push)
+    IDEX (0x55, push_r, push)
+    IDEX (0x56, push_r, push)
+    IDEX (0x57, push_r, push)
     IDEXW(0x80, I2E, gp1, 1)
     IDEX (0x81, I2E, gp1)
     IDEX (0x83, SI2E, gp1)
```

`opcode & 0x7` 标识了我们 `push` 的是哪一个寄存器，因此，译码函数和执行函数相同。

```git
diff --git a/nemu/src/isa/x86/local-include/decode.h b/nemu/src/isa/x86/local-include/decode.h
index d57bc53..16e96d8 100644
--- a/nemu/src/isa/x86/local-include/decode.h
+++ b/nemu/src/isa/x86/local-include/decode.h

 /* I386 manual does not contain this abbreviation.
@@ -296,6 +297,11 @@ static inline def_DHelper(call_rel) {
   decode_I(s);
 }

+// push reg
+static inline def_DHelper(push_r) {
+  decode_r(s);
+}
+
```

我们直接调用辅助函数 `decode_r` 用于译码**寄存器**，其调用路径为 `DHepler->DopHelper->operand_reg`。

```c
static inline void operand_reg(DecodeExecState *s, Operand *op, bool load_val, int r, int width) {
  op->type = OP_TYPE_REG;
  op->reg = r;

  if (width == 4) {
    op->preg = &reg_l(r); // 我们将寄存器的地址保存在 preg 中
  } else {
    assert(width == 1 || width == 2);
    op->preg = &op->val;
    if (load_val) rtl_lr(s, &op->val, r, width);
  }

  print_Dop(op->str, OP_STR_SIZE, "%%%s", reg_name(r, width));
}

static inline def_DopHelper(r) {
  operand_reg(s, op, load_val, s->opcode & 0x7, op->width);
}

static inline def_DHelper(r) {
  decode_op_r(s, id_dest, true);
}
```

### 执行

![[2-2 RTFSC(2) 2020#^6cbfx4]]

我们在译码阶段通过 `operand_reg` 函数将相应寄存器 (opcode&0x7) 的地址保存在 preg 中，现在我们需要执行 push 的逻辑代码了。

```c
static inline def_EHelper(push) {
  rtl_push(s, ddest);
  print_asm_template1(push);
}

static inline def_rtl(push, const rtlreg_t* src1) {
  // esp <- esp - 4
  // M[esp] <- src1
  cpu.esp = cpu.esp - 4;
  rtl_sm(s, &cpu.esp, 0, src1, 4);
}

static inline def_rtl(sm, const rtlreg_t* addr, word_t offset, const rtlreg_t* src1, int len) {
  vaddr_write(*addr + offset, *src1, len);
}
```

因为 push 会在 call 等指令用到，因此我们把其逻辑抽象为 RTL 指令 (`rtl_push`)。

