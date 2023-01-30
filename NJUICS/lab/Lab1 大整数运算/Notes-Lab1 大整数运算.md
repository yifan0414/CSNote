# Reference

https://www.quora.com/How-can-I-execute-A-*-B-mod-C-without-overflow-if-A-and-B-are-lesser-than-C

https://www.luogu.com.cn/problem/U203580


https://en.wikipedia.org/wiki/Modular_arithmetic#Example_implementations

https://www.quora.com/How-can-I-execute-A-*-B-mod-C-without-overflow-if-A-and-B-are-lesser-than-C/answer/Dana-Jacobsen

https://oi-wiki.org/math/bignum/#%E9%AB%98%E7%B2%BE%E5%BA%A6%E9%AB%98%E7%B2%BE%E5%BA%A6

# Note

两种方法：
1. 高精度乘法和高精度除法（低精度除法的话只能保证 63 bit）
2. 快速幂，然后加法？

![[Notes-Lab1 大整数运算.png]]

注意这里最多为 $10^{18}$，这个数是比 $2^{64} - 1$ 小的。

#todo 这个问题有点难，虽然在网上找到了几乎完美的解决方案，但是还没有理解其中的 trick。

即使如此，通过思考这个 Lab 加深了对 makefile 和构造测试用例的理解