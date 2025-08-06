#!/usr/bin/env python
"""
测试GitLab自动仓库发现功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sonar_resolve.utils.git_manager import GitRepositoryManager
from src.sonar_resolve.core.config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_git_auto_discovery():
    """测试Git自动发现功能"""
    print("=== 测试GitLab自动仓库发现功能 ===")
    
    try:
        # 创建Git仓库管理器
        repo_manager = GitRepositoryManager()
        
        # 测试项目名（替换为实际的项目名）
        test_project_name = "test-project"  # 这里需要替换为你的实际项目名
        
        print(f"\n1. 测试GitLab连接和项目搜索...")
        print(f"GitLab URL: {Config.GITLAB_URL}")
        print(f"本地工作目录: {Config.LOCAL_WORKSPACE}")
        
        # 搜索项目
        repo_info = repo_manager.find_repository_by_project_name(test_project_name)
        
        if repo_info:
            print(f"\n✅ 找到匹配的GitLab项目:")
            print(f"   项目名: {repo_info['name']}")
            print(f"   完整路径: {repo_info['full_path']}")
            print(f"   克隆URL: {repo_info['clone_url']}")
            print(f"   默认分支: {repo_info['default_branch']}")
            
            # 测试本地路径生成
            local_path = repo_manager.get_local_repo_path(test_project_name)
            print(f"   本地路径: {local_path}")
            
            print(f"\n2. 测试仓库克隆/更新...")
            success, local_repo_path = repo_manager.clone_or_update_repository(test_project_name)
            
            if success:
                print(f"✅ 仓库准备成功: {local_repo_path}")
            else:
                print(f"❌ 仓库准备失败")
        else:
            print(f"❌ 未找到匹配的GitLab项目: {test_project_name}")
            print("请检查:")
            print("1. GitLab URL和Token是否正确配置")
            print("2. 项目名是否正确")
            print("3. 是否有访问该项目的权限")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_config():
    """测试配置"""
    print("=== 测试配置 ===")
    
    print(f"SonarQube URL: {Config.SONARQUBE_URL}")
    print(f"GitLab URL: {Config.GITLAB_URL}")
    print(f"GitLab Token配置: {'✅' if Config.GITLAB_TOKEN else '❌'}")
    print(f"本地工作目录: {Config.LOCAL_WORKSPACE}")
    
    try:
        Config.validate_config()
        print("✅ 基础配置验证通过")
    except Exception as e:
        print(f"❌ 基础配置验证失败: {e}")
    
    try:
        Config.validate_gitlab_config()
        print("✅ GitLab配置验证通过")
    except Exception as e:
        print(f"❌ GitLab配置验证失败: {e}")

if __name__ == "__main__":
    print("SonarResolve - Git自动发现功能测试")
    print("=" * 50)
    
    test_config()
    print("\n" + "=" * 50)
    test_git_auto_discovery()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("\n使用说明:")
    print("1. 确保在.env文件中正确配置了GitLab URL和Token")
    print("2. 修改test_project_name为你的实际项目名进行测试")
    print("3. 系统会自动根据SonarQube项目名查找对应的GitLab仓库")
    print("4. 首次运行会克隆仓库，后续运行会执行git pull更新")
