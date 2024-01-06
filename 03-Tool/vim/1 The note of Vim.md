## 1 how to copy/paste content within system clipboard and vim clipboard

>[!success] 
>
>1. use `"+y` copy the content to system clipboard
>2. use `"+p` paste the system clipboard to content

## 2 怎么查找选中的内容

>[!success] 
> 如果是一个单词，可以使用 `shift+*` 快速查找该单词。
> 
> The following sequence will do what you want, given an already selected block of text:
> 
> -   `y` (yank the selected text, into the `"` register by default)
> -   `/` (enter search mode)
> -   (`\` `V`) (optional, enter "very no magic" mode*)
> -   `<C-r>+"` (insert text from `"` register)
> -   Enter (Engage!)
> 
> (*) "very no magic" mode interprets the following text as plain text instead of as a regex. note however that `\` and `/` are still special and will have to be handled in other ways. If the text does not have any characters considered special, you can skip this step.

## 3 怎么使用Vimdiff?

>[!question] 3\. 怎么使用 Vimdiff

>[!bug] 4\. vim 中的宏定义记录过程中似乎是不能取消的
> 如果在记录过程中使用 u 进行撤销，这个宏定义会不能正常工作。

## 4 Vim中宏定义的使用方法

```ad-tip
title: 怎么使用 vim 宏定义产生递增的列表？

Often times it seems I have a list of items, and I need to add numbers in front of them. For example:

~~~
Item one
Item two
Item three
~~~

Which should be:

~~~text
1. Item one
2. Item two
3. Item three
~~~

 ***Answer:***
 
You can easily record a macro to do it.

First insert `1.` at the start of the first line (there are a couple of spaces after the `1.` but you can't see them).

Go to the start of the second line and go into record mode with `qa`.

Press the following key sequence:

~~~text
i                         # insert mode
<ctrl-Y><ctrl-Y><ctrl-Y>  # copy the first few characters from the line above  
<ESC>                     # back to normal mode
|                         # go back to the start of the line
<ctrl-A>                  # increment the number
j0                         # down to the next line, if there is no 0, when the number increase upon 10, cause a bug
q                         # stop recording
~~~

Now you can play back the recording with `@a` (the first time; for subsequent times, you can do `@@` to repeat the last-executed macro) and it will add a new incremented number to the start of each line.

 ***Reference:***
 
 [VIM学习笔记 增减数值(CTRL-A/CTRL-X) - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/146498017)
```

## 5 Vim中鼠标的配置

```ad-note
title:Vim 中的 scrollToCursor
~~~txt
1. { keys: 'zz', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'center' }},

2. { keys: 'z.', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'center' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },

3. { keys: 'zt', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'top' }},

4. { keys: 'z<CR>', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'top' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },

5. { keys: 'zb', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'bottom' }},

6. { keys: 'z-', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'bottom' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },
~~~
```

>[!note] 在 Obsidian 的 vimrc 中使用 surround
>使用了插件 `vimrc support`，配置如下：
>```vimrc
>exmap surround_wiki surround [[ ]]
>exmap surround_double_quotes surround " "
>exmap surround_single_quotes surround ' '
>exmap surround_brackets surround ( )
>exmap surround_square_brackets surround [ ]
>exmap surround_curly_brackets surround { }
>exmap surround_equal surround == ==
>exmap surround_code surround ` `
>exmap surround_italic surround * *
>exmap surround_bold surround ** **
>exmap surround_underline surround <u> </u>
>
>" NOTE: must use 'map' and not 'nmap'
>map [[ :surround_wiki
>nunmap s
>vunmap s
>map s" :surround_double_quotes
>map s' :surround_single_quotes
>map s ( :surround_brackets
>map s) :surround_brackets
>map s[ :surround_square_brackets
>map s] :surround_square_brackets
>map s{ :surround_curly_brackets
>map s} :surround_curly_brackets
>map s= :surround_equal
>map s` :surround_code
>map si :surround_italic
>map sb :surround_bold
>map su :surround_underline
>```

```ad-note
title: indent in Vim
 [Indent multiple lines quickly in vi](https://stackoverflow.com/questions/235839/indent-multiple-lines-quickly-in-vi)

![](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/ivGwBQ.png)

~~~txt
>>   Indent line by shiftwidth spaces
<<   De-indent line by shiftwidth spaces
5>>  Indent 5 lines
5==  Re-indent 5 lines

>%   Increase indent of a braced or bracketed block (place cursor on brace first)
=%   Reindent a braced or bracketed block (cursor on brace)
<\%   Decrease indent of a braced or bracketed block (cursor on brace)
]p   Paste text, aligning indentation with surroundings

=i{  Re-indent the 'inner block', i.e. the contents of the block
=a{  Re-indent 'a block', i.e. block and containing braces
=2a{ Re-indent '2 blocks', i.e. this block and containing block

>i{  Increase inner block indent
<i{  Decrease inner block indent
~~~
```

```ad-note
title:缩进的一点内容
 当我们选中几行后，可以使用 `>` 进行缩进，然后使用 `.` 去重复这个操作

```

```ad-danger
title:有关 inclusive 和 exclusive 的内容还部熟悉
比如怎么删除一个前面的单词且不保留这个字符呢？
![](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/rdVb8i.png)
直接使用 `db` 的话会留下一个字符，这时可以使用 `dvb`
这种操作也可以用到 `dt<>` `df<>`
这是我现在的配置
~~~txt
" delete backwards fully
nmap db dvb
nmap dT dvT
nmap dF dvF
nmap cb cvb
nmap cT cvT
nmap cF cvF
~~~
```

```ad-note
title:Search and replace in a visual selection
[Search and replace in a visual selection | Vim Tips Wiki | Fandom](https://vim.fandom.com/wiki/Search_and_replace_in_a_visual_selection)
```

## 6 Vim 中的缩进怎么做

reference：https://neovim.io/doc/user/fold.html

>[!command] 手动缩进的配置
> `set foldmethod=manual`


```ad-tip
title: save fold state

~~~vim
augroup remember_folds
  autocmd!
  autocmd BufWinLeave * mkview
  autocmd BufWinEnter * silent! loadview
augroup END
~~~
```