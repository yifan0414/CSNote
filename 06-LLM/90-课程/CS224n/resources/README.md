# CS224N Winter 2026 资源说明

本目录是 [Stanford CS224N 官网](https://web.stanford.edu/class/cs224n/index.html) Winter 2026 课程资料的个人学习归档，整理日期为 2026-09-04。课表中的原始 URL 保留在每节 Markdown 笔记和 `source/schedule-2026.json` 中。

## 目录

- `slides/`：官方课件 PDF，包括课程介绍与历史分卷。
- `notes/`：官方课程讲义与数学复习资料。
- `readings/`：官网课表列出的指定/扩展论文，以及官网列出的三本背景教材。
- `tutorials/`：Python、PyTorch 和 Hugging Face Notebook/课件。
- `assignments/`：A1–A4 代码包、PDF handout 和 LaTeX 模板。
- `projects/`：Proposal、Default Project、Milestone、Report、Poster 和项目建议。
- `source/`：官网 HTML 快照、结构化课表、笔记构建脚本和完整性校验脚本。

## 归档范围

- 22 个教学单元。
- 22 篇课程笔记均已写入知识正文，内容依据课件全文、Notebook 代码和官方指定阅读整理，不是只有大纲或学习计划。
- 课表中 110 处本地资源引用，去重后为 108 个文件，全部存在且通过格式校验。
- 102 个 PDF、7 个 ZIP、3 个 Jupyter Notebook。
- 16 项纯网页资源保留在笔记中，包括教程网页、讲者主页、博客文章和在线基准项目。
- 官网未发布 PPT 的课节会在对应 Markdown 中明确标注，不使用来源不明的替代课件。

## 校验

在 `CS224n` 目录上级运行：

```bash
python3 CS224n/resources/source/verify_archive.py
```

校验器会检查课表覆盖、PDF 可解析性、ZIP CRC、Notebook JSON、Python 语法、Markdown 数量与 Obsidian 双链目标。`SHA256SUMS.txt` 记录了归档文件的 SHA-256。

> [!note]
> 资料版权归原作者和发布方所有；本地归档仅用于个人学习。
