#### 1.为什么要在 Nemu 的黑色窗口中按键，才会被 am 中的 `AM_INPUT_KEYBRD` 捕捉到。✅
将下面的代码注释掉，就不会生成黑色窗口，按键也不会被捕捉到。
**这是通过 SDL_Event 控制的，见下一个问题。**
![[Pasted image 20231027032543.png]]

#### 2.在 Nemu 中，我按下键盘然后被 Nemu 捕捉是什么时候发生的 ✅

```c
#define KEYDOWN_MASK 0x8000

void __am_input_keybrd(AM_INPUT_KEYBRD_T *kbd) {
  /* kbd->keydown = 0; */
  /* kbd->keycode = AM_KEY_NONE; */
  uint32_t k = inl(KBD_ADDR);   // 读取端口
  kbd->keydown = (k & KEYDOWN_MASK ? true : false);
  kbd->keycode = k & (~KEYDOWN_MASK);
}

size_t events_read(void *buf, size_t offset, size_t len) {
  AM_INPUT_KEYBRD_T ev = io_read(AM_INPUT_KEYBRD); // 读取键盘端口
  if (ev.keycode == AM_KEY_NONE) return 0;
  return snprintf(buf, len, "%s %s", ev.keydown ? "kd" : "ku", keyname[ev.keycode]);
}
```

我们通过调用 `__am_input_keybrd` 函数来读取 KBD_ADDR 的端口，这个 `inl` 指令在 NEMU 中在读取键盘码之前会调用回调函数（设备真正的功能）。回调函数会模拟硬件的功能将要读取的值（键盘码）放到端口上。

```c
static void i8042_data_io_handler(uint32_t offset, int len, bool is_write) {
  assert(!is_write);
  assert(offset == 0);
  if (key_f != key_r) {
    i8042_data_port_base[0] = key_queue[key_f];
    key_f = (key_f + 1) % KEY_QUEUE_LEN;
  }
  else {
    i8042_data_port_base[0] = _KEY_NONE;
  }
}
```

那我们的按键是什么时候被捕捉到的呢？

```c
void cpu_exec(uint64_t n) {
   · · · · · ·
#ifdef HAS_IOE
    extern void device_update();
    device_update();
#endif
   · · · · · ·
}

void device_update() {
  if (!device_update_flag) {
    return;
  }
  device_update_flag = false;
  vga_update_screen();

  SDL_Event event;
  while (SDL_PollEvent(&event)) {
    switch (event.type) {
      case SDL_QUIT:
        nemu_state.state = NEMU_QUIT;
        break;
      // If a key was pressed
      case SDL_KEYDOWN:
      case SDL_KEYUP: {
        uint8_t k = event.key.keysym.scancode;
        bool is_keydown = (event.key.type == SDL_KEYDOWN);
        send_key(k, is_keydown); // 存入键盘码
        break;
      }
      default: break;
    }
  }
}
```

> [!chatgpt]
> 这段代码是一个事件循环，通常用于处理用户输入事件和其他类型的事件。它使用了SDL（Simple DirectMedia Layer）库来处理事件。让我解释这段代码的主要部分：
> 
> 1. `SDL_Event event;`：这一行定义了一个名为 `event` 的 `SDL_Event` 结构，用于存储从事件队列中接收到的事件。
> 
> 2. `while (SDL_PollEvent(&event))`：这是一个循环，它使用 `SDL_PollEvent` 函数来不断检查事件队列中是否有待处理的事件。`SDL_PollEvent` 函数会从事件队列中取出一个事件并将其存储在 `event` 结构中。循环会一直运行，直到事件队列为空。
> 
> 3. `switch (event.type)`：这是一个 `switch` 语句，根据事件的类型来执行不同的操作。`event.type` 存储了当前事件的类型，例如 `SDL_QUIT` 表示退出事件，`SDL_KEYDOWN` 表示按键按下事件，`SDL_KEYUP` 表示按键释放事件。
> 
> 4. `case SDL_QUIT:`：如果事件类型是退出事件，执行下面的代码块。在这里，它将 `nemu_state.state` 的状态设置为 `NEMU_QUIT`，这可能是表示退出应用程序的一种方式。
> 
> 5. `case SDL_KEYDOWN:` 和 `case SDL_KEYUP:`：如果事件类型是按键按下事件或按键释放事件，执行相同的代码块。在这里，它从事件中提取按键的扫描码（`event.key.keysym.scancode`）和按键的类型（按下或释放），然后调用 `send_key` 函数来处理按键事件。这可能是将按键事件传递给应用程序的一部分，以便执行相应的操作。
> 
> 6. `default:`：如果事件的类型不是上述提到的任何一种，就会执行这里的代码块。通常，这部分不执行任何操作，相当于忽略不处理。
> 
> 总之，这段代码是一个事件处理循环，它不断检查事件队列中的事件，并根据事件的类型执行不同的操作。根据事件的类型，它可以处理退出事件、按键按下事件和按键释放事件。这通常用于实现交互性应用程序，以响应用户的输入和其他事件。

