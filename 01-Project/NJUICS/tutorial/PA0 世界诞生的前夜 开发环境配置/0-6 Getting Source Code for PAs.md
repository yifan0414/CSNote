# Getting Source Code

Go back to the home directory by

```
cd ~
```

Usually, all works unrelated to system should be performed under the home directory. Other directories under the root of file system (`/`) are related to system. Therefore, do NOT finish your PAs and Labs under these directories by `sudo`.

>[!must] 不要使用 root 账户做实验!!! 
>使用 root 账户进行实验, 会改变实验相关文件的权限属性, 可能会导致开发跟踪系统无法正常工作; 更严重的, 你的误操作可能会无意中损坏系统文件, 导致系统无法启动! 往届有若干学长因此而影响了实验进度, 甚至由于损坏了实验相关的文件而影响了分数. 请大家引以为鉴, 不要贪图方便, 否则后果自负!
>
>如果你仍然不理解为什么要这样做, 你可以阅读这个页面: [Why is it bad to login as root?](http://askubuntu.com/questions/16178/why-is-it-bad-to-login-as-root) 正确的做法是: 永远使用你的普通账号做那些安分守己的事情(例如写代码), 当你需要进行一些需要root权限才能进行的操作时, 使用 `sudo`.


>[!edit] 在 github 上添加 ssh key
>在获取框架代码之前, 首先请你在 github 上添加一个 ssh key, 具体操作请 STFW.

Now get the source code for PA by the following command:

>[!must] 参加"一生一芯"的同学, 请参考"一生一芯"讲义获取代码链接
>如果你参加"一生一芯", 请勿使用下面的代码链接. 此外, PA 讲义中关于作业提交的要求, "一生一芯"的同学可以全部忽略, 但需要关注"一生一芯"讲义中的提交要求.


```
git clone -b 2022 git@github.com:NJU-ProjectN/ics-pa.git ics2022
```

A directory called `ics2022` will be created. This is the project directory for PAs. Details will be explained in PA1.

Then issue the following commands to perform `git` configuration:

```
git config --global user.name "211220000-Zhang San" # your student ID and name
git config --global user.email "zhangsan@foo.com"   # your email
git config --global core.editor vim                 # your favorite editor
git config --global color.ui true
```

You should configure `git` with your student ID, name, and email. Before continuing, please read [this](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/git.html) `git` tutorial to learn some basics of `git`. Another material recommended by jyy is [Visualizing Git Concepts with D3](http://onlywei.github.io/explain-git-with-d3). You can learn some `git` commands with the help of visualization.

Enter the project directory `ics2022`, then run

```
git branch -m master
bash init.sh nemu
bash init.sh abstract-machine
```

to initialize some subprojects. The script will pull some subprojects from github. We will explain them later.

Besides, the script will also add some environment variables into the bash configuration file `~/.bashrc`. These variables are defined by absolute path to support the compilation of the subprojects. Therefore, <font color=" #ff0000 ">DO NOT move your project to another directory once finishing the initialization</font>, else these variables will become invalid. Particularly, if you use shell other than `bash`, please set these variables in the corresponding configuration file manually.

To let the environment variables take effect, run

```
source ~/.bashrc
```

Then try

```
echo $NEMU_HOME
echo $AM_HOME
cd $NEMU_HOME
cd $AM_HOME
```

to check whether these environment variables get the right paths. If both the `echo` commands report the right paths, and both the `cd` command change to the target paths without errors, we are done. If not, please double check the steps above and the shell you are using.

## Git usage

We will use the `branch` feature of `git` to manage the process of development. A branch is an ordered list of commits, where a commit refers to some modifications in the project.

You can list all branches by

```
git branch
```

You will see there is only one branch called "master" now.

```
* master
```

To create a new branch, use `git checkout` command:

```
git checkout -b pa0
```

This command will create a branch called `pa0`, and check out to it. Now list all branches again, and you will see we are now at branch `pa0`:

```
  master
* pa0
```

From now on, all modifications of files in the project will be recorded in the branch `pa0`.

Now have a try! Modify the `STUID` and `STUNAME` variables in `ics2022/Makefile`:

```
STUID = 211220000  # your student ID
STUNAME = 张三     # your Chinese name
```

Run

```
git status
```

to see those files modified from the last commit:

```
On branch pa0
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes in working directory)

    modified:   Makefile

no changes added to commit (use "git add" and/or "git commit -a")
```

Run

```
git diff
```

to list modifications from the last commit:

```diff
diff --git a/Makefile b/Makefile
index c9b1708..b7b2e02 100644
--- a/Makefile
+++ b/Makefile
@@ -1,4 +1,4 @@
-STUID = 211220000
-STUNAME = 张三
+STUID = 211221234
+STUNAME = 李四

  # DO NOT modify the following code!!!
```

You should see `STUID` and `STUNAME` are modified. Now add the changes to commit by `git add`, and issue `git commit`:

```
git add .
git commit
```

The `git commit` command will call the text editor. Type `modified my info` in the first line, and keep the remaining contents unchanged. Save and exit the editor, and this finishes a commit. Now you should see a log labeled with your student ID and name by

```
git log
```

Now switch back to the `master` branch by

```
git checkout master
```

Open `ics2022/Makefile`, and you will find that `STUID` and `STUNAME` are still unchanged! By issuing `git log`, you will find that the commit log you just created has disappeared!

Don't worry! This is a feature of branches in `git`. Modifications in different branches are isolated, which means modifying files in one branch will not affect other branches. Switch back to `pa0` branch by

```
git checkout pa0
```

You will find that everything comes back! At the beginning of PA1, you will merge all changes in branch `pa0` into `master`.

The workflow above shows how you will use branch in PAs:

-   before starting a new PA, new a branch `pa?` and check out to it
-   coding in the branch `pa?` (this will introduce lot of modifications)
-   after finish the PA, merge the branch `pa?` into `master`, and check out back to `master`

# Compiling and Running NEMU
Now enter `nemu/` directory. Before the first time to compile NEMU, a configuration file should be generated by

```
make menuconfig
```

>[!notice] 编译报错了
>你有可能会遇到这个错误信息, 好吧确实是讲义疏忽了. 那就正好当作一个练习吧: 你需要把缺少的工具装上.
>
>至于怎么装, 当然是 STFW 了.

A menu will pop up. DO NOT modify anything. Just choose `Exit` and `Yes` to save the new configuration. After that, compile the project by `make`:

```
make
```

If nothing goes wrong, NEMU will be compiled successfully.

>[!cloud] 确认 llvm 版本
>若编译时遇到如下错误:
>
>```
>src/utils/disasm.cc: 37:2 : error: #error Please use LLVM with major version >= 11
>```
>
>请输入 `llvm-config --version` 查看 llvm 的版本, 确认其为 11 或以上的版本. 特别地, 若你使用的发行版为 Ubuntu 20.04, 可手动通过 `apt-get install llvm-11 llvm-11-dev` 安装 llvm-11, 然后进行如下改动来指定使用 llvm-11 的版本:
>
>```diff
diff --git a/nemu/src/utils/filelist.mk b/nemu/src/utils/filelist.mk
index c9b1708..b7b2e02 100644
--- a/nemu/src/utils/filelist.mk
+++ b/nemu/src/utils/filelist.mk
@@ -16,5 +16,5 @@
 ifdef CONFIG_ITRACE
 CXXSRC = src/utils/disasm.cc
-CXXFLAGS += $(shell llvm-config --cxxflags) -fPIE
-LIBS += $(shell llvm-config --libs)
+CXXFLAGS += $(shell llvm-config-11 --cxxflags) -fPIE
+LIBS += $(shell llvm-config-11 --libs)
 endif
>```
>
>若你使用的是其它发行版, 请自行寻找解决方案.

>[!sq] What happened?
>You should know how a program is generated in the 程序设计基础 course. But do you have any idea about what happened when a bunch of information is output to the screen during `make` is executed?

To perform a fresh compilation, type

```
make clean
```

to remove the old compilation result, then `make` again.

To run NEMU, type

```
make run
```

However, you will see an error message:

```
[src/monitor/monitor.c:35 welcome] Exercise: Please remove me in the source code and compile NEMU again.
riscv32-nemu-interpreter: src/monitor/monitor.c:36: welcome: Assertion `0' failed.
```

This message tells you that the program has triggered an assertion fail at line 36 of the file `nemu/src/monitor/monitor.c`. If you do not know what is assertion, blame the 程序设计基础 course. But just ignore it now, and you will fix it in PA1.

To debug NEMU with gdb, type

```
make gdb
```

# Development Tracing

Once the compilation succeeds, the change of source code will be traced by `git`. Type

```
git log
```

If you see something like

```
commit 4072d39e5b6c6b6837077f2d673cb0b5014e6ef9
Author: tracer-ics2022 <tracer@njuics.org>
Date:   Sun Jul 26 14:30:31 2022 +0800

    >  run NEMU
    211220000 张三
    Linux 9900k 5.10.0-10-amd64 #1 SMP Debian 5.10.84-1 (2021-12-08) x86_64 GNU/Linux
    15:57:01 up 22 days,  6:01, 16 users,  load average: 0.00, 0.00, 0.00
```

this means the change is traced successfully.

If you see the following message while executing make, this means the tracing fails.

```
fatal: Unable to create '/home/user/ics2022/.git/index.lock': File exists.

If no other git process is currently running, this probably means a
git process crashed in this repository earlier. Make sure no other git
process is running and remove the file manually to continue.
```

Try to clean the compilation result and compile again:

```
make clean
make
```

If the error message above always appears, please contact us as soon as possible.

>[!must] 开发跟踪
>我们使用 `git` 对你的实验过程进行跟踪, 不合理的跟踪记录会影响你的成绩. 往届有学长"完成"了某部分实验内容, 但我们找不到相应的 git log, 最终该部分内容被视为没有完成. git log 是独立完成实验的最有力证据, 完成了实验内容却缺少合理的 git log, 不仅会损失大量分数, 还会给抄袭判定提供最有力的证据. 因此, 请你注意以下事项:
>
>-   请你不定期查看自己的 git log, 检查是否与自己的开发过程相符.
>-   提交往届代码将被视为没有提交.
>-   不要把你的代码上传到公开的地方(现在 github 个人账号也可以创建私有仓库了).
>-   总是在工程目录下进行开发, 不要在其它地方进行开发, 然后一次性将代码复制到工程目录下, 这样 `git` 将不能正确记录你的开发过程.
>-   不要修改 `Makefile` 中与开发跟踪相关的内容.
>-   不要删除我们要求创建的分支, 否则会影响我们的脚本运行, 从而影响你的成绩
>-   不要清除 git log
>
>偶然的跟踪失败不会影响你的成绩. 如果上文中的错误信息总是出现, 请尽快联系我们.

>[!cloud]+ 我不是修读本课程的学生, 是否能够关闭开发跟踪?
>可进行如下修改关闭开发跟踪:
>
>```diff
>diff --git a/Makefile b/Makefile
>index c9b1708..b7b2e02 100644
>--- a/Makefile
>+++ b/Makefile
>@@ -9,6 +9,6 @@
 >  define git_commit
>-  -@git add .. -A --ignore-errors
>-  -@while (test -e .git/index.lock); do sleep 0.1; done
>-  -@(echo "> $(1)" && echo $(STUID) $(STUNAME) && uname -a && uptime) | git commit -F - $(GITFLAGS)
>-  -@sync
>+# -@git add .. -A --ignore-errors
>+# -@while (test -e .git/index.lock); do sleep 0.1; done
>+# -@(echo "> $(1)" && echo $(STUID) $(STUNAME) && uname -a && uptime) | git commit -F - $(GITFLAGS)
>+# -@sync
>  endef
 >```
 
 # Local Commit

Although the development tracing system will trace the change of your code after every successful compilation, the trace record is not suitable for your development. This is because the code is still buggy at most of the time. Also, it is not easy for you to identify those bug-free traces. Therefore, you should trace your bug-free code manually.

When you want to commit the change, type

```
git add .
git commit --allow-empty
```

The `--allow-empty` option is necessary, because usually the change is already committed by development tracing system. Without this option, `git` will reject no-change commits. If the commit succeeds, you can see a log labeled with your student ID and name by

```
git log
```

To filter out the commit logs corresponding to your manual commit, use `--author` option with `git log`. For details about how to use this option, RTFM.


# Writing Report
>[!must] 实验报告内容
>你必须在实验报告中描述以下内容:
>
>-   <font color=" #ff0000 ">实验进度. 简单描述即可, 例如"我完成了所有内容", "我只完成了 xxx".  </font>
>   <font color=" #ff0000 ">缺少实验进度的描述, 或者描述与实际情况不符, 将被视为没有完成本次实验.</font>
>-   <font color=" #ff0000 ">必答题.</font>
>
>你可以自由选择报告的其它内容. 你不必详细地描述实验过程, 但我们鼓励你在报告中描述如下内容:
>
>-   你遇到的问题和对这些问题的思考
>-   对讲义中蓝框思考题的看法
>-   或者你的其它想法, 例如实验心得, 对提供帮助的同学的感谢等
>
>认真描述实验心得和想法的报告将会获得分数的奖励; 蓝框题为选做, 完成了也不会得到分数的奖励, 但它们是经过精心准备的, 可以加深你对某些知识的理解和认识. 因此当你发现编写实验报告的时间所剩无几时, 你应该选择描述实验心得和想法. 如果你实在没有想法, 你可以提交一份不包含任何想法的报告, 我们不会强求. 但请不要
>
>-   大量粘贴讲义内容
>-   大量粘贴代码和贴图, 却没有相应的详细解释(让我们明显看出来是凑字数的)
>
>来让你的报告看起来十分丰富, 编写和阅读这样的报告毫无任何意义, 你也不会因此获得更多的分数, 同时还可能带来扣分的可能.

# Submission

>[!idea] 如果你参加"一生一芯", 请忽略这里的提交要求
>具体请参考"一生一芯"讲义中的要求.

Finally, you should submit your project to the submission website (具体提交方式请咨询ICS实验课程老师). To submit PA0, put your report file (ONLY `.pdf` file is accepted) under the project directory.

```
ics2022
├── 211220000.pdf   # put your report file here
├── abstract-machine
├── fceux-am
├── init.sh
├── Makefile
├── nemu
└── README.md
```

Double check whether everything is fine. In particular, you should check whether your `.pdf` file can be opened with a PDF reader.

>[!idea] 如何打开 PDF 文件?
>STFW.


>[!idea] 又报错了
>我知道, 那你说该怎么办呢?


<br>


# RTFSC and Enjoy

If you are new to GNU/Linux and finish this tutorial by yourself, congratulations! You have learned a lot! The most important, you have learned STFW and RTFM for using new tools and trouble-shooting. (<font color=" #ff0000 ">反思一下, 你真的做到了吗?</font>) With these skills, you can solve lots of troubles by yourself during PAs, as well as in the future.

In PA1, the first thing you will do is to [RTFSC](http://i.linuxtoy.org/docs/guide/ch48s06.html). If you have troubles during reading the source code, go to RTFM:

-   If you can not find the definition of a function, it is probably a library function. Read `man` for more information about that function.
-   If you can not understand the code related to hardware details, refer to the manual.

By the way, you will use C language for programming in all PAs. [Here](http://docs.huihoo.com/c/linux-c-programming) is an excellent tutorial about C language. It contains not only C language (such as how to use `printf()` and `scanf()`), but also other elements in a computer system (data structure, computer architecture, assembly language, linking, operating system, network...). It covers most parts of this course. You are strongly recommended to read this tutorial.

Finally, enjoy the journey of PAs, and you will find hardware is not mysterious, so does the computer system! But remember:

-   <font color=" #ff0000 ">STFW</font>
-   <font color=" #ff0000 ">RTFM</font>
-   <font color=" #ff0000 ">RTFSC</font>

>[!edit] 必答题
>独立解决问题是作为码农的一项十分重要的生存技能. 往届有同学在群里提出如下问题:
>
>-   su 认证失败是怎么回事?
>-   grep 提示 no such file or directory 是什么意思?
>-   请问怎么卸载 Ubuntu?
>-   C 语言的 xxx 语法是什么意思?
>-   ignoring return vaule of 'scanf'是什么意思?
>-   出现 curl: not found 该怎么办?
>-   为什么 strtok 返回 NULL?
>-   为什么会有 Segmentation fault 这个错误?
>-   什么是 busybox?
>
>请仔细阅读[提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)和[别像弱智一样提问](https://github.com/tangx/Stop-Ask-Questions-The-Stupid-Ways/blob/master/README.md) (这篇文章很短, 1 分钟就能看完)这两篇文章, 结合自己在大一时提问和被提问, 以及完成 PA0 的经历, 写一篇不少于 800 字的读后感, 谈谈你对"好的提问"以及"通过 STFW 和 RTFM 独立解决问题"的看法.
>
>Hint: 我们设置这道题并不是为了故意浪费大家的时间, 也不是为了禁止大家提出任何问题, 而是为了让大家知道"什么是正确的". 当你愿意为这些"正确的做法"去努力, 并且尝试用专业的方式提出问题的时候, 你就已经迈出了成为"成为专业人士"的第一步.

>[!abstract] Reminder
>This ends PA0. Please submit your project and report.