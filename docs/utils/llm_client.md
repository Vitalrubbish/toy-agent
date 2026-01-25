# LLM Client Utility Specification

## 职责
封装与大模型提供商（如 OpenAI）的 API 交互细节，提供统一的同步/异步接口，处理重试、错误捕获和 Token 计数。

## 类定义 `LLMClient`

### 依赖
*   `openai` SDK
*   `os` (Environment Variables)

### 方法

#### `__init__(self, provider="openai", api_key=None)`
*   读取 `OPENAI_API_KEY` 环境变量。
*   初始化 OpenAI Client。

#### `chat_completion(self, messages: List[Dict], model: str, temperature: float = 0.7, json_mode: bool = False) -> str`
*   **功能**: 发送对话请求。
*   **参数**:
    *   `messages`: 标准 OpenAI 格式的消息列表 `[{"role": "user", "content": ...}]`。
    *   `model`: 模型名称。
    *   `json_mode`: 是否强制 JSON 输出（设置 response_format）。
*   **处理**:
    *   添加 Retry 机制（处理 RateLimitError, APIConnectionError）。
    *   简单的 Token 消耗日志记录。
*   **多模态支持**:
    *   负责检查 `messages` 中是否包含 Image Content（Base64/URL），并适配 OpenAI 的 Vision API 格式。

#### `_encode_image(self, image_path: str) -> str`
*   辅助函数：将本地图片转换为 Base64 字符串，用于 Vision API 调用。
