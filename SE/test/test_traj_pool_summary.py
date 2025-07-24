#!/usr/bin/env python3
"""
测试 traj_pool_summary 算子的脚本
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from SE.operators import create_operator, list_operators


def test_traj_pool_summary():
    """测试 traj_pool_summary 算子"""
    
    print("=== 测试 traj_pool_summary 算子 ===")
    
    # 1. 检查算子是否注册成功
    operators = list_operators()
    print(f"已注册的算子: {operators}")
    
    if "traj_pool_summary" not in operators:
        print("❌ traj_pool_summary 算子未注册")
        return False
    
    # 2. 创建算子实例
    config = {
        "operator_models": {
            "name": "openai/deepseek-chat",
            "temperature": 0.0
        }
    }
    
    operator = create_operator("traj_pool_summary", config)
    if not operator:
        print("❌ 创建算子实例失败")
        return False
    
    print(f"✅ 算子创建成功: {operator.get_name()}")
    print(f"📝 策略前缀: {operator.get_strategy_prefix()}")
    
    # 3. 使用真实的traj.pool数据测试
    test_workspace = "/home/uaih3k9x/630_swe/SE/trajectories/test_20250714_153541"
    
    try:
        result = operator.process(
            workspace_dir=test_workspace,
            current_iteration=2,  # 假设处理第2次迭代
            num_workers=1
        )
        
        if result:
            print(f"✅ 算子处理成功")
            print(f"📤 返回结果: {result}")
            
            # 检查生成的模板文件
            templates_dir = result.get('instance_templates_dir')
            if templates_dir:
                templates_path = Path(templates_dir)
                if templates_path.exists():
                    yaml_files = list(templates_path.glob("*.yaml"))
                    print(f"📄 生成模板文件: {len(yaml_files)} 个")
                    
                    # 显示生成的内容
                    if yaml_files:
                        with open(yaml_files[0], 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"\n📋 生成的模板内容预览:")
                        print("=" * 50)
                        print(content)
                        print("=" * 50)
            
            return True
        else:
            print("❌ 算子处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False


if __name__ == "__main__":
    success = test_traj_pool_summary()
    if success:
        print("\n🎉 traj_pool_summary 算子测试通过！")
    else:
        print("\n⚠️ traj_pool_summary 算子测试失败")