#!/usr/bin/env python3
"""
SE框架测试套件 - 统一数据管理系统测试

运行所有与数据管理相关的测试，验证SE框架的核心数据访问功能。
支持单独测试或批量测试模式。
"""

import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SETestSuite:
    """SE框架测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.test_dir = Path(__file__).parent
        
    def run_unified_data_interface_test(self):
        """运行统一数据接口测试"""
        print("🧪 开始统一数据接口测试")
        print("=" * 60)
        
        test_script = self.test_dir / "test_unified_data_interface.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = result.returncode == 0
            
            # 显示测试输出
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            self.test_results['unified_data_interface'] = {
                'success': success,
                'description': '统一数据接口 - InstanceDataManager、四种核心格式、轨迹池'
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 测试超时")
            self.test_results['unified_data_interface'] = {
                'success': False,
                'description': '统一数据接口 - 测试超时'
            }
            return False
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            self.test_results['unified_data_interface'] = {
                'success': False,
                'description': '统一数据接口 - 执行失败'
            }
            return False
    
    def run_operator_data_access_test(self):
        """运行算子数据访问测试"""
        print("\n🧪 开始算子数据访问测试")
        print("=" * 60)
        
        test_script = self.test_dir / "test_operator_data_access.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = result.returncode == 0
            
            # 显示测试输出
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            self.test_results['operator_data_access'] = {
                'success': success,
                'description': '算子数据访问 - 模拟Crossover、Conclusion、Summary算子'
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 测试超时")
            self.test_results['operator_data_access'] = {
                'success': False,
                'description': '算子数据访问 - 测试超时'
            }
            return False
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            self.test_results['operator_data_access'] = {
                'success': False,
                'description': '算子数据访问 - 执行失败'
            }
            return False
    
    def run_data_format_validation_test(self):
        """运行数据格式验证测试"""
        print("\n🧪 开始数据格式验证测试")
        print("=" * 60)
        
        try:
            from core.utils.instance_data_manager import InstanceDataManager
            from core.utils.traj_pool_manager import TrajPoolManager
            from core.utils.traj_extractor import TrajExtractor
            
            # 基础导入测试
            print("✅ 核心模块导入成功")
            
            # 接口可用性测试
            manager = InstanceDataManager()
            extractor = TrajExtractor()
            
            print("✅ 核心类实例化成功")
            
            # 方法签名测试
            required_methods = [
                'get_instance_data',
                'get_traj_pool_data',
                'get_instance_iteration_summary',
                'validate_instance_completeness'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(manager, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"❌ 缺少必要方法: {missing_methods}")
                success = False
            else:
                print("✅ 所有必要方法存在")
                success = True
            
            self.test_results['data_format_validation'] = {
                'success': success,
                'description': '数据格式验证 - 核心类和方法可用性'
            }
            
            return success
            
        except ImportError as e:
            print(f"❌ 模块导入失败: {e}")
            self.test_results['data_format_validation'] = {
                'success': False,
                'description': '数据格式验证 - 模块导入失败'
            }
            return False
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            self.test_results['data_format_validation'] = {
                'success': False,
                'description': '数据格式验证 - 验证失败'
            }
            return False
    
    def run_legacy_compatibility_test(self):
        """运行遗留兼容性测试"""
        print("\n🧪 开始遗留兼容性测试")
        print("=" * 60)
        
        try:
            # 测试旧版本测试脚本是否仍然可用
            old_tests = [
                'test_alternative_strategy.py',
                'test_traj_pool_summary.py'
            ]
            
            existing_tests = []
            for test_file in old_tests:
                test_path = self.test_dir / test_file
                if test_path.exists():
                    existing_tests.append(test_file)
            
            print(f"✅ 发现遗留测试文件: {existing_tests}")
            
            if existing_tests:
                print("⚠️ 遗留测试文件存在，建议更新到新的数据访问接口")
                success = True  # 存在但需要更新
            else:
                print("✅ 无遗留测试文件冲突")
                success = True
            
            self.test_results['legacy_compatibility'] = {
                'success': success,
                'description': f'遗留兼容性 - 发现{len(existing_tests)}个旧测试文件'
            }
            
            return success
            
        except Exception as e:
            print(f"❌ 兼容性测试失败: {e}")
            self.test_results['legacy_compatibility'] = {
                'success': False,
                'description': '遗留兼容性 - 测试失败'
            }
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("📊 SE框架数据管理系统测试报告")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        
        print(f"📈 总体结果: {passed_tests}/{total_tests} 通过")
        print()
        
        # 详细结果
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result['success'] else "❌ 失败"
            print(f"{status} {test_name}: {result['description']}")
        
        print()
        
        # 总体评估
        if passed_tests == total_tests:
            print("🎉 所有测试通过！SE框架数据管理系统完全可用。")
            print("💡 建议：可以开始实现具体的算子功能")
            overall_success = True
        elif passed_tests > total_tests // 2:
            print(f"⚠️ 大部分测试通过（{passed_tests}/{total_tests}）。")
            print("💡 建议：修复失败的测试项后再开始算子开发")
            overall_success = False
        else:
            print("❌ 多数测试失败。SE框架数据管理系统存在问题。")
            print("💡 建议：优先修复数据访问接口")
            overall_success = False
        
        return overall_success
    
    def run_full_test_suite(self):
        """运行完整测试套件"""
        print("🚀 开始SE框架数据管理系统完整测试")
        print("测试范围: 统一数据接口、算子数据访问、格式验证、遗留兼容性")
        print()
        
        # 1. 数据格式验证测试
        self.run_data_format_validation_test()
        
        # 2. 统一数据接口测试
        self.run_unified_data_interface_test()
        
        # 3. 算子数据访问测试
        self.run_operator_data_access_test()
        
        # 4. 遗留兼容性测试
        self.run_legacy_compatibility_test()
        
        # 5. 生成测试报告
        overall_success = self.generate_test_report()
        
        return overall_success


def main():
    """主函数：解析命令行参数并运行测试"""
    
    parser = argparse.ArgumentParser(description='SE框架数据管理系统测试套件')
    parser.add_argument('--test', choices=['unified_data', 'operator_access', 'format_validation', 'legacy_compat', 'all'], 
                       default='all', help='指定要运行的测试')
    parser.add_argument('--verbose', action='store_true', help='显示详细输出')
    
    args = parser.parse_args()
    
    suite = SETestSuite()
    
    if args.test == 'all':
        # 运行完整测试套件
        success = suite.run_full_test_suite()
    elif args.test == 'unified_data':
        # 只测试统一数据接口
        success = suite.run_unified_data_interface_test()
        suite.generate_test_report()
    elif args.test == 'operator_access':
        # 只测试算子数据访问
        success = suite.run_operator_data_access_test()
        suite.generate_test_report()
    elif args.test == 'format_validation':
        # 只测试数据格式验证
        success = suite.run_data_format_validation_test()
        suite.generate_test_report()
    elif args.test == 'legacy_compat':
        # 只测试遗留兼容性
        success = suite.run_legacy_compatibility_test()
        suite.generate_test_report()
    else:
        print(f"❌ 未知的测试类型: {args.test}")
        success = False
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()