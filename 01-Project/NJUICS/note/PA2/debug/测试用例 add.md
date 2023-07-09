我在测试 add 的测试用例的时候，第一次出现了 HIT BAD TRAP 的错误

![Klt0ta](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Klt0ta.png)

通过查看源代码可以发现，我们在测试用例中添加了大量的 `check` 函数，用来确保正确性。如果 check 中的判断为 0，那么我们将会调用 `halt(1)` 指令，`halt(1)` 会把 1 传递给 `eax`（通过内联汇编）。然后会通过 `def_Ehelper(nemu_trap)` 中的 `rtl_exit` 结束程序。

```c
__attribute__((noinline))
void check(bool cond) {
  if (!cond) halt(1);
}

//---------------------------------------------------

void halt(int code) {
  nemu_trap(code);

  // should not reach here
  while (1);
}

//---------------------------------------------------

# define nemu_trap(code) asm volatile (".byte 0xd6" : :"a"(code))

//---------------------------------------------------

def_EHelper(nemu_trap) {
  difftest_skip_ref();

  rtl_exit(NEMU_END, cpu.pc, cpu.eax);

  print_asm("nemu trap");
  return;
}

//---------------------------------------------------

void rtl_exit(int state, vaddr_t halt_pc, uint32_t halt_ret) {
  nemu_state = (NEMUState) { .state = state, .halt_pc = halt_pc, .halt_ret = halt_ret };
}

//---------------------------------------------------

switch (nemu_state.state) {
case NEMU_RUNNING: nemu_state.state = NEMU_STOP; break;

case NEMU_END: case NEMU_ABORT:
  Log("nemu: %s\33[0m at pc = " FMT_WORD "\n\n",
	  (nemu_state.state == NEMU_ABORT ? "\33[1;31mABORT" :
	   (nemu_state.halt_ret == 0 ? "\33[1;32mHIT GOOD TRAP" : "\33[1;31mHIT BAD TRAP")),
	  nemu_state.halt_pc);
  // fall through
case NEMU_QUIT:
  monitor_statistic();
}

```


因此，我可以知道这是因为测试用例的某个 `check` 没有通过，然后我通过查看 Log，发现是第 10 个 `check` 没有通过，此时正在进行第二次内循环，所以可能是 `inc` 指令出现了问题。

```c
#include "trap.h"

int add(int a, int b) {
	int c = a + b;
	return c;
}

int test_data[] = {0, 1, 2, 0x7fffffff, 0x80000000, 0x80000001, 0xfffffffe, 0xffffffff};
int ans[] = {0, 0x1, 0x2, 0x7fffffff, 0x80000000, 0x80000001, 0xfffffffe, 0xffffffff, 0x1, 0x2, 0x3, 0x80000000, 0x80000001, 0x80000002, 0xffffffff, 0, 0x2, 0x3, 0x4, 0x80000001, 0x80000002, 0x80000003, 0, 0x1, 0x7fffffff, 0x80000000, 0x80000001, 0xfffffffe, 0xffffffff, 0, 0x7ffffffd, 0x7ffffffe, 0x80000000, 0x80000001, 0x80000002, 0xffffffff, 0, 0x1, 0x7ffffffe, 0x7fffffff, 0x80000001, 0x80000002, 0x80000003, 0, 0x1, 0x2, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff, 0, 0x7ffffffd, 0x7ffffffe, 0x7fffffff, 0xfffffffc, 0xfffffffd, 0xffffffff, 0, 0x1, 0x7ffffffe, 0x7fffffff, 0x80000000, 0xfffffffd, 0xfffffffe};

#define NR_DATA LENGTH(test_data)

int main() {
	int i, j, ans_idx = 0;
	for(i = 0; i < NR_DATA; i ++) {
		for(j = 0; j < NR_DATA; j ++) {
			check(add(test_data[i], test_data[j]) == ans[ans_idx ++]);
		}
		check(j == NR_DATA);
	}

	check(i == NR_DATA);

	return 0;
}
```


我发现之前的指令实现并没有**写入内存**，导致了错误

```git
diff --git a/nemu/src/isa/x86/exec/arith.h b/nemu/src/isa/x86/exec/arith.h
index 7894632..14ff916 100644
--- a/nemu/src/isa/x86/exec/arith.h
+++ b/nemu/src/isa/x86/exec/arith.h
@@ -34,7 +34,8 @@ static inline def_EHelper(cmp) {
 }

 static inline def_EHelper(inc) {
-  rtl_addi(s, ddest, ddest, 1);
+  rtl_addi(s, s0, ddest, 1);
+  operand_write(s, id_dest, s0);
   print_asm_template1(inc);
 }
```