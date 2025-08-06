#!/usr/bin/env python
"""
简化的Git管理器测试
"""

import sys
import os
import logging
from pathlib import Path

# 直接导入需要的模块，避免复杂的包导入
try:
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 测试配置加载
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=== Git自动发现功能配置测试 ===")
    
    # 显示配置
    gitlab_url = os.getenv('GITLAB_URL')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    local_workspace = os.getenv('LOCAL_WORKSPACE', './workspace')
    
    print(f"GitLab URL: {gitlab_url}")
    print(f"GitLab Token配置: {'✅' if gitlab_token else '❌'}")
    print(f"本地工作目录: {local_workspace}")
    
    if not gitlab_url or not gitlab_token:
        print("\n❌ GitLab配置不完整")
        print("请在.env文件中配置：")
        print("GITLAB_URL=https://your-gitlab-server.com")
        print("GITLAB_TOKEN=your_gitlab_token")
        sys.exit(1)
    
    # 测试GitLab库导入
    try:
        import gitlab
        print("✅ python-gitlab库已安装")
        
        # 测试GitLab连接
        try:
            gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
            gl.auth()
            print("✅ GitLab连接测试成功")
            
            # 测试搜索项目
            projects = gl.projects.list(search="test", all=False)
            print(f"✅ 项目搜索测试成功，找到{len(projects)}个匹配项目")
            
        except Exception as e:
            print(f"❌ GitLab连接失败: {e}")
            
    except ImportError:
        print("❌ python-gitlab库未安装")
        print("请运行: poetry add python-gitlab")
    
    # 测试工作目录
    workspace_path = Path(local_workspace)
    print(f"\n本地工作目录测试:")
    print(f"路径: {workspace_path.absolute()}")
    
    try:
        workspace_path.mkdir(parents=True, exist_ok=True)
        print("✅ 本地工作目录创建成功")
    except Exception as e:
        print(f"❌ 创建本地工作目录失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("如果所有项目都显示✅，说明配置正确，可以使用Git自动发现功能")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
