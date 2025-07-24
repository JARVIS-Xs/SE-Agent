# SE Operators 开发指南

## 概述

SE Operators 是一个模块化算子系统，用于在SWE-agent迭代间生成增强参数。基于Aeon generators的设计理念，提供统一的接口和强大的基础功能。

## 架构设计

### 系统组件

1. **BaseOperator**: 算子基类，提供通用功能
2. **TemplateOperator**: 模板算子，生成系统提示模板
3. **FilterOperator**: 过滤算子，生成历史过滤配置（待实现）
4. **OperatorRegistry**: 动态注册系统

### 数据流

```
迭代1完成 → 迭代2开始前 → 算子处理迭代1数据 → 生成增强参数 → 迭代2执行时使用
```

**关键时序**：算子是预处理器，在每次迭代执行前运行，分析之前的迭代数据为当前迭代提供指导。

**配置示例**：
```yaml
strategy:
  iterations:
    - base_config: "baseconfig1.yaml"
      operator: null                    # 迭代1：直接执行，无算子预处理
    - base_config: "baseconfig2.yaml"  
      operator: "alternative_strategy"  # 迭代2：执行前用算子处理迭代1结果
    - base_config: "baseconfig3.yaml"
      operator: "traj_pool_summary"     # 迭代3：执行前用算子处理迭代1+2结果
```

## Base类功能详解

### BaseOperator 核心功能

#### 1. LLM集成能力
```python
def _setup_model(self) -> None:
    """自动设置LLM模型实例"""
    # 支持operator_models配置，无成本限制
    # 使用sweagent的模型基础设施
```

#### 2. 实例发现
```python
def _discover_instances(self, workspace_dir: Path, current_iteration: int) -> List[Dict]:
    """自动发现可处理的实例"""
    # 查找 iteration_{current_iteration-1} 目录下的 .tra 文件
    # 返回实例信息列表
```

#### 3. 数据提取
```python
def _extract_problem_statement(self, trajectory_data: Dict) -> str:
    """从轨迹数据提取问题陈述"""
    # 解析<pr_description>标签内容
```

#### 4. 多线程处理
```python
def process(self, workspace_dir: str, current_iteration: int, num_workers: int = 1):
    """并发处理多个实例"""
    # 使用ThreadPoolExecutor并行处理
```

#### 5. 错误处理与日志
```python
self.logger = get_se_logger(f"operator.{self.get_name()}", emoji="🔧")
# 完整的异常捕获和日志记录
```

### TemplateOperator 专用功能

#### 1. 输出目录管理
```python
def _create_output_dir(self, workspace_dir: Path, current_iteration: int) -> Path:
    """创建 iteration_{current_iteration}/system_prompt/ 目录"""
```

#### 2. YAML模板生成
```python
def _create_yaml_content(self, strategy_content: str) -> str:
    """生成标准YAML格式的系统提示"""
    # 包含agent.templates.system_template结构
```

#### 3. 返回值规范
```python
return {'instance_templates_dir': 'path/to/system_prompt/'}
```

## 开发新算子指南

### 步骤1: 选择基类

#### 如果生成系统提示模板 → 继承 `TemplateOperator`
```python
from SE.operators import TemplateOperator

class MyTemplateOperator(TemplateOperator):
    pass
```

#### 如果生成其他配置 → 继承 `BaseOperator`
```python
from SE.operators import BaseOperator

class MyCustomOperator(BaseOperator):
    pass
```

### 步骤2: 实现必需方法

#### 对于 TemplateOperator

```python
class MyTemplateOperator(TemplateOperator):
    def get_name(self) -> str:
        """返回算子名称"""
        return "my_template"
    
    def get_strategy_prefix(self) -> str:
        """返回策略前缀标识"""
        return "MY SOLUTION STRATEGY"
    
    def _generate_content(self, instance_info: Dict, problem_statement: str, trajectory_data: Dict) -> str:
        """生成策略内容（核心逻辑）"""
        # 这里实现你的算子逻辑
        # 可以调用 self._call_llm_api() 使用LLM
        # 可以访问 self.logger 记录日志
        
        prompt = f"为以下问题生成解决策略：\n{problem_statement}"
        strategy = self._call_llm_api(prompt)
        return strategy
```

#### 对于 BaseOperator

