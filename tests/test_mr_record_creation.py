#!/usr/bin/env python3
"""
测试MR记录创建功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sonar_tools.service.sonar_service import SonarService
from sonar_tools.utils.project_db import ProjectStatusDB
from sonar_tools.core.models import SonarIssue


def test_mr_record_creation():
    """测试MR记录创建功能"""
    print("🧪 测试MR记录创建功能")

    # 创建服务实例
    sonar_service = SonarService()

    # 创建测试问题记录
    test_issue_key = "test:project:TestIssue001"
    test_jira_key = "TEST-001"
    test_project_key = "TEST"
    test_sonar_project = "test:project"

    print(f"1️⃣ 创建测试issue记录: {test_issue_key}")

    # 创建测试SonarIssue对象
    test_issue = SonarIssue(
        key=test_issue_key,
        rule="test:rule",
        message="测试问题",
        component=f"{test_sonar_project}:src/test.py",
        project=test_sonar_project,
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

    # 创建问题记录
    success = sonar_service.create_sonar_issue_record(
        sonar_issue=test_issue,
        jira_task_key=test_jira_key,
        jira_project_key=test_project_key,
    )

    if success:
        print("   ✅ 问题记录创建成功")
    else:
        print("   ❌ 问题记录创建失败")
        return False

    print(f"2️⃣ 测试添加MR记录: {test_issue_key}")

    # 添加MR记录
    mr_success = sonar_service.add_issue_mr_record(
        sonar_issue_key=test_issue_key,
        mr_url="https://gitlab.example.com/project/repo/-/merge_requests/123",
        mr_iid="123",
        mr_title="fix(sonar): 修复测试问题",
        mr_description="测试MR描述",
        branch_name="fix/sonar-test-001",
        source_branch="fix/sonar-test-001",
        target_branch="main",
        mr_status="created",
    )

    if mr_success:
        print("   ✅ MR记录创建成功")
    else:
        print("   ❌ MR记录创建失败")
        return False

    print(f"3️⃣ 验证is_issue_need_fix逻辑")

    # 测试逻辑
    result = sonar_service.is_issue_need_fix(test_issue_key)
    print(f"   需要修复: {'✅ 否' if not result['need_fix'] else '❌ 是'}")
    print(f"   原因: {result['reason']}")
    print(f"   建议操作: {result['action_required']}")

    # 测试MR被驳回的情况
    print(f"4️⃣ 测试MR驳回场景")

    # 更新MR状态为驳回
    reject_success = sonar_service.update_mr_record_status(
        mr_url="https://gitlab.example.com/project/repo/-/merge_requests/123",
        mr_status="rejected",
        rejection_reason="代码质量不符合要求",
    )

    if reject_success:
        print("   ✅ MR状态更新为驳回成功")

        # 再次检查是否需要修复
        result_after_reject = sonar_service.is_issue_need_fix(test_issue_key)
        print(
            f"   驳回后需要修复: {'✅ 是' if result_after_reject['need_fix'] else '❌ 否'}"
        )
        print(f"   原因: {result_after_reject['reason']}")
        print(f"   建议操作: {result_after_reject['action_required']}")

        if result_after_reject["need_fix"] and "驳回" in result_after_reject["reason"]:
            print("   ✅ 驳回逻辑正确")
        else:
            print("   ❌ 驳回逻辑错误")
            return False
    else:
        print("   ❌ MR状态更新失败")
        return False

    print("\n🎉 所有测试通过！MR记录创建功能正常工作")
    return True


if __name__ == "__main__":
    test_mr_record_creation()