#### 3.一切都是文件究竟是什么意思？

广义来说，一切都是文件意味着我们对设备的操作都可以抽象为对文件的操作，然后具体执行由操作系统控制。

> [!chatgpt]
> "一切都是文件" 是Unix和Unix-like操作系统的设计哲学之一，它强调了文件系统的普遍性和一致性。这个理念的核心概念是，操作系统将许多资源和设备（包括硬件设备、网络套接字、进程等）都视为文件，并提供了一种统一的文件系统接口，使得用户和程序可以以类似文件的方式与这些资源进行交互。虽然这是Unix设计的一个关键特点，但不是绝对真实的。
> 
> 这个理念的好处包括了提供了一种通用的方法来访问和操作各种资源，使编程更加简单和一致。例如，你可以使用类似的文件操作函数来读取文件、读取键盘输入、读取网络套接字数据等。这简化了编程，并减少了需要记住和处理的不同接口的数量。
> 
> 然而，尽管在Unix系统中，许多资源和设备都以文件的形式暴露出来，但并不是所有的操作都可以直接抽象为文件的操作。有一些特定的操作需要使用专门的系统调用和接口，如进程控制、内存分配、多线程等。因此，"一切都是文件" 是一个高度抽象的思想，有时需要在特定情况下使用更高级别的接口。
> 
> 总的来说，"一切都是文件" 是一个有益的思维方式，特别是在Unix系统编程中，但在现实中并不是绝对正确的。它强调了操作系统提供的一致性和通用性，但仍然需要在不同情况下了解不同的接口和操作。

比如：我们使用 `cat /proc/cpuinfo` 来获得 cpu 的信息，但 cpuinfo 这个文件是**空**的。但如果使用 vim 或者 cat 打开，cpuinfo 就不为空，可以证明在操作系统层面打开这个文件是由**特殊**的函数控制的。
![[Pasted image 20231027034804.png]]


> [!chatgpt]
> `cpuinfo` 文件通常不是一个普通的文本文件，而是一个特殊的虚拟文件，它是 `/proc` 文件系统的一部分，用于提供关于系统CPU的信息。因此，使用传统的文件大小查看工具如 `du` 来查看 `cpuinfo` 的文件大小可能会导致其大小为空或非常小。
> 
> `/proc/cpuinfo` 中包含的信息通常是动态生成的，而不是存储在文件中的静态数据。每次你读取 `/proc/cpuinfo` 文件时，内核都会实时生成文件的内容，以反映当前系统的CPU信息。这就是为什么你在使用 `vim` 打开文件时看到了内容，而在使用 `du` 查看文件大小时可能看到空文件或非常小的文件大小。
> 
> 如果你需要查看有关系统CPU的信息，可以使用命令行工具如 `cat` 来查看 `/proc/cpuinfo` 文件的内容，例如：
> 
> ~~~bash
> cat /proc/cpuinfo
> ~~~
> 
> 这将显示有关系统 CPU 的详细信息。请注意，不要试图编辑 `/proc/cpuinfo` 文件，因为它只是一个虚拟文件，任何更改都不会对实际硬件产生影响。

