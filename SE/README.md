# SE Framework 

## 🚀 快速开始

SE框架是基于SWE-agent的多样性实验系统，通过多次迭代和算子策略生成不同的解决方案。

### 立即使用

```bash
# 1. 快速演示 (推荐第一次使用)
python SE/basic_run.py --mode demo

# 2. 执行实验 (需要配置API key)
python SE/basic_run.py --mode execute

# 3. 使用自定义配置
python SE/basic_run.py --config SE/configs/se_configs/test_deepseek_se.yaml --mode execute
```

### 运行要求

- **工作目录**: 必须在项目根目录 `/home/uaih3k9x/630_swe` 执行
- **API配置**: 需要在配置文件中设置有效的API key
- **依赖**: 需要安装SWE-agent和相关依赖

## 🎯 核心特性

### 多迭代执行
- 对每个问题执行多次不同的解决尝试
- 每次迭代使用不同的配置和策略
- 自动生成时间戳目录避免冲突

### 算子系统
- **TemplateOperator**: 生成个性化系统提示
- **FilterOperator**: 生成历史过滤配置
- 模块化设计，易于扩展新算子

### 智能轨迹处理
- 自动压缩轨迹文件，节省75%-87%存储空间
- 智能提取问题描述为`.problem`文件
- LLM驱动的轨迹分析和总结

## 📁 项目结构

```
SE/
├── basic_run.py              # 主入口 - 多迭代执行器
├── configs/                  # 配置文件目录
│   ├── se_configs/           # SE主配置
│   └── base_configs/         # SWE-agent基础配置
├── core/                     # 核心功能模块
│   ├── swe_iterator.py       # SWE-agent迭代运行器
│   └── utils/               # 工具函数
├── operators/               # 算子系统
│   ├── base.py              # 算子基类
│   └── registry.py          # 算子注册管理
├── instances/               # 测试实例
└── trajectories/            # 执行结果输出
```

## 🔧 配置说明

### SE主配置文件 (se_configs/*.yaml)

```yaml
# 模型配置
model:
  name: "anthropic/claude-sonnet-4-20250514"
  api_base: "https://api.ezai88.com"
  api_key: "your-api-key"

# 实例配置
instances:
  json_file: "SE/instances/test.json"
  key: "instances"

# 输出配置
output_dir: "SE/trajectories/experiment_001"

# 策略编排 - 定义多次迭代
strategy:
  iterations:
    - base_config: "test_claude"      # 第1次
      operator: null
    - base_config: "baseconfig1"      # 第2次 
      operator: null
    - base_config: "test_claude"      # 第3次
      operator: "Crossover"
```

## 📊 输出结构

每次运行生成唯一的输出目录：

```
SE/trajectories/test_20250714_123456/
├── iteration_1/                    # 第一次迭代
│   ├── instance_name/
│   │   ├── instance.traj           # 原始轨迹
│   │   ├── instance.tra            # 压缩轨迹 (节省80%+)
│   │   ├── instance.problem        # 问题描述
│   │   └── instance.pred           # 预测结果
│   └── preds.json                  # 批次结果汇总
├── iteration_2/                    # 第二次迭代
└── se_framework.log                # 框架日志
```

## 🛠️ 开发指南

### 测试系统

```bash
# 运行测试套件
python SE/test/run_operator_tests.py

# 测试特定算子
python SE/test/test_alternative_strategy.py

# 算子开发测试
python SE/operator_dev.py
```

### 创建新算子

```python
from SE.operators import TemplateOperator, register_operator

class MyOperator(TemplateOperator):
    def get_name(self):
        return "my_operator"
    
    def get_strategy_prefix(self):
        return "MY CUSTOM STRATEGY"
    
    def _generate_content(self, instance_info, problem_description, trajectory_data):
        # 实现生成逻辑
        return "生成的策略内容"

# 注册算子
register_operator("my_operator", MyOperator)
```

## 📋 使用说明

### 第一次使用

1. **运行演示模式**：`python SE/basic_run.py --mode demo`
2. **阅读输出结构**：了解生成的文件和目录
3. **配置API key**：在配置文件中设置有效的API密钥
4. **执行实验**：`python SE/basic_run.py --mode execute`

### 自定义实验

1. **创建配置文件**：复制并修改`SE/configs/se_configs/`中的示例
2. **配置实例**：在`SE/instances/`中准备测试实例
3. **运行实验**：使用`--config`参数指定配置文件

## 🔗 相关文档

- 详细开发指南：`SE/test/README.md`
- 学习路径：`SE/LEARNING_GUIDE.md`
- 开发指南：`SE/DEVELOPMENT_GUIDE.md`
- 项目架构：根目录的`CLAUDE.md`

## ⚠️ 注意事项

- 所有SE相关命令必须在项目根目录执行
- 配置文件中的路径相对于项目根目录
- 需要配置有效的API key才能执行实验
- 演示模式不会消耗API额度，适合测试

## 🆘 故障排除

### 常见问题

1. **模块导入错误**：确保在项目根目录运行
2. **API调用失败**：检查API key和网络连接
3. **配置文件错误**：验证YAML语法和路径正确性
4. **权限问题**：确保有写入输出目录的权限

### 获取帮助

- 查看日志文件：`SE/trajectories/*/se_framework.log`
- 运行测试：`python SE/test/run_operator_tests.py`
- 查阅详细文档：`SE/test/README.md`

---

*开始您的多样性实验之旅！🚀*
