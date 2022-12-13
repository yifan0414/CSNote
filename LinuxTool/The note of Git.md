https://git-scm.com/book/en/v2

https://learngitbranching.js.org/?locale=zh_CN


>[!note] git commit --amend
>本意是修改上一个提交, 但只能作用于本地, 如果你已经 push 到远程分支, 那么这个命令还需要与远程分支进行合并
>[7.6 Git 工具 - 重写历史](https://git-scm.com/book/zh/v2/Git-%E5%B7%A5%E5%85%B7-%E9%87%8D%E5%86%99%E5%8E%86%E5%8F%B2)


>[!note] git reset --hard
>可以返回当前HEAD所在的commit, 常用于撤销所有的本地更改(不论是在暂存区还是在工作目录的修改)


>[!note] git log -p filename
>查看单个文件的 diff 历史

>[!question] git怎么删除已经删除文件的跟踪呢?
>就比如我在 1st commit 中有 1.pdf, 然后在 3rd commit 中直接删除了1.pdf. 那么怎么删除.git中的该文件追踪呢?