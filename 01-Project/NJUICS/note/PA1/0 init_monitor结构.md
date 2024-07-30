# 0 框架结构图

```txt
main(int argc, char *argv[])
  |
  +---init_monitor(argc, argv)
  |      |
  |      +---parse_args(argc, argv)   /* Parse arguments. */
  |      |
  |      +---init_log() /* Open the log file. */
  |      |
  |      +---init_mem() /* Fill the memory with garbage content. */
  |      |
  |      +---init_isa() /* Perform ISA dependent initialization. */
  |      |
  |      +---long img_size=load_img() /* Load the image to memory. */
  |      |
  |      +---init_regex() /* Compile the regular expressions. */
  |      |
  |      +---init_wp_pool() /* Initialize the watchpoint pool. */
  |      | 
  |      +---init_difftest() /* Initialize differential testing. */
  |      |
  |      +---welcome() /* Display welcome message. */
  |
  |
  +---engine_start()
         |
         +---init_device()
         |
         +---ui_mainloop()
```


# 1 parse_args (argc, argv)

## 1.1 代码

```c
static inline void parse_args(int argc, char *argv[]) {
  const struct option table[] = {
    {"batch"    , no_argument      , NULL, 'b'},
    {"log"      , required_argument, NULL, 'l'},
    {"diff"     , required_argument, NULL, 'd'},
    {"port"     , required_argument, NULL, 'p'},
    {"help"     , no_argument      , NULL, 'h'},
    {0          , 0                , NULL,  0 },
  };
  int o;
  while ( (o = getopt_long(argc, argv, "-bhl:d:p:", table, NULL)) != -1) {
    switch (o) {
      case 'b': batch_mode = true; break;
      case 'p': sscanf(optarg, "%d", &difftest_port); break;
      case 'l': log_file = optarg; break;
      case 'd': diff_so_file = optarg; break;
      case 1:
        if (img_file != NULL) Log("too much argument '%s', ignored", optarg);
        else img_file = optarg;
        break;
      default:
        printf("Usage: %s [OPTION...] IMAGE\n\n", argv[0]);
        printf("\t-b,--batch          run with batch mode\n");
        printf("\t-l,--log=FILE       output log to FILE\n");
        printf("\t-d,--diff=REF_SO    run DiffTest with reference REF_SO\n");
        printf("\t-p,--port=PORT      run DiffTest with port PORT\n");
        printf("\n");
        exit(0);
    }
  }
}


```

> [!chatgpt]
> 这段代码是C语言中对命令行参数进行解析的一种常见方式。它使用了`getopt_long()`函数，这个函数是GNU C库提供的用于解析命令行选项参数的函数。这段代码定义了一个`parse_args()`函数，用于解析传入的命令行参数。
> 
> 在函数内部，首先定义了一个`option`结构体的数组`table`，用于指定期望的命令行参数。在这个例子中，表格指定了`batch`、`log`、`diff`、`port`和`help`这五个选项。然后，使用`getopt_long()`函数来读取命令行参数并进行解析。
> 
> `getopt_long()`函数会返回解析到的选项的字符，未定义的选项会返回-1。在这里，使用`while`循环来持续解析选项，直到所有的选项都被解析完毕。
> 
> 在每次循环中，通过`switch`语句根据返回的选项字符来进行相应的处理。例如，如果返回的选项字符是'b'，则将`batch_mode`设置为`true`。如果返回的选项字符是'p'，则将`difftest_port`的值设置为选项参数（`optarg`）所指定的值。
> 
> 如果选项参数是无法识别的，或者用户指定了`help`选项，则会输出帮助信息，并退出程序。如果用户输入了多个未指定的参数，则会打印警告信息，并只保存第一个参数。

## 1.2 参数传递过程

作为程序启动后的**第一个函数**，`parse_args` 顾名思义是对命令行参数进行解析的函数，其参数是由命令行传递到 `main` 函数中然后传递到 `parse_args`。

NEMU 是通过 Makefile 进行构建的，所以所有的命令都在 Makefile 中。

![LZFv0R](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/LZFv0R.png)

