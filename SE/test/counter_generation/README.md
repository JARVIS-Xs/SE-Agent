# Claude API 客户端工具

这个工具包提供了一系列Python模块，用于简化与Claude AI API的交互。支持基本消息发送、多轮对话、流式响应以及代码生成和解释等功能。

## 功能特点

- 简单易用的API封装
- 支持单轮和多轮对话
- 支持流式响应
- 提供代码解释和生成功能
- 完整的类型提示和文档

## 文件说明

- `claude.py` - 核心API客户端模块
- `claude_api_test.py` - 基本连接测试
- `claude_stream.py` - 流式响应示例
- `claude_example.py` - 代码解释和生成示例

## 安装依赖

```bash
pip install requests
```

## 使用示例

### 基本用法

```python
from claude import ClaudeAPI, extract_content

# 创建客户端实例
api_key = "您的API密钥"
client = ClaudeAPI(api_key)

# 发送消息
response = client.send_message("你好，请介绍一下自己")
content = extract_content(response)
print(content)
```

### 多轮对话

```python
# 创建多轮对话
messages = [
    {"role": "user", "content": "什么是机器学习？"},
    {"role": "assistant", "content": "机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习和改进，而无需显式编程。"},
    {"role": "user", "content": "请给我举一个实际应用的例子"}
]

response = client.chat_completion(messages)
print(extract_content(response))
```

### 流式响应

```python
# 获取流式响应
response = client.chat_completion(
    messages=[{"role": "user", "content": "请写一篇短文"}],
    stream=True
)

# 处理流式响应
for chunk in client.stream_response(response):
    print(chunk, end='', flush=True)
```

### 代码工具

```bash
# 解释代码文件
python claude_example.py explain --file example.py

# 生成代码
python claude_example.py generate --description "一个HTTP服务器" --output server.py
```

## 环境变量

你可以设置`CLAUDE_API_KEY`环境变量来避免每次都需要手动传入API密钥：

```bash
export CLAUDE_API_KEY="您的API密钥"
```

## 配置选项

核心API方法支持多种参数配置：

- `model` - 模型名称，默认为"claude-3-sonnet-20240229"
- `temperature` - 温度参数，控制输出随机性
- `max_tokens` - 最大生成令牌数
- `top_p` - 控制输出多样性
- `stop` - 停止生成的序列
- `stream` - 是否使用流式响应

## 注意事项

- 请妥善保管你的API密钥
- 考虑为高频率使用设置适当的速率限制
- 检查你的API使用配额和限制 