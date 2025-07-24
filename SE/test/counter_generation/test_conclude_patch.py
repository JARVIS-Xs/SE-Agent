#!/usr/bin/env python
"""
测试conclude_patch.py中的Claude API请求功能
"""

import os
import sys
import json
from pathlib import Path
import pytest

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
# 确保能导入claude模块
sys.path.insert(0, str(current_dir))

# 导入要测试的模块
from conclude_patch import (
    analyze_patch_with_claude,
    ClaudeAPI,
    extract_content,
    load_filtered_predictions,
    save_predictions
)

def test_claude_api_request_simple():
    """
    简单测试Claude API请求功能，不验证详细字段，只验证能否成功连接
    """
    # 测试用的Claude API密钥
    test_api_key = "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"
    
    # 创建Claude API客户端
    claude_api = ClaudeAPI(test_api_key)
    
    # 发送简单请求
    response = claude_api.send_message(
        message="Hello, Claude! Please respond with a simple JSON: {\"test\": \"success\"}",
        model="claude-3-7-sonnet-20250219",
        temperature=0.3,
        max_tokens=100
    )
    
    # 验证是否收到响应
    assert response is not None, "未收到API响应"
    assert "content" in response, "响应格式错误"
    
    # 提取内容
    content = extract_content(response)
    print(f"API响应内容: {content[:100]}...")
    
    # 验证内容中是否包含"success"
    assert "success" in content.lower(), "响应内容不符合预期"
    
    print("Claude API连接测试成功!")

def test_claude_analysis_function():
    """
    测试analyze_patch_with_claude函数的基本功能
    """
    # 测试用的Claude API密钥
    test_api_key = "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"
    
    # 创建Claude API客户端
    claude_api = ClaudeAPI(test_api_key)
    
    # 测试用的数据
    test_problem = """
    Issue: The function `calculate_sum` does not handle negative numbers correctly.
    Expected behavior: The function should return the sum of all numbers, including negative ones.
    """
    
    test_patch = """
    def calculate_sum(numbers):
        return sum([n for n in numbers if n > 0])  # 只计算正数
    """
    
    test_instance_id = "test_instance_001"
    
    # 调用分析函数
    result = analyze_patch_with_claude(
        problem_statement=test_problem,
        model_patch=test_patch,
        instance_id=test_instance_id,
        claude_api=claude_api
    )
    
    # 只验证基本结构，不检查具体字段
    assert isinstance(result, dict), "返回结果应该是字典类型"
    print(f"分析结果包含的字段: {list(result.keys())}")
    
    # 至少应该有一些字段
    assert len(result) > 0, "返回结果为空字典"
    
    # 检查是否存在错误
    assert "error" not in result, f"API请求失败: {result.get('error', '')}"
    
    print("Claude分析函数测试成功!")

def test_claude_api_integration():
    """
    测试Claude API与文件处理的集成
    
    这个测试会：
    1. 创建一个测试用的conclusion.json文件
    2. 使用Claude API分析补丁
    3. 验证结果是否正确保存到文件中
    """
    # 测试用的Claude API密钥
    test_api_key = "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"
    
    # 创建Claude API客户端
    claude_api = ClaudeAPI(test_api_key)
    
    # 创建测试用的conclusion.json文件
    test_data = {
        "test_instance_001": {
            "problem_statement": "Issue: The function `calculate_sum` does not handle negative numbers correctly.",
            "model_patch": "def calculate_sum(numbers):\n    return sum([n for n in numbers if n > 0])  # 只计算正数"
        }
    }
    
    # 保存测试数据
    test_file = "test_conclusion.json"
    save_predictions(test_data, test_file)
    
    try:
        # 加载测试数据
        predictions = load_filtered_predictions(test_file)
        
        # 处理测试数据
        instance_id = "test_instance_001"
        instance_data = predictions[instance_id]
        
        # 调用分析函数
        analysis = analyze_patch_with_claude(
            problem_statement=instance_data["problem_statement"],
            model_patch=instance_data["model_patch"],
            instance_id=instance_id,
            claude_api=claude_api
        )
        
        # 将分析结果添加到数据中
        predictions[instance_id]["claude_analysis"] = analysis
        
        # 保存更新后的数据
        save_predictions(predictions, test_file)
        
        # 验证文件是否正确更新
        updated_predictions = load_filtered_predictions(test_file)
        assert "claude_analysis" in updated_predictions[instance_id], "分析结果未正确保存到文件中"
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            
    print("Claude API与文件处理集成测试成功!")

if __name__ == "__main__":
    test_claude_api_request_simple()
    test_claude_analysis_function()
    test_claude_api_integration()
    print("所有测试通过!") 