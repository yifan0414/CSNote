>[!question] 1\. how to copy/paste content within system clipboard and vim clipboard
>
>1. use `"+y` copy the content to system clipboard
>2. use `"+p` paste the system clipboard to content

>[!question] 2\. 怎么查找选中的内容
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

>[!question] 3\. 怎么使用 Vimdiff

>[!bug] 4\. vim 中的宏定义记录过程中似乎是不能取消的
> 如果在记录过程中使用 u 进行撤销，这个宏定义会不能正常工作。

>[!tip] 怎么使用 vim 宏定义产生递增的列表？
>
>Often times it seems I have a list of items, and I need to add numbers in front of them. For example:
>
>```
>Item one
>Item two
>Item three
>```
>
>Which should be:
>
>```text
>1. Item one
>2. Item two
>3. Item three
>```
>
> ***Answer:***
> 
>You can easily record a macro to do it.
>
>First insert `1.` at the start of the first line (there are a couple of spaces after the `1.` but you can't see them).
>
>Go to the start of the second line and go into record mode with `qa`.
>
>Press the following key sequence:
>
>```text
>i                         # insert mode
><ctrl-Y><ctrl-Y><ctrl-Y>  # copy the first few characters from the line above  
><ESC>                     # back to normal mode
>|                         # go back to the start of the line
><ctrl-A>                  # increment the number
>j0                         # down to the next line, if there is no 0, when the number increase upon 10, cause a bug
>q                         # stop recording
>```
>
>Now you can play back the recording with `@a` (the first time; for subsequent times, you can do `@@` to repeat the last-executed macro) and it will add a new incremented number to the start of each line.
>
> ***Reference:***
> 
> [VIM学习笔记 增减数值(CTRL-A/CTRL-X) - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/146498017)

>[!note] Vim 中的 scrollToCursor
>```txt
>1. { keys: 'zz', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'center' }},
>
>2. { keys: 'z.', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'center' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },
>
>3. { keys: 'zt', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'top' }},
>
>4. { keys: 'z<CR>', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'top' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },
>
>5. { keys: 'zb', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'bottom' }},
>
>6. { keys: 'z-', type: 'action', action: 'scrollToCursor', actionArgs: { position: 'bottom' }, motion: 'moveToFirstNonWhiteSpaceCharacter' },
>```

>[!note] A test
