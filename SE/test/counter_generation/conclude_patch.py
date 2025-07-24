#!/usr/bin/env python
"""
分析filtered_predictions.json中的补丁，使用Claude API或OpenAI API进行评估，
并将分析结果直接添加到原始filtered_predictions.json文件中
"""

import os
import json
import sys
import time
import glob
import argparse
import concurrent.futures
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
# 确保能导入claude模块
sys.path.insert(0, str(current_dir))

# 导入Claude API客户端
from claude import ClaudeAPI, extract_content

# OpenAI API配置(硬编码)
OPENAI_BASE_URL = "https://2fa18d9abe4c87dccc.gradio.live"
OPENAI_API_KEY = "sk-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
OPENAI_MODEL = "gpt-4o"

# 导入OpenAI API(如果可用)
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 为线程安全操作添加锁
save_lock = threading.Lock()

def load_filtered_predictions(file_path: str) -> Dict[str, Any]:
    """
    加载过滤后的预测文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        sys.exit(1)

def save_predictions(predictions: Dict[str, Any], file_path: str) -> None:
    """
    保存预测数据到JSON文件
    
    Args:
        predictions: 预测数据
        file_path: 输出文件路径
    """
    try:
        with save_lock:  # 使用锁确保线程安全
            # 使用临时文件然后重命名的方式，避免写入中断导致文件损坏
            temp_file = file_path + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, file_path)
            print(f"预测数据已保存到 {file_path}")
    except Exception as e:
        print(f"保存数据到 {file_path} 时出错: {e}")

def get_prompt_template() -> str:
    """
    获取分析补丁的提示模板
    
    Returns:
        提示模板字符串
    """
    return """
You are an AI assistant specialized in analyzing code patches. I will provide a GitHub issue (problem_statement) and a corresponding patch. Your task is to analyze this patch and provide detailed insights that could help develop an alternative solution.

Follow these steps:
1. Analyze the patch file and understand the changes made
2. Determine the core methods and techniques used to solve the problem
3. Identify the main files and sections that were modified
4. Identify key assumptions and limitations in the current solution

Return your analysis in JSON format with the following fields:
- approach_summary: Summary of the main approach used in the first solution
- modified_files: List of files that were modified
- key_changes: Description of key code changes in the patch
- strategy: The core solution strategy at an abstract level
- specific_technique_from_first_solution: Specific technique used that should be avoided in alternative solutions
- specific_files_or_functions: Files or functions that should not be modified in the same way
- assumptions_made_in_first_solution: Assumptions made in the first solution
- component_not_touched_in_first_solution: Components or key functions not touched but potentially relevant
- different_perspective: A different perspective for looking at the problem

The following examples are provided only for reference to illustrate the expected level of detail and abstraction for each field. Your analysis should be based on your own understanding of the patch and problem:

approach_summary example: "Added a conditional check to handle MultiOutputClassifier by accessing classes through the estimators_ attribute"
modified_files example: ["sklearn/model_selection/_validation.py"]
key_changes example: "Added a condition to check if estimator has 'estimators_' attribute, then uses estimator.estimators_[i_label].classes_ instead of estimator.classes_[i_label] for MultiOutputClassifier"
strategy example: "Component-specific exception handling" (instead of "Interface extension to provide unified attribute access")
specific_technique_from_first_solution example: "Direct attribute checking with hasattr() and conditional branching"
specific_files_or_functions example: "_fit_and_predict function in sklearn/model_selection/_validation.py"
assumptions_made_in_first_solution example: "Assumes that only MultiOutputClassifier needs special handling for classes_ attribute access"
component_not_touched_in_first_solution example: "MultiOutputClassifier class in sklearn/multioutput.py which could implement classes_ attribute directly"
different_perspective example: "API consistency perspective: make MultiOutputClassifier conform to the same interface as other classifiers instead of modifying the validation module"

