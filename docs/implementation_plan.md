# PPT-Agent 实现方案与计划

## 1. 项目概述

本项目旨在实现一个能够自动生成高质量 PPT 的智能体系统。采用 **Proposer-Reviewer (Editor-Critic)** 范式，利用 **Slidev** 作为底层渲染框架，结合 **Vision LLM** 进行视觉质量评估与迭代优化。

## 2. 系统架构

系统由两个核心 Agent 和一个渲染环境组成：

1.  **Editor Agent (Proposer)**:
    *   **职责**: 负责内容生成和代码编写。将输入的文本内容转化为符合 Slidev 语法的 Markdown/HTML 代码。
    *   **输入**: 原始文本（如论文摘要）、Critic 的反馈意见。
    *   **输出**: `slides.md` 文件内容。
    *   **能力**: 理解长文本逻辑、掌握 Markdown/HTML/Slidev 语法、根据反馈修改代码。

2.  **Critic Agent (Reviewer)**:
    *   **职责**: 负责视觉质量评估。
    *   **输入**: 每一页幻灯片的渲染截图。
    *   **输出**: 结构化的改进建议（JSON格式）。
    *   **能力**: 多模态视觉理解（Vision LLM）、设计美学评估、布局分析。

3.  **渲染环境 (Slidev Runtime)**:
    *   **职责**: 将 Markdown 代码渲染为可视化图像。
    *   **工具**: `slidev` 命令行工具。
    *   **动作**: 生成 PNG/PDF 用于 Critic 审查。

## 3. 工作流程 (Workflow)

整个过程是一个闭环迭代系统：

1.  **初始化**: 用户提供长文本输入（如 2000 字论文摘要）。
2.  **初稿生成 (Drafting)**: Editor Agent 分析文本，生成初始版本的 `slides.md`。
3.  **渲染 (Rendering)**: 系统调用 `slidev export` 将 `slides.md` 渲染为一系列 PNG 图片。
4.  **视觉审查 (Critique)**:
    *   Critic Agent 逐页（或批量）分析 PNG 图片。
    *   评估维度：内容密度、可读性、布局、美观度。
    *   生成反馈报告（包含页码、问题描述、具体修改建议）。
5.  **迭代修改 (Refining)**:
    *   Editor Agent 读取 `slides.md` 和 Critic 的反馈报告。
    *   针对性地修改代码（如拆分页面、调整字号、移动元素）。
    *   生成新版本的 `slides.md`。
6.  **终止判断**:
    *   如果 Critic 评分达标 OR 达到最大迭代次数（如 5 次），则输出最终结果。
    *   否则，返回步骤 3。

## 4. 文件结构设计

建议在 `PPT-agent` 目录下采用以下结构：

```text
PPT-agent/
├── data/                       # 存放输入数据
│   └── paper_summary.txt       # 示例：论文摘要输入
├── output/                     # 存放运行时的输出文件
│   ├── current/                # 当前最新版本
│   │   ├── slides.md           # Slidev 源码
│   │   └── images/             # 渲染出的图片 (page-01.png, ...)
│   └── history/                # 历史迭代记录 (用于分析对比)
│       └── iter_1/
├── src/                        # 源代码
│   ├── __init__.py
│   ├── agents/                 # Agent 定义
│   │   ├── base_agent.py
│   │   ├── editor.py           # Editor Agent 实现
│   │   └── critic.py           # Critic Agent 实现
│   ├── utils/                  # 工具类
│   │   ├── llm_client.py       # LLM API 封装 (OpenAI/Anthropic)
│   │   └── slidev_runner.py    # 调用 slidev layout/export 的封装
│   └── main.py                 # 主程序入口，控制迭代循环
├── assets/                     # 静态资源 (如需要的默认图片、Logo)
├── package.json                # Node.js 依赖 (Slidev)
├── requirements.txt            # Python 依赖
└── README.md                   # 项目说明
```

## 5. 详细实现步骤

### 第一阶段：环境搭建与基础打通
1.  **安装 Slidev**:
    *   在根目录初始化 `package.json`，安装 `@slidev/cli`, `@slidev/theme-default` 等。
    *   确保可以通过命令 `npx slidev export slides.md --output exported` 正常生成图片。
2.  **LLM 接口封装**:
    *   封装 Python 接口调用 GPT-4o (支持 Vision)。
    *   实现基础的 `chat(messages, image_paths=[])` 函数。

### 第二阶段：Editor Agent 实现
1.  **Prompt 设计**:
    *   System Prompt 需要包含 Slidev 的核心语法教程（Frontmatter, 分页符 `---`, 布局 `layout: two-cols` 等）。
    *   提供 few-shot 示例，展示如何将一段文字转化为幻灯片。
2.  **代码实现**:
    *   读取 `data/paper_summary.txt`。
    *   生成第一版 `slides.md` 并保存到 `output/current/`。

### 第三阶段：Critic Agent 与 渲染循环
1.  **渲染器封装**:
    *   编写 Python 脚本调用 `subprocess` 执行 slidev 导出命令。
    *   将生成的 PDF 或 PNG 路径整理为列表。
2.  **Critic Prompt 设计**:
    *   System Prompt 定义评估标准（密度、字号、重叠）。
    *   要求输出 JSON 格式的反馈，例如：`[{"page": 3, "issue": "text_overflow", "suggestion": "split into two slides"}]`。

### 第四阶段：迭代闭环
1.  **Orchestrator (Main Loop)**:
    *   编写 `main.py` 连接 Editor -> Renderer -> Critic -> Editor。
    *   处理 Critic 反馈，将其转换为自然语言提示词喂回给 Editor ("请根据以下反馈修改 slides.md: ...")。
2.  **状态管理**:
    *   保存每一轮的 `slides.md` 和 Critic 反馈，用于后续分析。

## 6. 关键难点与解决方案

1.  **Slidev 语法容错**:
    *   Editor 生成的 Markdown 可能包含语法错误导致 Slidev 渲染失败。
    *   *方案*: 在渲染前增加一个简单的 Syntax Check 步骤，或者将渲染报错信息反馈给 Editor 让其自我修复。
2.  **幻觉与上下文控制**:
    *   多轮迭代后 Context 会很长。
    *   *方案*: Editor 每一轮只保留“当前版本的代码”和“最新一轮的修改建议”，丢弃旧的历史代码和过期的建议。
3.  **精准定位修改**:
    *   Critic 指出“第 3 页有问题”，Editor 需要知道 Markdown 文件中哪一部分对应“第 3 页”。
    *   *方案*: 在 Prompt 中要求 Editor 严格使用 `---` 分隔，程序可以通过切分 `---` 来定位具体的 Slide 内容块。

## 7. 预备工作

请确保环境中已安装：
*   Python 3.10+
*   Node.js 18+
*   OpenAI API Key (支持 GPT-4o 或其他 Vision 模型)
