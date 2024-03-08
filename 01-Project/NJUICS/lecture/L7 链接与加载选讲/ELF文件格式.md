## 1 参考文档

[ELF 格式解读-(1) elf 头部与节头](https://blog.csdn.net/qfanmingyiq/article/details/124295287)

[ELF 格式解读-符号表](https://fanmingyi.blog.csdn.net/article/details/124510909?spm=1001.2014.3001.5502)

[ELF头规则](https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html)

[ELF节规则]( https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.sheader.html#sh_flags )



![[可重定位文件格式视图#^group=YqCMhfGkRGIm6RYEzqHvK|150]]

## 2 ELF 头

### 2.1 数据结构

以下是 32 位系统对应的数据结构，共占 52 字节。

```txt
#define EI_NIDENT 16

typedef struct {
        unsigned char   e_ident[EI_NIDENT];
        Elf32_Half      e_type;
        Elf32_Half      e_machine;
        Elf32_Word      e_version;
        Elf32_Addr      e_entry;
        Elf32_Off       e_phoff;
        Elf32_Off       e_shoff;
        Elf32_Word      e_flags;
        Elf32_Half      e_ehsize;
        Elf32_Half      e_phentsize;
        Elf32_Half      e_phnum;
        Elf32_Half      e_shentsize;
        Elf32_Half      e_shnum;
        Elf32_Half      e_shstrndx;
} Elf32_Ehdr;
```

文件开头几个字节称为**魔数**，通常用来确定文件的类型或格式。在加载或读取文件时，可用魔数确认文件类型是否正确。在 32 位 ELF 头的数据结构中，字段 e_ident 是一个长度为 16 的字节序列，其中，最开始的 4 字节为魔数，用来标识是否为 ELF 文件，第一个字节为 0x7F，后面三个字节分别为‘E’、‘L’、‘F’。再后面的 12 个字节中，主要包含一些标识信息，例如，标识是 32 位还是 64 位格式、标识数据按小端还是大端方式存放、标识 ELF 头的版本号等。
- 字段 e_type 用于说明目标文件的类型是可重定位文件、可执行文件、共享库文件，还是其他类型文件。
- 字段 e_machine 用于指定机器结构类型，如 IA-32、SPARC V9、AMD64 等。
- 字段 e_version 用于标识目标文件版本。字段 e_entry 用于指定系统将控制权转移到的起始虚拟地址 (人口点)，如果文件没有关联的入口点，则为零。例如，对于可重定位文件，此字段为 0。
- 字段 e_ehsize 用于说明 ELF 头的大小（以字节为单位）。
- 字段 e_shoff 指出节头表在文件中的偏移量（以字节为单位）。
- 字段 e_shentsize 表示节头表中一个表项的大小（以字节为单位），所有表项大小相同。
- 字段 e_shnum 表示节头表中的项数。
- 因此 e_shentsize 和 e_shnum 共同指定了节头表的大小（以字节为单位）。仅 ELF 头在文件中具有固定位置，即总是在最开始的位置，其他部分的位置由 ELF 头和节头表指出，不需要具有固定的顺序。

### 2.2 readelf 读

> [!command] readelf -h xxx.o
> 

```txt
ELF Header:
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF32
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              REL (Relocatable file)
  Machine:                           Intel 80386
  Version:                           0x1
  Entry point address:               0x0
  Start of program headers:          0 (bytes into file)
  Start of section headers:          852 (bytes into file)
  Flags:                             0x0
  Size of this header:               52 (bytes)
  Size of program headers:           0 (bytes)
  Number of program headers:         0
  Size of section headers:           40 (bytes)
  Number of section headers:         13
  Section header string table index: 12
```

## 3 符号表

### 3.1 数据结构

```txt
typedef struct {
	Elf32_Word	    st_name;
	Elf32_Addr	    st_value;
	Elf32_Word	    st_size;
	unsigned char	st_info;
	unsigned char	st_other;
	Elf32_Half	    st_shndx;
} Elf32_Sym;
```

1. `st_name`: 此成员保存了一个索引，该索引指向对象文件的符号字符串表，该表存储了符号名称的字符表示。如果值为非零，则表示一个字符串表索引，该索引给出了符号名称。否则，符号表条目没有名称。
2. `st_value`: 该成员提供了关联符号的值。根据上下文，这可能是一个绝对值、地址等；详细信息请参见下文。
	- **在可重定位目标文件中，是指符号所在位置相对于所在节起始位置的值。**
	- **在可执行目标文件和共享目标文件中，是符号所在的虚拟地址。**
3. `st_size`: 许多符号都有相关的大小。例如，数据对象的大小是对象中包含的字节数。如果符号没有大小或者大小未知，则该成员为0。
4. `st_info`: 该成员指定符号的类型和绑定属性。下面列出了值和含义的列表。符号类型占低 4 位，符号绑定占高 4 位。
```txt
#define ELF32_ST_BIND(i)   ((i)>>4)
#define ELF32_ST_TYPE(i)   ((i)&0xf)
#define ELF32_ST_INFO(b,t) (((b)<<4)+((t)&0xf))
```

符号类型可以是未指定 (NOTYPE)、变量（OBJECT）、函数（FUNC）、节（SECTION）等。当类型是“节”时，其表项主要用于重定位。绑定属性可以是本地（LOCAL）、全局（GLOBAL）、弱（WEAK）等。


## 3.2 readelf 读

> [!command] readelf -s xxx.o
> 

```txt
Symbol table '.symtab' contains 15 entries:
   Num:    Value  Size Type    Bind   Vis      Ndx Name
     0: 00000000     0 NOTYPE  LOCAL  DEFAULT  UND
     1: 00000000     0 FILE    LOCAL  DEFAULT  ABS main.c
     2: 00000000     0 SECTION LOCAL  DEFAULT    1
     3: 00000000     0 SECTION LOCAL  DEFAULT    3
     4: 00000000     0 SECTION LOCAL  DEFAULT    4
     5: 00000000     0 SECTION LOCAL  DEFAULT    5
     6: 00000000     0 SECTION LOCAL  DEFAULT    7
     7: 00000000     0 SECTION LOCAL  DEFAULT    8
     8: 00000000     0 SECTION LOCAL  DEFAULT    6
     9: 00000000    64 OBJECT  GLOBAL DEFAULT    5 zzGSwc
    10: 00000004     4 OBJECT  GLOBAL DEFAULT  COM phase
    11: 00000004     4 OBJECT  GLOBAL DEFAULT  COM phase_id
    12: 00000040    15 OBJECT  GLOBAL DEFAULT    5 challenge
    13: 00000000    64 FUNC    GLOBAL DEFAULT    1 main
    14: 00000000     0 NOTYPE  GLOBAL DEFAULT  UND puts
```