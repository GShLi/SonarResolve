#!/usr/bin/env python3
"""
使用示例和测试脚本
"""

import os
import logging
from config import Config
from sonarqube_client import SonarQubeClient
from jira_client import JiraClient

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sonarqube_connection():
    """测试SonarQube连接"""
    print("测试SonarQube连接...")
    
    try:
        client = SonarQubeClient(Config.SONARQUBE_URL, Config.SONARQUBE_TOKEN)
        
        if client.test_connection():
            print("✓ SonarQube连接成功")
            
            # 获取项目信息
            project_info = client.get_project_info(Config.SONARQUBE_PROJECT_KEY)
            print(f"项目名称: {project_info.get('name', 'N/A')}")
            print(f"项目键: {project_info.get('key', 'N/A')}")
            
            # 获取Critical问题统计
            issues = client.get_critical_issues(Config.SONARQUBE_PROJECT_KEY)
            print(f"Critical问题数量: {len(issues)}")
            
            if issues:
                print("\n前3个Critical问题:")
                for i, issue in enumerate(issues[:3], 1):
                    print(f"{i}. {issue.key} - {issue.get_location_info()}")
                    print(f"   {issue.message}")
        else:
            print("✗ SonarQube连接失败")
            
    except Exception as e:
        print(f"✗ SonarQube测试失败: {e}")

def test_jira_connection():
    """测试Jira连接"""
    print("\n测试Jira连接...")
    
    try:
        client = JiraClient(Config.JIRA_URL, Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        
        if client.test_connection():
            print("✓ Jira连接成功")
            
            # 获取项目信息
            project_info = client.get_project_info(Config.JIRA_PROJECT_KEY)
            if project_info:
                print(f"项目名称: {project_info.get('name', 'N/A')}")
                print(f"项目键: {project_info.get('key', 'N/A')}")
                print(f"项目负责人: {project_info.get('lead', 'N/A')}")
        else:
            print("✗ Jira连接失败")
            
    except Exception as e:
        print(f"✗ Jira测试失败: {e}")

def test_ai_config():
    """测试AI配置"""
    print("\n测试AI配置...")
    
    try:
        Config.validate_ai_config()
        print(f"✓ AI配置验证通过")
        print(f"AI提供商: {Config.AI_PROVIDER}")
        print(f"AI模型: {Config.AI_MODEL}")
        
        # 测试AI客户端初始化
        from ai_client import AIClientFactory
        ai_client = AIClientFactory.create_client()
        print("✓ AI客户端初始化成功")
        
    except Exception as e:
        print(f"✗ AI配置测试失败: {e}")

def test_git_config():
    """测试Git配置"""
    print("\n测试Git配置...")
    
    try:
        Config.validate_git_config()
        print(f"✓ Git配置验证通过")
        print(f"仓库路径: {Config.GIT_REPOSITORY_PATH}")
        print(f"远程URL: {Config.GIT_REMOTE_URL}")
        
        # 测试Git仓库
        if os.path.exists(Config.GIT_REPOSITORY_PATH):
            from git_manager import GitManager
            git_manager = GitManager(Config.GIT_REPOSITORY_PATH)
            print("✓ Git仓库访问成功")
        else:
            print(f"⚠ Git仓库路径不存在: {Config.GIT_REPOSITORY_PATH}")
        
    except Exception as e:
        print(f"✗ Git配置测试失败: {e}")

def test_gitlab_config():
    """测试GitLab配置"""
    print("\n测试GitLab配置...")
    
    if not all([Config.GITLAB_URL, Config.GITLAB_TOKEN, Config.GITLAB_PROJECT_ID]):
        print("⚠ GitLab配置不完整，将跳过Merge Request功能")
        return
    
    try:
        from git_manager import GitLabManager
        gitlab_manager = GitLabManager(
            Config.GITLAB_URL,
            Config.GITLAB_TOKEN,
            Config.GITLAB_PROJECT_ID
        )
        print("✓ GitLab连接成功")
        
    except Exception as e:
        print(f"✗ GitLab测试失败: {e}")

def show_example_config():
    """显示配置示例"""
    print("\n配置示例:")
    print("1. 复制 .env.example 为 .env")
    print("2. 编辑 .env 文件，填入实际配置:")
    print("""
# SonarQube配置
SONARQUBE_URL=https://your-sonarqube-server.com
SONARQUBE_TOKEN=your_sonarqube_token
SONARQUBE_PROJECT_KEY=your_project_key

# Jira配置  
JIRA_URL=https://your-jira-instance.atlassian.net
JIRA_EMAIL=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT

# Git配置
GIT_REPOSITORY_PATH=/path/to/your/local/repository
GIT_REMOTE_URL=https://gitlab.com/your-username/your-project.git
GIT_USERNAME=your_username
GIT_TOKEN=your_git_token

# GitLab配置
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token
GITLAB_PROJECT_ID=your_project_id

# AI配置
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4
""")

def main():
    """主测试函数"""
    print("SonarQube自动修复工具 - 连接测试")
    print("=" * 60)
    
    # 检查基础配置
    try:
        Config.validate_config()
        print("✓ 基础配置验证通过")
    except ValueError as e:
        print(f"✗ 基础配置验证失败: {e}")
        show_example_config()
        return
    
    # 测试各个组件连接
    test_sonarqube_connection()
    test_jira_connection()
    test_ai_config()
    test_git_config()
    test_gitlab_config()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n可用的运行命令:")
    print("1. 仅创建Jira任务: python main.py")
    print("2. 自动修复并创建MR: python auto_fix.py")
    print("3. 仅测试连接: python auto_fix.py --test-only")
    print("4. 自动修复但不创建Jira任务: python auto_fix.py --no-jira")

if __name__ == "__main__":
    main()
