#!/usr/bin/env python3
"""
SE框架模拟算子测试脚本

由于具体算子尚未实现，本脚本模拟测试算子的标准数据访问模式，
验证数据接口的完整性和可用性。
"""

import sys
import tempfile
import os
import json
from pathlib import Path

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils.instance_data_manager import InstanceDataManager
from core.utils.traj_pool_manager import TrajPoolManager


class MockOperator:
    """模拟算子，展示标准数据访问模式"""
    
    def __init__(self, name: str):
        self.name = name
        self.manager = InstanceDataManager()
    
    def process_instance(self, instance_path: str, traj_pool_path: str = None) -> dict:
        """模拟算子处理单个实例的标准流程"""
        
        print(f"🔧 {self.name} 处理实例: {Path(instance_path).name}")
        
        # 1. 获取实例完整数据
        instance_data = self.manager.get_instance_data(instance_path)
        
        # 2. 访问四种核心数据格式
        problem = instance_data.problem_description
        tra_content = instance_data.tra_content
        patch_content = instance_data.patch_content
        traj_content = instance_data.traj_content
        
        print(f"  📝 问题描述: {'✅' if problem else '❌'} ({len(problem) if problem else 0} 字符)")
        print(f"  📊 TRA数据: {'✅' if tra_content else '❌'} ({len(tra_content) if tra_content else 0} 字符)")
        print(f"  🔄 PATCH数据: {'✅' if patch_content else '❌'} ({len(patch_content) if patch_content else 0} 字符)")
        print(f"  📋 TRAJ数据: {'✅' if traj_content else '❌'} ({len(traj_content) if traj_content else 0} 字符)")
        
        # 3. 获取轨迹池历史数据 (如果可用)
        pool_data = None
        if traj_pool_path:
            instance_name = instance_data.instance_name
            pool_data = self.manager.get_traj_pool_data(traj_pool_path, instance_name)
            if pool_data:
                iterations = [k for k in pool_data.keys() if k.isdigit()]
                print(f"  🏊 轨迹池数据: ✅ ({len(iterations)} 个迭代)")
            else:
                print(f"  🏊 轨迹池数据: ❌")
        
        # 4. 数据完整性验证
        completeness = self.manager.validate_instance_completeness(instance_data)
        print(f"  📈 数据完整性: {completeness['completeness_score']}%")
        
        # 5. 模拟算子逻辑
        result = self._mock_operator_logic(problem, tra_content, patch_content, pool_data)
        
        return {
            "instance_name": instance_data.instance_name,
            "completeness": completeness['completeness_score'],
            "processing_result": result,
            "has_pool_data": pool_data is not None
        }
    
    def _mock_operator_logic(self, problem: str, tra_content: str, patch_content: str, pool_data: dict) -> str:
        """模拟算子的核心逻辑"""
        
        if not problem or not tra_content or not patch_content:
            return "数据不完整，无法处理"
        
        # 模拟不同类型算子的处理逻辑
        if "crossover" in self.name.lower():
            return f"基于历史轨迹生成交叉策略 (问题长度: {len(problem)}, 轨迹数据: {len(tra_content)})"
        elif "conclusion" in self.name.lower():
            return f"基于多次尝试生成收敛指导 (轨迹池数据: {'有' if pool_data else '无'})"
        elif "summary" in self.name.lower():
            iterations = len([k for k in pool_data.keys() if k.isdigit()]) if pool_data else 0
            return f"基于{iterations}次历史尝试生成风险分析"
        else:
            return f"通用策略生成 (数据完整性检查通过)"


def create_mock_workspace(temp_dir: str) -> tuple:
    """创建模拟的工作空间"""
    
    workspace = Path(temp_dir)
    
    # 创建多个实例
    instances = []
    for i in range(3):
        instance_name = f"mock-instance-{i+1:03d}"
        instance_dir = workspace / instance_name
        instance_dir.mkdir(exist_ok=True)
        
        # 创建.problem文件
        with open(instance_dir / f"{instance_name}.problem", 'w', encoding='utf-8') as f:
            f.write(f"Fix issue #{i+1} in the codebase documentation system")
        
        # 创建.tra文件
        tra_data = {
            "compressed_trajectory": f"instance_{i+1}_trajectory_data",
            "steps": ["analyze", "implement", "test"],
            "result": "completed"
        }
        with open(instance_dir / f"{instance_name}.tra", 'w', encoding='utf-8') as f:
            json.dump(tra_data, f, indent=2)
        
        # 创建.patch文件
        with open(instance_dir / f"{instance_name}.patch", 'w', encoding='utf-8') as f:
            f.write(f"diff --git a/file{i+1}.py b/file{i+1}.py\n+# Fix for issue {i+1}\n+fixed_code_here()")
        
        # 创建.traj文件
        with open(instance_dir / f"{instance_name}.traj", 'w', encoding='utf-8') as f:
            f.write(f"Full trajectory for instance {i+1}...\nDetailed execution log here...")
        
        instances.append(str(instance_dir))
    
    # 创建轨迹池
    pool_path = workspace / "mock.pool"
    pool_data = {}
    
    for i, instance_name in enumerate([f"mock-instance-{i+1:03d}" for i in range(3)]):
        pool_data[instance_name] = {
            "problem": f"Fix issue #{i+1} in the codebase documentation system",
            "1": {
                "approach_summary": f"Attempted to fix issue {i+1} using method A",
                "modified_files": [f"/path/to/file{i+1}.py"],
                "strategy": f"Direct modification approach for issue {i+1}",
                "tools_used": ["str_replace_editor", "bash"],
                "reasoning_pattern": "analyze -> implement -> test"
            },
            "2": {
                "approach_summary": f"Alternative approach for issue {i+1} using method B", 
                "modified_files": [f"/path/to/file{i+1}.py", f"/path/to/config{i+1}.json"],
                "strategy": f"Configuration-based approach for issue {i+1}",
                "tools_used": ["str_replace_editor", "find", "grep"],
                "reasoning_pattern": "research -> configure -> validate"
            }
        }
    
    with open(pool_path, 'w', encoding='utf-8') as f:
        json.dump(pool_data, f, indent=2, ensure_ascii=False)
    
    return instances, str(pool_path)


