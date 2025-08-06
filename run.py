#!/usr/bin/env python3
"""
快速启动脚本 - 运行各种SonarResolve功能

使用方法:
  python run.py test              # 测试连接
  python run.py projects          # 项目管理
  python run.py jira              # 创建Jira任务
  python run.py autofix           # AI自动修复
  python run.py --help            # 显示帮助
"""

import sys
import os
from pathlib import Path

# 添加src和scripts目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
scripts_path = project_root / "scripts"

sys.path.insert(0, str(src_path))
sys.path.insert(0, str(scripts_path))

def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("\n可用命令:")
    print("  test      - 测试SonarQube和Jira连接")
    print("  projects  - 启动项目管理器")
    print("  jira      - 创建Jira任务（第一阶段）")
    print("  autofix   - AI自动修复（第二阶段）")
    print("\n示例:")
    print("  python run.py test")
    print("  python run.py projects --list")
    print("  python run.py jira")
    print("  python run.py autofix --test-only")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'test':
            # 从scripts目录导入test_connections
            from scripts.test_connections import main as test_main
            test_main()
        elif command == 'projects':
            # 从scripts目录导入project_manager
            from scripts.project_manager import main as project_main
            project_main()
        elif command == 'jira':
            # 从src包导入main模块
            from sonar_resolve.core.main import main as jira_main
            jira_main()
        elif command == 'autofix':
            # 从src包导入auto_fix模块
            from sonar_resolve.core.auto_fix import main as autofix_main
            autofix_main()
        else:
            print(f"未知命令: {command}")
            print("使用 'python run.py --help' 查看可用命令")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保项目依赖已正确安装: poetry install")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
