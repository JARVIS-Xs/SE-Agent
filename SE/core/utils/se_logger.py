#!/usr/bin/env python3
"""
SE框架日志配置模块

基于SWE-agent现有日志系统，为SE框架提供统一的日志管理。
日志文件保存在每次运行的output_dir下，确保不会重叠覆盖。
"""

from pathlib import Path
from sweagent.utils.log import get_logger, add_file_handler


class SELoggerManager:
    """SE框架日志管理器"""
    
    def __init__(self):
        self.handler_id = None
        self.log_file_path = None
        
    def setup_logging(self, output_dir: str | Path) -> str:
        """
        为SE框架设置日志系统
        
        Args:
            output_dir: 输出目录路径（如 "SE/trajectories/testt_5/iteration_1"）
            
        Returns:
            日志文件的完整路径
        """
        output_dir = Path(output_dir)
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志文件路径
        self.log_file_path = output_dir / "se_framework.log"
        
        # 添加SE专用文件处理器
        self.handler_id = add_file_handler(
            self.log_file_path,
            filter="SE",  # 只记录SE相关的日志
            level="DEBUG"  # 记录所有级别：DEBUG, INFO, WARNING, ERROR
        )
        
        return str(self.log_file_path)
    
    def get_se_logger(self, module_name: str, emoji: str = "📋") -> object:
        """
        获取SE框架专用logger
        
        Args:
            module_name: 模块名称（如 "SE.core.utils"）
            emoji: 显示用的emoji（用于区分不同模块）
            
        Returns:
            配置好的logger对象
        """
        # 确保模块名称以SE开头，这样filter="SE"才能匹配
        if not module_name.startswith("SE"):
            module_name = f"SE.{module_name}"
            
        return get_logger(module_name, emoji=emoji)


# 全局实例
se_logger_manager = SELoggerManager()


def setup_se_logging(output_dir: str | Path) -> str:
    """
    快捷设置SE日志系统
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        日志文件路径
    """
    return se_logger_manager.setup_logging(output_dir)


def get_se_logger(module_name: str, emoji: str = "📋") -> object:
    """
    快捷获取SE logger
    
    Args:
        module_name: 模块名称
        emoji: 显示emoji
        
    Returns:
        logger对象
    """
    return se_logger_manager.get_se_logger(module_name, emoji)