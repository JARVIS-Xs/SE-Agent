#!/usr/bin/env python
"""
测试JSON提取功能
"""

import sys
import json
from pathlib import Path
import re

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
# 确保能导入claude模块
sys.path.insert(0, str(current_dir))

# 导入要测试的API
from claude import ClaudeAPI, extract_content

def test_json_extraction():
    """测试从Claude API响应中提取JSON内容"""
    
    # 模拟Claude API响应中的JSON代码块格式
    sample_response_with_code_block = {
        "id": "msg_01NLR3UDjC4qWJVnYBC4bK1v",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-7-sonnet-20250219",
        "content": [
            {
                "type": "text",
                "text": "```json\n{\n  \"approach_summary\": \"初始化变量\",\n  \"modified_files\": [\"file1.py\", \"file2.py\"],\n  \"key_changes\": \"添加了初始化代码\"\n}\n```"
            }
        ],
        "stop_reason": "end_turn"
    }
    
    # 模拟纯JSON格式的响应
    sample_response_pure_json = {
        "id": "msg_01NLR3UDjC4qWJVnYBC4bK1v",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-7-sonnet-20250219",
        "content": [
            {
                "type": "text",
                "text": "{\"approach_summary\": \"初始化变量\", \"modified_files\": [\"file1.py\", \"file2.py\"], \"key_changes\": \"添加了初始化代码\"}"
            }
        ],
        "stop_reason": "end_turn"
    }
    
    # 测试从代码块中提取JSON
    print("测试从代码块中提取JSON:")
    content = extract_content(sample_response_with_code_block)
    print(f"提取的内容: {content}")
    
    # 尝试提取JSON
    json_pattern = r"```json\s*([\s\S]*?)\s*```"
    json_match = re.search(json_pattern, content)
    
    if json_match:
        json_content = json_match.group(1)
        parsed_json = json.loads(json_content)
        print(f"解析的JSON: {parsed_json}")
    else:
        print("未找到JSON代码块")
        
        # 尝试提取一般JSON
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = content[start_idx:end_idx]
            parsed_json = json.loads(json_content)
            print(f"解析的一般JSON: {parsed_json}")
        else:
            print("未找到JSON内容")
    
    # 测试从纯文本中提取JSON
    print("\n测试从纯文本中提取JSON:")
    content = extract_content(sample_response_pure_json)
    print(f"提取的内容: {content}")
    
    # 尝试提取JSON
    json_pattern = r"```json\s*([\s\S]*?)\s*```"
    json_match = re.search(json_pattern, content)
    
    if json_match:
        json_content = json_match.group(1)
        parsed_json = json.loads(json_content)
        print(f"解析的JSON: {parsed_json}")
    else:
        print("未找到JSON代码块")
        
        # 尝试提取一般JSON
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = content[start_idx:end_idx]
            parsed_json = json.loads(json_content)
            print(f"解析的一般JSON: {parsed_json}")
        else:
            print("未找到JSON内容")
            
if __name__ == "__main__":
    test_json_extraction() 