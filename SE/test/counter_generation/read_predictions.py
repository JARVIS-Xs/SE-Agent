#!/usr/bin/env python
"""
读取并打印预测文件内容的脚本

此脚本读取指定路径下的preds.json文件，并打印其内容结构。
用于分析预测结果并提取需要的信息。
"""

import json
import os
from pathlib import Path


def read_predictions(file_path):
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
        return None
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的JSON格式")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {str(e)}")
        return None


def main():
    """主函数"""
    # 预测文件路径
    pred_file_path = "/home/uaih3k9x/swebench/evolve_agent/trajectories/uaih3k9x/default__deepseek/用于充当反例/preds.json"
    
    # 读取预测文件
    predictions = read_predictions(pred_file_path)
    
    if predictions:
        print(f"成功读取预测文件: {pred_file_path}")
        print(f"文件包含 {len(predictions)} 个预测结果")
        
        # 遍历输出预测内容
        for i, (instance_id, pred_data) in enumerate(predictions.items()):
            print(f"\n--- 预测 {i+1}: {instance_id} ---")
            
            # 输出预测数据的基本信息
            if isinstance(pred_data, dict):
                print(f"预测数据键: {', '.join(pred_data.keys())}")
                
                # 如果有model_patch字段，打印其摘要
                if "model_patch" in pred_data:
                    patch = pred_data["model_patch"]
                    if patch:
                        patch_preview = patch[:200] + "..." if len(patch) > 200 else patch
                        print(f"补丁内容摘要: {patch_preview}")
                    else:
                        print("补丁内容为空")
                
                # 如果有submission字段，打印其摘要
                if "submission" in pred_data:
                    submission = pred_data["submission"]
                    if submission:
                        submission_preview = submission[:200] + "..." if len(submission) > 200 else submission
                        print(f"提交内容摘要: {submission_preview}")
                    else:
                        print("提交内容为空")
                
                # 如果有exit_status字段，打印退出状态
                if "exit_status" in pred_data:
                    print(f"退出状态: {pred_data['exit_status']}")
            else:
                print(f"预测数据类型: {type(pred_data)}")


if __name__ == "__main__":
    main() 