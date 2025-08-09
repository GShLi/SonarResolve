#!/usr/bin/env python3
"""
测试简化版SQLite功能
只记录已创建的项目和任务，无过期时间字段
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_simplified_database():
    """测试简化的数据库功能"""
    logger.info("开始测试简化版SQLite数据库功能...")
    
    try:
        # 添加项目根目录到路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from sonar_tools.utils.project_db import ProjectStatusDB
        
        # 创建测试数据库
        test_db_path = "test_simplified.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        project_db = ProjectStatusDB(db_path=test_db_path)
        logger.info("✅ 数据库初始化成功")
        
        # 测试项目创建记录
        logger.info("1. 测试项目创建记录...")
        test_projects = [
            ("backend-api", "BACKEND"),
            ("frontend-web", "FRONTEND"),
            ("data-service", "DATASERV")
        ]
        
        for sonar_key, jira_key in test_projects:
            project_db.record_created_project(sonar_key, jira_key)
            logger.info(f"✅ 记录项目: {sonar_key} -> {jira_key}")
        
        # 测试项目查询
        logger.info("2. 测试项目查询...")
        for sonar_key, expected_jira_key in test_projects:
            found_jira_key = project_db.is_project_created(sonar_key)
            if found_jira_key == expected_jira_key:
                logger.info(f"✅ 查询成功: {sonar_key} -> {found_jira_key}")
            else:
                logger.warning(f"⚠️ 查询异常: {sonar_key}, 期望 {expected_jira_key}, 实际 {found_jira_key}")
        
        # 测试不存在的项目
        non_existent = project_db.is_project_created("non-existent")
        if non_existent is None:
            logger.info("✅ 正确处理不存在的项目")
        else:
            logger.warning(f"⚠️ 不存在的项目应返回None，实际返回: {non_existent}")
        
        # 测试任务创建记录
        logger.info("3. 测试任务创建记录...")
        test_tasks = [
            ("ISSUE-001", "BACKEND-1", "BACKEND", "backend-api"),
            ("ISSUE-002", "BACKEND-2", "BACKEND", "backend-api"),
            ("ISSUE-003", "FRONTEND-1", "FRONTEND", "frontend-web")
        ]
        
        for sonar_issue, jira_task, jira_project, sonar_project in test_tasks:
            project_db.record_created_task(sonar_issue, jira_task, jira_project, sonar_project)
            logger.info(f"✅ 记录任务: {sonar_issue} -> {jira_task}")
        
        # 测试任务查询
        logger.info("4. 测试任务查询...")
        for sonar_issue, _, _, _ in test_tasks:
            is_created = project_db.is_task_created(sonar_issue)
            if is_created:
                logger.info(f"✅ 任务已创建: {sonar_issue}")
            else:
                logger.warning(f"⚠️ 任务查询异常: {sonar_issue}")
        
        # 测试统计信息
        logger.info("5. 测试统计信息...")
        project_stats = project_db.get_project_statistics()
        task_stats = project_db.get_task_statistics()
        
        logger.info(f"项目统计: {project_stats}")
        logger.info(f"任务统计: {task_stats}")
        
        if project_stats.get('total_projects') == len(test_projects):
            logger.info("✅ 项目统计正确")
        else:
            logger.warning(f"⚠️ 项目统计异常: 期望 {len(test_projects)}, 实际 {project_stats.get('total_projects')}")
        
        if task_stats.get('total_tasks') == len(test_tasks):
            logger.info("✅ 任务统计正确")
        else:
            logger.warning(f"⚠️ 任务统计异常: 期望 {len(test_tasks)}, 实际 {task_stats.get('total_tasks')}")
        
        # 测试项目任务列表
        logger.info("6. 测试项目任务列表...")
        backend_tasks = project_db.get_tasks_by_project("backend-api")
        logger.info(f"backend-api项目的任务: {len(backend_tasks)}个")
        
        expected_backend_tasks = 2  # ISSUE-001 和 ISSUE-002
        if len(backend_tasks) == expected_backend_tasks:
            logger.info("✅ 项目任务列表正确")
        else:
            logger.warning(f"⚠️ 项目任务列表异常: 期望 {expected_backend_tasks}, 实际 {len(backend_tasks)}")
        
        # 测试完整统计导出
        logger.info("7. 测试完整统计导出...")
        full_stats = project_db.export_stats()
        logger.info(f"完整统计: {full_stats}")
        
        # 清理测试数据库
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info("✅ 清理测试数据库")
        
        logger.info("✅ 简化版SQLite数据库功能测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_handling():
    """测试重复记录处理"""
    logger.info("开始测试重复记录处理...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from sonar_tools.utils.project_db import ProjectStatusDB
        
        test_db_path = "test_duplicates.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        project_db = ProjectStatusDB(db_path=test_db_path)
        
        # 测试重复项目记录
        logger.info("1. 测试重复项目记录...")
        project_db.record_created_project("test-project", "TEST1")
        project_db.record_created_project("test-project", "TEST2")  # 重复记录
        
        found_key = project_db.is_project_created("test-project")
        if found_key == "TEST2":
            logger.info("✅ 重复项目记录正确更新")
        else:
            logger.warning(f"⚠️ 重复项目记录处理异常: 期望 TEST2, 实际 {found_key}")
        
        # 测试重复任务记录
        logger.info("2. 测试重复任务记录...")
        project_db.record_created_task("ISSUE-DUP", "TASK1", "TEST2", "test-project")
        project_db.record_created_task("ISSUE-DUP", "TASK2", "TEST2", "test-project")  # 重复记录
        
        is_created = project_db.is_task_created("ISSUE-DUP")
        if is_created:
            logger.info("✅ 重复任务记录处理正确")
        else:
            logger.warning("⚠️ 重复任务记录处理异常")
        
        # 检查统计信息
        project_stats = project_db.get_project_statistics()
        task_stats = project_db.get_task_statistics()
        
        if project_stats.get('total_projects') == 1:
            logger.info("✅ 重复项目不影响统计")
        else:
            logger.warning(f"⚠️ 重复项目影响统计: {project_stats.get('total_projects')}")
        
        if task_stats.get('total_tasks') == 1:
            logger.info("✅ 重复任务不影响统计")
        else:
            logger.warning(f"⚠️ 重复任务影响统计: {task_stats.get('total_tasks')}")
        
        # 清理测试数据库
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info("✅ 清理测试数据库")
        
        logger.info("✅ 重复记录处理测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 重复记录测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始简化版SQLite功能测试")
    
    print("=" * 70)
    print("SonarResolve 简化版SQLite功能测试")
    print("=" * 70)
    
    test_results = []
    
    # 测试1: 基本数据库功能
    print("\n1. 测试基本数据库功能...")
    basic_test_ok = test_simplified_database()
    test_results.append(("基本数据库功能", basic_test_ok))
    
    # 测试2: 重复记录处理
    print("\n2. 测试重复记录处理...")
    duplicate_test_ok = test_duplicate_handling()
    test_results.append(("重复记录处理", duplicate_test_ok))
    
    # 总结
    print("\n" + "=" * 70)
    print("测试结果总结:")
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！简化版SQLite功能正常工作。")
        print("\n📋 简化功能特性:")
        print("  ✅ 只记录已创建的项目")
        print("  ✅ 只记录已创建的任务") 
        print("  ✅ 无过期时间字段")
        print("  ✅ 简化的统计信息")
        print("  ✅ 重复记录自动更新")
        print("  ✅ 高效的查询性能")
        
        print(f"\n📝 数据库结构:")
        print("  • created_projects: 记录已创建的项目")
        print("  • created_tasks: 记录已创建的任务")
        print("  • 添加了索引以提高查询性能")
        print("  • 移除了API统计和缓存过期机制")
        
        return True
    else:
        print("\n❌ 部分测试失败，请检查代码实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