def test_crossover_operator():
    """测试交叉算子的数据访问模式"""
    print("1️⃣ 测试Crossover算子数据访问模式")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instances, pool_path = create_mock_workspace(temp_dir)
        
        operator = MockOperator("CrossoverOperator")
        results = []
        
        for instance_path in instances:
            result = operator.process_instance(instance_path, pool_path)
            results.append(result)
        
        # 验证结果
        success = all(r['completeness'] >= 100 for r in results)
        print(f"  {'✅' if success else '❌'} 所有实例数据完整性: {success}")
        
        return success


def test_conclusion_operator():
    """测试结论算子的数据访问模式"""
    print("2️⃣ 测试Conclusion算子数据访问模式")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instances, pool_path = create_mock_workspace(temp_dir)
        
        operator = MockOperator("ConclusionOperator")
        results = []
        
        for instance_path in instances:
            result = operator.process_instance(instance_path, pool_path)
            results.append(result)
        
        # 验证轨迹池数据访问
        success = all(r['has_pool_data'] for r in results)
        print(f"  {'✅' if success else '❌'} 轨迹池数据访问: {success}")
        
        return success


def test_summary_operator():
    """测试总结算子的数据访问模式"""
    print("3️⃣ 测试Summary算子数据访问模式")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instances, pool_path = create_mock_workspace(temp_dir)
        
        operator = MockOperator("SummaryOperator")
        results = []
        
        for instance_path in instances:
            result = operator.process_instance(instance_path, pool_path)
            results.append(result)
            print(f"    处理结果: {result['processing_result']}")
        
        # 验证处理成功
        success = all("历史尝试" in r['processing_result'] for r in results)
        print(f"  {'✅' if success else '❌'} 历史数据分析: {success}")
        
        return success


def test_data_format_standards():
    """测试数据格式标准"""
    print("4️⃣ 测试数据格式标准")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instances, pool_path = create_mock_workspace(temp_dir)
        
        manager = InstanceDataManager()
        format_checks = []
        
        for instance_path in instances:
            instance_data = manager.get_instance_data(instance_path)
            
            # 检查四种核心格式
            checks = {
                "problem_text": isinstance(instance_data.problem_description, str),
                "tra_json": instance_data.tra_content and '{' in instance_data.tra_content,
                "patch_diff": instance_data.patch_content and 'diff --git' in instance_data.patch_content,
                "traj_text": isinstance(instance_data.traj_content, str)
            }
            
            format_checks.append(all(checks.values()))
            print(f"    实例 {instance_data.instance_name}: {checks}")
        
        success = all(format_checks)
        print(f"  {'✅' if success else '❌'} 数据格式标准: {success}")
        
        return success


def test_priority_mechanisms():
    """测试优先级机制"""
    print("5️⃣ 测试文件优先级机制")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        instance_dir = Path(temp_dir) / "priority-test"
        instance_dir.mkdir()
        
        # 创建.patch和.pred文件
        with open(instance_dir / "priority-test.patch", 'w') as f:
            f.write("patch content - should be used")
        
        with open(instance_dir / "priority-test.pred", 'w') as f:
            f.write("pred content - should be ignored")
        
        # 创建.problem文件
        with open(instance_dir / "priority-test.problem", 'w') as f:
            f.write("problem from file")
        
        # 创建.tra文件（含problem描述）
        tra_data = {
            "Trajectory": [
                {"role": "user", "content": [{"text": "<pr_description>\nproblem from trajectory\n</pr_description>"}]}
            ]
        }
        with open(instance_dir / "priority-test.tra", 'w') as f:
            json.dump(tra_data, f)
        
        manager = InstanceDataManager()
        instance_data = manager.get_instance_data(str(instance_dir))
        
        # 验证优先级
        patch_priority = "patch content" in instance_data.patch_content
        problem_priority = instance_data.problem_description == "problem from file"
        
        print(f"    PATCH优先级: {'✅' if patch_priority else '❌'} (.patch > .pred)")
        print(f"    Problem优先级: {'✅' if problem_priority else '❌'} (.problem > trajectory)")
        
        success = patch_priority and problem_priority
        print(f"  {'✅' if success else '❌'} 优先级机制: {success}")
        
        return success


def main():
    """主测试函数"""
    print("🧪 SE框架模拟算子测试")
    print("测试范围: 算子数据访问模式、格式标准、优先级机制")
    print("=" * 60)
    
    tests = [
        ("Crossover算子数据访问", test_crossover_operator),
        ("Conclusion算子数据访问", test_conclusion_operator),
        ("Summary算子数据访问", test_summary_operator),
        ("数据格式标准", test_data_format_standards),
        ("优先级机制", test_priority_mechanisms),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    # 测试总结
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试总结")
    print("=" * 60)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！算子数据访问接口完全可用。")
        return True
    else:
        print("⚠️ 存在失败测试，算子实现需要遵循数据访问标准。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)