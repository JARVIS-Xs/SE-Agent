#!/usr/bin/env python3

"""
Trajectory Analyzer Operator

直接分析 .tra 轨迹文件，提取详细的问题陈述和轨迹数据，
生成基于完整轨迹内容的解决策略。
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from operators import TemplateOperator


class TrajectoryAnalyzerOperator(TemplateOperator):
    """轨迹分析算子，直接分析 .tra 文件生成详细策略"""
    
    def get_name(self) -> str:
        return "trajectory_analyzer"
    
    def get_strategy_prefix(self) -> str:
        return "SOLUTION STRATEGY"
    
    def _extract_detailed_problem_statement(self, trajectory_data: Dict[str, Any]) -> str:
        """从轨迹数据中提取详细的问题陈述"""
        try:
            trajectory = trajectory_data.get('Trajectory', [])
            if len(trajectory) >= 2:
                user_item = trajectory[1]  # 第二项（索引1）
                if user_item.get('role') == 'user' and 'content' in user_item:
                    content = user_item['content']
                    
                    # 提取文本内容
                    if isinstance(content, list) and len(content) > 0:
                        text = content[0].get('text', '')
                    elif isinstance(content, str):
                        text = content
                    else:
                        return ""
                    
                    # 提取<pr_description>标签内的内容
                    match = re.search(r'<pr_description>\s*(.*?)\s*</pr_description>', text, re.DOTALL)
                    if match:
                        return match.group(1).strip()
            return ""
        except Exception as e:
            self.logger.error(f"提取问题陈述失败: {e}")
            return ""
    
    def _extract_trajectory_analysis(self, trajectory_data: Dict[str, Any]) -> str:
        """提取轨迹分析信息"""
        try:
            trajectory = trajectory_data.get('Trajectory', [])
            
            # 统计轨迹信息
            total_steps = len(trajectory)
            assistant_steps = len([item for item in trajectory if item.get('role') == 'assistant'])
            user_steps = len([item for item in trajectory if item.get('role') == 'user'])
            
            # 提取最后几个助手响应
            assistant_responses = []
            for item in reversed(trajectory):
                if item.get('role') == 'assistant' and len(assistant_responses) < 3:
                    content = item.get('content', '')
                    if isinstance(content, list) and len(content) > 0:
                        text = content[0].get('text', '')
                    elif isinstance(content, str):
                        text = content
                    else:
                        continue
                    
                    # 截取前200字符
                    assistant_responses.append(text[:200] + "..." if len(text) > 200 else text)
            
            # 检查是否有工具使用
            has_tools = any('function_call' in str(item) or 'tool_calls' in str(item) for item in trajectory)
            
            analysis = f"""轨迹统计:
- 总步数: {total_steps}
- 助手响应: {assistant_steps}
- 用户输入: {user_steps}
- 工具使用: {'是' if has_tools else '否'}

最近的助手响应:
{chr(10).join(f'{i+1}. {resp}' for i, resp in enumerate(assistant_responses))}"""
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"提取轨迹分析失败: {e}")
            return ""
    
    def _generate_solution_strategy(self, problem_statement: str, trajectory_analysis: str, instance_name: str) -> str:
        """生成解决策略"""
        
        system_prompt = """You are an expert software engineering strategy consultant specializing in innovative problem-solving. Your task is to generate radically divergent problem-solving approaches for software engineering tasks, drawing from diverse methodologies across fields like reverse engineering, data-driven analysis, simulation-based testing, or interdisciplinary techniques borrowed from domains such as systems biology or game theory.

You will be given a problem and trajectory analysis from a previous attempt. Your job is to create a fundamentally different strategy that:
1. Leverages entirely novel investigation paradigms, such as starting from end-user impact analysis or component isolation experiments
2. Approaches the problem from an unconventional angle, like focusing on runtime behavior tracing instead of static code review
3. Incorporates alternative tools, techniques, or conceptual frameworks, such as visualization tools for data flow or probabilistic modeling for error prediction
4. Establishes a distinct logical progression, perhaps iterative prototyping over linear debugging

CRITICAL: Your strategy must be architecturally dissimilar to avoid the same limitations and blind spots.

Respond with a high-level conceptual strategy that outlines key actionable steps. Emphasize the COGNITIVE FRAMEWORK rather than granular code specifics.

IMPORTANT: 
- Respond ONLY with plain text without markdown formatting
- Do NOT use bullet points, headers, or special formatting
- Do NOT use any tools, commands, or function calls
- Provide ONLY the text content of the strategy
- Your response should be a cohesive strategic narrative in paragraph form"""
        
        prompt = f"""Generate a radically divergent solution strategy for this software engineering problem:

PROBLEM:
{problem_statement}

TRAJECTORY ANALYSIS:
{trajectory_analysis}

Requirements for the solution strategy:
1. Adopt a profoundly different investigation paradigm, such as empirical experimentation or holistic system modeling
2. Initiate from an alternative entry point (e.g., examining dependencies externally or simulating environmental factors)
3. Pursue a non-linear or inverted logical sequence, like working backwards from symptoms to causes
4. Integrate unconventional debugging/analysis techniques, such as fuzzing, profiling, or comparative benchmarking
5. Prioritize overlooked aspects, like performance metrics, edge-case simulations, or cross-version diffs
6. Incorporate diverse tools and commands, potentially from outside the standard toolkit, where feasible

The strategy should be conceptual yet executable - articulate the reasoning paradigm and pivotal strategic phases that would enable an agent to tackle this problem via an entirely novel trajectory.

Elaborate on WHY this approach diverges significantly and HOW it circumvents the shortcomings of the previous effort, potentially by introducing variability in assumptions or exploring parallel hypotheses.

Craft a strategy that empowers an AI agent to reconceptualize the problem from ground zero with an innovative methodology, fostering breakthrough potential."""
        
        return self._call_llm_api(prompt, system_prompt)
    
    def _generate_content(self, instance_info: Dict[str, Any], problem_statement: str, trajectory_data: Dict[str, Any]) -> str:
        """生成轨迹分析策略内容"""
        instance_name = instance_info['instance_name']
        
        # 提取详细的问题陈述
        detailed_problem = self._extract_detailed_problem_statement(trajectory_data)
        if not detailed_problem:
            detailed_problem = problem_statement
        
        # 提取轨迹分析
        trajectory_analysis = self._extract_trajectory_analysis(trajectory_data)
        
        self.logger.info(f"分析 {instance_name}: 基于完整轨迹数据生成策略")
        
        # 生成解决策略
        strategy = self._generate_solution_strategy(detailed_problem, trajectory_analysis, instance_name)
        
        if not strategy:
            # 如果LLM调用失败，提供默认策略
            strategy = f"""Adopt a systematic approach that begins with comprehensive problem space mapping rather than immediate code investigation. Start by establishing clear success criteria and testing boundaries, then proceed through iterative hypothesis formation and validation cycles. Focus on understanding the system's behavioral patterns through runtime observation and incremental experimentation rather than static analysis. This methodology emphasizes empirical validation over theoretical assumptions, allowing for rapid course correction when approaches prove ineffective. The strategy prioritizes building a robust mental model of the system's actual behavior before attempting modifications, ensuring that solutions address root causes rather than symptoms."""
        
        return strategy


# 注册算子
from operators import register_operator
register_operator("trajectory_analyzer", TrajectoryAnalyzerOperator)