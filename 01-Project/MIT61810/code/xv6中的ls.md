---
title: xv6的ls
---

```c 
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fs.h"
#include "kernel/fcntl.h"

char*
fmtname(char *path)
{
  static char buf[DIRSIZ+1];
  char *p;

  // Find first character after last slash.
  for(p=path+strlen(path); p >= path && *p != '/'; p--)
    ;
  p++;

  // Return blank-padded name.
  if(strlen(p) >= DIRSIZ)
    return p;
  memmove(buf, p, strlen(p));
  memset(buf+strlen(p), ' ', DIRSIZ-strlen(p));
  return buf;
}

void
ls(char *path)
{
  char buf[512], *p;
  int fd;
  struct dirent de;
  struct stat st;

  if((fd = open(path, O_RDONLY)) < 0){
    fprintf(2, "ls: cannot open %s\n", path);
    return;
  }

  if(fstat(fd, &st) < 0){
    fprintf(2, "ls: cannot stat %s\n", path);
    close(fd);
    return;
  }

  switch(st.type){
  case T_DEVICE:
  case T_FILE:
    printf("%s %d %d %l\n", fmtname(path), st.type, st.ino, st.size);
    break;

  case T_DIR:
    if(strlen(path) + 1 + DIRSIZ + 1 > sizeof buf){
      printf("ls: path too long\n");
      break;
    }
    strcpy(buf, path);
    p = buf+strlen(buf);
    *p++ = '/';
    while(read(fd, &de, sizeof(de)) == sizeof(de)){
      if(de.inum == 0)
        continue;
      memmove(p, de.name, DIRSIZ);
      p[DIRSIZ] = 0;
      if(stat(buf, &st) < 0){
        printf("ls: cannot stat %s\n", buf);
        continue;
      }
      printf("%s %d %d %d\n", fmtname(buf), st.type, st.ino, st.size);
    }
    break;
  }
  close(fd);
}

int
main(int argc, char *argv[])
{
  int i;

  if(argc < 2){
    ls(".");
    exit(0);
  }
  for(i=1; i<argc; i++)
    ls(argv[i]);
  exit(0);
}

```


## fmtname

```c
char*
fmtname(char *path)
{
  static char buf[DIRSIZ+1];
  char *p;

  // Find first character after last slash.
  for(p=path+strlen(path); p >= path && *p != '/'; p--)
    ;
  p++;

  // Return blank-padded name.
  if(strlen(p) >= DIRSIZ)
    return p;
  memmove(buf, p, strlen(p));
  memset(buf+strlen(p), ' ', DIRSIZ-strlen(p));
  return buf;
}
```

这个函数的目的是返回文件的名字，例如 `/home/suyi/example` 则会返回 `example`。这里建立 buf 数组的主要目的应该是使得文件名字**具有统一的形式**。

![image.png|300](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/20240114180423.png)

## case dir

```c
case T_DIR:
    if(strlen(path) + 1 + DIRSIZ + 1 > sizeof buf){
      printf("ls: path too long\n");
      break;
    }
    strcpy(buf, path);
    p = buf+strlen(buf);
    *p++ = '/';
    while(read(fd, &de, sizeof(de)) == sizeof(de)){
      if(de.inum == 0)
        continue;
      memmove(p, de.name, DIRSIZ);
      p[DIRSIZ] = 0;
      if(stat(buf, &st) < 0){
        printf("ls: cannot stat %s\n", buf);
        continue;
      }
      printf("%s %d %d %d\n", fmtname(buf), st.type, st.ino, st.size);
    }
```

这个 `case` 语句块是处理目录类型 (`T_DIR`) 的情况。当 `ls` 命令遇到一个目录时，它会尝试列出该目录中的所有文件和子目录。

```c
if(strlen(path) + 1 + DIRSIZ + 1 > sizeof buf){
  printf("ls: path too long\n");
  break;
}
```
首先检查路径长度是否会超出缓冲区 `buf` 的大小。**`DIRSIZ` 是文件名的最大长度**，在 `fs.h` 中定义。如果路径太长，就打印错误信息并跳出 `switch` 语句。

```c
strcpy(buf, path);
p = buf+strlen(buf);
*p++ = '/';
```
将提供的路径复制到 `buf` 中，然后 `p` 指针设置为 `buf` 中路径字符串的结尾，并在路径后面添加一个斜杠（`/`），准备拼接文件名。

```c
while(read(fd, &de, sizeof(de)) == sizeof(de)){
  if(de.inum == 0)
    continue;
  memmove(p, de.name, DIRSIZ);
  p[DIRSIZ] = 0;
  if(stat(buf, &st) < 0){
    printf("ls: cannot stat %s\n", buf);
    continue;
  }
  printf("%s %d %d %d\n", fmtname(buf), st.type, st.ino, st.size);
}
```
这是一个 `while` 循环，它从目录文件描述符 `fd` 中读取目录项 `de`。`read` 函数返回读取的字节数，如果读取到的字节数等于 `sizeof(de)`（即一个目录项的大小），则表示读取成功。

- 如果 `de.inum`（目录项的 inode 号）为 0，表示这个目录项未被使用（可能是已删除的文件占据的位置），则跳过这个目录项，继续下一个循环迭代。
- `memmove` 将目录项的名字拷贝到 `buf` 中 `p` 指针指向的位置，然后在 `DIRSIZ` 位置处添加一个空字符 `\0` 来结束字符串，形成完整的文件路径。
- `stat` 函数用于获取该路径的文件状态，并将其存储在 `st` 中。如果 `stat` 调用失败，则打印错误信息并继续下一个循环迭代。
- 如果 `stat` 调用成功，则使用 `fmtname` 函数格式化文件名，并打印出文件的信息：文件名、类型 (`st.type`)、inode 号 (`st.ino`) 和大小 (`st.size`)。

这个 `case` 语句的目的是遍历目录中的每个文件和子目录，并打印出它们的信息。这是 `ls` 命令的基本功能，用于列出目录内容。

## question

###  `.` 和 `..` 是每个目录创建时就有的“文件”，如何生成的（在 sysfile. c 276 行）
```c
if(type == T_DIR){  // Create . and .. entries.
    // No ip->nlink++ for ".": avoid cyclic ref count.
    if(dirlink(ip, ".", ip->inum) < 0 || dirlink(ip, "..", dp->inum) < 0)
      goto fail;
}
```