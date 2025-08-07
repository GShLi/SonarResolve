#!/usr/bin/env python3
"""
项目状态数据库管理
用于本地缓存Jira项目创建状态，减少API调用次数
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class ProjectStatusDB:
    """项目状态数据库管理器"""
    
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
        """
        检查项目是否已创建
        
        Args:
            sonar_project_key: SonarQube项目Key
            
        Returns:
            如果项目已创建返回Jira项目Key，否则返回None
        """
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
        """
        记录已创建的项目
        
        Args:
            sonar_project_key: SonarQube项目Key
            jira_project_key: Jira项目Key
        """
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
        """
        检查任务是否已创建
        
        Args:
            sonar_issue_key: SonarQube问题Key
            
        Returns:
            True表示任务已创建，False表示未创建
        """
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
        """
        记录已创建的任务
        
        Args:
            sonar_issue_key: SonarQube问题Key
            jira_task_key: Jira任务Key
            jira_project_key: Jira项目Key
            sonar_project_key: SonarQube项目Key
        """
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
        """
        获取项目统计信息
        
        Returns:
            项目统计信息
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 总项目数
                    cursor.execute('SELECT COUNT(*) FROM created_projects')
                    total_projects = cursor.fetchone()[0]
                    
                    # 按时间统计
                    cursor.execute('''
                        SELECT DATE(created_time) as date, COUNT(*) as count
                        FROM created_projects 
                        GROUP BY DATE(created_time)
                        ORDER BY date DESC
                        LIMIT 7
                    ''')
                    
                    daily_stats = []
                    for row in cursor.fetchall():
                        daily_stats.append({'date': row[0], 'count': row[1]})
                    
                    return {
                        'total_projects': total_projects,
                        'daily_creation_stats': daily_stats
                    }
                    
        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return {}
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            任务统计信息
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 总任务数
                    cursor.execute('SELECT COUNT(*) FROM created_tasks')
                    total_tasks = cursor.fetchone()[0]
                    
                    # 按项目统计
                    cursor.execute('''
                        SELECT sonar_project_key, COUNT(*) as task_count
                        FROM created_tasks 
                        GROUP BY sonar_project_key
                        ORDER BY task_count DESC
                        LIMIT 10
                    ''')
                    
                    project_task_stats = []
                    for row in cursor.fetchall():
                        project_task_stats.append({'project': row[0], 'task_count': row[1]})
                    
                    return {
                        'total_tasks': total_tasks,
                        'tasks_by_project': project_task_stats
                    }
                    
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 365):
        """
        清理旧记录（保留1年）
        
        Args:
            days: 保留天数
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cutoff_time = datetime.now() - timedelta(days=days)
                    
                    # 清理旧的任务记录
                    cursor.execute('''
                        DELETE FROM created_tasks 
                        WHERE created_time < ?
                    ''', (cutoff_time.isoformat(),))
                    
                    deleted_tasks = cursor.rowcount
                    
                    # 清理旧的项目记录
                    cursor.execute('''
                        DELETE FROM created_projects 
                        WHERE created_time < ?
                    ''', (cutoff_time.isoformat(),))
                    
                    deleted_projects = cursor.rowcount
                    
                    conn.commit()
                    
                    if deleted_projects > 0 or deleted_tasks > 0:
                        logger.info(f"清理完成: 删除 {deleted_projects} 个项目记录, {deleted_tasks} 个任务记录")
                    
        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
    
    def get_all_created_projects(self) -> List[Dict[str, Any]]:
        """
        获取所有已创建的项目
        
        Returns:
            已创建项目列表
        """
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
    
    def get_tasks_by_project(self, sonar_project_key: str) -> List[Dict[str, Any]]:
        """
        获取指定项目的所有已创建任务
        
        Args:
            sonar_project_key: SonarQube项目Key
            
        Returns:
            任务列表
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT sonar_issue_key, jira_task_key, created_time
                        FROM created_tasks 
                        WHERE sonar_project_key = ?
                        ORDER BY created_time DESC
                    ''', (sonar_project_key,))
                    
                    tasks = []
                    for row in cursor.fetchall():
                        tasks.append({
                            'sonar_issue_key': row[0],
                            'jira_task_key': row[1],
                            'created_time': row[2]
                        })
                    
                    return tasks
                    
        except Exception as e:
            logger.error(f"获取项目任务列表失败: {e}")
            return []
    
    def export_stats(self) -> Dict[str, Any]:
        """导出完整统计信息"""
        try:
            project_stats = self.get_project_statistics()
            task_stats = self.get_task_statistics()
            
            return {
                'database_stats': {
                    'total_projects': project_stats.get('total_projects', 0),
                    'total_tasks': task_stats.get('total_tasks', 0),
                    'daily_project_creation': project_stats.get('daily_creation_stats', []),
                    'tasks_by_project': task_stats.get('tasks_by_project', [])
                },
                'summary': {
                    'database_file': str(self.db_path),
                    'created_at': datetime.now().isoformat()
                }
            }
                    
        except Exception as e:
            logger.error(f"导出统计信息失败: {e}")
            return {}
