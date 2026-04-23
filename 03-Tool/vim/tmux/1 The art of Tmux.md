
>[!question] 1\. Tmux 怎么隐藏当前session，隐藏window会有同样的效果吗?
> `<C-a> + d` 隐藏当前session

>[!question] 2\. Tmux 中多个窗口的作用是？
> 也许是一个原因，如果你的电脑屏幕比较小，但需要做的任务又很多，可以使用 `<C-a> + n` 快捷的切换当前窗口

>[!question] 3\. 怎么关闭 session?
> 可以在命令行中使用 `tmux kill-session -t <name>`，也可以在tmux窗口中使用 `<C-a> + &` 关闭这个窗口，当关闭的这个窗口是该 session 最后一个时，自动关闭该 session


>[!tip] 在打开 session 的过程中，名字可以模糊搜索 #Fantastic
> 比如我现在的 session 如下：
> ```
> $ tmux list-sessions
> edit: 1 windows (created Sun Dec 18 15:29:18 2022) 
>```
>
>此时，我可以通过 `tmux attach-session -t ed` 进行搜索
>想一想，这里的模糊搜索是怎么实现的呢？


>[!tip] 怎样在 tmux 中鼠标模式下，鼠标选择后不退出 copy-mode？
>
>```bash
>set -g mouse on
>
># disable "release mouse drag to copy and exit copy-mode", ref: https://github.com/tmux/tmux/issues/140
>unbind-key -T copy-mode-vi MouseDragEnd1Pane
>
># since MouseDragEnd1Pane neither exit copy-mode nor clear selection now,
># let single click do selection clearing for us.
>bind-key -T copy-mode-vi MouseDown1Pane select-pane\; send-keys -X clear-selection
>
># this line changes the default binding of MouseDrag1Pane, the only difference
># is that we use `copy-mode -eM` instead of `copy-mode -M`, so that WheelDownPane
># can trigger copy-mode to exit when copy-mode is entered by MouseDrag1Pane
>bind -n MouseDrag1Pane if -Ft= '#{mouse_any_flag}' 'if -Ft= \"#{pane_in_mode}\" \"copy-mode -eM\" \"send-keys -M\"' 'copy-mode -eM'
>```
