---
citekey: he2016deep
authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
title: "Deep residual learning for image recognition"
alias: 
Year: 2016
tags: [literature-note, ]
Authors: Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
publisher: ""
doi: https://doi.org/10.48550/arXiv.1512.03385
---
# Deep residual learning for image recognition

> [!info]+ Info - [**Zotero**](zotero://select/library/items/IX39V35N) | [**DOI**](https://doi.org/https://doi.org/10.48550/arXiv.1512.03385)  | Local [**PDF**](file:////Users/yifansu/Zotero/storage/ZIVWRUPE/He%20等%20-%202016%20-%20Deep%20residual%20learning%20for%20image%20recognition.pdf)
> Authors: [[Kaiming He]], [[Xiangyu Zhang]], [[Shaoqing Ren]], [[Jian Sun]],  
> Type: conferencePaper
> Year: 2016
> Zotero links: [Item](zotero://select/library/items/IX39V35N) PDF: [Deep residual learning for image recognition.pdf](zotero://select/library/items/ZIVWRUPE) 
> Web links: [Item](http://zotero.org/users/9245962/items/IX39V35N) PDF: [Deep residual learning for image recognition.pdf](file:///Users/yifansu/Zotero/storage/ZIVWRUPE/He%20等%20-%202016%20-%20Deep%20residual%20learning%20for%20image%20recognition.pdf) 
> 
>
> **History**
> Date item added to Zotero: [[2023-06-06]]
> First date annotations or notes modified: [[2023-06-06]]
> Last date annotations or notes modified: [[2023-08-13]]

> [!abstract] Related Zotero items (1):  
>
> | title | proxy note | desktopURI |
> | --- | --- | --- |
> | Fast r-cnn | [[@girshick2015fast]] | [Zotero Link](zotero://select/library/items/5C7LSXPE) |  |

> [!abstract]+
> 
> Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth. On the ImageNet dataset we evaluate residual nets with a depth of up to 152 layers—8× deeper than VGG nets [41] but still having lower complexity. An ensemble of these residual nets achieves 3.57% error on the ImageNet test set. This result won the 1st place on the ILSVRC 2015 classification task. We also present analysis on CIFAR-10 with 100 and 1000 layers. The depth of representations is of central importance for many visual recognition tasks. Solely due to our extremely deep representations, we obtain a 28% relative improvement on the COCO object detection dataset. Deep residual nets are foundations of our submissions to ILSVRC & COCO 2015 competitions1, where we also won the 1st places on the tasks of ImageNet detection, ImageNet localization, COCO detection, and COCO segmentation.
> 

---
## Persistant notes 
%% begin notes %%






%% end notes %%

---
# Annotations <small>(Exported: [[2023-08-13]]</small>)

## 💚 Important To Me
💚 In this paper, we address the degradation problem by introducing a deep residual learning framework. Instead of hoping each few stacked layers directly fit a desired underlying mapping, we explicitly let these layers fit a residual mapping. Formally, denoting the desired underlying mapping as H(x), we let the stacked nonlinear layers fit another mapping of F(x) := H(x) − x. The original mapping is recast into F(x)+x. We hypothesize that it is easier to optimize the residual mapping than to optimize the original, unreferenced mapping. To the extreme, if an identity mapping were optimal, it would be easier to push the residual to zero than to fit an identity mapping by a stack of nonlinear layers.
 <small>([page-2](zotero://open-pdf/library/items/ZIVWRUPE?page=2&annotation=X6VPFJEF)) edited:[[2023-06-06]]</small> ^x6vpfjef

## 📚 Ordinary notes
>![[Paper/Note/he2016deep/image-1-x301-y488.png]]<br>📝️ Figure 1. Training error (left) and test error (right) on CIFAR-10 with 20-layer and 56-layer “plain” networks. The deeper network has higher training error, and thus test error. Similar phenomena on ImageNet is presented in Fig. 4.
 <small>([page-1](zotero://open-pdf/library/items/ZIVWRUPE?page=1&annotation=GEHPQUFJ)) edited:[[2023-06-06]]</small> ^gehpqufj

📚 Driven by the significance of depth, a question arises: Is learning better networks as easy as stacking more layers? An obstacle to answering this question was the notorious problem of vanishing/exploding gradients [1, 9], which hamper convergence from the beginning. This problem, however, has been largely addressed by normalized initialization [23, 9, 37, 13] and intermediate normalization layers [16], which enable networks with tens of layers to start converging for stochastic gradient descent (SGD) with backpropagation [22].
📝️ 这是一个新的评论
 <small>([page-1](zotero://open-pdf/library/items/ZIVWRUPE?page=1&annotation=ZPTGA5PK)) edited:[[2023-06-06]]</small> ^zptga5pk

>![[Paper/Note/he2016deep/image-5-x121-y570.png]]<br> <small>([page-5](zotero://open-pdf/library/items/ZIVWRUPE?page=5&annotation=9S8VD6PV)) edited:[[2023-08-13]]</small> ^9s8vd6pv

>![[Paper/Note/he2016deep/image-8-x260-y619.png]]<br> <small>([page-8](zotero://open-pdf/library/items/ZIVWRUPE?page=8&annotation=KZNK3T7E)) edited:[[2023-06-17]]</small> ^kznk3t7e



%% Import Date: 2023-08-13T16:35:29.080+08:00 %%
