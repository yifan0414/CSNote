---
状态: inbox
类型: idea
来源: thought
网址:
tags:
创建时间: 2026-04-25 01:13
---

## 核心观点

我们通常以为自己只是写了一句代码，或者给 AI 发了一句简单指令。  
但无论是传统编程，还是今天的 Agentic Model，真正决定最终行为的都不是这句“表面表达”本身，而是它背后的 **context（上下文）**。

在 C 语言里：

```c
printf("Hello\n");
```

表面上只是打印一句 `Hello`，但它背后依赖头文件、编译器、链接器、运行库、操作系统和终端。

在 Claude Code / Codex CLI / Cursor Agent 这类 Agentic 工具里：

```text
Hello
```

表面上只是向模型打招呼，但它背后可能携带系统提示词、工具说明、权限规则、历史对话、项目文件、当前运行环境，以及 Agent 的规划和工具调用机制。

所以，两者共同揭示了一个重要事实：

> **表达只是入口，真正决定行为的是表达所处的上下文。**

---

## 一、从文本大模型到推理大模型，再到 Agentic Model

大模型的发展可以粗略理解为三个阶段。

| 阶段 | 核心能力 | 典型表现 | 局限 |
|---|---|---|---|
| 文本大模型 | 生成、总结、翻译、问答 | 能流畅回答问题、写文章、写代码片段 | 主要停留在“说”，不一定真的执行 |
| 推理大模型 | 分解问题、逻辑推演、自我检查 | 数学、代码、复杂分析能力更强 | 能想，但不一定能操作真实环境 |
| Agentic Model | 规划、调用工具、执行任务、反馈修正 | 能读文件、改代码、跑命令、看结果、继续迭代 | 依赖上下文质量，容易受错误信息或环境限制影响 |

这条发展脉络可以概括为：

```text
会说话
→ 会思考
→ 会干活
```

文本大模型像一个会表达的人；  
推理大模型像一个会打草稿、会思考的人；  
Agentic Model 则像一个能打开电脑、调用工具、执行任务、检查结果的研究助理。

---

## 二、为什么说 Agentic Model 像传统编程工具链？

当我们在 C 语言中写：

```c
printf("Hello\n");
```

我们看到的是一行代码。  
但从系统角度看，它背后经历了完整的工具链：

```text
源代码
→ 预处理
→ 编译
→ 汇编
→ 链接
→ 加载
→ 运行
→ 调用系统接口
→ 终端显示 Hello
```

同样，当我们在 Agentic 工具中输入：

```text
Hello
```

看似只是一个简单 prompt，背后也可能发生：

```text
用户输入
→ 拼接系统 prompt
→ 拼接开发者规则
→ 拼接工具 schema
→ 拼接历史上下文
→ 读取项目环境
→ 模型判断意图
→ 生成计划
→ 可能调用工具
→ 观察工具结果
→ 再次推理
→ 输出最终结果
```

也就是说：

> **C 语言把人类可读代码转换成机器行为；Agentic Model 把自然语言转换成软件工具链行为。**

---

## 三、C 编译链与 Agent 运行时的对比

| C 语言世界            | Agentic Model 世界                       | 说明             |
| ----------------- | -------------------------------------- | -------------- |
| `printf("Hello")` | 用户输入 `Hello`                           | 表面表达都很简单       |
| 头文件               | 系统 prompt / 工具说明                       | 提供必要声明和能力边界    |
| 编译器               | 大模型                                    | 负责理解表达并转换成中间行为 |
| 链接器               | Agent runtime                          | 把模型能力和外部工具连接起来 |
| libc / runtime    | Claude Code / Codex CLI / Cursor Agent | 提供运行时能力        |
| 操作系统              | 文件系统、终端、浏览器、API                        | 提供真实执行环境       |
| 编译参数              | 工具权限、模型模式、上下文窗口                        | 影响最终行为         |
| 可执行文件             | 回复、代码修改、命令执行结果                         | 最终产物           |
| 系统调用              | 工具调用、API 调用、终端命令、文件读写                  | 真正改变外部世界的动作    |

这个对比说明：  
我们写下的表达本身并不是全部，背后的上下文和运行时系统才让它真正具有行为能力。

---

## 四、二者最相似的地方：高级表达依赖复杂上下文

无论是 C 语言，还是 Agentic Model，它们都体现了一个共同规律：

```text
高级表达 + 上下文 + 运行时 = 实际行为
```

### 1. C 语言中的例子

```c
#include <stdio.h>

int main() {
    printf("Hello\n");
    return 0;
}
```

这段代码能运行，并不是因为 `printf` 这几个字符天然会输出文字。  
它依赖：

- `stdio.h` 中的函数声明
- 编译器对 C 语言标准的理解
- 链接器找到标准库
- 操作系统提供进程和文件描述符
- 终端接收输出内容

所以可以写成：

```text
代码 + 编译上下文 + 链接上下文 + 运行上下文 = 程序行为
```

### 2. Agentic Model 中的例子

你在 Agent 工具里输入：

```text
帮我修复这个 bug
```

