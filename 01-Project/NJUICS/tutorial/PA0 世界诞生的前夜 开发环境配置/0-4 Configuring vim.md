
```
apt-get install vim
```

`vim` is called [编辑器之神](http://os.51cto.com/art/201101/242518.htm). You will use `vim` for coding in all PAs and Labs, as well as editing other files. If you prefer to `emacs`, you can download and install `emacs` from network mirrors.

### Learning vim

You are going to be asked to modify a file using `vim`. For most of you, this is the first time to use `vim`. The operations in `vim` are quite different from other editors you have ever used. To learn `vim`, you need a tutorial. There are two ways to get tutorials:

-   Issue the `vimtutor` command in terminal. This will launch a tutorial for `vim`.<font color="#ff0000">This way is recommended, since you can read the tutorial and practice at the same time.</font>
-   Search the Internet with keyword "vim 教程", and you will find a lot of tutorials about `vim`. Choose some of them to read, meanwhile you can practice with the a temporary file by ```vim test```

<font color="#ff0000">PRACTICE IS VERY IMPORTANT. You can not learn anything by only reading the tutorials.</font>

>[!notice] 为什么上课不讲GNU/Linux的使用? 
>你可能会想: 这是我第一次接触GNU/Linux, 为什么上课不讲讲怎么用?
>
>因为说明书不是用来讲的, 是用来一边看一边操作的; 你也不能光靠道听途说来掌握这些工具, 而是要自己去动手尝试. 你在大学课堂上应该学习到的是那些一脉相承的知识, 然后去思考这些知识背后的原则和思想, 将来有能力将这些原则和思想应用到新的领域.
>
>我们设计这些实验内容, 是为了让你明白, 你有能力自己去看教程学习新的工具; 以及, 以后接触新事物的时候, 你不应该等着别人来给你讲, 而应该自己主动去找教程来学习如何使用.

>[!cloud]  Some games operated with vim
>Here are some games to help you master some basic operations in `vim`. Have fun
> -   [Vim Adventures](http://vim-adventures.com/)
> -   [Vim Snake](http://www.vimsnake.com/)
> -  [Open Vim Tutorials](http://www.openvim.com/tutorial.html)
> -  [Vim Genius](http://www.vimgenius.com/)

>[!cloud] The power of vim
>You may never consider what can be done in such a "BAD" editor. Let's see two examples.
>
>The first example is to generate the following file:
>
>```
>1
>2
>3
>.....
>98
>99
>100
>```
>
>This file contains 100 lines, and each line contains a number. What will you do? In `vim`, this is a piece of cake. First change `vim` into normal state (when `vim` is just opened, it is in normal state), then press the following keys sequentially:
>```
>i1<ESC>q1yyp<C-a>q98@1
>```
>
>where `<ESC>` means the ESC key, and `<C-a>` means "Ctrl + a" here. You only press no more than 15 keys to generate this file. Is it amazing? What about a file with 1000 lines? What you do is just to press one more key:
>
>```
>i1<ESC>q1yyp<C-a>q998@1
>```
>
>The magic behind this example is recording and replaying. You initial the file with the first line. Then record the generation of the second. After that, you replay the generation for 998 times to obtain the file.
>
>The second example is to modify a file. Suppose you have such a file:
>
>```
>aaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbb
>cccccccccccccccccccccccccddddddddddddddddddddddddd
>eeeeeeeeeeeeeeeeeeeeeeeeefffffffffffffffffffffffff
>ggggggggggggggggggggggggghhhhhhhhhhhhhhhhhhhhhhhhh
>iiiiiiiiiiiiiiiiiiiiiiiiijjjjjjjjjjjjjjjjjjjjjjjjj
>```
>
>You want to modify it into:
>
>```
>bbbbbbbbbbbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaaaaaaaaaaa
>dddddddddddddddddddddddddccccccccccccccccccccccccc
>fffffffffffffffffffffffffeeeeeeeeeeeeeeeeeeeeeeeee
>hhhhhhhhhhhhhhhhhhhhhhhhhggggggggggggggggggggggggg
>jjjjjjjjjjjjjjjjjjjjjjjjjiiiiiiiiiiiiiiiiiiiiiiiii
>```
>
>What will you do? In `vim`, this is a piece of cake, too. First locate the cursor to first "a" in the first line. And change `vim` into normal state, then press the following keys sequentially:
>
>```
><C-v>24l4jd$p
>```
>
>where `<C-v>` means "Ctrl + v" here. What about a file with 100 such lines? What you do is just to press one more key:
>
>```
><C-v>24l99jd$p
>```
>
>Although these two examples are artificial, they display the powerful functionality of `vim`, comparing with other editors you have used.

# Enabling syntax highlight

`vim` provides more improvements comparing with `vi`. But these improvements are disabled by default. Therefore, you should enable them first.

We take syntax highlight as an example to illustrate how to enable the features of `vim`. To do this, you should modify the `vim` configuration file. The file is called `.vimrc`, and it is located under `/etc/vim` directory. We first make a copy of it to the home directory by `cp` command:

```
cp /etc/vim/vimrc ~/.vimrc
```

And switch to the home directory if you are not under it yet:

```
cd ~
```

If you use `ls` to list files, you will not see the `.vimrc` you just copied. This is because a file whose name starts with a `.` is a hidden file in GNU/Linux. To show hidden files, use `ls` with `-a` option:

```
ls -a
```

Then open `.vimrc` using `vim`:

```
vim .vimrc
```

After you learn some basic operations in `vim` (such as moving, inserting text, deleting text), you can try to modify the `.vimrc` file as following:

```diff
--- before modification
+++ after modification
@@ -17,3 +17,3 @@
 " Vim5 and later versions support syntax highlighting. Uncommenting the next
 " line enables syntax highlighting by default.
-"syntax on
+syntax on
```

We present the modification with [GNU diff format](http://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html). If you do not understand the diff format, please search the Internet for more information.

>[!notice] 为什么要STFW?
>你或许会想, 我问别人是为了节省我的时间.
>
>但现在是互联网时代了, 在网上你能得到各种信息: 比如diff格式这种标准信息, 网上是100%能搜到的; 就包括你遇到的问题, 很大概率也是别人在网上求助过的. 如果对于一个你本来只需要在搜索引擎上输入几个关键字就能找到解决方案的问题, 你都没有付出如此微小的努力, 而是首先想着找人来帮你解决, 占用别人宝贵的时间, 你将是这个时代的<font color="#ff0000">失败者</font>.
>
>于是有了STFW (Search The F**king Web) 的说法, 它的意思是, 在向别人求助之前自己先尝试通过正确的方式使用搜索引擎独立寻找解决方案.
>
>正确的STFW方式能够增加找到解决方案的概率, 包括
>
>-   使用[Google搜索引擎](https://nju-projectn.github.io/ics-pa-gitbook/ics2022/www.google.com)搜索一般性问题
>-   使用[英文维基百科](http://en.wikipedia.org/)查阅概念
>-   使用[stack overflow问答网站](http://stackoverflow.com/)搜索程序设计相关问题
>
>如果你没有使用上述方式来STFW, 请不要抱怨找不到解决方案而开始向别人求助, 你应该想, "噢我刚才用的是百度, 接下来我应该试试Google". 关于使用Google, 在学校可以尝试设置IPv6, 或者设置"科学上网", 具体设置方式请STFW.

>[!notice] 为什么不要用百度?
>相信大家都用过百度来搜索一些非技术问题, 而且一般很容易找到答案. 但随着问题技术含量的提高, 百度的搜索结果会变得越来越不靠谱. 坚持使用百度搜索技术问题, 你将很有可能会碰到以下情况之一:
>
>-   搜不到相关结果, 你感到挫败
>-   搜到看似相关的结果, 但无法解决问题, 你在感到挫败之余, 也发现自己浪费了不少时间
>-   你搜到了解决问题的方案, 但没有发现原因分析, 结果你不知道这个问题背后的细节
>
>你可能会觉得"可以解决问题就行, 不需要了解问题背后的细节". 但对于一些问题(例如编程问题), 你了解这些细节就相当于学到了新的知识, 所以你应该去了解这些细节, 让自己懂得更多.
>
>如果谷歌能以更高的概率提供可以解决问题的方案, 并且带有原因分析, 你应该没有理由使用百度来搜索技术问题. 如果你仍然坚持使用百度, 原因就只有一个: 你不想主动去成长.

After you are done, you should save your modification. Exit `vim` and open the `.vimrc` file again, you should see the syntax highlight feature is enabled.

>[!notice] 为什么要这么麻烦?
>搞了半天, 你发现其实也就是改动一个字符而已, 为什么不直接说清楚呢?
>
>这是为了"入乡随俗": 我们希望你了解怎么用计算机思维精简准确地表达我们想做的事情. diff格式是一种描述文件改动的常用方式. 实际上, 计算机的世界里面有很多约定俗成的"规矩", 当你慢慢去接触去了解这些规矩的时候, 你就会在不知不觉中明白计算机世界是怎么运转的.

# Enabling more vim features

Modify the `.vimrc` file mentioned above as the following:

```diff
--- before modification
+++ after modification
@@ -21,3 +21,3 @@
 " If using a dark background within the editing area and syntax highlighting
 " turn on this option as well
-"set background=dark
+set background=dark
@@ -31,5 +31,5 @@
 " Uncomment the following to have Vim load indentation rules and plugins
 " according to the detected filetype.
-"filetype plugin indent on
+filetype plugin indent on
@@ -37,10 +37,10 @@
 " The following are commented out as they cause vim to behave a lot
 " differently from regular Vi. They are highly recommended though.
 "set showcmd            " Show (partial) command in status line.
-"set showmatch          " Show matching brackets.
-"set ignorecase         " Do case insensitive matching
-"set smartcase          " Do smart case matching
-"set incsearch          " Incremental search
+set showmatch          " Show matching brackets.
+set ignorecase         " Do case insensitive matching
+set smartcase          " Do smart case matching
+set incsearch          " Incremental search
 "set autowrite          " Automatically save before commands like :next and :make
-"set hidden             " Hide buffers when they are abandoned
+set hidden             " Hide buffers when they are abandoned
 "set mouse=a            " Enable mouse usage (all modes)
```

You can append the following content at the end of the `.vimrc` file to enable more features. Note that contents after a double quotation mark `"` are comments, and you do not need to include them. Of course, you can inspect every features to determine to enable or not.

``` hl:28
setlocal noswapfile " 不要生成swap文件
set bufhidden=hide " 当buffer被丢弃的时候隐藏它
colorscheme evening " 设定配色方案
set number " 显示行号
set cursorline " 突出显示当前行
set ruler " 打开状态栏标尺
set shiftwidth=2 " 设定 << 和 >> 命令移动时的宽度为 2
set softtabstop=2 " 使得按退格键时可以一次删掉 2 个空格
set tabstop=2 " 设定 tab 长度为 2
set nobackup " 覆盖文件时不备份
set autochdir " 自动切换当前目录为当前文件所在的目录
set backupcopy=yes " 设置备份时的行为为覆盖
set hlsearch " 搜索时高亮显示被找到的文本
set noerrorbells " 关闭错误信息响铃
set novisualbell " 关闭使用可视响铃代替呼叫
set t_vb= " 置空错误铃声的终端代码
set matchtime=2 " 短暂跳转到匹配括号的时间
set magic " 设置魔术
set smartindent " 开启新行时使用智能自动缩进
set backspace=indent,eol,start " 不设定在插入状态无法用退格键和 Delete 键删除回车符
set cmdheight=1 " 设定命令行的行数为 1
set laststatus=2 " 显示状态栏 (默认值为 1, 无法显示状态栏)
set statusline=\ %<%F[%1*%M%*%n%R%H]%=\ %y\ %0(%{&fileformat}\ %{&encoding}\ Ln\ %l,\ Col\ %c/%L%) " 设置在状态行显示的信息
set foldenable " 开始折叠
set foldmethod=syntax " 设置语法折叠
set foldcolumn=0 " 设置折叠区域的宽度
setlocal foldlevel=1 " 设置折叠层数为 1
nnoremap <space> @=((foldclosed(line('.')) < 0) ? 'zc' : 'zo')<CR> " 用空格键来开关折叠
```

^mfs5ov

>[!notice] 提高开发效率的编辑器
>程序设计课上你学会了使用Visual Studio, 然后你可能会认为, 程序员就是这样写代码的了. 其实并不是, 程序员会追求那些提高效率的方法. 不是GUI不好, 而是你只是用记事本的操作方式来写代码. 所以你需要改变, 去尝试一些可以帮助你提高开发效率的工具.
>
>在GNU/Linux中, 与记事本的操作方式相比, 学会`vim`的基本操作就已经可以大大提高开发效率. 还有各种插件来增强`vim`的功能, 比如可以在代码中变量跳转的`ctags`等等. 你可以花点时间去配置一下`vim`, 具体配置方式请STFW. 总之, "编辑器之神"可不是浪得虚名的. ^zxcif3

