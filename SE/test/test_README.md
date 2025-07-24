# SE 算子测试目录

本目录包含SE算子系统的专用测试文件，用于验证各算子的功能正确性。

## 新增算子测试文件

### 1. `test_alternative_strategy.py`
- **功能**: 测试 `alternative_strategy` 算子
- **测试范围**: 
  - 算子创建和注册
  - 轨迹池数据加载
  - 最近失败尝试提取
  - 策略生成逻辑
  - 完整处理流程
  - 输出格式验证

### 2. `test_traj_pool_summary.py`
- **功能**: 测试 `traj_pool_summary` 算子
- **测试范围**:
  - 算子创建和注册
  - 多迭代数据加载和处理
  - 风险分析功能
  - 输出格式验证（BLIND SPOTS + CRITICAL RISKS + STRATEGIC APPROACH）
  - 完整处理流程

### 3. `run_operator_tests.py`
- **功能**: 批量测试脚本，运行所有算子测试
- **特性**:
  - 支持单独测试指定算子
  - 支持批量测试所有算子
  - 生成综合测试报告
  - 包含算子注册系统测试

## 使用方法

### 运行单个算子测试
```bash
# 测试 alternative_strategy 算子
python SE/test/test_alternative_strategy.py

# 测试 traj_pool_summary 算子
python SE/test/test_traj_pool_summary.py
```

### 运行批量测试
```bash
# 运行所有测试
python SE/test/run_operator_tests.py

# 只测试特定算子
python SE/test/run_operator_tests.py --operator alternative_strategy
python SE/test/run_operator_tests.py --operator traj_pool_summary

# 只测试注册系统
python SE/test/run_operator_tests.py --registry-only
```

## 测试数据

测试文件使用模拟数据，包括：

### AlternativeStrategy 测试数据
- **问题**: Python类型检查错误修复
- **历史尝试**: 基于函数声明修改的失败尝试
- **预期输出**: 生成正交的替代策略

### TrajPoolSummary 测试数据
- **问题**: Sphinx LaTeX输出格式问题
- **历史尝试**: 包含2次不同方向的失败尝试
- **预期输出**: 风险感知的综合指导

## 测试覆盖范围

### 功能测试
- ✅ 算子注册和创建
- ✅ 数据加载和解析
- ✅ LLM集成（模拟）
- ✅ 策略生成逻辑
- ✅ 输出格式验证
- ✅ 完整处理流程

### 错误处理测试
- ✅ 缺少数据文件的处理
- ✅ 无效数据格式的处理
- ✅ LLM调用失败的回退
- ✅ 输出目录创建失败的处理

### 性能测试
- ✅ 多线程处理验证
- ✅ 内存使用监控
- ✅ 输出长度控制

## 注意事项

1. **LLM调用**: 测试中会实际调用LLM API，确保配置了有效的API密钥
2. **临时文件**: 测试会创建临时工作空间，测试完成后自动清理
3. **网络依赖**: LLM调用需要网络连接，离线环境可能部分测试失败
4. **配置要求**: 测试使用默认配置，可在测试类中修改模型配置

## 故障排除

### 常见问题
1. **导入错误**: 确保从项目根目录运行测试
2. **API调用失败**: 检查网络连接和API密钥配置
3. **权限错误**: 确保有写入临时目录的权限

### 调试模式
测试文件包含详细的日志输出，可以通过输出信息定位问题：
- `✅` 表示测试通过
- `❌` 表示测试失败
- `⚠️` 表示警告信息
- `📊/📄/🏊` 等表示不同类型的信息

这些测试确保SE算子系统的稳定性和可靠性，建议在算子代码修改后运行相应测试验证功能正确性。

---

## 原有测试文件说明

### API测试文件
- `api_test.py`, `api_test_litellm.py`: API连接测试
- `test_llm_integration.py`: LLM集成测试

### 其他组件测试
- `test_instance_data_system.py`: 实例数据系统测试
- `test_problem_interface.py`: 问题接口测试

更多详细信息请参考各测试文件的文档说明。