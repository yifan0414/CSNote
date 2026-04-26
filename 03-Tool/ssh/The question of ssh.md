### 1 同一个局域网下 ping 延迟过高
![[attachments/138bb3e0ae1ed58d48f2e8307bcf3b54_MD5.png]]

看这个帖子 https://superuser.com/questions/1713147/high-variable-ping-times-to-machine-on-local-network

![[attachments/6f72e032aa39a3e0bf7989b1a2aa085e_MD5.png]]



首先在 Ubuntu 上使用 `iw dev` 查看设备名

![[attachments/963df15e2a4413f928f22b6b7ffeb6c8_MD5.png]]

然后使用 `sudo iw wlp2s0 set power_save off`
