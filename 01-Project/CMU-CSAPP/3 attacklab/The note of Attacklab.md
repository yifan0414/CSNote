> 注意看这个实验的名字

![vLwlKc](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/vLwlKc.png)

所以，这个实验的所有部分都是围绕 **Buffer Overflow** 进行的。

攻击分为两种，一种是 Code Inject Attack（CI），另一种是 Return-Oriented Programming（ROP）。

>[!note] 执行目标位置的代码，使用 ret 指令


- Code Inject Attack (CI)
	- 看名知意，就是让我们通过构造汇编指令，然后转换为字符串传递给程序，从而让程序在执行栈上的指令。

- Return-Oriented Programming (ROP)
	- 面对栈地址不固定和无法在栈上执行指令的机器，我们通常使用这种方法。
	- 我们可以通过 $rsp 获取当前栈地址