#!/usr/bin/env python3
"""
测试智能代码修复功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sonar_tools.clients.git_client import AutoFixProcessor


def test_smart_fix():
    """测试智能修复功能"""
    
    # 创建测试文件内容
    test_content = '''def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):  # SonarQube问题：应该直接遍历列表
        total += numbers[i]
    return total

def main():
    nums = [1, 2, 3, 4, 5]
    result = calculate_sum(nums)
    print(f"Sum: {result}")
'''

    # 模拟SonarQube问题和AI修复
    test_fix = {
        "file_path": "test_file.py",
        "fixed_code": '''def calculate_sum(numbers):
    total = 0
    for number in numbers:  # 修复：直接遍历列表
        total += number
    return total

def main():
    nums = [1, 2, 3, 4, 5]
    result = calculate_sum(nums)
    print(f"Sum: {result}")''',
        "code_snippet": '''文件: test_file.py
==================================================
   1: def calculate_sum(numbers):
   2:     total = 0
→  3:     for i in range(len(numbers)):  # SonarQube问题：应该直接遍历列表
   4:         total += numbers[i]
   5:     return total''',
        "line": 3,
        "language": "python",
        "issue_key": "test_issue",
        "rule": "python:S1481"
    }
    
    # 创建测试文件
    test_file = Path("test_file.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 测试修复
        processor = AutoFixProcessor()
        success = processor._apply_fix(test_file, test_fix)
        
        if success:
            print("✅ 智能修复测试成功")
            # 显示修复后的内容
            with open(test_file, "r", encoding="utf-8") as f:
                fixed_content = f.read()
            print("\n修复后的代码:")
            print("=" * 50)
            print(fixed_content)
        else:
            print("❌ 智能修复测试失败")
            
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    test_smart_fix()
