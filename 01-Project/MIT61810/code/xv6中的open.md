# 0 code

```c
uint64
sys_open(void)
{
  char path[MAXPATH];
  int fd, omode;
  struct file *f;
  struct inode *ip;
  int n;

  argint(1, &omode);
  if((n = argstr(0, path, MAXPATH)) < 0)
    return -1;

  begin_op();

  if(omode & O_CREATE){
    ip = create(path, T_FILE, 0, 0);
    if(ip == 0){
      end_op();
      return -1;
    }
  } else {
    if((ip = namei(path)) == 0){
      end_op();
      return -1;
    }
    ilock(ip);
    if(ip->type == T_DIR && omode != O_RDONLY){
      iunlockput(ip);
      end_op();
      return -1;
    }
  }

  if(ip->type == T_DEVICE && (ip->major < 0 || ip->major >= NDEV)){
    iunlockput(ip);
    end_op();
    return -1;
  }

  // 分配一个 `file` 结构体和一个文件描述符。如果任何一个分配失败，释放资源并返回错误。
  if((f = filealloc()) == 0 || (fd = fdalloc(f)) < 0){
    if(f)   // 意味着 f 成功分配，但是 fd 分配失败了，所以要释放
      fileclose(f);
    iunlockput(ip);
    end_op();
    return -1;
  }

  if(ip->type == T_DEVICE){
    f->type = FD_DEVICE;
    f->major = ip->major;
  } else {
    f->type = FD_INODE;
    f->off = 0;
  }
  f->ip = ip;
  f->readable = !(omode & O_WRONLY);
  f->writable = (omode & O_WRONLY) || (omode & O_RDWR);

  if((omode & O_TRUNC) && ip->type == T_FILE){
    itrunc(ip);
  }

  iunlock(ip);
  end_op();

  return fd;
}

```

# 1 analysis

## 1.1 summary
这个函数 `sys_open` 是操作系统内核（很可能是类 Unix 系统，例如 xv6）中处理文件打开请求的系统调用。它实现了打开文件的逻辑，包括创建新文件、打开已存在的文件、以及设置文件的不同模式（只读、只写、读写等）。下面是对这个函数的逐行解释：

1. **函数声明和变量初始化**:
   - `uint64 sys_open(void)`: 这是函数的声明，表明它返回一个 `uint64` 类型的值，可能是文件描述符。
   - 定义了一些局部变量，用于存储路径、文件描述符、文件和 inode 的指针等。

2. **获取参数**:
   - `argint(1, &omode)`: 从系统调用的参数中获取文件的打开模式（例如，只读、只写等）。
   - `argstr(0, path, MAXPATH)`: 从系统调用的参数中获取要打开或创建的文件路径。

3. **开始文件操作**:
   - `begin_op()`: 开始一个文件系统操作，可能是为了同步或日志记录。

4. **处理文件创建请求**:
   - 如果请求中包含 `O_CREATE`（创建文件的标志），则尝试创建一个新文件。如果创建失败，则返回错误。

5. **打开已存在的文件**:
   - 如果不是创建操作，则尝试通过路径找到已存在的文件（inode）。如果文件不存在，返回错误。
   - 检查是否试图以写模式打开一个目录，这是不允许的。

6. **检查设备类型**:
   - 如果文件是一个设备文件，检查它的主设备号是否有效。

7. **分配文件描述符**:
   - 分配一个 `file` 结构体和一个文件描述符。如果任何一个分配失败，释放资源并返回错误。

8. **设置文件类型和权限**:
   - 设置文件结构的类型（设备或 inode）和偏移量。
   - 根据打开模式设置文件为可读或可写。

9. **处理截断请求**:
   - 如果文件是普通文件且请求中包含 `O_TRUNC`（截断文件的标志），则截断文件。

10. **完成操作**:
    - 解锁 inode，完成文件系统操作，并返回文件描述符。

整体来说，这个函数处理了各种与打开文件相关的情况，包括权限检查、错误处理、资源分配等。通过这个函数，内核能够根据调用者提供的参数和系统的状态来打开或创建文件，并将其与一个文件描述符相关联。

## 1.2 why open always use the lowest num for fd?

```c
// Allocate a file descriptor for the given file.
// Takes over file reference from caller on success.
static int
fdalloc(struct file *f)
{
  int fd;
  struct proc *p = myproc();

  for(fd = 0; fd < NOFILE; fd++){
    if(p->ofile[fd] == 0){
      p->ofile[fd] = f;
      return fd;
    }
  }
  return -1;
}

```