这句话本身是不完整的。  
它需要结合上下文才有意义：

- 当前代码仓库是什么？
- 报错日志是什么？
- 哪些文件可以修改？
- 项目如何运行测试？
- 用户希望最小修改还是重构？
- 之前是否已经尝试过某些方案？
- Agent 有无权限运行命令？

所以可以写成：

```text
用户指令 + 项目上下文 + 工具权限 + 历史反馈 = Agent 行为
```

---

## 五、核心关键词：Context

这两件事共同揭示了一个关键词：

# Context

上下文不是附属信息，而是意义的一部分。

一句话、一行代码、一个 prompt，离开上下文后都可能变得模糊甚至无效。

可以用一个更抽象的公式表示：

```text
Expression + Context → Meaning + Behavior
```

| 概念 | 在 C 语言中 | 在 Agentic Model 中 |
|---|---|---|
| Expression | `printf("Hello")` | `Hello` / `帮我修 bug` |
| Context | 头文件、编译器、库、OS、编译参数 | 系统 prompt、历史对话、工具、文件、运行环境 |
| Meaning | 调用标准输出函数 | 打招呼、测试系统、继续任务、执行操作 |
| Behavior | 终端打印文本 | 回复、规划、调用工具、修改代码 |

---

## 六、为什么 Agent 比 C 更依赖 Context？

C 语言当然依赖上下文，但它的语义相对稳定。  
在正常情况下，`printf("Hello\n")` 的行为比较确定。

但自然语言更模糊。  
同一句话在不同上下文下可能完全不同。

例如：

```text
帮我看一下这个问题
```

在不同场景中可能表示：

| 上下文 | 真实含义 |
|---|---|
| 数学题旁边 | 解题 |
| 代码仓库里 | Debug |
| 论文草稿旁边 | 审稿和润色 |
| 服务器日志旁边 | 排查故障 |
| 实验表格旁边 | 分析结果 |

所以在 Agentic Model 中，context 不只是辅助材料，而几乎就是语义本身的一部分。

这也是为什么现在大家越来越重视：

- long context
- memory
- retrieval
- tool state
- environment grounding
- multi-turn planning
- context engineering

---

## 七、从 Prompt Engineering 到 Context Engineering

早期大家经常讨论 prompt engineering，似乎写出一句“神奇提示词”就能让模型变强。

但 Agent 时代更重要的是：

> **不是单个 prompt 多漂亮，而是完整上下文组织得好不好。**

这就是 **context engineering（上下文工程）**。

它关心的不是一句提示词，而是整个任务环境：

| Prompt Engineering | Context Engineering |
|---|---|
| 关注一句提示词怎么写 | 关注完整任务环境怎么组织 |
| 偏向一次性问答 | 偏向多步任务执行 |
| 主要优化表达方式 | 需要管理文档、工具、历史、反馈、权限 |
| 适合聊天模型 | 更适合 Agentic Model |
| 目标是让模型答得更好 | 目标是让 Agent 做得更对 |

举例来说，与其只写：

```
你是一个资深程序员，请帮我修 bug。
```

不如提供完整上下文（**当然目前的 Claude/Codex 一般都会引导执行操作系统命令去主动获取这些信息**）：

```
目标：修复训练脚本中的 CUDA OOM 问题
环境：4 张 RTX 4090，CUDA 12.1，PyTorch 2.4
约束：不能改动数据预处理逻辑
验证方式：运行 scripts/test_train_small.sh
期望结果：显存占用下降，最小测试通过
相关文件：train.py, configs/video_qa.yaml, models/encoder.py
```

后者明显更适合 Agent 执行真实任务。

---

## 八、未来软件工程可能从 Code-centric 走向 Context-centric

传统软件工程更偏 **code-centric**：

```text
代码是核心产物。
```

但 Agent 时代，软件工程会越来越 **context-centric**：

```text
代码仍然重要，但代码周围的上下文也成为一等公民。
```

也就是说，未来一个项目不只是要“能被人读懂”，还要“能被 Agent 理解”。

### 传统 code-centric 项目

```text
src/
models/
utils/
train.py
README.md
```

只要人能理解、代码能运行，大体就可以继续开发。

### 面向 Agent 的 context-centric 项目

```text
src/
models/
utils/
configs/
scripts/
tests/
docs/
README.md
AGENTS.md
CLAUDE.md
EXPERIMENTS.md
KNOWN_ISSUES.md
```

这里的额外文件并不是形式主义，而是在给 Agent 提供上下文：

| 文件 | 作用 |
|---|---|
| `README.md` | 说明项目目标和基本使用方法 |
| `AGENTS.md` / `CLAUDE.md` | 告诉 Agent 如何工作、哪些文件不能动、如何验证 |
| `configs/` | 保存实验配置，减少隐式参数 |
| `scripts/` | 提供可复现命令 |
| `tests/` | 提供自动验证标准 |
| `docs/` | 解释设计思路 |
| `KNOWN_ISSUES.md` | 记录已知问题和坑 |
| `EXPERIMENTS.md` | 记录实验结果和结论 |

---