我们可以通过直接查看 Makefile 源文件中的代码看到调用了那几个参数，也可以通过使用 `make run -nB` 直接在终端输出执行命令（更准确）
![[NEMU-Makefile#^tdabqo]]

可以看到 Makefile 将

`--log=./build/nemu-log.txt --diff=/home/yifansu/ics2020/nemu/tools/kvm-diff/build/x86-kvm-so --batch`

作为参数传递给 main 进而由 parse_args 进行解析。

## 1.3 函数执行过程

parse_args 中比较重要的是 `option` 结构体和 `getopt_long` 函数。这两个都来自于 `getopt_ext.h` 头文件。

`getopt_long` 是库函数中的一个命令解析函数。解决了手动字符串处理的麻烦，并且是一个通用标准。具体的请阅读 `man 3 getopt`

## 1.4 错误结果展示

![dKnBRz](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/dKnBRz.png)

对应 Default 分支


# 2 init_log()

比较简单，直接 RTFSC

```c
void init_log(const char *log_file) {
  if (log_file == NULL) return;
  log_fp = fopen(log_file, "w");
  Assert(log_fp, "Can not open '%s'", log_file);
}
```

# 3 init_mem ()

#todo 为什么要用垃圾信息填充呢？

```c
void init_mem() {
#ifndef DIFF_TEST
  srand(time(0));
  uint32_t *p = (uint32_t *)pmem;
  int i;
  for (i = 0; i < PMEM_SIZE / sizeof(p[0]); i ++) {
    p[i] = rand();
  }
#endif
}
```

# 4 init_isa ()

测试寄存器的实现（PA1 中的任务），并且初始化 `cpu.pc`，使其指向客户端程序

```c
static void restart() {
  /* Set the initial instruction pointer. */
  cpu.pc = PMEM_BASE + IMAGE_START;
}

void init_isa() {
  /* Test the implementation of the `CPU_state' structure. */
  void reg_test();
  reg_test();

  /* Load built-in image. */
  memcpy(guest_to_host(IMAGE_START), img, sizeof(img));

  /* Initialize this virtual computer system. */
  restart();
}
```

# 5 load_img ()

- [x] 这个函数是用来加载客户端程序，目前还没用到，等 PA2 再说 #todo ✅ 2023-06-20

![Qpxk86](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Qpxk86.png)

```c
static inline long load_img() {
  if (img_file == NULL) {
    Log("No image is given. Use the default build-in image.");
    return 4096; // built-in image size
  }

  FILE *fp = fopen(img_file, "rb");
  Assert(fp, "Can not open '%s'", img_file);

  Log("The image is %s", img_file);

  fseek(fp, 0, SEEK_END);
  long size = ftell(fp);

  fseek(fp, 0, SEEK_SET);
  int ret = fread(guest_to_host(IMAGE_START), size, 1, fp);
  assert(ret == 1);

  fclose(fp);
  return size;
}

```


# 6 init_regex ()

这个函数用于表达式求值时候进行正则表达式解析

```c
/* Rules are used for many times.
 * Therefore we compile them only once before any usage.
 */
void init_regex() {
  int i;
  char error_msg[128];
  int ret;

  for (i = 0; i < NR_REGEX; i ++) {
    ret = regcomp(&re[i], rules[i].regex, REG_EXTENDED);
    if (ret != 0) {
      regerror(ret, &re[i], error_msg, 128);
      panic("regex compilation failed: %s\n%s", error_msg, rules[i].regex);
    }
  }
}
```

# 7 init_wp_pool ()

#todo NEMU debugger 中的监视点

```c
#define NR_WP 32

static WP wp_pool[NR_WP] = {};
static WP *head = NULL, *free_ = NULL;

void init_wp_pool() {
  int i;
  for (i = 0; i < NR_WP; i ++) {
    wp_pool[i].NO = i;
    wp_pool[i].next = &wp_pool[i + 1];
  }
  wp_pool[NR_WP - 1].next = NULL;

  head = NULL;
  free_ = wp_pool;
}

/* TODO: Implement the functionality of watchpoint */
```

# 8 init_difftest ()

#todo 

