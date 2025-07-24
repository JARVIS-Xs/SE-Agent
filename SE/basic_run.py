#!/usr/bin/env python3
"""
SE框架多迭代执行脚本
支持策略驱动的多次SWE-agent迭代执行
"""

import sys
import json
import yaml
import subprocess
import tempfile
import os
import argparse
from pathlib import Path
from datetime import datetime

# 添加SE目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入SE日志系统和轨迹处理器
from core.utils.se_logger import setup_se_logging, get_se_logger
from core.utils.trajectory_processor import TrajectoryProcessor
from core.utils.traj_pool_manager import TrajPoolManager
from core.utils.traj_extractor import TrajExtractor

# 导入operator系统
from operators import create_operator, list_operators


def call_operator(operator_name, workspace_dir, current_iteration, se_config, logger):
    """
    调用指定的operator处理
    
    Args:
        operator_name: operator名称
        workspace_dir: 工作空间根目录 (不带迭代号)
        current_iteration: 当前迭代号
        se_config: SE配置字典
        logger: 日志记录器
        
    Returns:
        operator返回的参数字典 (如 {'instance_templates_dir': 'path'}) 或 None表示失败
    """
    try:
        logger.info(f"开始调用operator: {operator_name}")
        
        # 动态创建operator实例
        operator = create_operator(operator_name, se_config)
        if not operator:
            logger.error(f"无法创建operator实例: {operator_name}")
            return None
        
        logger.info(f"成功创建operator实例: {operator.__class__.__name__}")
        
        # 调用operator.process()方法
        result = operator.process(
            workspace_dir=workspace_dir,
            current_iteration=current_iteration,
            num_workers=se_config.get('num_workers', 1)
        )
        
        if result:
            logger.info(f"Operator {operator_name} 执行成功，返回: {list(result.keys())}")
            return result
        else:
            logger.warning(f"Operator {operator_name} 执行成功但返回空结果")
            return None
            
    except Exception as e:
        logger.error(f"Operator {operator_name} 执行失败: {e}", exc_info=True)
        return None


