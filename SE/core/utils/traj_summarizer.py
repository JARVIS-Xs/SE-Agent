#!/usr/bin/env python3
"""
轨迹总结器
为trajectory pool生成轨迹总结的专用prompt系统
"""

import json
from typing import Dict, Any, Optional
from core.utils.se_logger import get_se_logger


class TrajSummarizer:
    """轨迹总结器，生成轨迹分析prompt并解析响应"""
    
    def __init__(self):
        self.logger = get_se_logger("traj_summarizer", emoji="📊")
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词字符串
        """
        return """You are an AI assistant specialized in analyzing software engineering trajectories. Your task is to analyze execution trajectories from SWE-agent runs and provide structured insights about the solution approach.

You will be provided with:
1. A trajectory file (.tra) in JSON format containing the agent's step-by-step execution
2. A prediction file (.pred) containing the final result

Your goal is to extract and summarize the core solution strategy, techniques, and approaches used in this trajectory.

Return your analysis in JSON format with the following fields:
- approach_summary: A concise summary of the main approach used in this solution
- modified_files: List of files that were modified during execution  
- key_changes: Description of the most important code changes made
- strategy: The core solution strategy at an abstract level
- specific_techniques: Specific techniques or methods used in this solution
- tools_used: Tools and commands heavily utilized during execution
- reasoning_pattern: The problem-solving pattern observed in the trajectory
- assumptions_made: Key assumptions made during the solution process
- components_touched: Main components, functions, or modules that were modified

Focus on extracting actionable insights about the solution methodology rather than implementation details."""

    def get_user_prompt_template(self) -> str:
        """
        获取用户提示词模板
        
        Returns:
            用户提示词模板字符串
        """
        return """Please analyze the following SWE-agent trajectory and provide insights about the solution approach.

Trajectory Data (.tra file):
{trajectory_content}

Prediction Result (.patch/.pred file):
{patch_content}

Please provide your analysis in the JSON format specified in the system prompt."""

    def format_user_prompt(self, trajectory_content: str, patch_content: str) -> str:
        """
        格式化用户提示词
        
        Args:
            trajectory_content: 轨迹文件内容
            patch_content: 预测文件内容 (.patch/.pred)
            
        Returns:
            格式化后的用户提示词
        """
        template = self.get_user_prompt_template()
        return template.format(
            trajectory_content=trajectory_content,
            patch_content=patch_content
        )
    
    def parse_response(self, response_content: str) -> Dict[str, Any]:
        """
        解析LLM响应内容
        
        Args:
            response_content: LLM响应的原始内容
            
        Returns:
            解析后的JSON数据，如果解析失败返回错误信息
        """
        try:
            # 尝试直接解析JSON
            if response_content.strip().startswith('{'):
                return json.loads(response_content.strip())
            
            # 如果不是直接的JSON，尝试提取JSON部分
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_content = response_content[start_idx:end_idx]
                return json.loads(json_content)
            else:
                self.logger.warning("无法在响应中找到JSON格式内容")
                return {
                    "error": "无法解析JSON",
                    "raw_content": response_content[:500] + "..." if len(response_content) > 500 else response_content
                }
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return {
                "error": "JSON解析错误", 
                "details": str(e),
                "raw_content": response_content[:500] + "..." if len(response_content) > 500 else response_content
            }
    
    def validate_response_format(self, response_data: Dict[str, Any]) -> bool:
        """
        验证响应格式是否符合预期
        
        Args:
            response_data: 解析后的响应数据
            
        Returns:
            是否符合预期格式
        """
        required_fields = [
            "approach_summary",
            "modified_files", 
            "key_changes",
            "strategy",
            "specific_techniques",
            "tools_used",
            "reasoning_pattern",
            "assumptions_made",
            "components_touched"
        ]
        
        # 检查是否有错误字段
        if "error" in response_data:
            return False
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in response_data]
        if missing_fields:
            self.logger.warning(f"响应缺少必需字段: {missing_fields}")
            return False
        
        return True
    
    def create_fallback_summary(self, trajectory_content: str, patch_content: str, iteration: int) -> Dict[str, Any]:
        """
        创建备用总结（当LLM调用失败时使用）
        
        Args:
            trajectory_content: 轨迹内容
            patch_content: 预测内容 (.patch/.pred)
            iteration: 迭代次数
            
        Returns:
            备用总结数据
        """
        # 简单的备用分析
        trajectory_length = len(trajectory_content.split('\n')) if trajectory_content else 0
        patch_length = len(patch_content) if patch_content else 0
        
        return {
            "approach_summary": f"Iteration {iteration} execution with {trajectory_length} trajectory steps",
            "modified_files": ["unknown"],
            "key_changes": "Unable to analyze - LLM summarization failed",
            "strategy": f"iteration_{iteration}_strategy",
            "specific_techniques": ["automated_execution"],
            "tools_used": ["swe_agent"],
            "reasoning_pattern": "step_by_step_execution", 
            "assumptions_made": ["standard_swe_agent_assumptions"],
            "components_touched": ["unknown_components"],
            "meta": {
                "is_fallback": True,
                "trajectory_length": trajectory_length,
                "patch_length": patch_length,
                "iteration": iteration
            }
        }