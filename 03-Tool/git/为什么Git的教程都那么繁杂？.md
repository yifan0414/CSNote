作者：d41d8c  
链接：https://www.zhihu.com/question/594294987/answer/3023844792  
来源：知乎  
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。  
  

我当年学了 [clone](https://www.zhihu.com/search?q=clone&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 和 pull 之后就觉得这样够用了，反正我只是用来下载我感兴趣的项目源码。

后来为了看源码在一段时间内有哪些改动，学了 log 、 show 和 diff 。

为了找到感兴趣内容所在的文件，学了 grep （指 git grep）。

发现上游有多个分支，为了查看不同分支，学了 branch 和 checkout （现在一般用 switch）。

因为上游用了 submodule 所以也稍微学了一下。

在网络不理想的时候，为了从镜像拉取，学了 [remote](https://www.zhihu.com/search?q=remote&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

因为手痒，想自己给项目添加内容，为了让自己写的东西纳入 git 管理，学了 commit （那时候用的还是 commit -a ，用不到 add）。

大概是这时候，第一次遇到了躲不开的配置项，也就是 config 。

从上游拉取时，为了不和自己写的东西冲突，学了 merge 、 add 和 status，后来又学了 fetch 和 [rebase](https://www.zhihu.com/search?q=rebase&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

为了提 Pull Request，也为了备份自己写的东西，学了 push 。

为了把其他分支的修改转移到当前分支，学了 [cherry-pick](https://www.zhihu.com/search?q=cherry-pick&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

> git cherry-pick 是 Git 命令中的一种，用于将一个或多个提交（commit）从当前分支 “复制” 到另一个分支。它可以帮助开发者在不合并整个分支的情况下，从其他分支中选择特定的提交来应用到当前分支中。通常用于修复 bug、回滚代码等场景。

为了撤回修改，学了 reset （当时的需求现在可以用 restore 完成）。

为了恢复不慎删除的内容，学了 [reflog](https://www.zhihu.com/search?q=reflog&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

为了保存写到一半的内容，学了 stash 。

为了找到引入或修复 bug 的版本，学了 [bisect](https://www.zhihu.com/search?q=bisect&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 和 blame 。

为了知道最近的 tag 名称，学了 describe 。

为了知道 tag 对应的提交代码，学了 [rev-parse](https://www.zhihu.com/search?q=rev-parse&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

（以上两条是为了更方便地 blame 。）

为了同时访问多个分支，学了 [worktree](https://www.zhihu.com/search?q=worktree&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 。

为了降低索引的大小，学了 gc 、 prune 和 repack 。

最近还学到用 ls-files 查看自己改了哪些文件。

当然过程中也断断续续学了不少选项，比如 commit --amend 、pull --rebase 、rebase --autostash、commit --fixup 、rebase --[autosquash](https://www.zhihu.com/search?q=autosquash&search_source=Entity&hybrid_search_source=Entity&hybrid_search_extra=%7B%22sourceType%22%3A%22answer%22%2C%22sourceId%22%3A3023844792%7D) 等。

到这里我觉得我已经认识了大多数初级指令。但是对于如何使用 hook，如何直接操作索引中的对象，我还是一无所知。对于使用邮件的工作流程，我也不太了解。

回想起来，从一开始到现在，学的每个东西都是为了能用就行。但是因为有这么多需要，也确实只有学习这么多东西才够用