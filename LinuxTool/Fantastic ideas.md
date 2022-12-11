#### curl 和 wget 的区别
根据 `tldr` 的显示, curl 是用来向服务器发送数据或者从服务器获得数据, wget是从服务器上下载文件.
```
curl

  Transfers data from or to a server.
  Supports most protocols, including HTTP, FTP, and POP3.
  More information: https://curl.se.

  - Download the contents of a URL to a file:
    curl http://example.com --output filename
wget

  Download files from the Web.
  Supports HTTP, HTTPS, and FTP.
  More information: https://www.gnu.org/software/wget.

  - Download the contents of a URL to a file (named "foo" in this case):
    wget https://example.com/foo
```

#### chmod 改变了谁的权限
通过 [[1 Lecture overview and Shell#^lmmcdg | 改变文件的权限]] 可以知道, chmod 可以让用户不允许访问文件, 修改文件夹内容等等. 但是如果我再通过 chmod 改变回来不就行了吗, 通过测试 `chmod +rwx` 并不会使用用户密码验证. #todo 

#### 一个神奇的命令

```
wget -r -p -U Mozilla <url>
```

这个命令可以下载一个博客网站所有的内容, 包括源代码