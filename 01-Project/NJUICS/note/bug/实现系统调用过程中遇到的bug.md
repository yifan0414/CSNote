我在 `do_event(Event e, Context* c)` 函数简单实现了对系统调用事件的处理

```c
static Context* do_event(Event e, Context* c) {
  switch (e.event) {
    case EVENT_YIELD: printf("Hello 0x81\n"); break;
    case EVENT_SYSCALL: printf("Hello 0x80\n"); break;
    default: panic("Unhandled event ID = %d", e.event);
  }

  return c;
}
```

但当我通过 `nanos-lite` 运行 `dummy.c` 程序时，会出现死循环。

- [ ] 如何检查 nemu 中的死循环？ #pa/todo 

![WrBEvo](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/WrBEvo.png)


我们是通过 `naive_uload` 函数加载 `dummy.c` 程序的

```c
void naive_uload(PCB *pcb, const char *filename) {
  uintptr_t entry = loader(pcb, filename);
  Log("Jump to entry = %p", entry);
  ((void(*)())entry) ();
}
```

![[3-3 用户程序和系统调用#^6eu96k]]

这是通过汇编实现的

```c
//x86.S
.globl  _start
_start:
  movl $0, %ebp
  call call_main
```

我们可以看到在调用完 mian 函数后，通过 exit 函数退出，而这个 exit 函数又会调用 `_exit()` 函数

 ```c
//crt0.c
#include <stdint.h>
#include <stdlib.h>
#include <assert.h>

int main(int argc, char *argv[], char *envp[]);
extern char **environ;
void call_main(uintptr_t *args) {
  char *empty[] =  {NULL };
  environ = empty;
  exit(main(0, empty, empty));
  assert(0);
}
```

`_exit()` 函数如下

```c
void _exit(int status) {
  _syscall_(SYS_exit, status, 0, 0);
  while (1); // 死循环的原因
}
```

