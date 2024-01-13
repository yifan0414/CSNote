# 0 查看源文件的行数

使用下面的命令对可以看到 xv6 中 kernel 中源文件的行数排列

```bash
find . -type f \( -name "*.c" -o -name "*.h" \) -exec wc -l {} + | sort -nr
```

或者使用下面的命令只统计行数 ![[04-NEMU 框架选讲 (2) 代码导读#^qkeeer]]

> [!summary]- 结果
> 
> 
> ~~~
>   6146 total
>    697 ./fs.c
>    688 ./proc.c
>    505 ./sysfile.c
>    451 ./vm.c
>    363 ./riscv.h
>    327 ./virtio_disk.c
>    236 ./log.c
>    221 ./trap.c
>    192 ./console.c
>    190 ./uart.c
>    189 ./defs.h
>    182 ./file.c
>    166 ./exec.c
>    153 ./bio.c
>    147 ./syscall.c
>    135 ./printf.c
>    130 ./pipe.c
>    110 ./spinlock.c
>    107 ./string.c
>    107 ./proc.h
>     96 ./virtio.h
>     93 ./sysproc.c
>     89 ./start.c
>     82 ./kalloc.c
>     64 ./memlayout.h
>     60 ./fs.h
>     55 ./sleeplock.c
>     47 ./plic.c
>     45 ./ramdisk.c
>     45 ./main.c
>     42 ./elf.h
>     40 ./file.h
>     22 ./syscall.h
>     13 ./param.h
>     12 ./buf.h
>     11 ./stat.h
>     10 ./types.h
>     10 ./sleeplock.h
>      9 ./spinlock.h
>      5 ./fcntl.h
> ~~~
