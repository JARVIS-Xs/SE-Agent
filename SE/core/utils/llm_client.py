#!/usr/bin/env python3
"""
LLM客户端模块
为SE框架提供统一的LLM调用接口
"""

from openai import OpenAI
from typing import Dict, Any, Optional, List
from core.utils.se_logger import get_se_logger


class LLMClient:
    """LLM客户端，支持多种模型和API端点"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            model_config: 模型配置字典，包含name, api_base, api_key等
        """
        self.config = model_config
        self.logger = get_se_logger("llm_client", emoji="🤖")
        
        # 验证必需的配置参数
        required_keys = ["name", "api_base", "api_key"]
        missing_keys = [key for key in required_keys if key not in model_config]
        if missing_keys:
            raise ValueError(f"缺少必需的配置参数: {missing_keys}")
        
        # 初始化OpenAI客户端，遵循api_test.py的工作模式
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["api_base"],
        )
        
        self.logger.info(f"初始化LLM客户端: {self.config['name']}")
    
    def call_llm(self, messages: List[Dict[str, str]], 
                 temperature: float = 0.3, 
                 max_tokens: Optional[int] = None) -> str:
        """
        调用LLM并返回响应内容
        
        Args:
            messages: 消息列表，每个消息包含role和content
            temperature: 温度参数，控制输出随机性
            max_tokens: 最大输出token数，None表示使用配置默认值
            
        Returns:
            LLM响应的文本内容
            
        Raises:
            Exception: LLM调用失败时抛出异常
        """
        try:
            # 使用配置中的max_output_tokens作为默认值
            if max_tokens is None:
                max_tokens = self.config.get("max_output_tokens", 4000)
            
            self.logger.debug(f"调用LLM: {len(messages)} 条消息, temp={temperature}, max_tokens={max_tokens}")
            
            # 使用基本的OpenAI客户端调用，遵循api_test.py的工作模式
            # 不使用额外参数，避免服务器错误
            response = self.client.chat.completions.create(
                model=self.config["name"],
                messages=messages,
                temperature=temperature,
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            
            # 记录使用情况
            if response.usage:
                self.logger.debug(f"Token使用: 输入={response.usage.prompt_tokens}, "
                                f"输出={response.usage.completion_tokens}, "
                                f"总计={response.usage.total_tokens}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            raise
    
    def call_with_system_prompt(self, system_prompt: str, user_prompt: str, 
                               temperature: float = 0.3, 
                               max_tokens: Optional[int] = None) -> str:
        """
        使用系统提示词和用户提示词调用LLM
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大输出token数
            
        Returns:
            LLM响应的文本内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.call_llm(messages, temperature, max_tokens)
    
    @classmethod
    def from_se_config(cls, se_config: Dict[str, Any], use_operator_model: bool = False) -> "LLMClient":
        """
        从SE框架配置创建LLM客户端
        
        Args:
            se_config: SE框架配置字典
            use_operator_model: 是否使用operator_models配置而不是主模型配置
            
        Returns:
            LLM客户端实例
        """
        if use_operator_model and "operator_models" in se_config:
            model_config = se_config["operator_models"]
        else:
            model_config = se_config["model"]
        
        return cls(model_config)


class TrajectorySummarizer:
    """专门用于轨迹总结的LLM客户端包装器"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化轨迹总结器
        
        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        self.logger = get_se_logger("traj_summarizer", emoji="📊")
    
    def summarize_trajectory(self, trajectory_content: str, patch_content: str, 
                           iteration: int) -> Dict[str, Any]:
        """
        使用LLM总结轨迹内容
        
        Args:
            trajectory_content: .tra文件内容
            patch_content: .patch/.pred文件内容 (预测结果)
            iteration: 迭代次数
            
        Returns:
            轨迹总结字典
        """
        from .traj_summarizer import TrajSummarizer
        
        summarizer = TrajSummarizer()
        
        try:
            # 获取提示词
            system_prompt = summarizer.get_system_prompt()
            user_prompt = summarizer.format_user_prompt(trajectory_content, patch_content)
            
            self.logger.info(f"开始LLM轨迹总结 (迭代{iteration})")
            
            # 调用LLM
            response = self.llm_client.call_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # 解析响应
            summary = summarizer.parse_response(response)
            
            # 验证响应格式
            if summarizer.validate_response_format(summary):
                self.logger.info(f"LLM轨迹总结成功 (迭代{iteration})")
                return summary
            else:
                self.logger.warning(f"LLM响应格式不符合预期，使用备用总结 (迭代{iteration})")
                return summarizer.create_fallback_summary(trajectory_content, patch_content, iteration)
                
        except Exception as e:
            self.logger.error(f"LLM轨迹总结失败: {e}")
            # 返回备用总结
            return summarizer.create_fallback_summary(trajectory_content, patch_content, iteration)