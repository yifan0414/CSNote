> 这是在做 NJU ICS PA 实验时遇到的一个问题

众所周知，测试是软件工程中非常重要的一个环节，但测试代码往往是繁杂无用的（特别是为了测试而改变了程序的正常流程），那么我们如何维护测试代码就成了一个非常重要的问题。

# 0 自我探索过程

下图是我在做 PA1 时的 commit 列表，圈出的部分就是构造测试代码并完成测试的 commit (`99e00be`)。我当时的做法是直接把测试代码删除掉，还原成原来的样子，并再次做了一个 commit (`b7a4b54`)。我的想法是以后如果再用到这部分测试代码，我就使用 `git checkout 99e00be` 切换到该 commit。(事实证明这应该不是正确的做法)

![5h73xC](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/5h73xC.png)

这一天，我准备对之前做过的实验做一下笔记整理，所以会用到相关的代码和结果截图。因此我就按之前想的使用 `git checkout 99e00be` 切换到该提交（此时工作区的文件就会变成当时 commit 时的状态）。但 git 给了我以下的提醒：

```txt
Note: switching to '99e00be'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

HEAD is now at 99e00be Monitor: Construct The Expr Test Case And Test In Main function
```

其意思是我现在正处于 `detached HEAD` 状态，我可以浏览代码或者做一些实验性的改变并提交他们。

好巧不巧，我突然发现之前的测试代码有点问题，所以我进行了一些修改。那么问题来了，修改后的代码如何进行 commit 呢。我是在 `99e00be` 处进行提交还是在 `master` 处进行提交呢？（这里还隐藏了一个问题，如果我想在 `master` 处进行提交，那么我直接 `git checkout master` 会成功吗？）

答案显而易见，我们应该在 `99e00be` 处进行提交，因为这是对 `99e00be` 代码中独有的测试代码修改。

![LQvDBO](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/LQvDBO.png)

可以看我，我们在 master 分支的 `99e00bec` 节点正确提交了，此时的节点编号变成了 `1afe22a4`。

![[detachedHEAD.png]]

那么此时的 `1afe22a4` 属于什么分支呢？我们切换到 master 分支的最新节点。此时 git 会输出一段话。

```
Warning: you are leaving 1 commit behind, not connected to
any of your branches:

  1afe22a commit int 99e00bec

If you want to keep it by creating a new branch, this may be a good time
to do so with:

 git branch <new-branch-name> 1afe22a
```

虽然我们在 master 分支进行的提交，但是由于是在 `detached HEAD` 状态的提交，所以并不属于 master 分支，所以我们要新创建一个分支。然后使用 `git log --graph --oneline --all` 进行查看

![2V7tSA](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/2V7tSA.png)

可以看到，我们成功创建了一个分支（testbranch）并把刚才的提交放在了这个分支（testbranch）上。

回到最初，其实一开始也许就错了，我应该在构造测试代码的时候就创建一个分支，即 `99e00be` 本应在另一个分支上，这样比较符合逻辑。

# 1 工作区、暂存区、版本库、远程仓库

## 1.1 四个工作区概念

![z2mBYV](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/z2mBYV.jpg)

**Workspace**： 工作区，就是你平时存放项目代码的地方

**Index / Stage**： 暂存区，用于临时存放你的改动，事实上它只是一个文件，保存即将提交到文件列表信息

**Repository**： 仓库区（或版本库），就是安全存放数据的位置，这里面有你提交到所有版本的数据。其中 HEAD 指向最新放入仓库的版本。

**Remote**： 远程仓库，托管代码的服务器，可以简单的认为是你项目组中的一台电脑用于远程数据交换

## 1.2 工作流程

git 的工作流程一般是这样的：

１、在工作目录中添加、修改文件；

２、将需要进行版本管理的文件放入暂存区域；

３、将暂存区域的文件提交到git仓库。

因此，git 管理的文件有三种状态：已修改（modified）, 已暂存（staged）, 已提交 (committed)


## 1.3 文件的四种状态

版本控制就是对文件的版本控制，要对文件进行修改、提交等操作，首先要知道文件当前在什么状态，不然可能会提交了现在还不想提交的文件，或者要提交的文件没提交上。

GIT 不关心文件两个版本之间的具体差别，而是关心文件的整体是否有改变，若文件被改变，在添加提交时就生成文件新版本的快照，而判断文件整体是否改变的方法就是用 SHA-1 算法计算文件的校验和。

![5Gokq3](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/5Gokq3.png)

**Untracked:** 未跟踪, 此文件在文件夹中, 但并没有加入到 git 库, 不参与版本控制. 通过 git add 状态变为 Staged.

**Unmodify:** 文件已经入库, 未修改, 即版本库中的文件快照内容与文件夹中完全一致. 这种类型的文件有两种去处, 如果它被修改, 而变为 Modified. 如果使用 `git rm` 移出版本库, 则成为 Untracked 文件。

**Modified:** 文件已修改, 仅仅是修改, 并没有进行其他的操作. 这个文件也有两个去处, 通过 `git add` 可进入暂存 staged 状态, 使用 `git checkout` 则丢弃修改, 返回到 unmodify 状态, 这个 git checkout 即从库中取出文件, 覆盖当前修改

**Staged:** 暂存状态. 执行 git commit 则将修改同步到库中, 这时库中的文件和本地文件又变为一致, 文件为 Unmodify 状态. 执行 git reset HEAD filename 取消暂存, 文件状态为 Modified.


下面的图很好的解释了这四种状态的转变：

![a3XJK6](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/a3XJK6.jpg)


# 2 detached HEAD 的工作区

>[!question] 如果我们在 detached HEAD 中修改工作区并且 git checkout master 会怎么样，反之呢？

1. 首先看你修改的文件在 `detached HEAD` 和 `master HEAD` 中是否一致，如果不一致那么 git 会给出警告并且不执行命令

	![C0bk3h](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/C0bk3h.png)

2. 其他情况共用一个工作区

>[!cite] chatgpt
> 在 Git 的 detached HEAD 状态下，您处于一个特定的提交而不是在分支上。如果在此状态下对工作区进行了修改，然后执行 `git checkout master`，可能会遇到以下情况：
>1. 如果修改的文件在 master 分支上没有任何改动，那么您的修改将会保留，您会在 master 分支上看到这些修改。您可以选择提交这些修改，或者通过 `git stash` 暂存修改，然后在需要的时候再应用它们。
>2. 如果在 master 分支上对相同的文件进行了不同的修改，Git 会尝试自动合并这些修改。如果没有冲突，您的工作区将包含合并后的修改。您需要提交这些合并后的修改。
>3. 如果在 master 分支上对相同的文件进行了不同的修改，并且这些修改与您在 detached HEAD 状态下所做的修改产生了冲突，那么 Git 会提示您解决这些冲突。您需要手动解决冲突，然后提交修改。
>
>请注意，在 detached HEAD 状态下进行修改并返回到主分支可能会导致您的提交丢失。因此，在切换分支之前，最好先创建一个新分支来保存在 detached HEAD 状态下所做的修改。这可以通过以下命令完成：
>
>```
>git checkout -b new_branch_name
>```
>
>这将创建一个新分支，并将您的修改提交到该分支中。然后，您可以安全地切换回 master 分支，或将这些更改与 master 分支合并。