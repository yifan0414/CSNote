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
>
