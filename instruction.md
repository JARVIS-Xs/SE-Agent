# SWEAgent 使用说明

## 环境安装
这一部分的环境主要就是SWEAgent本身所需。我们的代码主要组织在SE目录下
### 源码安装

1.安装依赖：
```bash
pip install --editable .
```

2. 验证安装：
```bash
sweagent --help
```


## 基本运行指令

### 运行示例

基础运行命令：
```bash
python SE/basic_run.py --config /home/uaih3k9x/630_swe/SE/configs/se_configs/dpsk29.yaml
```

使用crossover算子的运行命令：
```bash
python SE/basic_run.py --config /home/uaih3k9x/SE-Agent/SE/configs/se_configs/crossover_test.yaml
```

### 命令参数说明

- `--config`: 指定配置文件路径，可以自定义不同的配置组合
- 其他参数请参考具体的配置文件设置

### Strategy参数详解

`strategy`参数定义了整个执行策略的迭代流程，采用多轮次的处理方式：

```yaml
strategy:
  iterations:
    - base_config: "SE/configs/base_configs/baseconfig1.yaml"
      operator: null
    - base_config: "SE/configs/base_configs/baseconfig2.yaml"
      operator: "alternative_strategy"
    - base_config: "SE/configs/base_configs/baseconfig2.yaml"
      operator: "crossover"
```

#### 参数解释：

1. **iterations**: 定义了3个迭代步骤的执行序列
   - 每个iteration代表一个处理阶段
   - 按照数组顺序依次执行

2. **base_config**: 指定每个迭代使用的基础配置文件
   - `baseconfig1.yaml`: 第一轮使用的基础配置
   - `baseconfig2.yaml`: 后续轮次使用的基础配置
   - 不同的base_config可能包含不同的模型参数、提示词等

3. **operator**: 指定每个迭代使用的算子（可选）
   - `null`: 不使用额外算子，仅使用基础配置
   - `"alternative_strategy"`: 使用替代策略算子，生成多种解决方案
   - `"crossover"`: 使用交叉算子，结合前面迭代的结果进行优化

#### 执行流程：

1. **第1轮**: 使用baseconfig1.yaml的基础配置，不加载额外算子
2. **第2轮**: 切换到baseconfig2.yaml配置，加载alternative_strategy算子生成替代策略
3. **第3轮**: 继续使用baseconfig2.yaml，加载crossover算子对前面的结果进行交叉优化

这种设计允许在不同阶段使用不同的策略组合，通过crossover算子实现解决方案的进化和优化。

## 框架特性

### 配置文件自定义

- 可以在config目录中自定义不同的配置组合
- 支持灵活的参数配置和策略选择
- 配置文件采用YAML格式，便于修改和扩展

### 算子扩展

- 可以在operator目录中继续编写自定义算子
- 支持模块化的算子组合
- 提供丰富的算子接口用于扩展功能

### 可扩展性

- 框架设计支持多种运行模式
- 可以根据需要添加新的功能模块
- 支持不同的评估策略和优化方案

## TODO

- [ ] 方案选择（评估函数）实现
- [ ] enhanceoperator算子功能开发
- [ ] se_run.py完整测试和验证(目前使用SE/basic_run.py即可)，支持断点续跑