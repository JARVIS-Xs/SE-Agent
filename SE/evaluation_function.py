import json
from typing import List, Dict, Optional
import requests
import os
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
)

def step_count_filter(traj: Dict, min_steps: int = 3, max_steps: int = 30) -> bool:
    """过滤轨迹步数是否在合理范围内"""
    steps = traj.get('steps', [])
    return min_steps <= len(steps) <= max_steps

def has_long_repetition(traj: Dict, max_repeat: int = 3) -> bool:
    """判断轨迹中是否有连续重复内容"""
    steps = traj.get('steps', [])
    last_content = None
    repeat_count = 1
    for step in steps:
        content = step.get('content', '').strip()
        if content == last_content and content:
            repeat_count += 1
            if repeat_count > max_repeat:
                return True
        else:
            repeat_count = 1
        last_content = content
    return False

def code_edit_ratio(traj: Dict, min_ratio: float = 0.2) -> bool:
    """判断轨迹中涉及代码编辑的步数比例是否达标"""
    steps = traj.get('steps', [])
    if not steps:
        return False
    edit_keywords = [k.lower() for k in ['edit', '修改', 'change', 'patch', 'diff', 'apply', '替换', '重写', 'fix', '修复']]
    edit_count = sum(
        any(k in step.get('content', '').lower() for k in edit_keywords)
        for step in steps
    )
    return (edit_count / len(steps)) >= min_ratio

def filter_non_empty(trajectories: List[Dict]) -> List[Dict]:
    """过滤空内容"""
    return [t for t in trajectories if t.get('content', '').strip()]

def filter_unique(trajectories: List[Dict]) -> List[Dict]:
    """内容去重"""
    seen = set()
    unique_trajs = []
    for traj in trajectories:
        content = traj.get('content', '').strip()
        if content and content not in seen:
            seen.add(content)
            unique_trajs.append(traj)
    return unique_trajs

def filter_length(trajectories: List[Dict], min_len: int = 10) -> List[Dict]:
    """过滤内容过短的轨迹"""
    return [t for t in trajectories if len(t.get('content', '').strip()) >= min_len]

def filter_bad_keywords(trajectories: List[Dict]) -> List[Dict]:
    """过滤包含负面关键词的轨迹"""
    bad_keywords = ['无法解决', 'error', 'not supported', '抱歉', "i don't know", '不知道', '失败', '未能', '不能', '无法', 'unsolved']
    def is_bad(traj):
        content = traj.get('content', '').lower()
        return any(k in content for k in bad_keywords)
    return [t for t in trajectories if not is_bad(t)]

def filter_step_count(trajectories: List[Dict]) -> List[Dict]:
    """过滤步数不合理的轨迹"""
    return [t for t in trajectories if step_count_filter(t)]

def filter_long_repetition(trajectories: List[Dict]) -> List[Dict]:
    """过滤有长重复的轨迹"""
    return [t for t in trajectories if not has_long_repetition(t)]

def filter_code_edit_ratio(trajectories: List[Dict]) -> List[Dict]:
    """过滤代码编辑比例不达标的轨迹"""
    return [t for t in trajectories if code_edit_ratio(t)]

def filter_trajectories(trajectories: List[Dict]) -> List[Dict]:
    """多步过滤轨迹，返回有效轨迹列表"""
    filtered = filter_non_empty(trajectories)
    filtered = filter_unique(filtered)
    filtered = filter_length(filtered)
    filtered = filter_bad_keywords(filtered)
    filtered = filter_step_count(filtered)
    filtered = filter_long_repetition(filtered)
    filtered = filter_code_edit_ratio(filtered)
    return filtered


def deepseek_r1_select(problem_statement: str, trajectories: list) -> int:
    """调用 DeepSeek R1 API 选择最优轨迹，返回索引"""
    prompt = (
        "You are an expert agent evaluator. Given a problem statement and several agent trajectories, "
        "your task is to select the trajectory that best solves the problem.\n\n"
        f"Problem Statement:\n{problem_statement}\n\n"
        "Agent Trajectories:\n"
    )
    for idx, traj in enumerate(trajectories):
        prompt += f"==== Trajectory {idx} ====\n" + json.dumps(traj, ensure_ascii=False) + "\n"
    prompt += (
        "\nPlease answer ONLY with the index (starting from 0) of the best trajectory. "
        "Do not output any explanation, punctuation, prefix, suffix, or any other content. "
        "Only output a single integer. If unsure, choose the closest one. If you cannot judge, output 0."
    )

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY":
        logging.error("未设置DEEPSEEK_API_KEY环境变量，无法调用DeepSeek API。请设置正确的API Key。")
        raise RuntimeError("DEEPSEEK_API_KEY未设置")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10,
        "temperature": 0.0
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        # 更健壮的返回格式判定
        if not (isinstance(result, dict) and 'choices' in result and result['choices'] and 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']):
            logging.error(f"API返回格式异常: {result}")
            return 0
        reply = result['choices'][0]['message']['content'].strip()
        match = re.match(r"^\s*(\d+)\s*$", reply)
        if match:
            idx = int(match.group(1))
        else:
            logging.warning(f"未能从回复中提取独立数字，回复内容: {reply}")
            idx = 0
    except Exception as e:
        logging.error(f"调用DeepSeek R1 API失败: {e}")
        idx = 0
    return idx


def select_best_trajectory(problem_statement: str, trajectories: List[Dict]) -> Optional[Dict]:
    """过滤并选择最优轨迹，返回最佳轨迹字典或None"""
    filtered_trajectories = filter_trajectories(trajectories)
    contents = [traj.get('content', '') for traj in filtered_trajectories]
    if not contents:
        logging.info("过滤后无有效轨迹，返回None。")
        return None
    best_idx = deepseek_r1_select(problem_statement, contents)
    if 0 <= best_idx < len(filtered_trajectories):
        return filtered_trajectories[best_idx]
    else:
        logging.warning(f"best_idx超出范围: {best_idx}, 轨迹数量: {len(filtered_trajectories)}，返回None。")
        return None


def process_file(input_path: str, output_path: str):
    """批量处理文件，逐行选择最优轨迹"""
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for lineno, line in enumerate(fin, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                problem_statement = data.get('problem_statement', '')
                trajectories = data.get('trajectories', [])
                best_traj = select_best_trajectory(problem_statement, trajectories)
                if best_traj is None:
                    data['best_trajectory'] = None
                else:
                    data['best_trajectory'] = best_traj
                fout.write(json.dumps(data, ensure_ascii=False) + '\n')
                # 每10行flush一次，提升效率
                if lineno % 10 == 0:
                    fout.flush()
            except Exception as e:
                logging.error(f"第{lineno}行处理失败: {e}，内容: {line.strip()}")
                continue
        fout.flush()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='基于DeepSeek R1选择最优轨迹')
    parser.add_argument('--input', type=str, default='input.jsonl', help='输入文件路径')
    parser.add_argument('--output', type=str, default='output.jsonl', help='输出文件路径')
    args = parser.parse_args()
    if not os.path.exists(args.input):
        logging.error(f"输入文件不存在: {args.input}")
        exit(1)
    # 启动前检查API Key
    if not os.environ.get("DEEPSEEK_API_KEY"):
        logging.error("未检测到DEEPSEEK_API_KEY环境变量，程序终止。")
        exit(1)
    process_file(args.input, args.output)
