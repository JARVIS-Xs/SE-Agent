# SE框架开发指南

## Python模块导入路径问题解决方案

在SE框架开发过程中，经常遇到Python模块导入路径问题。本指南总结了常见问题和标准解决方案。

### 🚨 常见路径问题

#### 1. **相对导入与绝对导入冲突**

**问题描述**: 
- 在包内使用相对导入 `from .module import something`
- 但脚本直接运行时或外部导入时出现 `ModuleNotFoundError`

**错误示例**:
```python
# SE/core/utils/trajectory_processor.py
from SE.core.utils.se_logger import get_se_logger  # ❌ 绝对导入在某些情况下失败
from .se_logger import get_se_logger                # ❌ 相对导入在直接运行时失败
```

#### 2. **循环导入问题**

**问题描述**:
- 模块A导入模块B，模块B又导入模块A
- 通过__init__.py间接产生的循环导入

**错误示例**:
```python
# SE/core/utils/__init__.py
from .se_logger import setup_se_logging
from .trajectory_processor import TrajectoryProcessor  # 导入trajectory_processor

# SE/core/utils/trajectory_processor.py  
from .se_logger import get_se_logger  # 这里又导入se_logger，可能产生循环
```

#### 3. **sys.path设置不一致**

**问题描述**:
- 不同脚本中的sys.path设置方式不同
- 导致模块查找路径不一致

### ✅ 标准解决方案

#### 1. **统一的sys.path设置模式**

对于项目根目录为 `/home/uaih3k9x/630_swe` 的SE框架：

```python
# 标准模式1: 在SE目录下的脚本（如SE/basic_run.py）
import sys
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 然后使用相对导入
from core.utils.se_logger import setup_se_logging
```

```python
# 标准模式2: 在SE子目录下的脚本（如SE/core/utils/generate_tra_files.py）
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent  # 根据层级调整
sys.path.insert(0, str(project_root))

# 然后使用绝对导入
from SE.core.utils.trajectory_processor import TrajectoryProcessor
```

#### 2. **延迟导入解决循环导入**

```python
class TrajectoryProcessor:
    def __init__(self):
        """初始化轨迹处理器"""
        # 延迟导入避免循环导入
        try:
            from .se_logger import get_se_logger
            self.logger = get_se_logger("trajectory_processor", emoji="🎬")
        except ImportError:
            # 回退方案：使用标准日志
            import logging
            self.logger = logging.getLogger("trajectory_processor")
            self.logger.setLevel(logging.INFO)
```

#### 3. **模块导入最佳实践**

```python
# ✅ 好的做法：在__init__.py中小心管理导出
# SE/core/utils/__init__.py
from .se_logger import setup_se_logging, get_se_logger

# 有条件的导入，避免立即触发循环导入
def get_trajectory_processor():
    from .trajectory_processor import TrajectoryProcessor
    return TrajectoryProcessor

__all__ = [
    'setup_se_logging',
    'get_se_logger', 
    'get_trajectory_processor'  # 函数形式导出
]
```

### 🛠️ 调试方法

#### 1. **导入问题调试脚本**

创建测试脚本验证导入：

```python
# debug_imports.py
import sys
from pathlib import Path

print("Python路径:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n尝试导入模块:")
try:
    from SE.core.utils import setup_se_logging
    print("✅ SE.core.utils导入成功")
except ImportError as e:
    print(f"❌ SE.core.utils导入失败: {e}")

try:
    from SE.core.utils.trajectory_processor import TrajectoryProcessor
    print("✅ TrajectoryProcessor导入成功")
except ImportError as e:
    print(f"❌ TrajectoryProcessor导入失败: {e}")
```

#### 2. **路径验证命令**

```bash
# 验证当前工作目录
pwd

# 验证Python能找到的模块
python -c "import sys; print('\n'.join(sys.path))"

# 验证特定模块是否可导入
python -c "from SE.core.utils import setup_se_logging; print('导入成功')"
```

### 📁 目录结构规范

SE框架标准目录结构：

```
/home/uaih3k9x/630_swe/           # 项目根目录
├── SE/                           # SE框架目录
│   ├── basic_run.py             # sys.path.insert(0, str(Path(__file__).parent))
│   ├── core/
│   │   └── utils/
│   │       ├── __init__.py      # 谨慎管理导出
│   │       ├── se_logger.py     # 基础模块，被其他模块导入
│   │       ├── trajectory_processor.py  # 使用延迟导入
│   │       └── generate_tra_files.py    # project_root = Path(__file__).parent.parent.parent.parent
│   └── ...
```

### 🔧 实际修复案例

#### 案例1: basic_run.py导入错误

**问题**: `ModuleNotFoundError: No module named 'SE'`

**原因**: trajectory_processor.py中使用了绝对导入，但sys.path没有包含项目根目录

**解决方案**:
```python
# 修改前
from SE.core.utils.se_logger import get_se_logger

# 修改后：延迟导入
def __init__(self):
    try:
        from .se_logger import get_se_logger
        self.logger = get_se_logger("trajectory_processor", emoji="🎬")
    except ImportError:
        import logging
        self.logger = logging.getLogger("trajectory_processor")
```

#### 案例2: generate_tra_files.py路径错误

**问题**: 深层目录脚本找不到SE模块

**解决方案**:
```python
# 计算正确的项目根目录路径
project_root = Path(__file__).parent.parent.parent.parent  # 从SE/core/utils/ 上4层到根目录
sys.path.insert(0, str(project_root))
```

### 📋 开发检查清单

在添加新模块或脚本时，检查以下事项：

- [ ] **确定脚本位置**: 明确脚本在项目中的层级位置
- [ ] **设置正确的sys.path**: 根据位置计算到项目根目录的相对路径
- [ ] **选择导入方式**: 优先使用相对导入，必要时使用延迟导入
- [ ] **避免循环导入**: 检查是否会产生直接或间接的循环导入
- [ ] **测试多种运行方式**: 直接运行、模块导入、pytest等
- [ ] **添加异常处理**: 为导入失败提供回退方案

### 🎯 最佳实践总结

1. **一致的路径设置**: 在整个项目中使用统一的sys.path设置模式
2. **延迟导入**: 对于可能产生循环导入的模块使用延迟导入
3. **回退机制**: 为导入失败提供合理的回退方案
4. **充分测试**: 在不同环境下测试导入是否正常
5. **文档记录**: 在代码中注释清楚路径设置的原理

通过遵循这些规范，可以避免在SE框架开发中遇到常见的Python路径问题。