```python
class MyCustomOperator(BaseOperator):
    def get_name(self) -> str:
        return "my_custom"
    
    def _generate_content(self, instance_info: Dict, problem_statement: str, trajectory_data: Dict) -> str:
        """生成内容"""
        pass
    
    def process(self, workspace_dir: str, current_iteration: int, num_workers: int = 1) -> Optional[Dict[str, str]]:
        """完整的处理逻辑"""
        # 自定义处理流程
        # 返回相应的参数字典
        return {'custom_param': 'value'}
```

### 步骤3: 注册算子

```python
from SE.operators import register_operator

# 注册算子
register_operator("my_template", MyTemplateOperator)
```

### 步骤4: 测试算子

```python
# 使用 operator_dev.py 测试
python SE/operator_dev.py --test-llm

# 或创建自定义测试
from SE.operators import create_operator

config = {...}  # 配置字典
operator = create_operator("my_template", config)
result = operator.process(workspace_dir, current_iteration, num_workers)
```

## 具体算子实现示例

### 现有算子总览

| 算子名称 | 功能 | 数据源 | 输出前缀 | 适用时机 |
|---------|------|--------|----------|----------|
| `alternative_strategy` | 生成替代解决方案 | 最近一次失败尝试 | ALTERNATIVE SOLUTION STRATEGY | 迭代2（基于迭代1失败） |
| `traj_pool_summary` | 风险感知综合分析 | 所有历史尝试 | RISK-AWARE PROBLEM SOLVING GUIDANCE | 迭代3+（综合历史分析） |

### 算子执行时序详解

```
时间线：
T1: 执行迭代1 (baseconfig1.yaml, operator: null)
    → 产生迭代1的轨迹和traj.pool数据

T2: 算子预处理 (alternative_strategy处理迭代1数据)
    → 生成 iteration_2/system_prompt/*.yaml
    → 执行迭代2 (baseconfig2.yaml + 算子生成的系统提示)
    → 产生迭代2的轨迹和traj.pool数据

T3: 算子预处理 (traj_pool_summary处理迭代1+2数据)
    → 生成 iteration_3/system_prompt/*.yaml  
    → 执行迭代3 (baseconfig3.yaml + 算子生成的系统提示)
```

**核心原则**：
- 算子在迭代执行**前**运行，作为预处理器
- 算子分析**之前所有迭代**的数据
- 算子为**当前迭代**生成增强的系统提示

### 示例1: AlternativeStrategy算子

基于最近一次失败尝试生成正交的替代策略：

```python
class AlternativeStrategyOperator(TemplateOperator):
    def get_name(self) -> str:
        return "alternative_strategy"
    
    def get_strategy_prefix(self) -> str:
        return "ALTERNATIVE SOLUTION STRATEGY"
    
    def _generate_content(self, instance_info, problem_statement, trajectory_data):
        # 加载traj.pool获取失败方法
        instance_dir = instance_info['instance_dir']
        previous_iteration = instance_info['previous_iteration']
        
        traj_pool = self._load_traj_pool(instance_dir)
        previous_approach = traj_pool.get(str(previous_iteration), "")
        
        if not previous_approach:
            return ""
        
        # 生成替代策略
        return self._generate_alternative_strategy(problem_statement, previous_approach)
    
    def _load_traj_pool(self, instance_dir: Path) -> Dict[str, str]:
        """加载策略池"""
        # 实现traj.pool加载逻辑
        pass
    
    def _generate_alternative_strategy(self, problem_statement: str, previous_approach: str) -> str:
        """使用LLM生成替代策略"""
        system_prompt = """你是软件工程策略专家..."""
        prompt = f"""生成替代策略：\n问题：{problem_statement}\n失败方法：{previous_approach}"""
        return self._call_llm_api(prompt, system_prompt)
```

### 示例2: TrajPoolSummary算子

基于所有历史尝试生成风险感知指导：

