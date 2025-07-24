#!/usr/bin/env python3
"""
SE框架统一数据接口测试脚本

测试统一的数据管理系统，包括：
- InstanceDataManager核心功能
- 四种标准数据格式访问
- 轨迹池数据获取
- 数据完整性验证
- 向后兼容性检查
"""

import sys
import tempfile
import os
import json
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils.instance_data_manager import InstanceDataManager, InstanceData
from core.utils.traj_pool_manager import TrajPoolManager
from core.utils.traj_extractor import TrajExtractor
from core.utils.llm_client import LLMClient


def create_test_instance(temp_dir: str, instance_name: str) -> str:
    """创建测试实例数据"""
    instance_dir = Path(temp_dir) / instance_name
    instance_dir.mkdir(exist_ok=True)
    
    # 创建.problem文件
    with open(instance_dir / f"{instance_name}.problem", 'w', encoding='utf-8') as f:
        f.write("Fix bug in sphinx documentation generation when handling None docstrings")
    
    # 创建.tra文件
    with open(instance_dir / f"{instance_name}.tra", 'w', encoding='utf-8') as f:
        f.write('{"step1": "analyze", "step2": "fix", "step3": "test"}')
    
    # 创建.patch文件 (优先于.pred)
    with open(instance_dir / f"{instance_name}.patch", 'w', encoding='utf-8') as f:
        f.write("diff --git a/file.py b/file.py\n+if docstring is None:\n+    return []")
    
    # 创建.pred文件 (应该被忽略)
    with open(instance_dir / f"{instance_name}.pred", 'w', encoding='utf-8') as f:
        f.write("This should be ignored in favor of .patch")
    
    # 创建.traj文件
    with open(instance_dir / f"{instance_name}.traj", 'w', encoding='utf-8') as f:
        f.write("Full trajectory content here...")
    
    return str(instance_dir)


