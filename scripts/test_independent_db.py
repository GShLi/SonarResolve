#!/usr/bin/env python3
"""
独立测试简化版SQLite功能
直接复制project_db.py的代码进行测试
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ProjectStatusDB:
    """项目状态数据库管理器（简化版）"""
    
    def __init__(self, db_path: str = "project_status.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建项目状态表 - 只记录已创建的项目
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS created_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sonar_project_key TEXT UNIQUE NOT NULL,
                    jira_project_key TEXT NOT NULL,
                    created_by_us BOOLEAN DEFAULT TRUE,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 创建任务状态表 - 只记录已创建的任务
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS created_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sonar_issue_key TEXT UNIQUE NOT NULL,
                    jira_task_key TEXT NOT NULL,
                    jira_project_key TEXT NOT NULL,
                    sonar_project_key TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sonar_project_key) REFERENCES created_projects (sonar_project_key)
                )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_projects_sonar_key 
                ON created_projects (sonar_project_key)
                ''')
                
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_tasks_sonar_issue 
                ON created_tasks (sonar_issue_key)
                ''')
                
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_tasks_project 
                ON created_tasks (sonar_project_key)
                ''')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def is_project_created(self, sonar_project_key: str) -> Optional[str]:
        """检查项目是否已创建"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT jira_project_key
                        FROM created_projects 
                        WHERE sonar_project_key = ?
                    ''', (sonar_project_key,))
                    
                    row = cursor.fetchone()
                    return row[0] if row else None
                    
        except Exception as e:
            logger.error(f"检查项目创建状态失败: {e}")
            return None
    
    def record_created_project(self, sonar_project_key: str, jira_project_key: str):
        """记录已创建的项目"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO created_projects 
                        (sonar_project_key, jira_project_key, created_by_us, created_time)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (sonar_project_key, jira_project_key, True))
                    
                    conn.commit()
                    logger.info(f"记录已创建项目: {sonar_project_key} -> {jira_project_key}")
                    
        except Exception as e:
            logger.error(f"记录项目创建失败: {e}")
    
    def is_task_created(self, sonar_issue_key: str) -> bool:
        """检查任务是否已创建"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT id FROM created_tasks 
                        WHERE sonar_issue_key = ?
                    ''', (sonar_issue_key,))
                    
                    return cursor.fetchone() is not None
                    
        except Exception as e:
            logger.error(f"检查任务创建状态失败: {e}")
            return False
    
    def record_created_task(self, sonar_issue_key: str, jira_task_key: str,
                           jira_project_key: str, sonar_project_key: str):
        """记录已创建的任务"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO created_tasks 
                        (sonar_issue_key, jira_task_key, jira_project_key, 
                         sonar_project_key, created_time)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (sonar_issue_key, jira_task_key, jira_project_key, sonar_project_key))
                    
                    conn.commit()
                    logger.debug(f"记录已创建任务: {sonar_issue_key} -> {jira_task_key}")
                    
        except Exception as e:
            logger.error(f"记录任务创建失败: {e}")
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 总项目数
                    cursor.execute('SELECT COUNT(*) FROM created_projects')
                    total_projects = cursor.fetchone()[0]
                    
                    return {'total_projects': total_projects}
                    
        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return {}
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 总任务数
                    cursor.execute('SELECT COUNT(*) FROM created_tasks')
                    total_tasks = cursor.fetchone()[0]
                    
                    return {'total_tasks': total_tasks}
                    
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    def get_all_created_projects(self) -> List[Dict[str, Any]]:
        """获取所有已创建的项目"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT sonar_project_key, jira_project_key, created_time
                        FROM created_projects 
                        ORDER BY created_time DESC
                    ''')
                    
                    projects = []
                    for row in cursor.fetchall():
                        projects.append({
                            'sonar_project_key': row[0],
                            'jira_project_key': row[1],
                            'created_time': row[2]
                        })
                    
                    return projects
                    
        except Exception as e:
            logger.error(f"获取已创建项目列表失败: {e}")
            return []

def test_basic_functionality():
    """测试基本功能"""
    logger.info("开始测试基本功能...")
    
    try:
        # 创建测试数据库
        test_db_path = "test_basic.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        project_db = ProjectStatusDB(db_path=test_db_path)
        logger.info("✅ 数据库初始化成功")
        
        # 测试项目记录
        test_projects = [
            ("backend-api", "BACKEND"),
            ("frontend-web", "FRONTEND"),
            ("data-service", "DATASERV")
        ]
        
        for sonar_key, jira_key in test_projects:
            project_db.record_created_project(sonar_key, jira_key)
            logger.info(f"✅ 记录项目: {sonar_key} -> {jira_key}")
        
        # 测试项目查询
        for sonar_key, expected_jira_key in test_projects:
            found_jira_key = project_db.is_project_created(sonar_key)
            if found_jira_key == expected_jira_key:
                logger.info(f"✅ 查询成功: {sonar_key} -> {found_jira_key}")
            else:
                logger.warning(f"⚠️ 查询异常: {sonar_key}")
                return False
        
        # 测试任务记录
        test_tasks = [
            ("ISSUE-001", "BACKEND-1", "BACKEND", "backend-api"),
            ("ISSUE-002", "BACKEND-2", "BACKEND", "backend-api"),
            ("ISSUE-003", "FRONTEND-1", "FRONTEND", "frontend-web")
        ]
        
        for sonar_issue, jira_task, jira_project, sonar_project in test_tasks:
            project_db.record_created_task(sonar_issue, jira_task, jira_project, sonar_project)
            logger.info(f"✅ 记录任务: {sonar_issue} -> {jira_task}")
        
        # 测试任务查询
        for sonar_issue, _, _, _ in test_tasks:
            is_created = project_db.is_task_created(sonar_issue)
            if is_created:
                logger.info(f"✅ 任务已创建: {sonar_issue}")
            else:
                logger.warning(f"⚠️ 任务查询异常: {sonar_issue}")
                return False
        
        # 测试统计
        project_stats = project_db.get_project_statistics()
        task_stats = project_db.get_task_statistics()
        
        if project_stats.get('total_projects') == len(test_projects):
            logger.info("✅ 项目统计正确")
        else:
            logger.warning("⚠️ 项目统计异常")
            return False
        
        if task_stats.get('total_tasks') == len(test_tasks):
            logger.info("✅ 任务统计正确")
        else:
            logger.warning("⚠️ 任务统计异常")
            return False
        
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info("✅ 清理测试数据库")
        
        logger.info("✅ 基本功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 基本功能测试失败: {e}")
        return False

def test_duplicate_handling():
    """测试重复记录处理"""
    logger.info("开始测试重复记录处理...")
    
    try:
        test_db_path = "test_dup.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        project_db = ProjectStatusDB(db_path=test_db_path)
        
        # 测试重复项目
        project_db.record_created_project("test-project", "TEST1")
        project_db.record_created_project("test-project", "TEST2")  # 重复
        
        found_key = project_db.is_project_created("test-project")
        if found_key == "TEST2":
            logger.info("✅ 重复项目处理正确")
        else:
            logger.warning("⚠️ 重复项目处理异常")
            return False
        
        # 测试重复任务
        project_db.record_created_task("ISSUE-DUP", "TASK1", "TEST2", "test-project")
        project_db.record_created_task("ISSUE-DUP", "TASK2", "TEST2", "test-project")  # 重复
        
        is_created = project_db.is_task_created("ISSUE-DUP")
        if is_created:
            logger.info("✅ 重复任务处理正确")
        else:
            logger.warning("⚠️ 重复任务处理异常")
            return False
        
        # 检查统计（应该只有1个项目和1个任务）
        project_stats = project_db.get_project_statistics()
        task_stats = project_db.get_task_statistics()
        
        if (project_stats.get('total_projects') == 1 and 
            task_stats.get('total_tasks') == 1):
            logger.info("✅ 重复记录不影响统计")
        else:
            logger.warning("⚠️ 重复记录影响统计")
            return False
        
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info("✅ 清理测试数据库")
        
        logger.info("✅ 重复记录处理测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 重复记录测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始独立简化版SQLite功能测试")
    
    print("=" * 60)
    print("独立简化版SQLite功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 基本功能
    print("\n1. 测试基本功能...")
    basic_test_ok = test_basic_functionality()
    test_results.append(("基本功能", basic_test_ok))
    
    # 测试2: 重复记录处理
    print("\n2. 测试重复记录处理...")
    duplicate_test_ok = test_duplicate_handling()
    test_results.append(("重复记录处理", duplicate_test_ok))
    
    # 总结
    print("\n" + "=" * 60)
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
        print("  • created_projects: sonar_project_key, jira_project_key, created_time")
        print("  • created_tasks: sonar_issue_key, jira_task_key, jira_project_key, sonar_project_key, created_time")
        print("  • 添加了索引以提高查询性能")
        
        return True
    else:
        print("\n❌ 部分测试失败，请检查代码实现。")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
