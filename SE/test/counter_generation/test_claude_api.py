#!/usr/bin/env python
"""
测试增强后的Claude API客户端
"""

import sys
import json
from pathlib import Path

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
# 确保能导入claude模块
sys.path.insert(0, str(current_dir))

# 导入要测试的API
from claude import ClaudeAPI, extract_content

def test_claude_api_with_retry():
    """测试带有重试机制的Claude API客户端"""
    
    # 测试用的Claude API密钥
    test_api_key = "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"
    
    # 创建Claude API客户端
    print("初始化Claude API客户端...")
    claude_api = ClaudeAPI(test_api_key)
    
    # 测试简单请求
    print("\n发送简单请求以测试连接...")
    message = "Hello, please respond with a very short greeting."
    
    try:
        # 使用更短的超时和更多重试次数进行测试
        response = claude_api.send_message(
            message=message,
            model="claude-3-7-sonnet-20250219",
            temperature=0.7,
            max_tokens=100,
            max_retries=3,
            timeout=30
        )
        
        # 检查是否有错误
        if "error" in response:
            print(f"请求返回错误: {response['error']}")
            return False
        
        # 提取内容
        content = extract_content(response)
        print(f"响应内容: {content}")
        
        print("API请求成功!")
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_claude_api_with_retry()
    if success:
        print("\n✅ 测试通过: API工作正常")
    else:
        print("\n❌ 测试失败: API连接问题") 