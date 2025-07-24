#!/usr/bin/env python3
"""
修复现有的traj.pool文件，添加真实数据
"""

import sys
import json
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.traj_extractor import TrajExtractor
from core.utils.traj_pool_manager import TrajPoolManager


def fix_traj_pool(base_dir: str):
    """
    修复指定目录下的traj.pool文件
    
    Args:
        base_dir: 包含iteration目录和traj.pool的基础目录
    """
    base_path = Path(base_dir)
    pool_path = base_path / "traj.pool"
    
    if not base_path.exists():
        print(f"❌ 目录不存在: {base_path}")
        return
    
    if not pool_path.exists():
        print(f"❌ traj.pool文件不存在: {pool_path}")
        return
    
    print(f"🔧 修复轨迹池: {pool_path}")
    
    # 备份原文件
    backup_path = pool_path.with_suffix('.pool.backup')
    try:
        import shutil
        shutil.copy2(pool_path, backup_path)
        print(f"📁 备份创建: {backup_path}")
    except Exception as e:
        print(f"⚠️ 备份失败: {e}")
    
    # 创建新的管理器和提取器
    manager = TrajPoolManager(str(pool_path))
    extractor = TrajExtractor()
    
    # 重新初始化池
    manager.initialize_pool()
    
    # 查找所有iteration目录
    iteration_dirs = []
    for item in base_path.iterdir():
        if item.is_dir() and item.name.startswith('iteration_'):
            try:
                iteration_num = int(item.name.split('_')[1])
                iteration_dirs.append((iteration_num, item))
            except (ValueError, IndexError):
                continue
    
    iteration_dirs.sort(key=lambda x: x[0])  # 按迭代次数排序
    
    print(f"📊 找到 {len(iteration_dirs)} 个迭代目录")
    
    total_instances = 0
    total_iterations = 0
    
    # 处理每个迭代
    for iteration_num, iteration_dir in iteration_dirs:
        print(f"\n🔄 处理迭代 {iteration_num}: {iteration_dir}")
        
        # 提取数据
        instance_data_list = extractor.extract_instance_data_from_directory(iteration_dir)
        
        if instance_data_list:
            for instance_name, problem, trajectory_content, prediction_content in instance_data_list:
                # 添加到池
                manager.add_iteration_summary(
                    instance_name=instance_name,
                    iteration=iteration_num,
                    trajectory_content=trajectory_content,
                    prediction_content=prediction_content,
                    problem=problem
                )
                print(f"  ✅ 添加: {instance_name}")
                total_iterations += 1
            
            total_instances += len(instance_data_list)
        else:
            print(f"  ⚠️ 迭代 {iteration_num} 没有找到有效数据")
    
    # 显示最终结果
    final_stats = manager.get_pool_stats()
    print(f"\n🎯 修复完成:")
    print(f"  总实例: {final_stats['total_instances']}")
    print(f"  总迭代: {final_stats['total_iterations']}")
    print(f"  实例列表: {final_stats['instances']}")
    
    # 显示文件大小
    try:
        file_size = pool_path.stat().st_size
        print(f"  文件大小: {file_size:,} 字节")
    except Exception as e:
        print(f"  文件大小获取失败: {e}")
    
    # 显示第一个实例的示例
    if final_stats['instances']:
        first_instance = final_stats['instances'][0]
        instance_summary = manager.get_instance_summary(first_instance)
        print(f"\n📝 {first_instance} 示例:")
        
        if instance_summary and "problem" in instance_summary:
            problem_preview = instance_summary["problem"][:100] + "..." if len(instance_summary["problem"]) > 100 else instance_summary["problem"]
            print(f"  问题: {problem_preview}")
        
        for key, value in instance_summary.items():
            if key != "problem" and key.isdigit():
                if isinstance(value, dict):
                    approach = value.get('approach_summary', 'N/A')
                    strategy = value.get('strategy', 'N/A')
                    print(f"  迭代{key}: {approach} (策略: {strategy})")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='修复现有的traj.pool文件')
    parser.add_argument('directory', 
                        default='/home/uaih3k9x/630_swe/SE/trajectories/test_20250714_142331',
                        nargs='?',
                        help='包含traj.pool和iteration目录的基础目录')
    
    args = parser.parse_args()
    
    print("🔧 Traj Pool修复工具")
    print("=" * 50)
    print(f"目标目录: {args.directory}")
    
    try:
        fix_traj_pool(args.directory)
        print("\n✅ 修复完成!")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()