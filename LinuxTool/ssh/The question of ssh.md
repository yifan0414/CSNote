### 1 同一个局域网下 ping 延迟过高
![Uh0MG1](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Uh0MG1.png)

看这个帖子 https://superuser.com/questions/1713147/high-variable-ping-times-to-machine-on-local-network

![ZJHqpU](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/ZJHqpU.png)


首先在 Ubuntu 上使用 `iw dev` 查看设备名

![b8ttND](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/b8ttND.png)

然后使用 `sudo iw wlp2s0 set power_save off`