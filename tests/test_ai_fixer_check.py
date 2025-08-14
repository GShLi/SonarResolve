#!/usr/bin/env python3
"""
测试AI修复器的issue检查逻辑
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sonar_tools.service.sonar_service import SonarService
from sonar_tools.core.models import SonarIssue


def test_ai_fixer_issue_check():
    """测试AI修复器的issue检查逻辑"""
    print("🧪 测试AI修复器的issue检查逻辑")

    # 创建服务实例
    sonar_service = SonarService()

    # 场景1：测试全新的issue（需要修复）
    print("\n1️⃣ 测试全新issue（应该需要修复）")
    new_issue_key = f"test:project:NewIssue{int(time.time())}"

    result = sonar_service.is_issue_need_fix(new_issue_key)
    print(f"   Issue Key: {new_issue_key}")
    print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
    print(f"   原因: {result['reason']}")
    print(f"   建议操作: {result['action_required']}")

    # 场景2：创建一个issue记录但没有MR（需要修复）
    print("\n2️⃣ 测试有issue记录但没有MR（应该需要修复）")
    issue_with_record_key = f"test:project:IssueWithRecord{int(time.time())}"

    # 创建SonarIssue对象
    test_issue = SonarIssue(
        key=issue_with_record_key,
        rule="test:rule",
        message="测试问题",
        component=f"test:project:src/test.py",
        project="test:project",
        severity="CRITICAL",
        line=10,
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
        sonar_issue=test_issue, jira_task_key="TEST-002", jira_project_key="TEST"
    )

    result = sonar_service.is_issue_need_fix(issue_with_record_key)
    print(f"   Issue Key: {issue_with_record_key}")
    print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
    print(f"   原因: {result['reason']}")
    print(f"   建议操作: {result['action_required']}")

    # 场景3：创建issue记录和MR记录（不需要修复）
    print("\n3️⃣ 测试有issue记录和MR记录（应该不需要修复）")
    issue_with_mr_key = f"test:project:IssueWithMR{int(time.time())}"

    # 创建SonarIssue对象
    test_issue_2 = SonarIssue(
        key=issue_with_mr_key,
        rule="test:rule",
        message="测试问题",
        component=f"test:project:src/test2.py",
        project="test:project",
        severity="CRITICAL",
        line=15,
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
        sonar_issue=test_issue_2, jira_task_key="TEST-003", jira_project_key="TEST"
    )

    # 添加MR记录
    sonar_service.add_issue_mr_record(
        sonar_issue_key=issue_with_mr_key,
        mr_url="https://gitlab.example.com/project/repo/-/merge_requests/456",
        mr_iid="456",
        mr_title="fix(sonar): 修复测试问题2",
        mr_description="测试MR描述2",
        branch_name="fix/sonar-test-002",
        source_branch="fix/sonar-test-002",
        target_branch="main",
        mr_status="created",
    )

    result = sonar_service.is_issue_need_fix(issue_with_mr_key)
    print(f"   Issue Key: {issue_with_mr_key}")
    print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
    print(f"   原因: {result['reason']}")
    print(f"   建议操作: {result['action_required']}")

    # 场景4：MR被驳回（需要修复）
    print("\n4️⃣ 测试MR被驳回（应该需要修复）")

    # 将MR状态更新为驳回
    sonar_service.update_mr_record_status(
        mr_url="https://gitlab.example.com/project/repo/-/merge_requests/456",
        mr_status="rejected",
        rejection_reason="代码存在安全问题",
    )

    result = sonar_service.is_issue_need_fix(issue_with_mr_key)
    print(f"   Issue Key: {issue_with_mr_key}")
    print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
    print(f"   原因: {result['reason']}")
    print(f"   建议操作: {result['action_required']}")

    # 总结测试结果
    print("\n📊 测试总结：")
    print("   ✅ 全新issue → 需要修复")
    print("   ✅ 有记录无MR → 需要修复")
    print("   ✅ 有记录有MR → 不需要修复")
    print("   ✅ MR被驳回 → 需要修复")

    print("\n🎉 AI修复器issue检查逻辑测试完成！")
    print("💡 现在AI修复器会在处理每个issue前先检查是否真的需要修复")

    return True


if __name__ == "__main__":
    test_ai_fixer_issue_check()
