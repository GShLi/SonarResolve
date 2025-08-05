"""
快速开始脚本
提供安装、配置和运行的便捷入口
"""

import os
import sys
import subprocess

def install_dependencies():
    """安装依赖包"""
    print("安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖包安装失败: {e}")
        return False

def setup_config():
    """设置配置文件"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("创建配置文件...")
            import shutil
            shutil.copy('.env.example', '.env')
            print("✓ 配置文件已创建: .env")
            print("请编辑 .env 文件，填入实际的配置信息")
            return False
        else:
            print("✗ 找不到配置文件模板")
            return False
    else:
        print("✓ 配置文件已存在")
        return True

def main():
    """主函数"""
    print("SonarQube到Jira工具 - 快速开始")
    print("=" * 40)
    
    # 1. 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 2. 设置配置
    config_ready = setup_config()
    
    print("\n下一步操作:")
    if not config_ready:
        print("1. 编辑 .env 文件，填入实际配置")
        print("2. 运行测试: python test_connections.py")
        print("3. 运行主程序: python main.py")
    else:
        print("1. 运行测试: python test_connections.py")
        print("2. 运行主程序: python main.py")
    
    print("\n配置文件说明:")
    print("- SONARQUBE_URL: SonarQube服务器地址")
    print("- SONARQUBE_TOKEN: SonarQube用户令牌")
    print("- SONARQUBE_PROJECT_KEY: 项目键")
    print("- JIRA_URL: Jira服务器地址")
    print("- JIRA_EMAIL: Jira登录邮箱")
    print("- JIRA_API_TOKEN: Jira API令牌")
    print("- JIRA_PROJECT_KEY: Jira项目键")

if __name__ == "__main__":
    main()
