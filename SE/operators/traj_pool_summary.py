#!/usr/bin/env python3

"""
Trajectory Pool Summary Operator

分析轨迹池中的历史失败尝试，识别常见盲区和风险点，
生成简洁的风险感知解决指导。
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from operators import TemplateOperator


class TrajPoolSummaryOperator(TemplateOperator):
    """轨迹池总结算子，生成风险感知的问题解决指导"""
    
    def get_name(self) -> str:
        return "traj_pool_summary"
    
    def get_strategy_prefix(self) -> str:
        return "RISK-AWARE PROBLEM SOLVING GUIDANCE"
    
    def _discover_instances(self, workspace_dir: Path, current_iteration: int) -> List[Dict[str, Any]]:
        """
        重写实例发现逻辑，直接查找工作目录中的traj.pool文件
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号
            
        Returns:
            实例信息列表
        """
        instances = []
        
        # 直接在工作目录中查找traj.pool文件
        traj_pool_file = workspace_dir / "traj.pool"
        if not traj_pool_file.exists():
            self.logger.warning(f"traj.pool文件不存在: {traj_pool_file}")
            return instances
        
        # 加载traj.pool数据
        try:
            with open(traj_pool_file, 'r', encoding='utf-8') as f:
                pool_data = json.load(f)
        except Exception as e:
            self.logger.error(f"加载traj.pool失败 {traj_pool_file}: {e}")
            return instances
        
        # 为每个实例创建实例信息
        for instance_name, instance_data in pool_data.items():
            if isinstance(instance_data, dict) and len(instance_data) > 0:
                # 检查是否有数字键（迭代数据）
                has_iteration_data = any(key.isdigit() for key in instance_data.keys())
                if has_iteration_data:
                    instances.append({
                        'instance_name': instance_name,
                        'instance_dir': workspace_dir,  # 使用工作目录作为实例目录
                        'trajectory_file': traj_pool_file,  # 使用traj.pool文件
                        'previous_iteration': current_iteration - 1,
                        'pool_data': instance_data  # 附加池数据
                    })
        
        self.logger.info(f"发现 {len(instances)} 个可处理的实例")
        return instances
    
    def _extract_problem_statement(self, trajectory_data: Dict[str, Any]) -> str:
        """
        重写问题陈述提取，返回占位符
        因为我们在_generate_content中直接使用pool_data中的问题陈述
        """
        return "placeholder"
    
    def _load_traj_pool(self, instance_dir: Path) -> Dict[str, Any]:
        """加载轨迹池数据 - 适配SE框架的traj.pool格式"""
        traj_pool_file = instance_dir / "traj.pool"
        
        if not traj_pool_file.exists():
            self.logger.warning(f"traj.pool文件不存在: {traj_pool_file}")
            return {}
        
        try:
            with open(traj_pool_file, 'r', encoding='utf-8') as f:
                pool_data = json.load(f)
            
            # SE框架的traj.pool格式: {instance_name: {problem: str, "1": {data}, "2": {data}}}
            # 提取第一个实例的数据
            for instance_name, instance_data in pool_data.items():
                if isinstance(instance_data, dict):
                    return instance_data
            
            return {}
            
        except Exception as e:
            self.logger.error(f"加载traj.pool失败 {traj_pool_file}: {e}")
            return {}
    
    def _format_approaches_data(self, approaches_data: Dict[str, Any]) -> str:
        """格式化历史尝试数据为简洁文本"""
        formatted_text = ""
        
        for key, data in approaches_data.items():
            if key == "problem":
                continue
                
            if isinstance(data, dict):
                formatted_text += f"\nATTEMPT {key}:\n"
                formatted_text += f"Strategy: {data.get('strategy', 'N/A')}\n"
                formatted_text += f"Files Modified: {', '.join(data.get('modified_files', []))}\n"
                formatted_text += f"Key Changes: {'; '.join(data.get('key_changes', []))}\n"
                formatted_text += f"Tools: {', '.join(data.get('tools_used', []))}\n"
                formatted_text += f"Assumptions: {'; '.join(data.get('assumptions_made', []))}\n"
        
        return formatted_text
    
    def _generate_risk_aware_guidance(self, problem_statement: str, approaches_data: Dict[str, Any]) -> str:
        """生成简洁的风险感知指导"""
        
        system_prompt = """You are a software engineering consultant specializing in failure analysis. Analyze failed attempts and provide concise, actionable guidance for avoiding common pitfalls.

Your output will be used as system prompt guidance, so be direct and specific.

Focus on:
1. Key blind spots to avoid
2. Critical risk points
3. Brief strategic approach

IMPORTANT: 
- Keep response under 200 words total
- Use plain text, no formatting
- Be specific and actionable
- Focus on risk avoidance"""
        
        formatted_attempts = self._format_approaches_data(approaches_data)
        
        prompt = f"""Analyze these failed attempts and provide concise guidance:

PROBLEM:
{problem_statement[:300]}...

FAILED ATTEMPTS:
{formatted_attempts[:800]}...

Provide concise guidance in this structure:

BLIND SPOTS TO AVOID:
[List 2-3 key systematic limitations observed]

CRITICAL RISKS:
[List 2-3 specific failure patterns to watch for]

STRATEGIC APPROACH:
[2-3 sentences on how to approach this problem differently]

Keep total response under 200 words. Be specific and actionable."""
        
        return self._call_llm_api(prompt, system_prompt)
    
    def _generate_content(self, instance_info: Dict[str, Any], problem_statement: str, trajectory_data: Dict[str, Any]) -> str:
        """生成轨迹池总结内容"""
        instance_name = instance_info['instance_name']
        
        # 直接使用附加的池数据
        approaches_data = instance_info.get('pool_data', {})
        if not approaches_data:
            self.logger.warning(f"跳过 {instance_name}: 无轨迹池数据")
            return ""
        
        # 使用占位符问题陈述（因为当前traj.pool格式没有problem字段）
        pool_problem = f"Instance {instance_name} software engineering problem"
        
        # 获取所有迭代数据（数字键）
        iteration_data = {k: v for k, v in approaches_data.items() 
                         if k.isdigit() and isinstance(v, dict)}
        
        if not iteration_data:
            self.logger.warning(f"跳过 {instance_name}: 无有效迭代数据")
            return ""
        
        self.logger.info(f"分析 {instance_name}: {len(iteration_data)} 个历史尝试")
        
        # 生成风险感知指导
        guidance = self._generate_risk_aware_guidance(pool_problem, iteration_data)
        
        if not guidance:
            # 如果LLM调用失败，提供简化的默认指导
            guidance = "Be careful with changes that affect multiple files. Test each change incrementally. Focus on understanding the problem before implementing solutions."
        
        return guidance


# 注册算子
from operators import register_operator
register_operator("traj_pool_summary", TrajPoolSummaryOperator)