# BitXor
```c
/* 
 * bitXor - x^y using only ~ and & 
 *   Example: bitXor(4, 5) = 1
 *   Legal ops: ~ &
 *   Max ops: 14
 *   Rating: 1
 */
int bitXor(int x, int y) {
    return (~x & y) | (x & ~y); // why here can use "|"
}
```

- [ ] 数字逻辑电路真值表化简与迪摩根定律的使用 #todo 🔼 🛫 2022-12-27