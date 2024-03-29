# Learning to use basic tools
After installing tools for PAs, it is time to explore GNU/Linux again! [Here](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/linux.html) is a small tutorial for GNU/Linux written by jyy. If you are new to GNU/Linux, read the tutorial carefully, and most important, try every command mentioned in the tutorial. <font color="#ff0000">Remember, you can not learn anything by only reading the tutorial.</font> Besides, [鸟哥的Linux私房菜](http://linux.vbird.org/linux_basic) is a book suitable for freshman in GNU/Linux. Another book recommended by us is [Harley Hahn's Guide to Unix and Linux](http://www.harley.com/books/sg3.html).

>[!notice] RTFM
>The most important command in GNU/Linux is `man` - the on-line manual pager. This is because `man` can tell you how to use other commands. [Here](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/man.html) is a small tutorial for `man`. Remember, learn to use `man`, learn to use everything. Therefore, if you want to know something about GNU/Linux (such as shell commands, system calls, library functions, device files, configuration files...), [RTFM](http://en.wikipedia.org/wiki/RTFM).

>[!notice] 为什么要RTFM?
>RTFM是STFW的长辈, 在互联网还不是很流行的年代, RTFM是解决问题的一种有效方法. 这是因为手册包含了查找对象的所有信息, 关于查找对象的一切问题都可以在手册中找到答案.
>
>你或许会觉得翻阅手册太麻烦了, 所以可能会在百度上随便搜一篇博客来尝试寻找解决方案. 但是, 你需要明确以下几点:
>
>-   你搜到的博客可能也是转载别人的, 有可能有坑
>-   博主只是分享了他的经历, 有些说法也不一定准确
>-   搜到了相关内容, 也不一定会有全面的描述
>
>最重要的是, 当你尝试了上述方法而又无法解决问题的时候, 你需要明确"我刚才只是在尝试走捷径, 看来我需要试试RTFM了".

>[!edit] Write a "Hello World" program under GNU/Linux
>   Write a "Hello World" program, compile it, then run it under GNU/Linux. If you do not know what to do, refer to the GNU/Linux tutorial above.

>[!edit] Write a Makefile to compile the "Hello World" program
>Write a Makefile to compile the "Hello World" program above. If you do not know what to do, refer to the GNU/Linux tutorial above.

Now, stop here. [Here](http://www.cprogramming.com/gdb.html) is a small tutorial for GDB. GDB is the most common used debugger under GNU/Linux. If you have not used a debugger yet (even in Visual Studio), blame the 程序设计基础 course first, then blame yourself, and finally, <font color="#ff0000">read the tutorial to learn to use GDB.</font>

>[!edit] Learn to use GDB
>Read the GDB tutorial above and use GDB following the tutorial. In PA1, you will be required to implement a simplified version of GDB. If you have not used GDB, you may have no idea to finish PA1.

>[!must] 嘿! 别偷懒啊!
>上文让你写个"Hello World"程序, 然后写个Makefile来编译它, 并且看教程学习一下GDB的基本使用呢!

# Installing tmux

`tmux` is a terminal multiplexer. With it, you can create multiple terminals in a single screen. It is very convenient when you are working with a high resolution monitor. To install `tmux`, just issue the following command:

```
apt-get install tmux
```

Now you can run `tmux`, but let's do some configuration first. Go back to the home directory:

```
cd ~
```

New a file called `.tmux.conf`:

```
vim .tmux.conf
```

Append the following content to the file:

```
bind-key c new-window -c "#{pane_current_path}"
bind-key % split-window -h -c "#{pane_current_path}"
bind-key '"' split-window -c "#{pane_current_path}"
```

These three lines of settings make `tmux` "remember" the current working directory of the current pane while creating new window/pane.

Maximize the terminal windows size, then use `tmux` to create multiple normal-size terminals within single screen. For example, you may edit different files in different directories simultaneously. You can edit them in different terminals, compile them or execute other commands in another terminal, without opening and closing source files back and forth. You can scroll the content in a `tmux` terminal up and down. For how to use `tmux`, please STFW.

>[!notice] 又要没完没了地STFW了? 
>对.
>
>PA除了让大家巩固ICS理论课的知识之外, 还承担着一个重要的任务: 把大家培养成一个素质合格的CSer. 事实上, 一个素质合格的CSer, 需要具备独立搜索解决方案的能力. 这是IT企业和科研机构对程序员的一个基本要求: 你将来的老板很可能会把一个任务直接丢给你, 如果你一遇到困难就找人帮忙, 老板就会认为你没法创造价值.
>
>PA在尝试让你重视这些业界和学术界都看重的基本要求, 从而让你锻炼这些能力和心态: 遇到问题了, 第一反应不是赶紧找个大神帮忙搞定, 而是"我来试试STFW和RTFM, 看能不能自己解决". 所以PA不是按部就班的中学实验, 不要抱怨讲义没写清楚导致你走了弯路, 我们就是故意的: 我们会尽量控制路不会太弯, 只要你摆正心态, 你是有能力去独立解决这些问题的. 重要的是, 你得接受现实: 你走的弯路, 都在说明你的能力有待提升, 以后少走弯路的唯一方法, 就是你现在认真把路走下去.

>[!notice] 提问的智慧/别像弱智一样提问
>一个素质合格的CSer需要具备的另一个标准是, 懂得如何提问.
>
>相信大家作为CSer, 被问如何修电脑的事情应该不会少. 比如你有一个文科小伙伴, 他QQ跟你说一句"我的电脑出问题了", 让你帮他修. 然后你得问东问西才了解具体的问题, 接着你让他尝试各种方案, 让他给你尝试的反馈. 如果你有10个这样的小伙伴, 相信你肯定受不了了. 这下你多少能体会到助教的心情了吧.
>
>事实上, 如果希望能提高得到回答的概率, 提问者应该学会如何更好地提问. 换句话说, 提问者应该去积极思考 "<font color="#548dd4">我可以主动做些什么来让对方更方便地帮助我诊断问题</font>". 文科小伙伴确实不是学习计算机专业的, 你可以选择原谅他; 但你是CSer, 至少你得在问题中描述具体的现象以及你做过的尝试, 而不是直接丢一句"我的程序挂了", 就等着别人来救场. 在你将来的职业生涯中也很有可能需要向别人求助, 比如在github等开源社区中发issue, 或者是在stackoverflow等论坛上发帖, 或者给技术工程师发邮件等, <font color="#ff0000">如果你的提问方式非常不专业, 很可能没有人愿意关注你的问题, 因为这不仅让人觉得你随便提的问题没那么重要, 而且大家也不愿意花费大量的时间向你来回地咨询</font>.
>
>一种推荐的提问方式如下:
>
>```
>我在xxx的时候遇到了xxx的错误. 这个错误可以通过以下步骤重现: (描述具体的现象)
>1. 我的系统版本是xxx, 相关的工具版本是xxx
>2. 我做了xxx (必要的时候贴个图)
>3. 然后xxx (必要的时候贴个图)
>...
>为了排查这个错误, 我进行了以下尝试: (说明我很希望可以解决问题, 真的没办法才提问的)
>1. 我做了xxx, 出现了xxx的结果 (必要的时候贴个图)
>2. 我还做了xxx, 出现了xxx的结果 (必要的时候贴个图)
>...
>最后问题还没有解决, 请问我还需要做哪些事情?
>```
>
>另外请大家务必阅读[提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)和[别像弱智一样提问](https://github.com/tangx/Stop-Ask-Questions-The-Stupid-Ways/blob/master/README.md)这两篇文章, 里面有不少例子供大家参考.

The following picture shows a scene working with multiple terminals within single screen. Is it COOL?
![J0QEhC](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/J0QEhC.jpg)

>[!notice] 为什么要使用tmux?
>这其实是一个"使用正确的工具做事情"的例子.
>
>计算机天生就是为用户服务的, 只要你有任何需求, 你都可以想, "有没有工具能帮我实现?". 我们希望每个终端做不同的事情, 能够在屏幕上一览无余的同时, 还能在终端之间快速切换. 事实上, 通过STFW和RTFM你就可以掌握如何使用一款正确的工具: 你只要在搜索引擎上搜索"Linux 终端 分屏", 就可以搜到`tmux`这个工具; 然后再搜索"tmux 使用教程", 就可以学习到`tmux`的基本使用方法; 在终端中输入`man tmux`, 就可以查阅关于`tmux`的任何疑问.
>
>当然, 学习不是零成本的. 往届有学长提出一种零学习成本的分屏方式: 打开4个终端, 并将它们分别拖动到屏幕的4个角落, 发现用Alt+Tab快捷键不方便选择窗口(因为4个窗口的外貌都差不多), 就使用鼠标点击的方式来切换. 然后形容安装学习`tmux`是"脱裤子放屁 -- 多此一举".
>
>`tmux`的初衷就是为用户节省上述的操作成本. 如果你抱着不愿意付出任何学习成本的心态, 就无法享受到工具带来的便利.

>[!sq] Things behind scrolling
>You should have used scroll bars in GUI. You may take this for granted. So you may consider the original un-scrollable terminal (the one you use when you just log in) the hell. But think of these: why the original terminal can not be scrolled? How does `tmux` make the terminals scrollable? And last, do you know how to implement a scroll bar?
>
>GUI is not something mysterious. Remember, behind every elements in GUI, there is a story about it. Learn the story, and you will learn a lot. You may say "I just use GUI, and it is unnecessary to learn the story." Yes, you are right. The appearance of GUI is to hide the story for users. But almost everyone uses GUI in the world, and that is why you can not tell the difference between you and them.

# Why GNU/Linux and How to
>[!notice] 为什么要使用Linux?
>我们先来看两个例子.
>
>**如何比较两个文件是否完全相同?** 这个例子看上去非常简单, 在Linux下使用`diff`命令就可以实现. 如果文件很大, 那不妨用`md5sum`来计算并比较它们的MD5. 对一个Linux用户来说, 键入这些命令只需要花费大约3秒的时间. 但在Windows下, 这件事要做起来就不那么容易了. 也许你下载了一个MD5计算工具, 但你需要点击多少次鼠标才能完成比较呢? 也许你觉得一次好像也省不了多少时间, 然而真相是, <font color="#ff0000">你的开发效率就是这样一点点降低的.</font>
>
>**如何列出一个C语言项目中所有被包含过的头文件?** 这个例子比刚才的稍微复杂一些, 但在Windows下你几乎无法高效地做到它. 在Linux中, 我们只需要通过一行命令就可以做到了:
>
>```
>find . -name "*.[ch]" | xargs grep "#include" | sort | uniq
>```
>
>
>通过查阅`man`, 你应该不难理解上述命令是如何实现所需功能的. 这个例子再次体现了Unix哲学:
>
>-   每个工具只做一件事情, 但做到极致
>-   工具采用文本方式进行输入输出, 从而易于使用
>-   通过工具之间的组合来解决复杂问题
>
>Unix哲学的最后一点最能体现Linux和Windows的区别: <font color="#548dd4">编程创造</font>. 如果把工具比作代码中的函数, 工具之间的组合就是一种编程. 而Windows的工具之间几乎无法组合, 因为面向普通用户的Windows需要强调易用性.
>
>所以, 你应该使用Linux的原因非常简单: <font color="#ff0000">作为一个码农, Windows一直在阻碍你思想, 能力和效率的提升.</font>

>[!notice] 如何用好Linux?
>1.  ~~卸载Windows~~, 解放思想, 摆脱Windows对你的阻碍. 与其默认"没办法, 也只能这样了", 你应该去尝试"<font color="#76923c">看看能不能把这件事做好</font>".
>	-   Linux下也有相应的常用软件, 如Chrome, WPS, 中文输入法, mplayer...
>	-   没有Windows你也可以活下去
>	-   实在不行可以装个Windows虚拟机备用
>2.  熟悉一些常用的命令行工具, 并强迫自己在日常操作中使用它们
>	-   文件管理 - `cd`, `pwd`, `mkdir`, `rmdir`, `ls`, `cp`, `rm`, `mv`, `tar`
>	-   文件检索 - `cat`, `more`, `less`, `head`, `tail`, `file`, `find`
> 	   -   输入输出控制 - 重定向, 管道, `tee`, `xargs`
> 	   -   文本处理 - `vim`, `grep`, `awk`, `sed`, `sort`, `wc`, `uniq`, `cut`, `tr`
> 	  -   正则表达式
> 	   -   系统监控 - `jobs`, `ps`, `top`, `kill`, `free`, `dmesg`, `lsof`
> 	   -   上述工具覆盖了程序员绝大部分的需求
> 	       -   可以先从简单的尝试开始, 用得多就记住了, 记不住就`man`
>3.  RTFM + STFW
>4.  坚持.
> 	   -   心态上, 相信<font color="#0070c0">总有对的工具能帮助我做得更好</font>
> 	   -   行动上, 愿意付出时间去<font color="#0070c0">找到它, 学它, 用它</font>

>[!notice] 强裂推荐: The Missing Semester of Your CS Education
>[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)是jyy墙裂推荐的Linux工具系列教程, 教你如何使用各种工具来帮助你在计算机上高效地完成各种任务, 让你终身收益.
>
>这套教程有中文版, 去看看吧.

>[!idea] 克服恐惧, 累积最初的信心
>事实上, 学习使用Linux是一个低成本, 高成功率的锻炼机会. 只要你愿意STFW和RTFM, 就能解决绝大部分的问题. 相比较而言, 你之后(后续PA中/后续课程中/工作中)遇到的问题只会更加困难. 因此, 独立解决这些简单的小问题, 你就会开始积累最初的信心, 从而也慢慢相信自己有能力解决更难的问题.