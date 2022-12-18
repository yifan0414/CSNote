# QuickLook
```txt
功能：
    (1) 分屏。
    (2) 允许断开Terminal连接后，继续运行进程。
结构：
    一个tmux可以包含多个session，一个session可以包含多个window，一个window可以包含多个pane。
    实例：
        tmux:
            session 0:
                window 0:
                    pane 0
                    pane 1
                    pane 2
                    ...
                window 1
                window 2
                ...
            session 1
            session 2
            ...
```

# Key bindings

|                   name                    | function                                                                                                                   |
|:-----------------------------------------:| -------------------------------------------------------------------------------------------------------------------------- |
|                    C-b                    | Send the prefix key (C-b) through to the application.                                                                      |
|                    C-o                    | Rotate the panes in the current window forwards.                                                                           |
|                    C-z                    | Suspend the tmux client.                                                                                                   |
|                     !                     | Break the current pane out of the window.                                                                                  |
|                     "                     | Split the current pane into two, top and bottom.                                                                           |
|                     #                     | List all paste buffers.                                                                                                    |
|                     $                     | Rename the current session.                                                                                                |
|                     %                     | Split the current pane into two, left and right.                                                                           |
|                     &                     | <font color="#ff0000">Kill</font> the current window.                                                                                                   |
|                     '                     | Prompt for a window index to select.                                                                                       |
|                     (                     | Switch the attached client to the previous session.                                                                        |
|                     )                     | Switch the attached client to the next session.                                                                            |
|                     ,                     | Rename the current window.                                                                                                 |
|                     -                     | Delete the most recently copied buffer of text.                                                                            |
|                     .                     | Prompt for an index to move the current window.                                                                            |
|                  0 to 9                   | Select windows 0 to 9.                                                                                                     |
|                     :                     | Enter the tmux command prompt.                                                                                             |
|                     ;                     | Move to the previously active pane.                                                                                        |
|                     =                     | Choose which buffer to paste interactively from a list.                                                                    |
|                     ***?***                     | ***List all key bindings.***                                                                                                     |
|                     D                     | Choose a client to detach.                                                                                                 |
|                     L                     | Switch the attached client back to the last session.                                                                       |
|                    \[                     | Enter copy mode to copy text or view the history.                                                                          |
|                    \]                     | Paste the most recently copied buffer of text.                                                                             |
|                     c                     | Create a new window.                                                                                                       |
|                     d                     | Detach the current client.                                                                                                 |
|                     f                     | Prompt to search for text in open windows.                                                                                 |
|                     i                     | Display some information about the current window.                                                                         |
|                     l                     | Move to the previously selected window.                                                                                    |
|                     m                     | Mark the current pane (see select-pane -m).                                                                                |
|                     M                     | Clear the marked pane.                                                                                                     |
|                     n                     | Change to the next window.                                                                                                 |
|                     o                     | Select the next pane in the current window.                                                                                |
|                     p                     | Change to the previous window.                                                                                             |
|                     q                     | Briefly display pane indexes.                                                                                              |
|                     r                     | Force redraw of the attached client.                                                                                       |
|                     s                     | Select a new session for the attached client interactively.                                                                |
|                     t                     | Show the time.                                                                                                             |
|                     w                     | Choose the current window interactively.                                                                                   |
|                     x                     | <font color="#ff0000">Kill</font> the current pane.                                                                                                     |
| <span style="background:#d2cbff">z</span> | <span style="background:#d2cbff">Toggle zoom state of the current pane.</span>                                             |
|                     {                     | Swap the current pane with the previous pane.                                                                              |
|                     }                     | Swap the current pane with the next pane.                                                                                  |
|                     ~                     | Show previous messages from tmux, if any.                                                                                  |
|                  Page Up                  | Enter copy mode and scroll one page up.                                                                                    |
|            Up,Down,Left,Right             | Change to the pane above, below, to the left, or to the right of the current pane.                                         |
|                M-1 to M-5                 | Arrange panes in one of the five preset layouts: even-horizontal, even-vertical, main-horizontal, main-vertical, or tiled. |
|                   Space                   | Arrange the current window in the next preset layout.                                                                      |
|                    M-n                    | Move to the next window with a bell or activity marker.                                                                    |
|                    M-o                    | Rotate the panes in the current window backwards.                                                                          |
|                    M-p                    | Move to the previous window with a bell or activity marker.                                                                |
|       C-Up, C-Down, C-Left, C-Right       | Resize the current pane in steps of one cell.                                                                              |
|       M-Up, M-Down, M-Left, M-Right       | Resize the current pane in steps of five cells.                                                                            |

