# Base Agent Specification

## 职责
定义所有 Agent 的基类，规范 LLM 的调用接口、状态管理和日志记录。

## 类定义 `BaseAgent`

### 属性
*   `role`: Agent 的角色名称 (e.g., "Editor", "Critic").
*   `model_name`: 使用的模型名称 (e.g., "gpt-4o").
*   `llm_client`: `LLMClient` 的实例，用于发送请求。
*   `history`: 对话历史记录（System Prompt, User Messages, Assistant Messages）。

### 方法
#### `__init__(self, role: str, model_name: str = "gpt-4o")`
初始化 Agent，设置角色和模型。

#### `chat(self, user_content: str, image_paths: List[str] = None) -> str`
*   核心交互方法。
*   **Args**:
    *   `user_content`: 用户的文本输入。
    *   `image_paths`: (可选) 图片路径列表，用于 Vision 能力。
*   **Behavior**:
    1.  构造 Message 列表（包含 System Prompt）。
    2.  如果存在图片，将图片编码为 Base64 或 URL 格式加入 Message。
    3.  调用 `self.llm_client.chat_completion(messages)`。
    4.  更新 `history`。
    5.  返回响应文本。

#### `reset_history(self)`
清空对话历史（保留 System Prompt）。如果策略是每一轮都重置 Context 以避免污染，此方法很重要。

#### `set_system_prompt(self, prompt: str)`
设置或更新 System Prompt。
