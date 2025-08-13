#!/usr/bin/env python3
"""
项目状态数据库管理
用于本地缓存Jira项目创建状态，减少API调用次数
"""

import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProjectStatusDB:
    """项目状态数据库管理器"""

    def __init__(self, db_path: str = None):
        # 如果没有指定路径，使用配置中的默认路径
        if db_path is None:
            try:
                from ..core.config import Config

                db_path = Config.DATABASE_PATH
            except ImportError:
                # 如果无法导入配置，使用默认路径
                project_root = Path(__file__).parent.parent.parent.parent
                db_path = project_root / "db" / "project_status.db"

        self.db_path = Path(db_path)

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 创建项目状态表 - 只记录已创建的项目
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS created_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sonar_project_key TEXT UNIQUE NOT NULL,
                    jira_project_key TEXT NOT NULL,
                    created_by_us BOOLEAN DEFAULT TRUE,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                )

                # 创建SonarQube问题跟踪表 - 记录问题处理状态
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS sonar_issue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sonar_issue_key TEXT UNIQUE NOT NULL,
                    jira_task_key TEXT NOT NULL,
                    jira_project_key TEXT NOT NULL,
                    sonar_project_key TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sonar_project_key) REFERENCES created_projects (sonar_project_key)
                )
                """
                )

                # 创建MR提交记录表 - 记录每次MR提交的详细信息
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS mr_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sonar_issue_key TEXT NOT NULL,
                    mr_url TEXT NOT NULL,
                    mr_iid TEXT,
                    mr_title TEXT,
                    mr_description TEXT,
                    branch_name TEXT,
                    source_branch TEXT,
                    target_branch TEXT,
                    mr_status TEXT DEFAULT 'created',
                    rejection_reason TEXT,
                    submitted_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_latest BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (sonar_issue_key) REFERENCES sonar_issue (sonar_issue_key)
                )
                """
                )

                # 创建索引以提高查询性能
                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_created_projects_sonar_key 
                ON created_projects (sonar_project_key)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_sonar_issue_sonar_key 
                ON sonar_issue (sonar_issue_key)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_sonar_issue_project 
                ON sonar_issue (sonar_project_key)
                """
                )

                # 创建MR记录表的索引
                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_mr_records_sonar_issue 
                ON mr_records (sonar_issue_key)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_mr_records_status 
                ON mr_records (mr_status)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_mr_records_latest 
                ON mr_records (is_latest)
                """
                )

                conn.commit()
                logger.info(f"数据库初始化完成: {self.db_path}")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库基本信息

        Returns:
            数据库信息字典
        """
        try:
            db_info = {
                "database_path": str(self.db_path.absolute()),
                "database_exists": self.db_path.exists(),
                "database_size": 0,
                "database_directory": str(self.db_path.parent.absolute()),
                "directory_exists": self.db_path.parent.exists(),
            }

            if self.db_path.exists():
                db_info["database_size"] = self.db_path.stat().st_size

            return db_info

        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {}

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

                    cursor.execute(
                        """
                        SELECT jira_project_key
                        FROM created_projects 
                        WHERE sonar_project_key = ?
                    """,
                        (sonar_project_key,),
                    )

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

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO created_projects 
                        (sonar_project_key, jira_project_key, created_by_us, created_time)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                        (sonar_project_key, jira_project_key, True),
                    )

                    conn.commit()
                    logger.info(
                        f"记录已创建项目: {sonar_project_key} -> {jira_project_key}"
                    )

        except Exception as e:
            logger.error(f"记录项目创建失败: {e}")

    def is_task_created(self, sonar_issue_key: str) -> bool:
        """
        检查SonarQube问题是否已创建

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            True表示问题已创建，False表示未创建
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT id FROM sonar_issue 
                        WHERE sonar_issue_key = ?
                    """,
                        (sonar_issue_key,),
                    )

                    return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"检查问题创建状态失败: {e}")
            return False

    def record_created_task(
        self,
        sonar_issue_key: str,
        jira_task_key: str,
        jira_project_key: str,
        sonar_project_key: str,
    ):
        """
        记录已创建的SonarQube问题

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

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO sonar_issue 
                        (sonar_issue_key, jira_task_key, jira_project_key, 
                         sonar_project_key, created_time, updated_time)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                        (
                            sonar_issue_key,
                            jira_task_key,
                            jira_project_key,
                            sonar_project_key,
                        ),
                    )

                    conn.commit()
                    logger.debug(
                        f"记录已创建问题: {sonar_issue_key} -> {jira_task_key}"
                    )

        except Exception as e:
            logger.error(f"记录问题创建失败: {e}")

    def create_mr_record(
        self,
        sonar_issue_key: str,
        mr_url: str,
        mr_iid: str = None,
        mr_title: str = None,
        mr_description: str = None,
        branch_name: str = None,
        source_branch: str = None,
        target_branch: str = None,
        mr_status: str = "created",
    ) -> bool:
        """
        创建MR提交记录

        Args:
            sonar_issue_key: SonarQube问题Key
            mr_url: MR地址
            mr_iid: MR的内部ID
            mr_title: MR标题
            mr_description: MR描述
            branch_name: 分支名称
            source_branch: 源分支
            target_branch: 目标分支
            mr_status: MR状态 (created, merged, closed, rejected)

        Returns:
            True表示创建成功，False表示失败
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 将之前的记录标记为非最新
                    cursor.execute(
                        """
                        UPDATE mr_records 
                        SET is_latest = FALSE, updated_time = CURRENT_TIMESTAMP
                        WHERE sonar_issue_key = ? AND is_latest = TRUE
                    """,
                        (sonar_issue_key,),
                    )

                    # 插入新的MR记录
                    cursor.execute(
                        """
                        INSERT INTO mr_records 
                        (sonar_issue_key, mr_url, mr_iid, mr_title, mr_description,
                         branch_name, source_branch, target_branch, mr_status,
                         submitted_time, updated_time, is_latest)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE)
                    """,
                        (
                            sonar_issue_key,
                            mr_url,
                            mr_iid,
                            mr_title,
                            mr_description,
                            branch_name,
                            source_branch,
                            target_branch,
                            mr_status,
                        ),
                    )

                    conn.commit()
                    logger.debug(f"创建MR记录: {sonar_issue_key} -> {mr_url}")
                    return True

        except Exception as e:
            logger.error(f"创建MR记录失败: {e}")
            return False

    def update_mr_record_status(
        self, mr_url: str, mr_status: str, rejection_reason: str = None
    ) -> bool:
        """
        更新MR记录状态

        Args:
            mr_url: MR地址
            mr_status: 新的MR状态 (created, merged, closed, rejected)
            rejection_reason: 如果被驳回，记录驳回原因

        Returns:
            True表示更新成功，False表示失败
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    if rejection_reason:
                        cursor.execute(
                            """
                            UPDATE mr_records 
                            SET mr_status = ?, rejection_reason = ?, updated_time = CURRENT_TIMESTAMP
                            WHERE mr_url = ?
                        """,
                            (mr_status, rejection_reason, mr_url),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE mr_records 
                            SET mr_status = ?, updated_time = CURRENT_TIMESTAMP
                            WHERE mr_url = ?
                        """,
                            (mr_status, mr_url),
                        )

                    conn.commit()
                    if cursor.rowcount > 0:
                        logger.debug(f"更新MR记录状态: {mr_url} -> {mr_status}")
                        return True
                    return False

        except Exception as e:
            logger.error(f"更新MR记录状态失败: {e}")
            return False

    def get_mr_records(self, sonar_issue_key: str) -> List[Dict[str, Any]]:
        """
        获取问题的所有MR记录

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            MR记录列表，按提交时间倒序排列
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT id, sonar_issue_key, mr_url, mr_iid, mr_title, mr_description,
                               branch_name, source_branch, target_branch, mr_status,
                               rejection_reason, submitted_time, updated_time, is_latest
                        FROM mr_records 
                        WHERE sonar_issue_key = ?
                        ORDER BY submitted_time DESC
                    """,
                        (sonar_issue_key,),
                    )

                    records = []
                    for row in cursor.fetchall():
                        records.append(
                            {
                                "id": row[0],
                                "sonar_issue_key": row[1],
                                "mr_url": row[2],
                                "mr_iid": row[3],
                                "mr_title": row[4],
                                "mr_description": row[5],
                                "branch_name": row[6],
                                "source_branch": row[7],
                                "target_branch": row[8],
                                "mr_status": row[9],
                                "rejection_reason": row[10],
                                "submitted_time": row[11],
                                "updated_time": row[12],
                                "is_latest": bool(row[13]),
                            }
                        )

                    return records

        except Exception as e:
            logger.error(f"获取MR记录失败: {e}")
            return []

    def get_latest_mr_record(self, sonar_issue_key: str) -> Optional[Dict[str, Any]]:
        """
        获取问题的最新MR记录

        Args:
            sonar_issue_key: SonarQube问题Key

        Returns:
            最新的MR记录，如果不存在返回None
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT id, sonar_issue_key, mr_url, mr_iid, mr_title, mr_description,
                               branch_name, source_branch, target_branch, mr_status,
                               rejection_reason, submitted_time, updated_time, is_latest
                        FROM mr_records 
                        WHERE sonar_issue_key = ? AND is_latest = TRUE
                    """,
                        (sonar_issue_key,),
                    )

                    row = cursor.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "sonar_issue_key": row[1],
                            "mr_url": row[2],
                            "mr_iid": row[3],
                            "mr_title": row[4],
                            "mr_description": row[5],
                            "branch_name": row[6],
                            "source_branch": row[7],
                            "target_branch": row[8],
                            "mr_status": row[9],
                            "rejection_reason": row[10],
                            "submitted_time": row[11],
                            "updated_time": row[12],
                            "is_latest": bool(row[13]),
                        }
                    return None

        except Exception as e:
            logger.error(f"获取最新MR记录失败: {e}")
            return None

    def get_rejected_mrs(self) -> List[Dict[str, Any]]:
        """
        获取所有被驳回的MR记录

        Returns:
            被驳回的MR记录列表
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT mr.id, mr.sonar_issue_key, mr.mr_url, mr.mr_iid, 
                               mr.mr_title, mr.mr_description, mr.branch_name,
                               mr.source_branch, mr.target_branch, mr.mr_status,
                               mr.rejection_reason, mr.submitted_time, mr.updated_time,
                               si.jira_task_key, si.sonar_project_key
                        FROM mr_records mr
                        LEFT JOIN sonar_issue si ON mr.sonar_issue_key = si.sonar_issue_key
                        WHERE mr.mr_status = 'rejected'
                        ORDER BY mr.updated_time DESC
                    """,
                    )

                    records = []
                    for row in cursor.fetchall():
                        records.append(
                            {
                                "id": row[0],
                                "sonar_issue_key": row[1],
                                "mr_url": row[2],
                                "mr_iid": row[3],
                                "mr_title": row[4],
                                "mr_description": row[5],
                                "branch_name": row[6],
                                "source_branch": row[7],
                                "target_branch": row[8],
                                "mr_status": row[9],
                                "rejection_reason": row[10],
                                "submitted_time": row[11],
                                "updated_time": row[12],
                                "jira_task_key": row[13],
                                "sonar_project_key": row[14],
                            }
                        )

                    return records

        except Exception as e:
            logger.error(f"获取被驳回MR列表失败: {e}")
            return []

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
                    cursor.execute("SELECT COUNT(*) FROM created_projects")
                    total_projects = cursor.fetchone()[0]

                    # 按时间统计
                    cursor.execute(
                        """
                        SELECT DATE(created_time) as date, COUNT(*) as count
                        FROM created_projects 
                        GROUP BY DATE(created_time)
                        ORDER BY date DESC
                        LIMIT 7
                    """
                    )

                    daily_stats = []
                    for row in cursor.fetchall():
                        daily_stats.append({"date": row[0], "count": row[1]})

                    return {
                        "total_projects": total_projects,
                        "daily_creation_stats": daily_stats,
                    }

        except Exception as e:
            logger.error(f"获取项目统计失败: {e}")
            return {}

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取SonarQube问题统计信息

        Returns:
            问题统计信息
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # 总问题数
                    cursor.execute("SELECT COUNT(*) FROM sonar_issue")
                    total_tasks = cursor.fetchone()[0]

                    # 按项目统计
                    cursor.execute(
                        """
                        SELECT sonar_project_key, COUNT(*) as task_count
                        FROM sonar_issue 
                        GROUP BY sonar_project_key
                        ORDER BY task_count DESC
                        LIMIT 10
                    """
                    )

                    project_task_stats = []
                    for row in cursor.fetchall():
                        project_task_stats.append(
                            {"project": row[0], "task_count": row[1]}
                        )

                    # 按修复状态统计
                    cursor.execute(
                        """
                        SELECT fix_status, COUNT(*) as count
                        FROM sonar_issue 
                        GROUP BY fix_status
                        ORDER BY count DESC
                    """
                    )

                    fix_status_stats = []
                    for row in cursor.fetchall():
                        fix_status_stats.append({"status": row[0], "count": row[1]})

                    # 按MR状态统计
                    cursor.execute(
                        """
                        SELECT mr_status, COUNT(*) as count
                        FROM sonar_issue 
                        GROUP BY mr_status
                        ORDER BY count DESC
                    """
                    )

                    mr_status_stats = []
                    for row in cursor.fetchall():
                        mr_status_stats.append({"status": row[0], "count": row[1]})

                    # MR记录统计
                    cursor.execute("SELECT COUNT(*) FROM mr_records")
                    total_mr_records = cursor.fetchone()[0]

                    # 按MR记录状态统计
                    cursor.execute(
                        """
                        SELECT mr_status, COUNT(*) as count
                        FROM mr_records 
                        GROUP BY mr_status
                        ORDER BY count DESC
                    """
                    )

                    mr_record_status_stats = []
                    for row in cursor.fetchall():
                        mr_record_status_stats.append(
                            {"status": row[0], "count": row[1]}
                        )

                    # 被驳回的MR数量
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM mr_records 
                        WHERE mr_status = 'rejected'
                    """
                    )
                    rejected_mr_count = cursor.fetchone()[0]

                    return {
                        "total_tasks": total_tasks,
                        "tasks_by_project": project_task_stats,
                        "fix_status_stats": fix_status_stats,
                        "mr_status_stats": mr_status_stats,
                        "mr_records": {
                            "total_mr_records": total_mr_records,
                            "mr_record_status_stats": mr_record_status_stats,
                            "rejected_mr_count": rejected_mr_count,
                        },
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

                    # 清理旧的问题记录
                    cursor.execute(
                        """
                        DELETE FROM sonar_issue 
                        WHERE created_time < ?
                    """,
                        (cutoff_time.isoformat(),),
                    )

                    deleted_tasks = cursor.rowcount

                    # 清理旧的MR记录
                    cursor.execute(
                        """
                        DELETE FROM mr_records 
                        WHERE submitted_time < ?
                    """,
                        (cutoff_time.isoformat(),),
                    )

                    deleted_mr_records = cursor.rowcount

                    # 清理旧的项目记录
                    cursor.execute(
                        """
                        DELETE FROM created_projects 
                        WHERE created_time < ?
                    """,
                        (cutoff_time.isoformat(),),
                    )

                    deleted_projects = cursor.rowcount

                    conn.commit()

                    if (
                        deleted_projects > 0
                        or deleted_tasks > 0
                        or deleted_mr_records > 0
                    ):
                        logger.info(
                            f"清理完成: 删除 {deleted_projects} 个项目记录, {deleted_tasks} 个问题记录, {deleted_mr_records} 个MR记录"
                        )

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

                    cursor.execute(
                        """
                        SELECT sonar_project_key, jira_project_key, created_time
                        FROM created_projects 
                        ORDER BY created_time DESC
                    """
                    )

                    projects = []
                    for row in cursor.fetchall():
                        projects.append(
                            {
                                "sonar_project_key": row[0],
                                "jira_project_key": row[1],
                                "created_time": row[2],
                            }
                        )

                    return projects

        except Exception as e:
            logger.error(f"获取已创建项目列表失败: {e}")
            return []

    def get_tasks_by_project(self, sonar_project_key: str) -> List[Dict[str, Any]]:
        """
        获取指定项目的所有SonarQube问题

        Args:
            sonar_project_key: SonarQube项目Key

        Returns:
            问题列表
        """
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT sonar_issue_key, jira_task_key, created_time, updated_time
                        FROM sonar_issue 
                        WHERE sonar_project_key = ?
                        ORDER BY updated_time DESC
                    """,
                        (sonar_project_key,),
                    )

                    tasks = []
                    for row in cursor.fetchall():
                        tasks.append(
                            {
                                "sonar_issue_key": row[0],
                                "jira_task_key": row[1],
                                "created_time": row[2],
                                "updated_time": row[3],
                            }
                        )

                    return tasks

        except Exception as e:
            logger.error(f"获取项目问题列表失败: {e}")
            return []

    def export_stats(self) -> Dict[str, Any]:
        """导出完整统计信息"""
        try:
            project_stats = self.get_project_statistics()
            task_stats = self.get_task_statistics()
            db_info = self.get_database_info()

            return {
                "database_stats": {
                    "total_projects": project_stats.get("total_projects", 0),
                    "total_tasks": task_stats.get("total_tasks", 0),
                    "daily_project_creation": project_stats.get(
                        "daily_creation_stats", []
                    ),
                    "tasks_by_project": task_stats.get("tasks_by_project", []),
                },
                "database_info": db_info,
                "summary": {
                    "database_file": str(self.db_path.absolute()),
                    "database_directory": str(self.db_path.parent.absolute()),
                    "created_at": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"导出统计信息失败: {e}")
            return {}
