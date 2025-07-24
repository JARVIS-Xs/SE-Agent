#!/usr/bin/env python3
"""
测试轨迹池和prompt系统的独立脚本
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.traj_pool_manager import TrajPoolManager
from core.utils.traj_summarizer import TrajSummarizer


def test_traj_summarizer():
    """测试轨迹总结器"""
    print("=== 测试TrajSummarizer ===")
    
    summarizer = TrajSummarizer()
    
    # 模拟轨迹和预测数据
    mock_trajectory = {
        "trajectory": [
            {"action": "str_replace", "observation": "File modified"},
            {"action": "bash", "observation": "Test passed"}
        ],
        "info": {"exit_status": "submission"}
    }
    
    mock_prediction = {
        "instance_id": "test_123", 
        "model_patch": "some patch content",
        "reasoning": "solution approach"
    }
    
    import json
    trajectory_content = json.dumps(mock_trajectory, indent=2)
    prediction_content = json.dumps(mock_prediction, indent=2)
    
    print("1. System Prompt:")
    print(summarizer.get_system_prompt()[:200] + "...")
    
    print("\n2. User Prompt:")
    user_prompt = summarizer.format_user_prompt(trajectory_content, prediction_content)
    print(user_prompt[:300] + "...")
    
    print("\n3. Fallback Summary:")
    fallback = summarizer.create_fallback_summary(trajectory_content, prediction_content, 1)
    print(json.dumps(fallback, indent=2))
    
    print("\n4. Response Validation:")
    is_valid = summarizer.validate_response_format(fallback)
    print(f"Fallback summary is valid: {is_valid}")


def test_traj_pool_manager():
    """测试轨迹池管理器"""
    print("\n=== 测试TrajPoolManager ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        pool_path = os.path.join(temp_dir, "test_traj.pool")
        manager = TrajPoolManager(pool_path)
        
        print(f"1. 初始化轨迹池: {pool_path}")
        manager.initialize_pool()
        
        print("2. 添加测试数据")
        # 模拟数据
        test_instances = [
            ("sphinx-doc__sphinx-8548", "模拟轨迹内容1", "模拟预测内容1"),
            ("sphinx-doc__sphinx-8551", "模拟轨迹内容2", "模拟预测内容2")
        ]
        
        for instance_name, traj_content, pred_content in test_instances:
            for iteration in [1, 2]:
                manager.add_iteration_summary(
                    instance_name=instance_name,
                    iteration=iteration,
                    trajectory_content=traj_content,
                    prediction_content=pred_content
                )
                print(f"   添加: {instance_name} 迭代{iteration}")
        
        print("3. 轨迹池统计")
        stats = manager.get_pool_stats()
        print(f"   总实例数: {stats['total_instances']}")
        print(f"   总迭代数: {stats['total_iterations']}")
        print(f"   实例列表: {stats['instances']}")
        
        print("4. 获取特定实例总结")
        instance_summary = manager.get_instance_summary("sphinx-doc__sphinx-8548")
        if instance_summary:
            print(f"   sphinx-doc__sphinx-8548 有 {len(instance_summary)} 次迭代")
            for iter_num, summary in instance_summary.items():
                approach = summary.get('approach_summary', 'N/A') if isinstance(summary, dict) else str(summary)[:50]
                print(f"     迭代{iter_num}: {approach}")
        
        print(f"5. 池文件内容预览")
        pool_data = manager.load_pool()
        print(f"   文件大小: {len(str(pool_data))} 字符")
        
        # 显示第一个实例的第一次迭代作为示例
        if pool_data:
            first_instance = list(pool_data.keys())[0]
            first_iteration = list(pool_data[first_instance].keys())[0]
            first_summary = pool_data[first_instance][first_iteration]
            print(f"   示例总结: {first_instance} 迭代{first_iteration}")
            if isinstance(first_summary, dict):
                print(f"     策略: {first_summary.get('strategy', 'N/A')}")
                print(f"     技术: {first_summary.get('specific_techniques', 'N/A')}")


def main():
    """主测试函数"""
    print("🧪 轨迹池和Prompt系统测试")
    print("=" * 50)
    
    try:
        test_traj_summarizer()
        test_traj_pool_manager()
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()