## 理论

```
Opcode      Instruction      Clocks   Description

2C  ib      SUB AL,imm8      2        Subtract immediate byte from AL
2D  iw      SUB AX,imm16     2        Subtract immediate word from AX
2D  id      SUB EAX,imm32    2        Subtract immediate dword from EAX
80  /5 ib   SUB r/m8,imm8    2/7      Subtract immediate byte from r/m byte
81  /5 iw   SUB r/m16,imm16  2/7      Subtract immediate word from r/m word
81  /5 id   SUB r/m32,imm32  2/7      Subtract immediate dword from r/m
                                      dword
83  /5 ib   SUB r/m16,imm8   2/7      Subtract sign-extended immediate byte
                                      from r/m word
83  /5 ib   SUB r/m32,imm8   2/7      Subtract sign-extended immediate byte
                                      from r/m dword
28  /r      SUB r/m8,r8      2/6      Subtract byte register from r/m byte
29  /r      SUB r/m16,r16    2/6      Subtract word register from r/m word
29  /r      SUB r/m32,r32    2/6      Subtract dword register from r/m
                                      dword
2A  /r      SUB r8,r/m8      2/7      Subtract r/m byte from byte register
2B  /r      SUB r16,r/m16    2/7      Subtract r/m word from word register
2B  /r      SUB r32,r/m32    2/7      Subtract r/m dword from dword
                                      register
```

我们这里实现的是

```
83  /5 ib   SUB r/m16,imm8   2/7      Subtract sign-extended immediate byte
                                      from r/m word
83  /5 ib   SUB r/m32,imm8   2/7      Subtract sign-extended immediate byte
                                      from r/m dword
```


https://github.com/SnakeHit/ics2020/commit/77ecfba198c22a9261bdef910316228b36ed43a9