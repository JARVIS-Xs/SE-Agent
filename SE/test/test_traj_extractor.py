#!/usr/bin/env python3
"""
测试TrajExtractor和更新后的TrajPoolManager
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.traj_extractor import TrajExtractor
from core.utils.traj_pool_manager import TrajPoolManager


def test_real_data_extraction():
    """测试从实际运行结果中提取数据"""
    print("=== 测试实际数据提取 ===")
    
    # 使用您提到的实际运行结果目录
    test_dir = Path("/home/uaih3k9x/630_swe/SE/trajectories/test_20250714_142331/iteration_1")
    
    if not test_dir.exists():
        print(f"⚠️ 测试目录不存在: {test_dir}")
        return
    
    extractor = TrajExtractor()
    
    print(f"1. 从目录提取数据: {test_dir}")
    instance_data_list = extractor.extract_instance_data_from_directory(test_dir)
    
    print(f"2. 提取到 {len(instance_data_list)} 个实例")
    
    for instance_name, problem, tra_content, pred_content in instance_data_list:
        print(f"\n实例: {instance_name}")
        print(f"  问题长度: {len(problem) if problem else 0} 字符")
        print(f"  轨迹长度: {len(tra_content)} 字符") 
        print(f"  预测长度: {len(pred_content)} 字符")
        
        if problem:
            problem_preview = problem[:100] + "..." if len(problem) > 100 else problem
            print(f"  问题预览: {problem_preview}")
        
        # 测试轨迹池管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            pool_path = os.path.join(temp_dir, "test_real.pool")
            manager = TrajPoolManager(pool_path)
            manager.initialize_pool()
            
            # 添加数据
            manager.add_iteration_summary(
                instance_name=instance_name,
                iteration=1,
                trajectory_content=tra_content,
                prediction_content=pred_content,
                problem=problem
            )
            
            # 检查结果
            pool_data = manager.load_pool()
            instance_pool_data = pool_data.get(instance_name, {})
            
            print(f"  轨迹池包含字段: {list(instance_pool_data.keys())}")
            if "problem" in instance_pool_data:
                print(f"  ✅ 问题字段已添加")
            if "1" in instance_pool_data:
                iteration_summary = instance_pool_data["1"]
                if isinstance(iteration_summary, dict):
                    print(f"  ✅ 迭代1总结包含 {len(iteration_summary)} 个字段")
                    print(f"  策略: {iteration_summary.get('strategy', 'N/A')}")
                    print(f"  方法: {iteration_summary.get('approach_summary', 'N/A')}")


def test_multiple_iterations():
    """测试多迭代数据"""
    print("\n=== 测试多迭代数据 ===")
    
    base_dir = Path("/home/uaih3k9x/630_swe/SE/trajectories/test_20250714_142331")
    
    if not base_dir.exists():
        print(f"⚠️ 基础目录不存在: {base_dir}")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pool_path = os.path.join(temp_dir, "test_multi.pool")
        manager = TrajPoolManager(pool_path)
        manager.initialize_pool()
        extractor = TrajExtractor()
        
        # 处理多个迭代
        for iteration in [1, 2]:
            iteration_dir = base_dir / f"iteration_{iteration}"
            if iteration_dir.exists():
                print(f"\n处理迭代 {iteration}:")
                instance_data_list = extractor.extract_instance_data_from_directory(iteration_dir)
                
                for instance_name, problem, tra_content, pred_content in instance_data_list:
                    manager.add_iteration_summary(
                        instance_name=instance_name,
                        iteration=iteration,
                        trajectory_content=tra_content,
                        prediction_content=pred_content,
                        problem=problem
                    )
                    print(f"  ✅ 添加 {instance_name} 迭代{iteration}")
        
        # 显示最终统计
        stats = manager.get_pool_stats()
        print(f"\n最终统计:")
        print(f"  总实例: {stats['total_instances']}")
        print(f"  总迭代: {stats['total_iterations']}")
        print(f"  实例列表: {stats['instances']}")
        
        # 显示第一个实例的完整数据
        if stats['instances']:
            first_instance = stats['instances'][0]
            instance_summary = manager.get_instance_summary(first_instance)
            print(f"\n{first_instance} 完整数据:")
            if instance_summary and "problem" in instance_summary:
                problem_preview = instance_summary["problem"][:100] + "..." if len(instance_summary["problem"]) > 100 else instance_summary["problem"]
                print(f"  问题: {problem_preview}")
            
            for key, value in instance_summary.items():
                if key != "problem" and key.isdigit():
                    print(f"  迭代{key}: {value.get('approach_summary', 'N/A') if isinstance(value, dict) else str(value)[:50]}")


def main():
    """主测试函数"""
    print("🧪 TrajExtractor和TrajPoolManager集成测试")
    print("=" * 60)
    
    try:
        test_real_data_extraction()
        test_multiple_iterations()
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()