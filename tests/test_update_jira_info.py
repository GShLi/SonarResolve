#!/usr/bin/env python3
"""
测试更新Jira信息功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sonar_tools.core.models import SonarIssue
from sonar_tools.service.sonar_service import SonarService
from sonar_tools.utils.project_db import ProjectStatusDB


def test_update_jira_info():
    """测试更新Jira信息功能"""

    # 使用临时数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # 创建数据库和服务
        project_db = ProjectStatusDB(db_path)
        sonar_service = SonarService(project_db)

        # 创建测试用的SonarQube问题
        test_issue = SonarIssue(
            key="TEST-ISSUE-001",
            rule="java:S1234",
            severity="MAJOR",
            component="src/main/java/Test.java",
            project="test-project",
            line=10,
            message="Test issue message",
            author="test@example.com",
            creation_date="2023-08-01T10:00:00Z",
            update_date="2023-08-01T10:00:00Z",
            status="OPEN",
            resolution=None,
            effort="5min",
            debt="5min",
            tags=["bug"],
        )

        print("=== 测试更新Jira信息功能 ===")

        # 步骤1：先创建一个初始记录（模拟is_issue_need_fix中的自动创建）
        print("\n1. 创建初始记录（Jira信息为空）")
        project_db.record_created_task(
            sonar_issue_key=test_issue.key,
            jira_task_key=None,
            jira_project_key=None,
            sonar_project_key=test_issue.project,
        )

        # 验证记录已创建但Jira信息为空
        initial_info = project_db.get_task_basic_info(test_issue.key)
        print(f"初始记录: {initial_info}")
        assert initial_info is not None
        assert initial_info["jira_task_key"] is None
        assert initial_info["jira_project_key"] is None

        # 验证is_task_created返回False（因为Jira信息为空）
        is_created = project_db.is_task_created(test_issue.key)
        print(f"is_task_created 结果: {is_created}")
        assert not is_created, "应该返回False，因为Jira信息为空"

        # 步骤2：调用create_sonar_issue_record填充Jira信息
        print("\n2. 调用create_sonar_issue_record填充Jira信息")
        success = sonar_service.create_sonar_issue_record(
            sonar_issue=test_issue,
            jira_task_key="JIRA-123",
            jira_project_key="TESTPROJ",
        )

        print(f"填充Jira信息结果: {success}")
        assert success, "应该成功填充Jira信息"

        # 验证记录已更新
        updated_info = project_db.get_task_basic_info(test_issue.key)
        print(f"更新后记录: {updated_info}")
        assert updated_info["jira_task_key"] == "JIRA-123"
        assert updated_info["jira_project_key"] == "TESTPROJ"

        # 验证is_task_created现在返回True
        is_created_after = project_db.is_task_created(test_issue.key)
        print(f"更新后 is_task_created 结果: {is_created_after}")
        assert is_created_after, "现在应该返回True，因为Jira信息已填充"

        # 步骤3：再次调用create_sonar_issue_record，应该直接返回成功
        print("\n3. 再次调用create_sonar_issue_record（应该直接返回成功）")
        success2 = sonar_service.create_sonar_issue_record(
            sonar_issue=test_issue,
            jira_task_key="JIRA-456",  # 不同的值，但不应该更新
            jira_project_key="TESTPROJ2",
        )

        print(f"第二次调用结果: {success2}")
        assert success2, "应该成功返回"

        # 验证记录没有被覆盖
        final_info = project_db.get_task_basic_info(test_issue.key)
        print(f"最终记录: {final_info}")
        assert final_info["jira_task_key"] == "JIRA-123", "原有的Jira信息不应该被覆盖"
        assert final_info["jira_project_key"] == "TESTPROJ"

        # 步骤4：测试全新记录的创建
        print("\n4. 测试全新记录的创建")
        new_issue = SonarIssue(
            key="TEST-ISSUE-002",
            rule="java:S5678",
            severity="MINOR",
            component="src/main/java/Test2.java",
            project="test-project",
            line=20,
            message="Another test issue",
            author="test2@example.com",
            creation_date="2023-08-01T11:00:00Z",
            update_date="2023-08-01T11:00:00Z",
            status="OPEN",
            resolution=None,
            effort="3min",
            debt="3min",
            tags=["code-smell"],
        )

        success3 = sonar_service.create_sonar_issue_record(
            sonar_issue=new_issue, jira_task_key="JIRA-789", jira_project_key="TESTPROJ"
        )

        print(f"新记录创建结果: {success3}")
        assert success3, "应该成功创建新记录"

        # 验证新记录
        new_info = project_db.get_task_basic_info(new_issue.key)
        print(f"新记录信息: {new_info}")
        assert new_info["jira_task_key"] == "JIRA-789"
        assert new_info["jira_project_key"] == "TESTPROJ"

        # 验证is_task_created返回True
        is_created_new = project_db.is_task_created(new_issue.key)
        print(f"新记录 is_task_created 结果: {is_created_new}")
        assert is_created_new, "新记录应该立即返回True"

        print("\n✅ 所有测试通过！")

        # 打印统计信息
        print("\n=== 数据库状态 ===")
        db_info = project_db.get_database_info()
        print(f"数据库路径: {db_info['database_path']}")
        print(f"数据库大小: {db_info['database_size']} bytes")

        task_stats = project_db.get_task_statistics()
        print(f"总任务数: {task_stats.get('total_tasks', 0)}")

    finally:
        # 清理临时文件
        try:
            os.unlink(db_path)
        except:
            pass


if __name__ == "__main__":
    test_update_jira_info()
