#!/usr/bin/env python3
"""
使用实际轨迹数据测试LLM集成
"""

import sys
import os
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.llm_client import LLMClient, TrajectorySummarizer
from core.utils.traj_pool_manager import TrajPoolManager

def test_with_real_trajectory():
    """使用实际轨迹数据测试"""
    
    # 模拟SE配置
    se_config = {
        "model": {
            "name": "openai/deepseek-chat",
            "api_base": "http://publicshare.a.pinggy.link", 
            "api_key": "EMPTY",
            "max_input_tokens": 128000,
            "max_output_tokens": 64000
        },
        "operator_models": {
            "name": "openai/deepseek-chat",
            "api_base": "http://publicshare.a.pinggy.link",
            "api_key": "EMPTY", 
            "max_input_tokens": 128000,
            "max_output_tokens": 64000
        }
    }
    
    print("🧪 使用实际轨迹数据测试LLM集成...")
    
    try:
        # 创建LLM客户端
        llm_client = LLMClient.from_se_config(se_config, use_operator_model=True)
        print(f"✅ LLM客户端创建成功: {llm_client.config['name']}")
        
        # 创建轨迹池管理器
        pool_path = "/tmp/real_traj_test_pool.json"
        traj_pool_manager = TrajPoolManager(pool_path, llm_client)
        traj_pool_manager.initialize_pool()
        
        # 读取实际轨迹数据
        traj_dir = "trajectories/test_20250714_143856"
        iteration_dirs = ["iteration_1", "iteration_2"]
        
        for i, iter_dir in enumerate(iteration_dirs, 1):
            print(f"\n🔍 处理{iter_dir}...")
            
            # 轨迹文件路径
            tra_file = f"{traj_dir}/{iter_dir}/sphinx-doc__sphinx-10435/sphinx-doc__sphinx-10435.tra"
            pred_file = f"{traj_dir}/{iter_dir}/sphinx-doc__sphinx-10435/sphinx-doc__sphinx-10435.pred"
            
            # 检查文件是否存在
            if not os.path.exists(tra_file):
                print(f"❌ 轨迹文件不存在: {tra_file}")
                continue
                
            if not os.path.exists(pred_file):
                print(f"❌ 预测文件不存在: {pred_file}")
                continue
            
            # 读取文件内容
            with open(tra_file, 'r', encoding='utf-8') as f:
                trajectory_content = f.read()
            
            with open(pred_file, 'r', encoding='utf-8') as f:
                prediction_content = f.read()
            
            print(f"📊 轨迹内容长度: {len(trajectory_content)} 字符")
            print(f"📊 预测内容长度: {len(prediction_content)} 字符")
            
            # 进行LLM总结
            summary = traj_pool_manager.summarize_trajectory(
                trajectory_content, prediction_content, i
            )
            
            print(f"✅ 第{i}次迭代LLM总结:")
            print(f"  方法总结: {summary.get('approach_summary', 'N/A')}")
            print(f"  修改文件: {summary.get('modified_files', 'N/A')}")
            print(f"  关键变化: {summary.get('key_changes', 'N/A')}")
            print(f"  策略: {summary.get('strategy', 'N/A')}")
            print(f"  技术: {summary.get('specific_techniques', 'N/A')}")
            print(f"  是否为备用: {summary.get('meta', {}).get('is_fallback', False)}")
            
            # 添加到轨迹池
            problem = "Incorrect result with Quaternion.to_rotation_matrix()"
            traj_pool_manager.add_iteration_summary(
                instance_name="sphinx-doc__sphinx-10435",
                iteration=i,
                trajectory_content=trajectory_content,
                prediction_content=prediction_content,
                problem=problem
            )
        
        # 显示最终统计
        stats = traj_pool_manager.get_pool_stats()
        print(f"\n📊 最终轨迹池统计: {stats}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理
    try:
        os.remove(pool_path)
        print(f"\n🧹 清理临时文件: {pool_path}")
    except:
        pass

if __name__ == "__main__":
    test_with_real_trajectory()