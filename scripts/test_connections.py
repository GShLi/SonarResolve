#!/usr/bin/env python3
"""
使用示例和测试脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sonar_resolve.core.config import Config
from sonar_resolve.clients.sonarqube_client import SonarQubeClient
from sonar_resolve.clients.jira_client import JiraClient
from sonar_resolve.core.project_discovery import ProjectDiscovery

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_project_discovery():
    """测试项目发现功能"""
    print("\n测试项目发现功能...")
    
    try:
        sonar_client = SonarQubeClient(Config.SONARQUBE_URL, Config.SONARQUBE_TOKEN)
        jira_client = JiraClient(Config.JIRA_URL, Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        
        project_discovery = ProjectDiscovery(sonar_client, jira_client)
        
        # 获取所有项目
        available_projects = project_discovery.list_available_projects()
        
        print(f"✓ 发现 {len(available_projects['sonar_projects'])} 个SonarQube项目")
        print(f"✓ 发现 {len(available_projects['jira_projects'])} 个Jira项目")
        
        # 显示前几个项目
        if available_projects['sonar_projects']:
            print("\nSonarQube项目示例:")
            for project in available_projects['sonar_projects'][:3]:
                print(f"  - {project['name']} ({project['key']})")
        
        if available_projects['jira_projects']:
            print("\nJira项目示例:")
            for project in available_projects['jira_projects'][:3]:
                print(f"  - {project['name']} ({project['key']})")
        
        # 尝试自动匹配
        git_url = getattr(Config, 'GIT_REMOTE_URL', None)
        best_mapping = project_discovery.get_best_project_mapping(git_url)
        
        if best_mapping:
            print(f"\n✓ 找到最佳项目匹配:")
            print(f"  SonarQube: {best_mapping.sonar_name} ({best_mapping.sonar_key})")
            print(f"  Jira: {best_mapping.jira_name} ({best_mapping.jira_key})")
            print(f"  相似度: {best_mapping.similarity_score:.2f}")
            print(f"  匹配原因: {best_mapping.mapping_reason}")
        else:
            print("⚠ 未找到匹配的项目")
            
    except Exception as e:
        print(f"✗ 项目发现测试失败: {e}")

def test_sonarqube_connection():
    """测试SonarQube连接"""
    print("测试SonarQube连接...")
    
    try:
        client = SonarQubeClient(Config.SONARQUBE_URL, Config.SONARQUBE_TOKEN)
        
        if client.test_connection():
            print("✓ SonarQube连接成功")
            
            # 获取项目信息 - 不再依赖固定的项目KEY
            print("获取SonarQube项目列表...")
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
            
            # 获取项目信息 - 不再依赖固定的项目KEY
            print("获取Jira项目列表...")
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
        from sonar_resolve.clients.ai_client import AIClientFactory
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
            from sonar_resolve.utils.git_manager import GitManager
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
        from sonar_resolve.utils.git_manager import GitLabManager
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

# Jira配置  
JIRA_URL=https://your-jira-instance.atlassian.net
JIRA_EMAIL=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token

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
    test_project_discovery()
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
