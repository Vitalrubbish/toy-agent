# Main Orchestrator Specification

## 职责
`main.py` 是系统的入口和编排器（Orchestrator），负责协调 Editor Agent、Critic Agent 和 Slidev Environment 之间的交互。

## 流程逻辑
1.  **初始化**:
    *   加载环境变量（OpenAI API Key）。
    *   读取输入数据（如 `data/paper_summary.txt`）。
    *   初始化 `EditorAgent` 和 `CriticAgent` 实例。
    *   建立输出目录结构 `output/current/`, `output/history/`。

2.  **迭代循环 (Iteration Loop)**:
    *   **Loop Condition**: `current_iteration < max_iterations` AND `quality_score < threshold` (可选，或仅基于 Critic 通过与否)。
    *   **Step 1: Drafting/Refining (Editor)**
        *   调用 `EditorAgent.generate_slides(content, feedback)`。
        *   如果 `feedback` 为空（由于是第一轮），则进行初稿生成。
        *   如果 `feedback` 存在，则进行修改。
        *   将生成的 `slides.md` 保存到 `output/current/slides.md`。
    *   **Step 2: Rendering (Environment)**
        *   调用 `SlidevRunner.build(input_file, output_dir)`。
        *   等待渲染完成，获取截图路径列表 `[path/to/page-1.png, ...]`.
    *   **Step 3: Critiquing (Critic)**
        *   调用 `CriticAgent.review(image_paths)`。
        *   获取结构化反馈 `JSON` 对象。
        *   保存反馈到 `output/history/iter_N/critique.json`。
    *   **Step 4: Logging**
        *   将当前轮次的 `slides.md` 和截图归档到 `output/history/iter_N/`。
    *   **Step 5: Decision**
        *   分析 Critic 反馈，如果反馈中没有严重问题（Severity High），或者 Critic 明确表示 "Approved"，则跳出循环。
        *   否则，将反馈传递给下一轮 Editor。

3.  **结束**:
    *   输出最终结果路径。
    *   打印总耗时和Token消耗统计。

## 依赖关系
*   `src.agents.editor.EditorAgent`
*   `src.agents.critic.CriticAgent`
*   `src.utils.slidev_runner.SlidevRunner`
