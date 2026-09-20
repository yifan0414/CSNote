---
类型: tool
status: unread
来源: null
网址: null
发现时间: 2026-04-28
tags:
  - macOS
  - MathJax
  - 浏览器
  - 用户脚本
created: 2026-04-28
updated: 2026-09-20
---

# 解决 Mac 上浏览器 MathJax 渲染问题

```js
// ==UserScript==
// @name         Codeforces MathJax TeX Font Fix
// @namespace    http://tampermonkey.net/
// @version      0.6
// @description  修复 macOS Edge/Chrome 下 Codeforces MathJax 字体渲染，同时避免首次进入显示 $$$...$$$
// @match        https://codeforces.com/*
// @match        https://www.acwing.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const script = document.createElement('script');
    script.type = 'text/x-mathjax-config';

    script.textContent = `
        MathJax.Hub.Config({
            "HTML-CSS": {
                availableFonts: ["TeX"],
                preferredFont: "TeX",
                webFont: "TeX",
                imageFont: null
            },
            SVG: {
                font: "TeX"
            },
            CommonHTML: {
                font: "TeX"
            }
        });

        MathJax.Hub.Register.StartupHook("End", function () {
            try {
                MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
            } catch (e) {}
        });

        console.log("[油猴脚本] MathJax 字体配置已追加，未覆盖 Codeforces 原配置。");
    `;

    document.documentElement.appendChild(script);
})();
```
