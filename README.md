这是本人的学习笔记，如想获得最佳浏览效果，请下载 Obsidian 和本仓库文件，然后在 Obsidian 中打开该仓库。

This is my study notes. For the best viewing experience, please download Obsidian and the files from this repository, then open the repository in Obsidian.

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

![](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/no-god-oh-my-god.gif)


![[girshick2015fast#^837h4lni]]

![[he2016deep#^h9rsjh]]