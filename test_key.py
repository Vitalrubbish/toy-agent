import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. 加载 .env 文件
print("正在加载环境变量...")
load_success = load_dotenv()
if load_success:
    print("✅ .env 文件加载成功")
else:
    print("❌ 未找到 .env 文件，将尝试使用系统环境变量")

# 2. 获取 API Key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ 错误: 未读取到 OPENAI_API_KEY，请检查 .env 文件内容或格式。")
    exit(1)
else:
    # 为了安全，只打印前几位和最后几位
    masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"✅ 读取到 API Key: {masked_key}")

# 3. 尝试调用 API
print("\n正在尝试连接 OpenAI API...")
try:
    client = OpenAI(api_key=api_key)
    
    # 根据你的 .env 配置，如果设置了 BASE_URL 也需要传递
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        print(f"ℹ️ 使用自定义 Base URL: {base_url}")
        client.base_url = base_url

    response = client.chat.completions.create(
        model="moonshot-v1-8k", # 使用最便宜的模型测试连通性
        messages=[
            {"role": "user", "content": "Hello, simply reply with 'API is working!'"}
        ],
        max_tokens=20
    )
    
    result = response.choices[0].message.content
    print(f"✅ API 连接成功! 模型回复: {result}")

except Exception as e:
    print(f"❌ API 调用失败: {e}")
    print("请检查你的 Key 余额、网络连接（是否需要代理）或 Base URL 配置。")
