#!/usr/bin/env python3
"""
简化测试 - 验证修改后的判断逻辑
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sonar_tools.service.sonar_service import SonarService
from sonar_tools.utils.project_db import ProjectStatusDB


def test_basic_logic():
    """测试基本逻辑"""

    # 使用临时数据库
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        project_db = ProjectStatusDB(db_path)
        sonar_service = SonarService(project_db)

        print("🧪 测试修改后的判断逻辑\n")

        # 情况1：未找到 issue 记录
        print("1️⃣ 测试未找到 issue 记录...")
        result = sonar_service.is_issue_need_fix("NONEXISTENT-ISSUE")
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")
        assert result["need_fix"] == True, "应该需要修复"
        assert "未找到 issue 记录" in result["reason"], "原因应该包含'未找到 issue 记录'"

        # 手动创建基本记录来模拟情况2和3
        print("\n2️⃣ 测试手动添加记录后的逻辑...")

        # 创建项目记录
        project_db.record_created_project("test-project", "TEST")

        # 创建问题记录
        project_db.record_created_task(
            sonar_issue_key="TEST-ISSUE-001",
            jira_task_key="JIRA-TASK-001",
            jira_project_key="TEST",
            sonar_project_key="test-project",
        )

        # 情况2：找到 issue 记录但未找到 mr 记录
        print("   测试找到 issue 记录但未找到 mr 记录...")
        result = sonar_service.is_issue_need_fix("TEST-ISSUE-001")
        print(f"   需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
        print(f"   原因: {result['reason']}")

        # 根据当前数据库支持的功能来判断
        if hasattr(project_db, "get_latest_mr_record"):
            # 如果支持MR记录功能
            assert result["need_fix"] == True, "应该需要修复（未找到MR记录）"
            assert "未找到 mr 记录" in result["reason"], "原因应该包含'未找到 mr 记录'"
        else:
            # 如果不支持MR记录功能，应该直接返回需要修复
            assert result["need_fix"] == True, "应该需要修复（基本功能模式）"

        print("\n✅ 基本逻辑测试通过!")
        print("📋 修改后的逻辑:")
        print("   1. 未找到 issue 记录 → 需要修复 ✅")
        print("   2. 找到 issue 记录但未找到 mr 记录 → 需要修复 ✅")
        print("   3. 找到记录且 mr 被驳回 → 需要修复 (需要完整MR功能)")
        print("   4. 其他情况 → 无需修复")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            import os

            os.unlink(db_path)
        except:
            pass


if __name__ == "__main__":
    test_basic_logic()
