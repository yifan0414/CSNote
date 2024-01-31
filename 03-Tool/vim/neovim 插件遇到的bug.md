# 1 kanagawa

![LLa5Y9](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/LLa5Y9.png)

# 2 Lsp hover


我调用 `vim.lsp.buf.hover` 来显示相关信息，但其调用的 `float window` 的位置却显示不正确，如下图所示：

![ZHdJe6](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/ZHdJe6.png)

![MbKlgf](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/MbKlgf.png)

通过查看源码可以知道，这个窗口是 noice 负责的，而 noice 又是通过调用 nui 配置的，所以**修改 nui** 的源码可以改变其位置

![Rck4Nt](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Rck4Nt.png)


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