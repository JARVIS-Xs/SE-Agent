#!/usr/bin/env python
"""
过滤并保存预测结果的脚本

此脚本从预测文件中过滤出指定ID的预测结果，并将其保存到新文件中。
"""

import json
import os
from pathlib import Path
from typing import Dict, Set, Any


def read_predictions(file_path: str) -> Dict[str, Any]:
    """
    读取并解析预测文件
    
    Args:
        file_path: 预测文件的路径
        
    Returns:
        解析后的JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        return {}
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的JSON格式")
        return {}
    except Exception as e:
        print(f"读取文件时发生错误: {str(e)}")
        return {}


def filter_predictions(predictions: Dict[str, Any], target_ids: Set[str]) -> Dict[str, Any]:
    """
    过滤预测结果，只保留指定ID的预测
    
    Args:
        predictions: 所有预测结果的字典
        target_ids: 目标ID集合
        
    Returns:
        过滤后的预测结果字典
    """
    filtered_predictions = {}
    i = 0
    for instance_id, pred_data in predictions.items():
        if instance_id  not in target_ids:
            filtered_predictions[instance_id] = pred_data
            print(i, end=" ")
        i += 1
    
    return filtered_predictions


def save_predictions(predictions: Dict[str, Any], output_path: str) -> None:
    """
    保存预测结果到指定文件
    
    Args:
        predictions: 预测结果字典
        output_path: 输出文件路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        print(f"已成功保存 {len(predictions)} 个预测结果到 {output_path}")
    except Exception as e:
        print(f"保存文件时发生错误: {str(e)}")


def main():
    """主函数"""
    # 目标实例ID集合
    target_ids = {
        "django__django-11551",
        "django__django-14672",
        "django__django-15930",
        "django__django-16082",
        "django__django-13012",
        "django__django-12193",
        "django__django-11299",
        "django__django-11749",
        "django__django-12143",
        "django__django-7530",
        "sphinx-doc__sphinx-9281"
    }
    
    # 预测文件路径 - 用户可以根据需要修改
    pred_file_path = "/home/uaih3k9x/swebench/evolve_agent/trajectories/uaih3k9x/default__deepseek/用于充当反例/preds.json"
    
    # 输出文件路径
    output_dir = Path("counter_generation")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "filtered_predictions.json"
    
    # 读取预测文件
    print(f"正在读取预测文件: {pred_file_path}")
    predictions = read_predictions(pred_file_path)
    
    if predictions:
        print(f"成功读取预测文件，包含 {len(predictions)} 个预测结果")
        
        # 过滤预测
        filtered_predictions = filter_predictions(predictions, target_ids)
        print(f"已过滤得到 {len(filtered_predictions)} 个匹配的预测结果")
        
        # 保存过滤后的预测
        save_predictions(filtered_predictions, output_path)
    else:
        print("没有找到预测结果，请检查预测文件路径是否正确")


if __name__ == "__main__":
    main() 