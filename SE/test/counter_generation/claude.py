#!/usr/bin/env python
"""
Claude API客户端
提供与Anthropic Claude API交互的简单接口
使用官方anthropic Python库
"""

import json
import time
from typing import Dict, Any, List, Optional, Union

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("警告: 未找到anthropic库，请使用 pip install anthropic 进行安装")

class ClaudeAPI:
    """Claude API客户端类"""
    
    def __init__(self, api_key: str):
        """
        初始化Claude API客户端
        
        Args:
            api_key: Claude API密钥
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("未安装anthropic库。请使用 pip install anthropic 安装")
            
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
    
    def send_message(
        self, 
        message: str, 
        model: str = "claude-3-7-sonnet-20250219",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None,
        max_retries: int = 3,  # 额外的应用层重试
        timeout: int = 60  # 超时设置，单位秒
    ) -> Dict[str, Any]:
        """
        发送消息到Claude API
        
        Args:
            message: 用户消息内容
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大生成的token数
            system: 系统提示
            max_retries: 额外重试次数
            timeout: 请求超时时间(秒)
            
        Returns:
            API响应
        """
        # 使用应用层重试机制
        for attempt in range(max_retries + 1):
            try:
                kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                }
                
                if system:
                    kwargs["system"] = system
                
                # 调用Anthropic客户端
                message_response = self.client.messages.create(**kwargs, timeout=timeout)
                
                # 转换为统一格式
                return {
                    "id": message_response.id,
                    "model": message_response.model,
                    "content": message_response.content
                }
            
            except Exception as e:
                print(f"API请求失败 (尝试 {attempt+1}/{max_retries+1}): {e}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    return {"error": str(e)}

def extract_content(response: Dict[str, Any]) -> str:
    """
    从Claude API响应中提取文本内容
    
    Args:
        response: Claude API响应
        
    Returns:
        提取的文本内容
    """
    if "error" in response:
        return f"错误: {response['error']}"
    
    if "content" not in response:
        return "错误: 响应中未找到content字段"
    
    content_blocks = response["content"]
    
    if not content_blocks:
        return ""
    
    # 处理内容块
    extracted_text = ""
    for block in content_blocks:
        # 如果是TextBlock对象（anthropic库的响应格式）
        if hasattr(block, 'text'):
            extracted_text += block.text
        # 如果是字典（我们自己转换的格式）
        elif isinstance(block, dict) and block.get("type") == "text":
            extracted_text += block.get("text", "")
    
    return extracted_text
