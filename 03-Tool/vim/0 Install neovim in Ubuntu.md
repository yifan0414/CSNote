### [AppImage ("universal" Linux package)](https://github.com/neovim/neovim/wiki/Installing-Neovim#appimage-universal-linux-package)

The [Releases](https://github.com/neovim/neovim/releases) page provides an [AppImage](https://appimage.org/) that runs on most Linux systems. No installation is needed, just download `nvim.appimage` and run it. (It might not work if your Linux distribution is more than 4 years old.)

```
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
chmod u+x nvim.appimage
./nvim.appimage
```

然后可以使用下面的命令

```
mv nvim.appimage /usr/local/bin
```
