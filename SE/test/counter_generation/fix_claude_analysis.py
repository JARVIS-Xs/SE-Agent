#!/usr/bin/env python
"""
检查并修复conclusion.json文件中的claude_analysis字段，
确保所有必需的键都存在且有值，对于不符合要求的分析结果重新生成
"""

import os
import json
import sys
import time
import glob
import argparse
import concurrent.futures
import threading
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
# 确保能导入claude模块
sys.path.insert(0, str(current_dir))

# 导入Claude API客户端
from claude import ClaudeAPI, extract_content

# OpenAI API配置
OPENAI_BASE_URL = "https://2fa18d9abe4c87dccc.gradio.live"
OPENAI_API_KEY = "sk-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
OPENAI_MODEL = "gpt-4o"

# Claude API配置
CLAUDE_API_KEY = "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"
CLAUDE_MODEL = "claude-3-7-sonnet-20250219"
CLAUDE_BASE_URL = "https://api.anthropic.com/v1/messages"

# 导入OpenAI API(如果可用)
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 用于线程安全的锁
save_lock = threading.Lock()
print_lock = threading.Lock()  # 添加用于打印的锁
stats_lock = threading.Lock()  # 用于更新统计信息的锁

# 统计信息
stats = {
    "total_items": 0,
    "processed_items": 0,
    "fixed_items": 0,
    "skipped_items": 0,
    "failed_items": 0,
    "empty_patch_items": 0,  # 记录model_patch为空的项
    "start_time": None,
    "end_time": None,
    "item_times": {}  # 记录每个item的处理时间
}

# 必需的分析字段
REQUIRED_KEYS = {
    "approach_summary",
    "modified_files",
    "key_changes",
    "strategy",
    "specific_technique_from_first_solution",
    "specific_files_or_functions",
    "assumptions_made_in_first_solution",
    "component_not_touched_in_first_solution",
    "different_perspective"
}

def log_message(message: str):
    """
    线程安全的日志打印
    
    Args:
        message: 要打印的消息
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with print_lock:
        print(f"[{timestamp}] {message}")

def load_filtered_predictions(file_path: str) -> Dict[str, Any]:
    """
    加载过滤后的预测文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的JSON数据
    """
    try:
        log_message(f"加载文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_message(f"加载文件 {file_path} 时出错: {e}")
        sys.exit(1)

def save_predictions(predictions: Dict[str, Any], file_path: str) -> None:
    """
    保存预测数据到JSON文件
    
    Args:
        predictions: 预测数据
        file_path: 输出文件路径
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        log_message(f"预测数据已保存到 {file_path}")
    except Exception as e:
        log_message(f"保存数据到 {file_path} 时出错: {e}")

def get_prompt_template() -> str:
    """
    获取分析补丁的提示模板 (适用于有model_patch的情况)
    
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

def get_empty_patch_prompt_template() -> str:
    """
    获取分析空补丁的提示模板 (适用于model_patch为空的情况)
    
    Returns:
        提示模板字符串
    """
    return """
You are an AI assistant specialized in analyzing unsuccessful solution attempts for code problems. I will provide a GitHub issue (problem_statement) that has been attempted but did not result in a successful patch submission. Your task is to analyze why a solution might have failed and provide insights that could help develop a successful solution.

Context: When a solution attempt fails to produce a valid patch, it often indicates one of these problems:
1. Too many ineffective operations were attempted
2. The approach was overly complex and not sufficiently targeted
3. The solution contained circular logic or infinite loops
4. The problem was misunderstood (either oversimplified or overcomplicated)
5. The approach missed the fundamental issue

