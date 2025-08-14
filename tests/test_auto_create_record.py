#!/usr/bin/env python3
"""
测试自动创建初始记录功能
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sonar_tools.service.sonar_service import SonarService
from sonar_tools.utils.project_db import ProjectStatusDB


def test_auto_create_initial_record():
    """测试自动创建初始记录功能"""
    print("🧪 测试自动创建初始记录功能")

    # 创建服务实例
    sonar_service = SonarService()
    project_db = sonar_service.project_db

    # 测试一个全新的issue key
    new_issue_key = f"auto:test:Issue{int(time.time())}"

    print(f"\n1️⃣ 测试全新issue: {new_issue_key}")

    # 首先确认这个issue不存在
    exists_before = project_db.is_task_created(new_issue_key)
    print(f"   创建前是否存在: {'✅ 是' if exists_before else '❌ 否'}")

    # 调用is_issue_need_fix，应该会自动创建记录
    result = sonar_service.is_issue_need_fix(new_issue_key)

    print(f"   检查结果:")
    print(f"     需要修复: {'✅ 是' if result['need_fix'] else '❌ 否'}")
    print(f"     原因: {result['reason']}")
    print(f"     建议操作: {result['action_required']}")

    # 再次检查是否已创建记录
    exists_after = project_db.is_task_created(new_issue_key)
    print(f"   创建后是否存在: {'✅ 是' if exists_after else '❌ 否'}")

    if exists_after and not exists_before:
        print("   ✅ 自动创建初始记录成功")
    else:
        print("   ❌ 自动创建初始记录失败")
        return False

    # 测试再次调用的情况
    print(f"\n2️⃣ 再次检查同一个issue: {new_issue_key}")

    result2 = sonar_service.is_issue_need_fix(new_issue_key)
    print(f"   第二次检查结果:")
    print(f"     需要修复: {'✅ 是' if result2['need_fix'] else '❌ 否'}")
    print(f"     原因: {result2['reason']}")
    print(f"     建议操作: {result2['action_required']}")

    # 应该显示找到记录但没有MR
    if "找到 issue 记录但未找到 mr 记录" in result2["reason"]:
        print("   ✅ 第二次检查逻辑正确")
    else:
        print("   ❌ 第二次检查逻辑错误")
        return False

    # 测试创建MR后的情况
    print(f"\n3️⃣ 为issue添加MR记录")

    mr_success = sonar_service.add_issue_mr_record(
        sonar_issue_key=new_issue_key,
        mr_url=f"https://gitlab.example.com/test/repo/-/merge_requests/{int(time.time())}",
        mr_iid=str(int(time.time())),
        mr_title="测试MR",
        mr_description="自动测试创建的MR",
        branch_name="test-branch",
        source_branch="test-branch",
        target_branch="main",
        mr_status="created",
    )

    if mr_success:
        print("   ✅ MR记录创建成功")
    else:
        print("   ❌ MR记录创建失败")
        return False

    # 再次检查
    result3 = sonar_service.is_issue_need_fix(new_issue_key)
    print(f"   添加MR后检查结果:")
    print(f"     需要修复: {'✅ 是' if result3['need_fix'] else '❌ 否'}")
    print(f"     原因: {result3['reason']}")
    print(f"     建议操作: {result3['action_required']}")

    # 现在应该不需要修复
    if not result3["need_fix"] and "MR状态为: created" in result3["reason"]:
        print("   ✅ 添加MR后逻辑正确")
    else:
        print("   ❌ 添加MR后逻辑错误")
        return False

    print("\n📊 测试总结：")
    print("   ✅ 全新issue自动创建初始记录")
    print("   ✅ 第二次检查显示正确状态")
    print("   ✅ 添加MR后状态更新正确")
    print("   ✅ 完整的生命周期管理")

    print("\n🎉 自动创建初始记录功能测试完成！")
    print("💡 现在系统会自动为新issue创建追踪记录，无需手动处理")

    return True


if __name__ == "__main__":
    test_auto_create_initial_record()
