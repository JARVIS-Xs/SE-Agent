#!/bin/bash
# 运行补丁分析脚本

# 决定是否使用测试模式
TEST_MODE=""
if [ "$1" = "--test" ]; then
    TEST_MODE="--test"
    echo "使用测试模式 - 只处理第一个条目"
fi

# 运行Python脚本
echo "开始运行补丁分析..."
python3 conclude_patch.py $TEST_MODE

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "分析完成！结果保存在 filtered_predict_conclusion.json"
else
    echo "执行过程中出现错误"
    exit 1
fi 