> [!question] /proc/cpuinfo 是一个虚拟文件，那么当我 cat /proc/cpuinfo 时，为什么会得到信息，这个信息是如何产生的呢
> 
> `/proc/cpuinfo` 是 Linux 系统中 `/proc` 文件系统的一部分，它是一个虚拟文件系统，也称为伪文件系统。`/proc` 文件系统不在硬盘上存储数据，而是在内存中动态生成的，并且直接由内核提供信息。当你执行 `cat /proc/cpuinfo` 命令时，这里发生的事情可以分解为以下几个步骤：
> 
> 1. **访问 `/proc/cpuinfo`**:
>    - 当你运行 `cat /proc/cpuinfo` 时，系统会尝试读取 `/proc/cpuinfo` 文件的内容。
>    - 尽管 `/proc/cpuinfo` 看起来像是一个普通文件，但它实际上并不存在于磁盘上。相反，它是由内核在运行时动态生成的。
> 
> 2. **内核生成信息**:
>    - Linux 内核有一个 `/proc` 文件系统的处理模块，负责处理对 `/proc` 下文件的读取请求。
>    - 当 `/proc/cpuinfo` 被读取时，内核会动态生成包含当前 CPU 信息的数据。这些信息包括 CPU 型号、核心数、速度、缓存大小等。
> 
> 3. **输出到终端**:
>    - 内核将这些信息传递给 `cat` 命令，`cat` 命令随后将这些信息输出到终端。
>    - 所以，你在终端看到的 CPU 信息实际上是内核实时生成的，而不是从磁盘上读取的静态数据。
> 
> 4. **即时更新**:
>    - 由于 `/proc/cpuinfo` 是动态生成的，它总是反映当前系统的最新状态。每次你读取 `/proc/cpuinfo` 时，内核都会生成最新的 CPU 信息。
> 
> 总之，`/proc/cpuinfo` 是一个虚拟文件，它提供了一种机制，使得用户和程序能够以读取文件的方式获取系统信息。这种方法在 Linux 系统中非常常见，它允许内核以一种对用户友好的方式来呈现复杂的系统信息。这种机制不仅适用于 CPU 信息，还适用于许多其他类型的系统信息。


> [!question] 这个读命令是如何捕捉的，或者是在哪个步骤被内核的处理模块捕捉到的
> 
> 当您执行像 `cat /proc/cpuinfo` 这样的命令来读取 `/proc` 文件系统中的文件时，这个读操作是通过标准的文件系统接口由操作系统内核捕获和处理的。这个过程大致可以分为以下几个步骤：
> 
> 1. **系统调用**:
>    - 当您执行 `cat /proc/cpuinfo` 命令时，`cat` 程序会发起一个读文件的系统调用。在 Linux 中，这通常是 `read()` 系统调用。
>    - 系统调用是用户空间程序（如 `cat`）请求内核提供服务的标准方式。在这个案例中，服务是读取文件的内容。
> 
> 2. **内核的 VFS 层**:
>    - 当系统调用到达内核时，它首先通过虚拟文件系统（VFS）层。VFS 提供了一个统一的接口来处理所有文件系统的操作，无论这些文件系统是物理的（如 ext4）、网络的（如 NFS）还是虚拟的（如 `/proc`）。
>    - VFS 根据文件路径（这里是 `/proc/cpuinfo`）确定哪个文件系统和哪个文件要处理这个请求。
> 
> 3. **`/proc` 文件系统处理**:
>    - `/proc` 文件系统注册了自己的一套处理函数来处理对 `/proc` 中文件的操作。所以，当 VFS 确定请求针对的是 `/proc/cpuinfo` 时，它会调用 `/proc` 文件系统的相应函数。
>    - 这个特定的处理函数是内核中为 `/proc/cpuinfo` 定制的，用于生成当前 CPU 的相关信息。
> 
> 4. **动态生成内容**:
>    - `/proc/cpuinfo` 的处理函数在内核中动态生成关于 CPU 的信息，如型号、核心数、速度等。这个信息是实时从系统的当前状态中获取的。
>    - 然后，这些生成的数据被传递回系统调用，并最终回到 `cat` 程序。
> 
> 5. **输出到用户空间**:
>    - `cat` 程序接收到从 `/proc/cpuinfo` 读取的数据，并将其输出到标准输出（通常是终端或命令行界面）。
> 
> 总的来说，这个过程涉及用户空间程序（`cat`）、系统调用接口、内核的虚拟文件系统层和 `/proc` 文件系统的特定处理逻辑。这种机制允许内核以文件的形式向用户空间程序提供各种系统信息。


#### 4 `\n` 刷新缓冲区

![]( https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/20240120090510.png )

可以看到，如果我不加换行符的情况下，需要等到缓冲区慢了之后才能输出。


#### 5 navy 上应用程序的 printf 用的是 am 的 klib 的还是 navy, libc 的呢？