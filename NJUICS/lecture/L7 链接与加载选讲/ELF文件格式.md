## 1 参考文档

[ELF 格式解读-(1) elf 头部与节头](https://blog.csdn.net/qfanmingyiq/article/details/124295287)

[ELF 格式解读-符号表](https://fanmingyi.blog.csdn.net/article/details/124510909?spm=1001.2014.3001.5502)

[ELF头规则](https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html)

[ELF节规则]( https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.sheader.html#sh_flags )



![[NJUICS/lecture/L7 链接与加载选讲/可重定位文件格式视图.md#^group=YqCMhfGkRGIm6RYEzqHvK|150]]

## 2 ELF 头

### 2.1 数据结构

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


### 2.2 readelf 读

```ad-command
readelf -h xxx.o
```

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

