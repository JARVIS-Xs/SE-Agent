#!/usr/bin/env python3

"""
SE Operators Base Classes

基于Aeon generators设计理念，为SE项目提供模块化算子系统。
支持两种基础算子类型：
- TemplateOperator: 返回instance_templates_dir（系统提示模板）
- EnhanceOperator: 返回enhance_history_filter_json（历史增强配置）
"""

import abc
import yaml
import json
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from sweagent.agent.models import get_model, GenericAPIModelConfig
from sweagent.tools.tools import ToolConfig
from core.utils.se_logger import get_se_logger


class BaseOperator(abc.ABC):
    """SE算子基类，定义通用功能和接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化算子
        
        Args:
            config: 包含operator_models等配置信息
        """
        self.config = config
        self.model = None  # LLM模型实例，延迟初始化
        self.logger = get_se_logger(f"operator.{self.get_name()}", emoji="🔧")
        
    def _setup_model(self) -> None:
        """设置LLM模型实例（复用Aeon generators的模型配置方式）"""
        if self.model is not None:
            return
            
        # 使用operator_models配置（如果存在），否则回退到model配置
        model_config_data = self.config.get('operator_models', self.config.get('model', {}))
        
        # 创建无成本限制的模型配置（算子不受成本限制）
        model_config = GenericAPIModelConfig(
            name=model_config_data.get('name', 'anthropic/claude-sonnet-4-20250514'),
            api_base=model_config_data.get('api_base'),
            api_key=model_config_data.get('api_key'),
            max_input_tokens=model_config_data.get('max_input_tokens'),
            max_output_tokens=model_config_data.get('max_output_tokens'),
            # 算子无成本限制
            per_instance_cost_limit=0,
            total_cost_limit=0,
            temperature=model_config_data.get('temperature', 0.0),
            top_p=model_config_data.get('top_p', 1.0),
        )
        
        # 创建最小工具配置（禁用函数调用）
        tools = ToolConfig(
            commands=[],
            use_function_calling=False,
            submit_command="submit"
        )
        
        self.model = get_model(model_config, tools)
        self.logger.info(f"LLM模型已初始化: {model_config.name}")
    
    def _call_llm_api(self, prompt: str, system_prompt: str = "") -> str:
        """
        调用LLM API（复用Aeon generators的调用方式）
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            
        Returns:
            LLM生成的响应文本
        """
        self._setup_model()
        
        # 构建消息历史
        history = []
        if system_prompt:
            history.append({"role": "system", "content": system_prompt})
        history.append({"role": "user", "content": prompt})
        
        try:
            response = self.model.query(history)
            message = response.get("message", "")
            return message if message else ""
        except Exception as e:
            self.logger.error(f"LLM API调用失败: {e}")
            return ""
    
    def _discover_instances(self, workspace_dir: Path, current_iteration: int) -> List[Dict[str, Any]]:
        """
        发现可处理的实例列表
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号
            
        Returns:
            实例信息列表，每个元素包含: {
                'instance_name': str,
                'instance_dir': Path,
                'trajectory_file': Path,
                'previous_iteration': int
            }
        """
        instances = []
        previous_iteration = current_iteration - 1
        
        if previous_iteration < 1:
            self.logger.warning(f"无效的前一迭代号: {previous_iteration}")
            return instances
        
        # 查找前一迭代的输出目录
        prev_iter_dir = workspace_dir / f"iteration_{previous_iteration}"
        if not prev_iter_dir.exists():
            self.logger.warning(f"前一迭代目录不存在: {prev_iter_dir}")
            return instances
        
        # 查找前一迭代中的所有实例目录
        for instance_dir in prev_iter_dir.iterdir():
            if not instance_dir.is_dir() or instance_dir.name.startswith('.'):
                continue
            
            # 查找.tra轨迹文件
            tra_files = list(instance_dir.glob("*.tra"))
            if not tra_files:
                continue
            
            # 使用第一个找到的.tra文件
            trajectory_file = tra_files[0]
            
            instances.append({
                'instance_name': instance_dir.name,
                'instance_dir': instance_dir,
                'trajectory_file': trajectory_file,
                'previous_iteration': previous_iteration
            })
        
        self.logger.info(f"发现 {len(instances)} 个可处理的实例")
        return instances
    
    def _load_trajectory_data(self, trajectory_file: Path) -> Dict[str, Any]:
        """
        加载轨迹数据（复用Aeon generators的数据加载逻辑）
        
        Args:
            trajectory_file: 轨迹文件路径
            
        Returns:
            轨迹数据字典
        """
        try:
            with open(trajectory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载轨迹文件失败 {trajectory_file}: {e}")
            return {}
    
    def _extract_problem_statement(self, trajectory_data: Dict[str, Any]) -> str:
        """
        从轨迹数据中提取问题陈述（复用Aeon generators的提取逻辑）
        
        Args:
            trajectory_data: 轨迹数据字典
            
        Returns:
            问题陈述文本
        """
        import re
        
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
    
    def _process_single_instance(self, instance_info: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        处理单个实例（在子类中实现具体逻辑）
        
        Args:
            instance_info: 实例信息字典
            
        Returns:
            (instance_name, generated_content) 或 None表示处理失败
        """
        instance_name = instance_info['instance_name']
        try:
            # 加载轨迹数据
            trajectory_data = self._load_trajectory_data(instance_info['trajectory_file'])
            if not trajectory_data:
                self.logger.warning(f"跳过 {instance_name}: 无法加载轨迹数据")
                return None
            
            # 提取问题陈述
            problem_statement = self._extract_problem_statement(trajectory_data)
            if not problem_statement:
                self.logger.warning(f"跳过 {instance_name}: 无法提取问题陈述")
                return None
            
            # 调用子类的生成逻辑
            generated_content = self._generate_content(instance_info, problem_statement, trajectory_data)
            if not generated_content:
                self.logger.warning(f"跳过 {instance_name}: 内容生成失败")
                return None
            
            return (instance_name, generated_content)
            
        except Exception as e:
            self.logger.error(f"处理实例 {instance_name} 时出错: {e}")
            return None
    
    @abc.abstractmethod
    def get_name(self) -> str:
        """获取算子名称"""
        pass
    
    @abc.abstractmethod
    def _generate_content(self, instance_info: Dict[str, Any], problem_statement: str, trajectory_data: Dict[str, Any]) -> str:
        """
        生成内容（子类实现核心逻辑）
        
        Args:
            instance_info: 实例信息
            problem_statement: 问题陈述
            trajectory_data: 轨迹数据
            
        Returns:
            生成的内容字符串
        """
        pass
    
    @abc.abstractmethod
    def process(self, workspace_dir: str, current_iteration: int, num_workers: int = 1) -> Optional[Dict[str, str]]:
        """
        处理算子逻辑的主入口方法
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号
            num_workers: 并发worker数量
            
        Returns:
            算子返回的参数字典，如 {'instance_templates_dir': 'path'} 或 None表示失败
        """
        pass


class TemplateOperator(BaseOperator):
    """
    模板算子基类，用于生成系统提示模板
    返回 instance_templates_dir 参数
    """
    
    def _create_output_dir(self, workspace_dir: Path, current_iteration: int) -> Path:
        """
        创建输出目录
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号
            
        Returns:
            输出目录路径
        """
        # 输出到当前迭代的system_prompt目录
        output_dir = workspace_dir / f"iteration_{current_iteration}" / "system_prompt"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"创建输出目录: {output_dir}")
        return output_dir
    
    def _create_yaml_content(self, strategy_content: str) -> str:
        """
        创建YAML格式的系统提示内容（复用Aeon generators的格式）
        
        Args:
            strategy_content: 策略内容文本
            
        Returns:
            YAML格式的配置内容
        """
        # 标准前缀
        prefix = "You are a helpful assistant that can interact with a terminal to solve software engineering tasks."
        
        # 组合前缀和策略内容
        full_content = f"{prefix}\n\n{self.get_strategy_prefix()}:\n\n{strategy_content}"
        
        # 创建YAML结构
        yaml_content = {
            'agent': {
                'templates': {
                    'system_template': full_content
                }
            }
        }
        
        return yaml.dump(yaml_content, default_flow_style=False, allow_unicode=True, width=1000)
    
    def _save_instance_template(self, instance_name: str, content: str, output_dir: Path) -> None:
        """
        保存实例模板文件
        
        Args:
            instance_name: 实例名称
            content: 生成的内容
            output_dir: 输出目录
        """
        yaml_content = self._create_yaml_content(content)
        output_file = output_dir / f"{instance_name}.yaml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        self.logger.debug(f"保存模板文件: {output_file}")
    
    @abc.abstractmethod
    def get_strategy_prefix(self) -> str:
        """获取策略前缀标识（如 'ALTERNATIVE SOLUTION STRATEGY'）"""
        pass
    
    def process(self, workspace_dir: str, current_iteration: int, num_workers: int = 1) -> Optional[Dict[str, str]]:
        """
        处理模板算子逻辑
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号  
            num_workers: 并发worker数量
            
        Returns:
            {'instance_templates_dir': 'path'} 或 None表示失败
        """
        workspace_path = Path(workspace_dir)
        
        self.logger.info(f"开始处理 {self.get_name()} 算子")
        self.logger.info(f"工作目录: {workspace_path}")
        self.logger.info(f"当前迭代: {current_iteration}")
        self.logger.info(f"并发数: {num_workers}")
        
        # 发现实例
        instances = self._discover_instances(workspace_path, current_iteration)
        if not instances:
            self.logger.warning("未找到可处理的实例")
            return None
        
        # 创建输出目录
        output_dir = self._create_output_dir(workspace_path, current_iteration)
        
        # 并行处理实例
        processed_count = 0
        failed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # 提交所有任务
            future_to_instance = {
                executor.submit(self._process_single_instance, instance_info): instance_info['instance_name']
                for instance_info in instances
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_instance):
                instance_name = future_to_instance[future]
                try:
                    result = future.result()
                    if result is not None:
                        name, content = result
                        self._save_instance_template(name, content, output_dir)
                        processed_count += 1
                        self.logger.debug(f"成功处理实例: {name}")
                    else:
                        failed_count += 1
                        self.logger.warning(f"处理实例失败: {instance_name}")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"处理实例 {instance_name} 时出现异常: {e}")
        
        self.logger.info(f"处理完成: 成功 {processed_count}, 失败 {failed_count}")
        
        if processed_count == 0:
            self.logger.error("没有成功处理任何实例")
            return None
        
        # 返回instance_templates_dir
        return {'instance_templates_dir': str(output_dir)}


class EnhanceOperator(BaseOperator):
    """
    增强算子基类，用于生成历史增强配置
    返回 enhance_history_filter_json 参数
    """
    
    def process(self, workspace_dir: str, current_iteration: int, num_workers: int = 1) -> Optional[Dict[str, str]]:
        """
        处理增强算子逻辑（未开发）
        
        Args:
            workspace_dir: 工作目录路径
            current_iteration: 当前迭代号
            num_workers: 并发worker数量
            
        Returns:
            {'enhance_history_filter_json': 'path'} 或 None表示失败
        """
        # TODO: 此类型算子还未开发完成
        self.logger.warning("EnhanceOperator 类型算子还未开发完成")
        return None