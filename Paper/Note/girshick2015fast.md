---
citekey: girshick2015fast
authors: Ross Girshick
title: "Fast r-cnn"
alias: 
Year: 2015
tags: [literature-note, ]
Authors: Ross Girshick
publisher: ""
doi: 
---
# Fast r-cnn

> [!info]+ Info - [**Zotero**](zotero://select/library/items/5C7LSXPE)   | Local [**PDF**](file:////Users/yifansu/Zotero/storage/8VBVTWY6/Girshick%20-%202015%20-%20Fast%20r-cnn.pdf)
> Authors: [[Ross Girshick]],  
> Type: conferencePaper
> Year: 2015
> Zotero links: [Item](zotero://select/library/items/5C7LSXPE) PDF: [Girshick - 2015 - Fast r-cnn.pdf](zotero://select/library/items/8VBVTWY6) 
> Web links: [Item](http://zotero.org/users/9245962/items/5C7LSXPE) PDF: [Girshick - 2015 - Fast r-cnn.pdf](file:///Users/yifansu/Zotero/storage/8VBVTWY6/Girshick%20-%202015%20-%20Fast%20r-cnn.pdf) 
> 
>
> **History**
> Date item added to Zotero: [[2023-06-06]]
> First date annotations or notes modified: [[2023-06-06]]
> Last date annotations or notes modified: [[2023-08-03]]

> [!abstract] Related Zotero items (1):  
>
> | title | proxy note | desktopURI |
> | --- | --- | --- |
> | Deep residual learning for image recognition | [[@he2016deep]] | [Zotero Link](zotero://select/library/items/IX39V35N) |  |

> [!abstract]+
> 
> 这是一个测试
> 

---
## Persistant notes 
%% begin notes %%






%% end notes %%

---
# Annotations <small>(Exported: [[2023-08-13]]</small>)

## ⛔ Disagree With Author
⛔ First, the last max pooling layer is replaced by a RoI pooling layer that is configured by setting H and W to be compatible with the net’s first fully connected layer (e.g., H = W = 7 for VGG16).
 <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=K7AH77XD)) edited:[[2023-06-06]]</small> ^k7ah77xd

## 📚 Ordinary notes
📚 Complexity arises because detection requires the accurate localization of objects, creating two primary challenges. First, numerous candidate object locations (often called “proposals”) must be processed. Second, these candidates provide only rough localization that must be refined to achieve precise localization. Solutions to these problems often compromise speed, accuracy, or simplicity.
 <small>([page-1](zotero://open-pdf/library/items/8VBVTWY6?page=1&annotation=9DPR6P6D)) edited:[[2023-06-06]]</small> ^9dpr6p6d

>![[Paper/Note/girshick2015fast/image-1-x322-y395.png]]<br> <small>([page-1](zotero://open-pdf/library/items/8VBVTWY6?page=1&annotation=FLQ9GQ5Q)) edited:[[2023-06-11]]</small> ^flq9gq5q

>![[Paper/Note/girshick2015fast/image-2-x308-y616.png]]<br>📝️ Figure 1. Fast R-CNN architecture. $$L_{\mathrm{loc}}\left(t^u, v\right)=\sum_{i \in\{\mathrm{x}, \mathrm{y}, \mathrm{w}, \mathrm{h}\}} \operatorname{smooth}_{L_1}\left(t_i^u-v_i\right)$$
 <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=837H4LNI)) edited:[[2023-06-08]]</small> ^837h4lni

>![[Paper/Note/girshick2015fast/image-2-x300-y410.png]]<br>#zotero://note/u/zzbi4gqj/  <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=QRYGMGDT)) edited:[[2023-06-11]]</small> ^qrygmgdt

>![[Paper/Note/girshick2015fast/image-3-x46-y539.png]]<br> <small>([page-3](zotero://open-pdf/library/items/8VBVTWY6?page=3&annotation=HKI5VPKH)) edited:[[2023-06-11]]</small> ^hki5vpkh

📝️ 这里是一个不错的选择，但是我并不理解
 <small>([page-3](zotero://open-pdf/library/items/8VBVTWY6?page=3&annotation=B92WK4K7)) edited:[[2023-06-06]]</small> ^b92wk4k7

>![[Paper/Note/girshick2015fast/image-3-x325-y658.png]]<br> <small>([page-3](zotero://open-pdf/library/items/8VBVTWY6?page=3&annotation=6W523CQG)) edited:[[2023-07-03]]</small> ^6w523cqg

>![[Paper/Note/girshick2015fast/image-4-x95-y608.png]]<br> <small>([page-4](zotero://open-pdf/library/items/8VBVTWY6?page=4&annotation=DPXUZDBY)) edited:[[2023-06-11]]</small> ^dpxuzdby

>![[Paper/Note/girshick2015fast/image-6-x46-y420.png]]<br> <small>([page-6](zotero://open-pdf/library/items/8VBVTWY6?page=6&annotation=3ES8ESFA)) edited:[[2023-06-06]]</small> ^3es8esfa

>![[Paper/Note/girshick2015fast/image-7-x92-y653.png]]<br> <small>([page-7](zotero://open-pdf/library/items/8VBVTWY6?page=7&annotation=X596UG35)) edited:[[2023-08-02]]</small> ^x596ug35

📚 There are (broadly) two types of object detectors: those that use a sparse set of object proposals (e.g., selective search [21]) and those that use a dense set (e.g., DPM [8]). Classifying sparse proposals is a type of cascade [22] in which the proposal mechanism first rejects a vast number of candidates leaving the classifier with a small set to evaluate.
 <small>([page-8](zotero://open-pdf/library/items/8VBVTWY6?page=8&annotation=XE39QYDD)) edited:[[2023-08-03]]</small> ^xe39qydd

## ⚙️ Methodology
⚙️ Training all network weights with back-propagation is an important capability of Fast R-CNN. First, let’s elucidate why SPPnet is unable to update weights below the spatial pyramid pooling layer.
 <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=C8EM34U4)) edited:[[2023-06-21]]</small> ^c8em34u4



%% Import Date: 2023-08-13T16:31:56.448+08:00 %%
