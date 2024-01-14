## 0 echo

```c
#include "kernel/types.h"
#include "user/user.h"

// echo.c

int
main(int argc, char *argv[])
{
  int i;

  for(i = 1; i < argc; i++){
    write(1, argv[i], strlen(argv[i]));
    if(i + 1 < argc){
      write(1, " ", 1);
    } else {
      write(1, "\n", 1);
    }
  }
  exit(0);
}
```


## 1 copy input to output

```c
// ex1.c: copy input to output.

#include "kernel/types.h"
#include "user/user.h"

int
main()
{
  char buf[64];

  while(1){
    int n = read(0, buf, sizeof(buf));
    if(n <= 0)
      break;
    write(1, buf, n);
  }

  exit(0);
}
```

## 2 create a file, write to it.

```c
  
// ex2.c: create a file, write to it.

#include "kernel/types.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int
main()
{
  int fd = open("out", O_WRONLY | O_CREATE | O_TRUNC);

  printf("open returned fd %d\n", fd);

  write(fd, "ooo\n", 4);

  exit(0);
}
```


## 3 create a new process with fork()

```c
  
// ex3.c: create a new process with fork()

#include "kernel/types.h"
#include "user/user.h"

int
main()
{
  int pid;

  pid = fork();

  printf("fork() returned %d\n", pid);

  if(pid == 0){
    printf("child\n");
  } else {
    printf("parent\n");
  }
  
  exit(0);
}
```

## 4 replace a process with an executable file

```c
  
// ex4.c: replace a process with an executable file

#include "kernel/types.h"
#include "user/user.h"

int
main()
{
  char *argv[] = { "echo", "this", "is", "echo", 0 };

  exec("echo", argv);

  printf("exec failed!\n");

  exit(0);
}
```


## 5 fork then exec

```c
  
#include "kernel/types.h"
#include "user/user.h"

// ex5.c: fork then exec

int
main()
{
  int pid, status;

  pid = fork();
  if(pid == 0){
    char *argv[] = { "echo", "THIS", "IS", "ECHO", 0 };
    exec("echo", argv);
    printf("exec failed!\n");
    exit(1);
  } else {
    printf("parent waiting\n");
    wait(&status);
    printf("the child exited with status %d\n", status);
  }

  exit(0);
}
```

## 6 run a command with output redirected

```c
  
#include "kernel/types.h"
#include "user/user.h"
#include "kernel/fcntl.h"

// ex6.c: run a command with output redirected

int
main()
{
  int pid;

  pid = fork();
  if(pid == 0){
    close(1);
    open("out", O_WRONLY | O_CREATE | O_TRUNC);

    char *argv[] = { "echo", "this", "is", "redirected", "echo", 0 };
    exec("echo", argv);
    printf("exec failed!\n");
    exit(1);
  } else {
    wait((int *) 0);
  }

  exit(0);
}
```


## 7 communication over a pipe

```c
  
// ex7.c: communication over a pipe

#include "kernel/types.h"
#include "user/user.h"

int
main()
{
  int fds[2];
  char buf[100];
  int n;

  // create a pipe, with two FDs in fds[0], fds[1].
  pipe(fds);
  
  // write to the pipe
  write(fds[1], "xyz\n", 4);

  // read from the pipe
  n = read(fds[0], buf, sizeof(buf));

  // display the results on the terminal
  write(1, buf, n);

  exit(0);
}
```

## 8 communication between two processes

```c
#include "kernel/types.h"
#include "user/user.h"

// ex8.c: communication between two processes

int
main()
{
  int n, pid;
  int fds[2];
  char buf[100];
  
  // create a pipe, with two FDs in fds[0], fds[1].
  pipe(fds);

  pid = fork();
  if (pid == 0) {
    // child
    write(fds[1], "this is ex8\n", 12);
  } else {
    // parent
    n = read(fds[0], buf, sizeof(buf));
    write(1, buf, n);
  }

  exit(0);
}
```

## 9 list file names in the current directory

```c
#include "kernel/types.h"
#include "user/user.h"

// ex9.c: list file names in the current directory

struct dirent {
  ushort inum;
  char name[14];
};

int
main()
{
  int fd;
  struct dirent e;

  fd = open(".", 0);
  while(read(fd, &e, sizeof(e)) == sizeof(e)){
    if(e.name[0] != '\0'){
      printf("%s\n", e.name);
    }
  }
  exit(0);
}
```