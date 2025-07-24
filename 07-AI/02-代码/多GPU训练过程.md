---
created: 2025-04-27 01:27
tags:
---
![[Pasted image 20250427012806.png]]

好的，我们来分析一下这张图。

这张图（图12.3.1）展示了**在一个CPU和两个GPU上训练一个两层多层感知机（MLP）的计算图及其依赖关系**。它描绘了一种典型的**数据并行**（Data Parallelism）训练模式。

以下是详细分析：

1.  **硬件配置**:
    * 中间是一个CPU（标有Intel标志）。
    * 左右两边各有一个GPU。

2.  **模型**:
    * 这是一个两层的多层感知机，包含两个全连接层（图中用 `fc1` 和 `fc2` 表示）。

3.  **训练流程 (数据并行)**:
    * **数据准备 (CPU)**: `data = next_batch()` - CPU负责获取下一个训练数据批次。
    * **数据分发 (CPU -> GPUs)**:
        * `data[gpu0].copyfrom(data[0:50])` - 数据批次的前半部分（样本0到50）被复制到GPU 0。
        * `data[gpu1].copyfrom(data[51:100])` - 数据批次的后半部分（样本51到100）被复制到GPU 1。
        * 同样地，对应的标签（`label`）也被分发到各自的GPU。
    * **前向传播 (GPUs)**:
        * 每个GPU独立地对其分配到的数据子集执行完整的前向传播计算 (`FullForward`)，通过两个全连接层 (`fc1`, `fc2`)。
        * `fc1[gpu0] = FullForward(data[gpu0], fc1_weight[gpu0])`
        * `fc2[gpu0] = FullForward(fc1[gpu0], fc2_weight[gpu0])`
        * GPU 1 执行类似操作。
    * **损失计算和梯度计算 (GPUs)**:
        * 每个GPU根据其前向传播的输出和对应的标签计算损失，并开始反向传播，计算输出层的梯度 (`LossGrad`)。
        * `fc2_ograd[gpu0] = LossGrad(fc2[gpu0], label[0:50])`
        * GPU 1 执行类似操作。
    * **反向传播 (GPUs)**:
        * 每个GPU独立地完成剩余的反向传播过程 (`FullBackward`)，计算各层权重 (`fc1_wgrad`, `fc2_wgrad`) 和激活值的梯度。
        * `fc1_ograd[gpu0], fc2_wgrad[gpu0] = FullBackward(fc2_ograd[gpu0], fc2_weight[gpu0])`
        * `_, fc1_wgrad[gpu0] = FullBackward(fc1_ograd[gpu0], fc1_weight[gpu0])`
        * GPU 1 执行类似操作。
    * **梯度聚合 (GPUs -> CPU)**:
        * 两个GPU上计算出的同一层权重的梯度被发送回CPU。
        * CPU将来自两个GPU的梯度相加，得到整个批次数据的总梯度。
        * `fc2_wgrad[cpu] = fc2_wgrad[gpu0] + fc2_wgrad[gpu1]`
        * `fc1_wgrad[cpu] = fc1_wgrad[gpu0] + fc1_wgrad[gpu1]`
    * **权重更新 (CPU)**:
        * CPU使用聚合后的总梯度和学习率 (`lr`) 来更新模型的权重 (`fc1_weight`, `fc2_weight`)。
        * `fc2_weight[cpu] -= lr * fc2_wgrad[cpu]` (图中 `fc12_wgrad[gpu0]` 可能有误，逻辑上应使用聚合后的 `fc2_wgrad[cpu]`)
        * `fc1_weight[cpu] -= lr * fc1_wgrad[cpu]`
    * **权重分发 (CPU -> GPUs)**:
        * CPU将更新后的权重 (`fc1_weight[cpu]`, `fc2_weight[cpu]`) 复制回两个GPU，以便用于下一个训练迭代。
        * `fc2_weight[cpu].copyto(fc2_weight[gpu0], fc2_weight[gpu1])`
        * `fc1_weight[cpu].copyto(fc1_weight[gpu0], fc1_weight[gpu1])`

4.  **总结**:
    * 该图展示了利用多个GPU加速神经网络训练的一种常见方法——数据并行。
    * **GPU** 负责主要的计算密集型任务（前向和反向传播）。
    * **CPU** 负责数据加载、任务协调、梯度聚合和参数更新。
    * 这种模式的效率依赖于计算和通信的平衡。GPU之间的计算是并行的，但数据的分发、梯度的聚合以及权重的分发都需要CPU与GPU之间的通信，这可能成为性能瓶颈。

总的来说，这张图清晰地描绘了在CPU-GPU混合系统上进行分布式（数据并行）模型训练的计算流程和数据流向。