```python
class TrajPoolSummaryOperator(TemplateOperator):
    def get_name(self) -> str:
        return "traj_pool_summary"
    
    def get_strategy_prefix(self) -> str:
        return "RISK-AWARE PROBLEM SOLVING GUIDANCE"
    
    def _generate_content(self, instance_info, problem_statement, trajectory_data):
        # 加载所有历史尝试数据
        approaches_data = self._load_traj_pool(instance_info['instance_dir'])
        
        # 生成风险感知指导（控制在200字内）
        guidance = self._generate_risk_aware_guidance(problem_statement, approaches_data)
        return guidance
    
    def _generate_risk_aware_guidance(self, problem_statement: str, approaches_data: Dict) -> str:
        """生成简洁的风险感知指导"""
        # 使用LLM分析历史失败模式，生成盲区识别和风险规避策略
        # 输出格式：BLIND SPOTS TO AVOID + CRITICAL RISKS + STRATEGIC APPROACH
        pass
```

## 配置要求

### operator_models配置

在配置文件中添加算子专用的模型配置：

```yaml
# SE配置文件
operator_models:
  name: "anthropic/claude-sonnet-4-20250514"
  api_base: "https://api.ezai88.com"
  api_key: "your-api-key"
  temperature: 0.0
  max_output_tokens: 4000

# 或使用默认model配置
model:
  name: "openai/deepseek-chat"
  # ...
```

### 迭代配置

在strategy配置中使用算子：

```yaml
strategy:
  iterations:
    - base_config: "SE/configs/base_configs/baseconfig1.yaml"
      operator: null
    - base_config: "SE/configs/base_configs/baseconfig2.yaml"
      operator: "alternative_strategy"  # 使用注册的算子名称
```

## 最佳实践

### 1. 日志使用
```python
self.logger.info("开始处理实例")
self.logger.debug("详细调试信息")
self.logger.warning("警告信息")
self.logger.error("错误信息")
```

### 2. 错误处理
```python
try:
    result = self._some_operation()
except Exception as e:
    self.logger.error(f"操作失败: {e}")
    return None
```

### 3. LLM调用
```python
# 简单调用
response = self._call_llm_api(prompt)

# 带系统提示调用
response = self._call_llm_api(prompt, system_prompt)

# 检查响应
if not response:
    self.logger.warning("LLM调用失败")
    return default_content
```

### 4. 性能优化
- 算子内部已支持多线程，无需额外优化
- LLM调用会自动重用模型实例
- 使用logger.debug()记录详细信息，避免过度打印

## 调试技巧

### 1. 使用开发脚本
```bash
# 测试算子基础功能
python SE/operator_dev.py

# 测试LLM连接
python SE/operator_dev.py --test-llm

# 指定配置文件
python SE/operator_dev.py --config custom_config.yaml
```

### 2. 查看日志
```bash
# 日志文件位置
SE/trajectories/operator_dev_test/test_*/se_framework.log
```

### 3. 检查输出文件
```bash
# 模板文件位置
SE/trajectories/*/iteration_*/system_prompt/*.yaml
```

## 常见问题

### Q: 如何访问历史策略数据？
A: 使用`_load_traj_pool()`方法加载traj.pool文件，包含所有历史策略。

### Q: 如何处理LLM调用失败？
A: `_call_llm_api()`失败时返回空字符串，应提供默认策略或跳过该实例。

### Q: 如何自定义输出格式？
A: 继承BaseOperator并重写`process()`方法，返回自定义的参数字典。

### Q: 如何添加新的数据源？
A: 在`_generate_content()`中添加自定义的数据加载逻辑。

## 扩展功能

### 1. 自定义数据提取
```python
def _extract_custom_data(self, trajectory_data: Dict) -> Any:
    """提取自定义数据"""
    # 实现特定的数据提取逻辑
    pass
```

### 2. 多阶段策略生成
```python
def _generate_content(self, instance_info, problem_statement, trajectory_data):
    # 阶段1：分析
    analysis = self._analyze_problem(problem_statement)
    
    # 阶段2：策略生成
    strategy = self._generate_strategy(analysis)
    
    # 阶段3：优化
    optimized_strategy = self._optimize_strategy(strategy)
    
    return optimized_strategy
```

### 3. 条件式处理
```python
def _generate_content(self, instance_info, problem_statement, trajectory_data):
    if self._is_bug_fix(problem_statement):
        return self._generate_bug_fix_strategy(...)
    elif self._is_feature_request(problem_statement):
        return self._generate_feature_strategy(...)
    else:
        return self._generate_general_strategy(...)
```

这个指南提供了完整的算子开发流程和最佳实践。基于这个框架，你可以快速开发各种专门化的算子来增强SWE-agent的迭代能力。