def create_temp_config(iteration_params, base_config_path):
    """
    为单次迭代创建临时配置文件
    
    Args:
        iteration_params: 迭代参数字典  
        base_config_path: 基础配置文件路径
        
    Returns:
        临时配置文件路径
    """
    # 创建类似test_claude.yaml格式的配置
    # 这样swe_iterator.py会正确合并base_config
    temp_config = {
        'base_config': base_config_path,
        'model': iteration_params['model'],
        'instances': iteration_params['instances'],
        'output_dir': iteration_params['output_dir'],
        'suffix': 'iteration_run',
        'num_workers': iteration_params.get('num_workers', 1)  # 使用传入的num_workers，默认为1
    }
    
    # 处理operator返回的额外参数
    # operator可能返回instance_templates_dir或enhance_history_filter_json等参数
    operator_params = iteration_params.get('operator_params', {})
    if operator_params:
        # 将operator返回的参数添加到临时配置中
        temp_config.update(operator_params)
        print(f"🔧 Operator参数: {list(operator_params.keys())}")
    
    # 创建临时文件
    temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='se_iteration_')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            yaml.dump(temp_config, temp_file, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        # 如果fdopen成功了，不需要手动关闭temp_fd，因为with语句会处理
        # 如果fdopen失败了，需要手动关闭
        try:
            os.close(temp_fd)
        except:
            pass
        # 删除可能已创建的临时文件
        try:
            os.unlink(temp_path)
        except:
            pass
        raise e
    
    return temp_path


def call_swe_iterator(iteration_params, logger, dry_run=False):
    """
    调用swe_iterator.py执行单次迭代
    
    Args:
        iteration_params: 迭代参数字典
        logger: 日志记录器
        dry_run: 是否为演示模式
        
    Returns:
        执行结果
    """
    base_config_path = iteration_params['base_config']
    
    try:
        # 创建临时配置文件
        logger.debug(f"创建临时配置文件，基于: {base_config_path}")
        temp_config_path = create_temp_config(iteration_params, base_config_path)
        
        logger.info(f"临时配置文件: {temp_config_path}")
        
        # 打印实际配置参数以供确认（无论是否演示模式都显示）
        print("📋 实际执行配置：")
        try:
            with open(temp_config_path, 'r', encoding='utf-8') as f:
                temp_config_content = yaml.safe_load(f)
            
            # 关键参数显示
            print(f"  - base_config: {temp_config_content.get('base_config', 'N/A')}")
            print(f"  - model.name: {temp_config_content.get('model', {}).get('name', 'N/A')}")
            print(f"  - instances.json_file: {temp_config_content.get('instances', {}).get('json_file', 'N/A')}")
            print(f"  - output_dir: {temp_config_content.get('output_dir', 'N/A')}")
            print(f"  - num_workers: {temp_config_content.get('num_workers', 'N/A')}")
            print(f"  - suffix: {temp_config_content.get('suffix', 'N/A')}")
            
            logger.debug(f"临时配置内容: {json.dumps(temp_config_content, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"  ⚠️ 无法读取配置文件: {e}")
        
        if dry_run:
            logger.warning("演示模式：跳过实际执行")
            return {"status": "skipped", "reason": "dry_run"}
        
        # 调用swe_iterator.py
        logger.info("开始执行SWE-agent迭代")
        
        # 动态确定SE框架根目录和项目根目录
        se_root = Path(__file__).parent  # SE目录
        project_root = se_root.parent    # 630_swe目录
        swe_iterator_path = se_root / "core" / "swe_iterator.py"
        
        print(f"🚀 执行命令: python {swe_iterator_path} {temp_config_path}")
        print(f"📁 工作目录: {project_root}")
        print("=" * 60)
        
        cmd = ["python", str(swe_iterator_path), temp_config_path]
        
        # 不使用capture_output，让SWE-agent输出直接显示
        result = subprocess.run(
            cmd,
            cwd=str(project_root),  # 使用动态确定的项目根目录
            text=True
        )
        
        print("=" * 60)
        if result.returncode == 0:
            logger.info("迭代执行成功")
            print("✅ 迭代执行成功")
            return {"status": "success"}
        else:
            logger.error(f"迭代执行失败，返回码: {result.returncode}")
            print(f"❌ 迭代执行失败，返回码: {result.returncode}")
            return {"status": "failed", "returncode": result.returncode}
            
    except Exception as e:
        logger.error(f"调用swe_iterator时出错: {e}", exc_info=True)
        return {"status": "error", "exception": str(e)}
    finally:
        # 清理临时文件
        try:
            if 'temp_config_path' in locals():
                os.unlink(temp_config_path)
                logger.debug(f"清理临时文件: {temp_config_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")


def main():
    """主函数：策略驱动的多迭代执行"""
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='SE框架多迭代执行脚本')
    parser.add_argument('--config', default="SE/configs/se_configs/test_deepseek_se.yaml", 
                       help='SE配置文件路径')
    parser.add_argument('--mode', choices=['demo', 'execute'], default='execute',
                       help='运行模式: demo=演示模式, execute=直接执行')
    args = parser.parse_args()
    
    print("=== SE框架多迭代执行 ===")
    print(f"配置文件: {args.config}")
    print(f"运行模式: {args.mode}")
    
    try:
        # 读取配置文件
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 生成timestamp并替换输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config['output_dir'].replace("{timestamp}", timestamp)
        
        # 设置日志系统
        log_file = setup_se_logging(output_dir)
        print(f"日志文件: {log_file}")
        
        # 获取logger实例
        logger = get_se_logger("basic_run", emoji="⚙️")
        logger.info("SE框架多迭代执行启动")
        logger.debug(f"使用配置文件: {args.config}")
        logger.info(f"生成timestamp: {timestamp}")
        logger.info(f"实际输出目录: {output_dir}")
        
        # 初始化轨迹池管理器
        traj_pool_path = os.path.join(output_dir, "traj.pool")
        
        # 创建LLM客户端用于轨迹总结
        llm_client = None
        try:
            from core.utils.llm_client import LLMClient
            # 使用operator_models配置，如果没有则使用主模型配置
            llm_client = LLMClient.from_se_config(config, use_operator_model=True)
            logger.info(f"LLM客户端初始化成功: {llm_client.config['name']}")
        except Exception as e:
            logger.warning(f"LLM客户端初始化失败，将使用备用总结: {e}")
        
        traj_pool_manager = TrajPoolManager(traj_pool_path, llm_client)
        traj_pool_manager.initialize_pool()
        logger.info(f"轨迹池初始化: {traj_pool_path}")
        print(f"🏊 轨迹池: {traj_pool_path}")
        
        print(f"\n📊 配置概览:")
        print(f"  基础配置: {config['base_config']}")
        print(f"  模型: {config['model']['name']}")
        print(f"  实例文件: {config['instances']['json_file']}")
        print(f"  输出目录: {output_dir}")
        print(f"  迭代次数: {len(config['strategy']['iterations'])}")
        
        # 真正执行策略中的每个迭代
        iterations = config['strategy']['iterations']
        for i, iteration in enumerate(iterations, 1):
            logger.info(f"开始第{i}次迭代")
            print(f"\n=== 第{i}次迭代调用 ===")
            
            # 构建迭代参数
            # 注意：只有以下三个参数在迭代间会发生变化：
            # 1. base_config - 每次迭代使用不同的SWE-agent基础配置
            # 2. operator - 每次迭代可能使用不同的算子策略 
            # 3. output_dir - 每次迭代独立的输出目录
            # 其他参数(model, instances, num_workers)在所有迭代中保持一致
            iteration_output_dir = f"{output_dir}/iteration_{i}"
            iteration_params = {
                "base_config": iteration['base_config'],      # 🔄 可变：SWE基础配置
                "operator": iteration.get('operator'),       # 🔄 可变：算子策略
                "model": config['model'],                     # ✋ 固定：模型配置
                "instances": config['instances'],             # ✋ 固定：实例配置
                "output_dir": iteration_output_dir,           # 🔄 可变：迭代输出目录
                "num_workers": config.get('num_workers', 1)  # ✋ 固定：并发数配置
            }
            
            # 处理operator返回的额外参数
            operator_name = iteration.get('operator')
            if operator_name:
                print(f"🔧 调用算子: {operator_name}")
                logger.info(f"执行算子: {operator_name}")
                
                # 调用operator处理（传递workspace_dir而不是iteration_output_dir）
                operator_result = call_operator(operator_name, output_dir, i, config, logger)
                if operator_result:
                    iteration_params['operator_params'] = operator_result
                    print(f"✅ Operator {operator_name} 执行成功")
                    print(f"📋 生成参数: {list(operator_result.keys())}")
                else:
                    print(f"⚠️  Operator {operator_name} 执行失败，继续执行但不使用增强")
                    logger.warning(f"Operator {operator_name} 执行失败，继续执行但不使用增强")
            else:
                print(f"🔄 无算子处理")
                logger.debug(f"第{i}次迭代无算子处理")
            
            logger.debug(f"第{i}次迭代参数: {json.dumps(iteration_params, ensure_ascii=False)}")
            print(f"使用配置: {iteration['base_config']}")
            print(f"算子: {iteration.get('operator', 'None')}")
            print(f"输出目录: {iteration_output_dir}")
            
            # 根据模式执行
            if args.mode == 'execute':
                logger.info(f"直接执行模式：第{i}次迭代")
                result = call_swe_iterator(iteration_params, logger, dry_run=False)
                print(f"执行结果: {result['status']}")
                
                # 如果迭代成功，生成.tra文件
                if result['status'] == 'success':
                    logger.info(f"开始为第{i}次迭代生成.tra文件")
                    try:
                        processor = TrajectoryProcessor()
                        iteration_dir = Path(iteration_output_dir)
                        
                        # 处理当前iteration目录
                        tra_stats = processor.process_iteration_directory(iteration_dir)
                        
                        if tra_stats and tra_stats.get('total_tra_files', 0) > 0:
                            logger.info(f"第{i}次迭代.tra文件生成完成: "
                                      f"{tra_stats['total_tra_files']}个文件, "
                                      f"~{tra_stats['total_tokens']}tokens")
                            print(f"📝 生成了 {tra_stats['total_tra_files']} 个.tra文件")
                            
                            # 更新轨迹池
                            logger.info(f"开始更新轨迹池: 第{i}次迭代")
                            try:
                                # 从实际数据中提取instance信息和.tra/.patch文件内容
                                extractor = TrajExtractor()
                                instance_data_list = extractor.extract_instance_data(iteration_dir)
                                
                                if instance_data_list:
                                    for instance_name, problem_description, trajectory_content, patch_content in instance_data_list:
                                        traj_pool_manager.add_iteration_summary(
                                            instance_name=instance_name,
                                            iteration=i,
                                            trajectory_content=trajectory_content,
                                            patch_content=patch_content,
                                            problem_description=problem_description
                                        )
                                    
                                    logger.info(f"成功提取并处理了 {len(instance_data_list)} 个实例")
                                else:
                                    logger.warning(f"第{i}次迭代没有找到有效的实例数据")
                                    print("⚠️ 没有找到有效的实例数据")
                                
                                # 显示轨迹池统计
                                pool_stats = traj_pool_manager.get_pool_stats()
                                logger.info(f"轨迹池更新完成: {pool_stats['total_instances']}实例, "
                                          f"{pool_stats['total_iterations']}总迭代")
                                print(f"🏊 轨迹池更新: {pool_stats['total_instances']}实例, "
                                      f"{pool_stats['total_iterations']}总迭代")
                                
                            except Exception as pool_error:
                                logger.error(f"第{i}次迭代轨迹池更新失败: {pool_error}")
                                print(f"⚠️ 轨迹池更新失败: {pool_error}")
                                # 不因为轨迹池更新失败而中断整个流程
                        else:
                            logger.warning(f"第{i}次迭代未生成.tra文件")
                            print("⚠️ 未生成.tra文件（可能没有有效轨迹）")
                            
                    except Exception as tra_error:
                        logger.error(f"第{i}次迭代生成.tra文件失败: {tra_error}")
                        print(f"⚠️ .tra文件生成失败: {tra_error}")
                        # 不因为.tra文件生成失败而中断整个流程
                
                if result['status'] == 'failed':
                    logger.error(f"第{i}次迭代执行失败，停止后续迭代")
                    break
            else:  # demo mode
                logger.info(f"演示模式：第{i}次迭代")
                result = call_swe_iterator(iteration_params, logger, dry_run=True)
                print(f"演示结果: {result['status']}")
                print("📝 演示模式：跳过.tra文件生成")
            
        logger.info("所有迭代准备完成")
        
        # 显示最终轨迹池统计
        try:
            final_pool_stats = traj_pool_manager.get_pool_stats()
            logger.info(f"最终轨迹池统计: {final_pool_stats}")
        except Exception as e:
            logger.warning(f"获取轨迹池统计失败: {e}")
            final_pool_stats = {"total_instances": 0, "total_iterations": 0}
        
        print(f"\n🎯 执行总结:")
        print(f"  ✅ 解析{len(iterations)}个迭代配置")
        print(f"  ✅ 时间戳: {timestamp}")
        print(f"  ✅ 日志文件: {log_file}")
        print(f"  🏊 轨迹池: {final_pool_stats['total_instances']}实例, "
              f"{final_pool_stats['total_iterations']}总迭代")
        print(f"  🏊 轨迹池文件: {traj_pool_path}")
        
        logger.info("SE框架多迭代执行完成")
        
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"运行出错: {e}", exc_info=True)
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()