#!/usr/bin/env python3

"""
SE Operators Registry System

提供算子的动态注册和获取功能，支持通过名称查找算子类。
"""

from typing import Dict, Type, Optional
from .base import BaseOperator


class OperatorRegistry:
    """算子注册表，管理所有可用的算子类"""
    
    def __init__(self):
        self._operators: Dict[str, Type[BaseOperator]] = {}
    
    def register(self, name: str, operator_class: Type[BaseOperator]) -> None:
        """
        注册算子类
        
        Args:
            name: 算子名称
            operator_class: 算子类
        """
        if not issubclass(operator_class, BaseOperator):
            raise ValueError(f"算子类 {operator_class} 必须继承自 BaseOperator")
        
        self._operators[name] = operator_class
        print(f"✅ 已注册算子: {name} -> {operator_class.__name__}")
    
    def get(self, name: str) -> Optional[Type[BaseOperator]]:
        """
        获取算子类
        
        Args:
            name: 算子名称
            
        Returns:
            算子类或None
        """
        return self._operators.get(name)
    
    def list_operators(self) -> Dict[str, str]:
        """
        列出所有已注册的算子
        
        Returns:
            算子名称到类名的映射
        """
        return {name: cls.__name__ for name, cls in self._operators.items()}
    
    def create_operator(self, name: str, config: Dict) -> Optional[BaseOperator]:
        """
        创建算子实例
        
        Args:
            name: 算子名称
            config: 算子配置
            
        Returns:
            算子实例或None
        """
        operator_class = self.get(name)
        if operator_class is None:
            print(f"❌ 未找到算子: {name}")
            return None
        
        try:
            return operator_class(config)
        except Exception as e:
            print(f"❌ 创建算子 {name} 失败: {e}")
            return None


# 全局算子注册表
_global_registry = OperatorRegistry()


def register_operator(name: str, operator_class: Type[BaseOperator]) -> None:
    """
    注册算子到全局注册表
    
    Args:
        name: 算子名称
        operator_class: 算子类
    """
    _global_registry.register(name, operator_class)


def get_operator_class(name: str) -> Optional[Type[BaseOperator]]:
    """
    从全局注册表获取算子类
    
    Args:
        name: 算子名称
        
    Returns:
        算子类或None
    """
    return _global_registry.get(name)


def create_operator(name: str, config: Dict) -> Optional[BaseOperator]:
    """
    从全局注册表创建算子实例
    
    Args:
        name: 算子名称
        config: 算子配置
        
    Returns:
        算子实例或None
    """
    return _global_registry.create_operator(name, config)


def list_operators() -> Dict[str, str]:
    """
    列出所有已注册的算子
    
    Returns:
        算子名称到类名的映射
    """
    return _global_registry.list_operators()


def get_registry() -> OperatorRegistry:
    """获取全局注册表实例"""
    return _global_registry