Based on the problem statement alone, provide your analysis in JSON format with the following fields:
- approach_summary: "No successful patch was submitted. This likely indicates difficulties in implementing a working solution."
- modified_files: List of files that would likely need to be modified based on the problem description
- key_changes: Description of changes that would likely be needed to solve the problem
- strategy: A suggested core solution strategy at an abstract level
- specific_technique_from_first_solution: "No specific technique to avoid since no working solution was submitted, but likely pitfalls include [your analysis]"
- specific_files_or_functions: Specific files or functions that would likely need to be modified
- assumptions_made_in_first_solution: "The unsuccessful attempt likely made assumptions such as [your analysis]"
- component_not_touched_in_first_solution: Components or key functions that might be relevant but overlooked
- different_perspective: A different perspective or approach that might lead to a successful solution

Problem:
{problem_statement}

Note: Remember, there was no successful patch submitted for this problem. Your analysis should focus on why previous attempts might have failed and what approaches might be more successful.
"""

def analyze_patch_with_openai(
    problem_statement: str, 
    model_patch: str, 
    instance_id: str, 
    api_key: str = OPENAI_API_KEY,
    base_url: str = OPENAI_BASE_URL,
    model: str = OPENAI_MODEL,
    is_empty_patch: bool = False
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
        is_empty_patch: 是否为空补丁 (model_patch为空)
        
    Returns:
        OpenAI的分析结果
    """
    if not OPENAI_AVAILABLE:
        log_message("错误: 未安装openai库，请使用 pip install openai 进行安装")
        return {"error": "未安装openai库"}
    
    # 获取提示模板并填充
    if is_empty_patch:
        prompt_template = get_empty_patch_prompt_template()
        prompt = prompt_template.format(
            problem_statement=problem_statement
        )
        log_message(f"正在使用OpenAI API分析空补丁 {instance_id}...")
    else:
        prompt_template = get_prompt_template()
        prompt = prompt_template.format(
            problem_statement=problem_statement,
            model_patch=model_patch
        )
        log_message(f"正在使用OpenAI API分析补丁 {instance_id}...")
    
    try:
        # 创建OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
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
                log_message(f"警告: 无法在OpenAI响应中找到JSON格式内容: {content[:100]}...")
                return {"error": "无法解析JSON", "raw_content": content}
        except json.JSONDecodeError as e:
            log_message(f"解析OpenAI JSON响应时出错: {e}")
            return {"error": "JSON解析错误", "raw_content": content}
            
    except Exception as e:
        log_message(f"调用OpenAI API时出错: {e}")
        return {"error": f"OpenAI API错误: {str(e)}"}

