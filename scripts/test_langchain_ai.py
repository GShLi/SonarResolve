#!/usr/bin/env python
"""
测试增强版 AI 客户端功能（优化的提示词）
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sonar_resolve.clients.ai_client import EnhancedOpenAIClient, EnhancedAnthropicClient, AIClientFactory
from src.sonar_resolve.core.config import Config
from src.sonar_resolve.core.models import SonarIssue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_enhanced_clients():
    """测试增强版 AI 客户端"""
    print("=== 测试增强版 AI 客户端（优化提示词）===")
    
    # 测试配置
    print(f"AI Provider: {Config.AI_PROVIDER}")
    print(f"AI Model: {Config.AI_MODEL}")
    print(f"OpenAI API Key配置: {'✅' if Config.OPENAI_API_KEY else '❌'}")
    print(f"Anthropic API Key配置: {'✅' if Config.ANTHROPIC_API_KEY else '❌'}")
    
    # 创建测试问题
    test_issue = SonarIssue(
        key="test-issue-1",
        rule="java:S1192",
        severity="CRITICAL",
        message="String literals should not be duplicated",
        component="src/main/java/Test.java",
        project="test-project",
        type="CODE_SMELL",
        line=10,
        creation_date="2024-01-01T10:00:00Z",
        update_date="2024-01-01T10:00:00Z",
        status="OPEN",
        debt="5min",
        effort="5min",
        tags=["bug", "security"]
    )
    
    test_code = '''public class Test {
    public void method1() {
        String message = "Hello World";
        System.out.println("Hello World");
    }
    
    public void method2() {
        String greeting = "Hello World";
        System.out.println("Hello World");
    }
}'''
    
    try:
        # 测试AI客户端工厂
        print(f"\n1. 测试增强版AI客户端工厂...")
        ai_client = AIClientFactory.create_client()
        print(f"✅ AI客户端创建成功: {type(ai_client).__name__}")
        
        # 测试代码修复
        print(f"\n2. 测试代码修复功能...")
        print("使用优化的提示词结构:")
        print("- 分离的系统提示词和用户提示词")
        print("- 结构化的问题信息")
        print("- 专门针对SonarQube Critical问题优化")
        
        fixed_content = ai_client.fix_code_issue(test_issue, test_code)
        
        if fixed_content:
            print(f"✅ 代码修复成功")
            print(f"修复后的代码长度: {len(fixed_content)} 字符")
            if fixed_content.strip() != test_code.strip():
                print("✅ 代码确实被修改了")
                print("\n修复后的代码预览:")
                print("-" * 40)
                print(fixed_content[:200] + "..." if len(fixed_content) > 200 else fixed_content)
                print("-" * 40)
            else:
                print("ℹ️ 代码没有被修改（可能不需要修复）")
        else:
            print(f"❌ 代码修复失败")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装相应的AI库:")
        print("- OpenAI: poetry add openai")
        print("- Anthropic: poetry add anthropic")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_prompt_comparison():
    """对比提示词优化效果"""
    print("\n=== 提示词优化对比 ===")
    
    print("✅ 增强版提示词特性:")
    print("1. 系统角色明确: 资深代码修复专家")
    print("2. 结构化问题信息: 规则代码、严重程度、问题描述等")
    print("3. 清晰的修复要求: 5个具体要求点")
    print("4. 代码块标记: 使用语言标识的代码块")
    print("5. 输出格式严格: 只返回修复后代码，无解释")
    
    print("\n📊 提示词结构:")
    print("- SystemMessage: 设定专家角色和修复规范")
    print("- HumanMessage: 结构化的问题信息和修复要求")
    print("- 代码清理: 自动移除AI返回的代码块标记")

def test_specific_client():
    """测试特定的增强版客户端"""
    print("\n=== 测试特定增强版客户端 ===")
    
    # 测试OpenAI客户端
    if Config.OPENAI_API_KEY:
        try:
            print("测试增强版OpenAI客户端...")
            openai_client = EnhancedOpenAIClient(
                api_key=Config.OPENAI_API_KEY,
                model="gpt-3.5-turbo"  # 使用更便宜的模型测试
            )
            print("✅ 增强版OpenAI客户端初始化成功")
            print("   特性: 分离的系统/用户提示词，优化的问题描述格式")
        except Exception as e:
            print(f"❌ 增强版OpenAI客户端测试失败: {e}")
    
    # 测试Anthropic客户端
    if Config.ANTHROPIC_API_KEY:
        try:
            print("测试增强版Anthropic客户端...")
            anthropic_client = EnhancedAnthropicClient(
                api_key=Config.ANTHROPIC_API_KEY,
                model="claude-3-haiku-20240307"  # 使用更便宜的模型测试
            )
            print("✅ 增强版Anthropic客户端初始化成功")
            print("   特性: 专门为Claude优化的提示词结构")
        except Exception as e:
            print(f"❌ 增强版Anthropic客户端测试失败: {e}")

if __name__ == "__main__":
    print("SonarResolve - 增强版AI客户端测试（优化提示词）")
    print("=" * 60)
    
    test_enhanced_clients()
    test_prompt_comparison()
    test_specific_client()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("\n✨ 增强版特性说明:")
    print("1. 🎯 优化的提示词结构，专门针对SonarQube问题修复")
    print("2. 🔧 分离的系统和用户提示词，提高AI理解准确性")
    print("3. 📋 结构化的问题信息展示，包含完整的SonarQube上下文")
    print("4. 🚀 兼容Python 3.8+，无需升级Python版本")
    print("5. 💡 自动代码块清理，确保输出格式正确")
    print("\n⚠️ 注意: 虽然没有使用LangChain框架，但提示词已经按照")
    print("   LangChain的最佳实践进行了优化，具备相似的效果。")
