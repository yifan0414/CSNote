# Debian 手动安装

> 原文：[Manual Debian installation](https://archive.fo/p1ZHn)

> 译者：[飞龙](https://github.com/wizardforcel)

> 协议：[CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/)

> 自豪地采用[谷歌翻译](https://translate.google.cn/)

尽管这个部分很啰嗦，但是不推荐给那些不熟悉 VirtualBox 和 Debian 的人。此外，它是为 Windows 编写的，如果你使用其他系统，我希望，对本指南进行适当的替换相当容易。

首先，下载你需要的东西：

+   下载并安装 [VirtualBox](https://www.virtualbox.org/wiki/Downloads)。
+   下载最新的 [Debian 6 Squeeze CD 映像](http://cdimage.debian.org/debian-cd/6.0.5/amd64/iso-cd/)。你需要第一张 CD，例如`debian-6.0.5-amd64-CD-1.iso`。

对于 Windows 用户，你需要下载 [putty](ttp://www.chiark.greenend.org.uk/~sgtatham/putty/download.html)。你需要这个文件：`putty.exe`。它不需要安装，你可以像这样运行它。

## Debian 安装指南

1.  启动 VirtualBox。

    ![[attachments/c986b78ace170075eb7c76d0c48105df_MD5.png]]
    
2.  按下`New`按钮来创建新的虚拟机。在`Name`字段中输入`vm1`，之后选择`Operating System: Linux, Version: Debian (64 bit)`，之后按下`Next >`。

    ![[attachments/2526b78bd0209e80eb92df4349cb3fcf_MD5.png]]
    
3.  从内存至少选择`512 MB`。如果你的机子上安装了足够的 RAM，`1024 GB`也可以。按下`Next >`。

    ![[attachments/a9c6ab3bf6e9ee20c54e655856f78f43_MD5.png]]
    
4.  这里只需按下`Next >`。

    ![[attachments/e416e5dc173a02aa3aad087aa3c7b8fa_MD5.png]]
    
5.  选择`VDI (VirtualBox Disk Image)`，并按下`Next >`。

    ![[attachments/f8f64307d0f2c185aeb2bd8c7d4eb211_MD5.png]]
    
6.  选择`Dynamically allocated`，并按下`Next >`。

    ![[attachments/7a12279d13cc86ae36ca36008ca41c87_MD5.png]]
    
7.  在`Location`中输入`vm1`，并按下`Next >`。

    ![[attachments/79d42392716fa62aa5e1604aa8ce2850_MD5.png]]
    
8.  点击`Create`。

    ![[attachments/adb083659cd3a1d0c6add154c4f676e0_MD5.png]]
    
9.  选择`vm1`并点击`Start`。

    ![[attachments/143aab04413e219745fcbc6b62d3d983_MD5.png]]
    
0.  点击`Next >`。

    ![[attachments/0ca45cbd5d2885edde728a5eb558b179_MD5.png]]
    
1.  点击`folder button`。

    ![[attachments/5cb7e25d9dee04511cd7b26124f9f7fd_MD5.png]]
    
2.  浏览并选择你的`Debian 6 Squeeze CD-image`，点击`Open`。

    ![[attachments/5879e8aea12ca9dcabed4830c20fd104_MD5.png]]
    
3.  点击`Next >`。

    ![[attachments/925008981447327fdee3cab9e5eca366_MD5.png]]
    
4.  点击`Start`。

    ![[attachments/366e67a4f7e1ec28baaace6022471672_MD5.png]]
    
5.  关闭烦人的 VirtualBox 窗口。点击 VirtualBox 窗口内部并按下`<ENTER>`。
    ![[attachments/4f406cdcad6d719ca88531e3ce326e76_MD5.png]]
    
6.  按下`<ENTER>`。

    ![[attachments/5b1edc5d3af6f1155a341c319eddda81_MD5.png]]
    
7.  按下`<ENTER>`。

    > 译者注：这里你可以选“中文（简体）”。
    
    ![[attachments/a2a45661ad555553f820028a2094adea_MD5.png]]
    
8.  按下`<ENTER>`。

    > 译者注：这里你可以选“HongKong”。
    
    ![[attachments/e6e1b1173f41ac6c85110c2179405827_MD5.png]]
    
9.  按下`<ENTER>`。

    ![[attachments/91cbde718eadd17731f0134e5f118ad1_MD5.png]]
    
0.  输入`vm1`并按下`<ENTER>`。

    ![[attachments/f5a9ab65076e4eaccdeadefd8c62ab71_MD5.png]]
    
1.  输入`site`并按下`<ENTER>`。

    ![[attachments/94f95c9dcfd9e5b41ca758ebd936aca5_MD5.png]]
    
2.  输入`123qwe`并按下`<ENTER>`。

    ![[attachments/1b97bd01a7b36583b92b0d674a476e6d_MD5.png]]
    
3.  输入`123qwe`并按下`<ENTER>`。

    ![[attachments/f0598b8e5114a7cc11476a394ac57ab6_MD5.png]]
    
4.  输入`user1`并按下`<ENTER>`。

    ![[attachments/4e255e18f7073205d924a3f78325c77d_MD5.png]]
    
5.  按下`<ENTER>`。

    ![[attachments/babb1ae833f218fbbe19e4557d28d82c_MD5.png]]
    
6.  输入`123qwe`并按下`<ENTER>`。

    ![[attachments/8ec526207902db0fb57e1f7a8b05dbb4_MD5.png]]
    
7.  输入`123qwe`并按下`<ENTER>`。

    ![[attachments/fc043d21a5d1bca34fb37eab49552739_MD5.png]]
    
8.  如果你不知道这里做什么，只需按下`<ENTER>`。

    ![[attachments/ffc28018b03bc786725f1a03dfe06d26_MD5.png]]
    
9.  选择`Guided partitioning`并按下`<ENTER>`。

    ![[attachments/c64ba7e57b791801e5ea50b008b0a690_MD5.png]]
    
0.  选择`Guided – use entire disk`并按下`<ENTER>`。

    ![[attachments/73f08573880a51a142a930620490e040_MD5.png]]
    
1.  再次按下`<ENTER>`。

    ![[attachments/91f1dc002790ade6992ad80e63380d0c_MD5.png]]
    
2.  选择`eparate /home, /usr, /var, and /tmp partitions`并按下`<ENTER>`。

    ![[attachments/1edfb3ffcec5a553518591adc8657f73_MD5.png]]
    
3.  选择`Finish partitioning and write changes to disk`并按下`<ENTER>`。

    ![[attachments/c2ff9de14a9b820ee975ae0d3ae4b096_MD5.png]]
    
4.  选择`<Yes>`并按下`<ENTER>`。

    ![[attachments/aeb5323560fbde1a9d6df03314b421f9_MD5.png]]
    
5.  选择`<No>`并按下`<ENTER>`。

    ![[attachments/ea5f7a0dc45604671ba9680bc4ab7879_MD5.png]]
    
6.  选择`<Yes>`并按下`<ENTER>`。

    ![[attachments/449f9f6be34341bf446793a7e9c2bb58_MD5.png]]
    
7.  选择`ftp.egr.msu.edu`并按下`<ENTER>`。如果出现错误，选择其它的东西。

    ![[attachments/0d54974e499940dc1863346eb199448e_MD5.png]]

8.  再次按下`<ENTER>`。

    ![[attachments/1f2e1cec905930c7dc1f50dc59a9ea06_MD5.png]]
    
9.  选择`<No>`并按下`<ENTER>`。

    ![[attachments/2cca6148a4bad2959335ed65f211ddd7_MD5.png]]
    
0.  使用`<SPACE>`选择`SSH server and Standard system utilities`，并按下`<ENTER>`。

    ![[attachments/93cd31bc5ead1422bcad3f27db27d851_MD5.png]]
    
1.  选择`<Yes>`并按下`<ENTER>`。

    ![[attachments/a406d6b6e8d4ae965ac5248ae9d4f6b6_MD5.png]]
    
2.  选择`<Continue>`并按下`<ENTER>`。你新安装的 Debian 会重启。

    ![[attachments/c29f7a6d935034ad6c0c337395fc95bb_MD5.png]]
    
3.  点击`Devices`并选择`Network adapters`。

    ![[attachments/66cb289d47da7fdcb2e6449c94cfc6a8_MD5.png]]
    
4.  点击`Port Forwarding`。

    ![[attachments/1e9a9b03edddb884b3bac0e8b1de11cc_MD5.png]]
    
5.  点击`Plus`按钮。

    ![[attachments/d2921600392fdd96a154b13b2aef49ad_MD5.png]]
    
6.  在`Host Port`中输入`22`，`Guest Port`中输入`22`，点击`OK`。

    ![[attachments/660071950ada2ed985cb47053499533e_MD5.png]]
    
7.  再次点击`OK`。

    ![[attachments/ca3fc862da0c472545f0ca61eb7aae34_MD5.png]]
    
8.  让你的 Debian 系统运行一会儿。

    ![[attachments/67ba10c933a1f7ab5e0f2922569c8a9a_MD5.png]]
    
9.  启动`putty`，在`Host Name`中输入`localhost`（或 IP 地址），在`Port`字段中输入`22`。点击`Open`。

    ![[attachments/d75baa75bff5e714e3d845b06016d7ca_MD5.png]]
    
0.  点击`Yes`。

    ![[attachments/23914f49b29eaf798a078ddc9b00caa1_MD5.png]]
    
1.  输入`user1`，点击`<ENTER>`。输入`123qwe`，并再输入一次，来真正享受你的作品吧。

    ![[attachments/5afc9be19927baf8b64a0a52e75e5105_MD5.png]]
    
你以为这就完了吗？现在将这些输入`putty`，通过按下`<ENTER>`结束每个命令：

```
1: su
2: 123qwe
3: sed -i '/^deb cdrom.*$/d' /etc/apt/sources.list
4: aptitude update
5: aptitude install vim sudo parted
```

询问时，输入`y`并按下`<ENTER>`。

```
6: update-alternatives --config editor
```

询问时，输入`3`并按下`<ENTER>`。

```
7: sed -i 's/%sudo ALL=(ALL) ALL/%sudo ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers
8: usermod user1 -G sudo
```

关闭`putty`，再次打开它，并作为`user1`登入`vm1`，输入这个：

```
9: sudo -s
```

如果你得到了`root@vm1:/home/user1#`，那么一切正常，开瓶啤酒奖励自己吧。

## 你会看到什么

```
user1@vm1:~$ su
Password:
root@vm1:/home/user1# sed -i '/^deb cdrom.*$/d' /etc/apt/sources.list
root@vm1:/home/user1# aptitude update
Hit http://security.debian.org squeeze/updates Release.gpg
Ign http://security.debian.org/ squeeze/updates/main Translation-en
Ign http://security.debian.org/ squeeze/updates/main Translation-en_US
Hit http://security.debian.org squeeze/updates Release
Hit http://ftp.egr.msu.edu squeeze Release.gpg
Hit http://security.debian.org squeeze/updates/main Sources
Hit http://security.debian.org squeeze/updates/main amd64 Packages
Ign http://ftp.egr.msu.edu/debian/ squeeze/main Translation-en
Ign http://ftp.egr.msu.edu/debian/ squeeze/main Translation-en_US
Hit http://ftp.egr.msu.edu squeeze-updates Release.gpg
Ign http://ftp.egr.msu.edu/debian/ squeeze-updates/main Translation-en
Ign http://ftp.egr.msu.edu/debian/ squeeze-updates/main Translation-en_US
Hit http://ftp.egr.msu.edu squeeze Release
Hit http://ftp.egr.msu.edu squeeze-updates Release
Hit http://ftp.egr.msu.edu squeeze/main Sources
Hit http://ftp.egr.msu.edu squeeze/main amd64 Packages
Get:1 http://ftp.egr.msu.edu squeeze-updates/main Sources/DiffIndex [2,161 B]
Hit http://ftp.egr.msu.edu squeeze-updates/main amd64 Packages/DiffIndex
Hit http://ftp.egr.msu.edu squeeze-updates/main amd64 Packages
Fetched 2,161 B in 3s (603 B/s)
root@vm1:/home/user1# aptitude install vim sudo parted
The following NEW packages will be installed:
  libparted0debian1{a} parted sudo vim vim-runtime{a}
0 packages upgraded, 5 newly installed, 0 to remove and 0 not upgraded.
Need to get 8,231 kB of archives. After unpacking 29.8 MB will be used.
Do you want to continue? [Y/n/?] y
Get:1 http://security.debian.org/ squeeze/updates/main sudo amd64 1.7.4p4-2.squeeze.3 [610 kB]
Get:2 http://ftp.egr.msu.edu/debian/ squeeze/main libparted0debian1 amd64 2.3-5 [341 kB]
Get:3 http://ftp.egr.msu.edu/debian/ squeeze/main parted amd64 2.3-5 [156 kB]
Get:4 http://ftp.egr.msu.edu/debian/ squeeze/main vim-runtime all 2:7.2.445+hg~cb94c42c0e1a-1 [6,207 kB]
Get:5 http://ftp.egr.msu.edu/debian/ squeeze/main vim amd64 2:7.2.445+hg~cb94c42c0e1a-1 [915 kB]
Fetched 8,231 kB in 1min 18s (105 kB/s)
Selecting previously deselected package libparted0debian1.
(Reading database ... 34745 files and directories currently installed.)
Unpacking libparted0debian1 (from .../libparted0debian1_2.3-5_amd64.deb) ...
Selecting previously deselected package parted.
Unpacking parted (from .../parted_2.3-5_amd64.deb) ...
Selecting previously deselected package sudo.
Unpacking sudo (from .../sudo_1.7.4p4-2.squeeze.3_amd64.deb) ...
Selecting previously deselected package vim-runtime.
Unpacking vim-runtime (from .../vim-runtime_2%3a7.2.445+hg~cb94c42c0e1a-1_all.deb) ...
Adding 'diversion of /usr/share/vim/vim72/doc/help.txt to /usr/share/vim/vim72/doc/help.txt.vim-tiny by vim-runtime'
Adding 'diversion of /usr/share/vim/vim72/doc/tags to /usr/share/vim/vim72/doc/tags.vim-tiny by vim-runtime'
Selecting previously deselected package vim.
Unpacking vim (from .../vim_2%3a7.2.445+hg~cb94c42c0e1a-1_amd64.deb) ...
Processing triggers for man-db ...
Setting up libparted0debian1 (2.3-5) ...
Setting up parted (2.3-5) ...
Setting up sudo (1.7.4p4-2.squeeze.3) ...
No /etc/sudoers found... creating one for you.
Setting up vim-runtime (2:7.2.445+hg~cb94c42c0e1a-1) ...
Processing /usr/share/vim/addons/doc
Setting up vim (2:7.2.445+hg~cb94c42c0e1a-1) ...
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/vim (vim) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/vimdiff (vimdiff) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/rvim (rvim) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/rview (rview) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/vi (vi) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/view (view) in auto mode.
update-alternatives: using /usr/bin/vim.basic to provide /usr/bin/ex (ex) in auto mode.
root@vm1:/home/user1# update-alternatives --config editor
There are 3 choices for the alternative editor (providing /usr/bin/editor).
 
  Selection    Path                Priority   Status
------------------------------------------------------------
* 0            /bin/nano            40        auto mode
  1            /bin/nano            40        manual mode
  2            /usr/bin/vim.basic   30        manual mode
  3            /usr/bin/vim.tiny    10        manual mode
 
Press enter to keep the current choice[*], or type selection number: 3
update-alternatives: using /usr/bin/vim.tiny to provide /usr/bin/editor (editor) in manual mode.
root@vm1:/home/user1# sed -i 's/%sudo ALL=(ALL) ALL/%sudo ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers
root@vm1:/home/user1# usermod user1 -G sudo
root@vm1:/home/user1#
```

## 解释

1.  使你成为超级用户或`root`用户。
1.  你在安装过程中输入的`root`密码。
1.  修改仓库文件，因此 Debian 将尝试仅仅从互联网安装新软件。
1.  更新可用软件数据库。
1.  安装`vim`，`sudo`和`parted`包。
1.  将默认系统文本编辑器更改为`vim`。
1.  允许你通过修改`sudo`配置文件成为超级用户，而不输入密码。
1.  将你添加到`sudo`组，以便你可以通过`sudo`成为`root`。
1.  检查你是否能够成为`root`。 
