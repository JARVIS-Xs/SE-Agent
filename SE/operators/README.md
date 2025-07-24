# SE Operators System

SE框架的算子系统提供了模块化的轨迹分析和策略生成功能。通过不同的算子，SE可以分析历史执行轨迹，生成个性化的解决策略。

## 🏗️ 架构设计

### 核心架构

```
BaseOperator (抽象基类)
├── TemplateOperator (模板算子基类)
│   ├── AlternativeStrategyOperator ✅
│   ├── TrajPoolSummaryOperator ✅
│   ├── TrajectoryAnalyzerOperator ✅
│   └── CrossoverOperator ✅
└── EnhanceOperator (增强算子基类) ❌ (未开发)
```

### 算子类型

#### 1. **TemplateOperator** (模板算子)
- **功能**: 生成个性化的系统提示模板
- **输出**: `instance_templates_dir` 参数，指向包含YAML模板文件的目录
- **用途**: 为每个实例生成针对性的解决策略提示

#### 2. **EnhanceOperator** (增强算子) ❌ **未开发**
- **功能**: 生成历史增强配置
- **输出**: `enhance_history_filter_json` 参数，指向JSON配置文件
- **用途**: 优化历史对话的过滤和选择，提供增强功能
- **状态**: 此类型算子还未开发完成

## 📋 已实现算子

### 1. **AlternativeStrategyOperator** ✅
- **类型**: TemplateOperator
- **功能**: 基于最近一次失败尝试生成截然不同的替代解决策略
- **策略前缀**: `ALTERNATIVE SOLUTION STRATEGY`
- **数据来源**: 轨迹池 (`traj.pool`) 中的历史失败数据
- **特点**: 
  - 分析最近失败的尝试
  - 生成正交的解决方案避免重复错误
  - 支持LLM生成和默认降级策略

### 2. **TrajPoolSummaryOperator** ✅
- **类型**: TemplateOperator
- **功能**: 分析轨迹池中的历史失败尝试，识别常见盲区和风险点
- **策略前缀**: `RISK-AWARE PROBLEM SOLVING GUIDANCE`
- **数据来源**: 轨迹池 (`traj.pool`) 中的所有历史数据
- **特点**:
  - 跨迭代分析，识别系统性风险
  - 生成简洁的风险感知指导
  - 专注于盲区避免和风险点识别

### 3. **TrajectoryAnalyzerOperator** ✅
- **类型**: TemplateOperator
- **功能**: 直接分析 `.tra` 轨迹文件，提取详细的问题陈述和轨迹数据
- **策略前缀**: `SOLUTION STRATEGY`
- **数据来源**: 前一迭代的 `.tra` 文件
- **特点**:
  - 直接从轨迹文件分析
  - 提取详细的问题陈述和执行统计
  - 生成基于完整轨迹内容的解决策略

### 4. **CrossoverOperator** ✅
- **类型**: TemplateOperator
- **功能**: 交叉对比算子，结合两条轨迹的特性生成新策略
- **策略前缀**: `CROSSOVER STRATEGY`
- **数据来源**: 轨迹池 (`traj.pool`) 中的历史数据
- **特点**:
  - 要求轨迹池中有效条数 >= 2
  - 分析最近两条轨迹的优劣
  - 生成综合两种方法优点的混合策略
  - 有效条数不足时记录错误并跳过

## ❌ 未开发算子类型

### **EnhanceOperator** (增强算子基类)
- **状态**: 此类型算子还未开发完成
- **预期功能**: 生成历史增强配置，优化SWE-agent的历史对话处理
- **预期输出**: `enhance_history_filter_json` 参数
- **开发计划**: 未来版本将提供多种增强算子实现

## 🔧 算子开发

### 核心接口

每个算子都需要实现以下核心方法：

```python
from operators import TemplateOperator, register_operator

class MyOperator(TemplateOperator):
    def get_name(self) -> str:
        """返回算子唯一名称"""
        return "my_operator"
    
    def get_strategy_prefix(self) -> str:
        """返回策略前缀标识"""
        return "MY STRATEGY"
    
    def _generate_content(self, instance_info: Dict[str, Any], 
                         problem_statement: str, 
                         trajectory_data: Dict[str, Any]) -> str:
        """实现核心生成逻辑"""
        # 分析数据，生成策略内容
        return "生成的策略内容"

# 注册算子
register_operator("my_operator", MyOperator)
```

### 算子基类功能

**BaseOperator** 提供以下通用功能：

