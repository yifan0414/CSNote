## 1 readline 快捷键

readline是[GNU](https://so.csdn.net/so/search?q=GNU&spm=1001.2101.3001.7020)的库，实现命令行编辑功能，bash、ftp、python、zsh、mysql等程序的命令行界面都是使用readline实现的，具体实现有ctrl-r（查找历史命令）、ctrl-p（上一历史命令）、ctrl-a(跳到行首）等。

最重要的还有本次我们所需的 alt+. (dot)、esc+. 、meta+. 得到上一命令的**最后一个参数**。还有更多快捷键可以参考[readline shortcuts](https://www.bigsmoke.us/readline/shortcuts)。

mac上没有alt 和 meta 键，所以我一般使用 `esc+.` 来获取上一条最后的参数。

## 2 shell/bash历史展开(history expand)

用`!$`获取上一命令的**最后一个参数**。

历史展开由**命令**、**参数**、**操作符**三部分构成，分别表示展开哪一条命令、该命令的哪个参数、对命令的操作。命令展开完成之后才会进入.bash\_history中，即执行history命令不会看到用于历史展开的参数。

本节的所有命令都假设当前bash已经有如下的历史：

```zsh
$ history
1 echo 1 2 3 4 5
2 ls 6 7 8 9 10
3 echo 11 12 13 14 15
4 cat 16 17 18 19 20
5 echo 21 22 23 24 25
```

​a. 命令（Event Designators），用 `!` 开始一个历史展开。

```zsh
$ !n                # 表示第n条命令，如!2表示执行ls 6 7 8 9 10
$ !-n               # 表示倒数第n条命令，如!-3表示执行echo 11 12 13 14 15
$ !!                # 表示上一条命令，是!-1的快捷方式
$ !string           # 表示以string开始的最近的一条命令，如!echo表示echo 21 22 23 24 25
$ !?string?         # 表示含有string的最近的一条命令，如!?6?表示cat 16 17 18 19 20
$ ^string1^string2^ # 表示执行上一条命令，并将其中的第一个string1替换为string2，如果string1不存在则替换失败，不会执行命令。
$ !#                # 表示当前命令现在已经输入的部分，如echo 1 2 !#会执行echo 1 2 echo 1 2
```

​b. 参数（Word Designators），命令中选取指定的参数，`:` 用于分割命令部分与参数部分。

```zsh
$ !!:0              # 表示上一命令的第0个参数，即命令本身，得到的是echo
$ !2:n              # 表示第2个命令的第n个参数，如!2:2得到的是7
$ !!:^              # 表示上一命令第1个参数，可进一步简写为!^，与!!:1同义，得到的是21
$ !!:$              # 表示上一命令的最后一个参数，可进一步简写为!$，得到的是25
$ !!:x-y            # 表示第x到第y个参数，-y意为0-y，如!-2:3-4得到的是18 19
$ !!:*              # 表示上一命令的参数部分，可进一步简写为!*，如!!:*得到的是21 22 23 24 25
$ !!:n*             # 跟!!:n-$同义
$ !!:n-             # 意为!!:n-$-1，从第n个参数到倒数第二个参数，如!-2:3-得到的是18 19
```

通过bash历史展开实现创建并cd到目录的方式为:

```zsh
$ mkdir somewhere/dir && cd !#:1          # 其中!#表示本行所有命令"mkdir somewhere/dir && cd”，:1取第一个参数就是目录名
```

​c. 操作符（Modifiers），在可选的参数部分之后，用一个或多个 `:` 操作符加特定字符。

- h 去除最后的一个文件路径部分，假设上一条命令echo /tmp/123/456/，则`cd !:1:h:h`意为cd /tmp/123；假设上一条命令echo /tmp/123/456，则`cd !:1:h:h`意为cd /tmp
- t 去除所有的开始的文件路径部分，假设上一条命令为echo /tmp/123/456/，则`cd !:1:t`意为cd；假设上一条命令为echo /tmp/123/456，则`cd !:1:t`意为cd 456
- r 去除后缀，假设上一条命令为echo /tmp/bbs.c，则`echo !:1:r`意为echo /tmp/bbs
- e 得到后缀，假设上一条命令为echo /tmp/bbs.c，则`echo !:1:e`意为echo .c
- p print命令而不执行
- \[g\]s/string1/sting2/ 将命令的string1替换为string2，g意为全局替换，假设上一条命令为echo 1 2 1，则`!:gs/1/3/`意为echo 3 2 3。3.1中的`^string1^string2^`相当于`!!:s/string1/string2/`
- \[g\]& 意为执行上次替换，g意为全局替换。接上例，假设上一条命令为echo 123451，则`!:&`意为echo 323451

## 3 使用符号 $ （$\_）

在 shell/bash 里 $ 符号表示当前是普通用户（# 是root），在 sh 脚本或命令行里，$ 开头的表示变量。

```zsh
# root 用户
[root@localhost iotl] # echo root
# 普通用户
[root@localhost iotl] $ echo hello
```

以下是一些特殊变量：

1. $\_ 代表上一个命令的最后一个参数
2. $# 参数个数。
3. $0 当前 shell 名称（zsh or bash）或脚本的名字。
4. $1 传递给该shell脚本的第一个参数。
5. $2 传递给该shell脚本的第二个参数。
6. $@ 表示所有的独立的参数，将各个参数分别加双引号返回。
7. $\* 以一对双引号给出参数列表。
8. $$ 脚本运行的当前进程ID号或所在命令的PID。
9. $? 显示最后命令的退出状态，0表示执行成功，其他表示失败。
10. $! 代表最后执行的**后台**命令的PID

## 4 总结

快捷键使用 `esc + .`

**执行**最近的以xxx开头的命令 !xxx

快捷**修改**上一条命令用三个 ^^^ (例如 `^/^/etc^` 将 `ls /` 改为 `ls /etc`)

**重复**当前行前面的命令 `!#`

灵活的**找到**前面的参数: 冒号 `!!:3` 、^ 开始、& 结束（可以缩写为 `!^` 和 `!&`，注意不是 `!#` ）

重复前面的命令的参数 `!#:1`

  

实际中更多使用快捷键，比如交换前后字母有 `ctrl + t` 和 `esc + t` ，比如交换前后单词(word)有 `alt + t` (别和 `alt + dot` 搞混了)

参考链接:

\[1\] http://www.gnu.org/software/bash/manual/bashref.html#History-Interaction

\[2\] http://[stackoverflow](https://so.csdn.net/so/search?q=stackoverflow&spm=1001.2101.3001.7020).com/questions/4009412/bash-first-argument-of-the-previous-command

\[3\] https://www.cnblogs.com/tianyapiaozi/archive/2012/09/21/bash\_history\_arguments.html