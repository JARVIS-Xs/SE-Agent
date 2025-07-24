#!/usr/bin/env python3

"""
SE Framework Utils Package

SE框架工具模块，提供日志管理、轨迹处理等核心功能。
"""

from .se_logger import setup_se_logging, get_se_logger
from .trajectory_processor import TrajectoryProcessor, process_trajectory_files, extract_problems_from_workspace
from .traj_pool_manager import TrajPoolManager
from .traj_summarizer import TrajSummarizer
from .traj_extractor import TrajExtractor
from .llm_client import LLMClient, TrajectorySummarizer
from .problem_manager import ProblemManager, get_problem_manager, get_problem_description, validate_problem_availability
from .instance_data_manager import (
    InstanceData, InstanceDataManager, get_instance_data_manager, 
    get_instance_data, get_iteration_instances, get_traj_pool_data
)

__all__ = [
    # 日志系统
    'setup_se_logging',
    'get_se_logger', 
    # 轨迹处理
    'TrajectoryProcessor',
    'process_trajectory_files',
    'extract_problems_from_workspace',
    'TrajPoolManager',
    'TrajSummarizer',
    'TrajExtractor',
    # LLM集成
    'LLMClient',
    'TrajectorySummarizer',
    # 问题管理 (统一接口)
    'ProblemManager',
    'get_problem_manager', 
    'get_problem_description', 
    'validate_problem_availability',
    # Instance数据管理 (统一数据流转)
    'InstanceData',
    'InstanceDataManager',
    'get_instance_data_manager',
    'get_instance_data',
    'get_iteration_instances',
    'get_traj_pool_data'
]