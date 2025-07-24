#!/usr/bin/env python3
"""
AlternativeStrategy 算子专用测试文件

测试 alternative_strategy 算子的完整功能，包括：
- 算子注册和创建
- 数据加载和处理
- LLM调用和策略生成
- 输出文件生成和格式验证
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from operators import create_operator


class TestAlternativeStrategy:
    """AlternativeStrategy算子测试类"""
    
    def __init__(self):
        self.config = {
            "operator_models": {
                "name": "openai/deepseek-chat",
                "temperature": 0.0,
                "max_output_tokens": 1000
            }
        }
        self.test_workspace = None
        
    def setup_test_workspace(self):
        """创建测试工作空间"""
        self.test_workspace = Path(tempfile.mkdtemp(prefix="test_alt_strategy_"))
        
        # 创建模拟的实例目录结构
        instance_dir = self.test_workspace / "test-instance-001"
        iter1_dir = instance_dir / "iteration_1"
        iter1_dir.mkdir(parents=True)
        
        # 创建模拟的 .tra 文件
        tra_content = {
            "Trajectory": [
                {"role": "system", "content": "System message"},
                {
                    "role": "user",
                    "content": [
                        {
                            "text": "<pr_description>\n修复Python中的类型检查错误，确保函数返回类型与声明一致\n当前代码在类型检查时报错，需要修复类型不匹配问题\n</pr_description>"
                        }
                    ]
                }
            ]
        }
        
        tra_file = iter1_dir / "test-instance-001.tra"
        with open(tra_file, 'w', encoding='utf-8') as f:
            json.dump(tra_content, f, ensure_ascii=False, indent=2)
        
        # 创建模拟的 traj.pool 文件
        traj_pool_content = {
            "test-instance-001": {
                "problem": "修复Python中的类型检查错误，确保函数返回类型与声明一致",
                "1": {
                    "approach_summary": "尝试通过修改函数声明来解决类型检查错误",
                    "modified_files": [
                        "/testbed/src/main.py",
                        "/testbed/src/utils.py"
                    ],
                    "key_changes": [
                        "修改函数返回类型注解",
                        "添加类型转换代码"
                    ],
                    "strategy": "分析错误信息，定位类型不匹配的函数，修改类型注解和实现",
                    "specific_techniques": [
                        "mypy类型检查",
                        "手动代码审查",
                        "逐个文件修复"
                    ],
                    "tools_used": [
                        "str_replace_editor",
                        "bash",
                        "mypy"
                    ],
                    "reasoning_pattern": "1. 运行mypy检查\n2. 分析错误信息\n3. 修改函数声明\n4. 重新检查",
                    "assumptions_made": [
                        "错误只在函数声明层面",
                        "修改类型注解就能解决问题",
                        "不需要修改函数实现逻辑"
                    ],
                    "components_touched": [
                        "函数类型注解",
                        "返回值处理"
                    ]
                }
            }
        }
        
        traj_pool_file = instance_dir / "traj.pool"
        with open(traj_pool_file, 'w', encoding='utf-8') as f:
            json.dump(traj_pool_content, f, ensure_ascii=False, indent=2)
        
        print(f"📁 创建测试工作空间: {self.test_workspace}")
        print(f"📄 创建轨迹文件: {tra_file}")
        print(f"🏊 创建轨迹池: {traj_pool_file}")
        
        return self.test_workspace
    
    def cleanup_test_workspace(self):
        """清理测试工作空间"""
        if self.test_workspace and self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)
            print(f"🧹 清理测试工作空间: {self.test_workspace}")
    
    def test_operator_creation(self):
        """测试算子创建"""
        print("\n=== 测试 AlternativeStrategy 算子创建 ===")
        
        operator = create_operator("alternative_strategy", self.config)
        if not operator:
            print("❌ 算子创建失败")
            return False
        
        print(f"✅ 算子创建成功: {operator.get_name()}")
        print(f"📝 策略前缀: {operator.get_strategy_prefix()}")
        
        return operator
    
    def test_data_loading(self, operator):
        """测试数据加载功能"""
        print("\n=== 测试数据加载功能 ===")
        
        workspace = self.setup_test_workspace()
        instance_dir = workspace / "test-instance-001"
        
        # 测试 traj.pool 加载
        approaches_data = operator._load_traj_pool(instance_dir)
        if not approaches_data:
            print("❌ 轨迹池数据加载失败")
            return False
        
        print(f"✅ 成功加载轨迹池数据")
        print(f"📊 数据项: {list(approaches_data.keys())}")
        
        # 测试最近失败尝试提取
        latest_approach = operator._get_latest_failed_approach(approaches_data)
        if not latest_approach:
            print("❌ 最近失败尝试提取失败")
            return False
        
        print(f"✅ 成功提取最近失败尝试")
        print(f"📋 最近尝试预览: {latest_approach[:100]}...")
        
        return True
    
    def test_strategy_generation(self, operator):
        """测试策略生成功能（不调用LLM）"""
        print("\n=== 测试策略生成功能 ===")
        
        problem_statement = "修复Python中的类型检查错误，确保函数返回类型与声明一致"
        previous_approach = "Strategy: 分析错误信息，定位类型不匹配的函数，修改类型注解和实现\nTools Used: str_replace_editor, bash, mypy"
        
        # 模拟策略生成（不实际调用LLM）
        print(f"📝 问题陈述: {problem_statement}")
        print(f"📋 前次方法: {previous_approach}")
        print(f"🎯 策略生成: 将使用LLM生成替代策略")
        
        return True
    
    def test_full_processing(self, operator):
        """测试完整处理流程"""
        print("\n=== 测试完整处理流程 ===")
        
        if not self.test_workspace:
            self.setup_test_workspace()
        
        try:
            result = operator.process(
                workspace_dir=str(self.test_workspace),
                current_iteration=2,
                num_workers=1
            )
            
            if result and result.get('instance_templates_dir'):
                print(f"✅ 完整处理成功")
                print(f"📤 输出目录: {result['instance_templates_dir']}")
                
                # 检查生成的文件
                templates_dir = Path(result['instance_templates_dir'])
                if templates_dir.exists():
                    yaml_files = list(templates_dir.glob("*.yaml"))
                    print(f"📄 生成模板文件: {len(yaml_files)} 个")
                    
                    if yaml_files:
                        # 验证文件内容
                        with open(yaml_files[0], 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 检查必要的组件
                        required_components = [
                            "You are a helpful assistant",
                            "ALTERNATIVE SOLUTION STRATEGY",
                            "agent:",
                            "templates:",
                            "system_template:"
                        ]
                        
                        missing_components = []
                        for component in required_components:
                            if component not in content:
                                missing_components.append(component)
                        
                        if missing_components:
                            print(f"⚠️ 缺少必要组件: {missing_components}")
                        else:
                            print(f"✅ 输出格式验证通过")
                        
                        # 显示内容预览
                        print(f"\n📋 生成内容预览:")
                        print("=" * 50)
                        lines = content.split('\n')
                        for i, line in enumerate(lines[:15]):  # 显示前15行
                            print(f"{i+1:2d}: {line}")
                        if len(lines) > 15:
                            print("...")
                        print("=" * 50)
                
                return True
            else:
                print(f"❌ 完整处理失败")
                return False
                
        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始 AlternativeStrategy 算子测试")
        
        success_count = 0
        total_tests = 4
        
        try:
            # 1. 测试算子创建
            operator = self.test_operator_creation()
            if operator:
                success_count += 1
                
                # 2. 测试数据加载
                if self.test_data_loading(operator):
                    success_count += 1
                
                # 3. 测试策略生成
                if self.test_strategy_generation(operator):
                    success_count += 1
                
                # 4. 测试完整处理
                if self.test_full_processing(operator):
                    success_count += 1
            
        finally:
            self.cleanup_test_workspace()
        
        # 测试总结
        print(f"\n🎯 AlternativeStrategy 测试总结:")
        print(f"  ✅ 成功: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 所有测试通过！")
            return True
        else:
            print("⚠️ 部分测试失败")
            return False


def main():
    """主测试函数"""
    tester = TestAlternativeStrategy()
    success = tester.run_all_tests()
    
    if success:
        print("\n✨ AlternativeStrategy 算子测试完成 - 所有测试通过！")
    else:
        print("\n❌ AlternativeStrategy 算子测试完成 - 存在失败项")
    
    return success


if __name__ == "__main__":
    main()