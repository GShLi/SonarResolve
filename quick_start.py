#!/usr/bin/env python3
"""
SonarResolve 快速入门脚本

这个脚本会引导你完成项目的初始设置和基本使用。
"""

import os
import sys
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🚀 SonarQube自动修复与Jira集成工具 - 快速入门")
    print("=" * 60)
    print()

def check_environment():
    """检查环境配置"""
    print("📋 检查环境配置...")
    
    # 检查.env文件
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("❌ 未找到.env文件")
            print("📝 请复制.env.example到.env并填写配置:")
            print(f"   copy {env_example} {env_file}")
            return False
        else:
            print("❌ 未找到配置文件模板")
            return False
    
    print("✅ 找到.env配置文件")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8, 1):
        print("⚠️  Python版本过低，建议使用3.8.1+")
        print("📖 查看docs/PYTHON_COMPATIBILITY.md了解详情")
    
    return True

def check_dependencies():
    """检查依赖安装"""
    print("\n📦 检查依赖安装...")
    
    try:
        import requests
        import jira
        print("✅ 核心依赖已安装")
        
        # 检查AI依赖
        try:
            import openai
            import anthropic
            print("✅ AI依赖已安装")
            ai_available = True
        except ImportError:
            print("⚠️  AI依赖未安装（可选功能）")
            print("💡 使用 'poetry install --extras ai' 安装AI功能")
            ai_available = False
        
        return True, ai_available
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        print("🔧 请运行: poetry install")
        return False, False

def show_usage_guide():
    """显示使用指南"""
    print("\n📚 使用指南:")
    print("-" * 40)
    
    print("\n1️⃣  测试连接:")
    print("   python run.py test")
    
    print("\n2️⃣  项目管理:")
    print("   python run.py projects --list        # 列出所有项目")
    print("   python run.py projects --discover    # 自动匹配项目")
    print("   python run.py projects --interactive # 交互式选择")
    
    print("\n3️⃣  创建Jira任务:")
    print("   python run.py jira")
    
    print("\n4️⃣  AI自动修复 (需要AI依赖):")
    print("   python run.py autofix")
    print("   python run.py autofix --test-only    # 仅测试AI连接")
    
    print("\n📖 更多信息:")
    print("   - README.md: 完整使用文档")
    print("   - docs/PROJECT_STRUCTURE.md: 项目结构说明")
    print("   - docs/PYTHON_COMPATIBILITY.md: Python版本兼容性")

def interactive_setup():
    """交互式设置"""
    print("\n🎯 交互式设置向导")
    print("-" * 40)
    
    choice = input("是否要运行连接测试？ (y/n): ").lower().strip()
    if choice == 'y':
        print("\n🔍 运行连接测试...")
        try:
            # 添加路径
            sys.path.insert(0, "scripts")
            from scripts.test_connections import main as test_main
            test_main()
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            print("请检查.env配置和网络连接")
            return
    
    print("\n🎉 设置完成！")
    print("现在可以使用以下命令:")
    print("  python run.py projects --discover  # 发现项目匹配")
    print("  python run.py jira                 # 创建Jira任务")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请先配置环境变量")
        return
    
    # 检查依赖
    deps_ok, ai_available = check_dependencies()
    if not deps_ok:
        print("\n❌ 依赖检查失败，请先安装依赖")
        return
    
    # 显示使用指南
    show_usage_guide()
    
    # 交互式设置
    print("\n" + "=" * 60)
    choice = input("是否要进行交互式设置？ (y/n): ").lower().strip()
    if choice == 'y':
        interactive_setup()
    else:
        print("\n🎉 环境检查完成！可以开始使用SonarResolve了。")

if __name__ == "__main__":
    main()
