---
创建时间: 2025-07-30 11:58
tags: 
---
虽然 CNN 自动从数据中学习特征，但整个模型还是离不开人来“打地基”——也就是**架构设计**和**训练配置**上的一系列超参数选择。下面归纳几个关键的、需要人为设计的部分，以及它们对模型的影响：

---

## 1. 网络架构（Network Architecture）

* **层数与宽度（Depth & Width）**

  * 决定模型的表达能力与容量。层越深／每层通道数越多，能学习更复杂的特征，但也更容易过拟合、训练困难、计算代价高。
* **卷积核大小（Kernel Size）**

  * 影响感受野（receptive field）大小。小核（如 3×3）更灵活、参数少；大核（如 7×7）一次能看更大区域，但参数更多。
* **步幅与填充（Stride & Padding）**

  * 决定特征图尺寸缩放速度。大步幅／无填充会快速下采样，减小空间分辨率；填充则保持尺寸，便于深度堆叠。
* **池化方式（Pooling Type）**

  * 常见有 MaxPool、AvgPool。MaxPool 更强调显著特征，AvgPool 更平滑，把握整体趋势；也可用全局池化直接生成分类特征。
* **跳跃连接／残差结构（Skip Connections）**

  * 例如 ResNet 中的残差块，帮助缓解梯度消失，加速训练深层网络。是否使用、如何设计，都需要人为决策。

---

## 2. 激活函数（Activation Function）

* 常用 ReLU、Leaky‑ReLU、ELU、GELU 等
* 影响非线性建模能力、梯度传播稳定性和训练速度
* 不同功能更适合不同网络（例如 Transformer 中常用 GELU 而非 ReLU）

---

## 3. 目标函数与损失（Loss Function）

* **分类**：交叉熵（Cross‑Entropy）
* **回归**：均方误差（MSE）、Smooth‑L1 等
* **特殊任务**：比如目标检测常用的 Focal Loss、IoU Loss，不同损失会偏向不同优化目标（召回 vs 精度）

---

## 4. 优化器与学习率策略（Optimizer & LR Schedule）

* **优化器**：SGD（动量）、Adam、RMSProp、AdamW…

  * Adam 收敛快但有时泛化略差，SGD 泛化好但需要更精心调 LR。
* **学习率调度**：固定、Step Decay、Cosine Annealing、Warm‑up 等

  * 直接决定模型的收敛速度与最终性能，策略选不好容易卡在局部最优或震荡不收敛。

---

## 5. 正则化与归一化（Regularization & Normalization）

* **归一化层**：BatchNorm、LayerNorm、GroupNorm…

  * 稳定训练、加速收敛；不同场景（小 batch、大模型）下选型不同。
* **正则化手段**：Dropout、权重衰减（Weight Decay）、数据增强（Data Augmentation）

  * 提升模型泛化能力，防止过拟合；Augmentation 的策略（旋转、裁剪、色彩抖动等）也需人为设计。

---

## 6. 输入预处理与数据增强（Preprocessing & Augmentation）

* **归一化**：减均值、除方差，保证不同通道分布一致
* **增强策略**：随机翻转、旋转、色彩变换、Mixup、CutMix…

  * 决定模型在各种畸变下的鲁棒性，好的增强能显著提高性能。

---

## 7. 批量大小与训练轮数（Batch Size & Epochs）

* **Batch Size**

  * 大 Batch 加速硬件利用但需要更高 LR 调整，小 Batch 泛化通常更好。
* **Epochs**

  * 训练轮数过少模型欠拟合，过多容易过拟合。需配合早停（Early Stopping）等策略。

---

### 总结

尽管特征“自动”从数据中学习，CNN 的整体表现却高度依赖于上述**人为设计**的架构和超参数选择。每一项决策都在影响：

* **表达能力**（能学多复杂的特征）
* **计算效率**（训练／推理速度、显存占用）
* **收敛行为**（快慢、稳不稳）
* **泛化性能**（是否容易过拟合／稳健性）

通过经验、网格搜索（Grid Search）、贝叶斯优化（Bayesian Optimization）等手段调整这些设计，才能在实际任务中得到最优的 CNN 模型。

