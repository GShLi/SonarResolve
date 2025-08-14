#!/usr/bin/env python3
"""
演示AI修复器智能检查逻辑的示例
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sonar_tools.service.sonar_service import SonarService
from sonar_tools.core.models import SonarIssue


def demo_ai_fixer_smart_check():
    """演示AI修复器的智能检查功能"""
    print("🎯 AI修复器智能检查功能演示")
    print("=" * 50)

    # 创建服务实例
    sonar_service = SonarService()

    # 模拟多个issue的处理流程
    issues_data = [
        {
            "key": f"project:security:SecurityIssue{int(time.time())}",
            "description": "全新的安全问题",
            "has_record": False,
            "has_mr": False,
            "mr_status": None,
        },
        {
            "key": f"project:bug:BugIssue{int(time.time())}",
            "description": "已创建记录但未修复的Bug",
            "has_record": True,
            "has_mr": False,
            "mr_status": None,
        },
        {
            "key": f"project:code:CodeSmell{int(time.time())}",
            "description": "已修复并提交MR的代码异味",
            "has_record": True,
            "has_mr": True,
            "mr_status": "created",
        },
        {
            "key": f"project:performance:PerfIssue{int(time.time())}",
            "description": "MR被驳回需要重新修复的性能问题",
            "has_record": True,
            "has_mr": True,
            "mr_status": "rejected",
        },
    ]

    # 预设数据
    for i, issue_data in enumerate(issues_data):
        if issue_data["has_record"]:
            # 创建SonarIssue对象
            test_issue = SonarIssue(
                key=issue_data["key"],
                rule="test:rule",
                message=issue_data["description"],
                component=f"test:project:src/file{i}.py",
                project="test:project",
                severity="CRITICAL",
                line=10 + i,
                creation_date="2023-08-13T10:00:00+0000",
                update_date="2023-08-13T10:00:00+0000",
                status="OPEN",
                type="BUG",
                debt="5min",
                effort="5min",
                tags=["test", "critical"],
            )

            # 创建issue记录
            sonar_service.create_sonar_issue_record(
                sonar_issue=test_issue,
                jira_task_key=f"TEST-{100+i}",
                jira_project_key="TEST",
            )

            if issue_data["has_mr"]:
                # 添加MR记录
                sonar_service.add_issue_mr_record(
                    sonar_issue_key=issue_data["key"],
                    mr_url=f"https://gitlab.example.com/project/repo/-/merge_requests/{700+i}",
                    mr_iid=str(700 + i),
                    mr_title=f"fix(sonar): 修复{issue_data['description']}",
                    mr_description=f"修复描述: {issue_data['description']}",
                    branch_name=f"fix/sonar-issue-{i}",
                    source_branch=f"fix/sonar-issue-{i}",
                    target_branch="main",
                    mr_status=issue_data["mr_status"],
                )

                # 如果是被驳回的MR，更新状态
                if issue_data["mr_status"] == "rejected":
                    sonar_service.update_mr_record_status(
                        mr_url=f"https://gitlab.example.com/project/repo/-/merge_requests/{700+i}",
                        mr_status="rejected",
                        rejection_reason="代码质量不符合要求，需要重构",
                    )

    print("\n🔍 模拟AI修复器处理流程：")
    print("-" * 50)

    # 模拟AI修复器的处理逻辑
    total_issues = len(issues_data)
    need_fix_count = 0
    skip_count = 0

    for i, issue_data in enumerate(issues_data, 1):
        issue_key = issue_data["key"]
        description = issue_data["description"]

        print(f"\n{i}. 处理Issue: {description}")
        print(f"   Key: {issue_key}")

        # 检查是否需要修复（这就是我们添加的逻辑）
        fix_check_result = sonar_service.is_issue_need_fix(issue_key)

        if fix_check_result.get("need_fix", True):
            need_fix_count += 1
            print(f"   🔧 需要修复: {fix_check_result.get('reason')}")
            print(f"   ⚡ 建议操作: {fix_check_result.get('action_required')}")
            print("   → 开始执行修复流程...")
        else:
            skip_count += 1
            print(f"   ⏭️  跳过修复: {fix_check_result.get('reason')}")
            print(f"   💡 建议操作: {fix_check_result.get('action_required')}")
            print("   → 跳过此issue，处理下一个...")

    print("\n📊 处理结果统计：")
    print("-" * 30)
    print(f"   总issue数量: {total_issues}")
    print(f"   需要修复: {need_fix_count}")
    print(f"   已跳过: {skip_count}")
    print(
        f"   效率提升: {skip_count}/{total_issues} = {skip_count/total_issues*100:.1f}%"
    )

    print("\n✨ 智能检查的优势：")
    print("   🎯 避免重复修复已处理的问题")
    print("   ⚡ 提高处理效率，节省资源")
    print("   🔍 精确识别真正需要修复的问题")
    print("   📝 提供清晰的处理建议和原因")
    print("   🔄 支持MR驳回后的重新修复流程")

    return True


if __name__ == "__main__":
    demo_ai_fixer_smart_check()
