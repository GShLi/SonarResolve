#!/usr/bin/env python3
"""
AI自动修复启动脚本
独立的AI代码修复入口点
"""

import argparse

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sonar_tools.ai.ai_code_fixer import AICodeFixer
from sonar_tools.core.config import Config

# 配置日志
logger = Config.setup_logging(__name__)


def main():
    """AI自动修复主函数"""
    parser = argparse.ArgumentParser(
        description="SonarQube Critical问题AI自动修复工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python ai_fix.py                                # 修复所有项目
  python ai_fix.py --project MY_PROJECT           # 修复指定项目
  python ai_fix.py --test                         # 连接测试
  python ai_fix.py --dry-run                      # 试运行（分析但不修复）
        """,
    )

    parser.add_argument(
        "--project", type=str, help="指定项目Key（可选，不指定则处理所有项目）"
    )

    parser.add_argument(
        "--test", action="store_true", help="仅测试连接，不执行实际操作"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="试运行模式，分析问题但不实际修复"
    )

    parser.add_argument(
        "--max-issues", type=int, default=10, help="单次处理的最大问题数量（默认10个）"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("🤖 SonarQube AI自动修复工具启动")
        logger.info(f"📁 项目范围: {args.project or '所有项目'}")
        logger.info(f"🔢 最大处理数量: {args.max_issues}")
        if args.dry_run:
            logger.info("🧪 试运行模式：仅分析不修复")
        logger.info("=" * 60)

        # 初始化AI修复器
        fixer = AICodeFixer()

        if args.test:
            # 连接测试
            logger.info("🔍 开始连接测试...")
            if fixer.test_connection():
                logger.info("✅ 所有连接测试成功")
                return 0
            else:
                logger.error("❌ 连接测试失败")
                return 1

        if args.dry_run:
            logger.info("🧪 试运行模式：分析问题...")
            # TODO: 实现试运行逻辑
            # 可以获取问题列表并分析但不实际修复
            try:
                issues = fixer.sonar_client.get_critical_issues(args.project)
                if not issues:
                    logger.info("✅ 没有发现Critical问题")
                    return 0

                logger.info(f"📊 发现 {len(issues)} 个Critical问题")

                # 按项目分组显示
                issues_by_project = fixer._group_issues_by_project(issues)
                for project_name, project_issues in issues_by_project.items():
                    logger.info(f"  📁 {project_name}: {len(project_issues)} 个问题")
                    for issue in project_issues[:3]:  # 只显示前3个
                        logger.info(f"    🐛 {issue.rule}: {issue.message}")
                    if len(project_issues) > 3:
                        logger.info(f"    ⋮ 还有 {len(project_issues) - 3} 个问题...")

                logger.info("✅ 试运行完成，使用 --dry-run 移除此参数来执行实际修复")
                return 0

            except Exception as e:
                logger.error(f"❌ 试运行失败: {e}")
                return 1

        # 执行实际修复
        logger.info("🚀 开始AI自动修复...")
        success = fixer.process_critical_issues(args.project)

        if success:
            logger.info("🎉 AI自动修复完成")
            return 0
        else:
            logger.error("❌ AI自动修复失败")
            return 1

    except KeyboardInterrupt:
        logger.info("⏹️  用户中断程序")
        return 0
    except Exception as e:
        logger.error(f"💥 程序异常退出: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
