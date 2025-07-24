# 代码补丁分析工具

此工具用于分析filtered_predictions.json中的代码补丁，使用Claude API生成替代解决方案的框架。API密钥已内置在代码中。

## 功能

- 遍历filtered_predictions.json中的所有条目
- 提取每个条目的problem_statement和model_patch
- 使用Claude API分析补丁并生成替代解决方案框架
- 将结果保存到filtered_predict_conclusion.json

## 环境要求

- Python 3.6+
- 已安装requests库

## 安装依赖

```bash
pip install requests
```

## 使用方法

1. 确保filtered_predictions.json文件已存在于同一目录
2. 运行bash脚本:

```bash
chmod +x run_conclude_patch.sh
./run_conclude_patch.sh
```

要仅处理第一个条目进行测试，请使用:

```bash
./run_conclude_patch.sh --test
```

## 输出格式

输出文件filtered_predict_conclusion.json的格式如下:

```json
{
  "instance_id_1": {
    "approach_summary": "...",
    "modified_files": ["..."],
    "key_changes": "...",
    "strategy": "...",
    "specific_technique_from_first_solution": "...",
    "specific_files_or_functions": "...",
    "assumptions_made_in_first_solution": "...",
    "alternative_approach_1": "...",
    "component_not_touched_in_first_solution": "...",
    "different_perspective": "..."
  },
  "instance_id_2": {
    // ...同上
  },
  // 更多实例...
}
```

## 注意事项

- 如果输出文件已存在，脚本会加载现有数据并仅处理未处理的条目
- 每处理一个条目后，会立即保存结果，以防程序中断导致数据丢失
- 处理条目之间有1秒的延迟，以避免API调用过于频繁 