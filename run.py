#!/usr/bin/env python3
"""
SonarResolve 统一启动脚本
支持Jira任务创建和AI自动修复
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sonar_tools.core.config import Config

# 配置日志
Config.setup_logging()

def main():
    """统一启动脚本主函数"""
    parser = argparse.ArgumentParser(
        description="SonarResolve - SonarQube问题处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 功能模式:
  jira      创建Jira任务（默认）
  ai-fix    AI自动修复代码

📋 使用示例:
  # Jira任务创建
  python run.py                                   # 默认模式
  python run.py --mode jira                       # 显式指定
  python run.py --mode jira --test                # 连接测试
  
  # AI自动修复
  python run.py --mode ai-fix                     # 修复所有项目
  python run.py --mode ai-fix --project MY_PRJ    # 修复指定项目
  python run.py --mode ai-fix --test              # AI系统测试
  python run.py --mode ai-fix --dry-run           # 试运行模式

🔧 环境变量配置:
  必需配置:
    SONARQUBE_URL, SONARQUBE_TOKEN
    JIRA_URL, JIRA_API_TOKEN, JIRA_PROJECT_LEAD
  
  AI修复额外配置:
    GITLAB_URL, GITLAB_TOKEN
    OPENAI_API_KEY, OPENAI_BASE_URL (LiteLLM代理)
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["jira", "ai-fix"],
        default="jira",
        help="运行模式 (默认: jira)"
    )
    
    parser.add_argument(
        "--project",
        type=str,
        help="指定项目Key（可选）"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="仅测试连接"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式（仅AI修复支持）"
    )
    
    parser.add_argument(
        "--max-issues",
        type=int,
        default=10,
        help="最大处理问题数量（AI修复模式）"
    )

    args = parser.parse_args()

    # 根据模式调用相应的处理逻辑
    if args.mode == "jira":
        from sonar_tools.main import main as jira_main
        # 设置命令行参数供main函数使用
        sys.argv = ["main.py"]
        if args.project:
            sys.argv.extend(["--project", args.project])
        if args.test:
            sys.argv.append("--test")
        if args.dry_run:
            sys.argv.append("--dry-run")
        sys.argv.extend(["--mode", "jira"])
        
        return jira_main()
        
    elif args.mode == "ai-fix":
        from sonar_tools.ai_fix import main as ai_fix_main
        # 设置命令行参数
        sys.argv = ["ai_fix.py"]
        if args.project:
            sys.argv.extend(["--project", args.project])
        if args.test:
            sys.argv.append("--test")
        if args.dry_run:
            sys.argv.append("--dry-run")
        sys.argv.extend(["--max-issues", str(args.max_issues)])
        
        return ai_fix_main()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"💥 启动失败: {e}")
        sys.exit(1)
