---
创建时间: 2023-06-11 05:05
难度: 
URL:
tag: 
---

```dataviewjs
var y = "2023"
var m = Array(12).fill(0).map(function(v,i){return i});
var d = [31,29,31,30,31,30,31,31,30,31,30,31]

for(let i of m)
{
    var n = Array(d[i]).fill(0).map(function(v,i){return i+1});
    var data = Array(d[i]).fill(0);

    for(let j of dv.pages(`"Algorithm/leetcode"`).filter(p=>String(p.file.cday).split("-")[0]==y && String(p.file.cday).split("-")[1]==i+1).groupBy(p=>String(p.file.cday).split("-")[2].slice(0,2)))
         data[j.key-1] = dv.pages(`"Algorithm/leetcode"`).filter(p=>String(p.file.cday).split("-")[2].slice(0,2)==j.key).length;

    if(data.every(p=>p==0))
        continue
    dv.header(4, i+1+"月");
    dv.paragraph(`\`\`\`chart
type: line
labels: [${n}]
series:
- title: Algorithm/leetcode
  data: [${data}]
labelColors: true
\`\`\``)
}
```

```dataview
table 创建时间,难度,tag from "Algorithm/leetcode" 
sort 创建时间
```
