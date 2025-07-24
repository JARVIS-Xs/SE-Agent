#!/usr/bin/env python3
"""
测试统一的Instance数据管理系统
验证新的数据流转接口是否正常工作
"""

import sys
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import (
    get_instance_data, get_iteration_instances, get_traj_pool_data,
    get_instance_data_manager, InstanceData
)

def test_instance_data_management():
    """测试Instance数据管理系统"""
    
    print("🧪 测试统一Instance数据管理系统...")
    
    # 测试目录
    test_iteration = "trajectories/Demo_Structure/iteration_1"
    test_instance = "trajectories/Demo_Structure/iteration_1/sphinx-doc__sphinx-8548"
    test_pool = "trajectories/Demo_Structure/traj.pool"
    
    # 1. 测试单个实例数据获取
    print("\n1️⃣ 测试单个实例数据获取...")
    try:
        instance_data = get_instance_data(test_instance)
        print(f"✅ 实例数据获取成功: {instance_data.instance_name}")
        print(f"  Problem: {'✓' if instance_data.problem_description else '✗'}")
        print(f"  TRA: {'✓' if instance_data.tra_content else '✗'}")
        print(f"  TRAJ: {'✓' if instance_data.traj_content else '✗'}")
        print(f"  Patch: {'✓' if instance_data.patch_content else '✗'}")
        print(f"  可用文件: {instance_data.available_files}")
        
        if instance_data.problem_description:
            print(f"  问题预览: {instance_data.problem_description[:100]}...")
        
    except Exception as e:
        print(f"❌ 单个实例数据获取失败: {e}")
    
    # 2. 测试迭代实例列表获取
    print("\n2️⃣ 测试迭代实例列表获取...")
    try:
        instances = get_iteration_instances(test_iteration)
        print(f"✅ 迭代实例获取成功: {len(instances)} 个实例")
        
        for i, instance in enumerate(instances[:3]):  # 只显示前3个
            print(f"  实例{i+1}: {instance.instance_name}")
            print(f"    数据完整性: Problem={bool(instance.problem_description)}, "
                  f"TRA={bool(instance.tra_content)}, Patch={bool(instance.patch_content)}")
        
        if len(instances) > 3:
            print(f"  ... 还有 {len(instances) - 3} 个实例")
            
    except Exception as e:
        print(f"❌ 迭代实例列表获取失败: {e}")
    
    # 3. 测试数据完整性验证
    print("\n3️⃣ 测试数据完整性验证...")
    try:
        manager = get_instance_data_manager()
        instance_data = get_instance_data(test_instance)
        validation = manager.validate_instance_completeness(instance_data)
        
        print(f"✅ 完整性验证:")
        print(f"  实例: {validation['instance_name']}")
        print(f"  完整性评分: {validation['completeness_score']}%")
        print(f"  缺失数据: {validation['missing_data']}")
        print(f"  可用文件: {validation['available_files']}")
        
    except Exception as e:
        print(f"❌ 数据完整性验证失败: {e}")
    
    # 4. 测试轨迹池数据获取
    print("\n4️⃣ 测试轨迹池数据获取...")
    try:
        if Path(test_pool).exists():
            pool_data = get_traj_pool_data(test_pool, "sphinx-doc__sphinx-8548")
            if pool_data:
                print(f"✅ 轨迹池数据获取成功")
                print(f"  问题: {pool_data.get('problem', 'N/A')[:100]}...")
                iterations = [k for k in pool_data.keys() if k.isdigit()]
                print(f"  迭代数量: {len(iterations)}")
            else:
                print("⚠️  轨迹池中未找到指定实例")
        else:
            print("⚠️  轨迹池文件不存在")
            
    except Exception as e:
        print(f"❌ 轨迹池数据获取失败: {e}")
    
    # 5. 测试批量完整性报告
    print("\n5️⃣ 测试批量完整性报告...")
    try:
        from core.utils.traj_extractor import TrajExtractor
        extractor = TrajExtractor()
        report = extractor.get_instance_completeness_report(test_iteration)
        
        print(f"✅ 完整性报告生成成功:")
        print(f"  总实例数: {report['total_instances']}")
        print(f"  完整实例: {report['complete_instances']}")
        print(f"  不完整实例: {len(report['incomplete_instances'])}")
        print(f"  文件可用性:")
        for file_type, count in report['file_availability'].items():
            percentage = (count / report['total_instances']) * 100 if report['total_instances'] > 0 else 0
            print(f"    {file_type}: {count}/{report['total_instances']} ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ 批量完整性报告失败: {e}")
    
    print("\n🎯 Instance数据管理系统测试完成")

if __name__ == "__main__":
    test_instance_data_management()