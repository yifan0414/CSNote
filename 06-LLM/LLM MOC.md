---
title: LLM MOC
aliases:
  - 06-LLM 学习地图
  - LLM 学习入口
tags:
  - moc
  - llm
  - transformer
type: moc
created: 2026-09-09
updated: 2026-09-09
---

# LLM MOC

这个页面是 `06-LLM` 的学习入口。目录按**主题**划分，编号 `90-`/`91-` 存放课程与问答类材料；多模态内容统一放在 `07-MultiModal`。

## 目录结构

| 目录 | 内容 |
| --- | --- |
| `00-MOC` | 本页、AI 发展史图、流派随笔 |
| `01-数学基础` | 概率、损失函数、优化器、矩阵求导 |
| `02-机器学习基础` | 神经网络、梯度下降、CNN、学习率 |
| `03-Transformer` | 分词 → 词向量 → RNN → Seq2Seq → Attention → Transformer |
| `04-训练与推理` | 训练工程与推理相关代码笔记 |
| `90-课程` | CS224n / CS229 / 李宏毅课程笔记 |
| `91-问题` | 零散问答型笔记 |

## 主线：从分词到 Transformer

- [[00-分词|00 分词]]
- [[01-词向量|01 词向量]]
- [[02-RNN|02 RNN]]
- [[03-LSTM与GRU|03 LSTM 与 GRU]]
- [[04-Seq2Seq|04 Seq2Seq]]
- [[05-Attention|05 Attention]]
- [[06-transformer|06 Transformer]]
- [[从 Seq2Seq 到 Attention 再到 Transformer|演变史：从 Seq2Seq 到 Transformer]]
- [[dive-to-attention|dive-to-attention 对话记录]]

> [!note] 同一主题的多个版本
> Transformer 相关内容目前分散在四处，各自定位不同，暂未合并：
> - [[06-transformer]]：主讲义，`status: active`，shape 推导与例题最完整。
> - [[01-transformer]]：`07-MultiModal/Video-MLLM` 的路线图配套笔记，`status: planned`。
> - [[07-Transformer]]：CS224n 第 7 讲课程笔记。
> - [[从 Seq2Seq 到 Attention 再到 Transformer]]：以「信息访问方式」为主线的演变史。

## 数学基础

- [[从概率建模统一理解机器学习损失 MLE、NLL、Cross-Entropy、KL、MSE 与 MAE|从概率建模统一理解损失函数]]
- [[交叉熵系统整理]]
- [[最大似然MLE]]
- [[KL 散度]]
- [[Foward KL 和 Reverse KL]]
- [[均方误差损失函数]]
- [[均方误差解析解]]
- [[Adam优化器系统整理]]
- [[贝叶斯公式]]
- [[二阶范数的梯度]]
- [[线性函数与多层感知机的数学前提]]
- [[行列式]]
- [[雅克比矩阵]]
- [[矩阵求导]]
- [[矩阵求导术]]
- [[反向传播]]

## 机器学习基础

- [[神经网络所解决的问题]]
- [[学习率]]
- [[高斯朴素贝叶斯分类器]]
- [[梯度]]
- [[梯度下降权重更新公式]]
- [[随机梯度下降]]
- [[梯度归一化 .sum().backward()|梯度归一化（.sum().backward()）]]
- [[CNN中的滤波器]]
- [[CNN中需要学习的内容]]

## 训练与推理

- [[负对数似然]]
- [[多GPU训练过程]]
- [[权重共享]]

## 课程笔记

- [[00-CS224n-2026-课程总览|CS224n 2026 课程总览]]（23 讲，见 `90-课程/CS224n`）
- [[CS 229 - Supervised Learning Cheatsheet 1|CS229 Supervised Learning Cheatsheet]]
- [[Where does the error come from?|李宏毅 00 Model]]
- [[Adagrad|李宏毅 02 Gradient Descent]]
- [[CNN|李宏毅 06 CNN]]
- [[Why CNN works]]
- [[反向识别滤波器提取的特征]]

## 问题

- [[⭐线性回归是如何进化为神经网络的]]
- [[线性回归是如何计算w和b的]]
- [[为什么sigmoid函数容易梯度消失]]
- [[为什么首先使用的不是relu，而是sigmoid]]
- [[为什么小权重比大权重更好]]
- [[损失函数和优化器的选择]]

## 其他

- [[频率派和贝叶斯派]]
- [[人工智能发展史]]
- [[RoadMap|Video MLLM 学习路线]]（`07-MultiModal/Video-MLLM`）
- [[MLLM|多模态推理总览]]（`07-MultiModal`）
