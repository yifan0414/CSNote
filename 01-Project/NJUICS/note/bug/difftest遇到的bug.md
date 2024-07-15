![[8C097030-CBB7-4401-8318-225B6143FDB1_1_201_a.jpeg]]

```c
static inline def_EHelper(int) {
  raise_intr(s, *ddest, s->seq_pc);
  
  print_asm("int %s", id_dest->str);

#ifndef __DIFF_REF_NEMU__
  // BUG: if use difftest_skip_dut(1, 2), pc for qemu will strange
  // difftest_skip_dut(1, 2);
  difftest_skip_ref();
#endif
}
```

NEMU 的简化会导致某些指令的行为与 REF 有所差异, 因而无法进行对比. 为了解决这个问题, 框架中准备了 `difftest_skip_ref()` 和 `difftest_skip_dut()` 这两个函数: 

-   有的指令不能让 REF 直接执行, 或者执行后的行为肯定与 NEMU 不同, 例如 `nemu_trap` 指令, 在 REF 中, 执行后将会抛出一个调试异常. 此时可以通过 `difftest_skip_ref()` 进行校准, 执行它后, 在 `difftest_step()` 中会让 REF 跳过当前指令的执行, 同时把 NEMU 的当前的寄存器状态直接同步到 REF 中, 效果相当于"该指令的执行结果以 NEMU 的状态为准".
-   由于实现的特殊性, QEMU 在少数时候会把几条指令打包一起执行. 这时候, 我们调用一次 `difftest_step()`, QEMU 就会执行多条指令. 但由于 NEMU 的 `fetch_decode_exec_updatepc()` 是一次执行一条指令, 这样就会引入偏差. 此时可以通过 `difftest_skip_dut(int nr_ref, int nr_dut)` 来进行校准, 执行它后, 会马上让 REF 单步执行 `nr_ref` 次, 然后期望 NEMU 可以在 `nr_dut` 条指令之内追上 REF 的状态, 期间会跳过其中所有指令的检查. [[2-4 基础设施(2) 2020#Differential Testing]]

- [ ] 这里按照 `difftest_skip_dut (1,2)` 会遇到难以解释的错误 #pa/todo