#!/usr/bin/env python3
"""
最简单的LiteLLM测试 - 发送"你好"并打印响应
"""

import litellm

def test_simple_litellm():
    """测试LiteLLM基本调用"""
    print("开始LiteLLM测试...")
    
    # 配置参数
    model_name = "openai/deepseek-chat"
    api_base = "http://publicshare.a.pinggy.link"
    api_key = "EMPTY"
    
    print(f"使用模型: {model_name}")
    print(f"API端点: {api_base}")
    
    # 构建消息
    messages = [
        {"role": "user", "content": "你好"}
    ]
    
    try:
        print("正在调用LiteLLM...")
        
        # 调用LiteLLM
        response = litellm.completion(
            model=model_name,
            messages=messages,
            api_base=api_base,
            api_key=api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        print("\n=== 响应结果 ===")
        print(f"模型: {response.model}")
        print(f"内容: {response.choices[0].message.content}")
        print(f"使用的tokens: {response.usage.total_tokens if response.usage else '未知'}")        
    except Exception as e:
        print(f"调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    test_simple_litellm()