Problem:
{problem_statement}
Patch:
{model_patch}
"""

def analyze_patch_with_openai(
    problem_statement: str, 
    model_patch: str, 
    instance_id: str, 
    api_key: str = OPENAI_API_KEY,
    base_url: str = OPENAI_BASE_URL,
    model: str = OPENAI_MODEL
) -> Dict[str, Any]:
    """
    使用OpenAI API分析补丁
    
    Args:
        problem_statement: 问题描述
        model_patch: 模型补丁
        instance_id: 实例ID
        api_key: OpenAI API密钥
        base_url: OpenAI API的基础URL
        model: 模型名称
        
    Returns:
        OpenAI的分析结果
    """
    if not OPENAI_AVAILABLE:
        print("错误: 未安装openai库，请使用 pip install openai 进行安装")
        return {"error": "未安装openai库"}
    
    # 获取提示模板并填充
    prompt_template = get_prompt_template()
    prompt = prompt_template.format(
        problem_statement=problem_statement,
        model_patch=model_patch
    )
    
    print(f"📝 正在使用OpenAI API分析 {instance_id}...")
    
    retry_count = 0
    max_retries = 3
    
    while retry_count <= max_retries:
        try:
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120  # 设置2分钟超时
            )
            
            # 调用OpenAI API
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            
            # 提取内容
            content = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                # 如果返回的内容包含围绕JSON的额外文本，提取JSON部分
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx]
                    return json.loads(json_content)
                else:
                    print(f"⚠️ 警告: 无法在OpenAI响应中找到JSON格式内容: {content[:100]}...")
                    return {"error": "无法解析JSON", "raw_content": content}
            except json.JSONDecodeError as e:
                print(f"⚠️ 解析OpenAI JSON响应时出错: {e}")
                return {"error": "JSON解析错误", "raw_content": content}
                
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 5 * retry_count  # 指数退避
                print(f"⚠️ 调用OpenAI API时出错 (尝试 {retry_count}/{max_retries}): {e}，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"❌ 调用OpenAI API失败，已达最大重试次数: {e}")
                return {"error": f"OpenAI API错误: {str(e)}"}

def analyze_patch_with_claude(problem_statement: str, model_patch: str, instance_id: str, claude_api: ClaudeAPI) -> Dict[str, Any]:
    """
    使用Claude API分析补丁
    
    Args:
        problem_statement: 问题描述
        model_patch: 模型补丁
        instance_id: 实例ID
        claude_api: Claude API客户端
        
    Returns:
        Claude的分析结果
    """
    # 获取提示模板并填充
    prompt_template = get_prompt_template()
    prompt = prompt_template.format(
        problem_statement=problem_statement,
        model_patch=model_patch
    )
    
    print(f"📝 正在使用Claude API分析 {instance_id}...")
    
    retry_count = 0
    max_retries = 3
    
    while retry_count <= max_retries:
        try:
            response = claude_api.send_message(
                message=prompt,
                model="claude-3-7-sonnet-20250219",
                temperature=0.3,
                max_tokens=4000
            )
            
            content = extract_content(response)
            
            # 尝试解析JSON响应
            try:
                # 如果Claude返回的内容包含围绕JSON的额外文本，我们需要提取JSON部分
                # 这里使用一个简单的方法：寻找第一个{和最后一个}之间的内容
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx]
                    return json.loads(json_content)
                else:
                    print(f"⚠️ 警告: 无法在响应中找到JSON格式内容: {content[:100]}...")
                    return {"error": "无法解析JSON", "raw_content": content}
            except json.JSONDecodeError as e:
                print(f"⚠️ 解析JSON响应时出错: {e}")
                return {"error": "JSON解析错误", "raw_content": content}
                
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                wait_time = 5 * retry_count  # 指数退避
                print(f"⚠️ 调用Claude API时出错 (尝试 {retry_count}/{max_retries}): {e}，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"❌ 调用Claude API失败，已达最大重试次数: {e}")
                return {"error": f"Claude API错误: {str(e)}"}

def process_single_entry(
    entry_data: Tuple[str, Dict[str, Any]], 
    predictions: Dict[str, Any],
    conclusion_file: str,
    api_type: str,
    claude_api: Optional[ClaudeAPI] = None,
    force_reprocess: bool = False
) -> None:
    """
    处理单个条目
    
    Args:
        entry_data: 包含键和数据的元组
        predictions: 预测数据字典
        conclusion_file: 输出文件路径
        api_type: API类型，'claude'或'openai'
        claude_api: Claude API客户端(当api_type为'claude'时使用)
        force_reprocess: 是否强制重新处理已有分析的条目
    """
    key, instance_data = entry_data
    
    # 如果已经处理过这个键且不强制重新处理，跳过
    if "claude_analysis" in instance_data and not force_reprocess:
        print(f"跳过已处理的条目: {key}")
        return
    elif "claude_analysis" in instance_data and force_reprocess:
        print(f"强制重新处理条目: {key}")
    
    # 提取问题陈述和补丁
    if "problem_statement" not in instance_data:
        print(f"警告: {key} 没有问题陈述，跳过")
        return
        
    problem_statement = instance_data["problem_statement"]
    model_patch = instance_data["model_patch"]
    
    try:
        # 根据API类型调用相应的分析函数
        if api_type == 'claude' and claude_api:
            analysis = analyze_patch_with_claude(problem_statement, model_patch, key, claude_api)
        elif api_type == 'openai':
            analysis = analyze_patch_with_openai(problem_statement, model_patch, key)
        else:
            print(f"错误: 无效的API配置")
            return
        
        # 添加分析结果并保存
        with save_lock:
            predictions[key]["claude_analysis"] = analysis
            # 保存时使用临时文件然后重命名，避免文件损坏风险
            temp_file = conclusion_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, conclusion_file)
            print(f"✅ 条目 {key} 处理完成并保存")
    except Exception as e:
        print(f"❌ 处理条目 {key} 时出错: {str(e)}")
        return None

def process_conclusion_file(
    conclusion_file: str, 
    api_type: str, 
    claude_api: Optional[ClaudeAPI] = None, 
    test_mode: bool = False,
    max_workers: int = 3,
    force_reprocess: bool = False
) -> None:
    """
    处理单个conclusion.json文件，使用多线程并发处理
    
    Args:
        conclusion_file: conclusion.json文件路径
        api_type: API类型，'claude'或'openai'
        claude_api: Claude API客户端(当api_type为'claude'时使用)
        test_mode: 是否仅测试第一条数据
        max_workers: 最大并发线程数
        force_reprocess: 是否强制重新处理已有分析的条目
    """
    print(f"处理文件: {conclusion_file}")
    
    # 加载conclusion.json数据
    predictions = load_filtered_predictions(conclusion_file)
    
    # 确定要处理的键列表
    keys_to_process = list(predictions.keys())
    if test_mode:
        # 仅处理第一个条目
        keys_to_process = keys_to_process[0:1]
    
    # 准备需要处理的条目列表
    entries_to_process = []
    for key in keys_to_process:
        # 如果强制重新处理或没有分析过，则添加到处理列表
        if force_reprocess or "claude_analysis" not in predictions[key]:
            entries_to_process.append((key, predictions[key]))
    
    if not entries_to_process:
        print(f"文件 {conclusion_file} 中所有条目已处理，跳过")
        return
    
    print(f"文件 {conclusion_file} 中有 {len(entries_to_process)} 条待处理")
    
    # 使用顺序 + 并发方式处理条目（分批处理）
    batch_size = min(max_workers, len(entries_to_process))
    processed_count = 0
    
    for i in range(0, len(entries_to_process), batch_size):
        batch = entries_to_process[i:i+batch_size]
        print(f"正在处理批次 {i//batch_size + 1}/{(len(entries_to_process) + batch_size - 1)//batch_size}，共 {len(batch)} 条")
        
        # 使用ThreadPoolExecutor处理当前批次
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for entry_data in batch:
                futures.append(
                    executor.submit(
                        process_single_entry,
                        entry_data,
                        predictions,
                        conclusion_file,
                        api_type,
                        claude_api,
                        force_reprocess
                    )
                )
            
            # 等待当前批次完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result(timeout=180)  # 设置3分钟超时
                    processed_count += 1
                except concurrent.futures.TimeoutError:
                    print(f"⚠️ 处理条目超时")
                except Exception as e:
                    print(f"⚠️ 处理条目时出错: {e}")
        
        # 批次间等待，避免API限流
        if i + batch_size < len(entries_to_process):
            wait_time = 2  # 每批次间等待2秒
            print(f"批次处理完成，等待 {wait_time} 秒后处理下一批...")
            time.sleep(wait_time)
    
    print(f"文件 {conclusion_file} 处理完成，成功处理 {processed_count}/{len(entries_to_process)} 条数据")

def find_conclusion_files(base_path: str) -> list:
    """
    查找所有符合条件的conclusion.json文件
    
    Args:
        base_path: 基础路径
        
    Returns:
        文件路径列表
    """
    conclusion_files = []
    
    # 遍历5个default文件夹
    for i in range(1, 6):
        folder_pattern = f"{base_path}/default_{i}/*/"
        timestamp_folders = glob.glob(folder_pattern)
        
        for timestamp_folder in timestamp_folders:
            conclusion_file = os.path.join(timestamp_folder, "conclusion.json")
            if os.path.exists(conclusion_file):
                conclusion_files.append(conclusion_file)
    
    return conclusion_files

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="使用LLM API分析补丁并将结果添加到conclusion.json文件")
    parser.add_argument("--base_path", default="/home/uaih3k9x/swebench/evolve_agent/newest_exp_claude37_30-125",
                        help="基础路径，包含5个default文件夹")
    parser.add_argument("--test", action="store_true", help="测试模式：只处理每个文件的第一条数据")
    parser.add_argument("--api_type", choices=["claude", "openai"], default="claude",
                        help="使用的API类型：claude或openai(默认)")
    parser.add_argument("--claude_api_key", default="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",
                        help="Claude API密钥")
    parser.add_argument("--max_workers", type=int, default=3, 
                        help="最大并发线程数，默认为3")
    parser.add_argument("--force", action="store_true",
                        help="强制重新处理已有分析的条目")
    args = parser.parse_args()
    
    # 根据API类型处理
    if args.api_type == 'claude':
        # 初始化Claude API客户端
        claude_api = ClaudeAPI(args.claude_api_key)
    else:  # openai
        if not OPENAI_AVAILABLE:
            print("错误: 未安装openai库，请使用 pip install openai 进行安装")
            return
        claude_api = None
    
    # 查找所有conclusion.json文件
    conclusion_files = find_conclusion_files(args.base_path)
    print(f"找到 {len(conclusion_files)} 个conclusion.json文件")
    
    # 处理每个文件（文件之间是顺序处理的）
    for file_path in conclusion_files:
        process_conclusion_file(
            file_path, 
            args.api_type, 
            claude_api, 
            args.test,
            args.max_workers,
            args.force
        )
        
    print("所有文件处理完成")

if __name__ == "__main__":
    main() 