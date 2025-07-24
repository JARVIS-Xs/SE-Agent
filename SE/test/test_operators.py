#!/usr/bin/env python3
"""
测试 SE 算子系统的完整功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from SE.operators import list_operators, create_operator


def test_all_operators():
    """测试所有已注册的算子"""
    
    print("=== 测试 SE 算子系统 ===")
    
    # 1. 列出所有算子
    operators = list_operators()
    print(f"已注册的算子: {operators}")
    
    expected_operators = ["traj_pool_summary", "alternative_strategy"]
    for op_name in expected_operators:
        if op_name not in operators:
            print(f"❌ {op_name} 算子未注册")
            return False
    
    print("✅ 所有期望的算子都已注册")
    
    # 2. 测试算子创建
    config = {
        "operator_models": {
            "name": "openai/deepseek-chat",
            "temperature": 0.0
        }
    }
    
    test_workspace = "/home/uaih3k9x/630_swe/SE/trajectories/test_20250714_151848"
    
    for op_name in expected_operators:
        print(f"\n--- 测试 {op_name} 算子 ---")
        
        # 创建算子实例
        operator = create_operator(op_name, config)
        if not operator:
            print(f"❌ 创建 {op_name} 算子失败")
            continue
        
        print(f"✅ 算子创建成功: {operator.get_name()}")
        print(f"📝 策略前缀: {operator.get_strategy_prefix()}")
        
        # 测试算子处理
        try:
            result = operator.process(
                workspace_dir=test_workspace,
                current_iteration=2,
                num_workers=1
            )
            
            if result and result.get('instance_templates_dir'):
                print(f"✅ {op_name} 处理成功")
                print(f"📤 输出目录: {result['instance_templates_dir']}")
                
                # 检查生成的文件
                templates_path = Path(result['instance_templates_dir'])
                if templates_path.exists():
                    yaml_files = list(templates_path.glob("*.yaml"))
                    print(f"📄 生成文件: {len(yaml_files)} 个")
                    
                    if yaml_files:
                        # 显示第一个文件的内容摘要
                        with open(yaml_files[0], 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取策略内容预览
                        lines = content.split('\n')
                        strategy_started = False
                        strategy_lines = []
                        
                        for line in lines:
                            if operator.get_strategy_prefix() in line:
                                strategy_started = True
                                continue
                            if strategy_started and line.strip():
                                strategy_lines.append(line.strip())
                                if len(strategy_lines) >= 3:  # 只显示前3行
                                    break
                        
                        print(f"📋 策略内容预览:")
                        for line in strategy_lines:
                            print(f"  {line}")
                        if len(strategy_lines) >= 3:
                            print("  ...")
                else:
                    print(f"⚠️ 输出目录不存在: {templates_path}")
            else:
                print(f"❌ {op_name} 处理失败")
                
        except Exception as e:
            print(f"❌ {op_name} 测试出错: {e}")
    
    print(f"\n🎯 测试完成")
    return True


def show_operator_comparison():
    """显示两个算子的功能对比"""
    
    print("\n=== 算子功能对比 ===")
    
    comparison = {
        "traj_pool_summary": {
            "功能": "分析所有历史失败尝试，识别系统性盲区和风险点",
            "输入": "所有历史迭代数据",
            "输出": "风险感知指导 (RISK-AWARE PROBLEM SOLVING GUIDANCE)",
            "适用场景": "已有多次尝试，需要综合分析"
        },
        "alternative_strategy": {
            "功能": "基于最近一次失败生成截然不同的替代方案",
            "输入": "最近一次失败尝试数据",
            "输出": "替代解决策略 (ALTERNATIVE SOLUTION STRATEGY)",
            "适用场景": "刚失败一次，需要不同方向的尝试"
        }
    }
    
    for op_name, details in comparison.items():
        print(f"\n📊 {op_name}:")
        for key, value in details.items():
            print(f"  {key}: {value}")
    
    print(f"\n💡 使用建议:")
    print(f"  - 迭代2: 使用 alternative_strategy (基于迭代1的失败)")
    print(f"  - 迭代3+: 使用 traj_pool_summary (综合分析所有历史)")


if __name__ == "__main__":
    success = test_all_operators()
    
    if success:
        show_operator_comparison()
        print("\n🎉 SE 算子系统测试通过！")
    else:
        print("\n⚠️ SE 算子系统测试失败")