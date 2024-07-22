```pseudo
\begin{algorithm}
\caption{Quicksort}
\begin{algorithmic}
	\Procedure{Quicksort}{$A, p, r$}
		\If{$p < r$}
			\State $q \gets $ \Call{Partition}{$A, p, r$}
			\State \Call{Quicksort}{$A, p, q - 1$}
			\State \Call{Quicksort}{$A, q + 1, r$}
		\EndIf
	\EndProcedure
	\Procedure{Partition}{$A, p, r$}
		\State $x \gets A[r]$
		\State $i \gets p - 1$
		\For{$j \gets p$ \To $r - 1$}
			\If{$A[j] < x$}
				\State $i \gets i + 1$
				\State exchange
				$A[i]$ with $A[j]$
			\EndIf
		\State exchange $A[i]$ with $A[r]$
		\EndFor
	\EndProcedure
	\end{algorithmic}
\end{algorithm}
```
![未命名绘图.svg](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/%E6%9C%AA%E5%91%BD%E5%90%8D%E7%BB%98%E5%9B%BE.svg)

$$
A(n)=\underbrace{n-1}_{ {\small PARTITION} 的代价} + \underbrace{\sum_{i=0}^{n-1} \frac{1}{n}\left[ A(i) + A(n-1-i) \right]}_{递归排序左、右部分的代价}, n \ge2
$$



$$
\frac{2}{n} \sum_{i=1}^{n-1} c i \ln i \leq \frac{2 c}{n} \int_1^n x \ln x d x \approx \frac{2 c}{n}\left(\frac{n^2 \ln n}{2}-\frac{n^2}{4}\right)=c n \ln n-\frac{c n}{2}
$$