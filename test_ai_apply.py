#!/usr/bin/env python3
"""
AI代码应用测试脚本
演示大模型智能应用代码修复的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ai_code_application():
    """测试AI代码应用功能"""
    print("🤖 AI代码应用测试")
    print("=" * 50)
    
    try:
        # 导入AI客户端
        from sonar_tools.clients.langchain_client import LangChainClient
        
        print("✅ AI客户端初始化成功")
        ai_client = LangChainClient()
        
        # 示例：原始文件内容（包含问题的Python代码）
        original_content = """def calculate_average(numbers):
    # 这里有一个除零错误的风险
    total = sum(numbers)
    count = len(numbers)
    return total / count  # 当numbers为空时会抛出ZeroDivisionError

def process_data(data_list):
    if data_list:
        avg = calculate_average(data_list)
        print(f"平均值: {avg}")
    else:
        print("数据列表为空")

# 测试代码
test_data = [1, 2, 3, 4, 5]
process_data(test_data)
process_data([])  # 这会导致问题
"""
        
        # AI修复后的代码
        fixed_code = """def calculate_average(numbers):
    # 修复除零错误
    if not numbers:
        return 0
    total = sum(numbers)
    count = len(numbers)
    return total / count

def process_data(data_list):
    if data_list:
        avg = calculate_average(data_list)
        print(f"平均值: {avg}")
    else:
        print("数据列表为空")

# 测试代码
test_data = [1, 2, 3, 4, 5]
process_data(test_data)
process_data([])  # 现在安全了
"""
        
        # 问题数据
        issue_data = {
            "component": "test_example.py",
            "line": 4,
            "language": "python", 
            "message": "Potential division by zero error",
            "code_snippet": "    return total / count  # 当numbers为空时会抛出ZeroDivisionError",
            "key": "test_issue_001"
        }
        
        print("\n📝 原始代码:")
        print("-" * 30)
        print(original_content)
        
        print("\n🔧 AI修复后的代码:")
        print("-" * 30)
        print(fixed_code)
        
        print("\n🤖 请求AI智能应用修复...")
        
        # 使用AI应用修复
        result = ai_client.apply_code_fix(original_content, fixed_code, issue_data)
        
        print(f"\n📊 AI应用结果:")
        print(f"成功: {result.get('success')}")
        print(f"策略: {result.get('strategy_used')}")
        print(f"信心等级: {result.get('confidence')}/10")
        print(f"修改摘要: {result.get('changes_summary')}")
        
        if result.get('warnings'):
            print(f"⚠️  警告: {', '.join(result['warnings'])}")
            
        if result.get('success'):
            print("\n✅ 修复应用后的代码:")
            print("-" * 30)
            print(result['modified_content'])
            
            # 验证修复
            print("\n🔍 验证修复质量...")
            validation = ai_client.validate_fix(
                original_content, 
                result['modified_content'], 
                issue_data
            )
            
            print(f"总分: {validation.get('overall_score')}/20")
            print(f"合规检查: {validation.get('compliance_check')}")
            print(f"质量等级: {validation.get('quality_grade')}")
            print(f"审批状态: {validation.get('approval_status')}")
            
        else:
            print("❌ AI应用失败")
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装所需依赖: pip install langchain langchain-openai")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请检查环境变量配置（OPENAI_API_KEY等）")

def test_traditional_vs_ai():
    """对比传统方法和AI方法"""
    print("\n🔬 传统方法 vs AI方法对比")
    print("=" * 50)
    
    # 模拟传统方法的问题
    print("🔧 传统方法的问题:")
    print("1. 简单字符串替换 - 格式不匹配")
    print("2. 行号范围替换 - 上下文丢失")  
    print("3. 模式匹配 - 精度不够")
    print("4. 函数块替换 - 范围判断困难")
    
    print("\n🤖 AI方法的优势:")
    print("1. 智能理解代码语义和结构")
    print("2. 精确定位需要修改的位置")
    print("3. 保持代码格式和风格一致")
    print("4. 避免误修改无关代码")
    print("5. 提供信心评估和风险警告")
    
    print("\n📈 推荐使用策略:")
    print("1. 优先使用AI智能应用（信心≥7分）")
    print("2. AI失败时回退到传统多策略方法")
    print("3. 根据文件类型和项目特点调整阈值")

if __name__ == "__main__":
    print("🚀 开始AI代码应用测试")
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量")
        print("请在.env文件中配置或设置环境变量")
        print("示例: OPENAI_API_KEY=your_api_key_here")
        
    test_ai_code_application()
    test_traditional_vs_ai()
    
    print("\n✅ 测试完成")
    print("\n📚 更多信息请查看: docs/SMART_FIX_GUIDE.md")
