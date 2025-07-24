#!/usr/bin/env python3
"""
测试LLM集成到trajectory pool manager的功能
"""

import sys
import os
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.utils.llm_client import LLMClient, TrajectorySummarizer
from core.utils.traj_pool_manager import TrajPoolManager

def test_llm_integration():
    """测试LLM集成功能"""
    
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
    
    print("🧪 测试LLM客户端创建...")
    try:
        llm_client = LLMClient.from_se_config(se_config, use_operator_model=True)
        print(f"✅ LLM客户端创建成功: {llm_client.config['name']}")
    except Exception as e:
        print(f"❌ LLM客户端创建失败: {e}")
        return
    
    print("\n🧪 测试轨迹池管理器...")
    try:
        # 创建临时轨迹池
        pool_path = "/tmp/test_traj_pool.json"
        traj_pool_manager = TrajPoolManager(pool_path, llm_client)
        traj_pool_manager.initialize_pool()
        print(f"✅ 轨迹池管理器创建成功: {pool_path}")
    except Exception as e:
        print(f"❌ 轨迹池管理器创建失败: {e}")
        return
    
    print("\n🧪 测试轨迹总结...")
    try:
        # 模拟轨迹数据
        trajectory_content = """
        {
            "history": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Fix the quaternion rotation matrix bug"},
                {"role": "assistant", "content": "I'll analyze the quaternion.py file..."},
                {"role": "user", "content": "Good, what did you find?"},
                {"role": "assistant", "content": "The issue is with the sign of sin(x) in the rotation matrix"}
            ]
        }
        """
        
        prediction_content = """
        The bug was in the to_rotation_matrix() method where one of the sin(x) terms 
        should be negative. I fixed it by changing the sign in the matrix construction.
        """
        
        summary = traj_pool_manager.summarize_trajectory(
            trajectory_content, prediction_content, 1
        )
        
        print(f"✅ 轨迹总结成功:")
        print(f"  方法总结: {summary.get('approach_summary', 'N/A')}")
        print(f"  修改文件: {summary.get('modified_files', 'N/A')}")
        print(f"  关键变化: {summary.get('key_changes', 'N/A')}")
        print(f"  是否为备用: {summary.get('meta', {}).get('is_fallback', False)}")
        
    except Exception as e:
        print(f"❌ 轨迹总结失败: {e}")
    
    print("\n🧪 测试添加迭代总结...")
    try:
        traj_pool_manager.add_iteration_summary(
            instance_name="test-instance",
            iteration=1,
            trajectory_content=trajectory_content,
            prediction_content=prediction_content,
            problem="Fix quaternion rotation matrix bug"
        )
        print("✅ 迭代总结添加成功")
        
        # 检查池统计
        stats = traj_pool_manager.get_pool_stats()
        print(f"  池统计: {stats}")
        
    except Exception as e:
        print(f"❌ 迭代总结添加失败: {e}")
    
    # 清理
    try:
        os.remove(pool_path)
        print(f"\n🧹 清理临时文件: {pool_path}")
    except:
        pass

if __name__ == "__main__":
    test_llm_integration()