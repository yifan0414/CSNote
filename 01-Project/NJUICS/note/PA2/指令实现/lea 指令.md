# Reference

https://nju-projectn.github.io/i386-manual/LEA.htm

# 

# LEA -- Load Effective Address

```
Opcode  Instruction  Clocks  Description

8D  /r  LEA r16,m    2       Store effective address for m in register r16
8D  /r  LEA r32,m    2       Store effective address for m in register r32
8D  /r  LEA r16,m    2       Store effective address for m in register r16
8D  /r  LEA r32,m    2       Store effective address for m in register r32
```

## Operation

```
IF OperandSize = 16 AND AddressSize = 16
THEN r16 := Addr(m);
ELSE
   IF OperandSize = 16 AND AddressSize = 32
   THEN
      r16 := Truncate_to_16bits(Addr(m));   (* 32-bit address *)
   ELSE
      IF OperandSize = 32 AND AddressSize = 16
      THEN
         r32 := Truncate_to_16bits(Addr(m));
      ELSE
         IF OperandSize = 32 AND AddressSize = 32
         THEN  r32 := Addr(m);
         FI;
      FI;
   FI;
FI;
```

## Description

LEA calculates the effective address (offset part) and stores it in the specified register. The operand-size attribute of the instruction (represented by OperandSize in the algorithm under "Operation" above) is determined by the chosen register. The address-size attribute (represented by AddressSize) is determined by the USE attribute of the segment containing the second operand. The address-size and operand-size attributes affect the action performed by LEA, as follows:



```
Operand Size  Address Size  Action Performed

    16            16        16-bit effective address is calculated and
                            stored in requested 16-bit register
                            destination.

    16            32        32-bit effective address is calculated. The
                            *lower* 16 bits of the address are stored in
                            the requested 16-bit register destination.

    32            16        16-bit effective address is calculated. The
                            16-bit address is *zero-extended* and stored
                            in the requested 32-bit register destination.

    32            32        32-bit effective address is calculated and
                            stored in the requested 32-bit register
                            destination.
```