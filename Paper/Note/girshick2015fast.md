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
> Last date annotations or notes modified: [[2023-06-06]]

> [!abstract]+
> 
> 这是一个测试
> 


> [!note] Notes (1)
> ### 注释  
(2023/6/6 上午3:03:17)

[Go to annotation](zotero://open-pdf/library/items/8VBVTWY6?page=1&annotation=9DPR6P6D)“Complexity arises because detection requires the accurate localization of objects, creating two primary challenges. First, numerous candidate object locations (often called “proposals”) must be processed. Second, these candidates provide only rough localization that must be refined to achieve precise localization. Solutions to these problems often compromise speed, accuracy, or simplicity.” ([Girshick, 2015, p. 1](zotero://select/library/items/5C7LSXPE))

 [Go to annotation](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=837H4LNI)  
([Girshick, 2015, p. 2](zotero://select/library/items/5C7LSXPE)) Figure 1. Fast R-CNN architecture.  

$$L_{\mathrm{loc}}\left(t^u, v\right)=\sum_{i \in\{\mathrm{x}, \mathrm{y}, \mathrm{w}, \mathrm{h}\}} \operatorname{smooth}_{L_1}\left(t_i^u-v_i\right),$$

> 这是一个不错的选择

 [Go to annotation](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=QRYGMGDT)  
([Girshick, 2015, p. 2](zotero://select/library/items/5C7LSXPE))

[Go to annotation](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=K7AH77XD)“First, the last max pooling layer is replaced by a RoI pooling layer that is configured by setting H and W to be compatible with the net’s first fully connected layer (e.g., H = W = 7 for VGG16).” ([Girshick, 2015, p. 2](zotero://select/library/items/5C7LSXPE))

([Girshick, 2015, p. 3](zotero://select/library/items/5C7LSXPE)) 这里是一个不错的选择，但是我并不理解

 [Go to annotation](zotero://open-pdf/library/items/8VBVTWY6?page=6&annotation=3ES8ESFA)  
([Girshick, 2015, p. 6](zotero://select/library/items/5C7LSXPE)) 这里说明了一个好的选择
>> 
> <small>📝️ (modified: 2023-06-06) [link](zotero://select/library/items/8RBRUXL4) - [web](http://zotero.org/users/9245962/items/8RBRUXL4)</small>
>  
> ---

---
## Persistant notes 
%% begin notes %%







%% end notes %%

---
# Annotations <small>(Exported: [[2023-06-06]]</small>)

## ⛔ Disagree With Author
⛔ First, the last max pooling layer is replaced by a RoI pooling layer that is configured by setting H and W to be compatible with the net’s first fully connected layer (e.g., H = W = 7 for VGG16).
 <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=K7AH77XD)) edited:[[2023-06-06]]</small> ^k7ah77xd

## 📚 Ordinary notes
📚 Complexity arises because detection requires the accurate localization of objects, creating two primary challenges. First, numerous candidate object locations (often called “proposals”) must be processed. Second, these candidates provide only rough localization that must be refined to achieve precise localization. Solutions to these problems often compromise speed, accuracy, or simplicity.
 <small>([page-1](zotero://open-pdf/library/items/8VBVTWY6?page=1&annotation=9DPR6P6D)) edited:[[2023-06-06]]</small> ^9dpr6p6d

>![[Paper/Note/girshick2015fast/image-2-x308-y616.png]]<br>📝️ Figure 1. Fast R-CNN architecture.
>$$
L_{\mathrm{loc}}\left(t^u, v\right)=\sum_{i \in\{\mathrm{x}, \mathrm{y}, \mathrm{w}, \mathrm{h}\}} \operatorname{smooth}_{L_1}\left(t_i^u-v_i\right)
>$$
 <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=837H4LNI)) edited:[[2023-06-06]]</small> ^837h4lni

>![[Paper/Note/girshick2015fast/image-2-x300-y410.png]]<br> <small>([page-2](zotero://open-pdf/library/items/8VBVTWY6?page=2&annotation=QRYGMGDT)) edited:[[2023-06-06]]</small> ^qrygmgdt

📝️ 这里是一个不错的选择，但是我并不理解
 <small>([page-3](zotero://open-pdf/library/items/8VBVTWY6?page=3&annotation=B92WK4K7)) edited:[[2023-06-06]]</small> ^b92wk4k7

>![[Paper/Note/girshick2015fast/image-6-x46-y420.png]]<br> <small>([page-6](zotero://open-pdf/library/items/8VBVTWY6?page=6&annotation=3ES8ESFA)) edited:[[2023-06-06]]</small> ^3es8esfa



%% Import Date: 2023-06-06T04:40:54.007+08:00 %%
