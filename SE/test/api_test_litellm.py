#!/usr/bin/env python3
"""
使用LiteLLM测试deepseek模型连接
"""

import litellm
import requests

# 测试API连接
API_BASE = "http://publicshare.a.pinggy.link"
API_KEY = "EMPTY"  # 使用与原始测试相同的密钥

def test_api_endpoint():
    """测试API端点连接"""
    print("测试API端点连接...")
    try:
        response = requests.get(API_BASE)
        print(f"API端点状态: {response.status_code}")
        print(f"响应内容: {response.text[:100]}...")  # 只打印前100个字符
    except Exception as e:
        print(f"连接API端点失败: {e}")

def test_different_providers():
    """尝试不同的提供者前缀"""
    # 尝试不同的提供者前缀
    providers = [
        "vllm/deepseek-chat",
        "openai/deepseek-chat",
        "deepseek-chat",
        "custom/deepseek-chat",
        "deepseek/deepseek-chat"
    ]
    
    for model_name in providers:
        print(f"\n尝试模型名: {model_name}")
        try:
            # 最简单的请求
            response = litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                api_base=API_BASE,
                api_key=API_KEY,
                max_tokens=10  # 限制响应长度以加快测试速度
            )
            
            print("✓ 成功!")
            print(f"模型: {response.model}")
            print(f"内容: {response.choices[0].message.content}")
            return model_name  # 返回有效的模型名称
        
        except Exception as e:
            print(f"✗ 失败: {e}")
    
    return None  # 所有尝试均失败

def try_custom_completion_with_provider(working_model=None):
    """使用定制参数测试completion"""
    model_name = working_model or "custom/deepseek-chat"
    print(f"\n使用模型 {model_name} 尝试定制参数...")
    
    try:
        # 添加litellm的调试模式
        litellm.set_verbose = True
        
        print("正在调用LiteLLM...")
        response = litellm.completion(
            model=model_name,
            messages=[{"role": "user", "content": "Who are you?"}],
            api_base=API_BASE,
            api_key=API_KEY,
            temperature=0.6,
        )
        
        print("\n=== 响应结果 ===")
        print(f"模型: {response.model}")
        print(f"内容: {response.choices[0].message.content}")
        print(f"使用的tokens: {response.usage.total_tokens if response.usage else '未知'}")
        
    except Exception as e:
        print(f"调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")

if __name__ == "__main__":
    # 首先测试API端点连接
    test_api_endpoint()
    
    # 然后尝试不同提供者
    working_model = test_different_providers()
    
    # 如果找到有效模型名称，尝试使用它
    try_custom_completion_with_provider(working_model) 