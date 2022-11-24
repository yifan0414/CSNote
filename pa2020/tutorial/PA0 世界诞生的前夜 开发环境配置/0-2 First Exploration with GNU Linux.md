Open `terminal`, you will see the following prompt:

```
username@hostname:~$
```

>[!info] 找不到终端?
>如果你不知道如何打开`terminal`(终端), 你需要在互联网上搜索一些Ubuntu的使用教程来学习.

This prompt shows your username, host name, and the current working directory. The username should be the same as you set during the installation. The current working directory is `~` now. As you switching to another directory, the prompt will change as well. You are going to code under this environment, so try to make friends with terminal!

>[!sq] Where is GUI?
>Many of you always use operating system with GUI, such as Windows. But the terminal is completely with CLI (Command Line Interface). Have you wondered if there is something that you can do it in CLI, but can not in GUI? Have no idea? If you are asked to count how many lines of code you have coded during the 程序设计基础 course, what will you do?
>
>If you stick to Visual Studio, you will never understand why `vim` is called 编辑器之神. If you stick to Windows, you will never know what is [Unix Philosophy](http://en.wikipedia.org/wiki/Unix_philosophy). If you stick to GUI, you can only do what it can; but in CLI, it can do what you want. One of the most important spirits of young people like you is to try new things to bade farewell to the past.
>
>GUI wins when you do something requires high definition displaying, such as watching movies. [Here](http://www.computerhope.com/issues/ch000619.htm) is an article discussing the comparision between GUI and CLI.

Now you can see how much disk space Ubuntu occupies. Type the following command:

```
df -h
```

To shut down the system, issue the following command:

```
poweroff
```

However, you will receive an error message:

```
-bash: poweroff: command not found
```

This error is due to the property of the `poweroff` command - it is a system administration command. Execute this command requires superuser privilege.

>[!sq] Why executing the "poweroff" command requires superuser privilege?
>Can you provide a scene where bad thing will happen if the `poweroff` command does not require superuser privilege?

Therefore, to shut down the system, you should first switch to the root account:

```
su -
```

Enter the root password you set during the installation. You will see the prompt changes:

```
root@hostname:/home/username#
```

The last character is `#`, instead of `$` before you executing `su -`. `#` is the indicator of root account. Now execute `poweroff` command again, you will find that the command is executed successfully.

>[!must] 不要强制关闭虚拟机!!!
>如果你使用虚拟机, 你务必通过`poweroff`命令关闭虚拟机. 如果你通过点击窗口右上角的`X`按钮强制关闭虚拟机, 可能会造成虚拟机中文件损坏的现象. 往届有若干学长因此而影响了实验进度, 甚至由于损坏了实验相关的文件而影响了分数. 请大家引以为鉴, 不要贪图方便, 否则后果自负!