def analyze_patch_with_claude(
    problem_statement: str, 
    model_patch: str, 
    instance_id: str, 
    claude_api: ClaudeAPI,
    is_empty_patch: bool = False
) -> Dict[str, Any]:
    """
    使用Claude API分析补丁
    
    Args:
        problem_statement: 问题描述
        model_patch: 模型补丁
        instance_id: 实例ID
        claude_api: Claude API客户端
        is_empty_patch: 是否为空补丁 (model_patch为空)
        
    Returns:
        Claude的分析结果
    """
    # 获取提示模板并填充
    if is_empty_patch:
        prompt_template = get_empty_patch_prompt_template()
        prompt = prompt_template.format(
            problem_statement=problem_statement
        )
        log_message(f"正在使用Claude API分析空补丁 {instance_id}...")
    else:
        prompt_template = get_prompt_template()
        prompt = prompt_template.format(
            problem_statement=problem_statement,
            model_patch=model_patch
        )
        log_message(f"正在使用Claude API分析补丁 {instance_id}...")
    
    # 直接使用send_message方法
    response = claude_api.send_message(
        message=prompt,
        model=CLAUDE_MODEL,  # 使用全局变量
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
            log_message(f"警告: 无法在响应中找到JSON格式内容: {content[:100]}...")
            return {"error": "无法解析JSON", "raw_content": content}
    except json.JSONDecodeError as e:
        log_message(f"解析JSON响应时出错: {e}")
        return {"error": "JSON解析错误", "raw_content": content}

def is_valid_analysis(analysis: Dict[str, Any]) -> bool:
    """
    检查分析结果是否有效(包含所有必需的键且值不为空)
    
    Args:
        analysis: 分析结果
        
    Returns:
        是否有效
    """
    # 检查是否存在错误
    if "error" in analysis:
        return False
    
    # 检查所有必需的键是否存在且值不为空
    for key in REQUIRED_KEYS:
        if key not in analysis:
            return False
        
        value = analysis[key]
        # 检查值是否为空
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return False
    
    return True

def fix_analysis_item(
    key: str,
    instance_data: Dict[str, Any],
    api_type: str,
    claude_api: Optional[ClaudeAPI] = None,
    rate_limit_delay: float = 1.0
) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
    """
    检查并修复单个分析项
    
    Args:
        key: 预测项的键
        instance_data: 预测项数据
        api_type: API类型，'claude'或'openai'
        claude_api: Claude API客户端(当api_type为'claude'时使用)
        rate_limit_delay: API调用之间的延迟(秒)
        
    Returns:
        元组(键, 是否需要修复, 新的分析结果(如果需要修复))
    """
    # 记录处理开始时间
    start_time = time.time()
    
    # 更新统计信息
    with stats_lock:
        stats["item_times"][key] = {"start_time": start_time}
    
    # 检查是否存在claude_analysis
    if "claude_analysis" not in instance_data:
        log_message(f"警告: {key} 没有claude_analysis字段，跳过")
        with stats_lock:
            stats["failed_items"] += 1
            stats["processed_items"] += 1
            stats["item_times"][key]["end_time"] = time.time()
            stats["item_times"][key]["success"] = False
            stats["item_times"][key]["error"] = "没有claude_analysis字段"
        return key, False, None
    
    # 检查分析结果是否有效
    analysis = instance_data["claude_analysis"]
    if is_valid_analysis(analysis):
        log_message(f"{key} 的分析结果有效，无需修复")
        with stats_lock:
            stats["skipped_items"] += 1
            stats["processed_items"] += 1
            stats["item_times"][key]["end_time"] = time.time()
            stats["item_times"][key]["success"] = True
            duration = stats["item_times"][key]["end_time"] - stats["item_times"][key]["start_time"]
            stats["item_times"][key]["duration"] = duration
        return key, False, None
    
    # 如果分析结果无效，需要重新生成
    log_message(f"{key} 的分析结果无效，需要重新生成")
    
    # 提取问题陈述和补丁
    if "problem_statement" not in instance_data:
        log_message(f"警告: {key} 缺少问题陈述，无法重新生成")
        with stats_lock:
            stats["failed_items"] += 1
            stats["processed_items"] += 1
            stats["item_times"][key]["end_time"] = time.time()
            stats["item_times"][key]["success"] = False
            stats["item_times"][key]["error"] = "缺少问题陈述"
        return key, False, None
    
    problem_statement = instance_data["problem_statement"]
    
    # 检查model_patch是否为空
    is_empty_patch = False
    if "model_patch" not in instance_data or not instance_data["model_patch"]:
        log_message(f"{key} 的model_patch为空，使用空补丁模板")
        model_patch = ""
        is_empty_patch = True
        with stats_lock:
            stats["empty_patch_items"] += 1
    else:
        model_patch = instance_data["model_patch"]
    
    try:
        # 根据API类型重新生成分析
        if api_type == 'claude' and claude_api:
            new_analysis = analyze_patch_with_claude(
                problem_statement, 
                model_patch, 
                key, 
                claude_api,
                is_empty_patch
            )
        elif api_type == 'openai':
            new_analysis = analyze_patch_with_openai(
                problem_statement, 
                model_patch, 
                key,
                is_empty_patch=is_empty_patch
            )
        else:
            log_message(f"错误: 无效的API配置")
            with stats_lock:
                stats["failed_items"] += 1
                stats["processed_items"] += 1
                stats["item_times"][key]["end_time"] = time.time()
                stats["item_times"][key]["success"] = False
                stats["item_times"][key]["error"] = "无效的API配置"
            return key, False, None
        
        # 检查新的分析结果是否有效
        if is_valid_analysis(new_analysis):
            log_message(f"成功重新生成 {key} 的分析结果")
            with stats_lock:
                stats["fixed_items"] += 1
                stats["processed_items"] += 1
                stats["item_times"][key]["end_time"] = time.time()
                stats["item_times"][key]["success"] = True
                duration = stats["item_times"][key]["end_time"] - stats["item_times"][key]["start_time"]
                stats["item_times"][key]["duration"] = duration
            
            # 避免API调用过于频繁
            time.sleep(rate_limit_delay)
            
            return key, True, new_analysis
        else:
            log_message(f"重新生成的分析结果仍然无效: {key}")
            with stats_lock:
                stats["failed_items"] += 1
                stats["processed_items"] += 1
                stats["item_times"][key]["end_time"] = time.time()
                stats["item_times"][key]["success"] = False
                stats["item_times"][key]["error"] = "重新生成的分析结果无效"
            
            # 避免API调用过于频繁
            time.sleep(rate_limit_delay)
            
            return key, False, None
        
    except Exception as e:
        import traceback
        log_message(f"处理 {key} 时出错: {str(e)}")
        log_message(traceback.format_exc())
        
        # 更新统计信息
        with stats_lock:
            stats["failed_items"] += 1
            stats["processed_items"] += 1
            stats["item_times"][key]["end_time"] = time.time()
            stats["item_times"][key]["success"] = False
            stats["item_times"][key]["error"] = str(e)
            duration = stats["item_times"][key]["end_time"] - stats["item_times"][key]["start_time"]
            stats["item_times"][key]["duration"] = duration
        
        return key, False, None

def fix_conclusion_file(
    conclusion_file: str, 
    api_type: str, 
    claude_api: Optional[ClaudeAPI] = None, 
    test_mode: bool = False,
    max_workers: int = 4,
    rate_limit_delay: float = 1.0,
    test_item: Optional[str] = None
) -> None:
    """
    修复conclusion.json文件中的分析结果
    
    Args:
        conclusion_file: conclusion.json文件路径
        api_type: API类型，'claude'或'openai'
        claude_api: Claude API客户端(当api_type为'claude'时使用)
        test_mode: 是否仅测试第一条数据
        max_workers: 最大并发工作线程数
        rate_limit_delay: API调用之间的延迟(秒)
        test_item: 测试特定的项ID
    """
    log_message(f"修复文件: {conclusion_file}")
    
    # 加载conclusion.json数据
    predictions = load_filtered_predictions(conclusion_file)
    
    # 如果指定了测试特定的项
    if test_item:
        if test_item in predictions:
            log_message(f"测试处理项 {test_item}")
            # 更新统计信息
            with stats_lock:
                stats["total_items"] = 1
            
            # 修复单个项
            key, need_fix, new_analysis = fix_analysis_item(
                test_item,
                predictions[test_item],
                api_type,
                claude_api,
                rate_limit_delay
            )
            
            # 如果需要修复且有新的分析结果
            if need_fix and new_analysis:
                # 保存结果
                with save_lock:
                    predictions[test_item]["claude_analysis"] = new_analysis
                    save_predictions(predictions, conclusion_file)
                log_message(f"测试项结果已保存")
            return
        else:
            log_message(f"错误: 找不到项 {test_item}")
            return
    
    # 确定要处理的键列表
    keys_to_process = list(predictions.keys())
    if test_mode:
        # 仅处理第一个条目
        keys_to_process = keys_to_process[0:1]

    # 更新统计信息
    with stats_lock:
        stats["total_items"] = len(keys_to_process)
        stats["start_time"] = time.time()
    
    # 打印开始时间
    start_timestamp = datetime.datetime.fromtimestamp(stats["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
    log_message(f"开始修复 {len(keys_to_process)} 个项目，时间: {start_timestamp}")

    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_key = {
            executor.submit(
                fix_analysis_item, key, predictions[key], api_type, claude_api, rate_limit_delay
            ): key for key in keys_to_process
        }
        
        # 处理完成的任务
        completed = 0
        for future in concurrent.futures.as_completed(future_to_key):
            key = future_to_key[future]
            completed += 1
            
            # 计算进度百分比
            progress = (completed / len(keys_to_process)) * 100
            log_message(f"进度: {progress:.2f}% ({completed}/{len(keys_to_process)})")
            
            try:
                item_key, need_fix, new_analysis = future.result()
                # 如果需要修复且有新的分析结果
                if need_fix and new_analysis:
                    with save_lock:
                        # 更新内存中的预测
                        predictions[item_key]["claude_analysis"] = new_analysis
                        # 保存更新后的预测
                        save_predictions(predictions, conclusion_file)
                        log_message(f"已修复并保存 {item_key} 的分析结果")
            except Exception as e:
                log_message(f"处理 {key} 时出错: {str(e)}")
                import traceback
                log_message(traceback.format_exc())
    
    # 更新统计信息
    with stats_lock:
        stats["end_time"] = time.time()
    
    # 计算总处理时间
    if stats["start_time"] and stats["end_time"]:
        total_duration = stats["end_time"] - stats["start_time"]
        end_timestamp = datetime.datetime.fromtimestamp(stats["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
        log_message(f"文件 {conclusion_file} 修复完成，总耗时 {total_duration:.2f} 秒")
        log_message(f"结束时间: {end_timestamp}")
        log_message(f"统计信息: 总项目数 {stats['total_items']}, 已处理 {stats['processed_items']}, "
                  f"已修复 {stats['fixed_items']}, 已跳过 {stats['skipped_items']}, 空补丁 {stats['empty_patch_items']}, 失败 {stats['failed_items']}")
    else:
        log_message(f"文件 {conclusion_file} 修复完成")

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

def print_time_stats():
    """
    打印时间统计信息
    """
    if not stats["item_times"]:
        log_message("没有时间统计信息")
        return
    
    # 计算平均时间、最短时间和最长时间
    durations = []
    for item_id, time_info in stats["item_times"].items():
        if "duration" in time_info:
            durations.append(time_info["duration"])
    
    if durations:
        avg_time = sum(durations) / len(durations)
        min_time = min(durations)
        max_time = max(durations)
        
        log_message(f"时间统计:")
        log_message(f"  平均处理时间: {avg_time:.2f} 秒")
        log_message(f"  最短处理时间: {min_time:.2f} 秒")
        log_message(f"  最长处理时间: {max_time:.2f} 秒")
        log_message(f"  总处理项目数: {len(durations)}")
    
    # 打印总体处理时间
    if stats["start_time"] and stats["end_time"]:
        total_duration = stats["end_time"] - stats["start_time"]
        log_message(f"  总处理时间: {total_duration:.2f} 秒")

def start_tmux_session(session_name, command):
    """
    启动tmux会话并运行命令
    
    Args:
        session_name: 会话名称
        command: 要运行的命令
    """
    try:
        # 检查是否存在相同名称的会话
        check_cmd = ["tmux", "has-session", "-t", session_name]
        result = subprocess.run(check_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        if result.returncode == 0:
            log_message(f"会话 {session_name} 已存在，将关闭它")
            kill_cmd = ["tmux", "kill-session", "-t", session_name]
            subprocess.run(kill_cmd)
        
        # 创建新会话
        create_cmd = ["tmux", "new-session", "-d", "-s", session_name]
        subprocess.run(create_cmd)
        
        # 在会话中运行命令
        run_cmd = ["tmux", "send-keys", "-t", session_name, command, "C-m"]
        subprocess.run(run_cmd)
        
        log_message(f"启动tmux会话 {session_name} 并运行命令: {command}")
        log_message(f"可以使用 'tmux attach-session -t {session_name}' 查看进度")
        
        return True
    except Exception as e:
        log_message(f"启动tmux会话时出错: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="修复conclusion.json文件中的claude_analysis字段")
    parser.add_argument("--base_path", default="/home/uaih3k9x/swebench/evolve_agent/exp_claude37_0-30",
                        help="基础路径，包含5个default文件夹")
    parser.add_argument("--scan_dir", help="指定要扫描的目录路径，将处理该目录下的所有conclusion.json文件")
    parser.add_argument("--test", action="store_true", help="测试模式：只处理每个文件的第一条数据")
    parser.add_argument("--api_type", choices=["claude", "openai"], default="openai",
                        help="使用的API类型：claude或openai(默认)")
    parser.add_argument("--claude_api_key", default=CLAUDE_API_KEY,
                        help="Claude API密钥")
    parser.add_argument("--specific_file", help="直接处理指定的preds.json或conclusion.json文件，而不是扫描目录")
    parser.add_argument("--max_workers", type=int, default=4, help="并发处理的最大线程数")
    parser.add_argument("--rate_limit_delay", type=float, default=1.0, 
                       help="API请求之间的延迟时间(秒)，用于避免频率限制")
    parser.add_argument("--test_item", help="处理特定的项ID进行测试")
    parser.add_argument("--tmux", action="store_true", help="在tmux会话中运行")
    parser.add_argument("--tmux_session", default="fix_analysis", help="tmux会话名称")
    args = parser.parse_args()
    
    # 如果指定了tmux模式，则启动tmux会话
    if args.tmux:
        # 构建相同的命令，但不带--tmux参数
        cmd_parts = sys.argv.copy()
        cmd = " ".join([p for p in cmd_parts if p != "--tmux"])
        
        # 启动tmux会话
        start_tmux_session(args.tmux_session, cmd)
        return
    
    # 记录开始时间
    log_message("开始运行脚本")
    
    # 根据API类型处理
    if args.api_type == 'claude':
        # 初始化Claude API客户端
        claude_api = ClaudeAPI(args.claude_api_key)
    else:  # openai
        if not OPENAI_AVAILABLE:
            log_message("错误: 未安装openai库，请使用 pip install openai 进行安装")
            return
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        claude_api = None
    
    # 如果指定了特定文件
    if args.specific_file:
        if os.path.exists(args.specific_file):
            log_message(f"直接处理指定文件: {args.specific_file}")
            fix_conclusion_file(
                args.specific_file,
                args.api_type,
                claude_api,
                args.test,
                args.max_workers,
                args.rate_limit_delay,
                args.test_item
            )
        else:
            log_message(f"错误: 指定的文件 {args.specific_file} 不存在")
        
        # 打印时间统计
        print_time_stats()
        return
    
    # 如果指定了扫描目录
    if args.scan_dir:
        if os.path.exists(args.scan_dir):
            log_message(f"开始扫描目录: {args.scan_dir}")
            # 使用glob递归查找所有conclusion.json文件
            conclusion_files = glob.glob(os.path.join(args.scan_dir, "**", "conclusion.json"), recursive=True)
            log_message(f"找到 {len(conclusion_files)} 个conclusion.json文件")
            
            # 处理每个文件
            for file_path in conclusion_files:
                fix_conclusion_file(
                    file_path, 
                    args.api_type, 
                    claude_api, 
                    args.test,
                    args.max_workers,
                    args.rate_limit_delay
                )
        else:
            log_message(f"错误: 指定的扫描目录 {args.scan_dir} 不存在")
        
        # 打印时间统计
        print_time_stats()
        return
    
    # 查找所有conclusion.json文件
    conclusion_files = find_conclusion_files(args.base_path)
    log_message(f"找到 {len(conclusion_files)} 个conclusion.json文件")
    
    # 处理每个文件
    for file_path in conclusion_files:
        fix_conclusion_file(
            file_path, 
            args.api_type, 
            claude_api, 
            args.test,
            args.max_workers,
            args.rate_limit_delay
        )
    
    # 打印时间统计
    print_time_stats()    
    log_message("所有文件修复完成")

if __name__ == "__main__":
    main() 