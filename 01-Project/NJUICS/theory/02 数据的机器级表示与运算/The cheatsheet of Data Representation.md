
### 1. The data range of C language

##### Figure 1: Typical sizes (in bytes) of basic C data types.

$$
\begin{array}{|llcc|}
\hline {\text { C declaration }}& & {\text { Bytes }} \\
\hline \text { Signed } & \text { Unsigned } & \text { 32-bit } & \text { 64-bit } \\
\hline \text { [signed] char } & \text { unsigned char } & 1 & 1 \\
\text { short } & \text { unsigned short } & 2 & 2 \\
\text { int } & \text { unsigned } & 4 & 4 \\
\text { long } & \text { unsigned long } & 4 & 8 \\
\text { int32\_t } & \text { uint32\_t } & 4 & 4 \\
\text { int64\_t } & \text { uint64\_t } & 8 & 8 \\
\text { char } * & & 4 & 8 \\
\text { float } & & 4 & 4 \\
\text { double } & & 8 & 8 \\
\hline
\end{array}
$$




##### Figure 2: Typical ranges for C integral data types for 32-bit programs.


$$
\begin{array}{lrr}
\hline \text { C data type } & \text { Minimum } & \text { Maximum } \\
\hline \text { [signed] char } & -2^7 & 2^7-1 \\
\text { unsigned char } & 0 & 2^8-1 \\[5pt]
\text { short } & -2^{15} & 2^{15}-1 \\
\text { unsigned short } & 0 & 2^{16} -1 \\[5pt]
\text { int } & -2^{31} & 2^{31}-1 \\
\text { unsigned } & 0 & 2^{32}-1 \\[5pt]
\text { long } & -2^{31} & 2^{31}-1 \\
\text { unsigned long } & 0 & 2^{32}-1 \\[5pt]
\text { int32\_t } & -2^{31} & 2^{31}-1 \\
\text { uint32\_t } & 0 & 2^{32}-1 \\[5pt]
\text { int64\_t } & -2^{63} & 2^{63}-1 \\
\text { uint64\_t } & 0 & 2^{64}-1 \\
\hline
\end{array}
$$


##### Figure 3: Typical ranges for C integral data types for 64-bit programs.

$$
\begin{array}{lrr}
\hline \text { C data type } & \text { Minimum } & \text { Maximum } \\
\hline \text { [signed] char } & -2^7 & 2^7-1 \\
\text { unsigned char } & 0 & 2^8-1 \\[5pt]
\text { short } & -2^{15} & 2^{15}-1 \\
\text { unsigned short } & 0 & 2^{16} -1 \\[5pt]
\text { int } & -2^{31} & 2^{31}-1 \\
\text { unsigned } & 0 & 2^{32}-1 \\[5pt]
\text { long } & -2^{63} & 2^{63}-1 \\
\text { unsigned long } & 0 & 2^{64}-1 \\[5pt]
\text { int32\_t } & -2^{31} & 2^{31}-1 \\
\text { uint32\_t } & 0 & 2^{32}-1 \\[5pt]
\text { int64\_t } & -2^{63} & 2^{63}-1 \\
\text { uint64\_t } & 0 & 2^{64}-1 \\
\hline
\end{array}
$$

##### Figure 4: C90 标准下长整数类型
$$
\begin{array}{|c|c|}
\hline \text { 范围 } & \text { 类型 } \\
\hline 0 \sim 2^{31}-1 & \text { int } \\
\hline 2^{31} \sim 2^{32}-1 & \text { unsigned int } \\
\hline 2^{32} \sim 2^{63}-1 & \text { long long } \\
\hline 2^{63} \sim 2^{64}-1 & \text { unsigned long long } \\
\hline
\end{array}
$$

^325888

##### Figure 5: C99 标准下长整数类型
$$
\begin{array}{|c|c|}
\hline \text { 范围 } & \text { 类型 } \\
\hline 0 \sim 2^{31}-1 & \text { int } \\
\hline 2^{31} \sim 2^{63}-1 & \text { long long } \\
\hline 2^{63} \sim 2^{64}-1 & \text { unsigned long long } \\
\hline
\end{array}
$$


##### Figure 6: Effects of C promotion rules
$$
\begin{array}{|rrrlc|}
\hline {\text { Expression }} & & & \text { Type } & \text { Evaluation } \\
\hline 0 & == & \text { 0U } & \text { Unsigned } & 1 \\
-1 & < & 0 & \text { Signed } & 1 \\
-1 & < & \text { 0U } & \text { Unsigned } & 0^* \\
2147483647 & > & -2147483647-1 & \text { Signed } & 1 \\
2147483647 \mathrm{U} & > & -2147483647-1 & \text { Unsigned } & 0^* \\
2147483647 & > & \text { (int) } 2147483648 \mathrm{U} & \text { Signed } & 1^* \\
-1 & > & -2 & \text { Signed } & 1 \\
\text { (unsigned) }-1 & > & -2 & \text { Unsigned } & 1 \\
\hline
\end{array}
$$