def test_instance_data_manager():
    """测试InstanceDataManager核心功能"""
    print("1️⃣ 测试InstanceDataManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试实例
        instance_path = create_test_instance(temp_dir, "test-instance")
        
        # 测试数据管理器
        manager = InstanceDataManager()
        instance_data = manager.get_instance_data(instance_path)
        
        # 验证数据完整性
        completeness = manager.validate_instance_completeness(instance_data)
        
        print(f"  ✅ 实例数据加载: {instance_data.instance_name}")
        print(f"  ✅ 完整性验证: {completeness['completeness_score']}%")
        
        # 验证.patch优先于.pred
        if "diff --git" in instance_data.patch_content:
            print(f"  ✅ 正确使用.patch文件")
        else:
            print(f"  ❌ 错误使用.pred文件")
            return False
        
        return True


def test_four_core_formats():
    """测试四种核心数据格式"""
    print("2️⃣ 测试四种核心数据格式...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instance_path = create_test_instance(temp_dir, "format-test")
        
        manager = InstanceDataManager()
        instance_data = manager.get_instance_data(instance_path)
        
        # 1. Problem Description
        if instance_data.problem_description:
            print(f"  ✅ Problem Description: {len(instance_data.problem_description)} 字符")
        else:
            print(f"  ❌ Problem Description 缺失")
            return False
        
        # 2. TRA (压缩轨迹)
        if instance_data.tra_content:
            print(f"  ✅ TRA Content: {len(instance_data.tra_content)} 字符")
        else:
            print(f"  ❌ TRA Content 缺失")
            return False
        
        # 3. PATCH (预测结果)
        if instance_data.patch_content:
            print(f"  ✅ PATCH Content: {len(instance_data.patch_content)} 字符")
        else:
            print(f"  ❌ PATCH Content 缺失")
            return False
        
        # 4. TRAJ (原始轨迹)
        if instance_data.traj_content:
            print(f"  ✅ TRAJ Content: {len(instance_data.traj_content)} 字符")
        else:
            print(f"  ⚠️ TRAJ Content 缺失 (可选)")
        
        return True


def test_trajectory_pool():
    """测试轨迹池数据管理"""
    print("3️⃣ 测试轨迹池数据管理...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建轨迹池
        pool_path = os.path.join(temp_dir, "test.pool")
        
        # 创建模拟的LLM客户端（如果可用）
        llm_client = None
        try:
            test_config = {
                "model": {
                    "name": "openai/deepseek-chat",
                    "api_base": "http://publicshare.a.pinggy.link",
                    "api_key": "EMPTY",
                    "max_output_tokens": 1000
                }
            }
            llm_client = LLMClient.from_se_config(test_config)
            print(f"  ✅ LLM客户端初始化成功")
        except Exception as e:
            print(f"  ⚠️ LLM客户端不可用，使用备用模式: {e}")
        
        pool_manager = TrajPoolManager(pool_path, llm_client)
        pool_manager.initialize_pool()
        
        # 添加测试数据
        pool_manager.add_iteration_summary(
            instance_name="test-instance",
            iteration=1,
            trajectory_content='{"test": "trajectory"}',
            patch_content="test patch content",
            problem_description="Test problem description"
        )
        
        # 测试数据获取
        manager = InstanceDataManager()
        pool_data = manager.get_traj_pool_data(pool_path, "test-instance")
        
        if pool_data:
            print(f"  ✅ 轨迹池数据获取成功")
            print(f"  ✅ 包含数据: {list(pool_data.keys())}")
            
            # 测试特定迭代获取
            iter_summary = manager.get_instance_iteration_summary(pool_path, "test-instance", 1)
            if iter_summary:
                print(f"  ✅ 迭代数据获取成功")
            else:
                print(f"  ❌ 迭代数据获取失败")
                return False
        else:
            print(f"  ❌ 轨迹池数据获取失败")
            return False
        
        return True


def test_backward_compatibility():
    """测试向后兼容性"""
    print("4️⃣ 测试向后兼容性...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建多个测试实例
        for i in range(3):
            create_test_instance(temp_dir, f"compat-test-{i+1:03d}")
        
        extractor = TrajExtractor()
        
        # 测试旧接口
        legacy_data = extractor.extract_instance_data(temp_dir)
        print(f"  ✅ 旧接口提取: {len(legacy_data)} 个实例")
        
        # 测试新接口
        structured_data = extractor.extract_instances_structured(temp_dir)
        print(f"  ✅ 新接口提取: {len(structured_data)} 个实例")
        
        # 验证一致性
        if len(legacy_data) == len(structured_data):
            print(f"  ✅ 新旧接口数据一致")
        else:
            print(f"  ❌ 新旧接口数据不一致")
            return False
        
        return True


def test_operator_integration():
    """测试Operator集成模式"""
    print("5️⃣ 测试Operator集成模式...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instance_path = create_test_instance(temp_dir, "operator-test")
        
        # 模拟Operator的标准数据访问模式
        manager = InstanceDataManager()
        
        # 获取实例数据
        instance_data = manager.get_instance_data(instance_path)
        
        # 访问四种核心数据
        problem = instance_data.problem_description
        tra_data = instance_data.tra_content
        patch_data = instance_data.patch_content
        traj_data = instance_data.traj_content
        
        print(f"  ✅ Problem访问: {'成功' if problem else '失败'}")
        print(f"  ✅ TRA访问: {'成功' if tra_data else '失败'}")
        print(f"  ✅ Patch访问: {'成功' if patch_data else '失败'}")
        print(f"  ✅ Traj访问: {'成功' if traj_data else '失败'}")
        
        # 验证数据完整性
        validation = manager.validate_instance_completeness(instance_data)
        print(f"  ✅ 数据完整性: {validation['completeness_score']}%")
        
        return validation['completeness_score'] >= 100


def main():
    """主测试函数"""
    print("🧪 SE框架统一数据接口测试")
    print("=" * 50)
    
    tests = [
        ("InstanceDataManager核心功能", test_instance_data_manager),
        ("四种核心数据格式", test_four_core_formats),
        ("轨迹池数据管理", test_trajectory_pool),
        ("向后兼容性", test_backward_compatibility),
        ("Operator集成模式", test_operator_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 30)
        try:
            success = test_func()
            results.append(success)
            print(f"{'✅ 通过' if success else '❌ 失败'}")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    # 测试总结
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试总结")
    print("=" * 50)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！统一数据接口完全可用。")
        return True
    else:
        print("⚠️ 存在失败测试，请检查系统配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)