#!/usr/bin/env python3
"""
Problem描述标准化接口
提供统一的问题描述获取和管理功能
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
from core.utils.se_logger import get_se_logger


class ProblemManager:
    """问题描述管理器 - 统一problem获取接口"""
    
    def __init__(self):
        self.logger = get_se_logger("problem_manager", emoji="❓")
    
    def get_problem_description(self, instance_path: str, method: str = "auto") -> Optional[str]:
        """
        获取实例的问题描述
        
        Args:
            instance_path: 实例目录路径或实例名称
            method: 获取方法 - 'auto', 'file', 'trajectory', 'json'
            
        Returns:
            问题描述文本，失败时返回None
        """
        instance_path = Path(instance_path)
        
        if method == "auto":
            # 优先级：.problem文件 > trajectory提取 > JSON配置
            return (self._get_from_problem_file(instance_path) or 
                   self._get_from_trajectory(instance_path) or
                   self._get_from_json_config(instance_path))
        elif method == "file":
            return self._get_from_problem_file(instance_path)
        elif method == "trajectory": 
            return self._get_from_trajectory(instance_path)
        elif method == "json":
            return self._get_from_json_config(instance_path)
        else:
            self.logger.error(f"未知的获取方法: {method}")
            return None
    
    def _get_from_problem_file(self, instance_path: Path) -> Optional[str]:
        """从.problem文件获取问题描述"""
        if instance_path.is_file() and instance_path.suffix == ".problem":
            problem_file = instance_path
        else:
            # 查找实例目录下的.problem文件
            instance_name = instance_path.name
            problem_file = instance_path / f"{instance_name}.problem"
            
        if problem_file.exists():
            try:
                with open(problem_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                self.logger.debug(f"从.problem文件获取: {problem_file}")
                return content
            except Exception as e:
                self.logger.error(f"读取.problem文件失败: {e}")
        return None
    
    def _get_from_trajectory(self, instance_path: Path) -> Optional[str]:
        """从轨迹文件提取问题描述"""
        instance_name = instance_path.name
        
        # 查找.traj或.tra文件
        traj_files = list(instance_path.glob(f"{instance_name}.traj"))
        if not traj_files:
            traj_files = list(instance_path.glob(f"{instance_name}.tra"))
            
        if not traj_files:
            return None
            
        try:
            with open(traj_files[0], 'r', encoding='utf-8') as f:
                trajectory_data = json.load(f)
            
            # 提取PR描述
            if (len(trajectory_data) > 1 and 
                "content" in trajectory_data[1] and 
                len(trajectory_data[1]["content"]) > 0):
                
                text_content = trajectory_data[1]["content"][0].get("text", "")
                
                # 提取<pr_description>标签内容
                pr_match = re.search(r'<pr_description>(.*?)</pr_description>', 
                                   text_content, re.DOTALL)
                if pr_match:
                    problem_text = pr_match.group(1).strip()
                    self.logger.debug(f"从轨迹文件提取问题描述: {traj_files[0]}")
                    return problem_text
                    
        except Exception as e:
            self.logger.error(f"从轨迹文件提取问题描述失败: {e}")
        
        return None
    
    def _get_from_json_config(self, instance_path: Path) -> Optional[str]:
        """从JSON配置文件获取问题描述（待实现）"""
        # TODO: 实现从实例JSON配置文件获取问题描述
        return None
    
    def create_problem_file(self, instance_path: str, problem_text: str) -> bool:
        """
        创建.problem文件
        
        Args:
            instance_path: 实例目录路径
            problem_text: 问题描述文本
            
        Returns:
            是否创建成功
        """
        try:
            instance_path = Path(instance_path)
            instance_name = instance_path.name
            problem_file = instance_path / f"{instance_name}.problem"
            
            with open(problem_file, 'w', encoding='utf-8') as f:
                f.write(problem_text)
            
            self.logger.info(f"创建.problem文件: {problem_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建.problem文件失败: {e}")
            return False
    
    def validate_problem_availability(self, instance_path: str) -> Dict[str, Any]:
        """
        验证实例的问题描述可用性
        
        Args:
            instance_path: 实例目录路径
            
        Returns:
            验证结果字典
        """
        instance_path = Path(instance_path)
        result = {
            "instance_name": instance_path.name,
            "methods_available": [],
            "primary_source": None,
            "problem_length": 0,
            "problem_preview": None
        }
        
        # 检查各种获取方法
        for method in ["file", "trajectory", "json"]:
            problem = self.get_problem_description(instance_path, method)
            if problem:
                result["methods_available"].append(method)
                if not result["primary_source"]:
                    result["primary_source"] = method
                    result["problem_length"] = len(problem)
                    result["problem_preview"] = problem[:100] + "..." if len(problem) > 100 else problem
        
        return result


# 全局实例
_problem_manager = None

def get_problem_manager() -> ProblemManager:
    """获取全局Problem管理器实例"""
    global _problem_manager
    if _problem_manager is None:
        _problem_manager = ProblemManager()
    return _problem_manager

def get_problem_description(instance_path: str, method: str = "auto") -> Optional[str]:
    """便捷函数：获取问题描述"""
    return get_problem_manager().get_problem_description(instance_path, method)

def validate_problem_availability(instance_path: str) -> Dict[str, Any]:
    """便捷函数：验证问题描述可用性"""
    return get_problem_manager().validate_problem_availability(instance_path)