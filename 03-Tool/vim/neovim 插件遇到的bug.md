# 1 kanagawa

![[attachments/f0e7227303338e11b74042dd53db2a1d_MD5.png]]

# 2 Lsp hover


我调用 `vim.lsp.buf.hover` 来显示相关信息，但其调用的 `float window` 的位置却显示不正确，如下图所示：

![[attachments/a89f9f714d63340f6ad7bbc04cf14354_MD5.png]]

![[attachments/f08b3c16b3904386299bad3ea9fa4080_MD5.png]]

通过查看源码可以知道，这个窗口是 noice 负责的，而 noice 又是通过调用 nui 配置的，所以**修改 nui** 的源码可以改变其位置

![[attachments/4c6510c14aaaebe0e2a24de0a6d6bcc2_MD5.png]]


## Neovim 中的 copy-paste

可以参考 [Provider - Neovim docs](https://neovim.io/doc/user/provider.html#provider-paste)

```lua
vim.g.clipboard = {
  name = "TmuxClipboard",
  copy = {
    ["+"] = "tmux load-buffer -w -",
    ["*"] = "tmux load-buffer -w -",
  },
  paste = {
    ["+"] = "tmux save-buffer -",
    ["*"] = "tmux save-buffer -",
  },
  cache_enabled = 1,
}
```