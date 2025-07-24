---
title: "(93 封私信 / 2 条消息) 深度学习把两篇论文的方法拼接在一起，效果实现了新的sota，可以发论文吗？ - 知乎"
source: "https://www.zhihu.com/question/637834653/answer/3580194041"
author:
created: 2025-03-25
description: "当然可以。是时候拿出我收藏很久的学术表情包了：Source: u/TheInsaneApp传统深度学习时代，常见的论文开…"
tags:
  - "clippings"
---
[模型](https://www.zhihu.com/topic/19579715) [计算机视觉](https://www.zhihu.com/topic/19590195) [深度学习（Deep Learning）](https://www.zhihu.com/topic/19813032) [大模型](https://www.zhihu.com/topic/25402720) [大语言模型](https://www.zhihu.com/topic/27267395)

## 深度学习把两篇论文的方法拼接在一起，效果实现了新的sota，可以发论文吗？

我看了两篇文章，想把他们拼接在一起，发现效果出奇的好，提上了5%，不知道该怎么写论文描述呢。 [查看全部 46 个回答](https://www.zhihu.com/question/637834653)

当然可以。是时候拿出我收藏很久的学术表情包了：

Source: u/TheInsaneApp

传统深度学习时代，常见的论文开题方式有——

- **微改网络结构 + 旧数据集** = 《我发明了新的网络结构》
- **旧网络结构 + 新数据集** = 《我开源了新的数据造福人类》
- **跑了一堆微改的网络结构，找到那个0.3%领先的** = 《我大大改进了现有网络结构》
- **旧网络结构 + 旧数据集 + 新的应用领域** = 《我开辟了深度学习在X领域的应用》
- **旧网络结构 + 旧数据集 + 新的评估方法** = 《我认为这样评估模型更合理》

题主的方法，是很常见的第一条模式，微改网络结构。

以上方法有一些变种，比如我 WACV 2024 论文《 Fast and Interpretable Face Identification for Out-Of-Distribution Data Using Vision Transformers 》，属于 **微改网络结构** （ [视觉transformer](https://zhida.zhihu.com/search?content_id=681013960&content_type=Answer&match_order=1&q=%E8%A7%86%E8%A7%89transformer&zhida_source=entity) ） + **旧数据集** + **新的应用领域** （人脸识别当中比较少见的像戴口罩这样的例子）。

这两年，进入大模型时代以后，又增加了一些新姿势——

- **旧的应用领域 + 新出的大模型** = 《站在巨人的肩膀上》
- **旧的网络结构 + 旧数据集 + 加大算力** = 《大力出奇迹》

比如我 CVPR Workshop 蕞佳论文《 Segment Anything Model for Road Network Graph Extraction 》，属于 **旧的应用领域** （道路分割问题） + **新出的大模型** （分割大模型SAM）。

写了一大堆同一领域的论文以后，还可以写综述（survey），整理该领域所有论文并提出见解。好了好了，本水怪先溜了。。。

有编程基础、在工业界工作的朋友，对发论文感兴趣的话欢迎找我～多交流！

---

相关回答：

重要问题可走咨询：

![](https://picx.zhimg.com/v2-fb13cef54ed3abe7642c17d7a96209f1_l.jpg?source=f2fdee93) 甜菜欣欣 1 次咨询 5.0 10897 次赞同去咨询 [编辑于 2024-08-29 01:07](https://www.zhihu.com/question/637834653/answer/3580194041) ・IP 属地美国

#### 更多回答

谢邀 [@Intelsp](https://www.zhihu.com/people/intelsp)

不是大佬，舔着脸回答一波哈。

先说结论，能啊，肯定能，大大滴能。

你看何恺明大神的Resnet，它提出的identity mapping和short connection在此前也被不少人使用过，但能排列组合使用得好，不妨碍resnet成为经典之作，这就是大道至简呐。

两篇论文拼接在一起实现新sota已经很好了，多少人水论文都是搭积木+调参数勉强提个1个百分点，顶着算法工程师的头衔，拿着顶配的算力资源，实质干着大专生都能干的活……连一些顶会的论文都是疯狂调参数。

这是现实，但也实属正常，新人要练手，社畜要恰饭，研究所有论文指标的嘛，各有所需。

沐神也说，即便是顶会，真正有用的工作也不足10%，剩下90%其实就是培养新人用的。所以不要觉得自己的论文没含金量而气馁，都有这么一个过程。

写论文最重要的是要讲好一个故事……虽然这么说不大好听，但现在想投一个好期刊，好好包装反而成为了重中之重。

题主现在该考虑的是如何包装你的这个idea，使得它看起来很有创新性即可。何况你有5个百分点的提升，感觉这就已经赢了太多人了。

题主可以搜搜论文写作相关的词条，不少大佬专门分享如何写一个精彩纷呈的论文故事。

期待题主的好消息呀！

Transformer中所有组件你都可以在别的论文中找到，但不妨碍它变为Attention is All You Need～

[查看全部 46 个回答](https://www.zhihu.com/question/637834653)