## 九、一个面向 Agent 的项目说明文件示例

可以在项目根目录放一个 `AGENTS.md`：

```markdown
# Project Guide for AI Agents

## Project Goal

本项目用于长视频理解 / 视频问答实验，重点研究视频 token 压缩和 question-aware frame selection。

## Environment

- Python: 3.10
- CUDA: 12.1
- PyTorch: 2.4
- GPU: 2 x RTX 3090

## Common Commands

### Run minimal test

```bash
bash scripts/test_minimal.sh
```

### Run evaluation

```bash
python scripts/eval.py --config configs/egoschema.yaml
```

### Check latency

```bash
python scripts/check_latency.py --config configs/latency.yaml
```

## Directory Structure

- `models/`: 模型结构
- `configs/`: 实验配置
- `scripts/`: 训练、评测和测试脚本
- `data/`: 数据路径配置，不要修改原始数据
- `outputs/`: 实验输出结果
- `docs/`: 方法说明和实验记录

## Rules for Agents

1. 不要删除 `data/` 和 `outputs/` 下的文件。
2. 修改模型结构后，必须运行 `scripts/test_minimal.sh`。
3. 修改配置文件后，需要说明具体改动原因。
4. 优先做最小可验证修改，不要无意义重构。
5. 如果测试失败，需要保留报错信息并分析原因。

## Known Issues

- 某些视频数据路径依赖本地软链接。
- `torchrun` 参数和单卡运行参数不同。
- batch size 过大时容易出现 CUDA OOM。
```
这样的文件对人类开发者有用，对 Agent 更有用。

它相当于给 Agent 提供了项目的“编译环境”和“运行说明”。
```

---

## 十、为什么测试和验证会变得更重要？

当 Agent 能自动改代码以后，核心问题不再只是：

```text
它会不会写？
```

而是：

```text
怎么知道它写对了？
```

所以测试、benchmark、验证脚本会成为非常重要的 context。

没有测试时，Agent 只能根据语言判断“看起来对”。  
有测试时，Agent 可以进入闭环：

```text
修改代码
→ 运行测试
→ 看到报错
→ 分析原因
→ 再次修改
→ 直到通过
```

这也是为什么 coding agent 发展最快。  
因为代码任务天然具有明确反馈：

- 编译是否通过
- 单元测试是否通过
- benchmark 是否提升
- latency 是否下降
- error log 是否消失

相比之下，写论文、做设计、做战略分析更难，因为它们的反馈标准不如代码任务明确。

---

## 十一、Context-centric 也会带来新问题

上下文越重要，管理上下文就越重要。

| 问题 | 说明 |
|---|---|
| 上下文过期 | README 写的是旧命令，会误导 Agent |
| 上下文冲突 | 文档说一种做法，代码实际是另一种做法 |
| 上下文污染 | 历史对话中的错误结论被继续沿用 |
| 上下文过长 | 信息太多，模型抓不住重点 |
| 上下文缺失 | 没有测试、没有日志、没有约束，Agent 只能猜 |
| 上下文安全 | 仓库或网页中可能包含恶意 prompt injection |

因此，未来 Agent 工程中可能会出现一系列新问题：

```text
上下文选择
上下文压缩
上下文优先级
上下文验证
上下文隔离
上下文版本管理
上下文安全
```

这些问题会越来越像传统软件工程里的依赖管理、编译配置和运行时管理。

---

## 十二、对个人开发者和科研工作的启发

对于个人开发者，尤其是经常做科研代码和实验的人，最实际的启发是：

> **不要只写代码，还要主动构造让人和 Agent 都能理解的上下文。**

具体来说：

1. 项目根目录写清楚 `README.md`
2. 给 Agent 准备 `AGENTS.md` 或 `CLAUDE.md`
3. 把常用命令沉淀到 `scripts/`
4. 把实验参数写进 `configs/`
5. 把最小验证流程做成脚本
6. 把已知问题记录到 `KNOWN_ISSUES.md`
7. 把实验结论记录到 `EXPERIMENTS.md`
8. 让每次修改都有可验证标准

这样做的好处是：

- 人类更容易接手项目
- Agent 更不容易误解任务
- 实验更容易复现
- Debug 更容易形成闭环
- 长期维护成本更低

---

## 十三、总结

从 `printf("Hello")` 到 Agentic Model，我们看到的是同一个趋势：

> **表面表达越来越简单，背后的上下文系统越来越复杂。**

传统编程中，一行代码依赖编译器、库和操作系统。  
Agentic Model 中，一句自然语言依赖 prompt、历史、工具、环境和反馈。

所以真正重要的不是孤立的代码，也不是孤立的 prompt，而是：

```text
Expression + Context → Meaning + Behavior
```

未来的软件工程可能会逐渐从：

```text
Code-centric
```

走向：

```text
Context-centric
```

也就是说，程序员不只是写代码的人，也会越来越像上下文系统的设计者。

最后可以用一句话概括：

> **源码不是程序的全部，prompt 也不是模型行为的全部。真正决定结果的，是表达与上下文共同构成的系统。**
