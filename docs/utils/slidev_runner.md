# Slidev Runner Utility Specification

## 职责
封装 Node.js `slidev` 命令行工具的调用，负责将 Markdown 源码编译/渲染为图像文件。

## 类定义 `SlidevRunner`

### 依赖
*   `subprocess`: 执行 Shell 命令。
*   `pathlib`: 路径处理。

### 方法

#### `__init__(self, work_dir: str)`
*   `work_dir`: PPT-Agent 的工作根目录（包含 `package.json` 的目录）。

#### `install_dependencies(self)`
*   执行 `npm install` 确保 Slidev 环境就绪。
*   (可选) 检查 `npm list` 确认 slidev 是否存在。

#### `render_slides(self, md_file_path: str, output_dir: str) -> List[str]`
*   **功能**: 调用 slidev 导出功能。
*   **命令**: `npx slidev export <md_file_path> --output <output_dir> --format png --timeout 60000` (具体参数视 slidev 版本而定)。
*   **Wait**: 阻塞直到渲染完成。
*   **Return**: 生成的图片文件的绝对路径列表，按页码排序。
*   **异常处理**: 捕获 `stderr`，如果渲染失败（如 Markdown 语法错误），抛出自定义异常 `RenderError`，供 EditorAgent 捕获并尝试修复。

#### `check_syntax(self, code: str) -> bool`
*   (Advanced) 在渲染前进行简单的静态检查，防止明显的 Slidev 语法错误（如 Frontmatter 格式错误）。

## 注意事项
*   Slidev Export 需要 Playwright/Chromium 支持。在 Docker 或无头环境中可能需要特殊配置。
*   输出文件名通常是 `01.png`, `02.png` 或 `slides-1.png`，需要编写逻辑来正确收集这些文件。