- **LLM集成**: `_call_llm_api()` 方法调用LLM API
- **模型管理**: 自动配置和管理LLM模型实例
- **实例发现**: `_discover_instances()` 发现可处理的实例
- **轨迹加载**: `_load_trajectory_data()` 加载轨迹数据
- **问题提取**: `_extract_problem_statement()` 提取问题陈述
- **并发处理**: 支持多线程并发处理实例
- **日志记录**: 统一的日志记录和错误处理

**TemplateOperator** 额外提供：

- **输出目录管理**: `_create_output_dir()` 创建输出目录
- **YAML生成**: `_create_yaml_content()` 生成YAML格式模板
- **模板保存**: `_save_instance_template()` 保存实例模板文件

**EnhanceOperator** (未开发)：
- 此类型算子还未开发完成，未来将提供历史增强相关功能

### 算子注册系统

```python
from operators import register_operator, list_operators, create_operator

# 注册算子
register_operator("my_operator", MyOperatorClass)

# 列出所有算子
operators = list_operators()
print(operators)  # {'my_operator': 'MyOperatorClass'}

# 创建算子实例
config = {"model": {...}}
operator = create_operator("my_operator", config)
```

## 📊 数据流

### 输入数据

算子系统使用以下标准化数据：

1. **问题描述**: 从 `.problem` 文件或轨迹数据中提取
2. **轨迹数据**: 从 `.tra` 文件中加载的压缩轨迹
3. **轨迹池**: 从 `traj.pool` 中加载的跨迭代分析数据
4. **实例信息**: 包含实例名称、路径等元数据

### 输出格式

#### TemplateOperator 输出

```yaml
agent:
  templates:
    system_template: |
      You are a helpful assistant that can interact with a terminal to solve software engineering tasks.
      
      [STRATEGY PREFIX]:
      
      [生成的策略内容]
```

#### EnhanceOperator 输出 (未开发)

```json
{
  "history_filter": {
    "max_history_length": 10,
    "filter_patterns": ["pattern1", "pattern2"],
    "priority_weights": {...}
  }
}
```

## 🧪 测试和开发

### 开发测试

```bash
# 算子开发测试
python SE/operator_dev.py

# 运行算子集成测试
python SE/test/run_operator_tests.py

# 测试特定算子
python SE/test/test_alternative_strategy.py
```

### 调试模式

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 创建算子实例
from operators import create_operator
operator = create_operator("alternative_strategy", config)

# 手动处理实例
result = operator.process(workspace_dir, current_iteration, num_workers=1)
```

## 📁 文件结构

```
SE/operators/
├── __init__.py                    # 统一入口和导出
├── README.md                      # 本文档
├── base.py                        # 基类定义
├── registry.py                    # 注册系统
├── alternative_strategy.py        # ✅ 替代策略算子
├── traj_pool_summary.py          # ✅ 轨迹池总结算子
├── trajectory_analyzer.py        # ✅ 轨迹分析算子
└── crossover.py                   # ✅ 交叉对比算子
```

## 🔗 与SE框架集成

### 配置文件中的算子使用

```yaml
# SE配置文件 (se_configs/*.yaml)
strategy:
  iterations:
    - base_config: "test_claude"
      operator: null                           # 无算子
    - base_config: "baseconfig1"
      operator: "alternative_strategy"         # 使用替代策略算子
    - base_config: "test_claude"
      operator: "crossover"                   # 使用交叉对比算子
```

### 运行时集成

SE框架会自动：
1. 根据配置文件创建算子实例
2. 传递workspace目录和当前迭代信息
3. 获取算子输出的参数（如 `instance_templates_dir`）
4. 将参数传递给SWE-agent执行

## 📚 最佳实践

1. **错误处理**: 所有算子都应该提供降级策略，LLM调用失败时返回默认内容
2. **日志记录**: 使用统一的日志系统记录处理过程和错误
3. **数据验证**: 在处理前验证输入数据的完整性
4. **性能优化**: 利用并发处理提高大量实例的处理效率
5. **内容长度**: 生成的策略内容应该简洁明了，避免过长的提示

## 🚀 扩展新算子

要添加新的算子类型：

1. 继承合适的基类（`TemplateOperator` 或 `EnhanceOperator`）
2. 实现必需的抽象方法
3. 在 `__init__.py` 中导入并注册
4. 添加相应的测试用例
5. 更新本文档

注意：`EnhanceOperator` 类型算子还未开发完成，建议优先开发 `TemplateOperator` 类型算子。

---

*算子系统是SE框架的核心组件，通过模块化设计实现了灵活的策略生成和轨迹分析能力。*