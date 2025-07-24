#!/usr/bin/env python3
"""
测试统一的问题描述获取接口
"""

import sys
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import get_problem_description, validate_problem_availability

def test_problem_interface():
    """测试统一问题描述接口"""
    
    print("🧪 测试统一问题描述获取接口...")
    
    # 测试目录 - 使用Demo_Structure中的实例
    test_instance = "trajectories/Demo_Structure/iteration_1/sphinx-doc__sphinx-8548"
    
    if not Path(test_instance).exists():
        print(f"❌ 测试实例目录不存在: {test_instance}")
        return
    
    print(f"\n🔍 测试实例: {test_instance}")
    
    # 1. 验证问题描述可用性
    print("\n1️⃣ 验证问题描述可用性...")
    try:
        validation = validate_problem_availability(test_instance)
        print(f"✅ 验证结果:")
        print(f"  实例名称: {validation['instance_name']}")
        print(f"  可用方法: {validation['methods_available']}")
        print(f"  主要来源: {validation['primary_source']}")
        print(f"  内容长度: {validation['problem_length']}")
        print(f"  内容预览: {validation['problem_preview']}")
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    
    # 2. 测试自动获取
    print("\n2️⃣ 测试自动获取...")
    try:
        problem_auto = get_problem_description(test_instance)
        if problem_auto:
            print(f"✅ 自动获取成功: {len(problem_auto)} 字符")
            print(f"  预览: {problem_auto[:100]}...")
        else:
            print("❌ 自动获取失败")
    except Exception as e:
        print(f"❌ 自动获取异常: {e}")
    
    # 3. 测试各种方法
    methods = ['file', 'trajectory', 'json']
    for method in methods:
        print(f"\n3️⃣ 测试{method}方法...")
        try:
            problem = get_problem_description(test_instance, method=method)
            if problem:
                print(f"✅ {method}方法成功: {len(problem)} 字符")
            else:
                print(f"⚠️  {method}方法无结果")
        except Exception as e:
            print(f"❌ {method}方法异常: {e}")
    
    print("\n🎯 统一问题描述接口测试完成")

if __name__ == "__main__":
    test_problem_interface()