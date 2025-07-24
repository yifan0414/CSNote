---
created: 2025-05-09 20:15
tags:
---
> [!quote] 
[Visualizing and Understanding Convolutional Networks](zotero://select/library/items/B4SH66A4)


# Objective
用比较少的参数做影像处理

# Why CNN for Image

## 1 只需要关注一个小区域，而不需要观察整张图
![[Pasted image 20250509202621.png]]
## 2 Parameter Sharing

![[Pasted image 20250509202732.png]]
在一个卷积层中，用于检测特定特征的卷积核（滤波器）会在整个输入图像上滑动（或称为卷积）。这意味着，无论这个特征出现在图像的哪个位置（例如，一个竖直边缘可能出现在图像的左边、右边或中间），都会使用**相同的参数（同一个卷积核）** 去检测它。

**效果**：

- **大幅减少参数数量**：相比于MLP中每个连接都有独立的权重，CNN通过共享参数极大地减少了模型的参数总量。例如，一个用于检测竖直边缘的3x3卷积核，在整个图像上共享这9个参数，而不是为图像的每个3x3区域都学习一套新的参数。
- **平移不变性 (Translation Invariance)**：由于同一个特征检测器（卷积核）在整个图像上共享，模型能够识别出在图像不同位置出现的相同特征。这就是为什么CNN对物体的位置变化不那么敏感。


## 3 架构设计
![[Pasted image 20250509203057.png]]

## 与神经网络的联系
![[Pasted image 20250509210509.png]]

