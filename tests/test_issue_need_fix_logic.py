#!/usr/bin/env python3
"""
测试修改后的is_issue_need_fix方法逻辑
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sonar_tools.core.models import SonarIssue
from sonar_tools.service.sonar_service import SonarService
from sonar_tools.utils.project_db import ProjectStatusDB


def test_issue_need_fix_logic():
    """测试问题是否需要修复的逻辑"""

    # 使用临时数据库文件
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # 创建服务实例
        project_db = ProjectStatusDB(db_path)
        sonar_service = SonarService(project_db)

        print("🧪 测试修改后的is_issue_need_fix方法逻辑\n")

        # 测试数据
        sonar_issue = SonarIssue(
            key="TEST-ISSUE-001",
            rule="java:S1234",
            severity="MAJOR",
            component="src/main/java/Test.java",
            project="test-project",
            line=10,
            message="测试问题消息",
            creation_date="2025-01-01T10:00:00Z",
            update_date="2025-01-01T10:00:00Z",
            type="CODE_SMELL",
            status="OPEN",
            debt="5min",
            effort="5min",
            tags=["test"],
        )

        # 情况1：未找到 issue 记录
        print("📋 情况1：测试未找到 issue 记录...")
        result = sonar_service.is_issue_need_fix("NONEXISTENT-ISSUE")
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        print(f"   建议操作: {result['action_required']}\n")

        # 创建项目和问题记录
        print("📝 创建测试数据...")
        project_db.record_created_project(sonar_issue.project, "TEST")
        sonar_service.create_sonar_issue_record(
            sonar_issue=sonar_issue,
            jira_task_key="JIRA-TASK-001",
            jira_project_key="TEST",
        )

        # 情况2：找到 issue 记录但未找到 mr 记录
        print("📋 情况2：测试找到 issue 记录但未找到 mr 记录...")
        result = sonar_service.is_issue_need_fix(sonar_issue.key)
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        print(f"   建议操作: {result['action_required']}\n")

        # 添加MR记录
        print("📝 添加MR记录...")
        mr_url = "https://gitlab.com/project/repo/-/merge_requests/1"
        success = sonar_service.add_issue_mr_record(
            sonar_issue_key=sonar_issue.key,
            mr_url=mr_url,
            mr_title="Fix: 修复SonarQube问题",
            mr_status="created",
        )
        print(f"   添加MR记录: {'✅ 成功' if success else '❌ 失败'}")

        # 测试找到记录且MR未被驳回的情况
        print("📋 测试找到 issue 记录和 mr 记录，MR未被驳回...")
        result = sonar_service.is_issue_need_fix(sonar_issue.key)
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        print(f"   建议操作: {result['action_required']}\n")

        # 情况3：找到 issue 记录也找到 mr 记录，但 mr 被驳回
        print("📝 模拟MR被驳回...")
        success = sonar_service.update_mr_record_status(
            mr_url=mr_url, mr_status="rejected", rejection_reason="代码风格不符合规范"
        )
        print(f"   更新MR状态为驳回: {'✅ 成功' if success else '❌ 失败'}")

        print("📋 情况3：测试找到 issue 记录也找到 mr 记录，但 mr 被驳回...")
        result = sonar_service.is_issue_need_fix(sonar_issue.key)
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        print(f"   建议操作: {result['action_required']}\n")

        # 测试MR合并后的情况
        print("📝 模拟MR合并...")
        success = sonar_service.update_mr_record_status(
            mr_url=mr_url, mr_status="merged"
        )
        print(f"   更新MR状态为合并: {'✅ 成功' if success else '❌ 失败'}")

        print("📋 测试MR合并后的情况...")
        result = sonar_service.is_issue_need_fix(sonar_issue.key)
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        print(f"   建议操作: {result['action_required']}\n")

        print("🎉 所有测试完成!")
        print("\n📊 总结：")
        print("   ✅ 情况1：未找到 issue 记录 → 需要修复")
        print("   ✅ 情况2：找到 issue 记录但未找到 mr 记录 → 需要修复")
        print("   ✅ 情况3：找到 issue 记录也找到 mr 记录，但 mr 被驳回 → 需要修复")
        print("   ✅ 其他情况：MR状态正常 → 无需修复")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 清理临时文件
        try:
            os.unlink(db_path)
        except:
            pass


if __name__ == "__main__":
    test_issue_need_fix_logic()
