from openai import OpenAI
import requests

"""
API测试脚本 - 已修复版本

注意：经测试发现，基本请求可以工作，但是额外参数（如chat_template_kwargs）
会导致服务器错误："name 'base_url' is not defined"
"""

# API配置
openai_api_key = "EMPTY"
openai_api_base = "http://publicshare.a.pinggy.link"

# 测试API连接
print("测试API基本连接...")
try:
    response = requests.get(openai_api_base)
    print(f"API端点状态: {response.status_code}")
    print(f"响应内容: {response.text[:100]}...")  # 只打印前100个字符
except Exception as e:
    print(f"连接API端点失败: {e}")

# 初始化客户端
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# 尝试基本API请求（可行方式）
try:
    print("\n尝试基本API请求...")
    chat_response = client.chat.completions.create(
        model="openai/deepseek-chat",
        messages=[
            {"role": "user", "content": "Who you are?"}
        ],
        temperature=0.6,
    )
    print("响应成功!")
    print(f"模型: {chat_response.model}")
    print(f"内容: {chat_response.choices[0].message.content}")
    print(f"使用的tokens: {chat_response.usage.total_tokens}")
except Exception as e:
    print(f"请求失败: {e}")

# 注意：下面的请求会导致服务器错误，因此被注释掉
"""
try:
    print("\n尝试带额外参数的请求（可能会失败）...")
    chat_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "Who you are?"},
        ],
        temperature=0.6,
        top_p=0.95,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True},  # 这个参数会导致服务器错误
        }, 
    )
    print("响应成功:", chat_response)
except Exception as e:
    print(f"预期中的错误: {e}")
"""