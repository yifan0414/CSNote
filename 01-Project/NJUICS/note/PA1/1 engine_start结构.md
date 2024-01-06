# 0 框架结构图

```c
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


# 1 init_device ()

#todo 

# 2 ui_mainloop ()

类似于终端的命令行提示符，只不过这是在 NEMU 内部执行的，可以很容易的访问内部状态。

![ZL47x0](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/ZL47x0.png)


```c
void ui_mainloop() {
  if (is_batch_mode()) { // 在 init_monitor 中有介绍 batch_mode
    cmd_c(NULL);
    return;
  }

  for (char *str; (str = rl_gets()) != NULL; ) {
    char *str_end = str + strlen(str);

    /* extract the first token as the command */
    char *cmd = strtok(str, " ");
    if (cmd == NULL) { continue; }

    /* treat the remaining string as the arguments,
     * which may need further parsing
     */
    char *args = cmd + strlen(cmd) + 1; // 如果不仅仅是一个空格呢?
    if (args >= str_end) {
      args = NULL;
    }

#ifdef HAS_IOE
    extern void sdl_clear_event_queue();
    sdl_clear_event_queue();
#endif

    int i;
    for (i = 0; i < NR_CMD; i ++) {
      if (strcmp(cmd, cmd_table[i].name) == 0) {
        if (cmd_table[i].handler(args) < 0) { return; }
        break;
      }
    }

    if (i == NR_CMD) { printf("Unknown command '%s'\n", cmd); }
  }
}

```

要想理解这个函数在做什么，必须理解以下知识点：
- `rl_gets()`
- `strtok()`
- 函数指针

## 2.1 `rl_gets()`

通过名字就可以看出来，这个函数是读取 prompt 的输入内容的。其用到了两个库函数：`readline()` 和 `add_history()`。

>[!note] 静态局部变量
> 存放在静态存储区，只在被声明的代码块中可见，生命周期是整个程序运行周期。
> [static变量及其作用，C语言static变量详解](http://c.biancheng.net/view/301.html)
>

```c
/* We use the `readline' library to provide more flexibility to read from stdin. */
static char* rl_gets() {
  static char *line_read = NULL; // 静态局部变量，这一步只执行一次
  
  // 第二次执行时为 true
  if (line_read) {
    free(line_read);
    line_read = NULL;
  }

  line_read = readline("(nemu) ");

  if (line_read && *line_read) {
    add_history(line_read); // 可以使用方向键翻动历史
  }

  return line_read;
}
```

>[!sc] man 3 readline
>
>```c
>char *
readline (const char *prompt);
>```
>readline  will  read a line from the terminal and return it, using prompt as a prompt.  If prompt is NULL or the empty string, no prompt is issued.  The line returned is allocated with `malloc(3)`; **the caller must free it  when finished**.  The line returned has the final newline removed, so only the text of the line remains.


## 2.2 `strtok()`


```c
char *strtok(char *str, const char *delim );
```

Finds the **next token** in a null-terminated byte string pointed to by `str`. The **separator characters** are identified by null-terminated byte string pointed to by `delim`.

This function is designed to be called multiple times to obtain **successive tokens** from the same string.

-   If `str` is not a null pointer, the call is treated as the first call to `strtok` for this particular string. The function searches for the first character which is _not_ contained in `delim`. （搜索未包含 `delim` 的第一个字符）
-   If no such character was found, there are no tokens in `str` at all, and the function returns a `null pointer`.
-   If such character was found, it is the _beginning of the token_. The function then searches from that point on for the first character that _is_ contained in `delim`. （如果找到了，则继续搜索第一个包含 `delim` 的字符）

	-   If no such character was found, `str` has only one token, and future calls to `strtok` will return a null pointer
	-   If such character was found, it is _replaced_ by the null character `'\0'` and the pointer to the following character is stored in a static location for subsequent invocations. （将其置换为 `\0` ）

-   The function then returns the pointer to the beginning of the token
-   If `str` is a null pointer, the call is treated as a subsequent calls to `strtok`: the function continues from where it left in previous invocation. The behavior is the same as if the previously stored pointer is passed as `str`.

The behavior is **undefined** if either `str` or `delim` is not a pointer to a null-terminated byte string.

>[!example]
>
>```c
>#include <string.h>
>#include <stdio.h>
> 
>int main(void)
>{
>    char input[] = "A bird came down the walk";
>    printf("Parsing the input string '%s'\n", input);
>    char *token = strtok(input, " ");
>    while(token) {
>        puts(token);
>        token = strtok(NULL, " ");
>    }
> 
>    printf("Contents of the input string now: '");
>    for(size_t n = 0; n < sizeof input; ++n)
>        input[n] ? putchar(input[n]) : fputs("\\0", stdout);
>    puts("'");
>}
>/*
>Parsing the input string 'A bird came down the walk'
>A
>bird
>came
>down
>the
>walk
>Contents of the input string now: 'A\0bird\0came\0down\0the\0walk\0'
>*/
>```


## 2.3 函数指针

注意看，当我们通过上面的步骤成功提取 `cmd` 和其参数后，我们有一个循环比较操作

```c
int i;
for (i = 0; i < NR_CMD; i ++) {
	if (strcmp(cmd, cmd_table[i].name) == 0) {
		if (cmd_table[i].handler(args) < 0) { return; }
		break;
	}
}
if (i == NR_CMD) { printf("Unknown command '%s'\n", cmd); }
```

其中的关键在于 `cmd_table[i].handler(args)`

```c
static struct {
  char *name;
  char *description;
  int (*handler) (char *);
} cmd_table [] = {
  { "help", "Display informations about all supported commands", cmd_help },
  { "c", "Continue the execution of the program", cmd_c },
  { "q", "Exit NEMU", cmd_q },
  { "si", "Single Step Execution", cmd_si},
  { "info", "Print register and watch point info", cmd_info},
  { "x", "Scan the memory", cmd_x},
  { "p", "Evaluate the expression", cmd_p},
  /* TODO: Add more commands */
};

#define NR_CMD (sizeof(cmd_table) / sizeof(cmd_table[0]))

```

这是一个结构体，其中有三个成员，最为特殊的就是 `int (*handler) (char*)` ，他是一个函数指针，可以指向返回值为 `int`，参数为 `char*` 的函数。

因此，这个函数的具体细节也比较清晰了，就是通过 `rl_gets()` 读取用户输入的内容，然后通过 `strtok()` 提取出 `cmd` 及其参数，最后根据 `cmd` 的名字对应调用不同的处理函数。

## 2.4 处理函数

### 2.4.1 cmd_info

```c
static int cmd_info(char *args) {
  if (args == NULL) {
    // 这里到底是直接退出好呢? 还是重来?
    // Assert(0, "缺少参数");
    Log("Please give one args from 'r' and 'w'");
    return 0;
  }
  // 看起来多此一举, 但是其作用是忽略第一个非空白字符前的所有的空白字符
  char* arg = strtok(NULL, " ");
  if (strcmp(arg, "r") == 0) {
    isa_reg_display();
  }
  else if (strcmp(arg, "w") == 0) {
    // TODO: 实现打印监视点信息
    TODO();
  }
  else {
    Log("undefined info args");
  } 
  return 0;
}
```
