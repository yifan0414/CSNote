# A simple example
```makefile
.PHONY: run clean test

CFLAGS = -Wall -Werror -std=c11 -O2
CC = gcc
LD = gcc

yemu: yemu.o idex.o
	$(LD) $(LDFLAGS) -o yemu yemu.o idex.o

yemu.o: yemu.c yemu.h
	$(CC) $(CFLAGS) -c -o yemu.o yemu.c

idex.o: idex.c yemu.h
	$(CC) $(CFLAGS) -c -o idex.o idex.c

run: yemu
	@./yemu

clean:
	rm -f test yemu *.o

test: yemu
	$(CC) $(CFLAGS) -o test idex.o test.c && ./test
```

>[!note] make的本质
>makefile 的本质就是自动化多文件项目的编译过程.
>
>在没有 makefile 的时候, 我们只能对先对每一个不依赖于其他文件的源文件进行编译, 然后再编译那些依赖于已经编译过的文件的文件. 本质上就是对一个有向无环图进行拓扑排序, 并依次进行编译. 当项目体量不断增加的情况下, 可想而知这是一个非常繁杂而无意义的工作.


## the graph of the example

![[Makefile示例.svg]]
根据上图我们可以得知两个关键的点
1. 当某一个源文件改变时, 只需要重新编译某些文件(其依赖的与依赖其本身的)
2. 某些源文件的编译没有依赖关系, 所以可以并行编译