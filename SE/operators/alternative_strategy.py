#!/usr/bin/env python3

"""
Alternative Strategy Operator

基于最近一次失败尝试生成截然不同的替代解决策略，
避免重复相同的错误方法。
"""

import json
from pathlib import Path
from typing import Dict, Any
from operators import TemplateOperator


class AlternativeStrategyOperator(TemplateOperator):
    """替代策略算子，针对最近失败尝试生成正交的解决方案"""
    
    def get_name(self) -> str:
        return "alternative_strategy"
    
    def get_strategy_prefix(self) -> str:
        return "ALTERNATIVE SOLUTION STRATEGY"
    
    def _load_traj_pool(self, workspace_dir: Path) -> Dict[str, Any]:
        """加载轨迹池数据"""
        traj_pool_file = workspace_dir / "traj.pool"
        
        if not traj_pool_file.exists():
            self.logger.warning(f"traj.pool文件不存在: {traj_pool_file}")
            return {}
        
        try:
            with open(traj_pool_file, 'r', encoding='utf-8') as f:
                pool_data = json.load(f)
            
            # 返回第一个实例的数据
            for instance_name, instance_data in pool_data.items():
                if isinstance(instance_data, dict):
                    return instance_data
            
            return {}
            
        except Exception as e:
            self.logger.error(f"加载traj.pool失败 {traj_pool_file}: {e}")
            return {}
    
    def _get_latest_failed_approach(self, approaches_data: Dict[str, Any]) -> str:
        """获取最近一次失败尝试的详细信息"""
        if not approaches_data:
            return ""
        
        # 找到最大的迭代号
        iteration_nums = []
        for key in approaches_data.keys():
            if key != "problem" and key.isdigit():
                iteration_nums.append(int(key))
        
        if not iteration_nums:
            return ""
        
        latest_iteration = max(iteration_nums)
        latest_data = approaches_data.get(str(latest_iteration), {})
        
        # 格式化最近尝试的信息
        approach_summary = []
        approach_summary.append(f"Strategy: {latest_data.get('strategy', 'N/A')}")
        
        # 检查是否为失败实例
        if latest_data.get('strategy_status') == 'FAILED':
            approach_summary.append(f"STATUS: FAILED - {latest_data.get('failure_reason', 'Unknown failure')}")
        
        if latest_data.get('modified_files'):
            approach_summary.append(f"Modified Files: {', '.join(latest_data['modified_files'])}")
        
        if latest_data.get('key_changes'):
            approach_summary.append(f"Key Changes: {'; '.join(latest_data['key_changes'])}")
            
        if latest_data.get('tools_used'):
            approach_summary.append(f"Tools Used: {', '.join(latest_data['tools_used'])}")
            
        if latest_data.get('reasoning_pattern'):
            approach_summary.append(f"Reasoning Pattern: {latest_data['reasoning_pattern']}")
            
        if latest_data.get('assumptions_made'):
            approach_summary.append(f"Assumptions: {'; '.join(latest_data['assumptions_made'])}")
        
        return "\n".join(approach_summary)
    
    def _generate_alternative_strategy(self, problem_statement: str, previous_approach: str) -> str:
        """生成截然不同的替代策略"""
        
        system_prompt = """You are an expert software engineering strategist specializing in breakthrough problem-solving. Your task is to generate a fundamentally different approach to a software engineering problem, based on analyzing a previous failed attempt.

You will be given a problem and a previous approach that FAILED (possibly due to cost limits, early termination, or strategic inadequacy). Create a completely orthogonal strategy that:
1. Uses different investigation paradigms (e.g., runtime analysis vs static analysis)
2. Approaches from unconventional angles (e.g., user impact vs code structure)
3. Employs alternative tools and techniques
4. Follows different logical progression

CRITICAL: Your strategy must be architecturally dissimilar to avoid the same limitations and blind spots.

SPECIAL FOCUS: If the previous approach failed due to early termination or cost limits, prioritize:
- More focused, direct approaches
- Faster problem identification techniques
- Incremental validation methods
- Minimal viable change strategies

IMPORTANT: 
- Respond with plain text, no formatting
- Keep response under 200 words for system prompt efficiency
- Focus on cognitive framework rather than code specifics
- Provide actionable strategic guidance"""

        prompt = f"""Generate a radically different solution strategy:

PROBLEM:
{problem_statement[:400]}...

PREVIOUS FAILED APPROACH:
{previous_approach[:600]}...

Requirements for alternative strategy:
1. Adopt different investigation paradigm (e.g., empirical vs theoretical)
2. Start from alternative entry point (e.g., dependencies vs core logic)
3. Use non-linear logical sequence (e.g., symptom-to-cause vs cause-to-symptom)
4. Integrate unconventional techniques (e.g., profiling, fuzzing, visualization)
5. Prioritize overlooked aspects (e.g., performance, edge cases, integration)

Provide a concise strategic framework that enables an AI agent to approach this problem through an entirely different methodology. Focus on WHY this approach differs and HOW it circumvents previous limitations.

Keep response under 200 words."""

        return self._call_llm_api(prompt, system_prompt)
    
    def _generate_content(self, instance_info: Dict[str, Any], problem_statement: str, trajectory_data: Dict[str, Any]) -> str:
        """生成替代策略内容"""
        instance_dir = instance_info['instance_dir']
        instance_name = instance_info['instance_name']
        
        # 加载轨迹池数据（从workspace_dir，通过instance_dir计算）
        workspace_dir = instance_dir.parent.parent
        approaches_data = self._load_traj_pool(workspace_dir)
        if not approaches_data:
            self.logger.warning(f"跳过 {instance_name}: 无轨迹池数据")
            return ""
        
        # 获取最近一次失败尝试
        latest_approach = self._get_latest_failed_approach(approaches_data)
        if not latest_approach:
            self.logger.warning(f"跳过 {instance_name}: 无最近失败尝试数据")
            return ""
        
        self.logger.info(f"分析 {instance_name}: 基于最近失败尝试生成替代策略")
        
        # 生成替代策略
        strategy = self._generate_alternative_strategy(problem_statement, latest_approach)
        
        if not strategy:
            # 如果LLM调用失败，提供简单的默认替代策略
            strategy = "Try a more direct approach: focus on the specific error message, search for similar issues in the codebase, and make minimal targeted changes rather than broad modifications."
        
        return strategy


# 注册算子
from operators import register_operator
register_operator("alternative_strategy", AlternativeStrategyOperator)