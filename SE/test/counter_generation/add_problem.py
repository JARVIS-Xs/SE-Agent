#!/usr/bin/env python
"""
将问题描述添加到filtered_predictions.json文件中

此脚本遍历filtered_predictions.json文件，根据实例ID从SWE-bench数据集获取对应的问题描述，
然后将问题描述添加到filtered_predictions.json的每个条目中。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import glob

# 添加项目根目录到路径以导入sweagent模块
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# 导入SWE-bench相关的函数
from datasets import load_dataset


def get_problem_statements(subset: str = "verified", split: str = "test") -> Dict[str, str]:
    """
    从SWE-bench数据集获取问题描述
    
    Args:
        subset: 数据集子集，可选值为 "lite", "verified", "full"
        split: 数据集分割，可选值为 "dev", "test"
        
    Returns:
        包含实例ID到问题描述映射的字典
    """
    dataset_name = ""
    if subset == "full":
        dataset_name = "princeton-nlp/SWE-Bench"
    elif subset == "verified":
        dataset_name = "princeton-nlp/SWE-Bench_Verified"
    elif subset == "lite":
        dataset_name = "princeton-nlp/SWE-Bench_Lite"
    else:
        raise ValueError(f"不支持的数据集子集: {subset}")
    
    print(f"正在加载数据集: {dataset_name}, 分割: {split}")
    ds = load_dataset(dataset_name, split=split)
    
    # 创建实例ID到问题描述的映射
    problem_statements = {}
    for instance in ds:
        instance_id = instance["instance_id"]
        problem_statement = instance["problem_statement"]
        problem_statements[instance_id] = problem_statement
    
    print(f"从数据集中加载了 {len(problem_statements)} 个问题描述")
    return problem_statements


def update_filtered_predictions(
    filtered_predictions_path: str,
    problem_statements: Dict[str, str],
    output_path: str = None
) -> None:
    """
    更新filtered_predictions.json文件，添加问题描述
    
    Args:
        filtered_predictions_path: filtered_predictions.json的路径
        problem_statements: 实例ID到问题描述的映射
        output_path: 输出文件路径，如果为None则覆盖原文件
    """
    # 读取filtered_predictions.json
    with open(filtered_predictions_path, 'r', encoding='utf-8') as f:
        filtered_predictions = json.load(f)
    
    # 添加问题描述到每个条目
    not_found_instances = []
    updated_count = 0
    for instance_id, instance_data in filtered_predictions.items():
        if instance_id in problem_statements:
            instance_data["problem_statement"] = problem_statements[instance_id]
            updated_count += 1
        else:
            not_found_instances.append(instance_id)
    
    # 报告未找到问题描述的实例
    if not_found_instances:
        print(f"警告: 未找到以下实例的问题描述: {', '.join(not_found_instances)}")
    
    print(f"共更新了 {updated_count} 个实例的问题描述")
    
    # 保存更新后的数据
    if output_path is None:
        output_path = filtered_predictions_path
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_predictions, f, ensure_ascii=False, indent=2)
    
    print(f"已将问题描述添加到 {output_path}")


def main():
    """主函数"""
    # 命令行参数解析
    import argparse
    parser = argparse.ArgumentParser(description="将问题描述添加到pred.json文件并保存为conclusion.json")
    parser.add_argument("--base_path", default="/home/uaih3k9x/swebench/evolve_agent/newest_exp_claude37_30-125",
                        help="基础路径，包含5个文件夹")
    parser.add_argument("--subset", default="verified", choices=["lite", "verified", "full"],
                        help="SWE-bench数据集子集 (默认: verified)")
    parser.add_argument("--split", default="test", choices=["dev", "test"],
                        help="SWE-bench数据集分割 (默认: test)")
    args = parser.parse_args() 
    
    # 从SWE-bench获取问题描述
    problem_statements = get_problem_statements(subset=args.subset, split=args.split)
    
    # 查找所有符合条件的pred.json文件
    # 假设5个文件夹的名称格式为default_1, default_2, ...
    processed_count = 0
    for i in range(1, 6):
        folder_pattern = f"{args.base_path}/default_{i}/*/"
        timestamp_folders = glob.glob(folder_pattern)
        
        for timestamp_folder in timestamp_folders:
            pred_file = os.path.join(timestamp_folder, "preds.json")
            if os.path.exists(pred_file):
                conclusion_file = os.path.join(timestamp_folder, "conclusion.json")
                print(f"处理文件: {pred_file}")
                print(f"输出文件: {conclusion_file}")
                
                # 更新pred.json并保存为conclusion.json
                update_filtered_predictions(pred_file, problem_statements, conclusion_file)
                processed_count += 1
    
    print(f"处理完成，共处理了 {processed_count} 个文件")


if __name__ == "__main__":
    main() 