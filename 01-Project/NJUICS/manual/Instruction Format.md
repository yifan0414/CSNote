
All instruction encodings are subsets of the general instruction format shown in [Figure 17-1](https://nju-projectn.github.io/i386-manual/s17_02.htm#fig17-1) . Instructions consist of optional instruction prefixes, one or two primary opcode bytes, possibly an address specifier consisting of the ModR/M byte and the SIB (Scale Index Base) byte, a displacement, if required, and an immediate data field, if required.

Smaller encoding fields can be defined within the primary opcode or opcodes. These fields define the direction of the operation, the size of the displacements, the register encoding, or sign extension; encoding fields vary depending on the class of operation.

Most instructions that can refer to an operand in memory have an addressing form byte following the primary opcode byte(s). This byte, called the ModR/M byte, specifies the address form to be used. Certain encodings of the ModR/M byte indicate a second addressing byte, the SIB (Scale Index Base) byte, which follows the ModR/M byte and is required to fully specify the addressing form.

Addressing forms can include a displacement immediately following either the ModR/M or SIB byte. If a displacement is present, it can be 8-, 16- or 32-bits.

If the instruction specifies an immediate operand, the immediate operand always follows any displacement bytes. The immediate operand, if specified, is always the last field of the instruction.

The following are the allowable instruction prefix codes:
```txt
F3H    REP prefix (used only with string instructions)
F3H    REPE/REPZ prefix (used only with string instructions
F2H    REPNE/REPNZ prefix (used only with string instructions)
F0H    LOCK prefix
```

The following are the segment override prefixes:

```txt
2EH    CS segment override prefix
36H    SS segment override prefix
3EH    DS segment override prefix
26H    ES segment override prefix
64H    FS segment override prefix
65H    GS segment override prefix
66H    Operand-size override
67H    Address-size override
```

Figure 17-1.  80386 Instruction Format

```txt
+---------------+---------------+---------------+---------------+
|  INSTRUCTION  |   ADDRESS-    |    OPERAND-   |   SEGMENT     |
|    PREFIX     |  SIZE PREFIX  |  SIZE PREFIX  |   OVERRIDE    |
|---------------+---------------+---------------+---------------|
|     0 OR 1         0 OR 1           0 OR 1         0 OR 1     |
|- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -|
|                        NUMBER OF BYTES                        |
+---------------------------------------------------------------+

+----------+-----------+-------+------------------+-------------+
|  OPCODE  |  MODR/M   |  SIB  |   DISPLACEMENT   |  IMMEDIATE  |
|          |           |       |                  |             |
|----------+-----------+-------+------------------+-------------|
|  1 OR 2     0 OR 1    0 OR 1      0,1,2 OR 4       0,1,2 OR 4 |
|- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -|
|                        NUMBER OF BYTES                        |
+---------------------------------------------------------------+
```


## 1 ModR/M and SIB Bytes

The ModR/M and SIB bytes follow the opcode byte(s) in many of the 80386 instructions. They contain the following information:

- The indexing type or register number to be used in the instruction
- The register to be used, or more information to select the instruction
- The base, index, and scale information

The ModR/M byte contains three fields of information:

- The mod field, which occupies the two most significant bits of the byte, combines with the r/m field to form 32 possible values: eight registers and 24 indexing modes
- The reg field, which occupies the next three bits following the mod field, specifies either a register number or three more bits of opcode information. The meaning of the reg field is determined by the first (opcode) byte of the instruction.
- The r/m field, which occupies the three least significant bits of the byte, can specify a register as the location of an operand, or can form part of the addressing-mode encoding in combination with the field as described above

The based indexed and scaled indexed forms of 32-bit addressing require the SIB byte. The presence of the SIB byte is indicated by certain encodings of the ModR/M byte. The SIB byte then includes the following fields:

- The ss field, which occupies the two most significant bits of the byte, specifies the scale factor
- The index field, which occupies the next three bits following the ss field and specifies the register number of the index register
- The base field, which occupies the three least significant bits of the byte, specifies the register number of the base register

[Figure 17-2](https://nju-projectn.github.io/i386-manual/s17_02.htm#fig17-2) shows the formats of the ModR/M and SIB bytes. The values and the corresponding addressing forms of the ModR/M and SIB bytes are shown in Tables 17-2, 17-3, and 17-4. The 16-bit addressing forms specified by the ModR/M byte are in Table 17-2. The 32-bit addressing forms specified by ModR/M are in Table 17-3. Table 17-4 shows the 32-bit addressing forms specified by the SIB byte

Figure 17-2.  ModR/M and SIB Byte Formats

```
                                 MODR/M BYTE

                     7    6    5    4    3    2    1    0
                    +--------+-------------+-------------+
                    |  MOD   | REG/OPCODE  |     R/M     |
                    +--------+-------------+-------------+

                          SIB (SCALE INDEX BASE) BYTE

                     7    6    5    4    3    2    1    0
                    +--------+-------------+-------------+
                    |   SS   |    INDEX    |    BASE     |
                    +--------+-------------+-------------+
```

>[!cloud]- Table 17-2. 16-Bit Addressing Forms with the ModR/M Byte
>
>```txt
>
>r8(/r)                     AL    CL    DL    BL    AH    CH    DH    BH
>r16(/r)                    AX    CX    DX    BX    SP    BP    SI    DI
>r32(/r)                    EAX   ECX   EDX   EBX   ESP   EBP   ESI   EDI
>/digit (Opcode)            0     1     2     3     4     5     6     7
>REG =                      000   001   010   011   100   101   110   111
>
>   Effective 
>+---Address--+ +Mod R/M+ +--------ModR/M Values in Hexadecimal--------+
>
>[BX + SI]            000   00    08    10    18    20    28    30    38
>[BX + DI]            001   01    09    11    19    21    29    31    39
>[BP + SI]            010   02    0A    12    1A    22    2A    32    3A
>[BP + DI]            011   03    0B    13    1B    23    2B    33    3B
>[SI]             00  100   04    0C    14    1C    24    2C    34    3C
>[DI]                 101   05    0D    15    1D    25    2D    35    3D
>disp16               110   06    0E    16    1E    26    2E    36    3E
>[BX]                 111   07    0F    17    1F    27    2F    37    3F
>
>[BX+SI]+disp8        000   40    48    50    58    60    68    70    78
>[BX+DI]+disp8        001   41    49    51    59    61    69    71    79
>[BP+SI]+disp8        010   42    4A    52    5A    62    6A    72    7A
>[BP+DI]+disp8        011   43    4B    53    5B    63    6B    73    7B
>[SI]+disp8       01  100   44    4C    54    5C    64    6C    74    7C
>[DI]+disp8           101   45    4D    55    5D    65    6D    75    7D
>[BP]+disp8           110   46    4E    56    5E    66    6E    76    7E
>[BX]+disp8           111   47    4F    57    5F    67    6F    77    7F
>
>[BX+SI]+disp16       000   80    88    90    98    A0    A8    B0    B8
>[BX+DI]+disp16       001   81    89    91    99    A1    A9    B1    B9
>[BP+SI]+disp16       010   82    8A    92    9A    A2    AA    B2    BA
>[BP+DI]+disp16       011   83    8B    93    9B    A3    AB    B3    BB
>[SI]+disp16      10  100   84    8C    94    9C    A4    AC    B4    BC
>[DI]+disp16          101   85    8D    95    9D    A5    AD    B5    BD
>[BP]+disp16          110   86    8E    96    9E    A6    AE    B6    BE
>[BX]+disp16          111   87    8F    97    9F    A7    AF    B7    BF
>
>EAX/AX/AL            000   C0    C8    D0    D8    E0    E8    F0    F8
>ECX/CX/CL            001   C1    C9    D1    D9    E1    E9    F1    F9
>EDX/DX/DL            010   C2    CA    D2    DA    E2    EA    F2    FA
>EBX/BX/BL            011   C3    CB    D3    DB    E3    EB    F3    FB
>ESP/SP/AH        11  100   C4    CC    D4    DC    E4    EC    F4    FC
>EBP/BP/CH            101   C5    CD    D5    DD    E5    ED    F5    FD
>ESI/SI/DH            110   C6    CE    D6    DE    E6    EE    F6    FE
>EDI/DI/BH            111   C7    CF    D7    DF    E7    EF    F7    FF
>```


### Notes

_disp8 denotes an 8-bit displacement following the ModR/M byte, to be sign-extended and added to the index. disp16 denotes a 16-bit displacement following the ModR/M byte, to be added to the index. Default segment register is SS for the effective addresses containing a BP index, DS for other effective addresses._

Table 17-3. 32-Bit Addressing Forms with the ModR/M Byte

```txt
r8(/r)                     AL    CL    DL    BL    AH    CH    DH    BH
r16(/r)                    AX    CX    DX    BX    SP    BP    SI    DI
r32(/r)                    EAX   ECX   EDX   EBX   ESP   EBP   ESI   EDI
/digit (Opcode)            0     1     2     3     4     5     6     7
REG =                      000   001   010   011   100   101   110   111

   Effective
+---Address--+ +Mod R/M+ +---------ModR/M Values in Hexadecimal-------+

[EAX]                000   00    08    10    18    20    28    30    38
[ECX]                001   01    09    11    19    21    29    31    39
[EDX]                010   02    0A    12    1A    22    2A    32    3A
[EBX]                011   03    0B    13    1B    23    2B    33    3B
[--] [--]        00  100   04    0C    14    1C    24    2C    34    3C
disp32               101   05    0D    15    1D    25    2D    35    3D
[ESI]                110   06    0E    16    1E    26    2E    36    3E
[EDI]                111   07    0F    17    1F    27    2F    37    3F

disp8[EAX]           000   40    48    50    58    60    68    70    78
disp8[ECX]           001   41    49    51    59    61    69    71    79
disp8[EDX]           010   42    4A    52    5A    62    6A    72    7A
disp8[EBX]           011   43    4B    53    5B    63    6B    73    7B
disp8[--] [--]   01  100   44    4C    54    5C    64    6C    74    7C
disp8[EBP]           101   45    4D    55    5D    65    6D    75    7D
disp8[ESI]           110   46    4E    56    5E    66    6E    76    7E
disp8[EDI]           111   47    4F    57    5F    67    6F    77    7F

disp32[EAX]          000   80    88    90    98    A0    A8    B0    B8
disp32[ECX]          001   81    89    91    99    A1    A9    B1    B9
disp32[EDX]          010   82    8A    92    9A    A2    AA    B2    BA
disp32[EBX]          011   83    8B    93    9B    A3    AB    B3    BB
disp32[--] [--]  10  100   84    8C    94    9C    A4    AC    B4    BC
disp32[EBP]          101   85    8D    95    9D    A5    AD    B5    BD
disp32[ESI]          110   86    8E    96    9E    A6    AE    B6    BE
disp32[EDI]          111   87    8F    97    9F    A7    AF    B7    BF

EAX/AX/AL            000   C0    C8    D0    D8    E0    E8    F0    F8
ECX/CX/CL            001   C1    C9    D1    D9    E1    E9    F1    F9
EDX/DX/DL            010   C2    CA    D2    DA    E2    EA    F2    FA
EBX/BX/BL            011   C3    CB    D3    DB    E3    EB    F3    FB
ESP/SP/AH        11  100   C4    CC    D4    DC    E4    EC    F4    FC
EBP/BP/CH            101   C5    CD    D5    DD    E5    ED    F5    FD
ESI/SI/DH            110   C6    CE    D6    DE    E6    EE    F6    FE
EDI/DI/BH            111   C7    CF    D7    DF    E7    EF    F7    FF
```


### Notes

_\[--\] \[--\] means a SIB follows the ModR/M byte. disp8 denotes an 8-bit displacement following the SIB byte, to be sign-extended and added to the index. disp32 denotes a 32-bit displacement following the ModR/M byte, to be added to the index._


> [!abstract]
> 
> $
> SIB.base + SIB.index * SIB.scale + displacement
> $


Table 17-4. 32-Bit Addressing Forms with the SIB Byte

```txt
   r32                      EAX   ECX   EDX   EBX   ESP   [*]   ESI   EDI
   Base =                   0     1     2     3     4     5     6     7
   Base =                   000   001   010   011   100   101   110   111

+Scaled Index+ +SS Index+ +--------ModR/M Values in Hexadecimal--------+

[EAX]                000    00    01    02    03    04    05    06    07
[ECX]                001    08    09    0A    0B    0C    0D    0E    0F
[EDX]                010    10    11    12    13    14    15    16    17
[EBX]                011    18    19    1A    1B    1C    1D    1E    1F
none             00  100    20    21    22    23    24    25    26    27
[EBP]                101    28    29    2A    2B    2C    2D    2E    2F
[ESI]                110    30    31    32    33    34    35    36    37
[EDI]                111    38    39    3A    3B    3C    3D    3E    3F

[EAX*2]              000    40    41    42    43    44    45    46    47
[ECX*2]              001    48    49    4A    4B    4C    4D    4E    4F
[EDX*2]              010    50    51    52    53    54    55    56    57
[EBX*2]              011    58    59    5A    5B    5C    5D    5E    5F
none             01  100    60    61    62    63    64    65    66    67
[EBP*2]              101    68    69    6A    6B    6C    6D    6E    6F
[ESI*2]              110    70    71    72    73    74    75    76    77
[EDI*2]              111    78    79    7A    7B    7C    7D    7E    7F

[EAX*4]              000    80    81    82    83    84    85    86    87
[ECX*4]              001    88    89    8A    8B    8C    8D    8E    8F
[EDX*4]              010    90    91    92    93    94    95    96    97
[EBX*4]              011    98    99    9A    9B    9C    9D    9E    9F
none             10  100    A0    A1    A2    A3    A4    A5    A6    A7
[EBP*4]              101    A8    A9    AA    AB    AC    AD    AE    AF
[ESI*4]              110    B0    B1    B2    B3    B4    B5    B6    B7
[EDI*4]              111    B8    B9    BA    BB    BC    BD    BE    BF

[EAX*8]              000    C0    C1    C2    C3    C4    C5    C6    C7
[ECX*8]              001    C8    C9    CA    CB    CC    CD    CE    CF
[EDX*8]              010    D0    D1    D2    D3    D4    D5    D6    D7
[EBX*8]              011    D8    D9    DA    DB    DC    DD    DE    DF
none             11  100    E0    E1    E2    E3    E4    E5    E6    E7
[EBP*8]              101    E8    E9    EA    EB    EC    ED    EE    EF
[ESI*8]              110    F0    F1    F2    F3    F4    F5    F6    F7
[EDI*8]              111    F8    F9    FA    FB    FC    FD    FE    FF
```

### Notes

_\[\*\] means a disp32 with no base if MOD is 00. Otherwise, [*] means disp8[EBP] or disp32[EBP]. This provides the following addressing modes:_

      disp32[index]        (MOD=00)
      disp8[EBP][index]    (MOD=01)
      disp32[EBP][index]   (MOD=10)

## 2 How to Read the Instruction Set Pages

The following is an example of the format used for each 80386 instruction description in this chapter:

### CMC -- Complement Carry Flag


```txt
Opcode   Instruction         Clocks      Description

F5        CMC                  2            Complement carry flag
```

The above table is followed by paragraphs labelled "Operation," "Description," "Flags Affected," "Protected Mode Exceptions," "Real Address Mode Exceptions," and, optionally, "Notes." The following sections explain the notational conventions and abbreviations used in these paragraphs of the instruction descriptions.

### 2.1 Opcode

The "Opcode" column gives the complete object code produced for each form of the instruction. When possible, the codes are given as hexadecimal bytes, in the same order in which they appear in memory. Definitions of entries other than hexadecimal bytes are as follows:

- **/digit**:
	- (digit is between 0 and 7) indicates that the ModR/M byte of the instruction uses only the r/m (register or memory) operand. The reg field contains the digit that provides an extension to the instruction's opcode.
	- （数字介于 0 和 7 之间）表示指令的 ModR/M 字节仅使用 r/m（寄存器或内存）操作数。reg 字段包含提供指令操作码扩展的数字。
	- ![Ttng2E|600](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Ttng2E.png)
- **/r**:
	- indicates that the ModR/M byte of the instruction contains both a register operand and an r/m operand.（表示指令的 ModR/M 字节同时包含寄存器操作数和 r/m 操作数。）
	- 寄存器操作数由 reg/opcode 指示，r/m 操作数由 MOD 和 R/M 指示。
- **cb, cw, cd, cp**:
	- a 1-byte (cb), 2-byte (cw), 4-byte (cd) or 6-byte (cp) value following the opcode that is used to specify a code offset and possibly a new value for the code segment register.
- **ib, iw, id**:
	- a 1-byte (ib), 2-byte (iw), or 4-byte (id) immediate operand to the instruction that follows the opcode, ModR/M bytes or scale-indexing bytes. The opcode determines if the operand is a signed value. All words and doublewords are given with the low-order byte first.（一个1字节（ib），2字节（iw）或4字节（id）的立即操作数，用于跟随操作码、ModR/M 字节或比例索引字节的指令。操作码确定操作数是否为有符号值。所有单词和双字都以低位字节优先顺序给出。）
- **+rb, +rw, +rd**:
	- a register code, from 0 through 7, added to the hexadecimal byte given at the left of the plus sign to form a single opcode byte. The codes are
	```txt
      rb         rw         rd
    AL = 0     AX = 0     EAX = 0
    CL = 1     CX = 1     ECX = 1
    DL = 2     DX = 2     EDX = 2
    BL = 3     BX = 3     EBX = 3
    AH = 4     SP = 4     ESP = 4
    CH = 5     BP = 5     EBP = 5
    DH = 6     SI = 6     ESI = 6
    BH = 7     DI = 7     EDI = 7
	```
	- 直接由 opcode 的低三位给出。